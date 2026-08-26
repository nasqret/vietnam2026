"""Bind review source receipts to a complete, immutable Git source inventory.

The receipt's SHA256 is an integrity check, not an authentication mechanism.
Execution also requires its exact historical source inventory and Git blob
identities to agree with bounded, nonsymlink working files. A later HEAD (and
later unrelated Python files) is allowed when verifying an older archive.

Draft identities may be dirty. This module never grants a human review, a
signature, a clean benchmark, or permission to run a model.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import stat
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
# Repository-relative, so tests can select an isolated repository using ROOT.
SCRIPT = Path("scripts/check_peano_hydra_review.py")
MODULE_DIRECTORIES = (
    "training/peano_hydra", "training/peano_policy", "peano-lab/py/peano_lab",
)
SCRIPTS = (SCRIPT.as_posix(), "scripts/hydra_bounded_exec.py")
REQUIRED_FILES = frozenset(SCRIPTS) | frozenset(
    f"training/peano_hydra/{name}.py" for name in (
        "review", "review_sources", "reference", "review_runtime", "conformance",
        "lineage_review", "cold_replay", "protocol", "epoch", "frontier",
    )
) | frozenset(
    f"peano-lab/py/peano_lab/kernel/{name}.py" for name in (
        "__init__", "checker", "formulas", "terms", "subst", "proofs",
    )
) | frozenset({
    "training/peano_hydra/__init__.py", "training/peano_policy/__init__.py",
    "peano-lab/py/peano_lab/__init__.py", "peano-lab/py/peano_lab/batch.py",
})

MAX_SOURCE_FILES = 2048
MAX_SOURCE_BYTES = 8 * 1024**2
MAX_TOTAL_SOURCE_BYTES = 64 * 1024**2
MAX_INVENTORY_BYTES = 2 * 1024**2
MAX_STATUS_BYTES = 4 * 1024**2
MAX_DIRECTORY_ENTRIES = 32768
MAX_PATH_BYTES = 1024
GIT_TIMEOUT_SECONDS = 10
_OID = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ReviewSourceError(ValueError):
    """Missing, dirty, unsafe, or unauthenticated review source evidence."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _path(relative: object) -> str:
    if type(relative) is not str:
        raise ReviewSourceError("source path must be a canonical relative POSIX string")
    try:
        length = len(relative.encode("utf-8"))
    except UnicodeError as exc:
        raise ReviewSourceError("source path is not valid UTF-8") from exc
    parts = relative.split("/")
    if (not 1 <= length <= MAX_PATH_BYTES or len(parts) > 64
        or any(part in {"", ".", ".."} for part in parts)
        or "\\" in relative or any(ord(char) < 32 or ord(char) == 127 for char in relative)
        or PurePosixPath(relative).is_absolute() or PurePosixPath(relative).as_posix() != relative):
        raise ReviewSourceError("source path must be a canonical relative POSIX string")
    return relative


def _in_scope(relative: str) -> bool:
    return relative in SCRIPTS or any(
        relative.startswith(directory + "/") for directory in MODULE_DIRECTORIES
    )


def bounded_git(project: Path, *arguments: str, maximum: int) -> bytes:
    """Read bounded Git output from one explicit project, without lazy fetches.

    Source and reference provenance share this environment/replace-ref policy;
    callers do not redirect the module's ROOT or inherit Git repository flags.
    """
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1", "LC_ALL": "C",
    })
    command = [
        "git", "--no-replace-objects", "--no-optional-locks", "-C", str(project),
        "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", *arguments,
    ]
    process = None
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=environment,
        )
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ReviewSourceError("source Git inspection exceeded its time bound")
            for key, _ in selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffer = buffers[key.data]
                limit = maximum if key.data == "stdout" else 16384
                if len(buffer) + len(chunk) > limit:
                    raise ReviewSourceError("source Git inspection exceeded its output bound")
                buffer.extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0 or process.wait(timeout=remaining) != 0:
            raise ReviewSourceError("recorded source commit or Git repository is unavailable")
        return bytes(buffers["stdout"])
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReviewSourceError("bounded source Git inspection failed") from exc
    finally:
        selector.close()
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()


def _git(*arguments: str, maximum: int) -> bytes:
    return bounded_git(ROOT, *arguments, maximum=maximum)


