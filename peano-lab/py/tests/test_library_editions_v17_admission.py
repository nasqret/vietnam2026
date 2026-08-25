"""Immutable Alpha-v17 supplementary-law closure and checked-use audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library import editions_v16 as v16
from peano_lab.library import editions_v17 as v17


REPOSITORY = Path(__file__).resolve().parents[3]
CATALOG = REPOSITORY / "artifacts/peano-library/alpha/catalog-v17.json"
CHANNELS = REPOSITORY / "artifacts/peano-library/channels-v17.json"


def test_v17_preserves_exact_parent_ledger_and_stable() -> None:
    assert len(v16.ALPHA_ENTRIES) == len(v17.ALPHA_ENTRIES) == 1_673
    assert v17.ALPHA_SPECS == v16.ALPHA_SPECS
    assert v17.STABLE_EDITION is v16.STABLE_EDITION
    assert v17.STABLE_ENTRIES is v16.STABLE_ENTRIES
    assert v17.STABLE_SPECS is v16.STABLE_SPECS
    assert len(v17.STABLE_SPECS) == 432
    assert v17.ALPHA_V17_ENROLLMENT_SHA256 == v16.ALPHA_V16_ENROLLMENT_SHA256
    assert v17.ALPHA_V17_IDENTITY_SHA256 == (
        "db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4"
    )
    promoted = frozenset(v17.SUPPLEMENTARY_PROMOTED_NAMES)
    for older, newer in zip(v16.ALPHA_ENTRIES, v17.ALPHA_ENTRIES, strict=True):
        if older.spec.name in promoted:
            assert not older.checked_use
            assert newer == replace(older, evidence=v17.EvidenceStatus.ALPHA_CLOSED)
        else:
            assert newer is older


def test_v17_exact_evidence_transition_and_topology() -> None:
    assert Counter(item.evidence.value for item in v17.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 484,
        "body_checked": 757,
    }
    assert len(v17.ALPHA_CHECKED_SPECS) == 916
    assert len(v17.SUPPLEMENTARY_PROMOTED_NAMES) == 31
    assert sha256("\n".join(v17.SUPPLEMENTARY_PROMOTED_NAMES).encode()).hexdigest() == (
        "21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7"
    )
    assert (v17.ALPHA_EDITION.edge_count, v17.ALPHA_EDITION.layer_count) == (
        5_615,
        53,
    )
    checked = {spec.name for spec in v17.ALPHA_CHECKED_SPECS}
    assert sum(len(spec.dependencies) for spec in v17.ALPHA_CHECKED_SPECS) == 2_743
    assert all(set(spec.dependencies) <= checked for spec in v17.ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize("name", v17.SUPPLEMENTARY_ROOT_NAMES)
def test_v17_both_supplementary_roots_are_checked_alpha_only(name: str) -> None:
    root = v17.entry(name, edition="alpha")
    assert root is not None
    assert root.evidence is v17.EvidenceStatus.ALPHA_CLOSED
    assert root.checked_use
    assert v17.entry(name, edition="stable") is None
    assert v17.edition() is v16.STABLE_EDITION


@pytest.mark.parametrize(
    "name",
    [
        "bertrand_strict",
        "lucas_theorem",
        "four_square_lagrange",
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
    ],
)
def test_v17_does_not_promote_unrelated_body_only_roots(name: str) -> None:
    row = v17.entry(name, edition="alpha")
    assert row is not None
    assert row.evidence is v17.EvidenceStatus.BODY_CHECKED
    assert not row.checked_use
    with pytest.raises(v17.EditionV17ReplayError, match="checked theorem use"):
        v17.replay(name, edition="alpha")


def test_v17_promoted_use_checks_actual_original_kernel_proof() -> None:
    actual = v17.replay(v17.SUPPLEMENTARY_PROMOTED_NAMES[0], edition="alpha")
    assert actual.spec.name == "eisenstein_initial_segment_indicator_choice"
    assert check((), actual.certificate, actual.formula)
    bundle, receipt = v17._checked_supplementary_bundle()
    assert len(bundle.nodes) == receipt.node_count == receipt.kernel_calls == 438
    assert receipt.dependency_edges == 1_429
    assert receipt.total_body_nodes == 33_173
    assert bundle.root == 437
    assert bundle.nodes[-1].dependencies == (415, 436)


def test_v17_missing_actual_proof_artifact_fails_closed(tmp_path: Path) -> None:
    v17.set_supplementary_bundle_source(tmp_path / "missing-proof-bundle.json")
    try:
        with pytest.raises(v17.EditionV17ReplayError, match="unavailable"):
            v17.replay(v17.SUPPLEMENTARY_PROMOTED_NAMES[0], edition="alpha")
    finally:
        v17.set_supplementary_bundle_source(None)


def test_v17_mutated_actual_proof_artifact_fails_closed(tmp_path: Path) -> None:
    source = REPOSITORY / (
        "research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json"
    )
    destination = tmp_path / "mutated-proof-bundle.json"
    original = source.read_bytes()
    destination.write_bytes(original[:-1] + b" ")
    v17.set_supplementary_bundle_source(destination)
    try:
        with pytest.raises(v17.EditionV17ReplayError, match="frozen provenance"):
            v17.replay(v17.SUPPLEMENTARY_PROMOTED_NAMES[0], edition="alpha")
    finally:
        v17.set_supplementary_bundle_source(None)


def test_v17_sealed_artifacts_preserve_stable_and_promote_both_roots() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    channels = json.loads(CHANNELS.read_text(encoding="utf-8"))
    parent = json.loads(
        (REPOSITORY / "artifacts/peano-library/alpha/catalog-v16.json").read_text(
            encoding="utf-8"
        )
    )
    parent_channels = json.loads(
        (REPOSITORY / "artifacts/peano-library/channels-v16.json").read_text(
            encoding="utf-8"
        )
    )
    assert catalog["schema"] == "peano-library-alpha-snapshot-v17"
    assert catalog["theorem_count"] == 1_673
    assert catalog["checked_use_count"] == 916
    assert catalog["edition_identity_sha256"] == v17.ALPHA_V17_IDENTITY_SHA256
    assert catalog["ordered_enrollment_root_sha256"] == (
        parent["ordered_enrollment_root_sha256"]
    )
    assert channels["default_channel"] == "stable"
    assert channels["channels"]["stable"] == parent_channels["channels"]["stable"]
    assert channels["channels"]["alpha"]["checked_use_count"] == 916
    rows = {row["name"]: row for row in catalog["theorems"]}
    for name, expected_node in zip(v17.SUPPLEMENTARY_ROOT_NAMES, (415, 436), strict=True):
        root = rows[name]
        assert root["evidence_status"] == "alpha_closed"
        assert root["checked_use"] is True
        assert root["empty_context_closure"]["bundle_node_id"] == expected_node
        assert root["empty_context_closure"]["certificate_sha256"] == (
            v17.EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256
        )
