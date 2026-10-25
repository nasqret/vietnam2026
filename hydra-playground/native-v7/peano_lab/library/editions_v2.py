"""Versioned Stable/Alpha runtime for the 17-row K3C append.

The v1 runtime and its 885-row enrollment ledger remain byte-sealed.  Alpha
v2 converts that immutable ledger into the v2 metadata type and appends the
frozen K3C validity, membership, and semantic-interface rows.  All K3C rows
have dependency-curried body evidence only, so none crosses the checked-use
boundary.

Stable release order is represented independently from Alpha enrollment
order.  It remains the same 432 names in v2, but this separation prevents a
future promotion from overwriting a theorem's historical enrollment origin.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
import json
from types import MappingProxyType

from . import editions as v1
from .alpha_enrollment_v2 import (
    K3C_EXPECTED_COUNT,
    K3C_EXPECTED_NAMES,
    K3C_START_INDEX,
    PARENT_ALPHA_V1_COUNT,
    PARENT_ALPHA_V1_ENROLLMENT_SHA256,
    PARENT_ALPHA_V1_IDENTITY_SHA256,
    alpha_v2_enrollment,
)
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v1.EditionName
Membership = v1.Membership
EvidenceStatus = v1.EvidenceStatus


class EditionV2Error(ValueError):
    """An Alpha v2 manifest, topology, or lookup violates its seal."""


class EditionV2ReplayError(EditionV2Error):
    """A v2 theorem is absent or lacks empty-context closure evidence."""


class EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment tranche, extended with K3C."""

    STABLE = "stable"
    QR = "qr"
    HA = "ha"
    K3B = "k3b"
    K3C = "k3c"


@dataclass(frozen=True, slots=True)
class EditionEntry:
    """One v2 specification with independent release and evidence metadata."""

    spec: TheoremSpec
    membership: Membership
    evidence: EvidenceStatus
    enrollment_origin: EnrollmentOrigin
    provenance: tuple[EnrollmentOrigin, ...]
    source_module: str

    @property
    def checked_use(self) -> bool:
        return self.evidence.checked_use

    @property
    def editions(self) -> frozenset[EditionName]:
        if self.membership is Membership.STABLE:
            return frozenset({EditionName.STABLE, EditionName.ALPHA})
        return frozenset({EditionName.ALPHA})


@dataclass(frozen=True, slots=True)
class LibraryEdition:
    """One immutable, dependency-topological v2 edition view."""

    name: EditionName
    entries: tuple[EditionEntry, ...]
    specs: tuple[TheoremSpec, ...]
    by_name: Mapping[str, EditionEntry]
    dependency_depth_by_name: Mapping[str, int]
    dependency_layers: tuple[tuple[TheoremSpec, ...], ...]
    edge_count: int
    layer_count: int
    enrollment_identity_sha256: str
    identity_sha256: str

    @property
    def checked_entries(self) -> tuple[EditionEntry, ...]:
        return tuple(entry for entry in self.entries if entry.checked_use)

    @property
    def checked_specs(self) -> tuple[TheoremSpec, ...]:
        return tuple(entry.spec for entry in self.entries if entry.checked_use)


def _topology(
    specs: Iterable[TheoremSpec],
) -> tuple[
    tuple[TheoremSpec, ...],
    Mapping[str, int],
    tuple[tuple[TheoremSpec, ...], ...],
    int,
]:
    ordered = tuple(specs)
    available: dict[str, TheoremSpec] = {}
    depths: dict[str, int] = {}
    edge_count = 0
    for spec in ordered:
        if type(spec) is not TheoremSpec:
            raise EditionV2Error("edition rows must be exact TheoremSpec values")
        if spec.name in available:
            raise EditionV2Error(f"duplicate v2 theorem {spec.name!r}")
        for dependency in spec.dependencies:
            if dependency not in available:
                raise EditionV2Error(
                    f"missing or forward dependency {dependency!r} "
                    f"for v2 theorem {spec.name!r}"
                )
        available[spec.name] = spec
        depths[spec.name] = (
            0
            if not spec.dependencies
            else 1 + max(depths[name] for name in spec.dependencies)
        )
        edge_count += len(spec.dependencies)
    layer_count = max(depths.values(), default=-1) + 1
    layers: list[list[TheoremSpec]] = [[] for _ in range(layer_count)]
    for spec in ordered:
        layers[depths[spec.name]].append(spec)
    return (
        ordered,
        MappingProxyType(depths),
        tuple(tuple(layer) for layer in layers),
        edge_count,
    )


