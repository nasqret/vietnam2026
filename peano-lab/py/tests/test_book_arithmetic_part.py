"""Contracts for the generated, interactive arithmetic Jupyter Book part."""

from __future__ import annotations

import collections
import html
import json
from pathlib import Path
import re
import subprocess
import sys


REPO = Path(__file__).resolve().parents[3]
BOOK = REPO / "book"
ATLAS = BOOK / "arithmetic-library" / "theorem-atlas.md"
GUIDE = BOOK / "arithmetic-library" / "guided-tour.md"
SNAPSHOT = REPO / "artifacts" / "peano-library" / "catalog-v1.json"
RESEARCH = REPO / "research" / "arithmetic-library" / "catalog.json"
GENERATOR = REPO / "scripts" / "build_arithmetic_book_atlas.py"
BOOK_GATE = REPO / "scripts" / "verify_book_commands.py"

DOMAIN_COUNTS = {
    "equality": 10,
    "addition": 12,
    "multiplication": 19,
    "order": 29,
    "divisibility": 20,
    "congruence": 34,
    "division": 9,
    "gcd_coprime": 25,
    "primes": 13,
    "factorization": 76,
    "quadratic_residues": 137,
}
PROOF_SNAPSHOT_COMMIT = "5fff3eab2a7599035a6833c52b658da118f4a20c"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_arithmetic_dashboard_tour_atlas_and_dependency_chapters_are_ordered() -> None:
    toc = (BOOK / "_toc.yml").read_text(encoding="utf-8")
    chapters = (
        "index",
        "guided-tour",
        "theorem-atlas",
        "proof-explorer",
        "language-and-trust",
        "proof-sharing",
        "dependency-ladder",
        "divisibility-and-congruence",
        "gcd-and-bezout",
        "primes-and-factorization",
        "quadratic-reciprocity",
        "source-audit",
        "using-the-library",
    )
    positions = [
        toc.index(f"- file: arithmetic-library/{chapter}") for chapter in chapters
    ]
    assert positions == sorted(positions)
    for chapter in chapters:
        source = BOOK / "arithmetic-library" / f"{chapter}.md"
        assert source.is_file()
        assert source.read_text(encoding="utf-8").startswith("# ")


def test_generated_atlas_is_byte_current() -> None:
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_atlas_embeds_every_checked_statement_script_receipt_and_edge() -> None:
    snapshot = _load(SNAPSHOT)
    source = ATLAS.read_text(encoding="utf-8")
    cards = re.findall(
        r'<article class="pa-theorem-card" id="theorem-[^"]+".*?</article>',
        source,
        flags=re.DOTALL,
    )
    by_name: dict[str, str] = {}
    for card in cards:
        match = re.search(r'data-name="([^"]+)"', card)
        assert match is not None
        assert match.group(1) not in by_name
        by_name[match.group(1)] = card

    theorems = snapshot["theorems"]
    assert len(theorems) == snapshot["theorem_count"] == 384
    assert len(by_name) == 384
    assert sum(len(theorem["dependencies"]) for theorem in theorems) == 1_038

    for theorem in theorems:
        card = by_name[theorem["name"]]
        recipe = [f"pa prove {theorem['statement']}"]
        recipe.extend(f"use {name}" for name in theorem["dependencies"])
        recipe.extend(theorem["script"])
        recipe.append("qed")
        assert html.escape(theorem["statement"], quote=True) in card
        assert html.escape("\n".join(recipe), quote=True) in card
        assert theorem["certificate_sha256"] in card
        assert f"<dd>{theorem['proof_nodes']:,}</dd>" in card
        assert f"<dd>{theorem['distinct_proof_objects']:,}</dd>" in card
        assert f"<dd>{theorem['reused_proof_references']:,}</dd>" in card
        assert f"<dd>{theorem['proof_depth']}</dd>" in card
        assert f"<dd>{theorem['cut_nodes']:,}</dd>" in card
        for dependency in theorem["dependencies"]:
            assert f'href="#theorem-{dependency}"' in card

    assert source.count('data-status="blocked_by_language"') == 1
    assert "Bézout identity with integer coefficients" in source
    assert "This card deliberately contains no native proof script" in source


