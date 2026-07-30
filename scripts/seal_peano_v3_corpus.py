#!/usr/bin/env python3
"""Create or independently verify an immutable Peano model-v3 corpus seal."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType


SCRIPT_PATH = Path(os.path.abspath(__file__))
REPOSITORY_ROOT = SCRIPT_PATH.parents[1]
_CLI_RELATIVE_PATH = Path("scripts/seal_peano_v3_corpus.py")
_MODULE_RELATIVE_PATH = Path("training/peano_policy/corpus_seal.py")
_STANDALONE_DIRECTORIES = frozenset(
    {
        Path("scripts"),
        Path("training"),
        Path("training/peano_policy"),
    }
)
_STANDALONE_FILES = frozenset({_CLI_RELATIVE_PATH, _MODULE_RELATIVE_PATH})
_SHA256_HEXDIGEST_LENGTH = 64


class BootstrapError(ValueError):
    """The standalone sealing program is incomplete, mutable, or unexpected."""


def _stable_regular_source(path: Path, *, single_link: bool) -> bytes:
    """Read one source file without following links or accepting replacement."""

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        before = os.lstat(path)
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise BootstrapError(f"cannot open reviewed source {path}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise BootstrapError(f"reviewed source is not one stable regular file: {path}")
        if single_link and (before.st_nlink != 1 or opened.st_nlink != 1):
            raise BootstrapError(f"reviewed source has a hard-link alias: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = os.lstat(path)
    except OSError as exc:
        raise BootstrapError(f"reviewed source disappeared after reading: {path}") from exc
    identity = lambda value: (  # noqa: E731 - compact immutable stat projection
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    if identity(before) != identity(opened) or identity(opened) != identity(after_open):
        raise BootstrapError(f"reviewed source changed while being read: {path}")
    if identity(after_open) != identity(after_path):
        raise BootstrapError(f"reviewed source path was replaced while being read: {path}")
    return b"".join(chunks)


def _sha256_argument(value: str, label: str) -> str:
    if (
        len(value) != _SHA256_HEXDIGEST_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise BootstrapError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _standalone_sources(
    root: Path,
    *,
    cli_sha256: str,
    module_sha256: str,
    _running_cli: Path = SCRIPT_PATH,
) -> dict[Path, bytes]:
    """Validate and read the complete cache-free standalone bootstrap tree."""

    if not root.is_absolute() or ".." in root.parts:
        raise BootstrapError("standalone root must be one absolute traversal-free path")
    if root / _CLI_RELATIVE_PATH != _running_cli:
        raise BootstrapError(
            f"standalone root {root} does not contain the running CLI {_running_cli}"
        )
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise BootstrapError(f"cannot inspect standalone root {root}: {exc}") from exc
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise BootstrapError("standalone root must be one non-symlink directory")

    expected = _STANDALONE_DIRECTORIES | _STANDALONE_FILES
    seen: dict[Path, str] = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise BootstrapError(f"cannot enumerate standalone tree {directory}: {exc}") from exc
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts:
                raise BootstrapError(
                    f"standalone tree contains forbidden bytecode cache: {relative}"
                )
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise BootstrapError(f"cannot inspect standalone entry {relative}: {exc}") from exc
            if stat.S_ISLNK(metadata.st_mode):
                kind = "symlink"
            elif stat.S_ISDIR(metadata.st_mode):
                kind = "directory"
                pending.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                kind = "file"
            else:
                kind = "special"
            seen[relative] = kind

    if set(seen) != expected:
        missing = sorted(path.as_posix() for path in expected - set(seen))
        unexpected = sorted(path.as_posix() for path in set(seen) - expected)
        raise BootstrapError(
            "standalone inventory differs from the reviewed two-file program: "
            f"missing={missing}, unexpected={unexpected}"
        )
    wrong_types = sorted(
        path.as_posix()
        for path in _STANDALONE_DIRECTORIES
        if seen[path] != "directory"
    ) + sorted(
        path.as_posix() for path in _STANDALONE_FILES if seen[path] != "file"
    )
    if wrong_types:
        raise BootstrapError(
            f"standalone inventory contains wrong entry types: {wrong_types}"
        )

    expected_hashes = {
        _CLI_RELATIVE_PATH: _sha256_argument(cli_sha256, "standalone CLI digest"),
        _MODULE_RELATIVE_PATH: _sha256_argument(
            module_sha256, "standalone module digest"
        ),
    }
    sources: dict[Path, bytes] = {}
    for relative, expected_sha256 in expected_hashes.items():
        source = _stable_regular_source(root / relative, single_link=True)
        actual_sha256 = hashlib.sha256(source).hexdigest()
        if actual_sha256 != expected_sha256:
            raise BootstrapError(
                f"standalone source digest mismatch for {relative}: "
                f"expected {expected_sha256}, got {actual_sha256}"
            )
        sources[relative] = source
    return sources


def _load_corpus_seal(source: bytes, location: Path) -> ModuleType:
    """Compile the reviewed source directly, without package or bytecode import.

    The first corpus must be sealed while the historical source tree and its
    unsealed ``data/`` directory are still live.  That old tree necessarily
    predates this module.  The bootstrap is deliberately a two-source program:
    loading ``training.peano_policy`` would execute its package marker and may
    consume unreviewed cached bytecode.  Compiling the already verified bytes
    keeps the executable closure explicit and cache-free.
    """

    sys.dont_write_bytecode = True
    module = ModuleType("_peano_standalone_corpus_seal")
    module.__file__ = str(location)
    module.__package__ = ""
    code = compile(source, str(location), "exec", dont_inherit=True, optimize=0)
    exec(code, module.__dict__)
    return module


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--standalone-root",
        type=Path,
        help="require the exact reviewed two-file bootstrap rooted here",
    )
    parser.add_argument("--standalone-cli-sha256")
    parser.add_argument("--standalone-module-sha256")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create",
        help="validate and atomically publish a new non-overwriting seal",
    )
    create.add_argument("--artifact-dir", type=Path, required=True)
    create.add_argument("--dataset-attestation", type=Path, required=True)
    create.add_argument("--token-audit", type=Path, required=True)
    create.add_argument("--runtime-smoke", type=Path, required=True)
    create.add_argument("--destination", type=Path, required=True)
    create.add_argument("--source-commit", required=True)
    create.add_argument("--prepare-job-id", required=True)

    verify = subparsers.add_parser(
        "verify",
        help="recompute and cross-check every file and report identity",
    )
    verify.add_argument("--seal", type=Path, required=True)
    verify.add_argument("--source-commit")
    verify.add_argument("--prepare-job-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    standalone_values = (
        args.standalone_root,
        args.standalone_cli_sha256,
        args.standalone_module_sha256,
    )
    try:
        if any(value is not None for value in standalone_values):
            if not all(value is not None for value in standalone_values):
                raise BootstrapError(
                    "standalone root and both reviewed SHA-256 digests are required together"
                )
            sources = _standalone_sources(
                args.standalone_root,
                cli_sha256=args.standalone_cli_sha256,
                module_sha256=args.standalone_module_sha256,
            )
            module_source = sources[_MODULE_RELATIVE_PATH]
        else:
            module_source = _stable_regular_source(
                REPOSITORY_ROOT / _MODULE_RELATIVE_PATH,
                single_link=False,
            )
        corpus_seal = _load_corpus_seal(
            module_source,
            REPOSITORY_ROOT / _MODULE_RELATIVE_PATH,
        )
    except (BootstrapError, OSError) as exc:
        print(f"Peano v3 corpus seal failed: {exc}", file=sys.stderr)
        return 2

    try:
        if args.command == "create":
            manifest = corpus_seal.seal_corpus(
                args.artifact_dir,
                args.dataset_attestation,
                args.token_audit,
                args.runtime_smoke,
                args.destination,
                source_commit=args.source_commit,
                prepare_job_id=args.prepare_job_id,
            )
            location = args.destination
        else:
            manifest = corpus_seal.verify_seal(
                args.seal,
                source_commit=args.source_commit,
                prepare_job_id=args.prepare_job_id,
            )
            location = args.seal
    except (corpus_seal.CorpusSealError, FileExistsError, OSError) as exc:
        print(f"Peano v3 corpus seal failed: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "verified",
                "seal": str(location),
                "source_commit": manifest["source"]["git_commit"],
                "prepare_job_id": manifest["source"]["prepare_job_id"],
                "content_sha256": manifest["content_sha256"],
                "files": len(manifest["files"]),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
