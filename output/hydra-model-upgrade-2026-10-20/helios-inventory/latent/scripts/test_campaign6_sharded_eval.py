"""SLURM-only behavioral and corruption tests; no model dependencies required."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys

if not os.environ.get("SLURM_JOB_ID"):
    raise RuntimeError("Campaign 6 tests must run under SLURM")
import pytest
from latentproof import qwen_eval

from latentproof import campaign6_sharded_eval as target


def protocol():
    fixed = [{"label": f"fixed{depth}", "policy": {"kind": "fixed", "depth": depth}}
             for depth in (1, 2, 4)]
    return {"format": target.PROTOCOL_FORMAT, "campaign_id": "literal-c6",
        "training_protocol_sha256": "d" * 64,
        "budgets": {"max_actions": 4, "max_new_tokens": 64,
            "max_total_decision_tokens": 256, "max_context_tokens": 1024,
            "search_width": 1, "candidates_per_step": 1},
        "max_wall_seconds_per_task": 30, "chunk_size": 2, "worker_count": 3,
        "infrastructure_attempt_limit": 2, "splits": ["dev", "test"],
        "evaluation_scopes": ["test-fresh", "test-diagnostic", "dev"],
        "policies_by_arm": {"qwen_vanilla": fixed[:1], "qwen_fixed": fixed,
            "qwen_random": fixed, "qwen_adaptive": fixed + [{"label": "learned050",
                "policy": {"kind": "learned", "quantile": 0.5}}]},
        "primary_policy_by_arm": {"qwen_vanilla": "fixed1", "qwen_fixed": "fixed2",
            "qwen_random": "fixed2", "qwen_adaptive": "learned050"},
        "test_used_for_model_selection": False}


def task(key="literal"):
    return {"id": key, "session_id": key, "task_family": "literal", "stratum": "literal",
        "split": "test", "formula": "A", "environment_sha256": "a" * 64,
        "initial_state": ["⊢ A"], "library_prefix_length": 247, "focus": 0}


def plan():
    cfg = protocol()
    return {"protocol": cfg, "runs": [{"run_id": arm + "-s" + str(seed), "arm": arm, "seed": seed}
        for seed in (11, 29, 47) for arm in target.ARMS],
        "rosters": {scope: {"proof_tasks": [task(scope + str(index)) for index in range(5)]}
            for scope in cfg["evaluation_scopes"]}}


class Tokenizer:
    eos_token_id = 255
    all_special_ids = [255]
    def __len__(self):
        return 256
    def get_added_vocab(self):
        return {"EOS": 255}
    def encode(self, text, **kwargs):
        return [1, 2]
    def convert_ids_to_tokens(self, ids):
        inverse = {value: key for key, value in qwen_eval.byte_decoder().items()}
        return [inverse[value] for value in ids]
    def decode(self, ids, **kwargs):
        return bytes(ids).decode()


class Runtime:
    def initial_state(self, item):
        return item["initial_state"]
    def run_prefix(self, item, actions, previous_transitions):
        accepted = actions in (["intro h"], ["intro h", "exact h"], ["refl"])
        solved = actions in (["refl"], ["intro h", "exact h"])
        goals = [] if solved else ["h : A ⊢ A"] if accepted else item["initial_state"]
        return {"status": "proved" if solved else "open" if accepted else "tactic_error",
            "valid_transition": accepted, "python_kernel_complete": solved,
            "native_error": None if accepted else "bad action", "native_error_type": None if accepted else "TacticError",
            "native_result": {"kernel_checked": solved, "theorem": item["formula"], "goals": goals},
            "transitions": [{"status": "ok", "goals_after": goals} for _ in actions] if accepted else previous_transitions,
            "remaining_goals": goals, "proof_nodes": 1, "trace_sha256": "e" * 64}


def provenance():
    return {"run_id": "literal", "checkpoint_sha256": "a" * 64,
        "tokenizer_identity_sha256": "b" * 64, "source_inventory_sha256": "c" * 64,
        "policy": {"kind": "fixed", "depth": 1}, "model_vocab_size": 256}


def callback(actions):
    iterator = iter(actions)
    def propose(prompt, *, max_new_tokens, deadline_monotonic=None):
        ids = (list(next(iterator).encode()) + [255])[:max_new_tokens]
        eos = ids[-1] == 255
        return {"format": qwen_eval.GENERATION_FORMAT, "provenance": provenance(),
            "model_vocab_size": 256, "decision_ids": ids, "eos": eos,
            "stop_reason": "eos" if eos else "token_budget",
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt_tokens": 2,
            "max_new_tokens": max_new_tokens, "max_context_tokens": 1024,
            "recurrence_depths": [1] * len(ids), "block_calls": [28] * len(ids),
            "head_calls": [1] * len(ids), "gate_calls": [0] * len(ids), "readouts": [1] * len(ids)}
    return propose


def record(actions, runtime=None, deadline=None):
    cfg = protocol()
    proof = target.rollout(task(), callback(actions), runtime or Runtime(), Tokenizer(), cfg["budgets"],
        expected_provenance=provenance(), budget_ceiling=cfg["budgets"], deadline_monotonic=deadline)
    return {"proof": proof, "generation_provenance": provenance(), "max_wall_seconds_per_task": 30}


def test_registered_queue_covers_every_task_once_and_primary_first():
    frozen = plan()
    target.checked_protocol(frozen["protocol"])
    queue = list(target.chunks(frozen))
    seen = set()
    for chunk in queue:
        for item in target.chunk_tasks(frozen, chunk):
            key = (chunk["cell"]["id"], item["id"])
            assert key not in seen
            seen.add(key)
    assert len(seen) == len(target.cells(frozen)) * 5
    flags = [cell["primary"] for cell in target.cells(frozen)]
    assert flags == sorted(flags, reverse=True)
    assert target.cells(frozen)[0]["split"] == "test-fresh"


@pytest.mark.parametrize("mutation", ["test-selection", "vanilla-depth", "bool-depth", "no-baseline", "overlap"])
def test_protocol_rejects_selection_or_invalid_policy(mutation):
    cfg = protocol()
    if mutation == "test-selection": cfg["test_used_for_model_selection"] = True
    elif mutation == "vanilla-depth": cfg["policies_by_arm"]["qwen_vanilla"][0]["policy"]["depth"] = 2
    elif mutation == "bool-depth": cfg["policies_by_arm"]["qwen_random"][0]["policy"]["depth"] = True
    elif mutation == "no-baseline": del cfg["policies_by_arm"]["qwen_vanilla"]
    elif mutation == "overlap": cfg["evaluation_scopes"].append("test-complement")
    with pytest.raises(target.IntegrityError):
        target.checked_protocol(cfg)


def test_long_vanilla_protocol_subset_is_valid():
    cfg = protocol()
    cfg["policies_by_arm"] = {"qwen_vanilla": cfg["policies_by_arm"]["qwen_vanilla"]}
    cfg["primary_policy_by_arm"] = {"qwen_vanilla": "fixed1"}
    target.checked_protocol(cfg)


def test_atomic_chunk_resume_binds_plan_task_and_no_success_retries(tmp_path):
    frozen = plan()
    chunk = next(target.chunks(frozen))
    item = target.chunk_tasks(frozen, chunk)[0]
    value = target.new_chunk("a" * 64, chunk)
    saved = {"task_id": item["id"], "task_sha256": target.object_digest(item),
        "cell": chunk["cell"], "attempts": 1, "state": "infrastructure-error", "error": {}}
    value["records"].append(saved)
    path = target.chunk_path(tmp_path, chunk)
    target.atomic_json(path, value)
    assert target.check_chunk(target.read_json(path), frozen, "a" * 64, chunk) == value
    assert not target.terminal(saved, frozen["protocol"])
    saved["attempts"] = 2
    assert target.terminal(saved, frozen["protocol"])
    saved["state"] = "evaluated"
    saved["attempts"] = 1
    assert target.terminal(saved, frozen["protocol"])
    with pytest.raises(target.IntegrityError):
        target.check_chunk(value, frozen, "b" * 64, chunk)


def test_dynamic_claim_exclusive_then_resumable(tmp_path):
    chunk = next(target.chunks(plan()))
    first = target.acquire_claim(tmp_path, chunk)
    assert first is not None
    assert target.acquire_claim(tmp_path, chunk) is None
    first.close()
    second = target.acquire_claim(tmp_path, chunk)
    assert second is not None
    second.close()


@pytest.mark.parametrize("actions,solved", [(["refl"], True), (["intro h", "exact h"], True), (["bad"], False)])
def test_saved_actions_replayed_from_original_target(actions, solved):
    saved = record(actions)
    checked = target.replay_record(saved, task(), Runtime(), Tokenizer(), plan())
    assert checked["proved"] is solved
    assert checked["native_prefixes"] == len(actions)


@pytest.mark.parametrize("mutation", ["action", "prompt", "tokens", "authority-certificate", "outcome", "cost"])
def test_corrupt_generated_trajectory_rejected(mutation):
    saved = record(["refl"])
    proof = saved["proof"]
    if mutation == "action": proof["actions"][0] = "bad"
    elif mutation == "prompt": proof["steps"][0]["prompt"] = "different"
    elif mutation == "tokens": proof["generated_decision_tokens"] += 1
    elif mutation == "authority-certificate": proof["native_result"]["theorem"] = "false"
    elif mutation == "outcome": proof["autonomous_python_kernel_proof"] = False
    elif mutation == "cost": proof["steps"][0]["generation"]["block_calls"] = []
    with pytest.raises(target.IntegrityError):
        target.replay_record(saved, task(), Runtime(), Tokenizer(), plan())


@pytest.mark.parametrize("field", ["block_calls", "head_calls", "readouts", "recurrence_depths"])
def test_consistent_hash_but_wrong_same_length_cost_rejected(field):
    saved = record(["refl"])
    step = saved["proof"]["steps"][0]
    raw = step["generation"]
    raw[field] = [0] * len(raw["decision_ids"])
    # The adversary also updates the ordinary record hash. Architecture/policy
    # arithmetic must reject the otherwise structurally consistent receipt.
    step["decoded"]["prediction_record_sha256"] = target.object_digest(raw)
    with pytest.raises(target.IntegrityError):
        target.replay_record(saved, task(), Runtime(), Tokenizer(), plan())


def test_late_native_proof_is_still_budget_failure(monkeypatch):
    clock = [10.]
    monkeypatch.setattr(target.time, "monotonic", lambda: clock[0])
    class Slow(Runtime):
        def run_prefix(self, *args):
            result = super().run_prefix(*args)
            clock[0] = 13.
            return result
    saved = record(["refl"], runtime=Slow(), deadline=12.)
    assert saved["proof"]["status"] == "deadline_after_native_call"
    replay = target.replay_record(saved, task(), Runtime(), Tokenizer(), plan())
    assert not replay["proved"]


def test_individual_task_clock_does_not_skip_next_task(monkeypatch):
    clock = [10.]
    monkeypatch.setattr(target.time, "monotonic", lambda: clock[0])
    first = record(["refl"], deadline=9.)
    second = record(["refl"], deadline=clock[0] + 30.)
    assert first["proof"]["model_calls"] == 0
    assert second["proof"]["autonomous_python_kernel_proof"] is True


def test_actual_native_replay_for_literal_constructive_proof():
    # Paths are explicit test-job arguments; no user corpus details are printed.
    root = os.environ.get("C6_TEST_PEANO")
    data = os.environ.get("C6_TEST_DATA")
    if not root or not data:
        pytest.skip("Set C6_TEST_PEANO and C6_TEST_DATA for the pinned native fixture")
    admission = Path(data) / "admission.json"
    runtime = target.PeanoRuntime(Path(root), admission,
        expected_admission_sha256=target.digest(admission), split="test")
    parsed, names = runtime.batch.parse_formula_with_names("forall n. n=n")
    item = {**task(), "formula": runtime.batch.pretty_formula(parsed, list(names)),
        "initial_state": runtime.render_goals(runtime.batch.start(parsed, names)),
        "environment_sha256": next(iter(runtime.authorities))}
    cfg = protocol()
    proof = target.rollout(item, callback(["intro k", "refl"]), runtime, Tokenizer(), cfg["budgets"],
        expected_provenance=provenance(), budget_ceiling=cfg["budgets"])
    assert proof["autonomous_python_kernel_proof"]
    saved = {"proof": proof, "generation_provenance": provenance(), "max_wall_seconds_per_task": 30}
    replay = target.replay_record(saved, item, runtime, Tokenizer(), plan())
    assert replay["proved"]
    runtime.assert_unchanged()
