"""Focused runtime seals for the versioned K3C Alpha v2 append."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library import editions as v1
from peano_lab.library import editions_v2 as v2
from peano_lab.library.alpha_enrollment_v2 import (
    K3C_BODY_ENROLLMENT_MANIFEST,
    K3C_EXPECTED_COUNT,
    K3C_EXPECTED_NAMES,
    K3C_START_INDEX,
    PARENT_ALPHA_V1_COUNT,
    PARENT_ALPHA_V1_ENROLLMENT_SHA256,
    PARENT_ALPHA_V1_IDENTITY_SHA256,
    alpha_v2_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies


EXPECTED_ALPHA_V2_ENROLLMENT_SHA256 = (
    "00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe"
)
EXPECTED_ALPHA_V2_IDENTITY_SHA256 = (
    "aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4"
)
EXPECTED_K3C_DEPTHS = {
    "cell_list_valid_nil": 2,
    "cell_list_valid_cell_intro": 19,
    "cell_list_valid_cases": 19,
    "cell_list_valid_cell_elim": 20,
    "list_at_implies_cell_list_valid": 1,
    "list_member_implies_cell_list_valid": 2,
    "list_member_nil_false": 20,
    "list_member_cell_intro_head": 19,
    "list_member_cell_intro_tail": 19,
    "list_member_cell_elim": 19,
    "list_member_cell_iff": 20,
    "list_member_pointwise_transport": 21,
    "list_at_exists_unique": 20,
    "cell_list_nonempty_iff_head_exists": 19,
    "cell_list_code_eq_lookup_values": 20,
    "cell_list_code_eq_iff_pointwise": 21,
    "cell_list_decompose_unique": 19,
}
EXPECTED_BODY_RECEIPTS = {
    "cell_list_valid_nil": (1, 4, 5, 5, 5, 4, 0),
    "cell_list_valid_cell_intro": (1, 18, 19, 13, 19, 18, 0),
    "cell_list_valid_cases": (2, 35, 41, 22, 41, 40, 0),
    "cell_list_valid_cell_elim": (3, 33, 56, 23, 56, 55, 0),
    "list_at_implies_cell_list_valid": (1, 14, 15, 11, 15, 14, 0),
    "list_member_implies_cell_list_valid": (1, 9, 21, 13, 21, 20, 0),
    "list_member_nil_false": (5, 33, 41, 19, 41, 40, 0),
    "list_member_cell_intro_head": (1, 18, 19, 13, 19, 18, 0),
    "list_member_cell_intro_tail": (1, 20, 21, 15, 21, 20, 0),
    "list_member_cell_elim": (3, 77, 100, 41, 100, 99, 0),
    "list_member_cell_iff": (3, 32, 79, 23, 79, 78, 0),
    "list_member_pointwise_transport": (2, 37, 71, 25, 71, 70, 0),
    "list_at_exists_unique": (2, 25, 30, 19, 30, 29, 0),
    "cell_list_nonempty_iff_head_exists": (2, 38, 46, 14, 46, 45, 0),
    "cell_list_code_eq_lookup_values": (1, 17, 40, 24, 40, 39, 0),
    "cell_list_code_eq_iff_pointwise": (2, 30, 62, 29, 62, 61, 0),
    "cell_list_decompose_unique": (2, 29, 36, 22, 36, 35, 0),
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
        for item in v2.ALPHA_ENTRIES
    )
    return sha256("\x1c".join(rows).encode("utf-8")).hexdigest()


def test_v2_preserves_the_exact_v1_parent_and_stable_release() -> None:
    assert PARENT_ALPHA_V1_COUNT == len(v1.ALPHA_ENTRIES) == 885
    assert PARENT_ALPHA_V1_ENROLLMENT_SHA256 == (
        "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
    )
    assert v1.ALPHA_ENROLLMENT_SHA256 == PARENT_ALPHA_V1_ENROLLMENT_SHA256
    assert PARENT_ALPHA_V1_IDENTITY_SHA256 == (
        "b464c50cced007f06aa7bdf0d61ad6687a09c0e5bfb5c29f1879ffc68b016588"
    )
    assert v1.ALPHA_EDITION.identity_sha256 == PARENT_ALPHA_V1_IDENTITY_SHA256

    parent = v2.ALPHA_ENTRIES[:PARENT_ALPHA_V1_COUNT]
    assert len(parent) == len(v1.ALPHA_ENTRIES)
    for old, new in zip(v1.ALPHA_ENTRIES, parent, strict=True):
        assert new.spec is old.spec
        assert new.membership is old.membership
        assert new.evidence is old.evidence
        assert new.enrollment_origin.value == old.enrollment_origin.value
        assert tuple(item.value for item in new.provenance) == tuple(
            item.value for item in old.provenance
        )
        assert new.source_module == old.source_module

    assert v2.STABLE_RELEASE_ORDER == tuple(
        spec.name for spec in v1.STABLE_SPECS
    )
    assert v2.STABLE_SPECS == v1.STABLE_SPECS
    assert (len(v2.STABLE_SPECS), v2.STABLE_EDITION.edge_count) == (432, 1_185)
    assert v2.STABLE_EDITION.layer_count == 22
    assert v2.STABLE_EDITION.enrollment_identity_sha256 == (
        v1.STABLE_EDITION.enrollment_identity_sha256
    )
    assert v2.STABLE_EDITION.identity_sha256 == (
        v1.STABLE_EDITION.identity_sha256
    )


def test_v2_has_the_exact_cumulative_topology_counts_and_identities() -> None:
    assert len(v2.ALPHA_ENTRIES) == 902
    assert len({item.spec.name for item in v2.ALPHA_ENTRIES}) == 902
    assert (v2.ALPHA_EDITION.edge_count, v2.ALPHA_EDITION.layer_count) == (
        2_674,
        45,
    )
    positions = {
        item.spec.name: index for index, item in enumerate(v2.ALPHA_ENTRIES)
    }
    for item in v2.ALPHA_ENTRIES:
        assert all(
            positions[dependency] < positions[item.spec.name]
            for dependency in item.spec.dependencies
        )
    assert {
        name: v2.ALPHA_EDITION.dependency_depth_by_name[name]
        for name in K3C_EXPECTED_NAMES
    } == EXPECTED_K3C_DEPTHS

    assert _enrollment_sha256() == EXPECTED_ALPHA_V2_ENROLLMENT_SHA256
    assert (
        v2.EXPECTED_ALPHA_V2_ENROLLMENT_SHA256
        == EXPECTED_ALPHA_V2_ENROLLMENT_SHA256
    )
    assert v2.ALPHA_V2_ENROLLMENT_SHA256 == (
        EXPECTED_ALPHA_V2_ENROLLMENT_SHA256
    )
    assert v2.EXPECTED_ALPHA_V2_IDENTITY_SHA256 == (
        EXPECTED_ALPHA_V2_IDENTITY_SHA256
    )
    assert v2.ALPHA_V2_IDENTITY_SHA256 == EXPECTED_ALPHA_V2_IDENTITY_SHA256
    assert Counter(item.membership for item in v2.ALPHA_ENTRIES) == {
        v2.Membership.STABLE: 432,
        v2.Membership.ALPHA_ONLY: 470,
    }
    assert Counter(item.evidence for item in v2.ALPHA_ENTRIES) == {
        v2.EvidenceStatus.STABLE_CLOSED: 432,
        v2.EvidenceStatus.ALPHA_CLOSED: 138,
        v2.EvidenceStatus.BODY_CHECKED: 331,
        v2.EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    assert Counter(item.enrollment_origin for item in v2.ALPHA_ENTRIES) == {
        v2.EnrollmentOrigin.STABLE: 432,
        v2.EnrollmentOrigin.QR: 316,
        v2.EnrollmentOrigin.HA: 120,
        v2.EnrollmentOrigin.K3B: 17,
        v2.EnrollmentOrigin.K3C: 17,
    }


def test_v2_manifest_and_k3c_append_are_exact_disjoint_and_body_only() -> None:
    assert K3C_EXPECTED_COUNT == len(K3C_EXPECTED_NAMES) == 17
    assert K3C_START_INDEX == 885
    assert tuple(
        (source.module, source.factory, source.names)
        for source in K3C_BODY_ENROLLMENT_MANIFEST
    ) == (
        (
            "ha_cell_list_validity_candidate",
            "make_ha_cell_list_validity_candidate_theorems",
            K3C_EXPECTED_NAMES[:5],
        ),
        (
            "ha_cell_list_membership_candidate",
            "make_ha_cell_list_membership_candidate_theorems",
            K3C_EXPECTED_NAMES[5:12],
        ),
        (
            "ha_cell_list_interface_candidate",
            "make_ha_cell_list_interface_candidate_theorems",
            K3C_EXPECTED_NAMES[12:],
        ),
    )

    enrollment = alpha_v2_enrollment()
    assert enrollment.parent_entries is v1.ALPHA_ENTRIES
    assert tuple(spec.name for spec in enrollment.k3c_specs) == (
        K3C_EXPECTED_NAMES
    )
    assert not (
        set(K3C_EXPECTED_NAMES)
        & {item.spec.name for item in enrollment.parent_entries}
    )
    tail = v2.ALPHA_ENTRIES[K3C_START_INDEX:]
    assert tuple(item.spec.name for item in tail) == K3C_EXPECTED_NAMES
    repository = Path(__file__).resolve().parents[3]
    for item in tail:
        assert item.membership is v2.Membership.ALPHA_ONLY
        assert item.evidence is v2.EvidenceStatus.BODY_CHECKED
        assert not item.checked_use
        assert item.enrollment_origin is v2.EnrollmentOrigin.K3C
        assert item.provenance == (v2.EnrollmentOrigin.K3C,)
        assert item.source_module == enrollment.source_by_name[item.spec.name]
        assert (repository / item.source_module).is_file()


def test_all_seventeen_k3c_bodies_have_exact_kernel_checked_receipts() -> None:
    enrollment = alpha_v2_enrollment()
    core = {item.spec.name: item.spec for item in enrollment.parent_entries}
    receipts = replay_candidate_bodies(enrollment.k3c_specs, core=core)
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


def test_v2_checked_use_boundary_refuses_body_and_pending_rows() -> None:
    assert len(v2.ALPHA_CHECKED_SPECS) == 570
    checked_names = {spec.name for spec in v2.ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names
        for spec in v2.ALPHA_CHECKED_SPECS
    )
    for name in K3C_EXPECTED_NAMES:
        assert v2.entry(name) is None
        with pytest.raises(v2.EditionV2ReplayError, match="body_checked"):
            v2.replay(name, edition="alpha")
    with pytest.raises(
        v2.EditionV2ReplayError, match="pending_layered_closure"
    ):
        v2.replay(v1.ALPHA_QR_ROOT_NAME, edition="alpha")

    item = v2.entry("dt_shell_successor", edition="alpha")
    assert item is not None
    assert item.evidence is v2.EvidenceStatus.ALPHA_CLOSED
    assert item.spec.dependencies == (
        "mul_succ_left",
        "add_assoc",
        "add_comm",
    )
    checked = v2.replay(item.spec.name, edition="alpha")
    assert checked.spec == item.spec
    assert check((), checked.certificate, checked.formula)