def _historical_inventory(commit: str) -> dict[str, tuple[str, str]]:
    if _git("cat-file", "-t", commit, maximum=32) != b"commit\n":
        raise ReviewSourceError("recorded source identity is not a real Git commit")
    raw = _git(
        "ls-tree", "-r", "-z", commit, "--", *MODULE_DIRECTORIES, *SCRIPTS,
        maximum=MAX_INVENTORY_BYTES,
    )
    if raw and not raw.endswith(b"\0"):
        raise ReviewSourceError("historical Git inventory is incomplete")
    inventory: dict[str, tuple[str, str]] = {}
    entries = raw[:-1].split(b"\0") if raw else []
    if len(entries) > MAX_DIRECTORY_ENTRIES:
        raise ReviewSourceError("historical Git inventory exceeds its entry bound")
    for entry in entries:
        try:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, object_id = metadata.decode("ascii").split(" ")
            relative = _path(name.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ReviewSourceError("historical Git source entry is malformed") from exc
        if (mode not in {"100644", "100755"} or kind != "blob"
            or _OID.fullmatch(object_id) is None):
            raise ReviewSourceError("historical source inventory contains a symlink or nonregular entry")
        if not _in_scope(relative):
            raise ReviewSourceError("historical source inventory escapes the reviewed implementation")
        if not relative.endswith(".py"):
            continue
        if relative in inventory:
            raise ReviewSourceError("historical source inventory repeats a path")
        inventory[relative] = (mode, object_id)
        if len(inventory) > MAX_SOURCE_FILES:
            raise ReviewSourceError("historical source inventory exceeds its file bound")
    return inventory


def _open_directory(relative: str | None = None) -> int:
    """Traverse every in-repository parent with O_NOFOLLOW, including ROOT."""
    descriptor = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in (() if relative is None else _path(relative).split("/")):
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_source(relative: str) -> int:
    parts = _path(relative).split("/")
    parent = _open_directory("/".join(parts[:-1]) if len(parts) > 1 else None)
    try:
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)


