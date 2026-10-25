"""Pure synthetic admission/metadata tests; no native/model/process/network work."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import remote_training_control as c
import training_launchers as l


def choice():
    return {"schema": "hydra-p6-8b-training-allocation-choice-v1", "model_key": "qwen3-8b-base",
        "seconds": 600, "soft_limit_seconds": 540, "throughput": {}, "transfer_receipt": {}, "base_admission": {},
        "completed_8b_smoke": {"prepared_sha256": "a" * 64,
            "collection": {"response": "response", "transport": "transport", "actual_completion": "actual_completion"}}}


def allocation():
    return l.make_spec(choice(), "a" * 32, "b" * 64)


def smoke_fixture():
    """Reuse the sealed pure smoke fixture, never a real completion record."""
    reader = l.smoke_reader()
    path = reader.HERE / "test_smoke_launchers.py"
    handoff = json.loads((reader.HERE / "PREPARED.json").read_bytes())
    l.read(path, handoff["files"][path.name]["sha256"])
    names = {"remote_smoke_control": reader.control, "smoke_launchers": reader}
    prior, prior_path = {name: sys.modules.get(name) for name in names}, list(sys.path)
    try:
        sys.modules.update(names)
        item = importlib.util.spec_from_file_location("_sealed_smoke_synthetic_fixture", path)
        module = importlib.util.module_from_spec(item)
        item.loader.exec_module(module)
        observation, spec, record, source_map = module.SmokeResultAdmission().fixture()
    finally:
        sys.path[:] = prior_path
        for name, old in prior.items():
            if old is None: sys.modules.pop(name, None)
            else: sys.modules[name] = old
    values = {"response": {"schema": "hydra-p6-8b-smoke-control-phase-v1", "phase": "collect", "completed": True,
        "error": None, "result": observation}, "transport": {"actual_ssh_exit_code": 0, "owned_child_reaped": True,
        "stop_reason": None, "output_complete": True, "remote_script_sha256": l.SMOKE_PINS["remote_smoke_control.py"]},
        "actual_completion": {"actual_exit_code": 0, "completion_chunk": "synthetic_fixture_only"}}
    return reader, observation, spec, record, source_map, values


def admit_fixture(mutate=None):
    reader, observation, spec, record, source_map, values = smoke_fixture()
    selected = choice()
    selected["throughput"] = {"format": "json", "path": "synthetic", "sha256": observation["files"]["job/result/throughput.json"]["sha256"]}
    if mutate: mutate(values, selected, reader)
    probe = reader.complete_json(observation, "job/result/throughput.json")
    with patch.object(l, "smoke_reader", return_value=reader), \
         patch.object(reader, "load_prepared", return_value=(reader.HERE, {}, spec, source_map)) as load, \
         patch.object(reader, "evidence", side_effect=lambda key: c.canonical(values[key])), \
         patch.object(l, "evidence", return_value=probe):
        result = l.admit_completed_smoke(selected)
        load.assert_called_once_with("a" * 64, recheck_pilots=True)
    return result


class Fixed8BContract(unittest.TestCase):
    def test_single8b_config_plan_and_existing_training_command(self):
        self.assertEqual(set(c.MODELS), {"qwen3-8b-base"})
        _, launch, _ = l.bundle_inputs()
        model = c.MODELS["qwen3-8b-base"]
        self.assertEqual(model["plan_sha256"], launch["models"]["qwen3-8b-base"]["plan_sha256"])
        spec = allocation(); c.validate_spec(spec)
        self.assertEqual((spec["training_rows"], spec["validation_rows"], spec["expected_optimizer_steps"]), (2047, 432, 256))
        command = c.job_script(spec)
        self.assertIn("--model-key qwen3-8b-base", command)
        self.assertIn(c.SOURCE + "/" + model["config"], command)
        self.assertNotIn("--resume", command)
        self.assertFalse(spec["resume"])

    def test_no_defaults_old_choices_other_models_or_step_overrides(self):
        for key, value in (("seconds", None), ("seconds", 599), ("seconds", 7260), ("soft_limit_seconds", 541),
            ("model_key", "qwen3-4b-base"), ("schema", "hydra-p6-training-allocation-choice-v1"), ("extra_steps", 10)):
            item = choice(); item[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): l.validate_choice(item)
        item = allocation(); item["expected_optimizer_steps"] = 512
        with self.assertRaises(ValueError): c.validate_spec(item)

    def test_frozen_two_model_launcher_and_smoke_dependencies_are_unchanged(self):
        reader = l.smoke_reader()
        self.assertEqual(set(reader.training_reader().control.MODELS), {"qwen3-1.7b-base", "qwen3-4b-base"})
        self.assertIs(sys.modules["remote_training_control"], c)
        self.assertEqual(reader.control.PLAN_SHA, c.MODELS["qwen3-8b-base"]["plan_sha256"])


class Admission(unittest.TestCase):
    def test_complete_synthetic_smoke_requires_pilots_and_never_infers_duration(self):
        result = admit_fixture()
        self.assertEqual(result["seconds"], 600)
        self.assertIsNone(result["inferred_training_duration"])
        self.assertFalse(result["native_replay_or_model_load_performed"])
        self.assertEqual(set(result["pilot_evidence"]), {"qwen3-1.7b-base", "qwen3-4b-base"})

    def test_failed_transport_receipt_query_or_training_probe_is_rejected(self):
        def failed_transport(values, selected, reader): values["transport"]["actual_ssh_exit_code"] = 1
        def no_actual_receipt(values, selected, reader): values["actual_completion"].pop("completion_chunk")
        def failed_slurm(values, selected, reader):
            sacct = values["response"]["result"]["scheduler"]["sacct"]
            sacct["stdout_stderr"] = sacct["stdout_stderr"].replace("COMPLETED|0:0", "FAILED|1:0")
        def wrong_probe(values, selected, reader): selected["throughput"]["sha256"] = "f" * 64
        for mutation in (failed_transport, no_actual_receipt, failed_slurm, wrong_probe):
            with self.subTest(mutation=mutation.__name__), self.assertRaises(ValueError): admit_fixture(mutation)

    def test_missing_real_smoke_stops_before_attempt_directory_or_transport(self):
        selected = choice()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); path = base / "choice.json"
            raw = c.canonical(selected); path.write_bytes(raw)
            args = SimpleNamespace(choice=str(path), choice_sha256=c.digest(raw), ledger_sha256="a" * 64)
            with patch.object(l, "HERE", base), patch.object(l, "admit_completed_smoke", side_effect=ValueError("missing actual smoke")), \
                 patch.object(l, "ssh_once", side_effect=AssertionError("forbidden SSH")):
                with self.assertRaises(ValueError): l.prepare(args)
            self.assertFalse((base / "attempts").exists())


class ChargePolicy(unittest.TestCase):
    def ledger(self):
        admission = admit_fixture()
        previous = {"p6-training-fresh-1.7b-v2-01": admission["pilot_evidence"]["qwen3-1.7b-base"],
            "p6-training-fresh-4b-v2-01": admission["pilot_evidence"]["qwen3-4b-base"], admission["attempt"]: admission}
        rows = [{"attempt": attempt, "gpus": 1, "allocated_seconds": item["seconds"],
                 **{key: item[key] for key in ("job_id", "seconds", "reservation_sha256")}} for attempt, item in previous.items()]
        return {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6, "automatic_retry": False,
            "gpu_seconds_reserved": 1800, "gpu_hours_allocated": 0.5, "gpu_reservations": rows}, admission

    def test_all_three_full_predecessor_charges_are_required(self):
        ledger, admission = self.ledger(); l.check_completed_predecessor_charges(ledger, admission)
        for mutation in ("missing", "refunded", "wrong_job"):
            changed = copy.deepcopy(ledger)
            if mutation == "missing": changed["gpu_reservations"].pop(0)
            if mutation == "refunded": changed["gpu_reservations"][-1]["allocated_seconds"] = 0
            if mutation == "wrong_job": changed["gpu_reservations"][-1]["job_id"] = "9009"
            with self.assertRaises(ValueError): l.check_completed_predecessor_charges(changed, admission)

    def test_new_families_and_full_ceiling_are_checked_without_touching_ledger(self):
        ledger, _ = self.ledger()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / "ledger.json"; raw = c.canonical(ledger); path.write_bytes(raw)
            charge = {"attempt": "student", "job_id": "998", "seconds": 600, "allocated_seconds": 600, "reservation_sha256": "f" * 64}
            with patch.object(l, "CAMPAIGN_FILE", path), patch.object(l, "charge_records", return_value=[charge]), self.assertRaises(ValueError):
                l.current_ledger(c.digest(raw), "qwen3-8b-base")
            self.assertEqual(path.read_bytes(), raw)
        source = (Path(l.__file__)).read_text()
        self.assertIn("p7-student-launchers-v*/attempts/*/release/charge-intent.json", source)
        self.assertIn("p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json", source)
        ledger["gpu_seconds_reserved"] = 21601
        with self.assertRaises(ValueError): l.ledger_seconds(ledger)

    def test_charge_is_written_before_one_unknown_release_and_kept(self):
        ledger, admission = self.ledger()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve(); (directory / "submit").mkdir()
            l.put(directory / "submit/transport-completion.json", {"actual_ssh_exit_code": 0, "stop_reason": None, "owned_child_reaped": True})
            l.put(directory / "submit/response.json", {"result": {"actual_sbatch_exit_code": 0, "held": True, "released": False, "job_id": "8888", "uid": 105923}})
            calls = []
            def uncertain(path, payload):
                charge = json.loads((path / "charge-intent.json").read_bytes())
                self.assertEqual(charge["allocated_seconds"], 600); calls.append(payload)
                raise ValueError("synthetic unknown release")
            args = SimpleNamespace(action="release", model_key="qwen3-8b-base", prepared_sha256="a" * 64, ledger_sha256="b" * 64)
            with patch.object(l, "load_prepared", return_value=(directory, {"smoke_admission": admission}, allocation(), {})), \
                 patch.object(l, "current_ledger", return_value=(ledger, c.canonical(ledger), 1800)), patch.object(l, "execute_phase", side_effect=uncertain):
                with self.assertRaises(ValueError): l.mutate_phase(args)
                with self.assertRaises(FileExistsError): l.mutate_phase(args)
            self.assertEqual(len(calls), 1)


class ExactReuse(unittest.TestCase):
    def functions(self, path):
        return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_bytes()).body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef))}

    def test_remote_resource_queue_source_command_and_collect_helpers_are_unchanged(self):
        before = self.functions(l.HERE.parent / "p6-training-launchers-v2/remote_training_control.py")
        after = self.functions(Path(c.__file__))
        for name in before.keys() - {"validate_spec"}: self.assertEqual(before[name], after[name], name)

    def test_local_transport_ledger_and_final_saved_artifact_admission_are_unchanged(self):
        before = self.functions(l.HERE.parent / "p6-training-launchers-v2/training_launchers.py")
        after = self.functions(Path(l.__file__))
        for name in ("ssh_once", "execute_phase", "ledger_seconds", "check_charges", "summarize", "progress_snapshot", "phase_lock", "bundle_inputs"):
            self.assertEqual(before[name], after[name], name)


if __name__ == "__main__":
    unittest.main()
