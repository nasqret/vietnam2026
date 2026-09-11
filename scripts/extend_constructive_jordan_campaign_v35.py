"""Append Jordan evidence to the unchanged144-node/120-goal campaign blueprint.

No milestone contract, prerequisite or historical proof record is rewritten.
G008 alone gains closure; G091, G009 and every unrelated node remain identical.
"""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import re

from constructive_jordan_definitions_v35 import build_definition_graph, JORDAN_DEFINITIONS
from build_constructive_jordan_explorer_v35 import (
    ROOT, SLUG, OUTPUT_NAME as READER_PACKAGE, json_bytes, _require, _validate_data,
    family_metadata, research,
)
from sync_constructive_grand_campaign import _expected, validate_campaign_dags
import constructive_completed_lower_publication_v31 as transport

OUTPUT_NAME = "constructive-jordan-campaign-v35"
PARENT_RELATIVE = "book/_static/constructive-research-campaign-v34"
PARENT_PINS = {
    "campaign.json": (834605, "68953b1a4c862d1ee048c8d7eb78c1bb53fdb878c36179346d2ecbe3da715d30"),
    "definitions.json": (1494727, "be0e8fc9d2ecf3d23b8497e615aa2086b99f7dce6398f834459fef77c0afad74"),
    "dag-audit.json": (11907, "c9cd0587b163e1fc8e83dabe9dd9ed17a684e8d81ae2ba4894b070926542e5a5"),
    "index.html": (844591, "6b7bdfaeb577e00a8cafd428065035f67ffb6b6f18010d5c4f859f4fa98742b6"),
}
ROOT_NAME = "jordan_totient_multiplicativity_exists"
SUMMARY = ("G008 is proved by actual finite primitive-tuple enumerations and a canonical tuple CRT. "
    "Alpha v35 adds95 novel admissions from96 source lemmas; one equality alias reuses its historical "
    "admission. The complete359-node bundle has original HA and same-byte compiled Lean checks, with "
    "seven separately checked ordinary roots. Count existence, uniqueness, coprime multiplicativity, "
    "the unit modulus and prime-power primitivity are covered. The stronger general prime-power "
    "count and distinct-prime product formula remain open. No G091 or Stable admission is made.")


def parent_files():
    return {name: transport.read_pinned(ROOT / PARENT_RELATIVE / name, size, digest)
            for name, (size, digest) in PARENT_PINS.items()}


def _preserved(original, result):
    _require(len(original["nodes"]) == len(result["nodes"]) == 144,
             "the144 milestone inventory changed")
    for before, after in zip(original["nodes"], result["nodes"], strict=True):
        if before["id"] != "G008":
            _require(before == after, "an unrelated milestone, including G091, was rewritten")
        else:
            _require(before["status"] == "open" and after["status"] == "alpha_closed",
                     "G008 alone must acquire exact checked closure")
            _require(all(after.get(key) == value for key, value in before.items()
                         if key not in {"status", "why"}), "G008's original statement or prerequisites changed")
            _require(after["historical_v34_record"]["record"] == before,
                     "G008's original open record was not retained")
    _require(original["definitions"] == result["definitions"]
        and original["sources"] == result["sources"][:len(original["sources"])],
        "historical blueprint vocabulary or provenance changed")


