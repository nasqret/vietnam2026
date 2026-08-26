"""Bounded, fail-closed promotion planning for the exact Lagrange slice."""

from __future__ import annotations

from dataclasses import replace

import pytest

from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v13 as v13
from peano_lab.library import four_square_frontier_promotion as promotion
from peano_lab.library.four_square_frontier_promotion import (
    FOUR_SQUARE_BETA_PARENT_CHECKED_DIAGNOSTICS,
    FOUR_SQUARE_BETA_PARENT_NAMES,
    FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS,
    FOUR_SQUARE_BETA_PARENT_STATEMENT_SHA256,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_NODE_UPPER_BOUND,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_OBJECT_UPPER_BOUND,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_DIAGNOSTICS,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_PREREQUISITE_DIAGNOSTICS,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_NODE_UPPER_BOUND,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_OBJECT_UPPER_BOUND,
    FOUR_SQUARE_CAMPAIGN_CONTINUATION_READY_COUNT,
    FOUR_SQUARE_CAMPAIGN_NEXT_READY_COUNT,
    FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_DIAGNOSTICS,
    FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_PREREQUISITE_DIAGNOSTICS,
    FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_NODE_UPPER_BOUND,
    FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_OBJECT_UPPER_BOUND,
    FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES,
    FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_PREREQUISITES,
    FOUR_SQUARE_ESTABLISHED_PARENT_DIAGNOSTICS,
    FOUR_SQUARE_ESTABLISHED_PARENT_NAMES,
    FOUR_SQUARE_FRONTIER_EXACT_SURFACE_SHA256,
    FOUR_SQUARE_FRONTIER_ORDERED_NAMES_SHA256,
    FOUR_SQUARE_INITIAL_CAMPAIGN_BATCH_LEAF_BUDGETS,
    FOUR_SQUARE_INITIAL_CAMPAIGN_CHECKED_BATCH_DIAGNOSTICS,
    FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS,
    FOUR_SQUARE_INITIAL_CAMPAIGN_READY_COUNT,
    FOUR_SQUARE_NON_BETA_MICROBATCH_DIAGNOSTICS,
    FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH,
    FOUR_SQUARE_NON_BETA_PARENT_NAMES,
    construct_four_square_beta_parent_certificates,
    construct_four_square_campaign_microbatch,
    construct_four_square_continuation_campaign_microbatch,
    construct_four_square_initial_campaign_certificates,
    construct_four_square_parent_microbatch,
    construct_four_square_shared_closed_candidate,
    four_square_frontier_plan,
    four_square_hypothetical_ready_rows,
    four_square_initial_campaign_batches,
)
from peano_lab.library.frontier_promotion import FrontierPromotionError


def test_exact_four_square_slice_is_sealed_dependency_closed_and_evidence_honest() -> None:
    plan = four_square_frontier_plan()

    assert plan.source.roots == ("four_square_lagrange",)
    assert len(plan.source.rows) == 390
    assert len(plan.source.stable_rows) == 166
    assert len(plan.source.alpha_closed_rows) == 5
    assert len(plan.obligations) == 219
    assert len(plan.parent_obligations) == 23
    assert len(plan.campaign_obligations) == 196
    assert plan.source.dependency_edge_count == 1_187
    assert plan.source.ordered_names_sha256 == (
        FOUR_SQUARE_FRONTIER_ORDERED_NAMES_SHA256
    )
    assert plan.source.exact_surface_sha256 == (
        FOUR_SQUARE_FRONTIER_EXACT_SURFACE_SHA256
    )
    assert plan.source.parent_alpha_identity_sha256 == v13.ALPHA_V13_IDENTITY_SHA256
    assert len(v13.ALPHA_CHECKED_SPECS) == 570
    assert not v13.ALPHA_EDITION.by_name["four_square_lagrange"].checked_use


