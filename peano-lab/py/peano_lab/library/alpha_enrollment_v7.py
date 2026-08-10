"""Code-owned append manifest for the Bertrand Alpha-v7 tranche.

Alpha v6 is an immutable 993-row parent.  This module appends exactly twenty-
four reviewed rows in dependency-topological source order: three previously
unenrolled initial-segment constructors, five Legendre successor rows, four
capacity-shared power rows, two compact H/J base-window rows, five finite
Legendre-recurrence rows, three compact H/J transport rows, and two
factorial--Legendre agreement rows.  Enrollment records dependency-curried
body evidence only; it never admits an empty-context theorem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v6 import (
    ALPHA_ENTRIES as ALPHA_V6_ENTRIES,
    ALPHA_V6_ENROLLMENT_SHA256,
    ALPHA_V6_IDENTITY_SHA256,
    EditionEntry as EditionEntryV6,
)
from .theorems import TheoremSpec


class AlphaV7EnrollmentError(ValueError):
    """The frozen v6 parent or reviewed twenty-four-row append is inconsistent."""


class BertrandV7EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v7 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV7:
    """One exact candidate factory and its executable audit source."""

    origin: BertrandV7EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV7Enrollment:
    """The sealed v6 parent and exact twenty-four-row Bertrand append."""

    parent_entries: tuple[EditionEntryV6, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV7EnrollmentOrigin]


PARENT_ALPHA_V6_COUNT = 993
PARENT_ALPHA_V6_ENROLLMENT_SHA256 = (
    "dc25a3dc0ab7346f9188eee1262700b40bb09efdacfa849f3a27475ed870b5a7"
)
PARENT_ALPHA_V6_IDENTITY_SHA256 = (
    "7e46b80c4799e51da32cedf21a130274200fa14b21e0fec3b42f74d1523ab23b"
)
BERTRAND_V7_START_INDEX = PARENT_ALPHA_V6_COUNT
BERTRAND_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md"
)


BERTRAND_V7_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV7, ...] = (
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_initial_segment_constructor_candidate",
        "make_bertrand_initial_segment_constructor_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_initial_segment_constructor_candidate.py",
        (
            "eisenstein_initial_segment_indicator_choice",
            "eisenstein_initial_segment_prefix_extend",
            "eisenstein_initial_segment_prefix_exists",
        ),
    ),
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_legendre_successor_candidate",
        "make_bertrand_legendre_successor_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_legendre_successor_candidate.py",
        (
            "division_remainder_successor_cases",
            "division_successor_quotient_by_bit",
            "valuation_threshold_bit_decides_power_divides",
            "power_quotient_prefix_decoded_divrem",
            "power_quotient_successor_pointwise_add",
        ),
    ),
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_power_total_candidate",
        "make_bertrand_power_total_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_power_total_candidate.py",
        (
            "pow_successor_compose_from_total",
            "pow_mul_exp_from_total",
            "pow_exponent_monotone_from_total",
            "pow_two_seed_bundle_from_total",
        ),
    ),
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_hj_base_window_candidate",
        "make_bertrand_hj_base_window_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_hj_base_window_candidate.py",
        (
            "pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
            "bertrand_hj_base_window_from_total",
        ),
    ),
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_legendre_recurrence_candidate",
        "make_bertrand_legendre_recurrence_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_legendre_recurrence_candidate.py",
        (
            "beta_sum_succ_last_zero",
            "prime_power_quotient_prefix_last_zero",
            "legendre_sum_zero_extended_prefix",
            "initial_segment_prefix_sum_exists",
            "prime_legendre_sum_succ",
        ),
    ),
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_hj_transport_candidate",
        "make_bertrand_hj_transport_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_hj_transport_candidate.py",
        (
            "bertrand_h_six_step_transport_from_total",
            "bertrand_j_six_step_transport_from_total",
            "bertrand_hj_six_step_from_total",
        ),
    ),
    EnrollmentSourceV7(
        BertrandV7EnrollmentOrigin.BERTRAND,
        "bertrand_factorial_legendre_candidate",
        "make_bertrand_factorial_legendre_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_factorial_legendre_candidate.py",
        (
            "factorial_legendre_successor_agreement",
            "prime_factorial_valuation_eq_legendre_sum",
        ),
    ),
)

BERTRAND_V7_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V7_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V7_EXPECTED_COUNTS = (3, 5, 4, 2, 5, 3, 2)
BERTRAND_V7_EXPECTED_COUNT = 24


def _load_source(source: EnrollmentSourceV7) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV7EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV7EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    produced_names = tuple(spec.name for spec in produced)
    if produced_names != source.names:
        raise AlphaV7EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: "
            f"{produced_names!r}"
        )
    if len(set(produced_names)) != len(produced_names):
        raise AlphaV7EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v7_enrollment() -> AlphaV7Enrollment:
    """Return the exact v6 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V6_ENTRIES) != PARENT_ALPHA_V6_COUNT:
        raise AlphaV7EnrollmentError("Alpha v6 parent count changed")
    if ALPHA_V6_ENROLLMENT_SHA256 != PARENT_ALPHA_V6_ENROLLMENT_SHA256:
        raise AlphaV7EnrollmentError("Alpha v6 enrollment identity changed")
    if ALPHA_V6_IDENTITY_SHA256 != PARENT_ALPHA_V6_IDENTITY_SHA256:
        raise AlphaV7EnrollmentError("Alpha v6 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V6_ENTRIES}
    if len(available) != PARENT_ALPHA_V6_COUNT:
        raise AlphaV7EnrollmentError("Alpha v6 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV7EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V7_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV7EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV7EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV7EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V7_EXPECTED_NAMES:
        raise AlphaV7EnrollmentError("Bertrand v7 append order changed")
    if tuple(len(source.names) for source in BERTRAND_V7_BODY_ENROLLMENT_MANIFEST) != (
        BERTRAND_V7_EXPECTED_COUNTS
    ):
        raise AlphaV7EnrollmentError("Bertrand v7 source-block counts changed")
    if len(result) != BERTRAND_V7_EXPECTED_COUNT:
        raise AlphaV7EnrollmentError("Bertrand v7 append count changed")
    return AlphaV7Enrollment(
        parent_entries=ALPHA_V6_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV7Enrollment",
    "AlphaV7EnrollmentError",
    "BERTRAND_RFC_PATH",
    "BERTRAND_V7_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V7_EXPECTED_COUNT",
    "BERTRAND_V7_EXPECTED_COUNTS",
    "BERTRAND_V7_EXPECTED_NAMES",
    "BERTRAND_V7_START_INDEX",
    "BertrandV7EnrollmentOrigin",
    "EnrollmentSourceV7",
    "PARENT_ALPHA_V6_COUNT",
    "PARENT_ALPHA_V6_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V6_IDENTITY_SHA256",
    "alpha_v7_enrollment",
]
