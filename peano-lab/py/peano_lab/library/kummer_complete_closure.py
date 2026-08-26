"""Complete constructive proof graph for both exact Alpha-v17 Kummer roots.

The immutable parent contains 280 transitive theorem rows: 171 Stable rows,
11 independently closed Alpha rows, and 98 dependency-curried body-only rows.
Genuine quadratic-reciprocity and supplementary-law proof artifacts supply 175
checked parent bodies.  The other seven already-checked parent bodies and all
98 missing bodies are reconstructed from their exact, unchanged scripts in
microbatches bounded by 16 bodies, 125,000 proof nodes, and 25,000 objects.

The resulting artifact contains ordinary intuitionistic proof data only.  A
synthetic conjunction makes both exact original Kummer endpoints reachable;
it is not enrolled and introduces no new axiom or kernel rule.  Planning,
construction, independent verification, and export never change the immutable
Alpha-v17 release, its checked-use authority, or the Stable channel.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v16 as v16
from . import editions_v17 as v17
from .frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayError,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
)
from .proof_bundle import (
    BundleNode,
    CheckedProofBundle,
    ProofBundle,
    ProofBundleError,
    check_proof_bundle,
    decode_proof_bundle,
    encode_proof_bundle,
)
from .quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from .supplementary_laws_closure import (
    SupplementaryClosureError,
    checked_supplementary_proof_bundle,
    supplementary_laws_closure_plan,
)
from .theorems import CheckedTheorem, _closed_formula, _primitive


KUMMER_ROOT_NAMES = (
    "kummer_binomial_carry_bit_count",
    "kummer_carry_free_iff_not_divides",
)
EXPECTED_KUMMER_THEOREM_COUNT = 280
EXPECTED_KUMMER_STABLE_COUNT = 171
EXPECTED_KUMMER_ALPHA_CLOSED_COUNT = 11
EXPECTED_KUMMER_PENDING_COUNT = 98
EXPECTED_KUMMER_REUSED_PARENT_COUNT = 175
EXPECTED_KUMMER_RECONSTRUCTED_PARENT_COUNT = 7
EXPECTED_KUMMER_CONSTRUCTED_BODY_COUNT = 105
EXPECTED_KUMMER_DEPENDENCY_EDGE_COUNT = 777
EXPECTED_KUMMER_BUNDLE_NODE_COUNT = 281
EXPECTED_KUMMER_BUNDLE_EDGE_COUNT = 779
EXPECTED_KUMMER_BUNDLE_BODY_PROOF_NODES = 19_062
EXPECTED_KUMMER_BUNDLE_BYTES = 1_528_814
EXPECTED_KUMMER_BUNDLE_SHA256 = (
    "49fd86708fe5b289d0159526285e73b2aea008c26e0eb41ae8a053c970d4210e"
)
EXPECTED_KUMMER_ROOT_NODE_IDS = (277, 279)
EXPECTED_KUMMER_ROOT_PROOF_NODES = (23_564, 24_170)
EXPECTED_KUMMER_ROOT_STATEMENT_SHA256 = (
    "f9f7312eacb89563dff059b63d310a3148b0b7df7f9e0425bbf4fdbd868e3c4f",
    "ed30b756bd9703193020ae395a87f1f32a12859d2b9df8fbb79708e9bed2dc00",
)
EXPECTED_KUMMER_ORDERED_NAMES_SHA256 = (
    "87c0aa87596f7177836f4171728027e7d372d56214d34e602680f7ddb7d6c881"
)
EXPECTED_KUMMER_PENDING_NAMES_SHA256 = (
    "50d495e0dff1489e42098198b667c71060bacaf32c2de3b10935129b8f87fd3b"
)
EXPECTED_KUMMER_SURFACE_SHA256 = (
    "1e0778b0e2415aa6b4f74dd500fe54f00c039f29eab375e080aa7aeec9bbfe34"
)
KUMMER_RECONSTRUCTED_CHECKED_NAMES = (
    "mul_lt_mul_succ_left_nonzero",
    "zero_remainder_implies_multiple",
    "multiple_has_zero_remainder",
    "one_multiple",
    "multiple_decidable_nonzero",
    "multiple_decidable",
    "add_shuffle_middle",
)


class KummerClosureError(ValueError):
    """The exact frozen Kummer surface, actual proof, or resource cap failed."""


@dataclass(frozen=True, slots=True)
class KummerClosureRow:
    """One immutable exact Alpha-v17 theorem row, with unchanged evidence."""

    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    evidence: str
    enrollment_origin: str

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v17.EvidenceStatus.BODY_CHECKED.value


@dataclass(frozen=True, slots=True)
class KummerClosurePlan:
    """Sealed dependency graph and genuine-body sources; never authority."""

    roots: tuple[str, str]
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[KummerClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    pending_names_sha256: str
    surface_sha256: str
    reused_parent_names: tuple[str, ...]
    reconstructed_parent_names: tuple[str, ...]

    @property
    def pending_rows(self) -> tuple[KummerClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def checked_parent_rows(self) -> tuple[KummerClosureRow, ...]:
        return tuple(row for row in self.rows if not row.needs_closure)

    @property
    def construction_rows(self) -> tuple[KummerClosureRow, ...]:
        extra = frozenset(self.reconstructed_parent_names)
        return tuple(row for row in self.rows if row.needs_closure or row.name in extra)


@dataclass(frozen=True, slots=True)
class KummerCheckedBody:
    """An actual checked dependency-curried proof; never release authority."""

    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    target: Formula
    curried_target: Formula
    certificate: Proof
    proof_nodes: int
    proof_objects: int
    proof_depth: int
    annotation_occurrences: int
    envelope_depth: int


@dataclass(frozen=True, slots=True)
class KummerBodyMicrobatch:
    """At most sixteen actual bodies under the unchanged hard resource caps."""

    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[KummerCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class KummerCheckedBundle:
    """Self-contained actual proof data accepted by the original kernel."""

    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


@lru_cache(maxsize=1)
def kummer_complete_closure_plan() -> KummerClosurePlan:
    """Seal both exact transitive root slices without replaying any proof."""

    table = v17.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = list(reversed(KUMMER_ROOT_NAMES))
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise KummerClosureError(f"unknown frozen Alpha-v17 dependency {name!r}")
        if item.evidence is v17.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise KummerClosureError(f"Kummer dependency {name!r} has pending evidence")
        selected.add(name)
        pending.extend(reversed(item.spec.dependencies))

    rows: list[KummerClosureRow] = []
    surfaces: list[dict[str, object]] = []
    seen: set[str] = set()
    for alpha_index, item in enumerate(v17.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        if not set(item.spec.dependencies).issubset(seen):
            raise KummerClosureError(f"non-topological frozen Kummer row {item.spec.name!r}")
        digest = sha256(item.spec.statement.encode("utf-8")).hexdigest()
        row = KummerClosureRow(
            node_id=len(rows),
            alpha_index=alpha_index,
            name=item.spec.name,
            statement_sha256=digest,
            dependencies=item.spec.dependencies,
            evidence=item.evidence.value,
            enrollment_origin=item.enrollment_origin.value,
        )
        rows.append(row)
        surfaces.append(
            {
                "alpha_index": alpha_index,
                "name": row.name,
                "statement_sha256": digest,
                "dependencies": row.dependencies,
                "evidence": row.evidence,
                "enrollment_origin": row.enrollment_origin,
            }
        )
        seen.add(row.name)
    if seen != selected:
        raise KummerClosureError("Kummer transitive dependency closure is incomplete")

    edges = sum(len(row.dependencies) for row in rows)
    unclosed = tuple(row for row in rows if row.needs_closure)
    names_digest = sha256("\n".join(row.name for row in rows).encode()).hexdigest()
    pending_digest = sha256("\n".join(row.name for row in unclosed).encode()).hexdigest()
    surface_digest = sha256(
        json.dumps(
            surfaces,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    if (
        len(rows) != EXPECTED_KUMMER_THEOREM_COUNT
        or len(unclosed) != EXPECTED_KUMMER_PENDING_COUNT
        or edges != EXPECTED_KUMMER_DEPENDENCY_EDGE_COUNT
        or names_digest != EXPECTED_KUMMER_ORDERED_NAMES_SHA256
        or pending_digest != EXPECTED_KUMMER_PENDING_NAMES_SHA256
        or surface_digest != EXPECTED_KUMMER_SURFACE_SHA256
    ):
        raise KummerClosureError("the exact immutable Alpha-v17 Kummer surface changed")
    if Counter(row.evidence for row in rows) != {
        "stable_closed": EXPECTED_KUMMER_STABLE_COUNT,
        "alpha_closed": EXPECTED_KUMMER_ALPHA_CLOSED_COUNT,
        "body_checked": EXPECTED_KUMMER_PENDING_COUNT,
    }:
        raise KummerClosureError("the exact Kummer parent evidence partition changed")

    locations = {row.name: row.node_id for row in rows}
    if tuple(locations[name] for name in KUMMER_ROOT_NAMES) != EXPECTED_KUMMER_ROOT_NODE_IDS:
        raise KummerClosureError("the exact Kummer endpoint node identities changed")
    if tuple(rows[locations[name]].statement_sha256 for name in KUMMER_ROOT_NAMES) != (
        EXPECTED_KUMMER_ROOT_STATEMENT_SHA256
    ):
        raise KummerClosureError("an exact immutable Kummer endpoint formula changed")

    qr_names = {spec.name for spec in quadratic_reciprocity_stack().admission_order}
    supplementary_names = {
        row.name for row in supplementary_laws_closure_plan().rows
    }
    reusable = qr_names | supplementary_names
    reused = tuple(row.name for row in rows if not row.needs_closure and row.name in reusable)
    reconstructed = tuple(
        row.name for row in rows if not row.needs_closure and row.name not in reusable
    )
    if (
        len(reused) != EXPECTED_KUMMER_REUSED_PARENT_COUNT
        or reconstructed != KUMMER_RECONSTRUCTED_CHECKED_NAMES
    ):
        raise KummerClosureError("the exact checked-parent proof-body partition changed")

    return KummerClosurePlan(
        roots=KUMMER_ROOT_NAMES,
        parent_alpha_identity_sha256=v17.ALPHA_V17_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=v17.ALPHA_V17_ENROLLMENT_SHA256,
        rows=tuple(rows),
        dependency_edge_count=edges,
        ordered_names_sha256=names_digest,
        pending_names_sha256=pending_digest,
        surface_sha256=surface_digest,
        reused_parent_names=reused,
        reconstructed_parent_names=reconstructed,
    )


def _sealed_plan(plan: KummerClosurePlan | None) -> KummerClosurePlan:
    expected = kummer_complete_closure_plan()
    if plan is not None and (type(plan) is not KummerClosurePlan or plan != expected):
        raise KummerClosureError("Kummer plan differs from its exact frozen Alpha-v17 surface")
    return expected


def _completed_construction_names(
    names: Sequence[str] | frozenset[str],
    plan: KummerClosurePlan,
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise KummerClosureError("completed Kummer body names must be a tuple, list, or frozenset")
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise KummerClosureError("completed Kummer body names must be distinct exact strings")
    result = set(names)
    known = {row.name for row in plan.construction_rows}
    unknown = result.difference(known)
    if unknown:
        raise KummerClosureError(f"unknown completed Kummer body rows: {sorted(unknown)!r}")
    for row in plan.construction_rows:
        if row.name in result:
            missing = set(row.dependencies).intersection(known).difference(result)
            if missing:
                raise KummerClosureError(
                    f"completed Kummer rows are not dependency closed at {row.name!r}: "
                    f"{sorted(missing)!r}"
                )
    return result


def kummer_pending_layers(
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: KummerClosurePlan | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return exact body-only dependency waves; names grant no authority."""

    selected = _sealed_plan(plan)
    known = {row.name for row in selected.pending_rows}
    if isinstance(completed_names, str) or not isinstance(
        completed_names, (tuple, list, frozenset)
    ):
        raise KummerClosureError("completed pending Kummer rows must be an exact collection")
    supplied = set(completed_names)
    if len(supplied) != len(completed_names) or not supplied.issubset(known):
        raise KummerClosureError("completed pending Kummer rows are unknown or repeated")
    available = {row.name for row in selected.checked_parent_rows} | supplied
    for row in selected.pending_rows:
        if row.name in supplied and not set(row.dependencies).issubset(available):
            raise KummerClosureError("completed pending Kummer rows are not dependency closed")
    remaining = [row for row in selected.pending_rows if row.name not in supplied]
    result: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name for row in remaining if set(row.dependencies).issubset(available)
        )
        if not ready:
            raise KummerClosureError("exact pending Kummer dependency graph is cyclic")
        result.append(ready)
        available.update(ready)
        remaining = [row for row in remaining if row.name not in available]
    return tuple(result)


