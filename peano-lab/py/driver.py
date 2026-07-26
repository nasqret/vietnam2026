"""Browser REPL driver for Peano Lab.

The driver is intentionally thin.  It dispatches the ``pa`` command family,
but a live proof session owns raw input *before* ordinary command handlers are
considered.  Proof construction and final checking live in ``peano_lab``;
this module only provides the browser-shaped ``run_line`` / ``banner`` API.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from peano_lab.engine.decide import DecisionError, evaluate_closed_term
from peano_lab.engine.rewrite import PA_SIMP_SET, SimpError, simplify_formula
from peano_lab.engine.tactics import TACTIC_NAMES
from peano_lab.kernel.checker import axiom_formula
from peano_lab.kernel.formulas import Eq, pretty_formula
from peano_lab.kernel.terms import (
    ParseError,
    parse_term_with_names,
    pretty_term,
)
from peano_lab.ui import prove as web_prove


NL = "\r\n"
MAX_INPUT = 4_000
MAX_NUMERAL = 256
_NUMERAL_LITERAL = re.compile(r"(?<![\w'#])\d+(?![\w'])", re.UNICODE)


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _browser_safe(text: object) -> str:
    """Neutralize Unicode control/format codes while preserving line layout."""

    source = str(text)
    result: list[str] = []
    for char in source:
        code = ord(char)
        if char in "\r\n\t" or unicodedata.category(char) not in {
            "Cc",
            "Cf",
            "Cs",
            "Zl",
            "Zp",
        }:
            result.append(char)
        else:
            result.append(f"\\u{code:04x}" if code > 0xFF else f"\\x{code:02x}")
    return "".join(result)


def _oversized_numeral(source: str) -> str | None:
    """Find a browser-dangerous numeral without matching digits in names."""

    for match in _NUMERAL_LITERAL.finditer(source):
        if int(match.group()) > MAX_NUMERAL:
            return match.group()
    return None


def _usage() -> str:
    return _lines(
        "Peano Lab — commands",
        "",
        "  pa prove <formula>   interactive kernel-checked proof",
        "  pa tactic [name]     tactic-language index (full cards in M6)",
        "  pa lib [name]        theorem-library entry point (library in M7)",
        "  pa axioms            the six PA rule constants",
        "  pa eval <term>       evaluate a closed arithmetic term",
        "  pa simp <term>       normalize with the ordered PA3–PA6 simp set",
        "",
        "Formula aliases: -> / →, /\\ / ∧, \\/ / ∨, ~ / ¬, forall / ∀, exists / ∃.",
        f"Browser resource limit: numeral literals 0..{MAX_NUMERAL}.",
        "Try: pa prove forall n. 0 + n = n",
    )


_TACTIC_SUMMARY = {
    "intro": "introduce an implication hypothesis or universal variable",
    "apply": "match a hypothesis, PA axiom, or enabled DNE against the goal",
    "exact": "close with a named hypothesis",
    "assumption": "close with the first matching hypothesis",
    "split": "turn a conjunction into its two component goals",
    "left": "prove the left side of a disjunction",
    "right": "prove the right side of a disjunction",
    "cases": "eliminate a structured hypothesis",
    "exfalso": "replace the target by false",
    "exists": "supply a witness (or `?` for a scoped metavariable)",
    "specialize": "instantiate a universal hypothesis",
    "forall_elim": "alias of specialize",
    "induction": "make base and successor-step goals",
    "refl": "close a reflexive equation",
    "symm": "reverse an equality goal",
    "trans": "insert an equality midpoint",
    "congr": "reduce equality of constructors to their arguments",
    "rewrite": "transport through one equality occurrence",
    "simp": "ordered certified rewriting with PA3–PA6",
    "undo": "restore the exact previous proof state",
}


class LabSession:
    """One browser tab's command history and one possible proof owner."""

    def __init__(self) -> None:
        self.history: list[str] = []
        self.webstate: dict = {}

    def _session_owner(self) -> str | None:
        return "prove" if web_prove.is_active(self.webstate) else None

    def run(self, line: str) -> str:
        if not isinstance(line, str):
            return "Error: input must be text."
        line = line.strip()
        if not line:
            if self._session_owner() == "prove":
                return _browser_safe(web_prove.handle("", self.webstate))
            return ""
        if len(line) > MAX_INPUT:
            return f"Input is too long (max {MAX_INPUT} characters)."
        oversized = _oversized_numeral(line)
        if oversized is not None:
            return (
                f"Error: numeral {oversized} exceeds the browser limit "
                f"of {MAX_NUMERAL}."
            )
        self.history.append(line)
        try:
            # Audit law: an active proof owns the COMPLETE line before the
            # driver lowercases or dispatches any ordinary command name.
            if self._session_owner() == "prove":
                return _browser_safe(web_prove.handle(line, self.webstate))

            pieces = line.split(maxsplit=1)
            command = pieces[0].lower()
            args = pieces[1].strip() if len(pieces) > 1 else ""
            handler = getattr(self, f"cmd_{command}", None)
            if handler is None:
                return _browser_safe(
                    f"Unknown command {pieces[0]!r}. Type `help`; Peano commands start with `pa`."
                )
            return _browser_safe(handler(args))
        except (ParseError, DecisionError, SimpError, ValueError) as exc:
            return _browser_safe(f"Error: {exc}")
        except RecursionError:
            return "Error: the expression is too deeply nested for the browser."
        except Exception as exc:  # keep the browser REPL alive, but surface bugs
            return _browser_safe(f"{type(exc).__name__}: {exc}")

    def cmd_help(self, args: str) -> str:
        topic = args.strip().lower()
        if topic in {"pa", "prove"}:
            return web_prove.usage() if topic == "prove" else _usage()
        if topic:
            return f"No help topic {args.strip()!r}. Type `help` or `pa help`."
        return _usage()

    cmd_commands = cmd_help

    def cmd_about(self, args: str) -> str:
        del args
        return _lines(
            "Peano Lab · a small, readable theorem prover for Peano arithmetic",
            "Soundness boundary: tactics build certificates; every QED is rechecked",
            "against the original theorem by the independent kernel.",
            "Logic: intuitionistic PA by default; classical DNE is explicit and labeled.",
            "The Python runtime stays client-side in the browser.",
        )

    def cmd_pa(self, args: str) -> str:
        args = args.strip()
        if not args or args == "help":
            return _usage()
        pieces = args.split(maxsplit=1)
        subcommand = pieces[0].lower()
        rest = pieces[1].strip() if len(pieces) > 1 else ""
        handler = getattr(self, f"pa_{subcommand}", None)
        if handler is None:
            return f"Unknown `pa` command {pieces[0]!r}. Type `pa help`."
        return handler(rest)

    def pa_prove(self, args: str) -> str:
        return web_prove.handle(args, self.webstate)

    def pa_tactic(self, args: str) -> str:
        name = args.strip()
        if not name:
            operational = ", ".join(TACTIC_NAMES)
            return _lines(
                "Operational tactics",
                f"  {operational}",
                "Tacticals: ;, <|>, repeat, first [...], all_goals, focus.",
                "Automation: auto [depth]. Full teaching cards arrive in M6.",
            )
        if name in _TACTIC_SUMMARY:
            return _lines(name, f"  {_TACTIC_SUMMARY[name]}")
        if name in {"auto", "repeat", "first", "all_goals", "focus", ";", "<|>"}:
            return _lines(name, "  an M4 automation/tactical command; type `pa prove tactics` for syntax.")
        return f"No tactic named {name!r}. Type `pa tactic`."

    def pa_lib(self, args: str) -> str:
        name = args.strip()
        if name:
            return f"No published library entry {name!r} yet; the checked ladder ships in M7."
        return "The checked named-theorem library ships in M7; interactive proving is live now."

    def pa_axioms(self, args: str) -> str:
        if args:
            return "Usage: pa axioms"
        rows = ["Peano arithmetic rule constants"]
        for name in ("PA1", "PA2", "PA3", "PA4", "PA5", "PA6"):
            formula = axiom_formula(name)
            assert formula is not None
            rows.append(f"  {name}: {pretty_formula(formula, [])}")
        rows.append("  IND: structural induction schema (instantiated per motive)")
        return _lines(*rows)

    def pa_eval(self, args: str) -> str:
        if not args:
            return "Usage: pa eval <closed-term>"
        term, names = parse_term_with_names(args)
        if names:
            return f"Cannot evaluate an open term; free variable(s): {', '.join(names)}."
        value = evaluate_closed_term(term)
        return _lines(
            "Closed-term evaluation",
            f"  {pretty_term(term, [])} = {value}",
        )

    def pa_simp(self, args: str) -> str:
        if not args:
            return "Usage: pa simp <term>"
        term, names = parse_term_with_names(args)
        # The public simplifier works over formulas so that every rewrite step
        # carries a transport certificate.  A reflexive display equation lets
        # us reuse that exact ordered engine without a second term rewriter.
        result = simplify_formula(Eq(term, term), PA_SIMP_SET)
        simplified = result.formula.left
        rules: list[str] = []
        for step in result.steps:
            if step.rule not in rules:
                rules.append(step.rule)
        suffix = ", ".join(rules) if rules else "no rule fired"
        return _lines(
            "PA simp normal form (ordered PA3–PA6)",
            f"  {pretty_term(term, list(names))} ⇝ {pretty_term(simplified, list(names))}",
            f"  {suffix}",
        )


_SESSION: Optional[LabSession] = None


def get_session() -> LabSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = LabSession()
    return _SESSION


def run_line(line: str) -> str:
    return get_session().run(line)


def banner() -> str:
    return _lines(
        "  Peano Lab · kernel-checked arithmetic proofs · VIASM 2026",
        "  intuitionistic PA by default; classical DNE is always explicit",
        "",
        "  type `help` to begin, or try `pa prove forall n. 0 + n = n`",
        "",
    )


__all__ = ["LabSession", "get_session", "run_line", "banner"]
