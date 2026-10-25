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
    """Synthetic transport-shape fixtures, never evidence accepted by admit_pair."""
    result = {}
    for model in c.PILOTS:
        recovered = model == "qwen3-1.7b-base"
        original = {"job_id": "21912020" if recovered else "90002", "attempt": c.PILOTS[model][0],
            "seconds": 1200 if recovered else 2100, "reservation_sha256": "a" * 64,
            "source_root": c.SOURCE if recovered else c.FRESH4_SOURCE,
            "source_pins_sha256": c.SOURCE_MAP_SHA if recovered else c.FRESH4_MAP_SHA,
            "provider_sha256": c.PROVIDER_SHA, "slurm_state": "FAILED" if recovered else "COMPLETED",
            "slurm_exit_code": "1:0" if recovered else "0:0", "process_exit_code": 1 if recovered else 0,
            "controller_completed": not recovered}
        if not recovered: original["controller_sha256"] = c.FRESH4_CONTROLLER_SHA
        recovery = None if not recovered else {"job_id": "90003", "attempt": c.RECOVERY_ATTEMPT,
            "seconds": 300, "reservation_sha256": "b" * 64, "selector": "import4", "slurm_state": "COMPLETED",
            "slurm_exit_code": "0:0", "process_exit_code": 0, "status": "saved_adapter_independent_reload_complete",
            "runtime_source_root": c.RECOVERY_SOURCE, "runtime_source_pins_sha256": c.RECOVERY_MAP_SHA,
            "runtime_provider_sha256": c.RECOVERY_PROVIDER_SHA, "runtime_manifest_sha256": c.RECOVERY_MANIFEST_SHA,
            "runtime_inference_only": True, "runtime_training_execution_allowed": False,
            "cpu_metadata_sha256": "c" * 64, "cpu_actual_sha256": "d" * 64,
            "plan_derivation": {"synthetic": True}, "adapter_config_admission": {"synthetic": True}}
        manifest = "3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135" if recovered else "e" * 64
        files = {path: {"bytes": 1, "sha256": "f" * 64} for path in sorted(c.pilot_remote_paths(model))}
        files[c.pilot_artifact(model) + "/manifest.json"]["sha256"] = manifest
        if recovered:
            files[c.RECOVERY_PACKAGE + "/metadata-recovery-import4.json"]["sha256"] = recovery["cpu_metadata_sha256"]
            files[c.RECOVERY_PACKAGE + "/metadata-actual-completion-import4.json"]["sha256"] = recovery["cpu_actual_sha256"]
            files[str(Path(c.RECOVERY_SOURCE).parent / "manifest.json")]["sha256"] = c.RECOVERY_MANIFEST_SHA
        row = {key: {} for key in c.ADMISSION_FIELDS}
        row.update(schema="hydra-pilot-completion-admission-v2", kind=c.ADMISSION_KINDS[model], model_key=model,
            job_id=original["job_id"], artifact_directory=c.pilot_artifact(model),
            base_directory=c.CAMPAIGN + "/authenticated-bases-01/" + model,
            manifest_sha256=manifest, final_tensor_population_sha256=(
                "2499801811ee63fb4f6c20e022d59aa0eeb2bb202ee41c9edd6bcd271e646c3c" if recovered else "e" * 64),
            training_exposure={"synthetic_metadata_fixture_only": True}, original_training=original, recovery=recovery,
            normal_training_success=not recovered, original_failure_preserved=recovered,
            prior_independent_reload_completed=recovered, remote_files=files, admission_source_sha256=c.ADMISSION_SHA,
            reload_required_in_each_paired_case=True, adapter_reload_admitted_for_future_inference=False,
            quality_evaluated=False, automatic_retry=False)
        result[model] = row
    return result


def spec():
    return {**c.fixed_spec_fields(), "nonce": "a" * 32, "manifest_content_sha256": "b" * 64, "pilot_evidence": pilots()}


def pack(raw):
    return {"bytes": len(raw), "sha256": c.digest(raw), "base64": c.base64.b64encode(raw).decode(),
        "offset": 0, "file_bytes_before": len(raw), "file_bytes_after": len(raw), "stable": True, "complete_file": True}


