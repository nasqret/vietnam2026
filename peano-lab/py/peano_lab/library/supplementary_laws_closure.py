"""Actual, bounded constructive closure of both quadratic supplementary laws.

The frozen Alpha-v16 dependency closure contains 437 theorem rows: 406 already
proved rows from the independently checked quadratic-reciprocity proof bundle,
three older Eisenstein-prefix bodies, and 28 supplementary-law bodies.  This
module constructs the missing bodies in resource-bounded microbatches and
combines all 437 *actual proofs* into one self-contained proof bundle.  A
synthetic constructive conjunction node makes both supplementary roots
reachable without changing either exact theorem statement.

Planning, constructing bodies, and checking a bundle never change Alpha, Stable,
or checked-use authority.  Every returned closed theorem is assembled as an
ordinary layered ``Cut`` certificate and checked by the unchanged
intuitionistic kernel from the empty context.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v16 as v16
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
    decode_formula,
    decode_proof,
    decode_proof_bundle,
    encode_formula,
    encode_proof,
    encode_proof_bundle,
)
from .quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from .theorems import CheckedTheorem, _closed_formula, _primitive


SUPPLEMENTARY_ROOT_NAMES = (
    "quadratic_supplement_minus_one_complete",
    "quadratic_supplement_two_complete",
)
SUPPLEMENTARY_EXISTING_BERTRAND_NAMES = (
    "eisenstein_initial_segment_indicator_choice",
    "eisenstein_initial_segment_prefix_extend",
    "eisenstein_initial_segment_prefix_exists",
)
EXPECTED_SUPPLEMENTARY_THEOREM_COUNT = 437
EXPECTED_SUPPLEMENTARY_CHECKED_PARENT_COUNT = 406
EXPECTED_SUPPLEMENTARY_PROMOTION_COUNT = 31
EXPECTED_SUPPLEMENTARY_NEW_BODY_COUNT = 28
EXPECTED_SUPPLEMENTARY_DEPENDENCY_EDGE_COUNT = 1_427
EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT = 438
EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT = 1_429
EXPECTED_SUPPLEMENTARY_ORDERED_NAMES_SHA256 = (
    "9591f44b6cb8d2edbe1e4242193d28da948ebb61ba8f466377f7ceeae96c5b82"
)
EXPECTED_SUPPLEMENTARY_PROMOTION_NAMES_SHA256 = (
    "21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7"
)
EXPECTED_SUPPLEMENTARY_SURFACE_SHA256 = (
    "669f6cbce067830bb0f87a413247866b25c508f11d9ca9df069530bfe9e3d24a"
)
EXPECTED_SUPPLEMENTARY_ROOT_NODE_IDS = (415, 436)
EXPECTED_SUPPLEMENTARY_ROOT_STATEMENT_SHA256 = (
    "7ea81062b843e7fff4939ffce5b6fa14a87312619f7f49e3abd5993bfa02134e",
    "146a886f8f3a54d358321b54faf68a591362016e86139bd487a5496c7af74034",
)
EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256 = (
    "79fc4717dbe570bf836cca5ec699492ff3995700ec25336a20d03cc57261054c"
)
EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES = 1_732_249
EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES = 33_173
SUPPLEMENTARY_BODY_CHECKPOINT_FORMAT = "peano-lab-supplementary-body-batch-v1"
MAX_SUPPLEMENTARY_BODY_CHECKPOINT_BYTES = 16 * 1024 * 1024
PYODIDE_SUPPLEMENTARY_BUNDLE_PATH = (
    "/lab/proof-artifacts/supplementary-laws-proof-bundle-v1.json"
)


class SupplementaryClosureError(ValueError):
    """A frozen supplementary surface, actual body, or proof artifact failed."""


@dataclass(frozen=True, slots=True)
class SupplementaryClosureRow:
    """One immutable Alpha-v16 theorem surface, with unchanged evidence."""

    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    evidence: str
    enrollment_origin: str

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v16.EvidenceStatus.BODY_CHECKED.value


@dataclass(frozen=True, slots=True)
class SupplementaryClosurePlan:
    """The exact dependency-closed immutable parent surface, never authority."""

    roots: tuple[str, str]
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[SupplementaryClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    promotion_names_sha256: str
    surface_sha256: str

    @property
    def pending_rows(self) -> tuple[SupplementaryClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def checked_parent_rows(self) -> tuple[SupplementaryClosureRow, ...]:
        return tuple(row for row in self.rows if not row.needs_closure)


@dataclass(frozen=True, slots=True)
class SupplementaryCheckedBody:
    """Actual proof of ``dependency₁ → ⋯ → theorem``, not theorem authority."""

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
class SupplementaryBodyMicrobatch:
    """At most sixteen independently checked dependency-curried bodies."""

    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[SupplementaryCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class SupplementaryCheckedBundle:
    """One self-contained, independently kernel-checked constructive graph."""

    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


@lru_cache(maxsize=1)
def supplementary_laws_closure_plan() -> SupplementaryClosurePlan:
    """Seal both exact Alpha-v16 theorem slices without reading proof data."""

    table = v16.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = list(reversed(SUPPLEMENTARY_ROOT_NAMES))
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise SupplementaryClosureError(
                f"missing frozen Alpha-v16 supplementary dependency {name!r}"
            )
        if item.evidence is v16.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise SupplementaryClosureError(
                f"supplementary dependency {name!r} has pending layered evidence"
            )
        selected.add(name)
        pending.extend(reversed(item.spec.dependencies))

    rows: list[SupplementaryClosureRow] = []
    surfaces: list[dict[str, object]] = []
    seen: set[str] = set()
    edges = 0
    for alpha_index, item in enumerate(v16.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        missing = set(item.spec.dependencies).difference(seen)
        if missing:
            raise SupplementaryClosureError(
                f"non-topological supplementary row {item.spec.name!r}: "
                f"{sorted(missing)!r}"
            )
        digest = sha256(item.spec.statement.encode("utf-8")).hexdigest()
        row = SupplementaryClosureRow(
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
        edges += len(row.dependencies)
        seen.add(row.name)
    if len(seen) != len(selected):
        raise SupplementaryClosureError("supplementary dependency closure is incomplete")

    unclosed = tuple(row for row in rows if row.needs_closure)
    names_sha256 = sha256(
        "\n".join(row.name for row in rows).encode("utf-8")
    ).hexdigest()
    promotion_sha256 = sha256(
        "\n".join(row.name for row in unclosed).encode("utf-8")
    ).hexdigest()
    surface_sha256 = sha256(
        json.dumps(
            surfaces,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    if (
        len(rows) != EXPECTED_SUPPLEMENTARY_THEOREM_COUNT
        or len(unclosed) != EXPECTED_SUPPLEMENTARY_PROMOTION_COUNT
        or edges != EXPECTED_SUPPLEMENTARY_DEPENDENCY_EDGE_COUNT
        or names_sha256 != EXPECTED_SUPPLEMENTARY_ORDERED_NAMES_SHA256
        or promotion_sha256 != EXPECTED_SUPPLEMENTARY_PROMOTION_NAMES_SHA256
        or surface_sha256 != EXPECTED_SUPPLEMENTARY_SURFACE_SHA256
    ):
        raise SupplementaryClosureError(
            "the exact frozen Alpha-v16 supplementary surface or promotion slice changed"
        )
    if tuple(row.name for row in unclosed[:3]) != SUPPLEMENTARY_EXISTING_BERTRAND_NAMES:
        raise SupplementaryClosureError("the exact three older Eisenstein rows changed")
    if (
        sum(row.enrollment_origin == "bertrand" for row in unclosed) != 3
        or sum(row.enrollment_origin == "ha" for row in unclosed)
        != EXPECTED_SUPPLEMENTARY_NEW_BODY_COUNT
    ):
        raise SupplementaryClosureError("the frozen supplementary campaign ownership changed")

    positions = {row.name: row.node_id for row in rows}
    if tuple(positions[name] for name in SUPPLEMENTARY_ROOT_NAMES) != (
        EXPECTED_SUPPLEMENTARY_ROOT_NODE_IDS
    ):
        raise SupplementaryClosureError("the exact supplementary root node positions changed")
    if tuple(
        rows[positions[name]].statement_sha256 for name in SUPPLEMENTARY_ROOT_NAMES
    ) != EXPECTED_SUPPLEMENTARY_ROOT_STATEMENT_SHA256:
        raise SupplementaryClosureError("an exact supplementary-law statement changed")

    qr_names = {
        spec.name for spec in quadratic_reciprocity_stack().admission_order
    }
    if any(row.name not in qr_names for row in rows if not row.needs_closure):
        raise SupplementaryClosureError(
            "a checked supplementary prerequisite is outside the actual QR proof graph"
        )
    return SupplementaryClosurePlan(
        roots=SUPPLEMENTARY_ROOT_NAMES,
        parent_alpha_identity_sha256=v16.ALPHA_V16_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=v16.ALPHA_V16_ENROLLMENT_SHA256,
        rows=tuple(rows),
        dependency_edge_count=edges,
        ordered_names_sha256=names_sha256,
        promotion_names_sha256=promotion_sha256,
        surface_sha256=surface_sha256,
    )


def _sealed_plan(plan: SupplementaryClosurePlan | None) -> SupplementaryClosurePlan:
    expected = supplementary_laws_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not SupplementaryClosurePlan or plan != expected:
        raise SupplementaryClosureError(
            "supplementary plan differs from its exact sealed Alpha-v16 parent"
        )
    return plan


def supplementary_pending_layers(
    *,
    existing_names: Sequence[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return exact dependency-ready waves; names alone never grant authority."""

    selected = _sealed_plan(plan)
    supplied = _completed_pending_names(existing_names, selected)
    available = {
        row.name for row in selected.checked_parent_rows
    } | supplied
    remaining = [row for row in selected.pending_rows if row.name not in supplied]
    layers: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name for row in remaining if set(row.dependencies).issubset(available)
        )
        if not ready:
            raise SupplementaryClosureError("supplementary pending graph is cyclic")
        layers.append(ready)
        available.update(ready)
        remaining = [row for row in remaining if row.name not in available]
    return tuple(layers)


