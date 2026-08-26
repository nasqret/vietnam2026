"""Verifier-backed proof optimization, discovery, and post-training exports."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
for import_root in (ROOT, SCRIPTS):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import prepare_peano_hydra as prepare_script  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_hydra.curriculum import (  # noqa: E402
    HydraCurriculumError,
    _lineage,
    _lineage_index,
    build_verified_curriculum,
    encode_jsonl,
)
from training.peano_hydra.development import (  # noqa: E402
    AlphaNormalizedScriptPolicy,
    DevelopmentLimits,
    DiscoveryProposal,
    DiscoveryResult,
    HydraDevelopmentError,
    OptimizationResult,
    OptimizationRoute,
    _normalize_metavariables,
    discover_proof,
    optimize_proof,
    recorded_route_factory,
)
from training.peano_hydra.epoch import HydraEpoch  # noqa: E402
from training.peano_hydra.policy import RecordedState, ScriptCandidatePolicy  # noqa: E402
from training.peano_policy.prompt import ProofExample, parse_prompt  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


@pytest.fixture(scope="module")
def prepared() -> tuple[HydraEpoch, OptimizationResult, DiscoveryResult]:
    epoch, _ = prepare_script._audited_epoch()
    return epoch, prepare_script._optimization(epoch), prepare_script._discovery(epoch)


def test_optimization_prefers_shorter_independently_checked_original_proof(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, result, _ = prepared

    assert result.epoch_sha256 == epoch.epoch_sha256
    assert result.theorem_name == "zero_add"
    assert result.baseline.commands == (
        "have h : 0 = 0",
        "refl",
        "induction n",
        "simp",
        "simp [IH]",
    )
    assert result.winner.commands == ("induction n", "simp", "simp [IH]")
    assert result.tactic_decisions_saved == 2
    assert result.baseline.replay is not None
    assert result.winner.replay is not None
    assert result.baseline.replay.kernel_checked is True
    assert result.winner.replay.kernel_checked is True
    assert result.to_dict()["global_optimality_claim"] is False
    assert result.to_dict()["research_claim_eligible"] is False


def test_teacher_discovery_is_checked_but_not_admitted_or_claimed_novel(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, discovery = prepared
    receipt = discovery.to_dict()

    assert discovery.epoch_sha256 == epoch.epoch_sha256
    assert discovery.checked is True
    assert discovery.result.replay is not None
    assert discovery.result.replay.kernel_checked is True
    assert len(discovery.result.commands) == 13
    assert discovery.result.search.certificate_nodes == 180
    assert receipt["candidate_status"] == "kernel_checked_candidate_not_admitted"
    assert receipt["source"] == "teacher_oracle_plumbing"
    assert receipt["alpha_admitted"] is False
    assert receipt["semantic_novelty_claim"] is False
    assert receipt["research_claim_eligible"] is False


def test_verified_curriculum_contains_only_complete_qed_transitions(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    curriculum = build_verified_curriculum(epoch, optimization, discovery)

    assert len(curriculum.transitions) == 16
    assert len(curriculum.preferences) == 1
    assert len(curriculum.discoveries) == 1
    assert [row["theorem_name"] for row in curriculum.transitions[:3]] == [
        "zero_add",
        "zero_add",
        "zero_add",
    ]
    assert all(row["kernel_checked"] is True for row in curriculum.transitions)
    assert all(row["research_claim_eligible"] is False for row in curriculum.transitions)
    for row in curriculum.transitions:
        parsed = parse_prompt(row["prompt"])
        assert parsed.environment_sha256 == row["environment_sha256"]
        assert parsed.goals == tuple(row["goals_before"])
        assert ProofExample(
            example_id=f"verified:{row['theorem_name']}:{row['step']}",
            prompt=row["prompt"],
            completion=row["completion"],
            environment_sha256=row["environment_sha256"],
        ).tactic == row["action"]


def test_preferences_compare_two_separately_checked_complete_routes(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    preference = build_verified_curriculum(epoch, optimization, discovery).preferences[0]

    assert preference["chosen"] == "induction n</tactic>"
    assert preference["rejected"] == "have h : 0 = 0</tactic>"
    assert preference["chosen_remaining_tactics"] == 3
    assert preference["rejected_remaining_tactics"] == 5
    assert preference["chosen_kernel_checked"] is True
    assert preference["rejected_kernel_checked"] is True


def test_manifest_keeps_theorem_lineages_and_frozen_historical_adapter_separate(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    curriculum = build_verified_curriculum(epoch, optimization, discovery)
    manifest = curriculum.manifest()

    assert manifest["development_only"] is True
    assert manifest["sealed_benchmark"] is False
    assert manifest["model_trained"] is False
    assert manifest["alpha_admitted"] is False
    assert manifest["research_claim_eligible"] is False
    assert manifest["historical_model_authority"]["frozen_checked_theorem_count"] == 247
    assert manifest["historical_model_authority"]["silently_expanded"] is False
    assert not set(manifest["split_lineages"]["train"]) & set(
        manifest["split_lineages"]["dev"]
    )
    payload = encode_jsonl(curriculum.transitions)
    assert manifest["files"]["sft.jsonl"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert manifest["files"]["sft.jsonl"]["bytes"] == len(payload)


def test_additional_frozen_catalog_routes_expand_verified_training_data(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    additional = prepare_script._catalog_optimizations(
        epoch,
        prefix_count=2,
        theorem_names=("add_comm",),
    )
    curriculum = build_verified_curriculum(
        epoch,
        optimization,
        discovery,
        additional_optimizations=additional,
    )

    assert [item.theorem_name for item in additional] == ["add_succ_left", "add_comm"]
    assert len(curriculum.transitions) == 26
    assert sum(row["track"] == "checked_catalog_replay" for row in curriculum.transitions) == 10
    assert additional[1].winner.commands[:2] == (
        "use zero_add as zero_add",
        "use add_succ_left as add_succ_left",
    )
    assert all(
        row["source"] == "independently_checked_frozen_catalog_script"
        for row in curriculum.transitions
        if row["track"] == "checked_catalog_replay"
    )


def test_metavariable_normalization_preserves_names_and_exact_state_priority(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    _, optimization, _ = prepared

    assert _normalize_metavariables(
        ("⊢ ?t8 + ?t15 = ?t8", "⊢ ?t15 = ?t3")
    ) == ("⊢ ?t1 + ?t2 = ?t1", "⊢ ?t2 = ?t3")
    assert _normalize_metavariables(("⊢ ?t8 = ?t15",)) != (
        "⊢ ?t1 = ?t1",
    )

    source = ScriptCandidatePolicy.from_records(
        (
            RecordedState(("⊢ ?t8 = ?t8",), ("refl",)),
            RecordedState(("⊢ ?t15 = ?t15",), ("simp",)),
        ),
        name="exact-state-priority",
        policy_environment=optimization.winner.environment,
        provider_identity={"kind": "metavariable-alpha-regression"},
    )
    policy = AlphaNormalizedScriptPolicy(source)

    assert policy.propose(("⊢ ?t15 = ?t15",), max_candidates=2) == ("simp",)
    assert policy.propose(("⊢ ?t22 = ?t22",), max_candidates=2) == (
        "refl",
        "simp",
    )
    assert policy.propose(("⊢ ?t22 = ?t22",), max_candidates=1) == ("refl",)


def test_metavariable_renaming_keeps_multigoal_catalog_route_kernel_checked(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    additional = prepare_script._catalog_optimizations(
        epoch,
        prefix_count=0,
        theorem_names=("le_antisymm",),
    )
    winner = additional[0].winner

    assert winner.replay is not None
    assert winner.replay.kernel_checked is True
    assert len(winner.commands) == 10
    assert winner.commands[-2:] == ("exact h_nm_witness", "exact h_mn_witness")

    policy = winner.policy_identity["heads"][0]["policy"]
    assert policy["kind"] == "peano-hydra-metavariable-alpha-script-policy-v1"
    assert policy["normalization"] == "engine-metavariable-first-visible-occurrence-v1"
    assert policy["source"]["provider"]["batch"]["kernel_checked"] is True


def test_duplicate_checked_transitions_are_removed_without_merging_authority(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    broad = prepare_script._catalog_optimizations(
        epoch,
        prefix_count=0,
        theorem_names=("add_succ_left",),
    )[0]
    deduplicated = build_verified_curriculum(
        epoch,
        optimization,
        discovery,
        additional_optimizations=(broad, broad),
    )

    assert len(deduplicated.transitions) == 20
    assert deduplicated.duplicate_transitions_removed == 4
    assert deduplicated.manifest()["duplicate_transitions_removed"] == 4

    theorem = epoch.theorem("add_succ_left")
    capabilities = epoch.alpha_capabilities(
        allowed_commands=frozenset({"intro", "induction", "simp"}),
        allowed_theorems=frozenset(),
    )
    route = OptimizationRoute(
        "narrow-add-succ-left",
        recorded_route_factory(
            theorem.statement,
            theorem.script,
            capabilities=capabilities,
            name="narrow-add-succ-left",
        ),
        prepare_script._route_limits(len(theorem.script)),
    )
    narrow = optimize_proof(
        epoch,
        theorem.name,
        (route,),
        capabilities=capabilities,
    )
    separated = build_verified_curriculum(
        epoch,
        optimization,
        discovery,
        additional_optimizations=(broad, narrow),
    )
    catalog_rows = [
        row for row in separated.transitions if row["track"] == "checked_catalog_replay"
    ]

    assert len(separated.transitions) == 24
    assert separated.duplicate_transitions_removed == 0
    assert len({row["environment_sha256"] for row in catalog_rows}) == 2


def test_explicit_current_alpha_only_target_produces_checked_training_route(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    additional = prepare_script._catalog_optimizations(
        epoch,
        prefix_count=0,
        theorem_names=("crt_product_witness",),
    )

    assert len(additional) == 1
    assert additional[0].theorem_name == "crt_product_witness"
    assert additional[0].winner.replay is not None
    assert additional[0].winner.replay.kernel_checked is True
    assert len(additional[0].winner.commands) == 4


def test_complete_frozen_catalog_census_separates_decision_and_memory_eligibility(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    collection = prepare_script._collect_catalog_routes(
        epoch,
        prefix_count=0,
        theorem_names=(),
    )
    coverage = collection.coverage
    decision_eligible = tuple(
        theorem
        for theorem in epoch.theorems
        if theorem.name != "zero_add"
        and len(theorem.dependencies) + len(theorem.script)
        <= prepare_script.MAX_CATALOG_ROUTE_DECISIONS
    )
    resource_eligible = tuple(
        theorem
        for theorem in decision_eligible
        if len(theorem.statement.encode("utf-8"))
        <= prepare_script.MAX_CATALOG_STATEMENT_BYTES
    )
    by_name = {theorem.name: theorem for theorem in epoch.theorems}
    replay_safe = tuple(
        theorem
        for theorem in resource_eligible
        if prepare_script._catalog_prerequisite_profile(theorem, by_name)[0] is None
    )

    assert collection.results == ()
    assert coverage["enrolled_theorem_count"] == len(epoch.theorems)
    assert coverage["eligible_theorem_count"] == len(decision_eligible)
    assert coverage["resource_eligible_theorem_count"] == len(resource_eligible)
    assert coverage["replay_safe_theorem_count"] == len(replay_safe)
    for membership in prepare_script.CATALOG_MEMBERSHIPS:
        assert coverage["eligible_membership_counts"][membership] == sum(
            theorem.membership == membership for theorem in decision_eligible
        )
        assert coverage["resource_eligible_membership_counts"][membership] == sum(
            theorem.membership == membership for theorem in resource_eligible
        )
        assert coverage["replay_safe_membership_counts"][membership] == sum(
            theorem.membership == membership for theorem in replay_safe
        )
    assert coverage["skipped_reason_counts"]["built_in_optimization"] == 1
    assert coverage["skipped_reason_counts"]["decision_bound"] == (
        len(epoch.theorems) - len(decision_eligible) - 1
    )
    assert coverage["skipped_reason_counts"]["statement_byte_bound"] == (
        len(decision_eligible) - len(resource_eligible)
    )
    assert coverage["skipped_theorem_count"] == len(epoch.theorems)


def test_complete_catalog_sampling_is_deterministic_and_includes_alpha_early(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    by_name = {theorem.name: theorem for theorem in epoch.theorems}
    eligible = tuple(
        theorem
        for theorem in epoch.theorems
        if theorem.name != "zero_add"
        and len(theorem.dependencies) + len(theorem.script) <= 4
        and len(theorem.statement.encode("utf-8"))
        <= prepare_script.MAX_CATALOG_STATEMENT_BYTES
        and prepare_script._catalog_prerequisite_profile(theorem, by_name)[0] is None
    )
    first = prepare_script._catalog_order(epoch, eligible)
    second = prepare_script._catalog_order(epoch, eligible)

    assert first == second
    assert {theorem.name for theorem in first} == {theorem.name for theorem in eligible}
    assert {theorem.membership for theorem in first[:3]} == {"alpha_only", "stable"}
    assert any(theorem.enrollment_index >= epoch.stable_count for theorem in first[:3])

    collection = prepare_script._collect_catalog_routes(
        epoch,
        prefix_count=3,
        theorem_names=(),
        scan_all=True,
        max_decisions=4,
    )
    coverage = collection.coverage

    assert [result.theorem_name for result in collection.results] == [
        theorem.name for theorem in first[:3]
    ]
    assert coverage["collection_mode"] == "bounded_full_catalog_scan"
    assert coverage["selected_route_count"] == 3
    assert coverage["checked_route_count"] == 3
    assert coverage["checked_membership_counts"] == {
        membership: sum(theorem.membership == membership for theorem in first[:3])
        for membership in prepare_script.CATALOG_MEMBERSHIPS
    }
    assert coverage["attempted_tactic_decisions"] == sum(
        len(result.winner.commands) for result in collection.results
    )
    assert coverage["attempted_proof_state_reservations"] == (
        coverage["attempted_tactic_decisions"] + 3
    )
    assert all(result.winner.replay.kernel_checked for result in collection.results)


def test_catalog_scan_counts_rejected_routes_but_explicit_targets_fail_closed(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    epoch, _, _ = prepared
    original = prepare_script._checked_catalog_route
    by_name = {theorem.name: theorem for theorem in epoch.theorems}
    eligible = tuple(
        theorem
        for theorem in epoch.theorems
        if theorem.name != "zero_add"
        and len(theorem.dependencies) + len(theorem.script) <= 4
        and len(theorem.statement.encode("utf-8"))
        <= prepare_script.MAX_CATALOG_STATEMENT_BYTES
        and prepare_script._catalog_prerequisite_profile(theorem, by_name)[0] is None
    )
    ordered = prepare_script._catalog_order(epoch, eligible)
    rejected = ordered[0].name

    def reject_one(current: HydraEpoch, theorem: object) -> OptimizationResult:
        if theorem.name == rejected:
            raise HydraDevelopmentError("recorded route failed its original-goal source replay")
        return original(current, theorem)

    monkeypatch.setattr(prepare_script, "_checked_catalog_route", reject_one)
    collection = prepare_script._collect_catalog_routes(
        epoch,
        prefix_count=3,
        theorem_names=(),
        scan_all=True,
        max_decisions=4,
    )
    coverage = collection.coverage

    assert coverage["selected_route_count"] == 3
    assert coverage["checked_route_count"] == 2
    assert coverage["skipped_reason_counts"]["source_replay_rejected"] == 1
    assert coverage["failed_routes"][0]["theorem_name"] == rejected
    assert coverage["failed_routes"][0]["reason"] == "source_replay_rejected"
    assert coverage["attempted_tactic_decisions"] == sum(
        len(theorem.dependencies) + len(theorem.script)
        for theorem in ordered[:3]
    )
    assert rejected not in {item.theorem_name for item in collection.results}

    with pytest.raises(HydraDevelopmentError, match="failed its bounded checked route"):
        prepare_script._collect_catalog_routes(
            epoch,
            prefix_count=1,
            theorem_names=(rejected,),
            scan_all=True,
            max_decisions=4,
        )


def test_catalog_scan_reserves_failed_or_oversized_work_before_running_it(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    collection = prepare_script._collect_catalog_routes(
        epoch,
        prefix_count=2,
        theorem_names=(),
        scan_all=True,
        max_decisions=4,
        max_total_tactics=1,
    )
    coverage = collection.coverage

    assert coverage["checked_route_count"] == 1
    assert coverage["checked_membership_counts"] == {"alpha_only": 0, "stable": 1}
    assert coverage["attempted_tactic_decisions"] == 1
    assert coverage["attempted_proof_state_reservations"] == 2
    assert coverage["skipped_reason_counts"]["tactic_budget"] >= 1
    assert collection.results[0].theorem_name in {"succ_ne_zero", "succ_injective"}

    oversized = next(
        theorem
        for theorem in epoch.theorems
        if len(theorem.dependencies) + len(theorem.script) <= 32
        and len(theorem.statement.encode("utf-8"))
        > prepare_script.MAX_CATALOG_STATEMENT_BYTES
    )
    with pytest.raises(HydraDevelopmentError, match="byte statement bound"):
        prepare_script._collect_catalog_routes(
            epoch,
            prefix_count=0,
            theorem_names=(oversized.name,),
        )


def test_catalog_scan_rejects_expensive_promoted_prerequisites_before_replay(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    epoch, _, _ = prepared
    dangerous = epoch.theorem("four_square_product_square")
    assert dangerous is not None
    by_name = {theorem.name: theorem for theorem in epoch.theorems}

    assert prepare_script._catalog_prerequisite_profile(dangerous, by_name)[0] == (
        "alpha_prerequisite_replay_bound"
    )

    invoked: list[str] = []
    original = prepare_script._checked_catalog_route

    def audited(current: HydraEpoch, theorem: object) -> OptimizationResult:
        invoked.append(theorem.name)
        return original(current, theorem)

    monkeypatch.setattr(prepare_script, "_checked_catalog_route", audited)
    collection = prepare_script._collect_catalog_routes(
        epoch,
        prefix_count=1,
        theorem_names=(),
        scan_all=True,
        max_decisions=4,
    )

    assert dangerous.name not in invoked
    assert collection.coverage["skipped_reason_counts"][
        "alpha_prerequisite_replay_bound"
    ] >= 1
    assert collection.coverage["automatic_prerequisite_membership"] == "stable_only"

    with pytest.raises(HydraDevelopmentError, match="bounded prerequisite replay policy"):
        prepare_script._collect_catalog_routes(
            epoch,
            prefix_count=1,
            theorem_names=(dangerous.name,),
            scan_all=True,
            max_decisions=4,
        )
    assert dangerous.name not in invoked


def test_precomputed_lineage_index_preserves_each_exact_frozen_component(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    lineages = _lineage_index(epoch)

    assert len(lineages) == len(epoch.theorems)
    for theorem in (
        epoch.theorems[0],
        epoch.theorems[epoch.stable_count - 1],
        epoch.theorems[epoch.stable_count],
        epoch.theorems[-1],
    ):
        assert lineages[theorem.name] == _lineage(epoch, (theorem.name,))
        for dependency in theorem.dependencies:
            assert lineages[dependency] == lineages[theorem.name]


def test_catalog_scan_refuses_to_retain_independently_checked_oversized_traces(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    epoch, _, _ = prepared
    monkeypatch.setattr(
        prepare_script,
        "_catalog_evidence_bytes",
        lambda result: prepare_script.MAX_CATALOG_ROUTE_EVIDENCE_BYTES + 1,
    )
    collection = prepare_script._collect_catalog_routes(
        epoch,
        prefix_count=1,
        theorem_names=(),
        scan_all=True,
        max_decisions=4,
    )
    coverage = collection.coverage

    assert collection.results == ()
    assert coverage["selected_route_count"] == 1
    assert coverage["checked_route_count"] == 0
    assert coverage["retained_evidence_bytes"] == 0
    assert coverage["skipped_reason_counts"]["route_evidence_byte_bound"] == 1
    assert coverage["failed_routes"][0]["reason"] == "route_evidence_byte_bound"


def test_cli_accepts_bounded_whole_catalog_scan_without_changing_legacy_defaults() -> None:
    parser = prepare_script.build_parser()
    ordinary = parser.parse_args([])
    expanded = parser.parse_args(
        [
            "--catalog-all",
            "--catalog-limit",
            "256",
            "--catalog-max-decisions",
            "16",
            "--catalog-max-tactics",
            "2048",
        ]
    )

    assert ordinary.catalog_all is False
    assert ordinary.catalog_limit == 0
    assert ordinary.catalog_max_decisions == 32
    assert ordinary.catalog_max_tactics == 8192
    assert expanded.catalog_all is True
    assert expanded.catalog_limit == 256
    assert expanded.catalog_max_decisions == 16
    assert expanded.catalog_max_tactics == 2048


def test_additional_catalog_routes_reject_unknown_or_excessive_requests(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    with pytest.raises(HydraDevelopmentError, match="0–512"):
        prepare_script._catalog_optimizations(epoch, prefix_count=513, theorem_names=())
    with pytest.raises(HydraDevelopmentError, match="is not enrolled"):
        prepare_script._catalog_optimizations(
            epoch,
            prefix_count=0,
            theorem_names=("not_an_admitted_alpha_theorem",),
        )
    with pytest.raises(HydraDevelopmentError, match="1–32"):
        prepare_script._collect_catalog_routes(
            epoch,
            prefix_count=1,
            theorem_names=(),
            scan_all=True,
            max_decisions=33,
        )
    with pytest.raises(HydraDevelopmentError, match="between 1 and 8192"):
        prepare_script._collect_catalog_routes(
            epoch,
            prefix_count=1,
            theorem_names=(),
            scan_all=True,
            max_total_tactics=8193,
        )


def test_unchecked_or_wrong_epoch_proofs_never_create_positive_training_rows(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    unchecked = replace(
        optimization,
        winner=replace(
            optimization.winner,
            replay=replace(optimization.winner.replay, kernel_checked=False),
        ),
    )
    with pytest.raises(HydraCurriculumError, match="original-goal QED replay"):
        build_verified_curriculum(epoch, unchecked, discovery)

    wrong_epoch = replace(discovery, epoch_sha256="0" * 64)
    with pytest.raises(HydraCurriculumError, match="frozen epoch"):
        build_verified_curriculum(epoch, optimization, wrong_epoch)


def test_training_proofs_cannot_be_mislabeled_under_other_checked_theorems(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, discovery = prepared
    wrong_target = replace(optimization, theorem_name="add_succ_left")
    with pytest.raises(HydraCurriculumError, match="exact enrolled statement"):
        build_verified_curriculum(epoch, wrong_target, discovery)

    changed_proposal = replace(
        discovery,
        proposal=replace(discovery.proposal, theorem="forall n. n = n"),
    )
    with pytest.raises(HydraCurriculumError, match="exact proposed statement"):
        build_verified_curriculum(epoch, optimization, changed_proposal)


def test_route_resource_reservations_fail_before_running_policy_factory(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, _ = prepared
    called = False

    def forbidden():
        nonlocal called
        called = True
        raise AssertionError("the out-of-budget route must never start")

    capabilities = epoch.alpha_capabilities(
        allowed_commands=frozenset({"induction", "simp"}),
        allowed_theorems=frozenset(),
    )
    route = OptimizationRoute(
        "excessive",
        forbidden,
        SearchLimits(
            max_depth=3,
            beam_width=1,
            candidates_per_state=1,
            max_model_calls=4,
            max_states=4,
        ),
    )
    with pytest.raises(HydraDevelopmentError, match="model-call reservations"):
        optimize_proof(
            epoch,
            "zero_add",
            (route,),
            capabilities=capabilities,
            limits=DevelopmentLimits(max_total_model_calls=3),
        )
    assert called is False


def test_optimization_cannot_import_its_target_as_a_trivial_proof(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, optimization, _ = prepared
    capabilities = epoch.alpha_capabilities(
        allowed_commands=frozenset({"exact", "use"}),
        allowed_theorems=frozenset({"zero_add"}),
    )
    route = OptimizationRoute(
        "forbidden-self-import",
        lambda: optimization.winner,
        SearchLimits(
            max_depth=2,
            beam_width=1,
            candidates_per_state=1,
            max_model_calls=2,
            max_states=3,
        ),
    )
    with pytest.raises(HydraDevelopmentError, match="target or a descendant"):
        optimize_proof(epoch, "zero_add", (route,), capabilities=capabilities)


def test_discovery_cannot_reuse_existing_name_or_exact_statement(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, discovery = prepared
    capabilities = epoch.alpha_capabilities(
        allowed_commands=frozenset({"induction", "simp"}),
        allowed_theorems=frozenset(),
    )
    target = epoch.theorem("zero_add")
    factory = recorded_route_factory(
        target.statement,
        target.script,
        capabilities=capabilities,
        name="known-foundation",
    )
    limits = SearchLimits(
        max_depth=3,
        beam_width=1,
        candidates_per_state=1,
        max_model_calls=3,
        max_states=4,
    )
    reused_name = DiscoveryProposal(
        target.name,
        discovery.proposal.theorem,
        (),
        factory,
        limits,
    )
    with pytest.raises(HydraDevelopmentError, match="name already belongs"):
        discover_proof(epoch, reused_name, capabilities=capabilities)

    reused_formula = DiscoveryProposal(
        "same_foundation_under_a_new_name",
        target.statement,
        (),
        factory,
        limits,
    )
    with pytest.raises(HydraDevelopmentError, match="statement already appears"):
        discover_proof(epoch, reused_formula, capabilities=capabilities)


def test_discovery_theorem_allowlist_must_match_exact_declared_dependencies(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, discovery = prepared
    capabilities = epoch.alpha_capabilities(
        allowed_commands=frozenset({"exact", "use"}),
        allowed_theorems=frozenset({"zero_add"}),
    )
    with pytest.raises(HydraDevelopmentError, match="allowlist must match exactly"):
        discover_proof(epoch, discovery.proposal, capabilities=capabilities)


def test_hydra_never_accepts_default_stable_surface_as_alpha_authority(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
) -> None:
    epoch, _, discovery = prepared
    stable = SurfaceCapabilities(
        label="ordinary-stable-only",
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    with pytest.raises(HydraDevelopmentError, match="exact frozen Alpha epoch"):
        discover_proof(epoch, discovery.proposal, capabilities=stable)


def test_prepare_cli_publishes_complete_reproducible_local_artifacts(
    prepared: tuple[HydraEpoch, OptimizationResult, DiscoveryResult],
    tmp_path: Path,
) -> None:
    del prepared
    output = tmp_path / "hydra-development"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "prepare_peano_hydra.py"),
        "--output-dir",
        str(output),
    ]
    first = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    initial = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.iterdir()
    }
    second = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    repeated = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.iterdir()
    }

    assert set(initial) == set(prepare_script.OUTPUT_FILENAMES)
    assert initial == repeated
    assert json.loads(first.stdout) == json.loads(second.stdout)
    assert json.loads(first.stdout)["duplicate_transitions_removed"] == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["transition_count"] == 16
    assert manifest["duplicate_transitions_removed"] == 0
    assert manifest["preference_count"] == 1
    assert manifest["optimization"]["tactic_decisions_saved"] == 2
    assert manifest["discovery"]["kernel_checked"] is True


def test_hydra_output_refuses_existing_symlink_targets(tmp_path: Path) -> None:
    directory = tmp_path / "hydra"
    directory.mkdir()
    protected = tmp_path / "protected.json"
    protected.write_text("unchanged", encoding="utf-8")
    (directory / "manifest.json").symlink_to(protected)

    with pytest.raises(HydraDevelopmentError, match="not a regular file"):
        prepare_script._publish(
            directory,
            epoch=None,
            curriculum=None,
            manifest={},
            include_graphs=False,
        )
    assert protected.read_text(encoding="utf-8") == "unchanged"
