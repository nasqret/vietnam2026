"""Bounded audit of the high-column Lucas zero-boundary candidates."""

from __future__ import annotations

from functools import lru_cache
from math import comb

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.lucas_block_digit_candidate import (
    LUCAS_ONE_STEP_DIVISION_CONGRUENCE,
    LUCAS_POSITIVE_LOWER_QUOTIENT_DIGIT_COEFFICIENT_ZERO,
    LUCAS_POSITIVE_LOWER_QUOTIENT_EXCEEDS_UPPER_DIGIT,
    LUCAS_PRIME_BLOCK_DIGIT_CONGRUENCE,
    LUCAS_ZERO_UPPER_QUOTIENT_HIGH_COLUMN_VANISHES,
    make_lucas_block_digit_candidate_theorems,
)
from peano_lab.library.lucas_low_digit_candidate import (
    make_lucas_low_digit_candidate_theorems,
)
from peano_lab.library.lucas_convolution_candidate import (
    make_lucas_convolution_candidate_theorems,
)
from peano_lab.library.lucas_digit_candidate import make_lucas_digit_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    LUCAS_POSITIVE_LOWER_QUOTIENT_EXCEEDS_UPPER_DIGIT,
    LUCAS_POSITIVE_LOWER_QUOTIENT_DIGIT_COEFFICIENT_ZERO,
    LUCAS_ZERO_UPPER_QUOTIENT_HIGH_COLUMN_VANISHES,
    LUCAS_PRIME_BLOCK_DIGIT_CONGRUENCE,
    LUCAS_ONE_STEP_DIVISION_CONGRUENCE,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_lucas_block_digit_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    rows = {row.name: row for row in editions_v12.ALPHA_SPECS}
    rows.update((row.name, row) for row in make_lucas_digit_candidate_theorems(TheoremSpec))
    rows.update((row.name, row) for row in make_lucas_convolution_candidate_theorems(TheoremSpec))
    rows.update((row.name, row) for row in make_lucas_low_digit_candidate_theorems(TheoremSpec))
    return rows


def test_high_column_candidates_are_ordered_first_order_and_release_isolated() -> None:
    seen: set[str] = set()
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in _specs_by_name()
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert set(row.dependencies) <= set(_core()) | seen
        seen.add(row.name)


def test_high_column_candidates_are_kernel_checked_and_bounded() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(row.proof_nodes for row in receipts) < 1200
    assert max(row.proof_depth for row in receipts) < 130


@pytest.mark.parametrize("base", (2, 3, 4, 5, 7, 11))
@pytest.mark.parametrize("lower_quotient", (1, 2, 4, 9))
def test_positive_lower_quotient_forces_out_of_range(
    base: int,
    lower_quotient: int,
) -> None:
    for upper_digit in range(base):
        for lower_digit in range(base):
            lower = base * lower_quotient + lower_digit
            assert upper_digit < lower
            assert (comb(upper_digit, lower) if lower <= upper_digit else 0) == 0


@pytest.mark.parametrize("base", (2, 3, 5, 7, 11))
@pytest.mark.parametrize("upper_quotient", (0, 1, 2, 4, 9))
@pytest.mark.parametrize("lower_quotient", (0, 1, 3))
def test_complete_lucas_prime_block_congruence_matches_all_digits(
    base: int,
    upper_quotient: int,
    lower_quotient: int,
) -> None:
    quotient_coefficient = (
        comb(upper_quotient, lower_quotient)
        if lower_quotient <= upper_quotient
        else 0
    )
    for upper_digit in range(base):
        for lower_digit in range(base):
            upper = base * upper_quotient + upper_digit
            lower = base * lower_quotient + lower_digit
            whole = comb(upper, lower) if lower <= upper else 0
            digit = (
                comb(upper_digit, lower_digit)
                if lower_digit <= upper_digit
                else 0
            )
            assert (whole - quotient_coefficient * digit) % base == 0
