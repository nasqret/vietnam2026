"""Additive priority-campaign definition DAG with explicit planning errata."""

from collections.abc import Mapping, Sequence
from typing import Any

import constructive_lower_layer_definition_graph as historical
from constructive_priority_layer_definitions import PRIORITY_LAYER_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES = historical.DEFAULT_REGISTRIES + PRIORITY_LAYER_REGISTRIES
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
    planned = campaign.get("definitions", {}).get("Convergent", {})
    if planned.get("reviewed_definition_id") != "ND0205":
        # The v28 prose required u>0 and therefore omitted the genuine initial
        # convergent 0/1. A matching arity alone cannot repair that meaning.
        raise DefinitionGraphError("the old Convergent plan excludes 0/1; archive and refine it before linking the reviewed computation")
    return historical.build_definition_graph(campaign, registries=registries, aliases=aliases)


__all__ = (
    "DEFAULT_REGISTRIES", "DefinitionGraphError", "REVIEWED_BLUEPRINT_ALIASES",
    "SCHEMA", "build_definition_graph", "reviewed_registry",
)
