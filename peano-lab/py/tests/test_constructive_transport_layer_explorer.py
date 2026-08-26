"""Fail-closed original-design explorers for three checked Alpha-v22 campaigns."""

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

import build_constructive_transport_layer_explorer as explorer  # noqa: E402
from constructive_proof_explorer_template import (  # noqa: E402
    ProofExplorerTemplateError,
    render_canonical_family_landing,
)
from constructive_advanced_layer_definitions import (  # noqa: E402
    ADVANCED_LAYER_DEFINITIONS_BY_NAME,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS_BY_NAME,
)
from constructive_transport_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_DEFINITIONS,
    TRANSPORT_LAYER_DEFINITIONS_BY_NAME,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.kernel.terms import ParseError  # noqa: E402


EXPECTED = {
    "binary-length": (21, "D04", "F11", ("G101", "G102")),
    "euclidean-gcd-transport": (20, "D04", "F11", ("G101",)),
    "binary-modular-execution": (19, "D04", "F11", ("G102",)),
}
EXPECTED_ROOT_TAGS = {
    ("binary-length", "binary_length_exists"): "BL0011",
    ("binary-length", "binary_length_functional"): "BL0013",
    ("binary-length", "binary_length_exists_unique"): "BL0014",
    ("binary-length", "binary_length_power_exact"): "BL0015",
    ("euclidean-gcd-transport", "euclidean_trace_terminal_gcd_exists"): "GT000F",
    ("euclidean-gcd-transport", "euclidean_execution_terminal_identified"): "GT0010",
    ("euclidean-gcd-transport", "euclidean_anchored_execution_exists"): "GT0011",
    ("euclidean-gcd-transport", "euclidean_anchored_execution_linear_bound"): "GT0012",
    ("binary-modular-execution", "binary_execution_prefix_exists"): "BE000B",
    ("binary-modular-execution", "binary_modular_execution_exists"): "BE000C",
    ("binary-modular-execution", "binary_modular_execution_power_correct"): "BE0010",
    ("binary-modular-execution", "binary_modular_execution_horner_exists"): "BE0011",
    ("binary-modular-execution", "binary_modular_execution_result_exists_unique"): "BE0013",
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
    return {
        slug: json.loads(generated[f"{slug}/api/corpus.json"])
        for slug in EXPECTED
    }


def test_manifest_binds_current_v24_to_independently_verified_first_admission_v22(
    generated: dict[str, bytes], inputs: dict
) -> None:
    manifest = json.loads(generated["manifest.json"])
    digest = sha256(explorer.CURRENT_CATALOG.read_bytes()).hexdigest()
    assert manifest["schema"] == "peano-lab-constructive-transport-layer-explorer-v1-manifest"
    assert manifest["alpha_edition_version"] == "v25"
    assert manifest["alpha_first_enrolled_version"] == "v22"
    assert manifest["catalog_sha256"] == digest
    assert manifest["first_enrollment_catalog_sha256"] == sha256(
        explorer.CATALOG.read_bytes()
    ).hexdigest()
    assert manifest["html_revision"] == digest[:12]
    assert manifest["edition_identity_sha256"] == inputs["current_edition_identity_sha256"]
    assert manifest["proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert manifest["proof_bundle_node_count"] == 240
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 60
    assert manifest["stable_count"] == 0
    assert manifest["file_count"] + 1 == len(generated)
    assert {item["slug"]: item["theorem_count"] for item in manifest["families"]} == {
        slug: info[0] for slug, info in EXPECTED.items()
    }
    for family in manifest["families"]:
        assert family["alpha_edition_version"] == "v25"
        assert family["alpha_first_enrolled_version"] == "v22"
    for item in manifest["files"]:
        payload = generated[item["path"]]
        assert item["bytes"] == len(payload)
        assert item["sha256"] == sha256(payload).hexdigest()


def test_immutable_original_quadratic_explorer_assets_are_reused_byte_for_byte(
    generated: dict[str, bytes],
) -> None:
    for name, source in explorer.ASSET_SOURCES.items():
        payload = generated[f"assets/{name}"]
        assert payload == source.read_bytes()
        if name in explorer.PINNED_ASSETS:
            assert sha256(payload).hexdigest() == explorer.PINNED_ASSETS[name]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_family_landing_is_a_true_structural_sibling_of_quadratic_reciprocity(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    family = next(item for item in explorer.FAMILIES if item.slug == slug)
    source = generated[f"{slug}/index.html"].decode()
    reference = (ROOT / "deploy/proofs/quadratic-reciprocity.html").read_text()
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
    assert 'class="proof-hero"' not in source
    assert 'class="proof-card"' not in source
    revision = corpus["alpha_catalog_sha256"][:12]
    assert f'href="../assets/proofs.css?v={revision}"' in source
    assert f'href="explorer/defined/?v={revision}"' in source
    assert f'href="explorer/?v={revision}"' in source
    assert f'first admitted {corpus["alpha_first_enrolled_version"]}' in source
    assert f'Alpha {corpus["alpha_edition_version"]} checked-use theorem family' in source
    assert corpus["alpha_proof_bundle_sha256"] in source
    assert "independently accept all 240 bundle nodes" in source
    for root in family.roots:
        tag = corpus["tags"][root]
        assert f'explorer/defined/tag/{tag}.html?v={revision}' in source
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
    assert any(
        f"target={root_tag}" in link["href"] and "view=prerequisites" in link["href"]
        for link in graphs
    )
    assert {link.get("data-campaign-link") for link in links} >= {
        "global", "domain", "family", "goal", "milestone"
    }
    canonical = next(
        attrs for tag, attrs in markup.elements
        if tag == "link" and attrs.get("rel") == "canonical"
    )
    assert canonical["href"] == (
        f"https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/{slug}/"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("slug", "../escape"),
        ("title", ""),
        ("domain", "D4"),
        ("family_id", "F111"),
        ("milestones", ()),
        ("milestones", ("javascript:alert(1)",)),
        ("roots", ()),
        ("roots", ("nonexistent_unverified_theorem",)),
        ("caveat", ""),
    ),
)
def test_canonical_family_renderer_rejects_unsafe_or_unverified_family_contracts(
    field: str, value: object, corpora: dict[str, dict],
) -> None:
    family = replace(explorer.FAMILIES[0], **{field: value})
    with pytest.raises(ProofExplorerTemplateError):
        render_canonical_family_landing(
            family,
            corpora["binary-length"],
            revision=corpora["binary-length"]["alpha_catalog_sha256"][:12],
            current_alpha_version="v25",
            first_admitted_version="v22",
            bundle_node_count=240,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("alpha_checked_use_node_count", 20),
        ("node_count", False),
        ("definition_count", -1),
        ("alpha_proof_bundle_sha256", "0"),
        ("independent_lean_bundle_verified", False),
        ("tags", {}),
    ),
)
def test_canonical_family_renderer_never_accepts_forged_evidence(
    field: str, value: object, corpora: dict[str, dict],
) -> None:
    corpus = dict(corpora["binary-length"], **{field: value})
    with pytest.raises(ProofExplorerTemplateError):
        render_canonical_family_landing(
            explorer.FAMILIES[0],
            corpus,
            revision=corpora["binary-length"]["alpha_catalog_sha256"][:12],
            current_alpha_version="v25",
            first_admitted_version="v22",
            bundle_node_count=240,
        )


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_family_boundaries_exact_release_rows_and_honest_open_milestones(
    slug: str, corpora: dict[str, dict], inputs: dict,
) -> None:
    corpus = corpora[slug]
    count, domain, family, milestones = EXPECTED[slug]
    assert corpus["node_count"] == count
    assert corpus["alpha_checked_use_node_count"] == count
    assert corpus["alpha_enrolled_node_count"] == count
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["campaign_domain_id"] == domain
    assert corpus["campaign_family_id"] == family
    assert corpus["campaign_goal_id"] == milestones[-1]
    assert corpus["campaign_milestone_ids"] == list(milestones)
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"] is True
    assert corpus["alpha_edition_version"] == "v25"
    assert corpus["alpha_first_enrolled_version"] == "v22"
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
        assert node["alpha_first_enrolled_version"] == "v22"
        assert node["independent_lean_bundle_verified"] is True
        assert node["stable_member"] is False
        assert node["campaign_milestone"] == milestones[-1]


@pytest.mark.parametrize(("key", "tag"), EXPECTED_ROOT_TAGS.items())
def test_major_transport_root_tags_are_pinned_to_exact_original_theorem_order(
    key: tuple[str, str], tag: str, corpora: dict[str, dict],
) -> None:
    slug, theorem = key
    corpus = corpora[slug]
    assert corpus["tags"][theorem] == tag
    assert theorem in corpus["root_names"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_local_definition_dags_are_hygienic_shared_dependency_first_and_exact(
    slug: str, corpora: dict[str, dict], inputs: dict,
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
                TRANSPORT_LAYER_DEFINITIONS_BY_NAME.get(item["name"])
                or ADVANCED_LAYER_DEFINITIONS_BY_NAME.get(item["name"])
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


def test_all_ten_transport_conservative_definitions_have_exact_global_identities(
    corpora: dict[str, dict], inputs: dict,
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
    assert len(TRANSPORT_LAYER_DEFINITIONS) == 10
    for definition in TRANSPORT_LAYER_DEFINITIONS:
        row = all_records[definition.name]
        match = matches[definition.name]
        global_row = reviewed[definition.name]
        assert row["id"] == match["reviewed_id"] == global_row["id"] == definition.stable_id
        assert row["arity"] == definition.arity
        assert row["parameters"] == list(definition.parameters)
        assert row["dependency_names"] == list(definition.conceptual_dependencies)
        assert row["expansion_sha256"] == global_row["expansion_sha256"]
        assert TRANSPORT_LAYER_DEFINITIONS_BY_NAME[definition.name] is definition
        assert ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[definition.name] is definition


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_compact_transport_statement_expands_to_identical_kernel_formula(
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
        "BitLen(n)",
        "BitLen(n,l,x)",
        "PowTwo(e)",
        "UnknownTransportDefinition(n)",
        "EuclideanAnchoredExecution(a,b,g,k)",
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
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    graph = json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
    assert graph["alpha_edition_version"] == "v25"
    assert graph["alpha_first_enrolled_version"] == "v22"
    assert graph["milestone_status"] == "alpha_closed"
    assert graph["path_policy"] == "proof_dependency_edges_only"
    tags = set(corpus["tags"].values())
    definitions = set(corpus["definition_topological_order"])
    assert tags.isdisjoint(definitions)
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            assert node["alpha_edition_version"] == "v25"
            assert node["alpha_first_enrolled_version"] == "v22"
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
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
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
        assert "Alpha v21" not in page
        assert "ALPHA v21" not in page
        assert "grand-campaign/" in page
        assert f'v={corpus["alpha_catalog_sha256"][:12]}' in html.unescape(page)
    graph_page = generated[f"{slug}/explorer/defined/graph.html"].decode()
    assert "data-defined-graph" in graph_page
    assert "data-graph-svg" in graph_page
    assert "window.PA_DEFINED_GRAPH=" in graph_page
    assert 'class="pa-defined-proof-site"' in graph_page


@pytest.mark.parametrize(("key", "tag"), EXPECTED_ROOT_TAGS.items())
def test_every_major_root_has_exact_and_definition_aware_complete_proof_pages(
    key: tuple[str, str], tag: str, generated: dict[str, bytes],
) -> None:
    slug, theorem = key
    exact = generated[f"{slug}/explorer/tag/{tag}.html"].decode()
    defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
    assert theorem in exact
    assert theorem in defined
    assert "Alpha v25" in defined
    assert "/ 240</dd>" in defined
    assert "all 240 exact bundle nodes" in defined
    assert "Actual proof prerequisites" in defined
    assert "Complete unchanged native tactic proof" in defined


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_current_v24_authority_preserves_v23_closure_and_v22_first_admission(
    slug: str, corpora: dict[str, dict], generated: dict[str, bytes],
) -> None:
    corpus = corpora[slug]
    landing = generated[f"{slug}/index.html"].decode()
    root = corpus["tags"][corpus["root_names"][-1]]
    theorem = generated[f"{slug}/explorer/defined/tag/{root}.html"].decode()
    assert "OPEN" in landing
    assert "OPEN" in theorem
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
def test_corrupt_transport_release_rows_and_receipts_fail_closed(
    inputs: dict, mutation: str,
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
        row["dependencies"] = ["forged_dependency"]
    elif mutation == "source":
        row["source"]["path"] = "missing.py"
    elif mutation == "checked-use":
        row["checked_use"] = False
    elif mutation == "stable":
        row["membership"] = "stable"
    elif mutation == "campaign":
        row["frontier_campaign"] = "euclidean_gcd_transport"
    elif mutation == "bundle-campaign":
        row["empty_context_closure"]["bundle_campaign"] = "advanced_layer"
    elif mutation == "bundle-node":
        row["empty_context_closure"]["bundle_node_id"] = 240
    else:
        row["alpha_v22_frontier_enrollment"]["bundle_sha256"] = "0" * 64
    with pytest.raises(explorer.TransportLayerExplorerError):
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
    inputs: dict, mutation: str,
) -> None:
    family = explorer.FAMILIES[0]
    altered = dict(inputs)
    altered["global_graph"] = deepcopy(inputs["global_graph"])
    target = next(
        item for item in altered["global_graph"]["reviewed_definitions"]
        if item["name"] == "PowTwo"
    )
    if mutation == "identity":
        target["id"] = "ND0029"
    elif mutation == "global-id":
        match = next(
            item for item in altered["global_graph"]["compatible_reviewed_matches"]
            if item["blueprint_name"] == "PowTwo"
        )
        match["reviewed_id"] = "ND0029"
    elif mutation == "global-template":
        target["expansion_sha256"] = "0" * 64
    elif mutation == "global-signature":
        altered["blueprint"] = deepcopy(inputs["blueprint"])
        altered["blueprint"]["PowTwo"]["parameters"] = ["e"]
    elif mutation == "route":
        target["route"] = "euclidean-gcd-transport"
    else:
        target["dependencies"] = ["BinaryDigit"]
    with pytest.raises(explorer.TransportLayerExplorerError):
        explorer._definition_records(family, altered)


def test_transport_explorer_never_decodes_checks_or_replays_a_proof_bundle() -> None:
    source = (SCRIPTS / "build_constructive_transport_layer_explorer.py").read_text()
    assert "decode_proof_bundle(" not in source
    assert "checked_transport_layer_bundle(" not in source
    assert "replay_candidate_bodies(" not in source
    assert "compile_layered_replay(" not in source


def test_three_family_output_is_deterministically_generated_and_stale_checked(
    generated: dict[str, bytes], tmp_path: Path,
) -> None:
    explorer._write(tmp_path, generated)
    assert explorer._check(tmp_path, generated)
    (tmp_path / "index.html").write_bytes(b"corrupt")
    assert not explorer._check(tmp_path, generated)


def test_public_transport_explorer_snapshot_is_fresh() -> None:
    result = subprocess.run(
        ["python3", str(SCRIPTS / "build_constructive_transport_layer_explorer.py"), "--check"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "60 checked theorems" in result.stdout
