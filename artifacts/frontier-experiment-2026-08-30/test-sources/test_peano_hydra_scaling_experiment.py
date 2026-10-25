"""Tiny metadata-only adversaries; no model, native replay or allocation."""

from copy import deepcopy
import hashlib

import pytest

from training.peano_hydra import scaling_experiment as exp


def pilot(**changes):
    arguments = {
        "run_id": "frontier-pilot-v1", "source_manifest_sha256": "1" * 64,
        "shard_manifest_sha256": "2" * 64, "lineage_proposal_sha256": "3" * 64,
        "epoch_sha256": "4" * 64, "authority_sha256": "5" * 64,
        "baseline_adapter_manifest_sha256": "6" * 64,
        "split_rows": {"train": 13104, "dev": 2160, "quarantine": 0},
    }
    return exp.build_pilot_plan(**{**arguments, **changes})


def evaluation(**changes):
    goals = [
        {"name": "review_goal_" + str(i), "source": f"{i} = {i}",
         "statement": f"{i} = {i}",
         "statement_sha256": hashlib.sha256(f"{i} = {i}".encode()).hexdigest(),
         "lineage_sha256": "a" * 64}
        for i in range(3)
    ]
    arguments = {
        "goals": goals, "cohort": "review-candidate-dev", "epoch_sha256": "1" * 64,
        "authority_sha256": "2" * 64, "lineage_proposal_sha256": "3" * 64,
        "baseline_adapter_manifest_sha256": "4" * 64,
        "candidate_training_plan_sha256": "5" * 64, "source_files_sha256": "6" * 64,
    }
    return exp.build_evaluation_plan(**{**arguments, **changes})


def resign(value, field="plan_sha256"):
    value[field] = exp.digest({k: v for k, v in value.items() if k != field})
    return value


def outcome(role="saved-corrected", budget=8, goal="review_goal_0", status="proof"):
    positive = status == "proof"
    return {
        "role": role, "max_model_calls": budget, "goal": goal, "status": status,
        "model_generate_calls": 2 if positive else budget,
        "tactic_decisions": 2 if positive else None,
        "proof_nodes": 3 if positive else None,
        "commands_sha256": "f" * 64 if positive else None,
    }


def test_pilot_keeps_existing_caps_and_never_approves_gpu():
    p = pilot()
    assert p["expected_optimizer_steps"] == 1638
    assert p["epochs"] == 1 and p["max_optimizer_steps"] == 2048
    assert p["token_fit_checked"] is False
    assert p["training_authorized"] is p["transfer_authorized"] is p["gpu_execution_authorized"] is False
    assert p["preferences_consumed"] is p["reinforcement_learning"] is False
    assert exp.validate_pilot_plan(p) == p


def test_smoke_is_not_silently_promoted_to_training():
    p = pilot(profile="smoke", split_rows={"train": 72, "dev": 15, "quarantine": 0})
    assert p["status"] == "smoke-only-not-a-training-run"
    assert exp.validate_pilot_plan(p) == p
    with pytest.raises(ValueError):
        pilot(split_rows={"train": 72, "dev": 15, "quarantine": 0})


@pytest.mark.parametrize("counts", [
    {"train": True, "dev": 1, "quarantine": 0},
    {"train": 13000.0, "dev": 1000, "quarantine": 0},
    {"train": 15000, "dev": 1385, "quarantine": 0},
    {"train": 11999, "dev": 1, "quarantine": 0},
    {"train": 15001, "dev": 1, "quarantine": 0},
    {"train": 13000, "dev": 0, "quarantine": 0},
    {"train": 13000, "dev": 1000},
])
def test_pilot_rejects_invalid_data_schedule(counts):
    with pytest.raises(ValueError):
        pilot(split_rows=counts)


@pytest.mark.parametrize("run_id", ["", "../old", "/tmp/old", "old\n", True, "x" * 97])
def test_run_identity_cannot_escape_fresh_model_namespace(run_id):
    with pytest.raises(ValueError):
        pilot(run_id=run_id)


@pytest.mark.parametrize("field,value", [
    ("epochs", 2), ("training_authorized", True), ("resume", True),
    ("token_fit_checked", True), ("expected_optimizer_steps", 100),
    ("preferences_consumed", True), ("model_trained", True),
])
def test_rehashed_pilot_cannot_change_execution_contract(field, value):
    p = pilot()
    p[field] = value
    with pytest.raises(ValueError):
        exp.validate_pilot_plan(resign(p))


