"""Runtime and evidence-boundary seals for Bertrand Alpha v9."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v8 as v8
from peano_lab.library import editions_v9 as v9
from peano_lab.library.alpha_enrollment_v9 import (
    BERTRAND_RFC_PATHS,
    BERTRAND_V9_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V9_EXPECTED_COUNT,
    BERTRAND_V9_EXPECTED_COUNTS,
    BERTRAND_V9_EXPECTED_MICROBATCH_SOURCE_COUNTS,
    BERTRAND_V9_EXPECTED_NAMES,
    BERTRAND_V9_MICROBATCH_COUNTS,
    BERTRAND_V9_MICROBATCH_NAMES,
    BERTRAND_V9_START_INDEX,
    PARENT_ALPHA_V8_COUNT,
    PARENT_ALPHA_V8_ENROLLMENT_SHA256,
    PARENT_ALPHA_V8_IDENTITY_SHA256,
    BertrandV9EnrollmentOrigin,
    alpha_v9_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f"
)
EXPECTED_IDENTITY_SHA256 = (
    "b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "61f33ba9e49219ff4a199d082722d9582ac6d87f825851173ac7fdb6931bb52d"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab"
)
EXPECTED_RFC_SHA256 = {
    (
        "research/arithmetic-library/"
        "ha-bertrand-primorial-foundation-tranche-rfc-v1.md"
    ): "c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89",
    (
        "research/arithmetic-library/"
        "ha-bertrand-primorial-membership-tranche-rfc-v1.md"
    ): "4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5",
}
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v8.json": (
        "c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370"
    ),
    "artifacts/peano-library/alpha/metrics-v8.json": (
        "90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v8.mmd": (
        "ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008"
    ),
    "artifacts/peano-library/channels-v8.json": (
        "dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d"
    ),
}

EXPECTED_FIRST_MICROBATCH_NAMES = (
    "primorial_factor_choice_exists",
    "primorial_factor_choice_functional",
    "primorial_factor_prefix_extend",
    "primorial_factor_prefix_exists",
    "primorial_factor_prefix_transport_entry",
    "primorial_exists",
    "primorial_functional",
    "primorial_zero",
    "primorial_succ_decompose",
    "primorial_positive",
)
EXPECTED_SECOND_MICROBATCH_NAMES = (
    "primorial_index_eq_transport",
    "primorial_factor_choice_prime_divisor_eq",
    "primorial_prime_divides_of_le",
    "primorial_prime_le_of_divides",
    "primorial_prime_divides_iff_le",
    "primorial_succ_factor",
    "primorial_succ_divides",
    "primorial_add_length_divides",
    "primorial_le_divides",
    "primorial_le_positive_quotient",
    "primorial_le_monotone",
)
EXPECTED_SOURCE_COUNTS = (10, 11)
EXPECTED_SOURCE_MODULES = (
    "bertrand_primorial_foundation_candidate",
    "bertrand_primorial_membership_candidate",
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v9_preserves_exact_v8_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V8_COUNT == len(v8.ALPHA_ENTRIES) == 1_055
    assert PARENT_ALPHA_V8_ENROLLMENT_SHA256 == v8.ALPHA_V8_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V8_IDENTITY_SHA256 == v8.ALPHA_V8_IDENTITY_SHA256
    parent = v9.ALPHA_ENTRIES[:PARENT_ALPHA_V8_COUNT]
    for old, new in zip(v8.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v9.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v8.STABLE_SPECS)
    assert v9.STABLE_SPECS == v8.STABLE_SPECS
    assert v9.STABLE_EDITION.identity_sha256 == v8.STABLE_EDITION.identity_sha256
    assert v9.STABLE_EDITION.enrollment_identity_sha256 == (
        v8.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v9_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v9_enrollment()
    expected_batches = (
        EXPECTED_FIRST_MICROBATCH_NAMES,
        EXPECTED_SECOND_MICROBATCH_NAMES,
    )
    expected_names = expected_batches[0] + expected_batches[1]
    assert enrollment.parent_entries is v8.ALPHA_ENTRIES
    assert BERTRAND_V9_START_INDEX == 1_055
    assert BERTRAND_V9_EXPECTED_COUNT == len(expected_names) == 21
    assert BERTRAND_V9_EXPECTED_NAMES == expected_names
    assert BERTRAND_V9_MICROBATCH_COUNTS == (10, 11)
    assert BERTRAND_V9_EXPECTED_MICROBATCH_SOURCE_COUNTS == (1, 1)
    assert BERTRAND_V9_MICROBATCH_NAMES == expected_batches
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == expected_names
    assert tuple(
        len(source.names) for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    ) == BERTRAND_V9_EXPECTED_COUNTS == EXPECTED_SOURCE_COUNTS
    assert len(BERTRAND_V9_BODY_ENROLLMENT_MANIFEST) == 2
    assert tuple(
        source.module for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    ) == EXPECTED_SOURCE_MODULES
    assert tuple(
        source.factory for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    ) == tuple(f"make_{module}_theorems" for module in EXPECTED_SOURCE_MODULES)
    assert tuple(
        source.test_path for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    ) == tuple(
        f"peano-lab/py/tests/test_{module}.py" for module in EXPECTED_SOURCE_MODULES
    )
    assert tuple(
        source.rfc_path for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    ) == BERTRAND_RFC_PATHS == tuple(EXPECTED_RFC_SHA256)
    assert all(
        source.origin is BertrandV9EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in BERTRAND_RFC_PATHS
    } == EXPECTED_RFC_SHA256

    available = {entry.spec.name for entry in enrollment.parent_entries}
    for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST:
        for name in source.names:
            assert enrollment.rfc_by_name[name] == source.rfc_path
    for spec in enrollment.bertrand_specs:
        assert spec.name not in available
        assert set(spec.dependencies) <= available
        assert all("DNE" not in command for command in spec.script)
        assert (repository / enrollment.source_by_name[spec.name]).is_file()
        assert (repository / enrollment.test_by_name[spec.name]).is_file()
        assert (repository / enrollment.rfc_by_name[spec.name]).is_file()
        assert enrollment.origin_by_name[spec.name].value == "bertrand"
        available.add(spec.name)


def test_v9_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v9.ALPHA_ENTRIES) == 1_076
    assert len({entry.spec.name for entry in v9.ALPHA_ENTRIES}) == 1_076
    assert (v9.ALPHA_EDITION.edge_count, v9.ALPHA_EDITION.layer_count) == (
        v9.EXPECTED_ALPHA_V9_EDGE_COUNT,
        v9.EXPECTED_ALPHA_V9_LAYER_COUNT,
    ) == (3_276, 45)
    depths = {
        name: v9.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V9_EXPECTED_NAMES
    }
    actual_depth_root = sha256(_compact(depths).encode()).hexdigest()
    if EXPECTED_DEPTH_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v9 depth-root bootstrap required: "
            f"root={actual_depth_root}"
        )
    assert actual_depth_root == EXPECTED_DEPTH_ROOT_SHA256
    assert v9.ALPHA_V9_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v9.EXPECTED_ALPHA_V9_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v9.ALPHA_V9_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v9.EXPECTED_ALPHA_V9_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v9.ALPHA_ENTRIES) == {
        v9.Membership.STABLE: 432,
        v9.Membership.ALPHA_ONLY: 644,
    }
    assert Counter(entry.evidence for entry in v9.ALPHA_ENTRIES) == {
        v9.EvidenceStatus.STABLE_CLOSED: 432,
        v9.EvidenceStatus.ALPHA_CLOSED: 138,
        v9.EvidenceStatus.BODY_CHECKED: 505,
        v9.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    origins = Counter(entry.enrollment_origin for entry in v9.ALPHA_ENTRIES)
    assert origins[v9.EnrollmentOrigin.BERTRAND] == 111
    assert sum(origins.values()) == 1_076


def test_all_twenty_one_v9_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v9_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    actual_root = sha256(_compact(payload).encode()).hexdigest()
    assert len(receipts) == 21
    if EXPECTED_BODY_RECEIPT_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v9 body-receipt bootstrap required: "
            f"root={actual_root}"
        )
    assert actual_root == EXPECTED_BODY_RECEIPT_ROOT_SHA256


def test_v9_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v9.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v9.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v9.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V9_EXPECTED_NAMES:
        assert v9.entry(name) is None
        item = v9.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v9.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v9.EnrollmentOrigin.BERTRAND
        assert item.provenance == (v9.EnrollmentOrigin.BERTRAND,)
        assert not item.checked_use
        with pytest.raises(v9.EditionV9ReplayError, match="body_checked"):
            v9.replay(name, edition="alpha")

    old = v9.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
