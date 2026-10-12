
#!/usr/bin/env python3
"""AllyTech LLC NVMe SSD testing and sanitization utility.

Runs manually on the Ubuntu test workstation. Identifies a supported SSD,
checks its health, overwrites and verifies accessible storage, performs
TCG Opal initialization and Revert, and records the results.
"""

import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
INVENTORY = BASE / "ssd_inventory.csv"
REPORTS = ROOT / "Reports"

REQUIRED = (
    "nvme",
    "sedutil-cli",
    "dd",
    "lsblk",
    "blockdev",
    "parted",
    "swapon",
)

# Fields written to the processing summary, independent of the source inventory.
CSV_FIELDS = [
    "timestamp",
    "serial",
    "model",
    "firmware",
    "capacity_bytes",
    "status",
    "sanitization_category",
    "zero_overwrite",
    "full_verification",
    "opal_initialization",
    "opal_revert",
    "opal_verification",
    "self_test",
    "media_errors",
    "percentage_used",
    "error",
]

SUPPORTED_MODELS = {
    "SAMSUNG MZVLW256HEHP-000L7",
    "SAMSUNG MZVLW128HEGR-000L1",
    "SAMSUNG MZVLB256HAHQ-000L7",
}


def utc_now():
    """Return the current UTC time as an ISO 8601 string."""
    return dt.datetime.now(dt.timezone.utc).isoformat()


def cmd(argv, timeout=60, check=True, secret=None):
    """Run an external command and capture its output.

    Args:
        argv: Command and arguments, passed without shell interpretation.
        timeout: Maximum execution time in seconds.
        check: Raise RuntimeError when the command returns a nonzero status.
        secret: Value to redact from command error output.

    Returns:
        The completed subprocess result.

    Raises:
        RuntimeError: The command times out or fails when check is enabled.
    """
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Command timeout: {argv[0]}"
        ) from None

    if check and result.returncode:
        output = (result.stdout + result.stderr).strip()

        if secret:
            output = output.replace(
                secret, "[REDACTED]"
            )

        raise RuntimeError(
            f"{argv[0]} failed "
            f"({result.returncode}): {output}"
        )

    return result


def load_inventory(path=INVENTORY):
    """Load and validate SSD records indexed by electronic serial number.

    Normalizes serial numbers and model names for comparison with NVMe
    controller identification. The historical PSID field is optional.
    """
    with path.open(newline="") as file:
        reader = csv.DictReader(file)

        required = {
            "serial",
            "model",
            "capacity_gb",
        }

        if not required.issubset(
            reader.fieldnames or []
        ):
            raise RuntimeError(
                "SSD inventory columns missing"
            )

        rows = list(reader)

    if not rows:
        raise RuntimeError(
            "SSD inventory is empty"
        )

    inventory = {}

    for row in rows:
        serial = (row["serial"] or "").strip().upper()
        model = (row["model"] or "").strip().upper()

        if not serial or serial in inventory:
            raise RuntimeError(
                "Empty or duplicate inventory serial: "
                + serial
            )

        if not model:
            raise RuntimeError(
                "Missing inventory model for " + serial
            )

        if not model.startswith("SAMSUNG "):
            model = "SAMSUNG " + model

        try:
            capacity = int(row["capacity_gb"])
        except (ValueError, TypeError):
            raise RuntimeError(
                "Invalid inventory capacity for "
                + serial
            ) from None

        if capacity <= 0:
            raise RuntimeError(
                "Invalid inventory capacity for "
                + serial
            )

        row["serial"] = serial
        row["model"] = model
        row["capacity_gb"] = str(capacity)
        row["psid"] = (
            row.get("psid") or ""
        ).strip().upper()

        inventory[serial] = row

    return inventory


def disks():
    """Return the block-device hierarchy reported by lsblk."""
    result = cmd([
        "lsblk",
        "-J",
        "-o",
        "NAME,PATH,TYPE,MOUNTPOINTS,TRAN",
    ])

    return json.loads(
        result.stdout
    )["blockdevices"]


