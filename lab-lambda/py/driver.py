"""Browser REPL driver for Lambda Lab.

Wraps the *real* vendored engine (``lambda_lab.lab.lc`` / ``parser`` /
``church``) behind a single ``LabSession.run(line) -> str`` method that returns
ANSI-colored text for xterm.js. The heavy interactive layers of the desktop app
(``prompt_toolkit`` REPL, ``typer`` CLI, ``rich`` console, ``openai`` judge,
``subprocess`` Lean calls) are intentionally NOT imported here — the browser
build is fully client-side and offline.

Commands:  help · about · commands/constants · church · numeral · expand ·
reduce · nf · lam · decode · tour · clear
"""

from __future__ import annotations

import re
from typing import List, Optional

from lambda_lab.lab import lc
from lambda_lab.lab.parser import parse, ParseError
from lambda_lab.lab import church

# ── ANSI helpers ───────────────────────────────────────────────────────────
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
MAX_NUMERAL = 24
MAX_TRACE = 60


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _term(t) -> str:
    """Pretty-print a term in unicode λ notation, colored."""
    return cyan(lc.pretty(t))


# ── numeral preprocessing ──────────────────────────────────────────────────
def _expand_numbers(src: str) -> str:
    """Replace standalone integer literals with their Church-numeral source.

    ``\\b\\d+\\b`` leaves digits inside identifiers (``x1``) untouched.
    """
    def repl(m: "re.Match[str]") -> str:
        n = int(m.group())
        if n > MAX_NUMERAL:
            raise ValueError(f"numeral {n} is too large for the browser (max {MAX_NUMERAL})")
        return f"({church.church_numeral_src(n)})"

    return re.sub(r"\b\d+\b", repl, src)


def _prepare(src: str) -> str:
    """Numbers → Church numerals, then named constants → λ-bodies."""
    return church.expand_named(_expand_numbers(src))


def _decode_note(t) -> Optional[str]:
    n = church.try_decode_numeral(t)
    if n is not None:
        return f"{green('= ' + str(n))}  {dim('(Church numeral)')}"
    b = church.try_decode_bool(t)
    if b is not None:
        name = "TRUE" if b else "FALSE"
        return f"{green('= ' + name)}  {dim('(Church boolean)')}"
    return None


