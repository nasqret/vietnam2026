"""Fail-closed Stable/Alpha runtime for Bertrand Round-2 infrastructure.

The exact 923-row Alpha-v3 ledger is retained as a prefix and forty-two
dependency-curried candidate rows are appended.  Membership and evidence are
orthogonal: every new row is Alpha-only ``body_checked`` and therefore cannot
be returned by :func:`replay` as an empty-context theorem.
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

from . import editions_v3 as v3
from .alpha_enrollment_v4 import (
    BERTRAND_V4_EXPECTED_COUNT,
    BERTRAND_V4_EXPECTED_NAMES,
    BERTRAND_V4_START_INDEX,
    PARENT_ALPHA_V3_COUNT,
    PARENT_ALPHA_V3_ENROLLMENT_SHA256,
    PARENT_ALPHA_V3_IDENTITY_SHA256,
    alpha_v4_enrollment,
)
from .theorems import CheckedTheorem, TheoremSpec


EditionName = v3.EditionName
Membership = v3.Membership
EvidenceStatus = v3.EvidenceStatus


class EditionV4Error(ValueError):
    """An Alpha-v4 manifest, topology, or lookup violates its seal."""


class EditionV4ReplayError(EditionV4Error):
    """A v4 theorem is absent or lacks empty-context closure evidence."""


class EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment tranche, extended for Round 2."""

    STABLE = "stable"
    QR = "qr"
    HA = "ha"
    K3B = "k3b"
    K3C = "k3c"
    BERTRAND_B0_INTERVAL = "bertrand_b0_interval"
    BERTRAND_B1_POWER_ORDER = "bertrand_b1_power_order"
    BERTRAND_B1_POWER_GROWTH = "bertrand_b1_power_growth"
    BERTRAND_B2_BOUNDED_VALUATION = "bertrand_b2_bounded_valuation"
    BERTRAND_B2_VALUATION_LAWS = "bertrand_b2_valuation_laws"
    BERTRAND_B2_VALUATION_MULTIPLICATION = (
        "bertrand_b2_valuation_multiplication"
    )
    BERTRAND_B6_INTEGER_ENVELOPE = "bertrand_b6_integer_envelope"
    BERTRAND_B6_CEIL_SQRT = "bertrand_b6_ceil_sqrt"
    BERTRAND_B6_FLOOR_SQRT_TOTAL = "bertrand_b6_floor_sqrt_total"
    BERTRAND_B6_QUOTIENT_BUDGET = "bertrand_b6_quotient_budget"


@dataclass(frozen=True, slots=True)
class EditionEntry:
    """One v4 specification with independent release/evidence metadata."""

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
    """One immutable, dependency-topological v4 edition view."""

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
            raise EditionV4Error("edition rows must be exact TheoremSpec values")
        if spec.name in available:
            raise EditionV4Error(f"duplicate v4 theorem {spec.name!r}")
        for dependency in spec.dependencies:
            if dependency not in available:
                raise EditionV4Error(
                    f"missing or forward dependency {dependency!r} "
                    f"for v4 theorem {spec.name!r}"
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
        raise EditionV4Error(f"duplicate rows in {name.value} v4 edition")
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


def _convert_parent_entry(entry: v3.EditionEntry) -> EditionEntry:
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
    enrollment = alpha_v4_enrollment()
    result = [
        _convert_parent_entry(entry) for entry in enrollment.parent_entries
    ]
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
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in ALPHA_ENTRIES
)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    entry.spec for entry in ALPHA_ENTRIES if entry.checked_use
)

