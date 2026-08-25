"""Real bounded proofs of both previously oversized power-valuation roots."""

from __future__ import annotations

from dataclasses import replace

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import editions_v12 as v12
from peano_lab.library import valuation_shared_promotion as shared
from peano_lab.library.bertrand_promotion import (
    MAX_BERTRAND_CLOSURE_MICROBATCH,
    MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    bertrand_promotion_plan,
)
from peano_lab.library.theorems import _closed_formula
from peano_lab.library.valuation_shared_promotion import (
    BOUNDED_VALUATION_SHARED_TARGET,
    CANONICAL_VALUATION_SHARED_TARGET,
    VALUATION_NAIVE_BOUNDED_PROOF_NODES,
    VALUATION_NAIVE_CANONICAL_PROOF_NODES,
    VALUATION_REUSED_POWER_TOTALITY_PROOF_NODES,
    VALUATION_SHARED_PENDING_ROWS,
    VALUATION_SHARED_STABLE_LEAF_PROOF_NODES,
    VALUATION_SHARED_STABLE_LEAF_PROOF_OBJECTS,
    VALUATION_SHARED_STABLE_LEAVES,
    VALUATION_SHARED_TARGETS,
    ValuationSharedPromotionError,
    check_valuation_shared_candidate,
    construct_valuation_shared_closed_candidate,
    valuation_shared_promotion_plan,
)


@pytest.fixture(scope="module")
def actually_closed():
    plan = bertrand_promotion_plan()
    return {
        name: construct_valuation_shared_closed_candidate(name, plan=plan)
        for name in VALUATION_SHARED_TARGETS
    }


def test_exact_deferred_targets_have_sealed_dependency_order() -> None:
    bounded = valuation_shared_promotion_plan(BOUNDED_VALUATION_SHARED_TARGET)
    canonical = valuation_shared_promotion_plan(CANONICAL_VALUATION_SHARED_TARGET)

    assert bounded.pending_rows == VALUATION_SHARED_PENDING_ROWS
    assert canonical.pending_rows == (
        *VALUATION_SHARED_PENDING_ROWS,
        CANONICAL_VALUATION_SHARED_TARGET,
    )
    assert bounded.stable_leaves == VALUATION_SHARED_STABLE_LEAVES
    assert canonical.stable_leaves == VALUATION_SHARED_STABLE_LEAVES
    assert bounded.parent_alpha_identity_sha256 == v12.ALPHA_V12_IDENTITY_SHA256
    assert canonical.parent_alpha_enrollment_sha256 == (
        v12.ALPHA_V12_ENROLLMENT_SHA256
    )


def test_actual_proof_graph_respects_the_unchanged_sixteen_row_ceiling() -> None:
    bounded = valuation_shared_promotion_plan(BOUNDED_VALUATION_SHARED_TARGET)
    canonical = valuation_shared_promotion_plan(CANONICAL_VALUATION_SHARED_TARGET)

    assert bounded.contextual_body_count == 4
    assert canonical.contextual_body_count == 5
    assert bounded.proof_graph_node_count == 15
    assert canonical.proof_graph_node_count == MAX_BERTRAND_CLOSURE_MICROBATCH == 16


