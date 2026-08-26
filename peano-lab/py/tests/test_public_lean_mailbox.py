"""Adversarial checks for the private, Python-3.8-compatible NFS proof broker."""

from __future__ import annotations

import ast
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import public_lean_mailbox as mailbox  # noqa: E402


IDENTIFIER = "a" * 32


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        kind: str = "application/json; charset=utf-8",
        length: int | None = None,
        disposition: str | None = None,
    ) -> None:
        self.body = body
        self.status = status
        self.offset = 0
        self.headers = [
            ("Content-Type", kind),
            ("Content-Length", str(len(body) if length is None else length)),
        ]
        if disposition is not None:
            self.headers.append(("Content-Disposition", disposition))

    def getheaders(self) -> list[tuple[str, str]]:
        return self.headers

    def read(self, maximum: int) -> bytes:
        selected = self.body[self.offset:self.offset + maximum]
        self.offset += len(selected)
        return selected


class FakeConnection:
    def __init__(self, response: FakeResponse | BaseException) -> None:
        self.response = response
        self.calls: list[tuple[str, str, bytes | None, dict[str, str]]] = []
        self.closed = False

    def request(
        self,
        method: str,
        target: str,
        *,
        body: bytes | None,
        headers: dict[str, str],
    ) -> None:
        self.calls.append((method, target, body, headers))

    def getresponse(self) -> FakeResponse:
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response

    def close(self) -> None:
        self.closed = True


@pytest.fixture()
def private_directory(tmp_path: Path) -> Path:
    return tmp_path / mailbox.DIRECTORY_NAME


@pytest.fixture()
def broker(private_directory: Path) -> mailbox.MailboxBroker:
    return mailbox.MailboxBroker(private_directory)


def create_request(
    directory: Path,
    *,
    identifier: str = IDENTIFIER,
    method: str = "GET",
    target: str = "/api/lean-strands/config",
    body: bytes = b"",
    changes: dict[str, Any] | None = None,
) -> Path:
    payload = {
        "schema": mailbox.SCHEMA,
        "id": identifier,
        "method": method,
        "target": target,
        "body_base64": base64.b64encode(body).decode("ascii"),
    }
    if changes is not None:
        payload.update(changes)
    destination = directory / (identifier + ".request.json")
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return destination


def fake_upstream(
    monkeypatch: pytest.MonkeyPatch,
    selected: FakeResponse | BaseException,
) -> FakeConnection:
    connection = FakeConnection(selected)

    def factory(host: str, port: int, *, timeout: float) -> FakeConnection:
        assert host == "127.0.0.1"
        assert port == 18787
        assert timeout == 20.0
        return connection

    monkeypatch.setattr(mailbox.http.client, "HTTPConnection", factory)
    return connection


def read_response(directory: Path, identifier: str = IDENTIFIER) -> tuple[dict[str, Any], bytes]:
    metadata = directory / (identifier + ".response.json")
    body = directory / (identifier + ".body")
    assert metadata.stat().st_mode & 0o777 == 0o600
    assert body.stat().st_mode & 0o777 == 0o600
    selected = json.loads(metadata.read_text(encoding="utf-8"))
    content = body.read_bytes()
    assert selected["body_bytes"] == len(content)
    assert selected["body_sha256"] == sha256(content).hexdigest()
    return selected, content


def test_remote_broker_source_is_python_38_compatible() -> None:
    source = (SCRIPTS / "public_lean_mailbox.py").read_text(encoding="utf-8")
    ast.parse(source, feature_version=(3, 8))


def test_private_owner_mailbox_is_created_outside_public_web_root(
    broker: mailbox.MailboxBroker,
) -> None:
    assert broker.directory.name == ".hydra-lean-mailbox"
    assert broker.directory.stat().st_uid == os.getuid()
    assert broker.directory.stat().st_mode & 0o777 == 0o700


def test_mailbox_rejects_public_web_root_even_if_private(tmp_path: Path) -> None:
    public = tmp_path / "public_html"
    public.mkdir()
    with pytest.raises(mailbox.MailboxError, match="outside the public"):
        mailbox.MailboxBroker(public / mailbox.DIRECTORY_NAME)