def packed(value):
    return pack(c.canonical(value) + b"\n")





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
        with self.assertRaises(ValueError): l.validate_choice({"schema": "hydra-p6-8b-smoke-evidence-choice-v2", "pilots": {}, "seconds": 600})

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
        self.assertEqual(l.admission_api().KINDS, c.ADMISSION_KINDS)
        expected = l.expected_smoke_pins(source_map)
        self.assertGreater(len(expected), 100)
        self.assertEqual(expected[c.SMOKE], c.SMOKE_SHA)





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

    def test_original_failure_recovery_and_normal_pilot_all_remain_fully_charged(self):
        admitted = pilots()
        allocations = [item for row in admitted.values() for item in (row["original_training"], row["recovery"]) if item]
        rows = [{key: item[key] for key in ("attempt", "job_id", "seconds", "reservation_sha256")} | {
            "gpus": 1, "allocated_seconds": item["seconds"]} for item in allocations]
        ledger = {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6,
            "automatic_retry": False, "gpu_hours_allocated": 1, "gpu_seconds_reserved": 3600, "gpu_reservations": rows}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp).resolve() / "ledger.json"
            def check(value, charges=()):
                raw = c.canonical(value); path.write_bytes(raw)
                with patch.object(l, "CAMPAIGN_FILE", path), patch.object(l, "charge_records", return_value=charges):
                    return l.current_ledger(c.digest(raw), admitted)
            self.assertEqual(check(ledger)[2], 3600)
            for mutation in ("refund_failure", "omit_recovery", "replace_reservation", "over_budget", "reuse_attempt"):
                changed = copy.deepcopy(ledger)
                if mutation == "refund_failure": changed["gpu_reservations"][0]["allocated_seconds"] = 12
                if mutation == "omit_recovery": changed["gpu_reservations"] = [r for r in rows if r["attempt"] != c.RECOVERY_ATTEMPT]
                if mutation == "replace_reservation": changed["gpu_reservations"][0]["reservation_sha256"] = "f" * 64
                if mutation == "over_budget": changed["gpu_seconds_reserved"] = 21500
                if mutation == "reuse_attempt": changed["gpu_reservations"].append({"attempt": c.ATTEMPT, "job_id": "90004",
                    "seconds": 600, "allocated_seconds": 600, "reservation_sha256": "e" * 64, "gpus": 1})
                with self.subTest(mutation=mutation), self.assertRaises(ValueError): check(changed)
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


