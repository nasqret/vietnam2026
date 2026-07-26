"""The small, independent Peano Lab proof checker.

Tactics are untrusted.  This module accepts only a context, a certificate, and
the *original* goal, then checks the certificate from scratch.  It imports
nothing outside :mod:`peano_lab.kernel` and deliberately returns ``False`` for
malformed input instead of exposing exceptions to a caller.
"""

from __future__ import annotations

from .formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from .proofs import (
    AndElimL, AndElimR, AndIntro, Axiom, BotElim, CongAdd, CongMul, CongS,
    EqRefl, EqSubst, EqSym, EqTrans, ExistsElim, ExistsIntro, ForallElim,
    ForallIntro, Hyp, ImpElim, ImpIntro, Ind, OrElim, OrIntroL, OrIntroR, Proof,
)
from .subst import shift_formula, subst_formula
from .terms import Add, Mul, Succ, Term, Var, Zero


Context = tuple[Formula, ...]


def axiom_formula(name: str) -> Formula | None:
    """Return the closed formula denoted by a PA axiom constant."""

    z = Zero()
    x, y = Var(1), Var(0)  # below two nested quantifiers: x is outer
    axioms = {
        "PA1": Forall(Imp(Eq(Succ(Var(0)), z), Bot())),
        "PA2": Forall(Forall(Imp(Eq(Succ(x), Succ(y)), Eq(x, y)))),
        "PA3": Forall(Eq(Add(Var(0), z), Var(0))),
        "PA4": Forall(Forall(Eq(Add(x, Succ(y)), Succ(Add(x, y))))),
        "PA5": Forall(Eq(Mul(Var(0), z), z)),
        "PA6": Forall(Forall(Eq(Mul(x, Succ(y)), Add(Mul(x, y), x)))),
    }
    return axioms.get(name)


def _valid_term(term: object) -> bool:
    if type(term) is Var:
        return type(term.index) is int and term.index >= 0
    if type(term) is Zero:
        return True
    if type(term) is Succ:
        return _valid_term(term.term)
    if type(term) in (Add, Mul):
        return _valid_term(term.left) and _valid_term(term.right)
    return False


def _valid_formula(formula: object) -> bool:
    if type(formula) is Eq:
        return _valid_term(formula.left) and _valid_term(formula.right)
    if type(formula) is Bot:
        return True
    if type(formula) in (Imp, And, Or):
        return _valid_formula(formula.left) and _valid_formula(formula.right)
    if type(formula) in (Forall, Exists):
        return _valid_formula(formula.body)
    return False


def _normalise_context(ctx: object) -> Context | None:
    if not isinstance(ctx, (tuple, list)):
        return None
    result: list[Formula] = []
    for entry in ctx:
        formula = entry
        if isinstance(entry, tuple) and len(entry) == 2 and isinstance(entry[0], str):
            formula = entry[1]
        if not _valid_formula(formula):
            return None
        result.append(formula)
    return tuple(result)


def _under_term_binder(ctx: Context) -> Context:
    return tuple(shift_formula(formula, 1) for formula in ctx)


def _successor_instance(motive: Formula) -> Formula:
    # Insert the step's bound n after the motive's placeholder, then open the
    # placeholder with S n.  Outer parameters thereby retain their indices.
    lifted = shift_formula(motive, 1, cutoff=1)
    return subst_formula(lifted, 0, Succ(Var(0)))


