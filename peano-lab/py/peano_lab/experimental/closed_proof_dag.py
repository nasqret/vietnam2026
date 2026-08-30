"""Executable prototype of a self-contained closed-proof DAG.

This module deliberately does not add a proof constructor to
``peano_lab.kernel.proofs`` and does not change the ordinary checker.  A bundle
node stores an ordinary proof of its dependency-curried target.  The existing
kernel checks that proof once from the empty context.  Previously established
nodes discharge the curried premises by the meta-level repeated-modus-ponens
argument documented in ``research/arithmetic-library/closed-proof-dag.md``.

The prototype is an architecture experiment, not an admission path.  In
particular, importing this module does not register a theorem and a returned
receipt is not accepted by the production kernel or tactic engine.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import heapq

from ..kernel import checker as kernel_checker
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import Proof
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


class ClosedDagError(ValueError):
    """A bundle violates the closed-DAG checking contract."""


@dataclass(frozen=True, slots=True)
class ClosedDagLimits:
    """Availability policy for the in-memory architecture prototype.

    Structural occurrences are charged on every incoming edge.  Object counts
    are charged separately for each body, matching a future streaming decoder
    that releases a body after checking it.  None of these bounds grants proof
    authority; they only reject expensive input before recursive kernel work.
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
    max_total_body_occurrences: int = 5_000_000
    max_total_body_objects: int = 500_000


DEFAULT_LIMITS = ClosedDagLimits()


@dataclass(frozen=True, slots=True)
class ClosedNode:
    """One locally identified, dependency-curried closed proof body.

    ``node_id`` is a bundle-local integer reference, never a theorem name or a
    content hash.  If dependencies ``d0, ..., dn`` conclude ``A0, ..., An``,
    ``body`` must kernel-check from ``()`` against
    ``A0 -> ... -> An -> target`` in exactly the listed order.
    """

    node_id: int
    target: Formula
    dependencies: tuple[int, ...]
    body: Proof


@dataclass(frozen=True, slots=True)
class ClosedBundle:
    """A complete finite graph and one designated root.

    One logic mode applies to every node.  A classical body therefore cannot
    be smuggled into an intuitionistic bundle through a dependency edge.
    """

    nodes: tuple[ClosedNode, ...]
    root: int
    classical: bool = False


@dataclass(frozen=True, slots=True)
class CheckedNodeReceipt:
    """Non-authoritative diagnostics for one successful kernel call."""

    node_id: int
    dependencies: tuple[int, ...]
    body_occurrences: int
    body_objects: int
    body_depth: int


@dataclass(frozen=True, slots=True)
class ClosedBundleReceipt:
    """Diagnostics returned only after the whole bundle succeeds.

    The receipt is deliberately not a proof object and the production kernel
    has no rule that consumes it.
    """

    root: int
    target: Formula
    classical: bool
    topological_order: tuple[int, ...]
    dependency_edges: int
    formula_occurrences: int
    body_occurrences: int
    body_objects: int
    maximum_body_depth: int
    nodes: tuple[CheckedNodeReceipt, ...]


def _require_positive_limits(limits: ClosedDagLimits) -> None:
    if type(limits) is not ClosedDagLimits:
        raise ClosedDagError("limits must be an exact ClosedDagLimits value")
    for item in fields(limits):
        value = getattr(limits, item.name)
        if type(value) is not int or value <= 0:
            raise ClosedDagError(f"{item.name} must be a positive integer")


def _closed_formula_metrics(
    formula: object,
    *,
    max_occurrences: int,
    max_depth: int,
) -> tuple[int, int]:
    """Validate a closed exact PA formula and return occurrences/depth.

    The traversal is iterative and charges sharing structurally, so cyclic or
    adversarially shared objects cannot evade either limit.  A variable is
    accepted only below a matching formula binder.
    """

    pending: list[tuple[object, int, int, bool]] = [(formula, 0, 1, True)]
    occurrences = 0
    maximum_depth = 0
    while pending:
        value, binders, depth, is_formula = pending.pop()
        occurrences += 1
        maximum_depth = max(maximum_depth, depth)
        if occurrences > max_occurrences:
            raise ClosedDagError("target formula exceeds its occurrence limit")
        if depth > max_depth:
            raise ClosedDagError("target formula exceeds its depth limit")

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
                raise ClosedDagError("target contains a non-kernel formula node")
            continue

        if type(value) is Var:
            if (
                type(value.index) is not int
                or value.index < 0
                or value.index >= binders
            ):
                raise ClosedDagError("target formula contains a free term variable")
        elif type(value) is Zero:
            continue
        elif type(value) is Succ:
            pending.append((value.term, binders, depth + 1, False))
        elif type(value) in (Add, Mul):
            pending.append((value.right, binders, depth + 1, False))
            pending.append((value.left, binders, depth + 1, False))
        else:
            raise ClosedDagError("target contains a non-kernel term node")
    return occurrences, maximum_depth


