
# DMK SSD Testing and Sanitization

Python application for testing, overwriting, sanitizing, and documenting used NVMe SSDs recovered from DMK computers.

The application starts manually and processes one SSD unattended.

## Platform

- Lenovo ThinkCentre M910q Tiny
- Ubuntu Linux
- Python 3.14
- M.2 NVMe test SSD
- Internal SATA system SSD

## Installation

Install Linux dependencies:

```bash
sudo apt update
sudo apt install nvme-cli sedutil smartmontools parted util-linux
```

Install Python dependencies from the repository root:

```bash
.venv/bin/python -m pip install -r App/requirements.txt
```

## SSD Inventory

Source inventory:

`App/ssd_inventory.csv`

The inventory contains the electronic serial number, model, capacity, and PSID for each SSD.

The application matches the installed SSD against this inventory before processing.

An SSD without a recorded valid PSID cannot complete the PSID Revert procedure.

## Operation

1. Shut down Ubuntu.
2. Install the SSD in the M.2 NVMe slot.
3. Boot Ubuntu.
4. Open a terminal in the project root.
5. Run the read-only preflight.
6. Start the full processing operation.
7. Review the report after completion.
8. Shut down and replace the SSD.

### Preflight

```bash
sudo .venv/bin/python App/ssd_test.py
```

### Start Processing

```bash
sudo .venv/bin/python App/ssd_test.py --execute
```

Processing includes:

1. SSD identification and inventory matching.
2. SMART diagnostics.
3. NVMe short self-test.
4. Full logical-device zero overwrite.
5. Distributed overwrite verification.
6. TCG Opal PSID Revert.
7. Post-revert checks.
8. PDF and CSV report generation.

## Reports

Results are stored in:

`Reports/`

The summary CSV is:

`Reports/inventory.csv`

Each SSD receives:

```text
Reports/<SERIAL_NUMBER>/
├── report.pdf
└── execution.log
```

## Software Tests

Run from the repository root:

```bash
.venv/bin/python -m unittest discover -s Tests -v
```

## Documentation

- `Docs/REQUIREMENTS.md`
- `Docs/ARCHITECTURE.md`
- `Docs/FOLDERS.md`
