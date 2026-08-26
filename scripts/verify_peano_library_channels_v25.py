#!/usr/bin/env python3
"""Independently verify the fully proof-closed additive Alpha-v25 release."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v25 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v25 as v25
from peano_lab.library.alpha_enrollment_v25 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V25_EXPECTED_COUNT,
    FRONTIER_V25_EXPECTED_NAMES_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v25_enrollment,
)


EXPECTED_CAMPAIGNS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
FRONTIER_ROOT_NAMES = tuple(ROOT_STATEMENT_SHA256)
INDEPENDENT_BREAKTHROUGH_STATEMENT_SHA256 = {
    "signed_cofactor_minor_family_exists": "8486fcb74e3c32d6967e4ec4a3058c06ef7d2a6b031551e0722f73ce62b0355c",
    "signed_alternating_cofactor_fold_exists_unique": "cded0e0b36963f8d799d0b1a2d5a89b58ca00219d40e378bdd31cfc58addfbd5",
    "signed_matrix_cofactor_family_and_fold_exists": "1f013b934c7540f73e135257094d612345f43f3163b5ee7280dbe97f4f142d2a",
    "beta_horner_taylor_remainder_exists": "5df4c9bd62d28df38c7fdcd0daf41c5fddf518942db92a74ac3a17676033ed82",
    "hensel_correction_exists_unique": "116197e3bebc5a3e2ee9290c2826b209e4d7f3047121533cc22c8e32324c3d70",
    "beta_horner_hensel_lift_divisibility": "9ddf76110a1036269b8a07f6d80cd83bd26ea3ed7c6416508e1193dc7bbc506b",
    "beta_horner_hensel_lift_exists": "9cfc4633ea27c492b0deb35a56fe44b25b8dbf50d56fb27f29285f74b6c58a8b",
    "crt_prefix_solution_implies_pairwise_compatible": "4b114040f7ff0a3e9e98279d8600d587741ebedcd598de06f2d899caad6fde1d",
    "crt_merge_compatible_prefix_solution_exists": "1e30822d43996807abe877aa76d88026a59c293dfe440ed00461e6a4eb17acc9",
    "crt_merge_compatible_prefix_canonical_exists_unique": "9e3d68192e707b5953b2fd3c9e4716e9fe90317f63be49734bbed00e3492b927",
    "crt_is_gcd_scale": "abe947735d13b946283776bfb832f7f0e8dc17861fbd0850c5b7b51827d68f77",
    "crt_is_gcd_coprime_product": "e3b28cbcdf65cdad1e51c834812bf2efb8a45cb534bb8a5daa1e4245b4d0a347",
    "crt_gcd_lcm_distributes_divisibility": "0ac6861e424c4c961810fe6565850227601a3c79438256678a50f8df25a544dd",
    "crt_pairwise_compatible_dominating_last_canonical_exists_unique": "f249f7835eb127e8d5f15e74b3d4344d5d98503d8b01394d608bf2e677823fb0",
}
FORBIDDEN_UNPROVED_CLAIMS = frozenset(
    {
        "integer_matrix_arbitrary_determinant_exists",
        "signed_matrix_arbitrary_determinant_exists",
        "integer_matrix_rank_exists",
        "lattice_basis_reduction_exists",
        "simple_root_hensel_lifting",
        "hensel_simple_root_lift_exists",
        "hensel_canonical_power_lift_exists_unique",
        "crt_pairwise_compatible_prefix_canonical_exists_unique",
        "generalized_pairwise_compatible_crt_prefix_canonical_exists_unique",
        "crt_pairwise_compatible_prefix_implies_merge_compatible",
        "finite_field_irreducible_factorization",
    }
)


def _fail(message: str) -> None:
    raise ValueError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"cannot read {path}: {error}")
    if type(value) is not dict:
        _fail(f"{path} must contain a JSON object")
    return value


def _verify_inherited_evidence_documents(
    documents: dict[str, dict[str, Any]], parent: dict[str, Any]
) -> None:
    inventory = parent.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v25 lost its immutable Alpha-v24 evidence-document inventory")
    inherited: dict[str, dict[str, Any]] = {}
    for record in inventory:
        if type(record) is not dict or type(record.get("path")) is not str:
            _fail("Alpha-v25 inherited a malformed Alpha-v24 evidence-document binding")
        path = record["path"]
        if path in inherited:
            _fail(f"duplicate immutable Alpha-v24 evidence-document binding {path!r}")
        inherited[path] = record
        if documents.get(path) != record:
            _fail(f"Alpha-v25 changed immutable Alpha-v24 evidence-document binding {path!r}")

    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = inherited.get(path)
    if (
        record is None
        or record.get("path") != path
        or record.get("sha256") != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or type(record.get("bytes")) is not int
        or record["bytes"] != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        _fail("Alpha-v25 changed its immutable quadratic-reciprocity corpus catalog binding")
    try:
        payload = builder.IMMUTABLE_QR_CORPUS.read_bytes()
    except OSError as error:
        _fail(f"immutable quadratic-reciprocity corpus evidence is unavailable: {error}")
    if (
        len(payload) != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
        or sha256(payload).hexdigest() != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
    ):
        _fail("immutable quadratic-reciprocity corpus evidence bytes changed")


def _documents(
    catalog: dict[str, Any], *, parent: dict[str, Any] | None = None
) -> dict[str, dict[str, Any]]:
    inventory = catalog.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v25 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if (
            type(item) is not dict
            or type(item.get("path")) is not str
            or type(item.get("sha256")) is not str
            or type(item.get("bytes")) is not int
        ):
            _fail("Alpha-v25 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v25 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v25_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        record = result.get(path)
        if record is None:
            _fail(f"missing Alpha-v25 actual-proof control document {path!r}")
        try:
            payload = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v25 actual-proof source {path!r}: {error}")
        if record["sha256"] != sha256(payload).hexdigest():
            _fail(f"changed Alpha-v25 actual-proof control document {path!r}")
        if record["bytes"] != len(payload):
            _fail(f"changed Alpha-v25 actual-proof byte count {path!r}")

    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v25 lost its immutable sealed Alpha-v24 parent document")
    _verify_inherited_evidence_documents(
        result, _load(builder.PARENT_ALPHA) if parent is None else parent
    )
    return result


def _expected_evidence_links(
    *, source: str, test: str, rfc: str, node_id: int,
    documents: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    parent = builder._repository_path(builder.PARENT_ALPHA)
    specifications = (
        (source, "alpha_v25_frontier_dependency_curried_body", "dependency_curried_body", "document"),
        (test, "alpha_v25_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
        (rfc, "alpha_v25_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
        (
            builder.CLOSURE_ARTIFACT,
            "alpha_v25_breakthrough_layer_self_contained_constructive_proof_bundle",
            "independently_kernel_checked_dependency_closed_proof",
            f"nodes[id={node_id}]",
        ),
        (
            builder.CLOSURE_RECEIPT,
            "alpha_v25_breakthrough_layer_original_kernel_receipt",
            "original_kernel_independent_dependency_closure_verification",
            "document",
        ),
        (parent, "sealed_alpha_v24_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
    )
    return [
        {
            "document_sha256": documents[path]["sha256"],
            "kind": kind,
            "path": path,
            "role": role,
            "selector": selector,
        }
        for path, kind, role, selector in specifications
    ]


def _verify_frontier_row(
    row: dict[str, Any], *, index: int, bundle: Any, receipt: Any,
    node_id: int, documents: dict[str, dict[str, Any]],
) -> None:
    enrollment = alpha_v25_enrollment()
    spec = enrollment.frontier_specs[index - builder.EXPECTED_PARENT_COUNT]
    name = spec.name
    if row.get("name") != name:
        _fail(f"frontier theorem changed its exact additive order at index {index}")
    campaign = enrollment.campaign_by_name[name].value
    source = enrollment.source_by_name[name]
    test = enrollment.test_by_name[name]
    rfc = enrollment.rfc_by_name[name]
    expected = {
        "body_checked": True,
        "checked_use": True,
        "dependencies": list(spec.dependencies),
        "dependencies_sha256": sha256(("\n".join(spec.dependencies) + "\n").encode()).hexdigest(),
        "enrollment_index": index,
        "enrollment_origin": "ha",
        "evidence_status": "alpha_closed",
        "frontier_campaign": campaign,
        "logical_spec_sha256": base._logical_spec_sha256(spec),
        "membership": "alpha_only",
        "name": name,
        "proof_tag": None,
        "provenance": ["ha"],
        "script": list(spec.script),
        "script_sha256": sha256(("\n".join(spec.script) + "\n").encode()).hexdigest(),
        "source": {"kind": "candidate_module", "path": source, "sha256": documents[source]["sha256"]},
        "statement": spec.statement,
        "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
        "summary": spec.summary,
        "summary_sha256": sha256(spec.summary.encode()).hexdigest(),
    }
    expected_keys = {
        *expected, "body_receipt", "empty_context_closure",
        "alpha_v25_frontier_enrollment", "evidence_links",
    }
    if set(row) != expected_keys:
        _fail(f"frontier theorem {name!r} changed its exact immutable field set")
    for key, value in expected.items():
        actual = row.get(key)
        if actual != value or (type(value) is bool and actual is not value):
            _fail(f"frontier theorem {name!r} changed exact source-bound field {key!r}")

    body = bundle.nodes[node_id].body
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    body_receipt = {
        "command_count": len(spec.script), "dependency_count": len(spec.dependencies),
        "dne_command_count": 0, "name": name, "proof_depth": depth,
        "proof_edges": edges, "proof_nodes": nodes, "proof_objects": objects,
        "reused_objects": reused, "status": "kernel_checked_dependency_curried_body",
    }
    if row.get("body_receipt") != body_receipt:
        _fail(f"frontier theorem {name!r} changed its independent original-kernel body receipt")
    artifact_digest = documents[builder.CLOSURE_ARTIFACT]["sha256"]
    transition = {
        "body_receipt_sha256": builder._digest(builder._compact(body_receipt)),
        "bundle_campaign": "breakthrough_layer", "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest, "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if row.get("alpha_v25_frontier_enrollment") != transition:
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    closure = {
        "body_proof_depth": depth, "body_proof_nodes": nodes,
        "bundle_campaign": "breakthrough_layer",
        "bundle_dependency_edge_count": receipt.dependency_edges,
        "bundle_node_count": receipt.node_count, "bundle_node_id": node_id,
        "bundle_path": builder.CLOSURE_ARTIFACT, "bundle_root_id": bundle.root,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": artifact_digest,
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": row["statement_sha256"], "status": "checked",
    }
    if row.get("empty_context_closure") != closure:
        _fail(f"frontier theorem {name!r} changed its actual checked proof binding")

    links = row.get("evidence_links")
    if type(links) is not list:
        _fail(f"frontier theorem {name!r} has malformed source/proof evidence links")
    expected_links = _expected_evidence_links(
        source=source, test=test, rfc=rfc, node_id=node_id, documents=documents
    )
    required = {item["path"] for item in expected_links}
    if {item.get("path") for item in links if type(item) is dict} != required:
        _fail(f"frontier theorem {name!r} lost a source/test/RFC/proof/parent link")
    if len(links) != len(required):
        _fail(f"frontier theorem {name!r} duplicated a source/proof evidence link")
    for item in links:
        path = item["path"]
        if item.get("document_sha256") != documents[path]["sha256"]:
            _fail(f"frontier theorem {name!r} changed evidence-document digest {path!r}")
    proof_link = next(item for item in links if item["path"] == builder.CLOSURE_ARTIFACT)
    if proof_link.get("selector") != f"nodes[id={node_id}]":
        _fail(f"frontier theorem {name!r} changed its exact proof-node selector")
    if links != expected_links:
        _fail(f"frontier theorem {name!r} changed exact evidence-link authority or order")


def _verify_truthful_boundaries(names: set[str]) -> None:
    missing = set(FRONTIER_ROOT_NAMES).difference(names)
    if missing:
        _fail(f"Alpha-v25 omitted a genuine constructive boundary root: {sorted(missing)!r}")
    invented = FORBIDDEN_UNPROVED_CLAIMS.intersection(names)
    if invented:
        _fail(f"Alpha-v25 falsely admitted an unproved ambitious boundary: {sorted(invented)!r}")
    for name, expected in INDEPENDENT_BREAKTHROUGH_STATEMENT_SHA256.items():
        source = v25.ALPHA_EDITION.by_name[name].spec
        if sha256(source.statement.encode()).hexdigest() != expected:
            _fail(f"Alpha-v25 changed independently pinned breakthrough statement {name!r}")
    matrix = v25.ALPHA_EDITION.by_name["signed_matrix_cofactor_family_and_fold_exists"].spec
    hensel = v25.ALPHA_EDITION.by_name["beta_horner_hensel_lift_exists"].spec
    merge = v25.ALPHA_EDITION.by_name["crt_merge_compatible_prefix_canonical_exists_unique"].spec
    dominating = v25.ALPHA_EDITION.by_name[
        "crt_pairwise_compatible_dominating_last_canonical_exists_unique"
    ].spec
    if (
        not matrix.statement.startswith("forall")
        or "cofactor" not in matrix.summary.lower()
        or "crt_merge_compatible_prefix_solution_exists" not in merge.dependencies
        or "crt_pairwise_compatible_dominating_last_solution" not in dominating.dependencies
        or "correction" not in hensel.summary.lower()
        or "next modulus" not in hensel.summary.lower()
    ):
        _fail("Alpha-v25 misrepresented its still-open determinant/Hensel/generalized-CRT boundaries")


def _verify_independent_lean_evidence(
    promotion: dict[str, Any], proof_record: dict[str, Any]
) -> None:
    if (
        promotion.get("independent_lean_bundle_verified") is not True
        or proof_record.get("independent_lean_bundle_verified") is not True
    ):
        _fail("Alpha-v25 omitted independently compiled Lean proof-bundle verification")


def _verify_rows(
    rows: list[dict[str, Any]], parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]], checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != v25.EXPECTED_ALPHA_V25_COUNT
    ):
        _fail("Alpha-v25 changed its exact 2,008-row parent or additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v25 lacks its independently checked breakthrough-layer proof bundle")
    bundle, receipt, positions = checked
    if type(positions) is not dict:
        _fail("Alpha-v25 lacks exact independently checked proof-node positions")
    for index, old in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(old) is not dict:
            _fail(f"Alpha-v25 historical theorem row {index} is malformed")
        name = str(old.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v25 changed immutable theorem order at index {index}")
        if row != old:
            _fail(f"Alpha-v25 modified immutable Alpha-v24 parent row {name!r}")
    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, v25.EXPECTED_ALPHA_V25_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v25 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row, index=index, bundle=bundle, receipt=receipt,
            node_id=positions[name], documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v25.FRONTIER_NEW_NAMES:
        _fail("Alpha-v25 changed its exact ordered additive theorem frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V25_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v25 changed its sealed additive theorem-name digest")
    if (
        campaigns != Counter(EXPECTED_CAMPAIGNS)
        or campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
    ):
        _fail("Alpha-v25 changed its exact three constructive theorem-family counts")
    expected_evidence = Counter(
        stable_closed=builder.EXPECTED_STABLE_COUNT,
        alpha_closed=v25.EXPECTED_ALPHA_V25_COUNT - builder.EXPECTED_STABLE_COUNT,
    )
    if Counter(row.get("evidence_status") for row in rows) != expected_evidence:
        _fail("Alpha-v25 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v25 retained an unchecked theorem in its completely checked edition")
    available: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= available:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in available:
            _fail(f"Alpha-v25 duplicated the checked theorem {name!r}")
        available.add(name)
        edges += len(dependencies)
    if (
        len(available) != v25.EXPECTED_ALPHA_V25_COUNT
        or edges != v25.EXPECTED_ALPHA_V25_EDGE_COUNT
    ):
        _fail("Alpha-v25 changed its complete original-kernel-checked dependency DAG")
    _verify_truthful_boundaries(set(frontier))


def _verify_topology(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    topology = metrics.get("dependency_graph")
    if type(topology) is not dict:
        _fail("Alpha-v25 lost its complete checked dependency graph")
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    kept = [{"dependency": dep, "theorem": theorem} for dep, theorem in kept_edges]
    redundant = [{"dependency": dep, "theorem": theorem} for dep, theorem in redundant_edges]
    counts = Counter(depths.values())
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_origins = Counter(origins[name] for _dependency, name in redundant_edges)
    parent = _load(builder.PARENT_ALPHA_METRICS)["dependency_graph"]
    if (
        topology.get("declared_edge_count") != v25.EXPECTED_ALPHA_V25_EDGE_COUNT
        or topology.get("layer_count") != v25.EXPECTED_ALPHA_V25_LAYER_COUNT
        or max(depths.values(), default=-1) + 1 != v25.EXPECTED_ALPHA_V25_LAYER_COUNT
        or topology.get("dependency_free_theorem_count") != sum(not row["dependencies"] for row in rows)
        or topology.get("maximum_direct_dependency_count") != max(len(row["dependencies"]) for row in rows)
        or topology.get("maximum_transitive_dependency_count") != max(map(len, closures.values()), default=0)
        or topology.get("theorems_by_depth") != {str(depth): count for depth, count in sorted(counts.items())}
        or topology.get("transitive_reduction_edge_count") != len(kept)
        or topology.get("transitive_reduction_edge_sha256") != builder._digest(builder._compact(kept))
        or topology.get("reachability_redundant_direct_dependencies") != redundant
        or topology.get("reachability_redundant_direct_dependency_count") != len(redundant)
        or topology.get("reachability_redundant_direct_dependency_count_by_enrollment_origin") != dict(sorted(redundant_origins.items()))
        or topology.get("reachability_redundant_direct_dependency_sha256") != builder._digest(builder._compact(redundant))
        or topology.get("reachability_reduction_scope") != parent["reachability_reduction_scope"]
        or topology.get("transitive_reduction_preserves_reachability") is not True
    ):
        _fail("Alpha-v25 changed independently derived checked-DAG topology")


def verify(*, verify_roots: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v25 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v25 artifact schemas changed")
    rows = catalog.get("theorems")
    evidence = {
        "alpha_closed": v25.EXPECTED_ALPHA_V25_COUNT - builder.EXPECTED_STABLE_COUNT,
        "stable_closed": builder.EXPECTED_STABLE_COUNT,
    }
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or metrics.get("theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != v25.EXPECTED_ALPHA_V25_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != v25.EXPECTED_ALPHA_V25_CHECKED_USE_COUNT
        or catalog.get("edge_count") != v25.EXPECTED_ALPHA_V25_EDGE_COUNT
        or catalog.get("layer_count") != v25.EXPECTED_ALPHA_V25_LAYER_COUNT
        or catalog.get("evidence_counts") != evidence
    ):
        _fail("Alpha-v25 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v25.ALPHA_V25_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v25.ALPHA_V25_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256") != base._ordered_root(v25.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v25 changed exact additive enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v24") != builder._parent_binding():
        _fail("Alpha-v25 lost exact sealed Alpha-v24 artifact provenance")

    documents = _documents(catalog, parent=parent)
    # Executes the unchanged independent HA kernel AND the compiled Lean verifier.
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        catalog.get("alpha_v25_breakthrough_layer_promotion") != promotion
        or metrics.get("alpha_v25_breakthrough_layer_promotion") != promotion
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V25_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != v25.EXPECTED_ALPHA_V25_COUNT
        or promotion.get("campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v25 changed its exact breakthrough-layer additive proof evidence")
    proof = promotion.get("proof_bundle")
    if (
        type(proof) is not dict
        or proof.get("artifact_sha256") != documents[builder.CLOSURE_ARTIFACT]["sha256"]
        or proof.get("node_count") != len(bundle.nodes)
        or proof.get("kernel_calls") != receipt.kernel_calls
        or receipt.kernel_calls != len(bundle.nodes)
        or proof.get("dependency_edges") != receipt.dependency_edges
        or proof.get("body_proof_nodes") != receipt.total_body_nodes
    ):
        _fail("Alpha-v25 changed independently checked breakthrough-layer proof metrics")
    _verify_independent_lean_evidence(promotion, proof)
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v25 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed" or full.get("checked") != v25.EXPECTED_ALPHA_V25_COUNT
        or full.get("missing") != 0 or full.get("required") != v25.EXPECTED_ALPHA_V25_COUNT
    ):
        _fail("Alpha-v25 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    historical = _load(builder.PARENT_ALPHA_METRICS)["checked_closure_metrics"]
    expected_digests = historical["certificate_digest_kinds"][
        "self-contained-proof-bundle-sha256"
    ] + FRONTIER_V25_EXPECTED_COUNT
    if (
        accounting.get("metric_bearing_theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        ) != expected_digests
    ):
        _fail("Alpha-v25 misstated its complete independently checked proof accounting")
    campaign = accounting.get("campaign_v25_bundle_accounting", {})
    if (
        campaign.get("campaign_count") != len(EXPECTED_CAMPAIGNS)
        or campaign.get("new_checked_theorem_count") != FRONTIER_V25_EXPECTED_COUNT
        or campaign.get("campaign_counts") != EXPECTED_CAMPAIGNS
        or campaign.get("proof_bundle") != proof
        or gates.get("complete_constructive_alpha_v25_breakthrough_layer")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v25 changed exact breakthrough-layer proof-accounting gates")
    _verify_topology(rows, metrics)

    catalog_digest = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_digest = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_digest = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_digest
        or metrics.get("dependency_graph_sha256") != graph_digest
        or metrics.get("edition_identity_sha256") != v25.ALPHA_V25_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v25.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v25 catalog, dependency graph, or metrics artifact changed")
    old_channels = _load(builder.PARENT_CHANNELS)
    actual = channels.get("channels")
    if (
        type(actual) is not dict or channels.get("default_channel") != "stable"
        or actual.get("stable") != old_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256") != builder._digest(builder._compact(actual))
        or channels.get("parent_channels_v24") != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v25 changed immutable Stable pointer or default release channel")
    alpha = actual.get("alpha")
    if (
        type(alpha) is not dict or alpha.get("artifact_sha256") != catalog_digest
        or alpha.get("theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or alpha.get("checked_use_count") != v25.EXPECTED_ALPHA_V25_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v25.ALPHA_V25_IDENTITY_SHA256
        or alpha.get("parent_alpha_v24_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v25_frontier_new_count") != FRONTIER_V25_EXPECTED_COUNT
        or alpha.get("frontier_v25_campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v25 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_digest), ("metrics", metrics_digest), ("dependency_graph", graph_digest)
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v25 changed exact {key} channel pointer digest")

    # Avoid loading unrelated historical Alpha proof artifacts.
    result = v25.replay("zero_add", edition="stable")
    if not check((), result.certificate, result.formula):
        _fail("unchanged kernel rejected the immutable historical Stable theorem")
    if verify_roots:
        for name in FRONTIER_ROOT_NAMES:
            result = v25.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-roots", action="store_true")
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v25 independently: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={v25.EXPECTED_ALPHA_V25_COUNT}, "
        f"checked-use={v25.EXPECTED_ALPHA_V25_CHECKED_USE_COUNT}, "
        f"frontier-new={FRONTIER_V25_EXPECTED_COUNT}, "
        f"campaigns={len(EXPECTED_CAMPAIGNS)}, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
