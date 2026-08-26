"""Bounded, read-only end-to-end audit of the public Alpha-v24 research layer.

No test regenerates a snapshot, stages a website, starts a browser/server, or
replays a proof.  In particular, the historically sealed Quadratic Reciprocity
corpus is evidence in *both* the immutable v23 parent and its v24 child: its
v23 bytes and edition label must never be silently replaced by current labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.proof_bundle import decode_formula


ROOT = Path(__file__).resolve().parents[3]
STATIC = ROOT / "book" / "_static"
CATALOG_PATH = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
PARENT_CATALOG_PATH = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v23.json"
CHANNELS_PATH = ROOT / "artifacts" / "peano-library" / "channels-v24.json"
CAMPAIGN_PATH = STATIC / "constructive-grand-campaign" / "campaign.json"
DEFINITION_GRAPH_PATH = STATIC / "constructive-grand-campaign" / "definitions.json"
BUNDLE_NAME = "alpha-v24-research-layer-proof-bundle-v1.json"
BUNDLE_PATH = ROOT / "research" / "arithmetic-library" / "artifacts" / BUNDLE_NAME
QR_CORPUS_PATH = STATIC / "pa-proof-explorer" / "api" / "corpus.json"
QR_CURRENT_CORPUS_PATH = STATIC / "pa-proof-explorer" / "api" / "current-corpus.json"
BERTRAND_CORPUS_PATH = STATIC / "bertrand-proof-explorer" / "api" / "corpus.json"

ALPHA_VERSION = "v24"
ALPHA_COUNT = 2_008
STABLE_COUNT = 432
PARENT_COUNT = 1_949
NEW_THEOREM_COUNT = 59
ALPHA_IDENTITY = "1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b"
PARENT_IDENTITY = "02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85"
CATALOG_SHA256 = "94ac4d193cbfe8c2ec04e54024221bc2c3a534c0ae014d381663b86174b3dcc1"
PARENT_CATALOG_SHA256 = "818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2"
HTML_REVISION = CATALOG_SHA256[:12]
BUNDLE_SHA256 = "627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9"
QR_CORPUS_SHA256 = "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"

LAYER_FAMILIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "constructive-frontier-explorer",
        (
            "supplementary-laws", "kummer", "two-squares", "four-squares", "lucas",
            "pythagorean-fermat-four",
        ),
    ),
    (
        "constructive-next-layer-explorer",
        (
            "polynomial-horner", "matrix-dot-product", "bertrand-prime-chains",
            "continued-fractions",
        ),
    ),
    (
        "constructive-advanced-layer-explorer",
        ("matrix-coded-products", "euclidean-complexity", "binary-modular-exponentiation"),
    ),
    (
        "constructive-transport-layer-explorer",
        ("binary-length", "euclidean-gcd-transport", "binary-modular-execution"),
    ),
    (
        "constructive-milestone-closure-explorer",
        ("euclidean-logarithmic-bound", "binary-digit-extraction", "primes-three-mod-four"),
    ),
    (
        "constructive-research-layer-explorer",
        ("matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold"),
    ),
)
ALL_FAMILIES = tuple(
    (layer, slug) for layer, families in LAYER_FAMILIES for slug in families
)

NEW_DEFINITIONS: dict[str, tuple[str, str]] = {
    "ND0046": ("MatrixSkipIndex", "matrix-determinant-minors"),
    "ND0047": ("MatrixMinorCell", "matrix-determinant-minors"),
    "ND0048": ("MatrixMinorPrefix", "matrix-determinant-minors"),
    "ND0049": ("SignedMatrixMinor", "matrix-determinant-minors"),
    "ND0050": ("HornerDerivativeTrace", "polynomial-hensel"),
    "ND0051": ("HornerDerivative", "polynomial-hensel"),
    "ND0052": ("HornerDerivativeOnly", "polynomial-hensel"),
    "ND0053": ("CRTPositiveModuliPrefix", "generalized-crt-fold"),
    "ND0054": ("CRTPairwiseCoprimePrefix", "generalized-crt-fold"),
    "ND0055": ("CRTPrefixSolution", "generalized-crt-fold"),
    "ND0056": ("CRTPrefixLCM", "generalized-crt-fold"),
    "ND0057": ("CRTCanonicalPrefixSolution", "generalized-crt-fold"),
}


@dataclass(frozen=True, slots=True)
class _RootEvidence:
    slug: str
    milestone: str
    name: str
    statement_sha256: str
    node_id: int
    tag: str
    definition: str
    full_scope_flag: str
    open_boundary: str


RESEARCH_ROOTS = (
    _RootEvidence(
        "matrix-determinant-minors", "T13", "beta_signed_matrix_minor_exists",
        "bf6e9238c2928e4f6525a14015198b673b41022924c6da1944ab87c8df61bba1",
        155, "MN000D", "SignedMatrixMinor", "full_arbitrary_determinant_proved",
        "unrestricted determinant evaluation",
    ),
    _RootEvidence(
        "polynomial-hensel", "G095", "beta_horner_derivative_exists_unique",
        "171b5939376bfb9e9ec9469d3addd98e27584931fa7994dccb4b372c4d9a693f",
        170, "HD000B", "HornerDerivative", "full_simple_root_hensel_lift_proved",
        "Hensel lift have not been proved",
    ),
    _RootEvidence(
        "generalized-crt-fold", "G011",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f",
        201, "CR001B", "CRTPrefixLCM", "full_generalized_crt_proved",
        "noncoprime pairwise gcd-compatible lists",
    ),
)

CANONICAL_QR_MARKERS = (
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
    '<section class="release-note"',
)


class _HubMarkup(HTMLParser):
    """Collect semantic campaign cards without fragile HTML regex matching."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict[str, object]] = []
        self.links: list[dict[str, str]] = []
        self._current: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        classes = frozenset(attributes.get("class", "").split())
        if tag == "article" and "family-card" in classes:
            self._current = {"classes": classes, "links": []}
            self.cards.append(self._current)
        if tag == "a":
            self.links.append(attributes)
            if self._current is not None:
                self._current["links"].append(attributes)

    def handle_endtag(self, tag: str) -> None:
        if tag == "article":
            self._current = None


