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
        native = {"config": {"lora": {"target_modules": ("q_proj", "k_proj"), "alpha": 32}}}
        native["plan_sha256"] = sha256(m.canonical(native)).hexdigest()
        disk = json.loads(m.canonical(native))
        self.assertNotEqual(native, disk)
        with patch.object(m, "PLAN_SHA", native["plan_sha256"]):
            self.assertEqual(m.normalized_plan(native, disk, disk), disk)
            changed = copy.deepcopy(disk)
            changed["config"]["lora"]["alpha"] = 33
            with self.assertRaises(ValueError):
                m.normalized_plan(native, changed, disk)
            changed = copy.deepcopy(disk)
            changed["extra_unbound_field"] = True
            with self.assertRaises(ValueError):
                m.normalized_plan(native, disk, changed)

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
