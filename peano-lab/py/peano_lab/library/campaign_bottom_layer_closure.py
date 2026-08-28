"""Non-admitting complete HA proof checkpoints over immutable Alpha v30.

The input is untrusted ordinary theorem syntax, not a new library edition.
Every dependency is included and every resulting body reaches the original
checker.  Explicit seed files are freshly checked proof data, never trusted
receipts.  A successful export does not grant Alpha or Stable membership.

This development tool deliberately does not extend the current catalogue or
change any mathematical, bundle, sharing, or service resource limit.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Callable

from ..engine.tactics import TacticError
from ..kernel.checker import check
from ..kernel.formulas import Formula, Imp
from ..kernel.proofs import Proof
from .campaign_gaussian_factorization_closure import (
    compile_gaussian_factorization_replay,
)
from .campaign_lower_layer_closure import (
    MAX_BATCH_ROWS,
    MAX_BATCH_PROOF_NODES,
    MAX_BATCH_PROOF_OBJECTS,
    _packaging_root,
    _reconstruct_body,
    _specs_digest,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    intern_layered_replay_bodies,
)
from .proof_bundle import (
    DEFAULT_BUNDLE_LIMITS,
    BundleNode,
    CheckedProofBundle,
    ProofBundle,
    check_proof_bundle,
    decode_proof_bundle,
    encode_proof_bundle,
)
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


_PARENTS = Path(__file__).resolve().parents
ROOT = _PARENTS[4] if len(_PARENTS) > 4 else Path("/lab")
PARENT_CATALOG = "artifacts/peano-library/alpha/catalog-v30.json"
PARENT_CATALOG_BYTES = 66_503_303
PARENT_CATALOG_SHA256 = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
PARENT_COUNT = 3_222
PARENT_IDENTITY_SHA256 = "8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9"
PARENT_ENROLLMENT_SHA256 = "04b73a38d04d1bd8038c1712b7f4f6cc77156f97a890515524761bb1cdf71393"


class BottomLayerClosureError(ValueError):
    """A source, exact target, dependency, proof, or resource gate failed."""


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
class BottomLayerRow:
    node_id: int
    inventory_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    is_frontier: bool


@dataclass(frozen=True, slots=True)
class BottomLayerPlan:
    rows: tuple[BottomLayerRow, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    frontier_specs_sha256: str


@dataclass(frozen=True, slots=True)
class CheckedBottomLayerBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    plan: BottomLayerPlan
    origins: tuple[tuple[str, str, int | None], ...]


def _read_pinned(path: Path, size: int, digest: str) -> bytes:
    """Bound the read before hashing; a digest is provenance, not a proof."""
    if not path.is_file() or path.is_symlink() or path.stat().st_size != size:
        raise BottomLayerClosureError(f"sealed source size/type changed: {path.name}")
    with path.open("rb") as source:
        payload = source.read(size + 1)
    if len(payload) != size or sha256(payload).hexdigest() != digest:
        raise BottomLayerClosureError(f"sealed source bytes changed: {path.name}")
    return payload


@lru_cache(maxsize=1)
def parent_snapshot() -> ParentSnapshot:
    payload = _read_pinned(ROOT / PARENT_CATALOG, PARENT_CATALOG_BYTES, PARENT_CATALOG_SHA256)
    data = json.loads(payload)
    del payload
    if (
        data.get("theorem_count") != PARENT_COUNT
        or data.get("checked_use_count") != PARENT_COUNT
        or data.get("stable_count") != 432
        or data.get("edition_identity_sha256") != PARENT_IDENTITY_SHA256
        or data.get("ordered_enrollment_root_sha256") != PARENT_ENROLLMENT_SHA256
        or len(data.get("theorems", ())) != PARENT_COUNT
    ):
        raise BottomLayerClosureError("the immutable v30 inventory or Stable partition changed")
    specs = tuple(
        TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]),
                    tuple(row["script"]), row["summary"])
        for row in data["theorems"]
    )
    seen: set[str] = set()
    for record, row in zip(data["theorems"], specs, strict=True):
        if (
            record.get("checked_use") is not True
            or record.get("body_checked") is not True
            or row.name in seen
            or len(set(row.dependencies)) != len(row.dependencies)
            or not set(row.dependencies) <= seen
            or sha256(row.statement.encode()).hexdigest() != record["statement_sha256"]
        ):
            raise BottomLayerClosureError("the pinned parent contains an invalid exact theorem row")
        seen.add(row.name)
    documents = []
    paths: set[str] = set()
    for item in data["evidence_documents"]:
        path = item["path"]
        if not (path.startswith("research/arithmetic-library/artifacts/")
                and path.endswith("proof-bundle-v1.json")):
            continue
        if (Path(path).is_absolute() or ".." in Path(path).parts or path in paths
                or type(item["bytes"]) is not int or item["bytes"] < 1
                or item["bytes"] > DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
            raise BottomLayerClosureError("a pinned parent proof-provider record is malformed")
        paths.add(path)
        documents.append(ParentDocument(path, item["bytes"], item["sha256"]))
    if not documents:
        raise BottomLayerClosureError("the immutable parent has no ordinary proof providers")
    return ParentSnapshot(specs, tuple(sorted(documents, key=lambda item: (item.bytes, item.path))))


def _validate_frontier(frontier: tuple[TheoremSpec, ...]) -> None:
    if (type(frontier) is not tuple or not frontier
            or len(frontier) >= DEFAULT_BUNDLE_LIMITS.max_nodes
            or any(type(row) is not TheoremSpec for row in frontier)):
        raise BottomLayerClosureError("frontier must be a nonempty bounded tuple of exact theorem specs")
    seen: set[str] = set()
    for row in frontier:
        if (type(row.name) is not str or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", row.name) is None
                or row.name in seen or type(row.statement) is not str
                or type(row.summary) is not str or type(row.dependencies) is not tuple
                or any(type(name) is not str for name in row.dependencies)
                or len(set(row.dependencies)) != len(row.dependencies)
                or type(row.script) is not tuple or not row.script
                or any(type(command) is not str or not command.strip()
                       or command.startswith(("use ", "admit", "sorry")) or "DNE" in command
                       for command in row.script)):
            raise BottomLayerClosureError("a frontier name, script, or ordered dependency list is malformed")
        _closed_formula(row.statement)
        seen.add(row.name)


def _table(frontier: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    return {row.name: row for row in (*parent_snapshot().specs, *frontier)}


def bottom_layer_plan(frontier: tuple[TheoremSpec, ...]) -> BottomLayerPlan:
    """Plan every requested candidate's complete actual dependency cone."""
    _validate_frontier(frontier)
    parent = parent_snapshot().specs
    inventory = (*parent, *frontier)
    table = {row.name: row for row in inventory}
    if len(table) != len(inventory):
        raise BottomLayerClosureError("an additive frontier overwrites a parent or candidate name")
    available = {row.name for row in parent}
    for row in frontier:
        if not set(row.dependencies) <= available:
            raise BottomLayerClosureError(f"unknown, forward, or cyclic dependency in {row.name!r}")
        available.add(row.name)
    used = {name for row in frontier for name in row.dependencies}
    frontier_names = tuple(row.name for row in frontier)
    frontier_set = set(frontier_names)
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise BottomLayerClosureError("the frontier has no maximal theorem")
    included: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in included:
            continue
        if name not in table:
            raise BottomLayerClosureError(f"missing actual proof prerequisite {name!r}")
        included.add(name)
        pending.extend(table[name].dependencies)
    if len(included) + 1 > DEFAULT_BUNDLE_LIMITS.max_nodes:
        raise BottomLayerClosureError("complete checkpoint exceeds the unchanged bundle node limit")
    rows: list[BottomLayerRow] = []
    seen: set[str] = set()
    for index, row in enumerate(inventory):
        if row.name not in included:
            continue
        if not set(row.dependencies) <= seen:
            raise BottomLayerClosureError("the complete dependency cone is not topological")
        rows.append(BottomLayerRow(len(rows), index, row.name,
                                  sha256(row.statement.encode()).hexdigest(),
                                  row.dependencies, row.name in frontier_set))
        seen.add(row.name)
    if not frontier_set <= seen:
        raise BottomLayerClosureError("the complete checkpoint omitted a requested candidate")
    edges = sum(len(row.dependencies) for row in rows)
    if edges + len(roots) > DEFAULT_BUNDLE_LIMITS.max_edges:
        raise BottomLayerClosureError("complete checkpoint exceeds the unchanged edge limit")
    return BottomLayerPlan(tuple(rows), roots, frontier_names, edges,
                           sha256("\n".join(row.name for row in rows).encode()).hexdigest(),
                           _specs_digest(frontier))


