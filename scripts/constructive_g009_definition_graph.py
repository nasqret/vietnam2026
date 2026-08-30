"""Additive G009 expansion DAG; no new theorem or admission authority."""

from collections.abc import Mapping, Sequence
from typing import Any

# Load the scratch-safe registry first; it establishes the unchanged repo
# import roots without importing an Alpha edition or invoking any factory.
from constructive_g009_definitions import G009_REGISTRIES
import constructive_dirichlet_inverse_definition_graph as previous
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES = previous.DEFAULT_REGISTRIES + G009_REGISTRIES
# In particular, no Multiplicative(f) -> MultiplicativePrefix(N,F) alias.
REVIEWED_BLUEPRINT_ALIASES = previous.REVIEWED_BLUEPRINT_ALIASES
DefinitionGraphError = previous.DefinitionGraphError
SCHEMA = previous.SCHEMA


def reviewed_registry(registries: Sequence[tuple[str,Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES):
    return previous.reviewed_registry(registries)


def build_definition_graph(
    campaign: Mapping[str,Any], *,
    registries: Sequence[tuple[str,Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES,
    aliases: Mapping[str,tuple[str,tuple[int,...] | None]] = REVIEWED_BLUEPRINT_ALIASES,
) -> dict[str,Any]:
    return previous.build_definition_graph(campaign,registries=registries,aliases=aliases)


__all__ = ('DEFAULT_REGISTRIES','REVIEWED_BLUEPRINT_ALIASES','DefinitionGraphError',
           'SCHEMA','reviewed_registry','build_definition_graph')
