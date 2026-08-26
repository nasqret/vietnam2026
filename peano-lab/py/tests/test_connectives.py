"""M3 full first-order connective tactics and classical-mode boundary."""

from __future__ import annotations

from dataclasses import replace

import pytest

from peano_lab.engine.state import Goal, start
from peano_lab.engine.tactics import (
    InvalidProof,
    TacticError,
    apply_tactic,
    checked_final,
    hint,
    logic_banner,
    set_classical_mode,
)
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.checker import check, check_classical
from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import ForallIntro, ImpIntro
from peano_lab.kernel.terms import Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)


def _run(state, commands, *, classical: bool = False):
    for tactic, args in commands:
        state = apply_tactic(state, tactic, args, classical=classical)
    return state


def _snapshot(state):
    return (
        state.goals,
        state.partial,
        state.history,
        state.target,
        dict(state.subst),
    )


def test_implication_apply_uses_hypotheses_and_builds_application() -> None:
    target = parse_formula("(0 = 0 -> 1 = 1) -> 0 = 0 -> 1 = 1")
    state = _run(
        start(target),
        (
            ("intro", "f"),
            ("intro", "p"),
            ("apply", "f"),
            ("exact", "p"),
        ),
    )
    assert check((), checked_final(state, target), target)


def test_apply_instantiates_multiple_universals_with_shared_scoped_metas() -> None:
    target = parse_formula("(forall x y. x = y) -> 0 = 1")
    state = _run(
        start(target),
        (("intro", "h"), ("apply", "h")),
    )
    assert state.subst
    assert check((), checked_final(state, target), target)


def test_apply_closes_a_vacuous_universal_with_canonical_zero() -> None:
    target = parse_formula("(forall x. 0 = 0) -> 0 = 0")
    state = _run(start(target), (("intro", "h"), ("apply", "h")))

    assert not state.goals
    assert ZERO in state.subst.values()
    assert check((), checked_final(state, target), target)


def test_split_left_and_right_have_kernel_checked_certificates() -> None:
    conjunction = parse_formula("0 = 0 -> 1 = 1 -> 0 = 0 /\\ 1 = 1")
    state = _run(
        start(conjunction),
        (
            ("intro", "p"),
            ("intro", "q"),
            ("split", ""),
            ("exact", "p"),
            ("exact", "q"),
        ),
    )
    assert check((), checked_final(state, conjunction), conjunction)

    left_target = parse_formula("0 = 0 -> 0 = 0 \\/ 0 = 1")
    left_state = _run(
        start(left_target),
        (("intro", "p"), ("left", ""), ("exact", "p")),
    )
    assert check((), checked_final(left_state, left_target), left_target)

    right_target = parse_formula("0 = 0 -> 0 = 1 \\/ 0 = 0")
    right_state = _run(
        start(right_target),
        (("intro", "p"), ("right", ""), ("exact", "p")),
    )
    assert check((), checked_final(right_state, right_target), right_target)


def test_cases_handles_disjunction_and_conjunction() -> None:
    commuted_or = parse_formula(
        "(0 = 0 \\/ 1 = 1) -> 1 = 1 \\/ 0 = 0"
    )
    state = _run(
        start(commuted_or),
        (
            ("intro", "h"),
            ("cases", "h"),
            ("right", ""),
            ("exact", "h_left"),
            ("left", ""),
            ("exact", "h_right"),
        ),
    )
    assert check((), checked_final(state, commuted_or), commuted_or)

    commuted_and = parse_formula(
        "(0 = 0 /\\ 1 = 1) -> 1 = 1 /\\ 0 = 0"
    )
    state = _run(
        start(commuted_and),
        (
            ("intro", "h"),
            ("cases", "h"),
            ("split", ""),
            ("exact", "h_right"),
            ("exact", "h_left"),
        ),
    )
    assert check((), checked_final(state, commuted_and), commuted_and)


def test_cases_bottom_and_exfalso_are_both_sound() -> None:
    target = parse_formula("false -> 0 = 1")
    by_cases = _run(start(target), (("intro", "h"), ("cases", "h")))
    assert check((), checked_final(by_cases, target), target)

    by_exfalso = _run(
        start(target),
        (("intro", "h"), ("exfalso", ""), ("exact", "h")),
    )
    assert check((), checked_final(by_exfalso, target), target)


def test_exists_concrete_and_inferred_witnesses_kernel_check() -> None:
    target = parse_formula("exists x. x = 0")
    concrete = _run(start(target), (("exists", "0"), ("refl", "")))
    assert check((), checked_final(concrete, target), target)

    inferred = _run(start(target), (("exists", "?"), ("refl", "")))
    certificate = checked_final(inferred, target)
    assert inferred.subst
    assert check((), certificate, target)


def test_vacuous_existential_defaults_its_proof_only_witness_to_zero() -> None:
    target = parse_formula("exists x. 0 = 0")
    state = apply_tactic(start(target), "exists", "?")

    assert ZERO in state.subst.values()
    state = apply_tactic(state, "refl")
    assert check((), checked_final(state, target), target)