def validate_parent_provider_bytes() -> tuple[ParentDocument, ...]:
    """Check every pinned provider, including providers outside the new cone."""
    documents = parent_snapshot().documents
    for document in documents:
        _read_pinned(ROOT / document.path, document.bytes, document.sha256)
    return documents


def _validate_seeds(seeds: tuple[str | Path, ...]) -> tuple[Path, ...]:
    if type(seeds) is not tuple or any(not isinstance(item, (str, Path)) for item in seeds):
        raise BottomLayerClosureError("proof seeds must be an explicit tuple of paths")
    paths = tuple(Path(item) for item in seeds)
    if len({str(path.resolve()) for path in paths}) != len(paths):
        raise BottomLayerClosureError("proof seed paths must be distinct")
    return paths


def _reused_bodies(
    plan: BottomLayerPlan,
    table: dict[str, TheoremSpec],
    seeds: tuple[Path, ...],
    report: Callable[[str], None],
) -> tuple[dict[str, Proof], dict[str, tuple[str, int | None]]]:
    wanted = {row.name for row in plan.rows}
    targets = {name: _closed_formula(table[name].statement) for name in wanted}
    candidates: dict[int, list[str]] = defaultdict(list)
    for name, formula in targets.items():
        candidates[hash(formula)].append(name)
    bodies: dict[str, Proof] = {}
    origins: dict[str, tuple[str, int | None]] = {}

    def retain(bundle: ProofBundle, source: str) -> int:
        nodes = {node.node_id: node for node in bundle.nodes}
        retained = 0
        for node in bundle.nodes:
            for name in candidates.get(hash(node.target), ()):
                if name not in wanted or node.target != targets[name]:
                    continue
                dependencies = table[name].dependencies
                if (len(node.dependencies) != len(dependencies)
                        or any(index not in nodes or nodes[index].target != targets[dependency]
                               for index, dependency in zip(node.dependencies, dependencies))):
                    continue
                bodies[name] = node.body
                origins[name] = (source, node.node_id)
                wanted.remove(name)
                retained += 1
        return retained

    # Always authenticate all parent providers, even if explicit checked seeds
    # happen to contain every requested body.  None of these hashes grants use.
    documents = validate_parent_provider_bytes()
    for path in seeds:
        if not path.is_file() or path.stat().st_size > DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
            raise BottomLayerClosureError("proof seed is missing or exceeds the unchanged byte limit")
        with path.open("rb") as source:
            raw = source.read(DEFAULT_BUNDLE_LIMITS.max_payload_bytes + 1)
        if len(raw) > DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
            raise BottomLayerClosureError("proof seed grew beyond the unchanged byte limit")
        bundle, target = decode_proof_bundle(raw.decode("utf-8"))
        del raw
        receipt = check_proof_bundle(bundle, target)
        retained = retain(bundle, str(path))
        report(f"bottom-layer checked seed {path.name}: {receipt.kernel_calls} kernel calls; retained {retained}")
        del bundle
        gc.collect()

    # Historical providers supply proof syntax only.  Every retained historical
    # body is checked again as part of the complete result below.
    wanted.intersection_update(row.name for row in plan.rows if not row.is_frontier)
    for document in documents:
        if not wanted:
            break
        raw = _read_pinned(ROOT / document.path, document.bytes, document.sha256)
        bundle, _ = decode_proof_bundle(raw.decode("utf-8"))
        del raw
        retained = retain(bundle, document.path)
        report(f"bottom-layer provider {Path(document.path).name}: retained {retained}; missing {len(wanted)}")
        del bundle
        gc.collect()
    return bodies, origins


