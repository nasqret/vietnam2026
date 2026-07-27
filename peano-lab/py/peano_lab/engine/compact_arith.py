"""Small, cost-aware PA certificates for recurrent arithmetic identities.

``ring`` is deliberately general: it sends both sides of an equality through
one commutative-semiring normal form.  That is a good decision procedure, but
it can be a poor *certificate compressor*.  This module takes the complementary
approach.  It recognizes a few reusable shapes suggested directly by PA3--PA6
and constructs short, parameter-specialized induction proofs for them.

Nothing in this file is trusted.  Every selected assumption is checked in the
focused context, every result is checked for its exact equality before it can
enter a proof state, and normal QED checks the completed certificate against
the session owner's original theorem once more.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from math import isfinite
from time import monotonic
from typing import Callable

from ..kernel.checker import check
from ..kernel.formulas import Eq, Forall, Formula
from ..kernel.proofs import (
    Axiom,
    CongAdd,
    CongMul,
    CongS,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    Ind,
    Proof,
)
from ..kernel.subst import shift_term, subst_formula
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero
from .proof_reduction import ProofReductionError, normalise_cuts
from .state import (
    Goal,
    ProofState,
    StateError,
    Step,
    apply_formula_subst,
    apply_term_subst,
    invariants_ok,
    metas_in_formula,
    metas_in_proof,
    record_step,
    replace_current_hole,
)
from .tactics import TacticError, TacticLimit


ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)


@dataclass(frozen=True, slots=True)
class CompactArithLimits:
    """Deterministic structural limits for one compact proof search."""

    max_ast_nodes: int = 256
    max_ast_depth: int = 64
    max_assumptions: int = 16
    max_template_instances: int = 64
    max_search_states: int = 512
    max_candidates: int = 512
    max_annotation_nodes: int = 100_000
    max_annotation_depth: int = 256
    max_work_units: int = 20_000
    max_proof_nodes: int = 10_000
    max_proof_depth: int = 256
    max_partial_nodes: int = 100_000
    max_partial_depth: int = 512
    max_seconds: float = 5.0

    def __post_init__(self) -> None:
        integers = (
            self.max_ast_nodes,
            self.max_ast_depth,
            self.max_assumptions,
            self.max_template_instances,
            self.max_search_states,
            self.max_candidates,
            self.max_annotation_nodes,
            self.max_annotation_depth,
            self.max_work_units,
            self.max_proof_nodes,
            self.max_proof_depth,
            self.max_partial_nodes,
            self.max_partial_depth,
        )
        if any(type(value) is not int or value < 1 for value in integers):
            raise ValueError("compact_arith integer limits must be positive integers")
        finite = False
        if type(self.max_seconds) in (int, float):
            try:
                finite = isfinite(self.max_seconds)
            except OverflowError:
                finite = False
        if not finite or self.max_seconds <= 0:
            raise ValueError("compact_arith time limit must be positive")


DEFAULT_COMPACT_ARITH_LIMITS = CompactArithLimits()


@dataclass(frozen=True, slots=True)
class CompactArithAssumption:
    """One explicitly selected, oriented equality proof from the goal context."""

    name: str
    equation: Eq
    proof: Proof

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise TypeError("a compact_arith assumption needs a non-empty name")
        if type(self.equation) is not Eq or not isinstance(self.proof, Proof):
            raise TypeError("a compact_arith assumption needs an equality and proof")


@dataclass(frozen=True, slots=True)
class CompactArithResult:
    equation: Eq
    certificate: Proof
    proof_nodes: int
    proof_depth: int
    annotation_nodes: int
    work_units: int
    strategy: str
    used_assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _EqualityProof:
    """An ordinary proof paired with the exact endpoints it must establish."""

    left: Term
    right: Term
    proof: Proof

    def __post_init__(self) -> None:
        if not isinstance(self.left, Term) or not isinstance(self.right, Term):
            raise TypeError("compact_arith equality endpoints must be PA terms")
        if not isinstance(self.proof, Proof):
            raise TypeError("compact_arith equality evidence must be a proof")


@dataclass(frozen=True, slots=True)
class _Candidate:
    left: Term
    right: Term
    proof: Proof
    strategy: str
    nodes: int
    depth: int
    annotation_nodes: int
    ordinal: int
    used_assumptions: tuple[str, ...]


class _Budget:
    def __init__(
        self,
        limits: CompactArithLimits,
        clock: Callable[[], float],
    ) -> None:
        if type(limits) is not CompactArithLimits:
            raise TacticError("`compact_arith` needs exact CompactArithLimits.")
        if not callable(clock):
            raise TacticError("`compact_arith` needs a clock for its time limit.")
        self.limits = limits
        self.clock = clock
        self.started = self._read_clock()
        self.work_units = 0

    def _read_clock(self) -> float:
        return _read_clock(self.clock)

    def tick(self, amount: int = 1) -> None:
        if type(amount) is not int or amount < 0:
            raise TacticError("internal compact_arith work accounting failed.")
        self.work_units += amount
        if self.work_units > self.limits.max_work_units:
            raise TacticLimit(
                "`compact_arith` exceeded its "
                f"{self.limits.max_work_units}-work-unit limit."
            )
        if self._read_clock() - self.started > self.limits.max_seconds:
            raise TacticLimit(
                "`compact_arith` exceeded its "
                f"{self.limits.max_seconds:g}-second time limit."
            )

    def limit(self, message: str) -> None:
        raise TacticLimit(f"`compact_arith` exceeded its {message} limit.")


def _read_clock(clock: Callable[[], float]) -> float:
    """Read a caller-supplied clock without leaking its exceptions or values."""

    try:
        value = clock()
    except Exception:
        raise TacticError("`compact_arith` clock failed.") from None
    finite = False
    if type(value) in (int, float):
        try:
            finite = isfinite(value)
        except OverflowError:
            finite = False
    if not finite:
        raise TacticError("`compact_arith` clock must return a finite number.")
    return float(value)


class _Deadline:
    """One wall-clock interval shared by preflight, search, and publication."""

    def __init__(
        self,
        limits: CompactArithLimits,
        clock: Callable[[], float],
    ) -> None:
        if not callable(clock):
            raise TacticError("`compact_arith` needs a clock for its time limit.")
        self.limits = limits
        self.clock = clock
        self.started = _read_clock(clock)

    def check(self) -> None:
        if _read_clock(self.clock) - self.started > self.limits.max_seconds:
            raise TacticLimit(
                "`compact_arith` exceeded its "
                f"{self.limits.max_seconds:g}-second time limit."
            )

    def planner_clock(self) -> Callable[[], float]:
        first = True

        def shared() -> float:
            nonlocal first
            if first:
                first = False
                return self.started
            return _read_clock(self.clock)

        return shared


def _safe_fields(value: object, label: str):
    try:
        return fields(value)
    except (AttributeError, TypeError, ValueError):
        raise TacticError(f"`compact_arith` received a malformed {label}.") from None


def _safe_getattr(value: object, name: str, label: str):
    try:
        return getattr(value, name)
    except (AttributeError, TypeError, ValueError):
        raise TacticError(f"`compact_arith` received a malformed {label}.") from None


def _annotation_metrics(proof: Proof, budget: _Budget) -> tuple[int, int]:
    """Count term/formula annotations, which ``proof_size`` omits by design."""

    pending: list[tuple[object, int]] = [(proof, 0)]
    nodes = 0
    maximum_depth = 0
    while pending:
        current, depth = pending.pop()
        for item in _safe_fields(current, "proof certificate"):
            child = _safe_getattr(current, item.name, "proof certificate")
            if isinstance(child, Proof):
                pending.append((child, depth))
            elif isinstance(child, (Term, Formula)):
                annotation_pending: list[tuple[object, int]] = [(child, depth + 1)]
                while annotation_pending:
                    annotation, annotation_depth = annotation_pending.pop()
                    nodes += 1
                    maximum_depth = max(maximum_depth, annotation_depth)
                    if nodes > budget.limits.max_annotation_nodes:
                        budget.limit(
                            f"{budget.limits.max_annotation_nodes}-annotation-node"
                        )
                    if annotation_depth > budget.limits.max_annotation_depth:
                        budget.limit(
                            f"{budget.limits.max_annotation_depth}-annotation-depth"
                        )
                    for annotation_field in _safe_fields(
                        annotation, "term or formula annotation"
                    ):
                        descendant = _safe_getattr(
                            annotation,
                            annotation_field.name,
                            "term or formula annotation",
                        )
                        if isinstance(descendant, (Term, Formula)):
                            annotation_pending.append(
                                (descendant, annotation_depth + 1)
                            )
    return nodes, maximum_depth


def _proof_metrics(proof: Proof, budget: _Budget) -> tuple[int, int, int]:
    pending = [(proof, 1)]
    nodes = 0
    maximum_depth = 0
    while pending:
        current, depth = pending.pop()
        nodes += 1
        maximum_depth = max(maximum_depth, depth)
        if nodes > budget.limits.max_proof_nodes:
            budget.limit(f"{budget.limits.max_proof_nodes}-proof-node")
        if depth > budget.limits.max_proof_depth:
            budget.limit(f"{budget.limits.max_proof_depth}-proof-depth")
        for item in _safe_fields(current, "proof certificate"):
            child = _safe_getattr(current, item.name, "proof certificate")
            if isinstance(child, Proof):
                pending.append((child, depth + 1))
    annotation_nodes, _ = _annotation_metrics(proof, budget)
    return nodes, maximum_depth, annotation_nodes


def _enforce_partial_bounds(
    proof: Proof,
    limits: CompactArithLimits,
    deadline: _Deadline | None = None,
) -> None:
    pending = [(proof, 1)]
    nodes = 0
    while pending:
        current, depth = pending.pop()
        nodes += 1
        if nodes > limits.max_partial_nodes:
            raise TacticLimit(
                "`compact_arith` exceeded its "
                f"{limits.max_partial_nodes}-partial-proof-node limit."
            )
        if depth > limits.max_partial_depth:
            raise TacticLimit(
                "`compact_arith` exceeded its "
                f"{limits.max_partial_depth}-partial-proof-depth limit."
            )
        if deadline is not None and nodes % 128 == 0:
            deadline.check()
        for item in _safe_fields(current, "partial proof certificate"):
            child = _safe_getattr(current, item.name, "partial proof certificate")
            if isinstance(child, Proof):
                pending.append((child, depth + 1))
    if deadline is not None:
        deadline.check()


def _validate_state(state: ProofState) -> None:
    """Reject shallowly forged states before any proof-state operation can leak."""

    try:
        invalid = (
            not isinstance(state.partial, Proof)
            or not isinstance(state.target, Formula)
            or any(type(goal) is not Goal for goal in state.goals)
            or any(
                type(step) is not Step
                or type(step.tactic) is not str
                or type(step.args) is not str
                or type(step.state_before) is not ProofState
                for step in state.history
            )
            or any(type(name) is not str for name in state.variables)
            or any(
                type(meta_id) is not int
                or meta_id < 0
                or not isinstance(term, Term)
                for meta_id, term in state.subst.items()
            )
            or any(
                not isinstance(goal.target, Formula)
                or any(type(name) is not str for name in goal.variables)
                or any(
                    type(entry) is not tuple
                    or len(entry) != 2
                    or type(entry[0]) is not str
                    or not isinstance(entry[1], Formula)
                    for entry in goal.context
                )
                for goal in state.goals
            )
        )
    except (AttributeError, TypeError, ValueError):
        invalid = True
    if invalid:
        raise TacticError("`compact_arith` needs a valid exact proof state.")

    try:
        metas_in_proof(state.partial, state.subst)
        apply_formula_subst(state.target, state.subst)
        for term in state.subst.values():
            apply_term_subst(term, state.subst)
        for goal in state.goals:
            apply_formula_subst(goal.target, state.subst)
            for _, formula in goal.context:
                apply_formula_subst(formula, state.subst)
        valid = invariants_ok(state)
    except RecursionError:
        raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
    except (AttributeError, StateError, TypeError, ValueError):
        raise TacticError("`compact_arith` needs a valid exact proof state.") from None
    if not valid:
        raise TacticError("`compact_arith` needs a valid exact proof state.")


def _scan_terms(terms: tuple[Term, ...], budget: _Budget) -> None:
    """Enforce one aggregate input-node budget while retaining per-term depth."""

    pending = [(term, 1) for term in terms]
    nodes = 0
    while pending:
        current, depth = pending.pop()
        budget.tick()
        nodes += 1
        if nodes > budget.limits.max_ast_nodes:
            budget.limit(f"{budget.limits.max_ast_nodes}-AST-node")
        if depth > budget.limits.max_ast_depth:
            budget.limit(f"{budget.limits.max_ast_depth}-AST-depth")
        if type(current) in (Zero, Var):
            if type(current) is Var:
                index = _safe_getattr(current, "index", "input term")
                if type(index) is not int or index < 0:
                    raise TacticError(
                        "`compact_arith` found a malformed variable index."
                    )
            continue
        if type(current) is Succ:
            pending.append(
                (_safe_getattr(current, "term", "input term"), depth + 1)
            )
            continue
        if type(current) in (Add, Mul):
            pending.append(
                (_safe_getattr(current, "right", "input term"), depth + 1)
            )
            pending.append(
                (_safe_getattr(current, "left", "input term"), depth + 1)
            )
            continue
        raise TacticError(
            "`compact_arith` needs rigid terms with no unresolved metavariables."
        )


def _refl(term: Term) -> _EqualityProof:
    return _EqualityProof(term, term, EqRefl(term))


def _symm(value: _EqualityProof) -> _EqualityProof:
    return _EqualityProof(value.right, value.left, EqSym(value.proof))


def _trans(first: _EqualityProof, second: _EqualityProof) -> _EqualityProof:
    if first.right != second.left:
        raise TacticError(
            "internal compact_arith transitivity endpoints do not compose."
        )
    return _EqualityProof(first.left, second.right, EqTrans(first.proof, second.proof))


def _cong_s(value: _EqualityProof) -> _EqualityProof:
    return _EqualityProof(Succ(value.left), Succ(value.right), CongS(value.proof))


def _cong_add(left: _EqualityProof, right: _EqualityProof) -> _EqualityProof:
    return _EqualityProof(
        Add(left.left, right.left),
        Add(left.right, right.right),
        CongAdd(left.proof, right.proof),
    )


def _cong_mul(left: _EqualityProof, right: _EqualityProof) -> _EqualityProof:
    return _EqualityProof(
        Mul(left.left, right.left),
        Mul(left.right, right.right),
        CongMul(left.proof, right.proof),
    )


def _subst_eq(
    motive: Formula,
    equation: _EqualityProof,
    body: _EqualityProof,
) -> _EqualityProof:
    source = subst_formula(motive, 0, equation.left)
    target = subst_formula(motive, 0, equation.right)
    if source != Eq(body.left, body.right):
        raise TacticError(
            "internal compact_arith substitution source does not match its body."
        )
    if type(target) is not Eq:
        raise TacticError(
            "internal compact_arith equality substitution produced a non-equation."
        )
    return _EqualityProof(
        target.left,
        target.right,
        EqSubst(motive, equation.proof, body.proof),
    )


def _expect_endpoints(
    value: _EqualityProof,
    left: Term,
    right: Term,
    operation: str,
) -> _EqualityProof:
    if value.left != left or value.right != right:
        raise TacticError(
            f"internal compact_arith {operation} endpoints do not match."
        )
    return value


def _pa3(a: Term) -> _EqualityProof:
    return _EqualityProof(Add(a, ZERO), a, ForallElim(Axiom("PA3"), a))


def _pa4(a: Term, b: Term) -> _EqualityProof:
    return _EqualityProof(
        Add(a, Succ(b)),
        Succ(Add(a, b)),
        ForallElim(ForallElim(Axiom("PA4"), a), b),
    )


def _pa5(a: Term) -> _EqualityProof:
    return _EqualityProof(Mul(a, ZERO), ZERO, ForallElim(Axiom("PA5"), a))


def _pa6(a: Term, b: Term) -> _EqualityProof:
    return _EqualityProof(
        Mul(a, Succ(b)),
        Add(Mul(a, b), a),
        ForallElim(ForallElim(Axiom("PA6"), a), b),
    )


def _chain(*proofs: _EqualityProof) -> _EqualityProof:
    if not proofs:
        raise TacticError("internal compact_arith equality chain is empty.")
    result = proofs[0]
    for proof in proofs[1:]:
        result = _trans(result, proof)
    return result


def _instantiate(proof: Proof, *terms: Term) -> Proof:
    result = proof
    for term in terms:
        result = ForallElim(result, term)
    try:
        return normalise_cuts(result)
    except ProofReductionError as exc:
        if "host recursion limit" in str(exc):
            raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
        raise TacticError(f"compact_arith recurrence reduction failed: {exc}.") from None


def _qone(a: Term) -> _EqualityProof:
    """Prove ``a + 1 = S a`` directly from PA3 and PA4."""

    motive = Eq(Add(shift_term(a, 1), ONE), Succ(Var(0)))
    return _subst_eq(motive, _pa3(a), _pa4(a, ZERO))


def _qtwo(a: Term) -> _EqualityProof:
    """Prove ``a + 2 = S (S a)`` without generic numeral normalization."""

    motive = Eq(Add(shift_term(a, 1), TWO), Succ(Var(0)))
    return _subst_eq(motive, _qone(a), _pa4(a, ONE))


def _mul_add_one(a: Term, b: Term) -> _EqualityProof:
    """Prove ``a * (b + 1) = a * b + a`` in eleven nodes."""

    right = Add(Mul(a, b), a)
    motive = Eq(Mul(shift_term(a, 1), Var(0)), shift_term(right, 1))
    return _subst_eq(motive, _symm(_qone(b)), _pa6(a, b))


def _add_succ_theorem() -> Proof:
    """Build ``forall a b. S a + b = S (a + b)`` (20 nodes)."""

    b = Var(0)
    a = Var(1)
    motive = Eq(Add(Succ(a), b), Succ(Add(a, b)))

    outer_a = Var(0)
    base = _subst_eq(
        Eq(Add(Succ(shift_term(outer_a, 1)), ZERO), Succ(Var(0))),
        _symm(_pa3(outer_a)),
        _pa3(Succ(outer_a)),
    )

    b = Var(0)
    a = Var(1)
    left = Add(Succ(a), Succ(b))
    left_motive = Eq(shift_term(left, 1), Succ(Var(0)))
    ih = _EqualityProof(
        Add(Succ(a), b),
        Succ(Add(a, b)),
        Hyp(0),
    )
    left_to_normal = _subst_eq(left_motive, ih, _pa4(Succ(a), b))
    step = _subst_eq(left_motive, _symm(_pa4(a, b)), left_to_normal)
    return ForallIntro(
        Ind(motive, base.proof, ForallIntro(ImpIntro(step.proof)))
    )


_ADD_SUCC = _add_succ_theorem()
_ADD_SUCC_FORMULA = Forall(
    Forall(Eq(Add(Succ(Var(1)), Var(0)), Succ(Add(Var(1), Var(0)))))
)
if not check((), _ADD_SUCC, _ADD_SUCC_FORMULA):
    raise RuntimeError("the compact_arith add-successor template failed checking")


def _add_succ_at(a: Term, b: Term) -> _EqualityProof:
    return _EqualityProof(
        Add(Succ(a), b),
        Succ(Add(a, b)),
        _instantiate(_ADD_SUCC, a, b),
    )


def _offset_swap(a0: Term, a: Term, n: Term) -> _EqualityProof:
    """Prove ``(a0+n)+S a = (a0+a)+S n`` by a specialized induction."""

    a0_motive = shift_term(a0, 1)
    a_motive = shift_term(a, 1)
    j = Var(0)
    motive = Eq(
        Add(Add(a0_motive, j), Succ(a_motive)),
        Add(Add(a0_motive, a_motive), Succ(j)),
    )
    base_core = _chain(_pa4(a0, a), _symm(_qone(Add(a0, a))))
    base = _subst_eq(
        Eq(
            Add(Var(0), shift_term(Succ(a), 1)),
            shift_term(Add(Add(a0, a), ONE), 1),
        ),
        _symm(_pa3(a0)),
        base_core,
    )

    a0_step = shift_term(a0, 1)
    a_step = shift_term(a, 1)
    successor_j = Succ(j)
    original_left = Add(Add(a0_step, successor_j), Succ(a_step))
    successor_bridge = _add_succ_at(Add(a0_step, j), Succ(a_step))
    first_motive = Eq(
        Add(Var(0), shift_term(Succ(a_step), 1)),
        Succ(shift_term(Add(Add(a0_step, j), Succ(a_step)), 1)),
    )
    first = _subst_eq(first_motive, _symm(_pa4(a0_step, j)), successor_bridge)
    ih = _EqualityProof(
        Add(Add(a0_step, j), Succ(a_step)),
        Add(Add(a0_step, a_step), Succ(j)),
        Hyp(0),
    )
    second = _subst_eq(
        Eq(shift_term(original_left, 1), Succ(Var(0))),
        ih,
        first,
    )
    third = _subst_eq(
        Eq(shift_term(original_left, 1), Var(0)),
        _symm(_pa4(Add(a0_step, a_step), successor_j)),
        second,
    )
    theorem = Ind(motive, base.proof, ForallIntro(ImpIntro(third.proof)))
    if not check((), theorem, Forall(motive)):
        raise TacticError("compact_arith offset-swap template failed checking.")
    return _EqualityProof(
        Add(Add(a0, n), Succ(a)),
        Add(Add(a0, a), Succ(n)),
        ForallElim(theorem, n),
    )


def _mul_succ_left(a: Term, n: Term) -> _EqualityProof:
    """Prove ``S a * n = a * n + n`` by a specialized induction."""

    a_motive = shift_term(a, 1)
    j = Var(0)
    motive = Eq(Mul(Succ(a_motive), j), Add(Mul(a_motive, j), j))
    base = _chain(
        _pa5(Succ(a)),
        _symm(_chain(_pa3(Mul(a, ZERO)), _pa5(a))),
    )

    a_step = shift_term(a, 1)
    product = Mul(a_step, j)
    successor_a = Succ(a_step)
    successor_j = Succ(j)
    original_left = Mul(successor_a, successor_j)
    ih = _EqualityProof(
        Mul(successor_a, j),
        Add(product, j),
        Hyp(0),
    )
    first = _subst_eq(
        Eq(
            shift_term(original_left, 1),
            Add(Var(0), shift_term(successor_a, 1)),
        ),
        ih,
        _pa6(successor_a, j),
    )
    second = _subst_eq(
        Eq(shift_term(original_left, 1), Var(0)),
        _offset_swap(product, a_step, j),
        first,
    )
    third = _subst_eq(
        Eq(
            shift_term(original_left, 1),
            Add(Var(0), shift_term(successor_j, 1)),
        ),
        _symm(_pa6(a_step, j)),
        second,
    )
    theorem = Ind(motive, base.proof, ForallIntro(ImpIntro(third.proof)))
    if not check((), theorem, Forall(motive)):
        raise TacticError("compact_arith multiplication template failed checking.")
    return _EqualityProof(
        Mul(Succ(a), n),
        Add(Mul(a, n), n),
        ForallElim(theorem, n),
    )


def _double_add(w: Term, value: Term) -> _EqualityProof:
    """Prove ``(2*w+value)+value = 2*(w+value)`` by induction on value."""

    w_motive = shift_term(w, 1)
    j = Var(0)
    twice_w = Mul(TWO, w_motive)
    motive = Eq(
        Add(Add(twice_w, j), j),
        Mul(TWO, Add(w_motive, j)),
    )

    twice_w_base = Mul(TWO, w)
    original_base_left = Add(Add(twice_w_base, ZERO), ZERO)
    left_to_twice_w = _chain(_pa3(Add(twice_w_base, ZERO)), _pa3(twice_w_base))
    base = _subst_eq(
        Eq(shift_term(original_base_left, 1), Mul(TWO, Var(0))),
        _symm(_pa3(w)),
        left_to_twice_w,
    )

    w_step = shift_term(w, 1)
    twice_w = Mul(TWO, w_step)
    successor_j = Succ(j)
    new_left = Add(Add(twice_w, successor_j), successor_j)
    old_witness = Add(w_step, j)
    successor_bridge = _add_succ_at(Add(twice_w, j), successor_j)
    first_motive = Eq(
        Add(Var(0), shift_term(successor_j, 1)),
        Succ(shift_term(Add(Add(twice_w, j), successor_j), 1)),
    )
    first = _subst_eq(first_motive, _symm(_pa4(twice_w, j)), successor_bridge)
    second = _subst_eq(
        Eq(shift_term(new_left, 1), Succ(Var(0))),
        _pa4(Add(twice_w, j), j),
        first,
    )
    ih = _EqualityProof(
        Add(Add(twice_w, j), j),
        Mul(TWO, Add(w_step, j)),
        Hyp(0),
    )
    third = _subst_eq(
        Eq(shift_term(new_left, 1), Succ(Succ(Var(0)))),
        ih,
        second,
    )
    right_normal = _chain(_pa6(TWO, old_witness), _qtwo(Mul(TWO, old_witness)))
    fourth = _trans(third, _symm(right_normal))
    fifth = _subst_eq(
        Eq(shift_term(new_left, 1), Mul(TWO, Var(0))),
        _symm(_pa4(w_step, j)),
        fourth,
    )
    theorem = Ind(motive, base.proof, ForallIntro(ImpIntro(fifth.proof)))
    if not check((), theorem, Forall(motive)):
        raise TacticError("compact_arith doubling template failed checking.")
    return _EqualityProof(
        Add(Add(Mul(TWO, w), value), value),
        Mul(TWO, Add(w, value)),
        ForallElim(theorem, value),
    )


def _replace_all(term: Term, old: Term, new: Term) -> Term:
    if term == old:
        return new
    if type(term) in (Zero, Var):
        return term
    if type(term) is Succ:
        return Succ(_replace_all(term.term, old, new))
    if type(term) is Add:
        return Add(
            _replace_all(term.left, old, new),
            _replace_all(term.right, old, new),
        )
    if type(term) is Mul:
        return Mul(
            _replace_all(term.left, old, new),
            _replace_all(term.right, old, new),
        )
    raise TacticError("internal compact_arith replacement received malformed syntax.")


def _abstract_all(term: Term, old: Term) -> Term:
    """Shift outer variables and replace every exact ``old`` by motive slot zero."""

    if term == old:
        return Var(0)
    if type(term) is Zero:
        return term
    if type(term) is Var:
        return Var(term.index + 1)
    if type(term) is Succ:
        return Succ(_abstract_all(term.term, old))
    if type(term) is Add:
        return Add(_abstract_all(term.left, old), _abstract_all(term.right, old))
    if type(term) is Mul:
        return Mul(_abstract_all(term.left, old), _abstract_all(term.right, old))
    raise TacticError("internal compact_arith abstraction received malformed syntax.")


def _zero_normalize(term: Term, budget: _Budget) -> _EqualityProof:
    """Normalize only cheap right-zero redexes, retaining an exact proof."""

    budget.tick()
    if type(term) is Add and term.right == ZERO:
        head = _pa3(term.left)
        reduced = _zero_normalize(term.left, budget)
        if reduced.right == term.left:
            return head
        return _trans(head, reduced)
    if type(term) is Mul and term.right == ZERO:
        return _pa5(term.left)
    return _refl(term)


class _Planner:
    def __init__(
        self,
        context: tuple[Formula, ...],
        assumptions: tuple[CompactArithAssumption, ...],
        budget: _Budget,
    ) -> None:
        self.context = context
        self.assumptions = assumptions
        self.budget = budget
        self.memo: dict[tuple[Term, Term, bool], _Candidate | None] = {}
        self.active: set[tuple[Term, Term, bool]] = set()
        self.next_ordinal = 0
        self.template_instances = 0

    def _template(self) -> None:
        self.template_instances += 1
        if self.template_instances > self.budget.limits.max_template_instances:
            self.budget.limit(
                f"{self.budget.limits.max_template_instances}-template-instance"
            )
        self.budget.tick()

    def _candidate(
        self,
        equality: _EqualityProof,
        strategy: str,
        used_assumptions: tuple[str, ...] = (),
    ) -> _Candidate:
        if self.next_ordinal >= self.budget.limits.max_candidates:
            self.budget.limit(f"{self.budget.limits.max_candidates}-candidate")
        self.budget.tick()
        try:
            normalized = normalise_cuts(equality.proof)
        except ProofReductionError as exc:
            if "host recursion limit" in str(exc):
                raise TacticLimit(
                    "`compact_arith` exceeded the host recursion limit."
                ) from None
            raise TacticError(
                f"compact_arith candidate reduction failed: {exc}."
            ) from None
        nodes, depth, annotation_nodes = _proof_metrics(normalized, self.budget)
        ordinal = self.next_ordinal
        self.next_ordinal += 1
        return _Candidate(
            equality.left,
            equality.right,
            normalized,
            strategy,
            nodes,
            depth,
            annotation_nodes,
            ordinal,
            used_assumptions,
        )

    @staticmethod
    def _equality(candidate: _Candidate) -> _EqualityProof:
        return _EqualityProof(candidate.left, candidate.right, candidate.proof)

    def _best(self, candidates: list[_Candidate]) -> _Candidate | None:
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda item: (
                item.nodes,
                item.depth,
                item.annotation_nodes,
                item.ordinal,
            ),
        )

    def solve(
        self,
        left: Term,
        right: Term,
        *,
        allow_assumptions: bool = True,
    ) -> _Candidate | None:
        key = (left, right, allow_assumptions)
        if key in self.memo:
            return self.memo[key]
        if key in self.active:
            return None
        if len(self.memo) + len(self.active) >= self.budget.limits.max_search_states:
            self.budget.limit(f"{self.budget.limits.max_search_states}-search-state")
        self.active.add(key)
        self.budget.tick()
        candidates: list[_Candidate] = []
        try:
            if left == right:
                candidates.append(self._candidate(_refl(left), "reflexivity"))

            direct = self._direct_seed(left, right)
            if direct is not None:
                candidates.append(direct)
            reverse = self._direct_seed(right, left)
            if reverse is not None:
                candidates.append(
                    self._candidate(
                        _expect_endpoints(
                            _symm(self._equality(reverse)),
                            left,
                            right,
                            "symmetry",
                        ),
                        f"symmetry({reverse.strategy})",
                    )
                )

            structural = self._structural(left, right, allow_assumptions)
            if structural is not None:
                candidates.append(structural)

            left_zero = _zero_normalize(left, self.budget)
            right_zero = _zero_normalize(right, self.budget)
            if (
                left_zero.right == right_zero.right
                and (left_zero.right != left or right_zero.right != right)
            ):
                proof = _trans(left_zero, _symm(right_zero))
                candidates.append(
                    self._candidate(proof, "right-zero normalization")
                )

            recursive_mul = self._right_recursive_mul(left, right)
            if recursive_mul is not None:
                candidates.append(recursive_mul)
            reverse_mul = self._right_recursive_mul(right, left)
            if reverse_mul is not None:
                candidates.append(
                    self._candidate(
                        _expect_endpoints(
                            _symm(self._equality(reverse_mul)),
                            left,
                            right,
                            "symmetry",
                        ),
                        f"symmetry({reverse_mul.strategy})",
                    )
                )

            if allow_assumptions:
                for assumption in self.assumptions:
                    if assumption.equation == Eq(left, right):
                        candidates.append(
                            self._candidate(
                                _EqualityProof(left, right, assumption.proof),
                                f"selected assumption {assumption.name}",
                                (assumption.name,),
                            )
                        )
                    transported = self._transport_to_recurrence(
                        left, right, assumption
                    )
                    if transported is not None:
                        candidates.append(transported)

            result = self._best(candidates)
            if result is not None and (result.left != left or result.right != right):
                raise TacticError(
                    "internal compact_arith candidate endpoints do not match the search goal."
                )
            self.memo[key] = result
            return result
        finally:
            self.active.remove(key)

    def _direct_seed(self, left: Term, right: Term) -> _Candidate | None:
        # PA's primitive right-recursion equations are always cheapest when
        # their endpoints already match the focused target.
        if type(left) is Add and left.right == ZERO and right == left.left:
            return self._candidate(_pa3(left.left), "PA3")
        if type(left) is Add and type(left.right) is Succ:
            expected = Succ(Add(left.left, left.right.term))
            if right == expected:
                return self._candidate(
                    _pa4(left.left, left.right.term),
                    "PA4",
                )
        if type(left) is Mul and left.right == ZERO and right == ZERO:
            return self._candidate(_pa5(left.left), "PA5")
        if type(left) is Mul and type(left.right) is Succ:
            expected = Add(Mul(left.left, left.right.term), left.left)
            if right == expected:
                return self._candidate(
                    _pa6(left.left, left.right.term),
                    "PA6",
                )
        if type(right) is Succ and left == Add(right.term, ONE):
            self._template()
            return self._candidate(_qone(right.term), "one-successor bridge")
        if (
            type(right) is Succ
            and type(right.term) is Succ
            and left == Add(right.term.term, TWO)
        ):
            self._template()
            return self._candidate(_qtwo(right.term.term), "two-successor bridge")
        if (
            type(left) is Mul
            and type(left.right) is Add
            and left.right.right == ONE
            and right == Add(Mul(left.left, left.right.left), left.left)
        ):
            self._template()
            return self._candidate(
                _mul_add_one(left.left, left.right.left),
                "multiplication-by-add-one bridge",
            )

        if (
            type(left) is Add
            and type(left.left) is Succ
            and type(right) is Succ
            and right.term == Add(left.left.term, left.right)
        ):
            self._template()
            return self._candidate(
                _add_succ_at(left.left.term, left.right),
                "successor-left addition recurrence",
            )
        if (
            type(left) is Mul
            and type(left.left) is Succ
            and right == Add(Mul(left.left.term, left.right), left.right)
        ):
            self._template()
            return self._candidate(
                _mul_succ_left(left.left.term, left.right),
                "successor-left multiplication recurrence",
            )
        if (
            type(left) is Add
            and type(left.left) is Add
            and type(left.right) is Succ
            and type(right) is Add
            and type(right.left) is Add
            and type(right.right) is Succ
            and left.left.left == right.left.left
            and left.left.right == right.right.term
            and left.right.term == right.left.right
        ):
            self._template()
            return self._candidate(
                _offset_swap(
                    left.left.left,
                    left.right.term,
                    left.left.right,
                ),
                "additive offset-swap recurrence",
            )
        if (
            type(left) is Add
            and type(left.left) is Add
            and type(left.left.left) is Mul
            and left.left.left.left == TWO
            and left.left.right == left.right
            and type(right) is Mul
            and right.left == TWO
            and type(right.right) is Add
            and right.right.left == left.left.left.right
            and right.right.right == left.right
        ):
            self._template()
            return self._candidate(
                _double_add(left.left.left.right, left.right),
                "doubling recurrence",
            )
        return None

    def _structural(
        self,
        left: Term,
        right: Term,
        allow_assumptions: bool,
    ) -> _Candidate | None:
        if type(left) is Succ and type(right) is Succ:
            child = self.solve(
                left.term,
                right.term,
                allow_assumptions=allow_assumptions,
            )
            if child is not None:
                return self._candidate(
                    _expect_endpoints(
                        _cong_s(self._equality(child)),
                        left,
                        right,
                        "congruence",
                    ),
                    f"successor congruence({child.strategy})",
                )
        if type(left) in (Add, Mul) and type(right) is type(left):
            left_child = self.solve(
                left.left,
                right.left,
                allow_assumptions=allow_assumptions,
            )
            right_child = self.solve(
                left.right,
                right.right,
                allow_assumptions=allow_assumptions,
            )
            if left_child is not None and right_child is not None:
                used = tuple(
                    dict.fromkeys(
                        left_child.used_assumptions
                        + right_child.used_assumptions
                    )
                )
                left_equality = self._equality(left_child)
                right_equality = self._equality(right_child)
                equality = (
                    _cong_add(left_equality, right_equality)
                    if type(left) is Add
                    else _cong_mul(left_equality, right_equality)
                )
                return self._candidate(
                    _expect_endpoints(equality, left, right, "congruence"),
                    f"structural {type(left).__name__.lower()}",
                    used,
                )
        return None

    def _right_recursive_mul(self, left: Term, right: Term) -> _Candidate | None:
        if (
            type(left) is not Mul
            or type(left.right) is not Succ
            or type(right) is not Add
            or right.right != left.left
        ):
            return None
        old_inner = Mul(left.left, left.right.term)
        inner = self.solve(old_inner, right.left, allow_assumptions=False)
        if inner is None:
            return None
        motive = Eq(
            shift_term(left, 1),
            Add(Var(0), shift_term(left.left, 1)),
        )
        proof = _subst_eq(
            motive,
            self._equality(inner),
            _pa6(left.left, left.right.term),
        )
        return self._candidate(
            _expect_endpoints(proof, left, right, "substitution"),
            f"PA6 transport({inner.strategy})",
        )

    def _double_predecessor(self, right: Term) -> _EqualityProof | None:
        if (
            type(right) is Mul
            and right.left == TWO
            and type(right.right) is Add
        ):
            self._template()
            w, value = right.right.left, right.right.right
            return _double_add(w, value)
        return None

    def _transport_to_recurrence(
        self,
        left: Term,
        right: Term,
        assumption: CompactArithAssumption,
    ) -> _Candidate | None:
        finish = self._double_predecessor(right)
        if finish is None:
            return None
        post = finish.left
        old, new = assumption.equation.left, assumption.equation.right
        pre = _replace_all(post, new, old)
        if pre == post:
            return None
        prefix = self.solve(left, pre, allow_assumptions=False)
        if prefix is None:
            return None
        motive = Eq(shift_term(left, 1), _abstract_all(pre, old))
        transported = _subst_eq(
            motive,
            _EqualityProof(old, new, assumption.proof),
            self._equality(prefix),
        )
        proof = _trans(transported, finish)
        return self._candidate(
            _expect_endpoints(proof, left, right, "transitivity"),
            f"{assumption.name} transport then doubling recurrence",
            (assumption.name,),
        )


def prove_compact_equation(
    equation: Eq,
    *,
    context: tuple[Formula, ...] = (),
    assumptions: tuple[CompactArithAssumption, ...] = (),
    limits: CompactArithLimits = DEFAULT_COMPACT_ARITH_LIMITS,
    clock: Callable[[], float] = monotonic,
) -> CompactArithResult:
    """Construct and independently check one small PA equality certificate."""

    if type(equation) is not Eq:
        raise TacticError("`compact_arith` needs an equality goal.")
    if not isinstance(context, tuple) or not all(
        isinstance(formula, Formula) for formula in context
    ):
        raise TacticError("`compact_arith` needs an exact formula context.")
    if not isinstance(assumptions, tuple) or not all(
        type(item) is CompactArithAssumption for item in assumptions
    ):
        raise TacticError("`compact_arith` needs exact selected assumptions.")

    budget = _Budget(limits, clock)
    if len(assumptions) > limits.max_assumptions:
        budget.limit(f"{limits.max_assumptions}-selected-assumption")
    input_terms: list[Term] = [equation.left, equation.right]
    for assumption in assumptions:
        input_terms.extend((assumption.equation.left, assumption.equation.right))
    _scan_terms(tuple(input_terms), budget)
    for assumption in assumptions:
        _proof_metrics(assumption.proof, budget)
        budget.tick()
        if not check(context, assumption.proof, assumption.equation):
            raise TacticError(
                "the independent kernel rejected compact_arith assumption "
                f"{assumption.name!r}."
            )

    planner = _Planner(context, assumptions, budget)
    try:
        selected = planner.solve(equation.left, equation.right)
    except RecursionError:
        raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
    if selected is None:
        raise TacticError(
            "`compact_arith` found no proof in its bounded PA recurrence grammar."
        )
    try:
        certificate = normalise_cuts(selected.proof)
    except RecursionError:
        raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
    except ProofReductionError as exc:
        if "host recursion limit" in str(exc):
            raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
        raise TacticError(
            f"compact_arith final reduction failed: {exc}."
        ) from None
    proof_nodes, proof_depth, annotation_nodes = _proof_metrics(certificate, budget)
    budget.tick()
    if not check(context, certificate, equation):
        raise TacticError(
            "the independent kernel rejected the generated compact_arith certificate."
        )
    budget.tick()
    return CompactArithResult(
        equation=equation,
        certificate=certificate,
        proof_nodes=proof_nodes,
        proof_depth=proof_depth,
        annotation_nodes=annotation_nodes,
        work_units=budget.work_units,
        strategy=selected.strategy,
        used_assumptions=selected.used_assumptions,
    )


def compact_arith_checked(
    state: ProofState,
    assumptions: tuple[CompactArithAssumption, ...] = (),
    *,
    limits: CompactArithLimits = DEFAULT_COMPACT_ARITH_LIMITS,
    clock: Callable[[], float] = monotonic,
) -> ProofState:
    """Close the focused equality with a generated, checked compact proof."""

    if type(state) is not ProofState:
        raise TacticError("`compact_arith` needs an exact proof state.")
    if type(limits) is not CompactArithLimits:
        raise TacticError("`compact_arith` needs exact CompactArithLimits.")
    deadline = _Deadline(limits, clock)
    try:
        partial = state.partial
    except (AttributeError, TypeError, ValueError):
        raise TacticError("`compact_arith` needs a valid exact proof state.") from None
    _enforce_partial_bounds(partial, limits, deadline)
    _validate_state(state)
    deadline.check()
    goal = state.current()
    if goal is None:
        raise TacticError("there is no open goal.")
    try:
        target = apply_formula_subst(goal.target, state.subst)
        context = tuple(
            apply_formula_subst(formula, state.subst)
            for _, formula in goal.context
        )
    except RecursionError:
        raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
    except (AttributeError, StateError, TypeError, ValueError):
        raise TacticError("`compact_arith` needs a valid exact proof state.") from None
    if metas_in_formula(target, state.subst):
        raise TacticError("`compact_arith` cannot guess unresolved term metavariables.")
    if type(target) is not Eq:
        raise TacticError("`compact_arith` needs an equality goal.")
    result = prove_compact_equation(
        target,
        context=context,
        assumptions=assumptions,
        limits=limits,
        clock=deadline.planner_clock(),
    )
    try:
        after = replace_current_hole(state, result.certificate, ())
    except RecursionError:
        raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
    except (AttributeError, StateError, TypeError, ValueError):
        raise TacticError(
            "internal compact_arith result could not replace the focused hole."
        ) from None
    _enforce_partial_bounds(after.partial, limits, deadline)
    try:
        valid = invariants_ok(after)
    except RecursionError:
        raise TacticLimit("`compact_arith` exceeded the host recursion limit.") from None
    except (AttributeError, TypeError, ValueError):
        valid = False
    if not valid:
        raise TacticError(
            "internal compact_arith result mismatched goals and certificate holes."
        )
    args = ""
    if assumptions:
        args = "[" + ", ".join(item.name for item in assumptions) + "]"
    published = record_step(
        state,
        replace(after, history=state.history),
        "compact_arith",
        args,
    )
    deadline.check()
    return published


__all__ = [
    "CompactArithLimits",
    "DEFAULT_COMPACT_ARITH_LIMITS",
    "CompactArithAssumption",
    "CompactArithResult",
    "prove_compact_equation",
    "compact_arith_checked",
]
