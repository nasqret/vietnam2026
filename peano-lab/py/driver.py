"""Browser REPL driver for Peano Lab.

The driver is intentionally thin.  It dispatches the ``pa`` command family,
but a live proof or tutorial session owns raw input *before* ordinary command
handlers are considered.  Proof construction and final checking live in
``peano_lab``; this module only provides the browser-shaped ``run_line`` /
``banner`` API.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Optional

from peano_lab.engine.decide import DecisionError, evaluate_closed_term
from peano_lab.engine.rewrite import PA_SIMP_SET, SimpError, simplify_formula
from peano_lab.kernel.checker import axiom_formula
from peano_lab.kernel.formulas import Eq, pretty_formula
from peano_lab.kernel.terms import (
    ParseError,
    parse_term_with_names,
    pretty_term,
)
from peano_lab.ui import data_kb, data_library, data_tactics, tutorial
from peano_lab.ui import prove as web_prove


NL = "\r\n"
MAX_INPUT = 4_000
MAX_NUMERAL = web_prove.MAX_NUMERAL
_oversized_numeral = web_prove.oversized_numeral
_PYTHON_ERROR_LINE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*Error:")


def _failed_output(output: str) -> bool:
    """Classify the driver's pinned first-line failure protocol.

    Multiline replay needs a structured stop signal.  Existing public command
    text remains unchanged; Python, rather than browser JavaScript, examines
    the first rendered line where each driver/proof failure contract places
    its final English label.
    """

    first = output.splitlines()[0] if output.splitlines() else ""
    return (
        _PYTHON_ERROR_LINE.match(first) is not None
        or first.startswith("Error:")
        or first.startswith("Parse error:")
        or first.startswith("Tactic error:")
        or first.startswith("QED check failed:")
        or first.startswith("Unknown command ")
        or first.startswith("Unknown `pa` command ")
        or first.startswith("Usage:")
        or first.startswith("Input is too long ")
        or first == "A proof is already in progress."
        or first == "Proof aborted. No theorem was claimed."
        or (first.startswith("`") and "acts only when typed alone" in first)
    )


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


def _usage() -> str:
    return _lines(
        "Peano Lab — commands",
        "",
        "  pa prove <formula>   interactive kernel-checked proof",
        "  pa tactic [name]     executable tactic-language encyclopedia",
        "  pa kb [topic]        PA/kernel knowledge cards (`kb` is an alias)",
        "  pa tutorial [name]   guided, ENTER-driven lessons",
        "  pa lib [name]        checked theorem statements + replay scripts",
        "  pa lean <name>       Lean 4 statement/stub + exact Live Lean link",
        "  script [download]    inspect/save the active or last checked replay",
        "  pa axioms            the six PA rule constants",
        "  pa eval <term>       evaluate a closed arithmetic term",
        "  pa simp <term>       normalize with the ordered PA3–PA6 simp set",
        "",
        "Formula aliases: -> / →, /\\ / ∧, \\/ / ∨, ~ / ¬, forall / ∀, exists / ∃.",
        f"Browser resource limit: numeral literals 0..{MAX_NUMERAL}.",
        "Try: pa prove forall n. 0 + n = n",
    )


class LabSession:
    """One browser tab's command history and one possible interactive owner."""

    def __init__(self) -> None:
        self.history: list[str] = []
        self.webstate: dict = {}

    def _session_owner(self) -> str | None:
        if web_prove.is_active(self.webstate):
            return "prove"
        if tutorial.is_active(self.webstate):
            return "tutorial"
        return None

    def run(self, line: str) -> str:
        if not isinstance(line, str):
            return "Error: input must be text."
        # A browser download is a one-shot response to this exact command.  A
        # later, unrelated command must never consume a stale payload.
        self.webstate.pop(web_prove.KEY_PENDING_DOWNLOAD, None)
        line = line.strip()
        if not line:
            if self._session_owner() == "prove":
                return _browser_safe(web_prove.handle("", self.webstate))
            if self._session_owner() == "tutorial":
                return _browser_safe(tutorial.handle("", self.webstate))
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
            if self._session_owner() == "tutorial":
                return _browser_safe(tutorial.handle(line, self.webstate))

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

    def run_result(self, line: str) -> dict[str, object]:
        """Run one line and return the worker's structured replay status.

        The ordinary ``run`` API and its exact output stay pinned.  ``failed``
        is advisory browser control flow only: it can stop a pasted batch, but
        it never grants QED or bypasses the independent checker.
        """

        owner_before = self._session_owner()
        output = self.run(line)
        owner_after = self._session_owner()
        source = line.strip() if isinstance(line, str) else ""
        failed = _failed_output(output)

        opens_proof = re.match(
            r"^pa\s+prove(?:\s|$)", source, re.IGNORECASE
        ) is not None
        if opens_proof:
            # A statement line succeeds only if it really created a proof
            # owner from an idle session.  An active tutorial owns raw input
            # just as strictly as an active proof, so it must also stop here.
            failed = failed or owner_before is not None or owner_after != "prove"
        elif owner_before == "prove":
            if source in {"qed", "done", "finish"}:
                failed = failed or owner_after is not None or "No open goals. QED." not in output
            elif owner_after != "prove":
                # ``abort`` and any unexpected owner loss stop the batch.  A
                # successful QED is handled by the exact branch above.
                failed = True

        return {"out": output, "failed": bool(failed)}

    def cmd_help(self, args: str) -> str:
        topic = args.strip().lower()
        if topic in {"pa", "prove"}:
            return web_prove.usage() if topic == "prove" else _usage()
        if topic == "tactic":
            return data_tactics.render_index()
        if topic == "kb":
            return self.pa_kb("help")
        if topic == "tutorial":
            return tutorial.handle("help", self.webstate)
        if topic == "lib":
            return data_library.render_request("help")
        if topic == "lean":
            return "Usage: pa lean <theorem>; list names with `pa lib`."
        if topic:
            return f"No help topic {args.strip()!r}. Type `help` or `pa help`."
        return _usage()

    cmd_commands = cmd_help

    def cmd_kb(self, args: str) -> str:
        return self.pa_kb(args)

    def cmd_tutorial(self, args: str) -> str:
        return self.pa_tutorial(args)

    def cmd_script(self, args: str) -> str:
        return web_prove.script_request(args, self.webstate)

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
        if not args or args.lower() == "help":
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
            return data_tactics.render_index()
        return data_tactics.render_card(name)

    def pa_kb(self, args: str) -> str:
        request = args.strip()
        folded = request.casefold()
        if not request or folded in {"list", "ls"}:
            return data_kb.render_index()
        if folded in {"help", "?"}:
            return _lines(
                "Peano Lab knowledge base",
                "  kb                       list cards",
                "  kb <slug>                open one card",
                "  kb search <words>         deterministic full-text search",
                "  kb list                  list cards (`pa kb ...` also works)",
            )
        pieces = request.split(maxsplit=1)
        if pieces[0].casefold() == "search":
            if len(pieces) == 1:
                return "Usage: kb search <words>"
            return data_kb.render_index(data_kb.search_cards(pieces[1]))
        card = data_kb.get_card(request)
        if card is None:
            return f"No knowledge-base card {request!r}. Type `kb` or `kb search <words>`."
        return data_kb.render_card(card)

    def pa_tutorial(self, args: str) -> str:
        return tutorial.handle(args, self.webstate)

    def pa_lib(self, args: str) -> str:
        return data_library.render_request(args)

    def pa_lean(self, args: str) -> str:
        return data_library.render_lean(args)

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

    def take_download(self) -> str:
        """Consume the current command's validated replay-download bytes."""

        return web_prove.take_pending_download(self.webstate)


_SESSION: Optional[LabSession] = None


def get_session() -> LabSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = LabSession()
    return _SESSION


def run_line(line: str) -> str:
    return get_session().run(line)


def run_line_result(line: str) -> str:
    """Return one JSON command envelope for the browser worker."""

    return json.dumps(
        get_session().run_result(line),
        ensure_ascii=True,
        separators=(",", ":"),
    )


def take_download() -> str:
    return get_session().take_download()


def banner() -> str:
    return _lines(
        "  Peano Lab · kernel-checked arithmetic proofs · VIASM 2026",
        "  intuitionistic PA by default; classical DNE is always explicit",
        "",
        "  type `help` to begin, or try `pa prove forall n. 0 + n = n`",
        "",
    )


__all__ = [
    "LabSession",
    "get_session",
    "run_line",
    "run_line_result",
    "take_download",
    "banner",
]
