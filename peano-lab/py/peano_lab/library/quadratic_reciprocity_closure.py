"""Bounded, fail-closed construction of the genuine quadratic-reciprocity root.

The 557 reviewed theorem scripts already form one dependency-closed graph, but
replaying all of them in one unbounded workstation operation is unsafe.  This
module exposes deterministic microbatches of at most sixteen *actual*,
independently checked dependency-curried proof bodies.  Such a body is not an
empty-context proof of its uncurried theorem, and neither a microbatch nor a
receipt changes Alpha, Stable, checked-use authority, or release evidence.

Only :func:`assemble_quadratic_reciprocity_root` may return a closed-root
candidate.  It rechecks every supplied real body, compiles an ordinary layered
``Cut`` certificate under the existing capacity policy, and asks the unchanged
intuitionistic kernel to check that certificate from the empty context.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import platform
import resource
from time import perf_counter
from typing import Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import Formula, Imp
from ..kernel.proofs import Proof
from . import editions_v15 as v15
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
    intern_layered_replay_bodies,
)
from .quadratic_reciprocity_stack import QR_ROOT_NAME
from .quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from .quadratic_residue_surface import QUADRATIC_RECIPROCITY_COMBINED
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
from .theorems import _closed_formula, _primitive


QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_FORMAT = (
    "peano-lab-qr-body-batch-v1"
)
MAX_QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_BYTES = 16 * 1024 * 1024


class QuadraticReciprocityClosureError(ValueError):
    """A frozen QR surface, microbatch, body, or final certificate is invalid."""


@dataclass(frozen=True, slots=True)
class QuadraticReciprocityClosureRow:
    """One frozen theorem surface; its evidence is never strengthened here."""

    node_id: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    layer: int
    script_command_count: int
    evidence: str


@dataclass(frozen=True, slots=True)
class QuadraticReciprocityClosurePlan:
    """Exact immutable 557-node source/Alpha snapshot, without proof claims."""

    root: str
    graph_sha256: str
    source_sha256: str
    alpha_enrollment_sha256: str
    alpha_identity_sha256: str
    rows: tuple[QuadraticReciprocityClosureRow, ...]
    layers: tuple[tuple[str, ...], ...]
    dependency_edge_count: int


@dataclass(frozen=True, slots=True)
class QuadraticReciprocityCheckedBody:
    """Actual checked proof of ``dependency_1 -> ... -> target`` only."""

    node_id: int
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
class QuadraticReciprocityBodyBatch:
    """Bounded checked proof bodies, explicitly not closed-theorem evidence."""

    graph_sha256: str
    source_sha256: str
    alpha_identity_sha256: str
    rows: tuple[QuadraticReciprocityCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class QuadraticReciprocityClosedRoot:
    """One actual unchanged-kernel-accepted empty-context QR certificate."""

    certificate: Proof
    target: Formula
    graph_sha256: str
    source_sha256: str
    body_count: int
    dependency_edge_count: int
    layer_count: int
    proof_nodes: int
    proof_objects: int
    proof_depth: int
    annotation_occurrences: int
    envelope_depth: int


@dataclass(frozen=True, slots=True)
class QuadraticReciprocityCheckedBundle:
    """Actual self-contained QR theorem graph checked once node by node."""

    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    graph_sha256: str
    source_sha256: str


@lru_cache(maxsize=1)
def quadratic_reciprocity_closure_plan() -> QuadraticReciprocityClosurePlan:
    """Freeze the actual stack and exact Alpha-v15 evidence without replay."""

    stack = quadratic_reciprocity_stack()
    table = v15.ALPHA_EDITION.by_name
    rows: list[QuadraticReciprocityClosureRow] = []
    seen: set[str] = set()
    edge_count = 0
    for node_id, spec in enumerate(stack.admission_order):
        entry = table.get(spec.name)
        if entry is None or entry.spec != spec:
            raise QuadraticReciprocityClosureError(
                f"QR row {spec.name!r} does not match the sealed Alpha-v15 source"
            )
        if spec.name in seen:
            raise QuadraticReciprocityClosureError(
                f"duplicate QR closure theorem {spec.name!r}"
            )
        missing = set(spec.dependencies).difference(seen)
        if missing:
            raise QuadraticReciprocityClosureError(
                f"non-topological QR dependencies for {spec.name!r}: "
                f"{sorted(missing)!r}"
            )
        rows.append(
            QuadraticReciprocityClosureRow(
                node_id=node_id,
                name=spec.name,
                statement_sha256=sha256(
                    spec.statement.encode("utf-8")
                ).hexdigest(),
                dependencies=spec.dependencies,
                layer=stack.dependency_depth_by_name[spec.name],
                script_command_count=len(spec.script),
                evidence=entry.evidence.value,
            )
        )
        seen.add(spec.name)
        edge_count += len(spec.dependencies)

    if not rows or rows[-1].name != QR_ROOT_NAME:
        raise QuadraticReciprocityClosureError(
            "QR closure graph does not end in its exact pending root"
        )
    if rows[-1].evidence != v15.EvidenceStatus.PENDING_LAYERED_CLOSURE.value:
        raise QuadraticReciprocityClosureError(
            "QR root is not the sealed pending-layered-closure entry"
        )
    if _closed_formula(stack.admission_order[-1].statement) != _closed_formula(
        QUADRATIC_RECIPROCITY_COMBINED
    ):
        raise QuadraticReciprocityClosureError(
            "QR closure root does not match its exact public mathematical surface"
        )
    return QuadraticReciprocityClosurePlan(
        root=QR_ROOT_NAME,
        graph_sha256=stack.graph_sha256,
        source_sha256=stack.source_sha256,
        alpha_enrollment_sha256=v15.ALPHA_V15_ENROLLMENT_SHA256,
        alpha_identity_sha256=v15.ALPHA_V15_IDENTITY_SHA256,
        rows=tuple(rows),
        layers=tuple(
            tuple(spec.name for spec in layer)
            for layer in stack.dependency_layers
        ),
        dependency_edge_count=edge_count,
    )


def _sealed_plan(
    plan: QuadraticReciprocityClosurePlan | None,
) -> QuadraticReciprocityClosurePlan:
    expected = quadratic_reciprocity_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not QuadraticReciprocityClosurePlan or plan != expected:
        raise QuadraticReciprocityClosureError(
            "QR closure plan does not match its exact sealed Alpha-v15 snapshot"
        )
    return plan


def _checked_name_set(
    names: object,
    *,
    plan: QuadraticReciprocityClosurePlan,
    label: str,
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise QuadraticReciprocityClosureError(
            f"{label} must be a tuple, list, or frozenset of exact theorem names"
        )
    if any(type(name) is not str for name in names):
        raise QuadraticReciprocityClosureError(
            f"{label} must contain only exact theorem names"
        )
    result = set(names)
    if len(result) != len(names):
        raise QuadraticReciprocityClosureError(f"{label} repeats a theorem")
    known = {row.name for row in plan.rows}
    unexpected = result.difference(known)
    if unexpected:
        raise QuadraticReciprocityClosureError(
            f"{label} contains unknown QR theorems: {sorted(unexpected)!r}"
        )
    for row in plan.rows:
        if row.name in result:
            missing = set(row.dependencies).difference(result)
            if missing:
                raise QuadraticReciprocityClosureError(
                    f"{label} is not dependency closed at {row.name!r}: "
                    f"{sorted(missing)!r}"
                )
    return result


def quadratic_reciprocity_next_microbatch(
    completed_names: Sequence[str] | frozenset[str] = (),
    *,
    plan: QuadraticReciprocityClosurePlan | None = None,
    max_rows: int = MAX_FRONTIER_CLOSURE_MICROBATCH,
) -> tuple[str, ...]:
    """Return the next dependency-safe batch; completed names grant no authority."""

    selected = _sealed_plan(plan)
    if (
        type(max_rows) is not int
        or max_rows <= 0
        or max_rows > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise QuadraticReciprocityClosureError(
            f"QR microbatch size must be in [1,{MAX_FRONTIER_CLOSURE_MICROBATCH}]"
        )
    completed = _checked_name_set(
        completed_names,
        plan=selected,
        label="completed QR scheduling names",
    )
    return tuple(
        row.name for row in selected.rows if row.name not in completed
    )[:max_rows]


def _body_target(
    row: QuadraticReciprocityClosureRow,
) -> tuple[Formula, Formula]:
    stack = quadratic_reciprocity_stack()
    spec = stack.admission_order[row.node_id]
    if spec.name != row.name:
        raise QuadraticReciprocityClosureError(
            f"QR row {row.name!r} no longer matches its source position"
        )
    target = _closed_formula(spec.statement)
    curried = target
    for dependency in reversed(spec.dependencies):
        curried = Imp(
            _closed_formula(v15.ALPHA_EDITION.by_name[dependency].spec.statement),
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
    except (
        AttributeError,
        LayeredReplayError,
        RecursionError,
        TypeError,
        ValueError,
    ) as exc:
        raise QuadraticReciprocityClosureError(
            f"{label} violates its unchanged proof/resource envelope"
        ) from exc


def construct_quadratic_reciprocity_body_batch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> QuadraticReciprocityBodyBatch:
    """Build at most sixteen real checked bodies, never a closed QR theorem."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise QuadraticReciprocityClosureError(
            "QR microbatch theorem names must be a tuple or list"
        )
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise QuadraticReciprocityClosureError(
            f"QR microbatch must contain between 1 and "
            f"{MAX_FRONTIER_CLOSURE_MICROBATCH} theorem bodies"
        )
    if any(type(name) is not str for name in names):
        raise QuadraticReciprocityClosureError(
            "QR microbatch names must be exact strings"
        )
    if len(set(names)) != len(names):
        raise QuadraticReciprocityClosureError(
            "QR microbatch repeats a theorem body"
        )
    completed = _checked_name_set(
        completed_names,
        plan=selected,
        label="completed QR scheduling names",
    )
    table = {row.name: row for row in selected.rows}
    previous_node_id = -1
    ready = set(completed)
    for name in names:
        row = table.get(name)
        if row is None:
            raise QuadraticReciprocityClosureError(
                f"unknown QR microbatch theorem {name!r}"
            )
        if row.node_id <= previous_node_id:
            raise QuadraticReciprocityClosureError(
                "QR microbatch is not in its sealed dependency-safe source order"
            )
        if name in completed:
            raise QuadraticReciprocityClosureError(
                f"QR microbatch theorem {name!r} is already scheduled complete"
            )
        missing = set(row.dependencies).difference(ready)
        if missing:
            raise QuadraticReciprocityClosureError(
                f"QR theorem {name!r} has unfinished batch predecessors: "
                f"{sorted(missing)!r}"
            )
        ready.add(name)
        previous_node_id = row.node_id

    stack = quadratic_reciprocity_stack()
    bodies: list[QuadraticReciprocityCheckedBody] = []
    total_nodes = 0
    total_objects = 0
    total_annotations = 0
    for name in names:
        row = table[name]
        spec = stack.admission_order[row.node_id]
        target, body_target = _body_target(row)
        try:
            state = start(body_target)
            for dependency in spec.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for command_index, command in enumerate(spec.script):
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise QuadraticReciprocityClosureError(
                        f"QR theorem {name!r} attempts unchecked external "
                        f"authority at command {command_index}"
                    )
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, body_target)
        except QuadraticReciprocityClosureError:
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
            raise QuadraticReciprocityClosureError(
                f"cannot independently check the actual QR body for {name!r}"
            ) from exc

        nodes, objects, depth, annotations, envelope_depth = _body_metrics(
            certificate,
            node_budget=(
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - total_nodes
            ),
            object_budget=(
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - total_objects
            ),
            label=f"QR dependency-curried body {name}",
        )
        total_nodes += nodes
        total_objects += objects
        total_annotations += annotations
        if (
            total_annotations
            > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences
        ):
            raise QuadraticReciprocityClosureError(
                "QR microbatch exceeds its total proof-annotation budget"
            )
        bodies.append(
            QuadraticReciprocityCheckedBody(
                node_id=row.node_id,
                name=name,
                statement_sha256=row.statement_sha256,
                target=target,
                curried_target=body_target,
                certificate=certificate,
                proof_nodes=nodes,
                proof_objects=objects,
                proof_depth=depth,
                annotation_occurrences=annotations,
                envelope_depth=envelope_depth,
            )
        )
    return QuadraticReciprocityBodyBatch(
        graph_sha256=selected.graph_sha256,
        source_sha256=selected.source_sha256,
        alpha_identity_sha256=selected.alpha_identity_sha256,
        rows=tuple(bodies),
        proof_nodes=total_nodes,
        proof_objects=total_objects,
        annotation_occurrences=total_annotations,
    )


