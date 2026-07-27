"""Bounded, certificate-producing normalization of numerical term islands.

This module is deliberately independent of proof states, tactics, and the UI.
It normalizes only equality terms.  Maximal variable-free, non-numeral
subterms are sent to :func:`prove_closed_term`; open parents are rebuilt with
ordinary equality congruence.  Python arithmetic chooses a candidate numeral
but never grants proof authority: every closed-island certificate, both whole
term certificates, and the final equality bridge cross the kernel checker.

The later tactic wrapper may close a reflexive result with ``certificate`` or
install ``normal_form`` as one residual goal and use :meth:`transport_back`.
Normal QED must still check the completed proof against the original theorem.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from math import isfinite
from time import monotonic
from typing import Callable

from ..kernel.checker import check
from ..kernel.formulas import Eq
from ..kernel.proofs import (
    CongAdd,
    CongMul,
    CongS,
    EqRefl,
    EqSym,
    EqTrans,
    Hyp,
    Proof,
)
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero
from .decide import DecisionError, prove_closed_term


class NormNumError(ValueError):
    """A numerical normalization request is malformed or inapplicable."""


class NormNumLimit(NormNumError):
    """Numerical normalization reached an explicit resource bound."""


@dataclass(frozen=True, slots=True)
class NormNumLimits:
    """Explicit limits for one browser-facing numerical normalization."""

    max_ast_nodes: int = 256
    max_ast_depth: int = 64
    max_computations: int = 32
    max_value: int = 128
    max_work_units: int = 25_000
    max_proof_nodes: int = 50_000
    max_proof_depth: int = 256
    max_seconds: float = 5.0

    def __post_init__(self) -> None:
        integer_limits = (
            self.max_ast_nodes,
            self.max_ast_depth,
            self.max_computations,
            self.max_value,
            self.max_work_units,
            self.max_proof_nodes,
            self.max_proof_depth,
        )
        if any(type(value) is not int or value < 1 for value in integer_limits):
            raise ValueError("norm_num integer limits must be positive integers")
        try:
            finite_seconds = isfinite(self.max_seconds)
        except (OverflowError, TypeError, ValueError):
            finite_seconds = False
        if (
            type(self.max_seconds) not in (int, float)
            or not finite_seconds
            or self.max_seconds <= 0
        ):
            raise ValueError("norm_num time limit must be finite and positive")


DEFAULT_NORM_NUM_LIMITS = NormNumLimits()


@dataclass(frozen=True, slots=True)
class NumeralStep:
    """One maximal closed island and its exact checked numeral equation."""

    source: Term
    value: int
    normal_form: Term
    certificate: Proof


@dataclass(frozen=True, slots=True)
class TermNormalization:
    """A proof ``source = normal_form`` assembled from checked pieces."""

    source: Term
    normal_form: Term
    certificate: Proof
    steps: tuple[NumeralStep, ...]
    closed: bool


@dataclass(frozen=True, slots=True)
class NormNumResult:
    """Deterministic preview and proof data for one normalized equality."""

    equation: Eq
    normal_form: Eq
    left: TermNormalization
    right: TermNormalization
    steps: tuple[NumeralStep, ...]
    certificate: Proof | None
    proof_nodes: int
    proof_depth: int
    work_units: int

    @property
    def computations(self) -> int:
        return len(self.steps)

    @property
    def made_progress(self) -> bool:
        return bool(self.steps)

    @property
    def closes(self) -> bool:
        return self.certificate is not None

    @property
    def fully_closed(self) -> bool:
        return self.left.closed and self.right.closed

    @property
    def applicable(self) -> bool:
        """Whether a tactic can close the goal or expose a changed residual."""

        return self.closes or self.made_progress

    def transport_back(self, normal_proof: Proof) -> Proof:
        """Turn a proof of ``normal_form`` into one of ``equation``."""

        if not isinstance(normal_proof, Proof):
            raise NormNumError("norm_num transport needs an exact proof certificate")
        return _transport_back(self.left, self.right, normal_proof)


class _Budget:
    def __init__(
        self,
        limits: NormNumLimits,
        clock: Callable[[], float],
    ) -> None:
        if type(limits) is not NormNumLimits:
            raise NormNumError("norm_num needs exact NormNumLimits")
        if not callable(clock):
            raise NormNumError("norm_num needs a clock for its time limit")
        self.limits = limits
        self.clock = clock
        self.started = self._reading()
        self.work_units = 0

    def _reading(self) -> float:
        try:
            value = self.clock()
            finite = isfinite(value)
        except (OverflowError, TypeError, ValueError):
            raise NormNumError("norm_num clock returned a non-finite number") from None
        if type(value) not in (int, float) or not finite:
            raise NormNumError("norm_num clock returned a non-finite number")
        return value

    def check_time(self) -> None:
        if self._reading() - self.started > self.limits.max_seconds:
            raise NormNumLimit(
                f"norm_num exceeded its {self.limits.max_seconds:g}-second time limit"
            )

    def tick(self, amount: int = 1) -> None:
        self.work_units += amount
        if self.work_units > self.limits.max_work_units:
            raise NormNumLimit(
                f"norm_num exceeded its {self.limits.max_work_units}-work-unit limit"
            )
        self.check_time()

    def limit(self, label: str) -> None:
        raise NormNumLimit(f"norm_num exceeded its {label} limit")


def _proof_metrics(proof: Proof, budget: _Budget) -> tuple[int, int]:
    pending = [(proof, 1)]
    nodes = 0
    maximum_depth = 0
    try:
        while pending:
            current, depth = pending.pop()
            nodes += 1
            maximum_depth = max(maximum_depth, depth)
            if nodes > budget.limits.max_proof_nodes:
                budget.limit(f"{budget.limits.max_proof_nodes}-proof-node")
            if depth > budget.limits.max_proof_depth:
                budget.limit(f"{budget.limits.max_proof_depth}-proof-depth")
            if nodes % 128 == 0:
                budget.check_time()
            for item in fields(current):
                child = getattr(current, item.name)
                if isinstance(child, Proof):
                    pending.append((child, depth + 1))
    except NormNumError:
        raise
    except (AttributeError, TypeError, ValueError):
        raise NormNumError("norm_num generated a malformed proof") from None
    budget.check_time()
    return nodes, maximum_depth


def _scan_equation(equation: Eq, budget: _Budget) -> None:
    pending = [(equation.left, 1), (equation.right, 1)]
    nodes = 0
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
                raise NormNumError("norm_num found a malformed variable index")
        elif type(term) is Zero:
            pass
        elif type(term) is Succ:
            pending.append((term.term, depth + 1))
        elif type(term) in (Add, Mul):
            pending.append((term.right, depth + 1))
            pending.append((term.left, depth + 1))
        else:
            raise NormNumError(
                "norm_num needs rigid terms with no unresolved metavariables"
            )


def _is_closed(term: Term, budget: _Budget) -> bool:
    budget.tick()
    if type(term) is Var:
        return False
    if type(term) is Zero:
        return True
    if type(term) is Succ:
        return _is_closed(term.term, budget)
    if type(term) in (Add, Mul):
        left_closed = _is_closed(term.left, budget)
        right_closed = _is_closed(term.right, budget)
        return left_closed and right_closed
    raise NormNumError("norm_num encountered malformed term syntax")


def _is_numeral(term: Term, budget: _Budget) -> bool:
    current = term
    while type(current) is Succ:
        budget.tick()
        current = current.term
    budget.tick()
    return type(current) is Zero


def _value_limit(budget: _Budget) -> None:
    budget.limit(f"value-{budget.limits.max_value}")


def _bounded_value(term: Term, budget: _Budget) -> int:
    """Evaluate below ``max_value`` without ever constructing a larger int."""

    budget.tick()
    maximum = budget.limits.max_value
    if type(term) is Zero:
        return 0
    if type(term) is Succ:
        value = _bounded_value(term.term, budget)
        if value >= maximum:
            _value_limit(budget)
        return value + 1
    if type(term) is Add:
        left = _bounded_value(term.left, budget)
        right = _bounded_value(term.right, budget)
        if left > maximum - right:
            _value_limit(budget)
        return left + right
    if type(term) is Mul:
        left = _bounded_value(term.left, budget)
        right = _bounded_value(term.right, budget)
        if left != 0 and right > maximum // left:
            _value_limit(budget)
        return left * right
    raise NormNumError("norm_num tried to evaluate an open or malformed term")


def _refl(term: Term, budget: _Budget) -> Proof:
    budget.tick()
    return EqRefl(term)


class _Normalizer:
    def __init__(self, budget: _Budget) -> None:
        self.budget = budget
        self.computations = 0

    def normalize(self, term: Term) -> TermNormalization:
        closed = _is_closed(term, self.budget)
        if closed:
            value = _bounded_value(term, self.budget)
            if _is_numeral(term, self.budget):
                return TermNormalization(term, term, _refl(term, self.budget), (), True)
            self.computations += 1
            if self.computations > self.budget.limits.max_computations:
                self.budget.limit(
                    f"{self.budget.limits.max_computations}-computation"
                )
            self.budget.tick()
            try:
                result = prove_closed_term(
                    term,
                    max_value=self.budget.limits.max_value,
                )
            except DecisionError as exc:
                if "too deeply nested" in str(exc):
                    raise NormNumLimit(
                        "norm_num exceeded the host recursion limit"
                    ) from None
                raise NormNumError(f"norm_num closed calculation failed: {exc}") from None
            self.budget.check_time()
            if (
                result.source != term
                or result.value != value
                or result.normal_form == term
            ):
                raise NormNumError(
                    "norm_num closed calculation returned inconsistent metadata"
                )
            _proof_metrics(result.certificate, self.budget)
            self.budget.tick()
            if not check(
                (),
                result.certificate,
                Eq(result.source, result.normal_form),
            ):
                raise NormNumError(
                    "the independent kernel rejected a norm_num calculation"
                )
            self.budget.tick()
            step = NumeralStep(
                result.source,
                result.value,
                result.normal_form,
                result.certificate,
            )
            return TermNormalization(
                term,
                result.normal_form,
                result.certificate,
                (step,),
                True,
            )

        if type(term) is Var:
            return TermNormalization(term, term, _refl(term, self.budget), (), False)
        if type(term) is Succ:
            child = self.normalize(term.term)
            self.budget.tick()
            return TermNormalization(
                term,
                Succ(child.normal_form),
                CongS(child.certificate),
                child.steps,
                False,
            )
        if type(term) in (Add, Mul):
            left = self.normalize(term.left)
            right = self.normalize(term.right)
            self.budget.tick()
            constructor = Add if type(term) is Add else Mul
            congruence = CongAdd if type(term) is Add else CongMul
            return TermNormalization(
                term,
                constructor(left.normal_form, right.normal_form),
                congruence(left.certificate, right.certificate),
                left.steps + right.steps,
                False,
            )
        raise NormNumError("norm_num encountered malformed term syntax")


def _transport_back(
    left: TermNormalization,
    right: TermNormalization,
    normal_proof: Proof,
) -> Proof:
    return EqTrans(
        left.certificate,
        EqTrans(normal_proof, EqSym(right.certificate)),
    )


def normalize_equality(
    equation: Eq,
    *,
    limits: NormNumLimits = DEFAULT_NORM_NUM_LIMITS,
    clock: Callable[[], float] = monotonic,
) -> NormNumResult:
    """Normalize maximal closed numerical islands in one exact equality.

    A reflexive normal form carries a checked closing certificate.  Otherwise
    the result is a pure preview whose ``transport_back`` method can surround
    a later proof of its single residual equality.
    """

    if type(equation) is not Eq:
        raise NormNumError("norm_num needs an equality")
    try:
        budget = _Budget(limits, clock)
        _scan_equation(equation, budget)
        normalizer = _Normalizer(budget)
        left = normalizer.normalize(equation.left)
        right = normalizer.normalize(equation.right)
        normal_form = Eq(left.normal_form, right.normal_form)

        budget.tick()
        if not check((), left.certificate, Eq(left.source, left.normal_form)):
            raise NormNumError(
                "the independent kernel rejected the left norm_num transport"
            )
        budget.tick()
        if not check((), right.certificate, Eq(right.source, right.normal_form)):
            raise NormNumError(
                "the independent kernel rejected the right norm_num transport"
            )

        closes = left.normal_form == right.normal_form
        body: Proof = EqRefl(left.normal_form) if closes else Hyp(0)
        bridge = _transport_back(left, right, body)
        proof_nodes, proof_depth = _proof_metrics(bridge, budget)
        context = () if closes else (normal_form,)
        budget.tick()
        if not check(context, bridge, equation):
            raise NormNumError(
                "the independent kernel rejected the norm_num equality bridge"
            )
        budget.tick()
        return NormNumResult(
            equation=equation,
            normal_form=normal_form,
            left=left,
            right=right,
            steps=left.steps + right.steps,
            certificate=bridge if closes else None,
            proof_nodes=proof_nodes,
            proof_depth=proof_depth,
            work_units=budget.work_units,
        )
    except NormNumError:
        raise
    except RecursionError:
        raise NormNumLimit("norm_num exceeded the host recursion limit") from None
    except (AttributeError, TypeError, ValueError):
        raise NormNumError("norm_num received malformed equality syntax") from None


__all__ = [
    "NormNumError",
    "NormNumLimit",
    "NormNumLimits",
    "DEFAULT_NORM_NUM_LIMITS",
    "NumeralStep",
    "TermNormalization",
    "NormNumResult",
    "normalize_equality",
]
