"""Exact ancillary data for the two retained Alpha-v28 native hotspots.

These raw seals identify historical, self-contained ordinary proof bundles.
Checking their bytes is input preflight, never kernel verification or a new
proof receipt. The unchanged public loaders still decode and check the actual
bodies in each bounded fresh worker. No path override or source setter is used.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from .cold_replay_v28 import ALPHA_V28_EPOCH, HOTSPOT_NAMES


SCHEMA = "peano-hydra-native-calibration-input-closure-v28-v1"
MODES = ("native-hotspots", "reference-only", "full-plan-only")
PROOF_FILES = (
    (
        "research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json",
        14_368_763,
        "84078d40d2df7b072938975191fb70c95731059ced716a12050df4376e2d4883",
    ),
    (
        "research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json",
        2_518_315,
        "cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11",
    ),
)
MAX_FILE_BYTES = 16 * 1024**2
MAX_TOTAL_BYTES = 16_887_078
ALTERNATE_DIRECTORY = Path("/lab/proof-artifacts")
_STAT_FIELDS = (
    "st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns",
)


class ReviewInputError(ValueError):
    """A native calibration input is missing, changed, or outside its closure."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def ancillary_input_closure(mode: str) -> dict[str, object]:
    """Return fixed declarations without reading or verifying any proof data."""
    if type(mode) is not str or mode not in MODES:
        raise ReviewInputError("unknown v28 ancillary-input mode")
    files = {name: {"bytes": size, "sha256": sha}
             for name, size, sha in PROOF_FILES} if mode == "native-hotspots" else {}
    record = {
        "schema": SCHEMA, "mode": mode, "epoch_sha256": ALPHA_V28_EPOCH,
        "target_names": list(HOTSPOT_NAMES) if files else [],
        "loader_policy": "unchanged-default-repository-relative-paths",
        "files": files, "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files.values()),
        "external_provenance_files": [], "kernel_checked": False,
    }
    record["input_closure_sha256"] = hashlib.sha256(_canonical(record)).hexdigest()
    return record


def validate_ancillary_inputs(record: object, *, mode: str) -> None:
    """Pure exact metadata validation, including re-sealed input mutations."""
    if type(record) is not dict or _canonical(record) != _canonical(ancillary_input_closure(mode)):
        raise ReviewInputError("v28 ancillary input closure differs from the exact historical data")


def _open_input(root: Path, relative: str) -> int:
    # Walk all ancestors, including those above the execution root. O_PATH on
    # Linux permits search-only scratch ancestors without requiring listing.
    flags = getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open("/", flags)
    try:
        for part in (*root.parts[1:], *relative.split("/")[:-1]):
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return os.open(relative.rsplit("/", 1)[-1],
                       os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
    finally:
        os.close(descriptor)


def _identity(metadata) -> tuple[int, ...]:
    return tuple(getattr(metadata, name) for name in _STAT_FIELDS)


def _check_file(root: Path, relative: str, expected: dict[str, object]) -> tuple[int, ...]:
    descriptor = None
    try:
        descriptor = _open_input(root, relative)
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or not 0 < before.st_size <= MAX_FILE_BYTES or before.st_size != expected["bytes"]):
            raise ReviewInputError(f"ancillary input is not its exact bounded regular file: {relative}")
        sha, length = hashlib.sha256(), 0
        while chunk := os.read(descriptor, min(65536, expected["bytes"] - length + 1)):
            length += len(chunk)
            if length > expected["bytes"]:
                raise ReviewInputError(f"ancillary input grew past its exact byte reservation: {relative}")
            sha.update(chunk)
        after = os.fstat(descriptor)
        fresh = _open_input(root, relative)
        try:
            current = os.fstat(fresh)
        finally:
            os.close(fresh)
        if (_identity(before) != _identity(after) or _identity(before) != _identity(current)
            or length != expected["bytes"] or sha.hexdigest() != expected["sha256"]):
            raise ReviewInputError(f"ancillary input bytes or file identity changed: {relative}")
        return _identity(before)
    except OSError as error:
        raise ReviewInputError(f"ancillary input is missing, inaccessible, or uses a symlink: {relative}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def check_ancillary_inputs(record: object, *, mode: str, root: Path) -> dict[str, tuple[int, ...]]:
    """Stream fixed raw bytes and reject aliases before any native replay.

    The returned local file identities allow the same process to detect drift
    across its worker(s). They are observations, not portable proof authority.
    Planning and archived metadata validation use validate_ancillary_inputs and
    do not require these historical bytes to be present.
    """
    validate_ancillary_inputs(record, mode=mode)
    if not record["files"]:
        return {}
    if (not isinstance(root, Path) or not root.is_absolute()
        or any(part in {".", ".."} for part in root.parts)):
        raise ReviewInputError("ancillary inputs require the explicit absolute execution root")
    if record["total_bytes"] > MAX_TOTAL_BYTES:
        raise ReviewInputError("ancillary closure exceeds its exact total byte reservation")
    observed = {}
    for relative, expected in record["files"].items():
        # These legacy /lab alternatives take precedence in the original
        # providers. A pinned repository copy must never silently lose to one.
        if os.path.lexists(ALTERNATE_DIRECTORY / Path(relative).name):
            raise ReviewInputError("a legacy /lab proof source shadows the pinned repository input")
        observed[relative] = _check_file(root, relative, expected)
    return observed
