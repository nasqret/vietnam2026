"""Fail-closed Stable/Alpha runtime for the Bertrand Alpha-v12 append.

The exact 1,123-row Alpha-v11 ledger is retained as an immutable prefix.
One hundred eighty reviewed Bertrand rows are appended with
dependency-curried body evidence only. Alpha membership records their exact
identity and provenance; it does not admit any appended row as an empty-context
theorem.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from . import editions_v11 as v11
from .alpha_enrollment_v12 import (
    BERTRAND_V12_EXPECTED_COUNT,
    BERTRAND_V12_EXPECTED_NAMES,
    BERTRAND_V12_START_INDEX,
    PARENT_ALPHA_V11_COUNT,
    PARENT_ALPHA_V11_ENROLLMENT_SHA256,
    PARENT_ALPHA_V11_IDENTITY_SHA256,
    alpha_v12_enrollment,
)
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v11.EditionName
Membership = v11.Membership
EvidenceStatus = v11.EvidenceStatus
EnrollmentOrigin = v11.EnrollmentOrigin
EditionEntry = v11.EditionEntry
LibraryEdition = v11.LibraryEdition


class EditionV12Error(ValueError):
    """An Alpha-v12 manifest, topology, or lookup violates its seal."""


class EditionV12ReplayError(EditionV12Error):
    """A v12 theorem is absent or lacks empty-context closure evidence."""


def dependency_depths(specs):
    return v11.dependency_depths(specs)


def dependency_layers(specs):
    return v11.dependency_layers(specs)


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_v12_enrollment()
    result = list(enrollment.parent_entries)
    for spec in enrollment.bertrand_specs:
        origin = EnrollmentOrigin(enrollment.origin_by_name[spec.name].value)
        result.append(
            EditionEntry(
                spec=spec,
                membership=Membership.ALPHA_ONLY,
                evidence=EvidenceStatus.BODY_CHECKED,
                enrollment_origin=origin,
                provenance=(origin,),
                source_module=enrollment.source_by_name[spec.name],
            )
        )
    return tuple(result)


ALPHA_ENTRIES: tuple[EditionEntry, ...] = _alpha_entries()
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(entry.spec for entry in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in ALPHA_ENTRIES if entry.checked_use
)

STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(spec.name for spec in v11.STABLE_SPECS)
_ALPHA_BY_NAME = {entry.spec.name: entry for entry in ALPHA_ENTRIES}
STABLE_ENTRIES: tuple[EditionEntry, ...] = tuple(
    _ALPHA_BY_NAME[name] for name in STABLE_RELEASE_ORDER
)
STABLE_SPECS: tuple[TheoremSpec, ...] = tuple(entry.spec for entry in STABLE_ENTRIES)

STABLE_EDITION = v11.v10.v9.v8.v7.v6.v5._make_edition(
    EditionName.STABLE,
    STABLE_ENTRIES,
)
ALPHA_EDITION = v11.v10.v9.v8.v7.v6.v5._make_edition(
    EditionName.ALPHA,
    ALPHA_ENTRIES,
)

ALPHA_V12_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V12_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V12_ENROLLMENT_SHA256

EXPECTED_ALPHA_V12_EDGE_COUNT = 4_302
EXPECTED_ALPHA_V12_LAYER_COUNT = 45
EXPECTED_ALPHA_V12_ENROLLMENT_SHA256 = (
    "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b"
)
EXPECTED_ALPHA_V12_IDENTITY_SHA256 = (
    "bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061"
)


def _validate_seals() -> None:
    if len(ALPHA_ENTRIES) != PARENT_ALPHA_V11_COUNT + BERTRAND_V12_EXPECTED_COUNT:
        raise EditionV12Error("Alpha v12 theorem count changed")
    if tuple(
        entry.spec.name for entry in ALPHA_ENTRIES[BERTRAND_V12_START_INDEX:]
    ) != BERTRAND_V12_EXPECTED_NAMES:
        raise EditionV12Error("Alpha v12 Bertrand append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V11_COUNT]
    if parent != v11.ALPHA_ENTRIES:
        raise EditionV12Error("Alpha v12 no longer preserves exact v11 entries")
    if (
        v11.v10.v9.v8.v7.v6.v5._enrollment_identity(parent)
        != PARENT_ALPHA_V11_ENROLLMENT_SHA256
    ):
        raise EditionV12Error("Alpha v12 no longer preserves its v11 parent ledger")
    if (
        v11.v10.v9.v8.v7.v6.v5._identity(EditionName.ALPHA, parent)
        != PARENT_ALPHA_V11_IDENTITY_SHA256
    ):
        raise EditionV12Error("Alpha v12 changed v11 edition metadata")
    if STABLE_SPECS != v11.STABLE_SPECS or len(STABLE_SPECS) != 432:
        raise EditionV12Error("Stable v12 view changed the sealed 432-row release")
    if STABLE_EDITION.identity_sha256 != v11.STABLE_EDITION.identity_sha256:
        raise EditionV12Error("Stable v12 metadata changed")

    actual_topology = (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count)
    expected_topology = (
        EXPECTED_ALPHA_V12_EDGE_COUNT,
        EXPECTED_ALPHA_V12_LAYER_COUNT,
    )
    if -1 in expected_topology:
        raise EditionV12Error(
            "Alpha v12 topology bootstrap required: "
            f"edge_count={actual_topology[0]}, layer_count={actual_topology[1]}, "
            f"enrollment={ALPHA_V12_ENROLLMENT_SHA256}, "
            f"identity={ALPHA_V12_IDENTITY_SHA256}"
        )
    if actual_topology != expected_topology:
        raise EditionV12Error("Alpha v12 topology seal changed")
    if (
        EXPECTED_ALPHA_V12_ENROLLMENT_SHA256.startswith("UNSEALED_")
        or EXPECTED_ALPHA_V12_IDENTITY_SHA256.startswith("UNSEALED_")
    ):
        raise EditionV12Error(
            "Alpha v12 identity bootstrap required: "
            f"enrollment={ALPHA_V12_ENROLLMENT_SHA256}, "
            f"identity={ALPHA_V12_IDENTITY_SHA256}"
        )
    if ALPHA_V12_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V12_ENROLLMENT_SHA256:
        raise EditionV12Error("Alpha v12 enrollment identity changed")
    if ALPHA_V12_IDENTITY_SHA256 != EXPECTED_ALPHA_V12_IDENTITY_SHA256:
        raise EditionV12Error("Alpha v12 edition identity changed")

    if Counter(entry.membership for entry in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 871,
    }:
        raise EditionV12Error("Alpha v12 release-membership counts changed")
    if Counter(entry.evidence for entry in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 732,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }:
        raise EditionV12Error("Alpha v12 evidence counts changed")
    origins = Counter(entry.enrollment_origin for entry in ALPHA_ENTRIES)
    if (
        origins[EnrollmentOrigin.BERTRAND] != 338
        or sum(origins.values()) != 1303
    ):
        raise EditionV12Error("Alpha v12 enrollment-origin counts changed")
    if len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV12Error("body-only v12 rows changed checked use")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV12Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[BERTRAND_V12_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.checked_use
            or entry.enrollment_origin is not EnrollmentOrigin.BERTRAND
            or entry.provenance != (EnrollmentOrigin.BERTRAND,)
        ):
            raise EditionV12Error("Bertrand v12 evidence boundary changed")


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV12Error(f"unknown theorem-library v12 edition {value!r}")


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
        raise EditionV12ReplayError(
            f"unknown {selected_name.value} v12 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV12ReplayError(
            f"{selected_name.value} v12 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    return v11.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V12_ENROLLMENT_SHA256",
    "ALPHA_V12_IDENTITY_SHA256",
    "BERTRAND_V12_START_INDEX",
    "EXPECTED_ALPHA_V12_EDGE_COUNT",
    "EXPECTED_ALPHA_V12_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V12_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V12_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV12Error",
    "EditionV12ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "LibraryEdition",
    "Membership",
    "PARENT_ALPHA_V11_COUNT",
    "PARENT_ALPHA_V11_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V11_IDENTITY_SHA256",
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