def _completed_pending_names(
    names: Sequence[str] | frozenset[str],
    plan: SupplementaryClosurePlan,
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise SupplementaryClosureError(
            "completed supplementary scheduling names must be a tuple, list, or frozenset"
        )
    if any(type(name) is not str for name in names):
        raise SupplementaryClosureError("supplementary scheduling names must be exact strings")
    result = set(names)
    if len(result) != len(names):
        raise SupplementaryClosureError("supplementary scheduling repeats a theorem")
    known = {row.name for row in plan.pending_rows}
    unknown = result.difference(known)
    if unknown:
        raise SupplementaryClosureError(
            f"unknown completed supplementary rows: {sorted(unknown)!r}"
        )
    for row in plan.pending_rows:
        if row.name in result:
            missing = {
                dependency
                for dependency in row.dependencies
                if dependency in known and dependency not in result
            }
            if missing:
                raise SupplementaryClosureError(
                    f"completed supplementary rows are not dependency closed at "
                    f"{row.name!r}: {sorted(missing)!r}"
                )
    return result


def _body_target(row: SupplementaryClosureRow) -> tuple[Formula, Formula]:
    item = v16.ALPHA_ENTRIES[row.alpha_index]
    if (
        item.spec.name != row.name
        or sha256(item.spec.statement.encode("utf-8")).hexdigest()
        != row.statement_sha256
    ):
        raise SupplementaryClosureError(
            f"supplementary row {row.name!r} differs from its exact parent source"
        )
    target = _closed_formula(item.spec.statement)
    curried = target
    for dependency in reversed(item.spec.dependencies):
        curried = Imp(
            _closed_formula(v16.ALPHA_EDITION.by_name[dependency].spec.statement),
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
        raise SupplementaryClosureError(
            f"{label} violates the unchanged 125000-node/25000-object envelope"
        ) from exc


def construct_supplementary_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> SupplementaryBodyMicrobatch:
    """Construct at most sixteen actual independently checked proof bodies."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise SupplementaryClosureError("supplementary microbatch names must be a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise SupplementaryClosureError(
            f"supplementary microbatch must contain 1..{MAX_FRONTIER_CLOSURE_MICROBATCH} bodies"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise SupplementaryClosureError("supplementary microbatch names must be unique exact strings")
    completed = _completed_pending_names(completed_names, selected)
    by_name = {row.name: row for row in selected.pending_rows}
    available = {row.name for row in selected.checked_parent_rows} | completed
    previous = -1
    for name in names:
        row = by_name.get(name)
        if row is None:
            raise SupplementaryClosureError(f"unknown or already-closed supplementary row {name!r}")
        if row.node_id <= previous or name in completed:
            raise SupplementaryClosureError("supplementary microbatch repeats or reorders a row")
        missing = set(row.dependencies).difference(available)
        if missing:
            raise SupplementaryClosureError(
                f"supplementary body {name!r} lacks predecessor bodies: {sorted(missing)!r}"
            )
        available.add(name)
        previous = row.node_id

    result: list[SupplementaryCheckedBody] = []
    nodes = 0
    objects = 0
    annotations = 0
    for name in names:
        row = by_name[name]
        spec = v16.ALPHA_ENTRIES[row.alpha_index].spec
        target, curried = _body_target(row)
        try:
            state = start(curried)
            for dependency in spec.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for position, command in enumerate(spec.script):
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise SupplementaryClosureError(
                        f"supplementary body {name!r} requests implicit authority "
                        f"at command {position}"
                    )
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
        except SupplementaryClosureError:
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
            raise SupplementaryClosureError(
                f"cannot independently check supplementary body {name!r}"
            ) from exc
        metrics = _body_metrics(
            certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"supplementary dependency-curried body {name}",
        )
        proof_nodes, proof_objects, depth, proof_annotations, envelope_depth = metrics
        nodes += proof_nodes
        objects += proof_objects
        annotations += proof_annotations
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise SupplementaryClosureError("supplementary microbatch exceeds its annotation limit")
        result.append(
            SupplementaryCheckedBody(
                node_id=row.node_id,
                alpha_index=row.alpha_index,
                name=name,
                statement_sha256=row.statement_sha256,
                target=target,
                curried_target=curried,
                certificate=certificate,
                proof_nodes=proof_nodes,
                proof_objects=proof_objects,
                proof_depth=depth,
                annotation_occurrences=proof_annotations,
                envelope_depth=envelope_depth,
            )
        )
    return SupplementaryBodyMicrobatch(
        parent_alpha_identity_sha256=selected.parent_alpha_identity_sha256,
        surface_sha256=selected.surface_sha256,
        rows=tuple(result),
        proof_nodes=nodes,
        proof_objects=objects,
        annotation_occurrences=annotations,
    )


def verify_supplementary_body_microbatch(
    batch: SupplementaryBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> SupplementaryBodyMicrobatch:
    """Recheck actual proofs; metrics, names, and receipts grant no authority."""

    selected = _sealed_plan(plan)
    if type(batch) is not SupplementaryBodyMicrobatch:
        raise SupplementaryClosureError("supplementary microbatch has an invalid exact type")
    if (
        batch.parent_alpha_identity_sha256 != selected.parent_alpha_identity_sha256
        or batch.surface_sha256 != selected.surface_sha256
    ):
        raise SupplementaryClosureError("supplementary microbatch changed its frozen parent surface")
    if (
        type(batch.rows) is not tuple
        or not batch.rows
        or len(batch.rows) > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise SupplementaryClosureError("supplementary microbatch exceeds its sixteen-proof policy")
    completed = _completed_pending_names(completed_names, selected)
    available = {row.name for row in selected.checked_parent_rows} | completed
    by_name = {row.name: row for row in selected.pending_rows}
    previous = -1
    nodes = objects = annotations = 0
    for actual in batch.rows:
        if type(actual) is not SupplementaryCheckedBody:
            raise SupplementaryClosureError("supplementary microbatch contains an invalid proof row")
        frozen = by_name.get(actual.name)
        if (
            frozen is None
            or actual.node_id != frozen.node_id
            or actual.alpha_index != frozen.alpha_index
            or actual.statement_sha256 != frozen.statement_sha256
        ):
            raise SupplementaryClosureError(
                f"supplementary proof {actual.name!r} changed its frozen theorem surface"
            )
        if actual.node_id <= previous or actual.name in available:
            raise SupplementaryClosureError("supplementary microbatch repeats or reorders a proof")
        missing = set(frozen.dependencies).difference(available)
        if missing:
            raise SupplementaryClosureError(
                f"supplementary proof {actual.name!r} lacks predecessors: {sorted(missing)!r}"
            )
        target, curried = _body_target(frozen)
        if actual.target != target or actual.curried_target != curried:
            raise SupplementaryClosureError(
                f"supplementary proof {actual.name!r} changed its exact curried target"
            )
        metrics = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"supplementary dependency-curried body {actual.name}",
        )
        if metrics != (
            actual.proof_nodes,
            actual.proof_objects,
            actual.proof_depth,
            actual.annotation_occurrences,
            actual.envelope_depth,
        ):
            raise SupplementaryClosureError(
                f"supplementary proof {actual.name!r} changed its measured envelope"
            )
        if not check((), actual.certificate, curried):
            raise SupplementaryClosureError(
                f"unchanged intuitionistic kernel rejected supplementary proof {actual.name!r}"
            )
        nodes += actual.proof_nodes
        objects += actual.proof_objects
        annotations += actual.annotation_occurrences
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise SupplementaryClosureError("supplementary microbatch exceeds its annotation limit")
        available.add(actual.name)
        previous = actual.node_id
    if (batch.proof_nodes, batch.proof_objects, batch.annotation_occurrences) != (
        nodes,
        objects,
        annotations,
    ):
        raise SupplementaryClosureError("supplementary microbatch changed its aggregate envelope")
    return batch


def encode_supplementary_body_microbatch(
    batch: SupplementaryBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> str:
    """Encode full checked proof trees; metadata alone grants no authority."""

    actual = verify_supplementary_body_microbatch(
        batch,
        completed_names=completed_names,
        plan=plan,
    )
    # The canonical proof codec reconstructs one proof object per structural
    # occurrence. Charge that true future object count before serialization.
    if actual.proof_nodes > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
        raise SupplementaryClosureError(
            "supplementary checkpoint exceeds its 25000-object rehydration bound"
        )
    try:
        rows = [
            [
                row.node_id,
                row.alpha_index,
                row.name,
                row.statement_sha256,
                encode_formula(row.target),
                encode_formula(row.curried_target),
                encode_proof(row.certificate),
                row.proof_nodes,
                row.proof_nodes,
                row.proof_depth,
                row.annotation_occurrences,
                row.envelope_depth,
            ]
            for row in actual.rows
        ]
        payload = json.dumps(
            [
                SUPPLEMENTARY_BODY_CHECKPOINT_FORMAT,
                actual.parent_alpha_identity_sha256,
                actual.surface_sha256,
                rows,
                actual.proof_nodes,
                actual.proof_nodes,
                actual.annotation_occurrences,
            ],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ) + "\n"
    except (OverflowError, ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError(
            "cannot canonically encode the actual supplementary proof microbatch"
        ) from exc
    if len(payload.encode("utf-8")) > MAX_SUPPLEMENTARY_BODY_CHECKPOINT_BYTES:
        raise SupplementaryClosureError("supplementary checkpoint exceeds its 16-MiB limit")
    return payload


def _checkpoint_natural(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise SupplementaryClosureError(
            f"supplementary checkpoint {label} must be an exact nonnegative integer"
        )
    return value


def decode_supplementary_body_microbatch(
    payload: str,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> SupplementaryBodyMicrobatch:
    """Decode canonical actual proof trees and kernel-recheck every body."""

    if type(payload) is not str:
        raise SupplementaryClosureError("supplementary checkpoint must be exact JSON text")
    if len(payload.encode("utf-8")) > MAX_SUPPLEMENTARY_BODY_CHECKPOINT_BYTES:
        raise SupplementaryClosureError("supplementary checkpoint exceeds its 16-MiB limit")
    try:
        decoded = json.loads(payload)
        canonical = json.dumps(
            decoded,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ) + "\n"
    except (json.JSONDecodeError, OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError("supplementary checkpoint is not canonical JSON") from exc
    if canonical != payload:
        raise SupplementaryClosureError("supplementary checkpoint JSON bytes are not canonical")
    if (
        type(decoded) is not list
        or len(decoded) != 7
        or decoded[0] != SUPPLEMENTARY_BODY_CHECKPOINT_FORMAT
        or type(decoded[1]) is not str
        or type(decoded[2]) is not str
        or type(decoded[3]) is not list
        or not decoded[3]
        or len(decoded[3]) > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise SupplementaryClosureError(
            "supplementary checkpoint has invalid version, provenance, or row count"
        )
    proof_nodes = _checkpoint_natural(decoded[4], "proof-node count")
    proof_objects = _checkpoint_natural(decoded[5], "proof-object count")
    annotations = _checkpoint_natural(decoded[6], "annotation count")
    if (
        proof_nodes > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        or proof_objects > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        or annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences
    ):
        raise SupplementaryClosureError("supplementary checkpoint declares an unsafe envelope")
    rows: list[SupplementaryCheckedBody] = []
    try:
        for item in decoded[3]:
            if type(item) is not list or len(item) != 12:
                raise SupplementaryClosureError("supplementary checkpoint row has invalid arity")
            if type(item[2]) is not str or type(item[3]) is not str:
                raise SupplementaryClosureError("supplementary checkpoint row has invalid identity")
            rows.append(
                SupplementaryCheckedBody(
                    node_id=_checkpoint_natural(item[0], "node ID"),
                    alpha_index=_checkpoint_natural(item[1], "Alpha enrollment index"),
                    name=item[2],
                    statement_sha256=item[3],
                    target=decode_formula(item[4]),
                    curried_target=decode_formula(item[5]),
                    certificate=decode_proof(item[6]),
                    proof_nodes=_checkpoint_natural(item[7], "body proof-node count"),
                    proof_objects=_checkpoint_natural(item[8], "body proof-object count"),
                    proof_depth=_checkpoint_natural(item[9], "body proof depth"),
                    annotation_occurrences=_checkpoint_natural(item[10], "body annotation count"),
                    envelope_depth=_checkpoint_natural(item[11], "body envelope depth"),
                )
            )
    except SupplementaryClosureError:
        raise
    except (AttributeError, ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError(
            "supplementary checkpoint contains a malformed formula or proof"
        ) from exc
    return verify_supplementary_body_microbatch(
        SupplementaryBodyMicrobatch(
            parent_alpha_identity_sha256=decoded[1],
            surface_sha256=decoded[2],
            rows=tuple(rows),
            proof_nodes=proof_nodes,
            proof_objects=proof_objects,
            annotation_occurrences=annotations,
        ),
        completed_names=completed_names,
        plan=plan,
    )


def _checkpoint_filename(first: SupplementaryClosureRow, last: SupplementaryClosureRow) -> str:
    return f"supplementary-body-{first.node_id:04d}-{last.node_id:04d}.json"


def write_supplementary_body_checkpoint(
    batch: SupplementaryBodyMicrobatch,
    directory: str | Path,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> Path:
    """Create one deterministic actual-proof checkpoint without overwriting."""

    if not isinstance(directory, (str, Path)):
        raise SupplementaryClosureError("supplementary checkpoint directory must be a path")
    folder = Path(directory)
    if not folder.is_dir():
        raise SupplementaryClosureError("supplementary checkpoint directory must already exist")
    payload = encode_supplementary_body_microbatch(
        batch,
        completed_names=completed_names,
        plan=plan,
    )
    path = folder / (
        f"supplementary-body-{batch.rows[0].node_id:04d}-{batch.rows[-1].node_id:04d}.json"
    )
    try:
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise SupplementaryClosureError(
            f"cannot create fresh supplementary proof checkpoint {path!s}"
        ) from exc
    return path


def load_supplementary_body_checkpoint(
    source: str | Path,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: SupplementaryClosurePlan | None = None,
) -> SupplementaryBodyMicrobatch:
    """Load deterministic bounded proof bytes and independently recheck them."""

    if not isinstance(source, (str, Path)):
        raise SupplementaryClosureError("supplementary checkpoint source must be a path")
    path = Path(source)
    try:
        if path.stat().st_size > MAX_SUPPLEMENTARY_BODY_CHECKPOINT_BYTES:
            raise SupplementaryClosureError("supplementary checkpoint exceeds its 16-MiB limit")
        payload = path.read_text(encoding="utf-8")
    except SupplementaryClosureError:
        raise
    except (OSError, UnicodeError) as exc:
        raise SupplementaryClosureError(
            f"cannot read bounded supplementary proof checkpoint {path!s}"
        ) from exc
    batch = decode_supplementary_body_microbatch(
        payload,
        completed_names=completed_names,
        plan=plan,
    )
    expected = (
        f"supplementary-body-{batch.rows[0].node_id:04d}-{batch.rows[-1].node_id:04d}.json"
    )
    if path.name != expected:
        raise SupplementaryClosureError("supplementary checkpoint filename changes exact proof IDs")
    return batch


def _synthetic_conjunction_body() -> Proof:
    return ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0))))


def check_supplementary_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: SupplementaryClosurePlan | None = None,
) -> SupplementaryCheckedBundle:
    """Verify every exact theorem body and both roots using the existing kernel."""

    selected = _sealed_plan(plan)
    if type(bundle) is not ProofBundle:
        raise SupplementaryClosureError("supplementary evidence must be a real proof bundle")
    if (
        type(bundle.nodes) is not tuple
        or len(bundle.nodes) != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT
        or bundle.root != EXPECTED_SUPPLEMENTARY_THEOREM_COUNT
    ):
        raise SupplementaryClosureError("supplementary proof graph changed its exact node count or root")
    positions = {row.name: row.node_id for row in selected.rows}
    for row, node in zip(selected.rows, bundle.nodes[:-1], strict=True):
        expected, _curried = _body_target(row)
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != expected
            or node.dependencies
            != tuple(positions[dependency] for dependency in row.dependencies)
        ):
            raise SupplementaryClosureError(
                f"supplementary bundle changed exact frozen theorem {row.name!r}"
            )
    roots = tuple(positions[name] for name in selected.roots)
    left = bundle.nodes[roots[0]].target
    right = bundle.nodes[roots[1]].target
    exact_target = And(left, right)
    synthetic = bundle.nodes[-1]
    if (
        target != exact_target
        or type(synthetic) is not BundleNode
        or synthetic.node_id != EXPECTED_SUPPLEMENTARY_THEOREM_COUNT
        or synthetic.target != exact_target
        or synthetic.dependencies != roots
        or synthetic.body != _synthetic_conjunction_body()
    ):
        raise SupplementaryClosureError(
            "supplementary conjunction changed either exact theorem root or its constructive body"
        )
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError(
            "the unchanged intuitionistic kernel rejected the complete supplementary proof graph"
        ) from exc
    if (
        receipt.node_count != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT
        or receipt.kernel_calls != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT
        or receipt.target != exact_target
    ):
        raise SupplementaryClosureError("supplementary proof bundle returned inconsistent evidence")
    return SupplementaryCheckedBundle(bundle, target, receipt, selected.surface_sha256)


def assemble_supplementary_proof_bundle(
    batches: Sequence[SupplementaryBodyMicrobatch],
    *,
    plan: SupplementaryClosurePlan | None = None,
) -> SupplementaryCheckedBundle:
    """Combine 406 genuinely proved QR rows with all 31 newly checked bodies."""

    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise SupplementaryClosureError("supplementary proof batches must be an ordered tuple or list")
    actual: dict[str, SupplementaryCheckedBody] = {}
    completed: list[str] = []
    for batch in batches:
        verify_supplementary_body_microbatch(
            batch,
            completed_names=completed,
            plan=selected,
        )
        for row in batch.rows:
            if row.name in actual:
                raise SupplementaryClosureError(
                    f"supplementary closure repeats proof body {row.name!r}"
                )
            actual[row.name] = row
            completed.append(row.name)
    required = {row.name for row in selected.pending_rows}
    if set(actual) != required:
        raise SupplementaryClosureError(
            f"supplementary closure requires exactly {len(required)} actual proof bodies; "
            f"received {len(actual)}"
        )

    try:
        qr_bundle, _receipt = v16._checked_qr_bundle()
    except (v16.EditionV16Error, ProofBundleError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError(
            "the genuine independently checked parent QR proof bundle is unavailable"
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
            tuple(positions[dependency] for dependency in row.dependencies),
            actual[row.name].certificate
            if row.needs_closure
            else qr_nodes[row.name].body,
        )
        for row in selected.rows
    )
    roots = tuple(positions[name] for name in selected.roots)
    target = And(nodes[roots[0]].target, nodes[roots[1]].target)
    synthetic = BundleNode(
        EXPECTED_SUPPLEMENTARY_THEOREM_COUNT,
        target,
        roots,
        _synthetic_conjunction_body(),
    )
    return check_supplementary_proof_bundle(
        ProofBundle(nodes + (synthetic,), synthetic.node_id),
        target,
        plan=selected,
    )


_supplementary_bundle_source: Path | None = None


def _default_supplementary_bundle_source() -> Path:
    pyodide = Path(PYODIDE_SUPPLEMENTARY_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    if len(location.parents) > 4:
        return (
            location.parents[4]
            / "research"
            / "arithmetic-library"
            / "artifacts"
            / "supplementary-laws-proof-bundle-v1.json"
        )
    return pyodide


def set_supplementary_bundle_source(source: str | Path | None) -> None:
    """Change explicit proof-data source and invalidate all proof caches."""

    global _supplementary_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise SupplementaryClosureError("supplementary proof source must be a filesystem path")
    _supplementary_bundle_source = None if source is None else Path(source)
    _checked_supplementary_bundle.cache_clear()
    replay_supplementary_closed_theorem.cache_clear()


@lru_cache(maxsize=1)
def _checked_supplementary_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _supplementary_bundle_source or _default_supplementary_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SupplementaryClosureError(
            f"actual supplementary-law proof data are unavailable: {source!s}"
        ) from exc
    data = payload.encode("utf-8")
    if (
        len(data) != EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256
    ):
        raise SupplementaryClosureError(
            "supplementary proof artifact differs from its frozen actual-proof provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError(
            "supplementary artifact is not a canonical complete constructive proof bundle"
        ) from exc
    actual = check_supplementary_proof_bundle(bundle, target)
    if actual.receipt.total_body_nodes != EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES:
        raise SupplementaryClosureError("supplementary proof bundle body metrics changed")
    return actual.bundle, actual.receipt


def checked_supplementary_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Return only independently checked actual complete proof data."""

    return _checked_supplementary_bundle()


@lru_cache(maxsize=None)
def replay_supplementary_closed_theorem(name: str) -> CheckedTheorem:
    """Construct and kernel-check one actual ordinary empty-context proof."""

    if type(name) is not str:
        raise SupplementaryClosureError("supplementary replay name must be an exact string")
    plan = supplementary_laws_closure_plan()
    row = next((item for item in plan.pending_rows if item.name == name), None)
    if row is None:
        raise SupplementaryClosureError(
            f"theorem {name!r} is outside the exact 31-row supplementary promotion"
        )
    bundle, _receipt = _checked_supplementary_bundle()
    required: set[int] = set()
    pending = [row.node_id]
    while pending:
        node_id = pending.pop()
        if node_id not in required:
            required.add(node_id)
            pending.extend(bundle.nodes[node_id].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(
                node.node_id,
                node.target,
                node.dependencies,
                node.body,
            )
            for node in bundle.nodes[:-1]
            if node.node_id in required
        ),
        row.node_id,
    )
    item = v16.ALPHA_ENTRIES[row.alpha_index]
    formula = _closed_formula(item.spec.statement)
    try:
        candidate = compile_layered_replay(
            layered,
            formula,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
    except (LayeredReplayError, RecursionError, TypeError, ValueError) as exc:
        raise SupplementaryClosureError(
            f"cannot compile the ordinary supplementary theorem proof {name!r}"
        ) from exc
    if candidate is None:
        raise SupplementaryClosureError(
            f"supplementary theorem {name!r} exceeds the unchanged layered resource policy"
        )
    if not check((), candidate.certificate, formula):
        raise SupplementaryClosureError(
            f"the unchanged intuitionistic kernel rejected supplementary theorem {name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


def export_supplementary_proof_bundle(
    destination: str | Path,
    *,
    batch_size: int = MAX_FRONTIER_CLOSURE_MICROBATCH,
    checkpoint_directory: str | Path | None = None,
) -> tuple[Path, SupplementaryCheckedBundle]:
    """Construct all actual proofs and durably export one new canonical bundle."""

    if not isinstance(destination, (str, Path)):
        raise SupplementaryClosureError("supplementary export destination must be a filesystem path")
    if (
        type(batch_size) is not int
        or batch_size <= 0
        or batch_size > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise SupplementaryClosureError("supplementary export batch size must be between 1 and 16")
    if checkpoint_directory is not None and not isinstance(
        checkpoint_directory,
        (str, Path),
    ):
        raise SupplementaryClosureError("supplementary checkpoint directory must be a path")
    folder = None if checkpoint_directory is None else Path(checkpoint_directory)
    if folder is not None and not folder.is_dir():
        raise SupplementaryClosureError("supplementary checkpoint directory must already exist")
    path = Path(destination)
    if path.exists():
        raise SupplementaryClosureError(
            f"supplementary proof artifact destination already exists: {path!s}"
        )
    plan = supplementary_laws_closure_plan()
    ordered = tuple(row.name for row in plan.pending_rows)
    by_name = {row.name: row for row in plan.pending_rows}
    completed: list[str] = []
    batches: list[SupplementaryBodyMicrobatch] = []
    for start_index in range(0, len(ordered), batch_size):
        names = ordered[start_index : start_index + batch_size]
        checkpoint = (
            None
            if folder is None
            else folder / _checkpoint_filename(by_name[names[0]], by_name[names[-1]])
        )
        if checkpoint is not None and checkpoint.is_file():
            batch = load_supplementary_body_checkpoint(
                checkpoint,
                completed_names=completed,
                plan=plan,
            )
            if batch.names != names:
                raise SupplementaryClosureError(
                    "supplementary checkpoint does not match the exact deterministic batch"
                )
        else:
            batch = construct_supplementary_body_microbatch(
                names,
                completed_names=completed,
                plan=plan,
            )
            if folder is not None:
                written = write_supplementary_body_checkpoint(
                    batch,
                    folder,
                    completed_names=completed,
                    plan=plan,
                )
                batch = load_supplementary_body_checkpoint(
                    written,
                    completed_names=completed,
                    plan=plan,
                )
        verify_supplementary_body_microbatch(
            batch,
            completed_names=completed,
            plan=plan,
        )
        batches.append(batch)
        completed.extend(batch.names)
    actual = assemble_supplementary_proof_bundle(tuple(batches), plan=plan)
    payload = encode_proof_bundle(actual.bundle, actual.target)
    canonical, target = decode_proof_bundle(payload)
    check_supplementary_proof_bundle(canonical, target, plan=plan)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise SupplementaryClosureError(
            f"cannot create fresh supplementary proof artifact {path!s}"
        ) from exc
    return path, actual


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Construct and independently check both supplementary-law proofs."
    )
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=MAX_FRONTIER_CLOSURE_MICROBATCH)
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        help="Existing directory for deterministic resumable actual-proof checkpoints.",
    )
    options = parser.parse_args(argv)
    path, actual = export_supplementary_proof_bundle(
        options.export,
        batch_size=options.batch_size,
        checkpoint_directory=options.checkpoint_dir,
    )
    data = path.read_bytes()
    print(
        json.dumps(
            {
                "path": str(path),
                "bytes": len(data),
                "sha256": sha256(data).hexdigest(),
                "theorem_count": EXPECTED_SUPPLEMENTARY_THEOREM_COUNT,
                "promotion_count": EXPECTED_SUPPLEMENTARY_PROMOTION_COUNT,
                "bundle_nodes": actual.receipt.node_count,
                "bundle_edges": actual.receipt.dependency_edges,
                "body_proof_nodes": actual.receipt.total_body_nodes,
                "kernel_calls": actual.receipt.kernel_calls,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256",
    "EXPECTED_SUPPLEMENTARY_CHECKED_PARENT_COUNT",
    "EXPECTED_SUPPLEMENTARY_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_SUPPLEMENTARY_NEW_BODY_COUNT",
    "EXPECTED_SUPPLEMENTARY_ORDERED_NAMES_SHA256",
    "EXPECTED_SUPPLEMENTARY_PROMOTION_COUNT",
    "EXPECTED_SUPPLEMENTARY_PROMOTION_NAMES_SHA256",
    "EXPECTED_SUPPLEMENTARY_ROOT_NODE_IDS",
    "EXPECTED_SUPPLEMENTARY_ROOT_STATEMENT_SHA256",
    "EXPECTED_SUPPLEMENTARY_SURFACE_SHA256",
    "EXPECTED_SUPPLEMENTARY_THEOREM_COUNT",
    "MAX_SUPPLEMENTARY_BODY_CHECKPOINT_BYTES",
    "PYODIDE_SUPPLEMENTARY_BUNDLE_PATH",
    "SUPPLEMENTARY_BODY_CHECKPOINT_FORMAT",
    "SUPPLEMENTARY_EXISTING_BERTRAND_NAMES",
    "SUPPLEMENTARY_ROOT_NAMES",
    "SupplementaryBodyMicrobatch",
    "SupplementaryCheckedBody",
    "SupplementaryCheckedBundle",
    "SupplementaryClosureError",
    "SupplementaryClosurePlan",
    "SupplementaryClosureRow",
    "assemble_supplementary_proof_bundle",
    "check_supplementary_proof_bundle",
    "checked_supplementary_proof_bundle",
    "construct_supplementary_body_microbatch",
    "decode_supplementary_body_microbatch",
    "encode_supplementary_body_microbatch",
    "export_supplementary_proof_bundle",
    "load_supplementary_body_checkpoint",
    "replay_supplementary_closed_theorem",
    "set_supplementary_bundle_source",
    "supplementary_laws_closure_plan",
    "supplementary_pending_layers",
    "verify_supplementary_body_microbatch",
    "write_supplementary_body_checkpoint",
]
