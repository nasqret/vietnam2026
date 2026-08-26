"""Fail-closed Alpha-v14 release of complete constructive Kummer bodies.

The 1,543-row Alpha-v13 ledger remains an object-identical immutable prefix.
Exactly 13 dependency-minimal Kummer theorem/corollary bodies are admitted as
Alpha-only ``body_checked`` entries.  Stable and all checked-use authority are
unchanged: enrollment is not an empty-context proof or a promotion.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from . import editions_v13 as v13
from .alpha_enrollment_v14 import (
    FRONTIER_V14_EXPECTED_COUNT,
    FRONTIER_V14_EXPECTED_NAMES,
    FRONTIER_V14_ROOT_NAMES,
    FRONTIER_V14_START_INDEX,
    KUMMER_THEOREM_V14_EXPECTED_COUNT,
    PARENT_ALPHA_V13_COUNT,
    PARENT_ALPHA_V13_ENROLLMENT_SHA256,
    PARENT_ALPHA_V13_IDENTITY_SHA256,
    alpha_v14_enrollment,
)
from .editions_v5 import _enrollment_identity, _identity, _make_edition
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v13.EditionName
Membership = v13.Membership
EvidenceStatus = v13.EvidenceStatus
EnrollmentOrigin = v13.EnrollmentOrigin
EditionEntry = v13.EditionEntry
LibraryEdition = v13.LibraryEdition


class EditionV14Error(ValueError):
    """An Alpha-v14 manifest, topology, evidence label, or lookup is invalid."""


class EditionV14ReplayError(EditionV14Error):
    """A v14 theorem is absent or lacks actual empty-context closure evidence."""


def dependency_depths(specs):
    return v13.dependency_depths(specs)


def dependency_layers(specs):
    return v13.dependency_layers(specs)


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_v14_enrollment()
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

STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(spec.name for spec in v13.STABLE_SPECS)
STABLE_ENTRIES: tuple[EditionEntry, ...] = v13.STABLE_ENTRIES
STABLE_SPECS: tuple[TheoremSpec, ...] = v13.STABLE_SPECS
STABLE_EDITION = v13.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)

ALPHA_V14_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V14_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V14_ENROLLMENT_SHA256

EXPECTED_ALPHA_V14_COUNT = 1_556
EXPECTED_ALPHA_V14_EDGE_COUNT = 5_251
EXPECTED_ALPHA_V14_LAYER_COUNT = 45
EXPECTED_ALPHA_V14_ENROLLMENT_SHA256 = (
    "d7758c5cfcce4fbe2b48b6b213b134acf9126b84a58a0016c523055be952024e"
)
EXPECTED_ALPHA_V14_IDENTITY_SHA256 = (
    "06274ac80612403f6851266fa00f8b543d904072434d5717ca95ae7d40588c16"
)


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V14_COUNT
        or len(ALPHA_ENTRIES)
        != PARENT_ALPHA_V13_COUNT + FRONTIER_V14_EXPECTED_COUNT
    ):
        raise EditionV14Error("Alpha-v14 theorem count changed")
    if tuple(entry.spec.name for entry in ALPHA_ENTRIES[FRONTIER_V14_START_INDEX:]) != (
        FRONTIER_V14_EXPECTED_NAMES
    ):
        raise EditionV14Error("Alpha-v14 exact minimal append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V13_COUNT]
    if parent != v13.ALPHA_ENTRIES or any(
        newer is not older for newer, older in zip(parent, v13.ALPHA_ENTRIES, strict=True)
    ):
        raise EditionV14Error("Alpha-v14 no longer preserves exact Alpha-v13 objects")
    if _enrollment_identity(parent) != PARENT_ALPHA_V13_ENROLLMENT_SHA256:
        raise EditionV14Error("Alpha-v14 changed its sealed Alpha-v13 parent ledger")
    if _identity(EditionName.ALPHA, parent) != PARENT_ALPHA_V13_IDENTITY_SHA256:
        raise EditionV14Error("Alpha-v14 changed sealed Alpha-v13 edition metadata")
    if (
        STABLE_EDITION is not v13.STABLE_EDITION
        or STABLE_ENTRIES is not v13.STABLE_ENTRIES
        or STABLE_SPECS is not v13.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV14Error("Alpha-v14 changed the sealed Stable release")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V14_EDGE_COUNT,
        EXPECTED_ALPHA_V14_LAYER_COUNT,
    ):
        raise EditionV14Error("Alpha-v14 dependency topology changed")
    if (
        ALPHA_V14_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V14_ENROLLMENT_SHA256
        or ALPHA_V14_IDENTITY_SHA256 != EXPECTED_ALPHA_V14_IDENTITY_SHA256
    ):
        raise EditionV14Error("Alpha-v14 exact runtime identity changed")
    if ALPHA_CHECKED_SPECS != v13.ALPHA_CHECKED_SPECS or len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV14Error("Alpha-v14 body-only append changed checked theorem use")
    expected_evidence = Counter(
        stable_closed=432,
        alpha_closed=138,
        body_checked=985,
        pending_layered_closure=1,
    )
    if Counter(entry.evidence.value for entry in ALPHA_ENTRIES) != expected_evidence:
        raise EditionV14Error("Alpha-v14 evidence-status ledger changed")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV14Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[FRONTIER_V14_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.checked_use
            or entry.enrollment_origin is not EnrollmentOrigin.HA
            or entry.provenance != (EnrollmentOrigin.HA,)
        ):
            raise EditionV14Error("Alpha-v14 frontier body-only evidence boundary changed")
    if (
        ALPHA_ENTRIES[
            FRONTIER_V14_START_INDEX + KUMMER_THEOREM_V14_EXPECTED_COUNT - 1
        ].spec.name
        != FRONTIER_V14_ROOT_NAMES[0]
        or ALPHA_ENTRIES[-1].spec.name != FRONTIER_V14_ROOT_NAMES[1]
    ):
        raise EditionV14Error("Alpha-v14 Kummer theorem/corollary boundaries changed")


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV14Error(f"unknown theorem-library v14 edition {value!r}")


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
        raise EditionV14ReplayError(
            f"unknown {selected_name.value} v14 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV14ReplayError(
            f"{selected_name.value} v14 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    return v13.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V14_ENROLLMENT_SHA256",
    "ALPHA_V14_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV14Error",
    "EditionV14ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "EXPECTED_ALPHA_V14_COUNT",
    "EXPECTED_ALPHA_V14_EDGE_COUNT",
    "EXPECTED_ALPHA_V14_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V14_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V14_LAYER_COUNT",
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