@lru_cache(maxsize=None)
def _json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def catalog() -> dict:
    value = _json(CATALOG_PATH)
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def theorem_rows(catalog: dict) -> dict[str, dict]:
    return {row["name"]: row for row in catalog["theorems"]}


@pytest.fixture(scope="module")
def campaign() -> dict:
    value = _json(CAMPAIGN_PATH)
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def definition_graph() -> dict:
    value = _json(DEFINITION_GRAPH_PATH)
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def bundle_record() -> list:
    value = _json(BUNDLE_PATH)
    assert isinstance(value, list)
    return value


def test_sealed_v24_catalog_channels_parent_and_exact_additive_counts(catalog: dict) -> None:
    channels = _json(CHANNELS_PATH)
    parent = _json(PARENT_CATALOG_PATH)
    assert _digest(CATALOG_PATH) == CATALOG_SHA256
    assert _digest(PARENT_CATALOG_PATH) == PARENT_CATALOG_SHA256
    assert catalog["schema"] == "peano-library-alpha-snapshot-v24"
    assert catalog["theorem_count"] == catalog["checked_use_count"] == ALPHA_COUNT
    assert len(catalog["theorems"]) == ALPHA_COUNT
    assert catalog["stable_count"] == STABLE_COUNT
    assert catalog["edition_identity_sha256"] == ALPHA_IDENTITY
    assert catalog["parent_alpha_v23"]["theorem_count"] == PARENT_COUNT
    assert catalog["parent_alpha_v23"]["edition_identity_sha256"] == PARENT_IDENTITY
    assert parent["theorem_count"] == parent["checked_use_count"] == PARENT_COUNT
    assert parent["stable_count"] == STABLE_COUNT

    promotion = catalog["alpha_v24_research_layer_promotion"]
    assert promotion["checked_use_before"] == PARENT_COUNT
    assert promotion["checked_use_after"] == ALPHA_COUNT
    assert promotion["frontier_new_count"] == NEW_THEOREM_COUNT
    assert promotion["remaining_body_checked_count"] == 0
    assert promotion["campaign_counts"] == {
        "matrix_determinant_minors": 17,
        "polynomial_hensel": 15,
        "generalized_crt_fold": 27,
    }

    assert channels["schema"] == "peano-library-channels-v24"
    assert channels["default_channel"] == "stable"
    assert channels["channels"]["stable"]["theorem_count"] == STABLE_COUNT
    assert channels["channels"]["stable"]["checked_use_count"] == STABLE_COUNT
    alpha = channels["channels"]["alpha"]
    assert alpha["theorem_count"] == alpha["checked_use_count"] == ALPHA_COUNT
    assert alpha["alpha_v24_frontier_new_count"] == NEW_THEOREM_COUNT
    assert alpha["edition_identity_sha256"] == ALPHA_IDENTITY
    assert alpha["artifact_sha256"] == CATALOG_SHA256


