"""Immutable, path-bound publication for one checked model-v3 corpus.

The preparation job writes a directory of twelve data artifacts and three
independent reports.  Training must never consume a hand-picked subset of
those files, nor a mixture of reports from different Slurm jobs.  This module
copies the closed set into a new sibling staging directory, validates all JSON
strictly, joins the hashes and runtime identities, and publishes the result
with an operating-system no-replace rename.

The seal is an integrity envelope, not a signature.  A verifier that needs an
external trust anchor should pass the expected source commit and preparation
job id to :func:`verify_seal`.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence


SEAL_FORMAT = "peano-policy-v3-corpus-seal"
SEAL_VERSION = 1
SEAL_MANIFEST = "seal.json"

DATA_FILES = (
    "balanced-raw-traces.jsonl",
    "balanced-session-metadata.jsonl",
    "balanced-source-manifest.json",
    "combined-metadata-manifest.json",
    "library-raw-traces.jsonl",
    "library-session-metadata.jsonl",
    "library-source-manifest.json",
    "manifest.json",
    "session-metadata.jsonl",
    "test.jsonl",
    "train.jsonl",
    "val.jsonl",
)
REPORT_FILES = {
    "dataset_attestation": "dataset-attestation.json",
    "token_audit": "token-audit.json",
    "runtime_smoke": "runtime-smoke.json",
}

EXPECTED_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
EXPECTED_MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
EXPECTED_LIBRARY_SIZE = 247
EXPECTED_TOKEN_BUDGET = 32_768
EXPECTED_PREPARE_SCRIPT = "slurm/peano_wmi_prepare_v3_training.sbatch"

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_JOB_ID_RE = re.compile(r"[0-9]+")
_MAX_JSON_BYTES = 64 * 1024 * 1024
_MAX_JSONL_LINE_BYTES = 64 * 1024 * 1024
_COPY_CHUNK_BYTES = 1024 * 1024


class CorpusSealError(ValueError):
    """The requested corpus publication is incomplete, mixed, or unsafe."""


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_bytes(value: object) -> bytes:
    return (_canonical_json(value) + "\n").encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _decode_json(raw: bytes, *, location: str) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise CorpusSealError(f"{location}: invalid JSON: {exc}") from exc
    if type(value) is not dict:
        raise CorpusSealError(f"{location}: expected one JSON object")
    return value


def _control_free(value: str) -> bool:
    return bool(value) and not any(ord(character) < 32 or ord(character) == 127 for character in value)


def _safe_absolute_path(value: str | os.PathLike[str], label: str) -> Path:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise CorpusSealError(f"{label}: path is not filesystem text") from exc
    if type(raw) is not str or not _control_free(raw):
        raise CorpusSealError(f"{label}: path contains empty or control text")
    lexical = Path(raw)
    if ".." in lexical.parts:
        raise CorpusSealError(f"{label}: parent traversal is forbidden")
    if not lexical.is_absolute():
        lexical = Path.cwd() / lexical
    return lexical


def _reject_symlink_components(
    path: Path,
    label: str,
    *,
    allow_missing_leaf: bool = False,
) -> None:
    if not path.is_absolute():  # pragma: no cover - internal invariant
        raise AssertionError("component walk requires an absolute path")
    current = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current /= part
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            if allow_missing_leaf and index == len(parts) - 1:
                return
            raise CorpusSealError(f"{label}: path component is missing: {current}")
        except OSError as exc:
            raise CorpusSealError(f"{label}: cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise CorpusSealError(f"{label}: symlinked path component is forbidden: {current}")


def _regular_lstat(path: Path, label: str) -> os.stat_result:
    try:
        metadata = os.lstat(path)
    except OSError as exc:
        raise CorpusSealError(f"{label}: cannot inspect regular file: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CorpusSealError(f"{label}: expected one non-symlink regular file")
    return metadata


def _open_regular(path: Path, label: str) -> tuple[int, os.stat_result]:
    before = _regular_lstat(path, label)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CorpusSealError(f"{label}: cannot open regular file: {exc}") from exc
    opened = os.fstat(descriptor)
    if (
        not stat.S_ISREG(opened.st_mode)
        or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
    ):
        os.close(descriptor)
        raise CorpusSealError(f"{label}: file changed while it was opened")
    return descriptor, opened


def _require_stable_read(
    path: Path,
    *,
    label: str,
    opened: os.stat_result,
    after: os.stat_result,
) -> None:
    """Reject replacement or in-place mutation during an open-file read."""

    try:
        current = os.lstat(path)
    except OSError as exc:
        raise CorpusSealError(f"{label}: file disappeared during read") from exc
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(opened, field) != getattr(after, field) for field in stable_fields) or any(
        getattr(opened, field) != getattr(current, field) for field in stable_fields
    ):
        raise CorpusSealError(f"{label}: file changed while it was read")


def _read_regular_bytes(path: Path, label: str, *, limit: int) -> bytes:
    descriptor, opened = _open_regular(path, label)
    if opened.st_size > limit:
        os.close(descriptor)
        raise CorpusSealError(f"{label}: file exceeds the {limit}-byte safety limit")
    try:
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise CorpusSealError(f"{label}: cannot read regular file: {exc}") from exc
    if len(raw) > limit:
        raise CorpusSealError(f"{label}: file exceeds the {limit}-byte safety limit")
    _require_stable_read(path, label=label, opened=opened, after=after)
    return raw


def _load_json_object(path: Path, label: str) -> tuple[dict[str, object], bytes]:
    raw = _read_regular_bytes(path, label, limit=_MAX_JSON_BYTES)
    return _decode_json(raw, location=label), raw


def _load_jsonl(path: Path, label: str) -> int:
    descriptor, opened = _open_regular(path, label)
    count = 0
    try:
        with os.fdopen(descriptor, "rb") as stream:
            while True:
                raw = stream.readline(_MAX_JSONL_LINE_BYTES + 1)
                if not raw:
                    break
                count += 1
                if len(raw) > _MAX_JSONL_LINE_BYTES:
                    raise CorpusSealError(
                        f"{label}:{count}: JSONL record exceeds the safety limit"
                    )
                if not raw.endswith(b"\n"):
                    raise CorpusSealError(
                        f"{label}:{count}: incomplete JSONL record (missing newline)"
                    )
                if raw == b"\n":
                    raise CorpusSealError(f"{label}:{count}: blank JSONL record")
                _decode_json(raw[:-1], location=f"{label}:{count}")
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise CorpusSealError(f"{label}: cannot stream JSONL: {exc}") from exc
    if count == 0:
        raise CorpusSealError(f"{label}: JSONL file is empty")
    _require_stable_read(path, label=label, opened=opened, after=after)
    return count


def _copy_regular_file(source: Path, target: Path, label: str) -> dict[str, object]:
    source_descriptor, opened = _open_regular(source, label)
    destination_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        target_descriptor = os.open(target, destination_flags, 0o600)
    except OSError:
        os.close(source_descriptor)
        raise

    digest = hashlib.sha256()
    copied = 0
    try:
        with os.fdopen(source_descriptor, "rb") as input_stream, os.fdopen(
            target_descriptor, "wb"
        ) as output_stream:
            while True:
                chunk = input_stream.read(_COPY_CHUNK_BYTES)
                if not chunk:
                    break
                output_stream.write(chunk)
                digest.update(chunk)
                copied += len(chunk)
            output_stream.flush()
            os.fsync(output_stream.fileno())
            after = os.fstat(input_stream.fileno())
    except OSError as exc:
        raise CorpusSealError(f"{label}: copy failed: {exc}") from exc

    try:
        current = os.lstat(source)
    except OSError as exc:
        raise CorpusSealError(f"{label}: source disappeared during copy") from exc
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(opened, field) != getattr(after, field) for field in stable_fields) or (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_ctime_ns,
    ) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
        opened.st_ctime_ns,
    ):
        raise CorpusSealError(f"{label}: source changed while it was copied")
    if copied != opened.st_size:
        raise CorpusSealError(f"{label}: copied byte count changed unexpectedly")
    return {"bytes": copied, "sha256": digest.hexdigest()}


def _hash_regular_file(path: Path, label: str) -> dict[str, object]:
    descriptor, opened = _open_regular(path, label)
    digest = hashlib.sha256()
    copied = 0
    try:
        with os.fdopen(descriptor, "rb") as stream:
            while True:
                chunk = stream.read(_COPY_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
                copied += len(chunk)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise CorpusSealError(f"{label}: cannot hash regular file: {exc}") from exc
    if copied != opened.st_size:
        raise CorpusSealError(f"{label}: file changed while it was hashed")
    _require_stable_read(path, label=label, opened=opened, after=after)
    return {"bytes": copied, "sha256": digest.hexdigest()}


def _file_record(relative: str, measured: Mapping[str, object]) -> dict[str, object]:
    return {
        "path": relative,
        "bytes": measured["bytes"],
        "sha256": measured["sha256"],
    }


def _scan_data_directory(path: Path) -> dict[str, Path]:
    _reject_symlink_components(path, "artifact directory")
    try:
        metadata = os.lstat(path)
    except OSError as exc:
        raise CorpusSealError(f"artifact directory: cannot inspect path: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CorpusSealError("artifact directory must be one non-symlink directory")
    try:
        entries = {entry.name: entry for entry in os.scandir(path)}
    except OSError as exc:
        raise CorpusSealError(f"artifact directory: cannot list entries: {exc}") from exc
    expected = set(DATA_FILES)
    missing = sorted(expected - set(entries))
    unexpected = sorted(set(entries) - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected {', '.join(unexpected)}")
        raise CorpusSealError("artifact directory is not closed: " + "; ".join(details))
    result: dict[str, Path] = {}
    inodes: set[tuple[int, int]] = set()
    for name in DATA_FILES:
        entry = entries[name]
        try:
            entry_stat = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise CorpusSealError(f"artifact {name}: cannot inspect entry: {exc}") from exc
        if entry.is_symlink() or not stat.S_ISREG(entry_stat.st_mode):
            raise CorpusSealError(f"artifact {name}: expected one non-symlink regular file")
        inode = (entry_stat.st_dev, entry_stat.st_ino)
        if inode in inodes:
            raise CorpusSealError(f"artifact {name}: hard-linked artifact aliases are forbidden")
        inodes.add(inode)
        result[name] = path / name
    return result


def _expected_report_source_names(job_id: str) -> dict[str, str]:
    return {
        "dataset_attestation": f"peano-wmi-v3-dataset-attestation-{job_id}.json",
        "token_audit": f"peano-wmi-v3-token-audit-{job_id}.json",
        "runtime_smoke": f"peano-wmi-v3-prepare-runtime-{job_id}.json",
    }


def _prepare_report_paths(
    report_paths: Mapping[str, str | os.PathLike[str]], job_id: str
) -> dict[str, Path]:
    if set(report_paths) != set(REPORT_FILES):
        raise CorpusSealError("exactly the attestation, token audit, and smoke reports are required")
    expected_names = _expected_report_source_names(job_id)
    result: dict[str, Path] = {}
    inodes: set[tuple[int, int]] = set()
    for role in REPORT_FILES:
        path = _safe_absolute_path(report_paths[role], f"{role} report")
        _reject_symlink_components(path, f"{role} report")
        metadata = _regular_lstat(path, f"{role} report")
        if path.name != expected_names[role]:
            raise CorpusSealError(
                f"{role} report: expected source filename {expected_names[role]!r}"
            )
        inode = (metadata.st_dev, metadata.st_ino)
        if inode in inodes:
            raise CorpusSealError("preparation reports must be three distinct files")
        inodes.add(inode)
        result[role] = path
    return result


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise CorpusSealError(f"{label}: expected a JSON object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if type(value) is not list:
        raise CorpusSealError(f"{label}: expected a JSON array")
    return value


def _text(value: object, label: str) -> str:
    if type(value) is not str or not _control_free(value):
        raise CorpusSealError(f"{label}: expected non-empty control-free text")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise CorpusSealError(f"{label}: expected an integer >= {minimum}")
    return value


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise CorpusSealError(f"{label}: expected one lowercase SHA-256")
    return value


def _commit(value: object, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise CorpusSealError(f"{label}: expected one lowercase 40-hex Git commit")
    return value


def _job_id(value: object, label: str) -> str:
    if type(value) is not str or _JOB_ID_RE.fullmatch(value) is None:
        raise CorpusSealError(f"{label}: expected one decimal Slurm job id")
    return value


def _embedded_path_name(value: object, expected: str, label: str) -> None:
    text = _text(value, f"{label}.path")
    path = Path(text)
    if ".." in path.parts or path.name != expected:
        raise CorpusSealError(f"{label}.path: expected an unambiguous reference to {expected}")


def _record_table(records: Sequence[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for record in records:
        path = _text(record.get("path"), "seal file path")
        result[path] = record
    return result


def _match_artifact_record(
    value: object,
    *,
    expected_name: str,
    records: Mapping[str, Mapping[str, object]],
    label: str,
) -> None:
    record = _mapping(value, label)
    _embedded_path_name(record.get("path"), expected_name, label)
    actual = records[f"data/{expected_name}"]
    if _integer(record.get("bytes"), f"{label}.bytes") != actual["bytes"]:
        raise CorpusSealError(f"{label}: byte count differs from sealed artifact")
    if _sha256(record.get("sha256"), f"{label}.sha256") != actual["sha256"]:
        raise CorpusSealError(f"{label}: hash differs from sealed artifact")


def _validate_source_manifests(
    documents: Mapping[str, Mapping[str, object]],
    records: Mapping[str, Mapping[str, object]],
) -> None:
    for stem, expected_format in (
        ("balanced", "peano-policy-corpus"),
        ("library", "peano-library-policy-corpus"),
    ):
        document = documents[f"{stem}-source-manifest.json"]
        if document.get("format") != expected_format or document.get("version") != 1:
            raise CorpusSealError(f"{stem} source manifest has the wrong format/version")
        artifacts = _mapping(document.get("artifacts"), f"{stem} source artifacts")
        _match_artifact_record(
            artifacts.get("trace"),
            expected_name=f"{stem}-raw-traces.jsonl",
            records=records,
            label=f"{stem} source trace",
        )
        _match_artifact_record(
            artifacts.get("metadata"),
            expected_name=f"{stem}-session-metadata.jsonl",
            records=records,
            label=f"{stem} source metadata",
        )
    balanced = documents["balanced-source-manifest.json"]
    authority = _mapping(balanced.get("authority_schedule"), "balanced authority schedule")
    if (
        balanced.get("profile") != "model-v3"
        or authority.get("method") != "full-synthetic-v1"
        or authority.get("library_prefix_length") != EXPECTED_LIBRARY_SIZE
        or authority.get("library_size") != EXPECTED_LIBRARY_SIZE
    ):
        raise CorpusSealError("balanced source manifest is not the full model-v3 authority")
    library = documents["library-source-manifest.json"]
    library_identity = _mapping(library.get("library"), "library source authority")
    if library_identity.get("size") != EXPECTED_LIBRARY_SIZE:
        raise CorpusSealError("library source manifest has the wrong library size")

    combined = documents["combined-metadata-manifest.json"]
    if combined.get("format") != "peano-v3-combined-corpus-metadata" or combined.get("version") != 1:
        raise CorpusSealError("combined metadata manifest has the wrong format/version")
    inputs = _mapping(combined.get("inputs"), "combined metadata inputs")
    _match_artifact_record(
        inputs.get("library_metadata"),
        expected_name="library-session-metadata.jsonl",
        records=records,
        label="combined library metadata",
    )
    _match_artifact_record(
        inputs.get("synthetic_metadata"),
        expected_name="balanced-session-metadata.jsonl",
        records=records,
        label="combined synthetic metadata",
    )
    artifact = _mapping(combined.get("artifact"), "combined metadata artifact")
    _match_artifact_record(
        artifact.get("metadata"),
        expected_name="session-metadata.jsonl",
        records=records,
        label="combined output metadata",
    )


def _hash_dataset(root: Path) -> str:
    digest = hashlib.sha256()
    for split in ("train", "val", "test"):
        digest.update(split.encode("ascii") + b"\0")
        descriptor, _ = _open_regular(root / "data" / f"{split}.jsonl", f"sealed {split} split")
        with os.fdopen(descriptor, "rb") as stream:
            while True:
                chunk = stream.read(_COPY_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
    return digest.hexdigest()


def _validate_dataset_and_attestation(
    root: Path,
    documents: Mapping[str, Mapping[str, object]],
    reports: Mapping[str, Mapping[str, object]],
    records: Mapping[str, Mapping[str, object]],
    line_counts: Mapping[str, int],
) -> dict[str, object]:
    manifest = documents["manifest.json"]
    if manifest.get("format") != "peano-lab-next-tactic" or manifest.get("version") != 1:
        raise CorpusSealError("dataset manifest has the wrong format/version")
    manifest_hash = records["data/manifest.json"]["sha256"]
    aggregate = _hash_dataset(root)
    if _sha256(manifest.get("dataset_sha256"), "dataset aggregate hash") != aggregate:
        raise CorpusSealError("dataset manifest aggregate hash differs from sealed splits")

    split_table = _mapping(manifest.get("splits"), "dataset split table")
    if set(split_table) != {"train", "val", "test"}:
        raise CorpusSealError("dataset manifest must name exactly train, val, and test")
    split_identities: dict[str, object] = {}
    for split in ("train", "val", "test"):
        claimed = _mapping(split_table.get(split), f"dataset {split} split")
        actual = records[f"data/{split}.jsonl"]
        if _sha256(claimed.get("sha256"), f"dataset {split} hash") != actual["sha256"]:
            raise CorpusSealError(f"dataset {split} hash differs from sealed split")
        rows = _integer(claimed.get("rows"), f"dataset {split} rows", minimum=1)
        if rows != line_counts[f"{split}.jsonl"]:
            raise CorpusSealError(f"dataset {split} row count differs from sealed split")
        split_identities[split] = {"rows": rows, "sha256": actual["sha256"]}

    source = _mapping(manifest.get("source"), "dataset source provenance")
    traces = _sequence(source.get("traces"), "dataset source traces")
    if len(traces) != 2:
        raise CorpusSealError("dataset source must contain exactly two trace files")
    observed_trace_hashes: dict[str, str] = {}
    for index, value in enumerate(traces, 1):
        trace = _mapping(value, f"dataset source trace {index}")
        path_text = _text(trace.get("path"), f"dataset source trace {index}.path")
        path = Path(path_text)
        if ".." in path.parts or path.name not in {
            "library-raw-traces.jsonl",
            "balanced-raw-traces.jsonl",
        }:
            raise CorpusSealError(f"dataset source trace {index} has an unsafe path")
        if path.name in observed_trace_hashes:
            raise CorpusSealError("dataset source traces contain a duplicate")
        digest = _sha256(trace.get("sha256"), f"dataset source trace {index}.sha256")
        if digest != records[f"data/{path.name}"]["sha256"]:
            raise CorpusSealError(f"dataset source trace {path.name} hash mismatch")
        observed_trace_hashes[path.name] = digest
    metadata = _mapping(source.get("metadata"), "dataset source metadata")
    _embedded_path_name(metadata.get("path"), "session-metadata.jsonl", "dataset source metadata")
    metadata_hash = _sha256(metadata.get("sha256"), "dataset source metadata.sha256")
    if metadata_hash != records["data/session-metadata.jsonl"]["sha256"]:
        raise CorpusSealError("dataset source metadata hash mismatch")

    attestation = reports["dataset_attestation"]
    if (
        attestation.get("format") != "peano-policy-dataset-attestation"
        or attestation.get("v") != 2
        or attestation.get("prompt_version") != 3
        or attestation.get("independent_replay") is not True
        or attestation.get("held_out_contamination") != 0
    ):
        raise CorpusSealError("dataset attestation is not an accepted model-v3 replay")
    if _sha256(attestation.get("manifest_sha256"), "attested manifest hash") != manifest_hash:
        raise CorpusSealError("attestation names a different dataset manifest")
    if _sha256(attestation.get("dataset_sha256"), "attested dataset hash") != aggregate:
        raise CorpusSealError("attestation names a different dataset aggregate")
    attested_source = _mapping(attestation.get("source_artifacts"), "attested source artifacts")
    attested_traces = _sequence(attested_source.get("traces"), "attested source trace hashes")
    if sorted(_sha256(value, "attested source trace hash") for value in attested_traces) != sorted(
        observed_trace_hashes.values()
    ):
        raise CorpusSealError("attestation source traces differ from sealed traces")
    if _sha256(attested_source.get("metadata"), "attested metadata hash") != metadata_hash:
        raise CorpusSealError("attestation source metadata differs from sealed metadata")

    attested_splits = _mapping(attestation.get("splits"), "attested splits")
    if set(attested_splits) != {"train", "val", "test"}:
        raise CorpusSealError("attestation must name exactly train, val, and test")
    for split in ("train", "val", "test"):
        claimed = _mapping(attested_splits.get(split), f"attested {split} split")
        expected = split_identities[split]
        assert type(expected) is dict
        if (
            _sha256(claimed.get("sha256"), f"attested {split} hash") != expected["sha256"]
            or _integer(claimed.get("rows"), f"attested {split} rows", minimum=1) != expected["rows"]
        ):
            raise CorpusSealError(f"attested {split} identity differs from sealed split")

    schedule = _mapping(attestation.get("authority_schedule"), "attested authority schedule")
    if (
        schedule.get("method") != "catalog-predecessor-prefix-v1+full-synthetic-v1"
        or schedule.get("library_size") != EXPECTED_LIBRARY_SIZE
        or schedule.get("training_prefixes") != list(range(EXPECTED_LIBRARY_SIZE + 1))
        or schedule.get("inference_prefix") != EXPECTED_LIBRARY_SIZE
    ):
        raise CorpusSealError("attestation has the wrong model-v3 authority schedule")

    return {
        "manifest_sha256": manifest_hash,
        "dataset_sha256": aggregate,
        "prompt_version": 3,
        "library_snapshot_sha256": _sha256(
            attestation.get("library_snapshot_sha256"),
            "attested library snapshot",
        ),
        "prompt_contract_sha256": _sha256(
            attestation.get("prompt_contract_sha256"),
            "attested prompt contract",
        ),
        "held_out_contract_sha256": _sha256(
            attestation.get("held_out_contract_sha256"),
            "attested held-out contract",
        ),
        "training_environments_sha256": _sha256(
            attestation.get("training_environments_sha256"),
            "attested training environments",
        ),
        "authority_schedule": dict(schedule),
        "splits": split_identities,
    }


def _validate_token_audit(
    report: Mapping[str, object],
    records: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if (
        report.get("format") != "peano-policy-token-audit"
        or report.get("v") != 1
        or report.get("status") != "passed"
    ):
        raise CorpusSealError("token audit has the wrong format/version/status")
    config = _mapping(report.get("config"), "token audit config")
    config_path = _text(config.get("path"), "token audit config.path")
    if ".." in Path(config_path).parts or Path(config_path).name != "qwen3_1_7b_v3_library.toml":
        raise CorpusSealError("token audit used a different or unsafe configuration path")
    config_sha = _sha256(config.get("sha256"), "token audit config.sha256")
    if config.get("max_length") != EXPECTED_TOKEN_BUDGET:
        raise CorpusSealError("token audit did not retain the 32768-token budget")

    tokenizer = _mapping(report.get("tokenizer"), "token audit tokenizer")
    if (
        tokenizer.get("model_id") != EXPECTED_MODEL_ID
        or tokenizer.get("requested_revision") != EXPECTED_MODEL_REVISION
        or tokenizer.get("resolved_revision") != EXPECTED_MODEL_REVISION
    ):
        raise CorpusSealError("token audit did not use the pinned Qwen tokenizer")
    inputs = _mapping(report.get("inputs"), "token audit inputs")
    for role, data_name in (("train", "train.jsonl"), ("eval", "val.jsonl")):
        value = _mapping(inputs.get(role), f"token audit {role} input")
        _embedded_path_name(value.get("path"), data_name, f"token audit {role} input")
        if _sha256(value.get("sha256"), f"token audit {role} hash") != records[f"data/{data_name}"]["sha256"]:
            raise CorpusSealError(f"token audit {role} input differs from sealed data")
    splits = _mapping(report.get("splits"), "token audit split summaries")
    if set(splits) != {"train", "eval"}:
        raise CorpusSealError("token audit must summarize exactly train and eval")
    split_summaries: dict[str, object] = {}
    for role in ("train", "eval"):
        value = _mapping(splits.get(role), f"token audit {role} summary")
        rows = _integer(value.get("rows"), f"token audit {role} rows", minimum=1)
        maximum = _integer(value.get("maximum"), f"token audit {role} maximum", minimum=1)
        headroom = _integer(value.get("headroom"), f"token audit {role} headroom")
        if value.get("budget") != EXPECTED_TOKEN_BUDGET or maximum + headroom != EXPECTED_TOKEN_BUDGET:
            raise CorpusSealError(f"token audit {role} summary is internally inconsistent")
        split_summaries[role] = {
            "rows": rows,
            "maximum": maximum,
            "headroom": headroom,
        }
    return {
        "config_sha256": config_sha,
        "max_length": EXPECTED_TOKEN_BUDGET,
        "tokenizer": {
            "model_id": EXPECTED_MODEL_ID,
            "revision": EXPECTED_MODEL_REVISION,
        },
        "splits": split_summaries,
    }


def _validate_smoke(
    report: Mapping[str, object],
    *,
    expected_commit: str,
    expected_job_id: str,
) -> tuple[dict[str, object], dict[str, object]]:
    if (
        report.get("format") != "peano-policy-wmi-a100-v3-smoke"
        or report.get("v") != 1
        or report.get("status") != "passed"
    ):
        raise CorpusSealError("runtime smoke has the wrong format/version/status")
    model = _mapping(report.get("model"), "runtime smoke model")
    if (
        model.get("id") != EXPECTED_MODEL_ID
        or model.get("requested_revision") != EXPECTED_MODEL_REVISION
        or model.get("model_commit") != EXPECTED_MODEL_REVISION
        or model.get("tokenizer_commit") != EXPECTED_MODEL_REVISION
    ):
        raise CorpusSealError("runtime smoke did not load the pinned Qwen snapshot")

    job = _mapping(report.get("job"), "runtime smoke job")
    if job.get("scheduler") != "slurm" or _job_id(job.get("job_id"), "runtime smoke job id") != expected_job_id:
        raise CorpusSealError("runtime smoke belongs to a different preparation job")
    deployment = _mapping(job.get("deployment"), "runtime smoke deployment")
    source_sync = _mapping(deployment.get("source_sync"), "runtime smoke source sync")
    if (
        source_sync.get("status") != "synced"
        or _commit(source_sync.get("git_commit"), "runtime smoke source commit") != expected_commit
        or source_sync.get("git_dirty") is not False
    ):
        raise CorpusSealError("runtime smoke did not run from the expected clean source")
    source_sync_sha = _sha256(source_sync.get("sha256"), "runtime smoke source sync hash")
    synced_at = _text(source_sync.get("synced_at"), "runtime smoke source sync timestamp")

    script = _mapping(deployment.get("job_script"), "runtime smoke job script")
    if script.get("status") != "declared" or script.get("path") != EXPECTED_PREPARE_SCRIPT:
        raise CorpusSealError("runtime smoke used a different preparation script")
    script_sha = _sha256(script.get("sha256"), "runtime smoke job script hash")

    submission = _mapping(job.get("submission"), "runtime smoke submission")
    if (
        _job_id(submission.get("job_id"), "runtime smoke submission job id") != expected_job_id
        or _commit(submission.get("git_commit"), "runtime smoke submission commit") != expected_commit
        or submission.get("git_dirty") != "false"
        or submission.get("script") != EXPECTED_PREPARE_SCRIPT
        or _sha256(submission.get("script_sha256"), "runtime smoke submitted script hash") != script_sha
    ):
        raise CorpusSealError("runtime smoke submission differs from its clean deployment")
    submitted_at = _text(submission.get("timestamp"), "runtime smoke submission timestamp")
    ledger = _mapping(job.get("ledger"), "runtime smoke ledger")
    ledger_sha = _sha256(ledger.get("row_sha256"), "runtime smoke ledger row hash")
    if ledger_sha != _sha256_json(dict(submission)):
        raise CorpusSealError("runtime smoke ledger hash does not cover its submission row")

    source_identity = {
        "git_commit": expected_commit,
        "git_dirty": False,
        "source_sync_sha256": source_sync_sha,
        "source_synced_at": synced_at,
        "prepare_job_id": expected_job_id,
        "scheduler": "slurm",
        "submitted_at": submitted_at,
        "submission_ledger_row_sha256": ledger_sha,
        "job_script": {"path": EXPECTED_PREPARE_SCRIPT, "sha256": script_sha},
    }
    model_identity = {"id": EXPECTED_MODEL_ID, "revision": EXPECTED_MODEL_REVISION}
    return source_identity, model_identity


def _load_bundle_json(
    root: Path,
) -> tuple[
    dict[str, Mapping[str, object]],
    dict[str, Mapping[str, object]],
    dict[str, int],
]:
    documents: dict[str, Mapping[str, object]] = {}
    reports: dict[str, Mapping[str, object]] = {}
    line_counts: dict[str, int] = {}
    for name in DATA_FILES:
        path = root / "data" / name
        if name.endswith(".jsonl"):
            line_counts[name] = _load_jsonl(path, f"sealed data/{name}")
        else:
            documents[name] = _load_json_object(path, f"sealed data/{name}")[0]
    for role, name in REPORT_FILES.items():
        reports[role] = _load_json_object(
            root / "reports" / name,
            f"sealed reports/{name}",
        )[0]
    return documents, reports, line_counts


def _validate_bundle(
    root: Path,
    file_records: Sequence[Mapping[str, object]],
    *,
    expected_commit: str,
    expected_job_id: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    records = _record_table(file_records)
    documents, reports, line_counts = _load_bundle_json(root)
    _validate_source_manifests(documents, records)
    dataset_identity = _validate_dataset_and_attestation(
        root, documents, reports, records, line_counts
    )
    token_identity = _validate_token_audit(reports["token_audit"], records)
    source_identity, model_identity = _validate_smoke(
        reports["runtime_smoke"],
        expected_commit=expected_commit,
        expected_job_id=expected_job_id,
    )
    tokenizer_identity = _mapping(
        token_identity["tokenizer"], "validated tokenizer identity"
    )
    if (
        tokenizer_identity.get("model_id") != model_identity["id"]
        or tokenizer_identity.get("revision") != model_identity["revision"]
    ):
        raise CorpusSealError("token audit and runtime smoke identify different models")

    expected_names = _expected_report_source_names(expected_job_id)
    record_table = _record_table(file_records)
    report_identities = {
        "dataset_attestation": {
            "source_name": expected_names["dataset_attestation"],
            "sealed_path": f"reports/{REPORT_FILES['dataset_attestation']}",
            "sha256": record_table[f"reports/{REPORT_FILES['dataset_attestation']}"]["sha256"],
            "format": "peano-policy-dataset-attestation",
            "version": 2,
            "manifest_sha256": dataset_identity["manifest_sha256"],
            "dataset_sha256": dataset_identity["dataset_sha256"],
        },
        "token_audit": {
            "source_name": expected_names["token_audit"],
            "sealed_path": f"reports/{REPORT_FILES['token_audit']}",
            "sha256": record_table[f"reports/{REPORT_FILES['token_audit']}"]["sha256"],
            "format": "peano-policy-token-audit",
            "version": 1,
            "config_sha256": token_identity["config_sha256"],
        },
        "runtime_smoke": {
            "source_name": expected_names["runtime_smoke"],
            "sealed_path": f"reports/{REPORT_FILES['runtime_smoke']}",
            "sha256": record_table[f"reports/{REPORT_FILES['runtime_smoke']}"]["sha256"],
            "format": "peano-policy-wmi-a100-v3-smoke",
            "version": 1,
            "ledger_row_sha256": source_identity["submission_ledger_row_sha256"],
        },
    }
    return source_identity, dataset_identity, model_identity, report_identities


def _seal_manifest(
    file_records: Sequence[Mapping[str, object]],
    source_identity: Mapping[str, object],
    dataset_identity: Mapping[str, object],
    model_identity: Mapping[str, object],
    report_identities: Mapping[str, object],
) -> dict[str, object]:
    files = [dict(record) for record in file_records]
    identity = {
        "source": dict(source_identity),
        "dataset": dict(dataset_identity),
        "model": dict(model_identity),
        "reports": dict(report_identities),
        "files": files,
    }
    return {
        "format": SEAL_FORMAT,
        "version": SEAL_VERSION,
        **identity,
        "files_sha256": _sha256_json(files),
        "content_sha256": _sha256_json(identity),
    }


def _write_exclusive(path: Path, payload: bytes) -> None:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _protect_tree(root: Path) -> None:
    for directory in (root / "data", root / "reports"):
        for entry in os.scandir(directory):
            os.chmod(entry.path, 0o444, follow_symlinks=False)
        os.chmod(directory, 0o555, follow_symlinks=False)
    os.chmod(root / SEAL_MANIFEST, 0o444, follow_symlinks=False)
    os.chmod(root, 0o555, follow_symlinks=False)


def _remove_staging(root: Path) -> None:
    if not root.exists():
        return
    for current, directories, files in os.walk(root, topdown=False, followlinks=False):
        for name in files:
            try:
                os.chmod(Path(current) / name, 0o600, follow_symlinks=False)
            except OSError:
                pass
        for name in directories:
            try:
                os.chmod(Path(current) / name, 0o700, follow_symlinks=False)
            except OSError:
                pass
    try:
        os.chmod(root, 0o700, follow_symlinks=False)
    except OSError:
        pass
    shutil.rmtree(root)


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically install one sibling directory without replacing a target."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        try:
            rename = libc.renamex_np
        except AttributeError as exc:  # pragma: no cover - unsupported old platform
            raise CorpusSealError("atomic no-replace publication is unavailable") from exc
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        try:
            rename = libc.renameat2
        except AttributeError as exc:  # pragma: no cover - unsupported old libc
            raise CorpusSealError("atomic no-replace publication is unavailable") from exc
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 1)  # RENAME_NOREPLACE
    else:  # pragma: no cover - WMI and development hosts are Linux/macOS
        raise CorpusSealError("atomic no-replace publication is unsupported on this OS")
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(f"refusing to replace existing seal: {destination}")
    raise OSError(error, os.strerror(error), str(destination))


def _scan_sealed_tree(root: Path) -> dict[str, Path]:
    _reject_symlink_components(root, "sealed corpus")
    metadata = os.lstat(root)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CorpusSealError("sealed corpus must be one non-symlink directory")
    write_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    if metadata.st_mode & write_bits:
        raise CorpusSealError("sealed corpus root must be read-only")
    expected_root = {"data", "reports", SEAL_MANIFEST}
    root_entries = {entry.name: entry for entry in os.scandir(root)}
    if set(root_entries) != expected_root:
        raise CorpusSealError("sealed corpus root contains missing or unexpected entries")
    for directory_name in ("data", "reports"):
        entry = root_entries[directory_name]
        entry_stat = entry.stat(follow_symlinks=False)
        if entry.is_symlink() or not stat.S_ISDIR(entry_stat.st_mode):
            raise CorpusSealError(f"sealed {directory_name} must be a non-symlink directory")
        if entry_stat.st_mode & write_bits:
            raise CorpusSealError(f"sealed {directory_name} directory must be read-only")
    seal_entry = root_entries[SEAL_MANIFEST]
    seal_stat = seal_entry.stat(follow_symlinks=False)
    if seal_entry.is_symlink() or not stat.S_ISREG(seal_stat.st_mode):
        raise CorpusSealError("seal manifest must be one non-symlink regular file")
    if seal_stat.st_mode & write_bits:
        raise CorpusSealError("seal manifest must be read-only")

    expected_by_directory = {
        "data": set(DATA_FILES),
        "reports": set(REPORT_FILES.values()),
    }
    files: dict[str, Path] = {}
    for directory_name, expected in expected_by_directory.items():
        directory = root / directory_name
        entries = {entry.name: entry for entry in os.scandir(directory)}
        if set(entries) != expected:
            raise CorpusSealError(f"sealed {directory_name} contains missing or unexpected entries")
        for name in sorted(expected):
            entry = entries[name]
            entry_stat = entry.stat(follow_symlinks=False)
            if entry.is_symlink() or not stat.S_ISREG(entry_stat.st_mode):
                raise CorpusSealError(f"sealed {directory_name}/{name} is not a regular file")
            if entry_stat.st_mode & write_bits:
                raise CorpusSealError(
                    f"sealed {directory_name}/{name} must be read-only"
                )
            relative = f"{directory_name}/{name}"
            files[relative] = directory / name
    return files


def verify_seal(
    destination: str | os.PathLike[str],
    *,
    source_commit: str | None = None,
    prepare_job_id: str | None = None,
) -> dict[str, object]:
    """Independently verify one existing sealed corpus and return its manifest."""

    root = _safe_absolute_path(destination, "sealed corpus")
    files = _scan_sealed_tree(root)
    manifest, raw_manifest = _load_json_object(root / SEAL_MANIFEST, "seal manifest")
    if raw_manifest != _canonical_bytes(manifest):
        raise CorpusSealError("seal manifest is not canonical compact JSON")
    if manifest.get("format") != SEAL_FORMAT or manifest.get("version") != SEAL_VERSION:
        raise CorpusSealError("seal manifest has the wrong format/version")

    claimed_files = _sequence(manifest.get("files"), "seal file inventory")
    expected_paths = sorted(files)
    actual_records = [
        _file_record(path, _hash_regular_file(files[path], f"sealed {path}"))
        for path in expected_paths
    ]
    if claimed_files != actual_records:
        raise CorpusSealError("seal file inventory differs from the closed tree")
    if _sha256(manifest.get("files_sha256"), "seal file inventory hash") != _sha256_json(actual_records):
        raise CorpusSealError("seal file inventory aggregate is invalid")

    source = _mapping(manifest.get("source"), "seal source identity")
    sealed_commit = _commit(source.get("git_commit"), "seal source commit")
    sealed_job = _job_id(source.get("prepare_job_id"), "seal preparation job id")
    if source_commit is not None and _commit(source_commit, "expected source commit") != sealed_commit:
        raise CorpusSealError("seal belongs to a different source commit")
    if prepare_job_id is not None and _job_id(prepare_job_id, "expected preparation job id") != sealed_job:
        raise CorpusSealError("seal belongs to a different preparation job")

    identities = _validate_bundle(
        root,
        actual_records,
        expected_commit=sealed_commit,
        expected_job_id=sealed_job,
    )
    expected_manifest = _seal_manifest(actual_records, *identities)
    if manifest != expected_manifest:
        raise CorpusSealError("seal manifest identities do not match the sealed bundle")
    return expected_manifest


def seal_corpus(
    artifact_dir: str | os.PathLike[str],
    dataset_attestation: str | os.PathLike[str],
    token_audit: str | os.PathLike[str],
    runtime_smoke: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    source_commit: str,
    prepare_job_id: str,
) -> dict[str, object]:
    """Validate and atomically publish one new, non-overwriting corpus seal."""

    expected_commit = _commit(source_commit, "expected source commit")
    expected_job = _job_id(prepare_job_id, "expected preparation job id")
    source_root = _safe_absolute_path(artifact_dir, "artifact directory")
    source_files = _scan_data_directory(source_root)
    report_sources = _prepare_report_paths(
        {
            "dataset_attestation": dataset_attestation,
            "token_audit": token_audit,
            "runtime_smoke": runtime_smoke,
        },
        expected_job,
    )

    target = _safe_absolute_path(destination, "seal destination")
    if target.name in {"", ".", ".."}:
        raise CorpusSealError("seal destination must have one safe final component")
    _reject_symlink_components(target.parent, "seal destination parent")
    parent_stat = os.lstat(target.parent)
    if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(parent_stat.st_mode):
        raise CorpusSealError("seal destination parent must be a non-symlink directory")
    try:
        os.lstat(target)
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError(f"refusing to replace existing seal: {target}")
    if target == source_root or source_root in target.parents:
        raise CorpusSealError("seal destination must be outside the source artifact directory")

    staging = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=target.parent)
    )
    published = False
    try:
        (staging / "data").mkdir(mode=0o700)
        (staging / "reports").mkdir(mode=0o700)
        file_records: list[dict[str, object]] = []
        for name in DATA_FILES:
            measured = _copy_regular_file(
                source_files[name], staging / "data" / name, f"artifact {name}"
            )
            file_records.append(_file_record(f"data/{name}", measured))
        for role, sealed_name in REPORT_FILES.items():
            measured = _copy_regular_file(
                report_sources[role],
                staging / "reports" / sealed_name,
                f"{role} report",
            )
            file_records.append(_file_record(f"reports/{sealed_name}", measured))
        file_records.sort(key=lambda record: str(record["path"]))

        identities = _validate_bundle(
            staging,
            file_records,
            expected_commit=expected_commit,
            expected_job_id=expected_job,
        )
        manifest = _seal_manifest(file_records, *identities)
        _write_exclusive(staging / SEAL_MANIFEST, _canonical_bytes(manifest))
        _fsync_directory(staging / "data")
        _fsync_directory(staging / "reports")
        _fsync_directory(staging)
        _protect_tree(staging)
        verify_seal(
            staging,
            source_commit=expected_commit,
            prepare_job_id=expected_job,
        )
        # macOS renamex_np(RENAME_EXCL) rejects a read-only source directory,
        # even though its parent is writable.  Linux does not, so its staging
        # root remains protected across the atomic install.  On macOS only the
        # root is briefly owner-writable; every payload and child directory is
        # already protected.
        if sys.platform == "darwin":
            os.chmod(staging, 0o700, follow_symlinks=False)
        _rename_noreplace(staging, target)
        published = True
        if sys.platform == "darwin":
            os.chmod(target, 0o555, follow_symlinks=False)
        _fsync_directory(target.parent)
        return verify_seal(
            target,
            source_commit=expected_commit,
            prepare_job_id=expected_job,
        )
    finally:
        if not published and staging.exists():
            _remove_staging(staging)


__all__ = [
    "CorpusSealError",
    "DATA_FILES",
    "REPORT_FILES",
    "SEAL_FORMAT",
    "SEAL_MANIFEST",
    "SEAL_VERSION",
    "seal_corpus",
    "verify_seal",
]
