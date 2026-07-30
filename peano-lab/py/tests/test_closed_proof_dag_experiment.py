"""Focused soundness and resource tests for the isolated closed-DAG prototype."""

from __future__ import annotations

from dataclasses import replace

import peano_lab.experimental.closed_proof_dag as dag
import pytest
from peano_lab.kernel.formulas import And, Bot, Eq, Imp
from peano_lab.kernel.proofs import AndIntro, DNE, EqRefl, Hyp, ImpIntro
from peano_lab.kernel.terms import Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)


def _valid_bundle() -> dag.ClosedBundle:
    return dag.ClosedBundle(
        nodes=(
            dag.ClosedNode(10, P, (), EqRefl(ZERO)),
            dag.ClosedNode(
                30,
                And(P, P),
                (10,),
                ImpIntro(AndIntro(Hyp(0), Hyp(0))),
            ),
        ),
        root=30,
    )


def test_bundle_checks_each_dependency_curried_body_once_from_empty_context(
    monkeypatch,
) -> None:
    observed: list[tuple[tuple[object, ...], object, object]] = []
    original = dag.kernel_checker.check

    def recording_check(context, proof, target):
        observed.append((context, proof, target))
        return original(context, proof, target)

    monkeypatch.setattr(dag.kernel_checker, "check", recording_check)
    receipt = dag.check_closed_bundle(_valid_bundle(), And(P, P))

    assert receipt is not None
    assert receipt.topological_order == (10, 30)
    assert receipt.dependency_edges == 1
    assert len(observed) == 2
    assert all(context == () for context, _, _ in observed)
    assert observed[0][2] == P
    assert observed[1][2] == Imp(P, And(P, P))


def test_bundle_order_is_derived_and_local_ids_grant_no_authority() -> None:
    original = _valid_bundle()
    reversed_input = replace(original, nodes=tuple(reversed(original.nodes)))

    receipt = dag.check_closed_bundle(reversed_input, And(P, P))

    assert receipt is not None
    assert receipt.topological_order == (10, 30)


def test_mutated_body_dependency_and_targets_are_rejected() -> None:
    original = _valid_bundle()
    leaf, root = original.nodes
    unrelated = dag.ClosedNode(20, Q, (), EqRefl(ONE))

    bad_leaf = replace(original, nodes=(replace(leaf, body=EqRefl(ONE)), root))
    bad_edge = replace(
        original,
        nodes=(leaf, unrelated, replace(root, dependencies=(20,))),
    )
    bad_annotation = replace(original, nodes=(replace(leaf, target=Q), root))

    assert dag.check_closed_bundle(bad_leaf, And(P, P)) is None
    assert dag.check_closed_bundle(bad_edge, And(P, P)) is None
    assert dag.check_closed_bundle(bad_annotation, And(P, P)) is None
    assert dag.check_closed_bundle(original, P) is None


def test_cycle_dangling_reference_duplicate_id_and_duplicate_edge_are_rejected() -> None:
    implication = Imp(P, P)
    cyclic = dag.ClosedBundle(
        (
            dag.ClosedNode(0, P, (1,), ImpIntro(Hyp(0))),
            dag.ClosedNode(1, P, (0,), ImpIntro(Hyp(0))),
        ),
        0,
    )
    dangling = dag.ClosedBundle(
        (dag.ClosedNode(0, P, (99,), ImpIntro(Hyp(0))),),
        0,
    )
    duplicate_id = dag.ClosedBundle(
        (
            dag.ClosedNode(0, P, (), EqRefl(ZERO)),
            dag.ClosedNode(0, Q, (), EqRefl(ONE)),
        ),
        0,
    )
    duplicate_edge = dag.ClosedBundle(
        (
            dag.ClosedNode(0, P, (), EqRefl(ZERO)),
            dag.ClosedNode(
                1,
                implication,
                (0, 0),
                ImpIntro(ImpIntro(ImpIntro(Hyp(0)))),
            ),
        ),
        1,
    )
    unreachable = dag.ClosedBundle(
        (
            dag.ClosedNode(0, P, (), EqRefl(ZERO)),
            dag.ClosedNode(1, Q, (), EqRefl(ONE)),
        ),
        0,
    )

    assert dag.check_closed_bundle(cyclic, P) is None
    assert dag.check_closed_bundle(dangling, P) is None
    assert dag.check_closed_bundle(duplicate_id, P) is None
    assert dag.check_closed_bundle(duplicate_edge, implication) is None
    assert dag.check_closed_bundle(unreachable, P) is None


