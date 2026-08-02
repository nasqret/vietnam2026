"""Loopback-server and stale-cache contracts for the training observatory."""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sys
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import serve_wmi_training_dashboard as dashboard_server  # noqa: E402


def _status(step: int = 123) -> dict[str, object]:
    return {
        "schema": "backend-private-schema",
        "v": 1,
        "fetched_at": "2026-08-01T09:00:00Z",
        "connection": {"status": "connected"},
        "job": {"id": "217859", "state": "RUNNING", "node": "g3n1"},
        "progress": {
            "phase": "training",
            "step": step,
            "total_steps": 649,
            "percent": step * 100 / 649,
            "seconds_per_step": 20.0,
            "eta_seconds": (649 - step) * 20,
        },
        "loss": {"status": "buffered", "smoke": {}, "points": []},
        "snapshots": {"planned_steps": [100, 200], "published": []},
        "samples": [],
        "logs": {"stdout": "", "stderr": "123/649"},
    }


def test_snapshot_cache_serializes_projection_and_preserves_success_on_failure() -> None:
    calls: list[tuple[str, str]] = []
    failure = False

    def fetcher(job_id: str, *, ssh_target: str) -> object:
        nonlocal failure
        calls.append((job_id, ssh_target))
        if failure:
            raise OSError("VPN unavailable\nsecond line must be flattened")
        return {"step": 123}

    def builder(raw: object) -> dict[str, object]:
        assert raw == {"step": 123}
        return _status()

    cache = dashboard_server.SnapshotCache(
        "217859", "wmicluster", 5.0, fetcher=fetcher, builder=builder
    )
    cache.collect_once()
    live = cache.snapshot()
    assert live["schema"] == dashboard_server.SCHEMA
    assert live["stale"] is False
    assert live["connection"]["state"] == "live"
    assert live["progress"]["step"] == 123

    failure = True
    cache.collect_once()
    stale = cache.snapshot()
    assert stale["stale"] is True
    assert stale["connection"]["state"] == "stale"
    assert stale["fetched_at"] == live["fetched_at"]
    assert stale["connection"]["last_attempt_at"] > live["fetched_at"]
    assert stale["connection"]["message"] == (
        "VPN unavailable second line must be flattened"
    )
    assert stale["progress"]["step"] == 123
    assert calls == [("217859", "wmicluster"), ("217859", "wmicluster")]


def test_initial_cache_never_invents_training_or_loss() -> None:
    cache = dashboard_server.SnapshotCache(
        "217859",
        "wmicluster",
        5.0,
        fetcher=lambda *_args, **_kwargs: None,
        builder=lambda _raw: _status(),
    )
    initial = cache.snapshot()
    assert initial["stale"] is True
    assert initial["connection"]["state"] == "connecting"
    assert initial["progress"]["step"] == 0
    assert initial["loss"]["points"] == []
    assert initial["snapshots"] == {
        "planned_steps": [],
        "published": [],
        "latest_step": None,
    }
    assert initial["resources"]["status"] == "unavailable"
    assert initial["artifacts"]["final_adapter"] is False


def test_cache_rejects_unreasonable_poll_intervals() -> None:
    for interval in (0.0, 1.99, 60.01, 1_000.0):
        with pytest.raises(ValueError, match="poll interval"):
            dashboard_server.SnapshotCache("217859", "wmicluster", interval)


def test_json_encoder_is_finite_and_bounded() -> None:
    with pytest.raises(ValueError):
        dashboard_server._strict_json_bytes({"value": float("nan")})
    with pytest.raises(ValueError, match="response limit"):
        dashboard_server._strict_json_bytes(
            {"value": "x" * dashboard_server.MAXIMUM_RESPONSE_BYTES}
        )


def test_loopback_http_server_is_get_only_no_store_and_fixed_route() -> None:
    cache = dashboard_server.SnapshotCache(
        "217859",
        "wmicluster",
        5.0,
        fetcher=lambda *_args, **_kwargs: {},
        builder=lambda _raw: _status(),
    )
    cache.collect_once()
    server = dashboard_server.DashboardServer(("127.0.0.1", 0), cache)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with closing(urlopen(base + "/api/status", timeout=3)) as response:
            payload = json.load(response)
            assert payload["schema"] == dashboard_server.SCHEMA
            assert payload["progress"]["step"] == 123
            assert response.headers["Cache-Control"] == "no-store, max-age=0"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert "connect-src 'self'" in response.headers["Content-Security-Policy"]

        with cache._condition:
            cache._refresh_requested = False
        refresh = Request(
            base + "/api/status", headers={"X-Peano-Refresh": "1"}
        )
        with closing(urlopen(refresh, timeout=3)):
            pass
        with cache._condition:
            assert cache._refresh_requested is True

        with closing(urlopen(base + "/", timeout=3)) as response:
            assert b"Training Observatory" in response.read()
            assert response.headers.get_content_type() == "text/html"

        for path, status in (("/api/status?job=2", 400), ("/../secret", 404)):
            with pytest.raises(HTTPError) as rejected:
                urlopen(base + path, timeout=3)
            assert rejected.value.code == status

        request = Request(base + "/api/status", data=b"x", method="POST")
        with pytest.raises(HTTPError) as rejected:
            urlopen(request, timeout=3)
        assert rejected.value.code == 405
        assert rejected.value.headers["Allow"] == "GET, HEAD"

        rebinding = Request(
            base + "/api/status", headers={"Host": "attacker.example"}
        )
        with pytest.raises(HTTPError) as rejected:
            urlopen(rebinding, timeout=3)
        assert rejected.value.code == 421
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_server_has_no_public_bind_or_scheduler_mutation_surface() -> None:
    source = (SCRIPTS / "serve_wmi_training_dashboard.py").read_text(
        encoding="utf-8"
    )
    assert dashboard_server.LOOPBACK_HOST == "127.0.0.1"
    assert "--host" not in source
    assert 'parsed.path == "/api/status"' in source
    assert 'parsed.path == "/healthz"' in source
    assert "do_POST = _method_not_allowed" in source
    assert "do_DELETE = _method_not_allowed" in source
    for command in ("sbatch", "scancel", "scontrol", "srun"):
        assert command not in source
