"""Local-only URL resolution and fake-curl regressions; no network or proof runtime."""
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import json

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_constructive_public_urls_v35 as check


def test_exact_queries_fragments_and_directory_index_mapping():
    url, name = check.resolve_url("../../../../assets/defined-explorer.js?v=1b95ce228950#ignored",
        check.ORIGIN + "/proofs/jordan-totient/explorer/defined/tag/JT004B.html")
    assert url == check.ORIGIN + "/proofs/assets/defined-explorer.js?v=1b95ce228950"
    assert name == "assets/defined-explorer.js"
    assert check.resolve_url("/proofs/", check.ORIGIN)[1] == "index.html"


@pytest.mark.parametrize("reference", ["https://example.org/proofs/a", "//example.org/proofs/a",
    "http://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/a", "/other/a", "/proofs/%2e%2e/a",
    "https://user@bnaskrecki.faculty.wmi.amu.edu.pl/proofs/a", "/proofs/a\nb"])
def test_unsafe_or_offsite_urls_never_resolve(reference):
    with pytest.raises(ValueError): check.resolve_url(reference, check.ORIGIN + "/proofs/")


def test_html_parser_keeps_real_queries_and_graph_links():
    parser = check.Links()
    parser.feed('<link rel="stylesheet" href="../assets/a.css?v=old">'
                '<script src="../assets/a.js?v=old"></script>'
                '<a href="graph.html?target=A&amp;v=old">Graph</a>'
                '<a href="#proof-line-1">Line</a>'
                '<div data-graph-json="api/graph.json?v=old"></div>')
    assert parser.rows == [("stylesheet", "../assets/a.css?v=old"), ("script", "../assets/a.js?v=old"),
        ("graph", "graph.html?target=A&v=old"), ("graph-payload", "api/graph.json?v=old")]
    with pytest.raises(ValueError): parser.feed('<base href="https://example.org/">')


@pytest.mark.parametrize("variant", ["success", "hash", "redirect", "url", "encoding", "oversized", "timeout"])
def test_exact_url_transport_with_fake_local_curl(monkeypatch, variant):
    real = subprocess.Popen
    url = check.ORIGIN + "/proofs/assets/test.js?v=actual"
    body = b"ok" if variant != "hash" else b"no"
    if variant == "oversized": body = b"too large"
    status = "302" if variant == "redirect" else "200"
    effective = url + "&wrong=1" if variant == "url" else url
    headers = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
    if variant == "encoding": headers += b"Content-Encoding: gzip\r\n"
    headers += b"\r\n"
    if variant == "timeout": monkeypatch.setattr(check, "REQUEST_SECONDS", 0.04)
    def fake(command, **kwargs):
        assert command[-1] == url and command[:2] == ["curl", "-q"]
        assert "--location" not in command and "--insecure" not in command
        target = command[command.index("--dump-header")+1]
        metadata = check.transport.MARKER + status.encode() + b" " + effective.encode() + b"\n"
        program = ("import os,sys,time;from pathlib import Path;time.sleep(float(sys.argv[1]));"
                   "Path(sys.argv[2]).write_bytes(bytes.fromhex(sys.argv[3]));"
                   "os.write(1,bytes.fromhex(sys.argv[4]));os.write(2,bytes.fromhex(sys.argv[5]))")
        return real([sys.executable, "-B", "-c", program, "0.5" if variant == "timeout" else "0",
                     str(target), headers.hex(), body.hex(), metadata.hex()], **kwargs)
    monkeypatch.setattr(check.subprocess, "Popen", fake)
    result = check.fetch_exact(dict(url=url, stage_relative_path="assets/test.js", sources=[],
                                   expected=dict(bytes=2, sha256=sha256(b"ok").hexdigest())), check.monotonic()+5)
    assert result["passed"] is (variant == "success")
    assert result["curl_exit"] is not None and result["cleanup_failed"] is False
    assert bool(result["failure"]) is (variant != "success")
    if variant == "success":
        assert result["effective_url"] == url and result["status"] == "200"


def test_exclusive_receipt_prevents_network_on_existing_output(tmp_path, monkeypatch):
    output = tmp_path / "receipt.json"
    output.write_bytes(b"previous observation")
    def forbidden(*args): raise AssertionError("network must not begin")
    monkeypatch.setattr(check, "run_batch", forbidden)
    with pytest.raises(FileExistsError):
        check.main(["--batch", "1", "--accepted-stage-manifest-sha256", "a"*64, "--output", str(output)])
    assert output.read_bytes() == b"previous observation"


def test_all_batches_collect_one_exclusive_non_authoritative_receipt(tmp_path, monkeypatch):
    seen = []
    def fake(batch, accepted):
        seen.append(batch)
        return dict(passed=True, request_count=4 if batch == 1 else 1,
                    successful_requests=4 if batch == 1 else 1, requests=[], batches=2,
                    source_binding={"sha256": "b"*64}, inventory_sha256="c"*64, inventory_path_count=5)
    monkeypatch.setattr(check, "run_batch", fake)
    output = tmp_path / "receipt.json"
    assert check.main(["--accepted-stage-manifest-sha256", "a"*64, "--output", str(output)]) == 0
    result = json.loads(output.read_bytes())
    assert seen == [1, 2] and result["passed"] and result["request_count"] == 5
    assert result["batch_count"] == 2 and result["proof_authority"] is False
