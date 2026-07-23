"""Browser REPL driver for Lambda Lab.

The browser build is client-side and intentionally excludes desktop-only
features that need a Lean process, local data files, or network models.
The reducer implemented here is beta reduction. Eta conversion is explained
in the knowledge base but is not silently mixed into normalization.
"""

from __future__ import annotations

import re
from typing import List, Optional

from lambda_lab.lab import church, lc
from lambda_lab.lab.parser import ParseError, parse

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
MAX_INPUT = 4_000
MAX_NUMERAL = 24
MAX_NODES = 20_000
MAX_REDUCTION_NODES = 50_000
MAX_TRACE = 60
MAX_NORMALIZE = 1_000
MAX_RENDER_CHARS = 12_000
MAX_TRACE_OUTPUT_CHARS = 180_000

_NEGATIVE_LITERAL = re.compile(r"(?<![\w'])-\d+(?![\w'])", re.UNICODE)
_POSITIVE_LITERAL = re.compile(r"(?<![\w'])\d+(?![\w'])", re.UNICODE)

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

DESKTOP_ONLY = {"ch", "tutorial", "games", "eml", "prove",
                "aristotle", "ag", "acorn", "lang"}

KB = {
    "beta-reduction": ("β-reduction", "The computational rule: (λx.t) u → t[x:=u]. Repeated β-reduction is computation; a term with no β-redex is a β-normal form."),
    "alpha-equivalence": ("α-equivalence", "Renaming bound variables leaves a term unchanged: λx.x ≡α λy.y. Bound names carry no meaning. The alpha command checks only this relation."),
    "substitution": ("Capture-avoiding substitution", "t[x:=u] replaces free x by u, renaming bound variables so no free variable of u is captured."),
    "eta": ("η-conversion", "Extensionality: λx.(t x) ≡η t when x is not free in t. This browser reducer is β-only; η is explained but not applied automatically."),
    "normal-form": ("Normal form", "A β-normal form has no β-redex. By Church–Rosser it is unique up to α when it exists. Ω has no β-normal form."),
    "church-rosser": ("Church–Rosser (confluence)", "If t reduces to u1 and u2, both reduce to a common term. Consequently, any β-normal form is unique up to α."),
    "church-encoding": ("Church encoding", "Data as pure functions: true=λt f.t, false=λt f.f, numeral n=λf x.fⁿx. In the untyped calculus FALSE and numeral 0 are the same term."),
    "church-numeral": ("Church numeral", "n = λf x. fⁿx — apply f to x exactly n times. Try: church 3 or peano 3."),
    "y-combinator": ("Y-combinator", "Y f →β f (Y f), providing fixed points and recursion in the untyped calculus."),
    "curry-howard": ("Curry–Howard correspondence", "Propositions correspond to types and proofs to terms; β-reduction corresponds to proof normalization."),
    "type-judgment": ("Typing judgment", "Γ ⊢ t : A means that term t has type A in context Γ."),
    "stlc": ("Simply-typed λ-calculus", "Types A ::= o | A→B. Every well-typed term is strongly normalizing, so Y is untypable in STLC."),
    "dependent-type": ("Dependent type", "A type may depend on a term: Π generalizes functions/universal quantification and Σ generalizes pairs/existential quantification."),
    "s-combinator": ("The S combinator", "S f g x = f x (g x). Its Curry–Howard type is a tautology whose proof term is S."),
    "lean": ("Lean 4", "A proof assistant based on the Calculus of Inductive Constructions. Lean's kernel is constructive; classical principles are available explicitly and are widely used in Mathlib."),
    "autoformalization": ("Autoformalization", "Natural-language statements or proofs are translated into formal syntax; the kernel, not the model, decides whether the result checks."),
    "eml": ("EML project", "A Lean 4 formalization used as the course capstone. See the linked repository for the machine-checked source and current counts."),
    "free-variables": ("Free and bound variables", "An occurrence is bound by its nearest enclosing binder of the same name; otherwise it is free. Shadowing therefore matters."),
    "bhk": ("BHK interpretation", "A proof of A∧B is a pair, of A∨B a tagged choice, of A→B a construction transforming proofs, and of ⊥ no construction."),
    "natural-deduction": ("Natural deduction", "Connectives have introduction rules for constructing proofs and elimination rules for using them."),
    "intuitionistic": ("Intuitionistic vs classical", "Intuitionistic logic does not accept excluded middle or double-negation elimination without an additional principle."),
    "church-vs-curry": ("Church vs Curry typing", "Church-style terms carry type annotations. Curry-style systems infer types for unannotated terms; principal typing in STLC is related to, but not identical with, Hindley–Milner let-polymorphism."),
    "mltt": ("Martin-Löf Type Theory", "MLTT uses dependent Π/Σ types, identity types, inductive types and a hierarchy of universes."),
    "four-foundations": ("Four foundations", "Lean and Rocq use CIC, Agda is based on MLTT, and Mizar uses set-theoretic foundations."),
    "mathlib": ("Mathlib", "Lean's community mathematics library. Counts change rapidly; consult Mathlib's own statistics for current figures."),
    "tactic-mode": ("Term mode vs tactic mode", "A term and a tactic script ultimately construct kernel-checkable proof terms."),
    "agda": ("Agda", "A dependently typed programming language and proof assistant based on Martin-Löf type theory."),
    "mizar": ("Mizar", "A declarative proof system based on classical first-order set theory rather than propositions-as-types."),
}

