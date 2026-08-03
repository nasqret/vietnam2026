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
    instantiate_formula,
    invariants_ok,
    proof_identity_metrics,
    proof_metrics,
    proof_resource_metrics,
    record_step,
    replace_current_hole,
    start,
    shift_engine_formula,
    undo,
    unify_formulas,
    unify_terms,
)
from peano_lab.kernel.formulas import Eq, Forall
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


def test_identity_metrics_expose_sharing_without_changing_tree_metrics() -> None:
    shared = EqRefl(ZERO)
    certificate = EqTrans(shared, shared)

    assert proof_metrics(certificate) == (3, 2)
    assert proof_identity_metrics(certificate) == (2, 2, 1)
    assert proof_resource_metrics(certificate) == (3, 2, 2, 2, 1)


def test_fused_resource_metrics_preserve_nested_sharing_and_iterative_depth() -> None:
    leaf = EqRefl(ZERO)
    shared = EqTrans(leaf, leaf)
    certificate = EqTrans(shared, shared)

    assert proof_resource_metrics(certificate) == (
        *proof_metrics(certificate),
        *proof_identity_metrics(certificate),
    ) == (7, 3, 3, 4, 2)

    deep = leaf
    for _ in range(1_500):
        deep = EqTrans(deep, leaf)
    assert proof_resource_metrics(deep) == (3_001, 1_501, 1_501, 3_000, 1_500)


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


def test_scoped_meta_rejects_eigenvariable_escape_but_accepts_outer_terms() -> None:
    meta = fresh_meta()
    protected = MetaVar(meta.id, 1)

    assert unify_terms(protected, Var(0)) is None
    subst = unify_terms(protected, Var(1))
    assert subst == {meta.id: Var(0)}
    assert apply_formula_subst(Eq(protected, Var(0)), subst) == Eq(
        Var(1), Var(0)
    )


def test_formula_instantiation_tracks_meta_depth_through_nested_binders() -> None:
    first, second = fresh_meta(), fresh_meta()
    after_first = instantiate_formula(
        Forall(Eq(Var(1), Var(0))), first
    )
    assert after_first == Forall(Eq(MetaVar(first.id, 1), Var(0)))

    after_second = instantiate_formula(after_first.body, second)
    assert after_second == Eq(first, second)


def test_engine_shift_protects_meta_from_a_new_eigenvariable() -> None:
    meta = fresh_meta()
    shifted = shift_engine_formula(Eq(meta, Var(0)), 1)
    assert shifted == Eq(MetaVar(meta.id, 1), Var(1))


def test_meta_aliasing_cannot_indirectly_smuggle_an_eigenvariable() -> None:
    outer, inner = fresh_meta(), fresh_meta()
    linked = unify_terms(MetaVar(outer.id, 1), inner)
    assert linked == {inner.id: MetaVar(outer.id, 1)}

    assert unify_terms(inner, Var(0), linked) is None
    resolved = unify_terms(inner, Var(1), linked)
    assert resolved == {
        inner.id: MetaVar(outer.id, 1),
        outer.id: Var(0),
    }


@pytest.mark.parametrize("depth", range(4))
@pytest.mark.parametrize("candidate_index", range(6))
def test_scoped_meta_lowering_matches_exact_de_bruijn_levels(
    depth: int,
    candidate_index: int,
) -> None:
    meta = MetaVar(20_000_000 + depth, depth)
    subst = unify_terms(meta, Var(candidate_index))
    if candidate_index < depth:
        assert subst is None
    else:
        assert subst == {meta.id: Var(candidate_index - depth)}
        assert apply_formula_subst(Eq(meta, ZERO), subst) == Eq(
            Var(candidate_index), ZERO
        )
