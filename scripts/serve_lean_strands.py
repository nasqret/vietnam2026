#!/usr/bin/env python3
"""Serve bounded, independently verified Lean proof jobs and theorem explorers.

The server is loopback-only unless an operator explicitly supplies
``--public-host``.  Exactly one proof-generation subprocess may be active;
the subprocess invokes the existing sealed-edition exporter and its real
one-worker Lean verification.  Existing theorem-explorer HTML gains the
shared selector assets only while it is served: frozen source pages are never
rewritten.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlsplit
import zipfile


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "scripts" / "export_peano_lean.py"
API_PREFIX = "/api/lean-strands"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
JOB_SCHEMA = "peano-lean-strand-service-v1"
LIVE_SCHEMA = "peano-lab-lean-live-v1"
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
THEOREM_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z")
SAFE_MODULE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
STAGES = frozenset({"plan", "translate", "certificate", "package", "compile", "repair", "complete"})
TERMINAL = frozenset({"completed", "failed", "cancelled"})
SENSITIVE_SUFFIXES = frozenset(
    {
        ".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db", ".token",
        ".py", ".pyc", ".pyo", ".env", ".toml", ".ini", ".cfg", ".conf",
        ".yaml", ".yml", ".sh", ".zsh", ".bash", ".lock",
    }
)
SENSITIVE_NAMES = frozenset(
    {
        "id_rsa", "id_ed25519", "credentials", "credentials.json", "secrets.json",
        "config.json", "settings.json", "service-account.json", "package.json",
    }
)
EXPLORER_SEGMENTS = frozenset(
    {
        "pa-proof-explorer",
        "bertrand-proof-explorer",
        "constructive-frontier-explorer",
        "constructive-grand-campaign",
    }
)


class ServiceError(ValueError):
    """An unsafe request, job transition, or generated artifact was rejected."""


class JobBusyError(ServiceError):
    """The one independently verified proof worker is already occupied."""


class JobNotFoundError(ServiceError):
    """The requested bounded, opaque job identifier is unavailable."""


class JobRateLimitError(ServiceError):
    """One client exceeded the bounded mutation window."""


@dataclass(frozen=True, slots=True)
class ServiceLimits:
    request_bytes: int = 16 * 1024
    response_bytes: int = 256 * 1024
    diagnostic_bytes: int = 64 * 1024
    event_line_bytes: int = 16 * 1024
    html_bytes: int = 4 * 1024 * 1024
    static_bytes: int = 128 * 1024 * 1024
    package_bytes: int = 64 * 1024 * 1024
    package_files: int = 4_096
    retained_jobs: int = 32
    ttl_seconds: int = 900
    memory_mib: int = 1_024
    verify_seconds: int = 180
    job_seconds: int = 240
    strand_nodes: int = 256
    strand_edges: int = 8_192
    strand_depth: int = 128
    proof_steps: int = 4_096
    proof_repairs: int = 16
    chunk_kib: int = 192
    live_url_bytes: int = 8_192
    concurrent_requests: int = 16
    mutations_per_minute: int = 30


@dataclass(frozen=True, slots=True)
class JobRequest:
    theorem: str
    edition: str
    memory_mib: int
    verify_seconds: int
    strand_nodes: int
    strand_edges: int
    strand_depth: int
    proof_steps: int
    proof_repairs: int
    chunk_kib: int
    strict_readable: bool


@dataclass(slots=True)
class JobRecord:
    identifier: str
    request: JobRequest
    directory: Path
    created_at: float
    updated_at: float
    status: str = "queued"
    stage: str = "queued"
    completed: int = 0
    total: int = 0
    diagnostics: deque[str] = field(default_factory=lambda: deque(maxlen=80))
    diagnostic_bytes: int = 0
    error: str | None = None
    manifest: dict[str, Any] | None = None
    lean_verified: bool = False
    verification_marker: bool = False
    live_url: str | None = None
    live_status: str = "fallback_required"
    live_source_bytes: int = 0
    process: subprocess.Popen[str] | None = None
    cancel_requested: bool = False
    revision: int = 0


def _safe_text(value: object, *, maximum: int = 512) -> str:
    if type(value) is not str:
        raise ServiceError("diagnostics and progress messages must be text")
    compact = " ".join(value.replace("\x00", "").split())
    return compact.encode("utf-8")[:maximum].decode("utf-8", errors="ignore")


def _bounded_json(payload: object, *, maximum: int) -> bytes:
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ServiceError("service response is not finite strict JSON") from error
    if len(encoded) > maximum:
        raise ServiceError("service response exceeds its reviewed byte limit")
    return encoded


def _validate_job_id(identifier: object) -> str:
    if type(identifier) is not str or JOB_ID.fullmatch(identifier) is None:
        raise JobNotFoundError("job identifier is not a valid opaque token")
    return identifier


def _bounded_integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ServiceError(f"{name} must be an integer between {minimum} and {maximum}")
    return value


def validate_request(payload: object, limits: ServiceLimits) -> JobRequest:
    """Accept only a bounded theorem request; never forward arbitrary CLI flags."""

    if type(payload) is not dict:
        raise ServiceError("proof-job request must be a JSON object")
    allowed = {
        "theorem",
        "edition",
        "max_memory_mib",
        "max_verify_seconds",
        "max_strand_nodes",
        "max_strand_edges",
        "max_strand_depth",
        "max_proof_steps",
        "max_proof_repairs",
        "max_chunk_kib",
        "strict_readable",
    }
    unexpected = set(payload).difference(allowed)
    if unexpected:
        raise ServiceError("unsupported proof-job option(s): " + ", ".join(sorted(unexpected)))
    name = payload.get("theorem")
    if type(name) is not str or name == "_" or THEOREM_NAME.fullmatch(name) is None:
        raise ServiceError("theorem must be one bounded safe Lean identifier")
    edition = payload.get("edition", "stable")
    if type(edition) is not str or edition not in {"stable", "alpha"}:
        raise ServiceError("edition must be exactly 'stable' or 'alpha'")
    strict = payload.get("strict_readable", False)
    if type(strict) is not bool:
        raise ServiceError("strict_readable must be an exact JSON boolean")
    return JobRequest(
        theorem=name,
        edition=edition,
        memory_mib=_bounded_integer(
            payload.get("max_memory_mib", limits.memory_mib),
            "max_memory_mib",
            64,
            limits.memory_mib,
        ),
        verify_seconds=_bounded_integer(
            payload.get("max_verify_seconds", limits.verify_seconds),
            "max_verify_seconds",
            1,
            limits.verify_seconds,
        ),
        strand_nodes=_bounded_integer(
            payload.get("max_strand_nodes", limits.strand_nodes),
            "max_strand_nodes",
            1,
            limits.strand_nodes,
        ),
        strand_edges=_bounded_integer(
            payload.get("max_strand_edges", limits.strand_edges),
            "max_strand_edges",
            1,
            limits.strand_edges,
        ),
        strand_depth=_bounded_integer(
            payload.get("max_strand_depth", limits.strand_depth),
            "max_strand_depth",
            1,
            limits.strand_depth,
        ),
        proof_steps=_bounded_integer(
            payload.get("max_proof_steps", limits.proof_steps),
            "max_proof_steps",
            1,
            limits.proof_steps,
        ),
        proof_repairs=_bounded_integer(
            payload.get("max_proof_repairs", limits.proof_repairs),
            "max_proof_repairs",
            0,
            limits.proof_repairs,
        ),
        chunk_kib=_bounded_integer(
            payload.get("max_chunk_kib", limits.chunk_kib),
            "max_chunk_kib",
            8,
            limits.chunk_kib,
        ),
        strict_readable=strict,
    )


def validate_live_url(value: object, *, maximum: int = 8_192) -> str | None:
    """Permit only the exact bounded official Lean Live code-share endpoint."""

    if value is None:
        return None
    if type(value) is not str or len(value.encode("utf-8")) > maximum:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "live.lean-lang.org"
        or parsed.netloc != "live.lean-lang.org"
        or parsed.path != "/"
        or parsed.query
        or not parsed.fragment.startswith("code=")
        or not parsed.fragment[5:]
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    return value


class JobManager:
    """One isolated, cancellable, independently verified Lean worker."""

    def __init__(
        self,
        storage: Path,
        *,
        limits: ServiceLimits | None = None,
        popen: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    ) -> None:
        self.limits = limits or ServiceLimits()
        selected_storage = Path(storage).expanduser()
        if selected_storage.is_symlink():
            raise ServiceError("proof-job storage cannot be a symlink")
        self.storage = selected_storage.resolve()
        self.storage.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.storage.is_dir():
            raise ServiceError("proof-job storage must be a directory")
        self._popen = popen
        self._lock = threading.RLock()
        self._changed = threading.Condition(self._lock)
        self._jobs: dict[str, JobRecord] = {}
        self._active: str | None = None
        self._mutation_windows: dict[str, deque[float]] = {}

    def check_mutation_rate(self, client: str) -> None:
        """Bound expensive mutations per client without retaining unbounded keys."""

        if type(client) is not str or not client or len(client) > 128:
            raise JobRateLimitError("proof-job client identity is unavailable")
        now = time.monotonic()
        with self._lock:
            if client not in self._mutation_windows:
                if len(self._mutation_windows) >= 1_024:
                    expired = [
                        key
                        for key, values in self._mutation_windows.items()
                        if not values or now - values[-1] >= 60.0
                    ]
                    for key in expired:
                        self._mutation_windows.pop(key, None)
                    if len(self._mutation_windows) >= 1_024:
                        raise JobRateLimitError("proof-job client capacity is temporarily full")
                self._mutation_windows[client] = deque()
            window = self._mutation_windows[client]
            while window and now - window[0] >= 60.0:
                window.popleft()
            if len(window) >= self.limits.mutations_per_minute:
                raise JobRateLimitError("proof-job mutation rate exceeded; retry within a minute")
            window.append(now)

    def _touch(self, job: JobRecord) -> None:
        job.updated_at = time.time()
        job.revision += 1
        self._changed.notify_all()

    def _remove_job_directory(self, job: JobRecord) -> None:
        target = job.directory.resolve()
        if (
            target.parent != self.storage
            or target.name != job.identifier
            or JOB_ID.fullmatch(target.name) is None
            or target.is_symlink()
        ):
            raise ServiceError("refusing to remove an unsafe proof-job directory")
        if target.is_dir():
            shutil.rmtree(target)

    def _cleanup_locked(self) -> None:
        deadline = time.time() - self.limits.ttl_seconds
        expired = [
            key
            for key, job in self._jobs.items()
            if job.status in TERMINAL and job.updated_at < deadline
        ]
        for key in expired:
            job = self._jobs.pop(key)
            self._remove_job_directory(job)

    def _snapshot_locked(self, job: JobRecord) -> dict[str, Any]:
        base = f"{API_PREFIX}/jobs/{job.identifier}"
        percent = (
            min(100, round(100 * job.completed / job.total))
            if job.total
            else (100 if job.status == "completed" else 0)
        )
        downloads = {
            "lean": base + "/download?format=lean",
            "zip": base + "/download?format=zip",
        }
        return {
            "schema": JOB_SCHEMA,
            "job_id": job.identifier,
            "theorem": job.request.theorem,
            "edition": job.request.edition,
            "status": job.status,
            "state": job.status,
            "stage": job.stage,
            "completed": job.completed,
            "total": job.total,
            "percent": percent,
            "progress": {
                "current": job.completed,
                "completed": job.completed,
                "total": job.total,
                "percent": percent,
            },
            "created_at": datetime.fromtimestamp(
                job.created_at,
                timezone.utc,
            ).isoformat(),
            "updated_at": datetime.fromtimestamp(
                job.updated_at,
                timezone.utc,
            ).isoformat(),
            "status_url": base,
            "events_url": base + "/events",
            "downloads": downloads,
            "download_urls": downloads,
            "live_url": job.live_url,
            "live_status": job.live_status,
            "live_compatible": job.live_status in {"ready", "oversized"},
            "standalone_lean": job.live_status in {"ready", "oversized"},
            "companion_required": job.live_status not in {"ready", "oversized"},
            "lean_live": {
                "compatible": job.live_status in {"ready", "oversized"},
                "url": job.live_url,
                "status": job.live_status,
                "source_bytes": job.live_source_bytes,
                "local_source_verified": job.live_status in {"ready", "oversized"},
                "remote_compilation": "not_run",
            },
            "lean_verified": job.lean_verified,
            "manifest": job.manifest,
            "diagnostics": list(job.diagnostics),
            "error": job.error,
        }

    def submit(self, payload: object) -> dict[str, Any]:
        request = validate_request(payload, self.limits)
        with self._changed:
            self._cleanup_locked()
            if self._active is not None:
                raise JobBusyError("one Lean proof job is already active; cancel it first")
            if len(self._jobs) >= self.limits.retained_jobs:
                raise JobBusyError("the bounded proof-job history is full")
            identifier = secrets.token_hex(16)
            if identifier in self._jobs:
                raise ServiceError("generated job identifier unexpectedly collided")
            directory = self.storage / identifier
            directory.mkdir(mode=0o700)
            now = time.time()
            job = JobRecord(identifier, request, directory, now, now)
            self._jobs[identifier] = job
            self._active = identifier
            thread = threading.Thread(
                target=self._execute,
                args=(identifier,),
                name=f"lean-proof-{identifier[:8]}",
                daemon=True,
            )
            thread.start()
            return self._snapshot_locked(job)

    def snapshot(self, identifier: str) -> dict[str, Any]:
        valid = _validate_job_id(identifier)
        with self._changed:
            self._cleanup_locked()
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            return self._snapshot_locked(job)

    def _diagnostic(self, job: JobRecord, message: object) -> None:
        try:
            text = _safe_text(message, maximum=1_024)
        except ServiceError:
            return
        if not text:
            return
        text = text.replace(str(ROOT), "<repository>").replace(
            str(job.directory),
            "<proof-job>",
        )
        encoded = len(text.encode("utf-8"))
        if job.diagnostic_bytes + encoded > self.limits.diagnostic_bytes:
            return
        job.diagnostic_bytes += encoded
        job.diagnostics.append(text)

    def _progress(self, job: JobRecord, payload: object) -> bool:
        if (
            type(payload) is not dict
            or payload.get("kind") != "lean_strand_progress"
            or type(payload.get("stage")) is not str
            or payload["stage"] not in STAGES
            or type(payload.get("completed")) is not int
            or type(payload.get("total")) is not int
            or not 0 <= payload["completed"] <= 10_000_000
            or not 0 <= payload["total"] <= 10_000_000
        ):
            return False
        theorem = payload.get("theorem")
        if theorem is not None and (
            type(theorem) is not str or THEOREM_NAME.fullmatch(theorem) is None
        ):
            return False
        module = payload.get("module")
        if module is not None and (
            type(module) is not str or SAFE_MODULE.fullmatch(module) is None
        ):
            return False
        job.stage = payload["stage"]
        job.completed = payload["completed"]
        job.total = payload["total"]
        message = payload.get("message")
        if message is not None:
            self._diagnostic(job, message)
        # Progress is not a proof receipt; publish URLs only after local checks.
        return True

    def _consume_stderr(self, identifier: str, stream: Any) -> None:
        while True:
            try:
                line = stream.readline(self.limits.event_line_bytes + 1)
            except (OSError, ValueError):
                return
            if not line:
                return
            with self._changed:
                job = self._jobs.get(identifier)
                if job is None:
                    return
                if len(line.encode("utf-8")) <= self.limits.event_line_bytes:
                    try:
                        event = json.loads(line)
                    except (TypeError, ValueError):
                        event = None
                    if not self._progress(job, event):
                        if line.strip() == "Independent Lean compilation: PASSED.":
                            job.verification_marker = True
                        self._diagnostic(job, line)
                else:
                    self._diagnostic(job, "exporter diagnostic exceeded its line limit")
                self._touch(job)

    def _command(self, job: JobRecord) -> list[str]:
        item = job.request
        command = [
            sys.executable,
            "-B",
            str(EXPORTER),
            item.theorem,
            "--edition",
            item.edition,
            "--format",
            "strand",
            "--package-dir",
            str(job.directory / "package"),
            "--verify",
            "--max-memory-mib",
            str(item.memory_mib),
            "--max-verify-seconds",
            str(item.verify_seconds),
            "--max-strand-nodes",
            str(item.strand_nodes),
            "--max-strand-edges",
            str(item.strand_edges),
            "--max-strand-depth",
            str(item.strand_depth),
            "--max-proof-steps",
            str(item.proof_steps),
            "--max-proof-repairs",
            str(item.proof_repairs),
            "--max-chunk-kib",
            str(item.chunk_kib),
            "--progress-json",
            "--live-lean-output",
            str(job.directory / "live.lean"),
        ]
        if item.strict_readable:
            command.append("--strict-readable")
        return command

    def _load_manifest(self, job: JobRecord) -> dict[str, Any]:
        source = job.directory / "package" / "manifest.json"
        if source.is_symlink() or not source.is_file():
            raise ServiceError("verified Lean job did not publish its proof-strand catalog")
        if source.stat().st_size > min(self.limits.package_bytes, 8 * 1024 * 1024):
            raise ServiceError("verified Lean job produced an oversized proof manifest")
        try:
            catalog = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as error:
            raise ServiceError("verified Lean job produced a malformed proof manifest") from error
        if (
            type(catalog) is not dict
            or catalog.get("schema") != "peano-lean-proof-strand-package-v1"
            or type(catalog.get("strands")) is not dict
            or len(catalog["strands"]) != 1
        ):
            raise ServiceError("verified Lean job produced an unauthenticated proof catalog")
        entry = next(iter(catalog["strands"].values()))
        if (
            type(entry) is not dict
            or entry.get("schema") != "peano-lab-lean-proof-strand-v1"
            or entry.get("name") != job.request.theorem
            or entry.get("edition") != job.request.edition
            or type(entry.get("node_count")) is not int
            or type(entry.get("translated_node_count")) is not int
            or type(entry.get("fallback_node_count")) is not int
            or type(entry.get("relative_path")) is not str
        ):
            raise ServiceError("verified Lean job manifest changed its selected theorem")
        return {
            "name": entry["name"],
            "edition": entry["edition"],
            "edition_version": entry.get("edition_version"),
            "node_count": entry["node_count"],
            "edge_count": entry.get("edge_count"),
            "translated_node_count": entry["translated_node_count"],
            "fallback_node_count": entry["fallback_node_count"],
            "chunk_count": entry.get("chunk_count"),
            "identity_sha256": entry.get("identity_sha256"),
            "relative_path": entry["relative_path"],
        }

    def _load_live(self, job: JobRecord) -> None:
        lean = job.directory / "live.lean"
        sidecar = job.directory / "live.json"
        if lean.is_symlink() or sidecar.is_symlink():
            raise ServiceError("Lean Live artifacts must not be symbolic links")
        if not lean.is_file() or not sidecar.is_file():
            job.live_status = "fallback_required"
            job.live_url = None
            return
        if sidecar.stat().st_size > self.limits.event_line_bytes:
            raise ServiceError("Lean Live metadata exceeds its reviewed size limit")
        if lean.stat().st_size > self.limits.package_bytes:
            raise ServiceError("Lean Live source exceeds its reviewed size limit")
        try:
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as error:
            raise ServiceError("Lean Live metadata is not canonical JSON") from error
        actual = lean.read_bytes()
        if (
            type(metadata) is not dict
            or metadata.get("schema") != LIVE_SCHEMA
            or metadata.get("theorem") != job.request.theorem
            or metadata.get("edition") != job.request.edition
            or metadata.get("source_sha256") != sha256(actual).hexdigest()
            or metadata.get("source_bytes") != len(actual)
            or metadata.get("local_source_verified") is not True
            or metadata.get("remote_compilation") != "not_run"
        ):
            raise ServiceError("Lean Live metadata does not authenticate its locally checked source")
        job.live_source_bytes = len(actual)
        shared = validate_live_url(
            metadata.get("share_url"),
            maximum=self.limits.live_url_bytes,
        )
        job.live_url = shared
        job.live_status = "ready" if shared is not None else "oversized"

    @staticmethod
    def _terminate_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except (OSError, ProcessLookupError):
            return
        try:
            process.wait(timeout=4.0)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except (OSError, ProcessLookupError):
                return

    def _execute(self, identifier: str) -> None:
        with self._changed:
            job = self._jobs.get(identifier)
            if job is None:
                return
            if job.cancel_requested:
                self._active = None
                return
            job.status = "running"
            job.stage = "plan"
            self._touch(job)
        reader: threading.Thread | None = None
        try:
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUNBUFFERED"] = "1"
            process = self._popen(
                self._command(job),
                cwd=str(ROOT),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=(os.name == "posix"),
            )
            with self._changed:
                job.process = process
                cancelled = job.cancel_requested
            if cancelled:
                self._terminate_process(process)
            elif process.stderr is not None:
                reader = threading.Thread(
                    target=self._consume_stderr,
                    args=(identifier, process.stderr),
                    name=f"lean-events-{identifier[:8]}",
                    daemon=True,
                )
                reader.start()
            try:
                result = process.wait(timeout=self.limits.job_seconds)
            except subprocess.TimeoutExpired:
                self._terminate_process(process)
                raise ServiceError(
                    f"proof job exceeded its {self.limits.job_seconds}-second global limit"
                ) from None
            if reader is not None:
                reader.join(timeout=2.0)
            with self._changed:
                if job.cancel_requested:
                    job.status = "cancelled"
                    job.stage = "cancelled"
                elif result != 0:
                    detail = job.diagnostics[-1] if job.diagnostics else f"exit code {result}"
                    job.status = "failed"
                    job.stage = "failed"
                    job.error = _safe_text(detail)
                else:
                    if not job.verification_marker:
                        raise ServiceError(
                            "proof exporter exited without an independent Lean compilation receipt"
                        )
                    job.manifest = self._load_manifest(job)
                    self._load_live(job)
                    job.status = "completed"
                    job.stage = "complete"
                    job.lean_verified = True
                    if job.total:
                        job.completed = job.total
                job.process = None
                self._active = None
                self._touch(job)
        except (OSError, ServiceError, ValueError) as error:
            with self._changed:
                if job.cancel_requested:
                    job.status = "cancelled"
                    job.stage = "cancelled"
                else:
                    job.status = "failed"
                    job.stage = "failed"
                    job.error = _safe_text(str(error))
                    self._diagnostic(job, str(error))
                job.process = None
                self._active = None
                self._touch(job)

    def cancel(self, identifier: str) -> dict[str, Any]:
        valid = _validate_job_id(identifier)
        with self._changed:
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            if job.status in TERMINAL:
                return self._snapshot_locked(job)
            job.cancel_requested = True
            job.status = "cancelled"
            job.stage = "cancelled"
            process = job.process
            self._touch(job)
        if process is not None:
            self._terminate_process(process)
        with self._changed:
            return self._snapshot_locked(job)

    def wait_for_update(
        self,
        identifier: str,
        revision: int,
        timeout: float,
    ) -> tuple[dict[str, Any], int]:
        valid = _validate_job_id(identifier)
        with self._changed:
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            if job.revision == revision and job.status not in TERMINAL:
                self._changed.wait(timeout=max(0.0, min(timeout, 5.0)))
            return self._snapshot_locked(job), job.revision

    def _checked_job(self, identifier: str) -> JobRecord:
        valid = _validate_job_id(identifier)
        with self._changed:
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            if job.status != "completed" or not job.lean_verified or job.manifest is None:
                raise ServiceError("only a completed independently verified proof can be downloaded")
            return job

    def lean_download(self, identifier: str) -> tuple[Path, bool]:
        job = self._checked_job(identifier)
        standalone = job.directory / "live.lean"
        if job.live_status in {"ready", "oversized"} and standalone.is_file():
            selected = standalone
            independent = True
        else:
            relative = job.manifest["relative_path"]  # type: ignore[index]
            if type(relative) is not str:
                raise ServiceError("verified proof manifest has no safe Lean module")
            selected = (job.directory / "package" / relative).resolve()
            independent = False
        root = job.directory.resolve()
        if (
            selected.is_symlink()
            or not selected.is_file()
            or not selected.is_relative_to(root)
            or selected.stat().st_size > self.limits.package_bytes
        ):
            raise ServiceError("requested Lean source escaped its bounded proof job")
        return selected, independent

    def zip_download(self, identifier: str) -> Path:
        job = self._checked_job(identifier)
        target = job.directory / "proof.zip"
        if target.is_symlink():
            raise ServiceError("proof ZIP output must not be a symbolic link")
        if target.is_file():
            if target.stat().st_size > self.limits.package_bytes:
                raise ServiceError("existing proof ZIP exceeds its reviewed size limit")
            return target
        package = (job.directory / "package").resolve()
        files: list[tuple[str, Path]] = []
        for item in package.rglob("*"):
            if item.is_symlink():
                raise ServiceError("generated Lean proof package must not contain symbolic links")
            if item.is_file() and item.suffix in {".lean", ".json"}:
                files.append((item.relative_to(package).as_posix(), item))
        live = job.directory / "live.lean"
        sidecar = job.directory / "live.json"
        if job.live_status in {"ready", "oversized"} and live.is_file() and sidecar.is_file():
            files.extend((("standalone.lean", live), ("lean-live.json", sidecar)))
        if len(files) > self.limits.package_files:
            raise ServiceError("proof ZIP exceeds its reviewed file-count limit")
        total = 0
        entries: list[tuple[str, Path]] = []
        names: set[str] = set()
        for name, source in files:
            if source.is_symlink():
                raise ServiceError("proof ZIP source must not be a symbolic link")
            resolved = source.resolve()
            if not resolved.is_relative_to(job.directory.resolve()):
                raise ServiceError("proof ZIP source escaped its bounded job")
            if not name or name.startswith("/") or "\\" in name or any(
                part in {"", ".", ".."} for part in name.split("/")
            ):
                raise ServiceError("proof ZIP contains an unsafe archive path")
            if name in names or name == "README.txt":
                raise ServiceError("proof ZIP contains colliding generated modules")
            names.add(name)
            total += resolved.stat().st_size
            if total > self.limits.package_bytes:
                raise ServiceError("proof ZIP exceeds its reviewed source-size limit")
            entries.append((name, resolved))
        manifest = job.manifest
        if manifest is None:
            raise ServiceError("verified proof archive is missing its checked manifest")
        standalone_status = (
            "PASSED; see standalone.lean"
            if job.live_status in {"ready", "oversized"}
            else "unavailable; separately installed checked Lean companion is required"
        )
        readme = (
            "HYDRA INDEPENDENTLY VERIFIED GENERATED LEAN PACKAGE\n"
            "==================================================\n\n"
            f"Theorem: {job.request.theorem}\n"
            f"Edition: {job.request.edition}\n"
            "Independent local package compilation: PASSED\n"
            f"Readable theorem nodes: {manifest['translated_node_count']}\n"
            f"Checked local certificate nodes: {manifest['fallback_node_count']}\n"
            f"Standalone core Lean verification: {standalone_status}\n"
            "Remote Lean Live compilation: NOT RUN\n\n"
            "This archive contains generated proof artifacts only. It intentionally "
            "does not publish the separately maintained private Lean companion. "
            "To recompile presentation or certificate-backed package modules, install "
            "that checked companion separately, overlay the generated PeanoLab/ tree, "
            "and review manifest.json and the final #print axioms command. "
            "When included, standalone.lean requires only the pinned core Lean toolchain.\n"
        ).encode("utf-8")
        total += len(readme)
        if total > self.limits.package_bytes:
            raise ServiceError("proof ZIP README exceeds its reviewed source-size limit")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".proof-", suffix=".zip.tmp", dir=job.directory
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, source in sorted(entries):
                    information = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    information.compress_type = zipfile.ZIP_DEFLATED
                    information.external_attr = 0o644 << 16
                    archive.writestr(information, source.read_bytes())
                information = zipfile.ZipInfo("README.txt", date_time=(1980, 1, 1, 0, 0, 0))
                information.compress_type = zipfile.ZIP_DEFLATED
                information.external_attr = 0o644 << 16
                archive.writestr(information, readme)
            if temporary.stat().st_size > self.limits.package_bytes:
                raise ServiceError("compressed proof ZIP exceeds its reviewed size limit")
            os.replace(temporary, target)
        finally:
            if temporary.is_file() and not temporary.is_symlink():
                temporary.unlink()
        return target


class LeanStrandServer(ThreadingHTTPServer):
    """Bounded-thread same-origin static and verified-proof HTTP service."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        manager: JobManager,
        directory: Path,
        *,
        public_host: bool = False,
    ) -> None:
        self.job_manager = manager
        self.static_directory = Path(directory).expanduser().resolve()
        if not self.static_directory.is_dir():
            raise ServiceError("static root must be an existing directory")
        if manager.storage.is_relative_to(self.static_directory):
            raise ServiceError("private proof-job storage must not lie beneath the public static root")
        self.public_host = public_host
        self._request_slots = threading.BoundedSemaphore(manager.limits.concurrent_requests)
        super().__init__(address, LeanStrandHandler)

    def process_request(self, request: Any, client_address: Any) -> None:
        if not self._request_slots.acquire(blocking=False):
            try:
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"Connection: close\r\nContent-Length: 0\r\n\r\n"
                )
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._request_slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


