"""Exact same-live Jordan publication tests; no saved receipt is a capability."""
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_jordan_publication_v35 as publication
import build_constructive_jordan_explorer_v35 as reader
import extend_constructive_jordan_campaign_v35 as atlas_builder


def _input(config, phase):
    value = getattr(config, "_alpha_v35_publication", None)
    assert type(value) is dict and value.get("phase") == phase, "a genuine same-live phase plugin is required"
    publication.require_live(value["context"])
    return value


def _read(actual, name):
    expected = actual["inventory"]["files"][name]
    path = actual["directory"] / name
    assert not path.is_symlink() and path.is_file()
    raw = path.read_bytes()
    assert len(raw) == expected["bytes"] and sha256(raw).hexdigest() == expected["sha256"]
    return raw


@pytest.fixture(scope="module")
def jordan(pytestconfig):
    return _input(pytestconfig, "jordan")


@pytest.fixture(scope="module")
def atlas(pytestconfig):
    return _input(pytestconfig, "atlas")


def test_jordan_live_inventory_and_exact_admission_boundary(jordan):
    context = jordan["context"]
    corpus = json.loads(_read(jordan, "jordan-totient/api/corpus.json"))
    reader._validate_data(context)
    assert corpus["alpha_catalog_sha256"] == context.catalog_sha256
    assert corpus["node_count"] == corpus["new_theorem_count"] == 95
    assert corpus["source_owned_theorem_count"] == 96
    assert corpus["source_aliases"] == dict(reader.ALIASES)
    assert corpus["alpha_edition_checked_use_count"] == 4318 and corpus["stable_edition_count"] == 432
    assert corpus["current_G091_prime_power_fields_proved"] is False
    assert corpus["jordan_prime_power_product_formula_proved"] is False
    assert len(json.loads(_read(jordan, "jordan-totient/api/first-admission.json"))) == 95
    assert len(corpus["checkpoint_report"]["principal_roots"]) == 7
    actual_paths = {path.relative_to(jordan["directory"]).as_posix()
                    for path in jordan["directory"].rglob("*") if path.is_file()}
    assert actual_paths == set(jordan["inventory"]["files"])
    for name in actual_paths:
        _read(jordan, name)


def test_jordan_exact_scripts_alias_provenance_and_paired_pages(jordan):
    corpus = json.loads(_read(jordan, "jordan-totient/api/corpus.json"))
    assert corpus["tags"] == reader.family_metadata()["tags"]
    for node, spec in zip(corpus["nodes"], reader.specs(), strict=True):
        assert node["name"] == spec.name and node["statement"] == spec.statement
        assert node["script"] == list(spec.script) and node["dependencies"] == list(spec.dependencies)
        assert node["script_sha256"] == sha256(("\n".join(spec.script) + "\n").encode()).hexdigest()
        tag = node["id"]
        exact = _read(jordan, f"jordan-totient/explorer/tag/{tag}.html").decode()
        defined = _read(jordan, f"jordan-totient/explorer/defined/tag/{tag}.html").decode()
        assert spec.statement in unescape(exact) and spec.statement in unescape(defined)
        assert 'data-campaign-link="family"' in exact and 'data-campaign-link="global"' in defined
        assert 'content="alpha-v35-checked-use"' in exact and 'content="alpha-v35-checked-use"' in defined
        assert len(node["defined"]["defined_script"]) == len(spec.script)
    alias = next(row for row in corpus["external_dependencies"] if row["name"] in reader.ALIASES)
    assert alias["canonical_admission_name"] == "integer_vector_equal_components_zero"
    assert alias["canonical_catalog_record"]["name"] == alias["canonical_admission_name"]
    assert alias["counted_as_new_owned_theorem"] is False and alias["first_admission_reclassified"] is False
    assert "jordan-totient/explorer/tag/JT0001.html" not in jordan["inventory"]["files"]


