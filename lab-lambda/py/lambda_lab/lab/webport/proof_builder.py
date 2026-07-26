"""The sound interactive proof engine shared by ``prove`` and ``ch build``.

Rewritten per the 2026-07-24 audit. The four soundness pillars:

* P0.1 — :func:`checked_final` is the ONLY way to finish: the completed term
  must be hole-free, closed, typable, and its principal type must instantiate
  (one-way) to the ORIGINAL rigid target. No QED without it.
* P0.2 — types come from the :mod:`stlc_types` kernel: parsed atoms are rigid
  ``Atom`` nodes; only inference ``MetaVar``\\ s unify.
* P0.3 — :class:`ProofState` carries a proof-wide substitution. Every
  successful ``exact``/``apply``/``assumption`` composes its unifier into it
  and the composed substitution is applied to EVERY remaining goal and
  context, so sibling goals share constraints visibly.
* P0.4 — every tactic term is rejected if it mentions a variable not bound by
  the goal's context (no smuggled free variables).

Plus P1.5: binder names are validated with the λ-parser's own identifier
rule, surplus arguments are errors, one user-level ``intros`` is one history
transaction, and history records the tactic the user actually typed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

from lambda_lab.lab.lc import App, Lam, Term, Var, free_vars, pretty
from lambda_lab.lab.parser import ParseError, parse

from .stlc_types import (
    Arrow,
    MetaVar,
    STLCTypeError,
    Subst,
    Type,
    apply_subst,
    find_inhabitant_ctx,
    infer_with_subst,
    metas_in,
    peel_arrows,
    pretty_type,
    pretty_types,
    target_is_instance_of,
    unify,
    walk,
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TacticError(Exception):
    """A tactic could not be applied; the message is final English text.
    The proof state is guaranteed unchanged when this is raised."""


class InvalidProof(Exception):
    """checked_final refused the completed proof; the session must survive."""


# ---------------------------------------------------------------------------
# Identifier rule — shared with the λ-term parser (audit P1.5)
# ---------------------------------------------------------------------------


def is_valid_binder(name: str) -> bool:
    if not name or name.startswith("?"):
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    return all(c.isalnum() or c in ("_", "'") for c in name[1:])


# ---------------------------------------------------------------------------
# Proof-state data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Goal:
    context: Tuple[Tuple[str, Type], ...]
    target: Type

    @property
    def context_dict(self) -> Dict[str, Type]:
        return dict(self.context)


@dataclass(frozen=True)
class PartialTerm:
    root: Term
    holes: Tuple[int, ...]
    next_hole: int

    @staticmethod
    def initial() -> "PartialTerm":
        return PartialTerm(root=_hole_var(0), holes=(0,), next_hole=1)


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
    h = _is_hole(t)
    if h == idx:
        return new
    if isinstance(t, Lam):
        return Lam(t.param, _replace_hole(t.body, idx, new))
    if isinstance(t, App):
        return App(_replace_hole(t.fn, idx, new), _replace_hole(t.arg, idx, new))
    return t


def holes_in(t: Term) -> Tuple[int, ...]:
    out: List[int] = []

    def go(x: Term) -> None:
        h = _is_hole(x)
        if h is not None:
            out.append(h)
        elif isinstance(x, Lam):
            go(x.body)
        elif isinstance(x, App):
            go(x.fn)
            go(x.arg)

    go(t)
    return tuple(out)


_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _to_subscript(n: int) -> str:
    return str(n).translate(_SUB)


def _pretty_with_subscripts(t: Term) -> str:
    """Pretty-print with holes shown as ``?₀, ?₁, …``."""
    import re
    s = pretty(t, rename=False)
    return re.sub(r"\?(\d+)", lambda m: "?" + _to_subscript(int(m.group(1))), s)


@dataclass(frozen=True)
class Step:
    tactic: str          # exactly what the user typed (audit P1.5)
    arg: str
    state_before: "ProofState"


@dataclass(frozen=True)
class ProofState:
    goals: Tuple[Goal, ...]
    partial: PartialTerm
    history: Tuple[Step, ...]
    target: Type                      # the ORIGINAL parsed (rigid) target
    subst: Dict[int, Type] = field(default_factory=dict)

    def is_done(self) -> bool:
        return not self.goals

    def current(self) -> Optional[Goal]:
        return self.goals[0] if self.goals else None

    def final_term(self) -> Optional[Term]:
        if self.goals or holes_in(self.partial.root):
            return None
        return self.partial.root

    def partial_str(self) -> str:
        return _pretty_with_subscripts(self.partial.root)


def start(target: Type) -> ProofState:
    return ProofState(
        goals=(Goal(context=(), target=target),),
        partial=PartialTerm.initial(),
        history=(),
        target=target,
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _suggest_name(used: set) -> str:
    # The teaching convention (slides, book, cookbook): p, q, r, … for
    # hypotheses; h0, h1, … once the preferred letters run out.
    for c in "pqrstuvwxyz":
        if c not in used:
            return c
    i = 0
    while f"h{i}" in used:
        i += 1
    return f"h{i}"


def _apply_everywhere(state: ProofState, s: Subst) -> ProofState:
    """Apply a composed substitution to every goal target and context type —
    the P0.3 propagation that keeps sibling goals consistent AND visible."""
    goals = tuple(
        Goal(
            context=tuple((n, apply_subst(t, s)) for n, t in g.context),
            target=apply_subst(g.target, s),
        )
        for g in state.goals
    )
    return replace(state, goals=goals, subst=dict(s))


def _parse_tactic_term(src: str) -> Term:
    try:
        return parse(src)
    except ParseError as e:
        raise TacticError(f"cannot parse the term: {e}")


def _reject_unknown_free(term: Term, goal: Goal) -> None:
    """P0.4: every free variable of a tactic term must be a hypothesis."""
    unknown = free_vars(term) - set(goal.context_dict)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise TacticError(
            f"unknown term variable(s): {names} — a proof may only use the "
            f"hypotheses in the current context (see the Context line).")


def _no_args(tac: str, args: str) -> None:
    if args.strip():
        raise TacticError(f"`{tac}` takes no arguments (got {args.strip()!r}).")


def _close_goal_with(state: ProofState, term: Term, s2: Subst,
                     tactic: str, arg: str) -> ProofState:
    """Replace the current hole by ``term``, drop the goal, propagate ``s2``."""
    if not state.partial.holes:
        raise TacticError("no open goal.")
    hole = state.partial.holes[0]
    new_partial = PartialTerm(
        root=_replace_hole(state.partial.root, hole, term),
        holes=state.partial.holes[1:],
        next_hole=state.partial.next_hole,
    )
    new_state = replace(
        state,
        goals=state.goals[1:],
        partial=new_partial,
        history=state.history + (Step(tactic, arg, state),),
    )
    return _apply_everywhere(new_state, s2)


# ---------------------------------------------------------------------------
# Tactics
# ---------------------------------------------------------------------------


def _intro_once(state: ProofState, name: Optional[str]) -> ProofState:
    goal = state.current()
    if goal is None:
        raise TacticError("no open goal.")
    target = apply_subst(goal.target, state.subst)
    if not isinstance(target, Arrow):
        raise TacticError(
            f"the goal is `{pretty_type(target)}` — not an implication, "
            f"so there is nothing to intro.")
    used = {n for n, _ in goal.context}
    if name is not None:
        if not is_valid_binder(name):
            raise TacticError(
                f"invalid hypothesis name {name!r} — use a λ-identifier "
                f"(letter or _, then letters/digits/_/'), not starting with '?'.")
        if name in used:
            raise TacticError(
                f"the name {name!r} is already used in this context — pick another.")
    else:
        name = _suggest_name(used)
    new_goal = Goal(context=goal.context + ((name, target.src),), target=target.dst)
    hole = state.partial.holes[0]
    new_idx = state.partial.next_hole
    new_partial = PartialTerm(
        root=_replace_hole(state.partial.root, hole, Lam(name, _hole_var(new_idx))),
        holes=(new_idx,) + state.partial.holes[1:],
        next_hole=new_idx + 1,
    )
    return replace(state, goals=(new_goal,) + state.goals[1:], partial=new_partial)


def intro(state: ProofState, args: str = "") -> ProofState:
    names = args.split()
    if len(names) > 1:
        raise TacticError(
            f"`intro` takes at most one name (got {len(names)}); "
            f"use `intros {' '.join(names)}` to introduce several.")
    new_state = _intro_once(state, names[0] if names else None)
    return replace(new_state, history=state.history + (Step("intro", args, state),))


def intros(state: ProofState, args: str = "") -> ProofState:
    names = args.split()
    scratch = state
    if names:
        for n in names:
            scratch = _intro_once(scratch, n)
    else:
        progressed = False
        while True:
            goal = scratch.current()
            if goal is None:
                break
            if not isinstance(apply_subst(goal.target, scratch.subst), Arrow):
                break
            scratch = _intro_once(scratch, None)
            progressed = True
        if not progressed:
            raise TacticError(
                "`intros` made no progress — the goal is not an implication.")
    # ONE history transaction for the whole intros (audit P1.5)
    return replace(scratch, history=state.history + (Step("intros", args, state),))


def _infer_in_goal(state: ProofState, term: Term, goal: Goal) -> Tuple[Type, Subst]:
    env = {n: apply_subst(t, state.subst) for n, t in goal.context}
    try:
        return infer_with_subst(term, env, state.subst)
    except STLCTypeError as e:
        raise TacticError(f"the term has no simple type here: {e}")


def exact(state: ProofState, args: str, *, tactic: str = "exact") -> ProofState:
    if not args.strip():
        raise TacticError(f"`{tactic}` needs a term, e.g. `{tactic} h` or "
                          f"`{tactic} \\p. p`.")
    goal = state.current()
    if goal is None:
        raise TacticError("no open goal.")
    term = _parse_tactic_term(args)
    _reject_unknown_free(term, goal)
    ty, s1 = _infer_in_goal(state, term, goal)
    target = apply_subst(goal.target, s1)
    s2 = unify(ty, target, s1)
    if s2 is None:
        got, want = pretty_types([apply_subst(ty, s1), target])
        raise TacticError(f"term `{pretty(term)}` has type `{got}` but the "
                          f"goal is `{want}`.")
    return _close_goal_with(state, term, s2, tactic, args)


def assumption(state: ProofState, args: str = "") -> ProofState:
    _no_args("assumption", args)
    goal = state.current()
    if goal is None:
        raise TacticError("no open goal.")
    target = apply_subst(goal.target, state.subst)
    for name, hyp in goal.context:
        s2 = unify(apply_subst(hyp, state.subst), target, state.subst)
        if s2 is not None:
            return _close_goal_with(state, Var(name), s2, "assumption", "")
    raise TacticError(
        f"no hypothesis matches the goal `{pretty_type(target)}` — "
        f"see the Context line.")


def apply_(state: ProofState, args: str) -> ProofState:
    if not args.strip():
        raise TacticError("`apply` needs a term, e.g. `apply f`.")
    goal = state.current()
    if goal is None:
        raise TacticError("no open goal.")
    term = _parse_tactic_term(args)
    _reject_unknown_free(term, goal)
    ty, s1 = _infer_in_goal(state, term, goal)
    ty = apply_subst(ty, s1)
    if isinstance(walk(ty, s1), MetaVar):
        raise TacticError(
            "the type of that term is not determined yet — close another goal "
            "first, or use `exact` with a full term.")
    arrow_args, ret = peel_arrows(ty)
    target = apply_subst(goal.target, s1)
    s2 = unify(ret, target, s1)
    if s2 is None:
        # maybe the whole type matches the goal — plain exact
        s3 = unify(ty, target, s1)
        if s3 is not None:
            return _close_goal_with(state, term, s3, "apply", args)
        got, want = pretty_types([ty, target])
        raise TacticError(f"term `{pretty(term)}` has type `{got}`; neither it "
                          f"nor its result matches the goal `{want}`.")
    if not arrow_args:
        return _close_goal_with(state, term, s2, "apply", args)
    hole = state.partial.holes[0]
    next_idx = state.partial.next_hole
    new_holes: List[int] = []
    new_term: Term = term
    for _ in arrow_args:
        new_term = App(new_term, _hole_var(next_idx))
        new_holes.append(next_idx)
        next_idx += 1
    new_partial = PartialTerm(
        root=_replace_hole(state.partial.root, hole, new_term),
        holes=tuple(new_holes) + state.partial.holes[1:],
        next_hole=next_idx,
    )
    # sibling goals keep the SAME MetaVar ids — s2 propagation links them
    new_goals = tuple(Goal(context=goal.context, target=a) for a in arrow_args)
    new_state = replace(
        state,
        goals=new_goals + state.goals[1:],
        partial=new_partial,
        history=state.history + (Step("apply", args, state),),
    )
    return _apply_everywhere(new_state, s2)


def refine(state: ProofState, args: str) -> ProofState:
    """An honest alias for ``exact`` (audit P1.4): explicit ``?_`` holes are
    not supported in this builder; the help text says exactly that."""
    if "?" in args:
        raise TacticError(
            "`refine` here is an alias for `exact` and does not support "
            "explicit `?_` holes — use `apply` to open argument subgoals.")
    return exact(state, args, tactic="refine")


def undo(state: ProofState, args: str = "") -> ProofState:
    _no_args("undo", args)
    if not state.history:
        raise TacticError("nothing to undo.")
    return state.history[-1].state_before


# ---------------------------------------------------------------------------
# Hint (audit P1.3): context-aware, honest about limits
# ---------------------------------------------------------------------------


def hint(state: ProofState) -> Tuple[str, Optional[str]]:
    """Returns ``(status, suggestion)``:

    * ``("done", None)`` — all goals closed;
    * ``("assumption", name)`` — a hypothesis closes the goal;
    * ``("intro", None)`` — no inhabitant found yet but the goal is an
      implication: introduce and look again;
    * ``("exact", term_text)`` — a found inhabitant using the context;
    * ``("limit", None)`` — search hit its depth limit: no verdict;
    * ``("none", None)`` — no proof exists in the implicational fragment;
    * ``("meta", None)`` — the goal still contains undetermined types.
    """
    goal = state.current()
    if goal is None:
        return ("done", None)
    target = apply_subst(goal.target, state.subst)
    ctx = tuple((n, apply_subst(t, state.subst)) for n, t in goal.context)
    if metas_in(target) or any(metas_in(t) for _, t in ctx):
        return ("meta", None)
    # 1. a hypothesis that closes the goal outright
    for name, hyp in ctx:
        if hyp == target:
            return ("assumption", name)
    # 2. full search WITH the context
    status, term = find_inhabitant_ctx(target, ctx, max_depth=10)
    if status == "found" and term is not None:
        # sanity: the suggestion must pass the same checker exact uses
        try:
            exact(state, pretty(term))
        except TacticError:
            return ("limit", None)
        return ("exact", pretty(term))
    if status == "limit":
        return ("limit", None)
    if isinstance(target, Arrow):
        return ("intro", None)
    return ("none", None)


# ---------------------------------------------------------------------------
# The trusted finish (audit P0.1)
# ---------------------------------------------------------------------------


def checked_final(state: ProofState) -> Tuple[Term, str]:
    """Validate the completed proof; returns ``(term, principal_pretty)``.

    Raises :class:`InvalidProof` (leaving the session intact) when the term
    has holes, is open, is untypable, or does not prove the ORIGINAL target.
    """
    if state.goals:
        raise InvalidProof(f"{len(state.goals)} goal(s) still open.")
    final = state.final_term()
    if final is None:
        raise InvalidProof("internal error: goals are closed but the proof "
                           "term still contains holes.")
    fv = free_vars(final)
    if fv:
        raise InvalidProof(
            f"the proof term is open — free variable(s): {', '.join(sorted(fv))}.")
    try:
        principal, _ = infer_with_subst(final, {}, {})
    except STLCTypeError as e:
        raise InvalidProof(f"the completed term is not typable: {e}")
    if not target_is_instance_of(principal, state.target):
        got, want = pretty_types([principal, state.target])
        raise InvalidProof(
            f"the completed term proves `{got}`, which does not instantiate "
            f"to the stated goal `{want}`.")
    return final, pretty_type(principal)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_TACTICS = {
    "intro": intro,
    "intros": intros,
    "exact": exact,
    "apply": apply_,
    "assumption": assumption,
    "refine": refine,
    "undo": undo,
}

TACTIC_NAMES = tuple(_TACTICS)


def apply_tactic(state: ProofState, tactic: str, args: str) -> ProofState:
    fn = _TACTICS.get(tactic)
    if fn is None:
        raise TacticError(
            f"unknown tactic {tactic!r} — available: {', '.join(TACTIC_NAMES)}; "
            f"`hint` suggests a move, `?` shows the state, `qed` finishes, "
            f"`abort` leaves.")
    return fn(state, args)


# ---------------------------------------------------------------------------
# Test-oracle helpers (audit "mandatory soundness oracle")
# ---------------------------------------------------------------------------


def invariants_ok(state: ProofState) -> bool:
    """len(goals) == len(holes) and the recorded holes are exactly the holes
    occurring in the partial term."""
    if len(state.goals) != len(state.partial.holes):
        return False
    return set(state.partial.holes) == set(holes_in(state.partial.root))
