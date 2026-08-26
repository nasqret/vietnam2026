"""Bounded constructive audit of the complete parity descent branches."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library import four_square_branch_descent_candidate as branch
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.four_square_descent_candidate import (
    make_four_square_descent_candidate_theorems,
)
from peano_lab.library.four_square_parity_selection_candidate import (
    make_four_square_parity_selection_candidate_theorems,
)
from peano_lab.library.four_square_signed_quaternion_candidate import (
    make_four_square_signed_quaternion_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    branch.FOUR_SQUARE_BRANCH_NONZERO_EVEN_HALF,
    branch.FOUR_SQUARE_BRANCH_POSITIVE_HALF_STRICT,
    branch.FOUR_SQUARE_BRANCH_EVEN_REPRESENTED_STRICT_STEP,
    branch.FOUR_SQUARE_BRANCH_ODD_REPRESENTED_STRICT_STEP,
    branch.FOUR_SQUARE_BOUNDED_STRICT_DESCENT_FROM_ODD_SIGNED_QUATERNION,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return branch.make_four_square_branch_descent_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    core = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_four_square_descent_candidate_theorems,
        make_four_square_parity_selection_candidate_theorems,
        make_four_square_signed_quaternion_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_branch_candidates_are_closed_deterministic_and_release_isolated() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert rows == branch.make_four_square_branch_descent_candidate_theorems(
        TheoremSpec
    )
    seen: set[str] = set()
    stable = _specs_by_name()
    for row in rows:
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in stable
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert set(row.dependencies) <= set(_core()) | seen
        assert not any(command.startswith(("ring", "omega", "auto")) for command in row.script)
        seen.add(row.name)


def test_branch_candidate_bodies_are_independently_kernel_checked() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) < 500
    assert max(receipt.proof_depth for receipt in receipts) < 100


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_branch_conclusions_are_rejected(name: str) -> None:
    rows = _rows()
    index = EXPECTED_NAMES.index(name)
    corrupted = replace(rows[index], statement=f"({rows[index].statement}) /\\ false")
    core = _core() | {row.name: row for row in rows[:index]}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


def test_branch_endpoint_retains_only_odd_signed_representation() -> None:
    root = _rows()[-1]
    parsed = _closed_formula(root.statement)
    assert isinstance(parsed, Imp)
    assert isinstance(parsed.antecedent, Forall)
    assert isinstance(parsed.consequent, Forall)
    assert "2 * fsbr_half_branch + 1" in root.statement
    assert "fslb_bounded_upper_gap_branch" in root.statement
    assert "four_square_branch_even_represented_strict_step" in root.dependencies
    assert "four_square_branch_odd_represented_strict_step" in root.dependencies
    assert sha256(root.statement.encode()).hexdigest() == (
        "89a33c3a5e637a028493cc776b7fc8e3f8d29558218bf2a5b9de69157dfeb851"
    )


@pytest.mark.parametrize("half", tuple(range(1, 25)))
def test_every_positive_even_half_is_nonzero_and_strictly_smaller(half: int) -> None:
    doubled = 2 * half
    assert half != 0
    assert half < doubled


def test_branch_rfc_identifies_the_only_remaining_obligation() -> None:
    repository = Path(__file__).resolve().parents[3]
    text = (
        repository / "research/arithmetic-library/four-square-branch-descent-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "four_square_bounded_strict_descent_from_odd_signed_quaternion" in text
    assert "odd signed centered quaternion" in text
    assert "unconditional" in text
    assert "No Alpha or Stable admission" in text
