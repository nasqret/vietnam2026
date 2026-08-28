"""Fail-closed audit of four historical Alpha-v20 / current Alpha-v30 explorers.

These documentation tests never decode, construct, replay, or check a proof
bundle. Original admission remains solely with the immutable Alpha-v20 proof;
the explorer additionally authenticates current Alpha-v30 checked authority.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import html
from html.parser import HTMLParser
import importlib
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_constructive_next_layer_explorer as explorer  # noqa: E402
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS,
    NEXT_LAYER_DEFINITIONS_BY_NAME,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.kernel.terms import ParseError  # noqa: E402


EXPECTED = {
    "polynomial-horner": (7, "D04", "F10", ("T12",)),
    "matrix-dot-product": (10, "D05", "F12", ("T13",)),
    "bertrand-prime-chains": (13, "D02", "F03", ("G023", "G024")),
    "continued-fractions": (9, "D03", "F08", ("G071",)),
}


@pytest.fixture(scope="module")
def generated() -> dict[str, bytes]:
    return explorer.build_files()


@pytest.fixture(scope="module")
def inputs() -> dict[str, Any]:
    return explorer._load_inputs()


@pytest.fixture(scope="module")
def corpora(generated: dict[str, bytes]) -> dict[str, dict[str, Any]]:
    return {
        slug: json.loads(generated[f"{slug}/api/corpus.json"])
        for slug in EXPECTED
    }


def test_manifest_is_bound_to_current_v30_and_immutable_v20_first_admission(
    generated: dict[str, bytes], inputs: dict[str, Any]
) -> None:
    manifest = json.loads(generated["manifest.json"])
    actual_catalog = explorer.CURRENT_CATALOG.read_bytes()
    assert manifest["catalog_sha256"] == sha256(actual_catalog).hexdigest()
    assert manifest["first_enrollment_catalog_sha256"] == sha256(
        explorer.CATALOG.read_bytes()
    ).hexdigest()
    assert manifest["html_revision"] == sha256(actual_catalog).hexdigest()[:12]
    assert manifest["edition_identity_sha256"] == inputs["current_edition_identity_sha256"]
    assert manifest["alpha_edition_version"] == "v30"
    assert manifest["alpha_first_enrolled_version"] == "v20"
    assert manifest["proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 39
    assert manifest["stable_count"] == 0
    assert manifest["file_count"] + 1 == len(generated)
    assert {row["slug"]: row["theorem_count"] for row in manifest["families"]} == {
        slug: data[0] for slug, data in EXPECTED.items()
    }
    for item in manifest["files"]:
        payload = generated[item["path"]]
        assert item["bytes"] == len(payload)
        assert item["sha256"] == sha256(payload).hexdigest()


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_historical_v20_family_landing_reuses_quadratic_reciprocity_structure(
    slug: str,
    generated: dict[str, bytes],
    corpora: dict[str, dict[str, Any]],
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
    assert "Alpha v30 checked-use theorem family" in source
    assert "first admitted v20" in source
    assert "independently accept all 590 bundle nodes" in source
    assert corpus["alpha_proof_bundle_sha256"] in source
    assert family.caveat in html.unescape(source)
    for root in family.roots:
        tag = corpus["tags"][root]
        assert f'explorer/defined/tag/{tag}.html?v={revision}' in source


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_family_boundaries_and_exact_checked_release_rows(
    slug: str,
    corpora: dict[str, dict[str, Any]],
    inputs: dict[str, Any],
) -> None:
    corpus = corpora[slug]
    count, domain, family, milestones = EXPECTED[slug]
    assert corpus["node_count"] == count
    assert corpus["alpha_checked_use_node_count"] == count
    assert corpus["alpha_enrolled_node_count"] == count
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["campaign_domain_id"] == domain
    assert corpus["campaign_family_id"] == family
    assert tuple(corpus["campaign_milestone_ids"]) == milestones
    assert corpus["alpha_edition_version"] == "v30"
    assert corpus["alpha_first_enrolled_version"] == "v20"
    assert corpus["alpha_proof_bundle_sha256"] == inputs["bundle"]["artifact_sha256"]
    assert corpus["independent_lean_bundle_verified"] is True
    for node in corpus["nodes"]:
        original = inputs["by_name"][node["name"]]
        closure = original["empty_context_closure"]
        assert node["statement"] == original["statement"]
        assert node["statement_sha256"] == original["statement_sha256"]
        assert node["script"] == original["script"]
        assert node["dependencies"] == original["dependencies"]
        assert node["proof_bundle_node_id"] == closure["bundle_node_id"]
        assert node["proof_bundle_sha256"] == closure["certificate_sha256"]
        assert node["body_proof_nodes"] == closure["body_proof_nodes"]
        assert node["body_proof_depth"] == closure["body_proof_depth"]
        assert node["sources"][0]["script_sha256"] == original["script_sha256"]
        assert node["alpha_checked_use"] is True
        assert node["alpha_edition_version"] == "v30"
        assert node["alpha_first_enrolled_version"] == "v20"
        assert node["independent_lean_bundle_verified"] is True
        assert node["stable_member"] is False
        assert node["admitted_to_stable"] is False


def test_major_milestone_tags_are_stable_and_exact(corpora: dict[str, dict[str, Any]]) -> None:
    expected = {
        ("polynomial-horner", "beta_horner_eval_exists"): "PH0002",
        ("matrix-dot-product", "beta_dot_product_exists_unique"): "MD0006",
        ("bertrand-prime-chains", "central_binom_prime_divisor_multiplicity_one_exists"): "BP0007",
        ("bertrand-prime-chains", "iterated_bertrand_prime_chain_exists"): "BP000D",
        ("continued-fractions", "continued_fraction_positive_exists"): "CF0009",
    }
    for (slug, theorem), tag in expected.items():
        assert corpora[slug]["tags"][theorem] == tag
        assert theorem in corpora[slug]["root_names"]


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_definitions_are_hygienic_dependency_first_and_signature_checked(
    slug: str,
    corpora: dict[str, dict[str, Any]],
    inputs: dict[str, Any],
) -> None:
    corpus = corpora[slug]
    definitions = {row["id"]: row for row in corpus["definitions"]}
    assert len(definitions) == corpus["definition_count"]
    assert corpus["definition_topological_order"] == list(definitions)
    seen: set[str] = set()
    for row in corpus["definitions"]:
        assert set(row["dependencies"]) <= seen
        assert row["arity"] == len(row["parameters"])
        assert row["expanded_template"]
        assert row["expansion_sha256"] == sha256(
            row["expanded_template"].encode()
        ).hexdigest()
        assert row["exact_ast_verified"] is True
        assert row["kernel_signature_unchanged"] is True
        if row["id"].startswith("ND"):
            assert row["shared_definition_identity"] == row["id"]
            assert row["reviewed_definition_route"]
            assert explorer._definition_specs()[row["name"]] is (
                NEXT_LAYER_DEFINITIONS_BY_NAME[row["name"]]
            )
            expected_reviewed_id = "PD0013" if row["name"] == "Beta" else row["id"]
            assert row["reviewed_definition_id"] == expected_reviewed_id
        assert parse_formula_in_context(
            row["expanded_template"], list(row["parameters"])
        ) == explorer._definition_specs()[row["name"]].template_formula
        assert row["topological_layer"] == max(
            (
                definitions[dependency]["topological_layer"] + 1
                for dependency in row["dependencies"]
            ),
            default=0,
        )
        closure = set(row["dependencies"])
        for dependency in row["dependencies"]:
            closure.update(definitions[dependency]["transitive_dependencies"])
        assert row["transitive_dependencies"] == sorted(closure)
        if row["global_definition"] is not None:
            global_row = inputs["blueprint"][row["global_definition"]]
            assert len(global_row["parameters"]) == row["arity"]
            assert sorted(row["global_argument_positions"]) == list(range(row["arity"]))
        seen.add(row["id"])


def test_new_definition_names_have_exact_arity_and_real_dependencies(
    corpora: dict[str, dict[str, Any]],
) -> None:
    expected = {
        "Beta": (4, ()),
        "Horner": (5, ("Beta", "Lt")),
        "MatrixAt": (6, ("Beta",)),
        "DotProduct": (6, ("Beta", "Lt", "Sum")),
        "SignedDet2": (6, ()),
        "BertrandWindow": (2, ("Prime", "Lt")),
        "PowerValuationOne": (2, ("PowerValuation",)),
        "BertrandChain": (4, ("Beta", "Lt", "BertrandWindow")),
        "ListCell": (3, ()),
        "ContinuedFractionTrace": (6, ("Beta", "Lt", "ListCell")),
        "ContinuedFraction": (3, ("ContinuedFractionTrace",)),
    }
    found = {
        row["name"]: row
        for corpus in corpora.values()
        for row in corpus["definitions"]
        if row["id"].startswith("ND")
    }
    assert set(found) == set(expected)
    for name, (arity, dependencies) in expected.items():
        assert found[name]["arity"] == arity
        assert tuple(found[name]["dependency_names"]) == dependencies
    assert found["Beta"]["reviewed_definition_id"] == "PD0013"
    assert len(NEXT_LAYER_DEFINITIONS) == len(found) == 11


def test_all_eight_blueprint_matches_share_exact_global_nd_registry_identity(
    corpora: dict[str, dict[str, Any]], inputs: dict[str, Any]
) -> None:
    reviewed = {
        row["name"]: row for row in inputs["global_graph"]["reviewed_definitions"]
    }
    matches = {
        row["blueprint_name"]: row
        for row in inputs["global_graph"]["compatible_reviewed_matches"]
    }
    expected = {
        "Horner": "ND0002",
        "MatrixAt": "ND0003",
        "DotProduct": "ND0004",
        "SignedDet2": "ND0005",
        "BertrandWindow": "ND0006",
        "PowerValuationOne": "ND0007",
        "BertrandChain": "ND0008",
        "ContinuedFraction": "ND0011",
    }
    rows = {
        item["name"]: item
        for corpus in corpora.values()
        for item in corpus["definitions"]
    }
    for name, identifier in expected.items():
        row = rows[name]
        match = matches[name]
        record = reviewed[name]
        assert row["id"] == row["reviewed_definition_id"] == identifier
        assert match["reviewed_id"] == record["id"] == identifier
        assert row["reviewed_definition_route"] == match["route"] == record["route"]
        assert row["expansion_sha256"] == record["expansion_sha256"]
        assert tuple(row["dependency_names"]) == tuple(record["dependencies"])
        assert NEXT_LAYER_DEFINITIONS_BY_NAME[name] is explorer._definition_specs()[name]


def test_four_argument_sum_uses_exact_beta_sum_not_incompatible_global_sum(
    corpora: dict[str, dict[str, Any]], inputs: dict[str, Any]
) -> None:
    matrix = {row["name"]: row for row in corpora["matrix-dot-product"]["definitions"]}
    assert matrix["Sum"]["arity"] == 4
    assert len(inputs["blueprint"]["Sum"]["parameters"]) == 3
    assert matrix["Sum"]["global_definition"] == "BetaSum"
    assert matrix["Sum"]["global_argument_positions"] == [0, 1, 2, 3]
    assert len(inputs["blueprint"]["BetaSum"]["parameters"]) == 4


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_every_compact_statement_expands_to_identical_original_formula(
    slug: str, corpora: dict[str, dict[str, Any]]
) -> None:
    corpus = corpora[slug]
    definitions = {
        record["name"]: explorer._definition_specs()[record["name"]]
        for record in corpus["definitions"]
    }
    for node in corpus["nodes"]:
        record = node["defined"]
        parser = explorer._LocalDefinedParser(record["defined_statement"], definitions)
        parser.free = list(record["free_names"])
        expanded = parser.parse()
        assert expanded == parse_formula_in_context(
            node["statement"], list(record["free_names"])
        )
        assert record["exact_ast_equivalence"] is True
        assert record["expanded_statement_sha256"] == node["statement_sha256"]
        assert Counter(
            part["definition"]
            for part in record["statement_parts"]
            if part["kind"] == "definition"
        ) == record["statement_definition_uses"]


@pytest.mark.parametrize(
    "source",
    (
        "Horner(a,b,c,d)",
        "Horner(a,b,c,d,e,f)",
        "UnknownDefinition(a)",
        "MatrixAt(a,b,c,d,e,f)",
    ),
)
def test_local_parser_rejects_wrong_arity_unknown_or_cross_family_symbols(source: str) -> None:
    definitions = {
        spec.name: spec
        for spec in explorer._definition_closure(explorer.FAMILIES[0].definitions)
    }
    with pytest.raises(ParseError):
        explorer._LocalDefinedParser(source, definitions).parse()


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_interactive_graph_contains_only_real_typed_edges_and_proof_paths(
    slug: str,
    generated: dict[str, bytes],
    corpora: dict[str, dict[str, Any]],
) -> None:
    corpus = corpora[slug]
    graph = json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
    nodes = {row["id"]: row for row in graph["nodes"]}
    assert graph["alpha_checked_use_node_count"] == corpus["node_count"]
    assert graph["independent_lean_bundle_verified"] is True
    assert graph["stable_admitted_node_count"] == 0
    assert graph["path_policy"] == "proof_dependency_edges_only"
    assert graph["definition_topological_order"] == corpus["definition_topological_order"]
    kinds = Counter(edge["kind"] for edge in graph["edges"])
    assert kinds["proof_dependency"] == corpus["internal_edge_count"]
    assert kinds["definition_uses_definition"] == corpus["definition_dependency_count"]
    assert kinds["uses_definition"] == corpus["statement_definition_use_count"]
    for edge in graph["edges"]:
        assert edge["source"] in nodes and edge["target"] in nodes
        if edge["kind"] == "proof_dependency":
            assert nodes[edge["source"]]["kind"] == "theorem"
            assert nodes[edge["target"]]["kind"] == "theorem"
            source = nodes[edge["source"]]["name"]
            target = nodes[edge["target"]]["name"]
            theorem = next(row for row in corpus["nodes"] if row["name"] == target)
            assert source in theorem["dependencies"]
            assert nodes[edge["source"]]["layer"] < nodes[edge["target"]]["layer"]
        elif edge["kind"] == "uses_definition":
            assert nodes[edge["source"]]["kind"] == "theorem"
            assert nodes[edge["target"]]["kind"] == "definition"
            assert edge["occurrence_count"] == edge["statement_occurrences"] > 0
            assert edge["local_proposition_occurrences"] == 0
        else:
            assert edge["kind"] == "definition_uses_definition"
            assert nodes[edge["source"]]["kind"] == "definition"
            assert nodes[edge["target"]]["kind"] == "definition"
            assert nodes[edge["source"]]["layer"] > nodes[edge["target"]]["layer"]
    for tag, row in graph["proof_adjacency"].items():
        path = row["critical_root_path"]
        assert path[-1] == tag
        assert all(nodes[item]["kind"] == "theorem" for item in path)
        assert all(
            any(
                edge["kind"] == "proof_dependency"
                and edge["source"] == before and edge["target"] == after
                for edge in graph["edges"]
            )
            for before, after in zip(path, path[1:])
        )


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_all_theorem_definition_graph_and_atlas_pages_are_navigable(
    slug: str,
    generated: dict[str, bytes],
    corpora: dict[str, dict[str, Any]],
) -> None:
    corpus = corpora[slug]
    _count, domain, family, milestones = EXPECTED[slug]
    for node in corpus["nodes"]:
        tag = corpus["tags"][node["name"]]
        for relative in (f"explorer/tag/{tag}.html", f"explorer/defined/tag/{tag}.html"):
            document = generated[f"{slug}/{relative}"].decode()
            assert html.escape(node["name"]) in document
            assert node["statement_sha256"] in document
            assert f"focus={domain}" in html.unescape(document)
            assert f"focus={family}" in html.unescape(document)
            assert f"focus={node['campaign_milestone']}" in html.unescape(document)
            assert "independently" in document
            assert "Stable" in document
        defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
        assert node["proof_bundle_sha256"] in defined
        assert f"{node['proof_bundle_node_id']} / 590" in defined
        assert "compiled verifier accepted all 590 exact bundle nodes" in defined
        assert defined.count('class="pd-proof-line"') == len(node["script"])

    for definition in corpus["definitions"]:
        document = generated[
            f"{slug}/explorer/defined/definition/{definition['id']}.html"
        ].decode()
        assert html.escape(definition["signature"]) in document
        assert definition["expansion_sha256"] in document
        assert "not a theorem, primitive, or axiom" in document
        if definition["global_definition"] is not None:
            assert f"focus={definition['global_definition']}" in html.unescape(document)
        else:
            assert 'data-campaign-link="definition"' not in document

    graph = generated[f"{slug}/explorer/defined/graph.html"].decode()
    assert "window.PA_DEFINED_GRAPH=" in graph
    assert "Alpha v30 checked-use theorem" in graph
    assert "first admitted v20" in graph
    assert "independently kernel and Lean verified" in graph
    assert "proof_dependency" in graph
    assert "definition_uses_definition" in graph
    assert all(f"focus={milestone}" in html.unescape(graph) for milestone in milestones)


def test_matrix_explorer_links_new_full_t13_without_upgrading_old_components(
    generated: dict[str, bytes], corpora: dict[str, dict[str, Any]]
) -> None:
    slug = "matrix-dot-product"
    landing = generated[f"{slug}/index.html"].decode()
    assert "Historical partial components only" in landing
    assert "T13 is now closed" in landing
    assert "integer-linear-algebra/" in landing
    assert 'data-current-milestone="T13"' in landing
    assert "lattice index or normal-form" in landing
    assert corpora[slug]["historical_component_only"] is True
    assert corpora[slug]["historical_milestone_status"] == "open"
    assert corpora[slug]["milestone_status"] == "alpha_closed"
    assert "rectangular_matrix_rank_exists_unique" not in corpora[slug]["tags"]
    for node in corpora[slug]["nodes"]:
        tag = corpora[slug]["tags"][node["name"]]
        defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
        assert "Historical partial components only" in defined
        assert "do not themselves establish the full T13 substrate" in defined
        assert "Full T13 proof · Alpha v27" in defined
        assert "integer-linear-algebra/" in defined


@pytest.mark.parametrize(
    ("section", "key", "value"),
    (
        (None, "checked_use", False),
        (None, "evidence_status", "body_checked"),
        (None, "statement_sha256", "0" * 64),
        ("empty_context_closure", "status", "unchecked"),
        ("empty_context_closure", "kernel_mode", "classical"),
        ("empty_context_closure", "bundle_node_id", 590),
        ("empty_context_closure", "certificate_sha256", "0" * 64),
        ("empty_context_closure", "node_statement_sha256", "0" * 64),
        ("alpha_v20_frontier_enrollment", "bundle_sha256", "0" * 64),
        ("alpha_v20_frontier_enrollment", "campaign", "bertrand_prime"),
    ),
)
def test_mutated_release_receipt_is_rejected_before_publication(
    section: str | None, key: str, value: object, inputs: dict[str, Any]
) -> None:
    enrollment = inputs["enrollment"]
    spec = enrollment.frontier_specs[0]
    row = deepcopy(inputs["by_name"][spec.name])
    if section is None:
        row[key] = value
    else:
        row[section][key] = value
    with pytest.raises(explorer.NextLayerExplorerError):
        explorer._validate_theorem(
            row,
            spec=spec,
            campaign=enrollment.campaign_by_name[spec.name],
            source=enrollment.source_by_name[spec.name],
            bundle=inputs["bundle"],
        )


def test_circular_unknown_and_wrong_blueprint_definitions_are_rejected(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(explorer.NextLayerExplorerError, match="unknown"):
        explorer._definition_closure(("UnreviewedMagic",))

    registry = dict(explorer._definition_specs())
    registry["Horner"] = replace(
        registry["Horner"], conceptual_dependencies=("Horner",)
    )
    monkeypatch.setattr(explorer, "_definition_specs", lambda: registry)
    with pytest.raises(explorer.NextLayerExplorerError, match="circular"):
        explorer._definition_closure(("Horner",))


def test_blueprint_signature_mutation_is_fail_closed(
    inputs: dict[str, Any]
) -> None:
    broken = dict(inputs)
    broken["blueprint"] = deepcopy(inputs["blueprint"])
    broken["blueprint"]["Horner"]["parameters"].append("spurious")
    with pytest.raises(explorer.NextLayerExplorerError, match="arity"):
        explorer._definition_records(explorer.FAMILIES[0], broken)


def test_assets_are_exact_reviewed_immutable_explorer_assets(
    generated: dict[str, bytes]
) -> None:
    for name, expected in explorer.PINNED_ASSETS.items():
        assert sha256(generated[f"assets/{name}"]).hexdigest() == expected
    javascript = generated["assets/defined-explorer.js"].decode()
    assert 'open.setAttribute("href", node.href)' in javascript
    assert "open.href = node.href" not in javascript


def test_reproducible_write_and_fail_closed_stale_detection(
    generated: dict[str, bytes], tmp_path: Path
) -> None:
    explorer._write(tmp_path, generated)
    assert explorer._check(tmp_path, generated)
    changed = tmp_path / "matrix-dot-product" / "index.html"
    changed.write_bytes(changed.read_bytes() + b"unaudited mutation")
    assert not explorer._check(tmp_path, generated)
    explorer._write(tmp_path, generated)
    assert explorer._check(tmp_path, generated)
    assert explorer._check(explorer.OUTPUT, generated)


class _GraphContract(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.attributes: list[set[str]] = []

    def handle_starttag(self, _tag: str, attributes: list[tuple[str, str | None]]) -> None:
        self.attributes.append({key for key, _ in attributes})


@pytest.mark.parametrize("slug", tuple(EXPECTED))
def test_graph_html_supplies_every_required_shared_interaction_contract(
    slug: str, generated: dict[str, bytes]
) -> None:
    parser = _GraphContract()
    parser.feed(generated[f"{slug}/explorer/defined/graph.html"].decode())
    present = set().union(*parser.attributes)
    assert {
        "data-defined-graph",
        "data-graph-form",
        "data-graph-target",
        "data-graph-view",
        "data-graph-definitions",
        "data-graph-edges",
        "data-graph-summary",
        "data-graph-svg",
        "data-graph-title",
        "data-graph-kind",
        "data-graph-description",
        "data-graph-metadata",
        "data-graph-open",
        "data-graph-outgoing",
        "data-graph-incoming",
        "data-graph-fit",
        "data-graph-zoom",
    } <= present


@pytest.mark.parametrize("slug", tuple(EXPECTED))
@pytest.mark.parametrize("focus_kind", ("theorem", "definition"))
def test_actual_shared_graph_renders_each_checked_family_and_firefox_svg_links(
    slug: str,
    focus_kind: str,
    generated: dict[str, bytes],
    corpora: dict[str, dict[str, Any]],
) -> None:
    """Run every real mixed DAG through the reviewed browser JavaScript."""

    page = generated[f"{slug}/explorer/defined/graph.html"].decode()
    assignment = re.search(
        r'<script id="pa-defined-graph-data">\s*window\.PA_DEFINED_GRAPH=(\{.*?\});\s*</script>',
        page, re.DOTALL,
    )
    assert assignment is not None
    payload = json.loads(assignment.group(1))
    assert payload == json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
    target = corpora[slug]["tags"][corpora[slug]["root_names"][-1]]
    focus = (
        target if focus_kind == "theorem"
        else corpora[slug]["definitions"][-1]["id"]
    )
    harness = (
        f"const payload = {json.dumps(payload)};\n"
        f"const selectedTarget = {json.dumps(target)};\n"
        f"const selectedFocus = {json.dumps(focus)};\n"
        + r"""
