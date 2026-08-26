"""Read-only Alpha-v25 campaign, exact-proof, and conservative-DAG audit."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v24 as parent
from peano_lab.library import editions_v25 as current
from peano_lab.library.alpha_enrollment_v25 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FrontierV25Campaign,
    ROOT_STATEMENT_SHA256,
    alpha_v25_enrollment,
)


ROOT = Path(__file__).resolve().parents[3]
ATLAS = ROOT / "book/_static/constructive-grand-campaign"
EXPLORERS = ROOT / "book/_static/constructive-breakthrough-layer-explorer"
CATALOG = ROOT / "artifacts/peano-library/alpha/catalog-v25.json"
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v24.json"

FAMILIES = (
    (FrontierV25Campaign.MATRIX_COFACTOR_EXPANSION, "matrix-cofactor-expansion", "T13"),
    (FrontierV25Campaign.POLYNOMIAL_TAYLOR_HENSEL, "polynomial-taylor-hensel", "G095"),
    (
        FrontierV25Campaign.GENERALIZED_CRT_COMPATIBILITY,
        "generalized-crt-compatibility",
        "G011",
    ),
)

REVIEWED_IDENTITIES = {
    "Even": "PD0009",
    "Odd": "PD0010",
    "ModEq": "PD0008",
    "MatrixMinorFourCode": "ND0058",
    "SignedMinorRecord": "ND0059",
    "SignedCofactorMinorPrefix": "ND0060",
    "SignedAlternatingCofactorTerm": "ND0061",
    "SignedAlternatingProductPrefix": "ND0062",
    "SignedAlternatingCofactorFold": "ND0063",
    "SignedFirstRowCofactorFold": "ND0064",
    "HornerTaylorRemainder": "ND0065",
    "HenselCorrection": "ND0066",
    "CRTPairwiseCompatiblePrefix": "ND0067",
    "CRTMergeCompatiblePrefix": "ND0068",
}


@pytest.fixture(scope="module")
def catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def atlas() -> tuple[dict, dict]:
    return (
        json.loads((ATLAS / "campaign.json").read_text(encoding="utf-8")),
        json.loads((ATLAS / "definitions.json").read_text(encoding="utf-8")),
    )


def test_v24_parent_rows_and_immutable_historical_corpus_remain_exact(catalog: dict) -> None:
    historical = json.loads(PARENT.read_text(encoding="utf-8"))
    assert sha256(PARENT.read_bytes()).hexdigest() == (
        "94ac4d193cbfe8c2ec04e54024221bc2c3a534c0ae014d381663b86174b3dcc1"
    )
    assert catalog["theorems"][: len(historical["theorems"])] == historical["theorems"]
    assert len(parent.STABLE_SPECS) == len(current.STABLE_SPECS) == 432
    corpus = ROOT / "book/_static/pa-proof-explorer/api/corpus.json"
    assert sha256(corpus.read_bytes()).hexdigest() == (
        "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
    )


def test_global_definition_dag_adds_only_hygienic_reviewed_identities(atlas) -> None:
    campaign, graph = atlas
    assert graph["definition_count"] == len(campaign["definitions"]) == 179
    assert graph["definition_edge_count"] == 165
    assert graph["reviewed_definition_count"] == len(graph["reviewed_definitions"]) == 120
    assert graph["reviewed_definition_edge_count"] == 214
    assert graph["compatible_reviewed_match_count"] == 88
    assert graph["exact_name_reviewed_match_count"] == 83
    assert graph["explicit_alias_reviewed_match_count"] == 5
    beta_sum = next(
        match for match in graph["compatible_reviewed_matches"]
        if match["blueprint_name"] == "BetaSum"
    )
    assert beta_sum["reviewed_name"] == "Sum"
    assert beta_sum["reviewed_id"] == "PD0015"
    assert beta_sum["kind"] == "explicit-alias"
    identities = {row["name"]: row["id"] for row in graph["reviewed_definitions"]}
    assert all(identities[name] == identifier for name, identifier in REVIEWED_IDENTITIES.items())
    ordering = {name: index for index, name in enumerate(graph["topological_order"])}
    for edge in graph["definition_edges"]:
        assert edge["kind"] == "definition_uses_definition"
        assert ordering[edge["target"]] < ordering[edge["source"]]


@pytest.mark.parametrize("campaign,slug,milestone", FAMILIES)
def test_new_family_exposes_exact_and_definition_aware_proof_graphs(
    campaign: FrontierV25Campaign,
    slug: str,
    milestone: str,
    catalog: dict,
    atlas,
) -> None:
    campaign_json, _definitions = atlas
    corpus = json.loads((EXPLORERS / slug / "api/corpus.json").read_text(encoding="utf-8"))
    graph = json.loads(
        (EXPLORERS / slug / "explorer/defined/api/graph.json").read_text(encoding="utf-8")
    )
    assert corpus["family_slug"] == graph["family_slug"] == slug
    assert corpus["alpha_edition_version"] == graph["alpha_edition_version"] == "v25"
    assert corpus["alpha_first_enrolled_version"] == "v25"
    assert corpus["node_count"] == EXPECTED_CAMPAIGN_COUNTS[campaign]
    assert corpus["alpha_checked_use_node_count"] == corpus["node_count"]
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["alpha_catalog_sha256"] == sha256(CATALOG.read_bytes()).hexdigest()
    assert corpus["independent_lean_bundle_verified"] is True
    assert {edge["kind"] for edge in graph["edges"]} == {
        "proof_dependency",
        "uses_definition",
        "definition_uses_definition",
    }
    by_name = {row["name"]: row for row in catalog["theorems"]}
    enrollment = alpha_v25_enrollment()
    expected_names = {
        name for name, owner in enrollment.campaign_by_name.items() if owner is campaign
    }
    assert {node["name"] for node in corpus["nodes"]} == expected_names
    assert all(by_name[name]["checked_use"] for name in expected_names)
    node = next(item for item in campaign_json["nodes"] if item["id"] == milestone)
    assert node["status"] == "open"
    assert node["evidence"]["partial_component_checked_use"] is True
    assert node["evidence"]["alpha_version"] == "v25"


@pytest.mark.parametrize("name,expected", ROOT_STATEMENT_SHA256.items())
def test_exact_checked_root_statement_is_not_a_notation_edge(name: str, expected: str) -> None:
    row = current.ALPHA_EDITION.by_name[name]
    assert row.checked_use
    assert sha256(row.spec.statement.encode()).hexdigest() == expected
    assert all(dependency in current.ALPHA_EDITION.by_name for dependency in row.spec.dependencies)
