"""Browser port of the desktop ``ch`` command — the Curry-Howard playground.

Faithful translation of ``lambda_lab/lab/commands/ch.py`` (Rich panels →
raw-ANSI rows, i18n → frozen English strings). Sub-commands:

* ``ch term <lambda>``      — principal type inference (Algorithm W) + the
  proof reading of the term,
* ``ch type <T>``           — type inhabitation / provability search for
  implicational intuitionistic propositions (Peirce's law comes out
  UNINHABITED),
* ``ch lib [name]``         — combinator catalogue (id, K, S, B, C, Y, …),
* ``ch lean <lambda>``      — emit a Lean 4 theorem for a λ-term,
* ``ch from-lean <expr>``   — parse a (subset) Lean term → λ + type,
* ``ch tactic [name]``      — the Lean tactic encyclopedia,
* ``ch build <T>``          — the interactive step-by-step proof builder,
* ``ch verify`` / ``ch explore --live`` — need a local Lean toolchain; the
  browser build prints a one-line notice (verify adds a Live Lean link),
* ``ch explore [slug]``     — static catalogue browser (the desktop's
  keyboard walker is desktop-only; the full proof-term tree is shown).

Driver contract: ``handle(arg, state) -> str`` where ``arg`` is everything
after ``ch``. The builder is an interactive flow: while a session is open,
``state["ch.interactive"]`` is truthy and the driver must route every raw
input line back into :func:`handle` unchanged (the line is then interpreted
as a builder tactic, exactly like the desktop's nested prompt).
State keys used (unique ``ch.`` prefix): ``ch.build``, ``ch.interactive``.
"""

from __future__ import annotations

import shlex
import urllib.parse
from typing import Dict, List, Optional, Tuple

from lambda_lab.lab.lc import free_vars, pretty
from lambda_lab.lab.parser import ParseError, parse

from . import _ansi as A
from . import ch_builder
from . import data_ch_explore
from . import data_ch_library
from . import data_ch_tactics
from .ch_stlc import (
    LeanParseError,
    STLCTypeError,
    find_inhabitant,
    infer,
    lambda_to_lean,
    lean_to_lambda,
    parse_type,
    pretty_type,
)

MAX_INPUT = 4_000

_BUILD_KEY = "ch.build"
_BUILD_TARGET_KEY = "ch.build.target"
_INTERACTIVE_KEY = "ch.interactive"


# ---------------------------------------------------------------------------
# English strings (desktop i18n EN entries, frozen)
# ---------------------------------------------------------------------------

