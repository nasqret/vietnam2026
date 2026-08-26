"""Adversarial tests for the real theorem-browser acceptance checker."""

from __future__ import annotations

import importlib.util
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.parse import quote
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts" / "check_lean_browser.py"
SPEC = importlib.util.spec_from_file_location("hydra_lean_browser_check", SOURCE)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECK
SPEC.loader.exec_module(CHECK)


def _archive(*, theorem: str = "add_comm", omit: str | None = None, extra: str | None = None) -> bytes:
    output = io.BytesIO()
    catalog = {
        "schema": "peano-lean-proof-strand-package-v1",
        "strands": {"fixture": {"name": theorem}},
    }
    files = {
        "PeanoLab/Presentation.lean": b"import Lean\n",
        "PeanoLab/Generated/AddComm_fixture/Strand.lean": b"import PeanoLab.Codec\n",
        "manifest.json": json.dumps(catalog).encode("utf-8"),
        "README.txt": b"lake build\n",
    }
    if omit is not None:
        files.pop(omit)
    if extra is not None:
        files[extra] = b"not safe\n"
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


def _live(source: str) -> str:
    return "https://live.lean-lang.org/#code=" + quote(source, safe="")


def test_accepts_loopback_http_and_public_https() -> None:
    assert CHECK._base_url("http://127.0.0.1:8787/") == "http://127.0.0.1:8787"
    assert CHECK._base_url("https://proof.example") == "https://proof.example"


@pytest.fixture()
def fresh_tls_cache():
    CHECK._verified_tls_context.cache_clear()
    try:
        yield
    finally:
        CHECK._verified_tls_context.cache_clear()


def unavailable_default_ca_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    monkeypatch.setattr(
        CHECK.ssl,
        "get_default_verify_paths",
        lambda: SimpleNamespace(
            cafile=None,
            capath=None,
            openssl_cafile_env="SSL_CERT_FILE",
            openssl_capath_env="SSL_CERT_DIR",
        ),
    )