# ── the session ────────────────────────────────────────────────────────────
class LabSession:
    def __init__(self) -> None:
        self.history: List[str] = []

    # -- dispatch ------------------------------------------------------------
    def run(self, line: str) -> str:
        line = (line or "").strip()
        if not line:
            return ""
        self.history.append(line)
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        try:
            handler = getattr(self, f"cmd_{cmd}", None)
            if handler is None:
                # bare term? try to reduce it.
                if any(ch in line for ch in "λ\\.()") or line.isidentifier():
                    return self.cmd_reduce(line)
                return red(f"Unknown command: {cmd!r}") + NL + dim("Type ") + bold("help") + dim(" for the list.")
            return handler(arg)
        except ParseError as e:
            return red("Parse error: ") + str(e)
        except RecursionError:
            return red("Reduction went too deep for the browser sandbox. Try a smaller term.")
        except ValueError as e:
            return red("Error: ") + str(e)
        except Exception as e:  # noqa: BLE001 — surface anything, never crash the REPL
            return red(f"{type(e).__name__}: {e}")

    # -- meta ----------------------------------------------------------------
    def cmd_help(self, arg: str) -> str:
        rows = [
            bold(magenta("Lambda Lab") + " — commands"),
            "",
            f"  {green('reduce')} {dim('<term>')}    step-by-step β-reduction  (alias: just type a term)",
            f"  {green('nf')} {dim('<term>')}        normal form only, with a decoded value",
            f"  {green('lam')} {dim('<term>')}       parse & pretty-print (λ and ASCII), free variables",
            f"  {green('expand')} {dim('<term>')}    expand named constants to raw λ-terms",
            f"  {green('church')} {dim('<NAME|n>')}  show a Church constant or numeral",
            f"  {green('numeral')} {dim('<n>')}      the Church numeral n = λf x. fⁿ x",
            f"  {green('decode')} {dim('<term>')}    normalize and read off a number / boolean",
            f"  {green('alpha')} {dim('<t> = <t>')}  are two terms the same function? (α-equivalence)",
            f"  {green('constants')}         list every named constant",
            f"  {green('tour')}              a 60-second guided tour",
            f"  {green('about')}             what this is",
            f"  {green('clear')}             clear the screen",
            "",
            dim("Terms use ") + cyan("λx. x") + dim(" or ") + cyan("\\x. x") + dim("; integers become Church numerals."),
            dim("Try:  ") + yellow("reduce AND TRUE FALSE") + dim("   ·   ") + yellow("nf PLUS 2 3") + dim("   ·   ") + yellow("church SUCC"),
        ]
        return _lines(*rows)

    def cmd_about(self, arg: str) -> str:
        return _lines(
            bold(magenta("Lambda Lab")) + dim(" · running entirely in your browser (Pyodide + xterm.js)"),
            "",
            "The λ-calculus playground from the VIASM mini-course",
            bold("“An Introduction to Automatic Theorem Proving in Mathematics.”"),
            "",
            "This is the author's real Python engine (α/β/η-reduction, Church encodings),",
            "compiled to WebAssembly — no server, no install, works offline once loaded.",
            "",
            dim("Course:  ") + blue("https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026"),
            dim("Source:  ") + blue("https://github.com/nasqret/vietnam2026"),
        )

    def cmd_constants(self, arg: str) -> str:
        groups = [
            ("Booleans", ["TRUE", "FALSE", "IF", "AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR", "IMPLIES", "IFF"]),
            ("Pairs", ["PAIR", "FST", "SND"]),
            ("Numerals & arithmetic", ["0", "SUCC", "PRED", "PLUS", "SUB", "MULT", "POW", "ISZERO", "LEQ", "EQ"]),
            ("Recursion & divergence", ["Y", "Z", "OMEGA"]),
        ]
        rows = [bold(magenta("Named constants")), ""]
        for title, names in groups:
            rows.append("  " + bold(title))
            rows.append("    " + "  ".join(green(n) for n in names))
            rows.append("")
        rows.append(dim("Use ") + yellow("church <NAME>") + dim(" to see any one expanded."))
        return _lines(*rows)

    cmd_commands = cmd_help

    # -- core ----------------------------------------------------------------
    def cmd_church(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "church <NAME|n>   e.g.  church SUCC   or   church 3"
        name = arg.strip()
        if name.lstrip("-").isdigit():
            n = int(name)
            if n < 0:
                return red("A Church numeral must be non-negative.")
            if n > MAX_NUMERAL:
                return red(f"Keep it ≤ {MAX_NUMERAL} in the browser.")
            t = church.church(n)
            return _lines(
                bold(f"Church numeral {n}") + dim(f"   =  λf x. apply f, {n} time(s), to x"),
                "  " + _term(t),
            )
        key = name.upper() if name.upper() in church.CONSTANTS else name
        if key not in church.CONSTANTS:
            return red(f"No constant named {name!r}. ") + dim("Try ") + bold("constants") + dim(".")
        concept = church.CONSTANTS[key]
        expanded = parse(church.expand_named(concept))
        rows = [
            bold(magenta(key)),
            dim("  conceptual:  ") + cyan(concept.replace("\\", "λ")),
            dim("  full λ-term: ") + _term(expanded),
        ]
        note = _decode_note(expanded)
        if note:
            rows.append("  " + note)
        return _lines(*rows)

    def cmd_numeral(self, arg: str) -> str:
        if not arg.strip().lstrip("-").isdigit():
            return yellow("Usage: ") + "numeral <n>   e.g.  numeral 4"
        return self.cmd_church(arg)

    def cmd_expand(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "expand <term>   e.g.  expand AND TRUE p"
        t = parse(_prepare(arg))
        return _lines(bold("Expanded to raw λ-term:"), "  " + _term(t))

    def cmd_lam(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "lam <term>   e.g.  lam \\x y. x (y z)"
        t = parse(_prepare(arg))
        fv = sorted(lc.free_vars(t))
        return _lines(
            bold("Parsed term"),
            "  λ-notation: " + _term(t),
            "  ASCII:      " + cyan(lc.show_ascii(t)),
            "  free vars:  " + (yellow(", ".join(fv)) if fv else dim("(none — closed term)")),
        )

    def cmd_reduce(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "reduce <term>   e.g.  reduce (\\x. x x) (\\y. y)"
        t = parse(_prepare(arg))
        rows = [bold("β-reduction") + dim("  (normal order)"), "  " + dim("start:  ") + _term(t)]
        steps = 0
        last = t
        for step in lc.trace_steps(t, max_steps=MAX_TRACE):
            steps += 1
            rows.append(f"  {dim('→β')}      " + cyan(lc.pretty(step.after)))
            last = step.after
        if steps == 0:
            rows.append("  " + dim("already in normal form."))
        elif steps >= MAX_TRACE:
            rows.append("  " + yellow(f"… stopped after {MAX_TRACE} steps (no normal form reached)."))
        else:
            rows.append("  " + green(f"normal form reached in {steps} step(s).") )
        note = _decode_note(last)
        if note:
            rows.append("  " + note)
        return _lines(*rows)

    cmd_red = cmd_reduce
    cmd_r = cmd_reduce

    def cmd_nf(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "nf <term>   e.g.  nf MULT 2 3"
        t = parse(_prepare(arg))
        result = lc.normalize(t, max_steps=1000)
        rows = [bold("Normal form"), "  " + _term(result)]
        note = _decode_note(result)
        if note:
            rows.append("  " + note)
        return _lines(*rows)

    cmd_whnf = cmd_nf

    def cmd_decode(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "decode <term>"
        t = parse(_prepare(arg))
        note = _decode_note(t)
        return "  " + (note if note else dim("Not a Church numeral or boolean."))

    def cmd_alpha(self, arg: str) -> str:
        if "=" not in arg:
            return yellow("Usage: ") + "alpha <term> = <term>   e.g.  alpha AND TRUE FALSE = FALSE"
        left, right = arg.split("=", 1)
        t1 = lc.normalize(parse(_prepare(left.strip())), max_steps=1000)
        t2 = lc.normalize(parse(_prepare(right.strip())), max_steps=1000)
        same = lc.alpha_eq(t1, t2)
        return _lines(
            bold("α-equivalence") + dim("  (both sides normalized first)"),
            "  left:  " + cyan(lc.pretty(t1)),
            "  right: " + cyan(lc.pretty(t2)),
            "  " + (green("≡  the same function (α-equivalent)") if same else red("≢  not equal")),
        )

    cmd_eq = cmd_alpha

    def cmd_tour(self, arg: str) -> str:
        demos = [
            ("Identity applied to a variable", "(\\x. x) y"),
            ("Church boolean AND", "AND TRUE FALSE"),
            ("Successor of 2", "SUCC 2"),
            ("2 + 3", "PLUS 2 3"),
            ("2 × 3", "MULT 2 3"),
        ]
        rows = [bold(magenta("A 60-second tour")), dim("Each of these you can run yourself:"), ""]
        for title, expr in demos:
            t = lc.normalize(parse(_prepare(expr)), max_steps=1000)
            note = _decode_note(t)
            rows.append("  " + bold(title))
            rows.append("    " + yellow(expr) + dim("  ⇝  ") + cyan(lc.pretty(t)) + ("   " + note if note else ""))
            rows.append("")
        rows.append(dim("Now try ") + yellow("reduce AND TRUE FALSE") + dim(" to see every step."))
        return _lines(*rows)


_SESSION: Optional[LabSession] = None


def get_session() -> LabSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = LabSession()
    return _SESSION


def run_line(line: str) -> str:
    """Entry point called from JavaScript."""
    return get_session().run(line)


def banner() -> str:
    return _lines(
        magenta(bold("  λ  Lambda Lab")) + dim("  ·  in-browser λ-calculus  ·  VIASM 2026"),
        dim("  the real engine, compiled to WebAssembly — offline, no install"),
        "",
        dim("  type ") + bold(green("help")) + dim(" to begin, or ") + bold(green("tour")) + dim(" for a quick taste."),
        "",
    )
