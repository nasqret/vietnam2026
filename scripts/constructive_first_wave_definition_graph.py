"""Add the preserved CF explorer identities without mutating the sealed v25 DAG.

The old graph module is part of immutable Alpha evidence.  Its audited graph
construction is reused in an isolated namespace; only the accepted identifier
set and the explicitly supplied registry grow.  Historical default calls still
produce exactly the 120-definition graph they originally authenticated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from types import FunctionType
from typing import Any

import constructive_definition_graph as historical
from constructive_first_wave_definitions import FIRST_WAVE_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES = historical.DEFAULT_REGISTRIES + FIRST_WAVE_REGISTRIES
REVIEWED_BLUEPRINT_ALIASES = historical.REVIEWED_BLUEPRINT_ALIASES
DefinitionGraphError = historical.DefinitionGraphError
SCHEMA = historical.SCHEMA

_registry_scope = dict(vars(historical))
_registry_scope["REVIEWED_ID"] = re.compile(r"(?:PD[0-9A-Y]{4}|ND[0-9]{4}|CF[0-9]{4})\Z")
_reviewed_registry = FunctionType(
    historical.reviewed_registry.__code__, _registry_scope,
    historical.reviewed_registry.__name__, historical.reviewed_registry.__defaults__,
    historical.reviewed_registry.__closure__,
)


def reviewed_registry(
    registries: Sequence[tuple[str, Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES,
) -> tuple[dict[str, dict[str, Any]], list[str], dict[str, int]]:
    """Audit the additive registry with the same parsed-expansion/DAG checks."""
    return _reviewed_registry(registries)


_graph_scope = dict(vars(historical))
_graph_scope["reviewed_registry"] = reviewed_registry
_build_definition_graph = FunctionType(
    historical.build_definition_graph.__code__, _graph_scope,
    historical.build_definition_graph.__name__, historical.build_definition_graph.__defaults__,
    historical.build_definition_graph.__closure__,
)
_build_definition_graph.__kwdefaults__ = historical.build_definition_graph.__kwdefaults__


def build_definition_graph(
    campaign: Mapping[str, Any], *,
    registries: Sequence[tuple[str, Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES,
    aliases: Mapping[str, tuple[str, tuple[int, ...] | None]] = REVIEWED_BLUEPRINT_ALIASES,
) -> dict[str, Any]:
    return _build_definition_graph(campaign, registries=registries, aliases=aliases)


__all__ = (
    "DEFAULT_REGISTRIES", "DefinitionGraphError", "REVIEWED_BLUEPRINT_ALIASES",
    "SCHEMA", "build_definition_graph", "reviewed_registry",
)