def test_four_square_pending_parent_and_campaign_layers_are_exact() -> None:
    plan = four_square_frontier_plan()

    assert tuple(len(layer) for layer in plan.layers) == (
        69, 43, 25, 19, 12, 9, 6, 5, 12, 11, 3, 2, 1, 1, 1
    )
    assert tuple(len(layer) for layer in plan.parent_layers) == (17, 5, 1)
    assert len(plan.ready_parent_names) == 17
    assert len(plan.ready_campaign_names) == 52
    assert set(plan.layers[0]) == (
        set(plan.ready_parent_names) | set(plan.ready_campaign_names)
    )
    assert all(item.source_release == "v12" for item in plan.parent_obligations)
    assert all(item.source_release == "v13" for item in plan.campaign_obligations)
    assert all(
        item.name in plan.layers[item.pending_layer]
        for item in plan.obligations
    )


def test_all_initial_campaign_rows_have_exact_bounded_independent_partitions() -> None:
    plan = four_square_frontier_plan()
    batches = four_square_initial_campaign_batches()
    names = tuple(name for batch in batches for name in batch.names)

    assert FOUR_SQUARE_INITIAL_CAMPAIGN_READY_COUNT == 52
    assert len(FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS) == 52
    assert len(batches) == 4
    assert tuple(
        (len(batch.names), batch.direct_leaf_proof_nodes, batch.direct_leaf_proof_objects)
        for batch in batches
    ) == FOUR_SQUARE_INITIAL_CAMPAIGN_BATCH_LEAF_BUDGETS == (
        (16, 733, 684),
        (16, 3_847, 3_310),
        (16, 9_420, 7_181),
        (4, 76_729, 14_610),
    )
    assert len(names) == len(set(names)) == 52
    assert set(names) == set(plan.ready_campaign_names)
    positions = {row.name: row.alpha_index for row in plan.source.unchecked_frontier_rows}
    for batch in batches:
        assert tuple(positions[name] for name in batch.names) == tuple(
            sorted(positions[name] for name in batch.names)
        )
        assert batch.direct_leaf_proof_nodes < (
            promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        )
        assert batch.direct_leaf_proof_objects < (
            promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        )


def test_fifty_two_actual_campaign_certificates_respect_separate_batch_envelopes() -> None:
    observed = FOUR_SQUARE_INITIAL_CAMPAIGN_CHECKED_BATCH_DIAGNOSTICS
    batches = four_square_initial_campaign_batches()

    assert observed == (
        (16, 1_232, 1_125),
        (16, 4_552, 3_664),
        (16, 10_261, 5_964),
        (4, 77_161, 12_811),
    )
    assert sum(count for count, _nodes, _objects in observed) == 52
    assert max(nodes for _count, nodes, _objects in observed) == 77_161
    assert max(objects for _count, _nodes, objects in observed) == 12_811
    assert all(
        count <= promotion.MAX_FRONTIER_CLOSURE_MICROBATCH
        and nodes < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        and objects < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        for count, nodes, objects in observed
    )
    assert all(
        not v13.ALPHA_EDITION.by_name[name].checked_use
        for batch in batches
        for name in batch.names
    )
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


def test_all_closed_parents_and_first_layer_unlock_exactly_forty_one_campaign_rows() -> None:
    plan = four_square_frontier_plan()
    closed = (
        *FOUR_SQUARE_NON_BETA_PARENT_NAMES,
        *FOUR_SQUARE_BETA_PARENT_NAMES,
        *plan.ready_campaign_names,
    )
    ready = four_square_hypothetical_ready_rows(closed)

    assert FOUR_SQUARE_CAMPAIGN_NEXT_READY_COUNT == len(ready) == 41
    assert set(ready) <= {item.name for item in plan.campaign_obligations}
    assert "four_square_square_residue_prefix_exists" in ready
    assert "four_square_prime_from_bounded_strict_descent_and_seed" in ready
    assert "quaternion_coordinate_absolute_total" in ready
    assert not v13.ALPHA_EDITION.by_name["four_square_lagrange"].checked_use


