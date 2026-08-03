"""M1 equational tactics, transactional failures, and checked finalization."""

from __future__ import annotations

from dataclasses import replace

import pytest

import peano_lab.engine.tactics as tactics_module
from peano_lab.engine.state import Goal, holes_in, invariants_ok, start
from peano_lab.engine.tactics import (
    InvalidProof,
    TacticError,
    TacticLimit,
    apply_tactic,
    assumption,
    checked_final,
    congr,
    exact,
    refl,
    rewrite,
    symm,
    trans,
    undo,
)
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import ImpIntro
from peano_lab.kernel.terms import Add, Succ, Zero


ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)


def _state_with_intros(original, context, target):
    """Build the M1 mid-state that future intro tactics will create."""

    state = start(original)
    partial = state.partial
    for _ in context:  # context is newest-first; wrappers are outer-to-inner
        partial = ImpIntro(partial)
    return replace(
        state,
        goals=(Goal(context, target),),
        partial_certificate_with_holes=partial,
    )


def test_refl_closes_and_qed_is_independently_kernel_checked() -> None:
    target = Eq(ZERO, ZERO)
    state = refl(start(target))
    certificate = checked_final(state, target)
    assert state.is_done()
    assert invariants_ok(state)
    assert check((), certificate, target)


def test_symm_and_congr_build_kernel_certificates() -> None:
    symmetric = symm(start(Eq(ZERO, ZERO)))
    symmetric = refl(symmetric)
    symmetric_target = Eq(ZERO, ZERO)
    assert check((), checked_final(symmetric, symmetric_target), symmetric_target)

    target = Eq(Add(ZERO, ONE), Add(ZERO, ONE))
    state = congr(start(target))
    assert len(state.goals) == 2
    state = refl(state)
    state = refl(state)
    assert check((), checked_final(state, target), target)


def test_trans_fresh_meta_is_shared_and_propagates_to_sibling_goal() -> None:
    target = Eq(ZERO, ZERO)
    state = trans(start(target), "?")
    assert len(state.goals) == 2
    assert state.goals[0].target.right == state.goals[1].target.left

    state = refl(state)
    assert state.goals[0].target == Eq(ZERO, ZERO)
    assert state.subst
    state = refl(state)
    assert check((), checked_final(state, target), target)


def test_exact_and_assumption_use_only_named_context_hypotheses() -> None:
    atom = Eq(ZERO, ZERO)
    original = Imp(atom, atom)
    context = (("h", atom),)

    exact_state = _state_with_intros(original, context, atom)
    assert check((), checked_final(exact(exact_state, "h"), original), original)

    assumption_state = _state_with_intros(original, context, atom)
    assert check((), checked_final(assumption(assumption_state), original), original)


def test_builtin_pa_rewrites_prove_a_closed_arithmetic_equation() -> None:
    target, names = parse_formula_with_names("S 0 + S 0 = S (S 0)")
    state = start(target, names)
    logger = TraceLogger(session_id="m1-arithmetic")
    state = apply_tactic(state, "rewrite", "PA4", trace=logger)
    state = apply_tactic(state, "rewrite", "PA3", trace=logger)
    state = apply_tactic(state, "refl", trace=logger)
    certificate = checked_final(state, target, trace=logger)
    assert check((), certificate, target)
    assert len(state.history) == 3
    assert [record.get("tactic") for record in logger.records[:-1]] == [
        "rewrite PA4",
        "rewrite PA3",
        "refl",
    ]
    assert logger.records[-1]["qed"] is True


def test_hypothesis_rewrite_on_goal_has_the_correct_certificate_direction() -> None:
    equation = Eq(ZERO, ONE)
    target = Eq(Succ(ZERO), Succ(ONE))
    original = Imp(equation, target)
    state = _state_with_intros(original, (("h", equation),), target)
    state = rewrite(state, "h")
    assert state.current().target == Eq(Succ(ONE), Succ(ONE))
    state = refl(state)
    assert check((), checked_final(state, original), original)


def test_reverse_hypothesis_rewrite_has_the_correct_certificate_direction() -> None:
    equation = Eq(ZERO, ONE)
    target = Eq(Succ(ONE), Succ(ZERO))
    original = Imp(equation, target)
    state = _state_with_intros(original, (("h", equation),), target)
    state = rewrite(state, "<- h")
    assert state.current().target == Eq(Succ(ZERO), Succ(ZERO))
    state = refl(state)
    assert check((), checked_final(state, original), original)