def tree_mounts(device):
    """Yield mounted filesystems from a device and its descendants."""
    for mount in device.get("mountpoints") or []:
        if mount:
            yield mount

    for child in device.get("children") or []:
        yield from tree_mounts(child)


def identify_target():
    """Locate the unmounted NVMe test device and exclude the system disk.

    Returns:
        A tuple containing the NVMe namespace and controller paths.

    Raises:
        RuntimeError: The system disk cannot be identified or the test
            target is missing, ambiguous, mounted, or active as swap.
    """
    all_disks = disks()

    # Refuse processing unless the Ubuntu system disk can be identified.
    # Never assume a particular /dev/sdX name is the system drive.
    system_disks = {
        disk["path"]
        for disk in all_disks
        if any(
            mount in ("/", "/boot", "/boot/efi")
            for mount in tree_mounts(disk)
        )
    }

    if not system_disks:
        raise RuntimeError(
            "Cannot identify Ubuntu system disk"
        )

    candidates = [
        disk
        for disk in all_disks
        if disk.get("type") == "disk"
        and re.fullmatch(
            r"nvme\d+n\d+",
            disk.get("name", ""),
        )
        and disk.get("tran") == "nvme"
    ]

    if len(candidates) != 1:
        raise RuntimeError(
            "Expected one onboard NVMe SSD; "
            f"found {len(candidates)}"
        )

    disk = candidates[0]
    path = disk["path"]

    if path in system_disks:
        raise RuntimeError(
            "NVMe target is the Ubuntu system drive"
        )

    if any(tree_mounts(disk)):
        raise RuntimeError(
            "NVMe target or partition is mounted"
        )

    # Active swap may not appear as an ordinary mounted filesystem.
    swap = cmd([
        "swapon",
        "--show=NAME",
        "--noheadings",
    ]).stdout.splitlines()

    for entry in swap:
        name = entry.strip()

        if name == path or re.fullmatch(
            re.escape(path) + r"p\d+",
            name,
        ):
            raise RuntimeError(
                "NVMe target is active swap"
            )

    # Convert a namespace such as /dev/nvme0n1 to its controller path.
    controller = re.sub(
        r"n\d+$", "", path
    )

    if not Path(controller).exists():
        raise RuntimeError(
            "NVMe controller device missing"
        )

    return path, controller


def ctrl_identity(controller):
    """Read the NVMe controller's model, serial, firmware, and capabilities."""
    output = cmd([
        "nvme",
        "id-ctrl",
        controller,
        "-o",
        "json",
    ]).stdout

    data = json.loads(output)

    def value(key):
        return str(
            data.get(key, "")
        ).strip().upper()

    return {
        "serial": value("sn"),
        "model": value("mn"),
        "firmware": value("fr"),
        "oacs": int(data.get("oacs", 0)),
    }


def smart(controller):
    """Return the NVMe SMART health log as a dictionary."""
    output = cmd([
        "nvme",
        "smart-log",
        controller,
        "-o",
        "json",
    ]).stdout

    return json.loads(output)


