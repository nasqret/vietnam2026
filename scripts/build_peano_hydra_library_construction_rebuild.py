#!/usr/bin/env python3
"""Build or check the candidate Peano Hydra A2.2 construction sidecar."""

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

from training.peano_hydra.library_construction_rebuild import (  # noqa: E402
    LibraryConstructionRebuildError,
    build_candidate_construction_rebuild,
    canonical_document_bytes,
)


SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json"
)


def _lexical_absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("output path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryConstructionRebuildError(
                    "output parent contains a link or non-directory component"
                )
        return current
    except LibraryConstructionRebuildError:
        raise
    except OSError as exc:
        raise LibraryConstructionRebuildError("cannot inspect output parent") from exc


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryConstructionRebuildError(
            "cannot inspect output destination"
        ) from exc
    raise LibraryConstructionRebuildError(
        "output destination already exists; use --check to verify it"
    )


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
        raise LibraryConstructionRebuildError("cannot stage output document") from exc


def _publish(path: Path, raw: bytes) -> None:
    destination = _lexical_absolute(path)
    parent = _safe_parent(destination)
    _require_absent(destination)
    temporary = _stage(destination, raw)
    published_identity: tuple[int, int] | None = None
    try:
        _require_absent(destination)
        source = temporary.lstat()
        os.link(temporary, destination, follow_symlinks=False)
        published_identity = (source.st_dev, source.st_ino)
        published = destination.lstat()
        if (
            not stat.S_ISREG(published.st_mode)
            or stat.S_ISLNK(published.st_mode)
            or (published.st_dev, published.st_ino) != published_identity
        ):
            raise LibraryConstructionRebuildError(
                "published destination identity is malformed"
            )
        temporary.unlink()
        descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except (LibraryConstructionRebuildError, OSError) as exc:
        if published_identity is not None:
            try:
                identity = destination.lstat()
                if (
                    stat.S_ISREG(identity.st_mode)
                    and not stat.S_ISLNK(identity.st_mode)
                    and (identity.st_dev, identity.st_ino) == published_identity
                ):
                    destination.unlink()
            except OSError:
                pass
        if isinstance(exc, LibraryConstructionRebuildError):
            raise
        raise LibraryConstructionRebuildError("cannot publish output document") from exc
    finally:
        try:
            temporary.unlink()
        except (FileNotFoundError, OSError):
            pass


def _read_exact(path: Path, expected: bytes) -> None:
    destination = _lexical_absolute(path)
    _safe_parent(destination)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(destination, flags)
    except OSError as exc:
        raise LibraryConstructionRebuildError(
            "cannot open construction rebuild for --check"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size != len(expected):
            raise LibraryConstructionRebuildError(
                "construction rebuild differs from the deterministic build"
            )
        chunks: list[bytes] = []
        remaining = len(expected) + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        actual = b"".join(chunks)
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
            raise LibraryConstructionRebuildError(
                "construction rebuild changed during --check"
            )
    except OSError as exc:
        raise LibraryConstructionRebuildError(
            "cannot read construction rebuild for --check"
        ) from exc
    finally:
        os.close(descriptor)
    if actual != expected:
        raise LibraryConstructionRebuildError(
            "construction rebuild differs from the deterministic build"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "No retained file is written by default. Suggested path: "
            f"{SUGGESTED_OUTPUT}"
        ),
    )
    parser.add_argument(
        "--output", type=Path, help="atomically publish the canonical sidecar"
    )
    parser.add_argument(
        "--check", action="store_true", help="compare an existing --output"
    )
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error("--check requires --output")

    document = build_candidate_construction_rebuild(repository_root=ROOT)
    raw = canonical_document_bytes(document)
    if args.check:
        _read_exact(args.output, raw)
    elif args.output is not None:
        _publish(args.output, raw)

    aggregate = document["aggregate"]
    print(
        f"candidate: {aggregate['rebuilt_theorem_count']} rebuilt theorems, "
        f"{aggregate['direct_edges_removed_in_candidate_rebuilds']} direct "
        f"Cut-spine edges removed, retained public graph "
        f"{aggregate['retained_public_graph_edges']}, root "
        f"{document['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except LibraryConstructionRebuildError as exc:
        raise SystemExit(str(exc)) from None
