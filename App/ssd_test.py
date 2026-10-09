#!/usr/bin/env python3
"""DMK SSD diagnostic, host-accessible overwrite and Opal PSID revert utility."""
import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent

INVENTORY = BASE / "ssd_inventory.csv"
REPORTS = PROJECT_ROOT / "Reports"
REQUIRED = ("nvme", "sedutil-cli", "dd", "lsblk", "findmnt", "blockdev", "parted")


def cmd(argv, timeout=60, check=True):
    p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(argv)}\n{p.stdout}\n{p.stderr}")
    return p


def valid_psid(value):
    return bool(re.fullmatch(r"[A-Z0-9]{32}", value or ""))


def load_inventory(path=INVENTORY):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    seen = set()
    for row in rows:
        sn = row["serial"].strip().upper()
        if not sn or sn in seen:
            raise RuntimeError("Duplicate or empty serial in inventory: " + sn)
        seen.add(sn)
        row["serial"] = sn
        row["psid"] = row["psid"].strip().upper()
        row["model"] = row["model"].strip().upper()
        if not row["model"].startswith("SAMSUNG "):row["model"] = "SAMSUNG " + row["model"]
    return {row["serial"]: row for row in rows}


def disks():
    data = json.loads(cmd(["lsblk", "-J", "-o", "NAME,PATH,TYPE,MOUNTPOINTS"]).stdout)
    return data.get("blockdevices", [])


def tree_mounts(item):
    for mount in (item.get("mountpoints") or []):
        if mount:
            yield mount
    for child in (item.get("children") or []):
        yield from tree_mounts(child)


def identify_target():
    all_disks = disks()
    system_disks = {d["path"] for d in all_disks if any(m in ("/", "/boot", "/boot/efi") for m in tree_mounts(d))}
    if not system_disks:
        raise RuntimeError("Could not identify system disk; refusing operation")
    candidates = [d for d in all_disks if d.get("type") == "disk" and re.fullmatch(r"nvme\d+n\d+", d.get("name", ""))]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one NVMe namespace; found {len(candidates)}")
    disk = candidates[0]
    path = disk["path"]
    if path in system_disks or any(tree_mounts(disk)):
        raise RuntimeError("Target SSD or partitions mounted; refusing operation")
    swaps = cmd(["swapon", "--show=NAME", "--noheadings"], check=False).stdout
    if re.search(re.escape(path) + r"(p\d+)?(?:\s|$)", swaps):
        raise RuntimeError("NVMe drive is active swap")
    controller = re.sub(r"n\d+$", "", path)
    if not Path(controller).exists():
        raise RuntimeError("NVMe controller missing")
    return path, controller


def ctrl_identity(controller):
    data = json.loads(cmd(["nvme", "id-ctrl", controller, "-o", "json"]).stdout)
    def txt(k):
        return str(data.get(k, "")).strip().upper()
    return {"serial": txt("sn"), "model": txt("mn"), "firmware": txt("fr"), "oacs": int(data.get("oacs", 0))}


def smart(controller):
    return json.loads(cmd(["nvme", "smart-log", controller, "-o", "json"]).stdout)


def smart_ok(data):
    try:
        return (int(data["critical_warning"]) == 0 and int(data["media_errors"]) == 0
                and int(data["available_spare"]) > int(data["available_spare_threshold"]))
    except (KeyError, TypeError, ValueError):
        return False


def short_test(controller, log):
    log("Starting NVMe short self-test")
    cmd(["nvme", "device-self-test", controller, "--self-test-code=1"])
    until = time.monotonic() + 900
    while time.monotonic() < until:
        time.sleep(15)
        result = cmd(["nvme", "self-test-log", controller], timeout=60).stdout
        current = re.search(r"Current operation:\s*(\d+)", result, re.I)
        completion = re.search(r"Current Completion:\s*(\d+)%", result, re.I)
        if current and current.group(1) == "0":
            section = result.split("Self Test Result[0]:", 1)
            if len(section) != 2:
                raise RuntimeError("Could not parse latest self-test result")
            code = re.search(r"Operation Result\s*:\s*(0x[0-9a-f]+|\d+)", section[1], re.I)
            kind = re.search(r"Self Test Code\s*:\s*(\d+)", section[1], re.I)
            if not code or int(code.group(1), 0) != 0 or not kind or int(kind.group(1)) != 1:
                raise RuntimeError("Short self-test did not pass: " + section[1][:300])
            log("NVMe short self-test PASSED")
            return
        log("Self-test running " + (completion.group(1) + "%" if completion else ""))
    raise RuntimeError("Self-test timeout")


