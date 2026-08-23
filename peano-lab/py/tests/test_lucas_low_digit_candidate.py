"""Bounded audit of the arbitrary-upper-quotient Lucas low-digit theorem."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from math import comb

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.lucas_convolution_candidate import (
    make_lucas_convolution_candidate_theorems,
)
from peano_lab.library.lucas_digit_candidate import make_lucas_digit_candidate_theorems
from peano_lab.library.lucas_low_digit_candidate import (
    LUCAS_LOW_DIGIT_CONGRUENCE,
    LUCAS_LOW_DIGIT_PRODUCT_CONGRUENCE,
    LUCAS_PRIME_BLOCK_SUCCESSOR_REASSOCIATION,
    LUCAS_PRIME_BLOCK_ZERO_REASSOCIATION,
    LUCAS_REPEATED_PRIME_SHIFT_BELOW_BASE,
    make_lucas_low_digit_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    LUCAS_PRIME_BLOCK_ZERO_REASSOCIATION,
    LUCAS_PRIME_BLOCK_SUCCESSOR_REASSOCIATION,
    LUCAS_REPEATED_PRIME_SHIFT_BELOW_BASE,
    LUCAS_LOW_DIGIT_CONGRUENCE,
    LUCAS_LOW_DIGIT_PRODUCT_CONGRUENCE,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_lucas_low_digit_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    rows = {row.name: row for row in editions_v12.ALPHA_SPECS}
    rows.update((row.name, row) for row in make_lucas_digit_candidate_theorems(TheoremSpec))
    rows.update(
        (row.name, row)
        for row in make_lucas_convolution_candidate_theorems(TheoremSpec)
    )
    return rows


def test_low_digit_candidates_are_exact_ordered_first_order_and_release_isolated() -> None:
    public = _specs_by_name()
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    seen: set[str] = set()
    for row in rows:
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in public
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(_core()) | seen
        assert all(token not in row.statement for token in ("Prime(", "Choose(", "ModEq("))
        seen.add(row.name)


def test_low_digit_candidates_have_bounded_independent_kernel_certificates() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(row.proof_nodes for row in receipts) < 450
    assert max(row.proof_depth for row in receipts) < 100


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_low_digit_candidates_reject_a_false_conclusion(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    known = _core() | {item.name: item for item in _rows()}
    corrupted = replace(row, statement=f"({row.statement}) /\\ 0 = 1")

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=known)


@pytest.mark.parametrize("prime", (2, 3, 5, 7, 11))
@pytest.mark.parametrize("quotient", (0, 1, 2, 4, 9))
def test_unrestricted_upper_quotient_matches_every_lower_digit(
    prime: int,
    quotient: int,
) -> None:
    for upper_digit in range(prime):
        for lower_digit in range(prime):
            upper = prime * quotient + upper_digit
            whole = comb(upper, lower_digit) if lower_digit <= upper else 0
            digit = comb(upper_digit, lower_digit) if lower_digit <= upper_digit else 0
            assert (whole - digit) % prime == 0


@pytest.mark.parametrize("composite", (4, 6, 8, 9, 10))
def test_prime_premise_cannot_be_removed(composite: int) -> None:
    assert any(
        (comb(composite, lower_digit) - 0) % composite != 0
        for lower_digit in range(1, composite)
    )
