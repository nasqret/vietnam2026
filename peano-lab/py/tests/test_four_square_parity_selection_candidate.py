"""Bounded independent checks for unconditional four-square even halving."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import product

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.four_square_descent_candidate import (
    make_four_square_descent_candidate_theorems,
)
from peano_lab.library.four_square_parity_selection_candidate import (
    FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING,
    FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION,
    FOUR_SQUARE_PARITY_REPRESENTED_ADDITIVE_DOUBLE_HALVING,
    FOUR_SQUARE_PARITY_REPRESENTED_DOUBLE_HALVING,
    make_four_square_parity_selection_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_parity_selection_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    core = {row.name: row for row in editions_v12.ALPHA_SPECS}
    core |= {
        row.name: row
        for row in make_four_square_descent_candidate_theorems(TheoremSpec)
    }
    return core


def test_parity_selection_rows_are_isolated_first_order_candidates() -> None:
    known = set(_core())
    stable = _specs_by_name()
    for row in _rows():
        assert row.name not in stable
        assert set(row.dependencies) <= known
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert "FourSquare(" not in row.statement
        known.add(row.name)


def test_parity_selection_candidate_bodies_replay_independently() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(_rows())
    assert max(receipt.proof_nodes for receipt in receipts) < 1200
    assert max(receipt.proof_depth for receipt in receipts) < 150


def test_unconditional_halving_contract_hashes_are_pinned() -> None:
    rows = {row.name: row for row in _rows()}
    expected = {
        FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION:
            "bf6c08a6d28dcdbeba707e392d200835051166f895801eb875f3f3ff008a4cae",
        FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING:
            "1e4b5821869e0e29b9e3eaafa009705e18a94dbc4079a9ec37e4217e30e862c3",
        FOUR_SQUARE_PARITY_REPRESENTED_DOUBLE_HALVING:
            "c5af9314d7cf3d665f914153f1a7e96176854a735ce7a7a82b4ae812125d12bc",
        FOUR_SQUARE_PARITY_REPRESENTED_ADDITIVE_DOUBLE_HALVING:
            "ceedc3db189c22bb6c0a7a6fc76fcebe7248e5de4dded044352ad9d1c7028c22",
    }
    assert len(rows) == 13
    assert {
        name: sha256(rows[name].statement.encode()).hexdigest()
        for name in expected
    } == expected


@pytest.mark.parametrize(
    "name",
    (
        FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION,
        FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING,
        FOUR_SQUARE_PARITY_REPRESENTED_DOUBLE_HALVING,
        FOUR_SQUARE_PARITY_REPRESENTED_ADDITIVE_DOUBLE_HALVING,
    ),
)
def test_false_flagship_conclusions_are_rejected(name: str) -> None:
    rows = _rows()
    position = next(index for index, row in enumerate(rows) if row.name == name)
    row = rows[position]
    core = _core() | {item.name: item for item in rows[:position]}
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


@pytest.mark.parametrize("coordinates", tuple(product(range(4), repeat=4)))
def test_every_even_norm_has_two_matching_parity_pairs(
    coordinates: tuple[int, int, int, int],
) -> None:
    a, b, c, d = coordinates
    if (a * a + b * b + c * c + d * d) % 2:
        return
    assert (
        (a % 2 == b % 2 and c % 2 == d % 2)
        or (a % 2 == c % 2 and b % 2 == d % 2)
        or (a % 2 == d % 2 and b % 2 == c % 2)
    )
