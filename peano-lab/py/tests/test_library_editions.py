"""Focused seals for the canonical Stable/Alpha theorem editions."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library.alpha_enrollment import (
    HA_QR_COMPATIBLE_OVERLAP,
    alpha_enrollment,
)
from peano_lab.library.editions import (
    ALPHA_CHECKED_SPECS,
    ALPHA_EDITION,
    ALPHA_ENROLLMENT_SHA256,
    ALPHA_ENTRIES,
    ALPHA_QR_ROOT_NAME,
    ALPHA_SPECS,
    STABLE_EDITION,
    STABLE_SPECS,
    EditionName,
    EditionReplayError,
    EnrollmentOrigin,
    EvidenceStatus,
    Membership,
    edition,
    entry,
    replay,
)
from peano_lab.library.theorems import THEOREMS


EXPECTED_ENROLLMENT_SHA256 = (
    "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
)
EXPECTED_ALPHA_IDENTITY_SHA256 = (
    "b464c50cced007f06aa7bdf0d61ad6687a09c0e5bfb5c29f1879ffc68b016588"
)


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
        for item in ALPHA_ENTRIES
    )
    return sha256("\x1c".join(rows).encode("utf-8")).hexdigest()


def test_stable_is_unchanged_and_alpha_has_exact_cumulative_topology() -> None:
    assert STABLE_SPECS is THEOREMS
    assert edition() is STABLE_EDITION
    assert edition(EditionName.STABLE) is STABLE_EDITION
    assert edition("alpha") is ALPHA_EDITION
    assert (len(STABLE_SPECS), STABLE_EDITION.edge_count) == (432, 1_185)
    assert STABLE_EDITION.layer_count == 22

    assert ALPHA_SPECS[:432] == STABLE_SPECS
    assert (len(ALPHA_SPECS), ALPHA_EDITION.edge_count) == (885, 2_641)
    assert ALPHA_EDITION.layer_count == 45
    assert len({spec.name for spec in ALPHA_SPECS}) == len(ALPHA_SPECS)
    positions = {spec.name: index for index, spec in enumerate(ALPHA_SPECS)}
    for spec in ALPHA_SPECS:
        assert all(
            positions[dependency] < positions[spec.name]
            for dependency in spec.dependencies
        )

    assert positions[ALPHA_QR_ROOT_NAME] == 747
    assert ALPHA_SPECS[-1].name == "cell_list_extensional"
    assert _enrollment_sha256() == EXPECTED_ENROLLMENT_SHA256
    assert ALPHA_ENROLLMENT_SHA256 == EXPECTED_ENROLLMENT_SHA256
    assert ALPHA_EDITION.enrollment_identity_sha256 == EXPECTED_ENROLLMENT_SHA256
    assert ALPHA_EDITION.identity_sha256 == EXPECTED_ALPHA_IDENTITY_SHA256


def test_alpha_membership_origin_and_evidence_are_independent_and_exact() -> None:
    assert Counter(item.membership for item in ALPHA_ENTRIES) == {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 453,
    }
    assert Counter(item.enrollment_origin for item in ALPHA_ENTRIES) == {
        EnrollmentOrigin.STABLE: 432,
        EnrollmentOrigin.QR: 316,
        EnrollmentOrigin.HA: 120,
        EnrollmentOrigin.K3B: 17,
    }
    origins = tuple(item.enrollment_origin for item in ALPHA_ENTRIES)
    assert origins[:432] == (EnrollmentOrigin.STABLE,) * 432
    assert origins[432:748] == (EnrollmentOrigin.QR,) * 316
    assert origins[748:868] == (EnrollmentOrigin.HA,) * 120
    assert origins[868:] == (EnrollmentOrigin.K3B,) * 17
    assert Counter(item.evidence for item in ALPHA_ENTRIES) == {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 314,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    assert len(ALPHA_CHECKED_SPECS) == 570
    assert sum(len(spec.dependencies) for spec in ALPHA_CHECKED_SPECS) == 1_485
    checked_names = {spec.name for spec in ALPHA_CHECKED_SPECS}
    assert all(
        set(spec.dependencies) <= checked_names for spec in ALPHA_CHECKED_SPECS
    )

    root = entry(ALPHA_QR_ROOT_NAME, edition="alpha")
    assert root is not None
    assert root.membership is Membership.ALPHA_ONLY
    assert root.enrollment_origin is EnrollmentOrigin.QR
    assert root.evidence is EvidenceStatus.PENDING_LAYERED_CLOSURE
    assert not root.checked_use


def test_compatible_qr_ha_overlap_retains_position_origin_and_both_sources() -> None:
    enrollment = alpha_enrollment()
    qr_spec = next(
        spec
        for spec in enrollment.qr_specs
        if spec.name == HA_QR_COMPATIBLE_OVERLAP
    )
    ha_spec = next(
        spec
        for spec in enrollment.ha_specs
        if spec.name == HA_QR_COMPATIBLE_OVERLAP
    )
    assert qr_spec == ha_spec

    overlap = entry(HA_QR_COMPATIBLE_OVERLAP, edition="alpha")
    assert overlap is not None
    assert overlap.spec == qr_spec
    assert overlap.membership is Membership.ALPHA_ONLY
    assert overlap.enrollment_origin is EnrollmentOrigin.QR
    assert overlap.provenance == (EnrollmentOrigin.QR, EnrollmentOrigin.HA)
    assert overlap.evidence is EvidenceStatus.ALPHA_CLOSED
    assert overlap.checked_use
    assert ALPHA_SPECS.index(overlap.spec) == 646

    repository = Path(__file__).resolve().parents[3]
    assert overlap.source_module.endswith("finite_sum_pointwise_mod_candidate.py")
    assert (repository / overlap.source_module).is_file()
    for item in ALPHA_ENTRIES:
        assert (repository / item.source_module).is_file()


def test_alpha_replay_refuses_body_only_and_pending_rows_before_execution() -> None:
    body_only = alpha_enrollment().qr_specs[0]
    body_entry = entry(body_only.name, edition="alpha")
    assert body_entry is not None
    assert body_entry.evidence is EvidenceStatus.BODY_CHECKED
    with pytest.raises(EditionReplayError, match="body_checked"):
        replay(body_only.name, edition="alpha")
    with pytest.raises(EditionReplayError, match="pending_layered_closure"):
        replay(ALPHA_QR_ROOT_NAME, edition="alpha")
    assert entry(body_only.name) is None


def test_alpha_replay_closes_and_checks_a_multi_dependency_alpha_row() -> None:
    item = entry("dt_shell_successor", edition="alpha")
    assert item is not None
    assert item.evidence is EvidenceStatus.ALPHA_CLOSED
    assert item.spec.dependencies == ("mul_succ_left", "add_assoc", "add_comm")
    checked = replay(item.spec.name, edition="alpha")
    assert checked.spec == item.spec
    assert check((), checked.certificate, checked.formula)
    assert replay(item.spec.name.upper(), edition="ALPHA") is checked