def check_bottom_layer_bundle(
    frontier: tuple[TheoremSpec, ...], bundle: ProofBundle, target: Formula,
) -> CheckedProofBundle:
    """Require the exact whole inventory, then check every original HA body."""
    plan = bottom_layer_plan(frontier)
    table = _table(frontier)
    positions = {row.name: row.node_id for row in plan.rows}
    if (type(bundle) is not ProofBundle or len(bundle.nodes) != len(plan.rows) + 1
            or bundle.root != len(plan.rows)):
        raise BottomLayerClosureError("the exact complete checkpoint inventory or root changed")
    for row, node in zip(plan.rows, bundle.nodes, strict=False):
        if (type(node) is not BundleNode or node.node_id != row.node_id
                or node.target != _closed_formula(table[row.name].statement)
                or node.dependencies != tuple(positions[name] for name in row.dependencies)):
            raise BottomLayerClosureError(f"an exact target or ordered premise changed: {row.name}")
    expected_target, expected_body = _packaging_root(
        tuple(_closed_formula(table[name].statement) for name in plan.root_names)
    )
    final = bundle.nodes[-1]
    if (type(final) is not BundleNode or final.node_id != len(plan.rows)
            or final.target != expected_target or final.body != expected_body
            or final.dependencies != tuple(positions[name] for name in plan.root_names)
            or target != expected_target):
        raise BottomLayerClosureError("the exact maximal-theorem packaging root changed")
    receipt = check_proof_bundle(bundle, target)
    if (receipt.kernel_calls != len(bundle.nodes)
            or receipt.dependency_edges != plan.dependency_edge_count + len(plan.root_names)):
        raise BottomLayerClosureError("not every ordinary body or actual premise reached the kernel")
    return receipt


