"""Constructed-record/source tests only: no reserved theorem or runtime work."""
from copy import deepcopy
from hashlib import sha256
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import paired_common as common
import paired_controller as controller
import paired_case_worker as worker
import paired_summary as summary
import teacher_exposure as teacher
import prepare_distilled_study as prepare


def fresh():
    return {"training_rows": 2047, "validation_rows": 432, "expected_optimizer_steps": 256,
        "training_row_ids_sha256": "a" * 64, "validation_row_ids_sha256": "b" * 64,
        "dataset_sha256": common.DATASET_SHA, "holdout_sha256": common.HOLDOUT_SHA,
        "epochs": 1, "prompt_schema": "primitive_v4", "planner_rows_allowed": False,
        "objective_sha256": teacher.digest({"fixture": "unchanged-objective"})}


def artifact():
    data = {"schema": teacher.ATTESTATION_SCHEMA, "manifest_sha256": "d" * 64,
        "base_manifest_sha256": common.DATASET_SHA, "base_training_rows": 2047,
        "teacher_rows_added": 8, "training_rows": 2055, "validation_rows": 432,
        "holdout_sha256": common.HOLDOUT_SHA, "selection_sha256": teacher.SELECTION_SHA,
        "reserved_intermediate_check": "exact_closed_AST_plus_declared_template_exclusions",
        "teacher_source_scope": "complete_teacher_proposed_native_continuation",
        "regenerated_byte_exact": True, "base_train_prefix_preserved": True, "validation_test_unchanged": True,
        "fresh_verified_continuations": 2, "actual_teacher_model_calls": 4,
        "teacher_model_manifest_sha256": "e" * 64,
        "teacher_input_spec": {"path": "fixture/spec.json", "sha256": "f" * 64},
        "fresh_replay_manifest": {"path": "fixture/replay.json", "sha256": "1" * 64}}
    plan = {"schema": teacher.PLAN_SCHEMA, "profile": teacher.PROFILE, "model": deepcopy(teacher.MODEL),
        "epochs": 1, "resume": False, "automatic_retry": False, "prompt_schema": "primitive_v4",
        "planner_rows_allowed": False, "initialization": "fresh_pinned_base_new_lora", "model_trained": False,
        "data_attestation": data, "training_rows": 2055, "validation_rows": 432,
        "training_row_ids_sha256": "2" * 64, "validation_row_ids_sha256": "b" * 64,
        "expected_optimizer_steps": 257, "config_sha256": "3" * 64,
        "objective": {"fixture": "unchanged-objective"}}
    plan["plan_sha256"] = teacher.digest(plan)
    return {"schema": "hydra-decision-pilot-artifact-v1", "profile": teacher.PROFILE,
        "model": deepcopy(teacher.MODEL), "model_trained": True, "resume": False, "automatic_retry": False,
        "saved_adapter_reload_admission": "required_by_P6_before_inference", "plan": plan,
        "actual_optimizer_steps": 257, "token_preflight": {"fixture": True},
        "reservation": {"job_id": "123456"}, "final_reservation": {"job_id": "123456"}}


def repin(record):
    record["plan"]["plan_sha256"] = teacher.digest({k: v for k, v in record["plan"].items() if k != "plan_sha256"})
    return record


def study():
    value = artifact()
    arms = {name: {"model_key": "qwen3-1.7b-base", "base_directory": "/fixture/base",
        "adapter_directory": "/fixture/" + name, "adapter_manifest_sha256": ("4" if name == "fresh_1_7b" else "5") * 64,
        "adapter_kind": teacher.PUBLIC_KIND if name == "distilled_1_7b" else teacher.TENSOR_KIND}
        for name in ("fresh_1_7b", "distilled_1_7b")}
    return {"schema": "hydra-p7-teacher-paired-study-v1", "study_id": "constructed-pure-fixture",
        "scope": "paired5", "comparison": "fixed_native_work_guarded", "wall_profile": "guarded-work-60-v1",
        "holdout_sha256": common.HOLDOUT_SHA, "slice_sha256": controller.SLICE_SHA,
        "source_pins_sha256": "6" * 64, "arms": arms, "features": deepcopy(common.FEATURES),
        "native_work": common.search_settings("guarded-work-60-v1"), "model_limits": deepcopy(common.MODEL_LIMITS),
        "resource_limits": deepcopy(common.RESOURCE_LIMITS), "fresh_training_exposure": fresh(),
        "distilled_training_exposure": teacher.teacher_training_exposure(value, fresh()),
        "teacher_admission": {"path": "fixture/admission.json", "bytes": 100, "sha256": "7" * 64},
        "training_allowed": False, "retrieval_allowed": False, "automatic_retry": False, "resume": False}


