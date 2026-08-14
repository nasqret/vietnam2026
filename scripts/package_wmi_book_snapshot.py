#!/usr/bin/env python3
"""Create a canonical, content-addressed WMI Jupyter Book snapshot.

The archive deliberately contains only the book and the repository inputs
needed by the WMI build and its non-executing integrity gates.  Generated
book output, virtual environments, caches, and host metadata are excluded.
Tar metadata is normalized so identical input bytes produce an identical
archive SHA-256 on every host supported by Python's standard library.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile


REPO = Path(__file__).resolve().parents[1]

TREE_INPUTS = (
    Path("book"),
    Path("artifacts/peano-library"),
    Path("artifacts/peano-hydra/l0-documentation-candidate-v1"),
    Path("research/arithmetic-library"),
    # The proof-explorer generator reads the theorem stack as well as the
    # native term/formula grammar, PA axioms, proof constructors, and tactic
    # registry.  Snapshot the complete package rather than relying on WMI's
    # ambient checkout for any part of that evidence boundary.
    Path("peano-lab/py/peano_lab"),
    # The selected-library page checker imports the complete Hydra package and
    # reconstructs its pages only from the retained five-file documentation
    # bundle above.  Keep that import/evidence boundary inside the snapshot.
    Path("training/peano_hydra"),
)

FILE_INPUTS = (
    Path("requirements.txt"),
    Path("scripts/build_arithmetic_book_atlas.py"),
    Path("scripts/build_pa_defined_explorer.py"),
    Path("scripts/build_pa_proof_explorer.py"),
    Path("scripts/build_peano_hydra_library_pages.py"),
    Path("scripts/check_wmi_book_build.py"),
    Path("scripts/package_wmi_book_snapshot.py"),
    Path("scripts/run_wmi_book_build.py"),
    Path("scripts/submit_wmi_book_build.sh"),
    Path("slurm/peano_wmi_book_build.sbatch"),
    Path(
        "artifacts/peano-hydra/"
        "library-page-deployment-candidate-v1-readiness.json"
    ),
)

EXCLUDED_PARTS = {
    "_build",
    "__pycache__",
    ".ipynb_checkpoints",
}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


@dataclass(frozen=True, slots=True)
class SnapshotEntry:
    """One immutable path/mode/payload observation used by every digest."""

    relative: Path
    mode: int
    payload: bytes


def _excluded(relative: Path) -> bool:
    return (
        any(part in EXCLUDED_PARTS for part in relative.parts)
        or relative.name in EXCLUDED_NAMES
        or relative.suffix in EXCLUDED_SUFFIXES
    )


def snapshot_files(root: Path = REPO) -> tuple[Path, ...]:
    """Return the exact sorted regular-file boundary for one snapshot."""

    root = root.resolve()
    files: set[Path] = set()
    for relative_tree in TREE_INPUTS:
        tree = root / relative_tree
        if not tree.is_dir() or tree.is_symlink():
            raise ValueError(f"missing or unsafe snapshot tree: {relative_tree}")
        for path in tree.rglob("*"):
            relative = path.relative_to(root)
            if _excluded(relative):
                continue
            if path.is_symlink():
                raise ValueError(f"snapshot input must not be a symlink: {relative}")
            if path.is_file():
                files.add(relative)
    for relative in FILE_INPUTS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or unsafe snapshot file: {relative}")
        files.add(relative)
    return tuple(sorted(files, key=lambda item: item.as_posix()))


def _output_identity(output: Path, root: Path) -> tuple[int, int] | None:
    """Reject repository outputs and safely identify an existing destination."""

    root = root.resolve()
    if output.is_symlink():
        raise ValueError("snapshot output must not be a symlink")
    resolved = output.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("snapshot output must be outside the repository")
    if not output.exists():
        return None
    observed = output.stat()
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError("existing snapshot output must be a regular file")
    return observed.st_dev, observed.st_ino


def snapshot_entries(
    root: Path = REPO,
    *,
    output_identity: tuple[int, int] | None = None,
) -> tuple[SnapshotEntry, ...]:
    """Read every selected payload and executable-mode bit exactly once."""

    root = root.resolve()
    entries: list[SnapshotEntry] = []
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    for relative in snapshot_files(root):
        path = root / relative
        descriptor = os.open(path, os.O_RDONLY | nofollow | cloexec)
        try:
            observed = os.fstat(descriptor)
            if not stat.S_ISREG(observed.st_mode):
                raise ValueError(f"snapshot input is not a regular file: {relative}")
            if output_identity == (observed.st_dev, observed.st_ino):
                raise ValueError(f"snapshot output is hardlinked to input: {relative}")
            with os.fdopen(descriptor, "rb", closefd=False) as source:
                payload = source.read()
            if len(payload) != observed.st_size:
                raise ValueError(f"snapshot input changed size while read: {relative}")
            entries.append(
                SnapshotEntry(
                    relative=relative,
                    mode=0o755 if observed.st_mode & stat.S_IXUSR else 0o644,
                    payload=payload,
                )
            )
        finally:
            os.close(descriptor)
    return tuple(entries)


def _snapshot_metadata(entries: tuple[SnapshotEntry, ...]) -> dict[str, object]:
    """Hash one immutable entry table without touching the filesystem."""

    manifest = hashlib.sha256()
    total_bytes = 0
    for entry in entries:
        digest = hashlib.sha256(entry.payload).hexdigest()
        total_bytes += len(entry.payload)
        manifest.update(entry.relative.as_posix().encode("utf-8"))
        manifest.update(b"\0")
        manifest.update(str(len(entry.payload)).encode("ascii"))
        manifest.update(b"\0")
        manifest.update(b"x" if entry.mode & 0o111 else b"-")
        manifest.update(b"\0")
        manifest.update(digest.encode("ascii"))
        manifest.update(b"\n")
    return {
        "content_manifest_sha256": manifest.hexdigest(),
        "file_count": len(entries),
        "total_bytes": total_bytes,
    }


def snapshot_metadata(root: Path = REPO) -> dict[str, object]:
    """Read the selected inputs once and return their content metadata."""

    return _snapshot_metadata(snapshot_entries(root))


def build_archive(output: Path, root: Path = REPO) -> dict[str, object]:
    """Write a normalized GNU tar archive and return strict JSON metadata."""

    root = root.resolve()
    output = output.absolute()
    identity = _output_identity(output, root)
    entries = snapshot_entries(root, output_identity=identity)
    if identity is not None:
        raise ValueError("snapshot output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, mode="x", format=tarfile.GNU_FORMAT) as archive:
        for entry in entries:
            info = tarfile.TarInfo(entry.relative.as_posix())
            info.size = len(entry.payload)
            info.mode = entry.mode
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(entry.payload))
    metadata = _snapshot_metadata(entries)
    metadata.update(
        {
            "archive_bytes": output.stat().st_size,
            "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "format": "peano-wmi-book-snapshot",
            "version": 1,
        }
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()
    if args.manifest_only == (args.output is not None):
        parser.error("choose exactly one of --output or --manifest-only")
    payload = (
        snapshot_metadata(REPO)
        if args.manifest_only
        else build_archive(args.output, REPO)
    )
    print(json.dumps(payload, allow_nan=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
