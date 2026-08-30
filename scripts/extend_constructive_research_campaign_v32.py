"""Current v32 atlas over the exact immutable polynomial research atlas.

This module performs no proof replay, catalogue loading, admission, or writes.
Only the genuine live release capability may enter the public builder. Old
research non-admission records survive literally as history; current admission
comes from that invocation's checked v32 catalogue and twelve ordinary roots.
The original 144-node atlas layout and all 390 reviewed definitions survive.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import re

import constructive_research_publication_v32 as publication
from extend_constructive_second_wave_campaign import _table_source
from peano_lab.library import campaign_research_v32_closure as research
from sync_constructive_grand_campaign import (
    MAX_CAMPAIGN_BYTES, _definition_dags, _digest, _expected,
    _milestone_dag, _projection_digest, validate_campaign_dags,
)


ROOT = Path(__file__).resolve().parents[1]
PARENT_RELATIVE = "book/_static/constructive-polynomial-division-explorer/grand-campaign"
PARENT = ROOT / PARENT_RELATIVE
PARENT_PINS = {
    "campaign.json": {"bytes": 640568, "sha256": "064d5a5d3525cd6222908dea11706693e44f22a8b3684dcc6673b394d36a9ab2"},
    "definitions.json": {"bytes": 1484978, "sha256": "55696e74c18e18a3ff8587763465f000fba72f1f387042bdee1e3691c1fffdea"},
    "dag-audit.json": {"bytes": 2819, "sha256": "c929df4553fb3ff066ec95aafe3b5dc6f6945c535d4d3b4bbac48dcce4bed851"},
    "index.html": {"bytes": 700235, "sha256": "591ae8e4d893203a55993da8feea3619c2e176f337f963508924d069fcd2f069"},
}
SOURCE_PATHS = (
    "scripts/extend_constructive_research_campaign_v32.py",
    "peano-lab/py/tests/test_constructive_research_campaign_v32.py",
    "scripts/constructive_research_publication_v32.py",
    "scripts/constructive_completed_lower_publication_v31.py",
    "scripts/sync_constructive_grand_campaign.py",
    "scripts/extend_constructive_second_wave_campaign.py",
    "scripts/constructive_lower_layer_definition_graph.py",
    "scripts/constructive_definition_graph.py",
    "scripts/check_alpha_v32_research.py",
)
SLUGS = ("multiplicative-convolution", "polynomial-division-prerequisites")
CATALOG_PATH = "artifacts/peano-library/alpha/catalog-v32.json"
RECEIPT_PATH = "research/arithmetic-library/artifacts/alpha-v32-research-receipt-v1.json"
RFC_PATH = "research/arithmetic-library/alpha-v32-research-promotion-rfc-v1.md"
EXPECTED_COUNT, EXPECTED_EDGES = 3971, 12751
REVIEWED_COUNT, REVIEWED_EDGES = 390, 844
G009_ROOT = "dirichlet_convolution_multiplicative_exists_unique"
G091_ROOT = "prime_field_polynomial_synthetic_zero_remainder_iff"
# These two registry names never denoted independently published families.
# Route to an already published page of the SAME reviewed definition identity.
# No abbreviation, expansion, alias or mathematical edge is changed here.
DEFINITION_PAGE_ROUTES = {
    "ND0251": ("ArithTable", "signed-arithmetic", "dirichlet-convolution"),
    "ND0252": ("ArithAt", "signed-arithmetic", "dirichlet-convolution"),
    "ND0253": ("SignedPrefixSum", "signed-arithmetic", "dirichlet-convolution"),
    "ND0254": ("ArithTableEqual", "signed-arithmetic", "dirichlet-convolution"),
    "ND0261": ("ArithReindex", "signed-arithmetic", "dirichlet-convolution"),
    "ND0262": ("BetaPrefixInto", "finite-prefix-data", "prime-field-polynomials"),
    "ND0263": ("BetaPrefixEqual", "finite-prefix-data", "prime-field-polynomials"),
}
G009_SUMMARY = (
    "Full G009 is proved for actual finite signed arithmetic-function tables. "
    "Construction, associativity, delta identity and the exact signed-unit "
    "inverse criterion are completed by normalized coprime multiplicative "
    "closure on every nonempty positive prefix, with m*n<=N. All tables, "
    "divisor pairs, Cartesian products and support maps are constructed. "
    "Zero-index values and physical encodings remain unrestricted. The 90 "
    "research theorems are now first admitted to Alpha v32, not to Stable. "
    "No inverse-multiplicativity or second-order function theorem is claimed."
)
G091_SUMMARY = (
    "The 85 polynomial prerequisites are first admitted to Alpha v32: canonical "
    "coefficient negation/subtraction, leading-zero trimming, genuine monic "
    "normalization and synthetic division by X-a. Their six ordinary "
    "empty-context HA certificates and same-byte compiled-Lean bundle have "
    "been checked afresh. General polynomial Euclidean division, gcd/Bezout, "
    "irreducible-polynomial existence and prime-power quotient fields are "
    "not proved by this tranche. G091 remains open; Stable is unchanged."
)
_ERROR = publication.PublicationError


def _require(condition, message):
    if not condition:
        raise _ERROR(message)


def _json(value):
    raw = publication.json_bytes(value)
    _require(len(raw) <= MAX_CAMPAIGN_BYTES, "atlas document exceeds the unchanged 8 MiB bound")
    return raw


def parent_files():
    """Read four literal history documents; hashes are never new proof authority."""
    _require(set(PARENT_PINS) == {"campaign.json", "definitions.json", "dag-audit.json", "index.html"},
             "the exact polynomial atlas parent inventory changed")
    result = {}
    for name, pin in PARENT_PINS.items():
        _require(type(pin) is dict and set(pin) == {"bytes", "sha256"}
                 and type(pin["bytes"]) is int and 0 < pin["bytes"] <= MAX_CAMPAIGN_BYTES
                 and type(pin["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]),
                 "an exact polynomial atlas pin is malformed")
        result[name] = publication.read_pinned(PARENT / name, pin["bytes"], pin["sha256"])
    return result


def source_binding():
    """Small fresh presentation fingerprint, with no theorem/catalogue import."""
    from check_alpha_v32_research import _file_digest
    records = [(PARENT_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest())
               for name, raw in parent_files().items()]
    for path in SOURCE_PATHS:
        size, digest = _file_digest(path, 2 * 1024 * 1024)
        records.append((path, size, digest))
    return sha256(publication.json_bytes(records)).hexdigest()


def _parent(parents):
    campaign = publication.strict_json(parents["campaign.json"])
    graph = publication.strict_json(parents["definitions.json"])
    audit = publication.strict_json(parents["dag-audit.json"])
    meta = campaign.get("meta", {})
    nodes = campaign.get("nodes", ())
    _require(campaign.get("schema") == "constructive-grand-campaign-v1"
             and meta.get("current_alpha_version") == "v31"
             and meta.get("current_alpha_checked_use_count") == 3796
             and meta.get("goal_count") == 120 and len(nodes) == 144
             and len({node.get("id") for node in nodes}) == 144,
             "the immutable parent atlas has a different milestone inventory")
    by_id = {node["id"]: node for node in nodes}
    _require(by_id["G009"].get("status") == "available"
             and by_id["G009"].get("research_proof_closed") is True
             and by_id["G009"].get("evidence", {}).get("full_G009_finite_coded_contract_proved") is True
             and by_id["G009"]["evidence"].get("alpha_enrolled") is False
             and by_id["G091"].get("status") == "open"
             and by_id["G091"].get("polynomial_prerequisite_progress", {}).get("full_G091_proved") is False
             and by_id["G091"]["polynomial_prerequisite_progress"].get("alpha_enrolled") is False,
             "the exact historical G009/G091 proof boundary changed")
    milestones, milestone_edges = _milestone_dag(campaign)
    definitions, reviewed, edges, reviewed_edges, uses, statements, declared = _definition_dags(campaign, graph)
    expected = {
        "alpha_version": "v31", "theorem_count": 3796, "theorem_edge_count": 12248,
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
             and len(reviewed) == REVIEWED_COUNT and reviewed_edges == REVIEWED_EDGES
             and len(definitions) == 474 and edges == 855,
             "the immutable parent definition/milestone audit is inconsistent")
    return campaign, graph, audit


def _package_map(metadata):
    _require(type(metadata) is tuple and len(metadata) == 65, "the exact 65-family route inventory changed")
    result = {}
    allowed = {publication.OUTPUT_NAMES[name] for name in ("research", "completed", "historical")}
    for item in metadata:
        _require(type(item) is dict and type(item.get("slug")) is str
                 and re.fullmatch(r"[a-z][a-z0-9-]*", item["slug"])
                 and item["slug"] not in result and item.get("package") in allowed,
                 "a current family route is duplicate, unsafe or foreign")
        result[item["slug"]] = item["package"]
    _require({name for name, package in result.items()
              if package == publication.OUTPUT_NAMES["research"]} == set(SLUGS),
             "the new Alpha research families were routed to a foreign package")
    _require(sum(value == publication.OUTPUT_NAMES["completed"] for value in result.values()) == 19
             and sum(value == publication.OUTPUT_NAMES["historical"] for value in result.values()) == 44,
             "the preserved 19/44 family partition changed")
    return result


def _graph(parent_graph, campaign, routes):
    """Preserve every definition/edge; repair seven presentation destinations."""
    result = deepcopy(parent_graph)
    definitions = {row["id"]: row for row in result["reviewed_definitions"]}
    overrides = result.setdefault("definition_page_overrides", {})
    for identifier, (name, registry, route) in DEFINITION_PAGE_ROUTES.items():
        _require(identifier in definitions and definitions[identifier]["name"] == name
                 and definitions[identifier]["route"] == registry
                 and identifier not in overrides and route in routes,
                 "a presentation-only definition destination shadows an existing identity")
        overrides[identifier] = {"name": name, "proof_authority": False,
                                 "registry_route": registry, "route": route}
    result["campaign_snapshot_sha256"] = _digest(campaign)
    return result


def _definition_targets(graph, routes):
    """Authenticate all 390 destinations against literal original reader bytes."""
    sources = {}
    for phase, (directory, size, expected) in publication.OLDER.items():
        root, manifest = publication._snapshot(directory, size, expected)
        for family in manifest["families"]:
            sources[family["slug"]] = (publication.OUTPUT_NAMES[phase], root, manifest)
    for slug, directory, size, expected in publication.RESEARCH:
        root, manifest = publication._snapshot(directory, size, expected)
        sources[slug] = (publication.OUTPUT_NAMES["research"], root, manifest)
    _require(set(sources) == set(routes), "the actual definition family inventory changed")
    result = {}
    for row in graph["reviewed_definitions"]:
        identifier = row["id"]
        override = graph.get("definition_page_overrides", {}).get(identifier)
        if override is not None:
            _require(type(override) is dict and override.get("name") == row["name"]
                     and override.get("registry_route") == row["route"]
                     and override.get("proof_authority") is False,
                     "a definition destination claims a different identity or proof authority")
        route = row["route"] if override is None else override["route"]
        _require(route in sources and routes.get(route) == sources[route][0]
                 and identifier not in result and re.fullmatch(r"(?:CF|PD|ND)[0-9]{4}", identifier),
                 "a reviewed definition has an unsafe, duplicate or nonexistent destination")
        _, root, manifest = sources[route]
        name = route + "/explorer/defined/definition/" + identifier + ".html"
        raw = publication._source(root, manifest, name)
        result[identifier] = {"route": route, "path": name, "bytes": len(raw),
                              "sha256": sha256(raw).hexdigest()}
    _require(len(result) == REVIEWED_COUNT, "not all reviewed definitions have actual pages")
    return result


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
        closure, admission = row.get("empty_context_closure", {}), row.get("alpha_v32_frontier_enrollment", {})
        _require(closure.get("status") == "checked" and closure.get("kernel_mode") == "intuitionistic"
                 and closure.get("certificate_sha256") == family.artifact_sha256
                 and closure.get("bundle_node_id") == report["owned_node_ids"][name]
                 and admission.get("first_enrolled_version") == "v32"
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
    """Pure presentation transformation; it cannot mint a live proof capability."""
    research.validate_research_metadata()
    _require(type(catalog) is dict and catalog.get("schema") == "peano-library-alpha-snapshot-v32"
             and catalog.get("theorem_count") == EXPECTED_COUNT
             and catalog.get("checked_use_count") == EXPECTED_COUNT
             and catalog.get("stable_count") == 432 and catalog.get("edge_count") == EXPECTED_EDGES
             and type(catalog_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", catalog_sha256)
             and type(source_binding_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", source_binding_sha256),
             "the current atlas needs exact v32 catalogue metadata")
    rows = catalog.get("theorems")
    _require(type(rows) is list and len(rows) == EXPECTED_COUNT
             and len({row.get("name") for row in rows}) == EXPECTED_COUNT
             and tuple(row.get("name") for row in rows[3796:]) == research.FRONTIER_NEW_NAMES
             and type(reports) is dict and tuple(reports) == SLUGS,
             "the current atlas needs the exact additive 3796+175 partition")
    by_name = {row["name"]: row for row in rows}
    for family in research.FAMILIES:
        _admitted_family(family, reports[family.slug], by_name)
    result = deepcopy(original)
    old_nodes = {node["id"]: node for node in original["nodes"]}
    nodes = {node["id"]: node for node in result["nodes"]}
    for identifier in ("G009", "G091"):
        nodes[identifier]["historical_research_checkpoint"] = {
            "source": PARENT_RELATIVE + "/campaign.json",
            **PARENT_PINS["campaign.json"], "stored_record_is_new_proof_authority": False,
            "record": deepcopy(old_nodes[identifier]),
        }
    g009 = nodes["G009"]
    principal = next(row for row in reports[SLUGS[0]]["principal_roots"] if row["name"] == G009_ROOT)
    g009["evidence"].update(
        implementation="independently_closed", alpha_version="v32", alpha_first_enrolled_version="v32",
        release_status="alpha_closed", alpha_enrolled=True, checked_use=True, stable_member=False,
        theorem_name=G009_ROOT, theorem_statement_sha256=by_name[G009_ROOT]["statement_sha256"],
        theorem_names=list(research.FAMILIES[0].principal_roots),
        ordinary_principal_roots=deepcopy(reports[SLUGS[0]]["principal_roots"]),
        current_release_receipt=RECEIPT_PATH, current_catalog_sha256=catalog_sha256,
        current_source_binding_sha256=source_binding_sha256,
        ordinary_certificate_nodes=principal["ordinary_certificate_nodes"],
    )
    g009["why"] = g009["representation_refinement"] = G009_SUMMARY
    g091 = nodes["G091"]
    progress = g091["polynomial_prerequisite_progress"]
    progress.update(
        alpha_version="v32", alpha_first_enrolled_version="v32", alpha_enrolled=True,
        checked_use=True, stable_member=False, full_G091_proved=False,
        scope="alpha_v32_polynomial_prerequisites_only", summary=G091_SUMMARY,
        principal_roots=deepcopy(reports[SLUGS[1]]["principal_roots"]),
        current_release_receipt=RECEIPT_PATH, current_catalog_sha256=catalog_sha256,
        current_source_binding_sha256=source_binding_sha256,
    )
    g091["why"] = old_nodes["G091"]["why"].split("\n\n", 1)[0] + "\n\n" + G091_SUMMARY
    for identifier, slug in (("G009", SLUGS[0]), ("G091", SLUGS[1])):
        chapters = [row for row in nodes[identifier]["additional_checked_chapters"] if row["slug"] == slug]
        _require(len(chapters) == 1, "a current research chapter is missing or repeated")
        chapters[0].update(authority="alpha_v32_checked_use", alpha_checked_use=True,
                           alpha_edition_version="v32", alpha_first_enrolled_version="v32",
                           stable_member=False)
        if identifier == "G091":
            _require(chapters[0]["closes_full_milestone"] is False, "prerequisites cannot close G091")
    meta = result["meta"]
    _require("v31" not in meta["historical_alpha_versions"], "v31 was already a historical atlas parent")
    meta["historical_alpha_versions"].append("v31")
    meta.update(current_alpha_version="v32", current_alpha_checked_use_count=EXPECTED_COUNT,
                current_alpha_catalog_sha256=catalog_sha256,
                current_alpha_identity_sha256=catalog["edition_identity_sha256"],
                current_research_new_theorem_count=175, current_research_family_count=2,
                current_G009_alpha_admitted=True, current_G091_proved=False)
    # The old g009_research_alpha_admission=False and polynomial counterpart
    # explicitly describe historical checkpoint generation, not this release.
    meta["historical_research_admission_flags_are_current_authority"] = False
    result["current_proof_family_packages"] = dict(routes)
    sources = [
        {"id": "S89", "kind": "release_manifest", "label": "Current Alpha v32 checked research admission",
         "path": CATALOG_PATH},
        {"id": "S90", "kind": "independent_closure_record", "label": "Fresh two-bundle HA/Lean and twelve ordinary-principal release audit",
         "path": RECEIPT_PATH},
        {"id": "S91", "kind": "admission_record", "label": "Exact additive Alpha v32 and still-open G091 contract",
         "path": RFC_PATH},
        {"id": "S92", "kind": "historical_presentation_parent", "label": "Unchanged final polynomial research atlas before Alpha admission",
         "path": PARENT_RELATIVE + "/campaign.json"},
    ]
    sources.extend({"id": f"S{93 + index}", "kind": "checked_source_module",
                    "label": f"Alpha v32 exact {owner.count}-theorem source: {owner.module}",
                    "path": owner.source, "bytes": owner.source_bytes, "sha256": owner.source_sha256}
                   for index, owner in enumerate(research.FACTORIES))
    _require(not {row["id"] for row in sources}.intersection(row["id"] for row in result["sources"]),
             "a historical atlas provenance identifier was reused")
    result["sources"].extend(sources)
    for identifier in ("G009", "G091"):
        nodes[identifier]["references"] = list(dict.fromkeys(
            (*nodes[identifier].get("references", ()), "S89", "S90", "S91", "S92")))
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v31_edition"]["role"] = "historical_immutable_release"
    boundaries["alpha_v32_edition"] = {
        "role": "current_immutable_release", "theorem_count": EXPECTED_COUNT,
        "checked_use_count": EXPECTED_COUNT, "stable_closed_count": 432, "alpha_closed_count": 3539,
        "body_checked_count": 0, "pending_layered_closure_count": 0,
        "checked_use_promotion_count": 175, "new_theorem_count": 175,
        "dependency_edge_count": EXPECTED_EDGES, "checked_dependency_edge_count": EXPECTED_EDGES,
        "layer_count": catalog["layer_count"], "enrollment_sha256": catalog["ordered_enrollment_root_sha256"],
        "identity_sha256": catalog["edition_identity_sha256"], "catalog_sha256": catalog_sha256,
        "evidence_root_sha256": catalog["evidence_root_sha256"], "stable_unchanged": True,
        "historical_v31_unchanged": True, "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_research",
    }
    boundaries["alpha_v32_research_admission"] = {
        "parent_v31_theorem_count": 3796, "new_theorem_count": 175, "current_v32_theorem_count": EXPECTED_COUNT,
        "new_family_count": 2, "proof_bundle_count": 2, "ordinary_principal_count": 12,
        "completed_named_targets": ["G009"], "full_G091_prime_power_field_construction": "open",
        "all_parent_admissions_replayed_here": False, "historical_research_receipts_are_new_proof_authority": False,
        "historical_parent": {"path": PARENT_RELATIVE + "/campaign.json", **PARENT_PINS["campaign.json"]},
        "original_parent_meta": deepcopy(original["meta"]),
        "original_parent_alpha_v31_edition": deepcopy(original["ambitious_boundaries"]["alpha_v31_edition"]),
    }
    _preserved(original, result)
    return result


def _preserved(original, current):
    _require(tuple((row["id"], row["status"], row["statement"], row["deps"]) for row in current["nodes"])
             == tuple((row["id"], row["status"], row["statement"], row["deps"]) for row in original["nodes"]),
             "admission changed a milestone identity, contract, status or dependency")
    _require(current["definitions"] == original["definitions"]
             and current["sources"][:len(original["sources"])] == original["sources"],
             "admission changed an inherited definition or source record")
    for before, after in zip(original["nodes"], current["nodes"], strict=True):
        if before["id"] in {"G009", "G091"}:
            _require(after["historical_research_checkpoint"]["record"] == before,
                     "a historical non-admitting research record was rewritten")
        else:
            _require(after == before, "an unrelated historical milestone was changed")
    by_id = {row["id"]: row for row in current["nodes"]}
    _require(by_id["G009"]["status"] == "available" and by_id["G009"]["evidence"]["checked_use"] is True
             and by_id["G091"]["status"] == "open"
             and by_id["G091"]["polynomial_prerequisite_progress"]["full_G091_proved"] is False
             and "evidence" not in by_id["G091"], "G009/G091 admission and proof boundaries were conflated")


def _audit(original, campaign, graph, parent_audit, catalog, catalog_sha256, reports):
    checked = validate_campaign_dags(campaign, definition_graph=graph, catalog=catalog,
                                    catalog_sha256=catalog_sha256)
    value = asdict(checked)
    _require(checked.theorem_count == EXPECTED_COUNT and checked.theorem_edge_count == EXPECTED_EDGES
             and checked.milestone_count == 144
             and checked.milestone_dag_sha256 == parent_audit["milestone_dag_sha256"]
             and checked.reviewed_definition_count == REVIEWED_COUNT
             and checked.reviewed_definition_edge_count == REVIEWED_EDGES
             and checked.reviewed_definition_dag_sha256 == parent_audit["reviewed_definition_dag_sha256"]
             and checked.definition_dag_sha256 == parent_audit["definition_dag_sha256"],
             "the separate current theorem, milestone or conservative-definition DAG changed")
    value["historical_parent_audit"] = {
        "path": PARENT_RELATIVE + "/dag-audit.json", **PARENT_PINS["dag-audit.json"],
        "stored_audit_is_new_proof_authority": False, "record": deepcopy(parent_audit),
    }
    value["current_research_admission"] = {
        "first_alpha_version": "v32", "new_theorem_count": 175, "family_count": 2,
        "ordinary_principal_count": 12, "full_G009_proved": True, "full_G091_proved": False,
        "stable_changed": False, "all_parent_admissions_replayed_here": False,
        "fresh_bundles": [deepcopy(reports[slug]["bundle"]) for slug in SLUGS],
        "notation_edges_are_proof_premises": False,
    }
    return value


def _once(source, before, after):
    _require(source.count(before) == 1, "the literal parent atlas display function changed")
    return source.replace(before, after, 1)


def _html(source, campaign, graph, routes, revision):
    _require(type(revision) is str and re.fullmatch(r"[0-9a-f]{12}", revision),
             "the current atlas requires a literal navigation revision")
    for name, key, compatible in (("COMPILED_DEFINITIONS", "compatible_reviewed_matches", True),
                                  ("INCOMPATIBLE_DEFINITIONS", "incompatible_reviewed_matches", False)):
        rows = [{**row, "route": graph.get("definition_page_overrides", {}).get(
            row["reviewed_id"], {}).get("route", row["route"])} for row in graph[key]]
        source, count = re.subn(r"      var " + name + r" = \{.*?\n      \};",
            lambda _match: _table_source(name, rows, compatible=compatible), source, flags=re.S)
        _require(count == 1, "the inherited atlas definition table changed")
    replacement = (
        '      function explorerBase(route) {\n'
        '        var deployed = /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "");\n'
        '        var currentFamilies = ' + json.dumps(routes, sort_keys=True) + ';\n'
        '        if (!Object.prototype.hasOwnProperty.call(currentFamilies, route)) throw new Error("Unknown current proof family");\n'
        '        if (deployed) return "../" + route + "/explorer/defined/";\n'
        '        return "../" + currentFamilies[route] + "/" + route + "/explorer/defined/";\n'
        '      }\n\n'
    )
    source, count = re.subn(r"      function explorerBase\(route\) \{.*?\n      \}\n\n",
                            lambda _match: replacement, source, flags=re.S)
    _require(count == 1, "the parent atlas has no unique family dispatcher")
    admission = (
        '      function currentResearchAdmitted(node) {\n'
        '        var evidence = node && node.evidence;\n'
        '        return !!node && node.id === "G009" && node.status === "available" && node.research_proof_closed === true &&\n'
        '          !!evidence && evidence.alpha_version === "v32" && evidence.alpha_first_enrolled_version === "v32" &&\n'
        '          evidence.checked_use === true && evidence.alpha_enrolled === true && evidence.stable_member === false &&\n'
        '          evidence.full_empty_context_closure === true && evidence.independent_lean_bundle_verified === true &&\n'
        '          evidence.full_G009_finite_coded_contract_proved === true;\n'
        '      }\n\n'
    )
    source = _once(source, '      function proved(node) {\n',
                   admission + '      function proved(node) {\n        if (currentResearchAdmitted(node)) return true;\n')
    source = _once(source, '      function describeStatus(node) {\n',
                   '      function describeStatus(node) {\n'
                   '        if (currentResearchAdmitted(node)) return "Independently proved G009; first admitted to Alpha v32, not Stable";\n')
    source = _once(source, '      function statusCaveat(node) {\n',
                   '      function statusCaveat(node) {\n'
                   '        if (currentResearchAdmitted(node)) return ' + json.dumps(G009_SUMMARY) + ';\n'
                   '        if (node.id === "G091" && node.status === "open" && node.polynomial_prerequisite_progress &&\n'
                   '            node.polynomial_prerequisite_progress.alpha_version === "v32" &&\n'
                   '            node.polynomial_prerequisite_progress.alpha_first_enrolled_version === "v32" &&\n'
                   '            node.polynomial_prerequisite_progress.alpha_enrolled === true &&\n'
                   '            node.polynomial_prerequisite_progress.checked_use === true &&\n'
                   '            node.polynomial_prerequisite_progress.full_G091_proved === false &&\n'
                   '            node.polynomial_prerequisite_progress.stable_member === false) return ' + json.dumps(G091_SUMMARY) + ';\n')
    source = _once(source,
                   '              "Verified polynomial prerequisite — G091 remains open; not Alpha/Stable" :\n',
                   '              (chapter.alpha_checked_use === true && chapter.alpha_edition_version === "v32" ?\n'
                   '                "Alpha v32 polynomial prerequisite — G091 remains open; not Stable" :\n'
                   '                "Verified historical polynomial prerequisite — not an admission record") :\n')
    source = _once(source,
                   '        document.querySelector("[data-proof-home]").setAttribute("href", proofHref("../index.html"));',
                   '        document.querySelector("[data-proof-home]").setAttribute("href", proofHref(\n'
                   '          /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "") ? "../index.html" :\n'
                   '          "../constructive-research-explorer-v32/index.html"));')
    source = _once(source, '<a href="../index.html?v=6c9ebfb3c37e" data-proof-home>',
                   '<a href="../constructive-research-explorer-v32/index.html?v=' + revision + '" data-proof-home>')
    # Only static navigation is changed; JSON history retains its literal old hashes.
    source = _once(source, 'index.html?v=6c9ebfb3c37e" data-proof-quadratic>',
                   'index.html?v=' + revision + '" data-proof-quadratic>')
    source = _once(source, 'index.html?v=6c9ebfb3c37e" data-proof-bertrand>',
                   'index.html?v=' + revision + '" data-proof-bertrand>')
    snapshot = json.dumps(campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    _require("</script" not in snapshot.lower() and len(snapshot.encode()) <= MAX_CAMPAIGN_BYTES,
             "the embedded current atlas is unsafe or oversized")
    result = _expected(source, snapshot)[1].encode()
    _require(len(result) <= MAX_CAMPAIGN_BYTES, "the current atlas HTML exceeds its original bound")
    return result


def build_files_from_live(context):
    """Four in-memory files only, after the actual source-bound v32 proof gates."""
    publication.require_live(context)
    binding = source_binding()
    parents = parent_files()
    original, parent_graph, parent_audit = _parent(parents)
    routes = _package_map(publication._all_family_metadata())
    campaign = _project(original, context.catalog, context.families, context.catalog_sha256,
                        context.source_binding_sha256, routes)
    # No new abbreviation or notation edge is introduced by Alpha admission.
    graph = _graph(parent_graph, campaign, routes)
    targets = _definition_targets(graph, routes)
    audit = _audit(original, campaign, graph, parent_audit, context.catalog,
                   context.catalog_sha256, context.families)
    files = {"campaign.json": _json(campaign), "definitions.json": _json(graph),
             "dag-audit.json": _json(audit),
             "index.html": _html(parents["index.html"].decode(), campaign, graph, routes, context.revision)}
    _require(parent_files() == parents and _definition_targets(graph, routes) == targets
             and source_binding() == binding,
             "an immutable atlas or formatter changed during rendering")
    publication.require_live(context)
    return files


__all__ = ("PARENT_PINS", "SOURCE_PATHS", "source_binding", "parent_files", "build_files_from_live")
