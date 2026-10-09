
# SSD Test and Sanitization — Architecture

## 1. Application

`App/ssd_test.py` runs under Python 3.14 on the Ubuntu Lenovo ThinkCentre M910q.

The application invokes Linux storage utilities through Python subprocesses. Processing starts manually and continues unattended.

## 2. Inputs

- `App/ssd_inventory.csv`: SSD model, serial number, capacity, and PSID.
- Electronic NVMe controller identification.
- `--execute`: Enables destructive operations. Without this argument, the application performs read-only preflight.

The electronic model and serial number must match the corresponding inventory record.

## 3. Dependencies

- `lsblk`: Device enumeration, mount detection, and system-drive exclusion.
- `nvme-cli`: Controller identification, SMART data, and NVMe self-tests.
- `blockdev`: Logical device capacity.
- `dd`: Full logical-device zero overwrite.
- Python binary file reads: Distributed zero verification.
- `sedutil-cli`: TCG Opal query and PSID Revert.
- `parted`: Partition-table inspection.
- `reportlab`: Printable PDF generation.

## 4. Processing Sequence

1. Identify the Ubuntu system drive and installed NVMe devices.
2. Exclude the system drive and reject ambiguous or mounted targets.
3. Read the target SSD's electronic model and serial number.
4. Match the SSD against `App/ssd_inventory.csv`.
5. Retrieve and validate the drive-specific PSID.
6. Check previous processing records.
7. Collect initial SMART data.
8. Execute and evaluate the NVMe short self-test.
9. Revalidate the target SSD.
10. Overwrite the complete host-accessible logical address space with zeros.
11. Verify distributed samples of overwritten logical storage.
12. Execute TCG Opal PSID Revert.
13. Verify firmware-reported PSID Revert completion.
14. Query the post-revert Opal security state.
15. Check drive accessibility and partition information.
16. Collect final SMART information.
17. Evaluate the overall result.
18. Generate the printable PDF report, execution log, and CSV results.
19. Exit.

## 5. Target Protection

- Identify the physical drive containing the Ubuntu root filesystem.
- Exclude that drive from destructive operations.
- Require exactly one NVMe test namespace.
- Reject mounted target partitions.
- Reject active swap on the target.
- Match electronic model and serial number against inventory.
- Revalidate the target before overwrite.
- Prevent repeated processing of completed SSDs.

## 6. Diagnostics

Collect:

- Model
- Serial number
- Firmware version
- Capacity
- Critical warnings
- Available spare
- Available spare threshold
- Percentage used
- Power-on hours
- Power cycles
- Media and data integrity errors
- NVMe short self-test result

## 7. Logical-Device Overwrite

Use `dd` to write zeros across the complete host-accessible logical capacity.

- Transfer block size: 16 MiB.
- Direct output I/O.
- Synchronize writes before completion.
- Record total bytes written and elapsed time.
- Treat unexpected I/O errors as failures.

Verify the overwrite by reading 32 distributed samples of 1 MiB each.

Record the number of samples, bytes checked, and verification result.

## 8. TCG Opal PSID Revert

Use `sedutil-cli`.

### Capability Query

Query the installed SSD and confirm TCG Opal support.

### PSID Selection

Read the SSD's electronic serial number and match it to `App/ssd_inventory.csv`.

Require a valid 32-character PSID.

### Revert

Execute the PSID Revert command using the matched PSID.

Require the response:

    revertTper completed successfully

### Post-Revert Verification

Verify:

- SSD remains accessible.
- Opal security information can be read.
- Locked state is disabled.
- Locking is disabled.
- SMART health information remains accessible.

Record the partition inspection result.

## 9. Result Classification

### PASS

All required diagnostics, zero overwrite, sample verification, PSID Revert, and post-revert checks succeed.

### FAIL

A required operation fails or a health acceptance criterion is not met.

## 10. Reporting

### CSV Inventory

`Reports/inventory.csv`

Maintain one processing-result record per SSD, including:

- Timestamp
- Serial number
- Model
- Capacity
- Final result
- Overwrite result
- Verification result
- PSID Revert result
- SMART health information

### Individual SSD Reports

`Reports/<SERIAL_NUMBER>/report.pdf`

Include:

- SSD identification
- Processing date
- SMART health information
- Diagnostic results
- Overwrite results
- Verification coverage and results
- PSID Revert result
- Post-revert security state
- Overall result

### Execution Log

`Reports/<SERIAL_NUMBER>/execution.log`

Record processing events, completion information, and errors.

## 11. Error Handling

- Stop destructive processing after a required operation fails.
- Preserve available diagnostic results.
- Record command failures and error information.
- Generate a failure report for processing errors.
- Do not automatically retry destructive operations.
- Do not automatically reprocess previously completed SSDs.

## 12. Execution

### Preflight

    sudo .venv/bin/python App/ssd_test.py

### Processing

    sudo .venv/bin/python App/ssd_test.py --execute

Commands execute from the repository root.

## 13. Implementation

- Python standard library for orchestration and CSV files.
- ReportLab for PDF generation.
- Sequential processing of one SSD.
- Local reporting.
- No automatic startup.
- No database or graphical interface.
