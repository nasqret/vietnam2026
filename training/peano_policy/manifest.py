"""Cryptographic provenance manifest for a Peano policy adapter."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any, Iterable, Mapping


MANIFEST_VERSION = 1
ADAPTER_SUBDIR = "adapter"
TOKENIZER_SUBDIR = "tokenizer"
_UNSAFE_MODEL_SUFFIXES = {".bin", ".pkl", ".pickle", ".pt", ".pth"}


class PublicationError(RuntimeError):
    """An immutable artifact could not be published safely."""


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
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


def _artifact_relative_directory(relative: str) -> str:
    if type(relative) is not str or not relative:
        raise ValueError("artifact directory must be one safe relative path")
    candidate = Path(relative)
    canonical = candidate.as_posix()
    if (
        candidate.is_absolute()
        or canonical in {"", "."}
        or ".." in candidate.parts
        or any(
            ord(character) < 32 or ord(character) == 127
            for character in relative
        )
    ):
        raise ValueError("artifact directory must be one safe relative path")
    return canonical


def _artifact_directory_path(output_dir: Path, canonical: str) -> Path:
    """Return one lexical, non-symlink artifact directory."""

    try:
        directory = _publication_path(
            Path(output_dir) / canonical,
            label="artifact directory",
        )
        try:
            metadata = os.lstat(directory)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"artifact directory does not exist: {directory}"
            ) from None
        except OSError as exc:
            raise ValueError(
                f"cannot inspect artifact directory {directory}: {exc}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(
                f"artifact directory must be one non-symlink directory: {directory}"
            )
        _reject_symlink_components(directory, label="artifact directory")
        _ordinary_directory(directory, label="artifact directory")
    except FileNotFoundError:
        raise
    except PublicationError as exc:
        raise ValueError(str(exc)) from exc
    return directory


_ARTIFACT_STABLE_STAT_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def _artifact_stat_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return tuple(
        int(getattr(metadata, field)) for field in _ARTIFACT_STABLE_STAT_FIELDS
    )


def _artifact_ordinary_directory(
    path: Path,
    *,
    device: int,
    require_protected: bool,
) -> os.stat_result:
    try:
        metadata = _ordinary_directory(path, label="artifact directory")
    except PublicationError as exc:
        raise ValueError(str(exc)) from exc
    if metadata.st_dev != device:
        raise ValueError(f"artifact directory crosses a filesystem boundary: {path}")
    if require_protected and stat.S_IMODE(metadata.st_mode) != 0o555:
        raise ValueError(f"artifact directory is not protected as 0555: {path}")
    return metadata


def _artifact_regular_file(
    path: Path,
    *,
    device: int,
    require_protected: bool,
) -> os.stat_result:
    try:
        metadata = _regular_publication_file(
            path,
            label="artifact payload",
            expected_device=device,
        )
    except PublicationError as exc:
        raise ValueError(str(exc)) from exc
    if require_protected and stat.S_IMODE(metadata.st_mode) != 0o444:
        raise ValueError(f"artifact payload is not protected as 0444: {path}")
    return metadata


def _artifact_tree_inventory(
    directory: Path,
    *,
    canonical: str,
    require_protected: bool,
) -> tuple[
    dict[str, tuple[int, ...]],
    dict[str, tuple[Path, os.stat_result]],
]:
    """Enumerate every node, rejecting aliases and non-regular payloads."""

    try:
        root_metadata = _ordinary_directory(directory, label="artifact directory")
    except PublicationError as exc:
        raise ValueError(str(exc)) from exc
    device = root_metadata.st_dev
    inventory: dict[str, tuple[int, ...]] = {}
    files: dict[str, tuple[Path, os.stat_result]] = {}
    seen_files: set[tuple[int, int]] = set()

    def walk_error(error: OSError) -> None:
        raise ValueError(f"cannot enumerate artifact directory: {error}")

    for current, child_directories, payload_names in os.walk(
        directory,
        topdown=True,
        followlinks=False,
        onerror=walk_error,
    ):
        current_path = Path(current)
        current_metadata = _artifact_ordinary_directory(
            current_path,
            device=device,
            require_protected=require_protected,
        )
        current_relative = current_path.relative_to(directory)
        directory_name = (
            canonical
            if current_relative == Path(".")
            else (Path(canonical) / current_relative).as_posix()
        )
        inventory[f"directory:{directory_name}"] = _artifact_stat_identity(
            current_metadata
        )

        # os.walk deliberately puts symlinks to directories in this list even
        # when followlinks=False.  Inspect them before os.walk can recurse.
        for name in child_directories:
            child = current_path / name
            child_metadata = _artifact_ordinary_directory(
                child,
                device=device,
                require_protected=require_protected,
            )
            child_name = (
                Path(canonical) / child.relative_to(directory)
            ).as_posix()
            inventory[f"directory:{child_name}"] = _artifact_stat_identity(
                child_metadata
            )

        # os.walk puts symlinks-to-files, FIFOs, sockets, and devices here.
        # Requiring an ordinary file before opening keeps those nodes inert.
        for name in payload_names:
            path = current_path / name
            metadata = _artifact_regular_file(
                path,
                device=device,
                require_protected=require_protected,
            )
            inode = (metadata.st_dev, metadata.st_ino)
            if inode in seen_files:
                raise ValueError(
                    f"artifact directory contains hard-linked aliases: {path}"
                )
            seen_files.add(inode)
            relative_name = (
                Path(canonical) / path.relative_to(directory)
            ).as_posix()
            inventory[f"file:{relative_name}"] = _artifact_stat_identity(metadata)
            files[relative_name] = (path, metadata)
    return inventory, files


def _stable_artifact_file_sha256(
    path: Path,
    *,
    before: os.stat_result,
    device: int,
    require_protected: bool,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Hash one descriptor-bound regular file and reject a changing read."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"cannot open artifact payload {path}: {exc}") from exc
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_dev != device
            or _artifact_stat_identity(opened) != _artifact_stat_identity(before)
            or (require_protected and stat.S_IMODE(opened.st_mode) != 0o444)
        ):
            raise ValueError(f"artifact payload changed while opened: {path}")
        while chunk := os.read(descriptor, chunk_size):
            digest.update(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise ValueError(f"cannot read artifact payload {path}: {exc}") from exc
    finally:
        os.close(descriptor)
    current = _artifact_regular_file(
        path,
        device=device,
        require_protected=require_protected,
    )
    expected_identity = _artifact_stat_identity(before)
    if (
        _artifact_stat_identity(opened) != expected_identity
        or _artifact_stat_identity(after) != expected_identity
        or _artifact_stat_identity(current) != expected_identity
    ):
        raise ValueError(f"artifact payload changed while hashed: {path}")
    return digest.hexdigest()


def artifact_directory_hash(
    output_dir: Path,
    relative: str,
    *,
    require_protected: bool = False,
) -> dict[str, Any]:
    """Hash one complete, stable, regular-file-only artifact tree.

    ``require_protected`` is intentionally opt-in so historical v1/v2
    adapters remain loadable.  Model-v3 finalization and admission can require
    exact 0555 directory and 0444 payload modes.
    """

    if type(require_protected) is not bool:
        raise TypeError("require_protected must be a bool")
    canonical = _artifact_relative_directory(relative)
    directory = _artifact_directory_path(Path(output_dir), canonical)
    before_inventory, before_files = _artifact_tree_inventory(
        directory,
        canonical=canonical,
        require_protected=require_protected,
    )
    if not before_files:
        raise FileNotFoundError(f"artifact directory is empty: {directory}")
    device = os.lstat(directory).st_dev
    entries = {
        relative_name: _stable_artifact_file_sha256(
            path,
            before=metadata,
            device=device,
            require_protected=require_protected,
        )
        for relative_name, (path, metadata) in sorted(before_files.items())
    }
    after_inventory, after_files = _artifact_tree_inventory(
        directory,
        canonical=canonical,
        require_protected=require_protected,
    )
    if (
        after_inventory != before_inventory
        or set(after_files) != set(before_files)
    ):
        raise ValueError(f"artifact directory changed while hashed: {directory}")
    return {"root": canonical, "sha256": sha256_json(entries), "files": entries}


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
    *,
    require_protected: bool = False,
) -> Path:
    """Require a manifest to cover the complete stable tree a loader will read."""

    if type(expected) is not dict or set(expected) != {"root", "sha256", "files"}:
        raise ValueError("malformed closed artifact-directory hash group")
    if type(require_protected) is not bool:
        raise TypeError("require_protected must be a bool")
    canonical = _artifact_relative_directory(relative)
    if expected.get("root") != canonical:
        raise ValueError("artifact hash group names a different loader directory")
    files = expected.get("files")
    aggregate = expected.get("sha256")
    if (
        type(files) is not dict
        or not files
        or type(aggregate) is not str
        or len(aggregate) != 64
        or any(character not in "0123456789abcdef" for character in aggregate)
    ):
        raise ValueError("malformed closed artifact-directory hash group")
    canonical_path = Path(canonical)
    for name, digest in files.items():
        if (
            type(name) is not str
            or type(digest) is not str
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("unsafe artifact manifest entry")
        candidate = Path(name)
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.as_posix() != name
        ):
            raise ValueError("unsafe artifact manifest entry")
        try:
            candidate.relative_to(canonical_path)
        except ValueError:
            raise ValueError(
                "artifact manifest entry escapes its loader directory"
            ) from None
    try:
        actual = artifact_directory_hash(
            root,
            canonical,
            require_protected=require_protected,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            f"artifact directory is missing or unsafe: {canonical}"
        ) from exc
    actual_names = set(actual["files"])
    if actual_names != set(files):
        raise ValueError(
            f"artifact manifest does not cover the complete {canonical} directory"
        )
    for name, digest in files.items():
        if actual["files"][name] != digest:
            raise ValueError(f"artifact hash mismatch: {name}")
    if actual["sha256"] != aggregate:
        raise ValueError("artifact aggregate hash mismatch")
    return _artifact_directory_path(Path(root), canonical)


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
    payload = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
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


def _publication_path(path: Path, *, label: str) -> Path:
    """Return an absolute lexical path without following a symlink."""

    try:
        raw = os.fspath(path)
    except TypeError as exc:
        raise PublicationError(f"{label} is not one filesystem path") from exc
    if (
        type(raw) is not str
        or not raw
        or any(ord(character) < 32 or ord(character) == 127 for character in raw)
    ):
        raise PublicationError(f"{label} contains empty or control text")
    lexical = Path(raw)
    if ".." in lexical.parts:
        raise PublicationError(f"{label} may not contain parent traversal")
    if not lexical.is_absolute():
        lexical = Path.cwd() / lexical
    if lexical.name in {"", ".", ".."}:
        raise PublicationError(f"{label} needs one safe final component")
    return lexical


def _reject_symlink_components(path: Path, *, label: str) -> None:
    """Require every existing component, including ``path``, to be non-symlink."""

    if not path.is_absolute():  # pragma: no cover - internal invariant
        raise AssertionError("publication component walk requires an absolute path")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            metadata = os.lstat(current)
        except OSError as exc:
            raise PublicationError(
                f"cannot inspect {label} component {current}: {exc}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise PublicationError(
                f"{label} may not contain a symlink component: {current}"
            )


def _ordinary_directory(path: Path, *, label: str) -> os.stat_result:
    try:
        metadata = os.lstat(path)
    except OSError as exc:
        raise PublicationError(f"cannot inspect {label} {path}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise PublicationError(f"{label} must be one non-symlink directory: {path}")
    return metadata


def _require_absent_publication(path: Path, *, label: str) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PublicationError(f"cannot inspect {label} {path}: {exc}") from exc
    raise FileExistsError(f"refusing to replace existing {label}: {path}")


def _fsync_publication_directory(path: Path) -> None:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PublicationError(f"cannot open publication directory {path}: {exc}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise PublicationError(
                f"publication directory changed type while opened: {path}"
            )
        os.fsync(descriptor)
    except OSError as exc:
        raise PublicationError(f"cannot flush publication directory {path}: {exc}") from exc
    finally:
        os.close(descriptor)


def _atomic_rename_noreplace(source: Path, destination: Path) -> None:
    """Rename one path atomically with the recovery-tested no-replace flags.

    This is the same minimal OS boundary used by adapter recovery:
    ``renamex_np(RENAME_EXCL)`` on macOS and
    ``renameat2(RENAME_NOREPLACE)`` on Linux.  It deliberately has no fallback
    to a check-then-rename sequence.
    """

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        try:
            rename = libc.renamex_np
        except AttributeError as exc:  # pragma: no cover - unsupported old macOS
            raise PublicationError(
                "atomic no-replace publication is unavailable"
            ) from exc
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        try:
            rename = libc.renameat2
        except AttributeError as exc:  # pragma: no cover - unsupported old libc
            raise PublicationError(
                "atomic no-replace publication is unavailable"
            ) from exc
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 1)
    else:  # pragma: no cover - production and development hosts are Linux/macOS
        raise PublicationError(
            "atomic no-replace publication is unsupported on this OS"
        )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(
            f"refusing to replace existing publication destination: {destination}"
        )
    raise OSError(error, os.strerror(error), str(destination))


def _regular_publication_file(
    path: Path,
    *,
    label: str,
    expected_device: int | None = None,
) -> os.stat_result:
    try:
        metadata = os.lstat(path)
    except OSError as exc:
        raise PublicationError(f"cannot inspect {label} {path}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise PublicationError(f"{label} must be one non-symlink regular file: {path}")
    if metadata.st_nlink != 1:
        raise PublicationError(f"{label} may not be hard-linked: {path}")
    if expected_device is not None and metadata.st_dev != expected_device:
        raise PublicationError(f"{label} crosses a filesystem boundary: {path}")
    return metadata


def _fsync_publication_tree(root: Path, *, device: int) -> None:
    """Flush a closed regular-file tree and reject unsafe payload nodes."""

    directories: list[Path] = [root]
    seen_files: set[tuple[int, int]] = set()

    def walk_error(error: OSError) -> None:
        raise PublicationError(f"cannot enumerate publication staging tree: {error}")

    for current, child_directories, files in os.walk(
        root, topdown=True, followlinks=False, onerror=walk_error
    ):
        current_path = Path(current)
        for name in child_directories:
            directory = current_path / name
            metadata = _ordinary_directory(directory, label="staging child")
            if metadata.st_dev != device:
                raise PublicationError(
                    f"staging child crosses a filesystem boundary: {directory}"
                )
            directories.append(directory)
        for name in files:
            path = current_path / name
            before = _regular_publication_file(
                path, label="staging payload", expected_device=device
            )
            inode = (before.st_dev, before.st_ino)
            if inode in seen_files:
                raise PublicationError(
                    f"staging tree contains hard-linked aliases: {path}"
                )
            seen_files.add(inode)
            flags = (
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                descriptor = os.open(path, flags)
            except OSError as exc:
                raise PublicationError(
                    f"cannot open staging payload {path}: {exc}"
                ) from exc
            try:
                opened = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or (opened.st_dev, opened.st_ino) != inode
                ):
                    raise PublicationError(
                        f"staging payload changed while opened: {path}"
                    )
                os.fsync(descriptor)
                after = os.fstat(descriptor)
            except OSError as exc:
                raise PublicationError(
                    f"cannot flush staging payload {path}: {exc}"
                ) from exc
            finally:
                os.close(descriptor)
            current_metadata = _regular_publication_file(
                path, label="staging payload", expected_device=device
            )
            stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            if any(
                getattr(before, field) != getattr(after, field)
                or getattr(before, field) != getattr(current_metadata, field)
                for field in stable_fields
            ):
                raise PublicationError(f"staging payload changed while flushed: {path}")
    for directory in reversed(directories):
        _fsync_publication_directory(directory)


def _protect_publication_tree(root: Path, *, device: int) -> None:
    """Make every payload read-only before its name can become authoritative."""

    def walk_error(error: OSError) -> None:
        raise PublicationError(f"cannot enumerate publication staging tree: {error}")

    for current, child_directories, files in os.walk(
        root, topdown=False, followlinks=False, onerror=walk_error
    ):
        current_path = Path(current)
        for name in files:
            path = current_path / name
            _regular_publication_file(
                path, label="staging payload", expected_device=device
            )
            try:
                os.chmod(path, 0o444, follow_symlinks=False)
            except OSError as exc:
                raise PublicationError(
                    f"cannot protect staging payload {path}: {exc}"
                ) from exc
        for name in child_directories:
            path = current_path / name
            metadata = _ordinary_directory(path, label="staging child")
            if metadata.st_dev != device:
                raise PublicationError(
                    f"staging child crosses a filesystem boundary: {path}"
                )
            try:
                os.chmod(path, 0o555, follow_symlinks=False)
            except OSError as exc:
                raise PublicationError(
                    f"cannot protect staging directory {path}: {exc}"
                ) from exc
    try:
        os.chmod(root, 0o555, follow_symlinks=False)
    except OSError as exc:
        raise PublicationError(f"cannot protect staging root {root}: {exc}") from exc


def _protected_publication_inventory(
    root: Path, *, device: int
) -> dict[str, tuple[object, ...]]:
    """Verify exact protected modes and capture inode-bound tree identity."""

    inventory: dict[str, tuple[object, ...]] = {}
    seen_files: set[tuple[int, int]] = set()

    def walk_error(error: OSError) -> None:
        raise PublicationError(f"cannot enumerate protected publication tree: {error}")

    for current, child_directories, files in os.walk(
        root, topdown=True, followlinks=False, onerror=walk_error
    ):
        current_path = Path(current)
        current_metadata = _ordinary_directory(
            current_path, label="protected staging directory"
        )
        if (
            current_metadata.st_dev != device
            or stat.S_IMODE(current_metadata.st_mode) != 0o555
        ):
            raise PublicationError(
                f"staging directory is not protected as 0555: {current_path}"
            )
        relative = current_path.relative_to(root).as_posix() or "."
        inventory[relative] = (
            "directory",
            current_metadata.st_dev,
            current_metadata.st_ino,
            stat.S_IMODE(current_metadata.st_mode),
        )
        for name in child_directories:
            child = current_path / name
            child_metadata = _ordinary_directory(child, label="protected staging child")
            if child_metadata.st_dev != device:
                raise PublicationError(
                    f"protected staging child crosses a filesystem boundary: {child}"
                )
        for name in files:
            path = current_path / name
            metadata = _regular_publication_file(
                path, label="protected staging payload", expected_device=device
            )
            if stat.S_IMODE(metadata.st_mode) != 0o444:
                raise PublicationError(
                    f"staging payload is not protected as 0444: {path}"
                )
            inode = (metadata.st_dev, metadata.st_ino)
            if inode in seen_files:
                raise PublicationError(
                    f"protected staging tree contains hard-linked aliases: {path}"
                )
            seen_files.add(inode)
            relative = path.relative_to(root).as_posix()
            inventory[relative] = (
                "file",
                metadata.st_dev,
                metadata.st_ino,
                stat.S_IMODE(metadata.st_mode),
                metadata.st_size,
                metadata.st_mtime_ns,
            )
    return inventory


def _restore_failed_darwin_staging_root(
    source: Path,
    *,
    expected_device: int,
    expected_inode: int,
) -> None:
    """Undo the narrow macOS rename compatibility mode after a failed call."""

    try:
        metadata = os.lstat(source)
    except OSError:
        return
    if (
        not stat.S_ISLNK(metadata.st_mode)
        and stat.S_ISDIR(metadata.st_mode)
        and (metadata.st_dev, metadata.st_ino) == (expected_device, expected_inode)
    ):
        os.chmod(source, 0o555, follow_symlinks=False)
        _fsync_publication_directory(source)
        _fsync_publication_directory(source.parent)


def write_manifest_noreplace(
    path: Path, manifest: Mapping[str, Any]
) -> Path:
    """Atomically publish one canonical manifest, never replacing authority.

    The parent must already be an ordinary, non-symlink directory.  Canonical
    bytes are first written and flushed under a recognizable hidden partial
    name, then installed with an OS-level no-replace rename, and finally the
    parent directory is flushed.  A failed publication can therefore leave a
    partial file, but never a partially written file at ``path``.
    """

    destination = _publication_path(path, label="manifest destination")
    parent = destination.parent
    _reject_symlink_components(parent, label="manifest destination parent")
    parent_metadata = _ordinary_directory(
        parent, label="manifest destination parent"
    )
    _require_absent_publication(destination, label="manifest")
    try:
        payload = (
            json.dumps(
                manifest,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PublicationError(f"manifest is not strict JSON: {exc}") from None

    descriptor, temporary_name = tempfile.mkstemp(
        dir=parent,
        prefix=f".{destination.name}.partial-",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_metadata = _regular_publication_file(
            temporary,
            label="partial manifest",
            expected_device=parent_metadata.st_dev,
        )
        try:
            os.chmod(temporary, 0o444, follow_symlinks=False)
        except OSError as exc:
            raise PublicationError(
                f"cannot protect partial manifest {temporary}: {exc}"
            ) from exc
        protected_partial = _regular_publication_file(
            temporary,
            label="protected partial manifest",
            expected_device=parent_metadata.st_dev,
        )
        if (
            (protected_partial.st_dev, protected_partial.st_ino)
            != (temporary_metadata.st_dev, temporary_metadata.st_ino)
            or protected_partial.st_size != len(payload)
            or stat.S_IMODE(protected_partial.st_mode) != 0o444
        ):
            raise PublicationError(
                "partial manifest changed or did not acquire protected mode"
            )
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            protected_descriptor = os.open(temporary, flags)
        except OSError as exc:
            raise PublicationError(
                f"cannot open protected partial manifest {temporary}: {exc}"
            ) from exc
        try:
            opened_partial = os.fstat(protected_descriptor)
            if (
                not stat.S_ISREG(opened_partial.st_mode)
                or opened_partial.st_nlink != 1
                or (opened_partial.st_dev, opened_partial.st_ino)
                != (protected_partial.st_dev, protected_partial.st_ino)
                or opened_partial.st_size != len(payload)
                or stat.S_IMODE(opened_partial.st_mode) != 0o444
            ):
                raise PublicationError(
                    "protected partial manifest changed while opened"
                )
            os.fsync(protected_descriptor)
            after_flush = os.fstat(protected_descriptor)
        except OSError as exc:
            raise PublicationError(
                f"cannot flush protected partial manifest {temporary}: {exc}"
            ) from exc
        finally:
            os.close(protected_descriptor)
        if (
            (after_flush.st_dev, after_flush.st_ino)
            != (protected_partial.st_dev, protected_partial.st_ino)
            or after_flush.st_nlink != 1
            or after_flush.st_size != len(payload)
            or stat.S_IMODE(after_flush.st_mode) != 0o444
        ):
            raise PublicationError(
                "protected partial manifest changed while flushed"
            )
        _fsync_publication_directory(parent)
        _require_absent_publication(destination, label="manifest")
        # An exception intentionally leaves this recognizable partial in place.
        _atomic_rename_noreplace(temporary, destination)
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    try:
        os.lstat(temporary)
    except FileNotFoundError:
        pass
    else:
        raise PublicationError("partial manifest still exists after publication")
    published = _regular_publication_file(
        destination,
        label="published manifest",
        expected_device=parent_metadata.st_dev,
    )
    if (
        (published.st_dev, published.st_ino)
        != (protected_partial.st_dev, protected_partial.st_ino)
        or published.st_size != len(payload)
        or stat.S_IMODE(published.st_mode) != 0o444
    ):
        raise PublicationError(
            "published manifest differs from its protected flushed partial"
        )
    current_parent = _ordinary_directory(parent, label="manifest destination parent")
    if (current_parent.st_dev, current_parent.st_ino) != (
        parent_metadata.st_dev,
        parent_metadata.st_ino,
    ):
        raise PublicationError("manifest destination parent changed during publication")
    _fsync_publication_directory(parent)
    return destination


def publish_staged_directory_noreplace(
    staging: Path, destination: Path
) -> Path:
    """Durably install one recognizable sibling staging directory exactly once.

    ``staging`` must be named ``.<destination>.partial-<nonempty>``.  The
    complete regular-file tree is flushed before a single OS-level no-replace
    rename makes it visible at ``destination``.  Validation and syscall
    failures intentionally retain the partial tree under its non-authoritative
    name; this function never cleans or replaces either pathname.
    """

    source = _publication_path(staging, label="publication staging directory")
    target = _publication_path(destination, label="publication destination")
    if source.parent != target.parent:
        raise PublicationError(
            "publication staging and destination must be lexical siblings"
        )
    expected_prefix = f".{target.name}.partial-"
    if not source.name.startswith(expected_prefix) or source.name == expected_prefix:
        raise PublicationError(
            f"publication staging name must begin {expected_prefix!r}"
        )

    parent = target.parent
    _reject_symlink_components(parent, label="publication parent")
    parent_metadata = _ordinary_directory(parent, label="publication parent")
    source_metadata = _ordinary_directory(source, label="publication staging")
    if source_metadata.st_dev != parent_metadata.st_dev:
        raise PublicationError(
            "publication staging and destination parent cross a filesystem boundary"
        )
    _require_absent_publication(target, label="publication destination")
    _fsync_publication_tree(source, device=parent_metadata.st_dev)
    _protect_publication_tree(source, device=parent_metadata.st_dev)
    _fsync_publication_tree(source, device=parent_metadata.st_dev)
    protected_before = _protected_publication_inventory(
        source, device=parent_metadata.st_dev
    )
    _fsync_publication_directory(parent)

    stable_source = _ordinary_directory(source, label="publication staging")
    stable_parent = _ordinary_directory(parent, label="publication parent")
    if (stable_source.st_dev, stable_source.st_ino) != (
        source_metadata.st_dev,
        source_metadata.st_ino,
    ):
        raise PublicationError("publication staging changed before installation")
    if (stable_parent.st_dev, stable_parent.st_ino) != (
        parent_metadata.st_dev,
        parent_metadata.st_ino,
    ):
        raise PublicationError("publication parent changed before installation")
    if (
        _protected_publication_inventory(source, device=parent_metadata.st_dev)
        != protected_before
    ):
        raise PublicationError("protected staging tree changed before installation")
    _require_absent_publication(target, label="publication destination")

    # macOS rejects renamex_np(RENAME_EXCL) on a 0555 source directory.  Match
    # recovery's audited compatibility path: only the root is briefly 0700;
    # every payload and child directory remains protected throughout.
    darwin_root_compatibility = sys.platform == "darwin"
    if darwin_root_compatibility:
        os.chmod(source, 0o700, follow_symlinks=False)
        _fsync_publication_directory(source)
    try:
        _atomic_rename_noreplace(source, target)
    except BaseException as exc:
        if darwin_root_compatibility:
            _restore_failed_darwin_staging_root(
                source,
                expected_device=source_metadata.st_dev,
                expected_inode=source_metadata.st_ino,
            )
        try:
            protected_after_failure = _protected_publication_inventory(
                source, device=parent_metadata.st_dev
            )
        except PublicationError as protection_error:
            raise PublicationError(
                "staging protection changed during failed publication"
            ) from protection_error
        if protected_after_failure != protected_before:
            raise PublicationError(
                "staging identity changed during failed publication"
            ) from exc
        raise
    if darwin_root_compatibility:
        os.chmod(target, 0o555, follow_symlinks=False)

    try:
        os.lstat(source)
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise PublicationError(
            f"cannot verify disappearance of publication staging: {exc}"
        ) from exc
    else:
        raise PublicationError("publication staging still exists after installation")
    published = _ordinary_directory(target, label="publication destination")
    if (published.st_dev, published.st_ino) != (
        source_metadata.st_dev,
        source_metadata.st_ino,
    ):
        raise PublicationError(
            "publication destination differs from the flushed staging directory"
        )
    protected_after = _protected_publication_inventory(
        target, device=parent_metadata.st_dev
    )
    if protected_after != protected_before:
        raise PublicationError(
            "published tree differs from its protected staging identity"
        )
    final_parent = _ordinary_directory(parent, label="publication parent")
    if (final_parent.st_dev, final_parent.st_ino) != (
        parent_metadata.st_dev,
        parent_metadata.st_ino,
    ):
        raise PublicationError("publication parent changed during installation")
    _fsync_publication_directory(target)
    _fsync_publication_directory(parent)
    return target
