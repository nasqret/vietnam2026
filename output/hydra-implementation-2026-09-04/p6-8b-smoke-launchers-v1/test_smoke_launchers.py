"""Synthetic metadata/transport tests only; no real job, child, or model."""
import ast
import copy
import json
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import remote_smoke_control as c
import smoke_launchers as l


def pilots():
    return {model: {"job_id": str(1001 + i), "seconds": 600,
        **{key: str(i + 1) * 64 for key in ("reservation_sha256", "manifest_sha256", "completion_sha256", "request_sha256", "base_identity_sha256")}}
        for i, model in enumerate(c.PILOTS)}


def spec():
    return {**c.fixed_spec_fields(), "nonce": "a" * 32, "manifest_content_sha256": "b" * 64, "pilot_evidence": pilots()}


def pack(raw):
    return {"bytes": len(raw), "sha256": c.digest(raw), "base64": c.base64.b64encode(raw).decode(),
        "offset": 0, "file_bytes_before": len(raw), "file_bytes_after": len(raw), "stable": True, "complete_file": True}


def packed(value):
    return pack(c.canonical(value) + b"\n")


def pilot_fixture(model, number):
    """Fabricated completion made from real pinned plan metadata; no pilot ran."""
    reader = l.training_reader()
    manifest, launch, source_map = reader.bundle_inputs()
    choice = {"schema": "hydra-p6-training-allocation-choice-v1", "model_key": model, "seconds": 600,
        "soft_limit_seconds": 540, "throughput": {}, "transfer_receipt": {}, "base_admission": {}}
    allocation = reader.make_spec(choice, "a" * 32, c.digest(c.canonical(manifest)))
    record = reader.control.reservation(allocation, str(number), c.UID)
    plan = json.loads(reader.read(reader.ROOT / launch["models"][model]["prepared_plan"]["path"]))
    audit = {key: 256 for key in ("expected_optimizer_boundaries", "observed_optimizer_boundaries",
        "raw_finite_optimizer_boundaries", "post_clip_finite_optimizer_boundaries")}
    audit.update(first_optimizer_step=1, last_optimizer_step=256)
    update = {"changed_parameter_tensors": 1, "initial_tensor_population_sha256": "a" * 64,
        "final_tensor_population_sha256": "b" * 64, "trainable_parameter_tensors": 392, "final_finite_parameter_tensors": 392}
    saved = {"schema": "hydra-decision-pilot-artifact-v1", "profile": "hydra-fresh-decision-pilot-v2", "model_trained": True,
        "actual_optimizer_steps": 256, "model": reader.control.MODELS[model]["model"], "automatic_retry": False,
        "resume": False, "plan": plan, "base": {"base_identity_sha256": "c" * 64}, "finite_gradient_audit": audit,
        "adapter_update": update, "saved_adapter_reload_admission": "required_by_P6_before_inference"}
    artifact = {"manifest_path": reader.control.MODELS[model]["artifact"] + "/manifest.json", "manifest_sha256": packed(saved)["sha256"],
        "actual_optimizer_steps": 256, "finite_gradient_audit": audit, "adapter_update": update,
        "base_identity_sha256": "c" * 64, "saved_adapter_reload_admission": "required_by_P6_before_inference"}
    completion = {"schema": "hydra-p6-remote-training-completion-v1", "completed": True, "error": None,
        "sources_unchanged": True, "execute_invoked": True, "optimizer_steps_observed": 256,
        "actual_optimizer_steps_in_complete_artifact": 256, "source_pins_after": source_map,
        "automatic_retry": False, "resume": False, "training_artifact": artifact}
    accounting = "|".join([record["job_id"], allocation["job_name"], c.REMOTE_USER, c.ACCOUNT, c.PARTITION,
        "COMPLETED", "0:0", "420", "10", "8", "64G", "cpu=8,mem=64G,node=1,gres/gpu=1",
        "cpu=8,mem=64G,node=1,gres/gpu=1", "gh200-node"]) + "\n"
    observation = {"job_id": record["job_id"], "read_only": True,
        "scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None, "stdout_stderr": accounting}},
        "files": {"job/actual-process-exit.txt": pack(b"0\n"), "artifact/manifest.json": packed(saved),
            "job/result/artifact-receipt.json": packed(artifact), "job/result/completion.json": packed(completion),
            "job/result/request.json": packed({"reservation": record, "reservation_sha256": c.digest(c.canonical(record) + b"\n"),
                                               "source_pins_before": source_map})}}
    values = {"response": {"schema": "hydra-p6-training-control-phase-v1", "phase": "collect", "completed": True,
        "error": None, "result": observation}, "transport": {"actual_ssh_exit_code": 0, "owned_child_reaped": True,
        "stop_reason": None, "remote_script_sha256": l.TRAINING_PINS["remote_training_control.py"]},
        "actual_completion": {"actual_exit_code": 0, "completion_chunk": "synthetic_test_only"}}
    return reader, manifest, values


