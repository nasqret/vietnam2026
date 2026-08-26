"""Complete, independently checked constructive closure of Lucas's theorem.

The exact Alpha-v17 dependency closure of ``lucas_theorem`` contains 213
theorems.  One hundred thirty-nine already have checked-use authority, and
136 of those complete proof bodies occur in the existing quadratic-reciprocity
artifact.  This module independently reconstructs the remaining three checked
Stable/Alpha bodies and all 74 still-body-only theorem bodies, then seals one
self-contained ordinary intuitionistic proof bundle.

Proof construction changes no release authority.  Every batch retains the
unchanged 16-row, 125,000-proof-node, and 25,000-proof-object ceilings; every
body and the exact final target are checked by the unchanged Peano kernel.
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


LUCAS_ROOT_NAME = "lucas_theorem"
LUCAS_CHECKED_OUTSIDE_QR_NAMES = (
    "mul_lt_mul_succ_left_nonzero",
    "beta_factor_divides_product",
    "add_shuffle_middle",
)
EXPECTED_LUCAS_THEOREM_COUNT = 213
EXPECTED_LUCAS_CHECKED_PARENT_COUNT = 139
EXPECTED_LUCAS_QR_BODY_COUNT = 136
EXPECTED_LUCAS_BODY_ONLY_COUNT = 74
EXPECTED_LUCAS_REBUILT_BODY_COUNT = 77
EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT = 617
EXPECTED_LUCAS_ROOT_NODE_ID = 212
EXPECTED_LUCAS_ORDERED_NAMES_SHA256 = (
    "52d9e8ec5eb1942d5a583cd272b7d26aecae5d8e6d4c78a48b6354a541f7af52"
)
EXPECTED_LUCAS_BODY_ONLY_NAMES_SHA256 = (
    "090793ef1fc8e9130bff47bbf42253dad06d05e4d1ddf3e580f6c3196a0f1b71"
)
EXPECTED_LUCAS_REBUILT_NAMES_SHA256 = (
    "db97f67f46ce3f81350061d1a755272237e1d9e23604030beeeeee8332783d52"
)
EXPECTED_LUCAS_SURFACE_SHA256 = (
    "f443f25090da07f3fe4432f7b75b3de5c15512bf4da6d7771524828d9c2d02cd"
)
EXPECTED_LUCAS_ROOT_STATEMENT_SHA256 = (
    "396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564"
)
EXPECTED_LUCAS_BUNDLE_SHA256 = (
    "02b1eef360dce55f0156bda2029e64567b8b83b5d58833d6c4f8695ab8d41832"
)
EXPECTED_LUCAS_BUNDLE_BYTES = 1_103_202
EXPECTED_LUCAS_BUNDLE_BODY_PROOF_NODES = 15_103
PYODIDE_LUCAS_BUNDLE_PATH = "/lab/proof-artifacts/lucas-proof-bundle-v1.json"


class LucasCompleteClosureError(ValueError):
    """A sealed Lucas surface, real proof body, or artifact failed closed."""


@dataclass(frozen=True, slots=True)
class LucasClosureRow:
    """One exact immutable Alpha-v17 theorem row, without new authority."""

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

    @property
    def requires_rebuilt_body(self) -> bool:
        return self.needs_closure or self.name in LUCAS_CHECKED_OUTSIDE_QR_NAMES


@dataclass(frozen=True, slots=True)
class LucasClosurePlan:
    """Complete exact dependency surface; names and hashes are not proofs."""

    root: str
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[LucasClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    body_only_names_sha256: str
    rebuilt_names_sha256: str
    surface_sha256: str

    @property
    def pending_rows(self) -> tuple[LucasClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def checked_parent_rows(self) -> tuple[LucasClosureRow, ...]:
        return tuple(row for row in self.rows if not row.needs_closure)

    @property
    def rebuilt_rows(self) -> tuple[LucasClosureRow, ...]:
        return tuple(row for row in self.rows if row.requires_rebuilt_body)


@dataclass(frozen=True, slots=True)
class LucasCheckedBody:
    """One actual unchanged-kernel proof of the exact curried theorem body."""

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
class LucasBodyMicrobatch:
    """At most 16 actual proofs under unchanged structural/object caps."""

    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[LucasCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class LucasCheckedBundle:
    """One complete self-contained intuitionistic proof graph and receipt."""

    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


@lru_cache(maxsize=1)
def lucas_closure_plan() -> LucasClosurePlan:
    """Seal the exact 213-row Alpha-v17 Lucas closure without proof replay."""

    table = v17.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = [LUCAS_ROOT_NAME]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise LucasCompleteClosureError(
                f"missing exact Alpha-v17 Lucas dependency {name!r}"
            )
        if item.evidence is v17.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise LucasCompleteClosureError(
                f"Lucas dependency {name!r} lacks even a checked proof body"
            )
        selected.add(name)
        pending.extend(reversed(item.spec.dependencies))

    rows: list[LucasClosureRow] = []
    surfaces: list[dict[str, object]] = []
    seen: set[str] = set()
    edges = 0
    for alpha_index, item in enumerate(v17.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        missing = set(item.spec.dependencies).difference(seen)
        if missing:
            raise LucasCompleteClosureError(
                f"non-topological Lucas theorem {item.spec.name!r}: {sorted(missing)!r}"
            )
        statement_digest = sha256(item.spec.statement.encode("utf-8")).hexdigest()
        row = LucasClosureRow(
            node_id=len(rows),
            alpha_index=alpha_index,
            name=item.spec.name,
            statement_sha256=statement_digest,
            dependencies=item.spec.dependencies,
            evidence=item.evidence.value,
            enrollment_origin=item.enrollment_origin.value,
        )
        rows.append(row)
        surfaces.append(
            {
                "alpha_index": alpha_index,
                "name": row.name,
                "statement_sha256": statement_digest,
                "dependencies": row.dependencies,
                "evidence": row.evidence,
                "enrollment_origin": row.enrollment_origin,
            }
        )
        edges += len(row.dependencies)
        seen.add(row.name)
    if len(rows) != len(selected):
        raise LucasCompleteClosureError("Lucas dependency closure is incomplete")

    unclosed = tuple(row for row in rows if row.needs_closure)
    rebuilt = tuple(row for row in rows if row.requires_rebuilt_body)
    names_sha256 = sha256("\n".join(row.name for row in rows).encode()).hexdigest()
    pending_sha256 = sha256("\n".join(row.name for row in unclosed).encode()).hexdigest()
    rebuilt_sha256 = sha256("\n".join(row.name for row in rebuilt).encode()).hexdigest()
    surface_sha256 = sha256(
        json.dumps(
            surfaces,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    if (
        len(rows) != EXPECTED_LUCAS_THEOREM_COUNT
        or len(unclosed) != EXPECTED_LUCAS_BODY_ONLY_COUNT
        or len(rebuilt) != EXPECTED_LUCAS_REBUILT_BODY_COUNT
        or edges != EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT
        or names_sha256 != EXPECTED_LUCAS_ORDERED_NAMES_SHA256
        or pending_sha256 != EXPECTED_LUCAS_BODY_ONLY_NAMES_SHA256
        or rebuilt_sha256 != EXPECTED_LUCAS_REBUILT_NAMES_SHA256
        or surface_sha256 != EXPECTED_LUCAS_SURFACE_SHA256
        or rows[-1].name != LUCAS_ROOT_NAME
        or rows[-1].node_id != EXPECTED_LUCAS_ROOT_NODE_ID
        or rows[-1].statement_sha256 != EXPECTED_LUCAS_ROOT_STATEMENT_SHA256
    ):
        raise LucasCompleteClosureError(
            "the exact frozen Alpha-v17 Lucas theorem/dependency surface changed"
        )
    qr_names = {
        specification.name
        for specification in quadratic_reciprocity_stack().admission_order
    }
    checked_outside = tuple(
        row.name for row in rows if not row.needs_closure and row.name not in qr_names
    )
    if checked_outside != LUCAS_CHECKED_OUTSIDE_QR_NAMES:
        raise LucasCompleteClosureError(
            "the exact three checked Lucas prerequisites outside the QR artifact changed"
        )
    if sum(row.name in qr_names and not row.needs_closure for row in rows) != (
        EXPECTED_LUCAS_QR_BODY_COUNT
    ):
        raise LucasCompleteClosureError("the exact 136 reused QR proof bodies changed")
    return LucasClosurePlan(
        root=LUCAS_ROOT_NAME,
        parent_alpha_identity_sha256=v17.ALPHA_V17_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=v17.ALPHA_V17_ENROLLMENT_SHA256,
        rows=tuple(rows),
        dependency_edge_count=edges,
        ordered_names_sha256=names_sha256,
        body_only_names_sha256=pending_sha256,
        rebuilt_names_sha256=rebuilt_sha256,
        surface_sha256=surface_sha256,
    )


def _sealed_plan(plan: LucasClosurePlan | None) -> LucasClosurePlan:
    expected = lucas_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not LucasClosurePlan or plan != expected:
        raise LucasCompleteClosureError(
            "Lucas plan differs from its exact sealed Alpha-v17 parent"
        )
    return plan


def lucas_pending_layers(*, plan: LucasClosurePlan | None = None) -> tuple[tuple[str, ...], ...]:
    """Return exact dependency-ready body-only waves, without proof authority."""

    selected = _sealed_plan(plan)
    available = {row.name for row in selected.checked_parent_rows}
    remaining = list(selected.pending_rows)
    layers: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name for row in remaining if set(row.dependencies).issubset(available)
        )
        if not ready:
            raise LucasCompleteClosureError("Lucas pending dependency graph is cyclic")
        layers.append(ready)
        available.update(ready)
        remaining = [row for row in remaining if row.name not in available]
    return tuple(layers)


def _completed_rebuilt_names(
    names: Sequence[str] | frozenset[str],
    selected: LucasClosurePlan,
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise LucasCompleteClosureError(
            "completed Lucas reconstruction names must be a tuple, list, or frozenset"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise LucasCompleteClosureError("completed Lucas names must be unique exact strings")
    result = set(names)
    known = {row.name for row in selected.rebuilt_rows}
    unknown = result.difference(known)
    if unknown:
        raise LucasCompleteClosureError(
            f"unknown completed Lucas theorem bodies: {sorted(unknown)!r}"
        )
    for row in selected.rebuilt_rows:
        if row.name in result:
            missing = {
                dependency
                for dependency in row.dependencies
                if dependency in known and dependency not in result
            }
            if missing:
                raise LucasCompleteClosureError(
                    f"completed Lucas bodies are not dependency closed at "
                    f"{row.name!r}: {sorted(missing)!r}"
                )
    return result


def _body_target(row: LucasClosureRow) -> tuple[Formula, Formula]:
    item = v17.ALPHA_ENTRIES[row.alpha_index]
    if (
        item.spec.name != row.name
        or sha256(item.spec.statement.encode()).hexdigest() != row.statement_sha256
    ):
        raise LucasCompleteClosureError(
            f"Lucas row {row.name!r} differs from its exact sealed theorem"
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
        raise LucasCompleteClosureError(
            f"{label} violates the unchanged 125000-node/25000-object envelope"
        ) from exc


def construct_lucas_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: LucasClosurePlan | None = None,
) -> LucasBodyMicrobatch:
    """Independently construct at most sixteen exact original proof bodies."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise LucasCompleteClosureError("Lucas microbatch names must be a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise LucasCompleteClosureError(
            f"Lucas microbatch must contain 1..{MAX_FRONTIER_CLOSURE_MICROBATCH} bodies"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise LucasCompleteClosureError("Lucas microbatch names must be unique exact strings")
    completed = _completed_rebuilt_names(completed_names, selected)
    by_name = {row.name: row for row in selected.rebuilt_rows}
    available = {row.name for row in selected.rows if not row.requires_rebuilt_body} | completed
    previous = -1
    for name in names:
        row = by_name.get(name)
        if row is None:
            raise LucasCompleteClosureError(f"unknown or reused QR Lucas theorem {name!r}")
        if row.node_id <= previous or name in completed:
            raise LucasCompleteClosureError("Lucas microbatch repeats or reorders a row")
        missing = set(row.dependencies).difference(available)
        if missing:
            raise LucasCompleteClosureError(
                f"Lucas theorem body {name!r} lacks predecessors: {sorted(missing)!r}"
            )
        available.add(name)
        previous = row.node_id

    result: list[LucasCheckedBody] = []
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
                    raise LucasCompleteClosureError(
                        f"Lucas body {name!r} requests implicit authority "
                        f"at command {position}"
                    )
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
        except LucasCompleteClosureError:
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
            raise LucasCompleteClosureError(
                f"cannot independently kernel-check Lucas body {name!r}"
            ) from exc
        proof_nodes, proof_objects, depth, proof_annotations, envelope_depth = _body_metrics(
            certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"Lucas dependency-curried body {name}",
        )
        if not check((), certificate, curried):
            raise LucasCompleteClosureError(
                f"unchanged intuitionistic kernel rejected Lucas body {name!r}"
            )
        nodes += proof_nodes
        objects += proof_objects
        annotations += proof_annotations
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise LucasCompleteClosureError("Lucas microbatch exceeds its annotation limit")
        result.append(
            LucasCheckedBody(
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
    return LucasBodyMicrobatch(
        parent_alpha_identity_sha256=selected.parent_alpha_identity_sha256,
        surface_sha256=selected.surface_sha256,
        rows=tuple(result),
        proof_nodes=nodes,
        proof_objects=objects,
        annotation_occurrences=annotations,
    )


def verify_lucas_body_microbatch(
    batch: LucasBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: LucasClosurePlan | None = None,
) -> LucasBodyMicrobatch:
    """Recheck every exact ordinary proof; diagnostics are never authority."""

    selected = _sealed_plan(plan)
    if type(batch) is not LucasBodyMicrobatch:
        raise LucasCompleteClosureError("Lucas microbatch has an invalid exact type")
    if (
        batch.parent_alpha_identity_sha256 != selected.parent_alpha_identity_sha256
        or batch.surface_sha256 != selected.surface_sha256
    ):
        raise LucasCompleteClosureError("Lucas microbatch changed its frozen parent")
    if type(batch.rows) is not tuple or not 0 < len(batch.rows) <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise LucasCompleteClosureError("Lucas microbatch exceeds its sixteen-row policy")
    completed = _completed_rebuilt_names(completed_names, selected)
    available = {row.name for row in selected.rows if not row.requires_rebuilt_body} | completed
    by_name = {row.name: row for row in selected.rebuilt_rows}
    previous = -1
    nodes = objects = annotations = 0
    for actual in batch.rows:
        if type(actual) is not LucasCheckedBody:
            raise LucasCompleteClosureError("Lucas microbatch contains an invalid proof row")
        frozen = by_name.get(actual.name)
        if (
            frozen is None
            or actual.node_id != frozen.node_id
            or actual.alpha_index != frozen.alpha_index
            or actual.statement_sha256 != frozen.statement_sha256
        ):
            raise LucasCompleteClosureError(
                f"Lucas proof {actual.name!r} changed its exact frozen theorem surface"
            )
        if actual.node_id <= previous or actual.name in available:
            raise LucasCompleteClosureError("Lucas microbatch repeats or reorders a proof")
        missing = set(frozen.dependencies).difference(available)
        if missing:
            raise LucasCompleteClosureError(
                f"Lucas proof {actual.name!r} lacks predecessors: {sorted(missing)!r}"
            )
        target, curried = _body_target(frozen)
        if actual.target != target or actual.curried_target != curried:
            raise LucasCompleteClosureError(
                f"Lucas proof {actual.name!r} changed its exact curried target"
            )
        measured = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"Lucas dependency-curried body {actual.name}",
        )
        if measured != (
            actual.proof_nodes,
            actual.proof_objects,
            actual.proof_depth,
            actual.annotation_occurrences,
            actual.envelope_depth,
        ):
            raise LucasCompleteClosureError(
                f"Lucas proof {actual.name!r} changed its measured envelope"
            )
        if not check((), actual.certificate, curried):
            raise LucasCompleteClosureError(
                f"unchanged intuitionistic kernel rejected Lucas proof {actual.name!r}"
            )
        nodes += actual.proof_nodes
        objects += actual.proof_objects
        annotations += actual.annotation_occurrences
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise LucasCompleteClosureError("Lucas microbatch exceeds its annotation limit")
        available.add(actual.name)
        previous = actual.node_id
    if (batch.proof_nodes, batch.proof_objects, batch.annotation_occurrences) != (
        nodes,
        objects,
        annotations,
    ):
        raise LucasCompleteClosureError("Lucas microbatch changed its aggregate proof envelope")
    return batch


def check_lucas_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: LucasClosurePlan | None = None,
) -> LucasCheckedBundle:
    """Independently check all 213 exact theorem bodies and the Lucas root."""

    selected = _sealed_plan(plan)
    if type(bundle) is not ProofBundle:
        raise LucasCompleteClosureError("Lucas evidence must be an actual proof bundle")
    if (
        type(bundle.nodes) is not tuple
        or len(bundle.nodes) != EXPECTED_LUCAS_THEOREM_COUNT
        or bundle.root != EXPECTED_LUCAS_ROOT_NODE_ID
    ):
        raise LucasCompleteClosureError("Lucas bundle changed its exact node count or root")
    positions = {row.name: row.node_id for row in selected.rows}
    for row, node in zip(selected.rows, bundle.nodes, strict=True):
        expected, _curried = _body_target(row)
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != expected
            or node.dependencies
            != tuple(positions[dependency] for dependency in row.dependencies)
        ):
            raise LucasCompleteClosureError(
                f"Lucas bundle changed exact frozen theorem {row.name!r}"
            )
    root = _closed_formula(v17.ALPHA_EDITION.by_name[LUCAS_ROOT_NAME].spec.statement)
    if target != root or bundle.nodes[-1].target != root:
        raise LucasCompleteClosureError("Lucas bundle changed the exact original theorem root")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise LucasCompleteClosureError(
            "the unchanged intuitionistic kernel rejected the complete Lucas proof graph"
        ) from exc
    if (
        receipt.node_count != EXPECTED_LUCAS_THEOREM_COUNT
        or receipt.kernel_calls != EXPECTED_LUCAS_THEOREM_COUNT
        or receipt.dependency_edges != EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT
        or receipt.target != root
    ):
        raise LucasCompleteClosureError("Lucas bundle returned inconsistent proof evidence")
    return LucasCheckedBundle(bundle, root, receipt, selected.surface_sha256)


