"""Code-owned append manifest for the second Bertrand infrastructure tranche.

Alpha v3 is an immutable 923-row parent.  This module appends exactly forty-two
reviewed Round-2 rows in source and dependency order: valuation laws, valuation
multiplication, the integer envelope, ceiling/floor-square relations, floor
square totality, and quotient budgets.  Enrollment records body evidence only;
it never admits an empty-context theorem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v3 import (
    ALPHA_ENTRIES as ALPHA_V3_ENTRIES,
    ALPHA_V3_ENROLLMENT_SHA256,
    ALPHA_V3_IDENTITY_SHA256,
    EditionEntry as EditionEntryV3,
)
from .theorems import TheoremSpec


class AlphaV4EnrollmentError(ValueError):
    """The frozen v3 parent or reviewed Round-2 append is inconsistent."""


class BertrandV4EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment tranche for every Alpha-v4 row."""

    B2_VALUATION_LAWS = "bertrand_b2_valuation_laws"
    B2_VALUATION_MULTIPLICATION = "bertrand_b2_valuation_multiplication"
    B6_INTEGER_ENVELOPE = "bertrand_b6_integer_envelope"
    B6_CEIL_SQRT = "bertrand_b6_ceil_sqrt"
    B6_FLOOR_SQRT_TOTAL = "bertrand_b6_floor_sqrt_total"
    B6_QUOTIENT_BUDGET = "bertrand_b6_quotient_budget"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV4:
    """One exact candidate factory and its executable review source."""

    origin: BertrandV4EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV4Enrollment:
    """The sealed v3 parent and exact Round-2 append."""

    parent_entries: tuple[EditionEntryV3, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV4EnrollmentOrigin]


PARENT_ALPHA_V3_COUNT = 923
PARENT_ALPHA_V3_ENROLLMENT_SHA256 = (
    "4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4"
)
PARENT_ALPHA_V3_IDENTITY_SHA256 = (
    "e20eefac839fb2bcd3e696989c091a5f6837de04824f94e1073723851a471a2f"
)
BERTRAND_V4_START_INDEX = PARENT_ALPHA_V3_COUNT
BERTRAND_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md"
)


BERTRAND_V4_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV4, ...] = (
    EnrollmentSourceV4(
        BertrandV4EnrollmentOrigin.B2_VALUATION_LAWS,
        "bertrand_power_valuation_laws_candidate",
        "make_bertrand_power_valuation_law_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_valuation_laws_candidate.py",
        (
            "prime_two_le",
            "succ_le_mul_of_two_le_right",
            "prime_power_exponent_le",
            "prime_power_divides_exponent_le_value",
            "power_valuation_successor_not_divides",
            "power_valuation_selected_and_successor_not_divides",
        ),
    ),
    EnrollmentSourceV4(
        BertrandV4EnrollmentOrigin.B2_VALUATION_MULTIPLICATION,
        "bertrand_power_divisibility_candidate",
        "make_bertrand_power_divisibility_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_divisibility_candidate.py",
        (
            "mul_shuffle_four",
            "power_divides_exponent_antitone",
            "power_divides_add_mul",
            "power_divides_successor_of_cofactor",
            "prime_power_successor_cancel_cofactor",
            "prime_nondivisor_mul",
            "power_valuation_exact_cofactor",
            "power_valuation_mul_successor_not_divides",
            "power_valuation_mul_lower",
            "power_valuation_mul_upper",
            "prime_power_valuation_mul",
        ),
    ),
    EnrollmentSourceV4(
        BertrandV4EnrollmentOrigin.B6_INTEGER_ENVELOPE,
        "bertrand_integer_envelope_candidate",
        "make_bertrand_integer_envelope_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_integer_envelope_candidate.py",
        (
            "two_mul_eq_add_self",
            "pow_mul_base",
            "pow_two_base_two_value_four",
            "pow_two_twelve_eq_pow_four_six",
            "bertrand_guard_six_step_transport",
        ),
    ),
    EnrollmentSourceV4(
        BertrandV4EnrollmentOrigin.B6_CEIL_SQRT,
        "bertrand_ceil_sqrt_candidate",
        "make_bertrand_ceil_sqrt_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_ceil_sqrt_candidate.py",
        (
            "ceil_div_six_shift",
            "ceil_div_six_total",
            "ceil_div_six_functional",
            "ceil_div_six_exists_unique",
            "square_six_shift_identity",
            "ceil_div_six_square_six_step",
            "floor_sqrt_lower_bound",
            "floor_sqrt_strict_upper_bound",
            "floor_sqrt_functional",
        ),
    ),
    EnrollmentSourceV4(
        BertrandV4EnrollmentOrigin.B6_FLOOR_SQRT_TOTAL,
        "bertrand_floor_sqrt_total_candidate",
        "make_bertrand_floor_sqrt_total_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_floor_sqrt_total_candidate.py",
        (
            "square_lt_successor_square",
            "floor_sqrt_total",
            "floor_sqrt_exists_unique",
            "floor_sqrt_monotone",
        ),
    ),
    EnrollmentSourceV4(
        BertrandV4EnrollmentOrigin.B6_QUOTIENT_BUDGET,
        "bertrand_quotient_budget_candidate",
        "make_bertrand_quotient_budget_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_quotient_budget_candidate.py",
        (
            "mul_le_cancel_left_nonzero",
            "three_mul_eq_two_mul_add_self",
            "ceil_div_six_le_of_upper",
            "double_triple_remainder_complement_budget",
            "canonical_double_triple_remainder_complement_budget",
            "floor_ceil_complement_budget",
            "floor_ceil_division_budget",
        ),
    ),
)

