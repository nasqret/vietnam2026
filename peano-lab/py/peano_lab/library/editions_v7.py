"""Fail-closed Stable/Alpha runtime for the twenty-four-row Bertrand v7 append.

The exact 993-row Alpha-v6 ledger is retained as a prefix.  Three missing
initial-segment constructors, five Legendre successor rows, four capacity-
shared power rows, two compact H/J base rows, five finite Legendre-recurrence
rows, three compact H/J transport rows, and two factorial--Legendre agreement
rows are appended with dependency-curried body evidence only.  None can be
replayed as an empty-context theorem.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from . import editions_v6 as v6
from .alpha_enrollment_v7 import (
    BERTRAND_V7_EXPECTED_COUNT,
    BERTRAND_V7_EXPECTED_NAMES,
    BERTRAND_V7_START_INDEX,
    PARENT_ALPHA_V6_COUNT,
    PARENT_ALPHA_V6_ENROLLMENT_SHA256,
    PARENT_ALPHA_V6_IDENTITY_SHA256,
    alpha_v7_enrollment,
)
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v6.EditionName
Membership = v6.Membership
EvidenceStatus = v6.EvidenceStatus
EnrollmentOrigin = v6.EnrollmentOrigin
EditionEntry = v6.EditionEntry
LibraryEdition = v6.LibraryEdition


class EditionV7Error(ValueError):
    """An Alpha-v7 manifest, topology, or lookup violates its seal."""


class EditionV7ReplayError(EditionV7Error):
    """A v7 theorem is absent or lacks empty-context closure evidence."""


def dependency_depths(specs):
    return v6.dependency_depths(specs)


def dependency_layers(specs):
    return v6.dependency_layers(specs)


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_v7_enrollment()
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

STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(spec.name for spec in v6.STABLE_SPECS)
_ALPHA_BY_NAME = {entry.spec.name: entry for entry in ALPHA_ENTRIES}
STABLE_ENTRIES: tuple[EditionEntry, ...] = tuple(
    _ALPHA_BY_NAME[name] for name in STABLE_RELEASE_ORDER
)
STABLE_SPECS: tuple[TheoremSpec, ...] = tuple(entry.spec for entry in STABLE_ENTRIES)

STABLE_EDITION = v6.v5._make_edition(EditionName.STABLE, STABLE_ENTRIES)
ALPHA_EDITION = v6.v5._make_edition(EditionName.ALPHA, ALPHA_ENTRIES)

ALPHA_V7_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V7_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V7_ENROLLMENT_SHA256

# Bootstrap sentinels.  The serial release gate replaces these four values
# with the exact runtime topology and identities before artifacts are built.
EXPECTED_ALPHA_V7_EDGE_COUNT = 3072
EXPECTED_ALPHA_V7_LAYER_COUNT = 45
EXPECTED_ALPHA_V7_ENROLLMENT_SHA256 = (
    "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
)
EXPECTED_ALPHA_V7_IDENTITY_SHA256 = (
    "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
)


def _validate_seals() -> None:
    if len(ALPHA_ENTRIES) != PARENT_ALPHA_V6_COUNT + BERTRAND_V7_EXPECTED_COUNT:
        raise EditionV7Error("Alpha v7 theorem count changed")
    if tuple(
        entry.spec.name for entry in ALPHA_ENTRIES[BERTRAND_V7_START_INDEX:]
    ) != BERTRAND_V7_EXPECTED_NAMES:
        raise EditionV7Error("Alpha v7 Bertrand append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V6_COUNT]
    if parent != v6.ALPHA_ENTRIES:
        raise EditionV7Error("Alpha v7 no longer preserves exact v6 entries")
    if v6.v5._enrollment_identity(parent) != PARENT_ALPHA_V6_ENROLLMENT_SHA256:
        raise EditionV7Error("Alpha v7 no longer preserves its v6 parent ledger")
    if v6.v5._identity(EditionName.ALPHA, parent) != PARENT_ALPHA_V6_IDENTITY_SHA256:
        raise EditionV7Error("Alpha v7 changed v6 edition metadata")
    if STABLE_SPECS != v6.STABLE_SPECS or len(STABLE_SPECS) != 432:
        raise EditionV7Error("Stable v7 view changed the sealed 432-row release")
    if STABLE_EDITION.identity_sha256 != v6.STABLE_EDITION.identity_sha256:
        raise EditionV7Error("Stable v7 metadata changed")

    actual_topology = (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count)
    expected_topology = (
        EXPECTED_ALPHA_V7_EDGE_COUNT,
        EXPECTED_ALPHA_V7_LAYER_COUNT,
    )
    if -1 in expected_topology:
        raise EditionV7Error(
            "Alpha v7 topology bootstrap required: "
            f"edge_count={actual_topology[0]}, layer_count={actual_topology[1]}, "
            f"enrollment={ALPHA_V7_ENROLLMENT_SHA256}, "
            f"identity={ALPHA_V7_IDENTITY_SHA256}"
        )
    if actual_topology != expected_topology:
        raise EditionV7Error("Alpha v7 topology seal changed")
    if (
        EXPECTED_ALPHA_V7_ENROLLMENT_SHA256.startswith("UNSEALED_")
        or EXPECTED_ALPHA_V7_IDENTITY_SHA256.startswith("UNSEALED_")
    ):
        raise EditionV7Error(
            "Alpha v7 identity bootstrap required: "
            f"enrollment={ALPHA_V7_ENROLLMENT_SHA256}, "
            f"identity={ALPHA_V7_IDENTITY_SHA256}"
        )
    if ALPHA_V7_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V7_ENROLLMENT_SHA256:
        raise EditionV7Error("Alpha v7 enrollment identity changed")
    if ALPHA_V7_IDENTITY_SHA256 != EXPECTED_ALPHA_V7_IDENTITY_SHA256:
        raise EditionV7Error("Alpha v7 edition identity changed")

    if Counter(entry.membership for entry in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 585,
    }:
        raise EditionV7Error("Alpha v7 release-membership counts changed")
    if Counter(entry.evidence for entry in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 446,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }:
        raise EditionV7Error("Alpha v7 evidence counts changed")
    origins = Counter(entry.enrollment_origin for entry in ALPHA_ENTRIES)
    if origins[EnrollmentOrigin.BERTRAND] != 52 or sum(origins.values()) != 1017:
        raise EditionV7Error("Alpha v7 enrollment-origin counts changed")
    if len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV7Error("body-only v7 rows changed checked use")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV7Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[BERTRAND_V7_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.checked_use
            or entry.enrollment_origin is not EnrollmentOrigin.BERTRAND
            or entry.provenance != (EnrollmentOrigin.BERTRAND,)
        ):
            raise EditionV7Error("Bertrand v7 evidence boundary changed")


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV7Error(f"unknown theorem-library v7 edition {value!r}")


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
        raise EditionV7ReplayError(
            f"unknown {selected_name.value} v7 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV7ReplayError(
            f"{selected_name.value} v7 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    return v6.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V7_ENROLLMENT_SHA256",
    "ALPHA_V7_IDENTITY_SHA256",
    "BERTRAND_V7_START_INDEX",
    "EXPECTED_ALPHA_V7_EDGE_COUNT",
    "EXPECTED_ALPHA_V7_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V7_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V7_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV7Error",
    "EditionV7ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "LibraryEdition",
    "Membership",
    "PARENT_ALPHA_V6_COUNT",
    "PARENT_ALPHA_V6_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V6_IDENTITY_SHA256",
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