def _fingerprint(relative: str) -> tuple[dict[str, object], str, str]:
    descriptor = None
    try:
        descriptor = _open_source(relative)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= MAX_SOURCE_BYTES:
            raise ReviewSourceError(f"review source must be a bounded regular file: {relative}")
        sha256 = hashlib.sha256()
        # Git commits bind blob IDs, not SHA256 receipt descriptions. Comparing
        # this hash to ls-tree authenticates the same bytes without one Git
        # subprocess (or an unbounded blob read) per source file.
        git_blob = hashlib.sha1(b"blob " + str(before.st_size).encode("ascii") + b"\0")
        length = 0
        while chunk := os.read(descriptor, 65536):
            length += len(chunk)
            if length > MAX_SOURCE_BYTES:
                raise ReviewSourceError(f"review source exceeded its byte bound: {relative}")
            sha256.update(chunk)
            git_blob.update(chunk)
        after = os.fstat(descriptor)
        fresh = _open_source(relative)
        try:
            current = os.fstat(fresh)
        finally:
            os.close(fresh)
        attributes = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
        if (length != before.st_size
            or any(getattr(before, field) != getattr(after, field)
                   or getattr(before, field) != getattr(current, field) for field in attributes)):
            raise ReviewSourceError(f"review source changed while being inspected: {relative}")
        mode = "100755" if before.st_mode & 0o111 else "100644"
        return {"bytes": length, "sha256": sha256.hexdigest()}, mode, git_blob.hexdigest()
    except OSError as exc:
        raise ReviewSourceError(f"review source is missing or uses a symlink: {relative}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _current_inventory() -> set[str]:
    paths = set(SCRIPTS)
    pending = list(MODULE_DIRECTORIES)
    examined = 0
    try:
        while pending:
            directory = pending.pop()
            descriptor = _open_directory(directory)
            try:
                with os.scandir(descriptor) as entries:
                    for entry in entries:
                        examined += 1
                        if examined > MAX_DIRECTORY_ENTRIES:
                            raise ReviewSourceError("current source inventory exceeds its entry bound")
                        relative = _path(directory + "/" + entry.name)
                        if entry.is_symlink():
                            raise ReviewSourceError(f"current source inventory contains a symlink: {relative}")
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(relative)
                        elif relative.endswith(".py"):
                            if not entry.is_file(follow_symlinks=False):
                                raise ReviewSourceError(f"current source is not a regular file: {relative}")
                            paths.add(relative)
                            if len(paths) > MAX_SOURCE_FILES:
                                raise ReviewSourceError("current source inventory exceeds its file bound")
            finally:
                os.close(descriptor)
    except OSError as exc:
        raise ReviewSourceError("current source directories are missing or use symlinks") from exc
    if not REQUIRED_FILES <= paths:
        raise ReviewSourceError("source identity omits required review or kernel implementation")
    return paths


def source_identity() -> dict[str, object]:
    """Describe a possibly dirty draft; only committed identities can execute."""
    commit = _git("rev-parse", "--verify", "HEAD", maximum=80).decode("ascii").strip()
    if _OID.fullmatch(commit) is None:
        raise ReviewSourceError("review source identity requires a full SHA1 Git commit")
    historical = _historical_inventory(commit)
    paths = _current_inventory()
    files = {}
    fingerprints = {}
    total = 0
    for relative in sorted(paths):
        description, mode, blob = _fingerprint(relative)
        total += description["bytes"]
        if total > MAX_TOTAL_SOURCE_BYTES:
            raise ReviewSourceError("review source inventory exceeds its total byte bound")
        files[relative] = description
        fingerprints[relative] = (mode, blob)
    dirty = bool(_git("status", "--porcelain=v1", "-z", "--untracked-files=all", maximum=MAX_STATUS_BYTES))
    # Includes ignored/untracked .py and assume-unchanged source modifications
    # that a porcelain status alone can fail to disclose.
    dirty = dirty or fingerprints != historical
    return {"git_commit": commit, "git_dirty": dirty, "files": files,
            "files_sha256": _digest(files)}


def _validated_files(record: dict[str, object]) -> dict[str, object]:
    """Validate the bounded receipt schema without invoking Git or a child."""
    if (type(record) is not dict
        or set(record) != {"git_commit", "git_dirty", "files", "files_sha256"}
        or type(record["git_commit"]) is not str or _OID.fullmatch(record["git_commit"]) is None
        or record["git_dirty"] is not False or type(record["files"]) is not dict
        or not 1 <= len(record["files"]) <= MAX_SOURCE_FILES
        or type(record["files_sha256"]) is not str or _SHA256.fullmatch(record["files_sha256"]) is None):
        raise ReviewSourceError("review source identity must be a well-formed, clean committed record")
    files = record["files"]
    total = 0
    for relative, descriptor in files.items():
        relative = _path(relative)
        if not relative.endswith(".py") or not _in_scope(relative):
            raise ReviewSourceError("source identity escapes the reviewed implementation")
        if (type(descriptor) is not dict or set(descriptor) != {"bytes", "sha256"}
            or type(descriptor["bytes"]) is not int or not 0 <= descriptor["bytes"] <= MAX_SOURCE_BYTES
            or type(descriptor["sha256"]) is not str or _SHA256.fullmatch(descriptor["sha256"]) is None):
            raise ReviewSourceError("source descriptor is malformed or exceeds its byte bound")
        total += descriptor["bytes"]
        if total > MAX_TOTAL_SOURCE_BYTES:
            raise ReviewSourceError("review source inventory exceeds its total byte bound")
    if _digest(files) != record["files_sha256"]:
        raise ReviewSourceError("review source inventory digest differs")
    if not REQUIRED_FILES <= files.keys():
        raise ReviewSourceError("source identity omits required review or kernel implementation")
    return files


def check_recorded_source_bytes(record: dict[str, object]) -> None:
    """Check parent-authenticated source bytes without spawning any process.

    This is only a worker drift check, not standalone historical provenance.
    The parent MUST call validate_sources before and after worker execution to
    authenticate the complete historical inventory, Git blobs, and file modes.
    This function checks the same strict receipt schema and bounded regular,
    nonsymlink files; the receipt itself records byte counts and SHA256 only.
    """
    files = _validated_files(record)
    for relative in sorted(files):
        descriptor, _, _ = _fingerprint(relative)
        if descriptor != files[relative]:
            raise ReviewSourceError(f"review requires its recorded source bytes: {relative}")


def validate_sources(record: dict[str, object]) -> None:
    """Authenticate exact historical source bytes, never a self-resealed claim.

    No current-HEAD equality or present-day directory glob is required: an
    archive can survive later unrelated additions. Every file recorded at its
    commit, including its verifier and kernel, must still match exactly.
    """
    files = _validated_files(record)
    historical = _historical_inventory(record["git_commit"])
    if set(files) != set(historical):
        raise ReviewSourceError("source identity is not its exact historical Git inventory")
    for relative in sorted(files):
        descriptor, mode, blob = _fingerprint(relative)
        if descriptor != files[relative]:
            raise ReviewSourceError(f"review requires its recorded source bytes: {relative}")
        if (mode, blob) != historical[relative]:
            raise ReviewSourceError(f"review source differs from its recorded Git blob: {relative}")