def verify_quadratic_reciprocity_body_batch(
    batch: QuadraticReciprocityBodyBatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> QuadraticReciprocityBodyBatch:
    """Recheck every actual batch proof; receipt fields grant no authority."""

    selected = _sealed_plan(plan)
    if type(batch) is not QuadraticReciprocityBodyBatch:
        raise QuadraticReciprocityClosureError(
            "QR body batch must be an exact bounded proof-batch value"
        )
    if (
        batch.graph_sha256 != selected.graph_sha256
        or batch.source_sha256 != selected.source_sha256
        or batch.alpha_identity_sha256 != selected.alpha_identity_sha256
    ):
        raise QuadraticReciprocityClosureError(
            "QR body batch does not match its frozen source/Alpha snapshot"
        )
    if type(batch.rows) is not tuple or not batch.rows:
        raise QuadraticReciprocityClosureError("QR body batch has no proof rows")
    if len(batch.rows) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise QuadraticReciprocityClosureError(
            "QR body batch exceeds its sixteen-body resource policy"
        )
    completed = _checked_name_set(
        completed_names,
        plan=selected,
        label="completed QR scheduling names",
    )
    table = {row.name: row for row in selected.rows}
    seen = set(completed)
    previous_node_id = -1
    total_nodes = 0
    total_objects = 0
    total_annotations = 0
    for row in batch.rows:
        if type(row) is not QuadraticReciprocityCheckedBody:
            raise QuadraticReciprocityClosureError(
                "QR body batch contains a noncanonical proof row"
            )
        frozen = table.get(row.name)
        if (
            frozen is None
            or row.node_id != frozen.node_id
            or row.statement_sha256 != frozen.statement_sha256
        ):
            raise QuadraticReciprocityClosureError(
                f"QR batch proof {row.name!r} changed its frozen theorem surface"
            )
        if row.node_id <= previous_node_id or row.name in seen:
            raise QuadraticReciprocityClosureError(
                "QR body batch repeats or reorders a theorem"
            )
        missing = set(frozen.dependencies).difference(seen)
        if missing:
            raise QuadraticReciprocityClosureError(
                f"QR batch proof {row.name!r} has unfinished predecessors: "
                f"{sorted(missing)!r}"
            )
        target, body_target = _body_target(frozen)
        if row.target != target or row.curried_target != body_target:
            raise QuadraticReciprocityClosureError(
                f"QR batch proof {row.name!r} changed its exact curried target"
            )
        metrics = _body_metrics(
            row.certificate,
            node_budget=(
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - total_nodes
            ),
            object_budget=(
                MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - total_objects
            ),
            label=f"QR dependency-curried body {row.name}",
        )
        nodes, objects, depth, annotations, envelope_depth = metrics
        if metrics != (
            row.proof_nodes,
            row.proof_objects,
            row.proof_depth,
            row.annotation_occurrences,
            row.envelope_depth,
        ):
            raise QuadraticReciprocityClosureError(
                f"QR batch proof {row.name!r} changed its exact measured envelope"
            )
        if not check((), row.certificate, body_target):
            raise QuadraticReciprocityClosureError(
                f"the unchanged kernel rejected QR body {row.name!r}"
            )
        total_nodes += nodes
        total_objects += objects
        total_annotations += annotations
        if (
            total_annotations
            > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences
        ):
            raise QuadraticReciprocityClosureError(
                "QR body batch exceeds its total proof-annotation budget"
            )
        seen.add(row.name)
        previous_node_id = row.node_id
    if (
        batch.proof_nodes != total_nodes
        or batch.proof_objects != total_objects
        or batch.annotation_occurrences != total_annotations
    ):
        raise QuadraticReciprocityClosureError(
            "QR body batch changed its measured cumulative resource envelope"
        )
    return batch


def encode_quadratic_reciprocity_body_batch(
    batch: QuadraticReciprocityBodyBatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> str:
    """Serialize complete real proof data; no digest or receipt replaces it."""

    verified = verify_quadratic_reciprocity_body_batch(
        batch,
        completed_names=completed_names,
        plan=plan,
    )
    # The canonical v2 proof codec is a self-contained tree, not an
    # identity-addressed DAG.  Decoding therefore turns every structural proof
    # occurrence into a distinct immutable object.  Charge that honest future
    # object count now rather than exporting an artifact that would exceed the
    # reviewed workstation envelope after rehydration.
    checkpoint_objects = verified.proof_nodes
    if checkpoint_objects > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint would exceed its proof-object bound after "
            "self-contained tree decoding"
        )
    try:
        rows = [
            [
                row.node_id,
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
            for row in verified.rows
        ]
        payload = json.dumps(
            [
                QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_FORMAT,
                verified.graph_sha256,
                verified.source_sha256,
                verified.alpha_identity_sha256,
                rows,
                verified.proof_nodes,
                checkpoint_objects,
                verified.annotation_occurrences,
            ],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ) + "\n"
    except (
        OverflowError,
        ProofBundleError,
        RecursionError,
        TypeError,
        ValueError,
    ) as exc:
        raise QuadraticReciprocityClosureError(
            "cannot canonically encode the actual checked QR body batch"
        ) from exc
    if (
        len(payload.encode("utf-8"))
        > MAX_QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_BYTES
    ):
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint exceeds its reviewed 16-MiB transport bound"
        )
    return payload


def _checkpoint_natural(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise QuadraticReciprocityClosureError(
            f"QR body checkpoint {label} must be an exact nonnegative integer"
        )
    return value


def decode_quadratic_reciprocity_body_batch(
    payload: str,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> QuadraticReciprocityBodyBatch:
    """Decode bounded canonical proof bytes and independently recheck all bodies."""

    if type(payload) is not str:
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint must be exact canonical JSON text"
        )
    if (
        len(payload.encode("utf-8"))
        > MAX_QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_BYTES
    ):
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint exceeds its reviewed 16-MiB transport bound"
        )
    try:
        decoded = json.loads(payload)
        canonical = json.dumps(
            decoded,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ) + "\n"
    except (
        json.JSONDecodeError,
        OverflowError,
        RecursionError,
        TypeError,
        ValueError,
    ) as exc:
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint is not valid bounded canonical JSON"
        ) from exc
    if canonical != payload:
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint JSON bytes are not canonical"
        )
    if (
        type(decoded) is not list
        or len(decoded) != 8
        or decoded[0] != QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_FORMAT
        or any(type(value) is not str for value in decoded[1:4])
        or type(decoded[4]) is not list
        or not decoded[4]
        or len(decoded[4]) > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint has an invalid version, provenance, or row count"
        )
    proof_nodes = _checkpoint_natural(decoded[5], "proof-node count")
    proof_objects = _checkpoint_natural(decoded[6], "proof-object count")
    annotation_occurrences = _checkpoint_natural(
        decoded[7],
        "annotation count",
    )
    if (
        proof_nodes > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        or proof_objects > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        or annotation_occurrences
        > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences
    ):
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint declares an out-of-policy proof envelope"
        )

    rows: list[QuadraticReciprocityCheckedBody] = []
    try:
        for item in decoded[4]:
            if type(item) is not list or len(item) != 11:
                raise QuadraticReciprocityClosureError(
                    "QR body checkpoint row has an invalid exact arity"
                )
            if type(item[1]) is not str or type(item[2]) is not str:
                raise QuadraticReciprocityClosureError(
                    "QR body checkpoint row has an invalid theorem identity"
                )
            rows.append(
                QuadraticReciprocityCheckedBody(
                    node_id=_checkpoint_natural(item[0], "node ID"),
                    name=item[1],
                    statement_sha256=item[2],
                    target=decode_formula(item[3]),
                    curried_target=decode_formula(item[4]),
                    certificate=decode_proof(item[5]),
                    proof_nodes=_checkpoint_natural(item[6], "body-node count"),
                    proof_objects=_checkpoint_natural(
                        item[7],
                        "body-object count",
                    ),
                    proof_depth=_checkpoint_natural(item[8], "body depth"),
                    annotation_occurrences=_checkpoint_natural(
                        item[9],
                        "body-annotation count",
                    ),
                    envelope_depth=_checkpoint_natural(
                        item[10],
                        "body-envelope depth",
                    ),
                )
            )
    except QuadraticReciprocityClosureError:
        raise
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        ValueError,
    ) as exc:
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint contains a malformed formula or proof tree"
        ) from exc

    batch = QuadraticReciprocityBodyBatch(
        graph_sha256=decoded[1],
        source_sha256=decoded[2],
        alpha_identity_sha256=decoded[3],
        rows=tuple(rows),
        proof_nodes=proof_nodes,
        proof_objects=proof_objects,
        annotation_occurrences=annotation_occurrences,
    )
    return verify_quadratic_reciprocity_body_batch(
        batch,
        completed_names=completed_names,
        plan=plan,
    )


