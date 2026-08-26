"""Complete ordinary constructive proof evidence for the Alpha-v20 layer.

Four frozen existing artifacts provide genuine, dependency-curried parent
proof bodies.  Three remaining checked-parent bodies and all 39 new theorem
bodies are reconstructed under the unchanged original-kernel microbatch caps.
Every reused body is embedded again in one self-contained proof bundle and is
independently checked by the unchanged intuitionistic kernel.  Twelve maximal
endpoints are joined by a balanced, unenrolled synthetic conjunction.

This evidence generator grants no theorem authority, changes no immutable
parent, and adds no axiom, proof rule, kernel constructor, or trusted
historical proof reference.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import gc
from hashlib import sha256
from pathlib import Path
from typing import Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v19 as v19
from .alpha_enrollment_v20 import (
    FRONTIER_V20_EXPECTED_COUNT,
    PARENT_ALPHA_V19_ENROLLMENT_SHA256,
    PARENT_ALPHA_V19_IDENTITY_SHA256,
    AlphaV20EnrollmentError,
    alpha_v20_enrollment,
)
from .bertrand_complete_closure import (
    EXPECTED_BERTRAND_BUNDLE_BYTES,
    EXPECTED_BERTRAND_BUNDLE_SHA256,
    bertrand_complete_closure_plan,
)
from .campaign_frontier_closure import (
    EXPECTED_FRONTIER_BUNDLE_BYTES,
    EXPECTED_FRONTIER_BUNDLE_SHA256,
    FRONTIER_ARTIFACT_FILENAME,
    campaign_frontier_plan,
)
from .campaign_residual_closure import (
    EXPECTED_RESIDUAL_BUNDLE_BYTES,
    EXPECTED_RESIDUAL_BUNDLE_SHA256,
    residual_closure_plan,
)
from .frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayError,
    _proof_envelope_metrics_bounded,
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
from .theorems import TheoremSpec, _closed_formula, _primitive
from .two_square_complete_closure import (
    EXPECTED_TWO_SQUARE_BUNDLE_BYTES,
    EXPECTED_TWO_SQUARE_BUNDLE_SHA256,
    two_square_closure_plan,
)


NEXT_LAYER_ARTIFACT_FILENAME = "alpha-v20-next-layer-proof-bundle-v1.json"
PYODIDE_NEXT_LAYER_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{NEXT_LAYER_ARTIFACT_FILENAME}"
)

EXPECTED_NEXT_LAYER_THEOREM_COUNT = 589
EXPECTED_NEXT_LAYER_PARENT_COUNT = 550
EXPECTED_NEXT_LAYER_FRONTIER_COUNT = 39
EXPECTED_NEXT_LAYER_ROOT_COUNT = 12
EXPECTED_NEXT_LAYER_DEPENDENCY_EDGE_COUNT = 2_033
EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT = 590
EXPECTED_NEXT_LAYER_BUNDLE_EDGE_COUNT = 2_045
EXPECTED_NEXT_LAYER_REUSED_BODY_COUNT = 547
EXPECTED_NEXT_LAYER_REBUILT_PARENT_COUNT = 3
EXPECTED_NEXT_LAYER_REBUILT_BODY_COUNT = 42
EXPECTED_NEXT_LAYER_ORDERED_NAMES_SHA256 = (
    "88865cb1ab2c4d3c463034dcadc21427b9e4f736f67814a6376997dd0abcc256"
)
EXPECTED_NEXT_LAYER_SOURCE_COUNTS = {
    "v19_frontier": 182,
    "bertrand": 362,
    "residual": 2,
    "two_square": 1,
    "parent_rebuild": 3,
    "new": 39,
}

# These provenance seals were frozen only after all 590 original-kernel checks
# and canonical-byte generation succeeded.  A digest never grants authority:
# the loader independently checks every embedded ordinary body again.
EXPECTED_NEXT_LAYER_BUNDLE_BYTES = 14_775_673
EXPECTED_NEXT_LAYER_BUNDLE_SHA256 = (
    "1b623064f36e362c1a117daa193b1ee33ee7905ec804ee1ac164b42345b67069"
)
EXPECTED_NEXT_LAYER_BUNDLE_BODY_PROOF_NODES = 190_533


class NextLayerClosureError(ValueError):
    """A frozen parent, exact surface, original body, graph, or cap failed."""


@dataclass(frozen=True, slots=True)
class NextLayerClosureRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    source: str
    new_theorem: bool


@dataclass(frozen=True, slots=True)
class NextLayerClosurePlan:
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[NextLayerClosureRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str

    @property
    def rebuilt_rows(self) -> tuple[NextLayerClosureRow, ...]:
        return tuple(row for row in self.rows if row.source in {"parent_rebuild", "new"})

    @property
    def reused_rows(self) -> tuple[NextLayerClosureRow, ...]:
        return tuple(row for row in self.rows if row.source not in {"parent_rebuild", "new"})


@dataclass(frozen=True, slots=True)
class CheckedNextLayerBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle


@dataclass(frozen=True, slots=True)
class _ParentProvider:
    label: str
    filename: str
    bytes: int
    digest: str
    rows: tuple[object, ...]


def _repository_artifact(filename: str) -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / filename
    )


def _artifact_path(filename: str) -> Path:
    pyodide = Path("/lab/proof-artifacts") / filename
    return pyodide if pyodide.is_file() else _repository_artifact(filename)


@lru_cache(maxsize=1)
def _parent_providers() -> tuple[_ParentProvider, ...]:
    """Freeze precedence while deferring all heavyweight artifact decoding."""

    return (
        _ParentProvider(
            "v19_frontier",
            FRONTIER_ARTIFACT_FILENAME,
            EXPECTED_FRONTIER_BUNDLE_BYTES,
            EXPECTED_FRONTIER_BUNDLE_SHA256,
            campaign_frontier_plan().rows,
        ),
        _ParentProvider(
            "bertrand",
            "bertrand-proof-bundle-v1.json",
            EXPECTED_BERTRAND_BUNDLE_BYTES,
            EXPECTED_BERTRAND_BUNDLE_SHA256,
            bertrand_complete_closure_plan().rows,
        ),
        _ParentProvider(
            "residual",
            "alpha-v19-residual-proof-bundle-v1.json",
            EXPECTED_RESIDUAL_BUNDLE_BYTES,
            EXPECTED_RESIDUAL_BUNDLE_SHA256,
            residual_closure_plan().rows,
        ),
        _ParentProvider(
            "two_square",
            "two-square-proof-bundle-v1.json",
            EXPECTED_TWO_SQUARE_BUNDLE_BYTES,
            EXPECTED_TWO_SQUARE_BUNDLE_SHA256,
            two_square_closure_plan().rows,
        ),
    )


@lru_cache(maxsize=1)
def next_layer_closure_plan() -> NextLayerClosurePlan:
    """Freeze every new theorem, its actual full parent cone, and all edges."""

    try:
        enrollment = alpha_v20_enrollment()
    except (AlphaV20EnrollmentError, AttributeError, TypeError, ValueError) as error:
        raise NextLayerClosureError("invalid immutable Alpha-v20 enrollment") from error
    if (
        v19.ALPHA_V19_IDENTITY_SHA256 != PARENT_ALPHA_V19_IDENTITY_SHA256
        or v19.ALPHA_V19_ENROLLMENT_SHA256 != PARENT_ALPHA_V19_ENROLLMENT_SHA256
        or len(enrollment.frontier_specs) != FRONTIER_V20_EXPECTED_COUNT
    ):
        raise NextLayerClosureError("immutable fully checked Alpha-v19 parent changed")

    specifications = (*v19.ALPHA_CHECKED_SPECS, *enrollment.frontier_specs)
    table = {item.name: item for item in specifications}
    if len(table) != len(specifications):
        raise NextLayerClosureError("duplicate theorem names in the exact parent surface")
    frontier_names = tuple(item.name for item in enrollment.frontier_specs)
    used_by_frontier = {
        dependency
        for item in enrollment.frontier_specs
        for dependency in item.dependencies
    }
    roots = tuple(name for name in frontier_names if name not in used_by_frontier)
    if not roots:
        raise NextLayerClosureError("the next constructive layer has no maximal roots")

    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise NextLayerClosureError(f"unknown exact next-layer dependency {name!r}")
        selected.add(name)
        pending.extend(item.dependencies)

    providers = tuple(
        (provider.label, frozenset(row.name for row in provider.rows))
        for provider in _parent_providers()
    )
    frontier = frozenset(frontier_names)
    seen: set[str] = set()
    rows: list[NextLayerClosureRow] = []
    edges = 0
    for alpha_index, item in enumerate(specifications):
        if item.name not in selected:
            continue
        if not set(item.dependencies) <= seen:
            raise NextLayerClosureError(
                f"next-layer dependency order changed for {item.name!r}"
            )
        new = item.name in frontier
        source = (
            "new"
            if new
            else next(
                (label for label, names in providers if item.name in names),
                "parent_rebuild",
            )
        )
        rows.append(
            NextLayerClosureRow(
                node_id=len(rows),
                alpha_index=alpha_index,
                name=item.name,
                statement_sha256=sha256(item.statement.encode()).hexdigest(),
                dependencies=item.dependencies,
                source=source,
                new_theorem=new,
            )
        )
        seen.add(item.name)
        edges += len(item.dependencies)

    digest = sha256("\n".join(row.name for row in rows).encode()).hexdigest()
    if (
        len(rows) != EXPECTED_NEXT_LAYER_THEOREM_COUNT
        or len(frontier_names) != EXPECTED_NEXT_LAYER_FRONTIER_COUNT
        or len(roots) != EXPECTED_NEXT_LAYER_ROOT_COUNT
        or edges != EXPECTED_NEXT_LAYER_DEPENDENCY_EDGE_COUNT
        or digest != EXPECTED_NEXT_LAYER_ORDERED_NAMES_SHA256
        or Counter(row.source for row in rows) != EXPECTED_NEXT_LAYER_SOURCE_COUNTS
        or not frontier <= seen
    ):
        raise NextLayerClosureError("the exact next-layer closure surface changed")

    return NextLayerClosurePlan(
        parent_alpha_identity_sha256=PARENT_ALPHA_V19_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=PARENT_ALPHA_V19_ENROLLMENT_SHA256,
        rows=tuple(rows),
        root_names=roots,
        frontier_names=frontier_names,
        dependency_edge_count=edges,
        ordered_names_sha256=digest,
    )


def _spec_table() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (*v19.ALPHA_CHECKED_SPECS, *alpha_v20_enrollment().frontier_specs)
    }


def _curried_target(specification: TheoremSpec, table: dict[str, TheoremSpec]) -> Formula:
    target = _closed_formula(specification.statement)
    for dependency in reversed(specification.dependencies):
        target = Imp(_closed_formula(table[dependency].statement), target)
    return target


def _body_metrics(proof: Proof, *, nodes: int, objects: int) -> tuple[int, int]:
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        occurrences, _depth, identities, _annotations, _envelope = (
            _proof_envelope_metrics_bounded(
                proof,
                max_proof_occurrences=nodes,
                max_proof_objects=objects,
                max_proof_depth=limits.max_body_depth,
                max_annotation_occurrences=limits.max_body_annotation_occurrences,
                max_annotation_depth=limits.max_formula_depth,
                max_envelope_depth=limits.max_body_envelope_depth,
                label="constructive Alpha-v20 next-layer body",
            )
        )
    except (AttributeError, LayeredReplayError, RecursionError, TypeError, ValueError) as error:
        raise NextLayerClosureError(
            "next-layer body exceeds unchanged 125000-node/25000-object caps"
        ) from error
    return occurrences, identities


def _reconstruct_body(specification: TheoremSpec, table: dict[str, TheoremSpec]) -> Proof:
    target = _curried_target(specification, table)
    try:
        state = start(target)
        for dependency in specification.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in specification.script:
            tactic, arguments = _primitive(command)
            if tactic == "use":
                raise NextLayerClosureError(
                    f"next-layer body {specification.name!r} requests implicit authority"
                )
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
    except NextLayerClosureError:
        raise
    except (
        AttributeError,
        IndexError,
        KeyError,
        RecursionError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        raise NextLayerClosureError(
            f"cannot reconstruct exact original-kernel body {specification.name!r}"
        ) from error
    if not check((), body, target):
        raise NextLayerClosureError(
            f"unchanged intuitionistic kernel rejected {specification.name!r}"
        )
    return body


def _reused_parent_bodies() -> dict[str, Proof]:
    """Decode one frozen source at a time and retain only required bodies."""

    plan = next_layer_closure_plan()
    table = _spec_table()
    wanted = {
        provider.label: frozenset(
            row.name for row in plan.rows if row.source == provider.label
        )
        for provider in _parent_providers()
    }
    bodies: dict[str, Proof] = {}
    for provider in sorted(_parent_providers(), key=lambda item: item.bytes):
        names = wanted[provider.label]
        if not names:
            continue
        try:
            data = _artifact_path(provider.filename).read_bytes()
            if len(data) != provider.bytes or sha256(data).hexdigest() != provider.digest:
                raise NextLayerClosureError(
                    f"frozen {provider.label} parent proof artifact changed"
                )
            bundle, _target = decode_proof_bundle(data.decode("utf-8"))
            del data
            provider_rows = {row.name: row for row in provider.rows}
            provider_positions = {
                row.name: row.node_id for row in provider.rows
            }
            if not names <= set(provider_rows):
                raise NextLayerClosureError(
                    f"frozen {provider.label} artifact lost required parent proofs"
                )
            for name in names:
                source_row = provider_rows[name]
                if source_row.node_id >= len(bundle.nodes):
                    raise NextLayerClosureError(
                        f"frozen {provider.label} node is missing for {name!r}"
                    )
                node = bundle.nodes[source_row.node_id]
                specification = table[name]
                if (
                    node.node_id != source_row.node_id
                    or node.target != _closed_formula(specification.statement)
                    or node.dependencies
                    != tuple(provider_positions[item] for item in specification.dependencies)
                ):
                    raise NextLayerClosureError(
                        f"frozen {provider.label} body surface changed for {name!r}"
                    )
                bodies[name] = node.body
            print(
                f"next-layer parent {provider.label}: retained {len(names)} "
                f"actual bodies from {provider.filename}",
                flush=True,
            )
            del bundle
            gc.collect()
        except NextLayerClosureError:
            raise
        except (KeyError, OSError, ProofBundleError, UnicodeError) as error:
            raise NextLayerClosureError(
                f"frozen {provider.label} parent proof artifact is unavailable"
            ) from error
    if len(bodies) != EXPECTED_NEXT_LAYER_REUSED_BODY_COUNT:
        raise NextLayerClosureError("next-layer parent proof-body inventory is incomplete")
    return bodies


def _balanced_formula(formulas: tuple[Formula, ...]) -> Formula:
    if len(formulas) == 1:
        return formulas[0]
    midpoint = len(formulas) // 2
    return And(_balanced_formula(formulas[:midpoint]), _balanced_formula(formulas[midpoint:]))


def _balanced_proof(indices: tuple[int, ...]) -> Proof:
    if len(indices) == 1:
        return Hyp(indices[0])
    midpoint = len(indices) // 2
    return AndIntro(_balanced_proof(indices[:midpoint]), _balanced_proof(indices[midpoint:]))


def _synthetic_root(formulas: tuple[Formula, ...]) -> tuple[Formula, Proof]:
    if len(formulas) != EXPECTED_NEXT_LAYER_ROOT_COUNT:
        raise NextLayerClosureError("next-layer synthetic root has the wrong endpoint set")
    body = _balanced_proof(tuple(reversed(range(len(formulas)))))
    for _ in formulas:
        body = ImpIntro(body)
    return _balanced_formula(formulas), body


def check_next_layer_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
) -> CheckedNextLayerBundle:
    """Freeze every graph edge and original-kernel-check every proof node."""

    plan = next_layer_closure_plan()
    table = _spec_table()
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        type(bundle) is not ProofBundle
        or len(bundle.nodes) != EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT
        or bundle.root != EXPECTED_NEXT_LAYER_THEOREM_COUNT
    ):
        raise NextLayerClosureError("next-layer proof bundle changed its exact node surface")

    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        specification = table[row.name]
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != _closed_formula(specification.statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)
        ):
            raise NextLayerClosureError(
                f"next-layer proof bundle changed frozen theorem {row.name!r}"
            )

    expected_target, expected_body = _synthetic_root(
        tuple(_closed_formula(table[name].statement) for name in plan.root_names)
    )
    final = bundle.nodes[-1]
    if (
        final.node_id != EXPECTED_NEXT_LAYER_THEOREM_COUNT
        or final.dependencies != tuple(positions[name] for name in plan.root_names)
        or final.target != expected_target
        or final.body != expected_body
        or target != expected_target
    ):
        raise NextLayerClosureError("next-layer synthetic balanced conjunction changed")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise NextLayerClosureError(
            "unchanged intuitionistic kernel rejected a next-layer proof body"
        ) from error
    if (
        receipt.kernel_calls != EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT
        or receipt.node_count != EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_NEXT_LAYER_BUNDLE_EDGE_COUNT
    ):
        raise NextLayerClosureError("next-layer checker omitted a genuine proof or edge")
    return CheckedNextLayerBundle(bundle, target, receipt)


def assemble_next_layer_proof_bundle(*, batch_size: int = 8) -> CheckedNextLayerBundle:
    """Reconstruct only 42 bounded bodies and check the entire parent cone."""

    if (
        type(batch_size) is not int
        or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH
    ):
        raise NextLayerClosureError("next-layer proof batches must contain 1..16 rows")
    plan = next_layer_closure_plan()
    rebuilding = plan.rebuilt_rows
    if len(rebuilding) != EXPECTED_NEXT_LAYER_REBUILT_BODY_COUNT:
        raise NextLayerClosureError("next-layer rebuilt-body inventory changed")
    table = _spec_table()
    bodies = _reused_parent_bodies()
    for offset in range(0, len(rebuilding), batch_size):
        batch = rebuilding[offset : offset + batch_size]
        proof_nodes = proof_objects = 0
        for row in batch:
            body = _reconstruct_body(table[row.name], table)
            occurrences, identities = _body_metrics(
                body,
                nodes=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - proof_nodes,
                objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - proof_objects,
            )
            proof_nodes += occurrences
            proof_objects += identities
            bodies[row.name] = body
        print(
            f"next-layer batch {offset // batch_size + 1}: {len(batch)} bodies, "
            f"{proof_nodes} nodes, {proof_objects} objects "
            f"({min(offset + batch_size, len(rebuilding))}/{len(rebuilding)})",
            flush=True,
        )

    positions = {row.name: row.node_id for row in plan.rows}
    nodes = [
        BundleNode(
            row.node_id,
            _closed_formula(table[row.name].statement),
            tuple(positions[name] for name in row.dependencies),
            bodies[row.name],
        )
        for row in plan.rows
    ]
    target, synthetic = _synthetic_root(
        tuple(_closed_formula(table[name].statement) for name in plan.root_names)
    )
    nodes.append(
        BundleNode(
            len(nodes),
            target,
            tuple(positions[name] for name in plan.root_names),
            synthetic,
        )
    )
    return check_next_layer_proof_bundle(ProofBundle(tuple(nodes), len(nodes) - 1), target)


@lru_cache(maxsize=1)
def checked_next_layer_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Load frozen bytes and independently recheck all 590 original bodies."""

    try:
        data = _artifact_path(NEXT_LAYER_ARTIFACT_FILENAME).read_bytes()
        if (
            len(data) != EXPECTED_NEXT_LAYER_BUNDLE_BYTES
            or sha256(data).hexdigest() != EXPECTED_NEXT_LAYER_BUNDLE_SHA256
        ):
            raise NextLayerClosureError("frozen next-layer proof artifact changed")
        bundle, target = decode_proof_bundle(data.decode("utf-8"))
        result = check_next_layer_proof_bundle(bundle, target)
    except NextLayerClosureError:
        raise
    except (OSError, ProofBundleError, UnicodeError) as error:
        raise NextLayerClosureError("frozen next-layer proof artifact is unavailable") from error
    if result.receipt.total_body_nodes != EXPECTED_NEXT_LAYER_BUNDLE_BODY_PROOF_NODES:
        raise NextLayerClosureError("frozen next-layer proof-body accounting changed")
    return result.bundle, result.receipt


