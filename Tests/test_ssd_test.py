
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "App" / "ssd_test.py"

spec = importlib.util.spec_from_file_location(
    "ssd_test", APP_PATH
)
ssd_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ssd_test)


class TestSSDInventory(unittest.TestCase):

    def test_valid_psid(self):
        self.assertTrue(
            ssd_test.valid_psid("A1B2C3D4" * 4)
        )

    def test_invalid_psid(self):
        self.assertFalse(ssd_test.valid_psid(""))
        self.assertFalse(ssd_test.valid_psid("ABC123"))
        self.assertFalse(
            ssd_test.valid_psid("INVALID-CHARACTERS-123456789012")
        )

    def test_inventory_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ssd_inventory.csv"

            with path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "serial", "model",
                    "capacity_gb", "psid"
                ])
                writer.writerow([
                    "TEST123",
                    "TEST-MODEL",
                    "256",
                    "A1B2C3D4" * 4
                ])

            inventory = ssd_test.load_inventory(path)

            self.assertIn("TEST123", inventory)
            self.assertEqual(
                inventory["TEST123"]["model"],
                "SAMSUNG TEST-MODEL"
            )
            self.assertEqual(
                inventory["TEST123"]["capacity_gb"],
                "256"
            )

    def test_duplicate_serial_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ssd_inventory.csv"

            path.write_text(
                "serial,model,capacity_gb,psid\n"
                "TEST123,MODEL,256,\n"
                "TEST123,MODEL,256,\n"
            )

            with self.assertRaises(RuntimeError):
                ssd_test.load_inventory(path)


class TestSSDHealth(unittest.TestCase):

    def test_healthy_drive(self):
        data = {
            "critical_warning": 0,
            "media_errors": 0,
            "avail_spare": 100,
            "spare_thresh": 10,
        }

        self.assertTrue(ssd_test.smart_ok(data))

    def test_media_errors(self):
        data = {
            "critical_warning": 0,
            "media_errors": 1,
            "avail_spare": 100,
            "spare_thresh": 10,
        }

        self.assertFalse(ssd_test.smart_ok(data))

    def test_critical_warning(self):
        data = {
            "critical_warning": 1,
            "media_errors": 0,
            "avail_spare": 100,
            "spare_thresh": 10,
        }

        self.assertFalse(ssd_test.smart_ok(data))

    def test_insufficient_spare(self):
        data = {
            "critical_warning": 0,
            "media_errors": 0,
            "avail_spare": 10,
            "spare_thresh": 10,
        }

        self.assertFalse(ssd_test.smart_ok(data))

    def test_missing_smart_fields(self):
        self.assertFalse(ssd_test.smart_ok({}))


class TestDeviceMounts(unittest.TestCase):

    def test_unmounted_disk(self):
        disk = {
            "name": "nvme0n1",
            "mountpoints": [None],
            "children": [
                {
                    "name": "nvme0n1p1",
                    "mountpoints": [None]
                }
            ]
        }

        self.assertEqual(
            list(ssd_test.tree_mounts(disk)),
            []
        )

    def test_mounted_partition(self):
        disk = {
            "name": "sda",
            "mountpoints": [None],
            "children": [
                {
                    "name": "sda2",
                    "mountpoints": ["/"]
                }
            ]
        }

        self.assertEqual(
            list(ssd_test.tree_mounts(disk)),
            ["/"]
        )


if __name__ == "__main__":
    unittest.main()
