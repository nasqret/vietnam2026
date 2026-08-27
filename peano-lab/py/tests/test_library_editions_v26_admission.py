"""Exact additive, fail-closed, original-kernel Alpha-v26 admission audits."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess

import pytest

from peano_lab.library import editions_v25 as parent
from peano_lab.library import editions_v26 as current
from peano_lab.library.alpha_enrollment_v26 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V26_EXPECTED_COUNT,
    FRONTIER_V26_EXPECTED_EDGE_COUNT,
    FRONTIER_V26_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V25_COUNT,
    PARENT_ALPHA_V25_ENROLLMENT_SHA256,
    PARENT_ALPHA_V25_IDENTITY_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v26_enrollment,
)
from peano_lab.library.campaign_first_wave_closure import (
    FIRST_WAVE_ARTIFACT_FILENAME,
    EXPECTED_FIRST_WAVE_BUNDLE_BYTES,
    EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT,
    EXPECTED_FIRST_WAVE_BUNDLE_SHA256,
)


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / FIRST_WAVE_ARTIFACT_FILENAME
)


def test_immutable_alpha_v25_parent_and_stable_are_preserved() -> None:
    assert len(parent.ALPHA_ENTRIES) == PARENT_ALPHA_V25_COUNT == 2_080
    assert parent.ALPHA_V25_ENROLLMENT_SHA256 == PARENT_ALPHA_V25_ENROLLMENT_SHA256
    assert parent.ALPHA_V25_IDENTITY_SHA256 == PARENT_ALPHA_V25_IDENTITY_SHA256
    assert current.ALPHA_ENTRIES[:PARENT_ALPHA_V25_COUNT] == parent.ALPHA_ENTRIES
    assert all(
        newer is older
        for newer, older in zip(current.ALPHA_ENTRIES, parent.ALPHA_ENTRIES, strict=False)
    )
    assert current.STABLE_EDITION is parent.STABLE_EDITION
    assert len(current.STABLE_SPECS) == 432


def test_frozen_frontier_is_nonempty_dependency_ordered_and_checked() -> None:
    enrollment = alpha_v26_enrollment()
    assert FRONTIER_V26_EXPECTED_COUNT > 0
    assert len(enrollment.frontier_specs) == FRONTIER_V26_EXPECTED_COUNT
    assert all(count > 0 for count in EXPECTED_CAMPAIGN_COUNTS.values())
    assert Counter(enrollment.campaign_by_name.values()) == EXPECTED_CAMPAIGN_COUNTS
    assert sum(len(row.dependencies) for row in enrollment.frontier_specs) == (
        FRONTIER_V26_EXPECTED_EDGE_COUNT
    )
    assert sha256("\n".join(row.name for row in enrollment.frontier_specs).encode()).hexdigest() == (
        FRONTIER_V26_EXPECTED_NAMES_SHA256
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
    assert len(current.ALPHA_ENTRIES) == current.EXPECTED_ALPHA_V26_COUNT
    assert len(current.ALPHA_CHECKED_SPECS) == current.EXPECTED_ALPHA_V26_CHECKED_USE_COUNT
    assert current.ALPHA_EDITION.edge_count == current.EXPECTED_ALPHA_V26_EDGE_COUNT
    assert current.ALPHA_EDITION.layer_count == current.EXPECTED_ALPHA_V26_LAYER_COUNT
    assert current.ALPHA_V26_ENROLLMENT_SHA256 == current.EXPECTED_ALPHA_V26_ENROLLMENT_SHA256
    assert current.ALPHA_V26_IDENTITY_SHA256 == current.EXPECTED_ALPHA_V26_IDENTITY_SHA256
    corpus = REPOSITORY / "book/_static/pa-proof-explorer/api/corpus.json"
    assert sha256(corpus.read_bytes()).hexdigest() == (
        "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
    )


def test_exact_self_contained_artifact_passes_independent_lean() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == EXPECTED_FIRST_WAVE_BUNDLE_BYTES > 0
    assert sha256(payload).hexdigest() == EXPECTED_FIRST_WAVE_BUNDLE_SHA256
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
    assert f"nodes={EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT}" in result.stdout


def test_new_alpha_theorems_never_leak_into_stable() -> None:
    stable_names = {row.name for row in current.STABLE_SPECS}
    assert stable_names.isdisjoint(current.FRONTIER_NEW_NAMES)
    for name in current.FRONTIER_NEW_NAMES:
        assert current.entry(name, edition="stable") is None

@pytest.fixture(autouse=True)
def _clear_first_wave_sources():
    current.set_first_wave_bundle_source(None)
    yield
    current.set_first_wave_bundle_source(None)


def test_exact_first_wave_bundle_authenticates_each_current_frontier_row() -> None:
    bundle, receipt, positions = current.checked_first_wave_bundle()
    assert set(current.FRONTIER_NEW_NAMES) <= positions.keys()
    assert receipt.node_count == len(bundle.nodes)
    assert receipt.kernel_calls == len(bundle.nodes)
    from peano_lab.library.theorems import _closed_formula
    for name in current.FRONTIER_NEW_NAMES:
        row = current.entry(name, edition="alpha")
        assert row is not None and row.checked_use
        node = bundle.nodes[positions[name]]
        assert node.target == _closed_formula(row.spec.statement)
        assert node.dependencies == tuple(positions[dependency] for dependency in row.spec.dependencies)


def test_missing_first_wave_artifact_fails_closed(tmp_path: Path) -> None:
    current.set_first_wave_bundle_source(tmp_path / "missing.json")
    with pytest.raises(current.EditionV26ReplayError, match="unavailable"):
        current.checked_first_wave_bundle()


@pytest.mark.parametrize("mutation", ("truncate", "alter"))
def test_changed_first_wave_artifact_fails_before_kernel_use(tmp_path: Path, mutation: str) -> None:
    payload = ARTIFACT.read_bytes()
    corrupted = payload[:-1] if mutation == "truncate" else bytes([payload[0] ^ 1]) + payload[1:]
    source = tmp_path / "changed.json"
    source.write_bytes(corrupted)
    current.set_first_wave_bundle_source(source)
    with pytest.raises(current.EditionV26ReplayError, match="frozen provenance"):
        current.checked_first_wave_bundle()


@pytest.mark.parametrize("source", (0, object(), b"artifact.json"))
def test_nonpath_artifact_source_is_rejected(source: object) -> None:
    with pytest.raises(current.EditionV26ReplayError, match="filesystem path"):
        current.set_first_wave_bundle_source(source)


def test_unsealed_proof_metadata_never_authorizes_checked_use(monkeypatch) -> None:
    from types import SimpleNamespace
    monkeypatch.setattr(current, "_first_wave_module", lambda: SimpleNamespace(
        EXPECTED_FIRST_WAVE_BUNDLE_BYTES=0,
        EXPECTED_FIRST_WAVE_BUNDLE_SHA256="",
        EXPECTED_FIRST_WAVE_BUNDLE_BODY_PROOF_NODES=0,
    ))
    with pytest.raises(current.EditionV26ReplayError, match="frozen provenance"):
        current.checked_first_wave_bundle()


def test_inherited_replay_still_delegates_to_the_immutable_parent(monkeypatch) -> None:
    sentinel = object()
    calls = []
    def inherited(name, *, edition):
        calls.append((name, edition))
        return sentinel
    monkeypatch.setattr(parent, "replay", inherited)
    assert current.replay("zero_add", edition="stable") is sentinel
    assert calls == [("zero_add", current.EditionName.STABLE)]


def test_new_classification_cannot_be_replayed_with_stable_authority() -> None:
    with pytest.raises(current.EditionV26ReplayError, match="unknown stable"):
        current.replay("pythagorean_positive_primitive_classification", edition="stable")

