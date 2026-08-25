#!/usr/bin/env python3
"""Exercise the real theorem-browser service with one bounded checked proof."""

from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import PurePosixPath
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
import zipfile


DEFAULT_BASE_URL = "http://127.0.0.1:8787"
API_ROOT = "/api/lean-strands"
MAX_HTML_BYTES = 4 * 1024 * 1024
MAX_JSON_BYTES = 512 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_FILES = 4_096
MAX_LIVE_URL_BYTES = 8_192
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
THEOREM = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,127}\Z")


class BrowserCheckError(ValueError):
    """The live browser service did not establish its claimed proof workflow."""


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
    maximum: int,
) -> bytes:
    data = None
    headers = {"Accept": "application/json, text/html, text/plain, application/zip"}
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
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


def _check_live_url(url: object, source: bytes) -> None:
    if type(url) is not str or len(url.encode("utf-8")) > MAX_LIVE_URL_BYTES:
        raise BrowserCheckError("Lean Live did not receive a bounded share URL")
    try:
        parsed = urlsplit(url)
        decoded = unquote(parsed.fragment.removeprefix("code="), errors="strict")
    except (UnicodeError, ValueError) as error:
        raise BrowserCheckError("Lean Live received an invalid source share") from error
    if (
        parsed.scheme != "https"
        or parsed.netloc != "live.lean-lang.org"
        or parsed.path not in {"", "/"}
        or parsed.query
        or not parsed.fragment.startswith("code=")
        or decoded.encode("utf-8") != source
    ):
        raise BrowserCheckError("Lean Live does not contain the exact downloaded proof")
    if (
        re.search(r"(?m)^\s*import\s+(?!Lean(?:\.Elab\.Tactic)?\s*$)", decoded)
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
    parser.add_argument("--theorem", default="add_comm")
    parser.add_argument("--edition", choices=("stable", "alpha"), default="stable")
    parser.add_argument("--timeout", type=int, default=240)
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
    try:
        base = _base_url(options.base_url)
        if THEOREM.fullmatch(options.theorem) is None:
            raise BrowserCheckError("the theorem name is not a bounded safe identifier")
        if not 5 <= options.timeout <= 1_200:
            raise BrowserCheckError("the smoke-test timeout must be between 5 and 1,200 seconds")

        configuration = _json_response(
            _request(_same_origin(base, API_ROOT + "/config"), maximum=MAX_JSON_BYTES)
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

        graph = _request(
            _same_origin(base, "/book/_static/pa-proof-explorer/graph.html?target=PA000F"),
            maximum=MAX_HTML_BYTES,
        )
        if b"lean-selector.js" not in graph or b"lean-selector.css" not in graph:
            raise BrowserCheckError("the selected-theorem browser controls were not installed")
        selector = _request(
            _same_origin(base, "/book/_static/lean-selector/lean-selector.js"),
            maximum=MAX_SOURCE_BYTES,
        )
        if b"PeanoLeanSelector" not in selector:
            raise BrowserCheckError("the theorem browser did not expose its selected-node controls")
        print("✓ Existing theorem graph includes its interactive Lean sidebar", flush=True)

        created = _json_response(
            _request(
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
            snapshot = _json_response(_request(job_url, maximum=MAX_JSON_BYTES))

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
        source = _request(_same_origin(base, downloads.get("lean")), maximum=MAX_SOURCE_BYTES)
        live_url = snapshot.get("live_url")
        if live_url is not None:
            _check_live_url(live_url, source)
            print(
                f"✓ Exact standalone proof opens in Lean Live "
                f"({len(source):,} source bytes, {len(live_url.encode('utf-8')):,} URL bytes)",
                flush=True,
            )
        elif not options.allow_non_live:
            raise BrowserCheckError("the selected theorem did not produce a directly usable Lean Live share")

        payload = _request(
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
                _request(job_url, method="DELETE", maximum=MAX_JSON_BYTES)
            except BrowserCheckError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
