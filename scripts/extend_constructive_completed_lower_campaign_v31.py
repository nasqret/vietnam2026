#!/usr/bin/env python3
"""Add exact completed lower-layer evidence to the unchanged broad blueprint.

The 120-goal planning graph, the actual checked-theorem DAG and conservative
definition DAG remain separate. G007 and G014 are closed by their exact
finite-table/Euler theorems; G009 retains its multiplicative-closure obligation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import re

import constructive_completed_lower_publication_v31 as publication
from constructive_dirichlet_inverse_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS, definition_closure,
)
from constructive_dirichlet_inverse_definition_graph import build_definition_graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from extend_constructive_second_wave_campaign import _table_source
from sync_constructive_grand_campaign import MAX_CAMPAIGN_BYTES, _expected, validate_campaign_dags
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.theorems import _closed_formula


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "constructive-completed-lower-campaign-v31"
OUTPUT = ROOT / "book/_static" / OUTPUT_NAME
PARENT = ROOT / "book/_static/constructive-gaussian-campaign"
PARENT_PINS = {
    "campaign.json": "2f0d367c693a51abc3af9fb0dde9e60ee83cbb9e1d51c1c3915b7e6b98f88764",
    "index.html": "1db67dfce7e7c34863732720706e30a8ef41273998af990025ecf975eebc2fe4",
    "definitions.json": "57c3d1e786d4107eadfa1a1e04c81610fdd060d24ff1eab32ff9c7ed1a4278fd",
}
G007_ROOT = "mobius_inversion_arithmetic_tables"
G014_ROOT = "euler_coprime_totient_power"
G009_COMPONENT = "dirichlet_inverse_criterion"
G007_REFINEMENT = (
    "For every actual finite signed input table F and divisor-transform table G, "
    "construct a real Mobius table and a convolution result equal to F on every "
    "positive represented index. The divisor-sum hypothesis holds at all positive "
    "inputs, not only at one selected value. Zero-index values are unrestricted. "
    "The finite transform and its Mobius inverse are proved, not built into a definition."
)
G009_REMAINING = (
    "Prove convolution closure for normalized multiplicative functions on a nonempty positive finite prefix.",
    "Construct the coprime-divisor decomposition and genuine support-sensitive finite-sum reindexing.",
    "Keep normalization F(1)=+1 distinct from the inverse criterion F(1)=+1 or -1.",
)


def _json(value):
    payload = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    if len(payload) > MAX_CAMPAIGN_BYTES:
        raise publication.PublicationError("campaign output exceeds the unchanged 8 MiB document bound")
    return payload


def historical_files():
    result = {}
    for name, expected in PARENT_PINS.items():
        path = PARENT / name
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_CAMPAIGN_BYTES:
            raise publication.PublicationError("immutable campaign parent has unsafe type or size")
        with path.open("rb") as stream:
            payload = stream.read(MAX_CAMPAIGN_BYTES + 1)
        if len(payload) > MAX_CAMPAIGN_BYTES or sha256(payload).hexdigest() != expected:
            raise publication.PublicationError("immutable Gaussian campaign parent changed")
        result[name] = payload
    return result


def _definition_record(definition):
    dependencies = definition_closure(tuple(definition.conceptual_dependencies))
    reading = _FormulaCompactor(dependencies).compact(definition.template_source)
    # Preserve the original planning Sum(n,f,s) and actual four-argument beta
    # sum as different signatures; never silently alias unlike definitions.
    source = re.sub(r"\bSum\(", "BetaSum(", reading["defined_statement"])
    aliases = {**DEFINITIONS, "BetaSum": replace(DEFINITIONS["Sum"], name="BetaSum")}
    exact, free_names = parse_formula_with_names(definition.template_source)
    parser = _LocalDefinedParser(source, aliases)
    parser.free = list(free_names)
    if parser.parse() != exact or tuple(parser.free) != free_names:
        raise publication.PublicationError("a campaign definition changed its conservative exact expansion")
    return {"parameters": list(definition.parameters), "meaning": definition.summary, "expansion": source,
            "reviewed_definition_id": definition.stable_id,
            "reviewed_expansion_sha256": publication.digest(definition.template_source),
            "exact_defined_expansion_equivalence_checked": True}


def _exact_display(node, row):
    publication._check_literal_row(node, row)
    reading = node["defined"]
    source = reading["defined_statement"]
    parser = _LocalDefinedParser(source, DEFINITIONS)
    if (parser.parse() != _closed_formula(row["statement"]) or parser.free
            or reading["expanded_statement_sha256"] != row["statement_sha256"]):
        raise publication.PublicationError("the exact campaign endpoint changed under defined notation")
    return source


def _routes(family):
    return [{"route": family["slug"], "label": name, "tag": family["root_tags"][name]}
            for name in family["root_names"]]


def _extend(original, catalog, families, corpora, reports, catalog_sha256):
    """Pure exact evidence projection; only the live wrapper may publish it."""
    if (original.get("schema") != "constructive-grand-campaign-v1"
            or original.get("meta", {}).get("current_alpha_version") != "v30"
            or len(original.get("nodes", ())) != 144 or original["meta"]["goal_count"] != 120
            or catalog.get("schema") != "peano-library-alpha-snapshot-v31"
            or type(catalog.get("checked_use_count")) is not int or catalog["checked_use_count"] != 3796):
        raise publication.PublicationError("the exact parent or current campaign release changed")
    result = deepcopy(original)
    goals = {row["id"]: row for row in result["nodes"]}
    by_name = {row["name"]: row for row in catalog["theorems"]}
    if (len(families) != 19 or sum(row["theorem_count"] for row in families) != 574
            or len({row["slug"] for row in families}) != 19
            or set(reports) != {row["slug"] for row in families}):
        raise publication.PublicationError("the exact admitted lower-layer family inventory changed")
    metadata = result["meta"]
    metadata.update(current_alpha_version="v31", current_alpha_checked_use_count=3796,
                    completed_lower_new_theorem_count=574, completed_lower_family_count=19,
                    completed_lower_release_date="2026-08-29", completed_lower_named_targets=["G007", "G014"])
    metadata["historical_alpha_versions"].append("v30")
    # Preserve every old blueprint definition, even where an old planning
    # name is not signature-compatible with the actual reviewed predicate.
    for name, definition in DEFINITIONS.items():
        if name not in result["definitions"]:
            result["definitions"][name] = _definition_record(definition)
    result["completed_lower_chapters"] = deepcopy(list(families))
    for family in families:
        report = reports[family["slug"]]
        if (report["new_theorem_count"] != family["theorem_count"]
                or not set(family["root_names"]) <= report["owned_node_ids"].keys()):
            raise publication.PublicationError("a chapter has unverified exact endpoints")
        for name in family["root_names"]:
            if name not in by_name or by_name[name]["checked_use"] is not True:
                raise publication.PublicationError("a chapter references an unavailable checked theorem")
        for identifier in family["goals"]:
            if identifier not in goals:
                raise publication.PublicationError("a chapter references an unknown blueprint goal")
            goals[identifier].setdefault("additional_checked_chapters", []).append({
                "slug": family["slug"], "title": family["title"], "theorem_count": family["theorem_count"],
                "proof_routes": _routes(family), "closes_full_milestone": False,
            })
    mobius = next(row for row in families if row["slug"] == "mobius-inversion")
    root = by_name[G007_ROOT]
    original_root = next(row for row in corpora["mobius-inversion"]["nodes"] if row["name"] == G007_ROOT)
    statement = _exact_display(original_root, root)
    goal = goals["G007"]
    goal.update(historical_planned_statement=original_root_statement(original, "G007"),
                historical_foundation_classification="open", status="alpha_closed", statement=statement,
                why=G007_REFINEMENT, representation_refinement=G007_REFINEMENT)
    used_ids = set(original_root["defined"]["statement_definition_uses"])
    goal["definition_refs"] = [definition.name for definition in DEFINITIONS.values() if definition.stable_id in used_ids]
    closure = root["empty_context_closure"]
    bundle = reports["mobius-inversion"]["bundle"]
    goal["evidence"] = {
        "implementation": "independently_closed", "alpha_version": "v31", "release_status": "alpha_closed",
        "alpha_enrolled": True, "checked_use": True, "stable_member": False,
        "full_empty_context_closure": True, "independent_lean_bundle_verified": True,
        "theorem_name": G007_ROOT, "theorem_statement_sha256": root["statement_sha256"],
        "theorem_names": list(mobius["root_names"]), "new_theorem_count": mobius["theorem_count"],
        "bundle_campaign": "mobius-inversion", "bundle_node_id": closure["bundle_node_id"],
        "bundle_nodes": bundle["nodes_including_packaging_root"],
        "bundle_dependencies": bundle["dependency_edges_including_packaging"],
        "bundle_path": bundle["path"], "bundle_sha256": bundle["sha256"],
        "route": "mobius-inversion/", "proof_tag": mobius["tags"][G007_ROOT],
        "proof_routes": _routes(mobius), "actual_signed_finite_tables": True,
        "divisor_hypothesis_at_every_positive_input": True, "unrestricted_zero_values": True,
        "multiplicative_closure_claimed": False,
    }
    goal["references"] = list(dict.fromkeys((*goal.get("references", ()), "S77", "S78", "S79")))
    for chapter in goal["additional_checked_chapters"]:
        chapter["closes_full_milestone"] = chapter["slug"] == "mobius-inversion"
    # The nonzero-modulus root covers PLAN/14's n=1 boundary as well as
    # composite moduli. The explicit-unit endpoint is separately checked too.
    euler = next(row for row in families if row["slug"] == "euler-units")
    euler_root = by_name[G014_ROOT]
    euler_original = next(row for row in corpora["euler-units"]["nodes"] if row["name"] == G014_ROOT)
    euler_bundle = reports["euler-units"]["bundle"]
    euler_goal = goals["G014"]
    euler_goal.update(
        historical_planned_statement=original_root_statement(original, "G014"),
        historical_foundation_classification="open", status="alpha_closed",
        statement=_exact_display(euler_original, euler_root),
        why="For every nonzero modulus, actual totient count and coprime residue, construct a power witness congruent to one. The unit formulation and modulus one are included.",
    )
    used_ids = set(euler_original["defined"]["statement_definition_uses"])
    euler_goal["definition_refs"] = [definition.name for definition in DEFINITIONS.values() if definition.stable_id in used_ids]
    euler_goal["evidence"] = {
        "implementation": "independently_closed", "alpha_version": "v31", "release_status": "alpha_closed",
        "alpha_enrolled": True, "checked_use": True, "stable_member": False,
        "full_empty_context_closure": True, "independent_lean_bundle_verified": True,
        "theorem_name": G014_ROOT, "theorem_statement_sha256": euler_root["statement_sha256"],
        "theorem_names": list(euler["root_names"]), "new_theorem_count": euler["theorem_count"],
        "bundle_campaign": "euler-units", "bundle_node_id": euler_root["empty_context_closure"]["bundle_node_id"],
        "bundle_nodes": euler_bundle["nodes_including_packaging_root"],
        "bundle_dependencies": euler_bundle["dependency_edges_including_packaging"],
        "bundle_path": euler_bundle["path"], "bundle_sha256": euler_bundle["sha256"],
        "route": "euler-units/", "proof_tag": euler["tags"][G014_ROOT], "proof_routes": _routes(euler),
        "modulus_one_included": True, "zero_modulus_excluded": True,
        "actual_totient_count": True, "actual_power_witness": True,
    }
    euler_goal["references"] = list(dict.fromkeys((*euler_goal.get("references", ()), "S77", "S78", "S79")))
    for chapter in euler_goal["additional_checked_chapters"]:
        chapter["closes_full_milestone"] = chapter["slug"] == "euler-units"
    # The condensed old atlas omitted one obligation present in PLAN/14.
    # Keep that full original obligation visible; inverse construction alone
    # is not declared to complete multiplicativity or the entire G009 goal.
    g009 = goals["G009"]
    g009["remaining_obligations"] = list(G009_REMAINING)
    g009["why"] = original_root_why(original, "G009") + " Remaining: " + " ".join(G009_REMAINING)
    g009["evidence"] = {
        "checked_use": False, "stable_member": False, "alpha_enrolled": False,
        "implementation": "checked_components_full_milestone_open",
        "partial_component_checked_use": True, "partial_theorem_name": G009_COMPONENT,
        "partial_theorem_statement_sha256": by_name[G009_COMPONENT]["statement_sha256"],
        "checked_theorem_names": [name for family in families if family["slug"].startswith("dirichlet-")
                                  for name in family["root_names"]],
        "proof_routes": [route for family in families if family["slug"].startswith("dirichlet-") for route in _routes(family)],
        "multiplicative_convolution_closure_proved": False,
        "inverse_criterion_includes_both_signed_units": True,
        "normalization_at_one_for_multiplicativity": "+1 only; not the signed-unit disjunction",
        "original_full_contract": "PLAN/14_constructive_number_theory_grand_campaign.md",
    }
    if g009["status"] != "open" or goals["G091"]["status"] != "open":
        raise publication.PublicationError("a partial chapter silently closed G009 or G091")
    for identifier, node in goals.items():
        old = next(row for row in original["nodes"] if row["id"] == identifier)
        if identifier not in {"G007", "G009", "G014"}:
            filtered = {key: value for key, value in node.items() if key != "additional_checked_chapters"}
            if filtered != old:
                raise publication.PublicationError("an unrelated historical goal changed")
    sources = (
        {"id": "S77", "kind": "release_manifest", "label": "Current Alpha v31 checked completed-lower channels", "path": "artifacts/peano-library/channels-v31.json"},
        {"id": "S78", "kind": "independent_closure_record", "label": "Fresh nineteen-bundle HA/Lean and 52 ordinary-principal release audit", "path": "research/arithmetic-library/artifacts/alpha-v31-completed-lower-receipt-v1.json"},
        {"id": "S79", "kind": "admission_record", "label": "Additive Alpha v31 contract and exact remaining boundaries", "path": "research/arithmetic-library/alpha-v31-completed-lower-rfc-v1.md"},
        {"id": "S80", "kind": "historical_presentation_parent", "label": "Byte-exact original Gaussian campaign", "path": "book/_static/constructive-gaussian-campaign/campaign.json"},
    )
    if {row["id"] for row in sources}.intersection(row["id"] for row in result["sources"]):
        raise publication.PublicationError("a campaign provenance identifier was reused")
    result["sources"].extend(sources)
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v30_edition"]["role"] = "historical_immutable_release"
    boundaries["alpha_v31_edition"] = {
        "role": "current_immutable_release", "theorem_count": 3796, "checked_use_count": 3796,
        "stable_closed_count": 432, "alpha_closed_count": 3364, "body_checked_count": 0,
        "pending_layered_closure_count": 0, "checked_use_promotion_count": 574, "new_theorem_count": 574,
        "dependency_edge_count": catalog["edge_count"], "checked_dependency_edge_count": catalog["edge_count"],
        "layer_count": catalog["layer_count"], "enrollment_sha256": catalog["ordered_enrollment_root_sha256"],
        "identity_sha256": catalog["edition_identity_sha256"], "catalog_sha256": catalog_sha256,
        "evidence_root_sha256": catalog["evidence_root_sha256"], "stable_unchanged": True,
        "historical_v30_unchanged": True, "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_completed_lower_layers",
    }
    boundaries["completed_lower_evidence_transition"] = {
        "parent_v30_theorem_count": 3222, "new_theorem_count": 574, "current_v31_theorem_count": 3796,
        "new_family_count": 19, "proof_bundle_count": 19, "ordinary_principal_count": 52,
        "completed_named_targets": ["G007", "G014"], "full_G009_multiplicative_closure": "open",
        "full_G091_prime_power_field_construction": "open", "definitions_are_not_proofs": True,
        "historical_local_receipts_relabelled": False, "broader_roadmap_bullets_automatically_closed": False,
    }
    return result


def original_root_statement(original, name):
    return next(row["statement"] for row in original["nodes"] if row["id"] == name)


def original_root_why(original, name):
    return next(row["why"] for row in original["nodes"] if row["id"] == name)


def _html(source, campaign, graph, families):
    for name, key, compatible in (("COMPILED_DEFINITIONS", "compatible_reviewed_matches", True),
                                  ("INCOMPATIBLE_DEFINITIONS", "incompatible_reviewed_matches", False)):
        rows = [{**row, "route": graph.get("definition_page_overrides", {}).get(row["reviewed_id"], {}).get("route", row["route"])}
                for row in graph[key]]
        source, count = re.subn(r"      var " + name + r" = \{.*?\n      \};",
                                lambda _match: _table_source(name, rows, compatible=compatible), source, count=1, flags=re.S)
        if count != 1:
            raise publication.PublicationError("missing original conservative atlas table")
    roots = {row["id"]: row for row in campaign["nodes"]}
    descriptor = "".join(
        f'        {identifier}: {{ route: {json.dumps(route)}, label: {json.dumps(label)}, tag: {json.dumps(roots[identifier]["evidence"]["proof_tag"])} }},\n'
        for identifier, route, label in (("G007", "mobius-inversion", "Möbius inversion on divisors"),
                                         ("G014", "euler-units", "Euler’s theorem for units")))
    if source.count("      var PROOF_ROOTS = {\n") != 1 or re.search(r"^\s*G0(?:07|14):", source, flags=re.M):
        raise publication.PublicationError("ambiguous original campaign proof-root table")
    source = source.replace("      var PROOF_ROOTS = {\n", "      var PROOF_ROOTS = {\n" + descriptor, 1)
    route_map = {family["slug"]: publication.OUTPUT_NAME for family in families}
    # All historical proof routes now live in one separately generated current
    # presentation tree; unchanged original artifacts stay independently linked.
    replacement = (
        '      function explorerBase(route) {\n'
        '        var deployed = /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "");\n'
        '        if (deployed) return "../" + route + "/explorer/defined/";\n'
        '        var currentFamilies = ' + json.dumps(route_map, sort_keys=True) + ';\n'
        '        var directory = currentFamilies[route] || "' + publication.HISTORICAL_OUTPUT_NAME + '";\n'
        '        return "../" + directory + "/" + route + "/explorer/defined/";\n'
        '      }\n\n'
    )
    source, count = re.subn(r"      function explorerBase\(route\) \{.*?\n      \}\n\n",
                            lambda _match: replacement, source, count=1, flags=re.S)
    if count != 1:
        raise publication.PublicationError("missing unique original atlas route dispatcher")
    marker = '        if (node.id === "G078" && proved(node)) {'
    insertion = (
        '        if (node.evidence && node.evidence.partial_component_checked_use && Array.isArray(node.evidence.proof_routes)) {\n'
        '          node.evidence.proof_routes.forEach(function (descriptor) {\n'
        '            include(descriptor, "Verified component — the full campaign remains open");\n'
        '          });\n'
        '        }\n'
        '        (node.additional_checked_chapters || []).forEach(function (chapter) {\n'
        '          (chapter.proof_routes || []).forEach(function (descriptor) {\n'
        '            include(descriptor, "Additional checked chapter — inspect the exact statement");\n'
        '          });\n'
        '        });\n'
    )
    if source.count(marker) != 1:
        raise publication.PublicationError("missing unique original atlas component navigation")
    source = source.replace(marker, insertion + marker, 1)
    snapshot = json.dumps(campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if "</script" in snapshot.lower() or len(snapshot.encode()) > MAX_CAMPAIGN_BYTES:
        raise publication.PublicationError("unsafe or oversized embedded campaign snapshot")
    return _expected(source, snapshot)[1].encode()


def build_files_from_live(context):
    publication.require_live(context)
    parents = historical_files()
    original = publication.strict_json(parents["campaign.json"])
    manifests = {snapshot.directory: publication.snapshot_manifest(snapshot) for snapshot in publication.SNAPSHOTS}
    corpora = publication.frozen_corpora(manifests)
    publication.validate_definition_identities(corpora)
    families = publication.family_metadata(corpora)
    campaign = _extend(original, context.catalog, families, corpora, context.families, context.catalog_sha256)
    graph = build_definition_graph(campaign)
    if graph["reviewed_definition_count"] != 372 or graph["reviewed_definition_edge_count"] != 787:
        raise publication.PublicationError("the full conservative definition inventory changed")
    audit = validate_campaign_dags(campaign, definition_graph=graph, catalog=context.catalog,
                                   catalog_sha256=context.catalog_sha256)
    result = {"campaign.json": _json(campaign), "definitions.json": _json(graph),
              "index.html": _html(parents["index.html"].decode(), campaign, graph, families),
              "dag-audit.json": _json(asdict(audit))}
    historical_files()
    publication.require_live(context)
    return result


__all__ = ("OUTPUT", "OUTPUT_NAME", "PARENT_PINS", "G007_ROOT", "G014_ROOT", "G009_COMPONENT", "G009_REMAINING", "build_files_from_live")
