#!/usr/bin/env python3
"""Execute and collect the isolated three-root Hydra A2.3a WMI pilot.

The compute path deliberately treats the optimizer and its independent
verifier as external programs.  It runs two fresh producer processes under
different hash seeds, requires byte-identical candidate documents, and then
runs the verifier in a third fresh process.  The execution receipt is the last
file published in the run directory.

The collection path binds one terminal Slurm accounting row to the execution
receipt and the exact stdout/stderr bytes.  Resource failures, scheduler
timeouts, and absent execution evidence are ``unknown`` rather than theorem or
optimizer failures.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import signal
import stat
import subprocess
import sys
from time import monotonic
from typing import Any, Mapping, Sequence


FORMAT_EXECUTION = "peano-hydra-a23a-wmi-execution-receipt"
FORMAT_COLLECTION = "peano-hydra-a23a-wmi-collection-receipt"
FORMAT_SOURCE_STATE = "peano-hydra-producer-source-state"
FORMAT_SOURCE_STATE_ROOT = "peano-hydra-producer-source-state-root-preimage"
FORMAT_GIT_RECEIPT = "peano-hydra-a23a-producer-git-verification-receipt"
FORMAT_GIT_RECEIPT_ROOT = (
    "peano-hydra-a23a-producer-git-verification-receipt-root-preimage"
)
FORMAT_VERIFIER = "peano-hydra-library-optimizer-comparison-pilot-verification"
FORMAT_VERIFIER_ROOT = (
    "peano-hydra-library-optimizer-comparison-pilot-verification-root-preimage"
)
FORMAT_VERIFIER_RECORDS = (
    "peano-hydra-library-optimizer-comparison-pilot-verification-records-preimage"
)
VERIFIER_ID = "independent-a2.3a-optimizer-comparison-pilot-verification-v1"
VERIFIER_MODULE_PATH = (
    "training/peano_hydra/library_optimizer_comparison_verifier.py"
)
VERIFIER_MODULE_SHA256 = (
    "683ee529ed4be0e93504846340eeddf47eae1cb3f84967168a971d422ade1dbe"
)
VERIFIER_CLI_SHA256 = (
    "1250d0202236a6aa727509c5270767fe91e48cf34e5a6fd9c13ac1a59722f014"
)
VERIFIER_FALSE_FIELDS = frozenset(
    {
        "a2_complete",
        "dependency_vectors_complete",
        "evaluation_eligible",
        "freeze_ready",
        "lineage_complete",
        "minimality_claim",
        "optimized_best_known",
        "optimized_vector_independently_audited",
        "producer_git_verified",
        "proof_authority",
        "publication_authority",
        "publication_ready",
        "publication_union_complete",
        "publication_union_verified",
        "retrieval_eligible",
        "review_complete",
        "theorem_admission_authority",
        "training_eligible",
    }
)
VERIFIER_BODY_FIELDS = VERIFIER_FALSE_FIELDS | frozenset(
    {
        "aggregate",
        "candidate",
        "candidate_status",
        "format",
        "id",
        "kernel_artifacts_verified",
        "logic_mode",
        "producer_source_state",
        "producer_source_state_sha256",
        "status",
        "theorem_count",
        "theorem_records",
        "v",
        "verifier",
    }
)
VERIFIER_FIELDS = VERIFIER_BODY_FIELDS | frozenset(
    {"root_preimage", "root_sha256", "theorems"}
)
VERIFIER_KERNEL_SOURCES = (
    (
        "peano_lab",
        "peano-lab/py/peano_lab/__init__.py",
        "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a",
    ),
    (
        "peano_lab.kernel",
        "peano-lab/py/peano_lab/kernel/__init__.py",
        "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    ),
    (
        "peano_lab.kernel.artifact_codec",
        "peano-lab/py/peano_lab/kernel/artifact_codec.py",
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
    ),
    (
        "peano_lab.kernel.checker",
        "peano-lab/py/peano_lab/kernel/checker.py",
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
    ),
    (
        "peano_lab.kernel.formulas",
        "peano-lab/py/peano_lab/kernel/formulas.py",
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    ),
    (
        "peano_lab.kernel.proofs",
        "peano-lab/py/peano_lab/kernel/proofs.py",
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    ),
    (
        "peano_lab.kernel.terms",
        "peano-lab/py/peano_lab/kernel/terms.py",
        "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185",
    ),
    (
        "peano_lab.kernel.subst",
        "peano-lab/py/peano_lab/kernel/subst.py",
        "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    ),
)
FORMAT_INFRASTRUCTURE = "peano-hydra-a23a-wmi-infrastructure-manifest"
FORMAT_INFRASTRUCTURE_ROOT = (
    "peano-hydra-a23a-wmi-infrastructure-manifest-root-preimage"
)
VERSION = 1
PINNED_WMI_PYTHON = (
    "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python"
)
DISABLED_PYCACHE_PREFIX = "/proc/peano-hydra-a23a-disabled-pycache"
WMI_REMOTE_ROOT = Path(
    "/work/bnaskrecki/peano-lab-training/tmp/hydra-a23a-pilot"
)
EXPECTED_ROOTS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
FROZEN_PRODUCER_SOURCES = (
    (
        "training/peano_hydra/library-optimizer-comparison-pilot-schema-v1.json",
        "006d38ef781fc022b7b8929be35058038df02a0eee91eb2213128598c66a59ae",
    ),
    (
        "training/peano_hydra/library_optimizer_comparison_pilot.py",
        "7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee",
    ),
    (
        "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
        "3acbd3ec0f190699d484ef0c800e4919c7cc8404fbbd50ba6daf90a5deb5d6ee",
    ),
    (
        "peano-lab/py/tests/test_peano_hydra_library_optimizer_comparison_pilot.py",
        "d5ae3e830573c7a561462f5e0e91ef99bff42f6533986106cc65fc34f0e35dc9",
    ),
)
SOURCE_STATE_GENERATOR = "scripts/build_peano_hydra_a23a_producer_source_state.py"
INFRASTRUCTURE_SOURCES = (
    SOURCE_STATE_GENERATOR,
    "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
    "scripts/verify_peano_hydra_library_optimizer_comparison_pilot.py",
    VERIFIER_MODULE_PATH,
    "scripts/run_peano_hydra_a23a_wmi.py",
    "scripts/submit_wmi_hydra_a23a_pilot.sh",
    "scripts/collect_wmi_hydra_a23a_pilot.sh",
    "slurm/peano_wmi_hydra_a23a_pilot.sbatch",
    "peano-lab/py/tests/test_peano_hydra_a23a_producer_source_state.py",
    "peano-lab/py/tests/test_peano_hydra_library_optimizer_comparison_verifier.py",
    "peano-lab/py/tests/test_peano_hydra_a23a_wmi_protocol.py",
)
EXPECTED_RESOURCES = {
    "partition": "cpu_idle",
    "nodes": 1,
    "ntasks": 1,
    "cpus_per_task": 1,
    "memory_mib": 4096,
    "time_limit": "00:15:00",
    "time_limit_seconds": 900,
}
AUTHORITY_CLAIM_KEYS = frozenset(
    {
        "a2_complete",
        "dependency_vectors_complete",
        "evaluation_eligible",
        "freeze_ready",
        "lineage_complete",
        "minimality_claim",
        "optimized_best_known",
        "optimized_vector_independently_audited",
        "proof_authority",
        "publication_authority",
        "publication_ready",
        "publication_union_complete",
        "publication_union_verified",
        "retrieval_eligible",
        "review_complete",
        "theorem_admission_authority",
        "training_eligible",
    }
)
PRODUCER_TIMEOUT_SECONDS = 360
VERIFIER_TIMEOUT_SECONDS = 90
MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_LOG_BYTES = 16 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SHA1_RE = re.compile(r"[0-9a-f]{40}")
JOB_ID_RE = re.compile(r"[1-9][0-9]*")
TIMESTAMP_RE = re.compile(r"[0-9TZ:+.-]+")
TIME_LIMIT_RE = re.compile(r"(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}")
EXIT_CODE_RE = re.compile(r"[0-9]+:[0-9]+")
TERMINAL_STATES = frozenset(
    {
        "BOOT_FAIL",
        "CANCELLED",
        "COMPLETED",
        "DEADLINE",
        "FAILED",
        "NODE_FAIL",
        "OUT_OF_MEMORY",
        "PREEMPTED",
        "REVOKED",
        "SPECIAL_EXIT",
        "TIMEOUT",
    }
)
RESOURCE_OR_EXTERNAL_STATES = frozenset(
    {
        "BOOT_FAIL",
        "CANCELLED",
        "DEADLINE",
        "NODE_FAIL",
        "OUT_OF_MEMORY",
        "PREEMPTED",
        "REVOKED",
        "TIMEOUT",
    }
)
ACCEPTED_SACCT_REQUESTED_MEMORY = frozenset({"4096M", "4096Mn", "4G", "4Gn"})


class A23AWMIError(ValueError):
    """The deposited run state or scheduler evidence is malformed."""


def _authority_claims() -> dict[str, bool]:
    return {name: False for name in sorted(AUTHORITY_CLAIM_KEYS)}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw,
        usedforsecurity=False,
    ).hexdigest()


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _safe_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise A23AWMIError(f"path has a linked or non-directory ancestor: {path}")
    except A23AWMIError:
        raise
    except OSError as exc:
        raise A23AWMIError(f"cannot inspect path ancestors: {path}") from exc
    return absolute


def _read_stable_file_record(
    path: Path, *, limit: int, allow_empty: bool = True
) -> tuple[bytes, os.stat_result]:
    absolute = _safe_parent(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(absolute, flags)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or (not allow_empty and before.st_size == 0)
        ):
            raise A23AWMIError(f"file is not one bounded regular file: {path}")
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
        identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        observed = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if len(raw) != before.st_size or identity != observed:
            raise A23AWMIError(f"file changed during bounded read: {path}")
        return raw, before
    except A23AWMIError:
        raise
    except OSError as exc:
        raise A23AWMIError(f"cannot read regular non-link file: {path}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_stable_file(path: Path, *, limit: int, allow_empty: bool = True) -> bytes:
    raw, _metadata = _read_stable_file_record(
        path, limit=limit, allow_empty=allow_empty
    )
    return raw


def _sha256_file(path: Path, *, limit: int | None = None) -> tuple[str, int]:
    raw = _read_stable_file(
        path, limit=MAX_JSON_BYTES if limit is None else limit
    )
    return _sha256_bytes(raw), len(raw)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise A23AWMIError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> object:
    raise A23AWMIError(f"non-finite JSON number {value!r}")


def _reject_float(value: str) -> object:
    raise A23AWMIError(f"floating-point JSON number {value!r}")


def _canonical_bytes(value: object) -> bytes:
    try:
        raw = (
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise A23AWMIError("cannot encode canonical JSON") from exc
    if len(raw) > MAX_JSON_BYTES:
        raise A23AWMIError("canonical JSON exceeds byte limit")
    return raw


def _compact_sha256(value: object) -> str:
    try:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise A23AWMIError("cannot encode compact JSON preimage") from exc
    return _sha256_bytes(raw)


def _strict_json(path: Path, *, limit: int = MAX_JSON_BYTES) -> tuple[dict[str, object], bytes]:
    raw = _read_stable_file(path, limit=limit, allow_empty=False)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise A23AWMIError(f"cannot decode strict JSON: {path}") from exc
    if type(value) is not dict:
        raise A23AWMIError(f"JSON input must be one object: {path}")
    if _canonical_bytes(value) != raw:
        raise A23AWMIError(f"JSON input is not canonical: {path}")
    return value, raw


def _regular_file(path: Path) -> os.stat_result:
    absolute = _safe_parent(path)
    try:
        metadata = absolute.lstat()
    except OSError as exc:
        raise A23AWMIError(f"missing or unreadable regular file: {path}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise A23AWMIError(f"path is not one regular non-link file: {path}")
    return metadata


def _require_digest(value: str, *, kind: str = "sha256") -> str:
    pattern = SHA256_RE if kind == "sha256" else SHA1_RE
    if pattern.fullmatch(value) is None:
        raise A23AWMIError(f"malformed {kind} identity")
    return value


def _require_job_id(value: str) -> str:
    if JOB_ID_RE.fullmatch(value) is None:
        raise A23AWMIError("malformed Slurm job id")
    return value


def _resource_record(environment: Mapping[str, str]) -> dict[str, object]:
    names = {
        "partition": "PEANO_A23A_REQUESTED_PARTITION",
        "nodes": "PEANO_A23A_REQUESTED_NODES",
        "ntasks": "PEANO_A23A_REQUESTED_NTASKS",
        "cpus_per_task": "PEANO_A23A_REQUESTED_CPUS_PER_TASK",
        "memory_mib": "PEANO_A23A_REQUESTED_MEMORY_MIB",
        "time_limit": "PEANO_A23A_REQUESTED_TIME_LIMIT",
        "time_limit_seconds": "PEANO_A23A_REQUESTED_TIME_LIMIT_SECONDS",
    }
    observed: dict[str, object] = {}
    for key, name in names.items():
        raw = environment.get(name, "")
        if key in {"partition", "time_limit"}:
            observed[key] = raw
        else:
            if not raw.isascii() or not raw.isdigit() or raw.startswith("0"):
                raise A23AWMIError(f"missing or malformed {name}")
            observed[key] = int(raw)
    if not TIME_LIMIT_RE.fullmatch(str(observed["time_limit"])):
        raise A23AWMIError("malformed WMI A2.3a time limit")
    if observed != EXPECTED_RESOURCES:
        raise A23AWMIError(f"unexpected WMI A2.3a resource profile: {observed!r}")
    return observed


def _assert_runtime() -> dict[str, object]:
    version = platform.python_version()
    machine = platform.machine()
    if version != "3.12.12":
        raise A23AWMIError(f"WMI A2.3a requires CPython 3.12.12, observed {version}")
    if machine != "x86_64":
        raise A23AWMIError(f"WMI A2.3a requires x86_64, observed {machine}")
    executable = Path(sys.executable)
    if str(executable) != PINNED_WMI_PYTHON:
        raise A23AWMIError(
            f"WMI A2.3a requires interpreter {PINNED_WMI_PYTHON}, "
            f"observed {executable}"
        )
    if (
        sys.dont_write_bytecode is not True
        or sys.flags.no_site != 1
        or sys.flags.safe_path is not True
        or sys.pycache_prefix != DISABLED_PYCACHE_PREFIX
    ):
        raise A23AWMIError("WMI A2.3a interpreter isolation flags differ")
    return {
        "dont_write_bytecode": True,
        "executable": str(executable),
        "implementation": platform.python_implementation(),
        "machine": machine,
        "no_site": True,
        "pycache_prefix": DISABLED_PYCACHE_PREFIX,
        "python_version": version,
        "safe_path": True,
    }


def _validate_provenance(path: Path, *, commit: str, expected_sha256: str) -> dict[str, object]:
    raw = _read_stable_file(path, limit=256, allow_empty=False)
    if _sha256_bytes(raw) != expected_sha256:
        raise A23AWMIError("source provenance hash mismatch")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise A23AWMIError("source provenance is not ASCII") from exc
    if text.count("\n") != 1 or not text.endswith("\n"):
        raise A23AWMIError("source provenance must contain exactly one terminated row")
    fields = text[:-1].split("\t")
    if len(fields) != 3:
        raise A23AWMIError("source provenance has the wrong field count")
    recorded_commit, dirty, timestamp = fields
    if recorded_commit != commit or dirty != "false" or TIMESTAMP_RE.fullmatch(timestamp) is None:
        raise A23AWMIError("source provenance is malformed, dirty, or mismatched")
    return {
        "git_commit": recorded_commit,
        "git_dirty": False,
        "sha256": expected_sha256,
        "sync_timestamp": timestamp,
    }


def _validate_deposited_json(
    path: Path,
    *,
    expected_sha256: str,
    expected_format: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    value, raw = _strict_json(path)
    digest = _sha256_bytes(raw)
    if digest != expected_sha256:
        raise A23AWMIError(f"deposited JSON hash mismatch: {path.name}")
    if expected_format is not None and value.get("format") != expected_format:
        raise A23AWMIError(f"deposited JSON format mismatch: {path.name}")
    return value, {"bytes": len(raw), "path": path.name, "sha256": digest}


def _source_file(root: Path, relative: str) -> tuple[bytes, os.stat_result]:
    parts = Path(relative).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise A23AWMIError("unsafe producer source path")
    current = root
    for part in parts[:-1]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise A23AWMIError(f"missing producer source parent: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise A23AWMIError(f"linked or non-directory producer source parent: {relative}")
    path = root.joinpath(*parts)
    raw, metadata = _read_stable_file_record(
        path, limit=16_000_000, allow_empty=False
    )
    return raw, metadata


def _validate_source_state_document(
    value: Mapping[str, object],
    *,
    raw: bytes,
    source_root: Path,
    commit: str,
    tree: str,
) -> None:
    if set(value) != {
        "commit_sha1",
        "files",
        "format",
        "git_verified",
        "root_preimage",
        "root_sha256",
        "tree_sha1",
        "v",
    }:
        raise A23AWMIError("producer source state has the wrong fields")
    if (
        value.get("format") != FORMAT_SOURCE_STATE
        or value.get("v") != VERSION
        or value.get("git_verified") is not False
        or value.get("commit_sha1") != commit
        or value.get("tree_sha1") != tree
    ):
        raise A23AWMIError("producer source state identity is malformed")
    rows = value.get("files")
    if type(rows) is not list or len(rows) != len(FROZEN_PRODUCER_SOURCES):
        raise A23AWMIError("producer source state file vector is malformed")
    for row, (relative, expected_sha) in zip(rows, FROZEN_PRODUCER_SOURCES, strict=True):
        if type(row) is not dict or set(row) != {"bytes", "path", "sha256"}:
            raise A23AWMIError("producer source state file row is malformed")
        source_raw, _metadata = _source_file(source_root, relative)
        if (
            row.get("path") != relative
            or type(row.get("bytes")) is not int
            or row["bytes"] != len(source_raw)
            or row.get("sha256") != expected_sha
            or _sha256_bytes(source_raw) != expected_sha
        ):
            raise A23AWMIError(f"producer source state file drifted: {relative}")
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {"format": FORMAT_SOURCE_STATE_ROOT, "payload": body, "v": VERSION}
    if value.get("root_preimage") != preimage or value.get("root_sha256") != _compact_sha256(preimage):
        raise A23AWMIError("producer source state root is malformed")
    if _sha256_bytes(raw) == _sha256_bytes(b""):
        raise A23AWMIError("producer source state unexpectedly empty")


def _validate_git_file_row(
    row: object,
    *,
    source_root: Path,
    relative: str,
    expected_sha: str | None,
) -> None:
    if type(row) is not dict or set(row) != {
        "blob_oid_sha1",
        "bytes",
        "committed_sha256",
        "live_sha256",
        "mode",
        "path",
        "verified",
    }:
        raise A23AWMIError("Git receipt source row is malformed")
    raw, metadata = _source_file(source_root, relative)
    actual_sha = _sha256_bytes(raw)
    actual_blob = _git_blob_sha1(raw)
    if (
        row.get("path") != relative
        or row.get("verified") is not True
        or row.get("mode") not in {"100644", "100755"}
        or row.get("blob_oid_sha1") != actual_blob
        or type(row.get("bytes")) is not int
        or row["bytes"] != len(raw)
        or row.get("committed_sha256") != actual_sha
        or row.get("live_sha256") != actual_sha
        or (expected_sha is not None and actual_sha != expected_sha)
        or ((metadata.st_mode & 0o111) != 0) != (row.get("mode") == "100755")
    ):
        raise A23AWMIError(f"Git receipt source row drifted: {relative}")


def _validate_git_receipt_document(
    value: Mapping[str, object],
    *,
    source_root: Path,
    source_state: Mapping[str, object],
    source_state_raw: bytes,
    commit: str,
    tree: str,
) -> None:
    expected_fields = {
        "authority_claims",
        "commands",
        "commit_sha1",
        "format",
        "generator",
        "git_tool",
        "root_preimage",
        "root_sha256",
        "source_files",
        "source_state_artifact_sha256",
        "source_state_root_sha256",
        "source_state_sha256",
        "status",
        "tree_sha1",
        "v",
        "verification",
    }
    if set(value) != expected_fields:
        raise A23AWMIError("producer Git receipt has the wrong fields")
    if (
        value.get("format") != FORMAT_GIT_RECEIPT
        or value.get("v") != VERSION
        or value.get("status") != "passed"
        or value.get("commit_sha1") != commit
        or value.get("tree_sha1") != tree
        or value.get("source_state_artifact_sha256") != _sha256_bytes(source_state_raw)
        or value.get("source_state_root_sha256") != source_state.get("root_sha256")
        or value.get("source_state_sha256") != _compact_sha256(source_state)
    ):
        raise A23AWMIError("producer Git receipt identity is malformed")
    claims = value.get("authority_claims")
    claim_keys = {
        "a2_complete",
        "evaluation_eligible",
        "freeze_ready",
        "minimality_claim",
        "optimized_best_known",
        "optimized_vector_independently_audited",
        "proof_authority",
        "publication_ready",
        "publication_union_complete",
        "training_eligible",
    }
    if (
        type(claims) is not dict
        or set(claims) != claim_keys
        or any(item is not False for item in claims.values())
    ):
        raise A23AWMIError("producer Git receipt authority claims are not all false")
    rows = value.get("source_files")
    if type(rows) is not list or len(rows) != len(FROZEN_PRODUCER_SOURCES):
        raise A23AWMIError("producer Git receipt source vector is malformed")
    for row, (relative, expected_sha) in zip(rows, FROZEN_PRODUCER_SOURCES, strict=True):
        _validate_git_file_row(
            row,
            source_root=source_root,
            relative=relative,
            expected_sha=expected_sha,
        )
    _validate_git_file_row(
        value.get("generator"),
        source_root=source_root,
        relative=SOURCE_STATE_GENERATOR,
        expected_sha=None,
    )
    source_receipt_rows = {
        row["path"]: row for row in [*rows, value["generator"]]
    }
    verification = value.get("verification")
    required_true = {
        "clean_after",
        "clean_before",
        "commit_stable",
        "diff_cached_quiet_after",
        "diff_cached_quiet_before",
        "diff_quiet_after",
        "diff_quiet_before",
        "generator_matches_head",
        "producer_files_match_head",
        "stage_zero_regular_blobs",
        "tree_stable",
    }
    verification_keys = required_true | {
        "head_after",
        "head_before",
        "porcelain_after_bytes",
        "porcelain_after_sha256",
        "porcelain_before_bytes",
        "porcelain_before_sha256",
        "tree_after",
        "tree_before",
    }
    if type(verification) is not dict or set(verification) != verification_keys:
        raise A23AWMIError("producer Git receipt verification is malformed")
    if any(verification.get(key) is not True for key in required_true):
        raise A23AWMIError("producer Git verification lacks a required true fact")
    if (
        verification.get("head_before") != commit
        or verification.get("head_after") != commit
        or verification.get("tree_before") != tree
        or verification.get("tree_after") != tree
        or verification.get("porcelain_before_bytes") != 0
        or verification.get("porcelain_after_bytes") != 0
        or verification.get("porcelain_before_sha256") != _sha256_bytes(b"")
        or verification.get("porcelain_after_sha256") != _sha256_bytes(b"")
    ):
        raise A23AWMIError("producer Git receipt clean-tree facts are malformed")
    commands = value.get("commands")
    tool = value.get("git_tool")
    if (
        type(tool) is not dict
        or set(tool) != {"bytes", "path", "sha256", "version"}
        or type(tool.get("bytes")) is not int
        or tool["bytes"] <= 0
        or type(tool.get("path")) is not str
        or not tool["path"].startswith("/")
        or type(tool.get("version")) is not str
        or not tool["version"].startswith("git version ")
        or type(tool.get("sha256")) is not str
        or SHA256_RE.fullmatch(tool["sha256"]) is None
    ):
        raise A23AWMIError("producer Git tool identity is malformed")
    paths = tuple(relative for relative, _digest in FROZEN_PRODUCER_SOURCES) + (
        SOURCE_STATE_GENERATOR,
    )
    expected_argv: list[list[str]] = [
        ["git", "--version"],
        ["git", "rev-parse", "--show-toplevel"],
        ["git", "rev-parse", "--verify", "HEAD"],
        ["git", "rev-parse", "--verify", "HEAD^{tree}"],
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ["git", "diff", "--quiet", "--no-ext-diff", "--"],
        ["git", "diff", "--cached", "--quiet", "--no-ext-diff", "--"],
    ]
    for relative in paths:
        expected_argv.extend(
            (
                ["git", "ls-files", "--stage", "-z", "--", relative],
                [
                    "git",
                    "show",
                    "--no-ext-diff",
                    "--no-textconv",
                    f"{commit}:{relative}",
                ],
            )
        )
    expected_argv.extend(
        (
            ["git", "rev-parse", "--verify", "HEAD"],
            ["git", "rev-parse", "--verify", "HEAD^{tree}"],
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            ["git", "diff", "--quiet", "--no-ext-diff", "--"],
            ["git", "diff", "--cached", "--quiet", "--no-ext-diff", "--"],
        )
    )
    if type(commands) is not list or len(commands) != len(expected_argv):
        raise A23AWMIError("producer Git receipt command transcript is missing")
    empty_sha = _sha256_bytes(b"")
    for row, argv in zip(commands, expected_argv, strict=True):
        if type(row) is not dict or set(row) != {
            "argv",
            "exit_code",
            "stderr_bytes",
            "stderr_sha256",
            "stdout_bytes",
            "stdout_sha256",
        }:
            raise A23AWMIError("producer Git command row is malformed")
        if (
            row.get("argv") != argv
            or row.get("exit_code") != 0
            or row.get("stderr_bytes") != 0
            or row.get("stderr_sha256") != empty_sha
            or type(row.get("stdout_bytes")) is not int
            or row["stdout_bytes"] < 0
            or type(row.get("stdout_sha256")) is not str
            or SHA256_RE.fullmatch(row["stdout_sha256"]) is None
        ):
            raise A23AWMIError("producer Git command transcript identity drifted")
        if argv[1] in {"status", "diff"} and (
            row["stdout_bytes"] != 0 or row["stdout_sha256"] != empty_sha
        ):
            raise A23AWMIError("producer Git clean command emitted output")
        if argv == ["git", "--version"]:
            expected = (tool["version"] + "\n").encode("utf-8")
            if row["stdout_bytes"] != len(expected) or row["stdout_sha256"] != _sha256_bytes(expected):
                raise A23AWMIError("producer Git version command output mismatch")
        if argv == ["git", "rev-parse", "--verify", "HEAD"]:
            expected = (commit + "\n").encode("ascii")
            if row["stdout_bytes"] != len(expected) or row["stdout_sha256"] != _sha256_bytes(expected):
                raise A23AWMIError("producer Git HEAD command output mismatch")
        if argv == ["git", "rev-parse", "--verify", "HEAD^{tree}"]:
            expected = (tree + "\n").encode("ascii")
            if row["stdout_bytes"] != len(expected) or row["stdout_sha256"] != _sha256_bytes(expected):
                raise A23AWMIError("producer Git tree command output mismatch")
        if len(argv) >= 2 and argv[1] == "show":
            relative = argv[-1].split(":", 1)[1]
            raw, _metadata = _source_file(source_root, relative)
            if row["stdout_bytes"] != len(raw) or row["stdout_sha256"] != _sha256_bytes(raw):
                raise A23AWMIError("producer Git show output mismatch")
        if len(argv) >= 2 and argv[1] == "ls-files":
            relative = argv[-1]
            source_row = source_receipt_rows[relative]
            expected = (
                f"{source_row['mode']} {source_row['blob_oid_sha1']} 0\t{relative}\0"
            ).encode("utf-8")
            if row["stdout_bytes"] != len(expected) or row["stdout_sha256"] != _sha256_bytes(expected):
                raise A23AWMIError("producer Git index command output mismatch")
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {"format": FORMAT_GIT_RECEIPT_ROOT, "payload": body, "v": VERSION}
    if value.get("root_preimage") != preimage or value.get("root_sha256") != _compact_sha256(preimage):
        raise A23AWMIError("producer Git receipt root is malformed")


def _infrastructure_manifest(
    *, repository_root: Path, commit: str, tree: str
) -> dict[str, object]:
    root = repository_root.resolve(strict=True)
    rows: list[dict[str, object]] = []
    for relative in INFRASTRUCTURE_SOURCES:
        raw, metadata = _source_file(root, relative)
        rows.append(
            {
                "bytes": len(raw),
                "mode": "100755" if metadata.st_mode & 0o111 else "100644",
                "path": relative,
                "sha256": _sha256_bytes(raw),
            }
        )
    return _receipt_with_root(
        {
            "files": rows,
            "format": FORMAT_INFRASTRUCTURE,
            "git_commit": commit,
            "git_tree": tree,
            "v": VERSION,
        }
    )


def _validate_infrastructure_manifest(
    value: Mapping[str, object],
    *,
    source_root: Path,
    commit: str,
    tree: str,
) -> None:
    if set(value) != {
        "files",
        "format",
        "git_commit",
        "git_tree",
        "root_preimage",
        "root_sha256",
        "v",
    }:
        raise A23AWMIError("A2.3a infrastructure manifest has the wrong fields")
    if (
        value.get("format") != FORMAT_INFRASTRUCTURE
        or value.get("v") != VERSION
        or value.get("git_commit") != commit
        or value.get("git_tree") != tree
    ):
        raise A23AWMIError("A2.3a infrastructure manifest identity is malformed")
    rows = value.get("files")
    if type(rows) is not list or len(rows) != len(INFRASTRUCTURE_SOURCES):
        raise A23AWMIError("A2.3a infrastructure source vector is malformed")
    for row, relative in zip(rows, INFRASTRUCTURE_SOURCES, strict=True):
        if type(row) is not dict or set(row) != {"bytes", "mode", "path", "sha256"}:
            raise A23AWMIError("A2.3a infrastructure source row is malformed")
        raw, metadata = _source_file(source_root, relative)
        expected_mode = "100755" if metadata.st_mode & 0o111 else "100644"
        if (
            row.get("path") != relative
            or row.get("mode") != expected_mode
            or type(row.get("bytes")) is not int
            or row["bytes"] != len(raw)
            or row.get("sha256") != _sha256_bytes(raw)
        ):
            raise A23AWMIError(f"A2.3a infrastructure source drifted: {relative}")
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {"format": FORMAT_INFRASTRUCTURE_ROOT, "payload": body, "v": VERSION}
    if value.get("root_preimage") != preimage or value.get("root_sha256") != _compact_sha256(preimage):
        raise A23AWMIError("A2.3a infrastructure manifest root is malformed")


def _isolated_environment(hash_seed: int) -> dict[str, str]:
    if hash_seed not in {0, 1, 2}:
        raise A23AWMIError("unreviewed producer/verifier hash seed")
    return {
        "HOME": "/nonexistent/peano-a23a-wmi",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": str(hash_seed),
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": DISABLED_PYCACHE_PREFIX,
        "TZ": "UTC",
    }


def _run_process(
    *,
    role: str,
    argv: Sequence[str],
    cwd: Path,
    run_root: Path,
    hash_seed: int,
    timeout_seconds: int,
) -> dict[str, object]:
    stdout_path = run_root / f"{role}.stdout.log"
    stderr_path = run_root / f"{role}.stderr.log"
    started_at = _utc_now()
    started = monotonic()
    timed_out = False
    output_limit_reached = False
    returncode: int | None = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            env=_isolated_environment(hash_seed),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        if process.stdout is None or process.stderr is None:
            raise A23AWMIError("cannot create bounded child-output pipes")
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, stdout)
        selector.register(process.stderr, selectors.EVENT_READ, stderr)
        counts = {stdout.fileno(): 0, stderr.fileno(): 0}

        def terminate_group() -> None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                try:
                    process.kill()
                except OSError:
                    pass

        stop_reading = False
        try:
            while selector.get_map():
                remaining = timeout_seconds - (monotonic() - started)
                if remaining <= 0:
                    timed_out = True
                    terminate_group()
                    stop_reading = True
                    break
                for key, _mask in selector.select(min(remaining, 0.25)):
                    pipe = key.fileobj
                    destination = key.data
                    chunk = os.read(pipe.fileno(), 65_536)
                    if not chunk:
                        selector.unregister(pipe)
                        pipe.close()
                        continue
                    written = counts[destination.fileno()]
                    available = MAX_LOG_BYTES - written
                    if len(chunk) > available:
                        if available:
                            destination.write(chunk[:available])
                            counts[destination.fileno()] += available
                        output_limit_reached = True
                        terminate_group()
                        stop_reading = True
                        break
                    destination.write(chunk)
                    counts[destination.fileno()] += len(chunk)
                if stop_reading:
                    break
        finally:
            for key in list(selector.get_map().values()):
                pipe = key.fileobj
                try:
                    selector.unregister(pipe)
                except Exception:
                    pass
                pipe.close()
            selector.close()
        try:
            returncode = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate_group()
            returncode = process.wait(timeout=5)
        stdout.flush()
        stderr.flush()
        os.fsync(stdout.fileno())
        os.fsync(stderr.fileno())
    duration = monotonic() - started
    stdout_sha, stdout_bytes = _sha256_file(stdout_path, limit=MAX_LOG_BYTES)
    stderr_sha, stderr_bytes = _sha256_file(stderr_path, limit=MAX_LOG_BYTES)
    if stdout_bytes > MAX_LOG_BYTES or stderr_bytes > MAX_LOG_BYTES:
        raise A23AWMIError("bounded child output exceeded its hard limit")
    return {
        "argv": list(argv),
        "duration_seconds_millis": int(duration * 1000),
        "environment": _isolated_environment(hash_seed),
        "finished_at": _utc_now(),
        "hash_seed": hash_seed,
        "output_limit_reached": output_limit_reached,
        "returncode": returncode,
        "role": role,
        "started_at": started_at,
        "stderr": {
            "bytes": stderr_bytes,
            "path": stderr_path.name,
            "sha256": stderr_sha,
        },
        "stdout": {
            "bytes": stdout_bytes,
            "path": stdout_path.name,
            "sha256": stdout_sha,
        },
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
    }


def _process_outcome(record: Mapping[str, object]) -> str:
    if record.get("timed_out") is True or record.get("output_limit_reached") is True:
        return "unknown"
    returncode = record.get("returncode")
    if type(returncode) is not int:
        return "unknown"
    if returncode == 0:
        return "passed"
    # A process exit status alone is infrastructure evidence, not a complete
    # typed optimizer/verifier rejection.  Signals, timeouts, and ordinary
    # nonzero exits are therefore all unknown here.
    return "unknown"


def _validate_candidate_document(
    candidate: Mapping[str, object],
    *,
    raw: bytes,
    filename: str,
    source_state: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    rows = candidate.get("theorems")
    if type(rows) is not list or tuple(
        (row.get("index"), row.get("name"))
        for row in rows
        if type(row) is dict
    ) != EXPECTED_ROOTS or len(rows) != len(EXPECTED_ROOTS):
        raise A23AWMIError("candidate does not contain exactly the three reviewed roots")
    if candidate.get("producer_source_state") != source_state:
        raise A23AWMIError("candidate does not embed the exact deposited source state")
    aggregate = candidate.get("aggregate")
    if type(aggregate) is not dict or aggregate.get("pilot_theorem_count") != 3:
        raise A23AWMIError("candidate aggregate is not the bounded three-root pilot")
    return dict(candidate), {
        "bytes": len(raw),
        "path": filename,
        "root_sha256": candidate.get("root_sha256"),
        "sha256": _sha256_bytes(raw),
    }


def _validate_candidate(
    path: Path, *, source_state: Mapping[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    candidate, raw = _strict_json(path)
    return _validate_candidate_document(
        candidate,
        raw=raw,
        filename=path.name,
        source_state=source_state,
    )


def _record_sha256(value: Mapping[str, object]) -> str:
    return _compact_sha256(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _validate_verifier_receipt(
    receipt: Mapping[str, object],
    *,
    candidate: Mapping[str, object],
    candidate_raw: bytes,
    source_state: Mapping[str, object],
    source_state_raw: bytes,
    source_root: Path,
) -> None:
    if set(receipt) != VERIFIER_FIELDS:
        raise A23AWMIError("independent verifier receipt has the wrong fields")
    if any(receipt.get(name) is not False for name in VERIFIER_FALSE_FIELDS):
        raise A23AWMIError("independent verifier receipt grants forbidden authority")
    if (
        receipt.get("format") != FORMAT_VERIFIER
        or receipt.get("id") != VERIFIER_ID
        or receipt.get("v") != VERSION
        or receipt.get("status") != "passed"
        or receipt.get("candidate_status") != "candidate"
        or receipt.get("logic_mode") != "intuitionistic"
        or receipt.get("kernel_artifacts_verified") is not True
        or receipt.get("theorem_count") != len(EXPECTED_ROOTS)
    ):
        raise A23AWMIError("independent verifier receipt identity is malformed")

    candidate_binding = receipt.get("candidate")
    candidate_records = candidate.get("theorem_records")
    if (
        type(candidate_binding) is not dict
        or set(candidate_binding)
        != {
            "artifact_bytes",
            "artifact_sha256",
            "root_sha256",
            "theorem_record_root_sha256",
        }
        or candidate_binding.get("artifact_bytes") != len(candidate_raw)
        or candidate_binding.get("artifact_sha256") != _sha256_bytes(candidate_raw)
        or candidate_binding.get("root_sha256") != candidate.get("root_sha256")
        or type(candidate_records) is not dict
        or candidate_binding.get("theorem_record_root_sha256")
        != candidate_records.get("root_sha256")
    ):
        raise A23AWMIError("independent verifier candidate binding differs")
    source_binding = receipt.get("producer_source_state")
    semantic_sha = _compact_sha256(source_state)
    if (
        type(source_binding) is not dict
        or set(source_binding)
        != {"artifact_bytes", "artifact_sha256", "root_sha256", "semantic_sha256"}
        or source_binding.get("artifact_bytes") != len(source_state_raw)
        or source_binding.get("artifact_sha256") != _sha256_bytes(source_state_raw)
        or source_binding.get("root_sha256") != source_state.get("root_sha256")
        or source_binding.get("semantic_sha256") != semantic_sha
        or receipt.get("producer_source_state_sha256") != semantic_sha
        or candidate.get("producer_source_state_sha256") != semantic_sha
    ):
        raise A23AWMIError("independent verifier source-state binding differs")

    candidate_rows = candidate.get("theorems")
    rows = receipt.get("theorems")
    if type(candidate_rows) is not list or type(rows) is not list or len(rows) != 3:
        raise A23AWMIError("independent verifier theorem vector is malformed")
    identities: list[dict[str, object]] = []
    frontier_total = 0
    representative_counts = {
        "retained-replay": 0,
        "a2.2-direct-cut-rebuild": 0,
        "layered-closure": 0,
    }
    accepted_artifacts = 0
    for (expected_index, expected_name), candidate_row, row in zip(
        EXPECTED_ROOTS, candidate_rows, rows, strict=True
    ):
        row_fields = {
            "artifacts",
            "candidate_record_sha256",
            "index",
            "name",
            "nondominated_candidate_ids_in_input_order",
            "record_sha256",
            "representative_candidate_id",
        }
        if (
            type(candidate_row) is not dict
            or type(row) is not dict
            or set(row) != row_fields
            or row.get("index") != expected_index
            or row.get("name") != expected_name
            or row.get("candidate_record_sha256") != candidate_row.get("record_sha256")
            or row.get("record_sha256") != _record_sha256(row)
        ):
            raise A23AWMIError("independent verifier theorem record differs")
        comparison = candidate_row.get("comparison")
        candidate_artifacts = candidate_row.get("artifacts")
        observations = row.get("artifacts")
        if (
            type(comparison) is not dict
            or row.get("nondominated_candidate_ids_in_input_order")
            != comparison.get("nondominated_candidate_ids_in_input_order")
            or row.get("representative_candidate_id")
            != comparison.get("representative_candidate_id")
            or type(candidate_artifacts) is not list
            or type(observations) is not list
            or len(candidate_artifacts) != 3
            or len(observations) != 3
        ):
            raise A23AWMIError("independent verifier comparison record differs")
        frontier = row["nondominated_candidate_ids_in_input_order"]
        representative = row["representative_candidate_id"]
        if type(frontier) is not list or not frontier or representative not in representative_counts:
            raise A23AWMIError("independent verifier frontier record is malformed")
        frontier_total += len(frontier)
        representative_counts[representative] += 1
        for expected_order, (candidate_artifact, observation) in enumerate(
            zip(candidate_artifacts, observations, strict=True)
        ):
            observation_fields = {
                "artifact_sha256",
                "candidate_id",
                "candidate_kind_order",
                "formula_sha256",
                "fuel",
                "kernel_accepted",
                "kernel_context",
                "metrics",
                "proof_term_sha256",
            }
            if (
                type(candidate_artifact) is not dict
                or type(observation) is not dict
                or set(observation) != observation_fields
                or observation.get("candidate_kind_order") != expected_order
                or any(
                    observation.get(key) != candidate_artifact.get(key)
                    for key in observation_fields
                )
                or observation.get("kernel_accepted") is not True
                or observation.get("kernel_context") != "empty"
                or type(observation.get("metrics")) is not dict
                or set(observation["metrics"])
                != {"artifact_bytes", "cut_nodes", "proof_depth", "proof_nodes"}
            ):
                raise A23AWMIError("independent verifier artifact observation differs")
            accepted_artifacts += 1
        identities.append(
            {
                "index": expected_index,
                "name": expected_name,
                "record_sha256": row["record_sha256"],
            }
        )
    records_preimage = {
        "format": FORMAT_VERIFIER_RECORDS,
        "records": identities,
        "v": VERSION,
    }
    expected_records = {
        "count": 3,
        "preimage": records_preimage,
        "root_sha256": _compact_sha256(records_preimage),
    }
    if receipt.get("theorem_records") != expected_records:
        raise A23AWMIError("independent verifier theorem-record root differs")
    candidate_aggregate = candidate.get("aggregate")
    aggregate = receipt.get("aggregate")
    if (
        type(candidate_aggregate) is not dict
        or type(aggregate) is not dict
        or set(aggregate)
        != {
            "candidate_artifact_count",
            "kernel_accepted_artifact_count",
            "nondominated_members_total",
            "pilot_theorem_count",
            "representative_counts",
        }
        or aggregate.get("candidate_artifact_count") != 9
        or aggregate.get("kernel_accepted_artifact_count") != accepted_artifacts
        or aggregate.get("nondominated_members_total") != frontier_total
        or aggregate.get("pilot_theorem_count") != 3
        or aggregate.get("representative_counts") != representative_counts
        or aggregate.get("nondominated_members_total")
        != candidate_aggregate.get("nondominated_members_total")
        or aggregate.get("representative_counts")
        != candidate_aggregate.get("representative_counts")
    ):
        raise A23AWMIError("independent verifier aggregate differs")

    verifier = receipt.get("verifier")
    expected_kernel_rows = [
        {"module": module, "path": path, "sha256": digest}
        for module, path, digest in VERIFIER_KERNEL_SOURCES
    ]
    if (
        type(verifier) is not dict
        or set(verifier)
        != {
            "bytecode_write_disabled",
            "import_policy",
            "kernel_sources",
            "load_mode",
            "path",
            "pycache_prefix",
            "safe_path",
            "sha256",
            "site_import_disabled",
            "source_loader_preflight",
            "stdlib_precedes_peano_root",
            "user_site_disabled",
        }
        or verifier.get("bytecode_write_disabled") is not True
        or verifier.get("import_policy") != "stdlib-and-peano-kernel-only"
        or verifier.get("load_mode")
        != "direct-source-module-without-training-package-init"
        or verifier.get("path") != VERIFIER_MODULE_PATH
        or verifier.get("pycache_prefix") != DISABLED_PYCACHE_PREFIX
        or verifier.get("safe_path") is not True
        or verifier.get("sha256") != VERIFIER_MODULE_SHA256
        or verifier.get("site_import_disabled") is not True
        or verifier.get("source_loader_preflight")
        != "pathfinder-sourcefileloader-exact-origin"
        or verifier.get("stdlib_precedes_peano_root") is not True
        or verifier.get("user_site_disabled") is not True
        or verifier.get("kernel_sources") != expected_kernel_rows
    ):
        raise A23AWMIError("independent verifier source identity differs")
    verifier_raw, _metadata = _source_file(source_root, VERIFIER_MODULE_PATH)
    if _sha256_bytes(verifier_raw) != VERIFIER_MODULE_SHA256:
        raise A23AWMIError("live independent verifier source hash differs")
    cli_raw, _metadata = _source_file(
        source_root, "scripts/verify_peano_hydra_library_optimizer_comparison_pilot.py"
    )
    if _sha256_bytes(cli_raw) != VERIFIER_CLI_SHA256:
        raise A23AWMIError("live independent verifier CLI hash differs")
    for _module, relative, digest in VERIFIER_KERNEL_SOURCES:
        raw, _metadata = _source_file(source_root, relative)
        if _sha256_bytes(raw) != digest:
            raise A23AWMIError(f"live verifier kernel source drifted: {relative}")

    body = {key: receipt[key] for key in VERIFIER_BODY_FIELDS}
    preimage = {"format": FORMAT_VERIFIER_ROOT, "payload": body, "v": VERSION}
    if receipt.get("root_preimage") != preimage or receipt.get("root_sha256") != _compact_sha256(preimage):
        raise A23AWMIError("independent verifier receipt root differs")


def _receipt_with_root(payload: dict[str, object]) -> dict[str, object]:
    preimage = {
        "format": f"{payload['format']}-root-preimage",
        "payload": payload,
        "v": payload["v"],
    }
    return {
        **payload,
        "root_preimage": preimage,
        "root_sha256": _sha256_bytes(
            json.dumps(
                preimage,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ),
    }


def _publish_create_only(path: Path, value: Mapping[str, object]) -> None:
    raw = _canonical_bytes(dict(value))
    path = _safe_parent(path)
    path.parent.mkdir(mode=0o700, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise A23AWMIError(f"refusing to replace existing receipt: {path}")
    stage = path.parent / f".{path.name}.{os.getpid()}.tmp"
    descriptor: int | None = None
    linked = False
    try:
        descriptor = os.open(
            stage,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, path, follow_symlinks=False)
        linked = True
        stage.unlink()
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        if linked:
            try:
                path.unlink()
            except OSError:
                pass
        raise A23AWMIError(f"cannot publish create-only receipt: {path}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            stage.unlink()
        except OSError:
            pass


def _execute(args: argparse.Namespace) -> int:
    snapshot_sha_early = _require_digest(
        os.environ.get("PEANO_A23A_SNAPSHOT_SHA256", "")
    )
    job_id_early = _require_job_id(os.environ.get("SLURM_JOB_ID", ""))
    snapshot_root = _lexical_absolute(
        Path(os.environ.get("PEANO_A23A_SNAPSHOT_ROOT", ""))
    )
    expected_snapshot = WMI_REMOTE_ROOT / snapshot_sha_early
    if snapshot_root != expected_snapshot:
        raise A23AWMIError("execute snapshot root differs from its content identity")
    source_root = _lexical_absolute(args.source_root)
    input_root = snapshot_root / "inputs"
    run_root = _lexical_absolute(args.run_root)
    expected_run_root = snapshot_root / "runs" / job_id_early
    if (
        source_root != snapshot_root / "source"
        or _lexical_absolute(Path(os.environ.get("PEANO_A23A_SOURCE_ROOT", "")))
        != source_root
        or _lexical_absolute(Path(os.environ.get("PEANO_A23A_INPUT_ROOT", "")))
        != input_root
        or _lexical_absolute(args.source_state)
        != input_root / "producer-source-state.json"
        or _lexical_absolute(args.git_receipt)
        != input_root / "producer-git-verification-receipt.json"
        or _lexical_absolute(args.infrastructure_manifest)
        != input_root / "wmi-infrastructure-manifest.json"
        or _lexical_absolute(args.provenance)
        != input_root / ".peano-source-provenance.tsv"
        or run_root != expected_run_root
    ):
        raise A23AWMIError("execute paths differ from the immutable snapshot layout")
    _safe_parent(source_root / "sentinel")
    source_metadata = source_root.lstat()
    if stat.S_ISLNK(source_metadata.st_mode) or not stat.S_ISDIR(source_metadata.st_mode):
        raise A23AWMIError("snapshot source root is linked or not a directory")
    _safe_parent(run_root)
    if run_root.exists() or run_root.is_symlink():
        raise A23AWMIError("A2.3a run directory already exists")
    run_root.parent.mkdir(parents=True, exist_ok=True)
    run_root.mkdir(mode=0o700)
    execution_path = run_root / "execution-receipt.json"
    started_at = _utc_now()
    process_records: list[dict[str, object]] = []
    status = "unknown"
    classification = "infrastructure-validation-failed"
    error: dict[str, str] | None = None
    evidence: dict[str, object] = {}
    resources: dict[str, object] | None = None
    runtime: dict[str, object] | None = None
    source: dict[str, object] = {}
    try:
        runtime = _assert_runtime()
        resources = _resource_record(os.environ)
        job_id = job_id_early
        commit = _require_digest(os.environ.get("PEANO_A23A_GIT_COMMIT", ""), kind="sha1")
        tree = _require_digest(os.environ.get("PEANO_A23A_GIT_TREE", ""), kind="sha1")
        snapshot_sha = snapshot_sha_early
        source_state_sha = _require_digest(os.environ.get("PEANO_A23A_SOURCE_STATE_SHA256", ""))
        git_receipt_sha = _require_digest(os.environ.get("PEANO_A23A_GIT_RECEIPT_SHA256", ""))
        provenance_sha = _require_digest(os.environ.get("PEANO_A23A_PROVENANCE_SHA256", ""))
        infrastructure_sha = _require_digest(
            os.environ.get("PEANO_A23A_INFRASTRUCTURE_SHA256", "")
        )
        source_state, source_state_record = _validate_deposited_json(
            args.source_state,
            expected_sha256=source_state_sha,
            expected_format=FORMAT_SOURCE_STATE,
        )
        git_receipt, git_receipt_record = _validate_deposited_json(
            args.git_receipt,
            expected_sha256=git_receipt_sha,
        )
        infrastructure, infrastructure_record = _validate_deposited_json(
            args.infrastructure_manifest,
            expected_sha256=infrastructure_sha,
            expected_format=FORMAT_INFRASTRUCTURE,
        )
        provenance_record = _validate_provenance(
            args.provenance, commit=commit, expected_sha256=provenance_sha
        )
        source_state_raw = _read_stable_file(
            args.source_state, limit=MAX_JSON_BYTES, allow_empty=False
        )
        _validate_source_state_document(
            source_state,
            raw=source_state_raw,
            source_root=source_root,
            commit=commit,
            tree=tree,
        )
        _validate_git_receipt_document(
            git_receipt,
            source_root=source_root,
            source_state=source_state,
            source_state_raw=source_state_raw,
            commit=commit,
            tree=tree,
        )
        _validate_infrastructure_manifest(
            infrastructure,
            source_root=source_root,
            commit=commit,
            tree=tree,
        )
        source = {
            "git_commit": commit,
            "git_receipt": git_receipt_record,
            "git_tree": tree,
            "infrastructure_manifest": infrastructure_record,
            "provenance": provenance_record,
            "snapshot_sha256": snapshot_sha,
            "source_state": source_state_record,
        }
        python_path = str(Path(sys.executable))
        producer_paths = (run_root / "candidate-hashseed-0.json", run_root / "candidate-hashseed-1.json")
        for seed, output in enumerate(producer_paths):
            argv = (
                python_path,
                "-B",
                "-P",
                "-s",
                "-S",
                "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
                "--producer-source-state",
                str(args.source_state),
                "--output",
                str(output),
            )
            record = _run_process(
                role=f"producer-{seed}",
                argv=argv,
                cwd=source_root,
                run_root=run_root,
                hash_seed=seed,
                timeout_seconds=PRODUCER_TIMEOUT_SECONDS,
            )
            process_records.append(record)
            outcome = _process_outcome(record)
            if outcome != "passed":
                status = outcome
                classification = f"{record['role']}-{outcome}"
                raise RuntimeError(classification)

        first_raw = _read_stable_file(
            producer_paths[0], limit=MAX_JSON_BYTES, allow_empty=False
        )
        second_raw = _read_stable_file(
            producer_paths[1], limit=MAX_JSON_BYTES, allow_empty=False
        )
        if first_raw != second_raw:
            status = "failed"
            classification = "producer-byte-divergence"
            raise RuntimeError(classification)
        try:
            candidate_document, candidate_raw = _strict_json(producer_paths[0])
        except A23AWMIError:
            status = "unknown"
            classification = "incomplete-candidate-artifact-unknown"
            raise
        try:
            candidate_document, candidate_record = _validate_candidate_document(
                candidate_document,
                raw=candidate_raw,
                filename=producer_paths[0].name,
                source_state=source_state,
            )
        except A23AWMIError:
            status = "failed"
            classification = "complete-candidate-contract-mismatch"
            raise
        second_sha, second_bytes = _sha256_file(producer_paths[1], limit=MAX_JSON_BYTES)
        if second_sha != candidate_record["sha256"] or second_bytes != candidate_record["bytes"]:
            raise A23AWMIError("byte-identical candidate accounting mismatch")

        verifier_path = run_root / "independent-verifier-receipt.json"
        verifier_argv = (
            python_path,
            "-B",
            "-P",
            "-s",
            "-S",
            "scripts/verify_peano_hydra_library_optimizer_comparison_pilot.py",
            "--candidate",
            str(producer_paths[0]),
            "--producer-source-state",
            str(args.source_state),
            "--output",
            str(verifier_path),
        )
        verifier_process = _run_process(
            role="independent-verifier",
            argv=verifier_argv,
            cwd=source_root,
            run_root=run_root,
            hash_seed=2,
            timeout_seconds=VERIFIER_TIMEOUT_SECONDS,
        )
        process_records.append(verifier_process)
        outcome = _process_outcome(verifier_process)
        if outcome != "passed":
            status = "unknown"
            classification = "independent-verifier-process-unknown"
            raise RuntimeError(classification)
        verifier, verifier_raw = _strict_json(verifier_path)
        if verifier.get("status") != "passed":
            status = "failed"
            classification = "complete-independent-verifier-receipt-mismatch"
            raise RuntimeError(classification)
        try:
            _validate_verifier_receipt(
                verifier,
                candidate=candidate_document,
                candidate_raw=first_raw,
                source_state=source_state,
                source_state_raw=source_state_raw,
                source_root=source_root,
            )
        except A23AWMIError:
            status = "failed"
            classification = "complete-independent-verifier-receipt-mismatch"
            raise
        status = "passed"
        classification = "two-producer-byte-identity-and-independent-verification"
        evidence = {
            "candidate": candidate_record,
            "producer_byte_identical": True,
            "producer_hash_seeds": [0, 1],
            "verifier": {
                "bytes": len(verifier_raw),
                "hash_seed": 2,
                "path": verifier_path.name,
                "root_sha256": verifier["root_sha256"],
                "sha256": _sha256_bytes(verifier_raw),
                "status": "passed",
            },
        }
    except RuntimeError as exc:
        if str(exc) != classification:
            error = {"message": str(exc), "type": type(exc).__name__}
    except Exception as exc:  # The failure receipt must survive controlled bad inputs.
        error = {"message": str(exc), "type": type(exc).__name__}
        if status == "passed":
            status = "unknown"
            classification = "post-verification-receipt-unknown"

    payload: dict[str, object] = {
        "authority_claims": _authority_claims(),
        "classification": classification,
        "error": error,
        "evidence": evidence,
        "finished_at": _utc_now(),
        "format": FORMAT_EXECUTION,
        "job_id": os.environ.get("SLURM_JOB_ID"),
        "processes": process_records,
        "requested_resources": resources,
        "runtime": runtime,
        "source": source,
        "started_at": started_at,
        "status": status,
        "v": VERSION,
    }
    receipt = _receipt_with_root(payload)
    _publish_create_only(execution_path, receipt)
    print(f"A2.3a WMI execution status={status} receipt={execution_path}", flush=True)
    return {"passed": 0, "failed": 1, "unknown": 3}[status]


def _build_manifest(args: argparse.Namespace) -> int:
    commit = _require_digest(args.git_commit, kind="sha1")
    tree = _require_digest(args.git_tree, kind="sha1")
    manifest = _infrastructure_manifest(
        repository_root=args.repository_root,
        commit=commit,
        tree=tree,
    )
    _publish_create_only(args.output, manifest)
    print(
        f"A2.3a WMI infrastructure manifest root={manifest['root_sha256']}",
        flush=True,
    )
    return 0


def _parse_sacct(path: Path, expected_job_id: str) -> dict[str, object]:
    raw = _read_stable_file(path, limit=16_384, allow_empty=False)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise A23AWMIError("sacct record is not ASCII") from exc
    lines = [line for line in text.splitlines() if line]
    if len(lines) != 1:
        raise A23AWMIError("sacct must provide exactly one allocation row")
    fields = lines[0].split("|")
    if len(fields) != 9:
        raise A23AWMIError("sacct allocation row has the wrong field count")
    (
        job_id,
        state,
        exit_code,
        derived_exit_code,
        elapsed_raw,
        max_rss,
        requested_memory,
        allocated_cpus,
        node_list,
    ) = fields
    state = state.split(maxsplit=1)[0].rstrip("+")
    if job_id != expected_job_id or not state or EXIT_CODE_RE.fullmatch(exit_code) is None or EXIT_CODE_RE.fullmatch(derived_exit_code) is None:
        raise A23AWMIError("sacct allocation row identity is malformed")
    if not elapsed_raw.isdigit() or not allocated_cpus.isdigit():
        raise A23AWMIError("sacct allocation row resources are malformed")
    return {
        "allocated_cpus": int(allocated_cpus),
        "derived_exit_code": derived_exit_code,
        "elapsed_raw_seconds": int(elapsed_raw),
        "exit_code": exit_code,
        "job_id": job_id,
        "max_rss": max_rss,
        "node_list": node_list,
        "raw_bytes": len(raw),
        "raw_sha256": _sha256_bytes(raw),
        "requested_memory": requested_memory,
        "state": state,
    }


def _validate_file_evidence(
    value: object, *, path: Path, expected_name: str, limit: int
) -> None:
    if type(value) is not dict or set(value) != {"bytes", "path", "sha256"}:
        raise A23AWMIError("execution file evidence is malformed")
    digest, size = _sha256_file(path, limit=limit)
    if (
        value.get("path") != expected_name
        or value.get("bytes") != size
        or value.get("sha256") != digest
    ):
        raise A23AWMIError("execution file evidence differs from live bytes")


def _validate_process_record(
    value: object,
    *,
    run_root: Path,
    role: str,
    hash_seed: int,
    expected_argv: list[str],
    timeout_seconds: int,
    require_success: bool,
) -> None:
    fields = {
        "argv",
        "duration_seconds_millis",
        "environment",
        "finished_at",
        "hash_seed",
        "output_limit_reached",
        "returncode",
        "role",
        "started_at",
        "stderr",
        "stdout",
        "timed_out",
        "timeout_seconds",
    }
    if type(value) is not dict or set(value) != fields:
        raise A23AWMIError("execution process record is malformed")
    if (
        value.get("role") != role
        or value.get("hash_seed") != hash_seed
        or value.get("environment") != _isolated_environment(hash_seed)
        or value.get("argv") != expected_argv
        or value.get("timeout_seconds") != timeout_seconds
        or type(value.get("output_limit_reached")) is not bool
        or type(value.get("duration_seconds_millis")) is not int
        or value["duration_seconds_millis"] < 0
        or type(value.get("started_at")) is not str
        or type(value.get("finished_at")) is not str
    ):
        raise A23AWMIError("execution process identity differs")
    if require_success and (
        value.get("returncode") != 0
        or value.get("timed_out") is not False
        or value.get("output_limit_reached") is not False
    ):
        raise A23AWMIError("passed execution contains an unsuccessful process")
    _validate_file_evidence(
        value.get("stdout"),
        path=run_root / f"{role}.stdout.log",
        expected_name=f"{role}.stdout.log",
        limit=MAX_LOG_BYTES,
    )
    _validate_file_evidence(
        value.get("stderr"),
        path=run_root / f"{role}.stderr.log",
        expected_name=f"{role}.stderr.log",
        limit=MAX_LOG_BYTES,
    )


def _validate_execution_receipt(
    receipt: Mapping[str, object],
    *,
    job_id: str,
    run_root: Path,
    source_root: Path,
    input_root: Path,
    submission: Mapping[str, object],
) -> None:
    body_fields = {
        "authority_claims",
        "classification",
        "error",
        "evidence",
        "finished_at",
        "format",
        "job_id",
        "processes",
        "requested_resources",
        "runtime",
        "source",
        "started_at",
        "status",
        "v",
    }
    if set(receipt) != body_fields | {"root_preimage", "root_sha256"}:
        raise A23AWMIError("execution receipt has the wrong fields")
    body = {key: receipt[key] for key in body_fields}
    preimage = {
        "format": f"{FORMAT_EXECUTION}-root-preimage",
        "payload": body,
        "v": VERSION,
    }
    if receipt.get("root_preimage") != preimage or receipt.get("root_sha256") != _compact_sha256(preimage):
        raise A23AWMIError("execution receipt root is malformed")
    status = receipt.get("status")
    if (
        receipt.get("format") != FORMAT_EXECUTION
        or receipt.get("v") != VERSION
        or receipt.get("job_id") != job_id
        or status not in {"passed", "failed", "unknown"}
        or type(receipt.get("classification")) is not str
        or type(receipt.get("started_at")) is not str
        or type(receipt.get("finished_at")) is not str
        or receipt.get("requested_resources") != EXPECTED_RESOURCES
    ):
        raise A23AWMIError("execution receipt identity is malformed")
    claims = receipt.get("authority_claims")
    if (
        type(claims) is not dict
        or set(claims) != AUTHORITY_CLAIM_KEYS
        or any(value is not False for value in claims.values())
    ):
        raise A23AWMIError("execution receipt grants forbidden authority")
    runtime = receipt.get("runtime")
    if (
        type(runtime) is not dict
        or runtime
        != {
            "dont_write_bytecode": True,
            "executable": PINNED_WMI_PYTHON,
            "implementation": "CPython",
            "machine": "x86_64",
            "no_site": True,
            "pycache_prefix": DISABLED_PYCACHE_PREFIX,
            "python_version": "3.12.12",
            "safe_path": True,
        }
    ):
        raise A23AWMIError("execution receipt runtime identity differs")
    source = receipt.get("source")
    if type(source) is not dict or set(source) != {
        "git_commit",
        "git_receipt",
        "git_tree",
        "infrastructure_manifest",
        "provenance",
        "snapshot_sha256",
        "source_state",
    }:
        raise A23AWMIError("execution receipt source binding is malformed")
    bindings = {
        "git_commit": "git_commit",
        "git_tree": "git_tree",
        "snapshot_sha256": "snapshot_sha256",
    }
    if any(source.get(key) != submission.get(column) for key, column in bindings.items()):
        raise A23AWMIError("execution receipt snapshot identity differs from submission")
    file_bindings = (
        ("source_state", "producer-source-state.json", "source_state_sha256"),
        (
            "git_receipt",
            "producer-git-verification-receipt.json",
            "git_receipt_sha256",
        ),
        (
            "infrastructure_manifest",
            "wmi-infrastructure-manifest.json",
            "infrastructure_sha256",
        ),
    )
    for source_key, filename, submission_key in file_bindings:
        record = source.get(source_key)
        path = input_root / filename
        if type(record) is not dict or set(record) != {"bytes", "path", "sha256"}:
            raise A23AWMIError("execution receipt deposited-file binding is malformed")
        digest, size = _sha256_file(path, limit=MAX_JSON_BYTES)
        if (
            record.get("path") != filename
            or record.get("sha256") != digest
            or record.get("sha256") != submission.get(submission_key)
            or record.get("bytes") != size
        ):
            raise A23AWMIError("execution receipt deposited-file binding differs")
    provenance = source.get("provenance")
    if (
        type(provenance) is not dict
        or set(provenance) != {"git_commit", "git_dirty", "sha256", "sync_timestamp"}
        or provenance.get("git_commit") != submission.get("git_commit")
        or provenance.get("git_dirty") is not False
        or provenance.get("sha256") != submission.get("provenance_sha256")
        or provenance.get("sync_timestamp") != submission.get("sync_timestamp")
    ):
        raise A23AWMIError("execution receipt provenance binding differs")

    # Unknown receipts remain unknown after their rooted identity and source
    # bindings are checked.  They can never promote a collection to passed.
    if status == "unknown":
        return
    classification = receipt["classification"]
    failed_classes = {
        "producer-byte-divergence",
        "complete-candidate-contract-mismatch",
        "complete-independent-verifier-receipt-mismatch",
    }
    if status == "failed" and classification not in failed_classes:
        raise A23AWMIError("execution failed without a complete contradiction class")
    if status == "passed" and (
        classification != "two-producer-byte-identity-and-independent-verification"
        or receipt.get("error") is not None
    ):
        raise A23AWMIError("passed execution classification is malformed")

    python_path = runtime["executable"]
    source_state_path = input_root / "producer-source-state.json"
    candidate_paths = (
        run_root / "candidate-hashseed-0.json",
        run_root / "candidate-hashseed-1.json",
    )
    verifier_path = run_root / "independent-verifier-receipt.json"
    expected_processes = (
        (
            "producer-0",
            0,
            [
                python_path,
                "-B",
                "-P",
                "-s",
                "-S",
                "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
                "--producer-source-state",
                str(source_state_path),
                "--output",
                str(candidate_paths[0]),
            ],
            PRODUCER_TIMEOUT_SECONDS,
        ),
        (
            "producer-1",
            1,
            [
                python_path,
                "-B",
                "-P",
                "-s",
                "-S",
                "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
                "--producer-source-state",
                str(source_state_path),
                "--output",
                str(candidate_paths[1]),
            ],
            PRODUCER_TIMEOUT_SECONDS,
        ),
        (
            "independent-verifier",
            2,
            [
                python_path,
                "-B",
                "-P",
                "-s",
                "-S",
                "scripts/verify_peano_hydra_library_optimizer_comparison_pilot.py",
                "--candidate",
                str(candidate_paths[0]),
                "--producer-source-state",
                str(source_state_path),
                "--output",
                str(verifier_path),
            ],
            VERIFIER_TIMEOUT_SECONDS,
        ),
    )
    processes = receipt.get("processes")
    required_process_count = (
        2
        if status == "failed"
        and classification
        in {"producer-byte-divergence", "complete-candidate-contract-mismatch"}
        else 3
    )
    if type(processes) is not list or len(processes) != required_process_count:
        raise A23AWMIError("complete execution process vector differs")
    for process, (role, seed, argv, timeout) in zip(
        processes, expected_processes[:required_process_count], strict=True
    ):
        _validate_process_record(
            process,
            run_root=run_root,
            role=role,
            hash_seed=seed,
            expected_argv=argv,
            timeout_seconds=timeout,
            require_success=(
                status == "passed"
                or role.startswith("producer-")
                or classification == "complete-independent-verifier-receipt-mismatch"
            ),
        )
    if status == "failed":
        first_raw = _read_stable_file(
            candidate_paths[0], limit=MAX_JSON_BYTES, allow_empty=False
        )
        second_raw = _read_stable_file(
            candidate_paths[1], limit=MAX_JSON_BYTES, allow_empty=False
        )
        if classification == "producer-byte-divergence":
            if first_raw == second_raw:
                raise A23AWMIError("byte-divergence failure has identical candidates")
            return
        if first_raw != second_raw:
            raise A23AWMIError("non-divergence failure has differing producer bytes")
        source_state, source_state_raw = _strict_json(source_state_path)
        if classification == "complete-candidate-contract-mismatch":
            # Parsing/canonicalization failures are incomplete infrastructure
            # evidence and must be downgraded to unknown by the collector.
            _strict_json(candidate_paths[0])
            try:
                _validate_candidate(candidate_paths[0], source_state=source_state)
            except A23AWMIError:
                return
            raise A23AWMIError("candidate-contract failure contains a valid candidate")
        candidate, _candidate_record = _validate_candidate(
            candidate_paths[0], source_state=source_state
        )
        verifier_receipt, verifier_raw = _strict_json(verifier_path)
        try:
            _validate_verifier_receipt(
                verifier_receipt,
                candidate=candidate,
                candidate_raw=first_raw,
                source_state=source_state,
                source_state_raw=source_state_raw,
                source_root=source_root,
            )
        except A23AWMIError:
            return
        raise A23AWMIError("verifier-mismatch failure contains a valid receipt")
    if status != "passed":
        return

    first_raw = _read_stable_file(candidate_paths[0], limit=MAX_JSON_BYTES, allow_empty=False)
    second_raw = _read_stable_file(candidate_paths[1], limit=MAX_JSON_BYTES, allow_empty=False)
    if first_raw != second_raw:
        raise A23AWMIError("passed execution producer bytes differ")
    source_state, source_state_raw = _strict_json(source_state_path)
    candidate, candidate_record = _validate_candidate(
        candidate_paths[0], source_state=source_state
    )
    verifier_receipt, verifier_raw = _strict_json(verifier_path)
    _validate_verifier_receipt(
        verifier_receipt,
        candidate=candidate,
        candidate_raw=first_raw,
        source_state=source_state,
        source_state_raw=source_state_raw,
        source_root=source_root,
    )
    evidence = receipt.get("evidence")
    if type(evidence) is not dict or set(evidence) != {
        "candidate",
        "producer_byte_identical",
        "producer_hash_seeds",
        "verifier",
    }:
        raise A23AWMIError("passed execution evidence is malformed")
    verifier_binding = evidence.get("verifier")
    expected_verifier_binding = {
        "bytes": len(verifier_raw),
        "hash_seed": 2,
        "path": verifier_path.name,
        "root_sha256": verifier_receipt["root_sha256"],
        "sha256": _sha256_bytes(verifier_raw),
        "status": "passed",
    }
    if (
        evidence.get("candidate") != candidate_record
        or evidence.get("producer_byte_identical") is not True
        or evidence.get("producer_hash_seeds") != [0, 1]
        or verifier_binding != expected_verifier_binding
    ):
        raise A23AWMIError("passed execution evidence differs from live artifacts")


def _optional_file_record(path: Path, *, limit: int) -> dict[str, object]:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parent.parts[1:]:
        current = current / component
        try:
            parent_metadata = current.lstat()
        except FileNotFoundError:
            return {"exists": False, "path": path.name}
        except OSError as exc:
            raise A23AWMIError(
                f"cannot inspect optional collection path: {path}"
            ) from exc
        if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(
            parent_metadata.st_mode
        ):
            raise A23AWMIError(
                f"optional collection path has an unsafe ancestor: {path}"
            )
    try:
        metadata = absolute.lstat()
    except FileNotFoundError:
        return {"exists": False, "path": path.name}
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise A23AWMIError(f"collection input is not one regular file: {path}")
    digest, size = _sha256_file(path, limit=limit)
    return {"bytes": size, "exists": True, "path": path.name, "sha256": digest}


def _collection_optional_record(
    path: Path, *, limit: int
) -> tuple[dict[str, object], str | None]:
    """Record optional terminal evidence without following rejected paths."""

    try:
        return _optional_file_record(path, limit=limit), None
    except A23AWMIError as exc:
        return (
            {
                "exists": None,
                "path": path.name,
                "read_status": "rejected-without-following",
            },
            str(exc),
        )


def _one_tsv_row(path: Path, *, fields: int, label: str) -> tuple[list[str], bytes]:
    raw = _read_stable_file(path, limit=16_384, allow_empty=False)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise A23AWMIError(f"{label} is not ASCII") from exc
    if text.count("\n") != 1 or not text.endswith("\n"):
        raise A23AWMIError(f"{label} must be one terminated row")
    values = text[:-1].split("\t")
    if len(values) != fields:
        raise A23AWMIError(f"{label} has the wrong field count")
    return values, raw


def _parse_submission_record(path: Path, job_id: str) -> dict[str, object]:
    values, raw = _one_tsv_row(path, fields=16, label="submission record")
    (
        timestamp,
        recorded_job,
        snapshot,
        commit,
        tree,
        source_state,
        git_receipt,
        infrastructure,
        provenance,
        sync_timestamp,
        partition,
        ntasks,
        cpus,
        memory,
        time_limit,
        sbatch,
    ) = values
    for value in (snapshot, source_state, git_receipt, infrastructure, provenance, sbatch):
        _require_digest(value)
    _require_digest(commit, kind="sha1")
    _require_digest(tree, kind="sha1")
    if (
        recorded_job != job_id
        or TIMESTAMP_RE.fullmatch(timestamp) is None
        or TIMESTAMP_RE.fullmatch(sync_timestamp) is None
        or partition != "cpu_idle"
        or (ntasks, cpus, memory, time_limit) != ("1", "1", "4096", "00:15:00")
    ):
        raise A23AWMIError("submission record identity or resources differ")
    return {
        "artifact_bytes": len(raw),
        "artifact_sha256": _sha256_bytes(raw),
        "cpus_per_task": 1,
        "git_commit": commit,
        "git_receipt_sha256": git_receipt,
        "git_tree": tree,
        "infrastructure_sha256": infrastructure,
        "job_id": recorded_job,
        "memory_mib": 4096,
        "ntasks": 1,
        "partition": partition,
        "provenance_sha256": provenance,
        "sbatch_sha256": sbatch,
        "snapshot_sha256": snapshot,
        "source_state_sha256": source_state,
        "submission_timestamp": timestamp,
        "sync_timestamp": sync_timestamp,
        "time_limit": time_limit,
    }


def _parse_deposit_record(
    path: Path, *, submission: Mapping[str, object]
) -> dict[str, object]:
    values, raw = _one_tsv_row(path, fields=9, label="deposit record")
    (
        snapshot,
        archive_bytes,
        commit,
        tree,
        source_state,
        git_receipt,
        infrastructure,
        provenance,
        sync_timestamp,
    ) = values
    if not archive_bytes.isdigit() or archive_bytes.startswith("0"):
        raise A23AWMIError("deposit archive byte count is malformed")
    expected = (
        ("snapshot_sha256", snapshot),
        ("git_commit", commit),
        ("git_tree", tree),
        ("source_state_sha256", source_state),
        ("git_receipt_sha256", git_receipt),
        ("infrastructure_sha256", infrastructure),
        ("provenance_sha256", provenance),
        ("sync_timestamp", sync_timestamp),
    )
    if any(submission.get(key) != value for key, value in expected):
        raise A23AWMIError("immutable deposit differs from the submission record")
    return {
        "archive_bytes": int(archive_bytes),
        "artifact_bytes": len(raw),
        "artifact_sha256": _sha256_bytes(raw),
        "git_commit": commit,
        "git_receipt_sha256": git_receipt,
        "git_tree": tree,
        "infrastructure_sha256": infrastructure,
        "provenance_sha256": provenance,
        "snapshot_sha256": snapshot,
        "source_state_sha256": source_state,
        "sync_timestamp": sync_timestamp,
    }


def _collection_status(
    *,
    accounting: Mapping[str, object],
    execution: Mapping[str, object] | None,
    stdout_exists: bool,
    stderr_exists: bool,
) -> tuple[str, str]:
    state = accounting["state"]
    if state not in TERMINAL_STATES:
        raise A23AWMIError(f"Slurm job is not terminal: {state}")
    if state in RESOURCE_OR_EXTERNAL_STATES:
        return "unknown", "scheduler-resource-timeout-or-external-termination"
    if (
        accounting.get("allocated_cpus") != 1
        or accounting.get("requested_memory") not in ACCEPTED_SACCT_REQUESTED_MEMORY
        or type(accounting.get("elapsed_raw_seconds")) is not int
        or accounting["elapsed_raw_seconds"] > EXPECTED_RESOURCES["time_limit_seconds"]
    ):
        return "unknown", "scheduler-resource-contract-mismatch"
    if execution is None:
        return "unknown", "terminal-job-missing-execution-receipt"
    if not stdout_exists or not stderr_exists:
        return "unknown", "terminal-job-missing-scheduler-log"
    execution_status = execution.get("status")
    if execution_status not in {"passed", "failed", "unknown"}:
        return "unknown", "malformed-execution-status"
    clean_exit = accounting["exit_code"] == "0:0" and accounting["derived_exit_code"] == "0:0"
    if state == "COMPLETED" and clean_exit and execution_status == "passed":
        return "passed", "completed-and-independently-verified"
    if execution_status == "failed" and state in {"COMPLETED", "FAILED", "SPECIAL_EXIT"}:
        return "failed", "controlled-producer-or-verifier-failure"
    return "unknown", "scheduler-execution-evidence-conflict-or-unknown"


def _collect(args: argparse.Namespace) -> int:
    job_id = _require_job_id(args.job_id)
    submission = _parse_submission_record(args.submission_record, job_id)
    deposit = _parse_deposit_record(args.deposit_record, submission=submission)
    sbatch_sha, sbatch_bytes = _sha256_file(args.sbatch_file, limit=1_000_000)
    if sbatch_sha != submission["sbatch_sha256"]:
        raise A23AWMIError("live sbatch file differs from the submitted identity")
    snapshot_root = WMI_REMOTE_ROOT / str(submission["snapshot_sha256"])
    source_root = _lexical_absolute(args.source_root)
    input_root = _lexical_absolute(args.input_root)
    run_root = _lexical_absolute(args.run_root)
    if (
        source_root != snapshot_root / "source"
        or input_root != snapshot_root / "inputs"
        or run_root != snapshot_root / "runs" / job_id
        or _lexical_absolute(args.execution_receipt)
        != run_root / "execution-receipt.json"
        or _lexical_absolute(args.deposit_record) != snapshot_root / "deposit.tsv"
        or _lexical_absolute(args.sbatch_file)
        != source_root / "slurm" / "peano_wmi_hydra_a23a_pilot.sbatch"
        or _lexical_absolute(args.output)
        != snapshot_root / "collections" / f"job-{job_id}.json"
        or _lexical_absolute(args.submission_record).parent
        != snapshot_root / "collections"
        or not _lexical_absolute(args.submission_record).name.startswith(
            f".submission-{job_id}."
        )
        or _lexical_absolute(args.sacct_record).parent
        != snapshot_root / "collections"
        or not _lexical_absolute(args.sacct_record).name.startswith(
            f".sacct-{job_id}."
        )
        or _lexical_absolute(args.stdout)
        != snapshot_root / "logs" / f"peano-hydra-a23a-{job_id}.out"
        or _lexical_absolute(args.stderr)
        != snapshot_root / "logs" / f"peano-hydra-a23a-{job_id}.err"
    ):
        raise A23AWMIError("collector paths differ from the submitted immutable snapshot")
    accounting = _parse_sacct(args.sacct_record, job_id)
    execution: dict[str, object] | None = None
    execution_validation: dict[str, object]
    execution_record, execution_record_error = _collection_optional_record(
        args.execution_receipt, limit=MAX_JSON_BYTES
    )
    if execution_record_error is not None:
        execution_validation = {
            "error": execution_record_error,
            "status": "rejected-as-unknown",
        }
    elif execution_record["exists"]:
        try:
            candidate_execution, raw = _strict_json(args.execution_receipt)
            _validate_execution_receipt(
                candidate_execution,
                job_id=job_id,
                run_root=run_root,
                source_root=source_root,
                input_root=input_root,
                submission=submission,
            )
            execution = candidate_execution
            execution_record["sha256"] = _sha256_bytes(raw)
            execution_record["bytes"] = len(raw)
            execution_record["root_sha256"] = execution["root_sha256"]
            execution_validation = {"status": "accepted"}
        except A23AWMIError as exc:
            execution = None
            execution_validation = {
                "error": str(exc),
                "status": "rejected-as-unknown",
            }
    else:
        execution_validation = {
            "error": "execution receipt is absent",
            "status": "missing-as-unknown",
        }
    log_rejections: dict[str, str] = {}
    log_records: dict[str, dict[str, object]] = {}
    for stream, path in (("stdout", args.stdout), ("stderr", args.stderr)):
        record, rejection = _collection_optional_record(path, limit=MAX_LOG_BYTES)
        log_records[stream] = record
        if rejection is not None:
            log_rejections[stream] = rejection
    stdout_record = log_records["stdout"]
    stderr_record = log_records["stderr"]
    status, classification = _collection_status(
        accounting=accounting,
        execution=execution,
        stdout_exists=bool(stdout_record["exists"]),
        stderr_exists=bool(stderr_record["exists"]),
    )
    if execution_record_error is not None:
        classification = "terminal-job-rejected-execution-receipt"
    elif log_rejections:
        classification = "terminal-job-rejected-scheduler-log"
    payload = {
        "accounting": accounting,
        "authority_claims": _authority_claims(),
        "classification": classification,
        "collected_at": _utc_now(),
        "execution_receipt": execution_record,
        "execution_validation": execution_validation,
        "format": FORMAT_COLLECTION,
        "job_id": job_id,
        "scheduler_logs": {
            "rejections": log_rejections,
            "stderr": stderr_record,
            "stdout": stdout_record,
        },
        "source_deposit": deposit,
        "submission": submission,
        "submitted_sbatch": {
            "bytes": sbatch_bytes,
            "path": args.sbatch_file.name,
            "sha256": sbatch_sha,
        },
        "status": status,
        "v": VERSION,
    }
    _publish_create_only(args.output, _receipt_with_root(payload))
    print(f"A2.3a WMI collection status={status} receipt={args.output}", flush=True)
    return {"passed": 0, "failed": 1, "unknown": 3}[status]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    manifest = subparsers.add_parser(
        "build-infrastructure-manifest",
        help="create the exact clean-snapshot infrastructure source vector",
    )
    manifest.add_argument("--repository-root", type=Path, required=True)
    manifest.add_argument("--git-commit", required=True)
    manifest.add_argument("--git-tree", required=True)
    manifest.add_argument("--output", type=Path, required=True)
    execute = subparsers.add_parser("execute", help="run the isolated three-process pilot")
    execute.add_argument("--source-root", type=Path, required=True)
    execute.add_argument("--run-root", type=Path, required=True)
    execute.add_argument("--source-state", type=Path, required=True)
    execute.add_argument("--git-receipt", type=Path, required=True)
    execute.add_argument("--infrastructure-manifest", type=Path, required=True)
    execute.add_argument("--provenance", type=Path, required=True)
    collect = subparsers.add_parser("collect", help="bind terminal Slurm and log evidence")
    collect.add_argument("--job-id", required=True)
    collect.add_argument("--submission-record", type=Path, required=True)
    collect.add_argument("--deposit-record", type=Path, required=True)
    collect.add_argument("--sbatch-file", type=Path, required=True)
    collect.add_argument("--source-root", type=Path, required=True)
    collect.add_argument("--input-root", type=Path, required=True)
    collect.add_argument("--run-root", type=Path, required=True)
    collect.add_argument("--sacct-record", type=Path, required=True)
    collect.add_argument("--execution-receipt", type=Path, required=True)
    collect.add_argument("--stdout", type=Path, required=True)
    collect.add_argument("--stderr", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build-infrastructure-manifest":
        return _build_manifest(args)
    if args.command == "execute":
        return _execute(args)
    if args.command == "collect":
        return _collect(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except A23AWMIError as exc:
        raise SystemExit(str(exc)) from None
