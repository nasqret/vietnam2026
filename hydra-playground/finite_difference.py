"""Untrusted finite-difference proposals; no tactics or certificates run here.

The bounded polynomial analyser only proposes ordinary native tactic text
and an explanatory AST. It proves nothing: both the stronger obligation and
the actual original theorem still require native proof and final replay.
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
            return None  # A larger invariant family is outside this bounded proposal.
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


# P4 is an opt-in extension. The original one-auxiliary API above deliberately
# retains its existing proposal and scheduling behavior.
MAX_COUPLED_AUXILIARIES = 2
MAX_COUPLED_PARAMETERS = 4
MAX_COUPLED_WORK = 65536
MAX_COUPLED_AST_NODES = 4096
MAX_COUPLED_COMMANDS = 16
MAX_COUPLED_BYTES = 16384


@dataclass(frozen=True, slots=True)
class CoupledStrengtheningProposal:
    commands: tuple[str, ...]
    strengthened: object
    parameter_indices: tuple[int, ...]
    divisors: tuple[int, ...]
    polynomials: tuple[tuple[tuple[tuple[int, ...], int], ...], ...]
    auxiliary_count: int
    analysis_work: int
    reason: str


class StrengtheningCancelled(ValueError):
    """The caller stopped an optional, untrusted strengthening analysis."""


class _CoupledLimit(ValueError):
    pass


class _CoupledBudget:
    def __init__(self, should_stop):
        if should_stop is not None and not callable(should_stop):
            raise TypeError("should_stop must be callable or None")
        self.should_stop = should_stop
        self.work = 0
        self.check()

    def check(self):
        if self.should_stop is not None and self.should_stop():
            raise StrengtheningCancelled("finite-difference analysis cancelled")

    def tick(self, amount=1):
        previous = self.work
        self.work += amount
        if self.work > MAX_COUPLED_WORK:
            raise _CoupledLimit("coupled finite-difference work bound exceeded")
        if self.work // 64 != previous // 64:
            self.check()


def _coupled_difference(polynomial, parameter, budget):
    result = {}
    for monomial, coefficient in polynomial.items():
        degree = monomial.count(parameter)
        remaining = tuple(index for index in monomial if index != parameter)
        for power in range(degree):
            budget.tick()
            term = tuple(sorted(remaining + (parameter,) * power))
            result[term] = result.get(term, 0) + coefficient * comb(degree, power)
            if abs(result[term]) > MAX_COEFFICIENT or len(result) > MAX_MONOMIALS:
                raise _CoupledLimit("coupled finite difference is too large")
    return {term: coefficient for term, coefficient in result.items() if coefficient}


def _coupled_reindex(term, indices, witness_count, budget, *, original=False):
    budget.tick()
    if type(term) is Var:
        if original and term.index == 0:
            return Var(witness_count - 1)
        index = term.index - (1 if original else 0)
        if index not in indices:
            raise _CoupledLimit("the proposed invariant has an unbound parameter")
        return Var(witness_count + len(indices) - 1 - indices.index(index))
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(_coupled_reindex(term.term, indices, witness_count, budget, original=original))
    if type(term) in (Add, Mul):
        return type(term)(
            _coupled_reindex(term.left, indices, witness_count, budget, original=original),
            _coupled_reindex(term.right, indices, witness_count, budget, original=original),
        )
    raise _CoupledLimit("the proposed invariant needs rigid native terms")


def _coupled_projection(goal, indices, proposition, context, witnesses, budget):
    used = set(goal.variables) | {name for name, _ in context}
    label = _fresh(PREFIX + "_pair", used)
    commands = [f"suffices {label} : {pretty_formula(proposition, list(goal.variables))}"]
    for parameter in indices:
        budget.tick()
        commands.append(f"specialize {label} {goal.variables[parameter]}")
        old, suffix = label + "_before", 2
        while old in used:
            budget.tick()
            old, suffix = label + "_before" + str(suffix), suffix + 1
        used.add(old)
    name, original_witness = label, None
    for _ in range(witnesses):
        budget.tick()
        witness = _fresh("x", used)
        if original_witness is None:
            original_witness = witness
        commands.append(f"cases {name}")
        name = _fresh(name + "_witness", used)
    left = _fresh(name + "_left", used)
    commands.extend((f"cases {name}", f"exists {original_witness}", f"exact {left}"))
    if (len(commands) > MAX_COUPLED_COMMANDS
            or sum(len(command.encode("utf-8")) + 1 for command in commands) > MAX_COUPLED_BYTES
            or any(len(command.encode("utf-8")) > 4096 for command in commands)):
        raise _CoupledLimit("coupled invariant projection exceeds its command bounds")
    return tuple(commands)


def propose_coupled_strengthening(goal, target, context, *, parameter_index=None,
                                  generalize_parameters=True, max_auxiliaries=2,
                                  should_stop=None):
    """Propose up to two auxiliary divisibility invariants, never a proof.

    Repeatedly write Delta_n F_i = g_i F_(i+1), with
    d_(i+1) = d_i / gcd(d_i, coefficients(Delta_n F_i)). The next invariant
    supplies a natural-number increment for the previous witness. Stop only
    when the last increment has a nonnegative integer polynomial quotient.
    Every base polynomial must itself have a nonnegative coefficientwise
    quotient. Other rigid parameters may be universally generalized, leaving
    them below the induction variable so an induction hypothesis can retain
    their quantifiers. These conditions guide proposals; native checking still
    owes all projection and stronger-theorem obligations.

    The old analyzer's two polynomial expansions are charged their *maximum*
    finite work, not a measured duration. Cancellation is checked around that
    bounded call and at least every 64 subsequent charged operations.
    """
    budget = _CoupledBudget(should_stop)
    if (type(max_auxiliaries) is not int or not 1 <= max_auxiliaries <= 2
            or type(generalize_parameters) is not bool):
        raise ValueError("coupled strengthening requires one or two auxiliaries and a Boolean generalization flag")
    if (type(target) is not Exists or type(target.body) is not Eq or len(context) > 32
            or any(name.startswith("IH") or name.startswith(PREFIX) for name, _ in context)):
        return None
    try:
        free = sorted(index - 1 for index in _indices(target.body) if index != 0)
        if (not free or len(free) > MAX_COUPLED_PARAMETERS
                or any(type(index) is not int or not 0 <= index < len(goal.variables) for index in free)):
            return None
        budget.tick(2 * MAX_WORK + 2 * MAX_TERM_NODES)
        problems = _linear_problems(target)
        budget.check()
        if len(problems) != 1:
            return None
        divisor, polynomial = problems[0]
        if not 1 < divisor <= 64:
            return None
        if parameter_index is None:
            parameter_index = min(free, key=lambda index: (
                -max((term.count(index) for term in polynomial), default=0), index))
        if type(parameter_index) is not int or parameter_index not in free:
            return None
        if not generalize_parameters and len(free) > 1:
            return None  # No implicit ambient-parameter capture in this extension.
        indices = (parameter_index,) + tuple(index for index in free if index != parameter_index)
        divisors, polynomials = [divisor], [polynomial]
        while True:
            current_divisor, current = divisors[-1], polynomials[-1]
            if any(coefficient < 0 or coefficient % current_divisor
                   for term, coefficient in current.items() if parameter_index not in term):
                return None
            delta = _coupled_difference(current, parameter_index, budget)
            if not delta:
                return None
            if all(value >= 0 and value % current_divisor == 0 for value in delta.values()):
                # Existing witness synthesis can express this final update.
                _quote({term: value // current_divisor for term, value in delta.items()})
                break
            if len(polynomials) - 1 == max_auxiliaries:
                return None
            common = current_divisor
            for value in delta.values():
                budget.tick()
                common = gcd(common, abs(value))
            next_divisor = current_divisor // common
            if next_divisor <= 1:
                return None  # A negative increment cannot be a natural witness.
            divisors.append(next_divisor)
            polynomials.append({term: value // common for term, value in delta.items()})
        if len(polynomials) == 1:
            return None  # No strengthening is needed for an already direct step.
        witnesses = len(polynomials)
        equations = [Eq(
            _coupled_reindex(target.body.left, indices, witnesses, budget, original=True),
            _coupled_reindex(target.body.right, indices, witnesses, budget, original=True),
        )]
        for offset, (current_divisor, current) in enumerate(zip(divisors[1:], polynomials[1:]), 1):
            positive = {term: value for term, value in current.items() if value > 0}
            negative = {term: -value for term, value in current.items() if value < 0}
            left = _coupled_reindex(_quote(positive), indices, witnesses, budget)
            product = Mul(_number(current_divisor), Var(witnesses - 1 - offset))
            right = (Add(_coupled_reindex(_quote(negative), indices, witnesses, budget), product)
                     if negative else product)
            equations.append(Eq(left, right))
        strengthened = equations[-1]
        for equation in reversed(equations[:-1]):
            strengthened = And(equation, strengthened)
        for _ in range(witnesses):
            strengthened = Exists(strengthened)
        for _ in reversed(indices):
            strengthened = Forall(strengthened)
        pending, count = [(strengthened, 0)], 0
        while pending:
            item, depth = pending.pop()
            budget.tick()
            count += 1
            if count > MAX_COUPLED_AST_NODES or depth > 64:
                raise _CoupledLimit("coupled invariant AST bound exceeded")
            if type(item) in (Exists, Forall):
                pending.append((item.body, depth + 1))
            elif type(item) in (And, Eq, Add, Mul):
                pending.extend(((item.left, depth + 1), (item.right, depth + 1)))
            elif type(item) is Succ:
                pending.append((item.term, depth + 1))
        commands = _coupled_projection(goal, indices, strengthened, context, witnesses, budget)
        budget.check()
        return CoupledStrengtheningProposal(
            commands, strengthened, indices, tuple(divisors),
            tuple(tuple(sorted(polynomial.items())) for polynomial in polynomials),
            witnesses - 1, budget.work,
            "Finite differences suggest a coupled invariant with at most two auxiliaries; "
            "all generalized and auxiliary statements remain native proof obligations.",
        )
    except StrengtheningCancelled:
        raise
    except (ValueError, TypeError, IndexError, RecursionError):
        return None
