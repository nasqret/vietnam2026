"""The selected-theorem Lean frontend is interactive, bounded, and honest."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "book" / "_static" / "lean-selector"
SCRIPT = ASSETS / "lean-selector.js"
STYLESHEET = ASSETS / "lean-selector.css"
HARNESS = Path(__file__).with_name("lean_selector_harness.js")
GUIDE = ROOT / "docs" / "LEAN_SELECTOR_UI.md"


def _campaign_manifests():
    for path in sorted((ROOT / "book/_static").glob("constructive-*-explorer/manifest.json")):
        manifest = json.loads(path.read_bytes())
        if manifest.get("publication_scope") == "local-only-checkpoint":
            # Checkpoint file inventories are deliberately non-admitting and
            # must not be mistaken for Alpha live-selector family manifests.
            assert manifest["schema"].startswith("peano-lab-local-")
            assert isinstance(manifest["files"], dict)
            assert "families" not in manifest
            continue
        assert isinstance(manifest["families"], list) and manifest["families"], path
        yield path, manifest


def test_selected_theorem_controls_execute_real_browser_interactions() -> None:
    result = subprocess.run(
        ["node", str(HARNESS), str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "browser interactions passed" in result.stdout


def test_shared_selector_only_uses_explicit_checked_same_origin_jobs() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "alpha_checked_use" in source
    assert "node.kind === \"definition\"" in source
    assert "node.alpha_checked_use === true" in source
    assert "/^Alpha v[0-9]+ checked use$/" in source
    assert "/^Alpha v[0-9]+; independently verified$/" in source
    assert 'metadata["Alpha evidence"] === "alpha_closed"' in source
    assert "snapshot.lean_verified !== true" in source
    assert "stable_member === true" in source
    assert "credentials = \"same-origin\"" in source
    assert "live.lean-lang.org" in source
    assert "LIVE_MAX_BYTES = 1048576" in source
    assert "POLL_MILLISECONDS = 750" in source
    assert "DEFAULT_MAX_NODES = 1024" in source
    assert "MutationObserver" in source
    assert "data-graph-title" in source
    assert "method: \"POST\"" in source
    assert "method: \"DELETE\"" in source
    assert "observer.observe(selectionTitle" in source
    assert "observer.observe(document.body" not in source
    assert "innerHTML" not in source


def test_selector_styles_are_component_scoped_and_accessible() -> None:
    styles = STYLESHEET.read_text(encoding="utf-8")
    source = SCRIPT.read_text(encoding="utf-8")

    assert ".peano-lean-selector" in styles
    assert "prefers-reduced-motion" in styles
    assert '"aria-live", "polite"' in source
    assert '"role", "status"' in source
    assert '"noopener noreferrer"' in source


def test_operator_guide_describes_exact_job_protocol_and_trust_boundary() -> None:
    guide = GUIDE.read_text(encoding="utf-8")

    assert "/api/lean-strands/jobs" in guide
    assert "format=lean" in guide
    assert "format=zip" in guide
    assert "Lean Live" in guide
    assert "524,288-byte" in guide
    assert "private project" in guide
    assert "lean_verified: true" in guide
    assert "unchanged Peano kernel" in guide
    assert "do not need regeneration" in guide


def test_shared_selector_covers_every_current_and_future_campaign_graph_surface() -> None:
    static = ROOT / "book" / "_static"
    primary = (
        static / "pa-proof-explorer" / "graph.html",
        static / "pa-proof-explorer" / "defined" / "graph.html",
        static / "bertrand-proof-explorer" / "graph.html",
        static / "bertrand-proof-explorer" / "defined" / "graph.html",
    )
    manifests = tuple(_campaign_manifests())
    assert len(manifests) >= 6
    campaign_graphs: list[Path] = []
    slugs: set[str] = set()
    for manifest_path, manifest in manifests:
        for family in manifest["families"]:
            slug = family["slug"]
            assert slug not in slugs, f"duplicate canonical campaign route: {slug}"
            slugs.add(slug)
            branch = manifest_path.parent / slug
            graph = branch / "explorer" / "defined" / "graph.html"
            campaign_graphs.append(graph)
            for path in (
                branch / "index.html",
                branch / "api" / "corpus.json",
                branch / "explorer" / "index.html",
                branch / "explorer" / "defined" / "index.html",
                graph,
                branch / "explorer" / "defined" / "api" / "graph.json",
            ):
                assert path.is_file(), f"incomplete canonical campaign browser surface: {path}"

    # Two original flagships each have exact + defined graphs.  Every remaining
    # family has the shared mixed theorem/definition graph plus both editions.
    assert len(slugs) >= 22
    assert len(primary + tuple(campaign_graphs)) >= 26
    for graph in primary + tuple(campaign_graphs):
        assert graph.is_file(), graph

    source = SCRIPT.read_text(encoding="utf-8")
    assert "global.PA_PROOF_GRAPH" in source
    assert "global.PA_DEFINED_GRAPH" in source


def test_every_campaign_mixed_graph_keeps_proof_and_definition_edges_separate() -> None:
    static = ROOT / "book" / "_static"
    for manifest_path, manifest in _campaign_manifests():
        for family in manifest["families"]:
            path = (
                manifest_path.parent
                / family["slug"]
                / "explorer"
                / "defined"
                / "api"
                / "graph.json"
            )
            graph = json.loads(path.read_bytes())
            assert graph["path_policy"] == "proof_dependency_edges_only", path
            theorem_ids = {row["id"] for row in graph["nodes"] if row["kind"] == "theorem"}
            definition_ids = {
                row["id"] for row in graph["nodes"] if row["kind"] == "definition"
            }
            assert theorem_ids.isdisjoint(definition_ids), path
            for edge in graph["edges"]:
                kind = edge["kind"]
                assert kind in {
                    "proof_dependency", "uses_definition", "definition_uses_definition"
                }, path
                if kind == "proof_dependency":
                    assert edge["source"] in theorem_ids and edge["target"] in theorem_ids, path
                elif kind == "uses_definition":
                    assert edge["source"] in theorem_ids and edge["target"] in definition_ids, path
                else:
                    assert edge["source"] in definition_ids and edge["target"] in definition_ids, path
            for identifier, adjacency in graph.get("proof_adjacency", {}).items():
                assert identifier in theorem_ids, path
                assert set(adjacency.get("dependencies", ())) <= theorem_ids, path
                assert set(adjacency.get("dependents", ())) <= theorem_ids, path
                assert set(adjacency.get("critical_root_path", ())) <= theorem_ids, path


def test_every_checked_campaign_has_matching_exact_and_defined_lean_theorem_pages() -> None:
    static = ROOT / "book" / "_static"
    audited_families = 0
    for manifest_path, manifest in _campaign_manifests():
        for family in manifest["families"]:
            branch = manifest_path.parent / family["slug"]
            graph = json.loads(
                (branch / "explorer" / "defined" / "api" / "graph.json").read_bytes()
            )
            checked = [
                row
                for row in graph["nodes"]
                if row["kind"] == "theorem" and row.get("alpha_checked_use") is True
            ]
            assert checked, f"campaign has no real checked theorem: {family['slug']}"
            # Pick the smallest authenticated theorem page to keep this complete
            # cross-family smoke test bounded even for enormous expanded proofs.
            selected = min(
                checked,
                key=lambda row: (
                    branch / "explorer" / "tag" / f"{row['id']}.html"
                ).stat().st_size,
            )
            tag = selected["id"]
            exact = branch / "explorer" / "tag" / f"{tag}.html"
            defined = branch / "explorer" / "defined" / "tag" / f"{tag}.html"
            assert exact.is_file(), exact
            assert defined.is_file(), defined
            source = exact.read_text(encoding="utf-8")
            assert 'class="pa-proof-sidebar' in source, exact
            assert "<dt>Alpha evidence</dt><dd>alpha_closed</dd>" in source, exact
            version = graph["alpha_edition_version"]
            assert (
                f"<dt>Checked-use authority</dt><dd>Alpha {version}; independently verified</dd>"
            ) in source, exact
            assert "grand-campaign/" in source, exact
            audited_families += 1

    assert audited_families >= 22
