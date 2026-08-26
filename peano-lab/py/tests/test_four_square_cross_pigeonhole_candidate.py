"""Bounded audit of actual cross-family finite beta-prefix collisions."""

from __future__ import annotations

from functools import lru_cache

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_two_squares_pigeonhole_candidate import (
    make_fermat_two_squares_pigeonhole_candidate_theorems,
)
from peano_lab.library.finite_prefix_collision_decision_candidate import (
    make_finite_prefix_collision_decision_candidate_theorems,
)
from peano_lab.library.four_square_cross_pigeonhole_candidate import (
    FOUR_SQUARE_CROSS_COVERED_PREFIX_BOUNDED,
    FOUR_SQUARE_CROSS_INTERLEAVED_PREFIX_EXISTS,
    FOUR_SQUARE_CROSS_INTERSECTION,
    FOUR_SQUARE_CROSS_PIGEONHOLE,
    make_four_square_cross_pigeonhole_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    FOUR_SQUARE_CROSS_COVERED_PREFIX_BOUNDED,
    FOUR_SQUARE_CROSS_PIGEONHOLE,
    FOUR_SQUARE_CROSS_INTERLEAVED_PREFIX_EXISTS,
    FOUR_SQUARE_CROSS_INTERSECTION,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_cross_pigeonhole_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    rows = {row.name: row for row in editions_v12.ALPHA_SPECS}
    rows.update(
        (row.name, row)
        for row in make_fermat_two_squares_pigeonhole_candidate_theorems(TheoremSpec)
    )
    rows.update(
        (row.name, row)
        for row in make_finite_prefix_collision_decision_candidate_theorems(TheoremSpec)
    )
    return rows


def test_cross_pigeonhole_candidates_are_first_order_and_registry_isolated() -> None:
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


def test_cross_pigeonhole_candidates_are_independently_kernel_checked() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(row.proof_nodes for row in receipts) < 750
    assert max(row.proof_depth for row in receipts) < 100


@pytest.mark.parametrize("modulus", (3, 5, 7, 11, 13))
def test_two_injective_odd_half_ranges_must_intersect(modulus: int) -> None:
    length = (modulus + 1) // 2
    for offset in range(modulus):
        left = set(range(length))
        right = {(offset + index) % modulus for index in range(length)}
        assert len(left) == length
        assert len(right) == length
        assert left & right
