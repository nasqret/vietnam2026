"""Pure launcher admission tests; no external commands or native/model imports."""
import ast
import base64
import copy
import hashlib
import importlib.abc
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class BlockRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "transformers", "peft", "mlx", "numpy", "peano_lab", "experimental_teacher"}:
            raise RuntimeError("Runtime import is forbidden in pure launcher tests: " + fullname)


sys.meta_path.insert(0, BlockRuntime())


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.getaddrinfo"}:
        raise RuntimeError("External execution/network is forbidden in pure launcher tests.")


sys.addaudithook(audit)
import remote_teacher_control as control
import teacher_launchers as launch


def held(spec):
    return {"JobId": "21919999", "JobName": spec["job_name"], "UserId": "plgnasqret(105923)",
        "Comment": "hydra-p6:" + spec["nonce"], "JobState": "PENDING", "Reason": "JobHeldUser",
        "Requeue": "0", "Restarts": "0", "Account": control.ACCOUNT, "Partition": control.PARTITION,
        "NumCPUs": "8", "NumTasks": "1", "NumNodes": "1-1", "TimeLimit": control.wall_string(spec["seconds"]),
        "Command": control.JOB + "/job.sbatch", "WorkDir": control.JOB,
        "StdOut": control.JOB + "/slurm.out", "StdErr": control.JOB + "/slurm.err",
        "ReqTRES": "cpu=8,mem=64G,node=1,billing=83,gres/gpu=1", "AllocTRES": "(null)"}


