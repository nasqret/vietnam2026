"""Capture-proof de Bruijn shifting and substitution.

``subst_term(t, i, s)`` and ``subst_formula(f, i, s)`` *open* one variable
slot: they replace index ``i`` by ``s`` and decrement indices above that slot.
Under a binder the sought index and replacement are lifted together.  This is
the small detail that prevents a free variable of ``s`` from being captured.
"""

from __future__ import annotations

from .formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from .terms import Add, Mul, Succ, Term, Var, Zero


def _require_index(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def shift_term(t: Term, by: int, cutoff: int = 0) -> Term:
    """Shift every variable index at least ``cutoff`` by ``by``."""

    if not isinstance(by, int) or isinstance(by, bool):
        raise ValueError("shift amount must be an integer")
    _require_index(cutoff, "cutoff")
    if isinstance(t, Var):
        index = t.index + by if t.index >= cutoff else t.index
        if index < 0:
            raise ValueError("shift would create a negative de Bruijn index")
        return Var(index)
    if isinstance(t, Zero):
        return t
    if isinstance(t, Succ):
        return Succ(shift_term(t.term, by, cutoff))
    if isinstance(t, Add):
        return Add(shift_term(t.left, by, cutoff), shift_term(t.right, by, cutoff))
    if isinstance(t, Mul):
        return Mul(shift_term(t.left, by, cutoff), shift_term(t.right, by, cutoff))
    raise TypeError("expected a PA term")


def shift_formula(f: Formula, by: int, cutoff: int = 0) -> Formula:
    """Shift free term variables in a formula, respecting its binders."""

    if isinstance(f, Eq):
        return Eq(shift_term(f.left, by, cutoff), shift_term(f.right, by, cutoff))
    if isinstance(f, Bot):
        return f
    if isinstance(f, Imp):
        return Imp(shift_formula(f.left, by, cutoff), shift_formula(f.right, by, cutoff))
    if isinstance(f, And):
        return And(shift_formula(f.left, by, cutoff), shift_formula(f.right, by, cutoff))
    if isinstance(f, Or):
        return Or(shift_formula(f.left, by, cutoff), shift_formula(f.right, by, cutoff))
    if isinstance(f, Forall):
        return Forall(shift_formula(f.body, by, cutoff + 1))
    if isinstance(f, Exists):
        return Exists(shift_formula(f.body, by, cutoff + 1))
    raise TypeError("expected a PA formula")


def _subst_term(t: Term, idx: int, replacement: Term, depth: int) -> Term:
    if isinstance(t, Var):
        sought = idx + depth
        if t.index == sought:
            return shift_term(replacement, depth)
        if t.index > sought:
            return Var(t.index - 1)
        return t
    if isinstance(t, Zero):
        return t
    if isinstance(t, Succ):
        return Succ(_subst_term(t.term, idx, replacement, depth))
    if isinstance(t, Add):
        return Add(
            _subst_term(t.left, idx, replacement, depth),
            _subst_term(t.right, idx, replacement, depth),
        )
    if isinstance(t, Mul):
        return Mul(
            _subst_term(t.left, idx, replacement, depth),
            _subst_term(t.right, idx, replacement, depth),
        )
    raise TypeError("expected a PA term")


def subst_term(t: Term, idx: int, replacement: Term) -> Term:
    """Open variable slot ``idx`` in ``t`` with ``replacement``."""

    _require_index(idx, "substitution index")
    if not isinstance(replacement, Term):
        raise TypeError("replacement must be a PA term")
    return _subst_term(t, idx, replacement, 0)


def _subst_formula(f: Formula, idx: int, replacement: Term, depth: int) -> Formula:
    if isinstance(f, Eq):
        return Eq(
            _subst_term(f.left, idx, replacement, depth),
            _subst_term(f.right, idx, replacement, depth),
        )
    if isinstance(f, Bot):
        return f
    if isinstance(f, Imp):
        return Imp(
            _subst_formula(f.left, idx, replacement, depth),
            _subst_formula(f.right, idx, replacement, depth),
        )
    if isinstance(f, And):
        return And(
            _subst_formula(f.left, idx, replacement, depth),
            _subst_formula(f.right, idx, replacement, depth),
        )
    if isinstance(f, Or):
        return Or(
            _subst_formula(f.left, idx, replacement, depth),
            _subst_formula(f.right, idx, replacement, depth),
        )
    if isinstance(f, Forall):
        return Forall(_subst_formula(f.body, idx, replacement, depth + 1))
    if isinstance(f, Exists):
        return Exists(_subst_formula(f.body, idx, replacement, depth + 1))
    raise TypeError("expected a PA formula")


def subst_formula(f: Formula, idx: int, replacement_term: Term) -> Formula:
    """Open free variable slot ``idx`` in ``f`` with ``replacement_term``."""

    _require_index(idx, "substitution index")
    if not isinstance(replacement_term, Term):
        raise TypeError("replacement must be a PA term")
    return _subst_formula(f, idx, replacement_term, 0)


__all__ = ["shift_term", "shift_formula", "subst_term", "subst_formula"]
