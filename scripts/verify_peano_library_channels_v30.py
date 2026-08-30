#!/usr/bin/env python3
"""Independently verify the fully proof-closed additive Alpha-v30 release."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v30 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v30 as v30
from peano_lab.library.alpha_enrollment_v30 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V30_EXPECTED_COUNT,
    FRONTIER_V30_EXPECTED_NAMES_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v30_enrollment,
)
from constructive_formula_compactor import _LocalDefinedParser
from constructive_gaussian_factorization_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
from peano_lab.library.theorems import _closed_formula


EXPECTED_CAMPAIGNS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
INDEPENDENT_GAUSSIAN_FACTORIZATION_STATEMENT_SHA256 = {
    "gaussian_unit_iff_norm_one": "1c480f8f6989ba91bf2103bec39c839a75aa0b3026dc5314b8141643c178a6e7",
    "gaussian_divides_input_valid": "51aedd3767e25d58e936a98a37f4ec1a9b59c95be1976d3bff6b2592bc58ed6e",
    "gaussian_divides_value_valid": "75c9826a99881c9e9ea45b6947fe64d07aa7cac2d054bc0b0b34635e06bccc74",
    "gaussian_divides_product_right": "c667470627951c96a2d2164cf79a963e66516ed7d2918f69d33a15be79478bdd",
    "gaussian_unit_divides": "f652687bfc69e1eef958ea56e0708fa5be0dfd73929fde4bcc7bb031c2d04a97",
    "gaussian_divides_decidable": "c008dfc3987d6c5565c6f85a23eb9ce2b618f58b327d1336039bfde9fb606569",
    "gaussian_associate_reflexive": "7374976c09975f92cde7f3213b1a2b6bd2fabdd3b1fbec5bff75b2f7a5a86596",
    "gaussian_associate_norm": "aaa4519eb61ce02f4d998c2d6760c348e99a5917163b90e961316c04557166f9",
    "gaussian_divisor_norm_bound": "f5d18361d3f4a6b7dd50809d625b8775dcf964e1c57f03c91db76c1939012cad",
    "gaussian_gcd_bezout_zero_right": "5b8d4b9317e0c9cbbe61b8b952a01fd32d43769f28c7c192b53a02a133dd2e15",
    "gaussian_common_divisor_of_bezout": "be7b180bfff891f64f847a70791c677947f0f50876c8821eb4964d757ea34c9e",
    "gaussian_gcd_bezout_exists": "67d09aa8ff5c895839b29eb5f9f44d9d91087f8f2316698b47530795b800f981",
    "gaussian_gcd_unique_up_to_associate": "2ea8e4c57a49cecb2aee00f5611ef247500d39fe0f1fc1b239b478a49bd3a7c5",
    "gaussian_irreducible_dvd_product": "e2fb26736c7080feea9c73498dc0609b2e08cfdd89bdf16857afd0e6a9eb7620",
    "gaussian_irreducible_iff_prime": "aa8c5f0706fbabf6c9069ae0fd2a7f7b3ecf9651b30bad9d7b4483fbd6d2689e",
    "gaussian_irreducible_decidable": "d2dda07b5adbba8a24df4aacbc1921b52c969822b96f7bbd9a61b484784bc3e9",
    "gaussian_prime_factorization_exists": "86d207a622593e87fc60e4c852a6aabb8e6b1057b960cbadc7e2ac736aae827b",
    "gaussian_factorization_value_valid": "287c3e10b11f20850b983fccafccff71dcd688966eabc0aecaf62ea187092edb",
    "gaussian_product_replace_balance_iff": "f9b481d187747f5c3084772a722011398d5f5692e2b7174f8a2d9215505c0f7c",
    "gaussian_unique_prime_factorization": "57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219",
    "gaussian_zero_has_no_prime_factorization": "98f2d733c8b7cab7fce0324135b3985336b1cb9922936d723adf48379a213034",
    "gaussian_unit_prime_factorization_length_zero": "66bcf4d61ae664d21b59e77b66203fe3b2cffb1d360d4263f228984dd2f66b1b",
    "gaussian_prime_factorizations_unique": "25362a390050bdd2b6b56a18b91f738860c534cb96779b0bdbeba3ef30064865"
}
# The public audit also covers the independent uniqueness companion, in
# addition to all 22 immutable enrollment endpoints.
FRONTIER_ROOT_NAMES = tuple(INDEPENDENT_GAUSSIAN_FACTORIZATION_STATEMENT_SHA256)

FORBIDDEN_UNPROVED_CLAIMS = frozenset(
    {
        "gaussian_sorted_primary_prime_factorization",
        "gaussian_literal_factor_list_uniqueness",
        "eisenstein_unique_factorization_exists",
        "gaussian_prime_classification_complete",
        "eisenstein_prime_classification_complete",
        "eisenstein_gcd_algorithm_complete",
        "lattice_basis_reduction_exists",
        "integer_lattice_independent_basis_exists",
        "integer_lattice_smith_normal_form_exists",
        "integer_lattice_hermite_normal_form_exists",
        "integer_lattice_lll_reduced_basis_exists",
        "finite_field_irreducible_factorization",
        "prime_number_theorem",
        "dirichlet_arithmetic_progressions",
    }
)


def _fail(message: str) -> None:
    raise ValueError(message)


def _exact_json(actual: object, expected: object) -> bool:
    """Unlike Python equality, release evidence never identifies 0/False or 1/True."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return actual.keys() == expected.keys() and all(
            _exact_json(actual[key], value) for key, value in expected.items()
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _exact_json(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON field {key!r} in release evidence")
        result[key] = value
    return result


def _nonfinite_constant(value: str) -> None:
    _fail(f"non-finite JSON constant {value!r} in release evidence")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_nonfinite_constant,
        )
    except (OSError, ValueError) as error:
        _fail(f"cannot read {path}: {error}")
    if type(value) is not dict:
        _fail(f"{path} must contain a JSON object")
    return value


