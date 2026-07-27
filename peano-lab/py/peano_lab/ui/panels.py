"""Plain-text proof panels for the browser terminal.

The UI deliberately has no authority over proofs.  These helpers only render
immutable engine values, using the same canonical formula renderer as JSONL
traces.  Output contains no ANSI escapes or other terminal control sequences,
which keeps it safe for xterm, copied transcripts, and browser tests alike.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..engine.proof_reduction import LocalHave, LocalSuffices
from ..engine.state import (
    Hole,
    MetaVar,
    ProofState,
    apply_formula_subst,
    apply_proof_subst,
    metas_in_formula,
    metas_in_proof,
)
from ..engine.trace import render_goal
from ..kernel.formulas import Formula
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
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
    Proof,
)
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero, pretty_term


NL = "\r\n"
MAX_CERTIFICATE_CHARS = 8_000
MAX_CERTIFICATE_DEPTH = 128
MAX_CERTIFICATE_RENDER_NODES = 2_048


def _formula_text(
    formula: Formula,
    names: tuple[str, ...],
    meta_names: dict[int, str],
) -> str:
    """Reuse the trace canonicalizer, discarding its dummy sequent prefix."""

    class _FormulaGoal:
        context = ()
        target = formula
        variables = names

    rendered = render_goal(_FormulaGoal(), meta_names=meta_names)
    return rendered.split("⊢ ", 1)[1]


def _term_text(term: Term, names: tuple[str, ...], metas: dict[int, str]) -> str:
    """Canonical term text extended only with engine metavariables."""

    if type(term) is MetaVar:
        if term.id not in metas:
            metas[term.id] = f"?t{len(metas) + 1}"
        return metas[term.id]
    if type(term) is Var:
        return (
            names[term.index]
            if 0 <= term.index < len(names)
            else f"#{term.index}"
        )
    if type(term) is Zero:
        return "0"
    if type(term) is Succ:
        # Delegate rigid numerals and ordinary terms to the kernel printer.
        try:
            return pretty_term(term, list(names))
        except TypeError:
            return f"S {_term_text(term.term, names, metas)}"
    if type(term) in (Add, Mul):
        symbol = "+" if type(term) is Add else "·"
        return (
            f"({_term_text(term.left, names, metas)} {symbol} "
            f"{_term_text(term.right, names, metas)})"
        )
    return "<malformed-term>"


def render_certificate(
    proof: Proof,
    names: tuple[str, ...] = (),
    *,
    meta_names: Mapping[int, str] | None = None,
) -> str:
    """Render a partial proof as compact constructor notation.

    Kernel certificates intentionally carry de Bruijn indices rather than UI
    binder names.  Names such as ``h`` and ``n`` below are therefore display
    binders only; ``hyp[0]`` keeps the actual index visible.
    """

    aliases = dict(meta_names or {})
    holes: dict[int, str] = {}
    rendered_nodes = 0

    def fresh_name(base: str, local_names: tuple[str, ...]) -> str:
        if base not in local_names:
            return base
        suffix = 1
        while f"{base}{suffix}" in local_names:
            suffix += 1
        return f"{base}{suffix}"

    def formula(value: Formula, local_names: tuple[str, ...] = names) -> str:
        return _formula_text(value, local_names, aliases)

    def go(value: Proof, depth: int, local_names: tuple[str, ...]) -> str:
        nonlocal rendered_nodes
        rendered_nodes += 1
        if rendered_nodes > MAX_CERTIFICATE_RENDER_NODES:
            return "…"
        if depth > MAX_CERTIFICATE_DEPTH:
            return "…"
        if type(value) is Hole:
            if value.id not in holes:
                holes[value.id] = f"?g{len(holes) + 1}"
            return holes[value.id]
        if type(value) is Hyp:
            return f"hyp[{value.index}]"
        if type(value) is ImpIntro:
            return f"(λh. {go(value.body, depth + 1, local_names)})"
        if type(value) is ImpElim:
            return (
                f"apply({go(value.function, depth + 1, local_names)}, "
                f"{go(value.argument, depth + 1, local_names)})"
            )
        if type(value) is LocalHave:
            return (
                f"have[{formula(value.proposition, local_names)}]("
                f"{go(value.proof, depth + 1, local_names)}, "
                f"λh. {go(value.body, depth + 1, local_names)})"
            )
        if type(value) is LocalSuffices:
            return (
                f"suffices[{formula(value.proposition, local_names)}]("
                f"λh. {go(value.body, depth + 1, local_names)}, "
                f"{go(value.proof, depth + 1, local_names)})"
            )
        if type(value) is AndIntro:
            return (
                f"⟨{go(value.left, depth + 1, local_names)}, "
                f"{go(value.right, depth + 1, local_names)}⟩"
            )
        if type(value) is AndElimL:
            return f"and.left({go(value.pair, depth + 1, local_names)})"
        if type(value) is AndElimR:
            return f"and.right({go(value.pair, depth + 1, local_names)})"
        if type(value) is OrIntroL:
            return f"or.left({go(value.proof, depth + 1, local_names)})"
        if type(value) is OrIntroR:
            return f"or.right({go(value.proof, depth + 1, local_names)})"
        if type(value) is OrElim:
            return (
                f"cases({go(value.disjunction, depth + 1, local_names)}, "
                f"{go(value.left_case, depth + 1, local_names)}, "
                f"{go(value.right_case, depth + 1, local_names)})"
            )
        if type(value) is BotElim:
            return f"false.elim({go(value.absurdity, depth + 1, local_names)})"
        if type(value) is ForallIntro:
            binder = fresh_name("n", local_names)
            return (
                f"(Λ{binder}. "
                f"{go(value.body, depth + 1, (binder,) + local_names)})"
            )
        if type(value) is ForallElim:
            return (
                f"forall.elim({go(value.universal, depth + 1, local_names)}, "
                f"{_term_text(value.term, local_names, aliases)})"
            )
        if type(value) is ExistsIntro:
            return (
                f"⟨{_term_text(value.term, local_names, aliases)}, "
                f"{go(value.proof, depth + 1, local_names)}⟩∃"
            )
        if type(value) is ExistsElim:
            binder = fresh_name("w", local_names)
            return (
                f"exists.elim({go(value.existential, depth + 1, local_names)}, "
                f"Λ{binder}. {go(value.body, depth + 1, (binder,) + local_names)})"
            )
        if type(value) is EqRefl:
            return f"refl({_term_text(value.term, local_names, aliases)})"
        if type(value) is EqSym:
            return f"symm({go(value.proof, depth + 1, local_names)})"
        if type(value) is EqTrans:
            return (
                f"trans({go(value.first, depth + 1, local_names)}, "
                f"{go(value.second, depth + 1, local_names)})"
            )
        if type(value) is CongS:
            return f"congr.S({go(value.proof, depth + 1, local_names)})"
        if type(value) is CongAdd:
            return (
                f"congr.+({go(value.left, depth + 1, local_names)}, "
                f"{go(value.right, depth + 1, local_names)})"
            )
        if type(value) is CongMul:
            return (
                f"congr.·({go(value.left, depth + 1, local_names)}, "
                f"{go(value.right, depth + 1, local_names)})"
            )
        if type(value) is EqSubst:
            binder = fresh_name("z", local_names)
            motive_names = (binder,) + local_names
            return (
                f"subst[{formula(value.motive, motive_names)}]("
                f"{go(value.equation, depth + 1, local_names)}, "
                f"{go(value.body, depth + 1, local_names)})"
            )
        if type(value) is DNE:
            return f"DNE[{formula(value.proposition, local_names)}]"
        if type(value) is Axiom:
            return value.name
        if type(value) is Ind:
            binder = fresh_name("n", local_names)
            motive_names = (binder,) + local_names
            return (
                f"IND[{formula(value.motive, motive_names)}]("
                f"{go(value.base, depth + 1, local_names)}, "
                f"{go(value.step, depth + 1, local_names)})"
            )
        return "<malformed-certificate>"

    try:
        text = go(proof, 0, names)
    except (AttributeError, RecursionError, TypeError, ValueError):
        text = "<malformed-certificate>"
    if len(text) > MAX_CERTIFICATE_CHARS:
        return text[: MAX_CERTIFICATE_CHARS - 1] + "…"
    return text


def collect_meta_ids(state: ProofState) -> tuple[int, ...]:
    """Return live metavariables in deterministic display order."""

    formulas: list[Formula] = []
    for goal in state.goals:
        formulas.extend(formula for _, formula in goal.context)
        formulas.append(goal.target)
    meta_ids: list[int] = []
    for value in formulas:
        for meta_id in metas_in_formula(value, state.subst):
            if meta_id not in meta_ids:
                meta_ids.append(meta_id)
    for meta_id in metas_in_proof(state.partial, state.subst):
        if meta_id not in meta_ids:
            meta_ids.append(meta_id)
    return tuple(meta_ids)


def render_state(
    state: ProofState,
    *,
    meta_names: Mapping[int, str] | None = None,
) -> str:
    """Render every goal plus one proof-wide partial-certificate panel.

    A session may supply its persistent alias table so a surviving ``?t2``
    never changes name merely because ``?t1`` was solved in another goal.
    """

    aliases = dict(meta_names or {})
    for meta_id in collect_meta_ids(state):
        if meta_id not in aliases:
            aliases[meta_id] = f"?t{len(aliases) + 1}"

    rows: list[str] = []
    total = len(state.goals)
    if not total:
        rows.append("No open goals.")
    for index, goal in enumerate(state.goals, start=1):
        rows.append(f"Goal {index}/{total}")
        if goal.variables:
            rows.append("  Variables")
            for name in reversed(goal.variables):
                rows.append(f"    {name} : ℕ")
        rows.append("  Context")
        if goal.context:
            for name, raw_formula in reversed(goal.context):
                shown = apply_formula_subst(raw_formula, state.subst)
                rows.append(
                    f"    {name} : {_formula_text(shown, goal.variables, aliases)}"
                )
        else:
            rows.append("    (empty)")
        target = apply_formula_subst(goal.target, state.subst)
        rows.append("  Target")
        rows.append(f"    {_formula_text(target, goal.variables, aliases)}")
        if index != total:
            rows.append("")

    partial = apply_proof_subst(state.partial, state.subst)
    if rows:
        rows.append("")
    rows.append("Partial certificate")
    rows.append(f"  {render_certificate(partial, state.variables, meta_names=aliases)}")
    return NL.join(rows)


__all__ = ["NL", "collect_meta_ids", "render_certificate", "render_state"]
