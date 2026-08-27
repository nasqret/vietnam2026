"""Read-only current hub contract preserving first-wave proof provenance."""

from __future__ import annotations

from hashlib import sha256
import html
import importlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import constructive_second_wave_definition_graph as definition_graph
from peano_lab.library.theorems import TheoremSpec


HUB = ROOT / "deploy/proofs/index.html"
CATALOG = ROOT / "artifacts/peano-library/alpha/catalog-v27.json"
FIRST_ADMISSION_CATALOG = ROOT / "artifacts/peano-library/alpha/catalog-v26.json"
FAMILY = ROOT / "book/_static/constructive-frontier-explorer/pythagorean-fermat-four"
ROOT_TAGS = {
    "pythagorean_positive_primitive_classification": "PF0023",
    "fermat_four_strict_descent_proved": "PF002M",
    "fermat_four_complete_classification": "PF002S",
    "fermat_four_positive_sum_not_square": "PF002T",
}
SECOND_WAVE_FAMILIES = {
    "integer-linear-algebra": ("matrix_determinants", 182, "T13"),
    "hensel-lifting": ("hensel", 40, "G095"),
    "generalized-crt": ("generalized_crt", 24, "G011"),
    "multinomial-kummer": ("multinomial_kummer", 19, "G035"),
    "prime-count-chebyshev": ("chebyshev", 55, "G027"),
    "cornacchia": ("cornacchia", 30, "G107"),
    "cauchy-davenport": ("cauchy_davenport", 72, "G051"),
}


@pytest.fixture(scope="module")
def surface():
    page = HUB.read_text(encoding="utf-8")
    cards: dict[str, str] = {}
    for card in re.findall(r"<article\b[^>]*>.*?</article>", page, re.S):
        link = re.search(r'<a class="primary-action" href="([^"]+)"', card)
        assert link is not None
        slug = urlsplit(html.unescape(link.group(1))).path.strip("/")
        assert slug not in cards
        cards[slug] = card
    return page, cards, sha256(CATALOG.read_bytes()).hexdigest()[:12]


def test_current_hub_authority_matches_sealed_catalog_and_actual_definition_dag(surface) -> None:
    page, _cards, _revision = surface
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    campaign = json.loads((ROOT / "book/_static/constructive-grand-campaign/campaign.json").read_text())
    graph = definition_graph.build_definition_graph(campaign)
    assert f"All {catalog['checked_use_count']:,} theorems have checked-use authority" in page
    assert f"{catalog['stable_count']} unchanged Stable theorems" in page
    assert f"{catalog['checked_use_count'] - catalog['stable_count']:,} additional Alpha-closed theorems" in page
    assert f"{catalog['edge_count']:,} genuine theorem dependencies" in page
    assert f"{graph['definition_count']} structured first-order definitions" in page
    assert f"{graph['reviewed_definition_count']} reviewed conservative definitions" in page
    assert f"{graph['reviewed_definition_edge_count']} audited definition prerequisites" in page
    assert f"{graph['compatible_reviewed_match_count']} signature-compatible definition links" in page
    assert "Immutable Alpha v27" in page
    assert "2,138 theorems have checked-use authority" not in page


def test_established_hub_structure_and_every_family_route_are_preserved(surface) -> None:
    page, cards, revision = surface
    assert len(cards) == 34
    assert '<header class="hero">' in page
    assert '<section class="family-grid" aria-label="Proof families">' in page
    assert '<section class="family-grid frontier-grid"' in page
    assert '<section class="method-note">' in page
    assert f'href="assets/proofs.css?v={revision}"' in page
    assert "<style" not in page
    assert "<script" not in page
    for href in re.findall(r'href="([^"]+)"', page):
        target = urlsplit(html.unescape(href))
        if target.scheme or target.path.startswith("artifacts/"):
            continue
        assert parse_qs(target.query).get("v") == [revision], href
    assert "Alpha v26 checked" not in page
    assert "all 34 proof families" in page


