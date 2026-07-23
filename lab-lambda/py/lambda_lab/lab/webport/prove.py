"""Browser ``prove`` command - the interactive Curry-Howard proof builder.

Port of the desktop ``ch build`` flow (``lab/commands/ch.py`` +
``lab/curry_howard/{types,builder,tactics,library,proof_search}.py``) to the
Pyodide + xterm.js build. Pure stdlib; colored output is raw ANSI escapes in
the same idiom as ``driver.py``.

Public API
----------

``handle(arg, state)`` where ``state`` is the mutable dict the driver persists
across lines:

* no active session: ``arg`` is everything after the word ``prove`` -
  a proposition/type starts a session; ``tactics``/``tactic [name]``/``lib
  [name]``/``help`` are informational subcommands;
* active session (``is_active(state)`` is True): the driver routes the *whole
  line* to ``handle`` - it is interpreted as a tactic (``intro``, ``intros``,
  ``exact``, ``apply``, ``refine``, ``assumption``) or a meta command
  (``hint``, ``undo``, ``?``, ``t``/``tactics``, ``qed``, ``abort``).

``qed`` (aliases ``done``, ``finish``) extracts the final λ-term - the proof
term. ``abort`` (aliases ``quit``, ``exit``, ``q``) leaves the builder.

Desktop features that need a Lean toolchain (``ch lean`` / ``ch verify`` /
``lean_bridge``) are stubbed with a one-line notice.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from lambda_lab.lab import lc
from lambda_lab.lab.webport import proof_builder as builder
from lambda_lab.lab.webport.data_prove import (
    LEMMAS,
    LIBRARY,
    LIBRARY_INDEX,
    STRINGS,
    TACTIC_INDEX,
    TACTICS,
)
from lambda_lab.lab.webport.stlc_types import (
    STLCTypeError,
    infer,
    parse_type,
    pretty_type,
)

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
MAX_INPUT = 2_000

# State keys (unique prefix `prove.`).
KEY_SESSION = "prove.session"
KEY_TARGET = "prove.target"
KEY_TARGET_SRC = "prove.target_src"

LEAN_STUB_NOTICE = ("Lean export/verification is desktop-only (it needs a Lean toolchain); "
                    "the browser build stops at the λ-term.")

_QED_WORDS = ("qed", "done", "finish")
_ABORT_WORDS = ("abort", "quit", "exit", "q")
_SESSION_ONLY_WORDS = set(_QED_WORDS) | set(_ABORT_WORDS) | {
    "intro", "intros", "exact", "apply", "refine", "assumption", "hint", "undo", "?",
}


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _t(key: str, **kwargs: object) -> str:
    msg = STRINGS.get(key, key)
    try:
        return msg.format(**kwargs)
    except Exception:
        return msg


def is_active(state: dict) -> bool:
    """True while a proof session is in progress (driver routes raw lines here)."""
    return state.get(KEY_SESSION) is not None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _show_state(st: builder.ProofState) -> List[str]:
    """Text version of the desktop per-goal panels."""
    rows: List[str] = []
    total = len(st.goals)
    for idx, goal in enumerate(st.goals, start=1):
        ctx = ", ".join(f"{n} : {pretty_type(ty)}" for n, ty in goal.context)
        if not ctx:
            ctx = _t("ch.build.empty_context")
        rows.append(bold(_t("ch.build.goal_label", idx=idx, total=total)))
        rows.append(dim(f"  {_t('ch.build.context_label')}: ") + ctx)
        rows.append(dim(f"  {_t('ch.build.target_label')}:  ") + green(pretty_type(goal.target)))
        if idx == 1:
            rows.append(dim(f"  {_t('ch.build.term_label')}:    ") + cyan(st.partial_str()))
    return rows


def _closed_banner() -> List[str]:
    return [
        green(_t("ch.build.no_more_goals")),
        dim("Type ") + bold("qed") + dim(" to extract the proof term, or ")
        + bold("undo") + dim(" to step back."),
    ]


def _cheat_sheet() -> str:
    """Text version of the desktop builder cheat sheet (`t` inside `ch build`)."""
    syntax = {
        "intro": "intro [name]",
        "intros": "intros [names]",
        "exact": "exact <term>",
        "apply": "apply <term>",
        "refine": "refine <term>",
        "assumption": "assumption",
    }
    rows = [bold(magenta(_t("ch.build.tactics_ref.title"))), ""]
    aliases = {"intros": "intro"}
    for name in ("intro", "intros", "exact", "apply", "refine", "assumption"):
        entry = TACTIC_INDEX.get(name) or TACTIC_INDEX.get(aliases.get(name, ""))
        label = syntax[name].ljust(16)
        if entry is None:
            rows.append("  " + green(label) + dim(STRINGS["games.runner.tactics_ref.no_doc"]))
            continue
        rows.append("  " + green(label) + entry["summary"])
        rows.append(" " * 18 + dim(f"{entry['example_goal']}   =>   {entry['example_after']}"))
    rows.append("")
    meta = [
        ("hint", _t("ch.build.tactics_ref.meta.hint")),
        ("undo", _t("ch.build.tactics_ref.meta.undo")),
        ("qed / done", _t("ch.build.tactics_ref.meta.done")),
        ("abort / quit / q", _t("ch.build.tactics_ref.meta.quit")),
        ("?", _t("ch.build.tactics_ref.meta.show")),
        ("t / tactics", _t("ch.build.tactics_ref.meta.tactics")),
    ]
    for name, desc in meta:
        rows.append("  " + green(name.ljust(16)) + dim(desc))
    return _lines(*rows)


def _usage() -> str:
    return _lines(
        bold(magenta("prove")) + dim("  —  interactive Curry–Howard proof builder"), "",
        "  " + _t("ch.build.usage"),
        "  Propositions live in the implicational fragment: atoms (P, Q, …) and →/->.",
        "  Each following line is a tactic; the proof term grows as you work.", "",
        "  " + bold("Tactics") + "  " + dim("intro [name] · intros · exact <term> · apply <term> · "
                                            "refine <term> · assumption"),
        "  " + bold("Meta") + "     " + dim("hint · undo · ? (state) · t (cheat sheet) · "
                                            "qed (extract the λ-term) · abort"), "",
        "  " + bold("More"),
        f"    {green('prove tactics')}        the builder cheat sheet",
        f"    {green('prove tactic')} {dim('[name]')}  encyclopedia of Lean 4 tactics",
        f"    {green('prove lib')} {dim('[name]')}     combinator library (id, K, S, B, C, …)", "",
        dim("Try: ") + yellow("prove P -> Q -> P") + dim("  ·  ")
        + yellow("prove (P -> Q -> R) -> (P -> Q) -> P -> R"),
    )


def _tactic_catalog() -> str:
    rows = [bold(magenta(_t("ch.tactic.list_title"))), ""]
    for entry in TACTICS:
        rows.append("  " + green(entry["name"].ljust(14)) + entry["summary"])
    rows.append("")
    rows.append(bold("Mathlib lemma cheat sheet") + dim("  (for exact / rw on the desktop)"))
    for l in LEMMAS:
        rows.append("  " + cyan(l["name"].ljust(14)) + l["statement"])
    rows.append("")
    rows.append(dim("Details: ") + bold(green("prove tactic <name>")) + dim("  e.g. ")
                + yellow("prove tactic cases"))
    return _lines(*rows)


def _tactic_entry(name: str) -> str:
    entry = TACTIC_INDEX.get(name)
    if entry is None:
        return yellow(_t("ch.tactic.unknown", name=name))
    label = "  {}: ".format
    rows = [
        bold(magenta(_t("ch.tactic.entry_title", name=entry["name"]))), "",
        dim(label(_t("ch.tactic.row.summary"))) + entry["summary"],
        dim(label(_t("ch.tactic.row.lambda"))) + entry["lambda_effect"],
        dim(label(_t("ch.tactic.row.goal"))) + entry["goal_effect"],
        dim(label(_t("ch.tactic.row.when"))) + entry["when"],
        dim(label(_t("ch.tactic.row.example_goal"))) + cyan(entry["example_goal"]),
        dim(label(_t("ch.tactic.row.example_after"))) + green(entry["example_after"]),
    ]
    if entry["name"] not in builder.TACTIC_NAMES:
        rows.append("")
        rows.append(dim("Note: the browser builder operates on the implicational fragment only - "
                        f"`{entry['name']}` is documentation, not an operational tactic here."))
    return _lines(*rows)


def _lib_catalog() -> str:
    rows = [bold(magenta(_t("ch.lib.list_title"))), ""]
    for c in LIBRARY:
        ty = c["type"] or _t("ch.lib.row.untypeable")
        alias = f" ({', '.join(c['aliases'])})" if c["aliases"] else ""
        rows.append("  " + green(c["name"].ljust(6)) + cyan(c["lambda"].ljust(34))
                    + ty.ljust(30) + dim(alias))
    rows.append("")
    rows.append(dim("Details: ") + bold(green("prove lib <name>")) + dim("  e.g. ")
                + yellow("prove lib S"))
    return _lines(*rows)


def _lib_entry(name: str) -> str:
    c = LIBRARY_INDEX.get(name)
    if c is None:
        return yellow(_t("ch.lib.unknown", name=name))
    label = "  {}: ".format
    rows = [
        bold(magenta(_t("ch.lib.entry_title", name=c["name"]))), "",
        dim(label(_t("ch.lib.row.lambda"))) + cyan(c["lambda"]),
        dim(label(_t("ch.lib.row.type"))) + (c["type"] or _t("ch.lib.row.untypeable")),
        dim(label(_t("ch.lib.row.lean"))) + c["lean"],
    ]
    if c["aliases"]:
        rows.append(dim(label(_t("ch.lib.row.aliases"))) + ", ".join(c["aliases"]))
    rows.append("  " + c["desc"])
    return _lines(*rows)


def _tactic_error_text(e: builder.TacticError) -> str:
    msg = _t(e.message_key, **e.format_args)
    if e.message_key == "ch.build.tactic_error":
        return yellow(msg)
    return yellow(_t("ch.build.tactic_error", error=msg))


# ---------------------------------------------------------------------------
# Session flow
# ---------------------------------------------------------------------------


def _start_session(arg: str, state: dict) -> str:
    if len(arg) > MAX_INPUT:
        return red(f"Input is too long (max {MAX_INPUT} characters).")
    try:
        target = parse_type(arg)
    except ValueError as e:
        rows = [red(_t("ch.build.parse_error", error=e))]
        if any(ch in arg for ch in "∧∨¬⊕⇔↔&|~"):
            rows.append(dim("The builder handles the implicational fragment only: "
                            "atoms (P, Q, …) and →/->."))
        return _lines(*rows)
    st = builder.start(target)
    state[KEY_SESSION] = st
    state[KEY_TARGET] = target
    state[KEY_TARGET_SRC] = arg
    rows = [bold(magenta(_t("ch.build.title")))
            + dim("  —  ⊢ ") + green(pretty_type(target)), ""]
    rows.extend(_show_state(st))
    rows.append("")
    rows.append(dim(_t("ch.build.tactics_hint")))
    return _lines(*rows)


def _finish_session(state: dict) -> str:
    st: builder.ProofState = state[KEY_SESSION]
    if not st.is_done():
        return yellow(_t("ch.build.done_without_close"))
    target = state.get(KEY_TARGET)
    final = st.final_term()
    _clear(state)
    rows = [green(_t("ch.build.no_more_goals")) + "  " + bold(green("QED."))]
    if final is not None:
        rows.append(dim(f"  {_t('ch.build.final_term')}: ") + cyan(lc.pretty(final)))
        if target is not None:
            rows.append(dim("  Proves:            ") + green(pretty_type(target)))
        try:
            principal = pretty_type(infer(final))
            rows.append(dim("  Principal type:    ") + principal)
        except STLCTypeError:
            pass
    rows.append("")
    rows.append(dim(f"[{LEAN_STUB_NOTICE}]"))
    rows.append(dim("Cross-ref: try ") + bold("kb curry-howard") + dim("."))
    return _lines(*rows)


def _clear(state: dict) -> None:
    for key in (KEY_SESSION, KEY_TARGET, KEY_TARGET_SRC):
        state.pop(key, None)


def _session_line(line: str, state: dict) -> str:
    st: builder.ProofState = state[KEY_SESSION]
    line = line.strip()
    if not line:
        return ""
    word = line.split()[0].lower()

    if word in _ABORT_WORDS:
        _clear(state)
        return dim(_t("ch.build.bye"))
    if word in _QED_WORDS:
        return _finish_session(state)
    if line == "undo":
        try:
            st = builder.undo(st)
        except builder.TacticError as e:
            return _tactic_error_text(e)
        state[KEY_SESSION] = st
        rows = [dim(_t("ch.build.undo_done"))]
        rows.extend(_show_state(st) if not st.is_done() else _closed_banner())
        return _lines(*rows)
    if line == "hint":
        suggestion = builder.hint(st)
        if suggestion is None:
            return dim(_t("ch.build.hint_none"))
        return green(_t("ch.build.hint_suggest", term=suggestion))
    if line == "?":
        if st.is_done():
            return _lines(*_closed_banner())
        return _lines(*_show_state(st))
    if line in ("t", "tactics", ":t"):
        return _cheat_sheet()

    # A tactic: name [args...]
    parts = line.split(maxsplit=1)
    tac = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    try:
        st = builder.apply_tactic(st, tac, rest)
    except builder.TacticError as e:
        rows = [_tactic_error_text(e)]
        if e.message_key == "ch.build.unknown_tactic" and tac in TACTIC_INDEX:
            rows.append(dim(f"`{tac}` is in the tactic encyclopedia (`prove tactic {tac}`) "
                            "but the builder covers the implicational fragment (→) only."))
        return _lines(*rows)
    state[KEY_SESSION] = st
    if st.is_done():
        return _lines(*_closed_banner())
    return _lines(*_show_state(st))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def handle(arg: str, state: dict) -> str:
    """Handle one line of the ``prove`` family.

    ``arg`` is the text after ``prove`` when no session is active, or the whole
    input line while a session is active (see :func:`is_active`).
    """
    arg = (arg or "").strip()

    if is_active(state):
        return _session_line(arg, state)

    if not arg or arg.lower() == "help":
        return _usage()

    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if sub in ("tactics", "t"):
        return _cheat_sheet()
    if sub == "tactic":
        return _tactic_entry(rest) if rest else _tactic_catalog()
    if sub == "lib":
        return _lib_entry(rest) if rest else _lib_catalog()
    if sub in _SESSION_ONLY_WORDS:
        return _lines(
            dim("No proof in progress."),
            dim("Start one with ") + bold(green("prove <type>")) + dim("  e.g. ")
            + yellow("prove P -> Q -> P"),
        )

    return _start_session(arg, state)
