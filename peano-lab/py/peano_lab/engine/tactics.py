"""Primitive Peano Lab tactics (untrusted certificate construction).

Every function is transactional: it builds a new immutable state and records
one history snapshot only after all parsing, matching, and invariant checks
succeed.  ``checked_final`` is the sole QED path and asks the independent
kernel to validate the finished certificate against the original target.
"""

from __future__ import annotations

from typing import Callable, Iterator

from ..kernel.checker import axiom_formula, check
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
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
    Hyp,
    ImpElim,
    ImpIntro,
    Proof,
)
from ..kernel.terms import Add, Mul, ParseError, Succ, Term, Var, Zero, parse_term_in_context
from .rewrite import NoRewriteOccurrence, RewriteError, RewriteUnderBinder, rewrite_formula
from .state import (
    Goal,
    Hole,
    ProofState,
    StateError,
    apply_formula_subst,
    apply_subst_everywhere,
    apply_term_subst,
    final_certificate,
    fresh_hole,
    fresh_meta,
    invariants_ok,
    metas_in_formula,
    proof_size,
    record_step,
    replace_current_hole,
    undo as undo_state,
    unify_formulas,
    unify_terms,
)
from .trace import TraceLogger


class TacticError(Exception):
    """A tactic failed; its message is final English and state is unchanged."""


class InvalidProof(Exception):
    """The independent checker refused QED; the session must survive."""


Tactic = Callable[[ProofState, str], ProofState]


def _current(state: ProofState) -> Goal:
    goal = state.current()
    if goal is None:
        raise TacticError("there is no open goal.")
    return goal


def _no_args(name: str, args: str) -> None:
    if args.strip():
        raise TacticError(f"`{name}` takes no arguments (got {args.strip()!r}).")


def _commit(
    before: ProofState,
    after: ProofState,
    tactic: str,
    args: str,
    subst: dict[int, Term] | None = None,
) -> ProofState:
    if subst is not None:
        after = apply_subst_everywhere(after, subst)
    if not invariants_ok(after):
        raise TacticError("internal error: goals and certificate holes are out of sync.")
    return record_step(before, after, tactic, args)


def _engine_term(goal: Goal, source: str, tactic: str) -> Term:
    text = source.strip()
    if not text:
        raise TacticError(f"`{tactic}` needs a term.")
    if text == "?":
        return fresh_meta()
    if text.startswith("?"):
        raise TacticError("use bare `?` for a fresh term metavariable.")
    try:
        return parse_term_in_context(text, list(goal.variables))
    except (ParseError, ValueError) as exc:
        raise TacticError(f"cannot parse the term: {exc}") from None


def refl(state: ProofState, args: str = "") -> ProofState:
    _no_args("refl", args)
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Eq:
        raise TacticError("`refl` applies only to an equality goal.")
    subst = unify_terms(target.left, target.right, state.subst)
    if subst is None:
        raise TacticError("`refl` failed because the two sides are not identical.")
    term = apply_term_subst(target.left, subst)
    after = replace_current_hole(state, EqRefl(term), ())
    return _commit(state, after, "refl", args, subst)


def symm(state: ProofState, args: str = "") -> ProofState:
    _no_args("symm", args)
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Eq:
        raise TacticError("`symm` applies only to an equality goal.")
    hole = fresh_hole()
    new_goal = Goal(goal.context, Eq(target.right, target.left), goal.variables)
    after = replace_current_hole(state, EqSym(hole), (new_goal,))
    return _commit(state, after, "symm", args)


def trans(state: ProofState, args: str) -> ProofState:
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Eq:
        raise TacticError("`trans` applies only to an equality goal.")
    middle = _engine_term(goal, args, "trans")
    left_hole, right_hole = fresh_hole(), fresh_hole()
    goals = (
        Goal(goal.context, Eq(target.left, middle), goal.variables),
        Goal(goal.context, Eq(middle, target.right), goal.variables),
    )
    after = replace_current_hole(state, EqTrans(left_hole, right_hole), goals)
    return _commit(state, after, "trans", args)


