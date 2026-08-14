#!/usr/bin/env python3
"""Build or check the isolated Peano Hydra candidate documentation bundle."""

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

from training.peano_hydra.library_documentation_bundle import (  # noqa: E402
    LibraryDocumentationBundleError,
    build_candidate_documentation_bundle,
    canonical_document_bytes,
    load_documentation_bundle,
)


SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/l0-documentation-candidate-v1"
)
DOCUMENT_FILES = (
    "schema.json",
    "explicit.json",
    "defined.json",
    "isolation-receipt.json",
    "manifest.json",
)


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    parent = _lexical_absolute(path).parent
    try:
        metadata = parent.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise LibraryDocumentationBundleError(
                "output parent must be a non-symlink directory"
            )
        resolved = parent.resolve(strict=True)
        if resolved != parent:
            raise LibraryDocumentationBundleError(
                "output parent path must not contain symlink components"
            )
        return resolved
    except OSError as exc:
        raise LibraryDocumentationBundleError("cannot resolve output parent") from exc


def _destination_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            "cannot inspect output destination"
        ) from exc
    raise LibraryDocumentationBundleError(
        "output directory already exists; use --check for an existing bundle"
    )


def _write_exact_file(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            f"cannot create staged member {path.name!r}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(descriptor)
        os.fchmod(descriptor, 0o644)
        os.fsync(descriptor)
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            f"cannot write staged member {path.name!r}"
        ) from exc
    finally:
        os.close(descriptor)


def _cleanup_staging(path: Path) -> None:
    try:
        for filename in DOCUMENT_FILES:
            try:
                (path / filename).unlink()
            except FileNotFoundError:
                pass
        path.rmdir()
    except OSError:
        # Preserve the original build/publication exception.  The mkdtemp
        # name remains visible for manual inspection if cleanup itself fails.
        pass


def _publish_atomic(
    destination: Path, documents: dict[str, dict[str, object]]
) -> None:
    if not isinstance(destination, Path):
        raise TypeError("output directory must be a pathlib.Path")
    destination = _lexical_absolute(destination)
    parent = _safe_parent(destination)
    _destination_absent(destination)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.", suffix=".staging", dir=parent
        )
    )
    published = False
    try:
        os.chmod(staging, 0o755)
        for filename in DOCUMENT_FILES:
            _write_exact_file(
                staging / filename,
                canonical_document_bytes(documents[filename]),
            )
        directory_descriptor = os.open(staging, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        # Revalidate staged canonical bytes and fixed-source reconstruction
        # before making the directory visible under its final name.
        load_documentation_bundle(staging, repository_root=ROOT)
        _destination_absent(destination)
        os.rename(staging, destination)
        published = True
        parent_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            "cannot publish staged documentation directory"
        ) from exc
    finally:
        if not published:
            _cleanup_staging(staging)


def _check_exact(
    directory: Path, expected: dict[str, dict[str, object]]
) -> None:
    loaded = load_documentation_bundle(directory, repository_root=ROOT)
    for filename in DOCUMENT_FILES:
        if canonical_document_bytes(loaded[filename]) != canonical_document_bytes(
            expected[filename]
        ):
            raise LibraryDocumentationBundleError(
                f"documentation member {filename!r} differs from deterministic build"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "No file is written without --output-dir. Suggested retained path: "
            f"{SUGGESTED_OUTPUT}"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="atomically publish the exact five-file candidate directory",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check an existing --output-dir without writing",
    )
    args = parser.parse_args()
    if args.check and args.output_dir is None:
        parser.error("--check requires --output-dir")

    documents = build_candidate_documentation_bundle(repository_root=ROOT)
    if args.check:
        _check_exact(args.output_dir, documents)
    elif args.output_dir is not None:
        _publish_atomic(args.output_dir, documents)

    manifest = documents["manifest.json"]
    print(
        f"candidate: {manifest['aggregate']['theorem_count']} theorems, "
        f"{manifest['aggregate']['declared_dependency_edges']} declared edges, "
        f"root {manifest['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except LibraryDocumentationBundleError as exc:
        raise SystemExit(str(exc)) from None
