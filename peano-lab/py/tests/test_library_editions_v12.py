"""Runtime and evidence-boundary seals for Bertrand Alpha v12."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v11 as v11
from peano_lab.library import editions_v12 as v12
from peano_lab.library.alpha_enrollment_v12 import (
    BERTRAND_RFC_PATHS,
    BERTRAND_V12_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V12_EXPECTED_COUNT,
    BERTRAND_V12_EXPECTED_COUNTS,
    BERTRAND_V12_EXPECTED_NAMES,
    BERTRAND_V12_MICROBATCH_COUNTS,
    BERTRAND_V12_MICROBATCH_NAMES,
    BERTRAND_V12_START_INDEX,
    PARENT_ALPHA_V11_COUNT,
    PARENT_ALPHA_V11_ENROLLMENT_SHA256,
    PARENT_ALPHA_V11_IDENTITY_SHA256,
    BertrandV12EnrollmentOrigin,
    alpha_v12_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b"
)
EXPECTED_IDENTITY_SHA256 = (
    "bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "ee9494f8dfb9e4070a2ce3d2d740b312d147948dcd296ac0da7ed059c9944e50"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "df0e5cb8402483360f8381c76c7ce6ed6c70245df45556107c40652d00beb0da"
)
EXPECTED_NAMES_SHA256 = (
    "fb92957c4378ad4fadf93470d1c632c970be2b76e1ba862b6694d7166f7b9a12"
)
EXPECTED_RFC_SHA256 = {
    (
        "research/arithmetic-library/"
        "ha-bertrand-b6-release-tranche-rfc-v1.md"
    ): "cb6a22a23f44958546eebedd9bdadb28ba466519c2951920cd2ac5f3c04760f3",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-order-quotient-tranche-rfc-v1.md"
    ): "fdcaf69b3913b7dbbcf312373b49f39b42819ba398cbb35f77e8eb66fb4762c1",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-central-valuation-tranche-rfc-v1.md"
    ): "aebab5f4cf6a63b67a0716c3dcd792a876f263bce6d371d25dcb4e3dbf78a8b3",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-central-carry-tranche-rfc-v1.md"
    ): "a9074118af3e2077b95305a7de7c2a25837bcf56999f44e7e7bc5b48eb144974",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-square-tail-tranche-rfc-v1.md"
    ): "dac2a5aee172a8ec78121ff5c83cbeead54f6b08733a0b91fb79183318eac7b5",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-zero-two-thirds-tranche-rfc-v1.md"
    ): "9b920ae8f646fb3b460a352ac82c332d4cd23e3d7bbe4e6fa9ba74e17c1696fc",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-factor-ranges-tranche-rfc-v1.md"
    ): "32765966c68b0db98fb48136e5b3fdbc3312b6c7ef6d35737e7f1381e03f2c3b",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-prime-contribution-foundation-tranche-rfc-v1.md"
    ): "4970fabdc7ff1872a52bed7a18643a777939304cf7b2061a196518533385b520",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-prime-contribution-completeness-tranche-rfc-v1.md"
    ): "0ec8561f2ea191df4e2d26edb381d8f48fcbb6c071d6e9dbe2e697b52517687e",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-range-boundaries-tranche-rfc-v1.md"
    ): "635a83faa0db7f4aae0f9c8632655789da91ad79ebb0a905bcf864d7bf646dbb",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-contribution-split-tranche-rfc-v1.md"
    ): "190c1d4616eef0debea1944385c8be0f7f3f0ac2f29c1254aa8b8729db534fd6",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b5-central-upper-tranche-rfc-v1.md"
    ): "c40e10fb041aa0fdccd07d830afde12c0d9ddac5431207abe91f85196f465b98",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b7-eventual-tranche-rfc-v1.md"
    ): "d95a8224beaef6eb70443444ac7c89155bd3e1f82ce4d4751926d4d61c1545be",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-prime-certificates-tranche-rfc-v1.md"
    ): "356e8d69498f117921b1229c9a07b42f9caad48febe612a2e89ab93578a3ba73",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-covering-tranche-rfc-v1.md"
    ): "1c21f5eb30e7f34ac41013aa10da736f7604696829a907134c6b6b9e3e7720f5",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-small-range-tranche-rfc-v1.md"
    ): "08ee855a908faa9e990f75b22a8d599314e446c5bc39773196c79d3130b85891",
    (
        "research/arithmetic-library/"
        "ha-bertrand-bp01-tranche-rfc-v1.md"
    ): "7eff83b267a9be832f2d6b7f0b6a2e2fff82d3cd1e6d09e806f264a5459c1ec3",
    (
        "research/arithmetic-library/"
        "ha-bertrand-bp02-tranche-rfc-v1.md"
    ): "ef97d7b1b524e8abce6da32abf463a74cb2bc2e39f0a3334c697946bd097df80",
}
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v11.json": (
        "d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c"
    ),
    "artifacts/peano-library/alpha/metrics-v11.json": (
        "92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v11.mmd": (
        "c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1"
    ),
    "artifacts/peano-library/channels-v11.json": (
        "039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f"
    ),
}
EXPECTED_SOURCE_COUNTS = (
    30,
    6,
    2,
    3,
    2,
    10,
    10,
    10,
    2,
    7,
    8,
    12,
    10,
    10,
    10,
    10,
    1,
    18,
    14,
    2,
    1,
    2,
)
EXPECTED_SOURCE_MODULES = (
    "bertrand_hj_base_thirty_two_candidate",
    "bertrand_hj_all_s_candidate",
    "bertrand_b6_growth_candidate",
    "bertrand_b6_main_inequality_candidate",
    "finite_product_order_candidate",
    "bertrand_b5_order_quotient_candidate",
    "bertrand_central_binom_valuation_candidate",
    "bertrand_central_binom_carry_candidate",
    "bertrand_central_binom_square_tail_candidate",
    "bertrand_central_binom_zero_range_candidate",
    "bertrand_central_binom_factor_ranges_candidate",
    "bertrand_prime_contribution_candidate",
    "bertrand_prime_contribution_complete_candidate",
    "bertrand_b5_range_boundaries_candidate",
    "bertrand_b5_contribution_split_candidate",
    "bertrand_b5_central_upper_candidate",
    "bertrand_b7_eventual_candidate",
    "bertrand_b8_prime_certificates_candidate",
    "bertrand_b8_covering_candidate",
    "bertrand_b8_small_candidate",
    "bertrand_bp01_candidate",
    "bertrand_bp02_candidate",
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v12_preserves_exact_v11_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V11_COUNT == len(v11.ALPHA_ENTRIES) == 1_123
    assert PARENT_ALPHA_V11_ENROLLMENT_SHA256 == v11.ALPHA_V11_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V11_IDENTITY_SHA256 == v11.ALPHA_V11_IDENTITY_SHA256
    parent = v12.ALPHA_ENTRIES[:PARENT_ALPHA_V11_COUNT]
    for old, new in zip(v11.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v12.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v11.STABLE_SPECS)
    assert v12.STABLE_SPECS == v11.STABLE_SPECS
    assert v12.STABLE_EDITION.identity_sha256 == v11.STABLE_EDITION.identity_sha256
    assert v12.STABLE_EDITION.enrollment_identity_sha256 == (
        v11.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v12_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v12_enrollment()
    expected_names = tuple(spec.name for spec in enrollment.bertrand_specs)
    assert enrollment.parent_entries is v11.ALPHA_ENTRIES
    assert BERTRAND_V12_START_INDEX == 1_123
    assert BERTRAND_V12_EXPECTED_COUNT == len(expected_names) == 180
    assert BERTRAND_V12_EXPECTED_NAMES == expected_names
    assert sha256(_compact(expected_names).encode()).hexdigest() == (
        EXPECTED_NAMES_SHA256
    )
    assert BERTRAND_V12_MICROBATCH_COUNTS == (20,) * 9
    assert BERTRAND_V12_MICROBATCH_NAMES == tuple(
        expected_names[offset : offset + 20] for offset in range(0, 180, 20)
    )
    assert tuple(
        len(source.names) for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
    ) == BERTRAND_V12_EXPECTED_COUNTS == EXPECTED_SOURCE_COUNTS
    assert len(BERTRAND_V12_BODY_ENROLLMENT_MANIFEST) == 22
    assert tuple(
        source.module for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
    ) == EXPECTED_SOURCE_MODULES
    assert all(
        source.factory.startswith("make_")
        and source.factory.endswith("candidate_theorems")
        for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
    )
    assert tuple(
        dict.fromkeys(
            source.rfc_path
            for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
        )
    ) == BERTRAND_RFC_PATHS == tuple(EXPECTED_RFC_SHA256)
    assert all(
        source.origin is BertrandV12EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in BERTRAND_RFC_PATHS
    } == EXPECTED_RFC_SHA256

    available = {entry.spec.name for entry in enrollment.parent_entries}
    for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST:
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


def test_v12_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v12.ALPHA_ENTRIES) == 1_303
    assert len({entry.spec.name for entry in v12.ALPHA_ENTRIES}) == 1_303
    assert (v12.ALPHA_EDITION.edge_count, v12.ALPHA_EDITION.layer_count) == (
        v12.EXPECTED_ALPHA_V12_EDGE_COUNT,
        v12.EXPECTED_ALPHA_V12_LAYER_COUNT,
    ) == (4_302, 45)
    depths = {
        name: v12.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V12_EXPECTED_NAMES
    }
    actual_depth_root = sha256(_compact(depths).encode()).hexdigest()
    if EXPECTED_DEPTH_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v12 depth-root bootstrap required: "
            f"root={actual_depth_root}"
        )
    assert actual_depth_root == EXPECTED_DEPTH_ROOT_SHA256
    assert v12.ALPHA_V12_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v12.EXPECTED_ALPHA_V12_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v12.ALPHA_V12_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v12.EXPECTED_ALPHA_V12_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v12.ALPHA_ENTRIES) == {
        v12.Membership.STABLE: 432,
        v12.Membership.ALPHA_ONLY: 871,
    }
    assert Counter(entry.evidence for entry in v12.ALPHA_ENTRIES) == {
        v12.EvidenceStatus.STABLE_CLOSED: 432,
        v12.EvidenceStatus.ALPHA_CLOSED: 138,
        v12.EvidenceStatus.BODY_CHECKED: 732,
        v12.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    origins = Counter(entry.enrollment_origin for entry in v12.ALPHA_ENTRIES)
    assert origins[v12.EnrollmentOrigin.BERTRAND] == 338
    assert sum(origins.values()) == 1_303


def test_all_one_hundred_eighty_v12_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v12_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    actual_root = sha256(_compact(payload).encode()).hexdigest()
    assert len(receipts) == 180
    if EXPECTED_BODY_RECEIPT_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v12 body-receipt bootstrap required: "
            f"root={actual_root}"
        )
    assert actual_root == EXPECTED_BODY_RECEIPT_ROOT_SHA256


def test_v12_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v12.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v12.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v12.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V12_EXPECTED_NAMES:
        assert v12.entry(name) is None
        item = v12.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v12.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v12.EnrollmentOrigin.BERTRAND
        assert item.provenance == (v12.EnrollmentOrigin.BERTRAND,)
        assert not item.checked_use
        with pytest.raises(v12.EditionV12ReplayError, match="body_checked"):
            v12.replay(name, edition="alpha")

    old = v12.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