def export_next_layer_proof_bundle(
    output: str | Path,
    *,
    batch_size: int = 8,
) -> CheckedNextLayerBundle:
    """Generate canonical self-contained bytes only after every kernel check."""

    result = assemble_next_layer_proof_bundle(batch_size=batch_size)
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    encoded = payload.encode("utf-8")
    print(
        f"next-layer proof bundle: {len(encoded)} bytes; "
        f"sha256={sha256(encoded).hexdigest()}; "
        f"nodes={result.receipt.node_count}; "
        f"edges={result.receipt.dependency_edges}; "
        f"body-nodes={result.receipt.total_body_nodes}",
        flush=True,
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    arguments = parser.parse_args(argv)
    export_next_layer_proof_bundle(arguments.output, batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CheckedNextLayerBundle",
    "EXPECTED_NEXT_LAYER_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_NEXT_LAYER_BUNDLE_BYTES",
    "EXPECTED_NEXT_LAYER_BUNDLE_EDGE_COUNT",
    "EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT",
    "EXPECTED_NEXT_LAYER_BUNDLE_SHA256",
    "EXPECTED_NEXT_LAYER_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_NEXT_LAYER_FRONTIER_COUNT",
    "EXPECTED_NEXT_LAYER_ORDERED_NAMES_SHA256",
    "EXPECTED_NEXT_LAYER_PARENT_COUNT",
    "EXPECTED_NEXT_LAYER_REBUILT_BODY_COUNT",
    "EXPECTED_NEXT_LAYER_REBUILT_PARENT_COUNT",
    "EXPECTED_NEXT_LAYER_REUSED_BODY_COUNT",
    "EXPECTED_NEXT_LAYER_ROOT_COUNT",
    "EXPECTED_NEXT_LAYER_SOURCE_COUNTS",
    "EXPECTED_NEXT_LAYER_THEOREM_COUNT",
    "NEXT_LAYER_ARTIFACT_FILENAME",
    "NextLayerClosureError",
    "NextLayerClosurePlan",
    "NextLayerClosureRow",
    "PYODIDE_NEXT_LAYER_BUNDLE_PATH",
    "assemble_next_layer_proof_bundle",
    "check_next_layer_proof_bundle",
    "checked_next_layer_proof_bundle",
    "export_next_layer_proof_bundle",
    "next_layer_closure_plan",
]
