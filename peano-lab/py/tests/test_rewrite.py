from __future__ import annotations

import pytest

from peano_lab.engine.rewrite import (
    NoRewriteOccurrence,
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


def test_outer_term_rewrites_capture_safely_below_a_quantifier() -> None:
    source = Add(Var(0), ZERO)
    formula = Forall(Eq(Add(Var(1), ZERO), Var(1)))
    replacement = Succ(Var(0))

    rewritten, motive = rewrite_first(formula, source, replacement)
    assert rewritten == Forall(Eq(Succ(Var(1)), Var(1)))
    assert motive == Forall(Eq(Var(1), Var(2)))
    assert subst_formula(motive, 0, source) == formula
    assert subst_formula(motive, 0, replacement) == rewritten


def test_bound_variable_is_not_mistaken_for_free_source() -> None:
    with pytest.raises(NoRewriteOccurrence, match="does not occur"):
        rewrite_first(Forall(Eq(Var(0), Var(0))), Var(0), ZERO)


def test_occurrence_order_now_enters_an_earlier_quantifier() -> None:
    formula = And(Forall(Eq(ZERO, ZERO)), Eq(ZERO, ZERO))

    rewritten, motive = rewrite_first(formula, ZERO, Succ(ZERO))

    assert rewritten == And(
        Forall(Eq(Succ(ZERO), ZERO)),
        Eq(ZERO, ZERO),
    )
    assert subst_formula(motive, 0, ZERO) == formula
    assert subst_formula(motive, 0, Succ(ZERO)) == rewritten


def test_replacement_with_an_outer_variable_is_not_captured() -> None:
    formula = Forall(Eq(ZERO, Var(0)))
    rewritten, motive = rewrite_first(formula, ZERO, Var(0))

    assert rewritten == Forall(Eq(Var(1), Var(0)))
    assert motive == Forall(Eq(Var(1), Var(0)))
    assert subst_formula(motive, 0, ZERO) == formula
    assert subst_formula(motive, 0, Var(0)) == rewritten


def test_nested_quantifiers_use_depth_two_without_moving_bound_indices() -> None:
    formula = Forall(Forall(Eq(Add(Var(2), Var(1)), Var(0))))
    rewritten, motive = rewrite_first(formula, Var(0), Succ(Var(0)))

    assert rewritten == Forall(
        Forall(Eq(Add(Succ(Var(2)), Var(1)), Var(0)))
    )
    assert subst_formula(motive, 0, Var(0)) == formula
    assert subst_formula(motive, 0, Succ(Var(0))) == rewritten


def test_under_binder_motive_builds_a_kernel_checked_transport() -> None:
    source, replacement = Var(0), Succ(Var(0))
    equation = Eq(source, replacement)
    old_formula = Forall(Eq(Var(1), Var(0)))
    new_formula, motive = rewrite_formula(old_formula, equation)
    certificate = EqSubst(motive, Hyp(0), Hyp(1))

    assert new_formula == Forall(Eq(Succ(Var(1)), Var(0)))
    assert check((equation, old_formula), certificate, new_formula)


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
