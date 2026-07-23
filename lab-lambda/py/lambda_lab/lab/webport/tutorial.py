"""Browser port of the desktop ``tutorial`` command — guided chapter walkthroughs.

Desktop source: ``lambda_lab/lab/commands/tutorial.py`` plus the
``lambda_lab/lab/tutorial`` package (loader / models / runner / progress).
The 12 JSON chapters are frozen into :mod:`data_tutorials` (English strings).

Subcommands (same surface as the desktop):

* ``tutorial``                  — table of chapters + status
* ``tutorial <slug|number>``    — start a chapter
* ``tutorial next``             — first unfinished chapter
* ``tutorial progress``         — compact status table
* ``tutorial reset``            — clear the progress journal
* ``tutorial help``             — detailed help

The desktop runner is a blocking read-loop; the browser build is a
line-at-a-time REPL, so the walkthrough is re-expressed as a state machine
stored in the driver's ``state`` dict (keys prefixed ``tutorial.``). While a
chapter is active, every input line is a control: ENTER advances, ``s``
skips, ``q`` quits, ``?`` re-shows the step — exactly the desktop controls.

Graceful degradation: step kinds that need the Lean toolchain, the quiz
bundles, the games engine or the kb topic files (``command``, ``lean_walk``,
``quiz_checkpoint``, ``exercise``, ``kb``) print their full desktop intro
(labels, Lean sources, targets) plus a one-line desktop-only notice;
``lean_walk`` steps additionally get a live.lean-lang.org link. Progress
lives only in the session state — nothing touches the filesystem.
"""

from __future__ import annotations

import textwrap
import urllib.parse
from typing import Dict, List, Optional

from lambda_lab.lab.webport.data_tutorials import CHAPTERS

RESET = "\x1b[0m"


def _c(s: str, code: str) -> str:
    return f"\x1b[{code}m{s}{RESET}"


def bold(s: str) -> str: return _c(s, "1")
def dim(s: str) -> str: return _c(s, "2")
def green(s: str) -> str: return _c(s, "92")
def cyan(s: str) -> str: return _c(s, "96")
def yellow(s: str) -> str: return _c(s, "93")
def magenta(s: str) -> str: return _c(s, "95")
def red(s: str) -> str: return _c(s, "91")
def blue(s: str) -> str: return _c(s, "94")


NL = "\r\n"
WRAP = 76

# State keys (unique prefix for the shared driver state dict).
K_ACTIVE = "tutorial.active"    # {"slug": str, "step": int, "phase": "gate"|"post"}
K_STATUS = "tutorial.status"    # {slug: "in_progress"|"complete"}

# Step kinds that pause BEFORE running their action (desktop pre-action gate).
GATED_KINDS = ("command", "lean_walk", "quiz_checkpoint", "exercise")

KIND_LABEL = {
    "narrative": "Narrative",
    "command": "Command",
    "lean_walk": "Lean term walk",
    "quiz_checkpoint": "Checkpoint - quiz",
    "exercise": "Exercise",
    "kb": "Reading",
}

STATUS_LABEL = {
    "not_started": "not started",
    "in_progress": "in progress",
    "complete": "complete",
}


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _wrap(text: str, indent: str = "  ") -> List[str]:
    out: List[str] = []
    for para in (text or "").splitlines():
        if not para.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(
            para, width=WRAP, initial_indent=indent, subsequent_indent=indent))
    return out


def _live_lean_url(code: str) -> str:
    """A live.lean-lang.org link that opens the Lean 4 web editor with this code."""
    return "https://live.lean-lang.org/#code=" + urllib.parse.quote(code, safe="")


# ---------------------------------------------------------------------------
# Catalog helpers
# ---------------------------------------------------------------------------


def _find_chapter(token: str) -> Optional[dict]:
    """Look up a chapter by slug or 1-based order number (desktop loader)."""
    token = (token or "").strip()
    if not token:
        return None
    if token.isdigit():
        want = int(token)
        for ch in CHAPTERS:
            if ch["order"] == want:
                return ch
        return None
    for ch in CHAPTERS:
        if ch["slug"] == token:
            return ch
    return None


def _statuses(state: dict) -> Dict[str, str]:
    st = state.get(K_STATUS)
    return st if isinstance(st, dict) else {}


def _mark(state: dict, slug: str, status: str) -> None:
    st = state.setdefault(K_STATUS, {})
    if status == "in_progress" and st.get(slug) == "complete":
        return  # desktop journal reducer: complete is never downgraded
    st[slug] = status