def test_factorial_evaluation_separates_training_and_search_effects():
    p = evaluation()
    assert len(p["ordered_slots"]) == 12
    assert p["max_model_calls_total"] == 144
    assert p["roles"] == ["saved-corrected", "new-frontier"]
    assert p["budgets"] == [8, 16]
    assert p["comparisons"]["cross_budget_training_claim_allowed"] is False
    assert p["candidate_adapter_binding_required_after_training"] is True
    assert p["gpu_execution_authorized"] is p["sealed_benchmark"] is False
    assert exp.validate_evaluation_plan(p) == p


@pytest.mark.parametrize("budgets", [(16,), (8, 32), (8, 8), (16, 8), (8.0, 16), [8, 16], (), (True,)])
def test_unreviewed_budgets_are_rejected(budgets):
    with pytest.raises(ValueError):
        evaluation(budgets=budgets)


@pytest.mark.parametrize("cohort", ["final", "sealed", "posthoc-frontier12", "exposed-primary32"])
def test_posthoc_and_final_claims_cannot_be_relabelled(cohort):
    with pytest.raises(ValueError):
        evaluation(cohort=cohort)


def test_duplicate_or_rehashed_changed_goals_fail():
    p = evaluation()
    goals = deepcopy(p["goals"])
    goals.append(goals[0])
    with pytest.raises(ValueError):
        evaluation(goals=goals)
    p["goals"][0]["statement"] = "0 = 1"
    with pytest.raises(ValueError):
        exp.validate_evaluation_plan(resign(p))


@pytest.mark.parametrize("cohort,count", [("exposed-primary32", 32), ("posthoc-frontier12", 12)])
def test_same_size_fake_cohort_cannot_impersonate_the_recorded_benchmark(cohort, count):
    goals = [{"name": "fake_" + str(i), "source": f"{i} = {i}", "statement": f"{i} = {i}",
              "statement_sha256": hashlib.sha256(f"{i} = {i}".encode()).hexdigest(),
              "lineage_sha256": "a" * 64} for i in range(count)]
    with pytest.raises(ValueError, match="exact ordered targets"):
        evaluation(cohort=cohort, goals=goals)


def test_missing_or_interrupted_rows_stay_unknown():
    p = evaluation()
    records = [outcome(), outcome("new-frontier", status="unknown"),
               outcome(goal="review_goal_1", status="exhausted"),
               outcome("new-frontier", goal="review_goal_1")]
    m = exp.summarize_outcomes(p, records)
    assert m["missing_records"] == 8 and m["explicit_unknown_records"] == 1
    assert m["matched_comparisons"][0]["known_paired_goals"] == 1
    assert m["matched_comparisons"][0]["reported_gains"] == ["review_goal_1"]
    assert m["matched_comparisons"][0]["reported_losses"] == []
    assert m["matched_comparisons"][1]["unknown_pairs"] == 3
    assert m["proof_replay_performed"] is False
    assert m["model_generation_attested"] is False


def test_metadata_never_claims_independent_native_verification():
    rows = [outcome(), outcome("new-frontier")]
    m = exp.summarize_outcomes(evaluation(), rows)
    assert m["status"] == "metadata-only-not-independent-proof-verification"
    assert m["matched_comparisons"][0]["common_proof_decisions"] == {
        "saved-corrected": 2, "new-frontier": 2}


@pytest.mark.parametrize("field,value", [
    ("model_generate_calls", True), ("model_generate_calls", 9),
    ("proof_nodes", 0), ("tactic_decisions", 17),
    ("commands_sha256", "F" * 64), ("status", "timeout-as-false"),
    ("role", "baseline"), ("max_model_calls", 32), ("goal", "not-planned"),
])
def test_malformed_outcome_is_rejected(field, value):
    row = outcome()
    row[field] = value
    with pytest.raises(ValueError):
        exp.summarize_outcomes(evaluation(), [row])


def test_duplicate_outcome_and_unproven_positive_payload_are_rejected():
    row = outcome()
    with pytest.raises(ValueError):
        exp.summarize_outcomes(evaluation(), [row, row])
    row["status"] = "unknown"
    with pytest.raises(ValueError):
        exp.summarize_outcomes(evaluation(), [row])


def test_frontier_exhaustion_can_happen_before_call_limit():
    row = outcome(status="exhausted")
    row["model_generate_calls"] = 3
    result = exp.summarize_outcomes(evaluation(), [row])
    assert result["explicit_unknown_records"] == 0
    row["status"] = "call-limit"
    with pytest.raises(ValueError):
        exp.summarize_outcomes(evaluation(), [row])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1, 2}, b"data"])
def test_nonjson_or_nonfinite_metadata_fails(value):
    with pytest.raises(ValueError):
        exp.canonical(value)
