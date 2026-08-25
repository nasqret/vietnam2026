"""Safe HTTP, compiler-receipt, artifact, and concurrency proof-service tests.

Every exporter process in this suite is a tiny in-memory fake: no test replays
an Alpha theorem, launches Lean, touches a public release, or reads sibling
private companion source.
"""

from __future__ import annotations

from collections import deque
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
PY_ROOT = ROOT / "peano-lab" / "py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

import serve_lean_strands as service  # noqa: E402


LIVE_URL = "https://live.lean-lang.org/#code=theorem%20example%20%3A%20True%20%3A%3D%20True.intro"


class FakeProcess:
    def __init__(self, lines: list[str], *, code: int = 0, blocking: bool = False) -> None:
        self.stderr = None if blocking else io.StringIO("".join(line + "\n" for line in lines))
        self.pid = 98_765_432
        self.returncode: int | None = None
        self._code = code
        self._blocking = blocking
        self._finished = threading.Event()

    def wait(self, timeout: float | None = None) -> int:
        if self._blocking and not self._finished.wait(timeout):
            raise subprocess.TimeoutExpired("fake-exporter", timeout)
        self.returncode = self._code
        return self._code

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self._code = 143
        self._finished.set()

    def kill(self) -> None:
        self.terminate()


class FakeExporter:
    def __init__(self, *, mode: str = "success", blocking: bool = False) -> None:
        self.mode = mode
        self.blocking = blocking
        self.calls: list[list[str]] = []
        self.processes: list[FakeProcess] = []

    @staticmethod
    def _value(command: list[str], flag: str) -> str:
        return command[command.index(flag) + 1]

    def __call__(self, command: list[str], **options: object) -> FakeProcess:
        self.calls.append(command)
        theorem = command[3]
        edition = self._value(command, "--edition")
        package = Path(self._value(command, "--package-dir"))
        live = Path(self._value(command, "--live-lean-output"))
        package.mkdir(parents=True)
        module = "PeanoLab/Generated/AddComm_test/Strand.lean"
        source = package / module
        source.parent.mkdir(parents=True)
        source.write_text("theorem add_comm : True := by trivial\n", encoding="utf-8")
        notation = package / "PeanoLab/Presentation.lean"
        notation.parent.mkdir(parents=True, exist_ok=True)
        notation.write_text("def readable : Nat := 0\n", encoding="utf-8")
        fallback = self.mode == "fallback"
        entry = {
            "schema": "peano-lab-lean-proof-strand-v1",
            "name": theorem,
            "edition": edition,
            "edition_version": "v19" if edition == "alpha" else "stable",
            "identity_sha256": "a" * 64,
            "node_count": 3,
            "edge_count": 2,
            "translated_node_count": 2 if fallback else 3,
            "fallback_node_count": 1 if fallback else 0,
            "chunk_count": 0,
            "relative_path": module,
        }
        if self.mode == "wrong_theorem":
            entry["name"] = "forged_theorem"
        if self.mode == "escape_manifest":
            entry["relative_path"] = "../../outside.lean"
        catalog = {
            "schema": "peano-lean-proof-strand-package-v1",
            "notation_module": "PeanoLab.Presentation",
            "strand_count": 1,
            "strands": {"AddComm_test": entry},
        }
        (package / "manifest.json").write_text(json.dumps(catalog), encoding="utf-8")
        individual = package / "strand-manifests" / "AddComm_test.json"
        individual.parent.mkdir(parents=True)
        individual.write_text(json.dumps(entry), encoding="utf-8")
        if not fallback and self.mode not in {"failed", "missing_live"}:
            content = "import Lean.Elab.Tactic\ntheorem add_comm : True := by trivial\n"
            live.write_text(content, encoding="utf-8")
            share = None if self.mode == "oversized" else LIVE_URL
            if self.mode == "unsafe_live_url":
                share = "https://live.lean-lang.org.evil.example/#code=steal"
            metadata = {
                "schema": "peano-lab-lean-live-v1",
                "theorem": theorem,
                "edition": edition,
                "source_sha256": sha256(content.encode("utf-8")).hexdigest(),
                "source_bytes": len(content.encode("utf-8")),
                "share_url": share,
                "share_status": "oversized" if share is None else "ready",
                "share_url_bytes": 0 if share is None else len(share),
                "local_source_verified": self.mode != "unverified_live",
                "remote_compilation": "not_run",
            }
            live.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
        progress = json.dumps(
            {
                "kind": "lean_strand_progress",
                "stage": "translate",
                "completed": 2,
                "total": 3,
                "theorem": theorem,
                "message": "translated named theorem",
            }
        )
        lines = [progress]
        if self.mode == "failed":
            lines.append("Unknown Alpha Peano theorem: missing")
        elif self.mode != "unverified":
            lines.append("Independent Lean compilation: PASSED.")
        if self.mode not in {"failed", "unverified"}:
            lines.append(
                json.dumps(
                    {
                        "kind": "lean_strand_progress",
                        "stage": "complete",
                        "completed": 3,
                        "total": 3,
                        "theorem": theorem,
                        "live_url": LIVE_URL,
                    }
                )
            )
        process = FakeProcess(lines, code=2 if self.mode == "failed" else 0, blocking=self.blocking)
        self.processes.append(process)
        return process


