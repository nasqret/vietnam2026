"""Alpha v18: evidence-only admission of five independently proved flagships.

The immutable Alpha-v17 theorem ledger, dependency graph and complete Stable
edition remain untouched. Exactly 673 genuinely proved, formerly body-only
theorems receive checked-use authority from the complete Lucas, Kummer,
Bertrand, four-square and two-square proof bundles.

Import builds and seals inventory only. It never opens or imports proof-bundle
providers. Actual use of a newly admitted theorem instead requires frozen
artifact bytes, all exact dependency-curried bodies accepted by the unchanged
intuitionistic kernel, and an ordinary empty-context root certificate replayed
under the unchanged layered resource limits.
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
from ..kernel.formulas import And, Imp
from . import editions_v17 as v17
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


EditionName = v17.EditionName
Membership = v17.Membership
EvidenceStatus = v17.EvidenceStatus
EnrollmentOrigin = v17.EnrollmentOrigin
EditionEntry = v17.EditionEntry
LibraryEdition = v17.LibraryEdition

FLAGSHIP_BUNDLE_LABELS = (
    "lucas",
    "kummer",
    "bertrand",
    "four_square",
    "two_square",
)
FLAGSHIP_ROOT_NAMES = (
    "lucas_theorem",
    "kummer_binomial_carry_bit_count",
    "kummer_carry_free_iff_not_divides",
    "bertrand_strict",
    "four_square_lagrange",
    "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
)
FLAGSHIP_BUNDLE_ROOTS: dict[str, tuple[str, ...]] = {
    "lucas": (FLAGSHIP_ROOT_NAMES[0],),
    "kummer": FLAGSHIP_ROOT_NAMES[1:3],
    "bertrand": (FLAGSHIP_ROOT_NAMES[3],),
    "four_square": (FLAGSHIP_ROOT_NAMES[4],),
    "two_square": (FLAGSHIP_ROOT_NAMES[5],),
}
EXPECTED_ALPHA_V18_COUNT = 1_673
EXPECTED_ALPHA_V18_EDGE_COUNT = 5_615
EXPECTED_ALPHA_V18_LAYER_COUNT = 53
EXPECTED_ALPHA_V18_CHECKED_USE_COUNT = 1_589
EXPECTED_ALPHA_V18_PROMOTION_COUNT = 673
EXPECTED_ALPHA_V18_DEPENDENCY_CLOSURE_COUNT = 1_113
EXPECTED_ALPHA_V18_CHECKED_EDGE_COUNT = 5_366
EXPECTED_ALPHA_V18_ENROLLMENT_SHA256 = (
    "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
)
EXPECTED_ALPHA_V18_IDENTITY_SHA256 = (
    "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66"
)
EXPECTED_ALPHA_V18_PROMOTION_NAMES_SHA256 = (
    "5b6faad95b90a3b3f11e6aea929aefd3cdbf9b5a1f3563e57d8e48f15e9d59e6"
)

_FLAGSHIP_MODULE_CONTRACTS: dict[str, tuple[str, str, str]] = {
    "lucas": ("lucas_complete_closure", "lucas_closure_plan", "LUCAS"),
    "kummer": (
        "kummer_complete_closure",
        "kummer_complete_closure_plan",
        "KUMMER",
    ),
    "bertrand": (
        "bertrand_complete_closure",
        "bertrand_complete_closure_plan",
        "BERTRAND",
    ),
    "four_square": (
        "four_square_complete_closure",
        "four_square_complete_closure_plan",
        "FOUR_SQUARE",
    ),
    "two_square": (
        "two_square_complete_closure",
        "two_square_closure_plan",
        "TWO_SQUARE",
    ),
}
FLAGSHIP_ARTIFACT_FILENAMES: dict[str, str] = {
    "lucas": "lucas-proof-bundle-v1.json",
    "kummer": "kummer-proof-bundle-v1.json",
    "bertrand": "bertrand-proof-bundle-v1.json",
    "four_square": "four-square-proof-bundle-v1.json",
    "two_square": "two-square-proof-bundle-v1.json",
}
PYODIDE_FLAGSHIP_BUNDLE_PATHS = {
    label: f"/lab/proof-artifacts/{filename}"
    for label, filename in FLAGSHIP_ARTIFACT_FILENAMES.items()
}


class EditionV18Error(ValueError):
    """The immutable parent, exact flagship closure, or release seal failed."""


class EditionV18ReplayError(EditionV18Error):
    """Checked use requires actual unchanged-kernel-accepted proof data."""


def dependency_depths(specs):
    return v17.dependency_depths(specs)


def dependency_layers(specs):
    return v17.dependency_layers(specs)


def _flagship_names(roots: tuple[str, ...]) -> tuple[str, ...]:
    selected: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        item = v17.ALPHA_EDITION.by_name.get(name)
        if item is None:
            raise EditionV18Error(
                f"flagship closure has an unknown immutable Alpha-v17 row {name!r}"
            )
        selected.add(name)
        pending.extend(item.spec.dependencies)
    return tuple(
        item.spec.name for item in v17.ALPHA_ENTRIES if item.spec.name in selected
    )


FLAGSHIP_BUNDLE_NAMES: dict[str, tuple[str, ...]] = {
    label: _flagship_names(FLAGSHIP_BUNDLE_ROOTS[label])
    for label in FLAGSHIP_BUNDLE_LABELS
}
_FLAGSHIP_BUNDLE_NAME_SETS = {
    label: frozenset(names) for label, names in FLAGSHIP_BUNDLE_NAMES.items()
}
_FLAGSHIP_BUNDLE_POSITIONS: dict[str, dict[str, int]] = {
    label: {name: index for index, name in enumerate(names)}
    for label, names in FLAGSHIP_BUNDLE_NAMES.items()
}
_FLAGSHIP_DEPENDENCY_SET = frozenset().union(*_FLAGSHIP_BUNDLE_NAME_SETS.values())
FLAGSHIP_DEPENDENCY_NAMES = tuple(
    item.spec.name
    for item in v17.ALPHA_ENTRIES
    if item.spec.name in _FLAGSHIP_DEPENDENCY_SET
)
FLAGSHIP_PROMOTED_NAMES = tuple(
    name
    for name in FLAGSHIP_DEPENDENCY_NAMES
    if not v17.ALPHA_EDITION.by_name[name].checked_use
)
_FLAGSHIP_PROMOTED_NAME_SET = frozenset(FLAGSHIP_PROMOTED_NAMES)
FLAGSHIP_PROMOTION_OWNERS: dict[str, str] = {
    name: next(
        label
        for label in FLAGSHIP_BUNDLE_LABELS
        if name in _FLAGSHIP_BUNDLE_NAME_SETS[label]
    )
    for name in FLAGSHIP_PROMOTED_NAMES
}

if (
    len(FLAGSHIP_DEPENDENCY_NAMES) != EXPECTED_ALPHA_V18_DEPENDENCY_CLOSURE_COUNT
    or len(FLAGSHIP_PROMOTED_NAMES) != EXPECTED_ALPHA_V18_PROMOTION_COUNT
    or sha256("\n".join(FLAGSHIP_PROMOTED_NAMES).encode("utf-8")).hexdigest()
    != EXPECTED_ALPHA_V18_PROMOTION_NAMES_SHA256
):
    raise EditionV18Error("Alpha-v18 exact flagship evidence-transition set changed")


ALPHA_ENTRIES: tuple[EditionEntry, ...] = tuple(
    replace(item, evidence=EvidenceStatus.ALPHA_CLOSED)
    if item.spec.name in _FLAGSHIP_PROMOTED_NAME_SET
    else item
    for item in v17.ALPHA_ENTRIES
)
ALPHA_SPECS: tuple[TheoremSpec, ...] = tuple(item.spec for item in ALPHA_ENTRIES)
ALPHA_CHECKED_SPECS: tuple[TheoremSpec, ...] = tuple(
    item.spec for item in ALPHA_ENTRIES if item.checked_use
)
STABLE_RELEASE_ORDER: tuple[str, ...] = v17.STABLE_RELEASE_ORDER
STABLE_ENTRIES: tuple[EditionEntry, ...] = v17.STABLE_ENTRIES
STABLE_SPECS: tuple[TheoremSpec, ...] = v17.STABLE_SPECS
STABLE_EDITION = v17.STABLE_EDITION
ALPHA_EDITION = _make_edition(EditionName.ALPHA, ALPHA_ENTRIES)
ALPHA_V18_ENROLLMENT_SHA256 = ALPHA_EDITION.enrollment_identity_sha256
ALPHA_V18_IDENTITY_SHA256 = ALPHA_EDITION.identity_sha256
ALPHA_ENROLLMENT_SHA256 = ALPHA_V18_ENROLLMENT_SHA256


def _validate_seals() -> None:
    if (
        len(ALPHA_ENTRIES) != EXPECTED_ALPHA_V18_COUNT
        or len(ALPHA_ENTRIES) != len(v17.ALPHA_ENTRIES)
        or ALPHA_SPECS != v17.ALPHA_SPECS
    ):
        raise EditionV18Error("Alpha-v18 changed its immutable v17 theorem ledger")
    if (
        STABLE_EDITION is not v17.STABLE_EDITION
        or STABLE_ENTRIES is not v17.STABLE_ENTRIES
        or STABLE_SPECS is not v17.STABLE_SPECS
        or len(STABLE_SPECS) != 432
    ):
        raise EditionV18Error("Alpha-v18 changed the immutable Stable edition")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_ALPHA_V18_EDGE_COUNT,
        EXPECTED_ALPHA_V18_LAYER_COUNT,
    ):
        raise EditionV18Error("Alpha-v18 changed its immutable dependency topology")
    if (
        ALPHA_V18_ENROLLMENT_SHA256 != EXPECTED_ALPHA_V18_ENROLLMENT_SHA256
        or ALPHA_V18_ENROLLMENT_SHA256 != v17.ALPHA_V17_ENROLLMENT_SHA256
        or _enrollment_identity(ALPHA_ENTRIES)
        != _enrollment_identity(v17.ALPHA_ENTRIES)
    ):
        raise EditionV18Error("Alpha-v18 changed its immutable enrollment identity")
    if (
        ALPHA_V18_IDENTITY_SHA256 != EXPECTED_ALPHA_V18_IDENTITY_SHA256
        or _identity(EditionName.ALPHA, ALPHA_ENTRIES)
        != EXPECTED_ALPHA_V18_IDENTITY_SHA256
    ):
        raise EditionV18Error("Alpha-v18 promoted-evidence identity changed")
    if Counter(item.evidence for item in ALPHA_ENTRIES) != {
        EvidenceStatus.STABLE_CLOSED: 432,
        EvidenceStatus.ALPHA_CLOSED: 1_157,
        EvidenceStatus.BODY_CHECKED: 84,
    }:
        raise EditionV18Error("Alpha-v18 promoted evidence partition changed")
    if Counter(item.membership for item in ALPHA_ENTRIES) != {
        Membership.STABLE: 432,
        Membership.ALPHA_ONLY: 1_241,
    }:
        raise EditionV18Error("Alpha-v18 changed immutable release membership")
    if len(ALPHA_CHECKED_SPECS) != EXPECTED_ALPHA_V18_CHECKED_USE_COUNT:
        raise EditionV18Error("Alpha-v18 checked-use evidence count changed")
    checked = {item.name for item in ALPHA_CHECKED_SPECS}
    if (
        sum(len(item.dependencies) for item in ALPHA_CHECKED_SPECS)
        != EXPECTED_ALPHA_V18_CHECKED_EDGE_COUNT
    ):
        raise EditionV18Error("Alpha-v18 checked-use dependency edge count changed")
    for spec in ALPHA_CHECKED_SPECS:
        missing = set(spec.dependencies).difference(checked)
        if missing:
            raise EditionV18Error(
                f"Alpha-v18 checked theorem {spec.name!r} has unchecked "
                f"prerequisites {sorted(missing)!r}"
            )
    for older, newer in zip(v17.ALPHA_ENTRIES, ALPHA_ENTRIES, strict=True):
        if newer.spec.name in _FLAGSHIP_PROMOTED_NAME_SET:
            if (
                older.checked_use
                or older.evidence is not EvidenceStatus.BODY_CHECKED
                or older.membership is not Membership.ALPHA_ONLY
                or newer != replace(older, evidence=EvidenceStatus.ALPHA_CLOSED)
            ):
                raise EditionV18Error(
                    f"invalid flagship evidence transition for {newer.spec.name!r}"
                )
        elif newer is not older:
            raise EditionV18Error(
                f"Alpha-v18 mutated unrelated parent row {older.spec.name!r}"
            )
    if Counter(FLAGSHIP_PROMOTION_OWNERS.values()) != {
        "lucas": 74,
        "kummer": 73,
        "bertrand": 241,
        "four_square": 196,
        "two_square": 89,
    }:
        raise EditionV18Error("Alpha-v18 exact flagship proof-owner precedence changed")
    for name in FLAGSHIP_ROOT_NAMES:
        if ALPHA_EDITION.by_name[name].evidence is not EvidenceStatus.ALPHA_CLOSED:
            raise EditionV18Error(f"Alpha-v18 flagship root {name!r} is not closed")


_validate_seals()

_flagship_bundle_sources: dict[str, Path] = {}


def _coerce_flagship_label(label: str) -> str:
    if type(label) is not str or label not in FLAGSHIP_BUNDLE_LABELS:
        raise EditionV18ReplayError(f"unknown exact Alpha-v18 proof family {label!r}")
    return label


def _default_flagship_bundle_source(label: str) -> Path:
    pyodide = Path(PYODIDE_FLAGSHIP_BUNDLE_PATHS[label])
    if pyodide.is_file():
        return pyodide
    location = Path(__file__).resolve()
    if len(location.parents) > 4:
        return (
            location.parents[4]
            / "research"
            / "arithmetic-library"
            / "artifacts"
            / FLAGSHIP_ARTIFACT_FILENAMES[label]
        )
    return pyodide


def set_flagship_bundle_source(label: str, source: str | Path | None) -> None:
    """Replace one actual-proof source and invalidate every checked-use cache."""

    selected = _coerce_flagship_label(label)
    if source is not None and not isinstance(source, (str, Path)):
        raise EditionV18ReplayError("flagship proof source must be a filesystem path")
    if source is None:
        _flagship_bundle_sources.pop(selected, None)
    else:
        _flagship_bundle_sources[selected] = Path(source)
    _checked_flagship_bundle.cache_clear()
    replay.cache_clear()


def _flagship_module(label: str) -> ModuleType:
    module_name, _plan_name, _prefix = _FLAGSHIP_MODULE_CONTRACTS[label]
    try:
        return import_module(f".{module_name}", package=__package__)
    except (ImportError, OSError, RecursionError, TypeError, ValueError) as exc:
        raise EditionV18ReplayError(
            f"actual Alpha-v18 {label} proof provider is unavailable or invalid"
        ) from exc


@lru_cache(maxsize=len(FLAGSHIP_BUNDLE_LABELS))
def _checked_flagship_bundle(
    label: str,
) -> tuple[ProofBundle, CheckedProofBundle, dict[str, int]]:
    """Load one exact immutable bundle and check every genuine proof body."""

    selected = _coerce_flagship_label(label)
    module = _flagship_module(selected)
    _module_name, plan_name, prefix = _FLAGSHIP_MODULE_CONTRACTS[selected]
    source = _flagship_bundle_sources.get(selected) or _default_flagship_bundle_source(
        selected
    )
    try:
        payload = source.read_text(encoding="utf-8")
        expected_bytes = getattr(module, f"EXPECTED_{prefix}_BUNDLE_BYTES")
        expected_sha256 = getattr(module, f"EXPECTED_{prefix}_BUNDLE_SHA256")
        expected_body_nodes = getattr(module, f"EXPECTED_{prefix}_BUNDLE_BODY_PROOF_NODES")
    except (AttributeError, OSError, UnicodeError) as exc:
        raise EditionV18ReplayError(
            f"actual Alpha-v18 {selected} proof data or frozen provenance "
            f"are unavailable: {source!s}"
        ) from exc
    data = payload.encode("utf-8")
    if len(data) != expected_bytes or sha256(data).hexdigest() != expected_sha256:
        raise EditionV18ReplayError(
            f"Alpha-v18 {selected} proof artifact differs from frozen genuine provenance"
        )
    try:
        plan = getattr(module, plan_name)()
        if selected == "kummer":
            actual = module.load_kummer_proof_bundle(source)
            bundle, receipt = actual.bundle, actual.receipt
        elif selected in _flagship_bundle_sources:
            bundle, target = decode_proof_bundle(payload)
            actual = getattr(module, f"check_{selected}_proof_bundle")(bundle, target)
            bundle, receipt = actual.bundle, actual.receipt
        else:
            bundle, receipt = getattr(module, f"checked_{selected}_proof_bundle")()
    except (
        AttributeError,
        OSError,
        ProofBundleError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise EditionV18ReplayError(
            f"the unchanged intuitionistic kernel rejected actual Alpha-v18 "
            f"{selected} proof evidence"
        ) from exc

    expected_names = FLAGSHIP_BUNDLE_NAMES[selected]
    positions = _FLAGSHIP_BUNDLE_POSITIONS[selected]
    synthetic_count = int(selected == "kummer")
    if (
        tuple(row.name for row in plan.rows) != expected_names
        or type(bundle) is not ProofBundle
        or len(bundle.nodes) != len(expected_names) + synthetic_count
        or bundle.root != len(bundle.nodes) - 1
        or receipt.node_count != len(bundle.nodes)
        or receipt.kernel_calls != len(bundle.nodes)
        or receipt.total_body_nodes != expected_body_nodes
    ):
        raise EditionV18ReplayError(
            f"Alpha-v18 {selected} proof artifact changed its exact theorem graph"
        )
    for index, name in enumerate(expected_names):
        node = bundle.nodes[index]
        spec = v17.ALPHA_EDITION.by_name[name].spec
        if (
            type(node) is not BundleNode
            or node.node_id != index
            or node.target != _closed_formula(spec.statement)
            or node.dependencies
            != tuple(positions[dependency] for dependency in spec.dependencies)
        ):
            raise EditionV18ReplayError(
                f"Alpha-v18 {selected} artifact changed frozen theorem {name!r}"
            )
    roots = FLAGSHIP_BUNDLE_ROOTS[selected]
    if selected == "kummer":
        formulas = tuple(
            _closed_formula(v17.ALPHA_EDITION.by_name[name].spec.statement)
            for name in roots
        )
        synthetic = bundle.nodes[-1]
        if (
            synthetic.node_id != len(expected_names)
            or synthetic.target != And(formulas[0], formulas[1])
            or synthetic.dependencies != tuple(positions[name] for name in roots)
            or receipt.target != synthetic.target
        ):
            raise EditionV18ReplayError(
                "Alpha-v18 Kummer artifact changed its exact synthetic conjunction root"
            )
    elif (
        positions[roots[0]] != bundle.root
        or receipt.target
        != _closed_formula(v17.ALPHA_EDITION.by_name[roots[0]].spec.statement)
    ):
        raise EditionV18ReplayError(
            f"Alpha-v18 {selected} proof artifact changed its exact original root"
        )
    return bundle, receipt, dict(positions)


def checked_flagship_bundle(
    label: str,
) -> tuple[ProofBundle, CheckedProofBundle, dict[str, int], ModuleType]:
    """Return actual checked proofs, exact theorem locations and their provider."""

    selected = _coerce_flagship_label(label)
    bundle, receipt, positions = _checked_flagship_bundle(selected)
    return bundle, receipt, positions, _flagship_module(selected)


def _flagship_owner(name: str) -> str:
    if type(name) is not str or name not in FLAGSHIP_PROMOTION_OWNERS:
        raise EditionV18ReplayError(
            f"theorem {name!r} has no newly promoted Alpha-v18 proof owner"
        )
    return FLAGSHIP_PROMOTION_OWNERS[name]


def promotion_owner(name: str) -> str:
    """Select the first exact independently checked bundle owning a promotion."""

    return _flagship_owner(name)


def _coerce_edition(value: EditionName | str) -> EditionName:
    if isinstance(value, EditionName):
        return value
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for candidate in EditionName:
            if candidate.value == wanted:
                return candidate
    raise EditionV18Error(f"unknown theorem-library v18 edition {value!r}")


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


def _replay_promoted_flagship(item: EditionEntry) -> CheckedTheorem:
    owner = _flagship_owner(item.spec.name)
    bundle, _receipt, positions = _checked_flagship_bundle(owner)
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
            LayeredReplayNode(node.node_id, node.target, node.dependencies, node.body)
            for node in bundle.nodes
            if node.node_id in selected
        ),
        root_id,
    )
    formula = _closed_formula(item.spec.statement)
    if owner == "bertrand":
        # The complete 544-node original Bertrand closure has 187,725 encoded
        # proof-body constructors.  Conservative structural hash-consing
        # reduces its actual ordinary root to 45,254 proof objects, safely
        # below the unchanged 100,000-object limit.  The prepass creates no
        # logical evidence: retain the exact frozen graph and independently
        # recheck every interned dependency-curried body in the original
        # intuitionistic kernel before compiling and checking the root.
        interned = intern_layered_replay_bodies(
            layered,
            formula,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
        if (
            interned is None
            or interned.root != layered.root
            or len(interned.nodes) != len(layered.nodes)
        ):
            raise EditionV18ReplayError(
                f"Alpha-v18 theorem {item.spec.name!r} rejected conservative "
                "proof-body interning under the unchanged resource policy"
            )
        for original, actual in zip(layered.nodes, interned.nodes, strict=True):
            if (
                actual.node_id != original.node_id
                or actual.target != original.target
                or actual.dependencies != original.dependencies
            ):
                raise EditionV18ReplayError(
                    "Alpha-v18 Bertrand proof interning changed its exact "
                    f"frozen theorem graph at node {original.node_id}"
                )
            curried = actual.target
            for dependency in reversed(actual.dependencies):
                curried = Imp(bundle.nodes[dependency].target, curried)
            if not check((), actual.body, curried):
                raise EditionV18ReplayError(
                    "the unchanged intuitionistic kernel rejected an "
                    f"interned Alpha-v18 Bertrand proof body {actual.node_id}"
                )
        layered = interned
    candidate = compile_layered_replay(
        layered,
        formula,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    if candidate is None:
        raise EditionV18ReplayError(
            f"Alpha-v18 theorem {item.spec.name!r} exceeds the unchanged "
            "layered proof/resource policy"
        )
    if not check((), candidate.certificate, formula):
        raise EditionV18ReplayError(
            f"the unchanged intuitionistic kernel rejected promoted Alpha-v18 "
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
        raise EditionV18ReplayError(f"unknown {selected.value} v18 theorem {name!r}")
    if not item.checked_use:
        raise EditionV18ReplayError(
            f"{selected.value} v18 theorem {item.spec.name!r} has evidence "
            f"{item.evidence.value!r}; checked theorem use requires "
            "stable_closed or alpha_closed"
        )
    if item.spec.name not in _FLAGSHIP_PROMOTED_NAME_SET:
        return v17.replay(item.spec.name, edition=selected)
    if selected is not EditionName.ALPHA:
        raise EditionV18ReplayError(
            f"promoted flagship theorem {item.spec.name!r} is not in Stable"
        )
    return _replay_promoted_flagship(item)


__all__ = [
    "ALPHA_CHECKED_SPECS",
    "ALPHA_EDITION",
    "ALPHA_ENROLLMENT_SHA256",
    "ALPHA_ENTRIES",
    "ALPHA_SPECS",
    "ALPHA_V18_ENROLLMENT_SHA256",
    "ALPHA_V18_IDENTITY_SHA256",
    "EditionEntry",
    "EditionName",
    "EditionV18Error",
    "EditionV18ReplayError",
    "EnrollmentOrigin",
    "EvidenceStatus",
    "EXPECTED_ALPHA_V18_CHECKED_EDGE_COUNT",
    "EXPECTED_ALPHA_V18_CHECKED_USE_COUNT",
    "EXPECTED_ALPHA_V18_COUNT",
    "EXPECTED_ALPHA_V18_DEPENDENCY_CLOSURE_COUNT",
    "EXPECTED_ALPHA_V18_EDGE_COUNT",
    "EXPECTED_ALPHA_V18_ENROLLMENT_SHA256",
    "EXPECTED_ALPHA_V18_IDENTITY_SHA256",
    "EXPECTED_ALPHA_V18_LAYER_COUNT",
    "EXPECTED_ALPHA_V18_PROMOTION_COUNT",
    "EXPECTED_ALPHA_V18_PROMOTION_NAMES_SHA256",
    "FLAGSHIP_ARTIFACT_FILENAMES",
    "FLAGSHIP_BUNDLE_LABELS",
    "FLAGSHIP_BUNDLE_NAMES",
    "FLAGSHIP_BUNDLE_ROOTS",
    "FLAGSHIP_DEPENDENCY_NAMES",
    "FLAGSHIP_PROMOTED_NAMES",
    "FLAGSHIP_PROMOTION_OWNERS",
    "FLAGSHIP_ROOT_NAMES",
    "LibraryEdition",
    "Membership",
    "PYODIDE_FLAGSHIP_BUNDLE_PATHS",
    "STABLE_EDITION",
    "STABLE_ENTRIES",
    "STABLE_RELEASE_ORDER",
    "STABLE_SPECS",
    "checked_flagship_bundle",
    "dependency_depths",
    "dependency_layers",
    "edition",
    "entry",
    "promotion_owner",
    "replay",
    "set_flagship_bundle_source",
]
