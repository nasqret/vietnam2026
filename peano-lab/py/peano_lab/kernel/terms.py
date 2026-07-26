"""Peano-arithmetic terms and their deterministic surface syntax.

Kernel variables are de Bruijn indices.  Because the pinned ``parse_term`` API
has no name environment, free surface names are assigned indices in order of
first appearance.  ``parse_term_with_names`` exposes that table for the UI;
the small pinned function simply returns its term component.
"""

from __future__ import annotations

from dataclasses import dataclass


class ParseError(ValueError):
    """A final, position-bearing surface-syntax error."""


class Term:
    """Marker base class for the five PA term constructors."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Var(Term):
    index: int


@dataclass(frozen=True, slots=True)
class Zero(Term):
    pass


@dataclass(frozen=True, slots=True)
class Succ(Term):
    term: Term


@dataclass(frozen=True, slots=True)
class Add(Term):
    left: Term
    right: Term


@dataclass(frozen=True, slots=True)
class Mul(Term):
    left: Term
    right: Term


@dataclass(frozen=True, slots=True)
class _Token:
    text: str
    column: int


class _TokenStream:
    def __init__(self, source: str):
        self.source = source
        self.tokens = _tokenize(source)
        self.position = 0

    def peek(self) -> str | None:
        return self.tokens[self.position].text if self.position < len(self.tokens) else None

    def column(self) -> int:
        return (
            self.tokens[self.position].column
            if self.position < len(self.tokens)
            else len(self.source) + 1
        )

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise ParseError(f"expected more input at column {self.column()}")
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
            raise ParseError(f"expected {choice!r}, got {shown} at column {self.column()}")


_TWO_CHARACTER_TOKENS = ("->", "/\\", "\\/")
_SINGLE_TOKENS = set("#()+*=.~¬⊥→∧∨∀∃·")


def _tokenize(source: str) -> list[_Token]:
    if not isinstance(source, str):
        raise ParseError("source must be text")
    tokens: list[_Token] = []
    i = 0
    while i < len(source):
        if source[i].isspace():
            i += 1
            continue
        pair = source[i : i + 2]
        if pair in _TWO_CHARACTER_TOKENS:
            tokens.append(_Token(pair, i + 1))
            i += 2
            continue
        char = source[i]
        if char in _SINGLE_TOKENS:
            tokens.append(_Token(char, i + 1))
            i += 1
            continue
        if char.isdigit():
            end = i + 1
            while end < len(source) and source[end].isdigit():
                end += 1
            tokens.append(_Token(source[i:end], i + 1))
            i = end
            continue
        if char.isalpha() or char == "_":
            end = i + 1
            while end < len(source) and (
                source[end].isalnum() or source[end] in "_'"
            ):
                end += 1
            tokens.append(_Token(source[i:end], i + 1))
            i = end
            continue
        raise ParseError(f"unexpected character {char!r} at column {i + 1}")
    return tokens


def _is_identifier(token: str | None) -> bool:
    return bool(
        token
        and (token[0].isalpha() or token[0] == "_")
        and all(char.isalnum() or char in "_'" for char in token[1:])
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


def _parse_term_prefix(stream: _TokenStream, bound: list[str], free: list[str]) -> Term:
    token = stream.peek()
    if token is None:
        raise ParseError(f"expected a term at column {stream.column()}")
    if token == "S":
        stream.take()
        return Succ(_parse_term_prefix(stream, bound, free))
    if token == "#":
        stream.take()
        index = stream.peek()
        if index is None or not index.isdigit():
            raise ParseError(
                f"expected a de Bruijn index after '#', at column {stream.column()}"
            )
        stream.take()
        return Var(int(index))
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
    raise ParseError(f"expected a term, got {token!r} at column {stream.column()}")


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
        level = precedence[operator]
        if level < minimum_precedence:
            break
        stream.take()
        right = _parse_term_from(stream, bound, free, level + 1)
        left = Add(left, right) if operator == "+" else Mul(left, right)
    return left


def parse_term_with_names(src: str) -> tuple[Term, tuple[str, ...]]:
    """Parse a term and return its first-occurrence free-name table."""

    stream = _TokenStream(src)
    if not stream.tokens:
        raise ParseError("expected a term at column 1")
    free: list[str] = []
    term = _parse_term_from(stream, [], free)
    if stream.peek() is not None:
        raise ParseError(f"unexpected token {stream.peek()!r} at column {stream.column()}")
    return term, tuple(free)


def parse_term_in_context(src: str, names: list[str]) -> Term:
    """Parse using an explicit index-to-name context, rejecting unknown names.

    This companion resolves the information deliberately absent from the
    pinned ``parse_term(src)`` signature.  It gives the future tactic layer a
    genuine inverse for ``pretty_term(term, names)``, even when some lower
    context slots do not occur in ``term``.
    """

    if (
        not isinstance(names, list)
        or not all(_is_identifier(name) for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("context names must be distinct surface identifiers")
    stream = _TokenStream(src)
    if not stream.tokens:
        raise ParseError("expected a term at column 1")
    free = list(names)
    term = _parse_term_from(stream, [], free)
    if stream.peek() is not None:
        raise ParseError(f"unexpected token {stream.peek()!r} at column {stream.column()}")
    if len(free) != len(names):
        unknown = ", ".join(free[len(names) :])
        raise ParseError(f"unknown term variable(s): {unknown}")
    return term


def parse_term(src: str) -> Term:
    """Parse ``0``, ``S``, ``+``, ``*``/``·``, variables, and numeral sugar."""

    return parse_term_with_names(src)[0]


def _successor_number(term: Term) -> int | None:
    count = 0
    while isinstance(term, Succ):
        count += 1
        term = term.term
    return count if isinstance(term, Zero) else None


def _pretty_term(term: Term, names: list[str], parent_precedence: int) -> str:
    if isinstance(term, Var):
        text = names[term.index] if 0 <= term.index < len(names) else f"#{term.index}"
        level = 4
    elif isinstance(term, Zero):
        text, level = "0", 4
    elif isinstance(term, Succ):
        number = _successor_number(term)
        if number is not None:
            text, level = str(number), 4
        else:
            text = "S " + _pretty_term(term.term, names, 3)
            level = 3
    elif isinstance(term, (Add, Mul)):
        level = 1 if isinstance(term, Add) else 2
        symbol = "+" if isinstance(term, Add) else "·"
        left = _pretty_term(term.left, names, level)
        right = _pretty_term(term.right, names, level + 1)
        text = f"{left} {symbol} {right}"
    else:
        raise TypeError("expected a PA term")
    return f"({text})" if level < parent_precedence else text


def pretty_term(t: Term, names: list[str]) -> str:
    """Return the single canonical Unicode surface representation of ``t``."""

    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise TypeError("names must be a list of strings")
    return _pretty_term(t, names, 0)


__all__ = [
    "Term",
    "Var",
    "Zero",
    "Succ",
    "Add",
    "Mul",
    "ParseError",
    "parse_term",
    "parse_term_with_names",
    "parse_term_in_context",
    "pretty_term",
]
