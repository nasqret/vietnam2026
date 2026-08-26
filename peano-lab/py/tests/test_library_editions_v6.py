"""Runtime and evidence-boundary seals for Bertrand Alpha v6."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v5 as v5
from peano_lab.library import editions_v6 as v6
from peano_lab.library.alpha_enrollment_v6 import (
    BERTRAND_RFC_PATH,
    BERTRAND_V6_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V6_EXPECTED_COUNT,
    BERTRAND_V6_EXPECTED_COUNTS,
    BERTRAND_V6_EXPECTED_NAMES,
    BERTRAND_V6_START_INDEX,
    PARENT_ALPHA_V5_COUNT,
    PARENT_ALPHA_V5_ENROLLMENT_SHA256,
    PARENT_ALPHA_V5_IDENTITY_SHA256,
    BertrandV6EnrollmentOrigin,
    alpha_v6_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "dc25a3dc0ab7346f9188eee1262700b40bb09efdacfa849f3a27475ed870b5a7"
)
EXPECTED_IDENTITY_SHA256 = (
    "7e46b80c4799e51da32cedf21a130274200fa14b21e0fec3b42f74d1523ab23b"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "d103de2054a0bd4de3b2faa9d98435a4f705594f8a69968e9ca956c455cb61d3"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "c23b2fc58fabd3803a0ded5f02d4ea348d67a00b25f5b28b35f3d6bcb00ff2f1"
)
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v5.json": (
        "94efc0f7022f31677619e842f7d6f1d0d0f8959efc54cd64cf346c3b5e8c4892"
    ),
    "artifacts/peano-library/alpha/metrics-v5.json": (
        "b560373c8cb4879f47e46083d5b9925cd29ebee1af4856cfc93e74017555acc2"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v5.mmd": (
        "4e8f1ea73b3ecfd51cf80d216dfc9171dabbe12f38d9c8392185ea1c610112ab"
    ),
    "artifacts/peano-library/channels-v5.json": (
        "946682733744d6969e89059df9165cc2782510101d4ee43a6a861aa7570a3f31"
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


def test_v6_preserves_exact_v5_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V5_COUNT == len(v5.ALPHA_ENTRIES) == 972
    assert PARENT_ALPHA_V5_ENROLLMENT_SHA256 == v5.ALPHA_V5_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V5_IDENTITY_SHA256 == v5.ALPHA_V5_IDENTITY_SHA256
    parent = v6.ALPHA_ENTRIES[:PARENT_ALPHA_V5_COUNT]
    for old, new in zip(v5.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v6.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v5.STABLE_SPECS)
    assert v6.STABLE_SPECS == v5.STABLE_SPECS
    assert v6.STABLE_EDITION.identity_sha256 == v5.STABLE_EDITION.identity_sha256
    assert v6.STABLE_EDITION.enrollment_identity_sha256 == (
        v5.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v6_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v6_enrollment()
    assert enrollment.parent_entries is v5.ALPHA_ENTRIES
    assert BERTRAND_V6_START_INDEX == 972
    assert BERTRAND_V6_EXPECTED_COUNT == len(BERTRAND_V6_EXPECTED_NAMES) == 21
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == (
        BERTRAND_V6_EXPECTED_NAMES
    )
    assert tuple(len(source.names) for source in BERTRAND_V6_BODY_ENROLLMENT_MANIFEST) == (
        BERTRAND_V6_EXPECTED_COUNTS
    )
    assert len(BERTRAND_V6_BODY_ENROLLMENT_MANIFEST) == 4
    assert all(
        source.origin is BertrandV6EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V6_BODY_ENROLLMENT_MANIFEST
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
        assert enrollment.origin_by_name[spec.name].value == "bertrand"
        available.add(spec.name)


def test_v6_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v6.ALPHA_ENTRIES) == 993
    assert len({entry.spec.name for entry in v6.ALPHA_ENTRIES}) == 993
    assert (v6.ALPHA_EDITION.edge_count, v6.ALPHA_EDITION.layer_count) == (
        2977,
        45,
    )
    depths = {
        name: v6.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V6_EXPECTED_NAMES
    }
    assert sha256(_compact(depths).encode()).hexdigest() == (
        EXPECTED_DEPTH_ROOT_SHA256
    )
    assert v6.ALPHA_V6_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v6.EXPECTED_ALPHA_V6_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v6.ALPHA_V6_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v6.EXPECTED_ALPHA_V6_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v6.ALPHA_ENTRIES) == {
        v6.Membership.STABLE: 432,
        v6.Membership.ALPHA_ONLY: 561,
    }
    assert Counter(entry.evidence for entry in v6.ALPHA_ENTRIES) == {
        v6.EvidenceStatus.STABLE_CLOSED: 432,
        v6.EvidenceStatus.ALPHA_CLOSED: 138,
        v6.EvidenceStatus.BODY_CHECKED: 422,
        v6.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }


def test_all_twenty_one_v6_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v6_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    assert len(receipts) == 21
    assert sha256(_compact(payload).encode()).hexdigest() == (
        EXPECTED_BODY_RECEIPT_ROOT_SHA256
    )


def test_v6_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v6.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v6.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v6.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V6_EXPECTED_NAMES:
        assert v6.entry(name) is None
        item = v6.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v6.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v6.EnrollmentOrigin.BERTRAND
        assert not item.checked_use
        with pytest.raises(v6.EditionV6ReplayError, match="body_checked"):
            v6.replay(name, edition="alpha")

    old = v6.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
