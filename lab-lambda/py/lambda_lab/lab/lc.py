"""Rdzeń rachunku λ: AST, α-konwersja, podstawienie, β/η-redukcja.

Zaadaptowane z ``sources/lambda/book/lc_core.py`` z dodatkowym wsparciem dla:
- ładnego pretty-printingu z minimalną liczbą nawiasów,
- śladu redukcji z informacją o zastosowanej regule,
- „środowiska stałych” (np. TRUE/FALSE/0/SUCC).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Set, Tuple, Union

# Wiele redukcji Churcha tworzy głębokie drzewa aplikacji. Podnosimy limit rekurencji
# raz dla całej aplikacji, żeby użytkownik nigdy nie trafił na RecursionError przy
# tak „rachunkowych” termach jak `PLUS 2 3` czy `MULT 3 3`.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Pretty printing — minimal parentheses
# ---------------------------------------------------------------------------


def _alpha_rename_unique(t: Term) -> Term:
    """Zwraca α-równoważny term, w którym KAŻDA λ-bindowana zmienna ma
    unikalną nazwę względem każdego nadrzędnego wiązania i każdej zmiennej
    wolnej. Czysto wizualne — używane tylko do prettyprintu, AST przed/po
    redukcji jest niezmienione (β-redukcja i tak działa capture-avoiding).

    Polityka świeżości: do nazwy doklejamy kolejne ``'`` (prim).
    Po trzech primach dokładamy numer (``f'''2``), żeby uniknąć ciągów
    typu ``f'''''``.
    """
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

    def go(t: Term, env: dict[str, str]) -> Term:
        if isinstance(t, Var):
            return Var(env.get(t.name, t.name))
        if isinstance(t, Lam):
            new_param = fresh_name(t.param)
            used.add(new_param)
            new_env = {**env, t.param: new_param}
            return Lam(new_param, go(t.body, new_env))
        if isinstance(t, App):
            return App(go(t.fn, env), go(t.arg, env))
        raise TypeError(f"Unknown term: {t!r}")

    return go(t, {})


def pretty(t: Term, *, lam: str = "λ", rename: bool = True) -> str:
    """Wypisz term w notacji zwyczajowej: λx. x (y z).

    ``rename=True`` (domyślnie) wykonuje czysto wizualne α-przemianowanie
    do unikalnych nazw — dzięki czemu wynik typu ``λx f. λf'. x`` nie
    ma mylącego shadowingu (zamiast ``λx f. λf. x``).
    """
    if rename:
        t = _alpha_rename_unique(t)

    def go(t: Term, ctx: str) -> str:
        if isinstance(t, Var):
            return t.name
        if isinstance(t, Lam):
            params = [t.param]
            body: Term = t.body
            while isinstance(body, Lam):
                params.append(body.param)
                body = body.body
            s = f"{lam}{' '.join(params)}. {go(body, 'lam')}"
            return s if ctx == "top" else f"({s})"
        if isinstance(t, App):
            left = go(t.fn, "app-left")
            right = go(t.arg, "app-right")
            s = f"{left} {right}"
            return s if ctx in ("top", "lam", "app-left") else f"({s})"
        raise TypeError(f"Unknown term: {t!r}")

    return go(t, "top")


def show_ascii(t: Term) -> str:
    """Wypisz term w ASCII (z ``\\``)."""
    return pretty(t, lam="\\")


# ---------------------------------------------------------------------------
# Free / bound variables, α-renaming
# ---------------------------------------------------------------------------


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
            new_param = fresh(used, t.param)
            renamed = alpha_rename(t, new_param)
            return Lam(renamed.param, subst(renamed.body, var, repl))
        return Lam(t.param, subst(t.body, var, repl))
    raise TypeError(f"Unknown term: {t!r}")


def alpha_eq(a: Term, b: Term,
             env_ab: Optional[Dict[str, str]] = None,
             env_ba: Optional[Dict[str, str]] = None) -> bool:
    env_ab = env_ab or {}
    env_ba = env_ba or {}
    if isinstance(a, Var) and isinstance(b, Var):
        if a.name in env_ab:
            return env_ab[a.name] == b.name
        if b.name in env_ba:
            return False
        return a.name == b.name
    if isinstance(a, App) and isinstance(b, App):
        return alpha_eq(a.fn, b.fn, env_ab, env_ba) and alpha_eq(a.arg, b.arg, env_ab, env_ba)
    if isinstance(a, Lam) and isinstance(b, Lam):
        nab = dict(env_ab); nba = dict(env_ba)
        nab[a.param] = b.param
        nba[b.param] = a.param
        return alpha_eq(a.body, b.body, nab, nba)
    return False


# ---------------------------------------------------------------------------
# β / η redukcja
# ---------------------------------------------------------------------------


def is_redex(t: Term) -> bool:
    return isinstance(t, App) and isinstance(t.fn, Lam)


@dataclass(frozen=True)
class Step:
    """Jeden krok redukcji: przed → po, z opisem reguły i zaznaczoną ścieżką."""
    before: Term
    after: Term
    rule: str                 # "β", "η", "α"
    redex_path: Tuple[int, ...]
    note: str = ""


def _find_outermost_redex(t: Term, path: Tuple[int, ...] = ()) -> Optional[Tuple[Term, Tuple[int, ...]]]:
    """Znajdź najbardziej zewnętrzny, najbardziej lewy redeks (normal-order).

    Zwraca ``(redex, path)`` albo ``None``, jeżeli term jest w postaci normalnej.
    """
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


def beta_step(t: Term) -> Optional[Step]:
    """Jeden krok β-redukcji w strategii normal-order.

    ``Step.after`` zawiera tylko *podstawiony* fragment (co wstawiamy w ``redex_path``).
    Całkowite nowe drzewo otrzymuje się przez ``_apply_step(t, step.redex_path, step.after)``.
    """
    found = _find_outermost_redex(t)
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


def trace(t: Term, *, max_steps: int = 200) -> List[Term]:
    """Śledź kolejne postacie redukcji; zwraca listę termów łącznie z wejściowym."""
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
    """Generator szczegółowych kroków — do ładnej animacji."""
    current = t
    for _ in range(max_steps):
        step = beta_step(current)
        if step is None:
            return
        next_term = _apply_step(current, step.redex_path, step.after)
        yield Step(before=current, after=next_term,
                   rule=step.rule, redex_path=step.redex_path, note=step.note)
        current = next_term


def _apply_step(root: Term, path: Tuple[int, ...], patch: Term) -> Term:
    """Podstaw ``patch`` w ``root`` w punkcie opisanym przez ``path``."""
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


def normalize(t: Term, *, max_steps: int = 500) -> Term:
    """Zwróć postać normalną, jeżeli istnieje w zadanym limicie kroków."""
    for term in trace(t, max_steps=max_steps):
        last = term
    return last  # type: ignore[possibly-unbound]
