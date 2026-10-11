
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "App" / "ssd_test.py"

spec = importlib.util.spec_from_file_location(
    "ssd_test", APP
)

ssd_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ssd_test)


class TestInventory(unittest.TestCase):

    def test_inventory_without_psid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "inventory.csv"

            path.write_text(
                "serial,model,capacity_gb,psid\n"
                "TEST123,MZVLW128HEGR-000L1,128,\n"
            )

            result = ssd_test.load_inventory(path)

            self.assertEqual(
                result["TEST123"]["model"],
                "SAMSUNG MZVLW128HEGR-000L1",
            )

            self.assertEqual(
                result["TEST123"]["psid"], ""
            )

    def test_duplicate_serial(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "inventory.csv"

            path.write_text(
                "serial,model,capacity_gb,psid\n"
                "TEST123,MODEL,256,\n"
                "TEST123,MODEL,256,\n"
            )

            with self.assertRaises(RuntimeError):
                ssd_test.load_inventory(path)

    def test_missing_model(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "inventory.csv"

            path.write_text(
                "serial,model,capacity_gb,psid\n"
                "TEST123,,256,\n"
            )

            with self.assertRaises(RuntimeError):
                ssd_test.load_inventory(path)

    def test_invalid_capacity(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "inventory.csv"

            path.write_text(
                "serial,model,capacity_gb,psid\n"
                "TEST123,MODEL,INVALID,\n"
            )

            with self.assertRaises(RuntimeError):
                ssd_test.load_inventory(path)

    def test_missing_columns(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "inventory.csv"

            path.write_text(
                "serial,model\n"
                "TEST123,MODEL\n"
            )

            with self.assertRaises(RuntimeError):
                ssd_test.load_inventory(path)


class TestHealth(unittest.TestCase):

    def setUp(self):
        self.healthy = {
            "critical_warning": 0,
            "media_errors": 0,
            "avail_spare": 100,
            "spare_thresh": 10,
        }

    def test_healthy(self):
        self.assertTrue(
            ssd_test.smart_ok(self.healthy)
        )

    def test_media_errors(self):
        data = dict(self.healthy)
        data["media_errors"] = 1

        self.assertFalse(
            ssd_test.smart_ok(data)
        )

    def test_critical_warning(self):
        data = dict(self.healthy)
        data["critical_warning"] = 1

        self.assertFalse(
            ssd_test.smart_ok(data)
        )

    def test_spare_threshold(self):
        data = dict(self.healthy)
        data["avail_spare"] = 10

        self.assertFalse(
            ssd_test.smart_ok(data)
        )

    def test_missing_fields(self):
        self.assertFalse(
            ssd_test.smart_ok({})
        )


class TestSelfTestParsing(unittest.TestCase):

    def test_pass(self):
        output = """
Current operation : 0
Current Completion: 0%
Self Test Result[0]:
    Operation Result : 0
    Self Test Code    : 1
"""
        self.assertTrue(
            ssd_test.parse_self_test(output)
        )

    def test_running(self):
        output = """
Current operation : 1
Current Completion: 50%
"""
        self.assertFalse(
            ssd_test.parse_self_test(output)
        )

    def test_failure(self):
        output = """
Current operation : 0
Self Test Result[0]:
    Operation Result : 5
    Self Test Code    : 1
"""
        with self.assertRaises(RuntimeError):
            ssd_test.parse_self_test(output)

    def test_wrong_test_code(self):
        output = """
Current operation : 0
Self Test Result[0]:
    Operation Result : 0
    Self Test Code    : 2
"""
        with self.assertRaises(RuntimeError):
            ssd_test.parse_self_test(output)


class TestMountDetection(unittest.TestCase):

    def test_unmounted(self):
        device = {
            "mountpoints": [None],
            "children": [
                {"mountpoints": [None]}
            ],
        }

        self.assertEqual(
            list(ssd_test.tree_mounts(device)),
            [],
        )

    def test_mounted(self):
        device = {
            "mountpoints": [None],
            "children": [
                {"mountpoints": ["/"]}
            ],
        }

        self.assertEqual(
            list(ssd_test.tree_mounts(device)),
            ["/"],
        )


class TestOpal(unittest.TestCase):

    def test_supported(self):
        text = """
LockingSupported = Y
MediaEncrypt = Y
OPAL 2.0 function (0x0203)
"""
        self.assertTrue(
            ssd_test.opal_capabilities(text)
        )

    def test_unsupported(self):
        self.assertFalse(
            ssd_test.opal_capabilities(
                "LockingSupported = N"
            )
        )

    def test_reset_state(self):
        text = """
Locked = N, LockingEnabled = N
MBRDone = N, MBREnabled = N
"""
        self.assertTrue(
            ssd_test.opal_reset_state(text)
        )

    def test_enabled_locking_rejected(self):
        text = """
Locked = N, LockingEnabled = Y
MBRDone = N, MBREnabled = N
"""
        self.assertFalse(
            ssd_test.opal_reset_state(text)
        )


class TestResultClassification(unittest.TestCase):

    def test_all_pass(self):
        self.assertEqual(
            ssd_test.classify_result(
                True, True, True
            ),
            "PASS",
        )

    def test_clear_only(self):
        self.assertEqual(
            ssd_test.classify_result(
                True, True, False
            ),
            "CLEAR_ONLY",
        )

    def test_failed_health(self):
        self.assertEqual(
            ssd_test.classify_result(
                True, False, True
            ),
            "FAIL",
        )

    def test_failed_clear(self):
        self.assertEqual(
            ssd_test.classify_result(
                False, True, True
            ),
            "FAIL",
        )

    def test_all_failed(self):
        self.assertEqual(
            ssd_test.classify_result(
                False, False, False
            ),
            "FAIL",
        )


class TestFullVerification(unittest.TestCase):

    def test_zero_device(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "device.bin"
            path.write_bytes(bytes(1024 * 1024))

            checked, elapsed = (
                ssd_test.verify_zeroes(
                    path,
                    path.stat().st_size,
                    lambda message: None,
                )
            )

            self.assertEqual(
                checked, 1024 * 1024
            )
            self.assertGreaterEqual(elapsed, 0)

    def test_nonzero_device(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "device.bin"

            path.write_bytes(
                bytes(512) + b"\x01" + bytes(512)
            )

            with self.assertRaises(RuntimeError):
                ssd_test.verify_zeroes(
                    path,
                    path.stat().st_size,
                    lambda message: None,
                )

    def test_short_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "device.bin"
            path.write_bytes(bytes(100))

            with self.assertRaises(RuntimeError):
                ssd_test.verify_zeroes(
                    path,
                    200,
                    lambda message: None,
                )


class TestRecoveryCredential(unittest.TestCase):

    def test_create_recovery_password(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)

            path = ssd_test.save_recovery_password(
                folder, "test-password"
            )

            self.assertEqual(
                path.read_text(),
                "test-password\n",
            )

            self.assertEqual(
                path.stat().st_mode & 0o777,
                0o600,
            )

    def test_no_credential_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)

            ssd_test.save_recovery_password(
                folder, "first"
            )

            with self.assertRaises(FileExistsError):
                ssd_test.save_recovery_password(
                    folder, "second"
                )


class TestArchiving(unittest.TestCase):

    def test_archive_existing_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            with patch.object(
                ssd_test, "REPORTS", root
            ):
                source = root / "SERIAL123"
                source.mkdir()

                (source / "report.pdf").write_text(
                    "previous report"
                )

                ssd_test.archive_existing(
                    "SERIAL123"
                )

                self.assertFalse(
                    source.exists()
                )

                files = list(
                    (root / "_archive").glob(
                        "SERIAL123_*/report.pdf"
                    )
                )

                self.assertEqual(len(files), 1)
                self.assertEqual(
                    files[0].read_text(),
                    "previous report",
                )


class TestCsvCompatibility(unittest.TestCase):

    def test_old_inventory_format(self):
        existing = [
            {
                "timestamp": "2026-10-10",
                "serial": "OLD123",
                "model": "SAMSUNG TEST",
                "capacity_bytes": "256000000000",
                "status": "PASS",
                "zero_overwrite": "PASS",
                "sample_verification": "PASS",
                "psid_revert": "PASS",
            }
        ]

        new_result = {
            "timestamp": "2026-10-11",
            "serial": "NEW456",
            "model": "SAMSUNG TEST2",
            "status": "PASS",
        }

        rows = ssd_test.merge_inventory_rows(
            existing,
            new_result,
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[0]["serial"], "OLD123"
        )
        self.assertEqual(
            rows[1]["serial"], "NEW456"
        )
        self.assertEqual(
            rows[0]["status"], "PASS"
        )

    def test_reprocessing_updates_summary(self):
        existing = [
            {
                "serial": "SAME123",
                "status": "FAIL",
            }
        ]

        new_result = {
            "serial": "SAME123",
            "status": "PASS",
        }

        rows = ssd_test.merge_inventory_rows(
            existing,
            new_result,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["status"], "PASS"
        )


if __name__ == "__main__":
    unittest.main()
