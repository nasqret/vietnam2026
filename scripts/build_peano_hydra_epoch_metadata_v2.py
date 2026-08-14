#!/usr/bin/env python3
"""Build or check the candidate Peano Hydra epoch-metadata v2 ledger."""

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

from training.peano_hydra.library_epoch_metadata_v2 import (  # noqa: E402
    LibraryEpochMetadataV2Error,
    _build_candidate_epoch_metadata_v2_with_readiness,
    canonical_document_bytes,
)


SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v2.json"
)
SUGGESTED_REPORT = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v2-readiness.json"
)


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    parts = absolute.parent.parts
    current = Path(parts[0])
    try:
        for part in parts[1:]:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryEpochMetadataV2Error(
                    "output parent contains a link or non-directory component"
                )
        return current
    except LibraryEpochMetadataV2Error:
        raise
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(
            "cannot inspect output parent"
        ) from exc


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(
            "cannot inspect output destination"
        ) from exc
    raise LibraryEpochMetadataV2Error(
        "output destination already exists; use --check to verify it"
    )


def _validate_destinations(
    output: Path | None, report: Path | None, *, check: bool
) -> list[tuple[Path, str]]:
    requested = [
        (path, label)
        for path, label in (
            (output, "candidate metadata-v2"),
            (report, "candidate readiness-v2"),
        )
        if path is not None
    ]
    absolute = [_lexical_absolute(path) for path, _label in requested]
    if len(set(absolute)) != len(absolute):
        raise LibraryEpochMetadataV2Error(
            "metadata and readiness destinations must differ"
        )
    result: list[tuple[Path, str]] = []
    for (path, label), destination in zip(requested, absolute, strict=True):
        _safe_parent(destination)
        if not check:
            _require_absent(destination)
        result.append((destination, label))
    return result


def _stage(path: Path, raw: bytes) -> Path:
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        return Path(temporary)
    except OSError as exc:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        raise LibraryEpochMetadataV2Error("cannot stage output document") from exc


def _publish_all(documents: list[tuple[Path, bytes]]) -> None:
    for path, _raw in documents:
        _safe_parent(path)
        _require_absent(path)
    staged: list[tuple[Path, Path]] = []
    published: list[tuple[Path, tuple[int, int]]] = []
    try:
        for path, raw in documents:
            staged.append((path, _stage(path, raw)))
        for path, temporary in staged:
            _require_absent(path)
            # A same-filesystem hard link is an atomic create-if-absent.
            # Unlike rename, it cannot overwrite a destination introduced
            # after the preceding inspection.
            source_identity = temporary.lstat()
            os.link(temporary, path, follow_symlinks=False)
            identity = path.lstat()
            expected_identity = (source_identity.st_dev, source_identity.st_ino)
            if (
                not stat.S_ISREG(identity.st_mode)
                or stat.S_ISLNK(identity.st_mode)
                or (identity.st_dev, identity.st_ino) != expected_identity
            ):
                raise LibraryEpochMetadataV2Error(
                    "published destination identity is malformed"
                )
            published.append((path, expected_identity))
            temporary.unlink()
        for parent in {path.parent for path, _raw in documents}:
            descriptor = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except (LibraryEpochMetadataV2Error, OSError) as exc:
        for path, expected_identity in published:
            try:
                identity = path.lstat()
                if (
                    stat.S_ISREG(identity.st_mode)
                    and not stat.S_ISLNK(identity.st_mode)
                    and (identity.st_dev, identity.st_ino) == expected_identity
                ):
                    path.unlink()
            except OSError:
                pass
        if isinstance(exc, LibraryEpochMetadataV2Error):
            raise
        raise LibraryEpochMetadataV2Error("cannot publish output documents") from exc
    finally:
        for _path, temporary in staged:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def _read_exact(path: Path, expected: bytes, label: str) -> None:
    _safe_parent(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(f"cannot open {label} for --check") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size != len(expected):
            raise LibraryEpochMetadataV2Error(
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
            raise LibraryEpochMetadataV2Error(f"{label} changed during --check")
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(f"cannot read {label} for --check") from exc
    finally:
        os.close(descriptor)
    if actual != expected:
        raise LibraryEpochMetadataV2Error(
            f"{label} differs from the deterministic build"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "No retained file is written by default. Suggested names: "
            f"{SUGGESTED_OUTPUT} and {SUGGESTED_REPORT}"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the canonical candidate successor ledger",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="write the closed candidate-readiness report",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare explicit destinations without writing",
    )
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error("--check requires --output")
    destinations = _validate_destinations(
        args.output, args.report, check=args.check
    )

    metadata, report = _build_candidate_epoch_metadata_v2_with_readiness(
        repository_root=ROOT
    )
    metadata_raw = canonical_document_bytes(metadata)
    report_raw = canonical_document_bytes(report)
    values = {
        "candidate metadata-v2": metadata_raw,
        "candidate readiness-v2": report_raw,
    }
    if args.check:
        for path, label in destinations:
            _read_exact(path, values[label], label)
    elif destinations:
        _publish_all([(path, values[label]) for path, label in destinations])
    else:
        sys.stdout.buffer.write(metadata_raw)
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        main()
    except LibraryEpochMetadataV2Error as exc:
        raise SystemExit(str(exc)) from None