def test_targets_must_be_closed_exact_kernel_formulas() -> None:
    open_formula = Eq(Var(0), Var(0))
    open_bundle = dag.ClosedBundle(
        (dag.ClosedNode(0, open_formula, (), EqRefl(Var(0))),),
        0,
    )

    class EvilEq(Eq):
        pass

    evil = EvilEq(ZERO, ZERO)
    evil_bundle = dag.ClosedBundle(
        (dag.ClosedNode(0, evil, (), EqRefl(ZERO)),),
        0,
    )

    assert dag.check_closed_bundle(open_bundle, open_formula) is None
    assert dag.check_closed_bundle(evil_bundle, evil) is None


def test_one_logic_mode_governs_every_body() -> None:
    dne_p = Imp(Imp(Imp(P, Bot()), Bot()), P)
    constructive = dag.ClosedBundle(
        (dag.ClosedNode(0, dne_p, (), DNE(P)),),
        0,
        classical=False,
    )
    classical = replace(constructive, classical=True)

    assert dag.check_closed_bundle(constructive, dne_p) is None
    assert dag.check_closed_bundle(classical, dne_p) is not None


def test_exact_resource_boundaries_and_one_past_reject_transactionally(
    monkeypatch,
) -> None:
    bundle = _valid_bundle()
    baseline = dag.check_closed_bundle(bundle, And(P, P))
    assert baseline is not None

    exact = dag.ClosedDagLimits(
        max_nodes=2,
        max_dependencies_per_node=1,
        max_dependency_edges=1,
        max_formula_occurrences_per_target=baseline.formula_occurrences,
        max_total_formula_occurrences=baseline.formula_occurrences,
        max_body_occurrences=max(item.body_occurrences for item in baseline.nodes),
        max_body_objects=max(item.body_objects for item in baseline.nodes),
        max_body_depth=baseline.maximum_body_depth,
        max_total_body_occurrences=baseline.body_occurrences,
        max_total_body_objects=baseline.body_objects,
    )
    assert dag.check_closed_bundle(bundle, And(P, P), limits=exact) is not None

    calls = 0
    original = dag.kernel_checker.check

    def recording_check(context, proof, target):
        nonlocal calls
        calls += 1
        return original(context, proof, target)

    monkeypatch.setattr(dag.kernel_checker, "check", recording_check)
    too_small = replace(exact, max_total_body_occurrences=baseline.body_occurrences - 1)

    assert dag.check_closed_bundle(bundle, And(P, P), limits=too_small) is None
    assert calls == 0


@pytest.mark.parametrize(
    ("field", "one_past"),
    (
        ("max_nodes", 1),
        ("max_formula_occurrences_per_target", 6),
        ("max_total_formula_occurrences", 16),
        ("max_body_occurrences", 3),
        ("max_body_objects", 3),
        ("max_body_depth", 2),
        ("max_total_body_occurrences", 4),
        ("max_total_body_objects", 4),
    ),
)
def test_each_node_formula_and_body_resource_dimension_rejects_one_past(
    field: str, one_past: int
) -> None:
    limits = replace(dag.DEFAULT_LIMITS, **{field: one_past})

    assert dag.check_closed_bundle(_valid_bundle(), And(P, P), limits=limits) is None


def test_dependency_width_and_edge_limits_reject_one_past() -> None:
    bundle = dag.ClosedBundle(
        (
            dag.ClosedNode(0, P, (), EqRefl(ZERO)),
            dag.ClosedNode(1, Q, (), EqRefl(ONE)),
            dag.ClosedNode(
                2,
                And(P, Q),
                (0, 1),
                ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0)))),
            ),
        ),
        2,
    )

    assert dag.check_closed_bundle(
        bundle,
        And(P, Q),
        limits=replace(dag.DEFAULT_LIMITS, max_dependencies_per_node=1),
    ) is None
    assert dag.check_closed_bundle(
        bundle,
        And(P, Q),
        limits=replace(dag.DEFAULT_LIMITS, max_dependency_edges=1),
    ) is None


def test_malformed_bundle_and_receipt_have_no_production_kernel_authority() -> None:
    receipt = dag.check_closed_bundle(_valid_bundle(), And(P, P))

    assert receipt is not None
    assert not isinstance(receipt, dag.Proof)
    assert dag.kernel_checker.check((), receipt, And(P, P)) is False
    assert dag.check_closed_bundle(object(), And(P, P)) is None
