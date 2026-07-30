"""Immutable, adapter-only recovery evidence for an interrupted training run.

These snapshots are deliberately *not* Transformers checkpoints.  They contain
no optimizer, scheduler, random-number-generator, or ``trainer_state`` bytes and
must never be passed to ``Trainer.train(resume_from_checkpoint=...)``.  Their
only purpose is to preserve useful LoRA weights if a one-shot model-v3 job ends
before its final adapter and training manifest can be published.

A snapshot becomes recognizable only when ``recovery-manifest.json`` is written
last.  The manifest says explicitly that training is incomplete and binds the
adapter bytes to the immutable run identity, source tree, and scheduler job.
No code in this module replaces or removes an existing path.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import stat
import sys
import tempfile
from typing import Any, Mapping

from .manifest import (
    artifact_directory_hash,
    require_safetensors_adapter,
    sha256_json,
    verify_artifact_directory,
)


RECOVERY_DIRECTORY = "recovery-snapshots"
RECOVERY_MANIFEST = "recovery-manifest.json"
RECOVERY_FORMAT = "peano-policy-adapter-recovery-snapshot"
RECOVERY_VERSION = 1
RECOVERY_PUBLICATION_PREFLIGHT_FORMAT = (
    "peano-policy-recovery-publication-filesystem-preflight"
)
RECOVERY_PUBLICATION_PREFLIGHT_VERSION = 1
_MAX_INTERVAL_STEPS = 100
_TARGET_SNAPSHOT_COUNT = 6
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_PREFLIGHT_PARENT_PREFIX = ".recovery-publication-preflight-"
_PREFLIGHT_SOURCE_NAME = "source"
_PREFLIGHT_DESTINATION_NAME = "published"
_PREFLIGHT_SENTINEL_NAME = "publication-sentinel.bin"
_PREFLIGHT_SENTINEL_BYTES = 64


class RecoverySnapshotError(RuntimeError):
    """A recovery snapshot could not be safely created or verified."""


def recovery_snapshot_plan(expected_optimizer_steps: int) -> dict[str, object]:
    """Return the deterministic adapter-only snapshot schedule.

    The interval is at most 100 optimizer steps and is reduced for shorter
    experiments to target roughly six intermediate saves.  The terminal step
    is excluded because the trainer writes the canonical final adapter there.
    A one-step experiment has no meaningful intermediate state.
    """

    if type(expected_optimizer_steps) is not int or expected_optimizer_steps < 1:
        raise ValueError("recovery planning requires a positive optimizer-step count")
    interval = min(
        _MAX_INTERVAL_STEPS,
        max(1, expected_optimizer_steps // _TARGET_SNAPSHOT_COUNT),
    )
    steps = list(range(interval, expected_optimizer_steps, interval))
    return {
        "format": "peano-policy-adapter-recovery-plan",
        "v": 1,
        "artifact": "adapter-safetensors-only",
        "resumable": False,
        "optimizer_state_included": False,
        "interval_optimizer_steps": interval,
        "planned_optimizer_steps": steps,
    }


def _strict_json_bytes(raw: bytes, *, location: str) -> object:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            if key in result:
                raise RecoverySnapshotError(
                    f"duplicate recovery-manifest key: {key}"
                )
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise RecoverySnapshotError(
            f"non-finite recovery-manifest number: {value}"
        )

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except RecoverySnapshotError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RecoverySnapshotError(
            f"cannot decode strict JSON at {location}: {exc}"
        ) from None


def _strict_json(path: Path) -> object:
    raw, _ = _stable_file_bytes(path, label="recovery JSON")
    return _strict_json_bytes(raw, location=str(path))


def _detached_json(value: object, *, label: str) -> object:
    try:
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not strict JSON: {exc}") from None


def _regular_file(path: Path, *, label: str) -> None:
    try:
        value = path.lstat()
    except OSError as exc:
        raise RecoverySnapshotError(f"cannot inspect {label} {path}: {exc}") from exc
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        raise RecoverySnapshotError(f"{label} is not one regular file: {path}")


def _stable_file_bytes(path: Path, *, label: str) -> tuple[bytes, str]:
    """Read one opened inode and recheck that its pathname still names it."""

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RecoverySnapshotError(f"cannot open {label} {path}: {exc}") from exc
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise RecoverySnapshotError(f"{label} is not one regular file: {path}")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            while block := stream.read(1024 * 1024):
                chunks.append(block)
                digest.update(block)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise RecoverySnapshotError(f"cannot read {label} {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    try:
        current = os.lstat(path)
    except OSError as exc:
        raise RecoverySnapshotError(f"{label} disappeared while read: {path}") from exc
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if (
        stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
        or any(getattr(opened, field) != getattr(after, field) for field in fields)
        or any(getattr(opened, field) != getattr(current, field) for field in fields)
    ):
        raise RecoverySnapshotError(f"{label} changed while read: {path}")
    return b"".join(chunks), digest.hexdigest()


def _stable_file_digest(path: Path, *, label: str) -> str:
    return _stable_file_bytes(path, label=label)[1]


def _safe_directory(path: Path, *, label: str) -> None:
    try:
        value = path.lstat()
    except OSError as exc:
        raise RecoverySnapshotError(f"cannot inspect {label} {path}: {exc}") from exc
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
        raise RecoverySnapshotError(f"{label} is not one ordinary directory: {path}")


def _job_label(job: Mapping[str, object]) -> str:
    scheduler = job.get("scheduler")
    if scheduler == "slurm":
        value = job.get("job_id")
        if type(value) is not str or not value.isdecimal():
            raise ValueError("Slurm recovery identity requires a decimal job id")
        return value
    if scheduler == "none":
        return "local"
    raise ValueError("recovery identity has an unsupported scheduler")


def _snapshot_name(step: int, run_identity_sha256: str, job_label: str) -> str:
    return f"step-{step:08d}-run-{run_identity_sha256[:16]}-job-{job_label}"


def _write_new_manifest(path: Path, value: Mapping[str, object]) -> None:
    """Durably create one canonical manifest without replacement semantics."""

    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RecoverySnapshotError(
            f"refusing to replace recovery manifest {path}: {exc}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        directory_descriptor = os.open(
            path.parent,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    """Encode one strict, byte-canonical JSON object."""

    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RecoverySnapshotError(
            f"recovery publication report is not strict JSON: {exc}"
        ) from None


def _write_new_canonical_report(
    path: Path, value: Mapping[str, object]
) -> None:
    """Durably create one protected report, never replacing a pathname."""

    payload = _canonical_json_bytes(value)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RecoverySnapshotError(
            f"refusing to replace recovery publication report {path}: {exc}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(path, 0o444, follow_symlinks=False)
        report_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(report_metadata.st_mode)
            or report_metadata.st_nlink != 1
            or stat.S_IMODE(report_metadata.st_mode) != 0o444
        ):
            raise RecoverySnapshotError(
                "recovery publication report did not acquire protected regular-file mode"
            )
        report_descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            os.fsync(report_descriptor)
        finally:
            os.close(report_descriptor)
        _fsync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_tree(root: Path) -> None:
    """Flush every regular payload before the directory publication point."""

    directories = [root]
    for current, child_directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories.extend(current_path / name for name in child_directories)
        for name in files:
            path = current_path / name
            _regular_file(path, label="recovery artifact")
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path, flags)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    for directory in reversed(directories):
        _fsync_directory(directory)


def _protect_tree(root: Path) -> None:
    """Make a completed staging tree non-writable before publication."""

    for current, directories, files in os.walk(root, topdown=False, followlinks=False):
        current_path = Path(current)
        for name in files:
            os.chmod(current_path / name, 0o444, follow_symlinks=False)
        for name in directories:
            os.chmod(current_path / name, 0o555, follow_symlinks=False)
    os.chmod(root, 0o555, follow_symlinks=False)


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically publish a sibling directory without replacing any target."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        try:
            rename = libc.renamex_np
        except AttributeError as exc:  # pragma: no cover - unsupported old macOS
            raise RecoverySnapshotError(
                "atomic no-replace recovery publication is unavailable"
            ) from exc
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        try:
            rename = libc.renameat2
        except AttributeError as exc:  # pragma: no cover - unsupported old libc
            raise RecoverySnapshotError(
                "atomic no-replace recovery publication is unavailable"
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
    else:  # pragma: no cover - WMI and development hosts are Linux/macOS
        raise RecoverySnapshotError(
            "atomic no-replace recovery publication is unsupported on this OS"
        )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(
            f"refusing to replace existing recovery snapshot {destination}"
        )
    raise OSError(error, os.strerror(error), str(destination))


def _absolute_path(path: Path, *, label: str) -> Path:
    try:
        value = Path(os.path.abspath(os.fspath(path)))
    except (TypeError, ValueError, OSError) as exc:
        raise RecoverySnapshotError(f"invalid {label}: {exc}") from None
    if not value.is_absolute():  # pragma: no cover - abspath is specified to be absolute
        raise RecoverySnapshotError(f"{label} is not absolute")
    return value


def _require_absent(path: Path, *, label: str) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise RecoverySnapshotError(f"cannot inspect {label} {path}: {exc}") from exc
    raise RecoverySnapshotError(f"refusing to replace existing {label} {path}")


def _mode_string(mode: int) -> str:
    return f"0o{stat.S_IMODE(mode):03o}"


def _inode_record(metadata: os.stat_result) -> dict[str, object]:
    """Return the stable identity and protection facts used by the probe."""

    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "links": metadata.st_nlink,
        "mode": _mode_string(metadata.st_mode),
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
    }


def _statvfs_record(path: Path) -> dict[str, int]:
    try:
        value = os.statvfs(path)
    except OSError as exc:
        raise RecoverySnapshotError(
            f"cannot inspect filesystem containing {path}: {exc}"
        ) from exc
    names = (
        "f_bsize",
        "f_frsize",
        "f_blocks",
        "f_bfree",
        "f_bavail",
        "f_files",
        "f_ffree",
        "f_favail",
        "f_flag",
        "f_namemax",
        "f_fsid",
    )
    return {
        name: int(getattr(value, name))
        for name in names
        if hasattr(value, name)
    }


def _publication_mechanism() -> dict[str, object]:
    """Describe the exact syscall branch used by ``_rename_noreplace``."""

    if sys.platform == "darwin":
        return {
            "binding": "ctypes.CDLL(None)",
            "syscall": "renamex_np",
            "flag": "RENAME_EXCL",
            "flag_value": 4,
            "atomic_no_replace": True,
        }
    if sys.platform.startswith("linux"):
        return {
            "binding": "ctypes.CDLL(None)",
            "syscall": "renameat2",
            "flag": "RENAME_NOREPLACE",
            "flag_value": 1,
            "atomic_no_replace": True,
        }
    raise RecoverySnapshotError(
        "atomic no-replace recovery publication is unsupported on this OS"
    )


def _new_probe_parent(root: Path) -> Path:
    """Create an unpredictable, exclusive child without collision cleanup."""

    for _ in range(32):
        candidate = root / f"{_PREFLIGHT_PARENT_PREFIX}{secrets.token_hex(16)}"
        try:
            candidate.mkdir(mode=0o700, exist_ok=False)
        except FileExistsError:
            continue
        except OSError as exc:
            raise RecoverySnapshotError(
                f"cannot create recovery publication probe parent: {exc}"
            ) from exc
        os.chmod(candidate, 0o700, follow_symlinks=False)
        metadata = os.lstat(candidate)
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            raise RecoverySnapshotError(
                f"probe parent has unsafe type or permissions: {candidate}"
            )
        _fsync_directory(candidate)
        _fsync_directory(root)
        return candidate
    raise RecoverySnapshotError(
        "could not allocate an unpredictable exclusive recovery probe parent"
    )


def _write_probe_sentinel(path: Path, payload: bytes) -> None:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RecoverySnapshotError(
            f"cannot exclusively create recovery probe sentinel {path}: {exc}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _restore_failed_probe_source(
    source: Path, *, expected_device: int, expected_inode: int
) -> None:
    """Re-protect our source after a failed Darwin publication attempt."""

    try:
        metadata = os.lstat(source)
    except OSError:
        return
    if (
        stat.S_ISDIR(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and (metadata.st_dev, metadata.st_ino) == (expected_device, expected_inode)
    ):
        os.chmod(source, 0o555, follow_symlinks=False)
        _fsync_directory(source)
        _fsync_directory(source.parent)


def _require_exact_keys(
    value: object, expected: set[str], *, label: str
) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected:
        raise RecoverySnapshotError(f"{label} has an incompatible shape")
    return value


def _require_inode_record(value: object, *, label: str) -> dict[str, object]:
    record = _require_exact_keys(
        value,
        {"device", "inode", "links", "mode", "size", "mtime_ns", "ctime_ns"},
        label=label,
    )
    if (
        any(
            type(record[name]) is not int
            for name in ("device", "inode", "links", "size", "mtime_ns", "ctime_ns")
        )
        or type(record["mode"]) is not str
        or re.fullmatch(r"0o[0-7]{3}", record["mode"]) is None
    ):
        raise RecoverySnapshotError(f"{label} contains invalid inode facts")
    return record


def _strict_preflight_record(
    report_path: Path, *, require_live_publication: bool
) -> dict[str, object]:
    """Read canonical preflight evidence and optionally recheck its live tree."""

    _regular_file(report_path, label="recovery publication report")
    report_metadata = os.lstat(report_path)
    if report_metadata.st_nlink != 1 or stat.S_IMODE(report_metadata.st_mode) != 0o444:
        raise RecoverySnapshotError(
            "recovery publication report is not one protected single-link file"
        )
    raw, _ = _stable_file_bytes(
        report_path, label="recovery publication report"
    )
    record = _strict_json_bytes(raw, location=str(report_path))
    if type(record) is not dict or raw != _canonical_json_bytes(record):
        raise RecoverySnapshotError(
            "recovery publication report is not byte-canonical JSON"
        )
    required = {
        "format",
        "v",
        "status",
        "report",
        "platform",
        "mechanism",
        "filesystem",
        "publication",
    }
    if set(record) != required:
        raise RecoverySnapshotError(
            "recovery publication report has an incompatible shape"
        )
    if (
        record.get("format") != RECOVERY_PUBLICATION_PREFLIGHT_FORMAT
        or record.get("v") != RECOVERY_PUBLICATION_PREFLIGHT_VERSION
        or record.get("status") != "passed"
    ):
        raise RecoverySnapshotError(
            "recovery publication report does not record a passing v1 probe"
        )
    report = record.get("report")
    if report != {
        "path": str(report_path),
        "encoding": "utf-8",
        "canonical_json": "sorted-keys-compact-lf",
        "exclusive_create": True,
        "mode": "0o444",
    }:
        raise RecoverySnapshotError(
            "recovery publication report differs from its external pathname"
        )
    if not require_live_publication:
        return record

    publication = _require_exact_keys(
        record.get("publication"),
        {"probe_parent", "source", "destination", "sentinel", "checks"},
        label="recovery publication evidence",
    )
    filesystem = _require_exact_keys(
        record.get("filesystem"),
        {
            "root",
            "root_device",
            "publication_device",
            "same_device",
            "statvfs",
        },
        label="recovery publication filesystem evidence",
    )
    mechanism = _require_exact_keys(
        record.get("mechanism"),
        {"binding", "syscall", "flag", "flag_value", "atomic_no_replace"},
        label="recovery publication mechanism",
    )
    platform_record = _require_exact_keys(
        record.get("platform"),
        {
            "os_name",
            "sys_platform",
            "system",
            "release",
            "machine",
            "python_implementation",
            "python_version",
            "filesystem_encoding",
            "pointer_bits",
        },
        label="recovery publication platform evidence",
    )
    if (
        any(
            type(platform_record[name]) is not str
            for name in platform_record
            if name != "pointer_bits"
        )
        or type(platform_record["pointer_bits"]) is not int
        or platform_record["pointer_bits"] not in {32, 64}
    ):
        raise RecoverySnapshotError("recovery publication platform facts are malformed")
    if (
        platform_record["os_name"] != os.name
        or platform_record["sys_platform"] != sys.platform
        or platform_record["pointer_bits"] != ctypes.sizeof(ctypes.c_void_p) * 8
    ):
        raise RecoverySnapshotError(
            "recovery publication platform differs from the current process"
        )
    if mechanism != _publication_mechanism():
        raise RecoverySnapshotError(
            "recovery publication mechanism differs from the current platform"
        )
    statvfs_record = filesystem["statvfs"]
    required_statvfs = {
        "f_bsize",
        "f_frsize",
        "f_blocks",
        "f_bfree",
        "f_bavail",
        "f_files",
        "f_ffree",
        "f_favail",
        "f_flag",
        "f_namemax",
    }
    if (
        type(filesystem["root"]) is not str
        or type(filesystem["root_device"]) is not int
        or type(filesystem["publication_device"]) is not int
        or filesystem["same_device"] is not True
        or type(statvfs_record) is not dict
        or not required_statvfs.issubset(statvfs_record)
        or not set(statvfs_record).issubset(required_statvfs | {"f_fsid"})
        or any(type(value) is not int for value in statvfs_record.values())
    ):
        raise RecoverySnapshotError("recovery publication filesystem facts are malformed")
    try:
        root = Path(filesystem["root"])
    except (TypeError, ValueError) as exc:
        raise RecoverySnapshotError(
            f"recovery publication root is malformed: {exc}"
        ) from None
    parent_record = _require_exact_keys(
        publication["probe_parent"],
        {"path", "exclusive_mkdir", "unpredictable_bits", "after"},
        label="recovery probe-parent evidence",
    )
    source_record = _require_exact_keys(
        publication["source"],
        {"path", "exclusive_mkdir", "absent_after"},
        label="recovery source evidence",
    )
    destination_record = _require_exact_keys(
        publication["destination"],
        {
            "path",
            "guaranteed_absent_before",
            "present_after",
            "before",
            "after",
        },
        label="recovery destination evidence",
    )
    sentinel_record = _require_exact_keys(
        publication["sentinel"],
        {"path", "exclusive_create", "content_hex", "size", "sha256", "before", "after"},
        label="recovery sentinel evidence",
    )
    checks = _require_exact_keys(
        publication["checks"],
        {
            "atomic_no_replace_returned",
            "destination_present",
            "directory_inode_preserved",
            "protected_modes",
            "same_device",
            "same_parent",
            "sentinel_bytes_preserved",
            "sentinel_inode_preserved",
            "source_absent",
        },
        label="recovery consistency checks",
    )
    parent_after_record = _require_inode_record(
        parent_record["after"], label="recovery probe-parent inode evidence"
    )
    destination_before_record = _require_inode_record(
        destination_record["before"], label="recovery source inode evidence"
    )
    destination_after_record = _require_inode_record(
        destination_record["after"], label="recovery destination inode evidence"
    )
    sentinel_before_record = _require_inode_record(
        sentinel_record["before"], label="recovery sentinel pre-publication evidence"
    )
    sentinel_after_record = _require_inode_record(
        sentinel_record["after"], label="recovery sentinel post-publication evidence"
    )
    if (
        parent_record["exclusive_mkdir"] is not True
        or parent_record["unpredictable_bits"] != 128
        or source_record["exclusive_mkdir"] is not True
        or source_record["absent_after"] is not True
        or destination_record["guaranteed_absent_before"] is not True
        or destination_record["present_after"] is not True
        or sentinel_record["exclusive_create"] is not True
    ):
        raise RecoverySnapshotError("recovery publication construction facts are malformed")
    try:
        parent = Path(parent_record["path"])
        source = Path(source_record["path"])
        destination = Path(destination_record["path"])
        sentinel = Path(sentinel_record["path"])
    except (KeyError, TypeError) as exc:
        raise RecoverySnapshotError(
            f"recovery publication path evidence is incomplete: {exc}"
        ) from None
    if (
        not all(path.is_absolute() for path in (root, parent, source, destination, sentinel))
        or parent.parent != root
        or not parent.name.startswith(_PREFLIGHT_PARENT_PREFIX)
        or source != parent / _PREFLIGHT_SOURCE_NAME
        or destination != parent / _PREFLIGHT_DESTINATION_NAME
        or sentinel != destination / _PREFLIGHT_SENTINEL_NAME
    ):
        raise RecoverySnapshotError("recovery publication paths are not canonical siblings")
    _safe_directory(root, label="recorded recovery probe root")
    _safe_directory(parent, label="recorded recovery probe parent")
    _safe_directory(destination, label="recorded recovery destination")
    try:
        parent_names = {entry.name for entry in parent.iterdir()}
        destination_names = {entry.name for entry in destination.iterdir()}
    except OSError as exc:
        raise RecoverySnapshotError(
            f"cannot enumerate retained recovery publication probe: {exc}"
        ) from exc
    if (
        parent_names != {_PREFLIGHT_DESTINATION_NAME}
        or destination_names != {_PREFLIGHT_SENTINEL_NAME}
    ):
        raise RecoverySnapshotError(
            "retained recovery publication probe contains unexpected paths"
        )
    try:
        os.lstat(source)
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise RecoverySnapshotError(
            f"cannot recheck absent recovery source {source}: {exc}"
        ) from exc
    else:
        raise RecoverySnapshotError(
            "recovery publication source exists after a reported successful rename"
        )
    _regular_file(sentinel, label="recovery publication sentinel")
    _require_protected_tree(destination)
    parent_metadata = os.lstat(parent)
    destination_metadata = os.lstat(destination)
    sentinel_raw, sentinel_sha256 = _stable_file_bytes(
        sentinel, label="recovery publication sentinel"
    )
    sentinel_metadata = os.lstat(sentinel)
    try:
        expected_payload = bytes.fromhex(sentinel_record["content_hex"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RecoverySnapshotError(
            f"recovery publication sentinel payload is malformed: {exc}"
        ) from None
    if (
        stat.S_IMODE(parent_metadata.st_mode) != 0o555
        or stat.S_IMODE(destination_metadata.st_mode) != 0o555
        or stat.S_IMODE(sentinel_metadata.st_mode) != 0o444
        or _inode_record(parent_metadata) != parent_after_record
        or _inode_record(destination_metadata) != destination_after_record
        or _inode_record(sentinel_metadata) != sentinel_after_record
        or sentinel_raw != expected_payload
        or len(sentinel_raw) != sentinel_record.get("size")
        or sentinel_sha256 != sentinel_record.get("sha256")
    ):
        raise RecoverySnapshotError(
            "live recovery publication differs from its protected report"
        )
    expected_checks = {
        "atomic_no_replace_returned": True,
        "destination_present": True,
        "directory_inode_preserved": (
            destination_before_record["device"] == destination_metadata.st_dev
            and destination_before_record["inode"] == destination_metadata.st_ino
        ),
        "protected_modes": True,
        "same_device": (
            filesystem.get("root_device") == destination_metadata.st_dev
        ),
        "same_parent": True,
        "sentinel_bytes_preserved": True,
        "sentinel_inode_preserved": (
            sentinel_before_record["device"] == sentinel_metadata.st_dev
            and sentinel_before_record["inode"] == sentinel_metadata.st_ino
        ),
        "source_absent": True,
    }
    if checks != expected_checks or not all(expected_checks.values()):
        raise RecoverySnapshotError(
            "recovery publication consistency checks do not all hold"
        )
    return record


def run_recovery_publication_preflight(
    probe_root: Path, *, report_path: Path
) -> dict[str, object]:
    """Prove atomic recovery publication on the caller's exact filesystem.

    The caller supplies an existing directory on the target filesystem and an
    absent report pathname.  The function creates a random exclusive probe
    parent, publishes a protected sentinel directory with the production
    no-replace primitive, and leaves the complete probe behind.  It never
    deletes or replaces a path, including after a failure.
    """

    root = _absolute_path(probe_root, label="recovery probe root")
    report = _absolute_path(report_path, label="recovery probe report")
    _safe_directory(root, label="recovery probe root")
    _safe_directory(report.parent, label="recovery probe report parent")
    _require_absent(report, label="recovery publication report")
    mechanism = _publication_mechanism()
    root_metadata = os.lstat(root)
    root_statvfs = _statvfs_record(root)
    parent = _new_probe_parent(root)
    source = parent / _PREFLIGHT_SOURCE_NAME
    destination = parent / _PREFLIGHT_DESTINATION_NAME
    sentinel = source / _PREFLIGHT_SENTINEL_NAME
    payload = secrets.token_bytes(_PREFLIGHT_SENTINEL_BYTES)

    try:
        source.mkdir(mode=0o700, exist_ok=False)
        os.chmod(source, 0o700, follow_symlinks=False)
        _require_absent(destination, label="recovery probe destination")
        _write_probe_sentinel(sentinel, payload)
        os.chmod(sentinel, 0o444, follow_symlinks=False)
        os.chmod(source, 0o555, follow_symlinks=False)
        _fsync_tree(source)
        _fsync_directory(parent)
        _fsync_directory(root)
        _require_protected_tree(source)

        source_before = os.lstat(source)
        sentinel_before = os.lstat(sentinel)
        stable_payload, stable_sha256 = _stable_file_bytes(
            sentinel, label="recovery probe sentinel"
        )
        if stable_payload != payload:
            raise RecoverySnapshotError(
                "recovery probe sentinel bytes changed before publication"
            )
        _require_absent(destination, label="recovery probe destination")

        # Match the production macOS compatibility path while keeping every
        # payload protected.  Linux renames the already read-only directory.
        if sys.platform == "darwin":
            os.chmod(source, 0o700, follow_symlinks=False)
        try:
            _rename_noreplace(source, destination)
        except (OSError, RecoverySnapshotError) as exc:
            _restore_failed_probe_source(
                source,
                expected_device=source_before.st_dev,
                expected_inode=source_before.st_ino,
            )
            raise RecoverySnapshotError(
                "atomic no-replace recovery probe failed; evidence was retained "
                f"at {parent}: {exc}"
            ) from exc
        if sys.platform == "darwin":
            os.chmod(destination, 0o555, follow_symlinks=False)

        try:
            os.lstat(source)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise RecoverySnapshotError(
                f"cannot verify disappearance of recovery probe source: {exc}"
            ) from exc
        else:
            raise RecoverySnapshotError(
                "recovery probe source still exists after no-replace rename"
            )
        _safe_directory(destination, label="recovery probe destination")
        _require_protected_tree(destination)
        destination_after = os.lstat(destination)
        destination_sentinel = destination / _PREFLIGHT_SENTINEL_NAME
        destination_payload, destination_sha256 = _stable_file_bytes(
            destination_sentinel, label="published recovery probe sentinel"
        )
        sentinel_after = os.lstat(destination_sentinel)
        if (
            (source_before.st_dev, source_before.st_ino)
            != (destination_after.st_dev, destination_after.st_ino)
            or (sentinel_before.st_dev, sentinel_before.st_ino)
            != (sentinel_after.st_dev, sentinel_after.st_ino)
            or destination_payload != stable_payload
            or destination_sha256 != stable_sha256
            or stat.S_IMODE(destination_after.st_mode) != 0o555
            or stat.S_IMODE(sentinel_after.st_mode) != 0o444
        ):
            raise RecoverySnapshotError(
                "recovery probe bytes, modes, or inodes changed during publication"
            )
        _fsync_tree(destination)
        _fsync_directory(parent)
        _fsync_directory(root)
        os.chmod(parent, 0o555, follow_symlinks=False)
        _fsync_directory(parent)
        _fsync_directory(root)
        parent_after = os.lstat(parent)
        if stat.S_IMODE(parent_after.st_mode) != 0o555:
            raise RecoverySnapshotError(
                "recovery probe parent did not acquire protected mode"
            )

        record: dict[str, object] = {
            "format": RECOVERY_PUBLICATION_PREFLIGHT_FORMAT,
            "v": RECOVERY_PUBLICATION_PREFLIGHT_VERSION,
            "status": "passed",
            "report": {
                "path": str(report),
                "encoding": "utf-8",
                "canonical_json": "sorted-keys-compact-lf",
                "exclusive_create": True,
                "mode": "0o444",
            },
            "platform": {
                "os_name": os.name,
                "sys_platform": sys.platform,
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "filesystem_encoding": sys.getfilesystemencoding(),
                "pointer_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
            },
            "mechanism": mechanism,
            "filesystem": {
                "root": str(root),
                "root_device": root_metadata.st_dev,
                "publication_device": destination_after.st_dev,
                "same_device": root_metadata.st_dev == destination_after.st_dev,
                "statvfs": root_statvfs,
            },
            "publication": {
                "probe_parent": {
                    "path": str(parent),
                    "exclusive_mkdir": True,
                    "unpredictable_bits": 128,
                    "after": _inode_record(parent_after),
                },
                "source": {
                    "path": str(source),
                    "exclusive_mkdir": True,
                    "absent_after": True,
                },
                "destination": {
                    "path": str(destination),
                    "guaranteed_absent_before": True,
                    "present_after": True,
                    "before": _inode_record(source_before),
                    "after": _inode_record(destination_after),
                },
                "sentinel": {
                    "path": str(destination_sentinel),
                    "exclusive_create": True,
                    "content_hex": payload.hex(),
                    "size": len(payload),
                    "sha256": stable_sha256,
                    "before": _inode_record(sentinel_before),
                    "after": _inode_record(sentinel_after),
                },
                "checks": {
                    "atomic_no_replace_returned": True,
                    "destination_present": True,
                    "directory_inode_preserved": True,
                    "protected_modes": True,
                    "same_device": root_metadata.st_dev == destination_after.st_dev,
                    "same_parent": True,
                    "sentinel_bytes_preserved": True,
                    "sentinel_inode_preserved": True,
                    "source_absent": True,
                },
            },
        }
        if root_metadata.st_dev != destination_after.st_dev:
            raise RecoverySnapshotError(
                "recovery probe publication crossed filesystem devices"
            )
        _write_new_canonical_report(report, record)
        return _strict_preflight_record(report, require_live_publication=True)
    except RecoverySnapshotError:
        raise
    except (OSError, ValueError) as exc:
        raise RecoverySnapshotError(
            "recovery publication preflight failed; probe evidence was retained "
            f"at {parent}: {exc}"
        ) from exc


def verify_recovery_publication_preflight(
    report_path: Path,
) -> dict[str, object]:
    """Recheck canonical report bytes and the live, retained publication probe."""

    report = _absolute_path(report_path, label="recovery probe report")
    return _strict_preflight_record(report, require_live_publication=True)


def _require_protected_tree(root: Path) -> None:
    """Require exact protected modes and ordinary single-link snapshot nodes."""

    seen_inodes: set[tuple[int, int]] = set()
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for path in [current_path, *(current_path / name for name in directories)]:
            metadata = os.lstat(path)
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise RecoverySnapshotError("recovery tree contains an unsafe directory")
            if stat.S_IMODE(metadata.st_mode) != 0o555:
                raise RecoverySnapshotError(
                    "recovery directories must have exact protected mode 0555"
                )
        for name in files:
            path = current_path / name
            metadata = os.lstat(path)
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
            ):
                raise RecoverySnapshotError("recovery tree contains an unsafe file")
            inode = (metadata.st_dev, metadata.st_ino)
            if inode in seen_inodes:
                raise RecoverySnapshotError(
                    "recovery tree contains hard-linked artifact aliases"
                )
            seen_inodes.add(inode)
            if stat.S_IMODE(metadata.st_mode) != 0o444:
                raise RecoverySnapshotError(
                    "recovery files must have exact protected mode 0444"
                )


class AdapterRecoverySnapshotter:
    """Write manifest-last LoRA snapshots at predeclared optimizer steps."""

    def __init__(
        self,
        *,
        output_dir: Path,
        run_identity_path: Path,
        run_identity_sha256: str,
        run_identity: Mapping[str, object],
        expected_optimizer_steps: int,
    ) -> None:
        if _SHA256_RE.fullmatch(run_identity_sha256) is None:
            raise ValueError("recovery run identity needs one SHA-256 digest")
        _safe_directory(output_dir, label="training output")
        _regular_file(run_identity_path, label="run identity")
        if run_identity_path.parent.resolve() != output_dir.resolve():
            raise ValueError("recovery run identity must be inside the training output")
        identity_raw, identity_digest = _stable_file_bytes(
            run_identity_path, label="run identity"
        )
        if identity_digest != run_identity_sha256:
            raise ValueError("recovery run identity bytes do not match their digest")

        detached = _detached_json(run_identity, label="run identity")
        if type(detached) is not dict:
            raise ValueError("recovery run identity must be a JSON object")
        if _strict_json_bytes(
            identity_raw, location=str(run_identity_path)
        ) != detached:
            raise ValueError("recovery run identity object differs from its bytes")
        source = detached.get("source")
        job = detached.get("job")
        if (
            type(source) is not dict
            or _SHA256_RE.fullmatch(str(source.get("sha256", ""))) is None
            or type(job) is not dict
        ):
            raise ValueError("recovery run identity lacks source or job evidence")
        plan = recovery_snapshot_plan(expected_optimizer_steps)

        recovery_root = output_dir / RECOVERY_DIRECTORY
        try:
            recovery_root.mkdir(mode=0o700, exist_ok=False)
        except FileExistsError:
            _safe_directory(recovery_root, label="recovery root")
        except OSError as exc:
            raise RecoverySnapshotError(
                f"cannot create recovery root {recovery_root}: {exc}"
            ) from exc

        self.output_dir = output_dir
        self.run_identity_path = run_identity_path
        self.run_identity_sha256 = run_identity_sha256
        self.run_identity = detached
        self.source = source
        self.job = job
        self.job_label = _job_label(job)
        self.plan = plan
        self.expected_optimizer_steps = expected_optimizer_steps
        self.recovery_root = recovery_root
        self.planned_steps = frozenset(plan["planned_optimizer_steps"])
        self._published_steps: set[int] = set()

    def maybe_save(self, model: Any, *, global_step: int) -> Path | None:
        """Publish a planned snapshot once; return its directory when written."""

        if type(global_step) is not int or global_step < 0:
            raise ValueError("recovery snapshot step must be a non-negative integer")
        if global_step not in self.planned_steps:
            return None
        if global_step in self._published_steps:
            return None
        identity_before = _stable_file_digest(
            self.run_identity_path, label="run identity"
        )
        if identity_before != self.run_identity_sha256:
            raise RecoverySnapshotError(
                "run identity changed before a recovery snapshot"
            )
        if not hasattr(model, "save_pretrained"):
            raise TypeError("recovery model does not expose save_pretrained")

        name = _snapshot_name(
            global_step, self.run_identity_sha256, self.job_label
        )
        snapshot = self.recovery_root / name
        try:
            os.lstat(snapshot)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise RecoverySnapshotError(
                f"cannot inspect recovery destination {snapshot}: {exc}"
            ) from exc
        else:
            raise RecoverySnapshotError(
                f"refusing to replace existing recovery snapshot {snapshot}"
            )
        try:
            staging = Path(
                tempfile.mkdtemp(
                    prefix=f".{name}.partial-", dir=self.recovery_root
                )
            )
        except OSError as exc:
            raise RecoverySnapshotError(
                f"cannot create recovery staging directory: {exc}"
            ) from exc

        adapter = staging / "adapter"
        # PEFT's safe serializer writes only inference-time adapter artifacts.
        # Any failure intentionally leaves a manifest-less partial directory;
        # it is evidence of an interrupted save and is never removed here.
        model.save_pretrained(adapter, safe_serialization=True)
        identity_after = _stable_file_digest(
            self.run_identity_path, label="run identity"
        )
        if identity_after != identity_before:
            raise RecoverySnapshotError(
                "run identity changed during a recovery snapshot"
            )
        if {entry.name for entry in staging.iterdir()} != {"adapter"}:
            raise RecoverySnapshotError(
                "adapter save wrote outside its recovery artifact directory"
            )
        artifacts = artifact_directory_hash(staging, "adapter")
        require_safetensors_adapter(artifacts, "adapter")

        manifest = {
            "format": RECOVERY_FORMAT,
            "v": RECOVERY_VERSION,
            "status": "partial-training-recovery",
            "training_complete": False,
            "eligible_as_training_result": False,
            "resumable": False,
            "optimizer_state_included": False,
            "global_step": global_step,
            "expected_optimizer_steps": self.expected_optimizer_steps,
            "plan": self.plan,
            "authority": {
                "run_identity_path": str(self.run_identity_path),
                "run_identity_sha256": self.run_identity_sha256,
                "source": self.source,
                "source_sha256": self.source["sha256"],
                "job": self.job,
                "job_sha256": sha256_json(self.job),
            },
            "adapter": artifacts,
        }
        # The manifest is the last payload written, but a staging name remains
        # invalid authority until the whole tree is flushed, protected,
        # verified, and installed with an OS-level no-replace rename.
        _write_new_manifest(staging / RECOVERY_MANIFEST, manifest)
        _fsync_tree(staging)
        _protect_tree(staging)
        _fsync_tree(staging)
        _verify_recovery_snapshot_record(
            staging,
            run_identity_path=self.run_identity_path,
            expected_optimizer_steps=self.expected_optimizer_steps,
            expected_global_step=global_step,
            require_canonical_name=False,
        )
        # macOS renamex_np(RENAME_EXCL) rejects a read-only source directory.
        # Only the staging root is briefly owner-writable; every payload and
        # child directory remains protected throughout publication.
        if sys.platform == "darwin":
            os.chmod(staging, 0o700, follow_symlinks=False)
        try:
            _rename_noreplace(staging, snapshot)
        except FileExistsError as exc:
            raise RecoverySnapshotError(str(exc)) from exc
        if sys.platform == "darwin":
            os.chmod(snapshot, 0o555, follow_symlinks=False)
        _fsync_directory(snapshot)
        _fsync_directory(self.recovery_root)
        verify_recovery_snapshot(
            snapshot,
            run_identity_path=self.run_identity_path,
            expected_optimizer_steps=self.expected_optimizer_steps,
            expected_global_step=global_step,
        )
        self._published_steps.add(global_step)
        return snapshot


class AdapterRecoveryCallbackMixin:
    """Transformers callback behavior without importing Transformers at import time."""

    def __init__(self, snapshotter: AdapterRecoverySnapshotter) -> None:
        self.snapshotter = snapshotter

    def on_step_end(
        self,
        args: object,
        state: object,
        control: object,
        **kwargs: object,
    ) -> object:
        del args
        if getattr(state, "is_world_process_zero", None) is not True:
            raise RecoverySnapshotError(
                "adapter recovery requires the audited one-process trainer"
            )
        step = getattr(state, "global_step", None)
        if type(step) is not int:
            raise RecoverySnapshotError("Trainer callback has no integer global_step")
        model = kwargs.get("model")
        if model is None:
            raise RecoverySnapshotError("Trainer callback did not provide its model")
        self.snapshotter.maybe_save(model, global_step=step)
        return control


def _verify_recovery_snapshot_record(
    snapshot: Path,
    *,
    run_identity_path: Path,
    expected_optimizer_steps: int,
    expected_global_step: int | None = None,
    require_canonical_name: bool,
) -> dict[str, object]:
    """Verify a staged or published snapshot against external run authority."""

    _safe_directory(snapshot, label="recovery snapshot")
    names = {entry.name for entry in snapshot.iterdir()}
    if names != {"adapter", RECOVERY_MANIFEST}:
        raise RecoverySnapshotError(
            "recovery snapshot is partial or contains unexpected artifacts"
        )
    _require_protected_tree(snapshot)
    manifest_path = snapshot / RECOVERY_MANIFEST
    _regular_file(manifest_path, label="recovery manifest")
    record = _strict_json(manifest_path)
    required = {
        "format",
        "v",
        "status",
        "training_complete",
        "eligible_as_training_result",
        "resumable",
        "optimizer_state_included",
        "global_step",
        "expected_optimizer_steps",
        "plan",
        "authority",
        "adapter",
    }
    if type(record) is not dict or set(record) != required:
        raise RecoverySnapshotError("recovery manifest has an incompatible shape")
    if (
        record.get("format") != RECOVERY_FORMAT
        or record.get("v") != RECOVERY_VERSION
        or record.get("status") != "partial-training-recovery"
        or record.get("training_complete") is not False
        or record.get("eligible_as_training_result") is not False
        or record.get("resumable") is not False
        or record.get("optimizer_state_included") is not False
    ):
        raise RecoverySnapshotError(
            "recovery snapshot falsely claims completion or resume capability"
        )
    step = record.get("global_step")
    if type(step) is not int or step < 1:
        raise RecoverySnapshotError("recovery snapshot has an invalid optimizer step")
    if expected_global_step is not None and step != expected_global_step:
        raise RecoverySnapshotError("recovery snapshot has an unexpected optimizer step")
    plan = recovery_snapshot_plan(expected_optimizer_steps)
    if (
        record.get("expected_optimizer_steps") != expected_optimizer_steps
        or record.get("plan") != plan
        or step not in plan["planned_optimizer_steps"]
    ):
        raise RecoverySnapshotError("recovery snapshot differs from its planned schedule")

    _regular_file(run_identity_path, label="external run identity")
    run_raw, run_digest = _stable_file_bytes(
        run_identity_path, label="external run identity"
    )
    run_identity = _strict_json_bytes(run_raw, location=str(run_identity_path))
    authority = record.get("authority")
    if type(run_identity) is not dict or type(authority) is not dict:
        raise RecoverySnapshotError("recovery authority is malformed")
    source = run_identity.get("source")
    job = run_identity.get("job")
    if type(source) is not dict or type(job) is not dict:
        raise RecoverySnapshotError("external run identity lacks source or job evidence")
    if authority != {
        "run_identity_path": str(run_identity_path),
        "run_identity_sha256": run_digest,
        "source": source,
        "source_sha256": source.get("sha256"),
        "job": job,
        "job_sha256": sha256_json(job),
    }:
        raise RecoverySnapshotError("recovery authority differs from the run identity")
    expected_name = _snapshot_name(step, run_digest, _job_label(job))
    if require_canonical_name and snapshot.name != expected_name:
        raise RecoverySnapshotError("recovery directory name differs from its authority")

    adapter = record.get("adapter")
    if type(adapter) is not dict:
        raise RecoverySnapshotError("recovery adapter record is malformed")
    verify_artifact_directory(
        snapshot,
        adapter,
        "adapter",
        require_protected=True,
    )
    require_safetensors_adapter(adapter, "adapter")
    return record


def verify_recovery_snapshot(
    snapshot: Path,
    *,
    run_identity_path: Path,
    expected_optimizer_steps: int,
    expected_global_step: int | None = None,
) -> dict[str, object]:
    """Verify one protected, canonically named snapshot against run authority."""

    return _verify_recovery_snapshot_record(
        snapshot,
        run_identity_path=run_identity_path,
        expected_optimizer_steps=expected_optimizer_steps,
        expected_global_step=expected_global_step,
        require_canonical_name=True,
    )


__all__ = [
    "AdapterRecoveryCallbackMixin",
    "AdapterRecoverySnapshotter",
    "RECOVERY_DIRECTORY",
    "RECOVERY_FORMAT",
    "RECOVERY_MANIFEST",
    "RECOVERY_PUBLICATION_PREFLIGHT_FORMAT",
    "RECOVERY_PUBLICATION_PREFLIGHT_VERSION",
    "RECOVERY_VERSION",
    "RecoverySnapshotError",
    "recovery_snapshot_plan",
    "run_recovery_publication_preflight",
    "verify_recovery_publication_preflight",
    "verify_recovery_snapshot",
]
