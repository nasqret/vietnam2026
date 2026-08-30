"""Mutation gates for immutable Alpha-v16 actual-proof evidence promotion."""

from __future__ import annotations

from copy import deepcopy

import pytest

import build_peano_library_channels_v16 as builder
import verify_peano_library_channels_v16 as verifier
from peano_lab.library import editions_v16 as v16
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME


@pytest.fixture(scope="module")
def release():
    parent = verifier._load(builder.PARENT_ALPHA)
    catalog = verifier._load(builder.DEFAULT_ALPHA)
    documents = verifier._documents(catalog)
    bundle, receipt = v16._checked_qr_bundle()
    assert receipt.kernel_calls == 557
    return parent["theorems"], catalog["theorems"], documents, bundle


def _rows(release):
    parent, rows, documents, bundle = release
    return parent, deepcopy(rows), documents, bundle


def _by_name(rows):
    return {row["name"]: row for row in rows}


def test_actual_dependency_closed_release_is_accepted(release) -> None:
    parent, rows, documents, bundle = release
    verifier._verify_rows(rows, parent, documents, bundle)


def test_unrelated_body_only_false_promotion_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)["bertrand_strict"]
    row["checked_use"] = True
    row["evidence_status"] = "alpha_closed"
    with pytest.raises(ValueError, match="unrelated immutable parent row"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_missing_qr_root_promotion_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    parent_by_name = _by_name(parent)
    index = next(i for i, row in enumerate(rows) if row["name"] == QR_ROOT_NAME)
    rows[index] = deepcopy(parent_by_name[QR_ROOT_NAME])
    with pytest.raises(ValueError, match="immutable field set"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_mutated_actual_proof_node_binding_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[QR_ROOT_NAME]
    row["empty_context_closure"]["bundle_node_id"] = 555
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_mutated_parent_row_provenance_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[v16.QR_PROMOTED_NAMES[0]]
    row["alpha_v16_promotion"]["parent_row_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="immutable parent transition"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_mutated_historical_evidence_link_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[v16.QR_PROMOTED_NAMES[0]]
    row["evidence_links"][0]["role"] = "forged"
    with pytest.raises(ValueError, match="immutable historical links"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_missing_actual_proof_evidence_link_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[v16.QR_PROMOTED_NAMES[0]]
    row["evidence_links"].pop()
    with pytest.raises(ValueError, match="immutable historical links"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_mutated_immutable_statement_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[v16.QR_PROMOTED_NAMES[0]]
    row["statement"] = "forall n. n = 0"
    with pytest.raises(ValueError, match="immutable parent field 'statement'"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_mutated_constructive_kernel_mode_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[v16.QR_PROMOTED_NAMES[0]]
    row["empty_context_closure"]["kernel_mode"] = "classical"
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, bundle)


def test_forward_or_missing_declared_dependency_is_rejected(release) -> None:
    parent, rows, documents, bundle = _rows(release)
    row = _by_name(rows)[v16.QR_PROMOTED_NAMES[0]]
    row["dependencies"].append(QR_ROOT_NAME)
    with pytest.raises(ValueError, match="immutable parent field 'dependencies'"):
        verifier._verify_rows(rows, parent, documents, bundle)
