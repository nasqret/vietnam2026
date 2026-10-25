"""Pure boundary tests. Every proof/model record here is synthetic test data.

These fixtures never invoke a native parser, tactic, checker, model, tokenizer,
solver or scheduler. They cannot create a positive teacher dataset or adapter.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import importlib.abc
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class ForbidExecutionImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"peano_lab", "torch", "transformers", "peft", "mlx"}:
            raise AssertionError("Pure gate attempted a forbidden runtime import: " + fullname)
        return None


sys.meta_path.insert(0, ForbidExecutionImports())
sys.path.insert(0, str(Path(__file__).resolve().parent))
import teacher_data as data
import remote_student_update as student


def trace_fixture():
    """A small JSON shape fixture, not an asserted native proof."""
    theorem = "forall a b. a=b -> a=b"
    commands = ["intro", "intro", "intro", "assumption"]
    goals = [["⊢ " + theorem], ["a\n⊢ forall b. a=b -> a=b"],
             ["a b\n⊢ a=b -> a=b"], ["a b\nh : a=b\n⊢ a=b"], []]
    origins = [{"source": "recorded_prefix", "command": command} for command in commands[:2]]
    origins += [{"source": "teacher_model", "command": "intro", "plan_sha256": "1" * 64},
                {"source": "heuristic", "command": "assumption"}]
    state = {"id": "fixture-state", "theorem": theorem, "commands_before": commands[:2],
             "all_goals_before": goals[2], "prefix_provenance": origins[:2], "split": "train",
             "theorem_identity": "fixture-identity", "family": "fixture-family", "template_family": "fixture-template"}
    trace = [{"step": i + 1, "tactic": command, "focus": 0, "status": "ok", "error": None,
              "goals_before": goals[i], "goals_after": goals[i+1], "origin": origins[i]}
             for i, command in enumerate(commands)]
    trace.append({"qed": True, "theorem": theorem, "tactic_count": 4, "proof_size": 9})
    result = {"schema": "hydra-teacher-native-result-v1", "status": "proved", "kernel_checked": True,
        "independent_replay_checked": True, "positive_distillation_eligible": True,
        "original_theorem": theorem, "state_id": state["id"], "kernel_identity": data.KERNEL_SHA,
        "final_goals": [], "prefix_commands": commands[:2], "commands": commands, "trace": trace,
        "provenance": origins, "counts": {"teacher_steps_accepted": 1},
        "replay": {"status": "proved", "kernel_checked": True, "goals": [], "proof_nodes": 9}}
    return state, result


def proposal_fixture():
    state, _ = trace_fixture()
    identity = {"model_manifest_sha256": "2" * 64, "tokenizer_sha256": "3" * 64,
                "chat_template_sha256": "4" * 64}
    prompt = "synthetic prompt; never model input"
    record = {"schema": "hydra-teacher-proposal-batch-v1", "state_id": state["id"], "status": "proposals",
        "actual_model_calls": 1, "generated_tokens": 2,
        "provider": {"available": True, "test_backend": False, "provider": {
            "kind": "local_model", "name": data.MODEL_KEY,
            "model_manifest_sha256": identity["model_manifest_sha256"], "tokenizer_sha256": identity["tokenizer_sha256"]}},
        "input": {"input_token_ids": [7, 8], "input_tokens": 2, "prompt_contract": data.PROMPT_CONTRACT,
            "chat_template_sha256": identity["chat_template_sha256"], "p4_prompt": prompt},
        "output": {"output_token_ids": [9, 10], "decoded_text": "synthetic"},
        "prompt_sha256": sha256(prompt.encode()).hexdigest(),
        "plans": [{"source": "planner_model", "commands": ["intro"]}]}
    return state, identity, record


def row(index, split="train"):
    return {"id": "row-" + str(index), "prompt": "prompt-" + str(index),
            "completion": "completion-" + str(index), "split": split}


def base_rows():
    # Deliberately noncanonical spacing checks byte preservation, not rendering.
    return b"".join((json.dumps(row(i), indent=None) + "\n").encode() for i in range(data.BASE_ROWS))


def helper_stub():
    return SimpleNamespace(ACCOUNT="test-account", PARTITION="test-partition",
        MODELS={"qwen3-1.7b-base": ("Qwen/Qwen3-1.7B-Base", "ea980cb0a6c2ae4b936e82123acc929f1cec04c1")},
        valid_sha=lambda value: type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value))


def reservation_fixture():
    return {"schema": student.CONTROLLER_SCHEMA, "job_id": "123456", "job_name": "test-only-not-submitted",
        "nonce": "a" * 32, "uid": os.getuid(), "account": "test-account", "partition": "test-partition",
        "model_key": "qwen3-1.7b-base", "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "seconds": 600, "soft_limit_seconds": 540,
        **{key: "b" * 64 for key in ("config_sha256", "dataset_sha256", "plan_sha256",
                                    "controller_sha256", "source_pins_sha256")}}


def plan_fixture():
    reservation = reservation_fixture()
    exposure = {"schema": "hydra-teacher-augmented-data-attestation-v1", "manifest_sha256": reservation["dataset_sha256"],
        "base_manifest_sha256": data.BASE_SHA, "base_training_rows": data.BASE_ROWS, "teacher_rows_added": 2,
        "fresh_verified_continuations": 1, "actual_teacher_model_calls": 1,
        "teacher_model_manifest_sha256": "c" * 64, "holdout_sha256": data.HOLDOUT_SHA,
        "selection_sha256": data.SELECTION_SHA,
        "reserved_intermediate_check": "exact_closed_AST_plus_declared_template_exclusions",
        "teacher_source_scope": "complete_teacher_proposed_native_continuation",
        "regenerated_byte_exact": True, "base_train_prefix_preserved": True, "validation_test_unchanged": True}
    rows = data.BASE_ROWS + 2
    plan = {"schema": "hydra-teacher-augmented-pilot-plan-v1", "profile": student.PROFILE,
        "model": dict(zip(("model_id", "revision"), helper_stub().MODELS[reservation["model_key"]])),
        "config_sha256": reservation["config_sha256"], "data_attestation": exposure,
        "training_rows": rows, "expected_optimizer_steps": (rows + 7) // 8,
        "epochs": 1, "resume": False, "automatic_retry": False, "model_trained": False,
        "prompt_schema": "primitive_v4", "planner_rows_allowed": False}
    repin(plan, reservation)
    return plan, reservation


def repin(plan, reservation):
    plan["plan_sha256"] = data.digest({k: v for k, v in plan.items() if k != "plan_sha256"})
    reservation["plan_sha256"] = plan["plan_sha256"]


class TraceBoundaryTests(unittest.TestCase):
    def test_complete_receipt_shape_and_original_prefix(self):
        state, result = trace_fixture()
        self.assertEqual(data.validate_native_trace(result, state), result["trace"][:-1])
        self.assertEqual(result["provenance"][0]["source"], "recorded_prefix")

    def test_manual_partial_or_changed_chain_cannot_be_teacher_data(self):
        for alteration in ("manual", "partial", "chain", "scope", "prefix", "counter", "original"):
            with self.subTest(alteration=alteration):
                state, value = trace_fixture()
                if alteration == "manual": value["provenance"][2]["source"] = "manual_fixture"
                if alteration == "partial": value["trace"].pop()
                if alteration == "chain": value["trace"][2]["goals_before"] = ["⊢ 0=1"]
                if alteration == "scope": value["positive_distillation_eligible"] = False
                if alteration == "prefix": value["prefix_commands"][0] = "ring"
                if alteration == "counter": value["counts"]["teacher_steps_accepted"] = True
                if alteration == "original": value["original_theorem"] = "0=1"
                with self.assertRaises(data.TeacherDataError): data.validate_native_trace(value, state)

    def test_actual_call_and_token_receipts_are_mandatory(self):
        state, identity, value = proposal_fixture()
        self.assertEqual(data.validate_proposal(value, state, identity, 0)["commands"], ["intro"])
        for alteration in ("zero", "bool", "test", "tokens", "population", "manifest", "source"):
            with self.subTest(alteration=alteration):
                state, identity, value = proposal_fixture()
                if alteration == "zero": value["actual_model_calls"] = 0
                if alteration == "bool": value["actual_model_calls"] = True
                if alteration == "test": value["provider"]["test_backend"] = True
                if alteration == "tokens": value["output"].pop("output_token_ids")
                if alteration == "population": value["output"]["output_token_ids"][0] = 102400
                if alteration == "manifest": value["provider"]["provider"]["model_manifest_sha256"] = "f" * 64
                if alteration == "source": value["plans"][0]["source"] = "test_backend"
                with self.assertRaises(data.TeacherDataError): data.validate_proposal(value, state, identity, 0)

    def test_fresh_original_goal_replay_must_match_every_transition(self):
        state, native = trace_fixture()
        candidate = {"state": state, "native": native, "source": {"sha256": "d" * 64}}
        record = {"schema": "hydra-teacher-fresh-replay-result-v1", "status": "verified", "kernel_checked": True,
            "state_id": state["id"], "kernel_identity": data.KERNEL_SHA, "native_source_sha256": "d" * 64,
            "commands_sha256": data.digest(native["commands"]), "model_calls": 0, "solver_calls": 0,
            "replay": {"status": "proved", "kernel_checked": True, "theorem": state["theorem"], "goals": [],
                       "commands": native["commands"], "trace": deepcopy(native["trace"]), "proof_nodes": 9}}
        data.validate_fresh_replay(record, candidate)
        for alteration in ("source", "transition", "final", "kernel", "commands"):
            broken = deepcopy(record)
            if alteration == "source": broken["native_source_sha256"] = "0" * 64
            if alteration == "transition": broken["replay"]["trace"][1]["goals_after"] = []
            if alteration == "final": broken["replay"]["trace"][-1]["qed"] = False
            if alteration == "kernel": broken["kernel_identity"] = "0" * 64
            if alteration == "commands": broken["commands_sha256"] = "0" * 64
            with self.subTest(alteration=alteration), self.assertRaises(data.TeacherDataError):
                data.validate_fresh_replay(broken, candidate)

    def test_owned_child_positive_requires_exit_and_reap(self):
        receipt = {"actual_exit_code": 0, "quiescent": True, "launched": True, "stopped_for": None,
                   "child_result_sha256": "e" * 64, "automatic_retry": False}
        data.validate_owned_execution(receipt, result_sha="e" * 64)
        for key, value in (("actual_exit_code", 1), ("actual_exit_code", False), ("quiescent", False),
                           ("launched", False), ("stopped_for", "rss_limit"), ("child_result_sha256", "a" * 64)):
            with self.subTest(key=key), self.assertRaises(data.TeacherDataError):
                data.validate_owned_execution({**receipt, key: value}, result_sha="e" * 64)


class DataBoundaryTests(unittest.TestCase):
    def test_all_base_line_bytes_preserved_and_duplicates_not_relabelled(self):
        base = base_rows()
        new = row(data.BASE_ROWS)
        raw, added, counts = data.merge_rows(base, [row(0), new, deepcopy(new)])
        self.assertTrue(raw.startswith(base))
        self.assertEqual(raw[:len(base)], base)
        self.assertEqual(added, [new])
        self.assertEqual(counts["base_rows_preserved"], 2047)
        self.assertEqual(counts["duplicate_teacher_rows_omitted"], 2)
        self.assertEqual(counts["rows_dropped_for_budget"], 0)

    def test_overflow_and_eval_rows_fail_instead_of_sampling(self):
        for additions in ([row(i) for i in range(data.BASE_ROWS, data.MAX_ROWS + 1)],
                          [row(data.BASE_ROWS, "val")], [row(data.BASE_ROWS, "test")]):
            with self.assertRaises(data.TeacherDataError): data.merge_rows(base_rows(), additions)

    def test_training_family_and_statement_are_all_required(self):
        state, _ = trace_fixture()
        group = {"split": "train", "members": ["statement:fixture-identity", "family:fixture-family", "template:fixture-template"]}
        data.require_training_component(state, group, "fixture-identity")
        for alteration in ("split", "family", "template", "statement"):
            value = deepcopy(group)
            identity = "fixture-identity"
            if alteration == "split": value["split"] = "val"
            if alteration == "family": value["members"].remove("family:fixture-family")
            if alteration == "template": value["members"].remove("template:fixture-template")
            if alteration == "statement": identity = "another-statement"
            with self.subTest(alteration=alteration), self.assertRaises(data.TeacherDataError):
                data.require_training_component(state, value, identity)

    def test_zero_candidates_writes_only_an_explicit_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "blocked-dataset"
            inputs = SimpleNamespace(pins={"test-spec.json": {"path": "test-spec.json", "sha256": "a" * 64}})
            loaded = (inputs, {"base_dataset": {"sha256": data.BASE_SHA}}, None, None, {}, None, [],
                      {"positive_teacher_continuations": 0, "actual_teacher_model_calls": 32})
            with patch.object(data, "source_pins", return_value={}), patch.object(data, "load_inputs", return_value=loaded), \
                 patch.object(data, "load_replays", side_effect=AssertionError("No replay for zero positives")):
                value = data.export_dataset("test-spec.json", expected_sha256="a" * 64, output=destination)
            self.assertEqual(value["status"], "blocked_zero_teacher_continuations")
            self.assertFalse(value["training_allowed"])
            self.assertEqual(value["teacher_rows_added"], 0)
            self.assertEqual([p.name for p in destination.iterdir()], ["blocked.json"])

    def test_zero_dataset_cannot_enter_student_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            raw = data.canonical({"schema": data.DATA_SCHEMA, "status": "complete", "training_allowed": True,
                                  "teacher_rows_added": 0, "training_rows": 2047, "base_rows_preserved": 2047})
            path.write_bytes(raw)
            with patch.object(data, "frozen_data", side_effect=AssertionError("No runtime admission for zero rows")), \
                 self.assertRaises(data.TeacherDataError):
                data.attest_teacher_dataset(path, expected_sha256=sha256(raw).hexdigest(), workspace=temporary)

    def test_evidence_inputs_reject_escape_mutation_size_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path = directory / "record.json"
            path.write_bytes(b'{"value":1}\n')
            inputs = data.Inputs(directory)
            self.assertEqual(inputs.json("record.json"), {"value": 1})
            for name in ("../record.json", "/record.json", "x/../record.json"):
                with self.subTest(name=name), self.assertRaises(data.TeacherDataError): inputs.read(name)
            with self.assertRaises(data.TeacherDataError): inputs.read("record.json", "f" * 64)
            with self.assertRaises(data.TeacherDataError): inputs.read("record.json", maximum=1)
            (directory / "alias.json").symlink_to(path)
            with self.assertRaises(data.TeacherDataError): inputs.read("alias.json")
            with self.assertRaises(data.TeacherDataError): data.strict_json('{"x":1,"x":2}')
            with self.assertRaises(data.TeacherDataError): data.strict_json('{"x":NaN}')
            with self.assertRaises(data.TeacherDataError): data.Inputs(directory, lambda: True).read("record.json")


class StudentBoundaryTests(unittest.TestCase):
    def test_distinct_allocation_schema_and_resources(self):
        with patch.object(student, "p6_helpers", return_value=helper_stub()):
            self.assertEqual(student.reservation_spec(reservation_fixture())["gpus"], 1)
            for key, value in (("schema", "hydra-decision-pilot-reservation-v1"), ("gpus", 2),
                               ("cpus", 9), ("seconds", 7201), ("soft_limit_seconds", 600), ("nodes", True)):
                with self.subTest(key=key), self.assertRaises(data.TeacherDataError):
                    student.reservation_spec({**reservation_fixture(), key: value})

    def test_new_plan_admission_does_not_accept_plain_v2_or_zero_teacher_data(self):
        with patch.object(student, "p6_helpers", return_value=helper_stub()):
            plan, reservation = plan_fixture()
            student.validate_plan(plan, reservation)
            for alteration in ("v2", "zero", "manual", "heldout", "replay", "base", "rows", "calls"):
                candidate, identity = deepcopy(plan), deepcopy(reservation)
                if alteration == "v2": candidate["schema"] = "hydra-decision-pilot-plan-v2"
                if alteration == "zero": candidate["data_attestation"]["teacher_rows_added"] = 0
                if alteration == "manual": candidate["data_attestation"]["teacher_source_scope"] = "manual_fixture"
                if alteration == "heldout": candidate["data_attestation"]["holdout_sha256"] = "0" * 64
                if alteration == "replay": candidate["data_attestation"]["fresh_verified_continuations"] = 0
                if alteration == "base": candidate["data_attestation"]["base_train_prefix_preserved"] = False
                if alteration == "rows": candidate["training_rows"] = 4097
                if alteration == "calls": candidate["data_attestation"]["actual_teacher_model_calls"] = True
                repin(candidate, identity)
                with self.subTest(alteration=alteration), self.assertRaises(data.TeacherDataError):
                    student.validate_plan(candidate, identity)

    def test_frozen_training_bodies_remain_exact_without_importing_them(self):
        derivation = json.loads((data.HERE / "DERIVATION.json").read_bytes())
        original = (data.ROOT / derivation["source"]).read_bytes()
        derived = (data.ROOT / derivation["derived"]).read_bytes()
        self.assertEqual(sha256(original).hexdigest(), derivation["source_sha256"])
        self.assertEqual(sha256(derived).hexdigest(), derivation["derived_sha256"])
        normalized = original.decode().replace("from .peano_policy", "from hydra_training_v5.peano_policy") \
            .replace("from .decision_data", "from hydra_training_v5.decision_data")
        sources = []
        for source in (normalized, derived.decode()):
            tree = ast.parse(source)
            sources.append({node.name: ast.get_source_segment(source, node) for node in tree.body
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))})
        for record in derivation["unchanged_functions_after_explicit_import_qualification"]:
            name = record["function"]
            with self.subTest(function=name):
                self.assertEqual(sources[0][name], sources[1][name])
                self.assertEqual(sha256(sources[1][name].encode()).hexdigest(), record["normalized_source_sha256"])
        self.assertFalse(derivation["training_executed"])
        self.assertFalse(derivation["underlying_objective_collator_tensor_audit_modified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