class FixedContract(unittest.TestCase):
    def test_gpu_argv_matches_smoke08_except_fixed_model_config_and_fresh_job(self):
        original = (l.BASE / "submit_p6_smoke_scheduler_v3.py").read_text()
        main = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == "main")
        node = next(n.value for n in main.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "command" for t in n.targets))
        expected = eval(compile(ast.Expression(node), "fixed-command-list", "eval"), {"__builtins__": {}},
            {"PROJECT": c.PROJECT, "SOURCE": c.SOURCE, "CAMPAIGN": c.CAMPAIGN, "JOB": spec()["remote_job_directory"]})
        expected = [part.replace("qwen3-4b-base", c.MODEL_KEY).replace("qwen3_4b_decisions", "qwen3_8b_decisions")
                    .replace("RESERVATION_SHA_PLACEHOLDER", "$HYDRA_RESERVATION_SHA") for part in expected]
        script = c.job_script(spec())
        actual = next(shlex.split(line) for line in script.splitlines() if line.startswith(c.PROJECT + "/.venv-helios/bin/python "))
        self.assertEqual(actual, expected)
        self.assertNotIn("--adapter-directory", script)
        self.assertNotIn("remote_training_pilot.py", script)

    def test_no_model_duration_adapter_update_or_argv_overrides(self):
        for name, value in (("seconds", 660), ("gpus", True), ("model_key", "qwen3-4b-base"),
            ("optimizer_updates", 1), ("source", "/tmp/other"), ("maximum_gradient_examples", 0),
            ("adapter_directory", "/tmp/adapter"), ("argv", ["other"])):
            altered = spec(); altered[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                c.validate_spec(altered)

    def test_missing_or_reused_pilot_identity_is_rejected(self):
        value = pilots(); del value["qwen3-4b-base"]
        with self.assertRaises(ValueError): c.validate_pilots(value)
        value = pilots(); value["qwen3-4b-base"]["job_id"] = value["qwen3-1.7b-base"]["job_id"]
        with self.assertRaises(ValueError): c.validate_pilots(value)
        with self.assertRaises(ValueError): l.validate_choice({"schema": "hydra-p6-8b-smoke-evidence-choice-v1", "pilots": {}, "seconds": 600})

    def test_reservation_schema_is_exact_frozen_smoke_not_training(self):
        result = c.reservation(spec(), "12345", c.UID)
        self.assertEqual(result["schema"], "hydra-p6-smoke-reservation-v1")
        self.assertEqual(set(result), {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
                                     "model_key", "gpus", "nodes", "cpus", "memory_gib", "seconds"})
        with self.assertRaises(ValueError): c.reservation(spec(), "12345", c.UID + 1)

    def test_sealed_bundle08_contract_and_plan_metadata(self):
        _, launch, source_map = l.bundle_inputs()
        self.assertEqual(launch["models"][c.MODEL_KEY]["plan_sha256"], c.PLAN_SHA)
        self.assertEqual(source_map[c.SMOKE]["sha256"], c.SMOKE_SHA)
        self.assertEqual(l.training_reader().control.MODELS.keys(), c.PILOTS.keys())
        expected = l.expected_smoke_pins(source_map)
        self.assertGreater(len(expected), 100)
        self.assertEqual(expected[c.SMOKE], c.SMOKE_SHA)


class PilotAdmission(unittest.TestCase):
    def test_two_distinct_complete_synthetic_pilots_are_admitted(self):
        for number, model in enumerate(c.PILOTS, 2001):
            reader, manifest, values = pilot_fixture(model, number)
            with patch.object(l, "evidence", side_effect=lambda name: c.canonical(values[name])):
                result = l.admit_pilot(model, {key: key for key in values}, reader, manifest, "c" * 64)
            self.assertEqual(result["job_id"], str(number))
            self.assertEqual(result["manifest_sha256"], values["response"]["result"]["files"]["artifact/manifest.json"]["sha256"])

    def test_missing_actual_receipt_failed_slurm_and_incomplete_training_stop_admission(self):
        reader, manifest, original = pilot_fixture("qwen3-4b-base", 2002)
        for mutation in ("receipt", "slurm", "steps", "changed_base", "changed_bytes"):
            values = copy.deepcopy(original)
            expected_base = "c" * 64
            if mutation == "receipt": values["actual_completion"]["actual_exit_code"] = 1
            if mutation == "slurm": values["response"]["result"]["scheduler"]["sacct"]["stdout_stderr"] = values["response"]["result"]["scheduler"]["sacct"]["stdout_stderr"].replace("COMPLETED|0:0", "FAILED|1:0")
            if mutation == "steps":
                obs = values["response"]["result"]
                completion = reader.complete_json(obs, "job/result/completion.json"); completion["optimizer_steps_observed"] = 255
                obs["files"]["job/result/completion.json"] = packed(completion)
            if mutation == "changed_base": expected_base = "d" * 64
            if mutation == "changed_bytes": values["response"]["result"]["files"]["artifact/manifest.json"]["sha256"] = "f" * 64
            with self.subTest(mutation=mutation), patch.object(l, "evidence", side_effect=lambda name: c.canonical(values[name])), self.assertRaises(ValueError):
                l.admit_pilot("qwen3-4b-base", {key: key for key in values}, reader, manifest, expected_base)


class QueueAndCharges(unittest.TestCase):
    def test_actual_shaped_pending_range_and_null_tres_remain_narrow(self):
        request = spec(); directory = request["remote_job_directory"]
        row = {"JobId": "123", "JobName": request["job_name"], "Comment": "hydra-p6:" + request["nonce"],
            "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0", "Account": c.ACCOUNT,
            "Partition": c.PARTITION, "NumCPUs": "8", "NumNodes": "1-1", "TimeLimit": "00:10:00", "UserId": "plgnasqret(105923)",
            "Command": directory + "/job.sbatch", "WorkDir": directory, "StdOut": directory + "/slurm.out", "StdErr": directory + "/slurm.err",
            "ReqTRES": "cpu=8,mem=64G,node=1,gres/gpu=1", "AllocTRES": "(null)"}
        c.check_held(row, request, "123", c.UID)
        self.assertEqual(c.check_queue_row("123", row, "123")["allocated_tres"], {})
        with self.assertRaises(ValueError): c.check_queue_row("123", row)
        for key, value in (("NumNodes", "1-2"), ("ReqTRES", "cpu=8,mem=64G,node=2,gres/gpu=1"), ("Restarts", "1")):
            changed = dict(row); changed[key] = value
            with self.assertRaises(ValueError): c.check_held(changed, request, "123", c.UID)
        cpu = {"ArrayJobId": "50", "ArrayTaskId": "2", "ReqTRES": "cpu=2,mem=4G,node=1", "AllocTRES": "(null)"}
        self.assertTrue(c.check_queue_row("50_2", cpu)["left_unchanged"])

    def test_full_charge_and_both_pilots_must_be_reconciled(self):
        rows = [{"attempt": attempt, "job_id": pilots()[model]["job_id"], "seconds": 600, "gpus": 1,
            "allocated_seconds": 600, "reservation_sha256": pilots()[model]["reservation_sha256"]}
            for model, (attempt, _) in c.PILOTS.items()]
        ledger = {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6,
            "automatic_retry": False, "gpu_hours_allocated": 1200 / 3600, "gpu_seconds_reserved": 1200, "gpu_reservations": rows}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp).resolve() / "ledger.json"
            def check(value, charges=()):
                raw = c.canonical(value); path.write_bytes(raw)
                with patch.object(l, "CAMPAIGN_FILE", path), patch.object(l, "charge_records", return_value=charges):
                    return l.current_ledger(c.digest(raw), pilots())
            self.assertEqual(check(ledger)[2], 1200)
            changed = copy.deepcopy(ledger); changed["gpu_reservations"][0]["allocated_seconds"] = 12
            with self.assertRaises(ValueError): check(changed)
            changed = copy.deepcopy(ledger); changed["gpu_reservations"][0]["reservation_sha256"] = "f" * 64
            with self.assertRaises(ValueError): check(changed)
            changed = copy.deepcopy(ledger); changed["gpu_seconds_reserved"] = 21500
            with self.assertRaises(ValueError): check(changed)
            charge = {"attempt": "other-family", "job_id": "808", "seconds": 600, "allocated_seconds": 600, "reservation_sha256": "f" * 64}
            with self.assertRaises(ValueError): check(ledger, [charge])

    def test_release_charge_precedes_unknown_transport_and_survives_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp).resolve(); (directory / "submit").mkdir()
            l.put(directory / "submit/transport-completion.json", {"actual_ssh_exit_code": 0, "owned_child_reaped": True,
                "output_complete": True, "stop_reason": None})
            l.put(directory / "submit/response.json", {"result": {"actual_sbatch_exit_code": 0, "held": True,
                "released": False, "job_id": "123", "uid": c.UID}})
            calls = []
            def uncertain(path, payload):
                charge = json.loads((path / "charge-intent.json").read_bytes())
                self.assertEqual(charge["allocated_seconds"], 600)
                self.assertFalse(charge["refund_allowed_automatically"])
                calls.append(payload)
                raise ValueError("synthetic uncertain transport")
            args = SimpleNamespace(action="release", prepared_sha256="a" * 64, ledger_sha256="b" * 64)
            with patch.object(l, "load_prepared", return_value=(directory, {}, spec(), {})), \
                 patch.object(l, "current_ledger", return_value=({}, b"{}", 1200)), patch.object(l, "execute_phase", side_effect=uncertain):
                with self.assertRaises(ValueError): l.mutate_phase(args)
                with self.assertRaises(FileExistsError): l.mutate_phase(args)
            self.assertEqual(len(calls), 1)
            self.assertTrue((directory / "release/charge-intent.json").is_file())

    def test_collection_whitelist_has_no_weights_or_arbitrary_paths(self):
        self.assertEqual(c.MAX_OBSERVATION, 8 * 1024**2)
        self.assertEqual(c.MAX_RESPONSE, 14 * 1024**2)
        self.assertTrue(all(name.startswith("job/") and ".." not in name for name in c.FILES))
        self.assertFalse(any(name.endswith((".safetensors", ".bin")) for name in c.FILES))
        with self.assertRaises(ValueError): l.validate_observation({"read_only": True, "files": {"job/weights.bin": pack(b"x")}})