def _verify_inherited_evidence_documents(
    documents: dict[str, dict[str, Any]], parent: dict[str, Any]
) -> None:
    inventory = parent.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v30 lost its immutable Alpha-v29 evidence-document inventory")
    inherited: dict[str, dict[str, Any]] = {}
    for record in inventory:
        if type(record) is not dict or type(record.get("path")) is not str:
            _fail("Alpha-v30 inherited a malformed Alpha-v29 evidence-document binding")
        path = record["path"]
        if path in inherited:
            _fail(f"duplicate immutable Alpha-v29 evidence-document binding {path!r}")
        inherited[path] = record
        if not _exact_json(documents.get(path), record):
            _fail(f"Alpha-v30 changed immutable Alpha-v29 evidence-document binding {path!r}")

    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = inherited.get(path)
    if (
        record is None
        or record.get("path") != path
        or record.get("sha256") != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or type(record.get("bytes")) is not int
        or record["bytes"] != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        _fail("Alpha-v30 changed its immutable quadratic-reciprocity corpus catalog binding")
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
        _fail("Alpha-v30 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if (
            type(item) is not dict
            or type(item.get("path")) is not str
            or type(item.get("sha256")) is not str
            or type(item.get("bytes")) is not int
        ):
            _fail("Alpha-v30 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v30 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v30_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        record = result.get(path)
        if record is None:
            _fail(f"missing Alpha-v30 actual-proof control document {path!r}")
        try:
            payload = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v30 actual-proof source {path!r}: {error}")
        if record["sha256"] != sha256(payload).hexdigest():
            _fail(f"changed Alpha-v30 actual-proof control document {path!r}")
        if record["bytes"] != len(payload):
            _fail(f"changed Alpha-v30 actual-proof byte count {path!r}")

    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v30 lost its immutable sealed Alpha-v29 parent document")
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
        (source, "alpha_v30_frontier_dependency_curried_body", "dependency_curried_body", "document"),
        (test, "alpha_v30_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
        (rfc, "alpha_v30_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
        (
            builder.CLOSURE_ARTIFACT,
            "alpha_v30_gaussian_factorization_self_contained_constructive_proof_bundle",
            "independently_kernel_checked_dependency_closed_proof",
            f"nodes[id={node_id}]",
        ),
        (
            builder.CLOSURE_RECEIPT,
            "alpha_v30_gaussian_factorization_original_kernel_receipt",
            "original_kernel_independent_dependency_closure_verification",
            "document",
        ),
        (parent, "sealed_alpha_v29_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
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
    enrollment = alpha_v30_enrollment()
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
        "alpha_v30_frontier_enrollment", "evidence_links",
    }
    if set(row) != expected_keys:
        _fail(f"frontier theorem {name!r} changed its exact immutable field set")
    for key, value in expected.items():
        actual = row.get(key)
        if not _exact_json(actual, value):
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
    if not _exact_json(row.get("body_receipt"), body_receipt):
        _fail(f"frontier theorem {name!r} changed its independent original-kernel body receipt")
    artifact_digest = documents[builder.CLOSURE_ARTIFACT]["sha256"]
    transition = {
        "body_receipt_sha256": builder._digest(builder._compact(body_receipt)),
        "bundle_campaign": "gaussian_factorization", "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest, "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if not _exact_json(row.get("alpha_v30_frontier_enrollment"), transition):
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    closure = {
        "body_proof_depth": depth, "body_proof_nodes": nodes,
        "bundle_campaign": "gaussian_factorization",
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
    if not _exact_json(row.get("empty_context_closure"), closure):
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
    if not _exact_json(links, expected_links):
        _fail(f"frontier theorem {name!r} changed exact evidence-link authority or order")


INDEPENDENT_EXACT_ENDPOINTS = {
    "gaussian_unique_prime_factorization":
        "forall z. ZPairValid(z) -> ~(z=0) -> exists u b c l. GPrimeFactorization(z,u,b,c,l) /\\ (forall v d e m. GPrimeFactorization(z,v,d,e,m) -> (l=m /\\ exists U V. GMatchedFactors(b,c,d,e,U,V,l)))",
    "gaussian_prime_factorization_exists":
        "forall z. ZPairValid(z) -> ~(z=0) -> exists u b c l. GPrimeFactorization(z,u,b,c,l)",
    "gaussian_unit_prime_factorization_length_zero":
        "forall z u b c l. GPrimeFactorization(z,u,b,c,l) -> GUnit(z) -> l=0",
    "gaussian_zero_has_no_prime_factorization":
        "forall u b c l. ~GPrimeFactorization(0,u,b,c,l)",
    "gaussian_prime_factorizations_unique":
        "forall z u b c l v d e m. GPrimeFactorization(z,u,b,c,l) -> GPrimeFactorization(z,v,d,e,m) -> (l=m /\\ exists U V. GMatchedFactors(b,c,d,e,U,V,l))",
}


def _endpoint_formula(source: str):
    parser = _LocalDefinedParser(source, ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
    formula = parser.parse()
    if parser.free:
        _fail("an independent public endpoint contains an undeclared parameter")
    return formula


def _verify_unconditional_endpoints(specs: dict[str, Any]) -> None:
    """Compare actual formulas with independently stated public contracts.

    Definitions expand to the original arithmetic AST, so this does not use
    a theorem summary, the catalogue's digest, or an atlas status as evidence.
    The separate literal root digests also pin the exact source statements.
    """
    for name, statement in INDEPENDENT_EXACT_ENDPOINTS.items():
        row = specs.get(name)
        if row is None or _closed_formula(row.statement) != _endpoint_formula(statement):
            _fail(f"Alpha-v30 changed the exact unconditional endpoint {name!r}")


def _verify_truthful_boundaries(names: set[str]) -> None:
    missing = set(FRONTIER_ROOT_NAMES).difference(names)
    if missing:
        _fail(f"Alpha-v30 omitted a genuine constructive boundary root: {sorted(missing)!r}")
    invented = FORBIDDEN_UNPROVED_CLAIMS.intersection(names)
    if invented:
        _fail(f"Alpha-v30 falsely admitted an unproved ambitious boundary: {sorted(invented)!r}")
    for name, expected in INDEPENDENT_GAUSSIAN_FACTORIZATION_STATEMENT_SHA256.items():
        source = v30.ALPHA_EDITION.by_name[name].spec
        if sha256(source.statement.encode()).hexdigest() != expected:
            _fail(f"Alpha-v30 changed independently pinned gaussian-factorization statement {name!r}")
    _verify_unconditional_endpoints({name: entry.spec for name, entry in v30.ALPHA_EDITION.by_name.items()})


def _verify_independent_lean_evidence(
    promotion: dict[str, Any], proof_record: dict[str, Any]
) -> None:
    if (
        promotion.get("independent_lean_bundle_verified") is not True
        or proof_record.get("independent_lean_bundle_verified") is not True
    ):
        _fail("Alpha-v30 omitted independently compiled Lean proof-bundle verification")


def _verify_rows(
    rows: list[dict[str, Any]], parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]], checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != v30.EXPECTED_ALPHA_V30_COUNT
    ):
        _fail("Alpha-v30 changed its exact 3,042-row parent or additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v30 lacks its independently checked gaussian-factorization proof bundle")
    bundle, receipt, positions = checked
    if type(positions) is not dict:
        _fail("Alpha-v30 lacks exact independently checked proof-node positions")
    for index, old in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(old) is not dict:
            _fail(f"Alpha-v30 historical theorem row {index} is malformed")
        name = str(old.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v30 changed immutable theorem order at index {index}")
        if not _exact_json(row, old):
            _fail(f"Alpha-v30 modified immutable Alpha-v29 parent row {name!r}")
    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, v30.EXPECTED_ALPHA_V30_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v30 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row, index=index, bundle=bundle, receipt=receipt,
            node_id=positions[name], documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v30.FRONTIER_NEW_NAMES:
        _fail("Alpha-v30 changed its exact ordered additive theorem frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V30_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v30 changed its sealed additive theorem-name digest")
    if (
        campaigns != Counter(EXPECTED_CAMPAIGNS)
        or campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
    ):
        _fail("Alpha-v30 changed its exact constructive theorem-family counts")
    expected_evidence = Counter(
        stable_closed=builder.EXPECTED_STABLE_COUNT,
        alpha_closed=v30.EXPECTED_ALPHA_V30_COUNT - builder.EXPECTED_STABLE_COUNT,
    )
    if Counter(row.get("evidence_status") for row in rows) != expected_evidence:
        _fail("Alpha-v30 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v30 retained an unchecked theorem in its completely checked edition")
    available: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= available:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in available:
            _fail(f"Alpha-v30 duplicated the checked theorem {name!r}")
        available.add(name)
        edges += len(dependencies)
    if (
        len(available) != v30.EXPECTED_ALPHA_V30_COUNT
        or edges != v30.EXPECTED_ALPHA_V30_EDGE_COUNT
    ):
        _fail("Alpha-v30 changed its complete original-kernel-checked dependency DAG")
    _verify_truthful_boundaries(set(frontier))


def _verify_topology(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    topology = metrics.get("dependency_graph")
    if type(topology) is not dict:
        _fail("Alpha-v30 lost its complete checked dependency graph")
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    kept = [{"dependency": dep, "theorem": theorem} for dep, theorem in kept_edges]
    redundant = [{"dependency": dep, "theorem": theorem} for dep, theorem in redundant_edges]
    counts = Counter(depths.values())
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_origins = Counter(origins[name] for _dependency, name in redundant_edges)
    parent = _load(builder.PARENT_ALPHA_METRICS)["dependency_graph"]
    expected = {
        "declared_edge_count": v30.EXPECTED_ALPHA_V30_EDGE_COUNT,
        "layer_count": v30.EXPECTED_ALPHA_V30_LAYER_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values()), default=0),
        "theorems_by_depth": {str(depth): count for depth, count in sorted(counts.items())},
        "transitive_reduction_edge_count": len(kept),
        "transitive_reduction_edge_sha256": builder._digest(builder._compact(kept)),
        "reachability_redundant_direct_dependencies": redundant,
        "reachability_redundant_direct_dependency_count": len(redundant),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(sorted(redundant_origins.items())),
        "reachability_redundant_direct_dependency_sha256": builder._digest(builder._compact(redundant)),
        "reachability_reduction_scope": parent["reachability_reduction_scope"],
        "transitive_reduction_preserves_reachability": True,
    }
    if (
        not _exact_json(topology, expected)
        or max(depths.values(), default=-1) + 1 != v30.EXPECTED_ALPHA_V30_LAYER_COUNT
        or len(kept) + len(redundant) != v30.EXPECTED_ALPHA_V30_EDGE_COUNT
    ):
        _fail("Alpha-v30 changed independently derived checked-DAG topology")


def _verify_principal_roots() -> None:
    """Check one actual closed root at a time without retaining every materialized certificate."""
    for name in FRONTIER_ROOT_NAMES:
        print(f"checking Alpha-v30 principal root: {name}", flush=True)
        result = None
        try:
            result = v30.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")
            print(f"accepted Alpha-v30 principal root: {name}", flush=True)
        finally:
            result = None
            # Keep the single authenticated bundle, not every materialized
            # principal certificate. No kernel/resource policy is changed.
            v30.replay.cache_clear()
            gc.collect()


def verify(*, verify_roots: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v30 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v30 artifact schemas changed")
    rows = catalog.get("theorems")
    evidence = {
        "alpha_closed": v30.EXPECTED_ALPHA_V30_COUNT - builder.EXPECTED_STABLE_COUNT,
        "stable_closed": builder.EXPECTED_STABLE_COUNT,
    }
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != v30.EXPECTED_ALPHA_V30_COUNT
        or metrics.get("theorem_count") != v30.EXPECTED_ALPHA_V30_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != v30.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != v30.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or catalog.get("edge_count") != v30.EXPECTED_ALPHA_V30_EDGE_COUNT
        or catalog.get("layer_count") != v30.EXPECTED_ALPHA_V30_LAYER_COUNT
        or catalog.get("evidence_counts") != evidence
    ):
        _fail("Alpha-v30 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v30.ALPHA_V30_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v30.ALPHA_V30_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256") != base._ordered_root(v30.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v30 changed exact additive enrollment, theorem, or membership roots")
    if not _exact_json(catalog.get("parent_alpha_v29"), builder._parent_binding()):
        _fail("Alpha-v30 lost exact sealed Alpha-v29 artifact provenance")

    documents = _documents(catalog, parent=parent)
    # Executes the unchanged independent HA kernel AND the compiled Lean verifier.
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        not _exact_json(catalog.get("alpha_v30_gaussian_factorization_promotion"), promotion)
        or not _exact_json(metrics.get("alpha_v30_gaussian_factorization_promotion"), promotion)
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V30_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != v30.EXPECTED_ALPHA_V30_COUNT
        or promotion.get("campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v30 changed its exact gaussian-factorization additive proof evidence")
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
        _fail("Alpha-v30 changed independently checked gaussian-factorization proof metrics")
    _verify_independent_lean_evidence(promotion, proof)
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v30 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed" or full.get("checked") != v30.EXPECTED_ALPHA_V30_COUNT
        or full.get("missing") != 0 or full.get("required") != v30.EXPECTED_ALPHA_V30_COUNT
    ):
        _fail("Alpha-v30 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    historical = _load(builder.PARENT_ALPHA_METRICS)["checked_closure_metrics"]
    expected_digests = historical["certificate_digest_kinds"][
        "self-contained-proof-bundle-sha256"
    ] + FRONTIER_V30_EXPECTED_COUNT
    if (
        accounting.get("metric_bearing_theorem_count") != v30.EXPECTED_ALPHA_V30_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        ) != expected_digests
    ):
        _fail("Alpha-v30 misstated its complete independently checked proof accounting")
    campaign = accounting.get("campaign_v30_bundle_accounting", {})
    if (
        campaign.get("campaign_count") != len(EXPECTED_CAMPAIGNS)
        or campaign.get("new_checked_theorem_count") != FRONTIER_V30_EXPECTED_COUNT
        or campaign.get("campaign_counts") != EXPECTED_CAMPAIGNS
        or campaign.get("proof_bundle") != proof
        or gates.get("complete_constructive_alpha_v30_gaussian_factorization")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v30 changed exact gaussian-factorization proof-accounting gates")
    _verify_topology(rows, metrics)

    catalog_digest = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_digest = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_digest = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_digest
        or metrics.get("dependency_graph_sha256") != graph_digest
        or metrics.get("edition_identity_sha256") != v30.ALPHA_V30_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v30.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v30 catalog, dependency graph, or metrics artifact changed")
    old_channels = _load(builder.PARENT_CHANNELS)
    actual = channels.get("channels")
    if (
        type(actual) is not dict or channels.get("default_channel") != "stable"
        or actual.get("stable") != old_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256") != builder._digest(builder._compact(actual))
        or channels.get("parent_channels_v29") != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v30 changed immutable Stable pointer or default release channel")
    alpha = actual.get("alpha")
    if (
        type(alpha) is not dict or alpha.get("artifact_sha256") != catalog_digest
        or alpha.get("theorem_count") != v30.EXPECTED_ALPHA_V30_COUNT
        or alpha.get("checked_use_count") != v30.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v30.ALPHA_V30_IDENTITY_SHA256
        or alpha.get("parent_alpha_v29_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v30_frontier_new_count") != FRONTIER_V30_EXPECTED_COUNT
        or alpha.get("frontier_v30_campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v30 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_digest), ("metrics", metrics_digest), ("dependency_graph", graph_digest)
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v30 changed exact {key} channel pointer digest")

    # Avoid loading unrelated historical Alpha proof artifacts.
    result = v30.replay("zero_add", edition="stable")
    if not check((), result.certificate, result.formula):
        _fail("unchanged kernel rejected the immutable historical Stable theorem")
    if verify_roots:
        # Exact catalogue and provenance checks are complete. Do not retain
        # both large parsed catalogues while traversing ordinary certificates.
        # This releases presentation data only; the proof graph and all
        # original-kernel judgments and resource limits remain unchanged.
        del result, rows, catalog, parent, metrics, channels, old_channels
        del actual, alpha, documents, accounting, historical, campaign, full, gates
        gc.collect()
        _verify_principal_roots()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-roots", action="store_true")
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v30 independently: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={v30.EXPECTED_ALPHA_V30_COUNT}, "
        f"checked-use={v30.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT}, "
        f"frontier-new={FRONTIER_V30_EXPECTED_COUNT}, "
        f"campaigns={len(EXPECTED_CAMPAIGNS)}, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
