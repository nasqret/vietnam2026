"""Build one ordinary layered ``Cut`` proof from modular proof bodies.

This module is an untrusted constructive proof compiler.  It validates a
finite local-ID graph, packages dependency layers as balanced conjunctions,
and returns a certificate containing only existing kernel ``Proof``
constructors and no ``DNE`` node.  The returned
:class:`LayeredReplayCandidate` is not theorem authority: a caller must still
ask the unchanged intuitionistic kernel to check its certificate from the
empty context against the exact requested target.

The input contains no theorem names, registry references, source hashes, or
content-addressed proof references.  Importing this module registers nothing
and does not change the proof grammar, checker, or tactic engine.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import heapq

from ..engine.state import proof_identity_metrics
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import (
    AndElimL,
    AndElimR,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    Cut,
    DNE,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
    Proof,
)
from ..kernel.terms import Add, Mul, Succ, Var, Zero


class LayeredReplayError(ValueError):
    """The input cannot be compiled to a canonical layered certificate."""


@dataclass(frozen=True, slots=True)
class LayeredReplayLimits:
    """Fail-closed availability limits for the untrusted compiler.

    Structural occurrences charge every incoming reference.  Proof nodes and
    their embedded formula/term annotations have separate occurrence limits,
    while envelope depth bounds their combined nesting.  Identity counts
    separately bound the immutable proof objects retained by modular bodies.
    None of these resource checks grants logical authority.
    """

    max_nodes: int = 4_096
    max_dependencies_per_node: int = 256
    max_dependency_edges: int = 65_536
    max_formula_occurrences_per_target: int = 100_000
    max_total_formula_occurrences: int = 500_000
    max_formula_depth: int = 256
    max_body_occurrences: int = 500_000
    max_body_objects: int = 100_000
    max_body_depth: int = 256
    max_body_annotation_occurrences: int = 500_000
    max_body_envelope_depth: int = 256
    max_total_body_occurrences: int = 5_000_000
    max_total_body_objects: int = 500_000
    max_total_body_annotation_occurrences: int = 5_000_000
    max_package_formula_occurrences: int = 500_000
    max_package_formula_depth: int = 256
    max_candidate_proof_occurrences: int = 500_000
    max_candidate_proof_objects: int = 100_000
    max_candidate_proof_depth: int = 256
    max_candidate_annotation_occurrences: int = 5_000_000
    max_candidate_envelope_depth: int = 256


DEFAULT_LAYERED_REPLAY_LIMITS = LayeredReplayLimits()


@dataclass(frozen=True, slots=True)
class LayeredReplayNode:
    """One local-ID target and its dependency-curried ordinary proof body.

    If ``dependencies`` is ``(d0, ..., dn)``, ``body`` is intended to prove
    ``target[d0] -> ... -> target[dn] -> target`` in that exact order.  This
    compiler merely wires those implications into an ordinary proof; the
    unchanged kernel remains the authority that checks the result.
    """

    node_id: int
    target: Formula
    dependencies: tuple[int, ...]
    body: Proof


@dataclass(frozen=True, slots=True)
class LayeredReplayBundle:
    """A complete constructive graph and one designated local-ID root."""

    nodes: tuple[LayeredReplayNode, ...]
    root: int


@dataclass(frozen=True, slots=True)
class LayeredReplayCandidate:
    """Untrusted constructive proof plus deterministic envelope diagnostics."""

    certificate: Proof
    target: Formula
    layers: tuple[tuple[int, ...], ...]
    package_formulas: tuple[Formula, ...]
    package_formula_occurrences: int
    maximum_package_formula_depth: int
    proof_nodes: int
    proof_depth: int
    proof_objects: int
    proof_edges: int
    reused_objects: int
    proof_annotation_occurrences: int
    proof_envelope_depth: int


def _require_positive_limits(limits: LayeredReplayLimits) -> None:
    if type(limits) is not LayeredReplayLimits:
        raise LayeredReplayError(
            "limits must be an exact LayeredReplayLimits value"
        )
    for item in fields(limits):
        value = getattr(limits, item.name)
        if type(value) is not int or value <= 0:
            raise LayeredReplayError(f"{item.name} must be a positive integer")


def _closed_formula_metrics(
    formula: object,
    *,
    max_occurrences: int,
    max_depth: int,
) -> tuple[int, int]:
    """Validate an exact closed PA formula and return occurrences/depth."""

    pending: list[tuple[object, int, int, bool]] = [(formula, 0, 1, True)]
    occurrences = 0
    maximum_depth = 0
    while pending:
        value, binders, depth, is_formula = pending.pop()
        occurrences += 1
        maximum_depth = max(maximum_depth, depth)
        if occurrences > max_occurrences:
            raise LayeredReplayError(
                "target formula exceeds its occurrence limit"
            )
        if depth > max_depth:
            raise LayeredReplayError("target formula exceeds its depth limit")

        if is_formula:
            if type(value) is Eq:
                pending.append((value.right, binders, depth + 1, False))
                pending.append((value.left, binders, depth + 1, False))
            elif type(value) is Bot:
                continue
            elif type(value) in (Imp, And, Or):
                pending.append((value.right, binders, depth + 1, True))
                pending.append((value.left, binders, depth + 1, True))
            elif type(value) in (Forall, Exists):
                pending.append((value.body, binders + 1, depth + 1, True))
            else:
                raise LayeredReplayError(
                    "target contains a non-kernel formula node"
                )
            continue

        if type(value) is Var:
            if (
                type(value.index) is not int
                or value.index < 0
                or value.index >= binders
            ):
                raise LayeredReplayError(
                    "target formula contains a free term variable"
                )
        elif type(value) is Zero:
            continue
        elif type(value) is Succ:
            pending.append((value.term, binders, depth + 1, False))
        elif type(value) in (Add, Mul):
            pending.append((value.right, binders, depth + 1, False))
            pending.append((value.left, binders, depth + 1, False))
        else:
            raise LayeredReplayError("target contains a non-kernel term node")
    return occurrences, maximum_depth


def _proof_envelope_metrics_bounded(
    proof: object,
    *,
    max_proof_occurrences: int,
    max_proof_objects: int,
    max_proof_depth: int,
    max_annotation_occurrences: int,
    max_annotation_depth: int,
    max_envelope_depth: int,
    label: str,
) -> tuple[int, int, int, int, int]:
    """Validate and measure one complete constructive proof envelope.

    Proof occurrences and immutable proof identities retain the existing
    metrics.  Every formula or term annotation is additionally traversed for
    every incoming reference.  Annotation variables need only be exact
    non-negative kernel variables: motives and terms inside a proof may be
    open relative to surrounding proof binders, and the kernel remains the
    authority for that scoping judgment.
    """

    _PROOF = 0
    _FORMULA = 1
    _TERM = 2
    pending: list[tuple[int, object, int, int]] = [(_PROOF, proof, 1, 0)]
    proof_occurrences = 0
    annotation_occurrences = 0
    maximum_proof_depth = 0
    maximum_envelope_depth = 0
    proof_identities: set[int] = set()
    while pending:
        kind, value, depth, annotation_depth = pending.pop()
        maximum_envelope_depth = max(maximum_envelope_depth, depth)
        if depth > max_envelope_depth:
            raise LayeredReplayError(
                f"{label} exceeds its combined proof-envelope depth limit"
            )

        if kind == _PROOF:
            node_type = type(value)
            proof_occurrences += 1
            maximum_proof_depth = max(maximum_proof_depth, depth)
            proof_identities.add(id(value))
            if proof_occurrences > max_proof_occurrences:
                raise LayeredReplayError(
                    f"{label} exceeds its proof-occurrence limit"
                )
            if len(proof_identities) > max_proof_objects:
                raise LayeredReplayError(f"{label} exceeds its proof-object limit")
            if depth > max_proof_depth:
                raise LayeredReplayError(f"{label} exceeds its proof-depth limit")

            proof_children: tuple[object, ...]
            annotations: tuple[tuple[int, object], ...] = ()
            if node_type is Hyp:
                if type(value.i) is not int or value.i < 0:
                    raise LayeredReplayError(
                        f"{label} contains a malformed Hyp index"
                    )
                proof_children = ()
            elif node_type is Axiom:
                if type(value.name) is not str or value.name not in {
                    "PA1",
                    "PA2",
                    "PA3",
                    "PA4",
                    "PA5",
                    "PA6",
                }:
                    raise LayeredReplayError(
                        f"{label} contains an unknown arithmetic axiom"
                    )
                proof_children = ()
            elif node_type is DNE:
                raise LayeredReplayError(
                    f"{label} contains DNE in constructive layered replay"
                )
            elif node_type is ImpIntro:
                proof_children = (value.body,)
            elif node_type is ImpElim:
                proof_children = (value.f, value.a)
            elif node_type is Cut:
                proof_children = (value.lemma, value.body)
                annotations = (
                    (_FORMULA, value.proposition),
                    (_FORMULA, value.conclusion),
                )
            elif node_type is AndIntro:
                proof_children = (value.left, value.right)
            elif node_type in (AndElimL, AndElimR):
                proof_children = (value.pair,)
            elif node_type in (OrIntroL, OrIntroR):
                proof_children = (value.proof,)
            elif node_type is OrElim:
                proof_children = (
                    value.disjunction,
                    value.left_case,
                    value.right_case,
                )
            elif node_type is BotElim:
                proof_children = (value.absurdity,)
            elif node_type is ForallIntro:
                proof_children = (value.body,)
            elif node_type is ForallElim:
                proof_children = (value.p,)
                annotations = ((_TERM, value.t),)
            elif node_type is ExistsIntro:
                proof_children = (value.p,)
                annotations = ((_TERM, value.t),)
            elif node_type is ExistsElim:
                proof_children = (value.p, value.body)
            elif node_type is EqRefl:
                proof_children = ()
                annotations = ((_TERM, value.t),)
            elif node_type is EqSym:
                proof_children = (value.proof,)
            elif node_type is EqTrans:
                proof_children = (value.first, value.second)
            elif node_type is CongS:
                proof_children = (value.proof,)
            elif node_type in (CongAdd, CongMul):
                proof_children = (value.left, value.right)
            elif node_type is EqSubst:
                proof_children = (value.eq_proof, value.body_proof)
                annotations = ((_FORMULA, value.motive),)
            elif node_type is Ind:
                proof_children = (value.base, value.step)
                annotations = ((_FORMULA, value.motive),)
            else:
                raise LayeredReplayError(
                    f"{label} contains a non-kernel proof constructor"
                )

            pending.extend(
                (_PROOF, child, depth + 1, 0)
                for child in proof_children
            )
            pending.extend(
                (annotation_kind, annotation, depth + 1, 1)
                for annotation_kind, annotation in annotations
            )
            continue

        annotation_occurrences += 1
        if annotation_occurrences > max_annotation_occurrences:
            raise LayeredReplayError(
                f"{label} exceeds its formula/term-annotation occurrence limit"
            )
        if annotation_depth > max_annotation_depth:
            raise LayeredReplayError(
                f"{label} exceeds its formula/term-annotation depth limit"
            )

        if kind == _FORMULA:
            if type(value) is Eq:
                pending.append((_TERM, value.right, depth + 1, annotation_depth + 1))
                pending.append((_TERM, value.left, depth + 1, annotation_depth + 1))
            elif type(value) is Bot:
                continue
            elif type(value) in (Imp, And, Or):
                pending.append(
                    (_FORMULA, value.right, depth + 1, annotation_depth + 1)
                )
                pending.append(
                    (_FORMULA, value.left, depth + 1, annotation_depth + 1)
                )
            elif type(value) in (Forall, Exists):
                pending.append(
                    (_FORMULA, value.body, depth + 1, annotation_depth + 1)
                )
            else:
                raise LayeredReplayError(
                    f"{label} contains a non-kernel formula annotation"
                )
            continue

        if kind != _TERM:
            raise LayeredReplayError(f"{label} contains an invalid envelope tag")
        if type(value) is Var:
            if type(value.index) is not int or value.index < 0:
                raise LayeredReplayError(
                    f"{label} contains a malformed term variable annotation"
                )
        elif type(value) is Zero:
            continue
        elif type(value) is Succ:
            pending.append((_TERM, value.term, depth + 1, annotation_depth + 1))
        elif type(value) in (Add, Mul):
            pending.append((_TERM, value.right, depth + 1, annotation_depth + 1))
            pending.append((_TERM, value.left, depth + 1, annotation_depth + 1))
        else:
            raise LayeredReplayError(
                f"{label} contains a non-kernel term annotation"
            )
    return (
        proof_occurrences,
        len(proof_identities),
        maximum_proof_depth,
        annotation_occurrences,
        maximum_envelope_depth,
    )


def _topological_order(
    nodes: dict[int, LayeredReplayNode],
    *,
    edge_limit: int,
    dependency_limit: int,
) -> tuple[tuple[int, ...], int]:
    dependents: dict[int, list[int]] = {node_id: [] for node_id in nodes}
    indegree: dict[int, int] = {}
    edges = 0
    for node_id, node in nodes.items():
        if type(node.dependencies) is not tuple:
            raise LayeredReplayError(
                "dependencies must be a tuple of integer node IDs"
            )
        if len(node.dependencies) > dependency_limit:
            raise LayeredReplayError("node exceeds its dependency limit")
        if not all(type(dependency) is int for dependency in node.dependencies):
            raise LayeredReplayError(
                "dependencies must be a tuple of integer node IDs"
            )
        if len(set(node.dependencies)) != len(node.dependencies):
            raise LayeredReplayError(
                "duplicate dependency references are not canonical"
            )
        edges += len(node.dependencies)
        if edges > edge_limit:
            raise LayeredReplayError(
                "bundle exceeds its dependency-edge limit"
            )
        indegree[node_id] = len(node.dependencies)
        for dependency in node.dependencies:
            if dependency not in nodes:
                raise LayeredReplayError(
                    f"dangling dependency reference {dependency}"
                )
            dependents[dependency].append(node_id)

    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered: list[int] = []
    while ready:
        node_id = heapq.heappop(ready)
        ordered.append(node_id)
        for dependent in sorted(dependents[node_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(ordered) != len(nodes):
        raise LayeredReplayError("dependency graph contains a cycle")
    return tuple(ordered), edges


def _validate_graph(
    bundle: object,
    target: object,
    limits: LayeredReplayLimits,
) -> tuple[dict[int, LayeredReplayNode], tuple[int, ...]]:
    _require_positive_limits(limits)
    if type(bundle) is not LayeredReplayBundle:
        raise LayeredReplayError(
            "bundle must be an exact LayeredReplayBundle value"
        )
    if type(bundle.nodes) is not tuple or not bundle.nodes:
        raise LayeredReplayError("bundle nodes must be a non-empty tuple")
    if len(bundle.nodes) > limits.max_nodes:
        raise LayeredReplayError("bundle exceeds its node limit")
    if type(bundle.root) is not int or bundle.root < 0:
        raise LayeredReplayError(
            "root must be a non-negative integer node ID"
        )

    table: dict[int, LayeredReplayNode] = {}
    formula_occurrences = 0
    for node in bundle.nodes:
        if type(node) is not LayeredReplayNode:
            raise LayeredReplayError(
                "bundle entries must be exact LayeredReplayNode values"
            )
        if type(node.node_id) is not int or not 0 <= node.node_id < 2**31:
            raise LayeredReplayError(
                "node IDs must be 31-bit non-negative integers"
            )
        if node.node_id in table:
            raise LayeredReplayError(f"duplicate node ID {node.node_id}")
        occurrences, _ = _closed_formula_metrics(
            node.target,
            max_occurrences=limits.max_formula_occurrences_per_target,
            max_depth=limits.max_formula_depth,
        )
        formula_occurrences += occurrences
        if formula_occurrences > limits.max_total_formula_occurrences:
            raise LayeredReplayError(
                "bundle exceeds its formula-occurrence limit"
            )
        table[node.node_id] = node

    requested_occurrences, _ = _closed_formula_metrics(
        target,
        max_occurrences=limits.max_formula_occurrences_per_target,
        max_depth=limits.max_formula_depth,
    )
    formula_occurrences += requested_occurrences
    if formula_occurrences > limits.max_total_formula_occurrences:
        raise LayeredReplayError(
            "bundle and requested target exceed their formula-occurrence limit"
        )
    if bundle.root not in table:
        raise LayeredReplayError("root is a dangling node reference")
    if table[bundle.root].target != target:
        raise LayeredReplayError(
            "root target does not match the requested target"
        )
    order, _ = _topological_order(
        table,
        edge_limit=limits.max_dependency_edges,
        dependency_limit=limits.max_dependencies_per_node,
    )

    reachable: set[int] = set()
    pending = [bundle.root]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(table[node_id].dependencies)
    if reachable != set(table):
        raise LayeredReplayError(
            "canonical bundle contains nodes unreachable from the root"
        )

    body_occurrences = 0
    body_objects = 0
    body_annotation_occurrences = 0
    for node_id in order:
        (
            occurrences,
            objects,
            _proof_depth,
            annotation_occurrences,
            _envelope_depth,
        ) = _proof_envelope_metrics_bounded(
            table[node_id].body,
            max_proof_occurrences=limits.max_body_occurrences,
            max_proof_objects=limits.max_body_objects,
            max_proof_depth=limits.max_body_depth,
            max_annotation_occurrences=(
                limits.max_body_annotation_occurrences
            ),
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_body_envelope_depth,
            label="node body",
        )
        body_occurrences += occurrences
        body_objects += objects
        body_annotation_occurrences += annotation_occurrences
        if body_occurrences > limits.max_total_body_occurrences:
            raise LayeredReplayError(
                "bundle exceeds its body-occurrence limit"
            )
        if body_objects > limits.max_total_body_objects:
            raise LayeredReplayError("bundle exceeds its body-object limit")
        if (
            body_annotation_occurrences
            > limits.max_total_body_annotation_occurrences
        ):
            raise LayeredReplayError(
                "bundle exceeds its body formula/term-annotation limit"
            )
    return table, order


def _layers(
    table: dict[int, LayeredReplayNode], order: tuple[int, ...]
) -> tuple[tuple[tuple[int, ...], ...], dict[int, int]]:
    depths: dict[int, int] = {}
    for node_id in order:
        dependencies = table[node_id].dependencies
        depths[node_id] = (
            0
            if not dependencies
            else 1 + max(depths[item] for item in dependencies)
        )
    grouped: list[list[int]] = [
        [] for _ in range(1 + max(depths.values(), default=0))
    ]
    for node_id in sorted(table):
        grouped[depths[node_id]].append(node_id)
    return tuple(tuple(layer) for layer in grouped), depths


def _balanced_package(
    entries: tuple[tuple[int, Formula, Proof], ...]
) -> tuple[Formula, Proof, dict[int, tuple[bool, ...]]]:
    if not entries:
        raise LayeredReplayError("a theorem layer cannot be empty")
    if len(entries) == 1:
        node_id, formula, proof = entries[0]
        return formula, proof, {node_id: ()}
    middle = len(entries) // 2
    left_formula, left_proof, left_paths = _balanced_package(entries[:middle])
    right_formula, right_proof, right_paths = _balanced_package(entries[middle:])
    paths = {
        **{
            node_id: (False,) + path
            for node_id, path in left_paths.items()
        },
        **{
            node_id: (True,) + path
            for node_id, path in right_paths.items()
        },
    }
    return (
        And(left_formula, right_formula),
        AndIntro(left_proof, right_proof),
        paths,
    )


def _project(package_hypothesis: int, path: tuple[bool, ...]) -> Proof:
    proof: Proof = Hyp(package_hypothesis)
    for right in path:
        proof = AndElimR(proof) if right else AndElimL(proof)
    return proof


def _compile_layered_replay(
    bundle: LayeredReplayBundle,
    target: Formula,
    limits: LayeredReplayLimits,
) -> LayeredReplayCandidate:
    table, order = _validate_graph(bundle, target, limits)
    layers, depth_of = _layers(table, order)
    package_formulas: list[Formula] = []
    package_proofs: list[Proof] = []
    package_paths: list[dict[int, tuple[bool, ...]]] = []

    for layer_index, layer in enumerate(layers):
        theorem_entries: list[tuple[int, Formula, Proof]] = []
        for node_id in layer:
            node = table[node_id]
            theorem_proof = node.body
            for dependency in node.dependencies:
                dependency_layer = depth_of[dependency]
                if dependency_layer >= layer_index:
                    raise LayeredReplayError(
                        "dependency does not occur in an earlier layer"
                    )
                context_index = layer_index - 1 - dependency_layer
                dependency_proof = _project(
                    context_index,
                    package_paths[dependency_layer][dependency],
                )
                theorem_proof = ImpElim(theorem_proof, dependency_proof)
            theorem_entries.append((node_id, node.target, theorem_proof))

        package_formula, package_proof, paths = _balanced_package(
            tuple(theorem_entries)
        )
        package_formulas.append(package_formula)
        package_proofs.append(package_proof)
        package_paths.append(paths)

    package_formula_occurrences = 0
    maximum_package_formula_depth = 0
    for package_formula in package_formulas:
        occurrences, depth = _closed_formula_metrics(
            package_formula,
            max_occurrences=limits.max_package_formula_occurrences,
            max_depth=limits.max_package_formula_depth,
        )
        package_formula_occurrences += occurrences
        if (
            package_formula_occurrences
            > limits.max_package_formula_occurrences
        ):
            raise LayeredReplayError(
                "layer packages exceed their formula-occurrence limit"
            )
        maximum_package_formula_depth = max(
            maximum_package_formula_depth, depth
        )

    root_layer = depth_of[bundle.root]
    final: Proof = _project(
        len(layers) - 1 - root_layer,
        package_paths[root_layer][bundle.root],
    )
    for layer_index in reversed(range(len(layers))):
        final = Cut(
            package_formulas[layer_index],
            target,
            package_proofs[layer_index],
            final,
        )

    (
        nodes,
        bounded_objects,
        depth,
        candidate_annotation_occurrences,
        candidate_envelope_depth,
    ) = _proof_envelope_metrics_bounded(
        final,
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=(
            limits.max_candidate_annotation_occurrences
        ),
        max_annotation_depth=max(
            limits.max_formula_depth,
            limits.max_package_formula_depth,
        ),
        max_envelope_depth=limits.max_candidate_envelope_depth,
        label="candidate proof",
    )
    objects, edges, reused = proof_identity_metrics(final)
    if objects != bounded_objects:
        raise LayeredReplayError(
            "candidate proof object metrics are internally inconsistent"
        )
    return LayeredReplayCandidate(
        certificate=final,
        target=target,
        layers=layers,
        package_formulas=tuple(package_formulas),
        package_formula_occurrences=package_formula_occurrences,
        maximum_package_formula_depth=maximum_package_formula_depth,
        proof_nodes=nodes,
        proof_depth=depth,
        proof_objects=objects,
        proof_edges=edges,
        reused_objects=reused,
        proof_annotation_occurrences=candidate_annotation_occurrences,
        proof_envelope_depth=candidate_envelope_depth,
    )


def compile_layered_replay(
    bundle: object,
    target: object,
    *,
    limits: LayeredReplayLimits = DEFAULT_LAYERED_REPLAY_LIMITS,
) -> LayeredReplayCandidate | None:
    """Fail closed while building an untrusted ordinary proof candidate."""

    try:
        return _compile_layered_replay(bundle, target, limits)  # type: ignore[arg-type]
    except (
        AttributeError,
        IndexError,
        KeyError,
        LayeredReplayError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return None


__all__ = [
    "LayeredReplayError",
    "LayeredReplayLimits",
    "DEFAULT_LAYERED_REPLAY_LIMITS",
    "LayeredReplayNode",
    "LayeredReplayBundle",
    "LayeredReplayCandidate",
    "compile_layered_replay",
]
