"""Bounded, self-contained original-kernel closure of first-wave campaigns.

Only the actual transitive proof cone is retained. Immutable historical proof
bodies are read from the smallest available certificate providers, one file at
a time; new and unavailable bodies are reconstructed in capped microbatches.
The closure has no dependency on the new enrollment/edition modules, avoiding
a circular authority chain. A content digest never substitutes for a proof.
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

from ..kernel.formulas import Formula
from ..kernel.proofs import Proof
from . import editions_v25 as v25
from .campaign_breakthrough_layer_closure import (
    BREAKTHROUGH_LAYER_ARTIFACT_FILENAME,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_BYTES,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256,
    _ParentProvider,
    _balanced_formula,
    _balanced_proof,
    _parent_providers as _historical_parent_providers,
    _reconstruct_body,
    breakthrough_layer_plan,
)
from .coprime_square_factor_candidate import make_coprime_square_factor_candidate_theorems
from .fermat_four_descent_candidate import make_fermat_four_descent_candidate_theorems
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
from .pythagorean_inverse_candidate import make_pythagorean_inverse_candidate_theorems
from .theorems import TheoremSpec, _closed_formula


FIRST_WAVE_ARTIFACT_FILENAME = "alpha-v26-first-wave-proof-bundle-v1.json"
PYODIDE_FIRST_WAVE_BUNDLE_PATH = f"/lab/proof-artifacts/{FIRST_WAVE_ARTIFACT_FILENAME}"
PARENT_ALPHA_V25_COUNT = 2_080
PARENT_ALPHA_V25_IDENTITY_SHA256 = "3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28"
PARENT_ALPHA_V25_ENROLLMENT_SHA256 = "f724872707cdcf401f35cb69680e1bbec86d626c4bf56e6d41f01a3724e2be81"

# Frozen only after all 216 ordinary bodies and their exact dependency graph
# were accepted by both the unchanged HA kernel and compiled Lean verifier.
EXPECTED_FIRST_WAVE_FRONTIER_COUNT = 58
EXPECTED_FIRST_WAVE_FRONTIER_NAMES_SHA256 = "226cc91137521e0484dc6c3dcf90d2138e67acc79bf53798d84fb0deaf5973de"
EXPECTED_FIRST_WAVE_THEOREM_COUNT = 215
EXPECTED_FIRST_WAVE_ROOT_COUNT = 4
EXPECTED_FIRST_WAVE_DEPENDENCY_EDGE_COUNT = 554
EXPECTED_FIRST_WAVE_ORDERED_NAMES_SHA256 = "042e885b14e221f86cc724a815af4069dabffef18cac71425e54f6f7c4c1d0dc"
EXPECTED_FIRST_WAVE_SOURCE_COUNTS: dict[str, int] = {
    "new": 58,
    "parent_rebuild": 10,
    "v19_frontier": 65,
    "v21_advanced_layer": 5,
    "v22_transport_layer": 1,
    "v24_research_layer": 64,
    "v25_breakthrough_layer": 12,
}
EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT = 216
EXPECTED_FIRST_WAVE_BUNDLE_EDGE_COUNT = 558
EXPECTED_FIRST_WAVE_BUNDLE_BODY_PROOF_NODES = 10_397
EXPECTED_FIRST_WAVE_BUNDLE_BYTES = 364_186
EXPECTED_FIRST_WAVE_BUNDLE_SHA256 = "59afca707b33b68df907c941683e335492f7de12ee3888219339c5dfce8ec4fc"


class FirstWaveError(ValueError):
    """An actual theorem, historical proof, resource cap, or release seal failed."""


@dataclass(frozen=True, slots=True)
class FirstWaveRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    source: str
    new_theorem: bool


@dataclass(frozen=True, slots=True)
class FirstWavePlan:
    parent_alpha_identity_sha256: str
    parent_alpha_enrollment_sha256: str
    rows: tuple[FirstWaveRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str

    @property
    def rebuilt_rows(self) -> tuple[FirstWaveRow, ...]:
        return tuple(row for row in self.rows if row.source in {"parent_rebuild", "new"})


@dataclass(frozen=True, slots=True)
class CheckedFirstWaveBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle


def _artifact_path(filename: str) -> Path:
    browser = Path("/lab/proof-artifacts") / filename
    if browser.is_file():
        return browser
    return Path(__file__).resolve().parents[4] / "research/arithmetic-library/artifacts" / filename


@lru_cache(maxsize=1)
def first_wave_specs() -> tuple[TheoremSpec, ...]:
    """Return the three real candidate inventories in proof-dependency order."""

    return (
        *make_coprime_square_factor_candidate_theorems(TheoremSpec),
        *make_pythagorean_inverse_candidate_theorems(TheoremSpec),
        *make_fermat_four_descent_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _parent_providers() -> tuple[_ParentProvider, ...]:
    current = _ParentProvider(
        label="v25_breakthrough_layer",
        filename=BREAKTHROUGH_LAYER_ARTIFACT_FILENAME,
        bytes=EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_BYTES,
        digest=EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256,
        rows=breakthrough_layer_plan().rows,
    )
    return tuple(sorted((*_historical_parent_providers(), current), key=lambda item: item.bytes))


def _sealed_plan(plan: FirstWavePlan) -> None:
    if not EXPECTED_FIRST_WAVE_THEOREM_COUNT:
        return
    if (
        len(plan.frontier_names) != EXPECTED_FIRST_WAVE_FRONTIER_COUNT
        or sha256("\n".join(plan.frontier_names).encode()).hexdigest() != EXPECTED_FIRST_WAVE_FRONTIER_NAMES_SHA256
        or len(plan.rows) != EXPECTED_FIRST_WAVE_THEOREM_COUNT
        or len(plan.root_names) != EXPECTED_FIRST_WAVE_ROOT_COUNT
        or plan.dependency_edge_count != EXPECTED_FIRST_WAVE_DEPENDENCY_EDGE_COUNT
        or plan.ordered_names_sha256 != EXPECTED_FIRST_WAVE_ORDERED_NAMES_SHA256
        or Counter(row.source for row in plan.rows) != EXPECTED_FIRST_WAVE_SOURCE_COUNTS
    ):
        raise FirstWaveError("the frozen Alpha-v26 first-wave dependency cone changed")


@lru_cache(maxsize=1)
def first_wave_plan() -> FirstWavePlan:
    """Select the exact complete transitive cone of every new maximal theorem."""

    if (
        len(v25.ALPHA_ENTRIES) != PARENT_ALPHA_V25_COUNT
        or len(v25.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V25_COUNT
        or v25.ALPHA_V25_IDENTITY_SHA256 != PARENT_ALPHA_V25_IDENTITY_SHA256
        or v25.ALPHA_V25_ENROLLMENT_SHA256 != PARENT_ALPHA_V25_ENROLLMENT_SHA256
    ):
        raise FirstWaveError("the exact fully checked Alpha-v25 parent changed")
    frontier_specs = first_wave_specs()
    specifications = (*v25.ALPHA_CHECKED_SPECS, *frontier_specs)
    table = {item.name: item for item in specifications}
    if len(table) != len(specifications):
        raise FirstWaveError("the first-wave proof inventory repeats a theorem")
    frontier_names = tuple(item.name for item in frontier_specs)
    used = {dependency for item in frontier_specs for dependency in item.dependencies}
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise FirstWaveError("the first-wave campaign has no maximal theorem")
    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = table.get(name)
        if item is None:
            raise FirstWaveError(f"unknown actual proof dependency {name!r}")
        selected.add(name)
        pending.extend(item.dependencies)
    providers = tuple(
        (provider.label, frozenset(row.name for row in provider.rows))
        for provider in _parent_providers()
    )
    new_names = frozenset(frontier_names)
    seen: set[str] = set()
    rows: list[FirstWaveRow] = []
    for alpha_index, item in enumerate(specifications):
        if item.name not in selected:
            continue
        if not set(item.dependencies) <= seen:
            raise FirstWaveError(f"forward dependency in actual theorem {item.name!r}")
        new = item.name in new_names
        source = "new" if new else next(
            (label for label, available in providers if item.name in available), "parent_rebuild"
        )
        rows.append(FirstWaveRow(
            node_id=len(rows), alpha_index=alpha_index, name=item.name,
            statement_sha256=sha256(item.statement.encode()).hexdigest(),
            dependencies=item.dependencies, source=source, new_theorem=new,
        ))
        seen.add(item.name)
    if not new_names <= seen:
        raise FirstWaveError("the complete proof cone omitted a new theorem")
    plan = FirstWavePlan(
        parent_alpha_identity_sha256=PARENT_ALPHA_V25_IDENTITY_SHA256,
        parent_alpha_enrollment_sha256=PARENT_ALPHA_V25_ENROLLMENT_SHA256,
        rows=tuple(rows), root_names=roots, frontier_names=frontier_names,
        dependency_edge_count=sum(len(row.dependencies) for row in rows),
        ordered_names_sha256=sha256("\n".join(row.name for row in rows).encode()).hexdigest(),
    )
    _sealed_plan(plan)
    return plan


def _spec_table() -> dict[str, TheoremSpec]:
    return {item.name: item for item in (*v25.ALPHA_CHECKED_SPECS, *first_wave_specs())}


def _body_metrics(proof: Proof, *, nodes: int, objects: int) -> tuple[int, int]:
    """Charge actual immutable proof identities, not proof depth, to a batch."""

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        occurrences, identities, _depth, _annotations, _envelope = _proof_envelope_metrics_bounded(
            proof, max_proof_occurrences=nodes, max_proof_objects=objects,
            max_proof_depth=limits.max_body_depth,
            max_annotation_occurrences=limits.max_body_annotation_occurrences,
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_body_envelope_depth,
            label="constructive first-wave body",
        )
    except (AttributeError, LayeredReplayError, RecursionError, TypeError, ValueError) as error:
        raise FirstWaveError("first-wave body exceeds unchanged 125000-node/25000-object caps") from error
    return occurrences, identities


def _reused_parent_bodies() -> dict[str, Proof]:
    plan, table = first_wave_plan(), _spec_table()
    bodies: dict[str, Proof] = {}
    for provider in _parent_providers():
        wanted = frozenset(row.name for row in plan.rows if row.source == provider.label)
        if not wanted:
            continue
        try:
            data = _artifact_path(provider.filename).read_bytes()
            if len(data) != provider.bytes or sha256(data).hexdigest() != provider.digest:
                raise FirstWaveError(f"frozen historical proof artifact changed: {provider.filename}")
            bundle, _target = decode_proof_bundle(data.decode("utf-8"))
            del data
            rows = {row.name: row for row in provider.rows}
            positions = {row.name: row.node_id for row in provider.rows}
            if not wanted <= rows.keys():
                raise FirstWaveError(f"provider {provider.label!r} lost a needed theorem")
            for name in wanted:
                row = rows[name]
                if row.node_id >= len(bundle.nodes):
                    raise FirstWaveError(f"missing historical proof body {name!r}")
                node, specification = bundle.nodes[row.node_id], table[name]
                if (
                    node.node_id != row.node_id
                    or node.target != _closed_formula(specification.statement)
                    or node.dependencies != tuple(positions[dependency] for dependency in specification.dependencies)
                ):
                    raise FirstWaveError(f"historical proof surface changed: {name!r}")
                bodies[name] = node.body
            print(f"first-wave parent {provider.label}: retained {len(wanted)} actual bodies", flush=True)
            del bundle
            gc.collect()
        except FirstWaveError:
            raise
        except (KeyError, OSError, ProofBundleError, UnicodeError) as error:
            raise FirstWaveError(f"historical proof artifact unavailable: {provider.filename}") from error
    if len(bodies) != sum(row.source not in {"new", "parent_rebuild"} for row in plan.rows):
        raise FirstWaveError("incomplete historical ordinary-proof inventory")
    return bodies


def _synthetic_root(formulas: tuple[Formula, ...]) -> tuple[Formula, Proof]:
    from ..kernel.proofs import ImpIntro

    if not formulas:
        raise FirstWaveError("an empty synthetic packaging root is invalid")
    if EXPECTED_FIRST_WAVE_ROOT_COUNT and len(formulas) != EXPECTED_FIRST_WAVE_ROOT_COUNT:
        raise FirstWaveError("the frozen synthetic endpoint inventory changed")
    proof = _balanced_proof(tuple(reversed(range(len(formulas)))))
    for _ in formulas:
        proof = ImpIntro(proof)
    return _balanced_formula(formulas), proof


def check_first_wave_proof_bundle(bundle: ProofBundle, target: Formula) -> CheckedFirstWaveBundle:
    """Independently verify every actual body, target, edge, and final conjunction."""

    plan, table = first_wave_plan(), _spec_table()
    positions = {row.name: row.node_id for row in plan.rows}
    count = len(plan.rows) + 1
    if (
        type(bundle) is not ProofBundle or len(bundle.nodes) != count
        or bundle.root != len(plan.rows)
        or (EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT and count != EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT)
    ):
        raise FirstWaveError("the first-wave proof bundle changed its exact nodes")
    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        if (
            type(node) is not BundleNode or node.node_id != row.node_id
            or node.target != _closed_formula(table[row.name].statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)
        ):
            raise FirstWaveError(f"first-wave proof changed exact theorem {row.name!r}")
    expected_target, expected_body = _synthetic_root(
        tuple(_closed_formula(table[name].statement) for name in plan.root_names)
    )
    final = bundle.nodes[-1]
    if (
        final.node_id != len(plan.rows)
        or final.dependencies != tuple(positions[name] for name in plan.root_names)
        or final.target != expected_target or final.body != expected_body or target != expected_target
    ):
        raise FirstWaveError("the exact synthetic conjunction root changed")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise FirstWaveError("the unchanged intuitionistic kernel rejected a first-wave body") from error
    edges = plan.dependency_edge_count + len(plan.root_names)
    if (
        receipt.kernel_calls != count or receipt.node_count != count or receipt.dependency_edges != edges
        or (EXPECTED_FIRST_WAVE_BUNDLE_EDGE_COUNT and edges != EXPECTED_FIRST_WAVE_BUNDLE_EDGE_COUNT)
    ):
        raise FirstWaveError("the kernel omitted an actual proof body or edge")
    return CheckedFirstWaveBundle(bundle, target, receipt)


def assemble_first_wave_proof_bundle(*, batch_size: int = 1) -> CheckedFirstWaveBundle:
    """Reconstruct bounded batches, then check the complete closed dependency DAG."""

    if type(batch_size) is not int or not 1 <= batch_size <= MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FirstWaveError("first-wave proof batches must contain 1..16 rows")
    plan, table = first_wave_plan(), _spec_table()
    bodies = _reused_parent_bodies()
    rows = plan.rebuilt_rows
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset:offset + batch_size]
        proof_nodes = proof_objects = 0
        for row in batch:
            try:
                body = _reconstruct_body(table[row.name], table)
                occurrences, identities = _body_metrics(
                    body, nodes=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES - proof_nodes,
                    objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS - proof_objects,
                )
            except (AttributeError, RecursionError, TypeError, ValueError) as error:
                raise FirstWaveError(f"cannot construct a bounded original proof of {row.name!r}") from error
            proof_nodes += occurrences
            proof_objects += identities
            bodies[row.name] = body
        print(
            f"first-wave batch {offset // batch_size + 1}: {len(batch)} bodies, {proof_nodes} nodes, "
            f"{proof_objects} objects ({min(offset + batch_size, len(rows))}/{len(rows)})", flush=True,
        )
    positions = {row.name: row.node_id for row in plan.rows}
    nodes = [
        BundleNode(row.node_id, _closed_formula(table[row.name].statement),
                   tuple(positions[name] for name in row.dependencies), bodies[row.name])
        for row in plan.rows
    ]
    target, synthetic = _synthetic_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    nodes.append(BundleNode(len(nodes), target, tuple(positions[name] for name in plan.root_names), synthetic))
    return check_first_wave_proof_bundle(ProofBundle(tuple(nodes), len(nodes) - 1), target)


@lru_cache(maxsize=1)
def checked_first_wave_proof_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    """Accept sealed artifact bytes only after every unchanged-kernel check."""

    counts = (
        EXPECTED_FIRST_WAVE_FRONTIER_COUNT, EXPECTED_FIRST_WAVE_THEOREM_COUNT,
        EXPECTED_FIRST_WAVE_ROOT_COUNT, EXPECTED_FIRST_WAVE_DEPENDENCY_EDGE_COUNT,
        EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT, EXPECTED_FIRST_WAVE_BUNDLE_EDGE_COUNT,
        EXPECTED_FIRST_WAVE_BUNDLE_BYTES, EXPECTED_FIRST_WAVE_BUNDLE_BODY_PROOF_NODES,
    )
    digests = (
        EXPECTED_FIRST_WAVE_FRONTIER_NAMES_SHA256,
        EXPECTED_FIRST_WAVE_ORDERED_NAMES_SHA256, EXPECTED_FIRST_WAVE_BUNDLE_SHA256,
    )
    if (
        any(type(value) is not int or value <= 0 for value in counts)
        or any(len(value) != 64 or any(character not in "0123456789abcdef" for character in value) for value in digests)
        or not EXPECTED_FIRST_WAVE_SOURCE_COUNTS
    ):
        raise FirstWaveError("the first-wave proof artifact has not been frozen")
    try:
        payload = _artifact_path(FIRST_WAVE_ARTIFACT_FILENAME).read_bytes()
        if len(payload) != EXPECTED_FIRST_WAVE_BUNDLE_BYTES or sha256(payload).hexdigest() != EXPECTED_FIRST_WAVE_BUNDLE_SHA256:
            raise FirstWaveError("the sealed first-wave proof artifact changed")
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        result = check_first_wave_proof_bundle(bundle, target)
    except FirstWaveError:
        raise
    except (OSError, ProofBundleError, UnicodeError) as error:
        raise FirstWaveError("the first-wave proof artifact is unavailable") from error
    if result.receipt.total_body_nodes != EXPECTED_FIRST_WAVE_BUNDLE_BODY_PROOF_NODES:
        raise FirstWaveError("frozen first-wave proof-body accounting changed")
    return result.bundle, result.receipt


def export_first_wave_proof_bundle(output: str | Path, *, batch_size: int = 1) -> CheckedFirstWaveBundle:
    result = assemble_first_wave_proof_bundle(batch_size=batch_size)
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    encoded = payload.encode("utf-8")
    print(
        f"first-wave proof bundle: {len(encoded)} bytes; sha256={sha256(encoded).hexdigest()}; "
        f"nodes={result.receipt.node_count}; edges={result.receipt.dependency_edges}; "
        f"body-nodes={result.receipt.total_body_nodes}", flush=True,
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-size", type=int, default=1)
    arguments = parser.parse_args(argv)
    export_first_wave_proof_bundle(arguments.output, batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "FIRST_WAVE_ARTIFACT_FILENAME", "PYODIDE_FIRST_WAVE_BUNDLE_PATH",
    "FirstWaveError", "FirstWaveRow", "FirstWavePlan", "CheckedFirstWaveBundle",
    "EXPECTED_FIRST_WAVE_FRONTIER_COUNT", "EXPECTED_FIRST_WAVE_FRONTIER_NAMES_SHA256",
    "EXPECTED_FIRST_WAVE_THEOREM_COUNT", "EXPECTED_FIRST_WAVE_ROOT_COUNT",
    "EXPECTED_FIRST_WAVE_DEPENDENCY_EDGE_COUNT", "EXPECTED_FIRST_WAVE_ORDERED_NAMES_SHA256",
    "EXPECTED_FIRST_WAVE_SOURCE_COUNTS", "EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT",
    "EXPECTED_FIRST_WAVE_BUNDLE_EDGE_COUNT", "EXPECTED_FIRST_WAVE_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_FIRST_WAVE_BUNDLE_BYTES", "EXPECTED_FIRST_WAVE_BUNDLE_SHA256",
    "first_wave_specs", "first_wave_plan", "check_first_wave_proof_bundle",
    "assemble_first_wave_proof_bundle", "checked_first_wave_proof_bundle", "export_first_wave_proof_bundle",
]
