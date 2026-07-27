"""M10 live reuse of closed, independently checked library theorems."""

from __future__ import annotations

from dataclasses import replace
import sys

import pytest

import driver
from peano_lab.engine.state import final_certificate, start
from peano_lab.engine.tactics import (
    MAX_USE_PROOF_DEPTH,
    InvalidProof,
    TacticError,
    TacticLimit,
    checked_final,
    exact,
    use_checked,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import EqRefl, EqSym
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import LibraryError, normalise_cuts, replay
from peano_lab.ui import prove


ZERO = Zero()


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def test_engine_use_checked_builds_a_local_cut_then_normalises_to_closed_qed() -> None:
    theorem = replay("add_comm")
    initial = start(theorem.formula)

    imported = use_checked(
        initial,
        "comm",
        theorem.formula,
        theorem.certificate,
    )

    assert imported.current().context[0] == ("comm", theorem.formula)
    assert imported.history[-1].tactic == "use"
    completed = exact(imported, "comm")
    with pytest.raises(InvalidProof, match="independent kernel"):
        checked_final(completed, theorem.formula)

    raw = final_certificate(completed)
    assert raw is not None
    compiled = normalise_cuts(raw)
    transient = replace(completed, partial_certificate_with_holes=compiled)
    certificate = checked_final(transient, theorem.formula)
    assert check((), certificate, theorem.formula)


def test_engine_use_rejects_bad_certificates_and_name_collisions_transactionally() -> None:
    theorem = replay("add_comm")
    initial = start(theorem.formula)
    forged = EqRefl(ZERO)

    with pytest.raises(TacticError, match="independent kernel rejected"):
        use_checked(initial, "comm", theorem.formula, forged)
    assert initial.current().context == ()
    assert initial.history == ()

    imported = use_checked(initial, "comm", theorem.formula, theorem.certificate)
    before = imported
    with pytest.raises(TacticError, match="already in use"):
        use_checked(imported, "comm", theorem.formula, theorem.certificate)
    assert imported is before


def test_live_use_exact_qed_compiles_the_cut_and_checks_the_original_goal() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")

    panel = session.run("use add_comm")
    closed = session.run("exact add_comm")
    finished = session.run("qed")

    assert "add_comm : ∀ x. ∀ y. x + y = y + x" in panel
    assert "No open goals" in closed
    assert "QED." in finished
    assert "Theorem: ∀ x. ∀ y. x + y = y + x" in finished
    assert not prove.is_active(session.webstate)


def test_live_use_alias_specializes_capture_safely_below_term_binders() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")
    session.run("intro n")
    session.run("intro m")
    session.run("use add_comm as comm")
    session.run("specialize comm n")
    session.run("specialize comm m")

    assert "No open goals" in session.run("exact comm")
    assert "QED." in session.run("qed")


def test_live_use_alias_uses_the_same_unicode_identifier_rules_as_intro() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")

    assert "α : ∀ x. ∀ y. x + y = y + x" in session.run("use add_comm as α")
    assert "No open goals" in session.run("exact α")
    assert "QED." in session.run("qed")


def test_live_use_casefolds_lookup_and_keeps_the_canonical_default_alias() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")

    panel = session.run("use ADD_COMM")

    assert "add_comm : ∀ x. ∀ y. x + y = y + x" in panel
    assert "ADD_COMM :" not in panel


def test_live_use_participates_in_simp_and_surface_tacticals() -> None:
    simplified = driver.LabSession()
    simplified.run("pa prove forall n. 0 + n = n")
    assert "No open goals" in simplified.run("use zero_add; simp [zero_add]")
    owner = _owner(simplified)
    assert len(owner.state.history) == 1
    assert owner.trace.records[-1]["tactic"] == "use zero_add; simp [zero_add]"
    assert "QED." in simplified.run("qed")

    unused = driver.LabSession()
    unused.run("pa prove 0 = 0")
    unused.run("use add_comm")
    unused.run("refl")
    assert "QED." in unused.run("qed")


def test_live_use_composes_two_checked_facts_into_a_new_theorem() -> None:
    session = driver.LabSession()
    session.run("pa prove forall a b. S a + b = S (b + a)")
    session.run("use add_succ_left")
    session.run("use add_comm")
    session.run("intro a")
    session.run("intro b")

    assert "No open goals" in session.run("simp [add_succ_left, add_comm]")
    assert "QED." in session.run("qed")


def test_live_use_failures_are_traced_and_leave_the_exact_state_unchanged() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n. n = n")
    session.run("intro n")
    owner = _owner(session)
    before = owner.state

    unknown = session.run("use missing")
    assert "no checked library theorem 'missing'" in unknown
    assert _owner(session).state is before
    assert owner.trace.records[-1]["status"] == "error"

    collision = session.run("use zero_add as n")
    assert "name 'n' is already in use" in collision
    assert _owner(session).state is before

    syntax = session.run("use add_comm under alias")
    assert "syntax: `use <library-theorem> [as <alias>]`" in syntax
    assert _owner(session).state is before


def test_live_use_resource_limit_is_typed_traced_and_transactional() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = _owner(session)

    limit_error = None
    before_limit = owner.state
    for index in range(MAX_USE_PROOF_DEPTH + 1):
        before_limit = owner.state
        try:
            owner = prove._run_surface(
                owner,
                f"use succ_ne_zero as imported{index}",
            )
        except TacticLimit as exc:
            limit_error = exc
            break

    assert limit_error is not None
    assert "live-certificate limit" in str(limit_error)
    assert owner.state is before_limit
    assert owner.trace.records[-1]["status"] == "error"
    assert "live-certificate limit" in owner.trace.records[-1]["error"]


def test_live_use_obeys_orelse_and_inactive_session_grammar() -> None:
    fallback = driver.LabSession()
    fallback.run("pa prove 0 = 0")
    assert "No open goals" in fallback.run("use missing <|> refl")
    assert "QED." in fallback.run("qed")

    malformed = driver.LabSession()
    malformed.run("pa prove 0 = 0")
    before = _owner(malformed).state
    output = malformed.run("use add_comm under alias <|> refl")
    assert "syntax: `use <library-theorem> [as <alias>]`" in output
    assert _owner(malformed).state is before

    inactive = driver.LabSession()
    assert "No proof is in progress" in inactive.run("pa prove use")


def test_live_use_is_hole_safe_under_focus_all_goals_and_repeat() -> None:
    focused = driver.LabSession()
    focused.run("pa prove 0 = 0 /\\ 0 = 0")
    focused.run("split")
    focused.run("focus 2 use add_comm")
    owner = _owner(focused)
    assert owner.state.goals[0].context == ()
    assert owner.state.goals[1].context[0][0] == "add_comm"
    focused.run("all_goals refl")
    assert "QED." in focused.run("qed")

    every = driver.LabSession()
    every.run("pa prove 0 = 0 /\\ 0 = 0")
    every.run("split")
    every.run("all_goals use add_comm")
    assert all(goal.context[0][0] == "add_comm" for goal in _owner(every).state.goals)

    repeated = driver.LabSession()
    repeated.run("pa prove 0 = 0")
    before = _owner(repeated).state
    repeated.run("repeat use add_comm")
    imported = _owner(repeated).state
    assert [name for name, _ in imported.current().context] == ["add_comm"]
    assert len(imported.history) == 1
    repeated.run("undo")
    assert _owner(repeated).state is before


def test_live_use_undo_restores_the_exact_pre_import_state() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    before = _owner(session).state

    session.run("use add_comm")
    assert _owner(session).state.current().context
    session.run("undo")

    assert _owner(session).state is before


def test_cut_fallback_never_rescues_a_false_original_goal() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 1")
    session.run("use add_comm")
    owner = _owner(session)
    forged = replace(
        owner.state,
        goals=(),
        partial_certificate_with_holes=EqRefl(ZERO),
    )
    session.webstate[prove.KEY_SESSION] = replace(owner, state=forged)

    output = session.run("qed")

    assert "QED check failed" in output
    assert prove.is_active(session.webstate)


def test_surface_qed_normalises_only_complete_certificates(monkeypatch) -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    calls = []
    real_normalise = prove.normalise_cuts

    def spy(certificate):
        calls.append(certificate)
        return real_normalise(certificate)

    monkeypatch.setattr(prove, "normalise_cuts", spy)
    assert "1 goal(s) are still open" in session.run("qed")
    assert calls == []

    session.run("refl")
    assert "QED." in session.run("qed")
    assert len(calls) == 1


def test_cut_normalization_failure_keeps_the_exact_live_owner(monkeypatch) -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    session.run("refl")
    owner = _owner(session)

    def fail(_certificate):
        raise LibraryError("deliberate failure")

    monkeypatch.setattr(prove, "normalise_cuts", fail)
    output = session.run("qed")

    assert "theorem-reuse cut normalization failed" in output
    assert _owner(session) is owner
    assert not any(record.get("qed") is True for record in owner.trace.records)


def test_surface_finalization_maps_host_recursion_exhaustion_to_invalid_proof() -> None:
    target = Eq(ZERO, ZERO)
    certificate = EqRefl(ZERO)
    for _ in range(sys.getrecursionlimit() + 50):
        certificate = EqSym(certificate)
    hostile = replace(
        start(target),
        goals=(),
        partial_certificate_with_holes=certificate,
    )

    with pytest.raises(InvalidProof, match="host recursion limit"):
        prove.checked_surface_final(hostile, target)
