"""M5 browser-driver/session laws inherited from the Lambda Lab audit."""

from __future__ import annotations

from dataclasses import replace

import driver
from peano_lab.engine.state import ProofState
from peano_lab.ui import prove


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def test_pa_foundation_commands_are_plain_text_and_use_canonical_arithmetic() -> None:
    session = driver.LabSession()
    axioms = session.run("pa axioms")
    evaluated = session.run("pa eval (2 + 3) * 2")
    simplified = session.run("pa simp (0 + 1) + 0")

    assert "PA1: ∀ x. ¬S x = 0" in axioms
    assert "= 10" in evaluated
    assert "⇝ 1" in simplified
    assert "PA3" in simplified and "PA4" in simplified
    assert "\x1b" not in axioms + evaluated + simplified


def test_active_proof_owns_raw_line_before_ordinary_driver_dispatch() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    before = _owner(session)

    output = session.run("pa axioms")

    after = _owner(session)
    assert "unknown tactic 'pa'" in output
    assert after.state is before.state
    assert after.original_target is before.original_target


def test_nested_proof_is_refused_without_touching_the_owner() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    before = _owner(session)

    output = session.run("pa prove S 0 = S 0")

    assert "already in progress" in output
    assert _owner(session) is before


def test_qed_aliases_are_complete_line_and_case_sensitive() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    before = _owner(session)

    assert "typed alone" in session.run("qed please")
    assert prove.is_active(session.webstate)
    assert _owner(session).state is before.state

    assert "unknown tactic 'QED'" in session.run("QED")
    assert prove.is_active(session.webstate)
    session.run("abort")
    assert not prove.is_active(session.webstate)


def test_arrow_argument_is_a_proposition_before_prove_subcommands() -> None:
    session = driver.LabSession()
    output = session.run("pa prove (0 = 0) -> 0 = 0")

    assert "Theorem: 0 = 0 → 0 = 0" in output
    assert prove.is_active(session.webstate)


def test_every_qed_calls_checked_final_with_owner_original_and_exact_mode(
    monkeypatch,
) -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = _owner(session)
    session.run("refl")
    real_checked_final = prove.checked_final
    calls: list[tuple[ProofState, object, object, object]] = []

    def spy(state, original_target, *, classical=False, trace=None):
        calls.append((state, original_target, classical, trace))
        return real_checked_final(
            state,
            original_target,
            classical=classical,
            trace=trace,
        )

    monkeypatch.setattr(prove, "checked_final", spy)
    output = session.run("qed")

    assert "QED." in output
    assert len(calls) == 1
    assert calls[0][1] is owner.original_target
    assert calls[0][2] is False
    # The owner emits the footer after the checker returns, using its own
    # original name table rather than tactic-controlled state metadata.
    assert calls[0][3] is None
    assert not prove.is_active(session.webstate)
    assert owner.trace.records[-1]["qed"] is True


def test_failed_qed_calls_checker_and_keeps_the_exact_session(monkeypatch) -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = S 0")
    owner = _owner(session)
    calls = 0
    real_checked_final = prove.checked_final

    def spy(state, original_target, *, classical=False, trace=None):
        nonlocal calls
        calls += 1
        return real_checked_final(
            state,
            original_target,
            classical=classical,
            trace=trace,
        )

    monkeypatch.setattr(prove, "checked_final", spy)
    output = session.run("qed")

    assert calls == 1
    assert "QED check failed" in output
    assert _owner(session) is owner
    assert not any(record.get("qed") is True for record in owner.trace.records)


def test_qed_footer_uses_owner_names_not_tactic_owned_state_metadata() -> None:
    session = driver.LabSession()
    session.run("pa prove n = n")
    session.run("refl")
    owner = _owner(session)
    forged_state = replace(owner.state, variables=("forged",))
    session.webstate[prove.KEY_SESSION] = replace(owner, state=forged_state)

    output = session.run("qed")

    assert "QED." in output
    assert owner.trace.records[-1]["theorem"] == "n = n"
    assert "forged" not in owner.trace.records[-1]["theorem"]


def test_classical_authority_lives_outside_proofstate_and_final_mode_is_exact() -> None:
    theorem = "((0 = S 0 -> false) -> false) -> 0 = S 0"
    session = driver.LabSession()
    session.run(f"pa prove {theorem}")
    session.run("intro h")
    before = _owner(session)

    denied = session.run("apply DNE")
    assert "unavailable while classical mode is off" in denied
    assert _owner(session).state is before.state

    session.run("classical on")
    enabled = _owner(session)
    assert enabled.classical is True
    assert not hasattr(enabled.state, "classical")
    session.run("apply DNE")
    session.run("assumption")
    session.run("classical off")
    assert "QED check failed" in session.run("qed")
    assert prove.is_active(session.webstate)
    session.run("classical on")
    assert "QED." in session.run("qed")


def test_tactical_simp_and_auto_routes_keep_one_owner_and_kernel_check() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0 /\\ 0 = 0")
    owner = _owner(session)
    closed = session.run("split; refl")

    completed = _owner(session)
    assert "No open goals" in closed
    assert len(completed.state.history) == 1
    assert completed.state.history[-1].state_before is owner.state
    assert completed.trace.records[-1]["tactic"] == "split; refl"
    assert "QED." in session.run("qed")

    automated = driver.LabSession()
    automated.run("pa prove forall n. 0 + n = n")
    assert "No open goals" in automated.run("auto 5")
    assert "QED." in automated.run("qed")