def test_unrelated_historical_family_counts_do_not_change(surface) -> None:
    _page, cards, _revision = surface
    for slug, count in {
        "matrix-cofactor-expansion": 29,
        "polynomial-taylor-hensel": 19,
        "generalized-crt-compatibility": 24,
        "matrix-determinant-minors": 17,
        "polynomial-hensel": 15,
        "generalized-crt-fold": 27,
        "euclidean-logarithmic-bound": 17,
        "binary-digit-extraction": 24,
        "primes-three-mod-four": 18,
        "polynomial-horner": 7,
        "matrix-dot-product": 10,
        "bertrand-prime-chains": 13,
        "continued-fractions": 9,
        "matrix-coded-products": 23,
        "euclidean-complexity": 15,
        "binary-modular-exponentiation": 16,
        "binary-length": 21,
        "euclidean-gcd-transport": 20,
        "binary-modular-execution": 19,
    }.items():
        assert f"· {count} " in cards[slug]
    for value in ("557", "1,787", "40"):
        assert f"<dt>{value}</dt>" in cards["quadratic-reciprocity"]
    for value in ("544", "1,917", "28"):
        assert f"<dt>{value}</dt>" in cards["bertrand-postulate"]


def test_pythagorean_family_count_is_44_historical_plus_58_real_additions(surface) -> None:
    _page, cards, _revision = surface
    historical = (
        ("pythagorean_fermat_four_candidate", "make_pythagorean_fermat_four_candidate_theorems"),
        ("pythagorean_primitive_candidate", "make_pythagorean_primitive_candidate_theorems"),
    )
    additions = (
        ("coprime_square_factor_candidate", "make_coprime_square_factor_candidate_theorems"),
        ("pythagorean_inverse_candidate", "make_pythagorean_inverse_candidate_theorems"),
        ("fermat_four_descent_candidate", "make_fermat_four_descent_candidate_theorems"),
    )
    counts = [
        sum(len(getattr(importlib.import_module("peano_lab.library." + module), factory)(TheoremSpec)) for module, factory in group)
        for group in (historical, additions)
    ]
    assert counts == [44, 58]
    card = cards["pythagorean-fermat-four"]
    assert "102 independently proved theorems" in card
    assert "44 historical foundations and 58 new" in card
    assert "exact first-admission evidence" in card
    assert "G077 and G078 complete" in card
    assert "not Stable" in card
    assert re.search(r"\bconditional\b", card) is None
    assert "Open descent obligation" not in card


@pytest.mark.parametrize("name,tag", ROOT_TAGS.items())
def test_completed_roots_link_to_the_actual_defined_theorem_pages(surface, name: str, tag: str) -> None:
    _page, cards, revision = surface
    assert f'href="pythagorean-fermat-four/explorer/defined/tag/{tag}.html?v={revision}"' in cards["pythagorean-fermat-four"]
    graph = json.loads((FAMILY / "explorer/defined/api/graph.json").read_text())
    node = next(node for node in graph["nodes"] if node["name"] == name)
    assert node["tag"] == tag
    assert node["alpha_checked_use"] is True
    assert node["admitted_to_stable"] is False
    assert (FAMILY / f"explorer/defined/tag/{tag}.html").is_file()


def test_completed_goals_leave_future_targets_and_keep_atlas_links(surface) -> None:
    page, cards, revision = surface
    future = next(paragraph for paragraph in re.findall(r"<p>.*?</p>", page, re.S) if "Where the programme goes next:" in paragraph)
    assert "G077" not in future
    assert "G078" not in future
    for _campaign, _count, milestone in SECOND_WAVE_FAMILIES.values():
        assert milestone not in future
    assert "These are research targets, not claims of completed proofs" in future
    for milestone in ("G077", "G078"):
        assert f'href="grand-campaign/?view=goal&amp;focus={milestone}&amp;v={revision}"' in cards["pythagorean-fermat-four"]
    assert "Seven completed second-wave targets:" in page
    assert "full prime-power Hensel, and arbitrary pairwise-compatible non-coprime CRT milestones remain open" not in page