QUIZ_QS = [
    ("Reduce AND TRUE TRUE — what Church boolean do you get?", "TRUE"),
    ("What is PLUS 2 2 as a Church numeral?", "4"),
    ("Reduce NOT FALSE.", "TRUE"),
    ("Normal form of (\\x. x) (\\y. y)?", "\\y. y"),
    ("What is MULT 2 3?", "6"),
    ("Reduce FST (PAIR TRUE FALSE).", "TRUE"),
    ("What is PRED 3?", "2"),
    ("Is OR FALSE FALSE true or false?", "FALSE"),
    ("What is SUCC (SUCC 0)?", "2"),
    ("What is POW 2 3?", "8"),
    ("Reduce AND FALSE TRUE.", "FALSE"),
    ("What is SUB 5 2?", "3"),
    ("Reduce SND (PAIR TRUE FALSE).", "FALSE"),
    ("Is ISZERO 0 TRUE or FALSE?", "TRUE"),
    ("Is ISZERO 2 TRUE or FALSE?", "FALSE"),
    ("What is MULT 3 3?", "9"),
]


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _render(t: lc.Term) -> str:
    text = lc.pretty(t)
    if len(text) <= MAX_RENDER_CHARS:
        return text
    omitted = len(text) - MAX_RENDER_CHARS
    return text[:MAX_RENDER_CHARS] + f" … [{omitted} characters omitted]"


def _term(t: lc.Term) -> str:
    return cyan(_render(t))


def _expand_numbers(src: str) -> str:
    if _NEGATIVE_LITERAL.search(src):
        raise ValueError("A Church numeral must be non-negative.")

    def repl(match: re.Match[str]) -> str:
        n = int(match.group())
        if n > MAX_NUMERAL:
            raise ValueError(f"numeral {n} is too large for the browser (max {MAX_NUMERAL})")
        return f"({church.church_numeral_src(n)})"

    return _POSITIVE_LITERAL.sub(repl, src)


def _parse_term(src: str) -> lc.Term:
    if len(src) > MAX_INPUT:
        raise ValueError(f"input is too long for the browser (max {MAX_INPUT} characters)")
    term = church.expand_term(parse(_expand_numbers(src)))
    if lc.term_size(term, stop_after=MAX_NODES) > MAX_NODES:
        raise ValueError(f"expanded term is too large for the browser (max {MAX_NODES} AST nodes)")
    return term


def _decode_note_nf(t: lc.Term) -> Optional[str]:
    n = church.decode_numeral_nf(t)
    b = church.decode_bool_nf(t)
    if n == 0 and b is False:
        return f"{green('= 0 / FALSE')}  {dim('(the same untyped Church term)')}"
    if n is not None:
        return f"{green('= ' + str(n))}  {dim('(Church numeral)')}"
    if b is not None:
        return f"{green('= ' + ('TRUE' if b else 'FALSE'))}  {dim('(Church boolean)')}"
    return None


