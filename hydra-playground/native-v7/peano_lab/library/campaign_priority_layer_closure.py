"""Resource-bounded proof closure of the frozen four Alpha-v29 priority goals.

An immutable Alpha-v28 catalogue supplies specifications and exact historical
proof-artifact locations, never proof authority.  Candidate branches close
their actual dependencies, every ordinary body reaches the unchanged kernel,
and candidate exports remain separate from Alpha enrollment. The separately
sealed v29 provider below authenticates the complete four-goal artifact and
freshly checks every body. It does not import an edition or grant membership.
No kernel, cap, UI or historical artifact is edited. Later mathematical
campaigns must use a new additive release, never extend this frozen frontier.
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

from ..kernel.checker import check
from ..kernel.formulas import Formula, Imp
from ..kernel.proofs import Proof
from .campaign_lower_layer_closure import (
    _packaging_root, _reconstruct_body, _specs_digest,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS, LayeredReplayBundle, LayeredReplayNode,
    _proof_envelope_metrics_bounded, compile_layered_replay, intern_layered_replay_bodies,
)
from .proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, BundleNode, CheckedProofBundle, ProofBundle, check_proof_bundle,
    decode_proof_bundle, encode_proof_bundle,
)
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


_MODULE_PARENTS = Path(__file__).resolve().parents
ROOT = _MODULE_PARENTS[4] if len(_MODULE_PARENTS) > 4 else Path("/lab")
PARENT_CATALOG = "artifacts/peano-library/alpha/catalog-v28.json"
PARENT_CATALOG_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"
PARENT_COUNT = 2764
PARENT_IDENTITY_SHA256 = "4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b"
PARENT_ENROLLMENT_SHA256 = "75c80dffb8899dbf6f97a561322e630679d9df58416309e5c439746e96466fce"
PARENT_SPECS_SHA256 = "e80e011ab3dc4b19d9a11ce09033418c3157be91b7c905dc59db581a5bbcdc11"
PRIORITY_LAYER_ARTIFACT_FILENAME = "alpha-v29-priority-layer-proof-bundle-v1.json"
EXPECTED_PRIORITY_LAYER_FRONTIER_COUNT = 278
EXPECTED_PRIORITY_LAYER_THEOREM_COUNT = 565
EXPECTED_PRIORITY_LAYER_ROOT_COUNT = 29
EXPECTED_PRIORITY_LAYER_DEPENDENCY_EDGE_COUNT = 1661
EXPECTED_PRIORITY_LAYER_ORDERED_NAMES_SHA256 = "ce8ccc0cbbd5cac4fd5b24187c4c865f43c2a5080fd1cfdc2234ececb26bb47b"
EXPECTED_PRIORITY_LAYER_BUNDLE_NODE_COUNT = 566
EXPECTED_PRIORITY_LAYER_BUNDLE_EDGE_COUNT = 1690
EXPECTED_PRIORITY_LAYER_BUNDLE_BODY_PROOF_NODES = 38443
EXPECTED_PRIORITY_LAYER_BUNDLE_BYTES = 4200971
EXPECTED_PRIORITY_LAYER_BUNDLE_SHA256 = "4fcb3cd45e83448776abb9e33692496a7acfa98a051cae15761826a0b15fda44"

# Exactly the existing immutable authoring policy, not relaxed bounds.
MAX_BATCH_ROWS = 16
MAX_BATCH_PROOF_NODES = 125000
MAX_BATCH_PROOF_OBJECTS = 25000


class PriorityLayerError(ValueError):
    """An exact inventory, source, proof, topology or resource check failed."""


@dataclass(frozen=True, slots=True)
class PriorityLayerFactory:
    campaign: str
    module: str
    factory: str
    rfc: str
    source_sha256: str


FACTORIES = (
    PriorityLayerFactory("prime_valuation_support","prime_valuation_support_candidate","make_prime_valuation_support_candidate_theorems","prime-valuation-support-rfc-v1.md","bbd6e661a575f6a39f7a71424611da36a16d34cb6704cbae2b918387cc0f66d2"),
    PriorityLayerFactory("continued_fraction_approximation","continued_fraction_approximation_candidate","make_continued_fraction_approximation_candidate_theorems","continued-fraction-best-approximation-rfc-v1.md","a9074eacabc922aaf57dd7ef7eb5210ca23fe70679db334a8a283dfe2ad33e59"),
    PriorityLayerFactory("continued_fraction_approximation","continued_fraction_convergents_candidate","make_continued_fraction_convergents_candidate_theorems","continued-fraction-best-approximation-rfc-v1.md","f97eb7e8e34ad04b5c7089cdbf44641fe4ee00608371ea509b5fd07104d78aa9"),
    PriorityLayerFactory("euler_totient","euler_totient_count_candidate","make_euler_totient_count_candidate_theorems","euler-totient-product-rfc-v1.md","bb907716fb6a51c45f924068040a7732a7c0377b3fe4607274bd0b8f1a62cc14"),
    PriorityLayerFactory("euler_totient","euler_totient_interval_candidate","make_euler_totient_interval_candidate_theorems","euler-totient-product-rfc-v1.md","cd1b01f9645d47c1f8c02b5355f3dbd0173f47218ee7f34b01981ad0e7dce843"),
    PriorityLayerFactory("euler_totient","euler_totient_prime_step_candidate","make_euler_totient_prime_step_candidate_theorems","euler-totient-product-rfc-v1.md","179b7129bba16862808e3c2d083ffbfb8ed301d830976dcdb863d26aafd84ed2"),
    PriorityLayerFactory("euler_totient","euler_totient_algebra_candidate","make_euler_totient_algebra_candidate_theorems","euler-totient-product-rfc-v1.md","137a03f968e0487dce8444d937591617c5ba9ad57b4771c95a8d5ee99b734622"),
    PriorityLayerFactory("euler_totient","euler_totient_product_candidate","make_euler_totient_product_candidate_theorems","euler-totient-product-rfc-v1.md","98434c9fb1762f50fabc5eaa75c4bd6b7a2a0d05eaf3dc7860e6d05872076b67"),
    PriorityLayerFactory("squarefree_perfect_power","squarefree_decomposition_candidate","make_squarefree_decomposition_candidate_theorems","squarefree-decomposition-rfc-v1.md","3d4f2481e62adb13e53b6fbb70c0c22afd8c36b85ce62611686c04919f1bcec4"),
    PriorityLayerFactory("squarefree_perfect_power","perfect_power_profile_candidate","make_perfect_power_profile_candidate_theorems","perfect-power-profile-rfc-v1.md","6f29118bb08b670af9a170e95546084eb868608d3d3b853279d72fad53dded3d"),
    PriorityLayerFactory("odd_prime_lte","odd_prime_lte_candidate","make_odd_prime_lte_candidate_theorems","odd-prime-lte-rfc-v1.md","bd701478669f7a531fb4c387cf1e0949c57ef475a1675953cd5802cb43f62bdb"),
)


@dataclass(frozen=True, slots=True)
class ParentDocument:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ParentSnapshot:
    specs: tuple[TheoremSpec,...]
    documents: tuple[ParentDocument,...]


@dataclass(frozen=True, slots=True)
class PriorityLayerRow:
    node_id: int
    inventory_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str,...]
    campaign: str | None


@dataclass(frozen=True, slots=True)
class PriorityLayerPlan:
    campaigns: tuple[str,...]
    rows: tuple[PriorityLayerRow,...]
    root_names: tuple[str,...]
    frontier_names: tuple[str,...]
    dependency_edge_count: int
    ordered_names_sha256: str


@dataclass(frozen=True, slots=True)
class CheckedPriorityLayerBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    origins: tuple[tuple[str,str,int|None],...]


@lru_cache(maxsize=1)
def parent_snapshot() -> ParentSnapshot:
    raw = (ROOT/PARENT_CATALOG).read_bytes()
    if sha256(raw).hexdigest() != PARENT_CATALOG_SHA256:
        raise PriorityLayerError("the exact immutable Alpha-v28 parent catalogue changed")
    catalog = json.loads(raw)
    del raw
    if (catalog.get("theorem_count") != PARENT_COUNT
        or catalog.get("checked_use_count") != PARENT_COUNT
        or catalog.get("stable_count") != 432
        or catalog.get("edition_identity_sha256") != PARENT_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != PARENT_ENROLLMENT_SHA256):
        raise PriorityLayerError("the exact parent identity or Stable partition changed")
    specs = tuple(TheoremSpec(r["name"],r["statement"],tuple(r["dependencies"]),tuple(r["script"]),r["summary"]) for r in catalog["theorems"])
    _validated_parent_specs(specs)
    for data,row in zip(catalog["theorems"],specs):
        if (not data.get("checked_use") or not data.get("body_checked")
            or sha256(row.statement.encode()).hexdigest() != data["statement_sha256"]):
            raise PriorityLayerError("the parent catalogue contains an invalid exact theorem row")
    documents = tuple(sorted((ParentDocument(d["path"],d["bytes"],d["sha256"])
        for d in catalog["evidence_documents"]
        if d["path"].startswith("research/arithmetic-library/artifacts/")
        and d["path"].endswith("proof-bundle-v1.json")
        and ".." not in Path(d["path"]).parts),key=lambda d:(d.bytes,d.path)))
    if not documents:
        raise PriorityLayerError("the parent has no exact ordinary proof providers")
    return ParentSnapshot(specs,documents)


@lru_cache(maxsize=2)
def _validated_parent_specs(specs: tuple[TheoremSpec,...]) -> tuple[TheoremSpec,...]:
    if len(specs) != PARENT_COUNT or any(type(r) is not TheoremSpec for r in specs):
        raise PriorityLayerError("supplied parent specification inventory changed")
    seen = set()
    for row in specs:
        if row.name in seen or not set(row.dependencies) <= seen:
            raise PriorityLayerError("supplied parent order or dependency topology changed")
        seen.add(row.name)
    if _specs_digest(specs) != PARENT_SPECS_SHA256:
        raise PriorityLayerError("supplied parent differs from exact immutable v28 specifications")
    return specs


def _parent_specs(supplied: tuple[TheoremSpec,...]|None) -> tuple[TheoremSpec,...]:
    if supplied is None:
        return parent_snapshot().specs
    if type(supplied) is not tuple:
        raise PriorityLayerError("supplied parent specifications must be an exact tuple")
    return _validated_parent_specs(supplied)


@lru_cache(maxsize=32)
def _factory_specs(owner: PriorityLayerFactory) -> tuple[TheoremSpec,...]:
    module = import_module("."+owner.module,package=__package__)
    rows = tuple(getattr(module,owner.factory)(TheoremSpec))
    if not rows or any(type(r) is not TheoremSpec for r in rows):
        raise PriorityLayerError("a registered frozen factory lacks exact ordinary theorem specs")
    return rows


def selected_factories(campaigns: tuple[str,...]=()) -> tuple[PriorityLayerFactory,...]:
    if type(campaigns) is not tuple or any(type(c) is not str for c in campaigns) or len(set(campaigns)) != len(campaigns):
        raise PriorityLayerError("campaign selection must be a tuple of distinct known names")
    if not set(campaigns) <= {f.campaign for f in FACTORIES}:
        raise PriorityLayerError("unknown priority-layer campaign")
    owners = {}
    for factory in FACTORIES:
        for row in _factory_specs(factory):
            if row.name in owners:
                raise PriorityLayerError("registered frozen factories repeat a theorem name")
            owners[row.name] = factory
    selected = {f for f in FACTORIES if not campaigns or f.campaign in campaigns}
    pending = list(selected)
    while pending:
        owner = pending.pop()
        for row in _factory_specs(owner):
            for dependency in row.dependencies:
                prerequisite = owners.get(dependency)
                if prerequisite is not None and prerequisite not in selected:
                    selected.add(prerequisite)
                    pending.append(prerequisite)
    return tuple(f for f in FACTORIES if f in selected)


@lru_cache(maxsize=16)
def priority_layer_specs(campaigns: tuple[str,...]=()) -> tuple[TheoremSpec,...]:
    return tuple(row for owner in selected_factories(campaigns) for row in _factory_specs(owner))


def _table(campaigns: tuple[str,...],parent_specs: tuple[TheoremSpec,...]|None=None) -> dict[str,TheoremSpec]:
    return {row.name:row for row in (*_parent_specs(parent_specs),*priority_layer_specs(campaigns))}


@lru_cache(maxsize=16)
def priority_layer_plan(campaigns: tuple[str,...]=(),*,parent_specs: tuple[TheoremSpec,...]|None=None) -> PriorityLayerPlan:
    factories = selected_factories(campaigns)
    parent,frontier = _parent_specs(parent_specs),priority_layer_specs(campaigns)
    inventory = (*parent,*frontier)
    table = {row.name:row for row in inventory}
    if len(table) != len(inventory):
        raise PriorityLayerError("an additive candidate repeats a parent or candidate name")
    campaign_by_name = {row.name:owner.campaign for owner in factories for row in _factory_specs(owner)}
    used = {dependency for row in frontier for dependency in row.dependencies}
    frontier_names = tuple(row.name for row in frontier)
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise PriorityLayerError("a candidate inventory must have actual maximal theorems")
    selected,pending = set(),list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        if name not in table:
            raise PriorityLayerError(f"missing actual proof dependency {name!r}")
        selected.add(name)
        pending.extend(table[name].dependencies)
    seen,rows = set(),[]
    for position,row in enumerate(inventory):
        if row.name not in selected:
            continue
        if not set(row.dependencies) <= seen or len(set(row.dependencies)) != len(row.dependencies):
            raise PriorityLayerError(f"non-topological exact dependencies in {row.name!r}")
        if not row.script or any(c.startswith(("use ","admit","sorry")) or "DNE" in c for c in row.script):
            raise PriorityLayerError(f"implicit or classical proof authority requested by {row.name!r}")
        rows.append(PriorityLayerRow(len(rows),position,row.name,sha256(row.statement.encode()).hexdigest(),row.dependencies,campaign_by_name.get(row.name)))
        seen.add(row.name)
    if not set(frontier_names) <= seen:
        raise PriorityLayerError("the complete dependency cone omitted a requested candidate")
    return PriorityLayerPlan(tuple(dict.fromkeys(f.campaign for f in factories)),tuple(rows),roots,frontier_names,
        sum(len(r.dependencies) for r in rows),sha256("\n".join(r.name for r in rows).encode()).hexdigest())


def validate_candidate_source_bytes(campaigns: tuple[str,...]=()) -> tuple[PriorityLayerFactory,...]:
    selected = selected_factories(campaigns)
    for owner in selected:
        path = ROOT/"peano-lab/py/peano_lab/library"/(owner.module+".py")
        if sha256(path.read_bytes()).hexdigest() != owner.source_sha256:
            raise PriorityLayerError(f"a registered frozen candidate source changed: {owner.module}")
    return selected


def validate_parent_provider_bytes() -> tuple[ParentDocument,...]:
    documents = parent_snapshot().documents
    for document in documents:
        payload = (ROOT/document.path).read_bytes()
        if len(payload) != document.bytes or sha256(payload).hexdigest() != document.sha256:
            raise PriorityLayerError(f"sealed historical proof bytes changed: {document.path}")
    return documents


def _reused_bodies(plan: PriorityLayerPlan,table: dict[str,TheoremSpec],report: Callable[[str],None],seed_bundles: tuple[str|Path,...]=()) -> tuple[dict[str,Proof],dict[str,tuple[str,int|None]]]:
    wanted = {row.name for row in plan.rows}
    candidates = defaultdict(list)
    targets = {name:_closed_formula(table[name].statement) for name in wanted}
    for name,target in targets.items():
        candidates[hash(target)].append(name)
    bodies,origins = {},{}
    # Explicit candidate seeds are complete proof data, not trusted receipts.
    # Decode under the unchanged bounds and freshly check *every* seed node
    # before reusing any exact target and ordered-premise match.
    for source in seed_bundles:
        path = Path(source)
        if path.stat().st_size > DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
            raise PriorityLayerError("candidate seed exceeds the unchanged bundle byte limit")
        seed,seed_target = decode_proof_bundle(path.read_text(encoding="utf-8"))
        seed_receipt = check_proof_bundle(seed,seed_target)
        nodes = {node.node_id:node for node in seed.nodes}
        retained = 0
        for node in seed.nodes:
            for name in candidates.get(hash(node.target),()):
                if name not in wanted or node.target != targets[name]:
                    continue
                dependencies = table[name].dependencies
                if len(dependencies) != len(node.dependencies) or any(
                    index not in nodes or nodes[index].target != targets.get(dependency,_closed_formula(table[dependency].statement))
                    for index,dependency in zip(node.dependencies,dependencies)):
                    continue
                bodies[name] = node.body
                origins[name] = (str(path),node.node_id)
                wanted.remove(name)
                retained += 1
        report(f"priority-layer checked candidate seed {path.name}: {seed_receipt.kernel_calls} kernel calls; retained {retained} exact bodies")
        del seed,nodes
        gc.collect()
    wanted.intersection_update(row.name for row in plan.rows if row.campaign is None)
    for document in validate_parent_provider_bytes():
        if not wanted:
            break
        payload = (ROOT/document.path).read_bytes()
        if len(payload) != document.bytes or sha256(payload).hexdigest() != document.sha256:
            raise PriorityLayerError(f"sealed historical proof bytes changed: {document.path}")
        bundle,_ = decode_proof_bundle(payload.decode("utf-8"))
        del payload
        nodes = {node.node_id:node for node in bundle.nodes}
        retained = 0
        for node in bundle.nodes:
            for name in candidates.get(hash(node.target),()):
                if name not in wanted or node.target != targets[name]:
                    continue
                dependencies = table[name].dependencies
                if len(dependencies) != len(node.dependencies) or any(
                    index not in nodes or nodes[index].target != targets.get(dependency,_closed_formula(table[dependency].statement))
                    for index,dependency in zip(node.dependencies,dependencies)):
                    continue
                bodies[name] = node.body
                origins[name] = (document.path,node.node_id)
                wanted.remove(name)
                retained += 1
        report(f"priority-layer provider {Path(document.path).name}: retained {retained}; missing {len(wanted)}")
        del bundle,nodes
        gc.collect()
    return bodies,origins


def check_priority_layer_proof_bundle(bundle: ProofBundle,target: Formula,*,campaigns: tuple[str,...]=(),parent_specs: tuple[TheoremSpec,...]|None=None) -> CheckedProofBundle:
    plan = priority_layer_plan(campaigns,parent_specs=parent_specs)
    table = _table(campaigns,parent_specs)
    positions = {row.name:row.node_id for row in plan.rows}
    if type(bundle) is not ProofBundle or len(bundle.nodes) != len(plan.rows)+1 or bundle.root != len(plan.rows):
        raise PriorityLayerError("the exact candidate node inventory or root changed")
    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        if (type(node) is not BundleNode or node.node_id != row.node_id
            or node.target != _closed_formula(table[row.name].statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)):
            raise PriorityLayerError(f"changed exact target or ordered dependency edge for {row.name!r}")
    expected_target,expected_body = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    final = bundle.nodes[-1]
    if (final.node_id != len(plan.rows) or final.target != expected_target
        or final.dependencies != tuple(positions[name] for name in plan.root_names)
        or final.body != expected_body or target != expected_target):
        raise PriorityLayerError("the complete maximal-theorem packaging root changed")
    receipt = check_proof_bundle(bundle,target)
    if receipt.kernel_calls != len(bundle.nodes) or receipt.dependency_edges != plan.dependency_edge_count+len(plan.root_names):
        raise PriorityLayerError("not every actual candidate body and dependency reached the kernel")
    return receipt


def checked_priority_layer_proof_bundle(*,parent_specs: tuple[TheoremSpec,...]|None=None) -> tuple[ProofBundle,CheckedProofBundle]:
    """Read sealed v29 bytes and freshly kernel-check all 566 ordinary bodies.

    Provenance pins are additional integrity checks, never proof authority.
    Supplying exact parent specs supports the compact browser layout without
    loading a repository catalogue. No proof or receipt cache is consulted.
    """
    if (EXPECTED_PRIORITY_LAYER_FRONTIER_COUNT <= 0
        or EXPECTED_PRIORITY_LAYER_THEOREM_COUNT <= 0
        or EXPECTED_PRIORITY_LAYER_ROOT_COUNT <= 0
        or EXPECTED_PRIORITY_LAYER_DEPENDENCY_EDGE_COUNT <= 0
        or EXPECTED_PRIORITY_LAYER_BUNDLE_NODE_COUNT <= 0
        or EXPECTED_PRIORITY_LAYER_BUNDLE_EDGE_COUNT <= 0
        or EXPECTED_PRIORITY_LAYER_BUNDLE_BODY_PROOF_NODES <= 0
        or EXPECTED_PRIORITY_LAYER_BUNDLE_BYTES <= 0
        or len(EXPECTED_PRIORITY_LAYER_ORDERED_NAMES_SHA256) != 64
        or len(EXPECTED_PRIORITY_LAYER_BUNDLE_SHA256) != 64):
        raise PriorityLayerError("the priority-layer release is not sealed for checked use")
    browser=Path("/lab/proof-artifacts")/PRIORITY_LAYER_ARTIFACT_FILENAME
    source=browser if browser.is_file() else ROOT/"research/arithmetic-library/artifacts"/PRIORITY_LAYER_ARTIFACT_FILENAME
    payload=source.read_bytes()
    if len(payload)!=EXPECTED_PRIORITY_LAYER_BUNDLE_BYTES or sha256(payload).hexdigest()!=EXPECTED_PRIORITY_LAYER_BUNDLE_SHA256:
        raise PriorityLayerError("the immutable priority-layer proof artifact changed")
    bundle,target=decode_proof_bundle(payload.decode("utf-8"))
    plan=priority_layer_plan(parent_specs=parent_specs)
    if (len(plan.frontier_names)!=EXPECTED_PRIORITY_LAYER_FRONTIER_COUNT
        or len(plan.rows)!=EXPECTED_PRIORITY_LAYER_THEOREM_COUNT
        or len(plan.root_names)!=EXPECTED_PRIORITY_LAYER_ROOT_COUNT
        or plan.dependency_edge_count!=EXPECTED_PRIORITY_LAYER_DEPENDENCY_EDGE_COUNT
        or plan.ordered_names_sha256!=EXPECTED_PRIORITY_LAYER_ORDERED_NAMES_SHA256):
        raise PriorityLayerError("the exact sealed priority-layer inventory changed")
    receipt=check_priority_layer_proof_bundle(bundle,target,parent_specs=parent_specs)
    if (receipt.node_count!=EXPECTED_PRIORITY_LAYER_BUNDLE_NODE_COUNT
        or receipt.kernel_calls!=EXPECTED_PRIORITY_LAYER_BUNDLE_NODE_COUNT
        or receipt.dependency_edges!=EXPECTED_PRIORITY_LAYER_BUNDLE_EDGE_COUNT
        or receipt.total_body_nodes!=EXPECTED_PRIORITY_LAYER_BUNDLE_BODY_PROOF_NODES):
        raise PriorityLayerError("the sealed priority-layer original-kernel metrics changed")
    return bundle,receipt


def priority_layer_bundle(*,parent_specs: tuple[TheoremSpec,...]|None=None) -> tuple[ProofBundle,CheckedProofBundle]:
    """Public two-item provider; the edition wrapper adds theorem positions."""
    return checked_priority_layer_proof_bundle(parent_specs=parent_specs)


def replay_priority_layer_theorem(name: str,bundle: ProofBundle,target: Formula,*,campaigns: tuple[str,...]=(),parent_specs: tuple[TheoremSpec,...]|None=None) -> CheckedTheorem:
    """Materialize and kernel-check one ordinary empty-context candidate proof.

    This mirrors the existing conservative runtime proof compiler, but does
    not create an edition entry, grant checked use, or rely on a proof cache.
    """
    check_priority_layer_proof_bundle(bundle,target,campaigns=campaigns,parent_specs=parent_specs)
    plan = priority_layer_plan(campaigns,parent_specs=parent_specs)
    positions = {row.name:row.node_id for row in plan.rows}
    if type(name) is not str or name not in positions:
        raise PriorityLayerError("unknown actual candidate dependency-cone theorem")
    root = positions[name]
    included,pending = set(),[root]
    while pending:
        position = pending.pop()
        if position not in included:
            included.add(position)
            pending.extend(bundle.nodes[position].dependencies)
    layered = LayeredReplayBundle(tuple(LayeredReplayNode(node.node_id,node.target,node.dependencies,node.body)
        for node in bundle.nodes if node.node_id in included),root)
    specification = _table(campaigns,parent_specs)[name]
    formula = _closed_formula(specification.statement)
    interned = intern_layered_replay_bodies(layered,formula,limits=DEFAULT_LAYERED_REPLAY_LIMITS)
    if interned is None:
        raise PriorityLayerError("the candidate exceeded unchanged conservative sharing limits")
    for original,actual in zip(layered.nodes,interned.nodes,strict=True):
        if (original.node_id != actual.node_id or original.target != actual.target
            or original.dependencies != actual.dependencies):
            raise PriorityLayerError("conservative interning changed the exact candidate graph")
        body_target = actual.target
        for dependency in reversed(actual.dependencies):
            body_target = Imp(bundle.nodes[dependency].target,body_target)
        if not check((),actual.body,body_target):
            raise PriorityLayerError("the original kernel rejected an interned ordinary body")
    candidate = compile_layered_replay(interned,formula,limits=DEFAULT_LAYERED_REPLAY_LIMITS)
    if candidate is None or not check((),candidate.certificate,formula):
        raise PriorityLayerError("the unchanged kernel/resource policy rejected the materialized empty-context theorem")
    return CheckedTheorem(specification,formula,candidate.certificate,candidate.proof_nodes)


def assemble_priority_layer_proof_bundle(*,campaigns: tuple[str,...]=(),batch_size: int=1,seed_bundles: tuple[str|Path,...]=(),report: Callable[[str],None]=print) -> CheckedPriorityLayerBundle:
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH_ROWS:
        raise PriorityLayerError("priority authoring batches must contain 1..16 rows")
    if type(seed_bundles) is not tuple or any(not isinstance(p,(str,Path)) for p in seed_bundles):
        raise PriorityLayerError("candidate seeds must be an explicit tuple of proof-bundle paths")
    if len({str(Path(p).resolve()) for p in seed_bundles}) != len(seed_bundles):
        raise PriorityLayerError("candidate seed paths must be distinct")
    validate_candidate_source_bytes(campaigns)
    plan,table = priority_layer_plan(campaigns),_table(campaigns)
    bodies,origins = _reused_bodies(plan,table,report,seed_bundles)
    rebuilt = tuple(r for r in plan.rows if r.name not in bodies)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    for offset in range(0,len(rebuilt),batch_size):
        occurrences = identities = 0
        batch = rebuilt[offset:offset+batch_size]
        for row in batch:
            body = _reconstruct_body(table[row.name],table)
            count,objects,*_ = _proof_envelope_metrics_bounded(body,
                max_proof_occurrences=MAX_BATCH_PROOF_NODES-occurrences,
                max_proof_objects=MAX_BATCH_PROOF_OBJECTS-identities,
                max_proof_depth=limits.max_body_depth,
                max_annotation_occurrences=limits.max_body_annotation_occurrences,
                max_annotation_depth=limits.max_formula_depth,
                max_envelope_depth=limits.max_body_envelope_depth,label=f"priority body {row.name}")
            occurrences += count
            identities += objects
            bodies[row.name] = body
            origins[row.name] = ("new_script" if row.campaign else "parent_script",None)
        report(f"priority-layer batch {offset//batch_size+1}: {len(batch)} bodies, {occurrences} nodes, {identities} objects ({min(offset+batch_size,len(rebuilt))}/{len(rebuilt)})")
        gc.collect()
    positions = {r.name:r.node_id for r in plan.rows}
    nodes = [BundleNode(r.node_id,_closed_formula(table[r.name].statement),tuple(positions[d] for d in r.dependencies),bodies[r.name]) for r in plan.rows]
    target,body = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    nodes.append(BundleNode(len(nodes),target,tuple(positions[name] for name in plan.root_names),body))
    bundle = ProofBundle(tuple(nodes),len(nodes)-1)
    receipt = check_priority_layer_proof_bundle(bundle,target,campaigns=campaigns)
    return CheckedPriorityLayerBundle(bundle,target,receipt,tuple((r.name,*origins[r.name]) for r in plan.rows))


def export_priority_layer_proof_bundle(output: str|Path,*,campaigns: tuple[str,...]=(),batch_size: int=1,seed_bundles: tuple[str|Path,...]=()) -> CheckedPriorityLayerBundle:
    destination = Path(output)
    if destination.exists():
        raise PriorityLayerError("candidate export never overwrites an existing artifact")
    result = assemble_priority_layer_proof_bundle(campaigns=campaigns,batch_size=batch_size,seed_bundles=seed_bundles,report=lambda text:print(text,flush=True))
    payload = encode_proof_bundle(result.bundle,result.target)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("x",encoding="utf-8") as output_file:
        output_file.write(payload)
    raw = payload.encode("utf-8")
    print(f"NON-ADMITTING priority-layer original-kernel ACCEPT: nodes={result.receipt.node_count}; edges={result.receipt.dependency_edges}; body-nodes={result.receipt.total_body_nodes}; bytes={len(raw)}; sha256={sha256(raw).hexdigest()}",flush=True)
    return result


def main(argv: Sequence[str]|None=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path,help="new non-admitting artifact; existing files are never overwritten")
    parser.add_argument("--campaign",action="append",choices=tuple(dict.fromkeys(f.campaign for f in FACTORIES)),default=[])
    parser.add_argument("--batch-size",type=int,default=1)
    parser.add_argument("--seed-bundle",action="append",type=Path,default=[],help="explicit self-contained candidate proof data; every seed body is freshly kernel-checked")
    args = parser.parse_args(argv)
    export_priority_layer_proof_bundle(args.output,campaigns=tuple(args.campaign),batch_size=args.batch_size,seed_bundles=tuple(args.seed_bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