def test_apply_does_not_default_a_meta_shared_by_sibling_goals() -> None:
    target = parse_formula(
        "(forall x. x = 1 -> x = 1 -> 0 = 0) -> 0 = 0"
    )
    state = _run(start(target), (("intro", "h"), ("apply", "h")))

    assert len(state.goals) == 2
    assert not state.subst
    state = apply_tactic(state, "refl")
    assert ONE in state.subst.values()
    state = apply_tactic(state, "refl")
    assert check((), checked_final(state, target), target)


def test_intro_does_not_default_a_meta_retained_only_by_a_hypothesis() -> None:
    target = parse_formula("exists x. x = 1 -> 1 = 1")
    state = _run(start(target), (("exists", "?"), ("intro", "h")))

    assert not state.subst
    state = apply_tactic(state, "exact", "h")
    assert ONE in state.subst.values()
    assert check((), checked_final(state, target), target)


def test_scoped_witness_meta_survives_forall_but_cannot_escape() -> None:
    good = parse_formula("exists x. forall y. x = 0")
    good_state = _run(
        start(good),
        (("exists", "?"), ("intro", "y"), ("refl", "")),
    )
    assert check((), checked_final(good_state, good), good)

    false = parse_formula("exists x. forall y. x = y")
    false_state = _run(
        start(false),
        (("exists", "?"), ("intro", "y")),
    )
    before = _snapshot(false_state)
    with pytest.raises(TacticError, match="not identical"):
        apply_tactic(false_state, "refl")
    assert _snapshot(false_state) == before
    with pytest.raises(InvalidProof, match="open"):
        checked_final(false_state, false)


def test_exists_cases_respects_the_eigenvariable_boundary() -> None:
    target = parse_formula(
        "(exists x. x = 0) -> exists y. y = 0"
    )
    state = _run(
        start(target),
        (
            ("intro", "h"),
            ("cases", "h"),
            ("exists", "x"),
            ("exact", "h_witness"),
        ),
    )
    assert check((), checked_final(state, target), target)


def test_forall_elim_alias_records_its_own_command() -> None:
    universal = Forall(Eq(Var(0), Var(0)))
    instance = Eq(ZERO, ZERO)
    original = Imp(universal, instance)
    initial = start(original)
    state = replace(
        initial,
        goals=(Goal((("h", universal),), instance),),
        partial_certificate_with_holes=ImpIntro(initial.partial),
    )
    state = apply_tactic(state, "forall_elim", "h 0")
    assert state.history[-1].tactic == "forall_elim"
    state = apply_tactic(state, "exact", "h")
    assert check((), checked_final(state, original), original)


def test_pa1_application_proves_successor_is_not_zero() -> None:
    target, names = parse_formula_with_names("S n = 0 -> false")
    state = _run(
        start(target, names),
        (("intro", "h"), ("apply", "PA1"), ("exact", "h")),
    )
    assert check((), checked_final(state, target), target)


def test_le_refl_uses_defined_order_sugar_and_induction() -> None:
    target = parse_formula("forall n. n <= n")
    commands = (
        ("intro", "n"),
        ("exists", "0"),
        ("induction", "n"),
        ("rewrite", "PA3"),
        ("refl", ""),
        ("rewrite", "PA4"),
        ("congr", ""),
        ("exact", "IH"),
    )
    state = _run(start(target), commands)
    assert check((), checked_final(state, target), target)


def test_rewrite_uses_an_outer_equation_capture_safely_under_forall() -> None:
    target, names = parse_formula_with_names(
        "n = 0 -> forall x. n + x = 0 + x"
    )
    state = _run(
        start(target, names),
        (
            ("intro", "h"),
            ("rewrite", "h"),
            ("intro", "x"),
            ("refl", ""),
        ),
    )
    assert check((), checked_final(state, target), target)


def test_rewrite_at_a_quantified_hypothesis_uses_a_sound_cut() -> None:
    target, names = parse_formula_with_names(
        "n = 0 -> (forall x. n + x = n + x) -> forall x. 0 + x = n + x"
    )
    state = _run(
        start(target, names),
        (
            ("intro", "h"),
            ("intro", "p"),
            ("rewrite", "h at p"),
            ("exact", "p"),
        ),
    )
    assert check((), checked_final(state, target), target)


def test_rewrite_never_confuses_a_bound_variable_with_an_outer_one() -> None:
    target, names = parse_formula_with_names(
        "n = 0 -> forall n. n = n"
    )
    state = apply_tactic(start(target, names), "intro", "h")
    before = _snapshot(state)
    with pytest.raises(TacticError, match="does not occur"):
        apply_tactic(state, "rewrite", "h")
    assert _snapshot(state) == before


