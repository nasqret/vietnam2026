#!/usr/bin/env python3
"""Assemble the approved, read-only PHP transport around an exact Peano stage.

No upload, proof admission, server command, or mutation of an existing stage.
Gzip sidecars are deterministic and independently decoded before publication.
"""
from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "_deploy/peano-lab"
OUTPUT = ROOT / "_deploy/peano-lab-php"
SOURCE = ROOT / "deploy/peano-delivery"
MAX_FILE = 64 * 1024 * 1024
MAX_MANIFEST = 1024 * 1024
COMPRESS = {".html", ".js", ".css", ".json", ".py", ".txt", ".sha256", ".wasm"}
PUBLIC_TYPES = COMPRESS | {".zip", ".woff2"}
PATH = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.-]*)*\Z")


def digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            value.update(chunk)
    return value.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"Not a regular stage directory: {root}")
    result = {}
    for directory, children, files in os.walk(root, followlinks=False):
        for name in children + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError(f"Symlink/special file is forbidden: {path}")
            if mode & 0o022:
                raise ValueError(f"Shared-writable stage component: {path}")
        for name in files:
            path = Path(directory) / name
            if path.stat().st_size > MAX_FILE:
                raise ValueError(f"File exceeds the original 64 MiB delivery bound: {path}")
            result[path.relative_to(root).as_posix()] = digest(path)
    return dict(sorted(result.items()))


def rows(text: bytes) -> dict[str, str]:
    if not text or len(text) > MAX_MANIFEST or not text.endswith(b"\n"):
        raise ValueError("Invalid or oversized manifest")
    result = {}
    for line in text.decode("ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (?:\./)?(.+)", line)
        if match is None or not PATH.fullmatch(match[2]) or ".." in match[2]:
            raise ValueError("Unsafe manifest path")
        if match[2] in result or len(result) >= 8192:
            raise ValueError("Duplicate path or oversized manifest inventory")
        result[match[2]] = match[1]
    if list(result) != sorted(result):
        raise ValueError("Manifest is not in canonical C-locale path order")
    return result


def inspect_base(base: Path) -> tuple[dict[str, str], str, dict[str, bytes]]:
    files = inventory(base)
    index = (base / "index.html").read_bytes()
    if len(index) > MAX_MANIFEST:
        raise ValueError("Oversized mutable entrypoint")
    found = re.search(rb'const APP_ROOT="releases/(a-[0-9a-f]{12})/";', index)
    if found is None:
        raise ValueError("No canonical application pointer")
    app = found[1].decode("ascii")
    manifest_path = f"releases/{app}/APP_MANIFEST.sha256"
    text = (base / manifest_path).read_bytes()
    if "a-" + sha256(text).hexdigest()[:12] != app:
        raise ValueError("Application namespace does not match its exact manifest")
    expected = {"index.html": sha256(index).hexdigest(), ".htaccess": files.get(".htaccess"),
                manifest_path: sha256(text).hexdigest()}
    for path, value in rows(text).items():
        if Path(path).suffix not in PUBLIC_TYPES:
            raise ValueError("Executable or unsupported application payload")
        expected[f"releases/{app}/{path}"] = value
    vendor_text = (base / "vendor/MANIFEST.sha256").read_bytes()
    expected["vendor/MANIFEST.sha256"] = sha256(vendor_text).hexdigest()
    groups: dict[str, dict[str, str]] = {}
    for path, value in rows(vendor_text).items():
        match = re.fullmatch(r"(v-[0-9a-f]{12})/((?:fonts|pyodide|xterm)/.+)", path)
        if match is None or Path(path).suffix not in PUBLIC_TYPES:
            raise ValueError("Unsupported vendor namespace or payload")
        groups.setdefault(match[1], {})[match[2]] = value
        expected["vendor/" + path] = value
    vendors = {}
    for name, entries in groups.items():
        canonical = "".join(f"{value}  ./{path}\n" for path, value in sorted(entries.items())).encode("ascii")
        if name != "v-" + sha256(canonical).hexdigest()[:12]:
            raise ValueError("Vendor namespace does not match its canonical manifest")
        vendors[name] = canonical
    if not vendors or expected != files:
        raise ValueError("Base inventory differs from the exact application/vendor manifests")
    return files, app, vendors


