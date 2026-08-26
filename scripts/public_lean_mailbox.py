#!/usr/bin/env python3
"""Bridge the faculty PHP node to one owner-private, loopback Lean worker.

The SSH login node and public PHP node are different machines, but their owner
home directory is shared over NFS.  This foreground Python 3.8-compatible
broker claims tightly bounded proof requests from ``~/.hydra-lean-mailbox`` and
relays only reviewed API routes through the existing login-node SSH forward.
Neither the mailbox nor generated proof artifacts belong under ``public_html``.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
from typing import Any, BinaryIO, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit


SCHEMA = "peano-lean-mailbox-v1"
JOB_SCHEMA = "peano-lean-strand-service-v1"
DIRECTORY_NAME = ".hydra-lean-mailbox"
API_PREFIX = "/api/lean-strands"
UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 18787
WORKER_HOST = "127.0.0.1:8787"
MAX_REQUEST_BYTES = 16 * 1024
MAX_ENVELOPE_BYTES = 32 * 1024
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
MAX_JSON_BYTES = 3 * 1024 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_METADATA_BYTES = 8 * 1024
MAX_TARGET_BYTES = 4096
MAX_QUEUE_ENTRIES = 1024
MAX_REQUESTS_PER_PASS = 32
DEFAULT_TTL_SECONDS = 30
DEFAULT_POLL_SECONDS = 0.15
IDENTIFIER = re.compile(r"[0-9a-f]{32}\Z")
REQUEST_NAME = re.compile(r"([0-9a-f]{32})\.request\.json\Z")
QUEUE_NAME = re.compile(
    r"[0-9a-f]{32}\.(?:request\.json|processing\.json|response\.json|body)\Z"
)
TEMPORARY_NAME = re.compile(r"\.[0-9a-f]{32}\.[a-z]+\.[0-9a-f]{16}\.tmp\Z")
ROUTE = re.compile(
    r"/api/lean-strands/(?:config|health|jobs(?:/[0-9a-f]{32}(?:/download)?)?)\Z"
)
JOB_ROUTE = re.compile(r"/api/lean-strands/jobs/[0-9a-f]{32}\Z")
DOWNLOAD_ROUTE = re.compile(r"/api/lean-strands/jobs/[0-9a-f]{32}/download\Z")
DISPOSITION = re.compile(r'attachment; filename="[A-Za-z0-9_.-]{1,128}"\Z')
CONTENT_TYPES = {
    "application/json; charset=utf-8": MAX_JSON_BYTES,
    "application/json": MAX_JSON_BYTES,
    "application/zip": MAX_RESPONSE_BYTES,
    "text/plain; charset=utf-8": MAX_SOURCE_BYTES,
}


class MailboxError(ValueError):
    """The owner-private mailbox or its reviewed proof protocol is unsafe."""


def _strict_object(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    selected = {}  # type: Dict[str, Any]
    for key, value in pairs:
        if key in selected:
            raise MailboxError("mailbox JSON contains a duplicate object key")
        selected[key] = value
    return selected


def _reject_constant(_value: str) -> None:
    raise MailboxError("mailbox JSON contains a non-finite constant")


def _strict_json(content: bytes, *, maximum: int) -> Dict[str, Any]:
    if not content or len(content) > maximum:
        raise MailboxError("mailbox JSON exceeds its reviewed byte budget")
    try:
        selected = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError) as error:
        raise MailboxError("mailbox payload is not strict UTF-8 JSON") from error
    if type(selected) is not dict:
        raise MailboxError("mailbox payload must be exactly one JSON object")
    return selected


def _encoded_json(payload: Dict[str, Any], *, maximum: int) -> bytes:
    try:
        result = (
            json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    except (TypeError, UnicodeError, ValueError) as error:
        raise MailboxError("mailbox response cannot be encoded as strict JSON") from error
    if len(result) > maximum:
        raise MailboxError("mailbox response metadata exceeds its reviewed byte budget")
    return result


def _private_directory(path: Path, *, create: bool) -> Path:
    selected = path.expanduser()
    if selected.name != DIRECTORY_NAME or "public_html" in selected.parts:
        raise MailboxError("proof mailbox must be private and outside the public web directory")
    if selected.is_symlink():
        raise MailboxError("proof mailbox directory must not be a symbolic link")
    if create:
        selected.mkdir(mode=0o700, parents=False, exist_ok=True)
    try:
        details = selected.lstat()
    except OSError as error:
        raise MailboxError("private proof mailbox directory is unavailable") from error
    if (
        not stat.S_ISDIR(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) != 0o700
    ):
        raise MailboxError("proof mailbox must be an owner-private 0700 real directory")
    return selected.resolve()


def _private_file(path: Path, *, maximum: Optional[int] = None) -> os.stat_result:
    try:
        details = path.lstat()
    except OSError as error:
        raise MailboxError("private proof mailbox file is unavailable") from error
    if (
        not stat.S_ISREG(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) != 0o600
        or details.st_nlink != 1
    ):
        raise MailboxError("proof mailbox files must be owner-private 0600 regular files")
    if maximum is not None and details.st_size > maximum:
        raise MailboxError("private proof mailbox file exceeds its reviewed size limit")
    return details


def _atomic_open(directory: Path, identifier: str, label: str) -> Tuple[Path, BinaryIO]:
    temporary = directory / (
        "." + identifier + "." + label + "." + secrets.token_hex(8) + ".tmp"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(temporary), flags, 0o600)
    return temporary, os.fdopen(descriptor, "wb")


def _publish(directory: Path, identifier: str, label: str, target: Path, content: bytes) -> None:
    if target.exists() or target.is_symlink():
        raise MailboxError("refusing to overwrite an existing private proof artifact")
    temporary, output = _atomic_open(directory, identifier, label)
    try:
        with output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(str(temporary), str(target))
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _request_payload(content: bytes, identifier: str) -> Tuple[str, str, bytes]:
    selected = _strict_json(content, maximum=MAX_ENVELOPE_BYTES)
    if set(selected) != {"schema", "id", "method", "target", "body_base64"}:
        raise MailboxError("proof mailbox request has an unreviewed envelope shape")
    if selected["schema"] != SCHEMA or selected["id"] != identifier:
        raise MailboxError("proof mailbox request has the wrong schema or opaque identifier")
    method = selected["method"]
    target = selected["target"]
    encoded = selected["body_base64"]
    if method not in {"GET", "HEAD", "POST", "DELETE"}:
        raise MailboxError("unsupported proof mailbox request method")
    if (
        type(target) is not str
        or len(target) > MAX_TARGET_BYTES
        or not target.isascii()
        or any(ord(character) < 33 or ord(character) > 126 for character in target)
        or "\\" in target
    ):
        raise MailboxError("proof mailbox request target is unsafe")
    try:
        parsed = urlsplit(target)
    except ValueError as error:
        raise MailboxError("proof mailbox request target is malformed") from error
    if parsed.scheme or parsed.netloc or parsed.fragment or ROUTE.fullmatch(parsed.path) is None:
        raise MailboxError("proof mailbox request target is not explicitly approved")
    is_download = DOWNLOAD_ROUTE.fullmatch(parsed.path) is not None
    if is_download:
        if parsed.query not in {"format=lean", "format=zip"}:
            raise MailboxError("proof downloads require one exact approved format")
    elif parsed.query:
        raise MailboxError("proof mailbox requests do not accept unrelated query strings")
    if method == "POST" and parsed.path != API_PREFIX + "/jobs":
        raise MailboxError("POST is restricted to reviewed proof-job creation")
    if method == "DELETE" and JOB_ROUTE.fullmatch(parsed.path) is None:
        raise MailboxError("DELETE requires one exact opaque proof-job identifier")
    if is_download and method not in {"GET", "HEAD"}:
        raise MailboxError("proof downloads do not accept mutation requests")
    if type(encoded) is not str or len(encoded) > ((MAX_REQUEST_BYTES + 2) // 3) * 4:
        raise MailboxError("proof mailbox request body exceeds its reviewed limit")
    try:
        body = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeError, ValueError, binascii.Error) as error:
        raise MailboxError("proof mailbox request body is not canonical Base64") from error
    if base64.b64encode(body).decode("ascii") != encoded or len(body) > MAX_REQUEST_BYTES:
        raise MailboxError("proof mailbox request body is not canonical bounded Base64")
    if method == "POST":
        _strict_json(body, maximum=MAX_REQUEST_BYTES)
    elif body:
        raise MailboxError("read-only and cancellation requests must not contain a body")
    return method, target, body


class MailboxBroker:
    """Serial owner-private NFS request broker for an existing Lean worker."""

    def __init__(
        self,
        directory: Path,
        *,
        upstream_port: int = UPSTREAM_PORT,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        timeout_seconds: float = 20.0,
        create: bool = True,
    ) -> None:
        if type(upstream_port) is not int or not 1 <= upstream_port <= 65535:
            raise MailboxError("loopback upstream port must be a bounded integer")
        if type(ttl_seconds) is not int or not 5 <= ttl_seconds <= 300:
            raise MailboxError("proof mailbox TTL must remain between five and 300 seconds")
        if not 1.0 <= timeout_seconds <= 60.0:
            raise MailboxError("proof mailbox upstream timeout exceeds its reviewed bounds")
        self.directory = _private_directory(directory, create=create)
        self.upstream_port = upstream_port
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds

    def _response_headers(self, response: http.client.HTTPResponse) -> Dict[str, Any]:
        selected = {}  # type: Dict[str, str]
        for name, value in response.getheaders():
            lowered = name.lower()
            if lowered in {"content-type", "content-length", "content-disposition"}:
                if lowered in selected:
                    raise MailboxError("loopback proof worker returned duplicate response headers")
                selected[lowered] = value
        kind = selected.get("content-type", "")
        length = selected.get("content-length", "")
        if kind not in CONTENT_TYPES or not length.isdecimal() or len(length) > 8:
            raise MailboxError("loopback proof worker returned unsafe response metadata")
        size = int(length)
        if size > CONTENT_TYPES[kind]:
            raise MailboxError("loopback proof response exceeds its reviewed byte budget")
        result = {"content_type": kind, "content_length": size}  # type: Dict[str, Any]
        if "content-disposition" in selected:
            disposition = selected["content-disposition"]
            if DISPOSITION.fullmatch(disposition) is None:
                raise MailboxError("loopback proof worker supplied an unsafe download filename")
            result["content_disposition"] = disposition
        return result

    def _publish_response(
        self,
        identifier: str,
        status: int,
        headers: Dict[str, Any],
        *,
        source: Optional[http.client.HTTPResponse] = None,
        content: Optional[bytes] = None,
        head_only: bool = False,
    ) -> None:
        body_path = self.directory / (identifier + ".body")
        metadata_path = self.directory / (identifier + ".response.json")
        if body_path.exists() or body_path.is_symlink() or metadata_path.exists() or metadata_path.is_symlink():
            raise MailboxError("refusing to overwrite an existing private proof response")
        temporary, output = _atomic_open(self.directory, identifier, "body")
        digest = hashlib.sha256()
        remaining = 0 if head_only else headers["content_length"]
        written = 0
        try:
            with output:
                if content is not None and not head_only:
                    if len(content) != remaining:
                        raise MailboxError("private proof error response has inconsistent length")
                    output.write(content)
                    digest.update(content)
                    written = len(content)
                elif source is not None:
                    while remaining:
                        chunk = source.read(min(65536, remaining))
                        if not chunk or len(chunk) > remaining:
                            raise MailboxError("loopback proof worker returned an incomplete response")
                        output.write(chunk)
                        digest.update(chunk)
                        written += len(chunk)
                        remaining -= len(chunk)
                elif not head_only:
                    raise MailboxError("private proof response does not contain a body")
                output.flush()
                os.fsync(output.fileno())
            os.replace(str(temporary), str(body_path))
            payload = {
                "schema": SCHEMA,
                "id": identifier,
                "status": status,
                "headers": headers,
                "body_bytes": written,
                "body_sha256": digest.hexdigest(),
            }
            _publish(
                self.directory,
                identifier,
                "response",
                metadata_path,
                _encoded_json(payload, maximum=MAX_METADATA_BYTES),
            )
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _failure(self, identifier: str, status: int, message: str) -> None:
        body = _encoded_json(
            {"schema": JOB_SCHEMA, "error": message},
            maximum=MAX_JSON_BYTES,
        )
        self._publish_response(
            identifier,
            status,
            {"content_type": "application/json; charset=utf-8", "content_length": len(body)},
            content=body,
        )

    def _forward(self, identifier: str, method: str, target: str, body: bytes) -> None:
        connection = http.client.HTTPConnection(
            UPSTREAM_HOST,
            self.upstream_port,
            timeout=self.timeout_seconds,
        )
        headers = {"Host": WORKER_HOST, "Connection": "close", "Accept": "application/json"}
        if method == "POST":
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        try:
            connection.request(method, target, body=body if method == "POST" else None, headers=headers)
            response = connection.getresponse()
            if type(response.status) is not int or not 100 <= response.status <= 599:
                raise MailboxError("loopback proof worker returned an unsafe HTTP status")
            selected = self._response_headers(response)
            self._publish_response(
                identifier,
                response.status,
                selected,
                source=response,
                head_only=method == "HEAD",
            )
        finally:
            connection.close()

    def _claim(self, path: Path, identifier: str) -> Optional[Path]:
        _private_file(path, maximum=MAX_ENVELOPE_BYTES)
        claimed = self.directory / (identifier + ".processing.json")
        if claimed.exists() or claimed.is_symlink():
            return None
        try:
            os.replace(str(path), str(claimed))
        except FileNotFoundError:
            return None
        _private_file(claimed, maximum=MAX_ENVELOPE_BYTES)
        return claimed

    def _process(self, path: Path, identifier: str) -> bool:
        claimed = self._claim(path, identifier)
        if claimed is None:
            return False
        try:
            try:
                with claimed.open("rb") as stream:
                    content = stream.read(MAX_ENVELOPE_BYTES + 1)
                method, target, body = _request_payload(content, identifier)
            except (MailboxError, OSError) as error:
                self._failure(identifier, 400, "The public proof request was rejected.")
                print("Rejected private proof request: " + str(error), file=sys.stderr, flush=True)
                return True
            try:
                self._forward(identifier, method, target, body)
            except (http.client.HTTPException, MailboxError, OSError) as error:
                body_path = self.directory / (identifier + ".body")
                if body_path.exists() and not body_path.is_symlink():
                    _private_file(body_path, maximum=MAX_RESPONSE_BYTES)
                    body_path.unlink()
                self._failure(identifier, 503, "The public Lean proof worker is temporarily unavailable.")
                print("Private proof upstream unavailable: " + str(error), file=sys.stderr, flush=True)
            return True
        finally:
            if claimed.exists() and not claimed.is_symlink():
                claimed.unlink()

    def _cleanup(self, entries: List[os.DirEntry]) -> None:
        cutoff = time.time() - self.ttl_seconds
        for entry in entries:
            if QUEUE_NAME.fullmatch(entry.name) is None and TEMPORARY_NAME.fullmatch(entry.name) is None:
                continue
            try:
                details = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if (
                stat.S_ISREG(details.st_mode)
                and details.st_uid == os.getuid()
                and stat.S_IMODE(details.st_mode) == 0o600
                and details.st_mtime < cutoff
            ):
                try:
                    Path(entry.path).unlink()
                except OSError:
                    continue

    def run_once(self) -> int:
        _private_directory(self.directory, create=False)
        with os.scandir(str(self.directory)) as scanner:
            entries = list(scanner)
        if len(entries) > MAX_QUEUE_ENTRIES:
            raise MailboxError("private proof mailbox exceeded its reviewed entry budget")
        self._cleanup(entries)
        candidates = []  # type: List[Tuple[Path, str]]
        for entry in entries:
            selected = REQUEST_NAME.fullmatch(entry.name)
            if selected is not None:
                candidate = Path(entry.path)
                if candidate.exists() or candidate.is_symlink():
                    candidates.append((candidate, selected.group(1)))
        candidates.sort(key=lambda item: item[0].name)
        processed = 0
        for candidate, identifier in candidates[:MAX_REQUESTS_PER_PASS]:
            if self._process(candidate, identifier):
                processed += 1
        return processed

    def serve(self, *, poll_seconds: float = DEFAULT_POLL_SECONDS) -> None:
        if not 0.05 <= poll_seconds <= 5.0:
            raise MailboxError("private proof-mailbox polling exceeds its reviewed bounds")
        while True:
            if not self.run_once():
                time.sleep(poll_seconds)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path.home() / DIRECTORY_NAME)
    parser.add_argument("--upstream-port", type=int, default=UPSTREAM_PORT)
    parser.add_argument("--ttl-seconds", type=int, default=DEFAULT_TTL_SECONDS)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--once", action="store_true", help="process one bounded mailbox scan")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        broker = MailboxBroker(
            arguments.directory,
            upstream_port=arguments.upstream_port,
            ttl_seconds=arguments.ttl_seconds,
        )
        if arguments.once:
            broker.run_once()
        else:
            broker.serve(poll_seconds=arguments.poll_seconds)
        return 0
    except KeyboardInterrupt:
        return 0
    except (MailboxError, OSError) as error:
        print("Private Lean mailbox: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
