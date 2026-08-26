"""Structured command status used by browser multiline replay."""

from __future__ import annotations

import json

import driver
from peano_lab.ui import prove


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def test_structured_status_reaches_an_independently_checked_qed() -> None:
    session = driver.LabSession()

    opened = session.run_result("pa prove 0 = 0")
    solved = session.run_result("refl")
    closed = session.run_result("qed")

    assert opened["failed"] is False
    assert solved["failed"] is False
    assert closed["failed"] is False
    assert "No open goals. QED." in str(closed["out"])
    assert not prove.is_active(session.webstate)


def test_tactic_and_qed_failures_stop_without_mutating_the_proof() -> None:
    session = driver.LabSession()
    assert session.run_result("pa prove 0 = 0")["failed"] is False
    before = _owner(session)

    bad_tactic = session.run_result("not_a_tactic")

    assert bad_tactic["failed"] is True
    assert str(bad_tactic["out"]).startswith("Tactic error:")
    assert _owner(session) is before

    resource_failure = session.run_result("exact 999")
    assert resource_failure["failed"] is True
    assert str(resource_failure["out"]).startswith("Error:")
    assert _owner(session) is before

    bad_qed = session.run_result("qed")

    assert bad_qed["failed"] is True
    assert "still open" in str(bad_qed["out"]).lower()
    assert _owner(session) is before


def test_session_routing_usage_and_abort_are_structured_failures() -> None:
    inactive = driver.LabSession()
    help_instead_of_statement = inactive.run_result("pa prove help")
    assert help_instead_of_statement["failed"] is True
    assert not prove.is_active(inactive.webstate)

    session = driver.LabSession()
    assert session.run_result("pa prove 0 = 0")["failed"] is False
    owner = _owner(session)

    nested = session.run_result("pa prove S 0 = S 0")
    assert nested["failed"] is True
    assert _owner(session) is owner

    usage = session.run_result("script nonsense")
    assert usage["failed"] is True
    assert str(usage["out"]).startswith("Usage:")
    assert _owner(session) is owner

    aborted = session.run_result("abort")
    assert aborted["failed"] is True
    assert not prove.is_active(session.webstate)

    tutorial = driver.LabSession()
    tutorial.run("pa tutorial add_comm")
    assert tutorial._session_owner() == "tutorial"
    routed_to_tutorial = tutorial.run_result("pa prove 0 = 0")
    assert routed_to_tutorial["failed"] is True
    assert tutorial._session_owner() == "tutorial"


def test_browser_dispatcher_returns_a_json_status_envelope(monkeypatch) -> None:
    monkeypatch.setattr(driver, "_SESSION", driver.LabSession())

    result = json.loads(driver.run_line_result("pa prove 0 = 0"))

    assert result["failed"] is False
    assert "Theorem: 0 = 0" in result["out"]


def test_successful_prefix_keeps_ordinary_per_command_undo() -> None:
    session = driver.LabSession()
    assert session.run_result("pa prove forall n. n = n /\\ n = n")["failed"] is False

    assert session.run_result("intro n")["failed"] is False
    after_intro = _owner(session).state
    assert session.run_result("split")["failed"] is False
    after_split = _owner(session).state
    assert session.run_result("refl")["failed"] is False
    after_refl = _owner(session).state

    stopped = session.run_result("not_a_tactic")
    assert stopped["failed"] is True
    assert _owner(session).state is after_refl

    assert session.run_result("undo")["failed"] is False
    assert _owner(session).state is after_split
    assert session.run_result("undo")["failed"] is False
    assert _owner(session).state is after_intro
