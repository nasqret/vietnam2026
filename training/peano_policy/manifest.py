"""Cryptographic provenance manifest for a Peano policy adapter."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping


MANIFEST_VERSION = 1
ADAPTER_SUBDIR = "adapter"
TOKENIZER_SUBDIR = "tokenizer"
_UNSAFE_MODEL_SUFFIXES = {".bin", ".pkl", ".pickle", ".pt", ".pth"}


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def hash_files(root: Path, paths: Iterable[Path]) -> dict[str, Any]:
    """Hash selected files individually and as one path-bound collection."""

    entries: dict[str, str] = {}
    for path in sorted((candidate.resolve() for candidate in paths), key=str):
        relative = path.relative_to(root.resolve()).as_posix()
        entries[relative] = sha256_file(path)
    return {"sha256": sha256_json(entries), "files": entries}


def source_hash(source_root: Path) -> dict[str, Any]:
    paths = [
        path
        for path in source_root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name != "training-manifest.json"
    ]
    return hash_files(source_root, paths)


def artifact_hash(output_dir: Path, names: Iterable[str]) -> dict[str, Any]:
    paths = [output_dir / name for name in names if (output_dir / name).is_file()]
    if not paths:
        raise FileNotFoundError(f"none of the expected artifacts exist in {output_dir}")
    return hash_files(output_dir, paths)


def artifact_directory_hash(output_dir: Path, relative: str) -> dict[str, Any]:
    """Hash every regular loader-visible file in one closed artifact tree."""

    if (
        type(relative) is not str
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ValueError("artifact directory must be one safe relative path")
    directory = output_dir / relative
    if not directory.is_dir() or directory.is_symlink():
        raise FileNotFoundError(f"artifact directory does not exist: {directory}")
    entries = tuple(path for path in directory.rglob("*") if path.is_file())
    if not entries:
        raise FileNotFoundError(f"artifact directory is empty: {directory}")
    if any(path.is_symlink() for path in entries):
        raise ValueError(f"artifact directory contains a symlink: {directory}")
    result = hash_files(output_dir, entries)
    return {"root": Path(relative).as_posix(), **result}


def verify_hash_group(root: Path, expected: Mapping[str, Any]) -> None:
    """Reject a missing or mutated group before loading executable artifacts."""

    files = expected.get("files")
    aggregate = expected.get("sha256")
    if not isinstance(files, dict) or not isinstance(aggregate, str) or not files:
        raise ValueError("malformed artifact hash group")
    paths: list[Path] = []
    for relative, digest in files.items():
        if (
            not isinstance(relative, str)
            or not isinstance(digest, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise ValueError("unsafe artifact manifest entry")
        path = root / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"artifact hash mismatch: {relative}")
        paths.append(path)
    actual = hash_files(root, paths)
    if actual["sha256"] != aggregate:
        raise ValueError("artifact aggregate hash mismatch")


def verify_artifact_directory(
    root: Path,
    expected: Mapping[str, Any],
    relative: str,
) -> Path:
    """Require a manifest to cover the complete directory a loader will read."""

    if type(expected) is not dict or set(expected) != {"root", "sha256", "files"}:
        raise ValueError("malformed closed artifact-directory hash group")
    canonical = Path(relative).as_posix()
    if expected.get("root") != canonical:
        raise ValueError("artifact hash group names a different loader directory")
    directory = root / canonical
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError(f"artifact directory is missing or unsafe: {canonical}")
    actual_paths = tuple(path for path in directory.rglob("*") if path.is_file())
    if any(path.is_symlink() for path in actual_paths):
        raise ValueError(f"artifact directory contains a symlink: {canonical}")
    actual_names = {
        path.relative_to(root).as_posix()
        for path in actual_paths
    }
    files = expected.get("files")
    if type(files) is not dict or actual_names != set(files):
        raise ValueError(
            f"artifact manifest does not cover the complete {canonical} directory"
        )
    verify_hash_group(root, expected)
    return directory


def require_safetensors_adapter(
    expected: Mapping[str, Any],
    relative: str = ADAPTER_SUBDIR,
) -> None:
    """Reject PEFT's pickle fallback before any adapter loader is invoked."""

    files = expected.get("files")
    if type(files) is not dict:
        raise ValueError("malformed adapter artifact hash group")
    canonical = Path(relative).as_posix()
    required = f"{canonical}/adapter_model.safetensors"
    unsafe = sorted(
        name
        for name in files
        if type(name) is not str
        or Path(name).suffix.lower() in _UNSAFE_MODEL_SUFFIXES
    )
    safetensors = sorted(
        name
        for name in files
        if type(name) is str and Path(name).suffix.lower() == ".safetensors"
    )
    if unsafe or safetensors != [required]:
        detail = unsafe or safetensors
        raise ValueError(
            "adapter must contain exactly adapter_model.safetensors and no "
            f"pickle-compatible weights: {detail}"
        )


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    """Atomically write canonical, human-readable JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