def _split_equation(arg: str) -> tuple[str, str]:
    if "=" not in arg:
        raise ValueError("expected two terms separated by '='")
    left, right = arg.split("=", 1)
    if not left.strip() or not right.strip():
        raise ValueError("both sides of '=' must contain a term")
    return left.strip(), right.strip()


class LabSession:
    def __init__(self) -> None:
        self.history: List[str] = []
        self.quiz: Optional[str] = None
        self.quiz_idx = 0

    def run(self, line: str) -> str:
        line = (line or "").strip()
        if not line:
            return ""
        if len(line) > MAX_INPUT:
            return red(f"Input is too long (max {MAX_INPUT} characters).")
        self.history.append(line)
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        try:
            handler = getattr(self, f"cmd_{cmd}", None)
            if handler is None:
                if cmd in DESKTOP_ONLY:
                    return self._desktop_only(cmd)
                if self.quiz is not None:
                    return self._answer_quiz(line)
                # A bare lambda term may be an application such as `x y`.
                return self.cmd_reduce(line)
            return handler(arg)
        except ParseError as exc:
            return red("Parse error: ") + str(exc)
        except RecursionError:
            return red("The term is too deeply nested for the browser sandbox.")
        except ValueError as exc:
            return red("Error: ") + str(exc)
        except Exception as exc:  # keep the REPL alive while surfacing the error
            return red(f"{type(exc).__name__}: {exc}")

    def cmd_help(self, arg: str) -> str:
        del arg
        return _lines(
            bold(magenta("Lambda Lab") + " — commands"), "",
            f"  {green('reduce')} {dim('<term>')}    step-by-step β-reduction (or type a bare term)",
            f"  {green('nf')} {dim('<term>')}        β-normal form, with an explicit fuel status",
            f"  {green('whnf')} {dim('<term>')}      weak-head normal form (does not reduce under λ)",
            f"  {green('lam')} {dim('<term>')}       parse, pretty-print and list free variables",
            f"  {green('expand')} {dim('<term>')}    scope-safely expand free named constants",
            f"  {green('church')} {dim('<NAME|n>')}  show a Church constant or numeral",
            f"  {green('numeral')} {dim('<n>')}      show Church numeral n",
            f"  {green('peano')} {dim('<n>')}        Peano SUCC/ZERO ↔ Church numeral",
            f"  {green('decode')} {dim('<term>')}    normalize and decode a numeral / boolean",
            f"  {green('alpha')} {dim('<t> = <u>')}  strict α-equivalence (renaming only)",
            f"  {green('equiv')} {dim('<t> = <u>')}  compare β-normal forms up to α",
            f"  {green('lean')} {dim('[name]')}      show a course Lean snippet, read-only",
            f"  {green('kb')} {dim('[topic]')}       look up a concept",
            f"  {green('quiz')}              self-check question",
            f"  {green('constants')}         list named constants",
            f"  {green('tour')}              guided tour",
            f"  {green('about')}             architecture and limitations",
            f"  {green('clear')}             clear the terminal", "",
            dim("Terms use ") + cyan("λx. x") + dim(" or ") + cyan("\\x. x") + dim("; integers become Church numerals."),
            dim("Try: ") + yellow("reduce AND TRUE FALSE") + dim(" · ") + yellow("nf PLUS 2 3") + dim(" · ") + yellow("equiv SUCC 2 = 3"),
        )

    cmd_commands = cmd_help

    def cmd_about(self, arg: str) -> str:
        del arg
        return _lines(
            bold(magenta("Lambda Lab")) + dim(" · client-side Pyodide + xterm.js"), "",
            "The Python engine runs inside Pyodide's WebAssembly-hosted CPython runtime.",
            "Terms typed at the terminal stay in this browser. A ?cmd= deep link is part of the URL and may be logged by the host.",
            "The implemented evaluator performs capture-avoiding normal-order β-reduction.",
            "η-conversion is discussed as mathematics but is not applied automatically.", "",
            dim("Course: ") + blue("https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026/"),
            dim("Source: ") + blue("https://github.com/nasqret/vietnam2026"),
        )

    def cmd_constants(self, arg: str) -> str:
        del arg
        groups = [
            ("Booleans", ["TRUE", "FALSE", "IF", "AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR", "IMPLIES", "IFF"]),
            ("Pairs", ["PAIR", "FST", "SND"]),
            ("Numerals & arithmetic", ["0", "ZERO", "SUCC", "PRED", "PLUS", "SUB", "MULT", "POW", "ISZERO", "LEQ", "EQ"]),
            ("Recursion & divergence", ["Y", "Z", "OMEGA"]),
        ]
        rows = [bold(magenta("Named constants")), ""]
        for title, names in groups:
            rows.extend(("  " + bold(title), "    " + "  ".join(green(n) for n in names), ""))
        rows.append(dim("Use ") + yellow("church <NAME>") + dim(" to inspect one."))
        return _lines(*rows)

    def cmd_church(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "church <NAME|n>"
        name = arg.strip()
        if name.lstrip("-").isdigit():
            n = int(name)
            if n < 0:
                return red("A Church numeral must be non-negative.")
            if n > MAX_NUMERAL:
                return red(f"Keep it ≤ {MAX_NUMERAL} in the browser.")
            t = church.church(n)
            return _lines(bold(f"Church numeral {n}"), "  " + _term(t))
        key = name.upper() if name.upper() in church.CONSTANTS else name
        if key not in church.CONSTANTS:
            return red(f"No constant named {name!r}. ") + dim("Try ") + bold("constants") + dim(".")
        expanded = church.expand(key)
        rows = [
            bold(magenta(key)),
            dim("  conceptual:  ") + cyan(church.CONSTANTS[key].replace("\\", "λ")),
            dim("  full λ-term: ") + _term(expanded),
        ]
        if lc.beta_step(expanded) is None:
            note = _decode_note_nf(expanded)
            if note:
                rows.append("  " + note)
        return _lines(*rows)

    def cmd_numeral(self, arg: str) -> str:
        if not arg.strip().lstrip("-").isdigit():
            return yellow("Usage: ") + "numeral <n>"
        return self.cmd_church(arg)

    def cmd_expand(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "expand <term>"
        return _lines(bold("Expanded free constants to raw λ-terms:"), "  " + _term(_parse_term(arg)))

    def cmd_lam(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "lam <term>"
        t = _parse_term(arg)
        fv = sorted(lc.free_vars(t))
        return _lines(
            bold("Parsed term"),
            "  λ-notation: " + _term(t),
            "  ASCII:      " + cyan(lc.show_ascii(t)),
            "  free vars:  " + (yellow(", ".join(fv)) if fv else dim("(none — closed term)")),
        )

    def cmd_reduce(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "reduce <term>"
        t = _parse_term(arg)
        rows = [bold("β-reduction") + dim(" (normal order)"), "  " + dim("start: ") + _term(t)]
        rendered = sum(len(row) for row in rows)
        output_truncated = False
        last = t
        steps = 0
        for step in lc.trace_steps(t, max_steps=MAX_TRACE):
            steps += 1
            last = step.after
            if lc.term_size(last, stop_after=MAX_REDUCTION_NODES) > MAX_REDUCTION_NODES:
                rows.append("  " + yellow(f"… stopped at {steps} steps: intermediate term exceeded {MAX_REDUCTION_NODES:,} AST nodes."))
                output_truncated = True
                break
            if not output_truncated:
                row = f"  {dim('→β')}      " + cyan(_render(last))
                if rendered + len(row) <= MAX_TRACE_OUTPUT_CHARS:
                    rows.append(row)
                    rendered += len(row)
                else:
                    rows.append("  " + yellow("… intermediate trace output omitted (display budget reached)."))
                    output_truncated = True
        node_limited = lc.term_size(last, stop_after=MAX_REDUCTION_NODES) > MAX_REDUCTION_NODES
        complete = (not node_limited) and lc.beta_step(last) is None
        if steps == 0:
            rows.append("  " + dim("already in β-normal form."))
        elif complete:
            rows.append("  " + green(f"β-normal form reached in {steps} step(s)."))
        elif node_limited:
            rows.append("  " + yellow("The displayed term is partial because the AST size limit was reached."))
        else:
            rows.append("  " + yellow(f"… stopped after {MAX_TRACE} steps; the displayed term is partial."))
        if complete:
            note = _decode_note_nf(last)
            if note:
                rows.append("  " + note)
        return _lines(*rows)

    cmd_red = cmd_reduce
    cmd_r = cmd_reduce

    def cmd_nf(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "nf <term>"
        result = lc.normalize_checked(_parse_term(arg), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        if not result.complete:
            return _lines(
                bold("Reduction limit reached") + dim(f" after {result.steps} β-step(s)"),
                "  " + yellow(("Intermediate term exceeded the AST size limit." if result.reason == "node-limit" else "Step limit reached.") + " This is not claimed to be a normal form:"),
                "  " + _term(result.term),
            )
        rows = [bold("β-normal form") + dim(f" · {result.steps} step(s)"), "  " + _term(result.term)]
        note = _decode_note_nf(result.term)
        if note:
            rows.append("  " + note)
        return _lines(*rows)

    def cmd_whnf(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "whnf <term>"
        result = lc.whnf_checked(_parse_term(arg), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        title = "Weak-head normal form" if result.complete else "WHNF reduction limit reached"
        return _lines(bold(title) + dim(f" · {result.steps} step(s)"), "  " + _term(result.term))

    def cmd_decode(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "decode <term>"
        result = lc.normalize_checked(_parse_term(arg), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        if not result.complete:
            return yellow("Inconclusive: the β-normalization limit was reached.")
        note = _decode_note_nf(result.term)
        return "  " + (note if note else dim("Not a canonical Church numeral or boolean."))

    def cmd_alpha(self, arg: str) -> str:
        left, right = _split_equation(arg)
        t1, t2 = _parse_term(left), _parse_term(right)
        same = lc.alpha_eq(t1, t2)
        return _lines(
            bold("Strict α-equivalence") + dim(" (no β or η reduction)"),
            "  left:  " + cyan(_render(t1)),
            "  right: " + cyan(_render(t2)),
            "  " + (green("≡α alpha-equivalent") if same else red("≢α not alpha-equivalent")),
        )

    def cmd_equiv(self, arg: str) -> str:
        left, right = _split_equation(arg)
        r1 = lc.normalize_checked(_parse_term(left), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        r2 = lc.normalize_checked(_parse_term(right), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        if not r1.complete or not r2.complete:
            return yellow("Inconclusive: at least one side did not reach β-normal form within the limit.")
        same = lc.alpha_eq(r1.term, r2.term)
        return _lines(
            bold("β-convertibility by normal forms") + dim(" (η is not used)"),
            "  left NF:  " + cyan(_render(r1.term)),
            "  right NF: " + cyan(_render(r2.term)),
            "  " + (green("equal β-normal forms up to α") if same else red("different β-normal forms")),
        )

    cmd_eq = cmd_equiv

    def cmd_lean(self, arg: str) -> str:
        name = arg.strip().lower().replace("-", "_")
        if name in LEAN_SNIPPETS:
            title, code = LEAN_SNIPPETS[name]
            rows = [bold(magenta("Lean 4")) + dim(" · " + title)]
            rows.extend("  " + cyan(line) for line in code.strip("\n").splitlines())
            rows.append(dim("  Read-only source: verify it with the repository's Lean build."))
            return _lines(*rows)
        rows = [bold(magenta("Lean 4")) + dim(" · available snippets")]
        if name:
            rows.append(red(f"No baked snippet named {name!r}."))
        rows.append("  " + "  ".join(green(k) for k in sorted(LEAN_SNIPPETS)))
        return _lines(*rows)

    def cmd_peano(self, arg: str) -> str:
        a = arg.strip()
        if not a.lstrip("-").isdigit():
            return yellow("Usage: ") + "peano <n>"
        n = int(a)
        if n < 0 or n > MAX_NUMERAL:
            return red(f"Use 0..{MAX_NUMERAL}.")
        peano_expr = "ZERO" if n == 0 else ("SUCC (" * n) + "ZERO" + (")" * n)
        return _lines(
            bold(f"Peano ↔ Church for {n}"),
            "  Peano:  " + yellow(peano_expr),
            "  Church: " + cyan(lc.pretty(church.church(n))),
            dim("  Both ZERO and 0 expand to λf x. x."),
        )

    def _desktop_only(self, cmd: str) -> str:
        return _lines(
            yellow(f"'{cmd}'") + dim(" belongs to the full desktop Lambda Lab."),
            dim("This browser build is deliberately static and local-only. Type ") + bold("help") + dim("."),
        )

    def cmd_kb(self, arg: str) -> str:
        q = arg.strip().lower().replace(" ", "-")
        if not q:
            return _lines(
                bold(magenta("Knowledge base")) + dim(" · kb <topic>"),
                "  " + "  ".join(green(k) for k in KB),
            )
        key = q if q in KB else (next((k for k in KB if k.startswith(q)), None)
                                 or next((k for k in KB if q in k), None))
        if key is None:
            return red(f"No entry for {arg.strip()!r}. ") + dim("Try ") + bold("kb") + dim(".")
        title, body = KB[key]
        return _lines(bold(magenta(title)), "  " + body)

    def cmd_quiz(self, arg: str) -> str:
        if arg.strip().lower() in ("stop", "quit", "off"):
            self.quiz = None
            return dim("quiz closed.")
        q, answer = QUIZ_QS[self.quiz_idx % len(QUIZ_QS)]
        self.quiz_idx += 1
        self.quiz = answer
        return _lines(
            bold(magenta("Quiz")) + dim(f" · question {self.quiz_idx}"),
            "  " + q,
            dim("  answer with a λ-term or number; use ") + yellow("quiz stop") + dim(" to end"),
        )

    def _answer_quiz(self, line: str) -> str:
        expected = self.quiz or ""
        self.quiz = None
        nxt = dim("  type ") + bold("quiz") + dim(" for the next question.")
        if line.strip().upper() == expected.strip().upper():
            return _lines(green("✓ correct!"), nxt)
        try:
            got = lc.normalize_checked(_parse_term(line.strip()), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
            want = lc.normalize_checked(_parse_term(expected), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        except Exception:
            return _lines(red("Could not read that as a term.") + dim(" Expected ") + cyan(expected) + dim("."), nxt)
        if not got.complete or not want.complete:
            return _lines(yellow("Inconclusive: normalization reached the browser limit."), nxt)
        if lc.alpha_eq(got.term, want.term):
            return _lines(green("✓ correct!") + dim(" " + _render(got.term)), nxt)
        return _lines(
            red("✗ not quite.") + dim(" You gave ") + cyan(_render(got.term)),
            dim("  expected ") + cyan(_render(want.term)),
            nxt,
        )

    def cmd_tour(self, arg: str) -> str:
        del arg
        demos = [
            ("Identity applied to a variable", "(\\x. x) y"),
            ("Church boolean AND", "AND TRUE FALSE"),
            ("Successor of 2", "SUCC 2"),
            ("2 + 3", "PLUS 2 3"),
            ("2 × 3", "MULT 2 3"),
            ("Exponent zero", "POW 2 0"),
        ]
        rows = [bold(magenta("A guided tour")), dim("Each expression is normalized with an explicit limit:"), ""]
        for title, expr in demos:
            result = lc.normalize_checked(_parse_term(expr), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
            if result.complete:
                note = _decode_note_nf(result.term)
                suffix = "   " + note if note else ""
                value = cyan(_render(result.term)) + suffix
            else:
                value = yellow("limit reached")
            rows.extend(("  " + bold(title), "    " + yellow(expr) + dim(" ⇝ ") + value, ""))
        rows.append(dim("Try ") + yellow("reduce AND TRUE FALSE") + dim(" to inspect each β-step."))
        return _lines(*rows)


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
        magenta(bold("  λ  Lambda Lab")) + dim(" · in-browser β-reduction · VIASM 2026"),
        dim("  Python in Pyodide; terms typed at the prompt remain in this browser"), "",
        dim("  type ") + bold(green("help")) + dim(" to begin, or ") + bold(green("tour")) + dim(" for a quick taste."), "",
    )
