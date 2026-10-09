# DMK SSD Testing

Manually started, unattended SSD diagnostics, logical zero overwrite, TCG Opal PSID Revert, and printable PDF reporting.

## Install (Ubuntu)

    sudo apt update
    sudo apt install nvme-cli sedutil smartmontools parted util-linux
    .venv/bin/python -m pip install -r requirements.txt

## Inventory

`ssd_inventory.csv` has nine devices. Six PM961 PSIDs were transcribed from the supplied close-up photographs, along with the previously validated PM981 PSID. Empty PSID fields block destructive actions. The PM961 with serial S35ENX0J499755 requires a clearer PSID transcription. The 128GB Samsung drive has no printed PSID in the supplied photo.

## Run

Verify detection and inventory match without modifying the drive:

    sudo .venv/bin/python ssd_test.py

Begin unattended testing and erase:

    sudo .venv/bin/python ssd_test.py --execute

The Ubuntu system drive is excluded. Reports are written to `reports/`.

## Test application logic

    .venv/bin/python -m unittest discover -s tests -v