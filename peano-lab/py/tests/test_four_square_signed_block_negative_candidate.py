"""Independent HA checks for the two negative-heavy quaternion orientations."""

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
from peano_lab.library.four_square_euler_candidate import (
    make_four_square_euler_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.four_square_signed_block_negative_candidate import (
    FOUR_SQUARE_SIGNED_CONJUGATE_NEGATIVE_BLOCKS,
    FOUR_SQUARE_SIGNED_NATURAL_POSITIVE_FIRST_BLOCKS,
    make_four_square_signed_block_negative_candidate_theorems,
)
from peano_lab.library.four_square_signed_quaternion_candidate import (
    make_four_square_signed_quaternion_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    FOUR_SQUARE_SIGNED_CONJUGATE_NEGATIVE_BLOCKS,
    FOUR_SQUARE_SIGNED_NATURAL_POSITIVE_FIRST_BLOCKS,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_signed_block_negative_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    core = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_four_square_identity_candidate_theorems,
        make_four_square_euler_candidate_theorems,
        make_four_square_signed_quaternion_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_negative_block_rows_are_isolated_first_order_candidates() -> None:
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    stable = _specs_by_name()
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in stable
        assert set(row.dependencies) <= set(_core())


def test_negative_block_bodies_replay_independently() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == 2
    assert max(receipt.proof_nodes for receipt in receipts) < 1800
    assert max(receipt.proof_depth for receipt in receipts) < 150


def test_negative_canonical_surface_hashes_are_pinned() -> None:
    rows = {row.name: row for row in _rows()}
    assert {
        name: sha256(rows[name].statement.encode()).hexdigest()
        for name in EXPECTED_NAMES
    } == {
        FOUR_SQUARE_SIGNED_CONJUGATE_NEGATIVE_BLOCKS:
            "4bbfc13207d91959aea04b77ab54eacb81c586954f4edd4f00045d5b1d98e258",
        FOUR_SQUARE_SIGNED_NATURAL_POSITIVE_FIRST_BLOCKS:
            "ff332f2ab05eddd879d8e0665550add793fe35d246f278ec12af98fbe97da149",
    }


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_negative_block_conclusions_are_rejected(name: str) -> None:
    row = next(row for row in _rows() if row.name == name)
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_core())


@pytest.mark.parametrize("modulus", (2, 3, 5, 7))
def test_negative_and_positive_first_blocks_vanish_on_small_residues(
    modulus: int,
) -> None:
    for e, f, g, h in product(range(modulus), repeat=4):
        if (e * e + f * f + g * g + h * h) % modulus:
            continue
        a, b, c, d = (-e % modulus, -f % modulus, -g % modulus, -h % modulus)
        assert (a * e + b * f + c * g + d * h) % modulus == 0
        assert (a * f + c * h - b * e - d * g) % modulus == 0
        assert (a * g + d * f - c * e - b * h) % modulus == 0
        assert (a * h + b * g - d * e - c * f) % modulus == 0
        a = e
        assert (a * e - b * f - c * g - d * h) % modulus == 0
        assert (a * f + b * e + c * h - d * g) % modulus == 0
        assert (a * g + c * e + d * f - b * h) % modulus == 0
        assert (a * h + b * g + d * e - c * f) % modulus == 0
