"""Exact, conservative reading of priority-campaign statements and tactics."""

from functools import lru_cache
from hashlib import sha256
from types import FunctionType

from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_priority_layer_definitions import PRIORITY_LAYER_DEFINITIONS, definition_closure
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.library import bertrand_defined_edition as historical
from peano_lab.library.defined_edition import (
    DefinedEditionError, DefinitionUse, EquivalenceReceipt, FormulaCompaction, SurfacePart,
)


DEFINITIONS = definition_closure(tuple(dict.fromkeys((
    *(definition.name for definition in historical.ALL_BERTRAND_DEFINITIONS),
    *(definition.name for definition in PRIORITY_LAYER_DEFINITIONS),
    "PrimeFactorList", "ContinuedFraction",
))))
_COMPACTOR = _FormulaCompactor(DEFINITIONS)


@lru_cache(maxsize=128)
def compact_formula_source(source: str) -> FormulaCompaction:
    if not isinstance(source, str) or not source.strip():
        raise DefinedEditionError("formula source must be nonempty text")
    reading = _COMPACTOR.compact(source)
    exact, names = parse_formula_with_names(source)
    uses = reading["statement_definition_uses"]
    if uses:
        surface = reading["defined_statement"]
        parts = tuple(SurfacePart(part["kind"], part["text"], part.get("definition")) for part in reading["statement_parts"])
    else:
        surface, parts = source, (SurfacePart("text", source),)
    parser = _LocalDefinedParser(surface, _COMPACTOR.by_name)
    parser.free = list(names)
    expanded = parser.parse()
    if tuple(parser.free) != names or expanded != exact:
        raise DefinedEditionError("priority-layer notation changed the exact formula or free context")
    receipt = EquivalenceReceipt(
        expanded_source_sha256=sha256(source.encode()).hexdigest(),
        defined_source_sha256=sha256(surface.encode()).hexdigest(),
        canonical_expansion_sha256=sha256(pretty_formula(expanded, list(names)).encode()).hexdigest(),
        free_names=names,
        definition_uses=tuple(DefinitionUse(definition.stable_id, definition.name, uses[definition.stable_id])
                              for definition in DEFINITIONS if uses.get(definition.stable_id)),
        expanded_characters=len(source), defined_characters=len(surface),
        exact_ast_equivalence=True,
    )
    return FormulaCompaction(source, surface, parts, receipt)


_tactic_scope = dict(historical.compact_tactic_command.__globals__)
_tactic_scope["compact_formula_source"] = compact_formula_source
compact_tactic_command = FunctionType(
    historical.compact_tactic_command.__code__, _tactic_scope,
    historical.compact_tactic_command.__name__, historical.compact_tactic_command.__defaults__,
    historical.compact_tactic_command.__closure__,
)


__all__ = ("DEFINITIONS", "compact_formula_source", "compact_tactic_command")
