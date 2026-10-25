"""Bounded genuine constructive proof of the complete Lagrange theorem.

The exact immutable Alpha-v17 ancestor graph of ``four_square_lagrange`` has
390 theorem bodies. Of these, 174 already occur in the independently checked
quadratic-reciprocity proof bundle; 15 other previously checked prerequisites
and 201 genuinely body-only prerequisites are reconstructed from their exact
original scripts. Every body is checked independently by the unchanged
intuitionistic kernel inside bounded proof microbatches.

The resulting self-contained proof bundle has the original unconditional
Lagrange theorem as its exact root. This research artifact never mutates
Stable, Alpha, checked-use authority, or release membership.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import platform
import resource
from typing import Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import Formula, Imp
from ..kernel.proofs import Proof
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
from .theorems import CheckedTheorem, _closed_formula, _primitive


FOUR_SQUARE_ROOT_NAME = "four_square_lagrange"
EXPECTED_FOUR_SQUARE_THEOREM_COUNT = 390
EXPECTED_FOUR_SQUARE_DEPENDENCY_EDGE_COUNT = 1_187
EXPECTED_FOUR_SQUARE_BODY_ONLY_COUNT = 201
EXPECTED_FOUR_SQUARE_HA_BODY_COUNT = 196
EXPECTED_FOUR_SQUARE_CHECKED_PARENT_COUNT = 189
EXPECTED_FOUR_SQUARE_QR_REUSED_BODY_COUNT = 174
EXPECTED_FOUR_SQUARE_RECONSTRUCTED_CHECKED_PARENT_COUNT = 15
EXPECTED_FOUR_SQUARE_RECONSTRUCTED_BODY_COUNT = 216
EXPECTED_FOUR_SQUARE_ORDERED_NAMES_SHA256 = (
    "9a94742066b28f553ad78fd675c41354a461cbe5f69f8e5df3ec36f9b055a843"
)
EXPECTED_FOUR_SQUARE_BODY_ONLY_NAMES_SHA256 = (
    "f1b2a83e8f7ec612a9a1dd564902fc543dc5833907b3c8a355f2c22a96a85c71"
)
EXPECTED_FOUR_SQUARE_SURFACE_SHA256 = (
    "1ed816a1f32ec90601d58d46eb4e7bec27775a0b9c1d7b5fba84ac377231de9f"
)
EXPECTED_FOUR_SQUARE_ROOT_STATEMENT_SHA256 = (
    "fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5"
)
EXPECTED_FOUR_SQUARE_BUNDLE_SHA256 = (
    "dd8374b95184f95f28a296aba6682f8177538650c3cc2f8d94a8db723c9982f0"
)
EXPECTED_FOUR_SQUARE_BUNDLE_BYTES = 1_948_314
EXPECTED_FOUR_SQUARE_BUNDLE_BODY_PROOF_NODES = 31_942


class FourSquareCompleteClosureError(ValueError):
    """A frozen Lagrange dependency graph, actual proof, or bound is invalid."""


@dataclass(frozen=True, slots=True)
class FourSquareClosureRow:
    """One exact immutable Alpha-v17 theorem surface, without new authority."""

    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    evidence: str
    enrollment_origin: str
    qr_reusable: bool

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v17.EvidenceStatus.BODY_CHECKED.value


@dataclass(frozen=True, slots=True)
class FourSquareClosurePlan:
    """The complete exact frozen Lagrange dependency closure, never a proof."""

    root: str
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[FourSquareClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    body_only_names_sha256: str
    surface_sha256: str

    @property
    def pending_rows(self) -> tuple[FourSquareClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def qr_reused_rows(self) -> tuple[FourSquareClosureRow, ...]:
        return tuple(row for row in self.rows if row.qr_reusable)

    @property
    def reconstructed_rows(self) -> tuple[FourSquareClosureRow, ...]:
        return tuple(row for row in self.rows if not row.qr_reusable)


@dataclass(frozen=True, slots=True)
class FourSquareCheckedBody:
    """One actual independently checked dependency-curried proof body."""

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
class FourSquareBodyMicrobatch:
    """At most sixteen complete proof bodies under unchanged resource caps."""

    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[FourSquareCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class FourSquareCheckedBundle:
    """A complete actual original-kernel-checked Lagrange proof graph."""

    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


@lru_cache(maxsize=1)
def four_square_complete_closure_plan() -> FourSquareClosurePlan:
    """Freeze the exact v17 Lagrange ancestor slice without loading proofs."""

    table = v17.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = [FOUR_SQUARE_ROOT_NAME]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise FourSquareCompleteClosureError(
                f"missing immutable Alpha-v17 four-square dependency {name!r}"
            )
        if item.evidence is v17.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise FourSquareCompleteClosureError(
                f"four-square ancestor {name!r} has pending layered evidence"
            )
        selected.add(name)
        pending.extend(reversed(item.spec.dependencies))

    qr_names = {
        spec.name for spec in quadratic_reciprocity_stack().admission_order
    }
    rows: list[FourSquareClosureRow] = []
    surfaces: list[dict[str, object]] = []
    observed: set[str] = set()
    edges = 0
    for alpha_index, item in enumerate(v17.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        missing = set(item.spec.dependencies).difference(observed)
        if missing:
            raise FourSquareCompleteClosureError(
                f"non-topological four-square dependency {item.spec.name!r}: "
                f"{sorted(missing)!r}"
            )
        digest = sha256(item.spec.statement.encode("utf-8")).hexdigest()
        reusable = item.checked_use and item.spec.name in qr_names
        row = FourSquareClosureRow(
            node_id=len(rows),
            alpha_index=alpha_index,
            name=item.spec.name,
            statement_sha256=digest,
            dependencies=item.spec.dependencies,
            evidence=item.evidence.value,
            enrollment_origin=item.enrollment_origin.value,
            qr_reusable=reusable,
        )
        rows.append(row)
        surfaces.append(
            {
                "alpha_index": alpha_index,
                "name": row.name,
                "statement_sha256": row.statement_sha256,
                "dependencies": row.dependencies,
                "evidence": row.evidence,
                "enrollment_origin": row.enrollment_origin,
            }
        )
        edges += len(row.dependencies)
        observed.add(row.name)
    unclosed = tuple(row for row in rows if row.needs_closure)
    reused = tuple(row for row in rows if row.qr_reusable)
    reconstructed = tuple(row for row in rows if not row.qr_reusable)
    ordered_names = sha256(
        "\n".join(row.name for row in rows).encode("utf-8")
    ).hexdigest()
    body_only_names = sha256(
        "\n".join(row.name for row in unclosed).encode("utf-8")
    ).hexdigest()
    surface = sha256(
        json.dumps(
            surfaces,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    if (
        len(rows) != EXPECTED_FOUR_SQUARE_THEOREM_COUNT
        or len(unclosed) != EXPECTED_FOUR_SQUARE_BODY_ONLY_COUNT
        or len(reused) != EXPECTED_FOUR_SQUARE_QR_REUSED_BODY_COUNT
        or len(reconstructed) != EXPECTED_FOUR_SQUARE_RECONSTRUCTED_BODY_COUNT
        or edges != EXPECTED_FOUR_SQUARE_DEPENDENCY_EDGE_COUNT
        or ordered_names != EXPECTED_FOUR_SQUARE_ORDERED_NAMES_SHA256
        or body_only_names != EXPECTED_FOUR_SQUARE_BODY_ONLY_NAMES_SHA256
        or surface != EXPECTED_FOUR_SQUARE_SURFACE_SHA256
    ):
        raise FourSquareCompleteClosureError(
            "the exact immutable Alpha-v17 Lagrange dependency graph changed"
        )
    if Counter(row.evidence for row in rows) != {
        "stable_closed": 166,
        "alpha_closed": 23,
        "body_checked": 201,
    }:
        raise FourSquareCompleteClosureError("the frozen Lagrange evidence partition changed")
    if sum(row.enrollment_origin == "ha" for row in unclosed) != (
        EXPECTED_FOUR_SQUARE_HA_BODY_COUNT
    ):
        raise FourSquareCompleteClosureError("the exact four-square 196-row campaign changed")
    if (
        not rows
        or rows[-1].name != FOUR_SQUARE_ROOT_NAME
        or rows[-1].statement_sha256 != EXPECTED_FOUR_SQUARE_ROOT_STATEMENT_SHA256
    ):
        raise FourSquareCompleteClosureError("the exact unconditional Lagrange root changed")
    return FourSquareClosurePlan(
        root=FOUR_SQUARE_ROOT_NAME,
        parent_alpha_identity_sha256=v17.ALPHA_V17_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=v17.ALPHA_V17_ENROLLMENT_SHA256,
        rows=tuple(rows),
        dependency_edge_count=edges,
        ordered_names_sha256=ordered_names,
        body_only_names_sha256=body_only_names,
        surface_sha256=surface,
    )


def _sealed_plan(plan: FourSquareClosurePlan | None) -> FourSquareClosurePlan:
    expected = four_square_complete_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not FourSquareClosurePlan or plan != expected:
        raise FourSquareCompleteClosureError(
            "four-square plan differs from the exact frozen Alpha-v17 source"
        )
    return plan


def four_square_pending_layers(
    *,
    plan: FourSquareClosurePlan | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return dependency-ready body-only waves without inferring any proof."""

    selected = _sealed_plan(plan)
    ready = {row.name for row in selected.rows if not row.needs_closure}
    remaining = list(selected.pending_rows)
    layers: list[tuple[str, ...]] = []
    while remaining:
        current = tuple(
            row.name for row in remaining if set(row.dependencies).issubset(ready)
        )
        if not current:
            raise FourSquareCompleteClosureError("four-square dependency graph is cyclic")
        layers.append(current)
        ready.update(current)
        remaining = [row for row in remaining if row.name not in ready]
    return tuple(layers)


