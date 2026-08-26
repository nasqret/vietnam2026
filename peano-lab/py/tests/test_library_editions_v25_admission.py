"""Exact additive, fail-closed, original-kernel Alpha-v25 admission audits."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess

import pytest

from peano_lab.library import editions_v24 as parent
from peano_lab.library import editions_v25 as current
from peano_lab.library.alpha_enrollment_v25 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V25_EXPECTED_COUNT,
    FRONTIER_V25_EXPECTED_EDGE_COUNT,
    FRONTIER_V25_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V24_COUNT,
    PARENT_ALPHA_V24_ENROLLMENT_SHA256,
    PARENT_ALPHA_V24_IDENTITY_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v25_enrollment,
)
from peano_lab.library.campaign_breakthrough_layer_closure import (
    BREAKTHROUGH_LAYER_ARTIFACT_FILENAME,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_BYTES,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256,
)


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / BREAKTHROUGH_LAYER_ARTIFACT_FILENAME
)


def test_immutable_alpha_v24_parent_and_stable_are_preserved() -> None:
    assert len(parent.ALPHA_ENTRIES) == PARENT_ALPHA_V24_COUNT == 2_008
    assert parent.ALPHA_V24_ENROLLMENT_SHA256 == PARENT_ALPHA_V24_ENROLLMENT_SHA256
    assert parent.ALPHA_V24_IDENTITY_SHA256 == PARENT_ALPHA_V24_IDENTITY_SHA256
    assert current.ALPHA_ENTRIES[:PARENT_ALPHA_V24_COUNT] == parent.ALPHA_ENTRIES
    assert all(
        newer is older
        for newer, older in zip(current.ALPHA_ENTRIES, parent.ALPHA_ENTRIES, strict=False)
    )
    assert current.STABLE_EDITION is parent.STABLE_EDITION
    assert len(current.STABLE_SPECS) == 432


def test_frozen_frontier_is_nonempty_dependency_ordered_and_checked() -> None:
    enrollment = alpha_v25_enrollment()
    assert FRONTIER_V25_EXPECTED_COUNT > 0
    assert len(enrollment.frontier_specs) == FRONTIER_V25_EXPECTED_COUNT
    assert all(count > 0 for count in EXPECTED_CAMPAIGN_COUNTS.values())
    assert Counter(enrollment.campaign_by_name.values()) == EXPECTED_CAMPAIGN_COUNTS
    assert sum(len(row.dependencies) for row in enrollment.frontier_specs) == (
        FRONTIER_V25_EXPECTED_EDGE_COUNT
    )
    assert sha256("\n".join(row.name for row in enrollment.frontier_specs).encode()).hexdigest() == (
        FRONTIER_V25_EXPECTED_NAMES_SHA256
    )
    available = {row.spec.name for row in parent.ALPHA_ENTRIES}
    for row in enrollment.frontier_specs:
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert row.script
        assert current.ALPHA_EDITION.by_name[row.name].checked_use
        available.add(row.name)


@pytest.mark.parametrize("name,expected", ROOT_STATEMENT_SHA256.items())
def test_frozen_root_statement_is_exact(name: str, expected: str) -> None:
    row = current.ALPHA_EDITION.by_name[name]
    assert row.checked_use
    assert sha256(row.spec.statement.encode()).hexdigest() == expected


def test_full_edition_seals_and_immutable_quadratic_corpus() -> None:
    assert len(current.ALPHA_ENTRIES) == current.EXPECTED_ALPHA_V25_COUNT
    assert len(current.ALPHA_CHECKED_SPECS) == current.EXPECTED_ALPHA_V25_CHECKED_USE_COUNT
    assert current.ALPHA_EDITION.edge_count == current.EXPECTED_ALPHA_V25_EDGE_COUNT
    assert current.ALPHA_EDITION.layer_count == current.EXPECTED_ALPHA_V25_LAYER_COUNT
    assert current.ALPHA_V25_ENROLLMENT_SHA256 == current.EXPECTED_ALPHA_V25_ENROLLMENT_SHA256
    assert current.ALPHA_V25_IDENTITY_SHA256 == current.EXPECTED_ALPHA_V25_IDENTITY_SHA256
    corpus = REPOSITORY / "book/_static/pa-proof-explorer/api/corpus.json"
    assert sha256(corpus.read_bytes()).hexdigest() == (
        "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
    )


def test_exact_self_contained_artifact_passes_independent_lean() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_BYTES > 0
    assert sha256(payload).hexdigest() == EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256
    verifier = REPOSITORY.parent / "peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify"
    result = subprocess.run(
        [str(verifier), str(ARTIFACT)],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("ACCEPT\t")
    assert f"nodes={EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT}" in result.stdout


def test_new_alpha_theorems_never_leak_into_stable() -> None:
    stable_names = {row.name for row in current.STABLE_SPECS}
    assert stable_names.isdisjoint(current.FRONTIER_NEW_NAMES)
    for name in current.FRONTIER_NEW_NAMES:
        assert current.entry(name, edition="stable") is None
