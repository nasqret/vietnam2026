"""First-order formulas for intuitionistic Peano arithmetic.

The parser accepts ASCII and Unicode spellings.  The printer deliberately
chooses one Unicode spelling, one precedence convention, and fresh binder
names, so proof states and JSONL traces have stable text.
"""

from __future__ import annotations

from dataclasses import dataclass

from .terms import (
    Add,
    Mul,
    ParseError,
    Succ,
    Term,
    Var,
    Zero,
    _TokenStream,
    _is_identifier,
    _parse_term_from,
    _pretty_term,
)


class Formula:
    """Marker base class for PA formula constructors."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Eq(Formula):
    left: Term
    right: Term


@dataclass(frozen=True, slots=True)
class Bot(Formula):
    pass


@dataclass(frozen=True, slots=True)
class Imp(Formula):
    antecedent: Formula
    consequent: Formula

    @property
    def left(self) -> Formula:
        """Structural alias shared with ``And`` and ``Or`` traversals."""

        return self.antecedent

    @property
    def right(self) -> Formula:
        """Structural alias shared with ``And`` and ``Or`` traversals."""

        return self.consequent


@dataclass(frozen=True, slots=True)
class And(Formula):
    left: Formula
    right: Formula


@dataclass(frozen=True, slots=True)
class Or(Formula):
    left: Formula
    right: Formula


@dataclass(frozen=True, slots=True)
class Forall(Formula):
    body: Formula


@dataclass(frozen=True, slots=True)
class Exists(Formula):
    body: Formula


class _FormulaParser:
    def __init__(self, source: str):
        self.stream = _TokenStream(source)
        self.bound: list[str] = []  # innermost binder first
        self.free: list[str] = []   # outer names in first-occurrence order

    def parse(self) -> Formula:
        if not self.stream.tokens:
            raise ParseError("expected a formula at column 1")
        formula = self._implication()
        if self.stream.peek() is not None:
            raise ParseError(
                f"unexpected token {self.stream.peek()!r} at column {self.stream.column()}"
            )
        return formula

    def _implication(self) -> Formula:
        left = self._disjunction()
        if self.stream.accept("->", "→") is not None:
            return Imp(left, self._implication())
        return left

    def _disjunction(self) -> Formula:
        left = self._conjunction()
        while self.stream.accept("\\/", "∨") is not None:
            left = Or(left, self._conjunction())
        return left

    def _conjunction(self) -> Formula:
        left = self._prefix()
        while self.stream.accept("/\\", "∧") is not None:
            left = And(left, self._prefix())
        return left

    def _prefix(self) -> Formula:
        if self.stream.accept("~", "¬") is not None:
            return Imp(self._prefix(), Bot())
        quantifier = self.stream.accept("forall", "∀", "exists", "∃")
        if quantifier is not None:
            names: list[str] = []
            while _is_identifier(self.stream.peek()) and self.stream.peek() not in {
                "forall",
                "exists",
                "bot",
                "false",
            }:
                names.append(self.stream.take())
            if not names:
                raise ParseError(
                    f"expected a binder name at column {self.stream.column()}"
                )
            self.stream.expect(".")
            old_bound = self.bound
            self.bound = list(reversed(names)) + old_bound
            try:
                body = self._implication()
            finally:
                self.bound = old_bound
            constructor = Forall if quantifier in {"forall", "∀"} else Exists
            for _ in reversed(names):
                body = constructor(body)
            return body
        return self._atom()

    def _atom(self) -> Formula:
        if self.stream.accept("⊥", "bot", "false") is not None:
            return Bot()

        # A parenthesized term may begin an equality, while a parenthesized
        # formula may begin any connective.  Try the term reading first, then
        # roll back both tokens and newly allocated free names on failure.
        position = self.stream.position
        free_count = len(self.free)
        try:
            left = _parse_term_from(self.stream, self.bound, self.free)
            relation = self.stream.accept("=", "<=", "≤")
            if relation is None:
                raise ParseError("an atomic formula must be an equation")
            right = _parse_term_from(self.stream, self.bound, self.free)
            if relation == "=":
                return Eq(left, right)
            # Defined surface sugar only: a ≤ b means ∃k. k + a = b.
            # Inserting that binder shifts every variable already parsed.
            return Exists(
                Eq(
                    Add(Var(0), _lift_for_new_binder(left)),
                    _lift_for_new_binder(right),
                )
            )
        except ParseError:
            self.stream.position = position
            del self.free[free_count:]

        if self.stream.accept("(") is not None:
            formula = self._implication()
            self.stream.expect(")")
            return formula
        token = self.stream.peek()
        shown = "end of input" if token is None else repr(token)
        raise ParseError(
            f"expected an equation or parenthesized formula, got {shown} "
            f"at column {self.stream.column()}"
        )


def parse_formula_with_names(src: str) -> tuple[Formula, tuple[str, ...]]:
    """Parse a formula and return its deterministic free-name table."""

    parser = _FormulaParser(src)
    return parser.parse(), tuple(parser.free)


def parse_formula_in_context(src: str, names: list[str]) -> Formula:
    """Parse with an explicit free-variable context, rejecting unknown names."""

    if (
        not isinstance(names, list)
        or not all(_is_identifier(name) for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("context names must be distinct surface identifiers")
    parser = _FormulaParser(src)
    parser.free = list(names)
    formula = parser.parse()
    if len(parser.free) != len(names):
        unknown = ", ".join(parser.free[len(names) :])
        raise ParseError(f"unknown term variable(s): {unknown}")
    return formula


def parse_formula(src: str) -> Formula:
    """Parse PA surface syntax, expanding negation to implication-to-bottom."""

    return parse_formula_with_names(src)[0]


_BINDER_NAMES = ("x", "y", "z", "n", "m", "k", "i", "j", "u", "v", "w")


def _lift_for_new_binder(term: Term) -> Term:
    if type(term) is Var:
        return Var(term.index + 1)
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(_lift_for_new_binder(term.term))
    if type(term) is Add:
        return Add(
            _lift_for_new_binder(term.left),
            _lift_for_new_binder(term.right),
        )
    if type(term) is Mul:
        return Mul(
            _lift_for_new_binder(term.left),
            _lift_for_new_binder(term.right),
        )
    raise TypeError("expected a PA term")


def _drop_le_binder(term: Term) -> Term | None:
    """Remove the witness slot, rejecting terms that depend on it."""

    if type(term) is Var:
        return None if term.index == 0 else Var(term.index - 1)
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        child = _drop_le_binder(term.term)
        return None if child is None else Succ(child)
    if type(term) in (Add, Mul):
        left = _drop_le_binder(term.left)
        right = _drop_le_binder(term.right)
        if left is None or right is None:
            return None
        return type(term)(left, right)
    return None


def _as_le(formula: Formula) -> tuple[Term, Term] | None:
    if type(formula) is not Exists or type(formula.body) is not Eq:
        return None
    equation = formula.body
    if type(equation.left) is not Add or equation.left.left != Var(0):
        return None
    lower = _drop_le_binder(equation.left.right)
    upper = _drop_le_binder(equation.right)
    return None if lower is None or upper is None else (lower, upper)


def _fresh_binder(names: list[str]) -> str:
    used = set(names)
    for candidate in _BINDER_NAMES:
        if candidate not in used:
            return candidate
    index = 0
    while f"x{index}" in used:
        index += 1
    return f"x{index}"


def _pretty_formula(formula: Formula, names: list[str], parent_precedence: int) -> str:
    le_terms = _as_le(formula)
    if le_terms is not None:
        lower, upper = le_terms
        text = f"{_pretty_term(lower, names, 0)} ≤ {_pretty_term(upper, names, 0)}"
        level = 5
    elif isinstance(formula, Eq):
        text = f"{_pretty_term(formula.left, names, 0)} = {_pretty_term(formula.right, names, 0)}"
        level = 5
    elif isinstance(formula, Bot):
        text, level = "⊥", 5
    elif isinstance(formula, Imp) and isinstance(formula.right, Bot):
        text = "¬" + _pretty_formula(formula.left, names, 4)
        level = 4
    elif isinstance(formula, (And, Or, Imp)):
        if isinstance(formula, And):
            level, symbol = 3, "∧"
        elif isinstance(formula, Or):
            level, symbol = 2, "∨"
        else:
            level, symbol = 1, "→"
        left = _pretty_formula(formula.left, names, level + (1 if isinstance(formula, Imp) else 0))
        right_level = level if isinstance(formula, Imp) else level + 1
        if isinstance(formula, Imp) and isinstance(formula.right, (Forall, Exists)):
            # A quantifier after an arrow owns the whole right-hand side, so
            # parentheses add noise without resolving any ambiguity.
            right_level = 0
        right = _pretty_formula(formula.right, names, right_level)
        text = f"{left} {symbol} {right}"
    elif isinstance(formula, (Forall, Exists)):
        binder = _fresh_binder(names)
        symbol = "∀" if isinstance(formula, Forall) else "∃"
        text = f"{symbol} {binder}. {_pretty_formula(formula.body, [binder] + names, 0)}"
        level = 0
    else:
        raise TypeError("expected a PA formula")
    return f"({text})" if level < parent_precedence else text


def pretty_formula(f: Formula, names: list[str]) -> str:
    """Return the single canonical Unicode surface representation of ``f``."""

    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise TypeError("names must be a list of strings")
    return _pretty_formula(f, names, 0)


__all__ = [
    "Formula",
    "Eq",
    "Bot",
    "Imp",
    "And",
    "Or",
    "Forall",
    "Exists",
    "ParseError",
    "parse_formula",
    "parse_formula_with_names",
    "parse_formula_in_context",
    "pretty_formula",
]