def _completed_names(
    names: Sequence[str] | frozenset[str],
    plan: FourSquareClosurePlan,
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise FourSquareCompleteClosureError(
            "completed four-square scheduling names must be a tuple, list, or frozenset"
        )
    if any(type(name) is not str for name in names):
        raise FourSquareCompleteClosureError("four-square scheduling names must be exact strings")
    result = set(names)
    if len(result) != len(names):
        raise FourSquareCompleteClosureError("four-square scheduling repeats a theorem")
    known = {row.name for row in plan.reconstructed_rows}
    unexpected = result.difference(known)
    if unexpected:
        raise FourSquareCompleteClosureError(
            f"unknown completed four-square bodies: {sorted(unexpected)!r}"
        )
    for row in plan.reconstructed_rows:
        if row.name in result:
            missing = {
                dependency
                for dependency in row.dependencies
                if dependency in known and dependency not in result
            }
            if missing:
                raise FourSquareCompleteClosureError(
                    f"completed four-square rows are not dependency closed at "
                    f"{row.name!r}: {sorted(missing)!r}"
                )
    return result


def _body_target(row: FourSquareClosureRow) -> tuple[Formula, Formula]:
    item = v17.ALPHA_ENTRIES[row.alpha_index]
    if (
        item.spec.name != row.name
        or sha256(item.spec.statement.encode("utf-8")).hexdigest()
        != row.statement_sha256
    ):
        raise FourSquareCompleteClosureError(
            f"four-square body {row.name!r} changed its exact original source"
        )
    target = _closed_formula(item.spec.statement)
    curried = target
    for dependency in reversed(item.spec.dependencies):
        curried = Imp(
            _closed_formula(v17.ALPHA_EDITION.by_name[dependency].spec.statement),
            curried,
        )
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
        raise FourSquareCompleteClosureError(
            f"{label} violates the unchanged 125000-node/25000-object policy"
        ) from exc


def construct_four_square_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: FourSquareClosurePlan | None = None,
) -> FourSquareBodyMicrobatch:
    """Reconstruct at most sixteen independently checked actual proof bodies."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise FourSquareCompleteClosureError("four-square microbatch names must be a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FourSquareCompleteClosureError(
            f"four-square microbatch must contain 1..{MAX_FRONTIER_CLOSURE_MICROBATCH} proofs"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise FourSquareCompleteClosureError("four-square microbatch names must be unique strings")
    completed = _completed_names(completed_names, selected)
    table = {row.name: row for row in selected.reconstructed_rows}
    available = {row.name for row in selected.qr_reused_rows} | completed
    previous = -1
    for name in names:
        row = table.get(name)
        if row is None:
            raise FourSquareCompleteClosureError(
                f"unknown or QR-reused four-square body {name!r}"
            )
        if row.node_id <= previous or name in completed:
            raise FourSquareCompleteClosureError("four-square microbatch repeats or reorders a row")
        missing = set(row.dependencies).difference(available)
        if missing:
            raise FourSquareCompleteClosureError(
                f"four-square theorem {name!r} lacks predecessor bodies: {sorted(missing)!r}"
            )
        available.add(name)
        previous = row.node_id

    result: list[FourSquareCheckedBody] = []
    nodes = objects = annotations = 0
    for name in names:
        row = table[name]
        spec = v17.ALPHA_ENTRIES[row.alpha_index].spec
        target, curried = _body_target(row)
        try:
            state = start(curried)
            for dependency in spec.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for position, command in enumerate(spec.script):
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise FourSquareCompleteClosureError(
                        f"four-square theorem {name!r} invokes implicit authority "
                        f"at command {position}"
                    )
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
        except FourSquareCompleteClosureError:
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
            raise FourSquareCompleteClosureError(
                f"cannot independently check actual four-square body {name!r}"
            ) from exc
        metrics = _body_metrics(
            certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"four-square dependency-curried proof body {name}",
        )
        proof_nodes, proof_objects, depth, body_annotations, envelope_depth = metrics
        nodes += proof_nodes
        objects += proof_objects
        annotations += body_annotations
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise FourSquareCompleteClosureError("four-square microbatch exceeds its annotation limit")
        result.append(
            FourSquareCheckedBody(
                node_id=row.node_id,
                alpha_index=row.alpha_index,
                name=row.name,
                statement_sha256=row.statement_sha256,
                target=target,
                curried_target=curried,
                certificate=certificate,
                proof_nodes=proof_nodes,
                proof_objects=proof_objects,
                proof_depth=depth,
                annotation_occurrences=body_annotations,
                envelope_depth=envelope_depth,
            )
        )
    return FourSquareBodyMicrobatch(
        parent_alpha_identity_sha256=selected.parent_alpha_identity_sha256,
        surface_sha256=selected.surface_sha256,
        rows=tuple(result),
        proof_nodes=nodes,
        proof_objects=objects,
        annotation_occurrences=annotations,
    )


def verify_four_square_body_microbatch(
    batch: FourSquareBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: FourSquareClosurePlan | None = None,
) -> FourSquareBodyMicrobatch:
    """Independently check actual bodies, exact topology, and hard bounds."""

    selected = _sealed_plan(plan)
    if type(batch) is not FourSquareBodyMicrobatch:
        raise FourSquareCompleteClosureError("four-square microbatch has an invalid exact type")
    if (
        batch.parent_alpha_identity_sha256 != selected.parent_alpha_identity_sha256
        or batch.surface_sha256 != selected.surface_sha256
    ):
        raise FourSquareCompleteClosureError("four-square microbatch changed its frozen parent")
    if (
        type(batch.rows) is not tuple
        or not batch.rows
        or len(batch.rows) > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise FourSquareCompleteClosureError("four-square microbatch exceeds its sixteen-proof cap")
    completed = _completed_names(completed_names, selected)
    available = {row.name for row in selected.qr_reused_rows} | completed
    table = {row.name: row for row in selected.reconstructed_rows}
    previous = -1
    nodes = objects = annotations = 0
    for actual in batch.rows:
        if type(actual) is not FourSquareCheckedBody:
            raise FourSquareCompleteClosureError("four-square microbatch contains an invalid proof")
        frozen = table.get(actual.name)
        if (
            frozen is None
            or actual.node_id != frozen.node_id
            or actual.alpha_index != frozen.alpha_index
            or actual.statement_sha256 != frozen.statement_sha256
        ):
            raise FourSquareCompleteClosureError(
                f"four-square proof {actual.name!r} changed its exact theorem surface"
            )
        if actual.node_id <= previous or actual.name in available:
            raise FourSquareCompleteClosureError("four-square microbatch repeats or reorders a proof")
        missing = set(frozen.dependencies).difference(available)
        if missing:
            raise FourSquareCompleteClosureError(
                f"four-square proof {actual.name!r} lacks predecessors: {sorted(missing)!r}"
            )
        target, curried = _body_target(frozen)
        if actual.target != target or actual.curried_target != curried:
            raise FourSquareCompleteClosureError(
                f"four-square proof {actual.name!r} changed its exact curried target"
            )
        metrics = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"four-square dependency-curried proof body {actual.name}",
        )
        if metrics != (
            actual.proof_nodes,
            actual.proof_objects,
            actual.proof_depth,
            actual.annotation_occurrences,
            actual.envelope_depth,
        ):
            raise FourSquareCompleteClosureError(
                f"four-square proof {actual.name!r} changed its exact resource envelope"
            )
        if not check((), actual.certificate, curried):
            raise FourSquareCompleteClosureError(
                f"the unchanged intuitionistic kernel rejected four-square proof {actual.name!r}"
            )
        nodes += actual.proof_nodes
        objects += actual.proof_objects
        annotations += actual.annotation_occurrences
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise FourSquareCompleteClosureError("four-square microbatch exceeds its annotation limit")
        available.add(actual.name)
        previous = actual.node_id
    if (batch.proof_nodes, batch.proof_objects, batch.annotation_occurrences) != (
        nodes,
        objects,
        annotations,
    ):
        raise FourSquareCompleteClosureError("four-square microbatch changed its aggregate metrics")
    return batch


def check_four_square_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: FourSquareClosurePlan | None = None,
) -> FourSquareCheckedBundle:
    """Independently check all 390 actual proof bodies and exact root target."""

    selected = _sealed_plan(plan)
    if type(bundle) is not ProofBundle:
        raise FourSquareCompleteClosureError("four-square evidence must be a real proof bundle")
    if (
        type(bundle.nodes) is not tuple
        or len(bundle.nodes) != EXPECTED_FOUR_SQUARE_THEOREM_COUNT
        or bundle.root != EXPECTED_FOUR_SQUARE_THEOREM_COUNT - 1
    ):
        raise FourSquareCompleteClosureError("four-square proof graph changed its exact size or root")
    positions = {row.name: row.node_id for row in selected.rows}
    for row, node in zip(selected.rows, bundle.nodes, strict=True):
        expected, _curried = _body_target(row)
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != expected
            or node.dependencies
            != tuple(positions[name] for name in row.dependencies)
        ):
            raise FourSquareCompleteClosureError(
                f"four-square bundle changed exact frozen theorem {row.name!r}"
            )
    expected_target = _closed_formula(
        v17.ALPHA_EDITION.by_name[FOUR_SQUARE_ROOT_NAME].spec.statement
    )
    if target != expected_target:
        raise FourSquareCompleteClosureError("four-square bundle changed its exact unconditional root")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise FourSquareCompleteClosureError(
            "the unchanged intuitionistic kernel rejected the complete four-square graph"
        ) from exc
    if (
        receipt.node_count != EXPECTED_FOUR_SQUARE_THEOREM_COUNT
        or receipt.kernel_calls != EXPECTED_FOUR_SQUARE_THEOREM_COUNT
        or receipt.dependency_edges != EXPECTED_FOUR_SQUARE_DEPENDENCY_EDGE_COUNT
        or receipt.target != expected_target
    ):
        raise FourSquareCompleteClosureError("four-square proof graph returned inconsistent metrics")
    return FourSquareCheckedBundle(bundle, target, receipt, selected.surface_sha256)


def assemble_four_square_proof_bundle(
    batches: Sequence[FourSquareBodyMicrobatch],
    *,
    plan: FourSquareClosurePlan | None = None,
) -> FourSquareCheckedBundle:
    """Assemble the exact full Lagrange proof from only actual checked bodies."""

    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise FourSquareCompleteClosureError("four-square proof batches must be a tuple or list")
    actual: dict[str, FourSquareCheckedBody] = {}
    completed: list[str] = []
    for batch in batches:
        verify_four_square_body_microbatch(
            batch,
            completed_names=completed,
            plan=selected,
        )
        for row in batch.rows:
            if row.name in actual:
                raise FourSquareCompleteClosureError(
                    f"four-square closure repeats proof body {row.name!r}"
                )
            actual[row.name] = row
            completed.append(row.name)
    required = {row.name for row in selected.reconstructed_rows}
    if set(actual) != required:
        raise FourSquareCompleteClosureError(
            f"four-square closure requires exactly {len(required)} actual reconstructed "
            f"proof bodies; received {len(actual)}"
        )
    try:
        qr_bundle, _receipt = v16._checked_qr_bundle()
    except (v16.EditionV16Error, ProofBundleError, TypeError, ValueError) as exc:
        raise FourSquareCompleteClosureError(
            "the genuine original-kernel-checked QR prerequisite bundle is unavailable"
        ) from exc
    qr_nodes = {
        spec.name: node
        for spec, node in zip(
            quadratic_reciprocity_stack().admission_order,
            qr_bundle.nodes,
            strict=True,
        )
    }
    positions = {row.name: row.node_id for row in selected.rows}
    nodes = tuple(
        BundleNode(
            row.node_id,
            _body_target(row)[0],
            tuple(positions[name] for name in row.dependencies),
            qr_nodes[row.name].body
            if row.qr_reusable
            else actual[row.name].certificate,
        )
        for row in selected.rows
    )
    target = _closed_formula(v17.ALPHA_EDITION.by_name[selected.root].spec.statement)
    return check_four_square_proof_bundle(
        ProofBundle(nodes, len(nodes) - 1),
        target,
        plan=selected,
    )


_four_square_bundle_source: Path | None = None


def _default_four_square_bundle_source() -> Path:
    location = Path(__file__).resolve()
    if len(location.parents) > 4:
        return (
            location.parents[4]
            / "research"
            / "arithmetic-library"
            / "artifacts"
            / "four-square-proof-bundle-v1.json"
        )
    return Path("/lab/proof-artifacts/four-square-proof-bundle-v1.json")


def set_four_square_bundle_source(source: str | Path | None) -> None:
    """Change explicit actual-proof source and invalidate all proof caches."""

    global _four_square_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise FourSquareCompleteClosureError("four-square proof source must be a filesystem path")
    _four_square_bundle_source = None if source is None else Path(source)
    _checked_four_square_bundle.cache_clear()
    replay_four_square_closed_root.cache_clear()


@lru_cache(maxsize=1)
def _checked_four_square_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _four_square_bundle_source or _default_four_square_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FourSquareCompleteClosureError(
            f"actual four-square proof data are unavailable: {source!s}"
        ) from exc
    data = payload.encode("utf-8")
    if (
        len(data) != EXPECTED_FOUR_SQUARE_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_FOUR_SQUARE_BUNDLE_SHA256
    ):
        raise FourSquareCompleteClosureError(
            "four-square proof artifact differs from its frozen actual-proof provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise FourSquareCompleteClosureError(
            "four-square artifact is not a canonical complete constructive proof bundle"
        ) from exc
    actual = check_four_square_proof_bundle(bundle, target)
    if actual.receipt.total_body_nodes != EXPECTED_FOUR_SQUARE_BUNDLE_BODY_PROOF_NODES:
        raise FourSquareCompleteClosureError("four-square proof bundle body metrics changed")
    return actual.bundle, actual.receipt


def checked_four_square_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Return only the independently checked complete actual root proof graph."""

    return _checked_four_square_bundle()


