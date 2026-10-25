"""Seal the approved P7 file list using only bounded standard-library file I/O."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import signal
import stat
import sys
import tarfile
import time


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/hydra-implementation-2026-09-04/p7-source-bundle-01"
COPY_LIST = ROOT / "output/p7-prototype/copy-list-v1.json"
COPY_SHA = "d469d4bd0e41b1ed1582a64a9e86e04b9d1f9970b7ac3a619e86b4266235617e"
PUBLISHER = "hydra-playground/publish_showcase.py"
PRESERVED = ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-03/source" / PUBLISHER
MAP_SHA = "5955fbb1903a8ddf20c85886136b6ea9fd14ae980f410ad190d949c78fd553fb"
SELECTION_SHA = "26c09c2b28f54073f3964c4772113f7496eceb03107b356b892c619c9cc835d7"
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
BLOCK = 1024 * 1024


def require(value, message):
    if not value:
        raise RuntimeError(message)


def pin(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(BLOCK):
            size += len(chunk)
            digest.update(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def write_json(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(raw)


def source_path(name):
    return PRESERVED if name == PUBLISHER else ROOT / name


def ordinary_path(path):
    relative = path.relative_to(ROOT)
    cursor = ROOT
    for part in relative.parts:
        cursor /= part
        require(not cursor.is_symlink(), f"symlink forbidden: {cursor}")
    require(stat.S_ISREG(path.stat().st_mode), f"non-regular source: {path}")


def write_archive(destination, source, records):
    # All metadata and ordering are fixed. No timestamps, owner names or gzip
    # source filename are inherited from the host.
    with gzip.GzipFile(filename="", fileobj=destination, mode="wb", mtime=0,
                       compresslevel=9) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as tar:
            for name, expected in records.items():
                info = tarfile.TarInfo(name)
                info.size = expected["bytes"]
                info.mode = 0o600
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                with (source / name).open("rb") as stream:
                    tar.addfile(info, stream)


class DigestSink:
    def __init__(self):
        self.digest = hashlib.sha256()
        self.bytes = 0

    def write(self, raw):
        self.digest.update(raw)
        self.bytes += len(raw)
        return len(raw)

    def flush(self):
        pass


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 75))
    resource.setrlimit(resource.RLIMIT_FSIZE, (160 * BLOCK, 160 * BLOCK))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    started = time.monotonic()
    require(pin(COPY_LIST)["sha256"] == COPY_SHA, "copy-list hash changed")
    approved = json.loads(COPY_LIST.read_bytes())
    require(approved["schema"] == "hydra-p7-exact-copy-list-v1", "wrong copy-list schema")
    require(approved["file_count"] == 1273 and approved["total_bytes"] == 111330633,
            "approved size changed")
    require(approved["native_controller_source_map_sha256"] == MAP_SHA
            and approved["selection_sha256"] == SELECTION_SHA
            and approved["dataset_manifest_sha256"] == DATA_SHA, "P7 input pins changed")
    records = {}
    for row in approved["files"]:
        name = row["path"]
        path = PurePosixPath(name)
        require(isinstance(name, str) and not path.is_absolute() and str(path) == name
                and ".." not in path.parts and "\\" not in name and "\x00" not in name,
                "unsafe approved path")
        require(name not in records and not (ROOT / name).is_relative_to(OUT),
                "duplicate path or bundle self-inclusion")
        require(type(row["bytes"]) is int and 0 <= row["bytes"] <= 64 * BLOCK
                and len(row["sha256"]) == 64, "invalid file descriptor")
        records[name] = {"bytes": row["bytes"], "sha256": row["sha256"]}
    records = dict(sorted(records.items()))
    require(len(records) == 1273 and sum(p["bytes"] for p in records.values()) == 111330633,
            "copy-list content count differs")
    for name, expected in records.items():
        path = source_path(name)
        ordinary_path(path)
        require(pin(path) == expected, f"source pin mismatch: {name}")
    source_map = json.loads((ROOT / "output/p7-prototype/staged-source-pins.json").read_bytes())
    require(source_map["source_pins_sha256"] == MAP_SHA, "source-map declaration changed")
    require(pin(ROOT / "output/p7-prototype/selection-32-v1.json")["sha256"] == SELECTION_SHA,
            "selection changed")

    OUT.mkdir(mode=0o700, exist_ok=False)
    source = OUT / "source"
    source.mkdir(mode=0o700)
    with (OUT / "copy-list-v1.json").open("xb") as stream:
        stream.write(COPY_LIST.read_bytes())
    write_json(OUT / "build-plan.json", {
        "schema": "hydra-p7-file-only-build-plan-v1", "file_count": 1273,
        "expanded_bytes": 111330633, "copy_list_sha256": COPY_SHA,
        "limits": {"cpu_soft_seconds": 60, "cpu_hard_seconds": 75,
                   "wall_seconds": 120, "max_single_output_bytes": 160 * BLOCK},
        "project_imports": 0, "native_proof_runs": 0, "model_calls": 0,
        "solver_runs": 0, "gpu_allocations": 0, "uploads": 0,
        "substitution": {"logical_path": PUBLISHER,
                         "source": PRESERVED.relative_to(ROOT).as_posix(),
                         "required": records[PUBLISHER],
                         "current_live_bytes_not_used": pin(ROOT / PUBLISHER)},
    })

    copied = {}
    for name, expected in records.items():
        target = source / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with source_path(name).open("rb") as incoming, target.open("xb") as outgoing:
            while chunk := incoming.read(BLOCK):
                outgoing.write(chunk)
        copied[name] = pin(target)
        require(copied[name] == expected, f"copied pin mismatch: {name}")
        target.chmod(0o400)
    actual_names = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    require(actual_names == set(records), "copied tree has missing or extra files")

    archive = OUT / "source-data.tar.gz"
    with archive.open("xb") as destination:
        write_archive(destination, source, records)
    archive_pin = pin(archive)
    verified = {}
    with tarfile.open(archive, "r|gz") as tar:
        for item in tar:
            require(item.name in records and item.name not in verified and item.isfile(),
                    "archive contains an extra, duplicate or non-regular member")
            expected = records[item.name]
            require(item.size == expected["bytes"] and item.mode == 0o600
                    and item.uid == item.gid == item.mtime == 0
                    and item.uname == item.gname == "", "archive metadata changed")
            digest = hashlib.sha256()
            size = 0
            stream = tar.extractfile(item)
            require(stream is not None, "archive member is unreadable")
            with stream:
                while chunk := stream.read(BLOCK):
                    size += len(chunk)
                    digest.update(chunk)
            verified[item.name] = {"bytes": size, "sha256": digest.hexdigest()}
            require(verified[item.name] == expected, f"archive pin mismatch: {item.name}")
    require(verified == copied == records, "archive and copied inventory differ")

    repeat = DigestSink()
    write_archive(repeat, source, records)
    require(archive_pin == {"bytes": repeat.bytes, "sha256": repeat.digest.hexdigest()},
            "independent deterministic archive reproduction differs")
    for name, expected in records.items():
        require(pin(source_path(name)) == expected, f"source changed during build: {name}")
        require(pin(source / name) == expected, f"copy changed during verification: {name}")
    require(pin(COPY_LIST)["sha256"] == COPY_SHA, "copy-list changed during build")

    manifest = {
        "schema": "hydra-p7-sealed-source-data-bundle-v1", "status": "SEALED",
        "file_count": len(records), "expanded_bytes": sum(p["bytes"] for p in records.values()),
        "archive": "source-data.tar.gz", "archive_bytes": archive_pin["bytes"],
        "archive_sha256": archive_pin["sha256"], "files": records,
        "copy_list_sha256": COPY_SHA, "native_controller_source_map_sha256": MAP_SHA,
        "selection_sha256": SELECTION_SHA, "dataset_manifest_sha256": DATA_SHA,
        "includes_frameworks": approved["includes_frameworks"],
        "includes_teacher_weights": approved["includes_teacher_weights"],
        "automatic_launch": False, "model_calls": 0, "native_proof_runs": 0,
        "solver_runs": 0, "gpu_allocations": 0, "uploads": 0,
        "preserved_source_substitution": {PUBLISHER: PRESERVED.relative_to(ROOT).as_posix()},
        "deterministic_tar": {"ordering": "sorted-posix-path", "format": "pax",
                              "mode": "0600", "mtime": 0, "uid": 0, "gid": 0,
                              "uname": "", "gname": "", "gzip_mtime": 0,
                              "gzip_filename": "", "gzip_level": 9},
    }
    write_json(OUT / "manifest.json", manifest)
    write_json(OUT / "verification.json", {
        "schema": "hydra-p7-sealed-bundle-verification-v1", "status": "verified",
        "verified_copy_files": len(copied), "verified_archive_files": len(verified),
        "verified_originals_after": len(records), "archive_reproduced_identically": True,
        "copy_matches_archive_matches_approved": True, "files": verified,
        "source_map_declaration_sha256": MAP_SHA, "selection_sha256": SELECTION_SHA,
        "builder": pin(Path(__file__)), "python": sys.version.split()[0],
        "elapsed_seconds": time.monotonic() - started,
        "cpu_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime
                       + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        "peak_rss_native_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_units": "bytes" if sys.platform == "darwin" else "KiB",
    })
    seal = {
        "schema": "hydra-p7-source-bundle-seal-v1", "status": "SEALED",
        "archive": archive_pin,
        "manifest": pin(OUT / "manifest.json"),
        "verification": pin(OUT / "verification.json"),
        "copy_list": pin(OUT / "copy-list-v1.json"),
        "build_plan": pin(OUT / "build-plan.json"), "builder": pin(Path(__file__)),
        "file_count": 1273, "expanded_bytes": 111330633,
        "native_controller_source_map_sha256": MAP_SHA, "selection_sha256": SELECTION_SHA,
        "scope_extended": False, "source_files_modified": False,
        "project_imports": 0, "native_proof_runs": 0, "model_calls": 0,
        "solver_runs": 0, "gpu_allocations": 0, "uploads": 0,
    }
    write_json(OUT / "SEALED.json", seal)
    for path in OUT.iterdir():
        if path.is_file():
            path.chmod(0o400)
    for path in source.rglob("*"):
        if path.is_dir():
            path.chmod(0o500)
    source.chmod(0o500)
    signal.alarm(0)
    print(json.dumps({"status": "SEALED", "directory": OUT.relative_to(ROOT).as_posix(),
                      "archive": archive_pin, "manifest": seal["manifest"],
                      "seal": pin(OUT / "SEALED.json"), "file_count": 1273,
                      "expanded_bytes": 111330633,
                      "elapsed_seconds": time.monotonic() - started}, sort_keys=True))


if __name__ == "__main__":
    main()
