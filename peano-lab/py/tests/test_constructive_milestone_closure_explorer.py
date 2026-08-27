"""Historical v23 QR-design milestone proofs under current v28 authority."""

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

import build_constructive_milestone_closure_explorer as explorer  # noqa: E402
from constructive_milestone_closure_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    MILESTONE_CLOSURE_DEFINITIONS,
    MILESTONE_CLOSURE_DEFINITIONS_BY_NAME,
)
from constructive_proof_explorer_template import (  # noqa: E402
    ProofExplorerTemplateError,
    render_canonical_family_landing,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.kernel.terms import ParseError  # noqa: E402


EXPECTED = {
    "euclidean-logarithmic-bound": (17, "D04", "F11", "G101"),
    "binary-digit-extraction": (24, "D04", "F11", "G102"),
    "primes-three-mod-four": (18, "D02", "F03", "G025"),
}
EXPECTED_ROOT_TAGS = {
    ("euclidean-logarithmic-bound", "euclidean_log_trace_below_power"): "EL000C",
    ("euclidean-logarithmic-bound", "euclidean_log_trace_bound"): "EL000E",
    ("euclidean-logarithmic-bound", "euclidean_log_execution_strong"): "EL000F",
    ("euclidean-logarithmic-bound", "euclidean_gcd_execution_logarithmic_bound"): "EL0010",
    ("euclidean-logarithmic-bound", "euclidean_gcd_execution_logarithmic_exists"): "EL0011",
    ("binary-digit-extraction", "binary_exponent_digit_prefix_exists"): "BD000A",
    ("binary-digit-extraction", "binary_digit_operation_count_bound"): "BD0012",
    ("binary-digit-extraction", "binary_modular_exponent_coded_execution_exists"): "BD0014",
    ("binary-digit-extraction", "binary_modular_exponent_coded_execution_exists_unique"): "BD0016",
    ("binary-digit-extraction", "binary_modular_execution_bitlength_bound"): "BD0017",
    ("binary-digit-extraction", "binary_modular_execution_logarithmic_bound"): "BD0018",
    ("primes-three-mod-four", "positive_number_with_admissible_prime_divisors_is_two_square"): "TF0006",
    ("primes-three-mod-four", "three_mod_four_prime_divisor_exists"): "TF000D",
    ("primes-three-mod-four", "euclid_three_progression_prime_exists"): "TF000F",
    ("primes-three-mod-four", "euclid_three_prime_divisor_exceeds_bound"): "TF0011",
    ("primes-three-mod-four", "infinitely_many_primes_three_mod_four"): "TF0012",
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


def test_manifest_authenticates_current_v28_and_immutable_v23_first_admission(
    generated: dict[str, bytes], inputs: dict,
) -> None:
    manifest = json.loads(generated["manifest.json"])
    digest = sha256(explorer.CURRENT_CATALOG.read_bytes()).hexdigest()
    assert manifest["schema"] == "peano-lab-constructive-milestone-closure-explorer-v1-manifest"
    assert manifest["alpha_edition_version"] == "v28"
    assert manifest["alpha_first_enrolled_version"] == "v23"
    assert manifest["catalog_sha256"] == digest
    assert manifest["first_enrollment_catalog_sha256"] == sha256(
        explorer.CATALOG.read_bytes()
    ).hexdigest()
    assert manifest["html_revision"] == digest[:12]
    assert manifest["edition_identity_sha256"] == inputs["current_edition_identity_sha256"]
    assert manifest["proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert manifest["proof_bundle_node_count"] == 617
    assert manifest["independent_lean_bundle_verified"]
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 59
    assert manifest["stable_count"] == 0
    assert manifest["file_count"] + 1 == len(generated)
    assert {item["slug"]: item["theorem_count"] for item in manifest["families"]} == {
        slug: row[0] for slug, row in EXPECTED.items()
    }
    assert all(
        item["milestone_status"] == "alpha_closed" and item["milestone_checked_use"]
        for item in manifest["families"]
    )
    for item in manifest["files"]:
        payload = generated[item["path"]]
        assert item["bytes"] == len(payload)
        assert item["sha256"] == sha256(payload).hexdigest()


def test_original_quadratic_reciprocity_assets_are_byte_identical(
    generated: dict[str, bytes],
) -> None:
    for name, source in explorer.ASSET_SOURCES.items():
        payload = generated[f"assets/{name}"]
        assert payload == source.read_bytes()
        if name in explorer.PINNED_ASSETS:
            assert sha256(payload).hexdigest() == explorer.PINNED_ASSETS[name]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_each_family_uses_the_exact_canonical_quadratic_reciprocity_structure(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    family = next(item for item in explorer.FAMILIES if item.slug == slug)
    source = generated[f"{slug}/index.html"].decode()
    reference = (ROOT / "deploy" / "proofs" / "quadratic-reciprocity.html").read_text()
    markup = _LandingMarkup()
    markup.feed(source)
    for marker in (
        '<header class="family-hero">',
        '<div class="shell">',
        '<nav class="crumbs">',
        '<p class="eyebrow">',
        '<p class="formula">',
        '<p class="lede">',
        '<div class="hero-actions">',
        '<main class="shell family-main">',
        '<section class="view-grid">',
        '<article class="view-card featured">',
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
    assert "first admitted v23" in source
    assert "Alpha v28 checked-use theorem family" in source
    assert "independently accept all 617 bundle nodes" in source
    assert "fully proved" in source
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
def test_all_exact_milestone_root_tags_remain_stable(
    key: tuple[str, str], expected: str, corpora: dict[str, dict],
) -> None:
    slug, theorem = key
    assert corpora[slug]["tags"][theorem] == expected
    assert theorem in corpora[slug]["root_names"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_all_three_milestones_are_genuinely_closed_not_open_or_body_only(
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
    assert inputs["milestones"][milestone]["status"] == "alpha_closed"
    assert inputs["milestones"][milestone]["evidence"]["checked_use"]
    assert "fully proved" in generated[f"{slug}/index.html"].decode()
    assert not any(
        text in generated[f"{slug}/index.html"].decode()
        for text in (f"{milestone} remains OPEN", f"{milestone} remains open")
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
        assert node["alpha_edition_version"] == "v28"
        assert node["alpha_first_enrolled_version"] == "v23"
        assert node["alpha_checked_use"]
        assert node["independent_lean_bundle_verified"]
        assert not node["stable_member"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_local_definition_is_hygienic_dependency_first_and_exactly_shared(
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


def test_eight_new_definitions_and_existing_mod4three_share_exact_original_identities(
    corpora: dict[str, dict], inputs: dict,
) -> None:
    records = {
        row["name"]: row for corpus in corpora.values() for row in corpus["definitions"]
    }
    matches = {
        row["blueprint_name"]: row
        for row in inputs["global_graph"]["compatible_reviewed_matches"]
    }
    assert len(MILESTONE_CLOSURE_DEFINITIONS) == 8
    for definition in MILESTONE_CLOSURE_DEFINITIONS:
        row = records[definition.name]
        assert row["id"] == matches[definition.name]["reviewed_id"] == definition.stable_id
        assert row["parameters"] == list(definition.parameters)
        assert row["dependency_names"] == list(definition.conceptual_dependencies)
        assert MILESTONE_CLOSURE_DEFINITIONS_BY_NAME[definition.name] is definition
    mod4 = next(
        item for item in corpora["primes-three-mod-four"]["definitions"]
        if item["name"] == "Mod4Three"
    )
    assert mod4["id"] == mod4["reviewed_definition_id"] == "PD0012"
    assert mod4["global_definition"] == "Mod4Three"
    assert not any(
        item["id"].startswith("ND") and item["name"] == "Mod4Three"
        for item in corpora["primes-three-mod-four"]["definitions"]
    )


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_compact_milestone_statement_expands_to_the_identical_kernel_ast(
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
        "EuclideanBoundedTrace(a,b)",
        "EuclideanLogarithmicExecution(a,b,l,g)",
        "BinaryExponentDigitCode(e,l,b)",
        "PrimeThreeModFourDivisor(n)",
        "UnknownMilestoneDefinition(n)",
    ),
)
def test_defined_parser_rejects_wrong_arity_unknown_and_cross_family_relations(
    source: str,
) -> None:
    definitions = {
        item.name: item
        for item in explorer._definition_closure(explorer.FAMILIES[0].definitions)
    }
    with pytest.raises(ParseError):
        explorer._LocalDefinedParser(source, definitions).parse()


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_theorem_dependencies_notation_usage_and_definition_dags_stay_separate(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    graph = json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
    assert graph["alpha_edition_version"] == "v28"
    assert graph["alpha_first_enrolled_version"] == "v23"
    assert graph["milestone_status"] == "alpha_closed"
    assert graph["milestone_checked_use"]
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
def test_major_root_pages_expose_complete_scripts_evidence_and_lean_receipts(
    key: tuple[str, str], tag: str, generated: dict[str, bytes],
) -> None:
    slug, theorem = key
    exact = generated[f"{slug}/explorer/tag/{tag}.html"].decode()
    defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
    assert theorem in exact and theorem in defined
    assert "Alpha v28" in defined
    assert "/ 617</dd>" in defined
    assert "all 617 exact bundle nodes" in defined
    assert "Actual proof prerequisites" in defined
    assert "Complete unchanged native tactic proof" in defined


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_all_exact_defined_interactive_and_atlas_navigation_surfaces_exist(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    for suffix in (
        "index.html", "explorer/index.html", "explorer/defined/index.html",
        "explorer/defined/graph.html",
    ):
        page = generated[f"{slug}/{suffix}"].decode()
        assert "Alpha v20" not in page and "Alpha v21" not in page and "Alpha v22" not in page
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
def test_canonical_renderer_rejects_unsafe_family_and_missing_evidence_boundaries(
    field: str, value: object, corpora: dict[str, dict], inputs: dict,
) -> None:
    family = replace(explorer.FAMILIES[0], **{field: value})
    with pytest.raises(ProofExplorerTemplateError):
        render_canonical_family_landing(
            family,
            corpora["euclidean-logarithmic-bound"],
            revision=inputs["revision"],
            current_alpha_version="v28",
            first_admitted_version="v23",
            bundle_node_count=617,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "statement", "statement-digest", "script", "script-digest", "dependency", "source",
        "checked-use", "stable", "campaign", "bundle-campaign", "bundle-node", "bundle-digest",
    ),
)
def test_corrupt_release_rows_and_original_kernel_receipts_fail_closed(
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
        row["empty_context_closure"]["bundle_node_id"] = 617
    else:
        row["empty_context_closure"]["certificate_sha256"] = "0" * 64
    with pytest.raises(explorer.MilestoneClosureExplorerError):
        explorer._validate_theorem(
            row,
            spec=item,
            campaign=inputs["enrollment"].campaign_by_name[item.name],
            source=inputs["enrollment"].source_by_name[item.name],
            bundle=inputs["bundle"],
        )


def test_generated_snapshot_and_cli_check_are_exact(generated: dict[str, bytes]) -> None:
    assert explorer._check(explorer.OUTPUT, generated)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "build_constructive_milestone_closure_explorer.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "59 checked theorems" in result.stdout