def test_exact_v24_bundle_envelope_is_bounded_without_replaying_proofs(
    catalog: dict, bundle_record: list,
) -> None:
    assert _digest(BUNDLE_PATH) == BUNDLE_SHA256
    assert BUNDLE_PATH.stat().st_size == 738_923
    assert len(bundle_record) == 4
    assert bundle_record[0] == "peano-lab-bundle-v1"
    assert bundle_record[1] == 202
    assert len(bundle_record[3]) == 203
    assert sum(len(node[2]) for node in bundle_record[3]) == 502

    promotion = catalog["alpha_v24_research_layer_promotion"]
    evidence = promotion["proof_bundle"]
    assert promotion["independent_lean_bundle_verified"]
    assert evidence["independent_lean_bundle_verified"]
    assert evidence["artifact_sha256"] == BUNDLE_SHA256
    assert evidence["artifact_bytes"] == 738_923
    assert evidence["node_count"] == evidence["kernel_calls"] == 203
    assert evidence["dependency_edges"] == 502
    assert evidence["body_proof_nodes"] == 11_065


@pytest.mark.parametrize("root", RESEARCH_ROOTS, ids=lambda root: root.milestone)
def test_each_public_research_root_matches_exact_sealed_statement_and_bundle_node(
    root: _RootEvidence, theorem_rows: dict[str, dict], bundle_record: list,
) -> None:
    theorem = theorem_rows[root.name]
    assert theorem["checked_use"] and theorem["body_checked"]
    assert theorem["evidence_status"] == "alpha_closed"
    assert theorem["statement_sha256"] == root.statement_sha256
    assert sha256(theorem["statement"].encode()).hexdigest() == root.statement_sha256

    bundle_links = [
        link for link in theorem["evidence_links"]
        if link.get("path", "").endswith(BUNDLE_NAME)
    ]
    assert len(bundle_links) == 1
    assert bundle_links[0]["document_sha256"] == BUNDLE_SHA256
    assert bundle_links[0]["selector"] == f"nodes[id={root.node_id}]"

    # Decode only the three exact statement ASTs; never decode/replay proof bodies.
    assert decode_formula(bundle_record[3][root.node_id][1]) == (
        parse_formula_in_context(theorem["statement"], [])
    )

    corpus = _json(
        STATIC / "constructive-research-layer-explorer" / root.slug / "api" / "corpus.json"
    )
    node = next(item for item in corpus["nodes"] if item["name"] == root.name)
    assert node["statement"] == theorem["statement"]
    assert node["statement_sha256"] == root.statement_sha256
    assert node["proof_bundle_node_id"] == root.node_id
    assert node["proof_bundle_sha256"] == BUNDLE_SHA256
    assert node["alpha_checked_use"] and node["independent_lean_bundle_verified"]
    assert not node["stable_member"]
    assert corpus["tags"][root.name] == root.tag


