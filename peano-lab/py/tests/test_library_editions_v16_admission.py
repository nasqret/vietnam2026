"""Immutable Alpha-v16 quadratic-reciprocity closure and authority audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library import editions_v15 as v15
from peano_lab.library import editions_v16 as v16
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME


REPOSITORY = Path(__file__).resolve().parents[3]
CATALOG = REPOSITORY / "artifacts/peano-library/alpha/catalog-v16.json"
CHANNELS = REPOSITORY / "artifacts/peano-library/channels-v16.json"


def test_v16_preserves_exact_parent_ledger_and_stable() -> None:
    assert len(v15.ALPHA_ENTRIES) == len(v16.ALPHA_ENTRIES) == 1_673
    assert v16.ALPHA_SPECS == v15.ALPHA_SPECS
    assert v16.STABLE_EDITION is v15.STABLE_EDITION
    assert v16.STABLE_ENTRIES is v15.STABLE_ENTRIES
    assert v16.STABLE_SPECS is v15.STABLE_SPECS
    assert len(v16.STABLE_SPECS) == 432
    assert v16.ALPHA_V16_ENROLLMENT_SHA256 == v15.ALPHA_V15_ENROLLMENT_SHA256
    assert v16.ALPHA_V16_IDENTITY_SHA256 == (
        "3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10"
    )
    promoted = frozenset(v16.QR_PROMOTED_NAMES)
    for older, newer in zip(v15.ALPHA_ENTRIES, v16.ALPHA_ENTRIES, strict=True):
        if older.spec.name in promoted:
            assert not older.checked_use
            assert older.enrollment_origin is v16.EnrollmentOrigin.QR
            assert newer == replace(older, evidence=v16.EvidenceStatus.ALPHA_CLOSED)
        else:
            assert newer is older


def test_v16_exact_evidence_transition_and_topology() -> None:
    assert Counter(entry.evidence.value for entry in v16.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 453,
        "body_checked": 788,
    }
    assert len(v16.ALPHA_CHECKED_SPECS) == 885
    assert len(v16.QR_PROMOTED_NAMES) == 315
    assert v16.QR_PROMOTED_NAMES[-1] == QR_ROOT_NAME
    assert sha256("\n".join(v16.QR_PROMOTED_NAMES).encode()).hexdigest() == (
        "aba2d7a192b6f1c11fbafbed1001bf592ca9ed8f5bee7ac3f1de863dd870a80e"
    )
    assert (v16.ALPHA_EDITION.edge_count, v16.ALPHA_EDITION.layer_count) == (
        5_615,
        53,
    )
    checked = {spec.name for spec in v16.ALPHA_CHECKED_SPECS}
    assert sum(len(spec.dependencies) for spec in v16.ALPHA_CHECKED_SPECS) == 2_641
    assert all(set(spec.dependencies) <= checked for spec in v16.ALPHA_CHECKED_SPECS)


def test_v16_root_is_checked_alpha_only_and_stable_unchanged() -> None:
    root = v16.entry(QR_ROOT_NAME, edition="alpha")
    assert root is not None
    assert root.evidence is v16.EvidenceStatus.ALPHA_CLOSED
    assert root.checked_use
    assert v16.entry(QR_ROOT_NAME, edition="stable") is None
    assert v16.edition() is v15.STABLE_EDITION


@pytest.mark.parametrize(
    "name",
    [
        "bertrand_strict",
        "lucas_theorem",
        "four_square_lagrange",
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
    ],
)
def test_v16_does_not_promote_unrelated_body_only_roots(name: str) -> None:
    row = v16.entry(name, edition="alpha")
    assert row is not None
    assert row.evidence is v16.EvidenceStatus.BODY_CHECKED
    assert not row.checked_use
    with pytest.raises(v16.EditionV16ReplayError, match="checked theorem use"):
        v16.replay(name, edition="alpha")


def test_v16_promoted_use_checks_actual_original_kernel_proof() -> None:
    actual = v16.replay(v16.QR_PROMOTED_NAMES[0], edition="alpha")
    assert actual.spec.name == v16.QR_PROMOTED_NAMES[0]
    assert actual.proof_nodes == 91
    assert check((), actual.certificate, actual.formula)
    bundle, receipt = v16._checked_qr_bundle()
    assert len(bundle.nodes) == receipt.node_count == receipt.kernel_calls == 557
    assert receipt.dependency_edges == 1_787
    assert receipt.total_body_nodes == 41_722


def test_v16_missing_actual_proof_artifact_fails_closed(tmp_path: Path) -> None:
    v16.set_qr_bundle_source(tmp_path / "missing-proof-bundle.json")
    try:
        with pytest.raises(v16.EditionV16ReplayError, match="unavailable"):
            v16.replay(v16.QR_PROMOTED_NAMES[0], edition="alpha")
    finally:
        v16.set_qr_bundle_source(None)


def test_v16_mutated_actual_proof_artifact_fails_closed(tmp_path: Path) -> None:
    source = REPOSITORY / (
        "research/arithmetic-library/artifacts/"
        "quadratic-reciprocity-proof-bundle-v1.json"
    )
    destination = tmp_path / "mutated-proof-bundle.json"
    original = source.read_bytes()
    destination.write_bytes(original[:-1] + b" ")
    v16.set_qr_bundle_source(destination)
    try:
        with pytest.raises(v16.EditionV16ReplayError, match="frozen provenance"):
            v16.replay(v16.QR_PROMOTED_NAMES[0], edition="alpha")
    finally:
        v16.set_qr_bundle_source(None)


def test_v16_sealed_artifacts_preserve_stable_and_promote_exact_root() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    channels = json.loads(CHANNELS.read_text(encoding="utf-8"))
    parent = json.loads(
        (REPOSITORY / "artifacts/peano-library/alpha/catalog-v15.json").read_text(
            encoding="utf-8"
        )
    )
    parent_channels = json.loads(
        (REPOSITORY / "artifacts/peano-library/channels-v15.json").read_text(
            encoding="utf-8"
        )
    )
    assert catalog["schema"] == "peano-library-alpha-snapshot-v16"
    assert catalog["theorem_count"] == 1_673
    assert catalog["checked_use_count"] == 885
    assert catalog["edition_identity_sha256"] == v16.ALPHA_V16_IDENTITY_SHA256
    assert catalog["ordered_enrollment_root_sha256"] == (
        parent["ordered_enrollment_root_sha256"]
    )
    assert channels["default_channel"] == "stable"
    assert channels["channels"]["stable"] == parent_channels["channels"]["stable"]
    assert channels["channels"]["alpha"]["checked_use_count"] == 885
    rows = {row["name"]: row for row in catalog["theorems"]}
    root = rows[QR_ROOT_NAME]
    assert root["evidence_status"] == "alpha_closed"
    assert root["checked_use"] is True
    assert root["empty_context_closure"]["bundle_node_id"] == 556
    assert root["empty_context_closure"]["certificate_sha256"] == (
        v16.EXPECTED_QR_BUNDLE_SHA256
    )