MSG = {
    "ch.unknown": "Unknown sub-command `ch {sub}`. Try: term, type, lib, lean, from-lean, tactic, build, verify, explore.",
    "ch.help.title": "Curry-Howard playground",
    "ch.term.usage": "Usage: ch term <lambda>, e.g. `ch term \\p. p`.",
    "ch.term.parse_error": "Cannot parse the lambda-term: {error}",
    "ch.term.untypable": "Term not typeable in STLC: {error}",
    "ch.term.proof_interpretation": "Curry-Howard: this lambda-term is a proof that {prop}.",
    "ch.lean.usage": "Usage: ch lean <lambda> [--name=foo]. Produces `theorem foo : T := lambda`.",
    "ch.lean.parse_error": "Cannot parse the lambda-term: {error}",
    "ch.lean.untypable": "Term not typeable in STLC, cannot emit theorem: {error}",
    "ch.lib.unknown": "Unknown combinator `{name}`. Type `ch lib` to see the list.",
    "ch.lib.untypeable": "(not typeable in STLC)",
    "ch.type.usage": "Usage: ch type <T>, e.g. `ch type 'P -> P'`. Finds a lambda-term inhabiting T.",
    "ch.type.parse_error": "Cannot parse type: {error}",
    "ch.type.not_inhabited": (
        "Type {type} is not inhabited in intuitionistic STLC "
        "(classical theorems like Peirce have no constructive witness)."
    ),
    "ch.from_lean.usage": "Usage: ch from-lean '<expr>', e.g. `ch from-lean 'fun p => p'`.",
    "ch.from_lean.parse_error": "Cannot parse Lean expression: {error}",
    "ch.from_lean.untypable": "Parsed, but type does not exist in STLC: {error}",
    "ch.tactic.unknown": "Unknown tactic `{name}`. Run `ch tactic` to see the list.",
    "ch.tactic.list_title": "Encyclopedia of 22 Lean 4 tactics",
    "ch.build.usage": "Usage: ch build <type>, e.g. `ch build P -> P`.",
    "ch.build.parse_error": "Cannot parse type: {error}",
    "ch.build.tactics_hint": (
        "Tactics: intro [name], exact <term>, apply <term>, assumption, "
        "refine <term>, hint, undo, done, quit. Type `t` for a cheat sheet."
    ),
    "ch.build.no_more_goals": "All goals closed.",
    "ch.build.undo_done": "Last step undone.",
    "ch.build.history_empty": "History is empty - nothing to undo.",
    "ch.build.tactic_error": "Tactic error: {error}",
    "ch.build.hint_suggest": "Hint: try `exact {term}`.",
    "ch.build.hint_none": "No automatic hint for the current goal.",
    "ch.build.bye": "Leaving the builder.",
    "ch.build.done_without_close": "There are still open goals - cannot finish.",
    "ch.build.unknown_tactic": "Unknown tactic `{name}`. Type `hint` for a suggestion or `quit` to exit.",
    "ch.build.goal_not_implication": "Goal `{target}` is not an implication - `intro` does not apply here.",
    "ch.build.exact_needs_arg": "Tactic `exact` needs an argument, e.g. `exact p`.",
    "ch.build.apply_needs_arg": "Tactic `apply` needs an argument (the function to apply).",
    "ch.build.refine_needs_arg": "Tactic `refine` needs a term with holes `?_`.",
    "ch.build.exact_type_mismatch": "Term `{term}` has type `{got}` but the goal is `{want}`.",
    "ch.build.apply_not_implication": "`{term}` is not a function - `apply` needs an implication.",
    "ch.build.unknown_term": "I do not know term `{term}` in the current context.",
    "ch.build.assumption_no_match": "No hypothesis matches the goal `{target}`.",
    "ch.explore.unknown_slug": "Unknown entry `{slug}`. Type `ch explore` to see the catalogue.",
    "ch.explore.no_tactics": "No tactic steps for this entry.",
}


def _t(key: str, **kwargs: object) -> str:
    msg = MSG.get(key, key)
    try:
        return msg.format(**kwargs)
    except Exception:
        return msg


_HELP_BODY = (
    "A bridge between lambda-calculus, types, Lean and tactics.\n"
    "\n"
    "Sub-commands:\n"
    "  ch term <lambda>         - infer type + proof interpretation\n"
    "  ch type <T>              - find a lambda-term inhabiting type T\n"
    "  ch lib [name]            - catalogue of combinators (id, K, S, B, C, Y, ...)\n"
    "  ch lean <lambda>         - generate a Lean 4 theorem for lambda\n"
    "  ch from-lean <expr>      - parse a Lean term -> lambda + type\n"
    "  ch tactic [name]         - encyclopedia of 22 Lean tactics\n"
    "  ch build <T>             - interactive proof builder (step by step)\n"
    "  ch verify <theorem>      - check a theorem in Lean (LSP / inline)\n"
    "  ch explore [slug]        - interactive walker over the theorem catalogue\n"
)

_BROWSER_NOTE = (
    "Browser build: `ch verify` and `ch explore --live` need a local Lean "
    "toolchain; here they print a notice (verify adds a Live Lean link)."
)


# ---------------------------------------------------------------------------
# Small rendering helpers
# ---------------------------------------------------------------------------


def _kv_rows(pairs: List[Tuple[str, str]]) -> List[str]:
    """Aligned ``label: value`` rows (Rich ``Table.grid`` lookalike)."""
    width = max((A.display_width(label) for label, _ in pairs), default=0)
    rows = []
    for label, value in pairs:
        pad = " " * (width - A.display_width(label))
        rows.append(A.dim(label + ":") + pad + "  " + value)
    return rows