def test_verified_certifi_bundle_is_used_only_when_system_trust_is_absent(
    fresh_tls_cache,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unavailable_default_ca_store(monkeypatch)
    bundle = tmp_path / "reviewed-certifi.pem"
    bundle.write_text("fixture", encoding="utf-8")
    trusted = SimpleNamespace(
        verify_mode=CHECK.ssl.CERT_REQUIRED,
        check_hostname=True,
        cert_store_stats=lambda: {"x509_ca": 146},
    )
    calls: list[str | None] = []

    def create(*, cafile: str | None = None):
        calls.append(cafile)
        if cafile is None:
            return SimpleNamespace(cert_store_stats=lambda: {"x509_ca": 0})
        return trusted

    monkeypatch.setattr(CHECK.ssl, "create_default_context", create)
    monkeypatch.setitem(sys.modules, "certifi", SimpleNamespace(where=lambda: str(bundle)))

    assert CHECK._verified_tls_context() is trusted
    assert CHECK._verified_tls_context() is trusted
    assert calls == [None, str(bundle)]


def test_installed_system_ca_store_remains_authoritative(
    fresh_tls_cache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CHECK.ssl,
        "get_default_verify_paths",
        lambda: SimpleNamespace(
            cafile="/etc/ssl/certs/ca-certificates.crt",
            capath=None,
            openssl_cafile_env="SSL_CERT_FILE",
            openssl_capath_env="SSL_CERT_DIR",
        ),
    )
    monkeypatch.setattr(
        CHECK.ssl,
        "create_default_context",
        lambda **_options: pytest.fail("installed system TLS roots must not be overridden"),
    )

    assert CHECK._verified_tls_context() is None


@pytest.mark.parametrize("variable", ["SSL_CERT_FILE", "SSL_CERT_DIR"])
def test_explicit_operator_ca_configuration_is_never_overridden(
    fresh_tls_cache,
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
) -> None:
    unavailable_default_ca_store(monkeypatch)
    monkeypatch.setenv(variable, "/operator/selected/trust-store")
    monkeypatch.setattr(
        CHECK.ssl,
        "create_default_context",
        lambda **_options: pytest.fail("explicit operator TLS roots must not be overridden"),
    )

    assert CHECK._verified_tls_context() is None


@pytest.mark.parametrize(
    ("mode", "hostname", "count"),
    [
        (CHECK.ssl.CERT_NONE, False, 146),
        (CHECK.ssl.CERT_REQUIRED, False, 146),
        (CHECK.ssl.CERT_REQUIRED, True, 0),
    ],
)
def test_certifi_fallback_never_disables_verified_hostname_or_ca_checks(
    fresh_tls_cache,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: int,
    hostname: bool,
    count: int,
) -> None:
    unavailable_default_ca_store(monkeypatch)
    bundle = tmp_path / "reviewed-certifi.pem"
    bundle.write_text("fixture", encoding="utf-8")

    def create(*, cafile: str | None = None):
        return SimpleNamespace(
            verify_mode=mode,
            check_hostname=hostname,
            cert_store_stats=lambda: {"x509_ca": 0 if cafile is None else count},
        )

    monkeypatch.setattr(CHECK.ssl, "create_default_context", create)
    monkeypatch.setitem(sys.modules, "certifi", SimpleNamespace(where=lambda: str(bundle)))

    assert CHECK._verified_tls_context() is None


def test_missing_certifi_does_not_weaken_default_https_verification(
    fresh_tls_cache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unavailable_default_ca_store(monkeypatch)
    monkeypatch.setattr(
        CHECK.ssl,
        "create_default_context",
        lambda: SimpleNamespace(cert_store_stats=lambda: {"x509_ca": 0}),
    )
    monkeypatch.setitem(sys.modules, "certifi", None)

    assert CHECK._verified_tls_context() is None


@pytest.mark.parametrize("url", ["http://127.0.0.1:8787/config", "https://proof.example/config"])
def test_verified_ca_fallback_is_applied_only_to_public_https_requests(
    fresh_tls_cache,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    selected = object()
    observed: list[dict[str, object]] = []
    monkeypatch.setattr(CHECK, "_verified_tls_context", lambda: selected)

    class Response:
        headers = {"Content-Length": "2"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        @staticmethod
        def read(_maximum: int) -> bytes:
            return b"{}"

    def open_url(_request, **options):
        observed.append(options)
        return Response()

    monkeypatch.setattr(CHECK, "urlopen", open_url)

    assert CHECK._request(url, maximum=20) == b"{}"
    assert observed[0]["timeout"] == 20
    if url.startswith("https:"):
        assert observed[0]["context"] is selected
    else:
        assert "context" not in observed[0]


@pytest.mark.parametrize(
    ("origin", "expected"),
    (
        ("http://127.0.0.1:8787", ("127.0.0.1", 8787)),
        ("http://localhost:8890", ("localhost", 8890)),
        ("https://proof.example", None),
        ("https://127.0.0.1:8787", None),
        ("http://[::1]:8787", None),
    ),
)
def test_automatic_service_startup_is_limited_to_local_http(
    origin: str,
    expected: tuple[str, int] | None,
) -> None:
    assert CHECK._local_service_target(origin) == expected


def test_temporary_service_uses_only_the_reviewed_local_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    class FakeProcess:
        stopped = False

        def poll(self) -> int | None:
            return 0 if self.stopped else None

        def terminate(self) -> None:
            self.stopped = True

        def wait(self, *, timeout: int) -> int:
            assert timeout == 5
            return 0

    process = FakeProcess()

    def launch(command: list[str], **options: object) -> FakeProcess:
        calls.append((command, options))
        return process

    monkeypatch.setattr(CHECK.subprocess, "Popen", launch)
    monkeypatch.setattr(
        CHECK,
        "_request",
        lambda _url, **_options: b'{"status":"ok"}',
    )

    managed, log = CHECK._start_local_service("http://127.0.0.1:8787")
    assert managed is process
    assert calls[0][0][0] == sys.executable
    assert calls[0][0][-4:] == ["--host", "127.0.0.1", "--port", "8787"]
    assert "--public-host" not in calls[0][0]

    CHECK._stop_local_service(managed, log)
    assert process.stopped
    assert log.closed


def test_unavailable_local_service_is_started_and_cleaned_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = b"theorem checked : True := by trivial\n"
    identifier = "a" * 32
    job = {
        "job_id": identifier,
        "status": "completed",
        "stage": "complete",
        "completed": 3,
        "total": 3,
        "lean_verified": True,
        "manifest": {
            "name": "add_comm",
            "edition": "stable",
            "node_count": 3,
            "fallback_node_count": 0,
        },
        "downloads": {
            "lean": f"/api/lean-strands/jobs/{identifier}/download?format=lean",
            "zip": f"/api/lean-strands/jobs/{identifier}/download?format=zip",
        },
        "live_url": _live(source.decode("utf-8")),
        "lean_live": {
            "local_source_verified": True,
            "self_contained": True,
            "core_imports": [],
            "external_import_count": 0,
            "source_sha256": sha256(source).hexdigest(),
            "share_encoding": "code",
        },
    }
    attempts = 0

    class FakeProcess:
        stopped = False

        def poll(self) -> int | None:
            return 0 if self.stopped else None

        def terminate(self) -> None:
            self.stopped = True

        def wait(self, *, timeout: int) -> int:
            assert timeout == 5
            return 0

    process = FakeProcess()
    log = io.BytesIO()

    def request(url: str, **_options: object) -> bytes:
        nonlocal attempts
        if url.endswith("/config"):
            attempts += 1
            if attempts == 1:
                raise CHECK.BrowserCheckError("could not reach the theorem browser: refused")
            return json.dumps(
                {"single_worker": True, "independent_lean_verification": True}
            ).encode("utf-8")
        if "graph.html" in url:
            return b"lean-selector.js lean-selector.css"
        if url.endswith("lean-selector.js"):
            return b"PeanoLeanSelector"
        if "format=lean" in url:
            return source
        if "format=zip" in url:
            return _archive()
        return json.dumps(job).encode("utf-8")

    monkeypatch.setattr(CHECK, "_request", request)
    monkeypatch.setattr(CHECK, "_start_local_service", lambda _base: (process, log))

    assert CHECK.main([]) == 0
    assert attempts == 2
    assert process.stopped
    assert log.closed


@pytest.mark.parametrize(
    ("backend", "site", "cross_origin"),
    [
        ("https://faculty.example.test", "https://faculty.example.test", False),
        ("https://lean.example.test", "https://faculty.example.test", True),
    ],
)
def test_public_checker_uses_deployed_graph_and_exact_backend_origin(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    site: str,
    cross_origin: bool,
) -> None:
    source = b"theorem checked : True := by trivial\n"
    identifier = "b" * 32
    job = {
        "job_id": identifier,
        "status": "completed",
        "stage": "complete",
        "completed": 3,
        "total": 3,
        "lean_verified": True,
        "manifest": {
            "name": "add_comm",
            "edition": "stable",
            "node_count": 3,
            "fallback_node_count": 0,
        },
        "downloads": {
            "lean": f"/api/lean-strands/jobs/{identifier}/download?format=lean",
            "zip": f"/api/lean-strands/jobs/{identifier}/download?format=zip",
        },
        "live_url": _live(source.decode("utf-8")),
        "lean_live": {
            "local_source_verified": True,
            "self_contained": True,
            "core_imports": [],
            "external_import_count": 0,
            "source_sha256": sha256(source).hexdigest(),
            "share_encoding": "code",
        },
    }
    calls: list[tuple[str, dict[str, object]]] = []

    def response(url: str, **options: object) -> bytes:
        calls.append((url, options))
        if url.endswith("/config"):
            return json.dumps(
                {
                    "single_worker": True,
                    "independent_lean_verification": True,
                    "allowed_origins": [site] if cross_origin else [],
                }
            ).encode("utf-8")
        if options.get("method") == "OPTIONS":
            return b""
        if "graph.html" in url:
            return b"lean-selector.js lean-selector.css"
        if url.endswith("lean-selector.js"):
            return b"PeanoLeanSelector"
        if "format=lean" in url:
            return source
        if "format=zip" in url:
            return _archive()
        return json.dumps(job).encode("utf-8")

    monkeypatch.setattr(CHECK, "_request", response)

    assert CHECK.main(["--base-url", backend, "--site-url", site]) == 0
    assert any(
        url == site + "/proofs/quadratic-reciprocity/explorer/graph.html?target=PA000G"
        for url, _ in calls
    )
    assert any(url == site + "/proofs/assets/lean-selector.js" for url, _ in calls)
    proof_calls = [
        (url, options)
        for url, options in calls
        if "/api/lean-strands/" in url
    ]
    assert proof_calls
    assert all(url.startswith(backend + "/api/lean-strands/") for url, _ in proof_calls)
    if cross_origin:
        assert all(options.get("origin") == site for _, options in proof_calls)
        assert all(options.get("require_cors") is True for _, options in proof_calls)
        assert any(options.get("method") == "OPTIONS" for _, options in proof_calls)
    else:
        assert all(options.get("origin") is None for _, options in proof_calls)


def test_public_checker_rejects_unapproved_external_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CHECK,
        "_request",
        lambda _url, **_options: json.dumps(
            {
                "single_worker": True,
                "independent_lean_verification": True,
                "allowed_origins": ["https://other.example.test"],
            }
        ).encode("utf-8"),
    )

    assert CHECK.main(
        ["--base-url", "https://lean.example.test", "--site-url", "https://faculty.example.test"]
    ) == 1


@pytest.mark.parametrize(
    "option",
    [
        ["--graph-path", "https://evil.example.test/private"],
        ["--selector-path", "https://evil.example.test/private.js"],
    ],
)
def test_public_checker_rejects_cross_origin_browser_asset_paths(
    monkeypatch: pytest.MonkeyPatch,
    option: list[str],
) -> None:
    def response(url: str, **_options: object) -> bytes:
        if url.endswith("/config"):
            return b'{"single_worker":true,"independent_lean_verification":true}'
        if "graph.html" in url:
            return b"lean-selector.js lean-selector.css"
        pytest.fail("checker fetched a cross-origin public browser asset")

    monkeypatch.setattr(CHECK, "_request", response)

    assert CHECK.main(
        [
            "--base-url", "https://faculty.example.test",
            "--site-url", "https://faculty.example.test",
        ]
        + option
    ) == 1


def test_require_running_does_not_start_an_absent_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(_url: str, **_options: object) -> bytes:
        raise CHECK.BrowserCheckError("could not reach the theorem browser: refused")

    def forbidden(_base: str) -> None:
        pytest.fail("strict checking unexpectedly started a server")

    monkeypatch.setattr(CHECK, "_request", unavailable)
    monkeypatch.setattr(CHECK, "_start_local_service", forbidden)

    assert CHECK.main(["--require-running"]) == 1


@pytest.mark.parametrize(
    "value",
    (
        "http://proof.example",
        "https://user:password@proof.example",
        "https://proof.example/path",
        "https://proof.example?token=secret",
    ),
)
def test_rejects_unsafe_browser_origin(value: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError):
        CHECK._base_url(value)


def test_rejects_cross_origin_download() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="cross-origin"):
        CHECK._same_origin("http://127.0.0.1:8787", "https://invalid.example/leak.lean")


def test_live_share_contains_the_exact_standalone_source() -> None:
    source = "theorem checked : True := by trivial\n"
    CHECK._check_live_url(_live(source), source.encode("utf-8"))


def test_compressed_live_share_contains_the_exact_standalone_source() -> None:
    source = "theorem checked : True := by trivial\n"
    payload = "C4Cwpg9gTmC2AEBjciDWYAm8Bc8AqUArmDgLzwBGAnvMFAJYBu9AhgDYBQQA"

    CHECK._check_live_url(
        "https://live.lean-lang.org/#codez=" + payload,
        source.encode("utf-8"),
    )


def test_campaign_live_share_preserves_a_large_exact_standalone_source() -> None:
    from peano_lab.library.lean_proof_strand import compress_lean_live_codez

    source = "theorem checked : True := by trivial\n" + "".join(
        "-- " + sha256(str(index).encode("ascii")).hexdigest() + "\n"
        for index in range(800)
    )
    payload = quote(compress_lean_live_codez(source), safe="")
    url = "https://live.lean-lang.org/#codez=" + payload

    assert len(source.encode("utf-8")) > 50 * 1024
    assert len(url.encode("utf-8")) > 33 * 1024
    CHECK._check_live_url(url, source.encode("utf-8"))


@pytest.mark.parametrize(
    ("source", "payload"),
    (
        ("nnnnnnnnnnnnnnnn13", "HY1%2FAjAzEA"),
        ("😀~", "rwbgA9h%2BQ"),
    ),
)
def test_compressed_live_share_decodes_official_escaped_base64(
    source: str,
    payload: str,
) -> None:
    CHECK._check_live_url(
        "https://live.lean-lang.org/#codez=" + payload,
        source.encode("utf-8"),
    )


@pytest.mark.parametrize(
    "fragment",
    (
        "codez=",
        "codez=not%20canonical",
        "codez=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "codez=HY1-AjAzEA",
        "codez=HY1/AjAzEA",
        "codez=HY1%2fAjAzEA",
        "codez=HY1%252FAjAzEA",
        "codez=rwbgA9h+Q",
        "codez=rwbgA9h%2bQ",
        "codez=rwbgA9h%2BQ%3D",
        "url=https%3A%2F%2Fprivate.invalid%2Fsecret.lean",
    ),
)
def test_compressed_live_share_rejects_invalid_or_hosted_payload(fragment: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="invalid source share"):
        CHECK._check_live_url(
            "https://live.lean-lang.org/#" + fragment,
            b"theorem checked : True := True.intro\n",
        )


def test_compressed_live_share_rejects_a_changed_source() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="exact downloaded proof|invalid source share"):
        CHECK._check_live_url(
            "https://live.lean-lang.org/#codez=BYUwNmD2Q",
            b"hellx",
        )


def test_live_share_rejects_a_changed_source() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="exact downloaded proof"):
        CHECK._check_live_url(_live("import Lean\n"), b"import Lean\n-- changed\n")


