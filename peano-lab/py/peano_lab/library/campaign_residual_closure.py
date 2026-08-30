"""Close every remaining exact body-only theorem in immutable Alpha v18.

The current constructive release leaves precisely seventeen K3C cell/list
theorems and sixty-seven auxiliary Bertrand theorems outside checked use.
Their joint dependency closure contains 474 enrolled theorem rows.  Actual,
independently checked Bertrand and quadratic-reciprocity proof bundles already
supply 363 exact dependency-curried ordinary bodies; the remaining 111 bodies
are reconstructed and checked by the unchanged intuitionistic kernel.

One historical unary-arithmetic proof, ``pow_two_seven_exact``, contains two
large PA3--PA6 rewrite blocks whose complete annotation envelope exceeds the
unchanged 256-depth proof-bundle limit.  Replacing exactly those frozen blocks
with the existing original-kernel-checked ``norm_num`` tactic produces the
same exact theorem and dependency surface under all existing resource caps.
The immutable enrolled script, kernel, codec and release remain untouched.

The artifact has 474 real theorem nodes and one synthetic balanced
conjunction of the forty maximal residual roots.  The synthetic conjunction
is never enrolled and introduces no axiom, proof constructor, or trusted
external reference.  This module constructs evidence only; release admission
requires a separate explicitly versioned edition.
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
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v16 as v16
from . import editions_v18 as v18
from .bertrand_complete_closure import (
    bertrand_complete_closure_plan,
    checked_bertrand_complete_proof_bundle,
)
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


EXPECTED_RESIDUAL_THEOREM_COUNT = 474
EXPECTED_RESIDUAL_PROMOTION_COUNT = 84
EXPECTED_RESIDUAL_K3C_COUNT = 17
EXPECTED_RESIDUAL_BERTRAND_COUNT = 67
EXPECTED_RESIDUAL_CHECKED_PARENT_COUNT = 390
EXPECTED_RESIDUAL_REUSED_BODY_COUNT = 363
EXPECTED_RESIDUAL_REBUILT_BODY_COUNT = 111
EXPECTED_RESIDUAL_REBUILT_CHECKED_BODY_COUNT = 27
EXPECTED_RESIDUAL_DEPENDENCY_EDGE_COUNT = 1_412
EXPECTED_RESIDUAL_ROOT_COUNT = 40
EXPECTED_RESIDUAL_ROOT_NODE_ID = 474
EXPECTED_RESIDUAL_BUNDLE_NODE_COUNT = 475
EXPECTED_RESIDUAL_BUNDLE_EDGE_COUNT = 1_452
EXPECTED_RESIDUAL_SOURCE_COUNTS = {
    "bertrand": 361,
    "quadratic_reciprocity": 2,
    "rebuild": 111,
}
EXPECTED_RESIDUAL_ORDERED_NAMES_SHA256 = (
    "410ae78fa82fc7a4fc6e2653dbe7cd9668b26cafc1d43ab20b4ba93a3686ca69"
)
EXPECTED_RESIDUAL_PROMOTED_NAMES_SHA256 = (
    "0fd3159925c12b2e7249edb5d536f3be600e466e5a6695350a22c38e81d4f69e"
)
EXPECTED_RESIDUAL_ROOT_NAMES_SHA256 = (
    "303c4d33580900fd294f52a109211e1a43dd3872b2e6d6dbb7c1f02325d83a7d"
)
EXPECTED_RESIDUAL_REBUILT_NAMES_SHA256 = (
    "d6cc4d0df58e4adce37a1e318cf48cc0aa642526955516c485d895d12c576e17"
)
EXPECTED_RESIDUAL_SURFACE_SHA256 = (
    "343566c94dbb8e3c8aaab71655981b03bb59df87aeb737f1708a548e3464e9d5"
)

# Provenance seals bind the canonical independently kernel-checked artifact.
# A digest is never theorem authority: loading rechecks every ordinary body.
EXPECTED_RESIDUAL_BUNDLE_SHA256 = (
    "e69112c5e3b8c21bc452ad35838474f2af2e297152ff73fbdc62bfd935ffdebb"
)
EXPECTED_RESIDUAL_BUNDLE_BYTES = 4_176_537
EXPECTED_RESIDUAL_BUNDLE_BODY_PROOF_NODES = 38_688
PYODIDE_RESIDUAL_BUNDLE_PATH = (
    "/lab/proof-artifacts/alpha-v19-residual-proof-bundle-v1.json"
)


class ResidualClosureError(ValueError):
    """The exact immutable surface, original-kernel proof, or cap failed."""


@dataclass(frozen=True, slots=True)
class ResidualClosureRow:
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
        return self.evidence == v18.EvidenceStatus.BODY_CHECKED.value

    @property
    def requires_rebuilt_body(self) -> bool:
        return self.source == "rebuild"


@dataclass(frozen=True, slots=True)
class ResidualClosurePlan:
    roots: tuple[str, ...]
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[ResidualClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    promoted_names_sha256: str
    rebuilt_names_sha256: str
    root_names_sha256: str
    surface_sha256: str

    @property
    def pending_rows(self) -> tuple[ResidualClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def checked_parent_rows(self) -> tuple[ResidualClosureRow, ...]:
        return tuple(row for row in self.rows if not row.needs_closure)

    @property
    def rebuilt_rows(self) -> tuple[ResidualClosureRow, ...]:
        return tuple(row for row in self.rows if row.requires_rebuilt_body)


@dataclass(frozen=True, slots=True)
class ResidualCheckedBody:
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
class ResidualBodyMicrobatch:
    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[ResidualCheckedBody, ...]
    proof_nodes: int
    proof_objects: int
    annotation_occurrences: int

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(row.name for row in self.rows)


@dataclass(frozen=True, slots=True)
class ResidualCheckedBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


RESIDUAL_PROMOTED_NAMES = tuple(
    item.spec.name for item in v18.ALPHA_ENTRIES if not item.checked_use
)
_RESIDUAL_PROMOTED_SET = frozenset(RESIDUAL_PROMOTED_NAMES)
_RESIDUAL_NONMAXIMAL_SET = frozenset(
    dependency
    for item in v18.ALPHA_ENTRIES
    if item.spec.name in _RESIDUAL_PROMOTED_SET
    for dependency in item.spec.dependencies
    if dependency in _RESIDUAL_PROMOTED_SET
)
RESIDUAL_MAXIMAL_ROOT_NAMES = tuple(
    name for name in RESIDUAL_PROMOTED_NAMES if name not in _RESIDUAL_NONMAXIMAL_SET
)


@lru_cache(maxsize=1)
def residual_closure_plan() -> ResidualClosurePlan:
    """Seal all eighty-four exact Alpha-v18 residual theorem dependencies."""

    if (
        len(RESIDUAL_PROMOTED_NAMES) != EXPECTED_RESIDUAL_PROMOTION_COUNT
        or len(RESIDUAL_MAXIMAL_ROOT_NAMES) != EXPECTED_RESIDUAL_ROOT_COUNT
        or sha256("\n".join(RESIDUAL_PROMOTED_NAMES).encode()).hexdigest()
        != EXPECTED_RESIDUAL_PROMOTED_NAMES_SHA256
        or sha256("\n".join(RESIDUAL_MAXIMAL_ROOT_NAMES).encode()).hexdigest()
        != EXPECTED_RESIDUAL_ROOT_NAMES_SHA256
    ):
        raise ResidualClosureError("the exact Alpha-v18 residual evidence frontier changed")

    table = v18.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = list(reversed(RESIDUAL_PROMOTED_NAMES))
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise ResidualClosureError(f"unknown frozen residual dependency {name!r}")
        if item.evidence is v18.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise ResidualClosureError(
                f"residual theorem {name!r} has no independently checked ordinary body"
            )
        selected.add(name)
        pending.extend(reversed(item.spec.dependencies))

    bertrand_names = frozenset(
        row.name for row in bertrand_complete_closure_plan().rows
    )
    qr_names = frozenset(
        specification.name
        for specification in quadratic_reciprocity_stack().admission_order
    )
    rows: list[ResidualClosureRow] = []
    surfaces: list[dict[str, object]] = []
    seen: set[str] = set()
    for alpha_index, item in enumerate(v18.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        if not set(item.spec.dependencies).issubset(seen):
            raise ResidualClosureError(
                f"non-topological residual theorem {item.spec.name!r}"
            )
        name = item.spec.name
        source = (
            "bertrand"
            if name in bertrand_names
            else "quadratic_reciprocity"
            if name in qr_names
            else "rebuild"
        )
        digest = sha256(item.spec.statement.encode()).hexdigest()
        row = ResidualClosureRow(
            len(rows),
            alpha_index,
            name,
            digest,
            item.spec.dependencies,
            item.evidence.value,
            item.enrollment_origin.value,
            source,
        )
        rows.append(row)
        surfaces.append(
            {
                "alpha_index": alpha_index,
                "name": name,
                "statement_sha256": digest,
                "dependencies": row.dependencies,
                "evidence": row.evidence,
                "enrollment_origin": row.enrollment_origin,
                "source": source,
            }
        )
        seen.add(name)

    if seen != selected:
        raise ResidualClosureError("the residual dependency closure is incomplete")
    promoted = tuple(row for row in rows if row.needs_closure)
    rebuilt = tuple(row for row in rows if row.requires_rebuilt_body)
    ordered_digest = sha256("\n".join(row.name for row in rows).encode()).hexdigest()
    promoted_digest = sha256(
        "\n".join(row.name for row in promoted).encode()
    ).hexdigest()
    rebuilt_digest = sha256("\n".join(row.name for row in rebuilt).encode()).hexdigest()
    roots_digest = sha256("\n".join(RESIDUAL_MAXIMAL_ROOT_NAMES).encode()).hexdigest()
    surface_digest = sha256(
        json.dumps(
            surfaces,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    evidence = Counter(row.evidence for row in rows)
    origins = Counter(row.enrollment_origin for row in promoted)
    edges = sum(len(row.dependencies) for row in rows)
    if (
        len(rows) != EXPECTED_RESIDUAL_THEOREM_COUNT
        or len(promoted) != EXPECTED_RESIDUAL_PROMOTION_COUNT
        or len(rebuilt) != EXPECTED_RESIDUAL_REBUILT_BODY_COUNT
        or sum(not row.needs_closure for row in rebuilt)
        != EXPECTED_RESIDUAL_REBUILT_CHECKED_BODY_COUNT
        or Counter(row.source for row in rows) != EXPECTED_RESIDUAL_SOURCE_COUNTS
        or evidence != {"stable_closed": 189, "alpha_closed": 201, "body_checked": 84}
        or origins.get("k3c") != EXPECTED_RESIDUAL_K3C_COUNT
        or len(promoted) - origins.get("k3c", 0) != EXPECTED_RESIDUAL_BERTRAND_COUNT
        or edges != EXPECTED_RESIDUAL_DEPENDENCY_EDGE_COUNT
        or ordered_digest != EXPECTED_RESIDUAL_ORDERED_NAMES_SHA256
        or promoted_digest != EXPECTED_RESIDUAL_PROMOTED_NAMES_SHA256
        or rebuilt_digest != EXPECTED_RESIDUAL_REBUILT_NAMES_SHA256
        or roots_digest != EXPECTED_RESIDUAL_ROOT_NAMES_SHA256
        or surface_digest != EXPECTED_RESIDUAL_SURFACE_SHA256
    ):
        raise ResidualClosureError("the sealed exact Alpha-v18 residual proof surface changed")
    return ResidualClosurePlan(
        RESIDUAL_MAXIMAL_ROOT_NAMES,
        v18.ALPHA_V18_IDENTITY_SHA256,
        v18.ALPHA_V18_ENROLLMENT_SHA256,
        tuple(rows),
        edges,
        ordered_digest,
        promoted_digest,
        rebuilt_digest,
        roots_digest,
        surface_digest,
    )


def _sealed_plan(plan: ResidualClosurePlan | None) -> ResidualClosurePlan:
    expected = residual_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not ResidualClosurePlan or plan != expected:
        raise ResidualClosureError("residual plan differs from its sealed Alpha-v18 surface")
    return plan


def residual_pending_layers(
    *, plan: ResidualClosurePlan | None = None
) -> tuple[tuple[str, ...], ...]:
    selected = _sealed_plan(plan)
    available = {row.name for row in selected.checked_parent_rows}
    remaining = list(selected.pending_rows)
    result: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name for row in remaining if set(row.dependencies).issubset(available)
        )
        if not ready:
            raise ResidualClosureError("residual body-only dependencies contain a cycle")
        result.append(ready)
        available.update(ready)
        remaining = [row for row in remaining if row.name not in available]
    return tuple(result)


@lru_cache(maxsize=None)
def _frozen_formula(name: str) -> Formula:
    item = v18.ALPHA_EDITION.by_name.get(name)
    if item is None:
        raise ResidualClosureError(f"unknown frozen Alpha-v18 theorem {name!r}")
    return _closed_formula(item.spec.statement)


def _body_target(row: ResidualClosureRow) -> tuple[Formula, Formula]:
    item = v18.ALPHA_ENTRIES[row.alpha_index]
    if (
        item.spec.name != row.name
        or sha256(item.spec.statement.encode()).hexdigest() != row.statement_sha256
    ):
        raise ResidualClosureError(f"residual theorem {row.name!r} changed its exact surface")
    target = _frozen_formula(row.name)
    curried = target
    for dependency in reversed(row.dependencies):
        curried = Imp(_frozen_formula(dependency), curried)
    return target, curried


def _body_metrics(
    certificate: Proof, *, node_budget: int, object_budget: int, label: str
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
        raise ResidualClosureError(
            f"{label} violates an unchanged 125000-node/25000-object/256-depth cap"
        ) from exc


def _residual_body_script(
    name: str, script: tuple[str, ...]
) -> tuple[tuple[str, bool], ...]:
    if name != "pow_two_seven_exact":
        return tuple((command, False) for command in script)
    if len(script) != 243:
        raise ResidualClosureError("the immutable historical power-seven proof script changed")
    allowed = frozenset(("rewrite PA3", "rewrite PA4", "rewrite PA5", "rewrite PA6"))
    normalized: list[tuple[str, bool]] = []
    blocks: list[tuple[int, int]] = []
    position = 0
    while position < len(script):
        if script[position] == "symm":
            end = position + 1
            while end < len(script) and script[end] in allowed:
                end += 1
            if end > position + 1 and end < len(script) and script[end] == "refl":
                blocks.append((position, end))
                normalized.append(("norm_num", True))
                position = end + 1
                continue
        normalized.append((script[position], False))
        position += 1
    if tuple(blocks) != ((31, 101), (108, 242)) or len(normalized) != 39:
        raise ResidualClosureError("the two frozen power-seven arithmetic blocks changed")
    return tuple(normalized)


def _completed_rebuilt_names(
    names: Sequence[str] | frozenset[str], plan: ResidualClosurePlan
) -> set[str]:
    if isinstance(names, str) or not isinstance(names, (tuple, list, frozenset)):
        raise ResidualClosureError("completed residual names must be a tuple, list, or frozenset")
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise ResidualClosureError("completed residual names must be distinct exact strings")
    result = set(names)
    known = {row.name for row in plan.rebuilt_rows}
    if not result.issubset(known):
        raise ResidualClosureError("completed residual rows contain an unknown theorem")
    for row in plan.rebuilt_rows:
        if row.name in result and not set(row.dependencies).intersection(known).issubset(result):
            raise ResidualClosureError("completed residual rows are not dependency closed")
    return result


def construct_residual_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: ResidualClosurePlan | None = None,
) -> ResidualBodyMicrobatch:
    """Construct at most sixteen actual exact, independently checked bodies."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise ResidualClosureError("residual microbatch names must be a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise ResidualClosureError("residual microbatch must contain between one and sixteen rows")
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise ResidualClosureError("residual microbatch names must be distinct exact strings")
    completed = _completed_rebuilt_names(completed_names, selected)
    by_name = {row.name: row for row in selected.rebuilt_rows}
    available = {row.name for row in selected.rows if not row.requires_rebuilt_body} | completed
    previous = -1
    for name in names:
        row = by_name.get(name)
        if row is None or name in completed or row.node_id <= previous:
            raise ResidualClosureError("residual microbatch contains an unknown, repeated, or reordered row")
        if not set(row.dependencies).issubset(available):
            raise ResidualClosureError(f"residual proof {name!r} has unavailable predecessors")
        available.add(name)
        previous = row.node_id

    result: list[ResidualCheckedBody] = []
    nodes = objects = annotations = 0
    for name in names:
        row = by_name[name]
        specification = v18.ALPHA_ENTRIES[row.alpha_index].spec
        target, curried = _body_target(row)
        try:
            state = start(curried)
            for dependency in row.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for position, (command, normalized) in enumerate(
                _residual_body_script(name, specification.script)
            ):
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise ResidualClosureError(
                        f"residual body {name!r} requests implicit theorem authority"
                    )
                if normalized:
                    if tactic != "norm_num" or arguments:
                        raise ResidualClosureError("power-seven normalization changed its exact tactic")
                    state = norm_num(
                        state,
                        limits=replace(DEFAULT_NORM_NUM_LIMITS, max_ast_depth=192),
                    )
                else:
                    state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, curried)
        except ResidualClosureError:
            raise
        except (AttributeError, RecursionError, TypeError, ValueError) as exc:
            raise ResidualClosureError(
                f"actual residual proof {name!r} failed at command {position}"
            ) from exc
        metrics = _body_metrics(
            certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"residual dependency-curried body {name}",
        )
        if not check((), certificate, curried):
            raise ResidualClosureError(
                f"the unchanged intuitionistic kernel rejected residual proof {name!r}"
            )
        proof_nodes, proof_objects, proof_depth, annotation_count, envelope_depth = metrics
        nodes += proof_nodes
        objects += proof_objects
        annotations += annotation_count
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise ResidualClosureError("residual microbatch exceeds its annotation limit")
        result.append(
            ResidualCheckedBody(
                row.node_id,
                row.alpha_index,
                name,
                row.statement_sha256,
                target,
                curried,
                certificate,
                proof_nodes,
                proof_objects,
                proof_depth,
                annotation_count,
                envelope_depth,
            )
        )
    return ResidualBodyMicrobatch(
        selected.parent_alpha_identity_sha256,
        selected.surface_sha256,
        tuple(result),
        nodes,
        objects,
        annotations,
    )