def collection():
    a = artifact()
    r = {"schema": "hydra-p7-student-update-reservation-v1", "model_key": "qwen3-1.7b-base", "uid": 105923,
        "account": "plgccaiautore2026-gpu-gh200", "partition": "plgrid-gpu-gh200", "job_name": "fixture-only",
        "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64, "seconds": 600, "job_id": "123456", "nonce": "8" * 32,
        "controller_sha256": teacher.FIXED_TEACHER["output/p7-prototype/distillation/remote_student_update.py"],
        "source_pins_sha256": teacher.digest({"fixture.py": {"sha256": "9" * 64, "bytes": 1}}),
        "plan_sha256": a["plan"]["plan_sha256"], "config_sha256": a["plan"]["config_sha256"], "dataset_sha256": "d" * 64}
    reservation_raw = common.canonical(r) + b"\n"
    request = {"schema": "hydra-p7-student-update-request-v1", "profile": teacher.PROFILE,
        "reservation": r, "reservation_sha256": sha256(reservation_raw).hexdigest(),
        "source_pins_before": {"fixture.py": {"sha256": "9" * 64, "bytes": 1}}}
    completion = {"schema": "hydra-p7-student-update-completion-v1", "profile": teacher.PROFILE,
        "completed": True, "error": None, "sources_unchanged": True, "source_pins_after": request["source_pins_before"],
        "actual_optimizer_steps": 257, "optimizer_callbacks_observed": 257, "teacher_rows_added": 8,
        "base_rows_preserved": 2047, "resume": False, "automatic_retry": False}
    claim = {"schema": "hydra-p7-student-update-consumption-v1", "job_id": r["job_id"], "nonce": r["nonce"],
        "reservation_sha256": request["reservation_sha256"], "plan_sha256": r["plan_sha256"],
        "dataset_sha256": r["dataset_sha256"], "resume": False, "automatic_retry": False}
    raw = {"job/actual-process-exit.txt": b"0\n", "job/reservation.json": reservation_raw,
        "job/reservation.json.claimed": common.canonical(claim), "job/result/request.json": common.canonical(request),
        "job/result/completion.json": common.canonical(completion), "job/result/prepared-plan.json": common.canonical(a["plan"]),
        "job/result/token-preflight.json": common.canonical(a["token_preflight"]),
        "job/result/trained-artifact.json": common.canonical(a) + b"\n",
        "artifact/manifest.json": json.dumps(a, indent=2).encode()}
    obs = {"job_id": r["job_id"], "read_only": True, "files": {}, "scheduler": {"sacct": {
        "actual_exit_code": 0, "stop_reason": None,
        "stdout_stderr": "|".join([r["job_id"], r["job_name"], "plgnasqret", r["account"], r["partition"],
            "COMPLETED", "0:0", "120", "10", "8", "64Gn", "cpu=8,mem=64G,gres/gpu=1,node=1",
            "cpu=8,mem=64G,gres/gpu=1,node=1", "fixture-node"])}}}
    for name, value in raw.items():
        obs["files"][name] = {"stable": True, "complete_file": True, "bytes": len(value), "sha256": sha256(value).hexdigest()}
    transport = {"actual_ssh_exit_code": 0, "owned_child_reaped": True, "stop_reason": None,
        "output_complete": True, "automatic_retry": False}
    return obs, transport, raw, a


