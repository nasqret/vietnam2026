"""Exact, sealed Alpha-v14 admission of the constructive Kummer campaign.

The 1,543-row Alpha-v13 edition is an immutable parent.  Only the 13 missing
dependency-curried bodies required by the complete binomial carry theorem and
its carry-free divisibility criterion are appended.  Admission neither closes
an empty-context proof nor authorizes checked theorem use.
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

from .editions_v13 import (
    ALPHA_ENTRIES as ALPHA_V13_ENTRIES,
    ALPHA_V13_ENROLLMENT_SHA256,
    ALPHA_V13_IDENTITY_SHA256,
    EditionEntry as EditionEntryV13,
)
from .theorems import TheoremSpec


class AlphaV14EnrollmentError(ValueError):
    """The frozen Alpha-v13 parent or exact Kummer closure is invalid."""


class FrontierV14Campaign(str, Enum):
    """Human-facing campaign; runtime enrollment origin remains HA."""

    KUMMER = "kummer"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV14:
    """One exact candidate factory and its reviewed source/test/RFC provenance."""

    campaign: FrontierV14Campaign
    module: str
    factory: str
    test_path: str
    rfc_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV14Enrollment:
    """Immutable Alpha-v13 parent and exactly the required Kummer closure."""

    parent_entries: tuple[EditionEntryV13, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    factory_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV14Campaign]

    @property
    def theorem_specs(self) -> tuple[TheoremSpec, ...]:
        return self.frontier_specs[:KUMMER_THEOREM_V14_EXPECTED_COUNT]

    @property
    def corollary_specs(self) -> tuple[TheoremSpec, ...]:
        return self.frontier_specs[KUMMER_THEOREM_V14_EXPECTED_COUNT:]


PARENT_ALPHA_V13_COUNT = 1_543
PARENT_ALPHA_V13_ENROLLMENT_SHA256 = (
    "6b223edfe6a2e02dc09576671f4fc5f5a41aaf4156f829164222dd3e494da22f"
)
PARENT_ALPHA_V13_IDENTITY_SHA256 = (
    "a010e0ee5dece0d3325e8ec084c1f8769ef8e9ca47e2de891d344e54c1b439d1"
)
FRONTIER_V14_ROOT_NAMES = (
    "kummer_binomial_carry_bit_count",
    "kummer_carry_free_iff_not_divides",
)
FRONTIER_V14_ROOT_STATEMENT_SHA256 = MappingProxyType(
    {
        "kummer_binomial_carry_bit_count": (
            "f9f7312eacb89563dff059b63d310a3148b0b7df7f9e0425bbf4fdbd868e3c4f"
        ),
        "kummer_carry_free_iff_not_divides": (
            "ed30b756bd9703193020ae395a87f1f32a12859d2b9df8fbb79708e9bed2dc00"
        ),
    }
)
FRONTIER_V14_START_INDEX = PARENT_ALPHA_V13_COUNT
KUMMER_THEOREM_V14_EXPECTED_COUNT = 11
KUMMER_COROLLARY_V14_EXPECTED_COUNT = 2
FRONTIER_V14_EXPECTED_COUNT = (
    KUMMER_THEOREM_V14_EXPECTED_COUNT + KUMMER_COROLLARY_V14_EXPECTED_COUNT
)
FRONTIER_V14_EXPECTED_NAMES_SHA256 = (
    "2ff93cb296e4d4a077a8e8722bde54be2f0a9e4a72caedac5fcaa58508c60d6c"
)
KUMMER_CAMPAIGN_RFC = (
    "research/arithmetic-library/ha-kummer-theorem-campaign-rfc-v1.md"
)

_SOURCE_FACTORIES: tuple[tuple[str, str], ...] = (
    (
        "kummer_valuation_candidate",
        "make_kummer_valuation_candidate_theorems",
    ),
    (
        "kummer_carry_candidate",
        "make_kummer_carry_candidate_theorems",
    ),
    (
        "kummer_carry_candidate",
        "make_kummer_carry_corollary_candidate_theorems",
    ),
)


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@lru_cache(maxsize=1)
def _factory_inventory() -> tuple[
    Mapping[str, TheoremSpec],
    Mapping[str, str],
    Mapping[str, str],
]:
    specs: dict[str, TheoremSpec] = {}
    modules: dict[str, str] = {}
    factories: dict[str, str] = {}
    for module_name, factory_name in _SOURCE_FACTORIES:
        module = import_module(f"peano_lab.library.{module_name}")
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            raise AlphaV14EnrollmentError(
                f"missing Alpha-v14 source factory {module_name}.{factory_name}"
            )
        for spec in factory(TheoremSpec):
            previous = specs.get(spec.name)
            if previous is not None and previous != spec:
                raise AlphaV14EnrollmentError(
                    f"conflicting Alpha-v14 theorem factory rows {spec.name!r}"
                )
            if previous is None:
                specs[spec.name] = spec
                modules[spec.name] = module_name
                factories[spec.name] = factory_name
    return (
        MappingProxyType(specs),
        MappingProxyType(modules),
        MappingProxyType(factories),
    )


@lru_cache(maxsize=1)
def _ordered_frontier() -> tuple[TheoremSpec, ...]:
    if len(ALPHA_V13_ENTRIES) != PARENT_ALPHA_V13_COUNT:
        raise AlphaV14EnrollmentError("sealed Alpha-v13 parent count changed")
    if ALPHA_V13_ENROLLMENT_SHA256 != PARENT_ALPHA_V13_ENROLLMENT_SHA256:
        raise AlphaV14EnrollmentError("sealed Alpha-v13 enrollment identity changed")
    if ALPHA_V13_IDENTITY_SHA256 != PARENT_ALPHA_V13_IDENTITY_SHA256:
        raise AlphaV14EnrollmentError("sealed Alpha-v13 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V13_ENTRIES}
    candidates, _owners, _factories = _factory_inventory()
    ordered: list[TheoremSpec] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in available or name in visited:
            return
        if name in visiting:
            raise AlphaV14EnrollmentError(f"cyclic Alpha-v14 dependency {name!r}")
        spec = candidates.get(name)
        if spec is None:
            raise AlphaV14EnrollmentError(
                f"missing Alpha-v14 transitive dependency {name!r}"
            )
        visiting.add(name)
        for dependency in spec.dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        ordered.append(spec)

    for root in FRONTIER_V14_ROOT_NAMES:
        visit(root)
        if root not in visited:
            raise AlphaV14EnrollmentError(f"Alpha-v14 root {root!r} was already enrolled")
        actual = sha256(candidates[root].statement.encode("utf-8")).hexdigest()
        if actual != FRONTIER_V14_ROOT_STATEMENT_SHA256[root]:
            raise AlphaV14EnrollmentError(f"Alpha-v14 root statement changed: {root!r}")

    result = tuple(ordered)
    if len(result) != FRONTIER_V14_EXPECTED_COUNT:
        raise AlphaV14EnrollmentError(
            f"Alpha-v14 closure count changed: {len(result)} != "
            f"{FRONTIER_V14_EXPECTED_COUNT}"
        )
    if result[KUMMER_THEOREM_V14_EXPECTED_COUNT - 1].name != FRONTIER_V14_ROOT_NAMES[0]:
        raise AlphaV14EnrollmentError("Alpha-v14 Kummer theorem root boundary changed")
    if result[-1].name != FRONTIER_V14_ROOT_NAMES[1]:
        raise AlphaV14EnrollmentError("Alpha-v14 Kummer corollary root boundary changed")
    actual_names_root = sha256(
        _compact(tuple(spec.name for spec in result)).encode("utf-8")
    ).hexdigest()
    if actual_names_root != FRONTIER_V14_EXPECTED_NAMES_SHA256:
        raise AlphaV14EnrollmentError(
            "Alpha-v14 exact dependency-topological order changed: "
            f"{actual_names_root}"
        )
    return result


FRONTIER_V14_EXPECTED_NAMES: tuple[str, ...] = tuple(
    spec.name for spec in _ordered_frontier()
)
KUMMER_THEOREM_V14_EXPECTED_NAMES = FRONTIER_V14_EXPECTED_NAMES[
    :KUMMER_THEOREM_V14_EXPECTED_COUNT
]
KUMMER_COROLLARY_V14_EXPECTED_NAMES = FRONTIER_V14_EXPECTED_NAMES[
    KUMMER_THEOREM_V14_EXPECTED_COUNT:
]


def _source_manifest() -> tuple[EnrollmentSourceV14, ...]:
    _candidates, _owners, factories = _factory_inventory()
    result: list[EnrollmentSourceV14] = []
    for module, factory in _SOURCE_FACTORIES:
        names = tuple(
            spec.name
            for spec in _ordered_frontier()
            if factories[spec.name] == factory
        )
        if not names:
            raise AlphaV14EnrollmentError(f"empty Alpha-v14 source factory {factory!r}")
        result.append(
            EnrollmentSourceV14(
                campaign=FrontierV14Campaign.KUMMER,
                module=module,
                factory=factory,
                test_path=f"peano-lab/py/tests/test_{module}.py",
                rfc_path=KUMMER_CAMPAIGN_RFC,
                names=names,
            )
        )
    return tuple(result)


FRONTIER_V14_BODY_ENROLLMENT_MANIFEST = _source_manifest()
FRONTIER_V14_EXPECTED_SOURCE_COUNTS = tuple(
    len(source.names) for source in FRONTIER_V14_BODY_ENROLLMENT_MANIFEST
)
FRONTIER_V14_RFC_PATHS = (KUMMER_CAMPAIGN_RFC,)


@lru_cache(maxsize=1)
def alpha_v14_enrollment() -> AlphaV14Enrollment:
    """Return the sealed, dependency-minimal Alpha-v14 Kummer append."""

    ordered = _ordered_frontier()
    _candidates, owners, factories = _factory_inventory()
    source_by_name: dict[str, str] = {}
    factory_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    campaign_by_name: dict[str, FrontierV14Campaign] = {}
    manifest_by_factory = {
        source.factory: source for source in FRONTIER_V14_BODY_ENROLLMENT_MANIFEST
    }
    available = {entry.spec.name for entry in ALPHA_V13_ENTRIES}
    for spec in ordered:
        if spec.name in available:
            raise AlphaV14EnrollmentError(f"duplicate Alpha-v14 row {spec.name!r}")
        missing = set(spec.dependencies) - available
        if missing:
            raise AlphaV14EnrollmentError(
                f"forward Alpha-v14 dependencies for {spec.name!r}: {sorted(missing)!r}"
            )
        if any("DNE" in command for command in spec.script):
            raise AlphaV14EnrollmentError(
                f"Alpha-v14 constructive theorem contains DNE: {spec.name!r}"
            )
        source = manifest_by_factory[factories[spec.name]]
        source_by_name[spec.name] = f"peano-lab/py/peano_lab/library/{owners[spec.name]}.py"
        factory_by_name[spec.name] = source.factory
        test_by_name[spec.name] = source.test_path
        rfc_by_name[spec.name] = source.rfc_path
        campaign_by_name[spec.name] = FrontierV14Campaign.KUMMER
        available.add(spec.name)
    return AlphaV14Enrollment(
        parent_entries=ALPHA_V13_ENTRIES,
        frontier_specs=ordered,
        source_by_name=MappingProxyType(source_by_name),
        factory_by_name=MappingProxyType(factory_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        campaign_by_name=MappingProxyType(campaign_by_name),
    )


__all__ = [
    "AlphaV14Enrollment",
    "AlphaV14EnrollmentError",
    "EnrollmentSourceV14",
    "FRONTIER_V14_BODY_ENROLLMENT_MANIFEST",
    "FRONTIER_V14_EXPECTED_COUNT",
    "FRONTIER_V14_EXPECTED_NAMES",
    "FRONTIER_V14_EXPECTED_NAMES_SHA256",
    "FRONTIER_V14_EXPECTED_SOURCE_COUNTS",
    "FRONTIER_V14_RFC_PATHS",
    "FRONTIER_V14_ROOT_NAMES",
    "FRONTIER_V14_ROOT_STATEMENT_SHA256",
    "FRONTIER_V14_START_INDEX",
    "FrontierV14Campaign",
    "KUMMER_CAMPAIGN_RFC",
    "KUMMER_COROLLARY_V14_EXPECTED_COUNT",
    "KUMMER_COROLLARY_V14_EXPECTED_NAMES",
    "KUMMER_THEOREM_V14_EXPECTED_COUNT",
    "KUMMER_THEOREM_V14_EXPECTED_NAMES",
    "PARENT_ALPHA_V13_COUNT",
    "PARENT_ALPHA_V13_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V13_IDENTITY_SHA256",
    "alpha_v14_enrollment",
]
