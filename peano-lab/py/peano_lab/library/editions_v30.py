"""Fail-closed completion of Gaussian-factorization mathematical campaigns over the immutable Alpha-v29 release.

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
from . import editions_v29 as v29
from .alpha_enrollment_v30 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V30_EXPECTED_COUNT,
    FRONTIER_V30_EXPECTED_EDGE_COUNT,
    FRONTIER_V30_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V29_COUNT,
    PARENT_ALPHA_V29_ENROLLMENT_SHA256,
    PARENT_ALPHA_V29_IDENTITY_SHA256,
    alpha_v30_enrollment,
)
from .editions_v5 import _enrollment_identity, _identity, _make_edition
from .campaign_gaussian_factorization_closure import compile_gaussian_factorization_replay
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayNode,
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


EditionName = v29.EditionName
Membership = v29.Membership
EvidenceStatus = v29.EvidenceStatus
EnrollmentOrigin = v29.EnrollmentOrigin
EditionEntry = v29.EditionEntry
LibraryEdition = v29.LibraryEdition

# Exact Gaussian inventory; checked replay additionally requires the immutable
# complete artifact and every ordinary body to pass the original kernel.
EXPECTED_ALPHA_V30_COUNT = 3_222
EXPECTED_ALPHA_V30_CHECKED_USE_COUNT = 3_222
EXPECTED_ALPHA_V30_FRONTIER_COUNT = 180
EXPECTED_ALPHA_V30_EDGE_COUNT = 10_588
EXPECTED_ALPHA_V30_LAYER_COUNT = 53
EXPECTED_ALPHA_V30_ENROLLMENT_SHA256 = "04b73a38d04d1bd8038c1712b7f4f6cc77156f97a890515524761bb1cdf71393"
EXPECTED_ALPHA_V30_IDENTITY_SHA256 = "8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9"
GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME = "alpha-v30-gaussian-factorization-proof-bundle-v1.json"
PYODIDE_GAUSSIAN_FACTORIZATION_BUNDLE_PATH = (
    f"/lab/proof-artifacts/{GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME}"
)


class EditionV30Error(ValueError):
    """The immutable parent, additive theorem inventory, or seal changed."""


class EditionV30ReplayError(EditionV30Error):
    """Checked use requires complete unchanged-kernel-accepted proof bytes."""


def dependency_depths(specs):
    return v29.dependency_depths(specs)


def dependency_layers(specs):
    return v29.dependency_layers(specs)


_ENROLLMENT = alpha_v30_enrollment()
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
ALPHA_ENTRIES: tuple[EditionEntry, ...] = (*v29.ALPHA_ENTRIES, *_FRONTIER_ENTRIES)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER = v29.STABLE_RELEASE_ORDER
STABLE_ENTRIES = v29.STABLE_ENTRIES
STABLE_SPECS = v29.STABLE_SPECS
STABLE_EDITION = v29.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V30_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V30_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V30_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        EXPECTED_ALPHA_V30_COUNT <= PARENT_ALPHA_V29_COUNT
        or EXPECTED_ALPHA_V30_CHECKED_USE_COUNT != EXPECTED_ALPHA_V30_COUNT
        or EXPECTED_ALPHA_V30_FRONTIER_COUNT <= 0
        or EXPECTED_ALPHA_V30_EDGE_COUNT <= 0
        or EXPECTED_ALPHA_V30_LAYER_COUNT <= 0
        or len(EXPECTED_ALPHA_V30_ENROLLMENT_SHA256) != 64
        or len(EXPECTED_ALPHA_V30_IDENTITY_SHA256) != 64
    ):
        raise EditionV30Error("Alpha-v30 is not sealed for admission")
    if (
        len(v29.ALPHA_ENTRIES) != PARENT_ALPHA_V29_COUNT
        or tuple(ALPHA_ENTRIES[:PARENT_ALPHA_V29_COUNT]) != v29.ALPHA_ENTRIES
        or any(newer is not older for newer, older in zip(ALPHA_ENTRIES, v29.ALPHA_ENTRIES))
        or _enrollment_identity(v29.ALPHA_ENTRIES) != PARENT_ALPHA_V29_ENROLLMENT_SHA256
        or _identity(EditionName.ALPHA, v29.ALPHA_ENTRIES)
        != PARENT_ALPHA_V29_IDENTITY_SHA256
    ):
        raise EditionV30Error("Alpha-v30 changed its immutable checked Alpha-v29 parent")
    if (
        STABLE_EDITION is not v29.STABLE_EDITION
        or STABLE_ENTRIES is not v29.STABLE_ENTRIES
        or STABLE_SPECS is not v29.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV30Error("Alpha-v30 changed its immutable Stable edition")
    if FRONTIER_V30_EXPECTED_COUNT and (
        len(_FRONTIER_ENTRIES) != FRONTIER_V30_EXPECTED_COUNT
        or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
        != FRONTIER_V30_EXPECTED_NAMES_SHA256
        or sum(len(item.spec.dependencies) for item in _FRONTIER_ENTRIES)
        != FRONTIER_V30_EXPECTED_EDGE_COUNT
        or Counter(_ENROLLMENT.campaign_by_name.values()) != EXPECTED_CAMPAIGN_COUNTS
    ):
        raise EditionV30Error("Alpha-v30 changed its exact additive constructive frontier")
    if len(ALPHA_CHECKED_SPECS) != len(ALPHA_ENTRIES):
        raise EditionV30Error("Alpha-v30 contains an unchecked theorem")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: len(ALPHA_ENTRIES) - 432,
    }:
        raise EditionV30Error("Alpha-v30 changed its checked evidence partition")
    if EXPECTED_ALPHA_V30_COUNT and (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V30_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or len(_FRONTIER_ENTRIES) != EXPECTED_ALPHA_V30_FRONTIER_COUNT
        or ALPHA_EDITION.edge_count != EXPECTED_ALPHA_V30_EDGE_COUNT
        or ALPHA_EDITION.layer_count != EXPECTED_ALPHA_V30_LAYER_COUNT
        or ALPHA_V30_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V30_ENROLLMENT_SHA256
        or ALPHA_V30_IDENTITY_SHA256 != EXPECTED_ALPHA_V30_IDENTITY_SHA256
    ):
        raise EditionV30Error("Alpha-v30 immutable theorem, evidence, or graph seal changed")
    available: set[str] = set()
    for item in ALPHA_ENTRIES:
        if not set(item.spec.dependencies) <= available:
            raise EditionV30Error(f"unchecked or forward dependency in {item.spec.name!r}")
        available.add(item.spec.name)


_validate_seals()
_bundle_source: Path | None = None


def _default_gaussian_factorization_bundle_source() -> Path:
    pyodide = Path(PYODIDE_GAUSSIAN_FACTORIZATION_BUNDLE_PATH)
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
        / GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME
    )


def set_gaussian_factorization_bundle_source(source: str | Path | None) -> None:
    global _bundle_source
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV30ReplayError("Gaussian-factorization proof source must be a filesystem path")
    _bundle_source = None if source is None else Path(source)
    _checked_gaussian_factorization_bundle.cache_clear()
    replay.cache_clear()


def _gaussian_factorization_module() -> ModuleType:
    try:
        return import_module(".campaign_gaussian_factorization_closure", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as error:
        raise EditionV30ReplayError("actual Alpha-v30 proof provider is unavailable") from error


def require_gaussian_factorization_seal() -> None:
    """Reject unfinished Alpha metadata without opening any proof artifact.

    This is only an eligibility gate for UI, export and lookup. It does not
    replace the original-kernel proof checks performed on actual checked use.
    Stable lookups never call this gate or invoke the artifact provider.
    """
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V30_COUNT
        or len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or len(FRONTIER_NEW_NAMES) != EXPECTED_ALPHA_V30_FRONTIER_COUNT
        or EXPECTED_ALPHA_V30_FRONTIER_COUNT != FRONTIER_V30_EXPECTED_COUNT
        or ALPHA_V30_IDENTITY_SHA256 != EXPECTED_ALPHA_V30_IDENTITY_SHA256
        or ALPHA_V30_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V30_ENROLLMENT_SHA256
    ):
        raise EditionV30ReplayError("Alpha-v30 is not sealed for checked use")
    module = _gaussian_factorization_module()
    number_fields = (
        "FRONTIER_COUNT", "THEOREM_COUNT", "ROOT_COUNT",
        "DEPENDENCY_EDGE_COUNT", "BUNDLE_NODE_COUNT", "BUNDLE_EDGE_COUNT",
        "BUNDLE_BODY_PROOF_NODES", "BUNDLE_BYTES",
    )
    digest_fields = ("ORDERED_NAMES_SHA256", "BUNDLE_SHA256")
    values = {key: getattr(module, "EXPECTED_GAUSSIAN_FACTORIZATION_" + key, None)
              for key in (*number_fields, *digest_fields)}
    if (
        any(type(values[key]) is not int or values[key] <= 0 for key in number_fields)
        or any(type(values[key]) is not str or len(values[key]) != 64
               or values[key] == "0" * 64
               or any(char not in "0123456789abcdef" for char in values[key])
               for key in digest_fields)
        or values["FRONTIER_COUNT"] != len(FRONTIER_NEW_NAMES)
        or values["BUNDLE_NODE_COUNT"] != values["THEOREM_COUNT"] + 1
        or values["BUNDLE_EDGE_COUNT"] != values["DEPENDENCY_EDGE_COUNT"] + values["ROOT_COUNT"]
    ):
        raise EditionV30ReplayError("Alpha-v30 Gaussian proof metadata is not sealed for checked use")


@lru_cache(maxsize=1)
def _checked_gaussian_factorization_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    require_gaussian_factorization_seal()
    if (
        EXPECTED_ALPHA_V30_COUNT <= PARENT_ALPHA_V29_COUNT
        or FRONTIER_V30_EXPECTED_COUNT <= 0
        or len(EXPECTED_ALPHA_V30_ENROLLMENT_SHA256) != 64
        or len(EXPECTED_ALPHA_V30_IDENTITY_SHA256) != 64
        or len(FRONTIER_V30_EXPECTED_NAMES_SHA256) != 64
    ):
        raise EditionV30ReplayError("Alpha-v30 is not sealed for checked use")
    module = _gaussian_factorization_module()
    source = _bundle_source or _default_gaussian_factorization_bundle_source()
    try:
        payload = source.read_bytes()
        expected_size = getattr(module, "EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES")
        expected_digest = getattr(module, "EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256")
        expected_nodes = getattr(module, "EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError) as error:
        raise EditionV30ReplayError("actual Alpha-v30 proof bytes are unavailable") from error
    if (
        expected_size <= 0
        or len(expected_digest) != 64
        or len(payload) != expected_size
        or sha256(payload).hexdigest() != expected_digest
    ):
        raise EditionV30ReplayError("Alpha-v30 proof differs from its frozen provenance")
    try:
        bundle, target = decode_proof_bundle(payload.decode("utf-8"))
        receipt = module.check_gaussian_factorization_proof_bundle(
            bundle, target, parent_specs=v29.ALPHA_CHECKED_SPECS
        )
        plan = module.gaussian_factorization_plan(parent_specs=v29.ALPHA_CHECKED_SPECS)
    except (
        AttributeError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EditionV30ReplayError(
            "the unchanged intuitionistic kernel rejected the actual Alpha-v30 proof"
        ) from error
    positions = {row.name: row.node_id for row in plan.rows}
    if (
        not _FRONTIER_NEW_NAME_SET <= positions.keys()
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_nodes
    ):
        raise EditionV30ReplayError("Alpha-v30 changed its graph or skipped a kernel check")
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
            raise EditionV30ReplayError(f"Alpha-v30 proof changed exact theorem {name!r}")
    return bundle, receipt, positions


def checked_gaussian_factorization_bundle() -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    return _checked_gaussian_factorization_bundle()


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV30Error(f"unknown theorem-library v30 edition {value!r}")


def edition(name: EditionName | str = EditionName.STABLE) -> LibraryEdition:
    selected = _coerce_edition(name)
    if selected is EditionName.STABLE:
        return STABLE_EDITION
    require_gaussian_factorization_seal()
    return ALPHA_EDITION


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


def _replay_gaussian_factorization_theorem(item: EditionEntry) -> CheckedTheorem:
    bundle, _receipt, positions = _checked_gaussian_factorization_bundle()
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
        raise EditionV30ReplayError(f"Alpha-v30 theorem {item.spec.name!r} exceeds sharing limits")
    for original, actual in zip(layered.nodes, interned.nodes, strict=True):
        if (
            original.node_id != actual.node_id
            or original.target != actual.target
            or original.dependencies != actual.dependencies
        ):
            raise EditionV30ReplayError("conservative proof interning changed a theorem")
        target = actual.target
        for dependency in reversed(actual.dependencies):
            target = Imp(bundle.nodes[dependency].target, target)
        if not check((), actual.body, target):
            raise EditionV30ReplayError("the kernel rejected an interned Gaussian-factorization body")
    candidate = compile_gaussian_factorization_replay(
        interned,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None or not check((), candidate.certificate, formula):
        raise EditionV30ReplayError(
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
        raise EditionV30ReplayError(f"unknown {selected.value} v30 theorem {name!r}")
    if not item.checked_use:
        raise EditionV30ReplayError(f"Alpha-v30 theorem {item.spec.name!r} is not checked")
    if item.spec.name in _FRONTIER_NEW_NAME_SET:
        return _replay_gaussian_factorization_theorem(item)
    return v29.replay(item.spec.name, edition=selected)


__all__ = (
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V30_ENROLLMENT_SHA256",
    "ALPHA_V30_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V30_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V30_COUNT",
    "EXPECTED_ALPHA_V30_EDGE_COUNT",
    "EXPECTED_ALPHA_V30_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V30_FRONTIER_COUNT",
    "EXPECTED_ALPHA_V30_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V30_LAYER_COUNT",
    "EditionEntry",
    "EditionName",
    "EditionV30Error",
    "EditionV30ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "FRONTIER_NEW_NAMES",
    "LibraryEdition",
    "Membership",
    "PYODIDE_GAUSSIAN_FACTORIZATION_BUNDLE_PATH",
    "GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_gaussian_factorization_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "replay",
    "require_gaussian_factorization_seal",
    "set_gaussian_factorization_bundle_source",
)
