"""Mutation gates for the five genuine immutable Alpha-v18 flagship campaigns."""

from __future__ import annotations

from copy import deepcopy

import pytest

import build_peano_library_channels_v18 as builder
import verify_peano_library_channels_v18 as verifier
from peano_lab.library import editions_v18 as v18


@pytest.fixture(scope="module")
def release():
    parent = verifier._load(builder.PARENT_ALPHA)
    catalog = verifier._load(builder.DEFAULT_ALPHA)
    documents = verifier._documents(catalog)
    bundles = {
        label: v18._checked_flagship_bundle(label)
        for label in v18.FLAGSHIP_BUNDLE_LABELS
    }
    return parent["theorems"], catalog["theorems"], documents, bundles


def _rows(release):
    parent, rows, documents, bundles = release
    return parent, deepcopy(rows), documents, bundles


def _by_name(rows):
    return {row["name"]: row for row in rows}


def test_exact_five_campaign_dependency_closed_release_is_accepted(release) -> None:
    parent, rows, documents, bundles = release
    verifier._verify_rows(rows, parent, documents, bundles)


def test_unrelated_body_only_false_promotion_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = next(row for row in rows if row["evidence_status"] == "body_checked")
    row["checked_use"] = True
    row["evidence_status"] = "alpha_closed"
    with pytest.raises(ValueError, match="unrelated immutable parent row"):
        verifier._verify_rows(rows, parent, documents, bundles)


@pytest.mark.parametrize("name", v18.FLAGSHIP_ROOT_NAMES)
def test_missing_exact_flagship_root_promotion_is_rejected(release, name: str) -> None:
    parent, rows, documents, bundles = _rows(release)
    parent_by_name = _by_name(parent)
    index = next(i for i, row in enumerate(rows) if row["name"] == name)
    rows[index] = deepcopy(parent_by_name[name])
    with pytest.raises(ValueError, match="immutable field set"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_mutated_actual_proof_node_binding_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_ROOT_NAMES[-1]]
    row["empty_context_closure"]["bundle_node_id"] -= 1
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_mutated_actual_bundle_ownership_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_ROOT_NAMES[0]]
    row["alpha_v18_promotion"]["bundle_campaign"] = "bertrand"
    with pytest.raises(ValueError, match="immutable parent transition"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_mutated_parent_row_provenance_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_PROMOTED_NAMES[0]]
    row["alpha_v18_promotion"]["parent_row_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="immutable parent transition"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_mutated_historical_evidence_link_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_PROMOTED_NAMES[0]]
    row["evidence_links"][0]["role"] = "forged"
    with pytest.raises(ValueError, match="immutable historical links"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_missing_actual_proof_evidence_link_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_PROMOTED_NAMES[0]]
    row["evidence_links"].pop()
    with pytest.raises(ValueError, match="immutable historical links"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_mutated_immutable_statement_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_PROMOTED_NAMES[0]]
    row["statement"] = "forall n. n = 0"
    with pytest.raises(ValueError, match="immutable parent field 'statement'"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_mutated_constructive_kernel_mode_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_PROMOTED_NAMES[0]]
    row["empty_context_closure"]["kernel_mode"] = "classical"
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundles)


def test_forward_or_missing_declared_dependency_is_rejected(release) -> None:
    parent, rows, documents, bundles = _rows(release)
    row = _by_name(rows)[v18.FLAGSHIP_PROMOTED_NAMES[0]]
    row["dependencies"].append(v18.FLAGSHIP_ROOT_NAMES[-1])
    with pytest.raises(ValueError, match="immutable parent field 'dependencies'"):
        verifier._verify_rows(rows, parent, documents, bundles)
