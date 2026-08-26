"""Independently checked closure of the next constructive campaign frontier.

The canonical all-natural two-square proof artifact supplies already checked
parent proof bodies. Every missing parent body and every newly authored
campaign body is reconstructed from its exact dependency-curried tactic
script, checked by the unchanged intuitionistic kernel, and retained inside
one self-contained ordinary proof bundle. A balanced synthetic conjunction
keeps all independent frontier endpoints reachable without claiming that the
conjunction itself is an enrolled theorem.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from . import editions_v18 as v18
from .alpha_enrollment_v19 import (
    PARENT_ALPHA_V18_IDENTITY_SHA256,
    AlphaV19EnrollmentError,
    alpha_v19_enrollment,
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


FRONTIER_ARTIFACT_FILENAME = "alpha-v19-campaign-frontier-proof-bundle-v1.json"
PYODIDE_FRONTIER_BUNDLE_PATH = f"/lab/proof-artifacts/{FRONTIER_ARTIFACT_FILENAME}"
EXPECTED_FRONTIER_BUNDLE_BYTES = 1_617_207
EXPECTED_FRONTIER_BUNDLE_SHA256 = (
    "cf7947a944d54e9eb956fb153702b29c953100ece6cf05743162759b0fba9b17"
)
EXPECTED_FRONTIER_BUNDLE_BODY_PROOF_NODES = 34_020


class CampaignFrontierClosureError(ValueError):
    """An exact campaign surface, ordinary proof, artifact, or budget failed."""


@dataclass(frozen=True, slots=True)
class CampaignFrontierRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    source: str
    new_theorem: bool


@dataclass(frozen=True, slots=True)
class CampaignFrontierPlan:
    parent_alpha_identity_sha256: str
    rows: tuple[CampaignFrontierRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str

    @property
    def rebuilt_rows(self) -> tuple[CampaignFrontierRow, ...]:
        return tuple(row for row in self.rows if row.source != "two_square")


@dataclass(frozen=True, slots=True)
class CheckedCampaignFrontierBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle


def _repository_artifact(filename: str) -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / filename
    )


def _two_square_artifact() -> Path:
    pyodide = Path("/lab/proof-artifacts/two-square-proof-bundle-v1.json")
    return pyodide if pyodide.is_file() else _repository_artifact(
        "two-square-proof-bundle-v1.json"
    )


@lru_cache(maxsize=1)
def campaign_frontier_plan() -> CampaignFrontierPlan:
    """Freeze the exact new endpoints and their real full dependency cone."""

    try:
        enrollment = alpha_v19_enrollment()
    except AlphaV19EnrollmentError as error:
        raise CampaignFrontierClosureError("invalid sealed campaign enrollment") from error
    all_specs = (*v18.ALPHA_SPECS, *enrollment.frontier_specs)
    by_name = {spec.name: spec for spec in all_specs}
    frontier_names = tuple(spec.name for spec in enrollment.frontier_specs)
    used_by_frontier = {
        dependency
        for spec in enrollment.frontier_specs
        for dependency in spec.dependencies
    }
    roots = tuple(name for name in frontier_names if name not in used_by_frontier)
    if not roots:
        raise CampaignFrontierClosureError("campaign frontier has no maximal endpoints")
    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        spec = by_name.get(name)
        if spec is None:
            raise CampaignFrontierClosureError(f"unknown campaign dependency {name!r}")
        selected.add(name)
        pending.extend(spec.dependencies)

    reused = {row.name for row in two_square_closure_plan().rows}
    frontier_set = frozenset(frontier_names)
    seen: set[str] = set()
    rows: list[CampaignFrontierRow] = []
    edges = 0
    for alpha_index, spec in enumerate(all_specs):
        if spec.name not in selected:
            continue
        if not set(spec.dependencies) <= seen:
            raise CampaignFrontierClosureError(
                f"campaign dependency order changed for {spec.name!r}"
            )
        new = spec.name in frontier_set
        source = "frontier" if new else "two_square" if spec.name in reused else "parent"
        rows.append(
            CampaignFrontierRow(
                node_id=len(rows),
                alpha_index=alpha_index,
                name=spec.name,
                statement_sha256=sha256(spec.statement.encode()).hexdigest(),
                dependencies=spec.dependencies,
                source=source,
                new_theorem=new,
            )
        )
        seen.add(spec.name)
        edges += len(spec.dependencies)
    if not set(frontier_names) <= seen:
        raise CampaignFrontierClosureError("campaign frontier lost an enrolled theorem")
    return CampaignFrontierPlan(
        parent_alpha_identity_sha256=PARENT_ALPHA_V18_IDENTITY_SHA256,
        rows=tuple(rows),
        root_names=roots,
        frontier_names=frontier_names,
        dependency_edge_count=edges,
        ordered_names_sha256=sha256(
            "\n".join(row.name for row in rows).encode()
        ).hexdigest(),
    )


def _spec_table() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (*v18.ALPHA_SPECS, *alpha_v19_enrollment().frontier_specs)
    }


def _curried_target(spec: TheoremSpec, table: dict[str, TheoremSpec]) -> Formula:
    result = _closed_formula(spec.statement)
    for name in reversed(spec.dependencies):
        result = Imp(_closed_formula(table[name].statement), result)
    return result


def _body_metrics(proof: Proof, *, nodes: int, objects: int) -> tuple[int, int]:
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        count, _depth, identities, _annotations, _envelope = (
            _proof_envelope_metrics_bounded(
                proof,
                max_proof_occurrences=nodes,
                max_proof_objects=objects,
                max_proof_depth=limits.max_body_depth,
                max_annotation_occurrences=limits.max_body_annotation_occurrences,
                max_annotation_depth=limits.max_formula_depth,
                max_envelope_depth=limits.max_body_envelope_depth,
                label="constructive campaign frontier body",
            )
        )
    except (AttributeError, LayeredReplayError, RecursionError, TypeError, ValueError) as error:
        raise CampaignFrontierClosureError(
            "campaign proof body exceeds unchanged 125000-node/25000-object limits"
        ) from error
    return count, identities


def _reconstruct_body(
    spec: TheoremSpec,
    table: dict[str, TheoremSpec],
) -> Proof:
    target = _curried_target(spec, table)
    try:
        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, arguments = _primitive(command)
            if tactic == "use":
                raise CampaignFrontierClosureError(
                    f"campaign theorem {spec.name!r} requests implicit theorem authority"
                )
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
    except CampaignFrontierClosureError:
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
        raise CampaignFrontierClosureError(
            f"cannot reconstruct actual constructive proof body {spec.name!r}"
        ) from error
    if not check((), body, target):
        raise CampaignFrontierClosureError(
            f"unchanged intuitionistic kernel rejected campaign proof {spec.name!r}"
        )
    return body


def _reused_two_square_bodies() -> dict[str, Proof]:
    try:
        data = _two_square_artifact().read_bytes()
        if (
            len(data) != EXPECTED_TWO_SQUARE_BUNDLE_BYTES
            or sha256(data).hexdigest() != EXPECTED_TWO_SQUARE_BUNDLE_SHA256
        ):
            raise CampaignFrontierClosureError("immutable two-square proof bytes changed")
        bundle, _target = decode_proof_bundle(data.decode("utf-8"))
        rows = two_square_closure_plan().rows
        if len(rows) != len(bundle.nodes):
            raise CampaignFrontierClosureError("immutable two-square node count changed")
        return {row.name: bundle.nodes[row.node_id].body for row in rows}
    except (OSError, ProofBundleError, UnicodeError) as error:
        raise CampaignFrontierClosureError(
            "immutable two-square parent proof bodies are unavailable"
        ) from error


def _balanced_formula(formulas: tuple[Formula, ...]) -> Formula:
    if len(formulas) == 1:
        return formulas[0]
    midpoint = len(formulas) // 2
    return And(_balanced_formula(formulas[:midpoint]), _balanced_formula(formulas[midpoint:]))


def _balanced_proof(indices: tuple[int, ...]) -> Proof:
    if len(indices) == 1:
        return Hyp(indices[0])
    midpoint = len(indices) // 2
    return AndIntro(
        _balanced_proof(indices[:midpoint]),
        _balanced_proof(indices[midpoint:]),
    )


def _synthetic_root(
    formulas: tuple[Formula, ...],
) -> tuple[Formula, Proof]:
    if len(formulas) < 2:
        raise CampaignFrontierClosureError("campaign conjunction needs multiple endpoints")
    body = _balanced_proof(tuple(reversed(range(len(formulas)))))
    for _ in formulas:
        body = ImpIntro(body)
    return _balanced_formula(formulas), body


def check_campaign_frontier_proof_bundle(
    bundle: ProofBundle,
    target: Formula,
) -> CheckedCampaignFrontierBundle:
    """Reject graph mutations and independently kernel-check every ordinary body."""

    plan = campaign_frontier_plan()
    table = _spec_table()
    positions = {row.name: row.node_id for row in plan.rows}
    if len(bundle.nodes) != len(plan.rows) + 1 or bundle.root != len(plan.rows):
        raise CampaignFrontierClosureError("campaign proof bundle changed its node surface")
    for row in plan.rows:
        spec = table[row.name]
        node = bundle.nodes[row.node_id]
        if (
            node.node_id != row.node_id
            or node.target != _closed_formula(spec.statement)
            or node.dependencies != tuple(positions[name] for name in spec.dependencies)
        ):
            raise CampaignFrontierClosureError(
                f"campaign bundle changed exact theorem {row.name!r}"
            )
    roots = tuple(positions[name] for name in plan.root_names)
    expected_target, expected_body = _synthetic_root(
        tuple(_closed_formula(table[name].statement) for name in plan.root_names)
    )
    final = bundle.nodes[-1]
    if (
        final.node_id != len(plan.rows)
        or final.dependencies != roots
        or final.target != expected_target
        or final.body != expected_body
        or target != expected_target
    ):
        raise CampaignFrontierClosureError("campaign synthetic conjunction root changed")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise CampaignFrontierClosureError(
            "unchanged intuitionistic kernel rejected a campaign frontier body"
        ) from error
    if receipt.kernel_calls != len(bundle.nodes):
        raise CampaignFrontierClosureError("campaign checker skipped an actual proof body")
    return CheckedCampaignFrontierBundle(bundle, target, receipt)


def assemble_campaign_frontier_proof_bundle(
    *,
    batch_size: int = 8,
) -> CheckedCampaignFrontierBundle:
    """Reconstruct bounded actual bodies and seal the complete endpoint graph."""

    if type(batch_size) is not int or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise CampaignFrontierClosureError("campaign proof batches must contain 1..16 rows")
    plan = campaign_frontier_plan()
    table = _spec_table()
    bodies = _reused_two_square_bodies()
    rebuilding = plan.rebuilt_rows
    for offset in range(0, len(rebuilding), batch_size):
        batch = rebuilding[offset : offset + batch_size]
        nodes = objects = 0
        for row in batch:
            proof = _reconstruct_body(table[row.name], table)
            size, identities = _body_metrics(
                proof,
                nodes=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - nodes,
                objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - objects,
            )
            nodes += size
            objects += identities
            bodies[row.name] = proof
        print(
            f"campaign frontier batch {offset // batch_size + 1}: "
            f"{len(batch)} bodies, {nodes} nodes, {objects} objects "
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
    return check_campaign_frontier_proof_bundle(
        ProofBundle(tuple(nodes), len(nodes) - 1),
        target,
    )


def _default_frontier_bundle_source() -> Path:
    pyodide = Path(PYODIDE_FRONTIER_BUNDLE_PATH)
    return pyodide if pyodide.is_file() else _repository_artifact(FRONTIER_ARTIFACT_FILENAME)


@lru_cache(maxsize=1)
def checked_campaign_frontier_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Open frozen exact bytes and independently check every genuine proof body."""

    try:
        data = _default_frontier_bundle_source().read_bytes()
        if (
            len(data) != EXPECTED_FRONTIER_BUNDLE_BYTES
            or sha256(data).hexdigest() != EXPECTED_FRONTIER_BUNDLE_SHA256
        ):
            raise CampaignFrontierClosureError("frozen campaign frontier artifact changed")
        bundle, target = decode_proof_bundle(data.decode("utf-8"))
        result = check_campaign_frontier_proof_bundle(bundle, target)
    except (OSError, ProofBundleError, UnicodeError) as error:
        raise CampaignFrontierClosureError("campaign frontier artifact is unavailable") from error
    if result.receipt.total_body_nodes != EXPECTED_FRONTIER_BUNDLE_BODY_PROOF_NODES:
        raise CampaignFrontierClosureError("frozen campaign frontier body accounting changed")
    return result.bundle, result.receipt


def export_campaign_frontier_proof_bundle(
    output: str | Path,
    *,
    batch_size: int = 8,
) -> CheckedCampaignFrontierBundle:
    """Build and write a canonical, genuinely checked constructive proof bundle."""

    result = assemble_campaign_frontier_proof_bundle(batch_size=batch_size)
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    print(
        f"campaign frontier bundle: {len(payload.encode())} bytes; "
        f"sha256={sha256(payload.encode()).hexdigest()}; "
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
    export_campaign_frontier_proof_bundle(arguments.output, batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CampaignFrontierClosureError",
    "CampaignFrontierPlan",
    "CampaignFrontierRow",
    "CheckedCampaignFrontierBundle",
    "EXPECTED_FRONTIER_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_FRONTIER_BUNDLE_BYTES",
    "EXPECTED_FRONTIER_BUNDLE_SHA256",
    "FRONTIER_ARTIFACT_FILENAME",
    "PYODIDE_FRONTIER_BUNDLE_PATH",
    "assemble_campaign_frontier_proof_bundle",
    "campaign_frontier_plan",
    "check_campaign_frontier_proof_bundle",
    "checked_campaign_frontier_proof_bundle",
    "export_campaign_frontier_proof_bundle",
]