def verify_samples(path, size, log):
    # Sequentially read deterministic, evenly distributed 1 MiB samples.
    sample_size = min(1024 * 1024, size)
    offsets = sorted({min(size - sample_size, (size - sample_size) * i // 31) for i in range(32)})
    with open(path, "rb", buffering=0) as disk:
        for i, off in enumerate(offsets):
            disk.seek(off)
            buf = disk.read(sample_size)
            if len(buf) != sample_size or any(buf):
                raise RuntimeError(f"Zero verification failed at byte offset {off}")
    log(f"Overwrite sampling PASSED: {len(offsets)} x {sample_size} bytes across the full device")
    return len(offsets) * sample_size


def reports(serial, data, lines):
    folder = REPORTS / serial
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "execution.log").write_text("\n".join(lines) + "\n")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        raise RuntimeError("PDF library missing. Run: pip install -r requirements.txt")
    c = canvas.Canvas(str(folder / "report.pdf"), pagesize=letter)
    w, h = letter
    def page():
        c.setFont("Helvetica-Bold", 15)
        c.drawString(42, h - 45, "DMK SSD Test and Sanitization Report")
        c.setFont("Helvetica", 9)
        return h - 73
    y = page()
    for key, value in data.items():
        text = f"{key}: {value}"
        for chunk in [text[i:i + 106] for i in range(0, len(text), 106)]:
            if y < 52:
                c.showPage();y = page()
            c.drawString(42, y, chunk); y -= 16
    c.save()
    index_path = REPORTS / "inventory.csv"
    fields = ["timestamp", "serial", "model", "capacity_bytes", "status", "zero_overwrite", "sample_verification", "psid_revert", "media_errors", "percentage_used"]
    rows = []
    if index_path.exists():
        with index_path.open(newline="") as f:
            rows = list(csv.DictReader(f))
    rows = [r for r in rows if r["serial"] != serial]
    rows.append({field: str(data.get(field, "")) for field in fields})
    with index_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    return folder


def process(execute=False):
    inventory = load_inventory()
    path, ctrl = identify_target()
    ident = ctrl_identity(ctrl)
    serial = ident["serial"]
    record = inventory.get(serial)
    if not record or ident["model"] != record["model"]:
        raise RuntimeError("Serial/model mismatch or device not found in inventory")
    if not valid_psid(record["psid"]):
        raise RuntimeError(f"No confirmed 32-character PSID for serial {serial}; refusing operation")
    size = int(cmd(["blockdev", "--getsize64", path]).stdout.strip())
    before = smart(ctrl)
    print(f"TARGET: {path} | {ident['model']} | SN {serial} | {size} bytes")
    print(f"SYSTEM PROTECTION: system drive excluded; target unmounted")
    if (REPORTS / serial / "report.pdf").exists():
        raise RuntimeError("This serial already has a completed/attempted report; review before retry")
    if not execute:
        print("PREFLIGHT OK. No drive changes performed. Run with --execute to begin.")
        return
    if os.geteuid() != 0:
        raise RuntimeError("Run with sudo for --execute")
    if not smart_ok(before):
        raise RuntimeError("SMART health criteria not met")
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = []
    def log(s):
        line = f"{dt.datetime.now(dt.timezone.utc).isoformat()} {s}"
        lines.append(line); print(line, flush=True)
    data = {"timestamp":dt.datetime.now(dt.timezone.utc).isoformat(), "serial":serial,
            "model":ident["model"], "firmware":ident["firmware"], "capacity_bytes":size,
            "zero_overwrite":"NOT RUN", "sample_verification":"NOT RUN", "psid_revert":"NOT RUN",
            "status":"FAIL", "power_on_hours":before.get("power_on_hours", ""),
            "percentage_used":before.get("percentage_used", ""), "media_errors":before.get("media_errors", "")}
    try:
        if not (ident["oacs"] & (1 << 4)):
            raise RuntimeError("NVMe self-test not supported; test policy requires it")
        short_test(ctrl, log)
        path2, ctrl2 = identify_target()
        ident2 = ctrl_identity(ctrl2)
        if path2 != path or ident2["serial"] != serial or ident2["model"] != ident["model"]:
            raise RuntimeError("Target changed before overwrite")
        log("Starting full logical-device zero overwrite")
        # Count exact 512-byte sectors: no expected end-of-device ENOSPC.
        if size % 512:
            raise RuntimeError("Device capacity not sector aligned")
        t0=time.monotonic()
        with open(REPORTS / "_last_dd.log", "w") as out:
            p=subprocess.run(["dd", "if=/dev/zero",f"of={path}","bs=16M",f"count={size}",
                              "iflag=count_bytes,fullblock", "oflag=direct", "conv=fsync", "status=progress"],
                             stdout=out,stderr=subprocess.STDOUT)
        if p.returncode:
            raise RuntimeError(f"dd overwrite failed with exit code {p.returncode}")
        data["zero_overwrite"] = f"PASS, {size} bytes; {time.monotonic()-t0:.1f} seconds"
        log(data["zero_overwrite"])
        bytes_checked = verify_samples(path, size, log)
        data["sample_verification"] = f"PASS, {bytes_checked} bytes (32 samples, 1 MiB each)"
        log("Starting Opal PSID Revert")
        psid_cmd = ["sedutil-cli", "--yesIreallywanttoERASEALLmydatausingthePSID", record["psid"], path]
        result=cmd(psid_cmd, timeout=300)
        if "revertTper completed successfully" not in (result.stdout+result.stderr):
            raise RuntimeError("PSID revert did not report successful completion")
        data["psid_revert"] = "PASS (revertTper completed successfully)"
        state=cmd(["sedutil-cli", "--query", path]).stdout
        for field in ("Locked = N", "LockingEnabled = N"):
            if field not in state:
                raise RuntimeError("Post-revert Opal state check failed: " + field)
        data["opal_security_state"]="Unlocked; locking disabled"
        partition=cmd(["parted", "-s", path, "print"], check=False)
        data["partition_inspection"]=(partition.stdout+partition.stderr).strip()[:400]
        after=smart(ctrl)
        if not smart_ok(after):
            raise RuntimeError("Post-revert SMART health criteria not met")
        data["media_errors"] = after.get("media_errors", "")
        data["percentage_used"] = after.get("percentage_used", "")
        data["status"] = "PASS"
        log("All required checks PASSED")
    except Exception as ex:
        data["error"] = str(ex)
        log("FAILED: " + str(ex))
    finally:
        folder=reports(serial,data,lines)
        log("Report saved: " + str(folder / "report.pdf"))
        print("OVERALL:",data["status"])
    if data["status"] != "PASS":
        raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true",help="Perform irreversible full overwrite and PSID Revert")
    args=parser.parse_args()
    for utility in REQUIRED:
        if not shutil.which(utility):
            raise RuntimeError("Missing Linux utility: " + utility)
    process(args.execute)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:",exc,file=sys.stderr)
        sys.exit(1)