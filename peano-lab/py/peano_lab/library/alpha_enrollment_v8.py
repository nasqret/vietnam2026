"""Code-owned append manifest for the Bertrand Alpha-v8 tranche.

Alpha v7 is an immutable 1,017-row parent.  This module appends exactly
thirty-eight reviewed Choose and central-binomial rows in two dependency-
topological microbatches of twenty-four and fourteen rows.  Enrollment records
dependency-curried body evidence only; it never admits an empty-context
theorem or grants checked use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v7 import (
    ALPHA_ENTRIES as ALPHA_V7_ENTRIES,
    ALPHA_V7_ENROLLMENT_SHA256,
    ALPHA_V7_IDENTITY_SHA256,
    EditionEntry as EditionEntryV7,
)
from .theorems import TheoremSpec


class AlphaV8EnrollmentError(ValueError):
    """The frozen v7 parent or reviewed thirty-eight-row append is invalid."""


class BertrandV8EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v8 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV8:
    """One exact candidate factory and its executable audit source."""

    origin: BertrandV8EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV8Enrollment:
    """The sealed v7 parent and exact thirty-eight-row Bertrand append."""

    parent_entries: tuple[EditionEntryV7, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV8EnrollmentOrigin]


PARENT_ALPHA_V7_COUNT = 1_017
PARENT_ALPHA_V7_ENROLLMENT_SHA256 = (
    "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c"
)
PARENT_ALPHA_V7_IDENTITY_SHA256 = (
    "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff"
)
BERTRAND_V8_START_INDEX = PARENT_ALPHA_V7_COUNT
BERTRAND_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-choose-central-binomial-tranche-rfc-v1.md"
)


BERTRAND_V8_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV8, ...] = (
    # Microbatch one: recurrence-defined Choose foundation and initial laws.
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_foundation_candidate",
        "make_bertrand_choose_foundation_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_foundation_candidate.py",
        (
            "beta_pascal_zero_row_extend",
            "beta_pascal_zero_row_exists",
            "beta_pascal_row_step_extend",
            "beta_pascal_row_step_exists",
            "beta_pascal_table_prefix_extend",
            "beta_pascal_table_prefix_exists",
            "choose_exists",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_row_functional_candidate",
        "make_bertrand_choose_row_functional_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_row_functional_candidate.py",
        (
            "beta_pascal_zero_row_pointwise_functional",
            "beta_pascal_row_step_pointwise_functional",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_table_row_functional_candidate",
        "make_bertrand_choose_table_row_functional_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_choose_table_row_functional_candidate.py"
        ),
        ("beta_pascal_table_row_pointwise_functional",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_laws_candidate",
        "make_bertrand_choose_laws_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_laws_candidate.py",
        (
            "choose_functional",
            "choose_out_of_range_zero",
            "choose_zero",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_diagonal_candidate",
        "make_bertrand_choose_diagonal_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_diagonal_candidate.py",
        (
            "beta_pascal_table_diagonal_boundary",
            "choose_self",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_recurrence_candidate",
        "make_bertrand_choose_recurrence_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_recurrence_candidate.py",
        (
            "beta_pascal_table_successor_cell_recurrence",
            "choose_succ_succ_of_lt",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_pascal_candidate",
        "make_bertrand_choose_pascal_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_pascal_candidate.py",
        ("choose_succ_succ",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_symmetry_candidate",
        "make_bertrand_choose_symmetry_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_symmetry_candidate.py",
        (
            "choose_self_of_eq",
            "choose_symmetry",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_positive_candidate",
        "make_bertrand_choose_positive_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_positive_candidate.py",
        ("choose_positive",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_candidate",
        "make_bertrand_central_binom_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_candidate.py",
        (
            "central_binom_exists",
            "central_binom_functional",
            "central_binom_positive",
        ),
    ),
    # Microbatch two: central-binomial recurrence and lower-bound bridge.
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_zero_candidate",
        "make_bertrand_central_binom_zero_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_zero_candidate.py",
        ("central_binom_zero",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_succ_candidate",
        "make_bertrand_central_binom_succ_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_succ_candidate.py",
        (
            "choose_upper_eq_transport",
            "central_binom_succ_double_middle",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_weighted_vertical_candidate",
        "make_bertrand_choose_weighted_vertical_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_choose_weighted_vertical_candidate.py",
        ("choose_weighted_vertical",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_recurrence_candidate",
        "make_bertrand_central_binom_recurrence_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_recurrence_candidate.py"
        ),
        ("central_binom_succ_recurrence",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_factorial_support_candidate",
        "make_bertrand_choose_factorial_support_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_choose_factorial_support_candidate.py"
        ),
        (
            "factorial_length_eq_transport",
            "factorial_weighted_product_combine",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_choose_factorial_bridge_candidate",
        "make_bertrand_choose_factorial_bridge_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_choose_factorial_bridge_candidate.py"
        ),
        ("choose_factorial_bridge",),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_growth_candidate",
        "make_bertrand_central_binom_growth_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_growth_candidate.py",
        (
            "mul_lt_mul_right_nonzero",
            "four_power_central_recurrence_step",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_lower_seed_candidate",
        "make_bertrand_central_binom_lower_seed_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_lower_seed_candidate.py"
        ),
        (
            "pow_four_four_exact",
            "central_binom_four_weighted_of_recurrence",
            "four_pow_central_seed_package",
        ),
    ),
    EnrollmentSourceV8(
        BertrandV8EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_lower_bound_candidate",
        "make_bertrand_central_binom_lower_bound_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_lower_bound_candidate.py"
        ),
        ("four_pow_lt_mul_central_binom",),
    ),
)

BERTRAND_V8_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V8_EXPECTED_COUNTS = (
    7,
    2,
    1,
    3,
    2,
    2,
    1,
    2,
    1,
    3,
    1,
    2,
    1,
    1,
    2,
    1,
    2,
    3,
    1,
)
BERTRAND_V8_EXPECTED_MICROBATCH_SOURCE_COUNTS = (10, 9)
BERTRAND_V8_MICROBATCH_COUNTS = (24, 14)
BERTRAND_V8_MICROBATCH_NAMES = (
    BERTRAND_V8_EXPECTED_NAMES[: BERTRAND_V8_MICROBATCH_COUNTS[0]],
    BERTRAND_V8_EXPECTED_NAMES[BERTRAND_V8_MICROBATCH_COUNTS[0] :],
)
BERTRAND_V8_EXPECTED_COUNT = 38


def _load_source(source: EnrollmentSourceV8) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV8EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV8EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    produced_names = tuple(spec.name for spec in produced)
    if produced_names != source.names:
        raise AlphaV8EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: "
            f"{produced_names!r}"
        )
    if len(set(produced_names)) != len(produced_names):
        raise AlphaV8EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v8_enrollment() -> AlphaV8Enrollment:
    """Return the exact v7 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V7_ENTRIES) != PARENT_ALPHA_V7_COUNT:
        raise AlphaV8EnrollmentError("Alpha v7 parent count changed")
    if ALPHA_V7_ENROLLMENT_SHA256 != PARENT_ALPHA_V7_ENROLLMENT_SHA256:
        raise AlphaV8EnrollmentError("Alpha v7 enrollment identity changed")
    if ALPHA_V7_IDENTITY_SHA256 != PARENT_ALPHA_V7_IDENTITY_SHA256:
        raise AlphaV8EnrollmentError("Alpha v7 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V7_ENTRIES}
    if len(available) != PARENT_ALPHA_V7_COUNT:
        raise AlphaV8EnrollmentError("Alpha v7 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV8EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV8EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV8EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV8EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V8_EXPECTED_NAMES:
        raise AlphaV8EnrollmentError("Bertrand v8 append order changed")
    source_counts = tuple(
        len(source.names) for source in BERTRAND_V8_BODY_ENROLLMENT_MANIFEST
    )
    if source_counts != BERTRAND_V8_EXPECTED_COUNTS:
        raise AlphaV8EnrollmentError("Bertrand v8 source-block counts changed")
    first_sources, second_sources = BERTRAND_V8_EXPECTED_MICROBATCH_SOURCE_COUNTS
    if first_sources + second_sources != len(source_counts):
        raise AlphaV8EnrollmentError("Bertrand v8 microbatch boundary changed")
    microbatch_counts = (
        sum(source_counts[:first_sources]),
        sum(source_counts[first_sources:]),
    )
    if microbatch_counts != BERTRAND_V8_MICROBATCH_COUNTS:
        raise AlphaV8EnrollmentError("Bertrand v8 microbatch row counts changed")
    first_row_count = BERTRAND_V8_MICROBATCH_COUNTS[0]
    microbatch_names = (
        tuple(spec.name for spec in result[:first_row_count]),
        tuple(spec.name for spec in result[first_row_count:]),
    )
    if microbatch_names != BERTRAND_V8_MICROBATCH_NAMES:
        raise AlphaV8EnrollmentError("Bertrand v8 microbatch order changed")
    if len(result) != BERTRAND_V8_EXPECTED_COUNT:
        raise AlphaV8EnrollmentError("Bertrand v8 append count changed")
    return AlphaV8Enrollment(
        parent_entries=ALPHA_V7_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV8Enrollment",
    "AlphaV8EnrollmentError",
    "BERTRAND_RFC_PATH",
    "BERTRAND_V8_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V8_EXPECTED_COUNT",
    "BERTRAND_V8_EXPECTED_COUNTS",
    "BERTRAND_V8_EXPECTED_MICROBATCH_SOURCE_COUNTS",
    "BERTRAND_V8_EXPECTED_NAMES",
    "BERTRAND_V8_MICROBATCH_COUNTS",
    "BERTRAND_V8_MICROBATCH_NAMES",
    "BERTRAND_V8_START_INDEX",
    "BertrandV8EnrollmentOrigin",
    "EnrollmentSourceV8",
    "PARENT_ALPHA_V7_COUNT",
    "PARENT_ALPHA_V7_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V7_IDENTITY_SHA256",
    "alpha_v8_enrollment",
]
