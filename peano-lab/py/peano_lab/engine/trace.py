"""Deterministic JSONL traces for tactic applications.

The format is deliberately boring.  It is an interface between the proof
engine and later corpus-building tools, so key order and spelling are part of
the format contract (``docs/PEANO_LAB_DESIGN.md`` section 4).  The logger does
not know about tactics and it never decides whether a proof is valid.

Records are always retained in memory.  A text sink can additionally receive
each line as it is emitted; this is useful for a browser console, a file, or a
batch-search stream.
"""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from copy import deepcopy
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TextIO

from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or, pretty_formula
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero

from .state import MetaVar, metas_in_formula


TRACE_VERSION = 1

# Goal text comes from the canonical printer, not a terminal renderer.  The
# final scrub is defence in depth for user-chosen context names and for callers
# passing an already-rendered goal during data import.
_ANSI_ESCAPE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))"
)


def _without_ansi(text: str) -> str:
    text = _ANSI_ESCAPE.sub("", text).replace("\x1b", "")
    # JSON accepts several invisible control/format characters that are not
    # ANSI escapes (C1 CSI, bidi overrides, zero-width marks, ...).  Preserve
    # their identity as visible ASCII escapes so corpus records remain
    # deterministic, single-line, and safe to inspect in terminals/editors.
    return "".join(
        char
        if unicodedata.category(char) not in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        else (f"\\u{ord(char):04x}" if ord(char) <= 0xFFFF else f"\\U{ord(char):08x}")
        for char in text
    )


def sanitize_trace_text(text: str) -> str:
    """Return the exact safe text representation stored in a trace field."""

    if type(text) is not str:
        raise TypeError("trace text must be a string")
    return _without_ansi(text)


def _meta_aliases(
    formulas: Iterable[Formula], aliases: dict[int, str] | None = None
) -> dict[int, str]:
    aliases = aliases if aliases is not None else {}
    for formula in formulas:
        for meta_id in metas_in_formula(formula):
            if meta_id not in aliases:
                aliases[meta_id] = f"?t{len(aliases) + 1}"
    return aliases


def _pretty_engine_term(
    term: Term, names: list[str], metas: dict[int, str], parent: int = 0
) -> str:
    if type(term) is MetaVar:
        text, level = metas.get(term.id, f"?m{term.id}"), 4
    elif type(term) is Var:
        text = names[term.index] if 0 <= term.index < len(names) else f"#{term.index}"
        level = 4
    elif type(term) is Zero:
        text, level = "0", 4
    elif type(term) is Succ:
        count, tail = 0, term
        while type(tail) is Succ:
            count += 1
            tail = tail.term
        if type(tail) is Zero:
            text, level = str(count), 4
        else:
            text = "S " + _pretty_engine_term(term.term, names, metas, 3)
            level = 3
    elif type(term) in (Add, Mul):
        level = 1 if type(term) is Add else 2
        symbol = "+" if type(term) is Add else "·"
        text = (
            f"{_pretty_engine_term(term.left, names, metas, level)} {symbol} "
            f"{_pretty_engine_term(term.right, names, metas, level + 1)}"
        )
    else:
        raise TypeError("expected a PA term or engine metavariable")
    return f"({text})" if level < parent else text


def _fresh_binder(names: list[str]) -> str:
    used = set(names)
    for candidate in ("x", "y", "z", "n", "m", "k", "i", "j", "u", "v", "w"):
        if candidate not in used:
            return candidate
    index = 0
    while f"x{index}" in used:
        index += 1
    return f"x{index}"


