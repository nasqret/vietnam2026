"""Bounded, certificate-producing normalization for PA polynomial identities.

``ring`` computes a sparse commutative-semiring normal form only to choose a
proof path.  Every addition, multiplication, permutation, distribution, and
closed coefficient calculation is accompanied by an ordinary kernel proof
term.  The generated certificate is checked here before it can close a goal;
normal QED checks it again against the session owner's original theorem.

The module is deliberately below ``library/``.  Its caller supplies exact
closed theorem formula/certificate pairs, and :class:`_LawBook` rechecks them
before use.  No theorem name or polynomial computation is trusted by the
kernel.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from math import isfinite
from time import monotonic
from typing import Callable

from ..kernel.checker import axiom_formula, check
from ..kernel.formulas import Eq, Forall, Formula
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
from ..kernel.subst import subst_formula
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero
from .decide import DecisionError, prove_closed_equation
from .proof_reduction import ProofReductionError, normalise_cuts
from .state import (
    ProofState,
    apply_formula_subst,
    invariants_ok,
    metas_in_formula,
    record_step,
    replace_current_hole,
)
from .tactics import TacticError, TacticLimit


Monomial = tuple[tuple[int, int], ...]
Polynomial = tuple[tuple[Monomial, int], ...]

ZERO = Zero()
ONE = Succ(ZERO)

RING_LAW_NAMES = (
    "zero_add",
    "add_assoc",
    "add_comm",
    "mul_zero_left",
    "one_mul",
    "mul_one",
    "mul_assoc",
    "mul_comm",
    "mul_add",
    "add_mul",
)


@dataclass(frozen=True, slots=True)
class RingLaw:
    """One untrusted library payload supplied to the ring engine."""

    name: str
    formula: Formula
    certificate: Proof

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise TypeError("a ring law needs a non-empty text name")
        if not isinstance(self.formula, Formula) or not isinstance(
            self.certificate, Proof
        ):
            raise TypeError("a ring law needs an exact formula and proof certificate")


@dataclass(frozen=True, slots=True)
class RingLimits:
    """Explicit browser/resource bounds for one normalization attempt."""

    max_ast_nodes: int = 256
    max_ast_depth: int = 64
    max_variables: int = 16
    max_degree: int = 16
    max_monomials: int = 64
    max_coefficient: int = 128
    max_work_units: int = 25_000
    max_proof_nodes: int = 100_000
    max_proof_depth: int = 256
    max_seconds: float = 5.0

    def __post_init__(self) -> None:
        integer_fields = (
            self.max_ast_nodes,
            self.max_ast_depth,
            self.max_variables,
            self.max_degree,
            self.max_monomials,
            self.max_coefficient,
            self.max_work_units,
            self.max_proof_nodes,
            self.max_proof_depth,
        )
        if any(type(value) is not int or value < 1 for value in integer_fields):
            raise ValueError("ring integer limits must be positive integers")
        finite_time = False
        if type(self.max_seconds) in (int, float):
            try:
                finite_time = isfinite(self.max_seconds)
            except OverflowError:
                finite_time = False
        if not finite_time or self.max_seconds <= 0:
            raise ValueError("ring time limit must be positive")


DEFAULT_RING_LIMITS = RingLimits()


@dataclass(frozen=True, slots=True)
class EqualityCertificate:
    """A proof paired with the exact syntactic endpoints it must connect."""

    left: Term
    right: Term
    proof: Proof


@dataclass(frozen=True, slots=True)
class TermNormalization:
    source: Term
    polynomial: Polynomial
    normal_form: Term
    proof: Proof

    @property
    def equality(self) -> EqualityCertificate:
        return EqualityCertificate(self.source, self.normal_form, self.proof)


@dataclass(frozen=True, slots=True)
class RingResult:
    equation: Eq
    polynomial: Polynomial
    normal_form: Term
    certificate: Proof
    proof_nodes: int
    proof_depth: int
    work_units: int


class _Budget:
    def __init__(
        self,
        limits: RingLimits,
        clock: Callable[[], float],
    ) -> None:
        if type(limits) is not RingLimits:
            raise TacticError("`ring` needs exact RingLimits.")
        if not callable(clock):
            raise TacticError("`ring` needs a clock for its time limit.")
        self.limits = limits
        self.clock = clock
        self.started = clock()
        self.work_units = 0

    def tick(self, amount: int = 1) -> None:
        self.work_units += amount
        if self.work_units > self.limits.max_work_units:
            raise TacticLimit(
                f"`ring` exceeded its {self.limits.max_work_units}-work-unit limit."
            )
        if self.clock() - self.started > self.limits.max_seconds:
            raise TacticLimit(
                f"`ring` exceeded its {self.limits.max_seconds:g}-second time limit."
            )

    def limit(self, message: str) -> None:
        raise TacticLimit(f"`ring` exceeded its {message} limit.")


def _refl(term: Term, budget: _Budget) -> EqualityCertificate:
    budget.tick()
    return EqualityCertificate(term, term, EqRefl(term))


def _symm(value: EqualityCertificate, budget: _Budget) -> EqualityCertificate:
    budget.tick()
    return EqualityCertificate(value.right, value.left, EqSym(value.proof))


def _trans(
    first: EqualityCertificate,
    second: EqualityCertificate,
    budget: _Budget,
) -> EqualityCertificate:
    if first.right != second.left:
        raise TacticError("internal ring proof endpoints do not compose.")
    budget.tick()
    return EqualityCertificate(
        first.left,
        second.right,
        EqTrans(first.proof, second.proof),
    )


def _cong_add(
    left: EqualityCertificate,
    right: EqualityCertificate,
    budget: _Budget,
) -> EqualityCertificate:
    budget.tick()
    return EqualityCertificate(
        Add(left.left, right.left),
        Add(left.right, right.right),
        CongAdd(left.proof, right.proof),
    )


def _cong_mul(
    left: EqualityCertificate,
    right: EqualityCertificate,
    budget: _Budget,
) -> EqualityCertificate:
    budget.tick()
    return EqualityCertificate(
        Mul(left.left, right.left),
        Mul(left.right, right.right),
        CongMul(left.proof, right.proof),
    )


def _proof_metrics(proof: Proof, limits: RingLimits) -> tuple[int, int]:
    pending = [(proof, 1)]
    nodes = 0
    maximum_depth = 0
    try:
        while pending:
            current, depth = pending.pop()
            nodes += 1
            maximum_depth = max(maximum_depth, depth)
            if nodes > limits.max_proof_nodes:
                raise TacticLimit(
                    f"`ring` exceeded its {limits.max_proof_nodes}-proof-node limit."
                )
            if depth > limits.max_proof_depth:
                raise TacticLimit(
                    f"`ring` exceeded its {limits.max_proof_depth}-proof-depth limit."
                )
            for item in fields(current):
                child = getattr(current, item.name)
                if isinstance(child, Proof):
                    pending.append((child, depth + 1))
    except TacticLimit:
        raise
    except (AttributeError, TypeError, ValueError):
        raise TacticError("internal ring proof is malformed.") from None
    return nodes, maximum_depth


def _scan_equation(equation: Eq, budget: _Budget) -> None:
    pending = [(equation.left, 1), (equation.right, 1)]
    nodes = 0
    variables: set[int] = set()
    while pending:
        term, depth = pending.pop()
        budget.tick()
        nodes += 1
        if nodes > budget.limits.max_ast_nodes:
            budget.limit(f"{budget.limits.max_ast_nodes}-AST-node")
        if depth > budget.limits.max_ast_depth:
            budget.limit(f"{budget.limits.max_ast_depth}-AST-depth")
        if type(term) is Var:
            if type(term.index) is not int or term.index < 0:
                raise TacticError("`ring` found a malformed variable index.")
            variables.add(term.index)
        elif type(term) is Zero:
            pass
        elif type(term) is Succ:
            pending.append((term.term, depth + 1))
        elif type(term) in (Add, Mul):
            pending.append((term.right, depth + 1))
            pending.append((term.left, depth + 1))
        else:
            raise TacticError(
                "`ring` needs rigid terms with no unresolved metavariables."
            )
    if len(variables) > budget.limits.max_variables:
        budget.limit(f"{budget.limits.max_variables}-variable")


def _numeral(value: int, budget: _Budget) -> Term:
    if type(value) is not int or value < 0:
        raise TacticError("internal ring coefficient is not a natural number.")
    if value > budget.limits.max_coefficient:
        budget.limit(f"coefficient-{budget.limits.max_coefficient}")
    result: Term = ZERO
    for _ in range(value):
        budget.tick()
        result = Succ(result)
    return result


def _as_numeral(term: Term, budget: _Budget) -> int | None:
    count = 0
    current = term
    while type(current) is Succ:
        budget.tick()
        count += 1
        if count > budget.limits.max_coefficient:
            budget.limit(f"coefficient-{budget.limits.max_coefficient}")
        current = current.term
    return count if type(current) is Zero else None


def _monomial_key(monomial: Monomial) -> tuple[int, Monomial]:
    return sum(exponent for _, exponent in monomial), monomial


def _polynomial(entries: dict[Monomial, int], budget: _Budget) -> Polynomial:
    cleaned: list[tuple[Monomial, int]] = []
    for monomial, coefficient in entries.items():
        if coefficient == 0:
            continue
        if coefficient < 0:
            raise TacticError("internal ring coefficient became negative.")
        if coefficient > budget.limits.max_coefficient:
            budget.limit(f"coefficient-{budget.limits.max_coefficient}")
        degree = sum(exponent for _, exponent in monomial)
        if degree > budget.limits.max_degree:
            budget.limit(f"degree-{budget.limits.max_degree}")
        if any(
            type(index) is not int
            or index < 0
            or type(exponent) is not int
            or exponent < 1
            for index, exponent in monomial
        ):
            raise TacticError("internal ring monomial is malformed.")
        if tuple(index for index, _ in monomial) != tuple(
            sorted(index for index, _ in monomial)
        ):
            raise TacticError("internal ring monomial is not canonical.")
        cleaned.append((monomial, coefficient))
    cleaned.sort(key=lambda item: _monomial_key(item[0]))
    if len(cleaned) > budget.limits.max_monomials:
        budget.limit(f"{budget.limits.max_monomials}-monomial")
    return tuple(cleaned)


def _add_polynomial_data(
    left: Polynomial,
    right: Polynomial,
    budget: _Budget,
) -> Polynomial:
    entries = dict(left)
    for monomial, coefficient in right:
        budget.tick()
        entries[monomial] = entries.get(monomial, 0) + coefficient
    return _polynomial(entries, budget)


def _multiply_monomials(
    left: Monomial,
    right: Monomial,
    budget: _Budget,
) -> Monomial:
    powers = dict(left)
    for index, exponent in right:
        budget.tick()
        powers[index] = powers.get(index, 0) + exponent
    result = tuple(sorted(powers.items()))
    if sum(exponent for _, exponent in result) > budget.limits.max_degree:
        budget.limit(f"degree-{budget.limits.max_degree}")
    return result


def _join_add(items: tuple[Term, ...]) -> Term:
    result: Term = ZERO
    for item in reversed(items):
        result = Add(item, result)
    return result


def _join_mul(items: tuple[Term, ...]) -> Term:
    result: Term = ONE
    for item in reversed(items):
        result = Mul(item, result)
    return result


def _monomial_factors(monomial: Monomial, budget: _Budget) -> tuple[Term, ...]:
    factors: list[Term] = []
    for index, exponent in monomial:
        for _ in range(exponent):
            budget.tick()
            factors.append(Var(index))
    return tuple(factors)


def _quote_monomial(monomial: Monomial, budget: _Budget) -> Term:
    return _join_mul(_monomial_factors(monomial, budget))


def _quote_summand(entry: tuple[Monomial, int], budget: _Budget) -> Term:
    monomial, coefficient = entry
    return Mul(_numeral(coefficient, budget), _quote_monomial(monomial, budget))


def _summands(polynomial: Polynomial, budget: _Budget) -> tuple[Term, ...]:
    return tuple(_quote_summand(entry, budget) for entry in polynomial)


def _quote_polynomial(polynomial: Polynomial, budget: _Budget) -> Term:
    return _join_add(_summands(polynomial, budget))


def _term_key(term: Term) -> tuple:
    if type(term) is Zero:
        return (0,)
    if type(term) is Succ:
        return (1, _term_key(term.term))
    if type(term) is Var:
        return (2, term.index)
    if type(term) is Add:
        return (3, _term_key(term.left), _term_key(term.right))
    if type(term) is Mul:
        return (4, _term_key(term.left), _term_key(term.right))
    raise TacticError("internal ring term ordering received malformed syntax.")


class _LawBook:
    def __init__(
        self,
        laws: tuple[RingLaw, ...],
        budget: _Budget,
    ) -> None:
        if not isinstance(laws, tuple) or not all(type(law) is RingLaw for law in laws):
            raise TacticError("`ring` needs an exact tuple of checked laws.")
        table: dict[str, RingLaw] = {}
        for law in laws:
            budget.tick()
            if law.name in table:
                raise TacticError(f"duplicate ring law {law.name!r}.")
            _proof_metrics(law.certificate, budget.limits)
            if not check((), law.certificate, law.formula):
                raise TacticError(
                    f"the independent kernel rejected ring law {law.name!r}."
                )
            table[law.name] = law
        missing = [name for name in RING_LAW_NAMES if name not in table]
        if missing:
            raise TacticError("missing checked ring law(s): " + ", ".join(missing) + ".")
        self.table = table
        self.budget = budget
        self.cache: dict[tuple[str, tuple[Term, ...]], EqualityCertificate] = {}

    def instance(self, name: str, *terms: Term) -> EqualityCertificate:
        key = (name, tuple(terms))
        cached = self.cache.get(key)
        if cached is not None:
            self.budget.tick()
            return cached
        law = self.table[name]
        formula = law.formula
        proof = law.certificate
        for term in terms:
            self.budget.tick()
            if type(formula) is not Forall:
                raise TacticError(f"ring law {name!r} received too many terms.")
            formula = subst_formula(formula.body, 0, term)
            proof = ForallElim(proof, term)
        if type(formula) is not Eq:
            raise TacticError(f"ring law {name!r} did not instantiate to an equation.")
        try:
            proof = normalise_cuts(proof)
        except ProofReductionError as exc:
            if "host recursion limit" in str(exc):
                raise TacticLimit("`ring` exceeded the host recursion limit.") from None
            raise TacticError(f"ring law {name!r} reduction failed: {exc}.") from None
        if not check((), proof, formula):
            raise TacticError(
                f"the independent kernel rejected instantiated ring law {name!r}."
            )
        result = EqualityCertificate(formula.left, formula.right, proof)
        self.cache[key] = result
        return result

    def axiom(self, name: str, *terms: Term) -> EqualityCertificate:
        formula = axiom_formula(name)
        proof: Proof = Axiom(name)
        for term in terms:
            self.budget.tick()
            if type(formula) is not Forall:
                raise TacticError(f"PA axiom {name} received too many terms.")
            formula = subst_formula(formula.body, 0, term)
            proof = ForallElim(proof, term)
        if type(formula) is not Eq:
            raise TacticError(f"PA axiom {name} did not instantiate to an equation.")
        result = EqualityCertificate(formula.left, formula.right, proof)
        if not check((), result.proof, Eq(result.left, result.right)):
            raise TacticError(f"internal PA axiom instance {name} failed checking.")
        return result

    def expect(
        self,
        actual: EqualityCertificate,
        left: Term,
        right: Term,
    ) -> EqualityCertificate:
        if actual.left != left or actual.right != right:
            raise TacticError("a checked ring law has an unexpected statement.")
        return actual

    def add_zero(self, term: Term) -> EqualityCertificate:
        return self.expect(self.axiom("PA3", term), Add(term, ZERO), term)

    def zero_add(self, term: Term) -> EqualityCertificate:
        return self.expect(self.instance("zero_add", term), Add(ZERO, term), term)

    def add_assoc(self, a: Term, b: Term, c: Term) -> EqualityCertificate:
        return self.expect(
            self.instance("add_assoc", a, b, c),
            Add(Add(a, b), c),
            Add(a, Add(b, c)),
        )

    def add_comm(self, a: Term, b: Term) -> EqualityCertificate:
        return self.expect(self.instance("add_comm", a, b), Add(a, b), Add(b, a))

    def mul_zero(self, term: Term) -> EqualityCertificate:
        return self.expect(self.axiom("PA5", term), Mul(term, ZERO), ZERO)

    def zero_mul(self, term: Term) -> EqualityCertificate:
        return self.expect(
            self.instance("mul_zero_left", term), Mul(ZERO, term), ZERO
        )

    def one_mul(self, term: Term) -> EqualityCertificate:
        return self.expect(self.instance("one_mul", term), Mul(ONE, term), term)

    def mul_one(self, term: Term) -> EqualityCertificate:
        return self.expect(self.instance("mul_one", term), Mul(term, ONE), term)

    def mul_assoc(self, a: Term, b: Term, c: Term) -> EqualityCertificate:
        return self.expect(
            self.instance("mul_assoc", a, b, c),
            Mul(Mul(a, b), c),
            Mul(a, Mul(b, c)),
        )

    def mul_comm(self, a: Term, b: Term) -> EqualityCertificate:
        return self.expect(self.instance("mul_comm", a, b), Mul(a, b), Mul(b, a))

    def mul_add(self, a: Term, b: Term, c: Term) -> EqualityCertificate:
        return self.expect(
            self.instance("mul_add", a, b, c),
            Mul(a, Add(b, c)),
            Add(Mul(a, b), Mul(a, c)),
        )

    def add_mul(self, a: Term, b: Term, c: Term) -> EqualityCertificate:
        return self.expect(
            self.instance("add_mul", a, b, c),
            Mul(Add(a, b), c),
            Add(Mul(a, c), Mul(b, c)),
        )

    def successor_as_add_one(self, term: Term) -> EqualityCertificate:
        pa4 = self.axiom("PA4", term, ZERO)
        pa3 = self.add_zero(term)
        result = _symm(
            _trans(
                pa4,
                EqualityCertificate(
                    Succ(pa3.left),
                    Succ(pa3.right),
                    CongS(pa3.proof),
                ),
                self.budget,
            ),
            self.budget,
        )
        return self.expect(result, Succ(term), Add(term, ONE))

    def closed_equation(self, left: Term, right: Term) -> EqualityCertificate:
        self.budget.tick()
        equation = Eq(left, right)
        try:
            proof = prove_closed_equation(equation)
        except DecisionError as exc:
            raise TacticError(f"ring coefficient proof failed: {exc}.") from None
        if proof is None:
            raise TacticError("internal ring coefficient calculation is false.")
        return EqualityCertificate(left, right, proof)


class _ACSystem:
    def __init__(self, kind: str, laws: _LawBook, budget: _Budget) -> None:
        if kind not in {"add", "mul"}:
            raise ValueError("AC system must be addition or multiplication")
        self.kind = kind
        self.laws = laws
        self.budget = budget
        self.identity: Term = ZERO if kind == "add" else ONE

    def join(self, items: tuple[Term, ...]) -> Term:
        return _join_add(items) if self.kind == "add" else _join_mul(items)

    def constructor(self, left: Term, right: Term) -> Term:
        return Add(left, right) if self.kind == "add" else Mul(left, right)

    def congr(
        self,
        left: EqualityCertificate,
        right: EqualityCertificate,
    ) -> EqualityCertificate:
        return (
            _cong_add(left, right, self.budget)
            if self.kind == "add"
            else _cong_mul(left, right, self.budget)
        )

    def assoc(self, a: Term, b: Term, c: Term) -> EqualityCertificate:
        return (
            self.laws.add_assoc(a, b, c)
            if self.kind == "add"
            else self.laws.mul_assoc(a, b, c)
        )

    def comm(self, a: Term, b: Term) -> EqualityCertificate:
        return (
            self.laws.add_comm(a, b)
            if self.kind == "add"
            else self.laws.mul_comm(a, b)
        )

    def left_identity(self, term: Term) -> EqualityCertificate:
        return (
            self.laws.zero_add(term)
            if self.kind == "add"
            else self.laws.one_mul(term)
        )

    def right_identity(self, term: Term) -> EqualityCertificate:
        return (
            self.laws.add_zero(term)
            if self.kind == "add"
            else self.laws.mul_one(term)
        )

    def flatten(self, term: Term) -> tuple[Term, ...]:
        if term == self.identity:
            return ()
        if (self.kind == "add" and type(term) is Add) or (
            self.kind == "mul" and type(term) is Mul
        ):
            return self.flatten(term.left) + self.flatten(term.right)
        return (term,)

    def concat(
        self,
        left: tuple[Term, ...],
        right: tuple[Term, ...],
    ) -> EqualityCertificate:
        self.budget.tick()
        if not left:
            return self.left_identity(self.join(right))
        if not right:
            return self.right_identity(self.join(left))
        head, tail = left[0], left[1:]
        first = self.assoc(head, self.join(tail), self.join(right))
        recursive = self.concat(tail, right)
        second = self.congr(_refl(head, self.budget), recursive)
        return _trans(first, second, self.budget)

    def adjacent_swap(
        self,
        items: tuple[Term, ...],
        index: int,
    ) -> EqualityCertificate:
        self.budget.tick()
        if index < 0 or index + 1 >= len(items):
            raise TacticError("internal ring permutation index is invalid.")
        if index > 0:
            tail = self.adjacent_swap(items[1:], index - 1)
            return self.congr(_refl(items[0], self.budget), tail)
        a, b = items[0], items[1]
        tail_term = self.join(items[2:])
        first = _symm(self.assoc(a, b, tail_term), self.budget)
        second = self.congr(self.comm(a, b), _refl(tail_term, self.budget))
        third = self.assoc(b, a, tail_term)
        return _trans(first, _trans(second, third, self.budget), self.budget)

    def permutation(
        self,
        items: tuple[Term, ...],
        key: Callable[[Term], tuple] = _term_key,
    ) -> tuple[tuple[Term, ...], EqualityCertificate]:
        current = list(items)
        result = _refl(self.join(items), self.budget)
        for stop in range(len(current), 1, -1):
            for index in range(stop - 1):
                self.budget.tick()
                if key(current[index]) <= key(current[index + 1]):
                    continue
                step = self.adjacent_swap(tuple(current), index)
                result = _trans(result, step, self.budget)
                current[index], current[index + 1] = (
                    current[index + 1],
                    current[index],
                )
        return tuple(current), result

    def normalize(self, term: Term) -> tuple[tuple[Term, ...], EqualityCertificate]:
        self.budget.tick()
        if term == self.identity:
            return (), _refl(term, self.budget)
        is_constructor = (self.kind == "add" and type(term) is Add) or (
            self.kind == "mul" and type(term) is Mul
        )
        if not is_constructor:
            proof = _symm(self.right_identity(term), self.budget)
            return (term,), proof
        left_items, left_proof = self.normalize(term.left)
        right_items, right_proof = self.normalize(term.right)
        congruence = self.congr(left_proof, right_proof)
        concatenated = self.concat(left_items, right_items)
        merged = _trans(congruence, concatenated, self.budget)
        ordered_items, permutation = self.permutation(left_items + right_items)
        return ordered_items, _trans(merged, permutation, self.budget)

    def prove_equal(self, left: Term, right: Term) -> EqualityCertificate:
        left_items, left_proof = self.normalize(left)
        right_items, right_proof = self.normalize(right)
        if left_items != right_items:
            raise TacticError("internal ring AC normalization changed the factor multiset.")
        return _trans(left_proof, _symm(right_proof, self.budget), self.budget)


class _Normalizer:
    def __init__(self, laws: _LawBook, budget: _Budget) -> None:
        self.laws = laws
        self.budget = budget
        self.add_ac = _ACSystem("add", laws, budget)
        self.mul_ac = _ACSystem("mul", laws, budget)
        self.numeral_cache: dict[int, TermNormalization] = {}

    def normalize(self, term: Term) -> TermNormalization:
        self.budget.tick()
        numeral = _as_numeral(term, self.budget)
        if numeral is not None:
            return self.normalize_numeral(numeral)
        if type(term) is Var:
            polynomial = _polynomial({((term.index, 1),): 1}, self.budget)
            summand = _quote_summand(polynomial[0], self.budget)
            monomial = _quote_monomial(polynomial[0][0], self.budget)
            expose_monomial = _symm(self.laws.mul_one(term), self.budget)
            expose_coefficient = _symm(
                self.laws.one_mul(monomial), self.budget
            )
            expose_sum = _symm(self.laws.add_zero(summand), self.budget)
            proof = _trans(
                expose_monomial,
                _trans(expose_coefficient, expose_sum, self.budget),
                self.budget,
            )
            return TermNormalization(term, polynomial, Add(summand, ZERO), proof.proof)
        if type(term) is Succ:
            child = self.normalize(term.term)
            one = self.normalize_numeral(1)
            unfold = self.laws.successor_as_add_one(term.term)
            arguments = _cong_add(child.equality, one.equality, self.budget)
            added_poly, addition = self.add_polynomials(
                child.polynomial,
                one.polynomial,
            )
            proof = _trans(unfold, _trans(arguments, addition, self.budget), self.budget)
            return TermNormalization(
                term,
                added_poly,
                _quote_polynomial(added_poly, self.budget),
                proof.proof,
            )
        if type(term) is Add:
            left = self.normalize(term.left)
            right = self.normalize(term.right)
            arguments = _cong_add(left.equality, right.equality, self.budget)
            polynomial, operation = self.add_polynomials(
                left.polynomial,
                right.polynomial,
            )
            proof = _trans(arguments, operation, self.budget)
            return TermNormalization(
                term,
                polynomial,
                _quote_polynomial(polynomial, self.budget),
                proof.proof,
            )
        if type(term) is Mul:
            left = self.normalize(term.left)
            right = self.normalize(term.right)
            arguments = _cong_mul(left.equality, right.equality, self.budget)
            polynomial, operation = self.multiply_polynomials(
                left.polynomial,
                right.polynomial,
            )
            proof = _trans(arguments, operation, self.budget)
            return TermNormalization(
                term,
                polynomial,
                _quote_polynomial(polynomial, self.budget),
                proof.proof,
            )
        raise TacticError("`ring` found an unsupported or unresolved term.")

    def normalize_numeral(self, value: int) -> TermNormalization:
        cached = self.numeral_cache.get(value)
        if cached is not None:
            self.budget.tick()
            return cached
        source = _numeral(value, self.budget)
        if value == 0:
            result = TermNormalization(source, (), ZERO, EqRefl(ZERO))
            self.numeral_cache[value] = result
            return result
        polynomial = _polynomial({(): value}, self.budget)
        summand = _quote_summand(polynomial[0], self.budget)
        first = _symm(self.laws.mul_one(source), self.budget)
        second = _symm(self.laws.add_zero(summand), self.budget)
        proof = _trans(first, second, self.budget)
        result = TermNormalization(
            source,
            polynomial,
            Add(summand, ZERO),
            proof.proof,
        )
        self.numeral_cache[value] = result
        return result

    def combine_pair(
        self,
        left: tuple[Monomial, int],
        right: tuple[Monomial, int],
    ) -> tuple[tuple[Monomial, int], EqualityCertificate]:
        if left[0] != right[0]:
            raise TacticError("internal ring collection mixed distinct monomials.")
        monomial = left[0]
        coefficient = left[1] + right[1]
        if coefficient > self.budget.limits.max_coefficient:
            self.budget.limit(f"coefficient-{self.budget.limits.max_coefficient}")
        left_term = _quote_summand(left, self.budget)
        right_term = _quote_summand(right, self.budget)
        monomial_term = _quote_monomial(monomial, self.budget)
        left_number = _numeral(left[1], self.budget)
        right_number = _numeral(right[1], self.budget)
        total_number = _numeral(coefficient, self.budget)
        distribute = _symm(
            self.laws.add_mul(left_number, right_number, monomial_term),
            self.budget,
        )
        calculate = self.laws.closed_equation(
            Add(left_number, right_number),
            total_number,
        )
        replace_coefficient = _cong_mul(
            calculate,
            _refl(monomial_term, self.budget),
            self.budget,
        )
        proof = _trans(distribute, replace_coefficient, self.budget)
        if proof.left != Add(left_term, right_term):
            raise TacticError("internal ring coefficient collection lost its source.")
        return (monomial, coefficient), proof

    def combine_group(
        self,
        group: tuple[tuple[Monomial, int], ...],
    ) -> tuple[tuple[Monomial, int], EqualityCertificate]:
        if not group:
            raise TacticError("internal ring collection received an empty group.")
        if len(group) == 1:
            term = _quote_summand(group[0], self.budget)
            return group[0], _refl(Add(term, ZERO), self.budget)
        tail_entry, tail_proof = self.combine_group(group[1:])
        first_term = _quote_summand(group[0], self.budget)
        tail_term = _quote_summand(tail_entry, self.budget)
        descend = _cong_add(
            _refl(first_term, self.budget),
            tail_proof,
            self.budget,
        )
        reassociate = _symm(
            self.laws.add_assoc(first_term, tail_term, ZERO),
            self.budget,
        )
        combined_entry, pair = self.combine_pair(group[0], tail_entry)
        install = _cong_add(pair, _refl(ZERO, self.budget), self.budget)
        proof = _trans(
            descend,
            _trans(reassociate, install, self.budget),
            self.budget,
        )
        return combined_entry, proof

    def combine_sorted(
        self,
        entries: tuple[tuple[Monomial, int], ...],
    ) -> tuple[Polynomial, EqualityCertificate]:
        if not entries:
            return (), _refl(ZERO, self.budget)
        split = 1
        while split < len(entries) and entries[split][0] == entries[0][0]:
            split += 1
        group, tail = entries[:split], entries[split:]
        combined_entry, group_proof = self.combine_group(group)
        tail_polynomial, tail_proof = self.combine_sorted(tail)
        group_terms = tuple(_quote_summand(entry, self.budget) for entry in group)
        tail_terms = tuple(_quote_summand(entry, self.budget) for entry in tail)
        separate = _symm(self.add_ac.concat(group_terms, tail_terms), self.budget)
        descend = _cong_add(group_proof, tail_proof, self.budget)
        result_polynomial = (combined_entry,) + tail_polynomial
        combine = self.add_ac.concat(
            (_quote_summand(combined_entry, self.budget),),
            _summands(tail_polynomial, self.budget),
        )
        proof = _trans(separate, _trans(descend, combine, self.budget), self.budget)
        return result_polynomial, proof

    def collect_entries(
        self,
        entries: tuple[tuple[Monomial, int], ...],
    ) -> tuple[Polynomial, EqualityCertificate]:
        ordered = tuple(sorted(entries, key=lambda entry: (_monomial_key(entry[0]), entry[1])))
        source = _join_add(tuple(_quote_summand(entry, self.budget) for entry in entries))
        ordered_term = _join_add(
            tuple(_quote_summand(entry, self.budget) for entry in ordered)
        )
        arrange = self.add_ac.prove_equal(source, ordered_term)
        polynomial, combine = self.combine_sorted(ordered)
        canonical = _polynomial(dict(polynomial), self.budget)
        if canonical != polynomial:
            raise TacticError("internal ring collection did not produce canonical order.")
        return polynomial, _trans(arrange, combine, self.budget)

    def add_polynomials(
        self,
        left: Polynomial,
        right: Polynomial,
    ) -> tuple[Polynomial, EqualityCertificate]:
        left_terms = _summands(left, self.budget)
        right_terms = _summands(right, self.budget)
        concatenate = self.add_ac.concat(left_terms, right_terms)
        polynomial, collect = self.collect_entries(left + right)
        expected = _add_polynomial_data(left, right, self.budget)
        if polynomial != expected:
            raise TacticError("internal ring addition disagreed with sparse arithmetic.")
        return polynomial, _trans(concatenate, collect, self.budget)

    def distribute_summand(
        self,
        left: tuple[Monomial, int],
        right: Polynomial,
    ) -> tuple[
        tuple[tuple[tuple[Monomial, int], tuple[Monomial, int]], ...],
        EqualityCertificate,
    ]:
        left_term = _quote_summand(left, self.budget)
        if not right:
            return (), self.laws.mul_zero(left_term)
        head, tail = right[0], right[1:]
        head_term = _quote_summand(head, self.budget)
        tail_term = _quote_polynomial(tail, self.budget)
        unfold = self.laws.mul_add(left_term, head_term, tail_term)
        tail_pairs, recurse = self.distribute_summand(left, tail)
        descend = _cong_add(
            _refl(Mul(left_term, head_term), self.budget),
            recurse,
            self.budget,
        )
        return ((left, head),) + tail_pairs, _trans(unfold, descend, self.budget)

    def distribute(
        self,
        left: Polynomial,
        right: Polynomial,
    ) -> tuple[
        tuple[tuple[tuple[Monomial, int], tuple[Monomial, int]], ...],
        EqualityCertificate,
    ]:
        if not left:
            return (), self.laws.zero_mul(_quote_polynomial(right, self.budget))
        if not right:
            return (), self.laws.mul_zero(_quote_polynomial(left, self.budget))
        head, tail = left[0], left[1:]
        head_term = _quote_summand(head, self.budget)
        tail_term = _quote_polynomial(tail, self.budget)
        right_term = _quote_polynomial(right, self.budget)
        unfold = self.laws.add_mul(head_term, tail_term, right_term)
        head_pairs, head_proof = self.distribute_summand(head, right)
        tail_pairs, tail_proof = self.distribute(tail, right)
        descend = _cong_add(head_proof, tail_proof, self.budget)
        concatenate = self.add_ac.concat(
            tuple(
                Mul(_quote_summand(a, self.budget), _quote_summand(b, self.budget))
                for a, b in head_pairs
            ),
            tuple(
                Mul(_quote_summand(a, self.budget), _quote_summand(b, self.budget))
                for a, b in tail_pairs
            ),
        )
        proof = _trans(
            unfold,
            _trans(descend, concatenate, self.budget),
            self.budget,
        )
        return head_pairs + tail_pairs, proof

    def multiply_summands(
        self,
        left: tuple[Monomial, int],
        right: tuple[Monomial, int],
    ) -> tuple[tuple[Monomial, int], EqualityCertificate]:
        monomial = _multiply_monomials(left[0], right[0], self.budget)
        coefficient = left[1] * right[1]
        if coefficient > self.budget.limits.max_coefficient:
            self.budget.limit(f"coefficient-{self.budget.limits.max_coefficient}")
        result_entry = (monomial, coefficient)
        source = Mul(
            _quote_summand(left, self.budget),
            _quote_summand(right, self.budget),
        )
        left_number = _numeral(left[1], self.budget)
        right_number = _numeral(right[1], self.budget)
        coefficient_expression = Mul(left_number, right_number)
        monomial_term = _quote_monomial(monomial, self.budget)
        middle = Mul(coefficient_expression, monomial_term)
        arrange = self.mul_ac.prove_equal(source, middle)
        calculate = self.laws.closed_equation(
            coefficient_expression,
            _numeral(coefficient, self.budget),
        )
        install = _cong_mul(
            calculate,
            _refl(monomial_term, self.budget),
            self.budget,
        )
        proof = _trans(arrange, install, self.budget)
        expected = _quote_summand(result_entry, self.budget)
        if proof.right != expected:
            raise TacticError("internal ring monomial multiplication lost its target.")
        return result_entry, proof

    def congruent_sum(
        self,
        proofs: tuple[EqualityCertificate, ...],
    ) -> EqualityCertificate:
        if not proofs:
            return _refl(ZERO, self.budget)
        tail = self.congruent_sum(proofs[1:])
        return _cong_add(proofs[0], tail, self.budget)

    def multiply_polynomials(
        self,
        left: Polynomial,
        right: Polynomial,
    ) -> tuple[Polynomial, EqualityCertificate]:
        pairs, distribute = self.distribute(left, right)
        products: list[tuple[Monomial, int]] = []
        product_proofs: list[EqualityCertificate] = []
        for first, second in pairs:
            entry, proof = self.multiply_summands(first, second)
            products.append(entry)
            product_proofs.append(proof)
        normalize_products = self.congruent_sum(tuple(product_proofs))
        polynomial, collect = self.collect_entries(tuple(products))
        proof = _trans(
            distribute,
            _trans(normalize_products, collect, self.budget),
            self.budget,
        )
        return polynomial, proof


def prove_ring_equation(
    equation: Eq,
    laws: tuple[RingLaw, ...],
    *,
    limits: RingLimits = DEFAULT_RING_LIMITS,
    clock: Callable[[], float] = monotonic,
) -> RingResult:
    """Construct and independently check a certificate for one ring identity."""

    if type(equation) is not Eq:
        raise TacticError("`ring` needs an equality goal.")
    budget = _Budget(limits, clock)
    _scan_equation(equation, budget)
    law_book = _LawBook(laws, budget)
    normalizer = _Normalizer(law_book, budget)
    try:
        left = normalizer.normalize(equation.left)
        right = normalizer.normalize(equation.right)
    except RecursionError:
        raise TacticLimit("`ring` exceeded the host recursion limit.") from None
    if left.polynomial != right.polynomial:
        raise TacticError(
            "`ring` found different polynomial normal forms; this is not an identity."
        )
    certificate: Proof = EqTrans(left.proof, EqSym(right.proof))
    try:
        certificate = normalise_cuts(certificate)
    except ProofReductionError as exc:
        if "host recursion limit" in str(exc):
            raise TacticLimit("`ring` exceeded the host recursion limit.") from None
        raise TacticError(f"ring certificate reduction failed: {exc}.") from None
    proof_nodes, proof_depth = _proof_metrics(certificate, limits)
    budget.tick()
    if not check((), certificate, equation):
        raise TacticError(
            "the independent kernel rejected the generated ring certificate."
        )
    budget.tick()
    return RingResult(
        equation,
        left.polynomial,
        left.normal_form,
        certificate,
        proof_nodes,
        proof_depth,
        budget.work_units,
    )


def ring_checked(
    state: ProofState,
    laws: tuple[RingLaw, ...],
    *,
    limits: RingLimits = DEFAULT_RING_LIMITS,
    clock: Callable[[], float] = monotonic,
) -> ProofState:
    """Close the focused equality with a generated, already checked proof."""

    if type(state) is not ProofState:
        raise TacticError("`ring` needs an exact proof state.")
    goal = state.current()
    if goal is None:
        raise TacticError("there is no open goal.")
    target = apply_formula_subst(goal.target, state.subst)
    if metas_in_formula(target, state.subst):
        raise TacticError("`ring` cannot guess unresolved term metavariables.")
    if type(target) is not Eq:
        raise TacticError("`ring` needs an equality goal.")
    result = prove_ring_equation(target, laws, limits=limits, clock=clock)
    after = replace_current_hole(state, result.certificate, ())
    if not invariants_ok(after):
        raise TacticError("internal ring result mismatched goals and certificate holes.")
    return record_step(state, replace(after, history=state.history), "ring", "")


__all__ = [
    "Monomial",
    "Polynomial",
    "RingLaw",
    "RingLimits",
    "DEFAULT_RING_LIMITS",
    "RING_LAW_NAMES",
    "EqualityCertificate",
    "TermNormalization",
    "RingResult",
    "prove_ring_equation",
    "ring_checked",
]
