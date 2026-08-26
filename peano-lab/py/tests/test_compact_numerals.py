"""Conservative binary decimal literals preserve the historic PA proof kernel."""

from __future__ import annotations

from dataclasses import fields

import pytest

import driver
from peano_lab.batch import BatchRequestError, run_proof
from peano_lab.engine.decide import evaluate_closed_term
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, parse_formula, pretty_formula
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import (
    Add,
    Mul,
    Succ,
    Term,
    UNARY_NUMERAL_LIMIT,
    Var,
    Zero,
    numeral_value,
    parse_term,
    pretty_term,
)
from peano_lab.ui.prove import MAX_NUMERAL, oversized_numeral


def _structural_nodes(term: Term) -> int:
    pending = [term]
    count = 0
    while pending:
        current = pending.pop()
        count += 1
        assert type(current) in {Zero, Var, Succ, Add, Mul}
        for field in fields(current):
            child = getattr(current, field.name)
            if isinstance(child, Term):
                pending.append(child)
    return count


def _same_structure(left: Term, right: Term) -> bool:
    """Compare deep immutable ASTs without recursive dataclass equality."""

    pending = [(left, right)]
    while pending:
        first, second = pending.pop()
        if type(first) is not type(second):
            return False
        for field in fields(first):
            first_value = getattr(first, field.name)
            second_value = getattr(second, field.name)
            if isinstance(first_value, Term):
                if not isinstance(second_value, Term):
                    return False
                pending.append((first_value, second_value))
            elif first_value != second_value:
                return False
    return True


@pytest.mark.parametrize("value", [0, 1, 2, 5, 127, 255, 256])
def test_historic_public_numerals_retain_their_exact_unary_ast(value: int) -> None:
    term = parse_term(str(value))
    cursor = term
    for _ in range(value):
        assert type(cursor) is Succ
        cursor = cursor.term
    assert type(cursor) is Zero
    assert numeral_value(term) == value
    assert _structural_nodes(term) == value + 1


@pytest.mark.parametrize(
    "value",
    [257, 258, 511, 512, 1_024, 999_999, 1_000_000, 10**30, 2**512],
)
def test_large_literals_use_logarithmic_existing_language_terms(value: int) -> None:
    term = parse_term(str(value))
    assert type(term) in {Succ, Mul}
    assert numeral_value(term) == value
    assert evaluate_closed_term(term) == value
    assert pretty_term(term, []) == str(value)
    assert _same_structure(parse_term(pretty_term(term, [])), term)
    assert _structural_nodes(term) <= UNARY_NUMERAL_LIMIT + 5 * value.bit_length()


def test_noncanonical_closed_arithmetic_never_disappears_into_decimal_sugar() -> None:
    for source in ("2 * 2", "2 * (2 * 128)", "2 * (128 + 1)"):
        term = parse_term(source)
        assert numeral_value(term) is None
        assert parse_term(pretty_term(term, [])) == term


def test_compact_formula_roundtrips_and_original_kernel_checks_it() -> None:
    formula = parse_formula("1000000 = 1000000")
    assert type(formula) is Eq
    assert pretty_formula(formula, []) == "1000000 = 1000000"
    assert parse_formula(pretty_formula(formula, [])) == formula
    assert check((), EqRefl(formula.left), formula)


def test_browser_and_batch_accept_large_compact_literal_under_explicit_cap() -> None:
    assert MAX_NUMERAL == 1_000_000
    assert oversized_numeral("1000000 = 1000000") is None
    assert oversized_numeral("1000001 = 0") == "1000001"

    session = driver.LabSession()
    assert "1000000" in session.run("pa eval 1000000")
    result = run_proof("1000000 = 1000000", ("refl",))
    assert result.status == "proved"
    assert result.kernel_checked is True

    with pytest.raises(BatchRequestError, match="numeral 1000001"):
        run_proof("1000001 = 1000001", ("refl",))


def test_false_large_numeral_claim_still_fails_independent_kernel() -> None:
    left = parse_term("1000000")
    right = parse_term("999999")
    assert not check((), EqRefl(left), Eq(left, right))
