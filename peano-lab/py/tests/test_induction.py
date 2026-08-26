"""M2 induction, universal introduction, and specialization."""

from __future__ import annotations

from dataclasses import replace

import pytest

from peano_lab.engine.state import Goal, invariants_ok, start
from peano_lab.engine.tactics import TacticError, apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula
from peano_lab.kernel.proofs import ForallIntro, ImpIntro, Ind
from peano_lab.kernel.terms import Add, Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)


def _run(state, commands: tuple[tuple[str, str], ...]):
    for tactic, args in commands:
        state = apply_tactic(state, tactic, args)
    return state


def _snapshot(state):
    return (
        state.goals,
        state.partial,
        state.history,
        state.target,
        dict(state.subst),
    )


def test_zero_addition_is_proved_by_induction_in_six_tactics() -> None:
    target = parse_formula("forall n. 0 + n = n")
    commands = (
        ("induction", "n"),
        ("rewrite", "PA3"),
        ("refl", ""),
        ("rewrite", "PA4"),
        ("congr", ""),
        ("exact", "IH"),
    )
    state = _run(start(target), commands)

    certificate = checked_final(state, target)
    assert len(commands) <= 8
    assert len(state.history) == len(commands)
    assert type(certificate) is Ind
    assert check((), certificate, target)
    assert invariants_ok(state)


def test_intro_then_induction_on_a_named_context_variable_is_checked() -> None:
    target = parse_formula("forall n. 0 + n = n")
    commands = (
        ("intro", "n"),
        ("induction", "n"),
        ("rewrite", "PA3"),
        ("refl", ""),
        ("rewrite", "PA4"),
        ("congr", ""),
        ("exact", "IH"),
    )
    state = _run(start(target), commands)

    assert check((), checked_final(state, target), target)
    assert len(state.history) == 7


def test_context_variable_induction_is_capture_safe_below_an_inner_quantifier() -> None:
    target = parse_formula("forall n. forall m. n + m = n + m")
    commands = (
        ("intro", "n"),
        ("induction", "n"),
        ("intro", "m"),
        ("refl", ""),
        ("intro", "m"),
        ("refl", ""),
    )
    state = _run(start(target), commands)
    assert check((), checked_final(state, target), target)


def test_add_succ_left_is_interactively_provable() -> None:
    target = parse_formula("forall n. forall m. S n + m = S (n + m)")
    commands = (
        ("intro", "n"),
        ("induction", "m"),
        ("rewrite", "PA3"),
        ("rewrite", "PA3"),
        ("refl", ""),
        ("rewrite", "PA4"),
        ("rewrite", "PA4"),
        ("congr", ""),
        ("exact", "IH"),
    )
    state = _run(start(target), commands)

    assert check((), checked_final(state, target), target)


def test_intro_shifts_hypotheses_and_builds_forall_intro() -> None:
    target = parse_formula("forall x. x + 0 = x")
    state = _run(
        start(target),
        (("intro", "x"), ("rewrite", "PA3"), ("refl", "")),
    )
    assert check((), checked_final(state, target), target)


def test_specialize_adds_a_sound_local_instance() -> None:
    universal = Forall(Eq(Add(Var(0), ZERO), Var(0)))
    instance = Eq(Add(ONE, ZERO), ONE)
    original = Imp(universal, instance)
    initial = start(original)
    state = replace(
        initial,
        goals=(Goal((("h", universal),), instance),),
        partial_certificate_with_holes=ImpIntro(initial.partial),
    )

    state = apply_tactic(state, "specialize", "h 1")
    assert state.current().context[0] == ("h", instance)
    assert state.current().context[1][0] == "h_before"
    state = apply_tactic(state, "exact", "h")
    assert check((), checked_final(state, original), original)


def test_specialize_does_not_capture_an_outer_context_variable() -> None:
    # Below the outer n binder, h has type forall x. x = n.  Opening h at n
    # must produce n = n, not capture n as h's own binder.
    universal = Forall(Eq(Var(0), Var(1)))
    instance = Eq(Var(0), Var(0))
    original = Forall(Imp(universal, instance))
    initial = start(original)
    state = replace(
        initial,
        goals=(Goal((("h", universal),), instance, ("n",)),),
        partial_certificate_with_holes=ForallIntro(ImpIntro(initial.partial)),
    )

    state = apply_tactic(state, "specialize", "h n")
    state = apply_tactic(state, "exact", "h")
    assert check((), checked_final(state, original), original)


