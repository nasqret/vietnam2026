"""Fail-closed mutation gates for complete constructive Alpha-v19 admission."""

from __future__ import annotations

from copy import deepcopy

import pytest

import build_peano_library_channels_v19 as builder
import verify_peano_library_channels_v19 as verifier
from peano_lab.library import editions_v19 as v19


@pytest.fixture(scope="module")
def release():
    parent = verifier._load(builder.PARENT_ALPHA)
    catalog = verifier._load(builder.DEFAULT_ALPHA)
    documents = verifier._documents(catalog)
    bundles = {
        label: v19._checked_campaign_bundle(label)
        for label in v19.CAMPAIGN_BUNDLE_LABELS
    }
    return parent["theorems"], catalog["theorems"], documents, bundles


def _rows(release):
    parent, rows, documents, bundles = release
    return parent, deepcopy(rows), documents, bundles


def _by_name(rows):
    return {row["name"]: row for row in rows}


def _residual(rows):
    return _by_name(rows)[v19.RESIDUAL_PROMOTED_NAMES[0]]


def _frontier(rows):
    return _by_name(rows)[v19.FRONTIER_NEW_NAMES[0]]


def test_exact_complete_dependency_closed_additive_release_is_accepted(release) -> None:
    parent, rows, documents, bundles = release
    verifier._verify_rows(rows, parent, documents, bundles)


def test_unrelated_stable_historical_row_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    rows[0]["summary"] = "forged historical Stable summary"
    with pytest.raises(ValueError, match="unrelated immutable parent row"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_missing_residual_evidence_promotion_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    name = v19.RESIDUAL_PROMOTED_NAMES[0]
    parent_by_name = _by_name(parent)
    index = next(i for i, row in enumerate(rows) if row["name"] == name)
    rows[index] = deepcopy(parent_by_name[name])
    with pytest.raises(ValueError, match="exact immutable field set"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_false_extra_historical_promotion_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)["prime_mod_four_trichotomy"]
    row["alpha_v19_residual_promotion"] = {}
    with pytest.raises(ValueError, match="unrelated immutable parent row"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_immutable_statement_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["statement"] = "forall n. n = 0"
    with pytest.raises(ValueError, match="immutable parent field 'statement'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_parent_catalog_forgery_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["alpha_v19_residual_promotion"]["parent_catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="immutable parent transition"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_parent_row_forgery_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["alpha_v19_residual_promotion"]["parent_row_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="immutable parent transition"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_bundle_campaign_forgery_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["alpha_v19_residual_promotion"]["bundle_campaign"] = "frontier"
    with pytest.raises(ValueError, match="immutable parent transition"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_actual_proof_node_forgery_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["empty_context_closure"]["bundle_node_id"] += 1
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_classical_kernel_forgery_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["empty_context_closure"]["kernel_mode"] = "classical"
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_historical_link_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["evidence_links"][0]["role"] = "forged historical provenance"
    with pytest.raises(ValueError, match="immutable historical links"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_residual_missing_actual_proof_link_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _residual(rows)["evidence_links"].pop()
    with pytest.raises(ValueError, match="immutable historical links"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_missing_additive_frontier_row_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    rows.pop()
    with pytest.raises(ValueError, match="64-row additive frontier"):
        verifier._verify_rows(rows, parent, documents, bundles)


@pytest.mark.parametrize("name", verifier.FRONTIER_ROOT_NAMES)
def test_missing_exact_major_constructive_frontier_root_is_rejected(
    release,
    name: str,
) -> None:
    parent, rows, documents, bundles = _rows(release)
    _by_name(rows)[name]["name"] = f"forged_{name}"
    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_forward_additive_frontier_reordering_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    rows[builder.EXPECTED_PARENT_COUNT], rows[builder.EXPECTED_PARENT_COUNT + 1] = (
        rows[builder.EXPECTED_PARENT_COUNT + 1],
        rows[builder.EXPECTED_PARENT_COUNT],
    )
    with pytest.raises(ValueError, match="exact additive order"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_campaign_ownership_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["frontier_campaign"] = "linear_congruence"
    with pytest.raises(ValueError, match="source-bound field 'frontier_campaign'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_statement_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["statement"] = "forall n. n = 0"
    with pytest.raises(ValueError, match="source-bound field 'statement'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_tactic_script_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["script"].append("DNE")
    with pytest.raises(ValueError, match="source-bound field 'script'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_source_digest_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["source"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source-bound field 'source'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_enrollment_position_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["enrollment_index"] += 1
    with pytest.raises(ValueError, match="source-bound field 'enrollment_index'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_dependency_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["dependencies"].append(v19.FRONTIER_NEW_NAMES[-1])
    with pytest.raises(ValueError, match="source-bound field 'dependencies'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_bundle_node_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["empty_context_closure"]["bundle_node_id"] += 1
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_source_provenance_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["alpha_v19_frontier_enrollment"]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source/proof enrollment"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_parent_provenance_mutation_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["alpha_v19_frontier_enrollment"]["parent_catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source/proof enrollment"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_missing_independent_audit_link_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["evidence_links"].pop()
    with pytest.raises(ValueError, match="source/test/RFC/proof/parent link"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_forged_document_digest_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["evidence_links"][0]["document_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence-document digest"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_frontier_unchecked_evidence_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    _frontier(rows)["checked_use"] = False
    with pytest.raises(ValueError, match="source-bound field 'checked_use'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_unknown_or_missing_independent_bundle_family_is_rejected(release) -> None:
    parent, rows, documents, bundles = release
    with pytest.raises(ValueError, match="two independently checked proof-bundle families"):
        verifier._verify_rows(rows, parent, documents, {"residual": bundles["residual"]})
