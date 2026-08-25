"""Complete, self-contained constructive proof of Bertrand's postulate.

The exact immutable Alpha-v17 theorem ``bertrand_strict`` has a 544-node,
1,917-edge dependency closure.  Independently checked quadratic-reciprocity,
supplementary-law, Lucas, and Kummer artifacts already supply 283 complete
ordinary theorem proof bodies.  This module reconstructs the remaining 261
exact original bodies under the unchanged 16-row/125,000-node/25,000-object
microbatch caps and checks the resulting complete intuitionistic proof graph.

Planning, experimental proof construction, and this canonical artifact never
change Alpha/Stable authority or add a kernel rule, axiom, or proof oracle.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from ..engine.norm_num import DEFAULT_NORM_NUM_LIMITS
from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final, norm_num
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
from .kummer_complete_closure import (
    kummer_complete_closure_plan,
    load_kummer_proof_bundle,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayError,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
)
from .lucas_complete_closure import checked_lucas_proof_bundle, lucas_closure_plan
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
    checked_supplementary_proof_bundle,
    supplementary_laws_closure_plan,
)
from .theorems import CheckedTheorem, _closed_formula, _primitive


BERTRAND_ROOT_NAME = "bertrand_strict"
EXPECTED_BERTRAND_THEOREM_COUNT = 544
EXPECTED_BERTRAND_CHECKED_PARENT_COUNT = 214
EXPECTED_BERTRAND_BODY_ONLY_COUNT = 330
EXPECTED_BERTRAND_REUSED_BODY_COUNT = 283
EXPECTED_BERTRAND_REBUILT_BODY_COUNT = 261
EXPECTED_BERTRAND_REBUILT_CHECKED_BODY_COUNT = 20
EXPECTED_BERTRAND_REBUILT_BODY_ONLY_COUNT = 241
EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT = 1_917
EXPECTED_BERTRAND_ROOT_NODE_ID = 543
EXPECTED_BERTRAND_SOURCE_COUNTS = {
    "quadratic_reciprocity": 183,
    "supplementary": 3,
    "lucas": 33,
    "kummer": 64,
    "rebuild": 261,
}
EXPECTED_BERTRAND_ORDERED_NAMES_SHA256 = (
    "d0e90fb101f10684d792d9ba8a32ba2abc78a033bf18ea4c958f14a68cdd469e"
)
EXPECTED_BERTRAND_BODY_ONLY_NAMES_SHA256 = (
    "0fdc5b1d67fa127a50a523fff29a1341c7d50d42419a9466b7feeba306ba25b9"
)
EXPECTED_BERTRAND_REBUILT_NAMES_SHA256 = (
    "577788bc90686ce0e0874544f1b2110aba2f74b1241a94d796fcd8cea4209021"
)
EXPECTED_BERTRAND_SURFACE_SHA256 = (
    "f20a8e327e48ca29550639c021abb78771627aae181d9946d336a6ae210030e2"
)
EXPECTED_BERTRAND_ROOT_STATEMENT_SHA256 = (
    "6c55889276eb7ad2577191ad7b7e46cae45a6c1437a0275db44801b54ee7ad39"
)
EXPECTED_BERTRAND_BUNDLE_SHA256 = (
    "84078d40d2df7b072938975191fb70c95731059ced716a12050df4376e2d4883"
)
EXPECTED_BERTRAND_BUNDLE_BYTES = 14_368_763
EXPECTED_BERTRAND_BUNDLE_BODY_PROOF_NODES = 187_725
PYODIDE_BERTRAND_BUNDLE_PATH = "/lab/proof-artifacts/bertrand-proof-bundle-v1.json"


class BertrandCompleteClosureError(ValueError):
    """The frozen Bertrand proof surface, actual proof, or resource cap failed."""


@dataclass(frozen=True, slots=True)
class BertrandClosureRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    evidence: str
    enrollment_origin: str
    source: str

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v17.EvidenceStatus.BODY_CHECKED.value

    @property
    def requires_rebuilt_body(self) -> bool:
        return self.source == "rebuild"


@dataclass(frozen=True, slots=True)
class BertrandClosurePlan:
    root: str
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[BertrandClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    body_only_names_sha256: str
    rebuilt_names_sha256: str
    surface_sha256: str

    @property
    def pending_rows(self) -> tuple[BertrandClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def checked_parent_rows(self) -> tuple[BertrandClosureRow, ...]:
        return tuple(row for row in self.rows if not row.needs_closure)

    @property
    def rebuilt_rows(self) -> tuple[BertrandClosureRow, ...]:
        return tuple(row for row in self.rows if row.requires_rebuilt_body)


@dataclass(frozen=True, slots=True)
class BertrandCheckedBody:
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
class BertrandBodyMicrobatch:
    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[BertrandCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class BertrandCheckedBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


def _artifact_source_names() -> tuple[tuple[str, frozenset[str]], ...]:
    return (
        (
            "quadratic_reciprocity",
            frozenset(
                specification.name
                for specification in quadratic_reciprocity_stack().admission_order
            ),
        ),
        (
            "supplementary",
            frozenset(row.name for row in supplementary_laws_closure_plan().rows),
        ),
        ("lucas", frozenset(row.name for row in lucas_closure_plan().rows)),
        (
            "kummer",
            frozenset(row.name for row in kummer_complete_closure_plan().rows),
        ),
    )


@lru_cache(maxsize=1)
def bertrand_complete_closure_plan() -> BertrandClosurePlan:
    """Seal the exact 544-node Alpha-v17 Bertrand theorem/dependency surface."""

    table = v17.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = [BERTRAND_ROOT_NAME]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise BertrandCompleteClosureError(
                f"missing exact Alpha-v17 Bertrand dependency {name!r}"
            )
        if item.evidence is v17.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise BertrandCompleteClosureError(
                f"Bertrand dependency {name!r} lacks a checked ordinary proof body"
            )
        selected.add(name)
        pending.extend(reversed(item.spec.dependencies))

    sources = _artifact_source_names()
    rows: list[BertrandClosureRow] = []
    surfaces: list[dict[str, object]] = []
    seen: set[str] = set()
    edges = 0
    for alpha_index, item in enumerate(v17.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        missing = set(item.spec.dependencies).difference(seen)
        if missing:
            raise BertrandCompleteClosureError(
                f"non-topological Bertrand theorem {item.spec.name!r}: {sorted(missing)!r}"
            )
        source = next(
            (label for label, names in sources if item.spec.name in names),
            "rebuild",
        )
        digest = sha256(item.spec.statement.encode()).hexdigest()
        row = BertrandClosureRow(
            node_id=len(rows),
            alpha_index=alpha_index,
            name=item.spec.name,
            statement_sha256=digest,
            dependencies=item.spec.dependencies,
            evidence=item.evidence.value,
            enrollment_origin=item.enrollment_origin.value,
            source=source,
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
                "source": row.source,
            }
        )
        edges += len(row.dependencies)
        seen.add(row.name)
    if len(rows) != len(selected):
        raise BertrandCompleteClosureError("Bertrand dependency closure is incomplete")

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
        len(rows) != EXPECTED_BERTRAND_THEOREM_COUNT
        or len(unclosed) != EXPECTED_BERTRAND_BODY_ONLY_COUNT
        or len(rebuilt) != EXPECTED_BERTRAND_REBUILT_BODY_COUNT
        or sum(not row.needs_closure for row in rebuilt)
        != EXPECTED_BERTRAND_REBUILT_CHECKED_BODY_COUNT
        or edges != EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT
        or Counter(row.source for row in rows) != EXPECTED_BERTRAND_SOURCE_COUNTS
        or names_sha256 != EXPECTED_BERTRAND_ORDERED_NAMES_SHA256
        or pending_sha256 != EXPECTED_BERTRAND_BODY_ONLY_NAMES_SHA256
        or rebuilt_sha256 != EXPECTED_BERTRAND_REBUILT_NAMES_SHA256
        or surface_sha256 != EXPECTED_BERTRAND_SURFACE_SHA256
        or rows[-1].name != BERTRAND_ROOT_NAME
        or rows[-1].node_id != EXPECTED_BERTRAND_ROOT_NODE_ID
        or rows[-1].statement_sha256 != EXPECTED_BERTRAND_ROOT_STATEMENT_SHA256
    ):
        raise BertrandCompleteClosureError(
            "the exact frozen Alpha-v17 Bertrand theorem/proof-source surface changed"
        )
    return BertrandClosurePlan(
        root=BERTRAND_ROOT_NAME,
        parent_alpha_identity_sha256=v17.ALPHA_V17_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=v17.ALPHA_V17_ENROLLMENT_SHA256,
        rows=tuple(rows),
        dependency_edge_count=edges,
        ordered_names_sha256=names_sha256,
        body_only_names_sha256=pending_sha256,
        rebuilt_names_sha256=rebuilt_sha256,
        surface_sha256=surface_sha256,
    )


def _sealed_plan(plan: BertrandClosurePlan | None) -> BertrandClosurePlan:
    expected = bertrand_complete_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not BertrandClosurePlan or plan != expected:
        raise BertrandCompleteClosureError(
            "Bertrand plan differs from its exact sealed Alpha-v17 dependency surface"
        )
    return plan


def bertrand_pending_layers(*, plan: BertrandClosurePlan | None = None) -> tuple[tuple[str, ...], ...]:
    selected = _sealed_plan(plan)
    available = {row.name for row in selected.checked_parent_rows}
    remaining = list(selected.pending_rows)
    layers: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name for row in remaining if set(row.dependencies).issubset(available)
        )
        if not ready:
            raise BertrandCompleteClosureError("Bertrand pending dependency graph is cyclic")
        layers.append(ready)
        available.update(ready)
        remaining = [row for row in remaining if row.name not in available]
    return tuple(layers)


def _completed_rebuilt_names(
    names: Sequence[str] | frozenset[str],
    selected: BertrandClosurePlan,
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise BertrandCompleteClosureError(
            "completed Bertrand names must be a tuple, list, or frozenset"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise BertrandCompleteClosureError("completed Bertrand names must be unique strings")
    result = set(names)
    known = {row.name for row in selected.rebuilt_rows}
    unknown = result.difference(known)
    if unknown:
        raise BertrandCompleteClosureError(
            f"unknown completed Bertrand theorem bodies: {sorted(unknown)!r}"
        )
    for row in selected.rebuilt_rows:
        if row.name in result:
            missing = {
                dependency
                for dependency in row.dependencies
                if dependency in known and dependency not in result
            }
            if missing:
                raise BertrandCompleteClosureError(
                    f"completed Bertrand bodies are not dependency closed at "
                    f"{row.name!r}: {sorted(missing)!r}"
                )
    return result


def _body_target(row: BertrandClosureRow) -> tuple[Formula, Formula]:
    item = v17.ALPHA_ENTRIES[row.alpha_index]
    if (
        item.spec.name != row.name
        or sha256(item.spec.statement.encode()).hexdigest() != row.statement_sha256
    ):
        raise BertrandCompleteClosureError(
            f"Bertrand row {row.name!r} differs from its exact frozen theorem"
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
        raise BertrandCompleteClosureError(
            f"{label} violates the unchanged 125000-node/25000-object envelope"
        ) from exc


def _bertrand_body_script(
    name: str,
    script: tuple[str, ...],
) -> tuple[tuple[str, bool], ...]:
    """Return an actual checked-body script without changing immutable enrollment.

    The historical power seed expands ``32 * 2`` and ``64 * 2`` into two
    exceptionally long PA3--PA6 rewrite chains inside an already-large power
    formula.  Although its original proof checks, its annotation envelope has
    depth 270 and consequently cannot pass the unchanged 256-depth canonical
    bundle decoder.  Replace exactly those two frozen blocks with the existing
    independently kernel-checked ``norm_num`` tactic.  Its authoring-only AST
    depth allowance is raised just enough to inspect the already-enrolled
    unary numeral 128; the original ledger script, exact formula, dependency
    list, intuitionistic kernel, codec, proof envelope, and batch caps are
    untouched.  Every resulting candidate is independently kernel-checked.
    """

    if name != "pow_two_seed_bundle_from_total":
        return tuple((command, False) for command in script)
    if len(script) != 266:
        raise BertrandCompleteClosureError(
            "the frozen historical Bertrand power-seed script changed"
        )
    expected_blocks = ((49, 119), (128, 262))
    allowed_rewrites = frozenset(
        ("rewrite PA3", "rewrite PA4", "rewrite PA5", "rewrite PA6")
    )
    normalized: list[tuple[str, bool]] = []
    found_blocks: list[tuple[int, int]] = []
    position = 0
    while position < len(script):
        command = script[position]
        if command == "symm":
            end = position + 1
            while end < len(script) and script[end] in allowed_rewrites:
                end += 1
            if end > position + 1 and end < len(script) and script[end] == "refl":
                found_blocks.append((position, end))
                normalized.append(("norm_num", True))
                position = end + 1
                continue
        normalized.append((command, False))
        position += 1
    if tuple(found_blocks) != expected_blocks or len(normalized) != 62:
        raise BertrandCompleteClosureError(
            "the frozen Bertrand power-seed arithmetic rewrite blocks changed"
        )
    return tuple(normalized)


def construct_bertrand_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: BertrandClosurePlan | None = None,
) -> BertrandBodyMicrobatch:
    """Construct at most sixteen proofs of the exact original curried targets.

    The one frozen power-seed body receives the documented proof-only
    arithmetic normalization; its original immutable enrollment is unchanged.
    """

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise BertrandCompleteClosureError("Bertrand microbatch names must be a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise BertrandCompleteClosureError(
            f"Bertrand microbatch must contain 1..{MAX_FRONTIER_CLOSURE_MICROBATCH} bodies"
        )
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise BertrandCompleteClosureError("Bertrand microbatch names must be unique exact strings")
    completed = _completed_rebuilt_names(completed_names, selected)
    by_name = {row.name: row for row in selected.rebuilt_rows}
    available = {row.name for row in selected.rows if not row.requires_rebuilt_body} | completed
    previous = -1
    for name in names:
        row = by_name.get(name)
        if row is None:
            raise BertrandCompleteClosureError(f"unknown or reused Bertrand theorem {name!r}")
        if row.node_id <= previous or name in completed:
            raise BertrandCompleteClosureError("Bertrand microbatch repeats or reorders a row")
        missing = set(row.dependencies).difference(available)
        if missing:
            raise BertrandCompleteClosureError(
                f"Bertrand theorem body {name!r} lacks predecessors: {sorted(missing)!r}"
            )
        available.add(name)
        previous = row.node_id

    actual: list[BertrandCheckedBody] = []
    nodes = objects = annotations = 0
    for name in names:
        row = by_name[name]
        specification = v17.ALPHA_ENTRIES[row.alpha_index].spec
        target, curried = _body_target(row)
        try:
            state = start(curried)
            for dependency in specification.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for position, (command, normalized) in enumerate(
                _bertrand_body_script(name, specification.script)
            ):
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise BertrandCompleteClosureError(
                        f"Bertrand body {name!r} requests implicit authority "
                        f"at command {position}"
                    )
                if normalized:
                    if tactic != "norm_num" or arguments:
                        raise BertrandCompleteClosureError(
                            "Bertrand power-seed normalization changed its tactic"
                        )
                    state = norm_num(
                        state,
                        limits=replace(DEFAULT_NORM_NUM_LIMITS, max_ast_depth=192),
                    )
                else:
                    state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
        except BertrandCompleteClosureError:
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
            raise BertrandCompleteClosureError(
                f"cannot independently kernel-check Bertrand body {name!r}"
            ) from exc
        proof_nodes, proof_objects, depth, proof_annotations, envelope_depth = _body_metrics(
            certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"Bertrand dependency-curried body {name}",
        )
        if not check((), certificate, curried):
            raise BertrandCompleteClosureError(
                f"unchanged intuitionistic kernel rejected Bertrand body {name!r}"
            )
        nodes += proof_nodes
        objects += proof_objects
        annotations += proof_annotations
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise BertrandCompleteClosureError("Bertrand microbatch exceeds its annotation cap")
        actual.append(
            BertrandCheckedBody(
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
                proof_annotations,
                envelope_depth,
            )
        )
    return BertrandBodyMicrobatch(
        selected.parent_alpha_identity_sha256,
        selected.surface_sha256,
        tuple(actual),
        nodes,
        objects,
        annotations,
    )


def verify_bertrand_body_microbatch(
    batch: BertrandBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: BertrandClosurePlan | None = None,
) -> BertrandBodyMicrobatch:
    """Recheck exact proof bodies and all frozen parent/resource constraints."""

    selected = _sealed_plan(plan)
    if type(batch) is not BertrandBodyMicrobatch:
        raise BertrandCompleteClosureError("Bertrand microbatch has an invalid exact type")
    if (
        batch.parent_alpha_identity_sha256 != selected.parent_alpha_identity_sha256
        or batch.surface_sha256 != selected.surface_sha256
    ):
        raise BertrandCompleteClosureError("Bertrand microbatch changed its frozen parent")
    if type(batch.rows) is not tuple or not 0 < len(batch.rows) <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise BertrandCompleteClosureError("Bertrand microbatch exceeds its sixteen-row policy")
    completed = _completed_rebuilt_names(completed_names, selected)
    available = {row.name for row in selected.rows if not row.requires_rebuilt_body} | completed
    by_name = {row.name: row for row in selected.rebuilt_rows}
    previous = -1
    nodes = objects = annotations = 0
    for actual in batch.rows:
        if type(actual) is not BertrandCheckedBody:
            raise BertrandCompleteClosureError("Bertrand microbatch contains an invalid proof")
        frozen = by_name.get(actual.name)
        if (
            frozen is None
            or actual.node_id != frozen.node_id
            or actual.alpha_index != frozen.alpha_index
            or actual.statement_sha256 != frozen.statement_sha256
        ):
            raise BertrandCompleteClosureError(
                f"Bertrand proof {actual.name!r} changed its frozen exact theorem"
            )
        if actual.node_id <= previous or actual.name in available:
            raise BertrandCompleteClosureError("Bertrand microbatch repeats or reorders a proof")
        missing = set(frozen.dependencies).difference(available)
        if missing:
            raise BertrandCompleteClosureError(
                f"Bertrand proof {actual.name!r} lacks predecessors: {sorted(missing)!r}"
            )
        target, curried = _body_target(frozen)
        if actual.target != target or actual.curried_target != curried:
            raise BertrandCompleteClosureError(
                f"Bertrand proof {actual.name!r} changed its exact curried target"
            )
        metrics = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"Bertrand dependency-curried body {actual.name}",
        )
        if metrics != (
            actual.proof_nodes,
            actual.proof_objects,
            actual.proof_depth,
            actual.annotation_occurrences,
            actual.envelope_depth,
        ):
            raise BertrandCompleteClosureError(
                f"Bertrand proof {actual.name!r} changed its measured envelope"
            )
        if not check((), actual.certificate, curried):
            raise BertrandCompleteClosureError(
                f"unchanged intuitionistic kernel rejected Bertrand proof {actual.name!r}"
            )
        nodes += actual.proof_nodes
        objects += actual.proof_objects
        annotations += actual.annotation_occurrences
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise BertrandCompleteClosureError("Bertrand microbatch exceeds its annotation cap")
        available.add(actual.name)
        previous = actual.node_id
    if (batch.proof_nodes, batch.proof_objects, batch.annotation_occurrences) != (
        nodes,
        objects,
        annotations,
    ):
        raise BertrandCompleteClosureError("Bertrand microbatch changed its proof envelope")
    return batch


def _repository_artifact(name: str) -> Path:
    location = Path(__file__).resolve()
    return location.parents[4] / "research" / "arithmetic-library" / "artifacts" / name


def _checked_parent_body_table() -> dict[str, dict[str, BundleNode]]:
    """Independently check every source artifact before reusing its proofs."""

    qr_bundle, _qr_receipt = v16._checked_qr_bundle()
    supplementary_bundle, _supplementary_receipt = checked_supplementary_proof_bundle()
    lucas_bundle, _lucas_receipt = checked_lucas_proof_bundle()
    kummer = load_kummer_proof_bundle(
        _repository_artifact("kummer-proof-bundle-v1.json")
    )
    return {
        "quadratic_reciprocity": {
            specification.name: node
            for specification, node in zip(
                quadratic_reciprocity_stack().admission_order,
                qr_bundle.nodes,
                strict=True,
            )
        },
        "supplementary": {
            row.name: supplementary_bundle.nodes[row.node_id]
            for row in supplementary_laws_closure_plan().rows
        },
        "lucas": {
            row.name: lucas_bundle.nodes[row.node_id]
            for row in lucas_closure_plan().rows
        },
        "kummer": {
            row.name: kummer.bundle.nodes[row.node_id]
            for row in kummer_complete_closure_plan().rows
        },
    }


def check_bertrand_complete_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: BertrandClosurePlan | None = None,
) -> BertrandCheckedBundle:
    """Independently kernel-check all 544 exact constructive theorem bodies."""

    selected = _sealed_plan(plan)
    if type(bundle) is not ProofBundle:
        raise BertrandCompleteClosureError("Bertrand evidence must be an actual proof bundle")
    if (
        type(bundle.nodes) is not tuple
        or len(bundle.nodes) != EXPECTED_BERTRAND_THEOREM_COUNT
        or bundle.root != EXPECTED_BERTRAND_ROOT_NODE_ID
    ):
        raise BertrandCompleteClosureError("Bertrand bundle changed its exact node count/root")
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
            raise BertrandCompleteClosureError(
                f"Bertrand bundle changed exact frozen theorem {row.name!r}"
            )
    root = _closed_formula(v17.ALPHA_EDITION.by_name[BERTRAND_ROOT_NAME].spec.statement)
    if target != root or bundle.nodes[-1].target != root:
        raise BertrandCompleteClosureError("Bertrand bundle changed the exact original root")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise BertrandCompleteClosureError(
            "the unchanged intuitionistic kernel rejected the complete Bertrand proof graph"
        ) from exc
    if (
        receipt.node_count != EXPECTED_BERTRAND_THEOREM_COUNT
        or receipt.kernel_calls != EXPECTED_BERTRAND_THEOREM_COUNT
        or receipt.dependency_edges != EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT
        or receipt.target != root
    ):
        raise BertrandCompleteClosureError("Bertrand bundle returned inconsistent proof evidence")
    return BertrandCheckedBundle(bundle, root, receipt, selected.surface_sha256)


def assemble_bertrand_complete_proof_bundle(
    batches: Sequence[BertrandBodyMicrobatch],
    *,
    plan: BertrandClosurePlan | None = None,
) -> BertrandCheckedBundle:
    """Combine 283 independently checked source nodes and 261 rebuilt bodies."""

    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise BertrandCompleteClosureError("Bertrand batches must be an ordered tuple or list")
    actual: dict[str, BertrandCheckedBody] = {}
    completed: list[str] = []
    for batch in batches:
        verify_bertrand_body_microbatch(batch, completed_names=completed, plan=selected)
        for row in batch.rows:
            if row.name in actual:
                raise BertrandCompleteClosureError(
                    f"Bertrand proof repeats theorem body {row.name!r}"
                )
            actual[row.name] = row
            completed.append(row.name)
    required = {row.name for row in selected.rebuilt_rows}
    if set(actual) != required:
        raise BertrandCompleteClosureError(
            f"Bertrand proof requires exactly {len(required)} reconstructed "
            f"bodies; received {len(actual)}"
        )
    proven = _checked_parent_body_table()
    positions = {row.name: row.node_id for row in selected.rows}
    nodes = tuple(
        BundleNode(
            row.node_id,
            _body_target(row)[0],
            tuple(positions[dependency] for dependency in row.dependencies),
            actual[row.name].certificate
            if row.requires_rebuilt_body
            else proven[row.source][row.name].body,
        )
        for row in selected.rows
    )
    return check_bertrand_complete_proof_bundle(
        ProofBundle(nodes, EXPECTED_BERTRAND_ROOT_NODE_ID),
        nodes[-1].target,
        plan=selected,
    )


_bertrand_bundle_source: Path | None = None


def _default_bertrand_bundle_source() -> Path:
    pyodide = Path(PYODIDE_BERTRAND_BUNDLE_PATH)
    return (
        pyodide
        if pyodide.is_file()
        else _repository_artifact("bertrand-proof-bundle-v1.json")
    )


def set_bertrand_bundle_source(source: str | Path | None) -> None:
    """Changing genuine proof data invalidates all prior proof replay caches."""

    global _bertrand_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise BertrandCompleteClosureError("Bertrand proof source must be a filesystem path")
    _bertrand_bundle_source = None if source is None else Path(source)
    _checked_bertrand_complete_bundle.cache_clear()
    replay_bertrand_closed_theorem.cache_clear()


@lru_cache(maxsize=1)
def _checked_bertrand_complete_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _bertrand_bundle_source or _default_bertrand_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BertrandCompleteClosureError(
            f"actual complete Bertrand proof data are unavailable: {source!s}"
        ) from exc
    data = payload.encode()
    if (
        len(data) != EXPECTED_BERTRAND_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_BERTRAND_BUNDLE_SHA256
    ):
        raise BertrandCompleteClosureError(
            "Bertrand artifact differs from its frozen independently checked proof provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise BertrandCompleteClosureError(
            "Bertrand artifact is not a canonical complete constructive proof bundle"
        ) from exc
    actual = check_bertrand_complete_proof_bundle(bundle, target)
    if actual.receipt.total_body_nodes != EXPECTED_BERTRAND_BUNDLE_BODY_PROOF_NODES:
        raise BertrandCompleteClosureError("Bertrand proof bundle changed its body metrics")
    return actual.bundle, actual.receipt


def checked_bertrand_complete_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Return genuine independently checked complete proof data only."""

    return _checked_bertrand_complete_bundle()


