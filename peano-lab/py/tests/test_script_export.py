"""M15 replay scripts are deterministic observers, never theorem authority."""

from __future__ import annotations

from dataclasses import replace

import driver
from peano_lab.ui import prove


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def _artifact(session: driver.LabSession) -> prove.ProofScript:
    artifact = prove.get_script(session.webstate)
    assert artifact is not None
    return artifact


def _replay(text: str) -> tuple[driver.LabSession, str]:
    session = driver.LabSession()
    output = ""
    for command in text.splitlines():
        output = session.run(command)
        assert "Tactic error" not in output
        assert "QED check failed" not in output
    return session, output


def _displayed_body(output: str) -> str:
    lines = output.splitlines()
    start = lines.index("Replay (copy these lines):") + 1
    commands: list[str] = []
    for line in lines[start:]:
        if not line:
            break
        assert line.startswith("  ")
        commands.append(line[2:])
    return "\n".join(commands) + "\n"


def test_script_is_a_pure_active_observer_and_download_matches_preview() -> None:
    session = driver.LabSession()
    assert "No replay script is available" in session.run("script")
    session.run("pa prove forall n. n + 0 = n")
    session.run("intro n")
    before = _owner(session)
    trace_before = before.trace.records

    preview = session.run("script")
    after = _owner(session)

    assert "ACTIVE (not kernel-checked)" in preview
    assert "No theorem is claimed" in preview
    assert "  pa prove ∀ x. x + 0 = x" in preview
    assert "  intro n" in preview
    assert "  qed" not in preview
    assert after.state is before.state
    assert after.replay_steps == before.replay_steps
    assert after.classical is before.classical
    assert after.trace.records == trace_before

    requested = session.run("script download")
    body = session.take_download()
    assert body == _displayed_body(requested)
    assert body.endswith("\n") and "\r" not in body
    assert session.take_download() == ""
    assert _owner(session).state is before.state


def test_failures_inspection_and_undo_are_not_in_the_current_branch() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0 -> 0 = 0")
    failed = session.run("exact missing")
    assert "Tactic error" in failed
    session.run("hint")
    session.run("intro h")
    assert "intro h" in _artifact(session).commands

    session.run("undo")
    artifact = _artifact(session)

    assert artifact.commands == ("pa prove 0 = 0 → 0 = 0",)
    assert "missing" not in artifact.text
    assert "hint" not in artifact.text
    assert "undo" not in artifact.text
    assert any(record["status"] == "error" for record in _owner(session).trace.records)


def test_tactical_and_use_surface_spelling_replays_to_checked_qed() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")
    closed = session.run("use ADD_COMM as comm; exact comm")
    assert "No open goals" in closed

    active = _artifact(session)
    assert active.commands[-1] == "use ADD_COMM as comm; exact comm"
    assert "use comm" not in active.commands
    session.run("done")
    checked = _artifact(session)

    assert checked.checked is True
    assert checked.commands[-1] == "qed"
    replayed, output = _replay(checked.text)
    assert "QED." in output
    assert not prove.is_active(replayed.webstate)


def test_top_level_auto_exports_undoable_primitives_and_undo_removes_one() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n. 0 + n = n")
    assert "No open goals" in session.run("auto 5")
    before = _artifact(session)

    assert "auto 5" not in before.commands
    assert len(before.commands) == len(_owner(session).state.history) + 1
    session.run("undo")
    after = _artifact(session)

    assert len(after.commands) == len(before.commands) - 1
    replayed, _ = _replay(after.text)
    assert _owner(replayed).state.goals == _owner(session).state.goals
    assert _owner(replayed).classical is _owner(session).classical


def test_classical_authority_is_reconstructed_and_qed_is_canonical() -> None:
    theorem = "((0 = S 0 -> false) -> false) -> 0 = S 0"
    session = driver.LabSession()
    session.run(f"pa prove {theorem}")
    session.run("intro h")
    session.run("classical on")
    session.run("apply DNE")
    session.run("assumption")
    assert "QED." in session.run("finish")
    checked = _artifact(session)

    assert checked.commands[-1] == "qed"
    assert "finish" not in checked.commands
    assert checked.commands.index("classical on") < checked.commands.index("apply DNE")
    _, output = _replay(checked.text)
    assert "QED." in output
    assert "classical on" in checked.text

    undone = driver.LabSession()
    undone.run("pa prove 0 = 0")
    undone.run("classical on")
    undone.run("refl")
    undone.run("undo")
    assert _artifact(undone).commands == ("pa prove 0 = 0", "classical on")


def test_failed_qed_and_abort_cannot_overwrite_the_last_checked_artifact() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    session.run("refl")
    session.run("qed")
    previous = _artifact(session)

    session.run("pa prove 0 = S 0")
    assert "QED check failed" in session.run("qed")
    active = _artifact(session)
    assert active.checked is False and "qed" not in active.commands
    session.run("abort")

    assert _artifact(session) is previous
    assert "CHECKED QED" in session.run("script")


def test_download_is_one_shot_and_a_later_command_discards_stale_bytes() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    session.run("refl")
    session.run("qed")

    session.run("script download")
    assert session.take_download().endswith("qed\n")
    assert session.take_download() == ""

    session.run("script download")
    session.run("help")
    assert session.take_download() == ""


def test_export_failure_never_turns_a_valid_certificate_into_a_failed_qed() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    session.run("refl")
    session.run("qed")
    previous = _artifact(session)

    session.run("pa prove S 0 = S 0")
    session.run("refl")
    owner = _owner(session)
    hostile = replace(
        owner,
        replay_steps=(prove.ReplayStep("refl\u202e", False),),
    )
    session.webstate[prove.KEY_SESSION] = hostile

    assert "Script export failed" in session.run("script")
    finished = session.run("qed")
    assert "No open goals. QED." in finished
    assert "Replay export unavailable" in finished
    assert "retained checked replay" not in finished
    assert not prove.is_active(session.webstate)
    assert prove.get_script(session.webstate) is None
    assert "No replay script is available" in session.run("script")
    assert previous.theorem == "0 = 0"
