
# SSD Testing and Sanitization — Requirements

## 1. Purpose

AllyTech LLC requires a manually started Ubuntu application to test, sanitize, verify, and document used NVMe SSDs recovered from client computers for resale.

## 2. Hardware and Scope

- Host: Lenovo ThinkCentre M910q Tiny running Ubuntu.
- System drive: internal SATA SSD.
- Test connection: onboard M.2 NVMe slot.
- Supported inventory: Samsung PM961 and PM981 SSDs.
- One test SSD per execution.
- USB adapters and SATA test drives are excluded.
- The source inventory is `App/ssd_inventory.csv`.

## 3. Functional Requirements

### Identification and Protection

- REQ-01: Start manually; do not start automatically at boot.
- REQ-02: Identify the installed NVMe SSD electronically by model, serial number, firmware revision, and capacity.
- REQ-03: Require the electronic serial number and model to match the source inventory.
- REQ-04: Reject missing, ambiguous, mounted, or otherwise active test drives.
- REQ-05: Exclude the Ubuntu system drive from all destructive operations.
- REQ-06: Revalidate target identity immediately before destructive processing.
- REQ-07: Support deliberate reprocessing while retaining prior test records.

### Health Testing

- REQ-08: Record initial NVMe SMART information.
- REQ-09: Execute an NVMe short self-test and verify its completed result.
- REQ-10: Reject SSDs that fail the required health acceptance criteria.
- REQ-11: Record final SMART information following sanitization.

### Sanitization

- REQ-12: Overwrite the entire host-accessible SSD capacity with zeros.
- REQ-13: Verify the entire host-accessible capacity by reading it back and comparing against zeros.
- REQ-14: Confirm TCG Opal 2.0 support before performing Opal operations.
- REQ-15: Establish Opal ownership using `sedutil-cli --initialSetup`.
- REQ-16: Execute `sedutil-cli --revertTPer` with the administrator password established during initialization.
- REQ-17: Confirm successful Opal Revert completion and inspect the resulting security state.
- REQ-18: Record logical overwrite and Opal Revert outcomes independently.
- REQ-19: Do not require a PSID for the established `initialSetup` and `revertTPer` workflow.
- REQ-20: Do not label a firmware reset as a validated NIST Purge without supporting technical evidence for the particular SSD implementation.

### Authentication and Recovery

- REQ-21: Generate a unique temporary Opal administrator password for each processing attempt.
- REQ-22: Preserve that password locally with restrictive filesystem permissions until Opal Revert completes.
- REQ-23: Do not include the administrator password in normal execution logs, PDF reports, or CSV results.
- REQ-24: Preserve recovery information when Opal initialization succeeds but Revert does not complete.

### Reporting

- REQ-25: Generate a printable PDF report for each processing attempt.
- REQ-26: Generate an execution log containing operations, results, timestamps, and failures.
- REQ-27: Maintain a CSV processing summary.
- REQ-28: Preserve prior reports when explicitly reprocessing a serial number.
- REQ-29: Record unsupported, incomplete, and failed operations accurately.

## 4. Acceptance Criteria

### Health PASS

- Inventory model and serial number match.
- NVMe critical warning equals zero.
- Media and data integrity errors equal zero.
- Available spare exceeds the reported threshold.
- NVMe short self-test completes successfully.
- Final SMART health checks pass.

### Logical Sanitization PASS

- The application writes exactly the reported logical capacity.
- No overwrite errors occur.
- A full-device readback finds no nonzero bytes.
- The number of verified bytes equals the logical capacity.

The achieved sanitization category is Clear.

### Opal Revert PASS

- Opal 2.0 is detected.
- `initialSetup` completes successfully.
- `revertTPer` completes successfully.
- The drive remains electronically identifiable.
- The post-operation Opal query succeeds.
- `Locked = N`, `LockingEnabled = N`, and `MBREnabled = N`.

A successful Opal reset is recorded as a firmware security operation. It does not independently establish NIST Purge.

### Overall Result

- PASS: Health, logical sanitization, and Opal Revert all pass.
- CLEAR_ONLY: Logical sanitization passes but Opal Revert does not complete successfully.
- FAIL: Required diagnostics or logical sanitization fail.
- INCOMPLETE: Processing is interrupted or cannot be fully evaluated.

A CLEAR_ONLY result must remain distinguishable from full workflow PASS.

## 5. Operation

1. Shut down Ubuntu and disconnect power.
2. Install one SSD in the onboard M.2 NVMe slot.
3. Boot Ubuntu.
4. Run the read-only application preflight.
5. Execute the application.
6. Review the processing result and PDF report.
7. Shut down before changing SSDs.

## 6. Constraints

- Only one onboard NVMe test SSD is permitted.
- Destructive operations require explicit `--execute`.
- All reports are stored on the Ubuntu SATA system drive.
- Processing is sequential.
- No cloud services, database, or graphical interface are required.
- No automatic retry of failed destructive operations.
- No automatic classification of Opal Revert as NIST Purge.