@lru_cache(maxsize=1)
def replay_four_square_closed_root() -> CheckedTheorem:
    """Compile and independently kernel-check the ordinary exact Lagrange root."""

    bundle, _receipt = _checked_four_square_bundle()
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(
                row.node_id,
                row.target,
                row.dependencies,
                row.body,
            )
            for row in bundle.nodes
        ),
        bundle.root,
    )
    item = v17.ALPHA_EDITION.by_name[FOUR_SQUARE_ROOT_NAME]
    formula = _closed_formula(item.spec.statement)
    try:
        candidate = compile_layered_replay(
            layered,
            formula,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
    except (LayeredReplayError, RecursionError, TypeError, ValueError) as exc:
        raise FourSquareCompleteClosureError(
            "cannot compile the actual ordinary constructive four-square root proof"
        ) from exc
    if candidate is None:
        raise FourSquareCompleteClosureError(
            "the ordinary four-square root exceeds the unchanged layered resource policy"
        )
    if not check((), candidate.certificate, formula):
        raise FourSquareCompleteClosureError(
            "the unchanged intuitionistic kernel rejected the full four-square theorem"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


def _peak_rss_bytes() -> int:
    observed = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return observed if platform.system() == "Darwin" else observed * 1024


def export_four_square_proof_bundle(
    destination: str | Path,
    *,
    batch_size: int = MAX_FRONTIER_CLOSURE_MICROBATCH,
    max_rss_mib: int = 1_536,
    progress: bool = False,
) -> tuple[Path, FourSquareCheckedBundle]:
    """Build all actual bounded bodies and export one fresh complete proof."""

    if not isinstance(destination, (str, Path)):
        raise FourSquareCompleteClosureError("four-square export destination must be a path")
    if (
        type(batch_size) is not int
        or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise FourSquareCompleteClosureError("four-square batch size must be between 1 and 16")
    if type(max_rss_mib) is not int or max_rss_mib < 128:
        raise FourSquareCompleteClosureError("four-square RSS guard must be at least 128 MiB")
    if type(progress) is not bool:
        raise FourSquareCompleteClosureError("four-square progress flag must be a boolean")
    path = Path(destination)
    if path.exists():
        raise FourSquareCompleteClosureError(
            f"four-square proof artifact destination already exists: {path!s}"
        )
    plan = four_square_complete_closure_plan()
    ordered = tuple(row.name for row in plan.reconstructed_rows)
    completed: list[str] = []
    batches: list[FourSquareBodyMicrobatch] = []
    for offset in range(0, len(ordered), batch_size):
        names = ordered[offset : offset + batch_size]
        batch = construct_four_square_body_microbatch(
            names,
            completed_names=completed,
            plan=plan,
        )
        verify_four_square_body_microbatch(
            batch,
            completed_names=completed,
            plan=plan,
        )
        batches.append(batch)
        completed.extend(batch.names)
        peak = _peak_rss_bytes()
        if peak > max_rss_mib * 1024 * 1024:
            raise FourSquareCompleteClosureError(
                f"four-square microbatch exceeded its {max_rss_mib}-MiB RSS guard"
            )
        if progress:
            print(
                json.dumps(
                    {
                        "event": "four_square_body_batch_checked",
                        "completed": len(completed),
                        "total": len(ordered),
                        "rows": len(batch.rows),
                        "proof_nodes": batch.proof_nodes,
                        "proof_objects": batch.proof_objects,
                        "peak_rss_mib": round(peak / 1024 / 1024, 1),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    actual = assemble_four_square_proof_bundle(tuple(batches), plan=plan)
    payload = encode_proof_bundle(actual.bundle, actual.target)
    canonical, target = decode_proof_bundle(payload)
    check_four_square_proof_bundle(canonical, target, plan=plan)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise FourSquareCompleteClosureError(
            f"cannot create fresh four-square proof artifact {path!s}"
        ) from exc
    return path, actual


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Independently construct the complete Lagrange four-square proof."
    )
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=MAX_FRONTIER_CLOSURE_MICROBATCH)
    parser.add_argument("--max-rss-mib", type=int, default=1_536)
    parser.add_argument("--progress", action="store_true")
    options = parser.parse_args(argv)
    path, actual = export_four_square_proof_bundle(
        options.export,
        batch_size=options.batch_size,
        max_rss_mib=options.max_rss_mib,
        progress=options.progress,
    )
    data = path.read_bytes()
    print(
        json.dumps(
            {
                "event": "four_square_complete_root_bundle_checked",
                "path": str(path),
                "bytes": len(data),
                "sha256": sha256(data).hexdigest(),
                "root": FOUR_SQUARE_ROOT_NAME,
                "bundle_nodes": actual.receipt.node_count,
                "bundle_edges": actual.receipt.dependency_edges,
                "body_proof_nodes": actual.receipt.total_body_nodes,
                "kernel_calls": actual.receipt.kernel_calls,
                "peak_rss_mib": round(_peak_rss_bytes() / 1024 / 1024, 1),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "EXPECTED_FOUR_SQUARE_BODY_ONLY_COUNT",
    "EXPECTED_FOUR_SQUARE_BODY_ONLY_NAMES_SHA256",
    "EXPECTED_FOUR_SQUARE_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_FOUR_SQUARE_BUNDLE_BYTES",
    "EXPECTED_FOUR_SQUARE_BUNDLE_SHA256",
    "EXPECTED_FOUR_SQUARE_CHECKED_PARENT_COUNT",
    "EXPECTED_FOUR_SQUARE_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_FOUR_SQUARE_HA_BODY_COUNT",
    "EXPECTED_FOUR_SQUARE_ORDERED_NAMES_SHA256",
    "EXPECTED_FOUR_SQUARE_QR_REUSED_BODY_COUNT",
    "EXPECTED_FOUR_SQUARE_RECONSTRUCTED_BODY_COUNT",
    "EXPECTED_FOUR_SQUARE_RECONSTRUCTED_CHECKED_PARENT_COUNT",
    "EXPECTED_FOUR_SQUARE_ROOT_STATEMENT_SHA256",
    "EXPECTED_FOUR_SQUARE_SURFACE_SHA256",
    "EXPECTED_FOUR_SQUARE_THEOREM_COUNT",
    "FOUR_SQUARE_ROOT_NAME",
    "FourSquareBodyMicrobatch",
    "FourSquareCheckedBody",
    "FourSquareCheckedBundle",
    "FourSquareClosurePlan",
    "FourSquareClosureRow",
    "FourSquareCompleteClosureError",
    "assemble_four_square_proof_bundle",
    "check_four_square_proof_bundle",
    "checked_four_square_proof_bundle",
    "construct_four_square_body_microbatch",
    "export_four_square_proof_bundle",
    "four_square_complete_closure_plan",
    "four_square_pending_layers",
    "replay_four_square_closed_root",
    "set_four_square_bundle_source",
    "verify_four_square_body_microbatch",
]
