"""Independent v33 atlas identity, notation and interactive-route checks.

All standalone fixtures are presentation-only; none can mint a live release.
The publication plugin supplies genuine proof evidence to the strict wrapper.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import extend_constructive_research_campaign_v33 as atlas
from sync_constructive_grand_campaign import _definition_dags, _milestone_dag, validate_campaign_dags
from tests.test_constructive_research_campaign_v32 import _function, _node

NOTICE = "PRIVATE DISPLAY FIXTURE ONLY; NOT A VERIFIED CATALOGUE, PROOF OR RELEASE"
PINS = {
    "campaign.json": (692317, "fab08f9f1431cbef1239d0dce9ff0329ebba00978c9a4f21c092138b4f018b84"),
    "definitions.json": (1486171, "f5d780020b639b2a0039f4cab0cb7aa1b66f05d5f72395c7e2f762d060b3b5f1"),
    "dag-audit.json": (5743, "954827c9ec10a300542adc8d485b637f8f4acd8aaa2dbdea01ba11d79d4657dd"),
    "index.html": (742112, "090e11df1b34dfdbff4debd1df8e08630f87b98582c2d335b41082240308507d"),
}
DEFINITIONS = {
    "ND0334": "PolynomialLeftPad", "ND0335": "PolynomialPowerCoefficient",
    "ND0336": "PolynomialEquivalent", "ND0337": "FpPolynomialQuotientStep",
    "ND0338": "FpPolynomialQuotientPrefix", "ND0339": "PolynomialQuotientLength",
    "ND0340": "FpPolynomialDivisionExecution",
}
PRINCIPALS = (
    "prime_field_polynomial_division_execution_functional",
    "prime_field_polynomial_division_execution_exists_unique",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent",
    "prime_field_polynomial_convolution_both_left_paddings_exists",
    "prime_field_polynomial_equivalent_implies_left_pad",
    "prime_field_polynomial_add_equivalent_congruent",
    "prime_field_polynomial_subtract_equivalent_congruent",
    "prime_field_polynomial_convolution_equivalent_congruent",
)


def _goal(campaign, identifier):
    return next(row for row in campaign["nodes"] if row["id"] == identifier)


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(item) for item in value]
    return value


@pytest.mark.parametrize("name", tuple(PINS))
def test_exact_four_parent_documents_remain_literal(name):
    raw = atlas.parent_files()[name]
    assert (len(raw), sha256(raw).hexdigest()) == PINS[name]
    assert atlas.PARENT_PINS[name] == {"bytes": PINS[name][0], "sha256": PINS[name][1]}


@pytest.fixture(scope="module")
def formatting():
    parents = atlas.parent_files()
    original, old_graph, old_audit = atlas._parent(parents)
    campaign = deepcopy(original)
    campaign["meta"]["fixture_notice"] = NOTICE
    campaign["meta"]["current_alpha_version"] = "v33"
    campaign["ambitious_boundaries"]["alpha_v33_edition"] = {
        "catalog_sha256": "a" * 64, "fixture_notice": NOTICE}
    progress = {
        "alpha_version": "v33", "alpha_first_enrolled_version": "v33",
        "alpha_enrolled": True, "checked_use": True, "stable_member": False,
        "full_G091_proved": False, "division_execution_proved": True,
        "polynomial_associativity_proved": False, "polynomial_gcd_bezout_proved": False,
        "conservative_definition_ids": list(DEFINITIONS), "fixture_notice": NOTICE,
    }
    _goal(campaign, "G091")["polynomial_euclidean_progress"] = progress
    routes = {row["slug"]: atlas.publication.OUTPUT_NAMES[phase]
              for phase, snapshot in atlas.publication.OLDER.items()
              for row in atlas.publication._snapshot(*snapshot)[1]["families"]}
    routes[atlas.SLUGS[0]] = atlas.publication.OUTPUT_NAMES["polynomial"]
    graph = atlas._graph(old_graph, campaign, routes)
    html = atlas._html(parents["index.html"].decode(), campaign, graph, routes, "a" * 12)
    return SimpleNamespace(parents=parents, original=original, old_graph=old_graph, old_audit=old_audit,
                           campaign=campaign, progress=progress, routes=routes, graph=graph, html=html)


def test_397_reviewed_definitions_keep_all390_prior_expansions(formatting):
    old = {row["id"]: row for row in formatting.old_graph["reviewed_definitions"]}
    current = {row["id"]: row for row in formatting.graph["reviewed_definitions"]}
    assert len(old) == 390 and len(current) == 397
    assert set(current) - set(old) == set(DEFINITIONS)
    assert {key: current[key] for key in old} == old
    assert {key: current[key]["name"] for key in DEFINITIONS} == DEFINITIONS
    assert all(current[key]["route"] == "polynomial-euclidean-division" for key in DEFINITIONS)
    assert sum(len(row["dependencies"]) for row in old.values()) == 844
    assert sum(len(row["dependencies"]) for row in current.values()) == 865
    assert formatting.graph["definitions"] == formatting.old_graph["definitions"]
    assert formatting.graph["definition_edges"] == formatting.old_graph["definition_edges"]
    assert formatting.graph["milestone_usage_edges"] == formatting.old_graph["milestone_usage_edges"]
    assert formatting.graph["definition_page_overrides"] == formatting.old_graph["definition_page_overrides"]


def test_blueprint_and_144_milestone_dags_are_not_inflated_by_notation(formatting):
    assert _milestone_dag(formatting.campaign) == _milestone_dag(formatting.original)
    definitions, reviewed, edges, reviewed_edges, *_ = _definition_dags(formatting.campaign, formatting.graph)
    assert (len(definitions), len(reviewed), edges, reviewed_edges) == (474, 397, 855, 865)
    assert len(formatting.campaign["nodes"]) == 144
    assert sum(row["id"].startswith("G") for row in formatting.campaign["nodes"]) == 120


@pytest.mark.parametrize("field,value", (
    ("alpha_version", "v32"), ("alpha_first_enrolled_version", "v32"),
    ("alpha_enrolled", False), ("checked_use", False), ("stable_member", True),
    ("full_G091_proved", True), ("division_execution_proved", False),
    ("polynomial_associativity_proved", True), ("polynomial_gcd_bezout_proved", True),
))
def test_current_progress_display_guard_rejects_changed_boundary(formatting, field, value):
    source = formatting.html.decode()
    original = _goal(formatting.campaign, "G091")
    bad = deepcopy(original)
    bad["polynomial_euclidean_progress"][field] = value
    observed = _node(_function(source, "currentPolynomialDivisionProgress") + "\n"
        + "process.stdout.write(JSON.stringify([" +
        "currentPolynomialDivisionProgress(" + json.dumps(original) + ")," +
        "currentPolynomialDivisionProgress(" + json.dumps(bad) + ")]));")
    assert observed == [True, False]


def _notation_navigation(source, campaign, pathname):
    functions = "\n".join(_function(source, name) for name in (
        "currentPolynomialDivisionProgress", "renderNodeNotation", "explorerBase", "proofHref"))
    program = """
