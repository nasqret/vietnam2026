"""Pure rejection/serialization fixtures; no native or model modules are loaded."""
import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("metadata_recovery.py")
SPEC = importlib.util.spec_from_file_location("postsave_metadata_pure_fixture", PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class MetadataRecoveryTests(unittest.TestCase):
    def test_tuple_json_normalization_preserves_whole_plan(self):
        provider = "hydra-playground/experimental_model.py"
        native = {"config": {"lora": {"target_modules": ("q_proj", "k_proj"), "alpha": 32}},
                  "source_pins": {provider: m.PROVIDER_SHA}}
        native["plan_sha256"] = sha256(m.canonical(native)).hexdigest()
        disk = json.loads(m.canonical(native))
        self.assertNotEqual(native, disk)
        runtime = copy.deepcopy(native)
        runtime["source_pins"][provider] = m.RUNTIME_PROVIDER_SHA
        runtime["plan_sha256"] = sha256(m.canonical({k: v for k, v in runtime.items() if k != "plan_sha256"})).hexdigest()
        with patch.object(m, "PLAN_SHA", native["plan_sha256"]):
            original, rebound, derivation = m.normalized_plan(runtime, disk, disk)
            self.assertEqual(original, disk)
            self.assertEqual(m.canonical(rebound), m.canonical(runtime))
            self.assertFalse(derivation["training_exposure_changed"])
            changed = copy.deepcopy(disk)
            changed["config"]["lora"]["alpha"] = 33
            with self.assertRaises(ValueError):
                m.normalized_plan(runtime, changed, disk)
            changed = copy.deepcopy(disk)
            changed["extra_unbound_field"] = True
            with self.assertRaises(ValueError):
                m.normalized_plan(runtime, disk, changed)

    def test_exact_recorded_original_plan_has_only_one_runtime_rebind(self):
        path = PATH.parent.parent / "p6-source-bundle-08/original-prepared-qwen3-1.7b-base.json"
        original = json.loads(path.read_bytes())
        self.assertEqual(original["plan_sha256"], m.PLAN_SHA)
        runtime = copy.deepcopy(original)
        runtime["source_pins"]["hydra-playground/experimental_model.py"] = m.RUNTIME_PROVIDER_SHA
        runtime["plan_sha256"] = sha256(m.canonical({k: v for k, v in runtime.items() if k != "plan_sha256"})).hexdigest()
        self.assertEqual(runtime["plan_sha256"], "77119db9f4a4ef1b6a3bcb78dea8c28d7f4008671099154f84f8a18a9e86bb1f")
        admitted, rebound, derivation = m.normalized_plan(runtime, original, original)
        self.assertEqual(admitted, original)
        self.assertEqual(rebound, runtime)
        self.assertEqual(derivation["original_plan_sha256"], m.PLAN_SHA)
        self.assertFalse(derivation["new_training_performed"])
        for mutate in (lambda value: value.update(training_rows=2046),
                       lambda value: value["source_pins"].update({"another.py": "a" * 64}),
                       lambda value: value["config"]["lora"].update(alpha=33),
                       lambda value: value.update(unbound_exception=True)):
            changed = copy.deepcopy(runtime)
            mutate(changed)
            changed["plan_sha256"] = sha256(m.canonical({k: v for k, v in changed.items() if k != "plan_sha256"})).hexdigest()
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.normalized_plan(changed, original, original)

    def test_source_maps_must_retain_every_original_file_except_provider(self):
        original = json.loads(PATH.with_name("controller-source-pins.json").read_bytes())
        runtime = json.loads(PATH.with_name("runtime-source-pins-base3.json").read_bytes())
        m.validate_source_maps(original, runtime)
        changed = copy.deepcopy(runtime)
        key = next(name for name in sorted(runtime) if name != "hydra-playground/experimental_model.py")
        changed[key]["sha256"] = "f" * 64
        with patch.object(m, "RUNTIME_SOURCE_SHA", sha256(m.canonical(changed)).hexdigest()):
            with self.assertRaises(ValueError):
                m.validate_source_maps(original, changed)
        with self.assertRaises(ValueError):
            m.validate_source_maps(runtime, original)
        changed = copy.deepcopy(runtime); changed.pop(key)
        with self.assertRaises(ValueError):
            m.validate_source_maps(original, changed)

    def progress(self):
        rows = [{"kind": "loading-model", "model": {"model_id": "fixture"}},
                {"kind": "training-start", "rows": 2047, "expected_optimizer_steps": 256}]
        rows += [{"kind": "optimizer-step", "step": n} for n in range(1, 257)]
        rows += [{"kind": "training-complete", "optimizer_steps": 256}]
        for index, row in enumerate(rows, 1):
            row.update(event=index, elapsed_seconds=float(index))
        return rows, {"model": {"model_id": "fixture"}, "actual_optimizer_steps": 256}

    def test_all_callbacks_required(self):
        rows, artifact = self.progress()
        encode = lambda values: b"\n".join(m.canonical(v) for v in values)
        self.assertEqual(m.validate_progress(encode(rows), artifact)["optimizer_steps"], 256)
        for mutate in (lambda x: x.pop(10), lambda x: x[8].update(step=2),
                       lambda x: x[-1].update(kind="optimizer-step"),
                       lambda x: x[-1].update(elapsed_seconds=1140)):
            changed = copy.deepcopy(rows)
            mutate(changed)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.validate_progress(encode(changed), artifact)

    def failed_fixture(self):
        source = {"fixture.py": {"bytes": 1, "sha256": "0" * 64}}
        observation = {"job_id": m.JOB_ID, "read_only": True, "scheduler": {"sacct": {
            "actual_exit_code": 0, "executed": True, "owned_child_reaped": True, "stop_reason": None,
            "stdout_stderr": m.JOB_ID + "|hydra-p6-training-fresh-1.7b-v2-01|plgnasqret|"
              "plgccaiautore2026-gpu-gh200|plgrid-gpu-gh200|FAILED|1:0|916|20|8|64G|"
              "billing=1,cpu=8,gres/gpu=1,mem=64G,node=1|billing=1,cpu=8,gres/gpu=1,mem=64G,node=1|x1002c0s3b0n0\n"}}}
        transport = {"actual_ssh_exit_code": 0, "owned_child_reaped": True, "output_complete": True,
                     "stop_reason": None, "automatic_retry": False}
        completion = {"schema": "hydra-p6-remote-training-completion-v1", "completed": False,
            "error": dict(m.FAILURE), "execute_invoked": True, "reservation_claimed": True,
            "optimizer_steps_observed": 256, "actual_optimizer_steps_in_complete_artifact": None,
            "training_artifact": None, "model_reload_performed": False, "sources_unchanged": True,
            "automatic_retry": False, "resume": False, "source_pins_after": source,
            "model_inference_calls": 0, "native_proof_searches": 0, "native_proof_replays": 0, "solver_calls": 0}
        return observation, transport, completion, {"source_pins_before": source}

    def test_failure_is_preserved_not_relabelled(self):
        observation, transport, completion, request = self.failed_fixture()
        source_sha = sha256(m.canonical(request["source_pins_before"])).hexdigest()
        with patch.object(m, "SOURCE_SHA", source_sha):
            good = m.validate_failed_job(observation, transport, completion, request, b"1\n")
            self.assertEqual(good["original_slurm_state"], "FAILED")
            self.assertFalse(good["original_controller_completed"])
            with self.assertRaises(ValueError):
                m.validate_failed_job(observation, transport, completion, request, b"0\n")
            for key, value in (("completed", True), ("error", {"type": "ValueError", "detail": "unrelated"}),
                               ("training_artifact", {}), ("optimizer_steps_observed", 255)):
                changed = dict(completion, **{key: value})
                with self.subTest(key=key), self.assertRaises(ValueError):
                    m.validate_failed_job(observation, transport, changed, request, b"1\n")
            changed = copy.deepcopy(observation)
            changed["job_id"] = "another-job"
            with self.assertRaises(ValueError):
                m.validate_failed_job(changed, transport, completion, request, b"1\n")

    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                m.decode(raw)

    def test_ordinary_files_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path = root / "one.json"
            descriptor = m.save(path, {"n": 1})
            self.assertEqual(m.read(path)[1]["sha256"], descriptor["sha256"])
            with self.assertRaises(FileExistsError):
                m.save(path, {"n": 2})
            (root / "alias").symlink_to(path)
            with self.assertRaises(ValueError):
                m.read(root / "alias")
            with self.assertRaises(ValueError):
                m.relative(root, "../escape")

    def test_no_framework_network_or_child_authority(self):
        for name in ("torch", "transformers.models.qwen3", "tokenizers"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.prohibit_runtime("import", (name,))
        for name in ("subprocess.Popen", "socket.connect", "os.system", "os.exec"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.prohibit_runtime(name, ())
        m.prohibit_runtime("import", ("json",))


if __name__ == "__main__":
    unittest.main()
