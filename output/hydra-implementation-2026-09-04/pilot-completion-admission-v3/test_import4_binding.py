"""Pure selector/source gate; no successful recovery receipt is manufactured.

Only source hashes, strict rejection boundaries and unchanged code are checked.
There are no actual pilot admissions, prepared choices, or runtime executions.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
BASE = HERE.parent


def forbid_runtime(event, args):
    if event == "import" and args and args[0].split(".", 1)[0] in {
        "torch", "transformers", "tokenizers", "peano_lab", "mlx"}:
        raise AssertionError("Runtime import is outside this metadata-only gate.")
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}:
        raise AssertionError("Process/network execution is outside this gate.")
    if event == "open" and args and isinstance(args[0], (str, bytes)) and "reserved-holdout" in str(args[0]):
        raise AssertionError("Reserved cases cannot be read in this gate.")


sys.addaudithook(forbid_runtime)
spec = importlib.util.spec_from_file_location("_import4_admission_gate", HERE / "pilot_admission.py")
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


class NoEvidenceReads:
    def descriptor(self, *args, **kwargs):
        raise AssertionError("A rejected selector must fail before evidence is read.")


class Import4BindingTests(unittest.TestCase):
    def test_exact_reviewed_reader_sources_and_attempt_are_selected(self):
        expected = {
            "metadata_recovery.py": "aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16",
            "gpu_saved_reload.py": "b50a2f9c54e977d13dd1f1830cb414701631bd5f46317fe1c8346ce5c49e43e6",
            "remote_recovery_control.py": "2aba491b719679e7f7b2418ce6c15d5a87d28f50d338f06f1f4e8fe950128b38",
            "recovery_launchers.py": "bd7bb619fb33a64c732dcd46a7e6f1e64d8f58fa27de40bc0bc4ed9eae7119c6",
        }
        self.assertEqual(admission.RECOVERY, "p6-postsave-recovery-v4")
        self.assertEqual(admission.CPU_REPORT, "metadata-recovery-import4.json")
        self.assertEqual(admission.CPU_ACTUAL, "metadata-actual-completion-import4.json")
        for name, sha in expected.items():
            self.assertEqual(admission.PINNED[admission.RECOVERY + "/" + name], sha)
            self.assertEqual(admission.digest((BASE / admission.RECOVERY / name).read_bytes()), sha)
        with admission.readers(admission.Evidence(admission.ROOT), recovery=True) as modules:
            gpu, reader = modules["gpu_saved_reload"], modules["_pilot_collection_reader"]
            self.assertEqual(gpu.ATTEMPT, "p6-saved-recovery-1.7b-import4-01")
            self.assertEqual(reader.control.ATTEMPT, gpu.ATTEMPT)
            self.assertEqual(reader.control.METADATA_VERIFIER_SHA, expected["metadata_recovery.py"])
            self.assertEqual(reader.control.CONTROLLER_SHA, expected["gpu_saved_reload.py"])
            self.assertTrue(gpu.TRAINING_SOURCE.endswith("/bundles/source-data-07/source"))
            self.assertTrue(gpu.SOURCE.endswith("/bundles/source-data-09/source"))
            self.assertEqual(gpu.METADATA_SCHEMA, "hydra-p6-postsave-metadata-recovery-v2")

    def test_former_cpu_selectors_fail_before_any_receipt_read(self):
        correct = admission.REL + admission.RECOVERY + "/"
        for family, report, actual in (
            ("p6-postsave-recovery-v3", "metadata-recovery-base3.json", "metadata-actual-completion-base3.json"),
            (admission.RECOVERY, "metadata-recovery-base3.json", "metadata-actual-completion-base3.json"),
            (admission.RECOVERY, admission.CPU_REPORT, "metadata-actual-completion-base3.json"),
        ):
            prefix = admission.REL + family + "/"
            descriptor = {"kind": admission.KINDS["qwen3-1.7b-base"],
                          "cpu_metadata": {"path": prefix + report, "sha256": "0" * 64},
                          "cpu_actual_completion": {"path": prefix + actual, "sha256": "0" * 64},
                          "gpu_collection": {}}
            with self.subTest(family=family, report=report, actual=actual), self.assertRaisesRegex(ValueError, "CPU recovery receipt path"):
                admission.recovered(NoEvidenceReads(), descriptor)
        self.assertTrue(correct.endswith("p6-postsave-recovery-v4/"))

    def test_former_gpu_attempt_is_rejected_before_any_receipt_read(self):
        for family, attempt in (("p6-postsave-recovery-v3", "p6-saved-recovery-1.7b-base3-01"),
                                (admission.RECOVERY, "p6-saved-recovery-1.7b-base3-01")):
            prefix = admission.REL + family + "/attempts/" + attempt + "/observation-001/"
            descriptor = {key: {"path": prefix + name, "sha256": "0" * 64} for key, name in (
                ("response", "response.json"), ("transport", "transport-completion.json"),
                ("actual_completion", "actual-tool-completion.json"))}
            with self.subTest(family=family), self.assertRaisesRegex(ValueError, "exact admitted attempt"):
                admission.collection(NoEvidenceReads(), descriptor, None, admission.RECOVERY,
                    "p6-saved-recovery-1.7b-import4-01", "hydra-p6-saved-recovery-control-phase-v1")

    def test_missing_cpu_success_or_old_verifier_pin_still_rejects(self):
        with admission.readers(admission.Evidence(admission.ROOT), recovery=True) as modules:
            gpu = modules["gpu_saved_reload"]
            with self.assertRaisesRegex(ValueError, "CPU metadata"):
                gpu.validate_metadata({"passed": False, "job_id": "21912020"}, {}, "0" * 64,
                    admission.PINNED[admission.RECOVERY + "/metadata_recovery.py"])
        with self.assertRaisesRegex(ValueError, "Evidence SHA differs"):
            admission.Evidence(admission.ROOT).read(admission.REL + admission.RECOVERY + "/metadata_recovery.py",
                "3f11a9e6ef501cc4834662f01a4dd7a388892f71cae1bc70ad4a272524c5d2be")
        for record in ({}, {"actual_exit_code": 1, "completion_chunk": "abcdef"},
                       {"actual_exit_code": False, "completion_chunk": "abcdef"}):
            with self.subTest(record=record), self.assertRaises(ValueError):
                admission.actual_outer(record)

    def test_only_declared_helper_literals_change_normal4_and_charges_are_preserved(self):
        derivation = ast.parse((HERE / "derive_import4.py").read_bytes())
        replacements = next(ast.literal_eval(node.value) for node in derivation.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "REPLACEMENTS" for target in node.targets))
        old = (BASE / "pilot-completion-admission-v2/pilot_admission.py").read_text()
        new = (HERE / "pilot_admission.py").read_text()
        restored = new
        for first, second in reversed(tuple(replacements.items())):
            self.assertEqual(restored.count(second), 1)
            restored = restored.replace(second, first)
        self.assertEqual(restored, old)
        self.assertEqual(admission.FRESH4, "p6-training-launchers-v3")
        self.assertEqual(admission.PINNED[admission.FRESH4 + "/training_launchers.py"],
                         "b62eeeecdcd42d071b11fd54884ab788c6c57c8b369cf6c4ffbebc34bddaf437")
        self.assertEqual(admission.PINNED[admission.FRESH4 + "/remote_training_control.py"],
                         "c59c7343e08330d938ba7783827663354631b2a995ede1ee9172a9e86904e2b0")
        for pattern in ("p6-postsave-recovery-v*/attempts/*/release/charge-intent.json",
                        "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
                        "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json"):
            self.assertIn(pattern, admission.CHARGE_GLOBS)
        self.assertIn('"selector": "import4"', new)
        self.assertIn('"/runtime-source-pins-base3.json"', new)

    def test_final_local_bindings_preserve_both_transfer_branches_and_remote_bytes(self):
        own_sha = admission.digest((HERE / "pilot_admission.py").read_bytes())
        previous_sha = "0a4081a7acf35f255994dd9f053f19cec0c5776cabe1d0ab42c16534a40963dc"
        for family, local, remote in (
            ("paired-launchers-v4", "paired_launchers.py", "remote_paired_control.py"),
            ("p7-teacher-launchers-v4", "teacher_launchers.py", "remote_teacher_control.py"),
        ):
            with self.subTest(family=family):
                new = (BASE / family / local).read_text()
                prior = (BASE / "paired-launchers-v4/copy-transfer-gate-01/sources" / local).read_text()
                self.assertEqual(new.count(own_sha), 1)
                self.assertEqual(new.count("pilot-completion-admission-v3/pilot_admission.py"), 3)
                restored = new.replace(own_sha, previous_sha).replace(
                    "pilot-completion-admission-v3/pilot_admission.py", "pilot-completion-admission-v2/pilot_admission.py")
                self.assertEqual(restored, prior)
                self.assertEqual((BASE / family / remote).read_bytes(),
                    (BASE / family.replace("launchers-v4", "launchers-v3") / remote).read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
