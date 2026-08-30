"""Fail-closed additive research frontier over the immutable Alpha-v23 release.

Every new theorem becomes usable only after its exact ordinary proof body and
entire historical dependency cone pass the unchanged intuitionistic kernel.
The unchanged 432-theorem Stable edition never inherits Alpha-only authority.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import ModuleType

from ..kernel.checker import check
from ..kernel.formulas import Imp
from . import editions_v23 as v23
from .alpha_enrollment_v24 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V24_EXPECTED_COUNT,
    FRONTIER_V24_EXPECTED_EDGE_COUNT,
    FRONTIER_V24_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V23_COUNT,
    PARENT_ALPHA_V23_ENROLLMENT_SHA256,
    PARENT_ALPHA_V23_IDENTITY_SHA256,
    alpha_v24_enrollment,
)
from .editions_v5 import _enrollment_identity, _identity, _make_edition
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayNode,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from .proof_bundle import (
    BundleNode,
    CheckedProofBundle,
    ProofBundle,
    ProofBundleError,
    decode_proof_bundle,
)
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


EditionName = v23.EditionName
Membership = v23.Membership
EvidenceStatus = v23.EvidenceStatus
EnrollmentOrigin = v23.EnrollmentOrigin
EditionEntry = v23.EditionEntry
LibraryEdition = v23.LibraryEdition

# Zero or empty values never authorize actual theorem replay. Freeze only
# after all dependency-closed original proofs and their release are checked.
EXPECTED_ALPHA_V24_COUNT = 2_008
EXPECTED_ALPHA_V24_CHECKED_USE_COUNT = 2_008
EXPECTED_ALPHA_V24_FRONTIER_COUNT = 59
EXPECTED_ALPHA_V24_EDGE_COUNT = 6_423
EXPECTED_ALPHA_V24_LAYER_COUNT = 53
EXPECTED_ALPHA_V24_ENROLLMENT_SHA256 = (
    "7463b938ffb87fe85eea6cd0e40c10ac73c799087ca1c408a070fcbe2687d4e1"
)
EXPECTED_ALPHA_V24_IDENTITY_SHA256 = (
    "1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b"
)
RESEARCH_LAYER_ARTIFACT_FILENAME = "alpha-v24-research-layer-proof-bundle-v1.json"
PYODIDE_RESEARCH_LAYER_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{RESEARCH_LAYER_ARTIFACT_FILENAME}"
)


class EditionV24Error(ValueError):
    """The immutable parent, additive theorem inventory, or seal changed."""


class EditionV24ReplayError(EditionV24Error):
    """Checked use requires complete unchanged-kernel-accepted proof bytes."""


def dependency_depths(specs):
    return v23.dependency_depths(specs)


def dependency_layers(specs):
    return v23.dependency_layers(specs)


_ENROLLMENT = alpha_v24_enrollment()
FRONTIER_NEW_NAMES = tuple(item.name for item in _ENROLLMENT.frontier_specs)
_FRONTIER_NEW_NAME_SET = frozenset(FRONTIER_NEW_NAMES)
_FRONTIER_ENTRIES = tuple(
    EditionEntry(
        spec=item,
        membership=Membership.ALPHA_ONLY,
        evidence=EvidenceStatus.ALPHA_CLOSED,
        enrollment_origin=EnrollmentOrigin.HA,
        provenance=(EnrollmentOrigin.HA,),
        source_module=_ENROLLMENT.source_by_name[item.name],
    )
    for item in _ENROLLMENT.frontier_specs
)
ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v23.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v23.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v23.STABLE_ENTRIES
STABLE_SPECS = v23.STABLE_SPECS
STABLE_EDITION = v23.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V24_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V24_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V24_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(v23.ALPHA_ENTRIES) != PARENT_ALPHA_V23_COUNT
        or tuple(ALPHA_ENTRIES[:PARENT_ALPHA_V23_COUNT]) != v23.ALPHA_ENTRIES
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v23.ALPHA_ENTRIES))
        or _enrollment_identity(v23.ALPHA_ENTRIES) != PARENT_ALPHA_V23_ENROLLMENT_SHA256
        or _identity(EditionName.ALPHA, v23.ALPHA_ENTRIES)
        != PARENT_ALPHA_V23_IDENTITY_SHA256
    ):
        raise EditionV24Error("Alpha-v24 changed its immutable checked Alpha-v23 parent")
    if (
        STABLE_EDITION is not v23.STABLE_EDITION
        or STABLE_ENTRIES is not v23.STABLE_ENTRIES
        or STABLE_SPECS is not v23.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV24Error("Alpha-v24 changed its immutable Stable edition")
    if FRONTIER_V24_EXPECTED_COUNT and (
        len(_FRONTIER_ENTRIES) != FRONTIER_V24_EXPECTED_COUNT
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V24_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V24_EXPECTED_EDGE_COUNT
        or Counter(_ENROLLMENT.campaign_by_name.values()) != EXPECTED_CAMPAIGN_COUNTS
    ):
        raise EditionV24Error("Alpha-v24 changed its exact additive constructive frontier")
    if len(ALPHA_CHECKED_SPECS) != len(ALPHA_ENTRIES):
        raise EditionV24Error("Alpha-v24 contains an unchecked theorem")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: len(ALPHA_ENTRIES) - 432,
    }:
        raise EditionV24Error("Alpha-v24 changed its checked evidence partition")
    if EXPECTED_ALPHA_V24_COUNT and (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V24_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V24_FRONTIER_COUNT
        or ALPHA_EDITION.edge_count != EXPECTED_ALPHA_V24_EDGE_COUNT
        or ALPHA_EDITION.layer_count != EXPECTED_ALPHA_V24_LAYER_COUNT
        or ALPHA_V24_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V24_ENROLLMENT_SHA256
        or ALPHA_V24_IDENTITY_SHA256 != EXPECTED_ALPHA_V24_IDENTITY_SHA256
    ):
        raise EditionV24Error("Alpha-v24 immutable theorem, evidence, or graph seal changed")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if not set(item.spec.dependencies) <= available:
            raise EditionV24Error(f"unchecked or forward dependency in {item.spec.name!r}")
        available.add(item.spec.name)


_validate_seals()
_bundle_source: Path | None = None


def _default_research_layer_bundle_source() -> Path:
    pyodide = Path(PYODIDE_RESEARCH_LAYER_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / RESEARCH_LAYER_ARTIFACT_FILENAME
    )


def set_research_layer_bundle_source(source: str | Path | None) -> None:
    global _bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV24ReplayError("research proof source must be a filesystem path")
    _bundle_source = None if source is None else Path(source)
    _checked_research_layer_bundle.cache_clear()
    replay.cache_clear()


def _research_layer_module() -> ModuleType:
    try:
        return import_module(".campaign_research_layer_closure", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as error:
        raise EditionV24ReplayError("actual Alpha-v24 proof provider is unavailable") from error


@lru_cache(maxsize=1)
def _checked_research_layer_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    module = _research_layer_module()
    source = _bundle_source or _default_research_layer_bundle_source()
    try:
        payload = source.read_bytes()
        expected_size = getattr(module, "EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES")
        expected_digest = getattr(module, "EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256")
        expected_nodes = getattr(module, "EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError) as error:
        raise EditionV24ReplayError("actual Alpha-v24 proof bytes are unavailable") from error
    if (
        expected_size <= 0
        or len(expected_digest) != 64
        or len(payload) != expected_size
        or sha256(payload).hexdigest() != expected_digest
    ):
        raise EditionV24ReplayError("Alpha-v24 proof differs from its frozen provenance")
    try:
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        result = module.check_research_layer_proof_bundle(bundle, target)
        plan = module.research_layer_plan()
        receipt = result.receipt
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EditionV24ReplayError(
            "the unchanged intuitionistic kernel rejected the actual Alpha-v24 proof"
        ) from error
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        not _FRONTIER_NEW_NAME_SET <= positions.keys()
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_nodes
    ):
        raise EditionV24ReplayError("Alpha-v24 changed its graph or skipped a kernel check")
    for name, position in positions.items():
        item = ALPHA_EDITION.by_name.get(name)
        node = bundle.nodes[position]
        if (
            item is None
            or type(node) is not BundleNode
            or node.target != _closed_formula(item.spec.statement)
            or node.dependencies
            != tuple(positions[dependency] for dependency in item.spec.dependencies)
        ):
            raise EditionV24ReplayError(f"Alpha-v24 proof changed exact theorem {name!r}")
    return bundle, receipt, positions


def checked_research_layer_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    return _checked_research_layer_bundle()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV24Error(f"unknown theorem-library v24 edition {value!r}")


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
    normalized = name.strip()
    return selected.by_name.get(normalized) or next(
        (
            candidate
            for candidate in selected.entries
            if candidate.spec.name.casefold() == normalized.casefold()
        ),
        None,
    )


def _replay_research_layer_theorem(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt, positions = _checked_research_layer_bundle()
    root = positions[item.spec.name]
    included: set[int] = set()
    pending = [root]
    while pending:
        position = pending.pop()
        if position not in included:
            included.add(position)
            pending.extend(bundle.nodes[position].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
            for node in bundle.nodes
            if node.node_id in included
        ),
        root,
    )
    formula = _closed_formula(item.spec.statement)
    interned = intern_layered_replay_bodies(
        layered,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if interned is None:
        raise EditionV24ReplayError(f"Alpha-v24 theorem {item.spec.name!r} exceeds sharing limits")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id
            or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV24ReplayError("conservative proof interning changed a theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV24ReplayError("the kernel rejected an interned research-layer body")
    candidate = compile_layered_replay(
        interned,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise EditionV24ReplayError(
            f"the unchanged kernel/resource policy rejected actual proof {item.spec.name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


@lru_cache(maxsize=None)
def replay(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    selected = _coerce_edition(edition)
    item = entry(name, edition=selected)
    if item is None:
        raise EditionV24ReplayError(f"unknown {selected.value} v24 theorem {name!r}")
    if not item.checked_use:
        raise EditionV24ReplayError(f"Alpha-v24 theorem {item.spec.name!r} is not checked")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_research_layer_theorem(item)
    return v23.replay(item.spec.name, edition=selected)


__all__ = (
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V24_ENROLLMENT_SHA256",
    "ALPHA_V24_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V24_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V24_COUNT",
    "EXPECTED_ALPHA_V24_EDGE_COUNT",
    "EXPECTED_ALPHA_V24_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V24_FRONTIER_COUNT",
    "EXPECTED_ALPHA_V24_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V24_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV24Error",
    "EditionV24ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "FRONTIER_NEW_NAMES",
    "LibraryEdition",
    "Membership",
    "PYODIDE_RESEARCH_LAYER_BUNDLE_PATH",
    "RESEARCH_LAYER_ARTIFACT_FILENAME",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_research_layer_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_research_layer_bundle_source",
)