def _proof_metrics_bounded(
    proof: object,
    *,
    max_occurrences: int,
    max_objects: int,
    max_depth: int,
) -> tuple[int, int, int]:
    """Preflight one ordinary proof without trusting Python object identity."""

    if not isinstance(proof, Proof):
        raise ClosedDagError("node body must be a kernel Proof value")
    pending: list[tuple[Proof, int]] = [(proof, 1)]
    occurrences = 0
    maximum_depth = 0
    identities: set[int] = set()
    while pending:
        node, depth = pending.pop()
        occurrences += 1
        maximum_depth = max(maximum_depth, depth)
        identities.add(id(node))
        if occurrences > max_occurrences:
            raise ClosedDagError("node body exceeds its occurrence limit")
        if len(identities) > max_objects:
            raise ClosedDagError("node body exceeds its object limit")
        if depth > max_depth:
            raise ClosedDagError("node body exceeds its depth limit")
        try:
            children = [
                child
                for item in fields(node)
                if isinstance((child := getattr(node, item.name)), Proof)
            ]
        except (AttributeError, TypeError, ValueError) as exc:
            raise ClosedDagError("node body contains a malformed proof object") from exc
        pending.extend((child, depth + 1) for child in children)
    return occurrences, len(identities), maximum_depth


def _topological_order(
    nodes: dict[int, ClosedNode],
    *,
    edge_limit: int,
    dependency_limit: int,
) -> tuple[tuple[int, ...], int]:
    """Validate references and return a deterministic topological order."""

    dependents: dict[int, list[int]] = {node_id: [] for node_id in nodes}
    indegree: dict[int, int] = {}
    edges = 0
    for node_id, node in nodes.items():
        if type(node.dependencies) is not tuple or not all(
            type(dependency) is int for dependency in node.dependencies
        ):
            raise ClosedDagError("dependencies must be a tuple of integer node IDs")
        if len(node.dependencies) > dependency_limit:
            raise ClosedDagError("node exceeds its dependency limit")
        if len(set(node.dependencies)) != len(node.dependencies):
            raise ClosedDagError("duplicate dependency references are not canonical")
        edges += len(node.dependencies)
        if edges > edge_limit:
            raise ClosedDagError("bundle exceeds its dependency-edge limit")
        indegree[node_id] = len(node.dependencies)
        for dependency in node.dependencies:
            if dependency not in nodes:
                raise ClosedDagError(f"dangling dependency reference {dependency}")
            dependents[dependency].append(node_id)

    ready = list(node_id for node_id, degree in indegree.items() if degree == 0)
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
        raise ClosedDagError("dependency graph contains a cycle")
    return tuple(ordered), edges


