"""Sealed Alpha-v15 supplementary-law and two-square body-only edition."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from . import editions_v14 as v14
from .alpha_enrollment_v15 import (
    FRONTIER_V15_EXPECTED_COUNT,
    FRONTIER_V15_EXPECTED_NAMES,
    FRONTIER_V15_ROOT_NAMES,
    FRONTIER_V15_START_INDEX,
    PARENT_ALPHA_V14_COUNT,
    PARENT_ALPHA_V14_ENROLLMENT_SHA256,
    PARENT_ALPHA_V14_IDENTITY_SHA256,
    SUPPLEMENTARY_V15_EXPECTED_COUNT,
    alpha_v15_enrollment,
)
from .editions_v5 import _enrollment_identity, _identity, _make_edition
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v14.EditionName
Membership = v14.Membership
EvidenceStatus = v14.EvidenceStatus
EnrollmentOrigin = v14.EnrollmentOrigin
EditionEntry = v14.EditionEntry
LibraryEdition = v14.LibraryEdition


class EditionV15Error(ValueError):
    """The Alpha-v15 release, parent, evidence, or topology is invalid."""


class EditionV15ReplayError(EditionV15Error):
    """A theorem is absent or has no actual empty-context closure."""


def dependency_depths(specs):
    return v14.dependency_depths(specs)


def dependency_layers(specs):
    return v14.dependency_layers(specs)


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_v15_enrollment()
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
STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(spec.name for spec in v14.STABLE_SPECS)
STABLE_ENTRIES: tuple[EditionEntry, ...] = v14.STABLE_ENTRIES
STABLE_SPECS: tuple[TheoremSpec, ...] = v14.STABLE_SPECS
STABLE_EDITION = v14.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)

ALPHA_V15_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V15_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V15_ENROLLMENT_SHA256

EXPECTED_ALPHA_V15_COUNT = 1_673
EXPECTED_ALPHA_V15_EDGE_COUNT = 5_615
EXPECTED_ALPHA_V15_LAYER_COUNT = 53
EXPECTED_ALPHA_V15_ENROLLMENT_SHA256 = (
    "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
)
EXPECTED_ALPHA_V15_IDENTITY_SHA256 = (
    "2f1a097ac0b6821c74cd4da088c396d3b9960ffd43e169f22b4778d5871adc66"
)


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V15_COUNT
        or len(ALPHA_ENTRIES)
        != PARENT_ALPHA_V14_COUNT + FRONTIER_V15_EXPECTED_COUNT
    ):
        raise EditionV15Error("Alpha-v15 theorem count changed")
    if tuple(entry.spec.name for entry in ALPHA_ENTRIES[FRONTIER_V15_START_INDEX:]) != (
        FRONTIER_V15_EXPECTED_NAMES
    ):
        raise EditionV15Error("Alpha-v15 exact minimal append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V14_COUNT]
    if parent != v14.ALPHA_ENTRIES or any(
        newer is not older
        for newer, older in zip(parent, v14.ALPHA_ENTRIES, strict=True)
    ):
        raise EditionV15Error("Alpha-v15 changed immutable Alpha-v14 parent objects")
    if _enrollment_identity(parent) != PARENT_ALPHA_V14_ENROLLMENT_SHA256:
        raise EditionV15Error("Alpha-v15 changed its sealed Alpha-v14 parent order")
    if _identity(EditionName.ALPHA, parent) != PARENT_ALPHA_V14_IDENTITY_SHA256:
        raise EditionV15Error("Alpha-v15 changed its sealed Alpha-v14 parent identity")
    if (
        STABLE_EDITION is not v14.STABLE_EDITION
        or STABLE_ENTRIES is not v14.STABLE_ENTRIES
        or STABLE_SPECS is not v14.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV15Error("Alpha-v15 changed the sealed Stable edition")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V15_EDGE_COUNT,
        EXPECTED_ALPHA_V15_LAYER_COUNT,
    ):
        raise EditionV15Error("Alpha-v15 dependency topology seal changed")
    if ALPHA_V15_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V15_ENROLLMENT_SHA256:
        raise EditionV15Error("Alpha-v15 ordered enrollment identity changed")
    if ALPHA_V15_IDENTITY_SHA256 != EXPECTED_ALPHA_V15_IDENTITY_SHA256:
        raise EditionV15Error("Alpha-v15 full edition identity changed")
    if Counter(entry.membership for entry in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 1_241,
    }:
        raise EditionV15Error("Alpha-v15 release membership counts changed")
    if Counter(entry.evidence for entry in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 1_102,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }:
        raise EditionV15Error("Alpha-v15 proof-evidence counts changed")
    if ALPHA_CHECKED_SPECS != v14.ALPHA_CHECKED_SPECS or len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV15Error("Alpha-v15 body-only enrollment changed checked use")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV15Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[FRONTIER_V15_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.checked_use
            or entry.enrollment_origin is not EnrollmentOrigin.HA
            or entry.provenance != (EnrollmentOrigin.HA,)
        ):
            raise EditionV15Error("Alpha-v15 dependency-curried evidence boundary changed")
    if (
        ALPHA_ENTRIES[FRONTIER_V15_START_INDEX + 6].spec.name
        != FRONTIER_V15_ROOT_NAMES[0]
        or ALPHA_ENTRIES[
            FRONTIER_V15_START_INDEX + SUPPLEMENTARY_V15_EXPECTED_COUNT - 1
        ].spec.name
        != FRONTIER_V15_ROOT_NAMES[1]
        or ALPHA_ENTRIES[-1].spec.name != FRONTIER_V15_ROOT_NAMES[2]
    ):
        raise EditionV15Error("Alpha-v15 exact root boundaries changed")


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV15Error(f"unknown theorem-library v15 edition {value!r}")


def edition(name: EditionName | str = EditionName.STABLE) -> LibraryEdition:
    selected = _coerce_edition(name)
    return STABLE_EDITION if selected is EditionName.STABLE else ALPHA_EDITION


def entry(
    name: str, *, edition: EditionName | str = EditionName.STABLE
) -> EditionEntry | None:
    if not isinstance(name, str):
        return None
    selected = globals()["edition"](edition)
    return selected.by_name.get(name.strip()) or next(
        (
            candidate
            for candidate in selected.entries
            if candidate.spec.name.casefold() == name.strip().casefold()
        ),
        None,
    )


@lru_cache(maxsize=None)
def replay(
    name: str, *, edition: EditionName | str = EditionName.STABLE
) -> CheckedTheorem:
    selected_name = _coerce_edition(edition)
    item = entry(name, edition=selected_name)
    if item is None:
        raise EditionV15ReplayError(f"unknown {selected_name.value} v15 theorem {name!r}")
    if not item.checked_use:
        raise EditionV15ReplayError(
            f"{selected_name.value} v15 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    return v14.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V15_ENROLLMENT_SHA256",
    "ALPHA_V15_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV15Error",
    "EditionV15ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "EXPECTED_ALPHA_V15_COUNT",
    "EXPECTED_ALPHA_V15_EDGE_COUNT",
    "EXPECTED_ALPHA_V15_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V15_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V15_LAYER_COUNT",
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
