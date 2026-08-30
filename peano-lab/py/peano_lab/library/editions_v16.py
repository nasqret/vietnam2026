"""Immutable Alpha-v16 promotion of the independently closed QR proof graph.

Alpha v16 preserves every Alpha-v15 theorem specification, enrollment position,
origin, dependency, script, membership, and the entire Stable release.  Exactly
315 previously unclosed quadratic-reciprocity entries become ``alpha_closed``
because the complete self-contained 557-node constructive proof bundle has been
checked independently.  No unrelated body-only theorem is promoted.

Importing this module reads no proof artifact and checks no proof.  Using a
newly promoted theorem loads its complete actual proof data, reconstructs the
exact dependency-closed ordinary layered certificate, and asks the unchanged
intuitionistic kernel to check that certificate from the empty context.  Hashes
and release labels never replace a genuine proof.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from ..kernel.checker import check
from . import editions_v15 as v15
from .editions_v5 import _enrollment_identity, _identity, _make_edition
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayNode,
    compile_layered_replay,
)
from .proof_bundle import (
    BundleNode,
    CheckedProofBundle,
    ProofBundle,
    ProofBundleError,
    check_proof_bundle,
    decode_proof_bundle,
)
from .quadratic_reciprocity_stack import QR_ROOT_NAME
from .quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from .quadratic_residue_surface import QUADRATIC_RECIPROCITY_COMBINED
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


EditionName = v15.EditionName
Membership = v15.Membership
EvidenceStatus = v15.EvidenceStatus
EnrollmentOrigin = v15.EnrollmentOrigin
EditionEntry = v15.EditionEntry
LibraryEdition = v15.LibraryEdition

EXPECTED_ALPHA_V16_COUNT = 1_673
EXPECTED_ALPHA_V16_EDGE_COUNT = 5_615
EXPECTED_ALPHA_V16_LAYER_COUNT = 53
EXPECTED_ALPHA_V16_CHECKED_USE_COUNT = 885
EXPECTED_ALPHA_V16_PROMOTION_COUNT = 315
EXPECTED_ALPHA_V16_CHECKED_EDGE_COUNT = 2_641
EXPECTED_ALPHA_V16_ENROLLMENT_SHA256 = (
    "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
)
EXPECTED_ALPHA_V16_IDENTITY_SHA256 = (
    "3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10"
)
EXPECTED_ALPHA_V16_PROMOTION_NAMES_SHA256 = (
    "aba2d7a192b6f1c11fbafbed1001bf592ca9ed8f5bee7ac3f1de863dd870a80e"
)
EXPECTED_QR_BUNDLE_SHA256 = (
    "3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c"
)
EXPECTED_QR_BUNDLE_BYTES = 2_790_229
EXPECTED_QR_BUNDLE_NODE_COUNT = 557
EXPECTED_QR_BUNDLE_EDGE_COUNT = 1_787
EXPECTED_QR_BUNDLE_BODY_PROOF_NODES = 41_722
EXPECTED_QR_STACK_GRAPH_SHA256 = (
    "26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253"
)
EXPECTED_QR_STACK_SOURCE_SHA256 = (
    "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1"
)
PYODIDE_QR_BUNDLE_PATH = (
    "/lab/proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json"
)


class EditionV16Error(ValueError):
    """The immutable parent, promoted graph, or Alpha-v16 seal is invalid."""


class EditionV16ReplayError(EditionV16Error):
    """Checked use requires a real, unchanged-kernel-accepted closed proof."""


def dependency_depths(specs):
    return v15.dependency_depths(specs)


def dependency_layers(specs):
    return v15.dependency_layers(specs)


def _promotion_names() -> tuple[str, ...]:
    stack = quadratic_reciprocity_stack()
    if (
        len(stack.admission_order) != EXPECTED_QR_BUNDLE_NODE_COUNT
        or stack.graph_sha256 != EXPECTED_QR_STACK_GRAPH_SHA256
        or stack.source_sha256 != EXPECTED_QR_STACK_SOURCE_SHA256
    ):
        raise EditionV16Error("Alpha-v16 QR source/dependency graph changed")
    result = tuple(
        spec.name
        for spec in stack.admission_order
        if not v15.ALPHA_EDITION.by_name[spec.name].checked_use
    )
    if (
        len(result) != EXPECTED_ALPHA_V16_PROMOTION_COUNT
        or result[-1] != QR_ROOT_NAME
        or sha256("\n".join(result).encode("utf-8")).hexdigest()
        != EXPECTED_ALPHA_V16_PROMOTION_NAMES_SHA256
    ):
        raise EditionV16Error("Alpha-v16 exact QR evidence-transition set changed")
    return result


QR_PROMOTED_NAMES = _promotion_names()
_QR_PROMOTED_NAME_SET = frozenset(QR_PROMOTED_NAMES)


def _alpha_entries() -> tuple[EditionEntry, ...]:
    return tuple(
        replace(item, evidence=EvidenceStatus.ALPHA_CLOSED)
        if item.spec.name in _QR_PROMOTED_NAME_SET
        else item
        for item in v15.ALPHA_ENTRIES
    )


ALPHA_ENTRIES: tuple[EditionEntry, ...] = _alpha_entries()
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER: tuple[str, ...] = v15.STABLE_RELEASE_ORDER
STABLE_ENTRIES: tuple[EditionEntry, ...] = v15.STABLE_ENTRIES
STABLE_SPECS: tuple[TheoremSpec, ...] = v15.STABLE_SPECS
STABLE_EDITION = v15.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V16_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V16_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V16_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V16_COUNT
        or len(ALPHA_ENTRIES) != len(v15.ALPHA_ENTRIES)
        or ALPHA_SPECS != v15.ALPHA_SPECS
    ):
        raise EditionV16Error("Alpha-v16 changed its immutable v15 theorem ledger")
    if (
        STABLE_EDITION is not v15.STABLE_EDITION
        or STABLE_ENTRIES is not v15.STABLE_ENTRIES
        or STABLE_SPECS is not v15.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV16Error("Alpha-v16 changed the immutable Stable edition")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V16_EDGE_COUNT,
        EXPECTED_ALPHA_V16_LAYER_COUNT,
    ):
        raise EditionV16Error("Alpha-v16 changed its immutable dependency topology")
    if (
        ALPHA_V16_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V16_ENROLLMENT_SHA256
        or ALPHA_V16_ENROLLMENT_SHA256 != v15.ALPHA_V15_ENROLLMENT_SHA256
        or _enrollment_identity(ALPHA_ENTRIES)
        != _enrollment_identity(v15.ALPHA_ENTRIES)
    ):
        raise EditionV16Error("Alpha-v16 changed an immutable enrollment identity")
    if (
        ALPHA_V16_IDENTITY_SHA256 != EXPECTED_ALPHA_V16_IDENTITY_SHA256
        or _identity(EditionName.ALPHA, ALPHA_ENTRIES)
        != EXPECTED_ALPHA_V16_IDENTITY_SHA256
    ):
        raise EditionV16Error("Alpha-v16 promoted-evidence identity changed")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 453,
        EvidenceStatus.BODY_CHECKED: 788,
    }:
        raise EditionV16Error("Alpha-v16 promoted evidence partition changed")
    if Counter(item.membership for item in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 1_241,
    }:
        raise EditionV16Error("Alpha-v16 changed immutable release membership")
    if len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V16_CHECKED_USE_COUNT:
        raise EditionV16Error("Alpha-v16 checked-use evidence count changed")
    checked = {item.name for item in ALPHA_CHECKED_SPECS}
    if (
        sum(len(item.dependencies) for item in ALPHA_CHECKED_SPECS)
        != EXPECTED_ALPHA_V16_CHECKED_EDGE_COUNT
    ):
        raise EditionV16Error("Alpha-v16 checked-use dependency edge count changed")
    for spec in ALPHA_CHECKED_SPECS:
        missing = set(spec.dependencies).difference(checked)
        if missing:
            raise EditionV16Error(
                f"Alpha-v16 checked theorem {spec.name!r} has unchecked "
                f"prerequisites {sorted(missing)!r}"
            )
    for older, newer in zip(v15.ALPHA_ENTRIES, ALPHA_ENTRIES, strict=True):
        if newer.spec.name in _QR_PROMOTED_NAME_SET:
            if (
                older.checked_use
                or older.membership is not Membership.ALPHA_ONLY
                or older.enrollment_origin is not EnrollmentOrigin.QR
                or newer != replace(older, evidence=EvidenceStatus.ALPHA_CLOSED)
            ):
                raise EditionV16Error(
                    f"invalid QR evidence transition for {newer.spec.name!r}"
                )
        elif newer is not older:
            raise EditionV16Error(
                f"Alpha-v16 mutated unrelated parent row {older.spec.name!r}"
            )
    if ALPHA_EDITION.by_name[QR_ROOT_NAME].evidence is not EvidenceStatus.ALPHA_CLOSED:
        raise EditionV16Error("Alpha-v16 quadratic reciprocity root is not closed")


_validate_seals()

_qr_bundle_source: Path | None = None


def _default_qr_bundle_source() -> Path:
    pyodide = Path(PYODIDE_QR_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    if len(location.parents) > 4:
        return (
            location.parents[4]
            / "research"
            / "arithmetic-library"
            / "artifacts"
            / "quadratic-reciprocity-proof-bundle-v1.json"
        )
    return pyodide


def set_qr_bundle_source(source: str | Path | None) -> None:
    """Set the explicit actual-proof location; changing it invalidates caches."""

    global _qr_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV16ReplayError("QR proof-bundle source must be a filesystem path")
    _qr_bundle_source = None if source is None else Path(source)
    _checked_qr_bundle.cache_clear()
    replay.cache_clear()


@lru_cache(maxsize=1)
def _checked_qr_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _qr_bundle_source or _default_qr_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise EditionV16ReplayError(
            f"actual Alpha-v16 quadratic-reciprocity proof data are unavailable: "
            f"{source!s}"
        ) from exc
    data = payload.encode("utf-8")
    if (
        len(data) != EXPECTED_QR_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_QR_BUNDLE_SHA256
    ):
        raise EditionV16ReplayError(
            "Alpha-v16 QR proof artifact does not match its frozen provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise EditionV16ReplayError(
            "Alpha-v16 QR proof artifact is not a canonical complete proof bundle"
        ) from exc
    stack = quadratic_reciprocity_stack()
    expected_target = _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
    if (
        len(bundle.nodes) != EXPECTED_QR_BUNDLE_NODE_COUNT
        or bundle.root != len(bundle.nodes) - 1
        or target != expected_target
    ):
        raise EditionV16ReplayError("Alpha-v16 QR artifact changed its exact root")

    positions = {spec.name: index for index, spec in enumerate(stack.admission_order)}
    for index, (node, spec) in enumerate(
        zip(bundle.nodes, stack.admission_order, strict=True)
    ):
        if (
            type(node) is not BundleNode
            or node.node_id != index
            or node.target != _closed_formula(spec.statement)
            or node.dependencies
            != tuple(positions[name] for name in spec.dependencies)
        ):
            raise EditionV16ReplayError(
                f"Alpha-v16 QR artifact changed frozen theorem {spec.name!r}"
            )
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise EditionV16ReplayError(
            "the unchanged intuitionistic kernel rejected Alpha-v16 QR proof data"
        ) from exc
    if (
        receipt.node_count != EXPECTED_QR_BUNDLE_NODE_COUNT
        or receipt.kernel_calls != EXPECTED_QR_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_QR_BUNDLE_EDGE_COUNT
        or receipt.total_body_nodes != EXPECTED_QR_BUNDLE_BODY_PROOF_NODES
    ):
        raise EditionV16ReplayError("Alpha-v16 QR proof bundle metrics changed")
    return bundle, receipt


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV16Error(f"unknown theorem-library v16 edition {value!r}")


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


def _replay_promoted_qr(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt = _checked_qr_bundle()
    stack = quadratic_reciprocity_stack()
    positions = {spec.name: index for index, spec in enumerate(stack.admission_order)}
    root_id = positions[item.spec.name]
    selected: set[int] = set()
    pending = [root_id]
    while pending:
        node_id = pending.pop()
        if node_id in selected:
            continue
        selected.add(node_id)
        pending.extend(bundle.nodes[node_id].dependencies)
    layered = LayeredReplayBundle(
        tuple(
            LayeredReplayNode(
                node.node_id,
                node.target,
                node.dependencies,
                node.body,
            )
            for node in bundle.nodes
            if node.node_id in selected
        ),
        root_id,
    )
    formula = _closed_formula(item.spec.statement)
    candidate = compile_layered_replay(
        layered,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None:
        raise EditionV16ReplayError(
            f"Alpha-v16 theorem {item.spec.name!r} exceeds the unchanged "
            "layered proof/resource policy"
        )
    if not check((), candidate.certificate, formula):
        raise EditionV16ReplayError(
            f"the unchanged intuitionistic kernel rejected promoted Alpha-v16 "
            f"theorem {item.spec.name!r}"
        )
    return CheckedTheorem(
        item.spec,
        formula,
        candidate.certificate,
        candidate.proof_nodes,
    )


@lru_cache(maxsize=None)
def replay(
    name: str,
    *,
    edition: EditionName | str = EditionName.STABLE,
) -> CheckedTheorem:
    """Expose checked use only after an actual empty-context kernel check."""

    selected = _coerce_edition(edition)
    item = entry(name, edition=selected)
    if item is None:
        raise EditionV16ReplayError(
            f"unknown {selected.value} v16 theorem {name!r}"
        )
    if not item.checked_use:
        raise EditionV16ReplayError(
            f"{selected.value} v16 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    if item.spec.name not in _QR_PROMOTED_NAME_SET:
        return v15.replay(item.spec.name, edition=selected)
    if selected is not EditionName.ALPHA:
        raise EditionV16ReplayError(
            f"promoted QR theorem {item.spec.name!r} is not in Stable"
        )
    return _replay_promoted_qr(item)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V16_ENROLLMENT_SHA256",
    "ALPHA_V16_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV16Error",
    "EditionV16ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "EXPECTED_ALPHA_V16_CHECKED_EDGE_COUNT",
    "EXPECTED_ALPHA_V16_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V16_COUNT",
    "EXPECTED_ALPHA_V16_EDGE_COUNT",
    "EXPECTED_ALPHA_V16_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V16_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V16_LAYER_COUNT",
    "EXPECTED_ALPHA_V16_PROMOTION_COUNT",
    "EXPECTED_ALPHA_V16_PROMOTION_NAMES_SHA256",
    "EXPECTED_QR_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_QR_BUNDLE_BYTES",
    "EXPECTED_QR_BUNDLE_EDGE_COUNT",
    "EXPECTED_QR_BUNDLE_NODE_COUNT",
    "EXPECTED_QR_BUNDLE_SHA256",
    "LibraryEdition",
    "Membership",
    "PYODIDE_QR_BUNDLE_PATH",
    "QR_PROMOTED_NAMES",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_qr_bundle_source",
]