BERTRAND_V4_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V4_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V4_EXPECTED_COUNT = 42


def _load_source(source: EnrollmentSourceV4) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV4EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV4EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    names = tuple(spec.name for spec in produced)
    if names != source.names:
        raise AlphaV4EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: {names!r}"
        )
    if len(set(names)) != len(names):
        raise AlphaV4EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v4_enrollment() -> AlphaV4Enrollment:
    """Return the exact v3 ledger plus the non-admitting Round-2 append."""

    if len(ALPHA_V3_ENTRIES) != PARENT_ALPHA_V3_COUNT:
        raise AlphaV4EnrollmentError("Alpha v3 parent count changed")
    if ALPHA_V3_ENROLLMENT_SHA256 != PARENT_ALPHA_V3_ENROLLMENT_SHA256:
        raise AlphaV4EnrollmentError("Alpha v3 enrollment identity changed")
    if ALPHA_V3_IDENTITY_SHA256 != PARENT_ALPHA_V3_IDENTITY_SHA256:
        raise AlphaV4EnrollmentError("Alpha v3 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V3_ENTRIES}
    if len(available) != PARENT_ALPHA_V3_COUNT:
        raise AlphaV4EnrollmentError("Alpha v3 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV4EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V4_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV4EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV4EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV4EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V4_EXPECTED_NAMES:
        raise AlphaV4EnrollmentError("Bertrand v4 append order changed")
    if len(result) != BERTRAND_V4_EXPECTED_COUNT:
        raise AlphaV4EnrollmentError("Bertrand v4 append count changed")
    return AlphaV4Enrollment(
        parent_entries=ALPHA_V3_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV4Enrollment",
    "AlphaV4EnrollmentError",
    "BERTRAND_RFC_PATH",
    "BERTRAND_V4_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V4_EXPECTED_COUNT",
    "BERTRAND_V4_EXPECTED_NAMES",
    "BERTRAND_V4_START_INDEX",
    "BertrandV4EnrollmentOrigin",
    "EnrollmentSourceV4",
    "PARENT_ALPHA_V3_COUNT",
    "PARENT_ALPHA_V3_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V3_IDENTITY_SHA256",
    "alpha_v4_enrollment",
]
