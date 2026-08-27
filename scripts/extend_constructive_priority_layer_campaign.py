#!/usr/bin/env python3
"""Connect four exact checked endpoints to the unchanged broad campaign.

Proof prerequisites, conservative notation, and conceptual planning links
remain different edge kinds. No open successor is closed by implication.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
import re
from typing import Any

import build_constructive_priority_layer_explorer as explorer
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_priority_layer_definition_graph import build_definition_graph
from constructive_priority_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS,
    PRIORITY_LAYER_DEFINITIONS, definition_closure,
)
from extend_constructive_second_wave_campaign import _table_source
from peano_lab.kernel.formulas import parse_formula_with_names


PRIMARY_ROOTS = explorer.MILESTONE_ROOTS
REFINED_PLANNING_DEFINITIONS = frozenset({"Convergent", "Phi", "Squarefree", "PowerProfile"})
ACTUAL_TOOL_PREREQUISITES = {
    "G072": ("G071", "T03"), "G006": ("G004", "T09", "T11"),
    "G010": ("T09", "T07", "T11"), "G036": ("T09", "T08", "T05"),
}
SUBSTRATE_THEOREMS = {
    "G072": ("cf_convergent_actual_prefix_error_invariant", "cf_approximation_derived_invariant_best_signed"),
    "G006": ("prime_factorization_existence", "prime_valuation_support_exists"),
    "G010": ("prime_valuation_support_exists", "squarefree_decomposition_exists_unique"),
    "G036": ("power_valuation_exact_cofactor", "lte_prime_power_iteration", "lte_coprime_exponent_step"),
}
REFINEMENTS = {
    "G072": "Convergent is the actual indexed quotient-matrix computation, not a record containing the approximation result. The genuine initial 0/1 is included: the old planning-only u>0 restriction was erroneous. Every valid index has a unique convergent, adjacent determinants and coprimality are proved, and the terminal convergent is exact. The second-kind bound holds for every strictly smaller positive denominator, including arbitrary signed competitor numerators.",
    "G006": "Phi counts actual 0/1 coprimality bits for residues 0≤a<n. EulerProduct independently constructs distinct prime support, actual valuations, actual powers p^(e−1), and their actual finite product. Their equality is proved rather than built into either definition. The supplied input is n>0 alone; factorization, support, and totient witnesses are outputs. The empty product gives Phi(1,1); zero is excluded.",
    "G010": "The theorem constructs the unique positive squarefree-times-square decomposition and an actual encoded perfect-power profile. For n>1 the complete prime support, positive exponent gcd, and beta root table classify all positive root degrees. The unit n=1 has the distinguished zero code and a uniform proof for every positive exponent. NaturalSquarefreeDecomposition is not the polynomial SquarefreeDecomposition planning predicate.",
    "G036": "The original odd-prime and positive-input guards are retained exactly. Natural balances replace subtraction, and actual relational powers are constructed. A proved second-order correction identity gives the prime step; iteration and the actual prime-power cofactor of n give the complete valuation formula. The companion theorem covers every supplied actual power/difference witness. The binary-prime and other variants are not claimed.",
}


def historical_campaign() -> dict[str, Any]:
    from build_peano_library_channels_v29 import HISTORICAL_ATLAS_INPUTS

    for path, expected in HISTORICAL_ATLAS_INPUTS.items():
        if explorer._digest((explorer.REPO / path).read_bytes()) != expected:
            raise explorer.PriorityLayerExplorerError("the immutable v28 presentation parent changed")
    return explorer._strict_json((explorer.REPO / "book/_static/constructive-grand-campaign/campaign.json").read_bytes())


def _cone(root: str, rows: dict[str, Any]) -> set[str]:
    seen, pending = set(), [root]
    while pending:
        name = pending.pop()
        if name not in seen:
            seen.add(name)
            pending.extend(rows[name]["dependencies"])
    return seen


def _blueprint_expansion(definition) -> str:
    reading = _FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
    # The historical raw Sum has arity three; BetaSum is the reviewed arity-four
    # alias. Preserve this distinction even inside new definition expansions.
    source = re.sub(r"\bSum\(", "BetaSum(", reading["defined_statement"])
    aliases = {**DEFINITIONS, "BetaSum": replace(DEFINITIONS["Sum"], name="BetaSum")}
    exact, names = parse_formula_with_names(definition.template_source)
    parser = _LocalDefinedParser(source, aliases)
    parser.free = list(names)
    if parser.parse() != exact or tuple(parser.free) != names:
        raise explorer.PriorityLayerExplorerError("a blueprint display changed the exact conservative definition")
    return source


def _definition_record(definition) -> dict[str, Any]:
    return {"parameters": list(definition.parameters), "meaning": definition.summary,
            "expansion": _blueprint_expansion(definition),
            "reviewed_definition_id": definition.stable_id,
            "reviewed_expansion_sha256": explorer._digest(definition.template_source),
            "exact_defined_expansion_equivalence_checked": True}


def _roots_for_goal(identifier: str, family) -> tuple[str, ...]:
    return family.roots


def extend_campaign(original: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    historical = historical_campaign()
    result = deepcopy(original)
    version = result.get("meta", {}).get("current_alpha_version")
    if result.get("schema") != "constructive-grand-campaign-v1" or version not in {"v28", "v29"}:
        raise explorer.PriorityLayerExplorerError("priority-layer extension requires the exact v28/v29 campaign")
    old_nodes = {row["id"]: row for row in historical["nodes"]}
    nodes = {row["id"]: row for row in result["nodes"]}
    if len(nodes) != len(result["nodes"]) or nodes.keys() != old_nodes.keys():
        raise explorer.PriorityLayerExplorerError("the broad campaign milestone inventory changed")
    for identifier, node in old_nodes.items():
        if (version == "v28" or identifier not in PRIMARY_ROOTS) and explorer._json(nodes[identifier]) != explorer._json(node):
            raise explorer.PriorityLayerExplorerError(f"an unrelated historical milestone changed: {identifier}")
    for field in ("anchors", "tools", "families", "layers", "language", "dependency_policy", "title", "subtitle"):
        if explorer._json(result[field]) != explorer._json(historical[field]):
            raise explorer.PriorityLayerExplorerError(f"historical campaign structure changed: {field}")
    for name, boundary in historical["ambitious_boundaries"].items():
        expected = deepcopy(boundary)
        if version == "v29" and name == "alpha_v28_edition":
            expected["role"] = "historical_immutable_release"
        if explorer._json(result["ambitious_boundaries"].get(name)) != explorer._json(expected):
            raise explorer.PriorityLayerExplorerError(f"an immutable historical release boundary changed: {name}")
    historical_sources = historical["sources"]
    if explorer._json(result["sources"][:len(historical_sources)]) != explorer._json(historical_sources):
        raise explorer.PriorityLayerExplorerError("historical campaign provenance changed")
    expected_names = set(historical["definitions"]) | {item.name for item in PRIORITY_LAYER_DEFINITIONS}
    if set(result["definitions"]) - expected_names:
        raise explorer.PriorityLayerExplorerError("an unreviewed definition was added to the frozen campaign inventory")
    for name, record in historical["definitions"].items():
        if name not in REFINED_PLANNING_DEFINITIONS and explorer._json(result["definitions"].get(name)) != explorer._json(record):
            raise explorer.PriorityLayerExplorerError(f"a historical blueprint definition changed: {name}")
    planned = {name: deepcopy(historical["definitions"][name]) for name in REFINED_PLANNING_DEFINITIONS}
    if "historical_priority_layer_definition_plan" in result and explorer._json(result["historical_priority_layer_definition_plan"]) != explorer._json(planned):
        raise explorer.PriorityLayerExplorerError("an original planning definition was rewritten")
    result["historical_priority_layer_definition_plan"] = planned
    for definition in PRIORITY_LAYER_DEFINITIONS:
        expected = _definition_record(definition)
        name = definition.name
        if name in result["definitions"] and not (version == "v28" and name in REFINED_PLANNING_DEFINITIONS):
            if explorer._json(result["definitions"][name]) != explorer._json(expected):
                raise explorer.PriorityLayerExplorerError(f"an exact introduced definition changed: {name}")
        result["definitions"][name] = expected

    catalog, bundle = inputs["catalog"], inputs["bundle"]
    metadata = result["meta"]
    metadata.update(current_alpha_version="v29", current_alpha_checked_use_count=catalog["checked_use_count"],
                    priority_layer_named_targets=list(PRIMARY_ROOTS), priority_layer_new_theorem_count=len(inputs["frontier"]),
                    priority_layer_release_date="2026-08-28")
    if "v28" not in metadata["historical_alpha_versions"]:
        metadata["historical_alpha_versions"].append("v28")
    source_rows = (
        ("S67", "release_manifest", "Current Alpha v29 independently checked priority-layer channels", "artifacts/peano-library/channels-v29.json"),
        ("S68", "independent_proof_artifact", "Complete original-kernel and Lean-verified priority-layer proof bundle", explorer.EXPECTED_BUNDLE_PATH),
        ("S69", "independent_closure_record", "Exact priority-layer closure receipt and scope boundaries", "research/arithmetic-library/alpha-v29-priority-layer-receipt.md"),
        ("S70", "admission_record", "Immutable additive Alpha v29 priority-layer admission contract", "research/arithmetic-library/alpha-v29-priority-layer-rfc-v1.md"),
        ("S71", "historical_presentation_parent", "Byte-exact original v28 atlas, preserved separately", "book/_static/constructive-grand-campaign/campaign.json"),
    )
    known_sources = {row["id"]: row for row in result["sources"]}
    if len(known_sources) != len(result["sources"]):
        raise explorer.PriorityLayerExplorerError("campaign provenance repeats a source identifier")
    if set(known_sources) - {row["id"] for row in historical_sources} - {row[0] for row in source_rows}:
        raise explorer.PriorityLayerExplorerError("an unrelated provenance source entered this extension")
    for identifier, kind, label, path in source_rows:
        row = {"id": identifier, "kind": kind, "label": label, "path": path}
        if identifier in known_sources and known_sources[identifier] != row:
            raise explorer.PriorityLayerExplorerError("priority-layer provenance source changed")
        if identifier not in known_sources:
            result["sources"].append(row)
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v28_edition"]["role"] = "historical_immutable_release"
    boundaries["alpha_v29_edition"] = {
        "role": "current_immutable_release", "theorem_count": catalog["theorem_count"],
        "stable_closed_count": 432, "alpha_closed_count": catalog["alpha_only_count"],
        "checked_use_count": catalog["checked_use_count"], "body_checked_count": 0,
        "pending_layered_closure_count": 0, "checked_use_promotion_count": len(inputs["frontier"]),
        "new_theorem_count": len(inputs["frontier"]), "dependency_edge_count": catalog["edge_count"],
        "checked_dependency_edge_count": catalog["edge_count"], "layer_count": catalog["layer_count"],
        "enrollment_sha256": catalog["ordered_enrollment_root_sha256"],
        "parent_enrollment_sha256": explorer.closure.PARENT_ENROLLMENT_SHA256,
        "identity_sha256": catalog["edition_identity_sha256"], "catalog_sha256": inputs["catalog_sha256"],
        "evidence_root_sha256": catalog["evidence_root_sha256"],
        "frontier_new_names_sha256": catalog["frontier_v29_ordered_names_sha256"],
        "stable_unchanged": True, "historical_v28_unchanged": True,
        "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_exact_priority_layer_targets",
    }
    boundaries["priority_layer_evidence_transition"] = {
        "parent_v28_theorem_count": 2764, "new_theorem_count": len(inputs["frontier"]),
        "current_v29_theorem_count": catalog["theorem_count"],
        "authoring_campaign_counts": dict(Counter(owner.campaign for owner, _ in inputs["frontier"])),
        "presentation_family_counts": {family.slug: len(explorer._selected(family, inputs["frontier"])) for family in explorer.FAMILIES},
        "presentation_origin_distinction": "Five exact, disjoint theorem families: one shared valuation tool and four completed named targets. No theorem is duplicated or re-admitted.",
        "bundle_node_count": bundle["node_count"], "dependency_edge_count": bundle["dependency_edges"],
        "body_proof_nodes": bundle["body_proof_nodes"], "bundle_bytes": bundle["artifact_bytes"],
        "bundle_sha256": bundle["artifact_sha256"], "original_kernel_call_count": bundle["kernel_calls"],
        "independent_lean_bundle_verified": True, "stable_unchanged": True, "historical_v28_unchanged": True,
        "named_targets_complete": list(PRIMARY_ROOTS), "broader_roadmap_bullets_automatically_closed": False,
    }
    by_name = inputs["by_name"]
    for identifier, root_name in PRIMARY_ROOTS.items():
        goal, old = nodes[identifier], old_nodes[identifier]
        family = next(family for family in explorer.FAMILIES if identifier in family.milestones)
        root = by_name[root_name]
        history = {
            "historical_planned_statement": old["statement"],
            "historical_planned_dependencies": old["deps"],
            "historical_planned_layer": old["layer"],
            "historical_planned_why": old["why"],
            "historical_foundation_classification": old["status"],
        }
        for field, value in history.items():
            if field in goal and explorer._json(goal[field]) != explorer._json(value):
                raise explorer.PriorityLayerExplorerError(f"historical goal planning data changed: {identifier}")
            goal[field] = deepcopy(value)
        for field in ("id", "kind", "title", "family", "difficulty"):
            if goal.get(field) != old.get(field):
                raise explorer.PriorityLayerExplorerError(f"the original milestone identity changed: {identifier}")
        goal["deps"] = list(ACTUAL_TOOL_PREREQUISITES[identifier])
        goal["conceptual_refs"] = [name for name in dict.fromkeys((*old.get("conceptual_refs", ()), *old["deps"])) if name not in goal["deps"]]
        goal["layer"] = max(old["layer"], max(nodes[name]["layer"] + 1 for name in goal["deps"]))
        goal["status"] = "alpha_closed"
        definitions = explorer._family_definitions(family)
        reading = _FormulaCompactor(definitions).compact(root["statement"])
        goal["statement"] = re.sub(r"\bSum\(", "BetaSum(", reading["defined_statement"])
        goal["why"] = REFINEMENTS[identifier]
        goal["representation_refinement"] = REFINEMENTS[identifier]
        goal["definition_refs"] = [definition.name for definition in definitions if definition.stable_id in reading["statement_definition_uses"]]
        goal["references"] = list(dict.fromkeys((*old.get("references", ()), "S67", "S68", "S69", "S70")))
        selected = explorer._selected(family, inputs["frontier"])
        tags = {row.name: f"{family.prefix}{index:04X}" for index, (_, row) in enumerate(selected, 1)}
        roots = _roots_for_goal(identifier, family)
        if not set(SUBSTRATE_THEOREMS[identifier]) <= _cone(root_name, by_name):
            raise explorer.PriorityLayerExplorerError(f"an asserted actual prerequisite is not used by {identifier}")
        closure = root["empty_context_closure"]
        evidence = {
            "implementation": "independently_closed", "alpha_version": "v29", "release_status": "alpha_closed",
            "alpha_enrolled": True, "checked_use": True, "stable_member": False,
            "full_empty_context_closure": True, "independent_lean_bundle_verified": True,
            "theorem_name": root_name, "theorem_statement_sha256": root["statement_sha256"],
            "theorem_names": list(roots), "new_theorem_count": len(selected),
            "bundle_campaign": "priority_layer", "bundle_node_id": closure["bundle_node_id"],
            "bundle_nodes": bundle["node_count"], "bundle_dependencies": bundle["dependency_edges"],
            "bundle_sha256": bundle["artifact_sha256"], "bundle_path": bundle["artifact_path"],
            "route": family.slug + "/", "proof_tag": tags[root_name],
            "actual_substrate_theorem_names": list(SUBSTRATE_THEOREMS[identifier]),
            "proof_routes": [{"route": family.slug, "label": name, "tag": tags[name]} for name in roots],
        }
        if identifier == "G072":
            evidence.update(actual_quotient_trace=True, initial_zero_over_one_included=True,
                            every_valid_index_constructed=True, signed_competitors_included=True,
                            strictly_smaller_positive_denominators=True, approximation_premise_in_definition=False)
        elif identifier == "G006":
            evidence.update(actual_residue_count=True, product_definition_independent_of_phi=True,
                            complete_distinct_prime_support=True, unit_empty_product_included=True,
                            supplied_factorization_premise=False)
        elif identifier == "G010":
            evidence.update(actual_root_table=True, unit_uniform_profile=True,
                            squarefree_part_unique=True, all_positive_root_degrees_classified=True,
                            polynomial_decomposition_claimed=False)
        elif identifier == "G036":
            evidence.update(actual_powers_and_difference_constructed=True, odd_prime_guard_retained=True,
                            all_actual_power_witnesses_covered=True, binary_prime_variant_claimed=False)
        goal["evidence"] = evidence
    build_definition_graph(result)
    return result


def update_atlas_bindings(source: str, campaign: dict[str, Any]) -> str:
    graph = build_definition_graph(campaign)
    for name, key, compatible in (("COMPILED_DEFINITIONS", "compatible_reviewed_matches", True),
                                  ("INCOMPATIBLE_DEFINITIONS", "incompatible_reviewed_matches", False)):
        rows = [{**row, "route": graph.get("definition_page_overrides", {}).get(row["reviewed_id"], {}).get("route", row["route"])} for row in graph[key]]
        source, count = re.subn(r"      var " + name + r" = \{.*?\n      \};", lambda match: _table_source(name, rows, compatible=compatible), source, count=1, flags=re.S)
        if count != 1:
            raise explorer.PriorityLayerExplorerError(f"missing original atlas table {name}")
    roots = re.search(r"      var PROOF_ROOTS = \{(.*?)\n      \};", source, flags=re.S)
    if roots is None:
        raise explorer.PriorityLayerExplorerError("missing original atlas proof destinations")
    lines = [line.rstrip().rstrip(",") for line in roots.group(1).splitlines() if line.strip()
             and not any(re.match(r"\s*" + identifier + r":", line) for identifier in PRIMARY_ROOTS)]
    goals = {node["id"]: node for node in campaign["nodes"]}
    for identifier in PRIMARY_ROOTS:
        goal, evidence = goals[identifier], goals[identifier]["evidence"]
        lines.append(f'        {identifier}: {{ route: {json.dumps(evidence["route"].rstrip("/"))}, label: {json.dumps(goal["title"],ensure_ascii=False)}, tag: {json.dumps(evidence["proof_tag"])} }}')
    replacement = "      var PROOF_ROOTS = {\n" + ",\n".join(lines) + "\n      };"
    source = source[:roots.start()] + replacement + source[roots.end():]
    # The original atlas derives revisions from the active immutable boundary.
    # Preserve that mechanism rather than introducing a second version pointer.
    if ('state.campaign.ambitious_boundaries["alpha_" + metadata.current_alpha_version + "_edition"]' not in source
        or 'String(boundary.catalog_sha256 || "").slice(0, 12)' not in source):
        raise explorer.PriorityLayerExplorerError("missing original data-driven atlas revision binding")
    for old_route, current_route in (
        ("constructive-second-wave-explorer-v28", "constructive-second-wave-explorer-v29"),
        ("constructive-lower-layer-explorer", "constructive-lower-layer-explorer-v29"),
    ):
        old = f'return "../{old_route}/" + route + "/explorer/defined/";'
        new = f'return "../{current_route}/" + route + "/explorer/defined/";'
        if source.count(old) + source.count(new) != 1:
            raise explorer.PriorityLayerExplorerError("ambiguous historical local route dispatch")
        source = source.replace(old, new)
    priority_routes = ('        if (["prime-valuation-support", "best-approximation", "totient-products", "squarefree-kernels", "exponent-lifting"].indexOf(route) !== -1) {\n'
                       '          return "../constructive-priority-layer-explorer/" + route + "/explorer/defined/";\n'
                       '        }')
    deployed_route = '        if (deployed) return "../" + route + "/explorer/defined/";'
    if priority_routes not in source:
        if source.count(deployed_route) != 1:
            raise explorer.PriorityLayerExplorerError("missing unique original deployed route dispatch")
        source = source.replace(deployed_route, deployed_route + "\n" + priority_routes)
    if source.count(priority_routes) != 1:
        raise explorer.PriorityLayerExplorerError("duplicate priority-layer local route dispatch")

    return source



def build_files(inputs: dict[str, Any] | None = None) -> dict[str, bytes]:
    if inputs is None:
        inputs = explorer._load_release_inputs()
    campaign = extend_campaign(historical_campaign(), inputs)
    source = (explorer.REPO / "book/_static/constructive-grand-campaign/index.html").read_text()
    return {
        "campaign.json": explorer._json(campaign),
        "definitions.json": explorer._json(build_definition_graph(campaign)),
        "index.html": update_atlas_bindings(source, campaign).encode(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    explorer.write_or_check(build_files(), explorer.CAMPAIGN.parent, check=arguments.check)
    print("priority-layer campaign: PASS (four exact targets, frozen v28 parent, separate proof and definition DAGs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
