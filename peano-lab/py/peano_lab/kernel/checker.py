"""The small, independent Peano Lab proof checker.

Tactics are untrusted.  This module accepts only a context, a certificate, and
the *original* goal, then checks the certificate from scratch.  It imports
nothing outside :mod:`peano_lab.kernel` and deliberately returns ``False`` for
malformed input instead of exposing exceptions to a caller.
"""

from __future__ import annotations

from .formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from .proofs import (
    AndElimL, AndElimR, AndIntro, Axiom, BotElim, CongAdd, CongMul, CongS, Cut,
    DNE, EqRefl, EqSubst, EqSym, EqTrans, ExistsElim, ExistsIntro, ForallElim,
    ForallIntro, Hyp, ImpElim, ImpIntro, Ind, OrElim, OrIntroL, OrIntroR, Proof,
)
from .subst import shift_formula, subst_formula
from .terms import Add, Mul, Succ, Term, Var, Zero


# ``(formula, pending)`` denotes ``shift_formula(formula, pending)``.
ContextEntry = tuple[Formula, int]
Context = tuple[ContextEntry, ...]


def axiom_formula(name: str) -> Formula | None:
    """Return the closed formula denoted by a PA axiom constant."""

    if type(name) is not str:
        return None
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
    if type(term) is Add or type(term) is Mul:
        return _valid_term(term.left) and _valid_term(term.right)
    return False


def _valid_formula(formula: object) -> bool:
    if type(formula) is Eq:
        return _valid_term(formula.left) and _valid_term(formula.right)
    if type(formula) is Bot:
        return True
    if type(formula) is Imp or type(formula) is And or type(formula) is Or:
        return _valid_formula(formula.left) and _valid_formula(formula.right)
    if type(formula) is Forall or type(formula) is Exists:
        return _valid_formula(formula.body)
    return False


def _normalise_context(ctx: object) -> Context | None:
    if not isinstance(ctx, (tuple, list)):
        return None
    result: list[ContextEntry] = []
    for entry in ctx:
        formula = entry
        if isinstance(entry, tuple) and len(entry) == 2 and isinstance(entry[0], str):
            formula = entry[1]
        if not _valid_formula(formula):
            return None
        result.append((formula, 0))
    return tuple(result)


def _extend(ctx: Context, formula: Formula) -> Context:
    return ((formula, 0),) + ctx


def _under_term_binder(ctx: Context) -> Context:
    # Delaying the shift is extensionally equal to shifting every hypothesis
    # now, but avoids repeatedly rebuilding large contexts whose entries may
    # never be selected by a Hyp node.
    return tuple((formula, pending + 1) for formula, pending in ctx)


def _successor_instance(motive: Formula) -> Formula:
    # Insert the step's bound n after the motive's placeholder, then open the
    # placeholder with S n.  Outer parameters thereby retain their indices.
    lifted = shift_formula(motive, 1, cutoff=1)
    return subst_formula(lifted, 0, Succ(Var(0)))


def _infer(ctx: Context, proof: object, classical: bool) -> Formula | None:
    """Synthesize eliminations and annotated arithmetic proof forms."""

    if type(proof) is Hyp:
        i = proof.index
        if type(i) is not int or not 0 <= i < len(ctx):
            return None
        formula, pending = ctx[i]
        return shift_formula(formula, pending) if pending else formula
    if type(proof) is Axiom:
        return axiom_formula(proof.name)
    if type(proof) is EqRefl and _valid_term(proof.term):
        return Eq(proof.term, proof.term)
    if type(proof) is DNE and classical and _valid_formula(proof.proposition):
        negation = Imp(proof.proposition, Bot())
        return Imp(Imp(negation, Bot()), proof.proposition)
    if (
        type(proof) is Cut
        and _valid_formula(proof.proposition)
        and _valid_formula(proof.conclusion)
    ):
        if _check(ctx, proof.lemma, proof.proposition, classical) and _check(
            _extend(ctx, proof.proposition),
            proof.body,
            proof.conclusion,
            classical,
        ):
            return proof.conclusion
        return None
    if type(proof) is ImpElim:
        function = _infer(ctx, proof.function, classical)
        if type(function) is Imp and _check(ctx, proof.argument, function.left, classical):
            return function.right
        return None
    if type(proof) is AndElimL or type(proof) is AndElimR:
        pair = _infer(ctx, proof.pair, classical)
        if type(pair) is not And:
            return None
        return pair.left if type(proof) is AndElimL else pair.right
    if type(proof) is ForallElim and _valid_term(proof.term):
        universal = _infer(ctx, proof.universal, classical)
        return subst_formula(universal.body, 0, proof.term) if type(universal) is Forall else None
    if type(proof) is EqSym:
        equation = _infer(ctx, proof.proof, classical)
        return Eq(equation.right, equation.left) if type(equation) is Eq else None
    if type(proof) is EqTrans:
        first = _infer(ctx, proof.first, classical)
        second = _infer(ctx, proof.second, classical)
        if type(first) is Eq and type(second) is Eq and first.right == second.left:
            return Eq(first.left, second.right)
        return None
    if type(proof) is CongS:
        equation = _infer(ctx, proof.proof, classical)
        return Eq(Succ(equation.left), Succ(equation.right)) if type(equation) is Eq else None
    if type(proof) is CongAdd or type(proof) is CongMul:
        left = _infer(ctx, proof.left, classical)
        right = _infer(ctx, proof.right, classical)
        if type(left) is not Eq or type(right) is not Eq:
            return None
        constructor = Add if type(proof) is CongAdd else Mul
        return Eq(constructor(left.left, right.left), constructor(left.right, right.right))
    if type(proof) is EqSubst and _valid_formula(proof.motive):
        equation = _infer(ctx, proof.equation, classical)
        if type(equation) is not Eq:
            return None
        source = subst_formula(proof.motive, 0, equation.left)
        if _check(ctx, proof.body, source, classical):
            return subst_formula(proof.motive, 0, equation.right)
        return None
    if type(proof) is Ind and _valid_formula(proof.motive):
        base = subst_formula(proof.motive, 0, Zero())
        step = Forall(Imp(proof.motive, _successor_instance(proof.motive)))
        if _check(ctx, proof.base, base, classical) and _check(
            ctx, proof.step, step, classical
        ):
            return Forall(proof.motive)
    return None


