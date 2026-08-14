#!/usr/bin/env python3
"""Derive external clean-Git source evidence for the bounded Hydra A2.3c negative replay.

This program deliberately does not import the dependency-vector replayer it
identifies.  It reads four frozen replayer files, proves that their live bytes
are the stage-0 regular blobs at ``HEAD``, and emits two separate canonical
documents:

* the exact eight-field source-state object used by the external WMI execution boundary; and
* a domain-separated Git verification receipt.

No file is written by default.  With explicit output paths the source state is
published first and the Git receipt last, so the receipt is the pair's commit
marker.  Existing destinations are never replaced.

The resolved host Git executable is a trust precondition, not proof authority;
the receipt makes that precondition auditable by recording its path, bytes,
SHA-256 digest, version, and every bounded invocation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path("scripts/build_peano_hydra_a23c_replayer_source_state.py")

# These are raw-file SHA-256 pins, not Git blob object names and not semantic
# JSON digests.  Their order is part of the source-state protocol.
FROZEN_REPLAYER_SOURCES: tuple[tuple[Path, str], ...] = (
    (
        Path(
            "training/peano_hydra/"
            "library-pilot-dependency-vector-negative-replay-schema-v1.json"
        ),
        "be38f796e9d8923024514962f7cc5a5a4f19c828cf502e2912f1ea5094d12ce4",
    ),
    (
        Path(
            "training/peano_hydra/"
            "library_pilot_dependency_vector_negative_replay.py"
        ),
        "f5b5dd45c0ce4e2ed5587fd41b7ea206e92ee05526aebf7be96d80f5bb591aa4",
    ),
    (
        Path(
            "scripts/"
            "verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py"
        ),
        "524ced1b5ca78040ddccc3030f2d5eee9f10c8bdf455ea96efb625595c72759b",
    ),
    (
        Path(
            "peano-lab/py/tests/"
            "test_peano_hydra_library_pilot_dependency_vector_negative_replay.py"
        ),
        "dc5591dcc9d1e48028d1fbaf31971e65bc10c69377167b50317d4558596e6e82",
    ),
)

SOURCE_STATE_FORMAT = "peano-hydra-a23c-replayer-source-state"
SOURCE_STATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-a23c-replayer-source-state-root-preimage"
)
GIT_RECEIPT_FORMAT = "peano-hydra-a23c-replayer-git-verification-receipt"
GIT_RECEIPT_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-a23c-replayer-git-verification-receipt-root-preimage"
)
EVIDENCE_ENVELOPE_FORMAT = "peano-hydra-a23c-replayer-evidence"
EVIDENCE_ENVELOPE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-a23c-replayer-evidence-root-preimage"
)
VERSION = 1

MAX_SOURCE_FILE_BYTES = 16_000_000
MAX_TOOL_FILE_BYTES = 64_000_000
MAX_GIT_STDOUT_BYTES = 32_000_000
MAX_GIT_STDERR_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 4_000_000
MAX_JSON_DEPTH = 64
MAX_JSON_ITEMS = 20_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
GIT_TIMEOUT_SECONDS = 30.0

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_SHA1_RE = re.compile(r"[0-9a-f]{40}")
_GIT_VERSION_RE = re.compile(r"git version [^\r\n]+\n?\Z")
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_REGULAR_GIT_MODES = frozenset({"100644", "100755"})


class ReplayerSourceStateError(ValueError):
    """The source tree, Git evidence, JSON, or requested publication is invalid."""


@dataclass(frozen=True, slots=True)
class GitResult:
    """One bounded Git invocation and its canonical receipt row."""

    argv: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes

    def receipt(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "exit_code": self.returncode,
            "stderr_bytes": len(self.stderr),
            "stderr_sha256": _sha256_bytes(self.stderr),
            "stdout_bytes": len(self.stdout),
            "stdout_sha256": _sha256_bytes(self.stdout),
        }


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_json(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> int:
    if depth > MAX_JSON_DEPTH:
        raise ReplayerSourceStateError(f"{path} exceeds the JSON depth limit")
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise ReplayerSourceStateError(
                f"{path} exceeds the safe JSON integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ReplayerSourceStateError(
                f"{path} contains a Unicode surrogate"
            ) from None
        return 1
    if type(value) not in (list, dict):
        raise ReplayerSourceStateError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise ReplayerSourceStateError(f"{path} contains a cycle")
    if len(value) > MAX_JSON_ITEMS:
        raise ReplayerSourceStateError(f"{path} has too many items")
    descendants = ancestors | {marker}
    count = 1
    if type(value) is list:
        for index, item in enumerate(value):
            count += _validate_json(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=descendants,
            )
            if count > MAX_JSON_ITEMS:
                raise ReplayerSourceStateError("JSON document has too many items")
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise ReplayerSourceStateError(f"{path} contains a non-string key")
        count += _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=descendants,
        )
        if count > MAX_JSON_ITEMS:
            raise ReplayerSourceStateError("JSON document has too many items")
    return count


def _compact_json(value: object) -> bytes:
    _validate_json(value)
    try:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ReplayerSourceStateError("cannot encode compact canonical JSON") from exc
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ReplayerSourceStateError("compact canonical JSON is too large")
    return raw


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json(value))


def canonical_document_bytes(value: object) -> bytes:
    """Return the canonical, retained JSON representation."""

    _validate_json(value)
    try:
        raw = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ReplayerSourceStateError("cannot encode canonical JSON") from exc
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ReplayerSourceStateError("canonical JSON is too large")
    return raw


def _repository_root(value: Path) -> Path:
    if not isinstance(value, Path):
        raise TypeError("repository_root must be pathlib.Path")
    try:
        metadata = value.lstat()
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise ReplayerSourceStateError("cannot resolve repository_root") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ReplayerSourceStateError(
            "repository_root must be a non-symlink directory"
        )
    return resolved


def _safe_relative_file(root: Path, relative: Path, *, limit: int) -> bytes:
    if (
        not isinstance(relative, Path)
        or relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ReplayerSourceStateError("source path is not a safe relative path")
    current = root
    try:
        for component in relative.parts[:-1]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise ReplayerSourceStateError(
                    f"source parent is linked or not a directory: {relative.as_posix()}"
                )
    except ReplayerSourceStateError:
        raise
    except OSError as exc:
        raise ReplayerSourceStateError(
            f"cannot inspect source parent: {relative.as_posix()}"
        ) from exc

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(root / relative, flags)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size <= 0
            or before.st_size > limit
        ):
            raise ReplayerSourceStateError(
                f"source is not a bounded nonempty regular file: {relative.as_posix()}"
            )
        chunks: list[bytes] = []
        remaining = before.st_size + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if len(raw) != before.st_size or (
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
            raise ReplayerSourceStateError(
                f"source changed while read: {relative.as_posix()}"
            )
        return raw
    except ReplayerSourceStateError:
        raise
    except OSError as exc:
        raise ReplayerSourceStateError(
            f"cannot read source: {relative.as_posix()}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _safe_absolute_file(path: Path, *, limit: int) -> tuple[Path, bytes]:
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.lstat()
    except OSError as exc:
        raise ReplayerSourceStateError("cannot resolve Git executable") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0:
        raise ReplayerSourceStateError("Git executable is not a regular file")
    parent = resolved.parent
    name = Path(resolved.name)
    raw = _safe_relative_file(parent, name, limit=limit)
    return resolved, raw


def _bounded_process(
    executable: Path,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float = GIT_TIMEOUT_SECONDS,
) -> GitResult:
    if not args or any(type(item) is not str or "\x00" in item for item in args):
        raise ReplayerSourceStateError("Git argv is malformed")
    normalized = ("git", *args)
    # Start from no ambient process state.  In particular, GIT_DIR,
    # GIT_WORK_TREE, GIT_INDEX_FILE, object-store/namespace variables, and the
    # counted GIT_CONFIG_KEY/VALUE vector could otherwise redirect the source
    # observation.  The resolved Git executable is a host-controlled trust
    # precondition whose exact path and bytes are recorded in the receipt.
    environment = {
        "GIT_CONFIG_COUNT": "0",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": "/nonexistent/peano-hydra-a23c-source-state",
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
        "TMPDIR": "/tmp",
        "TZ": "UTC",
    }
    try:
        process = subprocess.Popen(
            [str(executable), *args],
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
        )
    except OSError as exc:
        raise ReplayerSourceStateError("cannot execute Git") from exc
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    deadline = time.monotonic() + timeout
    try:
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ReplayerSourceStateError("Git command timed out")
            events = selector.select(min(remaining, 0.25))
            if not events and process.poll() is not None:
                # Pipes may still contain bytes after process exit; keep polling
                # until EOF rather than trusting the return code as a drain signal.
                continue
            for key, _mask in events:
                stream = key.fileobj
                try:
                    chunk = os.read(stream.fileno(), 65_536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    continue
                destination = stdout if stream is process.stdout else stderr
                limit = (
                    MAX_GIT_STDOUT_BYTES
                    if stream is process.stdout
                    else MAX_GIT_STDERR_BYTES
                )
                destination.extend(chunk)
                if len(destination) > limit:
                    raise ReplayerSourceStateError("Git output exceeds its byte limit")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ReplayerSourceStateError("Git command timed out")
        returncode = process.wait(timeout=remaining)
    except (ReplayerSourceStateError, subprocess.TimeoutExpired):
        process.kill()
        process.wait()
        raise ReplayerSourceStateError("Git command failed its resource bounds") from None
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
    return GitResult(normalized, returncode, bytes(stdout), bytes(stderr))


def _require_git(
    executable: Path,
    args: Sequence[str],
    *,
    cwd: Path,
    commands: list[dict[str, object]],
    allowed_codes: frozenset[int] = frozenset({0}),
) -> GitResult:
    result = _bounded_process(executable, args, cwd=cwd)
    commands.append(result.receipt())
    if result.returncode not in allowed_codes:
        raise ReplayerSourceStateError(
            f"Git command failed: {' '.join(result.argv)}"
        )
    return result


def _one_line_sha1(raw: bytes, label: str) -> str:
    try:
        value = raw.decode("ascii").removesuffix("\n")
    except UnicodeDecodeError:
        raise ReplayerSourceStateError(f"{label} is not ASCII") from None
    if _SHA1_RE.fullmatch(value) is None:
        raise ReplayerSourceStateError(f"{label} is not a lowercase SHA-1")
    return value


def _git_blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(prefix + raw, usedforsecurity=False).hexdigest()


def _stage_zero_regular_blob(raw: bytes, expected_path: Path) -> tuple[str, str]:
    if not raw.endswith(b"\0") or raw.count(b"\0") != 1:
        raise ReplayerSourceStateError(
            f"Git index row is malformed: {expected_path.as_posix()}"
        )
    row = raw[:-1]
    try:
        header, path_raw = row.split(b"\t", 1)
        mode_raw, oid_raw, stage_raw = header.split(b" ", 2)
        mode = mode_raw.decode("ascii")
        oid = oid_raw.decode("ascii")
        path = path_raw.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        raise ReplayerSourceStateError(
            f"Git index row is malformed: {expected_path.as_posix()}"
        ) from None
    if (
        mode not in _REGULAR_GIT_MODES
        or _SHA1_RE.fullmatch(oid) is None
        or stage_raw != b"0"
        or path != expected_path.as_posix()
    ):
        raise ReplayerSourceStateError(
            f"path is not one stage-0 regular blob: {expected_path.as_posix()}"
        )
    return mode, oid


def _source_state(
    *, commit_sha1: str, tree_sha1: str, source_rows: list[dict[str, object]]
) -> dict[str, object]:
    body: dict[str, object] = {
        "commit_sha1": commit_sha1,
        "files": source_rows,
        "format": SOURCE_STATE_FORMAT,
        "git_verified": False,
        "tree_sha1": tree_sha1,
        "v": VERSION,
    }
    preimage = {
        "format": SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": VERSION,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }


def validate_replayer_source_state(
    value: object, *, repository_root: Path
) -> dict[str, object]:
    """Validate the frozen eight-field shape and its live file identities."""

    root = _repository_root(repository_root)
    if type(value) is not dict or set(value) != {
        "commit_sha1",
        "files",
        "format",
        "git_verified",
        "root_preimage",
        "root_sha256",
        "tree_sha1",
        "v",
    }:
        raise ReplayerSourceStateError("replayer source state has the wrong fields")
    if (
        value.get("format") != SOURCE_STATE_FORMAT
        or value.get("v") != VERSION
        or value.get("git_verified") is not False
        or type(value.get("commit_sha1")) is not str
        or _SHA1_RE.fullmatch(value["commit_sha1"]) is None
        or type(value.get("tree_sha1")) is not str
        or _SHA1_RE.fullmatch(value["tree_sha1"]) is None
    ):
        raise ReplayerSourceStateError("replayer source state identity is malformed")
    rows = value.get("files")
    if type(rows) is not list or len(rows) != len(FROZEN_REPLAYER_SOURCES):
        raise ReplayerSourceStateError("replayer source file list is malformed")
    for row, (expected_path, expected_sha256) in zip(
        rows, FROZEN_REPLAYER_SOURCES, strict=True
    ):
        if type(row) is not dict or set(row) != {"bytes", "path", "sha256"}:
            raise ReplayerSourceStateError("replayer source file row is malformed")
        raw = _safe_relative_file(
            root, expected_path, limit=MAX_SOURCE_FILE_BYTES
        )
        if (
            row.get("path") != expected_path.as_posix()
            or type(row.get("bytes")) is not int
            or row["bytes"] != len(raw)
            or row.get("sha256") != expected_sha256
            or _sha256_bytes(raw) != expected_sha256
        ):
            raise ReplayerSourceStateError(
                f"replayer source identity drifted: {expected_path.as_posix()}"
            )
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": VERSION,
    }
    if value.get("root_preimage") != preimage or value.get(
        "root_sha256"
    ) != _sha256_json(preimage):
        raise ReplayerSourceStateError("replayer source-state root is malformed")
    return json.loads(_compact_json(value))


def _authority_claims() -> dict[str, object]:
    return {
        "a2_complete": False,
        "dependency_vectors_complete": False,
        "evaluation_eligible": False,
        "freeze_ready": False,
        "lineage_complete": False,
        "minimality_claim": False,
        "optimized_best_known": False,
        "optimized_vector_independently_audited": False,
        "proof_authority": False,
        "public_graph_applied": False,
        "publication_authority": False,
        "publication_ready": False,
        "publication_union_complete": False,
        "publication_union_verified": False,
        "retrieval_eligible": False,
        "review_complete": False,
        "theorem_admission_authority": False,
        "training_eligible": False,
    }


def build_replayer_evidence(
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Build source state, Git receipt, and the canonical stdout envelope."""

    root = _repository_root(repository_root)
    which = shutil.which("git")
    if which is None:
        raise ReplayerSourceStateError("Git executable is unavailable")
    git_path, git_raw = _safe_absolute_file(Path(which), limit=MAX_TOOL_FILE_BYTES)
    commands: list[dict[str, object]] = []

    version_result = _require_git(git_path, ("--version",), cwd=root, commands=commands)
    try:
        git_version = version_result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise ReplayerSourceStateError("Git version output is not UTF-8") from None
    if version_result.stderr or _GIT_VERSION_RE.fullmatch(git_version) is None:
        raise ReplayerSourceStateError("Git version output is malformed")
    git_version = git_version.rstrip("\n")

    top_result = _require_git(
        git_path,
        ("rev-parse", "--show-toplevel"),
        cwd=root,
        commands=commands,
    )
    try:
        top = Path(top_result.stdout.decode("utf-8").rstrip("\n")).resolve(strict=True)
    except (UnicodeDecodeError, OSError):
        raise ReplayerSourceStateError("Git top-level output is malformed") from None
    if top != root:
        raise ReplayerSourceStateError("repository_root is not the Git top level")

    head_before = _one_line_sha1(
        _require_git(
            git_path,
            ("rev-parse", "--verify", "HEAD"),
            cwd=root,
            commands=commands,
        ).stdout,
        "HEAD before",
    )
    tree_before = _one_line_sha1(
        _require_git(
            git_path,
            ("rev-parse", "--verify", "HEAD^{tree}"),
            cwd=root,
            commands=commands,
        ).stdout,
        "HEAD tree before",
    )
    status_before = _require_git(
        git_path,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=root,
        commands=commands,
    ).stdout
    if status_before:
        raise ReplayerSourceStateError("Git worktree is not clean before verification")
    _require_git(
        git_path,
        ("diff", "--quiet", "--no-ext-diff", "--"),
        cwd=root,
        commands=commands,
    )
    _require_git(
        git_path,
        ("diff", "--cached", "--quiet", "--no-ext-diff", "--"),
        cwd=root,
        commands=commands,
    )

    live: dict[Path, bytes] = {}
    verified_rows: list[dict[str, object]] = []
    paths = tuple(path for path, _sha in FROZEN_REPLAYER_SOURCES) + (
        GENERATOR_PATH,
    )
    frozen_hashes = dict(FROZEN_REPLAYER_SOURCES)
    for relative in paths:
        limit = (
            MAX_SOURCE_FILE_BYTES
            if relative != GENERATOR_PATH
            else MAX_SOURCE_FILE_BYTES
        )
        raw = _safe_relative_file(root, relative, limit=limit)
        live[relative] = raw
        live_sha256 = _sha256_bytes(raw)
        expected = frozen_hashes.get(relative)
        if expected is not None and live_sha256 != expected:
            raise ReplayerSourceStateError(
                f"frozen replayer hash drifted: {relative.as_posix()}"
            )
        index = _require_git(
            git_path,
            ("ls-files", "--stage", "-z", "--", relative.as_posix()),
            cwd=root,
            commands=commands,
        )
        mode, blob_oid = _stage_zero_regular_blob(index.stdout, relative)
        committed = _require_git(
            git_path,
            (
                "show",
                "--no-ext-diff",
                "--no-textconv",
                f"{head_before}:{relative.as_posix()}",
            ),
            cwd=root,
            commands=commands,
        ).stdout
        if committed != raw or _git_blob_sha1(committed) != blob_oid:
            raise ReplayerSourceStateError(
                f"live/index/HEAD bytes disagree: {relative.as_posix()}"
            )
        verified_rows.append(
            {
                "blob_oid_sha1": blob_oid,
                "bytes": len(raw),
                "committed_sha256": _sha256_bytes(committed),
                "live_sha256": live_sha256,
                "mode": mode,
                "path": relative.as_posix(),
                "verified": True,
            }
        )

    # Read every owned input again before the final Git observation.  This
    # closes the ordinary replace/modify race without trusting path metadata.
    for relative, first in live.items():
        second = _safe_relative_file(root, relative, limit=MAX_SOURCE_FILE_BYTES)
        if second != first:
            raise ReplayerSourceStateError(
                f"source changed during verification: {relative.as_posix()}"
            )

    head_after = _one_line_sha1(
        _require_git(
            git_path,
            ("rev-parse", "--verify", "HEAD"),
            cwd=root,
            commands=commands,
        ).stdout,
        "HEAD after",
    )
    tree_after = _one_line_sha1(
        _require_git(
            git_path,
            ("rev-parse", "--verify", "HEAD^{tree}"),
            cwd=root,
            commands=commands,
        ).stdout,
        "HEAD tree after",
    )
    status_after = _require_git(
        git_path,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=root,
        commands=commands,
    ).stdout
    if status_after:
        raise ReplayerSourceStateError("Git worktree is not clean after verification")
    _require_git(
        git_path,
        ("diff", "--quiet", "--no-ext-diff", "--"),
        cwd=root,
        commands=commands,
    )
    _require_git(
        git_path,
        ("diff", "--cached", "--quiet", "--no-ext-diff", "--"),
        cwd=root,
        commands=commands,
    )
    if head_after != head_before or tree_after != tree_before:
        raise ReplayerSourceStateError("HEAD or its tree changed during verification")
    final_git_path, final_git_raw = _safe_absolute_file(
        Path(which), limit=MAX_TOOL_FILE_BYTES
    )
    if final_git_path != git_path or final_git_raw != git_raw:
        raise ReplayerSourceStateError("Git executable changed during verification")

    source_rows = [
        {
            "bytes": len(live[path]),
            "path": path.as_posix(),
            "sha256": frozen_hashes[path],
        }
        for path, _expected in FROZEN_REPLAYER_SOURCES
    ]
    source_state = _source_state(
        commit_sha1=head_before,
        tree_sha1=tree_before,
        source_rows=source_rows,
    )
    validate_replayer_source_state(source_state, repository_root=root)
    source_state_raw = canonical_document_bytes(source_state)

    generator_row = verified_rows[-1]
    receipt_body: dict[str, object] = {
        "authority_claims": _authority_claims(),
        "commands": commands,
        "commit_sha1": head_before,
        "format": GIT_RECEIPT_FORMAT,
        "generator": generator_row,
        "git_tool": {
            "bytes": len(git_raw),
            "path": str(git_path),
            "sha256": _sha256_bytes(git_raw),
            "version": git_version,
        },
        "source_files": verified_rows[:-1],
        "source_state_artifact_sha256": _sha256_bytes(source_state_raw),
        "source_state_root_sha256": source_state["root_sha256"],
        "source_state_sha256": _sha256_json(source_state),
        "status": "passed",
        "tree_sha1": tree_before,
        "v": VERSION,
        "verification": {
            "clean_after": True,
            "clean_before": True,
            "commit_stable": True,
            "diff_cached_quiet_after": True,
            "diff_cached_quiet_before": True,
            "diff_quiet_after": True,
            "diff_quiet_before": True,
            "generator_matches_head": True,
            "head_after": head_after,
            "head_before": head_before,
            "porcelain_after_bytes": len(status_after),
            "porcelain_after_sha256": _sha256_bytes(status_after),
            "porcelain_before_bytes": len(status_before),
            "porcelain_before_sha256": _sha256_bytes(status_before),
            "replayer_files_match_head": True,
            "stage_zero_regular_blobs": True,
            "tree_after": tree_after,
            "tree_before": tree_before,
            "tree_stable": True,
        },
    }
    receipt_preimage = {
        "format": GIT_RECEIPT_ROOT_PREIMAGE_FORMAT,
        "payload": receipt_body,
        "v": VERSION,
    }
    receipt = {
        **receipt_body,
        "root_preimage": receipt_preimage,
        "root_sha256": _sha256_json(receipt_preimage),
    }
    receipt_raw = canonical_document_bytes(receipt)

    envelope_body: dict[str, object] = {
        "format": EVIDENCE_ENVELOPE_FORMAT,
        "git_receipt": receipt,
        "git_receipt_artifact_sha256": _sha256_bytes(receipt_raw),
        "git_receipt_root_sha256": receipt["root_sha256"],
        "source_state": source_state,
        "source_state_artifact_sha256": _sha256_bytes(source_state_raw),
        "source_state_root_sha256": source_state["root_sha256"],
        "v": VERSION,
    }
    envelope_preimage = {
        "format": EVIDENCE_ENVELOPE_ROOT_PREIMAGE_FORMAT,
        "payload": envelope_body,
        "v": VERSION,
    }
    envelope = {
        **envelope_body,
        "root_preimage": envelope_preimage,
        "root_sha256": _sha256_json(envelope_preimage),
    }
    canonical_document_bytes(envelope)
    return source_state, receipt, envelope


