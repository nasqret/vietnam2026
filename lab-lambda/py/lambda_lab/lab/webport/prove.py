"""Browser ``prove`` command - the interactive Curry-Howard proof builder.

UI layer over the sound engine in ``proof_builder`` (which itself sits on the
``stlc_types`` kernel). Pure stdlib; colored output is raw ANSI escapes in the
same idiom as ``driver.py``.

Grammar (audit P1.1) — subcommands never steal propositions:

* an argument containing an arrow (``->`` or ``→``) is ALWAYS parsed as a
  proposition;
* ``prove t`` / ``prove tactics`` (exact, lowercase) — cheat sheet;
* ``prove tactic [name]`` / ``prove lib [name]`` (exact, lowercase) — docs;
* a session-only word (``qed``, ``intro``, …) is recognized only when the
  ENTIRE argument equals that word, case-sensitively — ``prove Q`` starts a
  proof of the atom ``Q``; it is never the ``q`` quit alias.

While a session is active (``is_active(state)``), the driver routes the whole
line here. ``qed``/``done``/``finish`` and ``abort``/``quit``/``exit``/``q``
match only as the COMPLETE line, case-sensitively (audit P1.2); ``help`` works
in-proof; a nested ``prove …`` is refused without touching the session.

``qed`` runs :func:`proof_builder.checked_final` — the completed term must be
hole-free, closed, typable, and actually prove the stated goal; if the check
fails the session survives (audit P0.1).
"""

from __future__ import annotations

from typing import List

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
    apply_subst,
    parse_type,
    pretty_type,
    pretty_types,
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
    """Text version of the desktop per-goal panels.

    Metavariable display names (α, β, …) are shared across ALL goals and
    contexts in the panel, so a constraint linking two goals is visible.
    """
    rows: List[str] = []
    total = len(st.goals)
    all_types = []
    for goal in st.goals:
        for _, ty in goal.context:
            all_types.append(apply_subst(ty, st.subst))
        all_types.append(apply_subst(goal.target, st.subst))
    pretty_list = pretty_types(all_types)
    pos = 0
    for idx, goal in enumerate(st.goals, start=1):
        names = [n for n, _ in goal.context]
        ctx_strs = pretty_list[pos:pos + len(names)]
        pos += len(names)
        target_str = pretty_list[pos]
        pos += 1
        ctx = ", ".join(f"{n} : {t}" for n, t in zip(names, ctx_strs))
        if not ctx:
            ctx = _t("ch.build.empty_context")
        rows.append(bold(_t("ch.build.goal_label", idx=idx, total=total)))
        rows.append(dim(f"  {_t('ch.build.context_label')}: ") + ctx)
        rows.append(dim(f"  {_t('ch.build.target_label')}:  ") + green(target_str))
        if idx == 1:
            rows.append(dim(f"  {_t('ch.build.term_label')}:    ") + cyan(st.partial_str()))
    return rows


def _closed_banner() -> List[str]:
    return [
        green(_t("ch.build.no_more_goals")),
        dim("Type ") + bold("qed") + dim(" to check and extract the proof term, or ")
        + bold("undo") + dim(" to step back."),
    ]


def _cheat_sheet() -> str:
    """Text version of the desktop builder cheat sheet (`t` inside the builder)."""
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
        label = syntax[name].ljust(18)
        if entry is None:
            rows.append("  " + green(label) + dim(STRINGS["games.runner.tactics_ref.no_doc"]))
            continue
        rows.append("  " + green(label) + entry["summary"])
        rows.append(" " * 20 + dim(f"{entry['example_goal']}   =>   {entry['example_after']}"))
    rows.append("")
    meta = [
        ("hint", _t("ch.build.tactics_ref.meta.hint")),
        ("undo", _t("ch.build.tactics_ref.meta.undo")),
        ("qed / done", _t("ch.build.tactics_ref.meta.done")),
        ("abort / quit / q", _t("ch.build.tactics_ref.meta.quit")),
        ("?", _t("ch.build.tactics_ref.meta.show")),
        ("t / tactics", _t("ch.build.tactics_ref.meta.tactics")),
        ("help", "This cheat sheet (works mid-proof)."),
    ]
    for name, desc in meta:
        rows.append("  " + green(name.ljust(18)) + dim(desc))
    rows.append("")
    rows.append(dim("qed / abort and friends act only when typed as the whole line."))
    return _lines(*rows)