def _project(original, context):
    expected, catalog, report, plan, measurements = _validate_data(context)
    _require(original["meta"]["current_alpha_version"] == "v34"
        and original["meta"]["current_alpha_checked_use_count"] == 4223,
        "the exact v34 campaign parent changed")
    metadata = family_metadata()
    routes = deepcopy(original["current_proof_family_packages"])
    _require(len(routes) == 68 and SLUG not in routes, "the68 historical family routes changed")
    routes[SLUG] = READER_PACKAGE
    result = deepcopy(original)
    node = next(row for row in result["nodes"] if row["id"] == "G008")
    before = deepcopy(node)
    proof_routes = [dict(label=name, route=SLUG, tag=metadata["tags"][name])
                    for name in research().research_family(SLUG).principal_roots]
    _require(ROOT_NAME in metadata["tags"], "the literalG008 existence endpoint is missing")
    node["status"] = "alpha_closed"
    node["why"] += "\n\n" + SUMMARY
    node["historical_v34_record"] = dict(path=PARENT_RELATIVE + "/campaign.json",
        sha256=PARENT_PINS["campaign.json"][1], stored_record_is_new_proof_authority=False, record=before)
    node["evidence"] = dict(alpha_enrolled=True, checked_use=True, stable_member=False,
        alpha_version="v35", alpha_first_enrolled_version="v35", release_status="alpha_closed",
        implementation="independently_closed", theorem_name=ROOT_NAME,
        theorem_statement_sha256=catalog[ROOT_NAME]["statement_sha256"],
        proof_tag=metadata["tags"][ROOT_NAME], route=SLUG + "/", proof_routes=proof_routes,
        full_G008_multiplicativity_proved=True, general_prime_power_count_proved=False,
        distinct_prime_product_formula_proved=False, current_G091_proved=False,
        original_ha_bundle_verified=True, independent_lean_bundle_verified=True,
        full_empty_context_closure=True, bundle=deepcopy(report["bundle"]),
        ordinary_principal_roots=deepcopy(report["principal_roots"]),
        source_owned_theorem_count=96, new_theorem_count=95, source_aliases=metadata["aliases"],
        conservative_definition_ids=[d.stable_id for d in JORDAN_DEFINITIONS],
        current_catalog_sha256=context.catalog_sha256,
        current_source_binding_sha256=context.source_binding_sha256)
    node["additional_checked_chapters"] = [dict(slug=SLUG, title=metadata["title"], theorem_count=95,
        source_owned_theorem_count=96, closes_full_milestone=True, authority="alpha_v35_checked_use",
        alpha_checked_use=True, alpha_edition_version="v35", alpha_first_enrolled_version="v35",
        stable_member=False, proof_routes=proof_routes)]
    meta = result["meta"]
    _require("v34" not in meta["historical_alpha_versions"], "the historical v34 release was already appended")
    meta["historical_alpha_versions"].append("v34")
    meta.update(current_alpha_version="v35", current_alpha_checked_use_count=4318,
        current_alpha_catalog_sha256=context.catalog_sha256,
        current_alpha_identity_sha256=context.catalog["edition_identity_sha256"],
        current_research_new_theorem_count=95, current_research_family_count=1,
        current_G008_alpha_admitted=True, current_G091_proved=False,
        reviewed_definition_count=418, alpha_catalog_remaining_entry_slots=8192 - 4318)
    result["current_proof_family_packages"] = routes
    boundary = result["ambitious_boundaries"]
    boundary["alpha_v34_edition"]["role"] = "historical_immutable_release"
    boundary["alpha_v35_edition"] = dict(role="current_immutable_release", theorem_count=4318,
        checked_use_count=4318, stable_closed_count=432, alpha_closed_count=3886,
        body_checked_count=0, pending_layered_closure_count=0, checked_use_promotion_count=95,
        new_theorem_count=95, dependency_edge_count=context.catalog["edge_count"],
        checked_dependency_edge_count=context.catalog["edge_count"], layer_count=context.catalog["layer_count"],
        enrollment_sha256=context.catalog["ordered_enrollment_root_sha256"],
        identity_sha256=context.catalog["edition_identity_sha256"], catalog_sha256=context.catalog_sha256,
        evidence_root_sha256=context.catalog["evidence_root_sha256"], stable_unchanged=True,
        historical_v34_unchanged=True, independent_lean_bundle_verified=True,
        promoted_origin="independently_kernel_and_lean_checked_jordan_totients")
    boundary["alpha_v35_jordan_admission"] = dict(parent_v34_theorem_count=4223,
        new_theorem_count=95, current_v35_theorem_count=4318, source_owned_theorem_count=96,
        inherited_source_alias_count=1, completed_named_targets=["G008"],
        full_G091_prime_power_field_construction="open", distinct_prime_product_formula="open",
        all_parent_admissions_replayed_here=False, historical_records_are_new_proof_authority=False)
    last = max(int(row["id"][1:]) for row in result["sources"])
    result["sources"].append(dict(id=f"S{last+1:03d}", kind="release_manifest",
        label="Alpha v35 Jordan admission:95 novel rows, one inherited alias",
        path="artifacts/peano-library/alpha/catalog-v35.json"))
    _preserved(original, result)
    return result


def _graph(original, campaign):
    graph = build_definition_graph(campaign)
    graph["definition_page_overrides"] = deepcopy(original["definition_page_overrides"])
    old = {row["id"]: row for row in original["reviewed_definitions"]}
    new = {row["id"]: row for row in graph["reviewed_definitions"]}
    _require(len(old) == 407 and len(new) == 418 and all(new[name] == row for name, row in old.items())
        and set(new) - set(old) == {d.stable_id for d in JORDAN_DEFINITIONS},
        "a historical conservative identity changed")
    for key in ("definition_edges", "milestone_usage_edges", "incompatible_reviewed_matches", "authority_policy"):
        _require(graph[key] == original[key], "an independent historical notation boundary changed")
    old_nodes = {row["name"]: row for row in original["definitions"]}
    for row in graph["definitions"]:
        before = old_nodes[row["name"]]
        _require(row == before if row["name"] != "Jordan" else
                 all(row[key] == value for key, value in before.items() if key != "reviewed_match"),
                 "blueprint notation was rewritten instead of linked")
    return graph


