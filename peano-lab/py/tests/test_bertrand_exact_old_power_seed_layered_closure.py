"""Exact Alpha-v7 power-seed identity, closure, and capacity audit.

The first two prerequisite roots retain their frozen, independently checked
LayeredReplay closures.  The original ``pow_two_seed_bundle_from_total`` row
is audited separately and honestly: its exact dependency-curried body is
kernel-valid but exceeds only the unchanged LayeredReplay body-envelope cap.
The default interner must therefore fail closed.  An independently rebuilt
direct empty-context closure still has to pass the unchanged intuitionistic
kernel, remain constructive, and reject corruption of both direct Cut edges.

Candidate specifications must equal the sealed Alpha-v7 entries and their
provider sources are pinned below.  Alpha metadata, pending blocker receipts,
and direct-closure diagnostics are never Stable theorem authority.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v7
from peano_lab.library.alpha_enrollment_v7 import alpha_v7_enrollment
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_total_candidate import (
    make_bertrand_power_total_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


ROOTS = (
    "pow_two_base_two_value_four",
    "pow_successor_compose_from_total",
    "pow_two_seed_bundle_from_total",
)
LAYERED_ROOTS = ROOTS[:-1]
SEED_ROOT = ROOTS[-1]

EXPECTED_ROOT_DEPENDENCIES = {
    "pow_two_base_two_value_four": ("pow_two",),
    "pow_successor_compose_from_total": (
        "pow_successor_pair_mul",
    ),
    "pow_two_seed_bundle_from_total": (
        "pow_successor_compose_from_total",
        "pow_two_base_two_value_four",
    ),
}

EXPECTED_SOURCE_MODULES = {
    "pow_two_base_two_value_four": (
        "peano-lab/py/peano_lab/library/"
        "bertrand_integer_envelope_candidate.py"
    ),
    "pow_successor_compose_from_total": (
        "peano-lab/py/peano_lab/library/"
        "bertrand_power_total_candidate.py"
    ),
    "pow_two_seed_bundle_from_total": (
        "peano-lab/py/peano_lab/library/"
        "bertrand_power_total_candidate.py"
    ),
}
EXPECTED_SOURCE_SHA256 = {
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_integer_envelope_candidate.py"
    ): "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_power_total_candidate.py"
    ): "6fbccade6d6d347ca11a6f8ace061dad56202bf733959ed40990e1dd21630410",
}
EXPECTED_V7_TEST_PATH = (
    "peano-lab/py/tests/test_bertrand_power_total_candidate.py"
)
EXPECTED_ALPHA_V7_ENROLLMENT_SHA256 = (
    "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
)
EXPECTED_ALPHA_V7_IDENTITY_SHA256 = (
    "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
)

PENDING_EXACT_OLD_SEED_BLOCKER_RECEIPT = (
    "PENDING_EXACT_OLD_SEED_BLOCKER_RECEIPT"
)
EXPECTED_AUDIT_RECEIPTS: dict[str, dict[str, object] | str] = {
    "pow_two_base_two_value_four": {
        "root_name": "pow_two_base_two_value_four",
        "alpha_v7_enrollment_sha256": (
            "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
        ),
        "alpha_v7_identity_sha256": (
            "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
        ),
        "provider_sources": (
            (
                "peano-lab/py/peano_lab/library/"
                "bertrand_integer_envelope_candidate.py",
                "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1",
            ),
        ),
        "topology_sha256": (
            "4bff87133e953d1c20f7d3353a9940235a7cbe97cf89722e7c191c9f14c32fc5"
        ),
        "candidate_pool_count": 1,
        "candidate_pool_script_sha256": (
            "f3988dcfad2e70347863434ca18b932434222d64c15a1a1cf20263e3e368208b"
        ),
        "candidate_pool_logical_sha256": (
            "72335d439ed0a8335d2febb87aaaad0d7d716bc2b225386c6e40df8c0252a178"
        ),
        "balanced_seed_substituted": False,
        "node_count": 2,
        "stable_atomic_count": 1,
        "candidate_body_count": 1,
        "dependency_edge_count": 1,
        "layer_sizes": (1, 1),
        "max_fan_in": 1,
        "raw_body_union_objects": 1_200,
        "interned_body_union_objects": 829,
        "body_union_object_savings": 371,
        "proof_nodes": 6_530,
        "proof_depth": 69,
        "proof_objects": 834,
        "proof_edges": 1_118,
        "reused_objects": 285,
        "annotation_occurrences": 27_732,
        "envelope_depth": 69,
        "package_formula_occurrences": 404,
        "package_formula_depth": 30,
        "proof_dag_sha256": (
            "5725df483d8104a9817e45956113a995436ab7fe8e5b30eb62772d44aa960fd9"
        ),
        "direct_cut_corruption_rejected": True,
    },
    "pow_successor_compose_from_total": {
        "root_name": "pow_successor_compose_from_total",
        "alpha_v7_enrollment_sha256": (
            "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
        ),
        "alpha_v7_identity_sha256": (
            "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
        ),
        "provider_sources": (
            (
                "peano-lab/py/peano_lab/library/"
                "bertrand_power_total_candidate.py",
                "6fbccade6d6d347ca11a6f8ace061dad56202bf733959ed40990e1dd21630410",
            ),
        ),
        "topology_sha256": (
            "f0d01afd8b35f8b771fea27421c5eac54771a5f8da589ceb60fcabf1ac14382c"
        ),
        "candidate_pool_count": 1,
        "candidate_pool_script_sha256": (
            "dda365a50c90facb26df0d64c8553cd86eebc75dd349f6e72b98dfdb8977a481"
        ),
        "candidate_pool_logical_sha256": (
            "22dcc8b6abd0ce3b8f2dfab2dafabe32f390f7f1cfd946a3a687f6fcb0dac00d"
        ),
        "balanced_seed_substituted": False,
        "node_count": 2,
        "stable_atomic_count": 1,
        "candidate_body_count": 1,
        "dependency_edge_count": 1,
        "layer_sizes": (1, 1),
        "max_fan_in": 1,
        "raw_body_union_objects": 1_338,
        "interned_body_union_objects": 912,
        "body_union_object_savings": 426,
        "proof_nodes": 5_332,
        "proof_depth": 66,
        "proof_objects": 917,
        "proof_edges": 1_208,
        "reused_objects": 292,
        "annotation_occurrences": 23_659,
        "envelope_depth": 66,
        "package_formula_occurrences": 956,
        "package_formula_depth": 33,
        "proof_dag_sha256": (
            "b2202d0126ba9135664e1838a72cf8c5c1bb440300240f8e4a9eeb8e1345ede3"
        ),
        "direct_cut_corruption_rejected": True,
    },
    "pow_two_seed_bundle_from_total": {
        "root_name": "pow_two_seed_bundle_from_total",
        "audit_kind": (
            "layered_body_envelope_blocker_and_direct_closure"
        ),
        "alpha_v7_enrollment_sha256": (
            "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
        ),
        "alpha_v7_identity_sha256": (
            "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
        ),
        "provider_sources": (
            (
                "peano-lab/py/peano_lab/library/"
                "bertrand_integer_envelope_candidate.py",
                "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1",
            ),
            (
                "peano-lab/py/peano_lab/library/"
                "bertrand_power_total_candidate.py",
                "6fbccade6d6d347ca11a6f8ace061dad56202bf733959ed40990e1dd21630410",
            ),
        ),
        "topology_sha256": (
            "34df0d425948009ab8de4d1d2f8a08cf44125991480a7ee731c98cad8859b0e5"
        ),
        "candidate_pool_count": 3,
        "candidate_pool_script_sha256": (
            "a40cdc07c8b35c4eb7a266da8572ed1b4d32cf82aa24c7871577c18e8e7d35e3"
        ),
        "candidate_pool_logical_sha256": (
            "5bf95cc6a319769c1d61934ee33342ab3222342e5faff468ca1d392d66b85efd"
        ),
        "balanced_seed_substituted": False,
        "dependency_curried_body_kernel_accepted": True,
        "dependency_curried_body_dne_count": 0,
        "dependency_curried_body_metrics": (1_484, 1_484, 143, 46_398, 270),
        "default_max_body_envelope_depth": 256,
        "other_default_body_caps_pass": True,
        "default_interner_returned_none": True,
        "diagnostic_max_body_envelope_depth": 270,
        "diagnostic_interner_succeeded": True,
        "direct_closure_kernel_accepted": True,
        "direct_closure_dne_count": 0,
        "direct_closure_metrics": (13_336, 143, 3_140, 3_192, 53),
        "direct_cut_corruptions_rejected": (True, True),
        "proof_dag_sha256": (
            "388f801f63d8cc7d4ca2b286791ead04ba8c3619d511f4e4f8176bc9600f1922"
        ),
    },
}

EXPECTED_SEED_BODY_ENVELOPE = (1_484, 1_484, 143, 46_398, 270)
EXPECTED_SEED_DIRECT_CLOSURE = (13_336, 143, 3_140, 3_192, 53)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class _Blueprint:
    names: tuple[str, ...]
    targets: tuple[Formula, ...]
    dependencies: tuple[tuple[int, ...], ...]
    layers: tuple[tuple[int, ...], ...]
    kinds: tuple[str, ...]
    root: int
    topology_sha256: str


@lru_cache(maxsize=1)
def _alpha_entries() -> tuple[editions_v7.EditionEntry, ...]:
    assert (
        editions_v7.ALPHA_V7_ENROLLMENT_SHA256
        == EXPECTED_ALPHA_V7_ENROLLMENT_SHA256
    )
    assert (
        editions_v7.ALPHA_V7_IDENTITY_SHA256
        == EXPECTED_ALPHA_V7_IDENTITY_SHA256
    )
    assert (
        editions_v7.EXPECTED_ALPHA_V7_ENROLLMENT_SHA256
        == EXPECTED_ALPHA_V7_ENROLLMENT_SHA256
    )
    assert (
        editions_v7.EXPECTED_ALPHA_V7_IDENTITY_SHA256
        == EXPECTED_ALPHA_V7_IDENTITY_SHA256
    )

    entries: list[editions_v7.EditionEntry] = []
    for root_name in ROOTS:
        item = editions_v7.entry(
            root_name,
            edition=editions_v7.EditionName.ALPHA,
        )
        assert item is not None
        assert item.spec.name == root_name
        assert item.spec.dependencies == EXPECTED_ROOT_DEPENDENCIES[root_name]
        assert item.membership is editions_v7.Membership.ALPHA_ONLY
        assert item.evidence is editions_v7.EvidenceStatus.BODY_CHECKED
        assert not item.checked_use
        assert item.provenance == (item.enrollment_origin,)
        assert item.source_module == EXPECTED_SOURCE_MODULES[root_name]
        assert item.spec not in editions_v7.ALPHA_CHECKED_SPECS
        assert editions_v7.entry(
            root_name,
            edition=editions_v7.EditionName.STABLE,
        ) is None
        entries.append(item)
    return tuple(entries)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    integer_rows = make_bertrand_integer_envelope_candidate_theorems(
        TheoremSpec
    )
    power_rows = make_bertrand_power_total_candidate_theorems(TheoremSpec)
    provider_rows = {row.name: row for row in (*integer_rows, *power_rows)}
    assert len(provider_rows) == len(integer_rows) + len(power_rows)

    rows = tuple(provider_rows[name] for name in ROOTS)
    alpha_rows = tuple(item.spec for item in _alpha_entries())
    assert rows == alpha_rows
    assert tuple(row.name for row in rows) == ROOTS
    assert tuple(row.dependencies for row in rows) == tuple(
        EXPECTED_ROOT_DEPENDENCIES[name] for name in ROOTS
    )
    assert not (set(ROOTS) & set(_specs_by_name()))

    enrollment = alpha_v7_enrollment()
    assert ROOTS[0] not in enrollment.source_by_name
    for name in ROOTS[1:]:
        assert enrollment.source_by_name[name] == EXPECTED_SOURCE_MODULES[name]
        assert enrollment.test_by_name[name] == EXPECTED_V7_TEST_PATH

    for source_path, expected_sha256 in EXPECTED_SOURCE_SHA256.items():
        assert sha256(
            (REPOSITORY_ROOT / source_path).read_bytes()
        ).hexdigest() == expected_sha256
    return rows


@lru_cache(maxsize=None)
def _candidate_pool(root_name: str) -> tuple[TheoremSpec, ...]:
    rows = _candidate_specs()
    if root_name == SEED_ROOT:
        pool = rows
    elif root_name in ROOTS[:-1]:
        pool = (rows[ROOTS.index(root_name)],)
    else:
        raise AssertionError(f"unknown exact-old-seed root {root_name!r}")
    assert len({row.name for row in pool}) == len(pool)
    assert sum(row.name == root_name for row in pool) == 1
    return pool


def _pool_script_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((row.name, *row.script)) for row in rows
    )
    return sha256(payload.encode()).hexdigest()


def _pool_logical_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((row.name, row.statement, *row.dependencies))
        for row in rows
    )
    return sha256(payload.encode()).hexdigest()


def _pool_source_receipt(
    rows: tuple[TheoremSpec, ...],
) -> tuple[tuple[str, str], ...]:
    source_paths = sorted(
        {EXPECTED_SOURCE_MODULES[row.name] for row in rows}
    )
    return tuple(
        (source_path, EXPECTED_SOURCE_SHA256[source_path])
        for source_path in source_paths
    )


@lru_cache(maxsize=None)
def _blueprint(root_name: str) -> _Blueprint:
    """Prune exactly one root and stop only at Stable theorem authority."""

    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    assert not (set(public) & set(candidates))

    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(name: str) -> None:
        if name in public:
            stable_names.add(name)
            return
        item = candidates.get(name)
        if item is None:
            raise AssertionError(
                f"unknown dependency {name!r} below {root_name!r}"
            )
        mark = marks.get(name, 0)
        if mark == 1:
            raise AssertionError(
                f"cyclic dependency at {name!r} below {root_name!r}"
            )
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(root_name)
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
        else tuple(positions[name] for name in item.dependencies)
        for kind, item in zip(kinds, selected_specs, strict=True)
    )

    depths: list[int] = []
    for node_id, node_dependencies in enumerate(dependencies):
        assert all(dependency < node_id for dependency in node_dependencies)
        depths.append(
            0
            if not node_dependencies
            else 1 + max(depths[item] for item in node_dependencies)
        )
    layer_lists: list[list[int]] = [
        [] for _ in range(1 + max(depths, default=0))
    ]
    for node_id, depth in enumerate(depths):
        layer_lists[depth].append(node_id)
    layers = tuple(tuple(layer) for layer in layer_lists)

    topology_rows = (
        "\x1f".join(
            (
                str(node_id),
                name,
                kinds[node_id],
                selected_specs[node_id].statement,
                "\x1e".join(
                    names[dependency]
                    for dependency in dependencies[node_id]
                ),
            )
        )
        for node_id, name in enumerate(names)
    )
    return _Blueprint(
        names=names,
        targets=targets,
        dependencies=dependencies,
        layers=layers,
        kinds=kinds,
        root=positions[root_name],
        topology_sha256=sha256(
            "\x1c".join(topology_rows).encode()
        ).hexdigest(),
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets_by_name: dict[str, Formula],
) -> Proof:
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
                f"candidate body {item.name!r} delegated through use"
            )
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=None)
def _direct_close(name: str) -> tuple[Formula, Proof]:
    """Rebuild one exact candidate closure without LayeredReplay authority."""

    public = _specs_by_name()
    if name in public:
        theorem = replay(name)
        assert theorem.spec == public[name]
        assert theorem.formula == _closed_formula(public[name].statement)
        return theorem.formula, theorem.certificate

    candidates = {row.name: row for row in _candidate_specs()}
    item = candidates.get(name)
    assert item is not None, f"unknown exact old-seed dependency {name!r}"
    targets_by_name = {
        item.name: _closed_formula(item.statement),
        **{
            dependency: _closed_formula(
                (candidates.get(dependency) or public[dependency]).statement
            )
            for dependency in item.dependencies
        },
    }
    body = _dependency_curried_body(item, targets_by_name)
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body

    formula = targets_by_name[item.name]
    for dependency in reversed(item.dependencies):
        dependency_formula, dependency_proof = _direct_close(dependency)
        assert dependency_formula == targets_by_name[dependency]
        body = Cut(dependency_formula, formula, dependency_proof, body)
    return formula, body


def _mutate_direct_cut(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(
            certificate,
            proposition=Eq(zero, zero),
            lemma=EqRefl(zero),
        )
    return replace(
        certificate,
        body=_mutate_direct_cut(certificate.body, index - 1),
    )


def _bundle(root_name: str) -> LayeredReplayBundle:
    """Build fresh proof bodies for exactly one selected root."""

    blueprint = _blueprint(root_name)
    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    targets_by_name = dict(
        zip(blueprint.names, blueprint.targets, strict=True)
    )
    nodes: list[LayeredReplayNode] = []
    built_candidates: list[str] = []
    for node_id, name in enumerate(blueprint.names):
        if blueprint.kinds[node_id] == "stable_atomic":
            stable_entry = editions_v7.entry(
                name,
                edition=editions_v7.EditionName.STABLE,
            )
            assert stable_entry is not None
            assert stable_entry.spec == public[name]
            assert stable_entry.membership is editions_v7.Membership.STABLE
            assert (
                stable_entry.evidence
                is editions_v7.EvidenceStatus.STABLE_CLOSED
            )
            theorem = replay(name)
            assert theorem.formula == blueprint.targets[node_id]
            assert theorem.spec == public[name]
            body = theorem.certificate
        else:
            built_candidates.append(name)
            body = _dependency_curried_body(
                candidates[name], targets_by_name
            )
        nodes.append(
            LayeredReplayNode(
                node_id=node_id,
                target=blueprint.targets[node_id],
                dependencies=blueprint.dependencies[node_id],
                body=body,
            )
        )
    assert tuple(built_candidates) == tuple(
        name
        for name, kind in zip(
            blueprint.names, blueprint.kinds, strict=True
        )
        if kind == "candidate_body"
    )
    return LayeredReplayBundle(tuple(nodes), blueprint.root)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _proof_union_object_count(proofs: tuple[Proof, ...]) -> int:
    pending = list(proofs)
    seen: set[int] = set()
    while pending:
        proof = pending.pop()
        identity = id(proof)
        if identity in seen:
            continue
        seen.add(identity)
        pending.extend(_proof_children(proof))
    return len(seen)


def _proof_dag_sha256(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
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
                digests[id(value)]
                if isinstance(value, Proof)
                else repr(value)
            )
        digests[identity] = sha256(
            "\x1f".join(payload).encode()
        ).hexdigest()
    return digests[id(proof)]


def test_exact_old_seed_static_manifest_is_fail_closed() -> None:
    assert tuple(EXPECTED_ROOT_DEPENDENCIES) == ROOTS
    assert tuple(EXPECTED_SOURCE_MODULES) == ROOTS
    assert tuple(EXPECTED_AUDIT_RECEIPTS) == ROOTS
    assert all(
        isinstance(EXPECTED_AUDIT_RECEIPTS[name], dict)
        for name in LAYERED_ROOTS
    )
    seed_expected = EXPECTED_AUDIT_RECEIPTS[SEED_ROOT]
    assert (
        seed_expected == PENDING_EXACT_OLD_SEED_BLOCKER_RECEIPT
        or isinstance(seed_expected, dict)
    )
    assert tuple(item.spec.name for item in _alpha_entries()) == ROOTS
    assert tuple(row.name for row in _candidate_specs()) == ROOTS
    assert tuple(row.name for row in _candidate_pool(ROOTS[0])) == ROOTS[:1]
    assert tuple(row.name for row in _candidate_pool(ROOTS[1])) == ROOTS[1:2]
    assert tuple(row.name for row in _candidate_pool(SEED_ROOT)) == ROOTS


@pytest.mark.parametrize("root_name", LAYERED_ROOTS, ids=LAYERED_ROOTS)
def test_exact_old_seed_prerequisite_layered_empty_context_closure(
    root_name: str,
) -> None:
    """Compile one exact prerequisite root, never the blocked seed body."""

    blueprint = _blueprint(root_name)
    pool = _candidate_pool(root_name)
    candidates = {row.name: row for row in pool}
    public = _specs_by_name()
    stable_names = {
        name
        for name, kind in zip(
            blueprint.names, blueprint.kinds, strict=True
        )
        if kind == "stable_atomic"
    }
    candidate_names = set(blueprint.names) - stable_names

    assert blueprint.names[blueprint.root] == root_name
    assert blueprint.targets[blueprint.root] == _closed_formula(
        candidates[root_name].statement
    )
    assert stable_names <= set(public)
    assert not (candidate_names & set(public))
    assert candidate_names == set(candidates)
    assert set(blueprint.kinds) <= {"stable_atomic", "candidate_body"}
    assert blueprint.kinds == (
        ("stable_atomic",) * len(stable_names)
        + ("candidate_body",) * len(candidate_names)
    )
    assert tuple(
        blueprint.names[dependency]
        for dependency in blueprint.dependencies[blueprint.root]
    ) == EXPECTED_ROOT_DEPENDENCIES[root_name]
    assert blueprint.root in blueprint.layers[-1]
    assert all(tuple(sorted(layer)) == layer for layer in blueprint.layers)
    assert {
        node_id for layer in blueprint.layers for node_id in layer
    } == set(range(len(blueprint.names)))
    assert all(
        dependency < node_id
        for node_id, dependencies in enumerate(blueprint.dependencies)
        for dependency in dependencies
    )
    for node_id, name in enumerate(blueprint.names):
        if blueprint.kinds[node_id] == "stable_atomic":
            assert blueprint.dependencies[node_id] == ()
        else:
            assert tuple(
                blueprint.names[dependency]
                for dependency in blueprint.dependencies[node_id]
            ) == candidates[name].dependencies

    reachable: set[int] = set()
    pending = [blueprint.root]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(blueprint.dependencies[node_id])
    assert reachable == set(range(len(blueprint.names)))

    assert candidate_names == {root_name}
    balanced_seed_substituted = False

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    assert len(blueprint.names) <= limits.max_nodes
    assert sum(map(len, blueprint.dependencies)) <= (
        limits.max_dependency_edges
    )
    assert max(map(len, blueprint.dependencies)) <= (
        limits.max_dependencies_per_node
    )

    raw_bundle = _bundle(root_name)
    interned_bundle = intern_layered_replay_bodies(
        raw_bundle,
        blueprint.targets[blueprint.root],
        limits=limits,
    )
    assert type(interned_bundle) is LayeredReplayBundle
    assert interned_bundle.root == raw_bundle.root
    assert len(interned_bundle.nodes) == len(raw_bundle.nodes)
    for raw_node, interned_node in zip(
        raw_bundle.nodes, interned_bundle.nodes, strict=True
    ):
        assert type(interned_node) is LayeredReplayNode
        assert interned_node.node_id == raw_node.node_id
        assert interned_node.target is raw_node.target
        assert interned_node.dependencies is raw_node.dependencies
        assert interned_node.body == raw_node.body

    raw_body_union_objects = _proof_union_object_count(
        tuple(node.body for node in raw_bundle.nodes)
    )
    interned_body_union_objects = _proof_union_object_count(
        tuple(node.body for node in interned_bundle.nodes)
    )
    assert interned_body_union_objects <= raw_body_union_objects
    assert interned_body_union_objects <= limits.max_total_body_objects
    body_union_object_savings = (
        raw_body_union_objects - interned_body_union_objects
    )

    targets_by_id = {
        node.node_id: node.target for node in interned_bundle.nodes
    }
    for node in interned_bundle.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(targets_by_id[dependency], body_target)
        assert check((), node.body, body_target), (
            f"interned body failed exact kernel judgment at {node.node_id} "
            f"({blueprint.names[node.node_id]!r}) below {root_name!r}"
        )
        assert not any(type(item) is DNE for item in _walk(node.body))

    compilation = compile_layered_replay(
        interned_bundle,
        blueprint.targets[blueprint.root],
        limits=limits,
    )
    assert type(compilation) is LayeredReplayCandidate
    assert compilation.target == blueprint.targets[blueprint.root]
    assert compilation.layers == blueprint.layers
    assert len(compilation.package_formulas) == len(blueprint.layers)
    assert compilation.package_formula_occurrences <= (
        limits.max_package_formula_occurrences
    )
    assert compilation.maximum_package_formula_depth <= (
        limits.max_package_formula_depth
    )
    assert compilation.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compilation.proof_objects <= limits.max_candidate_proof_objects
    assert compilation.proof_depth <= limits.max_candidate_proof_depth
    assert compilation.proof_annotation_occurrences <= (
        limits.max_candidate_annotation_occurrences
    )
    assert compilation.proof_envelope_depth <= (
        limits.max_candidate_envelope_depth
    )
    assert compilation.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert compilation.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert compilation.proof_objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(
        type(item) is DNE for item in _walk(compilation.certificate)
    )

    kernel_accepted = check(
        (), compilation.certificate, compilation.target
    )
    assert type(compilation.certificate) is Cut
    zero = Zero()
    corrupted = replace(
        compilation.certificate,
        proposition=Eq(zero, zero),
        lemma=EqRefl(zero),
    )
    direct_cut_corruption_rejected = not check(
        (), corrupted, compilation.target
    )

    actual: dict[str, object] = {
        "root_name": root_name,
        "alpha_v7_enrollment_sha256": (
            EXPECTED_ALPHA_V7_ENROLLMENT_SHA256
        ),
        "alpha_v7_identity_sha256": EXPECTED_ALPHA_V7_IDENTITY_SHA256,
        "provider_sources": _pool_source_receipt(pool),
        "topology_sha256": blueprint.topology_sha256,
        "candidate_pool_count": len(pool),
        "candidate_pool_script_sha256": _pool_script_sha256(pool),
        "candidate_pool_logical_sha256": _pool_logical_sha256(pool),
        "balanced_seed_substituted": balanced_seed_substituted,
        "node_count": len(blueprint.names),
        "stable_atomic_count": len(stable_names),
        "candidate_body_count": len(candidate_names),
        "dependency_edge_count": sum(map(len, blueprint.dependencies)),
        "layer_sizes": tuple(map(len, blueprint.layers)),
        "max_fan_in": max(map(len, blueprint.dependencies)),
        "raw_body_union_objects": raw_body_union_objects,
        "interned_body_union_objects": interned_body_union_objects,
        "body_union_object_savings": body_union_object_savings,
        "proof_nodes": compilation.proof_nodes,
        "proof_depth": compilation.proof_depth,
        "proof_objects": compilation.proof_objects,
        "proof_edges": compilation.proof_edges,
        "reused_objects": compilation.reused_objects,
        "annotation_occurrences": (
            compilation.proof_annotation_occurrences
        ),
        "envelope_depth": compilation.proof_envelope_depth,
        "package_formula_occurrences": (
            compilation.package_formula_occurrences
        ),
        "package_formula_depth": (
            compilation.maximum_package_formula_depth
        ),
        "proof_dag_sha256": _proof_dag_sha256(compilation.certificate),
        "direct_cut_corruption_rejected": (
            direct_cut_corruption_rejected
        ),
    }
    print(
        "BERTRAND EXACT OLD POWER SEED PREREQUISITE LAYERED RECEIPT "
        f"root={root_name!r} actual={actual!r} "
        f"kernel_accepted={kernel_accepted}",
        flush=True,
    )
    assert kernel_accepted
    assert direct_cut_corruption_rejected
    expected = EXPECTED_AUDIT_RECEIPTS[root_name]
    assert isinstance(expected, dict), (
        f"freeze the isolated receipt for {root_name!r} only after the "
        f"kernel accepts it and rejects the direct Cut corruption: {actual!r}"
    )
    assert actual == expected


def test_exact_old_seed_body_envelope_blocker_and_direct_closure() -> None:
    """Freeze the exact Layered blocker and independent direct closure."""

    blueprint = _blueprint(SEED_ROOT)
    pool = _candidate_pool(SEED_ROOT)
    assert tuple(row.name for row in pool) == ROOTS
    assert blueprint.names[blueprint.root] == SEED_ROOT
    assert blueprint.targets[blueprint.root] == _closed_formula(
        pool[-1].statement
    )
    assert tuple(
        blueprint.names[dependency]
        for dependency in blueprint.dependencies[blueprint.root]
    ) == EXPECTED_ROOT_DEPENDENCIES[SEED_ROOT]

    raw_bundle = _bundle(SEED_ROOT)
    seed_node = raw_bundle.nodes[blueprint.root]
    assert seed_node.target == blueprint.targets[blueprint.root]
    assert seed_node.dependencies == blueprint.dependencies[blueprint.root]
    targets_by_id = {
        node.node_id: node.target for node in raw_bundle.nodes
    }
    seed_body_target = seed_node.target
    for dependency in reversed(seed_node.dependencies):
        seed_body_target = Imp(
            targets_by_id[dependency], seed_body_target
        )
    seed_body_kernel_accepted = check(
        (), seed_node.body, seed_body_target
    )
    seed_body_dne_count = sum(
        type(item) is DNE for item in _walk(seed_node.body)
    )

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    diagnostic_limits = replace(
        limits,
        max_body_envelope_depth=EXPECTED_SEED_BODY_ENVELOPE[-1],
    )
    assert tuple(
        item.name
        for item in fields(limits)
        if getattr(limits, item.name)
        != getattr(diagnostic_limits, item.name)
    ) == ("max_body_envelope_depth",)
    seed_body_metrics = _proof_envelope_metrics_bounded(
        seed_node.body,
        max_proof_occurrences=diagnostic_limits.max_body_occurrences,
        max_proof_objects=diagnostic_limits.max_body_objects,
        max_proof_depth=diagnostic_limits.max_body_depth,
        max_annotation_occurrences=(
            diagnostic_limits.max_body_annotation_occurrences
        ),
        max_annotation_depth=diagnostic_limits.max_formula_depth,
        max_envelope_depth=diagnostic_limits.max_body_envelope_depth,
        label="exact old seed diagnostic body",
    )
    (
        body_occurrences,
        body_objects,
        body_proof_depth,
        body_annotation_occurrences,
        body_envelope_depth,
    ) = seed_body_metrics
    other_default_body_caps_pass = all(
        (
            body_occurrences <= limits.max_body_occurrences,
            body_objects <= limits.max_body_objects,
            body_proof_depth <= limits.max_body_depth,
            body_annotation_occurrences
            <= limits.max_body_annotation_occurrences,
        )
    )
    default_interned = intern_layered_replay_bodies(
        raw_bundle,
        blueprint.targets[blueprint.root],
        limits=limits,
    )
    diagnostic_interned = intern_layered_replay_bodies(
        raw_bundle,
        blueprint.targets[blueprint.root],
        limits=diagnostic_limits,
    )
    default_interner_returned_none = default_interned is None
    diagnostic_interner_succeeded = (
        type(diagnostic_interned) is LayeredReplayBundle
    )

    direct_formula, direct_certificate = _direct_close(SEED_ROOT)
    direct_kernel_accepted = check(
        (), direct_certificate, direct_formula
    )
    direct_dne_count = sum(
        type(item) is DNE for item in _walk(direct_certificate)
    )
    direct_nodes, direct_depth = proof_metrics(direct_certificate)
    direct_objects, direct_edges, direct_reused = proof_identity_metrics(
        direct_certificate
    )
    direct_metrics = (
        direct_nodes,
        direct_depth,
        direct_objects,
        direct_edges,
        direct_reused,
    )
    direct_cut_corruptions_rejected = tuple(
        not check(
            (),
            _mutate_direct_cut(direct_certificate, index),
            direct_formula,
        )
        for index in range(len(EXPECTED_ROOT_DEPENDENCIES[SEED_ROOT]))
    )

    actual: dict[str, object] = {
        "root_name": SEED_ROOT,
        "audit_kind": (
            "layered_body_envelope_blocker_and_direct_closure"
        ),
        "alpha_v7_enrollment_sha256": (
            EXPECTED_ALPHA_V7_ENROLLMENT_SHA256
        ),
        "alpha_v7_identity_sha256": EXPECTED_ALPHA_V7_IDENTITY_SHA256,
        "provider_sources": _pool_source_receipt(pool),
        "topology_sha256": blueprint.topology_sha256,
        "candidate_pool_count": len(pool),
        "candidate_pool_script_sha256": _pool_script_sha256(pool),
        "candidate_pool_logical_sha256": _pool_logical_sha256(pool),
        "balanced_seed_substituted": False,
        "dependency_curried_body_kernel_accepted": (
            seed_body_kernel_accepted
        ),
        "dependency_curried_body_dne_count": seed_body_dne_count,
        "dependency_curried_body_metrics": seed_body_metrics,
        "default_max_body_envelope_depth": (
            limits.max_body_envelope_depth
        ),
        "other_default_body_caps_pass": other_default_body_caps_pass,
        "default_interner_returned_none": (
            default_interner_returned_none
        ),
        "diagnostic_max_body_envelope_depth": (
            diagnostic_limits.max_body_envelope_depth
        ),
        "diagnostic_interner_succeeded": diagnostic_interner_succeeded,
        "direct_closure_kernel_accepted": direct_kernel_accepted,
        "direct_closure_dne_count": direct_dne_count,
        "direct_closure_metrics": direct_metrics,
        "direct_cut_corruptions_rejected": (
            direct_cut_corruptions_rejected
        ),
        "proof_dag_sha256": _proof_dag_sha256(direct_certificate),
    }
    print(
        "BERTRAND EXACT OLD POWER SEED CAP BLOCKER RECEIPT "
        f"actual={actual!r}",
        flush=True,
    )

    assert direct_formula == blueprint.targets[blueprint.root]
    assert seed_body_kernel_accepted
    assert seed_body_dne_count == 0
    assert seed_body_metrics == EXPECTED_SEED_BODY_ENVELOPE
    assert other_default_body_caps_pass
    assert body_envelope_depth > limits.max_body_envelope_depth
    assert default_interner_returned_none
    assert diagnostic_interner_succeeded
    assert direct_kernel_accepted
    assert direct_dne_count == 0
    assert direct_metrics == EXPECTED_SEED_DIRECT_CLOSURE
    assert direct_nodes <= MAX_LIVE_PROOF_NODES
    assert direct_depth <= MAX_LIVE_PROOF_DEPTH
    assert direct_objects <= MAX_LIVE_PROOF_OBJECTS
    assert direct_cut_corruptions_rejected == (True, True)

    expected = EXPECTED_AUDIT_RECEIPTS[SEED_ROOT]
    assert isinstance(expected, dict), (
        "freeze the exact old-seed blocker/direct-closure receipt only "
        f"after one isolated diagnostic run: {actual!r}"
    )
    assert actual == expected
