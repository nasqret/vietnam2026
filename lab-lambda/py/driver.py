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

# A few of the course's REAL Lean snippets, shown read-only in the browser
# (the Lean kernel itself can't run in Pyodide). Mirrors artifacts/lean/.
LEAN_SNIPPETS = {
    "s_comb": ("the S combinator (Curry–Howard)",
               "theorem s_combinator {p q r : Prop}\n"
               "    (f : p → q → r) (g : p → q) (x : p) : r :=\n  f x (g x)"),
    "modus_ponens": ("modus ponens is function application",
                     "theorem modus_ponens {P Q : Prop} : (P → Q) → P → Q :=\n  fun f p => f p"),
    "and_comm": ("conjunction is a swappable pair",
                 "theorem and_comm {P Q : Prop} : P ∧ Q → Q ∧ P :=\n  fun ⟨hp, hq⟩ => ⟨hq, hp⟩"),
    "imp_comp": ("implication composes",
                 "theorem imp_comp {P Q R : Prop} (f : P → Q) (g : Q → R) : P → R :=\n  fun p => g (f p)"),
    "add_comm": ("commutativity of + by induction",
                 "theorem add_comm' (n m : Nat) : n + m = m + n := by\n"
                 "  induction m with\n"
                 "  | zero      => rw [Nat.add_zero, Nat.zero_add]\n"
                 "  | succ m ih => rw [Nat.add_succ, Nat.succ_add, ih]"),
    "zero_add": ("0 + n = n needs induction (n + 0 = n is rfl)",
                 "theorem zero_add' : ∀ n : Nat, 0 + n = n\n"
                 "  | 0     => rfl\n"
                 "  | n + 1 => congrArg (· + 1) (zero_add' n)"),
    "eval": ("a tiny expression evaluator (EML in miniature)",
             "inductive Tm | lit : Nat → Tm | add : Tm → Tm → Tm\n\n"
             "def eval : Tm → Nat\n  | .lit n   => n\n  | .add a b => eval a + eval b\n\n"
             "example : eval (.add (.lit 1) (.lit 1)) = 2 := rfl"),
    "term_proofs": ("term mode vs tactic mode — the SAME term",
                    "theorem tm {P Q : Prop} : (P → Q) → P → Q := fun f p => f p\n"
                    "theorem tc {P Q : Prop} : (P → Q) → P → Q := by\n  intro f p; exact f p"),
}
LEAN_SNIPPETS["s_combinator"] = LEAN_SNIPPETS["s_comb"]

# Commands that exist in the full desktop lab (nasqret/falenty-2026) but are not
# part of this static browser build (they need data files / a Lean process / network).
DESKTOP_ONLY = {"ch", "tutorial", "games", "eml", "prove",
                "aristotle", "ag", "acorn", "lang"}

