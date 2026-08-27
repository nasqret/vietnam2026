"""Audit immutable Alpha-v24 admission under current Alpha-v28 publication.

No test regenerates a snapshot, stages a website, starts a browser/server, or
replays a proof.  In particular, the historically sealed Quadratic Reciprocity
corpus is evidence in the immutable v23 through v27 catalogs: its historical
bytes must never be silently replaced by the separate current reading surface.
The QR/Bertrand reading snapshots retain their sealed v25 authority metadata;
the constructive campaign publishers use v28 without changing first admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.proof_bundle import decode_formula


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
STATIC = ROOT / "book" / "_static"
CATALOG_PATH = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
SEALED_V25_CATALOG_PATH = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v25.json"
CURRENT_CATALOG_PATH = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v28.json"
PARENT_CATALOG_PATH = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v23.json"
CHANNELS_PATH = ROOT / "artifacts" / "peano-library" / "channels-v24.json"
SEALED_V25_CHANNELS_PATH = ROOT / "artifacts" / "peano-library" / "channels-v25.json"
CURRENT_CHANNELS_PATH = ROOT / "artifacts" / "peano-library" / "channels-v28.json"
CAMPAIGN_PATH = STATIC / "constructive-grand-campaign" / "campaign.json"
DEFINITION_GRAPH_PATH = STATIC / "constructive-grand-campaign" / "definitions.json"
BUNDLE_NAME = "alpha-v24-research-layer-proof-bundle-v1.json"
BUNDLE_PATH = ROOT / "research" / "arithmetic-library" / "artifacts" / BUNDLE_NAME
QR_CORPUS_PATH = STATIC / "pa-proof-explorer" / "api" / "corpus.json"
QR_CURRENT_CORPUS_PATH = STATIC / "pa-proof-explorer" / "api" / "current-corpus.json"
BERTRAND_CORPUS_PATH = STATIC / "bertrand-proof-explorer" / "api" / "corpus.json"

SEALED_V25_VERSION = "v25"
SEALED_V25_COUNT = 2_080
FIRST_ADMISSION_VERSION = "v24"
FIRST_ADMISSION_COUNT = 2_008
STABLE_COUNT = 432
PARENT_COUNT = 1_949
NEW_THEOREM_COUNT = 59
SEALED_V25_IDENTITY = "3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28"
FIRST_ADMISSION_IDENTITY = (
    "1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b"
)
PARENT_IDENTITY = "02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85"
SEALED_V25_CATALOG_SHA256 = "75fa146ac19bf6aa5f799265b6fc031b725c1e1b2e044854da91b31898d5876e"
FIRST_ADMISSION_CATALOG_SHA256 = (
    "94ac4d193cbfe8c2ec04e54024221bc2c3a534c0ae014d381663b86174b3dcc1"
)
PARENT_CATALOG_SHA256 = "818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2"
ACTIVE_ATLAS_VERSION = "v28"
ACTIVE_ATLAS_COUNT = 2_764
ACTIVE_ATLAS_IDENTITY = "4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b"
ACTIVE_ATLAS_CATALOG_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"
ACTIVE_ATLAS_HTML_REVISION = ACTIVE_ATLAS_CATALOG_SHA256[:12]
BUNDLE_SHA256 = "627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9"
HISTORICAL_V25_BUNDLE_SHA256 = (
    "d4532076049be869e4e397d0fcee81b668bd3fd5c7d9173028bb1bdb80b9793a"
)
SECOND_WAVE_BUNDLE_SHA256 = (
    "c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d"
)
SECOND_WAVE_BRANCHES = {
    "T13": ("integer-linear-algebra", "rectangular_matrix_rank_exists_unique"),
    "G095": ("hensel-lifting", "integer_polynomial_prime_simple_root_lifts_all_positive_powers"),
    "G011": ("generalized-crt", "crt_pairwise_compatible_prefix_normalized_exists_unique"),
}
SECOND_WAVE_SLUGS = {
    "integer-linear-algebra", "hensel-lifting", "generalized-crt", "multinomial-kummer",
    "prime-count-chebyshev", "cornacchia", "cauchy-davenport",
}
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
    (
        "constructive-breakthrough-layer-explorer",
        (
            "matrix-cofactor-expansion",
            "polynomial-taylor-hensel",
            "generalized-crt-compatibility",
        ),
    ),
)
ALL_FAMILIES = tuple(
    (layer, slug) for layer, families in LAYER_FAMILIES for slug in families
)
HISTORICAL_FIRST_ADMISSION_BY_LAYER = {
    "constructive-next-layer-explorer": "v20",
    "constructive-advanced-layer-explorer": "v21",
    "constructive-transport-layer-explorer": "v22",
    "constructive-milestone-closure-explorer": "v23",
    "constructive-research-layer-explorer": "v24",
    "constructive-breakthrough-layer-explorer": "v25",
}

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
        "canonical prime-power representative",
    ),
    _RootEvidence(
        "generalized-crt-fold", "G011",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f",
        201, "CR001B", "CRTPrefixLCM", "full_generalized_crt_proved",
        "unrestricted pairwise gcd compatibility",
    ),
)

HISTORICAL_PARTIAL_MILESTONE_ROOTS = {
    "T13": (
        "signed_matrix_cofactor_family_and_fold_exists",
        "1f013b934c7540f73e135257094d612345f43f3163b5ee7280dbe97f4f142d2a",
        257,
    ),
    "G095": (
        "beta_horner_hensel_lift_exists",
        "9cfc4633ea27c492b0deb35a56fe44b25b8dbf50d56fb27f29285f74b6c58a8b",
        276,
    ),
    "G011": (
        "crt_merge_compatible_prefix_canonical_exists_unique",
        "9e3d68192e707b5953b2fd3c9e4716e9fe90317f63be49734bbed00e3492b927",
        288,
    ),
}

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
    sealed_v25_catalog = _json(SEALED_V25_CATALOG_PATH)
    sealed_v25_channels = _json(SEALED_V25_CHANNELS_PATH)
    current_catalog = _json(CURRENT_CATALOG_PATH)
    current_channels = _json(CURRENT_CHANNELS_PATH)
    parent = _json(PARENT_CATALOG_PATH)
    assert _digest(CATALOG_PATH) == FIRST_ADMISSION_CATALOG_SHA256
    assert _digest(SEALED_V25_CATALOG_PATH) == SEALED_V25_CATALOG_SHA256
    assert _digest(CURRENT_CATALOG_PATH) == ACTIVE_ATLAS_CATALOG_SHA256
    assert _digest(PARENT_CATALOG_PATH) == PARENT_CATALOG_SHA256
    assert catalog["schema"] == "peano-library-alpha-snapshot-v24"
    assert catalog["theorem_count"] == catalog["checked_use_count"] == FIRST_ADMISSION_COUNT
    assert len(catalog["theorems"]) == FIRST_ADMISSION_COUNT
    assert catalog["stable_count"] == STABLE_COUNT
    assert catalog["edition_identity_sha256"] == FIRST_ADMISSION_IDENTITY
    assert catalog["parent_alpha_v23"]["theorem_count"] == PARENT_COUNT
    assert catalog["parent_alpha_v23"]["edition_identity_sha256"] == PARENT_IDENTITY
    assert parent["theorem_count"] == parent["checked_use_count"] == PARENT_COUNT
    assert parent["stable_count"] == STABLE_COUNT

    promotion = catalog["alpha_v24_research_layer_promotion"]
    assert promotion["checked_use_before"] == PARENT_COUNT
    assert promotion["checked_use_after"] == FIRST_ADMISSION_COUNT
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
    assert alpha["theorem_count"] == alpha["checked_use_count"] == FIRST_ADMISSION_COUNT
    assert alpha["alpha_v24_frontier_new_count"] == NEW_THEOREM_COUNT
    assert alpha["edition_identity_sha256"] == FIRST_ADMISSION_IDENTITY
    assert alpha["artifact_sha256"] == FIRST_ADMISSION_CATALOG_SHA256

    assert sealed_v25_catalog["schema"] == "peano-library-alpha-snapshot-v25"
    assert sealed_v25_catalog["theorem_count"] == sealed_v25_catalog["checked_use_count"] == SEALED_V25_COUNT
    assert sealed_v25_catalog["edition_identity_sha256"] == SEALED_V25_IDENTITY
    assert sealed_v25_catalog["parent_alpha_v24"]["edition_identity_sha256"] == (
        FIRST_ADMISSION_IDENTITY
    )
    assert sealed_v25_catalog["parent_alpha_v24"]["artifacts"]["catalog"]["sha256"] == (
        FIRST_ADMISSION_CATALOG_SHA256
    )
    assert sealed_v25_channels["schema"] == "peano-library-channels-v25"
    assert sealed_v25_channels["channels"]["alpha"]["artifact_sha256"] == SEALED_V25_CATALOG_SHA256
    assert sealed_v25_channels["channels"]["alpha"]["theorem_count"] == SEALED_V25_COUNT

    assert current_catalog["schema"] == "peano-library-alpha-snapshot-v28"
    assert current_catalog["theorem_count"] == current_catalog["checked_use_count"] == ACTIVE_ATLAS_COUNT
    assert current_catalog["stable_count"] == STABLE_COUNT
    assert current_catalog["edition_identity_sha256"] == ACTIVE_ATLAS_IDENTITY
    assert current_catalog["theorems"][:SEALED_V25_COUNT] == sealed_v25_catalog["theorems"]
    assert current_catalog["parent_alpha_v25"]["edition_identity_sha256"] == SEALED_V25_IDENTITY
    assert current_catalog["parent_alpha_v25"]["artifacts"]["catalog"]["sha256"] == (
        SEALED_V25_CATALOG_SHA256
    )
    assert current_channels["schema"] == "peano-library-channels-v28"
    assert current_channels["channels"]["alpha"]["artifact_sha256"] == ACTIVE_ATLAS_CATALOG_SHA256
    assert current_channels["channels"]["alpha"]["theorem_count"] == ACTIVE_ATLAS_COUNT
    assert current_channels["channels"]["stable"]["theorem_count"] == STABLE_COUNT


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
    assert campaign["meta"]["current_alpha_version"] == ACTIVE_ATLAS_VERSION
    assert campaign["meta"]["current_alpha_checked_use_count"] == ACTIVE_ATLAS_COUNT
    from constructive_lower_layer_definition_graph import build_definition_graph

    assert len(campaign["nodes"]) == 144
    assert definition_graph == build_definition_graph(campaign)
    assert definition_graph["definition_count"] == len(campaign["definitions"])

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
def test_new_full_milestones_keep_their_exact_historical_partial_receipts(
    root: _RootEvidence, campaign: dict,
) -> None:
    node = next(item for item in campaign["nodes"] if item["id"] == root.milestone)
    evidence = node["historical_partial_evidence"]
    current_name, current_digest, current_node = HISTORICAL_PARTIAL_MILESTONE_ROOTS[root.milestone]
    assert node["status"] == "alpha_closed"
    assert evidence["implementation"] == "independently_closed_partial"
    assert evidence["alpha_version"] == SEALED_V25_VERSION
    assert evidence["alpha_enrolled"]
    assert evidence["partial_component_checked_use"]
    assert not evidence["checked_use"]
    assert not evidence["stable_member"]
    assert evidence["partial_theorem_name"] == current_name
    assert evidence["partial_theorem_statement_sha256"] == current_digest
    assert evidence["bundle_node_id"] == current_node
    assert evidence["bundle_sha256"] == HISTORICAL_V25_BUNDLE_SHA256
    assert evidence["bundle_nodes"] == 302
    assert evidence["independent_lean_bundle_verified"]
    assert evidence[root.full_scope_flag] is False
    assert root.definition in node["definition_refs"]
    complete = node["evidence"]
    _, complete_name = SECOND_WAVE_BRANCHES[root.milestone]
    rows = {item["name"]: item for item in _json(CURRENT_CATALOG_PATH)["theorems"]}
    actual = rows[complete_name]
    assert complete["theorem_name"] == complete_name
    assert complete["theorem_statement_sha256"] == actual["statement_sha256"]
    assert complete["bundle_node_id"] == actual["empty_context_closure"]["bundle_node_id"]
    assert complete["bundle_sha256"] == SECOND_WAVE_BUNDLE_SHA256
    assert complete["bundle_nodes"] == 1224
    # Current presentation is v28; the independent full proof was first
    # admitted in v27, and its original closure receipt must remain exact.
    assert complete["alpha_version"] == "v27"
    assert complete["checked_use"] is True
    assert complete["independent_lean_bundle_verified"] is True
    assert complete[root.full_scope_flag] is True
    assert "partial_component_checked_use" not in complete


@pytest.mark.parametrize("layer,expected_families", LAYER_FAMILIES)
def test_all_published_layer_manifests_authorize_current_v28(
    layer: str, expected_families: tuple[str, ...],
) -> None:
    manifest = _json(STATIC / layer / "manifest.json")
    assert manifest["alpha_edition_version"] == ACTIVE_ATLAS_VERSION
    assert {row["slug"] for row in manifest["families"]} == set(expected_families)
    if layer == "constructive-frontier-explorer":
        assert manifest["alpha_edition_identity_sha256"] == ACTIVE_ATLAS_IDENTITY
        assert manifest["alpha_edition_checked_use_count"] == ACTIVE_ATLAS_COUNT
        assert manifest["alpha_catalog_sha256"] == ACTIVE_ATLAS_CATALOG_SHA256
    else:
        assert manifest["edition_identity_sha256"] == ACTIVE_ATLAS_IDENTITY
        assert manifest["catalog_sha256"] == ACTIVE_ATLAS_CATALOG_SHA256
        assert manifest["html_revision"] == ACTIVE_ATLAS_HTML_REVISION
        first_admission_version = HISTORICAL_FIRST_ADMISSION_BY_LAYER[layer]
        assert manifest["alpha_first_enrolled_version"] == first_admission_version
        first_admission_catalog = CATALOG_PATH.with_name(f"catalog-{first_admission_version}.json")
        assert manifest["first_enrollment_catalog_sha256"] == _digest(first_admission_catalog)


def test_public_hub_has_all_36_campaign_cards_and_both_original_anchors() -> None:
    source = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")
    parser = _HubMarkup()
    parser.feed(source)

    anchors = [card for card in parser.cards if "candidate-card" not in card["classes"]]
    campaigns = [card for card in parser.cards if "candidate-card" in card["classes"]]
    assert len(parser.cards) == 38
    assert len(anchors) == 2
    assert len(ALL_FAMILIES) == 25
    lower_layer = {
        "arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers",
    }
    assert len(campaigns) == len(ALL_FAMILIES) + len(SECOND_WAVE_SLUGS) + len(lower_layer) == 36
    assert {next(iter(card["classes"] - {"family-card"})) for card in anchors} == {
        "qr-card", "bertrand-card"
    }

    slugs = {slug for _, slug in ALL_FAMILIES} | SECOND_WAVE_SLUGS | lower_layer
    linked_slugs = {
        link["href"].split("/?", 1)[0]
        for card in campaigns
        for link in card["links"]
        if link.get("class") == "primary-action"
    }
    assert linked_slugs == slugs
    for slug in slugs | {"quadratic-reciprocity", "bertrand-postulate"}:
        assert f'href="{slug}/?v={ACTIVE_ATLAS_HTML_REVISION}"' in source

    assert "Alpha v28" in source
    assert f"{ACTIVE_ATLAS_COUNT:,} theorems" in source
    assert "432 unchanged Stable theorems" in source
    definitions = _json(DEFINITION_GRAPH_PATH)
    assert f'{definitions["definition_count"]} structured first-order definitions' in source
    assert f'{definitions["reviewed_definition_count"]} reviewed conservative definitions' in source
    assert BUNDLE_NAME in source

    for root in RESEARCH_ROOTS:
        assert f"focus={root.milestone}&amp;v={ACTIVE_ATLAS_HTML_REVISION}" in source
        assert f"view=definition&amp;focus={root.definition}&amp;v={ACTIVE_ATLAS_HTML_REVISION}" in source
    assert "T13, G095 and G011 remain OPEN" not in source
    for slug, _theorem in SECOND_WAVE_BRANCHES.values():
        assert f'href="{slug}/?v={ACTIVE_ATLAS_HTML_REVISION}"' in source
    assert "Fermat descent remains conditional" not in source


@pytest.mark.parametrize("layer,slug", ALL_FAMILIES, ids=[slug for _, slug in ALL_FAMILIES])
def test_every_campaign_retains_original_qr_design_definition_graph_and_v28_authority(
    layer: str, slug: str,
) -> None:
    revision = ACTIVE_ATLAS_HTML_REVISION
    version = ACTIVE_ATLAS_VERSION
    identity = ACTIVE_ATLAS_IDENTITY
    catalog_sha256 = ACTIVE_ATLAS_CATALOG_SHA256
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
    assert f'href="../assets/proofs.css?v={revision}"' in landing
    assert f'href="explorer/defined/?v={revision}"' in landing
    assert f'href="explorer/?v={revision}"' in landing
    assert "explorer/defined/graph.html?" in landing
    assert f"v={revision}" in landing
    assert f"Alpha {version}" in landing
    assert "not Stable" in landing

    for path in (
        "explorer/index.html", "explorer/defined/index.html",
        "explorer/defined/graph.html", "explorer/defined/api/graph.json",
    ):
        assert (family_root / path).is_file(), f"{slug} lacks canonical {path}"

    corpus = _json(family_root / "api" / "corpus.json")
    assert corpus["alpha_edition_version"] == version
    assert corpus["alpha_edition_identity_sha256"] == identity
    assert corpus["alpha_catalog_sha256"] == catalog_sha256
    assert corpus["alpha_checked_use_node_count"] > 0
    assert corpus["definition_count"] > 0
    assert corpus["root_names"]

    graph = _json(family_root / "explorer" / "defined" / "api" / "graph.json")
    assert graph["alpha_edition_version"] == version
    if layer in HISTORICAL_FIRST_ADMISSION_BY_LAYER:
        first_admission_version = HISTORICAL_FIRST_ADMISSION_BY_LAYER[layer]
        assert corpus["alpha_first_enrolled_version"] == first_admission_version
        assert graph["alpha_first_enrolled_version"] == first_admission_version
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
    assert f"view=definition&amp;focus={name}&amp;v={ACTIVE_ATLAS_HTML_REVISION}" in page

    reviewed = next(
        item for item in definition_graph["reviewed_definitions"] if item["id"] == identifier
    )
    assert reviewed["name"] == name
    assert reviewed["route"] == slug
    assert campaign["definitions"][name]["parameters"] == reviewed["parameters"]


@pytest.mark.parametrize("root", RESEARCH_ROOTS, ids=lambda root: root.slug)
def test_historical_research_pages_link_new_closure_without_upgrading_old_proof_scope(root: _RootEvidence) -> None:
    family_root = STATIC / "constructive-research-layer-explorer" / root.slug
    landing = (family_root / "index.html").read_text(encoding="utf-8")
    corpus = _json(family_root / "api" / "corpus.json")
    graph = _json(family_root / "explorer" / "defined" / "api" / "graph.json")

    assert "Historical partial components only" in landing
    complete_slug, complete_name = SECOND_WAVE_BRANCHES[root.milestone]
    assert f'{complete_slug}/?v={ACTIVE_ATLAS_HTML_REVISION}' in landing
    assert complete_name not in corpus["tags"]
    assert root.name in landing
    assert f"tag/{root.tag}.html?v={ACTIVE_ATLAS_HTML_REVISION}" in landing
    assert BUNDLE_SHA256 in landing
    for evidence in (corpus, graph):
        assert evidence["milestone_status"] == "alpha_closed"
        assert evidence["milestone_checked_use"]
        assert evidence["historical_component_only"]
        assert evidence["historical_milestone_status"] == "open"
        assert evidence["historical_partial_checked_use"]
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


def test_quadratic_reciprocity_sealed_v25_sidecar_never_replaces_immutable_evidence() -> None:
    manifest = _json(STATIC / "pa-proof-explorer" / "manifest.json")
    current = _json(QR_CURRENT_CORPUS_PATH)
    assert current["schema"] == "peano-lab-pa-proof-corpus-v1"
    assert current["alpha_edition_version"] == SEALED_V25_VERSION
    assert current["alpha_edition_identity_sha256"] == SEALED_V25_IDENTITY
    assert current["alpha_edition_checked_use_count"] == SEALED_V25_COUNT
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


def test_bertrand_preserves_historical_proof_and_sealed_v25_reading_authority() -> None:
    corpus = _json(BERTRAND_CORPUS_PATH)
    assert corpus["alpha_edition_version"] == SEALED_V25_VERSION
    assert corpus["alpha_edition_identity_sha256"] == SEALED_V25_IDENTITY
    assert corpus["alpha_edition_checked_use_count"] == SEALED_V25_COUNT
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
    assert f"Alpha: {ACTIVE_ATLAS_COUNT:,} proofs" in app_page
    for root in RESEARCH_ROOTS:
        assert f'data-cmd="pa lib alpha {root.name}"' in app_page
