"""Safe HTTP, compiler-receipt, artifact, and concurrency proof-service tests.

Every exporter process in this suite is a tiny in-memory fake: no test replays
an Alpha theorem, launches Lean, rewrites a public release, or reads sibling
private companion source. Actual publication checks are read-only and do not
create a listening server.
"""

from __future__ import annotations

from collections import deque
from functools import lru_cache
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import quote
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


LIVE_SOURCE = "theorem add_comm : True := by trivial\n"
LIVE_URL = "https://live.lean-lang.org/#code=" + quote(LIVE_SOURCE, safe="")
V27_FIRST_CATALOG_SHA256 = "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
CURRENT_PUBLICATIONS = {
    "constructive-lower-layer-explorer": {
        "schema": "peano-lab-constructive-lower-layer-explorer-v1-manifest",
        "first": "v28",
        "slug": "arithmetic-foundations",
        "tag": "AF0001",
        "slugs": {"arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers"},
    },
    "constructive-second-wave-explorer-v28": {
        "schema": "peano-lab-constructive-second-wave-explorer-v1-manifest",
        "first": "v27",
        "slug": "integer-linear-algebra",
        "tag": "DL0028",
        "slugs": {
            "integer-linear-algebra", "hensel-lifting", "generalized-crt",
            "multinomial-kummer", "prime-count-chebyshev", "cornacchia", "cauchy-davenport",
        },
    },
}


def install_test_release(root: Path, *, version: str = "v28") -> tuple[str, str]:
    """A tiny, consistently hashed owned release for isolated HTTP tests."""

    identity = "c" * 64
    count = 2764
    catalog = root / "artifacts/peano-library/alpha" / f"catalog-{version}.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_bytes(json.dumps({
        "schema": f"peano-library-alpha-snapshot-{version}",
        "theorem_count": count, "checked_use_count": count,
    }, sort_keys=True).encode("utf-8"))
    digest = sha256(catalog.read_bytes()).hexdigest()
    channel = root / "artifacts/peano-library" / f"channels-{version}.json"
    channel.write_text(json.dumps({
        "schema": f"peano-library-channels-{version}",
        "channels": {"alpha": {
            "artifact_path": f"artifacts/peano-library/alpha/catalog-{version}.json",
            "artifact_sha256": digest, "edition_identity_sha256": identity,
            "theorem_count": count, "checked_use_count": count,
        }},
    }), encoding="utf-8")
    campaign = root / "book/_static/constructive-grand-campaign/campaign.json"
    campaign.parent.mkdir(parents=True, exist_ok=True)
    campaign.write_text(json.dumps({
        "schema": "constructive-grand-campaign-v1",
        "meta": {"current_alpha_version": version, "current_alpha_checked_use_count": count},
        "ambitious_boundaries": {f"alpha_{version}_edition": {
            "role": "current_immutable_release", "catalog_sha256": digest,
            "identity_sha256": identity, "theorem_count": count, "checked_use_count": count,
        }},
    }), encoding="utf-8")
    return digest, identity


def non_listening_review_server(root: Path) -> service.LeanStrandServer:
    """Use the real file/owner/hash review without sockets or proof workers."""

    server = object.__new__(service.LeanStrandServer)
    server.static_directory = root.resolve()
    server.job_manager = SimpleNamespace(limits=service.ServiceLimits())
    server._constructive_authority_lock = threading.RLock()
    server._constructive_release_cache = {}
    server._constructive_manifest_cache = {}
    return server


