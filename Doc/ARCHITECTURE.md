
# SSD Test and Sanitization — Architecture

## 1. Overview

A Python application running on Ubuntu automates NVMe SSD identification, diagnostics, secure erasure, verification, and reporting.

## 2. Platform

- Computer: Lenovo ThinkCentre M910q Tiny
- Operating system: Ubuntu Linux
- Python: 3.14
- Development environment: VS Code
- Python virtual environment: `.venv`
- System storage: SATA SSD
- Test storage: M.2 NVMe SSD

## 3. Software

### Python Application

`ssd_test.py`

Controls the processing sequence, executes Linux utilities, evaluates results, and generates reports.

### Linux Utilities

- `lsblk` — Identify block devices.
- `nvme-cli` — NVMe identification, SMART information, diagnostics, and secure erase.
- `smartmontools` — SMART diagnostics and SSD self-tests.
- `systemd` — Automatic startup.

## 4. Processing Sequence

1. Identify installed storage devices.
2. Identify the Ubuntu system drive.
3. Identify the NVMe test drive.
4. Read model, serial number, and capacity.
5. Check whether the SSD was previously processed.
6. Collect SMART information.
7. Evaluate SSD health.
8. Execute supported diagnostic self-tests.
9. Evaluate diagnostic results.
10. Determine the supported secure erase command.
11. Execute secure erase.
12. Verify erase completion.
13. Collect final SMART information.
14. Determine PASS, FAIL, or REVIEW status.
15. Save results and generate printable report.
16. Exit.

## 5. System Drive Protection

- Identify the physical drive containing Ubuntu.
- Exclude the system drive from destructive commands.
- Reject ambiguous target configurations.
- Verify the test drive identity before erasure.
- Reject mounted target filesystems.

## 6. SSD Sanitization

Use `nvme-cli` to identify supported secure erase capabilities.

Supported methods may include:

- NVMe Sanitize
- NVMe Format with secure erase

Select the applicable command based on the drive's reported capabilities.

Confirm completion using the NVMe controller's reported status.

## 7. Diagnostics

Collect:

- Manufacturer
- Model number
- Serial number
- Capacity
- Firmware version
- Power-on hours
- Power cycles
- Percentage used
- Available spare
- Critical warnings
- Media and data integrity errors
- Diagnostic self-test results

## 8. Result Classification

### PASS

Required diagnostics, health checks, erasure, and verification succeed.

### FAIL

A required operation fails or a health criterion is not met.

### REVIEW

Required diagnostic information is unavailable or a result is inconclusive.

## 9. Reporting

### CSV Inventory

Maintain a CSV file with one record per SSD containing:

- Timestamp
- Model
- Serial number
- Capacity
- Power-on hours
- Percentage used
- Media errors
- Diagnostic result
- Secure erase result
- Overall status

### Individual SSD Report

Generate a printable report for each SSD containing:

- Manufacturer and model
- Serial number
- Capacity
- Firmware version
- Test date
- SMART health information
- Diagnostic tests performed
- Individual test results
- Secure erase method
- Secure erase completion status
- Overall PASS, FAIL, or REVIEW status

### Report Storage

Store reports and diagnostic logs on the Ubuntu SATA system drive.

The printable report format and generation method are not yet selected.

## 10. Error Handling

- Stop processing on errors.
- Record failed operations.
- Preserve partial reports.
- Detect command timeouts.
- Do not automatically retry destructive operations.
- Do not erase an SSD already recorded as successfully processed.

## 11. Execution

### Development

Run `ssd_test.py` manually from the VS Code terminal.

### Production

A `systemd` service starts `ssd_test.py` automatically when Ubuntu boots.

The application processes the installed NVMe SSD and exits when finished.

## 12. Implementation Sequence

1. Implement NVMe device discovery.
2. Implement system drive protection.
3. Implement SMART data collection.
4. Implement SSD diagnostics.
5. Implement secure erase.
6. Implement post-erase verification.
7. Implement CSV reporting.
8. Implement printable SSD reports.
9. Validate complete operation.
10. Configure automatic startup.
11. Test unattended execution.

## 13. Design Principles

- Python standard library preferred.
- Linux utilities perform NVMe operations.
- Sequential processing.
- Local file-based reporting.
- No database.
- No GUI.
- No cloud dependencies.
- No unnecessary frameworks.