def test_browser_session_acceptance_proves_add_comm_through_checked_qed() -> None:
    session = driver.LabSession()

    started = session.run("pa prove forall n m. n + m = m + n")
    searched = session.run("auto 5")
    finished = session.run("qed")

    assert "Theorem: ∀ x. ∀ y. x + y = y + x" in started
    assert "No open goals" in searched
    assert "QED." in finished
    assert not prove.is_active(session.webstate)


def test_orelse_first_focus_and_all_goals_are_surface_routable() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0 /\\ 0 = 0")
    assert "Goal 1/2" in session.run("split")
    assert "Goal 1/1" in session.run("focus 2 refl")
    assert _owner(session).trace.records[-1]["focus"] == 1
    assert "No open goals" in session.run("first [assumption | all_goals refl]")
    assert "QED." in session.run("qed")

    alternate = driver.LabSession()
    alternate.run("pa prove 0 = 0")
    assert "No open goals" in alternate.run("assumption <|> refl")


def test_hint_undo_help_and_state_panels_work_inside_proof() -> None:
    session = driver.LabSession()
    started = session.run("pa prove 0 = 0 -> 0 = 0")
    initial = _owner(session).state

    assert "Goal 1/1" in started
    assert "Context" in started and "Target" in started
    assert "Partial certificate" in started
    assert "try `intro h`" in session.run("hint")
    session.run("intro h")
    assert "hyp[" in session.run("assumption")
    undone = session.run("undo")
    assert "Goal 1/1" in undone
    assert _owner(session).state.current().target == initial.current().target.right
    assert "Tactics:" in session.run("help")


def test_panel_hole_names_are_session_local_and_browser_output_never_emits_controls() -> None:
    first = driver.LabSession().run("pa prove 0 = 0")
    second_session = driver.LabSession()
    second = second_session.run("pa prove 0 = 0")

    assert "?g1" in first and "?g1" in second
    assert "\x1b" not in first + second
    hostile = second_session.run("\x1bevil")
    assert "\x1b" not in hostile
    assert "\\x1b" in hostile
    c1_hostile = second_session.run("\x9bevil")
    assert "\x9b" not in c1_hostile
    assert "\\x9b" in c1_hostile
    separated = driver._browser_safe("evil\u2028next\u2029last")
    assert "\u2028" not in separated and "\u2029" not in separated
    assert r"\u2028" in separated and r"\u2029" in separated


def test_panel_metavariable_aliases_survive_sibling_progress_and_undo() -> None:
    session = driver.LabSession()
    session.run("pa prove (exists x. x = 0) /\\ (exists y. y = 0)")
    session.run("split")
    session.run("exists ?")
    both = session.run("focus 2 exists ?")
    assert "?t1" in both and "?t2" in both

    remaining = session.run("refl")
    assert "?t2 = 0" in remaining
    assert "?t1 = 0" not in remaining
    restored = session.run("undo")
    assert "?t1" in restored and "?t2" in restored


def test_abort_emits_a_false_footer_before_discarding_the_owner() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = _owner(session)

    assert "aborted" in session.run("abort")
    assert owner.trace.records[-1]["qed"] is False
    assert owner.trace.records[-1]["theorem"] == "0 = 0"
    assert not prove.is_active(session.webstate)


def test_inactive_tactics_and_nested_proof_whitespace_follow_audit_grammar() -> None:
    session = driver.LabSession()
    for word in ("intro", "refl", "simp", "undo"):
        assert "No proof is in progress" in session.run(f"pa prove {word}")

    session.run("pa prove 0 = 0")
    before = _owner(session)
    for nested in ("pa   prove S 0 = S 0", "pa\tprove 1 = 1", "PA PROVE 2 = 2"):
        assert "already in progress" in session.run(nested)
        assert _owner(session) is before


def test_redundant_groups_and_tab_separated_tacticals_are_supported() -> None:
    grouped = driver.LabSession()
    grouped.run("pa prove 0 = 0")
    assert "No open goals" in grouped.run("(((refl)))")

    focused = driver.LabSession()
    focused.run("pa prove 0 = 0 /\\ 0 = 0")
    focused.run("split")
    assert "Goal 1/1" in focused.run("focus\t2 ((refl))")
    assert "No open goals" in focused.run("all_goals\trefl")


def test_browser_driver_rejects_oversized_numerals_before_desugaring() -> None:
    session = driver.LabSession()
    output = session.run(f"pa eval {driver.MAX_NUMERAL + 1}")
    assert "exceeds the browser limit" in output
    assert session.history == []

    # Digits inside legal identifiers and explicit de Bruijn indices are not
    # numeral sugar and must not trip the value guard.
    assert "open term" in session.run(f"pa eval x{driver.MAX_NUMERAL + 1}")


def test_malformed_tactical_is_traced_as_an_unchanged_failure() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = _owner(session)
    before = owner.state

    output = session.run("first [refl |]")

    after = _owner(session)
    assert "Tactic error" in output
    assert after.state is before
    record = owner.trace.records[-1]
    assert record["status"] == "error"
    assert record["goals_before"] == record["goals_after"]