@lru_cache(maxsize=1)
def campaign_source() -> str:
    return LIVE_SOURCE + "".join(
        "-- " + sha256(str(index).encode("ascii")).hexdigest() + "\n"
        for index in range(3_500)
    )


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
        fallback = self.mode in {"fallback", "mixed_live"}
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
        if (not fallback or self.mode == "mixed_live") and self.mode not in {"failed", "missing_live"}:
            content = campaign_source() if self.mode == "campaign_codez" else LIVE_SOURCE
            if self.mode == "private_import":
                content = "import PeanoLab.Codec\ntheorem x : True := by trivial\n"
            elif self.mode == "mathlib_import":
                content = "import Mathlib\ntheorem x : True := by trivial\n"
            elif self.mode == "core_import":
                content = "import Lean.Elab.Tactic\ntheorem x : True := by trivial\n"
            elif self.mode == "sorry_proof":
                content = "theorem x : True := by sorry\n"
            elif self.mode == "new_axiom":
                content = "axiom invented : False\n"
            live.write_text(content, encoding="utf-8")
            share = (
                None
                if self.mode == "oversized"
                else "https://live.lean-lang.org/#code=" + quote(content, safe="")
            )
            encoding = "code"
            if self.mode in {"codez", "campaign_codez", "codez_forged", "codez_bomb"}:
                from peano_lab.library.lean_proof_strand import compress_lean_live_codez

                compressed_source = content
                if self.mode == "codez_forged":
                    compressed_source = "theorem forged : True := by trivial\n"
                elif self.mode == "codez_bomb":
                    compressed_source = "x" * 5_000
                share = (
                    "https://live.lean-lang.org/#codez="
                    + quote(compress_lean_live_codez(compressed_source), safe="")
                )
                encoding = "codez"
            if self.mode == "forged_live_source":
                share = "https://live.lean-lang.org/#code=" + quote("theorem forged : True := by trivial", safe="")
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
                "share_encoding": None if share is None else encoding,
                "share_url_bytes": 0 if share is None else len(share),
                "fallback_node_count": 1 if self.mode == "sidecar_fallback" else 0,
                "local_source_verified": self.mode != "unverified_live",
                "self_contained": self.mode != "not_self_contained",
                "core_imports": (
                    ["Mathlib"]
                    if self.mode == "declared_external_import"
                    else []
                ),
                "external_import_count": 1 if self.mode == "external_import_count" else 0,
                "remote_compilation": "not_run",
            }
            if self.mode == "wrong_encoding":
                metadata["share_encoding"] = "codez"
            elif self.mode == "unsupported_encoding":
                metadata["share_encoding"] = "url"
            elif self.mode == "wrong_share_status":
                metadata["share_status"] = "oversized"
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
    version = "v24"
    identity = "b" * 64
    catalog = root / "artifacts" / "peano-library" / "alpha" / f"catalog-{version}.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_bytes(
        json.dumps(
            {
                "schema": f"peano-library-alpha-snapshot-{version}",
                "theorem_count": 1,
                "checked_use_count": 1,
            },
            sort_keys=True,
        ).encode("utf-8")
    )
    digest = sha256(catalog.read_bytes()).hexdigest()
    channel = root / "artifacts" / "peano-library" / f"channels-{version}.json"
    channel.write_text(
        json.dumps(
            {
                "schema": f"peano-library-channels-{version}",
                "channels": {
                    "alpha": {
                        "artifact_path": (
                            f"artifacts/peano-library/alpha/catalog-{version}.json"
                        ),
                        "artifact_sha256": digest,
                        "edition_identity_sha256": identity,
                        "theorem_count": 1,
                        "checked_use_count": 1,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    campaign = root / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
    campaign.parent.mkdir(parents=True)
    campaign.write_text(
        json.dumps(
            {
                "schema": "constructive-grand-campaign-v1",
                "meta": {
                    "current_alpha_version": version,
                    "current_alpha_checked_use_count": 1,
                },
                "ambitious_boundaries": {
                    f"alpha_{version}_edition": {
                        "role": "current_immutable_release",
                        "catalog_sha256": digest,
                        "identity_sha256": identity,
                        "theorem_count": 1,
                        "checked_use_count": 1,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    reviewed = {
        "constructive-next-layer-explorer": "continued-fractions",
        "constructive-advanced-layer-explorer": "binary-exponentiation",
        "constructive-transport-layer-explorer": "euclidean-gcd",
        "constructive-milestone-closure-explorer": "prime-routes",
        "constructive-research-layer-explorer": "polynomial-hensel",
        "constructive-breakthrough-layer-explorer": "matrix-cofactor-expansion",
        "constructive-verified-future-explorer": "next-checked-frontier",
    }
    for segment, slug in reviewed.items():
        directory = root / "book" / "_static" / segment
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_text(
            json.dumps(
                {
                    "schema": f"peano-lab-{segment}-v1-manifest",
                    "alpha_edition_version": version,
                    "catalog_sha256": digest,
                    "edition_identity_sha256": identity,
                    "families": [{"slug": slug, "theorem_count": 1}],
                }
            ),
            encoding="utf-8",
        )
    for graph in (
        root / "book/_static/pa-proof-explorer/defined/graph.html",
        root / "book/_static/some-new-frontier/graph.html",
        root / "book/_static/constructive-next-layer-explorer/continued-fractions/explorer/defined/tag/CF0002.html",
        root / "book/_static/constructive-advanced-layer-explorer/binary-exponentiation/explorer/defined/tag/AL0002.html",
        root / "book/_static/constructive-transport-layer-explorer/euclidean-gcd/explorer/defined/tag/TL0002.html",
        root / "book/_static/constructive-milestone-closure-explorer/prime-routes/explorer/defined/tag/MC0002.html",
        root / "book/_static/constructive-research-layer-explorer/polynomial-hensel/explorer/defined/tag/RL0002.html",
        root / "book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/defined/tag/CE0002.html",
        root / "book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/tag/CE0002.html",
        root / "book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/defined/graph.html",
        root / "book/_static/constructive-verified-future-explorer/next-checked-frontier/explorer/defined/tag/FU0002.html",
        root / "book/_static/unreviewed-campaign/defined/tag/FAKE0002.html",
    ):
        graph.parent.mkdir(parents=True, exist_ok=True)
        graph.write_text("<html><head><title>Proof</title></head><body>proof</body></html>", encoding="utf-8")
    (root / "public.txt").write_text("public\n", encoding="utf-8")
    return root


@pytest.fixture()
def v28_static_root(static_root: Path) -> Path:
    digest, identity = install_test_release(static_root)
    publications = dict(CURRENT_PUBLICATIONS)
    publications["constructive-second-wave-explorer"] = {
        **CURRENT_PUBLICATIONS["constructive-second-wave-explorer-v28"],
    }
    for segment, publication in publications.items():
        historical = segment == "constructive-second-wave-explorer"
        directory = static_root / "book/_static" / segment
        directory.mkdir(parents=True)
        first = publication["first"]
        (directory / "manifest.json").write_text(json.dumps({
            "schema": publication["schema"],
            "alpha_edition_version": "v27" if historical else "v28",
            "catalog_sha256": V27_FIRST_CATALOG_SHA256 if historical else digest,
            "edition_identity_sha256": "d" * 64 if historical else identity,
            "alpha_first_enrolled_version": first,
            "first_enrollment_catalog_sha256": digest if first == "v28" else V27_FIRST_CATALOG_SHA256,
            "families": [{"slug": publication["slug"], "theorem_count": 1}],
        }), encoding="utf-8")
        for suffix in (
            "explorer/graph.html", "explorer/defined/graph.html",
            f"explorer/tag/{publication['tag']}.html",
            f"explorer/defined/tag/{publication['tag']}.html",
        ):
            page = directory / publication["slug"] / suffix
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("<html><head><title>Proof</title></head><body>proof</body></html>", encoding="utf-8")
    return static_root


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


@pytest.fixture()
def public_http_server(
    manager: service.JobManager,
    static_root: Path,
) -> tuple[str, service.LeanStrandServer]:
    server = service.LeanStrandServer(
        ("127.0.0.1", 0),
        manager,
        static_root,
        public_origin="https://lean.example.test",
        allowed_origins=("https://faculty.example.test",),
    )
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
    assert limits.strand_nodes == 1_024
    assert limits.verify_seconds == 180
    assert limits.retained_jobs == 32
    assert limits.live_url_bytes == 512 * 1024
    assert limits.live_source_bytes == 1024 * 1024
    assert limits.response_bytes == 3 * 1024 * 1024
    assert limits.live_metadata_bytes == 2 * 1024 * 1024
    assert limits.event_line_bytes == 16 * 1024


def test_campaign_transport_limits_match_the_independent_proof_codec() -> None:
    from peano_lab.library.lean_proof_strand import (
        DEFAULT_LIVE_SOURCE_BYTES,
        DEFAULT_LIVE_URL_BYTES,
        MAX_LIVE_CODEC_SOURCE_BYTES,
        MAX_LIVE_URL_BYTES,
    )

    assert service.DEFAULT_LIVE_URL_BYTES == DEFAULT_LIVE_URL_BYTES
    assert service.MAX_LIVE_URL_BYTES == MAX_LIVE_URL_BYTES
    assert service.DEFAULT_LIVE_SOURCE_BYTES == DEFAULT_LIVE_SOURCE_BYTES
    assert service.MAX_LIVE_SOURCE_BYTES == MAX_LIVE_CODEC_SOURCE_BYTES


def test_live_sidecar_schema_matches_real_exporter_contract_not_only_mock() -> None:
    from peano_lab.library.lean_proof_strand import LIVE_EXPORT_SCHEMA

    assert service.LIVE_SCHEMA == LIVE_EXPORT_SCHEMA
    assert service.LIVE_SCHEMA == "peano-lab-lean-live-v1"


def test_compact_live_decoder_matches_real_codec_contract() -> None:
    from peano_lab.library.lean_proof_strand import compress_lean_live_codez

    compressed = compress_lean_live_codez(LIVE_SOURCE)
    url = "https://live.lean-lang.org/#codez=" + quote(compressed, safe="")
    actual, encoding = service._decoded_live_source(url, maximum=len(LIVE_SOURCE.encode("utf-8")))
    assert actual == LIVE_SOURCE.encode("utf-8")
    assert encoding == "codez"


@pytest.mark.parametrize(
    ("source", "payload"),
    (
        ("nnnnnnnnnnnnnnnn13", "HY1%2FAjAzEA"),
        ("qqqqqqqqqqqqqqqqqq16", "I41%2BgjAbEA"),
    ),
)
def test_compact_live_decoder_matches_official_escaped_base64(
    source: str,
    payload: str,
) -> None:
    url = "https://live.lean-lang.org/#codez=" + payload
    actual, encoding = service._decoded_live_source(
        url,
        maximum=len(source.encode("utf-8")),
    )

    assert service.validate_live_url(url) == url
    assert actual == source.encode("utf-8")
    assert encoding == "codez"


def test_validated_requests_cannot_expand_operator_resource_caps() -> None:
    limits = service.ServiceLimits()
    selected = service.validate_request({"theorem": "alpha_proof'", "edition": "alpha"}, limits)
    assert selected.theorem == "alpha_proof'"
    assert selected.edition == "alpha"
    assert selected.memory_mib == 1_024
    assert selected.strand_nodes == 1_024
    with pytest.raises(service.ServiceError, match="max_memory_mib"):
        service.validate_request({"theorem": "ok", "max_memory_mib": 1_025}, limits)
    with pytest.raises(service.ServiceError, match="max_strand_nodes"):
        service.validate_request({"theorem": "ok", "max_strand_nodes": 1_025}, limits)


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
        "https://live.lean-lang.org/#url=https%3A%2F%2Fevil.invalid%2Fproof.lean",
        "https://live.lean-lang.org/#codez=",
        "https://live.lean-lang.org/#codez=bad%20payload",
        "https://live.lean-lang.org/#codez=HY1-AjAzEA",
        "https://live.lean-lang.org/#codez=HY1/AjAzEA",
        "https://live.lean-lang.org/#codez=HY1%2fAjAzEA",
        "https://live.lean-lang.org/#codez=HY1%252FAjAzEA",
        "https://live.lean-lang.org/#codez=I41+gjAbEA",
        "https://live.lean-lang.org/#codez=I41%2bgjAbEA",
        "https://live.lean-lang.org/#codez=BYUwNmD2Q%3D",
        "https://live.lean-lang.org/#codez=invalid$dollar",
        "https://live.lean-lang.org/#codez=bad/payload",
        "https://live.lean-lang.org/#codez=bad_payload",
        "https://live.lean-lang.org/#codez=bad=padding",
        "javascript:alert(1)",
    ],
)
def test_only_exact_bounded_official_lean_live_host_is_accepted(url: str) -> None:
    assert service.validate_live_url(url) is None


def test_campaign_live_links_keep_the_exact_operator_byte_ceiling() -> None:
    prefix = "https://live.lean-lang.org/#codez="
    supported = prefix + "A" * (33 * 1024)
    oversized = prefix + "A" * service.DEFAULT_LIVE_URL_BYTES

    assert service.validate_live_url(supported) == supported
    assert service.validate_live_url(oversized) is None


def test_exact_official_lean_live_host_is_accepted() -> None:
    assert service.validate_live_url(LIVE_URL) == LIVE_URL
    assert service.validate_live_url("https://live.lean-lang.org/#codez=BYUwNmD2Q") == (
        "https://live.lean-lang.org/#codez=BYUwNmD2Q"
    )
    assert service.validate_live_url("https://live.lean-lang.org/#codez=HY1%2FAjAzEA") == (
        "https://live.lean-lang.org/#codez=HY1%2FAjAzEA"
    )
    assert service.validate_live_url("https://live.lean-lang.org/#codez=I41%2BgjAbEA") == (
        "https://live.lean-lang.org/#codez=I41%2BgjAbEA"
    )


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
    assert terminal["live_encoding"] == "code"
    assert terminal["lean_live"]["share_encoding"] == "code"
    assert terminal["lean_live"]["source_sha256"] == sha256(LIVE_SOURCE.encode("utf-8")).hexdigest()
    assert terminal["lean_live"]["self_contained"] is True
    assert terminal["lean_live"]["core_imports"] == []
    assert terminal["lean_live"]["external_import_count"] == 0
    assert terminal["lean_live"]["local_source_verified"] is True
    command = fake_exporter.calls[0]
    assert "--verify" in command
    assert "--progress-json" in command
    assert "--live-lean-output" in command
    assert FakeExporter._value(command, "--max-memory-mib") == "1024"
    assert FakeExporter._value(command, "--max-strand-nodes") == "1024"
    assert FakeExporter._value(command, "--max-live-url-bytes") == "524288"
    assert FakeExporter._value(command, "--max-live-source-kib") == "1024"


@pytest.mark.parametrize(
    ("mode", "message"),
    [
        ("failed", "Unknown Alpha Peano theorem"),
        ("unverified", "independent Lean compilation receipt"),
        ("wrong_theorem", "selected theorem"),
        ("unverified_live", "locally checked source"),
        ("not_self_contained", "locally checked source"),
        ("declared_external_import", "locally checked source"),
        ("external_import_count", "locally checked source"),
        ("unsafe_live_url", "unsafe or oversized official URL"),
        ("forged_live_source", "exact locally compiled proof"),
        ("codez_forged", "exact locally compiled proof"),
        ("codez_bomb", "bounded exact proof"),
        ("wrong_encoding", "exact inline source encoding"),
        ("unsupported_encoding", "unsupported inline proof encoding"),
        ("wrong_share_status", "contradicts its checked metadata status"),
        ("mixed_live", "companion-backed certificates"),
        ("sidecar_fallback", "non-standalone certificate fallback"),
        ("private_import", "explicit import"),
        ("mathlib_import", "explicit import"),
        ("core_import", "explicit import"),
        ("sorry_proof", "unsafe unchecked placeholder"),
        ("new_axiom", "unaudited external axiom"),
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


def test_compact_exact_live_link_authenticates_the_same_locally_checked_source(tmp_path: Path) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode="codez"))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["status"] == "completed"
    assert terminal["lean_verified"] is True
    assert terminal["live_status"] == "ready"
    assert terminal["live_encoding"] == "codez"
    assert terminal["lean_live"]["share_encoding"] == "codez"
    assert terminal["lean_live"]["local_source_verified"] is True
    assert str(terminal["live_url"]).startswith("https://live.lean-lang.org/#codez=")
    decoded, encoding = service._decoded_live_source(
        str(terminal["live_url"]),
        maximum=len(LIVE_SOURCE.encode("utf-8")),
    )
    assert encoding == "codez"
    assert decoded == (manager.storage / str(job["job_id"]) / "live.lean").read_bytes()


def test_campaign_live_link_authenticates_large_source_and_snapshot(tmp_path: Path) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode="campaign_codez"))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])

    assert terminal["status"] == "completed"
    assert terminal["lean_verified"] is True
    assert terminal["live_status"] == "ready"
    source = campaign_source().encode("utf-8")
    assert len(source) > 200 * 1024
    url = str(terminal["live_url"])
    assert 128 * 1024 < len(url.encode("utf-8")) < manager.limits.live_url_bytes
    assert terminal["lean_live"]["url"] == url
    sidecar = manager.storage / str(job["job_id"]) / "live.json"
    assert sidecar.stat().st_size > manager.limits.event_line_bytes
    response = service._bounded_json(terminal, maximum=manager.limits.response_bytes)
    assert 256 * 1024 < len(response) < manager.limits.response_bytes
    decoded, encoding = service._decoded_live_source(url, maximum=len(source))
    assert encoding == "codez"
    assert decoded == source
    assert terminal["lean_live"]["source_sha256"] == sha256(source).hexdigest()


def test_campaign_live_source_cannot_exceed_the_operator_bound(tmp_path: Path) -> None:
    manager = service.JobManager(
        tmp_path / "jobs",
        limits=service.ServiceLimits(live_source_bytes=128 * 1024),
        popen=FakeExporter(mode="campaign_codez"),
    )
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])

    assert terminal["status"] == "failed"
    assert "source exceeds its reviewed size limit" in str(terminal["error"])


def test_untrusted_exporter_cannot_publish_a_spoofed_live_share(tmp_path: Path) -> None:
    manager = service.JobManager(tmp_path / "jobs", popen=FakeExporter(mode="unsafe_live_url"))
    job = manager.submit({"theorem": "add_comm"})
    terminal = await_terminal(manager, job["job_id"])
    assert terminal["status"] == "failed"
    assert "unsafe or oversized official URL" in str(terminal["error"])
    assert terminal["live_url"] is None


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
    assert selected["max_nodes"] == 1_024
    assert selected["max_live_url_bytes"] == 512 * 1024
    assert selected["max_live_source_bytes"] == 1024 * 1024
    assert selected["memory_mib"] == 1_024
    assert selected["public_origin"] is None
    assert selected["allowed_origins"] == []
    assert selected["trusted_proxy"] is False
    assert selected["api_only"] is False
    assert selected["api_root"] == service.API_PREFIX
    status, content, _ = request(base, service.API_PREFIX + "/health")
    assert status == 200
    assert json.loads(content)["status"] == "ok"


def test_public_service_advertises_only_its_exact_approved_browser(
    public_http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, _ = public_http_server
    status, content, headers = request(
        base,
        service.API_PREFIX + "/config",
        headers={"Origin": "https://faculty.example.test"},
    )

    assert status == 200
    selected = json.loads(content)
    assert selected["public_origin"] == "https://lean.example.test"
    assert selected["allowed_origins"] == ["https://faculty.example.test"]
    assert selected["api_root"] == "https://lean.example.test/api/lean-strands"
    assert selected["single_worker"] is True
    assert headers["Access-Control-Allow-Origin"] == "https://faculty.example.test"
    assert headers["Vary"] == "Origin"
    assert "Access-Control-Allow-Credentials" not in headers


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_public_service_approves_bounded_exact_origin_browser_preflight(
    public_http_server: tuple[str, service.LeanStrandServer],
    method: str,
) -> None:
    base, _ = public_http_server
    status, content, headers = request(
        base,
        service.API_PREFIX + "/jobs",
        method="OPTIONS",
        headers={
            "Origin": "https://faculty.example.test",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert status == 204
    assert content == b""
    assert headers["Access-Control-Allow-Origin"] == "https://faculty.example.test"
    assert method in headers["Access-Control-Allow-Methods"]
    assert "Content-Type" in headers["Access-Control-Allow-Headers"]
    assert headers["Access-Control-Max-Age"] == "600"
    assert "Access-Control-Allow-Credentials" not in headers


@pytest.mark.parametrize(
    ("origin", "method", "request_headers"),
    [
        ("https://evil.example.test", "POST", "content-type"),
        ("https://faculty.example.test.evil.invalid", "POST", "content-type"),
        ("null", "POST", "content-type"),
        ("https://faculty.example.test", "PUT", "content-type"),
        ("https://faculty.example.test", "POST", "authorization"),
        ("https://faculty.example.test", "POST", "content-type, x-csrf-token"),
    ],
)
def test_public_service_rejects_unapproved_cross_origin_preflight(
    public_http_server: tuple[str, service.LeanStrandServer],
    origin: str,
    method: str,
    request_headers: str,
) -> None:
    base, _ = public_http_server
    status, _, headers = request(
        base,
        service.API_PREFIX + "/jobs",
        method="OPTIONS",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": request_headers,
        },
    )

    assert status == 403
    if origin != "https://faculty.example.test":
        assert "Access-Control-Allow-Origin" not in headers


def test_public_service_runs_only_approved_cross_origin_proof_workflow(
    public_http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, server = public_http_server
    approved = {"Origin": "https://faculty.example.test"}
    status, content, headers = request(
        base,
        service.API_PREFIX + "/jobs",
        method="POST",
        payload={"theorem": "add_comm", "edition": "stable"},
        headers=approved,
    )

    assert status == 202
    assert headers["Access-Control-Allow-Origin"] == approved["Origin"]
    submitted = json.loads(content)
    completed = await_terminal(server.job_manager, submitted["job_id"])
    assert completed["lean_verified"] is True
    for path in (
        submitted["status_url"],
        submitted["status_url"] + "/events",
        completed["downloads"]["lean"],
        completed["downloads"]["zip"],
    ):
        status, _, headers = request(base, str(path), headers=approved)
        assert status == 200
        assert headers["Access-Control-Allow-Origin"] == approved["Origin"]

    status, _, headers = request(
        base,
        str(submitted["status_url"]),
        method="DELETE",
        headers=approved,
    )
    assert status == 200
    assert headers["Access-Control-Allow-Origin"] == approved["Origin"]


def test_public_service_rejects_unapproved_origin_and_spoofed_public_host(
    public_http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, _ = public_http_server
    status, _, headers = request(
        base,
        service.API_PREFIX + "/config",
        headers={"Origin": "https://evil.example.test"},
    )
    assert status == 403
    assert "Access-Control-Allow-Origin" not in headers
    assert request(base, "/health", headers={"Host": "evil.example.test"})[0] == 421


def test_http_campaign_snapshot_preserves_the_entire_authenticated_live_url(
    http_server: tuple[str, service.LeanStrandServer],
    fake_exporter: FakeExporter,
) -> None:
    base, server = http_server
    fake_exporter.mode = "campaign_codez"
    job = submit_http(base)
    terminal = await_terminal(server.job_manager, str(job["job_id"]))
    assert terminal["status"] == "completed"

    status, content, _headers = request(
        base,
        service.API_PREFIX + "/jobs/" + str(job["job_id"]),
    )

    assert status == 200
    assert 256 * 1024 < len(content) < server.job_manager.limits.response_bytes
    received = json.loads(content)
    assert received["live_url"] == received["lean_live"]["url"]
    assert len(received["live_url"].encode("utf-8")) > 128 * 1024
    assert received["lean_live"]["source_bytes"] > 200 * 1024
    assert received["lean_live"]["local_source_verified"] is True


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
        "/book/_static/constructive-next-layer-explorer/continued-fractions/explorer/defined/tag/CF0002.html",
        "/book/_static/constructive-advanced-layer-explorer/binary-exponentiation/explorer/defined/tag/AL0002.html",
        "/book/_static/constructive-transport-layer-explorer/euclidean-gcd/explorer/defined/tag/TL0002.html",
        "/book/_static/constructive-milestone-closure-explorer/prime-routes/explorer/defined/tag/MC0002.html",
        "/book/_static/constructive-research-layer-explorer/polynomial-hensel/explorer/defined/tag/RL0002.html",
        "/book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/defined/tag/CE0002.html",
        "/book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/tag/CE0002.html",
        "/book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/defined/graph.html",
        "/book/_static/constructive-verified-future-explorer/next-checked-frontier/explorer/defined/tag/FU0002.html",
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


def test_unreviewed_individual_campaign_pages_are_not_implicitly_enhanced(
    http_server: tuple[str, service.LeanStrandServer],
) -> None:
    base, _ = http_server
    status, content, _headers = request(
        base,
        "/book/_static/unreviewed-campaign/defined/tag/FAKE0002.html",
    )

    assert status == 200
    assert b"lean-selector.js" not in content
    assert b"lean-selector.css" not in content


@pytest.mark.parametrize(
    "tampering",
    (
        "missing_manifest",
        "stale_version",
        "wrong_schema",
        "wrong_catalog",
        "wrong_identity",
        "unknown_family",
        "zero_checked_theorems",
        "bool_checked_theorems",
        "duplicate_family",
        "unsafe_family_slug",
        "duplicate_json_field",
        "nonfinite_json_number",
        "manifest_symlink",
        "missing_campaign",
        "unsealed_future_release",
        "missing_channel",
        "corrupt_catalog",
    ),
)
def test_constructive_detail_controls_require_an_actual_current_sealed_family(
    http_server: tuple[str, service.LeanStrandServer],
    static_root: Path,
    tampering: str,
) -> None:
    base, _ = http_server
    directory = static_root / "book/_static/constructive-breakthrough-layer-explorer"
    manifest_path = directory / "manifest.json"
    campaign_path = static_root / "book/_static/constructive-grand-campaign/campaign.json"
    channel_path = static_root / "artifacts/peano-library/channels-v24.json"
    catalog_path = static_root / "artifacts/peano-library/alpha/catalog-v24.json"
    manifest = json.loads(manifest_path.read_bytes())

    if tampering == "missing_manifest":
        manifest_path.rename(directory / "manifest-unreviewed.json")
    elif tampering == "stale_version":
        manifest["alpha_edition_version"] = "v25"
    elif tampering == "wrong_schema":
        manifest["schema"] = "peano-lab-constructive-evil-explorer-v1-manifest"
    elif tampering == "wrong_catalog":
        manifest["catalog_sha256"] = "0" * 64
    elif tampering == "wrong_identity":
        manifest["edition_identity_sha256"] = "0" * 64
    elif tampering == "unknown_family":
        manifest["families"][0]["slug"] = "another-family"
    elif tampering == "zero_checked_theorems":
        manifest["families"][0]["theorem_count"] = 0
    elif tampering == "bool_checked_theorems":
        manifest["families"][0]["theorem_count"] = True
    elif tampering == "duplicate_family":
        manifest["families"].append(dict(manifest["families"][0]))
    elif tampering == "unsafe_family_slug":
        manifest["families"][0]["slug"] = "../matrix-cofactor-expansion"
    elif tampering == "duplicate_json_field":
        manifest_path.write_text('{"schema":"first","schema":"second"}', encoding="utf-8")
    elif tampering == "nonfinite_json_number":
        manifest_path.write_text('{"schema":NaN}', encoding="utf-8")
    elif tampering == "manifest_symlink":
        original = directory / "manifest-original.json"
        manifest_path.rename(original)
        manifest_path.symlink_to(original)
    elif tampering == "missing_campaign":
        campaign_path.rename(campaign_path.with_name("campaign-unreviewed.json"))
    elif tampering == "unsealed_future_release":
        campaign = json.loads(campaign_path.read_bytes())
        campaign["meta"]["current_alpha_version"] = "v25"
        campaign["ambitious_boundaries"]["alpha_v25_edition"] = dict(
            campaign["ambitious_boundaries"]["alpha_v24_edition"]
        )
        campaign_path.write_text(json.dumps(campaign), encoding="utf-8")
        manifest["alpha_edition_version"] = "v25"
    elif tampering == "missing_channel":
        channel_path.rename(channel_path.with_name("channels-v24-unreviewed.json"))
    elif tampering == "corrupt_catalog":
        catalog_path.write_bytes(catalog_path.read_bytes() + b" ")

    if tampering not in {
        "missing_manifest",
        "duplicate_json_field",
        "nonfinite_json_number",
        "manifest_symlink",
    }:
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status, content, _ = request(
        base,
        "/book/_static/constructive-breakthrough-layer-explorer/"
        "matrix-cofactor-expansion/explorer/defined/tag/CE0002.html",
    )

    assert status == 200
    assert b"lean-selector.js" not in content
    assert b"lean-selector.css" not in content


@pytest.mark.parametrize(
    "suffix",
    (
        "constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/defined/tag/FAKE.html",
        "constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/extra/tag/FAKE.html",
        "constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/defined/definition/FAKE.html",
        "constructive-Breakthrough-layer-explorer/matrix-cofactor-expansion/explorer/defined/tag/FAKE.html",
        "constructive-breakthrough_layer-explorer/matrix-cofactor-expansion/explorer/defined/tag/FAKE.html",
    ),
)
def test_constructive_controls_require_exact_owner_controlled_theorem_paths(
    http_server: tuple[str, service.LeanStrandServer],
    static_root: Path,
    suffix: str,
) -> None:
    base, _ = http_server
    page = static_root / "book" / "_static" / suffix
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("<html><head></head><body>proof</body></html>", encoding="utf-8")

    status, content, _ = request(base, "/book/_static/" + suffix)

    assert status == 200
    assert b"lean-selector.js" not in content


def test_constructive_release_cache_cannot_preserve_tampered_catalog_authority(
    http_server: tuple[str, service.LeanStrandServer],
    static_root: Path,
) -> None:
    base, _ = http_server
    path = (
        "/book/_static/constructive-breakthrough-layer-explorer/"
        "matrix-cofactor-expansion/explorer/defined/tag/CE0002.html"
    )
    status, reviewed, _ = request(base, path)
    assert status == 200
    assert b"lean-selector.js" in reviewed

    catalog = static_root / "artifacts/peano-library/alpha/catalog-v24.json"
    catalog.write_bytes(catalog.read_bytes() + b" ")
    status, unreviewed, _ = request(base, path)

    assert status == 200
    assert b"lean-selector.js" not in unreviewed


@pytest.mark.parametrize("publication", tuple(CURRENT_PUBLICATIONS))
@pytest.mark.parametrize("shape", (
    "explorer/tag/{tag}.html", "explorer/defined/tag/{tag}.html",
    "explorer/graph.html", "explorer/defined/graph.html",
))
def test_current_v28_publications_have_reviewed_exact_and_graph_controls(
    http_server: tuple[str, service.LeanStrandServer],
    v28_static_root: Path,
    publication: str,
    shape: str,
) -> None:
    base, server = http_server
    selected = CURRENT_PUBLICATIONS[publication]
    directory = v28_static_root / "book/_static" / publication
    assert server.reviewed_constructive_family(directory, selected["slug"])
    path = f"/book/_static/{publication}/{selected['slug']}/{shape.format(tag=selected['tag'])}"
    original = (v28_static_root / path.lstrip("/")).read_bytes()

    status, content, headers = request(base, path + "?v=current&target=checked")

    assert status == 200
    assert content.count(b"lean-selector.js") == content.count(b"lean-selector.css") == 1
    assert content.index(b"lean-selector.js") < content.index(b"</head>")
    assert (v28_static_root / path.lstrip("/")).read_bytes() == original
    head_status, head_content, head_headers = request(base, path, method="HEAD")
    assert head_status == 200 and head_content == b""
    assert head_headers["Content-Length"] == headers["Content-Length"] == str(len(content))


@pytest.mark.parametrize("publication", tuple(CURRENT_PUBLICATIONS))
@pytest.mark.parametrize("tampering", (
    "missing_manifest", "directory_derived_schema", "schema_without_manifest",
    "wrong_current_version", "wrong_catalog", "wrong_identity",
    "missing_first_version", "wrong_first_version", "missing_first_catalog", "wrong_first_catalog",
    "zero_checked_theorems", "bool_checked_theorems", "duplicate_family", "unknown_family",
    "wrong_family_version", "duplicate_json_field", "nonfinite_json_number",
    "manifest_symlink", "wrong_owner", "oversized_manifest", "corrupt_catalog",
))
def test_current_v28_publication_review_fails_closed_after_manifest_tampering(
    http_server: tuple[str, service.LeanStrandServer],
    v28_static_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    publication: str,
    tampering: str,
) -> None:
    base, server = http_server
    selected = CURRENT_PUBLICATIONS[publication]
    directory = v28_static_root / "book/_static" / publication
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    # Populate both real authority caches before invalidating the owned input.
    assert server.reviewed_constructive_family(directory, selected["slug"])
    assert server._constructive_release_cache and server._constructive_manifest_cache

    if tampering == "missing_manifest":
        manifest_path.rename(directory / "manifest-unreviewed.json")
    elif tampering == "directory_derived_schema":
        manifest["schema"] = (
            f"peano-lab-{publication}-v1-manifest"
            if publication.endswith("-v28")
            else f"peano-lab-{publication}-v2-manifest"
        )
    elif tampering == "schema_without_manifest":
        manifest["schema"] = manifest["schema"].removesuffix("-manifest")
    elif tampering == "wrong_current_version":
        manifest["alpha_edition_version"] = "v29"
    elif tampering == "wrong_catalog":
        manifest["catalog_sha256"] = "0" * 64
    elif tampering == "wrong_identity":
        manifest["edition_identity_sha256"] = "0" * 64
    elif tampering == "missing_first_version":
        del manifest["alpha_first_enrolled_version"]
    elif tampering == "wrong_first_version":
        manifest["alpha_first_enrolled_version"] = "v27" if selected["first"] == "v28" else "v28"
    elif tampering == "missing_first_catalog":
        del manifest["first_enrollment_catalog_sha256"]
    elif tampering == "wrong_first_catalog":
        manifest["first_enrollment_catalog_sha256"] = "0" * 64
    elif tampering == "zero_checked_theorems":
        manifest["families"][0]["theorem_count"] = 0
    elif tampering == "bool_checked_theorems":
        manifest["families"][0]["theorem_count"] = True
    elif tampering == "duplicate_family":
        manifest["families"].append(dict(manifest["families"][0]))
    elif tampering == "unknown_family":
        manifest["families"][0]["slug"] = "unreviewed-family"
    elif tampering == "wrong_family_version":
        manifest["families"][0]["alpha_edition_version"] = "v27"
    elif tampering == "duplicate_json_field":
        manifest_path.write_text('{"schema":"one","schema":"two"}', encoding="utf-8")
    elif tampering == "nonfinite_json_number":
        manifest_path.write_text('{"schema":NaN}', encoding="utf-8")
    elif tampering == "manifest_symlink":
        original = directory / "manifest-original.json"
        manifest_path.rename(original)
        manifest_path.symlink_to(original)
    elif tampering == "wrong_owner":
        ordinary_stat = Path.stat

        def different_owner(path: Path, *args: object, **kwargs: object) -> os.stat_result:
            information = ordinary_stat(path, *args, **kwargs)
            if path == manifest_path:
                fields = list(information)
                fields[4] = information.st_uid + 1
                return os.stat_result(fields)
            return information

        monkeypatch.setattr(Path, "stat", different_owner)
    elif tampering == "oversized_manifest":
        manifest_path.write_bytes(manifest_path.read_bytes() + b" " * (service.MAX_EXPLORER_MANIFEST_BYTES + 1))
    elif tampering == "corrupt_catalog":
        catalog = v28_static_root / "artifacts/peano-library/alpha/catalog-v28.json"
        catalog.write_bytes(catalog.read_bytes() + b" ")

    if tampering not in {
        "missing_manifest", "duplicate_json_field", "nonfinite_json_number", "manifest_symlink",
        "wrong_owner", "oversized_manifest", "corrupt_catalog",
    }:
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert not server.reviewed_constructive_family(directory, selected["slug"])
    for suffix in (f"explorer/defined/tag/{selected['tag']}.html", "explorer/defined/graph.html"):
        status, content, _ = request(base, f"/book/_static/{publication}/{selected['slug']}/{suffix}")
        assert status == 200
        assert b"lean-selector.js" not in content and b"lean-selector.css" not in content


@pytest.mark.parametrize("segment", (
    "constructive-second-wave-explorer-v29", "constructive-second-wave-explorer-v27",
    "constructive-second-wave-explorer-v028", "constructive-second-wave-explorer-v28-extra",
    "constructive-second-wave-explorer-V28", "constructive-lower-layer-explorer-v28",
    "constructive-unreviewed-explorer-v28", "Constructive-second-wave-explorer-v28",
    "constructive-second_wave-explorer-v28",
))
def test_unknown_versioned_publications_cannot_fall_through_to_legacy_graph_controls(
    http_server: tuple[str, service.LeanStrandServer],
    v28_static_root: Path,
    segment: str,
) -> None:
    base, server = http_server
    reviewed = v28_static_root / "book/_static/constructive-second-wave-explorer-v28"
    manifest = json.loads((reviewed / "manifest.json").read_bytes())
    directory = v28_static_root / "book/_static" / segment
    # Case-only forged spellings alias the fixture directory on default macOS
    # filesystems. Request spelling must still fail the exact route policy.
    directory.mkdir(parents=True, exist_ok=True)
    # All release/family fields are valid; neither a plausible derived schema
    # nor the real successor schema authorizes an unreviewed directory name.
    for schema in (manifest["schema"], f"peano-lab-{segment}-v1-manifest"):
        manifest["schema"] = schema
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        assert not server.reviewed_constructive_family(directory, "integer-linear-algebra")
        for suffix in ("explorer/graph.html", "explorer/defined/graph.html", "explorer/defined/tag/DL0028.html"):
            page = directory / "integer-linear-algebra" / suffix
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("<html><head></head><body>unreviewed</body></html>", encoding="utf-8")
            status, content, _ = request(base, "/" + page.relative_to(v28_static_root).as_posix())
            assert status == 200
            assert b"lean-selector.js" not in content and b"lean-selector.css" not in content


@pytest.mark.parametrize("relabel_current", (False, True))
def test_frozen_v27_directory_is_not_the_current_v28_publication(
    http_server: tuple[str, service.LeanStrandServer],
    v28_static_root: Path,
    relabel_current: bool,
) -> None:
    base, server = http_server
    directory = v28_static_root / "book/_static/constructive-second-wave-explorer"
    if relabel_current:
        current = v28_static_root / "book/_static/constructive-second-wave-explorer-v28/manifest.json"
        (directory / "manifest.json").write_bytes(current.read_bytes())
    assert not server.reviewed_constructive_family(directory, "integer-linear-algebra")
    for suffix in ("explorer/defined/tag/DL0028.html", "explorer/tag/DL0028.html", "explorer/defined/graph.html"):
        status, content, _ = request(base, "/" + (directory / "integer-linear-algebra" / suffix).relative_to(v28_static_root).as_posix())
        assert status == 200 and b"lean-selector.js" not in content


@pytest.mark.parametrize("version", ("v27", "v29"))
def test_known_successor_mapping_requires_v28_even_with_a_consistent_other_release(
    v28_static_root: Path,
    version: str,
) -> None:
    digest, identity = install_test_release(v28_static_root, version=version)
    directory = v28_static_root / "book/_static/constructive-second-wave-explorer-v28"
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest.update(alpha_edition_version=version, catalog_sha256=digest, edition_identity_sha256=identity)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    server = non_listening_review_server(v28_static_root)
    assert server._current_constructive_release(directory.parent, owner=directory.stat().st_uid) == (version, digest, identity)
    assert not server.reviewed_constructive_family(directory, "integer-linear-algebra")


@pytest.mark.parametrize("publication", tuple(CURRENT_PUBLICATIONS))
def test_actual_v28_publications_and_all_root_panels_pass_read_only_release_review(publication: str) -> None:
    server = non_listening_review_server(ROOT)
    handler = object.__new__(service.LeanStrandHandler)
    handler.server = server
    directory = ROOT / "book/_static" / publication
    manifest_path = directory / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["schema"] == CURRENT_PUBLICATIONS[publication]["schema"]
    assert manifest["alpha_edition_version"] == "v28"
    assert manifest["alpha_first_enrolled_version"] == CURRENT_PUBLICATIONS[publication]["first"]
    assert {family["slug"] for family in manifest["families"]} == CURRENT_PUBLICATIONS[publication]["slugs"]

    for family in manifest["families"]:
        assert server.reviewed_constructive_family(directory, family["slug"])
        suffixes = ["explorer/defined/graph.html"]
        for tag in family["root_tags"].values():
            suffixes.extend((f"explorer/tag/{tag}.html", f"explorer/defined/tag/{tag}.html"))
        for suffix in suffixes:
            page = directory / family["slug"] / suffix
            original = page.read_bytes()
            enhanced = handler._inject_selector(page, page.relative_to(ROOT).parts)
            assert enhanced is not None
            assert b"lean-selector.js" in enhanced and b"lean-selector.css" in enhanced
            assert page.read_bytes() == original
    assert manifest_path.read_bytes() == manifest_bytes


def test_actual_frozen_v27_publication_remains_unreviewed_for_current_browser() -> None:
    server = non_listening_review_server(ROOT)
    handler = object.__new__(service.LeanStrandHandler)
    handler.server = server
    directory = ROOT / "book/_static/constructive-second-wave-explorer"
    manifest = json.loads((directory / "manifest.json").read_bytes())
    assert manifest["alpha_edition_version"] == manifest["alpha_first_enrolled_version"] == "v27"
    for family in manifest["families"]:
        assert not server.reviewed_constructive_family(directory, family["slug"])
        page = directory / family["slug"] / "explorer/defined/graph.html"
        assert handler._inject_selector(page, page.relative_to(ROOT).parts) is None


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
    assert lean.startswith(b"theorem add_comm")
    assert b"import " not in lean
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


@pytest.mark.parametrize(
    "value",
    [
        "http://public.example.test",
        "https://user:secret@public.example.test",
        "https://public.example.test/private",
        "https://public.example.test?token=private",
        "https://public.example.test#fragment",
        "https://public.example.test:99999",
        "https://public.example.test,https://evil.example.test",
        "*",
        "null",
    ],
)
def test_public_origins_must_be_exact_https_without_secrets(value: str) -> None:
    with pytest.raises(service.ServiceError):
        service._safe_origin(value, label="public origin")


def test_exact_loopback_http_origins_remain_available_for_bounded_tests() -> None:
    assert service._safe_origin("http://127.0.0.1:8787/", label="origin") == "http://127.0.0.1:8787"
    assert service._safe_origin("https://FACULTY.example.test", label="origin") == "https://faculty.example.test"


def test_cli_rejects_unsafe_public_exposure_before_creating_a_listener(tmp_path: Path) -> None:
    public = tmp_path / "public"
    public.mkdir()
    options = ["--directory", str(public), "--storage", str(tmp_path / "jobs")]

    with pytest.raises(service.ServiceError, match="allowed origins require"):
        service.build_server(options + ["--allowed-origin", "https://faculty.example.test"])
    with pytest.raises(service.ServiceError, match="must use HTTPS"):
        service.build_server(options + ["--public-origin", "http://lean.example.test"])
    with pytest.raises(service.ServiceError, match="loopback-only"):
        service.build_server(
            options
            + [
                "--host", "0.0.0.0", "--public-host", "--trust-proxy",
                "--public-origin", "https://lean.example.test",
            ]
        )
    assert not (tmp_path / "jobs").exists()


def test_api_only_public_mode_does_not_publish_repository_files(tmp_path: Path) -> None:
    public = tmp_path / "public"
    public.mkdir()
    (public / "proof.html").write_text("sensitive draft", encoding="utf-8")
    server = service.build_server(
        [
            "--port", "0",
            "--directory", str(public),
            "--storage", str(tmp_path / "jobs"),
            "--public-origin", "https://lean.example.test",
            "--allowed-origin", "https://faculty.example.test",
            "--api-only",
            "--max-mutations-per-minute", "7",
            "--max-concurrent-requests", "4",
        ]
    )
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert request(base, "/")[0] == 404
        assert request(base, "/proof.html")[0] == 404
        assert request(base, "/health")[0] == 200
        status, content, _ = request(base, service.API_PREFIX + "/config")
        assert status == 200
        assert json.loads(content)["api_only"] is True
        assert server.job_manager.limits.mutations_per_minute == 7
        assert server.job_manager.limits.concurrent_requests == 4
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2.0)


def test_trusted_loopback_proxy_pins_https_host_and_client_rate_bucket(
    manager: service.JobManager,
    static_root: Path,
) -> None:
    server = service.LeanStrandServer(
        ("127.0.0.1", 0),
        manager,
        static_root,
        public_origin="https://lean.example.test",
        allowed_origins=("https://faculty.example.test",),
        trust_proxy=True,
    )
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    approved = {
        "Host": "lean.example.test",
        "X-Forwarded-Host": "lean.example.test",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-For": "192.0.2.9, 198.51.100.24",
        "Origin": "https://faculty.example.test",
    }
    try:
        status, content, headers = request(
            base,
            service.API_PREFIX + "/jobs",
            method="POST",
            payload={"theorem": "add_comm"},
            headers=approved,
        )
        assert status == 202
        assert headers["Access-Control-Allow-Origin"] == approved["Origin"]
        await_terminal(manager, json.loads(content)["job_id"])
        assert "198.51.100.24" in manager._mutation_windows
        assert "192.0.2.9" not in manager._mutation_windows

        insecure = dict(approved, **{"X-Forwarded-Proto": "http"})
        assert request(base, service.API_PREFIX + "/config", headers=insecure)[0] == 421
        forged = dict(approved, **{"X-Forwarded-Host": "evil.example.test"})
        assert request(base, service.API_PREFIX + "/config", headers=forged)[0] == 421
        invalid_client = dict(approved, **{"X-Forwarded-For": "not-an-ip"})
        assert request(
            base,
            service.API_PREFIX + "/jobs",
            method="POST",
            payload={"theorem": "add_comm"},
            headers=invalid_client,
        )[0] == 400
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2.0)
