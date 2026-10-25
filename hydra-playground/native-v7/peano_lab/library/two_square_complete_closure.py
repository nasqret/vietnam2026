"""Bounded complete constructive closure of the all-natural two-square theorem.

The immutable Alpha-v17 root has 517 exact theorem dependencies. Its 356
quadratic-reciprocity proof bodies are reused only after independent checking;
the other 161 bodies, including 140 currently body-only entries, are rebuilt
from their exact original scripts. Each reconstruction batch obeys the
unchanged 16-body, 125,000-node, and 25,000-object caps.

No planning result, receipt, hash, candidate, or proof bundle changes Stable
membership or grants release-authorized Alpha checked use.
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


TWO_SQUARE_ROOT_NAME = (
    "two_square_iff_zero_or_even_three_mod_four_prime_valuations"
)
EXPECTED_TWO_SQUARE_THEOREM_COUNT = 517
EXPECTED_TWO_SQUARE_CHECKED_PARENT_COUNT = 377
EXPECTED_TWO_SQUARE_QR_BODY_COUNT = 356
EXPECTED_TWO_SQUARE_BODY_ONLY_COUNT = 140
EXPECTED_TWO_SQUARE_REBUILT_BODY_COUNT = 161
EXPECTED_TWO_SQUARE_DEPENDENCY_EDGE_COUNT = 1_599
EXPECTED_TWO_SQUARE_ROOT_NODE_ID = 516
EXPECTED_TWO_SQUARE_ORDERED_NAMES_SHA256 = (
    "c9582d8b019af46768a50395147fbc43b5e4d399b67d648412cddc3f5d067673"
)
EXPECTED_TWO_SQUARE_BODY_ONLY_NAMES_SHA256 = (
    "50496cda1be2f866a3b50de72022daabda44135534e05e66fd811d44c9a10ec3"
)
EXPECTED_TWO_SQUARE_REBUILT_NAMES_SHA256 = (
    "477ac38cd80f9851c76dd1d8f7eb0d5b487410924c90718be835e33fe9df5983"
)
EXPECTED_TWO_SQUARE_SURFACE_SHA256 = (
    "d65032309c5fe029b54f58e9677cb550921613d42375cceab92edcb6e6e05b23"
)
EXPECTED_TWO_SQUARE_ROOT_STATEMENT_SHA256 = (
    "4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5"
)
EXPECTED_TWO_SQUARE_BUNDLE_SHA256 = (
    "f2e77dc6e8c87c715bf2c4f3325e999e7180a2c3ab0fa93f3e9a5006d3e1684e"
)
EXPECTED_TWO_SQUARE_BUNDLE_BYTES = 1_868_714
EXPECTED_TWO_SQUARE_BUNDLE_BODY_PROOF_NODES = 33_546
PYODIDE_TWO_SQUARE_BUNDLE_PATH = "/lab/proof-artifacts/two-square-proof-bundle-v1.json"


class TwoSquareCompleteClosureError(ValueError):
    """An exact surface, actual proof body, artifact, or resource cap failed."""


@dataclass(frozen=True, slots=True)
class TwoSquareClosureRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    evidence: str
    enrollment_origin: str
    needs_rebuild: bool

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v17.EvidenceStatus.BODY_CHECKED.value


@dataclass(frozen=True, slots=True)
class TwoSquareClosurePlan:
    root: str
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[TwoSquareClosureRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    body_only_names_sha256: str
    rebuilt_names_sha256: str
    surface_sha256: str

    @property
    def pending_rows(self) -> tuple[TwoSquareClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def rebuilt_rows(self) -> tuple[TwoSquareClosureRow, ...]:
        return tuple(row for row in self.rows if row.needs_rebuild)


@dataclass(frozen=True, slots=True)
class TwoSquareCheckedBody:
    node_id: int
    name: str
    statement_sha256: str
    target: Formula
    curried_target: Formula
    certificate: Proof
    proof_nodes: int
    proof_objects: int


@dataclass(frozen=True, slots=True)
class TwoSquareBodyMicrobatch:
    parent_alpha_identity_sha256: str
    surface_sha256: str
    rows: tuple[TwoSquareCheckedBody, ...]
    proof_nodes: int
    proof_objects: int


@dataclass(frozen=True, slots=True)
class TwoSquareCheckedBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    surface_sha256: str


def _ordered_digest(names: Sequence[str]) -> str:
    return sha256("\n".join(names).encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def two_square_closure_plan() -> TwoSquareClosurePlan:
    """Seal the complete exact v17 dependency surface without checking proofs."""

    table = v17.ALPHA_EDITION.by_name
    selected: set[str] = set()
    pending = [TWO_SQUARE_ROOT_NAME]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise TwoSquareCompleteClosureError(f"unknown two-square dependency {name!r}")
        if item.evidence is v17.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise TwoSquareCompleteClosureError(f"two-square body {name!r} is not checked")
        selected.add(name)
        pending.extend(item.spec.dependencies)

    qr_names = {spec.name for spec in quadratic_reciprocity_stack().admission_order}
    rows: list[TwoSquareClosureRow] = []
    surfaces: list[dict[str, object]] = []
    seen: set[str] = set()
    edges = 0
    for alpha_index, item in enumerate(v17.ALPHA_ENTRIES):
        if item.spec.name not in selected:
            continue
        if not set(item.spec.dependencies) <= seen:
            raise TwoSquareCompleteClosureError(
                f"two-square dependency order changed for {item.spec.name!r}"
            )
        digest = sha256(item.spec.statement.encode("utf-8")).hexdigest()
        row = TwoSquareClosureRow(
            len(rows),
            alpha_index,
            item.spec.name,
            digest,
            item.spec.dependencies,
            item.evidence.value,
            item.enrollment_origin.value,
            item.spec.name not in qr_names,
        )
        if not row.needs_rebuild and not item.checked_use:
            raise TwoSquareCompleteClosureError(
                f"unchecked two-square dependency {item.spec.name!r} entered QR cache"
            )
        rows.append(row)
        surfaces.append(
            {
                "alpha_index": alpha_index,
                "name": item.spec.name,
                "statement_sha256": digest,
                "dependencies": item.spec.dependencies,
                "evidence": item.evidence.value,
                "enrollment_origin": item.enrollment_origin.value,
            }
        )
        edges += len(item.spec.dependencies)
        seen.add(item.spec.name)

    result = TwoSquareClosurePlan(
        TWO_SQUARE_ROOT_NAME,
        v17.ALPHA_V17_IDENTITY_SHA256,
        v17.ALPHA_V17_ENROLLMENT_SHA256,
        tuple(rows),
        edges,
        _ordered_digest(tuple(row.name for row in rows)),
        _ordered_digest(tuple(row.name for row in rows if row.needs_closure)),
        _ordered_digest(tuple(row.name for row in rows if row.needs_rebuild)),
        sha256(
            json.dumps(surfaces, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            .encode("utf-8")
        ).hexdigest(),
    )
    if (
        len(result.rows) != EXPECTED_TWO_SQUARE_THEOREM_COUNT
        or len(result.pending_rows) != EXPECTED_TWO_SQUARE_BODY_ONLY_COUNT
        or len(result.rebuilt_rows) != EXPECTED_TWO_SQUARE_REBUILT_BODY_COUNT
        or result.dependency_edge_count != EXPECTED_TWO_SQUARE_DEPENDENCY_EDGE_COUNT
        or result.ordered_names_sha256 != EXPECTED_TWO_SQUARE_ORDERED_NAMES_SHA256
        or result.body_only_names_sha256 != EXPECTED_TWO_SQUARE_BODY_ONLY_NAMES_SHA256
        or result.rebuilt_names_sha256 != EXPECTED_TWO_SQUARE_REBUILT_NAMES_SHA256
        or result.surface_sha256 != EXPECTED_TWO_SQUARE_SURFACE_SHA256
        or result.rows[-1].name != TWO_SQUARE_ROOT_NAME
        or result.rows[-1].statement_sha256 != EXPECTED_TWO_SQUARE_ROOT_STATEMENT_SHA256
    ):
        raise TwoSquareCompleteClosureError("immutable complete two-square dependency surface changed")
    return result


def _sealed_plan(plan: TwoSquareClosurePlan | None) -> TwoSquareClosurePlan:
    expected = two_square_closure_plan()
    if plan is None:
        return expected
    if type(plan) is not TwoSquareClosurePlan or plan != expected:
        raise TwoSquareCompleteClosureError("two-square closure plan does not match its sealed parent")
    return expected


def _targets(row: TwoSquareClosureRow) -> tuple[Formula, Formula]:
    exact = v17.ALPHA_ENTRIES[row.alpha_index].spec
    if exact.name != row.name or sha256(exact.statement.encode()).hexdigest() != row.statement_sha256:
        raise TwoSquareCompleteClosureError(f"two-square theorem {row.name!r} changed")
    target = _closed_formula(exact.statement)
    curried = target
    for name in reversed(exact.dependencies):
        curried = Imp(_closed_formula(v17.ALPHA_EDITION.by_name[name].spec.statement), curried)
    return target, curried


def _body_metrics(proof: Proof, *, node_budget: int, object_budget: int) -> tuple[int, int]:
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        nodes, objects, _depth, _annotations, _envelope = _proof_envelope_metrics_bounded(
            proof,
            max_proof_occurrences=node_budget,
            max_proof_objects=object_budget,
            max_proof_depth=limits.max_body_depth,
            max_annotation_occurrences=limits.max_body_annotation_occurrences,
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_body_envelope_depth,
            label="two-square exact dependency-curried body",
        )
    except (AttributeError, LayeredReplayError, RecursionError, TypeError, ValueError) as error:
        raise TwoSquareCompleteClosureError(
            "two-square body exceeds the unchanged 125000-node/25000-object caps"
        ) from error
    return nodes, objects


def construct_two_square_body_microbatch(
    names: Sequence[str],
    *,
    completed_names: Sequence[str] = (),
    plan: TwoSquareClosurePlan | None = None,
) -> TwoSquareBodyMicrobatch:
    """Reconstruct actual proof bodies from immutable exact tactic scripts."""

    selected = _sealed_plan(plan)
    if isinstance(names, (str, bytes)) or not isinstance(names, (tuple, list)):
        raise TwoSquareCompleteClosureError("two-square microbatch names must form a tuple or list")
    if not names or len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise TwoSquareCompleteClosureError("two-square microbatch must contain 1..16 bodies")
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise TwoSquareCompleteClosureError("two-square microbatch names must be unique exact strings")
    by_name = {row.name: row for row in selected.rebuilt_rows}
    completed = set(completed_names)
    if len(completed) != len(completed_names) or not completed <= set(by_name):
        raise TwoSquareCompleteClosureError("two-square completed rows must be distinct sealed names")
    available = {row.name for row in selected.rows if not row.needs_rebuild} | completed
    previous = -1
    for name in names:
        row = by_name.get(name)
        if row is None or row.node_id <= previous or name in available:
            raise TwoSquareCompleteClosureError("two-square microbatch repeats, reorders, or invents a body")
        missing = set(row.dependencies).difference(available)
        if missing:
            raise TwoSquareCompleteClosureError(
                f"two-square proof {name!r} lacks exact predecessor bodies: {sorted(missing)!r}"
            )
        available.add(name)
        previous = row.node_id

    rows: list[TwoSquareCheckedBody] = []
    nodes = objects = 0
    for name in names:
        row = by_name[name]
        spec = v17.ALPHA_ENTRIES[row.alpha_index].spec
        target, curried = _targets(row)
        try:
            state = start(curried)
            for dependency in spec.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for command in spec.script:
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise TwoSquareCompleteClosureError(
                        f"two-square body {name!r} requests implicit theorem authority"
                    )
                state = apply_tactic(state, tactic, arguments)
            proof = checked_final(state, curried)
        except TwoSquareCompleteClosureError:
            raise
        except (AttributeError, IndexError, KeyError, RecursionError, RuntimeError, TypeError, ValueError) as error:
            raise TwoSquareCompleteClosureError(
                f"cannot independently reconstruct exact two-square proof body {name!r}"
            ) from error
        if not check((), proof, curried):
            raise TwoSquareCompleteClosureError(
                f"unchanged intuitionistic kernel rejected two-square body {name!r}"
            )
        proof_nodes, proof_objects = _body_metrics(
            proof,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
        )
        nodes += proof_nodes
        objects += proof_objects
        rows.append(
            TwoSquareCheckedBody(
                row.node_id,
                name,
                row.statement_sha256,
                target,
                curried,
                proof,
                proof_nodes,
                proof_objects,
            )
        )
    return TwoSquareBodyMicrobatch(
        selected.parent_alpha_identity_sha256,
        selected.surface_sha256,
        tuple(rows),
        nodes,
        objects,
    )


def _verify_microbatch(
    batch: TwoSquareBodyMicrobatch,
    *,
    completed: Sequence[str],
    plan: TwoSquareClosurePlan,
) -> None:
    if (
        type(batch) is not TwoSquareBodyMicrobatch
        or batch.parent_alpha_identity_sha256 != plan.parent_alpha_identity_sha256
        or batch.surface_sha256 != plan.surface_sha256
        or type(batch.rows) is not tuple
        or not 1 <= len(batch.rows) <= MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise TwoSquareCompleteClosureError("two-square microbatch changed its immutable provenance")
    rows = {row.name: row for row in plan.rebuilt_rows}
    available = {row.name for row in plan.rows if not row.needs_rebuild} | set(completed)
    nodes = objects = 0
    previous = -1
    for actual in batch.rows:
        frozen = rows.get(actual.name)
        if (
            type(actual) is not TwoSquareCheckedBody
            or frozen is None
            or actual.node_id != frozen.node_id
            or actual.node_id <= previous
            or actual.name in available
            or actual.statement_sha256 != frozen.statement_sha256
            or not set(frozen.dependencies) <= available
        ):
            raise TwoSquareCompleteClosureError("two-square microbatch changed its exact local proof graph")
        expected, curried = _targets(frozen)
        if actual.target != expected or actual.curried_target != curried:
            raise TwoSquareCompleteClosureError("two-square proof changed its exact formula")
        observed_nodes, observed_objects = _body_metrics(
            actual.certificate,
            node_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
            object_budget=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
        )
        if (actual.proof_nodes, actual.proof_objects) != (observed_nodes, observed_objects):
            raise TwoSquareCompleteClosureError("two-square proof changed its exact resource metrics")
        if not check((), actual.certificate, curried):
            raise TwoSquareCompleteClosureError("kernel rejected an actual two-square proof body")
        nodes += observed_nodes
        objects += observed_objects
        previous = actual.node_id
        available.add(actual.name)
    if (batch.proof_nodes, batch.proof_objects) != (nodes, objects):
        raise TwoSquareCompleteClosureError("two-square microbatch changed its aggregate proof envelope")


def check_two_square_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
    *,
    plan: TwoSquareClosurePlan | None = None,
) -> TwoSquareCheckedBundle:
    """Check all 517 exact ordinary proof bodies with the original kernel."""

    selected = _sealed_plan(plan)
    if (
        type(bundle) is not ProofBundle
        or len(bundle.nodes) != EXPECTED_TWO_SQUARE_THEOREM_COUNT
        or bundle.root != EXPECTED_TWO_SQUARE_ROOT_NODE_ID
    ):
        raise TwoSquareCompleteClosureError("two-square bundle changed its exact node count or root")
    positions = {row.name: row.node_id for row in selected.rows}
    for row, node in zip(selected.rows, bundle.nodes, strict=True):
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != _targets(row)[0]
            or node.dependencies != tuple(positions[name] for name in row.dependencies)
        ):
            raise TwoSquareCompleteClosureError(
                f"two-square bundle changed frozen dependency node {row.name!r}"
            )
    expected = _targets(selected.rows[-1])[0]
    if target != expected:
        raise TwoSquareCompleteClosureError("two-square proof bundle changed its exact universal root")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise TwoSquareCompleteClosureError(
            "unchanged intuitionistic kernel rejected the complete two-square graph"
        ) from error
    if (
        receipt.node_count != EXPECTED_TWO_SQUARE_THEOREM_COUNT
        or receipt.kernel_calls != EXPECTED_TWO_SQUARE_THEOREM_COUNT
        or receipt.dependency_edges != EXPECTED_TWO_SQUARE_DEPENDENCY_EDGE_COUNT
    ):
        raise TwoSquareCompleteClosureError("two-square kernel receipt changed its exact graph")
    return TwoSquareCheckedBundle(bundle, target, receipt, selected.surface_sha256)


def assemble_two_square_proof_bundle(
    batches: Sequence[TwoSquareBodyMicrobatch],
    *,
    plan: TwoSquareClosurePlan | None = None,
) -> TwoSquareCheckedBundle:
    """Combine actual QR and newly reconstructed local theorem bodies."""

    selected = _sealed_plan(plan)
    if isinstance(batches, (str, bytes)) or not isinstance(batches, (tuple, list)):
        raise TwoSquareCompleteClosureError("two-square proof batches must be an ordered tuple or list")
    actual: dict[str, Proof] = {}
    completed: list[str] = []
    for batch in batches:
        _verify_microbatch(batch, completed=completed, plan=selected)
        for row in batch.rows:
            actual[row.name] = row.certificate
            completed.append(row.name)
    if set(actual) != {row.name for row in selected.rebuilt_rows}:
        raise TwoSquareCompleteClosureError("two-square graph lacks its exact reconstructed proof bodies")
    qr_bundle, _receipt = v16._checked_qr_bundle()
    existing = {
        spec.name: node.body
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
            _targets(row)[0],
            tuple(positions[name] for name in row.dependencies),
            actual[row.name] if row.needs_rebuild else existing[row.name],
        )
        for row in selected.rows
    )
    return check_two_square_proof_bundle(
        ProofBundle(nodes, EXPECTED_TWO_SQUARE_ROOT_NODE_ID),
        nodes[-1].target,
        plan=selected,
    )


_two_square_bundle_source: Path | None = None


def _default_two_square_bundle_source() -> Path:
    pyodide = Path(PYODIDE_TWO_SQUARE_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    return (
        location.parents[4]
        / "research/arithmetic-library/artifacts/two-square-proof-bundle-v1.json"
        if len(location.parents) > 4
        else pyodide
    )


def set_two_square_bundle_source(source: str | Path | None) -> None:
    global _two_square_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise TwoSquareCompleteClosureError("two-square proof source must be a filesystem path")
    _two_square_bundle_source = None if source is None else Path(source)
    checked_two_square_proof_bundle.cache_clear()
    replay_two_square_closed_theorem.cache_clear()


@lru_cache(maxsize=1)
def checked_two_square_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Load immutable complete proof data and check every actual body."""

    source = _two_square_bundle_source or _default_two_square_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise TwoSquareCompleteClosureError("actual complete two-square proof data are unavailable") from error
    data = payload.encode("utf-8")
    if (
        len(data) != EXPECTED_TWO_SQUARE_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_TWO_SQUARE_BUNDLE_SHA256
    ):
        raise TwoSquareCompleteClosureError("two-square proof artifact differs from its frozen provenance")
    try:
        bundle, target = decode_proof_bundle(payload)
        actual = check_two_square_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise TwoSquareCompleteClosureError("actual complete two-square proof data were rejected") from error
    if actual.receipt.total_body_nodes != EXPECTED_TWO_SQUARE_BUNDLE_BODY_PROOF_NODES:
        raise TwoSquareCompleteClosureError("two-square actual body-proof metrics changed")
    return actual.bundle, actual.receipt