def await_terminal(manager: service.JobManager, identifier: str) -> dict[str, object]:
    deadline = time.monotonic() + 3.0
    revision = -1
    while time.monotonic() < deadline:
        snapshot, revision = manager.wait_for_update(identifier, revision, 0.1)
        if snapshot["status"] in service.TERMINAL:
            return snapshot
    raise AssertionError("mocked proof job did not finish within its three-second budget")


@pytest.fixture()
def fake_exporter() -> FakeExporter:
    return FakeExporter()


@pytest.fixture()
def manager(tmp_path: Path, fake_exporter: FakeExporter) -> service.JobManager:
    return service.JobManager(tmp_path / "jobs", popen=fake_exporter)


@pytest.fixture()
def static_root(tmp_path: Path) -> Path:
    root = tmp_path / "public"
    selector = root / "book" / "_static" / "lean-selector"
    selector.mkdir(parents=True)
    (selector / "lean-selector.js").write_text("console.log('selector');\n", encoding="utf-8")
    (selector / "lean-selector.css").write_text(".selector { display: block; }\n", encoding="utf-8")
    for graph in (
        root / "book/_static/pa-proof-explorer/defined/graph.html",
        root / "book/_static/some-new-frontier/graph.html",
    ):
        graph.parent.mkdir(parents=True)
        graph.write_text("<html><head><title>Proof</title></head><body>proof</body></html>", encoding="utf-8")
    (root / "public.txt").write_text("public\n", encoding="utf-8")
    return root


@pytest.fixture()
def http_server(
    manager: service.JobManager,
    static_root: Path,
) -> tuple[str, service.LeanStrandServer]:
    server = service.LeanStrandServer(("127.0.0.1", 0), manager, static_root)
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2.0)


