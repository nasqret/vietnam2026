"""One-step, directed and capture-safe rewriting.

The kernel's :class:`~peano_lab.kernel.proofs.EqSubst` rule does not store an
occurrence path.  Instead it stores a *motive*: a formula with a distinguished
free variable at de Bruijn index zero.  Replacing that variable by the left and
right sides of the equation must recover the formula before and after the
rewrite, respectively.

``rewrite_first`` constructs exactly that pair.  Occurrences are considered in
formula left-to-right order and term pre-order (a whole term before its
children), so the result is deterministic.  The extra motive variable is made
room for by shifting every other free variable; ``shift_formula`` performs this
capture-safely through any untouched quantifiers.

Below ``d`` quantifiers an outer source is represented by ``shift(source, d)``.
The replacement is lifted by the same amount, the motive placeholder becomes
``Var(d)``, and untouched free variables shift at cutoff ``d``.  Bound indices
below that cutoff never move.  This is the entire alpha-safety argument, and
``rewrite_first`` checks both substitution identities before returning.
"""

from __future__ import annotations

from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.subst import shift_formula, shift_term, subst_formula
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


class RewriteError(ValueError):
    """Base class for an expected directed-rewrite failure."""


class NoRewriteOccurrence(RewriteError):
    """The source term does not occur in the formula."""


class RewriteUnderBinder(RewriteError):
    """Compatibility name retained from M1; M3 enters binders safely."""


def _is_rigid_term(term: object) -> bool:
    """Return whether ``term`` is an exact, metavariable-free kernel term."""

    if type(term) is Var:
        return type(term.index) is int and term.index >= 0
    if type(term) is Zero:
        return True
    if type(term) is Succ:
        return _is_rigid_term(term.term)
    if type(term) in (Add, Mul):
        return _is_rigid_term(term.left) and _is_rigid_term(term.right)
    return False


def _is_formula(formula: object) -> bool:
    if type(formula) is Eq:
        return _is_rigid_term(formula.left) and _is_rigid_term(formula.right)
    if type(formula) is Bot:
        return True
    if type(formula) in (Imp, And, Or):
        return _is_formula(formula.left) and _is_formula(formula.right)
    if type(formula) in (Forall, Exists):
        return _is_formula(formula.body)
    return False


def _rewrite_term(
    term: Term, source: Term, replacement: Term, depth: int
) -> tuple[Term, Term, bool]:
    """Return ``(new_term, motive_term, found)`` for one pre-order step."""

    if term == shift_term(source, depth):
        return shift_term(replacement, depth), Var(depth), True

    if type(term) is Succ:
        new_child, motive_child, found = _rewrite_term(
            term.term, source, replacement, depth
        )
        if found:
            return Succ(new_child), Succ(motive_child), True
    elif type(term) in (Add, Mul):
        constructor = type(term)
        new_left, motive_left, found = _rewrite_term(
            term.left, source, replacement, depth
        )
        if found:
            return (
                constructor(new_left, term.right),
                constructor(motive_left, shift_term(term.right, 1, cutoff=depth)),
                True,
            )
        new_right, motive_right, found = _rewrite_term(
            term.right, source, replacement, depth
        )
        if found:
            return (
                constructor(term.left, new_right),
                constructor(shift_term(term.left, 1, cutoff=depth), motive_right),
                True,
            )

    # This entire subtree is untouched.  Its free variables still need to move
    # past the motive's fresh index zero.
    return term, shift_term(term, 1, cutoff=depth), False


