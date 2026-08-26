"""Exact Alpha-v15 supplementary-law and two-square body enrollment.

The immutable Alpha-v14 prefix acquires exactly 117 dependency-curried proof
bodies: both authentic bounded Euler/Gauss prerequisites, the complete two
quadratic supplementary laws, and the complete all-natural two-square iff.
Membership grants neither checked theorem use nor empty-context closure.
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

from .editions_v14 import (
    ALPHA_ENTRIES as ALPHA_V14_ENTRIES,
    ALPHA_V14_ENROLLMENT_SHA256,
    ALPHA_V14_IDENTITY_SHA256,
    EditionEntry as EditionEntryV14,
)
from .theorems import TheoremSpec


class AlphaV15EnrollmentError(ValueError):
    """The sealed v14 parent or minimal supplementary closure is invalid."""


class FrontierV15Campaign(str, Enum):
    SUPPLEMENTARY = "supplementary"
    TWO_SQUARE = "two_square"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV15:
    campaign: FrontierV15Campaign
    module: str
    factory: str
    test_path: str
    rfc_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV15Enrollment:
    parent_entries: tuple[EditionEntryV14, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV15Campaign]

    @property
    def supplementary_specs(self) -> tuple[TheoremSpec, ...]:
        return self.frontier_specs[:SUPPLEMENTARY_V15_EXPECTED_COUNT]

    @property
    def two_square_specs(self) -> tuple[TheoremSpec, ...]:
        return self.frontier_specs[SUPPLEMENTARY_V15_EXPECTED_COUNT:]


PARENT_ALPHA_V14_COUNT = 1_556
PARENT_ALPHA_V14_ENROLLMENT_SHA256 = (
    "d7758c5cfcce4fbe2b48b6b213b134acf9126b84a58a0016c523055be952024e"
)
PARENT_ALPHA_V14_IDENTITY_SHA256 = (
    "06274ac80612403f6851266fa00f8b543d904072434d5717ca95ae7d40588c16"
)
FRONTIER_V15_START_INDEX = PARENT_ALPHA_V14_COUNT
SUPPLEMENTARY_V15_EXPECTED_COUNT = 28
TWO_SQUARE_V15_EXPECTED_COUNT = 89
FRONTIER_V15_EXPECTED_COUNT = 117
FRONTIER_V15_ROOT_NAMES = (
    "quadratic_supplement_minus_one_complete",
    "quadratic_supplement_two_complete",
    "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
)
FRONTIER_V15_ROOT_STATEMENT_SHA256 = MappingProxyType(
    {
        "quadratic_supplement_minus_one_complete": (
            "7ea81062b843e7fff4939ffce5b6fa14a87312619f7f49e3abd5993bfa02134e"
        ),
        "quadratic_supplement_two_complete": (
            "146a886f8f3a54d358321b54faf68a591362016e86139bd487a5496c7af74034"
        ),
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations": (
            "4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5"
        ),
    }
)
FRONTIER_V15_EXPECTED_NAMES_SHA256 = (
    "0f351efe479507534d2cf8cca1b9bb82fe1a7eb6149a3c06224f0e9b42f93318"
)
FRONTIER_V15_SORTED_NAMES_SHA256 = (
    "32756c7da2db95fcb2948d53f79b74b0c22830b3bd3d5cb284228edfe7f54dbb"
)


_SOURCE_MODULES: tuple[tuple[FrontierV15Campaign, str], ...] = (
    (FrontierV15Campaign.SUPPLEMENTARY, "euler_criterion_bounded_candidate"),
    (FrontierV15Campaign.SUPPLEMENTARY, "quadratic_supplement_minus_one_candidate"),
    (FrontierV15Campaign.SUPPLEMENTARY, "gauss_lemma_bounded_candidate"),
    (FrontierV15Campaign.SUPPLEMENTARY, "quadratic_supplement_two_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_classification_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_collision_norm_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_factor_fold_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_pairing_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_pigeonhole_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_prime_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_residue_grid_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "fermat_two_squares_valuation_candidate"),
    (FrontierV15Campaign.TWO_SQUARE, "finite_prefix_collision_decision_candidate"),
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
        "euler_criterion_bounded_candidate": "euler-scaled-inverse.md",
        "gauss_lemma_bounded_candidate": "gauss-magnitude-permutation.md",
        "quadratic_supplement_minus_one_candidate": (
            "ha-quadratic-supplementary-laws-rfc-v1.md"
        ),
        "quadratic_supplement_two_candidate": (
            "ha-quadratic-supplementary-laws-rfc-v1.md"
        ),
        "fermat_two_squares_candidate": "fermat-two-squares-foundations-rfc-v1.md",
    }
    filename = special.get(
        module, f"{module.removesuffix('_candidate').replace('_', '-')}-rfc-v1.md"
    )
    return f"research/arithmetic-library/{filename}"


@lru_cache(maxsize=1)
def _factory_inventory() -> tuple[
    Mapping[str, TheoremSpec],
    Mapping[str, str],
    Mapping[str, FrontierV15Campaign],
]:
    specs: dict[str, TheoremSpec] = {}
    modules: dict[str, str] = {}
    campaigns: dict[str, FrontierV15Campaign] = {}
    for campaign, module_name in _SOURCE_MODULES:
        module = import_module(f"peano_lab.library.{module_name}")
        factory_name = (
            f"make_{module_name.removesuffix('_candidate')}_candidate_theorems"
        )
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            raise AlphaV15EnrollmentError(
                f"missing Alpha-v15 source factory {module_name}.{factory_name}"
            )
        for spec in factory(TheoremSpec):
            previous = specs.get(spec.name)
            if previous is not None and previous != spec:
                raise AlphaV15EnrollmentError(
                    f"conflicting Alpha-v15 source rows {spec.name!r}"
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
    if len(ALPHA_V14_ENTRIES) != PARENT_ALPHA_V14_COUNT:
        raise AlphaV15EnrollmentError("sealed Alpha-v14 parent count changed")
    if ALPHA_V14_ENROLLMENT_SHA256 != PARENT_ALPHA_V14_ENROLLMENT_SHA256:
        raise AlphaV15EnrollmentError("sealed Alpha-v14 enrollment identity changed")
    if ALPHA_V14_IDENTITY_SHA256 != PARENT_ALPHA_V14_IDENTITY_SHA256:
        raise AlphaV15EnrollmentError("sealed Alpha-v14 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V14_ENTRIES}
    candidates, _owners, campaigns = _factory_inventory()
    ordered: list[TheoremSpec] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in available or name in visited:
            return
        if name in visiting:
            raise AlphaV15EnrollmentError(f"cyclic Alpha-v15 dependency {name!r}")
        spec = candidates.get(name)
        if spec is None:
            raise AlphaV15EnrollmentError(
                f"missing Alpha-v15 transitive dependency {name!r}"
            )
        visiting.add(name)
        for dependency in spec.dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        ordered.append(spec)

    for root in FRONTIER_V15_ROOT_NAMES:
        visit(root)
        if root not in visited:
            raise AlphaV15EnrollmentError(f"Alpha-v15 root {root!r} already enrolled")
        actual = sha256(candidates[root].statement.encode("utf-8")).hexdigest()
        if actual != FRONTIER_V15_ROOT_STATEMENT_SHA256[root]:
            raise AlphaV15EnrollmentError(f"Alpha-v15 root statement changed: {root}")

    result = tuple(ordered)
    if len(result) != FRONTIER_V15_EXPECTED_COUNT:
        raise AlphaV15EnrollmentError(
            f"Alpha-v15 exact closure count changed: {len(result)}"
        )
    if (
        result[6].name != FRONTIER_V15_ROOT_NAMES[0]
        or result[SUPPLEMENTARY_V15_EXPECTED_COUNT - 1].name
        != FRONTIER_V15_ROOT_NAMES[1]
        or result[-1].name != FRONTIER_V15_ROOT_NAMES[2]
    ):
        raise AlphaV15EnrollmentError("Alpha-v15 root or campaign boundary changed")
    if any(
        campaigns[spec.name] is not FrontierV15Campaign.SUPPLEMENTARY
        for spec in result[:SUPPLEMENTARY_V15_EXPECTED_COUNT]
    ) or any(
        campaigns[spec.name] is not FrontierV15Campaign.TWO_SQUARE
        for spec in result[SUPPLEMENTARY_V15_EXPECTED_COUNT:]
    ):
        raise AlphaV15EnrollmentError("Alpha-v15 campaign closure boundary changed")
    actual_names = sha256(
        _compact(tuple(spec.name for spec in result)).encode("utf-8")
    ).hexdigest()
    if actual_names != FRONTIER_V15_EXPECTED_NAMES_SHA256:
        raise AlphaV15EnrollmentError(
            f"Alpha-v15 exact topological order changed: {actual_names}"
        )
    return result


def _source_manifest() -> tuple[EnrollmentSourceV15, ...]:
    _candidates, owners, _campaigns = _factory_inventory()
    source_names: dict[str, list[str]] = {
        module: [] for _campaign, module in _SOURCE_MODULES
    }
    for spec in _ordered_frontier():
        source_names[owners[spec.name]].append(spec.name)
    result: list[EnrollmentSourceV15] = []
    for campaign, module in _SOURCE_MODULES:
        names = tuple(source_names[module])
        if not names:
            raise AlphaV15EnrollmentError(f"empty Alpha-v15 source block {module!r}")
        result.append(
            EnrollmentSourceV15(
                campaign=campaign,
                module=module,
                factory=f"make_{module.removesuffix('_candidate')}_candidate_theorems",
                test_path=f"peano-lab/py/tests/test_{module}.py",
                rfc_path=_rfc_for_module(module),
                names=names,
            )
        )
    return tuple(result)


@lru_cache(maxsize=1)
def alpha_v15_enrollment() -> AlphaV15Enrollment:
    ordered = _ordered_frontier()
    _candidates, owners, campaigns = _factory_inventory()
    manifest = _source_manifest()
    by_module = {source.module: source for source in manifest}
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    campaign_by_name: dict[str, FrontierV15Campaign] = {}
    available = {entry.spec.name for entry in ALPHA_V14_ENTRIES}
    for spec in ordered:
        if spec.name in available:
            raise AlphaV15EnrollmentError(f"duplicate Alpha-v15 row {spec.name!r}")
        missing = set(spec.dependencies) - available
        if missing:
            raise AlphaV15EnrollmentError(
                f"forward Alpha-v15 dependencies for {spec.name!r}: {sorted(missing)!r}"
            )
        if any("DNE" in command for command in spec.script):
            raise AlphaV15EnrollmentError(
                f"Alpha-v15 constructive theorem contains DNE: {spec.name!r}"
            )
        source = by_module[owners[spec.name]]
        source_by_name[spec.name] = f"peano-lab/py/peano_lab/library/{source.module}.py"
        test_by_name[spec.name] = source.test_path
        rfc_by_name[spec.name] = source.rfc_path
        campaign_by_name[spec.name] = campaigns[spec.name]
        available.add(spec.name)
    return AlphaV15Enrollment(
        parent_entries=ALPHA_V14_ENTRIES,
        frontier_specs=ordered,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        campaign_by_name=MappingProxyType(campaign_by_name),
    )


FRONTIER_V15_EXPECTED_NAMES = tuple(spec.name for spec in _ordered_frontier())
FRONTIER_V15_BODY_ENROLLMENT_MANIFEST = _source_manifest()
FRONTIER_V15_EXPECTED_SOURCE_COUNTS = tuple(
    len(source.names) for source in FRONTIER_V15_BODY_ENROLLMENT_MANIFEST
)
FRONTIER_V15_RFC_PATHS = tuple(
    dict.fromkeys(source.rfc_path for source in FRONTIER_V15_BODY_ENROLLMENT_MANIFEST)
)


__all__ = [
    "AlphaV15Enrollment",
    "AlphaV15EnrollmentError",
    "EnrollmentSourceV15",
    "FRONTIER_V15_BODY_ENROLLMENT_MANIFEST",
    "FRONTIER_V15_EXPECTED_COUNT",
    "FRONTIER_V15_EXPECTED_NAMES",
    "FRONTIER_V15_EXPECTED_NAMES_SHA256",
    "FRONTIER_V15_EXPECTED_SOURCE_COUNTS",
    "FRONTIER_V15_RFC_PATHS",
    "FRONTIER_V15_ROOT_NAMES",
    "FRONTIER_V15_ROOT_STATEMENT_SHA256",
    "FRONTIER_V15_SORTED_NAMES_SHA256",
    "FRONTIER_V15_START_INDEX",
    "FrontierV15Campaign",
    "PARENT_ALPHA_V14_COUNT",
    "PARENT_ALPHA_V14_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V14_IDENTITY_SHA256",
    "SUPPLEMENTARY_V15_EXPECTED_COUNT",
    "TWO_SQUARE_V15_EXPECTED_COUNT",
    "alpha_v15_enrollment",
]
