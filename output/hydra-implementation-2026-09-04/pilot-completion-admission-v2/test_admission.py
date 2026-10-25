"""Pure admission rejection tests. Synthetic records are never execution evidence.

Real source/manifest bytes are read. No proof case, model, scheduler or network
is executed; fake-shaped success fields only test whether contrary evidence wins.
"""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pilot_admission as admission


def forbid_runtime(event, args):
    if event == "import" and args:
        if args[0].split(".", 1)[0] in {"torch", "transformers", "tokenizers", "peano_lab", "mlx"}:
            raise AssertionError("Runtime import is outside the pure gate.")
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}:
        raise AssertionError("No process/network execution is permitted in this gate.")
    if event == "open" and args and isinstance(args[0], (str, bytes)) and "reserved-holdout" in str(args[0]):
        raise AssertionError("No reserved-case input may be opened.")


sys.addaudithook(forbid_runtime)


def row(raw):
    return {"base64": base64.b64encode(raw).decode(), "bytes": len(raw), "sha256": admission.digest(raw),
            "stable": True, "complete_file": True, "offset": 0,
            "file_bytes_before": len(raw), "file_bytes_after": len(raw)}


class AdmissionRejections(unittest.TestCase):
    def test_failed_original_is_not_normal_success_and_old_4b_is_not_source08(self):
        for model, descriptor in (("qwen3-1.7b-base", {"kind": "ordinary_pilot_completion"}),
                                  ("qwen3-4b-base", {"kind": "fresh4b_source07_v2"})):
            with self.subTest(model=model), self.assertRaises(ValueError):
                admission.admit_pilot(model, descriptor)
        with self.assertRaisesRegex(ValueError, "separate CPU and GPU"):
            admission.admit_pilot("qwen3-1.7b-base", {"kind": "saved_pilot_recovery_v2"})
        with self.assertRaisesRegex(ValueError, "Both real pilot"):
            admission.admit_pair({"qwen3-4b-base": {"kind": "fresh4b_source08_v3"}})

    def test_actual_failure_bool_missing_or_conflicting_exit_cannot_pass(self):
        for record in ({}, {"actual_exit_code": False, "completion_chunk": "abcdef"},
                       {"actual_exit_code": 1, "completion_chunk": "abcdef"},
                       {"actual_exit_code": 0, "actual_process_exit_code": 1, "completion_chunk": "abcdef"},
                       {"actual_exit_code": 0, "completion_chunk": "not-observed"}):
            with self.subTest(record=record), self.assertRaises(ValueError):
                admission.actual_outer(record)

    def test_collection_rejects_other_source_nonzero_transport_and_old_attempt(self):
        with admission.readers(admission.Evidence(admission.ROOT)) as modules:
            reader = modules["_pilot_collection_reader"]
            attempt = reader.control.MODELS["qwen3-4b-base"]["attempt"]
            prefix = admission.REL + admission.FRESH4 + "/attempts/" + attempt + "/observation-001/"
            with tempfile.TemporaryDirectory(prefix="pure-rejection-", dir=HERE) as directory:
                root = Path(directory)
                target = root / prefix
                target.mkdir(parents=True)
                actual_raw = admission.canonical({"actual_exit_code": 0, "completion_chunk": "abcdef",
                                                   "synthetic_fixture_only": True})
                (target / "actual-tool-completion.json").write_bytes(actual_raw)
                actual = {"path": prefix + "actual-tool-completion.json", "sha256": admission.digest(actual_raw)}
                baseline = {"actual_ssh_exit_code": 0, "owned_child_reaped": True, "output_complete": True,
                    "stop_reason": None, "automatic_retry": False,
                    "remote_script_sha256": admission.PINNED[admission.FRESH4 + "/remote_training_control.py"]}
                for key, value in (("actual_ssh_exit_code", 1), ("output_complete", False),
                                   ("remote_script_sha256", "7c87dda334901f464cd63413fc394b4808485dd57e0449634daae9f3f4e7fb62")):
                    bad = dict(baseline); bad[key] = value
                    raw = admission.canonical(bad)
                    (target / "transport-completion.json").write_bytes(raw)
                    descriptors = {"response": {"path": prefix + "response.json", "sha256": "f" * 64},
                        "transport": {"path": prefix + "transport-completion.json", "sha256": admission.digest(raw)},
                        "actual_completion": actual}
                    with self.subTest(field=key), self.assertRaisesRegex(ValueError, "transport"):
                        admission.collection(admission.Evidence(root), descriptors, reader, admission.FRESH4, attempt,
                                             "hydra-p6-training-control-phase-v1")
                # Reach JSON/inventory admission under a valid-shaped transport;
                # malformed evidence must fail there, without a runtime call.
                transport_raw = admission.canonical(baseline)
                response_raw = admission.canonical({"schema": "hydra-p6-training-control-phase-v1", "phase": "collect",
                    "completed": True, "error": None, "result": {"read_only": False, "files": {}}})
                (target / "transport-completion.json").write_bytes(transport_raw)
                (target / "response.json").write_bytes(response_raw)
                descriptors["transport"]["sha256"] = admission.digest(transport_raw)
                descriptors["response"]["sha256"] = admission.digest(response_raw)
                with self.assertRaisesRegex(ValueError, "inventory"):
                    admission.collection(admission.Evidence(root), descriptors, reader, admission.FRESH4, attempt,
                                         "hydra-p6-training-control-phase-v1")
                descriptors["response"]["path"] = prefix.replace("p6-training-fresh-4b-v3-01", "p6-training-fresh-4b-v2-01") + "response.json"
                with self.assertRaisesRegex(ValueError, "exact admitted attempt"):
                    admission.collection(admission.Evidence(root), descriptors, reader, admission.FRESH4, attempt,
                                         "hydra-p6-training-control-phase-v1")

    def test_actual_failed_gpu_or_process_overrides_synthetic_success_fields(self):
        with admission.readers(admission.Evidence(admission.ROOT), recovery=True) as modules:
            reader = modules["_pilot_collection_reader"]
            spec = reader.make_spec("a" * 32, "b" * 64, "c" * 64, "d" * 64)
            record = reader.control.reservation(spec, "21919999", reader.control.UID)
            columns = [record["job_id"], spec["job_name"], reader.control.REMOTE_USER, reader.control.ACCOUNT,
                reader.control.PARTITION, "COMPLETED", "0:0", "10", "5", "8", "64G",
                "cpu=8,mem=64G,node=1,gres/gpu=1", "cpu=8,mem=64G,node=1,gres/gpu=1", "synthetic-node"]
            for slurm, code, process in (("FAILED", "1:0", b"0\n"), ("COMPLETED", "0:0", b"1\n")):
                bad_columns = columns[:]; bad_columns[5:7] = [slurm, code]
                observation = {"files": {"job/actual-process-exit.txt": row(process)},
                    "scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None,
                                             "stdout_stderr": "|".join(bad_columns)}}}
                summary = reader.summarize(observation, spec, record, {})
                with self.subTest(slurm=slurm, process=process):
                    self.assertEqual(summary["status"], "terminal_failed_or_incomplete_evidence")
                    self.assertFalse(summary["saved_adapter_reload_admitted"])
                    self.assertTrue(summary["errors"])

    def test_normal_4b_exact_owner_and_reservation_cannot_be_rebound(self):
        with admission.readers(admission.Evidence(admission.ROOT)) as modules:
            reader = modules["_pilot_collection_reader"]
            choice = {"schema": "hydra-p6-training-allocation-choice-v1", "model_key": "qwen3-4b-base",
                      "seconds": 2100, "soft_limit_seconds": 2040, "throughput": {},
                      "transfer_receipt": {}, "base_admission": {}}
            spec = reader.make_spec(choice, "a" * 32, "b" * 64)
            record = reader.control.reservation(spec, "21919998", admission.UID)
            for field, value in (("uid", 105924), ("gpus", True), ("source_pins_sha256", "f" * 64),
                                 ("controller_sha256", "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617")):
                bad = dict(record); bad[field] = value
                observation = {"job_id": record["job_id"], "files": {
                    "job/reservation.json": row(admission.canonical(bad) + b"\n")}}
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "owned reservation"):
                    admission.checked_reservation(observation, spec, reader)

    def test_saved_population_rejects_changed_weights_even_if_before_equals_after(self):
        manifest = admission.ROOT / admission.ORIGINAL / "artifact/manifest.json"
        raw = manifest.read_bytes()
        self.assertEqual(admission.digest(raw), "3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135")
        artifact = json.loads(raw)
        pin = {"bytes": len(raw), "sha256": admission.digest(raw)}
        before = {"manifest.json": pin}
        for group in ("adapter", "tokenizer"):
            for name, sha in artifact[group]["files"].items():
                before[name] = {"bytes": 1, "sha256": sha}  # Synthetic lengths; only rejections are asserted.
        weight = next(name for name in before if name.endswith(".safetensors"))
        changed = deepcopy(before); changed[weight]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Saved tensor/tokenizer bytes changed"):
            admission.saved_population(artifact, changed, deepcopy(changed), pin)
        partial = deepcopy(before); partial.pop(weight)
        with self.assertRaisesRegex(ValueError, "partial"):
            admission.saved_population(artifact, partial, deepcopy(partial), pin)

    def test_missing_cpu_success_and_changed_source_pin_reject(self):
        with admission.readers(admission.Evidence(admission.ROOT), recovery=True) as modules:
            gpu = modules["gpu_saved_reload"]
            with self.assertRaisesRegex(ValueError, "CPU metadata"):
                gpu.validate_metadata({"passed": False, "job_id": "21912020"}, {}, "b" * 64,
                                      admission.PINNED[admission.RECOVERY + "/metadata_recovery.py"])
        evidence = admission.Evidence(admission.ROOT)
        with self.assertRaisesRegex(ValueError, "Evidence SHA differs"):
            evidence.read(admission.REL + admission.FRESH4 + "/remote_training_control.py", "0" * 64)

    def test_recovery_cannot_replace_or_refund_original_charge(self):
        original = {"attempt": "p6-training-fresh-1.7b-v2-01", "job_id": "21912020", "seconds": 1200,
                    "reservation_sha256": "a" * 64}
        recovery = {"attempt": "synthetic-recovery-base3", "job_id": "21919999", "seconds": 300,
                    "reservation_sha256": "b" * 64}
        record = {"schema": "hydra-pilot-completion-admission-v2", "original_training": original, "recovery": recovery}
        rows = [{**item, "gpus": 1, "allocated_seconds": item["seconds"]} for item in (original, recovery)]
        for mutated in (rows[:1], rows[1:], [{**rows[0], "allocated_seconds": 916}, rows[1]],
                        [rows[0], {**rows[1], "reservation_sha256": "c" * 64}]):
            with self.subTest(rows=mutated), self.assertRaises(ValueError):
                admission.require_pilot_charges({"gpu_reservations": mutated}, [record])
        self.assertIn("p6-postsave-recovery-v*/attempts/*/release/charge-intent.json", admission.CHARGE_GLOBS)
        self.assertIn("paired-launchers-v*/prepared/arms/*/release/charge-intent.json", admission.CHARGE_GLOBS)
        self.assertIn("p7-teacher-launchers-v*/attempts/*/release/charge-intent.json", admission.CHARGE_GLOBS)

    def test_source09_runtime_and_source07_training_cannot_be_relabelled(self):
        with admission.readers(admission.Evidence(admission.ROOT), recovery=True) as modules:
            gpu = modules["gpu_saved_reload"]
            self.assertTrue(gpu.TRAINING_SOURCE.endswith("/bundles/source-data-07/source"))
            self.assertTrue(gpu.SOURCE.endswith("/bundles/source-data-09/source"))
            self.assertEqual(gpu.PROVIDER_SHA, "cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44")
            self.assertEqual(gpu.TRAINING_PROVIDER_SHA, "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f")
            self.assertEqual(gpu.METADATA_SCHEMA, "hydra-p6-postsave-metadata-recovery-v2")
            self.assertEqual(gpu.ATTEMPT, "p6-saved-recovery-1.7b-base3-01")
            base = HERE.parent / admission.RECOVERY
            training = json.loads((base / "controller-source-pins.json").read_bytes())
            runtime = json.loads((base / "runtime-source-pins-base3.json").read_bytes())
            gpu.validate_source_maps(training, runtime)
            # Actual pinned metadata, altered only in memory. No case/model load.
            for wrong in (deepcopy(training), deepcopy(runtime)):
                wrong["hydra-playground/experimental_model.py"] = training["hydra-playground/experimental_model.py"]
                with self.assertRaises(ValueError):
                    gpu.validate_source_maps(training, wrong)
            with self.assertRaises(ValueError):
                gpu.validate_metadata({"schema": "hydra-p6-postsave-metadata-recovery-v1", "passed": True},
                                      {}, "0" * 64, admission.PINNED[admission.RECOVERY + "/metadata_recovery.py"])
        with self.assertRaises(ValueError):
            admission.admit_pilot("qwen3-1.7b-base", {"kind": "saved_pilot_recovery_v1"})

    def test_new_launcher_bindings_require_actual_evidence_and_keep_training_roots(self):
        import importlib.util
        def module(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            value = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(value)
            return value
        pairs = HERE.parent / "paired-launchers-v3"
        control = module("pure_new_paired_control", pairs / "remote_paired_control.py")
        self.assertTrue(control.SOURCE.endswith("/bundles/combined-source-02/source"))
        self.assertIn("/bundles/source-data-07/source/", control.ARTIFACTS["fresh_1_7b"])
        self.assertIn("/bundles/source-data-08/source/", control.ARTIFACTS["fresh_4b"])
        self.assertEqual(control.attempt("fresh_1_7b"), "p6-paired-fresh-1-7b-v3-01")
        api = control.contract(HERE.parent / "combined-source-bundle-02/source")
        self.assertEqual(api.PROVIDER_SHA, "cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44")
        teacher_dir = HERE.parent / "p7-teacher-launchers-v3"
        teacher_control = module("pure_new_teacher_control", teacher_dir / "remote_teacher_control.py")
        old = sys.modules.get("remote_teacher_control")
        try:
            sys.modules["remote_teacher_control"] = teacher_control
            teacher = module("pure_new_teacher_launcher", teacher_dir / "teacher_launchers.py")
            self.assertEqual(teacher.ADMISSION_SHA, admission.digest((HERE / "pilot_admission.py").read_bytes()))
            self.assertEqual(teacher_control.ATTEMPT, "p7-teacher-32-v3-01")
            with self.assertRaises(ValueError):
                teacher.validate_choice({"schema": "hydra-p7-teacher-allocation-choice-v2"})
            with self.assertRaises(ValueError):
                teacher.bundle_inputs({"transfer": None})
            with self.assertRaises((ValueError, FileNotFoundError)):
                teacher.verify_prerequisites({})
        finally:
            if old is None:
                sys.modules.pop("remote_teacher_control", None)
            else:
                sys.modules["remote_teacher_control"] = old
        self.assertFalse((pairs / "prepared").exists())
        self.assertFalse((teacher_dir / "attempts").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
