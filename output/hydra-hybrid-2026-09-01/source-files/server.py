#!/usr/bin/env python3
"""Loopback-only Hydra playground with fresh, bounded proof/model workers."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit
import uuid

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))
import worker

# Preserve the venv launcher path; resolving its symlink can lose that runtime.
PYTHON = sys.executable
WORKER = APP / "worker.py"
POLL_SECONDS = 0.10
MAX_STDERR = 64 * 1024
MAX_STDOUT = 2 * worker.MAX_RESULT_BYTES
MAX_JOBS = 16
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/examples.json": ("examples.json", "application/json; charset=utf-8"),
    "/api/examples": ("examples.json", "application/json; charset=utf-8"),
}


class RequestError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def validate_origin(host: str | None, origin: str | None, port: int) -> None:
    allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
    if host not in allowed or (origin is not None and origin != "http://" + host):
        raise RequestError("Only this local playground origin is allowed.", 403)


def validate_token(actual: str | None, expected: str) -> None:
    if type(actual) is not str or not actual.isascii() or not secrets.compare_digest(actual, expected):
        raise RequestError("Missing or invalid playground CSRF token. Reload the page.", 403)


def metadata_status() -> dict:
    try:
        import model_runtime
        value = model_runtime.metadata_status()
        if type(value) is not dict or type(value.get("available")) is not bool:
            raise ValueError("The model metadata response is invalid.")
        return value
    except Exception as error:
        return {"available": False, "name": "Hydra mixed retention adapter", "device": None,
                "detail": "Model runtime is unavailable: " + " ".join(str(error).split())[:400]}


def vampire_status() -> dict:
    try:
        import vampire_process
        return vampire_process.metadata_status()
    except (ImportError, OSError, ValueError) as error:
        return {"available": False, "name": "Vampire", "detail": str(error)[:400]}


def search_modes(model, vampire):
    return {
        "model": {"available": model["available"], "name": "Model only"},
        "heuristic": {"available": True, "name": "Heuristics only"},
        "symbolic": {"available": vampire["available"], "name": "Heuristics + Vampire"},
        "hybrid": {"available": model["available"] and vampire["available"],
                   "name": "Heuristics + Vampire + model"},
    }


def worker_environment() -> dict:
    keep = {"HOME", "TMPDIR", "LANG", "LC_ALL", "USER", "LOGNAME", "SSL_CERT_FILE"}
    env = {key: value for key, value in os.environ.items() if key in keep}
    env.update(PATH=str(Path(PYTHON).parent) + ":/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
               TOKENIZERS_PARALLELISM="false", CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="8",
               MKL_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", VECLIB_MAXIMUM_THREADS="8")
    return env


def process_snapshot() -> dict[int, tuple[int, int, int, tuple[str, ...]]]:
    """PID/birth/parent/group/RSS metadata; never arguments or environment."""
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,pgid=,lstart=,rss="],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=2, check=False, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    if result.returncode != 0 or len(result.stdout) > 2 * 1024**2:
        raise RuntimeError("Owned-process accounting is unavailable; no computation will start.")
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 9 or not all(fields[index].isdigit() for index in (0, 1, 2, 5, 7, 8)):
            raise RuntimeError("Invalid process-accounting response.")
        pid, parent, group = map(int, fields[:3])
        birth = tuple(value.decode("ascii") for value in fields[3:8])
        rows[pid] = (parent, group, int(fields[8]) * 1024, birth)
    return rows


def owned_processes(rows: dict, pid: int, known: dict, *, unreaped=False) -> dict:
    """Discover only a live child or descendants of recorded birth identities.

    Keep ``known`` for the entire request, including entries that have exited.
    An unrelated process reusing the leader PID is never adopted after reaping.
    """
    retained = {item: birth for item, birth in known.items() if item in rows and rows[item][3] == birth}
    root_matches = pid in rows and (rows[pid][3] == known.get(pid) or (unreaped and pid not in known))
    group_matches = root_matches or any(rows[item][1] == pid for item in retained)
    owned = dict(retained)
    if group_matches:
        owned.update({item: value[3] for item, value in rows.items() if value[1] == pid})
    if root_matches:
        owned[pid] = rows[pid][3]
    while True:
        extra = {item: value[3] for item, value in rows.items() if value[0] in owned}
        if set(extra) <= set(owned):
            return owned
        owned.update(extra)


def group_is_empty(rows: dict, group: int) -> bool:
    # Lack of an observed birth identity is not evidence of an empty group.
    # Never adopt/signal an unknown member, but never publish quiescence either.
    return not any(value[1] == group for value in rows.values())


def _kill(process: subprocess.Popen, owned: dict) -> None:
    # An unreaped direct child cannot have its PID recycled. After reaping,
    # signal a group only if a recorded member's birth identity still matches.
    # Kill an unreaped direct child's group even when subsequent ps sampling
    # fails. Sampling failure must never leave that worker running.
    if process.returncode is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    rows = process_snapshot()
    verified = {pid: birth for pid, birth in owned.items() if pid in rows and rows[pid][3] == birth}
    if process.returncode is not None and any(rows[pid][1] == process.pid for pid in verified):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    # No standalone PID signals: user input cannot make us target unrelated PIDs.
    if any(rows[pid][1] != process.pid for pid in verified):
        raise RuntimeError("An unexpected process escaped its owned group; refusing unsafe PID signalling.")


def run_worker(mode: str, request: dict, cancel: threading.Event,
               on_progress=lambda _: None) -> dict:
    """Publish a result only after a real zero exit and an empty owned group."""
    limits = worker.LIMITS["manual" if mode == "replay" else "search"]
    started = time.monotonic()
    process = None
    selector = selectors.DefaultSelector()
    known: dict = {}
    stderr, line_buffer = bytearray(), bytearray()
    stdout_count, peak, solver_peak = 0, 0, 0
    final = None
    error = None
    cancelled = False
    code = None
    quiescent = True
    try:
        if cancel.is_set():
            cancelled = True
            raise RuntimeError("Cancelled by the user.")
        process_snapshot()  # Fail closed before model or native work if ps is denied.
        normalized = worker.validate_request(mode, request)
        allow_solver = mode == "search" and normalized["search_mode"] in {"symbolic", "hybrid"}
        payload = worker.json_bytes(normalized) + b"\n"
        if len(payload) > worker.MAX_BODY_BYTES:
            raise ValueError("Request exceeds its byte limit.")
        process = subprocess.Popen([PYTHON, "-I", "-B", str(WORKER), "--mode", mode],
                                   cwd=str(APP), env=worker_environment(), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, close_fds=True)
        quiescent = False
        for label in ("stdin", "stdout", "stderr"):
            stream = getattr(process, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_WRITE if label == "stdin" else selectors.EVENT_READ, label)
        offset, next_sample = 0, 0.0
        while selector.get_map() or process.poll() is None:
            now = time.monotonic()
            if cancel.is_set():
                cancelled = True
                raise RuntimeError("Cancelled by the user.")
            if now - started >= limits["wall_seconds"] - 4:
                raise TimeoutError("Request reached its wall-time limit.")
            if now >= next_sample:
                rows = process_snapshot()
                owned = owned_processes(rows, process.pid, known, unreaped=process.returncode is None)
                known.update(owned)
                rss = sum(rows[item][2] for item in owned if item in rows)
                peak = max(peak, rss)
                descendants = set(owned) - {process.pid}
                if descendants:
                    if not allow_solver or len(descendants) > 1 or any(
                        rows[pid][0] != process.pid or rows[pid][1] != process.pid for pid in descendants
                    ):
                        raise RuntimeError("Worker attempted an unauthorized additional process.")
                    solver_rss = sum(rows[pid][2] for pid in descendants)
                    solver_peak = max(solver_peak, solver_rss)
                    if solver_rss > worker.LIMITS["vampire"]["sampled_rss_bytes"]:
                        raise RuntimeError("Vampire exceeded its sampled memory limit.")
                if rss > limits["rss_bytes"]:
                    raise RuntimeError("Request exceeded its sampled memory limit.")
                next_sample = now + POLL_SECONDS
            for key, _ in selector.select(POLL_SECONDS):
                if key.data == "stdin":
                    try:
                        sent = os.write(key.fd, payload[offset:offset + 16384])
                    except BrokenPipeError:
                        sent = 0
                        offset = len(payload)
                    except BlockingIOError:
                        continue
                    offset += sent
                    if offset == len(payload):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                raw = os.read(key.fd, 65536)
                if not raw:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stderr":
                    stderr.extend(raw)
                    if len(stderr) > MAX_STDERR:
                        raise RuntimeError("Worker stderr exceeded its output limit.")
                    continue
                stdout_count += len(raw)
                if stdout_count > MAX_STDOUT:
                    raise RuntimeError("Worker output exceeded its byte limit.")
                line_buffer.extend(raw)
                while b"\n" in line_buffer:
                    line, _, rest = line_buffer.partition(b"\n")
                    line_buffer[:] = rest
                    if len(line) > worker.MAX_RESULT_BYTES or not line:
                        raise RuntimeError("Invalid worker event size.")
                    event = json.loads(line)
                    if type(event) is not dict or set(event) != {"type", event.get("type")}:
                        raise RuntimeError("Invalid worker event.")
                    kind = event["type"]
                    value = event[kind]
                    if type(value) is not dict or final is not None:
                        raise RuntimeError("Invalid worker event sequence.")
                    if kind == "progress" and len(line) <= worker.MAX_PROGRESS_BYTES:
                        on_progress(value)
                    elif kind == "result":
                        final = value
                    elif kind == "error":
                        error = str(value.get("message", "Worker failed."))[:2048]
                    else:
                        raise RuntimeError("Unknown worker event.")
        code = process.wait(timeout=2)
        if line_buffer:
            raise RuntimeError("Worker left an incomplete output event.")
        if code != 0 or error is not None or final is None:
            detail = error or bytes(stderr).decode("utf-8", "replace").strip()[-1200:]
            raise RuntimeError(detail or f"Worker exited without a result (exit {code}).")
        if type(final.get("kernel_checked")) is not bool or type(final.get("trace")) is not list:
            raise RuntimeError("Worker did not return a genuine proof result shape.")
        if cancel.is_set():
            cancelled = True
            raise RuntimeError("Cancelled by the user.")
    except Exception as failure:
        error = " ".join(str(failure).split())[:2048] or type(failure).__name__
    finally:
        if process is not None:
            try:
                if process.returncode is None:
                    _kill(process, known)
                process.wait(timeout=2)
                rows = process_snapshot()
                remaining = owned_processes(rows, process.pid, known)
                if remaining:
                    _kill(process, known)
                if remaining or not group_is_empty(rows, process.pid):
                    cleanup_until = time.monotonic() + 3.2
                    while (remaining or not group_is_empty(rows, process.pid)) and time.monotonic() < cleanup_until:
                        time.sleep(0.05)
                        rows = process_snapshot()
                        remaining = owned_processes(rows, process.pid, known)
                if remaining or not group_is_empty(rows, process.pid):
                    raise RuntimeError("The worker group has not quiesced.")
                quiescent = True
            except Exception as failure:
                # _kill signals the unreaped child before sampling. Always
                # attempt to reap it, but do not claim verified cleanup if
                # the final group observation is unavailable.
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                error = "Worker cleanup could not be confirmed: " + " ".join(str(failure).split())[:1200]
                cancelled = False
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
        selector.close()
    elapsed = time.monotonic() - started
    if elapsed >= limits["wall_seconds"] and error is None:
        error = "The request exceeded its whole wall-time limit."
    if cancel.is_set() and quiescent:
        cancelled = True
    return {"result": final if error is None and not cancelled and quiescent else None,
            "error": None if cancelled else error, "cancelled": cancelled,
            "elapsed_seconds": elapsed, "peak_sampled_rss_bytes": peak,
            "peak_sampled_solver_rss_bytes": solver_peak, "quiescent": quiescent}


@dataclass
class Job:
    id: str
    request: dict
    created: float = field(default_factory=time.monotonic)
    state: str = "queued"
    progress: dict = field(default_factory=lambda: {"phase": "queued", "message": "Waiting for the proof-search worker.", "model_calls": 0})
    result: dict | None = None
    error: str | None = None
    finished: float | None = None
    cancel: threading.Event = field(default_factory=threading.Event)

    def view(self) -> dict:
        return {"id": self.id, "state": self.state, "progress": self.progress,
                "result": self.result, "error": self.error,
                "elapsed_seconds": (self.finished or time.monotonic()) - self.created}


class Jobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.compute = threading.Lock()
        self.items: dict[str, Job] = {}
        self.threads: list[threading.Thread] = []
        self.active_cancel: threading.Event | None = None
        self.closing = False
        self.blocked: str | None = None

    def _begin(self, cancel: threading.Event) -> None:
        if not self.compute.acquire(blocking=False):
            raise RequestError("Another proof or model request is active. Wait or cancel it first.", 409)
        try:
            with self.lock:
                if self.closing or self.blocked:
                    raise RequestError(self.blocked or "The server is shutting down.", 503)
                self.active_cancel = cancel
        except Exception:
            self.compute.release()
            raise

    def _end(self, outcome: dict | None) -> None:
        with self.lock:
            self.active_cancel = None
            if outcome is None or not outcome.get("quiescent"):
                self.blocked = "Worker cleanup was not confirmed. Restart the local server before more work."
        self.compute.release()

    def replay(self, request: dict) -> dict:
        cancel = threading.Event()
        self._begin(cancel)
        outcome = None
        try:
            outcome = run_worker("replay", request, cancel)
            return outcome
        finally:
            self._end(outcome)

    def start(self, request: dict) -> str:
        job = Job(uuid.uuid4().hex, request)
        self._begin(job.cancel)
        try:
            with self.lock:
                while len(self.items) >= MAX_JOBS:
                    old = next((key for key, value in self.items.items() if value.finished is not None), None)
                    if old is None:
                        raise RequestError("Job history is full.", 429)
                    del self.items[old]
                self.items[job.id] = job
            thread = threading.Thread(target=self._run, args=(job,), daemon=True)
            self.threads = [item for item in self.threads if item.is_alive()]
            self.threads.append(thread)
            thread.start()
            return job.id
        except Exception:
            self._end({"quiescent": True})
            raise

    def _run(self, job: Job) -> None:
        outcome = None
        try:
            with self.lock:
                job.state = "running"
                job.progress = {"phase": "starting", "message": "Starting the bounded proof-search worker.", "model_calls": 0}

            def progress(value):
                with self.lock:
                    job.progress = value

            outcome = run_worker("search", job.request, job.cancel, progress)
            with self.lock:
                job.result, job.error = outcome["result"], outcome["error"]
                if job.result is not None:
                    job.result["execution"] = {key: outcome[key] for key in
                        ("elapsed_seconds", "peak_sampled_rss_bytes", "peak_sampled_solver_rss_bytes", "quiescent")}
                job.state = "cancelled" if outcome["cancelled"] else ("failed" if job.error else "completed")
                job.finished = time.monotonic()
        except Exception as error:
            with self.lock:
                job.error = "Worker cleanup failed: " + " ".join(str(error).split())[:1000]
                job.state, job.finished = "failed", time.monotonic()
        finally:
            self._end(outcome)

    def get(self, identifier: str) -> dict:
        with self.lock:
            if identifier not in self.items:
                raise RequestError("Unknown job; the server may have restarted.", 404)
            return json.loads(worker.json_bytes(self.items[identifier].view()))

    def cancel_job(self, identifier: str) -> dict:
        with self.lock:
            if identifier not in self.items:
                raise RequestError("Unknown job.", 404)
            job = self.items[identifier]
            if job.finished is None:
                job.cancel.set()
            return {"ok": True, "job_id": identifier, "state": job.state}

    def close(self) -> None:
        with self.lock:
            self.closing = True
            if self.active_cancel is not None:
                self.active_cancel.set()
            for job in self.items.values():
                if job.finished is None:
                    job.cancel.set()
        # Includes a synchronous manual replay in an HTTP request thread.
        if self.compute.acquire(timeout=10):
            self.compute.release()
        for thread in self.threads:
            thread.join(timeout=1)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_):
        pass

    def _origin(self):
        if len(self.headers.get_all("Host", [])) != 1:
            raise RequestError("Exactly one local Host header is required.", 403)
        if len(self.headers.get_all("Origin", [])) > 1:
            raise RequestError("Multiple Origin headers are not allowed.", 403)
        validate_origin(self.headers.get("Host"), self.headers.get("Origin"), self.server.server_port)
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise RequestError("Cross-site requests are not allowed.", 403)

    def _send(self, status: int, raw: bytes, content_type: str):
        if len(raw) > 2 * worker.MAX_RESULT_BYTES:
            raise RuntimeError("Response exceeds its byte limit.")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def _json(self, value: dict, status: int = 200):
        self._send(status, worker.json_bytes(value), "application/json; charset=utf-8")

    def _body(self, *, optional=False):
        if self.headers.get("Transfer-Encoding"):
            raise RequestError("Chunked request bodies are not supported.")
        lengths = self.headers.get_all("Content-Length", [])
        if optional and not lengths:
            return {}
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,6}", lengths[0]):
            raise RequestError("One bounded Content-Length header is required.")
        length = int(lengths[0])
        if length > worker.MAX_BODY_BYTES:
            raise RequestError("Request exceeds 64 KiB.", 413)
        if optional and length == 0:
            return {}
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise RequestError("Use application/json.", 415)
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise RequestError("Incomplete request body.")
        return worker.decode_json(raw)

    def do_GET(self):
        try:
            self._origin()
            path = urlsplit(self.path).path
            if path == "/api/status":
                model, vampire = metadata_status(), vampire_status()
                self._json({"ok": True, **worker.kernel_status(), "model": model, "vampire": vampire,
                            "search_modes": search_modes(model, vampire),
                            "computation_active": self.server.jobs.compute.locked(),
                            "limits": worker.LIMITS, "csrf_token": self.server.csrf_token})
            elif re.fullmatch(r"/api/jobs/[0-9a-f]{32}", path):
                self._json({"ok": True, "job": self.server.jobs.get(path.rsplit("/", 1)[1])})
            elif path in STATIC:
                name, mime = STATIC[path]
                fd = os.open(APP / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size > 512 * 1024:
                        raise RequestError("Static file is unavailable.", 404)
                    raw = stream.read(512 * 1024 + 1)
                self._send(200, raw, mime)
            else:
                raise RequestError("Not found.", 404)
        except (ValueError, OSError, RuntimeError) as error:
            self._json({"ok": False, "error": str(error)[:2048]}, getattr(error, "status", 400))

    def do_POST(self):
        try:
            self._origin()
            if len(self.headers.get_all("X-CSRF-Token", [])) != 1:
                raise RequestError("Exactly one CSRF token is required.", 403)
            validate_token(self.headers.get("X-CSRF-Token"), self.server.csrf_token)
            path = urlsplit(self.path).path
            if re.fullmatch(r"/api/jobs/[0-9a-f]{32}/cancel", path):
                value = self._body(optional=True)
                if value:
                    raise RequestError("Cancel does not accept parameters.")
                self._json(self.server.jobs.cancel_job(path.split("/")[3]))
                return
            if path not in ("/api/replay", "/api/search"):
                raise RequestError("Not found.", 404)
            mode = "replay" if path == "/api/replay" else "search"
            value = worker.validate_request(mode, self._body())
            if mode == "search":
                selected = value["search_mode"]
                model = metadata_status() if selected in {"model", "hybrid"} else {"available": False}
                if selected in {"model", "hybrid"} and not model["available"]:
                    raise RequestError(model.get("detail", "The model is not available locally."), 503)
                if selected in {"symbolic", "hybrid"}:
                    vampire = vampire_status()
                    if not vampire["available"]:
                        raise RequestError(vampire.get("detail", "Vampire is not available locally."), 503)
                self._json({"ok": True, "job_id": self.server.jobs.start(value)}, 202)
            else:
                outcome = self.server.jobs.replay(value)
                if outcome["error"]:
                    raise RequestError(outcome["error"], 422)
                if outcome["cancelled"]:
                    raise RequestError("The manual proof check was cancelled.", 409)
                self._json({"ok": True, "result": outcome["result"]})
        except (ValueError, OSError, RuntimeError) as error:
            self._json({"ok": False, "error": str(error)[:2048]}, getattr(error, "status", 400))


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, address):
        if address[0] != "127.0.0.1":
            raise ValueError("The playground binds only to 127.0.0.1.")
        self.csrf_token = secrets.token_urlsafe(32)
        self.jobs = Jobs()
        self.request_slots = threading.BoundedSemaphore(8)
        super().__init__(address, Handler)

    def process_request(self, request, client_address):
        if not self.request_slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.request_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.request_slots.release()

    def server_close(self):
        self.jobs.close()
        super().server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    worker.kernel_status()
    with Server(("127.0.0.1", args.port)) as server:
        print(f"Hydra playground: http://127.0.0.1:{args.port}", flush=True)
        print("Local manual kernel available. Model status is checked without loading weights.", flush=True)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
