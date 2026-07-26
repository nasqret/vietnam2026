"""Interactive ``pa prove`` session and surface tactic language.

This module copies Lambda Lab's post-audit grammar rules:

* a live proof owns the complete input line before ordinary driver dispatch;
* ``qed``/``abort`` aliases act only as complete, case-sensitive lines;
* an inactive ``pa prove`` argument containing ``->`` or ``→`` is always a
  proposition, never an informational subcommand.

The :class:`ProofSession` object is the security boundary between UI and the
untrusted tactic state.  It retains the original parsed theorem and an exact
Boolean classical-mode authority independently of :class:`ProofState`.  Every
QED passes those owner-held values explicitly to ``checked_final``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from ..engine.search import auto
from ..engine.state import ProofState, proof_size, start
from ..engine.tacticals import all_goals, first, focus, orelse, repeat, then
from ..engine.tactics import (
    TACTIC_NAMES,
    InvalidProof,
    Tactic,
    TacticError,
    apply_tactic,
    checked_final,
    hint,
    logic_banner,
    set_classical_mode,
)
from ..engine.trace import TraceLogger
from ..kernel.formulas import ParseError, Formula, parse_formula_with_names, pretty_formula
from .panels import NL, collect_meta_ids, render_certificate, render_state


MAX_INPUT = 4_000
KEY_SESSION = "pa.prove.session"

_QED_WORDS = ("qed", "done", "finish")
_ABORT_WORDS = ("abort", "quit", "exit", "q")
_SESSION_ONLY_WORDS = set(_QED_WORDS) | set(_ABORT_WORDS) | set(TACTIC_NAMES) | {
    "?",
    ":t",
    "all_goals",
    "auto",
    "classical",
    "focus",
    "first",
    "help",
    "hint",
    "repeat",
    "t",
    "tactics",
    "undo",
}


@dataclass(frozen=True, slots=True)
class ProofSession:
    """The one owner of an interactive theorem-proving session."""

    state: ProofState
    original_target: Formula
    original_names: tuple[str, ...]
    target_source: str
    classical: bool
    trace: TraceLogger
    meta_names: tuple[tuple[int, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.state) is not ProofState:
            raise TypeError("a proof session needs an exact ProofState")
        if not isinstance(self.original_target, Formula):
            raise TypeError("a proof session needs an original PA formula")
        if type(self.classical) is not bool:
            raise TypeError("a proof session's classical mode must be a Boolean")
        if type(self.trace) is not TraceLogger:
            raise TypeError("a proof session needs a TraceLogger")
        if not all(
            type(meta_id) is int and isinstance(name, str)
            for meta_id, name in self.meta_names
        ):
            raise TypeError("proof-session metavariable names must be integer/text pairs")


def _lines(*rows: str) -> str:
    return NL.join(rows)


def get_owner(shared: dict) -> ProofSession | None:
    """Return the active exact owner, or ``None`` for malformed/stale data."""

    owner = shared.get(KEY_SESSION)
    return owner if type(owner) is ProofSession else None


def is_active(shared: dict) -> bool:
    return get_owner(shared) is not None


def _put_owner(shared: dict, owner: ProofSession) -> None:
    shared[KEY_SESSION] = owner


def _clear(shared: dict) -> None:
    shared.pop(KEY_SESSION, None)


def _sync_meta_names(owner: ProofSession) -> ProofSession:
    """Extend, but never renumber, the owner's session-wide meta aliases."""

    aliases = dict(owner.meta_names)
    for meta_id in collect_meta_ids(owner.state):
        if meta_id not in aliases:
            aliases[meta_id] = f"?t{len(aliases) + 1}"
    entries = tuple(aliases.items())
    return owner if entries == owner.meta_names else replace(owner, meta_names=entries)


def _panel(owner: ProofSession) -> str:
    owner = _sync_meta_names(owner)
    return render_state(owner.state, meta_names=dict(owner.meta_names))


def usage() -> str:
    return _lines(
        "Peano Lab proof builder",
        "",
        "  pa prove <formula>",
        "",
        "Each following line is a tactic. The partial kernel certificate grows",
        "hole by hole, but QED trusts only the independent checker.",
        "",
        "  Tactics: intro · apply · exact · assumption · split · left · right",
        "           cases · exfalso · exists · specialize · forall_elim",
        "           refl · symm · trans · congr · rewrite · induction · simp",
        "  Language: t1; t2 · t1 <|> t2 · repeat t · first [t1 | t2]",
        "            all_goals t · focus n t · auto [depth]",
        "  Session: hint · undo · ? · classical on|off · qed · abort",
        "",
        "qed / abort and their aliases act only when typed alone on the line.",
        "Try: pa prove forall n. 0 + n = n",
    )