def verify_residual_body_microbatch(
    batch: ResidualBodyMicrobatch,
    *,
    completed_names: Sequence[str] | frozenset[str] = (),
    plan: ResidualClosurePlan | None = None,
) -> ResidualBodyMicrobatch:
    selected = _sealed_plan(plan)
    if (
        type(batch) is not ResidualBodyMicrobatch
        or batch.parent_alpha_identity_sha256 != selected.parent_alpha_identity_sha256
        or batch.surface_sha256 != selected.surface_sha256
        or type(batch.rows) is not tuple
        or not batch.rows
        or len(batch.rows) > MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise ResidualClosureError("residual microbatch changed its frozen identity or size")
    completed = _completed_rebuilt_names(completed_names, selected)
    known = {row.name: row for row in selected.rebuilt_rows}
    available = {row.name for row in selected.rows if not row.requires_rebuilt_body} | completed
    nodes = objects = annotations = 0
    previous = -1
    for actual in batch.rows:
        if type(actual) is not ResidualCheckedBody:
            raise ResidualClosureError("residual microbatch contains a malformed proof row")
        frozen = known.get(actual.name)
        if (
            frozen is None
            or actual.node_id != frozen.node_id
            or actual.alpha_index != frozen.alpha_index
            or actual.statement_sha256 != frozen.statement_sha256
            or actual.node_id <= previous
            or actual.name in available
            or not set(frozen.dependencies).issubset(available)
        ):
            raise ResidualClosureError(f"residual proof {actual.name!r} changed its frozen surface")
        target, curried = _body_target(frozen)
        if actual.target != target or actual.curried_target != curried:
            raise ResidualClosureError(f"residual proof {actual.name!r} changed its exact target")
        metrics = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            label=f"residual dependency-curried body {actual.name}",
        )
        if metrics != (
            actual.proof_nodes,
            actual.proof_objects,
            actual.proof_depth,
            actual.annotation_occurrences,
            actual.envelope_depth,
        ):
            raise ResidualClosureError(f"residual proof {actual.name!r} changed its measured envelope")
        if not check((), actual.certificate, curried):
            raise ResidualClosureError(f"original kernel rejected residual proof {actual.name!r}")
        nodes += actual.proof_nodes
        objects += actual.proof_objects
        annotations += actual.annotation_occurrences
        if annotations > DEFAULT_LAYERED_REPLAY_LIMITS.max_total_body_annotation_occurrences:
            raise ResidualClosureError("residual microbatch exceeds its annotation limit")
        available.add(actual.name)
        previous = actual.node_id
    if (batch.proof_nodes, batch.proof_objects, batch.annotation_occurrences) != (
        nodes,
        objects,
        annotations,
    ):
        raise ResidualClosureError("residual microbatch changed its aggregate envelope")
    return batch


