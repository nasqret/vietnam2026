"""Fail-closed Alpha-v13 release of constructive Lagrange and Lucas bodies.

The complete 1,303-row Alpha-v12 ledger remains an object-identical immutable
prefix.  The exact 196-row Lagrange and 44-row Lucas dependency closures are
Alpha-only ``body_checked`` entries: membership does not confer empty-context
closure or checked theorem use.  The sealed 432-row Stable edition is unchanged.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from . import editions_v12 as v12
from .alpha_enrollment_v13 import (
    FOUR_SQUARE_V13_EXPECTED_COUNT,
    FRONTIER_V13_EXPECTED_COUNT,
    FRONTIER_V13_EXPECTED_NAMES,
    FRONTIER_V13_ROOT_NAMES,
    FRONTIER_V13_START_INDEX,
    LUCAS_V13_EXPECTED_COUNT,
    PARENT_ALPHA_V12_COUNT,
    PARENT_ALPHA_V12_ENROLLMENT_SHA256,
    PARENT_ALPHA_V12_IDENTITY_SHA256,
    alpha_v13_enrollment,
)
from .editions_v5 import _enrollment_identity, _identity, _make_edition
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v12.EditionName
Membership = v12.Membership
EvidenceStatus = v12.EvidenceStatus
EnrollmentOrigin = v12.EnrollmentOrigin
EditionEntry = v12.EditionEntry
LibraryEdition = v12.LibraryEdition


class EditionV13Error(ValueError):
    """An Alpha-v13 manifest, topology, evidence label, or lookup is invalid."""


class EditionV13ReplayError(EditionV13Error):
    """A v13 theorem is absent or lacks actual empty-context closure evidence."""


def dependency_depths(specs):
    return v12.dependency_depths(specs)


def dependency_layers(specs):
    return v12.dependency_layers(specs)


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_v13_enrollment()
    result = list(enrollment.parent_entries)
    for spec in enrollment.frontier_specs:
        result.append(
            EditionEntry(
                spec=spec,
                membership=Membership.ALPHA_ONLY,
                evidence=EvidenceStatus.BODY_CHECKED,
                enrollment_origin=EnrollmentOrigin.HA,
                provenance=(EnrollmentOrigin.HA,),
                source_module=enrollment.source_by_name[spec.name],
            )
        )
    return tuple(result)


ALPHA_ENTRIES: tuple[EditionEntry, ...] = _alpha_entries()
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(entry.spec for entry in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in ALPHA_ENTRIES if entry.checked_use
)

STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(spec.name for spec in v12.STABLE_SPECS)
STABLE_ENTRIES: tuple[EditionEntry, ...] = v12.STABLE_ENTRIES
STABLE_SPECS: tuple[TheoremSpec, ...] = v12.STABLE_SPECS
STABLE_EDITION = v12.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)

ALPHA_V13_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V13_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V13_ENROLLMENT_SHA256

EXPECTED_ALPHA_V13_COUNT = 1_543
EXPECTED_ALPHA_V13_EDGE_COUNT = 5_189
EXPECTED_ALPHA_V13_LAYER_COUNT = 45
EXPECTED_ALPHA_V13_ENROLLMENT_SHA256 = (
    "6b223edfe6a2e02dc09576671f4fc5f5a41aaf4156f829164222dd3e494da22f"
)
EXPECTED_ALPHA_V13_IDENTITY_SHA256 = (
    "a010e0ee5dece0d3325e8ec084c1f8769ef8e9ca47e2de891d344e54c1b439d1"
)


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V13_COUNT
        or len(ALPHA_ENTRIES)
        != PARENT_ALPHA_V12_COUNT + FRONTIER_V13_EXPECTED_COUNT
    ):
        raise EditionV13Error("Alpha-v13 theorem count changed")
    if tuple(entry.spec.name for entry in ALPHA_ENTRIES[FRONTIER_V13_START_INDEX:]) != (
        FRONTIER_V13_EXPECTED_NAMES
    ):
        raise EditionV13Error("Alpha-v13 exact minimal append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V12_COUNT]
    if parent != v12.ALPHA_ENTRIES or any(
        newer is not older for newer, older in zip(parent, v12.ALPHA_ENTRIES, strict=True)
    ):
        raise EditionV13Error("Alpha-v13 no longer preserves exact Alpha-v12 objects")
    if _enrollment_identity(parent) != PARENT_ALPHA_V12_ENROLLMENT_SHA256:
        raise EditionV13Error("Alpha-v13 changed its sealed Alpha-v12 parent ledger")
    if _identity(EditionName.ALPHA, parent) != PARENT_ALPHA_V12_IDENTITY_SHA256:
        raise EditionV13Error("Alpha-v13 changed sealed Alpha-v12 edition metadata")
    if (
        STABLE_EDITION is not v12.STABLE_EDITION
        or STABLE_ENTRIES is not v12.STABLE_ENTRIES
        or STABLE_SPECS is not v12.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV13Error("Alpha-v13 changed the sealed Stable release")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V13_EDGE_COUNT,
        EXPECTED_ALPHA_V13_LAYER_COUNT,
    ):
        raise EditionV13Error("Alpha-v13 dependency topology seal changed")
    if ALPHA_V13_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V13_ENROLLMENT_SHA256:
        raise EditionV13Error("Alpha-v13 ordered enrollment identity changed")
    if ALPHA_V13_IDENTITY_SHA256 != EXPECTED_ALPHA_V13_IDENTITY_SHA256:
        raise EditionV13Error("Alpha-v13 edition identity changed")
    if Counter(entry.membership for entry in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 1_111,
    }:
        raise EditionV13Error("Alpha-v13 release-membership counts changed")
    if Counter(entry.evidence for entry in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 972,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }:
        raise EditionV13Error("Alpha-v13 evidence counts changed")
    if ALPHA_CHECKED_SPECS != v12.ALPHA_CHECKED_SPECS or len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV13Error("Alpha-v13 body-only append changed checked theorem use")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV13Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[FRONTIER_V13_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.checked_use
            or entry.enrollment_origin is not EnrollmentOrigin.HA
            or entry.provenance != (EnrollmentOrigin.HA,)
        ):
            raise EditionV13Error("Alpha-v13 frontier body-only evidence boundary changed")
    if (
        ALPHA_ENTRIES[
            FRONTIER_V13_START_INDEX + FOUR_SQUARE_V13_EXPECTED_COUNT - 1
        ].spec.name
        != FRONTIER_V13_ROOT_NAMES[0]
        or ALPHA_ENTRIES[-1].spec.name != FRONTIER_V13_ROOT_NAMES[1]
        or LUCAS_V13_EXPECTED_COUNT != 44
    ):
        raise EditionV13Error("Alpha-v13 exact campaign root boundaries changed")


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV13Error(f"unknown theorem-library v13 edition {value!r}")


def edition(name: EditionName | str = EditionName.STABLE) -> LibraryEdition:
    selected = _coerce_edition(name)
    return STABLE_EDITION if selected is EditionName.STABLE else ALPHA_EDITION


def entry(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> EditionEntry | None:
    if not isinstance(name, str):
        return None
    selected = globals()["edition"](edition)
    return selected.by_name.get(name.strip()) or next(
        (
            item
            for item in selected.entries
            if item.spec.name.casefold() == name.strip().casefold()
        ),
        None,
    )


@lru_cache(maxsize=None)
def replay(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    selected_name = _coerce_edition(edition)
    item = entry(name, edition=selected_name)
    if item is None:
        raise EditionV13ReplayError(
            f"unknown {selected_name.value} v13 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV13ReplayError(
            f"{selected_name.value} v13 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    return v12.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V13_ENROLLMENT_SHA256",
    "ALPHA_V13_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV13Error",
    "EditionV13ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "EXPECTED_ALPHA_V13_COUNT",
    "EXPECTED_ALPHA_V13_EDGE_COUNT",
    "EXPECTED_ALPHA_V13_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V13_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V13_LAYER_COUNT",
    "LibraryEdition",
    "Membership",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
]
