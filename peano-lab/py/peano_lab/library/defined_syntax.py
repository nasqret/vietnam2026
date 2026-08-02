"""Conservative, opt-in defined predicate syntax for Peano Lab.

The kernel language remains unchanged.  This module recognizes a small,
versioned registry of calls of the form ``Name(term, ...)`` and expands them
immediately to the existing first-order PA formula and term constructors.
The ordinary :mod:`peano_lab.kernel.formulas` parse APIs deliberately do not
enable these definitions.

Definitions are templates over de Bruijn parameter slots.  Instantiation is
simultaneous and binder-aware: actual arguments are lifted when copied under
a template binder, so neither template binders nor names chosen by the user
can capture them.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Mapping

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    _FormulaParser,
    parse_formula_in_context,
)
from peano_lab.kernel.terms import (
    Add,
    Mul,
    ParseError,
    Succ,
    Term,
    Var,
    Zero,
    _is_identifier,
    _parse_term_from,
)


DEFINED_SYNTAX_REGISTRY_ID = "peano-lab.defined-predicates"
DEFINED_SYNTAX_VERSION = 1
DEFAULT_EXPANSION_BUDGET = 32_768


@dataclass(frozen=True, slots=True)
class DefinitionSpec:
    """Immutable metadata and core template for one surface definition."""

    stable_id: str
    name: str
    parameters: tuple[str, ...]
    template_source: str
    template_formula: Formula
    summary: str
    category: str
    conceptual_dependencies: tuple[str, ...] = ()

    @property
    def arity(self) -> int:
        return len(self.parameters)


def _definition(
    *,
    stable_id: str,
    name: str,
    parameters: tuple[str, ...],
    template_source: str,
    summary: str,
    category: str,
    conceptual_dependencies: tuple[str, ...] = (),
) -> DefinitionSpec:
    if not stable_id or not isinstance(stable_id, str):
        raise ValueError("definition stable_id must be non-empty text")
    if not _is_identifier(name):
        raise ValueError("definition name must be a Peano identifier")
    if (
        not parameters
        or not all(_is_identifier(parameter) for parameter in parameters)
        or len(set(parameters)) != len(parameters)
    ):
        raise ValueError("definition parameters must be distinct Peano identifiers")
    template_formula = parse_formula_in_context(template_source, list(parameters))
    return DefinitionSpec(
        stable_id=stable_id,
        name=name,
        parameters=parameters,
        template_source=template_source,
        template_formula=template_formula,
        summary=summary,
        category=category,
        conceptual_dependencies=conceptual_dependencies,
    )


DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _definition(
        stable_id="PA-DEF-DVD-v1",
        name="Dvd",
        parameters=("d", "n"),
        template_source="exists q. n = d * q",
        summary="The natural number d divides n.",
        category="divisibility",
    ),
    _definition(
        stable_id="PA-DEF-LT-v1",
        name="Lt",
        parameters=("a", "b"),
        template_source="exists k. k + S a = b",
        summary="Strict order on natural numbers.",
        category="order",
    ),
    _definition(
        stable_id="PA-DEF-DIVREM-v1",
        name="DivRem",
        parameters=("n", "d", "q", "r"),
        template_source="n = d * q + r /\\ exists k. k + S r = d",
        summary="q and r are a quotient and a strict remainder for n by d.",
        category="division",
        conceptual_dependencies=("Lt",),
    ),
    _definition(
        stable_id="PA-DEF-PRIME-v1",
        name="Prime",
        parameters=("p",),
        template_source=(
            "~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1"
        ),
        summary="p is nonunit and every factorization of p has a unit factor.",
        category="primality",
    ),
    _definition(
        stable_id="PA-DEF-ISGCD-v1",
        name="IsGCD",
        parameters=("g", "a", "b"),
        template_source=(
            "(exists x. a = g * x) /\\ (exists y. b = g * y) /\\ "
            "forall c. (exists u. a = c * u) -> "
            "(exists v. b = c * v) -> exists w. g = c * w"
        ),
        summary="g divides a and b and is divisible by every common divisor.",
        category="gcd",
        conceptual_dependencies=("Dvd",),
    ),
    _definition(
        stable_id="PA-DEF-COPRIME-v1",
        name="Coprime",
        parameters=("a", "b"),
        template_source=(
            "forall c. (exists u. a = c * u) -> "
            "(exists v. b = c * v) -> c = 1"
        ),
        summary="Every common divisor of a and b is one.",
        category="gcd",
        conceptual_dependencies=("Dvd", "IsGCD"),
    ),
    _definition(
        stable_id="PA-DEF-MODEQ-v1",
        name="ModEq",
        parameters=("m", "a", "b"),
        template_source="exists u v. a + m * u = b + m * v",
        summary="a and b are congruent modulo m using balanced natural witnesses.",
        category="congruence",
    ),
)


def _build_definition_map() -> Mapping[str, DefinitionSpec]:
    result: dict[str, DefinitionSpec] = {}
    stable_ids: set[str] = set()
    for definition in DEFINITIONS:
        if definition.name in result:
            raise ValueError(f"duplicate definition name: {definition.name}")
        if definition.stable_id in stable_ids:
            raise ValueError(f"duplicate definition stable id: {definition.stable_id}")
        result[definition.name] = definition
        stable_ids.add(definition.stable_id)
    for definition in DEFINITIONS:
        unknown = set(definition.conceptual_dependencies) - result.keys()
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise ValueError(f"unknown conceptual dependencies for {definition.name}: {joined}")
    return MappingProxyType(result)


DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = _build_definition_map()


def _registry_sha256() -> str:
    record = {
        "registry_id": DEFINED_SYNTAX_REGISTRY_ID,
        "version": DEFINED_SYNTAX_VERSION,
        "definitions": [
            {
                "stable_id": definition.stable_id,
                "name": definition.name,
                "parameters": definition.parameters,
                "template_source": definition.template_source,
                "summary": definition.summary,
                "category": definition.category,
                "conceptual_dependencies": definition.conceptual_dependencies,
            }
            for definition in DEFINITIONS
        ],
    }
    payload = json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


DEFINED_SYNTAX_REGISTRY_SHA256 = _registry_sha256()


class _ExpansionCounter:
    __slots__ = ("limit", "used")

    def __init__(self, limit: int):
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("expansion_budget must be a positive integer")
        self.limit = limit
        self.used = 0

    def node(self, definition: DefinitionSpec, column: int) -> None:
        self.used += 1
        if self.used > self.limit:
            raise ParseError(
                f"defined-syntax expansion exceeds the {self.limit}-node budget "
                f"while expanding {definition.name!r} at column {column}"
            )


def _copy_shifted_argument(
    term: Term,
    by: int,
    counter: _ExpansionCounter,
    definition: DefinitionSpec,
    column: int,
) -> Term:
    counter.node(definition, column)
    if isinstance(term, Var):
        return Var(term.index + by)
    if isinstance(term, Zero):
        return term
    if isinstance(term, Succ):
        return Succ(_copy_shifted_argument(term.term, by, counter, definition, column))
    if isinstance(term, Add):
        return Add(
            _copy_shifted_argument(term.left, by, counter, definition, column),
            _copy_shifted_argument(term.right, by, counter, definition, column),
        )
    if isinstance(term, Mul):
        return Mul(
            _copy_shifted_argument(term.left, by, counter, definition, column),
            _copy_shifted_argument(term.right, by, counter, definition, column),
        )
    raise TypeError("expected a PA term")


def _instantiate_term(
    term: Term,
    arguments: tuple[Term, ...],
    depth: int,
    counter: _ExpansionCounter,
    definition: DefinitionSpec,
    column: int,
) -> Term:
    if isinstance(term, Var):
        if term.index < depth:
            counter.node(definition, column)
            return term
        parameter_index = term.index - depth
        if parameter_index >= len(arguments):
            raise ValueError(
                f"definition {definition.name!r} template has an unbound variable slot"
            )
        return _copy_shifted_argument(
            arguments[parameter_index], depth, counter, definition, column
        )
    counter.node(definition, column)
    if isinstance(term, Zero):
        return term
    if isinstance(term, Succ):
        return Succ(
            _instantiate_term(
                term.term, arguments, depth, counter, definition, column
            )
        )
    if isinstance(term, Add):
        return Add(
            _instantiate_term(
                term.left, arguments, depth, counter, definition, column
            ),
            _instantiate_term(
                term.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(term, Mul):
        return Mul(
            _instantiate_term(
                term.left, arguments, depth, counter, definition, column
            ),
            _instantiate_term(
                term.right, arguments, depth, counter, definition, column
            ),
        )
    raise TypeError("expected a PA term")


def _instantiate_formula(
    formula: Formula,
    arguments: tuple[Term, ...],
    depth: int,
    counter: _ExpansionCounter,
    definition: DefinitionSpec,
    column: int,
) -> Formula:
    counter.node(definition, column)
    if isinstance(formula, Eq):
        return Eq(
            _instantiate_term(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_term(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, Bot):
        return formula
    if isinstance(formula, Imp):
        return Imp(
            _instantiate_formula(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_formula(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, And):
        return And(
            _instantiate_formula(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_formula(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, Or):
        return Or(
            _instantiate_formula(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_formula(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, Forall):
        return Forall(
            _instantiate_formula(
                formula.body, arguments, depth + 1, counter, definition, column
            )
        )
    if isinstance(formula, Exists):
        return Exists(
            _instantiate_formula(
                formula.body, arguments, depth + 1, counter, definition, column
            )
        )
    raise TypeError("expected a PA formula")


class _DefinedFormulaParser(_FormulaParser):
    def __init__(self, source: str, expansion_budget: int):
        super().__init__(source)
        self.expansion_counter = _ExpansionCounter(expansion_budget)

    def _atom(self) -> Formula:
        token = self.stream.peek()
        position = self.stream.position
        has_open_parenthesis = (
            position + 1 < len(self.stream.tokens)
            and self.stream.tokens[position + 1].text == "("
        )
        # S(...) remains ordinary successor-term syntax.  Every other
        # identifier followed immediately by '(' is a predicate call in this
        # opt-in grammar, so misspellings receive a direct, positioned error.
        if _is_identifier(token) and token != "S" and has_open_parenthesis:
            column = self.stream.column()
            name = self.stream.take()
            definition = DEFINITIONS_BY_NAME.get(name)
            if definition is None:
                raise ParseError(
                    f"unknown defined predicate {name!r} at column {column}"
                )
            self.stream.expect("(")
            arguments: list[Term] = []
            if self.stream.accept(")") is None:
                while True:
                    arguments.append(
                        _parse_term_from(self.stream, self.bound, self.free)
                    )
                    if self.stream.accept(")") is not None:
                        break
                    self.stream.expect(",")
            if len(arguments) != definition.arity:
                suffix = "argument" if definition.arity == 1 else "arguments"
                raise ParseError(
                    f"defined predicate {name!r} expects {definition.arity} {suffix}, "
                    f"got {len(arguments)} at column {column}"
                )
            return _instantiate_formula(
                definition.template_formula,
                tuple(arguments),
                0,
                self.expansion_counter,
                definition,
                column,
            )
        return super()._atom()


def parse_defined_formula_with_names(
    src: str,
    *,
    expansion_budget: int = DEFAULT_EXPANSION_BUDGET,
) -> tuple[Formula, tuple[str, ...]]:
    """Parse opt-in defined syntax and return its surface free-name table."""

    parser = _DefinedFormulaParser(src, expansion_budget)
    return parser.parse(), tuple(parser.free)


def parse_defined_formula_in_context(
    src: str,
    names: list[str],
    *,
    expansion_budget: int = DEFAULT_EXPANSION_BUDGET,
) -> Formula:
    """Parse defined syntax in an exact free-variable context."""

    if (
        not isinstance(names, list)
        or not all(isinstance(name, str) and _is_identifier(name) for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("context names must be distinct surface identifiers")
    parser = _DefinedFormulaParser(src, expansion_budget)
    parser.free = list(names)
    formula = parser.parse()
    if len(parser.free) != len(names):
        unknown = ", ".join(parser.free[len(names) :])
        raise ParseError(f"unknown term variable(s): {unknown}")
    return formula


def parse_defined_formula(
    src: str,
    *,
    expansion_budget: int = DEFAULT_EXPANSION_BUDGET,
) -> Formula:
    """Parse a formula with the fixed defined-predicate registry enabled."""

    return parse_defined_formula_with_names(
        src, expansion_budget=expansion_budget
    )[0]


__all__ = [
    "DefinitionSpec",
    "DEFINED_SYNTAX_REGISTRY_ID",
    "DEFINED_SYNTAX_VERSION",
    "DEFINED_SYNTAX_REGISTRY_SHA256",
    "DEFAULT_EXPANSION_BUDGET",
    "DEFINITIONS",
    "DEFINITIONS_BY_NAME",
    "parse_defined_formula",
    "parse_defined_formula_with_names",
    "parse_defined_formula_in_context",
]
