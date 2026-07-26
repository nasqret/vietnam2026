"""Deterministic Lean 4 exports for closed Peano Lab formulas.

This module is deliberately outside the trusted kernel.  It translates a
kernel formula into a small, readable Lean statement and places the Peano Lab
tactic script in comments beside an intentional ``sorry`` proof stub.  The
stub is an invitation to cross-check the theorem in a second prover; it is not
part of Peano Lab's soundness story.

The surface ``a <= b`` notation has already been expanded by Peano Lab's
parser to ``exists k. k + a = b``.  The exporter renders that expanded formula
instead of silently replacing it with Lean's library order relation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re
from urllib.parse import quote

from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


LIVE_LEAN_PREFIX = "https://live.lean-lang.org/#code="

_BINDER_NAMES = ("x", "y", "z", "n", "m", "k", "i", "j", "u", "v", "w")
_LEAN_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")


@dataclass(frozen=True, slots=True)
class LeanExport:
    """A Lean theorem stub and the matching one-click web-editor link."""

    name: str
    statement: str
    code: str
    live_url: str


def _fresh_binder(names: tuple[str, ...]) -> str:
    used = set(names)
    for candidate in _BINDER_NAMES:
        if candidate not in used:
            return candidate
    suffix = 0
    while f"x{suffix}" in used:
        suffix += 1
    return f"x{suffix}"


def _successor_numeral(term: Term) -> int | None:
    count = 0
    while type(term) is Succ:
        count += 1
        term = term.term
    return count if type(term) is Zero else None


def _term_to_lean(term: Term, names: tuple[str, ...], parent_precedence: int) -> str:
    if type(term) is Var:
        if type(term.index) is not int or term.index < 0 or term.index >= len(names):
            raise ValueError(
                "Lean export requires a closed formula; "
                f"de Bruijn index #{term.index} is free at binder depth {len(names)}"
            )
        text, precedence = names[term.index], 4
    elif type(term) is Zero:
        text, precedence = "0", 4
    elif type(term) is Succ:
        numeral = _successor_numeral(term)
        if numeral is not None:
            text, precedence = str(numeral), 4
        else:
            text = f"Nat.succ ({_term_to_lean(term.term, names, 0)})"
            precedence = 3
    elif type(term) in (Add, Mul):
        precedence = 1 if type(term) is Add else 2
        symbol = "+" if type(term) is Add else "*"
        left = _term_to_lean(term.left, names, precedence)
        right = _term_to_lean(term.right, names, precedence + 1)
        text = f"{left} {symbol} {right}"
    else:
        raise TypeError("expected a Peano Lab term")
    return f"({text})" if precedence < parent_precedence else text


def _formula_to_lean(
    formula: Formula,
    names: tuple[str, ...],
    parent_precedence: int,
) -> str:
    if type(formula) is Eq:
        text = (
            f"{_term_to_lean(formula.left, names, 0)} = "
            f"{_term_to_lean(formula.right, names, 0)}"
        )
        precedence = 5
    elif type(formula) is Bot:
        text, precedence = "False", 5
    elif type(formula) in (And, Or, Imp):
        if type(formula) is And:
            precedence, symbol = 3, "∧"
        elif type(formula) is Or:
            precedence, symbol = 2, "∨"
        else:
            precedence, symbol = 1, "→"
        # Lean parses all three connectives right-associatively.  Parenthesize
        # an equal-precedence node on the left, while the right may retain the
        # default grouping.  This preserves Peano Lab's exact formula tree,
        # including its surface parser's deliberately left-folded /\ and \/.
        left = _formula_to_lean(formula.left, names, precedence + 1)
        right = _formula_to_lean(formula.right, names, precedence)
        text = f"{left} {symbol} {right}"
    elif type(formula) in (Forall, Exists):
        binder = _fresh_binder(names)
        symbol = "∀" if type(formula) is Forall else "∃"
        body = _formula_to_lean(formula.body, (binder,) + names, 0)
        text = f"{symbol} {binder} : Nat, {body}"
        precedence = 0
    else:
        raise TypeError("expected a Peano Lab formula")
    return f"({text})" if precedence < parent_precedence else text


def formula_to_lean(formula: Formula) -> str:
    """Render a closed Peano Lab formula as a deterministic Lean proposition.

    Peano Lab stores variables as de Bruijn indices, so binder spellings are
    not part of a kernel formula.  This function chooses fresh canonical names
    and rejects any index that remains free at the top level.
    """

    if not isinstance(formula, Formula):
        raise TypeError("formula must be a Peano Lab Formula")
    return _formula_to_lean(formula, (), 0)


def live_lean_url(code: str) -> str:
    """Return a URL that opens exactly ``code`` in the Live Lean editor."""

    if not isinstance(code, str):
        raise TypeError("Lean code must be text")
    return LIVE_LEAN_PREFIX + quote(code, safe="")


def _script_lines(script: Sequence[str] | str) -> tuple[str, ...]:
    if isinstance(script, str):
        entries: Sequence[str] = (script,)
    elif isinstance(script, Sequence) and all(isinstance(line, str) for line in script):
        entries = script
    else:
        raise TypeError("script must be text or a sequence of text lines")

    # Prefix every physical line separately so tactic text can never escape
    # from its Lean comment merely by containing a newline.
    lines: list[str] = []
    for entry in entries:
        split = entry.splitlines()
        lines.extend(split if split else ("",))
    return tuple(lines)


def _validate_theorem_name(name: str) -> None:
    if (
        not isinstance(name, str)
        or name == "_"
        or _LEAN_IDENTIFIER.fullmatch(name) is None
    ):
        raise ValueError("theorem name must be a non-underscore ASCII identifier")


def export_theorem(
    name: str,
    formula: Formula,
    script: Sequence[str] | str = (),
    *,
    dependencies: Sequence[str] = (),
) -> LeanExport:
    """Build a namespaced Lean theorem with a commented Peano tactic script.

    The generated theorem lives in ``namespace PeanoLab`` to avoid colliding
    with Mathlib names such as ``add_comm``.  The name is always emitted with
    Lean's ``«escaped identifier»`` syntax, so a future contextual keyword
    cannot make otherwise safe generated code invalid. Its body is
    intentionally ``sorry``: ``pa lean`` exports a cross-checking *stub*,
    never a second certificate that Peano Lab might accidentally trust.
    """

    _validate_theorem_name(name)
    if (
        not isinstance(dependencies, Sequence)
        or isinstance(dependencies, (str, bytes, bytearray))
        or not all(isinstance(dependency, str) for dependency in dependencies)
    ):
        raise TypeError("dependencies must be a sequence of theorem names")
    for dependency in dependencies:
        _validate_theorem_name(dependency)
    statement = formula_to_lean(formula)
    tactics = _script_lines(script)
    comments: list[str] = []
    if dependencies:
        comments.extend(
            (
                "  -- Earlier checked Peano Lab dependencies: "
                + ", ".join(dependencies),
                "  -- The library supplies them before this authored body.",
                "  -- Peano Lab authored tactic body:",
            )
        )
    else:
        comments.append("  -- Peano Lab tactic script:")
    if tactics:
        comments.extend(f"  --   {line}" for line in tactics)
    else:
        comments.append("  --   (no script supplied)")
    comments.append("  -- Replace this stub with a Lean proof to cross-check it.")

    code = "\n".join(
        (
            "-- Generated by Peano Lab; the statement is exact, the proof is a stub.",
            "namespace PeanoLab",
            "",
            f"theorem «{name}» : {statement} := by",
            *comments,
            "  sorry",
            "",
            "end PeanoLab",
        )
    )
    return LeanExport(name, statement, code, live_lean_url(code))


__all__ = [
    "LIVE_LEAN_PREFIX",
    "LeanExport",
    "formula_to_lean",
    "live_lean_url",
    "export_theorem",
]