def is_active(state: dict) -> bool:
    """True while a chapter walkthrough is consuming input lines."""
    return isinstance(state.get(K_ACTIVE), dict)


# ---------------------------------------------------------------------------
# Rendering (desktop wording, driver.py ANSI idiom)
# ---------------------------------------------------------------------------


def _pad(s: str, w: int) -> str:
    return s + " " * (w - len(s))


def _chapters_table(state: dict) -> List[str]:
    statuses = _statuses(state)
    headers = ("#", "Chapter", "Steps", "Time", "Status")
    rows = []
    for ch in CHAPTERS:
        status = statuses.get(ch["slug"], "not_started")
        rows.append((str(ch["order"]), ch["title"], str(len(ch["steps"])),
                     f"~{ch['duration_min']} min", status))
    widths = [max(len(headers[i]), max(len(r[i] if i < 4 else STATUS_LABEL[r[4]])
                                       for r in rows)) for i in range(5)]
    out = [bold(magenta("Lambda Lab tutorial - chapters")), ""]
    out.append("  " + "  ".join(bold(_pad(h, widths[i])) for i, h in enumerate(headers)))
    for order, title, steps, time_, status in rows:
        label = STATUS_LABEL[status]
        colored_status = (green(label) if status == "complete"
                          else yellow(label) if status == "in_progress"
                          else dim(label))
        out.append("  " + "  ".join((
            green(_pad(order, widths[0])),
            _pad(title, widths[1]),
            cyan(_pad(steps, widths[2])),
            cyan(_pad(time_, widths[3])),
            colored_status + " " * (widths[4] - len(label)),
        )))
    out.append("")
    out.append(dim("Type `tutorial 1`, `tutorial <slug>` or `tutorial next`."))
    return out


def _progress_table(state: dict) -> List[str]:
    statuses = _statuses(state)
    out: List[str] = []
    if not statuses:
        out.append(dim("No recorded attempts. Start with `tutorial 1`."))
    out.append(bold(magenta("Tutorial progress")))
    out.append("")
    width = max(len(ch["title"]) for ch in CHAPTERS)
    for ch in CHAPTERS:
        status = statuses.get(ch["slug"], "not_started")
        label = STATUS_LABEL[status]
        colored = (green(label) if status == "complete"
                   else yellow(label) if status == "in_progress"
                   else dim(label))
        out.append(f"  {green(str(ch['order']).rjust(2))}  {_pad(ch['title'], width)}  {colored}")
    return out


def _help_lines() -> List[str]:
    return [
        bold(magenta("Tutorial - help")), "",
        "The `tutorial` command is a coherent walk through twelve mathematical chapters:",
        f"  {green('tutorial')}                    - print the table of chapters",
        f"  {green('tutorial')} {dim('<slug|number>')}      - run a chapter (e.g. `tutorial 1` or `tutorial gauss_sum`)",
        f"  {green('tutorial next')}               - jump to the next unfinished chapter",
        f"  {green('tutorial progress')}           - status table",
        f"  {green('tutorial reset')}              - clear the progress journal",
        f"  {green('tutorial help')}               - show this help", "",
        dim("During a chapter: ENTER = advance, s = skip the step, q = quit, ? = re-show the step."),
    ]


def _chapter_header(ch: dict) -> List[str]:
    out = [bold(magenta(f"Chapter {ch['order']}: {ch['title']}")), ""]
    if ch.get("summary"):
        out.extend(_wrap(ch["summary"]))
        out.append("")
    out.append(dim(f"  Steps: {len(ch['steps'])}, time: ~{ch['duration_min']} min."))
    out.append(dim("  Controls: ENTER = next, s = skip step, q = quit, ? = re-show step."))
    return out


def _step_header(ch: dict, idx: int) -> List[str]:
    step = ch["steps"][idx]
    kind = KIND_LABEL.get(step["kind"], step["kind"])
    label = step.get("title") or step.get("label") or kind
    return [
        "",
        bold(f"Step {idx + 1}/{len(ch['steps'])}") + dim(" · " + kind),
        "  " + label,
        dim("  (ENTER = next · s = skip · q = quit · ? = re-show)"),
    ]


def _chapter_complete(ch: dict) -> List[str]:
    return [
        "",
        bold(green("Chapter complete")),
        f"  Done - chapter `{ch['title']}` complete. Type " + yellow("tutorial next")
        + " for the next one.",
    ]


def _gate_prompt() -> str:
    return dim("[ENTER to run this step · s to skip · q to quit]")


