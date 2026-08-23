"""Bounded audit of all-sign constructive centered quaternion integrality."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_two_squares_collision_norm_candidate import (
    make_fermat_two_squares_collision_norm_candidate_theorems,
)
from peano_lab.library.four_square_euler_candidate import (
    make_four_square_euler_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.four_square_signed_quaternion_candidate import (
    make_four_square_signed_quaternion_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_signed_quaternion_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    rows = {row.name: row for row in editions_v12.ALPHA_SPECS}
    rows.update(
        (row.name, row)
        for row in make_fermat_two_squares_collision_norm_candidate_theorems(TheoremSpec)
    )
    rows.update(
        (row.name, row)
        for row in make_four_square_identity_candidate_theorems(TheoremSpec)
    )
    rows.update(
        (row.name, row)
        for row in make_four_square_euler_candidate_theorems(TheoremSpec)
    )
    return rows


def test_signed_quaternion_candidates_are_first_order_and_release_isolated() -> None:
    seen: set[str] = set()
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in _specs_by_name()
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert set(row.dependencies) <= set(_core()) | seen
        seen.add(row.name)


def test_signed_quaternion_canonical_surfaces_are_pinned() -> None:
    rows = {row.name: row for row in _rows()}
    assert len(rows) == 28
    assert {
        name: sha256(rows[name].statement.encode()).hexdigest()
        for name in (
            "four_square_signed_centered_norm_quotient_exists",
            "four_square_signed_conjugate_positive_blocks",
            "four_square_signed_conjugate_mixed_blocks",
            "four_square_signed_natural_negative_first_blocks",
        )
    } == {
        "four_square_signed_centered_norm_quotient_exists":
            "3a3cd289475188f620ddc67826f18afb20f44646d6db3ca2f849fbd473e4bab5",
        "four_square_signed_conjugate_positive_blocks":
            "6a03706d5246dd92b6b79d801db89fb44a839cc9f374c56d1eae081f8eb8671a",
        "four_square_signed_conjugate_mixed_blocks":
            "a397c4c916e5cbf73d104a5172929602adccd7a2b229b2203d35a9014e006dbd",
        "four_square_signed_natural_negative_first_blocks":
            "30f8f87ffcb55fd6256addc01195d5e190a15492af577027211bed79380f3f4f",
    }


def test_signed_quaternion_bodies_are_kernel_checked_and_bounded() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(_rows())
    assert max(receipt.proof_nodes for receipt in receipts) < 900
    assert max(receipt.proof_depth for receipt in receipts) < 120


@pytest.mark.parametrize("modulus", (3, 5, 7, 9, 11, 15))
@pytest.mark.parametrize("pattern", range(16))
def test_all_sixteen_signed_patterns_preserve_square_norm(
    modulus: int, pattern: int
) -> None:
    centered = (1, 2 % modulus, 3 % modulus, 4 % modulus)
    original = tuple(
        value if pattern & (1 << index) == 0 else (modulus - value) % modulus
        for index, value in enumerate(centered)
    )
    assert sum(value * value for value in original) % modulus == sum(
        value * value for value in centered
    ) % modulus
