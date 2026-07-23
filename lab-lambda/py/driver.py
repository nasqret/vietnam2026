"""Browser REPL driver for Lambda Lab.

The browser build is client-side and intentionally excludes desktop-only
features that need a Lean process, local data files, or network models.
The reducer implemented here is beta reduction. Eta conversion is explained
in the knowledge base but is not silently mixed into normalization.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import List, Optional

from lambda_lab.lab import church, lc
from lambda_lab.lab.parser import ParseError, parse
from lambda_lab.lab.webport import ag as web_ag
from lambda_lab.lab.webport import ch as web_ch
from lambda_lab.lab.webport import alligators as web_alligators
from lambda_lab.lab.webport import kb as web_kb
from lambda_lab.lab.webport import prove as web_prove
from lambda_lab.lab.webport import quiz as web_quiz
from lambda_lab.lab.webport import tutorial as web_tutorial

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

DESKTOP_ONLY = {"games", "eml", "aristotle", "acorn", "lang"}

# Per-command help: syntax, what it does, worked examples, fine print.
# Rendered by `help <command>`.
HELP_TOPICS = {
    "reduce": {
        "syntax": "reduce <term>     (aliases: red, r — or just type the term)",
        "what": "Step-by-step β-reduction in normal order (leftmost-outermost), one line per step, "
                "with an honest status: normal form reached, or stopped at the step/size limit.",
        "examples": [
            ("reduce (\\x. x x) (\\y. y)", "self-application collapses to the identity in 2 steps"),
            ("reduce AND TRUE FALSE", "watch a Church-boolean circuit evaluate"),
            ("reduce IF TRUE a b", "the conditional selects its first branch"),
            ("PLUS 1 1", "no command needed — a bare term is reduced automatically"),
            ("reduce OMEGA", "(λx. x x)(λx. x x) loops forever; the trace stops at the limit"),
        ],
        "notes": f"Shows at most {MAX_TRACE} steps; intermediate terms are capped at "
                 f"{MAX_REDUCTION_NODES:,} AST nodes. A cut-off trace is labelled partial — "
                 "never presented as a normal form. Use nf for the result only.",
    },
    "nf": {
        "syntax": "nf <term>",
        "what": "β-normal form only (no trace), computed with a bigger fuel budget, then decoded "
                "as a Church numeral/boolean when possible.",
        "examples": [
            ("nf PLUS 2 3", "→ λf x. f (f (f (f (f x))))  = 5"),
            ("nf POW 2 5", "exponentiation by numeral application = 32"),
            ("nf PRED 3", "Kleene's predecessor trick in action = 2"),
            ("nf FST (PAIR TRUE FALSE)", "pairs are functions too → TRUE"),
            ("nf OMEGA", "honestly reports the step limit — Ω has no normal form"),
        ],
        "notes": f"Budget: {MAX_NORMALIZE:,} β-steps / {MAX_REDUCTION_NODES:,} nodes. "
                 "If the limit is hit you get 'reduction limit reached', not a fake answer.",
    },
    "whnf": {
        "syntax": "whnf <term>",
        "what": "Weak-head normal form: reduce only the head redex chain — never under a λ, never "
                "inside arguments. This is what lazy languages actually compute.",
        "examples": [
            ("whnf \\x. (\\y. y) z", "already in WHNF (the redex is under the λ) — nf would reduce it"),
            ("whnf (\\x. \\y. x) a b", "head reduction gives a without touching anything else"),
        ],
        "notes": "Contrast with nf on the same terms — the difference IS the definition.",
    },
    "lam": {
        "syntax": "lam <term>",
        "what": "Parse a term and print it in λ- and ASCII notation plus its free variables — "
                "without reducing anything.",
        "examples": [
            ("lam \\x y. x (y z)", "free variables: z"),
            ("lam \\TRUE. TRUE", "TRUE is a legal *bound* name — constants only expand when free"),
            ("lam x'2", "x'2 is one identifier, not x' applied to 2"),
        ],
        "notes": "Good first stop when a term misbehaves: check what the parser actually read.",
    },
    "expand": {
        "syntax": "expand <term>",
        "what": "Replace every *free* occurrence of a named constant (TRUE, PLUS, Y, …) by its "
                "λ-definition, scope-aware, without reducing.",
        "examples": [
            ("expand NOT p", "see the raw λ-term you would have to write by hand"),
            ("expand NAND p q", "nested definitions unfold recursively (NOT of AND)"),
            ("expand \\TRUE. TRUE", "a bound TRUE is left alone — scope matters"),
        ],
        "notes": "This is exactly the preprocessing reduce/nf apply before working.",
    },
    "church": {
        "syntax": "church <NAME|n>",
        "what": "Show a named Church constant (conceptual form + fully expanded λ-term) or the "
                "Church numeral for n, with a decoded value when it is already a normal form.",
        "examples": [
            ("church SUCC", "the successor: λn f x. f (n f x)"),
            ("church 3", "λf x. f (f (f x)) — apply f three times"),
            ("church PRED", "the famous 'hard one' (Kleene's pair trick)"),
            ("church Y", "the fixed-point combinator — shown, not normalized (it has no NF)"),
        ],
        "notes": "See `constants` for the full list. Reducible constants (Y, Z, OMEGA) are "
                 "displayed without hidden normalization, so this is always instant.",
    },
    "numeral": {
        "syntax": "numeral <n>",
        "what": "The Church numeral for n — shorthand for church <n>.",
        "examples": [("numeral 4", "λf x. f (f (f (f x)))")],
        "notes": f"n ranges 0..{MAX_NUMERAL} in the browser.",
    },
    "peano": {
        "syntax": "peano <n>",
        "what": "The same number two ways: Peano-style SUCC (SUCC (… ZERO)) and the Church numeral "
                "— the bridge between Lecture 2 and Lean's Nat in Lecture 4.",
        "examples": [("peano 3", "SUCC (SUCC (SUCC (ZERO)))  vs  λf x. f (f (f x))")],
        "notes": "Both ZERO and 0 are usable constants and expand to λf x. x.",
    },
    "decode": {
        "syntax": "decode <term>",
        "what": "Normalize the term, then read the normal form back as a Church numeral or boolean "
                "(binder-aware, so variable shadowing cannot fool it).",
        "examples": [
            ("decode SUCC (SUCC 0)", "= 2"),
            ("decode FALSE", "= 0 / FALSE — in the untyped calculus they are the SAME term"),
            ("decode \\f. \\f. f f", "not a canonical numeral: the shadowed binder is rejected"),
        ],
        "notes": "If normalization hits the limit the decode is 'inconclusive', never a guess.",
    },
    "alpha": {
        "syntax": "alpha <term> = <term>",
        "what": "STRICT α-equivalence: are the two terms identical up to renaming bound variables? "
                "No β (and no η) steps are taken.",
        "examples": [
            ("alpha \\x. x = \\y. y", "≡α — bound names carry no meaning"),
            ("alpha \\x. \\y. x = \\x. \\x. x", "NOT α-equivalent: one returns the outer, one the inner binder"),
            ("alpha SUCC 2 = 3", "NOT α-equivalent as raw terms — that's a β question; use equiv"),
        ],
        "notes": "The classic exam trap is the middle example. For 'same value after computing', "
                 "you want equiv.",
    },
    "equiv": {
        "syntax": "equiv <term> = <term>",
        "what": "β-convertibility via normal forms: normalize both sides (bounded), then compare "
                "up to α. Reports 'inconclusive' if either side hits the fuel limit.",
        "examples": [
            ("equiv SUCC 2 = 3", "equal β-normal forms — the arithmetic checks out"),
            ("equiv NAND TRUE TRUE = NOT TRUE", "verify a Boolean identity on actual values"),
            ("equiv POW 2 0 = 1", "the η-long POW makes exponent zero come out right"),
            ("equiv OMEGA = OMEGA", "inconclusive — neither side has a normal form"),
        ],
        "notes": "η is NOT used: λx. f x and f are not identified. Strict renaming-only "
                 "comparison is alpha.",
    },
    "lean": {
        "syntax": "lean [name]",
        "what": "Show one of the course's Lean 4 snippets (read-only) with a live.lean-lang.org "
                "link that opens the exact code in the Lean web editor, where you can RUN it.",
        "examples": [
            ("lean", "list the available snippets"),
            ("lean s_comb", "the S combinator — the proof term IS the program"),
            ("lean add_comm", "commutativity of + by induction, NNG-style"),
            ("lean eval", "the EML-in-miniature expression evaluator from the artifacts"),
        ],
        "notes": "The Lean kernel itself cannot run inside this page; the Live Lean link is the "
                 "one-click way to actually check the snippet.",
    },
    "kb": {
        "syntax": "kb [topic]  ·  kb search <text>  ·  kb show <id>",
        "what": "The knowledge base, ported from the desktop lab: concept explanations plus a "
                "searchable registry of books, courses and papers with readings per topic.",
        "examples": [
            ("kb", "list topics by category"),
            ("kb curry-howard", "propositions-as-types in one breath, with readings"),
            ("kb search induction", "full-text search across the registry"),
            ("kb show macbeth-mechanics-of-proof", "one entry in detail"),
        ],
        "notes": "Topics use kebab-case; prefix/substring match is accepted.",
    },
    "quiz": {
        "syntax": "quiz [bundle]  ·  quiz bundles · skip · hint · score · stop",
        "what": "The desktop quiz engine (9 bundles, ~290 questions): multiple-choice, true/false "
                "and open questions. Term answers are graded up to α-equivalence after "
                "normalization; score is kept for the session.",
        "examples": [
            ("quiz", "next question from the current bundle"),
            ("quiz bundles", "list all bundles — from intro_lambda to final_exam"),
            ("quiz church_essentials", "switch bundle"),
            ("quiz score", "how you are doing"),
        ],
        "notes": "The desktop's LLM judge is not available in the browser; grading is exact/α-β "
                 "equivalence. Commands still work mid-question.",
    },
    "ch": {
        "syntax": "ch term <λ-term>  ·  ch type <TYPE>  ·  ch build <TYPE>  ·  ch lib · tactic · lean · explore",
        "what": "Curry-style types (the Lecture 1 engine): principal-type inference (Algorithm W) "
                "for untyped terms, and inhabitation search for implicational propositions — "
                "provability in intuitionistic logic, live.",
        "examples": [
            ("ch term \\p. p", "principal type α → α"),
            ("ch term \\x. x x", "untypable — self-application has no simple type"),
            ("ch type (P -> Q) -> P -> P", "inhabited; the witness term is printed"),
            ("ch type ((P -> Q) -> P) -> P", "Peirce's law: UNINHABITED constructively"),
            ("ch build P -> Q -> P", "interactive: build the inhabitant tactic by tactic"),
        ],
        "notes": "The kb/`prove` cross-references apply; `ch verify` (Lean check) is desktop-only "
                 "but every result links to Live Lean.",
    },
    "prove": {
        "syntax": "prove <prop>  ·  then tactics: intro/intros/exact/apply/refine/assumption · hint · undo · qed · abort",
        "what": "The interactive Curry–Howard proof builder: state a proposition, prove it tactic "
                "by tactic, watch the λ-term grow hole by hole (?₀, ?₁, …), and extract the "
                "finished proof term — the program your proof IS.",
        "examples": [
            ("prove (P -> Q) -> P -> Q", "then: intro f · intro p · apply f · exact p · qed"),
            ("prove P -> Q -> P", "the K combinator, discovered interactively"),
            ("hint", "mid-proof: ask the Wajsberg proof search for the next move"),
        ],
        "notes": "Implicational fragment (→), like the desktop builder. qed prints the λ-term, "
                 "the proposition, and its principal type.",
    },
    "tutorial": {
        "syntax": "tutorial  ·  tutorial <n|name>  ·  then: answers · hint · skip · quit",
        "what": "Twelve guided walkthroughs from the desktop lab — Gauss's sum, √2 irrational, "
                "pigeonhole, Euclid's primes, AM-GM, Bézout, Cauchy–Schwarz, Fibonacci, Wilson, "
                "Euler's identity — each a stepwise dialogue with checked answers.",
        "examples": [
            ("tutorial", "list chapters with your progress"),
            ("tutorial 2", "√2 is irrational, step by step"),
            ("hint", "stuck mid-step? ask"),
        ],
        "notes": "Progress lasts for this browser session.",
    },
    "alligators": {
        "syntax": "alligators <term>",
        "what": "Bret Victor's Alligator Eggs: render a term as nested alligator families — a "
                "hungry alligator per λ, an egg per variable — the visual λ-calculus.",
        "examples": [
            ("alligators \\x. x", "one hungry alligator guarding one egg"),
            ("alligators (\\x. x x) (\\y. y)", "a family about to feed"),
        ],
        "notes": "Pure visualization; feeding (β-reduction) is what `reduce` shows textually.",
    },
    "ag": {
        "syntax": "ag  ·  ag <name>",
        "what": "Replay a pre-baked AlphaGeometry-style DD+AR proof step by step (Lecture 6): "
                "deductive-database steps + algebraic reasoning, as the system found them.",
        "examples": [
            ("ag", "list the available replays"),
            ("ag angle_bisector", "isosceles triangle: bisector = altitude"),
        ],
        "notes": "A replay of a recorded proof — the full AlphaGeometry stack is not (and could "
                 "not be) running in the browser.",
    },
    "constants": {
        "syntax": "constants",
        "what": "List every named constant the parser knows: booleans, pairs, numerals & "
                "arithmetic, and the fixed-point/divergence combinators.",
        "examples": [("constants", "the full table, grouped")],
        "notes": "Any of these names can appear in any term; free occurrences expand to their "
                 "λ-definitions.",
    },
    "tour": {
        "syntax": "tour",
        "what": "A guided one-minute tour: a curated sequence of reductions with commentary, "
                "each of which you can re-run yourself.",
        "examples": [("tour", "identity, AND, SUCC, PLUS, MULT, POW 2 0 — with decoded values")],
        "notes": "The best first command if you are new here.",
    },
    "about": {
        "syntax": "about",
        "what": "What this page is: architecture (Pyodide + xterm.js), privacy of typed terms, "
                "the β-only reduction contract, and links to the course.",
        "examples": [("about", "")],
        "notes": "",
    },
    "clear": {
        "syntax": "clear    (alias: cls, or Ctrl-L)",
        "what": "Clear the terminal and reprint the banner.",
        "examples": [("clear", "")],
        "notes": "",
    },
    "eta": {
        "syntax": "eta <term>",
        "what": "Opt-in η-reduction: contract λx. f x → f (when x is not free in f), step by step, "
                "to the η-normal form. No β steps are taken — reduce/nf remain β-only by design.",
        "examples": [
            ("eta \\x. f x", "one η-step to f — extensionality in action"),
            ("eta \\x. \\y. f x y", "two nested η-redexes collapse to f"),
            ("eta \\x. x x", "already η-normal: x IS free in the function part"),
            ("eta POW 2 0", "constants expand first; the η-story behind exponent zero"),
        ],
        "notes": "η identifies functions that agree on all arguments. The lab keeps it separate "
                 "from β so that 'normal form' always means exactly β-normal form.",
    },
    "debruijn": {
        "syntax": "debruijn <term>",
        "what": "The nameless De Bruijn view: each bound variable becomes the number of binders "
                "between it and its own λ. Free variables keep their names.",
        "examples": [
            ("debruijn \\x. x", "λ 0"),
            ("debruijn \\x. \\y. x", "λ λ 1 — the outer binder, one λ away"),
            ("debruijn \\x. \\x. x", "λ λ 0 — shadowing resolved: the INNER x wins"),
            ("debruijn \\f x. f (f x)", "the Church numeral 2, namelessly"),
        ],
        "notes": "α-equivalence = identical nameless forms; this is literally how the `alpha` "
                 "command (and Lean's kernel) compare binders.",
    },
    "let": {
        "syntax": "let NAME = <term>     ·  see also: defs, undef",
        "what": "Define your own session constant (UPPERCASE name). The right-hand side is expanded "
                "and stored; afterwards NAME can appear in any term, exactly like TRUE or PLUS.",
        "examples": [
            ("let COMPOSE = \\f g x. f (g x)", "then: nf COMPOSE SUCC SUCC 1  → 3"),
            ("let TWICE = \\f x. f (f x)", "TWICE is Church 2 in disguise — decode TWICE"),
            ("let W = \\x. x x", "then reduce W W — your own Ω"),
        ],
        "notes": "Definitions are expanded at let-time, so they can use earlier definitions but "
                 "never form cycles. They live only in this browser session. Built-in constant "
                 "names are protected.",
    },
    "defs": {
        "syntax": "defs",
        "what": "List your session `let` definitions with their expanded λ-terms.",
        "examples": [("defs", "")],
        "notes": "",
    },
    "undef": {
        "syntax": "undef NAME",
        "what": "Remove a session definition.",
        "examples": [("undef COMPOSE", "")],
        "notes": "",
    },
    "help": {
        "syntax": "help [command]     (alias: commands)",
        "what": "Without an argument: the command overview. With a command name: this kind of "
                "detailed page — syntax, semantics, worked examples, limits.",
        "examples": [("help alpha", "why α-equivalence is stricter than you think"),
                      ("help equiv", "what 'inconclusive' means")],
        "notes": "",
    },
}
HELP_ALIASES = {"red": "reduce", "r": "reduce", "eq": "equiv", "cls": "clear",
                "commands": "help", "num": "numeral"}


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


def _expand_user(term: lc.Term, defs, bound=frozenset()) -> lc.Term:
    """Expand free occurrences of session `let`-definitions, scope-aware —
    the same shape as church.expand_term. Stored definitions are already fully
    expanded at definition time, so one pass suffices and cycles cannot occur."""
    if isinstance(term, lc.Var):
        if term.name in defs and term.name not in bound:
            return defs[term.name]
        return term
    if isinstance(term, lc.Lam):
        return lc.Lam(term.param, _expand_user(term.body, defs, bound | {term.param}))
    if isinstance(term, lc.App):
        return lc.App(_expand_user(term.fn, defs, bound), _expand_user(term.arg, defs, bound))
    raise TypeError(f"Unknown term: {term!r}")


def _parse_term(src: str, defs=None) -> lc.Term:
    if len(src) > MAX_INPUT:
        raise ValueError(f"input is too long for the browser (max {MAX_INPUT} characters)")
    term = parse(_expand_numbers(src))
    if defs:
        term = _expand_user(term, defs)
    term = church.expand_term(term)
    if lc.term_size(term, stop_after=MAX_NODES) > MAX_NODES:
        raise ValueError(f"expanded term is too large for the browser (max {MAX_NODES} AST nodes)")
    return term


_HL_OPEN, _HL_CLOSE = "\x00[", "\x00]"


def _pretty_hl(t: lc.Term, path) -> str:
    """Pretty-print with the subtree at `path` highlighted (the next redex).
    α-renames first for display (pure renaming, so the path stays valid);
    unlike lc.pretty it keeps each λ separate, which keeps paths simple."""
    t = lc._alpha_rename_unique(t)

    def walk(node, ctx, p):
        mark = (p == path)
        if isinstance(node, lc.Var):
            s = node.name
        elif isinstance(node, lc.Lam):
            s = "λ" + node.param + ". " + walk(node.body, "lam", p + (0,))
            if ctx != "top":
                s = "(" + s + ")"
        elif isinstance(node, lc.App):
            s = walk(node.fn, "app-left", p + (0,)) + " " + walk(node.arg, "app-right", p + (1,))
            s = s if ctx in ("top", "lam", "app-left") else "(" + s + ")"
        else:
            raise TypeError(f"Unknown term: {node!r}")
        return (_HL_OPEN + s + _HL_CLOSE) if mark else s

    text = walk(t, "top", ())
    # markers → ANSI: leave cyan, paint the redex, resume cyan
    return text.replace(_HL_OPEN, RESET + "\x1b[1;93m").replace(_HL_CLOSE, RESET + "\x1b[96m")


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


def _live_lean_url(code: str) -> str:
    """A live.lean-lang.org link that opens the Lean 4 web editor with this code."""
    return "https://live.lean-lang.org/#code=" + urllib.parse.quote(code, safe="")


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
        self.defs: dict = {}          # session `let` definitions: NAME -> expanded Term
        self.webstate: dict = {}      # shared state for the ported feature modules

    def _parse(self, src: str) -> lc.Term:
        return _parse_term(src, self.defs)

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
                # Interactive sessions consume raw lines (tactics, answers, …).
                if self.webstate.get("ch.interactive"):
                    return web_ch.handle(line, self.webstate)
                if web_prove.is_active(self.webstate):
                    return web_prove.handle(line, self.webstate)
                if web_tutorial.is_active(self.webstate):
                    return web_tutorial.handle(line, self.webstate)
                if web_quiz.pending(self.webstate):
                    return web_quiz.handle(line, self.webstate)
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
        topic = arg.strip().lower()
        if topic:
            key = HELP_ALIASES.get(topic, topic)
            entry = HELP_TOPICS.get(key)
            if entry is None:
                near = [k for k in HELP_TOPICS if k.startswith(topic)] or \
                       [k for k in HELP_TOPICS if topic in k]
                if len(near) == 1:
                    key, entry = near[0], HELP_TOPICS[near[0]]
                else:
                    hint = ("  did you mean: " + "  ".join(green(k) for k in near)) if near else \
                           dim("  type ") + bold("help") + dim(" for the command list.")
                    return _lines(red(f"No help topic {arg.strip()!r}."), hint)
            rows = [bold(magenta(key)) + dim("  —  " + entry["syntax"]), ""]
            rows.append("  " + entry["what"])
            if entry.get("examples"):
                rows.append("")
                rows.append("  " + bold("Examples"))
                for cmd, why in entry["examples"]:
                    rows.append("    " + yellow(cmd) + (("   " + dim("— " + why)) if why else ""))
            if entry.get("notes"):
                rows.append("")
                rows.append("  " + dim(entry["notes"]))
            return _lines(*rows)
        return _lines(
            bold(magenta("Lambda Lab") + " — commands"), "",
            f"  {green('reduce')} {dim('<term>')}    step-by-step β-reduction (or type a bare term)",
            f"  {green('nf')} {dim('<term>')}        β-normal form, with an explicit fuel status",
            f"  {green('whnf')} {dim('<term>')}      weak-head normal form (does not reduce under λ)",
            f"  {green('eta')} {dim('<term>')}       opt-in η-reduction to η-normal form",
            f"  {green('debruijn')} {dim('<term>')}  the nameless De Bruijn view of a term",
            f"  {green('let')} {dim('NAME = <t>')}   define a session constant (defs · undef)",
            f"  {green('lam')} {dim('<term>')}       parse, pretty-print and list free variables",
            f"  {green('expand')} {dim('<term>')}    scope-safely expand free named constants",
            f"  {green('church')} {dim('<NAME|n>')}  show a Church constant or numeral",
            f"  {green('numeral')} {dim('<n>')}      show Church numeral n",
            f"  {green('peano')} {dim('<n>')}        Peano SUCC/ZERO ↔ Church numeral",
            f"  {green('decode')} {dim('<term>')}    normalize and decode a numeral / boolean",
            f"  {green('alpha')} {dim('<t> = <u>')}  strict α-equivalence (renaming only)",
            f"  {green('equiv')} {dim('<t> = <u>')}  compare β-normal forms up to α",
            f"  {green('lean')} {dim('[name]')}      show a course Lean snippet, read-only",
            f"  {green('ch')} {dim('term|type <x>')} principal types & inhabitation (Curry-style)",
            f"  {green('prove')} {dim('<prop>')}     interactive Curry–Howard proof builder",
            f"  {green('tutorial')} {dim('[n]')}     guided step-by-step tutorials",
            f"  {green('alligators')} {dim('<t>')}   Alligator Eggs view of a term",
            f"  {green('ag')} {dim('[name]')}        replay an AlphaGeometry proof",
            f"  {green('kb')} {dim('[topic]')}       look up a concept",
            f"  {green('quiz')}              self-check question",
            f"  {green('constants')}         list named constants",
            f"  {green('tour')}              guided tour",
            f"  {green('about')}             architecture and limitations",
            f"  {green('clear')}             clear the terminal", "",
            dim("Terms use ") + cyan("λx. x") + dim(" or ") + cyan("\\x. x") + dim("; integers become Church numerals."),
            dim("Try: ") + yellow("reduce AND TRUE FALSE") + dim(" · ") + yellow("nf PLUS 2 3") + dim(" · ") + yellow("equiv SUCC 2 = 3"),
            dim("Details per command: ") + bold(green("help <command>")) + dim("  e.g. ") + yellow("help alpha"),
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
        return _lines(bold("Expanded free constants to raw λ-terms:"), "  " + _term(self._parse(arg)))

    def cmd_lam(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "lam <term>"
        t = self._parse(arg)
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
        t = self._parse(arg)

        def shown(term):
            """Render `term` with its next β-redex highlighted (if any)."""
            nxt = lc.beta_step(term)
            if nxt is None:
                return cyan(_render(term))
            text = _pretty_hl(term, nxt.redex_path)
            if len(text) > MAX_RENDER_CHARS + 32:  # allow for markers
                return cyan(_render(term))         # too big to highlight usefully
            return cyan(text)

        rows = [bold("β-reduction") + dim(" (normal order · ") + "\x1b[1;93m" + "highlight" + RESET + dim(" = next redex)"),
                "  " + dim("start:  ") + shown(t)]
        rendered = sum(len(row) for row in rows)
        output_truncated = False
        last = t
        steps = 0
        current = t
        while steps < MAX_TRACE:
            step = lc.beta_step(current)
            if step is None:
                break
            current = lc._apply_step(current, step.redex_path, step.after)
            steps += 1
            last = current
            if lc.term_size(last, stop_after=MAX_REDUCTION_NODES) > MAX_REDUCTION_NODES:
                rows.append("  " + yellow(f"… stopped at {steps} steps: intermediate term exceeded {MAX_REDUCTION_NODES:,} AST nodes."))
                output_truncated = True
                break
            if not output_truncated:
                row = f"  {dim('→β')}      " + shown(last)
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
        result = lc.normalize_checked(self._parse(arg), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
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
        result = lc.whnf_checked(self._parse(arg), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        title = "Weak-head normal form" if result.complete else "WHNF reduction limit reached"
        return _lines(bold(title) + dim(f" · {result.steps} step(s)"), "  " + _term(result.term))

    def cmd_eta(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "eta <term>   (opt-in η-reduction; reduce/nf stay β-only)"
        t = self._parse(arg)
        rows = [bold("η-reduction") + dim("  (λx. f x → f when x ∉ FV(f); no β steps taken)"),
                "  " + dim("start:  ") + _term(t)]
        current = t
        steps = 0
        while steps < 100:
            step = lc.eta_step(current)
            if step is None:
                break
            current = lc._apply_step(current, step.redex_path, step.after)
            steps += 1
            rows.append(f"  {dim('→η')}      " + cyan(_render(current)))
        if steps == 0:
            rows.append("  " + dim("already η-normal — no subterm has the shape λx. f x with x ∉ FV(f)."))
        else:
            rows.append("  " + green(f"η-normal form reached in {steps} step(s)."))
            hint = lc.beta_step(current)
            if hint is not None:
                rows.append("  " + dim("(the result still has β-redexes — run nf on it if you want the β-normal form)"))
        return _lines(*rows)

    def cmd_debruijn(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "debruijn <term>   e.g.  debruijn \\x. \\y. x"
        t = self._parse(arg)

        def go(node, binders, ctx):
            if isinstance(node, lc.Var):
                idx = lc._bound_index(node.name, binders)
                return str(idx) if idx is not None else node.name
            if isinstance(node, lc.Lam):
                s = "λ " + go(node.body, binders + (node.param,), "lam")
                return s if ctx in ("top", "lam") else "(" + s + ")"
            if isinstance(node, lc.App):
                s = go(node.fn, binders, "app-left") + " " + go(node.arg, binders, "app-right")
                return s if ctx in ("top", "lam", "app-left") else "(" + s + ")"
            raise TypeError(f"Unknown term: {node!r}")

        return _lines(
            bold("De Bruijn view") + dim("  (indices count binders outward, from 0)"),
            "  named:    " + _term(t),
            "  nameless: " + cyan(go(t, (), "top")),
            dim("  free variables keep their names. Two terms are α-equivalent exactly when"),
            dim("  their nameless forms are identical — this is how `alpha` decides."),
        )

    _DEF_NAME = re.compile(r"^[A-Z][A-Z0-9_']*$")

    def cmd_let(self, arg: str) -> str:
        if "=" not in arg:
            return yellow("Usage: ") + "let NAME = <term>   e.g.  let COMPOSE = \\f g x. f (g x)"
        name, rhs = arg.split("=", 1)
        name, rhs = name.strip(), rhs.strip()
        if not self._DEF_NAME.match(name):
            return red(f"Bad name {name!r}: ") + dim("use UPPERCASE letters/digits/_ starting with a letter.")
        if name in church.CONSTANTS:
            return red(f"{name} is a built-in constant — pick another name. ") + dim("See `constants`.")
        if not rhs:
            return red("Missing right-hand side.")
        value = self._parse(rhs)   # fully expanded now → later lookup is one substitution, no cycles
        self.defs[name] = value
        rows = [green(f"defined {name}") + dim(" (this session only)"), "  " + _term(value)]
        note = _decode_note_nf(value) if lc.beta_step(value) is None else None
        if note:
            rows.append("  " + note)
        rows.append(dim("  use it in any term; `defs` lists, `undef " + name + "` removes."))
        return _lines(*rows)

    def cmd_defs(self, arg: str) -> str:
        del arg
        if not self.defs:
            return dim("No session definitions yet. Create one: ") + yellow("let ID = \\x. x")
        rows = [bold(magenta("Session definitions")), ""]
        for name, term in self.defs.items():
            rows.append("  " + green(name) + dim(" = ") + cyan(_render(term)))
        return _lines(*rows)

    def cmd_undef(self, arg: str) -> str:
        name = arg.strip()
        if name in self.defs:
            del self.defs[name]
            return dim(f"removed {name}.")
        return red(f"No session definition named {name!r}. ") + dim("See `defs`.")

    def cmd_decode(self, arg: str) -> str:
        if not arg:
            return yellow("Usage: ") + "decode <term>"
        result = lc.normalize_checked(self._parse(arg), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        if not result.complete:
            return yellow("Inconclusive: the β-normalization limit was reached.")
        note = _decode_note_nf(result.term)
        return "  " + (note if note else dim("Not a canonical Church numeral or boolean."))

    def cmd_alpha(self, arg: str) -> str:
        left, right = _split_equation(arg)
        t1, t2 = self._parse(left), self._parse(right)
        same = lc.alpha_eq(t1, t2)
        return _lines(
            bold("Strict α-equivalence") + dim(" (no β or η reduction)"),
            "  left:  " + cyan(_render(t1)),
            "  right: " + cyan(_render(t2)),
            "  " + (green("≡α alpha-equivalent") if same else red("≢α not alpha-equivalent")),
        )

    def cmd_equiv(self, arg: str) -> str:
        left, right = _split_equation(arg)
        r1 = lc.normalize_checked(self._parse(left), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        r2 = lc.normalize_checked(self._parse(right), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
        if not r1.complete or not r2.complete:
            return yellow("Inconclusive: at least one side did not reach β-normal form within the limit.")
        same = lc.alpha_eq(r1.term, r2.term)
        return _lines(
            bold("β-convertibility by normal forms") + dim(" (η is not used)"),
            "  left NF:  " + cyan(_render(r1.term)),
            "  right NF: " + cyan(_render(r2.term)),
            "  " + (green("equal β-normal forms up to α") if same else red("different β-normal forms")),
        )

    def cmd_lean(self, arg: str) -> str:
        name = arg.strip().lower().replace("-", "_")
        if name in LEAN_SNIPPETS:
            title, code = LEAN_SNIPPETS[name]
            rows = [bold(magenta("Lean 4")) + dim(" · " + title)]
            rows.extend("  " + cyan(line) for line in code.strip("\n").splitlines())
            rows.append("")
            rows.append(dim("  ▶ run it in Live Lean (click / open):"))
            rows.append("  " + blue(_live_lean_url(code)))
            return _lines(*rows)
        rows = [bold(magenta("Lean 4")) + dim(" · available snippets")]
        if name:
            rows.append(red(f"No baked snippet named {name!r}."))
        rows.append("  " + "  ".join(green(k) for k in sorted(LEAN_SNIPPETS)))
        rows.append(dim("  Each snippet includes a live.lean-lang.org link you can open and run."))
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
        return web_kb.handle(arg, self.webstate)

    def cmd_quiz(self, arg: str) -> str:
        return web_quiz.handle(arg, self.webstate)

    def cmd_tutorial(self, arg: str) -> str:
        return web_tutorial.handle(arg, self.webstate)

    def cmd_prove(self, arg: str) -> str:
        return web_prove.handle(arg, self.webstate)

    def cmd_alligators(self, arg: str) -> str:
        return web_alligators.handle(arg, self.webstate)

    def cmd_ag(self, arg: str) -> str:
        return web_ag.handle(arg, self.webstate)

    def cmd_ch(self, arg: str) -> str:
        return web_ch.handle(arg, self.webstate)

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
            result = lc.normalize_checked(self._parse(expr), max_steps=MAX_NORMALIZE, max_nodes=MAX_REDUCTION_NODES)
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
