
# AllyTech LLC — SSD Testing and Sanitization

## Overview

Python application for testing, sanitizing, verifying, and documenting used Samsung NVMe SSDs recovered from client computers for resale.

The application runs manually on an Ubuntu workstation, processes one SSD at a time, and generates a PDF report containing the test and sanitization results.

Processing continues unattended after initiation.

## Hardware and Software

### Test Workstation

- Lenovo ThinkCentre M910q Tiny
- Ubuntu Linux
- Python 3.14
- Internal SATA SSD containing Ubuntu
- Internal M.2 NVMe slot for the SSD being tested

### Supported SSDs

- Samsung PM961 128 GB
- Samsung PM961 256 GB
- Samsung PM981 256 GB

The installed SSD must match a supported model and an existing inventory record.

USB-to-NVMe adapters are not supported for processing.

## Initial Setup

Perform these steps once on the Ubuntu workstation.

### 1. Install Linux Dependencies

```bash
sudo apt update
sudo apt install nvme-cli sedutil parted util-linux coreutils python3-venv
```

### 2. Create the Python Virtual Environment

From the project root directory:

```bash
python3 -m venv .venv
```

### 3. Install Python Dependencies

```bash
.venv/bin/python -m pip install -r App/requirements.txt
```

The application uses ReportLab to generate PDF reports.

## SSD Inventory

Source inventory:

`App/ssd_inventory.csv`

Required fields:

| Field | Description |
|---|---|
| serial | SSD electronic serial number |
| model | SSD model number |
| capacity_gb | Manufacturer-rated capacity in GB |
| psid | Optional historical PSID information |

Before processing, the application reads the SSD's electronic identification and verifies the serial number and model against the inventory.

The PSID is not required for the current sanitization procedure.

The application does not modify the source inventory.

## Operating Instructions

### 1. Install the SSD

1. Shut down Ubuntu.
2. Disconnect power from the Lenovo computer.
3. Install one SSD in the internal M.2 NVMe slot.
4. Reconnect power and boot Ubuntu.
5. Open a terminal in the project root directory.

### 2. Run Preflight

```bash
sudo .venv/bin/python App/ssd_test.py
```

Preflight verifies:

- Exactly one supported NVMe test SSD is detected.
- The Ubuntu system drive is excluded.
- The test SSD is not mounted or being used as swap.
- The SSD model and serial number match the inventory.
- The SSD capacity matches the inventory.
- No existing processing record prevents execution.

Preflight does not modify the SSD.

Expected successful result:

```text
TARGET: /dev/nvme0n1 | SAMSUNG ... | SN ... | ... bytes
SYSTEM PROTECTION: system drive excluded; target unmounted
PREFLIGHT OK. No changes performed.
```

### 3. Start SSD Processing

```bash
sudo .venv/bin/python App/ssd_test.py --execute
```

The application performs:

1. SSD identification and SMART health checks.
2. NVMe short self-test.
3. TCG Opal capability verification.
4. Complete logical-device zero overwrite.
5. Full-device readback verification.
6. TCG Opal initialization and authenticated Revert.
7. Post-Revert security checks.
8. Final SMART health checks.
9. PDF report, execution log, and processing summary generation.

All data on the selected SSD is erased.

Allow the application to finish before removing the SSD.

### 4. Review the Results

The application displays the final processing result:

```text
OVERALL: PASS
```

Open the PDF report for the SSD:

`Reports/<SERIAL_NUMBER>/report.pdf`

Confirm the health, overwrite, verification, and Opal results before identifying the SSD as sanitized and ready for resale.

### 5. Replace the SSD

1. Shut down Ubuntu.
2. Disconnect power.
3. Remove the processed SSD.
4. Install the next SSD.
5. Repeat the preflight and processing steps.

## Processing Results

| Result | Meaning |
|---|---|
| PASS | Health tests, logical sanitization, and Opal Revert succeeded. |
| CLEAR_ONLY | Logical sanitization succeeded, but Opal processing did not fully succeed. |
| FAIL | Required health testing or logical sanitization failed. |

Only an overall PASS indicates that the complete processing workflow succeeded.

The application records the logical overwrite and Opal operations separately.

## Reports

Generated reports are stored under:

`Reports/`

### Individual SSD Report

Each processed SSD receives a directory identified by its serial number.

```text
Reports/<SERIAL_NUMBER>/
├── report.pdf
├── execution.log
└── dd.log
```

**report.pdf**

Printable record of SSD identification, diagnostic results, sanitization operations, verification, and final status.

**execution.log**

Timestamped application processing events and error information.

**dd.log**

Output from the full logical-device overwrite operation.

### Processing Summary

`Reports/inventory.csv`

Contains the current processing results for SSDs handled by the application.

This is separate from the source inventory in `App/ssd_inventory.csv`.

### Opal Recovery Information

If Opal initialization occurs but processing does not complete successfully, the application may retain:

`Reports/<SERIAL_NUMBER>/opal_recovery.txt`

This file contains a temporary Opal administrator credential.

It is stored with restricted permissions and must not be included with an SSD being sold.

### Reprocessing an SSD

The application normally rejects an SSD that already has a processing report.

To deliberately reprocess that SSD:

```bash
sudo .venv/bin/python App/ssd_test.py --execute --retry
```

The existing per-SSD report directory is moved to:

`Reports/_archive/`

A new processing report is then generated.

## Troubleshooting

### SSD Not Detected

Example error:

```text
ERROR: Expected one onboard NVMe SSD; found 0
```

Check whether Ubuntu detects the SSD:

```bash
lsblk -o NAME,PATH,TYPE,SIZE,MODEL,TRAN
```

Then:

```bash
sudo nvme list
```

If the SSD does not appear in either command, investigate the SSD's installation or hardware condition.

The Python application cannot process an SSD that Ubuntu does not detect.

### Inventory Mismatch

Example error:

```text
ERROR: SSD serial/model does not match inventory
```

Verify the electronic serial number and model against:

`App/ssd_inventory.csv`

Correct any inventory error before processing.

### Existing Processing Record

Example error:

```text
ERROR: Existing processing record. Use --retry for deliberate reprocessing.
```

Review the existing report before deciding whether another processing attempt is necessary.

### SMART or Self-Test Failure

If an SSD fails a required health check or NVMe short self-test, review the reported error.

A failed SSD should not be listed as tested working.

### Opal Failure

If an Opal operation fails, review:

- `report.pdf`
- `execution.log`
- Any retained `opal_recovery.txt`

Do not assume that the Opal reset completed unless the report confirms it.

## Software Tests

Run the Python unit tests from the project root:

```bash
.venv/bin/python -m unittest discover -s Tests -v
```

The tests verify application functions, including:

- Inventory validation
- SMART health evaluation
- NVMe self-test result interpretation
- Mount detection
- Opal status interpretation
- Logical overwrite verification
- Result classification
- Report archiving
- CSV compatibility

Unit tests do not perform destructive operations on an SSD.

## Project Documentation

- `Docs/REQUIREMENTS.md` — Functional requirements and acceptance criteria.
- `Docs/ARCHITECTURE.md` — Application design, processing sequence, and implementation.
- `Docs/FOLDERS.md` — Project directory structure and responsibilities.