class TeacherLauncherTests(unittest.TestCase):
    def test_fixed_duration_and_scope(self):
        for seconds in (600, 660, 7200):
            control.validate_spec(control.make_spec(seconds, "a" * 32))
        for seconds in (None, True, 599, 601, 7260):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                control.make_spec(seconds, "a" * 32)
        for key, value in (("gpus", 2), ("states", 33), ("max_model_calls", 65),
                           ("max_proposals", 129), ("max_output_tokens", 513), ("base_directory", "/raw-download")):
            spec = control.make_spec(600, "a" * 32)
            spec[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                control.validate_spec(spec)

    def test_pending_range_and_unallocated_tres(self):
        spec = control.make_spec(600, "a" * 32)
        row = held(spec)
        control.check_held(row, spec, "21919999", 105923)
        checked = control.check_queue_row("21919999", row, "21919999")
        self.assertEqual(checked["allocated_tres"], {})
        for key, value in (("NumNodes", "1-2"), ("NumCPUs", "16"), ("Comment", "hydra-p6:wrong"),
                           ("ReqTRES", "cpu=8,mem=64G,node=1,gres/gpu=2")):
            changed = dict(row, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                control.check_held(changed, spec, "21919999", 105923)

    def test_other_cpu_is_preserved_and_other_gpu_blocks(self):
        cpu = {"JobId": "21910001", "ReqTRES": "cpu=2,mem=4G,node=1", "AllocTRES": "(null)"}
        self.assertTrue(control.check_queue_row("21910001", cpu)["left_unchanged"])
        with self.assertRaises(ValueError):
            control.check_queue_row("21910001", dict(cpu, ReqTRES=cpu["ReqTRES"] + ",gres/gpu=1"))

    def test_existing_teacher_shell_and_reservation_contract(self):
        spec = control.make_spec(660, "a" * 32)
        script = control.job_script(spec)
        self.assertIn("exec /bin/bash -l " + control.SOURCE + "/" + control.JOB_BODY, script)
        self.assertNotIn("-P", script)
        record = control.reservation(spec, "21919999", 105923)
        self.assertEqual(set(record), {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
                                      "model_key", "gpus", "nodes", "cpus", "memory_gib", "seconds"})
        self.assertEqual(record["schema"], "hydra-p7-teacher-reservation-v1")

    def test_full_budget_no_short_failure_refund(self):
        ledger = {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6,
            "automatic_retry": False, "gpu_hours_allocated": 0, "gpu_seconds_reserved": 0,
            "gpu_reservations": [{"attempt": "old", "job_id": "21910000", "seconds": 600,
                                  "gpus": 1, "allocated_seconds": 600, "status": "failed"}]}
        self.assertEqual(launch.ledger_seconds(ledger), 600)
        ledger["gpu_reservations"][0]["allocated_seconds"] = 2
        with self.assertRaises(ValueError):
            launch.ledger_seconds(ledger)
        charge = {"attempt": "teacher", "job_id": "21919999", "seconds": 660,
                  "allocated_seconds": 660, "reservation_sha256": "b" * 64}
        with self.assertRaises(ValueError):
            launch.check_charges({"gpu_reservations": []}, [charge])
        launch.check_charges({"gpu_reservations": [charge]}, [charge])

    def test_exact_local_package_and_base_metadata_only(self):
        source_map = launch.bundle_inputs()
        self.assertEqual(control.digest(control.canonical(source_map)), control.SOURCE_MAP_SHA)
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("peano_lab", sys.modules)

    def test_prerequisites_are_not_invented(self):
        choice = {"schema": "hydra-p7-teacher-allocation-choice-v1", "seconds": 600,
                  "throughput": {}, "fresh_pilots": {"qwen3-1.7b-base": {}, "qwen3-4b-base": {}}}
        launch.validate_choice(choice)
        with patch.object(launch, "evidence", return_value={"status": "incomplete"}), self.assertRaises(ValueError):
            launch.verify_prerequisites(choice)

    def test_copied_remote_safety_helpers_exact(self):
        derivation = json.loads((HERE / "DERIVATION.json").read_bytes())
        text = (HERE / "remote_teacher_control.py").read_text()
        nodes = {n.name: n for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        for name, expected in derivation["remote_helper_sources"].items():
            self.assertEqual(hashlib.sha256(ast.get_source_segment(text, nodes[name]).encode()).hexdigest(), expected, name)

    def test_charge_precedes_actual_release_transport(self):
        text = (HERE / "teacher_launchers.py").read_text()
        node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "mutate_phase")
        calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
        charge = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == "put"
                      and "charge-intent.json" in ast.get_source_segment(text, n))
        ssh = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == "execute_phase")
        self.assertLess(charge.lineno, ssh.lineno)

    def test_zero_yield_metadata_never_admits_distillation(self):
        # Deliberately synthetic metadata-only fixture, never a teacher result.
        spec = control.make_spec(600, "a" * 32)
        record = control.reservation(spec, "21919999", 105923)
        source_map = json.loads((launch.BUNDLE / "source/output/p7-prototype/staged-source-pins.json").read_bytes())["sources"]
        identity = {"schema": "hydra-loaded-remote-teacher-v1", "model_key": control.MODEL_KEY,
            "model_id": "deepseek-ai/DeepSeek-Prover-V2-7B", "revision": "a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b",
            "base": {"base_identity_sha256": control.BASE_IDENTITY_SHA}, "model_loaded": True, "adapter_present": False,
            "source_sha256": "f16f46a9cbb98950749e9b67eb0b3818f011ce25256be6285a962700e4fd13da",
            "p6_helper_sha256": "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"}
        identity["model_manifest_sha256"] = control.digest(control.canonical(identity))
        completion = {"schema": "hydra-teacher-campaign-completion-v1", "completed": True, "error": None,
            "selected_states": 32, "states_completed": 32, "sources_unchanged": True, "automatic_retry": False,
            "student_model_calls": 0, "solver_calls": 0, "optimizer_updates": 0, "source_pins_after": source_map,
            "positive_continuations": 0, "proposals": 0,
            "session": {"identity": identity, "actual_model_calls": 0, "generated_tokens": 0}}
        request = {"reservation": record, "reservation_sha256": control.digest(control.canonical(record) + b"\n"),
            "selection_sha256": control.SELECTION_SHA, "source_pins_before": source_map}
        positives = {"schema": "hydra-teacher-positive-continuations-v1", "records": [], "positive_count": 0,
                     "training_performed": False, "fresh_p5_admission_required": True}
        def entry(raw):
            return {"complete_file": True, "stable": True, "base64": base64.b64encode(raw).decode()}
        row = [record["job_id"], spec["job_name"], control.REMOTE_USER, control.ACCOUNT, control.PARTITION,
               "COMPLETED", "0:0", "9", "10", "8", "64Gn", "cpu=8,mem=64G,node=1,gres/gpu=1",
               "cpu=8,mem=64G,node=1,gres/gpu=1", "gh200001"]
        observation = {"scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None,
                                               "stdout_stderr": "|".join(row) + "\n"}},
            "files": {"actual-process-exit.txt": entry(b"0\n"),
                "result/completion.json": entry(control.canonical(completion)),
                "result/request.json": entry(control.canonical(request)),
                "result/model-admission.json": entry(control.canonical({"identity": identity})),
                "result/positive-continuations.json": entry(control.canonical(positives))}}
        summary = launch.summarize(observation, spec, record)
        self.assertEqual(summary["status"], "teacher_complete_zero_yield_distillation_blocked")
        self.assertFalse(summary["distillation_admitted"])
        identity["model_key"] = "another-model"
        observation["files"]["result/model-admission.json"] = entry(control.canonical({"identity": identity}))
        self.assertFalse(launch.summarize(observation, spec, record)["teacher_campaign_metadata_complete"])


if __name__ == "__main__":
    unittest.main()