def test_rewrite_at_hypothesis_uses_a_sound_local_cut() -> None:
    equation = Eq(ZERO, ONE)
    premise = Eq(Succ(ZERO), Succ(ZERO))
    target = Eq(Succ(ONE), Succ(ZERO))
    original = Imp(equation, Imp(premise, target))
    context = (("p", premise), ("h", equation))
    state = _state_with_intros(original, context, target)

    state = rewrite(state, "h at p")
    assert state.current().context[0] == ("p", target)
    assert state.current().context[1][0] == "p_before"
    state = exact(state, "p")
    assert check((), checked_final(state, original), original)


@pytest.mark.parametrize(
    ("operation", "args", "message"),
    [
        (refl, "", "two sides"),
        (exact, "unknown", "unknown hypothesis"),
        (rewrite, "unknown", "unknown hypothesis or PA axiom"),
        (rewrite, "PA1", "not an equational"),
    ],
)
def test_failed_tactics_are_transactional(operation, args: str, message: str) -> None:
    target = Eq(ZERO, ONE)
    state = start(target)
    before_goals = state.goals
    before_partial = state.partial
    before_history = state.history
    before_subst = dict(state.subst)
    with pytest.raises(TacticError, match=message):
        operation(state, args)
    assert state.goals == before_goals
    assert state.partial == before_partial
    assert state.history == before_history
    assert dict(state.subst) == before_subst


def test_commit_uses_one_fused_resource_snapshot_transactionally(monkeypatch) -> None:
    state = start(Eq(ZERO, ZERO))
    before_goals = state.goals
    before_partial = state.partial
    before_history = state.history
    before_subst = state.subst
    calls = 0

    def over_limit(_proof):
        nonlocal calls
        calls += 1
        return (tactics_module.MAX_LIVE_PROOF_NODES + 1, 1, 1, 0, 0)

    monkeypatch.setattr(tactics_module, "proof_resource_metrics", over_limit)

    with pytest.raises(TacticLimit, match="live-proof-node limit"):
        refl(state)

    assert calls == 1
    assert state.goals is before_goals
    assert state.partial is before_partial
    assert state.history is before_history
    assert state.subst is before_subst


def test_rewrite_rejects_a_non_equation_hypothesis_transactionally() -> None:
    proposition = Imp(Eq(ZERO, ZERO), Eq(ZERO, ZERO))
    state = replace(
        start(Eq(ZERO, ZERO)),
        goals=(Goal((("h", proposition),), Eq(ZERO, ZERO)),),
    )
    with pytest.raises(TacticError, match="not an equation"):
        rewrite(state, "h")
    assert state.goals[0].context[0] == ("h", proposition)


def test_undo_restores_the_exact_pre_tactic_state() -> None:
    initial = start(Eq(ZERO, ZERO))
    completed = refl(initial)
    assert undo(completed) is initial
    with pytest.raises(TacticError, match="nothing to undo"):
        undo(initial)


def test_checked_final_rejects_false_or_forged_qed_and_keeps_state() -> None:
    false_target = Eq(ZERO, ONE)
    state = start(false_target)
    forged = replace(
        state,
        goals=(),
        partial_certificate_with_holes=state.partial.__class__(state.partial.id),
    )
    with pytest.raises(InvalidProof, match="hole or term metavariable"):
        checked_final(forged, false_target)

    wrong_certificate = replace(
        forged, partial_certificate_with_holes=peano_refl_zero()
    )
    with pytest.raises(InvalidProof, match="independent kernel"):
        checked_final(wrong_certificate, false_target)
    assert wrong_certificate.target == false_target
    assert wrong_certificate.goals == ()


def peano_refl_zero():
    from peano_lab.kernel.proofs import EqRefl

    return EqRefl(ZERO)


def test_dispatch_wires_success_failure_and_footer_trace_records() -> None:
    logger = TraceLogger(session_id="m1-test")
    target = Eq(ZERO, ZERO)
    state = start(target)
    with pytest.raises(TacticError, match="unknown tactic"):
        apply_tactic(state, "bogus", trace=logger)
    state = apply_tactic(state, "refl", trace=logger)
    certificate = checked_final(state, target, trace=logger)
    assert [record.get("status") for record in logger.records[:2]] == ["error", "ok"]
    assert logger.records[-1]["qed"] is True
    assert check((), certificate, state.target)


def test_trace_can_render_an_unresolved_shared_metavariable() -> None:
    logger = TraceLogger(session_id="meta-trace")
    state = start(Eq(ZERO, ZERO))
    state = apply_tactic(state, "trans", "?", trace=logger)
    assert len(logger.records[0]["goals_after"]) == 2
    first, second = logger.records[0]["goals_after"]
    assert "?t1" in first
    assert "?t1" in second
