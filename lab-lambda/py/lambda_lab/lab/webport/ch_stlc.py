"""STLC facade for the browser ``ch`` command.

Since the 2026-07-24 audit there is exactly ONE type engine —
:mod:`lambda_lab.lab.webport.stlc_types` (rigid ``Atom`` vs. inference
``MetaVar``). This module delegates every type operation to that kernel and
keeps only what is genuinely ``ch``-specific: the λ ↔ Lean bridge
(``lambda_to_lean`` / ``lean_to_lambda``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from lambda_lab.lab.lc import App, Lam, Term, Var

from .stlc_types import (  # noqa: F401  (re-exported facade)
    Arrow,
    Atom,
    MetaVar,
    STLCTypeError,
    Subst,
    Type,
    _meta_names,
    apply_subst,
    find_inhabitant_ctx,
    infer,
    infer_closed,
    inhabitation_status,
    metas_in,
    parse_type,
    peel_arrows,
    pretty_type,
    pretty_types,
    target_is_instance_of,
    unify,
)
from .stlc_types import find_inhabitant as _kernel_find_inhabitant


def find_inhabitant(typ: Type, depth: int = 10) -> Optional[Term]:
    """Back-compat wrapper (the old ``ch`` engine used ``depth=``)."""
    return _kernel_find_inhabitant(typ, max_depth=depth)


def free_type_vars(t: Type) -> Set[str]:
    """Names appearing in ``t``: atom names plus metavariable display names
    (α, β, … — the same names :func:`pretty_type` would print)."""
    names = _meta_names([t])
    out: Set[str] = set()

    def go(x: Type) -> None:
        if isinstance(x, Atom):
            out.add(x.name)
        elif isinstance(x, MetaVar):
            out.add(names.get(x.id, f"?m{x.id}"))
        elif isinstance(x, Arrow):
            go(x.src)
            go(x.dst)

    go(t)
    return out


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

    If no type is supplied, the principal type is inferred. Atom names and
    metavariable display names (α, β, …) become ``{P α : Prop}`` binders —
    the SAME names ``pretty_type`` prints, so the theorem statement and the
    binder list always agree.

    Example::

        >>> from lambda_lab.lab.parser import parse
        >>> print(lambda_to_lean(parse(r"\\p. p")))
        theorem ch_proof {α : Prop} : α → α :=
          fun p => p
    """
    if type is None:
        type = infer(term)
    names = _meta_names([type])
    atoms: List[str] = []

    def collect(x: Type) -> None:
        if isinstance(x, Atom):
            if x.name not in atoms:
                atoms.append(x.name)
        elif isinstance(x, Arrow):
            collect(x.src)
            collect(x.dst)

    collect(type)
    binder_names = sorted(atoms) + list(names.values())
    binder = "{" + " ".join(binder_names) + " : Prop}" if binder_names else ""
    type_text = pretty_type(type, arrow="→", names=names)
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
