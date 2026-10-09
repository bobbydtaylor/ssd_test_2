# SSD Test and Sanitization — Architecture

## 1. Application

`ssd_test.py` runs under Python 3.14 on the Ubuntu Lenovo M910q and invokes Linux storage utilities via subprocess. There is no automatic-start service.

## 2. Inputs

- `ssd_inventory.csv`: serial, model, capacity, PSID; unmatched or unconfirmed PSIDs are rejected.
- Electronic NVMe identity read from the controller.
- `--execute`: opt-in to destructive processing; without it the application performs read-only preflight.

## 3. Dependencies

- `lsblk`: physical device tree, system drive exclusion, mount detection.
- `nvme-cli`: controller identity, SMART data, short self-test and result log.
- `blockdev`: device byte size.
- `dd`: logical-address zero overwrite with direct I/O and synchronization.
- Python raw device reads: distributed zero verification.
- `sedutil-cli`: TCG Opal PSID Revert and security-state query.
- `parted`: post-revert partition table inspection.
- `reportlab`: PDF output.

## 4. Procedure

1. Enumerate drives and exclude any device containing `/`, `/boot`, or `/boot/efi`.
2. Confirm exactly one NVMe namespace, no mounted partitions and no active swap.
3. Match electronic serial and model against `ssd_inventory.csv` and require a confirmed PSID.
4. Check previous result and initial SMART health.
5. Run and evaluate NVMe short self-test.
6. Recheck target identity and mount status.
7. Overwrite full device length with zero bytes using `dd`.
8. Read 32 evenly distributed 1 MiB samples and compare each byte to zero.
9. Execute PSID Revert using `sedutil-cli`.
10. Require `revertTper completed successfully`.
11. Query Opal security state, inspect partitions and read final SMART health.
12. Generate CSV summary, PDF report and execution log.

## 5. Results

- `reports/inventory.csv`: one summary row per serial number.
- `reports/<serial>/report.pdf`: printable result report.
- `reports/<serial>/execution.log`: timestamped operation log.

Overall PASS requires the acceptance criteria in `REQUIREMENTS.md`. Otherwise FAIL is recorded. Command failures terminate further destructive operations.

## 6. Execution

Read-only preflight:

    sudo .venv/bin/python ssd_test.py

Execute processing:

    sudo .venv/bin/python ssd_test.py --execute

## 7. Implementation

- Python standard library for orchestration and CSV.
- ReportLab for PDF generation.
- No database, GUI, cloud dependency, or background process.