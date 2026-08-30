"""Small, bounded proof search for ``auto [depth]``.

Search is deliberately outside the trusted kernel.  It explores immutable
``ProofState`` values, remembers only a winning sequence of ordinary tactic
commands, then replays that sequence through the public dispatcher.  Failed
branches therefore cannot leak state, and emitted traces remain a linear,
replayable proof rather than a transcript that silently jumps backwards.

``depth`` is proof-tree depth, not the total number of commands.  Sibling goals
receive the same remaining allowance; this is why a split into two easy goals
does not cost twice as much as one.  ``max_nodes`` is a separate browser-safety
bound and an exhausted bound is reported as ``limit``, never as impossibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import Iterator, Literal

from ..kernel.checker import check, check_classical
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.terms import Add, Mul, Succ, Term, Var
from .proof_reduction import ProofReductionError, compile_local_cuts
from .state import ProofState, final_certificate, holes_in, invariants_ok
from .trace import TraceLogger


SearchStatus = Literal["found", "none", "limit"]
_INTERNAL_DEPTH_LIMIT = 256


@dataclass(frozen=True, slots=True)
class Command:
    """One primitive command in a winning plan."""

    tactic: str
    args: str = ""


@dataclass(frozen=True, slots=True)
class SearchResult:
    """An honest search outcome and the amount of explored work."""

    status: SearchStatus
    commands: tuple[Command, ...]
    checked: int


def _fresh_name(base: str, state: ProofState) -> str:
    goal = state.current()
    if goal is None:
        return base
    used = set(goal.variables) | {name for name, _ in goal.context}
    if base not in used:
        return base
    index = 1
    while f"{base}{index}" in used:
        index += 1
    return f"{base}{index}"


def _term_mentions(term: Term, index: int, depth: int) -> bool:
    if type(term) is Var:
        return term.index == index + depth
    if type(term) is Succ:
        return _term_mentions(term.term, index, depth)
    if type(term) in (Add, Mul):
        return _term_mentions(term.left, index, depth) or _term_mentions(
            term.right, index, depth
        )
    return False


def _formula_mentions(formula: Formula, index: int, depth: int = 0) -> bool:
    """Whether an outer free variable occurs, without confusing binders."""

    if type(formula) is Eq:
        return _term_mentions(formula.left, index, depth) or _term_mentions(
            formula.right, index, depth
        )
    if type(formula) in (Imp, And, Or):
        return _formula_mentions(formula.left, index, depth) or _formula_mentions(
            formula.right, index, depth
        )
    if type(formula) in (Forall, Exists):
        return _formula_mentions(formula.body, index, depth + 1)
    return False


def _equational_hypotheses(state: ProofState) -> tuple[str, ...]:
    """Context names whose leading-forall body is an equation."""

    goal = state.current()
    if goal is None:
        return ()
    result: list[str] = []
    for name, formula in goal.context:
        while type(formula) is Forall:
            formula = formula.body
        if type(formula) is Eq:
            result.append(name)
    return tuple(result)


def _contextual_simp_commands(state: ProofState) -> Iterator[Command]:
    """Try selected local equations, including decreasing reverse directions.

    Pairs are enough for the nested induction hypotheses in the first PA
    ladder.  Larger explicit sets remain available to users, but omitting them
    here keeps bounded search genuinely small.
    """

    names = _equational_hypotheses(state)
    for size in range(1, min(2, len(names)) + 1):
        for chosen in combinations(names, size):
            for reverse_flags in product((False, True), repeat=size):
                shown = [
                    ("<- " if reverse else "") + name
                    for name, reverse in zip(chosen, reverse_flags)
                ]
                yield Command("simp", f"[{', '.join(shown)}]")


def _candidates(state: ProofState, classical: bool) -> Iterator[Command]:
    """Yield a small deterministic menu; failures are normal backtracking."""

    goal = state.current()
    if goal is None:
        return
    target = goal.target

    # Cheap closing/simplifying moves precede branching ones.
    yield Command("simp")
    yield from _contextual_simp_commands(state)
    yield Command("assumption")
    if type(target) is Eq:
        yield Command("refl")

    # Applying a local theorem is often better than decomposing the goal.
    for name, _ in goal.context:
        yield Command("apply", name)

    if type(target) is Imp:
        yield Command("intro", _fresh_name("h", state))
    elif type(target) is Forall:
        # Expose variables first.  On the resulting equation, newest-first
        # named induction naturally chooses the recursive argument of + and ·.
        yield Command("intro", _fresh_name("n", state))
        yield Command("induction", _fresh_name("n", state))
    elif type(target) is And:
        yield Command("split")
    elif type(target) is Or:
        yield Command("left")
        yield Command("right")
    elif type(target) is Exists:
        yield Command("exists", "0")
        yield Command("exists", "?")
    elif type(target) is Eq:
        yield Command("congr")
        # A named context variable is a legal induction target.  Ignore
        # variables absent from the formula: induction on them only loops.
        for index, name in enumerate(goal.variables):
            if _formula_mentions(target, index):
                yield Command("induction", name)

    # Eliminating a structured hypothesis is a last, branching resort.
    for name, formula in goal.context:
        if type(formula) in (And, Or, Exists, Bot):
            yield Command("cases", name)
    if type(target) is Bot:
        for name, _ in goal.context:
            yield Command("apply", name)

    if classical:
        # Prefer constructive structure first even in classical sessions.
        # DNE remains an ordinary visible proof constant, offered only with
        # exact external authorization; the leaf checker uses the same mode.
        yield Command("apply", "DNE")

    # The two non-equational PA axioms are useful through ordinary apply.
    yield Command("apply", "PA1")
    yield Command("apply", "PA2")


class _Planner:
    def __init__(self, max_nodes: int, classical: bool) -> None:
        self.max_nodes = max_nodes
        self.classical = classical
        self.checked = 0
        self.hit_limit = False

    def _at_node_limit(self) -> bool:
        if self.checked >= self.max_nodes:
            self.hit_limit = True
            return True
        return False

    def _advisory_qed(self, state: ProofState) -> bool:
        """Reject a dead certificate leaf and keep backtracking.

        This uses the state's cached target only as a search heuristic.  It is
        not QED: the session owner must still call ``checked_final`` with its
        separately retained original statement and exact mode Boolean.
        """

        certificate = final_certificate(state)
        if certificate is None:
            return False
        try:
            certificate = compile_local_cuts(certificate)
        except ProofReductionError:
            return False
        checker = check_classical if self.classical else check
        return checker((), certificate, state.target)

    def _try(self, state: ProofState, command: Command) -> ProofState | None:
        if self._at_node_limit():
            return None
        self.checked += 1
        # Lazy import avoids making the tactic dispatcher and search module a
        # circular import when the UI later exposes `auto` as a command.
        from .tactics import (
            TacticError,
            TacticLimit,
            TacticSyntaxError,
            apply_tactic,
        )

        try:
            result = apply_tactic(
                state,
                command.tactic,
                command.args,
                classical=self.classical,
            )
        except TacticSyntaxError:
            raise
        except TacticLimit:
            self.hit_limit = True
            return None
        except TacticError:
            return None
        if result.goals == state.goals and dict(result.subst) == dict(state.subst):
            return None
        return result

    def solutions_one(
        self, state: ProofState, depth: int
    ) -> Iterator[tuple[ProofState, tuple[Command, ...]]]:
        """Enumerate ways to solve the focus while preserving its old tail."""

        if depth <= 0:
            self.hit_limit = True
            return
        before_holes = holes_in(state.partial)
        if not before_holes:
            if not state.goals and self._advisory_qed(state):
                yield state, ()
            return
        boundary = before_holes[1] if len(before_holes) > 1 else None

        for command in _candidates(state, self.classical):
            after = self._try(state, command)
            if after is None:
                if self._at_node_limit():
                    return
                continue
            for completed, child_plan in self.solutions_until(
                after, boundary, depth - 1
            ):
                yield completed, (command,) + child_plan
            if self._at_node_limit():
                return

    def solutions_until(
        self,
        state: ProofState,
        boundary: int | None,
        depth: int,
    ) -> Iterator[tuple[ProofState, tuple[Command, ...]]]:
        """Solve generated siblings, backtracking into every earlier sibling.

        A simple loop over the first child solution is incomplete when siblings
        share a metavariable: a later sibling may refute that first assignment.
        Recursive enumeration lets Python resume the earlier child's candidate
        iterator and try its next proof, exactly like a tiny logic engine.
        """

        current_holes = holes_in(state.partial)
        at_boundary = (
            not current_holes
            if boundary is None
            else bool(current_holes and current_holes[0] == boundary)
        )
        if at_boundary:
            if boundary is not None or self._advisory_qed(state):
                yield state, ()
            return
        for first_solved, first_plan in self.solutions_one(state, depth):
            for all_solved, rest_plan in self.solutions_until(
                first_solved, boundary, depth
            ):
                yield all_solved, first_plan + rest_plan
            if self._at_node_limit():
                return


def search(
    state: ProofState,
    max_depth: int = 5,
    *,
    max_nodes: int = 5_000,
    classical: bool = False,
) -> SearchResult:
    """Find a complete primitive plan without mutating ``state`` or tracing.

    ``none`` means this finite candidate tree was exhausted. ``limit`` means a
    depth or node boundary was reached, so failure is explicitly a non-verdict.
    """

    if type(state) is not ProofState or not invariants_ok(state):
        raise TypeError("auto search needs a valid exact ProofState")
    if type(max_depth) is not int or max_depth < 1:
        raise ValueError("auto depth must be a positive integer")
    if type(max_nodes) is not int or max_nodes < 1:
        raise ValueError("auto max_nodes must be a positive integer")
    if type(classical) is not bool:
        raise ValueError("classical mode must be a Boolean")
    planner = _Planner(max_nodes, classical)
    if not state.goals:
        status: SearchStatus = "found" if planner._advisory_qed(state) else "none"
        return SearchResult(status, (), 0)
    effective_depth = min(max_depth, _INTERNAL_DEPTH_LIMIT)
    if max_depth > _INTERNAL_DEPTH_LIMIT:
        planner.hit_limit = True
    try:
        for _, commands in planner.solutions_until(state, None, effective_depth):
            return SearchResult("found", commands, planner.checked)
    except RecursionError:
        # Defensive fallback for an unusually deep host Python stack.  Search
        # exhaustion is a non-verdict and must never escape as a raw crash.
        planner.hit_limit = True
    status = "limit" if planner.hit_limit else "none"
    return SearchResult(status, (), planner.checked)


def _parse_depth(args: str) -> int:
    if type(args) is not str:
        from .tactics import TacticSyntaxError

        raise TacticSyntaxError("syntax: `auto [positive-depth]`.")
    pieces = args.split()
    if not pieces:
        return 5
    if len(pieces) != 1 or not pieces[0].isdigit() or int(pieces[0]) < 1:
        from .tactics import TacticSyntaxError

        raise TacticSyntaxError("syntax: `auto [positive-depth]`.")
    return int(pieces[0])


def auto(
    state: ProofState,
    args: str = "",
    *,
    trace: TraceLogger | None = None,
    classical: bool = False,
    max_nodes: int = 5_000,
) -> ProofState:
    """Search, then replay only the winning primitive commands.

    The returned state may be submitted to ``checked_final`` by the session
    owner.  Search never calls QED itself because it does not own the original
    theorem statement or the classical-mode authority.
    """

    from .tactics import TacticError, TacticLimit, TacticSyntaxError, apply_tactic

    typed_input = f"auto {args}".strip()
    try:
        depth = _parse_depth(args)
        result = search(
            state,
            depth,
            max_nodes=max_nodes,
            classical=classical,
        )
    except (TacticError, TypeError, ValueError) as exc:
        error = exc if isinstance(exc, TacticError) else TacticError(str(exc))
        if trace is not None and type(state) is ProofState:
            trace.failure(state, 0, typed_input, error)
        raise error from None
    typed = f"auto {depth}"
    if result.status != "found":
        message = (
            f"auto reached its depth/node limit after {result.checked} checks."
            if result.status == "limit"
            else f"auto found no proof after {result.checked} checks."
        )
        error = (
            TacticLimit(message)
            if result.status == "limit"
            else TacticError(message)
        )
        if trace is not None:
            trace.failure(state, 0, typed, error)
        raise error

    if not result.commands:
        if trace is not None:
            trace.success(state, 0, typed, state)
        return state
    replayed = state
    try:
        for command in result.commands:
            replayed = apply_tactic(
                replayed,
                command.tactic,
                command.args,
                trace=trace,
                classical=classical,
            )
    except TacticSyntaxError as exc:  # pragma: no cover - defensive guard
        raise TacticSyntaxError(f"auto's winning plan did not replay: {exc}") from None
    except TacticLimit as exc:  # pragma: no cover - defensive determinism guard
        raise TacticLimit(f"auto's winning plan did not replay: {exc}") from None
    except TacticError as exc:  # pragma: no cover - defensive determinism guard
        raise TacticError(f"auto's winning plan did not replay: {exc}") from None
    return replayed


__all__ = [
    "SearchStatus",
    "Command",
    "SearchResult",
    "search",
    "auto",
]
