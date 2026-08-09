#!/usr/bin/env python3
"""Build or check candidate-only Peano Hydra library epoch metadata."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
for import_root in (str(PY_ROOT), str(ROOT)):
    while import_root in sys.path:
        sys.path.remove(import_root)
sys.path[:0] = [str(PY_ROOT), str(ROOT)]

from training.peano_hydra.library_epoch_metadata import (  # noqa: E402
    LibraryEpochMetadataError,
    build_candidate_epoch_metadata,
    canonical_document_bytes,
    readiness_report,
)


SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json"
)
SUGGESTED_REPORT = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1-readiness.json"
)


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _validate_destinations(output: Path | None, report: Path | None) -> None:
    if output is None or report is None:
        return
    if (
        _absolute_lexical(output) == _absolute_lexical(report)
        or output.resolve(strict=False) == report.resolve(strict=False)
    ):
        raise LibraryEpochMetadataError(
            "metadata and readiness report destinations must differ"
        )


def _existing_destination_is_safe(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryEpochMetadataError(f"cannot inspect destination {path}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryEpochMetadataError(
            f"destination {path} must be absent or a non-symlink regular file"
        )


def _write_atomic(path: Path, raw: bytes) -> None:
    if not isinstance(path, Path):
        raise TypeError("output destination must be a pathlib.Path")
    parent = path.parent
    if not parent.is_dir():
        raise LibraryEpochMetadataError(
            f"destination parent must be an existing directory: {parent}"
        )
    _existing_destination_is_safe(path)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o644)
        # Recheck immediately before publication so an existing destination
        # cannot silently change from a regular file into a link or directory.
        _existing_destination_is_safe(path)
        os.replace(temporary_name, path)
        temporary_name = None
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _check_exact(path: Path, expected: bytes, label: str) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryEpochMetadataError(f"cannot read {label} for --check") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size != len(expected):
            raise LibraryEpochMetadataError(
                f"{label} differs from the deterministic build"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            actual = stream.read(len(expected) + 1)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise LibraryEpochMetadataError(f"{label} changed during --check")
    except OSError as exc:
        raise LibraryEpochMetadataError(f"cannot read {label} for --check") from exc
    finally:
        os.close(descriptor)
    if actual != expected:
        raise LibraryEpochMetadataError(f"{label} differs from the deterministic build")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Suggested retained names (not written by default): "
            f"{SUGGESTED_OUTPUT} and {SUGGESTED_REPORT}"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="atomically write the canonical candidate ledger (default: stdout)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="atomically write the compact candidate-readiness report",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare --output and optional --report without writing",
    )
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error("--check requires --output")
    _validate_destinations(args.output, args.report)

    metadata = build_candidate_epoch_metadata(repository_root=ROOT)
    metadata_raw = canonical_document_bytes(metadata)
    report_raw = canonical_document_bytes(readiness_report(metadata, repository_root=ROOT))

    if args.check:
        _check_exact(args.output, metadata_raw, "candidate epoch metadata")
        if args.report is not None:
            _check_exact(args.report, report_raw, "candidate readiness report")
    else:
        if args.output is None:
            sys.stdout.buffer.write(metadata_raw)
            sys.stdout.buffer.flush()
        else:
            _write_atomic(args.output, metadata_raw)
        if args.report is not None:
            _write_atomic(args.report, report_raw)

    if args.output is not None:
        print(
            f"candidate: {metadata['theorem_count']} theorems, "
            f"{metadata['aggregate']['declared_dependency_edges']} declared edges, "
            f"root {metadata['root_sha256']}",
            flush=True,
        )


if __name__ == "__main__":
    try:
        main()
    except LibraryEpochMetadataError as exc:
        raise SystemExit(str(exc)) from None
