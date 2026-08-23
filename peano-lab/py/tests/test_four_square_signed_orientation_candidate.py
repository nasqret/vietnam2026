"""Bounded independent checks for signed four-square norm-product quotients."""

from __future__ import annotations

from functools import lru_cache

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.four_square_descent_candidate import (
    make_four_square_descent_candidate_theorems,
)
from peano_lab.library.four_square_signed_orientation_candidate import (
    FOUR_SQUARE_SIGNED_ABSOLUTE_BLOCK_REPRESENTATION,
    FOUR_SQUARE_SIGNED_CENTERED_REPRESENTATION,
    FOUR_SQUARE_SIGNED_DIVISIBLE_NORM_PRODUCT_REPRESENTATION,
    make_four_square_signed_orientation_candidate_theorems,
)
from peano_lab.library.four_square_signed_quaternion_candidate import (
    make_four_square_signed_quaternion_candidate_theorems,
)
from peano_lab.library.four_square_signed_cases_candidate import (
    make_four_square_signed_cases_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    FOUR_SQUARE_SIGNED_DIVISIBLE_NORM_PRODUCT_REPRESENTATION,
    FOUR_SQUARE_SIGNED_ABSOLUTE_BLOCK_REPRESENTATION,
    FOUR_SQUARE_SIGNED_CENTERED_REPRESENTATION,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_signed_orientation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    rows = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_four_square_descent_candidate_theorems,
        make_four_square_signed_quaternion_candidate_theorems,
        make_four_square_signed_cases_candidate_theorems,
    ):
        rows.update((row.name, row) for row in factory(TheoremSpec))
    return rows


def test_signed_orientation_candidates_are_first_order_and_release_isolated() -> None:
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


def test_signed_orientation_bodies_are_independently_kernel_checked() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) < 900
    assert max(receipt.proof_depth for receipt in receipts) < 100
