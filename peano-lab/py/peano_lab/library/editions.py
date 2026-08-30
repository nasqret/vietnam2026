"""Canonical stable and alpha editions of the Peano theorem library.

The stable edition is the existing checked :data:`theorems.THEOREMS` tuple,
unchanged.  Alpha is a cumulative specification inventory whose membership is
independent of proof evidence.  Consequently, appearing in alpha does *not*
make a theorem available to ``use``: only ``stable_closed`` and
``alpha_closed`` entries cross the checked-use boundary.

No proof is replayed at import time.  The alpha replay path reconstructs and
kernel-checks a complete empty-context certificate only after the evidence
gate has accepted the requested entry.

This module seals channel v1.  Its 432 Stable rows happen to be the initial
Alpha prefix.  That is not a general promotion invariant: a later channel
version must preserve this enrollment ledger and its origins, while deriving
Stable as an exact keyed subset with its own append-only release order.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from functools import lru_cache
from hashlib import sha256
import json
from types import MappingProxyType

from ..engine.state import proof_size, start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.checker import check
from ..kernel.formulas import Imp
from ..kernel.proofs import Cut, ImpIntro
from .alpha_enrollment import (
    ALPHA_QR_ROOT_NAME,
    EnrollmentSource,
    HA_QR_COMPATIBLE_OVERLAP,
    HA_CLOSED_ENROLLMENT_MANIFEST,
    K3B_CLOSED_ENROLLMENT_MANIFEST,
    alpha_enrollment,
)
from .theorems import (
    THEOREMS,
    CheckedTheorem,
    LibraryError,
    TheoremSpec,
    _closed_formula,
    _primitive,
    replay as replay_stable,
)


class EditionError(ValueError):
    """An edition name, manifest, or topology violates the runtime contract."""


class EditionReplayError(EditionError):
    """An edition theorem is absent or lacks checked-use evidence."""


class EditionName(str, Enum):
    """Supported theorem-library editions."""

    STABLE = "stable"
    ALPHA = "alpha"


class Membership(str, Enum):
    """Release membership, independent of evidence and historical origin."""

    STABLE = "stable"
    ALPHA_ONLY = "alpha_only"


class EnrollmentOrigin(str, Enum):
    """Immutable tranche that first enrolled a specification in alpha."""

    STABLE = "stable"
    QR = "qr"
    HA = "ha"
    K3B = "k3b"


class EvidenceStatus(str, Enum):
    """Evidence available for one enrolled specification."""

    STABLE_CLOSED = "stable_closed"
    ALPHA_CLOSED = "alpha_closed"
    BODY_CHECKED = "body_checked"
    PENDING_LAYERED_CLOSURE = "pending_layered_closure"

    @property
    def checked_use(self) -> bool:
        """Whether this evidence permits empty-context theorem use."""

        return self in {
            EvidenceStatus.STABLE_CLOSED,
            EvidenceStatus.ALPHA_CLOSED,
        }


@dataclass(frozen=True, slots=True)
class EditionEntry:
    """One enrolled specification with separate provenance and evidence."""

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
        """Return actual edition membership without inferring proof evidence."""

        if self.membership is Membership.STABLE:
            return frozenset({EditionName.STABLE, EditionName.ALPHA})
        return frozenset({EditionName.ALPHA})


@dataclass(frozen=True, slots=True)
class LibraryEdition:
    """One validated, immutable theorem edition."""

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
        return tuple(item for item in self.entries if item.checked_use)

    @property
    def checked_specs(self) -> tuple[TheoremSpec, ...]:
        return tuple(item.spec for item in self.entries if item.checked_use)


def _topology(
    specs: Iterable[TheoremSpec],
) -> tuple[
    tuple[TheoremSpec, ...],
    Mapping[str, int],
    tuple[tuple[TheoremSpec, ...], ...],
    int,
]:
    ordered = tuple(specs)
    by_name: dict[str, TheoremSpec] = {}
    depths: dict[str, int] = {}
    edge_count = 0
    for spec in ordered:
        if type(spec) is not TheoremSpec:
            raise EditionError("edition entries must contain exact TheoremSpec values")
        if spec.name in by_name:
            raise EditionError(f"duplicate edition theorem {spec.name!r}")
        for dependency in spec.dependencies:
            if dependency not in by_name:
                raise EditionError(
                    f"non-topological or missing dependency {dependency!r} "
                    f"for edition theorem {spec.name!r}"
                )
        by_name[spec.name] = spec
        depths[spec.name] = (
            0
            if not spec.dependencies
            else 1 + max(depths[dependency] for dependency in spec.dependencies)
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
    """Validate an ordered graph and return immutable dependency depths."""

    return _topology(specs)[1]


def dependency_layers(
    specs: Iterable[TheoremSpec],
) -> tuple[tuple[TheoremSpec, ...], ...]:
    """Validate an ordered graph and group its rows by dependency depth."""

    return _topology(specs)[2]


def _identity(name: EditionName, entries: tuple[EditionEntry, ...]) -> str:
    rows = [
        {
            "name": item.spec.name,
            "statement": item.spec.statement,
            "dependencies": list(item.spec.dependencies),
            "script": list(item.spec.script),
            "summary": item.spec.summary,
            "membership": item.membership.value,
            "evidence": item.evidence.value,
            "enrollment_origin": item.enrollment_origin.value,
            "provenance": [source.value for source in item.provenance],
            "source_module": item.source_module,
        }
        for item in entries
    ]
    payload = json.dumps(
        {"edition": name.value, "entries": rows},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return sha256(payload).hexdigest()


def _enrollment_identity(entries: tuple[EditionEntry, ...]) -> str:
    """Hash immutable origin and proof-source data in canonical alpha order."""

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
        for item in entries
    )
    return sha256("\x1c".join(rows).encode("utf-8")).hexdigest()


def _make_edition(
    name: EditionName,
    entries: tuple[EditionEntry, ...],
) -> LibraryEdition:
    specs, depths, layers, edge_count = _topology(item.spec for item in entries)
    by_name = {item.spec.name: item for item in entries}
    if len(by_name) != len(entries):
        raise EditionError(f"duplicate rows in {name.value} edition")
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


def _stable_entries() -> tuple[EditionEntry, ...]:
    return tuple(
        EditionEntry(
            spec=spec,
            membership=Membership.STABLE,
            evidence=EvidenceStatus.STABLE_CLOSED,
            enrollment_origin=EnrollmentOrigin.STABLE,
            provenance=(EnrollmentOrigin.STABLE,),
            source_module="peano-lab/py/peano_lab/library/theorems.py",
        )
        for spec in THEOREMS
    )


def _alpha_entries() -> tuple[EditionEntry, ...]:
    enrollment = alpha_enrollment()
    result = list(_stable_entries())
    positions = {item.spec.name: index for index, item in enumerate(result)}
    source_prefix = "peano-lab/py/peano_lab/library"

    def manifest_sources(manifest: tuple[EnrollmentSource, ...]) -> dict[str, str]:
        sources: dict[str, str] = {}
        for source in manifest:
            path = f"{source_prefix}/{source.module}.py"
            for theorem_name in source.names:
                if theorem_name in sources:
                    raise EditionError(
                        f"duplicate alpha source owner for {theorem_name!r}"
                    )
                sources[theorem_name] = path
        return sources

    ha_sources = manifest_sources(HA_CLOSED_ENROLLMENT_MANIFEST)
    k3b_sources = manifest_sources(K3B_CLOSED_ENROLLMENT_MANIFEST)

    def append_new(
        spec: TheoremSpec,
        origin: EnrollmentOrigin,
        evidence: EvidenceStatus,
        source_module: str,
    ) -> None:
        if spec.name in positions:
            raise EditionError(
                f"unexpected duplicate alpha specification {spec.name!r}"
            )
        positions[spec.name] = len(result)
        result.append(
            EditionEntry(
                spec,
                Membership.ALPHA_ONLY,
                evidence,
                origin,
                (origin,),
                source_module,
            )
        )

    for spec in enrollment.qr_specs:
        evidence = (
            EvidenceStatus.PENDING_LAYERED_CLOSURE
            if spec.name == ALPHA_QR_ROOT_NAME
            else EvidenceStatus.BODY_CHECKED
        )
        qr_owner = enrollment.qr_stack.owner_by_name[spec.name]
        append_new(
            spec,
            EnrollmentOrigin.QR,
            evidence,
            f"{source_prefix}/{qr_owner}.py",
        )

    compatible_overlaps: list[str] = []
    for spec in enrollment.ha_specs:
        position = positions.get(spec.name)
        if position is None:
            append_new(
                spec,
                EnrollmentOrigin.HA,
                EvidenceStatus.ALPHA_CLOSED,
                ha_sources[spec.name],
            )
            continue
        existing = result[position]
        if existing.spec != spec:
            raise EditionError(
                f"incompatible alpha overlap for theorem {spec.name!r}"
            )
        if existing.enrollment_origin is not EnrollmentOrigin.QR:
            raise EditionError(
                f"HA overlap {spec.name!r} did not originate in the QR tranche"
            )
        if EnrollmentOrigin.HA in existing.provenance:
            raise EditionError(f"duplicate HA provenance for {spec.name!r}")
        result[position] = replace(
            existing,
            evidence=EvidenceStatus.ALPHA_CLOSED,
            provenance=existing.provenance + (EnrollmentOrigin.HA,),
        )
        compatible_overlaps.append(spec.name)

    if compatible_overlaps != [HA_QR_COMPATIBLE_OVERLAP]:
        raise EditionError(
            f"unexpected compatible alpha overlaps: {compatible_overlaps!r}"
        )
    for spec in enrollment.k3b_specs:
        append_new(
            spec,
            EnrollmentOrigin.K3B,
            EvidenceStatus.ALPHA_CLOSED,
            k3b_sources[spec.name],
        )
    return tuple(result)


STABLE_ENTRIES: tuple[EditionEntry, ...] = _stable_entries()
ALPHA_ENTRIES: tuple[EditionEntry, ...] = _alpha_entries()
STABLE_SPECS: tuple[TheoremSpec, ...] = THEOREMS
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)

STABLE_EDITION = _make_edition(EditionName.STABLE, STABLE_ENTRIES)
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256


def _validate_seals() -> None:
    if STABLE_EDITION.specs is not STABLE_SPECS:
        # _make_edition materializes the generator; equality, not identity, is
        # the actual invariant.  This branch documents that distinction.
        if STABLE_EDITION.specs != STABLE_SPECS:
            raise EditionError("stable edition changed while constructing editions")
    # Initial-channel seal only.  Future promotions must not generalize this
    # into a prefix rule; see the module-level channel-version contract.
    if ALPHA_SPECS[: len(STABLE_SPECS)] != STABLE_SPECS:
        raise EditionError("alpha does not preserve the exact stable prefix")
    if (len(STABLE_SPECS), STABLE_EDITION.edge_count, STABLE_EDITION.layer_count) != (
        432,
        1185,
        22,
    ):
        raise EditionError("stable edition count/topology seal changed")
    if (len(ALPHA_SPECS), ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        885,
        2641,
        45,
    ):
        raise EditionError("alpha edition count/topology seal changed")
    counts = Counter(item.evidence for item in ALPHA_ENTRIES)
    expected = {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 138,
        EvidenceStatus.BODY_CHECKED: 314,
        EvidenceStatus.PENDING_LAYERED_CLOSURE: 1,
    }
    if counts != expected:
        raise EditionError(f"alpha evidence seal changed: {dict(counts)!r}")
    membership_counts = Counter(item.membership for item in ALPHA_ENTRIES)
    if membership_counts != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 453,
    }:
        raise EditionError(
            f"alpha release-membership seal changed: {dict(membership_counts)!r}"
        )
    origin_counts = Counter(item.enrollment_origin for item in ALPHA_ENTRIES)
    if origin_counts != {
        EnrollmentOrigin.STABLE: 432,
        EnrollmentOrigin.QR: 316,
        EnrollmentOrigin.HA: 120,
        EnrollmentOrigin.K3B: 17,
    }:
        raise EditionError(
            f"alpha enrollment-origin seal changed: {dict(origin_counts)!r}"
        )
    if len(ALPHA_CHECKED_SPECS) != 570:
        raise EditionError("alpha checked-use seal changed")
    checked_names = {spec.name for spec in ALPHA_CHECKED_SPECS}
    checked_edges = sum(len(spec.dependencies) for spec in ALPHA_CHECKED_SPECS)
    if checked_edges != 1485:
        raise EditionError("alpha checked-use edge seal changed")
    for spec in ALPHA_CHECKED_SPECS:
        unavailable = set(spec.dependencies).difference(checked_names)
        if unavailable:
            raise EditionError(
                f"checked-use theorem {spec.name!r} depends on unchecked rows "
                f"{sorted(unavailable)!r}"
            )
    root = ALPHA_EDITION.by_name.get(ALPHA_QR_ROOT_NAME)
    if root is None or root.evidence is not EvidenceStatus.PENDING_LAYERED_CLOSURE:
        raise EditionError("quadratic-reciprocity alpha root evidence changed")
    if ALPHA_SPECS[-1].name != "cell_list_extensional":
        raise EditionError("alpha terminal K3B row changed")
    if ALPHA_ENROLLMENT_SHA256 != (
        "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
    ):
        raise EditionError(
            "canonical alpha enrollment identity changed: "
            f"{ALPHA_ENROLLMENT_SHA256}"
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
    raise EditionError(f"unknown theorem-library edition {value!r}")


def edition(name: EditionName | str = EditionName.STABLE) -> LibraryEdition:
    """Return one immutable library edition; stable remains the default."""

    selected = _coerce_edition(name)
    return STABLE_EDITION if selected is EditionName.STABLE else ALPHA_EDITION


def entry(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> EditionEntry | None:
    """Look up an edition row by exact or case-folded canonical name."""

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
def _replay_alpha_closed(name: str) -> CheckedTheorem:
    item = ALPHA_EDITION.by_name.get(name)
    if item is None:
        raise EditionReplayError(f"unknown alpha theorem {name!r}")
    if not item.checked_use:
        raise EditionReplayError(
            f"alpha theorem {name!r} has evidence {item.evidence.value!r}; "
            "checked theorem use requires stable_closed or alpha_closed"
        )
    if item.evidence is EvidenceStatus.STABLE_CLOSED:
        return replay_stable(name)

    spec = item.spec
    target = _closed_formula(spec.statement)
    dependency_entries: list[EditionEntry] = []
    for dependency in spec.dependencies:
        dependency_entry = ALPHA_EDITION.by_name[dependency]
        if not dependency_entry.checked_use:
            raise EditionReplayError(
                f"checked alpha theorem {name!r} depends on unchecked theorem "
                f"{dependency!r}"
            )
        dependency_entries.append(dependency_entry)
    for dependency_entry in reversed(dependency_entries):
        target = Imp(_closed_formula(dependency_entry.spec.statement), target)

    try:
        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)
    except Exception as exc:
        raise EditionReplayError(f"alpha replay failed for {name!r}: {exc}") from exc

    closed = certificate
    dependency_proofs = tuple(
        _replay_alpha_closed(dependency).certificate
        for dependency in spec.dependencies
    )
    for dependency in spec.dependencies:
        if type(closed) is not ImpIntro:
            raise EditionReplayError(
                f"alpha replay for {name!r} did not expose dependency {dependency!r}"
            )
        closed = closed.body
    formula = _closed_formula(spec.statement)
    dependency_formulas = tuple(
        _closed_formula(item.spec.statement) for item in dependency_entries
    )
    for dependency_formula, dependency_proof in reversed(
        tuple(zip(dependency_formulas, dependency_proofs, strict=True))
    ):
        closed = Cut(dependency_formula, formula, dependency_proof, closed)
    if not check((), closed, formula):
        raise EditionReplayError(
            f"independent kernel rejected alpha theorem {name!r}"
        )
    return CheckedTheorem(spec, formula, closed, proof_size(closed))


def replay(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    """Replay a checked-use theorem from one edition, failing closed."""

    selected_name = _coerce_edition(edition)
    item = entry(name, edition=selected_name)
    if item is None:
        raise EditionReplayError(
            f"unknown {selected_name.value} theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionReplayError(
            f"{selected_name.value} theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    if selected_name is EditionName.STABLE:
        try:
            return replay_stable(item.spec.name)
        except LibraryError as exc:
            raise EditionReplayError(str(exc)) from exc
    return _replay_alpha_closed(item.spec.name)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_QR_ROOT_NAME",
    "ALPHA_SPECS",
    "EditionEntry",
    "EditionError",
    "EditionName",
    "EditionReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "LibraryEdition",
    "Membership",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_SPECS",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
]