def test_sixteen_actual_second_layer_campaign_proofs_have_actual_closed_premises() -> None:
    plan = four_square_frontier_plan()
    observed = FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_DIAGNOSTICS
    initial = set(plan.ready_campaign_names)
    parents = {item.name for item in plan.parent_obligations}

    assert FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_PREREQUISITE_DIAGNOSTICS == (
        10,
        2_973,
        2_114,
    )
    assert len(FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_PREREQUISITES) == 10
    assert set(FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_PREREQUISITES) <= (
        initial | parents
    )
    assert tuple(name for name, _nodes, _objects in observed) == (
        FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES
    )
    assert len(observed) == 16
    assert sum(nodes for _name, nodes, _objects in observed) == 10_229
    assert sum(objects for _name, _nodes, objects in observed) == 6_322
    assert FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_NODE_UPPER_BOUND == 18_284
    assert FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_DIRECT_OBJECT_UPPER_BOUND == 15_428
    assert 10_229 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 6_322 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    closed_campaign = initial | set(FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES)
    assert len(closed_campaign) == 68
    assert len(closed_campaign | parents) == 91
    assert all(
        not v13.ALPHA_EDITION.by_name[name].checked_use for name in closed_campaign
    )
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


def test_sixty_eight_closed_campaign_rows_unlock_exactly_thirty_four_more() -> None:
    plan = four_square_frontier_plan()
    closed = (
        *FOUR_SQUARE_NON_BETA_PARENT_NAMES,
        *FOUR_SQUARE_BETA_PARENT_NAMES,
        *plan.ready_campaign_names,
        *FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES,
    )
    ready = four_square_hypothetical_ready_rows(closed)

    assert len(ready) == FOUR_SQUARE_CAMPAIGN_CONTINUATION_READY_COUNT == 34
    assert set(FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES) <= set(ready)
    assert not v13.ALPHA_EDITION.by_name["four_square_lagrange"].checked_use


def test_continuation_precursor_and_target_batches_are_exactly_dependency_closed() -> None:
    plan = four_square_frontier_plan()
    obligations = {item.name: item for item in plan.obligations}
    positions = {row.name: row.alpha_index for row in plan.source.pending_rows}
    precursors = set(FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES)
    targets = set(FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES)

    assert len(precursors) == 16
    assert len(targets) == 12
    assert not precursors.intersection(targets)
    assert sum(name in {item.name for item in plan.parent_obligations} for name in precursors) == 6
    assert tuple(positions[name] for name in FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES) == tuple(
        sorted(positions[name] for name in FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITES)
    )
    assert tuple(positions[name] for name in FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES) == tuple(
        sorted(positions[name] for name in FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES)
    )
    assert all(
        set(obligations[name].pending_dependencies) <= precursors
        for name in precursors | targets
    )
    assert FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_NODE_UPPER_BOUND == 18_867
    assert FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_OBJECT_UPPER_BOUND == 13_801
    assert FOUR_SQUARE_CAMPAIGN_CONTINUATION_NODE_UPPER_BOUND == 21_029
    assert FOUR_SQUARE_CAMPAIGN_CONTINUATION_OBJECT_UPPER_BOUND == 15_823
    assert 18_867 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 21_029 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 13_801 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    assert 15_823 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS


def test_twelve_actual_continuation_proofs_advance_campaign_to_eighty() -> None:
    plan = four_square_frontier_plan()
    observed = FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_DIAGNOSTICS

    assert FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_PREREQUISITE_DIAGNOSTICS == (
        16,
        11_374,
        7_149,
    )
    assert tuple(name for name, _nodes, _objects in observed) == (
        FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES
    )
    assert len(observed) == 12
    assert sum(nodes for _name, nodes, _objects in observed) == 14_263
    assert sum(objects for _name, _nodes, objects in observed) == 7_471
    assert 14_263 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 7_471 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    closed_campaign = (
        set(plan.ready_campaign_names)
        | set(FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES)
        | set(FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES)
    )
    parents = {item.name for item in plan.parent_obligations}
    assert len(closed_campaign) == 80
    assert len(closed_campaign | parents) == 103
    assert all(
        not v13.ALPHA_EDITION.by_name[name].checked_use for name in closed_campaign
    )
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