def _post_prompt(ch: dict, idx: int) -> str:
    return dim(f"[tutorial {idx + 1}/{len(ch['steps'])} — ENTER next, s skip, q quit, ? re-show]")


# ---------------------------------------------------------------------------
# Per-kind step bodies (desktop intros + one-line desktop-only notices)
# ---------------------------------------------------------------------------


def _body_narrative(step: dict) -> List[str]:
    out: List[str] = []
    if step.get("title"):
        out.append(bold(step["title"]))
    out.extend(_wrap(step.get("body") or step.get("label") or ""))
    return out


def _body_command(step: dict) -> List[str]:
    out: List[str] = []
    if step.get("label"):
        out.extend(_wrap(step["label"]))
    out.append(dim("  Running command:"))
    out.append("    " + yellow(step.get("command", "")))
    out.append("  " + yellow(f"Desktop-only step: `{step.get('command', '')}` runs in the full desktop Lambda Lab — shown here, not executed."))
    return out


def _body_lean_walk(step: dict) -> List[str]:
    out: List[str] = []
    title = step.get("label") or step.get("name") or "Lean term walk"
    out.append(bold(magenta("Lean term walk")) + dim(" · " + title))
    if step.get("narrative"):
        out.extend(_wrap(step["narrative"]))
        out.append("")
    src = step.get("lean_source", "")
    if not src:
        out.append(dim("  No Lean source - step skipped."))
        return out
    out.append(dim("  Lean source:"))
    for ln in src.strip("\n").splitlines():
        out.append("    " + cyan(ln))
    out.append("")
    out.append(dim("  The interactive term walker needs the desktop Lean toolchain; open the source in Live Lean instead:"))
    out.append("  " + blue(_live_lean_url(src)))
    return out


def _body_quiz(step: dict) -> List[str]:
    out = [f"  Quiz bundle: `{step.get('bundle', '')}`."]
    if step.get("min_correct"):
        out.append(f"  Pass threshold: {step['min_correct']} correct answers.")
    out.append("  " + dim("Desktop-only step: quiz bundles run in the desktop build — type ")
               + bold("quiz") + dim(" at the main prompt for browser self-check questions."))
    return out


def _body_exercise(step: dict) -> List[str]:
    out: List[str] = []
    out.extend(_wrap(step.get("label") or "Opening a `games play`-style exercise level."))
    spec = step.get("exercise")
    if isinstance(spec, dict):
        out.append(f"  Target: game `{spec['game']}`, world `{spec['world']}`, level {spec['level']}.")
    else:
        out.append(dim("  No exercise spec attached to this step."))
    out.append("  " + dim("Desktop-only step: exercise levels need the desktop `games` engine."))
    return out


def _body_kb(step: dict) -> List[str]:
    out: List[str] = []
    if step.get("label"):
        out.extend(_wrap(step["label"]))
    topic = step.get("topic", "")
    out.append("  " + dim(f"Desktop-only step: `kb topic {topic}` opens in the desktop build — try ")
               + bold("kb") + dim(" at the main prompt for core concepts."))
    return out


def _dispatch(step: dict) -> List[str]:
    kind = step.get("kind", "")
    if kind == "narrative":
        return _body_narrative(step)
    if kind == "command":
        return _body_command(step)
    if kind == "lean_walk":
        return _body_lean_walk(step)
    if kind == "quiz_checkpoint":
        return _body_quiz(step)
    if kind == "exercise":
        return _body_exercise(step)
    if kind == "kb":
        return _body_kb(step)
    return [yellow(f"Unknown step kind: {kind}.")]


# ---------------------------------------------------------------------------
# Walkthrough state machine (desktop runner, inverted for line-at-a-time input)
# ---------------------------------------------------------------------------


def _control(line: str) -> str:
    """Map raw input to a control word: '' (advance), 's', 'q', '?', 'other'."""
    stripped = (line or "").strip().lower()
    if not stripped:
        return ""
    if stripped in ("s", "skip"):
        return "s"
    if stripped in ("q", "quit", "exit"):
        return "q"
    if stripped == "?":
        return "?"
    return "other"


