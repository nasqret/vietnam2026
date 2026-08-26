#!/usr/bin/env python3
"""Build the evidence-honest, layered constructive-number-theory definition DAG.

Blueprint descriptions are research vocabulary, never kernel definitions.  A
reviewed-registry link is allowed only after validating its identifier, parsed
first-order expansion, dependency DAG, argument arity, and explicit argument
alignment.  This module deliberately keeps notation edges separate from proof
dependencies and records incompatible homonyms instead of silently conflating
them.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.library.bertrand_defined_edition import (  # noqa: E402
    BERTRAND_DEFINITIONS,
)
from peano_lab.library.defined_syntax import DEFINITIONS, DefinitionSpec  # noqa: E402
from constructive_advanced_layer_definitions import ADVANCED_LAYER_REGISTRIES  # noqa: E402
from constructive_milestone_closure_definitions import MILESTONE_CLOSURE_REGISTRIES  # noqa: E402
from constructive_next_layer_definitions import NEXT_LAYER_REGISTRIES  # noqa: E402
from constructive_research_layer_definitions import RESEARCH_LAYER_REGISTRIES  # noqa: E402
from constructive_transport_layer_definitions import TRANSPORT_LAYER_REGISTRIES  # noqa: E402


SCHEMA = "constructive-number-theory-definition-dag-v1"
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
REVIEWED_ID = re.compile(r"(?:PD[0-9A-Y]{4}|ND[0-9]{4})\Z")
TOKENS = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

# Values list the position in the blueprint signature of each reviewed
# argument.  Thus IsGCD(g,a,b) is Gcd(a,b,g) with permutation [2,0,1].
REVIEWED_BLUEPRINT_ALIASES: dict[str, tuple[str, tuple[int, ...] | None]] = {
    "Beta": ("BetaAt", (0, 1, 2, 3)),
    "Binom": ("Choose", (0, 1, 2)),
    "Fact": ("Factorial", (0, 1)),
    "Gcd": ("IsGCD", (2, 0, 1)),
    # Product is a four-argument beta-code relation; the blueprint's Prod is a
    # three-argument list relation.  Keep the attempted correspondence visible,
    # but never grant it checked-definition evidence.
    "Prod": ("Product", None),
}

DEFAULT_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    ("quadratic-reciprocity", DEFINITIONS),
    ("bertrand-postulate", BERTRAND_DEFINITIONS),
) + (
    NEXT_LAYER_REGISTRIES
    + ADVANCED_LAYER_REGISTRIES
    + TRANSPORT_LAYER_REGISTRIES
    + MILESTONE_CLOSURE_REGISTRIES
    + RESEARCH_LAYER_REGISTRIES
)


class DefinitionGraphError(ValueError):
    """A blueprint definition or checked registry violates the DAG contract."""


def _digest(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return sha256(payload).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _identifier(value: object, *, context: str) -> str:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise DefinitionGraphError(f"{context} must be a valid identifier")
    return value


def _parameters(value: object, *, context: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise DefinitionGraphError(f"{context} must be an ordered parameter list")
    parameters = tuple(
        _identifier(parameter, context=f"{context}[{index}]")
        for index, parameter in enumerate(value)
    )
    if len(set(parameters)) != len(parameters):
        raise DefinitionGraphError(f"{context} repeats a parameter")
    return parameters


def _topological_layers(
    dependencies: Mapping[str, Sequence[str]], *, kind: str
) -> tuple[list[str], dict[str, int]]:
    pending = {name: set(dependency_names) for name, dependency_names in dependencies.items()}
    dependents: dict[str, list[str]] = defaultdict(list)
    for name, dependency_names in dependencies.items():
        if len(dependency_names) != len(set(dependency_names)):
            raise DefinitionGraphError(f"{kind} {name!r} repeats a dependency")
        for dependency in dependency_names:
            if dependency not in pending:
                raise DefinitionGraphError(
                    f"{kind} {name!r} references unknown definition {dependency!r}"
                )
            if dependency == name:
                raise DefinitionGraphError(f"{kind} {name!r} depends on itself")
            dependents[dependency].append(name)

    ordered: list[str] = []
    layers: dict[str, int] = {}
    available = sorted(name for name, required in pending.items() if not required)
    while available:
        current = available
        available = []
        for name in current:
            if name not in pending:
                continue
            ordered.append(name)
            layers[name] = max(
                (layers[dependency] + 1 for dependency in dependencies[name]),
                default=0,
            )
            del pending[name]
        for name in current:
            for dependent in dependents[name]:
                if dependent in pending:
                    pending[dependent].discard(name)
                    if not pending[dependent]:
                        available.append(dependent)
        available = sorted(set(available))

    if pending:
        cycle = ", ".join(sorted(pending))
        raise DefinitionGraphError(f"{kind} contains a circular dependency: {cycle}")
    return ordered, layers


def reviewed_registry(
    registries: Sequence[tuple[str, Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES,
) -> tuple[dict[str, dict[str, Any]], list[str], dict[str, int]]:
    """Parse and audit every existing conservative definition before linking."""

    by_name: dict[str, dict[str, Any]] = {}
    by_id: dict[str, str] = {}
    for route, definitions in registries:
        if not isinstance(route, str) or not route or "/" in route:
            raise DefinitionGraphError("checked definition registry has an invalid route")
        for definition in definitions:
            name = _identifier(definition.name, context="reviewed definition name")
            identifier = definition.stable_id
            if not isinstance(identifier, str) or REVIEWED_ID.fullmatch(identifier) is None:
                raise DefinitionGraphError(
                    f"reviewed definition {name!r} has an invalid stable identifier"
                )
            if name in by_name:
                raise DefinitionGraphError(f"reviewed definition name {name!r} is duplicated")
            if identifier in by_id:
                raise DefinitionGraphError(
                    f"reviewed definition ID {identifier!r} is shared by "
                    f"{by_id[identifier]!r} and {name!r}"
                )
            parameters = _parameters(
                definition.parameters,
                context=f"reviewed definition {name!r} parameters",
            )
            template = definition.template_source
            if not isinstance(template, str) or not template.strip():
                raise DefinitionGraphError(
                    f"reviewed definition {name!r} has no conservative expansion"
                )
            try:
                parsed = parse_formula_in_context(template, list(parameters))
            except Exception as error:
                raise DefinitionGraphError(
                    f"reviewed definition {name!r} has an invalid first-order expansion"
                ) from error
            if parsed != definition.template_formula:
                raise DefinitionGraphError(
                    f"reviewed definition {name!r} expansion disagrees with its formula"
                )
            dependency_names = tuple(
                _identifier(
                    dependency,
                    context=f"reviewed definition {name!r} dependency",
                )
                for dependency in definition.conceptual_dependencies
            )
            by_id[identifier] = name
            by_name[name] = {
                "name": name,
                "id": identifier,
                "route": route,
                "parameters": list(parameters),
                "arity": len(parameters),
                "dependencies": list(dependency_names),
                "expansion_sha256": _digest(template),
            }

    if not by_name:
        raise DefinitionGraphError("checked definition registries are empty")
    order, layers = _topological_layers(
        {name: record["dependencies"] for name, record in by_name.items()},
        kind="reviewed definition",
    )
    for name, layer in layers.items():
        by_name[name]["topological_layer"] = layer
    return by_name, order, layers


def _references(source: str, names: frozenset[str]) -> list[str]:
    return sorted({token for token in TOKENS.findall(source) if token in names})


def _closure(name: str, adjacency: Mapping[str, Sequence[str]]) -> list[str]:
    seen: set[str] = set()
    pending = list(adjacency[name])
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(adjacency[current])
    return sorted(seen)


def build_definition_graph(
    campaign: Mapping[str, Any],
    *,
    registries: Sequence[tuple[str, Sequence[DefinitionSpec]]] = DEFAULT_REGISTRIES,
    aliases: Mapping[str, tuple[str, tuple[int, ...] | None]] = REVIEWED_BLUEPRINT_ALIASES,
) -> dict[str, Any]:
    """Return the fully audited, evidence-honest research-definition graph."""

    if not isinstance(campaign, Mapping) or campaign.get("schema") != (
        "constructive-grand-campaign-v1"
    ):
        raise DefinitionGraphError("grand-campaign JSON has an invalid schema")
    raw_definitions = campaign.get("definitions")
    if not isinstance(raw_definitions, dict) or not raw_definitions:
        raise DefinitionGraphError("grand campaign needs a nonempty definition registry")

    reviewed, reviewed_order, _reviewed_layers = reviewed_registry(registries)
    names = frozenset(
        _identifier(name, context="blueprint definition name")
        for name in raw_definitions
    )
    dependencies: dict[str, list[str]] = {}
    parameters_by_name: dict[str, tuple[str, ...]] = {}
    for name, definition in raw_definitions.items():
        if not isinstance(definition, dict):
            raise DefinitionGraphError(f"blueprint definition {name!r} must be a mapping")
        parameters = _parameters(
            definition.get("parameters"),
            context=f"blueprint definition {name!r} parameters",
        )
        for field in ("meaning", "expansion"):
            value = definition.get(field)
            if not isinstance(value, str) or not value.strip():
                raise DefinitionGraphError(
                    f"blueprint definition {name!r} needs a nonempty {field}"
                )
        parameters_by_name[name] = parameters
        # Never erase the current name: a self-reference must fail closed.
        dependencies[name] = _references(definition["expansion"], names)

    ordered, layers = _topological_layers(dependencies, kind="blueprint definition")
    reverse: dict[str, list[str]] = {name: [] for name in names}
    for name, requirements in dependencies.items():
        for requirement in requirements:
            reverse[requirement].append(name)
    for dependents in reverse.values():
        dependents.sort()

    raw_nodes = campaign.get("nodes")
    if not isinstance(raw_nodes, list):
        raise DefinitionGraphError("grand campaign needs an ordered milestone list")
    milestone_names: set[str] = set()
    milestone_uses: dict[str, list[str]] = {name: [] for name in names}
    usage_edges: list[dict[str, str]] = []
    lexical_usage_count = 0
    declared_usage_count = 0
    for node in raw_nodes:
        if not isinstance(node, dict):
            raise DefinitionGraphError("grand campaign contains a malformed milestone")
        identifier = _identifier(node.get("id"), context="campaign milestone ID")
        if identifier in milestone_names:
            raise DefinitionGraphError(f"campaign milestone ID {identifier!r} is duplicated")
        milestone_names.add(identifier)
        statement = node.get("statement")
        if not isinstance(statement, str):
            raise DefinitionGraphError(f"campaign milestone {identifier!r} has no statement")
        lexical_references = _references(statement, names)
        declared_references = node.get("definition_refs", [])
        if not isinstance(declared_references, list):
            raise DefinitionGraphError(
                f"campaign milestone {identifier!r} has invalid declared notation references"
            )
        normalized_declared = [
            _identifier(
                name,
                context=f"campaign milestone {identifier!r} declared notation",
            )
            for name in declared_references
        ]
        if len(set(normalized_declared)) != len(normalized_declared):
            raise DefinitionGraphError(
                f"campaign milestone {identifier!r} repeats a declared notation reference"
            )
        unknown_declared = set(normalized_declared).difference(names)
        if unknown_declared:
            raise DefinitionGraphError(
                f"campaign milestone {identifier!r} declares unknown notation "
                f"{sorted(unknown_declared)!r}"
            )
        for name in lexical_references:
            usage_edges.append(
                {"kind": "statement_uses_definition", "source": identifier, "target": name}
            )
        for name in normalized_declared:
            usage_edges.append(
                {"kind": "declared_notation", "source": identifier, "target": name}
            )
        lexical_usage_count += len(lexical_references)
        declared_usage_count += len(normalized_declared)
        for name in sorted(set(lexical_references).union(normalized_declared)):
            milestone_uses[name].append(identifier)

    checked_matches: list[dict[str, Any]] = []
    incompatible: list[dict[str, Any]] = []
    definitions: list[dict[str, Any]] = []
    for name in ordered:
        definition = raw_definitions[name]
        parameters = parameters_by_name[name]
        candidate_name = name if name in reviewed else None
        declared_alignment: tuple[int, ...] | None = tuple(range(len(parameters)))
        match_kind = "exact-name"
        if name in aliases:
            alias_name, declared_alignment = aliases[name]
            _identifier(alias_name, context=f"blueprint definition {name!r} reviewed alias")
            if candidate_name is not None and candidate_name != alias_name:
                direct = reviewed[candidate_name]
                aliased = reviewed.get(alias_name)
                if (
                    aliased is None
                    or direct["parameters"] != aliased["parameters"]
                    or direct["expansion_sha256"] != aliased["expansion_sha256"]
                    or direct["dependencies"] != aliased["dependencies"]
                ):
                    raise DefinitionGraphError(
                        f"blueprint definition {name!r} has competing checked identities"
                    )
            candidate_name = alias_name
            match_kind = "explicit-alias"
            if candidate_name not in reviewed:
                raise DefinitionGraphError(
                    f"blueprint definition {name!r} aliases unknown reviewed "
                    f"definition {candidate_name!r}"
                )

        match: dict[str, Any] | None = None
        mismatch: dict[str, Any] | None = None
        if candidate_name is not None:
            candidate = reviewed[candidate_name]
            reviewed_parameters = tuple(candidate["parameters"])
            if len(reviewed_parameters) != len(parameters):
                mismatch = {
                    "blueprint_name": name,
                    "blueprint_parameters": list(parameters),
                    "blueprint_arity": len(parameters),
                    "reviewed_name": candidate_name,
                    "reviewed_parameters": list(reviewed_parameters),
                    "reviewed_arity": len(reviewed_parameters),
                    "reviewed_id": candidate["id"],
                    "route": candidate["route"],
                    "reason": "incompatible-arity",
                    "confers_checked_evidence": False,
                }
                incompatible.append(mismatch)
            elif declared_alignment is None:
                raise DefinitionGraphError(
                    f"blueprint definition {name!r} has no reviewed argument alignment"
                )
            elif (
                len(declared_alignment) != len(parameters)
                or set(declared_alignment) != set(range(len(parameters)))
            ):
                raise DefinitionGraphError(
                    f"blueprint definition {name!r} has an invalid reviewed argument permutation"
                )
            elif tuple(parameters[position] for position in declared_alignment) != (
                reviewed_parameters
            ):
                raise DefinitionGraphError(
                    f"blueprint definition {name!r} disagrees with its reviewed argument alignment"
                )
            else:
                match = {
                    "blueprint_name": name,
                    "reviewed_name": candidate_name,
                    "reviewed_id": candidate["id"],
                    "route": candidate["route"],
                    "kind": match_kind,
                    "blueprint_parameters": list(parameters),
                    "reviewed_parameters": list(reviewed_parameters),
                    "reviewed_argument_blueprint_positions": list(declared_alignment),
                    "reviewed_expansion_sha256": candidate["expansion_sha256"],
                    "blueprint_expansion_is_kernel_checked": False,
                }
                checked_matches.append(match)

        definitions.append(
            {
                "name": name,
                "parameters": list(parameters),
                "arity": len(parameters),
                "meaning": definition["meaning"],
                "expansion": definition["expansion"],
                "expansion_sha256": _digest(definition["expansion"]),
                "topological_layer": layers[name],
                "dependencies": dependencies[name],
                "dependents": reverse[name],
                "transitive_dependencies": _closure(name, dependencies),
                "transitive_dependents": _closure(name, reverse),
                "milestone_users": milestone_uses[name],
                "reviewed_match": match,
                "reviewed_incompatibility": mismatch,
                "authority": "blueprint-vocabulary-only",
            }
        )

    notation_edges = [
        {"kind": "definition_uses_definition", "source": name, "target": requirement}
        for name in ordered
        for requirement in dependencies[name]
    ]
    maximum_layer = max(layers.values(), default=-1)
    checked_matches.sort(key=lambda item: item["blueprint_name"])
    incompatible.sort(key=lambda item: item["blueprint_name"])
    return {
        "schema": SCHEMA,
        "authority_policy": {
            "blueprint_definitions": "research vocabulary only; never a kernel axiom, predicate, proof, or checked definition",
            "reviewed_matches": "only the separately linked conservative registry expansion is independently parsed and checked; the blueprint expansion itself remains uncertified",
            "notation_edges": "definition and milestone notation references only; never theorem-proof dependencies",
            "incompatible_names": "same-name or declared-alias arity mismatches grant no checked-definition evidence",
        },
        "campaign_snapshot_sha256": _digest(_canonical(campaign)),
        "definition_count": len(definitions),
        "definition_edge_count": len(notation_edges),
        "statement_usage_edge_count": lexical_usage_count,
        "declared_notation_edge_count": declared_usage_count,
        "milestone_usage_edge_count": len(usage_edges),
        "topological_layer_count": maximum_layer + 1,
        "reviewed_definition_count": len(reviewed),
        "reviewed_definition_edge_count": sum(
            len(record["dependencies"]) for record in reviewed.values()
        ),
        "compatible_reviewed_match_count": len(checked_matches),
        "exact_name_reviewed_match_count": sum(
            record["kind"] == "exact-name" for record in checked_matches
        ),
        "explicit_alias_reviewed_match_count": sum(
            record["kind"] == "explicit-alias" for record in checked_matches
        ),
        "incompatible_reviewed_match_count": len(incompatible),
        "topological_order": ordered,
        "layers": [
            {"number": layer, "definitions": [name for name in ordered if layers[name] == layer]}
            for layer in range(maximum_layer + 1)
        ],
        "definitions": definitions,
        "definition_edges": notation_edges,
        "milestone_usage_edges": usage_edges,
        "reviewed_definitions": [reviewed[name] for name in reviewed_order],
        "compatible_reviewed_matches": checked_matches,
        "incompatible_reviewed_matches": incompatible,
    }


def definition_graph_bytes(campaign: Mapping[str, Any]) -> bytes:
    """Serialize the entire graph reproducibly for public/static publication."""

    return (
        json.dumps(
            build_definition_graph(campaign),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