def assemble_bottom_layer_bundle(
    frontier: tuple[TheoremSpec, ...], *, batch_size: int = 1,
    seed_bundles: tuple[str | Path, ...] = (),
    report: Callable[[str], None] = print,
) -> CheckedBottomLayerBundle:
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH_ROWS:
        raise BottomLayerClosureError("authoring batches must contain 1..16 rows")
    seeds = _validate_seeds(seed_bundles)
    plan = bottom_layer_plan(frontier)
    table = _table(frontier)
    bodies, origins = _reused_bodies(plan, table, seeds, report)
    rebuilt = tuple(row for row in plan.rows if row.name not in bodies)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    for offset in range(0, len(rebuilt), batch_size):
        occurrences = identities = 0
        batch = rebuilt[offset:offset + batch_size]
        for row in batch:
            try:
                body = _reconstruct_body(table[row.name], table)
            except TacticError as error:
                raise BottomLayerClosureError(
                    f"ordinary HA body reconstruction failed for {row.name}: {error}"
                ) from error
            count, objects, *_ = _proof_envelope_metrics_bounded(
                body, max_proof_occurrences=MAX_BATCH_PROOF_NODES - occurrences,
                max_proof_objects=MAX_BATCH_PROOF_OBJECTS - identities,
                max_proof_depth=limits.max_body_depth,
                max_annotation_occurrences=limits.max_body_annotation_occurrences,
                max_annotation_depth=limits.max_formula_depth,
                max_envelope_depth=limits.max_body_envelope_depth,
                label=f"bottom-layer body {row.name}",
            )
            occurrences += count
            identities += objects
            bodies[row.name] = body
            origins[row.name] = ("new_script" if row.is_frontier else "parent_script", None)
        report(f"bottom-layer batch {offset // batch_size + 1}: {len(batch)} bodies, "
               f"{occurrences} nodes, {identities} objects ({min(offset + batch_size, len(rebuilt))}/{len(rebuilt)})")
        gc.collect()
    positions = {row.name: row.node_id for row in plan.rows}
    nodes = [BundleNode(row.node_id, _closed_formula(table[row.name].statement),
                        tuple(positions[name] for name in row.dependencies), bodies[row.name])
             for row in plan.rows]
    target, body = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    nodes.append(BundleNode(len(nodes), target, tuple(positions[name] for name in plan.root_names), body))
    bundle = ProofBundle(tuple(nodes), len(nodes) - 1)
    receipt = check_bottom_layer_bundle(frontier, bundle, target)
    return CheckedBottomLayerBundle(bundle, target, receipt, plan,
                                    tuple((row.name, *origins[row.name]) for row in plan.rows))


