"""Small, transactional combinators that turn tactics into a tactic language.

The children of a tactical may take several successful steps before a later
child fails.  That is safe because ``ProofState`` is immutable: we publish only
the final state, and collapse its child histories into one outer transaction.
Thus one command is one ``undo``, including ``t1; t2`` and ``all_goals t``.

These are Python combinators, not the surface-syntax parser (which belongs to
the interactive UI).  A child is consequently already assembled and receives
the empty argument string.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from ..kernel.formulas import Formula
from ..kernel.proofs import Proof
from ..kernel.terms import Term
from .state import (
    Goal,
    Hole,
    ProofState,
    Step,
    apply_subst_everywhere,
    holes_in,
    invariants_ok,
    record_step,
    replace_hole,
)
from .tactics import Tactic, TacticError, TacticLimit, TacticSyntaxError


_REPEAT_LIMIT = 256


def _state(value: object) -> ProofState:
    """Defend every public combinator before indexing goals or holes."""

    try:
        valid = (
            type(value) is ProofState
            and isinstance(value.partial, Proof)
            and isinstance(value.target, Formula)
            and all(type(goal) is Goal for goal in value.goals)
            and all(type(step) is Step for step in value.history)
            and all(type(name) is str for name in value.variables)
            and all(
                type(meta_id) is int
                and meta_id >= 0
                and isinstance(term, Term)
                for meta_id, term in value.subst.items()
            )
            and invariants_ok(value)
        )
    except (AttributeError, TypeError, ValueError, RecursionError):
        valid = False
    if not valid:
        raise TacticError("a tactical needs a valid exact ProofState.")
    return value  # type: ignore[return-value]


def _tactic(value: object, owner: str) -> Tactic:
    if not callable(value):
        raise TacticError(f"`{owner}` needs a tactic.")
    return value


def _no_args(name: str, args: str) -> None:
    if type(args) is not str or args.strip():
        raise TacticError(
            f"`{name}` is already assembled and takes no further arguments."
        )


def _run(child: Tactic, state: ProofState) -> ProofState:
    """Run a child, validate its contract, and hide its private history.

    A primitive normally appends a history entry.  Nested tacticals may append
    more than one.  The enclosing tactical must retain the *exact* old prefix
    and later replace all those entries by its own single transaction.
    """

    state = _state(state)
    result = child(state, "")
    try:
        result = _state(result)
    except TacticError:
        raise TacticError("a child tactic returned an invalid proof state.") from None
    if result.target != state.target or result.variables != state.variables:
        raise TacticError("a child tactic changed the original theorem.")
    old_count = len(state.history)
    if result.history[:old_count] != state.history or len(result.history) < old_count:
        raise TacticError("a child tactic changed earlier proof history.")
    for meta_id, term in state.subst.items():
        if result.subst.get(meta_id) != term:
            raise TacticError("a child tactic discarded an existing substitution.")
    return replace(result, history=state.history)


def _finish(before: ProofState, after: ProofState, name: str, args: str = "") -> ProofState:
    """Publish a compound success as exactly one undo transaction."""

    before = _state(before)
    try:
        after = _state(after)
    except TacticError:
        raise TacticError("a tactical produced an invalid proof state.") from None
    return record_step(before, replace(after, history=before.history), name, args)


def _focus_once(state: ProofState, index: int, child: Tactic) -> ProofState:
    """Run ``child`` on one zero-based goal, then splice its proof back.

    Merely moving a goal to the front would be unsound: goals correspond, in
    order, to holes at particular positions in the partial certificate.  We
    instead give the child a one-hole certificate and replace precisely that
    hole on success.  Its substitution is then propagated proof-wide.
    """

    state = _state(state)
    if index < 0 or index >= len(state.goals):
        raise TacticError(f"goal {index + 1} does not exist.")
    hole_id = holes_in(state.partial)[index]
    local = ProofState(
        goals=(state.goals[index],),
        partial_certificate_with_holes=Hole(hole_id),
        history=state.history,
        target=state.target,
        subst=state.subst,
        variables=state.variables,
    )
    result = _run(child, local)
    merged = replace(
        state,
        goals=state.goals[:index] + result.goals + state.goals[index + 1 :],
        partial_certificate_with_holes=replace_hole(
            state.partial, hole_id, result.partial
        ),
        subst=result.subst,
    )
    merged = apply_subst_everywhere(merged, result.subst)
    if not invariants_ok(merged):
        raise TacticError("a focused tactic returned mismatched goals and holes.")
    return merged


def then(left: Tactic, right: Tactic) -> Tactic:
    """``left; right``: apply ``right`` to every goal made by ``left``."""

    left, right = _tactic(left, "then"), _tactic(right, "then")

    def combined(state: ProofState, args: str = "") -> ProofState:
        _no_args("then", args)
        state = _state(state)
        # Isolating the old focus ensures even a compound left child cannot
        # accidentally touch the pre-existing tail goals.
        old_tail_count = max(0, len(state.goals) - 1)
        work = _focus_once(state, 0, left)
        made = len(work.goals) - old_tail_count
        cursor = 0
        for _ in range(made):
            before_count = len(work.goals)
            work = _focus_once(work, cursor, right)
            cursor += len(work.goals) - (before_count - 1)
        return _finish(state, work, "then")

    return combined


def orelse(left: Tactic, right: Tactic) -> Tactic:
    """Try ``left``; on ``TacticError``, run ``right`` on the exact snapshot."""

    left, right = _tactic(left, "orelse"), _tactic(right, "orelse")

    def combined(state: ProofState, args: str = "") -> ProofState:
        _no_args("orelse", args)
        try:
            result = _run(left, state)
        except TacticSyntaxError:
            raise
        except TacticError as left_error:
            try:
                result = _run(right, state)
            except TacticSyntaxError:
                raise
            except TacticError as right_error:
                limit = next(
                    (
                        error
                        for error in (left_error, right_error)
                        if isinstance(error, TacticLimit)
                    ),
                    None,
                )
                if limit is not None:
                    raise TacticLimit(
                        f"every tactic in `orelse` failed; {limit}"
                    ) from None
                raise
        return _finish(state, result, "orelse")

    return combined


def repeat(tactic: Tactic) -> Tactic:
    """Repeat until failure/no progress; cycles and runaway tactics terminate."""

    tactic = _tactic(tactic, "repeat")

    def combined(state: ProofState, args: str = "") -> ProofState:
        _no_args("repeat", args)
        work = _state(state)
        # Ignore history/certificate growth when detecting a logical cycle:
        # ``repeat symm`` must not grow ``EqSym(EqSym(...))`` forever.
        seen = [(work.goals, tuple(sorted(work.subst.items())))]
        for _ in range(_REPEAT_LIMIT):
            try:
                next_state = _run(tactic, work)
            except (TacticLimit, TacticSyntaxError):
                raise
            except TacticError:
                break
            key = (next_state.goals, tuple(sorted(next_state.subst.items())))
            work = next_state
            if key in seen:
                break
            seen.append(key)
        else:
            raise TacticLimit("`repeat` exceeded its 256-step termination guard.")
        return _finish(state, work, "repeat")

    return combined


def first(tactics: Iterable[Tactic]) -> Tactic:
    """Try candidates left-to-right, restoring the snapshot after each failure."""

    try:
        choices = tuple(tactics)
    except TypeError:
        raise TacticError("`first` needs a non-empty list of tactics.") from None
    if not choices:
        raise TacticError("`first` needs a non-empty list of tactics.")
    choices = tuple(_tactic(choice, "first") for choice in choices)

    def combined(state: ProofState, args: str = "") -> ProofState:
        _no_args("first", args)
        last_error: TacticError | None = None
        limit_error: TacticLimit | None = None
        for choice in choices:
            try:
                return _finish(state, _run(choice, state), "first")
            except TacticSyntaxError:
                raise
            except TacticError as error:
                last_error = error
                if isinstance(error, TacticLimit) and limit_error is None:
                    limit_error = error
        assert last_error is not None
        if limit_error is not None:
            raise TacticLimit(
                f"every tactic in `first` failed; {limit_error}"
            ) from None
        raise TacticError(f"every tactic in `first` failed; {last_error}") from None

    return combined


def all_goals(tactic: Tactic) -> Tactic:
    """Apply once to each goal present at entry, never to generated subgoals."""

    tactic = _tactic(tactic, "all_goals")

    def combined(state: ProofState, args: str = "") -> ProofState:
        _no_args("all_goals", args)
        state = _state(state)
        work, cursor = state, 0
        for _ in range(len(state.goals)):
            before_count = len(work.goals)
            work = _focus_once(work, cursor, tactic)
            cursor += len(work.goals) - (before_count - 1)
        return _finish(state, work, "all_goals")

    return combined


def focus(number: int, tactic: Tactic) -> Tactic:
    """Apply a tactic to the one-based goal ``number``, preserving its position."""

    if type(number) is not int or number < 1:
        raise TacticError("`focus` needs a positive one-based goal number.")
    tactic = _tactic(tactic, "focus")

    def combined(state: ProofState, args: str = "") -> ProofState:
        _no_args("focus", args)
        return _finish(state, _focus_once(state, number - 1, tactic), "focus", str(number))

    return combined


__all__ = ["then", "orelse", "repeat", "first", "all_goals", "focus"]
