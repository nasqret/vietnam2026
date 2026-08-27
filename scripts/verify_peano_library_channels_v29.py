#!/usr/bin/env python3
"""Independently verify the fully proof-closed additive Alpha-v29 release."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v29 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v29 as v29
from peano_lab.library.alpha_enrollment_v29 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V29_EXPECTED_COUNT,
    FRONTIER_V29_EXPECTED_NAMES_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v29_enrollment,
)
from constructive_formula_compactor import _LocalDefinedParser
from constructive_priority_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
from peano_lab.library.theorems import _closed_formula


EXPECTED_CAMPAIGNS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
FRONTIER_ROOT_NAMES = tuple(ROOT_STATEMENT_SHA256)
INDEPENDENT_PRIORITY_LAYER_STATEMENT_SHA256 = {
    "prime_valuation_support_exists": "d6e0d6a185004dcf15dae72c0bc893200f0b3d5688a8784c53497ef8fe60907b",
    "continued_fraction_convergent_index_is_valid": "7bf9f8067ced2ed2eb52386f08e7efa1a7cfe47aa05b36bfc9aa3048df5aeed7",
    "continued_fraction_initial_zero_over_one": "f3f23d230d72430e8d5af7462c5bf58a2d931e50d74083053c8d6374153ded00",
    "continued_fraction_has_exact_terminal_convergent": "4f2ff1801b78a9b8142e1e104bea9e49a5251d5c165f2982332e6a70fe966ea0",
    "continued_fraction_convergent_exists_unique_at_history_index": "a2350b3a79e730cf6c26001c3c5e8b515a6757a5d32cb64d83cd55853e6e6c5b",
    "continued_fraction_initial_convergent_is_first_quotient": "3c86b18e5e51da36f00546e6905a043475ce884f391fff5706099738e6fc3ade",
    "continued_fraction_adjacent_convergent_determinant": "5666bd5d85b19e815856e29a5c93bfa0c07e9e28b8e9aa651e08e9978dbded41",
    "continued_fraction_convergent_coprime": "dc7cd76880ad898f76cdcc22f0602e7ec51b08c4ac99e1e43afa1dd682fa859b",
    "continued_fraction_convergent_best_approximation_signed": "d1401bdb17320a1fc10ebfa605c42972b850cd596d1a6d114ad82b5be8f5492b",
    "continued_fraction_convergent_best_approximation": "f77356be459116bfcf711c13c7d70777afc2a7a5e93a91f28ee464d07c4bca2c",
    "totient_bounded": "69b251a8267787c85934ff7c8938bb84dc9a26ece3224c8c84ff61a90294cfcb",
    "totient_exists_unique": "949c4af14495d74cb45019f5e068fbb45580968e2abf1527f27b80146db77013",
    "totient_unit_count_modulus_transport": "f773949552a0f34466fcf6d695fdf06583d01c1add1627df2de3c967aa9cab87",
    "totient_prime_coprime_iff_nondivisor": "28dddd435dbbca016175a04306d00675492aaf81e7a19263d085fb01b8381f30",
    "totient_prime_power_value": "5a77436d23c80965981715a3196f5669122f4184a3201c19955d7fdfcdfb10f0",
    "totient_euler_factor_functional": "9e34f682291f3bdbe3c99335f23214c14fd3a291afe61926df6bf0bd8ef42150",
    "totient_euler_factor_prefix_drop_last": "40ba3047fc6390bb7a4f53a00ffa7d12a74215f671fb4d0aee5b4e4dfbffe7bb",
    "totient_euler_product_functional": "f47c7eb97e11c3971ab41e5c3fe090335cd36b1cfbc9264868d7b82d90678194",
    "totient_euler_product_iff": "1d37df29457d21f2f36c8fc9a652a0dfcde15bde5a730c8a3ae789fcf98eb176",
    "totient_euler_product_one": "5650edfce8b3712b3658545e921b60eeabc9f895078d4f2a756be5d19a698d45",
    "totient_euler_product_zero_excluded": "4f75707ef4318b5d242df321a53288e3f0d62bbd69acd9b487bfbe4d9a0484a4",
    "totient_euler_product_formula": "30f159a663418d13fe52b39acca9de20a67d44219cc28eb965c36f352ddcf2a2",
    "squarefree_one": "7836966aff0c8d2a23ca95bc525812398670799b96efeb0cb8db831bba43393e",
    "squarefree_decomposition_exists_unique": "efce5f0c441fd9d953dceab7c4a0869a11c41ad65e4eee3d1e73e3c6b92aacf3",
    "prime_exponent_prefix_gcd_functional": "2bbca6f988120d68d2789dd845c53c4df532890e8c301d90a8f2ba8c5d8b6182",
    "perfect_power_profile_data_degree_classification": "4c2d57506081b169c3db70a52b5996fcc7685864831fe45db892f6607586ecf4",
    "perfect_power_profile_data_root_lookup": "67dba36528e372272b28d94b01e479f8db3093917cae2768bda48ebe3ca57444",
    "perfect_power_profile_positive": "c1a1d56c0398396e62e907c86c128bcae4918d8e130dedb880fba3e3aa941819",
    "perfect_power_profile_unit_code": "60b383063bf7111a2d64778f10054bd8279c6781030bbf8934f90dea3f5133eb",
    "perfect_power_profile_nonunit_decode": "a6aab6715f2b60fed8d17529c812776693709806192da75df76904dc82de4fcf",
    "positive_squarefree_kernel_and_power_profile": "d90dd7d83bf94f698c6fde0134034eed5e89b5bae73c2caf58b6cdc788313949",
    "odd_prime_lifting_the_exponent": "36da85a059e7c726b9b4708cd6d34696d387b13f962fe6148654df3f0c469f6b",
    "odd_prime_lifting_the_exponent_value": "703616c3381acc0809aac4629c10006424894b62fceb60c40899b783329eac22"
}
FORBIDDEN_UNPROVED_CLAIMS = frozenset(
    {
        "gaussian_unique_factorization_exists",
        "eisenstein_unique_factorization_exists",
        "gaussian_prime_classification_complete",
        "eisenstein_prime_classification_complete",
        "gaussian_gcd_algorithm_complete",
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
        _fail("Alpha-v29 lost its immutable Alpha-v28 evidence-document inventory")
    inherited: dict[str, dict[str, Any]] = {}
    for record in inventory:
        if type(record) is not dict or type(record.get("path")) is not str:
            _fail("Alpha-v29 inherited a malformed Alpha-v28 evidence-document binding")
        path = record["path"]
        if path in inherited:
            _fail(f"duplicate immutable Alpha-v28 evidence-document binding {path!r}")
        inherited[path] = record
        if not _exact_json(documents.get(path), record):
            _fail(f"Alpha-v29 changed immutable Alpha-v28 evidence-document binding {path!r}")

    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = inherited.get(path)
    if (
        record is None
        or record.get("path") != path
        or record.get("sha256") != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or type(record.get("bytes")) is not int
        or record["bytes"] != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        _fail("Alpha-v29 changed its immutable quadratic-reciprocity corpus catalog binding")
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
        _fail("Alpha-v29 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if (
            type(item) is not dict
            or type(item.get("path")) is not str
            or type(item.get("sha256")) is not str
            or type(item.get("bytes")) is not int
        ):
            _fail("Alpha-v29 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v29 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v29_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        record = result.get(path)
        if record is None:
            _fail(f"missing Alpha-v29 actual-proof control document {path!r}")
        try:
            payload = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v29 actual-proof source {path!r}: {error}")
        if record["sha256"] != sha256(payload).hexdigest():
            _fail(f"changed Alpha-v29 actual-proof control document {path!r}")
        if record["bytes"] != len(payload):
            _fail(f"changed Alpha-v29 actual-proof byte count {path!r}")

    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v29 lost its immutable sealed Alpha-v28 parent document")
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
        (source, "alpha_v29_frontier_dependency_curried_body", "dependency_curried_body", "document"),
        (test, "alpha_v29_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
        (rfc, "alpha_v29_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
        (
            builder.CLOSURE_ARTIFACT,
            "alpha_v29_priority_layer_self_contained_constructive_proof_bundle",
            "independently_kernel_checked_dependency_closed_proof",
            f"nodes[id={node_id}]",
        ),
        (
            builder.CLOSURE_RECEIPT,
            "alpha_v29_priority_layer_original_kernel_receipt",
            "original_kernel_independent_dependency_closure_verification",
            "document",
        ),
        (parent, "sealed_alpha_v28_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
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
    enrollment = alpha_v29_enrollment()
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
        "alpha_v29_frontier_enrollment", "evidence_links",
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
        "bundle_campaign": "priority_layer", "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest, "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if not _exact_json(row.get("alpha_v29_frontier_enrollment"), transition):
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    closure = {
        "body_proof_depth": depth, "body_proof_nodes": nodes,
        "bundle_campaign": "priority_layer",
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
    "continued_fraction_convergent_best_approximation":
        "forall a b s i u v. (ContinuedFraction(a,b,s) /\\ Convergent(s,i,u,v)) -> BestApproximationSecondKind(a,b,u,v)",
    "continued_fraction_convergent_best_approximation_signed":
        "forall a b s i u v. ContinuedFraction(a,b,s) -> Convergent(s,i,u,v) -> SignedBestApproximationSecondKind(a,b,u,v)",
    "totient_euler_product_formula":
        "forall n. ~(n = 0) -> exists f g l t. PrimeFactorList(n,f,g,l) /\\ (Phi(n,t) /\\ EulerProduct(n,t))",
    "positive_squarefree_kernel_and_power_profile":
        "forall n. ~(n = 0) -> exists r s w. Squarefree(r) /\\ (n = r * (s*s) /\\ (PowerProfile(n,w) /\\ forall u v. Squarefree(u) -> n = u * (v*v) -> u = r /\\ v = s))",
    "odd_prime_lifting_the_exponent":
        "forall p x y d n a b. Prime(p) -> Lt(2,p) -> Lt(y,x) -> ~(y=0) -> ~(n=0) -> x=y+d -> Dvd(p,d) -> ~Dvd(p,x*y) -> PowerValuation(p,d,a) -> PowerValuation(p,n,b) -> exists X Y D. LiftedPowerDifference(p,x,y,n,a+b,X,Y,D)",
    "odd_prime_lifting_the_exponent_value":
        "forall p x y d n a b X Y D. Prime(p) -> Lt(2,p) -> Lt(y,x) -> ~(y=0) -> ~(n=0) -> x=y+d -> Dvd(p,d) -> ~Dvd(p,x*y) -> PowerValuation(p,d,a) -> PowerValuation(p,n,b) -> Pow(x,n,X) -> Pow(y,n,Y) -> X=Y+D -> PowerValuation(p,D,a+b)",
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
            _fail(f"Alpha-v29 changed the exact unconditional endpoint {name!r}")


def _verify_truthful_boundaries(names: set[str]) -> None:
    missing = set(FRONTIER_ROOT_NAMES).difference(names)
    if missing:
        _fail(f"Alpha-v29 omitted a genuine constructive boundary root: {sorted(missing)!r}")
    invented = FORBIDDEN_UNPROVED_CLAIMS.intersection(names)
    if invented:
        _fail(f"Alpha-v29 falsely admitted an unproved ambitious boundary: {sorted(invented)!r}")
    for name, expected in INDEPENDENT_PRIORITY_LAYER_STATEMENT_SHA256.items():
        source = v29.ALPHA_EDITION.by_name[name].spec
        if sha256(source.statement.encode()).hexdigest() != expected:
            _fail(f"Alpha-v29 changed independently pinned priority-layer statement {name!r}")
    _verify_unconditional_endpoints({name: entry.spec for name, entry in v29.ALPHA_EDITION.by_name.items()})


def _verify_independent_lean_evidence(
    promotion: dict[str, Any], proof_record: dict[str, Any]
) -> None:
    if (
        promotion.get("independent_lean_bundle_verified") is not True
        or proof_record.get("independent_lean_bundle_verified") is not True
    ):
        _fail("Alpha-v29 omitted independently compiled Lean proof-bundle verification")


def _verify_rows(
    rows: list[dict[str, Any]], parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]], checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != v29.EXPECTED_ALPHA_V29_COUNT
    ):
        _fail("Alpha-v29 changed its exact 2,764-row parent or additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v29 lacks its independently checked priority-layer proof bundle")
    bundle, receipt, positions = checked
    if type(positions) is not dict:
        _fail("Alpha-v29 lacks exact independently checked proof-node positions")
    for index, old in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(old) is not dict:
            _fail(f"Alpha-v29 historical theorem row {index} is malformed")
        name = str(old.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v29 changed immutable theorem order at index {index}")
        if not _exact_json(row, old):
            _fail(f"Alpha-v29 modified immutable Alpha-v28 parent row {name!r}")
    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, v29.EXPECTED_ALPHA_V29_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v29 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row, index=index, bundle=bundle, receipt=receipt,
            node_id=positions[name], documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v29.FRONTIER_NEW_NAMES:
        _fail("Alpha-v29 changed its exact ordered additive theorem frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V29_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v29 changed its sealed additive theorem-name digest")
    if (
        campaigns != Counter(EXPECTED_CAMPAIGNS)
        or campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
    ):
        _fail("Alpha-v29 changed its exact constructive theorem-family counts")
    expected_evidence = Counter(
        stable_closed=builder.EXPECTED_STABLE_COUNT,
        alpha_closed=v29.EXPECTED_ALPHA_V29_COUNT - builder.EXPECTED_STABLE_COUNT,
    )
    if Counter(row.get("evidence_status") for row in rows) != expected_evidence:
        _fail("Alpha-v29 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v29 retained an unchecked theorem in its completely checked edition")
    available: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= available:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in available:
            _fail(f"Alpha-v29 duplicated the checked theorem {name!r}")
        available.add(name)
        edges += len(dependencies)
    if (
        len(available) != v29.EXPECTED_ALPHA_V29_COUNT
        or edges != v29.EXPECTED_ALPHA_V29_EDGE_COUNT
    ):
        _fail("Alpha-v29 changed its complete original-kernel-checked dependency DAG")
    _verify_truthful_boundaries(set(frontier))


def _verify_topology(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    topology = metrics.get("dependency_graph")
    if type(topology) is not dict:
        _fail("Alpha-v29 lost its complete checked dependency graph")
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    kept = [{"dependency": dep, "theorem": theorem} for dep, theorem in kept_edges]
    redundant = [{"dependency": dep, "theorem": theorem} for dep, theorem in redundant_edges]
    counts = Counter(depths.values())
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_origins = Counter(origins[name] for _dependency, name in redundant_edges)
    parent = _load(builder.PARENT_ALPHA_METRICS)["dependency_graph"]
    expected = {
        "declared_edge_count": v29.EXPECTED_ALPHA_V29_EDGE_COUNT,
        "layer_count": v29.EXPECTED_ALPHA_V29_LAYER_COUNT,
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
        or max(depths.values(), default=-1) + 1 != v29.EXPECTED_ALPHA_V29_LAYER_COUNT
        or len(kept) + len(redundant) != v29.EXPECTED_ALPHA_V29_EDGE_COUNT
    ):
        _fail("Alpha-v29 changed independently derived checked-DAG topology")


def _verify_principal_roots() -> None:
    """Check one actual closed root at a time without retaining every materialized certificate."""
    for name in FRONTIER_ROOT_NAMES:
        print(f"checking Alpha-v29 principal root: {name}", flush=True)
        result = None
        try:
            result = v29.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")
            print(f"accepted Alpha-v29 principal root: {name}", flush=True)
        finally:
            result = None
            # Keep the single authenticated bundle, not every materialized
            # principal certificate. No kernel/resource policy is changed.
            v29.replay.cache_clear()
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
        _fail(f"cannot read sealed Alpha-v29 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v29 artifact schemas changed")
    rows = catalog.get("theorems")
    evidence = {
        "alpha_closed": v29.EXPECTED_ALPHA_V29_COUNT - builder.EXPECTED_STABLE_COUNT,
        "stable_closed": builder.EXPECTED_STABLE_COUNT,
    }
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != v29.EXPECTED_ALPHA_V29_COUNT
        or metrics.get("theorem_count") != v29.EXPECTED_ALPHA_V29_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != v29.EXPECTED_ALPHA_V29_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != v29.EXPECTED_ALPHA_V29_CHECKED_USE_COUNT
        or catalog.get("edge_count") != v29.EXPECTED_ALPHA_V29_EDGE_COUNT
        or catalog.get("layer_count") != v29.EXPECTED_ALPHA_V29_LAYER_COUNT
        or catalog.get("evidence_counts") != evidence
    ):
        _fail("Alpha-v29 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v29.ALPHA_V29_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v29.ALPHA_V29_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256") != base._ordered_root(v29.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v29 changed exact additive enrollment, theorem, or membership roots")
    if not _exact_json(catalog.get("parent_alpha_v28"), builder._parent_binding()):
        _fail("Alpha-v29 lost exact sealed Alpha-v28 artifact provenance")

    documents = _documents(catalog, parent=parent)
    # Executes the unchanged independent HA kernel AND the compiled Lean verifier.
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        not _exact_json(catalog.get("alpha_v29_priority_layer_promotion"), promotion)
        or not _exact_json(metrics.get("alpha_v29_priority_layer_promotion"), promotion)
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V29_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != v29.EXPECTED_ALPHA_V29_COUNT
        or promotion.get("campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v29 changed its exact priority-layer additive proof evidence")
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
        _fail("Alpha-v29 changed independently checked priority-layer proof metrics")
    _verify_independent_lean_evidence(promotion, proof)
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v29 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed" or full.get("checked") != v29.EXPECTED_ALPHA_V29_COUNT
        or full.get("missing") != 0 or full.get("required") != v29.EXPECTED_ALPHA_V29_COUNT
    ):
        _fail("Alpha-v29 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    historical = _load(builder.PARENT_ALPHA_METRICS)["checked_closure_metrics"]
    expected_digests = historical["certificate_digest_kinds"][
        "self-contained-proof-bundle-sha256"
    ] + FRONTIER_V29_EXPECTED_COUNT
    if (
        accounting.get("metric_bearing_theorem_count") != v29.EXPECTED_ALPHA_V29_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        ) != expected_digests
    ):
        _fail("Alpha-v29 misstated its complete independently checked proof accounting")
    campaign = accounting.get("campaign_v29_bundle_accounting", {})
    if (
        campaign.get("campaign_count") != len(EXPECTED_CAMPAIGNS)
        or campaign.get("new_checked_theorem_count") != FRONTIER_V29_EXPECTED_COUNT
        or campaign.get("campaign_counts") != EXPECTED_CAMPAIGNS
        or campaign.get("proof_bundle") != proof
        or gates.get("complete_constructive_alpha_v29_priority_layer")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v29 changed exact priority-layer proof-accounting gates")
    _verify_topology(rows, metrics)

    catalog_digest = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_digest = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_digest = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_digest
        or metrics.get("dependency_graph_sha256") != graph_digest
        or metrics.get("edition_identity_sha256") != v29.ALPHA_V29_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v29.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v29 catalog, dependency graph, or metrics artifact changed")
    old_channels = _load(builder.PARENT_CHANNELS)
    actual = channels.get("channels")
    if (
        type(actual) is not dict or channels.get("default_channel") != "stable"
        or actual.get("stable") != old_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256") != builder._digest(builder._compact(actual))
        or channels.get("parent_channels_v28") != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v29 changed immutable Stable pointer or default release channel")
    alpha = actual.get("alpha")
    if (
        type(alpha) is not dict or alpha.get("artifact_sha256") != catalog_digest
        or alpha.get("theorem_count") != v29.EXPECTED_ALPHA_V29_COUNT
        or alpha.get("checked_use_count") != v29.EXPECTED_ALPHA_V29_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v29.ALPHA_V29_IDENTITY_SHA256
        or alpha.get("parent_alpha_v28_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v29_frontier_new_count") != FRONTIER_V29_EXPECTED_COUNT
        or alpha.get("frontier_v29_campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v29 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_digest), ("metrics", metrics_digest), ("dependency_graph", graph_digest)
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v29 changed exact {key} channel pointer digest")

    # Avoid loading unrelated historical Alpha proof artifacts.
    result = v29.replay("zero_add", edition="stable")
    if not check((), result.certificate, result.formula):
        _fail("unchanged kernel rejected the immutable historical Stable theorem")
    if verify_roots:
        del result
        _verify_principal_roots()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-roots", action="store_true")
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v29 independently: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={v29.EXPECTED_ALPHA_V29_COUNT}, "
        f"checked-use={v29.EXPECTED_ALPHA_V29_CHECKED_USE_COUNT}, "
        f"frontier-new={FRONTIER_V29_EXPECTED_COUNT}, "
        f"campaigns={len(EXPECTED_CAMPAIGNS)}, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

