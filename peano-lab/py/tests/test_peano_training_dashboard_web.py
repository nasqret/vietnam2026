"""Static safety and accessibility contracts for the training observatory."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[3]
STATIC = ROOT / "training" / "peano_policy" / "dashboard_static"
INDEX = (STATIC / "index.html").read_text(encoding="utf-8")
CSS = (STATIC / "dashboard.css").read_text(encoding="utf-8")
JAVASCRIPT = (STATIC / "dashboard.js").read_text(encoding="utf-8")


def test_dashboard_is_self_contained_and_javascript_is_valid() -> None:
    asset_urls = re.findall(
        r'<(?:script|link)\b[^>]+(?:src|href)="([^"]+)"', INDEX
    )
    assert asset_urls == ["/dashboard.css", "/dashboard.js"]
    assert "https://" not in INDEX + CSS + JAVASCRIPT
    assert JAVASCRIPT.count("http://") == 1
    assert '"http://www.w3.org/2000/svg"' in JAVASCRIPT
    assert ".innerHTML" not in JAVASCRIPT
    assert ".textContent" in JAVASCRIPT

    checked = subprocess.run(
        ["node", "--check", "-"],
        input=JAVASCRIPT,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr


def test_dashboard_polls_one_read_only_status_endpoint_without_overlap() -> None:
    assert 'fetch("/api/status"' in JAVASCRIPT
    assert JAVASCRIPT.count("fetch(") == 1
    assert "if (state.fetching) {" in JAVASCRIPT
    assert "state.fetching = true" in JAVASCRIPT
    assert "state.fetching = false" in JAVASCRIPT
    assert "AbortController" in JAVASCRIPT
    assert 'cache: "no-store"' in JAVASCRIPT
    assert "POLL_VISIBLE_MS = 5000" in JAVASCRIPT
    assert "POLL_HIDDEN_MS = 30000" in JAVASCRIPT
    assert 'document.addEventListener("visibilitychange", schedulePoll)' in JAVASCRIPT
    assert not re.search(r"/(?:submit|cancel|delete|write|control)\b", JAVASCRIPT)


def test_dashboard_never_invents_current_loss_or_current_microbatch() -> None:
    assert "No exact production-loss records are available yet" in INDEX
    assert "No value is inferred from progress" in INDEX
    assert "Representative reported examples—not the exact shuffled microbatch" in INDEX
    assert "admission smoke only:" in JAVASCRIPT
    assert 'setText("metric-loss", "awaiting")' in JAVASCRIPT
    assert "smoke_loss" in JAVASCRIPT
    assert "loss.status" in JAVASCRIPT
    assert 'buffered: "Production loss is buffered' in JAVASCRIPT


def test_dashboard_exposes_accessible_status_chart_and_controls() -> None:
    assert 'role="status" aria-live="polite"' in INDEX
    assert '<progress id="optimizer-progress"' in INDEX
    assert 'aria-label="Optimizer progress"' in INDEX
    assert 'role="img" aria-labelledby="loss-chart-title loss-chart-description"' in INDEX
    assert '<table>' in INDEX
    assert '<th scope="col">Step</th>' in INDEX
    assert 'aria-label="Recent WMI training log lines"' in INDEX
    assert 'aria-expanded="false"' in INDEX
    assert 'aria-controls="target-answer" disabled' in INDEX
    assert 'id="sample-previous" class="small-button" type="button" aria-label="Previous corpus example" disabled' in INDEX
    assert 'id="sample-next" class="small-button" type="button" aria-label="Next corpus example" disabled' in INDEX
    assert 'aria-pressed="false"' in INDEX
    assert 'data-log-stream="combined" aria-pressed="true"' in INDEX
    assert 'class="skip-link"' in INDEX
    assert "prefers-reduced-motion" in CSS
    assert "prefers-contrast" in CSS
    assert ":focus-visible" in CSS
    assert "button:disabled" in CSS
    assert "min-width: 700px" in CSS
    assert "overflow-x: auto" in CSS


def test_dashboard_has_live_recovery_provenance_and_log_surfaces() -> None:
    assert 'data-step="100"' not in INDEX
    assert "snapshotRecord.planned_steps" in JAVASCRIPT
    assert "missingSteps.length" in JAVASCRIPT
    assert 'id="fact-source"' in INDEX
    assert 'id="fact-preparation"' in INDEX
    assert 'id="fact-gpu-load"' in INDEX
    assert 'id="fact-runtime"' in INDEX
    assert 'id="identity-eyebrow"' in INDEX
    assert 'id="seal-mark"' in INDEX
    assert 'id="snapshot-list"' in INDEX
    assert 'id="live-log"' in INDEX
    assert 'data-log-stream="stderr"' in INDEX
    assert "Adapter-only, intentionally non-resumable" in INDEX
    assert "Only independently kernel-checked proofs count as solved" in INDEX
    assert 'isOptimizerPhase(phase)' in JAVASCRIPT
    assert 'job.node_or_reason' in JAVASCRIPT
    assert 'resources.gpu_utilization_percent' in JAVASCRIPT
    assert "artifacts.run_identity === true" in JAVASCRIPT
    assert 'identityPresent ? "identity present"' in JAVASCRIPT
    assert 'node.setAttribute("aria-pressed"' in JAVASCRIPT
    assert "hasCachedSnapshot" in JAVASCRIPT
    assert "finalWindow" in JAVASCRIPT
    assert 'data.v !== 1' in JAVASCRIPT
    assert "Fresh WMI read requested" in JAVASCRIPT
    assert "MANUAL_REFRESH_WAIT_MS = 60000" in JAVASCRIPT
    assert "state.queuedManualRefresh = true" in JAVASCRIPT
    assert "hasSuccessfulSnapshot(state.lastData)" in JAVASCRIPT
    assert 'else lines = []' in JAVASCRIPT
    assert '"Current phase: "' in JAVASCRIPT