@pytest.mark.parametrize(
    ("name", "limit"),
    (
        (
            "FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_NODE_UPPER_BOUND",
            "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES",
        ),
        (
            "FOUR_SQUARE_CAMPAIGN_CONTINUATION_PREREQUISITE_OBJECT_UPPER_BOUND",
            "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS",
        ),
        (
            "FOUR_SQUARE_CAMPAIGN_CONTINUATION_NODE_UPPER_BOUND",
            "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES",
        ),
        (
            "FOUR_SQUARE_CAMPAIGN_CONTINUATION_OBJECT_UPPER_BOUND",
            "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS",
        ),
    ),
)
def test_continuation_rejects_every_oversized_envelope_before_replay(
    monkeypatch: pytest.MonkeyPatch, name: str, limit: str
) -> None:
    monkeypatch.setattr(promotion, name, getattr(promotion, limit))

    with pytest.raises(FrontierPromotionError, match="immutable cap"):
        construct_four_square_continuation_campaign_microbatch()


@pytest.mark.parametrize(
    ("names", "message"),
    (
        ((), "cannot be empty"),
        ("four_square_branch_nonzero_even_half", "tuple or list"),
        ((1,), "exact strings"),
        (("four_square_branch_nonzero_even_half",) * 17, "16-row"),
        (("bounded_nonzero_not_divides",), "non-campaign"),
        (("lucas_theorem",), "non-campaign"),
    ),
)
def test_campaign_constructor_rejects_invalid_scope_before_replay(
    names: object, message: str
) -> None:
    with pytest.raises(FrontierPromotionError, match=message):
        construct_four_square_campaign_microbatch(names)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("indices", "message"),
    (
        ((), "cannot be empty"),
        ("0", "tuple or list"),
        ((True,), "exact integers"),
        ((0, 0), "duplicated"),
        ((4,), "outside its exact plan"),
        ((1, 0), "dependency ordered"),
    ),
)
def test_campaign_batch_scheduler_rejects_forged_sequence_before_replay(
    indices: object, message: str
) -> None:
    with pytest.raises(FrontierPromotionError, match=message):
        construct_four_square_initial_campaign_certificates(indices)  # type: ignore[arg-type]


def test_campaign_batch_scheduler_rejects_invalid_progress_callback_before_replay() -> None:
    with pytest.raises(FrontierPromotionError, match="must be callable"):
        construct_four_square_initial_campaign_certificates(
            (0,),
            on_checked=1,  # type: ignore[arg-type]
        )


def test_campaign_scheduler_rejects_mutated_leaf_budget_before_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS
    mutated = (
        (
            original[0][0],
            promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
            original[0][2],
            original[0][3],
        ),
        *original[1:],
    )
    monkeypatch.setattr(promotion, "FOUR_SQUARE_INITIAL_CAMPAIGN_LEAF_BUDGETS", mutated)

    with pytest.raises(FrontierPromotionError, match="direct-leaf budget"):
        four_square_initial_campaign_batches()