@lru_cache(maxsize=None)
def replay_two_square_closed_theorem(name: str = TWO_SQUARE_ROOT_NAME) -> CheckedTheorem:
    """Compile and kernel-check an ordinary empty-context root, never release use."""

    plan = two_square_closure_plan()
    rows = {row.name: row for row in plan.rows}
    row = rows.get(name) if type(name) is str else None
    if row is None:
        raise TwoSquareCompleteClosureError("unknown theorem in the sealed two-square proof graph")
    bundle, _receipt = checked_two_square_proof_bundle()
    selected: set[int] = set()
    pending = [row.node_id]
    while pending:
        node_id = pending.pop()
        if node_id not in selected:
            selected.add(node_id)
            pending.extend(bundle.nodes[node_id].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
            for node in bundle.nodes
            if node.node_id in selected
        ),
        row.node_id,
    )
    formula = _targets(row)[0]
    candidate = compile_layered_replay(
        layered,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise TwoSquareCompleteClosureError(
            "unchanged kernel/resource policy rejected the exact ordinary two-square proof"
        )
    return CheckedTheorem(
        v17.ALPHA_EDITION.by_name[name].spec,
        formula,
        candidate.certificate,
        candidate.proof_nodes,
    )


def export_two_square_proof_bundle(
    output: str | Path,
    *,
    batch_size: int = 8,
) -> TwoSquareCheckedBundle:
    """Reconstruct bounded real proof batches, then seal a complete artifact."""

    if type(batch_size) is not int or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise TwoSquareCompleteClosureError("two-square batch size must be 1..16")
    plan = two_square_closure_plan()
    pending = tuple(row.name for row in plan.rebuilt_rows)
    completed: list[str] = []
    batches: list[TwoSquareBodyMicrobatch] = []
    for offset in range(0, len(pending), batch_size):
        names = pending[offset : offset + batch_size]
        batch = construct_two_square_body_microbatch(
            names,
            completed_names=completed,
            plan=plan,
        )
        batches.append(batch)
        completed.extend(names)
        print(
            f"two-square batch {len(batches)}: {len(names)} bodies, "
            f"{batch.proof_nodes} nodes, {batch.proof_objects} objects "
            f"({len(completed)}/{len(pending)})",
            flush=True,
        )
    result = assemble_two_square_proof_bundle(tuple(batches), plan=plan)
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    print(
        f"two-square bundle: {len(payload.encode())} bytes; "
        f"sha256={sha256(payload.encode()).hexdigest()}; "
        f"nodes={result.receipt.node_count}; "
        f"edges={result.receipt.dependency_edges}; "
        f"body-nodes={result.receipt.total_body_nodes}",
        flush=True,
    )
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    arguments = parser.parse_args()
    export_two_square_proof_bundle(arguments.output, batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
