"""Read-only delivery and certificate-verifying transport boundaries."""

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import check_lower_tier_delivery as delivery


@pytest.mark.parametrize("kind", ("missing", "empty", "oversized"))
def test_bounded_reads_reject_unsafe_files(tmp_path, monkeypatch, kind):
    path = tmp_path / "input"
    monkeypatch.setattr(delivery, "MAX_FILE_BYTES", 4)
    if kind != "missing":
        path.write_bytes(b"" if kind == "empty" else b"12345")
    with pytest.raises(ValueError):
        delivery.read(path)


def test_reads_reject_symlinks(tmp_path):
    source, linked = tmp_path / "source", tmp_path / "linked"
    source.write_bytes(b"x")
    linked.symlink_to(source)
    with pytest.raises(ValueError):
        delivery.read(linked)
    assert source.read_bytes() == b"x"


def test_staging_rejects_linked_root(tmp_path):
    source, linked = tmp_path / "source", tmp_path / "linked"
    source.mkdir()
    linked.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="ordinary directory"):
        delivery.staged(linked)


def test_system_transport_retains_tls_checks_and_explicit_limits(monkeypatch):
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stderr=b"", stdout=b"exact\n200\n" + command[-1].encode())
    monkeypatch.setattr(delivery.subprocess, "run", run)
    result = delivery.live({"example.html": b"exact"}, transport="curl")
    command, kwargs = calls[0]
    assert command[:3] == ["curl", "--proto", "=https"]
    assert not set(command) & {"--insecure", "-k", "--location", "-L"}
    assert command[command.index("--max-filesize") + 1] == "6"
    assert float(command[command.index("--max-time") + 1]) <= 25
    assert kwargs["timeout"] <= 30 and kwargs["capture_output"] is True
    assert command[-1].startswith(delivery.ORIGIN + "/proofs/")
    assert result["tls_certificate_verification"] is True
    assert result["https_objects_compared"] == 1 and result["https_bytes_compared"] == 5


@pytest.mark.parametrize("kind", ("status", "redirect", "bytes", "too_long", "tls_error"))
def test_system_transport_rejects_changed_served_evidence(monkeypatch, kind):
    def run(command, **_):
        data = b"wrong" if kind == "bytes" else b"exact"
        if kind == "too_long":
            data += b"extra"
        status = b"302" if kind == "status" else b"200"
        effective = b"https://other.example/" if kind == "redirect" else command[-1].encode()
        return SimpleNamespace(returncode=60 if kind == "tls_error" else 0, stderr=b"certificate failure",
                               stdout=data + b"\n" + status + b"\n" + effective)
    monkeypatch.setattr(delivery.subprocess, "run", run)
    with pytest.raises(ValueError):
        delivery.live({"example.html": b"exact"}, transport="curl")


def test_unknown_transport_cannot_disable_tls():
    with pytest.raises(ValueError, match="unknown"):
        delivery.live({}, transport="insecure")


def test_expired_request_budget_prevents_any_fetch(monkeypatch):
    times = iter((0, 100))
    monkeypatch.setattr(delivery, "monotonic", lambda: next(times))
    monkeypatch.setattr(delivery.subprocess, "run", lambda *_a, **_k: pytest.fail("late network call"))
    with pytest.raises(TimeoutError, match="90-second"):
        delivery.live({"example.html": b"exact"}, transport="curl")


@pytest.mark.parametrize("source", (b'<p id="x"></p><p id="x"></p>', b'<a href="a" href="b">x</a>'))
def test_ambiguous_html_is_rejected(source):
    with pytest.raises(ValueError, match="duplicate"):
        delivery.Document(source)


def test_html_link_entities_are_decoded_without_changing_fragment_ids():
    document = delivery.Document(b'<a id="target" href="graph.html?a=1&amp;b=2#target">x</a>')
    assert document.ids == {"target"}
    assert document.references == ["graph.html?a=1&b=2#target"]
