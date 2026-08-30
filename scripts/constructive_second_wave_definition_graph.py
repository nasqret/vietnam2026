"""Additive notation-DAG audit without changing either historical registry."""

from collections.abc import Mapping, Sequence
from typing import Any

import constructive_first_wave_definition_graph as historical
from constructive_second_wave_definitions import SECOND_WAVE_REGISTRIES
from peano_lab.library.defined_syntax import DefinitionSpec


DEFAULT_REGISTRIES = historical.DEFAULT_REGISTRIES + SECOND_WAVE_REGISTRIES
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
    result = historical.build_definition_graph(campaign, registries=registries, aliases=aliases)
    # PD0047 was registered with Bertrand but never appeared in that proof's
    # definition-page inventory. Reuse its identical old object/ID in the
    # relevant new valuation chapter. This is a navigation override, not a
    # change to any immutable reviewed record, template, or proof dependency.
    result["definition_page_overrides"] = {
        "PD0047": {"name": "PrimePowerValuation", "route": "multinomial-kummer",
                   "registry_route": "bertrand-postulate", "proof_authority": False}
    } if any(row["id"] == "PD0047" for row in result["reviewed_definitions"]) else {}
    return result


__all__ = (
    "DEFAULT_REGISTRIES", "DefinitionGraphError", "REVIEWED_BLUEPRINT_ALIASES",
    "SCHEMA", "build_definition_graph", "reviewed_registry",
)
