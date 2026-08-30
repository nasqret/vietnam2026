"""Independent v32 atlas regression tests, not a proof-admission fixture.

The private formatter fixture deliberately contains non-authorizing display
records and never enters the public builder or any successful verifier. Its
old reader/definition documents are authentic byte-pinned historical inputs,
not fresh proof evidence. The same-live assertion wrapper at the bottom accepts
only the actual publication capability. Its private content assertions can also
inspect explicitly non-authorizing observations, without authorizing output.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import inspect
import json
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

import extend_constructive_research_campaign_v32 as atlas
from sync_constructive_grand_campaign import CampaignDagError, _definition_dags, _milestone_dag

NOTICE = "PRIVATE FORMATTER FIXTURE ONLY: NOT A PROOF, CATALOGUE OR RELEASE CAPABILITY"
PARENT_PINS = {
    "campaign.json": (640568, "064d5a5d3525cd6222908dea11706693e44f22a8b3684dcc6673b394d36a9ab2"),
    "definitions.json": (1484978, "55696e74c18e18a3ff8587763465f000fba72f1f387042bdee1e3691c1fffdea"),
    "dag-audit.json": (2819, "c929df4553fb3ff066ec95aafe3b5dc6f6945c535d4d3b4bbac48dcce4bed851"),
    "index.html": (700235, "591ae8e4d893203a55993da8feea3619c2e176f337f963508924d069fcd2f069"),
}
PAGE_OVERRIDES = {
    "ND0251": ("ArithTable", "signed-arithmetic", "dirichlet-convolution"),
    "ND0252": ("ArithAt", "signed-arithmetic", "dirichlet-convolution"),
    "ND0253": ("SignedPrefixSum", "signed-arithmetic", "dirichlet-convolution"),
    "ND0254": ("ArithTableEqual", "signed-arithmetic", "dirichlet-convolution"),
    "ND0261": ("ArithReindex", "signed-arithmetic", "dirichlet-convolution"),
    "ND0262": ("BetaPrefixInto", "finite-prefix-data", "prime-field-polynomials"),
    "ND0263": ("BetaPrefixEqual", "finite-prefix-data", "prime-field-polynomials"),
}
G009_COMPONENTS = {
    "dirichlet_convolution_table_exists_extensionally_unique": "dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13",
    "dirichlet_convolution_associative": "7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738",
    "dirichlet_delta_unit_exists": "6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710",
    "dirichlet_inverse_positive_criterion": "b2130664b7580d7fbeaeb33ebed7c27718cd89676a2b893198751a39ce38d54d",
}
SLUGS = ("multiplicative-convolution", "polynomial-division-prerequisites")


def _goal(campaign, identifier):
    return next(row for row in campaign["nodes"] if row["id"] == identifier)


def _function(source, name):
    match = re.search(r"      function " + re.escape(name) + r"\([^\n]*\) \{.*?\n      \}", source, re.S)
    assert match, name
    return match[0]


def _table(source, name):
    match = re.search(r"      var " + name + r" = \{.*?\n      \};", source, re.S)
    assert match, name
    return match[0]


def _node(source):
    result = subprocess.run(["node"], input=source, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr[-12000:]
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def formatting():
    parents = atlas.parent_files()
    original, parent_graph, parent_audit = atlas._parent(parents)
    metadata = atlas.publication._all_family_metadata()
    routes = atlas._package_map(metadata)
    reports = {}
    rows = [{"name": "private_formatter_parent_" + str(index), "fixture_notice": NOTICE}
            for index in range(3796)]
    for family, source in zip(atlas.research.FAMILIES, atlas.publication.RESEARCH, strict=True):
        slug, directory, size, digest = source
        root, manifest = atlas.publication._snapshot(directory, size, digest)
        corpus = atlas.publication.strict_json(atlas.publication._source(root, manifest, slug + "/api/corpus.json"))
        by_name = {node["name"]: node for node in corpus["nodes"]}
        owned = {name: by_name[name]["proof_bundle_node_id"] for name in family.owned_names}
        principal_rows = []
        for name in family.principal_roots:
            principal_rows.append({
                "name": name, "node_id": owned[name],
                "statement_sha256": family.principal_statement_sha256[name],
                "complete_ordinary_ha_checked": True,
                "ordinary_certificate_nodes": 2, "fixture_notice": NOTICE,
            })
        reports[slug] = {
            "slug": slug, "new_theorem_count": family.count, "specs_sha256": family.specs_sha256,
            "owned_node_ids": owned, "rows": [{"name": name, "fixture_notice": NOTICE} for name in family.owned_names],
            "bundle": {
                "path": family.artifact, "bytes": family.artifact_bytes, "sha256": family.artifact_sha256,
                "nodes_including_packaging_root": family.node_count,
                "dependency_edges_including_packaging": family.bundle_edges,
                "body_proof_nodes": family.body_nodes, "kernel_calls": family.node_count,
                "original_ha_checked": True, "independent_lean_checked": True, "fixture_notice": NOTICE,
            },
            "principal_roots": principal_rows, "fixture_notice": NOTICE,
        }
        for name in family.owned_names:
            rows.append({
                "name": name, "statement_sha256": by_name[name]["statement_sha256"],
                "checked_use": True, "body_checked": True, "membership": "alpha_only", "evidence_status": "alpha_closed",
                "empty_context_closure": {"status": "checked", "kernel_mode": "intuitionistic",
                    "certificate_sha256": family.artifact_sha256, "bundle_node_id": owned[name]},
                "alpha_v32_frontier_enrollment": {"first_enrolled_version": "v32", "campaign": slug,
                    "bundle_sha256": family.artifact_sha256, "bundle_node_id": owned[name]},
                "fixture_notice": NOTICE,
            })
    catalog = {
        "schema": "peano-library-alpha-snapshot-v32", "theorems": rows, "theorem_count": 3971,
        "checked_use_count": 3971, "stable_count": 432, "edge_count": 12751, "layer_count": 53,
        "edition_identity_sha256": "d" * 64, "ordered_enrollment_root_sha256": "e" * 64,
        "evidence_root_sha256": "f" * 64, "fixture_notice": NOTICE,
    }
    before = deepcopy(original)
    projected = atlas._project(original, catalog, reports, "a" * 64, "b" * 64, routes)
    graph = atlas._graph(parent_graph, projected, routes)
    html = atlas._html(parents["index.html"].decode(), projected, graph, routes, "a" * 12)
    assert original == before and atlas.parent_files() == parents
    return SimpleNamespace(parents=parents, original=original, parent_graph=parent_graph,
        parent_audit=parent_audit, catalog=catalog, reports=reports, routes=routes, metadata=metadata,
        projected=projected, graph=graph, html=html, fixture_notice=NOTICE)


@pytest.mark.parametrize("name", tuple(PARENT_PINS))
def test_exact_four_original_atlas_documents_are_independently_pinned(name):
    raw = atlas.parent_files()[name]
    assert (len(raw), sha256(raw).hexdigest()) == PARENT_PINS[name]
    assert atlas.PARENT_PINS[name] == dict(zip(("bytes", "sha256"), PARENT_PINS[name]))


def test_all_144_contracts_and_120_statuses_and_142_unrelated_nodes_are_literal(formatting):
    old, new = formatting.original, formatting.projected
    assert len(old["nodes"]) == len(new["nodes"]) == 144
    assert sum(row["id"].startswith("G") for row in new["nodes"]) == 120
    for before, after in zip(old["nodes"], new["nodes"], strict=True):
        for field in ("id", "status", "statement", "deps", "family", "layer", "title", "difficulty"):
            assert after.get(field) == before.get(field)
        if before["id"] not in ("G009", "G091"):
            assert after == before
        else:
            history = after["historical_research_checkpoint"]
            assert history["record"] == before
            assert history["stored_record_is_new_proof_authority"] is False
            assert (history["bytes"], history["sha256"]) == PARENT_PINS["campaign.json"]
    assert new["definitions"] == old["definitions"]
    assert new["sources"][:len(old["sources"])] == old["sources"]


def test_g009_current_admission_keeps_exact_finite_scope_and_old_four_components(formatting):
    node = _goal(formatting.projected, "G009")
    old = _goal(formatting.original, "G009")
    evidence = node["evidence"]
    assert node["status"] == "available" and node["research_proof_closed"] is True
    assert evidence["alpha_version"] == evidence["alpha_first_enrolled_version"] == "v32"
    assert evidence["checked_use"] is evidence["alpha_enrolled"] is True
    assert evidence["stable_member"] is False
    assert evidence["theorem_name"] == "dirichlet_convolution_multiplicative_exists_unique"
    assert evidence["theorem_statement_sha256"] == "957aa567b3f1547a98478a195178e8d5a7e88cf6a01af0b67f94413191d56970"
    assert evidence["proof_tag"] == "MX0059" and evidence["bundle_node_id"] == 459
    assert evidence["proof_routes"] == old["evidence"]["proof_routes"]
    assert evidence["inherited_contract_components"] == old["evidence"]["inherited_contract_components"]
    assert {row["name"]: row["statement_sha256"] for row in evidence["inherited_contract_components"]} == G009_COMPONENTS
    assert evidence["inverse_multiplicativity_claimed"] is False
    assert evidence["normalization_at_one_for_multiplicativity"] == "+1 only"
    assert evidence["inverse_criterion_includes_both_signed_units"] is True
    assert evidence["unrestricted_zero_values"] is evidence["positive_represented_value_uniqueness"] is True
    assert "No inverse-multiplicativity or second-order" in node["why"]


def test_g091_admits_only_the_85_prerequisites_and_never_the_open_goal(formatting):
    node = _goal(formatting.projected, "G091")
    old = _goal(formatting.original, "G091")
    progress = node["polynomial_prerequisite_progress"]
    assert node["status"] == "open" and "evidence" not in node
    assert progress["new_theorem_count"] == 85 and progress["complete_cone_theorem_count"] == 292
    assert progress["full_G091_proved"] is False and progress["stable_member"] is False
    assert progress["alpha_version"] == progress["alpha_first_enrolled_version"] == "v32"
    assert progress["checked_use"] is progress["alpha_enrolled"] is True
    assert progress["representative_proof_tag"] == "PQ0055"
    assert progress["remaining_obligations"] == old["polynomial_prerequisite_progress"]["remaining_obligations"]
    assert progress["proof_routes"] == old["polynomial_prerequisite_progress"]["proof_routes"]
    assert progress["principal_roots"] == formatting.reports[SLUGS[1]]["principal_roots"]
    assert all(chapter["closes_full_milestone"] is False for chapter in node["additional_checked_chapters"])
    assert "G091 remains open" in node["why"] and "gcd/Bezout" in node["why"]


def test_current_and_historical_boundaries_have_unambiguous_different_authority(formatting):
    old, new = formatting.original, formatting.projected
    assert new["meta"]["current_alpha_version"] == "v32"
    assert new["meta"]["current_alpha_checked_use_count"] == 3971
    assert new["meta"]["current_alpha_catalog_sha256"] == "a" * 64
    assert new["meta"]["current_G009_alpha_admitted"] is True and new["meta"]["current_G091_proved"] is False
    assert new["meta"]["historical_alpha_versions"] == [*old["meta"]["historical_alpha_versions"], "v31"]
    assert new["meta"]["historical_research_admission_flags_are_current_authority"] is False
    for key in ("g009_research_alpha_admission", "polynomial_prerequisite_alpha_admission"):
        assert new["meta"][key] == old["meta"][key] is False
    boundary = new["ambitious_boundaries"]["alpha_v32_edition"]
    assert (boundary["theorem_count"], boundary["dependency_edge_count"], boundary["stable_closed_count"]) == (3971, 12751, 432)
    assert boundary["new_theorem_count"] == 175 and boundary["stable_unchanged"] is True
    historical = new["ambitious_boundaries"]["alpha_v32_research_admission"]
    assert historical["original_parent_meta"] == old["meta"]
    assert historical["original_parent_alpha_v31_edition"] == old["ambitious_boundaries"]["alpha_v31_edition"]
    assert historical["all_parent_admissions_replayed_here"] is False
    assert historical["historical_research_receipts_are_new_proof_authority"] is False
    assert historical["completed_named_targets"] == ["G009"]


@pytest.mark.parametrize("index", range(13))
def test_all_thirteen_new_source_references_match_actual_frozen_bytes(formatting, index):
    owner = atlas.research.FACTORIES[index]
    row = next(row for row in formatting.projected["sources"] if row["id"] == f"S{93 + index}")
    assert row["path"] == owner.source and row["bytes"] == owner.source_bytes and row["sha256"] == owner.source_sha256
    raw = (atlas.ROOT / owner.source).read_bytes()
    assert len(raw) == row["bytes"] and sha256(raw).hexdigest() == row["sha256"]


def test_only_current_identity_and_seven_page_overrides_change_definition_json(formatting):
    old, new = formatting.parent_graph, formatting.graph
    assert atlas.DEFINITION_PAGE_ROUTES == PAGE_OVERRIDES
    assert set(new) == set(old)
    assert {key: value for key, value in new.items() if key not in ("campaign_snapshot_sha256", "definition_page_overrides")} == {
        key: value for key, value in old.items() if key not in ("campaign_snapshot_sha256", "definition_page_overrides")}
    assert new["definition_page_overrides"]["PD0047"] == old["definition_page_overrides"]["PD0047"]
    assert set(new["definition_page_overrides"]) == {"PD0047", *PAGE_OVERRIDES}
    assert new["campaign_snapshot_sha256"] == atlas._digest(formatting.projected)
    result = _definition_dags(formatting.projected, new)
    assert (len(result[0]), len(result[1]), result[2], result[3]) == (474, 390, 855, 844)
    assert (result[4], result[5], result[6]) == (590, 325, 265)
    assert _milestone_dag(formatting.projected) == _milestone_dag(formatting.original)


@pytest.mark.parametrize("identifier", tuple(PAGE_OVERRIDES))
def test_seven_overrides_preserve_the_actual_reviewed_identity_and_expansion(formatting, identifier):
    name, registry, route = PAGE_OVERRIDES[identifier]
    row = next(row for row in formatting.graph["reviewed_definitions"] if row["id"] == identifier)
    old = next(row for row in formatting.parent_graph["reviewed_definitions"] if row["id"] == identifier)
    assert row == old and row["name"] == name and row["route"] == registry
    assert formatting.graph["definition_page_overrides"][identifier] == {
        "name": name, "registry_route": registry, "route": route, "proof_authority": False}
    assert registry not in formatting.routes and route in formatting.routes


def test_all_390_definition_targets_are_actual_same_id_bytes_not_invented_aliases(formatting):
    targets = atlas._definition_targets(formatting.graph, formatting.routes)
    assert len(targets) == 390
    assert set(targets) == {row["id"] for row in formatting.graph["reviewed_definitions"]}
    for identifier, target in targets.items():
        assert target["path"] == target["route"] + "/explorer/defined/definition/" + identifier + ".html"
        assert target["route"] in formatting.routes and target["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", target["sha256"])
    for identifier, (_, _, route) in PAGE_OVERRIDES.items():
        assert targets[identifier]["route"] == route
    assert {identifier for identifier in targets if identifier.startswith("CF")} == {
        "CF0011", "CF0013", "CF0014", "CF0015", "CF0016"}


@pytest.mark.parametrize("deployed", (False, True), ids=("raw", "public"))
def test_actual_javascript_routes_all_65_current_families_and_rejects_foreign_ones(formatting, deployed):
    path = "/proofs/grand-campaign/index.html" if deployed else "/book/_static/constructive-research-campaign-v32/index.html"
    source = "const window={location:{pathname:" + json.dumps(path) + "}};\n"
    source += _function(formatting.html.decode(), "explorerBase")
    source += "\nconst routes=" + json.dumps(formatting.routes) + ";\n"
    source += "const result={}; Object.keys(routes).forEach(r=>result[r]=explorerBase(r));\n"
    source += "const rejected=[]; for (const x of ['', '../evil', '__proto__', 'signed-arithmetic', 'finite-prefix-data']) {"
    source += "try {explorerBase(x);} catch(e) {rejected.push(x);}}\nconsole.log(JSON.stringify({result,rejected}));"
    actual = _node(source)
    assert len(actual["result"]) == 65 and len(actual["rejected"]) == 5
    for slug, package in formatting.routes.items():
        prefix = "../" if deployed else "../" + package + "/"
        assert actual["result"][slug] == prefix + slug + "/explorer/defined/"


def test_actual_definition_link_tables_use_every_reviewed_same_id_override(formatting):
    html = formatting.html.decode()
    source = _table(html, "COMPILED_DEFINITIONS") + "\n" + _table(html, "INCOMPATIBLE_DEFINITIONS")
    actual = _node(source + "\nconsole.log(JSON.stringify([COMPILED_DEFINITIONS,INCOMPATIBLE_DEFINITIONS]));")
    for table, key in zip(actual, ("compatible_reviewed_matches", "incompatible_reviewed_matches"), strict=True):
        assert set(table) == {row["blueprint_name"] for row in formatting.graph[key]}
        for row in formatting.graph[key]:
            result = table[row["blueprint_name"]]
            route = formatting.graph["definition_page_overrides"].get(row["reviewed_id"], {}).get("route", row["route"])
            assert (result["id"], result["name"], result["route"], result["parameters"]) == (
                row["reviewed_id"], row["reviewed_name"], route, row["reviewed_parameters"])
            assert route in formatting.routes
            if "argumentOrder" in result:
                assert result["argumentOrder"] == row["reviewed_argument_blueprint_positions"]


def test_original_styles_layout_and_unmodified_graph_functions_are_literal(formatting):
    before, after = formatting.parents["index.html"].decode(), formatting.html.decode()
    assert re.findall(r"<style[^>]*>.*?</style>", before, re.S) == re.findall(r"<style[^>]*>.*?</style>", after, re.S)
    for name in ("localResearchProved", "definitionDomains", "definitionButtons", "renderNodeNotation",
                 "proofHref", "renderProofLinks", "updateDetails"):
        assert _function(before, name) == _function(after, name)
    assert _table(before, "PROOF_ROOTS") == _table(after, "PROOF_ROOTS")
    for attribute in ("data-proof-home", "data-proof-quadratic", "data-proof-bertrand",
                      "data-node-proof-links", "data-node-status", "data-graph-svg"):
        assert after.count(attribute) == before.count(attribute)
    embedded = re.findall(r'<script type="application/json" id="campaign-data">(.*?)</script>', after, re.S)
    assert len(embedded) == 1 and json.loads(embedded[0]) == formatting.projected
    assert not re.search(r"^\s*G091:", after, re.M)


@pytest.mark.parametrize("deployed", (False, True), ids=("raw", "public"))
def test_actual_configured_home_and_query_revision_preserve_both_layouts(formatting, deployed):
    html = formatting.html.decode()
    path = "/proofs/grand-campaign/" if deployed else "/book/_static/constructive-research-campaign-v32/index.html"
    source = "const window={location:{pathname:" + json.dumps(path) + "}};\n"
    source += "const state={campaign:" + json.dumps(formatting.projected) + "};\n"
    source += _function(html, "proofHref") + "\n" + _function(html, "explorerBase")
    match = re.search(r'        document.querySelector\("\[data-proof-home\]"\)\.setAttribute\("href", proofHref\(\n.*?\n          .*?\)\);', html)
    assert match
    source += "\nlet home; const document={querySelector:()=>({setAttribute:(k,v)=>{home=v}})};\n" + match[0]
    source += '\nconsole.log(JSON.stringify({home,graph:proofHref(explorerBase("multiplicative-convolution")+"graph.html?target=MX0059&view=prerequisites")}));'
    actual = _node(source)
    expected = "../index.html" if deployed else "../constructive-research-explorer-v32/index.html"
    assert actual["home"] == expected + "?v=" + "a" * 12
    assert actual["graph"].endswith("graph.html?target=MX0059&view=prerequisites&v=" + "a" * 12)
    for token in ("data-proof-home", "data-proof-quadratic", "data-proof-bertrand"):
        initial = re.search(r'<a href="([^"]+)" ' + token, html)
        assert initial and initial[1].endswith("?v=" + "a" * 12)


def _status_runtime(formatting, g009=None, g091=None):
    html = formatting.html.decode()
    source = "\n".join(_function(html, name) for name in (
        "currentResearchAdmitted", "localResearchProved", "proved", "describeStatus", "statusCaveat"))
    source += "\nconst a=" + json.dumps(g009 or _goal(formatting.projected, "G009")) + ";"
    source += "\nconst b=" + json.dumps(g091 or _goal(formatting.projected, "G091")) + ";"
    source += "\nconsole.log(JSON.stringify({admitted:currentResearchAdmitted(a),proved:proved(a),"
    source += "status:describeStatus(a),g091proved:proved(b),g091status:describeStatus(b),caveat:statusCaveat(b)}));"
    return _node(source)


def test_actual_js_distinguishes_g009_admission_from_g091_open_prerequisites(formatting):
    result = _status_runtime(formatting)
    assert result["admitted"] is result["proved"] is True
    assert "first admitted to Alpha v32" in result["status"]
    assert result["g091proved"] is False and result["g091status"] == "Open research objective"
    assert "first admitted to Alpha v32" in result["caveat"] and "G091 remains open" in result["caveat"]


@pytest.mark.parametrize("field,value", (
    ("alpha_version", "v31"), ("alpha_first_enrolled_version", "v31"),
    ("checked_use", False), ("checked_use", 1), ("alpha_enrolled", False),
    ("stable_member", True), ("full_empty_context_closure", False),
    ("independent_lean_bundle_verified", False), ("full_G009_finite_coded_contract_proved", False),
))
def test_actual_js_current_admission_branch_rejects_missing_or_substituted_flags(formatting, field, value):
    node = deepcopy(_goal(formatting.projected, "G009"))
    node["evidence"][field] = value
    result = _status_runtime(formatting, g009=node)
    assert result["admitted"] is False and "first admitted to Alpha v32" not in result["status"]


@pytest.mark.parametrize("attack", ("schema", "alpha_count", "goal_count", "node_count", "g009_open",
    "g009_full_false", "g009_admitted", "g091_closed", "g091_full_true", "g091_admitted",
    "audit_count", "audit_snapshot", "graph_count", "definition_cycle"))
def test_changed_parent_metadata_never_enters_a_new_projection(formatting, attack):
    old, graph, audit = deepcopy(formatting.original), deepcopy(formatting.parent_graph), deepcopy(formatting.parent_audit)
    if attack == "schema": old["schema"] = "other"
    elif attack == "alpha_count": old["meta"]["current_alpha_checked_use_count"] -= 1
    elif attack == "goal_count": old["meta"]["goal_count"] -= 1
    elif attack == "node_count": old["nodes"].pop()
    elif attack == "g009_open": _goal(old, "G009")["status"] = "open"
    elif attack == "g009_full_false": _goal(old, "G009")["evidence"]["full_G009_finite_coded_contract_proved"] = False
    elif attack == "g009_admitted": _goal(old, "G009")["evidence"]["alpha_enrolled"] = True
    elif attack == "g091_closed": _goal(old, "G091")["status"] = "available"
    elif attack == "g091_full_true": _goal(old, "G091")["polynomial_prerequisite_progress"]["full_G091_proved"] = True
    elif attack == "g091_admitted": _goal(old, "G091")["polynomial_prerequisite_progress"]["alpha_enrolled"] = True
    elif attack == "audit_count": audit["theorem_count"] = 3971
    elif attack == "audit_snapshot": audit["campaign_snapshot_sha256"] = "0" * 64
    elif attack == "graph_count": graph["reviewed_definition_count"] -= 1
    elif attack == "definition_cycle": graph["reviewed_definitions"][0]["dependencies"] = [graph["reviewed_definitions"][0]["name"]]
    documents = {**formatting.parents, "campaign.json": atlas._json(old),
                 "definitions.json": atlas._json(graph), "dag-audit.json": atlas._json(audit)}
    with pytest.raises((atlas.publication.PublicationError, CampaignDagError)):
        atlas._parent(documents)


@pytest.mark.parametrize("attack", ("schema", "count", "checked", "stable", "edges", "duplicate",
                                    "owned_order", "families", "catalog_sha", "binding_sha"))
def test_private_projection_rejects_bad_current_scope_even_without_proof_authority(formatting, attack):
    catalog, reports = deepcopy(formatting.catalog), deepcopy(formatting.reports)
    catalog_sha, binding_sha = "a" * 64, "b" * 64
    if attack == "schema": catalog["schema"] = "peano-library-alpha-snapshot-v31"
    elif attack == "count": catalog["theorem_count"] -= 1
    elif attack == "checked": catalog["checked_use_count"] -= 1
    elif attack == "stable": catalog["stable_count"] += 1
    elif attack == "edges": catalog["edge_count"] += 1
    elif attack == "duplicate": catalog["theorems"][0] = deepcopy(catalog["theorems"][1])
    elif attack == "owned_order": catalog["theorems"][-1], catalog["theorems"][-2] = catalog["theorems"][-2], catalog["theorems"][-1]
    elif attack == "families": reports.pop(SLUGS[-1])
    elif attack == "catalog_sha": catalog_sha = "bad"
    elif attack == "binding_sha": binding_sha = None
    with pytest.raises(atlas.publication.PublicationError):
        atlas._project(formatting.original, catalog, reports, catalog_sha, binding_sha, formatting.routes)


@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("attack", ("owned_missing", "owned_order", "bundle_sha", "bundle_bytes",
    "bundle_ha", "bundle_lean", "kernel_calls", "principal_missing", "principal_false", "principal_node",
    "principal_sha", "principal_bool", "checked_false", "stable", "wrong_membership", "closure_sha", "first_admission"))
def test_private_family_projection_is_fail_closed_but_never_a_verifier(formatting, slug, attack):
    family = atlas.research.FAMILY_BY_SLUG[slug]
    report = deepcopy(formatting.reports[slug])
    rows = {row["name"]: deepcopy(row) for row in formatting.catalog["theorems"]}
    name = family.owned_names[0]
    if attack == "owned_missing": report["owned_node_ids"].pop(name)
    elif attack == "owned_order": report["rows"].reverse()
    elif attack == "bundle_sha": report["bundle"]["sha256"] = "0" * 64
    elif attack == "bundle_bytes": report["bundle"]["bytes"] += 1
    elif attack == "bundle_ha": report["bundle"]["original_ha_checked"] = False
    elif attack == "bundle_lean": report["bundle"]["independent_lean_checked"] = False
    elif attack == "kernel_calls": report["bundle"]["kernel_calls"] -= 1
    elif attack == "principal_missing": report["principal_roots"].pop()
    elif attack == "principal_false": report["principal_roots"][0]["complete_ordinary_ha_checked"] = False
    elif attack == "principal_node": report["principal_roots"][0]["node_id"] = -1
    elif attack == "principal_sha": report["principal_roots"][0]["statement_sha256"] = "0" * 64
    elif attack == "principal_bool": report["principal_roots"][0]["ordinary_certificate_nodes"] = True
    elif attack == "checked_false": rows[name]["checked_use"] = False
    elif attack == "stable": rows[name]["membership"] = "stable"
    elif attack == "wrong_membership": rows[name]["evidence_status"] = "pending_layered_closure"
    elif attack == "closure_sha": rows[name]["empty_context_closure"]["certificate_sha256"] = "0" * 64
    elif attack == "first_admission": rows[name]["alpha_v32_frontier_enrollment"]["first_enrolled_version"] = "v31"
    with pytest.raises(atlas.publication.PublicationError):
        atlas._admitted_family(family, report, rows)


@pytest.mark.parametrize("attack", ("missing", "extra", "duplicate", "traversal", "foreign", "research_to_old"))
def test_family_route_inventory_has_no_wildcard_or_legacy_fallback(formatting, attack):
    rows = deepcopy(list(formatting.metadata))
    if attack == "missing": rows.pop()
    elif attack == "extra": rows.append(deepcopy(rows[0]))
    elif attack == "duplicate": rows[1]["slug"] = rows[0]["slug"]
    elif attack == "traversal": rows[0]["slug"] = "../elsewhere"
    elif attack == "foreign": rows[0]["package"] = "external-package"
    elif attack == "research_to_old": rows[-1]["package"] = atlas.publication.OUTPUT_NAMES["completed"]
    with pytest.raises(atlas.publication.PublicationError):
        atlas._package_map(tuple(rows))


@pytest.mark.parametrize("attack", ("name", "registry", "authority", "route", "duplicate"))
def test_definition_destinations_cannot_change_identity_or_authority(formatting, attack):
    graph = deepcopy(formatting.graph)
    target = graph["definition_page_overrides"]["ND0251"]
    if attack == "name": target["name"] = "DifferentConcept"
    elif attack == "registry": target["registry_route"] = "prime-field-polynomials"
    elif attack == "authority": target["proof_authority"] = True
    elif attack == "route": target["route"] = "finite-prefix-data"
    elif attack == "duplicate": graph["reviewed_definitions"].append(deepcopy(graph["reviewed_definitions"][0]))
    with pytest.raises(atlas.publication.PublicationError):
        atlas._definition_targets(graph, formatting.routes)


@pytest.mark.parametrize("attack", ("shadow", "name", "registry", "missing_route"))
def test_seven_route_repairs_never_shadow_existing_definition_records(formatting, attack):
    graph, routes = deepcopy(formatting.parent_graph), dict(formatting.routes)
    row = next(row for row in graph["reviewed_definitions"] if row["id"] == "ND0251")
    if attack == "shadow": graph["definition_page_overrides"]["ND0251"] = {}
    elif attack == "name": row["name"] = "OtherName"
    elif attack == "registry": row["route"] = "prime-fields"
    elif attack == "missing_route": routes.pop("dirichlet-convolution")
    with pytest.raises(atlas.publication.PublicationError):
        atlas._graph(graph, formatting.projected, routes)


@pytest.mark.parametrize("attack", ("missing", "extra", "bool_bytes", "oversize", "wrong_hash", "bad_hash"))
def test_literal_parent_pins_have_no_missing_document_fallback(monkeypatch, attack):
    pins = deepcopy(atlas.PARENT_PINS)
    if attack == "missing": pins.pop("campaign.json")
    elif attack == "extra": pins["other.json"] = deepcopy(pins["campaign.json"])
    elif attack == "bool_bytes": pins["campaign.json"]["bytes"] = True
    elif attack == "oversize": pins["campaign.json"]["bytes"] = atlas.MAX_CAMPAIGN_BYTES + 1
    elif attack == "wrong_hash": pins["campaign.json"]["sha256"] = "0" * 64
    elif attack == "bad_hash": pins["campaign.json"]["sha256"] = None
    monkeypatch.setattr(atlas, "PARENT_PINS", pins)
    with pytest.raises(atlas.publication.PublicationError):
        atlas.parent_files()


@pytest.mark.parametrize("attack", ("dispatcher", "compiled", "incompatible", "proved", "status", "caveat",
    "home", "qr", "bertrand", "injection", "revision", "duplicate_dispatcher", "duplicate_compiled", "duplicate_incompatible"))
def test_changed_parent_html_or_unsafe_embedding_is_rejected(formatting, attack):
    source, campaign = formatting.parents["index.html"].decode(), deepcopy(formatting.projected)
    revision = "a" * 12
    replacements = {"dispatcher": "function explorerBase(route)", "compiled": "var COMPILED_DEFINITIONS = {",
                    "incompatible": "var INCOMPATIBLE_DEFINITIONS = {", "proved": "function proved(node)",
                    "status": "function describeStatus(node)", "caveat": "function statusCaveat(node)",
                    "home": "data-proof-home", "qr": "data-proof-quadratic", "bertrand": "data-proof-bertrand"}
    if attack in replacements:
        source = source.replace(replacements[attack], "changed_original_marker", 1)
    elif attack == "injection": campaign["title"] = "</script><script>throw 1</script>"
    elif attack == "revision": revision = "false_revision"
    elif attack == "duplicate_dispatcher": source += "\n" + _function(source, "explorerBase") + "\n\n"
    elif attack == "duplicate_compiled": source += "\n" + _table(source, "COMPILED_DEFINITIONS")
    elif attack == "duplicate_incompatible": source += "\n" + _table(source, "INCOMPATIBLE_DEFINITIONS")
    with pytest.raises(atlas.publication.PublicationError):
        atlas._html(source, campaign, formatting.graph, formatting.routes, revision)


@pytest.mark.parametrize("value", (None, {}, [], object()))
def test_actual_public_guard_rejects_noncapabilities_before_parent_or_projection(monkeypatch, value):
    def forbidden(*args, **kwargs):
        pytest.fail("a noncapability reached historical inputs or private projection")
    monkeypatch.setattr(atlas, "parent_files", forbidden)
    monkeypatch.setattr(atlas, "source_binding", forbidden)
    monkeypatch.setattr(atlas, "_project", forbidden)
    monkeypatch.setattr(sys.modules[__name__], "_assert_published_content", forbidden)
    with pytest.raises(atlas.publication.PublicationError):
        atlas.build_files_from_live(value)
    with pytest.raises(atlas.publication.PublicationError):
        _assert_published_files({}, value)


def test_private_formatting_fixture_is_not_an_authorizing_release(formatting):
    assert formatting.fixture_notice == NOTICE and formatting.catalog["fixture_notice"] == NOTICE
    assert not hasattr(formatting, "require_unchanged")
    with pytest.raises(atlas.publication.PublicationError):
        atlas.publication.require_live(formatting)


def test_public_builder_has_no_writes_receipt_input_catalogue_load_or_proof_replay():
    tree = ast.parse(inspect.getsource(atlas.build_files_from_live))
    function = tree.body[0]
    assert [argument.arg for argument in function.args.args] == ["context"]
    assert ast.unparse(function.body[1]) == "publication.require_live(context)"
    assert ast.unparse(function.body[-2]) == "publication.require_live(context)"
    calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not calls.intersection({"open", "load_catalog", "replay", "check", "write_bytes", "write_text"})
    assert "validate_campaign_dags" not in calls  # Invoked only inside _audit with the actual context catalogue.
    for node in ast.walk(ast.parse(inspect.getsource(atlas._audit))):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "validate_campaign_dags":
            assert {keyword.arg: ast.unparse(keyword.value) for keyword in node.keywords}["catalog"] == "catalog"
            break
    else:
        pytest.fail("the actual separate current catalogue DAG check disappeared")


def test_all_actual_formatter_inputs_are_source_bound_without_absolute_labels():
    required = {"scripts/extend_constructive_research_campaign_v32.py",
                "peano-lab/py/tests/test_constructive_research_campaign_v32.py",
                "scripts/constructive_research_publication_v32.py",
                "scripts/extend_constructive_second_wave_campaign.py",
                "scripts/sync_constructive_grand_campaign.py",
                "scripts/constructive_lower_layer_definition_graph.py",
                "scripts/constructive_definition_graph.py",
                "scripts/check_alpha_v32_research.py"}
    assert required <= set(atlas.SOURCE_PATHS)
    assert len(set(atlas.SOURCE_PATHS)) == len(atlas.SOURCE_PATHS)
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in atlas.SOURCE_PATHS)
    first = atlas.source_binding()
    assert first == atlas.source_binding() and re.fullmatch(r"[0-9a-f]{64}", first)


def _assert_published_files(files, context):
    """Assertions only for root's genuine same-live four-file publication phase."""
    atlas.publication.require_live(context)
    _assert_published_content(files, context)
    atlas.publication.require_live(context)