def request(
    base: str,
    path: str,
    *,
    method: str = "GET",
    payload: object | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    selected = dict(headers or {})
    if body is not None and "Content-Type" not in selected:
        selected["Content-Type"] = "application/json"
    item = Request(base + path, data=body, headers=selected, method=method)
    try:
        with urlopen(item, timeout=4.0) as response:
            return response.status, response.read(), dict(response.headers)
    except HTTPError as error:
        return error.code, error.read(), dict(error.headers)


def submit_http(base: str, *, theorem: str = "add_comm", edition: str = "stable") -> dict[str, object]:
    status, content, _ = request(
        base,
        service.API_PREFIX + "/jobs",
        method="POST",
        payload={"theorem": theorem, "edition": edition},
    )
    assert status == 202, content
    return json.loads(content)


def test_service_defaults_are_memory_safe_and_single_worker() -> None:
    limits = service.ServiceLimits()
    assert limits.memory_mib == 1_024
    assert limits.strand_nodes == 256
    assert limits.verify_seconds == 180
    assert limits.retained_jobs == 32


def test_live_sidecar_schema_matches_real_exporter_contract_not_only_mock() -> None:
    from peano_lab.library.lean_proof_strand import LIVE_EXPORT_SCHEMA

    assert service.LIVE_SCHEMA == LIVE_EXPORT_SCHEMA
    assert service.LIVE_SCHEMA == "peano-lab-lean-live-v1"


def test_validated_requests_cannot_expand_operator_resource_caps() -> None:
    limits = service.ServiceLimits()
    selected = service.validate_request({"theorem": "alpha_proof'", "edition": "alpha"}, limits)
    assert selected.theorem == "alpha_proof'"
    assert selected.edition == "alpha"
    assert selected.memory_mib == 1_024
    assert selected.strand_nodes == 256
    with pytest.raises(service.ServiceError, match="max_memory_mib"):
        service.validate_request({"theorem": "ok", "max_memory_mib": 1_025}, limits)
    with pytest.raises(service.ServiceError, match="max_strand_nodes"):
        service.validate_request({"theorem": "ok", "max_strand_nodes": 257}, limits)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"theorem": "_"},
        {"theorem": "../../escape"},
        {"theorem": "bad name"},
        {"theorem": "ok", "edition": "nightly"},
        {"theorem": "ok", "strict_readable": 1},
        {"theorem": "ok", "max_verify_seconds": True},
        {"theorem": "ok", "shell": "rm -rf /"},
    ],
)
def test_request_validation_rejects_untrusted_shape_and_flags(payload: object) -> None:
    with pytest.raises(service.ServiceError):
        service.validate_request(payload, service.ServiceLimits())


@pytest.mark.parametrize(
    "url",
    [
        "http://live.lean-lang.org/#code=theorem",
        "https://live.lean-lang.org.evil.invalid/#code=theorem",
        "https://live.lean-lang.org@evil.invalid/#code=theorem",
        "https://live.lean-lang.org/private#code=theorem",
        "https://live.lean-lang.org/?token=x#code=theorem",
        "https://live.lean-lang.org/#other=theorem",
        "javascript:alert(1)",
        "https://live.lean-lang.org/#code=" + "x" * 8_193,
    ],
)
def test_only_exact_bounded_official_lean_live_host_is_accepted(url: str) -> None:
    assert service.validate_live_url(url) is None


def test_exact_official_lean_live_host_is_accepted() -> None:
    assert service.validate_live_url(LIVE_URL) == LIVE_URL


def test_public_bind_requires_explicit_operator_opt_in() -> None:
    assert service._safe_bind_host("127.0.0.1", public_host=False) == "127.0.0.1"
    assert service._safe_bind_host("localhost", public_host=False) == "localhost"
    with pytest.raises(service.ServiceError, match="public-host"):
        service._safe_bind_host("0.0.0.0", public_host=False)
    assert service._safe_bind_host("0.0.0.0", public_host=True) == "0.0.0.0"


def test_manager_runs_only_the_bounded_verified_export_command(
    manager: service.JobManager,
    fake_exporter: FakeExporter,
) -> None:
    initial = manager.submit({"theorem": "add_comm", "edition": "stable"})
    terminal = await_terminal(manager, initial["job_id"])
    assert terminal["status"] == "completed"
    assert terminal["lean_verified"] is True
    assert terminal["live_status"] == "ready"
    assert terminal["live_compatible"] is True
    assert terminal["standalone_lean"] is True
    assert terminal["companion_required"] is False
    assert terminal["live_url"] == LIVE_URL
    assert terminal["lean_live"]["local_source_verified"] is True
    command = fake_exporter.calls[0]
    assert "--verify" in command
    assert "--progress-json" in command
    assert "--live-lean-output" in command
    assert FakeExporter._value(command, "--max-memory-mib") == "1024"
    assert FakeExporter._value(command, "--max-strand-nodes") == "256"


