"""Untrusted polynomial proposals that preserve repeated compound terms.

All algebraic reasoning here is proposal generation.  The small connecting
equalities, their uses, and the final generalized equation still execute as
ordinary native surface commands, with independent full replay by the caller.
"""
from __future__ import annotations

from collections import Counter

from arithmetic_search import _add, _quote
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.terms import Add, Mul, Succ, Var, pretty_term
from polynomial_chunks import ChunkPlan, NoPlan, _PlanBudget, _Planner, _abstraction, _nodes, _walk


MAX_ATOMS = 3
MAX_REWRITES = 8
MAX_REWRITE_CANDIDATES = 48


def _rewrite_first(equation, source, replacement):
    changed = False

    def walk(term):
        nonlocal changed
        if not changed and term == source:
            changed = True
            return replacement
        if type(term) is Succ:
            return Succ(walk(term.term))
        if type(term) in (Add, Mul):
            return type(term)(walk(term.left), walk(term.right))
        return term

    result = Eq(walk(equation.left), walk(equation.right))
    return result if changed else None


def _outside(term, atom):
    if term == atom:
        return
    yield term
    if type(term) is Succ:
        yield from _outside(term.term, atom)
    elif type(term) in (Add, Mul):
        yield from _outside(term.left, atom)
        yield from _outside(term.right, atom)


def _operations(equation, atom, budget):
    protected = set(_walk(atom))
    atom_poly = budget.polynomial(atom)
    seen, proposals = set(), []
    terms = (*_outside(equation.left, atom), *_outside(equation.right, atom))
    for source in terms:
        budget.tick()
        if source in seen or source in protected or type(source) not in (Add, Mul):
            continue
        seen.add(source)
        source_poly = budget.polynomial(source)
        # Expose the square of a composite additive factor without expanding
        # the factor. This is an instance of a small universal monomial law.
        if type(source) is Mul and source.left == source.right and type(source.left) is Mul:
            first, second = source.left.left, source.left.right
            if any(type(term) is Add for term in (*_walk(first), *_walk(second))):
                replacement = Mul(Mul(first, first), Mul(second, second))
                proposals.append((1, -_nodes(source), source, replacement, "expose a square's factors"))
        # Collect a single monomial only; preserve the selected compound atom.
        if len(source_poly) == 1:
            normal = _quote(source_poly)
            if normal != source:
                proposals.append((2, -_nodes(source), source, normal, "align a monomial around the compound atom"))
        # A small positive remainder can expose an existing compound term.
        # For example, (a+b)^2 becomes (a^2+2ab)+b^2 when that first sum is
        # already repeated elsewhere in the goal. No theorem names are used.
        difference = _add(source_poly, atom_poly, -1)
        if difference and len(difference) <= 2 and all(c > 0 for c in difference.values()):
            replacement = Add(atom, _quote(difference))
            if replacement != source:
                old_count = sum(term == atom for term in _walk(source))
                priority = 0 if not old_count else 3
                if len(source_poly) <= 4 and _nodes(source) + _nodes(replacement) <= 128:
                    proposals.append((priority, -_nodes(source), source, replacement,
                                      "expose a repeated compound term plus a small remainder"))
        if len(proposals) >= MAX_REWRITE_CANDIDATES:
            break
    proposals.sort(key=lambda proposal: proposal[:2])
    return tuple(proposals[:MAX_REWRITE_CANDIDATES])


def atom_polynomial_chunk_plan(equation, variables, context=(), *, should_stop=None):
    """A bounded atom-preserving plan, or None; no proof authority is added."""
    if type(equation) is not Eq:
        return None
    try:
        budget = _PlanBudget(should_stop)
        if budget.polynomial(equation.left) != budget.polynomial(equation.right):
            return None
        if len(variables) > 32 or any(term.index >= len(variables)
                for endpoint in (equation.left, equation.right) for term in _walk(endpoint)
                if type(term) is Var):
            return None
        first, second = Counter(_walk(equation.left)), Counter(_walk(equation.right))
        counts = first + second
        atoms = [term for term, count in counts.items()
                 if type(term) is Add and count >= 2 and _nodes(term) >= 5]
        atoms.sort(key=lambda term: (not (first[term] and second[term]), -_nodes(term), -counts[term]))
        for atom in atoms[:MAX_ATOMS]:
            planner = _Planner(variables, context, budget)
            current = equation
            used_forms = {current}
            local_rules = {}
            reasons = []
            for step in range(MAX_REWRITES + 1):
                budget.tick()
                generalized = _abstraction(current, budget)
                if step and generalized is not None and len(budget.polynomial(generalized[0].left)) <= 4:
                    planner.ring(current)
                    return ChunkPlan(tuple(planner.commands),
                        "Preserve a repeated compound term and check only small connecting arithmetic equalities.",
                        tuple(planner.obligations), {"polynomial_analyses": budget.analyses,
                            "control_work_units": budget.work, "script_bytes": planner.script_bytes,
                            "rewrites": step, "atom": pretty_term(atom, list(variables)),
                            "rewrite_reasons": reasons}, strategy="polynomial_atoms_v1")
                if step == MAX_REWRITES:
                    break
                for _, _, source, replacement, reason in _operations(current, atom, budget):
                    following = _rewrite_first(current, source, replacement)
                    if following is None or following in used_forms:
                        continue
                    if budget.polynomial(source) != budget.polynomial(replacement):
                        continue
                    pair = Eq(source, replacement)
                    lemma = local_rules.get(pair)
                    if lemma is None:
                        lemma = planner.fresh()
                        planner.emit("have " + lemma + " : " + planner.formula(pair))
                        # Congruence is useful when the unchanged compound atom
                        # is a sibling of a tiny coefficient reassociation.
                        planner.solve(pair)
                        local_rules[pair] = lemma
                    planner.emit("rewrite " + lemma)
                    used_forms.add(following)
                    current = following
                    reasons.append(reason)
                    break
                else:
                    break
        return None
    except (NoPlan, ValueError):
        return None