@lru_cache(maxsize=1)
def _checked_parent_bodies() -> dict[str, Proof]:
    """Reuse only actual proof bodies from independently checked artifacts."""

    try:
        bertrand_bundle, _bertrand_receipt = checked_bertrand_complete_proof_bundle()
        qr_bundle, _qr_receipt = v16._checked_qr_bundle()
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise ResidualClosureError("an existing independently checked proof artifact failed") from exc
    bertrand = {
        row.name: node
        for row, node in zip(
            bertrand_complete_closure_plan().rows,
            bertrand_bundle.nodes,
            strict=True,
        )
    }
    qr = {
        specification.name: node
        for specification, node in zip(
            quadratic_reciprocity_stack().admission_order,
            qr_bundle.nodes,
            strict=True,
        )
    }
    plan = residual_closure_plan()
    result: dict[str, Proof] = {}
    for row in plan.rows:
        if row.requires_rebuilt_body:
            continue
        node = bertrand.get(row.name) if row.source == "bertrand" else qr.get(row.name)
        if node is None or node.target != _frozen_formula(row.name):
            raise ResidualClosureError(f"actual parent proof body {row.name!r} is absent or altered")
        result[row.name] = node.body
    if len(result) != EXPECTED_RESIDUAL_REUSED_BODY_COUNT:
        raise ResidualClosureError("existing actual residual proof-body coverage changed")
    return result


