#!/usr/bin/env python3
"""Exercise the real theorem-browser service with one bounded checked proof."""

from __future__ import annotations

import argparse
from functools import lru_cache
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import ssl
import subprocess
import sys
import tempfile
import time
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
import zipfile


DEFAULT_BASE_URL = "http://127.0.0.1:8787"
API_ROOT = "/api/lean-strands"
MAX_HTML_BYTES = 4 * 1024 * 1024
MAX_JSON_BYTES = 3 * 1024 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_FILES = 4_096
MAX_LIVE_URL_BYTES = 1024 * 1024
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
THEOREM = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,127}\Z")
SERVER_STARTUP_SECONDS = 15.0


class BrowserCheckError(ValueError):
    """The live browser service did not establish its claimed proof workflow."""


@lru_cache(maxsize=1)
def _verified_tls_context() -> ssl.SSLContext | None:
    """Use installed certifi only when Python has no configured CA trust store."""

    paths = ssl.get_default_verify_paths()
    if (
        paths.cafile is not None
        or paths.capath is not None
        or os.environ.get(paths.openssl_cafile_env)
        or os.environ.get(paths.openssl_capath_env)
    ):
        return None
    try:
        default = ssl.create_default_context()
    except (OSError, ssl.SSLError):
        return None
    if default.cert_store_stats().get("x509_ca", 0) > 0:
        return None
    try:
        import certifi

        bundle = certifi.where()
        if type(bundle) is not str or not Path(bundle).is_file():
            return None
        selected = ssl.create_default_context(cafile=bundle)
    except (ImportError, OSError, ssl.SSLError, ValueError):
        return None
    if (
        selected.verify_mode != ssl.CERT_REQUIRED
        or selected.check_hostname is not True
        or selected.cert_store_stats().get("x509_ca", 0) < 1
    ):
        return None
    return selected


def _base_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise BrowserCheckError("the theorem browser URL is malformed") from error
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise BrowserCheckError("the browser URL must be one bare HTTP(S) origin")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise BrowserCheckError("a nonlocal theorem browser must use HTTPS")
    return parsed.scheme + "://" + parsed.netloc


def _same_origin(base: str, path: object) -> str:
    if type(path) is not str or not path or "\\" in path:
        raise BrowserCheckError("the browser service returned an unsafe URL")
    result = urljoin(base + "/", path)
    selected = urlsplit(result)
    expected = urlsplit(base)
    if (
        selected.scheme != expected.scheme
        or selected.netloc != expected.netloc
        or selected.username is not None
        or selected.password is not None
        or selected.fragment
    ):
        raise BrowserCheckError("the browser service returned a cross-origin URL")
    return result


def _request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    origin: str | None = None,
    additional_headers: dict[str, str] | None = None,
    require_cors: bool = False,
    maximum: int,
) -> bytes:
    data = None
    headers = {"Accept": "application/json, text/html, text/plain, application/zip"}
    if origin is not None:
        headers["Origin"] = origin
    if additional_headers is not None:
        headers.update(additional_headers)
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        selected = _verified_tls_context() if urlsplit(url).scheme == "https" else None
        options = {"timeout": 20}
        if selected is not None:
            options["context"] = selected
        with urlopen(request, **options) as response:
            if require_cors:
                if origin is None or response.headers.get("Access-Control-Allow-Origin") != origin:
                    raise BrowserCheckError(
                        "the proof service did not approve the exact public theorem-browser origin"
                    )
                if response.headers.get("Access-Control-Allow-Credentials", "").lower() == "true":
                    raise BrowserCheckError("the public proof service unexpectedly accepts credentials")
                if method == "OPTIONS":
                    approved = {
                        item.strip().upper()
                        for item in response.headers.get("Access-Control-Allow-Methods", "").split(",")
                    }
                    selected = headers.get("Access-Control-Request-Method", "").upper()
                    if selected not in approved:
                        raise BrowserCheckError(
                            "the proof service rejected its required cross-origin browser method"
                        )
                    requested = {
                        item.strip().lower()
                        for item in headers.get("Access-Control-Request-Headers", "").split(",")
                        if item.strip()
                    }
                    available = {
                        item.strip().lower()
                        for item in response.headers.get("Access-Control-Allow-Headers", "").split(",")
                    }
                    if not requested.issubset(available):
                        raise BrowserCheckError(
                            "the proof service rejected its required cross-origin browser headers"
                        )
            advertised = response.headers.get("Content-Length")
            if advertised is not None and (
                not advertised.isdecimal() or int(advertised) > maximum
            ):
                raise BrowserCheckError("the browser response exceeded its reviewed limit")
            content = response.read(maximum + 1)
    except HTTPError as error:
        detail = error.read(4_096).decode("utf-8", errors="replace")
        raise BrowserCheckError(f"browser request failed (HTTP {error.code}): {detail}") from error
    except (OSError, URLError, TimeoutError) as error:
        raise BrowserCheckError(f"could not reach the theorem browser: {error}") from error
    if len(content) > maximum:
        raise BrowserCheckError("the browser response exceeded its reviewed limit")
    return content


