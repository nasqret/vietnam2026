"""One pure spec/charge regression; no real phase or allocation is prepared."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import training_launchers as launcher
import remote_training_control as control


def forbid_process_network(event, args):
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.posix_spawn"} or event.startswith("socket."):
        raise AssertionError("Pure launcher regression cannot execute a process or network call.")


sys.addaudithook(forbid_process_network)


class Fresh4BOnly(unittest.TestCase):
    def test_fixed_spec_and_every_release_family_requires_full_reconciliation(self):
        manifest, launch, source_map = launcher.bundle_inputs()
        self.assertEqual(set(control.MODELS), {"qwen3-4b-base"})
        self.assertEqual(control.TRAINER_SHA, "b0701a1c337fb33e904e6f721b450aa7d541b72ae38b2c2cfaf54e790bc192b7")
        self.assertEqual(control.SOURCE_MAP_SHA, control.digest(control.canonical(source_map)))
        choice = {"schema": "hydra-p6-training-allocation-choice-v1", "model_key": "qwen3-4b-base",
                  "seconds": 600, "soft_limit_seconds": 540,
                  "throughput": None, "transfer_receipt": None, "base_admission": None}
        # This is only a pure spec fixture. None evidence prevents actual prepare.
        spec = launcher.make_spec(choice, "a" * 32, control.digest(control.canonical(manifest)))
        self.assertEqual(spec["attempt"], "p6-training-fresh-4b-v3-01")
        self.assertTrue(spec["source"].endswith("/source-data-08/source"))
        self.assertEqual((spec["training_rows"], spec["validation_rows"], spec["expected_optimizer_steps"]), (2047, 432, 256))
        self.assertEqual(spec["plan_sha256"], "e332678d9102db48071638b1d94b958cea0cf33c9c60234aef4bf7e5ba64ec7f")
        self.assertEqual(spec["plan_sha256"], launch["models"]["qwen3-4b-base"]["plan_sha256"])
        self.assertIn("--model-key qwen3-4b-base", control.job_script(spec))
        self.assertIn("p6-training-fresh-4b-v3-01", control.job_script(spec))
        with self.assertRaises(ValueError):
            launcher.make_spec({**choice, "model_key": "qwen3-1.7b-base"}, "a" * 32, spec["manifest_content_sha256"])
        with self.assertRaises(ValueError):
            control.validate_spec({**spec, "controller_sha256": "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617"})

        families = [
            "p6-training-launchers-v2/attempts/old/release/charge-intent.json",
            "p6-training-launchers-v3/attempts/prior/release/charge-intent.json",
            "p6-8b-smoke-launchers-v1/attempts/probe/release/charge-intent.json",
            "p6-8b-training-launchers-v1/attempts/train/release/charge-intent.json",
            "paired-launchers-v1/prepared/arms/arm/release/charge-intent.json",
            "p7-teacher-launchers-v1/attempts/teacher/release/charge-intent.json",
            "p7-student-launchers-v1/attempts/student/release/charge-intent.json",
            "p6-postsave-recovery-v1/attempts/recovery/release/charge-intent.json",
        ]
        with tempfile.TemporaryDirectory(prefix=".pure-spec-", dir=HERE) as temporary:
            root = Path(temporary)
            current = root / "p6-training-launchers-v3"
            current.mkdir()
            charges = []
            for index, relative in enumerate(families):
                charge = {"attempt": "synthetic-charge-" + str(index), "job_id": str(99000 + index),
                          "gpus": 1, "seconds": 300, "allocated_seconds": 300,
                          "reservation_sha256": format(index + 1, "064x"), "status": "FAILED"}
                charges.append(charge)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(control.canonical(charge) + b"\n")
            ledger_path = root / "campaign.json"

            def write_ledger(rows):
                ledger = {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6,
                          "automatic_retry": False, "gpu_reservations": rows,
                          "gpu_seconds_reserved": 300 * len(rows), "gpu_hours_allocated": 300 * len(rows) / 3600}
                raw = control.canonical(ledger) + b"\n"
                ledger_path.write_bytes(raw)
                return control.digest(raw)

            with patch.object(launcher, "HERE", current), patch.object(launcher, "CAMPAIGN_FILE", ledger_path):
                for omitted in range(len(charges)):
                    pin = write_ledger([row for i, row in enumerate(charges) if i != omitted])
                    with self.subTest(unreconciled_family=families[omitted]), self.assertRaisesRegex(ValueError, "Reconcile"):
                        launcher.current_ledger(pin, "qwen3-4b-base")
                pin = write_ledger(charges)
                _, _, used = launcher.current_ledger(pin, "qwen3-4b-base")
                self.assertEqual(used, 300 * len(charges))
                refunded = copy.deepcopy(charges)
                refunded[-1]["allocated_seconds"] = 1
                with self.assertRaisesRegex(ValueError, "partial refund"):
                    launcher.current_ledger(write_ledger(refunded), "qwen3-4b-base")


if __name__ == "__main__":
    unittest.main(verbosity=2)