def dependency_depths(specs: Iterable[TheoremSpec]) -> Mapping[str, int]:
    return _topology(specs)[1]


def dependency_layers(
    specs: Iterable[TheoremSpec],
) -> tuple[tuple[TheoremSpec, ...], ...]:
    return _topology(specs)[2]


def _enrollment_identity(entries: tuple[EditionEntry, ...]) -> str:
    rows = (
        "\x1f".join(
            (
                entry.enrollment_origin.value,
                entry.spec.name,
                entry.spec.statement,
                "\x1e".join(entry.spec.dependencies),
                "\x1e".join(entry.spec.script),
            )
        )
        for entry in entries
    )
    return sha256("\x1c".join(rows).encode("utf-8")).hexdigest()


def _identity(name: EditionName, entries: tuple[EditionEntry, ...]) -> str:
    rows = [
        {
            "name": entry.spec.name,
            "statement": entry.spec.statement,
            "dependencies": list(entry.spec.dependencies),
            "script": list(entry.spec.script),
            "summary": entry.spec.summary,
            "membership": entry.membership.value,
            "evidence": entry.evidence.value,
            "enrollment_origin": entry.enrollment_origin.value,
            "provenance": [origin.value for origin in entry.provenance],
            "source_module": entry.source_module,
        }
        for entry in entries
    ]
    payload = json.dumps(
        {"edition": name.value, "entries": rows},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _make_edition(
    name: EditionName,
    entries: tuple[EditionEntry, ...],
) -> LibraryEdition:
    specs, depths, layers, edge_count = _topology(
        entry.spec for entry in entries
    )
    by_name = {entry.spec.name: entry for entry in entries}
    if len(by_name) != len(entries):
        raise EditionV2Error(f"duplicate rows in {name.value} v2 edition")
    return LibraryEdition(
        name=name,
        entries=entries,
        specs=specs,
        by_name=MappingProxyType(by_name),
        dependency_depth_by_name=depths,
        dependency_layers=layers,
        edge_count=edge_count,
        layer_count=len(layers),
        enrollment_identity_sha256=_enrollment_identity(entries),
        identity_sha256=_identity(name, entries),
    )


def _convert_parent_entry(entry: v1.EditionEntry) -> EditionEntry:
    return EditionEntry(
        spec=entry.spec,
        membership=entry.membership,
        evidence=entry.evidence,
        enrollment_origin=EnrollmentOrigin(entry.enrollment_origin.value),
        provenance=tuple(
            EnrollmentOrigin(origin.value) for origin in entry.provenance
        ),
        source_module=entry.source_module,
    )


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_v2_enrollment()
    result = [
        _convert_parent_entry(entry) for entry in enrollment.parent_entries
    ]
    for spec in enrollment.k3c_specs:
        result.append(
            EditionEntry(
                spec=spec,
                membership=Membership.ALPHA_ONLY,
                evidence=EvidenceStatus.BODY_CHECKED,
                enrollment_origin=EnrollmentOrigin.K3C,
                provenance=(EnrollmentOrigin.K3C,),
                source_module=enrollment.source_by_name[spec.name],
            )
        )
    return tuple(result)


ALPHA_ENTRIES: tuple[EditionEntry, ...] = _alpha_entries()
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in ALPHA_ENTRIES
)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in ALPHA_ENTRIES if entry.checked_use
)

# Stable has an independent append-only release order.  It is deliberately a
# tuple of names, not a filter by enrollment origin.
STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(
    spec.name for spec in v1.STABLE_SPECS
)
_ALPHA_BY_NAME = {entry.spec.name: entry for entry in ALPHA_ENTRIES}
STABLE_ENTRIES: tuple[EditionEntry, ...] = tuple(
    _ALPHA_BY_NAME[name] for name in STABLE_RELEASE_ORDER
)
STABLE_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in STABLE_ENTRIES
)