def _panel(rows: List[str], title: str, border_fn=A.magenta) -> List[str]:
    return A.box(rows, title=A.bold(title), border_fn=border_fn, pad_x=1)


def _code_rows(code: str) -> List[str]:
    return [A.cyan(line) for line in code.splitlines()]


def _columns(header: List[str], rows: List[List[str]], styles=None) -> List[str]:
    """Simple aligned columns; ``styles`` are per-column colour functions."""
    styles = styles or [None] * len(header)
    plain = [header] + rows
    widths = [
        max(A.display_width(r[i]) for r in plain) for i in range(len(header))
    ]

    def fmt(row: List[str], is_header: bool) -> str:
        cells = []
        for i, cell in enumerate(row):
            pad = " " * (widths[i] - A.display_width(cell))
            if is_header:
                cells.append(A.bold(cell) + pad)
            else:
                style = styles[i]
                cells.append((style(cell) if style else cell) + pad)
        return "  " + "  ".join(cells).rstrip()

    out = [fmt(header, True)]
    out.extend(fmt(r, False) for r in rows)
    return out


def _live_lean_url(code: str) -> str:
    """A live.lean-lang.org link that opens the Lean 4 web editor with this code."""
    return "https://live.lean-lang.org/#code=" + urllib.parse.quote(code, safe="")


# ---------------------------------------------------------------------------
# Flag helpers (verbatim desktop ports)
# ---------------------------------------------------------------------------


