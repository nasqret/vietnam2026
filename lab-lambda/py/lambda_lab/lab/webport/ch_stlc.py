"""Simply-typed λ-calculus engine for the browser ``ch`` command.

A faithful, pure-stdlib port of three desktop modules:

* ``lambda_lab/lab/curry_howard/types.py`` — simple types (``TVar``/``Arrow``),
  the type parser (``P -> Q -> R``, right-associative, ``->`` or ``→``),
  pretty-printing with minimal parentheses, unification (MGU) and principal
  type inference in the empty context (Algorithm W, Hindley–Milner-lite:
  no let-generalisation). Fresh type variables are Greek letters α, β, γ, …
  Uppercase Latin names (``P``, ``Q``, ``R``) are atomic *constants* that
  unify only with themselves; Greek/lowercase names are unifiable variables.
* ``lambda_lab/lab/curry_howard/proof_search.py`` — Wajsberg-style proof
  search for the implicational fragment of intuitionistic logic (type
  inhabitation). Non-theorems such as Peirce ``((P → Q) → P) → P`` return
  ``None``.
* ``lambda_lab/lab/curry_howard/lean_bridge.py`` — λ ↔ Lean 4:
  ``lambda_to_lean`` emits a ``theorem`` template, ``lean_to_lambda`` parses
  the tiny ``fun x => x`` / application subset of Lean.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from lambda_lab.lab.lc import App, Lam, Term, Var


# ---------------------------------------------------------------------------
# Type AST
# ---------------------------------------------------------------------------


class Type:
    """Common base for type-tree nodes."""

    def __str__(self) -> str:  # pragma: no cover - thin wrapper
        return pretty_type(self)


@dataclass(frozen=True)
class TVar(Type):
    """A type variable or atomic constant.

    Convention: unifiable *variables* have Greek names (α, β, … plus an index
    for fresh ones). Uppercase Latin names ``P, Q, R`` are atomic constants —
    they unify only with themselves.
    """

    name: str


@dataclass(frozen=True)
class Arrow(Type):
    """The function type ``src → dst``."""

    src: Type
    dst: Type


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------


def pretty_type(t: Type, *, arrow: str = "→") -> str:
    """Pretty-print ``t`` with minimal parentheses (right-associative)."""

    def go(t: Type, ctx: str) -> str:
        if isinstance(t, TVar):
            return t.name
        if isinstance(t, Arrow):
            left = go(t.src, "left")
            right = go(t.dst, "right")
            s = f"{left} {arrow} {right}"
            return s if ctx == "right" else f"({s})"
        raise TypeError(f"Unknown type: {t!r}")

    return go(t, "right")


# ---------------------------------------------------------------------------
# Type parser
# ---------------------------------------------------------------------------


class _TypeParser:
    """Recursive descent for ``T := atom ('->' T)?``."""

    def __init__(self, src: str) -> None:
        self.src = src
        self.i = 0

    def _skip_ws(self) -> None:
        while self.i < len(self.src) and self.src[self.i].isspace():
            self.i += 1

    def _consume(self, prefix: str) -> bool:
        self._skip_ws()
        if self.src.startswith(prefix, self.i):
            self.i += len(prefix)
            return True
        return False

    def parse(self) -> Type:
        node = self._arrow()
        self._skip_ws()
        if self.i != len(self.src):
            rest = self.src[self.i:].lstrip()
            if rest.startswith("."):
                raise ValueError(
                    "types do not use dots — the dot belongs to lambda-terms (\\\\q. q). "
                "Write the proposition with arrows: P -> Q.")
            raise ValueError(
                f"Unexpected trailing input at pos {self.i}: {self.src[self.i:]!r}"
            )
        return node

    def _arrow(self) -> Type:
        left = self._atom()
        # Right-associative.
        if self._consume("->") or self._consume("→"):
            right = self._arrow()
            return Arrow(left, right)
        return left

    def _atom(self) -> Type:
        self._skip_ws()
        if self.i >= len(self.src):
            raise ValueError("Unexpected end of type expression")
        ch = self.src[self.i]
        if ch == "(":
            self.i += 1
            inner = self._arrow()
            self._skip_ws()
            if self.i >= len(self.src) or self.src[self.i] != ")":
                raise ValueError("Missing closing paren in type")
            self.i += 1
            return inner
        # Identifier (ASCII or Greek letter).
        start = self.i
        while self.i < len(self.src):
            c = self.src[self.i]
            if c.isalnum() or c == "_" or c in "αβγδεζηθικλμνξοπρστυφχψω":
                self.i += 1
            else:
                break
        if start == self.i:
            if ch in ("\\", "λ"):
                raise ValueError(
                    "that is lambda-TERM syntax, but this command expects a TYPE/proposition "
                    "(e.g. P -> Q). To infer a term's type instead, use `ch term \\q. q`.")
            if ch == ".":
                raise ValueError(
                    "types do not use dots — the dot belongs to lambda-terms (\\q. q). "
                    "Write the proposition with arrows: P -> Q.")
            raise ValueError(f"Expected identifier at pos {self.i}, got {ch!r}")
        return TVar(self.src[start:self.i])


def parse_type(s: str) -> Type:
    """Parse a type string ``"P -> Q -> R"`` (equivalently ``"P → Q → R"``)."""
    head = s.lstrip()[:1]
    if head in ("\\", "λ"):
        raise ValueError(
            "that is lambda-TERM syntax, but this command expects a TYPE/proposition "
            "(e.g. P -> Q). To infer a term's type instead, use `ch term \\\\q. q`.")
    return _TypeParser(s).parse()


# ---------------------------------------------------------------------------
# Type operations
# ---------------------------------------------------------------------------


def free_type_vars(t: Type) -> Set[str]:
    if isinstance(t, TVar):
        return {t.name}
    if isinstance(t, Arrow):
        return free_type_vars(t.src) | free_type_vars(t.dst)
    raise TypeError(f"Unknown type: {t!r}")


def substitute(t: Type, subst: Dict[str, Type]) -> Type:
    """Apply the substitution ``{name: Type}`` recursively."""
    if isinstance(t, TVar):
        return subst.get(t.name, t)
    if isinstance(t, Arrow):
        return Arrow(substitute(t.src, subst), substitute(t.dst, subst))
    raise TypeError(f"Unknown type: {t!r}")


def _compose(s2: Dict[str, Type], s1: Dict[str, Type]) -> Dict[str, Type]:
    """Composition of substitutions (``s2 ∘ s1``); ``s1`` takes precedence."""
    out = {k: substitute(v, s2) for k, v in s1.items()}
    for k, v in s2.items():
        if k not in out:
            out[k] = v
    return out


# Greek letters used for fresh type variables.
_FRESH_LETTERS = "αβγδεζηθικλμνξοπρστυφχψω"


class _FreshTVarFactory:
    """Factory for fresh type variables α, β, γ, … (with a cycle index)."""

    def __init__(self) -> None:
        self.idx = 0

    def fresh(self, used: Set[str]) -> TVar:
        while True:
            base = _FRESH_LETTERS[self.idx % len(_FRESH_LETTERS)]
            cycle = self.idx // len(_FRESH_LETTERS)
            name = base if cycle == 0 else f"{base}{cycle}"
            self.idx += 1
            if name not in used:
                return TVar(name)


def _occurs_in(name: str, t: Type) -> bool:
    return name in free_type_vars(t)


def _is_unifiable(name: str) -> bool:
    """Is the name a *variable* (unifiable) or an atomic *constant*?

    Heuristic (as on the desktop): Greek letters and names not starting with
    an uppercase Latin letter are variables; ``P, Q, R, A, B, …`` are atomic
    constants.
    """
    if not name:
        return False
    first = name[0]
    if first in _FRESH_LETTERS:
        return True
    return not first.isupper()


def unify(a: Type, b: Type) -> Optional[Dict[str, Type]]:
    """MGU (most general unifier); ``None`` when the types do not unify."""
    if isinstance(a, TVar) and isinstance(b, TVar) and a.name == b.name:
        return {}
    if isinstance(a, TVar) and _is_unifiable(a.name):
        if _occurs_in(a.name, b) and not (isinstance(b, TVar) and b.name == a.name):
            return None
        return {a.name: b}
    if isinstance(b, TVar) and _is_unifiable(b.name):
        if _occurs_in(b.name, a) and not (isinstance(a, TVar) and a.name == b.name):
            return None
        return {b.name: a}
    if isinstance(a, TVar) and isinstance(b, TVar):
        # Two distinct constants never unify.
        return None
    if isinstance(a, TVar) or isinstance(b, TVar):
        # Constant vs. arrow.
        return None
    if isinstance(a, Arrow) and isinstance(b, Arrow):
        s1 = unify(a.src, b.src)
        if s1 is None:
            return None
        s2 = unify(substitute(a.dst, s1), substitute(b.dst, s1))
        if s2 is None:
            return None
        return _compose(s2, s1)
    return None


# ---------------------------------------------------------------------------
# Type inference (Algorithm W)
# ---------------------------------------------------------------------------


class STLCTypeError(Exception):
    """The term is not typeable in STLC (e.g. self-application ``\\x. x x``)."""


def infer(term: Term, env: Optional[Dict[str, Type]] = None) -> Type:
    """Infer the type of ``term`` in environment ``env``.

    Returns a *type* (not a scheme — no generalisation, so this is not the
    full Hindley–Milner). Raises :class:`STLCTypeError` for untypeable terms.
    """
    factory = _FreshTVarFactory()

    used: Set[str] = set()
    if env:
        for v in env.values():
            used |= free_type_vars(v)

    def fresh() -> TVar:
        nonlocal used
        v = factory.fresh(used)
        used = used | {v.name}
        return v

    def w(env: Dict[str, Type], term: Term) -> Tuple[Dict[str, Type], Type]:
        """Algorithm W: returns (subst, type)."""
        if isinstance(term, Var):
            if term.name not in env:
                # Free variable — assign it a fresh atomic type.
                tv = fresh()
                return {}, tv
            return {}, env[term.name]
        if isinstance(term, Lam):
            tv = fresh()
            new_env = dict(env)
            new_env[term.param] = tv
            s_body, t_body = w(new_env, term.body)
            param_t = substitute(tv, s_body)
            return s_body, Arrow(param_t, t_body)
        if isinstance(term, App):
            s1, t1 = w(env, term.fn)
            env2 = {k: substitute(v, s1) for k, v in env.items()}
            s2, t2 = w(env2, term.arg)
            tv = fresh()
            t1_subst = substitute(t1, s2)
            mgu = unify(t1_subst, Arrow(t2, tv))
            if mgu is None:
                raise STLCTypeError(
                    f"Cannot unify {pretty_type(t1_subst)} with "
                    f"{pretty_type(Arrow(t2, tv))}"
                )
            s = _compose(mgu, _compose(s2, s1))
            return s, substitute(tv, mgu)
        raise TypeError(f"Unknown term: {term!r}")

    env_in: Dict[str, Type] = dict(env or {})
    s, ty = w(env_in, term)
    return _renumber(substitute(ty, s))


def _renumber(t: Type) -> Type:
    """After inference, rename type variables to α, β, γ, … (left to right)."""
    mapping: Dict[str, str] = {}
    counter = [0]

    def alloc(name: str) -> str:
        if name in mapping:
            return mapping[name]
        if not _is_unifiable(name):
            return name
        i = counter[0]
        base = _FRESH_LETTERS[i % len(_FRESH_LETTERS)]
        cycle = i // len(_FRESH_LETTERS)
        new_name = base if cycle == 0 else f"{base}{cycle}"
        mapping[name] = new_name
        counter[0] += 1
        return new_name

    def go(t: Type) -> Type:
        if isinstance(t, TVar):
            return TVar(alloc(t.name))
        if isinstance(t, Arrow):
            return Arrow(go(t.src), go(t.dst))
        raise TypeError(f"Unknown type: {t!r}")

    return go(t)


# ---------------------------------------------------------------------------
# Proof search (type inhabitation, implicational intuitionistic logic)
# ---------------------------------------------------------------------------


def _flatten_arrow(t: Type) -> Tuple[List[Type], Type]:
    """``A → B → C → D`` -> ``([A, B, C], D)``."""
    args: List[Type] = []
    while isinstance(t, Arrow):
        args.append(t.src)
        t = t.dst
    return args, t


def _suggest_var_name(env: Dict[str, Type]) -> str:
    """Suggest p, q, r, … or h0, h1, …, avoiding collisions."""
    preferred = ["p", "q", "r", "s", "x", "y", "z", "u", "v", "w"]
    used = set(env.keys())
    for n in preferred:
        if n not in used:
            return n
    i = 0
    while f"h{i}" in used:
        i += 1
    return f"h{i}"


def find_inhabitant(typ: Type, depth: int = 8) -> Optional[Term]:
    """Find a λ-term inhabiting ``typ`` (intuitionistic, ``->`` only).

    Returns the term, or ``None`` when nothing is found within ``depth``
    levels — e.g. for classically-but-not-intuitionistically valid types
    such as Peirce's law ``((P → Q) → P) → P``.
    """

    def go(env: Dict[str, Type], goal: Type, fuel: int) -> Optional[Term]:
        if fuel <= 0:
            return None
        # Introduction rule: a function goal introduces a hypothesis.
        if isinstance(goal, Arrow):
            name = _suggest_var_name(env)
            new_env = dict(env)
            new_env[name] = goal.src
            body = go(new_env, goal.dst, fuel - 1)
            if body is None:
                return None
            return Lam(name, body)

        # Elimination rule: find h : A1 → ... → An → goal in the environment.
        for hname, htype in env.items():
            args, ret = _flatten_arrow(htype)
            if ret != goal:
                continue
            # Try to fill the arguments recursively.
            arg_terms: List[Term] = []
            ok = True
            for a in args:
                sub = go(env, a, fuel - 1)
                if sub is None:
                    ok = False
                    break
                arg_terms.append(sub)
            if not ok:
                continue
            term: Term = Var(hname)
            for at in arg_terms:
                term = App(term, at)
            return term
        return None

    return go({}, typ, depth)


# ---------------------------------------------------------------------------
# λ → Lean
# ---------------------------------------------------------------------------


class LeanParseError(ValueError):
    """Error signature of the mini-Lean parser."""


def _lean_term(t: Term) -> str:
    """Term → Lean-syntax string with minimal parentheses."""
    if isinstance(t, Var):
        return t.name
    if isinstance(t, Lam):
        params: List[str] = [t.param]
        body: Term = t.body
        while isinstance(body, Lam):
            params.append(body.param)
            body = body.body
        return f"fun {' '.join(params)} => {_lean_term(body)}"
    if isinstance(t, App):
        left = _lean_term(t.fn)
        right = _lean_term(t.arg)
        # Parenthesise applied lambdas and nested applications when needed.
        if isinstance(t.fn, Lam):
            left = f"({left})"
        if isinstance(t.arg, (App, Lam)):
            right = f"({right})"
        return f"{left} {right}"
    raise TypeError(f"Unknown term: {t!r}")


def lambda_to_lean(term: Term, type: Optional[Type] = None, name: str = "ch_proof") -> str:
    """Generate a Lean 4 ``theorem`` for the given λ-term.

    If no type is supplied, it is inferred via :func:`infer`. Every atomic
    type name becomes a ``{P : Prop}`` binder.

    Example::

        >>> from lambda_lab.lab.parser import parse
        >>> print(lambda_to_lean(parse(r"\\p. p")))
        theorem ch_proof {α : Prop} : α → α :=
          fun p => p
    """
    if type is None:
        type = infer(term)
    atoms = sorted(free_type_vars(type))
    if atoms:
        binder = "{" + " ".join(atoms) + " : Prop}"
    else:
        binder = ""
    type_text = pretty_type(type, arrow="→")
    body = _lean_term(term)
    head = f"theorem {name}"
    if binder:
        head += f" {binder}"
    return f"{head} : {type_text} :=\n  {body}"


# ---------------------------------------------------------------------------
# Lean → λ
# ---------------------------------------------------------------------------


@dataclass
class _LeanLexer:
    src: str
    i: int = 0

    def peek(self) -> str:
        self._skip_ws()
        return self.src[self.i] if self.i < len(self.src) else ""

    def _skip_ws(self) -> None:
        while self.i < len(self.src) and self.src[self.i].isspace():
            self.i += 1

    def consume_ident_or_kw(self) -> str:
        self._skip_ws()
        if self.i >= len(self.src):
            return ""
        if not (self.src[self.i].isalpha() or self.src[self.i] == "_"):
            return ""
        j = self.i
        while j < len(self.src) and (self.src[j].isalnum() or self.src[j] in "_'"):
            j += 1
        text = self.src[self.i:j]
        self.i = j
        return text

    def try_consume(self, prefix: str) -> bool:
        self._skip_ws()
        if self.src.startswith(prefix, self.i):
            self.i += len(prefix)
            return True
        return False

    def at_end(self) -> bool:
        self._skip_ws()
        return self.i >= len(self.src)


_KEYWORDS = {"fun", "λ"}


def _parse_term(lex: _LeanLexer) -> Term:
    """``term := atom (atom)*`` (left-associative)."""
    atom = _parse_atom(lex)
    if atom is None:
        raise LeanParseError("Expected term")
    out: Term = atom
    while True:
        # Application may continue with: ident, "(".
        ch = lex.peek()
        if ch == "(":
            nxt = _parse_atom(lex)
            assert nxt is not None
            out = App(out, nxt)
            continue
        if ch == "" or ch == ")":
            break
        # Consider an identifier.
        save = lex.i
        ident = lex.consume_ident_or_kw()
        if not ident:
            break
        if ident in _KEYWORDS:
            # Start of a lambda — back up and stop the application chain.
            lex.i = save
            break
        out = App(out, Var(ident))
    return out


def _parse_atom(lex: _LeanLexer) -> Optional[Term]:
    ch = lex.peek()
    if ch == "":
        return None
    if ch == "(":
        lex.i += 1
        inner = _parse_term(lex)
        if not lex.try_consume(")"):
            raise LeanParseError("Missing closing ')'")
        return inner
    ident = lex.consume_ident_or_kw()
    if not ident:
        return None
    if ident in ("fun", "λ"):
        return _parse_lambda(lex)
    return Var(ident)


def _parse_lambda(lex: _LeanLexer) -> Term:
    """``fun x y z => body``  → ``Lam(x, Lam(y, Lam(z, body)))``."""
    params: List[str] = []
    while True:
        save = lex.i
        ident = lex.consume_ident_or_kw()
        if not ident:
            break
        if ident in _KEYWORDS:
            lex.i = save
            break
        params.append(ident)
        # "=>" (or "↦") after the names ends the parameter list.
        if lex.try_consume("=>") or lex.try_consume("↦"):
            break
    if not params:
        raise LeanParseError("fun without parameters")
    body = _parse_term(lex)
    out: Term = body
    for p in reversed(params):
        out = Lam(p, out)
    return out


def lean_to_lambda(src: str) -> Tuple[Term, Type]:
    """Parse a (small subset) Lean term → λ-term plus inferred type.

    Accepts ``fun x => x``, ``fun x y => x``, ``f x``, ``(f x) (g y)``, and
    ``theorem name : T := body`` (the body is taken). Anything else raises
    :class:`LeanParseError`.
    """
    src = src.strip()
    if src.startswith("theorem"):
        m_eq = src.find(":=")
        if m_eq < 0:
            raise LeanParseError("theorem without ':='")
        src = src[m_eq + 2:].strip()
    lex = _LeanLexer(src)
    term = _parse_term(lex)
    if not lex.at_end():
        raise LeanParseError(
            f"Unexpected trailing input at pos {lex.i}: {lex.src[lex.i:]!r}"
        )
    ty = infer(term)
    return term, ty
