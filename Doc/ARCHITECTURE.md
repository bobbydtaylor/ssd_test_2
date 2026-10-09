
# SSD Test and Sanitization — Architecture

## 1. Overview

A Python application running on Ubuntu performs NVMe SSD identification, diagnostics, secure erasure, verification, and reporting.

Processing begins only when manually initiated.

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

## 4. Processing Sequence

1. Operator manually starts the application.
2. Identify installed storage devices.
3. Identify the Ubuntu system drive.
4. Identify the NVMe test drive.
5. Read model, serial number, and capacity.
6. Check whether the SSD was previously processed.
7. Collect SMART information.
8. Evaluate SSD health.
9. Execute supported diagnostic self-tests.
10. Evaluate diagnostic results.
11. Determine the supported secure erase command.
12. Execute secure erase.
13. Verify erase completion.
14. Collect final SMART information.
15. Determine PASS, FAIL, or REVIEW status.
16. Save results and generate the printable report.
17. Exit.

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

The printable report format and generation method have not yet been selected.

## 10. Error Handling

- Stop processing on errors.
- Record failed operations.
- Preserve partial reports.
- Detect command timeouts.
- Do not automatically retry destructive operations.
- Do not erase an SSD already recorded as successfully processed.

## 11. Execution

- Operator manually starts `ssd_test.py` from Ubuntu.
- Application runs unattended after initiation.
- Application processes the installed NVMe SSD.
- Application saves the results and printable report.
- Application exits when processing finishes.
- No automatic startup service is used.

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
10. Test manually initiated unattended execution.

## 13. Design Principles

- Python standard library preferred.
- Linux utilities perform NVMe operations.
- Sequential processing.
- Local file-based reporting.
- No database.
- No GUI.
- No cloud dependencies.
- No unnecessary frameworks.