class SmokeResultAdmission(unittest.TestCase):
    def fixture(self):
        allocation = spec(); record = c.reservation(allocation, "8001", c.UID)
        _, _, source_map = l.bundle_inputs(); source_pins = l.expected_smoke_pins(source_map)
        identity = {"schema": "hydra-experimental-loaded-model-v1", "profile": "hydra-experimental-torch-qwen3-v2",
            **c.MODEL, "source_sha256": c.PROVIDER_SHA, "base_identity_sha256": c.BASE_SHA,
            "model_loaded": True, "adapter": {"adapter_present": False}, "allocation": {"job_id": record["job_id"]}}
        identity["model_manifest_sha256"] = c.digest(c.canonical(identity))
        request = {"schema": "hydra-p6-remote-smoke-request-v1", "reservation": record,
            "reservation_sha256": c.digest(c.canonical(record) + b"\n"), "source_pins_before": source_pins,
            "provider_sha256": c.PROVIDER_SHA, "base_directory": c.CAMPAIGN + "/authenticated-bases-01/" + c.MODEL_KEY,
            "adapter_directory": None, "optional_throughput_examples": 8}
        completion = {"schema": "hydra-p6-remote-smoke-completion-v1", "completed": True, "error": None,
            "sources_unchanged": True, "source_pins_after": source_pins, "transport_and_inference_passed": True,
            "optimizer_updates": 0, "model_trained_by_probe": False, "automatic_retry": False,
            "session": {"identity": identity, "actual_model_calls": 2, "forward_passes": 2, "generated_token_slots": 32}}
        probe = {"schema": "hydra-completion-gradient-probe-v1", "status": "complete", "model": c.MODEL,
            "plan_sha256": c.PLAN_SHA, "max_examples": 8, "examples_completed": 8, "forward_calls": 8,
            "backward_calls": 8, "optimizer_steps": 0, "optimizer_created": False, "finite_gradients": True,
            "trainable_tensors_unchanged": True, "model_trained": False, "adapter_saved": False, "elapsed_seconds": 0.5}
        accounting = "|".join([record["job_id"], allocation["job_name"], c.REMOTE_USER, c.ACCOUNT, c.PARTITION,
            "COMPLETED", "0:0", "40", "10", "8", "64G", "cpu=8,mem=64G,node=1,gres/gpu=1",
            "cpu=8,mem=64G,node=1,gres/gpu=1", "gh200-node"]) + "\n"
        result = {"job_id": record["job_id"], "read_only": True,
            "scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None, "stdout_stderr": accounting}},
            "files": {"job/actual-process-exit.txt": pack(b"0\n"), "job/result/request.json": packed(request),
                "job/result/completion.json": packed(completion), "job/result/model-admission.json": packed(identity),
                "job/result/primitive.json": packed({"actual_model_calls": 1}), "job/result/planner.json": packed({"actual_model_calls": 1}),
                "job/result/throughput.json": packed(probe)}}
        return result, allocation, record, source_map

    def test_complete_synthetic_smoke_never_claims_training_or_quality(self):
        args = self.fixture(); result = l.summarize(*args)
        self.assertEqual(result["status"], "complete_base_provider_and_gradient_smoke", result)
        self.assertEqual(result["actual_model_calls"], 2)
        self.assertFalse(result["model_trained"])
        self.assertFalse(result["adapter_saved"])
        self.assertFalse(result["quality_evaluated"])

    def test_failed_accounting_missing_call_wrong_model_or_updates_cannot_pass(self):
        for mutation in ("slurm", "planner", "model", "updates"):
            observation, allocation, record, source_map = self.fixture()
            if mutation == "slurm": observation["scheduler"]["sacct"]["stdout_stderr"] = observation["scheduler"]["sacct"]["stdout_stderr"].replace("COMPLETED|0:0", "FAILED|1:0")
            if mutation == "planner": observation["files"]["job/result/planner.json"] = packed({"actual_model_calls": 0})
            if mutation == "model":
                identity = l.complete_json(observation, "job/result/model-admission.json"); identity["model_id"] = "Qwen/Qwen3-4B-Base"
                observation["files"]["job/result/model-admission.json"] = packed(identity)
            if mutation == "updates":
                probe = l.complete_json(observation, "job/result/throughput.json"); probe["optimizer_steps"] = 1
                observation["files"]["job/result/throughput.json"] = packed(probe)
            result = l.summarize(observation, allocation, record, source_map)
            self.assertNotEqual(result["status"], "complete_base_provider_and_gradient_smoke", mutation)
            self.assertFalse(result["gradient_probe_complete"], mutation)


class HelperDerivation(unittest.TestCase):
    def test_remote_control_helpers_are_exact_reviewed_copies(self):
        old = ast.parse((l.BASE / "p6-training-launchers-v2/remote_training_control.py").read_bytes())
        new = ast.parse(Path(c.__file__).read_bytes())
        def functions(module):
            return {node.name: ast.dump(node, include_attributes=False) for node in module.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        before, after = functions(old), functions(new)
        for name in ("require", "canonical", "digest", "integer", "wall_string", "ordinary_bytes", "save", "fields",
                     "tres", "check_queue_row", "check_held", "bounded_command", "Phase", "submit", "release", "snapshot"):
            self.assertEqual(before[name], after[name], name)


if __name__ == "__main__":
    unittest.main()
