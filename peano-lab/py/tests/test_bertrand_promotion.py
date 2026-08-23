"""Fail-closed, bounded release planning for the complete Bertrand graph."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

import pytest

from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import DNE, EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v12 as v12
from peano_lab.library import bertrand_promotion as promotion_module
from peano_lab.library.bertrand_promotion import (
    BERTRAND_BOUNDED_VALUATION_DEFERRED,
    BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES,
    BERTRAND_BOUNDED_VALUATION_WINDOW,
    BERTRAND_PROMOTION_ROOTS,
    MAX_BERTRAND_CLOSURE_MICROBATCH,
    MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    BertrandPromotionError,
    BertrandPromotionPlan,
    bertrand_bounded_valuation_microbatch_plan,
    bertrand_promotion_plan,
    check_bertrand_promotion_batch,
    check_bertrand_promotion_certificate,
    construct_bertrand_closed_candidate,
    construct_bertrand_closed_microbatch,
)
from peano_lab.library.theorems import replay


def test_strict_bertrand_promotion_slice_is_exact_and_dependency_closed() -> None:
    plan = bertrand_promotion_plan()
    assert type(plan) is BertrandPromotionPlan
    assert plan.roots == BERTRAND_PROMOTION_ROOTS
    assert len(plan.rows) == 544
    assert len(plan.stable_rows) == 202
    assert len(plan.alpha_closed_rows) == 1
    assert len(plan.pending_rows) == 341
    assert plan.dependency_edge_count == 1_917
    assert plan.ordered_names_sha256 == (
        "d0e90fb101f10684d792d9ba8a32ba2abc78a033bf18ea4c958f14a68cdd469e"
    )
    assert plan.exact_surface_sha256 == (
        "e4583c4630b6342cc00095bee19e109bb7cd8064b699f069b0d9eb51e61d7206"
    )
    assert plan.parent_alpha_enrollment_sha256 == v12.ALPHA_V12_ENROLLMENT_SHA256
    assert plan.parent_alpha_identity_sha256 == v12.ALPHA_V12_IDENTITY_SHA256
    assert tuple(row.alpha_index for row in plan.rows) == tuple(
        sorted(row.alpha_index for row in plan.rows)
    )
    assert tuple(row.name for row in plan.rows[-3:]) == (
        "bertrand_closed_upper",
        "bertrand_upper_endpoint_factorization",
        "bertrand_strict",
    )

    observed: set[str] = set()
    for row in plan.rows:
        assert set(row.dependencies) <= observed
        observed.add(row.name)


def test_closed_upper_slice_is_smaller_and_exact() -> None:
    plan = bertrand_promotion_plan(("bertrand_closed_upper",))
    assert len(plan.rows) == 542
    assert len(plan.stable_rows) == 202
    assert len(plan.alpha_closed_rows) == 1
    assert len(plan.pending_rows) == 339
    assert plan.dependency_edge_count == 1_909
    assert plan.ordered_names_sha256 == (
        "e1d5a915a7512f5da651604c862505ae95bb8415ead4c51a2373dd58f5366e6b"
    )
    assert plan.exact_surface_sha256 == (
        "2b209f904b24195886390074725502bae7341c6bde97f745d1cbb96285023ffa"
    )
    assert plan.rows[-1].name == "bertrand_closed_upper"
    assert "bertrand_strict" not in {row.name for row in plan.rows}


def test_selected_roots_are_canonical_and_duplicate_roots_fail_closed() -> None:
    assert bertrand_promotion_plan(tuple(reversed(BERTRAND_PROMOTION_ROOTS))) == (
        bertrand_promotion_plan()
    )
    assert bertrand_promotion_plan(("bertrand_strict",)).rows == (
        bertrand_promotion_plan().rows
    )
    with pytest.raises(BertrandPromotionError, match="duplicate"):
        bertrand_promotion_plan(("bertrand_strict", "bertrand_strict"))


@pytest.mark.parametrize(
    ("roots", "message"),
    (
        ((), "at least one"),
        ("bertrand_strict", "tuple or list"),
        ((1,), "exact strings"),
        (("quadratic_reciprocity_combined",), "unsupported"),
        (("prime_unbounded",), "unsupported"),
    ),
)
def test_invalid_promotion_root_is_rejected(roots, message: str) -> None:
    with pytest.raises(BertrandPromotionError, match=message):
        bertrand_promotion_plan(roots)


def test_release_slice_exposes_cross_campaign_qr_dependencies_honestly() -> None:
    plan = bertrand_promotion_plan()
    assert Counter(row.enrollment_origin for row in plan.rows)["qr"] == 8
    assert {
        row.name
        for row in plan.pending_rows
        if row.enrollment_origin == "qr"
    } == {
        "beta_product_pointwise_coprime",
        "beta_sum_transport_prefix",
        "eisenstein_initial_segment_prefix_all_bits",
        "eisenstein_initial_segment_decoded_choice",
        "beta_all_one_bit_count_exact",
        "eisenstein_initial_segment_bit_count_functional",
        "eisenstein_initial_segment_bit_count_exact",
        "beta_sum_pointwise_add",
    }
    assert all(row.evidence != "pending_layered_closure" for row in plan.rows)


def test_planning_never_changes_evidence_or_sealed_edition_membership() -> None:
    before = (
        v12.ALPHA_V12_ENROLLMENT_SHA256,
        v12.ALPHA_V12_IDENTITY_SHA256,
        v12.STABLE_EDITION.identity_sha256,
        len(v12.ALPHA_CHECKED_SPECS),
    )
    plan = bertrand_promotion_plan()
    assert before == (
        v12.ALPHA_V12_ENROLLMENT_SHA256,
        v12.ALPHA_V12_IDENTITY_SHA256,
        v12.STABLE_EDITION.identity_sha256,
        len(v12.ALPHA_CHECKED_SPECS),
    )
    assert before[-1] == 570
    assert all(not v12.ALPHA_EDITION.by_name[row.name].checked_use for row in plan.pending_rows)


def test_fresh_kernel_check_accepts_an_actual_closed_ancestor() -> None:
    plan = bertrand_promotion_plan()
    theorem = replay("zero_add")
    receipt = check_bertrand_promotion_certificate(
        "zero_add", theorem.certificate, plan=plan
    )
    assert receipt.name == "zero_add"
    assert receipt.proof_nodes > 0
    assert receipt.proof_objects > 0
    assert receipt.proof_depth > 0
    assert receipt.statement_sha256 == next(
        row.statement_sha256 for row in plan.rows if row.name == "zero_add"
    )


def test_wrong_certificate_and_classical_dne_are_rejected() -> None:
    plan = bertrand_promotion_plan()
    with pytest.raises(BertrandPromotionError, match="kernel rejected"):
        check_bertrand_promotion_certificate(
            "zero_add", EqRefl(Zero()), plan=plan
        )
    with pytest.raises(BertrandPromotionError, match="classical DNE"):
        check_bertrand_promotion_certificate(
            "zero_add", DNE(Eq(Zero(), Zero())), plan=plan
        )


def test_unknown_theorem_invalid_plan_and_nonproof_are_rejected() -> None:
    plan = bertrand_promotion_plan()
    with pytest.raises(BertrandPromotionError, match="outside the promotion slice"):
        check_bertrand_promotion_certificate(
            "quadratic_reciprocity_combined", EqRefl(Zero()), plan=plan
        )
    with pytest.raises(BertrandPromotionError, match="invalid type"):
        check_bertrand_promotion_certificate(
            "zero_add", EqRefl(Zero()), plan=object()
        )
    with pytest.raises(BertrandPromotionError, match="must be a kernel proof"):
        check_bertrand_promotion_certificate("zero_add", object(), plan=plan)


def test_batch_requires_every_pending_dependency_before_checking_any_proof() -> None:
    plan = bertrand_promotion_plan()
    with pytest.raises(BertrandPromotionError, match="missing 341"):
        check_bertrand_promotion_batch({}, plan=plan)
    with pytest.raises(BertrandPromotionError, match="missing 340"):
        check_bertrand_promotion_batch(
            {plan.pending_rows[0].name: EqRefl(Zero())}, plan=plan
        )


def test_batch_rejects_unexpected_rows_and_forged_candidate_certificates() -> None:
    plan = bertrand_promotion_plan()
    certificates = {row.name: EqRefl(Zero()) for row in plan.pending_rows}
    certificates["zero_add"] = replay("zero_add").certificate
    with pytest.raises(BertrandPromotionError, match="unexpected promotion"):
        check_bertrand_promotion_batch(certificates, plan=plan)

    certificates.pop("zero_add")
    with pytest.raises(BertrandPromotionError, match="kernel rejected"):
        check_bertrand_promotion_batch(certificates, plan=plan)


def test_tampered_target_is_rejected_even_when_name_and_metadata_are_unchanged() -> None:
    plan = bertrand_promotion_plan()
    zero_add = next(row for row in plan.rows if row.name == "zero_add")
    mutated = replace(
        plan,
        rows=tuple(
            replace(row, statement="0 = 0") if row is zero_add else row
            for row in plan.rows
        ),
    )
    with pytest.raises(BertrandPromotionError, match="sealed Alpha-v12 slice"):
        check_bertrand_promotion_certificate(
            "zero_add", replay("zero_add").certificate, plan=mutated
        )


def test_tampered_plan_cannot_authorize_an_otherwise_valid_false_target() -> None:
    plan = bertrand_promotion_plan()
    mutated = replace(
        plan,
        rows=tuple(
            replace(row, statement="0 = 0") if row.name == "zero_add" else row
            for row in plan.rows
        ),
    )
    with pytest.raises(BertrandPromotionError, match="sealed Alpha-v12 slice"):
        check_bertrand_promotion_certificate(
            "zero_add", EqRefl(Zero()), plan=mutated
        )


def test_tampered_parent_identity_and_missing_dependencies_fail_closed() -> None:
    plan = bertrand_promotion_plan()
    for mutated in (
        replace(plan, parent_alpha_identity_sha256="0" * 64),
        replace(plan, rows=plan.rows[1:]),
        replace(plan, dependency_edge_count=plan.dependency_edge_count - 1),
    ):
        with pytest.raises(BertrandPromotionError, match="sealed Alpha-v12 slice"):
            check_bertrand_promotion_batch({}, plan=mutated)


@pytest.mark.parametrize(
    "name",
    (
        "beta_sum_transport_prefix",
        "eisenstein_initial_segment_prefix_all_bits",
    ),
)
def test_body_only_zero_dependency_candidate_gains_an_actual_closed_proof(
    name: str,
) -> None:
    plan = bertrand_promotion_plan()
    before = len(v12.ALPHA_CHECKED_SPECS)
    candidate = construct_bertrand_closed_candidate(name, plan=plan)
    assert candidate.name == name
    assert candidate.diagnostics.name == name
    assert candidate.diagnostics.proof_nodes > 0
    assert candidate.diagnostics.proof_objects > 0
    assert not v12.ALPHA_EDITION.by_name[name].checked_use
    assert len(v12.ALPHA_CHECKED_SPECS) == before == 570


def test_constructor_closes_a_candidate_from_existing_stable_dependencies() -> None:
    candidate = construct_bertrand_closed_candidate("le_mul_of_one_le_right")
    assert candidate.name == "le_mul_of_one_le_right"
    assert candidate.diagnostics.proof_nodes > 0
    assert not v12.ALPHA_EDITION.by_name[candidate.name].checked_use


def test_constructor_requires_actual_closed_body_only_prerequisites() -> None:
    with pytest.raises(BertrandPromotionError, match="missing independently closed"):
        construct_bertrand_closed_candidate("bounded_prime_interval_search")
    with pytest.raises(BertrandPromotionError, match="unexpected candidate"):
        construct_bertrand_closed_candidate(
            "beta_sum_transport_prefix",
            prerequisites={"zero_add": replay("zero_add").certificate},
        )
    with pytest.raises(BertrandPromotionError, match="already has closed evidence"):
        construct_bertrand_closed_candidate("zero_add")


def test_all_eight_cross_campaign_qr_rows_close_in_one_bounded_microbatch() -> None:
    plan = bertrand_promotion_plan()
    names = tuple(row.name for row in plan.pending_rows[:8])
    closed = construct_bertrand_closed_microbatch(names, plan=plan)
    assert tuple((row.name, row.diagnostics.proof_nodes) for row in closed) == (
        ("beta_product_pointwise_coprime", 6_748),
        ("beta_sum_transport_prefix", 59),
        ("eisenstein_initial_segment_prefix_all_bits", 25),
        ("eisenstein_initial_segment_decoded_choice", 1_162),
        ("beta_all_one_bit_count_exact", 5_172),
        ("eisenstein_initial_segment_bit_count_functional", 10_582),
        ("eisenstein_initial_segment_bit_count_exact", 41_170),
        ("beta_sum_pointwise_add", 2_794),
    )
    assert all(
        not v12.ALPHA_EDITION.by_name[row.name].checked_use for row in closed
    )
    assert sum(row.diagnostics.proof_nodes for row in closed) <= (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert sum(row.diagnostics.proof_objects for row in closed) <= (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS
    )
    assert len(v12.ALPHA_CHECKED_SPECS) == 570


def test_initial_bertrand_interval_and_power_rows_close_independently() -> None:
    plan = bertrand_promotion_plan()
    names = tuple(row.name for row in plan.pending_rows[8:16])
    closed = construct_bertrand_closed_microbatch(names, plan=plan)
    assert tuple((row.name, row.diagnostics.proof_nodes) for row in closed) == (
        ("prime_strictly_above_decidable", 2_492),
        ("bounded_prime_interval_search", 2_844),
        ("mul_le_mul", 521),
        ("le_mul_of_one_le_right", 141),
        ("le_mul_of_one_le_left", 383),
        ("pow_base_monotone", 4_401),
        ("one_le_pow", 4_049),
        ("pow_nonzero_of_one_le", 4_091),
    )
    assert all(
        not v12.ALPHA_EDITION.by_name[row.name].checked_use for row in closed
    )


def test_bounded_valuation_schedule_exposes_only_dependency_safe_rows() -> None:
    plan = bertrand_promotion_plan()
    assert tuple(row.name for row in plan.pending_rows[16:24]) == (
        BERTRAND_BOUNDED_VALUATION_WINDOW
    )
    assert BERTRAND_BOUNDED_VALUATION_DEFERRED == (
        "bounded_power_valuation_exists",
        "power_valuation_exists",
    )
    assert bertrand_bounded_valuation_microbatch_plan(plan=plan) == (
        ("power_divides_decidable",),
        ("power_divides_zero",),
        ("bounded_power_valuation_search",),
        (
            "power_valuation_functional",
            "power_valuation_power_divides",
            "power_valuation_dominates",
        ),
    ) == BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES

    # Rows 21--23 do not depend, directly or transitively through pending
    # premises, on the two explicitly deferred valuation-existence rows.
    for name in BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES[-1]:
        assert not {
            dependency
            for dependency in v12.ALPHA_EDITION.by_name[name].spec.dependencies
            if not v12.ALPHA_EDITION.by_name[dependency].checked_use
        }


def test_six_additional_valuation_rows_close_in_four_hard_bounded_batches() -> None:
    plan = bertrand_promotion_plan()
    before = (
        v12.ALPHA_V12_ENROLLMENT_SHA256,
        v12.ALPHA_V12_IDENTITY_SHA256,
        v12.STABLE_EDITION.identity_sha256,
        len(v12.ALPHA_CHECKED_SPECS),
    )
    certificates = {}
    batches = []
    for names in bertrand_bounded_valuation_microbatch_plan(plan=plan):
        closed = construct_bertrand_closed_microbatch(
            names,
            prerequisites=certificates,
            plan=plan,
        )
        assert len(closed) <= MAX_BERTRAND_CLOSURE_MICROBATCH
        assert sum(row.diagnostics.proof_nodes for row in closed) <= (
            MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
        )
        assert sum(row.diagnostics.proof_objects for row in closed) <= (
            MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS
        )
        certificates.update((row.name, row.certificate) for row in closed)
        batches.append(
            tuple((row.name, row.diagnostics.proof_nodes) for row in closed)
        )

    assert tuple(batches) == (
        (("power_divides_decidable", 63_931),),
        (("power_divides_zero", 61_118),),
        (("bounded_power_valuation_search", 64_301),),
        (
            ("power_valuation_functional", 252),
            ("power_valuation_power_divides", 21),
            ("power_valuation_dominates", 24),
        ),
    )

    # Combining the first two rows would exceed the aggregate cap by 49
    # nodes. The existence row requires the independently closed search and
    # zero-power premises, which already total 125,419 nodes before its own
    # body or remaining stable premise. Its successor inherits the blocker.
    assert batches[0][0][1] + batches[1][0][1] == 125_049
    assert batches[0][0][1] + batches[1][0][1] > (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert batches[2][0][1] + batches[1][0][1] == 125_419
    assert batches[2][0][1] + batches[1][0][1] > (
        MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert set(BERTRAND_BOUNDED_VALUATION_DEFERRED).isdisjoint(certificates)
    assert all(
        not v12.ALPHA_EDITION.by_name[name].checked_use for name in certificates
    )
    assert before == (
        v12.ALPHA_V12_ENROLLMENT_SHA256,
        v12.ALPHA_V12_IDENTITY_SHA256,
        v12.STABLE_EDITION.identity_sha256,
        len(v12.ALPHA_CHECKED_SPECS),
    )


def test_bounded_valuation_schedule_rejects_deferred_row_in_safe_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        promotion_module,
        "BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES",
        BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES
        + (("bounded_power_valuation_exists",),),
    )
    with pytest.raises(BertrandPromotionError, match="includes a deferred row"):
        bertrand_bounded_valuation_microbatch_plan()


def test_closure_microbatch_rejects_unsafe_or_non_topological_batches() -> None:
    plan = bertrand_promotion_plan()
    pending = tuple(row.name for row in plan.pending_rows)
    with pytest.raises(BertrandPromotionError, match="cannot be empty"):
        construct_bertrand_closed_microbatch((), plan=plan)
    with pytest.raises(BertrandPromotionError, match="exceeds 16"):
        construct_bertrand_closed_microbatch(
            pending[: MAX_BERTRAND_CLOSURE_MICROBATCH + 1], plan=plan
        )
    with pytest.raises(BertrandPromotionError, match="duplicate"):
        construct_bertrand_closed_microbatch((pending[0], pending[0]), plan=plan)
    with pytest.raises(BertrandPromotionError, match="dependency order"):
        construct_bertrand_closed_microbatch((pending[1], pending[0]), plan=plan)
    with pytest.raises(BertrandPromotionError, match="nonpending"):
        construct_bertrand_closed_microbatch(("zero_add",), plan=plan)
    with pytest.raises(BertrandPromotionError, match="missing independently closed"):
        construct_bertrand_closed_microbatch(
            ("bounded_prime_interval_search",), plan=plan
        )


@pytest.mark.parametrize(
    ("limit_name", "message"),
    (
        ("MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES", "proof-node budget"),
        ("MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS", "proof-object budget"),
    ),
)
def test_closure_microbatch_rejects_cumulative_resource_overflow(
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    message: str,
) -> None:
    monkeypatch.setattr(promotion_module, limit_name, 10)
    with pytest.raises(BertrandPromotionError, match=message):
        construct_bertrand_closed_microbatch(("beta_sum_transport_prefix",))