def _check(ctx: Context, proof: object, target: Formula, classical: bool) -> bool:
    inferred = _infer(ctx, proof, classical)
    if inferred is not None:
        return inferred == target
    if type(proof) is ImpElim:
        # An implication redex may put an introduction directly in function position.
        # Its domain can be recovered when the argument itself synthesizes.
        argument = _infer(ctx, proof.argument, classical)
        return argument is not None and _check(
            ctx, proof.function, Imp(argument, target), classical
        ) and _check(ctx, proof.argument, argument, classical)
    if type(proof) is ImpIntro and type(target) is Imp:
        return _check(
            _extend(ctx, target.left), proof.body, target.right, classical
        )
    if type(proof) is AndIntro and type(target) is And:
        return _check(ctx, proof.left, target.left, classical) and _check(
            ctx, proof.right, target.right, classical
        )
    if type(proof) is OrIntroL and type(target) is Or:
        return _check(ctx, proof.proof, target.left, classical)
    if type(proof) is OrIntroR and type(target) is Or:
        return _check(ctx, proof.proof, target.right, classical)
    if type(proof) is OrElim:
        source = _infer(ctx, proof.disjunction, classical)
        return (
            type(source) is Or
            and _check(_extend(ctx, source.left), proof.left_case, target, classical)
            and _check(_extend(ctx, source.right), proof.right_case, target, classical)
        )
    if type(proof) is BotElim:
        return _check(ctx, proof.absurdity, Bot(), classical)
    if type(proof) is ForallIntro and type(target) is Forall:
        return _check(_under_term_binder(ctx), proof.body, target.body, classical)
    if type(proof) is ExistsIntro and type(target) is Exists and _valid_term(proof.term):
        return _check(
            ctx,
            proof.proof,
            subst_formula(target.body, 0, proof.term),
            classical,
        )
    if type(proof) is ExistsElim:
        source = _infer(ctx, proof.existential, classical)
        if type(source) is not Exists:
            return False
        lifted_ctx = _under_term_binder(ctx)
        return _check(
            _extend(lifted_ctx, source.body),
            proof.body,
            shift_formula(target, 1),
            classical,
        )
    return False


def _entry(ctx: object, proof: object, formula: object, classical: bool) -> bool:
    """Shared defensive boundary for the two public logical judgments."""

    try:
        context = _normalise_context(ctx)
        if context is None or not _valid_formula(formula) or not isinstance(proof, Proof):
            return False
        return _check(context, proof, formula, classical)
    except (AttributeError, IndexError, TypeError, ValueError, RecursionError):
        return False


def check(ctx: object, proof: object, formula: object) -> bool:
    """Check in the intuitionistic core; every DNE node is rejected.

    The broad boundary catches malformed adversarial certificates.  Internal
    code remains ordinary structural recursion, so unexpected input cannot turn
    into a false positive.
    """

    return _entry(ctx, proof, formula, False)


def check_classical(ctx: object, proof: object, formula: object) -> bool:
    """Check the explicitly labeled PA+DNE extension."""

    return _entry(ctx, proof, formula, True)


__all__ = ["check", "check_classical", "axiom_formula"]
