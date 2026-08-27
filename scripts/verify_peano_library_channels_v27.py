#!/usr/bin/env python3
"""Independently verify the fully proof-closed additive Alpha-v27 release."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v27 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v27 as v27
from peano_lab.library.alpha_enrollment_v27 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V27_EXPECTED_COUNT,
    FRONTIER_V27_EXPECTED_NAMES_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v27_enrollment,
)
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.generalized_crt_full_candidate import (
    _expand as _crt_expand, _normalized_terms as _crt_normalized,
    _pairwise_terms as _crt_pairwise,
)
from peano_lab.library.hensel_simple_root_criterion_candidate import (
    _all_lifts as _hensel_all_lifts, _nonsingular as _hensel_nonsingular,
)
from peano_lab.library.cornacchia_candidate import _root_completion as _cornacchia_completion
from peano_lab.library.cauchy_davenport_candidate import _bound as _cauchy_bound
from peano_lab.library.finite_modular_set_candidate import (
    _count as _modular_count, _sumset as _modular_sumset,
)
from peano_lab.library.theorems import _closed_formula


EXPECTED_CAMPAIGNS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
FRONTIER_ROOT_NAMES = tuple(ROOT_STATEMENT_SHA256)
INDEPENDENT_SECOND_WAVE_STATEMENT_SHA256 = {
    "signed_recursive_determinant_exists_unique": "bf78d0b39617ddaabf5e7b617a4e5474ee57d308c14d296de7a54e93d42d0dbc",
    "signed_recursive_determinant_cofactor_equation": "584c7cd696d0844f5748f21a45f4a408b3a321ad64097c2a5bebfc623194970d",
    "signed_recursive_determinant_empty_equation": "cd74d5fd1dda41357c2a9cbbbec952fe1d8bcd2c3d9c7b21f85b4125daba7cb0",
    "rectangular_matrix_rank_exists_unique": "677f945b5341792d5b2281cc8948922456c461c1aeeec880c452199df7d178f1",
    "rectangular_matrix_rank_successor_minors_zero": "3f79bf62134e5de89064d0a4181a1e00ff647b3b309498c1b127c30da468de9d",
    "integer_column_span_contains_zero": "1df52e34af59b05182acebe099349fc54eb8b6ca59ac55dccdc096bc8aaf0d01",
    "integer_column_span_add_exists": "4c3ef723161578a73747c914a683d2b50ad3a80d087ee222b56a14ef4a1e296a",
    "integer_column_span_negate_exists": "c6723d098ae92d7069c1ae12d5207fb1c133bd40ec63ad6bd596df954791736a",
    "integer_polynomial_prime_simple_root_lifts_all_positive_powers": "158b28822061f364d34a4badf84986d5f02301b58c555b1e67ec758c786709e8",
    "crt_pairwise_compatible_prefix_normalized_exists_unique": "f333d811cf04309d630382e2c049885d0de6e2cf4f26a218faf0e6039b002587",
    "crt_pairwise_compatible_prefix_canonical_exists_unique": "ac5e941743de53a1954904f99231acf74a38f59c15ed7887d3896cf3b8fe65b8",
    "crt_pairwise_compatible_prefix_solvable_iff": "bbaf5b097637ebfb6178b95ff37f6fed77776532c4058ece4f2f79a94e65ba64",
    "multinomial_exists": "ce01b5413f8c187fd18fafea53aa19619510ca975c179b88a5c732d3bf71299c",
    "multinomial_kummer_carry_valuation": "f69d92599b4eaa9e893e3a4c0e8ab998234bbce6223fbbde949433c1ee7c8266",
    "prime_count_chebyshev_bounds": "38a80957c2e9e9545cf57e1a036768d506a64edd891be2d0125ffd499fab7428",
    "prime_count_exists_unique": "c4255dbed70cfaf30b466653ecbb13f24ab98d362095fd6331fcce9263c85708",
    "cornacchia_prime_two_squares_complete": "becd01e6f073d37e512d385ffbc5e4e929ea3113f9d900fcc189718fc83eefc7",
    "cornacchia_from_any_bounded_negative_one_root": "b473b37393a7202423d12f928eacdeda26ce6c851793864e2431eab1fa713195",
    "prime_cauchy_davenport_sumset_exists": "7f2babcbea49f9ebe8e3a5d2339d0009d16d61afbe33341fcf7b951ede80b6e1",
    "prime_cauchy_davenport_sumset_bound": "634e3a5403ad025cef1e894dc2b9c3401691bb84bb57c2b70cb3aba185b806fb",
    "finite_modular_sumset_exists": "46420a141069c2696880ec30397f7cedaa2c8b7866ddc2791ec2aff0c799a9d9",
    "signed_recursive_determinant_integer_invariant": "a5587046845e712ff96b73c8fc4f54b9ecfeac5cfa224a1d537c6ce20f728dd6",
    "rectangular_matrix_rank_integer_invariant": "d6c74c06c5a55da7ec89d026a4658e49604b6f6b11521d1b453c8bfa16168151",
    "absolute_recursive_determinant_exists_unique": "1a01953c2267c95c0c92fb0b853dade02a33fbf1dbee71af3dfa3a97378bcad8",
    "positive_determinant_matrix_data_exists_unique": "2d8c3aec5c5751dc8325a28477c9b6c7b7ddd8d8cd20bcc719d7af518bcc2676",
    "positive_determinant_matrix_data_full_rank": "2d861924f0f0b78f626e57e1521a2fa6145abe7bf1eadae069ecd2a906b20b48",
    "square_matrix_full_rank_from_nonzero_determinant": "4c54da0a9e91e210d5a9f1d93711e28706532e435a889f22a8beb470abe4bb1a",
}
FORBIDDEN_UNPROVED_CLAIMS = frozenset(
    {
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
        _fail("Alpha-v27 lost its immutable Alpha-v26 evidence-document inventory")
    inherited: dict[str, dict[str, Any]] = {}
    for record in inventory:
        if type(record) is not dict or type(record.get("path")) is not str:
            _fail("Alpha-v27 inherited a malformed Alpha-v26 evidence-document binding")
        path = record["path"]
        if path in inherited:
            _fail(f"duplicate immutable Alpha-v26 evidence-document binding {path!r}")
        inherited[path] = record
        if documents.get(path) != record:
            _fail(f"Alpha-v27 changed immutable Alpha-v26 evidence-document binding {path!r}")

    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = inherited.get(path)
    if (
        record is None
        or record.get("path") != path
        or record.get("sha256") != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or type(record.get("bytes")) is not int
        or record["bytes"] != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        _fail("Alpha-v27 changed its immutable quadratic-reciprocity corpus catalog binding")
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
        _fail("Alpha-v27 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if (
            type(item) is not dict
            or type(item.get("path")) is not str
            or type(item.get("sha256")) is not str
            or type(item.get("bytes")) is not int
        ):
            _fail("Alpha-v27 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v27 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v27_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        record = result.get(path)
        if record is None:
            _fail(f"missing Alpha-v27 actual-proof control document {path!r}")
        try:
            payload = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v27 actual-proof source {path!r}: {error}")
        if record["sha256"] != sha256(payload).hexdigest():
            _fail(f"changed Alpha-v27 actual-proof control document {path!r}")
        if record["bytes"] != len(payload):
            _fail(f"changed Alpha-v27 actual-proof byte count {path!r}")

    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v27 lost its immutable sealed Alpha-v26 parent document")
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
        (source, "alpha_v27_frontier_dependency_curried_body", "dependency_curried_body", "document"),
        (test, "alpha_v27_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
        (rfc, "alpha_v27_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
        (
            builder.CLOSURE_ARTIFACT,
            "alpha_v27_second_wave_self_contained_constructive_proof_bundle",
            "independently_kernel_checked_dependency_closed_proof",
            f"nodes[id={node_id}]",
        ),
        (
            builder.CLOSURE_RECEIPT,
            "alpha_v27_second_wave_original_kernel_receipt",
            "original_kernel_independent_dependency_closure_verification",
            "document",
        ),
        (parent, "sealed_alpha_v26_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
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
    enrollment = alpha_v27_enrollment()
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
        "alpha_v27_frontier_enrollment", "evidence_links",
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
        "bundle_campaign": "second_wave", "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest, "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if not _exact_json(row.get("alpha_v27_frontier_enrollment"), transition):
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    closure = {
        "body_proof_depth": depth, "body_proof_nodes": nodes,
        "bundle_campaign": "second_wave",
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


def _verify_unconditional_endpoints(specs: dict[str, Any]) -> None:
    """Audit exact no-supplied-witness endpoints, not merely display labels.

    Root digest pins below are independent of the enrollment table. These AST
    comparisons additionally expose the mathematical contract: unrestricted CRT
    compatibility, derivative nonvanishing rather than a supplied inverse, and
    existence of the complete Cornacchia trace rather than a successful trace
    hypothesis. The conservative relation constructors perform no inference.
    """
    pairwise = _crt_expand(
        _crt_pairwise, "r", "s", "b", "c", "l", tag="independent_v27_pairs"
    )
    chosen = _crt_normalized(
        "r", "s", "b", "c", "l", "x", "M", tag="independent_v27_chosen"
    )
    compared = _crt_normalized(
        "r", "s", "b", "c", "l", "y", "M", tag="independent_v27_compared"
    )
    nonsingular = _hensel_nonsingular(
        "pb", "pc", "nb", "nc", "a", "l", "p", "p",
        tag="independent_v27_nonsingular",
    )
    lifts = _hensel_all_lifts(
        "pb", "pc", "nb", "nc", "a", "l", "p", "k",
        tag="independent_v27_lifts",
    )
    exact = {
        "crt_pairwise_compatible_prefix_normalized_exists_unique": (
            f"forall r s b c l. ({pairwise}) -> exists x M. "
            f"(({chosen}) /\\ forall y. ({compared}) -> y = x)"
        ),
        "integer_polynomial_prime_simple_root_lifts_all_positive_powers": (
            "forall pb pc nb nc a l p k. "
            f"({prime('p', tag='independent_v27_hensel_prime')}) -> "
            f"~(k = 0) -> ({nonsingular}) -> ({lifts})"
        ),
        "cornacchia_prime_two_squares_complete": (
            f"forall p. ({prime('p', tag='independent_v27_cornacchia_prime')}) -> "
            "(exists k. p = 4 * k + 1) -> exists z. "
            f"({_cornacchia_completion('p', 'z', tag='independent_v27_trace')})"
        ),
        "prime_cauchy_davenport_sumset_exists": (
            "forall p b c d e k l. "
            f"({prime('p', tag='independent_v27_sumset_prime')}) -> "
            f"({_modular_count('b', 'c', 'p', 'k')}) -> "
            f"({_modular_count('d', 'e', 'p', 'l')}) -> "
            "~(k = 0) -> ~(l = 0) -> exists sb sc m. "
            f"({_modular_count('sb', 'sc', 'p', 'm')}) /\\ "
            f"(({_modular_sumset('b', 'c', 'd', 'e', 'sb', 'sc', 'p')}) /\\ "
            f"({_cauchy_bound('p', 'k', 'l', 'm')}))"
        ),
    }
    for name, statement in exact.items():
        row = specs.get(name)
        if row is None or _closed_formula(row.statement) != _closed_formula(statement):
            _fail(f"Alpha-v27 changed the exact unconditional endpoint {name!r}")

def _verify_truthful_boundaries(names: set[str]) -> None:
    missing = set(FRONTIER_ROOT_NAMES).difference(names)
    if missing:
        _fail(f"Alpha-v27 omitted a genuine constructive boundary root: {sorted(missing)!r}")
    invented = FORBIDDEN_UNPROVED_CLAIMS.intersection(names)
    if invented:
        _fail(f"Alpha-v27 falsely admitted an unproved ambitious boundary: {sorted(invented)!r}")
    for name, expected in INDEPENDENT_SECOND_WAVE_STATEMENT_SHA256.items():
        source = v27.ALPHA_EDITION.by_name[name].spec
        if sha256(source.statement.encode()).hexdigest() != expected:
            _fail(f"Alpha-v27 changed independently pinned second-wave statement {name!r}")
    _verify_unconditional_endpoints({name: entry.spec for name, entry in v27.ALPHA_EDITION.by_name.items()})


def _verify_independent_lean_evidence(
    promotion: dict[str, Any], proof_record: dict[str, Any]
) -> None:
    if (
        promotion.get("independent_lean_bundle_verified") is not True
        or proof_record.get("independent_lean_bundle_verified") is not True
    ):
        _fail("Alpha-v27 omitted independently compiled Lean proof-bundle verification")


def _verify_rows(
    rows: list[dict[str, Any]], parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]], checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != v27.EXPECTED_ALPHA_V27_COUNT
    ):
        _fail("Alpha-v27 changed its exact 2,138-row parent or additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v27 lacks its independently checked second-wave proof bundle")
    bundle, receipt, positions = checked
    if type(positions) is not dict:
        _fail("Alpha-v27 lacks exact independently checked proof-node positions")
    for index, old in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(old) is not dict:
            _fail(f"Alpha-v27 historical theorem row {index} is malformed")
        name = str(old.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v27 changed immutable theorem order at index {index}")
        if row != old:
            _fail(f"Alpha-v27 modified immutable Alpha-v26 parent row {name!r}")
    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, v27.EXPECTED_ALPHA_V27_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v27 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row, index=index, bundle=bundle, receipt=receipt,
            node_id=positions[name], documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v27.FRONTIER_NEW_NAMES:
        _fail("Alpha-v27 changed its exact ordered additive theorem frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V27_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v27 changed its sealed additive theorem-name digest")
    if (
        campaigns != Counter(EXPECTED_CAMPAIGNS)
        or campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
    ):
        _fail("Alpha-v27 changed its exact constructive theorem-family counts")
    expected_evidence = Counter(
        stable_closed=builder.EXPECTED_STABLE_COUNT,
        alpha_closed=v27.EXPECTED_ALPHA_V27_COUNT - builder.EXPECTED_STABLE_COUNT,
    )
    if Counter(row.get("evidence_status") for row in rows) != expected_evidence:
        _fail("Alpha-v27 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v27 retained an unchecked theorem in its completely checked edition")
    available: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= available:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in available:
            _fail(f"Alpha-v27 duplicated the checked theorem {name!r}")
        available.add(name)
        edges += len(dependencies)
    if (
        len(available) != v27.EXPECTED_ALPHA_V27_COUNT
        or edges != v27.EXPECTED_ALPHA_V27_EDGE_COUNT
    ):
        _fail("Alpha-v27 changed its complete original-kernel-checked dependency DAG")
    _verify_truthful_boundaries(set(frontier))


def _verify_topology(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    topology = metrics.get("dependency_graph")
    if type(topology) is not dict:
        _fail("Alpha-v27 lost its complete checked dependency graph")
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    kept = [{"dependency": dep, "theorem": theorem} for dep, theorem in kept_edges]
    redundant = [{"dependency": dep, "theorem": theorem} for dep, theorem in redundant_edges]
    counts = Counter(depths.values())
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_origins = Counter(origins[name] for _dependency, name in redundant_edges)
    parent = _load(builder.PARENT_ALPHA_METRICS)["dependency_graph"]
    if (
        topology.get("declared_edge_count") != v27.EXPECTED_ALPHA_V27_EDGE_COUNT
        or topology.get("layer_count") != v27.EXPECTED_ALPHA_V27_LAYER_COUNT
        or max(depths.values(), default=-1) + 1 != v27.EXPECTED_ALPHA_V27_LAYER_COUNT
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
        _fail("Alpha-v27 changed independently derived checked-DAG topology")


def _verify_principal_roots() -> None:
    """Check one actual closed root at a time without retaining 27 certificates."""
    for name in FRONTIER_ROOT_NAMES:
        result = None
        try:
            result = v27.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")
        finally:
            result = None
            # Keep the single authenticated bundle, not every materialized
            # principal certificate. No kernel/resource policy is changed.
            v27.replay.cache_clear()
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
        _fail(f"cannot read sealed Alpha-v27 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v27 artifact schemas changed")
    rows = catalog.get("theorems")
    evidence = {
        "alpha_closed": v27.EXPECTED_ALPHA_V27_COUNT - builder.EXPECTED_STABLE_COUNT,
        "stable_closed": builder.EXPECTED_STABLE_COUNT,
    }
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != v27.EXPECTED_ALPHA_V27_COUNT
        or metrics.get("theorem_count") != v27.EXPECTED_ALPHA_V27_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != v27.EXPECTED_ALPHA_V27_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != v27.EXPECTED_ALPHA_V27_CHECKED_USE_COUNT
        or catalog.get("edge_count") != v27.EXPECTED_ALPHA_V27_EDGE_COUNT
        or catalog.get("layer_count") != v27.EXPECTED_ALPHA_V27_LAYER_COUNT
        or catalog.get("evidence_counts") != evidence
    ):
        _fail("Alpha-v27 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v27.ALPHA_V27_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v27.ALPHA_V27_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256") != base._ordered_root(v27.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v27 changed exact additive enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v26") != builder._parent_binding():
        _fail("Alpha-v27 lost exact sealed Alpha-v26 artifact provenance")

    documents = _documents(catalog, parent=parent)
    # Executes the unchanged independent HA kernel AND the compiled Lean verifier.
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        catalog.get("alpha_v27_second_wave_promotion") != promotion
        or metrics.get("alpha_v27_second_wave_promotion") != promotion
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V27_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != v27.EXPECTED_ALPHA_V27_COUNT
        or promotion.get("campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v27 changed its exact second-wave additive proof evidence")
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
        _fail("Alpha-v27 changed independently checked second-wave proof metrics")
    _verify_independent_lean_evidence(promotion, proof)
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v27 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed" or full.get("checked") != v27.EXPECTED_ALPHA_V27_COUNT
        or full.get("missing") != 0 or full.get("required") != v27.EXPECTED_ALPHA_V27_COUNT
    ):
        _fail("Alpha-v27 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    historical = _load(builder.PARENT_ALPHA_METRICS)["checked_closure_metrics"]
    expected_digests = historical["certificate_digest_kinds"][
        "self-contained-proof-bundle-sha256"
    ] + FRONTIER_V27_EXPECTED_COUNT
    if (
        accounting.get("metric_bearing_theorem_count") != v27.EXPECTED_ALPHA_V27_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        ) != expected_digests
    ):
        _fail("Alpha-v27 misstated its complete independently checked proof accounting")
    campaign = accounting.get("campaign_v27_bundle_accounting", {})
    if (
        campaign.get("campaign_count") != len(EXPECTED_CAMPAIGNS)
        or campaign.get("new_checked_theorem_count") != FRONTIER_V27_EXPECTED_COUNT
        or campaign.get("campaign_counts") != EXPECTED_CAMPAIGNS
        or campaign.get("proof_bundle") != proof
        or gates.get("complete_constructive_alpha_v27_second_wave")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v27 changed exact second-wave proof-accounting gates")
    _verify_topology(rows, metrics)

    catalog_digest = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_digest = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_digest = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_digest
        or metrics.get("dependency_graph_sha256") != graph_digest
        or metrics.get("edition_identity_sha256") != v27.ALPHA_V27_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v27.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v27 catalog, dependency graph, or metrics artifact changed")
    old_channels = _load(builder.PARENT_CHANNELS)
    actual = channels.get("channels")
    if (
        type(actual) is not dict or channels.get("default_channel") != "stable"
        or actual.get("stable") != old_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256") != builder._digest(builder._compact(actual))
        or channels.get("parent_channels_v26") != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v27 changed immutable Stable pointer or default release channel")
    alpha = actual.get("alpha")
    if (
        type(alpha) is not dict or alpha.get("artifact_sha256") != catalog_digest
        or alpha.get("theorem_count") != v27.EXPECTED_ALPHA_V27_COUNT
        or alpha.get("checked_use_count") != v27.EXPECTED_ALPHA_V27_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v27.ALPHA_V27_IDENTITY_SHA256
        or alpha.get("parent_alpha_v26_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v27_frontier_new_count") != FRONTIER_V27_EXPECTED_COUNT
        or alpha.get("frontier_v27_campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v27 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_digest), ("metrics", metrics_digest), ("dependency_graph", graph_digest)
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v27 changed exact {key} channel pointer digest")

    # Avoid loading unrelated historical Alpha proof artifacts.
    result = v27.replay("zero_add", edition="stable")
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
        "verified Alpha v27 independently: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={v27.EXPECTED_ALPHA_V27_COUNT}, "
        f"checked-use={v27.EXPECTED_ALPHA_V27_CHECKED_USE_COUNT}, "
        f"frontier-new={FRONTIER_V27_EXPECTED_COUNT}, "
        f"campaigns={len(EXPECTED_CAMPAIGNS)}, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
