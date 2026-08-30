"""Self-contained, topologically checked intuitionistic proof bundles.

Each local node contains its *entire ordinary proof body*, not a trusted name,
digest, receipt, or external reference.  The unchanged kernel checks the body
exactly once from the empty context against

    dependency₁ → ⋯ → dependencyₖ → target.

Earlier local nodes discharge these premises by constructive implication
elimination.  The corresponding Lean module proves this composition sound.
Canonical bytes contain only exact-arity tagged arrays and nonnegative
integers; proof constructors use the existing `peano-lab-v2` spelling.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import heapq
import json
from typing import Any

from ..kernel import checker as kernel_checker
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
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


PROOF_BUNDLE_FORMAT = "peano-lab-bundle-v1"
AXIOM_NAMES = frozenset({"PA1", "PA2", "PA3", "PA4", "PA5", "PA6"})


class ProofBundleError(ValueError):
    """Malformed local topology, canonical bytes, or rejected proof body."""


@dataclass(frozen=True, slots=True)
class BundleLimits:
    max_nodes: int = 4_096
    max_dependencies_per_node: int = 256
    max_edges: int = 65_536
    max_body_nodes: int = 500_000
    max_total_body_nodes: int = 5_000_000
    max_body_depth: int = 256
    max_formula_nodes: int = 500_000
    max_formula_depth: int = 256
    max_payload_bytes: int = 64_000_000


DEFAULT_BUNDLE_LIMITS = BundleLimits()


@dataclass(frozen=True, slots=True)
class BundleNode:
    """An ordinary dependency-curried closed proof and bundle-local ID."""

    node_id: int
    target: Formula
    dependencies: tuple[int, ...]
    body: Proof
    fuel: int | None = None


@dataclass(frozen=True, slots=True)
class ProofBundle:
    """A complete finite proof graph and one designated local root."""

    nodes: tuple[BundleNode, ...]
    root: int


@dataclass(frozen=True, slots=True)
class CheckedProofBundle:
    """Diagnostics only: a hash or receipt never substitutes for proof data."""

    target: Formula
    root: int
    topological_order: tuple[int, ...]
    node_count: int
    dependency_edges: int
    total_body_nodes: int
    kernel_calls: int


def _natural(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ProofBundleError(f"{label} must be a nonnegative integer")
    return value


def _array(value: object, tag: str, arity: int) -> list[Any]:
    if (
        type(value) is not list
        or len(value) != arity
        or type(value[0]) is not str
        or value[0] != tag
    ):
        raise ProofBundleError(f"expected exact {tag!r} array of arity {arity}")
    return value


def encode_term(term: Term) -> list[Any]:
    """Encode one exact ordinary kernel term using the canonical v2 tags."""

    if type(term) is Var:
        return ["var", _natural(term.index, "variable index")]
    if type(term) is Zero:
        return ["zero"]
    if type(term) is Succ:
        return ["succ", encode_term(term.term)]
    if type(term) is Add:
        return ["add", encode_term(term.left), encode_term(term.right)]
    if type(term) is Mul:
        return ["mul", encode_term(term.left), encode_term(term.right)]
    raise ProofBundleError("expected an exact ordinary kernel term")


def decode_term(value: object, *, _depth: int = 256) -> Term:
    if _depth <= 0:
        raise ProofBundleError("term exceeds its decoding-depth limit")
    if type(value) is not list or not value or type(value[0]) is not str:
        raise ProofBundleError("term must be an exact tagged array")
    tag = value[0]
    if tag == "var":
        return Var(_natural(_array(value, tag, 2)[1], "variable index"))
    if tag == "zero":
        _array(value, tag, 1)
        return Zero()
    if tag == "succ":
        return Succ(decode_term(_array(value, tag, 2)[1], _depth=_depth - 1))
    if tag in {"add", "mul"}:
        items = _array(value, tag, 3)
        constructor = Add if tag == "add" else Mul
        return constructor(
            decode_term(items[1], _depth=_depth - 1),
            decode_term(items[2], _depth=_depth - 1),
        )
    raise ProofBundleError(f"unknown term tag {tag!r}")


def encode_formula(formula: Formula) -> list[Any]:
    """Encode one exact ordinary kernel formula using canonical v2 tags."""

    if type(formula) is Eq:
        return ["eq", encode_term(formula.left), encode_term(formula.right)]
    if type(formula) is Bot:
        return ["bot"]
    if type(formula) is Imp:
        return ["imp", encode_formula(formula.left), encode_formula(formula.right)]
    if type(formula) is And:
        return ["and", encode_formula(formula.left), encode_formula(formula.right)]
    if type(formula) is Or:
        return ["or", encode_formula(formula.left), encode_formula(formula.right)]
    if type(formula) is Forall:
        return ["forall", encode_formula(formula.body)]
    if type(formula) is Exists:
        return ["exists", encode_formula(formula.body)]
    raise ProofBundleError("expected an exact ordinary kernel formula")


def decode_formula(value: object, *, _depth: int = 256) -> Formula:
    if _depth <= 0:
        raise ProofBundleError("formula exceeds its decoding-depth limit")
    if type(value) is not list or not value or type(value[0]) is not str:
        raise ProofBundleError("formula must be an exact tagged array")
    tag = value[0]
    if tag == "eq":
        items = _array(value, tag, 3)
        return Eq(
            decode_term(items[1], _depth=_depth - 1),
            decode_term(items[2], _depth=_depth - 1),
        )
    if tag == "bot":
        _array(value, tag, 1)
        return Bot()
    if tag in {"imp", "and", "or"}:
        items = _array(value, tag, 3)
        constructor = {"imp": Imp, "and": And, "or": Or}[tag]
        return constructor(
            decode_formula(items[1], _depth=_depth - 1),
            decode_formula(items[2], _depth=_depth - 1),
        )
    if tag in {"forall", "exists"}:
        constructor = Forall if tag == "forall" else Exists
        return constructor(decode_formula(_array(value, tag, 2)[1], _depth=_depth - 1))
    raise ProofBundleError(f"unknown formula tag {tag!r}")


def encode_proof(proof: Proof) -> list[Any]:
    """Encode a complete ordinary proof, never a trusted theorem reference."""

    if type(proof) is Hyp:
        return ["hyp", _natural(proof.index, "hypothesis index")]
    if type(proof) is ImpIntro:
        return ["imp_intro", encode_proof(proof.body)]
    if type(proof) is ImpElim:
        return ["imp_elim", encode_proof(proof.function), encode_proof(proof.argument)]
    if type(proof) is Cut:
        return [
            "cut",
            encode_formula(proof.proposition),
            encode_formula(proof.conclusion),
            encode_proof(proof.lemma),
            encode_proof(proof.body),
        ]
    if type(proof) is AndIntro:
        return ["and_intro", encode_proof(proof.left), encode_proof(proof.right)]
    if type(proof) is AndElimL:
        return ["and_elim_l", encode_proof(proof.pair)]
    if type(proof) is AndElimR:
        return ["and_elim_r", encode_proof(proof.pair)]
    if type(proof) is OrIntroL:
        return ["or_intro_l", encode_proof(proof.proof)]
    if type(proof) is OrIntroR:
        return ["or_intro_r", encode_proof(proof.proof)]
    if type(proof) is OrElim:
        return [
            "or_elim",
            encode_proof(proof.disjunction),
            encode_proof(proof.left_case),
            encode_proof(proof.right_case),
        ]
    if type(proof) is BotElim:
        return ["bot_elim", encode_proof(proof.absurdity)]
    if type(proof) is ForallIntro:
        return ["forall_intro", encode_proof(proof.body)]
    if type(proof) is ForallElim:
        return ["forall_elim", encode_proof(proof.universal), encode_term(proof.term)]
    if type(proof) is ExistsIntro:
        return ["exists_intro", encode_term(proof.term), encode_proof(proof.proof)]
    if type(proof) is ExistsElim:
        return ["exists_elim", encode_proof(proof.existential), encode_proof(proof.body)]
    if type(proof) is EqRefl:
        return ["eq_refl", encode_term(proof.term)]
    if type(proof) is EqSym:
        return ["eq_sym", encode_proof(proof.proof)]
    if type(proof) is EqTrans:
        return ["eq_trans", encode_proof(proof.first), encode_proof(proof.second)]
    if type(proof) is CongS:
        return ["cong_s", encode_proof(proof.proof)]
    if type(proof) is CongAdd:
        return ["cong_add", encode_proof(proof.left), encode_proof(proof.right)]
    if type(proof) is CongMul:
        return ["cong_mul", encode_proof(proof.left), encode_proof(proof.right)]
    if type(proof) is EqSubst:
        return [
            "eq_subst",
            encode_formula(proof.motive),
            encode_proof(proof.equation),
            encode_proof(proof.body),
        ]
    if type(proof) is DNE:
        return ["dne", encode_formula(proof.proposition)]
    if type(proof) is Axiom:
        if proof.name not in AXIOM_NAMES:
            raise ProofBundleError("axiom name must be exactly PA1 through PA6")
        return ["axiom", proof.name]
    if type(proof) is Ind:
        return [
            "ind",
            encode_formula(proof.motive),
            encode_proof(proof.base),
            encode_proof(proof.step),
        ]
    raise ProofBundleError("expected an exact ordinary kernel proof constructor")


def decode_proof(value: object, *, _depth: int = 256) -> Proof:
    """Decode exact-arity inert proof constructors; this grants no authority."""

    if _depth <= 0:
        raise ProofBundleError("proof exceeds its decoding-depth limit")
    if type(value) is not list or not value or type(value[0]) is not str:
        raise ProofBundleError("proof must be an exact tagged array")
    tag = value[0]
    child_depth = _depth - 1
    unary: dict[str, type[Proof]] = {
        "imp_intro": ImpIntro,
        "and_elim_l": AndElimL,
        "and_elim_r": AndElimR,
        "or_intro_l": OrIntroL,
        "or_intro_r": OrIntroR,
        "bot_elim": BotElim,
        "forall_intro": ForallIntro,
        "eq_sym": EqSym,
        "cong_s": CongS,
    }
    binary: dict[str, type[Proof]] = {
        "imp_elim": ImpElim,
        "and_intro": AndIntro,
        "exists_elim": ExistsElim,
        "eq_trans": EqTrans,
        "cong_add": CongAdd,
        "cong_mul": CongMul,
    }
    if tag in unary:
        return unary[tag](decode_proof(_array(value, tag, 2)[1], _depth=child_depth))
    if tag in binary:
        items = _array(value, tag, 3)
        return binary[tag](
            decode_proof(items[1], _depth=child_depth),
            decode_proof(items[2], _depth=child_depth),
        )
    if tag == "hyp":
        return Hyp(_natural(_array(value, tag, 2)[1], "hypothesis index"))
    if tag == "cut":
        items = _array(value, tag, 5)
        return Cut(
            decode_formula(items[1], _depth=child_depth),
            decode_formula(items[2], _depth=child_depth),
            decode_proof(items[3], _depth=child_depth),
            decode_proof(items[4], _depth=child_depth),
        )
    if tag == "or_elim":
        items = _array(value, tag, 4)
        return OrElim(
            decode_proof(items[1], _depth=child_depth),
            decode_proof(items[2], _depth=child_depth),
            decode_proof(items[3], _depth=child_depth),
        )
    if tag == "forall_elim":
        items = _array(value, tag, 3)
        return ForallElim(
            decode_proof(items[1], _depth=child_depth),
            decode_term(items[2], _depth=child_depth),
        )
    if tag == "exists_intro":
        items = _array(value, tag, 3)
        return ExistsIntro(
            decode_term(items[1], _depth=child_depth),
            decode_proof(items[2], _depth=child_depth),
        )
    if tag == "eq_refl":
        return EqRefl(decode_term(_array(value, tag, 2)[1], _depth=child_depth))
    if tag == "eq_subst":
        items = _array(value, tag, 4)
        return EqSubst(
            decode_formula(items[1], _depth=child_depth),
            decode_proof(items[2], _depth=child_depth),
            decode_proof(items[3], _depth=child_depth),
        )
    if tag == "dne":
        return DNE(decode_formula(_array(value, tag, 2)[1], _depth=child_depth))
    if tag == "axiom":
        name = _array(value, tag, 2)[1]
        if type(name) is not str or name not in AXIOM_NAMES:
            raise ProofBundleError("axiom name must be exactly PA1 through PA6")
        return Axiom(name)
    if tag == "ind":
        items = _array(value, tag, 4)
        return Ind(
            decode_formula(items[1], _depth=child_depth),
            decode_proof(items[2], _depth=child_depth),
            decode_proof(items[3], _depth=child_depth),
        )
    raise ProofBundleError(f"unknown proof tag {tag!r}")


def _validate_limits(limits: BundleLimits) -> None:
    if type(limits) is not BundleLimits:
        raise ProofBundleError("bundle limits must be an exact BundleLimits value")
    for field in fields(limits):
        value = getattr(limits, field.name)
        if type(value) is not int or value <= 0:
            raise ProofBundleError(f"{field.name} must be a positive integer")


def _closed_formula_metrics(formula: object, limits: BundleLimits) -> int:
    pending: list[tuple[object, int, int, bool]] = [(formula, 0, 1, True)]
    count = 0
    while pending:
        value, binders, depth, is_formula = pending.pop()
        count += 1
        if count > limits.max_formula_nodes:
            raise ProofBundleError("formula exceeds its structural-node limit")
        if depth > limits.max_formula_depth:
            raise ProofBundleError("formula exceeds its structural-depth limit")
        if is_formula:
            if type(value) is Eq:
                pending.extend(
                    ((value.right, binders, depth + 1, False),
                     (value.left, binders, depth + 1, False))
                )
            elif type(value) is Bot:
                continue
            elif type(value) in (Imp, And, Or):
                pending.extend(
                    ((value.right, binders, depth + 1, True),
                     (value.left, binders, depth + 1, True))
                )
            elif type(value) in (Forall, Exists):
                pending.append((value.body, binders + 1, depth + 1, True))
            else:
                raise ProofBundleError("target contains a non-kernel formula")
        elif type(value) is Var:
            if type(value.index) is not int or not 0 <= value.index < binders:
                raise ProofBundleError("bundle targets must be syntactically closed")
        elif type(value) is Zero:
            continue
        elif type(value) is Succ:
            pending.append((value.term, binders, depth + 1, False))
        elif type(value) in (Add, Mul):
            pending.extend(
                ((value.right, binders, depth + 1, False),
                 (value.left, binders, depth + 1, False))
            )
        else:
            raise ProofBundleError("target contains a non-kernel term")
    return count


def _proof_size(proof: object, limits: BundleLimits) -> int:
    if not isinstance(proof, Proof):
        raise ProofBundleError("bundle bodies must be ordinary kernel proofs")
    pending: list[tuple[Proof, int]] = [(proof, 1)]
    count = 0
    while pending:
        value, depth = pending.pop()
        count += 1
        if count > limits.max_body_nodes:
            raise ProofBundleError("proof body exceeds its structural-node limit")
        if depth > limits.max_body_depth:
            raise ProofBundleError("proof body exceeds its structural-depth limit")
        try:
            children = (
                child
                for field in fields(value)
                if isinstance((child := getattr(value, field.name)), Proof)
            )
            pending.extend((child, depth + 1) for child in children)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ProofBundleError("bundle body is malformed") from exc
    return count


@dataclass(frozen=True, slots=True)
class _BundleAnalysis:
    table: dict[int, BundleNode]
    order: tuple[int, ...]
    body_sizes: dict[int, int]
    edges: int


def _analyze_bundle(
    bundle: object,
    target: object,
    limits: BundleLimits,
) -> _BundleAnalysis:
    _validate_limits(limits)
    if type(bundle) is not ProofBundle:
        raise ProofBundleError("bundle must be an exact ProofBundle value")
    if type(bundle.nodes) is not tuple or not 0 < len(bundle.nodes) <= limits.max_nodes:
        raise ProofBundleError("bundle has an invalid node count")
    _natural(bundle.root, "bundle root")
    _closed_formula_metrics(target, limits)

    table: dict[int, BundleNode] = {}
    for node in bundle.nodes:
        if type(node) is not BundleNode:
            raise ProofBundleError("bundle nodes must have the exact BundleNode type")
        node_id = _natural(node.node_id, "node ID")
        if node_id in table:
            raise ProofBundleError(f"duplicate local node ID {node_id}")
        if type(node.dependencies) is not tuple:
            raise ProofBundleError("node dependencies must be a tuple")
        if len(node.dependencies) > limits.max_dependencies_per_node:
            raise ProofBundleError("node exceeds its dependency-count limit")
        if node.fuel is not None and (
            type(node.fuel) is not int or node.fuel <= 0
        ):
            raise ProofBundleError("node fuel must be a positive integer")
        _closed_formula_metrics(node.target, limits)
        table[node_id] = node

    if bundle.root not in table or table[bundle.root].target != target:
        raise ProofBundleError("designated root differs from the exact caller target")

    dependents: dict[int, list[int]] = {node_id: [] for node_id in table}
    indegree: dict[int, int] = {}
    edges = 0
    for node_id, node in table.items():
        dependencies = node.dependencies
        if not all(type(dependency) is int and dependency >= 0 for dependency in dependencies):
            raise ProofBundleError("dependency IDs must be nonnegative integers")
        if len(set(dependencies)) != len(dependencies):
            raise ProofBundleError("duplicate local dependency references are forbidden")
        indegree[node_id] = len(dependencies)
        edges += len(dependencies)
        if edges > limits.max_edges:
            raise ProofBundleError("bundle exceeds its dependency-edge limit")
        for dependency in dependencies:
            if dependency not in table:
                raise ProofBundleError(f"dangling dependency reference {dependency}")
            dependents[dependency].append(node_id)

    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[int] = []
    while ready:
        node_id = heapq.heappop(ready)
        order.append(node_id)
        for dependent in sorted(dependents[node_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) != len(table):
        raise ProofBundleError("local dependency graph contains a cycle")

    reachable: set[int] = set()
    pending = [bundle.root]
    while pending:
        node_id = pending.pop()
        if node_id not in reachable:
            reachable.add(node_id)
            pending.extend(table[node_id].dependencies)
    if len(reachable) != len(table):
        raise ProofBundleError("canonical bundle contains unreachable proof nodes")

    sizes: dict[int, int] = {}
    total = 0
    for node_id in order:
        node = table[node_id]
        size = _proof_size(node.body, limits)
        if node.fuel is not None and node.fuel < 8 * size + 16:
            raise ProofBundleError(
                "node fuel is below its conservative checker allowance"
            )
        total += size
        if total > limits.max_total_body_nodes:
            raise ProofBundleError("bundle exceeds its aggregate body-node limit")
        sizes[node_id] = size
    return _BundleAnalysis(table, tuple(order), sizes, edges)


def check_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    limits: BundleLimits = DEFAULT_BUNDLE_LIMITS,
) -> CheckedProofBundle:
    """Check every local proof once, from the empty intuitionistic context."""

    analysis = _analyze_bundle(bundle, target, limits)
    established: set[int] = set()
    kernel_calls = 0
    for node_id in analysis.order:
        node = analysis.table[node_id]
        if not all(dependency in established for dependency in node.dependencies):
            raise ProofBundleError("a dependency was not previously established")
        curried = node.target
        for dependency in reversed(node.dependencies):
            curried = Imp(analysis.table[dependency].target, curried)
        kernel_calls += 1
        if not kernel_checker.check((), node.body, curried):
            raise ProofBundleError(f"intuitionistic kernel rejected local node {node_id}")
        established.add(node_id)
    return CheckedProofBundle(
        target=target,
        root=bundle.root,
        topological_order=analysis.order,
        node_count=len(analysis.order),
        dependency_edges=analysis.edges,
        total_body_nodes=sum(analysis.body_sizes.values()),
        kernel_calls=kernel_calls,
    )


def _bundle_record(
    bundle: ProofBundle,
    target: Formula,
    limits: BundleLimits,
) -> list[Any]:
    analysis = _analyze_bundle(bundle, target, limits)
    remap = {old_id: new_id for new_id, old_id in enumerate(analysis.order)}
    nodes: list[list[Any]] = []
    for node_id in analysis.order:
        node = analysis.table[node_id]
        fuel = node.fuel if node.fuel is not None else 8 * analysis.body_sizes[node_id] + 16
        nodes.append(
            [
                fuel,
                encode_formula(node.target),
                [remap[dependency] for dependency in node.dependencies],
                encode_proof(node.body),
            ]
        )
    return [PROOF_BUNDLE_FORMAT, remap[bundle.root], encode_formula(target), nodes]


def encode_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    limits: BundleLimits = DEFAULT_BUNDLE_LIMITS,
) -> str:
    """Persist every proof body once in canonical dense topological order."""

    payload = json.dumps(
        _bundle_record(bundle, target, limits),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ) + "\n"
    if len(payload.encode("utf-8")) > limits.max_payload_bytes:
        raise ProofBundleError("canonical proof bundle exceeds its byte limit")
    return payload


def decode_proof_bundle(
    payload: str,
    *,
    limits: BundleLimits = DEFAULT_BUNDLE_LIMITS,
) -> tuple[ProofBundle, Formula]:
    """Rehydrate all inert bodies; callers must still invoke the kernel checker."""

    _validate_limits(limits)
    if type(payload) is not str:
        raise ProofBundleError("proof bundle payload must be text")
    if len(payload.encode("utf-8")) > limits.max_payload_bytes:
        raise ProofBundleError("canonical proof bundle exceeds its byte limit")
    try:
        value = json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise ProofBundleError("invalid proof bundle JSON") from exc
    if (
        type(value) is not list
        or len(value) != 4
        or value[0] != PROOF_BUNDLE_FORMAT
        or type(value[3]) is not list
    ):
        raise ProofBundleError("invalid canonical proof bundle envelope")
    root = _natural(value[1], "bundle root")
    target = decode_formula(value[2], _depth=limits.max_formula_depth)
    if not 0 < len(value[3]) <= limits.max_nodes:
        raise ProofBundleError("bundle has an invalid node count")
    nodes: list[BundleNode] = []
    for node_id, item in enumerate(value[3]):
        if type(item) is not list or len(item) != 4:
            raise ProofBundleError("bundle node must have exactly four fields")
        fuel = _natural(item[0], "node fuel")
        if fuel == 0:
            raise ProofBundleError("node fuel must be strictly positive")
        if type(item[2]) is not list:
            raise ProofBundleError("node dependencies must be an exact array")
        dependencies = tuple(_natural(edge, "dependency ID") for edge in item[2])
        if any(dependency >= node_id for dependency in dependencies):
            raise ProofBundleError("canonical dependencies must point strictly backward")
        nodes.append(
            BundleNode(
                node_id,
                decode_formula(item[1], _depth=limits.max_formula_depth),
                dependencies,
                decode_proof(item[3], _depth=limits.max_body_depth),
                fuel,
            )
        )
    bundle = ProofBundle(tuple(nodes), root)
    if encode_proof_bundle(bundle, target, limits=limits) != payload:
        raise ProofBundleError("proof bundle bytes are not canonical")
    return bundle, target


def check_encoded_proof_bundle(
    payload: str,
    *,
    limits: BundleLimits = DEFAULT_BUNDLE_LIMITS,
) -> CheckedProofBundle:
    """Decode exact canonical bytes, then check every actual body exactly once."""

    bundle, target = decode_proof_bundle(payload, limits=limits)
    return check_proof_bundle(bundle, target, limits=limits)


__all__ = [
    "AXIOM_NAMES",
    "BundleLimits",
    "BundleNode",
    "CheckedProofBundle",
    "DEFAULT_BUNDLE_LIMITS",
    "PROOF_BUNDLE_FORMAT",
    "ProofBundle",
    "ProofBundleError",
    "check_encoded_proof_bundle",
    "check_proof_bundle",
    "decode_formula",
    "decode_proof",
    "decode_proof_bundle",
    "decode_term",
    "encode_formula",
    "encode_proof",
    "encode_proof_bundle",
    "encode_term",
]