class ExplicitPrerequisiteAdmission(unittest.TestCase):
    def test_shared_reader_is_exact_import4_and_rejects_old_or_missing_routes(self):
        api = l.admission_api()
        self.assertEqual(c.digest((l.BASE / "pilot-completion-admission-v3/pilot_admission.py").read_bytes()), c.ADMISSION_SHA)
        self.assertEqual(api.RECOVERY, "p6-postsave-recovery-v4")
        self.assertEqual(api.CPU_REPORT, "metadata-recovery-import4.json")
        for descriptors in ({}, {key: {} for key in c.PILOTS}, {key: {"kind": "normal_v2"} for key in c.PILOTS}):
            with self.assertRaises(ValueError): api.admit_pair(descriptors, root=l.ROOT)
        with self.assertRaises(ValueError): api.actual_outer({"actual_exit_code": 1, "completion_chunk": "abcdef"})

    def test_original_failure_successful_recovery_and_exact_new_sources(self):
        c.validate_pilots(pilots())
        for mutation in ("no_recovery", "old_selector", "old_runtime", "retcon", "old_4b", "failed_recovery", "bad_cpu_pin", "exposure"):
            rows = pilots(); small, large = rows["qwen3-1.7b-base"], rows["qwen3-4b-base"]
            if mutation == "no_recovery": small["recovery"] = None
            if mutation == "old_selector": small["recovery"]["selector"] = "base3"
            if mutation == "old_runtime": small["recovery"]["runtime_provider_sha256"] = c.PROVIDER_SHA
            if mutation == "retcon": small["original_training"]["controller_completed"] = True
            if mutation == "old_4b": large["original_training"]["source_root"] = c.SOURCE
            if mutation == "failed_recovery": small["recovery"]["process_exit_code"] = 1
            if mutation == "bad_cpu_pin": small["recovery"]["cpu_metadata_sha256"] = "e" * 64
            if mutation == "exposure": large["training_exposure"] = {"different": True}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_pilots(rows)

    def test_remote_inventory_is_exact_bounded_and_never_reads_weights(self):
        self.assertEqual([len(c.pilot_remote_paths(k)) for k in c.PILOTS], [16, 7])
        for mutation in ("missing", "extra", "oversize_file", "oversize_records"):
            rows = pilots(); row = rows["qwen3-1.7b-base"]
            if mutation == "missing": row["remote_files"].pop(next(iter(row["remote_files"])))
            if mutation == "extra": row["remote_files"][c.pilot_artifact("qwen3-1.7b-base") + "/adapter/model.safetensors"] = {"bytes": 1, "sha256": "e" * 64}
            if mutation == "oversize_file": next(iter(row["remote_files"].values()))["bytes"] = 2 * 1024**2 + 1
            if mutation == "oversize_records": row["evidence"] = {"x": "x" * c.MAX_PILOT_RECORD_BYTES}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_pilots(rows)

    def test_remote_hash_and_size_recheck_rejects_changes_after_local_admission(self):
        # Isolate byte revalidation from the separately tested signed-input shape.
        rows = pilots(); raw = {}
        for row in rows.values():
            for path in row["remote_files"]:
                raw[path] = ("synthetic-file:" + path).encode()
                row["remote_files"][path] = {"bytes": len(raw[path]), "sha256": c.digest(raw[path])}
        def read(path, _limit): return raw[str(path)]
        with patch.object(c, "validate_pilots") as shape, patch.object(c.Path, "exists", return_value=False),              patch.object(c, "ordinary_bytes", side_effect=read) as reader:
            c.verify_pilot_files(rows)
            shape.assert_called_once_with(rows)
            self.assertEqual(reader.call_count, 23)
            name = c.RECOVERY_PACKAGE + "/metadata-actual-completion-import4.json"
            raw[name] = bytes([raw[name][0] ^ 1]) + raw[name][1:]
            with self.assertRaises(ValueError): c.verify_pilot_files(rows)
        with patch.object(c.Path, "exists", return_value=True), self.assertRaises(ValueError):
            c.verify_pilot_files(pilots())

    def test_prerequisite_wiring_uses_shared_admission_not_normal_v2_reader(self):
        rows = pilots(); descriptors = {model: {"kind": c.ADMISSION_KINDS[model]} for model in c.PILOTS}
        cpu = {"schema": "hydra-p6-actual-cpu-prerequisite-v1", "completed": True, "scheduler_helper_sha256": c.SMOKE_SHA,
            **{key: True for key in ("positive_proof_replayed", "negative_probe_rejected", "owned_cleanup_verified")},
            **{key: 0 for key in ("actual_process_exit_code", "actual_scheduler_query_exit_code", "actual_collector_tool_exit_code")},
            "actual_scheduler_state": "COMPLETED", "actual_scheduler_exit": "0:0", "actual_collector_completion_chunk": "synthetic",
            "evidence_files": {"fixture" + str(i): "e" * 64 for i in range(3)}}
        transfer = {"actual_ssh_exit_code": 0, "archive_sha256": c.ARCHIVE_SHA, "archive_bytes": 10257464,
            "remote_directory": str(Path(c.SOURCE).parent)}
        base = {"completed": True, "models": {c.MODEL_KEY: {"identity": {"base_identity_sha256": c.BASE_SHA}}}}
        def read(path, *args, **kwargs):
            name = str(path)
            if name.endswith("p6-cpu-prerequisite-01.json"): return c.canonical(cpu)
            if name.endswith("p6-transfer-06/actual-completion.json"): return c.canonical(transfer)
            if name.endswith("p6-clean-base-admission-01/stdout.jsonl"): return c.canonical(base)
            if Path(name).name.startswith("fixture"): return b"synthetic"
            raise AssertionError("Unexpected metadata read: " + name)
        from unittest.mock import Mock
        api = SimpleNamespace(admit_pair=Mock(return_value=rows))
        with patch.object(l, "read", side_effect=read), patch.object(l, "admission_api", return_value=api):
            self.assertEqual(l.prerequisites({"schema": "hydra-p6-8b-smoke-evidence-choice-v2", "pilots": descriptors}, {}), rows)
        api.admit_pair.assert_called_once_with(descriptors, root=l.ROOT)

    def test_all_seven_charge_families_and_remote_rechecks_are_retained(self):
        globs = l.admission_api().CHARGE_GLOBS
        self.assertEqual(len(globs), 7)
        self.assertIn("p6-postsave-recovery-v*/attempts/*/release/charge-intent.json", globs)
        self.assertIn("p7-student-launchers-v*/attempts/*/release/charge-intent.json", globs)
        source = ast.parse(Path(c.__file__).read_bytes())
        functions = {n.name: n for n in source.body if isinstance(n, ast.FunctionDef)}
        for name in ("submit", "release"):
            self.assertIn("verify_sources", [n.func.id for n in ast.walk(functions[name]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)])
        self.assertIn("verify_pilot_files", [n.func.id for n in ast.walk(functions["verify_sources"]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)])

    def test_unchanged_gpu_and_transport_functions_have_exact_old_ast(self):
        def functions(path):
            return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_bytes()).body
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        old = l.BASE / "p6-8b-smoke-launchers-v1"
        for filename, names in (("remote_smoke_control.py", ("job_script", "reservation", "bounded_command", "Phase", "submit", "release", "collect", "snapshot", "check_held", "check_queue_row")),
            ("smoke_launchers.py", ("ssh_once", "mutate_phase", "collect", "summarize", "execute_phase", "ledger_seconds", "check_charges", "bundle_inputs", "expected_smoke_pins"))):
            before, after = functions(old / filename), functions(Path(l.__file__).parent / filename)
            for name in names: self.assertEqual(before[name], after[name], filename + ":" + name)


if __name__ == "__main__":
    unittest.main()
