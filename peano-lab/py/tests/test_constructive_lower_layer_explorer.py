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

import build_constructive_lower_layer_explorer as builder
from constructive_checked_explorer_renderer import ASSET_DIGESTS
from constructive_lower_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from extend_constructive_lower_layer_campaign import extend_campaign, update_atlas_bindings
from upgrade_constructive_second_wave_publication_v28 import historical_campaign


def test_four_families_partition_exactly_the_nine_named_targets():
    assert set(builder.MILESTONE_ROOTS) == {"G001", "G002", "G003", "G004", "G005", "G021", "G022", "G081", "G084"}
    assert len(builder.FAMILIES) == len({family.slug for family in builder.FAMILIES}) == 4
    assert len({family.prefix for family in builder.FAMILIES}) == 4
    assert Counter(goal for family in builder.FAMILIES for goal in family.milestones) == Counter(builder.MILESTONE_ROOTS.keys())
    frontier = builder._factory_rows()
    selected = [row.name for family in builder.FAMILIES for _, row in builder._selected(family, frontier)]
    assert Counter(selected) == Counter(row.name for _, row in frontier)
    foundations, primes = builder.FAMILIES[:2]
    assert len(builder._selected(foundations, frontier)) == 27
    assert len(builder._selected(primes, frontier)) == 19
    assert Counter(owner.campaign for owner, _ in frontier)["foundations"] == 28
    assert Counter(owner.campaign for owner, _ in frontier)["prime_enumeration"] == 18
    for family in builder.FAMILIES:
        assert set(family.roots) <= {row.name for _, row in builder._selected(family, frontier)}


def test_original_quadratic_reciprocity_assets_and_shared_definitions_are_reused():
    for name, digest in ASSET_DIGESTS.items():
        assert sha256(builder.ASSET_SOURCES[name].read_bytes()).hexdigest() == digest
    gaussian, eisenstein = builder.FAMILIES[-2:]
    first = {item.name: item for item in builder._family_definitions(gaussian)}
    second = {item.name: item for item in builder._family_definitions(eisenstein)}
    for name in ("ZPairDecode", "ZPairValid", "ZPairRep", "ZPairAdd", "SignedDecode"):
        assert first[name] is second[name] is DEFINITIONS[name]
    assert "ENorm" not in first and "GNorm" not in second


@pytest.mark.parametrize("location", (
    "file:///research/book/_static/constructive-lower-layer-explorer/gaussian-integers/explorer/defined/tag/GI0001.html",
    "http://localhost:8080/book/_static/constructive-lower-layer-explorer/gaussian-integers/explorer/defined/tag/GI0001.html",
    "https://example.test/proofs/gaussian-integers/explorer/defined/tag/GI0001.html",
))
def test_portable_links_preserve_queries_and_support_getter_only_href(location):
    page = builder._portable_navigation(b"<body></body>", "constructive-lower-layer-explorer").decode()
    source = page.split("<script>", 1)[1].split("</script>", 1)[0]
    links = ["../../../../grand-campaign/?view=goal&focus=G081&v=012345abcdef",
             "../../../../artifacts/alpha-v28-lower-layer-proof-bundle-v1.json?v=012345abcdef",
             "../../../../artifacts/alpha-v28-lower-layer-receipt.md?v=012345abcdef",
             "../graph.html?target=GI0001&v=012345abcdef", "#exact", "https://example.test/source"]
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
        assert actual[0].endswith("/book/_static/constructive-grand-campaign/?view=goal&focus=G081&v=012345abcdef")
        assert "/research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json?" in actual[1]
        assert "/research/arithmetic-library/alpha-v28-lower-layer-receipt.md?" in actual[2]
        assert actual[3:] == links[3:]


@pytest.fixture(scope="module")
def inputs():
    # Real independently checked artifact, not a mocked Alpha authority receipt.
    return builder._load_inputs()


