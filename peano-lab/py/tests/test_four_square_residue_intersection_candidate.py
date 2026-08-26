"""Bounded kernel audit for odd-prime half-square intersection foundations."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.four_square_cross_pigeonhole_candidate import (
    make_four_square_cross_pigeonhole_candidate_theorems,
)
from peano_lab.library.four_square_residue_intersection_candidate import (
    make_four_square_residue_intersection_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "four_square_half_double_below_odd",
    "four_square_two_half_ranges_overflow_odd",
    "four_square_half_sum_below_odd",
    "four_square_bounded_multiple_is_zero",
    "four_square_ordered_square_difference_factor",
    "four_square_ordered_square_congruence_factors",
    "four_square_ordered_half_square_injective",
    "four_square_prime_half_square_residues_injective",
    "four_square_square_residue_prefix_exists",
    "four_square_square_residue_prefix_bounded",
    "four_square_equal_square_remainders_are_congruent",
    "four_square_half_square_residue_prefix_injective",
    "four_square_bounded_complement_prefix_exists",
    "four_square_complement_gap_symmetry",
    "four_square_complement_prefix_bounded",
    "four_square_complement_prefix_preserves_injectivity",
    "four_square_complementary_remainders_form_multiple",
    "four_square_odd_prime_modular_seed",
    "four_square_non_two_prime_modular_seed",
    "four_square_prime_modular_seed",
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_residue_intersection_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    rows = {row.name: row for row in editions_v12.ALPHA_SPECS}
    rows.update(
        (row.name, row)
        for row in make_four_square_cross_pigeonhole_candidate_theorems(TheoremSpec)
    )
    return rows


def test_four_square_intersection_rows_are_first_order_and_release_isolated() -> None:
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


def test_four_square_intersection_bodies_are_kernel_checked_and_bounded() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) == 193
    assert max(receipt.proof_depth for receipt in receipts) == 41
    odd = next(
        receipt for receipt in receipts if receipt.name == "four_square_odd_prime_modular_seed"
    )
    assert (odd.proof_nodes, odd.proof_depth) == (193, 39)
    universal = next(
        receipt for receipt in receipts if receipt.name == "four_square_prime_modular_seed"
    )
    assert (universal.proof_nodes, universal.proof_depth) == (95, 21)


def test_four_square_prime_seed_statements_have_pinned_hashes() -> None:
    by_name = {row.name: row for row in _rows()}
    assert sha256(by_name["four_square_odd_prime_modular_seed"].statement.encode()).hexdigest() == (
        "3e55824a272594c24c76d9044a4877bb3a75c10d101318dde5d6d928961bfeb2"
    )
    assert sha256(by_name["four_square_non_two_prime_modular_seed"].statement.encode()).hexdigest() == (
        "79e165ce9e984729b5e131898679e59a04391124a61da10d3c9cb2e9339d691e"
    )
    assert sha256(by_name["four_square_prime_modular_seed"].statement.encode()).hexdigest() == (
        "41b3138912bebce6b45a92e266f018ae7d5cae16d20c817ed20a8decbf14c833"
    )


@pytest.mark.parametrize("prime", (3, 5, 7, 11, 13, 17, 19, 23, 31, 43))
def test_odd_prime_half_squares_are_injective_and_intersect(prime: int) -> None:
    half = prime // 2
    first = {(value * value) % prime for value in range(half + 1)}
    second = {(-1 - value * value) % prime for value in range(half + 1)}
    assert len(first) == half + 1
    assert len(second) == half + 1
    assert first & second


@pytest.mark.parametrize("prime", (2, 3, 5, 7, 11, 13, 17, 19, 23, 31, 43, 97, 127))
def test_every_prime_seed_has_actual_bounded_witnesses(prime: int) -> None:
    half = prime // 2
    witnesses = (
        (first, second, (first * first + second * second + 1) // prime)
        for first in range(half + 1)
        for second in range(half + 1)
        if (first * first + second * second + 1) % prime == 0
    )
    first, second, multiplier = next(witnesses)
    assert first * first + second * second + 1 == prime * multiplier
    assert 0 < multiplier < prime
