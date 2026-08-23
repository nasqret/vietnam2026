"""Bounded audit of constructive prime-row Pascal convolution candidates."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from math import comb

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.lucas_convolution_candidate import (
    make_lucas_convolution_candidate_theorems,
)
from peano_lab.library.lucas_digit_candidate import make_lucas_digit_candidate_theorems
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "lucas_choose_lower_eq_transport",
    "lucas_choose_zero_index_is_one",
    "lucas_choose_zero_upper_positive_is_zero",
    "lucas_divisible_implies_zero_mod",
    "lucas_positive_digit_has_bounded_complement",
    "lucas_prime_row_interior_zero_mod",
    "lucas_pascal_congruence_step",
    "lucas_predecessor_digit_below_base",
    "lucas_prime_shift_below_base",
    "lucas_prime_plus_index_nonzero",
    "lucas_add_positive_index_strict",
    "lucas_prime_shift_high_column",
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_lucas_convolution_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    result = {row.name: row for row in editions_v12.ALPHA_SPECS}
    result.update(
        (row.name, row) for row in make_lucas_digit_candidate_theorems(TheoremSpec)
    )
    return result


def test_lucas_convolution_candidates_are_ordered_and_registry_isolated() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert len({row.name for row in rows}) == len(rows)
    public = _specs_by_name()
    seen: set[str] = set()
    for row in rows:
        assert row.name not in public
        assert row.name not in editions_v12.ALPHA_EDITION.by_name
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(_core()) | seen
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            notation not in row.statement
            for notation in ("Choose(", "Prime(", "ModEq(", "Dvd(", "Polynomial(")
        )
        seen.add(row.name)


def test_lucas_convolution_bodies_are_kernel_checked_and_bounded() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert len(receipts) == len(_rows())
    assert max(receipt.proof_nodes for receipt in receipts) == 504
    assert max(receipt.proof_depth for receipt in receipts) == 58
    below = next(
        receipt for receipt in receipts if receipt.name == "lucas_prime_shift_below_base"
    )
    assert (below.proof_nodes, below.proof_depth) == (224, 44)
    high = next(
        receipt for receipt in receipts if receipt.name == "lucas_prime_shift_high_column"
    )
    assert (high.proof_nodes, high.proof_depth) == (504, 58)


def test_prime_shift_flagship_statements_have_pinned_hashes() -> None:
    by_name = {row.name: row for row in _rows()}
    assert sha256(by_name["lucas_prime_shift_below_base"].statement.encode()).hexdigest() == (
        "4c888d1f6dd9974f52317bc48c2ab28f9ca5331c05fe362eab8b1403a6fbbcc7"
    )
    assert sha256(by_name["lucas_prime_shift_high_column"].statement.encode()).hexdigest() == (
        "7b1c762ed80e5f588398b877dc372628b6f143bf9aae4bd289a0988bbb8f6ea0"
    )


def test_prime_shift_certificate_rejects_a_false_conclusion() -> None:
    row = next(item for item in _rows() if item.name == "lucas_prime_shift_below_base")
    available = _core() | {item.name: item for item in _rows()}

    def target(statement: str):
        formula = _closed_formula(statement)
        for dependency in reversed(row.dependencies):
            formula = Imp(_closed_formula(available[dependency].statement), formula)
        return formula

    genuine = target(row.statement)
    state = start(genuine)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    proof = checked_final(state, genuine)
    assert check((), proof, genuine)
    assert not check((), proof, target(f"({row.statement}) /\\ 0 = 1"))
    assert len(sha256(row.statement.encode()).hexdigest()) == 64


@pytest.mark.parametrize("prime", (2, 3, 5, 7, 11, 13, 17))
@pytest.mark.parametrize("upper", (0, 1, 2, 4, 9, 15))
def test_prime_row_shift_has_exact_finite_examples(prime: int, upper: int) -> None:
    for lower in range(prime):
        right = comb(upper, lower) if lower <= upper else 0
        assert (comb(prime + upper, lower) - right) % prime == 0


@pytest.mark.parametrize("prime", (2, 3, 5, 7, 11))
@pytest.mark.parametrize("upper", (0, 1, 2, 4, 9, 15))
def test_prime_high_column_shift_has_exact_finite_examples(
    prime: int, upper: int
) -> None:
    for index in range(min(upper + 3, 10)):
        lower = prime + index
        shifted = comb(prime + upper, lower) if lower <= prime + upper else 0
        unchanged = comb(upper, lower) if lower <= upper else 0
        predecessor = comb(upper, index) if index <= upper else 0
        assert (shifted - unchanged - predecessor) % prime == 0
