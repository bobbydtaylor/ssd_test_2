
# SSD Testing and Sanitization — Architecture

## 1. Overview

`App/ssd_test.py` is a Python application running on the AllyTech LLC Ubuntu test workstation.

The application uses standard Linux utilities to test and sanitize one SSD connected to the onboard M.2 NVMe slot.

Processing is sequential and manually initiated.

## 2. Inputs

- `App/ssd_inventory.csv`: Source inventory with serial number, model, capacity, and optional PSID.
- NVMe controller identity.
- NVMe SMART information.
- TCG Opal capabilities.
- `--execute`: Enables destructive processing.
- `--retry`: Permits explicit reprocessing of an SSD with an existing report.

The PSID inventory field is retained for historical reference but is not required by the current sanitization method.

## 3. Dependencies

- `lsblk`: Detect installed drives and mounted filesystems.
- `swapon`: Identify active swap.
- `nvme-cli`: Obtain identity, SMART, and self-test information.
- `blockdev`: Determine logical device size.
- `dd`: Overwrite the complete logical address space.
- Python binary reads: Verify the complete zero overwrite.
- `sedutil-cli`: Perform TCG Opal initialization, Revert, and security-state queries.
- `parted`: Inspect the resulting partition table.
- `reportlab`: Generate PDF reports.

## 4. Target Selection

The application:

1. Enumerates block devices.
2. Identifies the Ubuntu system drive by its mounted filesystems.
3. Requires exactly one onboard NVMe namespace.
4. Rejects the target if it belongs to the system drive.
5. Rejects mounted target partitions.
6. Rejects target swap usage.
7. Verifies the NVMe controller device exists.
8. Reads the controller's electronic identity.
9. Matches model and serial against inventory.

The selected device is reidentified before destructive processing.

## 5. Diagnostics

Collect NVMe SMART information before processing.

Health acceptance requires:

- Critical warning = 0.
- Media errors = 0.
- Available spare greater than the spare threshold.

Run the NVMe short self-test.

Poll the self-test log until the operation completes. Evaluate the latest result entry and require:

- Operation Result = 0.
- Self Test Code = 1.

A timeout or unsupported test is a diagnostic failure.

## 6. Complete Logical Overwrite

Write zeros across the entire host-accessible logical address space.

Use:

- `dd`
- 16 MiB transfer blocks
- Direct output I/O
- Exact byte count
- Write synchronization

Require successful completion.

Record the logical bytes written and duration.

## 7. Full Readback Verification

Read the complete logical address space sequentially using Python.

- Read in bounded chunks.
- Confirm the number of bytes read equals the device capacity.
- Reject any nonzero byte.
- Reject short reads and I/O errors.

Record the total verified bytes and elapsed time.

This establishes the result of the logical overwrite independently of the `dd` command result.

## 8. TCG Opal Processing

### 8.1 Capability Check

Run:

    sedutil-cli --query <device>

Require the Opal 2.0 capability and relevant security features.

### 8.2 Temporary Administrator Credential

Generate a random temporary administrator password.

Before modifying the SSD's Opal configuration, write the credential to a local recovery file with owner-only access.

Recovery credentials are excluded from the PDF report, CSV, and ordinary execution log.

### 8.3 Initialize Opal

Run:

    sedutil-cli --initialSetup <password> <device>

Require the initialization completion response.

Record the result.

### 8.4 Revert Opal

Run:

    sedutil-cli --revertTPer <password> <device>

Require:

    revertTper completed successfully

Do not run PSID Revert as part of the standard workflow.

### 8.5 Post-Revert Verification

Run another Opal query.

Require:

- `Locked = N`
- `LockingEnabled = N`
- `MBREnabled = N`

Confirm the SSD's model and serial number have not changed.

Inspect the partition table and record the observation.

Do not use the absence of a partition table as the sole evidence of sanitization.

Remove the temporary recovery credential only after successful Revert and verification.

If initialization succeeds but Revert fails, retain the recovery credential for controlled manual recovery.

## 9. Result Classification

### PASS

All health, overwrite, full-readback, and Opal operations pass.

### CLEAR_ONLY

Health and full logical sanitization pass, but Opal processing does not complete successfully.

### FAIL

Health testing or logical overwrite/verification fails.

### INCOMPLETE

The process is interrupted or an essential result cannot be determined.

The achieved sanitization category is recorded independently from the overall workflow result.

The application does not claim NIST Purge solely from `revertTPer` success.

## 10. Reporting

### Source Inventory

    App/ssd_inventory.csv

This file remains unchanged by processing.

### Current SSD Report

    Reports/<SERIAL>/report.pdf
    Reports/<SERIAL>/execution.log

### Processing Summary

    Reports/inventory.csv

One current result per serial number.

### Historical Reports

When `--retry` is explicitly used, existing files for that serial number are archived under:

    Reports/_archive/<SERIAL>_<TIMESTAMP>/

Previous reports must not be silently overwritten.

### Opal Recovery Credential

When required:

    Reports/<SERIAL>/opal_recovery.txt

This file is not part of the normal resale documentation.

It must have restrictive filesystem permissions.

## 11. Error Handling

- Do not continue to another destructive operation after a failed required step.
- Preserve results already established.
- Record command errors without exposing Opal passwords.
- Generate an error report whenever sufficient target identification is available.
- Do not automatically retry destructive operations.
- Allow explicit reprocessing through `--retry`.
- Preserve the temporary Opal credential when recovery may be required.

## 12. Execution

Preflight:

    sudo .venv/bin/python App/ssd_test.py

Full processing:

    sudo .venv/bin/python App/ssd_test.py --execute

Explicit reprocessing:

    sudo .venv/bin/python App/ssd_test.py --execute --retry

Run commands from the repository root.

## 13. Implementation Constraints

- Python standard library for orchestration.
- ReportLab for PDF reports.
- Native NVMe interface only.
- One SSD per execution.
- No automatic startup.
- No GUI, database, network access, or cloud dependency.
