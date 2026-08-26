"""Immutable Alpha v20: the next independently closed constructive layer.

The complete 1,737-row Alpha-v19 release and the 432-row Stable release are
preserved exactly. Thirty-nine new polynomial, finite-matrix, prime-window,
prime-chain, and continued-fraction propositions obtain checked-use authority
only from one complete ordinary, self-contained intuitionistic proof bundle.

Import validates only the exact sealed statement inventory; it intentionally
does not import a proof provider or grant theorem authority. Actual replay
loads immutable proof bytes, checks every bundle node with the unchanged
kernel, and checks the selected independently compiled empty-context proof.
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
from . import editions_v19 as v19
from .alpha_enrollment_v20 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V20_EXPECTED_COUNT,
    FRONTIER_V20_EXPECTED_EDGE_COUNT,
    FRONTIER_V20_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V19_COUNT,
    PARENT_ALPHA_V19_ENROLLMENT_SHA256,
    PARENT_ALPHA_V19_IDENTITY_SHA256,
    alpha_v20_enrollment,
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


EditionName = v19.EditionName
Membership = v19.Membership
EvidenceStatus = v19.EvidenceStatus
EnrollmentOrigin = v19.EnrollmentOrigin
EditionEntry = v19.EditionEntry
LibraryEdition = v19.LibraryEdition

EXPECTED_ALPHA_V20_COUNT = 1_776
EXPECTED_ALPHA_V20_CHECKED_USE_COUNT = 1_776
EXPECTED_ALPHA_V20_FRONTIER_COUNT = 39
EXPECTED_ALPHA_V20_EDGE_COUNT = 5_882
EXPECTED_ALPHA_V20_LAYER_COUNT = 53
EXPECTED_ALPHA_V20_ENROLLMENT_SHA256 = (
    "947e12db1db93decddd87b833067acf774a37fcb7d89de117010d53baf00065c"
)
EXPECTED_ALPHA_V20_IDENTITY_SHA256 = (
    "ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b"
)
NEXT_LAYER_ARTIFACT_FILENAME = "alpha-v20-next-layer-proof-bundle-v1.json"
PYODIDE_NEXT_LAYER_BUNDLE_PATH = f"/lab/proof-artifacts/{NEXT_LAYER_ARTIFACT_FILENAME}"


class EditionV20Error(ValueError):
    """The immutable parent, exact next frontier, or release seal failed."""


class EditionV20ReplayError(EditionV20Error):
    """Checked use requires actual unchanged-kernel-accepted proof data."""


def dependency_depths(specs):
    return v19.dependency_depths(specs)


def dependency_layers(specs):
    return v19.dependency_layers(specs)


_ENROLLMENT = alpha_v20_enrollment()
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

ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v19.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v19.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v19.STABLE_ENTRIES
STABLE_SPECS = v19.STABLE_SPECS
STABLE_EDITION = v19.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V20_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V20_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V20_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(v19.ALPHA_ENTRIES) != PARENT_ALPHA_V19_COUNT
        or tuple(ALPHA_ENTRIES[:PARENT_ALPHA_V19_COUNT]) != v19.ALPHA_ENTRIES
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v19.ALPHA_ENTRIES))
        or _enrollment_identity(v19.ALPHA_ENTRIES) != PARENT_ALPHA_V19_ENROLLMENT_SHA256
        or _identity(EditionName.ALPHA, v19.ALPHA_ENTRIES)
        != PARENT_ALPHA_V19_IDENTITY_SHA256
    ):
        raise EditionV20Error("Alpha-v20 changed its immutable fully checked v19 parent")
    if (
        STABLE_EDITION is not v19.STABLE_EDITION
        or STABLE_ENTRIES is not v19.STABLE_ENTRIES
        or STABLE_SPECS is not v19.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV20Error("Alpha-v20 changed the immutable Stable edition")
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V20_COUNT
        or len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V20_FRONTIER_COUNT
        or len(_FRONTIER_ENTRIES) != FRONTIER_V20_EXPECTED_COUNT
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V20_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V20_EXPECTED_EDGE_COUNT
    ):
        raise EditionV20Error("Alpha-v20 changed its exact additive constructive frontier")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V20_EDGE_COUNT,
        EXPECTED_ALPHA_V20_LAYER_COUNT,
    ):
        raise EditionV20Error("Alpha-v20 changed its constructive dependency topology")
    if (
        ALPHA_V20_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V20_ENROLLMENT_SHA256
        or ALPHA_V20_IDENTITY_SHA256 != EXPECTED_ALPHA_V20_IDENTITY_SHA256
    ):
        raise EditionV20Error("Alpha-v20 immutable statement or evidence identity changed")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 1_344,
    }:
        raise EditionV20Error("Alpha-v20 exact independently checked evidence partition changed")
    if len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V20_CHECKED_USE_COUNT:
        raise EditionV20Error("Alpha-v20 lost independently checked theorem authority")
    actual_campaign_counts = Counter(_ENROLLMENT.campaign_by_name.values())
    if actual_campaign_counts != EXPECTED_CAMPAIGN_COUNTS:
        raise EditionV20Error("Alpha-v20 changed an exact constructive campaign count")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if not set(item.spec.dependencies) <= available:
            raise EditionV20Error(f"unchecked or forward dependency in {item.spec.name!r}")
        available.add(item.spec.name)


_validate_seals()
_bundle_source: Path | None = None


def _default_next_layer_bundle_source() -> Path:
    pyodide = Path(PYODIDE_NEXT_LAYER_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / NEXT_LAYER_ARTIFACT_FILENAME
    )


def set_next_layer_bundle_source(source: str | Path | None) -> None:
    """Replace actual proof bytes for fail-closed tests and reset replay caches."""

    global _bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV20ReplayError("next-layer proof source must be a filesystem path")
    _bundle_source = None if source is None else Path(source)
    _checked_next_layer_bundle.cache_clear()
    replay.cache_clear()


def _next_layer_module() -> ModuleType:
    try:
        return import_module(".campaign_next_layer_closure", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as error:
        raise EditionV20ReplayError(
            "actual Alpha-v20 self-contained proof provider is unavailable"
        ) from error


@lru_cache(maxsize=1)
def _checked_next_layer_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    module = _next_layer_module()
    source = _bundle_source or _default_next_layer_bundle_source()
    try:
        payload = source.read_bytes()
        expected_size = getattr(module, "EXPECTED_NEXT_LAYER_BUNDLE_BYTES")
        expected_digest = getattr(module, "EXPECTED_NEXT_LAYER_BUNDLE_SHA256")
        expected_nodes = getattr(module, "EXPECTED_NEXT_LAYER_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError) as error:
        raise EditionV20ReplayError(
            "actual Alpha-v20 proof bytes or frozen exact provenance are unavailable"
        ) from error
    if len(payload) != expected_size or sha256(payload).hexdigest() != expected_digest:
        raise EditionV20ReplayError(
            "Alpha-v20 proof artifact differs from its frozen genuine provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        result = module.check_next_layer_proof_bundle(bundle, target)
        plan = module.next_layer_closure_plan()
        receipt = result.receipt
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EditionV20ReplayError(
            "unchanged intuitionistic kernel rejected the actual Alpha-v20 proof"
        ) from error
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        not _FRONTIER_NEW_NAME_SET <= positions.keys()
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_nodes
    ):
        raise EditionV20ReplayError("Alpha-v20 graph changed or skipped a kernel check")
    for name, position in positions.items():
        entry = ALPHA_EDITION.by_name.get(name)
        node = bundle.nodes[position]
        if (
            entry is None
            or type(node) is not BundleNode
            or node.target != _closed_formula(entry.spec.statement)
            or node.dependencies != tuple(positions[dependency] for dependency in entry.spec.dependencies)
        ):
            raise EditionV20ReplayError(f"Alpha-v20 proof changed exact theorem {name!r}")
    return bundle, receipt, positions


def checked_next_layer_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    """Return independently kernel-checked actual ordinary proof data."""

    return _checked_next_layer_bundle()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV20Error(f"unknown theorem-library v20 edition {value!r}")


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


def _replay_next_layer_theorem(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt, positions = _checked_next_layer_bundle()
    root = positions[item.spec.name]
    included: set[int] = set()
    pending = [root]
    while pending:
        current = pending.pop()
        if current not in included:
            included.add(current)
            pending.extend(bundle.nodes[current].dependencies)
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
        raise EditionV20ReplayError(
            f"Alpha-v20 theorem {item.spec.name!r} exceeds unchanged sharing limits"
        )
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id
            or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV20ReplayError("conservative proof interning changed a theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV20ReplayError(
                "unchanged intuitionistic kernel rejected an interned next-layer body"
            )
    candidate = compile_layered_replay(
        interned,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise EditionV20ReplayError(
            f"unchanged kernel/resource policy rejected actual Alpha-v20 proof "
            f"{item.spec.name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


@lru_cache(maxsize=None)
def replay(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    """Expose theorem use only after an exact empty-context kernel check."""

    selected = _coerce_edition(edition)
    item = entry(name, edition=selected)
    if item is None:
        raise EditionV20ReplayError(f"unknown {selected.value} v20 theorem {name!r}")
    if not item.checked_use:
        raise EditionV20ReplayError(f"Alpha-v20 theorem {item.spec.name!r} is not checked")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_next_layer_theorem(item)
    return v19.replay(item.spec.name, edition=selected)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V20_ENROLLMENT_SHA256",
    "ALPHA_V20_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V20_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V20_COUNT",
    "EXPECTED_ALPHA_V20_EDGE_COUNT",
    "EXPECTED_ALPHA_V20_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V20_FRONTIER_COUNT",
    "EXPECTED_ALPHA_V20_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V20_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV20Error",
    "EditionV20ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "FRONTIER_NEW_NAMES",
    "LibraryEdition",
    "Membership",
    "NEXT_LAYER_ARTIFACT_FILENAME",
    "PYODIDE_NEXT_LAYER_BUNDLE_PATH",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_next_layer_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_next_layer_bundle_source",
]