def tactic_help() -> str:
    return _lines(
        usage(),
        "",
        "Examples",
        "  induction n; simp",
        "  first [assumption | refl]",
        "  rewrite <- h at h2",
        "  focus 2 simp",
        "",
        "Logic starts intuitionistic. `classical on` explicitly authorizes DNE",
        "for later `apply DNE` / `auto` steps and for the final kernel check.",
    )


def _start_session(source: str, shared: dict) -> str:
    if len(source) > MAX_INPUT:
        return f"Input is too long (max {MAX_INPUT} characters)."
    try:
        target, names = parse_formula_with_names(source)
    except (ParseError, ValueError) as exc:
        return f"Parse error: {exc}"
    state = start(target, names)
    owner = ProofSession(
        state=state,
        original_target=target,
        original_names=names,
        target_source=source,
        classical=False,
        trace=TraceLogger(),
    )
    owner = _sync_meta_names(owner)
    _put_owner(shared, owner)
    return _lines(
        "Peano Lab proof",
        f"Theorem: {pretty_formula(target, list(names))}",
        logic_banner(False),
        "",
        _panel(owner),
        "",
        "Type `help` for tactics; `qed` checks; `abort` leaves.",
    )


def _closed_panel(owner: ProofSession) -> str:
    return _lines(
        _panel(owner),
        "",
        "All engine goals are closed. Type `qed` for an independent kernel check,",
        "or `undo` to reopen the preceding state.",
    )


def _finish_session(shared: dict, owner: ProofSession) -> str:
    """Attempt QED unconditionally; only a checked success ends the session."""

    try:
        certificate = checked_final(
            owner.state,
            owner.original_target,
            classical=owner.classical,
        )
    except InvalidProof as exc:
        return _lines(
            f"QED check failed: {exc}",
            "The proof session is still active: `?` shows it, `undo` steps back,",
            "and `abort` leaves without claiming a theorem.",
        )
    owner.trace.footer(
        qed=True,
        theorem=owner.original_target,
        proof_size=proof_size(certificate),
        names=owner.original_names,
    )
    theorem = pretty_formula(owner.original_target, list(owner.original_names))
    certificate_text = render_certificate(certificate, owner.original_names)
    mode = logic_banner(owner.classical)
    _clear(shared)
    return _lines(
        "No open goals. QED.",
        f"Theorem: {theorem}",
        f"Certificate: {certificate_text}",
        f"Checked under: {mode}",
    )


def _hint_text(owner: ProofSession) -> str:
    status, suggestion = hint(owner.state)
    if status == "done":
        return "No open goals. Type `qed` for the independent kernel check."
    if status == "found":
        return f"Hint (found): try `{suggestion}`."
    if status == "limit":
        return "Hint (limit): unresolved terms or the inspection budget prevent a verdict."
    return "Hint (none): no supported immediate move was found; this is not an unprovability claim."


def _scan_split(source: str, separator: str) -> list[str]:
    """Split a tactical separator only outside term/bracket grouping."""

    parts: list[str] = []
    start_at = 0
    round_depth = 0
    square_depth = 0
    index = 0
    while index < len(source):
        char = source[index]
        if char == "(":
            round_depth += 1
        elif char == ")":
            round_depth -= 1
        elif char == "[":
            square_depth += 1
        elif char == "]":
            square_depth -= 1
        if round_depth < 0 or square_depth < 0:
            raise TacticError("unbalanced grouping in tactical command.")
        if round_depth == square_depth == 0 and source.startswith(separator, index):
            parts.append(source[start_at:index].strip())
            index += len(separator)
            start_at = index
            continue
        index += 1
    if round_depth or square_depth:
        raise TacticError("unbalanced grouping in tactical command.")
    parts.append(source[start_at:].strip())
    if any(not part for part in parts):
        raise TacticError(f"`{separator}` needs a tactic on both sides.")
    return parts


def _strip_group(source: str) -> str:
    """Remove redundant outer parentheses that enclose the whole tactic."""

    if not (source.startswith("(") and source.endswith(")")):
        return source
    depth = 0
    for index, char in enumerate(source):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and index != len(source) - 1:
                return source
        if depth < 0:
            raise TacticError("unbalanced grouping in tactical command.")
    if depth:
        raise TacticError("unbalanced grouping in tactical command.")
    return _strip_group(source[1:-1].strip())


