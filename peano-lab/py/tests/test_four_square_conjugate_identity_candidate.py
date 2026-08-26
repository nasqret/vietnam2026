"""Independent kernel checks for the exact conjugate quaternion identity."""

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
from peano_lab.library.four_square_conjugate_identity_candidate import (
    FOUR_SQUARE_CONJUGATE_ABSOLUTE_COORDINATES_TOTAL,
    FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION,
    FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION,
    make_four_square_conjugate_identity_candidate_theorems,
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
    return make_four_square_conjugate_identity_candidate_theorems(TheoremSpec)


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


def test_conjugate_candidates_are_isolated_first_order_theorems() -> None:
    known = set(_core())
    stable = _specs_by_name()
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in stable
        assert set(row.dependencies) <= known
        known.add(row.name)


def test_conjugate_candidate_bodies_replay_independently() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == 9
    assert max(receipt.proof_nodes for receipt in receipts) < 3000
    assert max(receipt.proof_depth for receipt in receipts) < 180


def test_conjugate_quaternion_contract_hashes_are_pinned() -> None:
    rows = {row.name: row for row in _rows()}
    expected = {
        FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION:
            "01f9c0ae7ccb0eb485b27b2956ec2e1e531feed36a85963572bcee10b0c56c66",
        FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION:
            "94bd014681b8c5d3e9505fed47fae5cd591da1fc2428217d55d590062880d7a3",
        FOUR_SQUARE_CONJUGATE_ABSOLUTE_COORDINATES_TOTAL:
            "72e122dcb8c33e460a9e1e4829331deb9abfb18ca4e9e1bca9c2dac6f922b44c",
    }
    assert {
        name: sha256(rows[name].statement.encode()).hexdigest()
        for name in expected
    } == expected


@pytest.mark.parametrize(
    "name",
    (
        FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION,
        FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION,
    ),
)
def test_false_conjugate_identity_conclusions_are_rejected(name: str) -> None:
    rows = _rows()
    index = next(index for index, row in enumerate(rows) if row.name == name)
    corrupted = replace(rows[index], statement=f"({rows[index].statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (corrupted,), core=_core() | {row.name: row for row in rows[:index]}
        )


@pytest.mark.parametrize("coordinates", tuple(product(range(2), repeat=8)))
def test_exact_conjugate_blocks_preserve_the_full_quaternion_norm(
    coordinates: tuple[int, int, int, int, int, int, int, int],
) -> None:
    a, b, c, d, e, f, g, h = coordinates
    blocks = (
        a * e + b * f + c * g + d * h,
        a * f + c * h - b * e - d * g,
        a * g + d * f - c * e - b * h,
        a * h + b * g - d * e - c * f,
    )
    assert (a * a + b * b + c * c + d * d) * (
        e * e + f * f + g * g + h * h
    ) == sum(block * block for block in blocks)