def test_power_totality_is_one_genuine_shared_stable_leaf() -> None:
    plan = valuation_shared_promotion_plan(CANONICAL_VALUATION_SHARED_TARGET)

    assert plan.stable_leaves.count("pow_exists") == 1
    assert VALUATION_REUSED_POWER_TOTALITY_PROOF_NODES == 59_836
    assert VALUATION_SHARED_STABLE_LEAF_PROOF_NODES == 65_364
    assert VALUATION_SHARED_STABLE_LEAF_PROOF_OBJECTS == 7_956
    assert VALUATION_SHARED_STABLE_LEAF_PROOF_NODES < (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert VALUATION_SHARED_STABLE_LEAF_PROOF_OBJECTS < (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS
    )
    assert all(
        v12.ALPHA_EDITION.by_name[name].evidence is v12.EvidenceStatus.STABLE_CLOSED
        for name in plan.stable_leaves
    )


@pytest.mark.parametrize("name", VALUATION_SHARED_TARGETS)
def test_each_original_root_has_a_real_empty_context_kernel_proof(
    name: str,
    actually_closed,
) -> None:
    actual = actually_closed[name]
    exact = _closed_formula(v12.ALPHA_EDITION.by_name[name].spec.statement)

    assert actual.name == name
    assert actual.diagnostics.name == name
    assert actual.diagnostics.statement_sha256 == next(
        row.statement_sha256
        for row in bertrand_promotion_plan().rows
        if row.name == name
    )
    assert check((), actual.certificate, exact)
    assert actual.diagnostics.proof_nodes <= (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert actual.diagnostics.proof_objects <= (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS
    )


def test_shared_proofs_remove_the_old_actual_resource_obstruction(
    actually_closed,
) -> None:
    bounded = actually_closed[BOUNDED_VALUATION_SHARED_TARGET].diagnostics
    canonical = actually_closed[CANONICAL_VALUATION_SHARED_TARGET].diagnostics

    assert VALUATION_NAIVE_BOUNDED_PROOF_NODES == 125_454
    assert VALUATION_NAIVE_CANONICAL_PROOF_NODES == 125_470
    assert VALUATION_NAIVE_BOUNDED_PROOF_NODES > (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert VALUATION_NAIVE_CANONICAL_PROOF_NODES > (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert bounded.proof_nodes < VALUATION_NAIVE_BOUNDED_PROOF_NODES
    assert canonical.proof_nodes < VALUATION_NAIVE_CANONICAL_PROOF_NODES
    assert (bounded.proof_nodes, bounded.proof_objects, bounded.proof_depth) == (
        65_708,
        5_952,
        92,
    )
    assert (
        canonical.proof_nodes,
        canonical.proof_objects,
        canonical.proof_depth,
    ) == (65_727, 5_971, 92)


@pytest.mark.parametrize("name", VALUATION_SHARED_TARGETS)
def test_forged_empty_context_proof_is_rejected(name: str) -> None:
    with pytest.raises(ValuationSharedPromotionError, match="rejected"):
        check_valuation_shared_candidate(name, Hyp(0))


@pytest.mark.parametrize("name", ["pow_exists", "bertrand_strict", "missing", ""])
def test_non_deferred_target_cannot_be_granted_valuation_authority(name: str) -> None:
    with pytest.raises(ValuationSharedPromotionError, match="two exact deferred roots"):
        valuation_shared_promotion_plan(name)
    with pytest.raises(ValuationSharedPromotionError, match="two exact deferred roots"):
        check_valuation_shared_candidate(name, Hyp(0))


@pytest.mark.parametrize("field", ["target", "pending_rows", "stable_leaves"])
def test_mutated_frozen_proof_plan_fails_before_replay(field: str) -> None:
    original = valuation_shared_promotion_plan()
    if field == "target":
        mutated = replace(original, target=CANONICAL_VALUATION_SHARED_TARGET)
    elif field == "pending_rows":
        mutated = replace(original, pending_rows=original.pending_rows[:-1])
    else:
        mutated = replace(original, stable_leaves=original.stable_leaves[1:])

    with pytest.raises(ValuationSharedPromotionError, match="exact sealed"):
        construct_valuation_shared_closed_candidate(shared_plan=mutated)


def test_tighter_row_cap_is_enforced_without_constructing_a_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shared, "MAX_BERTRAND_CLOSURE_MICROBATCH", 14)

    with pytest.raises(ValuationSharedPromotionError, match="sixteen-row budget"):
        valuation_shared_promotion_plan()


def test_tighter_structural_cap_rejects_an_actual_root(
    monkeypatch: pytest.MonkeyPatch,
    actually_closed,
) -> None:
    actual = actually_closed[BOUNDED_VALUATION_SHARED_TARGET]
    monkeypatch.setattr(
        shared,
        "MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES",
        actual.diagnostics.proof_nodes - 1,
    )

    with pytest.raises(ValuationSharedPromotionError, match="125,000/25,000 limits"):
        check_valuation_shared_candidate(
            BOUNDED_VALUATION_SHARED_TARGET,
            actual.certificate,
        )


def test_actual_closures_do_not_change_release_or_stable_authority(
    actually_closed,
) -> None:
    assert set(actually_closed) == set(VALUATION_SHARED_TARGETS)
    assert len(v12.STABLE_SPECS) == 432
    assert all(
        v12.ALPHA_EDITION.by_name[name].evidence
        is v12.EvidenceStatus.BODY_CHECKED
        and not v12.ALPHA_EDITION.by_name[name].checked_use
        for name in VALUATION_SHARED_TARGETS
    )