const svgAnchors = [];
class Element {
  constructor(name, namespace = "html") {
    this.name = name;
    this.namespace = namespace;
    this.attributes = {};
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.textContent = "";
    this.value = "";
    this.clientWidth = 960;
    this.clientHeight = 640;
    this.classList = {add() {}, remove() {}, contains() { return false; }};
    this.parentElement = {classList: this.classList};
    if (namespace === "svg" && name === "a") {
      Object.defineProperty(this, "href", {
        enumerable: true,
        get: () => ({baseVal: this.attributes.href || ""})
      });
      svgAnchors.push(this);
    }
  }
  get firstChild() { return this.children[0] || null; }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "data-graph-node") this.dataset.graphNode = String(value);
  }
  appendChild(child) {
    child.parentElement = this;
    this.children.push(child);
    return child;
  }
  removeChild(child) {
    this.children.splice(this.children.indexOf(child), 1);
    return child;
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  focus() {}
}
const sidebarAnchor = new Element("a");
const svg = new Element("svg", "svg");
const title = new Element("h2");
const summary = new Element("p");
const selectors = new Map([
  ["[data-graph-summary]", summary],
  ["[data-graph-svg]", svg],
  ["[data-graph-target]", new Element("input")],
  ["[data-graph-view]", new Element("select")],
  ["[data-graph-definitions]", new Element("select")],
  ["[data-graph-edges]", new Element("select")],
  ["#pd-graph-theorems", new Element("datalist")],
  ["[data-graph-form]", new Element("form")],
  ["[data-graph-zoom='in']", new Element("button")],
  ["[data-graph-zoom='out']", new Element("button")],
  ["[data-graph-fit]", new Element("button")],
  ["[data-graph-title]", title],
  ["[data-graph-kind]", new Element("p")],
  ["[data-graph-description]", new Element("p")],
  ["[data-graph-metadata]", new Element("dl")],
  ["[data-graph-outgoing]", new Element("ul")],
  ["[data-graph-incoming]", new Element("ul")]
]);
const root = new Element("main");
root.querySelector = function (selector) {
  if (selector === "[data-graph-open]") return svgAnchors[0] || sidebarAnchor;
  if (selector === ".pd-graph-details [data-graph-open]") return sidebarAnchor;
  if (!selectors.has(selector)) throw new Error("Unexpected selector " + selector);
  return selectors.get(selector);
};
global.document = {
  readyState: "complete",
  body: {classList: {contains(name) { return name === "pa-defined-proof-site"; }}},
  createElement(name) { return new Element(name); },
  createElementNS(_namespace, name) { return new Element(name, "svg"); },
  createTextNode(value) { return {textContent: String(value)}; },
  getElementById() { return null; },
  querySelectorAll(selector) {
    return selector === "[data-defined-graph]" ? [root] : [];
  }
};
global.window = {
  PA_DEFINED_GRAPH: payload,
  location: {
    href: "https://proofs.example/graph.html?target=" + selectedTarget + "&focus=" + selectedFocus,
    hash: ""
  },
  history: {replaceState() {}},
  requestAnimationFrame(callback) { callback(); },
  addEventListener() {}
};
"""
        + generated["assets/defined-explorer.js"].decode()
        + r"""
