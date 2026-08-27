"""Canonical QR v25 breakthroughs, with separate v27 closure and original partial scope."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_constructive_breakthrough_layer_explorer as explorer  # noqa: E402
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    BREAKTHROUGH_LAYER_DEFINITIONS,
    BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME,
)
from constructive_proof_explorer_template import (  # noqa: E402
    ProofExplorerTemplateError,
    render_canonical_family_landing,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.kernel.terms import ParseError  # noqa: E402


EXPECTED = {
    "matrix-cofactor-expansion": (29, "D05", "F12", "T13"),
    "polynomial-taylor-hensel": (19, "D04", "F10", "G095"),
    "generalized-crt-compatibility": (24, "D01", "F02", "G011"),
}
EXPECTED_ROOT_TAGS = {
    ("matrix-cofactor-expansion", "matrix_minor_four_code_components_injective"): "CE0003",
    ("matrix-cofactor-expansion", "signed_cofactor_minor_family_exists"): "CE0009",
    ("matrix-cofactor-expansion", "signed_cofactor_minor_family_entry_projects_minor"): "CE000B",
    ("matrix-cofactor-expansion", "signed_alternating_product_prefix_exact_term"): "CE0015",
    ("matrix-cofactor-expansion", "signed_alternating_cofactor_fold_exists"): "CE0017",
    ("matrix-cofactor-expansion", "signed_alternating_cofactor_fold_functional"): "CE0018",
    ("matrix-cofactor-expansion", "signed_alternating_cofactor_fold_exists_unique"): "CE0019",
    ("matrix-cofactor-expansion", "signed_first_row_cofactor_fold_exists"): "CE001C",
    ("matrix-cofactor-expansion", "signed_matrix_cofactor_family_and_fold_exists"): "CE001D",
    ("polynomial-taylor-hensel", "beta_horner_eval_mod_congruence"): "TH0004",
    ("polynomial-taylor-hensel", "beta_horner_derivative_mod_congruence"): "TH0005",
    ("polynomial-taylor-hensel", "beta_horner_taylor_remainder_exists"): "TH0008",
    ("polynomial-taylor-hensel", "hensel_correction_exists_unique"): "TH000B",
    ("polynomial-taylor-hensel", "horner_derivative_coprime_bounded_inverse"): "TH000C",
    ("polynomial-taylor-hensel", "beta_horner_taylor_square_congruence"): "TH000D",
    ("polynomial-taylor-hensel", "beta_horner_hensel_lift_divisibility"): "TH0012",
    ("polynomial-taylor-hensel", "beta_horner_hensel_lift_exists"): "TH0013",
    ("generalized-crt-compatibility", "crt_prefix_solution_implies_pairwise_compatible"): "GC0005",
    ("generalized-crt-compatibility", "crt_merge_compatible_prefix_solution_exists"): "GC0009",
    ("generalized-crt-compatibility", "crt_prefix_zero_lcm_solution_unique"): "GC000B",
    ("generalized-crt-compatibility", "crt_is_gcd_scale"): "GC000E",
    ("generalized-crt-compatibility", "crt_lcm_gcd_cofactor_product"): "GC0012",
    ("generalized-crt-compatibility", "crt_gcd_lcm_distributes_divisibility"): "GC0015",
    ("generalized-crt-compatibility", "crt_pairwise_compatible_dominating_last_canonical_exists_unique"): "GC0018",
    ("generalized-crt-compatibility", "crt_merge_compatible_prefix_canonical_exists_unique"): "GC000C",
}


class _LandingMarkup(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, {key: value or "" for key, value in attrs}))


@pytest.fixture(scope="module")
def inputs() -> dict:
    return explorer._load_inputs()


@pytest.fixture(scope="module")
def generated() -> dict[str, bytes]:
    return explorer.build_files()


@pytest.fixture(scope="module")
def corpora(generated: dict[str, bytes]) -> dict[str, dict]:
    return {slug: json.loads(generated[f"{slug}/api/corpus.json"]) for slug in EXPECTED}


def test_manifest_authenticates_current_v27_historical_v25_bundle_kernel_and_lean(
    generated: dict[str, bytes], inputs: dict,
) -> None:
    manifest = json.loads(generated["manifest.json"])
    digest = sha256(explorer.CURRENT_CATALOG.read_bytes()).hexdigest()
    assert manifest["schema"] == "peano-lab-constructive-breakthrough-layer-explorer-v1-manifest"
    assert manifest["alpha_edition_version"] == "v27"
    assert manifest["alpha_first_enrolled_version"] == "v25"
    assert manifest["catalog_sha256"] == digest
    assert manifest["first_enrollment_catalog_sha256"] == (
        sha256(explorer.CATALOG.read_bytes()).hexdigest()
    )
    assert manifest["html_revision"] == digest[:12]
    assert manifest["edition_identity_sha256"] == inputs["catalog"]["edition_identity_sha256"]
    assert inputs["channels"]["channels"]["alpha"]["artifact_sha256"] == digest
    assert inputs["first_admission_catalog"]["parent_alpha_v24"]["artifacts"]["catalog"]["sha256"] == (
        sha256(explorer.PARENT_CATALOG.read_bytes()).hexdigest()
    )
    assert manifest["proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert manifest["proof_bundle_node_count"] == 302
    assert manifest["independent_lean_bundle_verified"]
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 72
    assert manifest["stable_count"] == 0
    assert manifest["file_count"] + 1 == len(generated)
    assert {item["slug"]: item["theorem_count"] for item in manifest["families"]} == {
        slug: row[0] for slug, row in EXPECTED.items()
    }
    assert all(
        item["milestone_status"] == "alpha_closed"
        and item["milestone_checked_use"]
        and item["historical_partial_checked_use"]
        for item in manifest["families"]
    )
    for item in manifest["files"]:
        payload = generated[item["path"]]
        assert item["bytes"] == len(payload)
        assert item["sha256"] == sha256(payload).hexdigest()


def test_original_quadratic_reciprocity_explorer_assets_stay_byte_identical(
    generated: dict[str, bytes],
) -> None:
    for name, source in explorer.ASSET_SOURCES.items():
        payload = generated[f"assets/{name}"]
        assert payload == source.read_bytes()
        if name in explorer.PINNED_ASSETS:
            assert sha256(payload).hexdigest() == explorer.PINNED_ASSETS[name]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_breakthrough_uses_exact_canonical_qr_landing_hierarchy(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    family = next(item for item in explorer.FAMILIES if item.slug == slug)
    source = generated[f"{slug}/index.html"].decode()
    reference = (ROOT / "deploy" / "proofs" / "quadratic-reciprocity.html").read_text()
    markup = _LandingMarkup()
    markup.feed(source)
    for marker in (
        '<header class="family-hero">', '<div class="shell">', '<nav class="crumbs">',
        '<p class="eyebrow">', '<p class="formula">', '<p class="lede">',
        '<div class="hero-actions">', '<main class="shell family-main">',
        '<section class="view-grid">', '<article class="view-card featured">',
        '<section class="release-note">',
    ):
        assert marker in reference
        assert marker in source
    assert f'<body class="family-page {slug}-page">' in source
    assert source.count('<article class="view-card') == 3
    assert '<body class="proof-library-site"' not in source
    assert 'class="proof-home' not in source
    revision = corpus["alpha_catalog_sha256"][:12]
    assert f'href="../assets/proofs.css?v={revision}"' in source
    assert f'href="explorer/defined/?v={revision}"' in source
    assert f'href="explorer/?v={revision}"' in source
    assert "first admitted v25" in source
    assert "Alpha v27 checked-use theorem family" in source
    assert "independently accept all 302 bundle nodes" in source
    assert "Historical partial components only" in source
    assert corpus["alpha_proof_bundle_sha256"] in source
    for root in family.roots:
        assert f'explorer/defined/tag/{corpus["tags"][root]}.html?v={revision}' in source
        assert root in source
    links = [attrs for tag, attrs in markup.elements if tag == "a"]
    graphs = [link for link in links if "defined/graph.html?" in link.get("href", "")]
    root_tag = corpus["tags"][family.roots[-1]]
    assert any(
        f"target={root_tag}" in link["href"]
        and "view=neighborhood" in link["href"]
        and "definitions=selected" in link["href"]
        and "edges=focus" in link["href"]
        for link in graphs
    )
    assert {link.get("data-campaign-link") for link in links} >= {
        "global", "domain", "family", "goal", "milestone",
    }
    canonical = next(
        attrs for tag, attrs in markup.elements
        if tag == "link" and attrs.get("rel") == "canonical"
    )
    assert canonical["href"] == f"https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/{slug}/"


@pytest.mark.parametrize(("key", "expected"), EXPECTED_ROOT_TAGS.items())
def test_all_major_breakthrough_roots_have_exact_stable_tags(
    key: tuple[str, str], expected: str, corpora: dict[str, dict],
) -> None:
    slug, theorem = key
    assert corpora[slug]["tags"][theorem] == expected
    assert theorem in corpora[slug]["root_names"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_independently_proved_results_never_close_stronger_unproved_goals(
    slug: str, corpora: dict[str, dict], inputs: dict, generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    count, domain, family, milestone = EXPECTED[slug]
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == count
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["campaign_domain_id"] == domain
    assert corpus["campaign_family_id"] == family
    assert corpus["campaign_goal_id"] == milestone
    assert corpus["campaign_milestone_ids"] == [milestone]
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"]
    assert corpus["historical_partial_checked_use"]
    assert corpus["historical_component_only"]
    assert corpus["historical_milestone_status"] == "open"
    full_slug, full_root = explorer.original.SECOND_WAVE_COMPLETIONS[milestone]
    assert corpus["milestone_full_proof_slug"] == full_slug
    assert corpus["milestone_full_theorem_name"] == full_root
    assert full_root not in corpus["tags"]
    assert inputs["milestones"][milestone]["status"] == "alpha_closed"
    assert inputs["milestones"][milestone]["evidence"]["checked_use"]
    assert inputs["milestones"][milestone]["historical_partial_evidence"]["partial_component_checked_use"]
    assert "Historical partial components only" in generated[f"{slug}/index.html"].decode()
    assert f'{full_slug}/?v={corpus["alpha_catalog_sha256"][:12]}' in (
        generated[f"{slug}/index.html"].decode()
    )
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
        assert node["alpha_edition_version"] == "v27"
        assert node["alpha_first_enrolled_version"] == "v25"
        assert node["alpha_checked_use"]
        assert node["independent_lean_bundle_verified"]
        assert not node["stable_member"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_local_definition_is_exact_hygienic_and_dependency_first(
    slug: str, corpora: dict[str, dict], inputs: dict,
) -> None:
    corpus = corpora[slug]
    records = {item["id"]: item for item in corpus["definitions"]}
    assert corpus["definition_topological_order"] == list(records)
    reviewed = {item["name"]: item for item in inputs["global_graph"]["reviewed_definitions"]}
    available: set[str] = set()
    for item in corpus["definitions"]:
        assert set(item["dependencies"]) <= available
        assert item["arity"] == len(item["parameters"])
        assert item["expansion_sha256"] == sha256(item["expanded_template"].encode()).hexdigest()
        assert item["exact_ast_verified"] and item["kernel_signature_unchanged"]
        assert parse_formula_in_context(
            item["expanded_template"], list(item["parameters"])
        ) == ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[item["name"]].template_formula
        assert item["topological_layer"] == max(
            (records[parent]["topological_layer"] + 1 for parent in item["dependencies"]),
            default=0,
        )
        closure = set(item["dependencies"])
        for parent in item["dependencies"]:
            closure.update(records[parent]["transitive_dependencies"])
        assert item["transitive_dependencies"] == sorted(closure)
        if item["id"].startswith("ND"):
            assert reviewed[item["name"]]["id"] == item["id"]
        if item["global_definition"] is not None:
            assert sorted(item["global_argument_positions"]) == list(range(item["arity"]))
        available.add(item["id"])


def test_all_eleven_breakthrough_aliases_have_exact_global_reviewed_identity(
    corpora: dict[str, dict], inputs: dict,
) -> None:
    records = {
        row["name"]: row for corpus in corpora.values() for row in corpus["definitions"]
    }
    matches = {
        row["blueprint_name"]: row
        for row in inputs["global_graph"]["compatible_reviewed_matches"]
    }
    assert len(BREAKTHROUGH_LAYER_DEFINITIONS) == 11
    assert tuple(definition.stable_id for definition in BREAKTHROUGH_LAYER_DEFINITIONS) == (
        tuple(f"ND{index:04d}" for index in range(58, 69))
    )
    for definition in BREAKTHROUGH_LAYER_DEFINITIONS:
        row = records[definition.name]
        assert row["id"] == matches[definition.name]["reviewed_id"] == definition.stable_id
        assert row["parameters"] == list(definition.parameters)
        assert row["dependency_names"] == list(definition.conceptual_dependencies)
        assert BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME[definition.name] is definition


def test_four_argument_beta_sum_drilldown_preserves_incompatible_generic_sum(
    corpora: dict[str, dict], inputs: dict,
) -> None:
    corpus = corpora["matrix-cofactor-expansion"]
    beta_sum = next(item for item in corpus["definitions"] if item["name"] == "Sum")
    assert beta_sum["arity"] == 4
    assert beta_sum["global_definition"] == "BetaSum"
    assert beta_sum["global_argument_positions"] == [0, 1, 2, 3]
    mismatch = next(
        item for item in inputs["global_graph"]["incompatible_reviewed_matches"]
        if item["blueprint_name"] == "Sum"
    )
    assert mismatch["blueprint_arity"] == 3
    assert mismatch["reviewed_arity"] == 4
    assert not mismatch["confers_checked_evidence"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_compact_breakthrough_formula_expands_to_identical_kernel_ast(
    slug: str, corpora: dict[str, dict],
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
        assert compact["exact_ast_equivalence"]
        assert compact["expanded_statement_sha256"] == node["statement_sha256"]
        assert Counter(
            item["definition"] for item in compact["statement_parts"]
            if item["kind"] == "definition"
        ) == compact["statement_definition_uses"]


@pytest.mark.parametrize(
    "source",
    (
        "MatrixMinorFourCode(z,up,us,un)",
        "SignedMinorRecord(pb,pc,nb,nc,q,j)",
        "SignedAlternatingCofactorFold(ab,ac,db,dc,eb,ec,fb,fc,l,p)",
        "HornerTaylorRemainder(b,c,x,h,l,n,d,y)",
        "HenselCorrection(d,p,q)",
        "CRTPairwiseCompatiblePrefix(r,s,b,c)",
        "CRTMergeCompatiblePrefix(r,s,b,c)",
        "UnknownBreakthroughDefinition(n)",
    ),
)
def test_defined_parser_rejects_wrong_arities_and_unknown_breakthrough_relations(
    source: str,
) -> None:
    with pytest.raises(ParseError):
        explorer._LocalDefinedParser(source, dict(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)).parse()


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_proof_notation_and_definition_edges_remain_independent(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    graph = json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
    assert graph["alpha_edition_version"] == "v27"
    assert graph["alpha_first_enrolled_version"] == "v25"
    assert graph["milestone_status"] == "alpha_closed"
    assert graph["milestone_checked_use"]
    assert graph["historical_partial_checked_use"]
    assert graph["path_policy"] == "proof_dependency_edges_only"
    tags = set(corpus["tags"].values())
    definitions = set(corpus["definition_topological_order"])
    assert tags.isdisjoint(definitions)
    for edge in graph["edges"]:
        if edge["kind"] == "proof_dependency":
            assert edge["source"] in tags and edge["target"] in tags
        elif edge["kind"] == "uses_definition":
            assert edge["source"] in tags and edge["target"] in definitions
        else:
            assert edge["kind"] == "definition_uses_definition"
            assert edge["source"] in definitions and edge["target"] in definitions
    for tag, row in graph["proof_adjacency"].items():
        assert tag in tags
        assert set(row["dependencies"]) <= tags
        assert set(row["dependents"]) <= tags
        assert set(row["critical_root_path"]) <= tags


@pytest.mark.parametrize(("key", "tag"), EXPECTED_ROOT_TAGS.items())
def test_major_root_pages_expose_complete_tactics_exact_proofs_and_historical_scope(
    key: tuple[str, str], tag: str, generated: dict[str, bytes],
) -> None:
    slug, theorem = key
    exact = generated[f"{slug}/explorer/tag/{tag}.html"].decode()
    defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
    assert theorem in exact and theorem in defined
    assert "Alpha v27" in defined
    assert "/ 302</dd>" in defined
    assert "all 302 exact bundle nodes" in defined
    assert "Actual proof prerequisites" in defined
    assert "Complete unchanged native tactic proof" in defined
    assert "Historical partial components only" in defined


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_all_exact_defined_graph_and_global_navigation_surfaces_exist(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    for suffix in (
        "index.html", "explorer/index.html", "explorer/defined/index.html",
        "explorer/defined/graph.html",
    ):
        page = generated[f"{slug}/{suffix}"].decode()
        assert "Alpha v20" not in page and "Alpha v21" not in page
        assert "Alpha v22" not in page and "Alpha v23" not in page
        assert "Alpha v24" not in page
        assert "grand-campaign/" in page
        assert f'v={corpus["alpha_catalog_sha256"][:12]}' in html.unescape(page)
    graph = generated[f"{slug}/explorer/defined/graph.html"].decode()
    assert "data-defined-graph" in graph
    assert "data-graph-svg" in graph
    assert "window.PA_DEFINED_GRAPH=" in graph
    assert 'class="pa-defined-proof-site"' in graph


@pytest.mark.parametrize(
    ("field", "value"),
    (("slug", "../escape"), ("title", ""), ("domain", "D4"), ("roots", ()), ("caveat", "")),
)
def test_canonical_renderer_fails_closed_for_unsafe_or_unsupported_families(
    field: str, value: object, corpora: dict[str, dict], inputs: dict,
) -> None:
    family = replace(explorer.FAMILIES[0], **{field: value})
    with pytest.raises(ProofExplorerTemplateError):
        render_canonical_family_landing(
            family, corpora["matrix-cofactor-expansion"], revision=inputs["revision"],
            current_alpha_version="v27", first_admitted_version="v25",
            bundle_node_count=302,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "statement", "statement-digest", "script", "script-digest", "dependency", "source",
        "checked-use", "stable", "campaign", "bundle-campaign", "bundle-node", "bundle-digest",
    ),
)
def test_corrupt_v25_rows_and_original_kernel_receipts_fail_closed(
    inputs: dict, mutation: str,
) -> None:
    item = inputs["enrollment"].frontier_specs[0]
    row = deepcopy(inputs["by_name"][item.name])
    if mutation == "statement":
        row["statement"] += " /\\ false"
    elif mutation == "statement-digest":
        row["statement_sha256"] = "0" * 64
    elif mutation == "script":
        row["script"] = row["script"][:-1]
    elif mutation == "script-digest":
        row["script_sha256"] = "0" * 64
    elif mutation == "dependency":
        row["dependencies"] = ["forged_dependency"]
    elif mutation == "source":
        row["source"]["path"] = "missing.py"
    elif mutation == "checked-use":
        row["checked_use"] = False
    elif mutation == "stable":
        row["membership"] = "stable"
    elif mutation == "campaign":
        row["frontier_campaign"] = "fake"
    elif mutation == "bundle-campaign":
        row["empty_context_closure"]["bundle_campaign"] = "forged"
    elif mutation == "bundle-node":
        row["empty_context_closure"]["bundle_node_id"] = 302
    else:
        row["empty_context_closure"]["certificate_sha256"] = "0" * 64
    with pytest.raises(explorer.BreakthroughLayerExplorerError):
        explorer._validate_theorem(
            row,
            spec=item,
            campaign=inputs["enrollment"].campaign_by_name[item.name],
            source=inputs["enrollment"].source_by_name[item.name],
            bundle=inputs["bundle"],
        )


def test_current_v27_preserves_exact_historical_admission_and_separate_stable(
    inputs: dict, corpora: dict[str, dict],
) -> None:
    current = inputs["catalog"]
    historical = inputs["first_admission_catalog"]
    assert current["schema"] == "peano-library-alpha-snapshot-v27"
    assert current["theorem_count"] == current["checked_use_count"] == explorer.current_alpha.EXPECTED_ALPHA_V27_CHECKED_USE_COUNT
    assert current["stable_count"] == 432
    assert historical["schema"] == "peano-library-alpha-snapshot-v25"
    assert current["theorems"][:historical["theorem_count"]] == historical["theorems"]
    assert inputs["first_admission_catalog_sha256"] == sha256(
        explorer.CATALOG.read_bytes()
    ).hexdigest()
    from constructive_second_wave_definition_graph import build_definition_graph

    assert inputs["global_graph"] == build_definition_graph(inputs["campaign"])
    for corpus in corpora.values():
        assert corpus["alpha_edition_version"] == "v27"
        assert corpus["alpha_first_enrolled_version"] == "v25"
        assert corpus["alpha_first_enrollment_catalog_sha256"] == (
            inputs["first_admission_catalog_sha256"]
        )
    for milestone in ("T13", "G095", "G011"):
        evidence = inputs["milestones"][milestone]["evidence"]
        historical_evidence = inputs["milestones"][milestone]["historical_partial_evidence"]
        assert evidence["alpha_version"] == "v27"
        assert evidence["checked_use"]
        assert "partial_component_checked_use" not in evidence
        assert historical_evidence["alpha_version"] == "v25"
        assert not historical_evidence["checked_use"]
        assert historical_evidence["partial_component_checked_use"]
        assert evidence["bundle_sha256"] != historical_evidence["bundle_sha256"]


@pytest.mark.parametrize(
    ("surface", "path", "value"),
    (
        ("catalog", ("schema",), "peano-library-alpha-snapshot-v25"),
        ("catalog", ("theorem_count",), 2080),
        ("catalog", ("checked_use_count",), 2080),
        ("catalog", ("stable_count",), 433),
        ("catalog", ("edition_identity_sha256",), "0" * 64),
        ("catalog", ("ordered_enrollment_root_sha256",), "0" * 64),
        ("catalog", ("parent_alpha_v25",), None),
        ("catalog", ("parent_alpha_v25", "schema"), "peano-library-alpha-snapshot-v24"),
        ("catalog", ("parent_alpha_v25", "theorem_count"), 2008),
        ("catalog", ("parent_alpha_v25", "edition_identity_sha256"), "0" * 64),
        ("catalog", ("parent_alpha_v25", "ordered_enrollment_root_sha256"), "0" * 64),
        ("catalog", ("parent_alpha_v25", "artifacts"), None),
        ("catalog", ("parent_alpha_v25", "artifacts", "catalog", "sha256"), "0" * 64),
        ("catalog", ("theorems",), []),
        ("catalog", ("theorems", 0, "statement"), "false"),
        ("catalog", ("theorems", 0, "checked_use"), False),
        ("catalog", ("theorems", 0, "script"), ["forged"]),
        ("channels", ("schema",), "peano-library-channels-v25"),
        ("channels", ("default_channel",), "alpha"),
        ("channels", ("parent_channels_v26", "path"), "artifacts/peano-library/channels-v24.json"),
        ("channels", ("parent_channels_v26", "sha256"), "0" * 64),
        ("channels", ("channels", "alpha", "artifact_path"), "artifacts/peano-library/alpha/catalog-v25.json"),
        ("channels", ("channels", "alpha", "artifact_sha256"), "0" * 64),
        ("channels", ("channels", "alpha", "theorem_count"), 2080),
        ("channels", ("channels", "alpha", "checked_use_count"), 2080),
        ("channels", ("channels", "alpha", "edition_identity_sha256"), "0" * 64),
        ("channels", ("channels", "alpha", "ordered_enrollment_root_sha256"), "0" * 64),
        ("channels", ("channels", "alpha", "parent_alpha_v25_sha256"), "0" * 64),
        ("channels", ("channels", "stable", "artifact_sha256"), "0" * 64),
        ("channels", ("channels", "stable", "theorem_count"), 433),
    ),
)
def test_current_authority_corruption_fails_closed_even_with_rehashed_pointer(
    inputs: dict,
    monkeypatch: pytest.MonkeyPatch,
    surface: str,
    path: tuple[str | int, ...],
    value: object,
) -> None:
    # Copy only the mutated path, preserving the large immutable theorem
    # inventory and keeping each corruption case's memory use bounded.
    document = dict(inputs["catalog"] if surface == "catalog" else inputs["channels"])
    cursor = document
    for key in path[:-1]:
        child = cursor[key]
        cursor[key] = dict(child) if isinstance(child, dict) else list(child)
        cursor = cursor[key]
    cursor[path[-1]] = value
    channels = deepcopy(inputs["channels"])
    current_raw = explorer.CURRENT_CATALOG.read_bytes()
    if surface == "catalog":
        current_raw = explorer._json(document)
        channels["channels"]["alpha"]["artifact_sha256"] = sha256(current_raw).hexdigest()
    else:
        channels = document
    channel_raw = explorer._json(channels)
    read_bytes = Path.read_bytes

    def mutated_read_bytes(path: Path) -> bytes:
        if path == explorer.CURRENT_CATALOG:
            return current_raw
        if path == explorer.CHANNELS:
            return channel_raw
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", mutated_read_bytes)
    with pytest.raises(explorer.BreakthroughLayerExplorerError, match="Alpha-v27"):
        explorer._load_inputs()


def test_generated_snapshot_and_cli_check_are_exact(generated: dict[str, bytes]) -> None:
    assert explorer._check(explorer.OUTPUT, generated)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "build_constructive_breakthrough_layer_explorer.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "72 checked theorems" in result.stdout
