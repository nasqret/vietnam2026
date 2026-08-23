"""Fail-closed mixed Stable/body-only Lucas promotion remains bounded."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v13 as v13
from peano_lab.library.frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    FrontierPromotionError,
    construct_frontier_closed_candidate,
    frontier_promotion_plan,
)
from peano_lab.library.lucas_mixed_promotion import (
    LUCAS_CAMPAIGN_EXPECTED_COUNT,
    LUCAS_CAMPAIGN_INITIAL_MICROBATCH,
    LUCAS_CAMPAIGN_INITIAL_OBSERVED_DIRECT_STABLE_NODES,
    LUCAS_CAMPAIGN_INITIAL_OBSERVED_DIRECT_STABLE_OBJECTS,
    LUCAS_CAMPAIGN_SECOND_MICROBATCH,
    LUCAS_CAMPAIGN_THIRD_MICROBATCH,
    LUCAS_CAMPAIGN_FOURTH_MICROBATCH,
    LUCAS_MIXED_OBSERVED_STABLE_LEAF_NODES,
    LUCAS_MIXED_OBSERVED_STABLE_LEAF_OBJECTS,
    LUCAS_MIXED_PENDING_ROWS,
    LUCAS_MIXED_STABLE_ROWS,
    LUCAS_MIXED_TARGET,
    construct_lucas_campaign_closed_microbatch,
    construct_lucas_mixed_closed_candidate,
    lucas_campaign_closure_plan,
    lucas_campaign_ready_after,
    lucas_mixed_promotion_plan,
)


def test_mixed_plan_counts_every_stable_and_pending_contextual_body() -> None:
    mixed = lucas_mixed_promotion_plan()
    assert mixed.contextual_body_count == MAX_FRONTIER_CLOSURE_MICROBATCH == 16
    assert len(mixed.pending_rows) == 11
    assert len(mixed.stable_rows) == 5
    assert len(mixed.checked_leaves) == 27
    assert mixed.pending_leaves == (
        "choose_zero",
        "choose_self",
        "choose_succ_succ",
        "factorial_length_eq_transport",
        "factorial_weighted_product_combine",
        "factorial_prime_divides_of_le",
        "factorial_prime_le_of_divides",
    )
    assert mixed.parent_alpha_identity_sha256 == v13.ALPHA_V13_IDENTITY_SHA256


def test_mixed_stable_leaf_receipts_have_exact_low_envelope() -> None:
    catalog_path = (
        Path(__file__).resolve().parents[3]
        / "artifacts/peano-library/alpha/catalog-v13.json"
    )
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in catalog["theorems"]}
    leaves = lucas_mixed_promotion_plan().checked_leaves
    assert (
        sum(by_name[name]["empty_context_closure"]["proof_nodes"] for name in leaves)
        == LUCAS_MIXED_OBSERVED_STABLE_LEAF_NODES
        == 42_391
    )
    assert (
        sum(by_name[name]["empty_context_closure"]["proof_objects"] for name in leaves)
        == LUCAS_MIXED_OBSERVED_STABLE_LEAF_OBJECTS
        == 10_413
    )


@pytest.mark.parametrize(
    "pending,stable",
    (
        (LUCAS_MIXED_PENDING_ROWS + ("choose_self",), LUCAS_MIXED_STABLE_ROWS),
        (LUCAS_MIXED_PENDING_ROWS, LUCAS_MIXED_STABLE_ROWS + ("zero_le",)),
        (LUCAS_MIXED_PENDING_ROWS, LUCAS_MIXED_STABLE_ROWS[::-1]),
        (("choose_self",) + LUCAS_MIXED_PENDING_ROWS[1:], LUCAS_MIXED_STABLE_ROWS),
        (LUCAS_MIXED_PENDING_ROWS, LUCAS_MIXED_STABLE_ROWS[:-1] + ("choose_zero",)),
        (LUCAS_MIXED_PENDING_ROWS[:-1], LUCAS_MIXED_STABLE_ROWS),
    ),
)
def test_mixed_plan_rejects_changed_row_cap_order_or_evidence(pending, stable) -> None:
    with pytest.raises(FrontierPromotionError):
        lucas_mixed_promotion_plan(pending_rows=pending, stable_rows=stable)


def test_mixed_constructor_rejects_missing_actual_closed_prerequisites() -> None:
    with pytest.raises(FrontierPromotionError, match="missing independently closed"):
        construct_lucas_mixed_closed_candidate()


def test_mixed_constructor_rejects_unexpected_prerequisites() -> None:
    mixed = lucas_mixed_promotion_plan()
    fake = {name: object() for name in mixed.pending_leaves}
    fake["zero_add"] = object()
    with pytest.raises(FrontierPromotionError, match="unexpected"):
        construct_lucas_mixed_closed_candidate(prerequisites=fake)


def test_lucas_campaign_scheduler_pins_all_forty_four_sealed_rows() -> None:
    campaign = lucas_campaign_closure_plan()
    assert len(campaign.rows) == LUCAS_CAMPAIGN_EXPECTED_COUNT == 44
    assert len(campaign.parent_names) == 30
    assert len(campaign.initially_ready_rows) == 15
    assert campaign.rows[0].name == "lucas_digit_chain_initial_code_exists"
    assert campaign.rows[-1].name == "lucas_theorem"
    assert len(LUCAS_CAMPAIGN_INITIAL_MICROBATCH) == MAX_FRONTIER_CLOSURE_MICROBATCH
    assert LUCAS_CAMPAIGN_INITIAL_OBSERVED_DIRECT_STABLE_NODES == 66_162
    assert LUCAS_CAMPAIGN_INITIAL_OBSERVED_DIRECT_STABLE_OBJECTS == 14_824


def test_lucas_campaign_rejects_parent_row_and_non_lucas_slice() -> None:
    with pytest.raises(FrontierPromotionError, match="noncampaign"):
        construct_lucas_campaign_closed_microbatch(("choose_zero",))
    with pytest.raises(FrontierPromotionError, match="exact sealed root"):
        lucas_campaign_closure_plan(
            plan=frontier_promotion_plan(("four_square_lagrange",))
        )


def test_lucas_campaign_ready_after_sixteen_exactly_exposes_nine_rows() -> None:
    campaign = lucas_campaign_closure_plan()
    ready = lucas_campaign_ready_after(
        LUCAS_CAMPAIGN_INITIAL_MICROBATCH,
        closed_parents=campaign.parent_names,
    )
    assert len(ready) == 9
    names = {row.name for row in ready}
    assert set(LUCAS_CAMPAIGN_SECOND_MICROBATCH) <= names
    assert names.difference(LUCAS_CAMPAIGN_SECOND_MICROBATCH) == {
        "lucas_choose_prefix_extend",
        "lucas_prime_row_interior_divisible",
    }
    with pytest.raises(FrontierPromotionError, match="foreign row"):
        lucas_campaign_ready_after(("choose_zero",))


def test_lucas_campaign_progression_reaches_thirty_without_expensive_parents() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    table = v13.ALPHA_EDITION.by_name
    cache = {}

    def close(name: str):
        if name in cache:
            return cache[name]
        prerequisites = {
            dependency: close(dependency)
            for dependency in table[name].spec.dependencies
            if not table[dependency].checked_use
        }
        result = construct_frontier_closed_candidate(
            name, prerequisites=prerequisites, plan=plan
        )
        cache[name] = result.certificate
        return result.certificate

    for names in (
        LUCAS_CAMPAIGN_SECOND_MICROBATCH,
        LUCAS_CAMPAIGN_THIRD_MICROBATCH,
        LUCAS_CAMPAIGN_FOURTH_MICROBATCH,
    ):
        local = set(names)
        required = {
            dependency
            for name in names
            for dependency in table[name].spec.dependencies
            if not table[dependency].checked_use and dependency not in local
        }
        for name in required:
            close(name)
        result = construct_lucas_campaign_closed_microbatch(
            names, prerequisites=cache, plan=plan
        )
        assert tuple(row.name for row in result) == names
        total_nodes = sum(row.diagnostics.proof_nodes for row in result)
        total_objects = sum(row.diagnostics.proof_objects for row in result)
        print(
            f"Lucas campaign batch {len(names)}: "
            f"{total_nodes} proof nodes / {total_objects} proof objects"
        )
        assert total_nodes <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        assert total_objects <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        cache.update({row.name: row.certificate for row in result})

    completed = (
        set(LUCAS_CAMPAIGN_INITIAL_MICROBATCH)
        | set(LUCAS_CAMPAIGN_SECOND_MICROBATCH)
        | set(LUCAS_CAMPAIGN_THIRD_MICROBATCH)
        | set(LUCAS_CAMPAIGN_FOURTH_MICROBATCH)
    )
    assert len(completed) == 30
    assert "choose_exists" not in cache
    assert "choose_prime_divides_between" not in cache
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


def test_lucas_campaign_initial_microbatch_genuinely_closes_sixteen_rows() -> None:
    result = construct_lucas_campaign_closed_microbatch()
    assert tuple(row.name for row in result) == LUCAS_CAMPAIGN_INITIAL_MICROBATCH
    assert sum(row.diagnostics.proof_nodes for row in result) <= (
        MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert sum(row.diagnostics.proof_objects for row in result) <= (
        MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    )
    assert all(not v13.ALPHA_EDITION.by_name[row.name].checked_use for row in result)
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


def test_final_lucas_parent_has_an_actual_bounded_empty_context_certificate() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    table = v13.ALPHA_EDITION.by_name
    cache = {}

    def closed(name: str):
        if name in cache:
            return cache[name]
        pending = {
            dependency: closed(dependency)
            for dependency in table[name].spec.dependencies
            if not table[dependency].checked_use
        }
        result = construct_frontier_closed_candidate(name, prerequisites=pending, plan=plan)
        cache[name] = result.certificate
        return result.certificate

    mixed = lucas_mixed_promotion_plan(plan=plan)
    prerequisites = {name: closed(name) for name in mixed.pending_leaves}
    result = construct_lucas_mixed_closed_candidate(
        prerequisites=prerequisites, plan=plan
    )
    assert result.name == LUCAS_MIXED_TARGET
    assert result.diagnostics.proof_nodes < MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert result.diagnostics.proof_objects < MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    assert table[LUCAS_MIXED_TARGET].checked_use is False
    assert len(v13.ALPHA_CHECKED_SPECS) == 570
