"""Static, body, and root-pruned closure audit for factorial/Legendre equality.

The cheap gates freeze the expanded statements and check both dependency-
curried proof bodies.  One focused hybrid gate then treats Stable certificates
as atomic checked leaves and shares every reachable candidate body through the
ordinary production ``LayeredReplay`` compiler.  The unchanged intuitionistic
kernel remains the final empty-context authority.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Hyp, Proof
from peano_lab.library.bertrand_factorial_legendre_candidate import (
    make_bertrand_factorial_legendre_candidate_theorems,
)
from peano_lab.library.bertrand_factorial_valuation_candidate import (
    make_bertrand_factorial_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_successor_candidate import (
    make_bertrand_legendre_successor_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_recurrence_candidate import (
    make_bertrand_legendre_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_sum_candidate import (
    make_bertrand_legendre_sum_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_valuation_bridge_candidate import (
    make_bertrand_legendre_valuation_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_power_divisibility_candidate import (
    make_bertrand_power_divisibility_candidate_theorems,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_candidate import (
    make_bertrand_power_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_laws_candidate import (
    make_bertrand_power_valuation_law_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from peano_lab.library.finite_sum_pointwise_add_candidate import (
    make_finite_sum_pointwise_add_candidate_theorems,
)
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    compile_layered_replay,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "factorial_legendre_successor_agreement": {
        "statement": (
            65_959,
            "8bc0d088d9ed0d911a3d0eb9a7ebfb6e1b66069215956b58b1f282dafa412a02",
        ),
        "dependencies": (
            "prime_factorial_valuation_succ",
            "prime_legendre_sum_succ",
        ),
        "body": (2, 45, 54, 29, 54, 53, 0),
    },
    "prime_factorial_valuation_eq_legendre_sum": {
        "statement": (
            25_480,
            "7123646c1dfc92f90c584772c3ee1df5fd6e34ed2b5590c9d66be4e6a2e49b9a",
        ),
        "dependencies": (
            "prime_factorial_valuation_zero",
            "legendre_sum_zero",
            "factorial_valuation_exists",
            "prime_legendre_sum_exists",
            "power_valuation_exists",
            "factorial_legendre_successor_agreement",
        ),
        "body": (6, 69, 84, 33, 84, 83, 0),
    },
}


HYBRID_ROOT = "prime_factorial_valuation_eq_legendre_sum"
EXPECTED_HYBRID_NODE_COUNT = 120
EXPECTED_HYBRID_STABLE_COUNT = 58
EXPECTED_HYBRID_CANDIDATE_COUNT = 62
EXPECTED_HYBRID_EDGE_COUNT = 205
EXPECTED_HYBRID_LAYER_SIZES = (
    62,
    21,
    9,
    3,
    5,
    4,
    4,
    3,
    2,
    2,
    1,
    1,
    1,
    1,
    1,
)
EXPECTED_HYBRID_MAX_FAN_IN = 10
EXPECTED_HYBRID_TOPOLOGY_SHA256 = (
    "a46490714f87d46b692f5cbc76425db5f8c4546a836465ca64a656bce5e1e539"
)
EXPECTED_HYBRID_PROOF_DAG_SHA256 = (
    "92b1333634e6937cf1afe4ab920ba07541686d421f0e50c839f3da3c7c1d7507"
)
EXPECTED_HYBRID_CLOSURE = {
    "proof_nodes": 259_219,
    "proof_depth": 95,
    "proof_objects": 13_347,
    "proof_edges": 13_719,
    "reused_objects": 373,
    "annotation_occurrences": 904_185,
    "envelope_depth": 95,
    "package_formula_occurrences": 37_765,
    "package_formula_depth": 47,
}
EXPECTED_UNREACHABLE_CANDIDATES = frozenset(
    {
        "mul_le_mul",
        "le_mul_of_one_le_left",
        "pow_base_monotone",
        "pow_exponent_monotone",
        "power_valuation_functional",
        "prime_power_valuation_exists",
        "prime_power_valuation_functional",
        "factorial_valuation_functional",
        "prime_factorial_valuation_succ_invert",
    }
)


@dataclass(frozen=True, slots=True)
class _HybridBlueprint:
    """Deterministic local-ID graph with Stable certificates as atomic leaves."""

    names: tuple[str, ...]
    targets: tuple[Formula, ...]
    dependencies: tuple[tuple[int, ...], ...]
    layers: tuple[tuple[int, ...], ...]
    kinds: tuple[str, ...]
    root: int
    topology_sha256: str


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    """Return only the direct, concrete statement providers for this gate."""

    return (
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_factorial_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_sum_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_recurrence_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_factorial_legendre_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


@lru_cache(maxsize=1)
def _closure_candidate_pool() -> tuple[TheoremSpec, ...]:
    """Return the exact candidate source pool, before root pruning."""

    rows = (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec),
        *make_bertrand_power_divisibility_candidate_theorems(TheoremSpec),
        *make_bertrand_factorial_valuation_candidate_theorems(TheoremSpec),
        *make_finite_sum_transport_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_sum_candidate_theorems(TheoremSpec),
        *make_eisenstein_initial_segment_count_candidate_theorems(TheoremSpec),
        *make_finite_sum_pointwise_add_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_valuation_bridge_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_legendre_successor_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_recurrence_candidate_theorems(TheoremSpec),
        *make_bertrand_factorial_legendre_candidate_theorems(TheoremSpec),
    )
    assert len({item.name for item in rows}) == len(rows)
    return rows


@lru_cache(maxsize=1)
def _hybrid_blueprint() -> _HybridBlueprint:
    """Prune at the root and stop every traversal at the Stable boundary."""

    public = _specs_by_name()
    candidates = {item.name: item for item in _closure_candidate_pool()}
    for name in set(public) & set(candidates):
        assert public[name] == candidates[name]

    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(name: str) -> None:
        if name in public:
            stable_names.add(name)
            return
        item = candidates.get(name)
        if item is None:
            raise AssertionError(f"unknown hybrid dependency {name!r}")
        mark = marks.get(name, 0)
        if mark == 1:
            raise AssertionError(f"cyclic hybrid dependency at {name!r}")
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(HYBRID_ROOT)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {name: index for index, name in enumerate(names)}
    assert len(positions) == len(names)

    kinds = tuple(
        "stable_atomic" if name in stable_names else "candidate_body"
        for name in names
    )
    selected_specs = tuple(
        public[name] if name in stable_names else candidates[name]
        for name in names
    )
    targets = tuple(_closed_formula(item.statement) for item in selected_specs)
    dependencies = tuple(
        ()
        if kind == "stable_atomic"
        else tuple(positions[dependency] for dependency in item.dependencies)
        for kind, item in zip(kinds, selected_specs, strict=True)
    )

    depths: list[int] = []
    for node_id, node_dependencies in enumerate(dependencies):
        if any(dependency >= node_id for dependency in node_dependencies):
            raise AssertionError("hybrid dependency did not precede its node")
        depths.append(
            0
            if not node_dependencies
            else 1 + max(depths[dependency] for dependency in node_dependencies)
        )
    layer_lists: list[list[int]] = [
        [] for _ in range(1 + max(depths, default=0))
    ]
    for node_id, depth in enumerate(depths):
        layer_lists[depth].append(node_id)
    layers = tuple(tuple(layer) for layer in layer_lists)

    rows = (
        "\x1f".join(
            (
                str(node_id),
                name,
                kinds[node_id],
                selected_specs[node_id].statement,
                "\x1e".join(names[item] for item in dependencies[node_id]),
            )
        )
        for node_id, name in enumerate(names)
    )
    return _HybridBlueprint(
        names=names,
        targets=targets,
        dependencies=dependencies,
        layers=layers,
        kinds=kinds,
        root=positions[HYBRID_ROOT],
        topology_sha256=sha256("\x1c".join(rows).encode()).hexdigest(),
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets_by_name: dict[str, Formula],
) -> Proof:
    """Build one ordinary checked body without closing its dependencies."""

    target = targets_by_name[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets_by_name[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        if tactic == "use":
            raise AssertionError(
                f"hybrid body {item.name!r} delegated authority through use"
            )
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=1)
def _hybrid_bundle() -> LayeredReplayBundle:
    """Attach Stable certificates and freshly checked candidate bodies once."""

    blueprint = _hybrid_blueprint()
    public = _specs_by_name()
    candidates = {item.name: item for item in _closure_candidate_pool()}
    targets_by_name = dict(
        zip(blueprint.names, blueprint.targets, strict=True)
    )
    nodes: list[LayeredReplayNode] = []
    for node_id, name in enumerate(blueprint.names):
        if blueprint.kinds[node_id] == "stable_atomic":
            theorem = replay(name)
            assert theorem.formula == blueprint.targets[node_id]
            assert theorem.spec == public[name]
            body = theorem.certificate
        else:
            body = _dependency_curried_body(
                candidates[name],
                targets_by_name,
            )
        nodes.append(
            LayeredReplayNode(
                node_id=node_id,
                target=blueprint.targets[node_id],
                dependencies=blueprint.dependencies[node_id],
                body=body,
            )
        )
    return LayeredReplayBundle(tuple(nodes), blueprint.root)


def _walk_unique_proof(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )


def _proof_dag_sha256(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = tuple(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def test_factorial_legendre_factory_is_frozen_hygienic_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_factorial_legendre_candidate_theorems(
        TheoremSpec
    ) == specs

    public = _specs_by_name()
    assert not (set(EXPECTED) & set(public))

    local = _local()
    available = set(public) | {item.name for item in _prior_specs()}
    for item in specs:
        expected = EXPECTED[item.name]
        assert local[item.name] is item
        assert item.dependencies == expected["dependencies"]
        assert all(dependency in available for dependency in item.dependencies)
        available.add(item.name)

        length, digest = expected["statement"]
        assert len(item.statement) == length
        assert sha256(item.statement.encode()).hexdigest() == digest
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "Factorial(",
                "FactorialVal(",
                "LegendreSum(",
                "PowerVal(",
                "PowerQuotPrefix(",
                "Prime(",
                "Pow(",
                "DivRem(",
                "BetaAt(",
                "Sum(",
                "^",
                "%",
                "∣",
                "<=",
            )
        )

    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {
            "auto",
            "choice",
            "compact_arith",
            "norm_num",
            "ring",
            "simp",
            "use",
        }
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "by_contra", "classical", "sorry")
    )


def test_factorial_legendre_hybrid_topology_is_exact_and_root_pruned() -> None:
    blueprint = _hybrid_blueprint()
    public = _specs_by_name()
    pool_names = {item.name for item in _closure_candidate_pool()}
    stable_names = {
        name
        for name, kind in zip(
            blueprint.names,
            blueprint.kinds,
            strict=True,
        )
        if kind == "stable_atomic"
    }
    candidate_names = set(blueprint.names) - stable_names

    assert len(_closure_candidate_pool()) == 71
    assert len(blueprint.names) == EXPECTED_HYBRID_NODE_COUNT
    assert len(stable_names) == EXPECTED_HYBRID_STABLE_COUNT
    assert len(candidate_names) == EXPECTED_HYBRID_CANDIDATE_COUNT
    assert stable_names <= set(public)
    assert not (candidate_names & set(public))
    assert pool_names - candidate_names == EXPECTED_UNREACHABLE_CANDIDATES
    assert candidate_names <= pool_names
    assert blueprint.names[blueprint.root] == HYBRID_ROOT
    assert blueprint.targets[blueprint.root] == _closed_formula(
        _specs()[1].statement
    )
    assert sum(map(len, blueprint.dependencies)) == EXPECTED_HYBRID_EDGE_COUNT
    assert max(map(len, blueprint.dependencies)) == EXPECTED_HYBRID_MAX_FAN_IN
    assert tuple(map(len, blueprint.layers)) == EXPECTED_HYBRID_LAYER_SIZES
    assert blueprint.root in blueprint.layers[-1]
    assert blueprint.kinds[:EXPECTED_HYBRID_STABLE_COUNT] == (
        "stable_atomic",
    ) * EXPECTED_HYBRID_STABLE_COUNT
    assert blueprint.kinds[EXPECTED_HYBRID_STABLE_COUNT:] == (
        "candidate_body",
    ) * EXPECTED_HYBRID_CANDIDATE_COUNT

    reachable: set[int] = set()
    pending = [blueprint.root]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(blueprint.dependencies[node_id])
    assert reachable == set(range(EXPECTED_HYBRID_NODE_COUNT))
    assert all(
        dependency < node_id
        for node_id, dependencies in enumerate(blueprint.dependencies)
        for dependency in dependencies
    )


def test_factorial_legendre_root_pruned_hybrid_empty_context_closure() -> None:
    blueprint = _hybrid_blueprint()
    assert blueprint.topology_sha256 == EXPECTED_HYBRID_TOPOLOGY_SHA256
    bundle = _hybrid_bundle()
    compilation = compile_layered_replay(
        bundle,
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )

    assert type(compilation) is LayeredReplayCandidate
    assert compilation.target == blueprint.targets[blueprint.root]
    assert compilation.layers == blueprint.layers
    assert len(compilation.package_formulas) == len(blueprint.layers)
    assert (
        compilation.package_formula_occurrences
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_package_formula_occurrences
    )
    assert (
        compilation.maximum_package_formula_depth
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_package_formula_depth
    )
    assert (
        compilation.proof_nodes
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
    )
    assert (
        compilation.proof_objects
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_objects
    )
    assert (
        compilation.proof_depth
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_depth
    )
    assert (
        compilation.proof_annotation_occurrences
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_annotation_occurrences
    )
    assert (
        compilation.proof_envelope_depth
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_envelope_depth
    )
    assert not any(
        type(node) is DNE
        for node in _walk_unique_proof(compilation.certificate)
    )
    actual_closure = {
        "proof_nodes": compilation.proof_nodes,
        "proof_depth": compilation.proof_depth,
        "proof_objects": compilation.proof_objects,
        "proof_edges": compilation.proof_edges,
        "reused_objects": compilation.reused_objects,
        "annotation_occurrences": compilation.proof_annotation_occurrences,
        "envelope_depth": compilation.proof_envelope_depth,
        "package_formula_occurrences": compilation.package_formula_occurrences,
        "package_formula_depth": compilation.maximum_package_formula_depth,
    }
    assert actual_closure == EXPECTED_HYBRID_CLOSURE
    proof_dag_sha256 = _proof_dag_sha256(compilation.certificate)
    assert proof_dag_sha256 == EXPECTED_HYBRID_PROOF_DAG_SHA256
    kernel_accepted = check((), compilation.certificate, compilation.target)

    # The first isolated pass intentionally reports rather than guesses the
    # certificate metrics.  Freeze them only after this kernel check succeeds.
    print(
        "FACTORIAL LEGENDRE HYBRID CLOSURE RECEIPT "
        f"topology_sha256={blueprint.topology_sha256} "
        f"nodes={len(blueprint.names)} "
        f"stable_atomic={EXPECTED_HYBRID_STABLE_COUNT} "
        f"candidate_bodies={EXPECTED_HYBRID_CANDIDATE_COUNT} "
        f"dependency_edges={EXPECTED_HYBRID_EDGE_COUNT} "
        f"layers={len(blueprint.layers)} "
        f"proof_nodes={compilation.proof_nodes} "
        f"proof_depth={compilation.proof_depth} "
        f"proof_objects={compilation.proof_objects} "
        f"proof_edges={compilation.proof_edges} "
        f"reused_objects={compilation.reused_objects} "
        f"annotation_occurrences="
        f"{compilation.proof_annotation_occurrences} "
        f"envelope_depth={compilation.proof_envelope_depth} "
        f"package_formula_occurrences="
        f"{compilation.package_formula_occurrences} "
        f"package_formula_depth="
        f"{compilation.maximum_package_formula_depth} "
        f"proof_dag_sha256={proof_dag_sha256} "
        f"kernel_accepted={kernel_accepted}",
        flush=True,
    )
    assert kernel_accepted


def test_factorial_legendre_hybrid_rejects_leaf_and_dependency_corruption() -> None:
    blueprint = _hybrid_blueprint()
    bundle = _hybrid_bundle()

    stable_leaf = blueprint.kinds.index("stable_atomic")
    corrupted_leaf = replace(bundle.nodes[stable_leaf], body=Hyp(0))
    corrupted_nodes = list(bundle.nodes)
    corrupted_nodes[stable_leaf] = corrupted_leaf
    corrupted_compilation = compile_layered_replay(
        LayeredReplayBundle(tuple(corrupted_nodes), bundle.root),
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert not check(
        (),
        corrupted_compilation.certificate,
        corrupted_compilation.target,
    )

    root_node = bundle.nodes[bundle.root]
    assert len(root_node.dependencies) >= 2
    swapped_dependencies = (
        root_node.dependencies[1],
        root_node.dependencies[0],
        *root_node.dependencies[2:],
    )
    swapped_nodes = list(bundle.nodes)
    swapped_nodes[bundle.root] = replace(
        root_node,
        dependencies=swapped_dependencies,
    )
    swapped_compilation = compile_layered_replay(
        LayeredReplayBundle(tuple(swapped_nodes), bundle.root),
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert not check(
        (),
        swapped_compilation.certificate,
        swapped_compilation.target,
    )


def test_factorial_legendre_bodies_have_exact_kernel_receipts() -> None:
    receipts = replay_candidate_bodies(_specs(), core=_available())
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == {name: expected["body"] for name, expected in EXPECTED.items()}


def test_factorial_legendre_rejects_false_targets_and_every_removed_edge() -> None:
    for item in _specs():
        false_item = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_item,), core=_available())

        for dependency in item.dependencies:
            without_edge = replace(
                item,
                dependencies=tuple(
                    candidate
                    for candidate in item.dependencies
                    if candidate != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((without_edge,), core=_available())