STABLE_RELEASE_ORDER: tuple[str, ...] = tuple(
    spec.name for spec in v3.STABLE_SPECS
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

ALPHA_V4_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V4_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V4_ENROLLMENT_SHA256

EXPECTED_ALPHA_V4_ENROLLMENT_SHA256 = (
    "e4c83174c1800c135d0fe9ac03b5cdfcc5f11e5517f871b3f198586973a20c31"
)
EXPECTED_ALPHA_V4_IDENTITY_SHA256 = (
    "e0324009614f755f2251a5b27d29587b0c43015385a78d567b328776b92239a5"
)


def _validate_seals() -> None:
    if len(ALPHA_ENTRIES) != PARENT_ALPHA_V3_COUNT + BERTRAND_V4_EXPECTED_COUNT:
        raise EditionV4Error("Alpha v4 theorem count changed")
    if tuple(
        entry.spec.name for entry in ALPHA_ENTRIES[BERTRAND_V4_START_INDEX:]
    ) != BERTRAND_V4_EXPECTED_NAMES:
        raise EditionV4Error("Alpha v4 Bertrand append order changed")
    parent = ALPHA_ENTRIES[:PARENT_ALPHA_V3_COUNT]
    if _enrollment_identity(parent) != PARENT_ALPHA_V3_ENROLLMENT_SHA256:
        raise EditionV4Error("Alpha v4 no longer preserves its v3 parent ledger")
    if _identity(EditionName.ALPHA, parent) != PARENT_ALPHA_V3_IDENTITY_SHA256:
        raise EditionV4Error("Alpha v4 changed v3 edition metadata")
    if STABLE_SPECS != v3.STABLE_SPECS or len(STABLE_SPECS) != 432:
        raise EditionV4Error("Stable v4 view changed the sealed 432-row release")
    if STABLE_EDITION.identity_sha256 != v3.STABLE_EDITION.identity_sha256:
        raise EditionV4Error("Stable v4 metadata changed")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (2891, 45):
        raise EditionV4Error("Alpha v4 topology seal changed")
    if ALPHA_V4_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V4_ENROLLMENT_SHA256:
        raise EditionV4Error("Alpha v4 enrollment identity changed")
    if ALPHA_V4_IDENTITY_SHA256 != EXPECTED_ALPHA_V4_IDENTITY_SHA256:
        raise EditionV4Error("Alpha v4 edition identity changed")

    membership = Counter(entry.membership for entry in ALPHA_ENTRIES)
    evidence = Counter(entry.evidence for entry in ALPHA_ENTRIES)
    origins = Counter(entry.enrollment_origin for entry in ALPHA_ENTRIES)
    if membership != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 533,
    }:
        raise EditionV4Error("Alpha v4 release-membership counts changed")
    if evidence != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 394,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }:
        raise EditionV4Error("Alpha v4 evidence counts changed")
    expected_origin_counts = {
        EnrollmentOrigin.STABLE: 432,
        EnrollmentOrigin.QR: 316,
        EnrollmentOrigin.HA: 120,
        EnrollmentOrigin.K3B: 17,
        EnrollmentOrigin.K3C: 17,
        EnrollmentOrigin.BERTRAND_B0_INTERVAL: 4,
        EnrollmentOrigin.BERTRAND_B1_POWER_ORDER: 4,
        EnrollmentOrigin.BERTRAND_B1_POWER_GROWTH: 3,
        EnrollmentOrigin.BERTRAND_B2_BOUNDED_VALUATION: 10,
        EnrollmentOrigin.BERTRAND_B2_VALUATION_LAWS: 6,
        EnrollmentOrigin.BERTRAND_B2_VALUATION_MULTIPLICATION: 11,
        EnrollmentOrigin.BERTRAND_B6_INTEGER_ENVELOPE: 5,
        EnrollmentOrigin.BERTRAND_B6_CEIL_SQRT: 9,
        EnrollmentOrigin.BERTRAND_B6_FLOOR_SQRT_TOTAL: 4,
        EnrollmentOrigin.BERTRAND_B6_QUOTIENT_BUDGET: 7,
    }
    if origins != expected_origin_counts:
        raise EditionV4Error("Alpha v4 enrollment-origin counts changed")
    if len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionV4Error("body-only Round-2 rows changed checked-use count")
    checked = {spec.name for spec in ALPHA_CHECKED_SPECS}
    for spec in ALPHA_CHECKED_SPECS:
        if not set(spec.dependencies) <= checked:
            raise EditionV4Error(
                f"checked theorem {spec.name!r} depends on unchecked evidence"
            )
    for entry in ALPHA_ENTRIES[BERTRAND_V4_START_INDEX:]:
        if (
            entry.membership is not Membership.ALPHA_ONLY
            or entry.evidence is not EvidenceStatus.BODY_CHECKED
            or entry.provenance != (entry.enrollment_origin,)
            or not entry.enrollment_origin.value.startswith("bertrand_")
        ):
            raise EditionV4Error(
                "Round-2 membership/evidence/origin seal changed"
            )


_validate_seals()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV4Error(f"unknown theorem-library v4 edition {value!r}")


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
        raise EditionV4ReplayError(
            f"unknown {selected_name.value} v4 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV4ReplayError(
            f"{selected_name.value} v4 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    return v3.replay(item.spec.name, edition=selected_name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V4_ENROLLMENT_SHA256",
    "ALPHA_V4_IDENTITY_SHA256",
    "BERTRAND_V4_START_INDEX",
    "EXPECTED_ALPHA_V4_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V4_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV4Error",
    "EditionV4ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "LibraryEdition",
    "Membership",
    "PARENT_ALPHA_V3_COUNT",
    "PARENT_ALPHA_V3_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V3_IDENTITY_SHA256",
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
