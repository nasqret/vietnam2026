"""Generic, bounded symbolic proposals checked through the unchanged kernel."""

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.batch import run_proof  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_hydra.runner import run_hydra  # noqa: E402
from training.peano_hydra.symbolic import (  # noqa: E402
    DEFAULT_SYMBOLIC_LIMITS,
    MAX_SYMBOLIC_EVIDENCE_BYTES,
    MAX_TACTIC_BYTES,
    SYMBOLIC_COMMANDS,
    SymbolicCandidatePolicy,
    SymbolicConfig,
    make_symbolic_policy,
    verify_symbolic_evidence,
)


def _capabilities(commands=SYMBOLIC_COMMANDS):
    return SurfaceCapabilities(
        label="hydra-symbolic-development-test", allowed_commands=commands,
        allowed_theorems=frozenset(),
    )


@pytest.mark.parametrize(
    "source",
    (
        "4 + 5 = 9",
        "forall u. (2 + 3) + u = 5 + u",
        "forall u. (u + 0) + 0 = u",
        "forall u. exists v. v = u",
        "exists w. 8 = w + 3",
        "(0 = 1 /\\ 1 = 2) -> 1 = 2",
        "(0 = 1 -> 2 = 3) -> 0 = 1 -> 2 = 3",
        "(0 = 1 \\/ 1 = 2) -> (1 = 2 \\/ 0 = 1)",
        "forall u. 0 + u = u",
        "forall u. S u = 0 -> false",
        "forall u. forall v. S u = S v -> u = v",
    ),
)
def test_combined_policy_proves_generic_logic_witness_and_induction_goals(source):
    capabilities = _capabilities()
    policy = make_symbolic_policy(capabilities)
    result = run_hydra(source, policy, capabilities=capabilities, limits=DEFAULT_SYMBOLIC_LIMITS)
    assert result.proved, (source, result.status, result.search.to_dict())
    assert not result.degraded
    fresh = run_proof(source, result.commands, capabilities=capabilities)
    assert fresh.kernel_checked
    assert fresh.theorem == result.theorem
    assert fresh.proof_nodes == result.replay.proof_nodes
    assert all(len(command.encode("utf-8")) <= MAX_TACTIC_BYTES for command in result.commands)
    work = policy.heads[0].policy.workload
    assert work["proposal_calls"] == result.search.model_calls
    assert work["candidate_lines_returned"] == sum(len(row["candidates"]) for row in result.proposal_records)
    assert work["model_calls"] == work["solver_calls"] == 0
    assert work["protocol_rejections"] == 0
    assert work["formula_nodes_scanned"] > 0
    records = policy.heads[0].policy.action_records
    assert len(records) <= work["proposal_calls"] * policy.heads[0].policy.config.candidates_per_state
    for record in records:
        unsigned = dict(record)
        digest = unsigned.pop("receipt_sha256")
        assert digest == hashlib.sha256(json.dumps(unsigned, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    returned = [command for record in records if record["status"] == "accepted" for command in record["compiled_commands"]]
    assert returned == [command for row in result.proposal_records for command in row["candidates"]]
    verify_symbolic_evidence(
        result.to_dict(include_trace=True), records, work,
        capabilities=capabilities, config=policy.heads[0].policy.config,
    )


def test_component_ablation_and_immutable_identity():
    capabilities = _capabilities()
    closure_config = SymbolicConfig(structural=False, witness=False, induction=False)
    closure = SymbolicCandidatePolicy(capabilities, closure_config)
    combined = SymbolicCandidatePolicy(capabilities)
    before = combined.evaluation_identity
    assert closure.evaluation_identity != before
    assert before["config"] == SymbolicConfig().to_dict()
    assert before["source_sha256"] == hashlib.sha256(
        (ROOT / "training/peano_hydra/symbolic.py").read_bytes()
    ).hexdigest()
    with pytest.raises(FrozenInstanceError):
        closure_config.witness = True
    detached = combined.evaluation_identity
    detached["config"]["max_witness_value"] = 100000
    assert combined.evaluation_identity == before
    assert closure.propose(("⊢ ∃ x. 8 = x + 3",), max_candidates=8) == ()
    witnesses = combined.propose(("⊢ ∃ x. 8 = x + 3",), max_candidates=8)
    assert witnesses[0] == "exists 5"
    assert combined.evaluation_identity == before
    assert combined.workload["witnesses_ranked"] <= combined.config.max_term_candidates


def test_observations_choose_generic_witnesses_without_goal_names_or_scripts():
    first = SymbolicCandidatePolicy(_capabilities())
    second = SymbolicCandidatePolicy(_capabilities())
    one = first.propose(("a : ℕ ⊢ ∃ x. x = a",), max_candidates=8)
    two = second.propose(("b : ℕ ⊢ ∃ x. x = b",), max_candidates=8)
    assert one[0] == "exists a"
    assert two[0] == "exists b"
    assert first.evaluation_identity == second.evaluation_identity
    assert first.workload == second.workload
    assert first.evaluation_identity["recorded_scripts"] is False


def test_induction_candidates_come_from_visible_state_and_have_a_finite_ceiling():
    policy = SymbolicCandidatePolicy(_capabilities(), SymbolicConfig(closure=False, structural=False, witness=False))
    assert policy.propose(("⊢ ∀ x. 0 + x = x",), max_candidates=8) == ()
    assert policy.propose(("a : ℕ ⊢ 0 + a = a",), max_candidates=8) == ("induction a",)
    assert policy.propose(("a : ℕ ⊢ 0 = 0",), max_candidates=8) == ()
    assert policy.propose(("a : ℕ, IH : 0 = 0, IH1 : 1 = 1 ⊢ 0 + a = a",), max_candidates=8) == ()


def test_meta_variables_remain_opaque_and_never_become_witnesses():
    policy = SymbolicCandidatePolicy(_capabilities())
    proposals = policy.propose(("a : ℕ, h : S a = 0 ⊢ S ?t17 = 0",), max_candidates=8)
    assert proposals[0] == "assumption"
    assert all("hydra_meta_" not in command and "?" not in command for command in proposals)
    assert not any(command.startswith(("induction", "exists", "norm_num", "simp")) for command in proposals)


@pytest.mark.parametrize(
    "goal",
    (
        "⊢ " + "(" * 97 + "0 = 0" + ")" * 97,
        "⊢ 1000000 = 1000000",
        "x : ℕ, x : ℕ ⊢ x = x",
        "⊢ 0 = 0\nabort",
        "⊢ ∃ x. " + "x + " * 2000 + "0 = 0",
    ),
)
def test_oversized_or_malformed_observations_are_explicitly_counted_unknown(goal):
    policy = SymbolicCandidatePolicy(_capabilities())
    assert policy.propose((goal,), max_candidates=8) == ()
    assert policy.workload["observation_limit_hits"] == 1
    assert policy.workload["model_calls"] == 0


def test_explicit_capability_restrictions_and_proposal_budget_are_not_widened():
    policy = SymbolicCandidatePolicy(_capabilities(frozenset({"refl"})), SymbolicConfig(max_proposals=1))
    assert policy.propose(("⊢ 0 = 0",), max_candidates=8) == ("refl",)
    assert policy.propose(("⊢ 0 = 0",), max_candidates=8) == ()
    assert policy.workload["proposal_limit_hits"] == 1
    assert policy.workload["proposal_calls"] == 1
    with pytest.raises(ValueError, match="finite commands"):
        SymbolicCandidatePolicy(SurfaceCapabilities(label="bad", allowed_commands=None, allowed_theorems=frozenset()))
    with pytest.raises(ValueError, match="empty theorem"):
        SymbolicCandidatePolicy(SurfaceCapabilities(label="bad", allowed_commands=SYMBOLIC_COMMANDS, allowed_theorems=frozenset({"zero_add"})))


def test_action_receipt_bound_never_discards_the_evidence_for_a_returned_candidate():
    policy = SymbolicCandidatePolicy(_capabilities(), SymbolicConfig(max_action_receipt_bytes=1_024))
    returned = policy.propose(("⊢ ∃ x. 8 = x + 3",), max_candidates=8)
    assert returned
    assert policy.workload["receipt_limit_hits"] == 1
    assert policy.workload["retained_action_receipt_bytes"] <= 1_024
    assert list(returned) == [line for record in policy.action_records if record["status"] == "accepted" for line in record["compiled_commands"]]
    detached = policy.action_records
    detached[0]["action"]["term"] = "999999"
    assert policy.action_records[0]["action"]["term"] != "999999"


def test_typed_rejection_is_a_bound_receipt_not_a_silent_dropped_action(monkeypatch):
    import training.peano_hydra.symbolic as symbolic

    def rejected(*args, **kwargs):
        raise ValueError("explicit test-only protocol rejection")

    monkeypatch.setattr(symbolic, "compile_action", rejected)
    policy = SymbolicCandidatePolicy(_capabilities())
    assert policy.propose(("⊢ 0 = 0",), max_candidates=8) == ()
    assert policy.workload["protocol_rejections"] > 0
    assert all(row["status"] == "rejected" and row["compiled_commands"] == [] for row in policy.action_records)
    assert all("test-only" in row["error"] for row in policy.action_records)


@pytest.mark.parametrize("field,value", (("max_witness_value", 17), ("max_term_candidates", 65), ("candidates_per_state", 9), ("max_proposals", True), ("closure", 1)))
def test_unbounded_or_untyped_configuration_is_rejected(field, value):
    with pytest.raises((TypeError, ValueError)):
        replace(SymbolicConfig(), **{field: value})


def test_no_component_can_publish_a_proof_of_false_arithmetic():
    already_imported = set(sys.modules)
    capabilities = _capabilities()
    policy = make_symbolic_policy(capabilities)
    result = run_hydra("1 = 2", policy, capabilities=capabilities, limits=DEFAULT_SYMBOLIC_LIMITS)
    assert not result.proved
    assert result.replay is None
    assert result.status in {"exhausted", "limit"}
    assert not result.degraded
    verify_symbolic_evidence(
        result.to_dict(include_trace=True), policy.heads[0].policy.action_records,
        policy.heads[0].policy.workload, capabilities=capabilities,
    )
    assert not ({"torch", "transformers", "peft"} & (set(sys.modules) - already_imported))


def _evidence_bundle(source="exists v. v = 0", config=SymbolicConfig()):
    capabilities = _capabilities()
    policy = make_symbolic_policy(capabilities, config=config)
    limits = replace(DEFAULT_SYMBOLIC_LIMITS, candidates_per_state=config.candidates_per_state,
                     max_model_calls=min(DEFAULT_SYMBOLIC_LIMITS.max_model_calls, config.max_proposals))
    result = run_hydra(source, policy, capabilities=capabilities, limits=limits)
    return capabilities, json.loads(json.dumps({
        "evidence": result.to_dict(include_trace=True),
        "action_records": list(policy.heads[0].policy.action_records),
        "workload": policy.heads[0].policy.workload,
    }))


def _verify(bundle, capabilities, config=SymbolicConfig()):
    return verify_symbolic_evidence(**bundle, capabilities=capabilities, config=config)


def test_evidence_verification_regenerates_no_search_or_tactics_and_does_not_mutate(monkeypatch):
    import training.peano_hydra.runner as runner
    import peano_lab.batch as batch

    capabilities, bundle = _evidence_bundle()
    before = json.dumps(bundle, sort_keys=True)
    def forbidden(*args, **kwargs):
        pytest.fail("attribution verification must not run search or tactics")
    monkeypatch.setattr(runner, "run_hydra", forbidden)
    monkeypatch.setattr(batch, "run_proof", forbidden)
    assert _verify(bundle, capabilities) is None
    assert json.dumps(bundle, sort_keys=True) == before


def test_evidence_verification_preserves_finite_execution_authority_and_lane():
    capabilities, bundle = _evidence_bundle()
    with pytest.raises(ValueError, match="authority"):
        _verify(bundle, _capabilities(frozenset({"exists", "refl"})))
    with pytest.raises(ValueError, match="configuration"):
        _verify(bundle, capabilities, SymbolicConfig(structural=False, witness=False, induction=False))


@pytest.mark.parametrize("mutation", (
    "action_value", "action_hash", "action_state", "missing_action", "extra_action",
    "proposal_command", "proposal_hash", "proposal_identity", "proposal_order",
    "workload_count", "workload_model_calls", "expansion_count", "negative_edges",
    "command_digest", "trace_tactic", "trace_goal", "trace_focus", "trace_footer",
))
def test_resealed_or_inconsistent_symbolic_evidence_is_rejected(mutation):
    capabilities, bundle = _evidence_bundle()
    evidence, actions, work = bundle["evidence"], bundle["action_records"], bundle["workload"]
    if mutation == "action_value":
        actions[0]["action"]["term"] = "1"
        unsigned = {key: value for key, value in actions[0].items() if key != "receipt_sha256"}
        actions[0]["receipt_sha256"] = hashlib.sha256(json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    elif mutation == "action_hash":
        actions[0]["receipt_sha256"] = "0" * 64
    elif mutation == "action_state":
        actions[0]["state_sha256"] = "0" * 64
    elif mutation == "missing_action":
        actions.pop()
    elif mutation == "extra_action":
        actions.append(actions[-1])
    elif mutation == "proposal_command":
        evidence["proposal_records"][0]["candidates"][0] = "exists 1"
    elif mutation == "proposal_hash":
        evidence["proposal_records"][0]["response_sha256"] = "0" * 64
    elif mutation == "proposal_identity":
        evidence["proposal_records"][0]["head_identity_sha256"] = "0" * 64
    elif mutation == "proposal_order":
        evidence["proposal_records"].reverse()
    elif mutation == "workload_count":
        work["witnesses_ranked"] += 1
    elif mutation == "workload_model_calls":
        work["model_calls"] = 1
    elif mutation == "expansion_count":
        evidence["search"]["states_expanded"] += 1
    elif mutation == "negative_edges":
        evidence["search"]["candidates_executed"] = -1
    elif mutation == "command_digest":
        evidence["commands_sha256"] = "0" * 64
    elif mutation == "trace_tactic":
        evidence["replay"]["trace"][0]["tactic"] = "exists 1"
    elif mutation == "trace_goal":
        evidence["replay"]["trace"][0]["goals_before"] = ["⊢ ∃ x. x = 1"]
    elif mutation == "trace_focus":
        evidence["replay"]["trace"][0]["focus"] = True
    elif mutation == "trace_footer":
        evidence["replay"]["trace"][-1]["proof_size"] += 1
    with pytest.raises(ValueError):
        _verify(bundle, capabilities)


def test_a_valid_kernel_proof_not_proposed_by_this_policy_is_rejected():
    config = SymbolicConfig(candidates_per_state=1)
    capabilities, bundle = _evidence_bundle("0 = 0", config)
    evidence = bundle["evidence"]
    assert evidence["search"]["commands"] == ["refl"]
    alternate = run_proof("0 = 0", ("norm_num",), capabilities=capabilities)
    assert alternate.kernel_checked
    evidence["search"]["commands"] = ["norm_num"]
    evidence["commands_sha256"] = hashlib.sha256(b'["norm_num"]').hexdigest()
    evidence["search"]["certificate_nodes"] = alternate.proof_nodes
    evidence["replay"] = alternate.to_dict(include_trace=True)
    with pytest.raises(ValueError, match="not an ordered accepted proposal"):
        _verify(bundle, capabilities, config)


def test_trace_global_meta_aliases_match_per_state_proposals_without_rewriting_receipts():
    capabilities, bundle = _evidence_bundle("(S 0 = 0 /\\ S 1 = 0) -> (false /\\ false)")
    evidence = bundle["evidence"]
    assert evidence["proved"]
    assert "?t2" in json.dumps(evidence["replay"]["trace"])
    assert "?t2" not in json.dumps(evidence["proposal_records"])
    assert _verify(bundle, capabilities) is None


def test_alias_matching_keeps_variable_distinctness_scope_and_complete_goal_order():
    from training.peano_hydra.symbolic import _goal_alias_key

    first = ("h : ?t8 = ?t8 ⊢ ?t8@1 = ?t9@0", "⊢ ?t9 = ?t8")
    renamed = ("h : ?t2 = ?t2 ⊢ ?t2@1 = ?t7@0", "⊢ ?t7 = ?t2")
    assert _goal_alias_key(first) == _goal_alias_key(renamed)
    assert _goal_alias_key(first) != _goal_alias_key(tuple(reversed(renamed)))
    assert _goal_alias_key(first) != _goal_alias_key(tuple(text.replace("?t7", "?t2") for text in renamed))
    assert _goal_alias_key(first) != _goal_alias_key(tuple(text.replace("@1", "@0") for text in renamed))


@pytest.mark.parametrize("mutation", ("bytes", "depth", "calls", "actions", "nonfinite", "opaque_object", "oversized_integer"))
def test_evidence_input_bounds_are_checked_before_regeneration(monkeypatch, mutation):
    import training.peano_hydra.symbolic as symbolic

    capabilities, bundle = _evidence_bundle()
    if mutation == "bytes":
        bundle["evidence"]["padding"] = "x" * (MAX_SYMBOLIC_EVIDENCE_BYTES + 1)
    elif mutation == "depth":
        deep = []
        for _ in range(40):
            deep = [deep]
        bundle["evidence"]["padding"] = deep
    elif mutation == "calls":
        bundle["evidence"]["proposal_records"] *= DEFAULT_SYMBOLIC_LIMITS.max_model_calls
    elif mutation == "actions":
        bundle["action_records"] = [bundle["action_records"][0]] * (SymbolicConfig().max_proposals * SymbolicConfig().candidates_per_state + 1)
    elif mutation == "nonfinite":
        bundle["workload"]["proposal_calls"] = float("nan")
    elif mutation == "opaque_object":
        bundle["workload"]["proposal_calls"] = object()
    elif mutation == "oversized_integer":
        bundle["workload"]["proposal_calls"] = 1 << 1000
    monkeypatch.setattr(symbolic, "make_symbolic_policy", lambda *args, **kwargs: pytest.fail("regeneration before bounds validation"))
    with pytest.raises(ValueError):
        _verify(bundle, capabilities)


def test_receipt_budget_hits_regenerate_without_silently_adding_positive_evidence():
    config = SymbolicConfig(max_action_receipt_bytes=1_024)
    capabilities, bundle = _evidence_bundle(config=config)
    assert bundle["workload"]["receipt_limit_hits"] > 0
    assert not bundle["evidence"]["proved"]
    assert _verify(bundle, capabilities, config) is None