def _assert_published_content(files, context):
    """Private display assertions only; observations never grant proof authority."""
    assert type(files) is dict and set(files) == set(PARENT_PINS)
    assert all(type(name) is str and type(raw) is bytes and 0 < len(raw) <= 8 * 1024 * 1024
               for name, raw in files.items())
    parents = atlas.parent_files()
    old = json.loads(parents["campaign.json"])
    parent_graph = json.loads(parents["definitions.json"])
    parent_audit = json.loads(parents["dag-audit.json"])
    campaign, graph, audit = (json.loads(files[name]) for name in ("campaign.json", "definitions.json", "dag-audit.json"))
    html = files["index.html"].decode()
    for name, document in (("campaign.json", campaign), ("definitions.json", graph), ("dag-audit.json", audit)):
        assert files[name] == atlas.publication.json_bytes(document)
    assert campaign["meta"]["current_alpha_version"] == "v32"
    assert campaign["meta"]["current_alpha_checked_use_count"] == len(context.catalog["theorems"]) == 3971
    assert campaign["meta"]["current_alpha_catalog_sha256"] == context.catalog_sha256
    assert context.catalog["stable_count"] == 432 and context.catalog["edge_count"] == 12751
    assert len(campaign["nodes"]) == 144 and sum(n["id"].startswith("G") for n in campaign["nodes"]) == 120
    for before, after in zip(old["nodes"], campaign["nodes"], strict=True):
        for field in ("id", "status", "statement", "deps", "family", "layer", "title", "difficulty"):
            assert after.get(field) == before.get(field)
        if before["id"] not in ("G009", "G091"):
            assert after == before
        else:
            history = after["historical_research_checkpoint"]
            assert history["record"] == before and history["stored_record_is_new_proof_authority"] is False
            assert (history["bytes"], history["sha256"]) == PARENT_PINS["campaign.json"]
    assert campaign["definitions"] == old["definitions"]
    assert campaign["sources"][:len(old["sources"])] == old["sources"]
    assert len(campaign["sources"]) == len(old["sources"]) + 17
    assert len({row["id"] for row in campaign["sources"]}) == len(campaign["sources"])
    assert _goal(campaign, "G009")["evidence"]["checked_use"] is True
    assert _goal(campaign, "G009")["evidence"]["full_G009_finite_coded_contract_proved"] is True
    assert _goal(campaign, "G009")["evidence"]["stable_member"] is False
    g091 = _goal(campaign, "G091")
    assert g091["status"] == "open" and "evidence" not in g091
    assert g091["polynomial_prerequisite_progress"]["full_G091_proved"] is False
    assert g091["polynomial_prerequisite_progress"]["stable_member"] is False
    assert g091["polynomial_prerequisite_progress"]["remaining_obligations"] == _goal(old, "G091")["polynomial_prerequisite_progress"]["remaining_obligations"]
    by_name = {row["name"]: row for row in context.catalog["theorems"]}
    assert {row["name"]: row["statement_sha256"] for row in _goal(campaign, "G009")["evidence"]["inherited_contract_components"]} == G009_COMPONENTS
    assert all(by_name[name]["statement_sha256"] == expected and by_name[name]["checked_use"] is True
               for name, expected in G009_COMPONENTS.items())
    for identifier, slug, field, roots in (
        ("G009", SLUGS[0], "evidence", "ordinary_principal_roots"),
        ("G091", SLUGS[1], "polynomial_prerequisite_progress", "principal_roots"),
    ):
        current, report = _goal(campaign, identifier)[field], context.families[slug]
        assert current[roots] == report["principal_roots"] and len(current[roots]) == 6
        assert current["alpha_version"] == current["alpha_first_enrolled_version"] == "v32"
        assert current["checked_use"] is current["alpha_enrolled"] is True
        assert current["current_catalog_sha256"] == context.catalog_sha256
        assert current["current_source_binding_sha256"] == context.source_binding_sha256
        assert current["bundle_sha256"] == report["bundle"]["sha256"]
        assert all(row["complete_ordinary_ha_checked"] is True and row["ordinary_certificate_nodes"] > 1 for row in current[roots])
        for principal in current[roots]:
            row = by_name[principal["name"]]
            assert row["checked_use"] is True and row["body_checked"] is True
            assert row["statement_sha256"] == principal["statement_sha256"]
            assert row["alpha_v32_frontier_enrollment"]["first_enrolled_version"] == "v32"
    assert {key: value for key, value in graph.items() if key not in ("campaign_snapshot_sha256", "definition_page_overrides")} == {
        key: value for key, value in parent_graph.items() if key not in ("campaign_snapshot_sha256", "definition_page_overrides")}
    assert graph["definition_page_overrides"]["PD0047"] == parent_graph["definition_page_overrides"]["PD0047"]
    assert set(graph["definition_page_overrides"]) == {"PD0047", *PAGE_OVERRIDES}
    assert graph["campaign_snapshot_sha256"] == atlas._digest(campaign)
    for identifier, (name, registry, route) in PAGE_OVERRIDES.items():
        assert graph["definition_page_overrides"][identifier] == {
            "name": name, "registry_route": registry, "route": route, "proof_authority": False}
    actual_definition_dags = _definition_dags(campaign, graph)
    assert (len(actual_definition_dags[0]), len(actual_definition_dags[1]),
            actual_definition_dags[2], actual_definition_dags[3]) == (474, 390, 855, 844)
    assert _milestone_dag(campaign) == _milestone_dag(old)
    assert audit["alpha_version"] == "v32" and audit["catalog_sha256"] == context.catalog_sha256
    assert (audit["theorem_count"], audit["theorem_edge_count"]) == (3971, 12751)
    assert audit["campaign_snapshot_sha256"] == atlas._digest(campaign)
    for key in ("milestone_count", "milestone_proof_edge_count", "milestone_dag_sha256",
                "definition_count", "definition_edge_count", "definition_dag_sha256",
                "reviewed_definition_count", "reviewed_definition_edge_count", "reviewed_definition_dag_sha256",
                "milestone_usage_edge_count", "statement_usage_edge_count", "declared_notation_edge_count"):
        assert audit[key] == parent_audit[key]
    assert audit["historical_parent_audit"]["record"] == parent_audit
    assert audit["historical_parent_audit"]["stored_audit_is_new_proof_authority"] is False
    admission = audit["current_research_admission"]
    assert admission["full_G009_proved"] is True and admission["full_G091_proved"] is False
    assert admission["stable_changed"] is admission["notation_edges_are_proof_premises"] is False
    assert admission["ordinary_principal_count"] == 12 and admission["new_theorem_count"] == 175
    assert admission["fresh_bundles"] == [context.families[slug]["bundle"] for slug in SLUGS]
    routes = atlas._package_map(atlas.publication._all_family_metadata())
    assert campaign["current_proof_family_packages"] == routes and len(routes) == 65
    assert len(atlas._definition_targets(graph, routes)) == 390
    embedded = re.findall(r'<script type="application/json" id="campaign-data">(.*?)</script>', html, re.S)
    assert len(embedded) == 1 and json.loads(embedded[0]) == campaign
    assert re.findall(r"<style[^>]*>.*?</style>", html, re.S) == re.findall(r"<style[^>]*>.*?</style>", parents["index.html"].decode(), re.S)
    assert _table(html, "PROOF_ROOTS") == _table(parents["index.html"].decode(), "PROOF_ROOTS")
    assert "Alpha v32 polynomial prerequisite — G091 remains open; not Stable" in html
    assert "first admitted to Alpha v32, not Stable" in html


