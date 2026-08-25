"""The selected-theorem Lean frontend is interactive, bounded, and honest."""

from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "book" / "_static" / "lean-selector"
SCRIPT = ASSETS / "lean-selector.js"
STYLESHEET = ASSETS / "lean-selector.css"
HARNESS = Path(__file__).with_name("lean_selector_harness.js")
GUIDE = ROOT / "docs" / "LEAN_SELECTOR_UI.md"


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
    assert "snapshot.lean_verified !== true" in source
    assert "stable_member === true" in source
    assert "credentials = \"same-origin\"" in source
    assert "live.lean-lang.org" in source
    assert "LIVE_MAX_BYTES = 8192" in source
    assert "POLL_MILLISECONDS = 750" in source
    assert "DEFAULT_MAX_NODES = 256" in source
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
    assert "8,192-byte" in guide
    assert "private project" in guide
    assert "lean_verified: true" in guide
    assert "unchanged Peano kernel" in guide
    assert "do not need regeneration" in guide


def test_shared_assets_cover_all_ten_existing_theorem_graph_surfaces() -> None:
    static = ROOT / "book" / "_static"
    primary = (
        static / "pa-proof-explorer" / "graph.html",
        static / "pa-proof-explorer" / "defined" / "graph.html",
        static / "bertrand-proof-explorer" / "graph.html",
        static / "bertrand-proof-explorer" / "defined" / "graph.html",
    )
    frontier = tuple(
        static
        / "constructive-frontier-explorer"
        / family
        / "explorer"
        / "defined"
        / "graph.html"
        for family in (
            "kummer",
            "lucas",
            "two-squares",
            "four-squares",
            "supplementary-laws",
            "pythagorean-fermat-four",
        )
    )

    assert len(primary + frontier) == 10
    for graph in primary + frontier:
        assert graph.is_file(), graph

    source = SCRIPT.read_text(encoding="utf-8")
    assert "global.PA_PROOF_GRAPH" in source
    assert "global.PA_DEFINED_GRAPH" in source
