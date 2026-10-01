"""Delivery invariants are not theorem-admission tests."""
from hashlib import sha256
import json
import gzip
import io
from pathlib import Path
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage_sqrt2_power_research as release


@pytest.mark.parametrize("name", ["", "../index.html", "/index.html", "a/../b", "a//b", "./b", "a\\b", "a b"])
def test_unsafe_names_rejected(tmp_path, name):
    with pytest.raises(ValueError):
        release.safe_path(tmp_path, name)


def test_symlinks_are_rejected(tmp_path):
    (tmp_path / "real").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        release.safe_path(tmp_path, "link/file")


def test_complete_inventory_detects_extra_missing_and_changed_bytes(tmp_path):
    path = tmp_path / "index.html"
    path.write_bytes(b"original")
    expected = {"index.html": release.pin(b"original")}
    release.inventory(tmp_path, expected)
    path.write_bytes(b"modified")
    with pytest.raises(ValueError, match="bytes differ"):
        release.inventory(tmp_path, expected)
    path.write_bytes(b"original")
    (tmp_path / "extra").write_bytes(b"unregistered")
    with pytest.raises(ValueError, match="unregistered"):
        release.inventory(tmp_path, expected)
    with pytest.raises(ValueError, match="unregistered"):
        release.inventory(tmp_path, {**expected, "missing": release.pin(b"")})


def test_manifest_authentication_and_self_reference(tmp_path):
    (tmp_path / "index.html").write_bytes(b"original")
    value = {"files": {"index.html": release.pin(b"original")}}
    raw = release.encode(value)
    (tmp_path / "manifest.json").write_bytes(raw)
    release.authenticated_manifest(tmp_path, "manifest.json", sha256(raw).hexdigest(), "files")
    with pytest.raises(ValueError, match="sealed"):
        release.authenticated_manifest(tmp_path, "manifest.json", "0"*64, "files")
    value["files"]["manifest.json"] = release.pin(raw)
    raw = release.encode(value)
    (tmp_path / "manifest.json").write_bytes(raw)
    with pytest.raises(ValueError, match="itself"):
        release.authenticated_manifest(tmp_path, "manifest.json", sha256(raw).hexdigest(), "files")


def test_navigation_is_additive_and_honest():
    files = release.entrance_bytes(release.PARENT)
    assert set(files) == set(release.ENTRANCES)
    for name, raw in files.items():
        original = (release.PARENT / name).read_bytes()
        marker = b'<main class="shell">' if name == "index.html" else b"<body>"
        before, after = original.split(marker)
        assert raw.startswith(before+marker) and raw.endswith(after)
        assert b'33' in raw and b"remain open" in raw
        assert b"sqrt2-power/" in raw
    assert b"not an Alpha admission" in files["index.html"]
    # All prior embedded graph data, styles and scripts are preserved exactly.
    opening = b'<script type="application/json" id="campaign-data">'
    old = (release.PARENT / release.ENTRANCES[1]).read_bytes().split(opening)[1].split(b"</script>")[0]
    new = files[release.ENTRANCES[1]].split(opening)[1].split(b"</script>")[0]
    assert old == new


def test_repeated_or_absent_insert_points_fail_closed():
    for raw in (b"absent insertion point", b"xx marker marker"):
        with pytest.raises(ValueError):
            release.insert_once(raw, b"marker", b"new")


def test_campaign_is_exactly_the_unadmitted_checkpoint():
    site, files = release.authenticated_manifest(release.SITE, release.SITE_MANIFEST,
        release.SITE_SHA256, "files")
    assert len(files) == 264 and site["authority"] == "planning_only"
    data = json.loads((release.SITE / "api/wave-results.json").read_bytes())
    assert data["counts"]["unique_HA_statements"] == 33
    assert data["counts"]["unique_Lean_checked_statements"] == 33
    assert data["library_admissions"] == data["IR_parents_closed"] == 0


def test_existing_stage_is_never_overwritten(tmp_path):
    with pytest.raises(ValueError, match="non-overwriting"):
        release.stage(tmp_path)


@pytest.mark.parametrize("encoding", ["identity", "gzip"])
def test_https_byte_check_handles_transfer_encoding(monkeypatch, encoding):
    import verify_sqrt2_power_publication as http
    payload = b"exact public bytes"
    class Response(io.BytesIO):
        status = 200
        url = http.BASE+"index.html?research=sqrt2-power-2026-10-01"
        headers = {"Content-Encoding": encoding}
    monkeypatch.setattr(http, "urlopen", lambda *a, **k:
        Response(gzip.compress(payload) if encoding == "gzip" else payload))
    result = http.fetch("index.html", release.pin(payload), time.monotonic()+5)
    assert result["passed"] and result["actual"] == release.pin(payload)
    assert not http.fetch("index.html", release.pin(b"wrong"), time.monotonic()+5)["passed"]


def test_https_timeouts_and_redirects_do_not_pass(monkeypatch):
    import verify_sqrt2_power_publication as http
    monkeypatch.setattr(http, "urlopen", lambda *a, **k: pytest.fail("expired request started"))
    assert not http.fetch("index.html", release.pin(b""), 0)["passed"]
    class Response(io.BytesIO):
        status = 200
        url = "https://unrelated.invalid/"
        headers = {}
    monkeypatch.setattr(http, "urlopen", lambda *a, **k: Response(b""))
    assert not http.fetch("index.html", release.pin(b""), time.monotonic()+5)["passed"]