def test_same_live_wrapper_preserves_the_exact_59_content_assertions_and_guards():
    wrapper = ast.parse(inspect.getsource(_assert_published_files)).body[0]
    assert [ast.unparse(node) for node in wrapper.body[1:]] == [
        "atlas.publication.require_live(context)",
        "_assert_published_content(files, context)",
        "atlas.publication.require_live(context)",
    ]
    content = ast.parse(inspect.getsource(_assert_published_content)).body[0]
    original = ast.Module(body=content.body[1:], type_ignores=[])
    assert sum(isinstance(node, ast.Assert) for node in ast.walk(original)) == 59
    assert sha256(ast.dump(original, include_attributes=False).encode()).hexdigest() == (
        "61214d85995843dffdd7b68690d45ed7dbfeb903bfe49cebc7a33daf57418d4e"
    )


def _main(argv=None):
    """Each selected test window has the original process and observed-RSS caps."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("the exact test window must be positive")

    class Window:
        def __init__(self):
            self.selected, self.passed, self.bad = [], set(), []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start + args.case_count]
            if not chosen or args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact requested test window is unavailable")
            ids = {item.nodeid for item in chosen}
            config.hook.pytest_deselected(items=[item for item in items if item.nodeid not in ids])
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            if report.when == "call" and report.passed:
                self.passed.add(report.nodeid)
            elif report.failed or report.skipped or getattr(report, "wasxfail", None):
                self.bad.append(report.nodeid)

    plugin = Window()
    options = [str(Path(__file__).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only:
        options.append("--collect-only")
    status = pytest.main(options, plugins=[plugin])
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    if not 0 < peak <= 1536 * 1024 * 1024:
        raise RuntimeError("the original observed RSS limit was exceeded")
    if not args.collect_only and (plugin.bad or plugin.passed != set(plugin.selected)):
        status = status or 1
    print(json.dumps({"selected": len(plugin.selected), "passed": len(plugin.passed),
        "collect_only": args.collect_only, "pytest_exit_code": int(status),
        "elapsed_seconds": time.monotonic() - _BOUNDED_STARTED, "peak_rss_bytes": peak,
        "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": 180}, sort_keys=True), flush=True)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(_main())