@pytest.mark.parametrize(
    ("mode", "message"),
    [
        ("failed", "Unknown Alpha Peano theorem"),
        ("unverified", "independent Lean compilation receipt"),
        ("wrong_theorem", "selected theorem"),
        ("unverified_live", "locally checked source"),
    ],
)
def test_success_requires_matching_manifest_and_actual_compiler_receipt(
    tmp_path: Path,
    mode: str,
    message: str,
) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode=mode))
    job = manager.submit({"theorem": "add_comm", "edition": "alpha"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["status"] == "failed"
    assert message in str(terminal["error"])
    with pytest.raises(service.ServiceError, match="completed"):
        manager.lean_download(job["job_id"])


@pytest.mark.parametrize("mode", ["fallback", "missing_live"])
def test_verified_fallback_honestly_requires_a_separate_private_companion(
    tmp_path: Path,
    mode: str,
) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode=mode))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["status"] == "completed"
    assert terminal["lean_verified"] is True
    assert terminal["live_status"] == "fallback_required"
    assert terminal["standalone_lean"] is False
    assert terminal["companion_required"] is True
    module, standalone = manager.lean_download(job["job_id"])
    assert module.name == "Strand.lean"
    assert standalone is False


def test_oversized_live_url_retains_locally_verified_standalone_source(tmp_path: Path) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode="oversized"))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["live_status"] == "oversized"
    assert terminal["live_url"] is None
    selected, independent = manager.lean_download(job["job_id"])
    assert independent is True
    assert selected.name == "live.lean"


def test_untrusted_exporter_cannot_publish_a_spoofed_live_share(tmp_path: Path) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode="unsafe_live_url"))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["status"] == "completed"
    assert terminal["live_url"] is None
    assert terminal["live_status"] == "oversized"


def test_generated_only_zip_is_deterministic_and_never_exports_private_companion(
    manager: service.JobManager,
) -> None:
    job = manager.submit({"theorem": "add_comm"})
    await_terminal(manager, job["job_id"])
    selected = manager.zip_download(job["job_id"])
    assert selected == manager.zip_download(job["job_id"])
    with zipfile.ZipFile(selected) as archive:
        names = set(archive.namelist())
        assert {
            "manifest.json",
            "PeanoLab/Presentation.lean",
            "PeanoLab/Generated/AddComm_test/Strand.lean",
            "strand-manifests/AddComm_test.json",
            "standalone.lean",
            "lean-live.json",
            "README.txt",
        }.issubset(names)
        assert not any(name.startswith("package/") for name in names)
        assert "PeanoLab/Codec.lean" not in names
        assert "PeanoLab.lean" not in names
        assert "lakefile.toml" not in names
        assert "lean-toolchain" not in names
        assert "separately maintained private Lean companion" in archive.read("README.txt").decode()
        assert all(not name.startswith("/") and ".." not in name.split("/") for name in names)
        assert all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist())


def test_zip_rejects_symlinks_inside_generated_package(
    manager: service.JobManager,
    tmp_path: Path,
) -> None:
    job = manager.submit({"theorem": "add_comm"})
    await_terminal(manager, job["job_id"])
    outside = tmp_path / "outside.lean"
    outside.write_text("private", encoding="utf-8")
    package = manager.storage / job["job_id"] / "package"
    (package / "outside.lean").symlink_to(outside)
    with pytest.raises(service.ServiceError, match="symbolic links"):
        manager.zip_download(job["job_id"])


def test_manifest_escape_cannot_be_used_as_a_download_path(tmp_path: Path) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode="escape_manifest"))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["status"] == "completed"
    # Force the certificate-backed download route without changing its selected manifest.
    with manager._changed:
        manager._jobs[job["job_id"]].live_status = "fallback_required"
    with pytest.raises(service.ServiceError, match="escaped"):
        manager.lean_download(job["job_id"])


def test_single_active_worker_refuses_concurrent_jobs_and_cancel_is_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeExporter(blocking=True)
    manager = service.JobManager(tmp_path / "jobs", popen=fake)
    monkeypatch.setattr(
        service.JobManager,
        "_terminate_process",
        staticmethod(lambda process: process.terminate()),
    )
    first = manager.submit({"theorem": "add_comm"})
    with pytest.raises(service.JobBusyError, match="already active"):
        manager.submit({"theorem": "mul_comm"})
    result = manager.cancel(first["job_id"])
    assert result["status"] == "cancelled"
    assert await_terminal(manager, first["job_id"])["status"] == "cancelled"


