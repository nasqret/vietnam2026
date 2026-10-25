"""Untrusted finite-difference proposals; no tactics or certificates run here.

This standalone prototype reuses the live v3 bounded polynomial *analyser*.
It is not imported by the playground. Its only output is ordinary native
tactic text and an explanatory AST; every obligation still needs native proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import comb, gcd

from arithmetic_search import (
    ArithmeticHint, MAX_COEFFICIENT, MAX_DEGREE, MAX_MONOMIALS, MAX_TERM_NODES,
    MAX_WORK, _linear_problems, _number, _quote,
)
from peano_lab.kernel.formulas import And, Eq, Exists, Forall, pretty_formula
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero

PREFIX = "hydra_fd"


@dataclass(frozen=True)
class StrengtheningProposal:
    commands: tuple[str, ...]
    strengthened: object
    parameter_index: int
    divisor: int
    common_factor: int
    auxiliary_divisor: int
    original_coefficients: tuple[tuple[int, int], ...]
    auxiliary_coefficients: tuple[tuple[int, int], ...]
    auxiliary_increment: tuple[tuple[int, int], ...]
    reason: str


def _difference(coefficients):
    """Compute P(n+1)-P(n) within the existing analyser's finite bounds."""
    result, work = {}, 0
    for degree, coefficient in coefficients.items():
        if not 0 <= degree <= MAX_DEGREE:
            raise ValueError("finite difference degree exceeded")
        for power in range(degree):
            work += 1
            if work > MAX_WORK:
                raise ValueError("finite difference work exceeded")
            result[power] = result.get(power, 0) + coefficient * comb(degree, power)
            if abs(result[power]) > MAX_COEFFICIENT:
                raise ValueError("finite difference coefficient exceeded")
    result = {power: coefficient for power, coefficient in result.items() if coefficient}
    if len(result) > MAX_MONOMIALS:
        raise ValueError("finite difference term count exceeded")
    return result


def _indices(equation):
    pending, found, count = [(equation.left, 0), (equation.right, 0)], set(), 0
    while pending:
        term, depth = pending.pop()
        count += 1
        if count > MAX_TERM_NODES or depth > 64:
            raise ValueError("finite difference source exceeds structural bounds")
        if type(term) is Var:
            found.add(term.index)
        elif type(term) is Succ:
            pending.append((term.term, depth + 1))
        elif type(term) in (Add, Mul):
            pending.extend(((term.left, depth + 1), (term.right, depth + 1)))
        elif type(term) is not Zero:
            raise ValueError("finite difference source must be rigid native arithmetic")
    return found


def _reindex(term, parameter):
    if type(term) is Var:
        if term.index == 0:
            return Var(1)  # Original witness k, under the new inner witness t.
        if term.index == parameter + 1:
            return Var(2)  # Parameter bound by the generated outer forall.
        raise ValueError("source has another free parameter")
    if type(term) is Succ:
        return Succ(_reindex(term.term, parameter))
    if type(term) in (Add, Mul):
        return type(term)(_reindex(term.left, parameter), _reindex(term.right, parameter))
    if type(term) is Zero:
        return term
    raise ValueError("source is not a rigid term")


def _fresh(base, used):
    candidate, index = base, 1
    while candidate in used:
        candidate = base + str(index)
        index += 1
    used.add(candidate)
    return candidate


def _projection(goal, parameter, proposition, context):
    """Mirror the native fresh-name rules, not a guess at existential names."""
    used = set(goal.variables) | {name for name, _ in context}
    label = _fresh(PREFIX, used)
    # specialize preserves its old forall under <name>_before[2,3,...].
    old, index = label + "_before", 2
    while old in used:
        old = label + "_before" + str(index)
        index += 1
    used.add(old)
    witness = _fresh("x", used)
    first = _fresh(label + "_witness", used)
    _fresh("x", used)  # Second existential's native eigenvariable.
    second = _fresh(first + "_witness", used)
    left = _fresh(second + "_left", used)
    commands = (
        f"suffices {label} : {pretty_formula(proposition, list(goal.variables))}",
        f"specialize {label} {goal.variables[parameter]}",
        f"cases {label}", f"cases {first}", f"cases {second}",
        f"exists {witness}", f"exact {left}",
    )
    if len(commands) > 8 or any(len(command.encode("utf-8")) > 512 for command in commands):
        raise ValueError("strengthening connector exceeds native macro bounds")
    return commands