def congr(state: ProofState, args: str = "") -> ProofState:
    _no_args("congr", args)
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Eq:
        raise TacticError("`congr` applies only to an equality goal.")
    left, right = target.left, target.right
    if type(left) is Succ and type(right) is Succ:
        hole = fresh_hole()
        replacement: Proof = CongS(hole)
        goals = (Goal(goal.context, Eq(left.term, right.term), goal.variables),)
    elif type(left) is Add and type(right) is Add:
        first, second = fresh_hole(), fresh_hole()
        replacement = CongAdd(first, second)
        goals = (
            Goal(goal.context, Eq(left.left, right.left), goal.variables),
            Goal(goal.context, Eq(left.right, right.right), goal.variables),
        )
    elif type(left) is Mul and type(right) is Mul:
        first, second = fresh_hole(), fresh_hole()
        replacement = CongMul(first, second)
        goals = (
            Goal(goal.context, Eq(left.left, right.left), goal.variables),
            Goal(goal.context, Eq(left.right, right.right), goal.variables),
        )
    else:
        raise TacticError("`congr` needs both sides to have the same outer symbol S, +, or ·.")
    after = replace_current_hole(state, replacement, goals)
    return _commit(state, after, "congr", args)


def _hypothesis(goal: Goal, name: str) -> tuple[int, Formula]:
    for index, (candidate, formula) in enumerate(goal.context):
        if candidate == name:
            return index, formula
    raise TacticError(f"unknown hypothesis {name!r}.")


def exact(state: ProofState, args: str) -> ProofState:
    name = args.strip()
    if not name or any(char.isspace() for char in name):
        raise TacticError("`exact` needs one hypothesis name, e.g. `exact h`.")
    goal = _current(state)
    index, formula = _hypothesis(goal, name)
    subst = unify_formulas(formula, goal.target, state.subst)
    if subst is None:
        raise TacticError(f"hypothesis {name!r} does not match the current goal.")
    after = replace_current_hole(state, Hyp(index), ())
    return _commit(state, after, "exact", args, subst)


def assumption(state: ProofState, args: str = "") -> ProofState:
    _no_args("assumption", args)
    goal = _current(state)
    for index, (_, formula) in enumerate(goal.context):
        subst = unify_formulas(formula, goal.target, state.subst)
        if subst is not None:
            after = replace_current_hole(state, Hyp(index), ())
            return _commit(state, after, "assumption", args, subst)
    raise TacticError("no hypothesis matches the current goal.")


def _term_occurrences(term: Term) -> Iterator[Term]:
    yield term
    if type(term) is Succ:
        yield from _term_occurrences(term.term)
    elif type(term) in (Add, Mul):
        yield from _term_occurrences(term.left)
        yield from _term_occurrences(term.right)


def _formula_terms(formula: Formula) -> Iterator[Term]:
    if type(formula) is Eq:
        yield from _term_occurrences(formula.left)
        yield from _term_occurrences(formula.right)
    elif type(formula) in (Imp, And, Or):
        yield from _formula_terms(formula.left)
        yield from _formula_terms(formula.right)
    elif type(formula) in (Forall, Exists):
        return  # M1 explicitly refuses to rewrite below a term binder


def _match_axiom_pattern(
    pattern: Term,
    candidate: Term,
    binder_count: int,
    assignments: dict[int, Term],
) -> bool:
    if type(pattern) is Var and 0 <= pattern.index < binder_count:
        previous = assignments.get(pattern.index)
        if previous is None:
            assignments[pattern.index] = candidate
            return True
        return previous == candidate
    if type(pattern) is not type(candidate):
        return False
    if type(pattern) in (Var, Zero):
        return pattern == candidate
    if type(pattern) is Succ:
        return _match_axiom_pattern(pattern.term, candidate.term, binder_count, assignments)
    if type(pattern) in (Add, Mul):
        return _match_axiom_pattern(
            pattern.left, candidate.left, binder_count, assignments
        ) and _match_axiom_pattern(
            pattern.right, candidate.right, binder_count, assignments
        )
    return False