def _first_items(source: str) -> list[str]:
    """Parse ``first [a | b]`` with comma and ``<|>`` aliases."""

    items: list[str] = []
    start_at = 0
    round_depth = 0
    square_depth = 0
    index = 0
    while index < len(source):
        char = source[index]
        if char == "(":
            round_depth += 1
        elif char == ")":
            round_depth -= 1
        elif char == "[":
            square_depth += 1
        elif char == "]":
            square_depth -= 1
        if round_depth < 0 or square_depth < 0:
            raise TacticError("unbalanced grouping in `first`.")
        separator_length = 0
        if round_depth == square_depth == 0:
            if source.startswith("<|>", index):
                separator_length = 3
            elif char in {"|", ","}:
                separator_length = 1
        if separator_length:
            items.append(source[start_at:index].strip())
            index += separator_length
            start_at = index
            continue
        index += 1
    if round_depth or square_depth:
        raise TacticError("unbalanced grouping in `first`.")
    items.append(source[start_at:].strip())
    if any(not item for item in items):
        raise TacticError("`first` needs non-empty tactic choices.")
    return items


def _primitive(name: str, args: str, classical: bool) -> Tactic:
    if name == "undo":
        raise TacticError("`undo` is a session command and cannot be nested in a tactical.")
    if name == "classical":
        raise TacticError("`classical` is a session command and cannot be nested in a tactical.")

    def run(state: ProofState, extra: str = "") -> ProofState:
        if extra.strip():
            raise TacticError("an assembled surface tactic takes no extra arguments.")
        if name == "auto":
            return auto(state, args, classical=classical)
        return apply_tactic(state, name, args, classical=classical)

    return run


def _compile(source: str, classical: bool) -> tuple[Tactic, bool]:
    """Compile the deliberately small surface grammar into M4 combinators."""

    source = _strip_group(source.strip())
    if not source:
        raise TacticError("expected a tactic.")

    alternatives = _scan_split(source, "<|>")
    if len(alternatives) > 1:
        compiled = [_compile(item, classical)[0] for item in alternatives]
        result = compiled[0]
        for choice in compiled[1:]:
            result = orelse(result, choice)
        return result, True

    sequence = _scan_split(source, ";")
    if len(sequence) > 1:
        compiled = [_compile(item, classical)[0] for item in sequence]
        result = compiled[0]
        for following in compiled[1:]:
            result = then(result, following)
        return result, True

    if re.match(r"^repeat(?:\s|$)", source):
        child = source[len("repeat") :].strip()
        if not child:
            raise TacticError("syntax: `repeat <tactic>`.")
        return repeat(_compile(child, classical)[0]), True

    if re.match(r"^all_goals(?:\s|$)", source):
        child = source[len("all_goals") :].strip()
        if not child:
            raise TacticError("syntax: `all_goals <tactic>`.")
        return all_goals(_compile(child, classical)[0]), True

    if re.match(r"^focus(?:\s|$)", source):
        match = re.fullmatch(r"focus\s+(\d+)\s+(.+)", source, re.DOTALL)
        if match is None or int(match.group(1)) < 1:
            raise TacticError("syntax: `focus <positive-goal-number> <tactic>`.")
        return focus(int(match.group(1)), _compile(match.group(2), classical)[0]), True

    if re.match(r"^first(?:\s|$)", source):
        match = re.fullmatch(r"first\s*\[(.*)\]", source, re.DOTALL)
        if match is None:
            raise TacticError("syntax: `first [tactic | tactic | ...]`.")
        choices = [_compile(item, classical)[0] for item in _first_items(match.group(1))]
        return first(choices), True

    pieces = source.split(maxsplit=1)
    name = pieces[0]
    args = pieces[1].strip() if len(pieces) > 1 else ""
    return _primitive(name, args, classical), False


def _trace_focus(line: str, state: ProofState) -> int:
    """Return the initial one-based ``focus`` selection as a trace index."""

    try:
        source = _strip_group(line.strip())
    except TacticError:
        return 0
    match = re.match(r"^focus\s+(\d+)(?:\s|$)", source)
    if match is None:
        return 0
    selected = int(match.group(1)) - 1
    return selected if 0 <= selected < len(state.goals) else 0


