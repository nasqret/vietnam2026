"""Runtime and evidence-boundary seals for Bertrand Alpha v8."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v7 as v7
from peano_lab.library import editions_v8 as v8
from peano_lab.library.alpha_enrollment_v8 import (
    BERTRAND_RFC_PATH,
    BERTRAND_V8_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V8_EXPECTED_COUNT,
    BERTRAND_V8_EXPECTED_COUNTS,
    BERTRAND_V8_EXPECTED_MICROBATCH_SOURCE_COUNTS,
    BERTRAND_V8_EXPECTED_NAMES,
    BERTRAND_V8_MICROBATCH_COUNTS,
    BERTRAND_V8_MICROBATCH_NAMES,
    BERTRAND_V8_START_INDEX,
    PARENT_ALPHA_V7_COUNT,
    PARENT_ALPHA_V7_ENROLLMENT_SHA256,
    PARENT_ALPHA_V7_IDENTITY_SHA256,
    BertrandV8EnrollmentOrigin,
    alpha_v8_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2"
)
EXPECTED_IDENTITY_SHA256 = (
    "2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "c13a4a20e16e2fc84fccbc11889dd64e2527ad42d45df15731845f3fd4eb94b1"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "fb6e40f2470a9c436f02676ea15b99a389ee7495b4c6cd81212a42a7010b4466"
)
EXPECTED_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-choose-central-binomial-tranche-rfc-v1.md"
)
EXPECTED_RFC_SHA256 = (
    "4f337990babf85ffaacdc990f0e09a3c1943b8edb20c72ffef675cbb28cde83b"
)
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v7.json": (
        "7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4"
    ),
    "artifacts/peano-library/alpha/metrics-v7.json": (
        "c40f18bda0ec8feb9294cf445d08b51daf868e46b3931daf55bad91413d39e0d"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v7.mmd": (
        "85a53bd719e227a31d5cff15fc25ff66abaa82d498030f5a918a7c40271abc9e"
    ),
    "artifacts/peano-library/channels-v7.json": (
        "fe9c11ec8a622eb759053a42ee6acb7c2bcb1d454fe0dc5fa4b729a07ffbbd30"
    ),
}

EXPECTED_FIRST_MICROBATCH_NAMES = (
    "beta_pascal_zero_row_extend",
    "beta_pascal_zero_row_exists",
    "beta_pascal_row_step_extend",
    "beta_pascal_row_step_exists",
    "beta_pascal_table_prefix_extend",
    "beta_pascal_table_prefix_exists",
    "choose_exists",
    "beta_pascal_zero_row_pointwise_functional",
    "beta_pascal_row_step_pointwise_functional",
    "beta_pascal_table_row_pointwise_functional",
    "choose_functional",
    "choose_out_of_range_zero",
    "choose_zero",
    "beta_pascal_table_diagonal_boundary",
    "choose_self",
    "beta_pascal_table_successor_cell_recurrence",
    "choose_succ_succ_of_lt",
    "choose_succ_succ",
    "choose_self_of_eq",
    "choose_symmetry",
    "choose_positive",
    "central_binom_exists",
    "central_binom_functional",
    "central_binom_positive",
)
EXPECTED_SECOND_MICROBATCH_NAMES = (
    "central_binom_zero",
    "choose_upper_eq_transport",
    "central_binom_succ_double_middle",
    "choose_weighted_vertical",
    "central_binom_succ_recurrence",
    "factorial_length_eq_transport",
    "factorial_weighted_product_combine",
    "choose_factorial_bridge",
    "mul_lt_mul_right_nonzero",
    "four_power_central_recurrence_step",
    "pow_four_four_exact",
    "central_binom_four_weighted_of_recurrence",
    "four_pow_central_seed_package",
    "four_pow_lt_mul_central_binom",
)
EXPECTED_SOURCE_COUNTS = (
    7,
    2,
    1,
    3,
    2,
    2,
    1,
    2,
    1,
    3,
    1,
    2,
    1,
    1,
    2,
    1,
    2,
    3,
    1,
)
EXPECTED_SOURCE_MODULES = (
    "bertrand_choose_foundation_candidate",
    "bertrand_choose_row_functional_candidate",
    "bertrand_choose_table_row_functional_candidate",
    "bertrand_choose_laws_candidate",
    "bertrand_choose_diagonal_candidate",
    "bertrand_choose_recurrence_candidate",
    "bertrand_choose_pascal_candidate",
    "bertrand_choose_symmetry_candidate",
    "bertrand_choose_positive_candidate",
    "bertrand_central_binom_candidate",
    "bertrand_central_binom_zero_candidate",
    "bertrand_central_binom_succ_candidate",
    "bertrand_choose_weighted_vertical_candidate",
    "bertrand_central_binom_recurrence_candidate",
    "bertrand_choose_factorial_support_candidate",
    "bertrand_choose_factorial_bridge_candidate",
    "bertrand_central_binom_growth_candidate",
    "bertrand_central_binom_lower_seed_candidate",
    "bertrand_central_binom_lower_bound_candidate",
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v8_preserves_exact_v7_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V7_COUNT == len(v7.ALPHA_ENTRIES) == 1_017
    assert PARENT_ALPHA_V7_ENROLLMENT_SHA256 == v7.ALPHA_V7_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V7_IDENTITY_SHA256 == v7.ALPHA_V7_IDENTITY_SHA256
    parent = v8.ALPHA_ENTRIES[:PARENT_ALPHA_V7_COUNT]
    for old, new in zip(v7.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v8.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v7.STABLE_SPECS)
    assert v8.STABLE_SPECS == v7.STABLE_SPECS
    assert v8.STABLE_EDITION.identity_sha256 == v7.STABLE_EDITION.identity_sha256
    assert v8.STABLE_EDITION.enrollment_identity_sha256 == (
        v7.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v8_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v8_enrollment()
    expected_batches = (
        EXPECTED_FIRST_MICROBATCH_NAMES,
        EXPECTED_SECOND_MICROBATCH_NAMES,
    )
    expected_names = expected_batches[0] + expected_batches[1]
    assert enrollment.parent_entries is v7.ALPHA_ENTRIES
    assert BERTRAND_V8_START_INDEX == 1_017
    assert BERTRAND_V8_EXPECTED_COUNT == len(expected_names) == 38
    assert BERTRAND_V8_EXPECTED_NAMES == expected_names
    assert BERTRAND_V8_MICROBATCH_COUNTS == (24, 14)
    assert BERTRAND_V8_EXPECTED_MICROBATCH_SOURCE_COUNTS == (10, 9)
    assert BERTRAND_V8_MICROBATCH_NAMES == expected_batches
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == expected_names
    assert tuple(
        len(source.names) for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    ) == BERTRAND_V8_EXPECTED_COUNTS == EXPECTED_SOURCE_COUNTS
    assert len(BERTRAND_V8_BODY_ENROLLMENT_MANIFEST) == 19
    assert tuple(
        source.module for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    ) == EXPECTED_SOURCE_MODULES
    assert tuple(
        source.factory for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    ) == tuple(f"make_{module}_theorems" for module in EXPECTED_SOURCE_MODULES)
    assert tuple(
        source.test_path for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    ) == tuple(
        f"peano-lab/py/tests/test_{module}.py"
        for module in EXPECTED_SOURCE_MODULES
    )
    assert all(
        source.origin is BertrandV8EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    )

    repository = Path(__file__).resolve().parents[3]
    assert BERTRAND_RFC_PATH == EXPECTED_RFC_PATH
    rfc_path = repository / BERTRAND_RFC_PATH
    assert rfc_path.is_file()
    assert sha256(rfc_path.read_bytes()).hexdigest() == EXPECTED_RFC_SHA256

    available = {entry.spec.name for entry in enrollment.parent_entries}
    for spec in enrollment.bertrand_specs:
        assert spec.name not in available
        assert set(spec.dependencies) <= available
        assert all("DNE" not in command for command in spec.script)
        assert (repository / enrollment.source_by_name[spec.name]).is_file()
        assert (repository / enrollment.test_by_name[spec.name]).is_file()
        assert enrollment.origin_by_name[spec.name].value == "bertrand"
        available.add(spec.name)


def test_v8_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v8.ALPHA_ENTRIES) == 1_055
    assert len({entry.spec.name for entry in v8.ALPHA_ENTRIES}) == 1_055
    assert (v8.ALPHA_EDITION.edge_count, v8.ALPHA_EDITION.layer_count) == (
        v8.EXPECTED_ALPHA_V8_EDGE_COUNT,
        v8.EXPECTED_ALPHA_V8_LAYER_COUNT,
    ) == (3_224, 45)
    depths = {
        name: v8.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V8_EXPECTED_NAMES
    }
    assert sha256(_compact(depths).encode()).hexdigest() == (
        EXPECTED_DEPTH_ROOT_SHA256
    )
    assert v8.ALPHA_V8_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v8.EXPECTED_ALPHA_V8_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v8.ALPHA_V8_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v8.EXPECTED_ALPHA_V8_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v8.ALPHA_ENTRIES) == {
        v8.Membership.STABLE: 432,
        v8.Membership.ALPHA_ONLY: 623,
    }
    assert Counter(entry.evidence for entry in v8.ALPHA_ENTRIES) == {
        v8.EvidenceStatus.STABLE_CLOSED: 432,
        v8.EvidenceStatus.ALPHA_CLOSED: 138,
        v8.EvidenceStatus.BODY_CHECKED: 484,
        v8.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }


def test_all_thirty_eight_v8_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v8_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    actual_root = sha256(_compact(payload).encode()).hexdigest()
    assert len(receipts) == 38
    if EXPECTED_BODY_RECEIPT_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v8 body-receipt bootstrap required: "
            f"root={actual_root}"
        )
    assert actual_root == EXPECTED_BODY_RECEIPT_ROOT_SHA256


def test_v8_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v8.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v8.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v8.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V8_EXPECTED_NAMES:
        assert v8.entry(name) is None
        item = v8.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v8.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v8.EnrollmentOrigin.BERTRAND
        assert item.provenance == (v8.EnrollmentOrigin.BERTRAND,)
        assert not item.checked_use
        with pytest.raises(v8.EditionV8ReplayError, match="body_checked"):
            v8.replay(name, edition="alpha")

    old = v8.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
