"""Laptop-safe trust and topology checks for production layered replay."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path

import peano_lab.library.layered_replay as layered
from peano_lab.engine.state import Hole, MetaVar
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Bot, Eq, Forall, Formula, Imp
from peano_lab.kernel.proofs import (
    Axiom,
    Cut,
    DNE,
    EqRefl,
    EqSubst,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    Ind,
    Proof,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    quadratic_reciprocity_stack,
)


ZERO = Zero()
ONE = Succ(ZERO)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)


@dataclass(frozen=True, slots=True)
class _ForeignProof(Proof):
    child: Proof


def _ignore_dependencies_body(count: int, proof: Proof | None = None) -> Proof:
    result = EqRefl(ZERO) if proof is None else proof
    for _ in range(count):
        result = ImpIntro(result)
    return result


def _diamond_bundle(depth: int = 3, width: int = 2) -> layered.LayeredReplayBundle:
    nodes = [layered.LayeredReplayNode(0, P, (), EqRefl(ZERO))]
    previous = (0,)
    next_id = 1
    for _ in range(depth):
        current: list[int] = []
        for _ in range(width):
            node_id = next_id
            next_id += 1
            nodes.append(
                layered.LayeredReplayNode(
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
        layered.LayeredReplayNode(
            root,
            P,
            previous,
            _ignore_dependencies_body(len(previous)),
        )
    )
    return layered.LayeredReplayBundle(tuple(nodes), root)


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


def _marker(node_id: int) -> object:
    marker = Succ(ZERO)
    for bit in f"{node_id + 1:b}"[1:]:
        marker = Add(marker, ZERO) if bit == "0" else Mul(marker, ZERO)
    return marker


def test_production_import_and_records_are_neutral_and_name_free() -> None:
    source = Path(layered.__file__).read_text(encoding="utf-8")
    package_root = Path(layered.__file__).resolve().parents[1]
    compatibility_source = (
        package_root / "experimental" / "layered_cut_bundle.py"
    ).read_text(encoding="utf-8")
    fallback_source = (
        package_root / "experimental" / "closed_proof_dag.py"
    ).read_text(encoding="utf-8")

    assert layered.__all__ == [
        "LayeredReplayError",
        "LayeredReplayLimits",
        "DEFAULT_LAYERED_REPLAY_LIMITS",
        "LayeredReplayNode",
        "LayeredReplayBundle",
        "LayeredReplayCandidate",
        "compile_layered_replay",
    ]
    assert tuple(item.name for item in fields(layered.LayeredReplayNode)) == (
        "node_id",
        "target",
        "dependencies",
        "body",
    )
    assert tuple(item.name for item in fields(layered.LayeredReplayBundle)) == (
        "nodes",
        "root",
    )
    limits = layered.DEFAULT_LAYERED_REPLAY_LIMITS
    assert (
        limits.max_candidate_proof_occurrences,
        limits.max_candidate_proof_objects,
        limits.max_candidate_proof_depth,
    ) == (500_000, 100_000, 256)
    assert (
        limits.max_body_annotation_occurrences,
        limits.max_body_envelope_depth,
        limits.max_total_body_annotation_occurrences,
        limits.max_candidate_annotation_occurrences,
        limits.max_candidate_envelope_depth,
    ) == (500_000, 256, 5_000_000, 5_000_000, 256)
    assert (
        limits.max_package_formula_occurrences,
        limits.max_package_formula_depth,
    ) == (500_000, 256)
    assert all(
        value.__module__ == "peano_lab.library.layered_replay"
        for value in (
            layered.LayeredReplayLimits,
            layered.LayeredReplayNode,
            layered.LayeredReplayBundle,
            layered.LayeredReplayCandidate,
        )
    )
    assert "experimental" not in source
    assert "library.theorems" not in source
    assert "quadratic_reciprocity" not in source
    assert "register_theorem" not in source
    assert "sha256" not in source
    assert "check(" not in source
    assert "from ..library.layered_replay import" in compatibility_source
    assert "compile_layered_replay(" in compatibility_source
    assert "def _balanced_package" not in compatibility_source
    assert "layered_replay" not in fallback_source


def test_balanced_candidate_is_only_existing_ordinary_proof_nodes() -> None:
    bundle = _diamond_bundle()
    candidate = layered.compile_layered_replay(bundle, P)

    assert type(candidate) is layered.LayeredReplayCandidate
    assert candidate.target == P
    assert candidate.layers == ((0,), (1, 2), (3, 4), (5, 6), (7,))
    assert type(candidate.certificate) is Cut
    assert candidate.package_formula_occurrences > 0
    assert candidate.maximum_package_formula_depth > 0
    assert candidate.proof_annotation_occurrences > 0
    assert candidate.proof_envelope_depth >= candidate.proof_depth
    assert all(
        type(node).__module__ == "peano_lab.kernel.proofs"
        for node in _all_proof_nodes(candidate.certificate)
    )
    assert check((), candidate.certificate, P)


def test_graph_resource_target_body_and_classical_mutations_fail_closed() -> None:
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
    unreachable = replace(
        original,
        nodes=original.nodes + (layered.LayeredReplayNode(99, Q, (), EqRefl(ONE)),),
    )
    duplicate = replace(
        original,
        nodes=original.nodes + (replace(leaf),),
    )
    mutated_body = replace(
        original,
        nodes=(replace(leaf, body=EqRefl(ONE)),) + original.nodes[1:],
    )
    open_target = Eq(Var(0), Var(0))
    open_bundle = layered.LayeredReplayBundle(
        (layered.LayeredReplayNode(0, open_target, (), EqRefl(Var(0))),),
        0,
    )

    assert layered.compile_layered_replay(dangling, P) is None
    assert layered.compile_layered_replay(cyclic, P) is None
    assert layered.compile_layered_replay(unreachable, P) is None
    assert layered.compile_layered_replay(duplicate, P) is None
    assert layered.compile_layered_replay(original, Q) is None
    assert layered.compile_layered_replay(open_bundle, open_target) is None
    assert (
        layered.compile_layered_replay(
            original,
            P,
            limits=replace(layered.DEFAULT_LAYERED_REPLAY_LIMITS, max_nodes=1),
        )
        is None
    )
    for field_name in (
        "max_package_formula_occurrences",
        "max_package_formula_depth",
        "max_candidate_proof_occurrences",
        "max_candidate_proof_objects",
        "max_candidate_proof_depth",
        "max_body_envelope_depth",
        "max_total_body_annotation_occurrences",
        "max_candidate_annotation_occurrences",
        "max_candidate_envelope_depth",
    ):
        assert (
            layered.compile_layered_replay(
                original,
                P,
                limits=replace(
                    layered.DEFAULT_LAYERED_REPLAY_LIMITS,
                    **{field_name: 1},
                ),
            )
            is None
        )

    bad_body = layered.compile_layered_replay(mutated_body, P)
    assert bad_body is not None
    assert not check((), bad_body.certificate, P)

    dne_p = Imp(Imp(Imp(P, Bot()), Bot()), P)
    classical_body = layered.LayeredReplayBundle(
        (layered.LayeredReplayNode(0, dne_p, (), DNE(P)),),
        0,
    )
    classical_candidate = layered.compile_layered_replay(classical_body, dne_p)
    assert classical_candidate is None
    nested_classical_body = layered.LayeredReplayBundle(
        (
            layered.LayeredReplayNode(
                0,
                P,
                (),
                Cut(dne_p, P, DNE(P), EqRefl(ZERO)),
            ),
        ),
        0,
    )
    assert layered.compile_layered_replay(nested_classical_body, P) is None


def test_proof_envelope_rejects_non_kernel_and_malformed_nodes() -> None:
    invalid_bodies = (
        Hole(0),
        _ForeignProof(EqRefl(ZERO)),
        EqRefl(MetaVar(0)),
        Hyp(-1),
        Hyp(True),
        Axiom("PA7"),
        ImpIntro("not a proof"),  # type: ignore[arg-type]
        Cut("not a formula", P, EqRefl(ZERO), EqRefl(ZERO)),  # type: ignore[arg-type]
    )
    for body in invalid_bodies:
        bundle = layered.LayeredReplayBundle(
            (layered.LayeredReplayNode(0, P, (), body),),
            0,
        )
        assert layered.compile_layered_replay(bundle, P) is None


def test_proof_envelope_allows_scoped_kernel_annotations() -> None:
    motive = Eq(Var(0), Var(0))
    substitution = EqSubst(motive, EqRefl(ZERO), EqRefl(ZERO))
    substitution_bundle = layered.LayeredReplayBundle(
        (layered.LayeredReplayNode(0, P, (), substitution),),
        0,
    )
    substitution_candidate = layered.compile_layered_replay(
        substitution_bundle,
        P,
    )
    assert substitution_candidate is not None
    assert check((), substitution_candidate.certificate, P)

    universal = Forall(motive)
    universal_bundle = layered.LayeredReplayBundle(
        (
            layered.LayeredReplayNode(
                0,
                universal,
                (),
                ForallIntro(EqRefl(Var(0))),
            ),
        ),
        0,
    )
    universal_candidate = layered.compile_layered_replay(
        universal_bundle,
        universal,
    )
    assert universal_candidate is not None
    assert check((), universal_candidate.certificate, universal)


def test_proof_envelope_bounds_annotations_and_combined_depth() -> None:
    deep = ZERO
    for _ in range(12):
        deep = Succ(deep)
    hidden = Eq(deep, deep)
    valid_body = Cut(hidden, P, EqRefl(deep), EqRefl(ZERO))
    bundle = layered.LayeredReplayBundle(
        (layered.LayeredReplayNode(0, P, (), valid_body),),
        0,
    )

    permissive = layered.compile_layered_replay(bundle, P)
    assert permissive is not None
    assert check((), permissive.certificate, P)
    assert (
        layered.compile_layered_replay(
            bundle,
            P,
            limits=replace(
                layered.DEFAULT_LAYERED_REPLAY_LIMITS,
                max_formula_depth=3,
            ),
        )
        is None
    )
    assert (
        layered.compile_layered_replay(
            bundle,
            P,
            limits=replace(
                layered.DEFAULT_LAYERED_REPLAY_LIMITS,
                max_body_annotation_occurrences=3,
            ),
        )
        is None
    )

    shallow = Succ(Succ(ZERO))
    shallow_formula = Eq(shallow, shallow)
    shallow_body = Cut(
        shallow_formula,
        P,
        EqRefl(shallow),
        EqRefl(ZERO),
    )
    shallow_bundle = layered.LayeredReplayBundle(
        (layered.LayeredReplayNode(0, P, (), shallow_body),),
        0,
    )
    assert (
        layered.compile_layered_replay(
            shallow_bundle,
            P,
            limits=replace(
                layered.DEFAULT_LAYERED_REPLAY_LIMITS,
                max_formula_depth=4,
                max_body_depth=2,
                max_body_envelope_depth=4,
            ),
        )
        is None
    )
    assert (
        layered.compile_layered_replay(
            layered.LayeredReplayBundle(
                (layered.LayeredReplayNode(0, P, (), EqRefl(ZERO)),),
                0,
            ),
            P,
            limits=replace(
                layered.DEFAULT_LAYERED_REPLAY_LIMITS,
                max_candidate_annotation_occurrences=1,
            ),
        )
        is None
    )


def test_every_annotated_constructor_branch_is_resource_scanned() -> None:
    deep_term = ZERO
    for _ in range(8):
        deep_term = Succ(deep_term)
    deep_motive = Eq(deep_term, deep_term)
    annotated_bodies = (
        ForallElim(EqRefl(ZERO), deep_term),
        ExistsIntro(deep_term, EqRefl(ZERO)),
        EqSubst(deep_motive, EqRefl(ZERO), EqRefl(ZERO)),
        Ind(deep_motive, EqRefl(ZERO), EqRefl(ZERO)),
    )
    limits = replace(
        layered.DEFAULT_LAYERED_REPLAY_LIMITS,
        max_formula_depth=3,
        max_body_annotation_occurrences=3,
    )
    for body in annotated_bodies:
        bundle = layered.LayeredReplayBundle(
            (layered.LayeredReplayNode(0, P, (), body),),
            0,
        )
        assert layered.compile_layered_replay(bundle, P, limits=limits) is None


def test_requested_target_is_charged_to_total_formula_limit() -> None:
    distinct_but_equal_target = Eq(Zero(), Zero())
    bundle = layered.LayeredReplayBundle(
        (layered.LayeredReplayNode(0, P, (), EqRefl(ZERO)),),
        0,
    )
    assert distinct_but_equal_target == P
    assert distinct_but_equal_target is not P
    assert (
        layered.compile_layered_replay(
            bundle,
            distinct_but_equal_target,
            limits=replace(
                layered.DEFAULT_LAYERED_REPLAY_LIMITS,
                max_total_formula_occurrences=3,
            ),
        )
        is None
    )


def test_invalid_topology_is_rejected_before_body_scanning(monkeypatch) -> None:
    original = _diamond_bundle(depth=2, width=2)
    leaf, *middle, root = original.nodes
    dangling = replace(
        original,
        nodes=tuple(middle) + (replace(root, dependencies=(999,)),),
    )
    cyclic_nodes = list(original.nodes)
    cyclic_nodes[0] = replace(leaf, dependencies=(original.root,))
    cyclic = replace(original, nodes=tuple(cyclic_nodes))
    unreachable = replace(
        original,
        nodes=original.nodes
        + (layered.LayeredReplayNode(99, Q, (), EqRefl(ONE)),),
    )

    def forbidden_body_scan(*_args, **_kwargs):
        raise AssertionError("body scan ran before malformed topology rejection")

    monkeypatch.setattr(
        layered,
        "_proof_envelope_metrics_bounded",
        forbidden_body_scan,
    )
    assert layered.compile_layered_replay(dangling, P) is None
    assert layered.compile_layered_replay(cyclic, P) is None
    assert layered.compile_layered_replay(unreachable, P) is None


def test_exact_557_node_qr_topology_surrogate_and_order_mutation() -> None:
    stack = quadratic_reciprocity_stack()
    names = tuple(spec.name for spec in stack.admission_order)
    positions = {name: index for index, name in enumerate(names)}
    dependencies = tuple(
        tuple(positions[name] for name in spec.dependencies)
        for spec in stack.admission_order
    )
    expected_layers = tuple(
        tuple(positions[spec.name] for spec in layer)
        for layer in stack.dependency_layers
    )
    targets: list[Formula] = [
        Eq(_marker(node_id), _marker(node_id)) for node_id in range(len(names))
    ]

    nodes: list[layered.LayeredReplayNode] = []
    for node_id, node_dependencies in enumerate(dependencies):
        node_target = targets[node_id]
        body: Proof = EqRefl(node_target.left)
        for dependency in reversed(node_dependencies):
            body = Cut(
                targets[dependency],
                node_target,
                Hyp(len(node_dependencies) - 1),
                body,
            )
        for _ in node_dependencies:
            body = ImpIntro(body)
        nodes.append(
            layered.LayeredReplayNode(
                node_id,
                node_target,
                node_dependencies,
                body,
            )
        )

    root = positions[QR_ROOT_NAME]
    bundle = layered.LayeredReplayBundle(tuple(nodes), root)
    target = targets[root]
    candidate = layered.compile_layered_replay(bundle, target)

    assert len(names) == 557
    assert len(expected_layers) == 45
    assert sum(map(len, dependencies)) == 1_792
    assert len(set(targets)) == 557
    assert candidate is not None
    assert candidate.layers == expected_layers
    assert candidate.package_formula_occurrences == 19_297
    assert candidate.maximum_package_formula_depth == 18
    assert (
        candidate.proof_nodes,
        candidate.proof_depth,
        candidate.proof_objects,
        candidate.proof_edges,
        candidate.reused_objects,
    ) == (19_099, 74, 19_099, 19_098, 0)
    assert (
        candidate.proof_annotation_occurrences,
        candidate.proof_envelope_depth,
    ) == (142_396, 84)
    assert check((), candidate.certificate, target)

    assert names[5] == "beta_range_empty"
    assert nodes[5].dependencies == (3, 4)
    swapped_nodes = list(nodes)
    swapped_nodes[5] = replace(swapped_nodes[5], dependencies=(4, 3))
    swapped = layered.compile_layered_replay(
        replace(bundle, nodes=tuple(swapped_nodes)),
        target,
    )
    assert swapped is not None
    assert not check((), swapped.certificate, target)
