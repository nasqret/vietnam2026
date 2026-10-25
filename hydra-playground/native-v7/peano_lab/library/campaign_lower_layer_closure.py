"""Memory-bounded, non-admitting construction of complete lower-layer proofs.

The sealed parent catalogue is only a specification and artifact locator.
Every reused body is matched against its exact target and ordered premises;
the complete self-contained result is then checked by the original kernel.
No catalogue hash, source name, historical receipt, or proof search is trusted
as a mathematical inference. No edition, kernel, or resource limit is changed.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
import gc
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Callable, Sequence

from ..engine.state import start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.formulas import And, Formula, Imp
from ..kernel.proofs import AndIntro, Hyp, ImpIntro, Proof
from .layered_replay import DEFAULT_LAYERED_REPLAY_LIMITS, _proof_envelope_metrics_bounded
from .proof_bundle import (
    BundleNode, CheckedProofBundle, ProofBundle, check_proof_bundle,
    decode_proof_bundle, encode_proof_bundle,
)
from .theorems import TheoremSpec, _closed_formula, _primitive


_MODULE_PARENTS = Path(__file__).resolve().parents
# Browser workers mount this module at /lab/peano_lab/library/*.py.  Runtime
# verification receives the exact parent specs and the self-contained bundle;
# importing it must not assume the deeper source-checkout directory layout.
ROOT = _MODULE_PARENTS[4] if len(_MODULE_PARENTS) > 4 else Path("/lab")
PARENT_CATALOG = "artifacts/peano-library/alpha/catalog-v27.json"
PARENT_CATALOG_SHA256 = "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
PARENT_COUNT = 2560
PARENT_IDENTITY_SHA256 = "5c5935ed524b63827068cba37da222fc78b458de6c5af2e07cf572bb9fab7d05"
PARENT_ENROLLMENT_SHA256 = "20866c3865baec2bc6cee3c8e54bcb2f55e95a7b1a7fc85c103e3c9b055ecf4e"
PARENT_SPECS_SHA256 = "56e4aaea9ae4177122d1215f6ae14acd9e4f1aee7f9f7faab1d18277da611633"
LOWER_LAYER_ARTIFACT_FILENAME = "alpha-v28-lower-layer-proof-bundle-v1.json"
EXPECTED_LOWER_LAYER_FRONTIER_COUNT = 204
EXPECTED_LOWER_LAYER_THEOREM_COUNT = 861
EXPECTED_LOWER_LAYER_ROOT_COUNT = 36
EXPECTED_LOWER_LAYER_DEPENDENCY_EDGE_COUNT = 3054
EXPECTED_LOWER_LAYER_ORDERED_NAMES_SHA256 = "d9900807b562cb3f6b5e40b398b4cc26e4ad0714dc5e7cc00263ada62ee73a15"
EXPECTED_LOWER_LAYER_BUNDLE_NODE_COUNT = 862
EXPECTED_LOWER_LAYER_BUNDLE_EDGE_COUNT = 3090
EXPECTED_LOWER_LAYER_BUNDLE_BODY_PROOF_NODES = 230464
EXPECTED_LOWER_LAYER_BUNDLE_BYTES = 18977050
EXPECTED_LOWER_LAYER_BUNDLE_SHA256 = "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"

# Same immutable authoring microbatch limits as frontier_promotion. Importing
# that historical module eagerly builds old editions; this standalone builder
# instead records the existing policy literally and tests the equality.
MAX_BATCH_ROWS = 16
MAX_BATCH_PROOF_NODES = 125000
MAX_BATCH_PROOF_OBJECTS = 25000


class LowerLayerError(ValueError):
    """An exact specification, artifact, proof, topology, or bound failed."""


@dataclass(frozen=True, slots=True)
class LowerLayerFactory:
    campaign: str
    module: str
    factory: str
    rfc: str


FACTORIES = (
    LowerLayerFactory("foundations", "foundation_saturation_candidate", "make_foundation_saturation_candidate_theorems", "foundation-saturation-rfc-v1.md"),
    LowerLayerFactory("foundations", "prime_factorization_permutation_candidate", "make_prime_factorization_permutation_candidate_theorems", "prime-factorization-permutation-rfc-v1.md"),
    LowerLayerFactory("gaussian_euclidean", "signed_integer_division_candidate", "make_signed_integer_division_candidate_theorems", "signed-integer-division-rfc-v1.md"),
    LowerLayerFactory("gaussian_euclidean", "gaussian_euclidean_candidate", "make_gaussian_euclidean_candidate_theorems", "gaussian-euclidean-rfc-v1.md"),
    LowerLayerFactory("eisenstein_euclidean", "eisenstein_euclidean_candidate", "make_eisenstein_euclidean_candidate_theorems", "eisenstein-euclidean-rfc-v1.md"),
    LowerLayerFactory("prime_enumeration", "prime_enumeration_candidate", "make_prime_enumeration_candidate_theorems", "prime-enumeration-rfc-v1.md"),
)


@dataclass(frozen=True, slots=True)
class ParentDocument:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ParentSnapshot:
    specs: tuple[TheoremSpec, ...]
    documents: tuple[ParentDocument, ...]


@dataclass(frozen=True, slots=True)
class LowerLayerRow:
    node_id: int
    alpha_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    campaign: str | None


@dataclass(frozen=True, slots=True)
class LowerLayerPlan:
    campaigns: tuple[str, ...]
    rows: tuple[LowerLayerRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str


@dataclass(frozen=True, slots=True)
class CheckedLowerLayerBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    origins: tuple[tuple[str, str, int | None], ...]


@lru_cache(maxsize=1)
def parent_snapshot() -> ParentSnapshot:
    data = (ROOT / PARENT_CATALOG).read_bytes()
    if sha256(data).hexdigest() != PARENT_CATALOG_SHA256:
        raise LowerLayerError("the exact immutable Alpha-v27 parent catalogue changed")
    catalog = json.loads(data)
    del data
    if (
        catalog.get("theorem_count") != PARENT_COUNT
        or catalog.get("checked_use_count") != PARENT_COUNT
        or catalog.get("stable_count") != 432
        or catalog.get("edition_identity_sha256") != PARENT_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != PARENT_ENROLLMENT_SHA256
    ):
        raise LowerLayerError("the immutable parent evidence partition or identity changed")
    specs = tuple(
        TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    )
    seen: set[str] = set()
    for row, specification in zip(catalog["theorems"], specs):
        if (
            not row.get("checked_use") or not row.get("body_checked")
            or specification.name in seen or not set(specification.dependencies) <= seen
            or sha256(specification.statement.encode()).hexdigest() != row["statement_sha256"]
        ):
            raise LowerLayerError("the pinned parent has an invalid exact theorem row")
        seen.add(specification.name)
    if len(specs) != PARENT_COUNT:
        raise LowerLayerError("the pinned parent inventory is incomplete")
    documents = tuple(sorted((
        ParentDocument(item["path"], item["bytes"], item["sha256"])
        for item in catalog["evidence_documents"]
        if item["path"].startswith("research/arithmetic-library/artifacts/")
        and item["path"].endswith("proof-bundle-v1.json")
        and ".." not in Path(item["path"]).parts
    ), key=lambda item: (item.bytes, item.path)))
    if not documents:
        raise LowerLayerError("the sealed parent has no ordinary proof providers")
    return ParentSnapshot(specs, documents)


def selected_factories(campaigns: tuple[str, ...] = ()) -> tuple[LowerLayerFactory, ...]:
    if type(campaigns) is not tuple or any(type(item) is not str for item in campaigns) or len(set(campaigns)) != len(campaigns):
        raise LowerLayerError("campaign selection must be a tuple of distinct known names")
    known = {item.campaign for item in FACTORIES}
    if not set(campaigns) <= known:
        raise LowerLayerError("unknown lower-layer campaign")
    return tuple(item for item in FACTORIES if not campaigns or item.campaign in campaigns)


@lru_cache(maxsize=16)
def lower_layer_specs(campaigns: tuple[str, ...] = ()) -> tuple[TheoremSpec, ...]:
    rows = []
    for owner in selected_factories(campaigns):
        module = import_module(f".{owner.module}", package=__package__)
        candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        if not candidates or any(type(row) is not TheoremSpec for row in candidates):
            raise LowerLayerError("a lower-layer factory has no exact ordinary theorem specs")
        rows.extend(candidates)
    return tuple(rows)


def _specs_digest(specs: tuple[TheoremSpec, ...]) -> str:
    """A streaming exact inventory pin, never a mathematical inference."""
    digest = sha256()
    for row in specs:
        record = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    return digest.hexdigest()


@lru_cache(maxsize=2)
def _validated_parent_specs(specs: tuple[TheoremSpec, ...]) -> tuple[TheoremSpec, ...]:
    if len(specs) != PARENT_COUNT or any(type(row) is not TheoremSpec for row in specs):
        raise LowerLayerError("supplied parent specification inventory changed")
    seen: set[str] = set()
    for row in specs:
        if row.name in seen or not set(row.dependencies) <= seen:
            raise LowerLayerError("supplied parent specification order or dependencies changed")
        seen.add(row.name)
    if _specs_digest(specs) != PARENT_SPECS_SHA256:
        raise LowerLayerError("supplied parent differs from the exact immutable v27 specifications")
    return specs


def _parent_specs(supplied: tuple[TheoremSpec, ...] | None) -> tuple[TheoremSpec, ...]:
    if supplied is None:
        return parent_snapshot().specs
    if type(supplied) is not tuple:
        raise LowerLayerError("supplied parent specifications must be an exact tuple")
    return _validated_parent_specs(supplied)


def _table(campaigns: tuple[str, ...], parent_specs: tuple[TheoremSpec, ...] | None = None) -> dict[str, TheoremSpec]:
    return {row.name: row for row in (*_parent_specs(parent_specs), *lower_layer_specs(campaigns))}


@lru_cache(maxsize=16)
def lower_layer_plan(campaigns: tuple[str, ...] = (), *, parent_specs: tuple[TheoremSpec, ...] | None = None) -> LowerLayerPlan:
    factories = selected_factories(campaigns)
    parent, frontier = _parent_specs(parent_specs), lower_layer_specs(campaigns)
    inventory = (*parent, *frontier)
    table = {row.name: row for row in inventory}
    if len(table) != len(inventory):
        raise LowerLayerError("the additive theorem inventory repeats a parent or candidate name")
    campaign_by_name = {}
    for owner in factories:
        module = import_module(f".{owner.module}", package=__package__)
        for row in getattr(module, owner.factory)(TheoremSpec):
            campaign_by_name[row.name] = owner.campaign
    used = {dependency for row in frontier for dependency in row.dependencies}
    frontier_names = tuple(row.name for row in frontier)
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise LowerLayerError("the requested inventory has no maximal theorem")
    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        if name not in table:
            raise LowerLayerError(f"missing actual proof dependency {name!r}")
        selected.add(name)
        pending.extend(table[name].dependencies)
    seen: set[str] = set()
    rows = []
    for alpha_index, row in enumerate(inventory):
        if row.name not in selected:
            continue
        if not set(row.dependencies) <= seen or len(row.dependencies) != len(set(row.dependencies)):
            raise LowerLayerError(f"non-topological actual proof dependencies in {row.name!r}")
        if not row.script or any(command.startswith("use ") or "DNE" in command for command in row.script):
            raise LowerLayerError(f"implicit or classical authority requested by {row.name!r}")
        rows.append(LowerLayerRow(len(rows), alpha_index, row.name, sha256(row.statement.encode()).hexdigest(), row.dependencies, campaign_by_name.get(row.name)))
        seen.add(row.name)
    if not set(frontier_names) <= seen:
        raise LowerLayerError("the complete proof cone omitted a requested new theorem")
    return LowerLayerPlan(
        tuple(dict.fromkeys(owner.campaign for owner in factories)), tuple(rows), roots,
        frontier_names, sum(len(row.dependencies) for row in rows),
        sha256("\n".join(row.name for row in rows).encode()).hexdigest(),
    )


def _balanced_formula(formulas: tuple[Formula, ...]) -> Formula:
    if len(formulas) == 1:
        return formulas[0]
    middle = len(formulas) // 2
    return And(_balanced_formula(formulas[:middle]), _balanced_formula(formulas[middle:]))


def _balanced_proof(indices: tuple[int, ...]) -> Proof:
    if len(indices) == 1:
        return Hyp(indices[0])
    middle = len(indices) // 2
    return AndIntro(_balanced_proof(indices[:middle]), _balanced_proof(indices[middle:]))


def _packaging_root(formulas: tuple[Formula, ...]) -> tuple[Formula, Proof]:
    if not formulas:
        raise LowerLayerError("an empty packaging root is invalid")
    proof = _balanced_proof(tuple(reversed(range(len(formulas)))))
    for _ in formulas:
        proof = ImpIntro(proof)
    return _balanced_formula(formulas), proof


def _reconstruct_body(row: TheoremSpec, table: dict[str, TheoremSpec]) -> Proof:
    target = _closed_formula(row.statement)
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(table[dependency].statement), target)
    state = start(target)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
        tactic, arguments = _primitive(command)
        if tactic == "use" or "DNE" in command:
            raise LowerLayerError("implicit authority is forbidden in ordinary body reconstruction")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


def validate_parent_provider_bytes() -> tuple[ParentDocument, ...]:
    """Authenticate every frozen parent provider, including unused providers.

    This is a provenance gate, not mathematical authority.  Reused bodies
    still undergo exact target/dependency matching and full kernel checking.
    Browser checked use does not call this source-checkout audit.
    """
    documents = parent_snapshot().documents
    for document in documents:
        payload = (ROOT / document.path).read_bytes()
        if len(payload) != document.bytes or sha256(payload).hexdigest() != document.sha256:
            raise LowerLayerError(f"sealed historical proof bytes changed: {document.path}")
    return documents


def _reused_bodies(plan: LowerLayerPlan, table: dict[str, TheoremSpec], report: Callable[[str], None]) -> tuple[dict[str, Proof], dict[str, tuple[str, int | None]]]:
    wanted = {row.name for row in plan.rows if row.campaign is None}
    candidates: dict[int, list[str]] = defaultdict(list)
    targets = {name: _closed_formula(table[name].statement) for name in wanted}
    for name, formula in targets.items():
        candidates[hash(formula)].append(name)
    bodies, origins = {}, {}
    for document in validate_parent_provider_bytes():
        if not wanted:
            break
        data = (ROOT / document.path).read_bytes()
        if len(data) != document.bytes or sha256(data).hexdigest() != document.sha256:
            raise LowerLayerError(f"sealed historical proof bytes changed: {document.path}")
        bundle, _ = decode_proof_bundle(data.decode("utf-8"))
        del data
        nodes = {node.node_id: node for node in bundle.nodes}
        retained = 0
        for node in bundle.nodes:
            for name in candidates.get(hash(node.target), ()):
                if name not in wanted or node.target != targets[name]:
                    continue
                dependencies = table[name].dependencies
                if len(dependencies) != len(node.dependencies) or any(
                    identifier not in nodes or nodes[identifier].target != targets.get(dependency, _closed_formula(table[dependency].statement))
                    for identifier, dependency in zip(node.dependencies, dependencies)
                ):
                    continue
                # Matching is only a reuse optimization. This body and every
                # actual prerequisite are independently checked below.
                bodies[name] = node.body
                origins[name] = (document.path, node.node_id)
                wanted.remove(name)
                retained += 1
        report(f"lower-layer provider {Path(document.path).name}: retained {retained} actual bodies; missing {len(wanted)}")
        del bundle, nodes
        gc.collect()
    return bodies, origins


def check_lower_layer_proof_bundle(bundle: ProofBundle, target: Formula, *, campaigns: tuple[str, ...] = (), parent_specs: tuple[TheoremSpec, ...] | None = None) -> CheckedProofBundle:
    plan = lower_layer_plan(campaigns, parent_specs=parent_specs)
    table = _table(campaigns, parent_specs)
    positions = {row.name: row.node_id for row in plan.rows}
    if type(bundle) is not ProofBundle or len(bundle.nodes) != len(plan.rows) + 1 or bundle.root != len(plan.rows):
        raise LowerLayerError("the exact lower-layer node inventory or root changed")
    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        if (
            type(node) is not BundleNode or node.node_id != row.node_id
            or node.target != _closed_formula(table[row.name].statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)
        ):
            raise LowerLayerError(f"changed exact target or dependency edge for {row.name!r}")
    expected_target, expected_body = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    final = bundle.nodes[-1]
    if (
        final.node_id != len(plan.rows) or final.target != expected_target
        or final.dependencies != tuple(positions[name] for name in plan.root_names)
        or final.body != expected_body or target != expected_target
    ):
        raise LowerLayerError("the complete conjunction packaging root changed")
    receipt = check_proof_bundle(bundle, target)
    if receipt.kernel_calls != len(bundle.nodes) or receipt.dependency_edges != plan.dependency_edge_count + len(plan.root_names):
        raise LowerLayerError("not every actual proof body and dependency reached the kernel")
    return receipt


def checked_lower_layer_proof_bundle(*, parent_specs: tuple[TheoremSpec, ...] | None = None) -> tuple[ProofBundle, CheckedProofBundle]:
    """Read exact sealed bytes and check every ordinary body; no replay cache."""
    if (
        EXPECTED_LOWER_LAYER_FRONTIER_COUNT <= 0
        or EXPECTED_LOWER_LAYER_THEOREM_COUNT <= 0
        or EXPECTED_LOWER_LAYER_BUNDLE_BYTES <= 0
        or len(EXPECTED_LOWER_LAYER_ORDERED_NAMES_SHA256) != 64
        or len(EXPECTED_LOWER_LAYER_BUNDLE_SHA256) != 64
    ):
        raise LowerLayerError("the lower-layer release is not sealed for checked use")
    browser = Path("/lab/proof-artifacts") / LOWER_LAYER_ARTIFACT_FILENAME
    source = browser if browser.is_file() else ROOT / "research/arithmetic-library/artifacts" / LOWER_LAYER_ARTIFACT_FILENAME
    payload = source.read_bytes()
    if len(payload) != EXPECTED_LOWER_LAYER_BUNDLE_BYTES or sha256(payload).hexdigest() != EXPECTED_LOWER_LAYER_BUNDLE_SHA256:
        raise LowerLayerError("the immutable lower-layer proof artifact changed")
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    plan = lower_layer_plan(parent_specs=parent_specs)
    if (len(plan.frontier_names) != EXPECTED_LOWER_LAYER_FRONTIER_COUNT
        or len(plan.rows) != EXPECTED_LOWER_LAYER_THEOREM_COUNT
        or len(plan.root_names) != EXPECTED_LOWER_LAYER_ROOT_COUNT
        or plan.dependency_edge_count != EXPECTED_LOWER_LAYER_DEPENDENCY_EDGE_COUNT
        or plan.ordered_names_sha256 != EXPECTED_LOWER_LAYER_ORDERED_NAMES_SHA256):
        raise LowerLayerError("the exact sealed lower-layer inventory changed")
    receipt = check_lower_layer_proof_bundle(bundle, target, parent_specs=parent_specs)
    if (receipt.node_count != EXPECTED_LOWER_LAYER_BUNDLE_NODE_COUNT
        or receipt.kernel_calls != EXPECTED_LOWER_LAYER_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_LOWER_LAYER_BUNDLE_EDGE_COUNT
        or receipt.total_body_nodes != EXPECTED_LOWER_LAYER_BUNDLE_BODY_PROOF_NODES):
        raise LowerLayerError("the sealed lower-layer original-kernel metrics changed")
    return bundle, receipt


def assemble_lower_layer_proof_bundle(*, campaigns: tuple[str, ...] = (), batch_size: int = 1, report: Callable[[str], None] = print) -> CheckedLowerLayerBundle:
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH_ROWS:
        raise LowerLayerError("lower-layer authoring batches must contain 1..16 rows")
    plan, table = lower_layer_plan(campaigns), _table(campaigns)
    bodies, origins = _reused_bodies(plan, table, report)
    rebuilt = tuple(row for row in plan.rows if row.name not in bodies)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    for offset in range(0, len(rebuilt), batch_size):
        nodes = objects = 0
        batch = rebuilt[offset:offset + batch_size]
        for row in batch:
            body = _reconstruct_body(table[row.name], table)
            count, identities, *_ = _proof_envelope_metrics_bounded(
                body, max_proof_occurrences=MAX_BATCH_PROOF_NODES - nodes,
                max_proof_objects=MAX_BATCH_PROOF_OBJECTS - objects,
                max_proof_depth=limits.max_body_depth,
                max_annotation_occurrences=limits.max_body_annotation_occurrences,
                max_annotation_depth=limits.max_formula_depth,
                max_envelope_depth=limits.max_body_envelope_depth,
                label=f"lower-layer body {row.name}",
            )
            nodes += count
            objects += identities
            bodies[row.name] = body
            origins[row.name] = ("new_script" if row.campaign else "parent_script", None)
        report(f"lower-layer batch {offset // batch_size + 1}: {len(batch)} actual bodies, {nodes} nodes, {objects} objects ({min(offset + batch_size, len(rebuilt))}/{len(rebuilt)})")
        gc.collect()
    positions = {row.name: row.node_id for row in plan.rows}
    nodes = [BundleNode(row.node_id, _closed_formula(table[row.name].statement), tuple(positions[name] for name in row.dependencies), bodies[row.name]) for row in plan.rows]
    target, proof = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    nodes.append(BundleNode(len(nodes), target, tuple(positions[name] for name in plan.root_names), proof))
    bundle = ProofBundle(tuple(nodes), len(nodes) - 1)
    receipt = check_lower_layer_proof_bundle(bundle, target, campaigns=campaigns)
    return CheckedLowerLayerBundle(bundle, target, receipt, tuple((row.name, *origins[row.name]) for row in plan.rows))


def export_lower_layer_proof_bundle(output: str | Path, *, campaigns: tuple[str, ...] = (), batch_size: int = 1) -> CheckedLowerLayerBundle:
    result = assemble_lower_layer_proof_bundle(campaigns=campaigns, batch_size=batch_size, report=lambda message: print(message, flush=True))
    payload = encode_proof_bundle(result.bundle, result.target)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8")
    raw = payload.encode("utf-8")
    print(f"lower-layer original-kernel ACCEPT: nodes={result.receipt.node_count}; edges={result.receipt.dependency_edges}; body-nodes={result.receipt.total_body_nodes}; bytes={len(raw)}; sha256={sha256(raw).hexdigest()}", flush=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--campaign", action="append", choices=tuple(dict.fromkeys(owner.campaign for owner in FACTORIES)), default=[])
    parser.add_argument("--batch-size", type=int, default=1)
    arguments = parser.parse_args(argv)
    export_lower_layer_proof_bundle(arguments.output, campaigns=tuple(arguments.campaign), batch_size=arguments.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
