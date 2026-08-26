"""M6 tutorials execute frozen scripts through checked proof sessions."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from peano_lab.ui import prove, tutorial
from peano_lab.ui.data_tutorials import CHAPTERS


def _finish(state: dict, slug: str, limit: int = 40) -> str:
    output = tutorial.handle(slug, state)
    for _ in range(limit):
        if not tutorial.is_active(state):
            return output
        output = tutorial.handle("", state)
    raise AssertionError(f"tutorial {slug!r} did not finish within {limit} ENTERs")


def test_catalog_contains_the_three_binding_tutorials_in_stable_order() -> None:
    assert [chapter["order"] for chapter in CHAPTERS] == [1, 2, 3]
    assert [chapter["slug"] for chapter in CHAPTERS] == [
        "add_comm",
        "symm_all",
        "norm_num",
    ]
    assert all(chapter["requires_qed"] for chapter in CHAPTERS)
    assert all(chapter["steps"][-1]["command"] == "qed" for chapter in CHAPTERS)

    output = tutorial.handle("", {})
    assert "Prove add_comm by hand" in output
    assert "Build a toy symm_all tactical" in output
    assert "Turn numerical computation into a proof" in output


@pytest.mark.parametrize("slug", ["add_comm", "symm_all", "norm_num"])
def test_enter_only_runs_real_commands_to_checked_completion(slug: str) -> None:
    state: dict = {}
    output = _finish(state, slug)

    assert "Tutorial complete:" in output
    assert "independent Peano kernel checker" in output
    assert state[tutorial.K_STATUS][slug] == "complete"
    assert state[tutorial.K_LAST_RUN]["slug"] == slug
    assert state[tutorial.K_LAST_RUN]["checked_qed"] is True
    assert state[tutorial.K_LAST_RUN]["commands"][-1] == "qed"
    assert not tutorial.is_active(state)


def test_add_comm_tutorial_reaches_the_production_checked_final(monkeypatch) -> None:
    calls: list[object] = []
    real_checked_final = prove.checked_final

    def spy(state, original_target, *, classical=False, trace=None):
        calls.append(original_target)
        return real_checked_final(
            state,
            original_target,
            classical=classical,
            trace=trace,
        )

    monkeypatch.setattr(prove, "checked_final", spy)
    state: dict = {}
    output = _finish(state, "add_comm")

    assert "Tutorial complete" in output
    assert len(calls) == 1
    commands = state[tutorial.K_LAST_RUN]["commands"]
    assert commands[0] == "pa prove forall n m. n + m = m + n"
    assert "auto" not in commands


def test_symm_all_walk_shows_source_changes_and_executes_equivalent_surface() -> None:
    state: dict = {}
    started = tutorial.handle("symm_all", state)
    assert "trusted kernel unchanged" in started

    tutorial.handle("", state)
    source_step = tutorial.handle("?", state)
    assert "peano_lab/ui/prove.py" in source_step
    assert "return all_goals" in source_step

    _finish_from_active(state)
    assert "all_goals symm" in state[tutorial.K_LAST_RUN]["commands"]


def test_norm_num_tutorial_pins_hints_and_both_supported_shapes() -> None:
    state: dict = {}
    output = _finish(state, "norm_num")

    assert "Tutorial complete" in output
    assert state[tutorial.K_LAST_RUN]["commands"] == (
        "pa prove (2 * 3 = 6) /\\ (forall n. n + (2 * 3) = n + 6)",
        "split",
        "hint",
        "norm_num",
        "intro n",
        "hint",
        "norm_num",
        "qed",
    )


def _finish_from_active(state: dict, limit: int = 40) -> str:
    output = ""
    for _ in range(limit):
        if not tutorial.is_active(state):
            return output
        output = tutorial.handle("", state)
    raise AssertionError("active tutorial did not finish")


def test_question_mark_is_pure_and_q_quits_without_losing_progress() -> None:
    state: dict = {}
    tutorial.handle("1", state)
    before = dict(state[tutorial.K_ACTIVE])

    shown = tutorial.handle("?", state)
    assert f"Step 1/{len(CHAPTERS[0]['steps'])}" in shown
    assert state[tutorial.K_ACTIVE] == before

    refused = tutorial.handle("pa axioms", state)
    assert "owns the complete line" in refused
    assert state[tutorial.K_ACTIVE] == before

    left = tutorial.handle("q", state)
    assert "Leaving the tutorial" in left
    assert not tutorial.is_active(state)
    assert state[tutorial.K_STATUS]["add_comm"] == "in_progress"


@dataclass
class _FailingRunner:
    checked_qed: bool = False
    commands: list[str] = field(default_factory=list)

    def run(self, command: str) -> str:
        self.commands.append(command)
        raise tutorial.TutorialCommandError("deliberate drift")


def test_failed_command_stays_on_the_exact_step() -> None:
    state: dict = {}
    runner = _FailingRunner()
    tutorial.handle("add_comm", state, runner=runner)
    tutorial.handle("", state)  # acknowledge narrative; command is now displayed
    before = dict(state[tutorial.K_ACTIVE])

    output = tutorial.handle("", state)

    assert "Tutorial command failed: deliberate drift" in output
    assert state[tutorial.K_ACTIVE] == before
    assert state[tutorial.K_STATUS]["add_comm"] == "in_progress"
    assert not runner.checked_qed


@dataclass
class _UncheckedRunner:
    checked_qed: bool = False
    commands: list[str] = field(default_factory=list)

    def run(self, command: str) -> str:
        self.commands.append(command)
        return "simulated output"


def test_chapter_cannot_complete_without_a_checked_qed_flag() -> None:
    state: dict = {}
    runner = _UncheckedRunner()
    tutorial.handle("symm_all", state, runner=runner)
    chapter = next(ch for ch in CHAPTERS if ch["slug"] == "symm_all")
    output = ""
    for _ in chapter["steps"]:
        output = tutorial.handle("", state)

    assert "checked QED has not succeeded" in output
    assert tutorial.is_active(state)
    assert state[tutorial.K_ACTIVE]["step"] == len(chapter["steps"]) - 1
    assert state[tutorial.K_STATUS]["symm_all"] == "in_progress"


def test_next_progress_and_reset_are_session_local() -> None:
    state: dict = {}
    assert "Tutorial 1:" in tutorial.handle("next", state)
    tutorial.handle("q", state)
    assert "add_comm: in_progress" in tutorial.handle("progress", state)
    assert tutorial.handle("reset", state) == "Tutorial progress cleared."
    assert tutorial.K_STATUS not in state
