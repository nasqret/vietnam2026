"""Resource-bounded full Gaussian factorization closure over frozen Alpha v29.

The immutable parent catalogue specifies exact historical targets and proof
providers, never proof authority. Seven frozen constructive factories close
their actual dependency cone. Every new or reused ordinary proof body reaches
the unchanged kernel, and only the separately sealed v30 provider may supply
checked proof data to an edition. This module neither imports an edition nor
grants membership. No kernel, historical artifact or resource cap is changed.
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
from ..kernel.proofs import Cut, Hyp, ImpElim, ImpIntro, Proof
from .campaign_lower_layer_closure import (
    _packaging_root, _reconstruct_body, _specs_digest,
)
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS, LayeredReplayBundle, LayeredReplayError,
    LayeredReplayLimits, LayeredReplayNode, _balanced_package,
    _closed_formula_metrics as _replay_formula_metrics, _layers, _project,
    _proof_envelope_metrics_bounded, _validate_graph, intern_layered_replay_bodies,
)
from .proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, BundleNode, CheckedProofBundle, ProofBundle, check_proof_bundle,
    decode_proof_bundle, encode_proof_bundle,
)
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


_MODULE_PARENTS = Path(__file__).resolve().parents
ROOT = _MODULE_PARENTS[4] if len(_MODULE_PARENTS) > 4 else Path("/lab")
PARENT_CATALOG = "artifacts/peano-library/alpha/catalog-v29.json"
PARENT_CATALOG_SHA256 = "2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0"
PARENT_COUNT = 3042
PARENT_IDENTITY_SHA256 = "57da70c3718579cb8eb81c59a4c2898a5071140fa944e31bca312fe53432574c"
PARENT_ENROLLMENT_SHA256 = "feac02afbfe516116accd30a6a117060f5d5cd99d608971a7f62bd1f3787104d"
PARENT_SPECS_SHA256 = "70c8d552afdf9ce499942ad263d5145e703c9dab834e9d4b66d753b5364582c1"
GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME = "alpha-v30-gaussian-factorization-proof-bundle-v1.json"
EXPECTED_GAUSSIAN_FACTORIZATION_FRONTIER_COUNT = 180
EXPECTED_GAUSSIAN_FACTORIZATION_THEOREM_COUNT = 452
EXPECTED_GAUSSIAN_FACTORIZATION_ROOT_COUNT = 18
EXPECTED_GAUSSIAN_FACTORIZATION_DEPENDENCY_EDGE_COUNT = 1430
EXPECTED_GAUSSIAN_FACTORIZATION_ORDERED_NAMES_SHA256 = "fe63423af323582ebbe7f05c2bd3848a3717ac5b83bb0de35913789c517ac35f"
EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_NODE_COUNT = 453
EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_EDGE_COUNT = 1448
EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES = 39423
EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES = 6143166
EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256 = "e0e10f11c5b12b411843054000a77be22ede7db53602814f9532e3e7c8daa270"

# Exactly the existing immutable authoring policy, not relaxed bounds.
MAX_BATCH_ROWS = 16
MAX_BATCH_PROOF_NODES = 125000
MAX_BATCH_PROOF_OBJECTS = 25000


class GaussianFactorizationError(ValueError):
    """An exact inventory, source, proof, topology or resource check failed."""


@dataclass(frozen=True, slots=True)
class GaussianFactorizationFactory:
    campaign: str
    module: str
    factory: str
    rfc: str
    source_sha256: str


FACTORIES = (
    GaussianFactorizationFactory("gaussian_factorization","gaussian_ring_candidate","make_gaussian_ring_candidate_theorems","gaussian-gcd-prime-rfc-v1.md","7e6d4a3ba15f7190047e656d91a2a0f781e6a24ab055ebcf7bc0efc6d15d3e44"),
    GaussianFactorizationFactory("gaussian_factorization","gaussian_divisibility_candidate","make_gaussian_divisibility_candidate_theorems","gaussian-gcd-prime-rfc-v1.md","ce5d6fd7d38504d2d6cd050e38bccef4b6a504f8ecb49f8ca86e78aaace48747"),
    GaussianFactorizationFactory("gaussian_factorization","gaussian_gcd_candidate","make_gaussian_gcd_candidate_theorems","gaussian-gcd-prime-rfc-v1.md","da72285e399ece582e3ececadf660cb71936e293627b75849410f6022946ef33"),
    GaussianFactorizationFactory("gaussian_factorization","gaussian_factor_search_candidate","make_gaussian_factor_search_candidate_theorems","gaussian-factorization-rfc-v1.md","039bb7e5d7bb3c3fe1acd3177904c99c62ecfd78424685e78c8c5dc28cd1b6ce"),
    GaussianFactorizationFactory("gaussian_factorization","gaussian_factorization_candidate","make_gaussian_factorization_candidate_theorems","gaussian-factorization-rfc-v1.md","cb95534689e6155fdbb1a7e80be843bdd91153504f9b5df99bf6ee59e77e8d1e"),
    GaussianFactorizationFactory("gaussian_factorization","gaussian_product_reindex_candidate","make_gaussian_product_reindex_candidate_theorems","gaussian-product-reindex-rfc-v1.md","7a5b5d0b19aa8217fab943d215b859e031bada36f7eebc1409c0949b99b33f2c"),
    GaussianFactorizationFactory("gaussian_factorization","gaussian_factor_permutation_candidate","make_gaussian_factor_permutation_candidate_theorems","gaussian-factorization-rfc-v1.md","13d404c9870cf2ef2fb089749f60224b858d2954ec581bb37b09320c23055f1f"),
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
class GaussianFactorizationRow:
    node_id: int
    inventory_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str,...]
    campaign: str | None


@dataclass(frozen=True, slots=True)
class GaussianFactorizationPlan:
    campaigns: tuple[str,...]
    rows: tuple[GaussianFactorizationRow,...]
    root_names: tuple[str,...]
    frontier_names: tuple[str,...]
    dependency_edge_count: int
    ordered_names_sha256: str


@dataclass(frozen=True, slots=True)
class CheckedGaussianFactorizationBundle:
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    origins: tuple[tuple[str,str,int|None],...]


@dataclass(frozen=True, slots=True)
class GaussianFactorizationReplayCandidate:
    """Untrusted ordinary syntax, with separate graph/argument accounting.

    Argument formulas are closed conditional proof values, not added graph
    targets or granted hypotheses. Their every occurrence is charged in the
    final proof-annotation envelope. Only an empty-context kernel check can
    turn this candidate into a theorem.
    """

    certificate: Proof
    target: Formula
    layers: tuple[tuple[int,...],...]
    graph_formula_occurrences: int
    package_formulas: tuple[Formula,...]
    package_formula_occurrences: int
    maximum_package_formula_depth: int
    conditional_formula_occurrences: int
    argument_formulas: tuple[Formula,...]
    argument_formula_occurrences: tuple[int,...]
    argument_formula_depths: tuple[int,...]
    proof_nodes: int
    proof_objects: int
    proof_depth: int
    proof_annotation_occurrences: int
    proof_envelope_depth: int


def _compile_gaussian_factorization_replay(
    graph: LayeredReplayBundle,target: Formula,limits: LayeredReplayLimits,
) -> GaussianFactorizationReplayCandidate:
    # Validate the ORIGINAL graph, including every unchanged target, edge and
    # body, under the existing graph limits. No expanded graph is substituted.
    table,order = _validate_graph(graph,target,limits)
    layers,depths = _layers(table,order)
    graph_occurrences = _replay_formula_metrics(target,
        max_occurrences=limits.max_formula_occurrences_per_target,
        max_depth=limits.max_formula_depth)[0]
    pending,groups = [],[]
    group_occurrences = conditional_occurrences = 0
    for node_id in order:
        node = table[node_id]
        graph_occurrences += _replay_formula_metrics(node.target,
            max_occurrences=limits.max_formula_occurrences_per_target,
            max_depth=limits.max_formula_depth)[0]
        formula = node.target
        for dependency in reversed(node.dependencies):
            formula = Imp(table[dependency].target,formula)
        occurrences,_ = _replay_formula_metrics(formula,
            max_occurrences=limits.max_package_formula_occurrences,
            max_depth=limits.max_package_formula_depth)
        conditional_occurrences += occurrences
        # These are separate ordinary proof ARGUMENTS, not theorem layers.
        # Bound each formula and fan-in; charge every resulting annotation
        # again in the complete candidate below, including both Cut fields.
        if pending and (len(pending) >= limits.max_dependencies_per_node
            or group_occurrences+occurrences+1 > limits.max_package_formula_occurrences):
            groups.append(_balanced_package(tuple(pending)))
            pending,group_occurrences = [],0
        group_occurrences += occurrences+(1 if pending else 0)
        pending.append((node_id,formula,node.body))
    if pending:
        groups.append(_balanced_package(tuple(pending)))
    placements = {node_id:(index,path)
        for index,(_,_,paths) in enumerate(groups) for node_id,path in paths.items()}
    argument_occurrences,argument_depths = [],[]
    envelope_limits = dict(
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=limits.max_candidate_annotation_occurrences,
        max_annotation_depth=max(limits.max_formula_depth,limits.max_package_formula_depth),
        max_envelope_depth=limits.max_candidate_envelope_depth,
    )
    for formula,body,_ in groups:
        occurrences,depth = _replay_formula_metrics(formula,
            max_occurrences=limits.max_package_formula_occurrences,
            max_depth=limits.max_package_formula_depth)
        argument_occurrences.append(occurrences)
        argument_depths.append(depth)
        _proof_envelope_metrics_bounded(body,**envelope_limits,label="conditional argument proof")

    # Compile only binder-free wiring in the enlarged temporary context.
    # The original closed bodies are never weakened under those hypotheses.
    # This is ordinary Imp/And/Cut syntax, not a new checker inference rule.
    package_formulas,package_proofs,package_paths = [],[],[]
    for layer_index,layer in enumerate(layers):
        entries = []
        for node_id in layer:
            node = table[node_id]
            group_index,path = placements[node_id]
            theorem = _project(layer_index+len(groups)-1-group_index,path)
            for dependency in node.dependencies:
                dependency_layer = depths[dependency]
                if dependency_layer >= layer_index:
                    raise LayeredReplayError("dependency is not in an earlier exact layer")
                theorem = ImpElim(theorem,_project(layer_index-1-dependency_layer,
                    package_paths[dependency_layer][dependency]))
            entries.append((node_id,node.target,theorem))
        formula,body,paths = _balanced_package(tuple(entries))
        package_formulas.append(formula)
        package_proofs.append(body)
        package_paths.append(paths)
    package_occurrences = package_depth = 0
    for formula in package_formulas:
        occurrences,depth = _replay_formula_metrics(formula,
            max_occurrences=limits.max_package_formula_occurrences,
            max_depth=limits.max_package_formula_depth)
        package_occurrences += occurrences
        if package_occurrences > limits.max_package_formula_occurrences:
            raise LayeredReplayError("original layer packages exceed their formula-occurrence limit")
        package_depth = max(package_depth,depth)
    final = _project(len(layers)-1-depths[graph.root],package_paths[depths[graph.root]][graph.root])
    for index in reversed(range(len(layers))):
        final = Cut(package_formulas[index],target,package_proofs[index],final)

    # Every temporary conditional premise is discharged by its genuine closed
    # body. Annotated identity cuts let the original checker synthesize the
    # argument types; the arguments themselves are checked in the empty outer
    # context. No free hypothesis, external proof reference or cache is added.
    for _ in groups:
        final = ImpIntro(final)
    for formula,body,_ in groups:
        final = ImpElim(final,Cut(formula,formula,body,Hyp(0)))
    nodes,objects,depth,annotations,envelope = _proof_envelope_metrics_bounded(
        final,**envelope_limits,label="complete hoisted candidate proof")
    return GaussianFactorizationReplayCandidate(
        final,target,layers,graph_occurrences,tuple(package_formulas),
        package_occurrences,package_depth,conditional_occurrences,
        tuple(formula for formula,_,_ in groups),tuple(argument_occurrences),
        tuple(argument_depths),nodes,objects,depth,annotations,envelope,
    )


def compile_gaussian_factorization_replay(
    graph: object,target: object,*,limits: LayeredReplayLimits=DEFAULT_LAYERED_REPLAY_LIMITS,
) -> GaussianFactorizationReplayCandidate | None:
    """Fail-closed untrusted hoisting; no kernel call or theorem authority.

    Original graph and dependency-layer budgets retain their exact domains.
    Additional conditional arguments are ordinary proof data, individually
    formula-bounded and fully charged under the unchanged final candidate
    occurrence/object/depth/annotation/envelope limits. Callers must check
    both every conservatively interned body and the entire returned proof
    with the original empty-context kernel judgment.
    """
    try:
        return _compile_gaussian_factorization_replay(graph,target,limits)
    except (AttributeError,IndexError,KeyError,LayeredReplayError,RecursionError,TypeError,ValueError):
        return None


@lru_cache(maxsize=1)
def parent_snapshot() -> ParentSnapshot:
    raw = (ROOT/PARENT_CATALOG).read_bytes()
    if sha256(raw).hexdigest() != PARENT_CATALOG_SHA256:
        raise GaussianFactorizationError("the exact immutable Alpha-v29 parent catalogue changed")
    catalog = json.loads(raw)
    del raw
    if (catalog.get("theorem_count") != PARENT_COUNT
        or catalog.get("checked_use_count") != PARENT_COUNT
        or catalog.get("stable_count") != 432
        or catalog.get("edition_identity_sha256") != PARENT_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != PARENT_ENROLLMENT_SHA256):
        raise GaussianFactorizationError("the exact parent identity or Stable partition changed")
    specs = tuple(TheoremSpec(r["name"],r["statement"],tuple(r["dependencies"]),tuple(r["script"]),r["summary"]) for r in catalog["theorems"])
    _validated_parent_specs(specs)
    for data,row in zip(catalog["theorems"],specs):
        if (not data.get("checked_use") or not data.get("body_checked")
            or sha256(row.statement.encode()).hexdigest() != data["statement_sha256"]):
            raise GaussianFactorizationError("the parent catalogue contains an invalid exact theorem row")
    documents = tuple(sorted((ParentDocument(d["path"],d["bytes"],d["sha256"])
        for d in catalog["evidence_documents"]
        if d["path"].startswith("research/arithmetic-library/artifacts/")
        and d["path"].endswith("proof-bundle-v1.json")
        and ".." not in Path(d["path"]).parts),key=lambda d:(d.bytes,d.path)))
    if not documents:
        raise GaussianFactorizationError("the parent has no exact ordinary proof providers")
    return ParentSnapshot(specs,documents)


@lru_cache(maxsize=2)
def _validated_parent_specs(specs: tuple[TheoremSpec,...]) -> tuple[TheoremSpec,...]:
    if len(specs) != PARENT_COUNT or any(type(r) is not TheoremSpec for r in specs):
        raise GaussianFactorizationError("supplied parent specification inventory changed")
    seen = set()
    for row in specs:
        if row.name in seen or not set(row.dependencies) <= seen:
            raise GaussianFactorizationError("supplied parent order or dependency topology changed")
        seen.add(row.name)
    if _specs_digest(specs) != PARENT_SPECS_SHA256:
        raise GaussianFactorizationError("supplied parent differs from exact immutable v29 specifications")
    return specs


def _parent_specs(supplied: tuple[TheoremSpec,...]|None) -> tuple[TheoremSpec,...]:
    if supplied is None:
        return parent_snapshot().specs
    if type(supplied) is not tuple:
        raise GaussianFactorizationError("supplied parent specifications must be an exact tuple")
    return _validated_parent_specs(supplied)


@lru_cache(maxsize=32)
def _factory_specs(owner: GaussianFactorizationFactory) -> tuple[TheoremSpec,...]:
    module = import_module("."+owner.module,package=__package__)
    rows = tuple(getattr(module,owner.factory)(TheoremSpec))
    if not rows or any(type(r) is not TheoremSpec for r in rows):
        raise GaussianFactorizationError("a registered frozen factory lacks exact ordinary theorem specs")
    return rows


def selected_factories(campaigns: tuple[str,...]=()) -> tuple[GaussianFactorizationFactory,...]:
    if type(campaigns) is not tuple or any(type(c) is not str for c in campaigns) or len(set(campaigns)) != len(campaigns):
        raise GaussianFactorizationError("campaign selection must be a tuple of distinct known names")
    if not set(campaigns) <= {f.campaign for f in FACTORIES}:
        raise GaussianFactorizationError("unknown gaussian-factorization campaign")
    owners = {}
    for factory in FACTORIES:
        for row in _factory_specs(factory):
            if row.name in owners:
                raise GaussianFactorizationError("registered frozen factories repeat a theorem name")
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
def gaussian_factorization_specs(campaigns: tuple[str,...]=()) -> tuple[TheoremSpec,...]:
    return tuple(row for owner in selected_factories(campaigns) for row in _factory_specs(owner))


def _table(campaigns: tuple[str,...],parent_specs: tuple[TheoremSpec,...]|None=None) -> dict[str,TheoremSpec]:
    return {row.name:row for row in (*_parent_specs(parent_specs),*gaussian_factorization_specs(campaigns))}


@lru_cache(maxsize=16)
def gaussian_factorization_plan(campaigns: tuple[str,...]=(),*,parent_specs: tuple[TheoremSpec,...]|None=None) -> GaussianFactorizationPlan:
    factories = selected_factories(campaigns)
    parent,frontier = _parent_specs(parent_specs),gaussian_factorization_specs(campaigns)
    inventory = (*parent,*frontier)
    table = {row.name:row for row in inventory}
    if len(table) != len(inventory):
        raise GaussianFactorizationError("an additive candidate repeats a parent or candidate name")
    campaign_by_name = {row.name:owner.campaign for owner in factories for row in _factory_specs(owner)}
    used = {dependency for row in frontier for dependency in row.dependencies}
    frontier_names = tuple(row.name for row in frontier)
    roots = tuple(name for name in frontier_names if name not in used)
    if not roots:
        raise GaussianFactorizationError("a candidate inventory must have actual maximal theorems")
    selected,pending = set(),list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        if name not in table:
            raise GaussianFactorizationError(f"missing actual proof dependency {name!r}")
        selected.add(name)
        pending.extend(table[name].dependencies)
    seen,rows = set(),[]
    for position,row in enumerate(inventory):
        if row.name not in selected:
            continue
        if not set(row.dependencies) <= seen or len(set(row.dependencies)) != len(row.dependencies):
            raise GaussianFactorizationError(f"non-topological exact dependencies in {row.name!r}")
        if not row.script or any(c.startswith(("use ","admit","sorry")) or "DNE" in c for c in row.script):
            raise GaussianFactorizationError(f"implicit or classical proof authority requested by {row.name!r}")
        rows.append(GaussianFactorizationRow(len(rows),position,row.name,sha256(row.statement.encode()).hexdigest(),row.dependencies,campaign_by_name.get(row.name)))
        seen.add(row.name)
    if not set(frontier_names) <= seen:
        raise GaussianFactorizationError("the complete dependency cone omitted a requested candidate")
    return GaussianFactorizationPlan(tuple(dict.fromkeys(f.campaign for f in factories)),tuple(rows),roots,frontier_names,
        sum(len(r.dependencies) for r in rows),sha256("\n".join(r.name for r in rows).encode()).hexdigest())


def validate_candidate_source_bytes(campaigns: tuple[str,...]=()) -> tuple[GaussianFactorizationFactory,...]:
    selected = selected_factories(campaigns)
    for owner in selected:
        path = ROOT/"peano-lab/py/peano_lab/library"/(owner.module+".py")
        if sha256(path.read_bytes()).hexdigest() != owner.source_sha256:
            raise GaussianFactorizationError(f"a registered frozen candidate source changed: {owner.module}")
    return selected


def validate_parent_provider_bytes() -> tuple[ParentDocument,...]:
    documents = parent_snapshot().documents
    for document in documents:
        payload = (ROOT/document.path).read_bytes()
        if len(payload) != document.bytes or sha256(payload).hexdigest() != document.sha256:
            raise GaussianFactorizationError(f"sealed historical proof bytes changed: {document.path}")
    return documents


def _reused_bodies(plan: GaussianFactorizationPlan,table: dict[str,TheoremSpec],report: Callable[[str],None],seed_bundles: tuple[str|Path,...]=()) -> tuple[dict[str,Proof],dict[str,tuple[str,int|None]]]:
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
            raise GaussianFactorizationError("candidate seed exceeds the unchanged bundle byte limit")
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
        report(f"gaussian-factorization checked candidate seed {path.name}: {seed_receipt.kernel_calls} kernel calls; retained {retained} exact bodies")
        del seed,nodes
        gc.collect()
    wanted.intersection_update(row.name for row in plan.rows if row.campaign is None)
    for document in validate_parent_provider_bytes():
        if not wanted:
            break
        payload = (ROOT/document.path).read_bytes()
        if len(payload) != document.bytes or sha256(payload).hexdigest() != document.sha256:
            raise GaussianFactorizationError(f"sealed historical proof bytes changed: {document.path}")
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
        report(f"gaussian-factorization provider {Path(document.path).name}: retained {retained}; missing {len(wanted)}")
        del bundle,nodes
        gc.collect()
    return bodies,origins


def check_gaussian_factorization_proof_bundle(bundle: ProofBundle,target: Formula,*,campaigns: tuple[str,...]=(),parent_specs: tuple[TheoremSpec,...]|None=None) -> CheckedProofBundle:
    plan = gaussian_factorization_plan(campaigns,parent_specs=parent_specs)
    table = _table(campaigns,parent_specs)
    positions = {row.name:row.node_id for row in plan.rows}
    if type(bundle) is not ProofBundle or len(bundle.nodes) != len(plan.rows)+1 or bundle.root != len(plan.rows):
        raise GaussianFactorizationError("the exact candidate node inventory or root changed")
    for row in plan.rows:
        node = bundle.nodes[row.node_id]
        if (type(node) is not BundleNode or node.node_id != row.node_id
            or node.target != _closed_formula(table[row.name].statement)
            or node.dependencies != tuple(positions[name] for name in row.dependencies)):
            raise GaussianFactorizationError(f"changed exact target or ordered dependency edge for {row.name!r}")
    expected_target,expected_body = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    final = bundle.nodes[-1]
    if (final.node_id != len(plan.rows) or final.target != expected_target
        or final.dependencies != tuple(positions[name] for name in plan.root_names)
        or final.body != expected_body or target != expected_target):
        raise GaussianFactorizationError("the complete maximal-theorem packaging root changed")
    receipt = check_proof_bundle(bundle,target)
    if receipt.kernel_calls != len(bundle.nodes) or receipt.dependency_edges != plan.dependency_edge_count+len(plan.root_names):
        raise GaussianFactorizationError("not every actual candidate body and dependency reached the kernel")
    return receipt


def checked_gaussian_factorization_proof_bundle(*,parent_specs: tuple[TheoremSpec,...]|None=None) -> tuple[ProofBundle,CheckedProofBundle]:
    """Read sealed v30 bytes and freshly kernel-check every ordinary body.

    Provenance pins are additional integrity checks, never proof authority.
    Supplying exact parent specs supports the compact browser layout without
    loading a repository catalogue. No proof or receipt cache is consulted.
    """
    if (EXPECTED_GAUSSIAN_FACTORIZATION_FRONTIER_COUNT <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_THEOREM_COUNT <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_ROOT_COUNT <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_DEPENDENCY_EDGE_COUNT <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_NODE_COUNT <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_EDGE_COUNT <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES <= 0
        or EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES <= 0
        or len(EXPECTED_GAUSSIAN_FACTORIZATION_ORDERED_NAMES_SHA256) != 64
        or len(EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256) != 64):
        raise GaussianFactorizationError("the gaussian-factorization release is not sealed for checked use")
    browser=Path("/lab/proof-artifacts")/GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME
    source=browser if browser.is_file() else ROOT/"research/arithmetic-library/artifacts"/GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME
    payload=source.read_bytes()
    if len(payload)!=EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES or sha256(payload).hexdigest()!=EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256:
        raise GaussianFactorizationError("the immutable gaussian-factorization proof artifact changed")
    bundle,target=decode_proof_bundle(payload.decode("utf-8"))
    plan=gaussian_factorization_plan(parent_specs=parent_specs)
    if (len(plan.frontier_names)!=EXPECTED_GAUSSIAN_FACTORIZATION_FRONTIER_COUNT
        or len(plan.rows)!=EXPECTED_GAUSSIAN_FACTORIZATION_THEOREM_COUNT
        or len(plan.root_names)!=EXPECTED_GAUSSIAN_FACTORIZATION_ROOT_COUNT
        or plan.dependency_edge_count!=EXPECTED_GAUSSIAN_FACTORIZATION_DEPENDENCY_EDGE_COUNT
        or plan.ordered_names_sha256!=EXPECTED_GAUSSIAN_FACTORIZATION_ORDERED_NAMES_SHA256):
        raise GaussianFactorizationError("the exact sealed gaussian-factorization inventory changed")
    receipt=check_gaussian_factorization_proof_bundle(bundle,target,parent_specs=parent_specs)
    if (receipt.node_count!=EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_NODE_COUNT
        or receipt.kernel_calls!=EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_NODE_COUNT
        or receipt.dependency_edges!=EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_EDGE_COUNT
        or receipt.total_body_nodes!=EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES):
        raise GaussianFactorizationError("the sealed gaussian-factorization original-kernel metrics changed")
    return bundle,receipt


def gaussian_factorization_bundle(*,parent_specs: tuple[TheoremSpec,...]|None=None) -> tuple[ProofBundle,CheckedProofBundle]:
    """Public two-item provider; the edition wrapper adds theorem positions."""
    return checked_gaussian_factorization_proof_bundle(parent_specs=parent_specs)


def replay_gaussian_factorization_theorem(name: str,bundle: ProofBundle,target: Formula,*,campaigns: tuple[str,...]=(),parent_specs: tuple[TheoremSpec,...]|None=None) -> CheckedTheorem:
    """Materialize and kernel-check one ordinary empty-context candidate proof.

    This mirrors the existing conservative runtime proof compiler, but does
    not create an edition entry, grant checked use, or rely on a proof cache.
    """
    check_gaussian_factorization_proof_bundle(bundle,target,campaigns=campaigns,parent_specs=parent_specs)
    plan = gaussian_factorization_plan(campaigns,parent_specs=parent_specs)
    positions = {row.name:row.node_id for row in plan.rows}
    if type(name) is not str or name not in positions:
        raise GaussianFactorizationError("unknown actual candidate dependency-cone theorem")
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
        raise GaussianFactorizationError("the candidate exceeded unchanged conservative sharing limits")
    for original,actual in zip(layered.nodes,interned.nodes,strict=True):
        if (original.node_id != actual.node_id or original.target != actual.target
            or original.dependencies != actual.dependencies):
            raise GaussianFactorizationError("conservative interning changed the exact candidate graph")
        body_target = actual.target
        for dependency in reversed(actual.dependencies):
            body_target = Imp(bundle.nodes[dependency].target,body_target)
        if not check((),actual.body,body_target):
            raise GaussianFactorizationError("the original kernel rejected an interned ordinary body")
    candidate = compile_gaussian_factorization_replay(interned,formula,limits=DEFAULT_LAYERED_REPLAY_LIMITS)
    if candidate is None or not check((),candidate.certificate,formula):
        raise GaussianFactorizationError("the unchanged kernel/resource policy rejected the materialized empty-context theorem")
    return CheckedTheorem(specification,formula,candidate.certificate,candidate.proof_nodes)


def assemble_gaussian_factorization_proof_bundle(*,campaigns: tuple[str,...]=(),batch_size: int=1,seed_bundles: tuple[str|Path,...]=(),report: Callable[[str],None]=print) -> CheckedGaussianFactorizationBundle:
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH_ROWS:
        raise GaussianFactorizationError("Gaussian factorization authoring batches must contain 1..16 rows")
    if type(seed_bundles) is not tuple or any(not isinstance(p,(str,Path)) for p in seed_bundles):
        raise GaussianFactorizationError("candidate seeds must be an explicit tuple of proof-bundle paths")
    if len({str(Path(p).resolve()) for p in seed_bundles}) != len(seed_bundles):
        raise GaussianFactorizationError("candidate seed paths must be distinct")
    validate_candidate_source_bytes(campaigns)
    plan,table = gaussian_factorization_plan(campaigns),_table(campaigns)
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
                max_envelope_depth=limits.max_body_envelope_depth,label=f"Gaussian factorization body {row.name}")
            occurrences += count
            identities += objects
            bodies[row.name] = body
            origins[row.name] = ("new_script" if row.campaign else "parent_script",None)
        report(f"gaussian-factorization batch {offset//batch_size+1}: {len(batch)} bodies, {occurrences} nodes, {identities} objects ({min(offset+batch_size,len(rebuilt))}/{len(rebuilt)})")
        gc.collect()
    positions = {r.name:r.node_id for r in plan.rows}
    nodes = [BundleNode(r.node_id,_closed_formula(table[r.name].statement),tuple(positions[d] for d in r.dependencies),bodies[r.name]) for r in plan.rows]
    target,body = _packaging_root(tuple(_closed_formula(table[name].statement) for name in plan.root_names))
    nodes.append(BundleNode(len(nodes),target,tuple(positions[name] for name in plan.root_names),body))
    bundle = ProofBundle(tuple(nodes),len(nodes)-1)
    receipt = check_gaussian_factorization_proof_bundle(bundle,target,campaigns=campaigns)
    return CheckedGaussianFactorizationBundle(bundle,target,receipt,tuple((r.name,*origins[r.name]) for r in plan.rows))


def export_gaussian_factorization_proof_bundle(output: str|Path,*,campaigns: tuple[str,...]=(),batch_size: int=1,seed_bundles: tuple[str|Path,...]=()) -> CheckedGaussianFactorizationBundle:
    destination = Path(output)
    if destination.exists():
        raise GaussianFactorizationError("candidate export never overwrites an existing artifact")
    result = assemble_gaussian_factorization_proof_bundle(campaigns=campaigns,batch_size=batch_size,seed_bundles=seed_bundles,report=lambda text:print(text,flush=True))
    payload = encode_proof_bundle(result.bundle,result.target)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("x",encoding="utf-8") as output_file:
        output_file.write(payload)
    raw = payload.encode("utf-8")
    print(f"NON-ADMITTING gaussian-factorization original-kernel ACCEPT: nodes={result.receipt.node_count}; edges={result.receipt.dependency_edges}; body-nodes={result.receipt.total_body_nodes}; bytes={len(raw)}; sha256={sha256(raw).hexdigest()}",flush=True)
    return result


def main(argv: Sequence[str]|None=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path,help="new non-admitting artifact; existing files are never overwritten")
    parser.add_argument("--campaign",action="append",choices=tuple(dict.fromkeys(f.campaign for f in FACTORIES)),default=[])
    parser.add_argument("--batch-size",type=int,default=1)
    parser.add_argument("--seed-bundle",action="append",type=Path,default=[],help="explicit self-contained candidate proof data; every seed body is freshly kernel-checked")
    args = parser.parse_args(argv)
    export_gaussian_factorization_proof_bundle(args.output,campaigns=tuple(args.campaign),batch_size=args.batch_size,seed_bundles=tuple(args.seed_bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
