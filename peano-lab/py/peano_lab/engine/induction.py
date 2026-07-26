"""Certificate construction for structural induction (M2).

The user sees two goals—base and successor step with a named IH—but the
partial certificate records the complete schema instance immediately.  This
module performs no trusted reasoning; QED still goes through the kernel.
"""

from __future__ import annotations

from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import ForallElim, ForallIntro, ImpIntro, Ind
from ..kernel.subst import shift_formula, subst_formula
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero
from .state import (
    Goal,
    ProofState,
    fresh_hole,
    metas_in_formula,
    replace_current_hole,
)


class InductionError(ValueError):
    """The requested induction split is not meaningful in this state."""


_RESERVED_NAMES = {"S", "forall", "exists", "bot", "false"}


def _valid_name(name: str) -> bool:
    return bool(
        name
        and name not in _RESERVED_NAMES
        and not name.startswith("?")
        and (name[0].isalpha() or name[0] == "_")
        and all(char.isalnum() or char in "_'" for char in name[1:])
    )


def _fresh_name(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    index = 1
    while f"{base}{index}" in used:
        index += 1
    return f"{base}{index}"


def _successor_instance(motive: Formula) -> Formula:
    # Environment before substitution: [placeholder, step n, outer ...].
    lifted = shift_formula(motive, 1, cutoff=1)
    return subst_formula(lifted, 0, Succ(Var(0)))


def _abstract_term(term: Term, variable_index: int, depth: int = 0) -> Term:
    """Add a placeholder slot and abstract one existing free variable."""

    sought = variable_index + 1 + depth
    if type(term) is Var:
        shifted = term.index + 1 if term.index >= depth else term.index
        return Var(depth) if shifted == sought else Var(shifted)
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(_abstract_term(term.term, variable_index, depth))
    if type(term) is Add:
        return Add(
            _abstract_term(term.left, variable_index, depth),
            _abstract_term(term.right, variable_index, depth),
        )
    if type(term) is Mul:
        return Mul(
            _abstract_term(term.left, variable_index, depth),
            _abstract_term(term.right, variable_index, depth),
        )
    raise InductionError("resolve term metavariables before induction.")


def _abstract_formula(
    formula: Formula, variable_index: int, depth: int = 0
) -> Formula:
    if type(formula) is Eq:
        return Eq(
            _abstract_term(formula.left, variable_index, depth),
            _abstract_term(formula.right, variable_index, depth),
        )
    if type(formula) is Bot:
        return formula
    if type(formula) in (Imp, And, Or):
        return type(formula)(
            _abstract_formula(formula.left, variable_index, depth),
            _abstract_formula(formula.right, variable_index, depth),
        )
    if type(formula) in (Forall, Exists):
        return type(formula)(
            _abstract_formula(formula.body, variable_index, depth + 1)
        )
    raise InductionError("expected a PA formula for induction.")


def _renamed_outer_variables(goal: Goal, index: int, induction_name: str) -> tuple[str, ...]:
    names = list(goal.variables)
    used = set(names) | {name for name, _ in goal.context}
    used.discard(names[index])
    names[index] = _fresh_name(f"{induction_name}_parameter", used | {induction_name})
    return tuple(names)


def build_induction(state: ProofState, variable_name: str) -> ProofState:
    """Replace the focused hole by an IND instance and open base/step goals.

    A quantified goal introduces a fresh surface name directly.  For a named
    context variable, the motive abstracts that rigid de Bruijn slot and the
    resulting universal proof is explicitly eliminated at the original term.
    """

    if not _valid_name(variable_name):
        raise InductionError("`induction` needs one variable name, not a term.")
    goal = state.current()
    if goal is None:
        raise InductionError("there is no open goal.")
    if metas_in_formula(goal.target, state.subst):
        raise InductionError("resolve term metavariables before induction.")

    target = goal.target
    eliminate_at: Term | None = None
    if variable_name in goal.variables:
        variable_index = goal.variables.index(variable_name)
        motive = _abstract_formula(target, variable_index)
        eliminate_at = Var(variable_index)
        if subst_formula(motive, 0, eliminate_at) != target:
            raise InductionError("internal error while abstracting the induction variable.")
        step_outer_names = _renamed_outer_variables(
            goal, variable_index, variable_name
        )
    elif type(target) is Forall:
        used_names = set(goal.variables) | {
            name for name, _ in goal.context
        }
        if variable_name in used_names:
            raise InductionError(
                f"the name {variable_name!r} is already used; choose a fresh binder name."
            )
        motive = target.body
        step_outer_names = goal.variables
    else:
        raise InductionError(
            "`induction` needs a universally quantified goal or a named context variable."
        )

    base_target = subst_formula(motive, 0, Zero())
    step_target = _successor_instance(motive)
    used_names = (
        {name for name, _ in goal.context}
        | set(goal.variables)
        | {variable_name}
    )
    ih_name = _fresh_name("IH", used_names)

    base_hole, step_hole = fresh_hole(), fresh_hole()
    shifted_context = tuple(
        (name, shift_formula(formula, 1)) for name, formula in goal.context
    )
    base_goal = Goal(goal.context, base_target, goal.variables)
    step_goal = Goal(
        ((ih_name, motive),) + shifted_context,
        step_target,
        (variable_name,) + step_outer_names,
    )

    induction = Ind(
        motive,
        base_hole,
        ForallIntro(ImpIntro(step_hole)),
    )
    replacement = (
        induction
        if eliminate_at is None
        else ForallElim(induction, eliminate_at)
    )
    return replace_current_hole(state, replacement, (base_goal, step_goal))


__all__ = ["InductionError", "build_induction"]
