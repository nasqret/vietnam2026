"""Minimal, sealed Alpha-v13 enrollment of complete Lagrange and Lucas proofs.

The 1,303 Alpha-v12 entries remain an immutable prefix.  Exactly the missing
transitive dependency closures of ``four_square_lagrange`` and
``lucas_theorem`` are appended: 196 four-square rows and 44 Lucas rows.
Enrollment records independently kernel-checkable dependency-curried bodies;
it grants no empty-context closure authority or checked theorem use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from types import MappingProxyType
from typing import Mapping

from .editions_v12 import (
    ALPHA_ENTRIES as ALPHA_V12_ENTRIES,
    ALPHA_V12_ENROLLMENT_SHA256,
    ALPHA_V12_IDENTITY_SHA256,
    EditionEntry as EditionEntryV12,
)
from .theorems import TheoremSpec


class AlphaV13EnrollmentError(ValueError):
    """The frozen Alpha-v12 parent or exact frontier closure is invalid."""


class FrontierV13Campaign(str, Enum):
    """Human-facing proof campaign; runtime enrollment origin remains HA."""

    FOUR_SQUARE = "four_square"
    LUCAS = "lucas"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV13:
    """One exact candidate factory and its source/test/RFC provenance."""

    campaign: FrontierV13Campaign
    module: str
    factory: str
    test_path: str
    rfc_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV13Enrollment:
    """Immutable v12 parent and exactly the two required proof closures."""

    parent_entries: tuple[EditionEntryV12, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV13Campaign]

    @property
    def four_square_specs(self) -> tuple[TheoremSpec, ...]:
        return self.frontier_specs[:FOUR_SQUARE_V13_EXPECTED_COUNT]

    @property
    def lucas_specs(self) -> tuple[TheoremSpec, ...]:
        return self.frontier_specs[FOUR_SQUARE_V13_EXPECTED_COUNT:]


PARENT_ALPHA_V12_COUNT = 1_303
PARENT_ALPHA_V12_ENROLLMENT_SHA256 = (
    "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b"
)
PARENT_ALPHA_V12_IDENTITY_SHA256 = (
    "bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061"
)
FRONTIER_V13_ROOT_NAMES = ("four_square_lagrange", "lucas_theorem")
FRONTIER_V13_ROOT_STATEMENT_SHA256 = MappingProxyType(
    {
        "four_square_lagrange": (
            "fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5"
        ),
        "lucas_theorem": (
            "396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564"
        ),
    }
)
FRONTIER_V13_START_INDEX = PARENT_ALPHA_V12_COUNT
FOUR_SQUARE_V13_EXPECTED_COUNT = 196
LUCAS_V13_EXPECTED_COUNT = 44
FRONTIER_V13_EXPECTED_COUNT = (
    FOUR_SQUARE_V13_EXPECTED_COUNT + LUCAS_V13_EXPECTED_COUNT
)
FRONTIER_V13_EXPECTED_NAMES_SHA256 = (
    "333c10386d23959fa397e763e236daeadaae0d438a00489b0b089aeb8a4b0148"
)

_SOURCE_MODULES: tuple[tuple[FrontierV13Campaign, str], ...] = (
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_branch_descent_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_parity_selection_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_descent_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_identity_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_euler_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "fermat_two_squares_classification_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_signed_quaternion_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "fermat_two_squares_collision_norm_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_residue_intersection_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_cross_pigeonhole_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "finite_prefix_collision_decision_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "fermat_two_squares_pigeonhole_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_bounded_seed_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_lagrange_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_lagrange_bridge_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_lagrange_final_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_signed_cases_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_signed_orientation_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_conjugate_identity_candidate"),
    (FrontierV13Campaign.FOUR_SQUARE, "four_square_signed_block_negative_candidate"),
    (FrontierV13Campaign.LUCAS, "lucas_multidigit_candidate"),
    (FrontierV13Campaign.LUCAS, "lucas_convolution_candidate"),
    (FrontierV13Campaign.LUCAS, "lucas_low_digit_candidate"),
    (FrontierV13Campaign.LUCAS, "lucas_digit_candidate"),
    (FrontierV13Campaign.LUCAS, "lucas_block_digit_candidate"),
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _rfc_for_module(module: str) -> str:
    special = {
        "four_square_identity_candidate": "four-square-identity-foundations-rfc-v1.md",
        "lucas_digit_candidate": "lucas-digit-foundations-rfc-v1.md",
    }
    filename = special.get(
        module, f"{module.removesuffix('_candidate').replace('_', '-')}-rfc-v1.md"
    )
    return f"research/arithmetic-library/{filename}"


@lru_cache(maxsize=1)
def _factory_inventory() -> tuple[
    Mapping[str, TheoremSpec],
    Mapping[str, str],
    Mapping[str, FrontierV13Campaign],
]:
    specs: dict[str, TheoremSpec] = {}
    modules: dict[str, str] = {}
    campaigns: dict[str, FrontierV13Campaign] = {}
    for campaign, module_name in _SOURCE_MODULES:
        module = import_module(f"peano_lab.library.{module_name}")
        factory_name = (
            f"make_{module_name.removesuffix('_candidate')}_candidate_theorems"
        )
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            raise AlphaV13EnrollmentError(
                f"missing Alpha-v13 source factory {module_name}.{factory_name}"
            )
        for spec in factory(TheoremSpec):
            previous = specs.get(spec.name)
            if previous is not None and previous != spec:
                raise AlphaV13EnrollmentError(
                    f"conflicting Alpha-v13 theorem factory rows {spec.name!r}"
                )
            if previous is None:
                specs[spec.name] = spec
                modules[spec.name] = module_name
                campaigns[spec.name] = campaign
    return (
        MappingProxyType(specs),
        MappingProxyType(modules),
        MappingProxyType(campaigns),
    )


@lru_cache(maxsize=1)
def _ordered_frontier() -> tuple[TheoremSpec, ...]:
    if len(ALPHA_V12_ENTRIES) != PARENT_ALPHA_V12_COUNT:
        raise AlphaV13EnrollmentError("sealed Alpha-v12 parent count changed")
    if ALPHA_V12_ENROLLMENT_SHA256 != PARENT_ALPHA_V12_ENROLLMENT_SHA256:
        raise AlphaV13EnrollmentError("sealed Alpha-v12 enrollment identity changed")
    if ALPHA_V12_IDENTITY_SHA256 != PARENT_ALPHA_V12_IDENTITY_SHA256:
        raise AlphaV13EnrollmentError("sealed Alpha-v12 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V12_ENTRIES}
    candidates, _owners, campaigns = _factory_inventory()
    ordered: list[TheoremSpec] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in available or name in visited:
            return
        if name in visiting:
            raise AlphaV13EnrollmentError(f"cyclic Alpha-v13 dependency {name!r}")
        spec = candidates.get(name)
        if spec is None:
            raise AlphaV13EnrollmentError(
                f"missing Alpha-v13 transitive dependency {name!r}"
            )
        visiting.add(name)
        for dependency in spec.dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        ordered.append(spec)

    for root in FRONTIER_V13_ROOT_NAMES:
        visit(root)
        if root not in visited:
            raise AlphaV13EnrollmentError(f"Alpha-v13 root {root!r} was already enrolled")
        expected = FRONTIER_V13_ROOT_STATEMENT_SHA256[root]
        actual = sha256(candidates[root].statement.encode("utf-8")).hexdigest()
        if actual != expected:
            raise AlphaV13EnrollmentError(f"Alpha-v13 root statement changed: {root!r}")

    result = tuple(ordered)
    if len(result) != FRONTIER_V13_EXPECTED_COUNT:
        raise AlphaV13EnrollmentError(
            f"Alpha-v13 closure count changed: {len(result)} != "
            f"{FRONTIER_V13_EXPECTED_COUNT}"
        )
    if result[FOUR_SQUARE_V13_EXPECTED_COUNT - 1].name != "four_square_lagrange":
        raise AlphaV13EnrollmentError("Alpha-v13 four-square root boundary changed")
    if result[-1].name != "lucas_theorem":
        raise AlphaV13EnrollmentError("Alpha-v13 Lucas root boundary changed")
    if any(
        campaigns[spec.name] is not FrontierV13Campaign.FOUR_SQUARE
        for spec in result[:FOUR_SQUARE_V13_EXPECTED_COUNT]
    ) or any(
        campaigns[spec.name] is not FrontierV13Campaign.LUCAS
        for spec in result[FOUR_SQUARE_V13_EXPECTED_COUNT:]
    ):
        raise AlphaV13EnrollmentError("Alpha-v13 campaign dependency closures overlap")
    actual_names_root = sha256(
        _compact(tuple(spec.name for spec in result)).encode("utf-8")
    ).hexdigest()
    if actual_names_root != FRONTIER_V13_EXPECTED_NAMES_SHA256:
        raise AlphaV13EnrollmentError(
            "Alpha-v13 exact dependency-topological order changed: "
            f"{actual_names_root}"
        )
    return result


FRONTIER_V13_EXPECTED_NAMES: tuple[str, ...] = tuple(
    spec.name for spec in _ordered_frontier()
)
FOUR_SQUARE_V13_EXPECTED_NAMES = FRONTIER_V13_EXPECTED_NAMES[
    :FOUR_SQUARE_V13_EXPECTED_COUNT
]
LUCAS_V13_EXPECTED_NAMES = FRONTIER_V13_EXPECTED_NAMES[
    FOUR_SQUARE_V13_EXPECTED_COUNT:
]


def _source_manifest() -> tuple[EnrollmentSourceV13, ...]:
    _candidates, owners, _campaigns = _factory_inventory()
    source_names: dict[str, list[str]] = {
        module: [] for _campaign, module in _SOURCE_MODULES
    }
    for spec in _ordered_frontier():
        source_names[owners[spec.name]].append(spec.name)
    result: list[EnrollmentSourceV13] = []
    for campaign, module in _SOURCE_MODULES:
        names = tuple(source_names[module])
        if not names:
            raise AlphaV13EnrollmentError(f"empty Alpha-v13 source block {module!r}")
        result.append(
            EnrollmentSourceV13(
                campaign=campaign,
                module=module,
                factory=f"make_{module.removesuffix('_candidate')}_candidate_theorems",
                test_path=f"peano-lab/py/tests/test_{module}.py",
                rfc_path=_rfc_for_module(module),
                names=names,
            )
        )
    return tuple(result)


FRONTIER_V13_BODY_ENROLLMENT_MANIFEST = _source_manifest()
FRONTIER_V13_EXPECTED_SOURCE_COUNTS = tuple(
    len(source.names) for source in FRONTIER_V13_BODY_ENROLLMENT_MANIFEST
)
FRONTIER_V13_RFC_PATHS = tuple(
    dict.fromkeys(source.rfc_path for source in FRONTIER_V13_BODY_ENROLLMENT_MANIFEST)
)


@lru_cache(maxsize=1)
def alpha_v13_enrollment() -> AlphaV13Enrollment:
    """Return the sealed, exact, dependency-topological Alpha-v13 append."""

    ordered = _ordered_frontier()
    _candidates, owners, campaigns = _factory_inventory()
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    campaign_by_name: dict[str, FrontierV13Campaign] = {}
    source_by_module = {
        source.module: source for source in FRONTIER_V13_BODY_ENROLLMENT_MANIFEST
    }
    available = {entry.spec.name for entry in ALPHA_V12_ENTRIES}
    for spec in ordered:
        if spec.name in available:
            raise AlphaV13EnrollmentError(f"duplicate Alpha-v13 row {spec.name!r}")
        missing = set(spec.dependencies) - available
        if missing:
            raise AlphaV13EnrollmentError(
                f"forward Alpha-v13 dependencies for {spec.name!r}: {sorted(missing)!r}"
            )
        if any("DNE" in command for command in spec.script):
            raise AlphaV13EnrollmentError(
                f"Alpha-v13 constructive theorem contains DNE: {spec.name!r}"
            )
        source = source_by_module[owners[spec.name]]
        source_by_name[spec.name] = f"peano-lab/py/peano_lab/library/{source.module}.py"
        test_by_name[spec.name] = source.test_path
        rfc_by_name[spec.name] = source.rfc_path
        campaign_by_name[spec.name] = campaigns[spec.name]
        available.add(spec.name)
    return AlphaV13Enrollment(
        parent_entries=ALPHA_V12_ENTRIES,
        frontier_specs=ordered,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        campaign_by_name=MappingProxyType(campaign_by_name),
    )


__all__ = [
    "AlphaV13Enrollment",
    "AlphaV13EnrollmentError",
    "EnrollmentSourceV13",
    "FOUR_SQUARE_V13_EXPECTED_COUNT",
    "FOUR_SQUARE_V13_EXPECTED_NAMES",
    "FRONTIER_V13_BODY_ENROLLMENT_MANIFEST",
    "FRONTIER_V13_EXPECTED_COUNT",
    "FRONTIER_V13_EXPECTED_NAMES",
    "FRONTIER_V13_EXPECTED_NAMES_SHA256",
    "FRONTIER_V13_EXPECTED_SOURCE_COUNTS",
    "FRONTIER_V13_RFC_PATHS",
    "FRONTIER_V13_ROOT_NAMES",
    "FRONTIER_V13_ROOT_STATEMENT_SHA256",
    "FRONTIER_V13_START_INDEX",
    "FrontierV13Campaign",
    "LUCAS_V13_EXPECTED_COUNT",
    "LUCAS_V13_EXPECTED_NAMES",
    "PARENT_ALPHA_V12_COUNT",
    "PARENT_ALPHA_V12_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V12_IDENTITY_SHA256",
    "alpha_v13_enrollment",
]
