"""Exact inverse notation using the unchanged, scoped formula/tactic reader."""

from functools import lru_cache
from types import FunctionType

import constructive_dirichlet_defined_adapter as previous
from constructive_dirichlet_inverse_definitions import (
    DIRICHLET_INVERSE_DEFINITIONS, definition_closure,
)
from constructive_formula_compactor import _FormulaCompactor


DEFINITIONS = definition_closure(tuple(dict.fromkeys((
    *(item.name for item in previous.DEFINITIONS),
    *(item.name for item in DIRICHLET_INVERSE_DEFINITIONS),
    "ArithExtend",
))))
_COMPACTOR = _FormulaCompactor(DEFINITIONS)

# Each function resolves names in a private copied scope. Neither historical
# module globals nor the old adapter's cache or definition tuple are changed.
_formula_original = previous.compact_formula_source.__wrapped__
_formula_scope = dict(_formula_original.__globals__)
_formula_scope.update(DEFINITIONS=DEFINITIONS, _COMPACTOR=_COMPACTOR)
compact_formula_source = lru_cache(maxsize=128)(FunctionType(
    _formula_original.__code__, _formula_scope, _formula_original.__name__,
    _formula_original.__defaults__, _formula_original.__closure__,
))

_tactic_scope = dict(previous.compact_tactic_command.__globals__)
_tactic_scope["compact_formula_source"] = compact_formula_source
compact_tactic_command = FunctionType(
    previous.compact_tactic_command.__code__, _tactic_scope,
    previous.compact_tactic_command.__name__, previous.compact_tactic_command.__defaults__,
    previous.compact_tactic_command.__closure__,
)


__all__ = ("DEFINITIONS", "compact_formula_source", "compact_tactic_command")