def _enter_step(ch: dict, idx: int, state: dict, out: List[str]) -> None:
    """Show step ``idx`` (or finish the chapter) and set the awaited phase."""
    if idx >= len(ch["steps"]):
        state.pop(K_ACTIVE, None)
        _mark(state, ch["slug"], "complete")
        out.extend(_chapter_complete(ch))
        return
    step = ch["steps"][idx]
    out.extend(_step_header(ch, idx))
    if step["kind"] in GATED_KINDS:
        state[K_ACTIVE] = {"slug": ch["slug"], "step": idx, "phase": "gate"}
        out.append(_gate_prompt())
    else:
        out.append("")
        out.extend(_dispatch(step))
        state[K_ACTIVE] = {"slug": ch["slug"], "step": idx, "phase": "post"}
        out.append("")
        out.append(_post_prompt(ch, idx))


def _start_chapter(ch: dict, state: dict) -> str:
    _mark(state, ch["slug"], "in_progress")
    out: List[str] = []
    out.extend(_chapter_header(ch))
    _enter_step(ch, 0, state, out)
    return _lines(*out)


def _on_line(line: str, state: dict) -> str:
    active = state.get(K_ACTIVE)
    ch = _find_chapter(active.get("slug", "")) if isinstance(active, dict) else None
    if ch is None:  # defensive — stale state
        state.pop(K_ACTIVE, None)
        return yellow("The tutorial catalog is empty.")
    idx = int(active.get("step", 0))
    phase = active.get("phase", "post")
    step = ch["steps"][idx]
    ctl = _control(line)
    out: List[str] = []

    if phase == "gate":
        if ctl == "q":
            state.pop(K_ACTIVE, None)
            return dim("Leaving the tutorial. Progress saved.")
        if ctl == "s":
            out.append(dim("Step skipped."))
            _enter_step(ch, idx + 1, state, out)
            return _lines(*out)
        # ENTER or anything else → run the step's action.
        out.append("")
        out.extend(_dispatch(step))
        state[K_ACTIVE] = {"slug": ch["slug"], "step": idx, "phase": "post"}
        out.append("")
        out.append(_post_prompt(ch, idx))
        return _lines(*out)

    # phase == "post"
    if ctl == "":
        _enter_step(ch, idx + 1, state, out)
        return _lines(*out)
    if ctl == "s":
        out.append(dim("Step skipped."))
        _enter_step(ch, idx + 1, state, out)
        return _lines(*out)
    if ctl == "q":
        state.pop(K_ACTIVE, None)
        return dim("Leaving the tutorial. Progress saved.")
    if ctl == "?":
        out.extend(_step_header(ch, idx))
        out.append(_post_prompt(ch, idx))
        return _lines(*out)
    out.append(dim("ENTER = advance, `s` = skip, `q` = quit, `?` = re-show."))
    out.append(_post_prompt(ch, idx))
    return _lines(*out)


# ---------------------------------------------------------------------------
# Subcommand dispatch (desktop commands/tutorial.py)
# ---------------------------------------------------------------------------


def _cmd_list(state: dict) -> str:
    return _lines(*_chapters_table(state))


def _cmd_progress(state: dict) -> str:
    return _lines(*_progress_table(state))


def _cmd_reset(state: dict) -> str:
    state.pop(K_STATUS, None)
    state.pop(K_ACTIVE, None)
    return green("Progress journal cleared.")


def _cmd_next(state: dict) -> str:
    statuses = _statuses(state)
    for ch in CHAPTERS:
        if statuses.get(ch["slug"]) != "complete":
            head = f"Opening chapter {ch['order']}: {ch['title']}."
            return _lines(head, "", _start_chapter(ch, state))
    return green("All chapters complete. Congratulations!")


def _run_chapter(token: str, state: dict) -> str:
    ch = _find_chapter(token)
    if ch is None:
        return yellow(f"I do not know chapter `{token}`. Type `tutorial` to see the list.")
    return _start_chapter(ch, state)


def handle(arg: str, state: dict) -> str:
    """Entry point: ``arg`` is the text after ``tutorial`` — or, while a
    chapter is active, the raw input line (the driver routes lines here via
    :func:`is_active`)."""
    if is_active(state):
        return _on_line(arg, state)

    parts = [tok for tok in (arg or "").strip().split() if tok != "--no-clear"]
    if not parts:
        return _cmd_list(state)
    head = parts[0]
    if head in ("help", "?"):
        return _lines(*_help_lines())
    if head in ("progress", "stats", "score"):
        return _cmd_progress(state)
    if head in ("reset", "clear-progress"):
        return _cmd_reset(state)
    if head == "next":
        return _cmd_next(state)
    if head in ("list", "ls"):
        return _cmd_list(state)
    return _run_chapter(head, state)


__all__ = ["handle", "is_active"]