def test_global_campaign_and_conservative_definition_dag_are_exact_and_current(
    campaign: dict, definition_graph: dict,
) -> None:
    assert campaign["schema"] == "constructive-grand-campaign-v1"
    assert campaign["meta"]["current_alpha_version"] == ALPHA_VERSION
    assert campaign["meta"]["current_alpha_checked_use_count"] == ALPHA_COUNT
    assert len(campaign["definitions"]) == 164
    assert len(campaign["nodes"]) == 144
    assert definition_graph["definition_count"] == 164
    assert definition_graph["reviewed_definition_count"] == 109
    assert definition_graph["compatible_reviewed_match_count"] == 73
    assert definition_graph["reviewed_definition_edge_count"] == 186

    canonical_campaign = json.dumps(
        campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode()
    assert definition_graph["campaign_snapshot_sha256"] == sha256(canonical_campaign).hexdigest()
    assert "never theorem-proof dependencies" in definition_graph["authority_policy"][
        "notation_edges"
    ]

    reviewed = {item["id"]: item for item in definition_graph["reviewed_definitions"]}
    assert set(NEW_DEFINITIONS) <= reviewed.keys()
    assert tuple(NEW_DEFINITIONS) == tuple(f"ND{index:04d}" for index in range(46, 58))
    for identifier, (name, route) in NEW_DEFINITIONS.items():
        assert reviewed[identifier]["name"] == name
        assert reviewed[identifier]["route"] == route
        assert name in campaign["definitions"]


@pytest.mark.parametrize("root", RESEARCH_ROOTS, ids=lambda root: root.milestone)
def test_partially_proved_major_milestones_stay_honestly_open(
    root: _RootEvidence, campaign: dict,
) -> None:
    node = next(item for item in campaign["nodes"] if item["id"] == root.milestone)
    evidence = node["evidence"]
    assert node["status"] == "open"
    assert evidence["implementation"] == "independently_closed_partial"
    assert evidence["alpha_version"] == ALPHA_VERSION
    assert evidence["alpha_enrolled"]
    assert evidence["partial_component_checked_use"]
    assert not evidence["checked_use"]
    assert not evidence["stable_member"]
    assert evidence["partial_theorem_name"] == root.name
    assert evidence["partial_theorem_statement_sha256"] == root.statement_sha256
    assert evidence["bundle_node_id"] == root.node_id
    assert evidence["bundle_sha256"] == BUNDLE_SHA256
    assert evidence["independent_lean_bundle_verified"]
    assert evidence[root.full_scope_flag] is False
    assert root.definition in node["definition_refs"]


@pytest.mark.parametrize("layer,expected_families", LAYER_FAMILIES)
def test_all_six_published_layer_manifests_authorize_current_v24(
    layer: str, expected_families: tuple[str, ...],
) -> None:
    manifest = _json(STATIC / layer / "manifest.json")
    assert manifest["alpha_edition_version"] == ALPHA_VERSION
    assert {row["slug"] for row in manifest["families"]} == set(expected_families)
    if layer == "constructive-frontier-explorer":
        assert manifest["alpha_edition_identity_sha256"] == ALPHA_IDENTITY
        assert manifest["alpha_edition_checked_use_count"] == ALPHA_COUNT
        assert manifest["alpha_catalog_sha256"] == CATALOG_SHA256
    else:
        assert manifest["edition_identity_sha256"] == ALPHA_IDENTITY
        assert manifest["catalog_sha256"] == CATALOG_SHA256
        assert manifest["html_revision"] == HTML_REVISION


def test_public_hub_has_exactly_22_campaign_cards_and_both_original_anchors() -> None:
    source = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")
    parser = _HubMarkup()
    parser.feed(source)

    anchors = [card for card in parser.cards if "candidate-card" not in card["classes"]]
    campaigns = [card for card in parser.cards if "candidate-card" in card["classes"]]
    assert len(parser.cards) == 24
    assert len(anchors) == 2
    assert len(campaigns) == len(ALL_FAMILIES) == 22
    assert {next(iter(card["classes"] - {"family-card"})) for card in anchors} == {
        "qr-card", "bertrand-card"
    }

    slugs = {slug for _, slug in ALL_FAMILIES}
    linked_slugs = {
        link["href"].split("/?", 1)[0]
        for card in campaigns
        for link in card["links"]
        if link.get("class") == "primary-action"
    }
    assert linked_slugs == slugs
    for slug in slugs | {"quadratic-reciprocity", "bertrand-postulate"}:
        assert f'href="{slug}/?v={HTML_REVISION}"' in source

    assert "Alpha v24" in source
    assert "2,008 theorems" in source
    assert "432-theorem Stable edition remains unchanged" in source
    assert "164 structured first-order definitions" in source
    assert "109 reviewed conservative definitions" in source
    assert BUNDLE_NAME in source

    for root in RESEARCH_ROOTS:
        assert f"focus={root.milestone}&amp;v={HTML_REVISION}" in source
        assert f"view=definition&amp;focus={root.definition}&amp;v={HTML_REVISION}" in source
    assert "milestones remain open" in source
    assert "Fermat descent remains conditional" in source


@pytest.mark.parametrize("layer,slug", ALL_FAMILIES, ids=[slug for _, slug in ALL_FAMILIES])
def test_every_campaign_retains_original_qr_design_definition_graph_and_v24_authority(
    layer: str, slug: str,
) -> None:
    family_root = STATIC / layer / slug
    landing = (family_root / "index.html").read_text(encoding="utf-8")
    canonical_anchor = (ROOT / "deploy" / "proofs" / "quadratic-reciprocity.html").read_text(
        encoding="utf-8"
    )
    for marker in CANONICAL_QR_MARKERS:
        assert marker in canonical_anchor
        assert marker in landing
    assert f'<body class="family-page {slug}-page">' in landing
    assert landing.count('<article class="view-card') == 3
    assert f'href="../assets/proofs.css?v={HTML_REVISION}"' in landing
    assert f'href="explorer/defined/?v={HTML_REVISION}"' in landing
    assert f'href="explorer/?v={HTML_REVISION}"' in landing
    assert "explorer/defined/graph.html?" in landing
    assert f"v={HTML_REVISION}" in landing
    assert "Alpha v24" in landing
    assert "not Stable" in landing

    for path in (
        "explorer/index.html", "explorer/defined/index.html",
        "explorer/defined/graph.html", "explorer/defined/api/graph.json",
    ):
        assert (family_root / path).is_file(), f"{slug} lacks canonical {path}"

    corpus = _json(family_root / "api" / "corpus.json")
    assert corpus["alpha_edition_version"] == ALPHA_VERSION
    assert corpus["alpha_edition_identity_sha256"] == ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == CATALOG_SHA256
    assert corpus["alpha_checked_use_node_count"] > 0
    assert corpus["definition_count"] > 0
    assert corpus["root_names"]

    graph = _json(family_root / "explorer" / "defined" / "api" / "graph.json")
    assert graph["alpha_edition_version"] == ALPHA_VERSION
    assert {node["kind"] for node in graph["nodes"]} >= {"theorem", "definition"}
    assert {edge["kind"] for edge in graph["edges"]} >= {
        "proof_dependency", "uses_definition"
    }


@pytest.mark.parametrize("identifier", tuple(NEW_DEFINITIONS))
def test_every_new_conservative_definition_has_live_local_and_global_drill_down(
    identifier: str, campaign: dict, definition_graph: dict,
) -> None:
    name, slug = NEW_DEFINITIONS[identifier]
    family_root = STATIC / "constructive-research-layer-explorer" / slug
    corpus = _json(family_root / "api" / "corpus.json")
    definition = next(item for item in corpus["definitions"] if item["name"] == name)
    assert definition["id"] == definition["reviewed_definition_id"] == identifier
    assert definition["reviewed_definition_route"] == slug
    assert definition["global_definition"] == name
    assert definition["exact_ast_verified"]
    assert definition["kernel_signature_unchanged"]

    page = (
        family_root / "explorer" / "defined" / "definition" / f"{identifier}.html"
    ).read_text(encoding="utf-8")
    assert name in page
    assert identifier in page
    assert "Conservative notation; not a theorem, primitive, or axiom" in page
    assert "Hygienic expanded first-order definition" in page
    assert f"view=definition&amp;focus={name}&amp;v={HTML_REVISION}" in page

    reviewed = next(
        item for item in definition_graph["reviewed_definitions"] if item["id"] == identifier
    )
    assert reviewed["name"] == name
    assert reviewed["route"] == slug
    assert campaign["definitions"][name]["parameters"] == reviewed["parameters"]


@pytest.mark.parametrize("root", RESEARCH_ROOTS, ids=lambda root: root.slug)
def test_new_research_pages_keep_exact_honest_open_scope_boundaries(root: _RootEvidence) -> None:
    family_root = STATIC / "constructive-research-layer-explorer" / root.slug
    landing = (family_root / "index.html").read_text(encoding="utf-8")
    corpus = _json(family_root / "api" / "corpus.json")
    graph = _json(family_root / "explorer" / "defined" / "api" / "graph.json")

    assert f"{root.milestone} remains OPEN" in landing
    assert root.open_boundary in landing
    assert root.name in landing
    assert f"tag/{root.tag}.html?v={HTML_REVISION}" in landing
    assert BUNDLE_SHA256 in landing
    for evidence in (corpus, graph):
        assert evidence["milestone_status"] == "open"
        assert not evidence["milestone_checked_use"]
        assert evidence["milestone_partial_checked_use"]
        assert evidence["independent_lean_bundle_verified"]


def test_quadratic_reciprocity_anchor_bytes_remain_immutable_v23_parent_evidence(
    catalog: dict,
) -> None:
    parent = _json(PARENT_CATALOG_PATH)
    relative_path = QR_CORPUS_PATH.relative_to(ROOT).as_posix()
    for edition in (parent, catalog):
        bindings = [
            item for item in edition["evidence_documents"] if item["path"] == relative_path
        ]
        assert len(bindings) == 1
        assert bindings[0]["sha256"] == QR_CORPUS_SHA256

    assert _digest(QR_CORPUS_PATH) == QR_CORPUS_SHA256, (
        "the historically pinned Quadratic Reciprocity corpus was regenerated; "
        "this invalidates both sealed v23-parent and current v24 evidence"
    )
    assert QR_CORPUS_PATH.stat().st_size == 17_229_311
    corpus = _json(QR_CORPUS_PATH)
    assert corpus["schema"] == "peano-lab-pa-proof-corpus-v1"
    assert corpus["theorem_count"] == 557
    assert corpus["edge_count"] == 1_787
    assert "alpha_edition_version" not in corpus


def test_quadratic_reciprocity_current_v24_sidecar_never_replaces_immutable_evidence() -> None:
    manifest = _json(STATIC / "pa-proof-explorer" / "manifest.json")
    current = _json(QR_CURRENT_CORPUS_PATH)
    assert current["schema"] == "peano-lab-pa-proof-corpus-v1"
    assert current["alpha_edition_version"] == ALPHA_VERSION
    assert current["alpha_edition_identity_sha256"] == ALPHA_IDENTITY
    assert current["alpha_edition_checked_use_count"] == ALPHA_COUNT
    assert current["proof_edition_version"] == "v16"
    assert current["proof_edition_checked_use_count"] == 885
    assert current["theorem_count"] == 557
    assert current["edge_count"] == 1_787

    assert manifest["immutable_evidence_corpus_path"] == "api/corpus.json"
    assert manifest["immutable_evidence_corpus_sha256"] == QR_CORPUS_SHA256
    assert manifest["immutable_evidence_corpus_bytes"] == 17_229_311
    assert manifest["current_corpus_path"] == "api/current-corpus.json"
    assert manifest["current_corpus_sha256"] == _digest(QR_CURRENT_CORPUS_PATH)
    files = {row["path"]: row for row in manifest["files"]}
    assert files["api/corpus.json"]["sha256"] == QR_CORPUS_SHA256
    assert files["api/current-corpus.json"]["sha256"] == _digest(QR_CURRENT_CORPUS_PATH)

    generator = (ROOT / "scripts" / "build_pa_proof_explorer.py").read_text(
        encoding="utf-8"
    )
    assert "_immutable_evidence_corpus" in generator
    assert "api/current-corpus.json" in generator
    assert QR_CORPUS_SHA256 in generator


def test_bertrand_preserves_historical_proof_but_uses_current_v24_authority() -> None:
    corpus = _json(BERTRAND_CORPUS_PATH)
    assert corpus["alpha_edition_version"] == ALPHA_VERSION
    assert corpus["alpha_edition_identity_sha256"] == ALPHA_IDENTITY
    assert corpus["alpha_edition_checked_use_count"] == ALPHA_COUNT
    assert corpus["proof_edition_version"] == "v18"
    assert corpus["proof_edition_checked_use_count"] == 1_589
    assert corpus["theorem_count"] == 544
    assert corpus["root_name"] == "bertrand_strict"
    assert corpus["root_tag"] == "BT0127"


def test_read_only_stage_recipes_reference_every_campaign_and_exact_v24_artifact() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    start = makefile.index("\nstage-proofs:")
    end = makefile.index("\nstage-lean-api:", start)
    recipe = makefile[start:end]
    assert recipe.startswith("\nstage-proofs: book-proof-explorer ")
    assert "book/_static/pa-proof-explorer/api/corpus.json" in recipe
    assert QR_CORPUS_SHA256 in recipe
    assert "Immutable Alpha parent quadratic-reciprocity evidence corpus changed" in recipe
    assert "book-constructive-research-layer-explorer" in recipe
    assert BUNDLE_NAME in recipe
    assert "alpha-v24-research-layer-receipt.md" in recipe
    assert "constructive-grand-campaign" in recipe
    assert '"$(STAGEPROOFS)/quadratic-reciprocity/explorer/' in recipe
    assert '"$(STAGEPROOFS)/bertrand-postulate/explorer/' in recipe

    for layer, slug in ALL_FAMILIES:
        assert f"book/_static/{layer}/{slug}/" in recipe
        assert f'"$(STAGEPROOFS)/{slug}/"' in recipe

    app_stage = makefile[makefile.index("\nstage-peano:"):]
    assert BUNDLE_NAME in app_stage
    assert "peano-lab/APP_MANIFEST.sha256" in app_stage
    assert "peano-lab/worker.js" in app_stage


def test_browser_app_worker_manifest_release_id_and_new_roots_are_consistent() -> None:
    app = ROOT / "peano-lab"
    manifest_path = app / "APP_MANIFEST.sha256"
    manifest = manifest_path.read_text(encoding="utf-8")
    rows = {}
    for line in manifest.splitlines():
        digest, separator, path = line.partition("  ")
        assert separator and path and re.fullmatch(r"[0-9a-f]{64}", digest)
        assert path not in rows
        rows[path] = digest

    assert rows[f"proof-artifacts/{BUNDLE_NAME}"] == BUNDLE_SHA256
    required_paths = (
        "worker.js",
        "py/peano_lab/library/alpha_enrollment_v24.py",
        "py/peano_lab/library/editions_v24.py",
        "py/peano_lab/library/campaign_research_layer_closure.py",
        "py/peano_lab/library/matrix_determinant_minors_candidate.py",
        "py/peano_lab/library/polynomial_hensel_candidate.py",
        "py/peano_lab/library/generalized_crt_fold_candidate.py",
    )
    for relative in required_paths:
        assert rows[relative] == _digest(app / relative)

    worker = (app / "worker.js").read_text(encoding="utf-8")
    for relative in required_paths[1:]:
        assert f'"{relative}"' in worker
    assert f'"proof-artifacts/{BUNDLE_NAME}"' in worker

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^override PEANOAPPID := (a-[0-9a-f]{12})$", makefile, re.MULTILINE)
    assert match is not None
    app_id = match.group(1)
    assert app_id == f"a-{_digest(manifest_path)[:12]}"

    app_page = (app / "index.html").read_text(encoding="utf-8")
    assert f'const APP_ROOT="releases/{app_id}/";' in app_page
    assert "Alpha: 2,008 proofs" in app_page
    for root in RESEARCH_ROOTS:
        assert f'data-cmd="pa lib alpha {root.name}"' in app_page
