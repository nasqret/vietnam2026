"""Proposal generation boundaries plus small real native proofs under a guard."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
from types import SimpleNamespace

import pytest

from training.peano_hydra import self_training_proposals as proposals, self_training as harvest


def exclusions(**changes):
    value = {key: [] for key in ("targets", "families", "lineages", "names", "root_skeletons", "states")}
    return {**value, **changes}


def route(name, family, source, split="train"):
    from training.peano_hydra.protocol import validate_statement
    statement = validate_statement(source)
    return {"name": name, "family": family, "source": source, "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
        "lineage_sha256": proposals.digest([family]), "split": split}


def round_plan(goals, *, max_candidates=None):
    return harvest.build_round_plan(round_id="authored-proposal-test", parent_dataset_sha256="1" * 64,
        lineage_proposal_sha256="2" * 64, epoch_sha256="3" * 64, authority_sha256="4" * 64,
        model_origin_sha256="5" * 64, execution_sources_sha256="6" * 64, goals=goals,
        excluded_statement_sha256s=[], excluded_lineage_sha256s=[],
        max_candidates=len(goals) if max_candidates is None else max_candidates)


def test_selection_is_balanced_deterministic_and_ignores_teacher_commands():
    routes = [route("a0", "a", "0 = 0"), route("a1", "a", "1 = 1"),
              route("b0", "b", "2 = 2"), route("b1", "b", "3 = 3"),
              route("dev", "diagnostic", "4 = 4", "dev")]
    eligible = {row["name"] for row in routes if row["split"] == "train"}
    first = proposals.select_train_goals(routes, eligible, round_id="r", maximum=3)
    for row in routes:
        row["commands"] = ["untrusted route metadata does not supply model proposals"]
    second = proposals.select_train_goals(list(reversed(routes)), eligible, round_id="r", maximum=3)
    assert first == second and [row["family"] for row in first] == ["a", "b", "a"]
    assert all(row["split"] == "train" and "commands" not in row for row in first)


@pytest.mark.parametrize("split", ["dev", "test", "quarantine", True, None])
def test_relabelled_eligible_nontrain_never_becomes_goal(split):
    row = route("reserved", "diagnostic", "0 = 0", split)
    with pytest.raises(ValueError, match="DEV"):
        proposals.select_train_goals([row], {"reserved"}, round_id="r", maximum=1)


def test_input_source_must_parse_to_exact_original_statement():
    row = route("goal", "train_family", "0 = 0")
    row["source"] = "1 = 1"
    with pytest.raises(ValueError, match="original"):
        proposals.select_train_goals([row], {"goal"}, round_id="r", maximum=1)


def test_identical_complete_statement_cannot_be_duplicated_by_name():
    rows = [route("a", "a", "0 = 0"), route("b", "b", "0 = 0")]
    with pytest.raises(ValueError, match="duplicated"):
        proposals.select_train_goals(rows, {"a", "b"}, round_id="r", maximum=2)


@pytest.mark.parametrize("field", ["targets", "states", "root_skeletons", "lineages"])
def test_exclusion_hash_lists_reject_bad_or_duplicate_entries(field):
    for values in (["not-a-sha"], ["a" * 64, "a" * 64], [True], "a" * 64):
        with pytest.raises(ValueError):
            proposals.validate_exclusions(exclusions(**{field: values}))


@pytest.mark.parametrize("field", ["families", "lineages", "names"])
def test_family_name_and_lineage_are_reserved_separately(field):
    goal = proposals._goal(route("training_goal", "training_family", "forall n. n = n"))
    key = {"families": "family", "lineages": "lineage_sha256", "names": "goal_id"}[field]
    with pytest.raises(proposals.ReservedOverlap):
        proposals.check_goal(goal, exclusions(**{field: [goal[key]]}))


def test_alpha_canonical_reserved_root_and_whole_template_are_checked():
    statement = route("a", "b", "forall n. n = n")["statement"]
    features = proposals._features(statement)
    with pytest.raises(proposals.ReservedOverlap):
        proposals.check_states(["⊢ " + statement], exclusions(targets=[features["canonical_sha256"]]))
    with pytest.raises(proposals.ReservedOverlap):
        proposals.check_states(["⊢ ∀ k. k + 1 = k + 1"], exclusions(root_skeletons=[features["skeleton_sha256"]]))


def test_full_state_exclusions_keep_context_and_allow_empty_terminal_state():
    state = ["h : 0 = 0\n⊢ 0 = 0"]
    reserved = exclusions(states=[proposals.digest(state)])
    with pytest.raises(proposals.ReservedOverlap):
        proposals.check_states(state, reserved)
    proposals.check_states(["other : 0 = 0\n⊢ 0 = 0"], reserved)
    proposals.check_states([], reserved)


class CountingPolicy:
    name = "explicit-test-fixture"
    policy_environment = {}
    evaluation_identity = {"name": name, "kind": "authored-test"}

    def __init__(self):
        self.calls = 0

    def propose(self, goals_before, *, max_candidates):
        self.calls += 1
        return ("refl",)


def test_reserved_state_is_blocked_before_underlying_policy_call():
    policy = CountingPolicy()
    state = ("⊢ 0 = 0",)
    guarded = proposals._GuardedPolicy(policy, exclusions(states=[proposals.digest(list(state))]), lambda: None)
    assert guarded.propose(state, max_candidates=4) == ()
    assert guarded.blocked_states == 1 and policy.calls == 0


def test_reservation_stop_cannot_be_swallowed_as_policy_exception():
    policy = CountingPolicy()
    def stopped():
        raise ValueError("reservation changed")
    guarded = proposals._GuardedPolicy(policy, exclusions(), stopped)
    with pytest.raises(proposals.GenerationStopped):
        guarded.propose(("⊢ 0 = 0",), max_candidates=4)
    assert policy.calls == 0
    assert not issubclass(proposals.GenerationStopped, Exception)


def authorization():
    goal = proposals._goal(route("goal", "family", "0 = 0"))
    plan = {"plan_sha256": "a" * 64, "round": round_plan([goal]), "max_model_calls_total": 16}
    auth = {"schema": proposals.AUTHORIZATION_SCHEMA, "plan_sha256": plan["plan_sha256"],
        "model_origin_sha256": plan["round"]["model_origin_sha256"], "pilot_review_file_sha256": "b" * 64,
        "max_goals": 1, "max_model_calls": 16, "wall_seconds": 1800, "gpus": 1,
        "one_use": True, "automatic_retry": False, "resume": False, "training_authorized": False}
    return plan, auth


def test_authorization_validation_is_only_external_metadata():
    plan, auth = authorization()
    raw_sha = hashlib.sha256(proposals.canonical(auth) + b"\n").hexdigest()
    assert proposals.check_authorization(plan, auth, expected_raw_sha256=raw_sha, pilot_review_sha256="b" * 64) == auth
    assert auth["training_authorized"] is False


@pytest.mark.parametrize("field,value", [("gpus", True), ("max_goals", True), ("max_model_calls", 17),
    ("wall_seconds", 1801), ("one_use", False), ("resume", True), ("automatic_retry", True),
    ("training_authorized", True), ("plan_sha256", "0" * 64), ("model_origin_sha256", "0" * 64)])
def test_changed_or_expanded_authorization_cannot_load_model(field, value):
    plan, auth = authorization()
    auth[field] = value
    raw_sha = hashlib.sha256(proposals.canonical(auth) + b"\n").hexdigest()
    with pytest.raises(ValueError):
        proposals.check_authorization(plan, auth, expected_raw_sha256=raw_sha, pilot_review_sha256="b" * 64)


def test_generate_requires_trusted_reservation_before_binding_or_model_import(monkeypatch):
    monkeypatch.setattr(proposals, "_refresh", lambda *a: pytest.fail("must fail before any input/native/model work"))
    with pytest.raises(ValueError, match="reservation"):
        proposals.generate(None, output=None, pilot_inputs={}, authorization={}, authorization_sha256="0" * 64,
                           reservation_check=None)


def test_standalone_cli_cannot_mint_resource_authority(capsys):
    path = proposals.ROOT / "scripts/propose_peano_hydra_self_training.py"
    spec = importlib.util.spec_from_file_location("proposal_cli_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    code = module.main(["--generate", "--request", "/does-not-exist", "--expected-request-sha256", "0" * 64,
        "--execution-inputs", "/does-not-exist-either", "--expected-execution-inputs-sha256", "1" * 64,
        "--output", "/must-not-be-created"])
    assert code == 2 and "separately reviewed owner" in capsys.readouterr().err


@pytest.fixture
def pilot_gate(monkeypatch):
    """Explicitly synthetic verifier records; no proof or review is created."""
    from training.peano_hydra import frontier_saved_benchmark_run as pilot
    from training.peano_hydra.frontier_benchmark_run import acceptance_protocol
    inputs = {key: {"path": "/unit-test-only/" + name, "sha256": number * 64}
              for key, name, number in (("pilot_request", "request.json", "1"),
                ("pilot_run", "run.json", "2"), ("pilot_verification", "verification.json", "3"),
                ("review", "not-a-real-review.json", "4"))}
    binding = {"manifest_file_sha256": "6" * 64, "audit_file_sha256": "7" * 64,
        "manifest_sha256": "a" * 64, "audit_sha256": "b" * 64, "epoch_sha256": "c" * 64,
        "reserved_goals_sha256": "d" * 64, "all64_exclusions_sha256": "e" * 64,
        "primary_goals_sha256": "f" * 64}
    benchmark = {key: value for key, value in binding.items() if key != "primary_goals_sha256"}
    benchmark["heldout_goals_sha256"] = binding["primary_goals_sha256"]
    plan = {"plan_sha256": "9" * 64, "round": {"model_origin_sha256": "5" * 64},
        "origin": {"adapter_manifest_sha256": "8" * 64}, "benchmark_binding": binding,
        "request": {"benchmark": {"manifest": {"sha256": binding["manifest_file_sha256"]},
                                  "audit": {"sha256": binding["audit_file_sha256"]}}}}
    record = {"benchmark_manifest": {"sha256": binding["manifest_file_sha256"]},
              "benchmark_audit": {"sha256": binding["audit_file_sha256"]}}
    model = {"origin_sha256": "5" * 64}
    checked = SimpleNamespace(record=record, benchmark=SimpleNamespace(load=lambda: benchmark),
                              candidate=SimpleNamespace(load=lambda: SimpleNamespace(origin=model)))
    decision = {"schema": "unit-test-only-decision", "status": "pilot-gate-met",
        "protocol_sha256": acceptance_protocol()["protocol_sha256"], "criteria": {"test": True},
        "verification_sha256": {"test": "old-resource-hash"}, "decision_sha256": "old-decision-hash"}
    saved = {"schema": "peano-hydra-frontier-pilot-independent-verification-v1", "status": "passed",
        "request_file_sha256": inputs["pilot_request"]["sha256"], "run_file_sha256": inputs["pilot_run"]["sha256"],
        "cohorts": {name: {"evaluation_sha256": digit * 64, "proof_replay_performed": True,
                           "verification_complete": True, "wall_seconds": 1.0}
                    for name, digit in (("primary", "a"), ("regression", "b"))}, "decision": decision}
    actual = deepcopy(saved)
    actual["cohorts"]["primary"]["wall_seconds"] = 2.0
    actual["decision"]["verification_sha256"] = {"test": "new-resource-hash"}
    actual["decision"]["decision_sha256"] = "new-decision-hash"
    review = {"schema": proposals.REVIEW_SCHEMA, "decision": "accept", "human_assertion": True,
        "reviewer_reference": "UNIT TEST ONLY; no human acceptance exists", "plan_sha256": plan["plan_sha256"],
        "model_origin_sha256": "5" * 64, "protocol_sha256": acceptance_protocol()["protocol_sha256"],
        "training_authorized": False, **{key + "_file_sha256": inputs[key]["sha256"]
                                        for key in ("pilot_request", "pilot_run", "pilot_verification")}}
    documents = {inputs["review"]["sha256"]: review, inputs["pilot_verification"]["sha256"]: saved,
                 inputs["pilot_run"]["sha256"]: {"candidate_adapter_manifest_sha256": "8" * 64}}
    monkeypatch.setattr(proposals, "_read", lambda descriptor, *a, **kw: documents[descriptor["sha256"]])
    monkeypatch.setattr(pilot, "check_request", lambda *a: checked)
    calls = []
    def verify(*args):
        calls.append(args)
        return actual
    monkeypatch.setattr(pilot, "verify_run", verify)
    return SimpleNamespace(bound=SimpleNamespace(to_dict=lambda: plan), inputs=inputs, plan=plan,
        checked=checked, benchmark=benchmark, model=model, actual=actual, saved=saved, review=review, calls=calls)


def test_fresh_pilot_resources_may_change_but_exact_outcomes_remain_bound(pilot_gate):
    result = proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)
    assert len(pilot_gate.calls) == 1 and result["decision_sha256"] == "new-decision-hash"
    assert result["human_identity_attested"] is False


@pytest.mark.parametrize("field", ["benchmark_manifest", "benchmark_audit"])
def test_valid_pilot_on_other_benchmark_cannot_unlock_generation(pilot_gate, field):
    pilot_gate.checked.record[field]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="benchmark raw pins"):
        proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)
    assert pilot_gate.calls == []


@pytest.mark.parametrize("field", ["heldout_goals_sha256", "reserved_goals_sha256", "all64_exclusions_sha256", "epoch_sha256"])
def test_changed_primary_reserve_or_exclusion_binding_stops_before_replay(pilot_gate, field):
    pilot_gate.benchmark[field] = "0" * 64
    with pytest.raises(ValueError, match="primary/reserve"):
        proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)
    assert pilot_gate.calls == []


def test_pilot_candidate_origin_cannot_be_replaced(pilot_gate):
    pilot_gate.model["origin_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="model identity"):
        proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)
    assert pilot_gate.calls == []


def test_actual_preregistered_gate_must_be_met_even_with_human_assertion(pilot_gate):
    pilot_gate.actual["decision"]["status"] = pilot_gate.saved["decision"]["status"] = "pilot-gate-not-met"
    with pytest.raises(ValueError, match="preregistered pilot"):
        proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)
    assert len(pilot_gate.calls) == 1


def test_incomplete_independent_proof_verification_is_not_acceptance(pilot_gate):
    pilot_gate.actual["cohorts"]["primary"]["proof_replay_performed"] = False
    with pytest.raises(ValueError, match="preregistered pilot"):
        proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)


def test_model_loss_record_is_not_a_pilot_acceptance(pilot_gate):
    pilot_gate.actual.clear()
    pilot_gate.actual.update({"train_loss": 0.0942, "dev_loss": 1.7488, "completed_steps": 1597})
    with pytest.raises((ValueError, KeyError)):
        proposals.check_pilot_acceptance(pilot_gate.bound, **pilot_gate.inputs)


def search_envelope():
    from training.peano_policy.state_identity import search_profile_contract
    plan = {"fixed_search": dict(proposals.SEARCH), "max_model_calls_per_goal": 16}
    row = {"candidate": {"commands": ["refl"]}, "search_calls": 1,
        "evidence": {"limits": {**proposals.SEARCH, "max_model_calls": 16},
            "search_profile": search_profile_contract("context-alpha-v1"),
            "search": {"commands": ["refl"], "model_calls": 1, "depth_reached": 1}}}
    return row, plan


def test_saved_search_envelope_matches_exact_optimized_search():
    row, plan = search_envelope()
    proposals.check_search_envelope(row, plan)


@pytest.mark.parametrize("length", [17, 24])
def test_legacy_24_command_capacity_cannot_expand_16_step_generator(length):
    row, plan = search_envelope()
    row["candidate"]["commands"] = ["refl"] * length
    row["evidence"]["search"]["commands"] = ["refl"] * length
    with pytest.raises(ValueError, match="planned search depth"):
        proposals.check_search_envelope(row, plan)


@pytest.mark.parametrize("field,value", [("max_depth", 24), ("beam_width", 8),
    ("candidates_per_state", 8), ("max_states", 128), ("max_model_calls", 17), ("max_depth", True)])
def test_resealed_generation_cannot_change_search_limits(field, value):
    row, plan = search_envelope()
    row["evidence"]["limits"][field] = value
    with pytest.raises(ValueError, match="fixed search limits"):
        proposals.check_search_envelope(row, plan)


@pytest.fixture
def replay_boundary(monkeypatch):
    """Mock transport only; real core/wrapper native checks are tested below."""
    from training.peano_hydra import review_runtime, scaling_workflow
    goal = proposals._goal(route("training_goal", "training_family", "0 = 0"))
    round_record = round_plan([goal], max_candidates=2)
    candidate = {"schema": harvest.CANDIDATE_SCHEMA, "round_sha256": round_record["round_sha256"],
        "goal_id": goal["goal_id"], "commands": ["refl"], "commands_sha256": proposals.digest(["refl"]),
        "model_origin_sha256": round_record["model_origin_sha256"], "proposal_evidence_sha256": "7" * 64,
        "provider_kind": "authored-test-fixture"}
    plan = {"round": round_record, "execution_sources_sha256": proposals.digest({}),
        "exclusions": exclusions(), "exclusions_sha256": proposals.digest(exclusions()),
        "existing_train_example_sha256s": []}
    calls, responses = [], []
    monkeypatch.setattr(proposals, "execution_sources", lambda: {})
    monkeypatch.setattr(scaling_workflow, "authenticate_harvest_parent", lambda *a, **kw: {})
    monkeypatch.setattr(review_runtime, "validate_process_record", lambda *a, **kw: None)
    def worker(command, **kwargs):
        calls.append((command, kwargs))
        if responses:
            return responses.pop(0)
        request = json.loads(kwargs["input_bytes"])["native"]
        row = {"step": 1, "split": "train", "epoch_sha256": request["epoch_sha256"],
            "lineage_sha256": goal["lineage_sha256"], "theorem": goal["statement"], "theorem_name": goal["goal_id"],
            "commands_sha256": candidate["commands_sha256"], "kernel_checked": True,
            "environment_sha256": "8" * 64, "state_sha256": proposals.digest(["⊢ 0 = 0"]), "action": "refl",
            "track": "verified_training_candidate", "source": "fresh_original_goal_native_replayed_candidate",
            "goals_before": ["⊢ 0 = 0"], "goals_after": []}
        result = {"schema": harvest.WORKER_SCHEMA,
            **{key: request[key] for key in ("round_sha256", "candidate_sha256", "epoch_sha256", "authority_sha256")},
            "goal_id": goal["goal_id"], "commands_sha256": candidate["commands_sha256"],
            "model_generation_performed": False, "training_authorized": False,
            "native_replay_performed": True, "complete_extra_reservations_checked": True,
            "extra_exclusions_sha256": plan["exclusions_sha256"], "status": "verified-training-candidate",
            "positive_transitions": [row], "proof_nodes": 1}
        return {"reason": "exited", "returncode": 0, "stdout": json.dumps(result), "stderr": ""}
    monkeypatch.setattr(review_runtime, "run_bounded", worker)
    def run(items=None):
        return proposals._replay_proposals(plan, [candidate] if items is None else items,
            parent_bundle="unit-test-only", parent_readiness_sha256="a" * 64, review={}, review_sha256="b" * 64)
    return SimpleNamespace(plan=plan, candidate=candidate, calls=calls, responses=responses, run=run)


def test_duplicate_complete_proposals_do_not_start_a_second_worker(replay_boundary):
    result = replay_boundary.run([replay_boundary.candidate, replay_boundary.candidate])
    assert result["accepted_transition_count"] == 1 and len(replay_boundary.calls) == 1
    assert result["outcomes"][1]["status"] == "duplicate-proof"
    assert replay_boundary.calls[0][0][-1] == "--replay-worker"
    assert replay_boundary.calls[0][1]["limits"].to_dict() == harvest.WORKER_LIMITS


def test_existing_parent_train_key_is_replayed_but_not_exported(replay_boundary):
    first = replay_boundary.run()
    replay_boundary.plan["existing_train_example_sha256s"] = [first["accepted_transitions"][0]["example_sha256"]]
    result = replay_boundary.run()
    assert len(replay_boundary.calls) == 2 and result["accepted_transition_count"] == 0


def test_limited_native_worker_is_unknown_without_retry_or_labels(replay_boundary):
    replay_boundary.responses.append({"reason": "cpu_limit", "returncode": -24, "stdout": "", "stderr": "bounded fixture failure"})
    result = replay_boundary.run()
    assert len(replay_boundary.calls) == 1 and result["accepted_transition_count"] == 0
    assert result["outcomes"][0]["status"] == "unknown-worker-failure"
    assert result["outcomes"][0]["process"]["stderr_excerpt"] == "bounded fixture failure"


def test_all_candidate_ids_are_validated_before_any_native_worker(replay_boundary):
    bad = {**replay_boundary.candidate, "goal_id": "dev_goal"}
    with pytest.raises(ValueError, match="registered TRAIN"):
        replay_boundary.run([replay_boundary.candidate, bad])
    assert not replay_boundary.calls


def guarded_fixture(source, commands, *, reserved=None, max_calls=16):
    if not (sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null"
            and resource.getrlimit(resource.RLIMIT_CPU) == (30, 31)):
        pytest.skip("real native fixture requires the exact isolated 30CPU/45wall guard")
    return proposals.fixture_worker({"schema": proposals.FIXTURE_SCHEMA, "source": source, "commands": commands,
                                     "exclusions": exclusions() if reserved is None else reserved, "max_model_calls": max_calls})


def test_real_native_complete_original_goal_search_and_fresh_replay():
    result = guarded_fixture("forall n. n = n -> n = n", ["intro n", "intro h", "exact h"])
    row = result["search"]
    assert row["status"] == "complete-proof-proposal-pending-independent-harvest"
    assert row["candidate"]["commands"] == ["intro n", "intro h", "exact h"]
    assert row["candidate"]["provider_kind"] == "authored-test-fixture"
    from training.peano_policy.state_identity import search_profile_contract
    assert row["evidence"]["search_profile"] == search_profile_contract("context-alpha-v1")
    assert result["independent_native_replay"]["status"] == "verified-training-candidate"
    assert result["independent_native_replay"]["positive_transitions"][-1]["goals_after"] == []
    assert result["positive_training_rows"] == result["model_calls"] == 0
    assert result["production_train_membership_authenticated"] is False


def test_real_native_partial_proof_or_call_limit_never_exports_positives():
    result = guarded_fixture("forall n. n = n", ["intro n"], max_calls=1)
    assert result["search"]["candidate"] is None and result["independent_native_replay"] is None
    assert result["search"]["negative_training_labels"] == []
    assert result["positive_training_rows"] == 0


def test_real_native_reserved_intermediate_never_reaches_fixture_policy():
    first = guarded_fixture("forall n. n = n", ["intro n", "refl"])
    state = first["search"]["evidence"]["replay"]["trace"][0]["goals_after"]
    result = guarded_fixture("forall n. n = n", ["intro n", "refl"],
                             reserved=exclusions(states=[proposals.digest(state)]))
    assert result["search"]["status"] == "quarantined-reserved-state"
    assert result["search"]["candidate"] is None and result["independent_native_replay"] is None
    assert result["search"]["blocked_state_calls"] == 1


def test_real_extra_replay_checks_entire_trace_before_deduplication():
    first = guarded_fixture("forall n. n = n", ["intro n", "refl"])
    packet = {"native": harvest._worker_request(first["round"], first["search"]["candidate"]),
        "exclusions": exclusions(), "execution_sources_sha256": proposals.digest(proposals.execution_sources())}
    checked = proposals.replay_worker(packet)
    assert checked["status"] == "verified-training-candidate" and len(checked["positive_transitions"]) == 2
    state = checked["positive_transitions"][0]["goals_after"]
    packet["exclusions"] = exclusions(states=[proposals.digest(state)])
    blocked = proposals.replay_worker(packet)
    assert blocked["status"] == "quarantined-extra-reservation" and blocked["positive_transitions"] == []
    assert blocked["native_replay_performed"] is True and blocked["complete_extra_reservations_checked"] is True


def test_real_native_replay_rejects_same_length_source_substitution():
    result = guarded_fixture("0 = 0", ["refl"])
    if result is None:  # pragma: no cover
        return
    from training.peano_hydra import composition
    from training.peano_hydra.epoch import freeze_epoch
    epoch = freeze_epoch(proposals.ROOT)
    _, _, authority, _, _ = composition._authority(epoch, composition.COMPOSITION_PROFILE)
    goal = proposals._goal(route("original", "authored_native_fixture", "0 = 0"))
    plan = harvest.build_round_plan(round_id="source-substitution-test", parent_dataset_sha256="1" * 64,
        lineage_proposal_sha256="2" * 64, epoch_sha256=epoch.epoch_sha256,
        authority_sha256=proposals.digest(authority), model_origin_sha256="5" * 64,
        execution_sources_sha256=proposals.digest(proposals.experiment.execution_source_inventory()), goals=[goal],
        excluded_statement_sha256s=[], excluded_lineage_sha256s=[], max_candidates=1)
    candidate = {**result["search"]["candidate"], "round_sha256": plan["round_sha256"],
                 "goal_id": goal["goal_id"], "model_origin_sha256": plan["model_origin_sha256"]}
    request = harvest._worker_request(plan, candidate)
    request["goal"]["source"] = "1 = 1"
    with pytest.raises(ValueError, match="original-goal"):
        harvest.native_replay_worker(request)


def test_parent_bound_source_inventory_is_not_extended_by_new_stage():
    assert "training/peano_hydra/self_training_proposals.py" not in proposals.experiment.execution_source_inventory()
    assert "training/peano_hydra/self_training_proposals.py" in proposals.EXTRA_SOURCES


def test_no_framework_is_loaded_by_planning_imports():
    assert not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules)