def _instantiate_pattern(term: Term, assignments: dict[int, Term]) -> Term:
    if type(term) is Var:
        return assignments[term.index]
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(_instantiate_pattern(term.term, assignments))
    if type(term) is Add:
        return Add(
            _instantiate_pattern(term.left, assignments),
            _instantiate_pattern(term.right, assignments),
        )
    if type(term) is Mul:
        return Mul(
            _instantiate_pattern(term.left, assignments),
            _instantiate_pattern(term.right, assignments),
        )
    raise TacticError("the PA axiom contains an unsupported term pattern.")


def _axiom_equation(
    name: str, formula: Formula, reverse: bool
) -> tuple[Eq, Proof]:
    axiom = axiom_formula(name)
    if axiom is None:
        raise TacticError(f"unknown hypothesis or PA axiom {name!r}.")
    binder_count = 0
    body = axiom
    while type(body) is Forall:
        binder_count += 1
        body = body.body
    if type(body) is not Eq:
        raise TacticError(f"{name} is not an equational PA axiom.")
    pattern = body.right if reverse else body.left
    chosen: dict[int, Term] | None = None
    for candidate in _formula_terms(formula):
        assignments: dict[int, Term] = {}
        if _match_axiom_pattern(pattern, candidate, binder_count, assignments):
            if len(assignments) == binder_count:
                chosen = assignments
                break
    if chosen is None:
        raise TacticError(
            f"{name} does not match an eligible occurrence; all axiom variables must be inferable."
        )
    equation = Eq(
        _instantiate_pattern(body.left, chosen),
        _instantiate_pattern(body.right, chosen),
    )
    proof: Proof = Axiom(name)
    for index in reversed(range(binder_count)):
        proof = ForallElim(proof, chosen[index])
    if not check((), proof, equation):
        raise TacticError("internal error: the instantiated PA axiom certificate is invalid.")
    return equation, proof


def _equation_source(
    goal: Goal, name: str, rewrite_target: Formula, reverse: bool, subst: dict[int, Term]
) -> tuple[Eq, Proof, int | None]:
    for index, (candidate, formula) in enumerate(goal.context):
        if candidate == name:
            formula = apply_formula_subst(formula, subst)
            if type(formula) is not Eq:
                raise TacticError(f"hypothesis {name!r} is not an equation.")
            return formula, Hyp(index), index
    equation, proof = _axiom_equation(name, rewrite_target, reverse)
    return equation, proof, None


def _rewrite_args(args: str) -> tuple[bool, str, str | None]:
    parts = args.split()
    reverse = bool(parts and parts[0] == "<-")
    if reverse:
        parts = parts[1:]
    if len(parts) == 1:
        return reverse, parts[0], None
    if len(parts) == 3 and parts[1] == "at":
        return reverse, parts[0], parts[2]
    raise TacticError("syntax: `rewrite h`, `rewrite <- h`, or add `at h'`.")


def _rewrite_failure(exc: RewriteError) -> TacticError:
    if isinstance(exc, RewriteUnderBinder):
        return TacticError("rewriting under quantifiers is deferred until M3.")
    if isinstance(exc, NoRewriteOccurrence):
        return TacticError("the selected side of the equation does not occur.")
    return TacticError(str(exc))


def _fresh_old_name(name: str, context: tuple[tuple[str, Formula], ...]) -> str:
    used = {candidate for candidate, _ in context}
    base = f"{name}_before"
    candidate, counter = base, 2
    while candidate in used:
        candidate = f"{base}{counter}"
        counter += 1
    return candidate