def assemble_lucas_proof_bundle(
    batches: Sequence[LucasBodyMicrobatch],
    *,
    plan: LucasClosurePlan | None = None,
) -> LucasCheckedBundle:
    """Combine 136 genuine QR proofs and 77 freshly checked exact bodies."""

    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise LucasCompleteClosureError("Lucas proof batches must be an ordered tuple or list")
    actual: dict[str, LucasCheckedBody] = {}
    completed: list[str] = []
    for batch in batches:
        verify_lucas_body_microbatch(batch, completed_names=completed, plan=selected)
        for row in batch.rows:
            if row.name in actual:
                raise LucasCompleteClosureError(f"Lucas proof repeats theorem {row.name!r}")
            actual[row.name] = row
            completed.append(row.name)
    required = {row.name for row in selected.rebuilt_rows}
    if set(actual) != required:
        raise LucasCompleteClosureError(
            f"Lucas proof requires exactly {len(required)} actual reconstructed "
            f"bodies; received {len(actual)}"
        )
    try:
        qr_bundle, _receipt = v16._checked_qr_bundle()
    except (v16.EditionV16Error, ProofBundleError, TypeError, ValueError) as exc:
        raise LucasCompleteClosureError(
            "the independently checked quadratic-reciprocity proof artifact is unavailable"
        ) from exc
    qr_nodes = {
        specification.name: node
        for specification, node in zip(
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
            if row.requires_rebuilt_body
            else qr_nodes[row.name].body,
        )
        for row in selected.rows
    )
    target = nodes[-1].target
    return check_lucas_proof_bundle(
        ProofBundle(nodes, EXPECTED_LUCAS_ROOT_NODE_ID),
        target,
        plan=selected,
    )