def _once(source, old, new):
    _require(source.count(old) == 1, "the canonical atlas extension point changed")
    return source.replace(old, new, 1)


def _html(parent, campaign, graph, revision):
    source = parent.decode()
    routes = campaign["current_proof_family_packages"]
    source, count = re.subn(r"        var currentFamilies = \{[^\n]*\};",
        lambda _: "        var currentFamilies = " + json.dumps(routes, sort_keys=True) + ";", source)
    _require(count == 1, "the original atlas dispatcher changed")
    source = _once(source, "      function statusCaveat(node) {\n",
        "      function statusCaveat(node) {\n"
        '        if (node.id === "G008" && node.status === "alpha_closed" && node.evidence && '
        'node.evidence.alpha_version === "v35" && node.evidence.full_G008_multiplicativity_proved === true) return '
        + json.dumps(SUMMARY) + ";\n")
    names = {d.stable_id: d.name for d in JORDAN_DEFINITIONS}
    source = _once(source, "      }\n\n      function proofHref(path) {",
        '        if (node.id === "G008" && node.evidence && node.evidence.alpha_version === "v35" && node.evidence.checked_use === true) {\n'
        '          var jordanReviewedNames = ' + json.dumps(names, sort_keys=True) + ';\n'
        '          Object.keys(jordanReviewedNames).forEach(function (id) {\n'
        '            var item = element("li");\n'
        '            item.appendChild(element("a", "Reviewed conservative definition (notation only): " + jordanReviewedNames[id], {\n'
        '              href: proofHref(explorerBase("jordan-totient") + "definition/" + id + ".html")\n'
        '            }));\n            ui.notation.appendChild(item);\n          });\n        }\n'
        "      }\n\n      function proofHref(path) {")
    snapshot = json.dumps(campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    _require("</script" not in snapshot.lower(), "unsafe inline atlas source")
    return _expected(source, snapshot)[1].encode()


def build_files_from_live(context, *, reader_files=None):
    publication = import_module("constructive_jordan_publication_v35")
    publication.require_live(context)
    parents = parent_files()
    original = json.loads(parents["campaign.json"])
    campaign = _project(original, context)
    graph = _graph(json.loads(parents["definitions.json"]), campaign)
    campaign["meta"]["reviewed_definition_edge_count"] = graph["reviewed_definition_edge_count"]
    # The graph's snapshot identity includes metadata: rebuild after exact count.
    graph = _graph(json.loads(parents["definitions.json"]), campaign)
    checked = validate_campaign_dags(campaign, definition_graph=graph,
        catalog=context.catalog, catalog_sha256=context.catalog_sha256)
    parent_audit = json.loads(parents["dag-audit.json"])
    _require(checked.theorem_count == 4318 and checked.reviewed_definition_count == 418
        and checked.milestone_dag_sha256 == parent_audit["milestone_dag_sha256"]
        and checked.definition_dag_sha256 == parent_audit["definition_dag_sha256"],
        "the unrelated milestone or blueprint-definition DAG changed")
    if reader_files is None:
        from build_constructive_jordan_explorer_v35 import build_files_from_live as build_reader
        reader_files = build_reader(context)
    for definition in JORDAN_DEFINITIONS:
        _require(SLUG + "/explorer/defined/definition/" + definition.stable_id + ".html" in reader_files,
                 "a reviewed Jordan definition has no actual reader page")
    audit = asdict(checked)
    audit["jordan_admission"] = dict(new_theorem_count=95, source_owned_theorem_count=96,
        source_alias_count=1, full_G008_proved=True, full_G091_proved=False,
        distinct_prime_product_formula_proved=False, notation_edges_are_proof_premises=False,
        all_parent_admissions_replayed_here=False)
    files = {"campaign.json": json_bytes(campaign), "definitions.json": json_bytes(graph),
        "dag-audit.json": json_bytes(audit), "index.html": _html(parents["index.html"], campaign, graph, context.revision)}
    _require(parent_files() == parents and all(len(raw) <= 8 * 1024 * 1024 for raw in files.values()),
             "historical atlas changed during rendering or output exceeds8MiB")
    publication.require_live(context)
    return files
