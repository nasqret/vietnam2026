#!/usr/bin/env python3
"""Add a checked presentation-only layer to an unchanged sealed public stage.

The base Alpha delivery, original explorer assets and all theorem evidence
remain untouched. Never grant admission or replace an existing output tree.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
from tempfile import TemporaryDirectory
import time

from proof_explorer_layout import LayoutError, repair_release_notices

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = "release-v34/manifest.json"
BASE_SHA256 = "7be4ebc968b7e60d79b387f292c8700053a1b48a7ca3598c85a64e27f5b6fa22"
LAYOUT_MANIFEST = "presentation/layout-v1.json"
MAX_FILES, MAX_FILE = 20000, 64 * 1024 * 1024
CPU_LIMITS, WALL_SECONDS, MAX_RSS = (170, 175), 180, 1536 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise LayoutError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def pin(payload):
    return {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}


def ordinary(path, *, directory=False):
    path = Path(path)
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), "symlink in layout path")
    info = path.stat()
    require(info.st_uid == os.getuid() and (stat.S_ISDIR(info.st_mode) if directory
        else stat.S_ISREG(info.st_mode)), "layout input is not an owned ordinary path")
    return info


def read(path):
    before = ordinary(path)
    require(0 < before.st_size <= MAX_FILE, "empty or oversized layout input")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC), "rb") as stream:
        opened = os.fstat(stream.fileno())
        require((before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino), "input changed before read")
        raw = stream.read(MAX_FILE + 1)
        after = os.fstat(stream.fileno())
    def identity(info):
        return (info.st_dev, info.st_ino, info.st_mode, info.st_uid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    require(len(raw) == before.st_size and identity(opened) == identity(after)
        and identity(ordinary(path)) == identity(before),
        "layout input changed during read")
    return raw


def inventory(base):
    ordinary(base, directory=True)
    files = {}
    for path in sorted(base.rglob("*")):
        require(not path.is_symlink(), "linked entry in layout tree")
        if path.is_dir():
            ordinary(path, directory=True)
            continue
        name = path.relative_to(base).as_posix()
        require(len(files) < MAX_FILES and ".." not in Path(name).parts, "invalid layout inventory")
        files[name] = pin(read(path))
    return files


def transformed(base, files):
    changes = {}
    notice_count = 0
    families = set()
    for name, before in files.items():
        if not name.endswith(".html"):
            continue
        raw = read(base / name)
        require(pin(raw) == before, "base page changed")
        revised, notices, changed = repair_release_notices(raw)
        notice_count += notices
        if notices:
            families.add(name.split("/", 1)[0])
        if changed:
            changes[name] = {"before": before, "after": pin(revised), "notices": changed}
    return changes, notice_count, sorted(families)


def validate_base(base, files, accepted_sha256):
    raw = read(base / BASE_MANIFEST)
    require(sha256(raw).hexdigest() == accepted_sha256, "base delivery manifest is not the accepted exact version")
    manifest = json.loads(raw)
    require(manifest.get("schema") == "peano-lab-alpha-v34-public-delivery-v1"
        and manifest.get("delivery_metadata_only") is True
        and manifest.get("alpha_admission_performed") is False
        and manifest.get("stable_admission_performed") is False,
        "base is not the original non-admitting v34 delivery")
    for name, expected in manifest["current_files"].items():
        require(files.get(name) == expected, "sealed base delivery bytes changed: " + name)
    require(LAYOUT_MANIFEST not in files, "base already has a layout overlay")
    return pin(raw)


def stage(base, output, *, check=False, accepted_sha256=BASE_SHA256):
    base, output = Path(base).absolute(), Path(output).absolute()
    require(base != output and base not in output.parents and output not in base.parents,
        "layout output must be separate from its preserved base")
    require(not output.is_symlink(), "linked layout destination")
    ordinary(output.parent, directory=True)
    if not check:
        require(not output.exists(), "layout output already exists; use --check")
    files = inventory(base)
    base_pin = validate_base(base, files, accepted_sha256)
    changes, notices, families = transformed(base, files)
    controls = {name: pin(read(ROOT / "scripts" / name)) for name in
        ("proof_explorer_layout.py", "stage_proof_explorer_layout.py",
         "constructive_alpha_v34_publication_process.py")}
    record = dict(schema="peano-proof-explorer-layout-v1", presentation_only=True,
        alpha_admission_performed=False, stable_admission_performed=False,
        proof_bytes_changed=False, original_assets_changed=False,
        base_manifest={"path": BASE_MANIFEST, **base_pin},
        base_inventory_sha256=sha256(canonical(files)).hexdigest(), base_file_count=len(files),
        changed_page_count=len(changes), notice_count=notices, families=families,
        changed_files=changes, controls=controls)
    manifest_bytes = canonical(record)
    require(len(manifest_bytes) <= 8 * 1024 * 1024, "layout manifest exceeds metadata budget")

    def verify(directory):
        actual = inventory(directory)
        require(set(actual) == set(files) | {LAYOUT_MANIFEST}, "layout output lost or added unexpected files")
        for name, before in files.items():
            require(actual[name] == changes.get(name, {}).get("after", before),
                "layout output changed an unexpected byte: " + name)
        require(read(directory / LAYOUT_MANIFEST) == manifest_bytes, "layout manifest differs")

    def rebind():
        require(inventory(base) == files, "preserved base changed during layout staging")
        require(all(pin(read(ROOT / "scripts" / name)) == value for name, value in controls.items()),
            "layout controller changed during staging")

    if check:
        verify(output)
        rebind()
    else:
        with TemporaryDirectory(prefix=".proof-layout-", dir=output.parent) as temporary:
            candidate = Path(temporary) / "files"
            candidate.mkdir()
            for name, before in files.items():
                raw = read(base / name)
                require(pin(raw) == before, "base changed before copying")
                if name in changes:
                    raw, _, _ = repair_release_notices(raw)
                    require(pin(raw) == changes[name]["after"], "nondeterministic layout rewrite")
                destination = candidate / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(raw)
                destination.chmod(0o644)
                original_info = ordinary(base / name)
                os.utime(destination, ns=(original_info.st_atime_ns, original_info.st_mtime_ns))
            destination = candidate / LAYOUT_MANIFEST
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(manifest_bytes)
            destination.chmod(0o644)
            verify(candidate)
            rebind()
            require(not output.exists() and not output.is_symlink(), "layout destination appeared during staging")
            # renamex_np(RENAME_EXCL) prevents clobbering even an empty directory.
            from constructive_alpha_v34_publication_process import _rename_new
            _rename_new(candidate, output)
    return dict(files=len(files) + 1, changed_pages=len(changes), notices=notices,
        family_count=len(families), manifest_sha256=sha256(manifest_bytes).hexdigest(),
        check_only=check, presentation_only=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "_deploy/proofs-v34")
    parser.add_argument("--output", type=Path, default=ROOT / "_deploy/proofs-layout-v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    started = time.monotonic()
    result = stage(args.base, args.output, check=args.check)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = int(rss if sys.platform == "darwin" else rss * 1024)
    require(0 < rss <= MAX_RSS and time.monotonic() - started < WALL_SECONDS, "layout staging resource limit exceeded")
    print(json.dumps(dict(result, seconds=time.monotonic() - started, peak_rss_bytes=rss), sort_keys=True))


if __name__ == "__main__":
    main()
