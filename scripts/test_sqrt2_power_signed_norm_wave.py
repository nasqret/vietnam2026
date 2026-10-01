"""Exact SN001 archival/presentation bindings, separate from proof production."""
from hashlib import sha256
import json
import sys

import pytest

from check_sqrt2_power_fresh_lean import exact_bundle
from index_sqrt2_power_wave import BASE, index_entry
from run_sqrt2_power_wave import target_for
from sqrt2_power_binary_dag import formula_sha256
from sqrt2_power_signed_norm import SIGNED_NORM_TARGET_SHA256
from sqrt2_power_wave_page import signed_norm_files
from sqrt2_power_wave_results import wave_results


def observation_view():
    return wave_results(dict(schema="sqrt2-power-wave-evidence-index-v1",
        reports=[index_entry("shared-wave-signed-norm-v1", "SN001")],
        lean_reports=[index_entry("fresh-lean-signed-norm-v1")]))


def test_signed_target_is_bound_separately_from_natural_core():
    assert formula_sha256(target_for("SN001")) == SIGNED_NORM_TARGET_SHA256
    assert target_for("SN001") != target_for("IR016")
    assert "peano_lab.library.theorems" not in sys.modules


def test_same_exact_signed_bundle_passed_fresh_HA_and_Lean():
    payload, intake = exact_bundle(BASE / "shared-wave-signed-norm-v1")
    view, files = observation_view()
    row, = view["rows"]
    assert row["independent_lean_checked"]
    assert row["target_ast_sha256"] == intake["target_ast_sha256"] == SIGNED_NORM_TARGET_SHA256
    assert sha256(payload).hexdigest() == row["bundle_sha256"]
    assert row["scope"] == "supporting_leaf"
    assert view["counts"]["unique_HA_statements"] == 1
    assert view["counts"]["unique_Lean_checked_statements"] == 1
    assert view["IR_parents_closed"] == view["library_admissions"] == 0
    assert row["proof_download"] in files


def test_named_statement_reuses_exact_existing_definition():
    view, _ = observation_view()
    row, = view["rows"]
    def plain_page(title, body, revision, **_kwargs):
        return (title+body).encode()
    files = signed_norm_files(row, plain_page, "test")
    data = json.loads(files["api/reused-signed-square-definition.json"])
    assert data["id"] == "ND0157" and data["name"] == "SignedDifferenceSquare"
    assert data["parameters"] == ["p", "n", "s"] and data["used_by"] == ["SN001"]
    assert data["authority"] == "same_existing_definition_reused_not_new_admission"
    page = files["checked/SN001.html"].decode()
    assert 'href="../reused-definitions/ND0157.html"' in page
    assert "full irrationality argument remain open" in page
    assert "Fresh HA and independently compiled Lean checks" in page


def test_natural_core_receipt_cannot_label_signed_statement():
    view, _ = observation_view()
    row, = view["rows"]
    with pytest.raises(ValueError, match="named signed norm bridge"):
        signed_norm_files(dict(row, target_ast_sha256=formula_sha256(target_for("IR016"))),
            lambda *_args, **_kwargs: b"", "test")