def test_per_ip_mutations_are_bounded(tmp_path: Path) -> None:
    manager = service.JobManager(
        tmp_path / "jobs",
        limits=service.ServiceLimits(mutations_per_minute=2),
        popen=FakeExporter(),
    )
    manager.check_mutation_rate("127.0.0.1")
    manager.check_mutation_rate("127.0.0.1")
    with pytest.raises(service.JobRateLimitError, match="rate exceeded"):
        manager.check_mutation_rate("127.0.0.1")


def test_expired_terminal_jobs_are_removed_without_touching_other_directories(
    manager: service.JobManager,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("keep me", encoding="utf-8")
    job = manager.submit({"theorem": "add_comm"})
    await_terminal(manager, job["job_id"])
    with manager._changed:
        manager._jobs[job["job_id"]].updated_at = time.time() - 10_000
        manager._cleanup_locked()
    assert outside.read_text(encoding="utf-8") == "keep me"
    with pytest.raises(service.JobNotFoundError):
        manager.snapshot(job["job_id"])


def test_http_health_and_conservative_config(http_server: tuple[str, service.LeanStrandServer]) -> None:
    base, _ = http_server
    status, content, _ = request(base, "/health")
    assert status == 200
    assert json.loads(content)["status"] == "ok"
    status, content, _ = request(base, service.API_PREFIX + "/config")
    selected = json.loads(content)
    assert status == 200
    assert selected["single_worker"] is True
    assert selected["max_concurrent_jobs"] == 1
    assert selected["max_nodes"] == 256
    assert selected["memory_mib"] == 1_024


def test_http_root_redirects_to_small_add_comm_graph(
    http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, _ = http_server

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req: object, fp: object, code: int, msg: str, headers: object, newurl: str) -> None:
            return None

    with pytest.raises(HTTPError) as error:
        build_opener(NoRedirect).open(base + "/", timeout=4)
    assert error.value.code == 302
    assert error.value.headers["Location"].endswith("graph.html?target=PA000F")
    assert "PA00FW" not in error.value.headers["Location"]


@pytest.mark.parametrize(
    "path",
    [
        "/book/_static/pa-proof-explorer/defined/graph.html",
        "/book/_static/some-new-frontier/graph.html",
    ],
)
def test_every_existing_graph_is_enhanced_only_while_served(
    http_server: tuple[str, service.LeanStrandServer],
    static_root: Path,
    path: str,
) -> None:
    base, _ = http_server
    original = (static_root / path.lstrip("/")).read_bytes()
    status, content, headers = request(base, path)
    assert status == 200
    assert b'/book/_static/lean-selector/lean-selector.js' in content
    assert b'/book/_static/lean-selector/lean-selector.css' in content
    assert content.index(b"lean-selector.js") < content.index(b"</head>")
    assert (static_root / path.lstrip("/")).read_bytes() == original
    head_status, head_content, head_headers = request(base, path, method="HEAD")
    assert head_status == 200
    assert head_content == b""
    assert head_headers["Content-Length"] == headers["Content-Length"]


def test_http_full_mocked_job_progress_and_safe_downloads(
    http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, server = http_server
    submitted = submit_http(base)
    terminal = await_terminal(server.job_manager, submitted["job_id"])
    assert terminal["status"] == "completed"
    status, encoded, _ = request(base, str(submitted["status_url"]))
    snapshot = json.loads(encoded)
    assert status == 200
    assert snapshot["lean_verified"] is True
    assert snapshot["progress"]["percent"] == 100
    assert snapshot["live_url"] == LIVE_URL
    status, lean, headers = request(base, snapshot["downloads"]["lean"])
    assert status == 200
    assert lean.startswith(b"import Lean.Elab.Tactic")
    assert 'filename="readable-standalone.lean"' in headers["Content-Disposition"]
    status, bundle, headers = request(base, snapshot["downloads"]["zip"])
    assert status == 200
    assert headers["Content-Type"] == "application/zip"
    assert 'filename="verified-lean-proof.zip"' in headers["Content-Disposition"]
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        assert "README.txt" in archive.namelist()
        assert "PeanoLab/Codec.lean" not in archive.namelist()


def test_http_rejects_cross_origin_mutation_and_host_spoofing(
    http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, _ = http_server
    status, _, _ = request(
        base,
        service.API_PREFIX + "/jobs",
        method="POST",
        payload={"theorem": "add_comm"},
        headers={"Origin": "https://evil.invalid"},
    )
    assert status == 403
    status, _, _ = request(base, "/health", headers={"Host": "evil.invalid"})
    assert status == 421


@pytest.mark.parametrize(
    "path",
    [
        "/.git/config",
        "/book/%2e%2e/private.txt",
        "/.env",
        "/service.py",
        "/config.json",
        "/secret.key",
    ],
)
def test_http_blocks_private_paths_python_configs_and_traversal(
    http_server: tuple[str, service.LeanStrandServer],
    path: str,
) -> None:
    base, _ = http_server
    assert request(base, path)[0] == 403


def test_http_blocks_static_symlink_escape(
    http_server: tuple[str, service.LeanStrandServer],
    static_root: Path,
    tmp_path: Path,
) -> None:
    base, _ = http_server
    outside = tmp_path / "private.txt"
    outside.write_text("private", encoding="utf-8")
    (static_root / "escape.txt").symlink_to(outside)
    assert request(base, "/escape.txt")[0] == 403


def test_http_bad_inputs_unknown_jobs_and_formats_fail_closed(
    http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, _ = http_server
    status, _, _ = request(
        base,
        service.API_PREFIX + "/jobs",
        method="POST",
        payload={"theorem": "../../no"},
    )
    assert status == 400
    assert request(base, service.API_PREFIX + "/jobs/not-a-token")[0] == 404
    submitted = submit_http(base)
    await_terminal(http_server[1].job_manager, submitted["job_id"])
    assert request(base, str(submitted["status_url"]) + "/download?format=exe")[0] == 409


def test_http_busy_job_and_cancellation(
    tmp_path: Path,
    static_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeExporter(blocking=True)
    manager = service.JobManager(tmp_path / "blocking-jobs", popen=fake)
    monkeypatch.setattr(
        service.JobManager,
        "_terminate_process",
        staticmethod(lambda process: process.terminate()),
    )
    server = service.LeanStrandServer(("127.0.0.1", 0), manager, static_root)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        first = submit_http(base)
        status, _, _ = request(
            base,
            service.API_PREFIX + "/jobs",
            method="POST",
            payload={"theorem": "mul_comm"},
        )
        assert status == 409
        status, encoded, _ = request(base, str(first["status_url"]), method="DELETE")
        assert status == 200
        assert json.loads(encoded)["status"] == "cancelled"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_mutation_rate_limit_returns_429(
    http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, server = http_server
    with server.job_manager._lock:
        server.job_manager._mutation_windows["127.0.0.1"] = deque(
            [time.monotonic()] * server.job_manager.limits.mutations_per_minute
        )
    status, _, _ = request(
        base,
        service.API_PREFIX + "/jobs",
        method="POST",
        payload={"theorem": "add_comm"},
    )
    assert status == 429


def test_ephemeral_port_and_safe_override_are_supported(tmp_path: Path) -> None:
    public = tmp_path / "public"
    public.mkdir()
    server = service.build_server(
        [
            "--port", "0",
            "--directory", str(public),
            "--storage", str(tmp_path / "jobs"),
            "--max-strand-nodes", "128",
            "--max-memory-mib", "512",
        ]
    )
    try:
        assert server.server_port > 0
        assert server.job_manager.limits.strand_nodes == 128
        assert server.job_manager.limits.memory_mib == 512
    finally:
        server.server_close()
