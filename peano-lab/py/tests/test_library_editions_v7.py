"""Runtime and evidence-boundary seals for Bertrand Alpha v7."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v6 as v6
from peano_lab.library import editions_v7 as v7
from peano_lab.library.alpha_enrollment_v7 import (
    BERTRAND_RFC_PATH,
    BERTRAND_V7_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V7_EXPECTED_COUNT,
    BERTRAND_V7_EXPECTED_COUNTS,
    BERTRAND_V7_EXPECTED_NAMES,
    BERTRAND_V7_START_INDEX,
    PARENT_ALPHA_V6_COUNT,
    PARENT_ALPHA_V6_ENROLLMENT_SHA256,
    PARENT_ALPHA_V6_IDENTITY_SHA256,
    BertrandV7EnrollmentOrigin,
    alpha_v7_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
)
EXPECTED_IDENTITY_SHA256 = (
    "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "1283469f3f8226681421675cca15a6d8d4ae43c10203b475ad352a21480fa189"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "3dc15f1dd94fbbef710bf40fe8890b6ca079cab48c2807e0efe01825afa55ba9"
)
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v6.json": (
        "c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d"
    ),
    "artifacts/peano-library/alpha/metrics-v6.json": (
        "f2a6c22b9fe50581a4cfe8d3b1b494fa274d26d0b51b60e92735650a09391be7"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v6.mmd": (
        "532c2482a3b1c371026bd80b1b7297faffc4a1b1ee3e53031e499f1611b3ae16"
    ),
    "artifacts/peano-library/channels-v6.json": (
        "6ef8bb93b2e24bdfe45389ca9417b6333ce83ae249ee49a957959a6b3471b86c"
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


def test_v7_preserves_exact_v6_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V6_COUNT == len(v6.ALPHA_ENTRIES) == 993
    assert PARENT_ALPHA_V6_ENROLLMENT_SHA256 == v6.ALPHA_V6_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V6_IDENTITY_SHA256 == v6.ALPHA_V6_IDENTITY_SHA256
    parent = v7.ALPHA_ENTRIES[:PARENT_ALPHA_V6_COUNT]
    for old, new in zip(v6.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v7.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v6.STABLE_SPECS)
    assert v7.STABLE_SPECS == v6.STABLE_SPECS
    assert v7.STABLE_EDITION.identity_sha256 == v6.STABLE_EDITION.identity_sha256
    assert v7.STABLE_EDITION.enrollment_identity_sha256 == (
        v6.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v7_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v7_enrollment()
    assert enrollment.parent_entries is v6.ALPHA_ENTRIES
    assert BERTRAND_V7_START_INDEX == 993
    assert BERTRAND_V7_EXPECTED_COUNT == len(BERTRAND_V7_EXPECTED_NAMES) == 24
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == (
        BERTRAND_V7_EXPECTED_NAMES
    )
    assert tuple(len(source.names) for source in BERTRAND_V7_BODY_ENROLLMENT_MANIFEST) == (
        BERTRAND_V7_EXPECTED_COUNTS
    )
    assert len(BERTRAND_V7_BODY_ENROLLMENT_MANIFEST) == 7
    constructor_source = BERTRAND_V7_BODY_ENROLLMENT_MANIFEST[0]
    assert constructor_source.module == (
        "bertrand_initial_segment_constructor_candidate"
    )
    assert constructor_source.factory == (
        "make_bertrand_initial_segment_constructor_candidate_theorems"
    )
    assert all(
        source.origin is BertrandV7EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V7_BODY_ENROLLMENT_MANIFEST
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


def test_v7_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v7.ALPHA_ENTRIES) == 1017
    assert len({entry.spec.name for entry in v7.ALPHA_ENTRIES}) == 1017
    assert (v7.ALPHA_EDITION.edge_count, v7.ALPHA_EDITION.layer_count) == (
        v7.EXPECTED_ALPHA_V7_EDGE_COUNT,
        v7.EXPECTED_ALPHA_V7_LAYER_COUNT,
    )
    depths = {
        name: v7.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V7_EXPECTED_NAMES
    }
    assert sha256(_compact(depths).encode()).hexdigest() == (
        EXPECTED_DEPTH_ROOT_SHA256
    )
    assert v7.ALPHA_V7_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v7.EXPECTED_ALPHA_V7_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v7.ALPHA_V7_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v7.EXPECTED_ALPHA_V7_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v7.ALPHA_ENTRIES) == {
        v7.Membership.STABLE: 432,
        v7.Membership.ALPHA_ONLY: 585,
    }
    assert Counter(entry.evidence for entry in v7.ALPHA_ENTRIES) == {
        v7.EvidenceStatus.STABLE_CLOSED: 432,
        v7.EvidenceStatus.ALPHA_CLOSED: 138,
        v7.EvidenceStatus.BODY_CHECKED: 446,
        v7.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }


def test_all_twenty_four_v7_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v7_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    assert len(receipts) == 24
    assert sha256(_compact(payload).encode()).hexdigest() == (
        EXPECTED_BODY_RECEIPT_ROOT_SHA256
    )


def test_v7_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v7.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v7.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v7.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V7_EXPECTED_NAMES:
        assert v7.entry(name) is None
        item = v7.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v7.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v7.EnrollmentOrigin.BERTRAND
        assert not item.checked_use
        with pytest.raises(v7.EditionV7ReplayError, match="body_checked"):
            v7.replay(name, edition="alpha")

    old = v7.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