def test_rewrite_lifts_an_outer_replacement_instead_of_capturing_it() -> None:
    target, names = parse_formula_with_names(
        "0 = n -> forall x. 0 = x"
    )
    state = apply_tactic(start(target, names), "intro", "h")
    state = apply_tactic(state, "rewrite", "h")
    assert state.current().target == Forall(Eq(Var(1), Var(0)))
    assert state.current().target != Forall(Eq(Var(0), Var(0)))


def test_bound_axiom_instantiation_requires_intro_before_rewrite() -> None:
    target = parse_formula("forall x. x + 0 = x")
    state = start(target)
    before = _snapshot(state)
    with pytest.raises(TacticError, match="eligible occurrence"):
        apply_tactic(state, "rewrite", "PA3")
    assert _snapshot(state) == before

    state = _run(
        state,
        (("intro", "x"), ("rewrite", "PA3"), ("refl", "")),
    )
    assert check((), checked_final(state, target), target)


def test_classical_mode_is_external_labeled_and_kernel_enforced() -> None:
    proposition = Eq(ZERO, ONE)
    target = Imp(Imp(Imp(proposition, parse_formula("false")), parse_formula("false")), proposition)
    logger = TraceLogger(session_id="m3-classical")
    mode = False
    assert logic_banner(mode).endswith("(classical off)")
    mode = set_classical_mode(mode, "on", state=start(target), trace=logger)
    assert mode is True
    assert logic_banner(mode).endswith("(classical on)")
    assert logger.records[0]["tactic"] == "classical on"
    assert logger.records[0]["goals_before"] == logger.records[0]["goals_after"]

    state = _run(
        start(target),
        (("intro", "h"), ("apply", "DNE"), ("exact", "h")),
        classical=mode,
    )
    certificate = checked_final(state, target, classical=True)
    assert check_classical((), certificate, target)
    assert not check((), certificate, target)
    with pytest.raises(InvalidProof, match="independent kernel"):
        checked_final(state, target)


def test_dne_is_unavailable_off_and_failure_is_transactional() -> None:
    target = Eq(ZERO, ONE)
    state = start(target)
    before = _snapshot(state)
    with pytest.raises(TacticError, match="mode is off"):
        apply_tactic(state, "apply", "DNE")
    assert _snapshot(state) == before
    with pytest.raises(TacticError, match="classical on"):
        set_classical_mode(False, "sometimes")


def test_classical_authority_requires_an_exact_boolean_and_traces_bad_modes() -> None:
    target = Eq(ZERO, ONE)
    state = start(target)
    before = _snapshot(state)
    logger = TraceLogger(session_id="m3-mode-errors")

    with pytest.raises(TacticError, match="Boolean"):
        apply_tactic(state, "apply", "DNE", classical=1, trace=logger)
    assert _snapshot(state) == before
    assert logger.records[-1]["status"] == "error"
    assert logger.records[-1]["goals_after"] == logger.records[-1]["goals_before"]

    with pytest.raises(TacticError, match="syntax"):
        set_classical_mode(False, "sometimes", state=state, trace=logger)
    assert logger.records[-1]["tactic"] == "classical sometimes"
    assert logger.records[-1]["status"] == "error"
    assert logger.records[-1]["goals_after"] == logger.records[-1]["goals_before"]


def test_hint_reports_only_found_none_limit_or_done_without_mutation() -> None:
    reflexive = start(Eq(ZERO, ZERO))
    before = _snapshot(reflexive)
    assert hint(reflexive) == ("found", "refl")
    assert _snapshot(reflexive) == before

    implication = start(Imp(Eq(ZERO, ZERO), Eq(ZERO, ZERO)))
    assert hint(implication) == ("found", "intro h")

    impossible = start(Eq(ZERO, ONE))
    assert hint(impossible) == ("none", None)

    meta_state = apply_tactic(start(Eq(ZERO, ZERO)), "trans", "?")
    assert hint(meta_state) == ("limit", None)

    done = apply_tactic(reflexive, "refl")
    assert hint(done) == ("done", None)


@pytest.mark.parametrize(
    ("tactic", "args", "message"),
    [
        ("split", "", "conjunction"),
        ("left", "", "disjunction"),
        ("right", "", "disjunction"),
        ("cases", "missing", "unknown hypothesis"),
        ("exists", "0", "existential"),
        ("apply", "missing", "unknown hypothesis"),
    ],
)
def test_connective_shape_failures_are_transactional(
    tactic: str,
    args: str,
    message: str,
) -> None:
    state = start(Eq(ZERO, ZERO))
    before = _snapshot(state)
    with pytest.raises(TacticError, match=message):
        apply_tactic(state, tactic, args)
    assert _snapshot(state) == before


def test_exfalso_rejects_no_progress_on_bottom() -> None:
    state = start(parse_formula("false"))
    before = _snapshot(state)
    with pytest.raises(TacticError, match="no progress"):
        apply_tactic(state, "exfalso")
    assert _snapshot(state) == before
