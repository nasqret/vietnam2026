"""Ordinary original-kernel evidence for the additive Alpha-v21 campaign.

Historical proof artifacts are opened individually; only the actual required
dependency-curried bodies are retained. New bodies are reconstructed in small
resource-bounded batches and then embedded, together with their entire real
historical dependency cone, in one self-contained intuitionistic proof bundle.

Artifact hashes authenticate bytes but never replace kernel checks. The final
balanced conjunction is an unenrolled packaging root, not a new theorem.
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

from ..kernel.checker import check
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v20 as v20
from .alpha_enrollment_v21 import (
    FRONTIER_V21_EXPECTED_COUNT,
    FRONTIER_V21_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V20_COUNT,
    PARENT_ALPHA_V20_ENROLLMENT_SHA256,
    PARENT_ALPHA_V20_IDENTITY_SHA256,
    AlphaV21EnrollmentError,
    alpha_v21_enrollment,
)
from .campaign_next_layer_closure import (
    EXPECTED_NEXT_LAYER_BUNDLE_BYTES,
    EXPECTED_NEXT_LAYER_BUNDLE_SHA256,
    NEXT_LAYER_ARTIFACT_FILENAME,
    _body_metrics,
    _parent_providers as _historical_parent_providers,
    _reconstruct_body,
    next_layer_closure_plan,
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


ADVANCED_LAYER_ARTIFACT_FILENAME = "alpha-v21-advanced-layer-proof-bundle-v1.json"
PYODIDE_ADVANCED_LAYER_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{ADVANCED_LAYER_ARTIFACT_FILENAME}"
)

# Seals are frozen immediately after the first complete original-kernel proof
# construction. Empty placeholders never authorize replay or admission.
EXPECTED_ADVANCED_LAYER_THEOREM_COUNT = 208
EXPECTED_ADVANCED_LAYER_ROOT_COUNT = 27
EXPECTED_ADVANCED_LAYER_DEPENDENCY_EDGE_COUNT = 464
EXPECTED_ADVANCED_LAYER_ORDERED_NAMES_SHA256 = (
    "4412c3b3b3d7479bbc5423e335e359fadbb5c006fe8b92248065f2839bb9ae20"
)
EXPECTED_ADVANCED_LAYER_SOURCE_COUNTS: dict[str, int] = {
    "v19_frontier": 132,
    "new": 54,
    "v20_next_layer": 13,
    "residual": 9,
}
EXPECTED_ADVANCED_LAYER_BUNDLE_NODE_COUNT = 209
EXPECTED_ADVANCED_LAYER_BUNDLE_EDGE_COUNT = 491
EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES = 10_304
EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES = 1_005_317
EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256 = (
    "65ecae7cb6b3e102790efa281451db3da5ab83868afcf9d57e6656f7a3eafda0"
)


class AdvancedLayerClosureError(ValueError):
    """An exact parent, original proof body, resource cap, or seal failed."""


@dataclass(frozen=True, slots=True)
class AdvancedLayerClosureRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    source: str
    new_theorem: bool


@dataclass(frozen=True, slots=True)
class AdvancedLayerClosurePlan:
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[AdvancedLayerClosureRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str

    @property
    def rebuilt_rows(self) -> tuple[AdvancedLayerClosureRow, ...]:
        return tuple(row for row in self.rows if row.source in {"parent_rebuild", "new"})


@dataclass(frozen=True, slots=True)
class CheckedAdvancedLayerBundle:
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
        if item.label in {"v19_frontier", "residual"}
    )
    current_parent = _ParentProvider(
        label="v20_next_layer",
        filename=NEXT_LAYER_ARTIFACT_FILENAME,
        bytes=EXPECTED_NEXT_LAYER_BUNDLE_BYTES,
        digest=EXPECTED_NEXT_LAYER_BUNDLE_SHA256,
        rows=next_layer_closure_plan().rows,
    )
    return tuple(sorted((*historical, current_parent), key=lambda item: item.bytes))


def _sealed_plan(plan: AdvancedLayerClosurePlan) -> None:
    if not EXPECTED_ADVANCED_LAYER_THEOREM_COUNT:
        return
    if (
        len(plan.rows) != EXPECTED_ADVANCED_LAYER_THEOREM_COUNT
        or len(plan.root_names) != EXPECTED_ADVANCED_LAYER_ROOT_COUNT
        or plan.dependency_edge_count != EXPECTED_ADVANCED_LAYER_DEPENDENCY_EDGE_COUNT
        or plan.ordered_names_sha256 != EXPECTED_ADVANCED_LAYER_ORDERED_NAMES_SHA256
        or Counter(row.source for row in plan.rows)
        != EXPECTED_ADVANCED_LAYER_SOURCE_COUNTS
    ):
        raise AdvancedLayerClosureError("the frozen Alpha-v21 full dependency cone changed")


@lru_cache(maxsize=1)
def advanced_layer_closure_plan() -> AdvancedLayerClosurePlan:
    """Find every real prerequisite of all maximal new theorem endpoints."""

    try:
        enrollment = alpha_v21_enrollment()
    except (AlphaV21EnrollmentError, AttributeError, TypeError, ValueError) as error:
        raise AdvancedLayerClosureError("invalid immutable Alpha-v21 enrollment") from error
    if (
        len(v20.ALPHA_ENTRIES) != PARENT_ALPHA_V20_COUNT
        or v20.ALPHA_V20_IDENTITY_SHA256 != PARENT_ALPHA_V20_IDENTITY_SHA256
        or v20.ALPHA_V20_ENROLLMENT_SHA256 != PARENT_ALPHA_V20_ENROLLMENT_SHA256
        or len(enrollment.frontier_specs) != FRONTIER_V21_EXPECTED_COUNT
    ):
        raise AdvancedLayerClosureError("the exact fully checked Alpha-v20 parent changed")

    specifications = (*v20.ALPHA_CHECKED_SPECS, *enrollment.frontier_specs)
    table = {item.name: item for item in specifications}
    if len(table) != len(specifications):
        raise AdvancedLayerClosureError("the Alpha-v21 proof surface repeats a theorem")
    frontier_names = tuple(item.name for item in enrollment.frontier_specs)
    if sha256("\n".join(frontier_names).encode()).hexdigest() != (
        FRONTIER_V21_EXPECTED_NAMES_SHA256
    ):
        raise AdvancedLayerClosureError("the Alpha-v21 exact frontier name seal changed")
    used = {dependency for item in enrollment.frontier_specs for dependency in item.dependencies}
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise AdvancedLayerClosureError("the Alpha-v21 campaign has no maximal theorem")

    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise AdvancedLayerClosureError(f"unknown actual proof dependency {name!r}")
        selected.add(name)
        pending.extend(item.dependencies)

    provider_names = tuple(
        (provider.label, frozenset(row.name for row in provider.rows))
        for provider in _parent_providers()
    )
    frontier = frozenset(frontier_names)
    seen: set[str] = set()
    rows: list[AdvancedLayerClosureRow] = []
    edges = 0
    for alpha_index, item in enumerate(specifications):
        if item.name not in selected:
            continue
        if not set(item.dependencies) <= seen:
            raise AdvancedLayerClosureError(
                f"forward dependency in the actual proof of {item.name!r}"
            )
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
            AdvancedLayerClosureRow(
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
        raise AdvancedLayerClosureError("the proof cone omitted a newly enrolled theorem")
    plan = AdvancedLayerClosurePlan(
        parent_alpha_identity_sha256=PARENT_ALPHA_V20_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=PARENT_ALPHA_V20_ENROLLMENT_SHA256,
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
        for item in (*v20.ALPHA_CHECKED_SPECS, *alpha_v21_enrollment().frontier_specs)
    }


def _reused_parent_bodies() -> dict[str, Proof]:
    plan = advanced_layer_closure_plan()
    table = _spec_table()
    bodies: dict[str, Proof] = {}
    for provider in _parent_providers():
        names = frozenset(row.name for row in plan.rows if row.source == provider.label)
        if not names:
            continue
        try:
            data = _artifact_path(provider.filename).read_bytes()
            if len(data) != provider.bytes or sha256(data).hexdigest() != provider.digest:
                raise AdvancedLayerClosureError(
                    f"frozen historical proof artifact changed: {provider.filename}"
                )
            bundle, _target = decode_proof_bundle(data.decode("utf-8"))
            del data
            rows = {row.name: row for row in provider.rows}
            positions = {row.name: row.node_id for row in provider.rows}
            if not names <= rows.keys():
                raise AdvancedLayerClosureError(
                    f"historical provider {provider.label!r} lost a needed theorem"
                )
            for name in names:
                row = rows[name]
                if row.node_id >= len(bundle.nodes):
                    raise AdvancedLayerClosureError(f"missing historical proof body {name!r}")
                node = bundle.nodes[row.node_id]
                spec = table[name]
                if (
                    node.node_id != row.node_id
                    or node.target != _closed_formula(spec.statement)
                    or node.dependencies
                    != tuple(positions[dependency] for dependency in spec.dependencies)
                ):
                    raise AdvancedLayerClosureError(
                        f"historical proof body changed its exact surface: {name!r}"
                    )
                bodies[name] = node.body
            print(
                f"advanced-layer parent {provider.label}: retained {len(names)} actual "
                f"bodies from {provider.filename}",
                flush=True,
            )
            del bundle
            gc.collect()
        except AdvancedLayerClosureError:
            raise
        except (KeyError, OSError, ProofBundleError, UnicodeError) as error:
            raise AdvancedLayerClosureError(
                f"historical original proof artifact unavailable: {provider.filename}"
            ) from error
    expected = sum(row.source not in {"new", "parent_rebuild"} for row in plan.rows)
    if len(bodies) != expected:
        raise AdvancedLayerClosureError("incomplete historical ordinary-proof inventory")
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
        raise AdvancedLayerClosureError("an empty synthetic packaging root is invalid")
    if EXPECTED_ADVANCED_LAYER_ROOT_COUNT and (
        len(formulas) != EXPECTED_ADVANCED_LAYER_ROOT_COUNT
    ):
        raise AdvancedLayerClosureError("the frozen synthetic endpoint inventory changed")
    proof = _balanced_proof(tuple(reversed(range(len(formulas)))))
    for _ in formulas:
        proof = ImpIntro(proof)
    return _balanced_formula(formulas), proof


def check_advanced_layer_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
) -> CheckedAdvancedLayerBundle:
    """Check every exact graph edge and every original intuitionistic body."""

    plan = advanced_layer_closure_plan()
    table = _spec_table()
    positions = {row.name: row.node_id for row in plan.rows}
    expected_count = len(plan.rows) + 1
    if (
        type(bundle) is not ProofBundle
        or len(bundle.nodes) != expected_count
        or bundle.root != len(plan.rows)
        or (
            EXPECTED_ADVANCED_LAYER_BUNDLE_NODE_COUNT
            and expected_count != EXPECTED_ADVANCED_LAYER_BUNDLE_NODE_COUNT
        )
    ):
        raise AdvancedLayerClosureError("the advanced proof bundle changed its exact nodes")
    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        specification = table[row.name]
        if (
            type(node) is not BundleNode
            or node.node_id != row.node_id
            or node.target != _closed_formula(specification.statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)
        ):
            raise AdvancedLayerClosureError(
                f"the advanced proof bundle changed exact theorem {row.name!r}"
            )
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
        raise AdvancedLayerClosureError("the exact synthetic conjunction root changed")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise AdvancedLayerClosureError(
            "the unchanged intuitionistic kernel rejected an advanced-layer body"
        ) from error
    expected_edges = plan.dependency_edge_count + len(plan.root_names)
    if (
        receipt.kernel_calls != expected_count
        or receipt.node_count != expected_count
        or receipt.dependency_edges != expected_edges
        or (
            EXPECTED_ADVANCED_LAYER_BUNDLE_EDGE_COUNT
            and expected_edges != EXPECTED_ADVANCED_LAYER_BUNDLE_EDGE_COUNT
        )
    ):
        raise AdvancedLayerClosureError("the kernel omitted an actual proof body or edge")
    return CheckedAdvancedLayerBundle(bundle, target, receipt)


def assemble_advanced_layer_proof_bundle(*, batch_size: int = 2) -> CheckedAdvancedLayerBundle:
    """Bound every reconstructed proof batch and check the entire real cone."""

    if type(batch_size) is not int or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise AdvancedLayerClosureError("advanced proof batches must contain 1..16 rows")
    plan = advanced_layer_closure_plan()
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
                raise AdvancedLayerClosureError(
                    f"cannot construct a bounded original-kernel proof of {row.name!r}"
                ) from error
            proof_nodes += occurrences
            proof_objects += identities
            bodies[row.name] = body
        print(
            f"advanced-layer batch {offset // batch_size + 1}: {len(batch)} bodies, "
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
    return check_advanced_layer_proof_bundle(ProofBundle(tuple(nodes), len(nodes) - 1), target)


@lru_cache(maxsize=1)
def checked_advanced_layer_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Accept frozen bytes only after all original kernel checks succeed."""

    if (
        EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES <= 0
        or len(EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256) != 64
        or EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES <= 0
    ):
        raise AdvancedLayerClosureError("the advanced proof artifact has not been frozen")
    try:
        payload = _artifact_path(ADVANCED_LAYER_ARTIFACT_FILENAME).read_bytes()
        if (
            len(payload) != EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES
            or sha256(payload).hexdigest() != EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256
        ):
            raise AdvancedLayerClosureError("the sealed advanced proof artifact changed")
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        result = check_advanced_layer_proof_bundle(bundle, target)
    except AdvancedLayerClosureError:
        raise
    except (OSError, ProofBundleError, UnicodeError) as error:
        raise AdvancedLayerClosureError("the advanced proof artifact is unavailable") from error
    if result.receipt.total_body_nodes != EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES:
        raise AdvancedLayerClosureError("frozen advanced proof-body accounting changed")
    return result.bundle, result.receipt