def put(root: Path, relative: str, data: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != data:
            raise ValueError(f"Conflicting generated bytes: {relative}")
        return
    with path.open("xb") as output:
        output.write(data)
    path.chmod(0o644)


def encode_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def assemble(base: Path, output: Path, source: Path = SOURCE, *, check: bool = False) -> dict:
    """Create once or compare an existing tree; never replace previous delivery bytes."""
    if output.is_symlink() or output == base or base in output.parents or output in base.parents:
        raise ValueError("Stage paths must be distinct non-nested directories")
    if check and not output.is_dir():
        raise ValueError("There is no existing PHP delivery stage to check")
    original, app, vendors = inspect_base(base)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="peano-php-assembly-", dir=output.parent))
    try:
        for relative in original:
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative != ".htaccess":
                shutil.copyfile(base / relative, target)
                target.chmod(0o644)
        put(temporary, ".htaccess", (source / ".htaccess").read_bytes())
        put(temporary, "peano-delivery.php", (source / "peano-delivery.php").read_bytes())
        for name, text in vendors.items():
            put(temporary, f".peano-delivery/vendors/{name}.sha256", text)
        encoded = set()
        wasm_encoded = {}
        for relative, plain_hash in original.items():
            if Path(relative).suffix not in COMPRESS or plain_hash in encoded:
                continue
            plain = (base / relative).read_bytes()
            compressed = gzip.compress(plain, compresslevel=9, mtime=0)
            # Python/zlib can choose a platform OS byte; make the RFC 1952 header portable.
            compressed = compressed[:9] + b"\xff" + compressed[10:]
            if gzip.decompress(compressed) != plain:
                raise ValueError("Compressed representation does not recover exact source")
            if relative.endswith("pyodide.asm.wasm"):
                if not 0 < len(compressed) < 3000000:
                    raise ValueError("WASM fails the unchanged encoded delivery bound")
                wasm_encoded[relative] = len(compressed)
            compressed_hash = sha256(compressed).hexdigest()
            put(temporary, f".peano-delivery/gzip/{compressed_hash}.gz", compressed)
            put(temporary, f".peano-delivery/gzip/{plain_hash}.json", encode_json({
                "schema": "peano-gzip-v1", "plain_sha256": plain_hash, "plain_bytes": len(plain),
                "sha256": compressed_hash, "bytes": len(compressed),
            }))
            encoded.add(plain_hash)
        files = inventory(temporary)
        preserved = {p: h for p, h in original.items() if p != ".htaccess"}
        if any(files[p] != value for p, value in preserved.items()) or inventory(base) != original:
            raise ValueError("Original application, entrypoint, or vendor bytes changed")
        report = {
            "schema": "peano-php-delivery-stage-v1", "proof_authority": False,
            "application_id": app, "base_file_count": len(original),
            "preserved_public_file_count": len(preserved), "gzip_representations": len(encoded),
            "encoded_wasm_bytes": wasm_encoded, "base_files": original, "files": files,
            "source_sha256": {name: digest(source / name) for name in (".htaccess", "peano-delivery.php")},
        }
        put(temporary, ".peano-delivery/stage.json", encode_json(report))
        for directory, _, _ in os.walk(temporary):
            Path(directory).chmod(0o755)
        if output.exists():
            if inventory(output) != inventory(temporary):
                raise ValueError("Existing PHP stage differs; retain it as a release backup before staging a new candidate")
        else:
            temporary.rename(output)
        return report
    finally:
        # This is only the generated mkdtemp tree, never the output or source tree.
        if temporary.exists():
            shutil.rmtree(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = assemble(BASE, OUTPUT, check=args.check)
    print(json.dumps({key: report[key] for key in (
        "schema", "application_id", "base_file_count", "preserved_public_file_count",
        "gzip_representations", "encoded_wasm_bytes")}, sort_keys=True))


if __name__ == "__main__":
    main()
