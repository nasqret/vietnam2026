"""Current v33 atlas:121 polynomial admissions and seven conservative aliases.

Only a genuine same-live v33 release may publish. The144 milestone contracts,
120 goals, all older admissions and the v32 atlas bytes remain immutable.
General division is a checked prerequisite; associativity, gcd/Bezout,
irreducible polynomials and full G091 are not claimed here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import re

import constructive_research_publication_v33 as publication
import extend_constructive_research_campaign_v32 as previous
from constructive_polynomial_euclidean_definition_graph import build_definition_graph
from peano_lab.library import campaign_research_v33_closure as research
from sync_constructive_grand_campaign import (
    MAX_CAMPAIGN_BYTES, _definition_dags, _digest, _expected, _milestone_dag,
    _projection_digest, validate_campaign_dags,
)

ROOT = Path(__file__).resolve().parents[1]
PARENT_RELATIVE = "book/_static/constructive-research-campaign-v32"
PARENT = ROOT / PARENT_RELATIVE
PARENT_PINS = {
    "campaign.json": {"bytes": 692317, "sha256": "fab08f9f1431cbef1239d0dce9ff0329ebba00978c9a4f21c092138b4f018b84"},
    "definitions.json": {"bytes": 1486171, "sha256": "f5d780020b639b2a0039f4cab0cb7aa1b66f05d5f72395c7e2f762d060b3b5f1"},
    "dag-audit.json": {"bytes": 5743, "sha256": "954827c9ec10a300542adc8d485b637f8f4acd8aaa2dbdea01ba11d79d4657dd"},
    "index.html": {"bytes": 742112, "sha256": "090e11df1b34dfdbff4debd1df8e08630f87b98582c2d335b41082240308507d"},
}
SOURCE_PATHS = (
    "scripts/extend_constructive_research_campaign_v33.py",
    "scripts/constructive_research_publication_v33.py",
    "scripts/constructive_polynomial_euclidean_definition_graph.py",
    "scripts/constructive_polynomial_euclidean_definitions.py",
    "scripts/build_constructive_polynomial_euclidean_explorer_v33.py",
    "scripts/sync_constructive_grand_campaign.py",
    "peano-lab/py/tests/test_constructive_research_campaign_v33.py",
)
SLUGS = ("polynomial-euclidean-division",)
CATALOG_PATH = "artifacts/peano-library/alpha/catalog-v33.json"
RECEIPT_PATH = "research/arithmetic-library/artifacts/alpha-v33-research-receipt-v1.json"
RFC_PATH = "research/arithmetic-library/alpha-v33-polynomial-euclidean-promotion-rfc-v1.md"
EXPECTED_COUNT, EXPECTED_EDGES = 4092, 13212
REVIEWED_COUNT, REVIEWED_EDGES = 397, 865
G091_ROOT = "prime_field_polynomial_division_execution_exists_unique"
NEW_DEFINITION_IDS = tuple(f"ND{index:04d}" for index in range(334, 341))
G091_SUMMARY = (
    "Alpha v33 admits121 exact polynomial theorems: arbitrary nonzero-divisor "
    "Euclidean execution, its coefficient identity and remainder-degree bound, "
    "execution uniqueness by decoded coefficients, genuine left padding and "
    "representation-independent addition, subtraction and multiplication. "
    "The377-node artifact has fresh original HA and same-byte compiled-Lean "
    "checks; eight principal roots have complete ordinary HA certificates. "
    "Coefficient order is highest-degree-first. Empty representations are "
    "explicit; raw beta encodings are never identified. Polynomial shift/scalar "
    "laws, associativity, arbitrary identity-pair quotient uniqueness, gcd/Bezout, "
    "irreducible-polynomial existence and general prime-power fields remain "
    "separate obligations. Full G091 remains open; Stable432 is unchanged."
)
_Error = publication.PublicationError


def _require(condition, message):
    if not condition:
        raise _Error(message)


def _json(value):
    raw = publication.json_bytes(value)
    _require(len(raw) <= MAX_CAMPAIGN_BYTES, "atlas exceeds the original8 MiB bound")
    return raw


def parent_files():
    _require(set(PARENT_PINS) == {"campaign.json", "definitions.json", "dag-audit.json", "index.html"},
             "the four-file historical atlas inventory changed")
    return {name: publication.read_pinned(PARENT / name, pin["bytes"], pin["sha256"])
            for name, pin in PARENT_PINS.items()}


def source_binding():
    from check_alpha_v33_research import _file_digest
    records = [(PARENT_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest())
               for name, raw in parent_files().items()]
    records.extend((path, *_file_digest(path, 2 * 1024 * 1024)) for path in SOURCE_PATHS)
    return sha256(publication.json_bytes(records)).hexdigest()


def _parent(parents):
    campaign = publication.strict_json(parents["campaign.json"])
    graph = publication.strict_json(parents["definitions.json"])
    audit = publication.strict_json(parents["dag-audit.json"])
    meta = campaign.get("meta", {})
    _require(campaign.get("schema") == "constructive-grand-campaign-v1"
             and meta.get("current_alpha_version") == "v32"
             and meta.get("current_alpha_checked_use_count") == 3971
             and meta.get("goal_count") == 120 and len(campaign.get("nodes", ())) == 144,
             "the exact historical144-node/120-goal atlas changed")
    nodes = {row["id"]: row for row in campaign["nodes"]}
    _require(len(nodes) == 144 and nodes["G009"]["status"] == "available"
             and nodes["G009"]["evidence"]["checked_use"] is True
             and nodes["G009"]["evidence"]["alpha_first_enrolled_version"] == "v32"
             and nodes["G091"]["status"] == "open"
             and nodes["G091"]["polynomial_prerequisite_progress"]["checked_use"] is True
             and nodes["G091"]["polynomial_prerequisite_progress"]["full_G091_proved"] is False,
             "historical G009/G091 admission boundaries changed")
    milestones, milestone_edges = _milestone_dag(campaign)
    definitions, reviewed, edges, reviewed_edges, uses, statements, declared = _definition_dags(campaign, graph)
    expected = {
        "alpha_version": "v32", "theorem_count": 3971, "theorem_edge_count": 12751,
        "milestone_count": 144, "milestone_proof_edge_count": milestone_edges,
        "milestone_dag_sha256": _projection_digest(milestones),
        "definition_count": len(definitions), "definition_edge_count": edges,
        "definition_dag_sha256": _projection_digest(definitions),
        "reviewed_definition_count": len(reviewed), "reviewed_definition_edge_count": reviewed_edges,
        "reviewed_definition_dag_sha256": _projection_digest(reviewed),
        "milestone_usage_edge_count": uses, "statement_usage_edge_count": statements,
        "declared_notation_edge_count": declared, "campaign_snapshot_sha256": _digest(campaign),
    }
    _require(all(audit.get(key) == value for key, value in expected.items())
             and len(reviewed) == 390 and reviewed_edges == 844
             and len(definitions) == 474 and edges == 855,
             "the exact parent milestone/definition audit is inconsistent")
    return campaign, graph, audit


def _package_map(metadata):
    _require(type(metadata) is tuple and len(metadata) == 66, "the exact66-family routes changed")
    result = {}
    allowed = {publication.OUTPUT_NAMES[name] for name in ("polynomial", "research", "completed", "historical")}
    for item in metadata:
        _require(type(item) is dict and type(item.get("slug")) is str
                 and re.fullmatch(r"[a-z][a-z0-9-]*", item["slug"])
                 and item["slug"] not in result and item.get("package") in allowed,
                 "duplicate, unsafe or foreign family route")
        result[item["slug"]] = item["package"]
    for phase, count in (("polynomial", 1), ("research", 2), ("completed", 19), ("historical", 44)):
        _require(sum(value == publication.OUTPUT_NAMES[phase] for value in result.values()) == count,
                 "the exact1/2/19/44 family partition changed")
    _require(result[SLUGS[0]] == publication.OUTPUT_NAMES["polynomial"],
             "the new polynomial family was assigned a foreign package")
    return result


def _graph(parent_graph, campaign, routes):
    graph = build_definition_graph(campaign)
    graph["definition_page_overrides"] = deepcopy(parent_graph["definition_page_overrides"])
    # Only the seven exact new registry identities and21 real expansion edges
    # are added. Milestone vocabulary and all390 older expansions are literal.
    old = {row["id"]: row for row in parent_graph["reviewed_definitions"]}
    new = {row["id"]: row for row in graph["reviewed_definitions"]}
    _require(len(old) == 390 and len(new) == 397 and set(new) - set(old) == set(NEW_DEFINITION_IDS)
             and all(new[key] == row for key, row in old.items())
             and graph["reviewed_definition_edge_count"] == 865,
             "a conservative expansion identity was rewritten or invented")
    for key in ("definitions", "definition_edges", "milestone_usage_edges",
                "compatible_reviewed_matches", "incompatible_reviewed_matches", "authority_policy"):
        _require(graph[key] == parent_graph[key], "the independent blueprint notation graph changed")
    return graph


def _admitted_family(family, report, by_name):
    """Validate projection inputs only; public authority is the live capability."""
    _require(type(report) is dict and report.get("slug") == family.slug
             and report.get("new_theorem_count") == family.count
             and report.get("specs_sha256") == family.specs_sha256
             and type(report.get("owned_node_ids")) is dict
             and set(report["owned_node_ids"]) == set(family.owned_names)
             and type(report.get("rows")) is list and len(report["rows"]) == family.count
             and tuple(row.get("name") for row in report["rows"]) == family.owned_names,
             "current family report lost its exact source ownership")
    bundle = report.get("bundle", {})
    _require(type(bundle) is dict and bundle.get("path") == family.artifact
             and bundle.get("bytes") == family.artifact_bytes and bundle.get("sha256") == family.artifact_sha256
             and bundle.get("nodes_including_packaging_root") == family.node_count
             and bundle.get("dependency_edges_including_packaging") == family.bundle_edges
             and bundle.get("body_proof_nodes") == family.body_nodes
             and bundle.get("kernel_calls") == family.node_count
             and bundle.get("original_ha_checked") is True and bundle.get("independent_lean_checked") is True,
             "current admission lost an exact complete HA/Lean proof bundle")
    for name in family.owned_names:
        row = by_name.get(name)
        _require(type(row) is dict and row.get("name") == name
                 and row.get("checked_use") is True and row.get("body_checked") is True
                 and row.get("membership") == "alpha_only" and row.get("evidence_status") == "alpha_closed",
                 "a research theorem has no actual current Alpha checked-use record")
        closure, admission = row.get("empty_context_closure", {}), row.get("alpha_v33_frontier_enrollment", {})
        _require(closure.get("status") == "checked" and closure.get("kernel_mode") == "intuitionistic"
                 and closure.get("certificate_sha256") == family.artifact_sha256
                 and closure.get("bundle_node_id") == report["owned_node_ids"][name]
                 and admission.get("first_enrolled_version") == "v33"
                 and admission.get("campaign") == family.slug
                 and admission.get("bundle_sha256") == family.artifact_sha256
                 and admission.get("bundle_node_id") == report["owned_node_ids"][name],
                 "current admission does not match its original exact bundle node")
    principals = report.get("principal_roots")
    _require(type(principals) is list
             and tuple(row.get("name") for row in principals) == family.principal_roots,
             "current atlas evidence omitted an ordinary principal")
    for principal in principals:
        name = principal["name"]
        _require(principal.get("complete_ordinary_ha_checked") is True
                 and type(principal.get("ordinary_certificate_nodes")) is int
                 and 1 < principal["ordinary_certificate_nodes"] <= 500000
                 and principal.get("node_id") == report["owned_node_ids"][name]
                 and principal.get("statement_sha256") == by_name[name].get("statement_sha256")
                 and principal["statement_sha256"] == family.principal_statement_sha256[name],
                 "an exact ordinary principal is missing or substituted")
    return principals



def _project(original, catalog, reports, catalog_sha256, source_binding_sha256, routes):
    research.validate_research_metadata()
    rows = catalog.get("theorems")
    _require(catalog.get("schema") == "peano-library-alpha-snapshot-v33"
             and catalog.get("theorem_count") == catalog.get("checked_use_count") == EXPECTED_COUNT
             and catalog.get("stable_count") == 432 and catalog.get("edge_count") == EXPECTED_EDGES
             and type(rows) is list and len(rows) == EXPECTED_COUNT
             and len({row.get("name") for row in rows}) == EXPECTED_COUNT
             and tuple(row.get("name") for row in rows[3971:]) == research.FRONTIER_NEW_NAMES
             and type(reports) is dict and tuple(reports) == SLUGS
             and re.fullmatch(r"[0-9a-f]{64}", catalog_sha256)
             and re.fullmatch(r"[0-9a-f]{64}", source_binding_sha256),
             "the current atlas lacks the exact3971+121 release")
    by_name = {row["name"]: row for row in rows}
    _require(len(research.FAMILIES) == 1, "new family inventory changed")
    family, report = research.FAMILIES[0], reports[SLUGS[0]]
    principals = _admitted_family(family, report, by_name)
    result = deepcopy(original)
    node = next(row for row in result["nodes"] if row["id"] == "G091")
    original_node = next(row for row in original["nodes"] if row["id"] == "G091")
    metadata = publication._new_family_metadata()
    tags = metadata["tags"]
    proof_routes = [{"label": name, "route": SLUGS[0], "tag": tags[name]}
                    for name in family.principal_roots]
    node["polynomial_euclidean_progress"] = {
        "scope": "alpha_v33_general_division_and_representation_laws",
        "summary": G091_SUMMARY, "new_theorem_count": 121,
        "alpha_version": "v33", "alpha_first_enrolled_version": "v33",
        "alpha_enrolled": True, "checked_use": True, "stable_member": False,
        "full_G091_proved": False, "division_execution_proved": True,
        "execution_uniqueness_proved": True, "formal_representation_congruence_proved": True,
        "arbitrary_identity_pair_quotient_uniqueness_proved": False,
        "polynomial_associativity_proved": False, "polynomial_gcd_bezout_proved": False,
        "bundle": deepcopy(report["bundle"]), "principal_roots": deepcopy(principals),
        "representative_theorem_name": G091_ROOT, "representative_proof_tag": tags[G091_ROOT],
        "representative_statement_sha256": by_name[G091_ROOT]["statement_sha256"],
        "proof_routes": proof_routes, "conservative_definition_ids": list(NEW_DEFINITION_IDS),
        "current_release_receipt": RECEIPT_PATH, "current_catalog_sha256": catalog_sha256,
        "current_source_binding_sha256": source_binding_sha256,
        "remaining_obligations": [
            "shift_and_scalar_convolution_laws", "polynomial_multiplication_associativity",
            "arbitrary_identity_pair_quotient_uniqueness", "polynomial_gcd_and_bezout",
            "irreducible_polynomials_in_every_positive_degree", "prime_power_quotient_fields",
        ],
    }
    node["additional_checked_chapters"].append({
        "slug": SLUGS[0], "title": metadata["title"], "theorem_count": 121,
        "closes_full_milestone": False, "full_G091_proved": False,
        "authority": "alpha_v33_checked_use", "alpha_checked_use": True,
        "alpha_edition_version": "v33", "alpha_first_enrolled_version": "v33",
        "stable_member": False, "proof_routes": proof_routes,
    })
    node["historical_v32_polynomial_progress"] = {
        "source": PARENT_RELATIVE + "/campaign.json", **PARENT_PINS["campaign.json"],
        "stored_record_is_new_proof_authority": False, "record": deepcopy(original_node),
    }
    node["why"] = original_node["why"].split("\n\n", 1)[0] + "\n\n" + G091_SUMMARY
    meta = result["meta"]
    _require("v32" not in meta["historical_alpha_versions"], "v32 history was already appended")
    meta["historical_alpha_versions"].append("v32")
    meta.update(current_alpha_version="v33", current_alpha_checked_use_count=EXPECTED_COUNT,
                current_alpha_catalog_sha256=catalog_sha256,
                current_alpha_identity_sha256=catalog["edition_identity_sha256"],
                current_research_new_theorem_count=121, current_research_family_count=1,
                current_G009_alpha_admitted=True, current_G091_proved=False,
                reviewed_definition_count=397, reviewed_definition_edge_count=865,
                alpha_catalog_remaining_entry_slots=4)
    result["current_proof_family_packages"] = dict(routes)
    sources = [
        {"id": "S106", "kind": "release_manifest", "label": "Current Alpha v33 polynomial admission", "path": CATALOG_PATH},
        {"id": "S107", "kind": "independent_closure_record", "label": "Fresh377-node HA/Lean and eight ordinary-root checks", "path": RECEIPT_PATH},
        {"id": "S108", "kind": "admission_record", "label": "Exact121-row admission and open associativity/gcd/G091 boundaries", "path": RFC_PATH},
        {"id": "S109", "kind": "historical_presentation_parent", "label": "Literal v32 atlas before polynomial Euclidean admission", "path": PARENT_RELATIVE + "/campaign.json"},
    ]
    sources.extend({"id": f"S{110 + index}", "kind": "checked_source_module",
                    "label": f"Alpha v33 exact{owner.count}-theorem source: {owner.module}",
                    "path": owner.source, "bytes": owner.source_bytes, "sha256": owner.source_sha256}
                   for index, owner in enumerate(research.FACTORIES))
    _require(not {row["id"] for row in sources}.intersection(row["id"] for row in result["sources"]),
             "an old atlas provenance ID was reused")
    result["sources"].extend(sources)
    node["references"] = list(dict.fromkeys((*node.get("references", ()), "S106", "S107", "S108", "S109")))
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v32_edition"]["role"] = "historical_immutable_release"
    boundaries["alpha_v33_edition"] = {
        "role": "current_immutable_release", "theorem_count": 4092, "checked_use_count": 4092,
        "stable_closed_count": 432, "alpha_closed_count": 3660, "body_checked_count": 0,
        "pending_layered_closure_count": 0, "checked_use_promotion_count": 121, "new_theorem_count": 121,
        "dependency_edge_count": EXPECTED_EDGES, "checked_dependency_edge_count": EXPECTED_EDGES,
        "layer_count": catalog["layer_count"], "enrollment_sha256": catalog["ordered_enrollment_root_sha256"],
        "identity_sha256": catalog["edition_identity_sha256"], "catalog_sha256": catalog_sha256,
        "evidence_root_sha256": catalog["evidence_root_sha256"], "stable_unchanged": True,
        "historical_v32_unchanged": True, "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_polynomial_checkpoint",
    }
    boundaries["alpha_v33_research_admission"] = {
        "parent_v32_theorem_count": 3971, "new_theorem_count": 121, "current_v33_theorem_count": 4092,
        "new_family_count": 1, "proof_bundle_count": 1, "ordinary_principal_count": 8,
        "completed_named_targets": [], "full_G091_prime_power_field_construction": "open",
        "polynomial_gcd_bezout": "open", "all_parent_admissions_replayed_here": False,
        "historical_research_receipts_are_new_proof_authority": False,
        "historical_parent": {"path": PARENT_RELATIVE + "/campaign.json", **PARENT_PINS["campaign.json"]},
        "original_parent_meta": deepcopy(original["meta"]),
    }
    _preserved(original, result)
    return result


def _preserved(original, current):
    for before, after in zip(original["nodes"], current["nodes"], strict=True):
        for key in ("id", "status", "statement", "deps", "family", "layer", "title", "difficulty"):
            _require(before.get(key) == after.get(key), "a milestone contract/status/dependency changed")
        if before["id"] != "G091":
            _require(before == after, "an unrelated historical milestone changed")
        else:
            _require(after["historical_v32_polynomial_progress"]["record"] == before
                     and after["polynomial_prerequisite_progress"] == before["polynomial_prerequisite_progress"]
                     and after["additional_checked_chapters"][:-1] == before["additional_checked_chapters"]
                     and after["status"] == "open" and "evidence" not in after
                     and after["polynomial_euclidean_progress"]["full_G091_proved"] is False,
                     "new prerequisites were confused with full G091 closure or older admissions")
    _require(current["definitions"] == original["definitions"]
             and current["sources"][:len(original["sources"])] == original["sources"],
             "historical vocabulary or source records changed")


def _definition_targets(graph, routes, new_files):
    sources = {}
    for phase, snapshot in publication.OLDER.items():
        root, manifest = publication._snapshot(*snapshot)
        for family in manifest["families"]:
            sources[family["slug"]] = (publication.OUTPUT_NAMES[phase], root, manifest)
    _require(set(sources) | set(SLUGS) == set(routes), "actual definition family inventory changed")
    targets = {}
    for row in graph["reviewed_definitions"]:
        identifier = row["id"]
        override = graph["definition_page_overrides"].get(identifier)
        if override is not None:
            _require(override["name"] == row["name"] and override["registry_route"] == row["route"]
                     and override["proof_authority"] is False, "definition destination claims authority")
        route = row["route"] if override is None else override["route"]
        name = route + "/explorer/defined/definition/" + identifier + ".html"
        if route == SLUGS[0]:
            _require(identifier in NEW_DEFINITION_IDS and name in new_files,
                     "a promoted definition has no genuine new reader page")
            raw = new_files[name]
        else:
            _require(route in sources and routes[route] == sources[route][0], "foreign definition route")
            _, root, manifest = sources[route]
            raw = publication._source(root, manifest, name)
        _require(identifier not in targets, "repeated reviewed definition ID")
        targets[identifier] = {"route": route, "path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    _require(len(targets) == 397, "not all397 definitions have actual pages")
    return targets


def _audit(original, campaign, graph, parent_audit, catalog, catalog_sha256, reports):
    checked = validate_campaign_dags(campaign, definition_graph=graph, catalog=catalog,
                                    catalog_sha256=catalog_sha256)
    _require(checked.theorem_count == 4092 and checked.theorem_edge_count == EXPECTED_EDGES
             and checked.milestone_count == 144
             and checked.milestone_dag_sha256 == parent_audit["milestone_dag_sha256"]
             and checked.reviewed_definition_count == 397 and checked.reviewed_definition_edge_count == 865
             and checked.definition_dag_sha256 == parent_audit["definition_dag_sha256"],
             "separate theorem/milestone/conservative-definition DAG boundaries changed")
    result = asdict(checked)
    result["historical_parent_audit"] = {
        "path": PARENT_RELATIVE + "/dag-audit.json", **PARENT_PINS["dag-audit.json"],
        "stored_audit_is_new_proof_authority": False, "record": deepcopy(parent_audit),
    }
    result["current_research_admission"] = {
        "first_alpha_version": "v33", "new_theorem_count": 121, "family_count": 1,
        "ordinary_principal_count": 8, "full_G009_proved": True, "full_G091_proved": False,
        "polynomial_associativity_proved": False, "polynomial_gcd_bezout_proved": False,
        "stable_changed": False, "all_parent_admissions_replayed_here": False,
        "fresh_bundles": [deepcopy(reports[SLUGS[0]]["bundle"])],
        "notation_edges_are_proof_premises": False,
    }
    return result


_once = previous._once


def _html(source, campaign, graph, routes, revision):
    _require(type(revision) is str and re.fullmatch(r"[0-9a-f]{12}", revision), "invalid current revision")
    route_pattern = r"        var currentFamilies = \{[^\n]*\};"
    source, count = re.subn(route_pattern,
        lambda _match: "        var currentFamilies = " + json.dumps(routes, sort_keys=True) + ";", source)
    _require(count == 1, "the exact inherited family dispatcher changed")
    for before, after in (
        ('../constructive-research-explorer-v32/index.html?v=41b9f387d88a" data-proof-home',
         '../constructive-research-explorer-v33/index.html?v=' + revision + '" data-proof-home'),
        ('"../constructive-research-explorer-v32/index.html"));',
         '"../constructive-research-explorer-v33/index.html"));'),
        ('index.html?v=41b9f387d88a" data-proof-quadratic', 'index.html?v=' + revision + '" data-proof-quadratic'),
        ('index.html?v=41b9f387d88a" data-proof-bertrand', 'index.html?v=' + revision + '" data-proof-bertrand'),
    ):
        source = _once(source, before, after)
    guard = (
        '      function currentPolynomialDivisionProgress(node) {\n'
        '        var progress = node && node.polynomial_euclidean_progress;\n'
        '        return !!node && node.id === "G091" && node.status === "open" && !!progress &&\n'
        '          progress.alpha_version === "v33" && progress.alpha_first_enrolled_version === "v33" &&\n'
        '          progress.alpha_enrolled === true && progress.checked_use === true &&\n'
        '          progress.division_execution_proved === true && progress.stable_member === false &&\n'
        '          progress.full_G091_proved === false && progress.polynomial_associativity_proved === false &&\n'
        '          progress.polynomial_gcd_bezout_proved === false;\n'
        '      }\n\n'
    )
    source = _once(source, '      function statusCaveat(node) {\n',
        guard + '      function statusCaveat(node) {\n'
        '        if (currentPolynomialDivisionProgress(node)) return ' + json.dumps(G091_SUMMARY) + ';\n')
    source = _once(source,
        '            include(descriptor, chapter.slug === "polynomial-division-prerequisites" && chapter.closes_full_milestone === false ?',
        '            include(descriptor, chapter.slug === "polynomial-euclidean-division" && currentPolynomialDivisionProgress(node) ?\n'
        '              "Alpha v33 general division and representation laws — G091 remains open; not Stable" :\n'
        '              chapter.slug === "polynomial-division-prerequisites" && chapter.closes_full_milestone === false ?')
    reviewed_names = {row["id"]: row["name"] for row in graph["reviewed_definitions"]
                      if row["id"] in NEW_DEFINITION_IDS}
    source = _once(source, '        ui.notationSection.hidden = names.length === 0;',
        '        ui.notationSection.hidden = names.length === 0 && !currentPolynomialDivisionProgress(node);')
    source = _once(source, '      }\n\n      function proofHref(path) {',
        '        if (currentPolynomialDivisionProgress(node)) {\n'
        '          var reviewedNames = ' + json.dumps(reviewed_names, sort_keys=True) + ';\n'
        '          node.polynomial_euclidean_progress.conservative_definition_ids.forEach(function (id) {\n'
        '            if (!Object.prototype.hasOwnProperty.call(reviewedNames, id)) throw new Error("Unknown conservative definition");\n'
        '            var item = element("li");\n'
        '            item.appendChild(element("a", "Reviewed conservative definition (notation only): " + reviewedNames[id], {\n'
        '              href: proofHref(explorerBase("polynomial-euclidean-division") + "definition/" + id + ".html")\n'
        '            }));\n'
        '            ui.notation.appendChild(item);\n'
        '          });\n'
        '        }\n'
        '      }\n\n      function proofHref(path) {')
    snapshot = json.dumps(campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    _require("</script" not in snapshot.lower() and len(snapshot.encode()) <= MAX_CAMPAIGN_BYTES,
             "unsafe or oversized inline current atlas")
    raw = _expected(source, snapshot)[1].encode()
    _require(len(raw) <= MAX_CAMPAIGN_BYTES, "current atlas HTML exceeds its original bound")
    return raw


def build_files_from_live(context):
    publication.require_live(context)
    binding = source_binding()
    parents = parent_files()
    original, parent_graph, parent_audit = _parent(parents)
    routes = _package_map(publication._all_family_metadata())
    campaign = _project(original, context.catalog, context.families, context.catalog_sha256,
                        context.source_binding_sha256, routes)
    graph = _graph(parent_graph, campaign, routes)
    from build_constructive_polynomial_euclidean_explorer_v33 import build_files_from_live as new_family_files
    new_files = new_family_files(context)
    targets = _definition_targets(graph, routes, new_files)
    audit = _audit(original, campaign, graph, parent_audit, context.catalog,
                   context.catalog_sha256, context.families)
    files = {"campaign.json": _json(campaign), "definitions.json": _json(graph),
             "dag-audit.json": _json(audit),
             "index.html": _html(parents["index.html"].decode(), campaign, graph, routes, context.revision)}
    _require(parent_files() == parents and _definition_targets(graph, routes, new_files) == targets
             and source_binding() == binding, "atlas inputs or actual definition targets changed during rendering")
    publication.require_live(context)
    return files
