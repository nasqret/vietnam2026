"""M4 closed computation, certified equations, and honest bounded checks."""

from __future__ import annotations

import pytest

from peano_lab.engine.decide import (
    BoundedVerdict,
    DecisionError,
    EquationVerdict,
    bounded_check,
    decide_closed_equation,
    evaluate_closed_term,
    prove_closed_equation,
)
from peano_lab.engine.state import MetaVar
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall, parse_formula
from peano_lab.kernel.proofs import Proof
from peano_lab.kernel.terms import Add, Succ, Var, Zero, parse_term


ZERO = Zero()
ONE = Succ(ZERO)


def test_closed_term_evaluation_uses_standard_natural_arithmetic() -> None:
    assert evaluate_closed_term(ZERO) == 0
    assert evaluate_closed_term(parse_term("S (2 + 3 * 4)")) == 15


@pytest.mark.parametrize(
    "term",
    [
        Var(0),
        Var(-1),
        Var(True),
        MetaVar(0),
        Add(ZERO, Var(0)),
        object(),
    ],
)
def test_closed_term_evaluation_rejects_open_or_malformed_terms(term: object) -> None:
    with pytest.raises(DecisionError, match="cannot evaluate term"):
        evaluate_closed_term(term)  # type: ignore[arg-type]


def test_closed_term_evaluation_rejects_term_subclasses() -> None:
    class PretendZero(Zero):
        pass

    with pytest.raises(DecisionError, match="exact PA term"):
        evaluate_closed_term(PretendZero())


def test_public_decision_boundaries_normalize_uninitialized_nodes() -> None:
    malformed_term = object.__new__(Succ)
    malformed_equation = object.__new__(Eq)

    with pytest.raises(DecisionError, match="malformed"):
        evaluate_closed_term(malformed_term)
    with pytest.raises(DecisionError, match="malformed"):
        decide_closed_equation(malformed_equation)
    with pytest.raises(DecisionError, match="malformed"):
        prove_closed_equation(malformed_equation)
    with pytest.raises(DecisionError, match="malformed"):
        bounded_check(malformed_equation, 2)


def test_equation_decision_is_a_report_not_a_certificate() -> None:
    equation = parse_formula("2 * (1 + 2) = 6")
    verdict = decide_closed_equation(equation)

    assert verdict == EquationVerdict(True, 6, 6)
    assert bool(verdict)
    assert verdict.label == "closed equation decision"
    assert not isinstance(verdict, Proof)
    assert not hasattr(verdict, "certificate")


def test_false_closed_equation_reports_values_and_has_no_proof() -> None:
    equation = parse_formula("2 + 2 = 5")
    verdict = decide_closed_equation(equation)

    assert not verdict
    assert (verdict.left_value, verdict.right_value) == (4, 5)
    assert prove_closed_equation(equation) is None


@pytest.mark.parametrize(
    "source",
    [
        "0 = 0",
        "1 + 2 = 3",
        "2 * 3 = 6",
        "(1 + 2) * 2 = 6",
        "S (2 * 2 + 1) = 6",
    ],
)
def test_true_closed_equations_get_independently_checked_certificates(source: str) -> None:
    equation = parse_formula(source)
    certificate = prove_closed_equation(equation)

    assert isinstance(certificate, Proof)
    assert check((), certificate, equation)


def test_equation_operations_reject_non_equations_open_terms_and_subclasses() -> None:
    with pytest.raises(DecisionError, match="expects an equation"):
        decide_closed_equation(parse_formula("false"))  # type: ignore[arg-type]
    with pytest.raises(DecisionError, match="open variable"):
        decide_closed_equation(Eq(Var(0), ZERO))

    class PretendEquation(Eq):
        pass

    forged = PretendEquation(ZERO, ZERO)
    with pytest.raises(DecisionError, match="expects an equation"):
        prove_closed_equation(forged)


def test_bounded_quantifiers_use_the_inclusive_domain_zero_through_bound() -> None:
    below = bounded_check(parse_formula("exists x. x = 3"), 2)
    reached = bounded_check(parse_formula("exists x. x = 3"), 3)

    assert below == BoundedVerdict(
        holds=False,
        bound=2,
        has_quantifiers=True,
        label="bounded check over 0..2 (inclusive)",
    )
    assert not below.complete
    assert reached.holds
    assert reached.label == "bounded check over 0..3 (inclusive)"


def test_bounded_check_handles_vacuous_nested_and_connective_formulas() -> None:
    examples = [
        ("forall x. 0 = 0", True),
        ("exists x. 0 = 1", False),
        ("forall x. exists y. x = y", True),
        ("forall x. x = 0 \\/ ~(x = 0)", True),
        ("(0 = 0 /\\ 1 = 1) -> (false \\/ 2 = 2)", True),
        ("false", False),
    ]
    for source, expected in examples:
        verdict = bounded_check(parse_formula(source), 2)
        assert verdict.holds is expected

    quantifier_free = bounded_check(parse_formula(r"0 = 0 \/ 0 = 1"), 0)
    assert quantifier_free.complete
    assert not quantifier_free.has_quantifiers


def test_bound_exhaustion_is_explicitly_not_a_proof_or_complete_decision() -> None:
    formula = parse_formula("exists x. x = 4")
    verdict = bounded_check(formula, 3)

    assert not verdict.holds
    assert not verdict.complete
    assert "bounded" in verdict.label
    assert not isinstance(verdict, Proof)
    assert not check((), verdict, formula)


@pytest.mark.parametrize("bound", [-1, True, 1.5, "2"])
def test_bounded_check_rejects_invalid_bounds(bound: object) -> None:
    with pytest.raises(DecisionError, match="non-negative integer"):
        bounded_check(parse_formula("forall x. x = x"), bound)  # type: ignore[arg-type]


def test_bounded_check_rejects_open_and_malformed_formulas() -> None:
    with pytest.raises(DecisionError, match="open variable"):
        bounded_check(Eq(Var(0), ZERO), 2)
    with pytest.raises(DecisionError, match="open variable"):
        bounded_check(Forall(Eq(Var(1), ZERO)), 2)
    # The true left arm must not let evaluator short-circuiting hide the open
    # variable in the right arm.
    with pytest.raises(DecisionError, match="open variable"):
        bounded_check(parse_formula(r"0 = 0 \/ x = 0"), 2)

    class PretendEquation(Eq):
        pass

    with pytest.raises(DecisionError, match="exact PA formula"):
        bounded_check(PretendEquation(ZERO, ZERO), 2)
