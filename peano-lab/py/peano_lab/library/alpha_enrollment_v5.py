"""Code-owned append manifest for the Bertrand FactorialVal tranche.

Alpha v4 is an immutable 965-row parent.  This module appends exactly seven
reviewed FactorialVal rows in source and dependency order.  Enrollment records
dependency-curried body evidence only; it never admits an empty-context
theorem or changes checked theorem use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v4 import (
    ALPHA_ENTRIES as ALPHA_V4_ENTRIES,
    ALPHA_V4_ENROLLMENT_SHA256,
    ALPHA_V4_IDENTITY_SHA256,
    EditionEntry as EditionEntryV4,
)
from .theorems import TheoremSpec


class AlphaV5EnrollmentError(ValueError):
    """The frozen v4 parent or reviewed FactorialVal append is inconsistent."""


class BertrandV5EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v5 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV5:
    """One exact candidate factory and its executable audit source."""

    origin: BertrandV5EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV5Enrollment:
    """The sealed v4 parent and exact FactorialVal append."""

    parent_entries: tuple[EditionEntryV4, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV5EnrollmentOrigin]


PARENT_ALPHA_V4_COUNT = 965
PARENT_ALPHA_V4_ENROLLMENT_SHA256 = (
    "e4c83174c1800c135d0fe9ac03b5cdfcc5f11e5517f871b3f198586973a20c31"
)
PARENT_ALPHA_V4_IDENTITY_SHA256 = (
    "e0324009614f755f2251a5b27d29587b0c43015385a78d567b328776b92239a5"
)
BERTRAND_V5_START_INDEX = PARENT_ALPHA_V4_COUNT
BERTRAND_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md"
)


BERTRAND_V5_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV5, ...] = (
    EnrollmentSourceV5(
        BertrandV5EnrollmentOrigin.BERTRAND,
        "bertrand_factorial_valuation_candidate",
        "make_bertrand_factorial_valuation_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_factorial_valuation_candidate.py",
        (
            "factorial_nonzero",
            "prime_power_valuation_one_zero",
            "factorial_valuation_exists",
            "factorial_valuation_functional",
            "prime_factorial_valuation_zero",
            "prime_factorial_valuation_succ",
            "prime_factorial_valuation_succ_invert",
        ),
    ),
)

BERTRAND_V5_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V5_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V5_EXPECTED_COUNT = 7


def _load_source(source: EnrollmentSourceV5) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV5EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV5EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    names = tuple(spec.name for spec in produced)
    if names != source.names:
        raise AlphaV5EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: {names!r}"
        )
    if len(set(names)) != len(names):
        raise AlphaV5EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v5_enrollment() -> AlphaV5Enrollment:
    """Return the exact v4 ledger plus the non-admitting FactorialVal append."""

    if len(ALPHA_V4_ENTRIES) != PARENT_ALPHA_V4_COUNT:
        raise AlphaV5EnrollmentError("Alpha v4 parent count changed")
    if ALPHA_V4_ENROLLMENT_SHA256 != PARENT_ALPHA_V4_ENROLLMENT_SHA256:
        raise AlphaV5EnrollmentError("Alpha v4 enrollment identity changed")
    if ALPHA_V4_IDENTITY_SHA256 != PARENT_ALPHA_V4_IDENTITY_SHA256:
        raise AlphaV5EnrollmentError("Alpha v4 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V4_ENTRIES}
    if len(available) != PARENT_ALPHA_V4_COUNT:
        raise AlphaV5EnrollmentError("Alpha v4 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV5EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V5_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV5EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV5EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV5EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V5_EXPECTED_NAMES:
        raise AlphaV5EnrollmentError("Bertrand v5 append order changed")
    if len(result) != BERTRAND_V5_EXPECTED_COUNT:
        raise AlphaV5EnrollmentError("Bertrand v5 append count changed")
    return AlphaV5Enrollment(
        parent_entries=ALPHA_V4_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV5Enrollment",
    "AlphaV5EnrollmentError",
    "BERTRAND_RFC_PATH",
    "BERTRAND_V5_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V5_EXPECTED_COUNT",
    "BERTRAND_V5_EXPECTED_NAMES",
    "BERTRAND_V5_START_INDEX",
    "BertrandV5EnrollmentOrigin",
    "EnrollmentSourceV5",
    "PARENT_ALPHA_V4_COUNT",
    "PARENT_ALPHA_V4_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V4_IDENTITY_SHA256",
    "alpha_v5_enrollment",
]
