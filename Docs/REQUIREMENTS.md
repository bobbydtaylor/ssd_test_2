# SSD Test and Sanitization — Requirements

## 1. Purpose

Automate testing and sanitization of used NVMe SSDs recovered from DMK computers for resale.

## 2. Hardware

- Host: Lenovo ThinkCentre M910q Tiny running Ubuntu Linux
- Ubuntu system drive: SATA SSD
- Test drive: one M.2 NVMe SSD
- Initial inventory: nine Samsung NVMe SSDs

## 3. Functional Requirements

- REQ-01: Start processing manually; continue unattended after initiation.
- REQ-02: Identify the installed SSD by model, serial number, firmware version, and capacity.
- REQ-03: Select the drive-specific PSID from a local inventory by electronic serial number.
- REQ-04: Refuse destructive operations unless the serial number, model, and 32-character PSID are present and consistent with the inventory.
- REQ-05: Exclude the Ubuntu system drive from destructive operations.
- REQ-06: Refuse an ambiguous or mounted target or one used as swap.
- REQ-07: Record initial SMART health and conduct an NVMe short self-test.
- REQ-08: Overwrite all host-accessible logical storage with zeros.
- REQ-09: Verify zero overwrite using read-back samples distributed across the device; record the amount verified.
- REQ-10: Execute TCG Opal PSID Revert after overwrite verification.
- REQ-11: Check PSID Revert reported completion and post-revert security state.
- REQ-12: Record post-revert SMART information and partition inspection.
- REQ-13: Produce a printable PDF report and processing log for each SSD.
- REQ-14: Maintain a CSV summary of processed SSDs.
- REQ-15: Record PASS or FAIL with reasons. Refuse unknown or unsupported configurations.
- REQ-16: Do not automatically reprocess a serial number with an existing report.
- REQ-17: Do not start at boot.

## 4. Acceptance Criteria

PASS requires:

- Device model and serial match the inventory.
- SMART critical warnings and media errors are zero, and available spare exceeds threshold.
- NVMe short self-test passes.
- Complete host-visible zero overwrite succeeds.
- Distributed zero read-back samples pass.
- TCG Opal PSID Revert reports success.
- Post-revert device remains accessible and Opal locking is disabled.
- Final SMART health checks pass.

## 5. Operation

1. Install one SSD with power off.
2. Boot Ubuntu and manually start the application.
3. Allow the diagnostic, overwrite, verification, and PSID Revert sequence to finish.
4. Review the PDF report and exchange the SSD after shutdown.

## 6. Constraints

- One NVMe SSD per run.
- Drive-specific PSIDs must be confirmed in the inventory.
- The system drive must never be an erase target.
- Reports and inventory remain on the Ubuntu SATA system drive.