def write_quadratic_reciprocity_body_checkpoint(
    batch: QuadraticReciprocityBodyBatch,
    directory: str | Path,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> Path:
    """Persist actual bounded proof bytes without overwriting existing data."""

    if not isinstance(directory, (str, Path)):
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint directory must be a filesystem path"
        )
    folder = Path(directory)
    if not folder.is_dir():
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint directory must already exist"
        )
    payload = encode_quadratic_reciprocity_body_batch(
        batch,
        completed_names=completed_names,
        plan=plan,
    )
    path = folder / (
        f"qr-body-{batch.rows[0].node_id:04d}-{batch.rows[-1].node_id:04d}.json"
    )
    try:
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise QuadraticReciprocityClosureError(
            f"cannot create a fresh bounded QR proof checkpoint {path!s}"
        ) from exc
    return path


def load_quadratic_reciprocity_body_checkpoint(
    path: str | Path,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> QuadraticReciprocityBodyBatch:
    """Load actual bounded proof bytes and independently kernel-recheck them."""

    if not isinstance(path, (str, Path)):
        raise QuadraticReciprocityClosureError(
            "QR body checkpoint must be a filesystem path"
        )
    source = Path(path)
    try:
        if source.stat().st_size > MAX_QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_BYTES:
            raise QuadraticReciprocityClosureError(
                "QR body checkpoint exceeds its reviewed 16-MiB transport bound"
            )
        payload = source.read_text(encoding="utf-8")
    except QuadraticReciprocityClosureError:
        raise
    except (OSError, UnicodeError) as exc:
        raise QuadraticReciprocityClosureError(
            f"cannot read bounded QR proof checkpoint {source!s}"
        ) from exc
    batch = decode_quadratic_reciprocity_body_batch(
        payload,
        completed_names=completed_names,
        plan=plan,
    )
    expected_name = (
        f"qr-body-{batch.rows[0].node_id:04d}-{batch.rows[-1].node_id:04d}.json"
    )
    if source.name != expected_name:
        raise QuadraticReciprocityClosureError(
            "QR checkpoint filename disagrees with its checked proof-body indices"
        )
    return batch


def _verified_complete_qr_bodies(
    batches: Sequence[QuadraticReciprocityBodyBatch],
    selected: QuadraticReciprocityClosurePlan,
) -> dict[str, QuadraticReciprocityCheckedBody]:
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise QuadraticReciprocityClosureError(
            "QR closure batches must be an ordered tuple or list"
        )
    supplied_count = 0
    for batch in batches:
        if type(batch) is not QuadraticReciprocityBodyBatch:
            raise QuadraticReciprocityClosureError(
                "QR closure contains a noncanonical proof batch"
            )
        if type(batch.rows) is not tuple:
            raise QuadraticReciprocityClosureError(
                "QR closure contains malformed proof rows"
            )
        supplied_count += len(batch.rows)
    if supplied_count != len(selected.rows):
        raise QuadraticReciprocityClosureError(
            f"QR closure requires all {len(selected.rows)} actual proof bodies; "
            f"received {supplied_count}"
        )

    completed: list[str] = []
    by_name: dict[str, QuadraticReciprocityCheckedBody] = {}
    for batch in batches:
        verify_quadratic_reciprocity_body_batch(
            batch,
            completed_names=completed,
            plan=selected,
        )
        for row in batch.rows:
            if row.name in by_name:
                raise QuadraticReciprocityClosureError(
                    f"QR closure repeats proof body {row.name!r}"
                )
            by_name[row.name] = row
            completed.append(row.name)
    if set(by_name) != {row.name for row in selected.rows}:
        raise QuadraticReciprocityClosureError(
            "QR closure does not cover its exact frozen theorem graph"
        )
    return by_name


def assemble_quadratic_reciprocity_proof_bundle(
    batches: Sequence[QuadraticReciprocityBodyBatch],
    *,
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> QuadraticReciprocityCheckedBundle:
    """Check the complete actual QR graph using the Lean-auditable bundle rule."""

    selected = _sealed_plan(plan)
    by_name = _verified_complete_qr_bodies(batches, selected)
    positions = {row.name: row.node_id for row in selected.rows}
    nodes = tuple(
        BundleNode(
            row.node_id,
            by_name[row.name].target,
            tuple(positions[name] for name in row.dependencies),
            by_name[row.name].certificate,
        )
        for row in selected.rows
    )
    target = _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
    bundle = ProofBundle(nodes, positions[selected.root])
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise QuadraticReciprocityClosureError(
            "the independently checked QR proof bundle failed closed"
        ) from exc
    if (
        receipt.node_count != len(selected.rows)
        or receipt.kernel_calls != len(selected.rows)
        or receipt.dependency_edges != selected.dependency_edge_count
        or receipt.target != target
    ):
        raise QuadraticReciprocityClosureError(
            "the checked QR proof bundle returned inconsistent exact evidence"
        )
    return QuadraticReciprocityCheckedBundle(
        bundle=bundle,
        target=target,
        receipt=receipt,
        graph_sha256=selected.graph_sha256,
        source_sha256=selected.source_sha256,
    )


def export_quadratic_reciprocity_proof_bundle(
    source: str | Path,
    destination: str | Path,
    *,
    plan: QuadraticReciprocityClosurePlan | None = None,
) -> tuple[Path, CheckedProofBundle]:
    """Independently recheck the complete exact graph before durable export."""

    if not isinstance(source, (str, Path)) or not isinstance(
        destination,
        (str, Path),
    ):
        raise QuadraticReciprocityClosureError(
            "QR proof-bundle export paths must be exact filesystem paths"
        )
    selected = _sealed_plan(plan)
    source_path = Path(source)
    destination_path = Path(destination)
    try:
        payload = source_path.read_text(encoding="utf-8")
        bundle, target = decode_proof_bundle(payload)
    except (OSError, ProofBundleError, RecursionError, UnicodeError) as exc:
        raise QuadraticReciprocityClosureError(
            "cannot decode the complete canonical QR source proof bundle"
        ) from exc

    expected_target = _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
    if (
        target != expected_target
        or len(bundle.nodes) != len(selected.rows)
        or bundle.root != len(selected.rows) - 1
    ):
        raise QuadraticReciprocityClosureError(
            "QR proof-bundle export changed its exact root or theorem count"
        )
    positions = {row.name: row.node_id for row in selected.rows}
    for frozen, node in zip(selected.rows, bundle.nodes, strict=True):
        expected, _curried = _body_target(frozen)
        if (
            node.node_id != frozen.node_id
            or node.target != expected
            or node.dependencies
            != tuple(positions[name] for name in frozen.dependencies)
        ):
            raise QuadraticReciprocityClosureError(
                f"QR proof-bundle export changed frozen node {frozen.name!r}"
            )
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise QuadraticReciprocityClosureError(
            "the unchanged kernel rejected the complete QR export graph"
        ) from exc
    if (
        receipt.node_count != len(selected.rows)
        or receipt.kernel_calls != len(selected.rows)
        or receipt.dependency_edges != selected.dependency_edge_count
    ):
        raise QuadraticReciprocityClosureError(
            "QR proof-bundle export changed its exact kernel-check evidence"
        )
    try:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with destination_path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise QuadraticReciprocityClosureError(
            f"cannot create a fresh durable QR proof bundle {destination_path!s}"
        ) from exc
    return destination_path, receipt


def assemble_quadratic_reciprocity_root(
    batches: Sequence[QuadraticReciprocityBodyBatch],
    *,
    plan: QuadraticReciprocityClosurePlan | None = None,
    intern_bodies: bool = True,
) -> QuadraticReciprocityClosedRoot:
    """Accept only a complete actual ordinary unchanged-kernel QR proof."""

    selected = _sealed_plan(plan)
    if type(intern_bodies) is not bool:
        raise QuadraticReciprocityClosureError(
            "QR proof-body interning switch must be an exact boolean"
        )
    by_name = _verified_complete_qr_bodies(batches, selected)

    positions = {row.name: row.node_id for row in selected.rows}
    nodes = tuple(
        LayeredReplayNode(
            row.node_id,
            by_name[row.name].target,
            tuple(positions[name] for name in row.dependencies),
            by_name[row.name].certificate,
        )
        for row in selected.rows
    )
    root_id = positions[selected.root]
    target = _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
    bundle = LayeredReplayBundle(nodes, root_id)
    if intern_bodies:
        interned = intern_layered_replay_bodies(bundle, target)
        if interned is None:
            raise QuadraticReciprocityClosureError(
                "QR proof-body interning rejected the exact bounded graph"
            )
        for node in interned.nodes:
            if not check(
                (),
                node.body,
                by_name[selected.rows[node.node_id].name].curried_target,
            ):
                raise QuadraticReciprocityClosureError(
                    f"the unchanged kernel rejected interned QR body "
                    f"{selected.rows[node.node_id].name!r}"
                )
        bundle = interned

    candidate = compile_layered_replay(
        bundle,
        target,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None:
        raise QuadraticReciprocityClosureError(
            "the genuine layered QR certificate exceeds the unchanged "
            "proof/resource policy or its graph is invalid"
        )
    if not check((), candidate.certificate, target):
        raise QuadraticReciprocityClosureError(
            "the unchanged intuitionistic kernel rejected the full QR root"
        )
    return QuadraticReciprocityClosedRoot(
        certificate=candidate.certificate,
        target=target,
        graph_sha256=selected.graph_sha256,
        source_sha256=selected.source_sha256,
        body_count=len(nodes),
        dependency_edge_count=selected.dependency_edge_count,
        layer_count=len(candidate.layers),
        proof_nodes=candidate.proof_nodes,
        proof_objects=candidate.proof_objects,
        proof_depth=candidate.proof_depth,
        annotation_occurrences=candidate.proof_annotation_occurrences,
        envelope_depth=candidate.proof_envelope_depth,
    )


def _peak_rss_bytes() -> int:
    observed = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return observed if platform.system() == "Darwin" else observed * 1024


def _campaign_cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely checkpoint the genuine 557-node QR proof graph."
    )
    parser.add_argument("--checkpoint-dir", required=True)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--assemble", action="store_true")
    parser.add_argument("--export-bundle")
    parser.add_argument("--max-rss-mib", type=int, default=1536)
    options = parser.parse_args(argv)
    if options.max_batches <= 0 or options.max_rss_mib <= 0:
        parser.error("batch and RSS bounds must be positive")

    selected = quadratic_reciprocity_closure_plan()
    directory = Path(options.checkpoint_dir)
    directory.mkdir(parents=True, exist_ok=True)
    if options.export_bundle and not options.assemble:
        source = directory / "quadratic-reciprocity-proof-bundle-v1.json"
        exported, receipt = export_quadratic_reciprocity_proof_bundle(
            source,
            options.export_bundle,
            plan=selected,
        )
        print(
            json.dumps(
                {
                    "event": "durable_proof_bundle_exported",
                    "source": str(source),
                    "path": str(exported),
                    "sha256": sha256(exported.read_bytes()).hexdigest(),
                    "bytes": exported.stat().st_size,
                    "nodes": receipt.node_count,
                    "edges": receipt.dependency_edges,
                    "kernel_calls": receipt.kernel_calls,
                    "proof_nodes": receipt.total_body_nodes,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return 0
    maximum_rss = options.max_rss_mib * 1024 * 1024
    maximum_batches = len(selected.rows) if options.all else options.max_batches
    completed: list[str] = []
    checkpoint_paths: list[Path] = []
    campaign_started = perf_counter()
    while len(checkpoint_paths) < maximum_batches:
        if _peak_rss_bytes() > maximum_rss:
            raise QuadraticReciprocityClosureError(
                "QR checkpoint campaign exceeded its reviewed peak-RSS guard"
            )
        names = quadratic_reciprocity_next_microbatch(completed, plan=selected)
        if not names:
            break
        first = selected.rows[len(completed)].node_id
        last = selected.rows[len(completed) + len(names) - 1].node_id
        expected = directory / f"qr-body-{first:04d}-{last:04d}.json"
        started = perf_counter()
        if expected.exists():
            batch = load_quadratic_reciprocity_body_checkpoint(
                expected,
                completed_names=completed,
                plan=selected,
            )
            event = "resumed"
        else:
            batch = construct_quadratic_reciprocity_body_batch(
                names,
                completed_names=completed,
                plan=selected,
            )
            written = write_quadratic_reciprocity_body_checkpoint(
                batch,
                directory,
                completed_names=completed,
                plan=selected,
            )
            if written != expected:
                raise QuadraticReciprocityClosureError(
                    "QR body checkpoint changed its deterministic path"
                )
            event = "constructed"
        if batch.names != names:
            raise QuadraticReciprocityClosureError(
                "QR body checkpoint does not match the next sealed frontier"
            )
        completed.extend(batch.names)
        checkpoint_paths.append(expected)
        print(
            json.dumps(
                {
                    "event": event,
                    "batch": len(checkpoint_paths),
                    "completed": len(completed),
                    "rows": len(batch.rows),
                    "proof_nodes": batch.proof_nodes,
                    "proof_objects": batch.proof_objects,
                    "checkpoint_bytes": expected.stat().st_size,
                    "seconds": round(perf_counter() - started, 4),
                    "peak_rss_bytes": _peak_rss_bytes(),
                    "last": batch.rows[-1].name,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        del batch
        gc.collect()

    if not options.assemble:
        return 0
    if len(completed) != len(selected.rows):
        raise QuadraticReciprocityClosureError(
            "QR root assembly requires every checkpoint in the exact graph"
        )

    rehydrated: list[QuadraticReciprocityBodyBatch] = []
    restored: list[str] = []
    for path in checkpoint_paths:
        batch = load_quadratic_reciprocity_body_checkpoint(
            path,
            completed_names=restored,
            plan=selected,
        )
        rehydrated.append(batch)
        restored.extend(batch.names)
        if _peak_rss_bytes() > maximum_rss:
            raise QuadraticReciprocityClosureError(
                "QR checkpoint rehydration exceeded its reviewed peak-RSS guard"
            )

    checked_bundle = assemble_quadratic_reciprocity_proof_bundle(
        rehydrated,
        plan=selected,
    )
    payload = encode_proof_bundle(checked_bundle.bundle, checked_bundle.target)
    bundle_path = directory / "quadratic-reciprocity-proof-bundle-v1.json"
    if bundle_path.exists():
        if bundle_path.read_text(encoding="utf-8") != payload:
            raise QuadraticReciprocityClosureError(
                "existing QR proof bundle differs from the exact checked graph"
            )
    else:
        with bundle_path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    print(
        json.dumps(
            {
                "event": "proof_bundle_kernel_checked",
                "path": str(bundle_path),
                "nodes": checked_bundle.receipt.node_count,
                "edges": checked_bundle.receipt.dependency_edges,
                "kernel_calls": checked_bundle.receipt.kernel_calls,
                "proof_nodes": checked_bundle.receipt.total_body_nodes,
                "bytes": bundle_path.stat().st_size,
                "peak_rss_bytes": _peak_rss_bytes(),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    root = assemble_quadratic_reciprocity_root(rehydrated, plan=selected)
    print(
        json.dumps(
            {
                "event": "ordinary_qr_root_kernel_checked",
                "body_count": root.body_count,
                "edges": root.dependency_edge_count,
                "layers": root.layer_count,
                "proof_nodes": root.proof_nodes,
                "proof_objects": root.proof_objects,
                "proof_depth": root.proof_depth,
                "annotation_occurrences": root.annotation_occurrences,
                "peak_rss_bytes": _peak_rss_bytes(),
                "seconds": round(perf_counter() - campaign_started, 4),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


__all__ = [
    "QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_FORMAT",
    "MAX_QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_BYTES",
    "QuadraticReciprocityClosureError",
    "QuadraticReciprocityClosureRow",
    "QuadraticReciprocityClosurePlan",
    "QuadraticReciprocityCheckedBody",
    "QuadraticReciprocityBodyBatch",
    "QuadraticReciprocityClosedRoot",
    "QuadraticReciprocityCheckedBundle",
    "quadratic_reciprocity_closure_plan",
    "quadratic_reciprocity_next_microbatch",
    "construct_quadratic_reciprocity_body_batch",
    "verify_quadratic_reciprocity_body_batch",
    "encode_quadratic_reciprocity_body_batch",
    "decode_quadratic_reciprocity_body_batch",
    "write_quadratic_reciprocity_body_checkpoint",
    "load_quadratic_reciprocity_body_checkpoint",
    "assemble_quadratic_reciprocity_proof_bundle",
    "export_quadratic_reciprocity_proof_bundle",
    "assemble_quadratic_reciprocity_root",
]


if __name__ == "__main__":
    raise SystemExit(_campaign_cli())