def test_research_domains_and_runtime_names_match_the_atlas_contract() -> None:
    snapshot_names = {
        theorem["name"] for theorem in _load(SNAPSHOT)["theorems"]
    }
    rows = _load(RESEARCH)["lemmas"]
    checked_names: set[str] = set()
    counts: collections.Counter[str] = collections.Counter()
    for row in rows:
        if row["status"] == "blocked_by_language":
            continue
        peano = row["peano"]
        name = peano.get("existing_name") or row["id"]
        assert name not in checked_names
        checked_names.add(name)
        counts[row["domain"]] += 1
    assert checked_names == snapshot_names
    assert dict(counts) == DOMAIN_COUNTS


def test_interaction_assets_are_local_progressive_and_auto_discovered_once() -> None:
    config = (BOOK / "_config.yml").read_text(encoding="utf-8")
    css = (BOOK / "_static" / "arithmetic-book.css").read_text(encoding="utf-8")
    js = (BOOK / "_static" / "arithmetic-book.js").read_text(encoding="utf-8")
    # Jupyter Book 1.x auto-discovers the local _static tree. Repeating these
    # Sphinx keys would load the same assets twice, but the files themselves
    # are a required, versioned part of the Book.
    assert "html_static_path" not in config
    assert "html_css_files" not in config
    assert "html_js_files" not in config
    assert (BOOK / "_static" / "arithmetic-book.css").is_file()
    assert (BOOK / "_static" / "arithmetic-book.js").is_file()
    assert (BOOK / "_static" / "pa-proof-explorer" / "assets" / "explorer.css").is_file()
    assert (BOOK / "_static" / "pa-proof-explorer" / "assets" / "explorer.js").is_file()
    assert "fetch(" not in js
    assert "innerHTML" not in js
    assert "prefers-reduced-motion" in css
    assert "@media print" in css
    atlas = ATLAS.read_text(encoding="utf-8")
    assert "```{raw} html\n<div class=\"pa-atlas\"" in atlas
    assert "</div>\n```\n\n## How to use this atlas" in atlas
    assert "data-pa-search" in atlas
    assert "data-pa-lab-command" not in atlas
    assert "after promotion" in atlas
    assert f"github.com/nasqret/vietnam2026/blob/{PROOF_SNAPSHOT_COMMIT}/" in atlas
    assert "github.com/nasqret/vietnam2026/blob/peano-lab/" not in atlas
    assert "data-pa-learning-route" in GUIDE.read_text(encoding="utf-8")
    for line in GUIDE.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("<"):
            assert "$" not in line, f"raw HTML contains unrendered TeX: {line}"
    assert "http://" not in css + js
    assert "https://" not in css + js


def test_guided_tour_sessions_replay_through_the_real_peano_driver() -> None:
    result = subprocess.run(
        [sys.executable, str(BOOK_GATE), str(GUIDE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all commands replay cleanly" in result.stdout
    assert "2 session blocks" in result.stdout


def test_arithmetic_narrative_does_not_reintroduce_the_pre_fta_blocker() -> None:
    texts = {
        path.name: path.read_text(encoding="utf-8")
        for path in (BOOK / "arithmetic-library").glob("*.md")
        if path.name != "theorem-atlas.md"
    }
    joined = "\n".join(texts.values())
    assert "native FTA is not yet proved" not in joined
    assert "The library does not yet have greatest-prime descent" not in joined
    assert "planned and expressible" not in joined
    assert "guided-tour" in (BOOK / "intro.md").read_text(encoding="utf-8")
    assert "theorem-atlas" in (BOOK / "peano" / "index.md").read_text(
        encoding="utf-8"
    )
