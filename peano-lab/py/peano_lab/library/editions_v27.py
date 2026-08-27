"""Fail-closed completion of second-wave mathematical campaigns over the immutable Alpha-v26 release.

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
from . import editions_v26 as v26
from .alpha_enrollment_v27 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V27_EXPECTED_COUNT,
    FRONTIER_V27_EXPECTED_EDGE_COUNT,
    FRONTIER_V27_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V26_COUNT,
    PARENT_ALPHA_V26_ENROLLMENT_SHA256,
    PARENT_ALPHA_V26_IDENTITY_SHA256,
    alpha_v27_enrollment,
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


EditionName = v26.EditionName
Membership = v26.Membership
EvidenceStatus = v26.EvidenceStatus
EnrollmentOrigin = v26.EnrollmentOrigin
EditionEntry = v26.EditionEntry
LibraryEdition = v26.LibraryEdition

# Frozen after every exact dependency-closed body passed both verifiers.
EXPECTED_ALPHA_V27_COUNT = 2_560
EXPECTED_ALPHA_V27_CHECKED_USE_COUNT = 2_560
EXPECTED_ALPHA_V27_FRONTIER_COUNT = 422
EXPECTED_ALPHA_V27_EDGE_COUNT = 8_196
EXPECTED_ALPHA_V27_LAYER_COUNT = 53
EXPECTED_ALPHA_V27_ENROLLMENT_SHA256 = "20866c3865baec2bc6cee3c8e54bcb2f55e95a7b1a7fc85c103e3c9b055ecf4e"
EXPECTED_ALPHA_V27_IDENTITY_SHA256 = "5c5935ed524b63827068cba37da222fc78b458de6c5af2e07cf572bb9fab7d05"
SECOND_WAVE_ARTIFACT_FILENAME = "alpha-v27-second-wave-proof-bundle-v1.json"
PYODIDE_SECOND_WAVE_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{SECOND_WAVE_ARTIFACT_FILENAME}"
)


class EditionV27Error(ValueError):
    """The immutable parent, additive theorem inventory, or seal changed."""


class EditionV27ReplayError(EditionV27Error):
    """Checked use requires complete unchanged-kernel-accepted proof bytes."""


def dependency_depths(specs):
    return v26.dependency_depths(specs)


def dependency_layers(specs):
    return v26.dependency_layers(specs)


_ENROLLMENT = alpha_v27_enrollment()
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
ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v26.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v26.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v26.STABLE_ENTRIES
STABLE_SPECS = v26.STABLE_SPECS
STABLE_EDITION = v26.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V27_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V27_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V27_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(v26.ALPHA_ENTRIES) != PARENT_ALPHA_V26_COUNT
        or tuple(ALPHA_ENTRIES[:PARENT_ALPHA_V26_COUNT]) != v26.ALPHA_ENTRIES
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v26.ALPHA_ENTRIES))
        or _enrollment_identity(v26.ALPHA_ENTRIES) != PARENT_ALPHA_V26_ENROLLMENT_SHA256
        or _identity(EditionName.ALPHA, v26.ALPHA_ENTRIES)
        != PARENT_ALPHA_V26_IDENTITY_SHA256
    ):
        raise EditionV27Error("Alpha-v27 changed its immutable checked Alpha-v26 parent")
    if (
        STABLE_EDITION is not v26.STABLE_EDITION
        or STABLE_ENTRIES is not v26.STABLE_ENTRIES
        or STABLE_SPECS is not v26.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV27Error("Alpha-v27 changed its immutable Stable edition")
    if FRONTIER_V27_EXPECTED_COUNT and (
        len(_FRONTIER_ENTRIES) != FRONTIER_V27_EXPECTED_COUNT
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V27_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V27_EXPECTED_EDGE_COUNT
        or Counter(_ENROLLMENT.campaign_by_name.values()) != EXPECTED_CAMPAIGN_COUNTS
    ):
        raise EditionV27Error("Alpha-v27 changed its exact additive constructive frontier")
    if len(ALPHA_CHECKED_SPECS) != len(ALPHA_ENTRIES):
        raise EditionV27Error("Alpha-v27 contains an unchecked theorem")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: len(ALPHA_ENTRIES) - 432,
    }:
        raise EditionV27Error("Alpha-v27 changed its checked evidence partition")
    if EXPECTED_ALPHA_V27_COUNT and (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V27_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V27_CHECKED_USE_COUNT
        or len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V27_FRONTIER_COUNT
        or ALPHA_EDITION.edge_count != EXPECTED_ALPHA_V27_EDGE_COUNT
        or ALPHA_EDITION.layer_count != EXPECTED_ALPHA_V27_LAYER_COUNT
        or ALPHA_V27_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V27_ENROLLMENT_SHA256
        or ALPHA_V27_IDENTITY_SHA256 != EXPECTED_ALPHA_V27_IDENTITY_SHA256
    ):
        raise EditionV27Error("Alpha-v27 immutable theorem, evidence, or graph seal changed")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if not set(item.spec.dependencies) <= available:
            raise EditionV27Error(f"unchecked or forward dependency in {item.spec.name!r}")
        available.add(item.spec.name)


_validate_seals()
_bundle_source: Path | None = None


def _default_second_wave_bundle_source() -> Path:
    pyodide = Path(PYODIDE_SECOND_WAVE_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    parents = Path(__file__).resolve().parents
    if len(parents) <= 4:
        # A compact browser installation need not have a repository layout.
        # Missing bytes must fail closed through the ordinary read error.
        return pyodide
    return (
        parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / SECOND_WAVE_ARTIFACT_FILENAME
    )


def set_second_wave_bundle_source(source: str | Path | None) -> None:
    global _bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV27ReplayError("second-wave proof source must be a filesystem path")
    _bundle_source = None if source is None else Path(source)
    _checked_second_wave_bundle.cache_clear()
    replay.cache_clear()


def _second_wave_module() -> ModuleType:
    try:
        return import_module(".campaign_second_wave_closure", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as error:
        raise EditionV27ReplayError("actual Alpha-v27 proof provider is unavailable") from error


@lru_cache(maxsize=1)
def _checked_second_wave_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    if (
        EXPECTED_ALPHA_V27_COUNT <= PARENT_ALPHA_V26_COUNT
        or FRONTIER_V27_EXPECTED_COUNT <= 0
        or len(EXPECTED_ALPHA_V27_ENROLLMENT_SHA256) != 64
        or len(EXPECTED_ALPHA_V27_IDENTITY_SHA256) != 64
        or len(FRONTIER_V27_EXPECTED_NAMES_SHA256) != 64
    ):
        raise EditionV27ReplayError("Alpha-v27 is not sealed for checked use")
    module = _second_wave_module()
    source = _bundle_source or _default_second_wave_bundle_source()
    try:
        payload = source.read_bytes()
        expected_size = getattr(module, "EXPECTED_SECOND_WAVE_BUNDLE_BYTES")
        expected_digest = getattr(module, "EXPECTED_SECOND_WAVE_BUNDLE_SHA256")
        expected_nodes = getattr(module, "EXPECTED_SECOND_WAVE_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError) as error:
        raise EditionV27ReplayError("actual Alpha-v27 proof bytes are unavailable") from error
    if (
        expected_size <= 0
        or len(expected_digest) != 64
        or len(payload) != expected_size
        or sha256(payload).hexdigest() != expected_digest
    ):
        raise EditionV27ReplayError("Alpha-v27 proof differs from its frozen provenance")
    try:
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        receipt = module.check_second_wave_proof_bundle(
            bundle, target, parent_specs=v26.ALPHA_CHECKED_SPECS
        )
        plan = module.second_wave_plan(parent_specs=v26.ALPHA_CHECKED_SPECS)
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EditionV27ReplayError(
            "the unchanged intuitionistic kernel rejected the actual Alpha-v27 proof"
        ) from error
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        not _FRONTIER_NEW_NAME_SET <= positions.keys()
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_nodes
    ):
        raise EditionV27ReplayError("Alpha-v27 changed its graph or skipped a kernel check")
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
            raise EditionV27ReplayError(f"Alpha-v27 proof changed exact theorem {name!r}")
    return bundle, receipt, positions


def checked_second_wave_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    return _checked_second_wave_bundle()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV27Error(f"unknown theorem-library v27 edition {value!r}")


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


def _replay_second_wave_theorem(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt, positions = _checked_second_wave_bundle()
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
        raise EditionV27ReplayError(f"Alpha-v27 theorem {item.spec.name!r} exceeds sharing limits")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id
            or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV27ReplayError("conservative proof interning changed a theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV27ReplayError("the kernel rejected an interned second-wave body")
    candidate = compile_layered_replay(
        interned,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise EditionV27ReplayError(
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
        raise EditionV27ReplayError(f"unknown {selected.value} v27 theorem {name!r}")
    if not item.checked_use:
        raise EditionV27ReplayError(f"Alpha-v27 theorem {item.spec.name!r} is not checked")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_second_wave_theorem(item)
    return v26.replay(item.spec.name, edition=selected)


__all__ = (
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V27_ENROLLMENT_SHA256",
    "ALPHA_V27_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V27_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V27_COUNT",
    "EXPECTED_ALPHA_V27_EDGE_COUNT",
    "EXPECTED_ALPHA_V27_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V27_FRONTIER_COUNT",
    "EXPECTED_ALPHA_V27_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V27_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV27Error",
    "EditionV27ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "FRONTIER_NEW_NAMES",
    "LibraryEdition",
    "Membership",
    "PYODIDE_SECOND_WAVE_BUNDLE_PATH",
    "SECOND_WAVE_ARTIFACT_FILENAME",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_second_wave_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_second_wave_bundle_source",
)