@lru_cache(maxsize=None)
def _frozen_formula(name: str) -> Formula:
    item = v17.ALPHA_EDITION.by_name.get(name)
    if item is None:
        raise KummerClosureError(f"unknown frozen Alpha-v17 theorem {name!r}")
    return _closed_formula(item.spec.statement)


def _body_target(row: KummerClosureRow) -> tuple[Formula, Formula]:
    item = v17.ALPHA_ENTRIES[row.alpha_index]
    if (
        item.spec.name != row.name
        or sha256(item.spec.statement.encode()).hexdigest() != row.statement_sha256
    ):
        raise KummerClosureError(f"Kummer proof row {row.name!r} changed its exact parent")
    target = _frozen_formula(row.name)
    curried = target
    for dependency in reversed(row.dependencies):
        curried = Imp(_frozen_formula(dependency), curried)
    return target, curried


def _body_metrics(
    certificate: Proof,
    *,
    node_budget: int,
    object_budget: int,
    label: str,
) -> tuple[int, int, int, int, int]:
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        return _proof_envelope_metrics_bounded(
            certificate,
            max_proof_occurrences=node_budget,
            max_proof_objects=object_budget,
            max_proof_depth=limits.max_body_depth,
            max_annotation_occurrences=limits.max_body_annotation_occurrences,
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_body_envelope_depth,
            label=label,
        )
    except (AttributeError, LayeredReplayError, RecursionError, TypeError, ValueError) as exc:
        raise KummerClosureError(
            f"{label} violates the unchanged 125000-node/25000-object envelope"
        ) from exc


