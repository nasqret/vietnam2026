"""Immutable Alpha-v17 promotion of both quadratic supplementary laws.

Alpha v17 preserves every theorem specification, enrollment position,
membership, dependency, proof script, and the complete Stable release from
Alpha v16. Exactly 31 previously body-only ancestors of the two supplementary
laws receive checked-use authority through a complete, independently checked
constructive proof bundle.

Import is inventory-only: it neither opens a proof artifact nor checks a proof.
Using a newly promoted theorem always decodes and checks every actual bundled
body and subsequently asks the unchanged intuitionistic kernel to check an
ordinary, dependency-closed empty-context certificate for that exact theorem.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from ..kernel.checker import check
from ..kernel.formulas import And
from . import editions_v16 as v16
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
from .theorems import CheckedTheorem, TheoremSpec, _closed_formula


EditionName = v16.EditionName
Membership = v16.Membership
EvidenceStatus = v16.EvidenceStatus
EnrollmentOrigin = v16.EnrollmentOrigin
EditionEntry = v16.EditionEntry
LibraryEdition = v16.LibraryEdition

SUPPLEMENTARY_ROOT_NAMES = (
    "quadratic_supplement_minus_one_complete",
    "quadratic_supplement_two_complete",
)
EXPECTED_ALPHA_V17_COUNT = 1_673
EXPECTED_ALPHA_V17_EDGE_COUNT = 5_615
EXPECTED_ALPHA_V17_LAYER_COUNT = 53
EXPECTED_ALPHA_V17_CHECKED_USE_COUNT = 916
EXPECTED_ALPHA_V17_PROMOTION_COUNT = 31
EXPECTED_ALPHA_V17_DEPENDENCY_CLOSURE_COUNT = 437
EXPECTED_ALPHA_V17_CHECKED_EDGE_COUNT = 2_743
EXPECTED_ALPHA_V17_ENROLLMENT_SHA256 = (
    "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
)
EXPECTED_ALPHA_V17_IDENTITY_SHA256 = (
    "db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4"
)
EXPECTED_ALPHA_V17_PROMOTION_NAMES_SHA256 = (
    "21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7"
)
EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256 = (
    "79fc4717dbe570bf836cca5ec699492ff3995700ec25336a20d03cc57261054c"
)
EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES = 1_732_249
EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT = 438
EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT = 1_429
EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES = 33_173
PYODIDE_SUPPLEMENTARY_BUNDLE_PATH = (
    "/lab/proof-artifacts/supplementary-laws-proof-bundle-v1.json"
)


class EditionV17Error(ValueError):
    """The immutable parent, supplementary graph, or release seal is invalid."""


class EditionV17ReplayError(EditionV17Error):
    """Checked use requires actual unchanged-kernel-accepted proof data."""


def dependency_depths(specs):
    return v16.dependency_depths(specs)


def dependency_layers(specs):
    return v16.dependency_layers(specs)


def _supplementary_names() -> tuple[str, ...]:
    selected: set[str] = set()
    pending = list(SUPPLEMENTARY_ROOT_NAMES)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = v16.ALPHA_EDITION.by_name.get(name)
        if item is None:
            raise EditionV17Error(
                f"supplementary closure has an unknown immutable parent row {name!r}"
            )
        selected.add(name)
        pending.extend(item.spec.dependencies)
    result = tuple(
        item.spec.name for item in v16.ALPHA_ENTRIES if item.spec.name in selected
    )
    if (
        len(result) != EXPECTED_ALPHA_V17_DEPENDENCY_CLOSURE_COUNT
        or len(result) != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT - 1
    ):
        raise EditionV17Error("Alpha-v17 supplementary dependency closure changed")
    return result


SUPPLEMENTARY_BUNDLE_NAMES = _supplementary_names()
_SUPPLEMENTARY_BUNDLE_POSITIONS = {
    name: index for index, name in enumerate(SUPPLEMENTARY_BUNDLE_NAMES)
}
SUPPLEMENTARY_PROMOTED_NAMES = tuple(
    name
    for name in SUPPLEMENTARY_BUNDLE_NAMES
    if not v16.ALPHA_EDITION.by_name[name].checked_use
)
_SUPPLEMENTARY_PROMOTED_NAME_SET = frozenset(SUPPLEMENTARY_PROMOTED_NAMES)

if (
    len(SUPPLEMENTARY_PROMOTED_NAMES) != EXPECTED_ALPHA_V17_PROMOTION_COUNT
    or sha256("\n".join(SUPPLEMENTARY_PROMOTED_NAMES).encode("utf-8")).hexdigest()
    != EXPECTED_ALPHA_V17_PROMOTION_NAMES_SHA256
):
    raise EditionV17Error("Alpha-v17 exact supplementary evidence-transition set changed")


ALPHA_ENTRIES: tuple[EditionEntry, ...] = tuple(
    replace(item, evidence=EvidenceStatus.ALPHA_CLOSED)
    if item.spec.name in _SUPPLEMENTARY_PROMOTED_NAME_SET
    else item
    for item in v16.ALPHA_ENTRIES
)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER: tuple[str, ...] = v16.STABLE_RELEASE_ORDER
STABLE_ENTRIES: tuple[EditionEntry, ...] = v16.STABLE_ENTRIES
STABLE_SPECS: tuple[TheoremSpec, ...] = v16.STABLE_SPECS
STABLE_EDITION = v16.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V17_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V17_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V17_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V17_COUNT
        or len(ALPHA_ENTRIES) != len(v16.ALPHA_ENTRIES)
        or ALPHA_SPECS != v16.ALPHA_SPECS
    ):
        raise EditionV17Error("Alpha-v17 changed its immutable v16 theorem ledger")
    if (
        STABLE_EDITION is not v16.STABLE_EDITION
        or STABLE_ENTRIES is not v16.STABLE_ENTRIES
        or STABLE_SPECS is not v16.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV17Error("Alpha-v17 changed the immutable Stable edition")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V17_EDGE_COUNT,
        EXPECTED_ALPHA_V17_LAYER_COUNT,
    ):
        raise EditionV17Error("Alpha-v17 changed its immutable dependency topology")
    if (
        ALPHA_V17_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V17_ENROLLMENT_SHA256
        or ALPHA_V17_ENROLLMENT_SHA256 != v16.ALPHA_V16_ENROLLMENT_SHA256
        or _enrollment_identity(ALPHA_ENTRIES)
        != _enrollment_identity(v16.ALPHA_ENTRIES)
    ):
        raise EditionV17Error("Alpha-v17 changed its immutable enrollment identity")
    if (
        ALPHA_V17_IDENTITY_SHA256 != EXPECTED_ALPHA_V17_IDENTITY_SHA256
        or _identity(EditionName.ALPHA, ALPHA_ENTRIES)
        != EXPECTED_ALPHA_V17_IDENTITY_SHA256
    ):
        raise EditionV17Error("Alpha-v17 promoted-evidence identity changed")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 484,
        EvidenceStatus.BODY_CHECKED: 757,
    }:
        raise EditionV17Error("Alpha-v17 promoted evidence partition changed")
    if Counter(item.membership for item in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 1_241,
    }:
        raise EditionV17Error("Alpha-v17 changed immutable release membership")
    if len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V17_CHECKED_USE_COUNT:
        raise EditionV17Error("Alpha-v17 checked-use evidence count changed")
    checked = {item.name for item in ALPHA_CHECKED_SPECS}
    if (
        sum(len(item.dependencies) for item in ALPHA_CHECKED_SPECS)
        != EXPECTED_ALPHA_V17_CHECKED_EDGE_COUNT
    ):
        raise EditionV17Error("Alpha-v17 checked-use dependency edge count changed")
    for spec in ALPHA_CHECKED_SPECS:
        missing = set(spec.dependencies).difference(checked)
        if missing:
            raise EditionV17Error(
                f"Alpha-v17 checked theorem {spec.name!r} has unchecked "
                f"prerequisites {sorted(missing)!r}"
            )
    for older, newer in zip(v16.ALPHA_ENTRIES, ALPHA_ENTRIES, strict=True):
        if newer.spec.name in _SUPPLEMENTARY_PROMOTED_NAME_SET:
            if (
                older.checked_use
                or older.membership is not Membership.ALPHA_ONLY
                or older.enrollment_origin
                not in (EnrollmentOrigin.BERTRAND, EnrollmentOrigin.HA)
                or newer != replace(older, evidence=EvidenceStatus.ALPHA_CLOSED)
            ):
                raise EditionV17Error(
                    f"invalid supplementary evidence transition for {newer.spec.name!r}"
                )
        elif newer is not older:
            raise EditionV17Error(
                f"Alpha-v17 mutated unrelated parent row {older.spec.name!r}"
            )
    for name in SUPPLEMENTARY_ROOT_NAMES:
        if ALPHA_EDITION.by_name[name].evidence is not EvidenceStatus.ALPHA_CLOSED:
            raise EditionV17Error(f"Alpha-v17 supplementary root {name!r} is not closed")


_validate_seals()

_supplementary_bundle_source: Path | None = None


def _default_supplementary_bundle_source() -> Path:
    pyodide = Path(PYODIDE_SUPPLEMENTARY_BUNDLE_PATH)
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    if len(location.parents) > 4:
        return (
            location.parents[4]
            / "research"
            / "arithmetic-library"
            / "artifacts"
            / "supplementary-laws-proof-bundle-v1.json"
        )
    return pyodide


def set_supplementary_bundle_source(source: str | Path | None) -> None:
    """Set the explicit actual-proof path and invalidate checked-use caches."""

    global _supplementary_bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV17ReplayError("supplementary proof source must be a filesystem path")
    _supplementary_bundle_source = None if source is None else Path(source)
    _checked_supplementary_bundle.cache_clear()
    replay.cache_clear()


@lru_cache(maxsize=1)
def _checked_supplementary_bundle() -> tuple[ProofBundle, CheckedProofBundle]:
    source = _supplementary_bundle_source or _default_supplementary_bundle_source()
    try:
        payload = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise EditionV17ReplayError(
            f"actual Alpha-v17 supplementary-law proof data are unavailable: {source!s}"
        ) from exc
    data = payload.encode("utf-8")
    if (
        len(data) != EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES
        or sha256(data).hexdigest() != EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256
    ):
        raise EditionV17ReplayError(
            "Alpha-v17 supplementary proof artifact does not match its frozen provenance"
        )
    try:
        bundle, target = decode_proof_bundle(payload)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise EditionV17ReplayError(
            "Alpha-v17 supplementary artifact is not a canonical complete proof bundle"
        ) from exc
    formulas = tuple(
        _closed_formula(v16.ALPHA_EDITION.by_name[name].spec.statement)
        for name in SUPPLEMENTARY_ROOT_NAMES
    )
    expected_target = And(formulas[0], formulas[1])
    if (
        len(bundle.nodes) != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT
        or bundle.root != len(bundle.nodes) - 1
        or target != expected_target
    ):
        raise EditionV17ReplayError("Alpha-v17 supplementary artifact changed its roots")
    for index, name in enumerate(SUPPLEMENTARY_BUNDLE_NAMES):
        node = bundle.nodes[index]
        spec = v16.ALPHA_EDITION.by_name[name].spec
        if (
            type(node) is not BundleNode
            or node.node_id != index
            or node.target != _closed_formula(spec.statement)
            or node.dependencies
            != tuple(_SUPPLEMENTARY_BUNDLE_POSITIONS[item] for item in spec.dependencies)
        ):
            raise EditionV17ReplayError(
                f"Alpha-v17 supplementary artifact changed frozen theorem {name!r}"
            )
    synthetic = bundle.nodes[-1]
    if (
        synthetic.node_id != len(bundle.nodes) - 1
        or synthetic.target != expected_target
        or synthetic.dependencies
        != tuple(_SUPPLEMENTARY_BUNDLE_POSITIONS[name] for name in SUPPLEMENTARY_ROOT_NAMES)
    ):
        raise EditionV17ReplayError("Alpha-v17 supplementary conjunction node changed")
    try:
        receipt = check_proof_bundle(bundle, target)
    except (ProofBundleError, RecursionError, TypeError, ValueError) as exc:
        raise EditionV17ReplayError(
            "the unchanged intuitionistic kernel rejected Alpha-v17 supplementary proofs"
        ) from exc
    if (
        receipt.node_count != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT
        or receipt.kernel_calls != EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT
        or receipt.dependency_edges != EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT
        or receipt.total_body_nodes != EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES
    ):
        raise EditionV17ReplayError("Alpha-v17 supplementary proof metrics changed")
    return bundle, receipt


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV17Error(f"unknown theorem-library v17 edition {value!r}")


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


def _replay_promoted_supplementary(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt = _checked_supplementary_bundle()
    root_id = _SUPPLEMENTARY_BUNDLE_POSITIONS[item.spec.name]
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
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
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
        raise EditionV17ReplayError(
            f"Alpha-v17 theorem {item.spec.name!r} exceeds the unchanged "
            "layered proof/resource policy"
        )
    if not check((), candidate.certificate, formula):
        raise EditionV17ReplayError(
            f"the unchanged intuitionistic kernel rejected promoted Alpha-v17 "
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
        raise EditionV17ReplayError(f"unknown {selected.value} v17 theorem {name!r}")
    if not item.checked_use:
        raise EditionV17ReplayError(
            f"{selected.value} v17 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    if item.spec.name not in _SUPPLEMENTARY_PROMOTED_NAME_SET:
        return v16.replay(item.spec.name, edition=selected)
    if selected is not EditionName.ALPHA:
        raise EditionV17ReplayError(
            f"promoted supplementary theorem {item.spec.name!r} is not in Stable"
        )
    return _replay_promoted_supplementary(item)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V17_ENROLLMENT_SHA256",
    "ALPHA_V17_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV17Error",
    "EditionV17ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "EXPECTED_ALPHA_V17_CHECKED_EDGE_COUNT",
    "EXPECTED_ALPHA_V17_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V17_COUNT",
    "EXPECTED_ALPHA_V17_DEPENDENCY_CLOSURE_COUNT",
    "EXPECTED_ALPHA_V17_EDGE_COUNT",
    "EXPECTED_ALPHA_V17_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V17_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V17_LAYER_COUNT",
    "EXPECTED_ALPHA_V17_PROMOTION_COUNT",
    "EXPECTED_ALPHA_V17_PROMOTION_NAMES_SHA256",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT",
    "EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256",
    "LibraryEdition",
    "Membership",
    "PYODIDE_SUPPLEMENTARY_BUNDLE_PATH",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "SUPPLEMENTARY_BUNDLE_NAMES",
    "SUPPLEMENTARY_PROMOTED_NAMES",
    "SUPPLEMENTARY_ROOT_NAMES",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "set_supplementary_bundle_source",
]
