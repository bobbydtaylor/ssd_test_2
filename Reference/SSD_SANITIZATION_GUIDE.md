
# SSD Sanitization and Resale Guide

**Organization:** AllyTech LLC  
**Document Type:** Engineering Reference  
**Scope:** Client SSDs recovered from decommissioned computers

## 1. Purpose

Establish industry practices for testing, sanitizing, verifying, and preparing used SSDs for resale.

The process must protect client information, establish drive condition, and produce a traceable record of the work performed.

## 2. Applicable Standards

### NIST SP 800-88 Revision 2

*Guidelines for Media Sanitization*, September 2025.

NIST defines three sanitization categories:

| Category | Description |
|---|---|
| Clear | Makes data recovery infeasible through the normal device interface using an approved technique. |
| Purge | Makes data recovery infeasible using more advanced recovery techniques. |
| Destroy | Physically renders the storage media unusable and the data unrecoverable to the required level of assurance. |

For SSDs transferred outside the client's control, Purge is the preferred objective when required by the client's information sensitivity and disposition policy.

NIST SP 800-88 Rev. 2 references IEEE 2883 and other approved technical standards for selecting specific sanitization techniques.

### IEEE 2883

*IEEE Standard for Sanitizing Storage.*

Provides technical sanitization requirements for storage devices, including solid-state media.

### NVM Express Specifications

Define NVMe controller commands, including Format NVM and Sanitize.

### Trusted Computing Group (TCG)

Defines storage security specifications, including Opal, which supports security management and certain cryptographic erase operations.

## 3. SSD Storage Characteristics

SSDs use NAND flash memory managed by an internal controller.

The controller performs:

- **Wear leveling:** Distributes writes across memory cells.
- **Overprovisioning:** Reserves flash capacity unavailable through normal operating-system access.
- **Bad-block management:** Replaces defective or worn memory blocks.
- **Garbage collection:** Reorganizes stored information and reclaims blocks.

A complete overwrite of the address space visible to Ubuntu does not guarantee that previously written information in inaccessible NAND blocks has been erased.

Controller-supported sanitization techniques are preferred when they meet the required sanitization category.

## 4. Sanitization Methods

### 4.1 NVMe Sanitize

NVMe Sanitize is a controller-managed operation.

Depending on the SSD, available actions include:

| Action | Operation |
|---|---|
| Block Erase | Erases NAND flash blocks. |
| Crypto Erase | Invalidates encryption keys protecting stored data. |
| Overwrite | Performs a controller-managed overwrite operation. |

**Requirements:**

- The SSD must support the selected operation.
- The connection must permit the command.
- Completion status must be checked.
- The sanitization result must be verified and validated.

An accepted command does not establish successful completion.

### 4.2 NVMe Format Secure Erase

The NVMe Format command supports Secure Erase Settings (SES).

| Setting | Operation |
|---|---|
| SES=0 | Format without a secure erase request. |
| SES=1 | User Data Erase. |
| SES=2 | Cryptographic Erase. |

SES=1 requests that the controller erase user data using its supported implementation.

SES=2 requests cryptographic erasure by invalidating the applicable encryption key.

The selected operation must be supported by the SSD and accessible through the connection.

### 4.3 TCG Opal PSID Revert

TCG Opal-capable SSDs can support a PSID Revert operation.

The PSID is a device-specific identifier generally printed on the physical SSD label.

PSID Revert resets the drive's TCG security state.

Where the device implementation provides suitable cryptographic key replacement, the operation may qualify as cryptographic sanitization.

**Requirements:**

- Confirm TCG Opal support.
- Match the SSD serial number to its recorded PSID.
- Execute PSID Revert using a compatible interface.
- Confirm successful completion.
- Confirm the resulting Opal security state.
- Establish whether the manufacturer's implementation supports the required sanitization category.

A successful PSID Revert is not automatically proof of NIST Purge compliance.

### 4.4 Full Logical Overwrite

A logical overwrite writes a known pattern, normally zeros, across the SSD's entire host-accessible address space.

**Procedure:**

1. Determine the device capacity.
2. Write zeros across the entire logical address space.
3. Confirm the expected number of bytes was written.
4. Verify selected samples or the complete logical address space.
5. Record the results.

