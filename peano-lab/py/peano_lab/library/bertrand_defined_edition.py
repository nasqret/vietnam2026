"""Conservative campaign-local defined notation for the Bertrand proof.

The shared quadratic-reciprocity notation registry is deliberately immutable.
This module adds a *presentation-only* Bertrand registry whose templates are
obtained directly from the reviewed, fully expanded authoring relations.  Both
the renderer and its opt-in parser live here; neither modifies the ordinary
Peano parser, trusted kernel, theorem registry, or shared QR definitions.

Every compacted statement and local tactic proposition is parsed again with
these definitions expanded immediately, and its de Bruijn formula must equal
the exact original formula before a display receipt is issued.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from functools import lru_cache
from hashlib import sha256
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    _as_le,
    _fresh_binder,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.kernel.terms import (
    ParseError,
    Term,
    _is_identifier,
    _parse_term_from,
    _pretty_term,
)

from .bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
)
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_choose_foundation_candidate import _choose_relation_term
from .bertrand_factorial_valuation_candidate import factorial_valuation
from .bertrand_legendre_sum_candidate import legendre_sum, power_quotient_prefix
from .bertrand_power_valuation_candidate import (
    bounded_power_valuation,
    power_divides,
    power_valuation,
    prime_power_valuation,
)
from .bertrand_primorial_foundation_candidate import _primorial_relation_term
from .defined_edition import (
    DEFINED_EDITION_EXPANSION_BUDGET,
    DefinedEditionError,
    DefinitionUse,
    EquivalenceReceipt,
    FormulaCompaction,
    SurfacePart,
    TacticCompaction,
    _append_part,
    _definition_json_records,
    _formula_nodes,
    _leading_source_binders,
    _match_formula,
)
from .defined_syntax import (
    DEFINITIONS as SHARED_DEFINITIONS,
    DefinitionSpec,
    _DefinedFormulaParser,
    _definition,
    _instantiate_formula,
)


_REPO_ROOT = Path(__file__).resolve().parents[4]


def _campaign_definition(
    *,
    stable_id: str,
    name: str,
    parameters: tuple[str, ...],
    template_source: str,
    summary: str,
    category: str,
    conceptual_dependencies: tuple[str, ...],
) -> DefinitionSpec:
    """Build an immutable template with the same validation as shared syntax."""

    return _definition(
        stable_id=stable_id,
        name=name,
        parameters=parameters,
        template_source=template_source,
        summary=summary,
        category=category,
        priority="P2",
        conceptual_dependencies=conceptual_dependencies,
    )


_CAMPAIGN_RECORDS: tuple[tuple[DefinitionSpec, Callable[..., Any]], ...] = (
    (
        _campaign_definition(
            stable_id="PD0041",
            name="Choose",
            parameters=("n", "k", "z"),
            template_source=_choose_relation_term(
                "n",
                "k",
                "z",
                tag="bertrand_defined_choose",
                variables=("n", "k", "z"),
            ),
            summary=(
                "z is the recurrence-defined binomial coefficient of row n "
                "and column k."
            ),
            category="bertrand_binomial",
            conceptual_dependencies=("Le", "Lt", "BetaAt"),
        ),
        _choose_relation_term,
    ),
    (
        _campaign_definition(
            stable_id="PD0042",
            name="CentralBinom",
            parameters=("n", "z"),
            template_source=_central_binom_relation_term(
                "n",
                "z",
                tag="bertrand_defined_central_binom",
                variables=("n", "z"),
            ),
            summary="z is the central binomial coefficient Choose(2n,n).",
            category="bertrand_binomial",
            conceptual_dependencies=("Choose",),
        ),
        _central_binom_relation_term,
    ),
    (
        _campaign_definition(
            stable_id="PD0043",
            name="Primorial",
            parameters=("n", "z"),
            template_source=_primorial_relation_term(
                "n",
                "z",
                tag="bertrand_defined_primorial",
                variables=("n", "z"),
            ),
            summary="z is the finite product of the primes at most n.",
            category="bertrand_prime_products",
            conceptual_dependencies=("Prime", "BetaAt", "Product"),
        ),
        _primorial_relation_term,
    ),
    (
        _campaign_definition(
            stable_id="PD0044",
            name="PowerDivides",
            parameters=("p", "e", "n"),
            template_source=power_divides(
                "p", "e", "n", tag="bertrand_defined_power_divides"
            ),
            summary="The relational power p to exponent e divides n.",
            category="bertrand_valuations",
            conceptual_dependencies=("Dvd", "Pow"),
        ),
        power_divides,
    ),
    (
        _campaign_definition(
            stable_id="PD0045",
            name="BoundedPowerValuation",
            parameters=("p", "n", "b", "e"),
            template_source=bounded_power_valuation(
                "p", "n", "b", "e", tag="bertrand_defined_bounded_valuation"
            ),
            summary=(
                "e is the greatest exponent at most b for which p to that "
                "exponent divides n."
            ),
            category="bertrand_valuations",
            conceptual_dependencies=("Le", "PowerDivides"),
        ),
        bounded_power_valuation,
    ),
    (
        _campaign_definition(
            stable_id="PD0046",
            name="PowerValuation",
            parameters=("p", "n", "e"),
            template_source=power_valuation(
                "p", "n", "e", tag="bertrand_defined_power_valuation"
            ),
            summary="e is the canonical bounded p-adic power valuation of n.",
            category="bertrand_valuations",
            conceptual_dependencies=("BoundedPowerValuation",),
        ),
        power_valuation,
    ),
    (
        _campaign_definition(
            stable_id="PD0047",
            name="PrimePowerValuation",
            parameters=("p", "n", "e"),
            template_source=prime_power_valuation(
                "p", "n", "e", tag="bertrand_defined_prime_power_valuation"
            ),
            summary=(
                "p is prime, n is nonzero, and e is the bounded p-adic "
                "valuation of n."
            ),
            category="bertrand_valuations",
            conceptual_dependencies=("Prime", "PowerValuation"),
        ),
        prime_power_valuation,
    ),
    (
        _campaign_definition(
            stable_id="PD0048",
            name="FactorialValuation",
            parameters=("p", "n", "e"),
            template_source=factorial_valuation(
                "p", "n", "e", tag="bertrand_defined_factorial_valuation"
            ),
            summary="e is the bounded p-adic valuation of the factorial n!.",
            category="bertrand_valuations",
            conceptual_dependencies=("Factorial", "PowerValuation"),
        ),
        factorial_valuation,
    ),
    (
        _campaign_definition(
            stable_id="PD0049",
            name="PowerQuotPrefix",
            parameters=("p", "n", "b", "c", "l"),
            template_source=power_quotient_prefix(
                "p", "n", "b", "c", "l", tag="bertrand_defined_power_quotients"
            ),
            summary=(
                "The beta-coded prefix stores the quotients of n by the "
                "first l positive powers of p."
            ),
            category="bertrand_legendre",
            conceptual_dependencies=("DivRem", "BetaAt", "Pow"),
        ),
        power_quotient_prefix,
    ),
    (
        _campaign_definition(
            stable_id="PD0050",
            name="LegendreSum",
            parameters=("p", "n", "e"),
            template_source=legendre_sum(
                "p", "n", "e", tag="bertrand_defined_legendre_sum"
            ),
            summary=(
                "e is the finite Legendre sum of the quotients of n by "
                "positive powers of p."
            ),
            category="bertrand_legendre",
            conceptual_dependencies=("Sum", "PowerQuotPrefix"),
        ),
        legendre_sum,
    ),
    (
        _campaign_definition(
            stable_id="PD0051",
            name="FloorSqrt",
            parameters=("n", "s"),
            template_source=floor_sqrt_relation(
                "n", "s", tag="bertrand_defined_floor_sqrt"
            ),
            summary="s is the integer floor square root: s² ≤ n < (s+1)².",
            category="bertrand_bounds",
            conceptual_dependencies=("Le", "Lt"),
        ),
        floor_sqrt_relation,
    ),
    (
        _campaign_definition(
            stable_id="PD0052",
            name="CeilDivSix",
            parameters=("n", "q"),
            template_source=ceil_div_six_relation(
                "n", "q", tag="bertrand_defined_ceil_div_six"
            ),
            summary="q is the ceiling of n divided by six.",
            category="bertrand_bounds",
            conceptual_dependencies=("Le", "Lt"),
        ),
        ceil_div_six_relation,
    ),
)

BERTRAND_DEFINITIONS: tuple[DefinitionSpec, ...] = tuple(
    definition for definition, _source in _CAMPAIGN_RECORDS
)
ALL_BERTRAND_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    *SHARED_DEFINITIONS,
    *BERTRAND_DEFINITIONS,
)
BERTRAND_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.name: definition for definition in ALL_BERTRAND_DEFINITIONS}
)

if len(BERTRAND_DEFINITIONS_BY_NAME) != len(ALL_BERTRAND_DEFINITIONS):
    raise DefinedEditionError("campaign definitions duplicate a shared name")
if len({row.stable_id for row in ALL_BERTRAND_DEFINITIONS}) != len(
    ALL_BERTRAND_DEFINITIONS
):
    raise DefinedEditionError("campaign definitions duplicate a stable ID")


def _formula_shape(formula: Formula, depth: int = 4) -> tuple[object, ...]:
    """A cheap, parameter-independent prefix that indexes template matches."""

    if depth <= 0:
        return (type(formula),)
    if isinstance(formula, (And, Or, Imp)):
        return (
            type(formula),
            _formula_shape(formula.left, depth - 1),
            _formula_shape(formula.right, depth - 1),
        )
    if isinstance(formula, (Forall, Exists)):
        return (type(formula), _formula_shape(formula.body, depth - 1))
    return (type(formula),)


_MATCH_ORDER = tuple(
    sorted(
        enumerate(ALL_BERTRAND_DEFINITIONS),
        key=lambda item: (
            -_formula_nodes(item[1].template_formula),
            item[1].arity,
            item[0],
        ),
    )
)
_MATCH_BY_SHAPE: Mapping[tuple[object, ...], tuple[DefinitionSpec, ...]] = (
    MappingProxyType(
        {
            shape: tuple(
                definition
                for _index, definition in _MATCH_ORDER
                if _formula_shape(definition.template_formula) == shape
            )
            for shape in {
                _formula_shape(definition.template_formula)
                for definition in ALL_BERTRAND_DEFINITIONS
            }
        }
    )
)


def _definition_match(
    formula: Formula,
) -> tuple[DefinitionSpec, tuple[Term, ...]] | None:
    for definition in _MATCH_BY_SHAPE.get(_formula_shape(formula), ()):
        bindings: list[Term | None] = [None] * definition.arity
        if _match_formula(
            definition.template_formula,
            formula,
            depth=0,
            arity=definition.arity,
            bindings=bindings,
        ) and all(binding is not None for binding in bindings):
            return definition, tuple(
                binding for binding in bindings if binding is not None
            )
    return None


class _BertrandDefinedFormulaParser(_DefinedFormulaParser):
    """Opt-in defined parser with a campaign-local immutable definition map."""

    def _atom(self) -> Formula:
        token = self.stream.peek()
        position = self.stream.position
        has_open_parenthesis = (
            position + 1 < len(self.stream.tokens)
            and self.stream.tokens[position + 1].text == "("
        )
        if _is_identifier(token) and token != "S" and has_open_parenthesis:
            column = self.stream.column()
            name = self.stream.take()
            definition = BERTRAND_DEFINITIONS_BY_NAME.get(name)
            if definition is None:
                raise ParseError(
                    f"unknown Bertrand defined predicate {name!r} "
                    f"at column {column}"
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
                    f"defined predicate {name!r} expects {definition.arity} "
                    f"{suffix}, got {len(arguments)} at column {column}"
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


def parse_bertrand_defined_formula_with_names(
    source: str,
    *,
    expansion_budget: int = DEFINED_EDITION_EXPANSION_BUDGET,
) -> tuple[Formula, tuple[str, ...]]:
    """Expand shared and Bertrand-only calls into an ordinary PA formula."""

    parser = _BertrandDefinedFormulaParser(source, expansion_budget)
    return parser.parse(), tuple(parser.free)


def parse_bertrand_defined_formula_in_context(
    source: str,
    names: list[str],
    *,
    expansion_budget: int = DEFINED_EDITION_EXPANSION_BUDGET,
) -> Formula:
    """Expand campaign notation while rejecting unknown free variables."""

    if (
        not isinstance(names, list)
        or not all(isinstance(name, str) and _is_identifier(name) for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("context names must be distinct surface identifiers")
    parser = _BertrandDefinedFormulaParser(source, expansion_budget)
    parser.free = list(names)
    formula = parser.parse()
    if len(parser.free) != len(names):
        unknown = ", ".join(parser.free[len(names) :])
        raise ParseError(f"unknown term variable(s): {unknown}")
    return formula


def _render_formula_parts(
    formula: Formula,
    names: list[str],
    parent_precedence: int,
    uses: Counter[str],
    leading_binders: list[tuple[type[Formula], str]] | None = None,
) -> list[SurfacePart]:
    match = _definition_match(formula)
    if match is not None:
        definition, arguments = match
        text = (
            f"{definition.name}("
            + ",".join(_pretty_term(argument, names, 0) for argument in arguments)
            + ")"
        )
        uses[definition.name] += 1
        parts = [SurfacePart("definition", text, definition.stable_id)]
        level = 5
    else:
        le_terms = _as_le(formula)
        if le_terms is not None:
            lower, upper = le_terms
            parts = [
                SurfacePart(
                    "text",
                    f"{_pretty_term(lower, names, 0)} ≤ "
                    f"{_pretty_term(upper, names, 0)}",
                )
            ]
            level = 5
        elif isinstance(formula, Eq):
            parts = [
                SurfacePart(
                    "text",
                    f"{_pretty_term(formula.left, names, 0)} = "
                    f"{_pretty_term(formula.right, names, 0)}",
                )
            ]
            level = 5
        elif isinstance(formula, Bot):
            parts, level = [SurfacePart("text", "⊥")], 5
        elif isinstance(formula, Imp) and isinstance(formula.right, Bot):
            parts = [SurfacePart("text", "¬")]
            for part in _render_formula_parts(formula.left, names, 4, uses):
                _append_part(parts, part.text, part.definition_id)
            level = 4
        elif isinstance(formula, (And, Or, Imp)):
            if isinstance(formula, And):
                level, symbol = 3, "∧"
            elif isinstance(formula, Or):
                level, symbol = 2, "∨"
            else:
                level, symbol = 1, "→"
            parts = _render_formula_parts(
                formula.left,
                names,
                level + (1 if isinstance(formula, Imp) else 0),
                uses,
            )
            _append_part(parts, f" {symbol} ")
            right_level = level if isinstance(formula, Imp) else level + 1
            if isinstance(formula, Imp) and isinstance(
                formula.right, (Forall, Exists)
            ):
                right_level = 0
            for part in _render_formula_parts(
                formula.right, names, right_level, uses
            ):
                _append_part(parts, part.text, part.definition_id)
        elif isinstance(formula, (Forall, Exists)):
            binder = _fresh_binder(names)
            if leading_binders and leading_binders[0][0] is type(formula):
                _quantifier, preferred = leading_binders.pop(0)
                if preferred not in names:
                    binder = preferred
            symbol = "∀" if isinstance(formula, Forall) else "∃"
            parts = [SurfacePart("text", f"{symbol} {binder}. ")]
            for part in _render_formula_parts(
                formula.body,
                [binder] + names,
                0,
                uses,
                leading_binders,
            ):
                _append_part(parts, part.text, part.definition_id)
            level = 0
        else:
            raise TypeError("expected a PA formula")

    if level < parent_precedence:
        wrapped: list[SurfacePart] = [SurfacePart("text", "(")]
        for part in parts:
            _append_part(wrapped, part.text, part.definition_id)
        _append_part(wrapped, ")")
        return wrapped
    return parts


def _uses(counter: Counter[str]) -> tuple[DefinitionUse, ...]:
    return tuple(
        DefinitionUse(definition.stable_id, definition.name, counter[definition.name])
        for definition in ALL_BERTRAND_DEFINITIONS
        if counter[definition.name]
    )


@lru_cache(maxsize=128)
def compact_formula_source(source: str) -> FormulaCompaction:
    """Compact reviewed Bertrand relations and verify exact AST expansion."""

    if not isinstance(source, str) or not source.strip():
        raise DefinedEditionError("formula source must be nonempty text")
    expanded_formula, names = parse_formula_with_names(source)
    counter: Counter[str] = Counter()
    parts = tuple(
        _render_formula_parts(
            expanded_formula,
            list(names),
            0,
            counter,
            _leading_source_binders(source),
        )
    )
    if not parts:
        raise DefinedEditionError("Bertrand formula renderer produced no surface parts")
    if counter:
        defined_source = "".join(part.text for part in parts)
    else:
        defined_source = source
        parts = (SurfacePart("text", source),)
    expanded_again = parse_bertrand_defined_formula_in_context(
        defined_source,
        list(names),
        expansion_budget=DEFINED_EDITION_EXPANSION_BUDGET,
    )
    if expanded_again != expanded_formula:
        raise DefinedEditionError(
            "Bertrand defined formula did not expand to its original AST"
        )
    canonical = pretty_formula(expanded_again, list(names))
    receipt = EquivalenceReceipt(
        expanded_source_sha256=sha256(source.encode("utf-8")).hexdigest(),
        defined_source_sha256=sha256(defined_source.encode("utf-8")).hexdigest(),
        canonical_expansion_sha256=sha256(canonical.encode("utf-8")).hexdigest(),
        free_names=names,
        definition_uses=_uses(counter),
        expanded_characters=len(source),
        defined_characters=len(defined_source),
        exact_ast_equivalence=True,
    )
    return FormulaCompaction(source, defined_source, parts, receipt)


def compact_tactic_command(command: str, line_number: int = 1) -> TacticCompaction:
    """Compact only local have/suffices propositions, preserving every replay."""

    if not isinstance(command, str) or not command.strip():
        raise DefinedEditionError("tactic command must be nonempty text")
    pieces = command.strip().split(maxsplit=1)
    tactic = pieces[0]
    if tactic not in {"have", "suffices"}:
        return TacticCompaction(
            line_number,
            tactic,
            command,
            command,
            (SurfacePart("text", command),),
            None,
            None,
        )
    args = pieces[1] if len(pieces) == 2 else ""
    name_source, separator, proposition_source = args.partition(":")
    if not separator or not name_source.strip() or not proposition_source.strip():
        raise DefinedEditionError(
            f"malformed {tactic} command on line {line_number}: "
            "expected name : proposition"
        )
    proposition = compact_formula_source(proposition_source.strip())
    local_name = name_source.strip()
    if not proposition.receipt.definition_uses:
        return TacticCompaction(
            line_number,
            tactic,
            command,
            command,
            (SurfacePart("text", command),),
            local_name,
            proposition,
        )
    prefix = f"{tactic} {local_name} : "
    parts: list[SurfacePart] = [SurfacePart("text", prefix)]
    for part in proposition.parts:
        _append_part(parts, part.text, part.definition_id)
    defined = "".join(part.text for part in parts)
    return TacticCompaction(
        line_number,
        tactic,
        command,
        defined,
        tuple(parts),
        local_name,
        proposition,
    )


def definition_json_records() -> list[dict[str, object]]:
    """Return shared and campaign-local definitions in dependency order."""

    records = _definition_json_records()
    ids_by_name = {
        definition.name: definition.stable_id
        for definition in ALL_BERTRAND_DEFINITIONS
    }
    source_receipts: dict[Path, str] = {}
    preceding = {str(record["id"]) for record in records}
    for definition, source_function in _CAMPAIGN_RECORDS:
        source_file = inspect.getsourcefile(source_function)
        if source_file is None:
            raise DefinedEditionError(
                f"cannot locate Bertrand definition source for {definition.name!r}"
            )
        source_path = Path(source_file).resolve()
        source_sha = source_receipts.setdefault(
            source_path,
            sha256(source_path.read_bytes()).hexdigest(),
        )
        source_line = inspect.getsourcelines(source_function)[1]
        dependencies = [
            ids_by_name[dependency]
            for dependency in definition.conceptual_dependencies
        ]
        if any(dependency not in preceding for dependency in dependencies):
            raise DefinedEditionError(
                f"Bertrand definition {definition.name!r} has a forward dependency"
            )
        records.append(
            {
                "id": definition.stable_id,
                "name": definition.name,
                "signature": (
                    f"{definition.name}({','.join(definition.parameters)})"
                ),
                "summary": definition.summary,
                "expansion": definition.template_source,
                "expansion_sha256": sha256(
                    definition.template_source.encode("utf-8")
                ).hexdigest(),
                "dependencies": dependencies,
                "source": {
                    "path": source_path.relative_to(_REPO_ROOT).as_posix(),
                    "line": source_line,
                    "sha256": source_sha,
                },
            }
        )
        preceding.add(definition.stable_id)
    return records


__all__ = [
    "ALL_BERTRAND_DEFINITIONS",
    "BERTRAND_DEFINITIONS",
    "BERTRAND_DEFINITIONS_BY_NAME",
    "compact_formula_source",
    "compact_tactic_command",
    "definition_json_records",
    "parse_bertrand_defined_formula_in_context",
    "parse_bertrand_defined_formula_with_names",
]
