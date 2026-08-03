"""Compatibility adapter and recursive baseline for layered replay.

The generic layered ordinary-proof builder now lives in
``peano_lab.library.layered_replay``.  This experimental module retains the
old ``ClosedBundle`` adapter and the recursive comparison only; it supplies no
logical authority and the fallback closed-DAG experiment remains isolated.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..engine.state import proof_resource_metrics
from ..kernel.formulas import Formula
from ..kernel.proofs import Cut, ImpIntro, Proof
from ..library.layered_replay import (
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayError,
    LayeredReplayLimits,
    LayeredReplayNode,
    compile_layered_replay,
)
from .closed_proof_dag import (
    ClosedBundle,
    ClosedDagLimits,
    ClosedNode,
    DEFAULT_LIMITS,
    _closed_formula_metrics,
    _proof_metrics_bounded,
    _require_positive_limits,
    _topological_order,
)


LayeredCutError = LayeredReplayError
LayeredCutCompilation = LayeredReplayCandidate


@dataclass(frozen=True, slots=True)
class RecursiveCutCompilation:
    """Diagnostic current-style recursive ``Cut`` closure for comparison."""

    certificate: Proof
    proof_nodes: int
    proof_depth: int
    proof_objects: int
    proof_edges: int
    reused_objects: int


def _production_limits(limits: ClosedDagLimits) -> LayeredReplayLimits:
    if type(limits) is not ClosedDagLimits:
        raise LayeredReplayError("limits must be an exact ClosedDagLimits value")
    return LayeredReplayLimits(
        max_nodes=limits.max_nodes,
        max_dependencies_per_node=limits.max_dependencies_per_node,
        max_dependency_edges=limits.max_dependency_edges,
        max_formula_occurrences_per_target=(
            limits.max_formula_occurrences_per_target
        ),
        max_total_formula_occurrences=limits.max_total_formula_occurrences,
        max_formula_depth=limits.max_formula_depth,
        max_body_occurrences=limits.max_body_occurrences,
        max_body_objects=limits.max_body_objects,
        max_body_depth=limits.max_body_depth,
        max_total_body_occurrences=limits.max_total_body_occurrences,
        max_total_body_objects=limits.max_total_body_objects,
    )


def _production_bundle(bundle: ClosedBundle) -> LayeredReplayBundle:
    if type(bundle) is not ClosedBundle:
        raise LayeredReplayError("bundle must be an exact ClosedBundle value")
    if type(bundle.classical) is not bool or bundle.classical:
        raise LayeredReplayError(
            "production layered replay accepts constructive bundles only"
        )
    if type(bundle.nodes) is not tuple:
        raise LayeredReplayError("bundle nodes must be a tuple")
    nodes: list[LayeredReplayNode] = []
    for node in bundle.nodes:
        if type(node) is not ClosedNode:
            raise LayeredReplayError(
                "bundle entries must be exact ClosedNode values"
            )
        nodes.append(
            LayeredReplayNode(
                node.node_id,
                node.target,
                node.dependencies,
                node.body,
            )
        )
    return LayeredReplayBundle(tuple(nodes), bundle.root)


def compile_layered_cut_bundle(
    bundle: object,
    target: object,
    *,
    limits: ClosedDagLimits = DEFAULT_LIMITS,
) -> LayeredCutCompilation | None:
    """Adapt an old constructive ``ClosedBundle`` to production replay."""

    try:
        production_bundle = _production_bundle(bundle)  # type: ignore[arg-type]
        production_limits = _production_limits(limits)
    except (
        AttributeError,
        LayeredReplayError,
        TypeError,
        ValueError,
    ):
        return None
    return compile_layered_replay(
        production_bundle,
        target,
        limits=production_limits,
    )


def _validate_recursive_graph(
    bundle: object,
    target: object,
    limits: ClosedDagLimits,
) -> tuple[dict[int, ClosedNode], tuple[int, ...]]:
    """Validate the isolated recursive comparison without using production."""

    _require_positive_limits(limits)
    if type(bundle) is not ClosedBundle:
        raise LayeredReplayError("bundle must be an exact ClosedBundle value")
    if type(bundle.nodes) is not tuple or not bundle.nodes:
        raise LayeredReplayError("bundle nodes must be a non-empty tuple")
    if len(bundle.nodes) > limits.max_nodes:
        raise LayeredReplayError("bundle exceeds its node limit")
    if type(bundle.root) is not int or bundle.root < 0:
        raise LayeredReplayError(
            "root must be a non-negative integer node ID"
        )
    if type(bundle.classical) is not bool:
        raise LayeredReplayError("classical mode must be an exact boolean")

    table: dict[int, ClosedNode] = {}
    formula_occurrences = 0
    body_occurrences = 0
    body_objects = 0
    for node in bundle.nodes:
        if type(node) is not ClosedNode:
            raise LayeredReplayError(
                "bundle entries must be exact ClosedNode values"
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
        occurrences, objects, _ = _proof_metrics_bounded(
            node.body,
            max_occurrences=limits.max_body_occurrences,
            max_objects=limits.max_body_objects,
            max_depth=limits.max_body_depth,
        )
        body_occurrences += occurrences
        body_objects += objects
        if body_occurrences > limits.max_total_body_occurrences:
            raise LayeredReplayError(
                "bundle exceeds its body-occurrence limit"
            )
        if body_objects > limits.max_total_body_objects:
            raise LayeredReplayError("bundle exceeds its body-object limit")
        table[node.node_id] = node

    _closed_formula_metrics(
        target,
        max_occurrences=limits.max_formula_occurrences_per_target,
        max_depth=limits.max_formula_depth,
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
    return table, order


def _compile_recursive_cut_bundle(
    bundle: ClosedBundle,
    target: Formula,
    limits: ClosedDagLimits,
) -> RecursiveCutCompilation:
    table, order = _validate_recursive_graph(bundle, target, limits)
    closed: dict[int, Proof] = {}
    for node_id in order:
        node = table[node_id]
        proof = node.body
        for _ in node.dependencies:
            if type(proof) is not ImpIntro:
                raise LayeredReplayError(
                    "recursive Cut baseline needs exposed dependency introductions"
                )
            proof = proof.body
        for dependency in reversed(node.dependencies):
            proof = Cut(
                table[dependency].target,
                node.target,
                closed[dependency],
                proof,
            )
        closed[node_id] = proof
    certificate = closed[bundle.root]
    nodes, depth, objects, edges, reused = proof_resource_metrics(certificate)
    return RecursiveCutCompilation(
        certificate,
        nodes,
        depth,
        objects,
        edges,
        reused,
    )


def compile_recursive_cut_bundle(
    bundle: object,
    target: object,
    *,
    limits: ClosedDagLimits = DEFAULT_LIMITS,
) -> RecursiveCutCompilation | None:
    """Build the isolated recursive comparison; never admission authority."""

    try:
        return _compile_recursive_cut_bundle(
            bundle, target, limits  # type: ignore[arg-type]
        )
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
    "LayeredCutError",
    "LayeredCutCompilation",
    "RecursiveCutCompilation",
    "compile_layered_cut_bundle",
    "compile_recursive_cut_bundle",
]
