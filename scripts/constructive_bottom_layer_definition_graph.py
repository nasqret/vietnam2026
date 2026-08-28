"""Separate actual definition edges for local post-v30 proof development."""

from collections.abc import Mapping, Sequence
from typing import Any

import constructive_gaussian_factorization_definition_graph as historical
from constructive_bottom_layer_definitions import BOTTOM_LAYER_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES = historical.DEFAULT_REGISTRIES + BOTTOM_LAYER_REGISTRIES
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
    # Prime-field arithmetic must not become a silent alias for the blueprint's
    # full irreducible-polynomial/extension-field presentation FiniteField(F,p,k).
    return historical.build_definition_graph(campaign, registries=registries, aliases=aliases)


__all__ = (
    "DEFAULT_REGISTRIES", "DefinitionGraphError", "REVIEWED_BLUEPRINT_ALIASES",
    "SCHEMA", "build_definition_graph", "reviewed_registry",
)
