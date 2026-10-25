"""Small untrusted polynomial analyses that propose ordinary native tactics.

The integer arithmetic in this module is guidance, never proof evidence.  A
proposed witness or equality bridge has exactly the same authority as model
text: the caller must execute every line through the original native surface
and independently replay a completed proof.  No certificates or imported
target theorems are constructed here.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from peano_lab.engine.state import instantiate_formula
from peano_lab.kernel.formulas import And, Eq, Exists
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero, pretty_term


# These are proposal-generation bounds, separate from both native arithmetic
# tactic limits and the enclosing search budgets. Expansion is never unbounded.
MAX_TERM_NODES = 256
MAX_DEGREE = 12
MAX_MONOMIALS = 64
MAX_COEFFICIENT = 4096
MAX_WORK = 16384
MAX_EQUATIONS = 12
MAX_REDUCTIONS = 3
MAX_REDUCTION_STATES = 32
MAX_PLAN_STEPS = 24


class _AnalysisLimit(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ArithmeticHint:
    commands: tuple[str, ...]
    reason: str
    closes_goal: bool = False


@dataclass(frozen=True, slots=True)
class _Equation:
    name: str
    formula: Eq
    left: dict
    right: dict
    difference: dict


def _bounded(poly):
    result = {monomial: coefficient for monomial, coefficient in poly.items() if coefficient}
    if len(result) > MAX_MONOMIALS or any(
            len(monomial) > MAX_DEGREE or abs(coefficient) > MAX_COEFFICIENT
            for monomial, coefficient in result.items()):
        raise _AnalysisLimit("polynomial proposal exceeded its structural bound")
    return result


def _add(left, right, factor=1):
    result = dict(left)
    for monomial, coefficient in right.items():
        result[monomial] = result.get(monomial, 0) + factor * coefficient
    return _bounded(result)


def _scale(poly, factor):
    return _bounded({monomial: factor * coefficient for monomial, coefficient in poly.items()})


def _polynomial(term):
    """Expand only a bounded native rigid term; unsupported terms stay unknown."""
    inspected = work = 0

    def visit(item, depth=0):
        nonlocal inspected, work
        inspected += 1
        if inspected > MAX_TERM_NODES or depth > 64:
            raise _AnalysisLimit("term proposal exceeded its structural bound")
        if type(item) is Zero:
            return {}
        if type(item) is Var and 0 <= item.index < 64:
            return {(item.index,): 1}
        if type(item) is Succ:
            return _add(visit(item.term, depth + 1), {(): 1})
        if type(item) not in (Add, Mul):
            raise _AnalysisLimit("only rigid native arithmetic terms are supported")
        left, right = visit(item.left, depth + 1), visit(item.right, depth + 1)
        if type(item) is Add:
            return _add(left, right)
        result = {}
        for first, a in left.items():
            for second, b in right.items():
                work += 1
                if work > MAX_WORK or len(first) + len(second) > MAX_DEGREE:
                    raise _AnalysisLimit("polynomial product exceeded its work bound")
                monomial = tuple(sorted(first + second))
                result[monomial] = result.get(monomial, 0) + a * b
                if len(result) > MAX_MONOMIALS:
                    raise _AnalysisLimit("polynomial product has too many monomials")
        return _bounded(result)

    return visit(term)


def polynomial_identity(formula):
    """Return True/False for a bounded polynomial equality, or None if unknown."""
    if type(formula) is not Eq:
        return None
    try:
        return _polynomial(formula.left) == _polynomial(formula.right)
    except (ValueError, RecursionError):
        return None


def _equations(context):
    equations = []
    for name, formula in context[:32]:
        if type(formula) is not Eq:
            continue
        try:
            left, right = _polynomial(formula.left), _polynomial(formula.right)
            difference = _add(left, right, -1)
        except (ValueError, RecursionError):
            continue
        if difference:
            equations.append(_Equation(name, formula, left, right, difference))
        if len(equations) == MAX_EQUATIONS:
            break
    return tuple(equations)


def _order(monomial):
    return len(monomial), monomial


def _reduce(poly, equations, *, divisor=None):
    """Try at most three scalar equality reductions, retaining alternatives.

    With a divisor, seek a nonnegative integer polynomial quotient. Without
    one, seek an exact linear combination of the supplied local equalities.
    This deliberately incomplete elimination is only a tactic proposal aid.
    """
    queue = deque([(poly, ())])
    seen = {tuple(sorted(poly.items()))}
    inspected = 0
    while queue and inspected < MAX_REDUCTION_STATES:
        current, path = queue.popleft()
        inspected += 1
        offending = [m for m, c in current.items()
                     if divisor is None or c < 0 or c % divisor]
        if not offending:
            return current, path
        if len(path) == MAX_REDUCTIONS:
            continue
        monomial = max(offending, key=_order)
        coefficient = current[monomial]
        for index, equation in enumerate(equations):
            if any(previous == index for previous, _ in path):
                continue
            if max(equation.difference, key=_order) != monomial:
                continue
            pivot = equation.difference[monomial]
            factors = []
            if coefficient % pivot == 0:
                factors.append(coefficient // pivot)
            if divisor is not None:
                # Small modular alternatives can work when exact elimination
                # would introduce a negative coefficient into the witness.
                for magnitude in range(1, min(divisor, 16) + 1):
                    for factor in (magnitude, -magnitude):
                        if (coefficient - factor * pivot) % divisor == 0 and factor not in factors:
                            factors.append(factor)
                    if len(factors) >= 3:
                        break
            for factor in factors[:3]:
                if not factor or abs(factor) > 64:
                    continue
                try:
                    following = _add(current, equation.difference, -factor)
                except ValueError:
                    continue
                key = tuple(sorted(following.items()))
                if key in seen or len(seen) >= MAX_REDUCTION_STATES:
                    continue
                seen.add(key)
                queue.append((following, path + ((index, factor),)))
    return None


def _number(value):
    if type(value) is not int or not 0 <= value <= 64:
        raise _AnalysisLimit("a proposed surface numeral must be in 0..64")
    term = Zero()
    for _ in range(value):
        term = Succ(term)
    return term


def _sum(terms):
    terms = list(terms)
    if not terms:
        return Zero()
    result = terms[0]
    for term in terms[1:]:
        result = Add(result, term)
    return result


def _quote(poly):
    """Quote a nonnegative polynomial as an ordinary PA term, not a proof."""
    terms = []
    # Put independent witness variables first, then larger powers of each
    # parameter; constants last. This keeps induction updates easy to inspect.
    order = sorted(poly, key=lambda m: (not bool(m), m[0] if m else 0, -len(m), m))
    for monomial in order:
        coefficient = poly[monomial]
        if not 0 < coefficient <= 64:
            raise _AnalysisLimit("a witness needs nonnegative bounded coefficients")
        if not monomial:
            terms.append(_number(coefficient))
            continue
        term = Var(monomial[0])
        for index in monomial[1:]:
            term = Mul(term, Var(index))
        if coefficient != 1:
            term = Mul(_number(coefficient), term)
        terms.append(term)
    return _sum(terms)


def _render(term, variables):
    text = pretty_term(term, list(variables))
    if len(text.encode("utf-8")) > 448:
        raise _AnalysisLimit("a proposed arithmetic term is too long")
    return text


def _bridge(target, equations, variables):
    left, right = _polynomial(target.left), _polynomial(target.right)
    difference = _add(left, right, -1)
    if not difference:
        if target.left == target.right:
            return ("refl",)
        return ("simp",) if not left else ("ring",)
    reduction = _reduce(difference, equations)
    if reduction is None:
        return None
    _, path = reduction
    for reverse in (False, True):
        sources, source_polynomial, rewrites = [], {}, []
        for index, factor in path:
            factor = -factor if reverse else factor
            equation = equations[index]
            source = equation.formula.left if factor > 0 else equation.formula.right
            polynomial = equation.left if factor > 0 else equation.right
            magnitude = abs(factor)
            sources.append(source if magnitude == 1 else Mul(_number(magnitude), source))
            source_polynomial = _add(source_polynomial, polynomial, magnitude)
            rewrites.append(f"rewrite {'<- ' if factor < 0 else ''}{equation.name}")
        remainder = _add(right if reverse else left, source_polynomial, -1)
        if any(value < 0 for value in remainder.values()):
            continue
        middle = _sum(sources + ([_quote(remainder)] if remainder else []))
        prefix = ("symm",) if reverse else ()
        if middle == (target.right if reverse else target.left):
            return prefix + (*rewrites, "ring")
        return prefix + (f"trans ({_render(middle, variables)})", "ring", *rewrites, "ring")
    return None


def _linear_problems(target):
    """Affine equations for the outer witness, also under nested exists/and."""
    depth, body = 0, target
    while type(body) is Exists and depth < 3:
        depth += 1
        body = body.body
    if not depth or type(body) is Exists:
        return ()
    stack, leaves = [body], []
    while stack and len(leaves) < 8:
        formula = stack.pop()
        if type(formula) is And:
            stack.extend((formula.right, formula.left))
        elif type(formula) is Eq:
            leaves.append(formula)
        else:
            return ()
        if len(stack) > 8:
            return ()
    if stack:
        return ()
    result = []
    witness = depth - 1
    for formula in leaves:
        difference = _add(_polynomial(formula.left), _polynomial(formula.right), -1)
        coefficient = difference.get((witness,), 0)
        if not coefficient or abs(coefficient) > 64:
            continue
        rest = {m: c for m, c in difference.items() if m != (witness,)}
        if any(any(index < depth for index in monomial) for monomial in rest):
            continue
        numerator = {tuple(index - depth for index in m): c if coefficient < 0 else -c
                     for m, c in rest.items()}
        result.append((abs(coefficient), numerator))
    return tuple(result)


def _witness(target, equations):
    for divisor, numerator in _linear_problems(target):
        reduction = _reduce(numerator, equations, divisor=divisor)
        if reduction is None:
            continue
        reduced, path = reduction
        quotient = {m: c // divisor for m, c in reduced.items()}
        try:
            return _quote(quotient), path
        except ValueError:
            continue
    return None


def _plan(target, equations, variables, *, depth=0):
    if depth > 6:
        return (), False
    if type(target) is Eq:
        bridge = _bridge(target, equations, variables)
        return (bridge, True) if bridge else ((), False)
    if type(target) is Exists:
        found = _witness(target, equations)
        if found is None:
            return (), False
        witness, _ = found
        tail, closes = _plan(instantiate_formula(target.body, witness), equations, variables, depth=depth + 1)
        return (f"exists ({_render(witness, variables)})",) + tail, closes
    if type(target) is And:
        left, first_closes = _plan(target.left, equations, variables, depth=depth + 1)
        if not first_closes:
            return (), False
        right, second_closes = _plan(target.right, equations, variables, depth=depth + 1)
        if not second_closes:
            return (), False
        return ("split",) + left + right, True
    return (), False


def arithmetic_hints(goal, target, context):
    """Return a bounded witness/bridge plan, always marked as heuristic work."""
    if type(target) not in (Eq, Exists):
        return ()
    try:
        equations = _equations(context)
        commands, closes = _plan(target, equations, goal.variables)
        if not commands or len(commands) > MAX_PLAN_STEPS:
            return ()
        reason = ("Synthesize nonnegative polynomial witnesses from the goal and local equalities; "
                  "check their obligations by native equality bridges."
                  if type(target) is Exists else
                  "Expose a bounded polynomial consequence of local equalities with native trans, rewrite, and ring."
                  if any(command.startswith("rewrite ") for command in commands) else
                  "A bounded polynomial comparison suggests this identity; the native arithmetic tactic must prove it.")
        return (ArithmeticHint(commands, reason, closes),)
    except (ValueError, TypeError, IndexError, RecursionError):
        return ()


def induction_hints(goal, target, context):
    """Give modular-existential induction a useful base-case macro when possible."""
    if type(target) is not Exists or any(name == "IH" or name.startswith("IH") for name, _ in context):
        return ()
    try:
        problems = _linear_problems(target)
        result = []
        for index, variable in enumerate(goal.variables):
            relevant = [(divisor, numerator) for divisor, numerator in problems
                        if any(index in monomial for monomial in numerator)]
            if not relevant:
                continue
            for divisor, numerator in relevant:
                base = {m: c for m, c in numerator.items() if index not in m}
                if any(c < 0 or c % divisor for c in base.values()):
                    continue
                commands = (f"induction {variable}",)
                if type(target.body) is Eq:
                    witness = _quote({m: c // divisor for m, c in base.items()})
                    commands += (f"exists ({_render(witness, goal.variables)})", "simp" if not base else "ring")
                result.append(ArithmeticHint(commands,
                    "Induct on a parameter of the modular witness equation and try its computed base witness."))
                break
            if len(result) == 3:
                break
        return tuple(result)
    except (ValueError, TypeError, IndexError, RecursionError):
        return ()


def arithmetic_priority(goal, target, context):
    """Favor calculable obligations over uninformed witness branches, not truth."""
    # A computable second witness says nothing about an already bad first
    # conjunct. Favor only a plan covering the whole focused obligation.
    if any(hint.closes_goal for hint in arithmetic_hints(goal, target, context)):
        return 0
    if type(target) is Eq and polynomial_identity(target) is False:
        return 2
    return 1


__all__ = ["ArithmeticHint", "arithmetic_hints", "arithmetic_priority", "induction_hints",
           "polynomial_identity"]
