"""Standalone copy of the established exact, hygienic display compactor.

The implementation is extracted from the canonical next-layer explorer.
Keeping presentation-only parsing separate avoids importing every historical
Alpha edition merely to render one formula. This module grants no authority.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from typing import Any

from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Formula, Imp, Or, _as_le, _fresh_binder,
    parse_formula_with_names,
)
from peano_lab.kernel.terms import (
    ParseError, Term, _is_identifier, _parse_term_from, _pretty_term,
)
from peano_lab.library.bertrand_defined_edition import _formula_shape
from peano_lab.library.defined_edition import (
    _formula_nodes, _leading_source_binders, _match_formula,
)
from peano_lab.library.defined_syntax import (
    DefinitionSpec, _DefinedFormulaParser, _instantiate_formula,
)

MAX_DEFINED_EXPANSION_NODES = 1_000_000


class ConservativeCompactionError(ValueError):
    """An alias changed an exact formula, binder, or definition-use receipt."""


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class _LocalDefinedParser(_DefinedFormulaParser):
    """Opt-in, isolated parser for only one family's conservative aliases."""

    def __init__(self, source: str, definitions: Mapping[str, DefinitionSpec]):
        super().__init__(source, MAX_DEFINED_EXPANSION_NODES)
        self._definitions = definitions

    def _atom(self) -> Formula:
        token = self.stream.peek()
        position = self.stream.position
        opened = (
            position + 1 < len(self.stream.tokens)
            and self.stream.tokens[position + 1].text == "("
        )
        if _is_identifier(token) and token != "S" and opened:
            column = self.stream.column()
            name = self.stream.take()
            definition = self._definitions.get(name)
            if definition is None:
                raise ParseError(f"unknown local definition {name!r} at column {column}")
            self.stream.expect("(")
            arguments: list[Term] = []
            if self.stream.accept(")") is None:
                while True:
                    arguments.append(_parse_term_from(self.stream, self.bound, self.free))
                    if self.stream.accept(")") is not None:
                        break
                    self.stream.expect(",")
            if len(arguments) != definition.arity:
                raise ParseError(
                    f"definition {name!r} expects {definition.arity} arguments, "
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


def _parts_append(
    parts: list[dict[str, str]],
    text: str,
    *,
    definition: str | None = None,
) -> None:
    if not text:
        return
    if definition is None and parts and parts[-1]["kind"] == "text":
        parts[-1]["text"] += text
    elif definition is None:
        parts.append({"kind": "text", "text": text})
    else:
        parts.append({"kind": "definition", "text": text, "definition": definition})


class _FormulaCompactor:
    """Render reviewed/new notation and require exact binder-safe AST equality."""

    def __init__(self, definitions: Sequence[DefinitionSpec]) -> None:
        self.by_name = {definition.name: definition for definition in definitions}
        if len(self.by_name) != len(definitions):
            raise ConservativeCompactionError("local definitions repeat a surface name")
        sorted_definitions = sorted(
            enumerate(definitions),
            key=lambda item: (-_formula_nodes(item[1].template_formula), item[0]),
        )
        self.by_shape: dict[tuple[object, ...], list[DefinitionSpec]] = {}
        for _position, definition in sorted_definitions:
            self.by_shape.setdefault(_formula_shape(definition.template_formula), []).append(
                definition
            )

    def _match(self, formula: Formula) -> tuple[DefinitionSpec, tuple[Term, ...]] | None:
        for definition in self.by_shape.get(_formula_shape(formula), ()):
            bindings: list[Term | None] = [None] * definition.arity
            if _match_formula(
                definition.template_formula,
                formula,
                depth=0,
                arity=definition.arity,
                bindings=bindings,
            ) and all(binding is not None for binding in bindings):
                return definition, tuple(value for value in bindings if value is not None)
        return None

    def _render(
        self,
        formula: Formula,
        names: list[str],
        parent_precedence: int,
        uses: Counter[str],
        binders: list[tuple[type[Formula], str]] | None = None,
    ) -> list[dict[str, str]]:
        found = self._match(formula)
        if found is not None:
            definition, arguments = found
            text = (
                definition.name
                + "("
                + ",".join(_pretty_term(argument, names, 0) for argument in arguments)
                + ")"
            )
            uses[definition.stable_id] += 1
            parts = [{"kind": "definition", "definition": definition.stable_id, "text": text}]
            precedence = 5
        else:
            weak_order = _as_le(formula)
            if weak_order is not None:
                lower, upper = weak_order
                parts = [{"kind": "text", "text": (
                    f"{_pretty_term(lower, names, 0)} ≤ {_pretty_term(upper, names, 0)}"
                )}]
                precedence = 5
            elif isinstance(formula, Eq):
                parts = [{"kind": "text", "text": (
                    f"{_pretty_term(formula.left, names, 0)} = "
                    f"{_pretty_term(formula.right, names, 0)}"
                )}]
                precedence = 5
            elif isinstance(formula, Bot):
                parts, precedence = [{"kind": "text", "text": "⊥"}], 5
            elif isinstance(formula, Imp) and isinstance(formula.right, Bot):
                parts = [{"kind": "text", "text": "¬"}]
                for item in self._render(formula.left, names, 4, uses):
                    _parts_append(parts, item["text"], definition=item.get("definition"))
                precedence = 4
            elif isinstance(formula, (And, Or, Imp)):
                if isinstance(formula, And):
                    precedence, symbol = 3, "∧"
                elif isinstance(formula, Or):
                    precedence, symbol = 2, "∨"
                else:
                    precedence, symbol = 1, "→"
                parts = self._render(
                    formula.left,
                    names,
                    precedence + (1 if isinstance(formula, Imp) else 0),
                    uses,
                )
                _parts_append(parts, f" {symbol} ")
                right_precedence = precedence if isinstance(formula, Imp) else precedence + 1
                if isinstance(formula, Imp) and isinstance(formula.right, (Forall, Exists)):
                    right_precedence = 0
                for item in self._render(formula.right, names, right_precedence, uses):
                    _parts_append(parts, item["text"], definition=item.get("definition"))
            elif isinstance(formula, (Forall, Exists)):
                binder = _fresh_binder(names)
                if binders and binders[0][0] is type(formula):
                    _quantifier, preferred = binders.pop(0)
                    if preferred not in names:
                        binder = preferred
                symbol = "∀" if isinstance(formula, Forall) else "∃"
                parts = [{"kind": "text", "text": f"{symbol} {binder}. "}]
                for item in self._render(formula.body, [binder] + names, 0, uses, binders):
                    _parts_append(parts, item["text"], definition=item.get("definition"))
                precedence = 0
            else:
                raise TypeError("expected an ordinary first-order Heyting-arithmetic formula")
        if precedence < parent_precedence:
            wrapped = [{"kind": "text", "text": "("}]
            for item in parts:
                _parts_append(wrapped, item["text"], definition=item.get("definition"))
            _parts_append(wrapped, ")")
            return wrapped
        return parts

    def compact(self, source: str) -> dict[str, Any]:
        exact, free_names = parse_formula_with_names(source)
        uses: Counter[str] = Counter()
        parts = self._render(
            exact,
            list(free_names),
            0,
            uses,
            _leading_source_binders(source),
        )
        surface = "".join(part["text"] for part in parts)
        parser = _LocalDefinedParser(surface, self.by_name)
        parser.free = list(free_names)
        expanded = parser.parse()
        if tuple(parser.free) != free_names or expanded != exact:
            raise ConservativeCompactionError(
                "local defined notation does not expand to the exact native formula"
            )
        if Counter(
            part["definition"] for part in parts if part["kind"] == "definition"
        ) != uses:
            raise ConservativeCompactionError("defined theorem tokens do not match their use receipt")
        return {
            "defined_statement": surface,
            "expanded_statement_sha256": _digest(source),
            "defined_statement_sha256": _digest(surface),
            "statement_parts": parts,
            "statement_definition_uses": dict(sorted(uses.items())),
            "script_definition_uses": {},
            "definition_uses": dict(sorted(uses.items())),
            "exact_ast_equivalence": True,
            "free_names": list(free_names),
        }



