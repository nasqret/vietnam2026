"""Additive actual expansion DAG; no new broad campaign aliases."""

import constructive_lower_tier_definition_graph as previous
from constructive_lower_continuation_definitions import CONTINUATION_REGISTRIES


DEFAULT_REGISTRIES = previous.DEFAULT_REGISTRIES + CONTINUATION_REGISTRIES
REVIEWED_BLUEPRINT_ALIASES = previous.REVIEWED_BLUEPRINT_ALIASES
DefinitionGraphError = previous.DefinitionGraphError
SCHEMA = previous.SCHEMA


def reviewed_registry(registries=DEFAULT_REGISTRIES):
    return previous.reviewed_registry(registries)


def build_definition_graph(campaign, *, registries=DEFAULT_REGISTRIES, aliases=REVIEWED_BLUEPRINT_ALIASES):
    return previous.build_definition_graph(campaign, registries=registries, aliases=aliases)
