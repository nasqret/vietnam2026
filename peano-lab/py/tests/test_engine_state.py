"""M1 proof-state, hole, and metavariable discipline."""

from dataclasses import replace

import pytest

from peano_lab.engine.state import (
    Goal,
    Hole,
    MetaVar,
    StateError,
    apply_formula_subst,
    apply_subst_everywhere,
    final_certificate,
    fresh_hole,
    fresh_meta,
    holes_in,
    invariants_ok,
    record_step,
    replace_current_hole,
    start,
    undo,
    unify_formulas,
    unify_terms,
)
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import EqRefl, EqTrans
from peano_lab.kernel.terms import Add, Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)


def test_start_has_one_goal_one_hole_and_original_target() -> None:
    target = Eq(Add(Var(0), ZERO), Var(0))
    state = start(target, ("n",))
    assert state.current() == Goal((), target, ("n",))
    assert state.target is target
    assert len(holes_in(state.partial)) == 1
    assert invariants_ok(state)
    assert final_certificate(state) is None


def test_only_engine_metavariables_are_flexible() -> None:
    meta = fresh_meta()
    subst = unify_terms(Add(meta, ZERO), Add(ONE, ZERO))
    assert subst == {meta.id: ONE}
    assert unify_terms(Var(0), Var(1)) is None
    assert unify_terms(Add(ZERO, ZERO), Succ(ZERO)) is None


def test_unification_is_copy_on_write_and_has_occurs_check() -> None:
    first = fresh_meta()
    second = fresh_meta()
    original = {first.id: ZERO}
    extended = unify_terms(second, ONE, original)
    assert original == {first.id: ZERO}
    assert extended == {first.id: ZERO, second.id: ONE}
    assert unify_terms(second, Succ(second), original) is None
    assert original == {first.id: ZERO}


def test_formula_unification_shares_one_substitution_across_term_leaves() -> None:
    meta = fresh_meta()
    left = Eq(Add(meta, ZERO), meta)
    right = Eq(Add(ONE, ZERO), ONE)
    subst = unify_formulas(left, right)
    assert subst == {meta.id: ONE}
    assert apply_formula_subst(left, subst) == right


def test_substitution_propagates_to_sibling_goals_and_partial_certificate_only() -> None:
    meta = fresh_meta()
    original_target = Eq(ZERO, ZERO)
    state = start(original_target)
    holes = (fresh_hole(), fresh_hole())
    state = replace(
        state,
        goals=(
            Goal((), Eq(meta, ZERO)),
            Goal((('h', Eq(meta, meta)),), Eq(Succ(meta), ONE)),
        ),
        partial_certificate_with_holes=EqTrans(holes[0], holes[1]),
        subst={},
    )
    propagated = apply_subst_everywhere(state, {meta.id: ZERO})
    assert propagated.goals[0].target == Eq(ZERO, ZERO)
    assert propagated.goals[1].context[0][1] == Eq(ZERO, ZERO)
    assert propagated.goals[1].target == Eq(ONE, ONE)
    assert propagated.target is original_target
    assert state.goals[0].target == Eq(meta, ZERO)
    assert state.subst == {}


def test_hole_replacement_preserves_goal_traversal_order() -> None:
    state = start(Eq(ZERO, ZERO))
    left, right = fresh_hole(), fresh_hole()
    goals = (Goal((), Eq(ZERO, ZERO)), Goal((), Eq(ONE, ONE)))
    state = replace_current_hole(state, EqTrans(left, right), goals)
    assert holes_in(state.partial) == (left.id, right.id)
    assert state.goals == goals
    assert invariants_ok(state)

    closed_left = replace_current_hole(state, EqRefl(ZERO), ())
    assert holes_in(closed_left.partial) == (right.id,)
    assert closed_left.goals == (goals[1],)
    assert invariants_ok(closed_left)


def test_mismatched_goal_and_hole_counts_are_rejected() -> None:
    state = start(Eq(ZERO, ZERO))
    with pytest.raises(StateError, match="do not match"):
        replace_current_hole(state, EqTrans(fresh_hole(), fresh_hole()), ())


def test_history_is_transactional_and_undo_restores_exact_snapshot() -> None:
    before = start(Eq(ZERO, ZERO))
    after = replace_current_hole(before, EqRefl(ZERO), ())
    committed = record_step(before, after, "refl", "")
    assert committed.history[-1].state_before is before
    assert undo(committed) is before
    with pytest.raises(StateError, match="nothing to undo"):
        undo(before)


def test_substitution_and_history_snapshots_are_deeply_immutable() -> None:
    meta = fresh_meta()
    source = {meta.id: ZERO}
    before = replace(start(Eq(ZERO, ZERO)), subst=source)
    source[meta.id] = ONE
    assert before.subst[meta.id] == ZERO
    with pytest.raises(TypeError):
        before.subst[meta.id] = ONE  # type: ignore[index]

    after = replace_current_hole(before, EqRefl(ZERO), ())
    committed = record_step(before, after, "refl", "")
    assert committed.history[-1].state_before is before
    assert undo(committed).subst[meta.id] == ZERO


def test_final_certificate_rejects_unresolved_metas_and_open_holes() -> None:
    meta = fresh_meta()
    state = start(Eq(ZERO, ZERO))
    state = replace_current_hole(state, EqRefl(meta), ())
    assert final_certificate(state) is None
    resolved = apply_subst_everywhere(state, {meta.id: ZERO})
    assert final_certificate(resolved) == EqRefl(ZERO)


def test_engine_nodes_are_distinct_from_rigid_kernel_nodes() -> None:
    assert isinstance(fresh_meta(), MetaVar)
    assert isinstance(fresh_hole(), Hole)
    assert type(fresh_meta()) is not Var
