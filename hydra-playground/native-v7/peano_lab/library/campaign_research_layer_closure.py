"""Complete original-kernel proof evidence for the additive Alpha-v24 layer.

Frozen historical certificates are decoded individually; only proof bodies in
the actual new dependency cone are retained. New and unavailable parent proofs
are reconstructed in bounded microbatches and independently checked by the
unchanged intuitionistic arithmetic kernel. Hashes never substitute for proofs.
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

from ..kernel.formulas import And, Formula
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v23 as v23
from .alpha_enrollment_v24 import (
    FRONTIER_V24_EXPECTED_COUNT,
    FRONTIER_V24_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V23_COUNT,
    PARENT_ALPHA_V23_ENROLLMENT_SHA256,
    PARENT_ALPHA_V23_IDENTITY_SHA256,
    AlphaV24EnrollmentError,
    alpha_v24_enrollment,
)
from .campaign_milestone_closure import (
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_BYTES,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256,
    MILESTONE_CLOSURE_ARTIFACT_FILENAME,
    _body_metrics,
    _parent_providers as _historical_parent_providers,
    _reconstruct_body,
    milestone_closure_plan,
)
from .frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
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
from .theorems import TheoremSpec, _closed_formula


RESEARCH_LAYER_ARTIFACT_FILENAME = "alpha-v24-research-layer-proof-bundle-v1.json"
PYODIDE_RESEARCH_LAYER_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{RESEARCH_LAYER_ARTIFACT_FILENAME}"
)

# Zero/empty placeholders never authorize admission or checked-use replay.
EXPECTED_RESEARCH_LAYER_THEOREM_COUNT = 202
EXPECTED_RESEARCH_LAYER_ROOT_COUNT = 18
EXPECTED_RESEARCH_LAYER_DEPENDENCY_EDGE_COUNT = 484
EXPECTED_RESEARCH_LAYER_ORDERED_NAMES_SHA256 = (
    "fd952ced2b920ccfa8c861306b591917623dbc57c4c6a4130df2b06b8d23de34"
)
EXPECTED_RESEARCH_LAYER_SOURCE_COUNTS: dict[str, int] = {
    "new": 59,
    "parent_rebuild": 14,
    "residual": 2,
    "v19_frontier": 3,
    "v20_next_layer": 1,
    "v21_advanced_layer": 115,
    "v22_transport_layer": 5,
    "v23_milestone_closure": 3,
}
EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT = 203
EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT = 502
EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES = 11_065
EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES = 738_923
EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256 = (
    "627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9"
)


class ResearchLayerError(ValueError):
    """A parent proof, actual dependency, resource cap, or seal failed."""


@dataclass(frozen=True, slots=True)
class ResearchLayerRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    source: str
    new_theorem: bool


@dataclass(frozen=True, slots=True)
class ResearchLayerPlan:
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[ResearchLayerRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str

    @property
    def rebuilt_rows(self) -> tuple[ResearchLayerRow, ...]:
        return tuple(row for row in self.rows if row.source in {"parent_rebuild", "new"})


@dataclass(frozen=True, slots=True)
class CheckedResearchLayerBundle:
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


def _artifact_path(filename: str) -> Path:
    pyodide = Path("/lab/proof-artifacts") / filename
    if pyodide.is_file():
        return pyodide
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / filename
    )


@lru_cache(maxsize=1)
def _parent_providers() -> tuple[_ParentProvider, ...]:
    historical = tuple(
        _ParentProvider(
            label=item.label,
            filename=item.filename,
            bytes=item.bytes,
            digest=item.digest,
            rows=item.rows,
        )
        for item in _historical_parent_providers()
    )
    current_parent = _ParentProvider(
        label="v23_milestone_closure",
        filename=MILESTONE_CLOSURE_ARTIFACT_FILENAME,
        bytes=EXPECTED_MILESTONE_CLOSURE_BUNDLE_BYTES,
        digest=EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256,
        rows=milestone_closure_plan().rows,
    )
    return tuple(sorted((*historical, current_parent), key=lambda item: item.bytes))


def _sealed_plan(plan: ResearchLayerPlan) -> None:
    if not EXPECTED_RESEARCH_LAYER_THEOREM_COUNT:
        return
    if (
        len(plan.rows) != EXPECTED_RESEARCH_LAYER_THEOREM_COUNT
        or len(plan.root_names) != EXPECTED_RESEARCH_LAYER_ROOT_COUNT
        or plan.dependency_edge_count != EXPECTED_RESEARCH_LAYER_DEPENDENCY_EDGE_COUNT
        or plan.ordered_names_sha256 != EXPECTED_RESEARCH_LAYER_ORDERED_NAMES_SHA256
        or Counter(row.source for row in plan.rows) != EXPECTED_RESEARCH_LAYER_SOURCE_COUNTS
    ):
        raise ResearchLayerError("the frozen Alpha-v24 full dependency cone changed")


@lru_cache(maxsize=1)
def research_layer_plan() -> ResearchLayerPlan:
    """Select every genuine prerequisite of all maximal new theorem roots."""

    try:
        enrollment = alpha_v24_enrollment()
    except (AlphaV24EnrollmentError, AttributeError, TypeError, ValueError) as error:
        raise ResearchLayerError("invalid immutable Alpha-v24 enrollment") from error
    if (
        len(v23.ALPHA_ENTRIES) != PARENT_ALPHA_V23_COUNT
        or v23.ALPHA_V23_IDENTITY_SHA256 != PARENT_ALPHA_V23_IDENTITY_SHA256
        or v23.ALPHA_V23_ENROLLMENT_SHA256 != PARENT_ALPHA_V23_ENROLLMENT_SHA256
        or len(enrollment.frontier_specs) != FRONTIER_V24_EXPECTED_COUNT
    ):
        raise ResearchLayerError("the exact fully checked Alpha-v23 parent changed")

    specifications = (*v23.ALPHA_CHECKED_SPECS, *enrollment.frontier_specs)
    table = {item.name: item for item in specifications}
    if len(table) != len(specifications):
        raise ResearchLayerError("the Alpha-v24 proof surface repeats a theorem")
    frontier_names = tuple(item.name for item in enrollment.frontier_specs)
    if sha256("\n".join(frontier_names).encode()).hexdigest() != (
        FRONTIER_V24_EXPECTED_NAMES_SHA256
    ):
        raise ResearchLayerError("the exact Alpha-v24 frontier name seal changed")
    used = {dependency for item in enrollment.frontier_specs for dependency in item.dependencies}
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise ResearchLayerError("the Alpha-v24 campaign has no maximal theorem")

    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise ResearchLayerError(f"unknown actual proof dependency {name!r}")
        selected.add(name)
        pending.extend(item.dependencies)

    provider_names = tuple(
        (provider.label, frozenset(row.name for row in provider.rows))
        for provider in _parent_providers()
    )
    frontier = frozenset(frontier_names)
    seen: set[str] = set()
    rows: list[ResearchLayerRow] = []
    edges = 0
    for alpha_index, item in enumerate(specifications):
        if item.name not in selected:
            continue
        if not set(item.dependencies) <= seen:
            raise ResearchLayerError(f"forward dependency in actual proof {item.name!r}")
        new = item.name in frontier
        source = (
            "new"
            if new
            else next(
                (label for label, available in provider_names if item.name in available),
                "parent_rebuild",
            )
        )
        rows.append(
            ResearchLayerRow(
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
    if not frontier <= seen:
        raise ResearchLayerError("the actual proof cone omitted a new theorem")
    plan = ResearchLayerPlan(
        parent_alpha_identity_sha256=PARENT_ALPHA_V23_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=PARENT_ALPHA_V23_ENROLLMENT_SHA256,
        rows=tuple(rows),
        root_names=roots,
        frontier_names=frontier_names,
        dependency_edge_count=edges,
        ordered_names_sha256=sha256("\n".join(row.name for row in rows).encode()).hexdigest(),
    )
    _sealed_plan(plan)
    return plan


def _spec_table() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (*v23.ALPHA_CHECKED_SPECS, *alpha_v24_enrollment().frontier_specs)
    }


def _reused_parent_bodies() -> dict[str, Proof]:
    plan = research_layer_plan()
    table = _spec_table()
    bodies: dict[str, Proof] = {}
    for provider in _parent_providers():
        names = frozenset(row.name for row in plan.rows if row.source == provider.label)
        if not names:
            continue
        try:
            data = _artifact_path(provider.filename).read_bytes()
            if len(data) != provider.bytes or sha256(data).hexdigest() != provider.digest:
                raise ResearchLayerError(
                    f"frozen historical proof artifact changed: {provider.filename}"
                )
            bundle, _target = decode_proof_bundle(data.decode("utf-8"))
            del data
            rows = {row.name: row for row in provider.rows}
            positions = {row.name: row.node_id for row in provider.rows}
            if not names <= rows.keys():
                raise ResearchLayerError(f"provider {provider.label!r} lost a needed theorem")
            for name in names:
                row = rows[name]
                if row.node_id >= len(bundle.nodes):
                    raise ResearchLayerError(f"missing historical proof body {name!r}")
                node = bundle.nodes[row.node_id]
                spec = table[name]
                if (
                    node.node_id != row.node_id
                    or node.target != _closed_formula(spec.statement)
                    or node.dependencies
                    != tuple(positions[dependency] for dependency in spec.dependencies)
                ):
                    raise ResearchLayerError(f"historical proof surface changed: {name!r}")
                bodies[name] = node.body
            print(
                f"research-layer parent {provider.label}: retained {len(names)} actual "
                f"bodies from {provider.filename}",
                flush=True,
            )
            del bundle
            gc.collect()
        except ResearchLayerError:
            raise
        except (KeyError, OSError, ProofBundleError, UnicodeError) as error:
            raise ResearchLayerError(
                f"historical original proof artifact unavailable: {provider.filename}"
            ) from error
    expected = sum(row.source not in {"new", "parent_rebuild"} for row in plan.rows)
    if len(bodies) != expected:
        raise ResearchLayerError("incomplete historical ordinary-proof inventory")
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
    if not formulas:
        raise ResearchLayerError("an empty synthetic packaging root is invalid")
    if EXPECTED_RESEARCH_LAYER_ROOT_COUNT and (
        len(formulas) != EXPECTED_RESEARCH_LAYER_ROOT_COUNT
    ):
        raise ResearchLayerError("the frozen synthetic endpoint inventory changed")
    proof = _balanced_proof(tuple(reversed(range(len(formulas)))))
    for _ in formulas:
        proof = ImpIntro(proof)
    return _balanced_formula(formulas), proof


def check_research_layer_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
) -> CheckedResearchLayerBundle:
    """Check every actual dependency and every ordinary original proof body."""

    plan = research_layer_plan()
    table = _spec_table()
    positions = {row.name: row.node_id for row in plan.rows}
    expected_count = len(plan.rows) + 1
    if (
        type(bundle) is not ProofBundle
        or len(bundle.nodes) != expected_count
        or bundle.root != len(plan.rows)
        or (
            EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
            and expected_count != EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
        )
    ):
        raise ResearchLayerError("the research proof bundle changed its exact nodes")
    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        specification = table[row.name]
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != _closed_formula(specification.statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)
        ):
            raise ResearchLayerError(f"research proof changed exact theorem {row.name!r}")
    expected_target, expected_body = _synthetic_root(
        tuple(_closed_formula(table[name].statement) for name in plan.root_names)
    )
    final = bundle.nodes[-1]
    if (
        final.node_id != len(plan.rows)
        or final.dependencies != tuple(positions[name] for name in plan.root_names)
        or final.target != expected_target
        or final.body != expected_body
        or target != expected_target
    ):
        raise ResearchLayerError("the exact synthetic conjunction root changed")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise ResearchLayerError(
            "the unchanged intuitionistic kernel rejected a research-layer body"
        ) from error
    expected_edges = plan.dependency_edge_count + len(plan.root_names)
    if (
        receipt.kernel_calls != expected_count
        or receipt.node_count != expected_count
        or receipt.dependency_edges != expected_edges
        or (
            EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT
            and expected_edges != EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT
        )
    ):
        raise ResearchLayerError("the kernel omitted an actual proof body or edge")
    return CheckedResearchLayerBundle(bundle, target, receipt)


def assemble_research_layer_proof_bundle(*, batch_size: int = 1) -> CheckedResearchLayerBundle:
    """Bound each reconstructed proof batch and check its full actual cone."""

    if type(batch_size) is not int or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise ResearchLayerError("research proof batches must contain 1..16 rows")
    plan = research_layer_plan()
    rows = plan.rebuilt_rows
    table = _spec_table()
    bodies = _reused_parent_bodies()
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset : offset + batch_size]
        proof_nodes = proof_objects = 0
        for row in batch:
            try:
                body = _reconstruct_body(table[row.name], table)
                occurrences, identities = _body_metrics(
                    body,
                    nodes=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - proof_nodes,
                    objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - proof_objects,
                )
            except (AttributeError, RecursionError, TypeError, ValueError) as error:
                raise ResearchLayerError(
                    f"cannot construct a bounded original-kernel proof of {row.name!r}"
                ) from error
            proof_nodes += occurrences
            proof_objects += identities
            bodies[row.name] = body
        print(
            f"research-layer batch {offset // batch_size + 1}: {len(batch)} bodies, "
            f"{proof_nodes} nodes, {proof_objects} objects "
            f"({min(offset + batch_size, len(rows))}/{len(rows)})",
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
            node_id=len(nodes),
            target=target,
            dependencies=tuple(positions[name] for name in plan.root_names),
            body=synthetic,
        )
    )
    return check_research_layer_proof_bundle(ProofBundle(tuple(nodes), len(nodes) - 1), target)


@lru_cache(maxsize=1)
def checked_research_layer_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Accept frozen artifact bytes only after all original kernel checks."""

    if (
        EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES <= 0
        or len(EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256) != 64
        or EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES <= 0
    ):
        raise ResearchLayerError("the research proof artifact has not been frozen")
    try:
        payload = _artifact_path(RESEARCH_LAYER_ARTIFACT_FILENAME).read_bytes()
        if (
            len(payload) != EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES
            or sha256(payload).hexdigest() != EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256
        ):
            raise ResearchLayerError("the sealed research proof artifact changed")
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        result = check_research_layer_proof_bundle(bundle, target)
    except ResearchLayerError:
        raise
    except (OSError, ProofBundleError, UnicodeError) as error:
        raise ResearchLayerError("the research proof artifact is unavailable") from error
    if result.receipt.total_body_nodes != EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES:
        raise ResearchLayerError("frozen research proof-body accounting changed")
    return result.bundle, result.receipt


