"""Conservative lower-layer notation DAG, preserving all historical identities."""

from collections.abc import Mapping, Sequence
from typing import Any

import constructive_second_wave_definition_graph as historical
from constructive_lower_layer_definitions import LOWER_LAYER_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES = historical.DEFAULT_REGISTRIES + LOWER_LAYER_REGISTRIES
REVIEWED_BLUEPRINT_ALIASES = historical.REVIEWED_BLUEPRINT_ALIASES
DefinitionGraphError = historical.DefinitionGraphError
SCHEMA = historical.SCHEMA


def reviewed_registry(registries: Sequence[tuple[str, Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES):
    return historical.reviewed_registry(registries)


def build_definition_graph(
    campaign: Mapping[str, Any], *,
    registries: Sequence[tuple[str, Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES,
    aliases: Mapping[str, tuple[str, tuple[int, ...] | None]] = REVIEWED_BLUEPRINT_ALIASES,
) -> dict[str, Any]:
    # Includes the original PD0047 page override, without altering its identity.
    return historical.build_definition_graph(campaign, registries=registries, aliases=aliases)


__all__ = (
    "DEFAULT_REGISTRIES", "DefinitionGraphError", "REVIEWED_BLUEPRINT_ALIASES",
    "SCHEMA", "build_definition_graph", "reviewed_registry",
)