class ExposureTests(unittest.TestCase):
    def test_constructed_nonempty_teacher_exposure_is_distinct(self):
        result = teacher.teacher_training_exposure(artifact(), fresh())
        self.assertEqual(result["teacher"]["teacher_rows_added"], 8)
        self.assertEqual(result["training_rows"], 2055)
        self.assertEqual(result["expected_optimizer_steps"], 257)
        with self.assertRaises(ValueError):
            common.training_exposure(artifact())

    def test_ordinary_or_wrong_student_cannot_be_relabelled(self):
        for field, replacement in (("schema", "hydra-decision-pilot-plan-v2"), ("profile", "hydra-fresh-decision-pilot-v2"),
                                  ("model", {"model_id": "Qwen/Qwen3-4B-Base", "revision": "0" * 40})):
            value = artifact(); value["plan"][field] = replacement; repin(value)
            with self.assertRaises(ValueError):
                teacher.teacher_training_exposure(value)

    def test_zero_unknown_or_unverified_yield_rejected(self):
        for key, replacement in (("teacher_rows_added", 0), ("teacher_rows_added", None), ("fresh_verified_continuations", 0),
            ("actual_teacher_model_calls", 0), ("selection_sha256", "0" * 64), ("holdout_sha256", "0" * 64),
            ("base_train_prefix_preserved", False), ("validation_test_unchanged", False), ("regenerated_byte_exact", False)):
            value = artifact(); value["plan"]["data_attestation"][key] = replacement; repin(value)
            with self.assertRaises(ValueError):
                teacher.teacher_training_exposure(value)

    def test_incomplete_update_and_plan_hash_tamper_rejected(self):
        for key, replacement in (("actual_optimizer_steps", 256), ("resume", True), ("model_trained", False)):
            value = artifact(); value[key] = replacement
            with self.assertRaises(ValueError):
                teacher.teacher_training_exposure(value)
        value = artifact(); value["plan"]["objective"]["fixture"] = "changed"
        with self.assertRaises(ValueError):
            teacher.teacher_training_exposure(value)

    def test_fresh_validation_and_objective_cannot_change(self):
        for key in ("validation_row_ids_sha256", "objective_sha256"):
            baseline = fresh(); baseline[key] = "0" * 64
            with self.assertRaises(ValueError):
                teacher.teacher_training_exposure(artifact(), baseline)

    def test_study_exact_two_arms_five_cases_and_separate_profiles(self):
        row = study(); self.assertIs(common.study_spec(row, controller.SLICE_SHA), row)
        row["wall_profile"] = "fixed-wall-30-v1"
        row["comparison"] = "fixed_wall_slice"
        row["native_work"] = common.search_settings(row["wall_profile"])
        self.assertIs(common.study_spec(row, controller.SLICE_SHA), row)
        row["comparison"] = "fixed_native_work_guarded"
        with self.assertRaises(ValueError):
            common.study_spec(row, controller.SLICE_SHA)

    def test_scope_budget_and_relabel_tampering_rejected(self):
        for key, replacement in (("scope", "full16"), ("wall_profile", None), ("training_allowed", True)):
            row = study(); row[key] = replacement
            with self.assertRaises(ValueError): common.study_spec(row, controller.SLICE_SHA)
        row = study(); row["native_work"]["max_tactic_attempts"] += 1
        with self.assertRaises(ValueError): common.study_spec(row, controller.SLICE_SHA)
        row = study(); row["arms"]["distilled_1_7b"] = deepcopy(row["arms"]["fresh_1_7b"])
        with self.assertRaises(ValueError): common.study_spec(row, controller.SLICE_SHA)

    def test_no_teacher_or_expectation_field_enters_search_input(self):
        row = {"theorem": "0 = 0", "expected": "not search input", "teacher": {"reference_script": ["refl"]}}
        self.assertEqual(set(common.case_payload(row, "guarded-work-60-v1")), {"theorem", "settings"})
        self.assertNotIn("reference_script", common.canonical(common.case_payload(row, "guarded-work-60-v1")).decode())