def _balanced_formula(formulas: tuple[Formula, ...]) -> Formula:
    if not formulas:
        raise ResidualClosureError("residual conjunction requires actual exact root formulas")
    if len(formulas) == 1:
        return formulas[0]
    middle = len(formulas) // 2
    return And(_balanced_formula(formulas[:middle]), _balanced_formula(formulas[middle:]))


def _balanced_proof(leaves: tuple[Proof, ...]) -> Proof:
    if len(leaves) == 1:
        return leaves[0]
    middle = len(leaves) // 2
    return AndIntro(_balanced_proof(leaves[:middle]), _balanced_proof(leaves[middle:]))


def _synthetic_conjunction_body() -> Proof:
    count = EXPECTED_RESIDUAL_ROOT_COUNT
    proof = _balanced_proof(tuple(Hyp(count - index - 1) for index in range(count)))
    for _ in range(count):
        proof = ImpIntro(proof)
    return proof


def check_residual_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: ResidualClosurePlan | None = None,
) -> ResidualCheckedBundle:
    """Independently kernel-check all 474 exact theorem bodies and 40 roots."""

    selected = _sealed_plan(plan)
    if (
        type(bundle) is not ProofBundle
        or type(bundle.nodes) is not tuple
        or len(bundle.nodes) != EXPECTED_RESIDUAL_BUNDLE_NODE_COUNT
        or bundle.root != EXPECTED_RESIDUAL_ROOT_NODE_ID
    ):
        raise ResidualClosureError("residual proof bundle changed its exact local graph")
    locations = {row.name: row.node_id for row in selected.rows}
    for row, node in zip(selected.rows, bundle.nodes[:-1], strict=True):
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != _frozen_formula(row.name)
            or node.dependencies
            != tuple(locations[dependency] for dependency in row.dependencies)
        ):
            raise ResidualClosureError(f"residual bundle changed frozen theorem {row.name!r}")
    root_ids = tuple(locations[name] for name in selected.roots)
    exact_target = _balanced_formula(tuple(_frozen_formula(name) for name in selected.roots))
    synthetic = bundle.nodes[-1]
    if (
        target != exact_target
        or type(synthetic) is not BundleNode
        or synthetic.node_id != EXPECTED_RESIDUAL_ROOT_NODE_ID
        or synthetic.target != exact_target
        or synthetic.dependencies != root_ids
        or synthetic.body != _synthetic_conjunction_body()
    ):
        raise ResidualClosureError("residual bundle changed its synthetic forty-root conjunction")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise ResidualClosureError(
            "the unchanged intuitionistic kernel rejected the full residual proof graph"
        ) from exc
    if (
        receipt.node_count != EXPECTED_RESIDUAL_BUNDLE_NODE_COUNT
        or receipt.kernel_calls != EXPECTED_RESIDUAL_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_RESIDUAL_BUNDLE_EDGE_COUNT
        or receipt.target != exact_target
        or receipt.total_body_nodes != EXPECTED_RESIDUAL_BUNDLE_BODY_PROOF_NODES
    ):
        raise ResidualClosureError("residual bundle returned inconsistent actual proof diagnostics")
    return ResidualCheckedBundle(bundle, exact_target, receipt, selected.surface_sha256)