def _pretty_engine_formula(
    formula: Formula, names: list[str], metas: dict[int, str], parent: int = 0
) -> str:
    if type(formula) is Eq:
        text = (
            f"{_pretty_engine_term(formula.left, names, metas)} = "
            f"{_pretty_engine_term(formula.right, names, metas)}"
        )
        level = 5
    elif type(formula) is Bot:
        text, level = "⊥", 5
    elif type(formula) is Imp and type(formula.right) is Bot:
        text = "¬" + _pretty_engine_formula(formula.left, names, metas, 4)
        level = 4
    elif type(formula) in (Imp, And, Or):
        if type(formula) is And:
            level, symbol = 3, "∧"
        elif type(formula) is Or:
            level, symbol = 2, "∨"
        else:
            level, symbol = 1, "→"
        left_parent = level + (1 if type(formula) is Imp else 0)
        right_parent = level if type(formula) is Imp else level + 1
        if type(formula) is Imp and type(formula.right) in (Forall, Exists):
            right_parent = 0
        text = (
            f"{_pretty_engine_formula(formula.left, names, metas, left_parent)} {symbol} "
            f"{_pretty_engine_formula(formula.right, names, metas, right_parent)}"
        )
    elif type(formula) in (Forall, Exists):
        binder = _fresh_binder(names)
        symbol = "∀" if type(formula) is Forall else "∃"
        text = (
            f"{symbol} {binder}. "
            f"{_pretty_engine_formula(formula.body, [binder] + names, metas)}"
        )
        level = 0
    else:
        raise TypeError("expected a PA formula")
    return f"({text})" if level < parent else text


def render_goal(goal: Any, *, meta_names: dict[int, str] | None = None) -> str:
    """Render one goal canonically, with no ANSI control sequences.

    A Peano Lab goal has ``context``, ``target``, and (from M1 onward) an
    optional ``variables`` tuple.  Variables and hypotheses are stored nearest
    binder/newest first for de Bruijn operations, but displayed oldest first.
    Accepting a string is intentional: it lets corpus importers pass canonical
    historical goal text through the same ANSI-free boundary.
    """

    if isinstance(goal, str):
        return _without_ansi(goal)

    try:
        target = goal.target
        context = tuple(goal.context)
    except AttributeError as exc:
        raise TypeError("a trace goal must be goal-like or canonical text") from exc
    if not isinstance(target, Formula):
        raise TypeError("a trace goal target must be a Formula")

    variables = tuple(getattr(goal, "variables", ()))
    if not all(isinstance(name, str) for name in variables):
        raise TypeError("goal variable names must be text")
    names = list(variables)  # index-to-name order for the de Bruijn printer
    formulas = [formula for _, formula in context] + [target]
    meta_names = _meta_aliases(formulas, meta_names)

    def rendered(formula: Formula) -> str:
        # Rigid formulas use the one kernel canonicalizer—including defined
        # sugar such as ≤.  The engine renderer is needed only for MetaVar.
        if not metas_in_formula(formula):
            return pretty_formula(formula, names)
        return _pretty_engine_formula(formula, names, meta_names)

    declarations = [f"{name} : ℕ" for name in reversed(variables)]
    for entry in reversed(context):
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise TypeError("goal context entries must be (name, Formula) pairs")
        name, formula = entry
        if not isinstance(name, str) or not isinstance(formula, Formula):
            raise TypeError("goal context entries must be (name, Formula) pairs")
        declarations.append(f"{name} : {rendered(formula)}")

    target_text = rendered(target)
    prefix = f"{', '.join(declarations)} " if declarations else ""
    return _without_ansi(f"{prefix}⊢ {target_text}")


def render_goals(
    goals_or_state: Any, *, meta_names: dict[int, str] | None = None
) -> list[str]:
    """Return canonical text for a state or an iterable of goals."""

    goals = getattr(goals_or_state, "goals", goals_or_state)
    if isinstance(goals, str):
        raise TypeError("goals must be an iterable, not one goal string")
    try:
        goals = list(goals)
        formulas: list[Formula] = []
        for goal in goals:
            if not isinstance(goal, str):
                formulas.extend(formula for _, formula in goal.context)
                formulas.append(goal.target)
        aliases = _meta_aliases(formulas, meta_names)
        return [render_goal(goal, meta_names=aliases) for goal in goals]
    except TypeError:
        raise
    except Exception as exc:
        raise TypeError("goals must be a state or an iterable of goals") from exc