def _split_flags(args: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """Very small splitter: ``--foo=bar`` and ``--foo bar`` -> dict."""
    pos: List[str] = []
    flags: Dict[str, str] = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            if "=" in a:
                k, v = a[2:].split("=", 1)
                flags[k] = v
            else:
                key = a[2:]
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    flags[key] = args[i + 1]
                    i += 1
                else:
                    flags[key] = "1"
        else:
            pos.append(a)
        i += 1
    return pos, flags


_RAW_SUBS = {"term", "lean", "type", "build", "verify", "from-lean", "fromlean"}


def _split_command_args(args: str, sub: str) -> List[str]:
    """Sub-commands taking one big raw block (a lambda or a type) keep the
    body as a single string with trailing ``--flags`` peeled off; everything
    else goes through shlex."""
    if sub in _RAW_SUBS:
        tokens = args.split()
        flags: List[str] = []
        i = len(tokens) - 1
        # Greedily collect flags from the end: --key=val and `--depth 8`.
        while i >= 0:
            tok = tokens[i]
            if tok.startswith("--"):
                flags.insert(0, tok)
                i -= 1
            elif (
                i >= 1
                and tokens[i - 1].startswith("--")
                and "=" not in tokens[i - 1]
            ):
                flags.insert(0, tok)
                flags.insert(0, tokens[i - 1])
                i -= 2
            else:
                break
        body = tokens[: i + 1]
        body_str = " ".join(body)
        # Strip one surrounding quote pair (`ch type 'P -> P'`).
        if (
            len(body_str) >= 2
            and body_str[0] == body_str[-1]
            and body_str[0] in ('"', "'")
        ):
            body_str = body_str[1:-1]
        result: List[str] = [body_str] if body_str else []
        result.extend(flags)
        return result
    try:
        return shlex.split(args)
    except ValueError:
        return args.split()


# ---------------------------------------------------------------------------
# Tier 1: term, lean, lib
# ---------------------------------------------------------------------------


def _cmd_term(args: List[str]) -> str:
    if not args:
        return A.yellow(_t("ch.term.usage"))
    src = args[0] if not args[0].startswith("--") else " ".join(
        a for a in args if not a.startswith("--")
    )
    if not src:
        return A.yellow(_t("ch.term.usage"))
    try:
        term = parse(src)
    except ParseError as e:
        return A.red(_t("ch.term.parse_error", error=e))
    try:
        ty = infer(term)
    except STLCTypeError as e:
        return A.yellow(_t("ch.term.untypable", error=e))
    fv = ", ".join(sorted(free_vars(term))) or "-"
    rows = _kv_rows([
        ("Term", A.cyan(pretty(term))),
        ("Type", A.yellow(pretty_type(ty))),
        ("Free variables", fv),
        ("Proof of", _t("ch.term.proof_interpretation", prop=pretty_type(ty))),
    ])
    return A.lines(*_panel(rows, "lambda-term + type"))


def _cmd_lean(args: List[str]) -> str:
    pos, flags = _split_flags(args)
    if not pos or not pos[0].strip():
        return A.yellow(_t("ch.lean.usage"))
    src = pos[0]
    name = flags.get("name", "ch_proof")
    try:
        term = parse(src)
    except ParseError as e:
        return A.red(_t("ch.lean.parse_error", error=e))
    try:
        ty = infer(term)
    except STLCTypeError as e:
        return A.yellow(_t("ch.lean.untypable", error=e))
    code = lambda_to_lean(term, ty, name=name)
    out = _panel(_code_rows(code), "Lean 4 theorem")
    out.append(A.dim("▶ run it in Live Lean (click / open):"))
    out.append(A.blue(_live_lean_url(code)))
    return A.lines(*out)


def _cmd_lib(args: List[str]) -> str:
    if not args:
        return _show_library_table()
    name = args[0]
    entry = data_ch_library.lookup(name)
    if entry is None:
        return A.yellow(_t("ch.lib.unknown", name=name))
    return _show_library_entry(entry)


def _show_library_table() -> str:
    rows = [A.bold(A.magenta("Combinator catalogue")), ""]
    table_rows = []
    descs = []
    for name in data_ch_library.canonical_names():
        c = data_ch_library.LIBRARY[name]
        ty = c["type_str"] or _t("ch.lib.untypeable")
        table_rows.append([
            c["name"], ", ".join(c["aliases"]) or "-", c["lambda_src"], ty,
        ])
        descs.append(c["description"])
    cols = _columns(
        ["Name", "Aliases", "lambda-term", "Type"],
        table_rows,
        styles=[A.green, A.dim, A.cyan, A.yellow],
    )
    rows.append(cols[0])
    for line, desc in zip(cols[1:], descs):
        rows.append(line)
        rows.append("      " + A.dim(desc))
    rows.append(A.dim("Type `ch lib <name>` for the full card of one combinator."))
    return A.lines(*rows)


def _show_library_entry(c: dict) -> str:
    pairs = [
        ("lambda", A.cyan(c["lambda_src"])),
        ("Type", A.yellow(c["type_str"] or _t("ch.lib.untypeable"))),
        ("Lean", A.cyan(c["lean_src"])),
    ]
    if c["aliases"]:
        pairs.append(("Aliases", ", ".join(c["aliases"])))
    rows = _kv_rows(pairs)
    rows.append("")
    rows.append(c["description"])
    return A.lines(*_panel(rows, f"Combinator {c['name']}"))


# ---------------------------------------------------------------------------
# Tier 2: type (proof search), from-lean
# ---------------------------------------------------------------------------


def _cmd_type(args: List[str]) -> str:
    if not args:
        return A.yellow(_t("ch.type.usage"))
    pos, flags = _split_flags(args)
    if not pos or not pos[0].strip():
        return A.yellow(_t("ch.type.usage"))
    src = pos[0]
    try:
        depth = int(flags.get("depth", "8"))
    except ValueError:
        return A.red("Error: --depth must be an integer.")
    try:
        ty = parse_type(src)
    except ValueError as e:
        return A.red(_t("ch.type.parse_error", error=e))
    term = find_inhabitant(ty, depth=depth)
    if term is None:
        return A.yellow(_t("ch.type.not_inhabited", type=pretty_type(ty)))
    lean_code = lambda_to_lean(term, ty)
    rows = _kv_rows([
        ("Goal", A.yellow(pretty_type(ty))),
        ("Lambda-term", A.cyan(pretty(term))),
    ])
    out = _panel(rows, "Found proof")
    out.extend(_panel(_code_rows(lean_code), "Lean", border_fn=A.dim))
    out.append(A.blue(_live_lean_url(lean_code)))
    return A.lines(*out)


def _cmd_from_lean(args: List[str]) -> str:
    if not args or not args[0].strip():
        return A.yellow(_t("ch.from_lean.usage"))
    src = args[0]
    try:
        term, ty = lean_to_lambda(src)
    except LeanParseError as e:
        return A.red(_t("ch.from_lean.parse_error", error=e))
    except STLCTypeError as e:
        return A.yellow(_t("ch.from_lean.untypable", error=e))
    rows = _kv_rows([
        ("Lean", A.cyan(src)),
        ("Lambda-term", A.cyan(pretty(term))),
        ("Type", A.yellow(pretty_type(ty))),
    ])
    return A.lines(*_panel(rows, "Lean -> lambda"))


# ---------------------------------------------------------------------------
# Tier 3: tactic encyclopedia
# ---------------------------------------------------------------------------


def _cmd_tactic(args: List[str]) -> str:
    if not args:
        return _show_tactic_table()
    name = args[0]
    entry = data_ch_tactics.lookup(name)
    if entry is None:
        return A.yellow(_t("ch.tactic.unknown", name=name))
    return _show_tactic_entry(entry)


def _show_tactic_table() -> str:
    rows = [A.bold(A.magenta(_t("ch.tactic.list_title"))), ""]
    table_rows = [
        [entry["name"], entry["summary"]]
        for entry in (data_ch_tactics.lookup(n) for n in data_ch_tactics.names())
    ]
    rows.extend(_columns(
        ["Tactic", "Short description"],
        table_rows,
        styles=[A.green, None],
    ))
    rows.append(A.dim("Type `ch tactic <name>` for the full card."))
    return A.lines(*rows)


def _show_tactic_entry(entry: dict) -> str:
    rows = _kv_rows([
        ("Summary", entry["summary"]),
        ("On the lambda-term", entry["lambda_effect"]),
        ("On the goal", entry["goal_effect"]),
        ("When to apply", entry["when"]),
        ("Example - goal", A.yellow(entry["example_goal"])),
        ("After the tactic", A.green(entry["example_after"])),
    ])
    return A.lines(*_panel(rows, f"Tactic {entry['name']}"))


# ---------------------------------------------------------------------------
# Tier 4: build (interactive via state), verify (Lean-only notice)
# ---------------------------------------------------------------------------


def _cmd_build(args: List[str], state: dict) -> str:
    pos, _flags = _split_flags(args)
    if not pos or not pos[0].strip():
        return A.yellow(_t("ch.build.usage"))
    type_src = pos[0]
    try:
        target = parse_type(type_src)
    except ValueError as e:
        return A.red(_t("ch.build.parse_error", error=e))
    build_state = ch_builder.start(target)
    state[_BUILD_KEY] = build_state
    state[_BUILD_TARGET_KEY] = target
    state[_INTERACTIVE_KEY] = True
    rows = _build_show_state(build_state)
    rows.append(A.dim(_t("ch.build.tactics_hint")))
    rows.append(A.dim("[ch.build] enter a tactic:"))
    return A.lines(*rows)


def _build_show_state(build_state: "ch_builder.ProofState") -> List[str]:
    if build_state.is_done():
        return []
    out: List[str] = []
    total = len(build_state.goals)
    for idx, goal in enumerate(build_state.goals, start=1):
        ctx = ", ".join(f"{n} : {pretty_type(ty)}" for n, ty in goal.context)
        if not ctx:
            ctx = "(empty)"
        pairs = [
            ("Context", ctx),
            ("Target", A.yellow(pretty_type(goal.target))),
        ]
        if idx == 1:
            pairs.append(("Term", A.cyan(build_state.partial_str())))
        out.extend(_panel(_kv_rows(pairs), f"Goal {idx}/{total}"))
    return out


def _build_show_tactics_reference() -> str:
    """Inside ``ch build``: cheat sheet of the tactics the builder accepts."""
    available = ["intro", "intros", "exact", "apply", "refine", "assumption"]
    meta = [
        ("hint", "Suggests the next step (proof search)."),
        ("undo", "Undo the last tactic."),
        ("done", "Finish (when all goals are closed)."),
        ("quit / q", "Leave the builder."),
        ("?", "Show the current proof state."),
        ("t / tactics", "Show this cheat sheet."),
    ]
    table_rows: List[List[str]] = []
    for name in available:
        entry = data_ch_tactics.lookup(name)
        if entry is None:
            table_rows.append([name, "(no encyclopedia entry)", "—", "—"])
            continue
        table_rows.append([
            name,
            entry["summary"],
            entry["example_goal"] or "—",
            entry["example_after"] or "—",
        ])
    for name, desc in meta:
        table_rows.append([name, desc, "—", "—"])
    rows = _columns(
        ["Tactic", "What it does", "Example goal", "After tactic"],
        table_rows,
        styles=[A.green, None, A.dim, A.dim],
    )
    return A.lines(*_panel(rows, "Cheat sheet: builder tactic syntax"))


def _build_finish(build_state: "ch_builder.ProofState", state: dict) -> str:
    target = state.pop(_BUILD_TARGET_KEY, None)
    state.pop(_BUILD_KEY, None)
    state.pop(_INTERACTIVE_KEY, None)
    rows = [A.green(_t("ch.build.no_more_goals"))]
    rows.append(A.dim("Related KB: `kb curry-howard`"))
    final_term = build_state.final_term()
    if final_term is not None:
        try:
            ty = infer(final_term)
        except STLCTypeError:
            ty = target
        lean_code = lambda_to_lean(final_term, ty)
        rows.extend(_panel(
            _kv_rows([("Final lambda-term", A.cyan(pretty(final_term)))]),
            "Proof builder",
        ))
        rows.extend(_panel(_code_rows(lean_code), "Lean theorem", border_fn=A.dim))
        rows.append(A.blue(_live_lean_url(lean_code)))
    return A.lines(*rows)


def _build_input(line: str, state: dict) -> str:
    """One line of builder interaction (the desktop's nested prompt loop)."""
    build_state: "ch_builder.ProofState" = state[_BUILD_KEY]
    line = (line or "").strip()
    if not line:
        return ""
    if line in ("quit", "exit", "q"):
        state.pop(_BUILD_KEY, None)
        state.pop(_BUILD_TARGET_KEY, None)
        state.pop(_INTERACTIVE_KEY, None)
        return A.dim(_t("ch.build.bye"))
    if line in ("done", "finish"):
        if not build_state.is_done():
            return A.yellow(_t("ch.build.done_without_close"))
        return _build_finish(build_state, state)
    if line == "undo":
        try:
            build_state = ch_builder.undo(build_state)
        except ch_builder.TacticError as e:
            return A.yellow(_t(e.message_key, **e.format_args))
        state[_BUILD_KEY] = build_state
        rows = [A.dim(_t("ch.build.undo_done"))]
        rows.extend(_build_show_state(build_state))
        return A.lines(*rows)
    if line == "hint":
        hint = ch_builder.hint(build_state)
        if hint is None:
            return A.dim(_t("ch.build.hint_none"))
        return A.green(_t("ch.build.hint_suggest", term=hint))
    if line in ("t", "tactics", ":t"):
        return _build_show_tactics_reference()
    if line == "?":
        return A.lines(*_build_show_state(build_state))
    # A tactic: name [args...]
    parts = line.split(maxsplit=1)
    tac = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    try:
        build_state = ch_builder.apply_tactic(build_state, tac, rest)
    except ch_builder.TacticError as e:
        msg = _t(e.message_key, **e.format_args)
        return A.yellow(_t("ch.build.tactic_error", error=msg))
    state[_BUILD_KEY] = build_state
    if build_state.is_done():
        return _build_finish(build_state, state)
    return A.lines(*_build_show_state(build_state))


def _cmd_verify(args: List[str]) -> str:
    pos, _flags = _split_flags(args)
    if not pos or not pos[0].strip():
        return A.yellow("Usage: ch verify <theorem-string> [--backend server|inline|auto].")
    src = pos[0]
    return A.lines(
        A.yellow("ch verify needs a local Lean toolchain (lake) — not available in the browser build."),
        A.dim("▶ check it in Live Lean instead (click / open):"),
        A.blue(_live_lean_url(src)),
    )


# ---------------------------------------------------------------------------
# Tier 5: explore (static catalogue browser)
# ---------------------------------------------------------------------------


_EXPLORE_BY_SLUG = {thm["id"]: thm for thm in data_ch_explore.THEOREMS}


def _tree_children(node: dict) -> List[dict]:
    kind = node["kind"]
    if kind == "lam":
        return [node["body"]]
    if kind == "app":
        return [node["fn"], node["arg"]]
    if kind == "let":
        return [node["value"], node["body"]]
    if kind == "match":
        return list(node.get("arms", []))
    return []


def _tree_label(node: dict, index: int) -> str:
    """One-line node label (mirrors the desktop ``_node_label``)."""
    idx = A.dim(f"[{index}] ")
    kind = node["kind"]
    if kind == "lam":
        binder = node.get("binder") or "_"
        open_b, close_b = ("{", "}") if node.get("implicit") else ("(", ")")
        text = A.magenta("λ") + A.dim(" " + open_b) + A.cyan(binder)
        if node.get("binder_type"):
            text += A.dim(" : ") + A.yellow(node["binder_type"])
        return idx + text + A.dim(close_b)
    if kind == "app":
        return idx + A.magenta("@") + A.dim(" application")
    if kind == "var":
        text = A.cyan(node.get("name") or "?")
        if node.get("type"):
            text += A.dim(" : ") + A.yellow(node["type"])
        return idx + text
    if kind == "const":
        text = A.green(node.get("name") or "?")
        if node.get("type"):
            text += A.dim(" : ") + A.yellow(node["type"])
        return idx + text
    if kind == "let":
        text = A.magenta("let ") + A.cyan(node.get("binder") or "_")
        if node.get("binder_type"):
            text += A.dim(" : ") + A.yellow(node["binder_type"])
        return idx + text
    if kind == "match":
        return idx + A.magenta("match ") + A.cyan(node.get("name") or "_")
    if kind == "raw":
        return idx + A.red(node.get("name") or "?") + "  " + A.dim("(unparsed)")
    return idx + A.yellow(f"<{kind}>")


def _tree_lines(root: dict) -> List[str]:
    """ASCII rendering of the proof-term tree with DFS pre-order indices."""
    counter = [0]
    out: List[str] = []

    def walk(node: dict, prefix: str, tail: Optional[bool]) -> None:
        index = counter[0]
        counter[0] += 1
        if tail is None:
            out.append(_tree_label(node, index))
            child_prefix = ""
        else:
            branch = "└── " if tail else "├── "
            out.append(prefix + A.dim(branch) + _tree_label(node, index))
            child_prefix = prefix + ("    " if tail else A.dim("│") + "   ")
        children = _tree_children(node)
        for i, child in enumerate(children):
            walk(child, child_prefix, i == len(children) - 1)

    walk(root, "", None)
    return out


def _format_path(path: List[int]) -> str:
    if not path:
        return "[]"
    return "[" + ".".join(str(i) for i in path) + "]"


def _explore_catalog() -> str:
    rows = [A.bold(A.magenta("ch explore catalogue")), ""]
    table_rows = [
        [thm["id"], thm["title"], thm["type_signature"], "*" * max(1, thm["difficulty"])]
        for thm in data_ch_explore.THEOREMS
    ]
    rows.extend(_columns(
        ["Slug", "Title", "Type", "Diff."],
        table_rows,
        styles=[A.green, None, A.yellow, A.dim],
    ))
    rows.append(A.dim("Type `ch explore <slug>` for the proof-term card."))
    return A.lines(*rows)


def _explore_entry(thm: dict) -> str:
    star = "*" * max(1, thm["difficulty"])
    overview = _kv_rows([
        ("Id", A.green(thm["id"])),
        ("Title", thm["title"]),
        ("Difficulty", star),
        ("Type", A.yellow(thm["type_signature"])),
        ("Summary", thm["summary"]),
    ])
    overview.append("")
    overview.append(A.dim("Lean source (tactic):"))
    overview.extend(_code_rows(thm["lean_source"]))
    out = _panel(overview, f"ch explore - {thm['id']}")

    out.extend(_panel(_tree_lines(thm["tree"]), "Proof term", border_fn=A.dim))

    steps = thm["tactic_steps"]
    if steps:
        mapping = _columns(
            ["L", "Tactic", "Path", "What it does"],
            [
                [str(s["line"]), s["tactic"], _format_path(s["subterm_path"]), s["narrative"]]
                for s in steps
            ],
            styles=[A.dim, A.green, A.yellow, None],
        )
    else:
        mapping = [A.dim(_t("ch.explore.no_tactics"))]
    out.extend(_panel(mapping, "Tactic -> subterm mapping", border_fn=A.dim))

    lam_rows = [A.cyan(thm["lambda_equivalent"]), "", A.dim(thm["lambda_intuition"])]
    out.extend(_panel(lam_rows, "Pure lambda equivalent", border_fn=A.dim))
    out.append(A.dim(
        "The desktop keyboard walker (collapse/expand, math view, live mode) "
        "is desktop-only; this card shows the full tree."
    ))
    return A.lines(*out)


def _cmd_explore(args: List[str]) -> str:
    pos, flags = _split_flags(args)
    if "live" in flags:
        return A.yellow(
            "ch explore --live compiles Lean via a local `lake` toolchain — "
            "not available in the browser build."
        )
    if not pos:
        return _explore_catalog()
    slug = pos[0].strip()
    thm = _EXPLORE_BY_SLUG.get(slug)
    if thm is None:
        return A.yellow(_t("ch.explore.unknown_slug", slug=slug))
    return _explore_entry(thm)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def _show_overview() -> str:
    rows = _HELP_BODY.rstrip("\n").splitlines()
    rows.append("")
    rows.append(A.dim(_BROWSER_NOTE))
    return A.lines(*_panel(rows, _t("ch.help.title")))


def _handle(arg: str, state: dict) -> str:
    if state.get(_BUILD_KEY) is not None:
        return _build_input(arg, state)
    args = (arg or "").strip()
    if len(args) > MAX_INPUT:
        return A.red(f"Input is too long (max {MAX_INPUT} characters).")
    if not args:
        return _show_overview()
    sp = args.split(maxsplit=1)
    sub = sp[0]
    rest_raw = sp[1] if len(sp) > 1 else ""
    rest = _split_command_args(rest_raw, sub)
    if sub == "term":
        return _cmd_term(rest)
    if sub == "lean":
        return _cmd_lean(rest)
    if sub == "lib":
        return _cmd_lib(rest)
    if sub == "type":
        return _cmd_type(rest)
    if sub in ("from-lean", "fromlean"):
        return _cmd_from_lean(rest)
    if sub == "tactic":
        return _cmd_tactic(rest)
    if sub == "build":
        return _cmd_build(rest, state)
    if sub == "verify":
        return _cmd_verify(rest)
    if sub == "explore":
        return _cmd_explore(rest)
    return A.yellow(_t("ch.unknown", sub=sub))


def handle(arg: str, state: dict) -> str:
    """Entry point for the browser driver: ``ch <sub> [args]``."""
    try:
        return _handle(arg, state)
    except RecursionError:
        return A.red("The term is too deeply nested for the browser sandbox.")
    except Exception as exc:  # keep the REPL alive while surfacing the error
        return A.red(f"{type(exc).__name__}: {exc}")
