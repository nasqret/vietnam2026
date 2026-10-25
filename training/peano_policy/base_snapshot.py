"""Close the exact loader-visible bytes of the pinned Qwen base snapshot."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re

from .manifest import sha256_file, sha256_json


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RECORD_PATH = Path(__file__).with_name("base-model-snapshot-v1.json")
RECORD_FORMAT = "peano-policy-base-model-snapshot"
RECORD_VERSION = 1
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_MODEL_ID_RE = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _record(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("base snapshot record must be one object")
    files = value.get("files")
    if type(files) is not dict:
        raise ValueError("base snapshot record has no file map")
    if (
        set(value)
        != {
            "algorithm",
            "file_count",
            "files",
            "format",
            "model_id",
            "revision",
            "sha256",
            "total_bytes",
            "v",
        }
        or value.get("format") != RECORD_FORMAT
        or value.get("v") != RECORD_VERSION
        or value.get("algorithm")
        != "sha256-json-v1(logical-path-to-size-and-sha256)"
        or type(value.get("model_id")) is not str
        or _MODEL_ID_RE.fullmatch(value["model_id"]) is None
        or type(value.get("revision")) is not str
        or _COMMIT_RE.fullmatch(value["revision"]) is None
        or type(value.get("file_count")) is not int
        or not files
        or value.get("file_count") != len(files)
        or type(value.get("sha256")) is not str
        or value.get("sha256") != sha256_json(files)
        or type(value.get("total_bytes")) is not int
    ):
        raise ValueError("base snapshot record has a forged aggregate identity")
    total_bytes = 0
    for relative, raw in files.items():
        path = Path(relative) if type(relative) is str else Path("/")
        if (
            type(relative) is not str
            or not relative
            or path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != relative
            or type(raw) is not dict
            or set(raw) != {"size", "sha256"}
            or type(raw.get("size")) is not int
            or int(raw["size"]) < 0
            or type(raw.get("sha256")) is not str
            or _SHA256_RE.fullmatch(raw["sha256"]) is None
        ):
            raise ValueError("base snapshot record contains an unsafe file identity")
        total_bytes += int(raw["size"])
    if value.get("total_bytes") != total_bytes:
        raise ValueError("base snapshot byte total is forged")
    return value


def expected_base_snapshot() -> dict[str, object]:
    if EXPECTED_RECORD_PATH.is_symlink() or not EXPECTED_RECORD_PATH.is_file():
        raise ValueError("base snapshot authority is not a regular file")
    try:
        value = json.loads(
            EXPECTED_RECORD_PATH.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot read base snapshot authority: {exc}") from None
    return _record(value)


def current_base_snapshot(
    *,
    model_id: str,
    revision: str,
    hf_home: Path | None = None,
) -> dict[str, object]:
    if _MODEL_ID_RE.fullmatch(model_id) is None:
        raise ValueError("base model id is not one owner/name pair")
    if _COMMIT_RE.fullmatch(revision) is None:
        raise ValueError("base model revision is not one commit")
    if hf_home is None:
        home_text = os.environ.get("HF_HOME")
        if not home_text:
            raise ValueError("HF_HOME is required for base snapshot validation")
        home = Path(home_text)
    else:
        home = Path(hf_home)
    model_root = home / "hub" / f"models--{model_id.replace('/', '--')}"
    blobs = model_root / "blobs"
    snapshots = model_root / "snapshots"
    snapshot = snapshots / revision
    for path, label in (
        (home, "HF_HOME"),
        (model_root, "base model cache"),
        (blobs, "base model blobs"),
        (snapshots, "base model snapshots"),
        (snapshot, "pinned base model snapshot"),
    ):
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"{label} is not one plain directory")
    blobs_root = blobs.resolve(strict=True)
    files: dict[str, dict[str, object]] = {}
    try:
        entries = sorted(snapshot.rglob("*"), key=lambda path: path.as_posix())
    except OSError as exc:
        raise ValueError(f"cannot enumerate pinned base snapshot: {exc}") from None
    for entry in entries:
        relative = entry.relative_to(snapshot).as_posix()
        if entry.is_dir():
            raise ValueError("base snapshot contains an unexpected directory")
        try:
            resolved = entry.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(
                f"base snapshot entry {relative} cannot be resolved: {exc}"
            ) from None
        if entry.is_symlink():
            try:
                target = os.readlink(entry)
            except OSError as exc:
                raise ValueError(
                    f"cannot read base snapshot link {relative}: {exc}"
                ) from None
            if Path(target).is_absolute() or not resolved.is_relative_to(blobs_root):
                raise ValueError(
                    f"base snapshot entry {relative} is not a safe relative blob link"
                )
        elif not entry.is_file() or resolved != entry.absolute():
            raise ValueError(
                f"base snapshot entry {relative} is not one plain regular file"
            )
        if not resolved.is_file():
            raise ValueError(f"base snapshot entry {relative} is not a regular file")
        try:
            size = resolved.stat().st_size
        except OSError as exc:
            raise ValueError(f"cannot stat base snapshot entry {relative}: {exc}") from None
        files[relative] = {"size": size, "sha256": sha256_file(resolved)}
    if not files:
        raise ValueError("pinned base model snapshot is empty")
    return {
        "algorithm": "sha256-json-v1(logical-path-to-size-and-sha256)",
        "file_count": len(files),
        "files": files,
        "format": RECORD_FORMAT,
        "model_id": model_id,
        "revision": revision,
        "sha256": sha256_json(files),
        "total_bytes": sum(int(item["size"]) for item in files.values()),
        "v": RECORD_VERSION,
    }


def validate_base_snapshot(
    *,
    model_id: str,
    revision: str,
    hf_home: Path | None = None,
) -> dict[str, object]:
    expected = expected_base_snapshot()
    if model_id != expected.get("model_id") or revision != expected.get("revision"):
        raise ValueError("requested base model has no matching snapshot authority")
    current = current_base_snapshot(
        model_id=model_id,
        revision=revision,
        hf_home=hf_home,
    )
    if current != expected:
        raise ValueError("loader-visible base model snapshot differs from authority")
    return current


def validated_snapshot_path(
    *,
    model_id: str,
    revision: str,
    hf_home: Path | None = None,
) -> tuple[Path, dict[str, object]]:
    identity = validate_base_snapshot(
        model_id=model_id,
        revision=revision,
        hf_home=hf_home,
    )
    if hf_home is None:
        home_text = os.environ.get("HF_HOME")
        if not home_text:  # pragma: no cover - already rejected by validation
            raise ValueError("HF_HOME is required for base snapshot validation")
        home = Path(home_text)
    else:
        home = Path(hf_home)
    path = (
        home
        / "hub"
        / f"models--{model_id.replace('/', '--')}"
        / "snapshots"
        / revision
    )
    return path.resolve(strict=True), identity


def authority_identity() -> dict[str, object]:
    expected = expected_base_snapshot()
    return {
        "path": EXPECTED_RECORD_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "record_sha256": sha256_file(EXPECTED_RECORD_PATH),
        "file_count": expected["file_count"],
        "total_bytes": expected["total_bytes"],
        "snapshot_sha256": expected["sha256"],
    }


__all__ = [
    "EXPECTED_RECORD_PATH",
    "authority_identity",
    "current_base_snapshot",
    "expected_base_snapshot",
    "validate_base_snapshot",
    "validated_snapshot_path",
]
