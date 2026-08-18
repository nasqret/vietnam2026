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
        "**1,017** theorems",
        "**1,055** theorems",
        "**1,076** theorems",
        "**1,085** theorems",
        "**1,123** theorems",
        "**1,303** theorems",
        "**570** theorems",
        "**2,641** edges / **45** layers",
        "**2,730** edges / **45** layers",
        "**2,891** edges / **45** layers",
        "**2,912** edges / **45** layers",
        "**3,072** edges / **45** layers",
        "**3,224** edges / **45** layers",
        "**3,276** edges / **45** layers",
        "**3,306** edges / **45** layers",
        "**3,482** edges / **45** layers",
        "**4,302** edges / **45** layers",
        "432 Stable plus 453 Alpha-only rows",
        "432 Stable plus 491 Alpha-only rows",
        "432 Stable plus 533 Alpha-only rows",
        "432 Stable plus 540 Alpha-only rows",
        "432 Stable plus 561 Alpha-only rows",
        "432 Stable plus 585 Alpha-only rows",
        "432 Stable plus 623 Alpha-only rows",
        "432 Stable plus 644 Alpha-only rows",
        "432 Stable plus 653 Alpha-only rows",
        "432 Stable plus 691 Alpha-only rows",
        "432 Stable plus 871 Alpha-only rows",
        "314 `body_checked`",
        "352 `body_checked`",
        "394 `body_checked`",
        "401 `body_checked`",
        "446 `body_checked`",
        "484 `body_checked`",
        "505 `body_checked`",
        "514 `body_checked`",
        "552 `body_checked`",
        "732 `body_checked`",
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
        "artifacts/peano-library/channels-v7.json",
        "artifacts/peano-library/alpha/catalog-v8.json",
        "artifacts/peano-library/alpha/metrics-v8.json",
        "artifacts/peano-library/alpha/dependency-graph-v8.mmd",
        "artifacts/peano-library/channels-v8.json",
        "artifacts/peano-library/alpha/catalog-v9.json",
        "artifacts/peano-library/alpha/metrics-v9.json",
        "artifacts/peano-library/alpha/dependency-graph-v9.mmd",
        "artifacts/peano-library/channels-v9.json",
        "artifacts/peano-library/alpha/catalog-v10.json",
        "artifacts/peano-library/alpha/metrics-v10.json",
        "artifacts/peano-library/alpha/dependency-graph-v10.mmd",
        "artifacts/peano-library/channels-v10.json",
        "artifacts/peano-library/alpha/catalog-v11.json",
        "artifacts/peano-library/alpha/metrics-v11.json",
        "artifacts/peano-library/alpha/dependency-graph-v11.mmd",
        "artifacts/peano-library/channels-v11.json",
        "artifacts/peano-library/alpha/catalog-v12.json",
        "artifacts/peano-library/alpha/metrics-v12.json",
        "artifacts/peano-library/alpha/dependency-graph-v12.mmd",
        "artifacts/peano-library/channels-v12.json",
        "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c",
        "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff",
        "a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2",
        "2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123",
        "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f",
        "b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80",
        "762d1310c41ed92da066701cf7529551324b09f7b501c5a29c530f443afeb998",
        "4c87c40b5a260d67b5582447cfabb7e3ce62e80303aa4f4d33b1b952995ec356",
        "108593843459a69d81c333305a50b5368294c3c722437f425b92c942391fe9be",
        "edfb0eacecbd9419b1b303098915e28e45643379b65ab7d807ffcd4d7bd4b3e7",
        "61f33ba9e49219ff4a199d082722d9582ac6d87f825851173ac7fdb6931bb52d",
        "1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab",
        "c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f",
        "1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d",
        "6ab70321b61bea288df325ffa433c992d0559e9546324583066b4f767249df46",
        "01ec76832d511806302056f2f823b2d8c45c477cf92d826bfae28197f1656013",
        "a00e426172d93e9c9254d97ec2295031873dd02fc97a003eb4824cc22b64e81a",
        "f2c2760dd275b94572e0ab5a5cc4837fc1e884ea26ea00a55074caa84a4d8f6e",
        "446f6c9d07c3f9e22fa0fbb41a46c95d27804a088d708b13aea0ddd7159c45dd",
        "fdac645cbc070b5a1cdfe71b19e98afe095a183d4cfa0ad4256fa42857ca736c",
        "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36",
        "46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3",
        "4a1f4302b0a4ede3bf5123ec021b4f2f5f98c2a7e22eadc6f13a446422ad9450",
        "2f0be30e7de93bcf89235700c419f46656cb638be85ca153154684845e8dabdb",
        "b82b567e59cabeda6f90fdfedaceb628ca2e7c4b7423be643b8f22865e7599bd",
        "ecce457947650ae7ddf2a638d8b1f2c8757daea6a95ea9c927ebaef3995d4ccd",
        "cf5d550d5a3aa4af1debf9268eca578c30ca408058dcdeb35892bc705287214e",
        "6c314d36cd7bb1e6cb5b213fec9bf9e04ab118e84121830b00c885ede2abac2a",
        "c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d",
        "7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4",
        "c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370",
        "90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813",
        "ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008",
        "dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d",
        "74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda",
        "7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65",
        "03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9",
        "77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34",
        "46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3",
        "63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de",
        "fdee73e6ea045c90afb7c024e8a209fbea8b03189538611c93678e4fa923aa76",
        "644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2",
        "d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c",
        "92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300",
        "c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1",
        "039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f",
        "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b",
        "bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061",
        "362da94c3c5e788f296f315b86b5d63534c1567ce00911dbb27227a66ab50e28",
        "726c6134461dace943f909a0073ca0a6cae95a54ff306f8aeefeb3d9a5151926",
        "de8a6a57b828c2b3893c6fb31f2611d5180f8de4d1002a21a681739616b761b5",
        "7ad0c942a2239532696f5d99ee1dc985e13302cf73b4637497b879871d05752c",
        "ee9494f8dfb9e4070a2ce3d2d740b312d147948dcd296ac0da7ed059c9944e50",
        "df0e5cb8402483360f8381c76c7ce6ed6c70245df45556107c40652d00beb0da",
        "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109",
        "64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4",
        "583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8",
        "0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982",
        "RFC HA-R6-BERTRAND-CB-1",
        "Primorial foundation RFC",
        "Primorial membership RFC",
        "Primorial interval-split RFC",
        "Bertrand campaign chapter",
        "direct neighborhood",
    ):
        assert exact in source
    for exact in (
        "<library-editions>",
        "<strong>1,303</strong><span>Alpha v12 theorems</span>",
        "1,303 theorems, 4,302 direct edges",
        "732 `body_checked`",
        "dependency-closed B6 support and B5--BP02 completion chain",
    ):
        assert exact in index
    assert "241 Stable prerequisites" in normalized_proof_explorer
    assert "316 Alpha-only specifications" in normalized_proof_explorer
    assert "748" in normalized_proof_explorer
    for exact in (
        "## Current Alpha v12 layer",
        "| Alpha v12 specifications | 1,303 |",
        "| `FactorialVal` rows | 7 |",
        "8 + 5 + 5 + 3",
        "3 + 5 + 4 + 2 + 5 + 3 + 2",
        "24 + 14",
        "10 + 11",
        "## Alpha v6 threshold, finite-sum, and bridge layer",
        "## Alpha v7 recurrence, equality, and $H/J$ layer",
        "## Alpha v8 recurrence-defined Choose and central lower bound",
        "## Alpha v9 Primorial foundation and membership",
        "## Alpha v10 Primorial interval splitting",
        "## Alpha v11 B4 capstone and B5 prime support",
        "## Alpha v12 complete Bertrand proof",
        "B3 Choose/CentralBinom [Alpha v8 body evidence]",
        (
            "B4 Primorial [Alpha v11 body evidence; bound closed; "
            "depends on B3]"
        ),
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
        "`70c5b16`",
        "`de58034`",
        "`985a773`",
        "`158d87c`",
        "`00e8361`",
        "`874e81e`",
        "`d1cbe16`",
        "`8ea03f2`",
        "`d1ad971`",
        "`d46e513`--`74dc219`",
        "prime_factorial_valuation_eq_legendre_sum",
        "four_pow_lt_mul_central_binom",
        "RFC HA-R6-BERTRAND-CB-1",
        "c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89",
        "4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5",
        "1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab",
        "`dfb2673`",
        "`b0bc5de`",
        "`c45d68a`",
        "`5eef9a5`--`7539b44`",
        "`56ecb02`",
        "make peano-library-alpha-v12-check",
        "complete Bertrand proof explorer",
        "BT0127",
    ):
        assert exact in bertrand
    for exact in (
        "## Peano Alpha v7 — Bertrand recurrence, equality, and transport",
        "[`peano-library/channels-v7.json`](peano-library/channels-v7.json)",
        "1,017 theorem specifications, 3,072 declared direct edges",
        "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c",
        "prime_factorial_valuation_eq_legendre_sum",
        "make peano-library-alpha-v7-check",
    ):
        assert exact in artifacts
    assert "all twenty-four additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v8 — Choose and central-binomial lower bound",
        "[`peano-library/channels-v8.json`](peano-library/channels-v8.json)",
        "1,055 theorem specifications, 3,224 declared direct edges",
        "a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2",
        "four_pow_lt_mul_central_binom",
        "RFC HA-R6-BERTRAND-CB-1",
        "make peano-library-alpha-v8-check",
    ):
        assert exact in artifacts
    assert "all thirty-eight additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v12 — complete Bertrand proof",
        "[`peano-library/channels-v12.json`](peano-library/channels-v12.json)",
        "1,303 theorem specifications, 4,302 declared direct edges",
        "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b",
        "bertrand_closed_upper",
        "bertrand_strict",
        "make peano-library-alpha-v12-check",
    ):
        assert exact in artifacts
    assert "all 180 additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v9 — Primorial foundation and membership",
        "[`peano-library/channels-v9.json`](peano-library/channels-v9.json)",
        "1,076 theorem specifications, 3,276 declared direct edges",
        "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f",
        "primorial_le_four_pow",
        "Primorial foundation RFC",
        "Primorial membership RFC",
        "make peano-library-alpha-v9-check",
    ):
        assert exact in artifacts
    assert "all twenty-one additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v10 — Primorial interval splitting",
        "[`peano-library/channels-v10.json`](peano-library/channels-v10.json)",
        "1,085 theorem specifications, 3,306 declared direct edges",
        "c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f",
        "Primorial interval-split RFC",
        "make peano-library-alpha-v10-check",
    ):
        assert exact in artifacts
    assert "all nine additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v11 — Primorial capstone and B5 support",
        "[`peano-library/channels-v11.json`](peano-library/channels-v11.json)",
        "1,123 theorem specifications, 3,482 declared direct edges",
        "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36",
        "primorial_le_four_pow",
        "make peano-library-alpha-v11-check",
    ):
        assert exact in artifacts
    assert "all thirty-eight additions fail closed" in normalized_artifacts


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
