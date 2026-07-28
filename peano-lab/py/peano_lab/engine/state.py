"""Immutable proof states, holes, and engine-only term metavariables.

This module copies the discipline of Lambda Lab's audited proof builder:
kernel variables and function symbols are rigid; only the distinct
``MetaVar`` class is flexible; unification is copy-on-write; and every
successful substitution is propagated through *all* goals and the partial
certificate.  The original target is never rewritten.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, fields, replace
from types import MappingProxyType
from typing import Mapping

from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import Proof
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


class StateError(ValueError):
    """An internal proof-state invariant would be violated."""


@dataclass(frozen=True, slots=True)
class MetaVar(Term):
    """A flexible engine term protected from ``depth`` newer binders.

    The ID identifies one proof-wide unknown.  ``depth`` is an occurrence
    annotation: ``?t`` below one later eigenvariable is ``MetaVar(id, 1)``.
    A solution is stored at depth zero and lifted at each protected occurrence.
    The kernel rejects this engine-only constructor at finalization.
    """

    id: int
    depth: int = 0

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id < 0:
            raise ValueError("metavariable ID must be a non-negative integer")
        if type(self.depth) is not int or self.depth < 0:
            raise ValueError("metavariable depth must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class Hole(Proof):
    """An engine-only open certificate position."""

    id: int


_meta_ids = itertools.count()
_hole_ids = itertools.count()


def fresh_meta() -> MetaVar:
    return MetaVar(next(_meta_ids))


def fresh_hole() -> Hole:
    return Hole(next(_hole_ids))


Subst = dict[int, Term]


@dataclass(frozen=True, slots=True)
class Goal:
    """One focused obligation; contexts are newest-hypothesis first."""

    context: tuple[tuple[str, Formula], ...]
    target: Formula
    variables: tuple[str, ...] = ()  # index-to-surface-name order

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", tuple(self.context))
        object.__setattr__(self, "variables", tuple(self.variables))

    @property
    def context_dict(self) -> dict[str, Formula]:
        return dict(reversed(self.context))


@dataclass(frozen=True, slots=True)
class Step:
    tactic: str
    args: str
    state_before: "ProofState"


@dataclass(frozen=True, slots=True)
class ProofState:
    goals: tuple[Goal, ...]
    partial_certificate_with_holes: Proof
    history: tuple[Step, ...]
    target: Formula  # the ORIGINAL stated goal
    subst: Mapping[int, Term] = field(default_factory=dict)
    variables: tuple[str, ...] = ()  # ORIGINAL index-to-name table

    def __post_init__(self) -> None:
        # A frozen dataclass containing a plain dict is only shallow-frozen.
        # Copy then hide the mapping so history snapshots cannot be mutated
        # through an alias held by a caller or a later tactic.
        object.__setattr__(self, "goals", tuple(self.goals))
        object.__setattr__(self, "history", tuple(self.history))
        object.__setattr__(self, "subst", MappingProxyType(dict(self.subst)))
        object.__setattr__(self, "variables", tuple(self.variables))

    def current(self) -> Goal | None:
        return self.goals[0] if self.goals else None

    def is_done(self) -> bool:
        return not self.goals

    @property
    def partial(self) -> Proof:
        """Concise compatibility alias for the pinned constructor field."""

        return self.partial_certificate_with_holes

    def final_certificate(self) -> Proof | None:
        return final_certificate(self)


def start(target: Formula, variables: tuple[str, ...] = ()) -> ProofState:
    """Start a theorem with one goal and one matching certificate hole."""

    return ProofState(
        goals=(Goal(context=(), target=target, variables=tuple(variables)),),
        partial_certificate_with_holes=fresh_hole(),
        history=(),
        target=target,
        subst={},
        variables=tuple(variables),
    )


def current(state: ProofState) -> Goal | None:
    return state.current()


def shift_engine_term(term: Term, by: int, cutoff: int = 0) -> Term:
    """Shift rigid variables and scoped metavariables together.

    Kernel shifting deliberately knows nothing about ``MetaVar``.  The engine
    companion increments an occurrence's protection depth when a newer binder
    is inserted at or below that depth.
    """

    if type(by) is not int or type(cutoff) is not int or cutoff < 0:
        raise ValueError("engine shift needs an integer amount and non-negative cutoff")
    if type(term) is MetaVar:
        depth = term.depth + by if term.depth >= cutoff else term.depth
        if depth < 0:
            raise ValueError("shift would create a negative metavariable depth")
        return MetaVar(term.id, depth)
    if type(term) is Var:
        index = term.index + by if term.index >= cutoff else term.index
        if index < 0:
            raise ValueError("shift would create a negative de Bruijn index")
        return Var(index)
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(shift_engine_term(term.term, by, cutoff))
    if type(term) is Add:
        return Add(
            shift_engine_term(term.left, by, cutoff),
            shift_engine_term(term.right, by, cutoff),
        )
    if type(term) is Mul:
        return Mul(
            shift_engine_term(term.left, by, cutoff),
            shift_engine_term(term.right, by, cutoff),
        )
    raise TypeError("expected a rigid kernel term or engine MetaVar")


def shift_engine_formula(formula: Formula, by: int, cutoff: int = 0) -> Formula:
    """Capture-safe formula shift that also scopes engine metavariables."""

    if type(formula) is Eq:
        return Eq(
            shift_engine_term(formula.left, by, cutoff),
            shift_engine_term(formula.right, by, cutoff),
        )
    if type(formula) is Bot:
        return formula
    if type(formula) in (Imp, And, Or):
        return type(formula)(
            shift_engine_formula(formula.left, by, cutoff),
            shift_engine_formula(formula.right, by, cutoff),
        )
    if type(formula) in (Forall, Exists):
        return type(formula)(
            shift_engine_formula(formula.body, by, cutoff + 1)
        )
    raise TypeError("expected a PA formula")


def _instantiate_term(term: Term, replacement: Term, depth: int) -> Term:
    if type(term) is MetaVar:
        # Opening removes one slot at ``depth``.  A meta created outside that
        # slot loses one layer of protection; a meta local to the body does not.
        return MetaVar(term.id, term.depth - 1) if term.depth > depth else term
    if type(term) is Var:
        if term.index == depth:
            return shift_engine_term(replacement, depth)
        if term.index > depth:
            return Var(term.index - 1)
        return term
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(_instantiate_term(term.term, replacement, depth))
    if type(term) is Add:
        return Add(
            _instantiate_term(term.left, replacement, depth),
            _instantiate_term(term.right, replacement, depth),
        )
    if type(term) is Mul:
        return Mul(
            _instantiate_term(term.left, replacement, depth),
            _instantiate_term(term.right, replacement, depth),
        )
    raise TypeError("expected a rigid kernel term or engine MetaVar")


def _instantiate_formula(formula: Formula, replacement: Term, depth: int) -> Formula:
    if type(formula) is Eq:
        return Eq(
            _instantiate_term(formula.left, replacement, depth),
            _instantiate_term(formula.right, replacement, depth),
        )
    if type(formula) is Bot:
        return formula
    if type(formula) in (Imp, And, Or):
        return type(formula)(
            _instantiate_formula(formula.left, replacement, depth),
            _instantiate_formula(formula.right, replacement, depth),
        )
    if type(formula) in (Forall, Exists):
        return type(formula)(
            _instantiate_formula(formula.body, replacement, depth + 1)
        )
    raise TypeError("expected a PA formula")


def instantiate_formula(formula: Formula, replacement: Term) -> Formula:
    """Open formula slot zero, retaining scope information for engine metas."""

    if not isinstance(replacement, Term):
        raise TypeError("replacement must be a PA term or engine MetaVar")
    return _instantiate_formula(formula, replacement, 0)


def walk_term(term: Term, subst: Mapping[int, Term]) -> Term:
    """Resolve a top-level meta and lift its depth-zero solution in place."""

    def resolve(value: Term, seen: set[int]) -> Term:
        if type(value) is not MetaVar or value.id not in subst:
            return value
        if value.id in seen:
            raise StateError("cyclic metavariable substitution")
        solution = resolve(subst[value.id], seen | {value.id})
        return shift_engine_term(solution, value.depth)

    return resolve(term, set())


def apply_term_subst(term: Term, subst: Mapping[int, Term]) -> Term:
    term = walk_term(term, subst)
    if type(term) is MetaVar or type(term) in (Var, Zero):
        return term
    if type(term) is Succ:
        return Succ(apply_term_subst(term.term, subst))
    if type(term) is Add:
        return Add(apply_term_subst(term.left, subst), apply_term_subst(term.right, subst))
    if type(term) is Mul:
        return Mul(apply_term_subst(term.left, subst), apply_term_subst(term.right, subst))
    raise TypeError("expected a rigid kernel term or engine MetaVar")


def apply_formula_subst(formula: Formula, subst: Mapping[int, Term]) -> Formula:
    if type(formula) is Eq:
        return Eq(apply_term_subst(formula.left, subst), apply_term_subst(formula.right, subst))
    if type(formula) is Bot:
        return formula
    if type(formula) in (Imp, And, Or):
        return type(formula)(
            apply_formula_subst(formula.left, subst),
            apply_formula_subst(formula.right, subst),
        )
    if type(formula) in (Forall, Exists):
        return type(formula)(apply_formula_subst(formula.body, subst))
    raise TypeError("expected a PA formula")


def apply_proof_subst(proof: Proof, subst: Mapping[int, Term]) -> Proof:
    """Apply a term substitution everywhere terms occur in a certificate."""

    if type(proof) is Hole:
        return proof
    if not isinstance(proof, Proof):
        raise TypeError("expected a proof certificate")
    changes: dict[str, object] = {}
    for item in fields(proof):
        value = getattr(proof, item.name)
        if isinstance(value, Proof):
            changes[item.name] = apply_proof_subst(value, subst)
        elif isinstance(value, Formula):
            changes[item.name] = apply_formula_subst(value, subst)
        elif isinstance(value, Term):
            changes[item.name] = apply_term_subst(value, subst)
    return replace(proof, **changes) if changes else proof


def _occurs(meta_id: int, term: Term, subst: Mapping[int, Term]) -> bool:
    term = walk_term(term, subst)
    if type(term) is MetaVar:
        return term.id == meta_id
    if type(term) is Succ:
        return _occurs(meta_id, term.term, subst)
    if type(term) in (Add, Mul):
        return _occurs(meta_id, term.left, subst) or _occurs(meta_id, term.right, subst)
    return False


def _lower_term(term: Term, by: int) -> Term | None:
    """Undo ``by`` protected binders, or reject eigenvariable dependence."""

    if type(term) is MetaVar:
        return MetaVar(term.id, term.depth - by) if term.depth >= by else None
    if type(term) is Var:
        return Var(term.index - by) if term.index >= by else None
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        child = _lower_term(term.term, by)
        return None if child is None else Succ(child)
    if type(term) in (Add, Mul):
        left, right = _lower_term(term.left, by), _lower_term(term.right, by)
        if left is None or right is None:
            return None
        return type(term)(left, right)
    raise TypeError("expected a rigid kernel term or engine MetaVar")


def unify_terms(
    left: Term, right: Term, subst: Mapping[int, Term] | None = None
) -> Subst | None:
    """Unify terms, extending a copy of ``subst``; only MetaVars may bind."""

    result: Subst = dict(subst or {})

    def bind(meta: MetaVar, value: Term) -> bool:
        lowered = _lower_term(value, meta.depth)
        if lowered is None or _occurs(meta.id, lowered, result):
            return False
        result[meta.id] = lowered
        return True

    def go(a: Term, b: Term) -> bool:
        a, b = walk_term(a, result), walk_term(b, result)
        if a == b:
            return True
        if type(a) is MetaVar:
            if bind(a, b):
                return True
            return type(b) is MetaVar and bind(b, a)
        if type(b) is MetaVar:
            return bind(b, a)
        if type(a) is not type(b):
            return False
        if type(a) is Succ:
            return go(a.term, b.term)
        if type(a) in (Add, Mul):
            return go(a.left, b.left) and go(a.right, b.right)
        return False  # distinct rigid variables, or a rigid symbol clash

    return result if go(left, right) else None


def unify_formulas(
    left: Formula, right: Formula, subst: Mapping[int, Term] | None = None
) -> Subst | None:
    """Unify identical formula shapes by unifying only their term leaves."""

    result: Subst = dict(subst or {})

    def terms(a: Term, b: Term) -> bool:
        nonlocal result
        extended = unify_terms(a, b, result)
        if extended is None:
            return False
        result = extended
        return True

    def formulas(a: Formula, b: Formula) -> bool:
        if type(a) is not type(b):
            return False
        if type(a) is Eq:
            return terms(a.left, b.left) and terms(a.right, b.right)
        if type(a) is Bot:
            return True
        if type(a) in (Imp, And, Or):
            return formulas(a.left, b.left) and formulas(a.right, b.right)
        if type(a) in (Forall, Exists):
            return formulas(a.body, b.body)
        return False

    return result if formulas(left, right) else None


def metas_in_term(term: Term, subst: Mapping[int, Term] | None = None) -> tuple[int, ...]:
    found: list[int] = []

    def visit(value: Term) -> None:
        value = walk_term(value, subst or {})
        if type(value) is MetaVar:
            if value.id not in found:
                found.append(value.id)
        elif type(value) is Succ:
            visit(value.term)
        elif type(value) in (Add, Mul):
            visit(value.left)
            visit(value.right)

    visit(term)
    return tuple(found)


def metas_in_formula(
    formula: Formula, subst: Mapping[int, Term] | None = None
) -> tuple[int, ...]:
    found: list[int] = []

    def visit(value: Formula) -> None:
        if type(value) is Eq:
            for term in (value.left, value.right):
                for meta_id in metas_in_term(term, subst):
                    if meta_id not in found:
                        found.append(meta_id)
        elif type(value) in (Imp, And, Or):
            visit(value.left)
            visit(value.right)
        elif type(value) in (Forall, Exists):
            visit(value.body)

    visit(formula)
    return tuple(found)


def metas_in_proof(
    proof: Proof, subst: Mapping[int, Term] | None = None
) -> tuple[int, ...]:
    found: list[int] = []

    def add(values: tuple[int, ...]) -> None:
        for meta_id in values:
            if meta_id not in found:
                found.append(meta_id)

    def visit(value: Proof) -> None:
        if type(value) is Hole:
            return
        for item in fields(value):
            child = getattr(value, item.name)
            if isinstance(child, Proof):
                visit(child)
            elif isinstance(child, Formula):
                add(metas_in_formula(child, subst))
            elif isinstance(child, Term):
                add(metas_in_term(child, subst))

    visit(proof)
    return tuple(found)


def holes_in(proof: Proof) -> tuple[int, ...]:
    found: list[int] = []

    def visit(value: Proof) -> None:
        if type(value) is Hole:
            found.append(value.id)
            return
        for item in fields(value):
            child = getattr(value, item.name)
            if isinstance(child, Proof):
                visit(child)

    visit(proof)
    return tuple(found)


def replace_hole(proof: Proof, hole_id: int, replacement: Proof) -> Proof:
    if type(proof) is Hole:
        return replacement if proof.id == hole_id else proof
    changes: dict[str, Proof] = {}
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            changes[item.name] = replace_hole(child, hole_id, replacement)
    return replace(proof, **changes) if changes else proof


def replace_current_hole(
    state: ProofState, replacement: Proof, new_goals: tuple[Goal, ...]
) -> ProofState:
    holes = holes_in(state.partial)
    if not state.goals or not holes:
        raise StateError("there is no current goal and certificate hole")
    if len(holes_in(replacement)) != len(new_goals):
        raise StateError("new goals do not match replacement certificate holes")
    result = replace(
        state,
        goals=tuple(new_goals) + state.goals[1:],
        partial_certificate_with_holes=replace_hole(state.partial, holes[0], replacement),
    )
    if not invariants_ok(result):
        raise StateError("goal/hole invariant failed after replacement")
    return result


def apply_subst_everywhere(state: ProofState, subst: Mapping[int, Term]) -> ProofState:
    """Propagate substitution proof-wide, deliberately preserving target/history."""

    goals = tuple(
        Goal(
            context=tuple(
                (name, apply_formula_subst(formula, subst))
                for name, formula in goal.context
            ),
            target=apply_formula_subst(goal.target, subst),
            variables=goal.variables,
        )
        for goal in state.goals
    )
    return replace(
        state,
        goals=goals,
        partial_certificate_with_holes=apply_proof_subst(state.partial, subst),
        subst=dict(subst),
    )


def record_step(
    before: ProofState, after: ProofState, tactic: str, args: str
) -> ProofState:
    return replace(
        after,
        history=before.history + (Step(tactic=tactic, args=args, state_before=before),),
    )


def undo(state: ProofState) -> ProofState:
    if not state.history:
        raise StateError("nothing to undo")
    return state.history[-1].state_before


def final_certificate(state: ProofState) -> Proof | None:
    certificate = apply_proof_subst(state.partial, state.subst)
    if state.goals or holes_in(certificate) or metas_in_proof(certificate):
        return None
    return certificate


def invariants_ok(state: ProofState) -> bool:
    holes = holes_in(state.partial)
    return len(state.goals) == len(holes) and len(holes) == len(set(holes))


def proof_metrics(proof: Proof) -> tuple[int, int]:
    """Return exact node count and depth without consuming Python recursion."""

    if not isinstance(proof, Proof):
        raise TypeError("proof_metrics expects a proof certificate")
    total = 0
    maximum_depth = 0
    pending = [(proof, 1)]
    while pending:
        node, depth = pending.pop()
        total += 1
        maximum_depth = max(maximum_depth, depth)
        pending.extend(
            (child, depth + 1)
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )
    return total, maximum_depth


def proof_size(proof: Proof) -> int:
    """Count certificate nodes (holes included while a proof is partial)."""

    return proof_metrics(proof)[0]


__all__ = [
    "StateError",
    "MetaVar",
    "Hole",
    "Subst",
    "Goal",
    "Step",
    "ProofState",
    "fresh_meta",
    "fresh_hole",
    "start",
    "current",
    "shift_engine_term",
    "shift_engine_formula",
    "instantiate_formula",
    "walk_term",
    "apply_term_subst",
    "apply_formula_subst",
    "apply_proof_subst",
    "unify_terms",
    "unify_formulas",
    "metas_in_term",
    "metas_in_formula",
    "metas_in_proof",
    "holes_in",
    "replace_hole",
    "replace_current_hole",
    "apply_subst_everywhere",
    "record_step",
    "undo",
    "final_certificate",
    "invariants_ok",
    "proof_metrics",
    "proof_size",
]