def _infer(ctx: Context, proof: object) -> Formula | None:
    """Synthesize eliminations and annotated arithmetic proof forms."""

    if type(proof) is Hyp:
        i = proof.index
        return ctx[i] if type(i) is int and 0 <= i < len(ctx) else None
    if type(proof) is Axiom:
        return axiom_formula(proof.name)
    if type(proof) is EqRefl and _valid_term(proof.term):
        return Eq(proof.term, proof.term)
    if type(proof) is ImpElim:
        function = _infer(ctx, proof.function)
        if type(function) is Imp and _check(ctx, proof.argument, function.left):
            return function.right
        return None
    if type(proof) in (AndElimL, AndElimR):
        pair = _infer(ctx, proof.pair)
        if type(pair) is not And:
            return None
        return pair.left if type(proof) is AndElimL else pair.right
    if type(proof) is ForallElim and _valid_term(proof.term):
        universal = _infer(ctx, proof.universal)
        return subst_formula(universal.body, 0, proof.term) if type(universal) is Forall else None
    if type(proof) is EqSym:
        equation = _infer(ctx, proof.proof)
        return Eq(equation.right, equation.left) if type(equation) is Eq else None
    if type(proof) is EqTrans:
        first, second = _infer(ctx, proof.first), _infer(ctx, proof.second)
        if type(first) is Eq and type(second) is Eq and first.right == second.left:
            return Eq(first.left, second.right)
        return None
    if type(proof) is CongS:
        equation = _infer(ctx, proof.proof)
        return Eq(Succ(equation.left), Succ(equation.right)) if type(equation) is Eq else None
    if type(proof) in (CongAdd, CongMul):
        left, right = _infer(ctx, proof.left), _infer(ctx, proof.right)
        if type(left) is not Eq or type(right) is not Eq:
            return None
        constructor = Add if type(proof) is CongAdd else Mul
        return Eq(constructor(left.left, right.left), constructor(left.right, right.right))
    if type(proof) is EqSubst and _valid_formula(proof.motive):
        equation = _infer(ctx, proof.equation)
        if type(equation) is not Eq:
            return None
        source = subst_formula(proof.motive, 0, equation.left)
        if _check(ctx, proof.body, source):
            return subst_formula(proof.motive, 0, equation.right)
        return None
    if type(proof) is Ind and _valid_formula(proof.motive):
        base = subst_formula(proof.motive, 0, Zero())
        step = Forall(Imp(proof.motive, _successor_instance(proof.motive)))
        if _check(ctx, proof.base, base) and _check(ctx, proof.step, step):
            return Forall(proof.motive)
    return None


def _check(ctx: Context, proof: object, target: Formula) -> bool:
    inferred = _infer(ctx, proof)
    if inferred is not None:
        return inferred == target
    if type(proof) is ImpElim:
        # A local cut may put an introduction directly in function position.
        # Its domain can be recovered when the argument itself synthesizes.
        argument = _infer(ctx, proof.argument)
        return argument is not None and _check(
            ctx, proof.function, Imp(argument, target)
        ) and _check(ctx, proof.argument, argument)
    if type(proof) is ImpIntro and type(target) is Imp:
        return _check((target.left,) + ctx, proof.body, target.right)
    if type(proof) is AndIntro and type(target) is And:
        return _check(ctx, proof.left, target.left) and _check(ctx, proof.right, target.right)
    if type(proof) is OrIntroL and type(target) is Or:
        return _check(ctx, proof.proof, target.left)
    if type(proof) is OrIntroR and type(target) is Or:
        return _check(ctx, proof.proof, target.right)
    if type(proof) is OrElim:
        source = _infer(ctx, proof.disjunction)
        return (
            type(source) is Or
            and _check((source.left,) + ctx, proof.left_case, target)
            and _check((source.right,) + ctx, proof.right_case, target)
        )
    if type(proof) is BotElim:
        return _check(ctx, proof.absurdity, Bot())
    if type(proof) is ForallIntro and type(target) is Forall:
        return _check(_under_term_binder(ctx), proof.body, target.body)
    if type(proof) is ExistsIntro and type(target) is Exists and _valid_term(proof.term):
        return _check(ctx, proof.proof, subst_formula(target.body, 0, proof.term))
    if type(proof) is ExistsElim:
        source = _infer(ctx, proof.existential)
        if type(source) is not Exists:
            return False
        lifted_ctx = _under_term_binder(ctx)
        return _check((source.body,) + lifted_ctx, proof.body, shift_formula(target, 1))
    return False


def check(ctx: object, proof: object, formula: object) -> bool:
    """Return whether ``proof`` establishes ``formula`` from ``ctx``.

    The broad boundary catches malformed adversarial certificates.  Internal
    code remains ordinary structural recursion, so unexpected input cannot turn
    into a false positive.
    """

    try:
        context = _normalise_context(ctx)
        if context is None or not _valid_formula(formula) or not isinstance(proof, Proof):
            return False
        return _check(context, proof, formula)
    except (AttributeError, IndexError, TypeError, ValueError, RecursionError):
        return False


__all__ = ["check", "axiom_formula"]
