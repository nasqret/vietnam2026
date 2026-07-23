"""Typed STLC for the browser build: simple types + algorithm W (Hindley-Milner-lite).

Faithful port of the desktop ``lambda_lab.lab.curry_howard.types`` (pure stdlib).

Types are modelled as:

* ``TVar(name)``     - a type variable or atom (e.g. ``α``, ``P``).
* ``Arrow(src, dst)`` - the function type ``A → B``.

Exports:

* ``parse_type(s)``   - parser for ``"P -> Q -> R"`` (right-assoc), ``→`` or ``->``.
* ``pretty_type(t)``  - pretty printer with minimal parentheses.
* ``free_type_vars(t)`` - set of type-variable names.
* ``substitute(t, s)`` - applies a substitution ``{name: Type}``.
* ``unify(a, b)``     - most general unifier or ``None``.
* ``infer(term)``     - types a λ-term; raises ``STLCTypeError`` for terms
  untypable in STLC (e.g. ``\\x. x x``).

Naming convention: Greek letters (``α, β, γ, …``) are *unifiable* variables;
uppercase Latin atoms (``P, Q, R``) are constants that unify only with themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Set

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
    """Type variable or atom."""

    name: str


@dataclass(frozen=True)
class Arrow(Type):
    """Function type ``src → dst``."""

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
            raise ValueError(f"Unexpected trailing input at pos {self.i}: {self.src[self.i:]!r}")
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
    head = s.lstrip()[:1]
    if head in ("\\", "λ"):
        raise ValueError(
            "that is lambda-TERM syntax, but this command expects a TYPE/proposition "
            "(e.g. P -> Q). To infer a term's type instead, use `ch term \\\\q. q`.")
    """Parse ``"P -> Q -> R"`` (equivalently ``"P → Q → R"``).

    The arrow is right-associative; parentheses work as usual.
    """
    return _TypeParser(s).parse()


# ---------------------------------------------------------------------------
# Operations on types
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
    """Composition of substitutions (``s2 ∘ s1``)."""
    out = {k: substitute(v, s2) for k, v in s1.items()}
    for k, v in s2.items():
        if k not in out:
            out[k] = v
    return out


# Greek letters used for fresh type variables.
_FRESH_LETTERS = "αβγδεζηθικλμνξοπρστυφχψω"


class _FreshTVarFactory:
    """Factory of fresh variables α, β, ... (with a numeric cycle suffix)."""

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


def fresh_tvar_name(used: Set[str]) -> str:
    """Find a fresh type-variable name (α, β, …)."""
    return _FreshTVarFactory().fresh(used).name


def _occurs_in(name: str, t: Type) -> bool:
    return name in free_type_vars(t)


def unify(a: Type, b: Type) -> Optional[Dict[str, Type]]:
    """MGU (most general unifier) for STLC types.

    Returns a dict ``{name: Type}`` or ``None`` when the types do not unify.
    Atoms ``P, Q, R`` (uppercase first letter) are constants - they unify only
    with themselves. Greek letters and lowercase names are variables.
    """
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
        # Two distinct constants - no unifier.
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


def _is_unifiable(name: str) -> bool:
    """Is the name a *variable* (unifiable) or an atomic *constant*?

    Heuristic: Greek letters (α, β, …) and names not starting with A-Z are
    variables. Uppercase Latin atoms ``P, Q, R, A, B, …`` are constants.
    """
    if not name:
        return False
    first = name[0]
    if first in _FRESH_LETTERS:
        return True
    return not first.isupper()


# ---------------------------------------------------------------------------
# Type inference (algorithm W)
# ---------------------------------------------------------------------------


class STLCTypeError(Exception):
    """The term is not typable in STLC (e.g. self-application ``\\x. x x``)."""


def infer(term: Term, env: Optional[Dict[str, Type]] = None) -> Type:
    """Infer the type of ``term`` in the environment ``env``.

    Returns a *type* (no generalization - this is not full H-M). For closed
    terms the result uses fresh Greek variables.

    Raises ``STLCTypeError`` when the term is not typable.
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

    def w(env: Dict[str, Type], term: Term):
        """Algorithm W: returns (subst, type)."""
        if isinstance(term, Var):
            if term.name not in env:
                # Free variable - assign it a fresh atomic type.
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
    """After inference, renumber type variables to α, β, γ, … (left-to-right)."""
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