def _json_response(content: bytes) -> dict[str, object]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, ValueError) as error:
        raise BrowserCheckError("the theorem browser returned malformed JSON") from error
    if type(value) is not dict:
        raise BrowserCheckError("the theorem browser returned a non-object JSON response")
    return value


def _local_service_target(base: str) -> tuple[str, int] | None:
    """Allow an automatically managed service only on safe local HTTP origins."""

    parsed = urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        return None
    try:
        port = parsed.port or 80
    except ValueError as error:
        raise BrowserCheckError("the local browser port is not valid") from error
    if not 1 <= port <= 65_535:
        raise BrowserCheckError("the local browser port is not valid")
    return parsed.hostname, port


def _stop_local_service(process: subprocess.Popen[bytes], log: BinaryIO) -> None:
    """Stop only the exact temporary loopback server created by this checker."""

    try:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    finally:
        log.close()


def _start_local_service(base: str) -> tuple[subprocess.Popen[bytes], BinaryIO]:
    """Start the checked repository service without exposing a public listener."""

    target = _local_service_target(base)
    if target is None:
        raise BrowserCheckError("automatic browser startup is limited to local HTTP")
    host, port = target
    service = Path(__file__).resolve().with_name("serve_lean_strands.py")
    if service.is_symlink() or not service.is_file():
        raise BrowserCheckError("the local theorem-browser service script is unavailable")
    log = tempfile.TemporaryFile(mode="w+b")
    try:
        process = subprocess.Popen(
            [sys.executable, "-B", str(service), "--host", host, "--port", str(port)],
            cwd=str(service.parent.parent),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
    except OSError as error:
        log.close()
        raise BrowserCheckError(f"could not start the local theorem browser: {error}") from error

    deadline = time.monotonic() + SERVER_STARTUP_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log.seek(0)
            detail = log.read(4_096).decode("utf-8", errors="replace").strip()
            log.close()
            raise BrowserCheckError(
                "the temporary local theorem browser exited before startup"
                + (f": {detail}" if detail else "")
            )
        try:
            health = _json_response(
                _request(_same_origin(base, "/health"), maximum=MAX_JSON_BYTES)
            )
        except BrowserCheckError:
            time.sleep(0.1)
            continue
        if health.get("status") == "ok":
            return process, log
        _stop_local_service(process, log)
        raise BrowserCheckError("the temporary local theorem browser failed its health check")

    _stop_local_service(process, log)
    raise BrowserCheckError("the temporary local theorem browser exceeded its startup deadline")


def _check_live_url(url: object, source: bytes) -> None:
    if type(url) is not str or len(url.encode("utf-8")) > MAX_LIVE_URL_BYTES:
        raise BrowserCheckError("Lean Live did not receive a bounded share URL")
    try:
        parsed = urlsplit(url)
    except (UnicodeError, ValueError) as error:
        raise BrowserCheckError("Lean Live received an invalid source share") from error
    if (
        parsed.scheme != "https"
        or parsed.netloc != "live.lean-lang.org"
        or parsed.path not in {"", "/"}
        or parsed.query
    ):
        raise BrowserCheckError("Lean Live does not contain the exact downloaded proof")
    try:
        if parsed.fragment.startswith("code="):
            decoded = unquote(parsed.fragment[5:], errors="strict")
        elif parsed.fragment.startswith("codez="):
            encoded = parsed.fragment[6:]
            compressed = unquote(encoded, errors="strict")
            if quote(compressed, safe="") != encoded:
                raise ValueError("Lean Live compressed payload is not canonical Base64 URL text")
            python_root = str(Path(__file__).resolve().parents[1] / "peano-lab" / "py")
            if python_root not in sys.path:
                sys.path.insert(0, python_root)
            from peano_lab.library.lean_proof_strand import decompress_lean_live_codez

            decoded = decompress_lean_live_codez(
                compressed,
                max_output_bytes=max(1, min(len(source), MAX_SOURCE_BYTES)),
            )
        else:
            raise BrowserCheckError("Lean Live must contain an approved inline proof fragment")
    except (ImportError, UnicodeError, ValueError) as error:
        raise BrowserCheckError("Lean Live received an invalid source share") from error
    if decoded.encode("utf-8") != source:
        raise BrowserCheckError("Lean Live does not contain the exact downloaded proof")
    if (
        re.search(r"(?m)^\s*import\b", decoded)
        or re.search(r"\b(?:sorry|sorryAx|native_decide)\b", decoded)
        or re.search(r"(?m)^\s*axiom\b", decoded)
    ):
        raise BrowserCheckError("Lean Live source contains unavailable or unproved material")


def _check_archive(payload: bytes, theorem: str) -> tuple[int, int]:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            records = archive.infolist()
            if not records or len(records) > MAX_ARCHIVE_FILES:
                raise BrowserCheckError("the Lean project ZIP exceeds its file-count limit")
            names: set[str] = set()
            total = 0
            for record in records:
                path = PurePosixPath(record.filename)
                if (
                    not record.filename
                    or path.is_absolute()
                    or ".." in path.parts
                    or "\\" in record.filename
                    or record.filename in names
                ):
                    raise BrowserCheckError("the Lean project ZIP contains an unsafe entry")
                total += record.file_size
                if total > MAX_ARCHIVE_BYTES:
                    raise BrowserCheckError("the Lean project ZIP exceeds its source-size limit")
                names.add(record.filename)
            required = {"PeanoLab/Presentation.lean", "manifest.json", "README.txt"}
            missing = required.difference(names)
            if missing:
                raise BrowserCheckError(
                    "the downloadable Lean package is incomplete: " + ", ".join(sorted(missing))
                )
            private_companion = {
                "lakefile.toml",
                "lake-manifest.json",
                "lean-toolchain",
                "PeanoLab.lean",
                "PeanoLab/Codec.lean",
                "PeanoLab/Checker.lean",
                "PeanoLab/Soundness.lean",
            }.intersection(names)
            if private_companion:
                raise BrowserCheckError(
                    "the Lean package unexpectedly exports separate companion source: "
                    + ", ".join(sorted(private_companion))
                )
            if not any(
                name.startswith("PeanoLab/Generated/") and name.endswith("/Strand.lean")
                for name in names
            ):
                raise BrowserCheckError("the Lean package is missing its named theorem strand")
            catalog = _json_response(archive.read("manifest.json"))
            strands = catalog.get("strands")
            entry = (
                next(iter(strands.values()))
                if type(strands) is dict and len(strands) == 1
                else None
            )
            if (
                catalog.get("schema") != "peano-lean-proof-strand-package-v1"
                or type(entry) is not dict
                or entry.get("name") != theorem
            ):
                raise BrowserCheckError("the Lean package manifest does not match its selected theorem")
            return len(records), total
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        raise BrowserCheckError("the downloaded Lean package ZIP is invalid") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--site-url",
        help="public HTTPS theorem-browser origin when checking deployed proof pages",
    )
    parser.add_argument(
        "--graph-path",
        help="same-origin graph path; defaults to the local or deployed theorem explorer",
    )
    parser.add_argument(
        "--selector-path",
        help="same-origin selector JavaScript path; defaults to the local or deployed asset",
    )
    parser.add_argument("--theorem", default="add_comm")
    parser.add_argument("--edition", choices=("stable", "alpha"), default="stable")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument(
        "--require-running",
        action="store_true",
        help="fail instead of temporarily starting a missing local browser service",
    )
    parser.add_argument(
        "--allow-non-live",
        action="store_true",
        help="accept larger or certificate-backed proofs without a Lean Live share",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    job_url: str | None = None
    terminal = False
    managed_service: subprocess.Popen[bytes] | None = None
    service_log: BinaryIO | None = None
    try:
        base = _base_url(options.base_url)
        site = base if options.site_url is None else _base_url(options.site_url)
        cross_origin = site != base
        graph_path = options.graph_path or (
            "/proofs/quadratic-reciprocity/explorer/graph.html?target=PA000G"
            if options.site_url is not None
            else "/book/_static/pa-proof-explorer/graph.html?target=PA000F"
        )
        selector_path = options.selector_path or (
            "/proofs/assets/lean-selector.js"
            if options.site_url is not None
            else "/book/_static/lean-selector/lean-selector.js"
        )

        def api_request(
            url: str,
            *,
            method: str = "GET",
            payload: dict[str, object] | None = None,
            maximum: int,
        ) -> bytes:
            return _request(
                url,
                method=method,
                payload=payload,
                origin=site if cross_origin else None,
                require_cors=cross_origin,
                maximum=maximum,
            )

        if THEOREM.fullmatch(options.theorem) is None:
            raise BrowserCheckError("the theorem name is not a bounded safe identifier")
        if not 5 <= options.timeout <= 1_200:
            raise BrowserCheckError("the smoke-test timeout must be between 5 and 1,200 seconds")

        configuration_url = _same_origin(base, API_ROOT + "/config")
        try:
            configuration = _json_response(
                api_request(configuration_url, maximum=MAX_JSON_BYTES)
            )
        except BrowserCheckError as error:
            if (
                options.require_running
                or _local_service_target(base) is None
                or not str(error).startswith("could not reach the theorem browser:")
            ):
                raise
            print("No local theorem browser is running; starting a temporary loopback service…", flush=True)
            managed_service, service_log = _start_local_service(base)
            print("✓ Temporary local theorem browser is ready", flush=True)
            configuration = _json_response(
                api_request(configuration_url, maximum=MAX_JSON_BYTES)
            )
        if (
            configuration.get("single_worker") is not True
            or configuration.get("independent_lean_verification") is not True
        ):
            raise BrowserCheckError("the theorem browser did not advertise bounded Lean verification")
        print(
            "✓ One bounded Lean worker; memory ceiling "
            + str(configuration.get("max_memory_mib"))
            + " MiB",
            flush=True,
        )
        if cross_origin:
            configured = configuration.get("allowed_origins")
            if type(configured) is not list or site not in configured:
                raise BrowserCheckError(
                    "the external Lean backend does not explicitly approve the public browser"
                )
            _request(
                _same_origin(base, API_ROOT + "/jobs"),
                method="OPTIONS",
                origin=site,
                additional_headers={
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
                require_cors=True,
                maximum=MAX_JSON_BYTES,
            )
            print("✓ External HTTPS Lean backend approves only its configured browser origin", flush=True)

        graph = _request(
            _same_origin(site, graph_path),
            maximum=MAX_HTML_BYTES,
        )
        if b"lean-selector.js" not in graph or b"lean-selector.css" not in graph:
            raise BrowserCheckError("the selected-theorem browser controls were not installed")
        selector = _request(
            _same_origin(site, selector_path),
            maximum=MAX_SOURCE_BYTES,
        )
        if b"PeanoLeanSelector" not in selector:
            raise BrowserCheckError("the theorem browser did not expose its selected-node controls")
        print("✓ Existing theorem graph includes its interactive Lean sidebar", flush=True)

        created = _json_response(
            api_request(
                _same_origin(base, API_ROOT + "/jobs"),
                method="POST",
                payload={"theorem": options.theorem, "edition": options.edition},
                maximum=MAX_JSON_BYTES,
            )
        )
        identifier = created.get("job_id")
        if type(identifier) is not str or JOB_ID.fullmatch(identifier) is None:
            raise BrowserCheckError("the theorem browser returned an unsafe proof-job identifier")
        job_url = _same_origin(base, API_ROOT + "/jobs/" + identifier)
        deadline = time.monotonic() + options.timeout
        last_progress: tuple[object, object, object] | None = None
        snapshot = created
        while True:
            status = snapshot.get("status")
            progress = (
                snapshot.get("stage"),
                snapshot.get("completed"),
                snapshot.get("total"),
            )
            if progress != last_progress:
                print(f"  {progress[0]}: {progress[1]} / {progress[2]}", flush=True)
                last_progress = progress
            if status in {"completed", "failed", "cancelled"}:
                terminal = True
                break
            if time.monotonic() >= deadline:
                raise BrowserCheckError("the checked browser proof exceeded its requested timeout")
            time.sleep(0.5)
            snapshot = _json_response(api_request(job_url, maximum=MAX_JSON_BYTES))

        if snapshot.get("status") != "completed" or snapshot.get("lean_verified") is not True:
            detail = snapshot.get("error") or snapshot.get("diagnostics") or snapshot.get("status")
            raise BrowserCheckError(f"the selected theorem was not independently Lean checked: {detail}")
        manifest = snapshot.get("manifest")
        if (
            type(manifest) is not dict
            or manifest.get("name") != options.theorem
            or manifest.get("edition") != options.edition
        ):
            raise BrowserCheckError("the browser proof manifest does not match the requested theorem")
        print(
            f"✓ Lean verified {manifest.get('node_count')} theorem nodes "
            f"({manifest.get('fallback_node_count')} certificate fallbacks)",
            flush=True,
        )

        downloads = snapshot.get("downloads")
        if type(downloads) is not dict:
            raise BrowserCheckError("the checked theorem has no safe download links")
        source = api_request(_same_origin(base, downloads.get("lean")), maximum=MAX_SOURCE_BYTES)
        live_url = snapshot.get("live_url")
        if live_url is not None:
            receipt = snapshot.get("lean_live")
            encoding = "codez" if "#codez=" in live_url else "code"
            if (
                type(receipt) is not dict
                or receipt.get("local_source_verified") is not True
                or receipt.get("self_contained") is not True
                or receipt.get("core_imports") != []
                or receipt.get("external_import_count") != 0
                or receipt.get("source_sha256") != sha256(source).hexdigest()
                or receipt.get("share_encoding") != encoding
                or manifest.get("fallback_node_count") != 0
            ):
                raise BrowserCheckError(
                    "Lean Live lacks an authenticated, locally compiled, import-free proof receipt"
                )
            _check_live_url(live_url, source)
            displayed_encoding = "compressed" if encoding == "codez" else "uncompressed"
            print(
                f"✓ Exact import-free standalone proof opens in Lean Live "
                f"({len(source):,} source bytes, "
                f"{len(live_url.encode('utf-8')):,} {displayed_encoding} URL bytes)",
                flush=True,
            )
        elif not options.allow_non_live:
            raise BrowserCheckError("the selected theorem did not produce a directly usable Lean Live share")

        payload = api_request(
            _same_origin(base, downloads.get("zip")),
            maximum=MAX_ARCHIVE_BYTES,
        )
        count, size = _check_archive(payload, options.theorem)
        print(
            f"✓ Verified Lean package contains {count} generated files "
            f"({size:,} uncompressed bytes; SHA-256 {sha256(payload).hexdigest()[:16]}…)",
            flush=True,
        )
        print("The interactive Lean theorem browser passed its complete live smoke test.")
        return 0
    except (BrowserCheckError, KeyboardInterrupt) as error:
        print(f"Lean browser check failed: {error}", file=sys.stderr)
        return 1
    finally:
        if job_url is not None and not terminal:
            try:
                api_request(job_url, method="DELETE", maximum=MAX_JSON_BYTES)
            except BrowserCheckError:
                pass
        if managed_service is not None and service_log is not None:
            _stop_local_service(managed_service, service_log)
            print("✓ Temporary local theorem browser stopped", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
