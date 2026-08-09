"""Contracts for the generated, interactive arithmetic Jupyter Book part."""

from __future__ import annotations

import collections
import hashlib
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
K3B_CHAPTER = BOOK / "arithmetic-library" / "cell-history-and-lookup.md"
K3B_SITE = BOOK / "_static" / "pa-proof-explorer" / "k3b"
LIBRARY_EDITIONS = BOOK / "arithmetic-library" / "library-editions.md"
BERTRAND_CAMPAIGN = BOOK / "arithmetic-library" / "bertrand-campaign.md"
K3B_RECEIPT = (
    REPO
    / "artifacts"
    / "peano-library"
    / "ha-k3b-listat-full-closure-219217.json"
)
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
    "congruence": 58,
    "division": 13,
    "gcd_coprime": 45,
    "primes": 13,
    "factorization": 76,
    "quadratic_residues": 137,
}
PROOF_SNAPSHOT_COMMIT = "2037b87905817ada187e2477af22c57ff47fb512"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_arithmetic_dashboard_tour_atlas_and_dependency_chapters_are_ordered() -> None:
    toc = (BOOK / "_toc.yml").read_text(encoding="utf-8")
    chapters = (
        "index",
        "library-editions",
        "guided-tour",
        "theorem-atlas",
        "proof-explorer",
        "language-and-trust",
        "proof-sharing",
        "dependency-ladder",
        "divisibility-and-congruence",
        "gcd-and-bezout",
        "strict-ha-campaign",
        "cell-history-and-lookup",
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


def test_alpha_k3b_book_chapter_and_sparse_graph_match_the_sealed_receipt() -> None:
    chapter = K3B_CHAPTER.read_text(encoding="utf-8")
    site = (K3B_SITE / "index.html").read_text(encoding="utf-8")
    css = (K3B_SITE / "assets" / "k3b.css").read_text(encoding="utf-8")
    javascript = (K3B_SITE / "assets" / "k3b.js").read_text(encoding="utf-8")
    receipt_bytes = K3B_RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)

    assert hashlib.sha256(receipt_bytes).hexdigest() == (
        "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8"
    )
    assert len(receipt_bytes) == 10_550
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["provenance"] == {
        "local_commit": "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
        "local_dirty": False,
        "payload_sha256": (
            "78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835"
        ),
    }
    assert all(row["dne_objects"] == 0 for row in receipt["results"].values())

    for exact in (
        "WMI job **219217**",
        "**Alpha-only**",
        "**closed checked**",
        "legacy evidence spelling\n`closed_checked_candidate`",
        "432-theorem Stable checked-use registry",
        "95,253",
        "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8",
        "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
        "78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835",
        "make ha-k3b-list-lookup-check",
    ):
        assert exact in chapter
    for name in receipt["selected_theorems"]:
        assert f"`{name}`" in chapter

    match = re.search(
        r'<script id="k3b-graph-data" type="application/json">\s*(\{.*?\})\s*</script>',
        site,
        flags=re.DOTALL,
    )
    assert match is not None
    graph = json.loads(match.group(1))
    assert graph["schema"] == "peano-k3b-book-graph-v2"
    assert graph["orientation"] == "dependency_to_dependent"
    assert graph["default_focus"] == "cell_list_extensional"
    assert graph["receipt"] == {
        "artifact": "ha-k3b-listat-full-closure-219217.json",
        "artifact_commit": "51f6e081a4aa1223bcdff7ff3ff0a662de8f9b08",
        "artifact_sha256": (
            "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8"
        ),
        "job_id": "219217",
        "source_commit": "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
    }

    nodes = graph["nodes"]
    by_id = {node["id"]: node for node in nodes}
    assert len(by_id) == len(nodes) == 41
    assert collections.Counter(node["kind"] for node in nodes) == {
        "definition": 7,
        "stable": 12,
        "alpha": 22,
    }
    assert collections.Counter(node["release"] for node in nodes) == {
        "presentation": 7,
        "stable": 12,
        "alpha_only": 22,
    }
    assert collections.Counter(node["evidence"] for node in nodes) == {
        "conservative_definition": 7,
        "closed_checked": 34,
    }
    assert all("status" not in node for node in nodes)
    assert all(not node["id"].startswith(("PA", "PD")) for node in nodes)
    assert all("tag" not in node for node in nodes)

    edge_keys = [(edge["source"], edge["target"], edge["kind"]) for edge in graph["edges"]]
    assert len(edge_keys) == len(set(edge_keys))
    assert {edge["kind"] for edge in graph["edges"]} == {"proof", "notation"}
    assert all(edge["source"] in by_id and edge["target"] in by_id for edge in graph["edges"])

    for name in receipt["selected_theorems"]:
        node = by_id[name]
        closed = receipt["results"][name]
        assert node["release"] == "alpha_only"
        assert node["evidence"] == "closed_checked"
        assert node["metrics"] == {
            "nodes": closed["proof_nodes"],
            "depth": closed["proof_depth"],
            "objects": closed["proof_objects"],
            "edges": closed["proof_edges"],
            "reused": closed["reused_objects"],
            "cuts": closed["cuts"],
        }
        proof_dependencies = [
            edge["source"]
            for edge in graph["edges"]
            if edge["kind"] == "proof" and edge["target"] == name
        ]
        assert proof_dependencies == closed["direct_dependencies"]
        source = REPO / node["source_path"]
        audit = REPO / node["test_path"]
        assert source.is_file() and audit.is_file()
        assert node["source_line"] <= len(source.read_text(encoding="utf-8").splitlines())
        assert node["test_line"] <= len(audit.read_text(encoding="utf-8").splitlines())

    for node in nodes:
        if node["kind"] == "stable":
            assert (K3B_SITE / node["href"]).resolve().is_file()
        elif node["href"].startswith("../../../arithmetic-library/"):
            fragment = node["href"].split("#", 1)[1]
            assert f'id="{fragment}"' in chapter

    local_assets = re.findall(
        r'<(?:link|script)\b[^>]*(?:href|src)="([^"]+)"', site
    )
    assert local_assets == ["assets/k3b.css", "assets/k3b.js"]
    assert all((K3B_SITE / relative).is_file() for relative in local_assets)
    assert "https://" not in site
    assert "http://" not in site
    assert "fetch(" not in javascript
    assert "innerHTML" not in javascript
    assert "immediateIds" in javascript
    assert 'viewControl.value === "all"' in javascript
    assert 'edgeControl.value === "none"' in javascript
    assert "body.k3b-site .k3b-node-definition polygon" in css
    assert "body.k3b-site .k3b-node-alpha rect" in css
    assert "body.k3b-site .k3b-node-stable rect" in css
    assert 'var order = { definition: 0, stable: 1, alpha: 2 }' in javascript
    assert 'appendPair(metrics, "Release", node.release)' in javascript
    assert 'appendPair(metrics, "Evidence", node.evidence)' in javascript
    assert "prefers-reduced-motion" in css

    toc = (BOOK / "_toc.yml").read_text(encoding="utf-8")
    assert toc.index("- file: arithmetic-library/strict-ha-campaign") < toc.index(
        "- file: arithmetic-library/cell-history-and-lookup"
    ) < toc.index("- file: arithmetic-library/primes-and-factorization")
    assert toc.index("- file: arithmetic-library/index") < toc.index(
        "- file: arithmetic-library/library-editions"
    ) < toc.index("- file: arithmetic-library/guided-tour")
    assert "<cell-history-and-lookup>" in (
        BOOK / "arithmetic-library" / "index.md"
    ).read_text(encoding="utf-8")
    assert "<cell-history-and-lookup>" in (
        BOOK / "arithmetic-library" / "strict-ha-campaign.md"
    ).read_text(encoding="utf-8")


