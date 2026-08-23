"""Fast fail-closed mutation audit for the additive Alpha-v15 verifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "verify_peano_library_channels_v15_under_test",
    ROOT / "scripts" / "verify_peano_library_channels_v15.py",
)
assert _SPEC is not None and _SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = VERIFIER
_SPEC.loader.exec_module(VERIFIER)
BUILDER = VERIFIER.builder


@pytest.fixture(scope="module")
def release() -> dict[str, Any]:
    catalog = VERIFIER._load(BUILDER.DEFAULT_ALPHA)
    return {
        "catalog": catalog,
        "rows": catalog["theorems"][BUILDER.EXPECTED_PARENT_COUNT :],
        "documents": {
            document["path"]: document
            for document in catalog["evidence_documents"]
            if type(document) is dict
        },
        "metrics": VERIFIER._load(BUILDER.DEFAULT_ALPHA_METRICS),
        "channels": VERIFIER._load(BUILDER.DEFAULT_CHANNELS),
        "parent_channels": VERIFIER._load(BUILDER.PARENT_CHANNELS),
    }


def _row(release: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = list(release["rows"])
    row = dict(rows[0])
    rows[0] = row
    return rows, row


def test_actual_all_117_body_receipts_validate_without_replay(
    release: dict[str, Any],
) -> None:
    receipts = VERIFIER._verify_frontier_rows(
        release["rows"], release["documents"]
    )
    assert len(receipts) == 117
    assert set(VERIFIER.FRONTIER_V15_ROOT_NAMES) <= receipts.keys()
    assert "bounded_euler_criterion_complete" in receipts
    assert "bounded_gauss_lemma_complete" in receipts


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("checked_use", True),
        ("evidence_status", "alpha_closed"),
        ("evidence_status", "stable_closed"),
        ("membership", "stable"),
        ("empty_context_closure", {"fabricated": True}),
        ("body_checked", False),
        ("proof_tag", "fabricated"),
        ("enrollment_origin", "stable"),
        ("provenance", ["stable"]),
        ("enrollment_index", -1),
    ),
)
def test_rejects_fabricated_checked_or_stable_authority(
    release: dict[str, Any], field: str, value: Any
) -> None:
    rows, first = _row(release)
    first[field] = value
    with pytest.raises(ValueError, match="body-only evidence boundary"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("statement", "forall n. n = S(n)"),
        ("dependencies", []),
        ("script", ["DNE"]),
        ("summary", "fabricated"),
        ("statement_sha256", "0" * 64),
        ("dependencies_sha256", "0" * 64),
        ("script_sha256", "0" * 64),
        ("summary_sha256", "0" * 64),
        ("logical_spec_sha256", "0" * 64),
    ),
)
def test_rejects_changed_exact_source_specification(
    release: dict[str, Any], field: str, value: Any
) -> None:
    rows, first = _row(release)
    first[field] = value
    with pytest.raises(ValueError, match="exact source specification"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("name", "fabricated", "inconsistent body receipt"),
        ("dependency_count", -1, "inconsistent body receipt"),
        ("command_count", -1, "inconsistent body receipt"),
        ("dne_command_count", 1, "inconsistent body receipt"),
        ("status", "alpha_closed", "inconsistent body receipt"),
        ("proof_nodes", "1", "nonnumeric proof metric"),
        ("proof_depth", None, "nonnumeric proof metric"),
        ("proof_objects", "1", "nonnumeric proof metric"),
        ("proof_edges", None, "nonnumeric proof metric"),
        ("proof_nodes", 0, "no actual proof object"),
        ("proof_objects", 0, "no actual proof object"),
    ),
)
def test_rejects_fabricated_actual_proof_receipt(
    release: dict[str, Any], field: str, value: Any, message: str
) -> None:
    rows, first = _row(release)
    receipt = dict(first["body_receipt"])
    receipt[field] = value
    first["body_receipt"] = receipt
    with pytest.raises(ValueError, match=message):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


def test_rejects_missing_actual_receipt(release: dict[str, Any]) -> None:
    rows, first = _row(release)
    first["body_receipt"] = None
    with pytest.raises(ValueError, match="no actual dependency-curried receipt"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize("mutation", ("campaign", "source", "link", "bundle"))
def test_rejects_broken_source_campaign_or_evidence_bundle(
    release: dict[str, Any], mutation: str
) -> None:
    rows, first = _row(release)
    if mutation == "campaign":
        first["frontier_campaign"] = "fabricated"
        message = "campaign partition"
    elif mutation == "source":
        source = dict(first["source"])
        source["sha256"] = "0" * 64
        first["source"] = source
        message = "candidate source binding"
    elif mutation == "link":
        links = list(first["evidence_links"])
        link = dict(links[0])
        link["document_sha256"] = "0" * 64
        links[0] = link
        first["evidence_links"] = links
        message = "invalid evidence link"
    else:
        first["frontier_v15_evidence_bundle_sha256"] = "0" * 64
        message = "actual-proof evidence bundle"
    with pytest.raises(ValueError, match=message):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


@pytest.mark.parametrize("mutation", ("reordered", "missing", "renamed"))
def test_rejects_incomplete_or_reordered_minimal_closure(
    release: dict[str, Any], mutation: str
) -> None:
    rows = list(release["rows"])
    if mutation == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "missing":
        rows.pop()
    else:
        first = dict(rows[0])
        first["name"] = "fabricated"
        rows[0] = first
    with pytest.raises(ValueError, match="minimal topological"):
        VERIFIER._verify_frontier_rows(rows, release["documents"])


def _mock_release(
    monkeypatch: pytest.MonkeyPatch,
    release: dict[str, Any],
    *,
    catalog: dict[str, Any] | None = None,
    channels: dict[str, Any] | None = None,
) -> None:
    parent = {
        "schema": "peano-library-alpha-snapshot-v14",
        "theorem_count": BUILDER.EXPECTED_PARENT_COUNT,
        "theorems": release["catalog"]["theorems"][: BUILDER.EXPECTED_PARENT_COUNT],
        "ordered_enrollment_root_sha256": BUILDER.PARENT_ALPHA_V14_ENROLLMENT_SHA256,
        "edition_identity_sha256": BUILDER.PARENT_ALPHA_V14_IDENTITY_SHA256,
    }
    values = {
        BUILDER.PARENT_ALPHA: parent,
        BUILDER.DEFAULT_ALPHA: release["catalog"] if catalog is None else catalog,
        BUILDER.DEFAULT_ALPHA_METRICS: release["metrics"],
        BUILDER.DEFAULT_CHANNELS: release["channels"] if channels is None else channels,
        BUILDER.PARENT_CHANNELS: release["parent_channels"],
    }
    monkeypatch.setattr(VERIFIER, "_load", lambda path: values[path])
    monkeypatch.setattr(BUILDER, "_validate_parent", lambda _parent: None)


def test_rejects_mutated_v14_parent_prefix(
    monkeypatch: pytest.MonkeyPatch, release: dict[str, Any]
) -> None:
    catalog = dict(release["catalog"])
    rows = list(catalog["theorems"])
    first = dict(rows[0])
    first["statement"] = "fabricated"
    rows[0] = first
    catalog["theorems"] = rows
    _mock_release(monkeypatch, release, catalog=catalog)
    with pytest.raises(ValueError, match="exact 1,556-row v14 ledger"):
        VERIFIER.verify()


@pytest.mark.parametrize("mutation", ("stable", "default", "root"))
def test_rejects_stable_pointer_and_default_channel_without_body_replay(
    monkeypatch: pytest.MonkeyPatch, release: dict[str, Any], mutation: str
) -> None:
    channels = dict(release["channels"])
    if mutation == "stable":
        pointers = dict(channels["channels"])
        stable = dict(pointers["stable"])
        stable["theorem_count"] = -1
        pointers["stable"] = stable
        channels["channels"] = pointers
    elif mutation == "default":
        channels["default_channel"] = "alpha"
    else:
        channels["channel_pointer_root_sha256"] = "0" * 64
    _mock_release(monkeypatch, release, channels=channels)
    monkeypatch.setattr(
        VERIFIER, "_verify_frontier_rows", lambda _rows, _documents: {}
    )

    def reject_replay(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("channel mutation reached proof-body replay")

    monkeypatch.setattr(VERIFIER, "replay_candidate_bodies", reject_replay)
    with pytest.raises(ValueError, match="sealed Stable pointer or default channel"):
        VERIFIER.verify()
