"""ENTER-driven Peano Lab tutorials backed by real checked proof sessions.

The browser driver owns the outer tutorial state.  Each chapter owns a private
``ProofCommandRunner`` whose nested state is passed directly to
``peano_lab.ui.prove``.  This separation is deliberate: routing a tutorial's
commands back through the same driver would deadlock because the active
tutorial correctly owns every raw input line.

While active, the grammar is intentionally tiny and deterministic:

* ENTER executes/acknowledges the displayed step;
* ``?`` re-renders it without changing state;
* ``q`` quits and preserves the in-progress status;
* every other line is refused without advancing.

Command failures stay on the same step.  A QED-gated chapter is marked complete
only after the normal proof UI has closed its session following the independent
kernel check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from . import prove as web_prove
from .data_tutorials import CHAPTERS


NL = "\r\n"
K_ACTIVE = "pa.tutorial.active"
K_STATUS = "pa.tutorial.status"
K_RUNNER = "pa.tutorial.runner"
K_LAST_RUN = "pa.tutorial.last_run"


class TutorialCommandError(RuntimeError):
    """A frozen tutorial command no longer works against the real engine."""


class CommandRunner(Protocol):
    """Minimal injectable boundary used by the deterministic state machine."""

    checked_qed: bool
    commands: list[str]

    def run(self, command: str) -> str:
        """Execute one frozen command or raise ``TutorialCommandError``."""


@dataclass
class ProofCommandRunner:
    """Execute a tutorial script through the production proof-session API."""

    proof_state: dict = field(default_factory=dict)
    commands: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    checked_qed: bool = False

    def run(self, command: str) -> str:
        command = command.strip()
        if not command:
            raise TutorialCommandError("the tutorial contains an empty command.")
        self.commands.append(command)

        if command.startswith("pa prove "):
            if web_prove.is_active(self.proof_state):
                raise TutorialCommandError("a nested proof command was attempted.")
            output = web_prove.handle(command[len("pa prove ") :], self.proof_state)
            if not web_prove.is_active(self.proof_state):
                raise TutorialCommandError(
                    "the tutorial's `pa prove` command did not open a proof."
                )
        else:
            if not web_prove.is_active(self.proof_state):
                raise TutorialCommandError(
                    f"cannot run `{command}` because no tutorial proof is active."
                )
            output = web_prove.handle(command, self.proof_state)

        self.outputs.append(output)
        first_line = output.splitlines()[0] if output.splitlines() else ""
        failure_markers = ("Tactic error:", "QED check failed:", "Error:")
        if any(marker in output for marker in failure_markers):
            raise TutorialCommandError(first_line or "the proof command failed.")

        if command == "qed":
            checked = "No open goals. QED." in output and not web_prove.is_active(
                self.proof_state
            )
            if not checked:
                raise TutorialCommandError(
                    "the independent kernel did not accept the tutorial proof."
                )
            self.checked_qed = True
        return output


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _find(token: str) -> dict | None:
    token = token.strip().lower()
    if token.isdigit():
        order = int(token)
        return next((chapter for chapter in CHAPTERS if chapter["order"] == order), None)
    return next((chapter for chapter in CHAPTERS if chapter["slug"] == token), None)


def _statuses(state: dict) -> dict[str, str]:
    value = state.get(K_STATUS)
    return value if isinstance(value, dict) else {}


def _mark(state: dict, slug: str, status: str) -> None:
    statuses = state.setdefault(K_STATUS, {})
    if status == "in_progress" and statuses.get(slug) == "complete":
        return
    statuses[slug] = status


def is_active(state: dict) -> bool:
    """Whether this shared browser state is currently owned by a tutorial."""

    return isinstance(state.get(K_ACTIVE), dict)


def _catalog(state: dict) -> str:
    statuses = _statuses(state)
    rows = ["Peano Lab tutorials", ""]
    for chapter in CHAPTERS:
        status = statuses.get(chapter["slug"], "not started")
        rows.append(
            f"  {chapter['order']}. {chapter['title']} "
            f"[{chapter['slug']}] — {status}"
        )
    rows.extend(("", "Start with `pa tutorial 1`, a slug, or `pa tutorial next`."))
    return _lines(*rows)


def _help() -> str:
    return _lines(
        "Peano Lab tutorial — help",
        "",
        "  pa tutorial                 list chapters",
        "  pa tutorial <n|slug>        start a chapter",
        "  pa tutorial next            first unfinished chapter",
        "  pa tutorial progress        show saved session progress",
        "  pa tutorial reset           clear tutorial progress",
        "",
        "During a chapter: ENTER advances; `?` re-shows; `q` quits.",
        "Frozen command steps execute against the real proof engine.",
    )


def _progress(state: dict) -> str:
    statuses = _statuses(state)
    rows = ["Tutorial progress", ""]
    for chapter in CHAPTERS:
        rows.append(
            f"  {chapter['slug']}: "
            f"{statuses.get(chapter['slug'], 'not started')}"
        )
    return _lines(*rows)


def _render_step(chapter: dict, index: int) -> str:
    step = chapter["steps"][index]
    rows = [
        f"Step {index + 1}/{len(chapter['steps'])} · {step['title']}",
        f"  kind: {step['kind']}",
    ]
    if step.get("body"):
        rows.extend(("", str(step["body"])))
    if step.get("path"):
        rows.extend(("", f"File: {step['path']}"))
    if step.get("source"):
        rows.extend(("", "Source change:"))
        rows.extend(f"    {line}" for line in str(step["source"]).splitlines())
    if step.get("command"):
        rows.extend(("", "Command:", f"  {step['command']}"))
    if step.get("note"):
        rows.extend(("", f"Why: {step['note']}"))
    rows.extend(("", "[ENTER run/advance · ? re-show · q quit]"))
    return _lines(*rows)


def _start(chapter: dict, state: dict, runner: CommandRunner | None) -> str:
    _mark(state, chapter["slug"], "in_progress")
    state[K_ACTIVE] = {"slug": chapter["slug"], "step": 0}
    state[K_RUNNER] = runner if runner is not None else ProofCommandRunner()
    return _lines(
        f"Tutorial {chapter['order']}: {chapter['title']}",
        chapter["summary"],
        "",
        "Controls: ENTER advances; `?` re-shows; `q` quits.",
        "",
        _render_step(chapter, 0),
    )


def _complete(chapter: dict, state: dict, runner: CommandRunner) -> str:
    if chapter.get("requires_qed") and not runner.checked_qed:
        return _lines(
            "Tutorial cannot complete: its checked QED has not succeeded.",
            _render_step(chapter, len(chapter["steps"]) - 1),
        )
    state[K_LAST_RUN] = {
        "slug": chapter["slug"],
        "commands": tuple(runner.commands),
        "checked_qed": bool(runner.checked_qed),
    }
    state.pop(K_ACTIVE, None)
    state.pop(K_RUNNER, None)
    _mark(state, chapter["slug"], "complete")
    return _lines(
        f"Tutorial complete: {chapter['title']}.",
        "The final certificate passed the independent Peano kernel checker.",
    )


def _active_line(line: str, state: dict) -> str:
    active = state.get(K_ACTIVE)
    chapter = _find(str(active.get("slug", ""))) if isinstance(active, dict) else None
    runner = state.get(K_RUNNER)
    if chapter is None or not hasattr(runner, "run"):
        state.pop(K_ACTIVE, None)
        state.pop(K_RUNNER, None)
        return "Tutorial state was invalid and has been cleared."

    control = line.strip().lower()
    index = int(active.get("step", 0))
    if control == "?":
        return _render_step(chapter, index)
    if control in {"q", "quit"}:
        state.pop(K_ACTIVE, None)
        state.pop(K_RUNNER, None)
        return "Leaving the tutorial. Progress remains in progress."
    if control:
        return _lines(
            "This tutorial owns the complete line: press ENTER, `?`, or `q`.",
            _render_step(chapter, index),
        )

    step = chapter["steps"][index]
    rows: list[str] = []
    if step["kind"] == "command":
        rows.append(f"> {step['command']}")
        try:
            rows.append(runner.run(str(step["command"])))
        except TutorialCommandError as exc:
            rows.extend(
                (
                    f"Tutorial command failed: {exc}",
                    "The step did not advance.",
                    "",
                    _render_step(chapter, index),
                )
            )
            return _lines(*rows)
    else:
        rows.append("Step acknowledged.")

    next_index = index + 1
    if next_index >= len(chapter["steps"]):
        rows.extend(("", _complete(chapter, state, runner)))
        return _lines(*rows)
    active["step"] = next_index
    rows.extend(("", _render_step(chapter, next_index)))
    return _lines(*rows)


def handle(
    arg: str,
    state: dict,
    *,
    runner: CommandRunner | None = None,
) -> str:
    """Handle a ``pa tutorial`` argument or a tutorial-owned raw input line."""

    if is_active(state):
        return _active_line(arg, state)

    token = arg.strip().lower()
    if not token or token in {"list", "ls"}:
        return _catalog(state)
    if token in {"help", "?"}:
        return _help()
    if token in {"progress", "status"}:
        return _progress(state)
    if token == "reset":
        state.pop(K_ACTIVE, None)
        state.pop(K_RUNNER, None)
        state.pop(K_STATUS, None)
        state.pop(K_LAST_RUN, None)
        return "Tutorial progress cleared."
    if token == "next":
        statuses = _statuses(state)
        chapter = next(
            (ch for ch in CHAPTERS if statuses.get(ch["slug"]) != "complete"),
            None,
        )
        if chapter is None:
            return "All Peano Lab tutorials are complete."
        return _start(chapter, state, runner)

    chapter = _find(token)
    if chapter is None:
        return f"No tutorial named {arg.strip()!r}. Type `pa tutorial`."
    return _start(chapter, state, runner)


__all__ = [
    "CommandRunner",
    "K_ACTIVE",
    "K_LAST_RUN",
    "K_RUNNER",
    "K_STATUS",
    "ProofCommandRunner",
    "TutorialCommandError",
    "handle",
    "is_active",
]
