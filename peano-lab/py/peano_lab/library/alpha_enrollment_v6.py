"""Code-owned append manifest for the Bertrand Alpha-v6 tranche.

Alpha v5 is an immutable 972-row parent.  This module appends exactly twenty-
one reviewed rows in dependency-topological source order: eight threshold
bases, five finite Legendre-sum interface rows, five relational-power bridge
rows, and three valuation bridge rows.  Enrollment records dependency-curried
body evidence only; it never admits an empty-context theorem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v5 import (
    ALPHA_ENTRIES as ALPHA_V5_ENTRIES,
    ALPHA_V5_ENROLLMENT_SHA256,
    ALPHA_V5_IDENTITY_SHA256,
    EditionEntry as EditionEntryV5,
)
from .theorems import TheoremSpec


class AlphaV6EnrollmentError(ValueError):
    """The frozen v5 parent or reviewed twenty-one-row append is inconsistent."""


class BertrandV6EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v6 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV6:
    """One exact candidate factory and its executable audit source."""

    origin: BertrandV6EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV6Enrollment:
    """The sealed v5 parent and exact twenty-one-row Bertrand append."""

    parent_entries: tuple[EditionEntryV5, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV6EnrollmentOrigin]


PARENT_ALPHA_V5_COUNT = 972
PARENT_ALPHA_V5_ENROLLMENT_SHA256 = (
    "46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473"
)
PARENT_ALPHA_V5_IDENTITY_SHA256 = (
    "bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af"
)
BERTRAND_V6_START_INDEX = PARENT_ALPHA_V5_COUNT
BERTRAND_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md"
)


BERTRAND_V6_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV6, ...] = (
    EnrollmentSourceV6(
        BertrandV6EnrollmentOrigin.BERTRAND,
        "bertrand_threshold_base_candidate",
        "make_bertrand_threshold_base_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_threshold_base_candidate.py",
        (
            "forty_two_le_sixty_four",
            "forty_three_le_sixty_four",
            "seventy_le_one_twenty_eight",
            "seventy_six_le_one_twenty_eight",
            "floor_sqrt_threshold_sixty_four",
            "forty_two_successor_le_square_of_sixty_four_le",
            "ceil_square_seven_successor_lower",
            "bertrand_base_residue_linear_bounds",
        ),
    ),
    EnrollmentSourceV6(
        BertrandV6EnrollmentOrigin.BERTRAND,
        "bertrand_legendre_sum_candidate",
        "make_bertrand_legendre_sum_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_legendre_sum_candidate.py",
        (
            "prime_power_quotient_prefix_exists",
            "power_quotient_prefix_transport",
            "prime_legendre_sum_exists",
            "legendre_sum_functional",
            "legendre_sum_zero",
        ),
    ),
    EnrollmentSourceV6(
        BertrandV6EnrollmentOrigin.BERTRAND,
        "bertrand_power_bridge_candidate",
        "make_bertrand_power_bridge_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_bridge_candidate.py",
        (
            "pow_successor_compose",
            "pow_two_two_exact",
            "pow_two_seven_exact",
            "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
            "bertrand_guard_base_residue",
        ),
    ),
    EnrollmentSourceV6(
        BertrandV6EnrollmentOrigin.BERTRAND,
        "bertrand_legendre_valuation_bridge_candidate",
        "make_bertrand_legendre_valuation_bridge_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_legendre_valuation_bridge_candidate.py",
        (
            "prime_power_quotient_tail_zero",
            "prime_power_divides_exponent_le_valuation",
            "power_divides_of_exponent_le_valuation",
        ),
    ),
)

BERTRAND_V6_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V6_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V6_EXPECTED_COUNTS = (8, 5, 5, 3)
BERTRAND_V6_EXPECTED_COUNT = 21


def _load_source(source: EnrollmentSourceV6) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV6EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV6EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    names = tuple(spec.name for spec in produced)
    if names != source.names:
        raise AlphaV6EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: {names!r}"
        )
    if len(set(names)) != len(names):
        raise AlphaV6EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v6_enrollment() -> AlphaV6Enrollment:
    """Return the exact v5 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V5_ENTRIES) != PARENT_ALPHA_V5_COUNT:
        raise AlphaV6EnrollmentError("Alpha v5 parent count changed")
    if ALPHA_V5_ENROLLMENT_SHA256 != PARENT_ALPHA_V5_ENROLLMENT_SHA256:
        raise AlphaV6EnrollmentError("Alpha v5 enrollment identity changed")
    if ALPHA_V5_IDENTITY_SHA256 != PARENT_ALPHA_V5_IDENTITY_SHA256:
        raise AlphaV6EnrollmentError("Alpha v5 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V5_ENTRIES}
    if len(available) != PARENT_ALPHA_V5_COUNT:
        raise AlphaV6EnrollmentError("Alpha v5 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV6EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V6_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV6EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV6EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV6EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V6_EXPECTED_NAMES:
        raise AlphaV6EnrollmentError("Bertrand v6 append order changed")
    if tuple(len(source.names) for source in BERTRAND_V6_BODY_ENROLLMENT_MANIFEST) != (
        BERTRAND_V6_EXPECTED_COUNTS
    ):
        raise AlphaV6EnrollmentError("Bertrand v6 source-block counts changed")
    if len(result) != BERTRAND_V6_EXPECTED_COUNT:
        raise AlphaV6EnrollmentError("Bertrand v6 append count changed")
    return AlphaV6Enrollment(
        parent_entries=ALPHA_V5_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV6Enrollment",
    "AlphaV6EnrollmentError",
    "BERTRAND_RFC_PATH",
    "BERTRAND_V6_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V6_EXPECTED_COUNT",
    "BERTRAND_V6_EXPECTED_COUNTS",
    "BERTRAND_V6_EXPECTED_NAMES",
    "BERTRAND_V6_START_INDEX",
    "BertrandV6EnrollmentOrigin",
    "EnrollmentSourceV6",
    "PARENT_ALPHA_V5_COUNT",
    "PARENT_ALPHA_V5_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V5_IDENTITY_SHA256",
    "alpha_v6_enrollment",
]