def propose_strengthening(goal, target, context):
    """One scalar quotient, one rigid parameter, and at most one auxiliary.

    If F(n)=d*k and Delta F=g*G, let e=d/g. A candidate G(n)=e*t
    makes k'=k+t. Emit it only when G's own difference already has a
    nonnegative coefficientwise quotient by e, so a third invariant is not
    required. These arithmetic checks guide search; they certify nothing.
    """
    if type(target) is not Exists or type(target.body) is not Eq or len(context) > 32:
        return None
    if any(name.startswith("IH") or name.startswith(PREFIX) for name, _ in context):
        return None
    try:
        problems = _linear_problems(target)
        if len(problems) != 1:
            return None
        divisor, polynomial = problems[0]
        if not 1 < divisor <= 64:
            return None
        free_indices = _indices(target.body) - {0}
        if len(free_indices) != 1:
            return None
        parameter = next(iter(free_indices)) - 1
        if not 0 <= parameter < len(goal.variables):
            return None
        if any(any(index != parameter for index in monomial) for monomial in polynomial):
            return None
        coefficients = {len(monomial): value for monomial, value in polynomial.items()}
        if coefficients.get(0, 0) < 0 or coefficients.get(0, 0) % divisor:
            return None
        delta = _difference(coefficients)
        if not delta:
            return None
        common = divisor
        for value in delta.values():
            common = gcd(common, abs(value))
        auxiliary_divisor = divisor // common
        if auxiliary_divisor == 1:
            return None  # Existing direct successor-witness synthesis suffices.
        auxiliary = {degree: value // common for degree, value in delta.items()}
        if auxiliary.get(0, 0) < 0 or auxiliary.get(0, 0) % auxiliary_divisor:
            return None
        auxiliary_delta = _difference(auxiliary)
        if any(value < 0 or value % auxiliary_divisor for value in auxiliary_delta.values()):
            return None  # A larger invariant family is outside this prototype.
        increment = {degree: value // auxiliary_divisor for degree, value in auxiliary_delta.items()}
        # Quoting applies the existing <=64 numeral and coefficient policy.
        _quote({(parameter,) * degree: value for degree, value in increment.items()})
        positive = {(2,) * degree: value for degree, value in auxiliary.items() if value > 0}
        negative = {(2,) * degree: -value for degree, value in auxiliary.items() if value < 0}
        witness_term = Mul(_number(auxiliary_divisor), Var(0))
        auxiliary_eq = Eq(_quote(positive), Add(_quote(negative), witness_term) if negative else witness_term)
        original_eq = Eq(_reindex(target.body.left, parameter), _reindex(target.body.right, parameter))
        strengthened = Forall(Exists(Exists(And(original_eq, auxiliary_eq))))
        commands = _projection(goal, parameter, strengthened, context)
        reason = ("A bounded finite difference suggests a coupled divisibility invariant; "
                  "prove the stronger quantified goal by native induction before using its projection.")
        return StrengtheningProposal(commands, strengthened, parameter, divisor, common, auxiliary_divisor,
            tuple(sorted(coefficients.items())), tuple(sorted(auxiliary.items())),
            tuple(sorted(increment.items())), reason)
    except (ValueError, TypeError, IndexError, RecursionError):
        return None


def strengthening_hints(goal, target, context):
    proposal = propose_strengthening(goal, target, context)
    return () if proposal is None else (ArithmeticHint(proposal.commands, proposal.reason, False),)