@pytest.mark.parametrize(
    "source",
    (
        "import Lean.Elab.Tactic\ntheorem checked : True := by trivial\n",
        "import Mathlib\ntheorem checked : True := by trivial\n",
        "import Lean\ntheorem unchecked : True := by sorry\n",
        "import Lean\naxiom unchecked : True\n",
    ),
)
def test_live_share_rejects_unavailable_or_unproved_source(source: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="unavailable or unproved"):
        CHECK._check_live_url(_live(source), source.encode("utf-8"))


def test_generated_lean_package_archive_is_complete() -> None:
    count, size = CHECK._check_archive(_archive(), "add_comm")
    assert count == 4
    assert size > 0


@pytest.mark.parametrize("missing", ("PeanoLab/Presentation.lean", "README.txt"))
def test_archive_rejects_missing_generated_package_file(missing: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="incomplete"):
        CHECK._check_archive(_archive(omit=missing), "add_comm")


@pytest.mark.parametrize("private", ("PeanoLab/Codec.lean", "lakefile.toml", "lean-toolchain"))
def test_archive_does_not_export_the_separate_private_companion(private: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="separate companion source"):
        CHECK._check_archive(_archive(extra=private), "add_comm")


@pytest.mark.parametrize("unsafe", ("../escape.lean", "/absolute.lean", "bad\\escape.lean"))
def test_archive_rejects_path_traversal(unsafe: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="unsafe entry"):
        CHECK._check_archive(_archive(extra=unsafe), "add_comm")


def test_archive_rejects_a_different_selected_theorem() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="selected theorem"):
        CHECK._check_archive(_archive(theorem="mul_comm"), "add_comm")
