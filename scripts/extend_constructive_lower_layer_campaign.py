#!/usr/bin/env python3
"""Connect nine exact checked endpoints to the unchanged broad campaign.

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

import build_constructive_lower_layer_explorer as explorer
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_lower_layer_definition_graph import build_definition_graph
from constructive_lower_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS,
    LOWER_LAYER_DEFINITIONS, definition_closure,
)
from extend_constructive_second_wave_campaign import _table_source
from peano_lab.kernel.formulas import parse_formula_with_names


PRIMARY_ROOTS = explorer.MILESTONE_ROOTS
REFINED_PLANNING_DEFINITIONS = frozenset({"GNorm", "ENorm"})
ACTUAL_TOOL_PREREQUISITES = {
    "G001": ("T06",), "G002": ("T07",), "G003": ("T07",),
    "G004": ("T08", "T11", "T15"), "G005": ("T08", "T11", "T15"),
    "G021": ("T08", "T11"), "G022": ("A02", "T04", "T05"),
    "G081": ("T06",), "G084": ("T06",),
}
SUBSTRATE_THEOREMS = {
    "G001": ("division_remainder_exists", "division_remainder_unique"),
    "G002": ("gcd_signed_bezout_exists", "is_gcd_unique"),
    "G003": ("gauss_coprime_cancel",),
    "G004": ("prime_factorization_existence",),
    "G005": ("prime_factor_lists_matching_by_length",),
    "G021": ("prime_unbounded",),
    "G022": ("prime_unbounded", "bertrand_strict", "least_prime_above_finite_scan", "beta_prefix_extend"),
    "G081": ("signed_integer_floor_exists", "gaussian_nearest_signed_quotient_exists"),
    "G084": ("signed_integer_floor_exists",),
}
REFINEMENTS = {
    "G001": "Expose the original actual quotient/remainder relation, with both outputs uniquely determined, from a positive divisor alone.",
    "G002": "Bézout coefficients are actual canonical signed-natural codes, not unsigned variables. The endpoint also handles a=b=0 and constructs the unique canonical gcd; the old positive-sum restriction is unnecessary.",
    "G003": "The quotient witnessing divisibility of c by a is an actual existential output. No division, factorization, or coprimality oracle is supplied.",
    "G004": "The opaque planning Factorization(n,s) is refined to PrimeFactorList(n,b,c,l): two beta parameters, a finite length, actual product n, and prime entries. The relation contains no sorting premise. The incompatible two-argument planning symbol is preserved, not silently aliased.",
    "G005": "Arbitrary unordered PrimeFactorList(n,b,c,l) and PrimeFactorList(n,d,e,m) admit equal lengths and an actual beta-coded bounded, injective, surjective matching of all prime occurrences. The planning three-argument Permutation is not treated as an arity-compatible abbreviation of the eight-argument checked relation.",
    "G021": "This is an exact wrapper around the already proved prime-unboundedness foundation, not a claim of a newly discovered infinitude theorem.",
    "G022": "InitialPrimeList(b,c,k) uses two beta parameters and contains exactly the first k primes. Global least-prime transitions prove strict increase and no omission. The final theorem constructs the list, terminal entry, 2^k, and 2^(2^k) from k≠0 alone. The two-argument planning PrimeList remains distinct. Because this proof genuinely uses Bertrand, its proof-DAG layer follows the existing Bertrand anchor.",
    "G081": "The input and output naturals are genuine injectively paired canonical signed-integer codes. GDivRem contains actual multiplication and addition; GNorm is the actual sum of two signed-coordinate squares. The quotient, remainder, and both norm witnesses are constructed, with no rounded-quotient or norm-bound premise. Higher matrix or lattice theorems are not prerequisites of this proof.",
    "G084": "Eisenstein integers reuse exactly the same signed-pair carrier and addition as Gaussian integers, but have multiplication ω²+ω+1=0 and norm a²−ab+b². A fundamental-parallelogram floor quotient gives strict norm decrease; the original planning suggestion of a globally nearest hexagonal quotient is not asserted or needed. No quotient or norm-bound oracle is supplied.",
}


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
        raise explorer.LowerLayerExplorerError("a blueprint display changed the exact conservative definition")
    return source


def _definition_record(definition) -> dict[str, Any]:
    return {"parameters": list(definition.parameters), "meaning": definition.summary,
            "expansion": _blueprint_expansion(definition),
            "reviewed_definition_id": definition.stable_id,
            "reviewed_expansion_sha256": explorer._digest(definition.template_source),
            "exact_defined_expansion_equivalence_checked": True}


def _roots_for_goal(identifier: str, family) -> tuple[str, ...]:
    if identifier == "G005":
        return PRIMARY_ROOTS[identifier], "prime_factorization_exists_unique_up_to_permutation"
    if identifier == "G022":
        return tuple(name for name in family.roots if name != PRIMARY_ROOTS["G021"])
    if identifier in {"G081", "G084"}:
        return family.roots
    return (PRIMARY_ROOTS[identifier],)


def extend_campaign(original: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    from upgrade_constructive_second_wave_publication_v28 import historical_campaign

    historical = historical_campaign()
    result = deepcopy(original)
    version = result.get("meta", {}).get("current_alpha_version")
    if result.get("schema") != "constructive-grand-campaign-v1" or version not in {"v27", "v28"}:
        raise explorer.LowerLayerExplorerError("lower-layer extension requires the exact v27/v28 campaign")
    old_nodes = {row["id"]: row for row in historical["nodes"]}
    nodes = {row["id"]: row for row in result["nodes"]}
    if len(nodes) != len(result["nodes"]) or nodes.keys() != old_nodes.keys():
        raise explorer.LowerLayerExplorerError("the broad campaign milestone inventory changed")
    for identifier, node in old_nodes.items():
        if (version == "v27" or identifier not in PRIMARY_ROOTS) and explorer._json(nodes[identifier]) != explorer._json(node):
            raise explorer.LowerLayerExplorerError(f"an unrelated historical milestone changed: {identifier}")
    for field in ("anchors", "tools", "families", "layers", "language", "dependency_policy", "title", "subtitle"):
        if explorer._json(result[field]) != explorer._json(historical[field]):
            raise explorer.LowerLayerExplorerError(f"historical campaign structure changed: {field}")
    for name, boundary in historical["ambitious_boundaries"].items():
        expected = deepcopy(boundary)
        if version == "v28" and name == "alpha_v27_edition":
            expected["role"] = "historical_immutable_release"
        if explorer._json(result["ambitious_boundaries"].get(name)) != explorer._json(expected):
            raise explorer.LowerLayerExplorerError(f"an immutable historical release boundary changed: {name}")
    historical_sources = historical["sources"]
    if explorer._json(result["sources"][:len(historical_sources)]) != explorer._json(historical_sources):
        raise explorer.LowerLayerExplorerError("historical campaign provenance changed")
    expected_names = set(historical["definitions"]) | {item.name for item in LOWER_LAYER_DEFINITIONS}
    if set(result["definitions"]) - expected_names:
        raise explorer.LowerLayerExplorerError("an unreviewed definition was added to the frozen campaign inventory")
    for name, record in historical["definitions"].items():
        if name not in REFINED_PLANNING_DEFINITIONS and explorer._json(result["definitions"].get(name)) != explorer._json(record):
            raise explorer.LowerLayerExplorerError(f"a historical blueprint definition changed: {name}")
    planned = {name: deepcopy(historical["definitions"][name]) for name in REFINED_PLANNING_DEFINITIONS}
    if "historical_lower_layer_definition_plan" in result and explorer._json(result["historical_lower_layer_definition_plan"]) != explorer._json(planned):
        raise explorer.LowerLayerExplorerError("an original unreviewed norm plan was rewritten")
    result["historical_lower_layer_definition_plan"] = planned
    for definition in LOWER_LAYER_DEFINITIONS:
        expected = _definition_record(definition)
        name = definition.name
        if name in result["definitions"] and not (version == "v27" and name in REFINED_PLANNING_DEFINITIONS):
            if explorer._json(result["definitions"][name]) != explorer._json(expected):
                raise explorer.LowerLayerExplorerError(f"an exact introduced definition changed: {name}")
        result["definitions"][name] = expected

    catalog, bundle = inputs["catalog"], inputs["bundle"]
    metadata = result["meta"]
    metadata.update(current_alpha_version="v28", current_alpha_checked_use_count=catalog["checked_use_count"],
                    lower_layer_named_targets=list(PRIMARY_ROOTS), lower_layer_new_theorem_count=len(inputs["frontier"]))
    if "v27" not in metadata["historical_alpha_versions"]:
        metadata["historical_alpha_versions"].append("v27")
    source_rows = (
        ("S62", "release_manifest", "Current Alpha v28 independently checked lower-layer channels", "artifacts/peano-library/channels-v28.json"),
        ("S63", "independent_proof_artifact", "Complete original-kernel and Lean-verified lower-layer proof bundle", explorer.EXPECTED_BUNDLE_PATH),
        ("S64", "independent_closure_record", "Exact lower-layer closure receipt and scope boundaries", "research/arithmetic-library/alpha-v28-lower-layer-receipt.md"),
        ("S65", "admission_record", "Immutable additive Alpha v28 lower-layer admission contract", "research/arithmetic-library/alpha-v28-lower-layer-rfc-v1.md"),
        ("S66", "historical_presentation_projection", "Exact archived v27 atlas inputs for unchanged historical checks", "research/arithmetic-library/artifacts/alpha-v27-campaign-projection-v1.json"),
    )
    known_sources = {row["id"]: row for row in result["sources"]}
    if len(known_sources) != len(result["sources"]):
        raise explorer.LowerLayerExplorerError("campaign provenance repeats a source identifier")
    if set(known_sources) - {row["id"] for row in historical_sources} - {row[0] for row in source_rows}:
        raise explorer.LowerLayerExplorerError("an unrelated provenance source entered this extension")
    for identifier, kind, label, path in source_rows:
        row = {"id": identifier, "kind": kind, "label": label, "path": path}
        if identifier in known_sources and known_sources[identifier] != row:
            raise explorer.LowerLayerExplorerError("lower-layer provenance source changed")
        if identifier not in known_sources:
            result["sources"].append(row)
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v27_edition"]["role"] = "historical_immutable_release"
    boundaries["alpha_v28_edition"] = {
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
        "frontier_new_names_sha256": catalog["frontier_v28_ordered_names_sha256"],
        "stable_unchanged": True, "historical_v27_unchanged": True,
        "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_exact_lower_layer_targets",
    }
    boundaries["lower_layer_evidence_transition"] = {
        "parent_v27_theorem_count": 2560, "new_theorem_count": len(inputs["frontier"]),
        "current_v28_theorem_count": catalog["theorem_count"],
        "authoring_campaign_counts": dict(Counter(owner.campaign for owner, _ in inputs["frontier"])),
        "presentation_family_counts": {family.slug: len(explorer._selected(family, inputs["frontier"])) for family in explorer.FAMILIES},
        "presentation_origin_distinction": "The existing prime-unboundedness wrapper is authored under foundations and displayed with prime enumeration; no theorem is duplicated or re-admitted.",
        "bundle_node_count": bundle["node_count"], "dependency_edge_count": bundle["dependency_edges"],
        "body_proof_nodes": bundle["body_proof_nodes"], "bundle_bytes": bundle["artifact_bytes"],
        "bundle_sha256": bundle["artifact_sha256"], "original_kernel_call_count": bundle["kernel_calls"],
        "independent_lean_bundle_verified": True, "stable_unchanged": True, "historical_v27_unchanged": True,
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
                raise explorer.LowerLayerExplorerError(f"historical goal planning data changed: {identifier}")
            goal[field] = deepcopy(value)
        for field in ("id", "kind", "title", "family", "difficulty"):
            if goal.get(field) != old.get(field):
                raise explorer.LowerLayerExplorerError(f"the original milestone identity changed: {identifier}")
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
        goal["references"] = list(dict.fromkeys((*old.get("references", ()), "S62", "S63", "S64", "S65")))
        selected = explorer._selected(family, inputs["frontier"])
        tags = {row.name: f"{family.prefix}{index:04X}" for index, (_, row) in enumerate(selected, 1)}
        roots = _roots_for_goal(identifier, family)
        if not set(SUBSTRATE_THEOREMS[identifier]) <= _cone(root_name, by_name):
            raise explorer.LowerLayerExplorerError(f"an asserted actual prerequisite is not used by {identifier}")
        closure = root["empty_context_closure"]
        evidence = {
            "implementation": "independently_closed", "alpha_version": "v28", "release_status": "alpha_closed",
            "alpha_enrolled": True, "checked_use": True, "stable_member": False,
            "full_empty_context_closure": True, "independent_lean_bundle_verified": True,
            "theorem_name": root_name, "theorem_statement_sha256": root["statement_sha256"],
            "theorem_names": list(roots), "new_theorem_count": len(selected),
            "bundle_campaign": "lower_layer", "bundle_node_id": closure["bundle_node_id"],
            "bundle_nodes": bundle["node_count"], "bundle_dependencies": bundle["dependency_edges"],
            "bundle_sha256": bundle["artifact_sha256"], "bundle_path": bundle["artifact_path"],
            "route": family.slug + "/", "proof_tag": tags[root_name],
            "actual_substrate_theorem_names": list(SUBSTRATE_THEOREMS[identifier]),
            "proof_routes": [{"route": family.slug, "label": name, "tag": tags[name]} for name in roots],
        }
        if identifier == "G002":
            evidence.update(actual_signed_coefficient_codes_proved=True, zero_zero_case_included=True)
        elif identifier in {"G004", "G005"}:
            evidence.update(arbitrary_unsorted_prime_factor_lists=True, sortedness_premise=False,
                            actual_matching_bijection_proved=identifier == "G005")
        elif identifier == "G022":
            evidence.update(actual_first_primes_proved=True, no_omission_proved=True,
                            actual_power_witnesses_constructed=True, supplied_prime_list_premise=False)
        elif identifier in {"G081", "G084"}:
            evidence.update(actual_canonical_signed_pair_codes=True, actual_ring_operations_proved=True,
                            actual_norms_constructed=True, full_euclidean_division_proved=True,
                            supplied_quotient_or_norm_bound_premise=False,
                            unique_factorization_claimed=False, prime_classification_claimed=False)
            if identifier == "G084":
                evidence["globally_nearest_quotient_claimed"] = False
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
            raise explorer.LowerLayerExplorerError(f"missing original atlas table {name}")
    roots = re.search(r"      var PROOF_ROOTS = \{(.*?)\n      \};", source, flags=re.S)
    if roots is None:
        raise explorer.LowerLayerExplorerError("missing original atlas proof destinations")
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
        raise explorer.LowerLayerExplorerError("missing original data-driven atlas revision binding")
    original_route = 'return "../constructive-second-wave-explorer/" + route + "/explorer/defined/";'
    current_route = 'return "../constructive-second-wave-explorer-v28/" + route + "/explorer/defined/";'
    if source.count(original_route) + source.count(current_route) != 1:
        raise explorer.LowerLayerExplorerError("missing unique historical/current second-wave local route")
    source = source.replace(original_route, current_route)
    lower_routes = ('        if (["arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers"].indexOf(route) !== -1) {\n'
                    '          return "../constructive-lower-layer-explorer/" + route + "/explorer/defined/";\n'
                    '        }')
    deployed_route = '        if (deployed) return "../" + route + "/explorer/defined/";'
    if lower_routes not in source:
        if source.count(deployed_route) != 1:
            raise explorer.LowerLayerExplorerError("missing unique original deployed route dispatch")
        source = source.replace(deployed_route, deployed_route + "\n" + lower_routes)
    if source.count(lower_routes) != 1:
        raise explorer.LowerLayerExplorerError("duplicate lower-layer local route dispatch")
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    inputs = explorer._load_release_inputs()
    original = explorer._strict_json(explorer.CAMPAIGN.read_bytes())
    campaign = extend_campaign(original, inputs)
    atlas = explorer.CAMPAIGN.with_name("index.html")
    source, payload = atlas.read_text(), explorer._json(campaign)
    expected = update_atlas_bindings(source, campaign)
    if arguments.check:
        if explorer._json(campaign) != explorer._json(original) or source != expected:
            raise explorer.LowerLayerExplorerError("the lower-layer campaign extension is stale")
    else:
        if explorer.CAMPAIGN.read_bytes() != payload:
            explorer.CAMPAIGN.write_bytes(payload)
        if source != expected:
            atlas.write_text(expected)
    print("lower-layer campaign: PASS (exact targets, unchanged historical proofs, separate DAGs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