STABLE_EDITION = _make_edition(EditionName.STABLE, STABLE_ENTRIES)
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)

ALPHA_V2_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V2_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V2_ENROLLMENT_SHA256

EXPECTED_ALPHA_V2_ENROLLMENT_SHA256 = (
    "00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe"
)
EXPECTED_ALPHA_V2_IDENTITY_SHA256 = (
    "aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4"
)


def _validate_seals() -> None:
    if len(ALPHA_ENTRIES) != PARENT_ALPHA_V1_COUNT + K3C_EXPECTED_COUNT:
        raise EditionV2Error("Alpha v2 theorem count changed")
    if tuple(entry.spec.name for entry in ALPHA_ENTRIES[K3C_START_INDEX:]) != (
        K3C_EXPECTED_NAMES
    ):
        raise EditionV2Error("Alpha v2 K3C append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V1_COUNT]
    if _enrollment_identity(parent) != PARENT_ALPHA_V1_ENROLLMENT_SHA256:
        raise EditionV2Error("Alpha v2 no longer preserves its v1 parent ledger")
    if _identity(EditionName.ALPHA, parent) != PARENT_ALPHA_V1_IDENTITY_SHA256:
        raise EditionV2Error("Alpha v2 changed v1 edition metadata")
    if STABLE_SPECS != v1.STABLE_SPECS or len(STABLE_SPECS) != 432:
        raise EditionV2Error("Stable v2 view changed the sealed 432-row release")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (2674, 45):
        raise EditionV2Error("Alpha v2 topology seal changed")
    if ALPHA_V2_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V2_ENROLLMENT_SHA256:
        raise EditionV2Error("Alpha v2 enrollment identity changed")
    if ALPHA_V2_IDENTITY_SHA256 != EXPECTED_ALPHA_V2_IDENTITY_SHA256:
        raise EditionV2Error("Alpha v2 edition identity changed")

    membership = Counter(entry.membership for entry in ALPHA_ENTRIES)
    evidence = Counter(entry.evidence for entry in ALPHA_ENTRIES)
    origins = Counter(entry.enrollment_origin for entry in ALPHA_ENTRIES)
    if membership != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 470,
    }:
        raise EditionV2Error("Alpha v2 release-membership counts changed")
    if evidence != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 331,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }:
        raise EditionV2Error("Alpha v2 evidence counts changed")
    if origins != {
        EnrollmentOrigin.STABLE: 432,
        EnrollmentOrigin.QR: 316,
        EnrollmentOrigin.HA: 120,
        EnrollmentOrigin.K3B: 17,
        EnrollmentOrigin.K3C: 17,
    }:
        raise EditionV2Error("Alpha v2 origin counts changed")
    if len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV2Error("body-only K3C rows changed checked-use count")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV2Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[K3C_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.enrollment_origin is not EnrollmentOrigin.K3C
            or entry.provenance != (EnrollmentOrigin.K3C,)
        ):
            raise EditionV2Error("K3C membership/evidence/origin seal changed")


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV2Error(f"unknown theorem-library v2 edition {value!r}")


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
    wanted = name.strip().casefold()
    return next(
        (
            item
            for item in selected.entries
            if item.spec.name.casefold() == wanted
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
        raise EditionV2ReplayError(
            f"unknown {selected_name.value} v2 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV2ReplayError(
            f"{selected_name.value} v2 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    # All checked-use rows in v2 are exact v1 rows.  K3C closure evidence is
    # intentionally absent, so delegating preserves the already audited Cut
    # packaging and independent-kernel replay path.
    return v1.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V2_ENROLLMENT_SHA256",
    "ALPHA_V2_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V2_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V2_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV2Error",
    "EditionV2ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "K3C_START_INDEX",
    "LibraryEdition",
    "Membership",
    "PARENT_ALPHA_V1_COUNT",
    "PARENT_ALPHA_V1_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V1_IDENTITY_SHA256",
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