class TraceLimitError(RuntimeError):
    """A configured trace byte budget was exhausted before publication."""


class TraceLogger:
    """Collect and optionally stream one version-1 JSON object per line.

    ``session_id`` is injectable so tests, examples, and deterministic batch
    jobs need not patch UUID generation.  When omitted, a fresh UUID string is
    used.  Tactic steps are one-based and include failed applications.
    """

    def __init__(
        self,
        sink: TextIO | Callable[[str], object] | None = None,
        *,
        session_id: str | None = None,
        max_bytes: int | None = None,
    ) -> None:
        if session_id is None:
            session_id = str(uuid.uuid4())
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be non-empty text")
        if sink is not None and not callable(sink) and not callable(getattr(sink, "write", None)):
            raise TypeError("sink must have write(text), be callable, or be None")
        if max_bytes is not None and (
            type(max_bytes) is not int or max_bytes <= 0
        ):
            raise ValueError("max_bytes must be a positive integer or None")

        self.session_id = session_id
        self._sink = sink
        self._records: list[dict[str, object]] = []
        self._lines: list[str] = []
        self._next_step = 1
        self._tactic_count = 0
        self._finished = False
        self._meta_names: dict[int, str] = {}
        self._max_bytes = max_bytes
        self._byte_count = 0

    @property
    def records(self) -> tuple[dict[str, object], ...]:
        """Detached copies of emitted records, in emission order.

        The logger is an append-only audit owner.  Returning copies prevents a
        caller that merely consumes a trace from rewriting an earlier record.
        """

        return deepcopy(tuple(self._records))

    @property
    def record_count(self) -> int:
        """Number of records emitted, including a footer when present."""

        return len(self._records)

    @property
    def byte_count(self) -> int:
        """UTF-8 bytes in the complete emitted JSONL stream."""

        return self._byte_count

    @property
    def last_record(self) -> dict[str, object] | None:
        """Return a detached copy of the newest record without copying history."""

        return None if not self._records else deepcopy(self._records[-1])

    def records_since(self, index: int) -> tuple[dict[str, object], ...]:
        """Return detached records from an O(1) append-only checkpoint."""

        if type(index) is not int or not 0 <= index <= len(self._records):
            raise ValueError("trace checkpoint is outside the emitted record range")
        return deepcopy(tuple(self._records[index:]))

    @property
    def tactic_count(self) -> int:
        """Number of successful and failed tactic applications recorded."""

        return self._tactic_count

    def jsonl(self) -> str:
        """Return the complete in-memory JSONL stream (with a final newline)."""

        return "" if not self._lines else "\n".join(self._lines) + "\n"

    def _emit(self, record: dict[str, object]) -> dict[str, object]:
        line = json.dumps(record, ensure_ascii=False)
        line_bytes = len(line.encode("utf-8")) + 1
        if (
            self._max_bytes is not None
            and self._byte_count + line_bytes > self._max_bytes
        ):
            raise TraceLimitError(
                f"trace exceeded its {self._max_bytes}-byte session limit"
            )
        self._records.append(record)
        self._lines.append(line)
        self._byte_count += line_bytes
        if self._sink is not None:
            writer = getattr(self._sink, "write", None)
            if callable(writer):
                writer(line + "\n")
            else:
                self._sink(line + "\n")  # type: ignore[operator]
        return deepcopy(record)

    def record_tactic(
        self,
        goals_before: Any,
        focus: int,
        tactic: str,
        goals_after: Any | None = None,
        *,
        error: str | BaseException | None = None,
    ) -> dict[str, object]:
        """Record one successful or failed tactic application.

        A success must supply ``goals_after``.  For a failure it may be
        omitted, and is then copied from ``goals_before``.  Supplying a changed
        after-state for a failure is rejected: tactic failure is transactional.
        """

        if self._finished:
            raise RuntimeError("cannot record a tactic after the session footer")
        if not isinstance(focus, int) or isinstance(focus, bool) or focus < 0:
            raise ValueError("focus must be a non-negative integer")
        if not isinstance(tactic, str) or not tactic.strip():
            raise ValueError("tactic must be non-empty text")

        before_text = render_goals(goals_before, meta_names=self._meta_names)
        if before_text and focus >= len(before_text):
            raise ValueError("focus is outside goals_before")

        if error is None:
            if goals_after is None:
                raise ValueError("a successful tactic needs goals_after")
            after_text = render_goals(goals_after, meta_names=self._meta_names)
            status = "ok"
            error_text: str | None = None
        else:
            error_text = sanitize_trace_text(str(error))
            if not error_text:
                raise ValueError("a failed tactic needs non-empty error text")
            after_text = (
                before_text
                if goals_after is None
                else render_goals(goals_after, meta_names=self._meta_names)
            )
            if after_text != before_text:
                raise ValueError("a failed tactic must leave goals unchanged")
            status = "error"

        # Insertion order here is the on-disk v=1 field order.  Do not sort.
        record: dict[str, object] = {
            "v": TRACE_VERSION,
            "session": self.session_id,
            "step": self._next_step,
            "goals_before": before_text,
            "focus": focus,
            "tactic": sanitize_trace_text(tactic),
            "goals_after": after_text,
            "status": status,
            "error": error_text,
        }
        self._next_step += 1
        self._tactic_count += 1
        return self._emit(record)

    def success(
        self,
        goals_before: Any,
        focus: int,
        tactic: str,
        goals_after: Any,
    ) -> dict[str, object]:
        """Convenience wrapper for a successful application."""

        return self.record_tactic(goals_before, focus, tactic, goals_after)

    def failure(
        self,
        goals_before: Any,
        focus: int,
        tactic: str,
        error: str | BaseException,
    ) -> dict[str, object]:
        """Convenience wrapper for a transactional failed application."""

        return self.record_tactic(goals_before, focus, tactic, error=error)

    def footer(
        self,
        *,
        qed: bool,
        theorem: Formula | str,
        proof_size: int,
        tactic_count: int | None = None,
        names: Sequence[str] = (),
    ) -> dict[str, object]:
        """Finish the session with the four-field footer from design section 4."""

        if self._finished:
            raise RuntimeError("the session footer was already recorded")
        if not isinstance(qed, bool):
            raise TypeError("qed must be a boolean")
        if not isinstance(proof_size, int) or isinstance(proof_size, bool) or proof_size < 0:
            raise ValueError("proof_size must be a non-negative integer")
        if tactic_count is None:
            tactic_count = self._tactic_count
        if (
            not isinstance(tactic_count, int)
            or isinstance(tactic_count, bool)
            or tactic_count < 0
        ):
            raise ValueError("tactic_count must be a non-negative integer")

        if isinstance(theorem, Formula):
            if not all(isinstance(name, str) for name in names):
                raise TypeError("theorem names must be text")
            theorem_text = pretty_formula(theorem, list(names))
        elif isinstance(theorem, str):
            theorem_text = _without_ansi(theorem)
        else:
            raise TypeError("theorem must be a Formula or canonical text")

        # The footer intentionally has no v/session fields: adjacency associates
        # it with the application records, exactly as the binding design shows.
        record: dict[str, object] = {
            "qed": qed,
            "theorem": theorem_text,
            "proof_size": proof_size,
            "tactic_count": tactic_count,
        }
        self._finished = True
        return self._emit(record)


__all__ = [
    "TRACE_VERSION",
    "TraceLimitError",
    "TraceLogger",
    "sanitize_trace_text",
    "render_goal",
    "render_goals",
]
