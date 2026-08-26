"""Bounded independent checks for strictly prime-bounded four-square seeds."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.four_square_bounded_seed_candidate import (
    FOUR_SQUARE_ODD_PRIME_BOUNDED_MODULAR_SEED,
    FOUR_SQUARE_ODD_PRIME_HALF_COORDINATE_SEED,
    FOUR_SQUARE_PRIME_BOUNDED_MODULAR_SEED,
    make_four_square_bounded_seed_candidate_theorems,
)
from peano_lab.library.four_square_cross_pigeonhole_candidate import (
    make_four_square_cross_pigeonhole_candidate_theorems,
)
from peano_lab.library.four_square_descent_candidate import (
    make_four_square_descent_candidate_theorems,
)
from peano_lab.library.four_square_residue_intersection_candidate import (
    make_four_square_residue_intersection_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_bounded_seed_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    core = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_four_square_cross_pigeonhole_candidate_theorems,
        make_four_square_residue_intersection_candidate_theorems,
        make_four_square_descent_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_bounded_seed_candidates_are_first_order_and_release_isolated() -> None:
    observed = set(_core())
    stable = _specs_by_name()
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in stable
        assert set(row.dependencies) <= observed
        observed.add(row.name)


def test_bounded_seed_candidate_bodies_replay_independently() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == 6
    assert max(receipt.proof_nodes for receipt in receipts) < 400
    assert max(receipt.proof_depth for receipt in receipts) < 80


def test_prime_bounded_seed_contract_hash_is_pinned() -> None:
    root = next(
        row for row in _rows() if row.name == FOUR_SQUARE_PRIME_BOUNDED_MODULAR_SEED
    )
    assert sha256(root.statement.encode()).hexdigest() == (
        "664f15010c001437b0d990b4e1f81f845a0bc734a8fb5a3b31633ed463774077"
    )


@pytest.mark.parametrize(
    "name",
    (
        FOUR_SQUARE_ODD_PRIME_HALF_COORDINATE_SEED,
        FOUR_SQUARE_ODD_PRIME_BOUNDED_MODULAR_SEED,
        FOUR_SQUARE_PRIME_BOUNDED_MODULAR_SEED,
    ),
)
def test_false_bounded_seed_conclusions_are_rejected(name: str) -> None:
    rows = _rows()
    index = next(index for index, row in enumerate(rows) if row.name == name)
    corrupted = replace(rows[index], statement=f"({rows[index].statement}) /\\ false")
    core = _core() | {row.name: row for row in rows[:index]}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


@pytest.mark.parametrize("prime", (2, 3, 5, 7, 11, 13, 17, 19, 23, 31, 43, 97))
def test_every_small_prime_has_an_actual_strictly_bounded_seed(prime: int) -> None:
    half = prime // 2
    assert any(
        0 <= (multiplier := (first * first + second * second + 1) // prime) < prime
        for first in range(half + 1)
        for second in range(half + 1)
        if (first * first + second * second + 1) % prime == 0
    )
