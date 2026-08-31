"""Additive checked Alpha-v33 over the immutable v32 and Stable editions.

All 121 completed polynomial execution/equivalence specifications are enrolled exactly once. Checked
use loads the selected family's unchanged complete proof artifact, checks every
body with the original HA kernel, then materializes and rechecks an ordinary
empty-context certificate. Neither hashes nor prior receipts replace proof
checking. Browser metadata and Stable use require no proof artifacts.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..kernel.checker import check
from ..kernel.formulas import Imp
from . import editions_v32 as v32
from .alpha_enrollment_v33 import (
    EXPECTED_CAMPAIGN_COUNTS, FRONTIER_V33_EXPECTED_COUNT,
    FRONTIER_V33_EXPECTED_EDGE_COUNT, FRONTIER_V33_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V32_COUNT, PARENT_ALPHA_V32_ENROLLMENT_SHA256,
    PARENT_ALPHA_V32_IDENTITY_SHA256, alpha_v33_enrollment,
)
from . import campaign_research_v33_closure as research
from .campaign_gaussian_factorization_closure import compile_gaussian_factorization_replay
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS, LayeredReplayBundle, LayeredReplayNode,
    intern_layered_replay_bodies,
)
from .proof_bundle import (
    BundleNode, CheckedProofBundle, ProofBundle, ProofBundleError, decode_proof_bundle,
)
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


EditionName = v32.EditionName
Membership = v32.Membership
EvidenceStatus = v32.EvidenceStatus
EnrollmentOrigin = v32.EnrollmentOrigin
EditionEntry = v32.EditionEntry
LibraryEdition = v32.LibraryEdition

EXPECTED_ALPHA_V33_COUNT = 4092
EXPECTED_ALPHA_V33_CHECKED_USE_COUNT = 4092
EXPECTED_ALPHA_V33_FRONTIER_COUNT = 121
EXPECTED_ALPHA_V33_EDGE_COUNT = 13212
EXPECTED_ALPHA_V33_LAYER_COUNT = 53
EXPECTED_ALPHA_V33_ENROLLMENT_SHA256 = "0d4101bfee06dfff5a49ee8cfaf955a2c81a43ac622623e27890d6fe541eeaa0"
EXPECTED_ALPHA_V33_IDENTITY_SHA256 = "9e66890600db5f787230fb5e48e18ce08026750ba4a9d3fa7b0b1e30f6e39a3d"
RESEARCH_FAMILIES = research.RESEARCH_FAMILIES
FAMILY_BY_NAME = research.FAMILY_BY_NAME
RESEARCH_ARTIFACT_FILENAMES = MappingProxyType({
    family.slug: family.artifact_filename for family in RESEARCH_FAMILIES
})
PYODIDE_RESEARCH_BUNDLE_PATHS = MappingProxyType({
    slug: f"/lab/proof-artifacts/{filename}"
    for slug, filename in RESEARCH_ARTIFACT_FILENAMES.items()
})


class EditionV33Error(ValueError):
    """The immutable parent, exact additive inventory or metadata seal changed."""


class EditionV33ReplayError(EditionV33Error):
    """Checked use requires complete unchanged-kernel-accepted proof data."""


def dependency_depths(specs):
    return v32.dependency_depths(specs)


def dependency_layers(specs):
    return v32.dependency_layers(specs)


# Exact inherited encoders and topology constructor; no old globals change.
_stream_enrollment_identity = v32._stream_enrollment_identity
_stream_identity = v32._stream_identity
_make_streamed_edition = v32._make_streamed_edition


_ENROLLMENT = alpha_v33_enrollment()
FRONTIER_NEW_NAMES = tuple(item.name for item in _ENROLLMENT.frontier_specs)
_FRONTIER_NEW_NAME_SET = frozenset(FRONTIER_NEW_NAMES)
_FRONTIER_ENTRIES = tuple(EditionEntry(
    spec=item, membership=Membership.ALPHA_ONLY, evidence=EvidenceStatus.ALPHA_CLOSED,
    enrollment_origin=EnrollmentOrigin.HA, provenance=(EnrollmentOrigin.HA,),
    source_module=_ENROLLMENT.source_by_name[item.name],
) for item in _ENROLLMENT.frontier_specs)
ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v32.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v32.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v32.STABLE_ENTRIES
STABLE_SPECS = v32.STABLE_SPECS
STABLE_EDITION = v32.STABLE_EDITION
ALPHA_EDITION = _make_streamed_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V33_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V33_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V33_ENROLLMENT_SHA256


def _validate_seals() -> None:
    research.validate_research_metadata()
    if (
        len(v32.ALPHA_ENTRIES) != PARENT_ALPHA_V32_COUNT
        or len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V33_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V33_CHECKED_USE_COUNT
        or EXPECTED_ALPHA_V33_COUNT != PARENT_ALPHA_V32_COUNT + FRONTIER_V33_EXPECTED_COUNT
        or EXPECTED_ALPHA_V33_CHECKED_USE_COUNT != EXPECTED_ALPHA_V33_COUNT
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v32.ALPHA_ENTRIES))
        or _stream_enrollment_identity(v32.ALPHA_ENTRIES) != PARENT_ALPHA_V32_ENROLLMENT_SHA256
        or _stream_identity(EditionName.ALPHA, v32.ALPHA_ENTRIES) != PARENT_ALPHA_V32_IDENTITY_SHA256
    ):
        raise EditionV33Error("Alpha-v33 changed its exact immutable Alpha-v32 parent")
    if (
        STABLE_EDITION is not v32.STABLE_EDITION or STABLE_ENTRIES is not v32.STABLE_ENTRIES
        or STABLE_SPECS is not v32.STABLE_SPECS
        or STABLE_RELEASE_ORDER is not v32.STABLE_RELEASE_ORDER or len(STABLE_SPECS) != 432
    ):
        raise EditionV33Error("Alpha-v33 changed the immutable Stable edition")
    if (
        len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V33_FRONTIER_COUNT
        or EXPECTED_ALPHA_V33_FRONTIER_COUNT != FRONTIER_V33_EXPECTED_COUNT
        or FRONTIER_NEW_NAMES != research.FRONTIER_NEW_NAMES
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V33_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V33_EXPECTED_EDGE_COUNT
        or Counter(_ENROLLMENT.campaign_by_name.values()) != EXPECTED_CAMPAIGN_COUNTS
        or ALPHA_EDITION.edge_count != EXPECTED_ALPHA_V33_EDGE_COUNT
        or ALPHA_EDITION.layer_count != EXPECTED_ALPHA_V33_LAYER_COUNT
        or ALPHA_V33_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V33_ENROLLMENT_SHA256
        or ALPHA_V33_IDENTITY_SHA256 != EXPECTED_ALPHA_V33_IDENTITY_SHA256
        or Counter(item.evidence for item in ALPHA_ENTRIES)
        != {EvidenceStatus.STABLE_CLOSED: 432, EvidenceStatus.ALPHA_CLOSED: len(ALPHA_ENTRIES) - 432}
    ):
        raise EditionV33Error("Alpha-v33 exact additive membership or graph seal changed")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if item.spec.name in available or not set(item.spec.dependencies) <= available:
            raise EditionV33Error(f"an unchecked or forward dependency changed: {item.spec.name}")
        available.add(item.spec.name)


_validate_seals()
_bundle_sources: dict[str, Path] = {}


def require_research_seal() -> None:
    """Metadata-only eligibility, never an artifact read or acceptance receipt."""
    try:
        v32.require_research_seal()
    except v32.EditionV32Error as error:
        raise EditionV33ReplayError(
            "the immutable Alpha-v32 parent is not sealed for checked use"
        ) from error
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V33_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V33_CHECKED_USE_COUNT
        or len(FRONTIER_NEW_NAMES) != FRONTIER_V33_EXPECTED_COUNT
        or EXPECTED_ALPHA_V33_FRONTIER_COUNT != FRONTIER_V33_EXPECTED_COUNT
        or EXPECTED_ALPHA_V33_COUNT != PARENT_ALPHA_V32_COUNT + FRONTIER_V33_EXPECTED_COUNT
        or ALPHA_V33_IDENTITY_SHA256 != EXPECTED_ALPHA_V33_IDENTITY_SHA256
        or ALPHA_V33_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V33_ENROLLMENT_SHA256
    ):
        raise EditionV33ReplayError("Alpha-v33 is not sealed for checked use")
    try:
        research.validate_research_metadata()
    except research.ResearchClosureError as error:
        raise EditionV33ReplayError("the research-v33 proof metadata is not sealed") from error


def _default_research_bundle_source(slug: str) -> Path:
    family = research.research_family(slug)
    pyodide = Path(PYODIDE_RESEARCH_BUNDLE_PATHS[slug])
    if pyodide.is_file():
        return pyodide
    parents = Path(__file__).resolve().parents
    # A browser installation need not expose the source checkout layout.
    return parents[4] / family.artifact if len(parents) > 4 else pyodide


def set_research_bundle_source(slug: str, source: str | Path | None) -> None:
    """Select one exact artifact source and invalidate all new proof caches."""
    try:
        research.research_family(slug)
    except research.ResearchClosureError as error:
        raise EditionV33ReplayError(str(error)) from error
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV33ReplayError("a research-v33 proof source must be a filesystem path")
    if source is None:
        _bundle_sources.pop(slug, None)
    else:
        _bundle_sources[slug] = Path(source)
    _checked_research_bundle.cache_clear()
    replay.cache_clear()
    research.clear_research_metadata_cache()


@lru_cache(maxsize=1)
def _checked_research_bundle(
    slug: str,
) -> tuple[ProofBundle, CheckedProofBundle, Mapping[str, int]]:
    require_research_seal()
    try:
        family = research.research_family(slug)
        source = _bundle_sources.get(slug) or _default_research_bundle_source(slug)
        payload = research.read_research_bundle_bytes(slug, source)
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        del payload
        receipt = research.check_research_proof_bundle(
            slug, bundle, target, parent_specs=v32.ALPHA_CHECKED_SPECS,
        )
        plan = research.research_plan(slug, parent_specs=v32.ALPHA_CHECKED_SPECS)
    except (
        research.ResearchClosureError, ProofBundleError,
        OSError, RecursionError, TypeError, UnicodeError, ValueError,
    ) as error:
        raise EditionV33ReplayError(
            f"actual Alpha-v33 proof source or original-kernel check failed: {slug!r}"
        ) from error
    positions = plan.positions
    if (
        not set(family.owned_names) <= positions.keys()
        or receipt.kernel_calls != family.node_count
        or receipt.node_count != len(bundle.nodes)
        or receipt.total_body_nodes != family.body_nodes
    ):
        raise EditionV33ReplayError("the exact research-v33 artifact skipped an actual proof body")
    for name, position in positions.items():
        item = ALPHA_EDITION.by_name.get(name)
        node = bundle.nodes[position]
        if (
            item is None or type(node) is not BundleNode
            or node.target != _closed_formula(item.spec.statement)
            or node.dependencies != tuple(positions[dependency] for dependency in item.spec.dependencies)
        ):
            raise EditionV33ReplayError(f"the exact admitted theorem changed: {name!r}")
    return bundle, receipt, positions


def checked_research_bundle(
    slug: str,
) -> tuple[ProofBundle, CheckedProofBundle, Mapping[str, int]]:
    try:
        research.research_family(slug)
    except research.ResearchClosureError as error:
        raise EditionV33ReplayError(str(error)) from error
    return _checked_research_bundle(slug)


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV33Error(f"unknown theorem-library v33 edition {value!r}")


def edition(name: EditionName | str = EditionName.STABLE) -> LibraryEdition:
    selected = _coerce_edition(name)
    if selected is EditionName.STABLE:
        return STABLE_EDITION
    require_research_seal()
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


def _replay_research_theorem(item: EditionEntry) -> CheckedTheorem:
    family = FAMILY_BY_NAME[item.spec.name]
    bundle, _receipt, positions = checked_research_bundle(family.slug)
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
        raise EditionV33ReplayError(f"the exact theorem exceeds unchanged sharing limits: {item.spec.name}")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV33ReplayError("conservative interning changed an exact theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV33ReplayError("the original kernel rejected an interned body")
    candidate = compile_gaussian_factorization_replay(
        interned, formula, limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or candidate.target != formula or not check((), candidate.certificate, formula):
        raise EditionV33ReplayError(
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
        raise EditionV33ReplayError(f"unknown {selected.value} v33 theorem {name!r}")
    if not item.checked_use:
        raise EditionV33ReplayError(f"the v33 theorem is not eligible for checked use: {item.spec.name!r}")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_research_theorem(item)
    return v32.replay(item.spec.name, edition=selected)


__all__ = (
    "ALPHA_ENTRIES", "ALPHA_SPECS", "ALPHA_CHECKED_SPECS", "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256", "ALPHA_V33_ENROLLMENT_SHA256", "ALPHA_V33_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V33_COUNT", "EXPECTED_ALPHA_V33_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V33_FRONTIER_COUNT", "EXPECTED_ALPHA_V33_EDGE_COUNT",
    "EXPECTED_ALPHA_V33_LAYER_COUNT", "EXPECTED_ALPHA_V33_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V33_IDENTITY_SHA256", "FRONTIER_NEW_NAMES",
    "RESEARCH_FAMILIES", "FAMILY_BY_NAME", "RESEARCH_ARTIFACT_FILENAMES",
    "PYODIDE_RESEARCH_BUNDLE_PATHS", "EditionName", "Membership",
    "EvidenceStatus", "EnrollmentOrigin", "EditionEntry", "LibraryEdition",
    "EditionV33Error", "EditionV33ReplayError", "STABLE_RELEASE_ORDER",
    "STABLE_ENTRIES", "STABLE_SPECS", "STABLE_EDITION", "dependency_depths",
    "dependency_layers", "edition", "entry", "replay", "require_research_seal",
    "checked_research_bundle", "set_research_bundle_source",
)
