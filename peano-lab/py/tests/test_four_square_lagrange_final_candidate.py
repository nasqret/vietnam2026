"""Exact constructive audit of the final odd-signed Lagrange reduction."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library import four_square_lagrange_final_candidate as final
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.four_square_branch_descent_candidate import (
    make_four_square_branch_descent_candidate_theorems,
)
from peano_lab.library.four_square_lagrange_bridge_candidate import (
    make_four_square_lagrange_bridge_candidate_theorems,
)
from peano_lab.library.four_square_lagrange_candidate import (
    make_four_square_lagrange_candidate_theorems,
)
from peano_lab.library.four_square_signed_orientation_candidate import (
    make_four_square_signed_orientation_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    final.FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION,
    final.FOUR_SQUARE_LAGRANGE_FROM_ODD_SIGNED_QUATERNION,
    final.FOUR_SQUARE_PRIME_REPRESENTATION,
    final.FOUR_SQUARE_LAGRANGE,
)
PINNED_ENDPOINTS = {
    final.FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION:
        "52fe02b94dec63cb023e60f00c5a6d3d7fd1cfc014a37227dd3cd91090442a04",
    final.FOUR_SQUARE_LAGRANGE_FROM_ODD_SIGNED_QUATERNION:
        "fbad3ff6a69377d2b3131db1066b174c89fb2e0b23dbeb64c8fc8893a4339241",
    final.FOUR_SQUARE_PRIME_REPRESENTATION:
        "561b591ea074bf6a2d715665afde074b2c6a90f86c08bdbfa4b6b94553a92240",
    final.FOUR_SQUARE_LAGRANGE:
        "fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return final.make_four_square_lagrange_final_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    core = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_four_square_lagrange_candidate_theorems,
        make_four_square_branch_descent_candidate_theorems,
        make_four_square_lagrange_bridge_candidate_theorems,
        make_four_square_signed_orientation_candidate_theorems,
    ):
        core.update((row.name, row) for row in factory(TheoremSpec))
    return core


def test_final_candidates_are_closed_deterministic_and_release_isolated() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert rows == final.make_four_square_lagrange_final_candidate_theorems(TheoremSpec)
    seen: set[str] = set()
    stable = _specs_by_name()
    for row in rows:
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert row.name not in stable
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert set(row.dependencies) <= set(_core()) | seen
        seen.add(row.name)


def test_final_candidate_bodies_replay_independently_with_small_proofs() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) < 30
    assert max(receipt.proof_depth for receipt in receipts) < 20


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_final_conclusions_are_rejected(name: str) -> None:
    rows = _rows()
    index = EXPECTED_NAMES.index(name)
    corrupted = replace(rows[index], statement=f"({rows[index].statement}) /\\ false")
    core = _core() | {row.name: row for row in rows[:index]}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


def test_final_prime_and_universal_roots_retain_exactly_one_premise() -> None:
    prime_row, universal_row = _rows()[:2]
    for row in (prime_row, universal_row):
        parsed = _closed_formula(row.statement)
        assert isinstance(parsed, Imp)
        assert isinstance(parsed.antecedent, Forall)
        assert isinstance(parsed.consequent, Forall)
        assert "2 * fsbr_half_final + 1" in row.statement
        assert "fsbr_multiplier_final * fsbr_quotient_final" in row.statement
        assert sha256(row.statement.encode()).hexdigest() == PINNED_ENDPOINTS[row.name]
    assert "four_square_bounded_strict_descent_from_odd_signed_quaternion" in prime_row.dependencies
    assert "four_square_prime_from_bounded_strict_descent" in prime_row.dependencies
    assert "four_square_lagrange_from_all_primes" in universal_row.dependencies


def test_unconditional_lagrange_root_has_no_hypotheses() -> None:
    prime_row, universal_row = _rows()[2:]
    prime_formula = _closed_formula(prime_row.statement)
    universal_formula = _closed_formula(universal_row.statement)
    assert isinstance(prime_formula, Forall)
    assert isinstance(universal_formula, Forall)
    assert prime_row.name == "four_square_prime_representation"
    assert universal_row.name == "four_square_lagrange"
    assert "four_square_signed_centered_representation" in prime_row.dependencies
    assert universal_row.dependencies == (
        "four_square_prime_representation",
        "four_square_lagrange_from_all_primes",
    )
    assert universal_row.statement.startswith("forall n. (exists ")
    assert sha256(prime_row.statement.encode()).hexdigest() == PINNED_ENDPOINTS[
        prime_row.name
    ]
    assert sha256(universal_row.statement.encode()).hexdigest() == PINNED_ENDPOINTS[
        universal_row.name
    ]


def test_final_rfc_names_the_single_honest_remaining_obligation() -> None:
    repository = Path(__file__).resolve().parents[3]
    text = (
        repository / "research/arithmetic-library/four-square-lagrange-final-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "four_square_lagrange_from_odd_signed_quaternion" in text
    assert "four_square_lagrange:" in text
    assert "odd signed centered quaternion" in text
    assert "unconditional" in text
    assert "No Alpha or Stable admission" in text
