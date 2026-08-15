"""Runtime and evidence-boundary seals for Bertrand Alpha v10."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v9 as v9
from peano_lab.library import editions_v10 as v10
from peano_lab.library.alpha_enrollment_v10 import (
    BERTRAND_RFC_PATHS,
    BERTRAND_V10_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V10_EXPECTED_COUNT,
    BERTRAND_V10_EXPECTED_COUNTS,
    BERTRAND_V10_EXPECTED_MICROBATCH_SOURCE_COUNTS,
    BERTRAND_V10_EXPECTED_NAMES,
    BERTRAND_V10_MICROBATCH_COUNTS,
    BERTRAND_V10_MICROBATCH_NAMES,
    BERTRAND_V10_START_INDEX,
    PARENT_ALPHA_V9_COUNT,
    PARENT_ALPHA_V9_ENROLLMENT_SHA256,
    PARENT_ALPHA_V9_IDENTITY_SHA256,
    BertrandV10EnrollmentOrigin,
    alpha_v10_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f"
)
EXPECTED_IDENTITY_SHA256 = (
    "1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "446f6c9d07c3f9e22fa0fbb41a46c95d27804a088d708b13aea0ddd7159c45dd"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "fdac645cbc070b5a1cdfe71b19e98afe095a183d4cfa0ad4256fa42857ca736c"
)
EXPECTED_RFC_SHA256 = {
    (
        "research/arithmetic-library/"
        "ha-bertrand-primorial-interval-split-tranche-rfc-v1.md"
    ): "db7d2d58f0b44d3793673b21496ea7f5d5d2747c75795587f6b1c99b2e80f46e",
}
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v9.json": (
        "74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda"
    ),
    "artifacts/peano-library/alpha/metrics-v9.json": (
        "7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v9.mmd": (
        "03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9"
    ),
    "artifacts/peano-library/channels-v9.json": (
        "77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34"
    ),
}

EXPECTED_MICROBATCH_NAMES = (
    "beta_product_prefix_suffix_split",
    "primorial_interval_factor_prefix_extend",
    "primorial_interval_factor_prefix_exists",
    "primorial_interval_factor_prefix_transport_entry",
    "primorial_interval_exists",
    "primorial_interval_functional",
    "primorial_interval_factor_prefix_shift",
    "primorial_factor_prefix_restrict_add",
    "primorial_prefix_interval_split",
)
EXPECTED_SOURCE_COUNTS = (1, 8)
EXPECTED_SOURCE_MODULES = (
    "finite_product_prefix_suffix_candidate",
    "bertrand_primorial_interval_candidate",
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v10_preserves_exact_v9_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V9_COUNT == len(v9.ALPHA_ENTRIES) == 1_076
    assert PARENT_ALPHA_V9_ENROLLMENT_SHA256 == v9.ALPHA_V9_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V9_IDENTITY_SHA256 == v9.ALPHA_V9_IDENTITY_SHA256
    parent = v10.ALPHA_ENTRIES[:PARENT_ALPHA_V9_COUNT]
    for old, new in zip(v9.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v10.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v9.STABLE_SPECS)
    assert v10.STABLE_SPECS == v9.STABLE_SPECS
    assert v10.STABLE_EDITION.identity_sha256 == v9.STABLE_EDITION.identity_sha256
    assert v10.STABLE_EDITION.enrollment_identity_sha256 == (
        v9.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v10_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v10_enrollment()
    expected_batches = (EXPECTED_MICROBATCH_NAMES,)
    expected_names = EXPECTED_MICROBATCH_NAMES
    assert enrollment.parent_entries is v9.ALPHA_ENTRIES
    assert BERTRAND_V10_START_INDEX == 1_076
    assert BERTRAND_V10_EXPECTED_COUNT == len(expected_names) == 9
    assert BERTRAND_V10_EXPECTED_NAMES == expected_names
    assert BERTRAND_V10_MICROBATCH_COUNTS == (9,)
    assert BERTRAND_V10_EXPECTED_MICROBATCH_SOURCE_COUNTS == (2,)
    assert BERTRAND_V10_MICROBATCH_NAMES == expected_batches
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == expected_names
    assert tuple(
        len(source.names) for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    ) == BERTRAND_V10_EXPECTED_COUNTS == EXPECTED_SOURCE_COUNTS
    assert len(BERTRAND_V10_BODY_ENROLLMENT_MANIFEST) == 2
    assert tuple(
        source.factory_count for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    ) == (2, 8)
    assert tuple(
        source.selected_count
        for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    ) == EXPECTED_SOURCE_COUNTS
    assert tuple(
        source.module for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    ) == EXPECTED_SOURCE_MODULES
    assert tuple(
        source.factory for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    ) == tuple(f"make_{module}_theorems" for module in EXPECTED_SOURCE_MODULES)
    assert tuple(
        source.test_path for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    ) == tuple(
        f"peano-lab/py/tests/test_{module}.py" for module in EXPECTED_SOURCE_MODULES
    )
    assert tuple(
        dict.fromkeys(
            source.rfc_path
            for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
        )
    ) == BERTRAND_RFC_PATHS == tuple(EXPECTED_RFC_SHA256)
    assert all(
        source.origin is BertrandV10EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in BERTRAND_RFC_PATHS
    } == EXPECTED_RFC_SHA256

    available = {entry.spec.name for entry in enrollment.parent_entries}
    for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST:
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


def test_v10_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v10.ALPHA_ENTRIES) == 1_085
    assert len({entry.spec.name for entry in v10.ALPHA_ENTRIES}) == 1_085
    assert (v10.ALPHA_EDITION.edge_count, v10.ALPHA_EDITION.layer_count) == (
        v10.EXPECTED_ALPHA_V10_EDGE_COUNT,
        v10.EXPECTED_ALPHA_V10_LAYER_COUNT,
    ) == (3_306, 45)
    depths = {
        name: v10.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V10_EXPECTED_NAMES
    }
    actual_depth_root = sha256(_compact(depths).encode()).hexdigest()
    if EXPECTED_DEPTH_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v10 depth-root bootstrap required: "
            f"root={actual_depth_root}"
        )
    assert actual_depth_root == EXPECTED_DEPTH_ROOT_SHA256
    assert v10.ALPHA_V10_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v10.EXPECTED_ALPHA_V10_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v10.ALPHA_V10_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v10.EXPECTED_ALPHA_V10_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v10.ALPHA_ENTRIES) == {
        v10.Membership.STABLE: 432,
        v10.Membership.ALPHA_ONLY: 653,
    }
    assert Counter(entry.evidence for entry in v10.ALPHA_ENTRIES) == {
        v10.EvidenceStatus.STABLE_CLOSED: 432,
        v10.EvidenceStatus.ALPHA_CLOSED: 138,
        v10.EvidenceStatus.BODY_CHECKED: 514,
        v10.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    origins = Counter(entry.enrollment_origin for entry in v10.ALPHA_ENTRIES)
    assert origins[v10.EnrollmentOrigin.BERTRAND] == 120
    assert sum(origins.values()) == 1_085


def test_all_nine_v10_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v10_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    actual_root = sha256(_compact(payload).encode()).hexdigest()
    assert len(receipts) == 9
    if EXPECTED_BODY_RECEIPT_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v10 body-receipt bootstrap required: "
            f"root={actual_root}"
        )
    assert actual_root == EXPECTED_BODY_RECEIPT_ROOT_SHA256


def test_v10_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v10.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v10.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v10.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V10_EXPECTED_NAMES:
        assert v10.entry(name) is None
        item = v10.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v10.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v10.EnrollmentOrigin.BERTRAND
        assert item.provenance == (v10.EnrollmentOrigin.BERTRAND,)
        assert not item.checked_use
        with pytest.raises(v10.EditionV10ReplayError, match="body_checked"):
            v10.replay(name, edition="alpha")

    old = v10.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