def export_bottom_layer_bundle(
    frontier: tuple[TheoremSpec, ...], output: str | Path, *, batch_size: int = 1,
    seed_bundles: tuple[str | Path, ...] = (),
) -> CheckedBottomLayerBundle:
    destination = Path(output)
    if destination.exists():
        raise BottomLayerClosureError("a mathematical checkpoint never overwrites an existing artifact")
    result = assemble_bottom_layer_bundle(frontier, batch_size=batch_size,
                                         seed_bundles=seed_bundles,
                                         report=lambda message: print(message, flush=True))
    payload = encode_proof_bundle(result.bundle, result.target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as output_file:
        output_file.write(payload)
    raw = payload.encode("utf-8")
    print(f"NON-ADMITTING bottom-layer original-kernel ACCEPT: nodes={result.receipt.node_count}; "
          f"edges={result.receipt.dependency_edges}; body-nodes={result.receipt.total_body_nodes}; "
          f"bytes={len(raw)}; sha256={sha256(raw).hexdigest()}", flush=True)
    return result


def replay_bottom_layer_theorem(
    frontier: tuple[TheoremSpec, ...], name: str, bundle: ProofBundle, target: Formula,
) -> CheckedTheorem:
    """Materialize an actual ordinary empty-context proof, without admission."""
    check_bottom_layer_bundle(frontier, bundle, target)
    plan = bottom_layer_plan(frontier)
    positions = {row.name: row.node_id for row in plan.rows}
    if type(name) is not str or name not in positions:
        raise BottomLayerClosureError("unknown actual dependency-cone theorem")
    root = positions[name]
    included: set[int] = set()
    pending = [root]
    while pending:
        position = pending.pop()
        if position not in included:
            included.add(position)
            pending.extend(bundle.nodes[position].dependencies)
    layered = LayeredReplayBundle(tuple(
        LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
        for node in bundle.nodes if node.node_id in included
    ), root)
    spec = _table(frontier)[name]
    formula = _closed_formula(spec.statement)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    interned = intern_layered_replay_bodies(layered, formula, limits=limits)
    if interned is None:
        raise BottomLayerClosureError("the theorem exceeds the unchanged sharing limits")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (original.node_id != actual.node_id or original.target != actual.target
                or original.dependencies != actual.dependencies):
            raise BottomLayerClosureError("conservative interning altered the exact proof graph")
        body_target = actual.target
        for dependency in reversed(actual.dependencies):
            body_target = Imp(bundle.nodes[dependency].target, body_target)
        if not check((), actual.body, body_target):
            raise BottomLayerClosureError("the original kernel rejected an interned body")
    # This existing compiler is generic ordinary HA syntax despite its
    # historical module name.  The original checker still judges its output.
    candidate = compile_gaussian_factorization_replay(interned, formula, limits=limits)
    if candidate is None or not check((), candidate.certificate, formula):
        raise BottomLayerClosureError("the original HA kernel/resource policy rejected the complete theorem")
    return CheckedTheorem(spec, formula, candidate.certificate, candidate.proof_nodes)
