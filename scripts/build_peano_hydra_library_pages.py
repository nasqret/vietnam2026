#!/usr/bin/env python3
"""Build or check the selected-only Peano Hydra candidate page tree."""

from __future__ import annotations

import argparse
import json
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

import training.peano_hydra.library_page_deployment as page_module  # noqa: E402
from training.peano_hydra.library_page_deployment import (  # noqa: E402
    LibraryPageDeploymentError,
    canonical_document_bytes,
    load_library_page_deployment,
)


SUGGESTED_OUTPUT = Path("book/_static/pa-selected-library")
SUGGESTED_REPORT = Path(
    "artifacts/peano-hydra/library-page-deployment-candidate-v1-readiness.json"
)
INCOMPLETE = ".incomplete"


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    parent = _lexical_absolute(path).parent
    try:
        observed = parent.lstat()
        if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
            raise LibraryPageDeploymentError(
                "output parent must be a non-symlink directory"
            )
        resolved = parent.resolve(strict=True)
    except LibraryPageDeploymentError:
        raise
    except OSError as exc:
        raise LibraryPageDeploymentError("cannot resolve output parent") from exc
    if resolved != parent:
        raise LibraryPageDeploymentError(
            "output parent path must not contain symlink components"
        )
    return resolved


def _require_absent(path: Path, *, label: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryPageDeploymentError(f"cannot inspect {label}") from exc
    raise LibraryPageDeploymentError(f"{label} already exists; use --check")


def _write_exact_file(path: Path, raw: bytes, *, mode: int = 0o644) -> tuple[int, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise LibraryPageDeploymentError(
            f"cannot create output member {path.name!r}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(descriptor)
        os.fchmod(descriptor, mode)
        observed = os.fstat(descriptor)
        os.fsync(descriptor)
        return observed.st_dev, observed.st_ino
    except OSError as exc:
        raise LibraryPageDeploymentError(
            f"cannot write output member {path.name!r}"
        ) from exc
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _expected_directories(files: dict[str, bytes]) -> tuple[str, ...]:
    values = {
        parent.as_posix()
        for relative in files
        for parent in Path(relative).parents
        if parent != Path(".")
    }
    return tuple(sorted(values, key=lambda value: (value.count("/"), value)))


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        observed = path.lstat()
    except OSError:
        return None
    return observed.st_dev, observed.st_ino


def _unlink_if_identity(path: Path, identity: tuple[int, int] | None) -> None:
    if identity is None or _identity(path) != identity:
        return
    try:
        path.unlink()
    except OSError:
        pass


def _cleanup_claimed_tree(
    destination: Path,
    destination_identity: tuple[int, int] | None,
    files: dict[str, bytes],
    file_identities: dict[str, tuple[int, int]],
    directory_identities: dict[str, tuple[int, int]],
) -> None:
    if destination_identity is None or _identity(destination) != destination_identity:
        return
    for relative in files:
        _unlink_if_identity(
            destination / relative, file_identities.get(relative)
        )
    _unlink_if_identity(
        destination / INCOMPLETE, file_identities.get(INCOMPLETE)
    )
    for relative in reversed(_expected_directories(files)):
        if _identity(destination / relative) != directory_identities.get(relative):
            continue
        try:
            (destination / relative).rmdir()
        except FileNotFoundError:
            pass
        except OSError:
            return
    try:
        destination.rmdir()
    except OSError:
        pass


def _publish(
    output: Path,
    report_path: Path,
    files: dict[str, bytes],
    report: dict[str, object],
) -> None:
    if not isinstance(output, Path) or not isinstance(report_path, Path):
        raise TypeError("output and report paths must be pathlib.Path values")
    output = _lexical_absolute(output)
    report_path = _lexical_absolute(report_path)
    output_parent = _safe_parent(output)
    report_parent = _safe_parent(report_path)
    _require_absent(output, label="output directory")
    _require_absent(report_path, label="readiness report")
    report_raw = canonical_document_bytes(report)
    report_descriptor, report_temp_text = tempfile.mkstemp(
        prefix=f".{report_path.name}.", suffix=".staging", dir=report_parent
    )
    os.close(report_descriptor)
    report_temp = Path(report_temp_text)
    # mkstemp created the file; replace it with the same no-follow writer path.
    report_temp.unlink()
    report_temp_identity: tuple[int, int] | None = None
    published_report_identity: tuple[int, int] | None = None
    output_identity: tuple[int, int] | None = None
    file_identities: dict[str, tuple[int, int]] = {}
    directory_identities: dict[str, tuple[int, int]] = {}
    success = False
    try:
        report_temp_identity = _write_exact_file(report_temp, report_raw)
        _require_absent(output, label="output directory")
        try:
            os.mkdir(output, 0o755)
        except FileExistsError as exc:
            raise LibraryPageDeploymentError(
                "output directory was created concurrently"
            ) from exc
        output_identity = _identity(output)
        if output_identity is None:
            raise LibraryPageDeploymentError("cannot identify claimed output directory")
        file_identities[INCOMPLETE] = _write_exact_file(
            output / INCOMPLETE, b"candidate page tree is incomplete\n"
        )
        for relative in _expected_directories(files):
            os.mkdir(output / relative, 0o755)
            observed_identity = _identity(output / relative)
            if observed_identity is None:
                raise LibraryPageDeploymentError(
                    "cannot identify claimed output subdirectory"
                )
            directory_identities[relative] = observed_identity
        for relative, raw in files.items():
            file_identities[relative] = _write_exact_file(
                output / relative, raw
            )
        for relative in reversed(_expected_directories(files)):
            _fsync_directory(output / relative)
        _fsync_directory(output)
        (output / INCOMPLETE).unlink()
        _fsync_directory(output)
        _fsync_directory(output_parent)
        if load_library_page_deployment(
            output, repository_root=ROOT
        ) != files:
            raise LibraryPageDeploymentError(
                "published page tree differs from staged bytes"
            )

        # The report is published last with create-if-absent hard-link
        # semantics.  A racing destination is preserved byte-for-byte.
        try:
            os.link(report_temp, report_path)
        except FileExistsError as exc:
            raise LibraryPageDeploymentError(
                "readiness report was created concurrently"
            ) from exc
        published_report_identity = _identity(report_path)
        if published_report_identity != report_temp_identity:
            raise LibraryPageDeploymentError(
                "published readiness report identity drifted"
            )
        report_temp.unlink()
        report_temp_identity = None
        _fsync_directory(report_parent)
        success = True
    except OSError as exc:
        raise LibraryPageDeploymentError("cannot publish selected page tree") from exc
    finally:
        if report_temp_identity is not None:
            _unlink_if_identity(report_temp, report_temp_identity)
        if not success and published_report_identity is not None:
            _unlink_if_identity(report_path, published_report_identity)
        if not success and output_identity is not None:
            _cleanup_claimed_tree(
                output,
                output_identity,
                files,
                file_identities,
                directory_identities,
            )


def _safe_existing_file(path: Path) -> Path:
    lexical = _lexical_absolute(path)
    parent = _safe_parent(lexical)
    if lexical.parent != parent:
        raise LibraryPageDeploymentError(
            "readiness report path contains a symlink component"
        )
    try:
        observed = lexical.lstat()
    except OSError as exc:
        raise LibraryPageDeploymentError("cannot inspect readiness report") from exc
    if not stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
        raise LibraryPageDeploymentError(
            "readiness report must be a non-symlink regular file"
        )
    return lexical


def _read_exact(path: Path, limit: int) -> bytes:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not (0 < before.st_size <= limit):
            raise LibraryPageDeploymentError("readiness report is not bounded")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
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
        ) or len(raw) != before.st_size:
            raise LibraryPageDeploymentError("readiness report changed while read")
        return raw
    finally:
        os.close(descriptor)


def _check(
    output: Path,
    report_path: Path,
    expected_files: dict[str, bytes],
    expected_report: dict[str, object],
) -> None:
    loaded = load_library_page_deployment(output, repository_root=ROOT)
    if loaded != expected_files:
        raise LibraryPageDeploymentError(
            "retained page tree differs from deterministic reconstruction"
        )
    actual_report = _read_exact(_safe_existing_file(report_path), 131_072)
    if actual_report != canonical_document_bytes(expected_report):
        raise LibraryPageDeploymentError(
            "retained readiness report differs from deterministic reconstruction"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "No file is written without both --output-dir and --report. "
            f"Suggested paths: {SUGGESTED_OUTPUT} and {SUGGESTED_REPORT}"
        ),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--check", action="store_true", help="validate retained outputs without writing"
    )
    args = parser.parse_args()
    if (args.output_dir is None) != (args.report is None):
        parser.error("--output-dir and --report must be supplied together")
    if args.check and args.output_dir is None:
        parser.error("--check requires --output-dir and --report")

    files, report = (
        page_module._build_candidate_library_page_deployment_with_readiness(
            repository_root=ROOT
        )
    )
    if args.check:
        _check(args.output_dir, args.report, files, report)
    elif args.output_dir is not None:
        _publish(args.output_dir, args.report, files, report)

    manifest = json.loads(files["manifest.json"])
    print(
        f"candidate page source: {manifest['aggregate']['html_page_count']} HTML pages, "
        f"{manifest['aggregate']['tree_file_count']} files, "
        f"root {manifest['root_sha256']}; deployed=false",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except LibraryPageDeploymentError as exc:
        raise SystemExit(str(exc)) from None
