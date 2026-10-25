#!/usr/bin/env python3
"""Install one pinned official macOS ARM64 Vampire release, without running it.

One bounded attempt; failures retain the new staging directory for inspection.
The package digest is published by the upstream GitHub release.  This helper
does not modify the model, a global PATH, or any historical project evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import resource
import shutil
import signal
import stat
import struct
import sys
import time
import urllib.request
import zipfile


APP = Path(__file__).resolve().parent
DESTINATION = APP / ".runtime" / "vampire"
VERSION = "5.0.1"
URL = "https://github.com/vprover/vampire/releases/download/v5.0.1/vampire-macOS-ARM64.zip"
RELEASE_PAGE = "https://github.com/vprover/vampire/releases/expanded_assets/v5.0.1"
ARCHIVE_SHA256 = "8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35"
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_WALL_SECONDS = 120
MAX_CPU_SECONDS = 30
SOLVER_ARGS = ["--mode", "vampire", "--input_syntax", "tptp", "--proof", "tptp",
               "--output_axiom_names", "on", "-t", "1", "-m", "256"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_info(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main() -> int:
    require(sys.flags.isolated and sys.dont_write_bytecode, "Run with Python -I -B.")
    require(len(sys.argv) == 1, "This pinned installer accepts no arguments.")
    require(platform.system() == "Darwin" and platform.machine() == "arm64",
            "This package is pinned for macOS ARM64 only.")
    require(not (APP / ".runtime").is_symlink(), "The runtime directory must not be a symlink.")
    require(not DESTINATION.exists() and not DESTINATION.is_symlink(),
            "The Vampire destination already exists; no automatic retry or overwrite is permitted.")
    require(shutil.disk_usage(APP).free >= MAX_DOWNLOAD_BYTES + MAX_EXPANDED_BYTES + 64 * 1024 * 1024,
            "Not enough free space for the bounded Vampire package.")
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_SECONDS, MAX_CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_EXPANDED_BYTES, MAX_EXPANDED_BYTES))
    started = time.monotonic()

    def deadline(*_):
        raise TimeoutError("Vampire setup exceeded its 120-second wall-time bound.")

    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, MAX_WALL_SECONDS)
    DESTINATION.mkdir(parents=True, exist_ok=False)
    archive = DESTINATION / "vampire-macOS-ARM64.zip"
    request = urllib.request.Request(URL, headers={"User-Agent": "Hydra-local-playground-pinned-setup/1"})
    transferred = 0
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=20) as response, archive.open("xb") as output:
        require(response.status == 200, "The official Vampire release did not return HTTP 200.")
        final_url = response.geturl()
        require(final_url.startswith("https://"), "The release redirected away from HTTPS.")
        declared = response.headers.get("Content-Length")
        require(declared is None or 0 < int(declared) <= MAX_DOWNLOAD_BYTES,
                "The official archive exceeds the reviewed download limit.")
        while True:
            block = response.read(min(1024 * 1024, MAX_DOWNLOAD_BYTES + 1 - transferred))
            if not block:
                break
            transferred += len(block)
            require(transferred <= MAX_DOWNLOAD_BYTES, "The download exceeded 20 MiB.")
            digest.update(block)
            output.write(block)
    require(digest.hexdigest() == ARCHIVE_SHA256, "The upstream-published Vampire archive digest did not match.")
    binary_part = DESTINATION / "vampire.part"
    with zipfile.ZipFile(archive) as package:
        entries = package.infolist()
        require(0 < len(entries) <= 64, "Unexpected number of archive members.")
        require(sum(item.file_size for item in entries) <= MAX_EXPANDED_BYTES,
                "The archive exceeds the reviewed 100 MiB expanded limit.")
        for item in entries:
            path = PurePosixPath(item.filename)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in item.filename,
                    "Unsafe archive path.")
            mode = item.external_attr >> 16
            require(not stat.S_ISLNK(mode) and not item.flag_bits & 1,
                    "Symlink and encrypted archive entries are not permitted.")
        candidates = [item for item in entries if not item.is_dir() and PurePosixPath(item.filename).name == "vampire"]
        require(len(candidates) == 1, "The official archive does not contain exactly one vampire executable.")
        member = candidates[0]
        require(1024 < member.file_size <= MAX_EXPANDED_BYTES, "Unexpected executable size.")
        copied = 0
        with package.open(member) as source, binary_part.open("xb") as output:
            while True:
                block = source.read(min(1024 * 1024, MAX_EXPANDED_BYTES + 1 - copied))
                if not block:
                    break
                copied += len(block)
                require(copied <= MAX_EXPANDED_BYTES, "Expanded executable exceeds its bound.")
                output.write(block)
        require(copied == member.file_size, "The archive executable length changed while reading.")
    with binary_part.open("rb") as source:
        header = source.read(8)
    require(len(header) == 8 and header[:4] == b"\xcf\xfa\xed\xfe"
            and struct.unpack("<I", header[4:])[0] == 0x0100000C,
            "The pinned package did not contain a macOS ARM64 Mach-O executable.")
    binary_part.chmod(0o700)
    binary = DESTINATION / "vampire"
    binary_part.rename(binary)
    manifest = {
        "schema": "hydra-playground-vampire-package-v1",
        "status": "installed-not-executed",
        "version": VERSION,
        "platform": "macOS-ARM64",
        "release": {"tag": "v5.0.1", "url": URL, "sha256": ARCHIVE_SHA256,
                    "digest_source": RELEASE_PAGE},
        "archive": file_info(archive),
        "executable": {**file_info(binary), "path": "vampire"},
        "allowed_solver_args": SOLVER_ARGS,
        "version_args": ["--version"],
        "network_bytes": transferred,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "automatic_retry": False,
        "solver_executed": False,
        "limits": {"download_bytes": MAX_DOWNLOAD_BYTES, "expanded_bytes": MAX_EXPANDED_BYTES,
                   "wall_seconds": MAX_WALL_SECONDS, "cpu_seconds": MAX_CPU_SECONDS},
        "trust": "External ATP output is advisory; only independently replayed Peano certificates prove goals.",
    }
    require(time.monotonic() - started < MAX_WALL_SECONDS, "Setup reached its wall-time bound.")
    manifest_part = DESTINATION / "manifest.part.json"
    with manifest_part.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")
    manifest_part.rename(DESTINATION / "manifest.json")
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({"status": manifest["status"], "manifest": str(DESTINATION / "manifest.json"),
                      "executable": manifest["executable"], "network_bytes": transferred}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status": "failed", "error": str(error), "automatic_retry": False}), file=sys.stderr)
        raise SystemExit(2)