def test_v26_bundle_and_receipt_links_bind_the_actual_certificate(surface) -> None:
    page, _cards, _revision = surface
    artifact = ROOT / "research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json"
    receipt = ROOT / "research/arithmetic-library/alpha-v26-first-wave-receipt.md"
    catalog = json.loads(FIRST_ADMISSION_CATALOG.read_text())
    documents = {row["path"]: row for row in catalog["evidence_documents"]}
    for path in (artifact, receipt):
        record = documents[path.relative_to(ROOT).as_posix()]
        assert sha256(path.read_bytes()).hexdigest() == record["sha256"]
        assert f'href="artifacts/{path.name}"' in page
    bundle = json.loads(artifact.read_text())
    assert bundle[0] == "peano-lab-bundle-v1"
    assert len(bundle[3]) == 216
    assert "kernel- and Lean-verified 216-node proof certificate" in page
    assert 'href="artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json"' in page


@pytest.mark.parametrize("slug", tuple(SECOND_WAVE_FAMILIES))
def test_second_wave_cards_have_exact_new_counts_and_closed_milestone_routes(surface, slug: str) -> None:
    _page, cards, revision = surface
    campaign, count, milestone = SECOND_WAVE_FAMILIES[slug]
    catalog = json.loads(CATALOG.read_text())
    promotion = catalog["alpha_v27_second_wave_promotion"]
    assert promotion["campaign_counts"][campaign] == count
    card = cards[slug]
    assert f"Alpha v27 checked use · {count} independently proved theorems" in card
    assert "independently kernel and Lean verified; not Stable" in card
    assert f'href="{slug}/?v={revision}"' in card
    assert f'href="grand-campaign/?view=goal&amp;focus={milestone}&amp;v={revision}"' in card


def test_second_wave_cards_do_not_overclaim_their_exact_mathematical_scope(surface) -> None:
    _page, cards, _revision = surface
    matrix = cards["integer-linear-algebra"]
    assert "T13 finite substrate complete" in matrix
    assert "Lattice index equals determinant, determinant multiplicativity, Smith and Hermite normal forms, and lattice reduction are not claimed" in matrix
    assert "Singular roots and p-adic completion are separate targets" in cards["hensel-lifting"]
    assert "Empty lists and zero moduli are included" in cards["generalized-crt"]
    assert "Empty lists and zero parts are included" in cards["multinomial-kummer"]
    assert "N ≤ 8kℓ and kℓ ≤ 8N" in cards["prime-count-chebyshev"]
    assert "every N ≥ 2" in cards["prime-count-chebyshev"]
    assert "This is not a general x² + d y² solver" in cards["cornacchia"]
    assert "for nonempty A and B" in cards["cauchy-davenport"]


def test_v27_bundle_and_receipt_bind_all_actual_second_wave_proofs(surface) -> None:
    page, _cards, _revision = surface
    catalog = json.loads(CATALOG.read_text())
    promotion = catalog["alpha_v27_second_wave_promotion"]
    assert promotion["frontier_new_count"] == 422
    assert promotion["independent_lean_bundle_verified"] is True
    documents = {row["path"]: row for row in catalog["evidence_documents"]}
    artifact = ROOT / "research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json"
    receipt = ROOT / "research/arithmetic-library/alpha-v27-second-wave-receipt.md"
    for path in (artifact, receipt):
        assert sha256(path.read_bytes()).hexdigest() == documents[path.relative_to(ROOT).as_posix()]["sha256"]
        assert f'href="artifacts/{path.name}"' in page
    assert sha256(artifact.read_bytes()).hexdigest() == "c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d"
    bundle = json.loads(artifact.read_text())
    assert bundle[0] == "peano-lab-bundle-v1"
    assert len(bundle[3]) == 1224
    assert "kernel- and Lean-verified 1,224-node proof certificate" in page
