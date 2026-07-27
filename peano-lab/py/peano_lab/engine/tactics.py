"""Primitive Peano Lab tactics (untrusted certificate construction).

Every function is transactional: it builds a new immutable state and records
one history snapshot only after all parsing, matching, and invariant checks
succeed.  ``checked_final`` is the sole QED path and asks the independent
kernel to validate the finished certificate against the original target.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Callable, Iterator

from ..kernel.checker import axiom_formula, check, check_classical
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import (
    AndElimL,
    AndElimR,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    DNE,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    OrElim,
    OrIntroL,
    OrIntroR,
    Proof,
)
from ..kernel.subst import shift_formula
from ..kernel.terms import Add, Mul, ParseError, Succ, Term, Var, Zero, parse_term_in_context
from .induction import InductionError, build_induction
from .rewrite import (
    PA_SIMP_SET,
    InvalidSimpRule,
    NoRewriteOccurrence,
    RewriteError,
    RewriteUnderBinder,
    SimpError,
    SimpLimitExceeded,
    SimpRule,
    SimpSet,
    rewrite_formula,
    simplify_formula,
)
from .state import (
    Goal,
    ProofState,
    StateError,
    apply_formula_subst,
    apply_subst_everywhere,
    apply_term_subst,
    final_certificate,
    fresh_hole,
    fresh_meta,
    instantiate_formula,
    invariants_ok,
    metas_in_formula,
    metas_in_proof,
    metas_in_term,
    proof_size,
    record_step,
    replace_current_hole,
    shift_engine_formula,
    undo as undo_state,
    unify_formulas,
    unify_terms,
)
from .trace import TraceLogger


class TacticError(Exception):
    """A tactic failed; its message is final English and state is unchanged."""


class TacticSyntaxError(TacticError):
    """A proposed tactic line is not a command in the surface language."""


class TacticLimit(TacticError):
    """A tactic failed specifically because an honest resource bound was hit."""


class InvalidProof(Exception):
    """The independent checker refused QED; the session must survive."""


Tactic = Callable[[ProofState, str], ProofState]

_RESERVED_TERM_NAMES = {"S", "forall", "exists", "bot", "false"}

# ``use`` embeds a checked theorem certificate in the live partial proof until
# surface finalization contracts the cut.  Honest bounds keep repeated aliases
# from turning that temporary tree into a host-recursion or browser-memory
# failure.  The current checked ladder's largest certificate is far smaller
# (222 nodes, depth 38), leaving ample room for later arithmetic lemmas.
MAX_USE_CERTIFICATE_NODES = 4_096
MAX_USE_PARTIAL_NODES = 32_768
MAX_USE_PROOF_DEPTH = 128


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
    # A universal instantiation may introduce an implicit term that no goal can
    # constrain (for example applying ``forall x. 0 = 0``).  Choose canonical
    # 0 only for such a *freshly introduced* proof-only meta.  An older meta may
    # still be constrained by a sibling hidden behind ``focus``; defaulting it
    # in an isolated child state would break proof-wide sharing.
    preexisting_meta_ids = set(before.subst)
    preexisting_meta_ids.update(metas_in_proof(before.partial))
    for term in before.subst.values():
        preexisting_meta_ids.update(metas_in_term(term))
    for old_goal in before.goals:
        preexisting_meta_ids.update(metas_in_formula(old_goal.target))
        for _, formula in old_goal.context:
            preexisting_meta_ids.update(metas_in_formula(formula))
    open_meta_ids: set[int] = set()
    for goal in after.goals:
        open_meta_ids.update(metas_in_formula(goal.target, after.subst))
        for _, formula in goal.context:
            open_meta_ids.update(metas_in_formula(formula, after.subst))
    proof_meta_ids = set(metas_in_proof(after.partial, after.subst))
    unconstrained = proof_meta_ids - open_meta_ids - preexisting_meta_ids
    if unconstrained:
        completed_subst = dict(after.subst)
        completed_subst.update(
            {meta_id: Zero() for meta_id in sorted(unconstrained)}
        )
        after = apply_subst_everywhere(after, completed_subst)
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


def _surface_name(source: str, tactic: str) -> str:
    """Parse the one identifier accepted by binder-oriented tactics."""

    name = source.strip()
    if (
        not name
        or name in _RESERVED_TERM_NAMES
        or name.startswith("?")
        or not (name[0].isalpha() or name[0] == "_")
        or not all(char.isalnum() or char in "_'" for char in name[1:])
    ):
        raise TacticError(f"`{tactic}` needs one variable name, e.g. `{tactic} n`.")
    return name


def _enforce_use_proof_budget(
    proof: Proof,
    *,
    max_nodes: int,
    label: str,
) -> None:
    """Measure a proof iteratively before ``use`` invokes recursive code."""

    pending = [(proof, 1)]
    node_count = 0
    try:
        while pending:
            current, depth = pending.pop()
            node_count += 1
            if node_count > max_nodes or depth > MAX_USE_PROOF_DEPTH:
                raise TacticLimit(
                    f"`use` exceeded its {max_nodes}-node / "
                    f"{MAX_USE_PROOF_DEPTH}-level {label} limit."
                )
            for item in fields(current):
                child = getattr(current, item.name)
                if isinstance(child, Proof):
                    pending.append((child, depth + 1))
    except TacticLimit:
        raise
    except (AttributeError, TypeError, ValueError):
        raise TacticError("`use` needs an exact checked theorem certificate.") from None


def _used_names(goal: Goal) -> set[str]:
    return set(goal.variables) | {name for name, _ in goal.context}


def _fresh_visible_name(base: str, goal: Goal, *extra: str) -> str:
    used = _used_names(goal) | set(extra)
    if base not in used and base not in _RESERVED_TERM_NAMES:
        return base
    counter = 1
    while f"{base}{counter}" in used:
        counter += 1
    return f"{base}{counter}"


def intro(state: ProofState, args: str = "") -> ProofState:
    """Introduce one implication hypothesis or universal eigenvariable."""

    goal = _current(state)
    pieces = args.split()
    if len(pieces) > 1:
        raise TacticError("`intro` takes at most one name.")
    supplied_name = _surface_name(pieces[0], "intro") if pieces else None
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) not in (Imp, Forall):
        raise TacticError("`intro` needs an implication or universally quantified goal.")

    name = supplied_name or _fresh_visible_name(
        "h" if type(target) is Imp else "n", goal
    )
    if name in _used_names(goal):
        raise TacticError(f"the name {name!r} is already in use; choose a fresh name.")

    hole = fresh_hole()
    if type(target) is Imp:
        replacement: Proof = ImpIntro(hole)
        new_goal = Goal(
            ((name, target.left),) + goal.context,
            target.right,
            goal.variables,
        )
    else:
        replacement = ForallIntro(hole)
        shifted_context = tuple(
            (hyp_name, shift_engine_formula(formula, 1))
            for hyp_name, formula in goal.context
        )
        new_goal = Goal(
            shifted_context,
            target.body,
            (name,) + goal.variables,
        )
    after = replace_current_hole(state, replacement, (new_goal,))
    return _commit(state, after, "intro", args)


def _specialize(state: ProofState, args: str, tactic: str) -> ProofState:
    """Add one explicitly instantiated copy of a universal hypothesis."""

    parts = args.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise TacticSyntaxError(f"syntax: `{tactic} h t`.")
    hypothesis_name, term_source = parts
    goal = _current(state)
    index, formula = _hypothesis(goal, hypothesis_name)
    formula = apply_formula_subst(formula, state.subst)
    if type(formula) is not Forall:
        raise TacticError(f"hypothesis {hypothesis_name!r} is not universally quantified.")
    term = _engine_term(goal, term_source, tactic)
    if metas_in_term(term, state.subst):
        raise TacticError(f"`{tactic}` needs a concrete term, not a metavariable.")

    instance = instantiate_formula(formula.body, term)
    derived = ForallElim(Hyp(index), term)
    hole = fresh_hole()
    renamed = list(goal.context)
    renamed[index] = (
        _fresh_old_name(hypothesis_name, goal.context, goal.variables),
        renamed[index][1],
    )
    new_context = ((hypothesis_name, instance),) + tuple(renamed)
    replacement = ImpElim(ImpIntro(hole), derived)
    new_goal = Goal(new_context, goal.target, goal.variables)
    after = replace_current_hole(state, replacement, (new_goal,))
    return _commit(state, after, tactic, args)


def specialize(state: ProofState, args: str) -> ProofState:
    return _specialize(state, args, "specialize")


def forall_elim(state: ProofState, args: str) -> ProofState:
    return _specialize(state, args, "forall_elim")


def induction(state: ProofState, args: str) -> ProofState:
    """Open the base and successor obligations for structural induction."""

    name = _surface_name(args, "induction")
    try:
        after = build_induction(state, name)
    except InductionError as exc:
        raise TacticError(str(exc)) from None
    return _commit(state, after, "induction", args)


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


def _dne_formula(proposition: Formula) -> Formula:
    negation = Imp(proposition, Bot())
    return Imp(Imp(negation, Bot()), proposition)


def _proof_source(
    goal: Goal,
    name: str,
    target: Formula,
    subst: dict[int, Term],
    *,
    classical: bool,
) -> tuple[Formula, Proof]:
    for index, (candidate, formula) in enumerate(goal.context):
        if candidate == name:
            return apply_formula_subst(formula, subst), Hyp(index)
    axiom = axiom_formula(name)
    if axiom is not None:
        return axiom, Axiom(name)
    if name == "DNE":
        if not classical:
            raise TacticError("DNE is unavailable while classical mode is off.")
        return _dne_formula(target), DNE(target)
    raise TacticError(f"unknown hypothesis or proof constant {name!r}.")


def apply_(
    state: ProofState,
    args: str,
    *,
    classical: bool = False,
) -> ProofState:
    """Apply a hypothesis, PA axiom, or explicitly enabled DNE certificate."""

    if type(classical) is not bool:
        raise TacticError("classical mode must be a Boolean.")
    name = args.strip()
    if not name or any(char.isspace() for char in name):
        raise TacticError("`apply` needs one hypothesis or proof constant.")
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    formula, proof = _proof_source(
        goal,
        name,
        target,
        dict(state.subst),
        classical=classical,
    )

    exact_subst = unify_formulas(formula, target, state.subst)
    if exact_subst is not None:
        after = replace_current_hole(state, proof, ())
        return _commit(state, after, "apply", args, exact_subst)

    while type(formula) is Forall:
        term = fresh_meta()
        formula = instantiate_formula(formula.body, term)
        proof = ForallElim(proof, term)

    premises: list[Formula] = []
    while type(formula) is Imp:
        premises.append(formula.left)
        formula = formula.right
    unified = unify_formulas(formula, target, state.subst)
    if unified is None:
        raise TacticError(
            f"the result of {name!r} does not match the current goal."
        )

    holes = tuple(fresh_hole() for _ in premises)
    replacement = proof
    for hole in holes:
        replacement = ImpElim(replacement, hole)
    new_goals = tuple(
        Goal(goal.context, premise, goal.variables) for premise in premises
    )
    after = replace_current_hole(state, replacement, new_goals)
    return _commit(state, after, "apply", args, unified)


def split(state: ProofState, args: str = "") -> ProofState:
    _no_args("split", args)
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not And:
        raise TacticError("`split` applies only to a conjunction goal.")
    left_hole, right_hole = fresh_hole(), fresh_hole()
    goals = (
        Goal(goal.context, target.left, goal.variables),
        Goal(goal.context, target.right, goal.variables),
    )
    after = replace_current_hole(
        state,
        AndIntro(left_hole, right_hole),
        goals,
    )
    return _commit(state, after, "split", args)


def left(state: ProofState, args: str = "") -> ProofState:
    _no_args("left", args)
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Or:
        raise TacticError("`left` applies only to a disjunction goal.")
    hole = fresh_hole()
    after = replace_current_hole(
        state,
        OrIntroL(hole),
        (Goal(goal.context, target.left, goal.variables),),
    )
    return _commit(state, after, "left", args)


def right(state: ProofState, args: str = "") -> ProofState:
    _no_args("right", args)
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Or:
        raise TacticError("`right` applies only to a disjunction goal.")
    hole = fresh_hole()
    after = replace_current_hole(
        state,
        OrIntroR(hole),
        (Goal(goal.context, target.right, goal.variables),),
    )
    return _commit(state, after, "right", args)


def cases(state: ProofState, args: str) -> ProofState:
    name = args.strip()
    if not name or any(char.isspace() for char in name):
        raise TacticError("`cases` needs one hypothesis name, e.g. `cases h`.")
    goal = _current(state)
    index, source = _hypothesis(goal, name)
    source = apply_formula_subst(source, state.subst)

    if type(source) is Or:
        left_name = _fresh_visible_name(f"{name}_left", goal)
        right_name = _fresh_visible_name(f"{name}_right", goal, left_name)
        left_hole, right_hole = fresh_hole(), fresh_hole()
        replacement: Proof = OrElim(Hyp(index), left_hole, right_hole)
        goals = (
            Goal(
                ((left_name, source.left),) + goal.context,
                goal.target,
                goal.variables,
            ),
            Goal(
                ((right_name, source.right),) + goal.context,
                goal.target,
                goal.variables,
            ),
        )
    elif type(source) is And:
        left_name = _fresh_visible_name(f"{name}_left", goal)
        right_name = _fresh_visible_name(f"{name}_right", goal, left_name)
        hole = fresh_hole()
        right_cut = ImpElim(
            ImpIntro(hole),
            AndElimR(Hyp(index + 1)),
        )
        replacement = ImpElim(
            ImpIntro(right_cut),
            AndElimL(Hyp(index)),
        )
        goals = (
            Goal(
                (
                    (right_name, source.right),
                    (left_name, source.left),
                )
                + goal.context,
                goal.target,
                goal.variables,
            ),
        )
    elif type(source) is Exists:
        witness_name = _fresh_visible_name("x", goal)
        proof_name = _fresh_visible_name(
            f"{name}_witness", goal, witness_name
        )
        shifted_context = tuple(
            (hyp_name, shift_engine_formula(formula, 1))
            for hyp_name, formula in goal.context
        )
        hole = fresh_hole()
        replacement = ExistsElim(Hyp(index), hole)
        goals = (
            Goal(
                ((proof_name, source.body),) + shifted_context,
                shift_engine_formula(goal.target, 1),
                (witness_name,) + goal.variables,
            ),
        )
    elif type(source) is Bot:
        replacement = BotElim(Hyp(index))
        goals = ()
    else:
        raise TacticError(
            f"hypothesis {name!r} is not a conjunction, disjunction, existential, or bottom."
        )

    after = replace_current_hole(state, replacement, goals)
    return _commit(state, after, "cases", args)


def exfalso(state: ProofState, args: str = "") -> ProofState:
    _no_args("exfalso", args)
    goal = _current(state)
    if type(apply_formula_subst(goal.target, state.subst)) is Bot:
        raise TacticError("the current goal is already bottom; `exfalso` made no progress.")
    hole = fresh_hole()
    after = replace_current_hole(
        state,
        BotElim(hole),
        (Goal(goal.context, Bot(), goal.variables),),
    )
    return _commit(state, after, "exfalso", args)


def exists_(state: ProofState, args: str) -> ProofState:
    goal = _current(state)
    target = apply_formula_subst(goal.target, state.subst)
    if type(target) is not Exists:
        raise TacticError("`exists` applies only to an existential goal.")
    witness = _engine_term(goal, args, "exists")
    hole = fresh_hole()
    instance = instantiate_formula(target.body, witness)
    after = replace_current_hole(
        state,
        ExistsIntro(witness, hole),
        (Goal(goal.context, instance, goal.variables),),
    )
    return _commit(state, after, "exists", args)


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
        # A proof instantiated outside this binder cannot borrow its local
        # variable.  Users may ``intro x`` and instantiate the axiom there.
        return


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
    raise TacticSyntaxError(
        "syntax: `rewrite h`, `rewrite <- h`, or add `at h'`."
    )


def _rewrite_failure(exc: RewriteError) -> TacticError:
    if isinstance(exc, RewriteUnderBinder):
        return TacticError("rewriting could not cross that quantifier safely.")
    if isinstance(exc, NoRewriteOccurrence):
        return TacticError("the selected side of the equation does not occur.")
    return TacticError(str(exc))


def _fresh_old_name(
    name: str,
    context: tuple[tuple[str, Formula], ...],
    variables: tuple[str, ...] = (),
) -> str:
    used = {candidate for candidate, _ in context} | set(variables)
    base = f"{name}_before"
    candidate, counter = base, 2
    while candidate in used:
        candidate = f"{base}{counter}"
        counter += 1
    return candidate


def use_checked(
    state: ProofState,
    name: str,
    formula: Formula,
    certificate: Proof,
) -> ProofState:
    """Expose one independently checked closed theorem as a local hypothesis.

    The engine deliberately receives the theorem data rather than importing the
    library by name.  It first asks the independent kernel to check the supplied
    closed certificate, then inserts an ordinary local cut.  The untrusted
    library/UI layer may later contract that cut before the final QED check; no
    theorem-name rule is added to the kernel.
    """

    goal = _current(state)
    visible_name = _surface_name(name, "use")
    if visible_name in _used_names(goal):
        raise TacticError(f"the name {visible_name!r} is already in use.")
    if not isinstance(formula, Formula) or not isinstance(certificate, Proof):
        raise TacticError("`use` needs an exact checked theorem certificate.")
    _enforce_use_proof_budget(
        certificate,
        max_nodes=MAX_USE_CERTIFICATE_NODES,
        label="import-certificate",
    )
    _enforce_use_proof_budget(
        state.partial,
        max_nodes=MAX_USE_PARTIAL_NODES,
        label="live-certificate",
    )
    if not check((), certificate, formula):
        raise TacticError(
            "the independent kernel rejected the library theorem certificate."
        )

    hole = fresh_hole()
    replacement = ImpElim(ImpIntro(hole), certificate)
    new_goal = Goal(
        ((visible_name, formula),) + goal.context,
        goal.target,
        goal.variables,
    )
    after = replace_current_hole(state, replacement, (new_goal,))
    _enforce_use_proof_budget(
        after.partial,
        max_nodes=MAX_USE_PARTIAL_NODES,
        label="live-certificate",
    )
    return _commit(state, after, "use", visible_name)


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
        old_name = _fresh_old_name(at_name, goal.context, goal.variables)
        renamed[target_index] = (old_name, renamed[target_index][1])
        new_context = ((at_name, rewritten),) + tuple(renamed)
        new_goal = Goal(new_context, goal.target, goal.variables)
    after = replace_current_hole(state, replacement, (new_goal,))
    return _commit(state, after, "rewrite", args)


def _simp_args(args: str) -> tuple[tuple[bool, str], ...]:
    """Parse the deliberately small explicit-set syntax ``simp [h, <- k]``."""

    text = args.strip()
    if not text:
        return ()
    if not (text.startswith("[") and text.endswith("]")):
        raise TacticSyntaxError("syntax: `simp` or `simp [h, <- k]`.")
    body = text[1:-1].strip()
    if not body:
        return ()
    result: list[tuple[bool, str]] = []
    for item in body.split(","):
        words = item.strip().split()
        reverse = bool(words and words[0] in {"<-", "←"})
        if reverse:
            words = words[1:]
        if len(words) != 1:
            raise TacticSyntaxError("syntax: `simp` or `simp [h, <- k]`.")
        name = words[0]
        if any(char.isspace() for char in name):
            raise TacticError("each simp lemma must be one hypothesis name.")
        result.append((reverse, name))
    shown = [("<- " if reverse else "") + name for reverse, name in result]
    if len(shown) != len(set(shown)):
        raise TacticError("each explicit simp lemma may be listed only once.")
    return tuple(result)


def _shift_simp_set(simp_set: SimpSet) -> SimpSet:
    """Move context-dependent rules below one freshly introduced binder."""

    return SimpSet(
        tuple(
            SimpRule(
                rule.name,
                shift_formula(rule.theorem, 1),
                rule.proof,
                rule.reverse,
            )
            for rule in simp_set.rules
        )
    )


def _solve_simp_normal(
    context: tuple[tuple[str, Formula], ...], formula: Formula
) -> Proof | None:
    """Close a normal form by exactness, reflexivity, or congruence only.

    This is deliberately not search: it follows the two equality terms in
    lockstep and stops at the first unsupported leaf.  Every successful branch
    returns an ordinary kernel certificate.
    """

    if type(formula) is Eq and formula.left == formula.right:
        return EqRefl(formula.left)
    for index, (_, hypothesis) in enumerate(context):
        if hypothesis == formula:
            return Hyp(index)
    if type(formula) is not Eq:
        return None

    left, right = formula.left, formula.right
    if type(left) is Succ and type(right) is Succ:
        child = _solve_simp_normal(context, Eq(left.term, right.term))
        return None if child is None else CongS(child)
    if type(left) is Add and type(right) is Add:
        left_proof = _solve_simp_normal(context, Eq(left.left, right.left))
        right_proof = _solve_simp_normal(context, Eq(left.right, right.right))
        if left_proof is not None and right_proof is not None:
            return CongAdd(left_proof, right_proof)
    if type(left) is Mul and type(right) is Mul:
        left_proof = _solve_simp_normal(context, Eq(left.left, right.left))
        right_proof = _solve_simp_normal(context, Eq(left.right, right.right))
        if left_proof is not None and right_proof is not None:
            return CongMul(left_proof, right_proof)
    return None


def simp(
    state: ProofState,
    args: str = "",
    *,
    tagged: SimpSet | None = None,
) -> ProofState:
    """Simplify the focused goal by certified, terminating rewrites.

    PA3--PA6 are always first in the ordered set.  ``tagged`` carries explicit
    library lemmas (a theorem formula paired with its proof certificate), and
    ``[h, <- k]`` appends selected context equations.  Every visible rewrite
    becomes an ``EqSubst`` node; a final reflexive equality or exact hypothesis
    is closed, otherwise the simplified normal form remains as one goal.
    """

    goal = _current(state)
    selected = _simp_args(args)
    if tagged is not None and type(tagged) is not SimpSet:
        raise TacticError("tagged simp lemmas must be supplied as a SimpSet.")

    resolved_context = tuple(
        apply_formula_subst(formula, state.subst)
        for _, formula in goal.context
    )
    if tagged is not None:
        for rule in tagged.rules:
            if not check(resolved_context, rule.proof, rule.theorem):
                raise TacticError(
                    f"tagged simp lemma {rule.name!r} is not checked in the current context."
                )
            # The current bidirectional kernel can check an introduction form
            # at a known forall target but cannot synthesize that target when
            # the proof is later placed under ForallElim.  Probe a canonical
            # instance now and reject such non-reusable certificates instead
            # of constructing a state that can only fail at QED.
            reusable_formula = rule.theorem
            reusable_proof = rule.proof
            while type(reusable_formula) is Forall:
                reusable_formula = instantiate_formula(
                    reusable_formula.body, Zero()
                )
                reusable_proof = ForallElim(reusable_proof, Zero())
            if not check(resolved_context, reusable_proof, reusable_formula):
                raise TacticError(
                    f"tagged simp lemma {rule.name!r} cannot be synthesized by the kernel."
                )

    extra_rules = list(tagged.rules if tagged is not None else ())
    for reverse, name in selected:
        index, raw_formula = _hypothesis(goal, name)
        formula = apply_formula_subst(raw_formula, state.subst)
        if metas_in_formula(formula, state.subst):
            raise TacticError(
                f"resolve term metavariables in simp lemma {name!r} first."
            )
        rule_name = f"<- {name}" if reverse else name
        extra_rules.append(SimpRule(rule_name, formula, Hyp(index), reverse))
    try:
        simp_set = PA_SIMP_SET.extend(*extra_rules)
    except InvalidSimpRule as exc:
        raise TacticError(f"invalid simp set: {exc}.") from None

    target = apply_formula_subst(goal.target, state.subst)
    if metas_in_formula(target, state.subst):
        raise TacticError("resolve term metavariables before simplification.")
    context = tuple(
        (name, formula)
        for (name, _), formula in zip(goal.context, resolved_context)
    )
    variables = goal.variables
    forall_count = 0

    # A PA axiom instantiated with a quantifier-local variable is not a proof
    # in the surrounding context.  Open leading quantifiers honestly, shift
    # context-dependent rules with them, then wrap the result in ForallIntro.
    while type(target) is Forall:
        temporary = Goal(context, target, variables)
        binder = _fresh_visible_name("x", temporary)
        context = tuple(
            (name, shift_engine_formula(formula, 1))
            for name, formula in context
        )
        variables = (binder,) + variables
        target = target.body
        simp_set = _shift_simp_set(simp_set)
        forall_count += 1

    try:
        result = simplify_formula(target, simp_set)
    except SimpLimitExceeded as exc:
        raise TacticLimit(f"simp failed: {exc}.") from None
    except (SimpError, TypeError, ValueError) as exc:
        raise TacticError(f"simp failed: {exc}.") from None

    normal_proof = _solve_simp_normal(context, result.formula)

    if normal_proof is None:
        if not result.steps:
            raise TacticError("`simp` made no progress on the current goal.")
        hole = fresh_hole()
        replacement = result.transport_back(hole)
        new_goals = (Goal(context, result.formula, variables),)
    else:
        replacement = result.transport_back(normal_proof)
        new_goals = ()
    for _ in range(forall_count):
        replacement = ForallIntro(replacement)

    after = replace_current_hole(state, replacement, new_goals)
    return _commit(state, after, "simp", args)


def undo(state: ProofState, args: str = "") -> ProofState:
    _no_args("undo", args)
    try:
        return undo_state(state)
    except StateError as exc:
        raise TacticError(f"{exc}.") from None


def set_classical_mode(
    current: bool,
    args: str,
    *,
    state: ProofState | None = None,
    trace: TraceLogger | None = None,
) -> bool:
    """Return the session owner's new mode and optionally trace the event.

    Mode deliberately does not live in ``ProofState``: a tactic-controlled
    state must not be able to authorize DNE at finalization.  The future UI
    owns this Boolean beside the original theorem statement.
    """

    typed = f"classical {args}".strip()

    def fail(
        message: str,
        error_type: type[TacticError] = TacticError,
    ) -> None:
        error = error_type(message)
        if trace is not None and state is not None:
            trace.failure(state, 0, typed, error)
        raise error

    if type(current) is not bool:
        fail("the current classical mode must be a Boolean.")
    word = args.strip()
    if word not in {"on", "off"}:
        fail("syntax: `classical on` or `classical off`.", TacticSyntaxError)
    enabled = word == "on"
    if trace is not None:
        if state is None:
            fail("tracing a mode change needs the current proof state.")
        trace.success(state, 0, typed, state)
    return enabled


def logic_banner(classical: bool) -> str:
    if type(classical) is not bool:
        raise TypeError("classical mode must be a Boolean")
    return (
        "Logic: PA + DNE (classical on)"
        if classical
        else "Logic: intuitionistic PA (classical off)"
    )


def hint(
    state: ProofState,
    *,
    max_checks: int = 64,
) -> tuple[str, str | None]:
    """Suggest one deterministic, supported move without mutating the state.

    ``found`` means the command is applicable, not that it completes the
    theorem. ``none`` means no immediate primitive was found. ``limit`` is an
    honest non-verdict when unresolved metas or the explicit scan budget stop
    inspection.
    """

    if type(max_checks) is not int or max_checks < 1:
        raise ValueError("hint max_checks must be a positive integer")
    goal = state.current()
    if goal is None:
        return "done", None
    target = apply_formula_subst(goal.target, state.subst)
    formulas = [target] + [
        apply_formula_subst(formula, state.subst)
        for _, formula in goal.context
    ]
    if any(metas_in_formula(formula, state.subst) for formula in formulas):
        return "limit", None

    for name, formula in goal.context:
        if formula == target:
            return "found", f"exact {name}"
    if type(target) is Eq and target.left == target.right:
        return "found", "refl"
    if type(target) is Imp:
        return "found", f"intro {_fresh_visible_name('h', goal)}"
    if type(target) is And:
        return "found", "split"
    if type(target) is Or:
        return "found", "left"
    if type(target) is Exists:
        zero_instance = instantiate_formula(target.body, Zero())
        if type(zero_instance) is Eq and zero_instance.left == zero_instance.right:
            return "found", "exists 0"

    checked = 0
    for name, raw_formula in goal.context:
        formula = apply_formula_subst(raw_formula, state.subst)
        if type(formula) is not Eq:
            continue
        for reverse in (False, True):
            checked += 1
            if checked > max_checks:
                return "limit", None
            try:
                rewrite_formula(target, formula, reverse=reverse)
            except (RewriteError, TypeError):
                continue
            arrow = "<- " if reverse else ""
            return "found", f"rewrite {arrow}{name}"
    for name in ("PA3", "PA4", "PA5", "PA6"):
        checked += 1
        if checked > max_checks:
            return "limit", None
        try:
            equation, _ = _axiom_equation(name, target, False)
            rewrite_formula(target, equation)
        except (TacticError, RewriteError, TypeError):
            continue
        return "found", f"rewrite {name}"
    if type(target) is Forall:
        return "found", f"induction {_fresh_visible_name('n', goal)}"
    return "none", None


def checked_final(
    state: ProofState,
    original_target: Formula,
    *,
    classical: bool = False,
    trace: TraceLogger | None = None,
) -> Proof:
    """Check QED against the session owner's original target.

    The original is an explicit argument on purpose: a buggy tactic can return
    an entirely new ``ProofState``, frozen fields and all.  The UI/session owns
    this argument and never obtains it back from the untrusted tactic result.
    """

    if state.goals:
        raise InvalidProof(f"{len(state.goals)} goal(s) are still open.")
    try:
        certificate = final_certificate(state)
    except RecursionError:
        raise InvalidProof(
            "certificate finalization exceeded the host recursion limit."
        ) from None
    if certificate is None:
        raise InvalidProof("the partial certificate still contains a hole or term metavariable.")
    if state.target != original_target:
        raise InvalidProof("the proof state no longer carries the session's original goal.")
    if type(classical) is not bool:
        raise InvalidProof("the session's classical mode is not a Boolean.")
    checker = check_classical if classical else check
    if not checker((), certificate, original_target):
        raise InvalidProof("the independent kernel rejected the certificate for the stated goal.")
    if trace is not None:
        try:
            certificate_size = proof_size(certificate)
        except RecursionError:
            raise InvalidProof(
                "certificate finalization exceeded the host recursion limit."
            ) from None
        trace.footer(
            qed=True,
            theorem=original_target,
            proof_size=certificate_size,
            names=state.variables,
        )
    return certificate


_TACTICS: dict[str, Tactic] = {
    "intro": intro,
    "specialize": specialize,
    "forall_elim": forall_elim,
    "induction": induction,
    "apply": apply_,
    "split": split,
    "left": left,
    "right": right,
    "cases": cases,
    "exfalso": exfalso,
    "exists": exists_,
    "refl": refl,
    "symm": symm,
    "trans": trans,
    "congr": congr,
    "exact": exact,
    "assumption": assumption,
    "rewrite": rewrite,
    "simp": simp,
    "undo": undo,
}
TACTIC_NAMES = tuple(_TACTICS)


def apply_tactic(
    state: ProofState,
    tactic: str,
    args: str = "",
    *,
    trace: TraceLogger | None = None,
    classical: bool = False,
) -> ProofState:
    """Dispatch one tactic and wire both success and failure trace records."""

    typed = f"{tactic} {args}".strip()
    function = _TACTICS.get(tactic)
    if function is None:
        error = TacticSyntaxError(
            f"unknown tactic {tactic!r}; available: {', '.join(TACTIC_NAMES)}."
        )
        if trace is not None:
            trace.failure(state, 0, typed, error)
        raise error
    try:
        result = (
            apply_(state, args, classical=classical)
            if tactic == "apply"
            else function(state, args)
        )
    except TacticError as error:
        if trace is not None:
            trace.failure(state, 0, typed, error)
        raise
    if trace is not None:
        trace.success(state, 0, typed, result)
    return result


def final_proof_size(
    state: ProofState,
    original_target: Formula,
    *,
    classical: bool = False,
) -> int:
    certificate = checked_final(state, original_target, classical=classical)
    return proof_size(certificate)


__all__ = [
    "TacticError",
    "TacticSyntaxError",
    "TacticLimit",
    "InvalidProof",
    "Tactic",
    "TACTIC_NAMES",
    "MAX_USE_CERTIFICATE_NODES",
    "MAX_USE_PARTIAL_NODES",
    "MAX_USE_PROOF_DEPTH",
    "intro",
    "specialize",
    "forall_elim",
    "induction",
    "apply_",
    "split",
    "left",
    "right",
    "cases",
    "exfalso",
    "exists_",
    "refl",
    "symm",
    "trans",
    "congr",
    "exact",
    "assumption",
    "rewrite",
    "simp",
    "undo",
    "set_classical_mode",
    "logic_banner",
    "hint",
    "use_checked",
    "apply_tactic",
    "checked_final",
    "final_proof_size",
]
