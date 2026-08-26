"""Fail-closed audit of four historical Alpha-v20 / current Alpha-v25 explorers.

These documentation tests never decode, construct, replay, or check a proof
bundle. Original admission remains solely with the immutable Alpha-v20 proof;
the explorer additionally authenticates current Alpha-v25 checked authority.
"""

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


def test_manifest_is_bound_to_current_v24_and_immutable_v20_first_admission(
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
    assert manifest["alpha_edition_version"] == "v25"
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
    assert "Alpha v25 checked-use theorem family" in source
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
    assert corpus["alpha_edition_version"] == "v25"
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
        assert node["alpha_edition_version"] == "v25"
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
    assert "Alpha v25 checked-use theorem" in graph
    assert "first admitted v20" in graph
    assert "independently kernel and Lean verified" in graph
    assert "proof_dependency" in graph
    assert "definition_uses_definition" in graph
    assert all(f"focus={milestone}" in html.unescape(graph) for milestone in milestones)


def test_matrix_explorer_never_claims_the_full_open_t13_milestone(
    generated: dict[str, bytes], corpora: dict[str, dict[str, Any]]
) -> None:
    slug = "matrix-dot-product"
    landing = generated[f"{slug}/index.html"].decode()
    assert "T13 milestone remains OPEN" in landing
    assert "arbitrary signed matrix" in landing
    assert "arbitrary-dimensional determinants, rank, and lattices remain open" in landing
    for node in corpora[slug]["nodes"]:
        tag = corpora[slug]["tags"][node["name"]]
        defined = generated[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
        assert "T13 remains open" in defined
        assert "not a proof of the full matrix-ring" in defined


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

    payload = json.loads(generated[f"{slug}/explorer/defined/api/graph.json"])
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