def test_alpha_and_stable_book_page_records_the_canonical_channel_contract() -> None:
    source = LIBRARY_EDITIONS.read_text(encoding="utf-8")
    bertrand = BERTRAND_CAMPAIGN.read_text(encoding="utf-8")
    index = (BOOK / "arithmetic-library" / "index.md").read_text(encoding="utf-8")
    artifacts = (REPO / "artifacts" / "README.md").read_text(encoding="utf-8")
    normalized_artifacts = " ".join(artifacts.split())
    proof_explorer = (
        BOOK / "arithmetic-library" / "proof-explorer.md"
    ).read_text(encoding="utf-8")
    normalized_proof_explorer = " ".join(proof_explorer.split())

    for exact in (
        "# Alpha and Stable library editions",
        "**885** theorems",
        "**902** theorems",
        "**923** theorems",
        "**965** theorems",
        "**972** theorems",
        "**993** theorems",
        "**570** theorems",
        "**2,641** edges / **45** layers",
        "**2,730** edges / **45** layers",
        "**2,891** edges / **45** layers",
        "**2,912** edges / **45** layers",
        "**2,977** edges / **45** layers",
        "432 Stable plus 453 Alpha-only rows",
        "432 Stable plus 491 Alpha-only rows",
        "432 Stable plus 533 Alpha-only rows",
        "432 Stable plus 540 Alpha-only rows",
        "432 Stable plus 561 Alpha-only rows",
        "314 `body_checked`",
        "352 `body_checked`",
        "394 `body_checked`",
        "401 `body_checked`",
        "422 `body_checked`",
        "one `pending_layered_closure`",
        'edition("alpha").checked_specs',
        'entry("cell_list_extensional", edition="alpha")',
        'replay("signed_decode_nonnegative_constructor", edition="alpha")',
        "95,253 proof nodes",
        "artifacts/peano-library/alpha/catalog-v1.json",
        "artifacts/peano-library/channels.json",
        "artifacts/peano-library/channels-v3.json",
        "artifacts/peano-library/channels-v4.json",
        "artifacts/peano-library/channels-v5.json",
        "artifacts/peano-library/channels-v6.json",
        "46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473",
        "bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af",
        "94efc0f7022f31677619e842f7d6f1d0d0f8959efc54cd64cf346c3b5e8c4892",
        "dc25a3dc0ab7346f9188eee1262700b40bb09efdacfa849f3a27475ed870b5a7",
        "7e46b80c4799e51da32cedf21a130274200fa14b21e0fec3b42f74d1523ab23b",
        "c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d",
        "Bertrand campaign chapter",
        "direct neighborhood",
    ):
        assert exact in source
    assert "<library-editions>" in index
    assert "241 Stable prerequisites" in normalized_proof_explorer
    assert "316 Alpha-only specifications" in normalized_proof_explorer
    assert "748" in normalized_proof_explorer
    for exact in (
        "## Current Alpha v6 layer",
        "| Alpha v6 specifications | 993 |",
        "| `FactorialVal` rows | 7 |",
        "8 + 5 + 5 + 3",
        "## Alpha v6 threshold, finite-sum, and bridge layer",
        "## Pushed candidates beyond Alpha v6",
        "eight-row threshold tranche",
        "five-row finite Legendre-sum interface",
        "does **not** yet prove",
        "relational-power bridge",
        "`05cb3ff`",
        "`f35b8ed`",
        "`4df44c9`",
        "`85625d6`",
        "`bb24543`",
        "`2f41a97`",
        "`5b9433a`",
        "`b2035ce`",
        "`5b189f0`",
        "81,828 structural nodes",
        "59,836, 59,833, 59,836, and 119,652 nodes",
        "make peano-library-alpha-v6-check",
    ):
        assert exact in bertrand
    for exact in (
        "## Peano Alpha v6 — threshold, finite-sum, and bridge layer",
        "[`peano-library/channels-v6.json`](peano-library/channels-v6.json)",
        "993 theorem specifications, 2,977 declared direct edges",
        "c23b2fc58fabd3803a0ded5f02d4ea348d67a00b25f5b28b35f3d6bcb00ff2f1",
        "five Legendre-successor rows in commit `5b9433a`",
    ):
        assert exact in artifacts
    assert "four capacity-shared `PowTotal` rows in `b2035ce`" in (
        normalized_artifacts
    )


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
    assert len(theorems) == snapshot["theorem_count"] == 432
    assert len(by_name) == 432
    assert sum(len(theorem["dependencies"]) for theorem in theorems) == 1_185

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
    assert "Stable repository theorem; hosted-runtime deployment is a separate channel" in atlas
    assert "# The Stable theorem atlas" in atlas
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
