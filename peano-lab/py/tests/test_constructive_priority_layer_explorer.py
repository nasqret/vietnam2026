"""Actual lower-layer proof evidence, canonical QR presentation, and DAG scope."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_constructive_priority_layer_explorer as builder
from constructive_checked_explorer_renderer import ASSET_DIGESTS
from constructive_priority_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from extend_constructive_priority_layer_campaign import extend_campaign, update_atlas_bindings
from extend_constructive_priority_layer_campaign import historical_campaign


def test_five_families_partition_four_major_targets_and_one_shared_tool():
    assert set(builder.MILESTONE_ROOTS) == {"G072", "G006", "G010", "G036"}
    assert len(builder.FAMILIES) == len({family.slug for family in builder.FAMILIES}) == 5
    assert len({family.prefix for family in builder.FAMILIES}) == 5
    assert Counter(goal for family in builder.FAMILIES for goal in family.milestones) == Counter((*builder.MILESTONE_ROOTS, "T09"))
    frontier = builder._factory_rows()
    selected = [row.name for family in builder.FAMILIES for _, row in builder._selected(family, frontier)]
    assert Counter(selected) == Counter(row.name for _, row in frontier)
    assert [len(builder._selected(family, frontier)) for family in builder.FAMILIES] == [20, 83, 84, 53, 38]
    for family in builder.FAMILIES:
        assert set(family.roots) <= {row.name for _, row in builder._selected(family, frontier)}


def test_original_quadratic_reciprocity_assets_and_shared_definitions_are_reused():
    for name, digest in ASSET_DIGESTS.items():
        assert sha256(builder.ASSET_SOURCES[name].read_bytes()).hexdigest() == digest
    first = {item.name: item for item in builder._family_definitions(builder.FAMILIES[2])}
    second = {item.name: item for item in builder._family_definitions(builder.FAMILIES[3])}
    for name in ("PrimeValuationSupport", "PowerValuation", "PrimeExponentEntries", "PrimeDivisorSupport"):
        assert first[name] is second[name] is DEFINITIONS[name]
    assert "Phi" not in second and "PowerProfile" not in first
    assert "Phi" not in DEFINITIONS["EulerProduct"].conceptual_dependencies
    assert "BestApproximationSecondKind" not in DEFINITIONS["Convergent"].conceptual_dependencies


@pytest.mark.parametrize("location", (
    "file:///research/book/_static/constructive-priority-layer-explorer/best-approximation/explorer/defined/tag/BA0001.html",
    "http://localhost:8080/book/_static/constructive-priority-layer-explorer/best-approximation/explorer/defined/tag/BA0001.html",
    "https://example.test/proofs/best-approximation/explorer/defined/tag/BA0001.html",
))
def test_portable_links_preserve_queries_and_support_getter_only_href(location):
    page = builder._portable_navigation(b"<body></body>", "constructive-priority-layer-explorer").decode()
    source = page.split("<script>", 1)[1].split("</script>", 1)[0]
    links = ["../../../../grand-campaign/?view=goal&focus=G072&v=012345abcdef",
             "../../../../artifacts/alpha-v29-priority-layer-proof-bundle-v1.json?v=012345abcdef",
             "../../../../artifacts/alpha-v29-priority-layer-receipt.md?v=012345abcdef",
             "../graph.html?target=BA0001&v=012345abcdef", "#exact", "https://example.test/source",
             "../../../../arithmetic-foundations/explorer/defined/tag/AF0001.html?v=012345abcdef",
             "../../../../integer-linear-algebra/explorer/defined/tag/DL0001.html?v=012345abcdef"]
    program = '''const vm=require("node:vm"),fs=require("node:fs");
const input=JSON.parse(fs.readFileSync(0,"utf8"));
const elements=input.links.map(value=>({value,get href(){return this.value;},
getAttribute(){return this.value;},setAttribute(name,value){this.value=value;}}));
vm.runInNewContext(input.source,{location:new URL(input.location),URL,document:{querySelectorAll(){return elements;}}});
process.stdout.write(JSON.stringify(elements.map(x=>x.value)));'''
    completed = subprocess.run(["node", "-e", program], input=json.dumps({"location": location, "links": links, "source": source}),
                               text=True, capture_output=True, timeout=20, check=True)
    actual = json.loads(completed.stdout)
    if "/proofs/" in location:
        assert actual == links
    else:
        assert actual[0].endswith("/book/_static/constructive-priority-campaign/?view=goal&focus=G072&v=012345abcdef")
        assert "/research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json?" in actual[1]
        assert "/research/arithmetic-library/alpha-v29-priority-layer-receipt.md?" in actual[2]
        assert actual[3].endswith("/best-approximation/explorer/defined/graph.html?target=BA0001&v=012345abcdef")
        assert actual[4:6] == links[4:6]
        assert "/constructive-lower-layer-explorer-v29/arithmetic-foundations/" in actual[6]
        assert "/constructive-second-wave-explorer-v29/integer-linear-algebra/" in actual[7]


@pytest.fixture(scope="module")
def inputs():
    # Real independently checked artifact, not a mocked Alpha authority receipt.
    return builder._load_inputs()


@pytest.fixture(scope="module")
def files(inputs):
    return builder.build_files()


def test_atlas_extension_preserves_unrelated_goals_and_refines_only_four_plans(inputs):
    campaign, old = inputs["campaign"], historical_campaign()
    assert extend_campaign(campaign, inputs) == campaign
    assert extend_campaign(old, inputs) == campaign
    nodes = {row["id"]: row for row in campaign["nodes"]}
    for previous in old["nodes"]:
        if previous["id"] not in builder.MILESTONE_ROOTS:
            assert nodes[previous["id"]] == previous
    for name in ("Factorization", "Permutation", "SquarefreeDecomposition", "Sum", "Prod"):
        assert campaign["definitions"][name] == old["definitions"][name]
    for name in ("Convergent", "Phi", "Squarefree", "PowerProfile"):
        assert campaign["historical_priority_layer_definition_plan"][name] == old["definitions"][name]
        assert campaign["definitions"][name]["exact_defined_expansion_equivalence_checked"] is True
    assert campaign["definitions"]["Convergent"]["reviewed_definition_id"] == "ND0205"
    assert "u,v>0" in old["definitions"]["Convergent"]["expansion"]
    assert nodes["G072"]["evidence"]["initial_zero_over_one_included"] is True
    assert nodes["G010"]["evidence"]["unit_uniform_profile"] is True
    for identifier in ("G082", "G083", "G085", "G086", "G091"):
        assert nodes[identifier]["status"] == "open"
    assert campaign["historical_lower_layer_definition_plan"] == old["historical_lower_layer_definition_plan"]
    assert campaign["meta"]["current_alpha_checked_use_count"] == 3042


@pytest.mark.parametrize("pathname,deployed", (("/proofs/grand-campaign/", True),
    ("/book/_static/constructive-priority-campaign/index.html", False),
    ("/local/research/book/_static/constructive-priority-campaign/index.html", False)))
def test_original_atlas_routes_and_revision_are_data_driven_and_idempotent(pathname, deployed, inputs):
    source = builder.CAMPAIGN.with_name("index.html").read_text()
    updated = update_atlas_bindings(source, inputs["campaign"])
    assert updated == source == update_atlas_bindings(updated, inputs["campaign"])
    functions = []
    for signature in (r"explorerBase\(route\)", r"proofHref\(path\)"):
        match = re.search(r"      function " + signature + r" \{.*?\n      \}", updated, re.S)
        assert match is not None
        functions.append(match.group(0))
    routes = [family.slug for family in builder.FAMILIES] + ["integer-linear-algebra", "cauchy-davenport"]
    program = '''const vm=require("node:vm"),fs=require("node:fs");
const input=JSON.parse(fs.readFileSync(0,"utf8"));
const context={window:{location:{pathname:input.pathname}},state:{campaign:input.campaign}};
vm.createContext(context);vm.runInContext(input.source,context);
process.stdout.write(JSON.stringify(input.routes.map(route=>context.proofHref(context.explorerBase(route)+"index.html"))));'''
    completed = subprocess.run(["node", "-e", program], input=json.dumps({
        "pathname": pathname, "routes": routes, "source": "\n".join(functions),
        "campaign": {"meta": inputs["campaign"]["meta"],
                     "ambitious_boundaries": {"alpha_v29_edition": {"catalog_sha256": inputs["catalog_sha256"]}}}}),
        text=True, capture_output=True, timeout=20, check=True)
    for route, href in zip(routes, json.loads(completed.stdout), strict=True):
        package = "constructive-priority-layer-explorer" if route in routes[:5] else "constructive-second-wave-explorer-v29"
        prefix = "../" if deployed else f"../{package}/"
        assert href == f"{prefix}{route}/explorer/defined/index.html?v={inputs['revision']}"


@pytest.mark.parametrize("mutation", ("duplicate", "missing", "both"))
def test_historical_local_routes_reject_ambiguous_or_missing_dispatch(mutation, inputs):
    source = builder.CAMPAIGN.with_name("index.html").read_text()
    current = 'return "../constructive-lower-layer-explorer-v29/" + route + "/explorer/defined/";'
    previous = 'return "../constructive-lower-layer-explorer/" + route + "/explorer/defined/";'
    assert source.count(current) == 1
    changed = {"duplicate": current + "\n" + current, "missing": "", "both": current + "\n" + previous}[mutation]
    with pytest.raises(ValueError, match="ambiguous historical local route dispatch"):
        update_atlas_bindings(source.replace(current, changed), inputs["campaign"])


@pytest.mark.parametrize("identifier,field,value", (
    ("G072", "initial_zero_over_one_included", False),
    ("G072", "approximation_premise_in_definition", True),
    ("G072", "signed_competitors_included", False),
    ("G006", "product_definition_independent_of_phi", False),
    ("G006", "supplied_factorization_premise", True),
    ("G010", "unit_uniform_profile", False),
    ("G010", "actual_root_table", False),
    ("G010", "polynomial_decomposition_claimed", True),
    ("G036", "odd_prime_guard_retained", False),
    ("G036", "binary_prime_variant_claimed", True),
    ("G036", "checked_use", 1), ("G036", "stable_member", True),
    ("G006", "theorem_statement_sha256", "0" * 64),
    ("G072", "bundle_node_id", -1), ("G010", "bundle_sha256", "0" * 64),
))
def test_atlas_rejects_corrupted_receipts_or_overstated_mathematics(identifier, field, value, inputs):
    campaign = deepcopy(inputs["campaign"])
    next(row for row in campaign["nodes"] if row["id"] == identifier)["evidence"][field] = value
    with pytest.raises(ValueError):
        builder._audit_current_campaign(campaign, builder.build_definition_graph(campaign), inputs)


@pytest.mark.parametrize("mutation", ("old_goal", "old_boundary", "old_definition", "new_definition", "old_plan", "definition_edge"))
def test_campaign_rejects_historical_or_conservative_definition_mutation(mutation, inputs):
    campaign, graph = deepcopy(inputs["campaign"]), deepcopy(inputs["global_graph"])
    if mutation == "old_goal":
        next(row for row in campaign["nodes"] if row["id"] == "G083")["status"] = "alpha_closed"
    elif mutation == "old_boundary":
        campaign["ambitious_boundaries"]["alpha_v27_edition"]["catalog_sha256"] = "0" * 64
    elif mutation == "old_definition":
        campaign["definitions"]["PrimeList"]["parameters"] = ["b", "c", "k"]
    elif mutation == "new_definition":
        campaign["definitions"]["Convergent"]["expansion"] = "0 = 0"
    elif mutation == "old_plan":
        campaign["historical_priority_layer_definition_plan"]["Phi"]["meaning"] = "changed"
    else:
        graph["reviewed_definition_edge_count"] += 1
    with pytest.raises(ValueError):
        builder._audit_current_campaign(campaign, graph, inputs)


@pytest.mark.parametrize("field,value", (
    ("statement_sha256", "0" * 64), ("script_sha256", "0" * 64),
    ("checked_use", False), ("checked_use", 1), ("body_checked", False),
    ("membership", "stable"), ("frontier_campaign", "other"),
))
def test_display_rejects_a_row_that_does_not_match_its_checked_source(field, value, inputs):
    candidate = dict(inputs)
    candidate["by_name"] = dict(inputs["by_name"])
    name = builder.MILESTONE_ROOTS["G072"]
    candidate["by_name"][name] = {**inputs["by_name"][name], field: value}
    with pytest.raises(ValueError):
        builder._family_corpus(builder.FAMILIES[1], candidate)


class Elements(HTMLParser):
    def __init__(self, payload):
        super().__init__()
        self.classes, self.attributes, self.hrefs = set(), [], []
        self.feed(payload.decode())

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        self.attributes.append((tag, attrs))
        self.classes.update(attrs.get("class", "").split())
        if "href" in attrs:
            self.hrefs.append(attrs["href"])


@pytest.mark.parametrize("family", builder.FAMILIES, ids=lambda item: item.slug)
def test_canonical_landing_exact_reader_and_defined_tree_are_complete(family, files, inputs):
    corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
    assert corpus["alpha_edition_version"] == corpus["alpha_first_enrolled_version"] == "v29"
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"]
    assert corpus["stable_admitted_node_count"] == 0
    landing = Elements(files[f"{family.slug}/index.html"])
    assert {"family-page", "family-hero", "view-grid", "view-card", "featured"} <= landing.classes
    assert all(f"v={inputs['revision']}" in href for href in landing.hrefs if not href.startswith(("#", "https:")))
    for node in corpus["nodes"]:
        row = inputs["by_name"][node["name"]]
        assert node["statement"] == row["statement"] and node["script"] == row["script"]
        assert node["dependencies"] == row["dependencies"]
        assert node["defined"]["exact_ast_equivalence"] is True
        assert len(node["defined"]["script_parts"]) == len(node["script"])
        for mode in ("explorer/tag", "explorer/defined/tag"):
            assert f"{family.slug}/{mode}/{node['id']}.html" in files
    for definition in corpus["definitions"]:
        assert f"{family.slug}/explorer/defined/definition/{definition['id']}.html" in files
        assert definition["exact_ast_verified"] is True


@pytest.mark.parametrize("family", builder.FAMILIES, ids=lambda item: item.slug)
def test_mixed_dag_keeps_notation_arrows_out_of_proof_paths(family, files):
    corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
    graph = json.loads(files[f"{family.slug}/explorer/defined/api/graph.json"])
    theorems, definitions = {row["id"] for row in corpus["nodes"]}, {row["id"] for row in corpus["definitions"]}
    assert theorems.isdisjoint(definitions)
    assert graph["path_policy"] == corpus["path_policy"] == "proof_dependency_edges_only"
    assert {edge["kind"] for edge in graph["edges"]} == {"proof_dependency", "uses_definition", "definition_uses_definition"}
    proof = set()
    for edge in graph["edges"]:
        if edge["kind"] == "proof_dependency":
            assert edge["source"] in theorems and edge["target"] in theorems
            proof.add((edge["source"], edge["target"]))
        elif edge["kind"] == "uses_definition":
            assert edge["source"] in theorems and edge["target"] in definitions
            assert edge["occurrence_count"] == edge["statement_occurrences"] + edge["local_proposition_occurrences"]
        else:
            assert edge["source"] in definitions and edge["target"] in definitions
    for path in corpus["proof_paths"].values():
        assert set(path) <= theorems and all(pair in proof for pair in zip(path, path[1:]))
    page = Elements(files[f"{family.slug}/explorer/defined/graph.html"])
    assert {"pa-defined-proof-site", "pd-graph-controls", "pd-graph-workspace"} <= page.classes
    assert any(tag == "a" and "data-graph-open" in attrs for tag, attrs in page.attributes)


@pytest.mark.parametrize("slug", ("totient-products", "squarefree-kernels"))
def test_shared_valuation_support_links_to_its_actual_proof(slug, files):
    corpus = json.loads(files[f"{slug}/api/corpus.json"])
    route = corpus["external_theorem_routes"]["prime_valuation_support_exists"]
    assert route.startswith("prime-valuation-support/explorer/defined/tag/PV")
    assert route in files
    users = [node for node in corpus["nodes"] if "prime_valuation_support_exists" in node["dependencies"]]
    assert users
    for node in users:
        page = Elements(files[f"{slug}/explorer/defined/tag/{node['id']}.html"])
        assert any(route in href for href in page.hrefs)


def test_exact_manifest_and_every_published_file_are_reproducible(files, inputs):
    manifest = json.loads(files["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == len(inputs["frontier"])
    assert manifest["catalog_sha256"] == manifest["first_enrollment_catalog_sha256"] == inputs["catalog_sha256"]
    assert manifest["file_count"] == len(files) - 1
    for record in manifest["files"]:
        data = files[record["path"]]
        assert len(data) == record["bytes"] and sha256(data).hexdigest() == record["sha256"]
    assert manifest["inventory_sha256"] == sha256(builder._json(manifest["files"])).hexdigest()
    actual = {path.relative_to(builder.OUTPUT).as_posix() for path in builder.OUTPUT.rglob("*") if path.is_file()}
    assert actual == set(files)
    assert all((builder.OUTPUT / name).read_bytes() == data for name, data in files.items())
