"""Focused metadata-only admission tests; no model, native checker or numerical execution."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "hydra-playground"))
spec = importlib.util.spec_from_file_location("hydra_newest_provider_test_target", HERE / "newest_provider.py")
provider = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = provider
spec.loader.exec_module(provider)


class Admission(unittest.TestCase):
    def setUp(self):
        self.loader, self.spec, self.training, self.pins = provider._metadata()
        self.exported = json.loads((HERE / "export-receipt.json").read_text())
        self.selection = json.loads((HERE / "selection.json").read_text())

    def validate(self, exported=None, selection=None):
        self.loader.validate_cpu_export_receipt(self.exported if exported is None else exported,
            self.selection if selection is None else selection, self.training, self.spec,
            provider.PINS["export_cpu.py"])

    def test_genuine_cpu_receipt_without_loading_model(self):
        self.validate()
        policy = provider.create_policy(object())
        self.assertEqual(policy.selection_id, "wmi-c6-long-vanilla11")
        self.assertEqual(policy.identity["selected_step"], 16384)
        self.assertIsNone(policy.policy)
        self.assertNotIn("mlx.core", sys.modules)
        self.assertNotIn("torch", sys.modules)

    def test_inference_receipt_cannot_impersonate_cpu_export(self):
        changed = copy.deepcopy(self.exported)
        changed["schema"] = "hydra-upgrade-arm-v1"
        with self.assertRaises(ValueError):
            self.validate(exported=changed)

    def test_changed_checkpoint_or_step_is_rejected(self):
        for field, value in (("checkpoint_sha256", "0" * 64), ("selected_step", 8192),
                             ("tensor_values_bitwise_equal", False), ("inference", True)):
            changed = copy.deepcopy(self.exported)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(exported=changed)
        changed = copy.deepcopy(self.selection)
        changed["state"] = "running"
        with self.assertRaises(ValueError):
            self.validate(selection=changed)


if __name__ == "__main__":
    unittest.main()