def export_research_layer_proof_bundle(
    output: str | Path,
    *,
    batch_size: int = 1,
) -> CheckedResearchLayerBundle:
    result = assemble_research_layer_proof_bundle(batch_size=batch_size)
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    encoded = payload.encode("utf-8")
    print(
        f"research-layer proof bundle: {len(encoded)} bytes; "
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
    parser.add_argument("--batch-size", type=int, default=1)
    arguments = parser.parse_args(argv)
    export_research_layer_proof_bundle(arguments.output, batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "RESEARCH_LAYER_ARTIFACT_FILENAME",
    "ResearchLayerError",
    "ResearchLayerPlan",
    "ResearchLayerRow",
    "CheckedResearchLayerBundle",
    "EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES",
    "EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT",
    "EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT",
    "EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256",
    "EXPECTED_RESEARCH_LAYER_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_RESEARCH_LAYER_ORDERED_NAMES_SHA256",
    "EXPECTED_RESEARCH_LAYER_ROOT_COUNT",
    "EXPECTED_RESEARCH_LAYER_SOURCE_COUNTS",
    "EXPECTED_RESEARCH_LAYER_THEOREM_COUNT",
    "PYODIDE_RESEARCH_LAYER_BUNDLE_PATH",
    "research_layer_plan",
    "assemble_research_layer_proof_bundle",
    "check_research_layer_proof_bundle",
    "checked_research_layer_proof_bundle",
    "export_research_layer_proof_bundle",
]