@pytest.mark.parametrize("mode", [0o755, 0o777, 0o733, 0o1733])
def test_mailbox_rejects_nonprivate_directory_permissions(tmp_path: Path, mode: int) -> None:
    directory = tmp_path / mailbox.DIRECTORY_NAME
    directory.mkdir(mode=0o700)
    directory.chmod(mode)
    with pytest.raises(mailbox.MailboxError, match="0700"):
        mailbox.MailboxBroker(directory, create=False)


def test_mailbox_rejects_directory_symlinks(tmp_path: Path) -> None:
    outside = tmp_path / "actual"
    outside.mkdir(mode=0o700)
    selected = tmp_path / mailbox.DIRECTORY_NAME
    selected.symlink_to(outside, target_is_directory=True)
    with pytest.raises(mailbox.MailboxError, match="symbolic link"):
        mailbox.MailboxBroker(selected)


def test_public_config_round_trip_is_exact_and_owner_private(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b'{"schema":"peano-lean-strand-service-v1","single_worker":true}\n'
    connection = fake_upstream(monkeypatch, FakeResponse(content))
    create_request(broker.directory)

    assert broker.run_once() == 1
    result, returned = read_response(broker.directory)
    assert returned == content
    assert result == {
        "schema": mailbox.SCHEMA,
        "id": IDENTIFIER,
        "status": 200,
        "headers": {
            "content_type": "application/json; charset=utf-8",
            "content_length": len(content),
        },
        "body_bytes": len(content),
        "body_sha256": sha256(content).hexdigest(),
    }
    assert connection.calls == [
        (
            "GET",
            "/api/lean-strands/config",
            None,
            {
                "Host": "127.0.0.1:8787",
                "Connection": "close",
                "Accept": "application/json",
            },
        )
    ]
    assert connection.closed is True
    assert not (broker.directory / (IDENTIFIER + ".request.json")).exists()
    assert not (broker.directory / (IDENTIFIER + ".processing.json")).exists()


def test_bounded_theorem_job_body_reaches_only_the_reviewed_local_worker(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b'{"status":"queued"}\n'
    connection = fake_upstream(monkeypatch, FakeResponse(content, status=202))
    original = b'{"theorem":"add_comm","edition":"stable"}'
    create_request(
        broker.directory,
        method="POST",
        target="/api/lean-strands/jobs",
        body=original,
    )

    assert broker.run_once() == 1
    response, returned = read_response(broker.directory)
    assert response["status"] == 202
    assert returned == content
    assert connection.calls[0][2] == original
    assert connection.calls[0][3]["Host"] == "127.0.0.1:8787"
    assert connection.calls[0][3]["Content-Type"] == "application/json"
    assert connection.calls[0][3]["Content-Length"] == str(len(original))


def test_head_preserves_representation_length_without_writing_a_body(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_upstream(monkeypatch, FakeResponse(b"", length=420))
    create_request(broker.directory, method="HEAD")

    assert broker.run_once() == 1
    metadata, body = read_response(broker.directory)
    assert metadata["headers"]["content_length"] == 420
    assert metadata["body_bytes"] == 0
    assert body == b""


@pytest.mark.parametrize(
    ("kind", "query", "disposition"),
    [
        (
            "text/plain; charset=utf-8",
            "format=lean",
            'attachment; filename="readable-standalone.lean"',
        ),
        (
            "application/zip",
            "format=zip",
            'attachment; filename="verified-lean-proof.zip"',
        ),
    ],
)
def test_checked_proof_downloads_remain_private_and_integrity_checked(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    query: str,
    disposition: str,
) -> None:
    original = (b"theorem checked : True := by trivial\n" * 3000)[:90000]
    fake_upstream(monkeypatch, FakeResponse(original, kind=kind, disposition=disposition))
    create_request(
        broker.directory,
        target="/api/lean-strands/jobs/" + "b" * 32 + "/download?" + query,
    )

    assert broker.run_once() == 1
    metadata, content = read_response(broker.directory)
    assert content == original
    assert metadata["headers"]["content_type"] == kind
    assert metadata["headers"]["content_disposition"] == disposition


@pytest.mark.parametrize(
    "changes",
    [
        {"schema": "forged"},
        {"id": "b" * 32},
        {"method": "PUT"},
        {"method": "POST", "target": "/api/lean-strands/config"},
        {"method": "DELETE", "target": "/api/lean-strands/jobs"},
        {"target": "https://evil.invalid/private"},
        {"target": "//evil.invalid/api/lean-strands/config"},
        {"target": "/api/lean-strands/config?private=1"},
        {"target": "/api/lean-strands/jobs/" + "b" * 32 + "/events"},
        {"target": "/api/lean-strands/jobs/" + "b" * 32 + "/download?format=exe"},
        {"target": "/api/lean-strands/jobs/" + "b" * 32 + "/download?format=zip&x=1"},
        {"target": "/api/lean-strands/../.ssh/id_ed25519"},
        {"target": "/api/lean-strands/config\r\nHost:evil.invalid"},
        {"body_base64": "!!!!"},
        {"body_base64": "YQ=="},
        {"unexpected": "secret"},
    ],
)
def test_untrusted_mailbox_requests_fail_closed_without_network_access(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, Any],
) -> None:
    connection = fake_upstream(monkeypatch, FakeResponse(b"never"))
    create_request(broker.directory, changes=changes)

    assert broker.run_once() == 1
    metadata, content = read_response(broker.directory)
    assert metadata["status"] == 400
    assert json.loads(content) == {
        "schema": mailbox.JOB_SCHEMA,
        "error": "The public proof request was rejected.",
    }
    assert connection.calls == []


def test_unavailable_private_worker_returns_no_host_or_filesystem_details(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = fake_upstream(monkeypatch, OSError("private.example: token unavailable"))
    create_request(broker.directory)

    assert broker.run_once() == 1
    metadata, content = read_response(broker.directory)
    assert metadata["status"] == 503
    assert b"private.example" not in content
    assert b"token" not in content
    assert connection.closed


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(b"{}", kind="text/html"),
        FakeResponse(b"{}", length=mailbox.MAX_JSON_BYTES + 1),
        FakeResponse(b"{}", disposition='inline; filename="secret"'),
    ],
)
def test_unsafe_upstream_headers_never_publish_private_proof_bytes(
    broker: mailbox.MailboxBroker,
    monkeypatch: pytest.MonkeyPatch,
    response: FakeResponse,
) -> None:
    fake_upstream(monkeypatch, response)
    create_request(broker.directory)

    assert broker.run_once() == 1
    metadata, _content = read_response(broker.directory)
    assert metadata["status"] == 503


def test_unapproved_symlink_request_is_never_followed(
    broker: mailbox.MailboxBroker,
    tmp_path: Path,
) -> None:
    private = tmp_path / "private.txt"
    private.write_text("keep me", encoding="utf-8")
    (broker.directory / (IDENTIFIER + ".request.json")).symlink_to(private)

    with pytest.raises(mailbox.MailboxError, match="0600 regular"):
        broker.run_once()
    assert private.read_text(encoding="utf-8") == "keep me"


def test_mailbox_rejects_requests_readable_by_other_accounts(
    broker: mailbox.MailboxBroker,
) -> None:
    request = create_request(broker.directory)
    request.chmod(0o644)

    with pytest.raises(mailbox.MailboxError, match="0600 regular"):
        broker.run_once()


def test_expired_queue_files_are_removed_without_touching_private_broker_source(
    broker: mailbox.MailboxBroker,
) -> None:
    original = create_request(broker.directory)
    expired = time.time() - broker.ttl_seconds - 5
    os.utime(original, (expired, expired))
    source = broker.directory / "broker.py"
    source.touch(mode=0o600)
    source.write_text("keep the private broker", encoding="utf-8")
    os.utime(source, (expired, expired))

    assert broker.run_once() == 0
    assert not original.exists()
    assert source.read_text(encoding="utf-8") == "keep the private broker"


def test_cli_can_process_one_empty_owner_private_mailbox(private_directory: Path) -> None:
    assert mailbox.main(["--directory", str(private_directory), "--once"]) == 0
    assert private_directory.stat().st_mode & 0o777 == 0o700
