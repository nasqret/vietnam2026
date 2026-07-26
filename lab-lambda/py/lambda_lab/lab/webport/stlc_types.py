"""The trusted STLC kernel: types, unification, Algorithm W, inhabitation.

Rewritten per the 2026-07-24 `prove` audit (P0.2/P0.4, P1.3). The crucial
design decision: **parsed proposition atoms and inference metavariables are
different node types.**

* :class:`Atom` — a rigid proposition letter (``P``, ``q``, ``α``, ``foo``);
  produced ONLY by :func:`parse_type`; never substituted by unification.
* :class:`MetaVar` — a flexible unification variable with a globally unique
  integer id; produced ONLY by inference; the only thing ``unify`` may bind.

Rigidity therefore never depends on spelling: lowercase, Greek and uppercase
atoms are all equally rigid, exactly as the course requires.

This module is the single kernel shared by ``prove`` and ``ch`` (their old
private copies delegate here).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from lambda_lab.lab.lc import App, Lam, Term, Var

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Type:
    """Base class for simple types."""


@dataclass(frozen=True)
class Atom(Type):
    """A rigid proposition atom, exactly as the user wrote it."""
    name: str


@dataclass(frozen=True)
class MetaVar(Type):
    """A flexible inference variable. Identity is the globally unique id."""
    id: int


@dataclass(frozen=True)
class Arrow(Type):
    src: "Type"
    dst: "Type"


_meta_counter = itertools.count()


def fresh_meta() -> MetaVar:
    """A globally unique metavariable (audit P0.3: ids never collide)."""
    return MetaVar(next(_meta_counter))


# Substitutions are keyed by MetaVar id — never by display strings.
Subst = Dict[int, Type]


class STLCTypeError(Exception):
    """Raised when a term has no simple type (or inference fails)."""


# ---------------------------------------------------------------------------
# Substitution machinery
# ---------------------------------------------------------------------------


def walk(t: Type, subst: Subst) -> Type:
    """Resolve a top-level MetaVar through the substitution to a fixpoint."""
    while isinstance(t, MetaVar) and t.id in subst:
        t = subst[t.id]
    return t


def apply_subst(t: Type, subst: Subst) -> Type:
    t = walk(t, subst)
    if isinstance(t, Arrow):
        return Arrow(apply_subst(t.src, subst), apply_subst(t.dst, subst))
    return t


def _occurs(mid: int, t: Type, subst: Subst) -> bool:
    t = walk(t, subst)
    if isinstance(t, MetaVar):
        return t.id == mid
    if isinstance(t, Arrow):
        return _occurs(mid, t.src, subst) or _occurs(mid, t.dst, subst)
    return False


def unify(a: Type, b: Type, subst: Optional[Subst] = None) -> Optional[Subst]:
    """Most general unifier extending ``subst``; only MetaVars are bindable.

    Returns the extended substitution, or ``None`` when the types clash.
    Atoms unify only with themselves — capitalization plays no role.
    """
    s: Subst = dict(subst) if subst else {}

    def go(x: Type, y: Type) -> bool:
        x, y = walk(x, s), walk(y, s)
        if x == y:
            return True
        if isinstance(x, MetaVar):
            if _occurs(x.id, y, s):
                return False
            s[x.id] = y
            return True
        if isinstance(y, MetaVar):
            if _occurs(y.id, x, s):
                return False
            s[y.id] = x
            return True
        if isinstance(x, Arrow) and isinstance(y, Arrow):
            return go(x.src, y.src) and go(x.dst, y.dst)
        return False  # Atom mismatch, or Atom vs Arrow

    return s if go(a, b) else None


def metas_in(t: Type, subst: Optional[Subst] = None) -> List[int]:
    """MetaVar ids occurring in ``t`` (after resolving through ``subst``)."""
    out: List[int] = []

    def go(x: Type) -> None:
        x = walk(x, subst or {})
        if isinstance(x, MetaVar):
            if x.id not in out:
                out.append(x.id)
        elif isinstance(x, Arrow):
            go(x.src)
            go(x.dst)

    go(t)
    return out


def target_is_instance_of(principal: Type, target: Type) -> bool:
    """One-way check: can ``target`` be obtained by instantiating ONLY the
    metavariables of ``principal``? ``target`` must be ground (atoms/arrows).
    Since ``unify`` can bind only MetaVars and a ground target contains none,
    plain unification is exactly this one-way instance check."""
    if metas_in(target):
        return False
    return unify(principal, target) is not None


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

_GREEK = ["α", "β", "γ", "δ", "ε", "ζ", "θ", "ι", "κ", "μ"]


def _meta_names(types: List[Type]) -> Dict[int, str]:
    """Stable display names (α, β, …) for metavariables, in first-appearance
    order across the given types. Display only — identity is the id."""
    order: List[int] = []
    for t in types:
        for mid in metas_in(t):
            if mid not in order:
                order.append(mid)
    names: Dict[int, str] = {}
    for i, mid in enumerate(order):
        names[mid] = _GREEK[i] if i < len(_GREEK) else f"τ{i - len(_GREEK) + 1}"
    return names


def pretty_type(t: Type, *, arrow: str = "→",
                names: Optional[Dict[int, str]] = None) -> str:
    names = names if names is not None else _meta_names([t])

    def go(x: Type, left_of_arrow: bool) -> str:
        if isinstance(x, Atom):
            return x.name
        if isinstance(x, MetaVar):
            return names.get(x.id, f"?m{x.id}")
        if isinstance(x, Arrow):
            s = f"{go(x.src, True)} {arrow} {go(x.dst, False)}"
            return f"({s})" if left_of_arrow else s
        raise TypeError(f"Unknown type node: {x!r}")

    return go(t, False)


def pretty_types(ts, *, arrow: str = "→") -> List[str]:
    """Pretty-print several types with ONE shared metavariable naming, so a
    metavar shows as the same Greek letter everywhere it occurs."""
    ts = list(ts)
    names = _meta_names(ts)
    return [pretty_type(t, arrow=arrow, names=names) for t in ts]


# ---------------------------------------------------------------------------
# Type parsing (produces Atoms only)
# ---------------------------------------------------------------------------


def is_type_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch == "_"


def is_type_ident_cont(ch: str) -> bool:
    return ch.isalnum() or ch in ("_", "'")


class _TypeParser:
    def __init__(self, src: str):
        self.src = src
        self.i = 0

    def _skip_ws(self) -> None:
        while self.i < len(self.src) and self.src[self.i].isspace():
            self.i += 1

    def _peek(self) -> str:
        return self.src[self.i] if self.i < len(self.src) else ""

    def parse(self) -> Type:
        t = self._arrow()
        self._skip_ws()
        if self.i < len(self.src):
            rest = self.src[self.i:].lstrip()
            if rest.startswith("."):
                raise ValueError(
                    "types do not use dots — the dot belongs to lambda-terms (\\q. q). "
                    "Write the proposition with arrows: P -> Q.")
            raise ValueError(
                f"Unexpected trailing input at pos {self.i}: {self.src[self.i:]!r}")
        return t

    def _arrow(self) -> Type:
        left = self._atom()
        self._skip_ws()
        if self.src.startswith("->", self.i):
            self.i += 2
            return Arrow(left, self._arrow())
        if self._peek() == "→":
            self.i += 1
            return Arrow(left, self._arrow())
        return left

    def _atom(self) -> Type:
        self._skip_ws()
        ch = self._peek()
        if ch == "(":
            self.i += 1
            inner = self._arrow()
            self._skip_ws()
            if self._peek() != ")":
                raise ValueError(f"Missing ')' at pos {self.i}")
            self.i += 1
            return inner
        if not ch:
            raise ValueError("Unexpected end of type — expected an atom or '('")
        if ch in ("\\", "λ"):
            raise ValueError(
                "that is lambda-TERM syntax, but this command expects a TYPE/proposition "
                "(e.g. P -> Q). To infer a term's type instead, use `ch term \\q. q`.")
        if not is_type_ident_start(ch):
            raise ValueError(f"Expected identifier at pos {self.i}, got {ch!r}")
        j = self.i + 1
        while j < len(self.src) and is_type_ident_cont(self.src[j]):
            j += 1
        name = self.src[self.i:j]
        self.i = j
        return Atom(name)


def parse_type(s: str) -> Type:
    head = s.lstrip()[:1]
    if head in ("\\", "λ"):
        raise ValueError(
            "that is lambda-TERM syntax, but this command expects a TYPE/proposition "
            "(e.g. P -> Q). To infer a term's type instead, use `ch term \\q. q`.")
    if not s.strip():
        raise ValueError("Empty type.")
    return _TypeParser(s).parse()


# ---------------------------------------------------------------------------
# Algorithm W
# ---------------------------------------------------------------------------


def infer_with_subst(
    term: Term,
    env: Dict[str, Type],
    subst: Subst,
    free_table: Optional[Dict[str, MetaVar]] = None,
) -> Tuple[Type, Subst]:
    """Algorithm W extending an existing substitution.

    ``env`` maps term variables to types (atoms and/or metavariables).
    Free term variables NOT in ``env`` receive ONE shared metavariable per
    name for the whole run (``free_table``); callers that require closed
    terms must check ``lc.free_vars`` themselves before calling.
    """
    ft: Dict[str, MetaVar] = free_table if free_table is not None else {}
    s: Subst = dict(subst)

    def go(t: Term, e: Dict[str, Type]) -> Type:
        nonlocal s
        if isinstance(t, Var):
            if t.name in e:
                return e[t.name]
            return ft.setdefault(t.name, fresh_meta())
        if isinstance(t, Lam):
            m = fresh_meta()
            body_ty = go(t.body, {**e, t.param: m})
            return Arrow(m, body_ty)
        if isinstance(t, App):
            fn_ty = go(t.fn, e)
            arg_ty = go(t.arg, e)
            res = fresh_meta()
            s2 = unify(fn_ty, Arrow(arg_ty, res), s)
            if s2 is None:
                a, b = pretty_types(
                    [apply_subst(fn_ty, s), apply_subst(Arrow(arg_ty, res), s)])
                raise STLCTypeError(f"cannot unify {a} with {b}")
            s = s2
            return res
        raise TypeError(f"Unknown term node: {t!r}")

    ty = go(term, dict(env))
    return apply_subst(ty, s), s


def infer(term: Term, env: Optional[Dict[str, Type]] = None) -> Type:
    """Principal type of ``term`` (display-oriented convenience wrapper)."""
    ty, _ = infer_with_subst(term, env or {}, {})
    return ty


def infer_closed(term: Term) -> Type:
    """Principal type of a CLOSED term; raises if any variable is free."""
    from lambda_lab.lab.lc import free_vars
    fv = free_vars(term)
    if fv:
        raise STLCTypeError(
            f"term is open — free variable(s): {', '.join(sorted(fv))}")
    return infer(term)


# ---------------------------------------------------------------------------
# Inhabitation search (implicational intuitionistic logic), context-aware
# ---------------------------------------------------------------------------


def peel_arrows(t: Type) -> Tuple[List[Type], Type]:
    args: List[Type] = []
    while isinstance(t, Arrow):
        args.append(t.src)
        t = t.dst
    return args, t


def find_inhabitant_ctx(
    target: Type,
    context: Tuple[Tuple[str, Type], ...] = (),
    max_depth: int = 10,
) -> Tuple[str, Optional[Term]]:
    """Search for an inhabitant of a GROUND target, using the hypotheses in
    ``context`` (audit P1.3).

    Returns ``(status, term)`` with status one of ``"found"``, ``"none"``
    (search space exhausted below the depth limit) or ``"limit"`` (the depth
    limit was hit somewhere, so absence of a proof is NOT established).
    """
    if metas_in(target) or any(metas_in(t) for _, t in context):
        return ("limit", None)  # undetermined types: refuse to guess

    limit_hit = [False]
    fresh_i = [0]

    def fresh_name(used: set) -> str:
        for base in "pqrstuvwxyz":
            if base not in used:
                return base
        fresh_i[0] += 1
        return f"h{fresh_i[0]}"

    def prove(ctx: Tuple[Tuple[str, Type], ...], goal: Type, depth: int,
              seen: frozenset) -> Optional[Term]:
        if depth <= 0:
            limit_hit[0] = True
            return None
        key = (goal, tuple(sorted(((n, repr(t)) for n, t in ctx))))
        if key in seen:
            return None
        seen = seen | {key}
        if isinstance(goal, Arrow):
            used = {n for n, _ in ctx}
            x = fresh_name(used)
            body = prove(ctx + ((x, goal.src),), goal.dst, depth - 1, seen)
            return Lam(x, body) if body is not None else None
        # goal is an Atom: try every hypothesis whose result is the goal
        for name, hyp in ctx:
            args, ret = peel_arrows(hyp)
            if ret != goal:
                continue
            term: Term = Var(name)
            ok = True
            for a in args:
                sub = prove(ctx, a, depth - 1, seen)
                if sub is None:
                    ok = False
                    break
                term = App(term, sub)
            if ok:
                return term
        return None

    term = prove(tuple(context), target, max_depth, frozenset())
    if term is not None:
        return ("found", term)
    return ("limit", None) if limit_hit[0] else ("none", None)


def find_inhabitant(target: Type, max_depth: int = 10) -> Optional[Term]:
    """Back-compat empty-context search."""
    status, term = find_inhabitant_ctx(target, (), max_depth)
    return term if status == "found" else None


def inhabitation_status(target: Type, max_depth: int = 12) -> Tuple[str, Optional[Term]]:
    """(status, witness) so UIs can distinguish 'uninhabited' from
    'search limit reached'."""
    return find_inhabitant_ctx(target, (), max_depth)
