"""Observation presentation integrity; this is not a proof-admission test."""
from copy import deepcopy
from hashlib import sha256
import gzip
import json
from unittest.mock import patch

import pytest
import sqrt2_power_pilot_results as results
from build_sqrt2_power_campaign import PILOT_MANIFEST_SHA256, pilot_results_files


def test_archive_manifest_is_pinned_and_exact_counts_stay_separate():
    assert sha256((results.ARCHIVE / "manifest.json").read_bytes()).hexdigest() == PILOT_MANIFEST_SHA256
    value, evidence = results.observation_results()
    assert value["counts"]["native_checked_leaves"] == 8
    assert value["counts"]["fully_checked_pilot_contracts"] == 3
    assert value["counts"]["checked_supporting_subleaves"] == 5
    assert value["solver_hits"] == dict(z3=8, eprover=3, vampire=1)
    assert value["IR_parents_closed"] == value["library_admissions"] == 0
    assert value["solver_proof_logs_translated"] == 0
    assert value["independent_lean_checked"] is False
    assert value["model_planning_and_engineering_tokens"] is None
    assert len(value["rows"]) == 12 and len(evidence) == 9


def test_downloads_are_exact_replayed_bytes_not_receipts_only():
    value, evidence = results.observation_results()
    for row in value["rows"]:
        if row["status"] != "fresh_ordinary_HA_checked":
            assert "certificate_path" not in row
            continue
        raw = gzip.decompress(evidence[row["certificate_path"]])
        assert len(raw) == row["certificate_bytes"]
        assert sha256(raw).hexdigest() == row["certificate_sha256"]
        assert json.loads(raw)[0] == "peano-lab-bundle-v1"


@pytest.mark.parametrize("mutation", ("counts", "parent", "certificate", "formula"))
def test_forged_report_cannot_change_coverage_or_replayed_bytes(mutation):
    original = results.archive_member
    raw, compressed = original(results.ARCHIVE, "run/report.json")
    report = deepcopy(json.loads(raw))
    if mutation == "counts":
        report["counts"]["native_checked_leaves"] = 12
    elif mutation == "parent":
        report["IR_parents_closed"] = 1
    elif mutation == "certificate":
        report["rows"][0]["native_only"]["fresh_replay"]["bundle_sha256"] = "0"*64
    else:
        report["rows"][0]["contract"]["source"] = "0=0"
    def altered(archive, name):
        if name == "run/report.json":
            return json.dumps(report).encode(), compressed
        return original(archive, name)
    with patch.object(results, "archive_member", altered), pytest.raises(ValueError):
        results.observation_results()


def test_results_page_does_not_promote_parent_or_solver_hits():
    files = pilot_results_files("test")
    page = files["pilot-results.html"].decode()
    for text in ("0 irrationality parent obligations closed", "P10 unresolved",
                 "not a proof-log translation", "quadratic-field lift remains open",
                 "engineering cost is not measured as zero", "Contract-specific mathematical mutation"):
        assert text in page
    assert 'href="map.html?target=IR045' in page
    assert 'href="evidence/P07-native.json.gz"' in page
    assert 'id="P12"' in page
