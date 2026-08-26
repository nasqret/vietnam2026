"""Bounded genuine empty-context planning for Lucas and Lagrange frontiers."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import DNE, EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v13 as v13
from peano_lab.library import frontier_promotion as promotion
from peano_lab.library.frontier_promotion import (
    FRONTIER_PROMOTION_ROOTS,
    LUCAS_FACTORIAL_BRIDGE_NAIVE_DIRECT_NODE_LOWER_BOUND,
    LUCAS_FACTORIAL_BRIDGE_OBSERVED_DIRECT_PROOF_NODES,
    LUCAS_PRIME_DIVIDES_MAXIMAL_SHARED_ROWS,
    LUCAS_PRIME_DIVIDES_OBSERVED_UNCHECKED_LEAF_PROOF_NODES,
    LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_COUNT,
    LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_PROOF_NODES,
    LUCAS_PRIME_DIVIDES_SHARED_LEAF_NODE_LOWER_BOUND,
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    FrontierPromotionError,
    FrontierPromotionPlan,
    check_frontier_promotion_batch,
    check_frontier_promotion_certificate,
    cold_frontier_microbatch_receipts,
    construct_frontier_closed_candidate,
    construct_frontier_closed_microbatch,
    construct_frontier_shared_closed_candidate,
    frontier_pending_layers,
    frontier_promotion_plan,
)


LUCAS_SAFE_MICROBATCH = (
    "le_mul_of_one_le_right",
    "prime_two_le",
    "succ_le_mul_of_two_le_right",
    "choose_out_of_range_zero",
    "choose_upper_eq_transport",
    "factorial_length_eq_transport",
    "factorial_weighted_product_combine",
)
LAGRANGE_SAFE_MICROBATCH = (
    "bounded_nonzero_not_divides",
    "pair_order_double_succ_length",
    "odd_half_strictly_below_modulus",
    "even_to_mod_two_zero",
    "odd_to_mod_two_one",
    "mul_le_mul",
    "two_mul_eq_add_self",
    "square_lt_successor_square",
    "mul_le_cancel_left_nonzero",
)


@pytest.mark.parametrize(
    (
        "roots",
        "row_count",
        "stable_count",
        "alpha_closed_count",
        "pending_count",
        "parent_count",
        "frontier_count",
        "edge_count",
        "names_digest",
        "surface_digest",
    ),
    (
        (
            ("lucas_theorem",),
            213,
            138,
            1,
            74,
            30,
            44,
            617,
            "52d9e8ec5eb1942d5a583cd272b7d26aecae5d8e6d4c78a48b6354a541f7af52",
            "21232d244a2d416f2ee1465d55e5d2a025b86fb61778f6316785ca917d7a7728",
        ),
        (
            ("four_square_lagrange",),
            390,
            166,
            5,
            219,
            23,
            196,
            1187,
            "9a94742066b28f553ad78fd675c41354a461cbe5f69f8e5df3ec36f9b055a843",
            "8a92bf2d6fd4c716112d1a84994725589f696c6289e6a33d1729ea33235759d5",
        ),
        (
            FRONTIER_PROMOTION_ROOTS,
            481,
            183,
            5,
            293,
            53,
            240,
            1537,
            "601b50c755aab5b56708d4f47cf9304e5fd0213695c0826e8c6f561c5516a55b",
            "c780df8c7855c09f5f2db6f0fe43a3deef80a6b527934c0ed29f6825fae8e92a",
        ),
    ),
)
def test_exact_frontier_promotion_slices_are_pinned_and_dependency_closed(
    roots: tuple[str, ...],
    row_count: int,
    stable_count: int,
    alpha_closed_count: int,
    pending_count: int,
    parent_count: int,
    frontier_count: int,
    edge_count: int,
    names_digest: str,
    surface_digest: str,
) -> None:
    plan = frontier_promotion_plan(roots)
    assert type(plan) is FrontierPromotionPlan
    assert plan.roots == roots
    assert len(plan.rows) == row_count
    assert len(plan.stable_rows) == stable_count
    assert len(plan.alpha_closed_rows) == alpha_closed_count
    assert len(plan.pending_rows) == pending_count
    assert len(plan.unchecked_parent_rows) == parent_count
    assert len(plan.unchecked_frontier_rows) == frontier_count
    assert plan.dependency_edge_count == edge_count
    assert plan.ordered_names_sha256 == names_digest
    assert plan.exact_surface_sha256 == surface_digest
    assert plan.parent_alpha_enrollment_sha256 == v13.ALPHA_V13_ENROLLMENT_SHA256
    assert plan.parent_alpha_identity_sha256 == v13.ALPHA_V13_IDENTITY_SHA256

    seen: set[str] = set()
    for row in plan.rows:
        assert set(row.dependencies) <= seen
        seen.add(row.name)


def test_frontier_unchecked_parent_campaigns_are_disjoint() -> None:
    lucas = frontier_promotion_plan(("lucas_theorem",))
    lagrange = frontier_promotion_plan(("four_square_lagrange",))
    union = frontier_promotion_plan()

    first = {row.name for row in lucas.unchecked_parent_rows}
    second = {row.name for row in lagrange.unchecked_parent_rows}
    assert len(first) == 30
    assert len(second) == 23
    assert not first & second
    assert first | second == {row.name for row in union.unchecked_parent_rows}
    assert {
        row.enrollment_origin
        for row in lucas.unchecked_parent_rows
    } == {"bertrand", "bertrand_b1_power_order", "bertrand_b2_valuation_laws"}
    assert Counter(row.enrollment_origin for row in lagrange.unchecked_parent_rows)[
        "qr"
    ] == 18
    assert "quadratic_reciprocity_combined" not in {row.name for row in union.rows}
    assert {
        "bounded_power_valuation_exists",
        "power_valuation_exists",
    }.isdisjoint(row.name for row in union.rows)


def test_frontier_pending_layers_are_dependency_safe_and_honest() -> None:
    plan = frontier_promotion_plan()
    layers = frontier_pending_layers(plan=plan)
    assert tuple(map(len, layers)) == (
        100, 53, 33, 24, 15, 11, 8, 6, 13, 12, 4, 4, 2, 2, 2, 1, 1, 1, 1,
    )
    pending = {row.name for row in plan.pending_rows}
    available = {row.name for row in plan.rows if row.checked_use}
    for layer in layers:
        assert set(layer) <= pending
        for name in layer:
            assert set(v13.ALPHA_EDITION.by_name[name].spec.dependencies) <= available
        available.update(layer)
    assert pending <= available


@pytest.mark.parametrize(
    ("roots", "message"),
    (
        ((), "at least one"),
        ("lucas_theorem", "tuple or list"),
        ((1,), "exact strings"),
        (("lucas_theorem", "lucas_theorem"), "duplicate"),
        (("bertrand_strict",), "unsupported"),
    ),
)
def test_invalid_frontier_root_selections_fail_closed(roots, message: str) -> None:
    with pytest.raises(FrontierPromotionError, match=message):
        frontier_promotion_plan(roots)


def test_promotion_planning_never_changes_existing_release_evidence() -> None:
    before = (
        v13.ALPHA_V13_ENROLLMENT_SHA256,
        v13.ALPHA_V13_IDENTITY_SHA256,
        v13.STABLE_EDITION.identity_sha256,
        len(v13.ALPHA_CHECKED_SPECS),
    )
    plan = frontier_promotion_plan()
    assert before == (
        v13.ALPHA_V13_ENROLLMENT_SHA256,
        v13.ALPHA_V13_IDENTITY_SHA256,
        v13.STABLE_EDITION.identity_sha256,
        len(v13.ALPHA_CHECKED_SPECS),
    )
    assert before[-1] == 570
    assert all(not v13.ALPHA_EDITION.by_name[row.name].checked_use for row in plan.pending_rows)


def test_actual_checked_use_certificate_can_be_verified_without_promoting_it() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    checked = v13.replay("zero_add", edition="alpha")
    receipt = check_frontier_promotion_certificate(
        "zero_add", checked.certificate, plan=plan
    )
    assert receipt.proof_nodes > 0
    assert receipt.proof_objects > 0
    assert receipt.statement_sha256 == next(
        row.statement_sha256 for row in plan.rows if row.name == "zero_add"
    )


def test_false_proof_classical_dne_and_nonproof_fail_closed() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    with pytest.raises(FrontierPromotionError, match="kernel rejected"):
        check_frontier_promotion_certificate("zero_add", EqRefl(Zero()), plan=plan)
    with pytest.raises(FrontierPromotionError, match="classical DNE"):
        check_frontier_promotion_certificate(
            "zero_add", DNE(Eq(Zero(), Zero())), plan=plan
        )
    with pytest.raises(FrontierPromotionError, match="must be a kernel proof"):
        check_frontier_promotion_certificate("zero_add", object(), plan=plan)


def test_unknown_theorem_wrong_plan_and_modified_statement_fail_closed() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    with pytest.raises(FrontierPromotionError, match="outside the frontier slice"):
        check_frontier_promotion_certificate(
            "quadratic_reciprocity_combined", EqRefl(Zero()), plan=plan
        )
    with pytest.raises(FrontierPromotionError, match="invalid type"):
        check_frontier_promotion_certificate("zero_add", EqRefl(Zero()), plan=object())
    mutated = replace(
        plan,
        rows=tuple(
            replace(row, statement="0 = 0") if row.name == "zero_add" else row
            for row in plan.rows
        ),
    )
    with pytest.raises(FrontierPromotionError, match="sealed Alpha-v13 slice"):
        check_frontier_promotion_certificate("zero_add", EqRefl(Zero()), plan=mutated)


def test_complete_batch_refuses_missing_unexpected_and_forged_proofs() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    with pytest.raises(FrontierPromotionError, match="missing 74"):
        check_frontier_promotion_batch({}, plan=plan)
    certificates = {row.name: EqRefl(Zero()) for row in plan.pending_rows}
    certificates["zero_add"] = v13.replay("zero_add", edition="alpha").certificate
    with pytest.raises(FrontierPromotionError, match="unexpected frontier"):
        check_frontier_promotion_batch(certificates, plan=plan)
    certificates.pop("zero_add")
    with pytest.raises(FrontierPromotionError, match="kernel rejected"):
        check_frontier_promotion_batch(certificates, plan=plan)


def test_lucas_safe_microbatch_constructs_seven_real_empty_context_proofs() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    result = construct_frontier_closed_microbatch(LUCAS_SAFE_MICROBATCH, plan=plan)
    assert tuple((row.name, row.diagnostics.proof_nodes) for row in result) == (
        ("le_mul_of_one_le_right", 141),
        ("prime_two_le", 125),
        ("succ_le_mul_of_two_le_right", 316),
        ("choose_out_of_range_zero", 95),
        ("choose_upper_eq_transport", 52),
        ("factorial_length_eq_transport", 26),
        ("factorial_weighted_product_combine", 382),
    )
    assert sum(row.diagnostics.proof_nodes for row in result) == 1_137
    assert sum(row.diagnostics.proof_objects for row in result) == 993
    assert all(not v13.ALPHA_EDITION.by_name[row.name].checked_use for row in result)
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


def test_lagrange_safe_microbatch_constructs_nine_real_empty_context_proofs() -> None:
    plan = frontier_promotion_plan(("four_square_lagrange",))
    result = construct_frontier_closed_microbatch(LAGRANGE_SAFE_MICROBATCH, plan=plan)
    assert tuple((row.name, row.diagnostics.proof_nodes) for row in result) == (
        ("bounded_nonzero_not_divides", 140),
        ("pair_order_double_succ_length", 46),
        ("odd_half_strictly_below_modulus", 315),
        ("even_to_mod_two_zero", 55),
        ("odd_to_mod_two_one", 115),
        ("mul_le_mul", 521),
        ("two_mul_eq_add_self", 275),
        ("square_lt_successor_square", 592),
        ("mul_le_cancel_left_nonzero", 679),
    )
    assert sum(row.diagnostics.proof_nodes for row in result) < (
        MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert sum(row.diagnostics.proof_objects for row in result) < (
        MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    )
    assert all(not v13.ALPHA_EDITION.by_name[row.name].checked_use for row in result)


def test_constructor_requires_actual_direct_unchecked_dependency_proofs() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    with pytest.raises(FrontierPromotionError, match="missing independently closed"):
        construct_frontier_closed_candidate("beta_pascal_zero_row_exists", plan=plan)
    with pytest.raises(FrontierPromotionError, match="already has closed evidence"):
        construct_frontier_closed_candidate("zero_add", plan=plan)
    with pytest.raises(FrontierPromotionError, match="unexpected frontier prerequisite"):
        construct_frontier_closed_candidate(
            "factorial_length_eq_transport",
            prerequisites={"zero_add": v13.replay("zero_add", edition="alpha").certificate},
            plan=plan,
        )


def test_naive_factorial_bridge_direct_prerequisite_barrier_is_exact() -> None:
    assert LUCAS_FACTORIAL_BRIDGE_OBSERVED_DIRECT_PROOF_NODES == (
        ("choose_exists", 89_492),
        ("choose_weighted_vertical", 102_493),
        ("choose_self_of_eq", 2_236),
        ("factorial_length_eq_transport", 26),
        ("factorial_weighted_product_combine", 382),
    )
    assert LUCAS_FACTORIAL_BRIDGE_NAIVE_DIRECT_NODE_LOWER_BOUND == 194_629
    assert (
        LUCAS_FACTORIAL_BRIDGE_NAIVE_DIRECT_NODE_LOWER_BOUND
        - MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    ) == 69_629
    bridge = v13.ALPHA_EDITION.by_name["choose_factorial_bridge"].spec
    assert {
        name for name, _count in LUCAS_FACTORIAL_BRIDGE_OBSERVED_DIRECT_PROOF_NODES
    } <= set(bridge.dependencies)


def test_maximal_prime_divisibility_shared_package_still_exceeds_fixed_limit() -> None:
    target = "choose_prime_divides_between"
    local = set(LUCAS_PRIME_DIVIDES_MAXIMAL_SHARED_ROWS + (target,))
    assert len(local) == MAX_FRONTIER_CLOSURE_MICROBATCH == 16
    plan = frontier_promotion_plan(("lucas_theorem",))
    pending = {row.name: row.alpha_index for row in plan.pending_rows}
    assert all(name in pending for name in local)
    ordered = LUCAS_PRIME_DIVIDES_MAXIMAL_SHARED_ROWS + (target,)
    assert tuple(pending[name] for name in ordered) == tuple(
        sorted(pending[name] for name in ordered)
    )

    repository = Path(__file__).resolve().parents[3]
    catalog = json.loads(
        (
            repository / "artifacts/peano-library/alpha/catalog-v13.json"
        ).read_text(encoding="utf-8")
    )
    by_name = {row["name"]: row for row in catalog["theorems"]}
    external = {
        dependency
        for name in local
        for dependency in by_name[name]["dependencies"]
        if dependency not in local
    }
    stable = {
        name for name in external if by_name[name]["evidence_status"] == "stable_closed"
    }
    unchecked = {
        name for name in external if by_name[name]["evidence_status"] == "body_checked"
    }
    assert len(external) == 32
    assert len(stable) == LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_COUNT == 29
    assert unchecked == {
        name
        for name, _nodes in LUCAS_PRIME_DIVIDES_OBSERVED_UNCHECKED_LEAF_PROOF_NODES
    }
    assert sum(
        by_name[name]["empty_context_closure"]["proof_nodes"]
        for name in stable
    ) == LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_PROOF_NODES == 76_923
    assert by_name["factorial_exists"]["empty_context_closure"]["proof_nodes"] == 59_841
    assert sum(
        nodes
        for _name, nodes in LUCAS_PRIME_DIVIDES_OBSERVED_UNCHECKED_LEAF_PROOF_NODES
    ) == 89_900
    assert LUCAS_PRIME_DIVIDES_SHARED_LEAF_NODE_LOWER_BOUND == 166_823
    assert (
        LUCAS_PRIME_DIVIDES_SHARED_LEAF_NODE_LOWER_BOUND
        - MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    ) == 41_823


def test_shared_layer_compiler_produces_an_actual_empty_context_certificate() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    diagonal = construct_frontier_closed_candidate(
        "beta_pascal_table_diagonal_boundary", plan=plan
    )
    result = construct_frontier_shared_closed_candidate(
        "choose_self_of_eq",
        shared_rows=("choose_self",),
        prerequisites={diagonal.name: diagonal.certificate},
        plan=plan,
    )
    assert result.name == "choose_self_of_eq"
    assert result.diagnostics.proof_nodes == 2_255
    assert result.diagnostics.proof_objects == 1_728
    assert result.diagnostics.proof_nodes < MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert result.diagnostics.proof_objects < MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    assert not v13.ALPHA_EDITION.by_name[result.name].checked_use


def test_shared_layer_rejects_missing_duplicate_and_reordered_body_rows() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    with pytest.raises(FrontierPromotionError, match="repeats"):
        construct_frontier_shared_closed_candidate(
            "choose_self", shared_rows=("choose_self",), plan=plan
        )
    with pytest.raises(FrontierPromotionError, match="nonpending"):
        construct_frontier_shared_closed_candidate(
            "choose_self", shared_rows=("zero_add",), plan=plan
        )
    with pytest.raises(FrontierPromotionError, match="dependency ordered"):
        construct_frontier_shared_closed_candidate(
            "choose_self", shared_rows=("choose_self_of_eq",), plan=plan
        )
    with pytest.raises(FrontierPromotionError, match="missing independently closed"):
        construct_frontier_shared_closed_candidate(
            "choose_self_of_eq", shared_rows=("choose_self",), plan=plan
        )


def test_microbatch_rejects_missing_rows_duplicates_and_bad_order() -> None:
    plan = frontier_promotion_plan(("lucas_theorem",))
    with pytest.raises(FrontierPromotionError, match="cannot be empty"):
        construct_frontier_closed_microbatch((), plan=plan)
    with pytest.raises(FrontierPromotionError, match="exceeds 16"):
        construct_frontier_closed_microbatch(
            tuple(row.name for row in plan.pending_rows[: MAX_FRONTIER_CLOSURE_MICROBATCH + 1]),
            plan=plan,
        )
    with pytest.raises(FrontierPromotionError, match="duplicate"):
        construct_frontier_closed_microbatch(
            ("factorial_length_eq_transport", "factorial_length_eq_transport"),
            plan=plan,
        )
    with pytest.raises(FrontierPromotionError, match="dependency order"):
        construct_frontier_closed_microbatch(
            ("factorial_length_eq_transport", "le_mul_of_one_le_right"),
            plan=plan,
        )
    with pytest.raises(FrontierPromotionError, match="nonpending"):
        construct_frontier_closed_microbatch(("zero_add",), plan=plan)


@pytest.mark.parametrize(
    ("limit", "message"),
    (
        ("MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES", "resource envelope|proof-node"),
        ("MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS", "resource envelope|proof-object"),
    ),
)
def test_constructor_enforces_immutable_local_resource_budgets(
    monkeypatch: pytest.MonkeyPatch, limit: str, message: str
) -> None:
    monkeypatch.setattr(promotion, limit, 10)
    with pytest.raises(FrontierPromotionError, match=message):
        construct_frontier_closed_microbatch(
            ("factorial_length_eq_transport",),
            plan=frontier_promotion_plan(("lucas_theorem",)),
        )


def test_genuine_cold_process_checks_an_actual_closed_certificate() -> None:
    receipts = cold_frontier_microbatch_receipts(
        ("factorial_length_eq_transport",),
        roots=("lucas_theorem",),
    )
    assert len(receipts) == 1
    assert receipts[0].name == "factorial_length_eq_transport"
    assert receipts[0].proof_nodes == 26
    assert not v13.ALPHA_EDITION.by_name[receipts[0].name].checked_use


def test_cold_process_rejects_bad_timeout_empty_rows_and_unknown_targets() -> None:
    with pytest.raises(FrontierPromotionError, match="positive integer"):
        cold_frontier_microbatch_receipts(("factorial_length_eq_transport",), timeout_seconds=0)
    with pytest.raises(FrontierPromotionError, match="nonempty sequence"):
        cold_frontier_microbatch_receipts(())
    with pytest.raises(FrontierPromotionError, match="rejected"):
        cold_frontier_microbatch_receipts(
            ("unknown_frontier_theorem",), roots=("lucas_theorem",)
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("statement", "unsealed theorem statement"),
        ("empty", "empty proof receipt"),
        ("node_budget", "proof-node budget"),
        ("object_budget", "proof-object budget"),
    ),
)
def test_cold_worker_receipt_mutations_fail_closed(
    monkeypatch: pytest.MonkeyPatch, mutation: str, message: str
) -> None:
    name = "factorial_length_eq_transport"
    row = next(
        item
        for item in frontier_promotion_plan(("lucas_theorem",)).pending_rows
        if item.name == name
    )
    receipt = {
        "name": name,
        "statement_sha256": row.statement_sha256,
        "proof_nodes": 26,
        "proof_objects": 26,
        "proof_depth": 14,
        "annotation_occurrences": 760,
        "proof_envelope_depth": 38,
    }
    if mutation == "statement":
        receipt["statement_sha256"] = "0" * 64
    if mutation == "empty":
        receipt["proof_nodes"] = 0
    if mutation == "node_budget":
        receipt["proof_nodes"] = MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES + 1
    if mutation == "object_budget":
        receipt["proof_objects"] = MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS + 1
    payload = {
        "schema": promotion.FRONTIER_COLD_CHECK_SCHEMA,
        "alpha_identity_sha256": v13.ALPHA_V13_IDENTITY_SHA256,
        "roots": ["lucas_theorem"],
        "receipts": [receipt],
    }
    monkeypatch.setattr(
        promotion.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=json.dumps(payload), stderr=""
        ),
    )
    with pytest.raises(FrontierPromotionError, match=message):
        cold_frontier_microbatch_receipts((name,), roots=("lucas_theorem",))