class CollectionTests(unittest.TestCase):
    def test_actual_collection_structure_allows_distinct_json_format_hashes(self):
        obs, transport, raw, a = collection()
        self.assertNotEqual(obs["files"]["artifact/manifest.json"]["sha256"], obs["files"]["job/result/trained-artifact.json"]["sha256"])
        result = teacher.validate_student_collection(obs, transport, raw, a)
        self.assertEqual(result["actual_student_exit_code"], 0)
        self.assertFalse(result["saved_tensor_reload_performed"])

    def test_transport_success_cannot_stand_in_for_training_success(self):
        obs, transport, raw, a = collection()
        obs["scheduler"]["sacct"]["stdout_stderr"] = obs["scheduler"]["sacct"]["stdout_stderr"].replace("COMPLETED|0:0", "FAILED|1:0")
        with self.assertRaises(ValueError): teacher.validate_student_collection(obs, transport, raw, a)

    def test_unknown_timeout_conflicting_exit_or_unreaped_transport_rejected(self):
        for key, value in (("actual_ssh_exit_code", None), ("actual_exit_code", 1), ("owned_child_reaped", False),
                           ("stop_reason", "ssh_wall_limit"), ("output_complete", False)):
            obs, transport, raw, a = collection(); transport[key] = value
            with self.assertRaises(ValueError): teacher.validate_student_collection(obs, transport, raw, a)

    def test_missing_partial_wrong_hash_or_nonzero_process_rejected(self):
        for transform in (
            lambda o, r: r.pop("job/reservation.json.claimed"),
            lambda o, r: o["files"]["artifact/manifest.json"].update(complete_file=False),
            lambda o, r: o["files"]["artifact/manifest.json"].update(sha256="0" * 64),
            lambda o, r: r.update({"job/actual-process-exit.txt": b"1\n"}),
            lambda o, r: o["files"].update({"artifact/incomplete.json": {}}),
        ):
            obs, transport, raw, a = collection(); transform(obs, raw)
            with self.assertRaises(ValueError): teacher.validate_student_collection(obs, transport, raw, a)

    def test_artifact_or_optimizer_substitution_rejected(self):
        obs, transport, raw, a = collection(); a["actual_optimizer_steps"] = 256
        with self.assertRaises(ValueError): teacher.validate_student_collection(obs, transport, raw, a)


