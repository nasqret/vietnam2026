"""Code-owned append manifest for the Bertrand Alpha-v12 tranche.

Alpha v11 is an immutable 1,123-row parent. This module appends exactly one
hundred eighty reviewed Bertrand rows in nine dependency-topological
microbatches of twenty rows.
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

from .editions_v11 import (
    ALPHA_ENTRIES as ALPHA_V11_ENTRIES,
    ALPHA_V11_ENROLLMENT_SHA256,
    ALPHA_V11_IDENTITY_SHA256,
    EditionEntry as EditionEntryV11,
)
from .theorems import TheoremSpec


class AlphaV12EnrollmentError(ValueError):
    """The frozen v11 parent or reviewed 180-row append is invalid."""


class BertrandV12EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v12 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV12:
    """One exact candidate factory and its executable audit sources."""

    origin: BertrandV12EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    rfc_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV12Enrollment:
    """The sealed v11 parent and exact 180-row Bertrand append."""

    parent_entries: tuple[EditionEntryV11, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV12EnrollmentOrigin]


PARENT_ALPHA_V11_COUNT = 1_123
PARENT_ALPHA_V11_ENROLLMENT_SHA256 = (
    "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36"
)
PARENT_ALPHA_V11_IDENTITY_SHA256 = (
    "46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3"
)
BERTRAND_V12_START_INDEX = PARENT_ALPHA_V11_COUNT
BERTRAND_B6_RELEASE_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-b6-release-tranche-rfc-v1.md"
)
BERTRAND_B5_ORDER_QUOTIENT_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-order-quotient-tranche-rfc-v1.md"
)
BERTRAND_B5_CENTRAL_VALUATION_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-central-valuation-tranche-rfc-v1.md"
)
BERTRAND_B5_CENTRAL_CARRY_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-central-carry-tranche-rfc-v1.md"
)
BERTRAND_B5_SQUARE_TAIL_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-square-tail-tranche-rfc-v1.md"
)
BERTRAND_B5_ZERO_TWO_THIRDS_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-zero-two-thirds-tranche-rfc-v1.md"
)
BERTRAND_B5_FACTOR_RANGES_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-factor-ranges-tranche-rfc-v1.md"
)
BERTRAND_B5_PRIME_CONTRIBUTION_FOUNDATION_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-prime-contribution-foundation-tranche-rfc-v1.md"
)
BERTRAND_B5_PRIME_CONTRIBUTION_COMPLETENESS_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-prime-contribution-completeness-tranche-rfc-v1.md"
)
BERTRAND_B5_RANGE_BOUNDARIES_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-range-boundaries-tranche-rfc-v1.md"
)
BERTRAND_B5_CONTRIBUTION_SPLIT_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-contribution-split-tranche-rfc-v1.md"
)
BERTRAND_B5_CENTRAL_UPPER_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-central-upper-tranche-rfc-v1.md"
)
BERTRAND_B7_EVENTUAL_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b7-eventual-tranche-rfc-v1.md"
)
BERTRAND_B8_PRIME_CERTIFICATES_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b8-prime-certificates-tranche-rfc-v1.md"
)
BERTRAND_B8_COVERING_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b8-covering-tranche-rfc-v1.md"
)
BERTRAND_B8_SMALL_RANGE_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b8-small-range-tranche-rfc-v1.md"
)
BERTRAND_BP01_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-bp01-tranche-rfc-v1.md"
)
BERTRAND_BP02_RFC_PATH = (
    "research/arithmetic-library/ha-bertrand-bp02-tranche-rfc-v1.md"
)
BERTRAND_RFC_PATHS = (
    BERTRAND_B6_RELEASE_RFC_PATH,
    BERTRAND_B5_ORDER_QUOTIENT_RFC_PATH,
    BERTRAND_B5_CENTRAL_VALUATION_RFC_PATH,
    BERTRAND_B5_CENTRAL_CARRY_RFC_PATH,
    BERTRAND_B5_SQUARE_TAIL_RFC_PATH,
    BERTRAND_B5_ZERO_TWO_THIRDS_RFC_PATH,
    BERTRAND_B5_FACTOR_RANGES_RFC_PATH,
    BERTRAND_B5_PRIME_CONTRIBUTION_FOUNDATION_RFC_PATH,
    BERTRAND_B5_PRIME_CONTRIBUTION_COMPLETENESS_RFC_PATH,
    BERTRAND_B5_RANGE_BOUNDARIES_RFC_PATH,
    BERTRAND_B5_CONTRIBUTION_SPLIT_RFC_PATH,
    BERTRAND_B5_CENTRAL_UPPER_RFC_PATH,
    BERTRAND_B7_EVENTUAL_RFC_PATH,
    BERTRAND_B8_PRIME_CERTIFICATES_RFC_PATH,
    BERTRAND_B8_COVERING_RFC_PATH,
    BERTRAND_B8_SMALL_RANGE_RFC_PATH,
    BERTRAND_BP01_RFC_PATH,
    BERTRAND_BP02_RFC_PATH,
)


BERTRAND_V12_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV12, ...] = (
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_hj_base_thirty_two_candidate",
        "make_bertrand_hj_base_thirty_two_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_hj_base_thirty_two_candidate.py"
        ),
        BERTRAND_B6_RELEASE_RFC_PATH,
        (
            "pow_block_bound_from_total",
            "pow_three_five_le_pow_four_four_from_total",
            "pow_eleven_two_le_pow_two_seven_from_total",
            "pow_six_ten_le_pow_four_thirteen_from_total",
            "linear_square_budget",
            "bertrand_scaled_budget_root_32",
            "bertrand_scaled_budget_root_33",
            "bertrand_scaled_budget_root_34",
            "bertrand_scaled_budget_root_35",
            "bertrand_scaled_budget_root_36",
            "bertrand_scaled_budget_root_37",
            "ceil_div_six_budget_of_scaled_le",
            "pow_six_six_le_pow_four_eight_from_total",
            "pow_six_four_le_pow_four_six_from_total",
            "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total",
            "pow_two_double_eq_pow_four_from_total",
            "pow_two_successor_double_le_pow_four_successor_from_total",
            "pow_eleven_double_block_le_pow_two_seven_block_from_total",
            "pow_eleven_double_block_le_pow_four_even_from_total",
            "pow_eleven_double_block_le_pow_four_odd_from_total",
            "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
            "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
            "bertrand_h_root_32_from_total",
            "bertrand_h_root_33_from_total",
            "bertrand_h_root_34_from_total",
            "bertrand_h_root_35_from_total",
            "bertrand_h_root_36_from_total",
            "bertrand_h_root_37_from_total",
            "bertrand_j_base_thirty_two_window_from_total",
            "bertrand_hj_base_window_thirty_two_from_total",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_hj_all_s_candidate",
        "make_bertrand_hj_all_s_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_hj_all_s_candidate.py",
        BERTRAND_B6_RELEASE_RFC_PATH,
        (
            "scaled_factor_square_identity",
            "thirty_two_square_eq_twice_sixteen_times_thirty_two",
            "floor_sqrt_factorized_threshold_thirty_two",
            "six_block_window_decomposition_above_thirty_two",
            "bertrand_hj_six_block_iterate_from_total",
            "bertrand_hj_envelope_thirty_two",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b6_growth_candidate",
        "make_bertrand_b6_growth_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b6_growth_candidate.py",
        BERTRAND_B6_RELEASE_RFC_PATH,
        (
            "bertrand_floor_power_product_le_h_from_total",
            "bertrand_four_power_product_le_of_sum_from_total",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b6_main_inequality_candidate",
        "make_bertrand_b6_main_inequality_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b6_layered_closure.py",
        BERTRAND_B6_RELEASE_RFC_PATH,
        (
            "bertrand_main_inequality_factorized_from_total",
            "bertrand_main_inequality_factorized",
            "bertrand_main_inequality_nat",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "finite_product_order_candidate",
        "make_finite_product_order_candidate_theorems",
        "peano-lab/py/tests/test_finite_product_order_candidate.py",
        BERTRAND_B6_RELEASE_RFC_PATH,
        (
            "beta_product_pointwise_le",
            "beta_product_uniform_le_pow",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b5_order_quotient_candidate",
        "make_bertrand_b5_order_quotient_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b5_order_quotient_candidate.py",
        BERTRAND_B5_ORDER_QUOTIENT_RFC_PATH,
        (
            "add_lt_add",
            "add_lt_cancel_left",
            "beta_sum_pointwise_le",
            "beta_sum_uniform_le_mul",
            "division_zero_quotient_of_lt",
            "division_double_quotient_bit",
            "division_double_quotient_lower",
            "division_double_quotient_upper",
            "pow_le_pow_of_exponent_le",
            "pow_tail_strict_of_square",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_valuation_candidate",
        "make_bertrand_central_binom_valuation_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_valuation_candidate.py",
        BERTRAND_B5_CENTRAL_VALUATION_RFC_PATH,
        (
            "power_valuation_value_eq_transport",
            "central_binom_factorial_valuation_balance",
            "central_binom_legendre_valuation_balance",
            "prime_power_quotient_zero_of_exponent_gt",
            "power_quotient_prefix_tail_entry_zero",
            "power_quotient_prefix_sum_extend_zero",
            "legendre_sum_extended_prefix_exists",
            "power_quotient_double_pointwise_upper",
            "beta_sum_pointwise_double_succ_le",
            "central_binom_prime_valuation_le_double",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_carry_candidate",
        "make_bertrand_central_binom_carry_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_central_binom_carry_candidate.py",
        BERTRAND_B5_CENTRAL_CARRY_RFC_PATH,
        (
            "double_quotient_carry_choice",
            "double_quotient_carry_prefix_extend",
            "double_quotient_carry_prefix_exists",
            "double_quotient_carry_prefix_all_bits",
            "double_quotient_carry_prefix_restrict",
            "bit_count_positive_last_one",
            "division_successor_quotient_divisor_le",
            "beta_sum_double_carry_exact",
            "central_binom_carry_bit_count",
            "central_binom_prime_power_contribution_le_double",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_square_tail_candidate",
        "make_bertrand_central_binom_square_tail_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_square_tail_candidate.py"
        ),
        BERTRAND_B5_SQUARE_TAIL_RFC_PATH,
        (
            "central_binom_prime_square_tail_exponent_not_two_le",
            "central_binom_prime_square_tail_valuation_le_one",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_zero_range_candidate",
        "make_bertrand_central_binom_zero_range_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_zero_range_candidate.py"
        ),
        BERTRAND_B5_ZERO_TWO_THIRDS_RFC_PATH,
        (
            "division_quotient_one_of_bounds",
            "division_quotient_two_of_bounds",
            "prime_square_tail_of_two_three_range",
            "division_first_two_of_two_three_range",
            "double_quotient_carry_prefix_entries_zero",
            "central_binom_prime_valuation_zero_of_exact_double_quotients",
            "central_binom_prime_valuation_zero_two_thirds_range",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_central_binom_factor_ranges_candidate",
        "make_bertrand_central_binom_factor_ranges_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_central_binom_factor_ranges_candidate.py"
        ),
        BERTRAND_B5_FACTOR_RANGES_RFC_PATH,
        (
            "division_three_scaled_upper_of_quotient_lt",
            "central_binom_prime_valuation_zero_above_third_quotient",
            "floor_sqrt_above_root_power_two_strict",
            "central_binom_prime_above_floor_sqrt_valuation_le_one",
            "no_bertrand_central_nonzero_valuation_live_ranges",
            "no_bertrand_central_nonzero_valuation_factor_ranges",
            "no_bertrand_central_nonzero_contribution_factor_ranges",
            "no_bertrand_central_prime_contribution_ranges",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_prime_contribution_candidate",
        "make_bertrand_prime_contribution_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_prime_contribution_candidate.py",
        BERTRAND_B5_PRIME_CONTRIBUTION_FOUNDATION_RFC_PATH,
        (
            "prime_contribution_choice_exists",
            "prime_contribution_choice_functional",
            "prime_contribution_prefix_extend",
            "prime_contribution_prefix_exists",
            "prime_contribution_prefix_transport_entry",
            "prime_contribution_product_exists",
            "prime_contribution_product_functional",
            "coprime_power_right",
            "coprime_powers",
            "prime_contribution_prefix_pairwise_coprime",
            "prime_contribution_factor_divides",
            "prime_contribution_product_divides",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_prime_contribution_complete_candidate",
        "make_bertrand_prime_contribution_complete_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_prime_contribution_complete_candidate.py"
        ),
        BERTRAND_B5_PRIME_CONTRIBUTION_COMPLETENESS_RFC_PATH,
        (
            "prime_contribution_selected_entry",
            "prime_contribution_selected_successor_divides",
            "prime_contribution_cofactor_prime_contradiction",
            "prime_contribution_cofactor_eq_one",
            "prime_contribution_reverse_divides",
            "prime_contribution_product_eq",
            "prime_contribution_complete_exists",
            "central_binom_prime_contribution_product_exists",
            "no_bertrand_central_contribution_choice_ranges",
            "no_bertrand_central_contribution_prefix_ranges",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b5_range_boundaries_candidate",
        "make_bertrand_b5_range_boundaries_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b5_range_boundaries_candidate.py",
        BERTRAND_B5_RANGE_BOUNDARIES_RFC_PATH,
        (
            "two_lt_double_lower_six",
            "floor_sqrt_two_le_of_two_lt",
            "three_mul_le_square_of_three_le",
            "floor_sqrt_three_mul_le_double",
            "division_quotient_lower_of_scaled_le",
            "floor_sqrt_le_third_quotient",
            "floor_sqrt_third_quotient_gap_exists",
            "division_quotient_le_dividend",
            "third_quotient_double_gap_exists",
            "floor_third_double_gap_package",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b5_contribution_split_candidate",
        "make_bertrand_b5_contribution_split_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_b5_contribution_split_candidate.py"
        ),
        BERTRAND_B5_CONTRIBUTION_SPLIT_RFC_PATH,
        (
            "prime_contribution_interval_prefix_extend",
            "prime_contribution_interval_prefix_exists",
            "prime_contribution_interval_prefix_transport_entry",
            "prime_contribution_interval_exists",
            "prime_contribution_interval_functional",
            "prime_contribution_interval_prefix_shift",
            "prime_contribution_prefix_restrict_add",
            "prime_contribution_prefix_interval_split",
            "prime_contribution_product_length_eq_transport",
            "prime_contribution_three_range_split",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b5_central_upper_candidate",
        "make_bertrand_b5_central_upper_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b5_central_upper_candidate.py",
        BERTRAND_B5_CENTRAL_UPPER_RFC_PATH,
        (
            "beta_product_all_one_exact",
            "no_bertrand_small_contribution_choice_le_double",
            "no_bertrand_middle_contribution_choice_le_selector",
            "no_bertrand_high_contribution_choice_eq_one",
            "no_bertrand_small_contribution_product_le_power",
            "no_bertrand_middle_contribution_interval_le_primorial_interval",
            "no_bertrand_middle_contribution_interval_le_four_pow",
            "no_bertrand_high_contribution_interval_eq_one",
            "central_binom_factorization_small",
            "central_binom_le_of_no_bertrand_prime",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b7_eventual_candidate",
        "make_bertrand_b7_eventual_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b7_eventual_candidate.py",
        BERTRAND_B7_EVENTUAL_RFC_PATH,
        ("bertrand_eventually_closed_upper",),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b8_prime_certificates_candidate",
        "make_bertrand_b8_prime_certificate_candidate_theorems",
        (
            "peano-lab/py/tests/"
            "test_bertrand_b8_prime_certificates_candidate.py"
        ),
        BERTRAND_B8_PRIME_CERTIFICATES_RFC_PATH,
        (
            "fixed_nontrivial_factor_not_prime",
            "factor_pair_has_small_member_below_square",
            "nonprime_has_small_prime_divisor_below_square",
            "prime_of_no_small_prime_divisor_below_square",
            "prime_le_twenty_two_cases",
            "nonzero_remainder_not_multiple",
            "scaled_remainder_lift",
            "add_remainder_lift",
            "double_scaled_remainder_lift",
            "prime_five",
            "prime_seven",
            "prime_thirteen",
            "prime_twenty_three",
            "prime_forty_three",
            "prime_eighty_three",
            "prime_one_hundred_sixty_three",
            "prime_three_hundred_seventeen",
            "prime_five_hundred_twenty_one",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b8_covering_candidate",
        "make_bertrand_b8_covering_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b8_covering_candidate.py",
        BERTRAND_B8_COVERING_RFC_PATH,
        (
            "bertrand_add_swap_nested",
            "bertrand_add_six_permute",
            "bertrand_covering_interval",
            "bertrand_cover_one_two",
            "bertrand_cover_two_three",
            "bertrand_cover_three_five",
            "bertrand_cover_five_seven",
            "bertrand_cover_seven_thirteen",
            "bertrand_cover_thirteen_twenty_three",
            "bertrand_cover_twenty_three_forty_three",
            "bertrand_cover_forty_three_eighty_three",
            "bertrand_cover_eighty_three_one_hundred_sixty_three",
            "bertrand_cover_one_hundred_sixty_three_three_hundred_seventeen",
            "bertrand_cover_three_hundred_seventeen_five_hundred_twenty_one",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_b8_small_candidate",
        "make_bertrand_b8_small_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_b8_small_candidate.py",
        BERTRAND_B8_SMALL_RANGE_RFC_PATH,
        (
            "bertrand_cutoff_lt_final_prime",
            "bertrand_small_closed_upper",
        ),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_bp01_candidate",
        "make_bertrand_bp01_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_bp01_candidate.py",
        BERTRAND_BP01_RFC_PATH,
        ("bertrand_closed_upper",),
    ),
    EnrollmentSourceV12(
        BertrandV12EnrollmentOrigin.BERTRAND,
        "bertrand_bp02_candidate",
        "make_bertrand_bp02_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_bp02_candidate.py",
        BERTRAND_BP02_RFC_PATH,
        (
            "bertrand_upper_endpoint_factorization",
            "bertrand_strict",
        ),
    ),
)

BERTRAND_V12_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V12_EXPECTED_COUNTS = (
    30,
    6,
    2,
    3,
    2,
    10,
    10,
    10,
    2,
    7,
    8,
    12,
    10,
    10,
    10,
    10,
    1,
    18,
    14,
    2,
    1,
    2,
)
BERTRAND_V12_MICROBATCH_COUNTS = (20,) * 9
BERTRAND_V12_MICROBATCH_NAMES = tuple(
    BERTRAND_V12_EXPECTED_NAMES[offset : offset + 20]
    for offset in range(0, 180, 20)
)
BERTRAND_V12_EXPECTED_COUNT = 180


def _load_source(source: EnrollmentSourceV12) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV12EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV12EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    produced_names = tuple(spec.name for spec in produced)
    if produced_names != source.names:
        raise AlphaV12EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: "
            f"{produced_names!r}"
        )
    if len(set(produced_names)) != len(produced_names):
        raise AlphaV12EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v12_enrollment() -> AlphaV12Enrollment:
    """Return the exact v11 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V11_ENTRIES) != PARENT_ALPHA_V11_COUNT:
        raise AlphaV12EnrollmentError("Alpha v11 parent count changed")
    if ALPHA_V11_ENROLLMENT_SHA256 != PARENT_ALPHA_V11_ENROLLMENT_SHA256:
        raise AlphaV12EnrollmentError("Alpha v11 enrollment identity changed")
    if ALPHA_V11_IDENTITY_SHA256 != PARENT_ALPHA_V11_IDENTITY_SHA256:
        raise AlphaV12EnrollmentError("Alpha v11 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V11_ENTRIES}
    if len(available) != PARENT_ALPHA_V11_COUNT:
        raise AlphaV12EnrollmentError("Alpha v11 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV12EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV12EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV12EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV12EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            rfc_by_name[spec.name] = source.rfc_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V12_EXPECTED_NAMES:
        raise AlphaV12EnrollmentError("Bertrand v12 append order changed")
    source_counts = tuple(
        len(source.names) for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
    )
    if source_counts != BERTRAND_V12_EXPECTED_COUNTS:
        raise AlphaV12EnrollmentError("Bertrand v12 source-block counts changed")
    if sum(BERTRAND_V12_MICROBATCH_COUNTS) != len(result):
        raise AlphaV12EnrollmentError("Bertrand v12 microbatch count changed")
    microbatch_names: list[tuple[str, ...]] = []
    offset = 0
    for row_count in BERTRAND_V12_MICROBATCH_COUNTS:
        microbatch_names.append(
            tuple(spec.name for spec in result[offset : offset + row_count])
        )
        offset += row_count
    if tuple(microbatch_names) != BERTRAND_V12_MICROBATCH_NAMES:
        raise AlphaV12EnrollmentError("Bertrand v12 microbatch order changed")
    source_rfc_paths = tuple(
        dict.fromkeys(
            source.rfc_path
            for source in BERTRAND_V12_BODY_ENROLLMENT_MANIFEST
        )
    )
    if source_rfc_paths != BERTRAND_RFC_PATHS:
        raise AlphaV12EnrollmentError("Bertrand v12 RFC binding changed")
    if len(result) != BERTRAND_V12_EXPECTED_COUNT:
        raise AlphaV12EnrollmentError("Bertrand v12 append count changed")
    return AlphaV12Enrollment(
        parent_entries=ALPHA_V11_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV12Enrollment",
    "AlphaV12EnrollmentError",
    "BERTRAND_B6_RELEASE_RFC_PATH",
    "BERTRAND_B5_CENTRAL_CARRY_RFC_PATH",
    "BERTRAND_B5_CENTRAL_UPPER_RFC_PATH",
    "BERTRAND_B5_CENTRAL_VALUATION_RFC_PATH",
    "BERTRAND_B5_CONTRIBUTION_SPLIT_RFC_PATH",
    "BERTRAND_B5_FACTOR_RANGES_RFC_PATH",
    "BERTRAND_B5_ORDER_QUOTIENT_RFC_PATH",
    "BERTRAND_B5_PRIME_CONTRIBUTION_COMPLETENESS_RFC_PATH",
    "BERTRAND_B5_PRIME_CONTRIBUTION_FOUNDATION_RFC_PATH",
    "BERTRAND_B5_RANGE_BOUNDARIES_RFC_PATH",
    "BERTRAND_B5_SQUARE_TAIL_RFC_PATH",
    "BERTRAND_B5_ZERO_TWO_THIRDS_RFC_PATH",
    "BERTRAND_B7_EVENTUAL_RFC_PATH",
    "BERTRAND_B8_COVERING_RFC_PATH",
    "BERTRAND_B8_PRIME_CERTIFICATES_RFC_PATH",
    "BERTRAND_B8_SMALL_RANGE_RFC_PATH",
    "BERTRAND_BP01_RFC_PATH",
    "BERTRAND_BP02_RFC_PATH",
    "BERTRAND_RFC_PATHS",
    "BERTRAND_V12_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V12_EXPECTED_COUNT",
    "BERTRAND_V12_EXPECTED_COUNTS",
    "BERTRAND_V12_EXPECTED_NAMES",
    "BERTRAND_V12_MICROBATCH_COUNTS",
    "BERTRAND_V12_MICROBATCH_NAMES",
    "BERTRAND_V12_START_INDEX",
    "BertrandV12EnrollmentOrigin",
    "EnrollmentSourceV12",
    "PARENT_ALPHA_V11_COUNT",
    "PARENT_ALPHA_V11_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V11_IDENTITY_SHA256",
    "alpha_v12_enrollment",
]
