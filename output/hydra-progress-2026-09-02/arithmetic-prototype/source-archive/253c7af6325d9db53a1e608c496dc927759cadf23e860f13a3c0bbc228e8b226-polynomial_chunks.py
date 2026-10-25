"""Untrusted factorwise polynomial proof proposals using the native surface.

This is an isolated development prototype, not a checker or a new tactic.
Every returned line still needs the original surface and full final replay.
In particular, an equality passing the sparse integer analysis below is not
proof evidence.  No native limits or certificates are changed here.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from arithmetic_search import _polynomial, _quote
from peano_lab.kernel.formulas import Eq, pretty_formula
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero, pretty_term


MAX_COMMANDS = 156
MAX_ABSTRACT_VARIABLES = 8
MAX_PLAN_DEPTH = 12


class NoPlan(ValueError):
    pass


@dataclass(frozen=True)
class ChunkPlan:
    commands: tuple[str, ...]
    reason: str
    obligations: tuple[dict, ...]
    strategy: str = "polynomial_chunks_v1"

    def chunks(self, max_steps=8):
        """Continuation chunks; execute a later one only after its predecessor."""
        if type(max_steps) is not int or not 1 <= max_steps <= 8:
            raise ValueError("native proposal chunks contain 1..8 commands")
        return tuple(self.commands[start:start + max_steps]
                     for start in range(0, len(self.commands), max_steps))


def _nodes(term):
    if type(term) in (Var, Zero):
        return 1
    if type(term) is Succ:
        return 1 + _nodes(term.term)
    if type(term) in (Add, Mul):
        return 1 + _nodes(term.left) + _nodes(term.right)
    raise NoPlan("only rigid native polynomial terms are supported")


def _walk(term):
    yield term
    if type(term) is Succ:
        yield from _walk(term.term)
    elif type(term) in (Add, Mul):
        yield from _walk(term.left)
        yield from _walk(term.right)


def _numeral(term):
    while type(term) is Succ:
        term = term.term
    return type(term) is Zero


def _replace(term, replacements):
    if term in replacements:
        return replacements[term]
    if type(term) in (Var, Zero):
        return term
    if type(term) is Succ:
        return Succ(_replace(term.term, replacements))
    return type(term)(_replace(term.left, replacements), _replace(term.right, replacements))


def _identity(left, right):
    return _polynomial(left) == _polynomial(right)


def _size(equation):
    return _nodes(equation.left) + _nodes(equation.right)


def _abstraction(equation):
    """Replace shared syntax only when the *generalized* identity remains true.

    For example, a common n^4 can become an independent variable throughout
    a high-degree product identity.  Coefficient-collection identities can
    instead abstract whole matching summands.  The native proof then checks
    the universal generalized equation, and `apply` checks its instantiation.
    """
    original_size = _size(equation)
    left, right = equation.left, equation.right
    scope = 1 + max((t.index for term in (left, right) for t in _walk(term)
                     if type(t) is Var), default=-1)
    if scope > 32:
        return None
    counts = Counter(_walk(left)) + Counter(_walk(right))
    candidates = sorted((term for term, count in counts.items()
                         if count >= 2 and type(term) not in (Var, Zero)
                         and not _numeral(term)), key=lambda term: (-_nodes(term), repr(term)))
    next_variable = scope
    for candidate in candidates:
        if next_variable >= 60:
            break
        following_left = _replace(left, {candidate: Var(next_variable)})
        following_right = _replace(right, {candidate: Var(next_variable)})
        if following_left == left and following_right == right:
            continue
        if _identity(following_left, following_right):
            left, right = following_left, following_right
            next_variable += 1
    indices = sorted({t.index for term in (left, right) for t in _walk(term)
                      if type(t) is Var})
    if not indices or len(indices) > MAX_ABSTRACT_VARIABLES:
        return None
    mapping = {Var(old): Var(new) for new, old in enumerate(indices)}
    generalized = Eq(_replace(left, mapping), _replace(right, mapping))
    if _size(generalized) >= original_size - 2:
        return None
    return generalized, len(indices)


def _flatten_add(term):
    if type(term) is Add:
        return _flatten_add(term.left) + _flatten_add(term.right)
    return [term]


def _sum(terms):
    result = terms[0]
    for term in terms[1:]:
        result = Add(result, term)
    return result


class _Planner:
    def __init__(self, variables, context):
        self.variables = list(variables)
        self.used = set(variables) | {name for name, _ in context}
        self.commands = []
        self.obligations = []
        self.counter = 0

    def fresh(self, stem="hc"):
        while True:
            name = stem + str(self.counter)
            self.counter += 1
            if name not in self.used:
                self.used.add(name)
                return name

    def emit(self, *commands):
        if len(self.commands) + len(commands) > MAX_COMMANDS:
            raise NoPlan("the proposed decomposition has too many surface steps")
        if any(len(command.encode("utf-8")) > 512 for command in commands):
            raise NoPlan("a proposed surface line exceeds 512 bytes")
        self.commands.extend(commands)

    def formula(self, equation):
        return pretty_formula(equation, self.variables)

    def term(self, term):
        return pretty_term(term, self.variables)

    def ring(self, equation, *, abstract=True):
        abstraction = _abstraction(equation) if abstract else None
        if abstraction is not None:
            generalized, count = abstraction
            names = [self.fresh("cp") for _ in range(count)]
            lemma = self.fresh()
            formula = "forall " + " ".join(reversed(names)) + ". " + pretty_formula(generalized, names)
            self.emit("suffices " + lemma + " : " + formula, "apply " + lemma)
            self.emit(*("intro " + name for name in reversed(names)), "ring")
            self.obligations.append({"kind": "abstracted_ring", "concrete": self.formula(equation),
                                     "generalized": formula, "theorem": formula, "variables": count})
        else:
            self.emit("ring")
            closed = (("forall " + " ".join(reversed(self.variables)) + ". ")
                      if self.variables else "") + self.formula(equation)
            self.obligations.append({"kind": "ring", "concrete": self.formula(equation), "theorem": closed})

    def solve(self, equation, depth=0):
        if depth > MAX_PLAN_DEPTH or not _identity(equation.left, equation.right):
            raise NoPlan("no bounded polynomial identity decomposition")
        left, right = equation.left, equation.right
        if left == right:
            self.emit("refl")
            return
        # Native congruence never asks ring to normalize an unrelated sibling.
        if type(left) is type(right) and type(left) in (Add, Mul):
            if _identity(left.left, right.left) and _identity(left.right, right.right):
                self.emit("congr")
                self.solve(Eq(left.left, right.left), depth + 1)
                self.solve(Eq(left.right, right.right), depth + 1)
                return
        if type(left) is Mul and type(left.right) is Succ and right == Add(Mul(left.left, left.right.term), left.left):
            self.emit("apply PA6")
            return
        left_poly = _polynomial(left)
        generalized = _abstraction(equation)
        # Simple arithmetic remains a single native ring obligation. Splitting
        # large sums comes first; the checker, not this estimate, enforces caps.
        if len(left_poly) <= 4 or (generalized is not None and
                len(_polynomial(generalized[0].left)) <= 4 and _size(generalized[0]) <= 180):
            self.ring(equation)
            return
        if (type(right) is Mul and (type(right.left) is Add or type(right.right) is Add)
                and not (type(left) is Mul and (type(left.left) is Add or type(left.right) is Add))):
            self.emit("symm")
            self.solve(Eq(right, left), depth + 1)
            return
        # Split one additive factor; preserve product order exactly. The first
        # equality is just a small universal distributivity instance. Separate
        # native obligations normalize each half before collecting coefficients.
        if type(left) is Mul and (type(left.left) is Add or type(left.right) is Add):
            side = 0 if type(left.left) is Add else 1
            factor = left.left if side == 0 else left.right
            other = left.right if side == 0 else left.left
            summands = _flatten_add(factor)
            split = len(summands) // 2
            first, second = _sum(summands[:split]), _sum(summands[split:])
            products = (Mul(first, other), Mul(second, other)) if side == 0 else (Mul(other, first), Mul(other, second))
            distributed = Add(*products)
            normal_parts = tuple(_quote(_polynomial(term)) for term in products)
            middle = Add(*normal_parts)
            self.emit("trans " + self.term(distributed))
            self.ring(Eq(left, distributed))
            self.emit("trans " + self.term(middle), "congr")
            self.solve(Eq(products[0], normal_parts[0]), depth + 1)
            self.solve(Eq(products[1], normal_parts[1]), depth + 1)
            self.solve(Eq(middle, right), depth + 1)
            return
        # Normalize a proper subexpression first. A binomial prefix of degree
        # at most five already fits the unchanged native tactic limits. Later
        # multiplications are split by the rule above, rather than sent whole.
        candidates = []
        for term in (*_walk(left), *_walk(right)):
            if term in (left, right) or type(term) not in (Add, Mul, Succ):
                continue
            poly = _polynomial(term)
            normal = _quote(poly)
            if term != normal and 2 <= len(poly) <= 8 and _nodes(term) >= 5:
                candidates.append((len(poly), _nodes(term), term, normal))
        if candidates:
            _, _, subterm, normal = max(candidates, key=lambda item: item[:2])
            lemma = self.fresh()
            self.emit("have " + lemma + " : " + self.formula(Eq(subterm, normal)))
            if len(_polynomial(subterm)) <= 6 and max(map(len, _polynomial(subterm)), default=0) <= 5:
                self.ring(Eq(subterm, normal))
            else:
                self.solve(Eq(subterm, normal), depth + 1)
            self.emit("rewrite " + lemma)
            # rewrite is a first-occurrence operation. Use the same preorder
            # replacement shape without constructing any proof certificate.
            changed = [False]

            def first(item):
                if not changed[0] and item == subterm:
                    changed[0] = True
                    return normal
                if type(item) is Succ:
                    return Succ(first(item.term))
                if type(item) in (Add, Mul):
                    return type(item)(first(item.left), first(item.right))
                return item

            self.solve(Eq(first(left), first(right)), depth + 1)
            return
        self.ring(equation)


def polynomial_chunk_plan(equation, variables, context=()):
    """Return a bounded, untrusted surface script or None; never claim a proof."""
    if type(equation) is not Eq:
        return None
    try:
        planner = _Planner(variables, context)
        planner.solve(equation)
        return ChunkPlan(tuple(planner.commands),
            "Split polynomial products and check small universally generalized equalities.",
            tuple(planner.obligations))
    except (NoPlan, ValueError, RecursionError):
        return None
