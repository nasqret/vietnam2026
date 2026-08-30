"""Additive Gaussian definition DAG, with no silent generic-ring aliases."""

from collections.abc import Mapping,Sequence
from typing import Any

import constructive_priority_layer_definition_graph as historical
from constructive_gaussian_factorization_definitions import GAUSSIAN_FACTORIZATION_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES=historical.DEFAULT_REGISTRIES+GAUSSIAN_FACTORIZATION_REGISTRIES
REVIEWED_BLUEPRINT_ALIASES=historical.REVIEWED_BLUEPRINT_ALIASES
DefinitionGraphError=historical.DefinitionGraphError
SCHEMA=historical.SCHEMA


def reviewed_registry(registries: Sequence[tuple[str,Sequence[DefinitionSpec]]]=DEFAULT_REGISTRIES):
    return historical.reviewed_registry(registries)


def build_definition_graph(campaign: Mapping[str,Any],*,registries: Sequence[tuple[str,Sequence[DefinitionSpec]]]=DEFAULT_REGISTRIES,aliases: Mapping[str,tuple[str,tuple[int,...]|None]]=REVIEWED_BLUEPRINT_ALIASES) -> dict[str,Any]:
    # The historical Convergent guard and all exact registry/AST/signature
    # checks remain in force.  No generic RingPrime or differently-encoded
    # GaussianFactorization planning predicate is automatically aliased here.
    return historical.build_definition_graph(campaign,registries=registries,aliases=aliases)


__all__=('DEFAULT_REGISTRIES','DefinitionGraphError','REVIEWED_BLUEPRINT_ALIASES','SCHEMA','build_definition_graph','reviewed_registry')
