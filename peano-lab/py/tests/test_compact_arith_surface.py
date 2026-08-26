"""Browser/session laws for compact, certificate-producing PA arithmetic."""

from __future__ import annotations

import driver

from peano_lab.engine.state import fresh_hole, fresh_meta
from peano_lab.ui import prove


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def test_compact_arith_closes_traces_replays_and_undoes_one_step() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n. n + 1 = S n")
    session.run("intro n")
    before_owner = _owner(session)
    before = before_owner.state
    trace_count = len(before_owner.trace.records)
    replay_count = len(before_owner.replay_steps)

    assert "No open goals" in session.run("compact_arith")
    owner = _owner(session)
    assert len(owner.state.history) == len(before.history) + 1
    assert len(owner.trace.records) == trace_count + 1
    assert len(owner.replay_steps) == replay_count + 1
    assert owner.replay_steps[-1].command == "compact_arith"
    assert owner.state.history[-1].tactic == "compact_arith"
    assert owner.trace.records[-1]["tactic"] == "compact_arith"
    assert owner.trace.records[-1]["status"] == "ok"

    script = session.run("script")
    assert "compact_arith" in script
    session.run("undo")
    assert _owner(session).state is before
    assert "No open goals" in session.run("compact_arith")
    assert "No open goals. QED." in session.run("qed")


def test_compact_arith_uses_only_explicit_oriented_equations() -> None:
    forward = driver.LabSession()
    forward.run("pa prove n = m -> n = m")
    forward.run("intro h")
    assert "Used equations: h" in forward.run("compact_arith? [h]")
    assert "No open goals" in forward.run("compact_arith [h]")
    assert "QED." in forward.run("qed")

    reverse = driver.LabSession()
    reverse.run("pa prove n = m -> m = n")
    reverse.run("intro h")
    assert "No open goals" in reverse.run("compact_arith [<- h]")
    assert "QED." in reverse.run("qed")

    hidden = driver.LabSession()
    hidden.run("pa prove n = m -> m = n")
    hidden.run("intro h")
    before = _owner(hidden).state
    output = hidden.run("compact_arith")
    assert "Tactic error:" in output
    assert _owner(hidden).state is before


def test_compact_arith_preview_is_pure_and_reports_only_a_candidate_fragment() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n. n + 1 = S n")
    session.run("intro n")
    owner = _owner(session)
    state = owner.state
    history = owner.replay_steps
    trace_count = len(owner.trace.records)
    meta_before = fresh_meta().id
    hole_before = fresh_hole().id

    output = session.run("compact_arith?")

    assert "untrusted; proof state unchanged" in output
    assert "Strategy:" in output
    assert "Used equations: (none)" in output
    assert "Candidate fragment:" in output
    assert "annotation nodes" in output
    assert "only `qed` checks the whole theorem" in output
    after = _owner(session)
    assert after.state is state
    assert after.replay_steps == history
    assert len(after.trace.records) == trace_count

    rejected = session.run("compact_arith? [missing]")
    assert "unknown hypothesis" in rejected
    after_rejection = _owner(session)
    assert after_rejection.state is state
    assert after_rejection.replay_steps == history
    assert len(after_rejection.trace.records) == trace_count
    assert fresh_meta().id == meta_before + 1
    assert fresh_hole().id == hole_before + 1


def test_compact_arith_argument_errors_are_traced_and_transactional() -> None:
    session = driver.LabSession()
    session.run("pa prove (0 = 0 -> 0 = 0) -> 0 = 0")
    session.run("intro not_equation")
    before = _owner(session).state

    for command, fragment in (
        ("compact_arith not_equation", "syntax:"),
        ("compact_arith [missing]", "unknown hypothesis"),
        ("compact_arith [not_equation]", "is not an equation"),
        ("compact_arith [missing,]", "syntax:"),
        ("compact_arith [not_equation, not_equation]", "may appear only once"),
    ):
        trace_count = len(_owner(session).trace.records)
        output = session.run(command)
        owner = _owner(session)
        assert fragment in output
        assert owner.state is before
        assert len(owner.trace.records) == trace_count + 1
        assert owner.trace.records[-1]["tactic"] == command
        assert owner.trace.records[-1]["status"] == "error"
        assert (
            owner.trace.records[-1]["goals_before"]
            == owner.trace.records[-1]["goals_after"]
        )


def test_compact_arith_empty_selection_and_nested_binders_are_capture_safe() -> None:
    empty = driver.LabSession()
    empty.run("pa prove forall n. n + 1 = S n")
    empty.run("intro n")
    assert "No open goals" in empty.run("compact_arith []")
    assert "QED." in empty.run("qed")

    # The generated recurrence proof is inserted below an implication, an
    # existential elimination binder, and two universal binders.  A missing
    # shift in a term or motive therefore changes the checked proposition.
    nested = driver.LabSession()
    nested.run(
        "pa prove (exists z. z = z) -> forall a b. S a + b = S (a + b)"
    )
    nested.run("intro h")
    nested.run("cases h")
    nested.run("intro a")
    nested.run("intro b")
    assert "No open goals" in nested.run("compact_arith")
    assert "No open goals. QED." in nested.run("qed")


def test_compact_arith_participates_in_tacticals_and_inactive_grammar() -> None:
    session = driver.LabSession()
    session.run("pa prove (n + 1 = S n) /\\ (m + 1 = S m)")
    session.run("split")

    assert "No open goals" in session.run("all_goals compact_arith")
    owner = _owner(session)
    assert owner.trace.records[-1]["tactic"] == "all_goals compact_arith"
    assert len(owner.state.history) == 2
    help_text = session.run("help")
    assert "compact_arith [h, <- k]" in help_text
    assert "compact_arith? [h, <- k]" in help_text
    assert "QED." in session.run("qed")

    focused = driver.LabSession()
    focused.run("pa prove (n + 1 = S n) /\\ (m + 1 = S m)")
    focused.run("split")
    history_count = len(_owner(focused).state.history)
    assert "Goal 1/1" in focused.run("focus 2 compact_arith")
    focused_owner = _owner(focused)
    assert focused_owner.trace.records[-1]["focus"] == 1
    assert len(focused_owner.state.history) == history_count + 1
    assert "No open goals" in focused.run("compact_arith")
    assert "QED." in focused.run("qed")

    inactive = driver.LabSession()
    assert "No proof is in progress" in inactive.run("pa prove compact_arith")
    assert "No proof is in progress" in inactive.run("pa prove compact_arith?")
