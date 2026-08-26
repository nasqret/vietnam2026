"""Growing attack oracle: tactics may fail, but they may never forge QED."""

from __future__ import annotations

from dataclasses import replace

import pytest

from peano_lab.engine.state import Goal, MetaVar, start
from peano_lab.engine.tactics import (
    InvalidProof,
    TacticError,
    checked_final,
    exact,
    induction,
    intro,
    refl,
    rewrite,
    exists_,
)
from peano_lab.kernel.checker import check, check_classical
from peano_lab.kernel.formulas import Bot, Eq, Forall, Imp, parse_formula
from peano_lab.kernel.proofs import DNE, EqRefl, EqSubst, Hyp
from peano_lab.kernel.terms import Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)
FALSE = Eq(ZERO, ONE)


def _assert_transactional_failure(state, tactic, args: str, pattern: str) -> None:
    snapshot = (
        state.goals,
        state.partial,
        state.history,
        state.target,
        dict(state.subst),
    )
    with pytest.raises(TacticError, match=pattern):
        tactic(state, args)
    assert (
        state.goals,
        state.partial,
        state.history,
        state.target,
        dict(state.subst),
    ) == snapshot


def test_zero_cannot_be_proved_equal_to_its_successor() -> None:
    state = start(FALSE)
    _assert_transactional_failure(state, refl, "", "not identical")
    with pytest.raises(InvalidProof, match="open"):
        checked_final(state, FALSE)


def test_unknown_hypothesis_cannot_be_smuggled_into_certificate() -> None:
    state = start(Eq(ZERO, ZERO))
    _assert_transactional_failure(state, exact, "invented", "unknown hypothesis")
    assert not check((), Hyp(0), state.target)


def test_non_equation_cannot_drive_rewrite() -> None:
    non_equation = Imp(Eq(ZERO, ZERO), Eq(ZERO, ZERO))
    state = start(Eq(ZERO, ZERO))
    state = replace(
        state,
        goals=(Goal((("h", non_equation),), state.target),),
    )
    _assert_transactional_failure(state, rewrite, "h", "not an equation")


def test_original_target_is_not_rewritten_by_tactic_substitution() -> None:
    meta = MetaVar(10_000_000)
    original = FALSE
    state = start(original)
    state = replace(state, goals=(Goal((), Eq(meta, ZERO)),))
    completed = refl(state)
    assert completed.target is original
    assert completed.goals == ()
    with pytest.raises(InvalidProof, match="independent kernel"):
        checked_final(completed, original)


def test_forged_closed_state_is_checked_against_original_goal() -> None:
    forged = replace(
        start(FALSE), goals=(), partial_certificate_with_holes=EqRefl(ZERO)
    )
    before = forged
    with pytest.raises(InvalidProof, match="independent kernel"):
        checked_final(forged, FALSE)
    assert forged == before
    assert forged.target == FALSE


def test_replacing_the_states_target_cannot_replace_the_session_original() -> None:
    true_formula = Eq(ZERO, ZERO)
    forged = replace(
        start(FALSE),
        goals=(),
        partial_certificate_with_holes=EqRefl(ZERO),
        target=true_formula,
    )
    with pytest.raises(InvalidProof, match="session's original goal"):
        checked_final(forged, FALSE)
    assert check((), forged.partial, true_formula)
    assert not check((), forged.partial, FALSE)


def test_unresolved_engine_metavariable_never_reaches_kernel_qed() -> None:
    meta = MetaVar(10_000_001)
    state = replace(
        start(Eq(ZERO, ZERO)),
        goals=(),
        partial_certificate_with_holes=EqRefl(meta),
    )
    with pytest.raises(InvalidProof, match="term metavariable"):
        checked_final(state, Eq(ZERO, ZERO))
    assert not check((), EqRefl(meta), Eq(ZERO, ZERO))


def test_mutating_visible_goal_does_not_mutate_original_statement() -> None:
    state = start(FALSE)
    state = replace(state, goals=(Goal((), Eq(ZERO, ZERO)),))
    completed = refl(state)
    assert completed.target == FALSE
    with pytest.raises(InvalidProof):
        checked_final(completed, FALSE)


def test_induction_hypothesis_is_scoped_only_to_the_step_and_cannot_be_misused() -> None:
    target = parse_formula("forall n. 0 + n = n")
    state = induction(start(target), "n")

    assert state.current().context == ()
    _assert_transactional_failure(state, exact, "IH", "unknown hypothesis")

    state = rewrite(state, "PA3")
    state = refl(state)
    assert state.current().context[0][0] == "IH"
    _assert_transactional_failure(state, exact, "IH", "does not match")
    with pytest.raises(InvalidProof, match="open"):
        checked_final(state, target)


def test_forged_dne_certificate_cannot_cross_the_default_off_boundary() -> None:
    proposition = FALSE
    theorem = Imp(Imp(Imp(proposition, Bot()), Bot()), proposition)
    forged = replace(
        start(theorem),
        goals=(),
        partial_certificate_with_holes=DNE(proposition),
    )
    assert check_classical((), forged.partial, theorem)
    assert not check((), forged.partial, theorem)
    with pytest.raises(InvalidProof, match="independent kernel"):
        checked_final(forged, theorem)


def test_existential_meta_cannot_unify_with_a_later_eigenvariable() -> None:
    target = parse_formula("exists x. forall y. x = y")
    state = exists_(start(target), "?")
    state = intro(state, "y")
    _assert_transactional_failure(state, refl, "", "not identical")
    with pytest.raises(InvalidProof, match="open"):
        checked_final(state, target)


def test_naive_bound_variable_rewrite_certificate_is_rejected() -> None:
    equation = Eq(Var(0), ZERO)  # an outer parameter n = 0
    reflexive_binder = Forall(Eq(Var(0), Var(0)))
    captured_target = Forall(Eq(ZERO, Var(0)))
    naive_motive = Forall(Eq(Var(0), Var(0)))
    forged = EqSubst(naive_motive, Hyp(0), Hyp(1))

    assert not check(
        (equation, reflexive_binder),
        forged,
        captured_target,
    )
