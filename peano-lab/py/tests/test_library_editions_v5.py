"""Runtime and evidence-boundary seals for Bertrand Alpha v5."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v4 as v4
from peano_lab.library import editions_v5 as v5
from peano_lab.library.alpha_enrollment_v5 import (
    BERTRAND_RFC_PATH,
    BERTRAND_V5_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V5_EXPECTED_COUNT,
    BERTRAND_V5_EXPECTED_NAMES,
    BERTRAND_V5_START_INDEX,
    PARENT_ALPHA_V4_COUNT,
    PARENT_ALPHA_V4_ENROLLMENT_SHA256,
    PARENT_ALPHA_V4_IDENTITY_SHA256,
    BertrandV5EnrollmentOrigin,
    alpha_v5_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473"
)
EXPECTED_IDENTITY_SHA256 = (
    "bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "8bb072c21e61ca32525bb14b078a1352255b2e027cc2ce6cd6811d71e794ebb5"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "7d98fa3cd118957c6867f55cf00320c84c5ce096926f253d17feb12b028d5632"
)
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v4.json": (
        "16e2b99de69487e7439521b25ee070b208d6a7436df48f60801d5628a3678f1a"
    ),
    "artifacts/peano-library/alpha/metrics-v4.json": (
        "bec61a932dbcf92715dcaac7440687e7310b8f380f5578746999c3007e1d6dac"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v4.mmd": (
        "9dc4c9531418b3de3def3c827a6b5fac54b12f78661d5a6860c84c08f748d28c"
    ),
    "artifacts/peano-library/channels-v4.json": (
        "cf3cdc6ead4d616b15bcf28b84fca586bc5df84b30125c807fb36a74985bdb76"
    ),
}


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v5_preserves_exact_v4_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V4_COUNT == len(v4.ALPHA_ENTRIES) == 965
    assert PARENT_ALPHA_V4_ENROLLMENT_SHA256 == v4.ALPHA_V4_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V4_IDENTITY_SHA256 == v4.ALPHA_V4_IDENTITY_SHA256
    parent = v5.ALPHA_ENTRIES[:PARENT_ALPHA_V4_COUNT]
    for old, new in zip(v4.ALPHA_ENTRIES, parent, strict=True):
        assert new.spec is old.spec
        assert new.membership is old.membership
        assert new.evidence is old.evidence
        assert new.enrollment_origin.value == old.enrollment_origin.value
        assert tuple(item.value for item in new.provenance) == tuple(
            item.value for item in old.provenance
        )
        assert new.source_module == old.source_module
    assert v5.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v4.STABLE_SPECS)
    assert v5.STABLE_SPECS == v4.STABLE_SPECS
    assert v5.STABLE_EDITION.identity_sha256 == v4.STABLE_EDITION.identity_sha256
    assert v5.STABLE_EDITION.enrollment_identity_sha256 == (
        v4.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v5_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v5_enrollment()
    assert enrollment.parent_entries is v4.ALPHA_ENTRIES
    assert BERTRAND_V5_START_INDEX == 965
    assert BERTRAND_V5_EXPECTED_COUNT == len(BERTRAND_V5_EXPECTED_NAMES) == 7
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == (
        BERTRAND_V5_EXPECTED_NAMES
    )
    assert len(BERTRAND_V5_BODY_ENROLLMENT_MANIFEST) == 1
    source = BERTRAND_V5_BODY_ENROLLMENT_MANIFEST[0]
    assert source.origin is BertrandV5EnrollmentOrigin.BERTRAND
    assert source.names == BERTRAND_V5_EXPECTED_NAMES
    repository = Path(__file__).resolve().parents[3]
    assert (repository / BERTRAND_RFC_PATH).is_file()
    available = {entry.spec.name for entry in enrollment.parent_entries}
    for spec in enrollment.bertrand_specs:
        assert spec.name not in available
        assert set(spec.dependencies) <= available
        assert all("DNE" not in command for command in spec.script)
        assert (repository / enrollment.source_by_name[spec.name]).is_file()
        assert (repository / enrollment.test_by_name[spec.name]).is_file()
        assert enrollment.origin_by_name[spec.name].value == "bertrand"
        available.add(spec.name)


def test_v5_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v5.ALPHA_ENTRIES) == 972
    assert len({entry.spec.name for entry in v5.ALPHA_ENTRIES}) == 972
    assert (v5.ALPHA_EDITION.edge_count, v5.ALPHA_EDITION.layer_count) == (
        2912,
        45,
    )
    depths = {
        name: v5.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V5_EXPECTED_NAMES
    }
    assert sha256(_compact(depths).encode()).hexdigest() == (
        EXPECTED_DEPTH_ROOT_SHA256
    )
    assert v5.ALPHA_V5_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v5.EXPECTED_ALPHA_V5_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v5.ALPHA_V5_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v5.EXPECTED_ALPHA_V5_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v5.ALPHA_ENTRIES) == {
        v5.Membership.STABLE: 432,
        v5.Membership.ALPHA_ONLY: 540,
    }
    assert Counter(entry.evidence for entry in v5.ALPHA_ENTRIES) == {
        v5.EvidenceStatus.STABLE_CLOSED: 432,
        v5.EvidenceStatus.ALPHA_CLOSED: 138,
        v5.EvidenceStatus.BODY_CHECKED: 401,
        v5.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }


def test_all_seven_factorialval_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v5_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    assert len(receipts) == 7
    assert sha256(_compact(payload).encode()).hexdigest() == (
        EXPECTED_BODY_RECEIPT_ROOT_SHA256
    )


def test_v5_checked_use_boundary_refuses_every_factorialval_row() -> None:
    assert len(v5.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v5.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v5.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V5_EXPECTED_NAMES:
        assert v5.entry(name) is None
        item = v5.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v5.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v5.EnrollmentOrigin.BERTRAND
        assert not item.checked_use
        with pytest.raises(v5.EditionV5ReplayError, match="body_checked"):
            v5.replay(name, edition="alpha")

    old = v5.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
