"""Code-owned append manifest for the first Bertrand Alpha-v3 tranche.

Alpha v2 is an immutable 902-row parent.  This module appends exactly the
reviewed B0 interval, B1 power-order, B1 power-growth, and B2 bounded
valuation candidate factories.  Constructing the manifest never admits a
theorem: all twenty-one rows remain dependency-curried body evidence until a
separate empty-context closure and promotion campaign succeeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v2 import (
    ALPHA_ENTRIES as ALPHA_V2_ENTRIES,
    ALPHA_V2_ENROLLMENT_SHA256,
    ALPHA_V2_IDENTITY_SHA256,
    EditionEntry as EditionEntryV2,
)
from .theorems import TheoremSpec


class AlphaV3EnrollmentError(ValueError):
    """The frozen v2 parent or reviewed Bertrand append is inconsistent."""


class BertrandEnrollmentOrigin(str, Enum):
    """Immutable first-enrollment tranche for the initial campaign rows."""

    B0_INTERVAL = "bertrand_b0_interval"
    B1_POWER_ORDER = "bertrand_b1_power_order"
    B1_POWER_GROWTH = "bertrand_b1_power_growth"
    B2_BOUNDED_VALUATION = "bertrand_b2_bounded_valuation"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV3:
    """One exact factory plus its executable review evidence."""

    origin: BertrandEnrollmentOrigin
    module: str
    factory: str
    test_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV3Enrollment:
    """The sealed v2 parent and exact first Bertrand append."""

    parent_entries: tuple[EditionEntryV2, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandEnrollmentOrigin]


PARENT_ALPHA_V2_COUNT = 902
PARENT_ALPHA_V2_ENROLLMENT_SHA256 = (
    "00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe"
)
PARENT_ALPHA_V2_IDENTITY_SHA256 = (
    "aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4"
)
BERTRAND_START_INDEX = PARENT_ALPHA_V2_COUNT
BERTRAND_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md"
)


BERTRAND_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV3, ...] = (
    EnrollmentSourceV3(
        BertrandEnrollmentOrigin.B0_INTERVAL,
        "bertrand_prime_interval_candidate",
        "make_bertrand_prime_interval_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_prime_interval_candidate.py",
        (
            "prime_strictly_above_decidable",
            "bounded_prime_interval_search",
            "prime_interval_exclusion_refutes_witness",
            "bounded_prime_interval_decidable",
        ),
    ),
    EnrollmentSourceV3(
        BertrandEnrollmentOrigin.B1_POWER_ORDER,
        "bertrand_power_order_candidate",
        "make_bertrand_power_order_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_order_candidate.py",
        (
            "mul_le_mul",
            "le_mul_of_one_le_right",
            "le_mul_of_one_le_left",
            "pow_base_monotone",
        ),
    ),
    EnrollmentSourceV3(
        BertrandEnrollmentOrigin.B1_POWER_GROWTH,
        "bertrand_power_growth_candidate",
        "make_bertrand_power_growth_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_growth_candidate.py",
        (
            "one_le_pow",
            "pow_nonzero_of_one_le",
            "pow_exponent_monotone",
        ),
    ),
    EnrollmentSourceV3(
        BertrandEnrollmentOrigin.B2_BOUNDED_VALUATION,
        "bertrand_power_valuation_candidate",
        "make_bertrand_power_valuation_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_valuation_candidate.py",
        (
            "power_divides_decidable",
            "power_divides_zero",
            "bounded_power_valuation_search",
            "bounded_power_valuation_exists",
            "power_valuation_exists",
            "power_valuation_functional",
            "power_valuation_power_divides",
            "power_valuation_dominates",
            "prime_power_valuation_exists",
            "prime_power_valuation_functional",
        ),
    ),
)

BERTRAND_EXPECTED_NAMES = tuple(
    name for source in BERTRAND_BODY_ENROLLMENT_MANIFEST for name in source.names
)
BERTRAND_EXPECTED_COUNT = 21


def _load_source(source: EnrollmentSourceV3) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV3EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV3EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    names = tuple(spec.name for spec in produced)
    if names != source.names:
        raise AlphaV3EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: {names!r}"
        )
    if len(set(names)) != len(names):
        raise AlphaV3EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v3_enrollment() -> AlphaV3Enrollment:
    """Return the validated v2 ledger plus the non-admitting append."""

    if len(ALPHA_V2_ENTRIES) != PARENT_ALPHA_V2_COUNT:
        raise AlphaV3EnrollmentError("Alpha v2 parent count changed")
    if ALPHA_V2_ENROLLMENT_SHA256 != PARENT_ALPHA_V2_ENROLLMENT_SHA256:
        raise AlphaV3EnrollmentError("Alpha v2 enrollment identity changed")
    if ALPHA_V2_IDENTITY_SHA256 != PARENT_ALPHA_V2_IDENTITY_SHA256:
        raise AlphaV3EnrollmentError("Alpha v2 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V2_ENTRIES}
    if len(available) != PARENT_ALPHA_V2_COUNT:
        raise AlphaV3EnrollmentError("Alpha v2 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandEnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV3EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV3EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if "DNE" in spec.script:
                raise AlphaV3EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_EXPECTED_NAMES:
        raise AlphaV3EnrollmentError("Bertrand append order changed")
    if len(result) != BERTRAND_EXPECTED_COUNT:
        raise AlphaV3EnrollmentError("Bertrand append count changed")
    return AlphaV3Enrollment(
        parent_entries=ALPHA_V2_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV3Enrollment",
    "AlphaV3EnrollmentError",
    "BERTRAND_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_EXPECTED_COUNT",
    "BERTRAND_EXPECTED_NAMES",
    "BERTRAND_RFC_PATH",
    "BERTRAND_START_INDEX",
    "BertrandEnrollmentOrigin",
    "EnrollmentSourceV3",
    "PARENT_ALPHA_V2_COUNT",
    "PARENT_ALPHA_V2_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V2_IDENTITY_SHA256",
    "alpha_v3_enrollment",
]