def assemble_residual_proof_bundle(
    batches: Sequence[ResidualBodyMicrobatch],
    *,
    plan: ResidualClosurePlan | None = None,
) -> ResidualCheckedBundle:
    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise ResidualClosureError("residual batches must be an ordered tuple or list")
    actual: dict[str, ResidualCheckedBody] = {}
    completed: list[str] = []
    for batch in batches:
        verify_residual_body_microbatch(batch, completed_names=completed, plan=selected)
        for row in batch.rows:
            if row.name in actual:
                raise ResidualClosureError(f"residual proof repeats actual body {row.name!r}")
            actual[row.name] = row
            completed.append(row.name)
    if set(actual) != {row.name for row in selected.rebuilt_rows}:
        raise ResidualClosureError("residual proof requires all 111 independently checked bodies")
    parents = _checked_parent_bodies()
    locations = {row.name: row.node_id for row in selected.rows}
    nodes = tuple(
        BundleNode(
            row.node_id,
            _frozen_formula(row.name),
            tuple(locations[dependency] for dependency in row.dependencies),
            actual[row.name].certificate if row.requires_rebuilt_body else parents[row.name],
        )
        for row in selected.rows
    )
    root_ids = tuple(locations[name] for name in selected.roots)
    target = _balanced_formula(tuple(_frozen_formula(name) for name in selected.roots))
    synthetic = BundleNode(
        EXPECTED_RESIDUAL_ROOT_NODE_ID,
        target,
        root_ids,
        _synthetic_conjunction_body(),
    )
    return check_residual_proof_bundle(
        ProofBundle(nodes + (synthetic,), EXPECTED_RESIDUAL_ROOT_NODE_ID),
        target,
        plan=selected,
    )


