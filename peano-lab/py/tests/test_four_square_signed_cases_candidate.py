"""Independent bounded checks for all sixteen signed quaternion masks."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library import four_square_signed_cases_candidate as cases
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_collision_norm_candidate import (
    make_fermat_two_squares_collision_norm_candidate_theorems,
)
from peano_lab.library.four_square_conjugate_identity_candidate import (
    make_four_square_conjugate_identity_candidate_theorems,
)
from peano_lab.library.four_square_euler_candidate import (
    make_four_square_euler_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.four_square_signed_block_negative_candidate import (
    make_four_square_signed_block_negative_candidate_theorems,
)
from peano_lab.library.four_square_signed_orientation_candidate import (
    make_four_square_signed_orientation_candidate_theorems,
)
from peano_lab.library.four_square_signed_quaternion_candidate import (
    make_four_square_signed_quaternion_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return cases.make_four_square_signed_cases_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    core = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_fermat_two_squares_collision_norm_candidate_theorems,
        make_four_square_identity_candidate_theorems,
        make_four_square_euler_candidate_theorems,
        make_four_square_signed_quaternion_candidate_theorems,
        make_four_square_conjugate_identity_candidate_theorems,
        make_four_square_signed_block_negative_candidate_theorems,
        make_four_square_signed_orientation_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_signed_case_candidates_are_closed_deterministic_and_release_isolated() -> None:
    rows = _rows()
    assert len(rows) == 17
    assert tuple(row.name for row in rows[1:]) == cases.FOUR_SQUARE_SIGNED_ORIENTATION_MASK_NAMES
    assert rows == cases.make_four_square_signed_cases_candidate_theorems(TheoremSpec)
    stable = _specs_by_name()
    observed = set(_core())
    for row in rows:
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in stable
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert set(row.dependencies) <= observed
        observed.add(row.name)


def test_all_sixteen_signed_case_bodies_are_independently_kernel_checked() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == 17
    assert max(receipt.proof_nodes for receipt in receipts) < 700
    assert max(receipt.proof_depth for receipt in receipts) < 100


@pytest.mark.parametrize("mask", tuple(range(16)))
def test_false_signed_orientation_case_is_rejected(mask: int) -> None:
    rows = _rows()
    index = mask + 1
    corrupted = replace(rows[index], statement=f"({rows[index].statement}) /\\ false")
    core = _core() | {row.name: row for row in rows[:index]}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


@pytest.mark.parametrize("mask", tuple(range(16)))
def test_each_mask_uses_its_exact_signed_centered_orientations(mask: int) -> None:
    row = _rows()[mask + 1]
    assert row.name.endswith(f"{mask:02d}")
    for index, (original, center) in enumerate(zip("abcd", "efgj", strict=True)):
        if mask & (1 << index):
            assert f"({original} + {center})" in row.statement
        else:
            assert f"({original}) + (k)" in row.statement


def test_signed_cases_rfc_records_all_sixteen_masks() -> None:
    repository = Path(__file__).resolve().parents[3]
    text = (
        repository / "research/arithmetic-library/four-square-signed-cases-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "sixteen" in text
    assert "four_square_signed_orientation_mask_00" in text
    assert "four_square_signed_orientation_mask_15" in text
    assert "No Alpha or Stable admission" in text
