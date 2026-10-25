"""TRAIN-only admission adversaries with explicitly mocked native children."""

from copy import deepcopy
import hashlib
import json

import pytest

from training.peano_hydra import self_training as harvest
from training.peano_hydra import review_runtime


def run_harvest(*args, **kwargs):
    return harvest.harvest_candidates(*args, parent_bundle="synthetic-parent-not-real-data",
        parent_readiness_sha256="c" * 64, review={}, review_sha256="d" * 64, **kwargs)


def goal(split="train", name="training_goal", source="0 = 0"):
    return {"goal_id": name, "source": source, "statement": source,
            "statement_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "family": "synthetic_family", "lineage_sha256": "a" * 64, "split": split}


def plan(**changes):
    arguments = {
        "round_id": "synthetic-round-not-a-real-training-run",
        "parent_dataset_sha256": "1" * 64, "lineage_proposal_sha256": "2" * 64,
        "epoch_sha256": "3" * 64, "authority_sha256": "4" * 64,
        "model_origin_sha256": "5" * 64, "execution_sources_sha256": harvest.digest({}),
        "goals": [goal()], "excluded_statement_sha256s": ["6" * 64],
        "excluded_lineage_sha256s": ["7" * 64], "max_candidates": 4,
    }
    return harvest.build_round_plan(**{**arguments, **changes})


def candidate(p, commands=None):
    commands = ["refl"] if commands is None else commands
    return {"schema": harvest.CANDIDATE_SCHEMA, "round_sha256": p["round_sha256"],
            "goal_id": "training_goal", "commands": commands,
            "commands_sha256": harvest.digest(commands),
            "model_origin_sha256": p["model_origin_sha256"],
            "proposal_evidence_sha256": "8" * 64, "provider_kind": "authored-test-fixture"}


def native_result(request):
    row = {
        "step": 1, "split": "train", "epoch_sha256": request["epoch_sha256"],
        "lineage_sha256": request["goal"]["lineage_sha256"],
        "theorem": request["goal"]["statement"],
        "commands_sha256": harvest.digest(request["commands"]),
        "kernel_checked": True, "environment_sha256": "9" * 64,
        "state_sha256": harvest.digest(["⊢ 0 = 0"]), "action": "refl",
        "track": "verified_training_candidate", "source": "fresh_original_goal_native_replayed_candidate",
        "goals_before": ["⊢ 0 = 0"], "goals_after": [],
    }
    return {
        "schema": harvest.WORKER_SCHEMA, "round_sha256": request["round_sha256"],
        "candidate_sha256": request["candidate_sha256"], "epoch_sha256": request["epoch_sha256"],
        "authority_sha256": request["authority_sha256"], "goal_id": request["goal"]["goal_id"],
        "commands_sha256": harvest.digest(request["commands"]),
        "native_replay_performed": True, "model_generation_performed": False,
        "training_authorized": False, "research_claim_eligible": False,
        "status": "verified-training-candidate", "error": None, "positive_transitions": [row],
        "proof_nodes": 1, "trace_sha256": "b" * 64,
    }


@pytest.fixture
def workers(monkeypatch):
    calls, results = [], []
    from training.peano_hydra import scaling_workflow
    monkeypatch.setattr(scaling_workflow, "authenticate_harvest_parent", lambda *a, **kw: {
        "parent_readiness_raw_sha256": "c" * 64, "lineage_review_sha256": "d" * 64})
    monkeypatch.setattr(harvest, "execution_source_inventory", lambda: {})
    def bounded(command, **options):
        calls.append((command, options))
        request = json.loads(options["input_bytes"])
        result = native_result(request)
        if results:
            change = results.pop(0)
            if callable(change):
                change(result)
            else:
                return change
        return {"returncode": 0, "reason": "exited", "stdout": json.dumps(result),
                "stderr": "", "raw_output_base64": None}
    monkeypatch.setattr(review_runtime, "run_bounded", bounded)
    monkeypatch.setattr(review_runtime, "validate_process_record", lambda *a, **kw: None)
    return calls, results


def test_round_is_not_model_generation_or_training_authority():
    p = plan()
    assert harvest.validate_round_plan(p) == p
    assert p["candidate_generation_authorized"] is p["training_authorized"] is False
    assert p["invalid_candidates_are_non_theorem_labels"] is False
    assert p["automatic_retry"] is p["resume"] is False


@pytest.mark.parametrize("split", ["dev", "test", "quarantine", None, True])
def test_nontrain_goals_never_reach_proposal_generation(split):
    with pytest.raises(ValueError, match="DEV"):
        plan(goals=[goal(split)])


@pytest.mark.parametrize("field", ["excluded_statement_sha256s", "excluded_lineage_sha256s"])
def test_exact_heldout_exclusion_is_fail_closed(field):
    g = goal()
    value = g["statement_sha256"] if field.startswith("excluded_statement") else g["lineage_sha256"]
    with pytest.raises(ValueError, match="held-out"):
        plan(**{field: [value]})


@pytest.mark.parametrize("commands", [[], ["refl"] * 25, ["refl\nadmit"], ["refl\ruse old"], [True]])
def test_malformed_candidate_fails_before_worker(workers, commands):
    p = plan()
    with pytest.raises(ValueError):
        run_harvest(p, [candidate(p, commands)])
    assert workers[0] == []


@pytest.mark.parametrize("field,value", [
    ("goal_id", "unregistered_test"), ("round_sha256", "0" * 64),
    ("model_origin_sha256", "0" * 64), ("commands_sha256", "0" * 64),
    ("provider_kind", "trusted-certificate"), ("proposal_evidence_sha256", "x"),
])
def test_candidate_identity_cannot_change_registered_authority(workers, field, value):
    p = plan()
    c = candidate(p)
    c[field] = value
    with pytest.raises(ValueError):
        run_harvest(p, [c])
    assert workers[0] == []


def test_all_candidates_preflight_before_any_native_work(workers):
    p = plan()
    bad = candidate(p)
    bad["goal_id"] = "test_goal"
    with pytest.raises(ValueError):
        run_harvest(p, [candidate(p), bad])
    assert not workers[0]


def test_acceptance_requires_fresh_worker_and_deduplicates_proofs(workers):
    p = plan()
    c = candidate(p)
    result = run_harvest(p, [c, c])
    assert len(workers[0]) == 1
    assert workers[0][0][0][-1] == "--harvest-worker"
    assert workers[0][0][1]["limits"].to_dict() == harvest.WORKER_LIMITS
    assert result["accepted_transition_count"] == 1
    assert result["outcomes"][1]["status"] == "duplicate-proof"
    assert result["training_authorized"] is result["model_generation_attested"] is False
    assert result["accepted_transitions"][0]["provider_kind"] == "authored-test-fixture"


def test_existing_state_action_identity_is_not_reexported(workers):
    p = plan()
    first = run_harvest(p, [candidate(p)])
    existing = first["accepted_transitions"][0]["example_sha256"]
    second = run_harvest(p, [candidate(p)], existing_example_sha256s=[existing])
    assert second["accepted_transition_count"] == 0
    assert len(workers[0]) == 2  # New source admission still requires fresh replay.


def test_resource_failure_is_unknown_and_never_retried(workers):
    workers[1].append({"returncode": -15, "reason": "rss_limit", "stdout": "", "stderr": ""})
    p = plan()
    result = run_harvest(p, [candidate(p)])
    assert len(workers[0]) == 1 and result["unknown_candidates"] == 1
    assert result["accepted_transition_count"] == 0
    assert result["outcomes"][0]["status"] == "unknown-worker-failure"


@pytest.mark.parametrize("field,value", [
    ("candidate_sha256", "0" * 64), ("epoch_sha256", "0" * 64),
    ("authority_sha256", "0" * 64), ("native_replay_performed", False),
    ("training_authorized", True), ("model_generation_performed", True),
    ("proof_nodes", True), ("proof_nodes", 0),
])
def test_changed_worker_identity_or_false_positive_fails(workers, field, value):
    workers[1].append(lambda r: r.update({field: value}))
    p = plan()
    with pytest.raises(ValueError):
        run_harvest(p, [candidate(p)])


@pytest.mark.parametrize("field,value", [
    ("split", "dev"), ("theorem", "0 = 1"), ("lineage_sha256", "0" * 64),
    ("action", "admit"), ("state_sha256", "0" * 64), ("goals_after", ["⊢ 0 = 1"]),
    ("kernel_checked", False), ("step", True),
])
def test_forged_disconnected_or_crosssplit_rows_fail(workers, field, value):
    workers[1].append(lambda r: r["positive_transitions"][0].update({field: value}))
    p = plan()
    with pytest.raises(ValueError):
        run_harvest(p, [candidate(p)])


def test_source_drift_stops_before_native_work(workers, monkeypatch):
    monkeypatch.setattr(harvest, "execution_source_inventory", lambda: {"changed": True})
    p = plan()
    with pytest.raises(ValueError, match="source"):
        run_harvest(p, [candidate(p)])
    assert not workers[0]


def test_bounded_output_does_not_export_a_partial_candidate(workers, monkeypatch):
    monkeypatch.setattr(harvest, "MAX_ACCEPTED_BYTES", 1)
    p = plan()
    result = run_harvest(p, [candidate(p)])
    assert result["accepted_transition_count"] == 0
    assert result["output_budget_unretained_candidates"] == 1
    assert result["outcomes"][0]["status"] == "verified-but-output-budget"


def test_ordinary_process_cannot_impersonate_guarded_native_worker():
    with pytest.raises(ValueError):
        harvest.native_replay_worker({})


def test_missing_or_relabelled_parent_partition_stops_before_worker(workers, monkeypatch):
    from training.peano_hydra import scaling_workflow
    def denied(*args, **kwargs):
        raise ValueError("not in authenticated TRAIN")
    monkeypatch.setattr(scaling_workflow, "authenticate_harvest_parent", denied)
    p = plan()
    with pytest.raises(ValueError, match="authenticated TRAIN"):
        run_harvest(p, [candidate(p)])
    assert not workers[0]


def test_production_harvest_requires_parent_and_external_review():
    p = plan()
    with pytest.raises(TypeError):
        harvest.harvest_candidates(p, [candidate(p)])