_residual_bundle_source: Path | None = None


def _default_residual_bundle_source() -> Path:
    pyodide = Path(PYODIDE_RESIDUAL_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    return (
        location.parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / "alpha-v19-residual-proof-bundle-v1.json"
    )


def set_residual_bundle_source(source: str | Path | None) -> None:
    global _residual_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise ResidualClosureError("residual proof source must be a filesystem path")
    _residual_bundle_source = None if source is None else Path(source)
    _checked_residual_proof_bundle.cache_clear()
    replay_residual_closed_theorem.cache_clear()


@lru_cache(maxsize=1)
def _checked_residual_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _residual_bundle_source or _default_residual_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ResidualClosureError(f"actual residual proof data are unavailable: {source!s}") from exc
    data = payload.encode()
    if (
        not EXPECTED_RESIDUAL_BUNDLE_SHA256
        or len(data) != EXPECTED_RESIDUAL_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_RESIDUAL_BUNDLE_SHA256
    ):
        raise ResidualClosureError("residual artifact differs from its frozen actual-proof provenance")
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise ResidualClosureError("residual artifact is not a canonical constructive proof bundle") from exc
    actual = check_residual_proof_bundle(bundle, target)
    return actual.bundle, actual.receipt


def checked_residual_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Return genuine independently kernel-checked residual proof data."""

    return _checked_residual_proof_bundle()


@lru_cache(maxsize=None)
def replay_residual_closed_theorem(name: str) -> CheckedTheorem:
    """Build and check one exact ordinary residual theorem from the empty context."""

    if type(name) is not str or name not in _RESIDUAL_PROMOTED_SET:
        raise ResidualClosureError("residual replay requires one of the exact 84 pending names")
    selected = residual_closure_plan()
    row = next(item for item in selected.pending_rows if item.name == name)
    bundle, _receipt = checked_residual_proof_bundle()
    required: set[int] = set()
    pending = [row.node_id]
    while pending:
        node_id = pending.pop()
        if node_id in required:
            continue
        required.add(node_id)
        pending.extend(bundle.nodes[node_id].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
            for node in bundle.nodes[:-1]
            if node.node_id in required
        ),
        row.node_id,
    )
    target = _frozen_formula(name)
    try:
        candidate = compile_layered_replay(
            layered, target, limits=DEFAULT_LAYERED_REPLAY_LIMITS
        )
    except (LayeredReplayError, RecursionError, TypeError, ValueError) as exc:
        raise ResidualClosureError(f"cannot construct exact residual theorem proof {name!r}") from exc
    if candidate is None or not check((), candidate.certificate, target):
        raise ResidualClosureError(f"original kernel rejected exact residual theorem {name!r}")
    return CheckedTheorem(
        v18.ALPHA_ENTRIES[row.alpha_index].spec,
        target,
        candidate.certificate,
        candidate.proof_nodes,
    )


def export_residual_proof_bundle(
    destination: str | Path,
    *,
    batch_size: int = 8,
    progress: bool = False,
) -> tuple[Path, ResidualCheckedBundle]:
    """Construct and canonically persist all 474 independently checked rows."""

    if not isinstance(destination, (str, Path)):
        raise ResidualClosureError("residual destination must be a filesystem path")
    if (
        type(batch_size) is not int
        or not 0 < batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise ResidualClosureError("residual batch size must be between one and sixteen")
    selected = residual_closure_plan()
    ordered = tuple(row.name for row in selected.rebuilt_rows)
    completed: list[str] = []
    committed: list[str] = []
    batches: list[ResidualBodyMicrobatch] = []
    waiting: list[ResidualCheckedBody] = []
    waiting_nodes = waiting_objects = waiting_annotations = 0

    def commit_waiting() -> None:
        nonlocal waiting_nodes, waiting_objects, waiting_annotations
        if not waiting:
            return
        batch = ResidualBodyMicrobatch(
            selected.parent_alpha_identity_sha256,
            selected.surface_sha256,
            tuple(waiting),
            waiting_nodes,
            waiting_objects,
            waiting_annotations,
        )
        verify_residual_body_microbatch(batch, completed_names=committed, plan=selected)
        batches.append(batch)
        committed.extend(batch.names)
        waiting.clear()
        waiting_nodes = waiting_objects = waiting_annotations = 0
        if progress:
            print(
                f"checked residual body batch {len(batches)}: "
                f"{len(committed)}/{len(ordered)} actual proofs, "
                f"{batch.proof_nodes} nodes, {batch.proof_objects} objects",
                flush=True,
            )

    for name in ordered:
        singleton = construct_residual_body_microbatch(
            (name,), completed_names=completed, plan=selected
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
    actual = assemble_residual_proof_bundle(tuple(batches), plan=selected)
    payload = encode_proof_bundle(actual.bundle, actual.target)
    decoded, target = decode_proof_bundle(payload)
    check_residual_proof_bundle(decoded, target, plan=selected)
    path = Path(destination)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    except (OSError, UnicodeError) as exc:
        raise ResidualClosureError(f"cannot persist exact residual proof artifact: {path!s}") from exc
    if progress:
        data = payload.encode()
        print(
            f"residual proof bundle: nodes={len(actual.bundle.nodes)} "
            f"edges={actual.receipt.dependency_edges} "
            f"body_nodes={actual.receipt.total_body_nodes} "
            f"bytes={len(data)} sha256={sha256(data).hexdigest()}",
            flush=True,
        )
    return path, actual


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--progress", action="store_true")
    arguments = parser.parse_args(argv)
    export_residual_proof_bundle(
        arguments.export,
        batch_size=arguments.batch_size,
        progress=arguments.progress,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
