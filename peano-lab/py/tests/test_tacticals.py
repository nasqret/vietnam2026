"""M4 tactic-language laws: composition, focus, and exact rollback."""

from __future__ import annotations

from dataclasses import replace

import pytest

from peano_lab.engine.state import (
    Goal,
    ProofState,
    holes_in,
    invariants_ok,
    metas_in_formula,
    start,
)
from peano_lab.engine.tacticals import all_goals, first, focus, orelse, repeat, then
from peano_lab.engine.tactics import (
    TacticError,
    TacticLimit,
    apply_tactic,
    checked_final,
    induction,
    refl,
    simp,
    split,
    symm,
    trans,
    undo,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, parse_formula
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Succ, Zero


ZERO = Zero()
ONE = Succ(ZERO)
TRUE = Eq(ZERO, ZERO)
FALSE = Eq(ZERO, ONE)


def _snapshot(state):
    return state.goals, state.partial, state.history, dict(state.subst)


def _fail(_state, _args: str = ""):
    raise TacticError("the test branch failed.")


def test_then_applies_rhs_to_every_goal_made_by_lhs_as_one_transaction() -> None:
    target = And(TRUE, TRUE)
    initial = start(target)
    result = then(split, refl)(initial, "")

    certificate = checked_final(result, target)
    assert check((), certificate, target)
    assert len(result.history) == 1
    assert result.history[-1].tactic == "then"
    assert undo(result) is initial


def test_induction_then_simp_proves_add_comm_with_prior_ladder_lemmas() -> None:
    target = parse_formula(
        "(forall x. 0 + x = x) -> "
        "(forall x y. S x + y = S (x + y)) -> "
        "forall n m. n + m = m + n"
    )
    state = apply_tactic(start(target), "intro", "zero_add")
    state = apply_tactic(state, "intro", "add_succ_left")

    def induction_n(current, _args: str = ""):
        return induction(current, "n")

    def ladder_simp(current, _args: str = ""):
        names = {name for name, _ in current.current().context}
        arguments = (
            "[add_succ_left, IH]" if "IH" in names else "[zero_add]"
        )
        return simp(current, arguments)

    completed = then(induction_n, ladder_simp)(state, "")

    assert check((), checked_final(completed, target), target)
    assert completed.history[-1].tactic == "then"


def test_then_does_not_apply_rhs_to_an_old_tail_goal() -> None:
    initial = trans(start(TRUE), "0")
    result = then(symm, refl)(initial, "")

    assert len(result.goals) == 1
    assert result.current().target == TRUE
    assert len(result.history) == len(initial.history) + 1
    assert undo(result) is initial


def test_orelse_discards_failed_branch_holes_metas_subst_and_history() -> None:
    initial = start(TRUE)
    before = _snapshot(initial)

    def make_meta_goals(state, _args: str = ""):
        return trans(state, "?")

    # The left branch allocates a meta and two holes, then fails.  The right
    # branch must see precisely the original one-hole, empty-substitution state.
    def fallback(state, _args: str = ""):
        assert state is initial
        assert _snapshot(state) == before
        return refl(state)

    result = orelse(then(make_meta_goals, _fail), fallback)(initial, "")
    assert result.is_done()
    assert result.partial == EqRefl(ZERO)
    assert dict(result.subst) == {}
    assert [step.tactic for step in result.history] == ["orelse"]
    assert undo(result) is initial
    assert _snapshot(initial) == before


def test_orelse_two_failures_leave_the_input_exactly_unchanged() -> None:
    initial = start(FALSE)
    before = _snapshot(initial)
    with pytest.raises(TacticError, match="test branch"):
        orelse(_fail, _fail)(initial, "")
    assert _snapshot(initial) == before


def test_repeat_closes_goals_and_stops_on_no_progress_or_a_cycle() -> None:
    target = TRUE
    closed = repeat(refl)(start(target), "")
    assert check((), checked_final(closed, target), target)

    calls = 0

    def no_progress(state, _args: str = ""):
        nonlocal calls
        calls += 1
        return state

    initial = start(FALSE)
    unchanged = repeat(no_progress)(initial, "")
    assert calls == 1
    assert unchanged.goals == initial.goals
    assert undo(unchanged) is initial

    # ``symm`` always succeeds, but its goals alternate.  Logical-cycle
    # detection prevents an ever-growing EqSym(EqSym(...)) certificate.
    cycled = repeat(symm)(initial, "")
    assert cycled.goals == initial.goals
    assert len(cycled.history) == 1
    assert invariants_ok(cycled)


def test_repeat_has_a_finite_guard_even_for_strictly_growing_bad_tactic() -> None:
    initial = start(FALSE)
    before = _snapshot(initial)

    def grow(state, _args: str = ""):
        goal = state.current()
        assert goal is not None
        deeper = Eq(Succ(goal.target.left), goal.target.right)
        return replace(state, goals=(Goal(goal.context, deeper, goal.variables),))

    with pytest.raises(TacticLimit, match="termination guard"):
        repeat(grow)(initial, "")
    assert _snapshot(initial) == before

    def limited(_state, _args: str = ""):
        raise TacticLimit("planned child budget exhaustion")

    with pytest.raises(TacticLimit, match="planned child budget exhaustion"):
        repeat(limited)(initial, "")
    assert _snapshot(initial) == before


def test_first_tries_candidates_left_to_right_as_one_transaction() -> None:
    initial = start(TRUE)
    result = first([_fail, refl])(initial, "")
    assert result.is_done()
    assert [step.tactic for step in result.history] == ["first"]
    assert undo(result) is initial


def test_all_goals_snapshots_inputs_and_does_not_revisit_new_subgoals() -> None:
    target = And(And(TRUE, TRUE), And(TRUE, TRUE))
    initial = split(start(target))
    expanded = all_goals(split)(initial, "")

    assert len(expanded.goals) == 4
    assert all(goal.target == TRUE for goal in expanded.goals)
    assert len(expanded.history) == len(initial.history) + 1
    assert undo(expanded) is initial

    closed = all_goals(refl)(expanded, "")
    assert check((), checked_final(closed, target), target)


def test_all_goals_failure_rolls_back_earlier_successes() -> None:
    initial = split(start(And(TRUE, FALSE)))
    before = _snapshot(initial)
    with pytest.raises(TacticError, match="not identical"):
        all_goals(refl)(initial, "")
    assert _snapshot(initial) == before


def test_focus_is_one_based_and_propagates_substitution_to_siblings() -> None:
    target = TRUE
    initial = trans(start(target), "?")
    meta_goal = initial.goals[0].target
    assert meta_goal != TRUE

    second_closed = focus(2, refl)(initial, "")
    assert second_closed.goals == (Goal((), TRUE),)
    assert dict(second_closed.subst)
    assert len(holes_in(second_closed.partial)) == 1
    assert undo(second_closed) is initial

    completed = focus(1, refl)(second_closed, "")
    assert check((), checked_final(completed, target), target)


def test_focused_tactics_do_not_default_a_meta_constrained_by_a_sibling() -> None:
    target = parse_formula("(forall x. x = x -> 0 = x) -> 0 = 1")
    state = apply_tactic(start(target), "intro", "h")
    state = apply_tactic(state, "trans", "?")
    state = apply_tactic(state, "apply", "h")
    assert len(state.goals) == 2
    assert metas_in_formula(state.goals[-1].target, state.subst)

    first_closed = focus(1, refl)(state, "")
    assert len(first_closed.goals) == 1
    assert metas_in_formula(first_closed.current().target, first_closed.subst)
    assert ZERO not in first_closed.subst.values()
    completed = focus(1, refl)(first_closed, "")

    assert ONE in completed.subst.values()
    assert check((), checked_final(completed, target), target)


def test_all_goals_preserves_a_meta_until_a_later_sibling_constrains_it() -> None:
    target = parse_formula("(forall x. x = x -> 0 = x) -> 0 = 1")
    state = apply_tactic(start(target), "intro", "h")
    state = apply_tactic(state, "trans", "?")
    state = apply_tactic(state, "apply", "h")

    completed = all_goals(refl)(state, "")

    assert ONE in completed.subst.values()
    assert check((), checked_final(completed, target), target)


@pytest.mark.parametrize("bad_number", [0, -1, True, 1.5, "1"])
def test_focus_rejects_malformed_goal_numbers(bad_number) -> None:
    with pytest.raises(TacticError, match="positive one-based"):
        focus(bad_number, refl)


def test_tactical_syntax_errors_are_final_and_transactional() -> None:
    initial = start(TRUE)
    before = _snapshot(initial)

    with pytest.raises(TacticError, match="non-empty list"):
        first([])
    with pytest.raises(TacticError, match="needs a tactic"):
        then(refl, object())
    with pytest.raises(TacticError, match="does not exist"):
        focus(2, refl)(initial, "")
    with pytest.raises(TacticError, match="no further arguments"):
        repeat(refl)(initial, "unexpected")

    assert _snapshot(initial) == before


def test_tacticals_reject_invalid_or_subclassed_states_before_indexing() -> None:
    initial = start(TRUE)
    invalid = replace(initial, goals=())  # one certificate hole, zero goals

    class PretendState(ProofState):
        pass

    subclassed = PretendState(
        initial.goals,
        initial.partial,
        initial.history,
        initial.target,
        initial.subst,
        initial.variables,
    )
    missing_fields = object.__new__(ProofState)
    malformed_partial = ProofState(
        initial.goals,
        object(),  # type: ignore[arg-type]
        (),
        initial.target,
    )
    malformed_subst = ProofState(
        initial.goals,
        initial.partial,
        (),
        initial.target,
        {0: ZERO, "x": ZERO},  # type: ignore[dict-item]
    )
    for bad in (
        invalid,
        subclassed,
        missing_fields,
        malformed_partial,
        malformed_subst,
    ):
        for tactical in (focus(1, refl), then(refl, refl), all_goals(refl)):
            with pytest.raises(TacticError, match="valid exact ProofState"):
                tactical(bad, "")


def test_focused_child_contract_rejects_bad_results_and_lost_state() -> None:
    initial = trans(start(TRUE), "?")
    initial = refl(initial)
    before = _snapshot(initial)

    class PretendState(ProofState):
        pass

    def subclass_result(state, _args: str = ""):
        return PretendState(
            state.goals,
            state.partial,
            state.history,
            state.target,
            state.subst,
            state.variables,
        )

    bad_children = (
        subclass_result,
        lambda state, _args="": replace(
            state, partial_certificate_with_holes=object()
        ),
        lambda state, _args="": replace(state, history=()),
        lambda state, _args="": replace(state, subst={}),
    )
    for child in bad_children:
        with pytest.raises(TacticError):
            focus(1, child)(initial, "")
        assert _snapshot(initial) == before
