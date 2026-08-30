"""Fail-closed mutation gates for immutable additive constructive Alpha v20."""

from __future__ import annotations

from copy import deepcopy

import pytest

import build_peano_library_channels_v20 as builder
import verify_peano_library_channels_v20 as verifier
from peano_lab.library import editions_v20 as v20


@pytest.fixture(scope="module")
def release():
    parent = verifier._load(builder.PARENT_ALPHA)
    catalog = verifier._load(builder.DEFAULT_ALPHA)
    documents = verifier._documents(catalog)
    checked = builder._checked_bundle()
    return parent["theorems"], catalog["theorems"], documents, checked


def _rows(release):
    parent, rows, documents, checked = release
    return parent, deepcopy(rows), documents, checked


def _by_name(rows):
    return {row["name"]: row for row in rows}


def _frontier(rows):
    return rows[builder.EXPECTED_PARENT_COUNT]


def test_exact_immutable_dependency_closed_additive_release_is_accepted(release) -> None:
    parent, rows, documents, checked = release
    verifier._verify_rows(rows, parent, documents, checked)


def test_historical_stable_row_mutation_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows[0]["summary"] = "forged historical Stable summary"
    with pytest.raises(ValueError, match="immutable Alpha-v19 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_historical_alpha_only_row_mutation_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows[builder.EXPECTED_PARENT_COUNT - 1]["checked_use"] = False
    with pytest.raises(ValueError, match="immutable Alpha-v19 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_historical_parent_row_reordering_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(ValueError, match="immutable theorem order"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_historical_parent_evidence_link_mutation_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows[0]["evidence_links"][0]["role"] = "forged immutable evidence"
    with pytest.raises(ValueError, match="immutable Alpha-v19 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_missing_additive_frontier_row_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows.pop()
    with pytest.raises(ValueError, match="39-row additive frontier"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_extra_unreviewed_additive_frontier_row_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows.append(deepcopy(rows[-1]))
    with pytest.raises(ValueError, match="39-row additive frontier"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("name", verifier.FRONTIER_ROOT_NAMES)
def test_missing_exact_major_constructive_root_is_rejected(release, name: str) -> None:
    parent, rows, documents, checked = _rows(release)
    _by_name(rows)[name]["name"] = f"forged_{name}"
    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_forward_additive_frontier_reordering_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    offset = builder.EXPECTED_PARENT_COUNT
    rows[offset], rows[offset + 1] = rows[offset + 1], rows[offset]
    with pytest.raises(ValueError, match="exact additive order"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("frontier_campaign", "bertrand_prime"),
        ("statement", "forall n. n = 0"),
        ("statement_sha256", "0" * 64),
        ("summary", "forged mathematical content"),
        ("summary_sha256", "0" * 64),
        ("dependencies", ["bertrand_strict"]),
        ("dependencies_sha256", "0" * 64),
        ("script", ["DNE"]),
        ("script_sha256", "0" * 64),
        ("checked_use", False),
        ("body_checked", False),
        ("evidence_status", "body_checked"),
        ("membership", "stable"),
        ("enrollment_index", 1_000_000),
        ("enrollment_origin", "stable"),
        ("provenance", ["stable"]),
        ("proof_tag", "forged"),
    ),
)
def test_frontier_source_bound_field_mutations_are_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)[field] = forged
    with pytest.raises(ValueError, match=f"source-bound field '{field}'"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_source_digest_mutation_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["source"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source-bound field 'source'"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_unknown_extra_metadata_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["unreviewed_authority"] = True
    with pytest.raises(ValueError, match="exact immutable field set"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("command_count", 0),
        ("dependency_count", 0),
        ("dne_command_count", 1),
        ("proof_nodes", 0),
        ("proof_depth", 0),
        ("proof_objects", 0),
        ("status", "unchecked"),
    ),
)
def test_frontier_actual_kernel_body_receipt_mutations_are_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["body_receipt"][field] = forged
    with pytest.raises(ValueError, match="original-kernel body receipt"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("bundle_node_id", -1),
        ("bundle_campaign", "invented"),
        ("bundle_sha256", "0" * 64),
        ("campaign", "continued_fraction"),
        ("parent_catalog_sha256", "0" * 64),
        ("source_sha256", "0" * 64),
        ("test_sha256", "0" * 64),
        ("rfc_sha256", "0" * 64),
        ("body_receipt_sha256", "0" * 64),
    ),
)
def test_frontier_source_and_proof_enrollment_forgery_is_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["alpha_v20_frontier_enrollment"][field] = forged
    with pytest.raises(ValueError, match="source/proof enrollment"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("bundle_node_id", -1),
        ("bundle_campaign", "invented"),
        ("bundle_node_count", 0),
        ("bundle_dependency_edge_count", 0),
        ("certificate_sha256", "0" * 64),
        ("kernel_mode", "classical"),
        ("node_statement_sha256", "0" * 64),
        ("status", "unchecked"),
    ),
)
def test_frontier_actual_checked_proof_binding_mutations_are_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["empty_context_closure"][field] = forged
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_missing_independent_audit_link_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"].pop()
    with pytest.raises(ValueError, match="source/test/RFC/proof/parent link"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_duplicate_evidence_link_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    links = _frontier(rows)["evidence_links"]
    links.append(deepcopy(links[0]))
    with pytest.raises(ValueError, match="duplicated a source/proof evidence link"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_evidence_document_digest_forgery_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"][0]["document_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence-document digest"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_proof_node_selector_forgery_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    links = _frontier(rows)["evidence_links"]
    next(link for link in links if link["path"] == builder.CLOSURE_ARTIFACT)[
        "selector"
    ] = "nodes[id=0]"
    with pytest.raises(ValueError, match="exact proof-node selector"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_missing_independently_checked_proof_bundle_is_rejected(release) -> None:
    parent, rows, documents, _checked = release
    with pytest.raises(ValueError, match="independently checked next-layer proof bundle"):
        verifier._verify_rows(rows, parent, documents, ())


def test_missing_independently_checked_proof_node_is_rejected(release) -> None:
    parent, rows, documents, checked = release
    bundle, receipt, positions = checked
    forged_positions = dict(positions)
    forged_positions.pop(v20.FRONTIER_NEW_NAMES[0])
    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, (bundle, receipt, forged_positions))
