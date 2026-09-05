"""Exact-byte and no-clobber contracts for the optional PHP delivery stage."""
from hashlib import sha256
import gzip
import json
from pathlib import Path
import re

import pytest

from stage_peano_php_delivery import SOURCE, assemble, inspect_base, inventory, rows


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o644)


@pytest.fixture
def base(tmp_path):
    root = tmp_path / "base"
    payloads = {"py/empty.py": b"", "py/kernel.py": b"# native checker source\n", "worker.js": b"// exact worker\n"}
    app_manifest = b"".join(f"{sha256(data).hexdigest()}  {path}\n".encode() for path, data in sorted(payloads.items()))
    app = "a-" + sha256(app_manifest).hexdigest()[:12]
    write(root / "index.html", f'<!doctype html><script>const APP_ROOT="releases/{app}/";</script>'.encode())
    write(root / ".htaccess", b"# preserved static configuration\n")
    write(root / "releases" / app / "APP_MANIFEST.sha256", app_manifest)
    for path, data in payloads.items():
        write(root / "releases" / app / path, data)
    vendor_files = {"fonts/Inter-400.woff2": b"already compressed font", "pyodide/pyodide.asm.wasm": b"\0asm" * 2000,
                    "pyodide/python_stdlib.zip": b"already compressed zip"}
    vendor_manifest = b"".join(f"{sha256(data).hexdigest()}  ./{path}\n".encode() for path, data in sorted(vendor_files.items()))
    vendor = "v-" + sha256(vendor_manifest).hexdigest()[:12]
    aggregate = b"".join(f"{sha256(data).hexdigest()}  ./{vendor}/{path}\n".encode() for path, data in sorted(vendor_files.items()))
    write(root / "vendor/MANIFEST.sha256", aggregate)
    for path, data in vendor_files.items():
        write(root / "vendor" / vendor / path, data)
    return root


def test_stage_preserves_every_client_byte_and_authenticates_encodings(base, tmp_path):
    before = inventory(base)
    output = tmp_path / "php"
    report = assemble(base, output)
    assert report["proof_authority"] is False
    assert report["preserved_public_file_count"] == len(before) - 1
    assert inventory(base) == before
    for path in before:
        if path != ".htaccess":
            assert (base / path).read_bytes() == (output / path).read_bytes()
    assert (output / ".htaccess").read_bytes() == (SOURCE / ".htaccess").read_bytes()
    for meta_path in (output / ".peano-delivery/gzip").glob("*.json"):
        meta = json.loads(meta_path.read_bytes())
        encoded = (output / ".peano-delivery/gzip" / (meta["sha256"] + ".gz")).read_bytes()
        plain = gzip.decompress(encoded)
        assert sha256(encoded).hexdigest() == meta["sha256"]
        assert len(encoded) == meta["bytes"]
        assert sha256(plain).hexdigest() == meta["plain_sha256"] == meta_path.stem
        assert len(plain) == meta["plain_bytes"]
        assert encoded[4:8] == b"\0\0\0\0" and encoded[9] == 255
    after = inventory(output)
    assert assemble(base, output, check=True) == report
    assert inventory(output) == after


def test_binary_archives_and_fonts_have_no_gzip_sidecars(base, tmp_path):
    output = tmp_path / "php"
    assemble(base, output)
    for path, value in inventory(base).items():
        if Path(path).suffix in {".woff2", ".zip"}:
            assert not (output / ".peano-delivery/gzip" / (value + ".json")).exists()


def test_existing_modified_stage_is_not_overwritten(base, tmp_path):
    output = tmp_path / "php"
    assemble(base, output)
    write(output / "index.html", b"owner's changed file")
    before = inventory(output)
    with pytest.raises(ValueError, match="Existing PHP stage differs"):
        assemble(base, output)
    assert inventory(output) == before
    assert not list(tmp_path.glob("peano-php-assembly-*"))


