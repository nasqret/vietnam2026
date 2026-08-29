"""Additive exact definition DAG for local Dirichlet convolution proofs.

Inherited blueprint aliases and every historical definition record are
unchanged. These are expansion edges, never theorem-proof prerequisites or
an Alpha/publication/milestone promotion mechanism.
"""

from collections.abc import Mapping,Sequence
from typing import Any

import constructive_lower_continuation_definition_graph as previous
from constructive_dirichlet_definitions import DIRICHLET_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES=previous.DEFAULT_REGISTRIES+DIRICHLET_REGISTRIES
REVIEWED_BLUEPRINT_ALIASES=previous.REVIEWED_BLUEPRINT_ALIASES
DefinitionGraphError=previous.DefinitionGraphError
SCHEMA=previous.SCHEMA


def reviewed_registry(registries: Sequence[tuple[str,Sequence[DefinitionSpec]]]=DEFAULT_REGISTRIES):
    return previous.reviewed_registry(registries)


def build_definition_graph(
    campaign: Mapping[str,Any], *,
    registries: Sequence[tuple[str,Sequence[DefinitionSpec]]]=DEFAULT_REGISTRIES,
    aliases: Mapping[str,tuple[str,tuple[int,...]|None]]=REVIEWED_BLUEPRINT_ALIASES,
) -> dict[str,Any]:
    return previous.build_definition_graph(campaign,registries=registries,aliases=aliases)


__all__=("DEFAULT_REGISTRIES","REVIEWED_BLUEPRINT_ALIASES","DefinitionGraphError",
         "SCHEMA","reviewed_registry","build_definition_graph")