def test_established_nine_parent_observations_never_grant_release_authority() -> None:
    plan = four_square_frontier_plan()
    parents = {item.name for item in plan.parent_obligations}

    assert FOUR_SQUARE_ESTABLISHED_PARENT_DIAGNOSTICS == (
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
    assert set(FOUR_SQUARE_ESTABLISHED_PARENT_NAMES) <= parents
    assert all(
        not v13.ALPHA_EDITION.by_name[name].checked_use
        for name in FOUR_SQUARE_ESTABLISHED_PARENT_NAMES
    )


def test_all_eighteen_non_beta_parent_rows_are_dependency_closed() -> None:
    plan = four_square_frontier_plan()
    parents = {item.name for item in plan.parent_obligations}
    selected = set(FOUR_SQUARE_NON_BETA_PARENT_NAMES)
    remaining = parents.difference(selected)

    assert len(selected) == 18
    assert remaining == {
        "beta_pointwise_mul_prefix_extend",
        "beta_pointwise_mul_prefix_exists",
        "beta_prefix_append_two_exists",
        "beta_division_prefix_extend",
        "beta_division_prefix_exists",
    }
    assert all(
        set(item.pending_parent_dependencies) <= selected
        for item in plan.parent_obligations
        if item.name in selected
    )
    assert len(FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH) == 16
    assert FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH == (
        FOUR_SQUARE_NON_BETA_PARENT_NAMES[:16]
    )


def test_five_beta_parent_surfaces_and_exact_stable_leaf_budgets_are_frozen() -> None:
    plan = four_square_frontier_plan()
    parents = {item.name: item for item in plan.parent_obligations}

    assert FOUR_SQUARE_BETA_PARENT_NAMES == (
        "beta_pointwise_mul_prefix_extend",
        "beta_pointwise_mul_prefix_exists",
        "beta_prefix_append_two_exists",
        "beta_division_prefix_extend",
        "beta_division_prefix_exists",
    )
    assert set(FOUR_SQUARE_BETA_PARENT_NAMES) == (
        set(parents).difference(FOUR_SQUARE_NON_BETA_PARENT_NAMES)
    )
    assert FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS == (
        ("beta_pointwise_mul_prefix_extend", 30_785, 5_716, ()),
        (
            "beta_pointwise_mul_prefix_exists",
            499,
            412,
            ("beta_pointwise_mul_prefix_extend",),
        ),
        ("beta_prefix_append_two_exists", 29_122, 4_571, ()),
        ("beta_division_prefix_extend", 29_185, 4_632, ()),
        (
            "beta_division_prefix_exists",
            718,
            608,
            ("beta_division_prefix_extend",),
        ),
    )
    assert dict(FOUR_SQUARE_BETA_PARENT_STATEMENT_SHA256) == {
        name: parents[name].statement_sha256 for name in FOUR_SQUARE_BETA_PARENT_NAMES
    }
    for name, nodes, objects, dependencies in (
        FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS
    ):
        assert nodes < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        assert objects < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        assert parents[name].pending_dependencies == dependencies
        assert not v13.ALPHA_EDITION.by_name[name].checked_use


@pytest.mark.parametrize(
    ("names", "message"),
    (
        ((), "cannot be empty"),
        ("beta_pointwise_mul_prefix_extend", "tuple or list"),
        ((1,), "exact strings"),
        (("beta_pointwise_mul_prefix_extend",) * 6, "exceeds five"),
        (("beta_pointwise_mul_prefix_extend",) * 2, "repeats"),
        (("bounded_nonzero_not_divides",), "non-beta"),
        (
            ("beta_pointwise_mul_prefix_exists", "beta_pointwise_mul_prefix_extend"),
            "dependency ordered",
        ),
    ),
)
def test_beta_sequence_rejects_invalid_scope_before_replay(
    names: object, message: str
) -> None:
    with pytest.raises(FrontierPromotionError, match=message):
        construct_four_square_beta_parent_certificates(names)  # type: ignore[arg-type]


def test_beta_sequence_requires_actual_predecessor_proof_before_replay() -> None:
    with pytest.raises(FrontierPromotionError, match="missing actual closed"):
        construct_four_square_beta_parent_certificates(
            ("beta_pointwise_mul_prefix_exists",)
        )
    with pytest.raises(FrontierPromotionError, match="unexpected four-square beta"):
        construct_four_square_beta_parent_certificates(
            ("beta_pointwise_mul_prefix_extend",),
            prerequisites={"beta_division_prefix_extend": EqRefl(Zero())},
        )


def test_beta_sequence_rejects_non_callable_progress_callback_before_replay() -> None:
    with pytest.raises(FrontierPromotionError, match="must be callable"):
        construct_four_square_beta_parent_certificates(
            ("beta_pointwise_mul_prefix_extend",),
            on_checked=1,  # type: ignore[arg-type]
        )


def test_beta_sequence_rejects_mutated_exact_statement_before_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = four_square_frontier_plan()
    mutated = replace(
        original,
        obligations=tuple(
            replace(item, statement_sha256="0" * 64)
            if item.name == "beta_pointwise_mul_prefix_extend"
            else item
            for item in original.obligations
        ),
    )
    monkeypatch.setattr(promotion, "four_square_frontier_plan", lambda: mutated)

    with pytest.raises(FrontierPromotionError, match="unsealed exact statement"):
        construct_four_square_beta_parent_certificates()


def test_beta_sequence_rejects_oversized_sealed_leaf_budget_before_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS
    mutated = (
        (
            original[0][0],
            promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
            original[0][2],
            original[0][3],
        ),
        *original[1:],
    )
    monkeypatch.setattr(
        promotion,
        "FOUR_SQUARE_BETA_PARENT_STABLE_DIRECT_LEAF_BUDGETS",
        mutated,
    )

    with pytest.raises(FrontierPromotionError, match="direct-leaf budget"):
        construct_four_square_beta_parent_certificates()


def test_all_twenty_three_old_parents_have_genuine_bounded_closed_constructions() -> None:
    observed = FOUR_SQUARE_BETA_PARENT_CHECKED_DIAGNOSTICS
    plan = four_square_frontier_plan()

    assert observed == (
        ("beta_pointwise_mul_prefix_extend", 30_906, 4_643),
        ("beta_pointwise_mul_prefix_exists", 31_467, 4_705),
        ("beta_prefix_append_two_exists", 29_185, 4_571),
        ("beta_division_prefix_extend", 29_317, 4_654),
        ("beta_division_prefix_exists", 30_106, 4_725),
    )
    assert tuple(name for name, _nodes, _objects in observed) == (
        FOUR_SQUARE_BETA_PARENT_NAMES
    )
    assert max(nodes for _name, nodes, _objects in observed) == 31_467
    assert max(objects for _name, _nodes, objects in observed) == 4_725
    assert sum(nodes for _name, nodes, _objects in observed) == 150_981
    assert sum(nodes for _name, nodes, _objects in observed) > (
        promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    )
    assert all(
        nodes < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        and objects < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        for _name, nodes, objects in observed
    )
    closed = {
        *FOUR_SQUARE_NON_BETA_PARENT_NAMES,
        *(name for name, _nodes, _objects in observed),
    }
    assert len(closed) == 23
    assert closed == {item.name for item in plan.parent_obligations}
    assert all(not v13.ALPHA_EDITION.by_name[name].checked_use for name in closed)
    assert len(v13.ALPHA_CHECKED_SPECS) == 570
    assert not v13.ALPHA_EDITION.by_name["four_square_lagrange"].checked_use


def test_sixteen_actual_parent_certificates_respect_all_unchanged_budgets() -> None:
    observed = FOUR_SQUARE_NON_BETA_MICROBATCH_DIAGNOSTICS

    assert tuple(name for name, _nodes, _objects in observed) == (
        FOUR_SQUARE_NON_BETA_PARENT_MICROBATCH
    )
    assert len(observed) == 16
    assert sum(nodes for _name, nodes, _objects in observed) == 18_008
    assert sum(objects for _name, _nodes, objects in observed) == 8_869
    assert 18_008 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 8_869 < promotion.MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    closed = {name for name, _nodes, _objects in observed}
    closed.update(FOUR_SQUARE_ESTABLISHED_PARENT_NAMES)
    assert closed == set(FOUR_SQUARE_NON_BETA_PARENT_NAMES)
    assert len(closed) == 18
    assert all(not v13.ALPHA_EDITION.by_name[name].checked_use for name in closed)


def test_hypothetical_ready_scheduling_cannot_claim_proof_or_checked_use() -> None:
    plan = four_square_frontier_plan()

    assert four_square_hypothetical_ready_rows(include_campaign=False) == (
        plan.ready_parent_names
    )
    after_even = four_square_hypothetical_ready_rows(
        ("even_sum_parity_cases",), include_campaign=False
    )
    assert "even_sum_iff_same_parity" in after_even
    assert not v13.ALPHA_EDITION.by_name["even_sum_parity_cases"].checked_use
    assert len(v13.ALPHA_CHECKED_SPECS) == 570


@pytest.mark.parametrize(
    ("names", "message"),
    (
        ("bounded_nonzero_not_divides", "tuple or list"),
        (("bounded_nonzero_not_divides",) * 2, "duplicate"),
        (("unknown_four_square_row",), "unknown"),
        ((1,), "exact strings"),
    ),
)
def test_hypothetical_scheduling_rejects_invalid_names(names: object, message: str) -> None:
    with pytest.raises(FrontierPromotionError, match=message):
        four_square_hypothetical_ready_rows(names)  # type: ignore[arg-type]


def test_hypothetical_scheduling_rejects_non_boolean_campaign_flag() -> None:
    with pytest.raises(FrontierPromotionError, match="boolean"):
        four_square_hypothetical_ready_rows(include_campaign=1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("parent_alpha_identity_sha256", "0" * 64),
        ("parent_alpha_enrollment_sha256", "1" * 64),
        ("dependency_edge_count", 1_188),
        ("exact_surface_sha256", "2" * 64),
        ("ordered_names_sha256", "3" * 64),
    ),
)
def test_four_square_planner_rejects_forged_source_receipts(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    source = four_square_frontier_plan().source
    mutated = replace(source, **{field: value})
    monkeypatch.setattr(promotion, "frontier_promotion_plan", lambda _roots: mutated)

    with pytest.raises(FrontierPromotionError, match="sealed Alpha-v13 slice"):
        four_square_frontier_plan()


@pytest.mark.parametrize(
    ("names", "message"),
    (
        ((), "cannot be empty"),
        ("bounded_nonzero_not_divides", "tuple or list"),
        (("four_square_lagrange",), "non-parent"),
        (tuple(FOUR_SQUARE_NON_BETA_PARENT_NAMES[:17]), "16-row"),
        ((1,), "exact strings"),
    ),
)
def test_parent_constructor_rejects_invalid_scope_before_replay(
    names: object, message: str
) -> None:
    with pytest.raises(FrontierPromotionError, match=message):
        construct_four_square_parent_microbatch(names)  # type: ignore[arg-type]


def test_parent_constructor_rejects_fake_unchecked_prerequisites() -> None:
    with pytest.raises(FrontierPromotionError, match="kernel rejected"):
        construct_four_square_parent_microbatch(
            ("even_sum_iff_same_parity",),
            prerequisites={"even_sum_parity_cases": EqRefl(Zero())},
        )


def test_shared_constructor_rejects_nonpending_or_cross_campaign_targets() -> None:
    for name in ("zero_add", "lucas_theorem", "unknown_four_square_row"):
        with pytest.raises(FrontierPromotionError, match="not an exact pending"):
            construct_four_square_shared_closed_candidate(name, shared_rows=())


def test_single_parent_proof_is_an_actual_bounded_empty_context_certificate() -> None:
    (checked,) = construct_four_square_parent_microbatch(
        ("bounded_nonzero_not_divides",)
    )

    assert checked.name == "bounded_nonzero_not_divides"
    assert checked.diagnostics.proof_nodes == 140
    assert checked.diagnostics.proof_objects <= 140
    assert not v13.ALPHA_EDITION.by_name[checked.name].checked_use
    assert len(v13.ALPHA_CHECKED_SPECS) == 570