def export_advanced_layer_proof_bundle(
    output: str | Path,
    *,
    batch_size: int = 2,
) -> CheckedAdvancedLayerBundle:
    result = assemble_advanced_layer_proof_bundle(batch_size=batch_size)
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    encoded = payload.encode("utf-8")
    print(
        f"advanced-layer proof bundle: {len(encoded)} bytes; "
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
    parser.add_argument("--batch-size", type=int, default=2)
    arguments = parser.parse_args(argv)
    export_advanced_layer_proof_bundle(arguments.output, batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ADVANCED_LAYER_ARTIFACT_FILENAME",
    "AdvancedLayerClosureError",
    "AdvancedLayerClosurePlan",
    "AdvancedLayerClosureRow",
    "CheckedAdvancedLayerBundle",
    "EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES",
    "EXPECTED_ADVANCED_LAYER_BUNDLE_EDGE_COUNT",
    "EXPECTED_ADVANCED_LAYER_BUNDLE_NODE_COUNT",
    "EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256",
    "EXPECTED_ADVANCED_LAYER_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_ADVANCED_LAYER_ORDERED_NAMES_SHA256",
    "EXPECTED_ADVANCED_LAYER_ROOT_COUNT",
    "EXPECTED_ADVANCED_LAYER_SOURCE_COUNTS",
    "EXPECTED_ADVANCED_LAYER_THEOREM_COUNT",
    "PYODIDE_ADVANCED_LAYER_BUNDLE_PATH",
    "advanced_layer_closure_plan",
    "assemble_advanced_layer_proof_bundle",
    "check_advanced_layer_proof_bundle",
    "checked_advanced_layer_proof_bundle",
    "export_advanced_layer_proof_bundle",
]
