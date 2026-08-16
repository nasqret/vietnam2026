"""Runtime and evidence-boundary seals for Bertrand Alpha v11."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v10 as v10
from peano_lab.library import editions_v11 as v11
from peano_lab.library.alpha_enrollment_v11 import (
    BERTRAND_RFC_PATHS,
    BERTRAND_V11_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V11_EXPECTED_COUNT,
    BERTRAND_V11_EXPECTED_COUNTS,
    BERTRAND_V11_EXPECTED_MICROBATCH_SOURCE_COUNTS,
    BERTRAND_V11_EXPECTED_NAMES,
    BERTRAND_V11_MICROBATCH_COUNTS,
    BERTRAND_V11_MICROBATCH_NAMES,
    BERTRAND_V11_START_INDEX,
    PARENT_ALPHA_V10_COUNT,
    PARENT_ALPHA_V10_ENROLLMENT_SHA256,
    PARENT_ALPHA_V10_IDENTITY_SHA256,
    BertrandV11EnrollmentOrigin,
    alpha_v11_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36"
)
EXPECTED_IDENTITY_SHA256 = (
    "46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3"
)
EXPECTED_DEPTH_ROOT_SHA256 = (
    "cf5d550d5a3aa4af1debf9268eca578c30ca408058dcdeb35892bc705287214e"
)
EXPECTED_BODY_RECEIPT_ROOT_SHA256 = (
    "6c314d36cd7bb1e6cb5b213fec9bf9e04ab118e84121830b00c885ede2abac2a"
)
EXPECTED_RFC_SHA256 = {
    (
        "research/arithmetic-library/"
        "ha-bertrand-primorial-duplicate-free-tranche-rfc-v1.md"
    ): "855a80eb661535a5e3fcf57bfc7dce60cbbfbe640c9e5f2a300b508217621703",
    (
        "research/arithmetic-library/"
        "ha-bertrand-primorial-choose-interval-tranche-rfc-v1.md"
    ): "dda6a985f1a05de4a5e655e73dc06ff7682fb3d3a0a76e2025a4ac28d191a722",
    (
        "research/arithmetic-library/"
        "ha-bertrand-central-binomial-upper-tranche-rfc-v1.md"
    ): "1aad1afa2ce0d44c04dc32d4ef61d84dd311e216f188977980bc18d7820ff05d",
    (
        "research/arithmetic-library/"
        "ha-bertrand-primorial-four-power-tranche-rfc-v1.md"
    ): "5edd10d8f7b43ce503a926bce3a73d76bb48470bed9fcb4720927a3b9ea8a567",
    (
        "research/arithmetic-library/"
        "ha-bertrand-central-prime-support-tranche-rfc-v1.md"
    ): "709a4ad357529d7f41ec086db1fd27fc9e4277f1ed0680532a9cb20d1ad02de9",
}
EXPECTED_PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v10.json": (
        "46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3"
    ),
    "artifacts/peano-library/alpha/metrics-v10.json": (
        "63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v10.mmd": (
        "fdee73e6ea045c90afb7c024e8a209fbea8b03189538611c93678e4fa923aa76"
    ),
    "artifacts/peano-library/channels-v10.json": (
        "644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2"
    ),
}

EXPECTED_MICROBATCH_NAMES = (
    (
        "beta_distinct_empty",
        "beta_distinct_succ_intro",
        "beta_distinct_succ_elim_prefix",
        "beta_distinct_succ_last_ne",
        "beta_distinct_transport",
        "beta_distinct_prime_product_coprime_last",
        "beta_distinct_prime_product_divides_common_multiple",
        "beta_bounded_prime_prefix_divides_primorial_pointwise",
        "beta_distinct_bounded_prime_product_divides_primorial",
        "beta_distinct_bounded_prime_product_le_primorial",
        "factorial_prime_divides_of_le",
        "factorial_prime_le_of_divides",
        "choose_prime_divides_between",
        "beta_pairwise_coprime_product_divides_common_multiple",
        "primorial_interval_pairwise_coprime",
        "primorial_interval_divides_choose_between",
        "primorial_even_interval_divides_central",
        "primorial_odd_interval_divides_middle",
        "primorial_even_interval_le_central",
        "primorial_odd_interval_le_middle",
    ),
    (
        "central_binom_strong_upper_step",
        "central_binom_recurrence_double_bundle",
        "central_binom_strong_upper_of_laws",
        "central_binom_upper_support_package",
        "central_binom_strong_upper",
        "central_binom_odd_middle_le_four_pow",
        "primorial_one",
        "double_half_predecessor_data",
        "odd_positive_prefix_predecessor_bound",
        "central_binom_nonzero_strong_upper",
        "primorial_four_power_support_package",
        "primorial_le_four_pow_bounded",
        "primorial_le_four_pow",
        "central_binom_prime_divisor_le_double",
        "no_bertrand_central_prime_divisor_le",
        "power_valuation_nonzero_exponent_divides_base",
        "prime_divisor_power_valuation_nonzero",
        "no_bertrand_central_prime_divisor_ranges",
    ),
)
EXPECTED_SOURCE_COUNTS = (10, 10, 6, 7, 5)
EXPECTED_SOURCE_MODULES = (
    "bertrand_primorial_duplicate_free_candidate",
    "bertrand_primorial_choose_interval_candidate",
    "bertrand_central_binom_upper_candidate",
    "bertrand_primorial_four_power_candidate",
    "bertrand_central_binom_prime_support_candidate",
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v11_preserves_exact_v10_parent_stable_and_artifact_bytes() -> None:
    assert PARENT_ALPHA_V10_COUNT == len(v10.ALPHA_ENTRIES) == 1_085
    assert PARENT_ALPHA_V10_ENROLLMENT_SHA256 == v10.ALPHA_V10_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V10_IDENTITY_SHA256 == v10.ALPHA_V10_IDENTITY_SHA256
    parent = v11.ALPHA_ENTRIES[:PARENT_ALPHA_V10_COUNT]
    for old, new in zip(v10.ALPHA_ENTRIES, parent, strict=True):
        assert new is old
    assert v11.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v10.STABLE_SPECS)
    assert v11.STABLE_SPECS == v10.STABLE_SPECS
    assert v11.STABLE_EDITION.identity_sha256 == v10.STABLE_EDITION.identity_sha256
    assert v11.STABLE_EDITION.enrollment_identity_sha256 == (
        v10.STABLE_EDITION.enrollment_identity_sha256
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in EXPECTED_PARENT_ARTIFACT_SHA256
    } == EXPECTED_PARENT_ARTIFACT_SHA256


def test_v11_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v11_enrollment()
    expected_names = tuple(
        name for batch in EXPECTED_MICROBATCH_NAMES for name in batch
    )
    assert enrollment.parent_entries is v10.ALPHA_ENTRIES
    assert BERTRAND_V11_START_INDEX == 1_085
    assert BERTRAND_V11_EXPECTED_COUNT == len(expected_names) == 38
    assert BERTRAND_V11_EXPECTED_NAMES == expected_names
    assert BERTRAND_V11_MICROBATCH_COUNTS == (20, 18)
    assert BERTRAND_V11_EXPECTED_MICROBATCH_SOURCE_COUNTS == (2, 3)
    assert BERTRAND_V11_MICROBATCH_NAMES == EXPECTED_MICROBATCH_NAMES
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == expected_names
    assert tuple(
        len(source.names) for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    ) == BERTRAND_V11_EXPECTED_COUNTS == EXPECTED_SOURCE_COUNTS
    assert len(BERTRAND_V11_BODY_ENROLLMENT_MANIFEST) == 5
    assert tuple(
        source.module for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    ) == EXPECTED_SOURCE_MODULES
    assert tuple(
        source.factory for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    ) == tuple(f"make_{module}_theorems" for module in EXPECTED_SOURCE_MODULES)
    assert tuple(
        source.test_path for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    ) == tuple(
        f"peano-lab/py/tests/test_{module}.py" for module in EXPECTED_SOURCE_MODULES
    )
    assert tuple(
        dict.fromkeys(
            source.rfc_path
            for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
        )
    ) == BERTRAND_RFC_PATHS == tuple(EXPECTED_RFC_SHA256)
    assert all(
        source.origin is BertrandV11EnrollmentOrigin.BERTRAND
        for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    )

    repository = Path(__file__).resolve().parents[3]
    assert {
        path: sha256((repository / path).read_bytes()).hexdigest()
        for path in BERTRAND_RFC_PATHS
    } == EXPECTED_RFC_SHA256

    available = {entry.spec.name for entry in enrollment.parent_entries}
    for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST:
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


def test_v11_runtime_counts_topology_depths_and_identities_are_sealed() -> None:
    assert len(v11.ALPHA_ENTRIES) == 1_123
    assert len({entry.spec.name for entry in v11.ALPHA_ENTRIES}) == 1_123
    assert (v11.ALPHA_EDITION.edge_count, v11.ALPHA_EDITION.layer_count) == (
        v11.EXPECTED_ALPHA_V11_EDGE_COUNT,
        v11.EXPECTED_ALPHA_V11_LAYER_COUNT,
    ) == (3_482, 45)
    depths = {
        name: v11.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_V11_EXPECTED_NAMES
    }
    actual_depth_root = sha256(_compact(depths).encode()).hexdigest()
    if EXPECTED_DEPTH_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v11 depth-root bootstrap required: "
            f"root={actual_depth_root}"
        )
    assert actual_depth_root == EXPECTED_DEPTH_ROOT_SHA256
    assert v11.ALPHA_V11_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v11.EXPECTED_ALPHA_V11_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v11.ALPHA_V11_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v11.EXPECTED_ALPHA_V11_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v11.ALPHA_ENTRIES) == {
        v11.Membership.STABLE: 432,
        v11.Membership.ALPHA_ONLY: 691,
    }
    assert Counter(entry.evidence for entry in v11.ALPHA_ENTRIES) == {
        v11.EvidenceStatus.STABLE_CLOSED: 432,
        v11.EvidenceStatus.ALPHA_CLOSED: 138,
        v11.EvidenceStatus.BODY_CHECKED: 552,
        v11.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    origins = Counter(entry.enrollment_origin for entry in v11.ALPHA_ENTRIES)
    assert origins[v11.EnrollmentOrigin.BERTRAND] == 158
    assert sum(origins.values()) == 1_123


def test_all_thirty_eight_v11_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v11_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    payload = {receipt.name: asdict(receipt) for receipt in receipts}
    actual_root = sha256(_compact(payload).encode()).hexdigest()
    assert len(receipts) == 38
    if EXPECTED_BODY_RECEIPT_ROOT_SHA256.startswith("UNSEALED_"):
        pytest.fail(
            "Alpha v11 body-receipt bootstrap required: "
            f"root={actual_root}"
        )
    assert actual_root == EXPECTED_BODY_RECEIPT_ROOT_SHA256


def test_v11_checked_use_boundary_refuses_every_appended_row() -> None:
    assert len(v11.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v11.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v11.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_V11_EXPECTED_NAMES:
        assert v11.entry(name) is None
        item = v11.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v11.EvidenceStatus.BODY_CHECKED
        assert item.enrollment_origin is v11.EnrollmentOrigin.BERTRAND
        assert item.provenance == (v11.EnrollmentOrigin.BERTRAND,)
        assert not item.checked_use
        with pytest.raises(v11.EditionV11ReplayError, match="body_checked"):
            v11.replay(name, edition="alpha")

    old = v11.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