@pytest.mark.parametrize("corruption", ["payload", "manifest", "extra", "symlink", "mode"])
def test_base_corruption_is_rejected_before_output_creation(base, tmp_path, corruption):
    app = next((base / "releases").iterdir())
    worker = app / "worker.js"
    if corruption == "payload":
        write(worker, b"wrong bytes")
    elif corruption == "manifest":
        write(app / "APP_MANIFEST.sha256", b"bad manifest\n")
    elif corruption == "extra":
        write(base / "unexpected.txt", b"not published")
    elif corruption == "symlink":
        worker.unlink()
        worker.symlink_to(base / "index.html")
    else:
        worker.chmod(0o666)
    output = tmp_path / "php"
    with pytest.raises(ValueError):
        assemble(base, output)
    assert not output.exists()


@pytest.mark.parametrize("text", [b"", b"not a manifest\n", b"a" * 64 + b"  ../secret\n",
    b"a" * 64 + b"  .hidden\n", b"a" * 64 + b"  x\n" + b"a" * 64 + b"  x\n",
    b"a" * 64 + b"  z\n" + b"a" * 64 + b"  a\n"])
def test_bad_manifests_fail_closed(text):
    with pytest.raises(ValueError):
        rows(text)


def test_output_cannot_be_nested_or_alias_the_input(base, tmp_path):
    for path in (base, base / "nested", base.parent):
        with pytest.raises(ValueError, match="distinct non-nested"):
            assemble(base, path)
    alias = tmp_path / "alias"
    alias.symlink_to(base, target_is_directory=True)
    with pytest.raises(ValueError):
        assemble(base, alias)


def test_check_requires_an_existing_stage(base, tmp_path):
    with pytest.raises(ValueError, match="no existing"):
        assemble(base, tmp_path / "absent", check=True)


def test_php_adapter_has_no_network_write_execution_or_proof_authority():
    source = (SOURCE / "peano-delivery.php").read_text()
    forbidden = r"\b(?:eval|exec|system|passthru|shell_exec|popen|proc_open|file_put_contents|fwrite|unlink|mkdir|curl_init|fsockopen|session_start|move_uploaded_file)\s*\("
    assert not re.search(forbidden, source)
    assert "hash_update_stream" in source and "hash_equals" in source
    assert "['GET', 'HEAD']" in source
    assert "min(65536, $left)" in source
    assert "MAX_FILE = 67108864" in source
    assert "MAX_MANIFEST = 1048576" in source
    assert "$_GET" not in source and "$_POST" not in source and "$_COOKIE" not in source


def test_adapter_and_portable_suite_keep_the_observed_php70_syntax_floor():
    # The SSH CLI is 7.4; the public FPM is 7.0. Real HTTPS is still mandatory.
    for path in (SOURCE / "peano-delivery.php", SOURCE.parents[1] / "scripts/test_peano_php_delivery.php"):
        source = path.read_text()
        assert not re.search(r"\?\s*(?:string|array|int|bool)\b", source)
        assert not re.search(r"\)\s*:\s*void\b", source)
        assert not re.search(r"\bas\s*\[|^\s*\[\$[^;]+\]\s*=", source, re.M)
    runbook = " ".join((SOURCE.parents[1] / "docs/PEANO_PHP_DELIVERY.md").read_text().split())
    assert "PHP 7.0.33" in runbook and "PHP 7.4.3" in runbook


def test_transport_route_is_peano_local_and_does_not_edit_the_canonical_static_policy():
    policy = (SOURCE / ".htaccess").read_text()
    assert 'RewriteRule ^ peano-delivery.php [END]' in policy
    assert 'SetEnv no-gzip 1' in policy and 'SetEnv no-brotli 1' in policy
    assert "X-Forwarded-Proto" in policy
    assert "https://%{HTTP_HOST}%{REQUEST_URI}" in policy
    assert "proxy:" not in policy and "http://" not in policy
    original = (SOURCE.parents[1] / "peano-lab/.htaccess").read_text()
    assert "Header set Cache-Control" in original