A complete verified overwrite provides evidence of logical clearing.

It does not establish that inaccessible NAND blocks were erased.

Additional overwrite passes do not eliminate this limitation.

### 4.5 Physical Destruction

Physical destruction is used when:

- The SSD cannot be sanitized to the required level.
- The SSD is defective and cannot be adequately sanitized.
- The client's disposal policy requires destruction.

The destruction technique must address the NAND storage components and meet the applicable destruction requirements.

A drive designated for destruction must not be resold.

## 5. Selecting the Sanitization Method

The method must be selected using the required sanitization category, SSD capabilities, manufacturer documentation, and available command interface.

| Method | Typical Capability | Principal Limitation |
|---|---|---|
| NVMe Sanitize | Controller-managed sanitization | Requires command and device support |
| NVMe Format SES=1 | Controller-managed user data erase | Implementation-dependent |
| NVMe Format SES=2 | Cryptographic erase | Requires suitable encryption and key handling |
| TCG Opal PSID Revert | Security reset; possible cryptographic erase | Requires verified encryption/key-reset behavior |
| Full logical overwrite | Logical clearing | Cannot address inaccessible NAND |
| Physical destruction | Permanent disposal | SSD cannot be resold |

**Preferred selection order:**

1. Supported, validated firmware-level sanitization appropriate to the required category.
2. Verified cryptographic sanitization where applicable.
3. Full logical overwrite when Clear satisfies the client requirements.
4. Physical destruction when the required category cannot be achieved.

Method selection must not rely solely on an advertised capability. Actual command support and successful execution must be established.

## 6. SSD Health Testing

### 6.1 Identification

Record:

- Manufacturer
- Model
- Serial number
- Firmware revision
- Capacity
- Interface and connection type

Use the serial number to associate the physical device with its inventory entry and test report.

### 6.2 SMART Assessment

For NVMe SSDs, evaluate:

| Parameter | Engineering Significance |
|---|---|
| Critical Warning | Controller-reported critical condition |
| Available Spare | Remaining spare capacity |
| Available Spare Threshold | Manufacturer-defined warning threshold |
| Percentage Used | Estimated endurance consumption |
| Media and Data Integrity Errors | Unrecovered data-integrity errors |
| Power-On Hours | Accumulated operating time |
| Unsafe Shutdowns | Unclean power-loss events |
| Error Information Log | Controller and command errors |

The error log must be interpreted by error type.

Invalid command errors, for example, do not necessarily indicate NAND failure.

Percentage Used is an endurance estimate, not a direct measurement of remaining service life.

### 6.3 Device Self-Test

Run an NVMe short self-test when supported.

Record:

- Whether the test started.
- Whether it completed.
- The final result code.
- Any reported failure.

A command that successfully starts a self-test is not evidence that the test passed.

### 6.4 Read Test

Read the accessible logical address space to identify I/O errors.

A full-device read test provides more complete coverage than sampling.

Record the bytes read and any errors.

### 6.5 Health Acceptance

Assign one of three results:

| Result | Criteria |
|---|---|
| PASS | All required health checks completed successfully |
| FAIL | One or more required checks failed |
| INCOMPLETE | Required testing could not be completed |

A specific health acceptance policy must define which SMART conditions and diagnostic failures cause rejection.

## 7. Sanitization Verification and Validation

NIST distinguishes verification from validation.

**Verification:** Confirm that the selected sanitization operation completed successfully.

**Validation:** Determine whether the operation achieved the required sanitization objective.

### 7.1 Firmware-Level Operations

Verification may include:

- Successful command result.
- Controller-reported completion.
- Final sanitization status.
- TCG security-state information.
- Relevant manufacturer-defined status information.

Validation must account for the selected technique and the SSD's documented implementation.

### 7.2 Logical Overwrite

A zero overwrite can be checked through:

- **Sampling:** Read selected locations and compare them against zeros.
- **Full comparison:** Read every host-accessible logical byte and compare against zeros.

Sampling verifies only the locations examined.

Full comparison verifies the accessible logical address space.

### 7.3 Cryptographic Erase

Cryptographic erase is validated using evidence that the required cryptographic keys were properly invalidated or replaced and that the technique is appropriate for the device.

A zero-filled logical address space is not a necessary result of cryptographic erase.

