"""Frozen theorem canonicalization for Hydra semantic profiles v1 and v2.

This compatibility module deliberately does not import Peano Lab's live
parser, printer, or browser admission constants.  Those surfaces may evolve
for a later semantic profile without changing how historical v1/v2 theorem
strings are admitted or canonicalized.  Only the inert kernel syntax classes
are shared: the grammar and printer below are the frozen v1 implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero


MAX_SOURCE_CHARACTERS = 8_192
MAX_DECIMAL_NUMERAL = 256
BINDER_NAMES = ("x", "y", "z", "n", "m", "k", "i", "j", "u", "v", "w")
FORBIDDEN_UNICODE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})

_NUMERAL_LITERAL = re.compile(r"(?<![\w'#])\d+", re.UNICODE)
_TWO_CHARACTER_TOKENS = ("->", "/\\", "\\/", "<=")
_SINGLE_TOKENS = frozenset("#(),+*=.~¬⊥→∧∨∀∃·≤")


class FrozenProfileTheoremError(ValueError):
    """A theorem is outside the frozen v1/v2 surface contract."""


@dataclass(frozen=True, slots=True)
class _Token:
    text: str
    column: int


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        pair = source[index : index + 2]
        if pair in _TWO_CHARACTER_TOKENS:
            tokens.append(_Token(pair, index + 1))
            index += 2
            continue
        character = source[index]
        if character in _SINGLE_TOKENS:
            tokens.append(_Token(character, index + 1))
            index += 1
            continue
        if character.isdigit():
            end = index + 1
            while end < len(source) and source[end].isdigit():
                end += 1
            tokens.append(_Token(source[index:end], index + 1))
            index = end
            continue
        if character.isalpha() or character == "_":
            end = index + 1
            while end < len(source) and (
                source[end].isalnum() or source[end] in "_'"
            ):
                end += 1
            tokens.append(_Token(source[index:end], index + 1))
            index = end
            continue
        raise FrozenProfileTheoremError(
            f"unexpected character {character!r} at column {index + 1}"
        )
    return tokens


class _TokenStream:
    __slots__ = ("position", "source", "tokens")

    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens = _tokenize(source)
        self.position = 0

    def peek(self) -> str | None:
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position].text

    def column(self) -> int:
        if self.position >= len(self.tokens):
            return len(self.source) + 1
        return self.tokens[self.position].column

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise FrozenProfileTheoremError(
                f"expected more input at column {self.column()}"
            )
        self.position += 1
        return token

    def accept(self, *choices: str) -> str | None:
        token = self.peek()
        if token in choices:
            self.position += 1
            return token
        return None

    def expect(self, choice: str) -> None:
        if self.accept(choice) is None:
            got = self.peek()
            shown = "end of input" if got is None else repr(got)
            raise FrozenProfileTheoremError(
                f"expected {choice!r}, got {shown} at column {self.column()}"
            )


def _is_identifier(token: str | None) -> bool:
    return bool(
        token
        and (token[0].isalpha() or token[0] == "_")
        and all(character.isalnum() or character in "_'" for character in token[1:])
    )


def _resolve_name(name: str, bound: list[str], free: list[str]) -> int:
    if name in bound:
        return bound.index(name)
    if name not in free:
        free.append(name)
    return len(bound) + free.index(name)


def _numeral(value: int) -> Term:
    result: Term = Zero()
    for _ in range(value):
        result = Succ(result)
    return result


def _parse_term_prefix(
    stream: _TokenStream,
    bound: list[str],
    free: list[str],
) -> Term:
    token = stream.peek()
    if token is None:
        raise FrozenProfileTheoremError(
            f"expected a term at column {stream.column()}"
        )
    if token == "S":
        stream.take()
        return Succ(_parse_term_prefix(stream, bound, free))
    if token == "#":
        stream.take()
        raw_index = stream.peek()
        if raw_index is None or not raw_index.isdigit():
            raise FrozenProfileTheoremError(
                f"expected a de Bruijn index after '#', at column {stream.column()}"
            )
        stream.take()
        return Var(int(raw_index))
    if token == "(":
        stream.take()
        term = _parse_term_from(stream, bound, free)
        stream.expect(")")
        return term
    if token.isdigit():
        stream.take()
        return _numeral(int(token))
    if _is_identifier(token):
        stream.take()
        return Var(_resolve_name(token, bound, free))
    raise FrozenProfileTheoremError(
        f"expected a term, got {token!r} at column {stream.column()}"
    )


def _parse_term_from(
    stream: _TokenStream,
    bound: list[str],
    free: list[str],
    minimum_precedence: int = 0,
) -> Term:
    left = _parse_term_prefix(stream, bound, free)
    precedence = {"+": 1, "*": 2, "·": 2}
    while stream.peek() in precedence:
        operator = stream.peek()
        assert operator is not None
        level = precedence[operator]
        if level < minimum_precedence:
            break
        stream.take()
        right = _parse_term_from(stream, bound, free, level + 1)
        left = Add(left, right) if operator == "+" else Mul(left, right)
    return left


def _lift_for_new_binder(term: Term) -> Term:
    if type(term) is Var:
        return Var(term.index + 1)
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        return Succ(_lift_for_new_binder(term.term))
    if type(term) is Add:
        return Add(_lift_for_new_binder(term.left), _lift_for_new_binder(term.right))
    if type(term) is Mul:
        return Mul(_lift_for_new_binder(term.left), _lift_for_new_binder(term.right))
    raise FrozenProfileTheoremError("expected an exact PA term")


class _FormulaParser:
    __slots__ = ("bound", "free", "stream")

    def __init__(self, source: str) -> None:
        self.stream = _TokenStream(source)
        self.bound: list[str] = []
        self.free: list[str] = []

    def parse(self) -> Formula:
        if not self.stream.tokens:
            raise FrozenProfileTheoremError("expected a formula at column 1")
        formula = self._implication()
        if self.stream.peek() is not None:
            raise FrozenProfileTheoremError(
                f"unexpected token {self.stream.peek()!r} "
                f"at column {self.stream.column()}"
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
                raise FrozenProfileTheoremError(
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
        position = self.stream.position
        free_count = len(self.free)
        try:
            left = _parse_term_from(self.stream, self.bound, self.free)
            relation = self.stream.accept("=", "<=", "≤")
            if relation is None:
                raise FrozenProfileTheoremError(
                    "an atomic formula must be an equation"
                )
            right = _parse_term_from(self.stream, self.bound, self.free)
            if relation == "=":
                return Eq(left, right)
            return Exists(
                Eq(
                    Add(Var(0), _lift_for_new_binder(left)),
                    _lift_for_new_binder(right),
                )
            )
        except FrozenProfileTheoremError:
            self.stream.position = position
            del self.free[free_count:]
        if self.stream.accept("(") is not None:
            formula = self._implication()
            self.stream.expect(")")
            return formula
        token = self.stream.peek()
        shown = "end of input" if token is None else repr(token)
        raise FrozenProfileTheoremError(
            f"expected an equation or parenthesized formula, got {shown} "
            f"at column {self.stream.column()}"
        )


def _parse_formula_with_names(source: str) -> tuple[Formula, tuple[str, ...]]:
    parser = _FormulaParser(source)
    return parser.parse(), tuple(parser.free)


def _well_scoped_term(term: object, depth: int) -> bool:
    if type(term) is Var:
        return type(term.index) is int and 0 <= term.index < depth
    if type(term) is Zero:
        return True
    if type(term) is Succ:
        return _well_scoped_term(term.term, depth)
    if type(term) is Add or type(term) is Mul:
        return _well_scoped_term(term.left, depth) and _well_scoped_term(
            term.right, depth
        )
    return False


def _well_scoped_formula(formula: object, depth: int = 0) -> bool:
    if type(formula) is Eq:
        return _well_scoped_term(formula.left, depth) and _well_scoped_term(
            formula.right, depth
        )
    if type(formula) is Bot:
        return True
    if type(formula) is Imp or type(formula) is And or type(formula) is Or:
        return _well_scoped_formula(formula.left, depth) and _well_scoped_formula(
            formula.right, depth
        )
    if type(formula) is Forall or type(formula) is Exists:
        return _well_scoped_formula(formula.body, depth + 1)
    return False


def _drop_le_binder(term: Term) -> Term | None:
    if type(term) is Var:
        return None if term.index == 0 else Var(term.index - 1)
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        child = _drop_le_binder(term.term)
        return None if child is None else Succ(child)
    if type(term) is Add or type(term) is Mul:
        left = _drop_le_binder(term.left)
        right = _drop_le_binder(term.right)
        if left is None or right is None:
            return None
        return Add(left, right) if type(term) is Add else Mul(left, right)
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


def _successor_number(term: Term) -> int | None:
    count = 0
    while type(term) is Succ:
        count += 1
        term = term.term
    return count if type(term) is Zero else None


def _pretty_term(term: Term, names: list[str], parent_precedence: int) -> str:
    if type(term) is Var:
        text = names[term.index] if 0 <= term.index < len(names) else f"#{term.index}"
        level = 4
    elif type(term) is Zero:
        text, level = "0", 4
    elif type(term) is Succ:
        number = _successor_number(term)
        if number is not None:
            text, level = str(number), 4
        else:
            text, level = "S " + _pretty_term(term.term, names, 3), 3
    elif type(term) is Add or type(term) is Mul:
        level = 1 if type(term) is Add else 2
        symbol = "+" if type(term) is Add else "·"
        text = (
            f"{_pretty_term(term.left, names, level)} {symbol} "
            f"{_pretty_term(term.right, names, level + 1)}"
        )
    else:
        raise FrozenProfileTheoremError("expected an exact PA term")
    return f"({text})" if level < parent_precedence else text


def _fresh_binder(names: list[str]) -> str:
    used = set(names)
    for candidate in BINDER_NAMES:
        if candidate not in used:
            return candidate
    index = 0
    while f"x{index}" in used:
        index += 1
    return f"x{index}"


def _pretty_formula(
    formula: Formula,
    names: list[str],
    parent_precedence: int,
) -> str:
    le_terms = _as_le(formula)
    if le_terms is not None:
        lower, upper = le_terms
        text = f"{_pretty_term(lower, names, 0)} ≤ {_pretty_term(upper, names, 0)}"
        level = 5
    elif type(formula) is Eq:
        text = (
            f"{_pretty_term(formula.left, names, 0)} = "
            f"{_pretty_term(formula.right, names, 0)}"
        )
        level = 5
    elif type(formula) is Bot:
        text, level = "⊥", 5
    elif type(formula) is Imp and type(formula.consequent) is Bot:
        text, level = "¬" + _pretty_formula(formula.antecedent, names, 4), 4
    elif type(formula) is And or type(formula) is Or or type(formula) is Imp:
        if type(formula) is And:
            level, symbol = 3, "∧"
        elif type(formula) is Or:
            level, symbol = 2, "∨"
        else:
            level, symbol = 1, "→"
        left = _pretty_formula(
            formula.left,
            names,
            level + (1 if type(formula) is Imp else 0),
        )
        right_level = level if type(formula) is Imp else level + 1
        if type(formula) is Imp and (
            type(formula.right) is Forall or type(formula.right) is Exists
        ):
            right_level = 0
        right = _pretty_formula(formula.right, names, right_level)
        text = f"{left} {symbol} {right}"
    elif type(formula) is Forall or type(formula) is Exists:
        binder = _fresh_binder(names)
        symbol = "∀" if type(formula) is Forall else "∃"
        text = f"{symbol} {binder}. {_pretty_formula(formula.body, [binder] + names, 0)}"
        level = 0
    else:
        raise FrozenProfileTheoremError("expected an exact PA formula")
    return f"({text})" if level < parent_precedence else text


def _oversized_numeral(source: str) -> str | None:
    ceiling = str(MAX_DECIMAL_NUMERAL)
    for match in _NUMERAL_LITERAL.finditer(source):
        literal = match.group()
        decimal = "".join(
            str(unicodedata.decimal(character)) for character in literal
        )
        significant = decimal.lstrip("0") or "0"
        if len(significant) > len(ceiling) or (
            len(significant) == len(ceiling) and significant > ceiling
        ):
            return literal
    return None


def canonicalize_profile_theorem(source: str) -> str:
    """Canonicalize under the immutable v1/v2 source and grammar contract."""

    if type(source) is not str or not source:
        raise FrozenProfileTheoremError("profile theorem must be non-empty text")
    if len(source) > MAX_SOURCE_CHARACTERS:
        raise FrozenProfileTheoremError(
            f"profile theorem exceeds the {MAX_SOURCE_CHARACTERS}-character transport bound"
        )
    if source != source.strip() or source.splitlines() != [source]:
        raise FrozenProfileTheoremError(
            "profile theorem must be exactly one line with no outer whitespace"
        )
    if any(
        unicodedata.category(character) in FORBIDDEN_UNICODE_CATEGORIES
        for character in source
    ):
        raise FrozenProfileTheoremError("profile theorem contains an unsafe character")
    if "#" in source:
        raise FrozenProfileTheoremError(
            "explicit de Bruijn indices are not admitted in profile targets"
        )
    dangerous_numeral = _oversized_numeral(source)
    if dangerous_numeral is not None:
        raise FrozenProfileTheoremError(
            f"profile theorem contains resource-dangerous numeral {dangerous_numeral}"
        )
    try:
        formula, free_names = _parse_formula_with_names(source)
    except RecursionError:
        raise FrozenProfileTheoremError(
            "profile theorem exceeded parser recursion"
        ) from None
    except (TypeError, ValueError) as exc:
        raise FrozenProfileTheoremError(f"invalid profile theorem: {exc}") from None
    if free_names:
        raise FrozenProfileTheoremError(
            "profile theorem must be closed; quantify free variables explicitly: "
            + ", ".join(free_names)
        )
    if not _well_scoped_formula(formula):
        raise FrozenProfileTheoremError(
            "profile theorem has a free de Bruijn index"
        )
    canonical = _pretty_formula(formula, [], 0)
    reparsed, reparsed_names = _parse_formula_with_names(canonical)
    if reparsed_names or reparsed != formula or not _well_scoped_formula(reparsed):
        raise FrozenProfileTheoremError(
            "profile theorem failed canonical round trip"
        )
    return canonical


def canonicalize_profile_formula(formula: Formula) -> str:
    """Print one closed kernel formula with the immutable v1/v2 printer."""

    if not _well_scoped_formula(formula):
        raise FrozenProfileTheoremError(
            "original target must be closed and well scoped"
        )
    try:
        canonical = _pretty_formula(formula, [], 0)
        reparsed, free_names = _parse_formula_with_names(canonical)
    except RecursionError:
        raise FrozenProfileTheoremError(
            "original target exceeded canonicalizer recursion"
        ) from None
    except (TypeError, ValueError) as exc:
        raise FrozenProfileTheoremError(
            f"original target cannot be canonicalized: {exc}"
        ) from None
    if free_names or reparsed != formula or not _well_scoped_formula(reparsed):
        raise FrozenProfileTheoremError(
            "original target is not an exact canonical profile formula"
        )
    return canonical


__all__ = [
    "BINDER_NAMES",
    "FORBIDDEN_UNICODE_CATEGORIES",
    "FrozenProfileTheoremError",
    "MAX_DECIMAL_NUMERAL",
    "MAX_SOURCE_CHARACTERS",
    "canonicalize_profile_formula",
    "canonicalize_profile_theorem",
]
