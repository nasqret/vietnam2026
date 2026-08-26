"""Immutable Alpha v21: the next dependency-closed constructive frontier.

The complete, independently checked 1,776-row Alpha-v20 release and the
432-row Stable release remain exact immutable parents. Inventory import never
loads a proof provider. Every newly admitted theorem becomes usable only by
loading its frozen self-contained ordinary proof bundle, checking every body
with the unchanged intuitionistic kernel, and independently checking the final
empty-context certificate under the existing conservative resource policy.
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
from . import editions_v20 as v20
from .alpha_enrollment_v21 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V21_EXPECTED_COUNT,
    FRONTIER_V21_EXPECTED_EDGE_COUNT,
    FRONTIER_V21_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V20_COUNT,
    PARENT_ALPHA_V20_ENROLLMENT_SHA256,
    PARENT_ALPHA_V20_IDENTITY_SHA256,
    alpha_v21_enrollment,
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


EditionName = v20.EditionName
Membership = v20.Membership
EvidenceStatus = v20.EvidenceStatus
EnrollmentOrigin = v20.EnrollmentOrigin
EditionEntry = v20.EditionEntry
LibraryEdition = v20.LibraryEdition
v19 = v20.v19

# Frozen only after the exact original-kernel-checked candidate inventories
# and independently checked additive release have been assembled.
EXPECTED_ALPHA_V21_COUNT = 1_830
EXPECTED_ALPHA_V21_CHECKED_USE_COUNT = 1_830
EXPECTED_ALPHA_V21_FRONTIER_COUNT = 54
EXPECTED_ALPHA_V21_EDGE_COUNT = 5_986
EXPECTED_ALPHA_V21_LAYER_COUNT = 53
EXPECTED_ALPHA_V21_ENROLLMENT_SHA256 = (
    "ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98"
)
EXPECTED_ALPHA_V21_IDENTITY_SHA256 = (
    "aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6"
)
ADVANCED_LAYER_ARTIFACT_FILENAME = "alpha-v21-advanced-layer-proof-bundle-v1.json"
PYODIDE_ADVANCED_LAYER_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{ADVANCED_LAYER_ARTIFACT_FILENAME}"
)


class EditionV21Error(ValueError):
    """The immutable parent, exact new frontier, or final seal changed."""


class EditionV21ReplayError(EditionV21Error):
    """Actual checked use needs complete original-kernel-accepted proofs."""


def dependency_depths(specs):
    return v20.dependency_depths(specs)


def dependency_layers(specs):
    return v20.dependency_layers(specs)


_ENROLLMENT = alpha_v21_enrollment()
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

ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v20.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v20.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v20.STABLE_ENTRIES
STABLE_SPECS = v20.STABLE_SPECS
STABLE_EDITION = v20.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V21_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V21_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V21_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(v20.ALPHA_ENTRIES) != PARENT_ALPHA_V20_COUNT
        or tuple(ALPHA_ENTRIES[:PARENT_ALPHA_V20_COUNT]) != v20.ALPHA_ENTRIES
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v20.ALPHA_ENTRIES))
        or _enrollment_identity(v20.ALPHA_ENTRIES) != PARENT_ALPHA_V20_ENROLLMENT_SHA256
        or _identity(EditionName.ALPHA, v20.ALPHA_ENTRIES)
        != PARENT_ALPHA_V20_IDENTITY_SHA256
    ):
        raise EditionV21Error("Alpha-v21 changed its immutable fully checked v20 parent")
    if (
        STABLE_EDITION is not v20.STABLE_EDITION
        or STABLE_ENTRIES is not v20.STABLE_ENTRIES
        or STABLE_SPECS is not v20.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV21Error("Alpha-v21 changed the immutable Stable edition")
    if (
        len(_FRONTIER_ENTRIES) != FRONTIER_V21_EXPECTED_COUNT
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V21_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V21_EXPECTED_EDGE_COUNT
    ):
        raise EditionV21Error("Alpha-v21 changed its exact constructive frontier")
    if Counter(_ENROLLMENT.campaign_by_name.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise EditionV21Error("Alpha-v21 changed an exact constructive campaign count")
    if len(ALPHA_CHECKED_SPECS) != len(ALPHA_ENTRIES):
        raise EditionV21Error("Alpha-v21 has an unchecked theorem")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: len(ALPHA_ENTRIES) - 432,
    }:
        raise EditionV21Error("Alpha-v21 changed its checked evidence partition")
    if EXPECTED_ALPHA_V21_COUNT and (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V21_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V21_CHECKED_USE_COUNT
        or len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V21_FRONTIER_COUNT
        or ALPHA_EDITION.edge_count != EXPECTED_ALPHA_V21_EDGE_COUNT
        or ALPHA_EDITION.layer_count != EXPECTED_ALPHA_V21_LAYER_COUNT
        or ALPHA_V21_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V21_ENROLLMENT_SHA256
        or ALPHA_V21_IDENTITY_SHA256 != EXPECTED_ALPHA_V21_IDENTITY_SHA256
    ):
        raise EditionV21Error("Alpha-v21 immutable statement, evidence, or graph seal changed")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if not set(item.spec.dependencies) <= available:
            raise EditionV21Error(f"unchecked or forward dependency in {item.spec.name!r}")
        available.add(item.spec.name)


_validate_seals()
_bundle_source: Path | None = None


def _default_advanced_layer_bundle_source() -> Path:
    pyodide = Path(PYODIDE_ADVANCED_LAYER_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / ADVANCED_LAYER_ARTIFACT_FILENAME
    )


def set_advanced_layer_bundle_source(source: str | Path | None) -> None:
    global _bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV21ReplayError("advanced-layer proof source must be a filesystem path")
    _bundle_source = None if source is None else Path(source)
    _checked_advanced_layer_bundle.cache_clear()
    replay.cache_clear()


def _advanced_layer_module() -> ModuleType:
    try:
        return import_module(".campaign_advanced_layer_closure", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as error:
        raise EditionV21ReplayError("actual Alpha-v21 proof provider is unavailable") from error


@lru_cache(maxsize=1)
def _checked_advanced_layer_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    module = _advanced_layer_module()
    source = _bundle_source or _default_advanced_layer_bundle_source()
    try:
        payload = source.read_bytes()
        expected_size = getattr(module, "EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES")
        expected_digest = getattr(module, "EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256")
        expected_nodes = getattr(module, "EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError) as error:
        raise EditionV21ReplayError("actual Alpha-v21 proof bytes are unavailable") from error
    if (
        expected_size <= 0
        or len(expected_digest) != 64
        or len(payload) != expected_size
        or sha256(payload).hexdigest() != expected_digest
    ):
        raise EditionV21ReplayError("Alpha-v21 proof differs from its frozen genuine provenance")
    try:
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        result = module.check_advanced_layer_proof_bundle(bundle, target)
        plan = module.advanced_layer_closure_plan()
        receipt = result.receipt
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EditionV21ReplayError(
            "the unchanged intuitionistic kernel rejected the actual Alpha-v21 proof"
        ) from error
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        not _FRONTIER_NEW_NAME_SET <= positions.keys()
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_nodes
    ):
        raise EditionV21ReplayError("Alpha-v21 changed its graph or skipped a kernel check")
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
            raise EditionV21ReplayError(f"Alpha-v21 proof changed exact theorem {name!r}")
    return bundle, receipt, positions


def checked_advanced_layer_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    return _checked_advanced_layer_bundle()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV21Error(f"unknown theorem-library v21 edition {value!r}")


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


def _replay_advanced_layer_theorem(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt, positions = _checked_advanced_layer_bundle()
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
        raise EditionV21ReplayError(f"Alpha-v21 theorem {item.spec.name!r} exceeds sharing limits")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id
            or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV21ReplayError("conservative proof interning changed a theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV21ReplayError("the kernel rejected an interned advanced-layer body")
    candidate = compile_layered_replay(
        interned,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise EditionV21ReplayError(
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
        raise EditionV21ReplayError(f"unknown {selected.value} v21 theorem {name!r}")
    if not item.checked_use:
        raise EditionV21ReplayError(f"Alpha-v21 theorem {item.spec.name!r} is not checked")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_advanced_layer_theorem(item)
    return v20.replay(item.spec.name, edition=selected)


__all__ = [
    "ADVANCED_LAYER_ARTIFACT_FILENAME",
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V21_ENROLLMENT_SHA256",
    "ALPHA_V21_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V21_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V21_COUNT",
    "EXPECTED_ALPHA_V21_EDGE_COUNT",
    "EXPECTED_ALPHA_V21_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V21_FRONTIER_COUNT",
    "EXPECTED_ALPHA_V21_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V21_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV21Error",
    "EditionV21ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "FRONTIER_NEW_NAMES",
    "LibraryEdition",
    "Membership",
    "PYODIDE_ADVANCED_LAYER_BUNDLE_PATH",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_advanced_layer_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_advanced_layer_bundle_source",
]
