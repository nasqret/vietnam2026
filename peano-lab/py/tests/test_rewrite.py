from __future__ import annotations

import pytest

from peano_lab.engine.rewrite import (
    NoRewriteOccurrence,
    RewriteUnderBinder,
    rewrite_first,
    rewrite_formula,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Forall, Imp
from peano_lab.kernel.proofs import EqSubst, Hyp
from peano_lab.kernel.subst import subst_formula
from peano_lab.kernel.terms import Add, Succ, Term, Var, Zero


ZERO = Zero()


def test_rewrite_first_is_left_to_right_term_preorder() -> None:
    x = Var(0)
    replacement = Succ(x)
    formula = And(Eq(Add(x, ZERO), x), Eq(x, x))

    rewritten, motive = rewrite_first(formula, x, replacement)

    assert rewritten == And(Eq(Add(replacement, ZERO), x), Eq(x, x))
    assert motive == And(
        Eq(Add(Var(0), ZERO), Var(1)),
        Eq(Var(1), Var(1)),
    )
    assert subst_formula(motive, 0, x) == formula
    assert subst_formula(motive, 0, replacement) == rewritten


def test_rewrite_prefers_a_whole_term_to_its_children() -> None:
    x = Var(0)
    source = Add(x, ZERO)
    replacement = Succ(x)
    formula = Eq(source, Add(source, x))

    rewritten, motive = rewrite_first(formula, source, replacement)

    assert rewritten == Eq(replacement, Add(source, x))
    assert subst_formula(motive, 0, source) == formula
    assert subst_formula(motive, 0, replacement) == rewritten


def test_motive_lifts_free_variables_without_capturing_bound_variables() -> None:
    formula = Imp(
        Eq(ZERO, Var(0)),
        Forall(Eq(Var(1), Var(0))),  # free outer #0, then bound #0
    )
    replacement = Succ(ZERO)

    rewritten, motive = rewrite_first(formula, ZERO, replacement)

    assert rewritten == Imp(Eq(replacement, Var(0)), Forall(Eq(Var(1), Var(0))))
    assert motive == Imp(
        Eq(Var(0), Var(1)),
        Forall(Eq(Var(2), Var(0))),
    )
    assert subst_formula(motive, 0, ZERO) == formula
    assert subst_formula(motive, 0, replacement) == rewritten


def test_rewrite_formula_chooses_direction_explicitly() -> None:
    x = Var(0)
    sx = Succ(x)
    equation = Eq(x, sx)

    forward, forward_motive = rewrite_formula(Eq(x, ZERO), equation)
    backward, backward_motive = rewrite_formula(
        Eq(sx, ZERO), equation, reverse=True
    )

    assert forward == Eq(sx, ZERO)
    assert backward == Eq(x, ZERO)
    assert subst_formula(forward_motive, 0, x) == Eq(x, ZERO)
    assert subst_formula(backward_motive, 0, sx) == Eq(sx, ZERO)


def test_returned_motive_builds_a_kernel_checked_eqsubst_certificate() -> None:
    x = Var(0)
    replacement = Succ(x)
    equation = Eq(x, replacement)
    old_formula = Eq(Add(x, ZERO), x)
    new_formula, motive = rewrite_formula(old_formula, equation)

    certificate = EqSubst(motive, Hyp(0), Hyp(1))

    assert check((equation, old_formula), certificate, new_formula)


def test_occurrence_only_below_quantifier_has_a_distinct_failure() -> None:
    source = Add(Var(0), ZERO)
    formula = Forall(Eq(Add(Var(1), ZERO), Var(1)))

    with pytest.raises(RewriteUnderBinder, match="under quantifiers"):
        rewrite_first(formula, source, Succ(Var(0)))


def test_bound_variable_is_not_mistaken_for_free_source() -> None:
    with pytest.raises(NoRewriteOccurrence, match="does not occur"):
        rewrite_first(Forall(Eq(Var(0), Var(0))), Var(0), ZERO)


def test_blocked_occurrence_does_not_hide_a_later_eligible_occurrence() -> None:
    formula = And(Forall(Eq(ZERO, ZERO)), Eq(ZERO, ZERO))

    rewritten, motive = rewrite_first(formula, ZERO, Succ(ZERO))

    assert rewritten == And(Forall(Eq(ZERO, ZERO)), Eq(Succ(ZERO), ZERO))
    assert subst_formula(motive, 0, ZERO) == formula
    assert subst_formula(motive, 0, Succ(ZERO)) == rewritten


def test_rewrite_rejects_non_rigid_sources_and_non_exact_equations() -> None:
    class Meta(Term):
        pass

    class EquationSubclass(Eq):
        pass

    formula = Eq(ZERO, ZERO)
    with pytest.raises(TypeError, match="rigid PA term"):
        rewrite_first(formula, Meta(), ZERO)
    with pytest.raises(TypeError, match="exact kernel equation"):
        rewrite_formula(formula, EquationSubclass(ZERO, ZERO))