class LeanStrandHandler(BaseHTTPRequestHandler):
    """Minimal safe static routes and one authenticated-by-compilation job API."""

    server: LeanStrandServer
    server_version = "HydraLeanStrands/1"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10.0)

    def _headers(self, kind: str, size: int, *, download: str | None = None) -> None:
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        if download is not None:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')

    def _json(self, status: HTTPStatus, payload: object, *, head_only: bool = False) -> None:
        try:
            content = _bounded_json(payload, maximum=self.server.job_manager.limits.response_bytes)
        except ServiceError:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            content = b'{"error":"response exceeded its reviewed size limit"}\n'
        self.send_response(status)
        self._headers("application/json; charset=utf-8", len(content))
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def _failure(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"schema": JOB_SCHEMA, "error": _safe_text(message)})

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        try:
            actual = urlsplit(origin)
        except ValueError:
            return False
        expected = self.headers.get("Host", "")
        return (
            actual.scheme in {"http", "https"}
            and actual.netloc == expected
            and not actual.username
            and not actual.password
            and not actual.query
            and not actual.fragment
        )

    def _host_allowed(self) -> bool:
        host = self.headers.get("Host", "")
        if not host or len(host) > 256 or any(char.isspace() for char in host):
            return False
        if self.server.public_host:
            return True
        expected = {
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
            f"[::1]:{self.server.server_port}",
        }
        return host in expected

    def _request_payload(self) -> object:
        if not self._same_origin():
            raise PermissionError("cross-origin proof mutation is forbidden")
        if self.headers.get("Transfer-Encoding") is not None:
            raise ServiceError("chunked proof-job requests are not supported")
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            raise ServiceError("proof-job requests require application/json")
        raw = self.headers.get("Content-Length")
        if raw is None or not raw.isdecimal():
            raise ServiceError("proof-job requests require an exact Content-Length")
        size = int(raw)
        if not 1 <= size <= self.server.job_manager.limits.request_bytes:
            raise ServiceError("proof-job request exceeds its reviewed size limit")
        try:
            return json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeError, TypeError, ValueError) as error:
            raise ServiceError("proof-job body is not valid UTF-8 JSON") from error

    def _api_parts(self) -> tuple[str, ...] | None:
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            return None
        path = parsed.path
        if path == API_PREFIX:
            return ()
        if not path.startswith(API_PREFIX + "/"):
            return None
        tail = path[len(API_PREFIX) + 1:]
        if not tail or any(part in {"", ".", ".."} for part in tail.split("/")):
            return None
        return tuple(tail.split("/"))

    def _static_path(self) -> tuple[Path, tuple[str, ...]]:
        try:
            raw = urlsplit(self.path).path
            decoded = unquote(raw, errors="strict")
        except (UnicodeError, ValueError) as error:
            raise PermissionError("unsafe static path encoding") from error
        if "\x00" in decoded or "\\" in decoded:
            raise PermissionError("unsafe static path characters")
        parts = tuple(part for part in decoded.split("/") if part)
        if any(
            part in {".", ".."}
            or part.startswith(".")
            or part.lower() in SENSITIVE_NAMES
            or Path(part).suffix.lower() in SENSITIVE_SUFFIXES
            for part in parts
        ):
            raise PermissionError("private repository or credential paths are unavailable")
        candidate = self.server.static_directory.joinpath(*parts).resolve()
        if not candidate.is_relative_to(self.server.static_directory):
            raise PermissionError("static path escapes its configured root")
        if candidate.is_dir():
            candidate = (candidate / "index.html").resolve()
            if not candidate.is_file():
                raise PermissionError("directory listings are disabled")
        if not candidate.is_file():
            raise FileNotFoundError("static resource not found")
        if candidate.stat().st_size > self.server.job_manager.limits.static_bytes:
            raise ServiceError("static resource exceeds its reviewed byte limit")
        return candidate, parts

    def _asset_prefix(self) -> str | None:
        base = self.server.static_directory
        for relative in (
            Path("book/_static/lean-selector"),
            Path("_static/lean-selector"),
            Path("lean-selector"),
        ):
            candidate = (base / relative).resolve()
            if (
                candidate.is_relative_to(base)
                and (candidate / "lean-selector.js").is_file()
                and (candidate / "lean-selector.css").is_file()
            ):
                return "/" + relative.as_posix()
        return None

    def _inject_selector(self, path: Path, parts: tuple[str, ...]) -> bytes | None:
        if (
            path.suffix.lower() != ".html"
            or not (
                (path.name == "graph.html" and "_static" in parts)
                or EXPLORER_SEGMENTS.intersection(parts)
            )
            or path.stat().st_size > self.server.job_manager.limits.html_bytes
        ):
            return None
        prefix = self._asset_prefix()
        if prefix is None:
            return None
        content = path.read_bytes()
        marker = b"lean-selector.js"
        if marker in content:
            return content
        closing = re.search(rb"</head\s*>", content, flags=re.IGNORECASE)
        if closing is None:
            return content
        insertion = (
            f'<link rel="stylesheet" href="{prefix}/lean-selector.css">\n'
            f'<script defer src="{prefix}/lean-selector.js"></script>\n'
        ).encode("utf-8")
        return content[:closing.start()] + insertion + content[closing.start():]

    def _serve_static(self, *, head_only: bool) -> None:
        try:
            source, parts = self._static_path()
            injected = self._inject_selector(source, parts)
        except PermissionError as error:
            self._failure(HTTPStatus.FORBIDDEN, str(error))
            return
        except FileNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        except (OSError, ServiceError) as error:
            self._failure(HTTPStatus.BAD_REQUEST, str(error))
            return
        content_type = mimetypes.guess_type(str(source))[0] or "application/octet-stream"
        if content_type.startswith(("text/", "application/javascript")):
            content_type += "; charset=utf-8"
        length = len(injected) if injected is not None else source.stat().st_size
        self.send_response(HTTPStatus.OK)
        self._headers(content_type, length)
        self.end_headers()
        if head_only:
            return
        if injected is not None:
            self.wfile.write(injected)
            return
        with source.open("rb") as stream:
            shutil.copyfileobj(stream, self.wfile, length=65_536)

    def _download(self, identifier: str, *, head_only: bool) -> None:
        try:
            query = parse_qs(urlsplit(self.path).query, strict_parsing=True)
        except ValueError:
            self._failure(HTTPStatus.BAD_REQUEST, "invalid proof-download query")
            return
        if set(query) != {"format"} or len(query["format"]) != 1:
            self._failure(HTTPStatus.BAD_REQUEST, "proof download needs exactly one format")
            return
        style = query["format"][0]
        try:
            if style == "lean":
                source, standalone = self.server.job_manager.lean_download(identifier)
                filename = (
                    "readable-standalone.lean" if standalone else "verified-proof-strand.lean"
                )
                kind = "text/plain; charset=utf-8"
            elif style == "zip":
                source = self.server.job_manager.zip_download(identifier)
                filename = "verified-lean-proof.zip"
                kind = "application/zip"
            else:
                raise ServiceError("proof download format must be exactly lean or zip")
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        except ServiceError as error:
            self._failure(HTTPStatus.CONFLICT, str(error))
            return
        self.send_response(HTTPStatus.OK)
        self._headers(kind, source.stat().st_size, download=filename)
        self.end_headers()
        if not head_only:
            with source.open("rb") as stream:
                shutil.copyfileobj(stream, self.wfile, length=65_536)

    def _events(self, identifier: str) -> None:
        try:
            snapshot = self.server.job_manager.snapshot(identifier)
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        revision = -1
        try:
            while True:
                snapshot, revision = self.server.job_manager.wait_for_update(
                    identifier,
                    revision,
                    2.0,
                )
                encoded = _bounded_json(
                    snapshot,
                    maximum=self.server.job_manager.limits.response_bytes,
                ).rstrip(b"\n")
                self.wfile.write(b"event: status\ndata: " + encoded + b"\n\n")
                self.wfile.flush()
                if snapshot["status"] in TERMINAL:
                    return
        except (BrokenPipeError, ConnectionError, JobNotFoundError, OSError, ServiceError):
            return

    def _get(self, *, head_only: bool) -> None:
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            prefix = "/book" if (self.server.static_directory / "book/_static").is_dir() else ""
            location = f"{prefix}/_static/pa-proof-explorer/defined/graph.html?target=PA000F"
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self._headers("text/plain; charset=utf-8", 0)
            self.end_headers()
            return
        if parsed.path in {"/health", "/healthz"}:
            self._json(HTTPStatus.OK, {"status": "ok", "schema": JOB_SCHEMA}, head_only=head_only)
            return
        parts = self._api_parts()
        if parts is None:
            self._serve_static(head_only=head_only)
            return
        if parts == ("config",):
            limits = self.server.job_manager.limits
            self._json(
                HTTPStatus.OK,
                {
                    "schema": JOB_SCHEMA,
                    "public_host": self.server.public_host,
                    "single_worker": True,
                    "max_concurrent_jobs": 1,
                    "independent_lean_verification": True,
                    "max_memory_mib": limits.memory_mib,
                    "memory_mib": limits.memory_mib,
                    "max_verify_seconds": limits.verify_seconds,
                    "max_strand_nodes": limits.strand_nodes,
                    "max_nodes": limits.strand_nodes,
                    "max_chunk_kib": limits.chunk_kib,
                },
                head_only=head_only,
            )
            return
        if len(parts) not in {2, 3} or parts[0] != "jobs":
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        if len(parts) == 3:
            if parts[2] == "download":
                self._download(parts[1], head_only=head_only)
            elif parts[2] == "events" and not head_only:
                self._events(parts[1])
            else:
                self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        try:
            snapshot = self.server.job_manager.snapshot(parts[1])
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        self._json(HTTPStatus.OK, snapshot, head_only=head_only)

    def do_GET(self) -> None:  # noqa: N802
        self._get(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802
        self._get(head_only=True)

    def do_POST(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        if self._api_parts() != ("jobs",):
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        try:
            payload = self._request_payload()
            self.server.job_manager.check_mutation_rate(self.client_address[0])
            snapshot = self.server.job_manager.submit(payload)
        except PermissionError as error:
            self._failure(HTTPStatus.FORBIDDEN, str(error))
            return
        except JobRateLimitError as error:
            self._failure(HTTPStatus.TOO_MANY_REQUESTS, str(error))
            return
        except JobBusyError as error:
            self._failure(HTTPStatus.CONFLICT, str(error))
            return
        except ServiceError as error:
            self._failure(HTTPStatus.BAD_REQUEST, str(error))
            return
        self._json(HTTPStatus.ACCEPTED, snapshot)

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        if not self._same_origin():
            self._failure(HTTPStatus.FORBIDDEN, "cross-origin proof cancellation is forbidden")
            return
        parts = self._api_parts()
        if parts is None or len(parts) != 2 or parts[0] != "jobs":
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        try:
            self.server.job_manager.check_mutation_rate(self.client_address[0])
            snapshot = self.server.job_manager.cancel(parts[1])
        except JobRateLimitError as error:
            self._failure(HTTPStatus.TOO_MANY_REQUESTS, str(error))
            return
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        self._json(HTTPStatus.OK, snapshot)

    def do_PUT(self) -> None:  # noqa: N802
        self._failure(HTTPStatus.METHOD_NOT_ALLOWED, "proof service does not support PUT")

    def do_PATCH(self) -> None:  # noqa: N802
        self._failure(HTTPStatus.METHOD_NOT_ALLOWED, "proof service does not support PATCH")

    def log_message(self, template: str, *arguments: object) -> None:
        sys.stderr.write("  " + _safe_text(template % arguments, maximum=1_024) + "\n")


def _safe_bind_host(host: str, *, public_host: bool) -> str:
    if type(host) is not str or not host or any(char.isspace() for char in host):
        raise ServiceError("listen host must be nonempty safe text")
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not loopback and not public_host:
        raise ServiceError("non-loopback exposure requires explicit --public-host")
    return host


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--public-host", action="store_true")
    parser.add_argument("--directory", type=Path, default=ROOT)
    parser.add_argument("--storage", type=Path)
    parser.add_argument("--max-memory-mib", type=int, default=1_024)
    parser.add_argument("--max-verify-seconds", type=int, default=180)
    parser.add_argument("--max-job-seconds", type=int, default=240)
    parser.add_argument("--job-ttl-seconds", type=int, default=900)
    parser.add_argument("--max-jobs", type=int, default=32)
    parser.add_argument("--max-strand-nodes", type=int, default=256)
    parser.add_argument("--max-chunk-kib", type=int, default=192)
    return parser


def build_server(argv: list[str] | None = None) -> LeanStrandServer:
    args = _parser().parse_args(argv)
    host = _safe_bind_host(args.host, public_host=args.public_host)
    port = _bounded_integer(args.port, "port", 0, 65_535)
    memory = _bounded_integer(args.max_memory_mib, "max_memory_mib", 64, 4_096)
    verification = _bounded_integer(args.max_verify_seconds, "max_verify_seconds", 1, 900)
    runtime = _bounded_integer(args.max_job_seconds, "max_job_seconds", verification, 1_200)
    ttl = _bounded_integer(args.job_ttl_seconds, "job_ttl_seconds", 30, 86_400)
    jobs = _bounded_integer(args.max_jobs, "max_jobs", 1, 256)
    nodes = _bounded_integer(args.max_strand_nodes, "max_strand_nodes", 1, 2_048)
    chunks = _bounded_integer(args.max_chunk_kib, "max_chunk_kib", 8, 1_024)
    storage = (
        args.storage
        if args.storage is not None
        else Path(tempfile.mkdtemp(prefix="hydra-lean-proof-jobs-"))
    )
    manager = JobManager(
        storage,
        limits=ServiceLimits(
            memory_mib=memory,
            verify_seconds=verification,
            job_seconds=runtime,
            ttl_seconds=ttl,
            retained_jobs=jobs,
            strand_nodes=nodes,
            chunk_kib=chunks,
        ),
    )
    return LeanStrandServer(
        (host, port),
        manager,
        args.directory,
        public_host=args.public_host,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        server = build_server(argv)
    except (OSError, ServiceError, ValueError) as error:
        print(f"Lean proof service: {error}", file=sys.stderr)
        return 1
    actual_host = server.server_address[0]
    display_host = "127.0.0.1" if actual_host == "0.0.0.0" else actual_host
    base = f"http://{display_host}:{server.server_port}"
    if server.static_directory == ROOT:
        frontier = "/book/_static/constructive-frontier-explorer/index.html"
        proof_graph = "/book/_static/pa-proof-explorer/defined/graph.html?target=PA000F"
    else:
        frontier = "/_static/constructive-frontier-explorer/index.html"
        proof_graph = "/_static/pa-proof-explorer/defined/graph.html?target=PA000F"
    print(f"Hydra Lean proof service: {base}")
    print(f"Frontier theorem explorer: {base}{frontier}")
    print(f"Safe first theorem (add_comm): {base}{proof_graph}")
    print(f"Verified proof-job API: {base}{API_PREFIX}/jobs")
    if server.public_host:
        print("PUBLIC HOST ENABLED: repository explorer and proof API are externally reachable.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