def rewrite(state: ProofState, args: str) -> ProofState:
    reverse, equation_name, at_name = _rewrite_args(args)
    goal = _current(state)
    target_formula = goal.target
    target_index: int | None = None
    if at_name is not None:
        target_index, target_formula = _hypothesis(goal, at_name)
    target_formula = apply_formula_subst(target_formula, state.subst)
    if metas_in_formula(target_formula, state.subst):
        raise TacticError("resolve term metavariables before rewriting.")
    equation, equation_proof, _ = _equation_source(
        goal, equation_name, target_formula, reverse, dict(state.subst)
    )
    try:
        rewritten, motive = rewrite_formula(target_formula, equation, reverse=reverse)
    except RewriteError as exc:
        raise _rewrite_failure(exc) from None
    except TypeError as exc:
        raise TacticError(f"rewrite could not use that equation: {exc}") from None

    hole = fresh_hole()
    if at_name is None:
        # The new hole proves motive[new].  Transport it back to the original
        # goal motive[old], hence the direction is opposite the visible rewrite.
        transport = equation_proof if reverse else EqSym(equation_proof)
        replacement = EqSubst(motive, transport, hole)
        new_goal = Goal(goal.context, rewritten, goal.variables)
    else:
        assert target_index is not None
        # Derive the rewritten hypothesis from the original one, then use a
        # local implication (cut).  The original is retained under a fresh
        # internal name so Hyp indices remain an honest kernel context.
        transport = EqSym(equation_proof) if reverse else equation_proof
        derived = EqSubst(motive, transport, Hyp(target_index))
        replacement = ImpElim(ImpIntro(hole), derived)
        renamed = list(goal.context)
        old_name = _fresh_old_name(at_name, goal.context)
        renamed[target_index] = (old_name, renamed[target_index][1])
        new_context = ((at_name, rewritten),) + tuple(renamed)
        new_goal = Goal(new_context, goal.target, goal.variables)
    after = replace_current_hole(state, replacement, (new_goal,))
    return _commit(state, after, "rewrite", args)


def undo(state: ProofState, args: str = "") -> ProofState:
    _no_args("undo", args)
    try:
        return undo_state(state)
    except StateError as exc:
        raise TacticError(f"{exc}.") from None


def checked_final(
    state: ProofState,
    original_target: Formula,
    *,
    trace: TraceLogger | None = None,
) -> Proof:
    """Check QED against the session owner's original target.

    The original is an explicit argument on purpose: a buggy tactic can return
    an entirely new ``ProofState``, frozen fields and all.  The UI/session owns
    this argument and never obtains it back from the untrusted tactic result.
    """

    if state.goals:
        raise InvalidProof(f"{len(state.goals)} goal(s) are still open.")
    certificate = final_certificate(state)
    if certificate is None:
        raise InvalidProof("the partial certificate still contains a hole or term metavariable.")
    if state.target != original_target:
        raise InvalidProof("the proof state no longer carries the session's original goal.")
    if not check((), certificate, original_target):
        raise InvalidProof("the independent kernel rejected the certificate for the stated goal.")
    if trace is not None:
        trace.footer(
            qed=True,
            theorem=original_target,
            proof_size=proof_size(certificate),
            names=state.variables,
        )
    return certificate


_TACTICS: dict[str, Tactic] = {
    "refl": refl,
    "symm": symm,
    "trans": trans,
    "congr": congr,
    "exact": exact,
    "assumption": assumption,
    "rewrite": rewrite,
    "undo": undo,
}
TACTIC_NAMES = tuple(_TACTICS)


def apply_tactic(
    state: ProofState,
    tactic: str,
    args: str = "",
    *,
    trace: TraceLogger | None = None,
) -> ProofState:
    """Dispatch one tactic and wire both success and failure trace records."""

    typed = f"{tactic} {args}".strip()
    function = _TACTICS.get(tactic)
    if function is None:
        error = TacticError(
            f"unknown tactic {tactic!r}; available: {', '.join(TACTIC_NAMES)}."
        )
        if trace is not None:
            trace.failure(state, 0, typed, error)
        raise error
    try:
        result = function(state, args)
    except TacticError as error:
        if trace is not None:
            trace.failure(state, 0, typed, error)
        raise
    if trace is not None:
        trace.success(state, 0, typed, result)
    return result


def final_proof_size(state: ProofState, original_target: Formula) -> int:
    certificate = checked_final(state, original_target)
    return proof_size(certificate)


__all__ = [
    "TacticError",
    "InvalidProof",
    "Tactic",
    "TACTIC_NAMES",
    "refl",
    "symm",
    "trans",
    "congr",
    "exact",
    "assumption",
    "rewrite",
    "undo",
    "apply_tactic",
    "checked_final",
    "final_proof_size",
]
