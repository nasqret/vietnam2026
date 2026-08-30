"""Alpha v19: complete legacy closure plus new constructive number theory.

All 1,673 immutable Alpha-v18 statements become independently checked: the
remaining 84 body-only rows receive checked-use authority solely from their
self-contained original-kernel-checked residual proof bundle. Exactly 64 new
constructive Pythagorean, prime two-square, linear-congruence, and prime
progression theorems are appended and independently checked by a second exact
proof bundle. Stable and every historical edition remain unchanged.

Import seals inventory only and never imports either actual proof provider.
Checked theorem use remains fail-closed until the exact frozen artifact bytes,
every dependency-curried proof body, and an ordinary empty-context root proof
have all been accepted by the unchanged intuitionistic kernel.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import ModuleType

from ..kernel.checker import check
from ..kernel.formulas import Imp
from . import editions_v18 as v18
from .alpha_enrollment_v19 import (
    FRONTIER_V19_EXPECTED_COUNT,
    FRONTIER_V19_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V18_COUNT,
    PARENT_ALPHA_V18_ENROLLMENT_SHA256,
    PARENT_ALPHA_V18_IDENTITY_SHA256,
    alpha_v19_enrollment,
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


EditionName = v18.EditionName
Membership = v18.Membership
EvidenceStatus = v18.EvidenceStatus
EnrollmentOrigin = v18.EnrollmentOrigin
EditionEntry = v18.EditionEntry
LibraryEdition = v18.LibraryEdition

EXPECTED_ALPHA_V19_COUNT = 1_737
EXPECTED_ALPHA_V19_EDGE_COUNT = 5_779
EXPECTED_ALPHA_V19_LAYER_COUNT = 53
EXPECTED_ALPHA_V19_CHECKED_USE_COUNT = 1_737
EXPECTED_ALPHA_V19_RESIDUAL_PROMOTION_COUNT = 84
EXPECTED_ALPHA_V19_FRONTIER_COUNT = 64
EXPECTED_ALPHA_V19_RESIDUAL_PROMOTION_NAMES_SHA256 = (
    "0fd3159925c12b2e7249edb5d536f3be600e466e5a6695350a22c38e81d4f69e"
)
EXPECTED_ALPHA_V19_ENROLLMENT_SHA256 = (
    "1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795"
)
EXPECTED_ALPHA_V19_IDENTITY_SHA256 = (
    "905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7"
)

CAMPAIGN_BUNDLE_LABELS = ("residual", "frontier")
CAMPAIGN_ARTIFACT_FILENAMES = {
    "residual": "alpha-v19-residual-proof-bundle-v1.json",
    "frontier": "alpha-v19-campaign-frontier-proof-bundle-v1.json",
}
PYODIDE_CAMPAIGN_BUNDLE_PATHS = {
    label: f"/lab/proof-artifacts/{filename}"
    for label, filename in CAMPAIGN_ARTIFACT_FILENAMES.items()
}


class EditionV19Error(ValueError):
    """The immutable parent, exact campaign frontier, or release seal failed."""


class EditionV19ReplayError(EditionV19Error):
    """Checked use requires actual unchanged-kernel-accepted proof data."""


def dependency_depths(specs):
    return v18.dependency_depths(specs)


def dependency_layers(specs):
    return v18.dependency_layers(specs)


RESIDUAL_PROMOTED_NAMES = tuple(
    entry.spec.name for entry in v18.ALPHA_ENTRIES if not entry.checked_use
)
_RESIDUAL_PROMOTED_NAME_SET = frozenset(RESIDUAL_PROMOTED_NAMES)
_ENROLLMENT = alpha_v19_enrollment()
FRONTIER_NEW_NAMES = tuple(spec.name for spec in _ENROLLMENT.frontier_specs)
_FRONTIER_NEW_NAME_SET = frozenset(FRONTIER_NEW_NAMES)

_PARENT_PREFIX = tuple(
    replace(item, evidence=EvidenceStatus.ALPHA_CLOSED)
    if item.spec.name in _RESIDUAL_PROMOTED_NAME_SET
    else item
    for item in v18.ALPHA_ENTRIES
)
_FRONTIER_ENTRIES = tuple(
    EditionEntry(
        spec=spec,
        membership=Membership.ALPHA_ONLY,
        evidence=EvidenceStatus.ALPHA_CLOSED,
        enrollment_origin=EnrollmentOrigin.HA,
        provenance=(EnrollmentOrigin.HA,),
        source_module=_ENROLLMENT.source_by_name[spec.name],
    )
    for spec in _ENROLLMENT.frontier_specs
)
ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*_PARENT_PREFIX, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v18.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v18.STABLE_ENTRIES
STABLE_SPECS = v18.STABLE_SPECS
STABLE_EDITION = v18.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V19_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V19_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V19_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V19_COUNT
        or len(_PARENT_PREFIX) != PARENT_ALPHA_V18_COUNT
        or len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V19_FRONTIER_COUNT
        or len(_FRONTIER_ENTRIES) != FRONTIER_V19_EXPECTED_COUNT
        or tuple(item.spec for item in _PARENT_PREFIX) != v18.ALPHA_SPECS
    ):
        raise EditionV19Error("Alpha-v19 changed its immutable parent or exact frontier")
    if (
        STABLE_EDITION is not v18.STABLE_EDITION
        or STABLE_ENTRIES is not v18.STABLE_ENTRIES
        or STABLE_SPECS is not v18.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV19Error("Alpha-v19 changed the immutable Stable edition")
    if (
        _enrollment_identity(v18.ALPHA_ENTRIES) != PARENT_ALPHA_V18_ENROLLMENT_SHA256
        or _identity(EditionName.ALPHA, v18.ALPHA_ENTRIES)
        != PARENT_ALPHA_V18_IDENTITY_SHA256
    ):
        raise EditionV19Error("Alpha-v19 changed its sealed Alpha-v18 parent")
    if (
        len(RESIDUAL_PROMOTED_NAMES) != EXPECTED_ALPHA_V19_RESIDUAL_PROMOTION_COUNT
        or sha256("\n".join(RESIDUAL_PROMOTED_NAMES).encode()).hexdigest()
        != EXPECTED_ALPHA_V19_RESIDUAL_PROMOTION_NAMES_SHA256
    ):
        raise EditionV19Error("Alpha-v19 exact residual evidence transition changed")
    if (
        len(FRONTIER_NEW_NAMES) != EXPECTED_ALPHA_V19_FRONTIER_COUNT
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V19_EXPECTED_NAMES_SHA256
    ):
        raise EditionV19Error("Alpha-v19 exact additive campaign order changed")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V19_EDGE_COUNT,
        EXPECTED_ALPHA_V19_LAYER_COUNT,
    ):
        raise EditionV19Error("Alpha-v19 exact constructive dependency topology changed")
    if (
        ALPHA_V19_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V19_ENROLLMENT_SHA256
        or ALPHA_V19_IDENTITY_SHA256 != EXPECTED_ALPHA_V19_IDENTITY_SHA256
    ):
        raise EditionV19Error("Alpha-v19 immutable campaign identities changed")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 1_305,
    }:
        raise EditionV19Error("Alpha-v19 complete checked evidence partition changed")
    if len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V19_CHECKED_USE_COUNT:
        raise EditionV19Error("Alpha-v19 lost independently checked theorem authority")
    for older, newer in zip(v18.ALPHA_ENTRIES, _PARENT_PREFIX, strict=True):
        if older.spec.name in _RESIDUAL_PROMOTED_NAME_SET:
            if (
                older.evidence is not EvidenceStatus.BODY_CHECKED
                or older.membership is not Membership.ALPHA_ONLY
                or newer != replace(older, evidence=EvidenceStatus.ALPHA_CLOSED)
            ):
                raise EditionV19Error(f"invalid residual promotion {older.spec.name!r}")
        elif newer is not older:
            raise EditionV19Error(f"mutated immutable parent theorem {older.spec.name!r}")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if not set(item.spec.dependencies) <= available:
            raise EditionV19Error(
                f"unchecked or forward dependencies in {item.spec.name!r}"
            )
        available.add(item.spec.name)


_validate_seals()

_bundle_sources: dict[str, Path] = {}


def _coerce_campaign_label(label: str) -> str:
    if type(label) is not str or label not in CAMPAIGN_BUNDLE_LABELS:
        raise EditionV19ReplayError(f"unknown Alpha-v19 proof family {label!r}")
    return label


def _default_campaign_bundle_source(label: str) -> Path:
    pyodide = Path(PYODIDE_CAMPAIGN_BUNDLE_PATHS[label])
    if pyodide.is_file():
        return pyodide
    return (
        Path(__file__).resolve().parents[4]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / CAMPAIGN_ARTIFACT_FILENAMES[label]
    )


def set_campaign_bundle_source(label: str, source: str | Path | None) -> None:
    """Replace exact proof bytes for fail-closed tests and clear replay caches."""

    selected = _coerce_campaign_label(label)
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV19ReplayError("campaign proof source must be a filesystem path")
    if source is None:
        _bundle_sources.pop(selected, None)
    else:
        _bundle_sources[selected] = Path(source)
    _checked_campaign_bundle.cache_clear()
    replay.cache_clear()


def _campaign_module(label: str) -> ModuleType:
    name = "campaign_residual_closure" if label == "residual" else "campaign_frontier_closure"
    try:
        return import_module(f".{name}", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as error:
        raise EditionV19ReplayError(
            f"actual Alpha-v19 {label} proof provider is unavailable"
        ) from error


@lru_cache(maxsize=2)
def _checked_campaign_bundle(
    label: str,
) -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    selected = _coerce_campaign_label(label)
    module = _campaign_module(selected)
    prefix = "RESIDUAL" if selected == "residual" else "FRONTIER"
    source = _bundle_sources.get(selected) or _default_campaign_bundle_source(selected)
    try:
        data = source.read_bytes()
        expected_bytes = getattr(module, f"EXPECTED_{prefix}_BUNDLE_BYTES")
        expected_digest = getattr(module, f"EXPECTED_{prefix}_BUNDLE_SHA256")
        expected_nodes = getattr(module, f"EXPECTED_{prefix}_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError) as error:
        raise EditionV19ReplayError(
            f"actual Alpha-v19 {selected} proof bytes or frozen provenance are unavailable"
        ) from error
    if len(data) != expected_bytes or sha256(data).hexdigest() != expected_digest:
        raise EditionV19ReplayError(
            f"Alpha-v19 {selected} proof artifact differs from frozen genuine provenance"
        )
    try:
        bundle, target = decode_proof_bundle(data.decode("utf-8"))
        if selected == "residual":
            result = module.check_residual_proof_bundle(bundle, target)
            plan = module.residual_closure_plan()
            expected = _RESIDUAL_PROMOTED_NAME_SET
        else:
            result = module.check_campaign_frontier_proof_bundle(bundle, target)
            plan = module.campaign_frontier_plan()
            expected = _FRONTIER_NEW_NAME_SET
        receipt = result.receipt
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EditionV19ReplayError(
            f"unchanged intuitionistic kernel rejected actual Alpha-v19 {selected} proof"
        ) from error
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        not expected <= positions.keys()
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_nodes
    ):
        raise EditionV19ReplayError(
            f"Alpha-v19 {selected} actual proof graph changed or skipped a kernel check"
        )
    for name, position in positions.items():
        item = ALPHA_EDITION.by_name.get(name)
        node = bundle.nodes[position]
        if (
            item is None
            or type(node) is not BundleNode
            or node.target != _closed_formula(item.spec.statement)
            or node.dependencies != tuple(positions[dep] for dep in item.spec.dependencies)
        ):
            raise EditionV19ReplayError(
                f"Alpha-v19 {selected} proof changed exact theorem {name!r}"
            )
    return bundle, receipt, positions


def checked_campaign_bundle(
    label: str,
) -> tuple[ProofBundle, CheckedProofBundle, dict[str, int], ModuleType]:
    """Return exact independently checked ordinary proofs and their provider."""

    selected = _coerce_campaign_label(label)
    bundle, receipt, positions = _checked_campaign_bundle(selected)
    return bundle, receipt, positions, _campaign_module(selected)


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV19Error(f"unknown theorem-library v19 edition {value!r}")


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
            candidate
            for candidate in selected.entries
            if candidate.spec.name.casefold() == name.strip().casefold()
        ),
        None,
    )


def _replay_campaign_theorem(item: EditionEntry, label: str) -> CheckedTheorem:
    bundle, _receipt, positions = _checked_campaign_bundle(label)
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
        raise EditionV19ReplayError(
            f"Alpha-v19 theorem {item.spec.name!r} exceeds unchanged proof-sharing limits"
        )
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id
            or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV19ReplayError("conservative proof interning changed a theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV19ReplayError(
                "unchanged intuitionistic kernel rejected an interned campaign proof body"
            )
    candidate = compile_layered_replay(
        interned,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise EditionV19ReplayError(
            f"unchanged kernel/resource policy rejected actual Alpha-v19 proof "
            f"{item.spec.name!r}"
        )
    return CheckedTheorem(item.spec, formula, candidate.certificate, candidate.proof_nodes)


@lru_cache(maxsize=None)
def replay(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    """Expose theorem authority only after an exact empty-context kernel check."""

    selected = _coerce_edition(edition)
    item = entry(name, edition=selected)
    if item is None:
        raise EditionV19ReplayError(f"unknown {selected.value} v19 theorem {name!r}")
    if not item.checked_use:
        raise EditionV19ReplayError(f"Alpha-v19 theorem {item.spec.name!r} is not checked")
    if item.spec.name in _RESIDUAL_PROMOTED_NAME_SET:
        return _replay_campaign_theorem(item, "residual")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_campaign_theorem(item, "frontier")
    return v18.replay(item.spec.name, edition=selected)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V19_ENROLLMENT_SHA256",
    "ALPHA_V19_IDENTITY_SHA256",
    "CAMPAIGN_ARTIFACT_FILENAMES",
    "CAMPAIGN_BUNDLE_LABELS",
    "EXPECTED_ALPHA_V19_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V19_COUNT",
    "EXPECTED_ALPHA_V19_EDGE_COUNT",
    "EXPECTED_ALPHA_V19_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V19_FRONTIER_COUNT",
    "EXPECTED_ALPHA_V19_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V19_LAYER_COUNT",
    "EXPECTED_ALPHA_V19_RESIDUAL_PROMOTION_COUNT",
    "EXPECTED_ALPHA_V19_RESIDUAL_PROMOTION_NAMES_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV19Error",
    "EditionV19ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "FRONTIER_NEW_NAMES",
    "LibraryEdition",
    "Membership",
    "PYODIDE_CAMPAIGN_BUNDLE_PATHS",
    "RESIDUAL_PROMOTED_NAMES",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_campaign_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_campaign_bundle_source",
]