_lucas_bundle_source: Path | None = None


def _default_lucas_bundle_source() -> Path:
    pyodide = Path(PYODIDE_LUCAS_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    if len(location.parents) > 4:
        return (
            location.parents[4]
            / "research"
            / "arithmetic-library"
            / "artifacts"
            / "lucas-proof-bundle-v1.json"
        )
    return pyodide


def set_lucas_bundle_source(source: str | Path | None) -> None:
    """Changing actual proof bytes invalidates every previously checked cache."""

    global _lucas_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise LucasCompleteClosureError("Lucas proof source must be a filesystem path")
    _lucas_bundle_source = None if source is None else Path(source)
    _checked_lucas_bundle.cache_clear()
    replay_lucas_closed_theorem.cache_clear()


@lru_cache(maxsize=1)
def _checked_lucas_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _lucas_bundle_source or _default_lucas_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise LucasCompleteClosureError(
            f"actual complete Lucas proof data are unavailable: {source!s}"
        ) from exc
    data = payload.encode("utf-8")
    if (
        len(data) != EXPECTED_LUCAS_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_LUCAS_BUNDLE_SHA256
    ):
        raise LucasCompleteClosureError(
            "Lucas artifact differs from its frozen independently checked proof provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise LucasCompleteClosureError(
            "Lucas artifact is not a canonical complete constructive proof bundle"
        ) from exc
    actual = check_lucas_proof_bundle(bundle, target)
    if actual.receipt.total_body_nodes != EXPECTED_LUCAS_BUNDLE_BODY_PROOF_NODES:
        raise LucasCompleteClosureError("Lucas proof bundle changed its actual body metrics")
    return actual.bundle, actual.receipt


def checked_lucas_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Return genuine independently checked complete proof data only."""

    return _checked_lucas_bundle()


@lru_cache(maxsize=None)
def replay_lucas_closed_theorem(name: str = LUCAS_ROOT_NAME) -> CheckedTheorem:
    """Build and check an ordinary empty-context proof without release promotion."""

    if type(name) is not str:
        raise LucasCompleteClosureError("Lucas replay name must be an exact string")
    selected = lucas_closure_plan()
    row = next((item for item in selected.pending_rows if item.name == name), None)
    if row is None:
        raise LucasCompleteClosureError(
            f"theorem {name!r} is outside the exact 74-row Lucas body-only slice"
        )
    bundle, _receipt = _checked_lucas_bundle()
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
            for node in bundle.nodes
            if node.node_id in required
        ),
        row.node_id,
    )
    item = v17.ALPHA_ENTRIES[row.alpha_index]
    formula = _closed_formula(item.spec.statement)
    try:
        candidate = compile_layered_replay(
            layered,
            formula,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
    except (LayeredReplayError, RecursionError, TypeError, ValueError) as exc:
        raise LucasCompleteClosureError(
            f"cannot compile the ordinary complete Lucas theorem proof {name!r}"
        ) from exc
    if candidate is None:
        raise LucasCompleteClosureError(
            f"Lucas theorem {name!r} exceeds the unchanged layered proof resource policy"
        )
    if not check((), candidate.certificate, formula):
        raise LucasCompleteClosureError(
            f"the unchanged intuitionistic kernel rejected Lucas theorem {name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


def export_lucas_proof_bundle(
    destination: str | Path,
    *,
    batch_size: int = MAX_FRONTIER_CLOSURE_MICROBATCH,
    progress: bool = False,
) -> tuple[Path, LucasCheckedBundle]:
    """Construct and durably export all exact independently checked bodies."""

    if not isinstance(destination, (str, Path)):
        raise LucasCompleteClosureError("Lucas export destination must be a filesystem path")
    if (
        type(batch_size) is not int
        or batch_size <= 0
        or batch_size > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise LucasCompleteClosureError("Lucas proof batch size must be between 1 and 16")
    selected = lucas_closure_plan()
    ordered = tuple(row.name for row in selected.rebuilt_rows)
    completed: list[str] = []
    batches: list[LucasBodyMicrobatch] = []
    for start_index in range(0, len(ordered), batch_size):
        names = ordered[start_index : start_index + batch_size]
        batch = construct_lucas_body_microbatch(
            names,
            completed_names=completed,
            plan=selected,
        )
        verify_lucas_body_microbatch(
            batch,
            completed_names=completed,
            plan=selected,
        )
        batches.append(batch)
        completed.extend(batch.names)
        if progress:
            print(
                f"checked Lucas body batch {len(batches)}: "
                f"{len(completed)}/{len(ordered)} actual proofs, "
                f"{batch.proof_nodes} nodes, {batch.proof_objects} objects",
                flush=True,
            )
    actual = assemble_lucas_proof_bundle(tuple(batches), plan=selected)
    payload = encode_proof_bundle(actual.bundle, actual.target)
    canonical, target = decode_proof_bundle(payload)
    check_lucas_proof_bundle(canonical, target, plan=selected)
    destination_path = Path(destination)
    try:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with destination_path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise LucasCompleteClosureError(
            f"cannot create fresh Lucas proof artifact {destination_path!s}"
        ) from exc
    return destination_path, actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--batch-size", type=int, default=MAX_FRONTIER_CLOSURE_MICROBATCH)
    arguments = parser.parse_args(argv)
    destination, actual = export_lucas_proof_bundle(
        arguments.destination,
        batch_size=arguments.batch_size,
        progress=True,
    )
    payload = destination.read_bytes()
    print(
        f"wrote complete Lucas proof: {destination}, bytes={len(payload)}, "
        f"sha256={sha256(payload).hexdigest()}, theorem-nodes={actual.receipt.node_count}, "
        f"edges={actual.receipt.dependency_edges}, body-nodes={actual.receipt.total_body_nodes}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "EXPECTED_LUCAS_BODY_ONLY_COUNT",
    "EXPECTED_LUCAS_BODY_ONLY_NAMES_SHA256",
    "EXPECTED_LUCAS_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_LUCAS_BUNDLE_BYTES",
    "EXPECTED_LUCAS_BUNDLE_SHA256",
    "EXPECTED_LUCAS_CHECKED_PARENT_COUNT",
    "EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_LUCAS_ORDERED_NAMES_SHA256",
    "EXPECTED_LUCAS_QR_BODY_COUNT",
    "EXPECTED_LUCAS_REBUILT_BODY_COUNT",
    "EXPECTED_LUCAS_REBUILT_NAMES_SHA256",
    "EXPECTED_LUCAS_ROOT_NODE_ID",
    "EXPECTED_LUCAS_ROOT_STATEMENT_SHA256",
    "EXPECTED_LUCAS_SURFACE_SHA256",
    "EXPECTED_LUCAS_THEOREM_COUNT",
    "LUCAS_CHECKED_OUTSIDE_QR_NAMES",
    "LUCAS_ROOT_NAME",
    "LucasBodyMicrobatch",
    "LucasCheckedBody",
    "LucasCheckedBundle",
    "LucasClosurePlan",
    "LucasClosureRow",
    "LucasCompleteClosureError",
    "PYODIDE_LUCAS_BUNDLE_PATH",
    "assemble_lucas_proof_bundle",
    "check_lucas_proof_bundle",
    "checked_lucas_proof_bundle",
    "construct_lucas_body_microbatch",
    "export_lucas_proof_bundle",
    "lucas_closure_plan",
    "lucas_pending_layers",
    "replay_lucas_closed_theorem",
    "set_lucas_bundle_source",
    "verify_lucas_body_microbatch",
]
