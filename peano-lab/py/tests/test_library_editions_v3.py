"""Runtime and evidence-boundary seals for the Bertrand Alpha-v3 append."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.library import editions_v2 as v2
from peano_lab.library import editions_v3 as v3
from peano_lab.library.alpha_enrollment_v3 import (
    BERTRAND_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_EXPECTED_COUNT,
    BERTRAND_EXPECTED_NAMES,
    BERTRAND_RFC_PATH,
    BERTRAND_START_INDEX,
    PARENT_ALPHA_V2_COUNT,
    PARENT_ALPHA_V2_ENROLLMENT_SHA256,
    PARENT_ALPHA_V2_IDENTITY_SHA256,
    BertrandEnrollmentOrigin,
    alpha_v3_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ENROLLMENT_SHA256 = (
    "4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4"
)
EXPECTED_IDENTITY_SHA256 = (
    "e20eefac839fb2bcd3e696989c091a5f6837de04824f94e1073723851a471a2f"
)
EXPECTED_DEPTHS = {
    "prime_strictly_above_decidable": 9,
    "bounded_prime_interval_search": 10,
    "prime_interval_exclusion_refutes_witness": 0,
    "bounded_prime_interval_decidable": 11,
    "mul_le_mul": 6,
    "le_mul_of_one_le_right": 3,
    "le_mul_of_one_le_left": 6,
    "pow_base_monotone": 8,
    "one_le_pow": 8,
    "pow_nonzero_of_one_le": 9,
    "pow_exponent_monotone": 20,
    "power_divides_decidable": 20,
    "power_divides_zero": 20,
    "bounded_power_valuation_search": 21,
    "bounded_power_valuation_exists": 22,
    "power_valuation_exists": 23,
    "power_valuation_functional": 4,
    "power_valuation_power_divides": 0,
    "power_valuation_dominates": 0,
    "prime_power_valuation_exists": 24,
    "prime_power_valuation_functional": 5,
}
EXPECTED_BODY_RECEIPTS = {
    "prime_strictly_above_decidable": (5, 38, 107, 33, 107, 106, 0),
    "bounded_prime_interval_search": (7, 68, 95, 25, 95, 94, 0),
    "prime_interval_exclusion_refutes_witness": (0, 13, 33, 19, 33, 32, 0),
    "bounded_prime_interval_decidable": (2, 18, 19, 12, 19, 18, 0),
    "mul_le_mul": (3, 24, 27, 16, 27, 26, 0),
    "le_mul_of_one_le_right": (2, 12, 14, 11, 14, 13, 0),
    "le_mul_of_one_le_left": (2, 12, 14, 11, 14, 13, 0),
    "pow_base_monotone": (4, 68, 90, 28, 90, 89, 0),
    "one_le_pow": (5, 46, 61, 22, 61, 60, 0),
    "pow_nonzero_of_one_le": (2, 17, 21, 16, 21, 20, 0),
    "pow_exponent_monotone": (5, 47, 55, 30, 55, 54, 0),
    "power_divides_decidable": (3, 33, 38, 20, 38, 37, 0),
    "power_divides_zero": (3, 22, 26, 18, 26, 25, 0),
    "bounded_power_valuation_search": (6, 122, 162, 28, 162, 161, 0),
    "bounded_power_valuation_exists": (3, 24, 28, 14, 28, 27, 0),
    "power_valuation_exists": (1, 6, 16, 10, 16, 15, 0),
    "power_valuation_functional": (1, 25, 34, 14, 34, 33, 0),
    "power_valuation_power_divides": (0, 7, 21, 13, 21, 20, 0),
    "power_valuation_dominates": (0, 12, 24, 16, 24, 23, 0),
    "prime_power_valuation_exists": (1, 15, 15, 10, 15, 14, 0),
    "prime_power_valuation_functional": (1, 15, 44, 26, 44, 43, 0),
}


def _enrollment_sha256() -> str:
    rows = (
        "\x1f".join(
            (
                item.enrollment_origin.value,
                item.spec.name,
                item.spec.statement,
                "\x1e".join(item.spec.dependencies),
                "\x1e".join(item.spec.script),
            )
        )
        for item in v3.ALPHA_ENTRIES
    )
    return sha256("\x1c".join(rows).encode("utf-8")).hexdigest()


def test_v3_preserves_exact_v2_parent_and_stable_release() -> None:
    assert PARENT_ALPHA_V2_COUNT == len(v2.ALPHA_ENTRIES) == 902
    assert PARENT_ALPHA_V2_ENROLLMENT_SHA256 == v2.ALPHA_V2_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V2_IDENTITY_SHA256 == v2.ALPHA_V2_IDENTITY_SHA256
    parent = v3.ALPHA_ENTRIES[:PARENT_ALPHA_V2_COUNT]
    for old, new in zip(v2.ALPHA_ENTRIES, parent, strict=True):
        assert new.spec is old.spec
        assert new.membership is old.membership
        assert new.evidence is old.evidence
        assert new.enrollment_origin.value == old.enrollment_origin.value
        assert tuple(item.value for item in new.provenance) == tuple(
            item.value for item in old.provenance
        )
        assert new.source_module == old.source_module
    assert v3.STABLE_RELEASE_ORDER == tuple(spec.name for spec in v2.STABLE_SPECS)
    assert v3.STABLE_SPECS == v2.STABLE_SPECS
    assert v3.STABLE_EDITION.identity_sha256 == v2.STABLE_EDITION.identity_sha256
    assert v3.STABLE_EDITION.enrollment_identity_sha256 == (
        v2.STABLE_EDITION.enrollment_identity_sha256
    )


def test_v3_manifest_is_exact_ordered_topological_and_evidence_bound() -> None:
    enrollment = alpha_v3_enrollment()
    assert enrollment.parent_entries is v2.ALPHA_ENTRIES
    assert BERTRAND_START_INDEX == 902
    assert BERTRAND_EXPECTED_COUNT == len(BERTRAND_EXPECTED_NAMES) == 21
    assert tuple(spec.name for spec in enrollment.bertrand_specs) == (
        BERTRAND_EXPECTED_NAMES
    )
    assert tuple(len(source.names) for source in BERTRAND_BODY_ENROLLMENT_MANIFEST) == (
        4,
        4,
        3,
        10,
    )
    assert tuple(source.origin for source in BERTRAND_BODY_ENROLLMENT_MANIFEST) == (
        BertrandEnrollmentOrigin.B0_INTERVAL,
        BertrandEnrollmentOrigin.B1_POWER_ORDER,
        BertrandEnrollmentOrigin.B1_POWER_GROWTH,
        BertrandEnrollmentOrigin.B2_BOUNDED_VALUATION,
    )
    repository = Path(__file__).resolve().parents[3]
    assert (repository / BERTRAND_RFC_PATH).is_file()
    available = {entry.spec.name for entry in enrollment.parent_entries}
    for spec in enrollment.bertrand_specs:
        assert spec.name not in available
        assert set(spec.dependencies) <= available
        assert "DNE" not in spec.script
        assert (repository / enrollment.source_by_name[spec.name]).is_file()
        assert (repository / enrollment.test_by_name[spec.name]).is_file()
        available.add(spec.name)


def test_v3_runtime_counts_topology_and_identities_are_sealed() -> None:
    assert len(v3.ALPHA_ENTRIES) == 923
    assert len({entry.spec.name for entry in v3.ALPHA_ENTRIES}) == 923
    assert (v3.ALPHA_EDITION.edge_count, v3.ALPHA_EDITION.layer_count) == (
        2730,
        45,
    )
    assert {
        name: v3.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in BERTRAND_EXPECTED_NAMES
    } == EXPECTED_DEPTHS
    assert _enrollment_sha256() == EXPECTED_ENROLLMENT_SHA256
    assert v3.ALPHA_V3_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v3.EXPECTED_ALPHA_V3_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert v3.ALPHA_V3_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert v3.EXPECTED_ALPHA_V3_IDENTITY_SHA256 == EXPECTED_IDENTITY_SHA256
    assert Counter(entry.membership for entry in v3.ALPHA_ENTRIES) == {
        v3.Membership.STABLE: 432,
        v3.Membership.ALPHA_ONLY: 491,
    }
    assert Counter(entry.evidence for entry in v3.ALPHA_ENTRIES) == {
        v3.EvidenceStatus.STABLE_CLOSED: 432,
        v3.EvidenceStatus.ALPHA_CLOSED: 138,
        v3.EvidenceStatus.BODY_CHECKED: 352,
        v3.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }


def test_all_twenty_one_bertrand_bodies_have_exact_kernel_receipts() -> None:
    enrollment = alpha_v3_enrollment()
    core = {entry.spec.name: entry.spec for entry in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.bertrand_specs, core=core)
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS


def test_v3_checked_use_boundary_refuses_every_bertrand_row() -> None:
    assert len(v3.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v3.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in v3.ALPHA_CHECKED_SPECS
    )
    for name in BERTRAND_EXPECTED_NAMES:
        assert v3.entry(name) is None
        item = v3.entry(name, edition="alpha")
        assert item is not None
        assert item.evidence is v3.EvidenceStatus.BODY_CHECKED
        assert not item.checked_use
        with pytest.raises(v3.EditionV3ReplayError, match="body_checked"):
            v3.replay(name, edition="alpha")

    old = v3.replay("add_comm", edition="alpha")
    assert old.spec.name == "add_comm"
