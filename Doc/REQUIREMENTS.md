
# SSD Test and Sanitization — Requirements

## 1. Purpose

Automate testing and secure erasure of used NVMe SSDs recovered from retired computers for resale.

## 2. Hardware

- Computer: Lenovo ThinkCentre M910q Tiny
- Operating system: Ubuntu Linux
- System drive: Internal SATA SSD
- Test drive: M.2 NVMe SSD
- Initial inventory: 9 Samsung NVMe SSDs

## 3. Functional Requirements

- REQ-01: Process one NVMe SSD per execution.
- REQ-02: Automatically start processing when Ubuntu boots.
- REQ-03: Operate unattended without user interaction.
- REQ-04: Automatically identify the test SSD by model, serial number, and capacity.
- REQ-05: Protect the Ubuntu system drive from erasure.
- REQ-06: Collect SMART health information.
- REQ-07: Record power-on hours, percentage used, available spare, critical warnings, and media errors.
- REQ-08: Perform supported SSD diagnostic self-tests.
- REQ-09: Securely erase the SSD using a supported NVMe command.
- REQ-10: Verify successful completion of the erase operation.
- REQ-11: Verify SSD accessibility and health after erasure.
- REQ-12: Stop processing the current SSD when an operation fails.
- REQ-13: Generate a report for each SSD.
- REQ-14: Maintain a CSV inventory of processed SSDs.
- REQ-15: Record PASS, FAIL, or REVIEW status.
- REQ-16: Prevent repeated processing of previously completed SSDs.
- REQ-17: Save diagnostic results and error information.
- REQ-18: Support repeated operation with different SSDs without software reconfiguration.
- REQ-19: Generate a printable report for each SSD.
- REQ-20: Include SSD identification, tests performed, test results, and health information in the printable report.
- REQ-21: Document the secure erase method and completion status.
- REQ-22: Identify whether the SSD passed all required tests and was successfully securely erased.

## 4. Acceptance Criteria

An SSD receives PASS when:

- Device identification succeeds.
- SMART critical warnings equal zero.
- Media and data integrity errors equal zero.
- Available spare exceeds the manufacturer's threshold.
- Required diagnostic tests pass.
- Secure erase completes successfully.
- Post-erase verification succeeds.

An SSD receives FAIL when a required operation fails or a health acceptance criterion is not met.

An SSD receives REVIEW when required diagnostic information is unavailable or results are inconclusive.

## 5. Operating Procedure

1. Shut down the computer.
2. Install an NVMe SSD.
3. Start the computer.
4. Allow automatic processing to finish.
5. Review the result and printable report.
6. Shut down and replace the SSD.

## 6. Constraints

- One SSD processed at a time.
- Ubuntu system drive must never be erased.
- No user interaction during normal processing.
- No cloud connectivity required.
- Results stored locally on Ubuntu.
- SSD exchange performed with computer powered off.