# A small knowledge base, distilled from the course Obsidian vault (vault/concepts/*).
KB = {
    "beta-reduction": ("β-reduction", "The one computational rule: (λx.t) u → t[x:=u]. Repeated β-reduction is computation; a term with no redex is a normal form. See: church-rosser, normal-form."),
    "alpha-equivalence": ("α-equivalence", "Renaming bound variables leaves a term unchanged: λx.x ≡ λy.y. Bound names carry no meaning. Try: alpha \\x.x = \\y.y"),
    "substitution": ("Capture-avoiding substitution", "t[x:=u] replaces free x by u, renaming bound variables so no free variable of u is captured. The subtle heart of the calculus."),
    "eta": ("η-reduction", "Extensionality: λx.(t x) → t when x is not free in t. Two functions equal on all inputs are identified."),
    "normal-form": ("Normal form", "A term with no β-redex. By Church–Rosser it is unique up to α when it exists. Ω = (λx.xx)(λx.xx) has none."),
    "church-rosser": ("Church–Rosser (confluence)", "If t reduces to u1 and to u2, both reduce to a common v. Hence normal forms are unique — 'the answer' is order-independent."),
    "church-encoding": ("Church encoding", "Data as pure functions: true=λt f.t, false=λt f.f, numeral n=λf x.fⁿx, pow=λm n.n m. Try: nf PLUS 2 3"),
    "church-numeral": ("Church numeral", "n = λf x. f(f(…(f x))) — apply f to x, n times. Arithmetic is composition. Try: church 3 or peano 3"),
    "y-combinator": ("Y-combinator", "Y = λf.(λx.f(x x))(λx.f(x x)) satisfies Y f → f (Y f): a fixed point of any f, giving recursion in the pure calculus."),
    "curry-howard": ("Curry–Howard correspondence", "Propositions ARE types; proofs ARE terms. → is a function, ∧ a product, ∨ a sum, ⊥ the empty type, ∀ a Π, ∃ a Σ; β-reduction is proof normalization."),
    "type-judgment": ("Typing judgment", "Γ ⊢ t : A — in context Γ, term t has type A. Type theory is a system of rules for deriving such judgments."),
    "stlc": ("Simply-typed λ-calculus", "Types A ::= o | A→B; three rules (var/abs/app). Every well-typed term is strongly normalizing, so the Y-combinator is untypable."),
    "dependent-type": ("Dependent type", "A type may depend on a term: Π-types generalize → and encode ∀; Σ-types generalize × and encode ∃. The core of MLTT and Lean."),
    "s-combinator": ("The S combinator", "S f g x = f x (g x). Its type (p→q→r)→(p→q)→p→r is a tautology whose proof IS S — the Rosetta stone proved in all four provers. Try: lean s_comb"),
    "lean": ("Lean 4", "A proof assistant on the Calculus of Inductive Constructions. Term & tactic mode; Prop vs Type; standard library Mathlib (~283k theorems). Try: lean add_comm"),
    "autoformalization": ("Autoformalization", "Statement autoformalization (NL → formal statement) vs proof autoformalization (find a kernel-checkable proof). LLM proposes, kernel disposes. See Lecture 6 and the EML project."),
    "eml": ("EML project", "Lean 4 formalization of arXiv:2603.21852: 36 elementary-function primitives realized by EMLTerm witnesses whose eval? provably matches; 100 theorems, sorry-free, 8062 kernel jobs."),
}

