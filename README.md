
# AllyTech LLC — SSD Testing and Sanitization

Python application for testing, sanitizing, verifying, and documenting Samsung NVMe SSDs recovered from client computer hardware.

## Platform

- Lenovo ThinkCentre M910q Tiny
- Ubuntu Linux
- Python 3.14
- Internal SATA Ubuntu system SSD
- Onboard M.2 NVMe test slot
- Samsung PM961 and PM981 SSDs

USB-connected SSD processing is not supported.

## Installation

Install Linux dependencies:

```bash
sudo apt update
sudo apt install nvme-cli sedutil smartmontools parted util-linux coreutils
```

Install Python dependencies:

```bash
.venv/bin/python -m pip install -r App/requirements.txt
```

## SSD Inventory

Source inventory:

`App/ssd_inventory.csv`

Required columns:

- `serial`
- `model`
- `capacity_gb`

The existing `psid` column may remain. It is not required by the current Opal processing method.

## Operating Procedure

1. Shut down Ubuntu.
2. Disconnect power.
3. Install one SSD in the onboard M.2 NVMe slot.
4. Reconnect power and boot Ubuntu.
5. Open a terminal in the project root.
6. Run preflight.
7. Start processing.
8. Review the report.
9. Shut down before replacing the SSD.

### Preflight

```bash
sudo .venv/bin/python App/ssd_test.py
```

### Full Processing

```bash
sudo .venv/bin/python App/ssd_test.py --execute
```

### Reprocess a Previously Tested SSD

```bash
sudo .venv/bin/python App/ssd_test.py --execute --retry
```

The `--retry` option archives the existing report before starting another processing attempt.

## Processing Sequence

1. Identify and validate the installed SSD.
2. Confirm the Ubuntu system drive is excluded.
3. Read SMART information.
4. Run NVMe short self-test.
5. Perform complete logical zero overwrite.
6. Verify every host-accessible byte against zero.
7. Confirm TCG Opal support.
8. Initialize Opal using a temporary password.
9. Execute authenticated `revertTPer`.
10. Verify the resulting Opal security state.
11. Collect final health information.
12. Generate reports and update the processing summary.

## Result Classification

| Result | Meaning |
|---|---|
| PASS | Health, logical sanitization, and Opal Revert passed. |
| CLEAR_ONLY | Logical sanitization passed; Opal processing did not fully pass. |
| FAIL | Health or logical sanitization failed. |
| INCOMPLETE | Processing could not be fully evaluated. |

Logical clearing and Opal firmware reset results are recorded separately.

The application does not automatically certify NIST Purge.

## Reports

Current reports:

```text
Reports/
├── inventory.csv
└── <SERIAL_NUMBER>/
    ├── report.pdf
    ├── execution.log
    └── dd.log
```

When an Opal operation requires manual recovery, the directory may also contain:

`opal_recovery.txt`

This file contains a temporary Opal administrator password. Keep it private and do not include it in resale documentation.

Previous reports from explicit retries are stored under:

`Reports/_archive/`

## Software Tests

```bash
.venv/bin/python -m unittest discover -s Tests -v
```

Unit tests do not replace hardware validation.

## Documentation

- `Docs/REQUIREMENTS.md`
- `Docs/ARCHITECTURE.md`
- `Docs/FOLDERS.md`
