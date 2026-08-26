"""Immutable, fail-closed Alpha-v18 admission of five constructive flagships."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v17 as v17
from peano_lab.library import editions_v18 as v18
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACTS = REPOSITORY / "research/arithmetic-library/artifacts"
PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v17.json": (
        "32acaae2a4dff14862469cf441e527ec1e1efbfff57974c246d603cd7a2e68d9"
    ),
    "artifacts/peano-library/alpha/metrics-v17.json": (
        "26c892fd040b72df05fc4a673ed6cd89a0d3b89dec65f7d0fb3751ed84d2e245"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v17.mmd": (
        "3aaae0b85b1a4f43d55967906678b8b406a6b8be374ee27ae1abf8e749b69962"
    ),
    "artifacts/peano-library/channels-v17.json": (
        "b43c622de353f22743c06ddacb9ff85f3ad8c6e40d81dbe296f8cd928377e6cb"
    ),
}
EXPECTED_FAMILY_METRICS = {
    "lucas": (213, 617, 15_103),
    "kummer": (281, 779, 19_062),
    "bertrand": (544, 1_917, None),
    "four_square": (390, 1_187, 31_942),
    "two_square": (517, 1_599, 33_546),
}
FIRST_PROMOTION = {
    label: next(
        name
        for name in v18.FLAGSHIP_PROMOTED_NAMES
        if v18.FLAGSHIP_PROMOTION_OWNERS[name] == label
    )
    for label in v18.FLAGSHIP_BUNDLE_LABELS
}


def test_import_builds_only_inventory_and_never_imports_actual_proof_providers() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from peano_lab.library import editions_v18 as v; "
                "assert all('peano_lab.library.' + contract[0] not in sys.modules "
                "for contract in v._FLAGSHIP_MODULE_CONTRACTS.values()); "
                "assert len(v.ALPHA_CHECKED_SPECS) == 1589"
            ),
        ],
        cwd=REPOSITORY / "peano-lab/py",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def test_exact_parent_theorem_ledger_stable_and_release_artifacts_are_immutable() -> None:
    assert len(v17.ALPHA_ENTRIES) == len(v18.ALPHA_ENTRIES) == 1_673
    assert v18.ALPHA_SPECS == v17.ALPHA_SPECS
    assert v18.STABLE_EDITION is v17.STABLE_EDITION
    assert v18.STABLE_ENTRIES is v17.STABLE_ENTRIES
    assert v18.STABLE_SPECS is v17.STABLE_SPECS
    assert v18.STABLE_RELEASE_ORDER is v17.STABLE_RELEASE_ORDER
    assert len(v18.STABLE_SPECS) == 432
    assert v18.ALPHA_V18_ENROLLMENT_SHA256 == v17.ALPHA_V17_ENROLLMENT_SHA256
    assert v18.ALPHA_V18_ENROLLMENT_SHA256 == (
        "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
    )
    for filename, frozen in PARENT_ARTIFACT_SHA256.items():
        assert sha256((REPOSITORY / filename).read_bytes()).hexdigest() == frozen


def test_only_the_673_genuinely_proved_body_only_rows_change_evidence() -> None:
    promoted = frozenset(v18.FLAGSHIP_PROMOTED_NAMES)
    for older, newer in zip(v17.ALPHA_ENTRIES, v18.ALPHA_ENTRIES, strict=True):
        if older.spec.name in promoted:
            assert older.evidence is v17.EvidenceStatus.BODY_CHECKED
            assert not older.checked_use
            assert older.membership is v17.Membership.ALPHA_ONLY
            assert newer == replace(older, evidence=v18.EvidenceStatus.ALPHA_CLOSED)
        else:
            assert newer is older
    assert len(promoted) == 673
    assert sha256("\n".join(v18.FLAGSHIP_PROMOTED_NAMES).encode()).hexdigest() == (
        "5b6faad95b90a3b3f11e6aea929aefd3cdbf9b5a1f3563e57d8e48f15e9d59e6"
    )
    assert v18.ALPHA_V18_IDENTITY_SHA256 == (
        "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66"
    )
    assert v17.ALPHA_V17_IDENTITY_SHA256 == (
        "db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4"
    )


def test_exact_evidence_partition_topology_and_checked_subgraph_are_sealed() -> None:
    assert Counter(item.evidence.value for item in v18.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 1_157,
        "body_checked": 84,
    }
    assert len(v18.ALPHA_CHECKED_SPECS) == 1_589
    assert len(v18.FLAGSHIP_DEPENDENCY_NAMES) == 1_113
    assert (v18.ALPHA_EDITION.edge_count, v18.ALPHA_EDITION.layer_count) == (
        5_615,
        53,
    )
    checked = {spec.name for spec in v18.ALPHA_CHECKED_SPECS}
    assert sum(len(spec.dependencies) for spec in v18.ALPHA_CHECKED_SPECS) == 5_366
    assert all(set(spec.dependencies) <= checked for spec in v18.ALPHA_CHECKED_SPECS)


def test_exact_five_family_closures_and_first_bundle_ownership_are_sealed() -> None:
    assert v18.FLAGSHIP_BUNDLE_LABELS == (
        "lucas",
        "kummer",
        "bertrand",
        "four_square",
        "two_square",
    )
    assert {
        label: len(v18.FLAGSHIP_BUNDLE_NAMES[label])
        for label in v18.FLAGSHIP_BUNDLE_LABELS
    } == {
        "lucas": 213,
        "kummer": 280,
        "bertrand": 544,
        "four_square": 390,
        "two_square": 517,
    }
    assert Counter(v18.FLAGSHIP_PROMOTION_OWNERS.values()) == {
        "lucas": 74,
        "kummer": 73,
        "bertrand": 241,
        "four_square": 196,
        "two_square": 89,
    }
    for name in v18.FLAGSHIP_PROMOTED_NAMES:
        expected = next(
            label
            for label in v18.FLAGSHIP_BUNDLE_LABELS
            if name in v18.FLAGSHIP_BUNDLE_NAMES[label]
        )
        assert v18.promotion_owner(name) == expected


@pytest.mark.parametrize("name", v18.FLAGSHIP_ROOT_NAMES)
def test_all_six_original_roots_become_checked_alpha_only(name: str) -> None:
    before = v17.entry(name, edition="alpha")
    after = v18.entry(name, edition="alpha")
    assert before is not None
    assert before.evidence is v17.EvidenceStatus.BODY_CHECKED
    assert not before.checked_use
    assert after is not None
    assert after.evidence is v18.EvidenceStatus.ALPHA_CLOSED
    assert after.checked_use
    assert v18.entry(name, edition="stable") is None
    assert v18.edition() is v17.STABLE_EDITION


def test_remaining_84_unproved_rows_never_receive_checked_use() -> None:
    pending = tuple(item for item in v18.ALPHA_ENTRIES if not item.checked_use)
    assert len(pending) == 84
    assert all(item.evidence is v18.EvidenceStatus.BODY_CHECKED for item in pending)
    with pytest.raises(v18.EditionV18ReplayError, match="checked theorem use"):
        v18.replay(pending[0].spec.name, edition="alpha")


@pytest.mark.parametrize("label", v18.FLAGSHIP_BUNDLE_LABELS)
def test_each_bundle_checks_all_actual_bodies_with_the_original_kernel(label: str) -> None:
    bundle, receipt, positions, module = v18.checked_flagship_bundle(label)
    node_count, edge_count, body_nodes = EXPECTED_FAMILY_METRICS[label]
    assert len(bundle.nodes) == receipt.node_count == receipt.kernel_calls == node_count
    assert receipt.dependency_edges == edge_count
    if body_nodes is not None:
        assert receipt.total_body_nodes == body_nodes
    assert receipt.total_body_nodes == getattr(
        module,
        f"EXPECTED_{label.upper()}_BUNDLE_BODY_PROOF_NODES",
    )
    assert tuple(positions) == v18.FLAGSHIP_BUNDLE_NAMES[label]
    assert len(positions) == node_count - int(label == "kummer")
    assert module.__name__ == (
        "peano_lab.library." + v18._FLAGSHIP_MODULE_CONTRACTS[label][0]
    )


def test_kummer_synthetic_conjunction_is_never_admitted_as_a_theorem() -> None:
    bundle, receipt, positions, _module = v18.checked_flagship_bundle("kummer")
    left, right = v18.FLAGSHIP_BUNDLE_ROOTS["kummer"]
    assert (positions[left], positions[right]) == (277, 279)
    assert bundle.root == 280
    assert bundle.root not in positions.values()
    assert bundle.nodes[-1].dependencies == (277, 279)
    assert receipt.target == And(
        _closed_formula(v17.ALPHA_EDITION.by_name[left].spec.statement),
        _closed_formula(v17.ALPHA_EDITION.by_name[right].spec.statement),
    )


@pytest.mark.parametrize("label", v18.FLAGSHIP_BUNDLE_LABELS)
def test_one_actual_promoted_theorem_per_family_replays_in_the_original_kernel(
    label: str,
) -> None:
    name = FIRST_PROMOTION[label]
    checked = v18.replay(name, edition="alpha")
    assert checked.spec is v17.ALPHA_EDITION.by_name[name].spec
    assert v18.promotion_owner(name) == label
    assert check((), checked.certificate, checked.formula)


def test_bertrand_checked_use_conservatively_interns_actual_proof_bodies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = FIRST_PROMOTION["bertrand"]
    original = v18.intern_layered_replay_bodies
    observed: list[tuple[int, int, object]] = []

    def audited(bundle, target, *, limits):
        observed.append((bundle.root, len(bundle.nodes), limits))
        return original(bundle, target, limits=limits)

    monkeypatch.setattr(v18, "intern_layered_replay_bodies", audited)
    v18.replay.cache_clear()
    actual = v18.replay(name, edition="alpha")

    assert len(observed) == 1
    root, node_count, limits = observed[0]
    assert root == v18._FLAGSHIP_BUNDLE_POSITIONS["bertrand"][name]
    assert node_count > 1
    assert limits is v18.DEFAULT_LAYERED_REPLAY_LIMITS
    assert actual.spec is v17.ALPHA_EDITION.by_name[name].spec
    assert actual.proof_nodes <= limits.max_candidate_proof_occurrences


def test_bertrand_proof_interning_failure_or_forgery_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = FIRST_PROMOTION["bertrand"]
    original = v18.intern_layered_replay_bodies

    def rejected(bundle, target, *, limits):
        return None

    monkeypatch.setattr(v18, "intern_layered_replay_bodies", rejected)
    v18.replay.cache_clear()
    with pytest.raises(v18.EditionV18ReplayError, match="rejected conservative"):
        v18.replay(name, edition="alpha")

    def forged(bundle, target, *, limits):
        interned = original(bundle, target, limits=limits)
        first = replace(interned.nodes[0], body=EqRefl(Zero()))
        return replace(interned, nodes=(first, *interned.nodes[1:]))

    monkeypatch.setattr(v18, "intern_layered_replay_bodies", forged)
    v18.replay.cache_clear()
    with pytest.raises(v18.EditionV18ReplayError, match="rejected an interned"):
        v18.replay(name, edition="alpha")
    v18.replay.cache_clear()


@pytest.mark.parametrize("label", v18.FLAGSHIP_BUNDLE_LABELS)
def test_missing_actual_proof_artifact_fails_closed(label: str, tmp_path: Path) -> None:
    name = FIRST_PROMOTION[label]
    v18.set_flagship_bundle_source(label, tmp_path / f"missing-{label}.json")
    try:
        assert v18.entry(name, edition="alpha").checked_use
        with pytest.raises(v18.EditionV18ReplayError, match="unavailable"):
            v18.replay(name, edition="alpha")
    finally:
        v18.set_flagship_bundle_source(label, None)


@pytest.mark.parametrize("label", v18.FLAGSHIP_BUNDLE_LABELS)
def test_mutated_actual_proof_artifact_fails_closed(label: str, tmp_path: Path) -> None:
    name = FIRST_PROMOTION[label]
    source = ARTIFACTS / v18.FLAGSHIP_ARTIFACT_FILENAMES[label]
    original = source.read_bytes()
    mutated = tmp_path / f"mutated-{label}.json"
    mutated.write_bytes(original[:-1] + (b" " if original[-1:] != b" " else b"x"))
    v18.set_flagship_bundle_source(label, mutated)
    try:
        with pytest.raises(v18.EditionV18ReplayError, match="frozen genuine provenance"):
            v18.replay(name, edition="alpha")
    finally:
        v18.set_flagship_bundle_source(label, None)


def test_checked_parent_replay_remains_exactly_delegated_to_alpha_v17() -> None:
    name = v17.SUPPLEMENTARY_PROMOTED_NAMES[0]
    assert v18.replay(name, edition="alpha") is v17.replay(name, edition="alpha")
    stable_name = v17.STABLE_RELEASE_ORDER[0]
    assert v18.replay(stable_name) is v17.replay(stable_name)


@pytest.mark.parametrize("invalid", (None, "", "gauss", 12, ("lucas",)))
def test_unknown_or_noncanonical_proof_family_is_rejected(invalid) -> None:
    with pytest.raises(v18.EditionV18ReplayError, match="unknown exact"):
        v18.checked_flagship_bundle(invalid)


def test_unknown_owner_and_nonfilesystem_source_are_rejected() -> None:
    with pytest.raises(v18.EditionV18ReplayError, match="no newly promoted"):
        v18.promotion_owner("zero_add")
    with pytest.raises(v18.EditionV18ReplayError, match="filesystem path"):
        v18.set_flagship_bundle_source("lucas", object())
