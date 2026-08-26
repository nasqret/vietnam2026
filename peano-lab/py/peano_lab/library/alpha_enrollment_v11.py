"""Code-owned append manifest for the Bertrand Alpha-v11 tranche.

Alpha v10 is an immutable 1,085-row parent.  This module appends exactly
thirty-eight reviewed Primorial, central-binomial, and prime-support rows in
two dependency-topological microbatches of twenty and eighteen rows.
Enrollment records dependency-curried body evidence only; it never admits an
empty-context theorem or grants checked use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v10 import (
    ALPHA_ENTRIES as ALPHA_V10_ENTRIES,
    ALPHA_V10_ENROLLMENT_SHA256,
    ALPHA_V10_IDENTITY_SHA256,
    EditionEntry as EditionEntryV10,
)
from .theorems import TheoremSpec


class AlphaV11EnrollmentError(ValueError):
    """The frozen v10 parent or reviewed thirty-eight-row append is invalid."""


class BertrandV11EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v11 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV11:
    """One exact candidate factory and its executable audit sources."""

    origin: BertrandV11EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    rfc_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV11Enrollment:
    """The sealed v10 parent and exact thirty-eight-row Bertrand append."""

    parent_entries: tuple[EditionEntryV10, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV11EnrollmentOrigin]


PARENT_ALPHA_V10_COUNT = 1_085
PARENT_ALPHA_V10_ENROLLMENT_SHA256 = (
    "c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f"
)
PARENT_ALPHA_V10_IDENTITY_SHA256 = (
    "1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d"
)
BERTRAND_V11_START_INDEX = PARENT_ALPHA_V10_COUNT
BERTRAND_PRIMORIAL_DUPLICATE_FREE_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-duplicate-free-tranche-rfc-v1.md"
)
BERTRAND_PRIMORIAL_CHOOSE_INTERVAL_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-choose-interval-tranche-rfc-v1.md"
)
BERTRAND_CENTRAL_BINOMIAL_UPPER_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-central-binomial-upper-tranche-rfc-v1.md"
)
BERTRAND_PRIMORIAL_FOUR_POWER_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-four-power-tranche-rfc-v1.md"
)
BERTRAND_CENTRAL_PRIME_SUPPORT_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-central-prime-support-tranche-rfc-v1.md"
)
BERTRAND_RFC_PATHS = (
    BERTRAND_PRIMORIAL_DUPLICATE_FREE_RFC_PATH,
    BERTRAND_PRIMORIAL_CHOOSE_INTERVAL_RFC_PATH,
    BERTRAND_CENTRAL_BINOMIAL_UPPER_RFC_PATH,
    BERTRAND_PRIMORIAL_FOUR_POWER_RFC_PATH,
    BERTRAND_CENTRAL_PRIME_SUPPORT_RFC_PATH,
)


BERTRAND_V11_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV11, ...] = (
    EnrollmentSourceV11(
        BertrandV11EnrollmentOrigin.BERTRAND,
        "bertrand_primorial_duplicate_free_candidate",
        "make_bertrand_primorial_duplicate_free_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_primorial_duplicate_free_candidate.py",
        BERTRAND_PRIMORIAL_DUPLICATE_FREE_RFC_PATH,
        (
            "beta_distinct_empty",
            "beta_distinct_succ_intro",
            "beta_distinct_succ_elim_prefix",
            "beta_distinct_succ_last_ne",
            "beta_distinct_transport",
            "beta_distinct_prime_product_coprime_last",
            "beta_distinct_prime_product_divides_common_multiple",
            "beta_bounded_prime_prefix_divides_primorial_pointwise",
            "beta_distinct_bounded_prime_product_divides_primorial",
            "beta_distinct_bounded_prime_product_le_primorial",
        ),
    ),
    EnrollmentSourceV11(
        BertrandV11EnrollmentOrigin.BERTRAND,
        "bertrand_primorial_choose_interval_candidate",
        "make_bertrand_primorial_choose_interval_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_primorial_choose_interval_candidate.py",
        BERTRAND_PRIMORIAL_CHOOSE_INTERVAL_RFC_PATH,
        (
            "factorial_prime_divides_of_le",
            "factorial_prime_le_of_divides",
            "choose_prime_divides_between",
            "beta_pairwise_coprime_product_divides_common_multiple",
            "primorial_interval_pairwise_coprime",
            "primorial_interval_divides_choose_between",
            "primorial_even_interval_divides_central",
            "primorial_odd_interval_divides_middle",
            "primorial_even_interval_le_central",
            "primorial_odd_interval_le_middle",
        ),
    ),
    EnrollmentSourceV11(
        BertrandV11EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_upper_candidate",
        "make_bertrand_central_binom_upper_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_upper_candidate.py",
        BERTRAND_CENTRAL_BINOMIAL_UPPER_RFC_PATH,
        (
            "central_binom_strong_upper_step",
            "central_binom_recurrence_double_bundle",
            "central_binom_strong_upper_of_laws",
            "central_binom_upper_support_package",
            "central_binom_strong_upper",
            "central_binom_odd_middle_le_four_pow",
        ),
    ),
    EnrollmentSourceV11(
        BertrandV11EnrollmentOrigin.BERTRAND,
        "bertrand_primorial_four_power_candidate",
        "make_bertrand_primorial_four_power_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_primorial_four_power_candidate.py",
        BERTRAND_PRIMORIAL_FOUR_POWER_RFC_PATH,
        (
            "primorial_one",
            "double_half_predecessor_data",
            "odd_positive_prefix_predecessor_bound",
            "central_binom_nonzero_strong_upper",
            "primorial_four_power_support_package",
            "primorial_le_four_pow_bounded",
            "primorial_le_four_pow",
        ),
    ),
    EnrollmentSourceV11(
        BertrandV11EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_prime_support_candidate",
        "make_bertrand_central_binom_prime_support_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_prime_support_candidate.py"
        ),
        BERTRAND_CENTRAL_PRIME_SUPPORT_RFC_PATH,
        (
            "central_binom_prime_divisor_le_double",
            "no_bertrand_central_prime_divisor_le",
            "power_valuation_nonzero_exponent_divides_base",
            "prime_divisor_power_valuation_nonzero",
            "no_bertrand_central_prime_divisor_ranges",
        ),
    ),
)

BERTRAND_V11_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V11_EXPECTED_COUNTS = (10, 10, 6, 7, 5)
BERTRAND_V11_EXPECTED_MICROBATCH_SOURCE_COUNTS = (2, 3)
BERTRAND_V11_MICROBATCH_COUNTS = (20, 18)
BERTRAND_V11_MICROBATCH_NAMES = (
    BERTRAND_V11_EXPECTED_NAMES[:20],
    BERTRAND_V11_EXPECTED_NAMES[20:],
)
BERTRAND_V11_EXPECTED_COUNT = 38


def _load_source(source: EnrollmentSourceV11) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV11EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV11EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    produced_names = tuple(spec.name for spec in produced)
    if produced_names != source.names:
        raise AlphaV11EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: "
            f"{produced_names!r}"
        )
    if len(set(produced_names)) != len(produced_names):
        raise AlphaV11EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v11_enrollment() -> AlphaV11Enrollment:
    """Return the exact v10 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V10_ENTRIES) != PARENT_ALPHA_V10_COUNT:
        raise AlphaV11EnrollmentError("Alpha v10 parent count changed")
    if ALPHA_V10_ENROLLMENT_SHA256 != PARENT_ALPHA_V10_ENROLLMENT_SHA256:
        raise AlphaV11EnrollmentError("Alpha v10 enrollment identity changed")
    if ALPHA_V10_IDENTITY_SHA256 != PARENT_ALPHA_V10_IDENTITY_SHA256:
        raise AlphaV11EnrollmentError("Alpha v10 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V10_ENTRIES}
    if len(available) != PARENT_ALPHA_V10_COUNT:
        raise AlphaV11EnrollmentError("Alpha v10 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV11EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV11EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV11EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV11EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            rfc_by_name[spec.name] = source.rfc_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V11_EXPECTED_NAMES:
        raise AlphaV11EnrollmentError("Bertrand v11 append order changed")
    source_counts = tuple(
        len(source.names) for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
    )
    if source_counts != BERTRAND_V11_EXPECTED_COUNTS:
        raise AlphaV11EnrollmentError("Bertrand v11 source-block counts changed")
    source_boundaries = BERTRAND_V11_EXPECTED_MICROBATCH_SOURCE_COUNTS
    if sum(source_boundaries) != len(source_counts):
        raise AlphaV11EnrollmentError("Bertrand v11 microbatch boundary changed")
    microbatch_counts: list[int] = []
    offset = 0
    for source_count in source_boundaries:
        microbatch_counts.append(sum(source_counts[offset : offset + source_count]))
        offset += source_count
    if tuple(microbatch_counts) != BERTRAND_V11_MICROBATCH_COUNTS:
        raise AlphaV11EnrollmentError("Bertrand v11 microbatch row counts changed")
    microbatch_names: list[tuple[str, ...]] = []
    offset = 0
    for row_count in BERTRAND_V11_MICROBATCH_COUNTS:
        microbatch_names.append(
            tuple(spec.name for spec in result[offset : offset + row_count])
        )
        offset += row_count
    if tuple(microbatch_names) != BERTRAND_V11_MICROBATCH_NAMES:
        raise AlphaV11EnrollmentError("Bertrand v11 microbatch order changed")
    source_rfc_paths = tuple(
        dict.fromkeys(
            source.rfc_path
            for source in BERTRAND_V11_BODY_ENROLLMENT_MANIFEST
        )
    )
    if source_rfc_paths != BERTRAND_RFC_PATHS:
        raise AlphaV11EnrollmentError("Bertrand v11 RFC binding changed")
    if len(result) != BERTRAND_V11_EXPECTED_COUNT:
        raise AlphaV11EnrollmentError("Bertrand v11 append count changed")
    return AlphaV11Enrollment(
        parent_entries=ALPHA_V10_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV11Enrollment",
    "AlphaV11EnrollmentError",
    "BERTRAND_CENTRAL_BINOMIAL_UPPER_RFC_PATH",
    "BERTRAND_CENTRAL_PRIME_SUPPORT_RFC_PATH",
    "BERTRAND_PRIMORIAL_CHOOSE_INTERVAL_RFC_PATH",
    "BERTRAND_PRIMORIAL_DUPLICATE_FREE_RFC_PATH",
    "BERTRAND_PRIMORIAL_FOUR_POWER_RFC_PATH",
    "BERTRAND_RFC_PATHS",
    "BERTRAND_V11_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V11_EXPECTED_COUNT",
    "BERTRAND_V11_EXPECTED_COUNTS",
    "BERTRAND_V11_EXPECTED_MICROBATCH_SOURCE_COUNTS",
    "BERTRAND_V11_EXPECTED_NAMES",
    "BERTRAND_V11_MICROBATCH_COUNTS",
    "BERTRAND_V11_MICROBATCH_NAMES",
    "BERTRAND_V11_START_INDEX",
    "BertrandV11EnrollmentOrigin",
    "EnrollmentSourceV11",
    "PARENT_ALPHA_V10_COUNT",
    "PARENT_ALPHA_V10_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V10_IDENTITY_SHA256",
    "alpha_v11_enrollment",
]