def _rewrite_in_formula(
    formula: Formula, source: Term, replacement: Term, depth: int
) -> tuple[Formula, Formula, bool]:
    """Return ``(new, motive, found)`` at the current binder depth."""

    if type(formula) is Eq:
        new_left, motive_left, found = _rewrite_term(
            formula.left, source, replacement, depth
        )
        if found:
            return (
                Eq(new_left, formula.right),
                Eq(motive_left, shift_term(formula.right, 1, cutoff=depth)),
                True,
            )
        new_right, motive_right, found = _rewrite_term(
            formula.right, source, replacement, depth
        )
        if found:
            return (
                Eq(formula.left, new_right),
                Eq(shift_term(formula.left, 1, cutoff=depth), motive_right),
                True,
            )
        return formula, shift_formula(formula, 1, cutoff=depth), False

    if type(formula) is Bot:
        return formula, formula, False

    if type(formula) in (Imp, And, Or):
        constructor = type(formula)
        new_left, motive_left, found = _rewrite_in_formula(
            formula.left, source, replacement, depth
        )
        if found:
            return (
                constructor(new_left, formula.right),
                constructor(
                    motive_left,
                    shift_formula(formula.right, 1, cutoff=depth),
                ),
                True,
            )
        new_right, motive_right, found = _rewrite_in_formula(
            formula.right, source, replacement, depth
        )
        if found:
            return (
                constructor(formula.left, new_right),
                constructor(
                    shift_formula(formula.left, 1, cutoff=depth),
                    motive_right,
                ),
                True,
            )
        return formula, shift_formula(formula, 1, cutoff=depth), False

    if type(formula) in (Forall, Exists):
        new_body, motive_body, found = _rewrite_in_formula(
            formula.body, source, replacement, depth + 1
        )
        if found:
            return type(formula)(new_body), type(formula)(motive_body), True
        return formula, shift_formula(formula, 1, cutoff=depth), False

    raise TypeError("expected a rigid PA formula")


def rewrite_first(
    formula: Formula, source: Term, replacement: Term
) -> tuple[Formula, Formula]:
    """Rewrite the first eligible ``source`` to ``replacement``.

    The returned pair is ``(new_formula, motive)`` and obeys::

        subst_formula(motive, 0, source) == formula
        subst_formula(motive, 0, replacement) == new_formula

    Both terms must be rigid kernel terms.  Quantifier bodies are traversed,
    but a bound variable is never mistaken for an outer variable of the same
    numerical index.
    """

    if not _is_formula(formula):
        raise TypeError("rewrite target must be a rigid PA formula")
    if not _is_rigid_term(source):
        raise TypeError("rewrite source must be a rigid PA term")
    if not _is_rigid_term(replacement):
        raise TypeError("rewrite replacement must be a rigid PA term")

    rewritten, motive, found = _rewrite_in_formula(
        formula, source, replacement, 0
    )
    if found:
        if subst_formula(motive, 0, source) != formula:
            raise RewriteError("internal error: rewrite motive does not recover the source.")
        if subst_formula(motive, 0, replacement) != rewritten:
            raise RewriteError("internal error: rewrite motive does not recover the result.")
        return rewritten, motive
    raise NoRewriteOccurrence("rewrite source does not occur in the target formula")


def rewrite_formula(
    formula: Formula, equation: Eq, *, reverse: bool = False
) -> tuple[Formula, Formula]:
    """Rewrite with an exact kernel equation, optionally right-to-left.

    ``reverse=False`` chooses ``equation.left`` as the source; ``True`` chooses
    ``equation.right``.  A tactic using the reverse direction must correspondingly
    pass ``EqSym(equation_proof)`` to the kernel's ``EqSubst`` constructor.
    """

    if type(equation) is not Eq or not _is_formula(equation):
        raise TypeError("rewrite theorem must be an exact kernel equation")
    if type(reverse) is not bool:
        raise TypeError("rewrite direction flag must be a boolean")
    source, replacement = (
        (equation.right, equation.left) if reverse else (equation.left, equation.right)
    )
    return rewrite_first(formula, source, replacement)


__all__ = [
    "RewriteError",
    "NoRewriteOccurrence",
    "RewriteUnderBinder",
    "rewrite_first",
    "rewrite_formula",
]
