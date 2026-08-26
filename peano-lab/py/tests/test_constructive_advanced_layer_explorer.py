"""Current Alpha-v25 explorers preserve three frozen Alpha-v21 proof campaigns."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import html
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_constructive_advanced_layer_explorer as explorer  # noqa: E402
from constructive_advanced_layer_definitions import (  # noqa: E402
    ADVANCED_LAYER_DEFINITIONS,
    ADVANCED_LAYER_DEFINITIONS_BY_NAME,
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS_BY_NAME,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.kernel.terms import ParseError  # noqa: E402


EXPECTED = {
    "matrix-coded-products": (23, "D05", "F12", "T13"),
    "euclidean-complexity": (15, "D04", "F11", "G101"),
    "binary-modular-exponentiation": (16, "D04", "F11", "G102"),
}
EXPECTED_ROOT_TAGS = {
    ("matrix-coded-products", "beta_matrix_product_exists"): "MC000B",
    ("matrix-coded-products", "beta_signed_matrix_product_exists"): "MC000E",
    ("matrix-coded-products", "beta_signed_dot_product_exists_unique"): "MC0013",
    ("matrix-coded-products", "signed_matrix_three_full_determinant_exists"): "MC0016",
    ("euclidean-complexity", "euclidean_two_step_halving"): "EC0006",
    ("euclidean-complexity", "euclidean_execution_exists"): "EC000D",
    ("euclidean-complexity", "euclidean_gcd_execution_linear_bound"): "EC000F",
    (
        "binary-modular-exponentiation",
        "binary_modular_exponentiation_result_exists_unique",
    ): "BX0010",
}


@pytest.fixture(scope="module")
def inputs() -> dict:
    return explorer._load_inputs()


@pytest.fixture(scope="module")
def generated() -> dict[str, bytes]:
    return explorer.build_files()


@pytest.fixture(scope="module")
def corpora(generated: dict[str, bytes]) -> dict[str, dict]:
    return {
        slug: json.loads(generated[f"{slug}/api/corpus.json"])
        for slug in EXPECTED
    }


def test_manifest_binds_current_v24_and_independently_verified_first_admission_v21(
    generated: dict[str, bytes], inputs: dict
) -> None:
    manifest = json.loads(generated["manifest.json"])
    digest = sha256(explorer.CURRENT_CATALOG.read_bytes()).hexdigest()
    historical_digest = sha256(explorer.CATALOG.read_bytes()).hexdigest()
    assert manifest["schema"] == "peano-lab-constructive-advanced-layer-explorer-v1-manifest"
    assert manifest["catalog_sha256"] == digest
    assert manifest["first_enrollment_catalog_sha256"] == historical_digest
    assert manifest["html_revision"] == digest[:12]
    assert manifest["edition_identity_sha256"] == inputs["current_edition_identity_sha256"]
    assert manifest["alpha_edition_version"] == "v25"
    assert manifest["alpha_first_enrolled_version"] == "v21"
    assert manifest["proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert manifest["proof_bundle_node_count"] == 209
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 54
    assert manifest["stable_count"] == 0
    assert manifest["file_count"] + 1 == len(generated)
    assert {item["slug"]: item["theorem_count"] for item in manifest["families"]} == {
        slug: info[0] for slug, info in EXPECTED.items()
    }
    for item in manifest["files"]:
        payload = generated[item["path"]]
        assert item["bytes"] == len(payload)
        assert item["sha256"] == sha256(payload).hexdigest()


def test_immutable_original_quadratic_explorer_assets_are_reused_byte_for_byte(
    generated: dict[str, bytes]
) -> None:
    for name, source in explorer.ASSET_SOURCES.items():
        payload = generated[f"assets/{name}"]
        assert payload == source.read_bytes()
        if name in explorer.PINNED_ASSETS:
            assert sha256(payload).hexdigest() == explorer.PINNED_ASSETS[name]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_historical_v21_family_landing_reuses_quadratic_reciprocity_structure(
    slug: str,
    generated: dict[str, bytes],
    corpora: dict[str, dict],
) -> None:
    corpus = corpora[slug]
    family = next(item for item in explorer.FAMILIES if item.slug == slug)
    source = generated[f"{slug}/index.html"].decode()
    reference = (ROOT / "deploy/proofs/quadratic-reciprocity.html").read_text()
    revision = corpus["alpha_catalog_sha256"][:12]

    for marker in (
        '<header class="family-hero">',
        '<nav class="crumbs">',
        '<div class="hero-actions">',
        '<main class="shell family-main">',
        '<section class="view-grid">',
        '<article class="view-card featured">',
        '<section class="release-note">',
    ):
        assert marker in reference
        assert marker in source
    assert f'<body class="family-page {slug}-page">' in source
    assert 'class="proof-hero"' not in source
    assert source.count('<article class="view-card') == 3
    assert f'href="../assets/proofs.css?v={revision}"' in source
    assert "Alpha v25 checked-use theorem family" in source
    assert "first admitted v21" in source
    assert "independently accept all 209 bundle nodes" in source
    assert corpus["alpha_proof_bundle_sha256"] in source
    assert family.caveat in html.unescape(source)
    for root in family.roots:
        tag = corpus["tags"][root]
        assert f'explorer/defined/tag/{tag}.html?v={revision}' in source


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_family_boundaries_exact_release_rows_and_honest_open_milestones(
    slug: str, corpora: dict[str, dict], inputs: dict
) -> None:
    corpus = corpora[slug]
    count, domain, family, milestone = EXPECTED[slug]
    assert corpus["node_count"] == count
    assert corpus["alpha_checked_use_node_count"] == count
    assert corpus["alpha_enrolled_node_count"] == count
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["campaign_domain_id"] == domain
    assert corpus["campaign_family_id"] == family
    assert corpus["campaign_goal_id"] == milestone
    assert corpus["campaign_milestone_ids"] == [milestone]
    assert corpus["milestone_status"] == ("open" if milestone == "T13" else "alpha_closed")
    assert corpus["milestone_checked_use"] is (milestone != "T13")
    assert corpus["alpha_edition_version"] == "v25"
    assert corpus["alpha_first_enrolled_version"] == "v21"
    assert corpus["alpha_first_enrollment_catalog_sha256"] == inputs[
        "historical_catalog_sha256"
    ]
    assert corpus["alpha_proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert corpus["independent_lean_bundle_verified"] is True
    for node in corpus["nodes"]:
        sealed = inputs["by_name"][node["name"]]
        closure = sealed["empty_context_closure"]
        assert node["statement"] == sealed["statement"]
        assert node["statement_sha256"] == sealed["statement_sha256"]
        assert node["script"] == sealed["script"]
        assert node["dependencies"] == sealed["dependencies"]
        assert node["proof_bundle_node_id"] == closure["bundle_node_id"]
        assert node["proof_bundle_sha256"] == closure["certificate_sha256"]
        assert node["body_proof_nodes"] == closure["body_proof_nodes"]
        assert node["body_proof_depth"] == closure["body_proof_depth"]
        assert node["sources"][0]["script_sha256"] == sealed["script_sha256"]
        assert node["alpha_checked_use"] is True
        assert node["alpha_edition_version"] == "v25"
        assert node["alpha_first_enrolled_version"] == "v21"
        assert node["independent_lean_bundle_verified"] is True
        assert node["stable_member"] is False
        assert node["campaign_milestone"] == milestone


@pytest.mark.parametrize(("key", "tag"), EXPECTED_ROOT_TAGS.items())
def test_major_campaign_root_tags_are_pinned_to_exact_original_theorem_order(
    key: tuple[str, str], tag: str, corpora: dict[str, dict]
) -> None:
    slug, theorem = key
    corpus = corpora[slug]
    assert corpus["tags"][theorem] == tag
    assert theorem in corpus["root_names"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_local_definition_dags_are_hygienic_shared_dependency_first_and_exact(
    slug: str, corpora: dict[str, dict], inputs: dict
) -> None:
    corpus = corpora[slug]
    records = {item["id"]: item for item in corpus["definitions"]}
    assert len(records) == corpus["definition_count"]
    assert corpus["definition_topological_order"] == list(records)
    reviewed = {
        item["name"]: item for item in inputs["global_graph"]["reviewed_definitions"]
    }
    available: set[str] = set()
    for item in corpus["definitions"]:
        assert set(item["dependencies"]) <= available
        assert item["arity"] == len(item["parameters"])
        assert item["expansion_sha256"] == sha256(
            item["expanded_template"].encode()
        ).hexdigest()
        assert item["exact_ast_verified"] is True
        assert item["kernel_signature_unchanged"] is True
        assert parse_formula_in_context(
            item["expanded_template"], list(item["parameters"])
        ) == explorer._definition_specs()[item["name"]].template_formula
        if item["id"].startswith("ND"):
            actual = (
                ADVANCED_LAYER_DEFINITIONS_BY_NAME.get(item["name"])
                or NEXT_LAYER_DEFINITIONS_BY_NAME.get(item["name"])
            )
            assert actual is explorer._definition_specs()[item["name"]]
            assert item["shared_definition_identity"] == item["id"]
            assert reviewed[item["name"]]["id"] == item["id"]
            assert item["reviewed_definition_id"] == (
                "PD0013" if item["name"] == "Beta" else item["id"]
            )
        assert item["topological_layer"] == max(
            (
                records[parent]["topological_layer"] + 1
                for parent in item["dependencies"]
            ),
            default=0,
        )
        closure = set(item["dependencies"])
        for parent in item["dependencies"]:
            closure.update(records[parent]["transitive_dependencies"])
        assert item["transitive_dependencies"] == sorted(closure)
        if item["global_definition"] is not None:
            blueprint = inputs["blueprint"][item["global_definition"]]
            assert len(blueprint["parameters"]) == item["arity"]
            assert sorted(item["global_argument_positions"]) == list(range(item["arity"]))
        available.add(item["id"])


def test_all_sixteen_advanced_conservative_definitions_have_exact_global_identities(
    corpora: dict[str, dict], inputs: dict
) -> None:
    all_records = {
        row["name"]: row
        for corpus in corpora.values()
        for row in corpus["definitions"]
    }
    reviewed = {
        row["name"]: row for row in inputs["global_graph"]["reviewed_definitions"]
    }
    matches = {
        row["blueprint_name"]: row
        for row in inputs["global_graph"]["compatible_reviewed_matches"]
    }
    assert len(ADVANCED_LAYER_DEFINITIONS) == 16
    for definition in ADVANCED_LAYER_DEFINITIONS:
        row = all_records[definition.name]
        match = matches[definition.name]
        global_row = reviewed[definition.name]
        assert row["id"] == match["reviewed_id"] == global_row["id"] == definition.stable_id
        assert row["arity"] == definition.arity
        assert row["parameters"] == list(definition.parameters)
        assert row["dependency_names"] == list(definition.conceptual_dependencies)
        assert row["expansion_sha256"] == global_row["expansion_sha256"]
        assert ADVANCED_LAYER_DEFINITIONS_BY_NAME[definition.name] is definition
        assert ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[definition.name] is definition


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_compact_advanced_statement_expands_to_identical_kernel_formula(
    slug: str, corpora: dict[str, dict]
) -> None:
    corpus = corpora[slug]
    definitions = {
        item["name"]: explorer._definition_specs()[item["name"]]
        for item in corpus["definitions"]
    }
    for node in corpus["nodes"]:
        compact = node["defined"]
        parser = explorer._LocalDefinedParser(compact["defined_statement"], definitions)
        parser.free = list(compact["free_names"])
        assert parser.parse() == parse_formula_in_context(
            node["statement"], list(compact["free_names"])
        )
        assert compact["exact_ast_equivalence"] is True
        assert compact["expanded_statement_sha256"] == node["statement_sha256"]
        assert Counter(
            part["definition"]
            for part in compact["statement_parts"]
            if part["kind"] == "definition"
        ) == compact["statement_definition_uses"]


@pytest.mark.parametrize(
    "source",
    (
        "MatrixAffineSlice(a,b,c,d,e,f)",
        "MatrixAffineSlice(a,b,c,d,e,f,g,h)",
        "SignedMatrixProduct(a,b,c)",
        "UnknownAdvancedDefinition(a)",
        "EuclideanExecution(a,b,c,d)",
    ),
)
def test_family_defined_parser_rejects_wrong_arity_unknown_and_cross_family_calls(
    source: str,
) -> None:
    definitions = {
        item.name: item
        for item in explorer._definition_closure(explorer.FAMILIES[0].definitions)
    }
    with pytest.raises(ParseError):
        explorer._LocalDefinedParser(source, definitions).parse()


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_proof_definition_and_notation_arrows_are_separate_and_acyclic(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes]
) -> None:
    corpus = corpora[slug]
    graph = json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
    assert graph["alpha_edition_version"] == "v25"
    assert graph["alpha_first_enrolled_version"] == "v21"
    assert graph["milestone_status"] == corpus["milestone_status"]
    assert graph["path_policy"] == "proof_dependency_edges_only"
    tags = set(corpus["tags"].values())
    definitions = set(corpus["definition_topological_order"])
    assert tags.isdisjoint(definitions)
    for edge in graph["edges"]:
        if edge["kind"] == "proof_dependency":
            assert edge["source"] in tags
            assert edge["target"] in tags
        elif edge["kind"] == "uses_definition":
            assert edge["source"] in tags
            assert edge["target"] in definitions
        else:
            assert edge["kind"] == "definition_uses_definition"
            assert edge["source"] in definitions
            assert edge["target"] in definitions
    for tag, row in graph["proof_adjacency"].items():
        assert tag in tags
        assert set(row["dependencies"]) <= tags
        assert set(row["dependents"]) <= tags
        assert set(row["critical_root_path"]) <= tags


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_family_retains_original_exact_defined_and_interactive_surfaces(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes]
) -> None:
    corpus = corpora[slug]
    for suffix in (
        "index.html",
        "explorer/index.html",
        "explorer/defined/index.html",
        "explorer/defined/graph.html",
    ):
        page = generated[f"{slug}/{suffix}"].decode()
        assert "Alpha v20" not in page
        assert "ALPHA v20" not in page
        assert "grand-campaign/" in page
        assert f'v={corpus["alpha_catalog_sha256"][:12]}' in html.unescape(page)
    graph_page = generated[f"{slug}/explorer/defined/graph.html"].decode()
    assert "data-defined-graph" in graph_page
    assert "data-graph-svg" in graph_page
    assert "window.PA_DEFINED_GRAPH=" in graph_page
    assert 'class="pa-defined-proof-site"' in graph_page


@pytest.mark.parametrize(("key", "tag"), EXPECTED_ROOT_TAGS.items())
def test_every_major_root_has_exact_and_definition_aware_complete_proof_pages(
    key: tuple[str, str], tag: str, generated: dict[str, bytes]
) -> None:
    slug, theorem = key
    exact = generated[f"{slug}/explorer/tag/{tag}.html"].decode()
    defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
    assert theorem in exact
    assert theorem in defined
    assert "Alpha v25" in defined
    assert "Alpha v21" in defined
    assert "/ 209</dd>" in defined
    assert "all 209 exact bundle nodes" in defined
    assert "Actual proof prerequisites" in defined
    assert "Complete unchanged native tactic proof" in defined


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_historical_open_milestones_distinguish_v23_closure_and_v24_open_t13(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes]
) -> None:
    corpus = corpora[slug]
    goal = corpus["campaign_goal_id"]
    landing = generated[f"{slug}/index.html"].decode()
    root = corpus["tags"][corpus["root_names"][-1]]
    theorem = generated[f"{slug}/explorer/defined/tag/{root}.html"].decode()
    if goal == "T13":
        assert f"{goal} remains OPEN" in landing
        assert f"{goal} remains OPEN" in theorem
        assert corpus["milestone_status"] == "open"
        assert corpus["milestone_checked_use"] is False
    else:
        assert f"{goal} was OPEN" in landing
        assert f"{goal} was OPEN" in theorem
        assert "CLOSED in Alpha v23" in landing
        assert "CLOSED in Alpha v23" in theorem
        assert corpus["milestone_status"] == "alpha_closed"
        assert corpus["milestone_checked_use"] is True


@pytest.mark.parametrize(
    "mutation",
    (
        "statement",
        "statement-digest",
        "script",
        "script-digest",
        "dependency",
        "source",
        "checked-use",
        "stable",
        "campaign",
        "bundle-campaign",
        "bundle-node",
        "bundle-digest",
    ),
)
def test_corrupt_advanced_release_rows_and_receipts_fail_closed(
    inputs: dict, mutation: str
) -> None:
    spec = inputs["enrollment"].frontier_specs[0]
    row = deepcopy(inputs["by_name"][spec.name])
    if mutation == "statement":
        row["statement"] += " /\\ false"
    elif mutation == "statement-digest":
        row["statement_sha256"] = "0" * 64
    elif mutation == "script":
        row["script"] = row["script"][:-1]
    elif mutation == "script-digest":
        row["script_sha256"] = "0" * 64
    elif mutation == "dependency":
        row["dependencies"] = []
    elif mutation == "source":
        row["source"]["path"] = "missing.py"
    elif mutation == "checked-use":
        row["checked_use"] = False
    elif mutation == "stable":
        row["membership"] = "stable"
    elif mutation == "campaign":
        row["frontier_campaign"] = "euclidean_complexity"
    elif mutation == "bundle-campaign":
        row["empty_context_closure"]["bundle_campaign"] = "next_layer"
    elif mutation == "bundle-node":
        row["empty_context_closure"]["bundle_node_id"] = 209
    else:
        row["alpha_v21_frontier_enrollment"]["bundle_sha256"] = "0" * 64
    with pytest.raises(explorer.AdvancedLayerExplorerError):
        explorer._validate_theorem(
            row,
            spec=spec,
            campaign=inputs["enrollment"].campaign_by_name[spec.name],
            source=inputs["enrollment"].source_by_name[spec.name],
            bundle=inputs["bundle"],
        )


@pytest.mark.parametrize(
    "mutation",
    ("identity", "global-id", "global-template", "global-signature", "route", "dependency"),
)
def test_forged_definition_identities_and_signatures_cannot_enter_public_explorer(
    inputs: dict, mutation: str
) -> None:
    family = explorer.FAMILIES[0]
    altered = dict(inputs)
    altered["global_graph"] = deepcopy(inputs["global_graph"])
    target = next(
        item for item in altered["global_graph"]["reviewed_definitions"]
        if item["name"] == "MatrixAffineSlice"
    )
    if mutation == "identity":
        target["id"] = "ND0013"
    elif mutation == "global-id":
        match = next(
            item for item in altered["global_graph"]["compatible_reviewed_matches"]
            if item["blueprint_name"] == "MatrixAffineSlice"
        )
        match["reviewed_id"] = "ND0013"
    elif mutation == "global-template":
        target["expansion_sha256"] = "0" * 64
    elif mutation == "global-signature":
        altered["blueprint"] = deepcopy(inputs["blueprint"])
        altered["blueprint"]["MatrixAffineSlice"]["parameters"] = ["b"]
    elif mutation == "route":
        target["route"] = "euclidean-complexity"
    else:
        target["dependencies"] = ["BinaryModulus"]
    with pytest.raises(explorer.AdvancedLayerExplorerError):
        explorer._definition_records(family, altered)


def test_advanced_explorer_never_decodes_checks_or_replays_a_proof_bundle() -> None:
    source = (SCRIPTS / "build_constructive_advanced_layer_explorer.py").read_text()
    assert "decode_proof_bundle(" not in source
    assert "checked_advanced_layer_bundle(" not in source
    assert "replay_candidate_bodies(" not in source
    assert "compile_layered_replay(" not in source


def test_three_family_output_is_deterministically_generated_and_stale_checked(
    generated: dict[str, bytes], tmp_path: Path
) -> None:
    explorer._write(tmp_path, generated)
    assert explorer._check(tmp_path, generated)
    (tmp_path / "index.html").write_bytes(b"corrupt")
    assert not explorer._check(tmp_path, generated)


def test_public_advanced_explorer_snapshot_is_fresh() -> None:
    result = subprocess.run(
        ["python3", str(SCRIPTS / "build_constructive_advanced_layer_explorer.py"), "--check"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "54 checked theorems" in result.stdout