@pytest.fixture(scope="module")
def files(inputs):
    return builder.build_files()


def test_atlas_extension_preserves_all_unrelated_goals_and_old_planning_signatures(inputs):
    campaign, old = inputs["campaign"], historical_campaign()
    assert extend_campaign(campaign, inputs) == campaign
    assert extend_campaign(old, inputs) == campaign
    nodes = {row["id"]: row for row in campaign["nodes"]}
    for previous in old["nodes"]:
        if previous["id"] not in builder.MILESTONE_ROOTS:
            assert nodes[previous["id"]] == previous
    for name in ("Factorization", "Permutation", "PrimeList", "Sum", "Prod"):
        assert campaign["definitions"][name] == old["definitions"][name]
    for name in ("GNorm", "ENorm"):
        assert campaign["historical_lower_layer_definition_plan"][name] == old["definitions"][name]
        assert campaign["definitions"][name]["exact_defined_expansion_equivalence_checked"] is True
    assert nodes["G022"]["historical_planned_layer"] == 5
    assert nodes["G022"]["layer"] == 6 and "A02" in nodes["G022"]["deps"]
    for identifier in ("G081", "G084"):
        assert "T13" not in nodes[identifier]["deps"]
        assert "T13" in nodes[identifier]["conceptual_refs"]
    for identifier in ("G006", "G082", "G083", "G085", "G086", "G091"):
        assert nodes[identifier]["status"] == "open"


@pytest.mark.parametrize("pathname,deployed", (("/proofs/grand-campaign/", True),
    ("/book/_static/constructive-grand-campaign/index.html", False),
    ("/local/research/book/_static/constructive-grand-campaign/index.html", False)))
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
                     "ambitious_boundaries": {"alpha_v28_edition": {"catalog_sha256": inputs["catalog_sha256"]}}}}),
        text=True, capture_output=True, timeout=20, check=True)
    for route, href in zip(routes, json.loads(completed.stdout), strict=True):
        package = "constructive-lower-layer-explorer" if route in routes[:4] else "constructive-second-wave-explorer-v28"
        prefix = "../" if deployed else f"../{package}/"
        assert href == f"{prefix}{route}/explorer/defined/index.html?v={inputs['revision']}"


@pytest.mark.parametrize("identifier,field,value", (
    ("G005", "actual_matching_bijection_proved", False),
    ("G005", "sortedness_premise", True),
    ("G022", "no_omission_proved", False),
    ("G022", "supplied_prime_list_premise", True),
    ("G081", "full_euclidean_division_proved", False),
    ("G084", "globally_nearest_quotient_claimed", True),
    ("G084", "unique_factorization_claimed", True),
    ("G002", "zero_zero_case_included", False),
    ("G081", "checked_use", 1), ("G081", "stable_member", True),
    ("G022", "theorem_statement_sha256", "0" * 64),
    ("G081", "bundle_node_id", -1), ("G084", "bundle_sha256", "0" * 64),
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
        campaign["definitions"]["GNorm"]["expansion"] = "0 = 0"
    elif mutation == "old_plan":
        campaign["historical_lower_layer_definition_plan"]["ENorm"]["meaning"] = "changed"
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
    name = builder.MILESTONE_ROOTS["G022"]
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
    assert corpus["alpha_edition_version"] == corpus["alpha_first_enrolled_version"] == "v28"
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


def test_eisenstein_shared_prerequisites_link_to_their_actual_gaussian_proofs(files):
    corpus = json.loads(files["eisenstein-integers/api/corpus.json"])
    route = corpus["external_theorem_routes"]["gaussian_representation_exists"]
    assert route.startswith("gaussian-integers/explorer/defined/tag/GI")
    assert route in files
    users = [node for node in corpus["nodes"] if "gaussian_representation_exists" in node["dependencies"]]
    assert users
    for node in users:
        page = Elements(files[f"eisenstein-integers/explorer/defined/tag/{node['id']}.html"])
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