var window={location:{pathname:__PATH__}};
var state={campaign:__CAMPAIGN__, nodeDefinitions:new Map()};
function element(tag,label,attrs){return {tag:tag,label:label,attrs:attrs||{},children:[],appendChild:function(x){this.children.push(x);}};}
function empty(node){node.children=[];}
var ui={notationSection:{hidden:true},notation:element("ul")};
function applyAtlasRoute(){throw Error("No invented blueprint alias");}
__FUNCTIONS__
var node=state.campaign.nodes.find(x=>x.id==="G091");
renderNodeNotation(node);
process.stdout.write(JSON.stringify({hidden:ui.notationSection.hidden,
 links:ui.notation.children.map(x=>x.children[0]),
 old:explorerBase("quadratic-reciprocity")}));
""".replace("__PATH__", json.dumps(pathname)).replace("__CAMPAIGN__", json.dumps(campaign)).replace("__FUNCTIONS__", functions)
    return _node(program)


@pytest.mark.parametrize("pathname,prefix", (
    ("/proofs/grand-campaign/", "../polynomial-euclidean-division/explorer/defined/"),
    ("/book/_static/constructive-research-campaign-v33/index.html",
     "../constructive-polynomial-euclidean-explorer-v33/polynomial-euclidean-division/explorer/defined/"),
))
def test_actual_public_and_local_notation_links_are_not_proof_edges(formatting, pathname, prefix):
    actual = _notation_navigation(formatting.html.decode(), formatting.campaign, pathname)
    assert actual["hidden"] is False
    assert len(actual["links"]) == 7
    for link, (identifier, name) in zip(actual["links"], DEFINITIONS.items(), strict=True):
        assert link["tag"] == "a"
        assert link["label"] == "Reviewed conservative definition (notation only): " + name
        assert link["attrs"]["href"] == prefix + "definition/" + identifier + ".html?v=" + "a" * 12


def test_actual_inline_javascript_compiles_without_relabeling_g009(formatting):
    source = formatting.html.decode()
    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", source, re.S)
    compiled = [body for attrs, body in scripts if 'type="application/json"' not in attrs]
    program = 'const vm=require("node:vm");JSON.parse(require("node:fs").readFileSync(0,"utf8")).forEach(x=>new vm.Script(x));'
    subprocess.run(["node", "-e", program], input=json.dumps(compiled), text=True,
                   capture_output=True, check=True, timeout=20)
    assert _function(source, "currentResearchAdmitted") == _function(formatting.parents["index.html"].decode(), "currentResearchAdmitted")
    assert _function(source, "proved") == _function(formatting.parents["index.html"].decode(), "proved")
    assert "first admitted to Alpha v32, not Stable" in source
    assert "Alpha v33 general division and representation laws" in source


@pytest.mark.parametrize("bad", (None, {}, SimpleNamespace(catalog={}, proofs_verified=True)))
def test_display_metadata_cannot_authorize_atlas_publication(bad):
    with pytest.raises(atlas.publication.PublicationError):
        atlas.build_files_from_live(bad)


def _assert_published_content(files, context):
    """Read-only assertions; this function deliberately confers no authority."""
    assert set(files) == {"campaign.json", "definitions.json", "dag-audit.json", "index.html"}
    parents = atlas.parent_files()
    old, old_graph, old_audit = atlas._parent(parents)
    campaign, graph, audit = (atlas.publication.strict_json(files[name])
                              for name in ("campaign.json", "definitions.json", "dag-audit.json"))
    assert campaign["meta"]["current_alpha_version"] == "v33"
    assert campaign["meta"]["current_alpha_checked_use_count"] == 4092
    assert campaign["meta"]["current_alpha_catalog_sha256"] == context.catalog_sha256
    assert campaign["meta"]["goal_count"] == 120 and len(campaign["nodes"]) == 144
    assert campaign["meta"]["historical_alpha_versions"] == [*old["meta"]["historical_alpha_versions"], "v32"]
    assert campaign["meta"]["current_G091_proved"] is False
    assert campaign["definitions"] == old["definitions"]
    assert campaign["sources"][:len(old["sources"])] == old["sources"]
    for before, after in zip(old["nodes"], campaign["nodes"], strict=True):
        if before["id"] != "G091":
            assert before == after
        else:
            for key in ("id", "status", "statement", "deps", "title", "family", "layer"):
                assert before.get(key) == after.get(key)
            assert after["historical_v32_polynomial_progress"]["record"] == before
            assert after["polynomial_prerequisite_progress"] == before["polynomial_prerequisite_progress"]
            assert after["additional_checked_chapters"][:-1] == before["additional_checked_chapters"]
    node = _goal(campaign, "G091")
    progress = node["polynomial_euclidean_progress"]
    report = _thaw(context.families["polynomial-euclidean-division"])
    assert node["status"] == "open" and "evidence" not in node
    assert progress["full_G091_proved"] is progress["polynomial_associativity_proved"] is progress["polynomial_gcd_bezout_proved"] is False
    assert progress["alpha_version"] == progress["alpha_first_enrolled_version"] == "v33"
    assert progress["alpha_enrolled"] is progress["checked_use"] is progress["division_execution_proved"] is True
    assert progress["stable_member"] is False and progress["new_theorem_count"] == 121
    assert progress["bundle"] == report["bundle"]
    assert progress["bundle"]["sha256"] == "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf"
    assert progress["bundle"]["nodes_including_packaging_root"] == 377
    assert progress["bundle"]["dependency_edges_including_packaging"] == 1071
    assert progress["bundle"]["original_ha_checked"] is progress["bundle"]["independent_lean_checked"] is True
    assert progress["principal_roots"] == report["principal_roots"]
    assert tuple(row["name"] for row in progress["principal_roots"]) == PRINCIPALS
    assert all(row["complete_ordinary_ha_checked"] is True for row in progress["principal_roots"])
    assert progress["conservative_definition_ids"] == list(DEFINITIONS)
    assert len(campaign["current_proof_family_packages"]) == 66
    assert campaign["current_proof_family_packages"]["polynomial-euclidean-division"] == "constructive-polynomial-euclidean-explorer-v33"
    assert audit["current_research_admission"]["ordinary_principal_count"] == 8
    assert audit["historical_parent_audit"]["record"] == old_audit
    old_defs = {row["id"]: row for row in old_graph["reviewed_definitions"]}
    new_defs = {row["id"]: row for row in graph["reviewed_definitions"]}
    assert len(new_defs) == 397 and {key: new_defs[key] for key in old_defs} == old_defs
    assert {key: new_defs[key]["name"] for key in set(new_defs) - set(old_defs)} == DEFINITIONS
    assert graph["reviewed_definition_edge_count"] == 865
    catalog = context.catalog if type(context.catalog) is dict else _thaw(context.catalog)
    checked = validate_campaign_dags(campaign, definition_graph=graph, catalog=catalog,
                                    catalog_sha256=context.catalog_sha256)
    assert (checked.theorem_count, checked.theorem_edge_count, checked.milestone_count) == (4092, 13212, 144)
    assert checked.milestone_dag_sha256 == old_audit["milestone_dag_sha256"]
    source = files["index.html"].decode()
    match = re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>', source, re.S)
    assert match and json.loads(match[1]) == campaign
    for path in ("/proofs/grand-campaign/", "/book/_static/constructive-research-campaign-v33/index.html"):
        observed = _notation_navigation(source, campaign, path)
        assert observed["hidden"] is False and len(observed["links"]) == 7
        assert all("v=" + context.revision in row["attrs"]["href"] for row in observed["links"])
    assert atlas.parent_files() == parents


def _assert_published_files(files, context):
    atlas.publication.require_live(context)
    _assert_published_content(files, context)
    atlas.publication.require_live(context)
