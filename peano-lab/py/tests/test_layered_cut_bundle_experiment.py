"""Small executable checks for unchanged-kernel layered DAG closure."""

from __future__ import annotations

from dataclasses import fields, replace

from peano_lab.experimental.closed_proof_dag import ClosedBundle, ClosedNode
from peano_lab.experimental.layered_cut_bundle import (
    compile_layered_cut_bundle,
    compile_recursive_cut_bundle,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Bot, Eq, Imp
from peano_lab.kernel.proofs import AndIntro, Cut, DNE, EqRefl, Hyp, ImpIntro, Proof
from peano_lab.kernel.terms import Succ, Zero


ZERO = Zero()
ONE = Succ(ZERO)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)


def _ignore_dependencies_body(count: int, target_proof: Proof | None = None) -> Proof:
    proof = EqRefl(ZERO) if target_proof is None else target_proof
    for _ in range(count):
        proof = ImpIntro(proof)
    return proof


def _diamond_bundle(depth: int = 6, width: int = 3) -> ClosedBundle:
    nodes: list[ClosedNode] = [ClosedNode(0, P, (), EqRefl(ZERO))]
    previous = (0,)
    next_id = 1
    for _ in range(depth):
        current: list[int] = []
        for _ in range(width):
            node_id = next_id
            next_id += 1
            nodes.append(
                ClosedNode(
                    node_id,
                    P,
                    previous,
                    _ignore_dependencies_body(len(previous)),
                )
            )
            current.append(node_id)
        previous = tuple(current)
    root = next_id
    nodes.append(
        ClosedNode(root, P, previous, _ignore_dependencies_body(len(previous)))
    )
    return ClosedBundle(tuple(nodes), root)


def _proof_occurrences_of_identity(proof: Proof, wanted: int) -> int:
    found = 0
    pending = [proof]
    while pending:
        node = pending.pop()
        found += id(node) == wanted
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )
    return found


def _all_proof_nodes(proof: Proof) -> tuple[Proof, ...]:
    result: list[Proof] = []
    pending = [proof]
    while pending:
        node = pending.pop()
        result.append(node)
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )
    return tuple(result)


def test_layered_compiler_produces_one_existing_closed_cut_certificate() -> None:
    bundle = _diamond_bundle(depth=3, width=2)
    compiled = compile_layered_cut_bundle(bundle, P)

    assert compiled is not None
    assert compiled.layers == ((0,), (1, 2), (3, 4), (5, 6), (7,))
    assert type(compiled.certificate) is Cut
    assert compiled.package_formula_occurrences > 0
    assert compiled.maximum_package_formula_depth > 0
    assert all(
        type(node).__module__ == "peano_lab.kernel.proofs"
        for node in _all_proof_nodes(compiled.certificate)
    )
    assert check((), compiled.certificate, P)
    assert all(
        _proof_occurrences_of_identity(compiled.certificate, id(node.body)) == 1
        for node in bundle.nodes
    )


def test_layered_bundle_beats_recursive_closure_on_reused_synthetic_dag() -> None:
    bundle = _diamond_bundle(depth=6, width=3)
    layered = compile_layered_cut_bundle(bundle, P)
    recursive = compile_recursive_cut_bundle(bundle, P)

    assert layered is not None and recursive is not None
    assert check((), layered.certificate, P)
    assert check((), recursive.certificate, P)
    assert layered.proof_nodes < recursive.proof_nodes
    assert layered.proof_depth < recursive.proof_depth
    assert recursive.proof_nodes >= 4 * layered.proof_nodes


def test_balanced_packages_project_exact_distinct_targets() -> None:
    nodes = (
        ClosedNode(0, P, (), EqRefl(ZERO)),
        ClosedNode(1, Q, (), EqRefl(ONE)),
        ClosedNode(
            2,
            And(P, Q),
            (0, 1),
            ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0)))),
        ),
    )
    bundle = ClosedBundle(nodes, 2)
    compiled = compile_layered_cut_bundle(bundle, And(P, Q))

    assert compiled is not None
    assert compiled.layers == ((0, 1), (2,))
    assert check((), compiled.certificate, And(P, Q))


def test_projection_indices_reach_nonadjacent_earlier_packages() -> None:
    pair = And(P, Q)
    target = And(P, pair)
    bundle = ClosedBundle(
        (
            ClosedNode(0, P, (), EqRefl(ZERO)),
            ClosedNode(1, Q, (), EqRefl(ONE)),
            ClosedNode(
                2,
                pair,
                (0, 1),
                ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0)))),
            ),
            ClosedNode(
                3,
                target,
                (0, 2),
                ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0)))),
            ),
        ),
        3,
    )
    compiled = compile_layered_cut_bundle(bundle, target)

    assert compiled is not None
    assert compiled.layers == ((0, 1), (2,), (3,))
    assert check((), compiled.certificate, target)


def test_graph_and_target_mutations_fail_closed_or_kernel_reject() -> None:
    original = _diamond_bundle(depth=2, width=2)
    leaf, *middle, root = original.nodes

    dangling = replace(
        original,
        nodes=tuple(middle) + (replace(root, dependencies=(999,)),),
    )
    cyclic_nodes = list(original.nodes)
    cyclic_nodes[0] = replace(
        leaf,
        dependencies=(original.root,),
        body=ImpIntro(leaf.body),
    )
    cyclic = replace(original, nodes=tuple(cyclic_nodes))
    mutated_body = replace(
        original,
        nodes=(replace(leaf, body=EqRefl(ONE)),) + tuple(original.nodes[1:]),
    )

    assert compile_layered_cut_bundle(dangling, P) is None
    assert compile_layered_cut_bundle(cyclic, P) is None
    compiled_bad_body = compile_layered_cut_bundle(mutated_body, P)
    assert compiled_bad_body is not None
    assert not check((), compiled_bad_body.certificate, P)
    assert compile_layered_cut_bundle(original, Q) is None


def test_production_adapter_rejects_declared_or_hidden_classical_bodies() -> None:
    dne_p = Imp(Imp(Imp(P, Bot()), Bot()), P)
    classical = ClosedBundle(
        (ClosedNode(0, dne_p, (), DNE(P)),),
        0,
        classical=True,
    )
    mislabeled_constructive = ClosedBundle(
        (ClosedNode(0, dne_p, (), DNE(P)),),
        0,
        classical=False,
    )

    assert compile_layered_cut_bundle(classical, dne_p) is None
    assert compile_layered_cut_bundle(mislabeled_constructive, dne_p) is None
