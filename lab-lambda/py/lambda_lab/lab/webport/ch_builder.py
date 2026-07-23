"""Interactive Curry-Howard proof builder — browser port.

A faithful, pure-stdlib port of ``lambda_lab/lab/curry_howard/builder.py``:

* :class:`Goal` — context of named hypotheses + STLC target type,
* :class:`PartialTerm` — partial λ-term with holes ``?₀, ?₁, …``,
* :class:`ProofState` — goal list + current term + history (for undo).

Operational tactics (a smaller set than the encyclopedia):

* ``intro [name]``  — introduce the hypothesis of an implication,
* ``exact <term>``  — close the goal with a term,
* ``apply <term>``  — apply a function, opening subgoals for its arguments,
* ``assumption``    — close the goal with a hypothesis from the context,
* ``refine <term>`` — alias for ``exact`` (holes not supported yet),
* ``undo``          — revert the last step.

All operations are *pure* — they return a new ``ProofState`` or raise
:class:`TacticError` carrying a message key + format parameters, which the
``ch`` dispatcher resolves to English text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from lambda_lab.lab.lc import App, Lam, Term, Var, pretty
from lambda_lab.lab.parser import ParseError, parse

from .ch_stlc import (
    Arrow,
    STLCTypeError,
    Type,
    find_inhabitant,
    infer,
    pretty_type,
    substitute,
    unify,
)


def _accepts(ty: Type, target: Type) -> Optional[Dict[str, Type]]:
    """``{}`` when the types agree verbatim; else their MGU when one exists.

    Goal atoms (P, Q, …) are rigid constants while a term's principal type
    carries fresh variables (α, β, …), so unification here is exactly the
    check "the goal is an instance of the term's type". Without this,
    ``exact λp q. p`` fails against ``P → Q → P`` — including the very terms
    that ``hint`` itself suggests (mirrors proof_builder._goal_match).
    """
    if pretty_type(ty) == pretty_type(target):
        return {}
    return unify(ty, target)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TacticError(Exception):
    """Tactic application error — carries a message key + parameters."""

    def __init__(self, message_key: str, **format_args: object) -> None:
        super().__init__(message_key)
        self.message_key = message_key
        self.format_args = format_args


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Goal:
    """A single goal: context of named hypotheses + target type."""

    context: Tuple[Tuple[str, Type], ...]
    target: Type

    @property
    def context_dict(self) -> Dict[str, Type]:
        return dict(self.context)


@dataclass(frozen=True)
class PartialTerm:
    """A partial term with holes ``?n``.

    Holes are represented as ``Var("?n")`` nodes; ``holes`` tracks the open
    hole indices and ``next_hole`` the next fresh index. The user-facing
    rendering shows ``?₀, ?₁, …`` (subscripts).
    """

    root: Term
    holes: Tuple[int, ...]
    next_hole: int

    @classmethod
    def initial(cls) -> "PartialTerm":
        return cls(root=Var("?0"), holes=(0,), next_hole=1)

    def pretty(self) -> str:
        return _pretty_with_subscripts(self.root)


def _hole_var(idx: int) -> Var:
    return Var(f"?{idx}")


def _is_hole(t: Term) -> Optional[int]:
    if isinstance(t, Var) and t.name.startswith("?"):
        try:
            return int(t.name[1:])
        except ValueError:
            return None
    return None


def _replace_hole(t: Term, idx: int, new: Term) -> Term:
    """Replace occurrences of ``?idx`` in ``t`` with ``new`` (recursively)."""
    h = _is_hole(t)
    if h == idx:
        return new
    if isinstance(t, Var):
        return t
    if isinstance(t, Lam):
        return Lam(t.param, _replace_hole(t.body, idx, new))
    if isinstance(t, App):
        return App(_replace_hole(t.fn, idx, new), _replace_hole(t.arg, idx, new))
    return t


_SUB = "₀₁₂₃₄₅₆₇₈₉"


def _to_subscript(n: int) -> str:
    return "".join(_SUB[int(d)] for d in str(n))


def _pretty_with_subscripts(t: Term) -> str:
    """Pretty-print with holes rendered as ``?₀, ?₁, …``."""
    rendered = pretty(t)
    return re.sub(r"\?(\d+)", lambda m: f"?{_to_subscript(int(m.group(1)))}", rendered)


@dataclass(frozen=True)
class Step:
    """History entry — enables undo."""

    tactic: str
    args: str
    state_before: "ProofState"


@dataclass(frozen=True)
class ProofState:
    goals: Tuple[Goal, ...]
    partial: PartialTerm
    history: Tuple[Step, ...] = field(default_factory=tuple)

    def is_done(self) -> bool:
        return not self.goals

    def current(self) -> Optional[Goal]:
        return self.goals[0] if self.goals else None

    def partial_str(self) -> str:
        return self.partial.pretty()

    def final_term(self) -> Optional[Term]:
        """When every goal is closed, return the hole-free term."""
        if self.goals:
            return None
        if _has_hole(self.partial.root):
            return None
        return self.partial.root


def _has_hole(t: Term) -> bool:
    if _is_hole(t) is not None:
        return True
    if isinstance(t, Var):
        return False
    if isinstance(t, Lam):
        return _has_hole(t.body)
    if isinstance(t, App):
        return _has_hole(t.fn) or _has_hole(t.arg)
    return False


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def start(target: Type) -> ProofState:
    goal = Goal(context=(), target=target)
    return ProofState(goals=(goal,), partial=PartialTerm.initial(), history=())


# ---------------------------------------------------------------------------
# Variable-name helper
# ---------------------------------------------------------------------------


def _suggest_name(used: set) -> str:
    for n in ("p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"):
        if n not in used:
            return n
    i = 0
    while f"h{i}" in used:
        i += 1
    return f"h{i}"


# ---------------------------------------------------------------------------
# Atomic tactics
# ---------------------------------------------------------------------------


def intro(state: ProofState, name: Optional[str] = None) -> ProofState:
    goal = state.current()
    if goal is None:
        raise TacticError("ch.build.no_more_goals")
    if not isinstance(goal.target, Arrow):
        raise TacticError("ch.build.goal_not_implication", target=pretty_type(goal.target))
    used = set(n for n, _ in goal.context)
    name = name or _suggest_name(used)
    if name in used:
        # The user supplied a colliding name — generate a fresh one.
        name = _suggest_name(used | {name})
    new_goal = Goal(
        context=goal.context + ((name, goal.target.src),),
        target=goal.target.dst,
    )
    # Replace the current hole with `fun name => ?new`.
    cur_hole = _first_hole_in(state.partial.root)
    if cur_hole is None:
        raise TacticError("ch.build.no_more_goals")
    new_idx = state.partial.next_hole
    body = Lam(name, _hole_var(new_idx))
    new_root = _replace_hole(state.partial.root, cur_hole, body)
    new_partial = PartialTerm(
        root=new_root,
        holes=tuple(h for h in state.partial.holes if h != cur_hole) + (new_idx,),
        next_hole=new_idx + 1,
    )
    return ProofState(
        goals=(new_goal,) + state.goals[1:],
        partial=new_partial,
        history=state.history + (Step("intro", name, state),),
    )


def exact(state: ProofState, term_src: str) -> ProofState:
    if not term_src.strip():
        raise TacticError("ch.build.exact_needs_arg")
    goal = state.current()
    if goal is None:
        raise TacticError("ch.build.no_more_goals")
    try:
        term = parse(term_src)
    except ParseError as e:
        raise TacticError("ch.build.tactic_error", error=str(e))
    env = goal.context_dict
    # Early catch: a lone variable outside the context = unknown_term.
    if isinstance(term, Var) and term.name not in env:
        raise TacticError("ch.build.unknown_term", term=term.name)
    try:
        ty = infer(term, env=env)
    except STLCTypeError:
        raise TacticError(
            "ch.build.exact_type_mismatch",
            term=pretty(term),
            got="?",
            want=pretty_type(goal.target),
        )
    # Accept when the goal is an instance of the term's (principal) type.
    if _accepts(ty, goal.target) is None:
        raise TacticError(
            "ch.build.exact_type_mismatch",
            term=pretty(term),
            got=pretty_type(ty),
            want=pretty_type(goal.target),
        )
    cur_hole = _first_hole_in(state.partial.root)
    if cur_hole is None:
        raise TacticError("ch.build.no_more_goals")
    new_root = _replace_hole(state.partial.root, cur_hole, term)
    new_partial = PartialTerm(
        root=new_root,
        holes=tuple(h for h in state.partial.holes if h != cur_hole),
        next_hole=state.partial.next_hole,
    )
    return ProofState(
        goals=state.goals[1:],
        partial=new_partial,
        history=state.history + (Step("exact", term_src, state),),
    )


def assumption(state: ProofState) -> ProofState:
    goal = state.current()
    if goal is None:
        raise TacticError("ch.build.no_more_goals")
    for name, ty in goal.context:
        if _accepts(ty, goal.target) is not None:
            return exact(state, name)
    raise TacticError("ch.build.assumption_no_match", target=pretty_type(goal.target))


def apply_(state: ProofState, term_src: str) -> ProofState:
    """``apply f`` for ``f : A1 -> ... -> An -> goal`` → n new subgoals."""
    if not term_src.strip():
        raise TacticError("ch.build.apply_needs_arg")
    goal = state.current()
    if goal is None:
        raise TacticError("ch.build.no_more_goals")
    try:
        term = parse(term_src)
    except ParseError as e:
        raise TacticError("ch.build.tactic_error", error=str(e))
    env = goal.context_dict
    try:
        ty = infer(term, env=env)
    except STLCTypeError:
        if isinstance(term, Var) and term.name not in env:
            raise TacticError("ch.build.unknown_term", term=term.name)
        raise TacticError("ch.build.tactic_error", error="cannot infer type")
    # Decompose ty into a chain of arrows.
    args: List[Type] = []
    ret = ty
    while isinstance(ret, Arrow):
        args.append(ret.src)
        ret = ret.dst
    theta = _accepts(ret, goal.target)
    if theta is None:
        # Result type doesn't match — try treating it as a plain exact.
        if _accepts(ty, goal.target) is not None:
            return exact(state, term_src)
        raise TacticError(
            "ch.build.exact_type_mismatch",
            term=pretty(term),
            got=pretty_type(ty),
            want=pretty_type(goal.target),
        )
    if not args:
        # Zero arity — effectively exact.
        return exact(state, term_src)
    # Instantiate the argument types with what unification learned, so the
    # subgoals are as concrete as the goal made them (e.g. apply λp q. p on
    # goal P yields subgoals P and β — not α and β).
    args = [substitute(a, theta) for a in args]
    cur_hole = _first_hole_in(state.partial.root)
    if cur_hole is None:
        raise TacticError("ch.build.no_more_goals")
    # Build the application chain f ?h1 ?h2 ...
    next_idx = state.partial.next_hole
    new_holes: List[int] = []
    new_term: Term = term
    for _ in args:
        new_term = App(new_term, _hole_var(next_idx))
        new_holes.append(next_idx)
        next_idx += 1
    new_root = _replace_hole(state.partial.root, cur_hole, new_term)
    # One new goal per argument, left to right.
    new_goals = tuple(Goal(context=goal.context, target=a) for a in args)
    new_partial = PartialTerm(
        root=new_root,
        holes=tuple(h for h in state.partial.holes if h != cur_hole) + tuple(new_holes),
        next_hole=next_idx,
    )
    return ProofState(
        goals=new_goals + state.goals[1:],
        partial=new_partial,
        history=state.history + (Step("apply", term_src, state),),
    )


def refine(state: ProofState, term_src: str) -> ProofState:
    """Simplified ``refine`` — an alias for ``exact`` here.

    Full refine with ``?_`` placeholders would need a hole-aware parser;
    a term containing ``?`` raises a more explicit error.
    """
    if not term_src.strip():
        raise TacticError("ch.build.refine_needs_arg")
    if "?" in term_src:
        raise TacticError(
            "ch.build.tactic_error",
            error="refine with explicit holes is not supported in the builder yet",
        )
    return exact(state, term_src)


def undo(state: ProofState) -> ProofState:
    if not state.history:
        raise TacticError("ch.build.history_empty")
    return state.history[-1].state_before


def hint(state: ProofState) -> Optional[str]:
    """Suggest the next move by searching for an inhabitant of the goal.

    Returns a term string usable as ``exact <term>``, or ``None``.
    """
    goal = state.current()
    if goal is None:
        return None
    # First the trivial `assumption`.
    target_pp = pretty_type(goal.target)
    for name, ty in goal.context:
        if pretty_type(ty) == target_pp:
            return name
    # Then proof search in the empty context.
    term = find_inhabitant(goal.target)
    if term is None:
        return None
    return pretty(term)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def apply_tactic(state: ProofState, tactic: str, args: str) -> ProofState:
    """Main textual dispatcher."""
    args = (args or "").strip()
    if tactic == "intro":
        name = args.split()[0] if args else None
        return intro(state, name)
    if tactic == "intros":
        # Greedily introduce while the goal is an implication.
        new_state = state
        names = args.split() if args else []
        idx = 0
        while True:
            current_goal = new_state.current()
            if current_goal is None or not isinstance(current_goal.target, Arrow):
                break
            n = names[idx] if idx < len(names) else None
            new_state = intro(new_state, n)
            idx += 1
        return new_state
    if tactic == "exact":
        return exact(state, args)
    if tactic == "apply":
        return apply_(state, args)
    if tactic == "assumption":
        return assumption(state)
    if tactic == "refine":
        return refine(state, args)
    raise TacticError("ch.build.unknown_tactic", name=tactic)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first_hole_in(t: Term) -> Optional[int]:
    h = _is_hole(t)
    if h is not None:
        return h
    if isinstance(t, Var):
        return None
    if isinstance(t, Lam):
        return _first_hole_in(t.body)
    if isinstance(t, App):
        f = _first_hole_in(t.fn)
        if f is not None:
            return f
        return _first_hole_in(t.arg)
    return None
