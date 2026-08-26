"""Contract tests for the generated complete Bertrand proof explorer."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[3]
if str(REPO / "peano-lab" / "py") not in sys.path:
    sys.path.insert(0, str(REPO / "peano-lab" / "py"))

from peano_lab.library import editions_v18 as proof_alpha  # noqa: E402
from peano_lab.library import editions_v24 as current_alpha  # noqa: E402

EXPLORER = REPO / "book" / "_static" / "bertrand-proof-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v12.json"
BUILDER = REPO / "scripts" / "build_bertrand_proof_explorer.py"
BOOK_PAGE = REPO / "book" / "arithmetic-library" / "bertrand-proof-explorer.md"
EXPECTED_AGGREGATE = (
    "427b92390d72df2297a91d042524cb3a8d59d2e88c7f42249d628f3e8c26b70f"
)
EXPECTED_CATALOG_SHA256 = (
    "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_bertrand_proof_explorer_is_byte_current() -> None:
    result = subprocess.run(
        [sys.executable, str(BUILDER), "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verified Bertrand proof explorer" in result.stdout


def test_exact_explorer_preserves_its_independent_defined_edition(
    monkeypatch, tmp_path: Path
) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import build_bertrand_proof_explorer as generator

    output = tmp_path / "explorer"
    defined = output / "defined" / "tag" / "BT0127.html"
    defined.parent.mkdir(parents=True)
    defined.write_text("independent defined edition", encoding="utf-8")
    stale = output / "stale.html"
    stale.write_text("stale exact artifact", encoding="utf-8")
    monkeypatch.setattr(generator, "OUTPUT", output)

    files = {"index.html": b"exact artifact"}
    generator._write(files)

    assert defined.read_text(encoding="utf-8") == "independent defined edition"
    assert not stale.exists()
    assert generator._check(files)

    stale.write_text("unexpected exact artifact", encoding="utf-8")
    assert not generator._check(files)


def test_manifest_freezes_the_complete_strict_closure() -> None:
    manifest = _load(EXPLORER / "manifest.json")
    assert _sha256(CATALOG) == EXPECTED_CATALOG_SHA256
    assert manifest["schema"] == "peano-lab-bertrand-proof-explorer-manifest-v1"
    assert manifest["theorem_count"] == 544
    assert manifest["public_count"] == 202
    assert manifest["candidate_count"] == 342
    assert manifest["alpha_edition_version"] == "v24"
    assert manifest["alpha_edition_identity_sha256"] == (
        current_alpha.ALPHA_V24_IDENTITY_SHA256
    )
    assert manifest["alpha_edition_checked_use_count"] == 2008
    assert manifest["proof_edition_version"] == "v18"
    assert manifest["proof_edition_identity_sha256"] == (
        proof_alpha.ALPHA_V18_IDENTITY_SHA256
    )
    assert manifest["proof_edition_checked_use_count"] == 1589
    assert manifest["graph_checked_use_count"] == 544
    assert manifest["graph_stable_closed_count"] == 202
    assert manifest["graph_alpha_closed_count"] == 342
    assert manifest["graph_newly_promoted_count"] == 330
    assert manifest["source_scope_policy"] == (
        "historical_origin_not_current_release_authority"
    )
    assert manifest["source_edition_version"] == "v12"
    assert manifest["source_checked_use_count"] == 203
    assert manifest["source_body_checked_count"] == 341
    assert manifest["edge_count"] == 1917
    assert manifest["layer_count"] == 45
    assert manifest["formal_line_count"] == 28410
    assert manifest["explicit_dependency_reference_count"] == 8786
    assert manifest["root_name"] == "bertrand_strict"
    assert manifest["root_tag"] == "BT0127"
    assert manifest["canonical_tag_page_count"] == 544
    assert manifest["name_alias_page_count"] == 544
    assert manifest["generated_file_count"] == 1095
    assert manifest["aggregate_sha256"] == EXPECTED_AGGREGATE


def test_graph_is_the_full_dependency_closure() -> None:
    graph = _load(EXPLORER / "api" / "graph.json")
    tags = [node["tag"] for node in graph["nodes"]]
    assert len(tags) == len(set(tags)) == 544
    assert graph["graph_checked_use_count"] == 544
    assert graph["graph_stable_closed_count"] == 202
    assert graph["graph_alpha_closed_count"] == 342
    assert all(node["alpha_checked_use"] is True for node in graph["nodes"])
    assert graph["terminals"] == ["BT0127"]
    assert len(graph["adjacency"]["BT0127"]["ancestors"]) == 543
    assert len(graph["adjacency"]["BT0127"]["critical_root_path"]) == 45
    assert graph["adjacency"]["BT0127"]["root_path_count"] == 441608
    assert [layer["index"] for layer in graph["layers"]] == list(range(45))
    edge_pairs = {
        (edge["dependency"], edge["dependent"])
        for edge in graph["edges"]
    }
    assert len(edge_pairs) == 1917
    adjacency_pairs = {
        (dependency, tag)
        for tag, row in graph["adjacency"].items()
        for dependency in row["dependencies"]
    }
    assert edge_pairs == adjacency_pairs


def test_corpus_preserves_v12_sources_and_overlays_actual_v24_evidence() -> None:
    catalog = _load(CATALOG)
    corpus = _load(EXPLORER / "api" / "corpus.json")
    catalog_by_name = {row["name"]: row for row in catalog["theorems"]}
    for row in corpus["theorems"]:
        source = catalog_by_name[row["name"]]
        assert row["statement"] == source["statement"]
        assert [line["text"] for line in row["lines"]] == source["script"]
        assert row["enrollment_index"] == source["enrollment_index"]
        assert row["tag"].startswith("BT")
        current = current_alpha.ALPHA_EDITION.by_name[row["name"]]
        assert row["checked_use"] is True
        assert row["alpha_checked_use"] is True
        assert row["proof_edition_version"] == "v18"
        assert row["alpha_evidence"] == current.evidence.value
        assert row["evidence_status"] == current.evidence.value
        assert row["stable_member"] is (
            current.membership is current_alpha.Membership.STABLE
        )
        assert row["scope"] == ("public" if row["stable_member"] else "candidate")
        assert row["source_edition_version"] == "v12"
        assert row["source_checked_use"] == source["checked_use"]
        assert row["source_evidence_status"] == source["evidence_status"]
    root = next(row for row in corpus["theorems"] if row["name"] == "bertrand_strict")
    assert root["tag"] == "BT0127"
    assert root["enrollment_index"] == 1302
    assert root["scope"] == "candidate"
    assert root["alpha_evidence"] == "alpha_closed"
    assert root["alpha_checked_use"] is True
    assert root["stable_member"] is False
    assert root["source_evidence_status"] == "body_checked"
    assert root["source_checked_use"] is False


def test_every_explorer_page_and_alias_exists() -> None:
    corpus = _load(EXPLORER / "api" / "corpus.json")
    for row in corpus["theorems"]:
        tag_page = EXPLORER / "tag" / f'{row["tag"]}.html'
        alias = EXPLORER / "name" / f'{row["name"]}.html'
        assert tag_page.is_file()
        assert alias.is_file()
        assert row["statement_sha256"] in tag_page.read_text(encoding="utf-8")


def test_interactive_surface_defaults_to_the_complete_map() -> None:
    graph_html = (EXPLORER / "graph.html").read_text(encoding="utf-8")
    index_html = (EXPLORER / "index.html").read_text(encoding="utf-8")
    book_page = BOOK_PAGE.read_text(encoding="utf-8")
    assert 'value="BT0127"' in graph_html
    assert '<option value="prerequisites" selected>' in graph_html
    assert "all 544 theorem" in graph_html
    assert "literal 1,917-edge graph" in graph_html
    assert "pa-bertrand-release-evidence" in graph_html
    assert "Alpha v24 checked-use theorem; independently kernel and Lean verified; not Stable" in graph_html
    assert "body-checked</span>" not in graph_html
    assert "Open the complete interactive proof map" in index_html
    assert "Stable checked-use (202)" in index_html
    assert "Alpha-only checked-use (342)" in index_html
    assert "Body-checked (341)" not in index_html
    assert "bertrand_strict" in index_html
    assert "BT0127" in index_html
    assert book_page.count("graph.html?view=prerequisites") == 3


def test_root_page_exposes_exact_endpoint_and_provenance() -> None:
    source = (EXPLORER / "tag" / "BT0127.html").read_text(encoding="utf-8")
    assert "bertrand_strict" in source
    assert "Every n greater than one has a prime strictly below n+n." in source
    assert "bertrand_bp02_candidate.py" in source
    assert "1bb7045f9b033e6e6167b329525d4833f66baab67bb5e846c3f572adbbb7ec0c" in source
    assert "proof-line-0039" in source
    assert "bertrand_closed_upper" in source
    assert "Alpha v24 checked-use theorem" in source
    assert "<dt>Current Alpha edition</dt><dd>v24</dd>" in source
    assert "<dt>Proof-bearing Alpha edition</dt><dd>v18</dd>" in source
    assert "historical Alpha-v18 proof bundle independently checks" in source
    assert "<dt>Current release evidence</dt><dd>alpha_closed</dd>" in source
    assert "<dt>Checked theorem use</dt><dd>yes</dd>" in source
    assert "<dt>Stable membership</dt><dd>no</dd>" in source
    assert "<dt>Historical Alpha-v12 evidence</dt><dd>body_checked</dd>" in source


def test_explorer_contains_no_classical_tactic() -> None:
    corpus = _load(EXPLORER / "api" / "corpus.json")
    commands = [
        line["text"]
        for row in corpus["theorems"]
        for line in row["lines"]
    ]
    assert not any(
        command == "dne" or command.startswith("dne ")
        for command in commands
    )


def test_every_bertrand_proof_page_links_its_definition_dag_and_research_atlas() -> None:
    current_catalog = (
        REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
    )
    revision = _sha256(current_catalog)[:12]
    assert revision == "94ac4d193cbf"
    for relative in ("index.html", "graph.html"):
        page = (EXPLORER / relative).read_text(encoding="utf-8")
        assert f'href="../../grand-campaign/?v={revision}"' in page
        assert f'view=domain&amp;focus=D02&amp;v={revision}' in page
        assert f'view=family&amp;focus=F03&amp;v={revision}' in page
        assert f'view=goal&amp;focus=A02&amp;v={revision}' in page

    corpus = _load(EXPLORER / "api" / "corpus.json")
    for theorem in corpus["theorems"]:
        tag = theorem["tag"]
        page = (EXPLORER / "tag" / f"{tag}.html").read_text(encoding="utf-8")
        assert f'href="../../../grand-campaign/?v={revision}"' in page
        assert f'view=family&amp;focus=F03&amp;v={revision}' in page
        assert f'view=goal&amp;focus=A02&amp;v={revision}' in page
        assert f'href="../defined/tag/{tag}.html"' in page
        assert f'href="../defined/graph.html?target={tag}&amp;view=neighborhood' in page
