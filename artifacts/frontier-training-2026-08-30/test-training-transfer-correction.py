"""Targeted v2 host-correction checks; never call plan, send, SSH or Slurm."""
import ast
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ARCHIVE = Path(__file__).absolute().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ARCHIVE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline = load("preserved_transfer_tests", "test-training-transfer-observer.py")
v2 = load("corrected_receiver", "transfer-frontier-training-remote-v2.py")
client = load("corrected_client", "transfer-frontier-training-correction.py")
# Reuse the unchanged receiver contract tests against the new receiver only.
# This does not modify the original test/helper files or any real payload.
baseline.r = v2


class CorrectedTransport(unittest.TestCase):
    def test_actual_approval_failure_probe_and_bundle_inventory_join(self):
        inventory, descriptors, diagnostic = client.context()
        self.assertEqual(inventory["file_count"], 954)
        self.assertEqual(diagnostic["status"], "read-only-control-check-passed")
        record = client.plan_record(inventory, descriptors, diagnostic, "2026-08-30T03:00:00Z")
        self.assertEqual(record["original_bundle"], {"path": "transfer-01/bundle.bin", **client.BUNDLE})
        self.assertEqual(record["current_receiver"]["sha256"], client.RECEIVER_SHA)
        self.assertEqual(inventory["remote_helper_sha256"], client.PINS["transfer-frontier-training-remote.py"])
        self.assertNotEqual(inventory["remote_helper_sha256"], record["current_receiver"]["sha256"])
        self.assertTrue(record["original_inventory_helper_pins_are_historical"])

    def test_failed_diagnostic_cannot_be_relabelled_ready_even_with_new_raw_pin(self):
        name = "transfer-receiver-corrected-probe-01.json"
        original_read = client.t.read_file
        outer = client.r.decode(original_read(ARCHIVE / name))
        inner = client.r.decode(outer["stdout"].encode())
        inner["parent_directory_opened"] = False
        outer["stdout"] = client.r.canonical(inner).decode()
        changed = client.r.canonical(outer)
        def read(path, *args, **kwargs):
            return changed if path == ARCHIVE / name else original_read(path, *args, **kwargs)
        with mock.patch.dict(client.PINS, {name: client.r.sha(changed)}), mock.patch.object(client.t, "read_file", side_effect=read):
            with self.assertRaisesRegex(ValueError, "host diagnostic"):
                client.context()

    def test_linux_ancestors_use_path_descriptors_and_leaf_requires_read(self):
        path_flag = 1 << 21
        with mock.patch.object(v2.sys, "platform", "linux"), mock.patch.object(v2.os, "O_PATH", path_flag, create=True), \
             mock.patch.object(v2.os, "open", side_effect=[100, 101, 102]) as opened, \
             mock.patch.object(v2.os, "close"):
            self.assertEqual(v2.directory("/ancestor/leaf"), 102)
            flags = v2.os.O_DIRECTORY | v2.os.O_NOFOLLOW
            self.assertEqual(opened.call_args_list, [mock.call("/", path_flag | flags),
                             mock.call("ancestor", path_flag | flags, dir_fd=100),
                             mock.call("leaf", v2.os.O_RDONLY | flags, dir_fd=101)])

    def test_receiver_python36_syntax_and_unchanged_small_limits(self):
        ast.parse((ARCHIVE / "transfer-frontier-training-remote-v2.py").read_text(), feature_version=(3, 6))
        self.assertEqual((v2.MAX_FILES, v2.MAX_FILE, v2.MAX_TOTAL), (4096, 64 * 1024**2, 512 * 1024**2))
        self.assertEqual(client.LIMITS["address_space_bytes"], 320 * 1024**2)
        self.assertEqual((client.LIMITS["remote_cpu_seconds"], client.LIMITS["remote_wall_seconds"], client.LIMITS["ssh_wall_seconds"]), (45, 55, 60))


if __name__ == "__main__":
    suite = unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(baseline.TransferSafety),
                               unittest.defaultTestLoader.loadTestsFromTestCase(CorrectedTransport)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