def construct_kummer_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: KummerClosurePlan | None = None,
) -> KummerBodyMicrobatch:
    """Construct at most sixteen independently kernel-checked actual bodies."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise KummerClosureError("Kummer microbatch names must be a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise KummerClosureError(
            f"Kummer microbatch must contain 1..{MAX_FRONTIER_CLOSURE_MICROBATCH} bodies"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise KummerClosureError("Kummer microbatch names must be distinct exact strings")
    completed = _completed_construction_names(completed_names, selected)
    by_name = {row.name: row for row in selected.construction_rows}
    available = set(selected.reused_parent_names) | completed
    previous = -1
    for name in names:
        row = by_name.get(name)
        if row is None:
            raise KummerClosureError(f"unknown or already-reused Kummer row {name!r}")
        if row.node_id <= previous or name in completed:
            raise KummerClosureError("Kummer microbatch repeats or reorders a theorem row")
        missing = set(row.dependencies).difference(available)
        if missing:
            raise KummerClosureError(
                f"Kummer body {name!r} lacks predecessor proofs: {sorted(missing)!r}"
            )
        available.add(name)
        previous = row.node_id

    rows: list[KummerCheckedBody] = []
    nodes = objects = annotations = 0
    for name in names:
        row = by_name[name]
        specification = v17.ALPHA_ENTRIES[row.alpha_index].spec
        target, curried = _body_target(row)
        try:
            state = start(curried)
            for dependency in specification.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for position, command in enumerate(specification.script):
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise KummerClosureError(
                        f"Kummer body {name!r} requests implicit authority at command {position}"
                    )
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
        except KummerClosureError:
            raise
        except (
            AttributeError,
            IndexError,
            KeyError,
            RecursionError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as exc:
            raise KummerClosureError(f"cannot reconstruct exact Kummer body {name!r}") from exc
        metrics = _body_metrics(
            certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"Kummer dependency-curried body {name}",
        )
        proof_nodes, proof_objects, depth, body_annotations, envelope_depth = metrics
        nodes += proof_nodes
        objects += proof_objects
        annotations += body_annotations
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise KummerClosureError("Kummer microbatch exceeds its annotation limit")
        rows.append(
            KummerCheckedBody(
                row.node_id,
                row.alpha_index,
                row.name,
                row.statement_sha256,
                target,
                curried,
                certificate,
                proof_nodes,
                proof_objects,
                depth,
                body_annotations,
                envelope_depth,
            )
        )
    return KummerBodyMicrobatch(
        selected.parent_alpha_identity_sha256,
        selected.surface_sha256,
        tuple(rows),
        nodes,
        objects,
        annotations,
    )


def verify_kummer_body_microbatch(
    batch: KummerBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: KummerClosurePlan | None = None,
) -> KummerBodyMicrobatch:
    """Recheck all genuine proof objects; diagnostics alone prove nothing."""

    selected = _sealed_plan(plan)
    if type(batch) is not KummerBodyMicrobatch:
        raise KummerClosureError("Kummer proof microbatch has an invalid exact type")
    if (
        batch.parent_alpha_identity_sha256 != selected.parent_alpha_identity_sha256
        or batch.surface_sha256 != selected.surface_sha256
    ):
        raise KummerClosureError("Kummer microbatch changed its frozen parent surface")
    if (
        type(batch.rows) is not tuple
        or not batch.rows
        or len(batch.rows) > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise KummerClosureError("Kummer microbatch exceeds its sixteen-proof policy")
    completed = _completed_construction_names(completed_names, selected)
    available = set(selected.reused_parent_names) | completed
    frozen = {row.name: row for row in selected.construction_rows}
    nodes = objects = annotations = 0
    previous = -1
    for actual in batch.rows:
        if type(actual) is not KummerCheckedBody:
            raise KummerClosureError("Kummer microbatch contains a malformed actual proof")
        expected = frozen.get(actual.name)
        if (
            expected is None
            or actual.node_id != expected.node_id
            or actual.alpha_index != expected.alpha_index
            or actual.statement_sha256 != expected.statement_sha256
        ):
            raise KummerClosureError(f"Kummer body {actual.name!r} changed its frozen identity")
        if actual.node_id <= previous or actual.name in available:
            raise KummerClosureError("Kummer proof batch repeats or reorders an actual body")
        missing = set(expected.dependencies).difference(available)
        if missing:
            raise KummerClosureError(
                f"Kummer proof {actual.name!r} lacks predecessor proofs: {sorted(missing)!r}"
            )
        target, curried = _body_target(expected)
        if actual.target != target or actual.curried_target != curried:
            raise KummerClosureError(f"Kummer proof {actual.name!r} changed its exact target")
        metrics = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"Kummer dependency-curried body {actual.name}",
        )
        if metrics != (
            actual.proof_nodes,
            actual.proof_objects,
            actual.proof_depth,
            actual.annotation_occurrences,
            actual.envelope_depth,
        ):
            raise KummerClosureError(f"Kummer body {actual.name!r} changed its proof envelope")
        if not check((), actual.certificate, curried):
            raise KummerClosureError(
                f"unchanged intuitionistic kernel rejected Kummer body {actual.name!r}"
            )
        nodes += actual.proof_nodes
        objects += actual.proof_objects
        annotations += actual.annotation_occurrences
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise KummerClosureError("Kummer microbatch exceeds its annotation limit")
        available.add(actual.name)
        previous = actual.node_id
    if (batch.proof_nodes, batch.proof_objects, batch.annotation_occurrences) != (
        nodes,
        objects,
        annotations,
    ):
        raise KummerClosureError("Kummer microbatch changed its aggregate proof envelope")
    return batch


@lru_cache(maxsize=1)
def _checked_parent_bodies() -> dict[str, Proof]:
    """Reuse only actual bodies from fully independently checked artifacts."""

    try:
        qr_bundle, _qr_receipt = v16._checked_qr_bundle()
        supplementary_bundle, _supplementary_receipt = checked_supplementary_proof_bundle()
    except (
        v16.EditionV16Error,
        SupplementaryClosureError,
        ProofBundleError,
        RecursionError,
        TypeError,
        ValueError,
    ) as exc:
        raise KummerClosureError("a genuine independently checked parent proof artifact failed") from exc
    qr = {
        specification.name: node
        for specification, node in zip(
            quadratic_reciprocity_stack().admission_order,
            qr_bundle.nodes,
            strict=True,
        )
    }
    supplementary = {
        row.name: node
        for row, node in zip(
            supplementary_laws_closure_plan().rows,
            supplementary_bundle.nodes[:-1],
            strict=True,
        )
    }
    selected = kummer_complete_closure_plan()
    result: dict[str, Proof] = {}
    for name in selected.reused_parent_names:
        node = qr.get(name) or supplementary.get(name)
        if node is None or node.target != _frozen_formula(name):
            raise KummerClosureError(f"checked parent proof body {name!r} is missing or altered")
        result[name] = node.body
    if len(result) != EXPECTED_KUMMER_REUSED_PARENT_COUNT:
        raise KummerClosureError("actual checked-parent Kummer proof-body coverage changed")
    return result


def _synthetic_conjunction_body() -> Proof:
    return ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0))))


def check_kummer_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: KummerClosurePlan | None = None,
) -> KummerCheckedBundle:
    """Check every exact theorem proof and both roots using the old kernel."""

    selected = _sealed_plan(plan)
    if type(bundle) is not ProofBundle:
        raise KummerClosureError("Kummer evidence must be an actual constructive proof bundle")
    if (
        type(bundle.nodes) is not tuple
        or len(bundle.nodes) != EXPECTED_KUMMER_BUNDLE_NODE_COUNT
        or bundle.root != EXPECTED_KUMMER_THEOREM_COUNT
    ):
        raise KummerClosureError("Kummer proof graph changed its exact node count or root")
    locations = {row.name: row.node_id for row in selected.rows}
    for row, node in zip(selected.rows, bundle.nodes[:-1], strict=True):
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != _frozen_formula(row.name)
            or node.dependencies
            != tuple(locations[dependency] for dependency in row.dependencies)
        ):
            raise KummerClosureError(f"Kummer bundle changed exact frozen theorem {row.name!r}")
    roots = tuple(locations[name] for name in selected.roots)
    exact_target = And(bundle.nodes[roots[0]].target, bundle.nodes[roots[1]].target)
    synthetic = bundle.nodes[-1]
    if (
        target != exact_target
        or type(synthetic) is not BundleNode
        or synthetic.node_id != EXPECTED_KUMMER_THEOREM_COUNT
        or synthetic.target != exact_target
        or synthetic.dependencies != roots
        or synthetic.body != _synthetic_conjunction_body()
    ):
        raise KummerClosureError("Kummer conjunction changed an exact root or constructive body")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise KummerClosureError(
            "the unchanged intuitionistic kernel rejected the complete Kummer proof graph"
        ) from exc
    if (
        receipt.node_count != EXPECTED_KUMMER_BUNDLE_NODE_COUNT
        or receipt.kernel_calls != EXPECTED_KUMMER_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_KUMMER_BUNDLE_EDGE_COUNT
        or receipt.total_body_nodes != EXPECTED_KUMMER_BUNDLE_BODY_PROOF_NODES
        or receipt.target != exact_target
    ):
        raise KummerClosureError("Kummer proof bundle returned inconsistent exact evidence")
    return KummerCheckedBundle(bundle, target, receipt, selected.surface_sha256)


def assemble_kummer_proof_bundle(
    batches: Sequence[KummerBodyMicrobatch],
    *,
    plan: KummerClosurePlan | None = None,
) -> KummerCheckedBundle:
    """Combine 175 actual parent proofs and 105 exact reconstructed bodies."""

    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise KummerClosureError("Kummer proof batches must be an ordered tuple or list")
    actual: dict[str, KummerCheckedBody] = {}
    completed: list[str] = []
    for batch in batches:
        verify_kummer_body_microbatch(batch, completed_names=completed, plan=selected)
        for body in batch.rows:
            if body.name in actual:
                raise KummerClosureError(f"Kummer closure repeats actual body {body.name!r}")
            actual[body.name] = body
            completed.append(body.name)
    required = {row.name for row in selected.construction_rows}
    if set(actual) != required:
        raise KummerClosureError(
            f"Kummer closure requires exactly {len(required)} actual reconstructed bodies; "
            f"received {len(actual)}"
        )
    parents = _checked_parent_bodies()
    positions = {row.name: row.node_id for row in selected.rows}
    nodes = tuple(
        BundleNode(
            row.node_id,
            _frozen_formula(row.name),
            tuple(positions[dependency] for dependency in row.dependencies),
            actual[row.name].certificate if row.name in actual else parents[row.name],
        )
        for row in selected.rows
    )
    roots = tuple(positions[name] for name in selected.roots)
    target = And(nodes[roots[0]].target, nodes[roots[1]].target)
    conjunction = BundleNode(
        EXPECTED_KUMMER_THEOREM_COUNT,
        target,
        roots,
        _synthetic_conjunction_body(),
    )
    return check_kummer_proof_bundle(
        ProofBundle(nodes + (conjunction,), conjunction.node_id),
        target,
        plan=selected,
    )


def export_kummer_proof_bundle(
    destination: str | Path,
    *,
    batch_size: int = MAX_FRONTIER_CLOSURE_MICROBATCH,
    progress: Callable[[int, int, tuple[str, ...]], None] | None = None,
) -> tuple[Path, KummerCheckedBundle]:
    """Construct all actual bodies, independently check, and export new bytes."""

    if not isinstance(destination, (str, Path)):
        raise KummerClosureError("Kummer proof destination must be a filesystem path")
    if (
        type(batch_size) is not int
        or batch_size <= 0
        or batch_size > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise KummerClosureError("Kummer proof batch size must be between 1 and 16")
    if progress is not None and not callable(progress):
        raise KummerClosureError("Kummer proof progress callback must be callable")
    path = Path(destination)
    if path.exists():
        raise KummerClosureError(f"Kummer proof artifact destination already exists: {path!s}")
    selected = kummer_complete_closure_plan()
    ordered = tuple(row.name for row in selected.construction_rows)
    completed: list[str] = []
    batches: list[KummerBodyMicrobatch] = []
    for offset in range(0, len(ordered), batch_size):
        names = ordered[offset : offset + batch_size]
        batch = construct_kummer_body_microbatch(
            names,
            completed_names=completed,
            plan=selected,
        )
        verify_kummer_body_microbatch(batch, completed_names=completed, plan=selected)
        batches.append(batch)
        completed.extend(batch.names)
        if progress is not None:
            progress(len(completed), len(ordered), batch.names)
    actual = assemble_kummer_proof_bundle(tuple(batches), plan=selected)
    try:
        payload = encode_proof_bundle(actual.bundle, actual.target)
        restored, restored_target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise KummerClosureError("cannot canonically encode the complete Kummer proof bundle") from exc
    actual_bytes = payload.encode("utf-8")
    if (
        len(actual_bytes) != EXPECTED_KUMMER_BUNDLE_BYTES
        or sha256(actual_bytes).hexdigest() != EXPECTED_KUMMER_BUNDLE_SHA256
    ):
        raise KummerClosureError("complete Kummer proof bundle changed its frozen canonical bytes")
    check_kummer_proof_bundle(restored, restored_target, plan=selected)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise KummerClosureError(f"cannot create a fresh Kummer proof artifact {path!s}") from exc
    return path, actual


def load_kummer_proof_bundle(source: str | Path) -> KummerCheckedBundle:
    """Decode complete actual proof data and recheck every unchanged body."""

    if not isinstance(source, (str, Path)):
        raise KummerClosureError("Kummer proof artifact must be a filesystem path")
    path = Path(source)
    try:
        data = path.read_bytes()
        if (
            len(data) != EXPECTED_KUMMER_BUNDLE_BYTES
            or sha256(data).hexdigest() != EXPECTED_KUMMER_BUNDLE_SHA256
        ):
            raise KummerClosureError("Kummer proof artifact changed its frozen actual-proof provenance")
        payload = data.decode("utf-8")
        bundle, target = decode_proof_bundle(payload)
    except KummerClosureError:
        raise
    except (OSError, UnicodeError, ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise KummerClosureError(f"cannot decode actual Kummer proof artifact {path!s}") from exc
    return check_kummer_proof_bundle(bundle, target)


def replay_kummer_closed_theorem(name: str, bundle: KummerCheckedBundle) -> CheckedTheorem:
    """If ordinary replay fits unchanged limits, check the exact root directly."""

    if type(name) is not str or name not in KUMMER_ROOT_NAMES:
        raise KummerClosureError("Kummer replay accepts only the two exact original endpoints")
    if type(bundle) is not KummerCheckedBundle:
        raise KummerClosureError("Kummer replay requires actual independently checked proof data")
    checked_bundle = check_kummer_proof_bundle(bundle.bundle, bundle.target)
    plan = kummer_complete_closure_plan()
    row = next(item for item in plan.rows if item.name == name)
    needed: set[int] = set()
    pending = [row.node_id]
    while pending:
        node_id = pending.pop()
        if node_id not in needed:
            needed.add(node_id)
            pending.extend(checked_bundle.bundle.nodes[node_id].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
            for node in checked_bundle.bundle.nodes[:-1]
            if node.node_id in needed
        ),
        row.node_id,
    )
    formula = _frozen_formula(name)
    try:
        candidate = compile_layered_replay(
            layered,
            formula,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
    except (LayeredReplayError, RecursionError, TypeError, ValueError) as exc:
        raise KummerClosureError(
            f"cannot compile ordinary exact Kummer proof {name!r} under unchanged limits"
        ) from exc
    if candidate is None:
        raise KummerClosureError(
            f"exact Kummer theorem {name!r} exceeds the unchanged layered resource policy"
        )
    if (
        candidate.proof_nodes > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        or candidate.proof_objects > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    ):
        raise KummerClosureError(
            f"exact Kummer theorem {name!r} exceeds the unchanged 125000/25000 limits"
        )
    expected_nodes = EXPECTED_KUMMER_ROOT_PROOF_NODES[KUMMER_ROOT_NAMES.index(name)]
    if candidate.proof_nodes != expected_nodes:
        raise KummerClosureError(f"exact Kummer theorem {name!r} changed its frozen proof size")
    if not check((), candidate.certificate, formula):
        raise KummerClosureError(f"original intuitionistic kernel rejected exact Kummer root {name!r}")
    return CheckedTheorem(
        v17.ALPHA_EDITION.by_name[name].spec,
        formula,
        candidate.certificate,
        candidate.proof_nodes,
    )


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Construct complete original-kernel proof data for both exact Kummer roots."
    )
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=MAX_FRONTIER_CLOSURE_MICROBATCH)
    options = parser.parse_args(argv)

    def progress(done: int, total: int, names: tuple[str, ...]) -> None:
        print(
            json.dumps(
                {"constructed": done, "total": total, "first": names[0], "last": names[-1]},
                sort_keys=True,
            ),
            flush=True,
        )

    path, actual = export_kummer_proof_bundle(
        options.export,
        batch_size=options.batch_size,
        progress=progress,
    )
    data = path.read_bytes()
    print(
        json.dumps(
            {
                "path": str(path),
                "bytes": len(data),
                "sha256": sha256(data).hexdigest(),
                "theorem_count": EXPECTED_KUMMER_THEOREM_COUNT,
                "pending_count": EXPECTED_KUMMER_PENDING_COUNT,
                "constructed_count": EXPECTED_KUMMER_CONSTRUCTED_BODY_COUNT,
                "bundle_nodes": actual.receipt.node_count,
                "bundle_edges": actual.receipt.dependency_edges,
                "body_proof_nodes": actual.receipt.total_body_nodes,
                "kernel_calls": actual.receipt.kernel_calls,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "EXPECTED_KUMMER_ALPHA_CLOSED_COUNT",
    "EXPECTED_KUMMER_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_KUMMER_BUNDLE_BYTES",
    "EXPECTED_KUMMER_BUNDLE_EDGE_COUNT",
    "EXPECTED_KUMMER_BUNDLE_NODE_COUNT",
    "EXPECTED_KUMMER_BUNDLE_SHA256",
    "EXPECTED_KUMMER_CONSTRUCTED_BODY_COUNT",
    "EXPECTED_KUMMER_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_KUMMER_ORDERED_NAMES_SHA256",
    "EXPECTED_KUMMER_PENDING_COUNT",
    "EXPECTED_KUMMER_PENDING_NAMES_SHA256",
    "EXPECTED_KUMMER_RECONSTRUCTED_PARENT_COUNT",
    "EXPECTED_KUMMER_REUSED_PARENT_COUNT",
    "EXPECTED_KUMMER_ROOT_NODE_IDS",
    "EXPECTED_KUMMER_ROOT_PROOF_NODES",
    "EXPECTED_KUMMER_ROOT_STATEMENT_SHA256",
    "EXPECTED_KUMMER_STABLE_COUNT",
    "EXPECTED_KUMMER_SURFACE_SHA256",
    "EXPECTED_KUMMER_THEOREM_COUNT",
    "KUMMER_RECONSTRUCTED_CHECKED_NAMES",
    "KUMMER_ROOT_NAMES",
    "KummerBodyMicrobatch",
    "KummerCheckedBody",
    "KummerCheckedBundle",
    "KummerClosureError",
    "KummerClosurePlan",
    "assemble_kummer_proof_bundle",
    "check_kummer_proof_bundle",
    "construct_kummer_body_microbatch",
    "export_kummer_proof_bundle",
    "kummer_complete_closure_plan",
    "kummer_pending_layers",
    "load_kummer_proof_bundle",
    "replay_kummer_closed_theorem",
    "verify_kummer_body_microbatch",
]