const svgHref = Object.getOwnPropertyDescriptor(svgAnchors[0], "href");
process.stdout.write(JSON.stringify({
  sidebarHref: sidebarAnchor.attributes.href,
  sidebarLabel: sidebarAnchor.textContent,
  title: title.textContent,
  summary: summary.textContent,
  svgAnchorCount: svgAnchors.length,
  getterOnlySvgHref: typeof svgHref.get === "function" && svgHref.set === undefined,
  viewportRendered: svg.attributes.viewBox !== undefined
}));
"""
    )
    result = json.loads(
        subprocess.run(
            ["node", "-e", harness], check=True, text=True, capture_output=True
        ).stdout
    )
    selected = next(row for row in payload["nodes"] if row["id"] == focus)
    assert result["title"] == f"{focus} · {selected['name']}"
    assert result["sidebarHref"] == selected["href"]
    assert result["sidebarLabel"] == (
        "Open theorem →" if focus_kind == "theorem" else "Open definition →"
    )
    assert result["svgAnchorCount"] > 0
    assert result["getterOnlySvgHref"] is True
    assert result["viewportRendered"] is True
    assert "theorem nodes" in result["summary"]


@pytest.mark.parametrize("mutation", ("version", "checked_count", "blueprint_count", "reviewed_count", "snapshot", "edge", "authority"))
def test_current_atlas_accepts_only_the_exact_additive_graph(mutation: str) -> None:
    campaign = json.loads(explorer.CAMPAIGN.read_text())
    graph = json.loads(explorer.GLOBAL_DEFINITIONS.read_text())
    explorer._audit_current_atlas(campaign, graph)
    # Current checked-use authority does not relabel historical first admission.
    assert explorer.CURRENT_CATALOG.name == "catalog-v30.json"
    assert explorer.CATALOG.name == "catalog-v20.json"
    if mutation == "version":
        campaign["meta"]["current_alpha_version"] = "v25"
    elif mutation == "checked_count":
        campaign["meta"]["current_alpha_checked_use_count"] = 2_080
    elif mutation == "blueprint_count":
        graph["definition_count"] -= 1
    elif mutation == "reviewed_count":
        graph["reviewed_definition_count"] -= 1
    elif mutation == "snapshot":
        graph["campaign_snapshot_sha256"] = "0" * 64
    elif mutation == "edge":
        graph["definition_edges"][0]["target"] = "MissingDefinition"
    else:
        graph["authority_policy"]["notation_edges"] = "notation grants theorem authority"
    with pytest.raises(explorer.NextLayerExplorerError, match="atlas definition artifact"):
        explorer._audit_current_atlas(campaign, graph)


CURRENT_RELEASE_PUBLISHERS = (
    ("build_constructive_next_layer_explorer", "NextLayerExplorerError", "v20"),
    ("build_constructive_advanced_layer_explorer", "AdvancedLayerExplorerError", "v21"),
    ("build_constructive_transport_layer_explorer", "TransportLayerExplorerError", "v22"),
    ("build_constructive_milestone_closure_explorer", "MilestoneClosureExplorerError", "v23"),
)


@pytest.mark.parametrize(("module_name", "error_name", "first_version"), CURRENT_RELEASE_PUBLISHERS)
def test_current_v30_publishers_preserve_the_full_first_admission_catalog(
    module_name: str, error_name: str, first_version: str
) -> None:
    publisher = importlib.import_module(module_name)
    inputs = publisher._load_inputs()
    channels = json.loads(publisher.CURRENT_CHANNELS.read_text())
    current = inputs["current_catalog"]
    assert publisher.CATALOG.name == f"catalog-{first_version}.json"
    assert publisher.CURRENT_CATALOG.name == "catalog-v30.json"
    assert publisher.CURRENT_CHANNELS.name == "channels-v30.json"
    assert current["schema"] == "peano-library-alpha-snapshot-v30"
    assert current["theorem_count"] == current["checked_use_count"] == (
        publisher.current_alpha.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
    )
    assert current["stable_count"] == 432
    assert current["theorems"][:publisher.EXPECTED_ALPHA_COUNT] == inputs["catalog"]["theorems"]
    assert inputs["catalog"]["schema"] == f"peano-library-alpha-snapshot-{first_version}"
    assert channels["parent_channels_v29"] == {
        "path": "artifacts/peano-library/channels-v29.json",
        "sha256": sha256(
            (ROOT / "artifacts/peano-library/channels-v29.json").read_bytes()
        ).hexdigest(),
    }
    for spec in inputs["enrollment"].frontier_specs:
        checked = publisher.current_alpha.entry(spec.name, edition="alpha")
        assert checked is not None and checked.checked_use
        assert checked.spec == spec


@pytest.mark.parametrize(("module_name", "error_name", "first_version"), CURRENT_RELEASE_PUBLISHERS)
@pytest.mark.parametrize(
    "mutation",
    (
        "channels_schema", "parent_path", "parent_digest", "catalog_digest",
        "catalog_schema", "theorem_count", "checked_count", "edition_identity",
        "enrollment_identity", "inherited_statement", "inherited_script",
        "inherited_body_digest", "inherited_order",
    ),
)
def test_current_publishers_reject_mutated_release_or_historical_proof_rows(
    module_name: str,
    error_name: str,
    first_version: str,
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = importlib.import_module(module_name)
    catalog = json.loads(publisher.CURRENT_CATALOG.read_bytes())
    channels = json.loads(publisher.CURRENT_CHANNELS.read_text())
    if mutation == "channels_schema":
        channels["schema"] = "peano-library-channels-v25"
    elif mutation == "parent_path":
        channels["parent_channels_v29"]["path"] = "artifacts/peano-library/channels-v24.json"
    elif mutation == "parent_digest":
        channels["parent_channels_v29"]["sha256"] = "0" * 64
    elif mutation == "catalog_schema":
        catalog["schema"] = f"peano-library-alpha-snapshot-{first_version}"
    elif mutation == "theorem_count":
        catalog["theorem_count"] -= 1
    elif mutation == "checked_count":
        catalog["checked_use_count"] -= 1
    elif mutation == "edition_identity":
        catalog["edition_identity_sha256"] = "0" * 64
    elif mutation == "enrollment_identity":
        catalog["ordered_enrollment_root_sha256"] = "0" * 64
    elif mutation == "inherited_statement":
        catalog["theorems"][0]["statement"] = "0 = S 0"
    elif mutation == "inherited_script":
        catalog["theorems"][0]["script"] = ["exact fabricated_proof"]
    elif mutation == "inherited_body_digest":
        catalog["theorems"][0]["empty_context_closure"]["certificate_sha256"] = "0" * 64
    elif mutation == "inherited_order":
        catalog["theorems"][0], catalog["theorems"][1] = catalog["theorems"][1], catalog["theorems"][0]

    # Simulate changed file bytes with a matching channel checksum: metadata
    # and complete historical rows must still authenticate independently.
    catalog_bytes = json.dumps(catalog).encode()
    catalog_digest = sha256(catalog_bytes).hexdigest()
    channels["channels"]["alpha"]["artifact_sha256"] = (
        "0" * 64 if mutation == "catalog_digest" else catalog_digest
    )
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    original_file_digest = publisher._file_digest

    def read_bytes(path: Path) -> bytes:
        return catalog_bytes if path == publisher.CURRENT_CATALOG else original_read_bytes(path)

    def read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        return json.dumps(channels) if path == publisher.CURRENT_CHANNELS else original_read_text(path, *args, **kwargs)

    def file_digest(path: Path) -> str:
        return catalog_digest if path == publisher.CURRENT_CATALOG else original_file_digest(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(publisher, "_file_digest", file_digest)
    with pytest.raises(getattr(publisher, error_name), match="current immutable Alpha-v30"):
        publisher._load_inputs()


def test_v30_retains_exact_v29_v28_v27_v26_objects_all_old_receipts_and_channel_ancestry(inputs: dict) -> None:
    catalog = inputs["current_catalog"]
    channels = json.loads(explorer.CURRENT_CHANNELS.read_bytes())
    # Audit before loading additional comparison copies, then retain only one
    # old catalogue at a time. Every prefix, object, receipt and Stable check
    # is unchanged; unrelated parsed parent copies need not coexist.
    explorer._audit_current_parent(catalog, channels)
    older_channels = json.loads((ROOT / "artifacts/peano-library/channels-v25.json").read_bytes())
    for version, edition, count in (
        ("v26", explorer.v26, 2138), ("v27", explorer.v27, 2560),
        ("v28", explorer.v28, 2764), ("v29", explorer.v29, 3042),
    ):
        recent = json.loads((ROOT / f"artifacts/peano-library/alpha/catalog-{version}.json").read_bytes())
        recent_channels = json.loads((ROOT / f"artifacts/peano-library/channels-{version}.json").read_bytes())
        assert catalog["theorems"][:count] == recent["theorems"]
        assert len(edition.ALPHA_ENTRIES) == count
        assert all(
            current is historical
            for current, historical in zip(explorer.current_alpha.ALPHA_ENTRIES, edition.ALPHA_ENTRIES)
        )
        assert channels["channels"]["stable"] == recent_channels["channels"]["stable"]
        if version == "v26":
            assert recent_channels["channels"]["stable"] == older_channels["channels"]["stable"]
        for key in recent:
            if key.startswith("parent_alpha_") or key.endswith("_promotion"):
                assert catalog[key] == recent[key]
        del recent, recent_channels


@pytest.mark.parametrize("mutation", (
    "v29_catalog", "v29_channels", "v29_dependency_graph", "v29_metrics", "v29_bundle",
    "v28_catalog", "v28_channels", "v28_dependency_graph", "v28_metrics", "v28_bundle",
    "v27_catalog", "v27_channels", "v27_dependency_graph", "v27_metrics",
    "v26_catalog", "v26_channels", "v25_channels", "object_identity", "v27_object_identity",
    "v28_object_identity", "v29_object_identity",
))
def test_current_parent_audit_rejects_changes_beneath_the_new_channel(
    inputs: dict, mutation: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = inputs["current_catalog"]
    channels = json.loads(explorer.CURRENT_CHANNELS.read_bytes())
    if mutation.endswith("object_identity"):
        entries = list(explorer.current_alpha.ALPHA_ENTRIES)
        index, edition = {
            "object_identity": (0, explorer.v26),
            "v27_object_identity": (2138, explorer.v27),
            "v28_object_identity": (2560, explorer.v28),
            "v29_object_identity": (2764, explorer.v29),
        }[mutation]
        entries[index] = replace(entries[index])
        assert entries[index] == edition.ALPHA_ENTRIES[index]
        assert entries[index] is not edition.ALPHA_ENTRIES[index]
        monkeypatch.setattr(explorer.current_alpha, "ALPHA_ENTRIES", tuple(entries))
    else:
        path = ROOT / {
            "v29_catalog": "artifacts/peano-library/alpha/catalog-v29.json",
            "v29_channels": "artifacts/peano-library/channels-v29.json",
            "v29_dependency_graph": "artifacts/peano-library/alpha/dependency-graph-v29.mmd",
            "v29_metrics": "artifacts/peano-library/alpha/metrics-v29.json",
            "v29_bundle": "research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json",
            "v28_catalog": "artifacts/peano-library/alpha/catalog-v28.json",
            "v28_channels": "artifacts/peano-library/channels-v28.json",
            "v28_dependency_graph": "artifacts/peano-library/alpha/dependency-graph-v28.mmd",
            "v28_metrics": "artifacts/peano-library/alpha/metrics-v28.json",
            "v28_bundle": "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json",
            "v27_catalog": "artifacts/peano-library/alpha/catalog-v27.json",
            "v27_channels": "artifacts/peano-library/channels-v27.json",
            "v27_dependency_graph": "artifacts/peano-library/alpha/dependency-graph-v27.mmd",
            "v27_metrics": "artifacts/peano-library/alpha/metrics-v27.json",
            "v26_catalog": "artifacts/peano-library/alpha/catalog-v26.json",
            "v26_channels": "artifacts/peano-library/channels-v26.json",
            "v25_channels": "artifacts/peano-library/channels-v25.json",
        }[mutation]
        if mutation.endswith(("_dependency_graph", "_metrics", "_bundle")):
            # These artifacts are authenticated by the streaming hash reader,
            # so alter its actual byte stream rather than an unused read API.
            open_path = Path.open
            monkeypatch.setattr(
                Path, "open", lambda current, *args, **kwargs:
                BytesIO(b"{}\n") if current == path else open_path(current, *args, **kwargs),
            )
        else:
            read_bytes = Path.read_bytes
            monkeypatch.setattr(
                Path, "read_bytes", lambda current: b"{}\n" if current == path else read_bytes(current)
            )
    with pytest.raises(explorer.NextLayerExplorerError, match="v26/v25 ancestry"):
        explorer._audit_current_parent(catalog, channels)


@pytest.mark.parametrize("field", ("schema", "count", "identity", "enrollment", "catalog", "channels", "dependency_graph", "metrics", "extra"))
def test_current_parent_rejects_any_forged_v27_parent_record(inputs: dict, field: str) -> None:
    catalog = deepcopy(inputs["current_catalog"])
    channels = json.loads(explorer.CURRENT_CHANNELS.read_bytes())
    parent = catalog["parent_alpha_v27"]
    if field == "schema":
        parent["schema"] = "peano-library-alpha-snapshot-v26"
    elif field == "count":
        parent["theorem_count"] -= 1
    elif field in ("identity", "enrollment"):
        parent["edition_identity_sha256" if field == "identity" else "ordered_enrollment_root_sha256"] = "0" * 64
    elif field == "extra":
        parent["unchecked_parent_override"] = True
    else:
        parent["artifacts"][field]["sha256"] = "0" * 64
    with pytest.raises(explorer.NextLayerExplorerError, match="v27/v26/v25 ancestry"):
        explorer._audit_current_parent(catalog, channels)


@pytest.mark.parametrize("version", ("v28", "v29"))
@pytest.mark.parametrize("field", (
    "schema", "count", "identity", "enrollment", "catalog", "channels",
    "dependency_graph", "metrics", "extra",
))
def test_current_parent_rejects_any_forged_recent_parent_record(
    inputs: dict, version: str, field: str,
) -> None:
    # Copy the changed parent record, not the 3,222 large proof statements.
    catalog = dict(inputs["current_catalog"])
    catalog[f"parent_alpha_{version}"] = deepcopy(catalog[f"parent_alpha_{version}"])
    channels = json.loads(explorer.CURRENT_CHANNELS.read_bytes())
    parent = catalog[f"parent_alpha_{version}"]
    if field == "schema":
        parent["schema"] = "peano-library-alpha-snapshot-v27"
    elif field == "count":
        parent["theorem_count"] -= 1
    elif field in ("identity", "enrollment"):
        parent["edition_identity_sha256" if field == "identity" else "ordered_enrollment_root_sha256"] = "0" * 64
    elif field == "extra":
        parent["unchecked_parent_override"] = True
    else:
        parent["artifacts"][field]["sha256"] = "0" * 64
    with pytest.raises(explorer.NextLayerExplorerError, match="v29/v28/v27/v26/v25 ancestry"):
        explorer._audit_current_parent(catalog, channels)


@pytest.mark.parametrize("version,promotion", (
    ("v28", "alpha_v28_lower_layer_promotion"),
    ("v29", "alpha_v29_priority_layer_promotion"),
))
@pytest.mark.parametrize("field", ("artifact_path", "artifact_sha256", "node_count", "independent_lean_bundle_verified"))
def test_current_parent_preserves_every_recent_proof_receipt(
    inputs: dict, version: str, promotion: str, field: str,
) -> None:
    catalog = dict(inputs["current_catalog"])
    catalog[promotion] = deepcopy(catalog[promotion])
    receipt = catalog[promotion]["proof_bundle"]
    receipt[field] = {
        "artifact_path": "research/arithmetic-library/artifacts/fabricated.json",
        "artifact_sha256": "0" * 64,
        "node_count": 1,
        "independent_lean_bundle_verified": False,
    }[field]
    channels = json.loads(explorer.CURRENT_CHANNELS.read_bytes())
    with pytest.raises(explorer.NextLayerExplorerError, match="v29/v28/v27/v26/v25 ancestry"):
        explorer._audit_current_parent(catalog, channels)


@pytest.mark.parametrize("field,value", (("theorem_count", 433), ("artifact_sha256", "0" * 64)))
def test_current_parent_rejects_changes_to_the_unchanged_stable_channel(
    inputs: dict, field: str, value: object,
) -> None:
    channels = json.loads(explorer.CURRENT_CHANNELS.read_bytes())
    channels["channels"]["stable"][field] = value
    with pytest.raises(explorer.NextLayerExplorerError, match="v29/v28/v27/v26/v25 ancestry"):
        explorer._audit_current_parent(inputs["current_catalog"], channels)


def test_recent_parent_hashes_are_literal_actual_release_pins() -> None:
    assert explorer.PARENT_ALPHA_V28_CATALOG_SHA256 == (
        "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"
    )
    assert explorer.PARENT_ALPHA_V29_CATALOG_SHA256 == (
        "2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0"
    )
    assert explorer.PARENT_CHANNELS_V28_SHA256 == (
        "e562059411b83ddc21019ed5a567149e73a96882883cdc684130c6724a70f879"
    )
    assert explorer.PARENT_CHANNELS_V29_SHA256 == (
        "7b16e92c6778216961da166d784b6f441f8417a1f733b4580e96bed23928d753"
    )
    assert set(explorer.RECENT_PARENT_PINS) == {"v28", "v29"}
    for version, expected_count in (("v28", 2764), ("v29", 3042)):
        pins = explorer.RECENT_PARENT_PINS[version]
        assert pins["theorem_count"] == expected_count
        for label, path in (
            ("catalog", f"artifacts/peano-library/alpha/catalog-{version}.json"),
            ("channels", f"artifacts/peano-library/channels-{version}.json"),
            ("dependency_graph", f"artifacts/peano-library/alpha/dependency-graph-{version}.mmd"),
            ("metrics", f"artifacts/peano-library/alpha/metrics-{version}.json"),
            ("bundle_sha256", pins["bundle_path"]),
        ):
            assert explorer._file_digest(ROOT / path) == pins[label]
        assert (ROOT / pins["bundle_path"]).stat().st_size == pins["bundle_bytes"]


def test_recent_parent_audit_preserves_the_real_frozen_older_chain() -> None:
    # This direct check needs no future child artifact and leaves the old
    # helper APIs usable by an archived presentation.
    parent = json.loads((ROOT / "artifacts/peano-library/alpha/catalog-v29.json").read_bytes())
    channels = json.loads((ROOT / "artifacts/peano-library/channels-v29.json").read_bytes())
    older, older_channels = explorer._audit_recent_parent(parent, channels, version="v28")
    explorer._audit_v27_parent(older, older_channels)
    with pytest.raises(explorer.NextLayerExplorerError, match="ancestry"):
        explorer._audit_recent_parent(parent, channels, version="v27")


def test_current_presentation_files_do_not_rewrite_any_v29_evidence_document() -> None:
    path = ROOT / "artifacts/peano-library/alpha/catalog-v29.json"
    raw = path.read_bytes()
    assert sha256(raw).hexdigest() == (
        "2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0"
    )
    catalog = json.loads(raw)
    documents = catalog["evidence_documents"]
    assert len(documents) == 699
    families = (
        "frontier", "next_layer", "advanced_layer", "transport_layer",
        "milestone_closure", "research_layer", "breakthrough_layer",
    )
    mutable = {f"scripts/build_constructive_{family}_explorer.py" for family in families}
    mutable.update(f"peano-lab/py/tests/test_constructive_{family}_explorer.py" for family in families)
    mutable.update({
        "peano-lab/py/tests/test_constructive_next_layer_public_site.py",
        "peano-lab/py/tests/test_constructive_research_publication_v24.py",
        "peano-lab/py/tests/test_constructive_breakthrough_publication_v25.py",
    })
    assert mutable.isdisjoint(document["path"] for document in documents)


@pytest.mark.parametrize("goal", tuple(explorer.SECOND_WAVE_COMPLETIONS))
@pytest.mark.parametrize(
    "mutation",
    (
        "historical_missing", "historical_scope", "historical_statement", "historical_bundle",
        "status", "root", "statement", "bundle", "node", "lean", "checked",
        "partial_flag", "full_scope", "root_list",
    ),
)
def test_closed_milestones_cannot_relabel_or_reuse_old_partial_proofs(
    inputs: dict, goal: str, mutation: str,
) -> None:
    node = deepcopy(inputs["milestones"][goal])
    catalog = inputs["current_catalog"]
    explorer._audit_second_wave_milestone(goal, node, catalog)
    if mutation == "historical_missing":
        del node["historical_partial_evidence"]
    elif mutation == "historical_scope":
        node["historical_partial_evidence"]["checked_use"] = True
    elif mutation == "historical_statement":
        node["historical_partial_evidence"]["partial_theorem_statement_sha256"] = "0" * 64
    elif mutation == "historical_bundle":
        node["historical_partial_evidence"]["bundle_sha256"] = node["evidence"]["bundle_sha256"]
    elif mutation == "status":
        node["status"] = "open"
    elif mutation == "root":
        node["evidence"]["theorem_name"] = explorer.HISTORICAL_PARTIAL_ROOTS[goal]
    elif mutation == "statement":
        node["evidence"]["theorem_statement_sha256"] = "0" * 64
    elif mutation == "bundle":
        node["evidence"]["bundle_sha256"] = node["historical_partial_evidence"]["bundle_sha256"]
    elif mutation == "node":
        node["evidence"]["bundle_node_id"] += 1
    elif mutation == "lean":
        node["evidence"]["independent_lean_bundle_verified"] = False
    elif mutation == "checked":
        node["evidence"]["checked_use"] = False
    elif mutation == "partial_flag":
        node["evidence"]["partial_component_checked_use"] = True
    elif mutation == "full_scope":
        node["evidence"][explorer.SECOND_WAVE_REQUIRED_FLAGS[goal][0]] = False
    else:
        node["evidence"]["theorem_names"] = [explorer.HISTORICAL_PARTIAL_ROOTS[goal]]
    with pytest.raises(explorer.NextLayerExplorerError, match="historical partial or full second-wave"):
        explorer._audit_second_wave_milestone(goal, node, catalog)


@pytest.mark.parametrize("name", ("BetaAt", "Factorial", "IsGCD"))
def test_additive_canonical_alias_keeps_the_original_checked_destination(name: str) -> None:
    blueprint = {"BetaAt": "Beta", "Factorial": "Fact", "IsGCD": "Gcd"}[name]
    old = {"reviewed_name": name, "blueprint_name": blueprint, "reviewed_id": "PD-test", "route": "historical"}
    new = {**old, "blueprint_name": name}
    for rows in ([old, new], [new, old]):
        assert explorer._preferred_reviewed_matches({"compatible_reviewed_matches": rows}) == {name: old}
    with pytest.raises(explorer.NextLayerExplorerError, match="repeats the checked identity"):
        explorer._preferred_reviewed_matches({"compatible_reviewed_matches": [old, old]})
    with pytest.raises(explorer.NextLayerExplorerError, match="repeats the checked identity"):
        explorer._preferred_reviewed_matches({"compatible_reviewed_matches": [old, {**new, "reviewed_id": "forged"}]})


@pytest.mark.parametrize("name,parameters", (("RingPrime", ["z", "ring"]), ("GaussianFactorization", None)))
def test_current_atlas_keeps_generic_ring_planning_notation_unaliased(
    name: str, parameters: list[str] | None,
) -> None:
    from constructive_gaussian_factorization_definition_graph import REVIEWED_BLUEPRINT_ALIASES

    graph = json.loads(explorer.GLOBAL_DEFINITIONS.read_bytes())
    rows = {row["name"]: row for row in graph["definitions"]}
    if parameters is None:
        # This planning-only name has never been declared in the actual
        # atlas.  The new five-argument GPrimeFactorization is not an alias.
        assert name not in rows
    else:
        assert rows[name]["parameters"] == parameters
        assert rows[name]["reviewed_match"] is None
    assert name not in REVIEWED_BLUEPRINT_ALIASES
    assert all(row["blueprint_name"] != name for row in graph["compatible_reviewed_matches"])


@pytest.mark.parametrize("suffix", ("index.html", "explorer/index.html", "explorer/defined/graph.html", "explorer/defined/tag/MD0006.html"))
def test_completion_navigation_is_relative_at_every_historical_page_depth(suffix: str) -> None:
    family = next(item for item in explorer.FAMILIES if item.slug == "matrix-dot-product")
    path = f"{family.slug}/{suffix}"
    original = (
        f'<main class="shell family-main"><p>{html.escape(family.caveat)}</p></main>'
    ).encode()
    files = {path: original, "assets/defined-explorer.js": b"unchanged canonical asset"}
    explorer._link_second_wave_completions(files, (family,), revision="012345abcdef")
    page = files[path].decode()
    target = "../" * path.count("/") + "integer-linear-algebra/?v=012345abcdef"
    assert f'href="{target}"' in page
    assert 'data-current-milestone="T13"' in page
    assert family.caveat in html.unescape(page)
    assert '<main class="shell family-main">' in page
    assert files["assets/defined-explorer.js"] == b"unchanged canonical asset"


@pytest.mark.parametrize("context", ("script", "style", "textarea", "template", "attribute", "comment"))
@pytest.mark.parametrize("visible_paragraph", (False, True), ids=("fallback", "paragraph"))
def test_completion_links_only_change_real_html_context(context: str, visible_paragraph: bool) -> None:
    original_family = next(item for item in explorer.FAMILIES if item.slug == "matrix-dot-product")
    family = SimpleNamespace(
        slug=original_family.slug, milestones=original_family.milestones,
        caveat="Known T13 boundary Ω",
    )
    caveat = html.escape(family.caveat)
    hidden = {
        "script": f'<script>window.note={json.dumps(family.caveat)};window.end="</main>";</script>',
        "style": f'<style>/* {family.caveat} </main> */</style>',
        "textarea": f'<textarea>{caveat} </main></textarea>',
        "template": f'<template><p>{caveat}</p><main></main></template>',
        "attribute": f'<div data-note="{caveat}"></div>',
        "comment": f'<!-- <p>{caveat}</p></main> -->',
    }[context]
    path = f"{family.slug}/explorer/defined/graph.html"
    prefix = f"<!doctype html>\n<html>\n{hidden}\n<main class=\"shell family-main\">\n"
    body = f"<p>{caveat}</p>" if visible_paragraph else "<section>Proof graph</section>"
    suffix = "\n</main></html>"
    original = (prefix + body + suffix).encode()
    files = {path: original}
    explorer._link_second_wave_completions(files, (family,), revision="012345abcdef")
    link = (
        '<a data-current-milestone="T13" '
        'href="../../../integer-linear-algebra/?v=012345abcdef">'
        'Full T13 proof · Alpha v27</a>'
    )
    if visible_paragraph:
        expected = prefix + f"<p>{caveat} {link}</p>" + suffix
    else:
        note = f'<p class="pd-callout">Separate complete second-wave branches: {link}.</p>'
        expected = prefix + body + "\n" + note + "</main></html>"
    assert files[path] == expected.encode()
    assert hidden in files[path].decode()


@pytest.mark.parametrize("document", (
    '<script>window.text="</main>";</script>',
    '<!-- <main></main> -->',
    '<template><main></main></template>',
    '<main></main><main></main>',
    '<script>window.text="unfinished";<main></main>',
))
def test_completion_links_reject_fake_or_ambiguous_html_boundaries(document: str) -> None:
    family = next(item for item in explorer.FAMILIES if item.slug == "matrix-dot-product")
    path = f"{family.slug}/explorer/defined/graph.html"
    files = {path: document.encode()}
    with pytest.raises(explorer.NextLayerExplorerError):
        explorer._link_second_wave_completions(files, (family,), revision="012345abcdef")
    assert files[path] == document.encode()


@pytest.mark.parametrize("module_name,first_version", (
    ("build_constructive_advanced_layer_explorer", "v21"),
    ("build_constructive_transport_layer_explorer", "v22"),
    ("build_constructive_milestone_closure_explorer", "v23"),
    ("build_constructive_research_layer_explorer", "v24"),
    ("build_constructive_breakthrough_layer_explorer", "v25"),
))
def test_presentation_retargets_preserve_exact_inline_graph_data(module_name: str, first_version: str) -> None:
    publisher = importlib.import_module(module_name)
    payload = {"summary": "Alpha v20 / Alpha v21 / Alpha-v20 / Alpha-v21; first admitted v20"}
    assignment = f'window.PA_DEFINED_GRAPH={json.dumps(payload)};'
    document = (
        '<main><p>Alpha v20; first admitted v20; 590-node bundle</p></main>'
        f'<script id="pa-defined-graph-data">{assignment}</script>'
        '<script>window.status="Alpha v20 first admitted v20";</script>'
    ).encode()
    result = publisher._retarget(document, publisher.FAMILIES[0]).decode()
    assert f'<script id="pa-defined-graph-data">{assignment}</script>' in result
    assert f'<main><p>Alpha {first_version}; first admitted {first_version};' in result
    assert f'window.status="Alpha {first_version} first admitted {first_version}";' in result


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "renamed"))
def test_graph_data_preservation_rejects_altered_script_boundaries(mutation: str) -> None:
    script = '<script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH={"summary":"Alpha v20"};</script>'
    original = ('<main></main>' + script).encode()
    changed = {
        "missing": b'<main></main>',
        "duplicate": original + script.encode(),
        "renamed": original.replace(b'pa-defined-graph-data', b'different-graph-data'),
    }[mutation]
    with pytest.raises(explorer.NextLayerExplorerError, match="script boundary"):
        explorer._preserve_defined_graph_data(original, changed)