class FileAndSourceTests(unittest.TestCase):
    def test_asserted_admission_cannot_omit_dataset_dependencies(self):
        a = artifact()
        code = {"path": "code.py", "bytes": 2, "sha256": "a" * 64}
        a["plan"]["source_pins"] = {"code.py": code["sha256"]}
        a["plan"]["data_attestation"]["source_pins"] = {"code.py": code["sha256"]}
        source = {"path": "fixture/source.json", "bytes": 3, "sha256": "b" * 64}
        train = {"path": "fixture/primitive-train.jsonl", "bytes": 4, "sha256": "c" * 64}
        data_ref = {"path": "fixture/manifest.json", "bytes": 5, "sha256": "d" * 64}
        dataset = {"schema": teacher.DATA_SCHEMA, "status": "complete", "training_allowed": True,
            "source_pins": a["plan"]["data_attestation"]["source_pins"],
            "input_spec": a["plan"]["data_attestation"]["teacher_input_spec"],
            "fresh_replay_manifest": a["plan"]["data_attestation"]["fresh_replay_manifest"],
            "inputs": [source], "files": {"primitive-train.jsonl": {k: train[k] for k in ("bytes", "sha256")}}}
        admission = {"teacher_dataset": data_ref, "inputs": [code, source, train, data_ref]}
        teacher.validate_bound_dependencies(admission, dataset, a)
        admission["inputs"].remove(source)
        with self.assertRaises(ValueError): teacher.validate_bound_dependencies(admission, dataset, a)

    def test_evidence_rejects_escape_links_and_changed_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / "evidence.json"; path.write_bytes(b"{}")
            ref = {"path": "evidence.json", "bytes": 2, "sha256": sha256(b"{}").hexdigest()}
            evidence = teacher.Evidence(root); self.assertEqual(evidence.json(ref), {})
            path.write_bytes(b"[]")
            with self.assertRaises(ValueError): evidence.read(ref)
            path.unlink(); (root / "target.json").write_bytes(b"{}"); path.symlink_to(root / "target.json")
            with self.assertRaises(ValueError): evidence.read(ref)
            with self.assertRaises(ValueError): teacher.descriptor({**ref, "path": "../outside.json"})

    def test_reference_size_type_and_stop_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); (root / "x").write_bytes(b"x")
            ref = {"path": "x", "bytes": 1, "sha256": sha256(b"x").hexdigest()}
            with self.assertRaises((ValueError, TimeoutError)): teacher.Evidence(root, lambda: True).read(ref)
            with self.assertRaises(ValueError): teacher.descriptor({**ref, "bytes": True})

    def test_controller_cleanup_functions_unchanged_from_frozen_v2(self):
        parent = HERE.parent / "paired-evaluation-v2"
        old = ast.parse((parent / "paired_controller.py").read_text())
        new = ast.parse((HERE / "paired_controller.py").read_text())
        functions = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        self.assertEqual(functions(old), functions(new))

    def test_search_replay_provider_policy_and_native_caps_unchanged(self):
        parent = HERE.parent / "paired-evaluation-v2"
        old = ast.parse((parent / "paired_case_worker.py").read_text())
        new = ast.parse((HERE / "paired_case_worker.py").read_text())
        def calls(tree, name):
            return [ast.dump(n, include_attributes=False) for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == name]
        for name in ("search", "run_proof"):
            self.assertEqual(calls(old, name), calls(new, name))
        classes = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.ClassDef)}
        self.assertEqual(classes(old)["RecordingPolicy"], classes(new)["RecordingPolicy"])
        a, b = ast.parse((parent / "paired_common.py").read_text()), ast.parse((HERE / "paired_common.py").read_text())
        funcs = lambda t: {n.name: ast.dump(n, include_attributes=False) for n in t.body if isinstance(n, ast.FunctionDef)}
        for name in ("search_settings", "case_payload", "source_pins", "native_identity", "validate_counts", "proof_acceptance", "job_seconds"):
            self.assertEqual(funcs(a)[name], funcs(b)[name])
        assignments = lambda t: {n.targets[0].id: ast.dump(n.value, include_attributes=False) for n in t.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
        for name in ("FEATURES", "NATIVE_WORK", "WALL_PROFILES", "MODEL_LIMITS", "RESOURCE_LIMITS", "PROVIDER_SHA", "SCHEDULER_SHA"):
            self.assertEqual(assignments(a)[name], assignments(b)[name])

    def test_metadata_imports_do_not_load_native_framework_or_trainer(self):
        forbidden = ("peano_lab", "torch", "transformers", "hydra_training_v5", "teacher_data", "teacher_student_pilot")
        self.assertFalse(any(name == prefix or name.startswith(prefix + ".") for name in sys.modules for prefix in forbidden))


class ReuseTests(unittest.TestCase):
    def pair(self):
        new = study()
        old = deepcopy(new)
        old.pop("teacher_admission")
        old.update(schema="hydra-p6-p10-paired-study-v1", scope="full16", distilled_training_exposure=None)
        old["arms"] = {"symbolic": None, "fresh_1_7b": deepcopy(new["arms"]["fresh_1_7b"])}
        for name, model, manifest, kind in (("fresh_4b", "qwen3-4b-base", "a" * 64, "fresh_decision_pilot"),
            ("historical_1_7b", "qwen3-1.7b-base", common.HISTORICAL_SHA, "historical_retention")):
            old["arms"][name] = {"model_key": model, "base_directory": "/fixture/base", "adapter_directory": "/fixture/" + name,
                "adapter_manifest_sha256": manifest, "adapter_kind": kind}
        runtime = {"hydra-playground/hybrid_search.py": {"bytes": 1, "sha256": "1" * 64}}
        before = {**runtime, summary.OLD_SCOPE + "paired_common.py": {"bytes": 2, "sha256": "2" * 64}}
        after = {**deepcopy(runtime), summary.NEW_SCOPE + "paired_common.py": {"bytes": 3, "sha256": "3" * 64}}
        old["source_pins_sha256"], new["source_pins_sha256"] = teacher.digest(before), teacher.digest(after)
        return old, new, before, after

    def test_reuse_only_allows_admission_scope_delta(self):
        old, new, before, after = self.pair()
        with mock.patch.object(summary, "BASELINE_MAP_SHA", teacher.digest(before)):
            self.assertTrue(summary.reuse_compatible(old, new, before, after))
            after["hydra-playground/hybrid_search.py"]["sha256"] = "4" * 64
            new["source_pins_sha256"] = teacher.digest(after)
            with self.assertRaises(ValueError): summary.reuse_compatible(old, new, before, after)

    def test_guarded_rows_cannot_be_relabelled_fixed_wall_or_other_exposure(self):
        for key, value in (("wall_profile", "fixed-wall-30-v1"), ("comparison", "fixed_wall_slice")):
            old, new, before, after = self.pair(); new[key] = value
            with mock.patch.object(summary, "BASELINE_MAP_SHA", teacher.digest(before)):
                with self.assertRaises(ValueError): summary.reuse_compatible(old, new, before, after)
        old, new, before, after = self.pair(); new["arms"]["fresh_1_7b"]["adapter_manifest_sha256"] = "0" * 64
        with mock.patch.object(summary, "BASELINE_MAP_SHA", teacher.digest(before)):
            with self.assertRaises(ValueError): summary.reuse_compatible(old, new, before, after)


if __name__ == "__main__":
    unittest.main()
