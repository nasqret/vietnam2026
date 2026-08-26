#!/usr/bin/env python3
"""Independently verify immutable, original-kernel-checked Alpha v24."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v24 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v24 as v24
from peano_lab.library.alpha_enrollment_v24 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V24_EXPECTED_COUNT,
    FRONTIER_V24_EXPECTED_NAMES_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v24_enrollment,
)


MATRIX_DETERMINANT_MINOR_ROOT_NAMES = (
    "beta_matrix_minor_exists",
    "beta_signed_matrix_minor_exists",
    "signed_matrix_four_cofactor_expansion_exists",
    "signed_matrix_four_full_determinant_exists",
    "signed_matrix_four_full_determinant_functional",
)
POLYNOMIAL_DERIVATIVE_ROOT_NAMES = (
    "beta_horner_derivative_trace_exists",
    "beta_horner_derivative_value_exists",
    "beta_horner_derivative_successor_decompose",
    "beta_horner_derivative_functional",
    "beta_horner_derivative_exists_unique",
    "beta_horner_derivative_only_exists_unique",
    "beta_horner_derivative_constant",
    "beta_horner_derivative_linear",
)
FINITE_CRT_ROOT_NAMES = (
    "crt_prefix_lcm_exists_unique",
    "crt_pairwise_coprime_prefix_product_is_lcm",
    "crt_pairwise_coprime_prefix_solution_exists",
    "crt_prefix_solution_class_iff_lcm",
    "crt_pairwise_coprime_prefix_canonical_exists_unique",
)
INDEPENDENT_RESEARCH_STATEMENT_SHA256 = {
    "beta_matrix_minor_exists": (
        "3abfa041aa3df531be6ac5580a3167802703e2adc4ecf13ae77f19309a31a8ee"
    ),
    "beta_signed_matrix_minor_exists": (
        "bf6e9238c2928e4f6525a14015198b673b41022924c6da1944ab87c8df61bba1"
    ),
    "signed_matrix_four_full_determinant_exists": (
        "7ae77d34a56bc459140fcd9afab5bb70cf4792cdb6ebac833c448381adfff848"
    ),
    "signed_matrix_four_full_determinant_functional": (
        "d1987b1ba2337c22463858a07b85da4144d00f20f8e036c076d53d99de8ada59"
    ),
    "beta_horner_derivative_trace_exists": (
        "5a7dbce648cc7ab15e0f82e80e7ba87888e8e709102920acd67f761d88b98f24"
    ),
    "beta_horner_derivative_value_exists": (
        "b012d6a0d97002529f35f80264535daa5c21fb1ca6ca67a7a1d0561c1c0c5c51"
    ),
    "beta_horner_derivative_successor_decompose": (
        "042cb58aec7a7a63eaef9c83958feefbc51b1ce89e927010c2e9427f401b7435"
    ),
    "beta_horner_derivative_exists_unique": (
        "171b5939376bfb9e9ec9469d3addd98e27584931fa7994dccb4b372c4d9a693f"
    ),
    "beta_horner_derivative_only_exists_unique": (
        "60a8a62113371b7c5ae1784f965d107b6f985af1fb059438ff42a222b796447d"
    ),
    "beta_horner_derivative_constant": (
        "e3b4e0f787e0acb66efae5dda93c207cff2c4c40bafa1c54e878d667b25f7aea"
    ),
    "beta_horner_derivative_linear": (
        "154adc2aae62495917763842a52646ccff31b05c36b09bc0250e3a8ed5e9437e"
    ),
    "crt_prefix_lcm_exists_unique": (
        "09fa610c42ac069677f4fb90f00c6e0780d2b1de843380599e725a9cf19e1175"
    ),
    "crt_pairwise_coprime_prefix_solution_exists": (
        "6e61d9a848010dc5857fdacbc8efc3973e160a997a421a17100a867e1c501e68"
    ),
    "crt_prefix_solution_class_iff_lcm": (
        "a943495e7c8817cf917f4cc282502ad316a2a3ce9892c5d6bb3ba2ab0fbd6488"
    ),
    "crt_pairwise_coprime_prefix_canonical_exists_unique": (
        "6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f"
    ),
}
EXPECTED_CAMPAIGNS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
FRONTIER_ROOT_NAMES = tuple(
    dict.fromkeys(
        (
            *ROOT_STATEMENT_SHA256,
            *MATRIX_DETERMINANT_MINOR_ROOT_NAMES,
            *POLYNOMIAL_DERIVATIVE_ROOT_NAMES,
            *FINITE_CRT_ROOT_NAMES,
        )
    )
)
FORBIDDEN_UNPROVED_CLAIMS = frozenset(
    {
        "integer_matrix_arbitrary_determinant_exists",
        "signed_matrix_arbitrary_determinant_exists",
        "integer_matrix_rank_exists",
        "lattice_basis_reduction_exists",
        "effective_chebyshev_prime_bounds",
        "cauchy_davenport_sumset_bound",
        "simple_root_hensel_lifting",
        "hensel_simple_root_lift_exists",
        "crt_pairwise_compatible_prefix_canonical_exists_unique",
        "generalized_pairwise_compatible_crt_prefix_canonical_exists_unique",
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
    documents: dict[str, dict[str, Any]],
    parent: dict[str, Any],
) -> None:
    """Keep every inherited binding and independently check the frozen QR bytes."""

    inventory = parent.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v24 lost its immutable Alpha-v23 evidence-document inventory")
    inherited: dict[str, dict[str, Any]] = {}
    for record in inventory:
        if type(record) is not dict or type(record.get("path")) is not str:
            _fail("Alpha-v24 inherited a malformed Alpha-v23 evidence-document binding")
        path = record["path"]
        if path in inherited:
            _fail(f"duplicate immutable Alpha-v23 evidence-document binding {path!r}")
        inherited[path] = record
        if documents.get(path) != record:
            _fail(f"Alpha-v24 changed immutable Alpha-v23 evidence-document binding {path!r}")

    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = inherited.get(path)
    if (
        record is None
        or record.get("path") != path
        or record.get("sha256") != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or type(record.get("bytes")) is not int
        or record["bytes"] != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        _fail("Alpha-v24 changed its immutable quadratic-reciprocity corpus catalog binding")

    try:
        payload = builder.IMMUTABLE_QR_CORPUS.read_bytes()
    except OSError as error:
        _fail(f"immutable quadratic-reciprocity corpus evidence is unavailable: {error}")
    if (
        len(payload) != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
        or sha256(payload).hexdigest()
        != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
    ):
        _fail("immutable quadratic-reciprocity corpus evidence bytes changed")


def _documents(
    catalog: dict[str, Any],
    *,
    parent: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    inventory = catalog.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v24 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if (
            type(item) is not dict
            or type(item.get("path")) is not str
            or type(item.get("sha256")) is not str
            or type(item.get("bytes")) is not int
        ):
            _fail("Alpha-v24 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v24 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v24_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        record = result.get(path)
        if record is None:
            _fail(f"missing Alpha-v24 actual-proof control document {path!r}")
        try:
            payload = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v24 actual-proof source {path!r}: {error}")
        if record["sha256"] != sha256(payload).hexdigest():
            _fail(f"changed Alpha-v24 actual-proof control document {path!r}")
        if record["bytes"] != len(payload):
            _fail(f"changed Alpha-v24 actual-proof byte count {path!r}")

    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v24 lost its immutable sealed Alpha-v23 parent document")
    _verify_inherited_evidence_documents(
        result,
        _load(builder.PARENT_ALPHA) if parent is None else parent,
    )
    return result


def _expected_closure(
    *,
    row: dict[str, Any],
    node_id: int,
    proof_nodes: int,
    proof_depth: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "body_proof_depth": proof_depth,
        "body_proof_nodes": proof_nodes,
        "bundle_campaign": "research_layer",
        "bundle_dependency_edge_count": receipt.dependency_edges,
        "bundle_node_count": receipt.node_count,
        "bundle_node_id": node_id,
        "bundle_path": builder.CLOSURE_ARTIFACT,
        "bundle_root_id": bundle.root,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": documents[builder.CLOSURE_ARTIFACT]["sha256"],
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": row["statement_sha256"],
        "status": "checked",
    }


def _expected_evidence_links(
    *,
    source: str,
    test: str,
    rfc: str,
    node_id: int,
    documents: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    parent = builder._repository_path(builder.PARENT_ALPHA)
    specifications = (
        (
            source,
            "alpha_v24_frontier_dependency_curried_body",
            "dependency_curried_body",
            "document",
        ),
        (
            test,
            "alpha_v24_frontier_executable_audit",
            "statement_dependency_replay_mutation_audit",
            "document",
        ),
        (
            rfc,
            "alpha_v24_frontier_campaign_rfc",
            "reviewed_constructive_campaign_contract",
            "document",
        ),
        (
            builder.CLOSURE_ARTIFACT,
            "alpha_v24_research_layer_self_contained_constructive_proof_bundle",
            "independently_kernel_checked_dependency_closed_proof",
            f"nodes[id={node_id}]",
        ),
        (
            builder.CLOSURE_RECEIPT,
            "alpha_v24_research_layer_original_kernel_receipt",
            "original_kernel_independent_dependency_closure_verification",
            "document",
        ),
        (parent, "sealed_alpha_v23_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
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
    row: dict[str, Any],
    *,
    index: int,
    bundle: Any,
    receipt: Any,
    node_id: int,
    documents: dict[str, dict[str, Any]],
) -> None:
    enrollment = alpha_v24_enrollment()
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
        "dependencies_sha256": sha256(
            ("\n".join(spec.dependencies) + "\n").encode()
        ).hexdigest(),
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
        "source": {
            "kind": "candidate_module",
            "path": source,
            "sha256": documents[source]["sha256"],
        },
        "statement": spec.statement,
        "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
        "summary": spec.summary,
        "summary_sha256": sha256(spec.summary.encode()).hexdigest(),
    }
    expected_keys = {
        *expected,
        "body_receipt",
        "empty_context_closure",
        "alpha_v24_frontier_enrollment",
        "evidence_links",
    }
    if set(row) != expected_keys:
        _fail(f"frontier theorem {name!r} changed its exact immutable field set")
    for key, value in expected.items():
        actual = row.get(key)
        if actual != value or (type(value) is bool and actual is not value):
            _fail(f"frontier theorem {name!r} changed exact source-bound field {key!r}")

    body = bundle.nodes[node_id].body
    proof_nodes, proof_depth = proof_metrics(body)
    proof_objects, proof_edges, reused_objects = proof_identity_metrics(body)
    expected_receipt = {
        "command_count": len(spec.script),
        "dependency_count": len(spec.dependencies),
        "dne_command_count": 0,
        "name": name,
        "proof_depth": proof_depth,
        "proof_edges": proof_edges,
        "proof_nodes": proof_nodes,
        "proof_objects": proof_objects,
        "reused_objects": reused_objects,
        "status": "kernel_checked_dependency_curried_body",
    }
    if row.get("body_receipt") != expected_receipt:
        _fail(f"frontier theorem {name!r} changed its independent original-kernel body receipt")
    artifact_digest = documents[builder.CLOSURE_ARTIFACT]["sha256"]
    expected_transition = {
        "body_receipt_sha256": builder._digest(builder._compact(expected_receipt)),
        "bundle_campaign": "research_layer",
        "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest,
        "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if row.get("alpha_v24_frontier_enrollment") != expected_transition:
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    if row.get("empty_context_closure") != _expected_closure(
        row=row,
        node_id=node_id,
        proof_nodes=proof_nodes,
        proof_depth=proof_depth,
        bundle=bundle,
        receipt=receipt,
        documents=documents,
    ):
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
    for link in links:
        path = link["path"]
        if link.get("document_sha256") != documents[path]["sha256"]:
            _fail(f"frontier theorem {name!r} changed evidence-document digest {path!r}")
    proof_link = next(item for item in links if item["path"] == builder.CLOSURE_ARTIFACT)
    if proof_link.get("selector") != f"nodes[id={node_id}]":
        _fail(f"frontier theorem {name!r} changed its exact proof-node selector")
    if links != expected_links:
        _fail(f"frontier theorem {name!r} changed exact evidence-link authority or order")


def _verify_truthful_boundaries(names: set[str]) -> None:
    missing = set(FRONTIER_ROOT_NAMES).difference(names)
    if missing:
        _fail(f"Alpha-v24 omitted a genuine constructive boundary root: {sorted(missing)!r}")
    invented = FORBIDDEN_UNPROVED_CLAIMS.intersection(names)
    if invented:
        _fail(f"Alpha-v24 falsely admitted an unproved ambitious boundary: {sorted(invented)!r}")
    for name, digest in INDEPENDENT_RESEARCH_STATEMENT_SHA256.items():
        source = v24.ALPHA_EDITION.by_name[name].spec.statement
        if sha256(source.encode()).hexdigest() != digest:
            _fail(f"Alpha-v24 changed independently pinned research statement {name!r}")
    matrix = v24.ALPHA_EDITION.by_name[
        "beta_signed_matrix_minor_exists"
    ].spec
    determinant = v24.ALPHA_EDITION.by_name[
        "signed_matrix_four_full_determinant_exists"
    ].spec
    if (
        "arbitrary-dimensional" not in matrix.summary
        or "row and column" not in matrix.summary
        or "four-by-four" not in determinant.summary
        or "32 natural entry components" not in determinant.summary
    ):
        _fail("Alpha-v24 misrepresented actual arbitrary-dimensional minors or the signed four-by-four determinant")

    derivative = v24.ALPHA_EDITION.by_name[
        "beta_horner_derivative_exists_unique"
    ].spec
    if (
        "exactly one" not in derivative.summary
        or "formal-derivative" not in derivative.summary
    ):
        _fail("Alpha-v24 misrepresented its exact polynomial/formal-derivative evaluation")

    all_modulus_lcm = v24.ALPHA_EDITION.by_name[
        "crt_prefix_lcm_exists_unique"
    ].spec
    finite_crt = v24.ALPHA_EDITION.by_name[
        "crt_pairwise_coprime_prefix_canonical_exists_unique"
    ].spec
    if (
        "noncoprime and zero entries" not in all_modulus_lcm.summary
        or "positive pairwise-coprime" not in finite_crt.summary
        or not finite_crt.statement.startswith("forall r s b c l.")
    ):
        _fail("Alpha-v24 misrepresented its actual finite-list CRT scope or the still-open noncoprime G011 boundary")


def _verify_independent_lean_evidence(
    promotion: dict[str, Any], proof_record: dict[str, Any]
) -> None:
    if (
        promotion.get("independent_lean_bundle_verified") is not True
        or proof_record.get("independent_lean_bundle_verified") is not True
    ):
        _fail("Alpha-v24 omitted independently compiled Lean proof-bundle verification")


def _verify_rows(
    rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list
        or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != v24.EXPECTED_ALPHA_V24_COUNT
    ):
        _fail("Alpha-v24 changed its exact 1,949-row parent or additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v24 lacks its independently checked research-layer proof bundle")
    bundle, receipt, positions = checked
    if type(positions) is not dict:
        _fail("Alpha-v24 lacks exact independently checked proof-node positions")

    for index, parent in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(parent) is not dict:
            _fail(f"Alpha-v24 historical theorem row {index} is malformed")
        name = str(parent.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v24 changed immutable theorem order at index {index}")
        if row != parent:
            _fail(f"Alpha-v24 modified immutable Alpha-v23 parent row {name!r}")

    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, v24.EXPECTED_ALPHA_V24_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v24 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row,
            index=index,
            bundle=bundle,
            receipt=receipt,
            node_id=positions[name],
            documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v24.FRONTIER_NEW_NAMES:
        _fail("Alpha-v24 changed its exact ordered additive theorem frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V24_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v24 changed its sealed additive theorem-name digest")
    if (
        campaigns != Counter(EXPECTED_CAMPAIGNS)
        or campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
    ):
        _fail("Alpha-v24 changed its exact three constructive theorem-family counts")
    expected_evidence = Counter(
        stable_closed=builder.EXPECTED_STABLE_COUNT,
        alpha_closed=v24.EXPECTED_ALPHA_V24_COUNT - builder.EXPECTED_STABLE_COUNT,
    )
    if Counter(row.get("evidence_status") for row in rows) != expected_evidence:
        _fail("Alpha-v24 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v24 retained an unchecked theorem in its completely checked edition")

    available: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= available:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in available:
            _fail(f"Alpha-v24 duplicated the checked theorem {name!r}")
        available.add(name)
        edges += len(dependencies)
    if len(available) != v24.EXPECTED_ALPHA_V24_COUNT or edges != v24.EXPECTED_ALPHA_V24_EDGE_COUNT:
        _fail("Alpha-v24 changed its complete original-kernel-checked dependency DAG")
    _verify_truthful_boundaries(set(frontier))


def _verify_topology(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    topology = metrics.get("dependency_graph")
    if type(topology) is not dict:
        _fail("Alpha-v24 lost its complete checked dependency graph")
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    kept = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    redundant = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    depth_counts = Counter(depths.values())
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_by_origin = Counter(
        origins[theorem] for _dependency, theorem in redundant_edges
    )
    parent_topology = _load(builder.PARENT_ALPHA_METRICS)["dependency_graph"]
    if (
        topology.get("declared_edge_count") != v24.EXPECTED_ALPHA_V24_EDGE_COUNT
        or topology.get("layer_count") != v24.EXPECTED_ALPHA_V24_LAYER_COUNT
        or max(depths.values(), default=-1) + 1 != v24.EXPECTED_ALPHA_V24_LAYER_COUNT
        or topology.get("dependency_free_theorem_count")
        != sum(not row["dependencies"] for row in rows)
        or topology.get("maximum_direct_dependency_count")
        != max(len(row["dependencies"]) for row in rows)
        or topology.get("maximum_transitive_dependency_count")
        != max(map(len, closures.values()), default=0)
        or topology.get("theorems_by_depth")
        != {str(depth): count for depth, count in sorted(depth_counts.items())}
        or topology.get("transitive_reduction_edge_count") != len(kept)
        or topology.get("transitive_reduction_edge_sha256")
        != builder._digest(builder._compact(kept))
        or topology.get("reachability_redundant_direct_dependencies") != redundant
        or topology.get("reachability_redundant_direct_dependency_count") != len(redundant)
        or topology.get("reachability_redundant_direct_dependency_count_by_enrollment_origin")
        != dict(sorted(redundant_by_origin.items()))
        or topology.get("reachability_redundant_direct_dependency_sha256")
        != builder._digest(builder._compact(redundant))
        or topology.get("reachability_reduction_scope")
        != parent_topology["reachability_reduction_scope"]
        or topology.get("transitive_reduction_preserves_reachability") is not True
    ):
        _fail("Alpha-v24 changed independently derived checked-DAG topology")


def verify(*, verify_roots: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v24 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v24 artifact schemas changed")
    rows = catalog.get("theorems")
    evidence_counts = {
        "alpha_closed": v24.EXPECTED_ALPHA_V24_COUNT - builder.EXPECTED_STABLE_COUNT,
        "stable_closed": builder.EXPECTED_STABLE_COUNT,
    }
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != v24.EXPECTED_ALPHA_V24_COUNT
        or metrics.get("theorem_count") != v24.EXPECTED_ALPHA_V24_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != v24.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != v24.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or catalog.get("edge_count") != v24.EXPECTED_ALPHA_V24_EDGE_COUNT
        or catalog.get("layer_count") != v24.EXPECTED_ALPHA_V24_LAYER_COUNT
        or catalog.get("evidence_counts") != evidence_counts
    ):
        _fail("Alpha-v24 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v24.ALPHA_V24_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v24.ALPHA_V24_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256")
        != base._ordered_root(v24.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v24 changed exact additive enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v23") != builder._parent_binding():
        _fail("Alpha-v24 lost exact sealed Alpha-v23 artifact provenance")

    documents = _documents(catalog, parent=parent)
    # This call performs an actual unchanged-kernel check AND starts the
    # independently compiled Lean executable. Boolean claims alone never suffice.
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        catalog.get("alpha_v24_research_layer_promotion") != promotion
        or metrics.get("alpha_v24_research_layer_promotion") != promotion
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V24_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != v24.EXPECTED_ALPHA_V24_COUNT
        or promotion.get("campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v24 changed its exact research-layer additive proof evidence")
    proof_record = promotion.get("proof_bundle")
    if (
        type(proof_record) is not dict
        or proof_record.get("artifact_sha256")
        != documents[builder.CLOSURE_ARTIFACT]["sha256"]
        or proof_record.get("node_count") != len(bundle.nodes)
        or proof_record.get("kernel_calls") != receipt.kernel_calls
        or receipt.kernel_calls != len(bundle.nodes)
        or proof_record.get("dependency_edges") != receipt.dependency_edges
        or proof_record.get("body_proof_nodes") != receipt.total_body_nodes
    ):
        _fail("Alpha-v24 changed independently checked research-layer proof metrics")
    _verify_independent_lean_evidence(promotion, proof_record)
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v24 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed"
        or full.get("checked") != v24.EXPECTED_ALPHA_V24_COUNT
        or full.get("missing") != 0
        or full.get("required") != v24.EXPECTED_ALPHA_V24_COUNT
    ):
        _fail("Alpha-v24 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    parent_accounting = _load(builder.PARENT_ALPHA_METRICS)["checked_closure_metrics"]
    expected_bundle_digests = parent_accounting["certificate_digest_kinds"][
        "self-contained-proof-bundle-sha256"
    ] + FRONTIER_V24_EXPECTED_COUNT
    if (
        accounting.get("metric_bearing_theorem_count") != v24.EXPECTED_ALPHA_V24_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        ) != expected_bundle_digests
    ):
        _fail("Alpha-v24 misstated its complete independently checked proof accounting")
    campaign_accounting = accounting.get("campaign_v24_bundle_accounting", {})
    if (
        campaign_accounting.get("campaign_count") != len(EXPECTED_CAMPAIGNS)
        or campaign_accounting.get("new_checked_theorem_count") != FRONTIER_V24_EXPECTED_COUNT
        or campaign_accounting.get("campaign_counts") != EXPECTED_CAMPAIGNS
        or campaign_accounting.get("proof_bundle") != proof_record
        or gates.get("complete_constructive_alpha_v24_research_layer")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v24 changed exact research-layer proof-accounting gates")
    _verify_topology(rows, metrics)

    catalog_hash = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_hash = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_hash = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_hash
        or metrics.get("dependency_graph_sha256") != graph_hash
        or metrics.get("edition_identity_sha256") != v24.ALPHA_V24_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v24.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v24 catalog, dependency graph, or metrics artifact changed")

    historical = _load(builder.PARENT_CHANNELS)
    actual_channels = channels.get("channels")
    if (
        type(actual_channels) is not dict
        or channels.get("default_channel") != "stable"
        or actual_channels.get("stable") != historical["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256")
        != builder._digest(builder._compact(actual_channels))
        or channels.get("parent_channels_v23")
        != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v24 changed immutable Stable pointer or default release channel")
    alpha = actual_channels.get("alpha")
    if (
        type(alpha) is not dict
        or alpha.get("artifact_sha256") != catalog_hash
        or alpha.get("theorem_count") != v24.EXPECTED_ALPHA_V24_COUNT
        or alpha.get("checked_use_count") != v24.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v24.ALPHA_V24_IDENTITY_SHA256
        or alpha.get("parent_alpha_v23_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v24_frontier_new_count") != FRONTIER_V24_EXPECTED_COUNT
        or alpha.get("frontier_v24_campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v24 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_hash),
        ("metrics", metrics_hash),
        ("dependency_graph", graph_hash),
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v24 changed exact {key} channel pointer digest")

    # Keep the independent release pass memory-bounded: the new bundle has
    # already checked every inherited node in its actual dependency cone.
    # Replaying a small Stable theorem avoids loading an unrelated historical
    # Alpha proof artifact just to exercise the legacy replay route.
    simple = v24.replay("zero_add", edition="stable")
    if not check((), simple.certificate, simple.formula):
        _fail("unchanged kernel rejected the immutable historical Stable theorem")
    if verify_roots:
        for name in FRONTIER_ROOT_NAMES:
            result = v24.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-roots",
        action="store_true",
        help="also compile and independently check every exact campaign root",
    )
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v24 independently: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={v24.EXPECTED_ALPHA_V24_COUNT}, "
        f"checked-use={v24.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT}, "
        f"frontier-new={FRONTIER_V24_EXPECTED_COUNT}, "
        f"campaigns={len(EXPECTED_CAMPAIGNS)}, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
