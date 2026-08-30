#!/usr/bin/env python3
"""Connect the exact Gaussian unique-factorization endpoint to the unchanged broad campaign.

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

import build_constructive_gaussian_factorization_explorer as explorer
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_gaussian_factorization_definition_graph import build_definition_graph
from constructive_gaussian_factorization_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS,
    GAUSSIAN_FACTORIZATION_DEFINITIONS, definition_closure,
)
from extend_constructive_second_wave_campaign import _table_source
from peano_lab.kernel.formulas import parse_formula_with_names
from sync_constructive_grand_campaign import MAX_CAMPAIGN_BYTES, _expected


PRIMARY_ROOTS = explorer.MILESTONE_ROOTS
REFINED_PLANNING_DEFINITIONS = frozenset()
ACTUAL_TOOL_PREREQUISITES = {"G082": ("G081", "T04", "T15")}
SUBSTRATE_THEOREMS = {
    "G082": ("gaussian_euclidean_division_exists", "gaussian_gcd_bezout_exists",
             "gaussian_irreducible_is_prime", "gaussian_prime_is_irreducible",
             "gaussian_irreducible_divisor_exists",
             "gaussian_product_swap_last_invariant",
             "gaussian_irreducible_products_associate_unique"),
}
REFINEMENTS = {
    "G082": "The sole inputs are a valid canonical Gaussian code and its nonzeroness. Euclidean gcd and Bezout establish the prime-divisor property; finite norm-bounded search and descent construct actual prime factors and their beta-coded product. Uniqueness constructs equal lengths and a genuinely bounded, injective and surjective beta map, with an actual multiplicative unit at each match. Repeated factors and empty unit factorizations are included. The Gaussian identity has code six, not natural code one. No prime factorization, primality decision oracle or matching is supplied as a premise. The generic planning RingPrime and two-argument GaussianFactorization remain distinct, unaliased planning concepts; sorted primary representatives, Gaussian prime classification and Eisenstein factorization are separate targets.",
}

def historical_campaign() -> dict[str, Any]:
    from build_peano_library_channels_v30 import HISTORICAL_ATLAS_INPUTS

    for path, expected in HISTORICAL_ATLAS_INPUTS.items():
        if explorer._digest((explorer.REPO / path).read_bytes()) != expected:
            raise explorer.GaussianFactorizationExplorerError("the immutable v29 presentation parent changed")
    return explorer._strict_json((explorer.REPO / "book/_static/constructive-priority-campaign/campaign.json").read_bytes())


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
        raise explorer.GaussianFactorizationExplorerError("a blueprint display changed the exact conservative definition")
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
    if result.get("schema") != "constructive-grand-campaign-v1" or version not in {"v29", "v30"}:
        raise explorer.GaussianFactorizationExplorerError("gaussian-factorization extension requires the exact v29/v30 campaign")
    old_nodes = {row["id"]: row for row in historical["nodes"]}
    nodes = {row["id"]: row for row in result["nodes"]}
    if len(nodes) != len(result["nodes"]) or nodes.keys() != old_nodes.keys():
        raise explorer.GaussianFactorizationExplorerError("the broad campaign milestone inventory changed")
    for identifier, node in old_nodes.items():
        if (version == "v29" or identifier not in PRIMARY_ROOTS) and explorer._json(nodes[identifier]) != explorer._json(node):
            raise explorer.GaussianFactorizationExplorerError(f"an unrelated historical milestone changed: {identifier}")
    if set(result) != set(historical):
        raise explorer.GaussianFactorizationExplorerError("the historical atlas field inventory changed")
    expected_history = list(historical["meta"]["historical_alpha_versions"])
    if version == "v30" and "v29" not in expected_history:
        expected_history.append("v29")
    if explorer._json(result["meta"].get("historical_alpha_versions")) != explorer._json(expected_history):
        raise explorer.GaussianFactorizationExplorerError("the historical Alpha-version inventory changed")
    allowed_metadata = set(historical["meta"]) | {
        "gaussian_factorization_named_targets", "gaussian_factorization_new_theorem_count",
        "gaussian_factorization_release_date",
    }
    if set(result["meta"]) - allowed_metadata:
        raise explorer.GaussianFactorizationExplorerError("unreviewed campaign metadata was added")
    if version == "v29" and explorer._json(result["meta"]) != explorer._json(historical["meta"]):
        raise explorer.GaussianFactorizationExplorerError("the original v29 metadata changed")
    for field in set(historical) - {"nodes", "definitions", "meta", "sources", "ambitious_boundaries"}:
        if explorer._json(result[field]) != explorer._json(historical[field]):
            raise explorer.GaussianFactorizationExplorerError(f"historical campaign structure changed: {field}")
    for field, value in historical["meta"].items():
        if field not in {"current_alpha_version", "current_alpha_checked_use_count", "historical_alpha_versions"}:
            if explorer._json(result["meta"].get(field)) != explorer._json(value):
                raise explorer.GaussianFactorizationExplorerError(f"historical campaign metadata changed: {field}")
    for name, boundary in historical["ambitious_boundaries"].items():
        expected = deepcopy(boundary)
        if version == "v30" and name == "alpha_v29_edition":
            expected["role"] = "historical_immutable_release"
        if explorer._json(result["ambitious_boundaries"].get(name)) != explorer._json(expected):
            raise explorer.GaussianFactorizationExplorerError(f"an immutable historical release boundary changed: {name}")
    historical_sources = historical["sources"]
    if explorer._json(result["sources"][:len(historical_sources)]) != explorer._json(historical_sources):
        raise explorer.GaussianFactorizationExplorerError("historical campaign provenance changed")
    expected_names = set(historical["definitions"]) | {item.name for item in GAUSSIAN_FACTORIZATION_DEFINITIONS}
    if set(result["definitions"]) - expected_names:
        raise explorer.GaussianFactorizationExplorerError("an unreviewed definition was added to the frozen campaign inventory")
    for name, record in historical["definitions"].items():
        if name not in REFINED_PLANNING_DEFINITIONS and explorer._json(result["definitions"].get(name)) != explorer._json(record):
            raise explorer.GaussianFactorizationExplorerError(f"a historical blueprint definition changed: {name}")
    for definition in GAUSSIAN_FACTORIZATION_DEFINITIONS:
        expected = _definition_record(definition)
        name = definition.name
        if name in result["definitions"] and not (version == "v29" and name in REFINED_PLANNING_DEFINITIONS):
            if explorer._json(result["definitions"][name]) != explorer._json(expected):
                raise explorer.GaussianFactorizationExplorerError(f"an exact introduced definition changed: {name}")
        result["definitions"][name] = expected

    catalog, bundle = inputs["catalog"], inputs["bundle"]
    metadata = result["meta"]
    metadata.update(current_alpha_version="v30", current_alpha_checked_use_count=catalog["checked_use_count"],
                    gaussian_factorization_named_targets=list(PRIMARY_ROOTS), gaussian_factorization_new_theorem_count=len(inputs["frontier"]),
                    gaussian_factorization_release_date="2026-08-28")
    if "v29" not in metadata["historical_alpha_versions"]:
        metadata["historical_alpha_versions"].append("v29")
    source_rows = (
        ("S72", "release_manifest", "Current Alpha v30 independently checked Gaussian-factorization channels", "artifacts/peano-library/channels-v30.json"),
        ("S73", "independent_proof_artifact", "Complete original-kernel and Lean-verified Gaussian-factorization proof bundle", explorer.EXPECTED_BUNDLE_PATH),
        ("S74", "independent_closure_record", "Exact Gaussian-factorization closure receipt and scope boundaries", "research/arithmetic-library/alpha-v30-gaussian-factorization-receipt.md"),
        ("S75", "admission_record", "Immutable additive Alpha v30 Gaussian-factorization admission contract", "research/arithmetic-library/alpha-v30-gaussian-factorization-rfc-v1.md"),
        ("S76", "historical_presentation_parent", "Byte-exact original v29 priority atlas, preserved separately", "book/_static/constructive-priority-campaign/campaign.json"),
    )
    known_sources = {row["id"]: row for row in result["sources"]}
    if len(known_sources) != len(result["sources"]):
        raise explorer.GaussianFactorizationExplorerError("campaign provenance repeats a source identifier")
    if set(known_sources) - {row["id"] for row in historical_sources} - {row[0] for row in source_rows}:
        raise explorer.GaussianFactorizationExplorerError("an unrelated provenance source entered this extension")
    for identifier, kind, label, path in source_rows:
        row = {"id": identifier, "kind": kind, "label": label, "path": path}
        if identifier in known_sources and known_sources[identifier] != row:
            raise explorer.GaussianFactorizationExplorerError("gaussian-factorization provenance source changed")
        if identifier not in known_sources:
            result["sources"].append(row)
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v29_edition"]["role"] = "historical_immutable_release"
    boundaries["alpha_v30_edition"] = {
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
        "frontier_new_names_sha256": catalog["frontier_v30_ordered_names_sha256"],
        "stable_unchanged": True, "historical_v29_unchanged": True,
        "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_exact_gaussian_factorization_targets",
    }
    boundaries["gaussian_factorization_evidence_transition"] = {
        "parent_v29_theorem_count": 3042, "new_theorem_count": len(inputs["frontier"]),
        "current_v30_theorem_count": catalog["theorem_count"],
        "authoring_campaign_counts": dict(Counter(owner.campaign for owner, _ in inputs["frontier"])),
        "presentation_family_counts": {family.slug: len(explorer._selected(family, inputs["frontier"])) for family in explorer.FAMILIES},
        "presentation_origin_distinction": "Seven proof factories form one Gaussian unique-factorization family. All 180 new theorems are admitted exactly once; the four priority targets and all earlier admissions are preserved.",
        "bundle_node_count": bundle["node_count"], "dependency_edge_count": bundle["dependency_edges"],
        "body_proof_nodes": bundle["body_proof_nodes"], "bundle_bytes": bundle["artifact_bytes"],
        "bundle_sha256": bundle["artifact_sha256"], "original_kernel_call_count": bundle["kernel_calls"],
        "independent_lean_bundle_verified": True, "stable_unchanged": True, "historical_v29_unchanged": True,
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
                raise explorer.GaussianFactorizationExplorerError(f"historical goal planning data changed: {identifier}")
            goal[field] = deepcopy(value)
        for field in ("id", "kind", "title", "family", "difficulty"):
            if goal.get(field) != old.get(field):
                raise explorer.GaussianFactorizationExplorerError(f"the original milestone identity changed: {identifier}")
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
        goal["references"] = list(dict.fromkeys((*old.get("references", ()), "S72", "S73", "S74", "S75")))
        selected = explorer._selected(family, inputs["frontier"])
        tags = {row.name: f"{family.prefix}{index:04X}" for index, (_, row) in enumerate(selected, 1)}
        roots = _roots_for_goal(identifier, family)
        if not set(SUBSTRATE_THEOREMS[identifier]) <= _cone(root_name, by_name):
            raise explorer.GaussianFactorizationExplorerError(f"an asserted actual prerequisite is not used by {identifier}")
        closure = root["empty_context_closure"]
        evidence = {
            "implementation": "independently_closed", "alpha_version": "v30", "release_status": "alpha_closed",
            "alpha_enrolled": True, "checked_use": True, "stable_member": False,
            "full_empty_context_closure": True, "independent_lean_bundle_verified": True,
            "theorem_name": root_name, "theorem_statement_sha256": root["statement_sha256"],
            "theorem_names": list(roots), "new_theorem_count": len(selected),
            "bundle_campaign": "gaussian_factorization", "bundle_node_id": closure["bundle_node_id"],
            "bundle_nodes": bundle["node_count"], "bundle_dependencies": bundle["dependency_edges"],
            "bundle_sha256": bundle["artifact_sha256"], "bundle_path": bundle["artifact_path"],
            "route": family.slug + "/", "proof_tag": tags[root_name],
            "actual_substrate_theorem_names": list(SUBSTRATE_THEOREMS[identifier]),
            "proof_routes": [{"route": family.slug, "label": name, "tag": tags[name]} for name in roots],
        }
        evidence.update(actual_canonical_signed_pair_codes=True, gaussian_identity_code=6,
                        actual_prime_divisor_property=True, actual_norm_descent=True,
                        actual_finite_product=True, actual_unit_coefficient=True,
                        equal_factor_lengths=True, actual_bounded_bijection=True,
                        witnessed_unit_at_every_match=True, repeated_factors_included=True,
                        unit_empty_factorization_included=True, zero_excluded=True,
                        supplied_factorization_or_matching_premise=False,
                        generic_planning_predicates_aliased=False,
                        sorted_primary_representatives_claimed=False,
                        gaussian_prime_classification_claimed=False,
                        eisenstein_factorization_claimed=False)
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
            raise explorer.GaussianFactorizationExplorerError(f"missing original atlas table {name}")
    roots = re.search(r"      var PROOF_ROOTS = \{(.*?)\n      \};", source, flags=re.S)
    if roots is None:
        raise explorer.GaussianFactorizationExplorerError("missing original atlas proof destinations")
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
        raise explorer.GaussianFactorizationExplorerError("missing original data-driven atlas revision binding")
    for old_route, current_route in (
        ("constructive-second-wave-explorer-v29", "constructive-second-wave-explorer-v30"),
        ("constructive-lower-layer-explorer-v29", "constructive-lower-layer-explorer-v30"),
        ("constructive-priority-layer-explorer", "constructive-priority-layer-explorer-v30"),
    ):
        old = f'return "../{old_route}/" + route + "/explorer/defined/";'
        new = f'return "../{current_route}/" + route + "/explorer/defined/";'
        if source.count(old) + source.count(new) != 1:
            raise explorer.GaussianFactorizationExplorerError("ambiguous historical local route dispatch")
        source = source.replace(old, new)
    gaussian_routes = ('        if (route === "gaussian-factorization") {\n'
                       '          return "../constructive-gaussian-factorization-explorer/" + route + "/explorer/defined/";\n'
                       '        }')
    deployed_route = '        if (deployed) return "../" + route + "/explorer/defined/";'
    if gaussian_routes not in source:
        if source.count(deployed_route) != 1:
            raise explorer.GaussianFactorizationExplorerError("missing unique original deployed route dispatch")
        source = source.replace(deployed_route, deployed_route + "\n" + gaussian_routes)
    if source.count(gaussian_routes) != 1:
        raise explorer.GaussianFactorizationExplorerError("duplicate Gaussian-factorization local route dispatch")

    return source



def embed_current_snapshot(source: str, campaign: dict[str, Any]) -> str:
    """Bind the original atlas's inert data to this exact current campaign."""
    snapshot = json.dumps(campaign, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":"))
    if "</script" in snapshot.lower():
        raise explorer.GaussianFactorizationExplorerError(
            "current campaign JSON cannot contain a closing script element")
    if len(snapshot.encode("utf-8")) > MAX_CAMPAIGN_BYTES:
        raise explorer.GaussianFactorizationExplorerError(
            "current campaign JSON exceeds the original atlas limit")
    return _expected(source, snapshot)[1]


def build_files(inputs: dict[str, Any] | None = None) -> dict[str, bytes]:
    if inputs is None:
        inputs = explorer._load_release_inputs()
    campaign = extend_campaign(historical_campaign(), inputs)
    source = (explorer.REPO / "book/_static/constructive-priority-campaign/index.html").read_text()
    return {
        "campaign.json": explorer._json(campaign),
        "definitions.json": explorer._json(build_definition_graph(campaign)),
        "index.html": embed_current_snapshot(update_atlas_bindings(source, campaign), campaign).encode(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    explorer.write_or_check(build_files(), explorer.CAMPAIGN.parent, check=arguments.check)
    print("gaussian-factorization campaign: PASS (exact Gaussian factorization, frozen v29 parent, separate proof and definition DAGs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