@pytest.mark.parametrize("argument", ["0", "S n", "n + 0"])
def test_induction_on_a_non_variable_fails_transactionally(argument: str) -> None:
    state = start(Eq(ZERO, ZERO))
    before = _snapshot(state)
    with pytest.raises(TacticError, match="variable name"):
        apply_tactic(state, "induction", argument)
    assert _snapshot(state) == before


def test_induction_requires_a_quantifier_or_named_context_variable() -> None:
    state = start(Eq(ZERO, ZERO))
    before = _snapshot(state)
    with pytest.raises(TacticError, match="universally quantified goal|context variable"):
        apply_tactic(state, "induction", "n")
    assert _snapshot(state) == before


def test_induction_hypothesis_cannot_close_the_wrong_step_goal() -> None:
    target = parse_formula("forall n. 0 + n = n")
    state = apply_tactic(start(target), "induction", "n")
    state = apply_tactic(state, "rewrite", "PA3")
    state = apply_tactic(state, "refl")
    before = _snapshot(state)

    with pytest.raises(TacticError, match="does not match"):
        apply_tactic(state, "exact", "IH")
    assert _snapshot(state) == before


def test_induction_variable_and_ih_names_never_collide() -> None:
    target = parse_formula("forall n. n = n")
    state = apply_tactic(start(target), "induction", "IH")
    step = state.goals[1]
    assert step.variables[0] == "IH"
    assert step.context[0][0] == "IH1"


def test_generated_parameter_name_avoids_hypothesis_names() -> None:
    atom = Eq(Var(0), Var(0))
    original = Forall(Imp(atom, atom))
    initial = start(original)
    state = replace(
        initial,
        goals=(Goal((("n_parameter", atom),), atom, ("n",)),),
        partial_certificate_with_holes=ForallIntro(ImpIntro(initial.partial)),
    )
    state = apply_tactic(state, "induction", "n")
    assert state.goals[1].variables == ("n", "n_parameter1")
    state = apply_tactic(state, "refl")
    state = apply_tactic(state, "refl")
    assert check((), checked_final(state, original), original)


def test_specialize_internal_name_avoids_term_variable_names() -> None:
    target = parse_formula("forall p. forall n. forall x. x = x")
    state = _run(
        start(target),
        (
            ("intro", "IH_before"),
            ("induction", "n"),
            ("intro", "x"),
            ("refl", ""),
            ("specialize", "IH 0"),
        ),
    )
    assert state.current().context[1][0] == "IH_before2"
    state = apply_tactic(state, "intro", "x")
    state = apply_tactic(state, "refl")
    assert check((), checked_final(state, target), target)


@pytest.mark.parametrize("name", ["S", "forall", "exists", "bot", "false"])
def test_binder_tactics_reject_reserved_surface_words(name: str) -> None:
    target = parse_formula("forall x. x = x")
    for tactic in ("intro", "induction"):
        state = start(target)
        before = _snapshot(state)
        with pytest.raises(TacticError, match="variable name"):
            apply_tactic(state, tactic, name)
        assert _snapshot(state) == before


def test_intro_and_specialize_reject_bad_shapes_transactionally() -> None:
    equality = Eq(ZERO, ZERO)
    state = start(equality)
    for tactic, args, message in (
        ("intro", "x", "universally quantified"),
        ("specialize", "h 0", "unknown hypothesis"),
        ("specialize", "h", "syntax"),
    ):
        before = _snapshot(state)
        with pytest.raises(TacticError, match=message):
            apply_tactic(state, tactic, args)
        assert _snapshot(state) == before


def test_specialize_rejects_a_metavariable_witness() -> None:
    universal = Forall(Eq(Var(0), Var(0)))
    original = Imp(universal, Eq(ZERO, ZERO))
    initial = start(original)
    state = replace(
        initial,
        goals=(Goal((("h", universal),), Eq(ZERO, ZERO)),),
        partial_certificate_with_holes=ImpIntro(initial.partial),
    )
    before = _snapshot(state)
    with pytest.raises(TacticError, match="concrete term"):
        apply_tactic(state, "specialize", "h ?")
    assert _snapshot(state) == before