def _check_closed_bundle(
    bundle: ClosedBundle,
    target: Formula,
    limits: ClosedDagLimits,
) -> ClosedBundleReceipt:
    """Strict implementation behind the fail-closed public boundary."""

    _require_positive_limits(limits)
    if type(bundle) is not ClosedBundle:
        raise ClosedDagError("bundle must be an exact ClosedBundle value")
    if type(bundle.nodes) is not tuple:
        raise ClosedDagError("bundle nodes must be a tuple")
    if not bundle.nodes or len(bundle.nodes) > limits.max_nodes:
        raise ClosedDagError("bundle has an invalid number of nodes")
    if type(bundle.root) is not int or bundle.root < 0:
        raise ClosedDagError("root must be a non-negative integer node ID")
    if type(bundle.classical) is not bool:
        raise ClosedDagError("classical mode must be an exact boolean")

    table: dict[int, ClosedNode] = {}
    formula_occurrences = 0
    for node in bundle.nodes:
        if type(node) is not ClosedNode:
            raise ClosedDagError("bundle entries must be exact ClosedNode values")
        if type(node.node_id) is not int or not 0 <= node.node_id < 2**31:
            raise ClosedDagError("node IDs must be 31-bit non-negative integers")
        if node.node_id in table:
            raise ClosedDagError(f"duplicate node ID {node.node_id}")
        occurrences, _ = _closed_formula_metrics(
            node.target,
            max_occurrences=limits.max_formula_occurrences_per_target,
            max_depth=limits.max_formula_depth,
        )
        formula_occurrences += occurrences
        if formula_occurrences > limits.max_total_formula_occurrences:
            raise ClosedDagError("bundle exceeds its total formula-occurrence limit")
        table[node.node_id] = node

    requested_occurrences, _ = _closed_formula_metrics(
        target,
        max_occurrences=limits.max_formula_occurrences_per_target,
        max_depth=limits.max_formula_depth,
    )
    formula_occurrences += requested_occurrences
    if formula_occurrences > limits.max_total_formula_occurrences:
        raise ClosedDagError("bundle exceeds its total formula-occurrence limit")
    if bundle.root not in table:
        raise ClosedDagError("root is a dangling node reference")
    if table[bundle.root].target != target:
        raise ClosedDagError("designated root target does not match requested target")

    order, dependency_edges = _topological_order(
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
        raise ClosedDagError("canonical bundle contains nodes unreachable from the root")

    # Preflight every body before recursive checking starts.  The receipt is
    # all-or-nothing, and a graph/resource failure therefore performs no
    # partial logical admission.
    body_metrics: dict[int, tuple[int, int, int]] = {}
    total_body_occurrences = 0
    total_body_objects = 0
    maximum_body_depth = 0
    for node_id in order:
        occurrences, objects, depth = _proof_metrics_bounded(
            table[node_id].body,
            max_occurrences=limits.max_body_occurrences,
            max_objects=limits.max_body_objects,
            max_depth=limits.max_body_depth,
        )
        total_body_occurrences += occurrences
        total_body_objects += objects
        maximum_body_depth = max(maximum_body_depth, depth)
        if total_body_occurrences > limits.max_total_body_occurrences:
            raise ClosedDagError("bundle exceeds its total body-occurrence limit")
        if total_body_objects > limits.max_total_body_objects:
            raise ClosedDagError("bundle exceeds its total body-object limit")
        body_metrics[node_id] = (occurrences, objects, depth)

    check = kernel_checker.check_classical if bundle.classical else kernel_checker.check
    receipts: list[CheckedNodeReceipt] = []
    established: set[int] = set()
    for node_id in order:
        node = table[node_id]
        if not all(dependency in established for dependency in node.dependencies):
            raise ClosedDagError("internal topological-order failure")
        curried = node.target
        for dependency in reversed(node.dependencies):
            curried = Imp(table[dependency].target, curried)

        # This is the only logical oracle call in the prototype: exactly one
        # empty-context kernel invocation per bundle node.
        if not check((), node.body, curried):
            raise ClosedDagError(f"kernel rejected closed node {node_id}")
        established.add(node_id)
        occurrences, objects, depth = body_metrics[node_id]
        receipts.append(
            CheckedNodeReceipt(
                node_id,
                node.dependencies,
                occurrences,
                objects,
                depth,
            )
        )

    return ClosedBundleReceipt(
        root=bundle.root,
        target=target,
        classical=bundle.classical,
        topological_order=order,
        dependency_edges=dependency_edges,
        formula_occurrences=formula_occurrences,
        body_occurrences=total_body_occurrences,
        body_objects=total_body_objects,
        maximum_body_depth=maximum_body_depth,
        nodes=tuple(receipts),
    )


def check_closed_bundle(
    bundle: object,
    target: object,
    *,
    limits: ClosedDagLimits = DEFAULT_LIMITS,
) -> ClosedBundleReceipt | None:
    """Fail closed while checking a complete bundle against one exact target.

    A successful receipt is diagnostic evidence from this experimental
    checker only.  It is neither serializable theorem authority nor an input
    accepted by :func:`peano_lab.kernel.checker.check`.
    """

    try:
        return _check_closed_bundle(bundle, target, limits)  # type: ignore[arg-type]
    except (
        AttributeError,
        ClosedDagError,
        IndexError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return None


__all__ = [
    "ClosedDagError",
    "ClosedDagLimits",
    "DEFAULT_LIMITS",
    "ClosedNode",
    "ClosedBundle",
    "CheckedNodeReceipt",
    "ClosedBundleReceipt",
    "check_closed_bundle",
]
