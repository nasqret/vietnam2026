"""Small, honest decision procedures for closed Peano arithmetic.

There are deliberately two different kinds of result in this module:

* :func:`decide_closed_equation` and :func:`bounded_check` report what
  computation found.  Their frozen verdict records are *not* proof terms.
* :func:`prove_closed_equation` constructs a certificate for a true closed
  equation and checks it with the independent kernel before returning it.

Quantifiers range over all natural numbers, so finite enumeration cannot
decide them in general.  ``bounded_check(formula, N)`` therefore says exactly
what it did: it interprets each quantifier over the inclusive sample
``0, ..., N`` and labels the result ``bounded``.  It never manufactures a
certificate from that finite observation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..kernel.checker import check
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import (
    Axiom,
    CongAdd,
    CongMul,
    CongS,
    EqRefl,
    EqSym,
    EqTrans,
    ForallElim,
    Proof,
)
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


class DecisionError(ValueError):
    """The requested expression is malformed, open, or outside this API."""


@dataclass(frozen=True, slots=True)
class NumeralCertificate:
    """A checked proof that one closed term equals its canonical numeral."""

    source: Term
    value: int
    normal_form: Term
    certificate: Proof


@dataclass(frozen=True, slots=True)
class EquationVerdict:
    """A computational verdict, deliberately separate from a proof term."""

    holds: bool
    left_value: int
    right_value: int
    label: str = "closed equation decision"

    def __bool__(self) -> bool:
        return self.holds


@dataclass(frozen=True, slots=True)
class BoundedVerdict:
    """Result of finite testing, never a theorem or proof certificate."""

    holds: bool
    bound: int
    has_quantifiers: bool
    label: str

    def __bool__(self) -> bool:
        return self.holds

    @property
    def complete(self) -> bool:
        """Whether finite enumeration happened to be a full decision.

        A quantifier-free closed formula is completely evaluated.  Any result
        involving a quantifier remains labeled incomplete, even when the
        finite sample found a witness or counterexample.  This conservative
        distinction keeps a reporting result from masquerading as a theorem.
        """

        return not self.has_quantifiers


def _bad_term(message: str) -> DecisionError:
    return DecisionError(f"cannot evaluate term: {message}")


def _evaluate_term(term: object, environment: tuple[int, ...]) -> int:
    """Interpret an exact kernel term in an innermost-first environment."""

    if type(term) is Var:
        if type(term.index) is not int or term.index < 0:
            raise _bad_term("variable indices must be non-negative integers")
        if term.index >= len(environment):
            raise _bad_term(f"open variable #{term.index}")
        return environment[term.index]
    if type(term) is Zero:
        return 0
    if type(term) is Succ:
        return _evaluate_term(term.term, environment) + 1
    if type(term) is Add:
        return _evaluate_term(term.left, environment) + _evaluate_term(
            term.right, environment
        )
    if type(term) is Mul:
        return _evaluate_term(term.left, environment) * _evaluate_term(
            term.right, environment
        )
    raise _bad_term("expected an exact PA term")


def evaluate_closed_term(term: Term) -> int:
    """Evaluate a closed PA term to a Python natural number.

    Free de Bruijn variables, engine metavariables, malformed nodes, and
    subclasses are rejected.  In particular, this function never guesses a
    value for a variable merely to make an equation true.
    """

    try:
        return _evaluate_term(term, ())
    except DecisionError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise DecisionError("cannot evaluate term: malformed PA term") from exc
    except RecursionError as exc:
        raise DecisionError("cannot evaluate term: expression is too deeply nested") from exc


def _require_equation(formula: object) -> Eq:
    if type(formula) is not Eq:
        raise DecisionError("closed-equation decision expects an equation")
    return formula


def decide_closed_equation(equation: Eq) -> EquationVerdict:
    """Compute both sides of a closed equation and report their equality.

    This is an evaluation result, not a certificate.  Use
    :func:`prove_closed_equation` when a tactic needs evidence for QED.
    """

    equation = _require_equation(equation)
    try:
        left = evaluate_closed_term(equation.left)
        right = evaluate_closed_term(equation.right)
    except DecisionError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise DecisionError("closed-equation decision received a malformed equation") from exc
    return EquationVerdict(left == right, left, right)


def _numeral(value: int) -> Term:
    result: Term = Zero()
    for _ in range(value):
        result = Succ(result)
    return result


def _pa_instance(name: str, *terms: Term) -> Proof:
    proof: Proof = Axiom(name)
    for term in terms:
        proof = ForallElim(proof, term)
    return proof


def _prove_numeral_add(left: Term, right: Term) -> Proof:
    """Prove ``left + right = numeral(value(left) + value(right))``."""

    if type(right) is Zero:
        return _pa_instance("PA3", left)
    if type(right) is Succ:
        unfold = _pa_instance("PA4", left, right.term)
        return EqTrans(unfold, CongS(_prove_numeral_add(left, right.term)))
    raise DecisionError("internal normalization expected a numeral")


def _prove_numeral_mul(left: Term, right: Term) -> Proof:
    """Prove ``left * right = numeral(value(left) * value(right))``."""

    if type(right) is Zero:
        return _pa_instance("PA5", left)
    if type(right) is Succ:
        unfold = _pa_instance("PA6", left, right.term)
        recursive = _prove_numeral_mul(left, right.term)
        rewrite_product = CongAdd(recursive, EqRefl(left))
        product_value = _evaluate_term(left, ()) * _evaluate_term(right.term, ())
        finish_sum = _prove_numeral_add(_numeral(product_value), left)
        return EqTrans(unfold, EqTrans(rewrite_product, finish_sum))
    raise DecisionError("internal normalization expected a numeral")


def _normalization_proof(term: Term) -> tuple[int, Term, Proof]:
    """Return value, canonical numeral, and a proof ``term = numeral``."""

    if type(term) is Zero:
        return 0, term, EqRefl(term)
    if type(term) is Succ:
        value, numeral, child_proof = _normalization_proof(term.term)
        return value + 1, Succ(numeral), CongS(child_proof)
    if type(term) is Add:
        left_value, left_numeral, left_proof = _normalization_proof(term.left)
        right_value, right_numeral, right_proof = _normalization_proof(term.right)
        rewrite_arguments = CongAdd(left_proof, right_proof)
        calculate = _prove_numeral_add(left_numeral, right_numeral)
        return (
            left_value + right_value,
            _numeral(left_value + right_value),
            EqTrans(rewrite_arguments, calculate),
        )
    if type(term) is Mul:
        left_value, left_numeral, left_proof = _normalization_proof(term.left)
        right_value, right_numeral, right_proof = _normalization_proof(term.right)
        rewrite_arguments = CongMul(left_proof, right_proof)
        calculate = _prove_numeral_mul(left_numeral, right_numeral)
        return (
            left_value * right_value,
            _numeral(left_value * right_value),
            EqTrans(rewrite_arguments, calculate),
        )
    # Validate variables and malformed nodes with the public-quality message.
    _evaluate_term(term, ())
    raise DecisionError("internal normalization failed")


def _value_limit(max_value: int) -> DecisionError:
    return DecisionError(
        f"cannot prove term: value exceeds the explicit {max_value} limit"
    )


def _bounded_normalization_proof(
    term: Term,
    max_value: int,
) -> tuple[int, Term, Proof]:
    """Normalize a closed term without first constructing an oversized value.

    Every recursive result is already at most ``max_value``.  Addition and
    multiplication therefore test their bounds *before* performing the Python
    operation or allocating its unary numeral.
    """

    if type(term) is Zero:
        return 0, term, EqRefl(term)
    if type(term) is Succ:
        value, numeral, child_proof = _bounded_normalization_proof(
            term.term, max_value
        )
        if value >= max_value:
            raise _value_limit(max_value)
        return value + 1, Succ(numeral), CongS(child_proof)
    if type(term) is Add:
        left_value, left_numeral, left_proof = _bounded_normalization_proof(
            term.left, max_value
        )
        right_value, right_numeral, right_proof = _bounded_normalization_proof(
            term.right, max_value
        )
        if left_value > max_value - right_value:
            raise _value_limit(max_value)
        value = left_value + right_value
        rewrite_arguments = CongAdd(left_proof, right_proof)
        calculate = _prove_numeral_add(left_numeral, right_numeral)
        return value, _numeral(value), EqTrans(rewrite_arguments, calculate)
    if type(term) is Mul:
        left_value, left_numeral, left_proof = _bounded_normalization_proof(
            term.left, max_value
        )
        right_value, right_numeral, right_proof = _bounded_normalization_proof(
            term.right, max_value
        )
        if left_value != 0 and right_value > max_value // left_value:
            raise _value_limit(max_value)
        value = left_value * right_value
        rewrite_arguments = CongMul(left_proof, right_proof)
        calculate = _prove_numeral_mul(left_numeral, right_numeral)
        return value, _numeral(value), EqTrans(rewrite_arguments, calculate)
    # Reuse the evaluator's exact messages for variables and malformed nodes.
    _evaluate_term(term, ())
    raise DecisionError("internal bounded normalization failed")


def prove_closed_term(
    term: Term,
    *,
    max_value: int = 128,
) -> NumeralCertificate:
    """Return checked evidence ``term = numeral(value)`` within a value bound.

    ``max_value`` bounds every intermediate value, not merely the final one.
    Consequently a compact repeated-multiplication term is rejected before a
    giant Python integer, unary numeral, or proof tree can be constructed.
    Computation only selects the claimed numeral: the independent kernel must
    still validate the exact equality before this function returns it.
    """

    if type(max_value) is not int or max_value < 0:
        raise DecisionError("closed-term value limit must be a non-negative integer")
    try:
        value, normal_form, certificate = _bounded_normalization_proof(
            term, max_value
        )
        equation = Eq(term, normal_form)
        if not check((), certificate, equation):
            raise DecisionError(
                "kernel rejected the generated closed-term certificate"
            )
        return NumeralCertificate(term, value, normal_form, certificate)
    except DecisionError:
        raise
    except RecursionError:
        raise DecisionError(
            "cannot prove term: expression is too deeply nested"
        ) from None
    except (AttributeError, TypeError, ValueError):
        raise DecisionError("cannot prove term: malformed PA term") from None


def prove_closed_equation(equation: Eq) -> Proof | None:
    """Return checked evidence for a true closed equation, otherwise ``None``.

    The generated proof normalizes both sides using congruence and PA3--PA6;
    computation itself is never trusted as a kernel rule.  A positive result
    crosses the independent checker here, as well as at normal QED
    finalization.  Thus a bug in this untrusted generator cannot return an
    invalid certificate for a tactic to install.
    """

    try:
        equation = _require_equation(equation)
        verdict = decide_closed_equation(equation)
        if not verdict.holds:
            return None
        left_value, left_numeral, left_proof = _normalization_proof(equation.left)
        right_value, right_numeral, right_proof = _normalization_proof(equation.right)
        if left_value != right_value or left_numeral != right_numeral:
            raise DecisionError(
                "internal equation normalization disagreed with evaluation"
            )
        certificate = EqTrans(left_proof, EqSym(right_proof))
        if not check((), certificate, equation):
            raise DecisionError("kernel rejected the generated equation certificate")
        return certificate
    except DecisionError:
        raise
    except RecursionError:
        raise DecisionError(
            "cannot prove equation: expression is too deeply nested"
        ) from None
    except (AttributeError, TypeError, ValueError):
        raise DecisionError("cannot prove equation: malformed PA equation") from None


def _evaluate_formula(formula: object, environment: tuple[int, ...], bound: int) -> bool:
    if type(formula) is Eq:
        return _evaluate_term(formula.left, environment) == _evaluate_term(
            formula.right, environment
        )
    if type(formula) is Bot:
        return False
    if type(formula) is Imp:
        return not _evaluate_formula(formula.antecedent, environment, bound) or (
            _evaluate_formula(formula.consequent, environment, bound)
        )
    if type(formula) is And:
        return _evaluate_formula(formula.left, environment, bound) and _evaluate_formula(
            formula.right, environment, bound
        )
    if type(formula) is Or:
        return _evaluate_formula(formula.left, environment, bound) or _evaluate_formula(
            formula.right, environment, bound
        )
    if type(formula) is Forall:
        return all(
            _evaluate_formula(formula.body, (value,) + environment, bound)
            for value in range(bound + 1)
        )
    if type(formula) is Exists:
        return any(
            _evaluate_formula(formula.body, (value,) + environment, bound)
            for value in range(bound + 1)
        )
    raise DecisionError("bounded check expects an exact PA formula")


def _validate_term_at_depth(term: object, depth: int) -> None:
    """Check shape and binding without relying on evaluator control flow."""

    if type(term) is Var:
        if type(term.index) is not int or term.index < 0:
            raise _bad_term("variable indices must be non-negative integers")
        if term.index >= depth:
            raise _bad_term(f"open variable #{term.index}")
        return
    if type(term) is Zero:
        return
    if type(term) is Succ:
        _validate_term_at_depth(term.term, depth)
        return
    if type(term) in (Add, Mul):
        _validate_term_at_depth(term.left, depth)
        _validate_term_at_depth(term.right, depth)
        return
    raise _bad_term("expected an exact PA term")


def _validate_formula_at_depth(formula: object, depth: int) -> None:
    if type(formula) is Eq:
        _validate_term_at_depth(formula.left, depth)
        _validate_term_at_depth(formula.right, depth)
        return
    if type(formula) is Bot:
        return
    if type(formula) in (Imp, And, Or):
        _validate_formula_at_depth(formula.left, depth)
        _validate_formula_at_depth(formula.right, depth)
        return
    if type(formula) in (Forall, Exists):
        _validate_formula_at_depth(formula.body, depth + 1)
        return
    raise DecisionError("bounded check expects an exact PA formula")


def _has_quantifiers(formula: Formula) -> bool:
    if type(formula) in (Forall, Exists):
        return True
    if type(formula) in (Imp, And, Or):
        return _has_quantifiers(formula.left) or _has_quantifiers(formula.right)
    return False


def bounded_check(formula: Formula, bound: int) -> BoundedVerdict:
    """Test a closed formula with every quantifier restricted to ``0..bound``.

    The endpoint is included, so ``bound=0`` still tests the value zero.  The
    returned label contains the word ``bounded`` and the exact finite domain.
    No outcome of this function is a :class:`~peano_lab.kernel.proofs.Proof`.
    """

    if type(bound) is not int or bound < 0:
        raise DecisionError("bounded-check limit must be a non-negative integer")
    try:
        # Validate the entire syntax tree before interpreting it.  Boolean
        # short-circuiting must not hide an open variable in an unvisited arm.
        _validate_formula_at_depth(formula, 0)
        holds = _evaluate_formula(formula, (), bound)
        quantified = _has_quantifiers(formula)
    except DecisionError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise DecisionError("bounded check received a malformed PA formula") from exc
    except RecursionError as exc:
        raise DecisionError("cannot check formula: expression is too deeply nested") from exc
    return BoundedVerdict(
        holds=holds,
        bound=bound,
        has_quantifiers=quantified,
        label=f"bounded check over 0..{bound} (inclusive)",
    )


__all__ = [
    "DecisionError",
    "NumeralCertificate",
    "EquationVerdict",
    "BoundedVerdict",
    "evaluate_closed_term",
    "decide_closed_equation",
    "prove_closed_term",
    "prove_closed_equation",
    "bounded_check",
]
