#!/usr/bin/env python3
"""Independently verify the fully proof-closed additive Alpha-v28 release."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v28 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v28 as v28
from peano_lab.library.alpha_enrollment_v28 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V28_EXPECTED_COUNT,
    FRONTIER_V28_EXPECTED_NAMES_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v28_enrollment,
)
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.fermat_residue_product_candidate import coprime
from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.ha_signed_bezout_candidate import signed_bezout
from peano_lab.library.foundation_saturation_candidate import prime_factor_list_relation
from peano_lab.library.prime_factorization_permutation_candidate import (
    prime_factor_list_permutation_relation,
)
from peano_lab.library.prime_enumeration_candidate import (
    next_prime_relation, prime_list_relation,
)
from peano_lab.library.binary_length_candidate import _power_two_terms
from peano_lab.library.finite_sum_theorems import _at
from peano_lab.library.gaussian_euclidean_candidate import (
    gaussian_integer_relation,
    gaussian_euclidean_division_relation,
    gaussian_signed_division_remainder_relation,
)
from peano_lab.library.eisenstein_euclidean_candidate import (
    eisenstein_integer_relation,
    eisenstein_euclidean_division_relation,
    eisenstein_signed_division_remainder_relation,
)
from peano_lab.library.theorems import _closed_formula


EXPECTED_CAMPAIGNS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
FRONTIER_ROOT_NAMES = tuple(ROOT_STATEMENT_SHA256)
INDEPENDENT_LOWER_LAYER_STATEMENT_SHA256 = {
    "foundation_division_exists_unique": "f43569ef56675e5aab556c26ad0606eea4f4de9c1c54078e6c51c3e96ef653ab",
    "foundation_signed_bezout_canonical_gcd": "3d20b5eb4e05f3b50ba301946c3fc791504ef4586ae3d2bed3f2bd58648790a6",
    "foundation_coprime_product_divisor": "4ec0d3dde7c6319356d61d282abed4edd22af6eeffba58e03162a18c4e58de42",
    "foundation_prime_factor_list_exists": "af68e2e841fe13eafddb375135f9f1abde79b0185d5722d3851c0fcf61af56dc",
    "foundation_primes_above_every_bound": "be3aeb8487e6cac71fa3093363e847f3afbdd176e23ebdbb5f003c080f518167",
    "prime_factor_lists_permutation_exists": "89df5c484cb30ab9c74dd04af9a5700c635ae402d01f8088ff934f75e0254518",
    "prime_factorization_exists_unique_up_to_permutation": "622f8362d88b818d10462b55bca228e06f0c517174001c7ea039b85bb054ab7c",
    "least_prime_above_exists_unique": "ccf83345ee78da1ec4542d321ee586284122be1121874e6b53de8e64960d043c",
    "first_primes_double_exponential_bound": "b69363aca6a0a887d3baba0ca6ddd13a550496075f15ec2cb4199e7c73054676",
    "prime_list_every_entry_is_prime": "d0a3b4a6314a9146f511ea2279ccf7ef6d02d4fd89a58620a3b6e94987e12e92",
    "prime_list_omits_no_smaller_prime": "6d518facea11f0601663db951a03bfcaa9790bfd7edfdd33ae81089de5a8c734",
    "prime_list_strictly_increasing": "3f5496bc64b968f967791192cf2d11b65e1de916b9e24ddbedb83163a8f75431",
    "first_primes_list_exists": "4427d0ffd64799cd180d0c99e4084a39db1023c734a88c77f840c2d59a215d7b",
    "gaussian_signed_euclidean_division_exists": "b74e03b044aac9c837f2098ad4e3d75a977fddf0d331ae84e02d440d422c91d8",
    "gaussian_euclidean_division_exists": "7c20ce64493b15888f961ece2d86e97171370aee53e8517ee21db8d53d82fd10",
    "gaussian_norm_exists_unique": "452d832311908cb4fca7139b9147039b0a05331967073d0b1743117f510599fd",
    "gaussian_add_exists": "af126fdb2cc45f1f1b2620570ac6e6759b4e3118a25acaa96862b53971ec255d",
    "gaussian_multiply_exists": "3ded8b89b9624cb91cd7a7eb23ea6a2921aa912aba4dc6a8c35d8d308d3971d0",
    "gaussian_norm_multiply": "b9f32039576506c3cabe3efcb762725f554089562b866d504fb0f92187159c64",
    "gaussian_representation_zero_iff": "7fa8a228116bfb6de5d50cd5782c6e33cc4e659ff2a2c4725d0979e77f0d6a08",
    "eisenstein_signed_euclidean_division_exists": "481e8a8d2b7dc8431901e86b902b578a144c8aa72133a5e5e6b4b6c8c5e44725",
    "eisenstein_euclidean_division_exists": "160d72250ab01db0ed32ca57bc472fd22d5ea307e4042815397cc771c3e102a9",
    "eisenstein_norm_exists": "e6d89e5a8fe3273d17fa59ff1f1f8df4011980acfc8ed776174a95edaa13cf24",
    "eisenstein_norm_functional": "887f9714c16a4ef5214f55c99765f59e34790e513d78487079ed0dd7b8e79463",
    "eisenstein_add_exists": "d4eef68809aa569e91530014909f8b0f27df7cb44d02d499c43403b89cbef319",
    "eisenstein_add_functional": "352350308e61675c50d3d6f9ed650738a0c23a0d42b64dbcd75e8796667d12d8",
    "eisenstein_multiply_exists": "06cca39ddb2e8b5d18210bf0ed9a24e36653bee25af58920a1ac1cca363ab482",
    "eisenstein_multiply_functional": "dbb42ca73f3287a28cdda7151f5e6fb4382429e74a2067d9e719d20d65724387",
    "eisenstein_norm_multiply": "42d3bea19f1c39be902a69da5b51c89dc4acef875a41d63dc46d20eef932e340",
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
        _fail("Alpha-v28 lost its immutable Alpha-v27 evidence-document inventory")
    inherited: dict[str, dict[str, Any]] = {}
    for record in inventory:
        if type(record) is not dict or type(record.get("path")) is not str:
            _fail("Alpha-v28 inherited a malformed Alpha-v27 evidence-document binding")
        path = record["path"]
        if path in inherited:
            _fail(f"duplicate immutable Alpha-v27 evidence-document binding {path!r}")
        inherited[path] = record
        if not _exact_json(documents.get(path), record):
            _fail(f"Alpha-v28 changed immutable Alpha-v27 evidence-document binding {path!r}")

    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = inherited.get(path)
    if (
        record is None
        or record.get("path") != path
        or record.get("sha256") != builder.EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or type(record.get("bytes")) is not int
        or record["bytes"] != builder.EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        _fail("Alpha-v28 changed its immutable quadratic-reciprocity corpus catalog binding")
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
        _fail("Alpha-v28 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if (
            type(item) is not dict
            or type(item.get("path")) is not str
            or type(item.get("sha256")) is not str
            or type(item.get("bytes")) is not int
        ):
            _fail("Alpha-v28 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v28 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v28_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        record = result.get(path)
        if record is None:
            _fail(f"missing Alpha-v28 actual-proof control document {path!r}")
        try:
            payload = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v28 actual-proof source {path!r}: {error}")
        if record["sha256"] != sha256(payload).hexdigest():
            _fail(f"changed Alpha-v28 actual-proof control document {path!r}")
        if record["bytes"] != len(payload):
            _fail(f"changed Alpha-v28 actual-proof byte count {path!r}")

    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v28 lost its immutable sealed Alpha-v27 parent document")
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
        (source, "alpha_v28_frontier_dependency_curried_body", "dependency_curried_body", "document"),
        (test, "alpha_v28_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
        (rfc, "alpha_v28_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
        (
            builder.CLOSURE_ARTIFACT,
            "alpha_v28_lower_layer_self_contained_constructive_proof_bundle",
            "independently_kernel_checked_dependency_closed_proof",
            f"nodes[id={node_id}]",
        ),
        (
            builder.CLOSURE_RECEIPT,
            "alpha_v28_lower_layer_original_kernel_receipt",
            "original_kernel_independent_dependency_closure_verification",
            "document",
        ),
        (parent, "sealed_alpha_v27_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
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
    enrollment = alpha_v28_enrollment()
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
        "alpha_v28_frontier_enrollment", "evidence_links",
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
        "bundle_campaign": "lower_layer", "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest, "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if not _exact_json(row.get("alpha_v28_frontier_enrollment"), transition):
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    closure = {
        "body_proof_depth": depth, "body_proof_nodes": nodes,
        "bundle_campaign": "lower_layer",
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
    """Check exact constructive witnesses, not conditional stand-ins.

    Factorizations are arbitrary unordered beta-coded prime lists.  The
    permutation conclusion includes a real bounded, injective, surjective
    index code.  Prime enumeration supplies the exhaustive first-prime list
    and both exponential witnesses; none is an input premise.
    """
    def lt(a: str, b: str, tag: str) -> str:
        return f"exists independent_{tag}. independent_{tag} + S ({a}) = ({b})"

    def division(q: str, r: str, tag: str) -> str:
        return f"n = d * {q} + {r} /\\ ({lt(r, 'd', tag)})"

    first = prime_factor_list_relation("n", "b", "c", "l", tag="independent_source")
    other = prime_factor_list_relation("n", "d", "e", "m", tag="independent_target")
    permutation = prime_factor_list_permutation_relation(
        "b", "c", "l", "d", "e", "m", "u", "v", tag="independent_matching"
    )
    exact = {
        "foundation_division_exists_unique": (
            "forall n d. ~(d = 0) -> exists q r. "
            f"(({division('q', 'r', 'chosen')}) /\\ "
            f"forall u v. ({division('u', 'v', 'compared')}) -> u = q /\\ v = r)"
        ),
        "foundation_signed_bezout_canonical_gcd": (
            "forall a b. exists g u v. "
            f"(({is_gcd('g', 'a', 'b', tag='independent_gcd')}) /\\ "
            f"(({signed_bezout('g', 'a', 'b', 'u', 'v', tag='independent_bezout')}) /\\ "
            f"forall h. ({is_gcd('h', 'a', 'b', tag='independent_comparison')}) -> h = g))"
        ),
        "foundation_coprime_product_divisor": (
            f"forall a b c. (({coprime('a', 'b', tag='independent_euclid')}) /\\ "
            "(exists q. b * c = a * q)) -> exists q. c = a * q"
        ),
        "foundation_prime_factor_list_exists": (
            f"forall n. ~(n = 0) -> exists l b c. ({first})"
        ),
        "foundation_primes_above_every_bound": (
            f"forall B. exists p. (({prime('p', tag='independent_unbounded')}) /\\ "
            f"({lt('B', 'p', 'unbounded')}))"
        ),
        "prime_factor_lists_permutation_exists": (
            f"forall n b c l d e m. (({first}) /\\ ({other})) -> "
            f"exists u v. ({permutation})"
        ),
        "prime_factorization_exists_unique_up_to_permutation": (
            f"forall n. ~(n = 0) -> exists l b c. (({first}) /\\ "
            f"forall m d e. ({other}) -> exists u v. ({permutation}))"
        ),
        "least_prime_above_exists_unique": (
            f"forall a. exists p. ({next_prime_relation('a', 'p', tag='independent_next')}) /\\ "
            f"forall q. ({next_prime_relation('a', 'q', tag='independent_other')}) -> q = p"
        ),
        "first_primes_list_exists": (
            f"forall k. exists b c. {prime_list_relation('b', 'c', 'k', tag='independent_total')}"
        ),
        "first_primes_double_exponential_bound": (
            "forall k. ~(k = 0) -> exists b c j p e B. k = S j /\\ "
            f"(({prime_list_relation('b', 'c', 'k', tag='independent_list')}) /\\ "
            f"(({_at('b', 'c', 'j', 'p', tag='independent_last')}) /\\ "
            f"(({_power_two_terms('k', 'e', tag='independent_exponent')}) /\\ "
            f"(({_power_two_terms('e', 'B', tag='independent_bound')}) /\\ "
            f"({lt('p', 'B', 'strict')})))))"
        ),
        "gaussian_signed_euclidean_division_exists": (
            "forall a b c d e f g h. ~(e = f /\\ g = h) -> "
            "exists qp qn up un rp rn sp sn U V. "
            f"({gaussian_signed_division_remainder_relation('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'qp', 'qn', 'up', 'un', 'rp', 'rn', 'sp', 'sn', 'U', 'V', tag='independent_gaussian_signed')})"
        ),
        "gaussian_euclidean_division_exists": (
            f"forall a b. ({gaussian_integer_relation('a', tag='independent_gaussian_dividend')}) -> "
            f"({gaussian_integer_relation('b', tag='independent_gaussian_divisor')}) -> "
            "~(b = 0) -> exists q r U V. "
            f"({gaussian_euclidean_division_relation('a', 'b', 'q', 'r', 'U', 'V', tag='independent_gaussian_euclidean')})"
        ),
        "eisenstein_signed_euclidean_division_exists": (
            "forall a b c d e f g h. ~(e = f /\\ g = h) -> "
            "exists qp qn up un rp rn sp sn U V. "
            f"({eisenstein_signed_division_remainder_relation('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'qp', 'qn', 'up', 'un', 'rp', 'rn', 'sp', 'sn', 'U', 'V', tag='independent_eisenstein_signed', variables=('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'qp', 'qn', 'up', 'un', 'rp', 'rn', 'sp', 'sn', 'U', 'V'))})"
        ),
        "eisenstein_euclidean_division_exists": (
            f"forall a b. ({eisenstein_integer_relation('a', tag='independent_eisenstein_dividend', variables=('a',))}) -> "
            f"({eisenstein_integer_relation('b', tag='independent_eisenstein_divisor', variables=('b',))}) -> "
            "~(b = 0) -> exists q r U V. "
            f"({eisenstein_euclidean_division_relation('a', 'b', 'q', 'r', 'U', 'V', tag='independent_eisenstein_euclidean', variables=('a', 'b', 'q', 'r', 'U', 'V'))})"
        ),
    }
    for name, statement in exact.items():
        row = specs.get(name)
        if row is None or _closed_formula(row.statement) != _closed_formula(statement):
            _fail(f"Alpha-v28 changed the exact unconditional endpoint {name!r}")


def _verify_truthful_boundaries(names: set[str]) -> None:
    missing = set(FRONTIER_ROOT_NAMES).difference(names)
    if missing:
        _fail(f"Alpha-v28 omitted a genuine constructive boundary root: {sorted(missing)!r}")
    invented = FORBIDDEN_UNPROVED_CLAIMS.intersection(names)
    if invented:
        _fail(f"Alpha-v28 falsely admitted an unproved ambitious boundary: {sorted(invented)!r}")
    for name, expected in INDEPENDENT_LOWER_LAYER_STATEMENT_SHA256.items():
        source = v28.ALPHA_EDITION.by_name[name].spec
        if sha256(source.statement.encode()).hexdigest() != expected:
            _fail(f"Alpha-v28 changed independently pinned lower-layer statement {name!r}")
    _verify_unconditional_endpoints({name: entry.spec for name, entry in v28.ALPHA_EDITION.by_name.items()})


def _verify_independent_lean_evidence(
    promotion: dict[str, Any], proof_record: dict[str, Any]
) -> None:
    if (
        promotion.get("independent_lean_bundle_verified") is not True
        or proof_record.get("independent_lean_bundle_verified") is not True
    ):
        _fail("Alpha-v28 omitted independently compiled Lean proof-bundle verification")


def _verify_rows(
    rows: list[dict[str, Any]], parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]], checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != v28.EXPECTED_ALPHA_V28_COUNT
    ):
        _fail("Alpha-v28 changed its exact 2,560-row parent or additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v28 lacks its independently checked lower-layer proof bundle")
    bundle, receipt, positions = checked
    if type(positions) is not dict:
        _fail("Alpha-v28 lacks exact independently checked proof-node positions")
    for index, old in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(old) is not dict:
            _fail(f"Alpha-v28 historical theorem row {index} is malformed")
        name = str(old.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v28 changed immutable theorem order at index {index}")
        if not _exact_json(row, old):
            _fail(f"Alpha-v28 modified immutable Alpha-v27 parent row {name!r}")
    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, v28.EXPECTED_ALPHA_V28_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v28 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row, index=index, bundle=bundle, receipt=receipt,
            node_id=positions[name], documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v28.FRONTIER_NEW_NAMES:
        _fail("Alpha-v28 changed its exact ordered additive theorem frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V28_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v28 changed its sealed additive theorem-name digest")
    if (
        campaigns != Counter(EXPECTED_CAMPAIGNS)
        or campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
    ):
        _fail("Alpha-v28 changed its exact constructive theorem-family counts")
    expected_evidence = Counter(
        stable_closed=builder.EXPECTED_STABLE_COUNT,
        alpha_closed=v28.EXPECTED_ALPHA_V28_COUNT - builder.EXPECTED_STABLE_COUNT,
    )
    if Counter(row.get("evidence_status") for row in rows) != expected_evidence:
        _fail("Alpha-v28 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v28 retained an unchecked theorem in its completely checked edition")
    available: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= available:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in available:
            _fail(f"Alpha-v28 duplicated the checked theorem {name!r}")
        available.add(name)
        edges += len(dependencies)
    if (
        len(available) != v28.EXPECTED_ALPHA_V28_COUNT
        or edges != v28.EXPECTED_ALPHA_V28_EDGE_COUNT
    ):
        _fail("Alpha-v28 changed its complete original-kernel-checked dependency DAG")
    _verify_truthful_boundaries(set(frontier))


def _verify_topology(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    topology = metrics.get("dependency_graph")
    if type(topology) is not dict:
        _fail("Alpha-v28 lost its complete checked dependency graph")
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    kept = [{"dependency": dep, "theorem": theorem} for dep, theorem in kept_edges]
    redundant = [{"dependency": dep, "theorem": theorem} for dep, theorem in redundant_edges]
    counts = Counter(depths.values())
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_origins = Counter(origins[name] for _dependency, name in redundant_edges)
    parent = _load(builder.PARENT_ALPHA_METRICS)["dependency_graph"]
    expected = {
        "declared_edge_count": v28.EXPECTED_ALPHA_V28_EDGE_COUNT,
        "layer_count": v28.EXPECTED_ALPHA_V28_LAYER_COUNT,
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
        or max(depths.values(), default=-1) + 1 != v28.EXPECTED_ALPHA_V28_LAYER_COUNT
        or len(kept) + len(redundant) != v28.EXPECTED_ALPHA_V28_EDGE_COUNT
    ):
        _fail("Alpha-v28 changed independently derived checked-DAG topology")


def _verify_principal_roots() -> None:
    """Check one actual closed root at a time without retaining every materialized certificate."""
    for name in FRONTIER_ROOT_NAMES:
        print(f"checking Alpha-v28 principal root: {name}", flush=True)
        result = None
        try:
            result = v28.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")
            print(f"accepted Alpha-v28 principal root: {name}", flush=True)
        finally:
            result = None
            # Keep the single authenticated bundle, not every materialized
            # principal certificate. No kernel/resource policy is changed.
            v28.replay.cache_clear()
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
        _fail(f"cannot read sealed Alpha-v28 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v28 artifact schemas changed")
    rows = catalog.get("theorems")
    evidence = {
        "alpha_closed": v28.EXPECTED_ALPHA_V28_COUNT - builder.EXPECTED_STABLE_COUNT,
        "stable_closed": builder.EXPECTED_STABLE_COUNT,
    }
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != v28.EXPECTED_ALPHA_V28_COUNT
        or metrics.get("theorem_count") != v28.EXPECTED_ALPHA_V28_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != v28.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != v28.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT
        or catalog.get("edge_count") != v28.EXPECTED_ALPHA_V28_EDGE_COUNT
        or catalog.get("layer_count") != v28.EXPECTED_ALPHA_V28_LAYER_COUNT
        or catalog.get("evidence_counts") != evidence
    ):
        _fail("Alpha-v28 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v28.ALPHA_V28_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v28.ALPHA_V28_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256") != base._ordered_root(v28.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v28 changed exact additive enrollment, theorem, or membership roots")
    if not _exact_json(catalog.get("parent_alpha_v27"), builder._parent_binding()):
        _fail("Alpha-v28 lost exact sealed Alpha-v27 artifact provenance")

    documents = _documents(catalog, parent=parent)
    # Executes the unchanged independent HA kernel AND the compiled Lean verifier.
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        not _exact_json(catalog.get("alpha_v28_lower_layer_promotion"), promotion)
        or not _exact_json(metrics.get("alpha_v28_lower_layer_promotion"), promotion)
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V28_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != v28.EXPECTED_ALPHA_V28_COUNT
        or promotion.get("campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v28 changed its exact lower-layer additive proof evidence")
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
        _fail("Alpha-v28 changed independently checked lower-layer proof metrics")
    _verify_independent_lean_evidence(promotion, proof)
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v28 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed" or full.get("checked") != v28.EXPECTED_ALPHA_V28_COUNT
        or full.get("missing") != 0 or full.get("required") != v28.EXPECTED_ALPHA_V28_COUNT
    ):
        _fail("Alpha-v28 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    historical = _load(builder.PARENT_ALPHA_METRICS)["checked_closure_metrics"]
    expected_digests = historical["certificate_digest_kinds"][
        "self-contained-proof-bundle-sha256"
    ] + FRONTIER_V28_EXPECTED_COUNT
    if (
        accounting.get("metric_bearing_theorem_count") != v28.EXPECTED_ALPHA_V28_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        ) != expected_digests
    ):
        _fail("Alpha-v28 misstated its complete independently checked proof accounting")
    campaign = accounting.get("campaign_v28_bundle_accounting", {})
    if (
        campaign.get("campaign_count") != len(EXPECTED_CAMPAIGNS)
        or campaign.get("new_checked_theorem_count") != FRONTIER_V28_EXPECTED_COUNT
        or campaign.get("campaign_counts") != EXPECTED_CAMPAIGNS
        or campaign.get("proof_bundle") != proof
        or gates.get("complete_constructive_alpha_v28_lower_layer")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v28 changed exact lower-layer proof-accounting gates")
    _verify_topology(rows, metrics)

    catalog_digest = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_digest = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_digest = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_digest
        or metrics.get("dependency_graph_sha256") != graph_digest
        or metrics.get("edition_identity_sha256") != v28.ALPHA_V28_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v28.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v28 catalog, dependency graph, or metrics artifact changed")
    old_channels = _load(builder.PARENT_CHANNELS)
    actual = channels.get("channels")
    if (
        type(actual) is not dict or channels.get("default_channel") != "stable"
        or actual.get("stable") != old_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256") != builder._digest(builder._compact(actual))
        or channels.get("parent_channels_v27") != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v28 changed immutable Stable pointer or default release channel")
    alpha = actual.get("alpha")
    if (
        type(alpha) is not dict or alpha.get("artifact_sha256") != catalog_digest
        or alpha.get("theorem_count") != v28.EXPECTED_ALPHA_V28_COUNT
        or alpha.get("checked_use_count") != v28.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v28.ALPHA_V28_IDENTITY_SHA256
        or alpha.get("parent_alpha_v27_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v28_frontier_new_count") != FRONTIER_V28_EXPECTED_COUNT
        or alpha.get("frontier_v28_campaign_counts") != EXPECTED_CAMPAIGNS
    ):
        _fail("Alpha-v28 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_digest), ("metrics", metrics_digest), ("dependency_graph", graph_digest)
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v28 changed exact {key} channel pointer digest")

    # Avoid loading unrelated historical Alpha proof artifacts.
    result = v28.replay("zero_add", edition="stable")
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
        "verified Alpha v28 independently: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={v28.EXPECTED_ALPHA_V28_COUNT}, "
        f"checked-use={v28.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT}, "
        f"frontier-new={FRONTIER_V28_EXPECTED_COUNT}, "
        f"campaigns={len(EXPECTED_CAMPAIGNS)}, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