def _usage() -> str:
    return _lines(
        bold(magenta("prove")) + dim("  —  interactive Curry–Howard proof builder"), "",
        "  " + _t("ch.build.usage"),
        "  Propositions live in the implicational fragment: atoms (P, Q, …) and →/->.",
        "  Each following line is a tactic; the proof term grows as you work.", "",
        "  " + bold("Tactics") + "  " + dim("intro [name] · intros · exact <term> · apply <term> · "
                                            "refine <term> · assumption"),
        "  " + bold("Meta") + "     " + dim("hint · undo · ? (state) · t (cheat sheet) · help · "
                                            "qed (check & extract the λ-term) · abort"), "",
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
    return yellow(_t("ch.build.tactic_error", error=str(e)))


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
    try:
        final, principal = builder.checked_final(st)
    except builder.InvalidProof as e:
        # The session SURVIVES a failed final check (audit P0.1).
        return _lines(
            red(f"QED check failed: {e}"),
            dim("The proof session is still active — ") + bold("?")
            + dim(" shows the state, ") + bold("undo") + dim(" steps back, ")
            + bold("abort") + dim(" leaves."),
        )
    target = state.get(KEY_TARGET)
    _clear(state)
    rows = [green(_t("ch.build.no_more_goals")) + "  " + bold(green("QED."))]
    rows.append(dim(f"  {_t('ch.build.final_term')}: ") + cyan(lc.pretty(final)))
    if target is not None:
        rows.append(dim("  Proves:            ") + green(pretty_type(target)))
    rows.append(dim("  Principal type:    ") + principal)
    rows.append("")
    rows.append(dim(f"[{LEAN_STUB_NOTICE}]"))
    rows.append(dim("Cross-ref: try ") + bold("kb curry-howard") + dim("."))
    return _lines(*rows)


def _clear(state: dict) -> None:
    for key in (KEY_SESSION, KEY_TARGET, KEY_TARGET_SRC):
        state.pop(key, None)


def _hint_text(st: builder.ProofState) -> str:
    status, suggestion = builder.hint(st)
    if status == "done":
        return _lines(green(_t("ch.build.no_more_goals")),
                      dim("Type ") + bold("qed")
                      + dim(" to check and extract the proof term."))
    if status == "assumption":
        return green(f"Hypothesis `{suggestion}` matches the goal — try ") \
            + bold(green(f"exact {suggestion}")) + green(" (or `assumption`).")
    if status == "exact":
        return green(_t("ch.build.hint_suggest", term=suggestion))
    if status == "intro":
        return _lines(
            yellow("No direct inhabitant found yet, but the goal is an implication."),
            dim("Try ") + bold("intro") + dim(" and then ask for a ") + bold("hint")
            + dim(" again."),
        )
    if status == "limit":
        return _lines(
            yellow("The proof search hit its depth limit — no verdict."),
            dim("The goal may still be provable: try ") + bold("intro") + dim(" / ")
            + bold("apply <hypothesis>") + dim(" by hand."),
        )
    if status == "meta":
        return _lines(
            yellow("This goal still contains undetermined types (α, β, …)."),
            dim("Close another goal first to pin them down, or use ")
            + bold("exact") + dim(" with a full term."),
        )
    # status == "none"
    return _lines(
        yellow("No proof of this goal exists in the implicational fragment (→ only)."),
        dim("If you believe the original proposition, check an earlier step with ")
        + bold("undo") + dim("."),
    )


def _session_line(line: str, state: dict) -> str:
    st: builder.ProofState = state[KEY_SESSION]
    line = line.strip()
    if not line:
        return ""

    # Complete-line, case-sensitive commands (audit P1.2): `qed please` and
    # the proposition atom `Q` must NOT trigger these.
    if line in _ABORT_WORDS:
        _clear(state)
        return dim(_t("ch.build.bye"))
    if line in _QED_WORDS:
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
        return _hint_text(st)
    if line == "?":
        if st.is_done():
            return _lines(*_closed_banner())
        return _lines(*_show_state(st))
    if line in ("t", "tactics", ":t", "help"):
        return _cheat_sheet()

    parts = line.split(maxsplit=1)
    tac = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    # A nested `prove …` must not touch the current session (audit P1.2).
    if tac == "prove":
        return _lines(
            yellow("A proof is already in progress."),
            dim("Finish it with ") + bold("qed") + dim(" or leave with ")
            + bold("abort") + dim(" before starting another."),
        )
    # Complete-line commands typed with extra words: refuse loudly rather
    # than fall through to `unknown tactic`.
    if tac in _QED_WORDS or tac in _ABORT_WORDS:
        return yellow(f"`{tac}` acts only when typed alone on the line "
                      f"(got extra input {rest!r}).")

    try:
        st = builder.apply_tactic(st, tac, rest)
    except builder.TacticError as e:
        rows = [_tactic_error_text(e)]
        if tac not in builder.TACTIC_NAMES and tac in TACTIC_INDEX:
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

    if not arg or arg == "help":
        return _usage()

    # Audit P1.1: anything containing an arrow is a PROPOSITION — subcommands
    # never steal it. `prove T -> T` proves T → T; `prove Q -> Q` proves Q → Q.
    has_arrow = ("->" in arg) or ("→" in arg)
    if not has_arrow:
        parts = arg.split(maxsplit=1)
        sub = parts[0]           # case-sensitive: `prove T` proves the atom T
        rest = parts[1].strip() if len(parts) > 1 else ""
        if arg in ("tactics", "t"):
            return _cheat_sheet()
        if sub == "tactic":
            return _tactic_entry(rest) if rest else _tactic_catalog()
        if sub == "lib":
            return _lib_entry(rest) if rest else _lib_catalog()
        if arg in _SESSION_ONLY_WORDS:
            return _lines(
                dim("No proof in progress."),
                dim("Start one with ") + bold(green("prove <type>")) + dim("  e.g. ")
                + yellow("prove P -> Q -> P"),
            )

    return _start_session(arg, state)
