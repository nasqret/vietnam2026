"""Exact proof, definition, and public-map audit of completed first-wave goals."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import editions_v25 as parent
from peano_lab.library import editions_v26 as first_admission
from peano_lab.library import editions_v28 as current
from peano_lab.library.alpha_enrollment_v26 import ROOT_STATEMENT_SHA256, alpha_v26_enrollment
from peano_lab.library.pythagorean_fermat_four_candidate import make_pythagorean_fermat_four_candidate_theorems
from peano_lab.library.pythagorean_primitive_candidate import make_pythagorean_primitive_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from constructive_first_wave_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    FIRST_WAVE_DEFINITIONS,
    HISTORICAL_DEFINITIONS_BY_NAME,
)


ATLAS = ROOT / "book/_static/constructive-grand-campaign"
EXPLORER = ROOT / "book/_static/constructive-frontier-explorer/pythagorean-fermat-four"
CATALOG = ROOT / "artifacts/peano-library/alpha/catalog-v26.json"
CURRENT_CATALOG = ROOT / "artifacts/peano-library/alpha/catalog-v28.json"
PARENT_CATALOG = ROOT / "artifacts/peano-library/alpha/catalog-v25.json"
CATALOG_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
CURRENT_CATALOG_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"
PARENT_SHA256 = "75fa146ac19bf6aa5f799265b6fc031b725c1e1b2e044854da91b31898d5876e"
BUNDLE_SHA256 = "59afca707b33b68df907c941683e335492f7de12ee3888219339c5dfce8ec4fc"

DEFINITION_IDENTITIES = {
    "Pythagorean": "CF0011",
    "PrimitivePythagorean": "CF0013",
    "FermatFourCounterexample": "CF0014",
    "FermatFourStrictDescent": "CF0015",
    "OppositeParity": "CF0016",
    "PrimitiveTriple": "ND0069",
    "EuclidParameters": "ND0070",
    "PrimitiveFermatFourCounterexample": "ND0071",
    "SmallerFermatFourCounterexample": "ND0072",
    "TrivialFermatFourSolution": "ND0073",
    "EuclidParametrization": "ND0074",
}


@pytest.fixture(scope="module")
def surfaces() -> dict[str, dict]:
    return {
        "catalog": json.loads(CATALOG.read_text()),
        "current_catalog": json.loads(CURRENT_CATALOG.read_text()),
        "parent": json.loads(PARENT_CATALOG.read_text()),
        "campaign": json.loads((ATLAS / "campaign.json").read_text()),
        "definitions": json.loads((ATLAS / "definitions.json").read_text()),
        "corpus": json.loads((EXPLORER / "api/corpus.json").read_text()),
        "graph": json.loads((EXPLORER / "explorer/defined/api/graph.json").read_text()),
    }


def _tag(index: int) -> str:
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    encoded = ""
    while index:
        index, digit = divmod(index, 36)
        encoded = digits[digit] + encoded
    return "PF" + encoded.rjust(4, "0")


def test_v26_adds_exactly_fifty_eight_rows_and_preserves_every_v25_evidence_record(surfaces) -> None:
    catalog, historical = surfaces["catalog"], surfaces["parent"]
    assert sha256(CATALOG.read_bytes()).hexdigest() == CATALOG_SHA256
    assert sha256(PARENT_CATALOG.read_bytes()).hexdigest() == PARENT_SHA256
    assert len(catalog["theorems"]) == 2_138
    assert len(historical["theorems"]) == 2_080
    assert catalog["theorems"][:2_080] == historical["theorems"]
    inherited_evidence = {row["path"]: row for row in historical["evidence_documents"]}
    evidence = {row["path"]: row for row in catalog["evidence_documents"]}
    assert len(inherited_evidence) == 512
    assert all(evidence[path] == row for path, row in inherited_evidence.items())
    assert first_admission.STABLE_EDITION is parent.STABLE_EDITION
    assert len(first_admission.STABLE_SPECS) == 432
    assert current.STABLE_EDITION is first_admission.STABLE_EDITION
    assert len(current.STABLE_SPECS) == 432
    assert sha256(CURRENT_CATALOG.read_bytes()).hexdigest() == CURRENT_CATALOG_SHA256
    assert surfaces["current_catalog"]["theorems"][:2_138] == catalog["theorems"]
    assert all(new is old for new, old in zip(current.ALPHA_ENTRIES, first_admission.ALPHA_ENTRIES))
    assert sha256((ROOT / "book/_static/pa-proof-explorer/api/corpus.json").read_bytes()).hexdigest() == (
        "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
    )


def test_existing_forty_four_pythagorean_tags_are_preserved_before_the_new_append(surfaces) -> None:
    corpus, graph = surfaces["corpus"], surfaces["graph"]
    historical = (
        *make_pythagorean_fermat_four_candidate_theorems(TheoremSpec),
        *make_pythagorean_primitive_candidate_theorems(TheoremSpec),
    )
    expected_names = [row.name for row in historical] + list(first_admission.FRONTIER_NEW_NAMES)
    assert len(historical) == 44
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == 102
    assert [row["name"] for row in corpus["nodes"]] == expected_names
    by_name = {row["name"]: row for row in graph["nodes"] if row["kind"] == "theorem"}
    assert {name: by_name[name]["tag"] for name in expected_names} == {
        name: _tag(index) for index, name in enumerate(expected_names)
    }
    assert Counter(row["alpha_admission_version"] for row in corpus["nodes"]) == {"v19": 44, "v26": 58}
    for old, published in zip(historical, corpus["nodes"]):
        assert published["statement"] == old.statement
        assert published["dependencies"] == list(old.dependencies)
        assert published["script"] == list(old.script)
    assert graph["alpha_edition_version"] == corpus["alpha_edition_version"] == "v28"
    assert corpus["alpha_catalog_sha256"] == graph["alpha_catalog_sha256"] == CURRENT_CATALOG_SHA256


@pytest.mark.parametrize("name,expected", tuple(ROOT_STATEMENT_SHA256.items()))
def test_every_new_major_root_displays_the_exact_admitted_proof_and_real_dependency_cone(surfaces, name: str, expected: str) -> None:
    corpus = {row["name"]: row for row in surfaces["corpus"]["nodes"]}
    catalog = {row["name"]: row for row in surfaces["catalog"]["theorems"]}
    published, admitted = corpus[name], catalog[name]
    assert published["alpha_checked_use"] is admitted["checked_use"] is True
    assert published["statement_sha256"] == admitted["statement_sha256"] == expected
    assert published["statement"] == admitted["statement"]
    assert published["script"] == admitted["script"]
    assert published["dependencies"] == admitted["dependencies"]
    assert published["alpha_admission_version"] == "v26"
    closure = admitted["empty_context_closure"]
    assert closure["certificate_sha256"] == BUNDLE_SHA256
    assert closure["bundle_node_count"] == 216
    assert closure["bundle_dependency_edge_count"] == 558
    assert closure["bundle_root_id"] == 215
    assert closure["bundle_node_id"] < 215
    assert closure["kernel_mode"] == "intuitionistic"
    assert closure["status"] == "checked"


def test_first_wave_registry_shares_existing_definitions_and_preserves_historical_identities(surfaces) -> None:
    assert len(HISTORICAL_DEFINITIONS_BY_NAME) == 120
    assert len(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME) == 131
    assert all(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name] is definition for name, definition in HISTORICAL_DEFINITIONS_BY_NAME.items())
    assert {definition.name: definition.stable_id for definition in FIRST_WAVE_DEFINITIONS} == DEFINITION_IDENTITIES
    reviewed = {row["name"]: row for row in surfaces["definitions"]["reviewed_definitions"]}
    local = {row["name"]: row for row in surfaces["corpus"]["definitions"]}
    from constructive_lower_layer_definition_graph import build_definition_graph

    assert surfaces["definitions"] == build_definition_graph(surfaces["campaign"])
    for definition in FIRST_WAVE_DEFINITIONS:
        assert reviewed[definition.name]["id"] == local[definition.name]["id"] == definition.stable_id
        assert local[definition.name]["dependency_names"] == list(definition.conceptual_dependencies)
        assert parse_formula_in_context(local[definition.name]["expanded_template"], list(definition.parameters)) == definition.template_formula


def test_new_theorem_statements_actually_use_the_new_conservative_definitions(surfaces) -> None:
    nodes = {row["name"]: row for row in surfaces["corpus"]["nodes"]}
    expected_uses = {
        "pythagorean_positive_primitive_classification": {"ND0069", "ND0074"},
        "pythagorean_primitive_odd_even_inverse": {"CF0013", "ND0070"},
        "fermat_four_strict_descent_proved": {"CF0015"},
        "fermat_four_complete_classification": {"ND0073"},
    }
    for name, identifiers in expected_uses.items():
        defined = nodes[name]["defined"]
        assert defined["statement_status"] == "exact-ast-equivalent"
        assert identifiers <= set(defined["statement_definition_uses"])
        assert defined["statement_receipt"]["exact_ast_equivalence"] is True
        assert defined["statement_receipt"]["free_names"] == []
        assert defined["expanded_statement_sha256"] == nodes[name]["statement_sha256"]


def test_mixed_graph_keeps_proof_paths_separate_from_definition_arrows(surfaces) -> None:
    graph = surfaces["graph"]
    nodes = {row["id"]: row for row in graph["nodes"]}
    kinds = Counter(edge["kind"] for edge in graph["edges"])
    assert set(kinds) == {"proof_dependency", "uses_definition", "definition_uses_definition"}
    assert graph["path_policy"] == "proof_dependency_edges_only"
    proof_pairs = {(edge["source"], edge["target"]) for edge in graph["edges"] if edge["kind"] == "proof_dependency"}
    for edge in graph["edges"]:
        source, target = nodes[edge["source"]], nodes[edge["target"]]
        if edge["kind"] == "proof_dependency":
            assert source["kind"] == target["kind"] == "theorem"
            assert source["layer"] < target["layer"]
        elif edge["kind"] == "uses_definition":
            assert source["kind"] == "theorem" and target["kind"] == "definition"
        else:
            assert source["kind"] == target["kind"] == "definition"
    for record in graph["proof_adjacency"].values():
        path = record["critical_root_path"]
        assert all(pair in proof_pairs for pair in zip(path, path[1:]))


@pytest.mark.parametrize("identifier,theorem_name,node_id", (
    ("G077", "pythagorean_positive_primitive_classification", 188),
    ("G078", "fermat_four_positive_sum_not_square", 214),
))
def test_closed_first_wave_goals_bind_full_statements_and_navigate_to_their_exact_proofs(surfaces, identifier: str, theorem_name: str, node_id: int) -> None:
    milestone = next(row for row in surfaces["campaign"]["nodes"] if row["id"] == identifier)
    assert milestone["status"] == "alpha_closed"
    evidence = milestone["evidence"]
    assert evidence["theorem_name"] == theorem_name
    assert evidence["theorem_statement_sha256"] == ROOT_STATEMENT_SHA256[theorem_name]
    assert evidence["alpha_version"] == "v26"
    assert evidence["checked_use"] is True and evidence["stable_member"] is False
    assert evidence["full_empty_context_closure"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert evidence["bundle_sha256"] == BUNDLE_SHA256
    assert evidence["bundle_node_id"] == node_id
    node = next(row for row in surfaces["graph"]["nodes"] if row["name"] == theorem_name)
    tag = node["tag"]
    for relative in (f"explorer/tag/{tag}.html", f"explorer/defined/tag/{tag}.html"):
        page = (EXPLORER / relative).read_text()
        assert evidence["theorem_statement_sha256"] in page
        assert "pa-" in page
    atlas = (ATLAS / "index.html").read_text()
    assert f'{identifier}: {{ route: "pythagorean-fermat-four"' in atlas
    assert f'tag: "{tag}"' in atlas


def test_separate_second_wave_closure_keeps_historical_partial_and_forward_evidence(surfaces) -> None:
    nodes = {row["id"]: row for row in surfaces["campaign"]["nodes"]}
    for identifier in ("T13", "G095", "G011"):
        assert nodes[identifier]["status"] == "alpha_closed"
        assert nodes[identifier]["evidence"]["checked_use"] is True
        assert nodes[identifier]["evidence"]["alpha_version"] == "v27"
        assert nodes[identifier]["historical_partial_evidence"]["checked_use"] is False
        assert nodes[identifier]["historical_partial_evidence"]["alpha_version"] == "v25"
    forward = nodes["A08"]["evidence"]
    assert forward["alpha_version"] == "v19"
    assert forward["inverse_parametrization_complete"] is False
    assert forward["fermat_four_descent_complete"] is False
    assert forward["new_theorem_count"] == 44
    assert set(alpha_v26_enrollment().campaign_by_name.values()) == {
        "coprime_square_factor", "pythagorean_inverse", "fermat_four_descent",
    }


def test_complete_pythagorean_branch_retains_the_canonical_quadratic_reciprocity_design(surfaces) -> None:
    landing = (EXPLORER / "index.html").read_text()
    for anchor in ('class="family-page pythagorean-fermat-four-page"', 'class="family-hero"', 'class="view-grid"', 'class="view-card featured"', 'class="release-note"'):
        assert anchor in landing
    assert f"v={CURRENT_CATALOG_SHA256[:12]}" in landing
    assert "remain unproved" not in landing and "remain open" not in landing
    assert surfaces["corpus"]["campaign_goal_id"] == "G078"
    shared = EXPLORER.parent / "assets"
    for filename, reference in (("defined-explorer.js", "explorer.js"), ("defined-explorer.css", "explorer.css")):
        original = ROOT / "book/_static/pa-proof-explorer/defined/assets" / reference
        assert (shared / filename).read_bytes() == original.read_bytes()