def test_jordan_canonical_graph_and_definition_dag(jordan):
    import constructive_historical_graph_test_support as graph_support
    corpus = json.loads(_read(jordan, "jordan-totient/api/corpus.json"))
    graph = json.loads(_read(jordan, "jordan-totient/api/graph.json"))
    assert graph == json.loads(_read(jordan, "jordan-totient/explorer/defined/api/graph.json"))
    assert corpus["path_policy"] == "proof_dependency_edges_only"
    assert set(row["kind"] for row in graph["edges"]) == {
        "proof_dependency", "uses_definition", "definition_uses_definition"}
    graph_support.assert_graph_views(graph)
    definitions = {row["id"]: row for row in corpus["definitions"]}
    assert {f"ND{i:04d}" for i in range(371, 382)} <= definitions.keys()
    assert "ND0121" in definitions and "ND0370" not in definitions
    visited = set()
    for row in corpus["definitions"]:
        assert set(row["dependencies"]) <= visited
        visited.add(row["id"])
        _read(jordan, "jordan-totient/explorer/defined/definition/" + row["id"] + ".html")
    landing = _read(jordan, "jordan-totient/index.html").decode()
    for marker in ('class="family-hero"', 'data-campaign-link="goal"', 'data-campaign-link="family"', 'data-campaign-link="domain"'):
        assert marker in landing
    assert "95" in landing and "96 source lemmas" in landing


def test_atlas_live_inventory_and_unchanged_campaign_contracts(atlas):
    context = atlas["context"]
    campaign = json.loads(_read(atlas, "campaign.json"))
    original = json.loads(atlas_builder.parent_files()["campaign.json"])
    atlas_builder._preserved(original, campaign)
    assert campaign["meta"]["current_alpha_version"] == "v35"
    assert campaign["meta"]["current_alpha_checked_use_count"] == 4318
    assert len(campaign["current_proof_family_packages"]) == 69
    g008 = next(row for row in campaign["nodes"] if row["id"] == "G008")
    g091 = next(row for row in campaign["nodes"] if row["id"] == "G091")
    assert g008["status"] == "alpha_closed" and g008["evidence"]["theorem_name"] == atlas_builder.ROOT_NAME
    assert g008["evidence"]["current_catalog_sha256"] == context.catalog_sha256
    assert g008["evidence"]["new_theorem_count"] == 95
    assert g008["evidence"]["source_owned_theorem_count"] == 96
    assert g008["evidence"]["distinct_prime_product_formula_proved"] is False
    assert g091["status"] == "open" and "evidence" not in g091
    for name in atlas["inventory"]["files"]:
        _read(atlas, name)


def test_atlas_conservative_definition_extension_and_real_routes(atlas):
    from sync_constructive_grand_campaign import validate_campaign_dags
    context = atlas["context"]
    campaign = json.loads(_read(atlas, "campaign.json"))
    graph = json.loads(_read(atlas, "definitions.json"))
    old = json.loads(atlas_builder.parent_files()["definitions.json"])
    old_defs = {row["id"]: row for row in old["reviewed_definitions"]}
    new_defs = {row["id"]: row for row in graph["reviewed_definitions"]}
    assert len(old_defs) == 407 and len(new_defs) == 418
    assert all(new_defs[name] == value for name, value in old_defs.items())
    match = next(row for row in graph["compatible_reviewed_matches"] if row["blueprint_name"] == "Jordan")
    assert match["reviewed_id"] == "ND0375" and match["reviewed_argument_blueprint_positions"] == [0, 1, 2]
    assert match["free_parameter_renaming"] == {"t": "j"}
    assert match["exact_renaming_ast_verified"] is True and match["blueprint_expansion_is_kernel_checked"] is False
    checked = validate_campaign_dags(campaign, definition_graph=graph,
        catalog=context.catalog, catalog_sha256=context.catalog_sha256)
    assert checked.theorem_count == 4318 and checked.reviewed_definition_count == 418
    html = _read(atlas, "index.html").decode()
    assert 'explorerBase("jordan-totient")' in html and 'full_G008_multiplicativity_proved === true' in html
    assert 'function renderNodeNotation(node)' in html