def build_replayer_source_state(
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    """Build the exact source-state child while retaining full Git verification."""

    source_state, _receipt, _envelope = build_replayer_evidence(repository_root)
    return source_state


def build_git_verification_receipt(
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    """Build the Git receipt child while retaining the exact source-state binding."""

    _source_state, receipt, _envelope = build_replayer_evidence(repository_root)
    return receipt


def _lexical_absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("output path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_output_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise ReplayerSourceStateError(
                    "output parent contains a link or non-directory component"
                )
        return current
    except ReplayerSourceStateError:
        raise
    except OSError as exc:
        raise ReplayerSourceStateError("cannot inspect output parent") from exc


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ReplayerSourceStateError("cannot inspect output destination") from exc
    raise ReplayerSourceStateError(
        "output destination already exists; use --check to verify it"
    )


def _publish_one(path: Path, raw: bytes) -> tuple[Path, tuple[int, int]]:
    destination = _lexical_absolute(path)
    parent = _safe_output_parent(destination)
    _require_absent(destination)
    descriptor: int | None = None
    temporary: Path | None = None
    temporary_identity: tuple[int, int] | None = None
    link_created = False
    completed = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=parent
        )
        temporary = Path(temporary_name)
        initial = os.fstat(descriptor)
        if not stat.S_ISREG(initial.st_mode):
            raise ReplayerSourceStateError(
                "staged output descriptor is not regular"
            )
        temporary_identity = (initial.st_dev, initial.st_ino)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(raw)
            stream.flush()
            os.fchmod(stream.fileno(), 0o644)
            os.fsync(stream.fileno())
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or (metadata.st_dev, metadata.st_ino) != temporary_identity
                or metadata.st_size != len(raw)
                or stat.S_IMODE(metadata.st_mode) != 0o644
            ):
                raise ReplayerSourceStateError(
                    "staged output descriptor identity, size, or mode drifted"
                )
        staged = temporary.lstat()
        if (
            stat.S_ISLNK(staged.st_mode)
            or not stat.S_ISREG(staged.st_mode)
            or (staged.st_dev, staged.st_ino) != temporary_identity
            or staged.st_size != len(raw)
            or stat.S_IMODE(staged.st_mode) != 0o644
        ):
            raise ReplayerSourceStateError(
                "staged output path no longer names its authenticated descriptor"
            )
        _require_absent(destination)
        os.link(temporary, destination, follow_symlinks=False)
        link_created = True
        published = destination.lstat()
        if (
            stat.S_ISLNK(published.st_mode)
            or not stat.S_ISREG(published.st_mode)
            or (published.st_dev, published.st_ino) != temporary_identity
            or published.st_size != len(raw)
            or stat.S_IMODE(published.st_mode) != 0o644
        ):
            raise ReplayerSourceStateError(
                "published output identity, size, or mode is malformed"
            )
        _remove_if_identity(temporary, temporary_identity)
        directory = os.open(
            parent,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        completed = True
        return destination, temporary_identity
    except FileExistsError as exc:
        raise ReplayerSourceStateError(
            "output destination raced or already exists"
        ) from exc
    except (OSError, ReplayerSourceStateError) as exc:
        if isinstance(exc, ReplayerSourceStateError):
            raise
        raise ReplayerSourceStateError("cannot publish output document") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if not completed and link_created and temporary_identity is not None:
            _remove_if_identity(destination, temporary_identity)
        if temporary is not None and temporary_identity is not None:
            _remove_if_identity(temporary, temporary_identity)


def _remove_if_identity(path: Path, identity: tuple[int, int]) -> None:
    try:
        metadata = path.lstat()
        if (
            stat.S_ISREG(metadata.st_mode)
            and not stat.S_ISLNK(metadata.st_mode)
            and (metadata.st_dev, metadata.st_ino) == identity
        ):
            path.unlink()
    except OSError:
        pass


def _read_exact(path: Path, expected: bytes) -> None:
    destination = _lexical_absolute(path)
    _safe_output_parent(destination)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(destination, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size != len(expected):
            raise ReplayerSourceStateError(
                "output differs from the deterministic clean-Git derivation"
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
        if actual != expected or (
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
            raise ReplayerSourceStateError(
                "output differs from the deterministic clean-Git derivation"
            )
    except ReplayerSourceStateError:
        raise
    except OSError as exc:
        raise ReplayerSourceStateError("cannot read output for --check") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _publish_pair(
    source_path: Path,
    source_raw: bytes,
    receipt_path: Path,
    receipt_raw: bytes,
) -> None:
    source_destination = _lexical_absolute(source_path)
    receipt_destination = _lexical_absolute(receipt_path)
    if source_destination == receipt_destination:
        raise ReplayerSourceStateError("the two output paths must be distinct")
    _require_absent(source_destination)
    _require_absent(receipt_destination)
    published_source: tuple[Path, tuple[int, int]] | None = None
    try:
        # The receipt is deliberately last: it is the pair's commit marker.
        published_source = _publish_one(source_destination, source_raw)
        _publish_one(receipt_destination, receipt_raw)
    except ReplayerSourceStateError:
        if published_source is not None:
            _remove_if_identity(*published_source)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="clean Git top level to verify (default: this script's repository)",
    )
    parser.add_argument(
        "--source-state-output",
        type=Path,
        help="create-only destination for the raw eight-field source state",
    )
    parser.add_argument(
        "--git-receipt-output",
        type=Path,
        help="create-only destination for the raw Git receipt (published last)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-check both existing explicit outputs instead of creating them",
    )
    args = parser.parse_args(argv)
    if (args.source_state_output is None) != (args.git_receipt_output is None):
        parser.error("both output paths must be supplied together")
    if args.check and args.source_state_output is None:
        parser.error("--check requires both output paths")

    source_state, receipt, envelope = build_replayer_evidence(args.repository_root)
    source_raw = canonical_document_bytes(source_state)
    receipt_raw = canonical_document_bytes(receipt)
    if args.check:
        _read_exact(args.source_state_output, source_raw)
        _read_exact(args.git_receipt_output, receipt_raw)
    elif args.source_state_output is not None:
        _publish_pair(
            args.source_state_output,
            source_raw,
            args.git_receipt_output,
            receipt_raw,
        )

    sys.stdout.buffer.write(canonical_document_bytes(envelope))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReplayerSourceStateError as exc:
        raise SystemExit(str(exc)) from None
