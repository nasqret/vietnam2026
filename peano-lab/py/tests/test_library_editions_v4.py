"""Runtime and evidence-boundary seals for Bertrand Alpha v4."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v3 as v3
from peano_lab.library import editions_v4 as v4
from peano_lab.library.alpha_enrollment_v4 import (
    BERTRAND_RFC_PATH,
    BERTRAND_V4_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V4_EXPECTED_COUNT,
    BERTRAND_V4_EXPECTED_NAMES,
    BERTRAND_V4_START_INDEX,
    PARENT_ALPHA_V3_COUNT,
    PARENT_ALPHA_V3_ENROLLMENT_SHA256,
    PARENT_ALPHA_V3_IDENTITY_SHA256,
    BertrandV4EnrollmentOrigin,
    alpha_v4_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "e4c83174c1800c135d0fe9ac03b5cdfcc5f11e5517f871b3f198586973a20c31"
)
EXPECTED_IDENTITY_SHA256 = (
    "e0324009614f755f2251a5b27d29587b0c43015385a78d567b328776b92239a5"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "902c465d0155c25820b12a65d957f52ee67e19277af5f3114327712f39bd7934"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "524c4a4f1139c673367d90b17f3ea246d8586e42b3ac14210005f7da08e6ec94"
)
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v3.json": (
        "1cd6b31379737efb3d889318e1c40beffcc14f77432a1b18cb74e80a5d29d199"
    ),
    "artifacts/peano-library/alpha/metrics-v3.json": (
        "50f5a2dab17fffa6b2ad0e936138bc197297caf066218e4054f8bc8b0e5ccd73"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v3.mmd": (
        "180ff8ddeccc9fafbc3607aa10b0587cbe2144cf4943621df52c2da5f26dbec7"
    ),
    "artifacts/peano-library/channels-v3.json": (
        "cd1618b8056abd22348dfac70d8a1686eecd5c6f875319c803d487c414f656ab"
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


def test_v4_preserves_exact_v3_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V3_COUNT == len(v3.ALPHA_ENTRIES) == 923
    assert PARENT_ALPHA_V3_ENROLLMENT_SHA256 == v3.ALPHA_V3_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V3_IDENTITY_SHA256 == v3.ALPHA_V3_IDENTITY_SHA256
    parent = v4.ALPHA_ENTRIES[:PARENT_ALPHA_V3_COUNT]
    for old, new in zip(v3.ALPHA_ENTRIES, parent, strict=True):
        assert new.spec is old.spec
        assert new.membership is old.membership
        assert new.evidence is old.evidence
        assert new.enrollment_origin.value == old.enrollment_origin.value
        assert tuple(item.value for item in new.provenance) == tuple(
            item.value for item in old.provenance
        )
        assert new.source_module == old.source_module
    assert v4.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v3.STABLE_SPECS)
    assert v4.STABLE_SPECS == v3.STABLE_SPECS
    assert v4.STABLE_EDITION.identity_sha256 == v3.STABLE_EDITION.identity_sha256
    assert v4.STABLE_EDITION.enrollment_identity_sha256 == (
        v3.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v4_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v4_enrollment()
    assert enrollment.parent_entries is v3.ALPHA_ENTRIES
    assert BERTRAND_V4_START_INDEX == 923
    assert BERTRAND_V4_EXPECTED_COUNT == len(BERTRAND_V4_EXPECTED_NAMES) == 42
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == (
        BERTRAND_V4_EXPECTED_NAMES
    )
    assert tuple(
        len(source.names) for source in BERTRAND_V4_BODY_ENROLLMENT_MANIFEST
    ) == (6, 11, 5, 9, 4, 7)
    assert tuple(source.origin for source in BERTRAND_V4_BODY_ENROLLMENT_MANIFEST) == (
        BertrandV4EnrollmentOrigin.B2_VALUATION_LAWS,
        BertrandV4EnrollmentOrigin.B2_VALUATION_MULTIPLICATION,
        BertrandV4EnrollmentOrigin.B6_INTEGER_ENVELOPE,
        BertrandV4EnrollmentOrigin.B6_CEIL_SQRT,
        BertrandV4EnrollmentOrigin.B6_FLOOR_SQRT_TOTAL,
        BertrandV4EnrollmentOrigin.B6_QUOTIENT_BUDGET,
    )
    repository = Path(__file__).resolve().parents[3]
    assert (repository / BERTRAND_RFC_PATH).is_file()
    available = {entry.spec.name for entry in enrollment.parent_entries}
    for spec in enrollment.bertrand_specs:
        assert spec.name not in available
        assert set(spec.dependencies) <= available
        assert all("DNE" not in command for command in spec.script)
        assert (repository / enrollment.source_by_name[spec.name]).is_file()
        assert (repository / enrollment.test_by_name[spec.name]).is_file()
        available.add(spec.name)


def test_v4_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v4.ALPHA_ENTRIES) == 965
    assert len({entry.spec.name for entry in v4.ALPHA_ENTRIES}) == 965
    assert (v4.ALPHA_EDITION.edge_count, v4.ALPHA_EDITION.layer_count) == (
        2891,
        45,
    )
    depths = {
        name: v4.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V4_EXPECTED_NAMES
    }
    assert sha256(_compact(depths).encode()).hexdigest() == (
        EXPECTED_DEPTH_ROOT_SHA256
    )
    assert v4.ALPHA_V4_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v4.EXPECTED_ALPHA_V4_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v4.ALPHA_V4_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v4.EXPECTED_ALPHA_V4_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v4.ALPHA_ENTRIES) == {
        v4.Membership.STABLE: 432,
        v4.Membership.ALPHA_ONLY: 533,
    }
    assert Counter(entry.evidence for entry in v4.ALPHA_ENTRIES) == {
        v4.EvidenceStatus.STABLE_CLOSED: 432,
        v4.EvidenceStatus.ALPHA_CLOSED: 138,
        v4.EvidenceStatus.BODY_CHECKED: 394,
        v4.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }


def test_all_forty_two_round2_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v4_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    assert len(receipts) == 42
    assert sha256(_compact(payload).encode()).hexdigest() == (
        EXPECTED_BODY_RECEIPT_ROOT_SHA256
    )


def test_v4_checked_use_boundary_refuses_every_round2_row() -> None:
    assert len(v4.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v4.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v4.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V4_EXPECTED_NAMES:
        assert v4.entry(name) is None
        item = v4.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v4.EvidenceStatus.BODY_CHECKED
        assert not item.checked_use
        with pytest.raises(v4.EditionV4ReplayError, match="body_checked"):
            v4.replay(name, edition="alpha")

    old = v4.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
