"""Canonical QR pages, exact local notation, and authenticated seven-goal maps."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_constructive_second_wave_explorer as builder
from constructive_second_wave_explorer_renderer import ASSET_DIGESTS


def test_exact_seven_named_targets_and_final_factory_counts():
    assert {family.milestones[-1] for family in builder.FAMILIES} == {"T13", "G011", "G095", "G035", "G027", "G051", "G107"}
    assert len({family.slug for family in builder.FAMILIES}) == len(builder.FAMILIES) == 7
    assert len({family.prefix for family in builder.FAMILIES}) == 7
    assert Counter(owner.campaign for owner, row in builder._factory_rows()) == {
        "matrix_determinants": 182, "hensel": 40, "generalized_crt": 24,
        "multinomial_kummer": 19, "chebyshev": 55, "cornacchia": 30, "cauchy_davenport": 72,
    }
    for family in builder.FAMILIES:
        names = {row.name for owner, row in builder._factory_rows() if owner.campaign == family.campaign}
        assert set(family.roots) <= names
        assert builder._family_definitions(family)
    multinomial = next(family for family in builder.FAMILIES if family.slug == "multinomial-kummer")
    assert any(item.stable_id == "PD0047" for item in builder._family_definitions(multinomial))


def test_original_quadratic_reciprocity_assets_are_byte_identical():
    for name, digest in ASSET_DIGESTS.items():
        assert sha256(builder.ASSET_SOURCES[name].read_bytes()).hexdigest() == digest
    assert builder.ASSET_SOURCES["proofs.css"] == ROOT / "deploy/proofs/proofs.css"


def test_duplicate_json_fields_and_non_objects_are_rejected():
    with pytest.raises(builder.SecondWaveExplorerError):
        builder._strict_json(b'{"checked_use":true,"checked_use":false}')
    with pytest.raises(builder.SecondWaveExplorerError):
        builder._strict_json(b'[]')


def test_atlas_table_preserves_all_reviewed_alias_names_and_argument_permutations():
    from extend_constructive_second_wave_campaign import _table_source

    graph = builder.build_definition_graph(json.loads(builder.CAMPAIGN.read_bytes()))
    aliases = [row for row in graph["compatible_reviewed_matches"] if row["reviewed_name"] != row["blueprint_name"]]
    assert len(aliases) == 5
    for row in aliases:
        rendered = _table_source("COMPILED_DEFINITIONS", [row], compatible=True)
        assert f'name: {json.dumps(row["reviewed_name"])}' in rendered
        positions = row["reviewed_argument_blueprint_positions"]
        if positions != list(range(len(positions))):
            assert f'argumentOrder: {json.dumps(positions)}' in rendered
    gcd = next(row for row in aliases if row["blueprint_name"] == "Gcd")
    assert gcd["reviewed_name"] == "IsGCD"
    assert gcd["reviewed_argument_blueprint_positions"] == [2, 0, 1]


@pytest.mark.parametrize("location", (
    "file:///research/book/_static/constructive-second-wave-explorer/hensel-lifting/explorer/defined/tag/HL0001.html",
    "http://localhost:8080/book/_static/constructive-second-wave-explorer/hensel-lifting/explorer/defined/tag/HL0001.html",
    "https://example.test/proofs/hensel-lifting/explorer/defined/tag/HL0001.html",
))
def test_portable_navigation_keeps_cache_keys_and_never_assigns_getter_only_href(location):
    links = ["../../../../grand-campaign/?view=goal&focus=G095&v=012345abcdef",
             "../../../../artifacts/alpha-v27-second-wave-proof-bundle-v1.json?v=012345abcdef",
             "../../../../artifacts/alpha-v27-second-wave-receipt.md?v=012345abcdef",
             "../graph.html?target=HL0001&v=012345abcdef", "#exact", "https://example.test/source"]
    source = builder.LOCAL_NAVIGATION.removeprefix("<script>").removesuffix("</script>")
    program = '''const vm=require("node:vm"), fs=require("node:fs");
const input=JSON.parse(fs.readFileSync(0,"utf8"));
const elements=input.links.map(value=>({value,get href(){return this.value;},
 getAttribute(name){return this.value;},setAttribute(name,value){this.value=value;}}));
vm.runInNewContext(input.source,{location:new URL(input.location),URL,
 document:{querySelectorAll(){return elements;}}});
process.stdout.write(JSON.stringify(elements.map(x=>x.value)));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"location": location, "links": links, "source": source}),
                            capture_output=True, text=True, timeout=20, check=True)
    actual = json.loads(result.stdout)
    if "/proofs/" in location:
        assert actual == links
    else:
        assert "/book/_static/constructive-grand-campaign/" in actual[0]
        assert actual[0].endswith("?view=goal&focus=G095&v=012345abcdef")
        assert "/research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json?" in actual[1]
        assert "/research/arithmetic-library/alpha-v27-second-wave-receipt.md?" in actual[2]
        assert actual[3:] == links[3:]


def test_portable_navigation_rejects_a_missing_or_duplicate_document_boundary():
    for source in (b"<body>", b"</body></body>"):
        with pytest.raises(builder.SecondWaveExplorerError):
            builder._portable_navigation(source)
    assert builder.LOCAL_NAVIGATION.encode() in builder._portable_navigation(b"<body></body>")


@pytest.fixture(scope="module")
def inputs():
    # This fixture is deliberately not a mocked authority receipt: all tests
    # below require the sealed full artifact to pass both actual verifiers.
    return builder._load_inputs()


@pytest.fixture(scope="module")
def files(inputs):
    return builder.build_files()


def test_exact_atlas_extension_is_idempotent_and_preserves_historical_partial_evidence(inputs):
    from extend_constructive_second_wave_campaign import extend_campaign, HISTORICAL_PARTIAL_SHA256

    assert extend_campaign(inputs["campaign"], inputs) == inputs["campaign"]
    goals = {node["id"]: node for node in inputs["campaign"]["nodes"]}
    for identifier, digest in HISTORICAL_PARTIAL_SHA256.items():
        historical = goals[identifier]["historical_partial_evidence"]
        assert sha256((json.dumps(historical, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()).hexdigest() == digest
        assert historical["checked_use"] is False
        assert goals[identifier]["evidence"]["checked_use"] is True
    assert inputs["campaign"]["ambitious_boundaries"]["second_wave_evidence_transition"]["broader_roadmap_bullets_automatically_closed"] is False


@pytest.mark.parametrize("field,value", (
    ("theorem_name", "zero_eq_zero"), ("theorem_statement_sha256", "0" * 64),
    ("bundle_node_id", 0), ("bundle_sha256", "0" * 64), ("alpha_version", "v26"),
    ("checked_use", False), ("stable_member", True), ("independent_lean_bundle_verified", False),
    ("full_arbitrary_determinant_proved", False), ("lattice_index_formula_proved", True),
))
def test_atlas_rejects_corrupted_or_overstated_milestone_authority(field, value, inputs):
    candidate = deepcopy(inputs["campaign"])
    next(row for row in candidate["nodes"] if row["id"] == "T13")["evidence"][field] = value
    graph = builder.build_definition_graph(candidate)
    with pytest.raises(ValueError):
        builder._audit_current_campaign(candidate, graph, inputs)


@pytest.mark.parametrize("identifier", ("T13", "G095", "G011"))
def test_atlas_rejects_rewriting_an_earlier_partial_receipt(identifier, inputs):
    candidate = deepcopy(inputs["campaign"])
    next(row for row in candidate["nodes"] if row["id"] == identifier)["historical_partial_evidence"]["checked_use"] = True
    graph = builder.build_definition_graph(candidate)
    with pytest.raises(ValueError, match="immutable partial evidence"):
        builder._audit_current_campaign(candidate, graph, inputs)


def test_atlas_rejects_a_reversed_definition_edge_or_stale_catalog_pin(inputs):
    graph = deepcopy(inputs["global_graph"])
    graph["reviewed_definition_edge_count"] += 1
    with pytest.raises(ValueError):
        builder._audit_current_campaign(inputs["campaign"], graph, inputs)
    campaign = deepcopy(inputs["campaign"])
    campaign["ambitious_boundaries"]["alpha_v27_edition"]["catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        builder._audit_current_campaign(campaign, builder.build_definition_graph(campaign), inputs)
    graph = deepcopy(inputs["global_graph"])
    graph["definition_page_overrides"]["PD0047"]["route"] = "missing-page"
    with pytest.raises(ValueError):
        builder._audit_current_campaign(inputs["campaign"], graph, inputs)


@pytest.mark.parametrize("name", ("SignedNonsingularHornerRoot", "BetaAt", "Factorial", "IsGCD", "Product"))
@pytest.mark.parametrize("field,value", (
    ("expansion", "0 = 0"), ("reviewed_definition_id", "PD0001"),
    ("reviewed_expansion_sha256", "0" * 64), ("exact_defined_expansion_equivalence_checked", False),
))
def test_existing_new_blueprint_definitions_are_reauthenticated_not_trusted(name, field, value, inputs):
    campaign = deepcopy(inputs["campaign"])
    campaign["definitions"][name][field] = value
    graph = builder.build_definition_graph(campaign)
    with pytest.raises(ValueError, match="exact introduced blueprint definition changed"):
        builder._audit_current_campaign(campaign, graph, inputs)


@pytest.mark.parametrize("location", ("catalog_digest", "catalog_path", "parent_identity", "channel_digest", "channel_path"))
def test_parent_release_chain_cannot_be_repointed(location):
    channels = json.loads(builder.CHANNELS.read_bytes())
    # Only this small metadata projection is needed; no proof/edition mock.
    parent = {
        "artifacts": deepcopy(builder.PARENT_ARTIFACTS), "schema": "peano-library-alpha-snapshot-v26",
        "theorem_count": builder.closure.PARENT_COUNT,
        "edition_identity_sha256": builder.closure.PARENT_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": builder.closure.PARENT_ENROLLMENT_SHA256,
    }
    catalog = {"parent_alpha_v26": parent}
    if location == "parent_identity":
        parent["edition_identity_sha256"] = "0" * 64
    elif location.startswith("catalog_"):
        parent["artifacts"]["catalog"]["sha256" if location.endswith("digest") else "path"] = "forged"
    else:
        channels["parent_channels_v26"]["sha256" if location.endswith("digest") else "path"] = "forged"
    with pytest.raises(ValueError, match="parent release chain"):
        builder._audit_parent_release_chain(catalog, channels)


def test_second_wave_overview_reuses_the_existing_library_layout(files):
    actual = Elements(files["index.html"])
    assert {"hero", "shell", "family-grid", "family-card", "stats", "primary-action"} <= actual.classes
    assert sum("family-card" in attrs.get("class", "").split() for tag, attrs in actual.attributes) == 7
    assert b"remain separate future work" in files["index.html"]


def test_unserved_historical_valuation_definition_has_an_exact_new_reference_page(files, inputs):
    override = inputs["global_graph"]["definition_page_overrides"]["PD0047"]
    assert override == {"name": "PrimePowerValuation", "route": "multinomial-kummer",
                        "registry_route": "bertrand-postulate", "proof_authority": False}
    original = next(row for row in inputs["global_graph"]["reviewed_definitions"] if row["id"] == "PD0047")
    assert original["route"] == "bertrand-postulate"
    page = files["multinomial-kummer/explorer/defined/definition/PD0047.html"]
    assert b"PrimePowerValuation" in page and original["expansion_sha256"].encode() in page


class Elements(HTMLParser):
    def __init__(self, data):
        super().__init__()
        self.classes, self.attributes, self.hrefs = set(), [], []
        self.feed(data.decode())

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        self.classes.update(values.get("class", "").split())
        self.attributes.append((tag, values))
        if "href" in values:
            self.hrefs.append(values["href"])


@pytest.mark.parametrize("family", builder.FAMILIES, ids=lambda family: family.slug)
def test_every_family_uses_the_actual_canonical_landing_model(family, files, inputs):
    actual = Elements(files[f"{family.slug}/index.html"])
    reference = Elements((ROOT / "deploy/proofs/quadratic-reciprocity.html").read_bytes())
    required = {"family-page", "family-hero", "shell", "family-main", "view-grid", "view-card", "featured", "release-note"}
    assert required <= actual.classes and required <= reference.classes
    assert "pa-defined-proof-site" not in actual.classes
    assert any("view=neighborhood&definitions=selected&edges=focus" in href for href in actual.hrefs)
    assert any("view=prerequisites&definitions=selected&edges=focus" in href for href in actual.hrefs)
    assert all(f"v={inputs['revision']}" in href for href in actual.hrefs if not href.startswith(("#", "https:")))
    for suffix in ("api/corpus.json", "explorer/index.html", "explorer/defined/index.html", "explorer/defined/graph.html", "explorer/defined/api/graph.json"):
        assert f"{family.slug}/{suffix}" in files


@pytest.mark.parametrize("family", builder.FAMILIES, ids=lambda family: family.slug)
def test_exact_rows_first_admission_and_all_tactic_lines_are_preserved(family, files, inputs):
    corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
    assert corpus["alpha_edition_version"] == corpus["alpha_first_enrolled_version"] == "v27"
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"]
    assert corpus["stable_admitted_node_count"] == 0
    for node in corpus["nodes"]:
        original = inputs["by_name"][node["name"]]
        assert node["statement"] == original["statement"]
        assert node["script"] == original["script"]
        assert node["dependencies"] == original["dependencies"]
        assert node["defined"]["exact_ast_equivalence"] is True
        assert len(node["defined"]["script_parts"]) == len(node["script"])
        assert ["".join(part["text"] for part in parts) for parts in node["defined"]["script_parts"]] == node["defined"]["defined_script"]
        for suffix in (f"explorer/tag/{node['id']}.html", f"explorer/defined/tag/{node['id']}.html"):
            assert f"{family.slug}/{suffix}" in files
    for definition in corpus["definitions"]:
        page = files[f"{family.slug}/explorer/defined/definition/{definition['id']}.html"]
        assert b"Definition in prerequisite notation" in page
        assert definition["exact_ast_verified"] is True


@pytest.mark.parametrize("family", builder.FAMILIES, ids=lambda family: family.slug)
def test_mixed_graph_has_three_distinct_edge_kinds_and_proof_only_paths(family, files):
    corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
    graph = json.loads(files[f"{family.slug}/explorer/defined/api/graph.json"])
    theorems = {node["id"] for node in corpus["nodes"]}
    definitions = {definition["id"] for definition in corpus["definitions"]}
    assert theorems.isdisjoint(definitions)
    assert graph["path_policy"] == corpus["path_policy"] == "proof_dependency_edges_only"
    assert {edge["kind"] for edge in graph["edges"]} == {"proof_dependency", "uses_definition", "definition_uses_definition"}
    proof_edges = set()
    for edge in graph["edges"]:
        if edge["kind"] == "proof_dependency":
            assert edge["source"] in theorems and edge["target"] in theorems
            proof_edges.add((edge["source"], edge["target"]))
        elif edge["kind"] == "uses_definition":
            assert edge["source"] in theorems and edge["target"] in definitions
            assert edge["occurrence_count"] == edge["statement_occurrences"] + edge["local_proposition_occurrences"]
        else:
            assert edge["source"] in definitions and edge["target"] in definitions
    for path in corpus["proof_paths"].values():
        assert set(path) <= theorems
        assert all(pair in proof_edges for pair in zip(path, path[1:]))
    page = Elements(files[f"{family.slug}/explorer/defined/graph.html"])
    assert {"pa-defined-proof-site", "pd-graph-controls", "pd-graph-workspace"} <= page.classes
    assert any(tag == "svg" and "data-graph-svg" in attrs for tag, attrs in page.attributes)
    assert any(tag == "a" and "data-graph-open" in attrs for tag, attrs in page.attributes)


def test_all_local_definition_links_are_in_the_family_dag(files):
    total_local_uses = 0
    for family in builder.FAMILIES:
        corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
        identifiers = {item["id"] for item in corpus["definitions"]}
        for node in corpus["nodes"]:
            uses = node["defined"]["definition_uses"]
            assert set(uses) <= identifiers
            total_local_uses += sum(node["defined"]["script_definition_uses"].values())
            page = files[f"{family.slug}/explorer/defined/tag/{node['id']}.html"]
            if node["defined"]["script_definition_uses"]:
                assert b"pd-definition-ref" in page and b"conservative notation" in page
    assert total_local_uses > 100


def test_sealed_manifest_and_all_snapshot_files_are_reproducible(files, inputs):
    manifest = json.loads(files["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 422
    assert manifest["catalog_sha256"] == inputs["catalog_sha256"]
    assert manifest["file_count"] == len(files) - 1
    assert len(manifest["families"]) == 7
    for record in manifest["files"]:
        payload = files[record["path"]]
        assert len(payload) == record["bytes"] and sha256(payload).hexdigest() == record["sha256"]
    assert manifest["inventory_sha256"] == sha256(builder._json(manifest["files"])).hexdigest()
    observed = {path.relative_to(builder.OUTPUT).as_posix() for path in builder.OUTPUT.rglob("*") if path.is_file()}
    assert observed == set(files)
    assert all((builder.OUTPUT / path).read_bytes() == payload for path, payload in files.items())