# Self-check quiz: (question, expected-answer source). The answer is checked
# by normalizing the learner's term and comparing up to α-equivalence.
QUIZ_QS = [
    ("Reduce  AND TRUE TRUE  — what Church boolean do you get?", "TRUE"),
    ("What is  PLUS 2 2  as a Church numeral?", "4"),
    ("Reduce  NOT FALSE .", "TRUE"),
    ("Normal form of  (\\x. x) (\\y. y) ?", "\\y. y"),
    ("What is  MULT 2 3 ?", "6"),
    ("Reduce  FST (PAIR TRUE FALSE) .", "TRUE"),
    ("What is  PRED 3 ?", "2"),
    ("Is  OR FALSE FALSE  true or false? (answer TRUE or FALSE)", "FALSE"),
]


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
        self.quiz: Optional[str] = None   # expected-answer source while a quiz question is open
        self.quiz_idx: int = 0

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
                if cmd in DESKTOP_ONLY:
                    return self._desktop_only(cmd)
                # a quiz is open and this isn't a command → treat the line as the answer
                if self.quiz is not None:
                    return self._answer_quiz(line)
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
            f"  {green('peano')} {dim('<n>')}        Peano SUCC/ZERO ↔ Church numeral",
            f"  {green('decode')} {dim('<term>')}    normalize and read off a number / boolean",
            f"  {green('alpha')} {dim('<t> = <t>')}  are two terms the same function? (α-equivalence)",
            f"  {green('lean')} {dim('[name]')}      show a course Lean snippet, read-only",
            f"  {green('kb')} {dim('[topic]')}       look up a concept (knowledge base)",
            f"  {green('quiz')}              a self-check question (answer with a term)",
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

    def cmd_lean(self, arg: str) -> str:
        name = arg.strip().lower().replace("-", "_")
        if name in LEAN_SNIPPETS:
            title, code = LEAN_SNIPPETS[name]
            rows = [bold(magenta("Lean 4")) + dim("  · " + title)]
            for ln in code.strip("\n").splitlines():
                rows.append("  " + cyan(ln))
            rows.append(dim("  (the browser can't run the Lean kernel — this is the real source; "
                            "build it with ") + bold("lake build") + dim(" in artifacts/lean)"))
            return _lines(*rows)
        rows = [bold(magenta("Lean 4")) + dim("  · the course's verified snippets")]
        if name:
            rows.append(red(f"no baked snippet named {name!r}. ") + dim("Available:"))
        else:
            rows.append(dim("Available snippets — try ") + yellow("lean s_comb") + dim(", ") + yellow("lean add_comm") + dim(":"))
        rows.append("  " + "  ".join(green(k) for k in sorted(LEAN_SNIPPETS)))
        rows.append(dim("  Full artifact (Lean/Agda/Rocq/Mizar): ") + blue("github.com/nasqret/vietnam2026/tree/main/artifacts"))
        rows.append(dim("  Run Lean live in a browser editor: ") + blue("live.lean-lang.org"))
        return _lines(*rows)

    def cmd_peano(self, arg: str) -> str:
        a = arg.strip()
        if not a.lstrip("-").isdigit():
            return yellow("Usage: ") + "peano <n>   e.g.  peano 3   (Peano SUCC/ZERO ↔ Church numeral)"
        n = int(a)
        if n < 0 or n > MAX_NUMERAL:
            return red(f"Use 0..{MAX_NUMERAL}.")
        peano_expr = "ZERO" if n == 0 else ("SUCC (" * n) + "ZERO" + (")" * n)
        t = church.church(n)
        return _lines(
            bold(f"Peano ↔ Church for {n}"),
            "  Peano:  " + yellow(peano_expr),
            "  Church: " + cyan(lc.pretty(t)),
            dim("  SUCC = λn f x. f (n f x)   ·   ZERO = λf x. x"),
        )

    def _desktop_only(self, cmd: str) -> str:
        hint = {
            "ch": " — Curry-style type inference; see Lecture 1 for the theory.",
            "kb": " — the knowledge base; browse the book at /vietnam2026/book instead.",
            "tutorial": " — guided tutorials; try the book chapters.",
            "quiz": " — quizzes; ", "games": " — proof games; ",
            "eml": " — the EML explorer; see nasqret.github.io/eml-formalization.",
            "aristotle": " — the Aristotle AI prover; needs a network model.",
        }.get(cmd, ".")
        return _lines(
            yellow(f"'{cmd}'") + dim(" lives in the full desktop Lambda Lab ") + blue("(github.com/nasqret/falenty-2026)") + dim(hint),
            dim("This in-browser lab covers: ") + green("reduce nf church numeral peano lam expand decode alpha lean tour") + dim(". Type ") + bold("help") + dim("."),
        )

    def cmd_kb(self, arg: str) -> str:
        q = arg.strip().lower().replace(" ", "-")
        if not q:
            return _lines(
                bold(magenta("Knowledge base")) + dim("  · kb <topic>"),
                "  " + "  ".join(green(k) for k in KB),
                dim("  e.g. ") + yellow("kb curry-howard") + dim("  ·  ") + yellow("kb y-combinator"),
            )
        key = q if q in KB else (next((k for k in KB if k.startswith(q)), None)
                                 or next((k for k in KB if q in k), None))
        if key is None:
            return red(f"No entry for {arg.strip()!r}. ") + dim("Try ") + bold("kb") + dim(" for the list.")
        title, body = KB[key]
        return _lines(bold(magenta(title)), "  " + body)

    def cmd_quiz(self, arg: str) -> str:
        if arg.strip().lower() in ("stop", "quit", "off"):
            self.quiz = None
            return dim("quiz closed.")
        q, ans = QUIZ_QS[self.quiz_idx % len(QUIZ_QS)]
        self.quiz_idx += 1
        self.quiz = ans
        return _lines(
            bold(magenta("Quiz")) + dim(f"  · question {self.quiz_idx}"),
            "  " + q,
            dim("  answer with a λ-term or number, then Enter   (") + yellow("quiz stop") + dim(" to end)"),
        )

    def _answer_quiz(self, line: str) -> str:
        expected = self.quiz or ""
        self.quiz = None
        nxt = dim("  type ") + bold("quiz") + dim(" for the next question.")
        if line.strip().upper() == expected.strip().upper():
            return _lines(green("✓ correct!"), nxt)
        try:
            got = lc.normalize(parse(_prepare(line.strip())), max_steps=1000)
            want = lc.normalize(parse(_prepare(expected)), max_steps=1000)
        except Exception:
            return _lines(red("Could not read that as a term.") + dim(" (expected ") + cyan(expected) + dim(")"), nxt)
        if lc.alpha_eq(got, want):
            return _lines(green("✓ correct!") + dim("  " + lc.pretty(got)), nxt)
        return _lines(
            red("✗ not quite.") + dim("  you gave ") + cyan(lc.pretty(got)),
            dim("  expected ") + cyan(lc.pretty(want)),
            nxt,
        )

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
