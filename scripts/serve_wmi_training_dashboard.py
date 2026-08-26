#!/usr/bin/env python3
"""Serve a read-only localhost observatory for one WMI Peano training job.

The browser never receives SSH authority.  One background collector executes
the fixed, bounded reader from :mod:`training.peano_policy.dashboard`, caches
its sanitized JSON projection, and serves it from ``/api/status``.  There are
no scheduler mutation, arbitrary path, command, upload, or write endpoints.

Usage::

    python3 scripts/serve_wmi_training_dashboard.py --job-id 217859
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
from typing import Callable, Mapping
from urllib.parse import urlsplit
import webbrowser


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.dashboard import (  # noqa: E402
    build_dashboard_status,
    fetch_remote_snapshot,
    validate_job_id,
    validate_ssh_target,
)


STATIC_ROOT = (
    REPOSITORY_ROOT / "training" / "peano_policy" / "dashboard_static"
)
LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_POLL_SECONDS = 5.0
MINIMUM_POLL_SECONDS = 2.0
MAXIMUM_POLL_SECONDS = 60.0
MAXIMUM_RESPONSE_BYTES = 2 * 1024 * 1024
SCHEMA = "peano-training-dashboard-v1"
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _strict_json_bytes(value: Mapping[str, object]) -> bytes:
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    if len(payload) > MAXIMUM_RESPONSE_BYTES:
        raise ValueError("dashboard status exceeds the local response limit")
    return payload


def _initial_status(job_id: str) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "v": 1,
        "fetched_at": _utc_now(),
        "stale": True,
        "connection": {
            "state": "connecting",
            "stale": True,
            "message": "waiting for the first WMI snapshot",
        },
        "job": {"id": job_id, "state": "UNKNOWN", "node": None},
        "progress": {
            "phase": "initializing",
            "step": 0,
            "total_steps": None,
            "percent": 0.0,
            "seconds_per_step": None,
            "eta_seconds": None,
        },
        "loss": {"status": "unavailable", "smoke": None, "points": []},
        "schedule": {},
        "model": {},
        "source": {},
        "snapshots": {"planned_steps": [], "published": [], "latest_step": None},
        "samples": [],
        "logs": {"stdout": "", "stderr": ""},
        "resources": {"status": "unavailable"},
        "artifacts": {
            "run_identity": False,
            "training_manifest": False,
            "final_adapter": False,
        },
    }


class SnapshotCache:
    """Serialize SSH collection and preserve the last successful projection."""

    def __init__(
        self,
        job_id: str,
        ssh_target: str,
        poll_seconds: float,
        *,
        fetcher: Callable[..., object] = fetch_remote_snapshot,
        builder: Callable[[object], dict[str, object]] = build_dashboard_status,
    ) -> None:
        self.job_id = validate_job_id(job_id)
        self.ssh_target = validate_ssh_target(ssh_target)
        if not MINIMUM_POLL_SECONDS <= poll_seconds <= MAXIMUM_POLL_SECONDS:
            raise ValueError(
                f"poll interval must lie between {MINIMUM_POLL_SECONDS:g} and "
                f"{MAXIMUM_POLL_SECONDS:g} seconds"
            )
        self.poll_seconds = poll_seconds
        self._fetcher = fetcher
        self._builder = builder
        self._condition = threading.Condition()
        self._status = _initial_status(self.job_id)
        self._last_success_monotonic: float | None = None
        self._stop = False
        self._refresh_requested = True
        self._thread = threading.Thread(
            target=self._run,
            name=f"peano-dashboard-{self.job_id}",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        with self._condition:
            self._stop = True
            self._condition.notify_all()
        self._thread.join(timeout=2.0)

    def request_refresh(self) -> None:
        with self._condition:
            self._refresh_requested = True
            self._condition.notify_all()

    def snapshot(self) -> dict[str, object]:
        with self._condition:
            value = copy.deepcopy(self._status)
            last_success = self._last_success_monotonic
        connection = value.get("connection")
        if type(connection) is not dict:
            connection = {}
            value["connection"] = connection
        connection["age_seconds"] = (
            None
            if last_success is None
            else round(max(0.0, time.monotonic() - last_success), 3)
        )
        return value

    def _publish_success(self, status: dict[str, object]) -> None:
        value = copy.deepcopy(status)
        value["schema"] = SCHEMA
        value["v"] = 1
        value.setdefault("fetched_at", _utc_now())
        value["stale"] = False
        connection = value.get("connection")
        if type(connection) is not dict:
            connection = {}
            value["connection"] = connection
        connection.update({"state": "live", "stale": False, "message": "live WMI snapshot"})
        _strict_json_bytes(value)
        with self._condition:
            self._status = value
            self._last_success_monotonic = time.monotonic()

    def _publish_failure(self, exc: Exception) -> None:
        message = str(exc).replace("\r", " ").replace("\n", " ")[:240]
        attempted_at = _utc_now()
        with self._condition:
            value = copy.deepcopy(self._status)
            had_success = self._last_success_monotonic is not None
            value["stale"] = True
            connection = value.get("connection")
            if type(connection) is not dict:
                connection = {}
                value["connection"] = connection
            connection.update(
                {
                    "state": "stale" if had_success else "error",
                    "stale": True,
                    "message": message or "WMI snapshot failed",
                    "last_attempt_at": attempted_at,
                }
            )
            self._status = value

    def collect_once(self) -> None:
        try:
            raw = self._fetcher(self.job_id, ssh_target=self.ssh_target)
            status = self._builder(raw)
            if type(status) is not dict:
                raise TypeError("dashboard builder did not return one JSON object")
            self._publish_success(status)
        except Exception as exc:  # collector must retain its last safe snapshot
            self._publish_failure(exc)

    def _run(self) -> None:
        while True:
            with self._condition:
                if self._stop:
                    return
                self._refresh_requested = False
            self.collect_once()
            deadline = time.monotonic() + self.poll_seconds
            with self._condition:
                while not self._stop and not self._refresh_requested:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    self._condition.wait(timeout=remaining)
                if self._stop:
                    return


class DashboardHandler(BaseHTTPRequestHandler):
    """GET-only handler for fixed dashboard assets and the cached status."""

    server_version = "PeanoTrainingDashboard/1"
    sys_version = ""

    @property
    def cache(self) -> SnapshotCache:
        value = getattr(self.server, "snapshot_cache", None)
        if not isinstance(value, SnapshotCache):
            raise RuntimeError("dashboard server has no snapshot cache")
        return value

    def _security_headers(self, content_type: str, content_length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")

    def _reply(
        self,
        status: HTTPStatus,
        payload: bytes,
        content_type: str,
        *,
        head_only: bool = False,
    ) -> None:
        self.send_response(status)
        self._security_headers(content_type, len(payload))
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _route(self, *, head_only: bool) -> None:
        expected_hosts = {
            f"{LOOPBACK_HOST}:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        }
        if self.headers.get("Host") not in expected_hosts:
            self._reply(
                HTTPStatus.MISDIRECTED_REQUEST,
                b"loopback host required\n",
                "text/plain; charset=utf-8",
                head_only=head_only,
            )
            return
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            self._reply(
                HTTPStatus.BAD_REQUEST,
                b"query strings are not accepted\n",
                "text/plain; charset=utf-8",
                head_only=head_only,
            )
            return
        if parsed.path == "/api/status":
            if self.headers.get("X-Peano-Refresh") == "1":
                self.cache.request_refresh()
            payload = _strict_json_bytes(self.cache.snapshot())
            self._reply(
                HTTPStatus.OK,
                payload,
                "application/json; charset=utf-8",
                head_only=head_only,
            )
            return
        if parsed.path == "/healthz":
            self._reply(
                HTTPStatus.OK,
                b"ok\n",
                "text/plain; charset=utf-8",
                head_only=head_only,
            )
            return
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/dashboard.css": ("dashboard.css", "text/css; charset=utf-8"),
            "/dashboard.js": ("dashboard.js", "text/javascript; charset=utf-8"),
        }
        asset = assets.get(parsed.path)
        if asset is None:
            self._reply(
                HTTPStatus.NOT_FOUND,
                b"not found\n",
                "text/plain; charset=utf-8",
                head_only=head_only,
            )
            return
        path = STATIC_ROOT / asset[0]
        try:
            payload = path.read_bytes()
        except OSError:
            self._reply(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                b"dashboard asset unavailable\n",
                "text/plain; charset=utf-8",
                head_only=head_only,
            )
            return
        self._reply(
            HTTPStatus.OK,
            payload,
            asset[1],
            head_only=head_only,
        )

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        self._route(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib handler API
        self._route(head_only=True)

    def _method_not_allowed(self) -> None:
        payload = b"method not allowed\n"
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "GET, HEAD")
        self._security_headers("text/plain; charset=utf-8", len(payload))
        self.end_headers()
        self.wfile.write(payload)

    do_POST = _method_not_allowed  # type: ignore[assignment]
    do_PUT = _method_not_allowed  # type: ignore[assignment]
    do_PATCH = _method_not_allowed  # type: ignore[assignment]
    do_DELETE = _method_not_allowed  # type: ignore[assignment]

    def log_message(self, template: str, *args: object) -> None:
        sys.stderr.write("  " + (template % args) + "\n")


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], cache: SnapshotCache) -> None:
        self.snapshot_cache = cache
        super().__init__(address, DashboardHandler)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True, help="one decimal WMI Slurm job id")
    parser.add_argument("--ssh-target", default="wmicluster")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--no-open", action="store_true", help="do not open the dashboard URL")
    parser.add_argument(
        "--once",
        action="store_true",
        help="fetch, print one sanitized JSON snapshot, and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        job_id = validate_job_id(args.job_id)
        ssh_target = validate_ssh_target(args.ssh_target)
        if not 1 <= args.port <= 65535:
            raise ValueError("port must lie between 1 and 65535")
        cache = SnapshotCache(
            job_id,
            ssh_target,
            args.poll_seconds,
        )
    except ValueError as exc:
        _parser().error(str(exc))

    if args.once:
        cache.collect_once()
        status = cache.snapshot()
        sys.stdout.buffer.write(_strict_json_bytes(status))
        connection = status.get("connection")
        return 0 if type(connection) is dict and connection.get("state") == "live" else 1

    if not STATIC_ROOT.is_dir():
        print(f"dashboard assets are missing: {STATIC_ROOT}", file=sys.stderr)
        return 1
    try:
        server = DashboardServer((LOOPBACK_HOST, args.port), cache)
    except OSError as exc:
        print(f"cannot bind http://{LOOPBACK_HOST}:{args.port}/: {exc}", file=sys.stderr)
        return 1

    url = f"http://{LOOPBACK_HOST}:{server.server_port}/"
    cache.start()
    print("\n  Peano Lab Training Observatory")
    print(f"  {url}")
    print(f"  WMI job {job_id} via {ssh_target}; read-only; Ctrl-C to stop.\n")
    if not args.no_open:
        threading.Timer(0.35, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\n  stopped.")
    finally:
        server.shutdown()
        server.server_close()
        cache.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
