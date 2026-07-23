"""Untyped lambda-calculus core: AST, capture-avoiding substitution and beta reduction."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterator, List, Optional, Set, Tuple, Union

sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Lam:
    param: str
    body: "Term"


@dataclass(frozen=True)
class App:
    fn: "Term"
    arg: "Term"


Term = Union[Var, Lam, App]


def _alpha_rename_unique(t: Term) -> Term:
    """Return an alpha-equivalent term with unique printed binder names."""
    used: Set[str] = set(free_vars(t))

    def fresh_name(hint: str) -> str:
        candidate = hint
        primes = 0
        while candidate in used and primes < 3:
            candidate += "'"
            primes += 1
        if candidate in used:
            stem = candidate
            n = 2
            while f"{stem}{n}" in used:
                n += 1
            candidate = f"{stem}{n}"
        return candidate

    def go(node: Term, env: dict[str, str]) -> Term:
        if isinstance(node, Var):
            return Var(env.get(node.name, node.name))
        if isinstance(node, Lam):
            new_param = fresh_name(node.param)
            used.add(new_param)
            return Lam(new_param, go(node.body, {**env, node.param: new_param}))
        if isinstance(node, App):
            return App(go(node.fn, env), go(node.arg, env))
        raise TypeError(f"Unknown term: {node!r}")

    return go(t, {})


def pretty(t: Term, *, lam: str = "λ", rename: bool = True) -> str:
    """Pretty-print with minimal parentheses."""
    if rename:
        t = _alpha_rename_unique(t)

    def go(node: Term, ctx: str) -> str:
        if isinstance(node, Var):
            return node.name
        if isinstance(node, Lam):
            params = [node.param]
            body: Term = node.body
            while isinstance(body, Lam):
                params.append(body.param)
                body = body.body
            text = f"{lam}{' '.join(params)}. {go(body, 'lam')}"
            return text if ctx == "top" else f"({text})"
        if isinstance(node, App):
            text = f"{go(node.fn, 'app-left')} {go(node.arg, 'app-right')}"
            return text if ctx in ("top", "lam", "app-left") else f"({text})"
        raise TypeError(f"Unknown term: {node!r}")

    return go(t, "top")


def show_ascii(t: Term) -> str:
    return pretty(t, lam="\\")


def free_vars(t: Term) -> Set[str]:
    if isinstance(t, Var):
        return {t.name}
    if isinstance(t, Lam):
        return free_vars(t.body) - {t.param}
    if isinstance(t, App):
        return free_vars(t.fn) | free_vars(t.arg)
    raise TypeError(f"Unknown term: {t!r}")


def all_vars(t: Term) -> Set[str]:
    if isinstance(t, Var):
        return {t.name}
    if isinstance(t, Lam):
        return {t.param} | all_vars(t.body)
    if isinstance(t, App):
        return all_vars(t.fn) | all_vars(t.arg)
    raise TypeError(f"Unknown term: {t!r}")


def term_size(t: Term, *, stop_after: Optional[int] = None) -> int:
    """Count AST nodes iteratively; optionally stop after a safety threshold."""
    count = 0
    stack = [t]
    while stack:
        node = stack.pop()
        count += 1
        if stop_after is not None and count > stop_after:
            return count
        if isinstance(node, Lam):
            stack.append(node.body)
        elif isinstance(node, App):
            stack.extend((node.fn, node.arg))
    return count


def _rename_bound(body: Term, old: str, new: str) -> Term:
    if isinstance(body, Var):
        return Var(new) if body.name == old else body
    if isinstance(body, App):
        return App(_rename_bound(body.fn, old, new), _rename_bound(body.arg, old, new))
    if isinstance(body, Lam):
        if body.param == old:
            return body
        return Lam(body.param, _rename_bound(body.body, old, new))
    raise TypeError(f"Unknown term: {body!r}")


def fresh(used: Set[str], hint: str = "x") -> str:
    base = hint.rstrip("0123456789'") or "x"
    i = 0
    while True:
        candidate = base if i == 0 and base not in used else f"{base}{i}"
        if candidate not in used:
            return candidate
        i += 1


def alpha_rename(lam: Lam, new_param: str) -> Lam:
    if new_param == lam.param:
        return lam
    used = all_vars(lam.body) | {lam.param}
    target = new_param if new_param not in used else fresh(used | {new_param}, new_param)
    return Lam(target, _rename_bound(lam.body, lam.param, target))


def subst(t: Term, var: str, repl: Term) -> Term:
    """Capture-avoiding substitution t[var := repl]."""
    if isinstance(t, Var):
        return repl if t.name == var else t
    if isinstance(t, App):
        return App(subst(t.fn, var, repl), subst(t.arg, var, repl))
    if isinstance(t, Lam):
        if t.param == var:
            return t
        if var not in free_vars(t.body):
            return t
        if t.param in free_vars(repl):
            used = all_vars(t.body) | all_vars(repl) | {var, t.param}
            renamed = alpha_rename(t, fresh(used, t.param))
            return Lam(renamed.param, subst(renamed.body, var, repl))
        return Lam(t.param, subst(t.body, var, repl))
    raise TypeError(f"Unknown term: {t!r}")


def _bound_index(name: str, binders: Tuple[str, ...]) -> Optional[int]:
    """De Bruijn index of ``name`` relative to the nearest enclosing binder."""
    for index, binder in enumerate(reversed(binders)):
        if name == binder:
            return index
    return None


def alpha_eq(a: Term, b: Term) -> bool:
    """True exactly when two terms differ only by bound-variable names.

    Binder stacks, rather than dictionaries keyed by variable name, are essential:
    dictionaries lose information when a binder shadows another binder.
    """

    def go(left: Term, right: Term, env_l: Tuple[str, ...], env_r: Tuple[str, ...]) -> bool:
        if isinstance(left, Var) and isinstance(right, Var):
            li = _bound_index(left.name, env_l)
            ri = _bound_index(right.name, env_r)
            if li is None or ri is None:
                return li is None and ri is None and left.name == right.name
            return li == ri
        if isinstance(left, App) and isinstance(right, App):
            return go(left.fn, right.fn, env_l, env_r) and go(left.arg, right.arg, env_l, env_r)
        if isinstance(left, Lam) and isinstance(right, Lam):
            return go(left.body, right.body, env_l + (left.param,), env_r + (right.param,))
        return False

    return go(a, b, (), ())


def is_redex(t: Term) -> bool:
    return isinstance(t, App) and isinstance(t.fn, Lam)


@dataclass(frozen=True)
class Step:
    before: Term
    after: Term
    rule: str
    redex_path: Tuple[int, ...]
    note: str = ""


@dataclass(frozen=True)
class ReductionResult:
    term: Term
    steps: int
    complete: bool
    reason: str = ""


def _find_outermost_redex(t: Term, path: Tuple[int, ...] = ()) -> Optional[Tuple[Term, Tuple[int, ...]]]:
    if is_redex(t):
        return t, path
    if isinstance(t, App):
        found = _find_outermost_redex(t.fn, path + (0,))
        if found is not None:
            return found
        return _find_outermost_redex(t.arg, path + (1,))
    if isinstance(t, Lam):
        return _find_outermost_redex(t.body, path + (0,))
    return None


def _find_head_redex(t: Term, path: Tuple[int, ...] = ()) -> Optional[Tuple[Term, Tuple[int, ...]]]:
    """Find the next normal-order redex needed for weak-head normalization."""
    if is_redex(t):
        return t, path
    if isinstance(t, App):
        return _find_head_redex(t.fn, path + (0,))
    # WHNF does not reduce under lambdas or inside arguments.
    return None


def _step_at(found: Optional[Tuple[Term, Tuple[int, ...]]]) -> Optional[Step]:
    if found is None:
        return None
    redex, path = found
    assert isinstance(redex, App) and isinstance(redex.fn, Lam)
    replacement = subst(redex.fn.body, redex.fn.param, redex.arg)
    return Step(
        before=redex,
        after=replacement,
        rule="β",
        redex_path=path,
        note=f"(λ{redex.fn.param}. _) _  →  _[{redex.fn.param} := _]",
    )


def beta_step(t: Term) -> Optional[Step]:
    return _step_at(_find_outermost_redex(t))


def whnf_step(t: Term) -> Optional[Step]:
    return _step_at(_find_head_redex(t))


def _apply_step(root: Term, path: Tuple[int, ...], patch: Term) -> Term:
    if not path:
        return patch
    head, *rest = path
    rest_tuple = tuple(rest)
    if isinstance(root, App):
        if head == 0:
            return App(_apply_step(root.fn, rest_tuple, patch), root.arg)
        if head == 1:
            return App(root.fn, _apply_step(root.arg, rest_tuple, patch))
    if isinstance(root, Lam) and head == 0:
        return Lam(root.param, _apply_step(root.body, rest_tuple, patch))
    raise IndexError(f"Bad path {path} for term {root!r}")


def trace(t: Term, *, max_steps: int = 200) -> List[Term]:
    out: List[Term] = [t]
    current = t
    for _ in range(max_steps):
        step = beta_step(current)
        if step is None:
            break
        current = _apply_step(current, step.redex_path, step.after)
        out.append(current)
    return out


def trace_steps(t: Term, *, max_steps: int = 200) -> Iterator[Step]:
    current = t
    for _ in range(max_steps):
        step = beta_step(current)
        if step is None:
            return
        next_term = _apply_step(current, step.redex_path, step.after)
        yield Step(current, next_term, step.rule, step.redex_path, step.note)
        current = next_term


def _reduce_checked(
    t: Term,
    step_fn,
    *,
    max_steps: int,
    max_nodes: Optional[int] = None,
) -> ReductionResult:
    current = t
    if max_nodes is not None and term_size(current, stop_after=max_nodes) > max_nodes:
        return ReductionResult(current, 0, False, "node-limit")
    steps = 0
    while steps < max_steps:
        step = step_fn(current)
        if step is None:
            return ReductionResult(current, steps, True)
        current = _apply_step(current, step.redex_path, step.after)
        steps += 1
        if max_nodes is not None and term_size(current, stop_after=max_nodes) > max_nodes:
            return ReductionResult(current, steps, False, "node-limit")
    # One non-mutating look-ahead distinguishes exact-bound completion from exhaustion.
    complete = step_fn(current) is None
    return ReductionResult(current, steps, complete, "" if complete else "step-limit")


def normalize_checked(
    t: Term, *, max_steps: int = 500, max_nodes: Optional[int] = None
) -> ReductionResult:
    return _reduce_checked(t, beta_step, max_steps=max_steps, max_nodes=max_nodes)


def whnf_checked(
    t: Term, *, max_steps: int = 500, max_nodes: Optional[int] = None
) -> ReductionResult:
    return _reduce_checked(t, whnf_step, max_steps=max_steps, max_nodes=max_nodes)


def normalize(t: Term, *, max_steps: int = 500) -> Term:
    """Compatibility wrapper; callers needing correctness must inspect complete."""
    return normalize_checked(t, max_steps=max_steps).term