def smart_ok(data):
    """Evaluate the SMART warning, media-error, and spare-capacity criteria."""
    try:
        return (
            int(data["critical_warning"]) == 0
            and int(data["media_errors"]) == 0
            and int(data["avail_spare"])
            > int(data["spare_thresh"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def parse_self_test(text):
    """Interpret the latest NVMe self-test log entry.

    Returns:
        False while a self-test is active, or True when the latest short
        self-test completed successfully.

    Raises:
        RuntimeError: The result is missing, invalid, or unsuccessful.
    """
    operation = re.search(
        r"Current operation\s*:\s*(\d+)",
        text,
        re.I,
    )

    if not operation:
        raise RuntimeError(
            "Cannot parse self-test operation status"
        )

    if int(operation.group(1)) != 0:
        return False

    # Entry zero is the most recent completed self-test in the NVMe log.
    match = re.search(
        r"Self Test Result\[0\]:(.*?)"
        r"(?:Self Test Result\[1\]:|\Z)",
        text,
        re.I | re.S,
    )

    if not match:
        raise RuntimeError(
            "Latest self-test result missing"
        )

    section = match.group(1)

    result = re.search(
        r"Operation Result\s*:\s*"
        r"(0x[0-9a-f]+|\d+)",
        section,
        re.I,
    )

    kind = re.search(
        r"Self Test Code\s*:\s*(\d+)",
        section,
        re.I,
    )

    if not result or not kind:
        raise RuntimeError(
            "Cannot parse latest self-test result"
        )

    if (
        int(result.group(1), 0) != 0
        or int(kind.group(1)) != 1
    ):
        raise RuntimeError(
            "NVMe short self-test failed"
        )

    return True


def short_test(controller, log):
    """Start and poll an NVMe short self-test, allowing up to 15 minutes."""
    log("Starting NVMe short self-test")

    cmd([
        "nvme",
        "device-self-test",
        controller,
        "--self-test-code=1",
    ])

    deadline = time.monotonic() + 900

    while time.monotonic() < deadline:
        time.sleep(15)

        output = cmd([
            "nvme",
            "self-test-log",
            controller,
        ]).stdout

        if parse_self_test(output):
            log("NVMe short self-test PASSED")
            return

    raise RuntimeError(
        "NVMe short self-test timeout"
    )


def verify_zeroes(path, size, log):
    """Read the entire logical device and reject any nonzero or missing data.

    Args:
        path: NVMe namespace device path.
        size: Expected readable capacity in bytes.
        log: Callback for recording progress and results.

    Returns:
        A tuple containing verified bytes and elapsed seconds.
    """
    # Use bounded reads to avoid loading the entire SSD into memory.
    chunk_size = 8 * 1024 * 1024
    checked = 0
    started = time.monotonic()

    log("Starting full-device zero verification")

    with open(path, "rb", buffering=0) as disk:
        while checked < size:
            amount = min(
                chunk_size,
                size - checked,
            )

            data = disk.read(amount)

            if len(data) != amount:
                raise RuntimeError(
                    "Short read during verification "
                    f"at byte {checked}"
                )

            if any(data):
                raise RuntimeError(
                    "Nonzero data found at or after "
                    f"byte {checked}"
                )

            checked += amount

    elapsed = time.monotonic() - started

    log(
        "Full zero verification PASSED: "
        f"{checked} bytes; "
        f"{elapsed:.1f} seconds"
    )

    return checked, elapsed


def opal_capabilities(text):
    """Check whether the sedutil query reports the required Opal features."""
    return (
        "OPAL 2.0 function" in text
        and "LockingSupported = Y" in text
        and "MediaEncrypt = Y" in text
    )


def opal_reset_state(text):
    """Check the expected unlocked state following Opal Revert."""
    return all(
        entry in text
        for entry in (
            "Locked = N",
            "LockingEnabled = N",
            "MBREnabled = N",
        )
    )


def classify_result(
    clear_passed,
    health_passed,
    opal_passed,
):
    """Classify the combined sanitization and health-test results.

    A verified logical overwrite without a successful Opal operation is
    distinguished from a complete workflow PASS.
    """
    if not health_passed:
        return "FAIL"

    if not clear_passed:
        return "FAIL"

    if not opal_passed:
        return "CLEAR_ONLY"

    return "PASS"


def save_recovery_password(folder, password):
    """Save the temporary Opal credential in a restricted local file.

    An existing recovery file is never overwritten. The credential is
    retained if the subsequent Opal operation requires manual recovery.
    """
    path = folder / "opal_recovery.txt"

    # O_EXCL prevents replacement of an existing recovery credential.
    # Mode 0600 restricts access to the file owner.
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
    )

    descriptor = os.open(
        path,
        flags,
        0o600,
    )

    try:
        with os.fdopen(descriptor, "w") as file:
            file.write(password + "\n")
            file.flush()
            os.fsync(file.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise

    return path


def archive_existing(serial):
    """Archive a previous per-SSD report directory before an explicit retry."""
    folder = REPORTS / serial

    if not folder.exists():
        return

    archive = REPORTS / "_archive"
    archive.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = dt.datetime.now(
        dt.timezone.utc
    ).strftime("%Y%m%dT%H%M%S%fZ")

    destination = (
        archive / f"{serial}_{stamp}"
    )

    folder.rename(destination)


def merge_inventory_rows(
    existing,
    data,
):
    """Merge a processing result with existing CSV records by serial number.

    Rebuilds rows using the current summary fields so older CSV formats
    remain readable when the report schema changes.
    """
    rows = []

    for row in existing:
        if row.get("serial") == data["serial"]:
            continue

        rows.append({
            field: str(row.get(field, "") or "")
            for field in CSV_FIELDS
        })

    rows.append({
        field: str(data.get(field, ""))
        for field in CSV_FIELDS
    })

    return rows


def write_reports(serial, data, lines):
    """Write the execution log, printable PDF, and processing summary CSV.

    The source SSD inventory is not modified.
    """
    folder = REPORTS / serial
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf = folder / "report.pdf"

    final_line = (
        f"{utc_now()} Report saved: {pdf}"
    )

    (folder / "execution.log").write_text(
        "\n".join(lines + [final_line]) + "\n"
    )

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    c = canvas.Canvas(
        str(pdf),
        pagesize=letter,
    )

    width, height = letter

    def new_page():
        """Start a report page with its identifying header."""
        c.setFont(
            "Helvetica-Bold", 14
        )
        c.drawString(
            40,
            height - 45,
            "AllyTech LLC - SSD Test and Sanitization",
        )
        c.setFont(
            "Helvetica", 9
        )
        return height - 75

    y = new_page()

    for key, value in data.items():
        line = f"{key}: {value}"

        # Continue on a new page when the remaining space is insufficient.
        chunks = [
            line[i:i + 105]
            for i in range(0, len(line), 105)
        ] or [""]

        for chunk in chunks:
            if y < 50:
                c.showPage()
                y = new_page()

            c.drawString(
                40,
                y,
                chunk,
            )
            y -= 15

    c.save()

    index_path = REPORTS / "inventory.csv"
    existing = []

    if index_path.exists():
        with index_path.open(newline="") as file:
            existing = list(
                csv.DictReader(file)
            )

    rows = merge_inventory_rows(
        existing,
        data,
    )

    with index_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
        )
        writer.writeheader()
        writer.writerows(rows)

    return pdf


def process(execute=False, retry=False):
    """Run the preflight or complete SSD testing and sanitization workflow.

    Args:
        execute: Enable destructive processing after target validation.
        retry: Archive existing reports and allow deliberate reprocessing.

    The test target is reidentified before the overwrite operation.
    Processing results are written even when a required operation fails.
    """
    inventory = load_inventory()

    path, controller = identify_target()
    identity = ctrl_identity(controller)

    serial = identity["serial"]
    record = inventory.get(serial)

    if (
        not record
        or identity["model"] != record["model"]
    ):
        raise RuntimeError(
            "SSD serial/model does not match inventory"
        )

    if identity["model"] not in SUPPORTED_MODELS:
        raise RuntimeError(
            "SSD model not in supported model list"
        )

    size = int(cmd([
        "blockdev",
        "--getsize64",
        path,
    ]).stdout.strip())

    expected_gb = int(
        record["capacity_gb"]
    )

    expected_bytes = (
        expected_gb * 1_000_000_000
    )

    if abs(
        size - expected_bytes
    ) > expected_bytes * 0.02:
        raise RuntimeError(
            "SSD capacity does not match inventory"
        )

    print(
        f"TARGET: {path} | "
        f"{identity['model']} | "
        f"SN {serial} | "
        f"{size} bytes"
    )

    print(
        "SYSTEM PROTECTION: system drive "
        "excluded; target unmounted"
    )

    folder = REPORTS / serial

    if folder.exists() and not retry:
        raise RuntimeError(
            "Existing processing record. "
            "Use --retry for deliberate reprocessing."
        )

    if not execute:
        print(
            "PREFLIGHT OK. "
            "No changes performed."
        )
        return

    if os.geteuid() != 0:
        raise RuntimeError(
            "Run --execute with sudo"
        )

    # Bit 4 of OACS indicates NVMe device self-test support.
    if not (
        identity["oacs"] & (1 << 4)
    ):
        raise RuntimeError(
            "NVMe short self-test not supported"
        )

    before = smart(controller)

    if not smart_ok(before):
        raise RuntimeError(
            "Initial SMART health check failed"
        )

    # An explicit retry preserves prior processing evidence.
    if retry:
        archive_existing(serial)

    REPORTS.mkdir(
        parents=True,
        exist_ok=True,
    )
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = []

    def log(message):
        """Timestamp and record a processing event."""
        line = f"{utc_now()} {message}"
        lines.append(line)
        print(line, flush=True)

    data = {
        "timestamp": utc_now(),
        "serial": serial,
        "model": identity["model"],
        "firmware": identity["firmware"],
        "capacity_bytes": size,
        "status": "INCOMPLETE",
        "sanitization_category": "NONE",
        "self_test": "NOT RUN",
        "zero_overwrite": "NOT RUN",
        "full_verification": "NOT RUN",
        "opal_initialization": "NOT RUN",
        "opal_revert": "NOT RUN",
        "opal_verification": "NOT RUN",
        "power_on_hours": before.get(
            "power_on_hours", ""
        ),
        "percentage_used": before.get(
            "percentage_used", ""
        ),
        "media_errors": before.get(
            "media_errors", ""
        ),
    }

    clear_passed = False
    health_passed = True
    opal_passed = False

    password = None
    recovery_path = None

    try:
        short_test(controller, log)
        data["self_test"] = "PASS"

        opal_before = cmd([
            "sedutil-cli",
            "--query",
            path,
        ]).stdout

        if not opal_capabilities(
            opal_before
        ):
            raise RuntimeError(
                "Required TCG Opal 2.0 "
                "capability missing"
            )

        # Check target identity again immediately before destructive I/O.
        # The initial inventory match alone is not sufficient if devices change.
        new_path, new_controller = (
            identify_target()
        )
        new_identity = ctrl_identity(
            new_controller
        )

        if (
            new_path != path
            or new_controller != controller
            or new_identity["serial"] != serial
            or new_identity["model"]
            != identity["model"]
        ):
            raise RuntimeError(
                "Target identity changed"
            )

        log(
            "Starting full logical-device "
            "zero overwrite"
        )

        started = time.monotonic()
        dd_log = folder / "dd.log"

        # Use an exact byte count, direct output I/O, and synchronized writes.
        # Store dd output separately from the application execution log.
        with dd_log.open("w") as output:
            result = subprocess.run(
                [
                    "dd",
                    "if=/dev/zero",
                    f"of={path}",
                    "bs=16M",
                    f"count={size}",
                    "iflag=count_bytes,fullblock",
                    "oflag=direct",
                    "conv=fsync",
                    "status=progress",
                ],
                stdout=output,
                stderr=subprocess.STDOUT,
            )

        if result.returncode:
            raise RuntimeError(
                "Zero overwrite failed: "
                f"exit code {result.returncode}"
            )

        elapsed = (
            time.monotonic() - started
        )

        data["zero_overwrite"] = (
            f"PASS; {size} bytes; "
            f"{elapsed:.1f} seconds"
        )

        log(data["zero_overwrite"])

        # Verify logical storage through an independent readback pass.
        checked, verify_time = verify_zeroes(
            path,
            size,
            log,
        )

        if checked != size:
            raise RuntimeError(
                "Full-device verification "
                "byte count mismatch"
            )

        data["full_verification"] = (
            f"PASS; {checked} bytes; "
            f"{verify_time:.1f} seconds"
        )

        clear_passed = True
        data["sanitization_category"] = "CLEAR"

        log(
            "Starting TCG Opal initialization"
        )

        # Retain the temporary credential until Revert and its checks finish.
        # It is needed if initialization succeeds but Revert fails.
        password = secrets.token_hex(16)

        recovery_path = save_recovery_password(
            folder,
            password,
        )

        initialization = cmd(
            [
                "sedutil-cli",
                "--initialSetup",
                password,
                path,
            ],
            timeout=300,
            secret=password,
        )

        response = (
            initialization.stdout
            + initialization.stderr
        )

        if (
            "Initial setup of TPer complete"
            not in response
        ):
            raise RuntimeError(
                "Opal initialization did not "
                "confirm completion"
            )

        data["opal_initialization"] = "PASS"
        log(
            "TCG Opal initialization PASSED"
        )

        log(
            "Starting TCG Opal revertTPer"
        )

        revert = cmd(
            [
                "sedutil-cli",
                "--revertTPer",
                password,
                path,
            ],
            timeout=300,
            secret=password,
        )

        response = (
            revert.stdout + revert.stderr
        )

        # A successful process exit alone is not the confirmation criterion.
        if (
            "revertTper completed successfully"
            not in response
        ):
            raise RuntimeError(
                "Opal Revert did not "
                "confirm completion"
            )

        data["opal_revert"] = "PASS"
        log(
            "TCG Opal revertTPer PASSED"
        )

        after_opal = cmd([
            "sedutil-cli",
            "--query",
            path,
        ]).stdout

        if not opal_reset_state(
            after_opal
        ):
            raise RuntimeError(
                "Post-Revert Opal "
                "security state invalid"
            )

        final_identity = ctrl_identity(
            controller
        )

        if (
            final_identity["serial"] != serial
            or final_identity["model"]
            != identity["model"]
        ):
            raise RuntimeError(
                "Device identity mismatch "
                "after Revert"
            )

        data["opal_verification"] = "PASS"
        log(
            "Post-Revert Opal "
            "verification PASSED"
        )

        # Partition inspection is recorded as an observation, not used
        # as proof that all logical storage was sanitized.
        partition = cmd(
            [
                "parted",
                "-s",
                path,
                "print",
            ],
            check=False,
        )

        data["partition_inspection"] = (
            partition.stdout
            + partition.stderr
        ).strip()[:400]

        after = smart(controller)

        if not smart_ok(after):
            health_passed = False
            raise RuntimeError(
                "Final SMART health check failed"
            )

        data["media_errors"] = after.get(
            "media_errors", ""
        )

        data["percentage_used"] = after.get(
            "percentage_used", ""
        )

        opal_passed = True

        # Remove the credential only after successful Opal and health checks.
        if recovery_path:
            recovery_path.unlink()
            recovery_path = None

        data["status"] = classify_result(
            clear_passed,
            health_passed,
            opal_passed,
        )

        log(
            "All required operations PASSED"
        )

    except Exception as exc:
        error = str(exc)

        if password:
            error = error.replace(
                password,
                "[REDACTED]",
            )

        data["error"] = error

        data["status"] = classify_result(
            clear_passed,
            health_passed,
            opal_passed,
        )

        log("FAILED: " + error)

        if (
            recovery_path
            and recovery_path.exists()
        ):
            data["recovery_note"] = (
                "Local Opal recovery credential "
                "retained. Review before further "
                "Opal operations."
            )

            log(
                "Opal recovery credential "
                "retained locally"
            )

    finally:
        # Preserve available results even when processing is unsuccessful.
        pdf = write_reports(
            serial,
            data,
            lines,
        )

        print(
            "Report saved:",
            pdf,
        )
        print(
            "OVERALL:",
            data["status"],
        )

    if data["status"] != "PASS":
        raise SystemExit(1)


def main():
    """Parse command-line options, check dependencies, and run processing."""
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Execute SSD testing "
            "and sanitization"
        ),
    )

    parser.add_argument(
        "--retry",
        action="store_true",
        help=(
            "Archive prior report "
            "and reprocess SSD"
        ),
    )

    args = parser.parse_args()

    if args.retry and not args.execute:
        parser.error(
            "--retry requires --execute"
        )

    for utility in REQUIRED:
        if not shutil.which(utility):
            raise RuntimeError(
                "Missing utility: " + utility
            )

    process(
        args.execute,
        args.retry,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            "ERROR:",
            exc,
            file=sys.stderr,
        )
        sys.exit(1)