def checked_bertrand_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Compatibility name for genuine independently checked proof data."""

    return _checked_bertrand_complete_bundle()


@lru_cache(maxsize=None)
def replay_bertrand_closed_theorem(name: str = BERTRAND_ROOT_NAME) -> CheckedTheorem:
    """Build/check one ordinary exact theorem if existing replay caps allow it."""

    if type(name) is not str:
        raise BertrandCompleteClosureError("Bertrand replay name must be an exact string")
    selected = bertrand_complete_closure_plan()
    row = next((item for item in selected.pending_rows if item.name == name), None)
    if row is None:
        raise BertrandCompleteClosureError(
            f"theorem {name!r} is outside the exact 330-row Bertrand body-only slice"
        )
    bundle, _receipt = _checked_bertrand_complete_bundle()
    required: set[int] = set()
    pending = [row.node_id]
    while pending:
        node_id = pending.pop()
        if node_id not in required:
            required.add(node_id)
            pending.extend(bundle.nodes[node_id].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
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
        raise BertrandCompleteClosureError(
            f"cannot compile the ordinary complete Bertrand theorem proof {name!r}"
        ) from exc
    if candidate is None:
        raise BertrandCompleteClosureError(
            f"Bertrand theorem {name!r} exceeds the unchanged layered proof policy"
        )
    if not check((), candidate.certificate, formula):
        raise BertrandCompleteClosureError(
            f"the unchanged intuitionistic kernel rejected Bertrand theorem {name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


def export_bertrand_complete_proof_bundle(
    destination: str | Path,
    *,
    batch_size: int = 8,
    progress: bool = False,
) -> tuple[Path, BertrandCheckedBundle]:
    """Independently construct and canonically persist the full Bertrand proof."""

    if not isinstance(destination, (str, Path)):
        raise BertrandCompleteClosureError("Bertrand destination must be a filesystem path")
    if (
        type(batch_size) is not int
        or batch_size <= 0
        or batch_size > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise BertrandCompleteClosureError("Bertrand batch size must be between 1 and 16")
    selected = bertrand_complete_closure_plan()
    ordered = tuple(row.name for row in selected.rebuilt_rows)
    completed: list[str] = []
    committed: list[str] = []
    batches: list[BertrandBodyMicrobatch] = []
    waiting: list[BertrandCheckedBody] = []
    waiting_nodes = waiting_objects = waiting_annotations = 0

    def commit_waiting() -> None:
        nonlocal waiting_nodes, waiting_objects, waiting_annotations
        if not waiting:
            return
        batch = BertrandBodyMicrobatch(
            selected.parent_alpha_identity_sha256,
            selected.surface_sha256,
            tuple(waiting),
            waiting_nodes,
            waiting_objects,
            waiting_annotations,
        )
        verify_bertrand_body_microbatch(batch, completed_names=committed, plan=selected)
        batches.append(batch)
        committed.extend(batch.names)
        waiting.clear()
        waiting_nodes = waiting_objects = waiting_annotations = 0
        if progress:
            print(
                f"checked Bertrand body batch {len(batches)}: "
                f"{len(committed)}/{len(ordered)} actual proofs, "
                f"{batch.proof_nodes} nodes, {batch.proof_objects} objects",
                flush=True,
            )

    for name in ordered:
        # Construct each exact body just once under the unchanged singleton
        # envelope, then greedily combine adjacent bodies into the largest
        # permitted microbatch.  Historical H/J arithmetic rows can consume
        # most of the 25,000-object cap individually, so fixed eight-row
        # windows are neither safe nor necessary.
        singleton = construct_bertrand_body_microbatch(
            (name,),
            completed_names=completed,
            plan=selected,
        )
        row = singleton.rows[0]
        if waiting and (
            len(waiting) == batch_size
            or waiting_nodes + row.proof_nodes
            > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
            or waiting_objects + row.proof_objects
            > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
            or waiting_annotations + row.annotation_occurrences
            > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences
        ):
            commit_waiting()
        waiting.append(row)
        waiting_nodes += row.proof_nodes
        waiting_objects += row.proof_objects
        waiting_annotations += row.annotation_occurrences
        completed.append(name)
        if len(waiting) == batch_size:
            commit_waiting()
    commit_waiting()
    actual = assemble_bertrand_complete_proof_bundle(tuple(batches), plan=selected)
    payload = encode_proof_bundle(actual.bundle, actual.target)
    decoded, target = decode_proof_bundle(payload)
    check_bertrand_complete_proof_bundle(decoded, target, plan=selected)
    path = Path(destination)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except OSError as exc:
        raise BertrandCompleteClosureError(
            f"cannot create a fresh Bertrand proof artifact {path!s}"
        ) from exc
    return path, actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    arguments = parser.parse_args(argv)
    path, actual = export_bertrand_complete_proof_bundle(
        arguments.destination,
        batch_size=arguments.batch_size,
        progress=True,
    )
    data = path.read_bytes()
    print(
        f"wrote complete Bertrand proof: {path}, bytes={len(data)}, "
        f"sha256={sha256(data).hexdigest()}, theorem-nodes={actual.receipt.node_count}, "
        f"edges={actual.receipt.dependency_edges}, body-nodes={actual.receipt.total_body_nodes}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BERTRAND_ROOT_NAME",
    "EXPECTED_BERTRAND_BODY_ONLY_COUNT",
    "EXPECTED_BERTRAND_BODY_ONLY_NAMES_SHA256",
    "EXPECTED_BERTRAND_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_BERTRAND_BUNDLE_BYTES",
    "EXPECTED_BERTRAND_BUNDLE_SHA256",
    "EXPECTED_BERTRAND_CHECKED_PARENT_COUNT",
    "EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_BERTRAND_ORDERED_NAMES_SHA256",
    "EXPECTED_BERTRAND_REBUILT_BODY_COUNT",
    "EXPECTED_BERTRAND_REBUILT_BODY_ONLY_COUNT",
    "EXPECTED_BERTRAND_REBUILT_CHECKED_BODY_COUNT",
    "EXPECTED_BERTRAND_REBUILT_NAMES_SHA256",
    "EXPECTED_BERTRAND_REUSED_BODY_COUNT",
    "EXPECTED_BERTRAND_ROOT_NODE_ID",
    "EXPECTED_BERTRAND_ROOT_STATEMENT_SHA256",
    "EXPECTED_BERTRAND_SOURCE_COUNTS",
    "EXPECTED_BERTRAND_SURFACE_SHA256",
    "EXPECTED_BERTRAND_THEOREM_COUNT",
    "BertrandBodyMicrobatch",
    "BertrandCheckedBody",
    "BertrandCheckedBundle",
    "BertrandClosurePlan",
    "BertrandClosureRow",
    "BertrandCompleteClosureError",
    "PYODIDE_BERTRAND_BUNDLE_PATH",
    "assemble_bertrand_complete_proof_bundle",
    "bertrand_complete_closure_plan",
    "bertrand_pending_layers",
    "check_bertrand_complete_proof_bundle",
    "checked_bertrand_complete_proof_bundle",
    "checked_bertrand_proof_bundle",
    "construct_bertrand_body_microbatch",
    "export_bertrand_complete_proof_bundle",
    "replay_bertrand_closed_theorem",
    "set_bertrand_bundle_source",
    "verify_bertrand_body_microbatch",
]
