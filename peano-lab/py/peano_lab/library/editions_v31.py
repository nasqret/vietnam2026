"""Additive checked Alpha-v31 over the immutable v30 and Stable editions.

All 574 completed research specifications are enrolled exactly once. Checked
use loads the selected family's unchanged complete proof artifact, checks every
body with the original HA kernel, then materializes and rechecks an ordinary
empty-context certificate. Neither hashes nor prior receipts replace proof
checking. Browser metadata and Stable use require no proof artifacts.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..kernel.checker import check
from ..kernel.formulas import Imp
from . import editions_v30 as v30
from .alpha_enrollment_v31 import (
    EXPECTED_CAMPAIGN_COUNTS, FRONTIER_V31_EXPECTED_COUNT,
    FRONTIER_V31_EXPECTED_EDGE_COUNT, FRONTIER_V31_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V30_COUNT, PARENT_ALPHA_V30_ENROLLMENT_SHA256,
    PARENT_ALPHA_V30_IDENTITY_SHA256, alpha_v31_enrollment,
)
from . import campaign_completed_lower_closure as completed_lower
from .campaign_gaussian_factorization_closure import compile_gaussian_factorization_replay
from .editions_v5 import _topology
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS, LayeredReplayBundle, LayeredReplayNode,
    intern_layered_replay_bodies,
)
from .proof_bundle import (
    BundleNode, CheckedProofBundle, ProofBundle, ProofBundleError, decode_proof_bundle,
)
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


EditionName = v30.EditionName
Membership = v30.Membership
EvidenceStatus = v30.EvidenceStatus
EnrollmentOrigin = v30.EnrollmentOrigin
EditionEntry = v30.EditionEntry
LibraryEdition = v30.LibraryEdition

EXPECTED_ALPHA_V31_COUNT = 3796
EXPECTED_ALPHA_V31_CHECKED_USE_COUNT = 3796
EXPECTED_ALPHA_V31_FRONTIER_COUNT = 574
EXPECTED_ALPHA_V31_EDGE_COUNT = 12248
EXPECTED_ALPHA_V31_LAYER_COUNT = 53
EXPECTED_ALPHA_V31_ENROLLMENT_SHA256 = "e4f6330197152cab52427ea724c488390e1cd3bd50a77c09746161cb0d343768"
EXPECTED_ALPHA_V31_IDENTITY_SHA256 = "902fa75c2bf4624bb7fc5aca9a6c49b71ff8fa4499f8bdf9ce726cfd4166a5d7"
COMPLETED_LOWER_FAMILIES = completed_lower.COMPLETED_LOWER_FAMILIES
FAMILY_BY_NAME = completed_lower.FAMILY_BY_NAME
COMPLETED_LOWER_ARTIFACT_FILENAMES = MappingProxyType({
    family.slug: family.artifact_filename for family in COMPLETED_LOWER_FAMILIES
})
PYODIDE_COMPLETED_LOWER_BUNDLE_PATHS = MappingProxyType({
    slug: f"/lab/proof-artifacts/{filename}"
    for slug, filename in COMPLETED_LOWER_ARTIFACT_FILENAMES.items()
})


class EditionV31Error(ValueError):
    """The immutable parent, exact additive inventory or metadata seal changed."""


class EditionV31ReplayError(EditionV31Error):
    """Checked use requires complete unchanged-kernel-accepted proof data."""


def dependency_depths(specs):
    return v30.dependency_depths(specs)


def dependency_layers(specs):
    return v30.dependency_layers(specs)


def _stream_enrollment_identity(entries: tuple[EditionEntry, ...]) -> str:
    """The exact old separator encoding, without a whole-edition temporary."""
    digest = sha256()
    for index, item in enumerate(entries):
        if index:
            digest.update(b"\x1c")
        fields = (
            item.enrollment_origin.value, item.spec.name, item.spec.statement,
            "\x1e".join(item.spec.dependencies), "\x1e".join(item.spec.script),
        )
        for field_index, value in enumerate(fields):
            if field_index:
                digest.update(b"\x1f")
            digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def _stream_identity(name: EditionName, entries: tuple[EditionEntry, ...]) -> str:
    """Byte-for-byte old sorted compact JSON, streamed one entry at a time.

    This is allocation scheduling only. The literal expected identity and
    every original field, encoding flag and array order remain unchanged.
    """
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = sha256()
    digest.update(b'{"edition":')
    digest.update(encoder.encode(name.value).encode("utf-8"))
    digest.update(b',"entries":[')
    for index, item in enumerate(entries):
        if index:
            digest.update(b",")
        record = {
            "name": item.spec.name, "statement": item.spec.statement,
            "dependencies": list(item.spec.dependencies), "script": list(item.spec.script),
            "summary": item.spec.summary, "membership": item.membership.value,
            "evidence": item.evidence.value, "enrollment_origin": item.enrollment_origin.value,
            "provenance": [origin.value for origin in item.provenance],
            "source_module": item.source_module,
        }
        for chunk in encoder.iterencode(record):
            digest.update(chunk.encode("utf-8"))
    digest.update(b"]}")
    return digest.hexdigest()


def _make_streamed_edition(name: EditionName, entries: tuple[EditionEntry, ...]) -> LibraryEdition:
    specs, depths, layers, edges = _topology(item.spec for item in entries)
    return LibraryEdition(
        name, entries, specs, MappingProxyType({item.spec.name: item for item in entries}),
        depths, layers, edges, len(layers), _stream_enrollment_identity(entries),
        _stream_identity(name, entries),
    )


_ENROLLMENT = alpha_v31_enrollment()
FRONTIER_NEW_NAMES = tuple(item.name for item in _ENROLLMENT.frontier_specs)
_FRONTIER_NEW_NAME_SET = frozenset(FRONTIER_NEW_NAMES)
_FRONTIER_ENTRIES = tuple(EditionEntry(
    spec=item, membership=Membership.ALPHA_ONLY, evidence=EvidenceStatus.ALPHA_CLOSED,
    enrollment_origin=EnrollmentOrigin.HA, provenance=(EnrollmentOrigin.HA,),
    source_module=_ENROLLMENT.source_by_name[item.name],
) for item in _ENROLLMENT.frontier_specs)
ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v30.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v30.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v30.STABLE_ENTRIES
STABLE_SPECS = v30.STABLE_SPECS
STABLE_EDITION = v30.STABLE_EDITION
ALPHA_EDITION = _make_streamed_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V31_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V31_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V31_ENROLLMENT_SHA256


def _validate_seals() -> None:
    completed_lower.validate_completed_lower_metadata()
    if (
        len(v30.ALPHA_ENTRIES) != PARENT_ALPHA_V30_COUNT
        or len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V31_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V31_CHECKED_USE_COUNT
        or EXPECTED_ALPHA_V31_COUNT != PARENT_ALPHA_V30_COUNT + FRONTIER_V31_EXPECTED_COUNT
        or EXPECTED_ALPHA_V31_CHECKED_USE_COUNT != EXPECTED_ALPHA_V31_COUNT
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v30.ALPHA_ENTRIES))
        or _stream_enrollment_identity(v30.ALPHA_ENTRIES) != PARENT_ALPHA_V30_ENROLLMENT_SHA256
        or _stream_identity(EditionName.ALPHA, v30.ALPHA_ENTRIES) != PARENT_ALPHA_V30_IDENTITY_SHA256
    ):
        raise EditionV31Error("Alpha-v31 changed its exact immutable Alpha-v30 parent")
    if (
        STABLE_EDITION is not v30.STABLE_EDITION or STABLE_ENTRIES is not v30.STABLE_ENTRIES
        or STABLE_SPECS is not v30.STABLE_SPECS
        or STABLE_RELEASE_ORDER is not v30.STABLE_RELEASE_ORDER or len(STABLE_SPECS) != 432
    ):
        raise EditionV31Error("Alpha-v31 changed the immutable Stable edition")
    if (
        len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V31_FRONTIER_COUNT
        or EXPECTED_ALPHA_V31_FRONTIER_COUNT != FRONTIER_V31_EXPECTED_COUNT
        or FRONTIER_NEW_NAMES != completed_lower.FRONTIER_NEW_NAMES
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V31_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V31_EXPECTED_EDGE_COUNT
        or Counter(_ENROLLMENT.campaign_by_name.values()) != EXPECTED_CAMPAIGN_COUNTS
        or ALPHA_EDITION.edge_count != EXPECTED_ALPHA_V31_EDGE_COUNT
        or ALPHA_EDITION.layer_count != EXPECTED_ALPHA_V31_LAYER_COUNT
        or ALPHA_V31_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V31_ENROLLMENT_SHA256
        or ALPHA_V31_IDENTITY_SHA256 != EXPECTED_ALPHA_V31_IDENTITY_SHA256
        or Counter(item.evidence for item in ALPHA_ENTRIES)
        != {EvidenceStatus.STABLE_CLOSED: 432, EvidenceStatus.ALPHA_CLOSED: len(ALPHA_ENTRIES) - 432}
    ):
        raise EditionV31Error("Alpha-v31 exact additive membership or graph seal changed")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if item.spec.name in available or not set(item.spec.dependencies) <= available:
            raise EditionV31Error(f"an unchecked or forward dependency changed: {item.spec.name}")
        available.add(item.spec.name)


_validate_seals()
_bundle_sources: dict[str, Path] = {}


def require_completed_lower_seal() -> None:
    """Metadata-only eligibility, never an artifact read or acceptance receipt."""
    try:
        v30.require_gaussian_factorization_seal()
    except v30.EditionV30Error as error:
        raise EditionV31ReplayError(
            "the immutable Alpha-v30 parent is not sealed for checked use"
        ) from error
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V31_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V31_CHECKED_USE_COUNT
        or len(FRONTIER_NEW_NAMES) != FRONTIER_V31_EXPECTED_COUNT
        or EXPECTED_ALPHA_V31_FRONTIER_COUNT != FRONTIER_V31_EXPECTED_COUNT
        or EXPECTED_ALPHA_V31_COUNT != PARENT_ALPHA_V30_COUNT + FRONTIER_V31_EXPECTED_COUNT
        or ALPHA_V31_IDENTITY_SHA256 != EXPECTED_ALPHA_V31_IDENTITY_SHA256
        or ALPHA_V31_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V31_ENROLLMENT_SHA256
    ):
        raise EditionV31ReplayError("Alpha-v31 is not sealed for checked use")
    try:
        completed_lower.validate_completed_lower_metadata()
    except completed_lower.CompletedLowerClosureError as error:
        raise EditionV31ReplayError("the completed-lower proof metadata is not sealed") from error


def _default_completed_lower_bundle_source(slug: str) -> Path:
    family = completed_lower.completed_lower_family(slug)
    pyodide = Path(PYODIDE_COMPLETED_LOWER_BUNDLE_PATHS[slug])
    if pyodide.is_file():
        return pyodide
    parents = Path(__file__).resolve().parents
    # A browser installation need not expose the source checkout layout.
    return parents[4] / family.artifact if len(parents) > 4 else pyodide


def set_completed_lower_bundle_source(slug: str, source: str | Path | None) -> None:
    """Select one exact artifact source and invalidate all new proof caches."""
    try:
        completed_lower.completed_lower_family(slug)
    except completed_lower.CompletedLowerClosureError as error:
        raise EditionV31ReplayError(str(error)) from error
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV31ReplayError("a completed-lower proof source must be a filesystem path")
    if source is None:
        _bundle_sources.pop(slug, None)
    else:
        _bundle_sources[slug] = Path(source)
    _checked_completed_lower_bundle.cache_clear()
    replay.cache_clear()
    completed_lower.clear_completed_lower_metadata_cache()


@lru_cache(maxsize=1)
def _checked_completed_lower_bundle(
    slug: str,
) -> tuple[ProofBundle, CheckedProofBundle, Mapping[str, int]]:
    require_completed_lower_seal()
    try:
        family = completed_lower.completed_lower_family(slug)
        source = _bundle_sources.get(slug) or _default_completed_lower_bundle_source(slug)
        payload = completed_lower.read_completed_lower_bundle_bytes(slug, source)
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        del payload
        receipt = completed_lower.check_completed_lower_proof_bundle(
            slug, bundle, target, parent_specs=v30.ALPHA_CHECKED_SPECS,
        )
        plan = completed_lower.completed_lower_plan(slug, parent_specs=v30.ALPHA_CHECKED_SPECS)
    except (
        completed_lower.CompletedLowerClosureError, ProofBundleError,
        OSError, RecursionError, TypeError, UnicodeError, ValueError,
    ) as error:
        raise EditionV31ReplayError(
            f"actual Alpha-v31 proof source or original-kernel check failed: {slug!r}"
        ) from error
    positions = plan.positions
    if (
        not set(family.owned_names) <= positions.keys()
        or receipt.kernel_calls != family.node_count
        or receipt.node_count != len(bundle.nodes)
        or receipt.total_body_nodes != family.body_nodes
    ):
        raise EditionV31ReplayError("the exact completed-lower artifact skipped an actual proof body")
    for name, position in positions.items():
        item = ALPHA_EDITION.by_name.get(name)
        node = bundle.nodes[position]
        if (
            item is None or type(node) is not BundleNode
            or node.target != _closed_formula(item.spec.statement)
            or node.dependencies != tuple(positions[dependency] for dependency in item.spec.dependencies)
        ):
            raise EditionV31ReplayError(f"the exact admitted theorem changed: {name!r}")
    return bundle, receipt, positions


def checked_completed_lower_bundle(
    slug: str,
) -> tuple[ProofBundle, CheckedProofBundle, Mapping[str, int]]:
    try:
        completed_lower.completed_lower_family(slug)
    except completed_lower.CompletedLowerClosureError as error:
        raise EditionV31ReplayError(str(error)) from error
    return _checked_completed_lower_bundle(slug)


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV31Error(f"unknown theorem-library v31 edition {value!r}")


def edition(name: EditionName | str = EditionName.STABLE) -> LibraryEdition:
    selected = _coerce_edition(name)
    if selected is EditionName.STABLE:
        return STABLE_EDITION
    require_completed_lower_seal()
    return ALPHA_EDITION


def entry(
    name: str, *, edition: EditionName | str = EditionName.STABLE,
) -> EditionEntry | None:
    if not isinstance(name, str):
        return None
    selected = globals()["edition"](edition)
    normalized = name.strip()
    return selected.by_name.get(normalized) or next((
        candidate for candidate in selected.entries
        if candidate.spec.name.casefold() == normalized.casefold()
    ), None)


def _replay_completed_lower_theorem(item: EditionEntry) -> CheckedTheorem:
    family = FAMILY_BY_NAME[item.spec.name]
    bundle, _receipt, positions = checked_completed_lower_bundle(family.slug)
    root = positions[item.spec.name]
    included: set[int] = set()
    pending = [root]
    while pending:
        position = pending.pop()
        if position not in included:
            included.add(position)
            pending.extend(bundle.nodes[position].dependencies)
    layered = LayeredReplayBundle(tuple(
        LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
        for node in bundle.nodes if node.node_id in included
    ), root)
    formula = _closed_formula(item.spec.statement)
    interned = intern_layered_replay_bodies(
        layered, formula, limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if (type(interned) is not LayeredReplayBundle or interned.root != layered.root
            or len(interned.nodes) != len(layered.nodes)):
        raise EditionV31ReplayError(f"the exact theorem exceeds unchanged sharing limits: {item.spec.name}")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV31ReplayError("conservative interning changed an exact theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV31ReplayError("the original kernel rejected an interned body")
    candidate = compile_gaussian_factorization_replay(
        interned, formula, limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or candidate.target != formula or not check((), candidate.certificate, formula):
        raise EditionV31ReplayError(
            f"the original empty-context kernel/resource gate rejected {item.spec.name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


@lru_cache(maxsize=1)
def replay(
    name: str, *, edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    selected = _coerce_edition(edition)
    item = entry(name, edition=selected)
    if item is None:
        raise EditionV31ReplayError(f"unknown {selected.value} v31 theorem {name!r}")
    if not item.checked_use:
        raise EditionV31ReplayError(f"the v31 theorem is not eligible for checked use: {item.spec.name!r}")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_completed_lower_theorem(item)
    return v30.replay(item.spec.name, edition=selected)


__all__ = (
    "ALPHA_ENTRIES", "ALPHA_SPECS", "ALPHA_CHECKED_SPECS", "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256", "ALPHA_V31_ENROLLMENT_SHA256", "ALPHA_V31_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V31_COUNT", "EXPECTED_ALPHA_V31_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V31_FRONTIER_COUNT", "EXPECTED_ALPHA_V31_EDGE_COUNT",
    "EXPECTED_ALPHA_V31_LAYER_COUNT", "EXPECTED_ALPHA_V31_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V31_IDENTITY_SHA256", "FRONTIER_NEW_NAMES",
    "COMPLETED_LOWER_FAMILIES", "FAMILY_BY_NAME", "COMPLETED_LOWER_ARTIFACT_FILENAMES",
    "PYODIDE_COMPLETED_LOWER_BUNDLE_PATHS", "EditionName", "Membership",
    "EvidenceStatus", "EnrollmentOrigin", "EditionEntry", "LibraryEdition",
    "EditionV31Error", "EditionV31ReplayError", "STABLE_RELEASE_ORDER",
    "STABLE_ENTRIES", "STABLE_SPECS", "STABLE_EDITION", "dependency_depths",
    "dependency_layers", "edition", "entry", "replay", "require_completed_lower_seal",
    "checked_completed_lower_bundle", "set_completed_lower_bundle_source",
)