def _run_surface(owner: ProofSession, line: str) -> ProofSession:
    """Run one primitive, tactical, simp, or auto with one public trace path."""

    pieces = line.split(maxsplit=1)
    name = pieces[0]
    args = pieces[1].strip() if len(pieces) > 1 else ""

    # Primitive commands use the public dispatcher directly.  This includes
    # simp and gives both success and failure exactly one v=1 trace record.
    if name in TACTIC_NAMES and name != "undo" and not any(
        marker in line for marker in (";", "<|>")
    ):
        new_state = apply_tactic(
            owner.state,
            name,
            args,
            trace=owner.trace,
            classical=owner.classical,
        )
        return replace(owner, state=new_state)

    # Auto replays its winning primitive plan through the public dispatcher;
    # those linear primitive records are the useful training transcript.
    if name == "auto" and not any(marker in line for marker in (";", "<|>")):
        new_state = auto(
            owner.state,
            args,
            trace=owner.trace,
            classical=owner.classical,
        )
        return replace(owner, state=new_state)

    before = owner.state
    trace_focus = _trace_focus(line, before)
    try:
        tactical, _ = _compile(line, owner.classical)
        after = tactical(before, "")
    except TacticError as exc:
        owner.trace.failure(before, trace_focus, line, exc)
        raise
    owner.trace.success(before, trace_focus, line, after)
    return replace(owner, state=after)


def _session_line(line: str, shared: dict, owner: ProofSession) -> str:
    line = line.strip()
    if not line:
        return ""
    owner = _sync_meta_names(owner)
    _put_owner(shared, owner)

    # Complete-line, case-sensitive aliases: `qed please`, `QED`, and a term
    # containing one of these words can never close or discard a session.
    if line in _ABORT_WORDS:
        owner.trace.footer(
            qed=False,
            theorem=owner.original_target,
            proof_size=proof_size(owner.state.partial),
            names=owner.original_names,
        )
        _clear(shared)
        return "Proof aborted. No theorem was claimed."
    if line in _QED_WORDS:
        return _finish_session(shared, owner)
    if line == "hint":
        return _hint_text(owner)
    if line == "?":
        return _closed_panel(owner) if owner.state.is_done() else _panel(owner)
    if line in {"t", "tactics", ":t", "help"}:
        return tactic_help()

    pieces = line.split(maxsplit=1)
    command = pieces[0]
    args = pieces[1].strip() if len(pieces) > 1 else ""

    if command in _QED_WORDS or command in _ABORT_WORDS:
        return f"`{command}` acts only when typed alone on the line (got extra input {args!r})."
    nested_pa = re.match(r"^pa\s+prove(?:\s|$)", line, re.IGNORECASE)
    if nested_pa is not None or command.lower() == "prove":
        return _lines(
            "A proof is already in progress.",
            "Finish it with `qed` or leave with `abort` before starting another.",
        )
    if command == "classical":
        try:
            enabled = set_classical_mode(
                owner.classical,
                args,
                state=owner.state,
                trace=owner.trace,
            )
        except TacticError as exc:
            return f"Tactic error: {exc}"
        owner = replace(owner, classical=enabled)
        _put_owner(shared, owner)
        return _lines(logic_banner(enabled), _panel(owner))
    if command == "undo":
        # Undo is intentionally a complete-line tactic with no arguments.
        try:
            new_state = apply_tactic(
                owner.state,
                "undo",
                args,
                trace=owner.trace,
                classical=owner.classical,
            )
        except TacticError as exc:
            return f"Tactic error: {exc}"
        owner = _sync_meta_names(replace(owner, state=new_state))
        _put_owner(shared, owner)
        return _panel(owner)

    try:
        owner = _sync_meta_names(_run_surface(owner, line))
    except TacticError as exc:
        return f"Tactic error: {exc}"
    _put_owner(shared, owner)
    return _closed_panel(owner) if owner.state.is_done() else _panel(owner)


def handle(arg: str, shared: dict) -> str:
    """Handle a ``pa prove`` argument, or a raw line owned by a live proof."""

    arg = (arg or "").strip()
    owner = get_owner(shared)
    if owner is not None:
        return _session_line(arg, shared, owner)

    if not arg or arg == "help":
        return usage()

    # Audit P1.1: arrows make the entire argument a proposition before any
    # informational subcommand is considered.
    has_arrow = "->" in arg or "→" in arg
    if not has_arrow:
        pieces = arg.split(maxsplit=1)
        sub = pieces[0]
        if arg in {"t", "tactics"}:
            return tactic_help()
        if sub in {"tactic", "lib"}:
            return (
                "Use `pa tactic [name]` for the executable M6 encyclopedia."
                if sub == "tactic"
                else "The named theorem library arrives in M7."
            )
        if arg in _SESSION_ONLY_WORDS:
            return _lines(
                "No proof is in progress.",
                "Start one with `pa prove <formula>`.",
            )

    return _start_session(arg, shared)


__all__ = [
    "KEY_SESSION",
    "MAX_INPUT",
    "ProofSession",
    "get_owner",
    "is_active",
    "usage",
    "tactic_help",
    "handle",
]
