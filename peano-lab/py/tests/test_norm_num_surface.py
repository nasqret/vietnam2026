"""M13 proof-state, hint, tactical, and browser wiring for ``norm_num``."""

from __future__ import annotations

from dataclasses import replace

import pytest

import driver
import peano_lab.engine.tactics as tactics_module
from peano_lab.engine.norm_num import DEFAULT_NORM_NUM_LIMITS, normalize_equality
from peano_lab.engine.state import MetaVar, ProofState, invariants_ok, start
from peano_lab.engine.tacticals import focus
from peano_lab.engine.tactics import (
    TacticError,
    TacticLimit,
    TacticSyntaxError,
    apply_tactic,
    checked_final,
    exact,
    hint,
    intro,
    norm_num,
    split,
    trans,
    undo,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Bot, Eq, Forall, parse_formula, pretty_formula
from peano_lab.kernel.proofs import AndIntro, Axiom, EqRefl, EqSym, EqTrans
from peano_lab.kernel.terms import Zero
from peano_lab.ui import prove


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def test_closed_and_mixed_numerical_equalities_close_with_checked_certificates() -> None:
    for source in (
        "(2 + 3) * 4 = 20",
        "n + (2 * 3) = n + 6",
        "forall n. n + (2 * 3) = n + 6",
    ):
        target = parse_formula(source)
        completed = norm_num(start(target))

        certificate = checked_final(completed, target)
        assert check((), certificate, target)
        assert completed.history[-1].tactic == "norm_num"


def test_open_normalization_leaves_one_explicit_residual_and_transports_it_back() -> None:
    target = parse_formula(
        "(n + 6 = m + 4) -> n + (2 * 3) = m + (2 + 2)"
    )
    initial = start(target)
    introduced = intro(initial, "h")

    normalized = norm_num(introduced)

    assert len(normalized.goals) == 1
    assert normalized.current().target == parse_formula("n + 6 = m + 4")
    completed = exact(normalized, "h")
    assert check((), checked_final(completed, target), target)
    assert undo(normalized) is introduced


def test_residual_below_two_foralls_shifts_an_outer_context_capture_safely() -> None:
    target = parse_formula(
        "forall z. (z + 6 = 6 + z) -> "
        "forall a b. z + (2 * 3) = 6 + z"
    )
    state = intro(start(target), "z")
    state = intro(state, "h")

    normalized = norm_num(state)

    assert normalized.current().variables == ("x1", "x", "z")
    assert pretty_formula(
        normalized.current().target,
        list(normalized.current().variables),
    ) == "z + 6 = 6 + z"
    completed = exact(normalized, "h")
    assert check((), checked_final(completed, target), target)


def test_residual_preserves_sibling_goal_and_focus_hole_order() -> None:
    target = parse_formula(
        "(n + (2 * 3) = m + (2 + 2)) /\\ (2 + 2 = 4)"
    )
    branched = split(start(target))

    normalized = focus(1, norm_num)(branched, "")

    assert [goal.target for goal in normalized.goals] == [
        parse_formula("n + 6 = m + 4"),
        parse_formula("2 + 2 = 4"),
    ]
    assert invariants_ok(normalized)
    assert undo(normalized) is branched

    sibling_closed = focus(2, norm_num)(normalized, "")
    assert [goal.target for goal in sibling_closed.goals] == [
        parse_formula("n + 6 = m + 4")
    ]
    assert invariants_ok(sibling_closed)


def test_false_closed_equations_and_context_oracles_fail_transactionally() -> None:
    target = parse_formula("(2 + 2 = 5) -> 2 + 2 = 5")
    state = intro(start(target), "h")

    with pytest.raises(TacticError, match="different numerals"):
        norm_num(state)

    assert state.current().context[0][0] == "h"
    assert state.current().target == parse_formula("2 + 2 = 5")
    assert len(state.history) == 1


def test_shape_metas_no_progress_and_argument_errors_are_typed_and_unchanged() -> None:
    cases = (
        (start(Bot()), "", TacticError, "equality goal"),
        (start(parse_formula("n + 2 = 2 + n")), "", TacticError, "no progress"),
        (start(parse_formula("0 = 0")), "now", TacticSyntaxError, "no arguments"),
    )
    for state, args, error_type, message in cases:
        with pytest.raises(error_type, match=message):
            norm_num(state, args)
        assert len(state.history) == 0

    meta_state = trans(start(Eq(Zero(), Zero())), "?")
    before_goals = meta_state.goals
    before_partial = meta_state.partial
    with pytest.raises(TacticError, match="unresolved term metavariables"):
        norm_num(meta_state)
    assert meta_state.goals is before_goals
    assert meta_state.partial is before_partial


def test_low_level_limit_maps_to_tactic_limit_without_a_commit() -> None:
    state = start(parse_formula("2 * 3 = 6"))
    readings = iter((0.0, 6.0))

    with pytest.raises(TacticLimit, match="5-second time limit"):
        norm_num(state, clock=lambda: next(readings, 6.0))

    assert len(state.history) == 0
    assert len(state.goals) == 1

    too_many_binders = Eq(Zero(), Zero())
    for _ in range(tactics_module.MAX_NORM_NUM_FORALLS + 1):
        too_many_binders = Forall(too_many_binders)
    quantified = start(too_many_binders)
    with pytest.raises(TacticLimit, match="64-leading-universal"):
        norm_num(quantified)
    assert quantified.history == ()
    assert hint(quantified) == ("limit", None)

    one_binder = Forall(Eq(Zero(), Zero()))
    completed = norm_num(
        start(one_binder),
        limits=replace(DEFAULT_NORM_NUM_LIMITS, max_ast_depth=1),
        clock=lambda: 0.0,
    )
    assert check((), checked_final(completed, one_binder), one_binder)


def test_live_partial_certificate_has_a_separate_iterative_guard() -> None:
    initial = start(parse_formula("2 * 3 = 6"))
    too_deep = initial.partial
    for _ in range(tactics_module.MAX_NORM_NUM_PARTIAL_DEPTH):
        too_deep = EqSym(too_deep)
    hostile = replace(initial, partial_certificate_with_holes=too_deep)

    with pytest.raises(TacticLimit, match="live-proof-depth"):
        norm_num(hostile)

    assert hostile.partial is too_deep
    assert hostile.history == ()


def test_live_node_guard_applies_before_and_after_splicing(monkeypatch) -> None:
    monkeypatch.setattr(tactics_module, "MAX_NORM_NUM_PARTIAL_NODES", 3)
    initial = start(parse_formula("2 * 3 = 6"))
    oversized = initial.partial
    for _ in range(3):
        oversized = EqSym(oversized)
    hostile = replace(initial, partial_certificate_with_holes=oversized)

    with pytest.raises(TacticLimit, match="3-live-proof-node"):
        norm_num(hostile, clock=lambda: 0.0)
    assert hostile.partial is oversized

    with pytest.raises(TacticLimit, match="3-live-proof-node"):
        norm_num(initial, clock=lambda: 0.0)
    assert initial.history == ()


def test_malformed_exact_states_are_rejected_before_generation(monkeypatch) -> None:
    initial = start(parse_formula("2 * 3 = 6"))
    hole_free = replace(
        initial,
        partial_certificate_with_holes=EqRefl(Zero()),
    )
    duplicated = replace(
        initial,
        goals=(initial.current(), initial.current()),
        partial_certificate_with_holes=AndIntro(initial.partial, initial.partial),
    )
    malformed_owner = replace(initial, target=object())
    malformed_subst = replace(initial, subst={"bad": Zero()})

    def forbidden_generator(*_args, **_kwargs):
        raise AssertionError("malformed state reached numerical generation")

    monkeypatch.setattr(tactics_module, "normalize_equality", forbidden_generator)
    for malformed in (
        hole_free,
        duplicated,
        malformed_owner,
        malformed_subst,
        object.__new__(ProofState),
    ):
        with pytest.raises(TacticError, match="proof state|certificate"):
            norm_num(malformed)


def test_shared_deadline_is_checked_after_the_commit_boundary(monkeypatch) -> None:
    expired = False
    real_commit = tactics_module._commit

    def commit_then_expire(*args, **kwargs):
        nonlocal expired
        result = real_commit(*args, **kwargs)
        expired = True
        return result

    monkeypatch.setattr(tactics_module, "_commit", commit_then_expire)
    state = start(parse_formula("2 * 3 = 6"))

    with pytest.raises(TacticLimit, match="5-second time limit"):
        norm_num(state, clock=lambda: 6.0 if expired else 0.0)

    assert state.history == ()
    assert len(state.goals) == 1


def test_direct_closure_rechecks_a_mutated_generator_result(monkeypatch) -> None:
    target = parse_formula("2 * 3 = 6")
    assert type(target) is Eq
    genuine = normalize_equality(target, clock=lambda: 0.0)
    forged = replace(genuine, certificate=Axiom("PA3"))
    monkeypatch.setattr(tactics_module, "normalize_equality", lambda *_a, **_k: forged)
    state = start(target)

    with pytest.raises(TacticError, match="kernel rejected"):
        norm_num(state)

    assert state.goals == start(target).goals
    assert state.history == ()
    assert hint(state) == ("limit", None)


def test_hint_uses_pure_arithmetic_preflight_and_respects_the_boundary(monkeypatch) -> None:
    def forbidden_hole():
        raise AssertionError("hint allocated a certificate hole")

    monkeypatch.setattr(tactics_module, "fresh_hole", forbidden_hole)
    useful = start(parse_formula("n + (2 * 3) = n + 6"))
    quantified = start(parse_formula("forall n. n + (2 * 3) = n + 6"))
    false = start(parse_formula("2 + 2 = 5"))
    polynomial = start(parse_formula("n + 2 = 2 + n"))

    assert hint(useful) == ("found", "norm_num")
    assert hint(quantified) == ("found", "norm_num")
    assert hint(false) != ("found", "norm_num")
    assert hint(polynomial) != ("found", "norm_num")
    assert len(useful.history) == 0


def test_hint_maps_hostile_state_and_live_proof_budgets_to_limit(monkeypatch) -> None:
    target = Eq(Zero(), Zero())
    for _ in range(1_200):
        target = Forall(target)
    assert hint(start(target)) == ("limit", None)
    assert hint(object.__new__(ProofState)) == ("limit", None)
    assert hint(object()) == ("limit", None)

    exact = start(parse_formula("2 * 3 = 6"))
    assert hint(replace(exact, target=object())) == ("limit", None)
    assert hint(replace(exact, goals=())) == ("limit", None)
    assert hint(
        replace(
            exact,
            goals=(),
            partial_certificate_with_holes=EqRefl(Zero()),
        )
    ) == ("done", None)

    cyclic = replace(
        exact,
        partial_certificate_with_holes=EqTrans(
            EqRefl(MetaVar(0)),
            exact.partial,
        ),
        subst={0: MetaVar(0)},
    )
    assert hint(cyclic) == ("limit", None)
    with pytest.raises(TacticError, match="malformed proof state"):
        norm_num(cyclic)

    monkeypatch.setattr(tactics_module, "MAX_NORM_NUM_PARTIAL_NODES", 3)
    initial = start(parse_formula("2 * 3 = 6"))
    oversized = initial.partial
    for _ in range(3):
        oversized = EqSym(oversized)
    hostile = replace(initial, partial_certificate_with_holes=oversized)
    assert hint(hostile) == ("limit", None)

    # The pre-state fits exactly, but splicing the checked numerical proof does
    # not.  ``hint`` must not promise a command that the live-proof guard rejects.
    assert hint(initial) == ("limit", None)


def test_hint_projects_into_the_same_focused_hole_as_norm_num() -> None:
    branched = split(
        start(parse_formula("(2 * 3 = 6) /\\ (2 * 3 = 6)"))
    )
    assert type(branched.partial) is AndIntro
    deep_left = branched.partial.left
    for _ in range(tactics_module.MAX_NORM_NUM_PARTIAL_DEPTH - 2):
        deep_left = EqSym(deep_left)
    hostile = replace(
        branched,
        partial_certificate_with_holes=AndIntro(
            deep_left,
            branched.partial.right,
        ),
    )

    assert hint(hostile) == ("limit", None)
    with pytest.raises(TacticLimit, match="live-proof-depth"):
        norm_num(hostile)


def test_hint_rejects_inconsistent_normalizer_metadata(monkeypatch) -> None:
    other = parse_formula("2 + 2 = 4")
    assert type(other) is Eq
    inconsistent = normalize_equality(other, clock=lambda: 0.0)
    monkeypatch.setattr(
        tactics_module,
        "normalize_equality",
        lambda *_args, **_kwargs: inconsistent,
    )

    assert hint(start(parse_formula("2 * 3 = 6"))) != ("found", "norm_num")


def test_surface_trace_undo_tacticals_and_syntax_finality() -> None:
    session = driver.LabSession()
    session.run("pa prove 2 * 3 = 6 /\\ (2 + 2 = 4)")
    session.run("split")
    before = _owner(session).state

    assert "No open goals" in session.run("all_goals norm_num")
    owner = _owner(session)
    assert owner.trace.records[-1]["tactic"] == "all_goals norm_num"
    assert owner.trace.records[-1]["status"] == "ok"
    session.run("undo")
    assert _owner(session).state is before

    malformed = driver.LabSession()
    malformed.run("pa prove 0 = 0")
    unchanged = _owner(malformed).state
    output = malformed.run("norm_num now <|> refl")
    assert "`norm_num` takes no arguments" in output
    assert _owner(malformed).state is unchanged
    assert _owner(malformed).trace.records[-1]["status"] == "error"


def test_surface_qed_checks_the_original_numerical_theorem() -> None:
    session = driver.LabSession()
    original = "forall n. n + (2 * 3) = n + 6"
    session.run(f"pa prove {original}")

    assert "No open goals" in session.run("norm_num")
    finished = session.run("qed")

    assert "No open goals. QED." in finished
    assert "Theorem: ∀ x. x + 2 · 3 = x + 6" in finished
    assert not prove.is_active(session.webstate)


def test_public_dispatcher_routes_norm_num() -> None:
    target = parse_formula("2 + 3 = 5")
    state = start(target)
    completed = apply_tactic(state, "norm_num")

    assert check((), checked_final(completed, target), target)
    assert "norm_num" in tactics_module.TACTIC_NAMES
    assert DEFAULT_NORM_NUM_LIMITS.max_value == 128
