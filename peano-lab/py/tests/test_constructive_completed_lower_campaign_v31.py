"""Pure atlas/definition contracts; test fixtures grant no theorem authority."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import extend_constructive_completed_lower_campaign_v31 as atlas
import constructive_completed_lower_publication_v31 as publication
from constructive_dirichlet_inverse_definition_graph import build_definition_graph


@pytest.fixture(scope="module")
def inputs():
    parents = atlas.historical_files()
    original = publication.strict_json(parents["campaign.json"])
    manifests = {snapshot.directory: publication.snapshot_manifest(snapshot) for snapshot in publication.SNAPSHOTS}
    corpora = publication.frozen_corpora(manifests)
    families = publication.family_metadata(corpora)
    # A syntax-only projection fixture exercises the pure formatter. It is NOT
    # a LiveReleaseContext and cannot pass the public publication entrypoint.
    rows, reports = [], {}
    for family in families:
        corpus = corpora[family["slug"]]
        positions = {}
        for node in corpus["nodes"]:
            position = node["proof_bundle_node_id"]
            positions[node["name"]] = position
            rows.append({"name": node["name"], "statement": node["statement"], "summary": node["summary"],
                         "script": node["script"], "dependencies": node["dependencies"],
                         "statement_sha256": node["statement_sha256"],
                         "script_sha256": sha256(("\n".join(node["script"]) + "\n").encode()).hexdigest(),
                         "checked_use": True, "body_checked": True, "membership": "alpha_only",
                         "evidence_status": "alpha_closed", "empty_context_closure": {"bundle_node_id": position}})
        reports[family["slug"]] = {
            "new_theorem_count": family["theorem_count"], "owned_node_ids": positions,
            "bundle": {"nodes_including_packaging_root": corpus["proof_bundle_node_count"],
                       "dependency_edges_including_packaging": 1, "path": "syntax-only-fixture.json", "sha256": "a" * 64},
        }
    catalog = {"schema": "peano-library-alpha-snapshot-v31", "checked_use_count": 3796,
               "theorems": rows, "edge_count": 12248, "layer_count": 53,
               "ordered_enrollment_root_sha256": "b" * 64, "edition_identity_sha256": "c" * 64,
               "evidence_root_sha256": "d" * 64}
    return parents, original, catalog, families, corpora, reports


@pytest.fixture(scope="module")
def projected(inputs):
    parents, original, catalog, families, corpora, reports = inputs
    result = atlas._extend(original, catalog, families, corpora, reports, "e" * 64)
    graph = build_definition_graph(result)
    return result, graph


def test_literal_gaussian_parent_is_unchanged(inputs):
    parents, original, *_ = inputs
    for filename, data in parents.items():
        assert sha256(data).hexdigest() == atlas.PARENT_PINS[filename]
    assert len(original["nodes"]) == 144
    assert sum(node["kind"] == "goal" for node in original["nodes"]) == 120


def test_exact_mobius_contract_and_open_g009_are_distinct(projected, inputs):
    result, _ = projected
    _, original, _, families, corpora, _ = inputs
    nodes = {node["id"]: node for node in result["nodes"]}
    mobius = nodes["G007"]
    exact = next(node for node in corpora["mobius-inversion"]["nodes"] if node["name"] == atlas.G007_ROOT)
    assert mobius["status"] == "alpha_closed"
    assert mobius["statement"] == exact["defined"]["defined_statement"]
    assert mobius["evidence"]["theorem_statement_sha256"] == exact["statement_sha256"]
    assert mobius["evidence"]["proof_tag"] == "MI0006"
    assert mobius["evidence"]["checked_use"] is True
    assert mobius["evidence"]["stable_member"] is False
    assert mobius["evidence"]["multiplicative_closure_claimed"] is False
    assert nodes["G009"]["status"] == nodes["G091"]["status"] == "open"
    assert nodes["G009"]["evidence"]["checked_use"] is False
    assert nodes["G009"]["evidence"]["partial_component_checked_use"] is True
    assert nodes["G009"]["evidence"]["partial_theorem_name"] == "dirichlet_inverse_criterion"
    assert nodes["G009"]["remaining_obligations"] == list(atlas.G009_REMAINING)
    assert "+1 only" in nodes["G009"]["evidence"]["normalization_at_one_for_multiplicativity"]
    assert len(result["completed_lower_chapters"]) == 19
    assert sum(family["theorem_count"] for family in families) == 574
    assert result["meta"]["completed_lower_named_targets"] == ["G007", "G014"]
    euler = nodes["G014"]
    euler_exact = next(node for node in corpora["euler-units"]["nodes"] if node["name"] == atlas.G014_ROOT)
    assert euler["status"] == "alpha_closed"
    assert euler["statement"] == euler_exact["defined"]["defined_statement"]
    assert euler["evidence"]["theorem_statement_sha256"] == euler_exact["statement_sha256"]
    assert euler["evidence"]["proof_tag"] == "EU0020"
    assert euler["evidence"]["modulus_one_included"] is True
    assert euler["evidence"]["zero_modulus_excluded"] is True
    assert euler["evidence"]["checked_use"] is True
    old = {node["id"]: node for node in original["nodes"]}
    for identifier in set(nodes) - {"G007", "G009", "G014"}:
        assert {key: value for key, value in nodes[identifier].items() if key != "additional_checked_chapters"} == old[identifier]


def test_full_conservative_definition_graph_preserves_all_historical_vocabulary(projected, inputs):
    result, graph = projected
    original = inputs[1]
    assert all(result["definitions"][name] == value for name, value in original["definitions"].items())
    assert graph["reviewed_definition_count"] == 372
    assert graph["reviewed_definition_edge_count"] == 787
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert reviewed["SignedUnit"]["id"] == "ND0313"
    assert reviewed["DirichletUnitAtOne"]["id"] == "ND0314"
    assert reviewed["DirichletInverse"]["id"] == "ND0315"
    assert reviewed["DirichletUnitAtOne"]["dependencies"] == ["ArithAt"]
    assert "SignedUnit" not in reviewed["DirichletUnitAtOne"]["dependencies"]
    assert set(reviewed["DirichletInverse"]["dependencies"]) == {"KroneckerDeltaTable", "DirichletTable"}


@pytest.mark.parametrize("name", ("SignedUnit", "DirichletUnitAtOne", "DirichletInverse", "DivisorTransform", "ArithPositiveEqual"))
def test_actual_new_definition_records_round_trip_exactly(name):
    definition = atlas.DEFINITIONS[name]
    record = atlas._definition_record(definition)
    assert record["reviewed_definition_id"] == definition.stable_id
    assert record["parameters"] == list(definition.parameters)
    assert record["reviewed_expansion_sha256"] == sha256(definition.template_source.encode()).hexdigest()
    assert record["exact_defined_expansion_equivalence_checked"] is True


@pytest.mark.parametrize("change", ("parent_version", "parent_goal_count", "current_version", "current_count", "missing_family", "wrong_family_count", "unknown_goal", "missing_root", "closed_g009", "closed_g091"))
def test_campaign_projection_rejects_unreviewed_scope_and_completion_changes(inputs, change):
    _, original, catalog, families, corpora, reports = inputs
    original, catalog, families, reports = deepcopy(original), deepcopy(catalog), deepcopy(families), deepcopy(reports)
    if change == "parent_version":
        original["meta"]["current_alpha_version"] = "v29"
    elif change == "parent_goal_count":
        original["meta"]["goal_count"] = 121
    elif change == "current_version":
        catalog["schema"] = "peano-library-alpha-snapshot-v30"
    elif change == "current_count":
        catalog["checked_use_count"] = True
    elif change == "missing_family":
        families = families[:-1]
    elif change == "wrong_family_count":
        reports[families[0]["slug"]]["new_theorem_count"] += 1
    elif change == "unknown_goal":
        families[0]["goals"] = ["G999"]
    elif change == "missing_root":
        reports["mobius-inversion"]["owned_node_ids"].pop(atlas.G007_ROOT)
    else:
        target = "G009" if change == "closed_g009" else "G091"
        next(node for node in original["nodes"] if node["id"] == target)["status"] = "alpha_closed"
    with pytest.raises(publication.PublicationError):
        atlas._extend(original, catalog, families, corpora, reports, "e" * 64)


def test_public_atlas_builder_refuses_any_saved_or_syntax_only_context(inputs):
    with pytest.raises(publication.PublicationError, match="live"):
        atlas.build_files_from_live({"catalog": inputs[2], "success": True})


def test_original_interactive_atlas_has_current_routes_and_honest_partial_navigation(projected, inputs):
    result, graph = projected
    parents, _, _, families, _, _ = inputs
    payload = atlas._html(parents["index.html"].decode(), result, graph, families).decode()
    assert 'G007: { route: "mobius-inversion"' in payload
    assert 'tag: "MI0006"' in payload
    assert 'G014: { route: "euler-units"' in payload
    assert 'tag: "EU0020"' in payload
    assert 'var directory = currentFamilies[route] || "constructive-historical-explorers-v31";' in payload
    assert '"dirichlet-inverses": "constructive-completed-lower-explorer-v31"' in payload
    assert "Verified component — the full campaign remains open" in payload
    marker = '<script type="application/json" id="campaign-data">'
    embedded = json.loads(payload.split(marker, 1)[1].split("</script>", 1)[0])
    assert embedded == result
    assert 'state.campaign.ambitious_boundaries["alpha_" + metadata.current_alpha_version + "_edition"]' in payload


def test_atlas_does_not_embed_closing_script_tags(projected, inputs):
    result, graph = projected
    result = deepcopy(result)
    result["title"] = "</script><script>bad()</script>"
    with pytest.raises(publication.PublicationError, match="unsafe"):
        atlas._html(inputs[0]["index.html"].decode(), result, graph, inputs[3])