### 7.4 Failure Criteria

Sanitization is unsuccessful or incomplete if:

- The required command fails.
- Completion cannot be established.
- Verification fails.
- Validation does not support the required sanitization category.

Such drives must be held for additional processing or designated for destruction.

## 8. USB-to-NVMe Adapters

USB adapters typically present an NVMe SSD to Ubuntu as a SCSI-style block device, such as `/dev/sdb`.

Native NVMe drives generally appear as `/dev/nvme0n1`.

Command availability depends on the adapter controller and its firmware.

| Operation | USB Adapter Dependency |
|---|---|
| Logical read/write | Generally available |
| SMART retrieval | Requires compatible passthrough |
| NVMe self-test | Requires compatible passthrough |
| NVMe Format | Requires supported administrative command access |
| NVMe Sanitize | Requires supported administrative command access |
| TCG Opal operations | Requires compatible security command passthrough |

Successful SMART or TCG Opal queries do not establish support for destructive commands.

Adapter compatibility should be evaluated using the actual SSD models and operations required by the workflow.

## 9. Automated Processing

The AllyTech LLC application should perform the following sequence:

1. Detect connected SSDs.
2. Identify the intended target.
3. Match the SSD against inventory by serial number and model.
4. Confirm the target is not the operating-system drive and is not mounted or otherwise in use.
5. Collect identification and initial SMART data.
6. Execute supported diagnostics.
7. Select an approved sanitization technique.
8. Execute sanitization.
9. Verify successful completion.
10. Validate the sanitization result.
11. Collect final device health information.
12. Generate a report.
13. Update the inventory and disposition status.

After target confirmation, processing should proceed unattended whenever supported by the hardware.

Failed operations must be recorded without producing a passing disposition.

## 10. Reporting

Each processed SSD requires a separate report.

### Identification

- Client or source asset
- SSD manufacturer and model
- Serial number
- Firmware
- Capacity
- Connection type
- Processing date

### Health Results

- Initial SMART measurements
- Device self-test result
- Read-test result, if performed
- Final SMART measurements
- Overall health result

### Sanitization Results

- Required category: Clear, Purge, or Destroy
- Selected technique
- Software utility and version
- Start and completion timestamps
- Execution result
- Verification method and result
- Validation result
- Errors or exceptions

### Disposition

- Approved for resale
- Additional testing required
- Additional sanitization required
- Rejected
- Designated for destruction

Reports must identify unsupported and unperformed tests rather than assigning them passing results.

A PDF report supports individual device documentation.

A CSV inventory supports consolidated tracking.

## 11. Chain of Custody

Maintain records connecting:

1. Client or source computer.
2. Physical SSD serial number.
3. Receipt or removal date.
4. Processing operator.
5. Sanitization and test results.
6. Final disposition.

This permits a specific SSD to be traced from client hardware removal through resale or destruction.

## 12. Resale Preparation

Release an SSD for resale only when:

- The client has authorized disposition.
- Sanitization satisfies the required category.
- Required health tests have passed.
- Verification and validation are complete.
- The processing report is retained.
- Inventory records show approval for resale.

Record the following information for resale listings:

- Manufacturer
- Model number
- Capacity
- Form factor
- Interface
- Used condition
- Relevant SMART information
- Completed test results

Do not represent a drive as having completed tests that were not performed.

## 13. Engineering Records

Maintain a record for every SSD processing attempt, including unsuccessful attempts.

The record should include the software version and actual operations performed.

A formal Certificate of Sanitization may be generated when required by the client.

The certificate must describe the sanitization technique, verification, validation, and final disposition accurately.

## 14. References

**NIST SP 800-88 Revision 2**  
Guidelines for Media Sanitization, September 2025  
https://doi.org/10.6028/NIST.SP.800-88r2

**IEEE 2883**  
IEEE Standard for Sanitizing Storage  
https://standards.ieee.org/

**NVM Express**  
NVMe Specifications  
https://nvmexpress.org/specifications/

**Trusted Computing Group**  
TCG Storage and Opal Specifications  
https://trustedcomputinggroup.org/

**Linux NVMe CLI**  
https://github.com/linux-nvme/nvme-cli

**sedutil**  
https://github.com/Drive-Trust-Alliance/sedutil
