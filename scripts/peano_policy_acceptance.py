#!/usr/bin/env python3
"""Run, validate, and score the preregistered model-v2 acceptance experiment.

Only ``run-primary`` loads model weights, once.  Validation, dataset audit, and
scoring are model-free: they identify the closed adapter artifacts, inspect
already-produced reports, and independently replay every counted tactic script.
The preregistration contains no reference proofs.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Callable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

DEFAULT_MANIFEST = (
    REPOSITORY_ROOT / "training" / "peano_policy" / "acceptance_v2.json"
)
MANIFEST_FORMAT = "peano-policy-acceptance-preregistration"
REPORT_FORMAT = "peano-policy-acceptance-report"
MANIFEST_VERSION = 1
REPORT_VERSION = 1
EXPECTED_MANIFEST_SHA256 = (
    "5e0b2ec865858750c11f10cd5c102405633605614b2aa682c71ffab9ee134e61"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_JOB_ID_RE = re.compile(r"[0-9]+")
PRIMARY_SESSION_FORMAT = "peano-policy-primary-session"
PRIMARY_SESSION_VERSION = 1
PRIMARY_SESSION_DIRECTORY = "acceptance-v2-primary"
PRIMARY_SESSION_LEDGER = "primary-session.json"
PRIMARY_SESSION_OPEN = "primary-session-open.json"
TRAINING_MANIFEST = "training-manifest.json"
RUN_IDENTITY = "run-identity.json"
DATASET_MANIFEST = "manifest.json"
DATASET_ATTESTATION = "attestation.json"
DATASET_SOURCE_MANIFEST = "source-manifest.json"
DATASET_SPLITS = ("train", "val", "test")
WMI_PROJECT_ROOT = "/work/bnaskrecki/peano-lab-training"
WMI_SUBMISSION_LEDGER = "logs/submissions.tsv"
WMI_PROOF_REQUEST_LEDGER = "logs/proof-requests.tsv"
WMI_PRETRAIN_DATA_AUDIT = "logs/peano-wmi-v2-acceptance-data-pretrain.json"
WMI_DATASET_GENERATOR_SCRIPT = "slurm/peano_wmi_prepare_v2_training.sbatch"
WMI_PREPARE_SCRIPT = "slurm/peano_wmi_finalize_v2_training.sbatch"
WMI_TRAIN_SCRIPT = "slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch"
WMI_EVAL_SCRIPT = "slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch"
WMI_PRIMARY_SCRIPT = "slurm/peano_wmi_acceptance_primary.sbatch"
WMI_SCORER_SCRIPT = "slurm/peano_wmi_acceptance_scorer.sbatch"
WMI_HELDOUT_REPORT = (
    "results/peano-policy/qwen3-1.7b-lora-v2-heavy/"
    "heldout-search-wmi-b16-c8-d32.json"
)
WMI_FINAL_REPORT = (
    "results/peano-policy/qwen3-1.7b-lora-v2-heavy/acceptance-v2-report.json"
)
WMI_SUBMISSION_FIELDS = (
    "timestamp",
    "job_id",
    "script",
    "dependency_job_id",
    "workdir",
    "git_commit",
    "git_dirty",
    "sync_timestamp",
    "script_sha256",
)
WMI_TRAINING_SCRIPTS = (
    WMI_PREPARE_SCRIPT,
    WMI_TRAIN_SCRIPT,
    WMI_EVAL_SCRIPT,
)
WMI_ACCEPTANCE_SCRIPTS = (WMI_PRIMARY_SCRIPT, WMI_SCORER_SCRIPT)
WMI_TRAINING_SCRIPT_SHA256 = {
    WMI_PREPARE_SCRIPT: "e9dd6a75c40022a2b0512d97785ce5a70e0fde63a22f320fe26596aeca4ef82d",
    WMI_TRAIN_SCRIPT: "aa58bad45672b39d16fa1f870109e935ecf7099d524c19d81c7d7769fed02cdb",
    WMI_EVAL_SCRIPT: "6b149e335201485c63e9acc7709c668737c997e9be03bd937b88082a277b3ece",
}
WMI_DATASET_GENERATOR_SCRIPT_SHA256 = (
    "477efcf20824e19e18728d9808cdfe27b9fdc331788f0e2509c296c341889401"
)
WMI_DATASET_GENERATOR_EVIDENCE = {
    "job_id": "171533",
    "state": "FAILED",
    "exit_code": "2:0",
    "elapsed": "02:59:27",
    "start": "2026-07-28T18:25:41",
    "end": "2026-07-28T21:25:08",
    "stdout": {
        "path": "logs/peano-wmi-v2-prepare-171533.out",
        "sha256": "cfba491bfcf9e16af1a71a4914c9030a704122b31e4ba7154ec273985317f5f4",
    },
    "stderr": {
        "path": "logs/peano-wmi-v2-prepare-171533.err",
        "sha256": "567446f26aa9ee5ac22b4363b8405b8e2057c7e441b2c991528b029363d19a3d",
    },
}
WMI_TRAINING_SUPPORT_SHA256 = (
    "410cecfc9a2f007d7ad43058d9172605de0c4f23fae43e4e83e6629420bae2da"
)
PRIMARY_SEMANTIC_SCRIPT_FILES = (
    "scripts/eval_peano_policy.py",
    "scripts/eval_trained_peano_policy.py",
    "scripts/peano_policy_proof_request.py",
    "scripts/peano_policy_repl.py",
)
PRIMARY_SEMANTIC_PROTOCOL_FILES = (
    "scripts/submit_wmi_slurm_job.sh",
    "scripts/verify_wmi_submission_predecessor.py",
    "scripts/wmi_common.sh",
    "scripts/wmi_job_environment.sh",
    "scripts/wmi_sync_project.sh",
    "slurm/peano_wmi_finalize_v2_training.sbatch",
    "slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch",
    "slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch",
    "slurm/peano_wmi_acceptance_primary.sbatch",
    "slurm/peano_wmi_acceptance_scorer.sbatch",
)
PRIMARY_SEMANTIC_TRAINING_REVIEWED_NONCODE_FILES = (
    "training/peano_policy/README.md",
    "training/peano_policy/base-model-snapshot-v1.json",
    "training/peano_policy/configs/pythagoras_4b_pilot.toml",
    "training/peano_policy/configs/qwen3_1_7b_smoke.toml",
    "training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml",
    "training/peano_policy/configs/qwen3_1_7b_wmi_smoke.toml",
    "training/peano_policy/configs/qwen3_4b_pilot.toml",
    "training/peano_policy/requirements-helios.lock",
    "training/peano_policy/requirements-wmi-overlay.lock",
    "training/peano_policy/wmi-base-v1.json",
)
# This one file cannot be part of the digest that it contains.  It is still
# required to be a plain file here, and validate_manifest() independently pins
# its exact bytes with EXPECTED_MANIFEST_SHA256 before this closure is trusted.
PRIMARY_SEMANTIC_EXTERNALLY_SEALED_FILES = (
    "training/peano_policy/acceptance_v2.json",
)
WMI_RUNTIME_PACKAGES = {
    "accelerate": "1.8.1",
    "certifi": "2025.11.12",
    "charset-normalizer": "3.4.4",
    "filelock": "3.20.1",
    "fsspec": "2025.5.1",
    "hf-xet": "1.1.5",
    "huggingface-hub": "0.33.4",
    "idna": "3.11",
    "Jinja2": "3.1.6",
    "MarkupSafe": "3.0.3",
    "mpmath": "1.3.0",
    "networkx": "3.6.1",
    "numpy": "2.3.5",
    "packaging": "25.0",
    "peft": "0.16.0",
    "pip": "25.2",
    "psutil": "7.1.3",
    "PyYAML": "6.0.3",
    "regex": "2024.11.6",
    "requests": "2.32.5",
    "safetensors": "0.5.3",
    "setuptools": "80.9.0",
    "sympy": "1.13.1",
    "tokenizers": "0.21.2",
    "tomli": "2.3.0",
    "torch": "2.5.1",
    "tqdm": "4.67.1",
    "transformers": "4.53.3",
    "typing-extensions": "4.15.0",
    "urllib3": "2.6.2",
    "torchaudio": "2.5.1",
    "torchvision": "0.20.1",
    "triton": "3.1.0",
}


class AcceptanceError(ValueError):
    """An input is not the exact preregistered experiment."""


@dataclass(frozen=True, slots=True)
class GoalOutcome:
    """One structurally checked primary attempt."""

    goal_id: str
    category: str
    proved: bool
    retrieval_hit: bool
    kernel_checked: bool
    status: str
    command_count: int
    proof_nodes: int | None

    @property
    def counted_success(self) -> bool:
        if not self.kernel_checked:
            return False
        return self.retrieval_hit if self.category == "retrieval" else self.proved


@dataclass(frozen=True, slots=True)
class AdapterAuthority:
    """Model-free identity of one closed, attested adapter directory."""

    directory: Path
    manifest: dict[str, object]
    identity: dict[str, str]


@dataclass(frozen=True, slots=True)
class PrimarySession:
    """One complete non-resumable interactive acceptance run."""

    ledger: dict[str, object]
    reports: tuple[dict[str, object], ...]


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AcceptanceError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise AcceptanceError(f"non-finite JSON number {value!r}")


def _read_json(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, AcceptanceError) as exc:
        raise AcceptanceError(f"cannot read {path}: {exc}") from None
    if type(value) is not dict:
        raise AcceptanceError(f"{path} must contain one JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise AcceptanceError(f"cannot hash {path}: {exc}") from None
    return digest.hexdigest()


def _sha256_json(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_json_line(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload + b"\n").hexdigest()


def _json_copy(value: object) -> object:
    """Detach tuples/dataclasses through the canonical JSON value domain."""

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
        raise AcceptanceError(f"value is not canonical JSON: {exc}") from None


def _has_path_suffix(value: object, relative: object) -> bool:
    """Compare a host-specific recorded path to one repository-relative path."""

    if type(value) is not str or type(relative) is not str:
        return False
    candidate = value.replace("\\", "/")
    expected = relative.replace("\\", "/").strip("/")
    return candidate == expected or candidate.endswith("/" + expected)


def _subject_adapter_directory(manifest: Mapping[str, object]) -> Path:
    subject = _mapping(manifest.get("subject"), "subject")
    relative = _text(subject.get("adapter_directory"), "subject.adapter_directory")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise AcceptanceError("subject adapter directory is not repository-relative")
    return (REPOSITORY_ROOT / path).resolve(strict=False)


def _plain_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise AcceptanceError(f"{label} must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AcceptanceError(f"{label} is unavailable: {exc}") from None
    if not resolved.is_dir():
        raise AcceptanceError(f"{label} must be a directory")
    return resolved


def _plain_file(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise AcceptanceError(f"{label} must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AcceptanceError(f"{label} is unavailable: {exc}") from None
    if not resolved.is_file():
        raise AcceptanceError(f"{label} must be a regular file")
    return resolved


def _utc_timestamp(value: object, label: str) -> datetime:
    text_value = _text(value, label)
    if not text_value.endswith("Z"):
        raise AcceptanceError(f"{label} must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(text_value[:-1] + "+00:00")
    except ValueError:
        raise AcceptanceError(f"{label} is not an ISO-8601 timestamp") from None
    if parsed.tzinfo != timezone.utc:
        raise AcceptanceError(f"{label} is not UTC")
    return parsed


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _file_timestamps(path: Path) -> tuple[datetime, datetime]:
    try:
        stat = path.stat()
    except OSError as exc:
        raise AcceptanceError(f"cannot stat sealed file {path}: {exc}") from None
    return (
        datetime.fromtimestamp(stat.st_mtime, timezone.utc),
        datetime.fromtimestamp(stat.st_ctime, timezone.utc),
    )


def _validate_pretraining_report_time(
    path: Path,
    created_value: object,
    training_timestamp: object,
) -> None:
    created = _utc_timestamp(created_value, "pre-training audit created_at")
    try:
        training_submitted = datetime.fromisoformat(
            _text(training_timestamp, "training submission timestamp").replace(
                "Z", "+00:00"
            )
        )
    except ValueError:
        raise AcceptanceError("training submission timestamp is malformed") from None
    if training_submitted.tzinfo is None:
        raise AcceptanceError("training submission timestamp is timezone-naive")
    modified, changed = _file_timestamps(path)
    latest_expected_write = created.timestamp() + 300
    if (
        created >= training_submitted
        or modified >= training_submitted
        or changed >= training_submitted
        or not created.timestamp() <= modified.timestamp() <= latest_expected_write
        or not created.timestamp() <= changed.timestamp() <= latest_expected_write
    ):
        raise AcceptanceError(
            "data contamination audit file does not predate training"
        )


def _mapping(value: object, label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise AcceptanceError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> list[object]:
    if type(value) is not list:
        raise AcceptanceError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise AcceptanceError(f"{label} must be non-empty text")
    return value


def _canonical_statement(source: object, label: str) -> str:
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula

    text = _text(source, label)
    try:
        formula, free_names = parse_formula_with_names(text)
    except (TypeError, ValueError, RecursionError) as exc:
        raise AcceptanceError(f"{label} is not a PA formula: {exc}") from None
    if free_names:
        raise AcceptanceError(
            f"{label} is not closed; free names: {', '.join(free_names)}"
        )
    return pretty_formula(formula, list(free_names))


def _goal_records(manifest: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    rows = _sequence(manifest.get("goals"), "goals")
    records = tuple(
        _mapping(row, f"goals[{index}]") for index, row in enumerate(rows)
    )
    if len(records) != 16:
        raise AcceptanceError("the preregistration must contain exactly 16 goals")
    ids = [_text(row.get("id"), "goal id") for row in records]
    if len(ids) != len(set(ids)):
        raise AcceptanceError("goal ids must be unique")
    return records


def _exact_int_mapping(
    value: object,
    expected: Mapping[str, int],
    label: str,
) -> None:
    record = _mapping(value, label)
    if record != dict(expected):
        raise AcceptanceError(f"{label} differs from the preregistered budget")


def _repository_path(relative: str, label: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise AcceptanceError(f"{label} is not repository-relative")
    return REPOSITORY_ROOT / path


def _current_protocol_file_sha256(relative: str, label: str) -> str:
    if (
        Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or not relative.startswith(("scripts/", "slurm/"))
    ):
        raise AcceptanceError(f"{label} is outside the protocol")
    return _sha256_file(_plain_file(REPOSITORY_ROOT / relative, label))


def _current_composite_script_sha256(script: str) -> str:
    job_hash = _current_protocol_file_sha256(script, "acceptance job script")
    support_hash = _current_protocol_file_sha256(
        "scripts/wmi_job_environment.sh", "acceptance support script"
    )
    return hashlib.sha256(
        f"{job_hash}\n{support_hash}\n".encode("ascii")
    ).hexdigest()


def _validate_source_identity(
    value: object,
    contract: Mapping[str, object],
    label: str,
) -> dict[str, object]:
    """Validate the sealed source inventory without requiring a Git checkout."""

    source = _mapping(value, label)
    files = _mapping(source.get("files"), f"{label}.files")
    if set(source) != {"sha256", "files"}:
        raise AcceptanceError(f"{label} has unexpected fields")
    if len(files) != contract.get("source_file_count"):
        raise AcceptanceError(f"{label} has the wrong file count")
    for relative, digest in files.items():
        if type(relative) is not str or type(digest) is not str or not relative:
            raise AcceptanceError(f"{label} contains an invalid file identity")
        path = Path(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "__pycache__" in path.parts
            or path.name == TRAINING_MANIFEST
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise AcceptanceError(f"{label} contains an invalid file identity")
    if (
        source.get("sha256") != contract.get("source_sha256")
        or _sha256_json(files) != source.get("sha256")
    ):
        raise AcceptanceError(f"{label} does not match the sealed source digest")
    return source


def _closed_tree_entries(
    root: Path, label: str
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Enumerate one source tree with lstat, never following an entry.

    ``Path.rglob`` silently omits symlinked directories on some Python
    versions.  That is unsuitable for a pre-import seal: an omitted symlink or
    device can change what a loader sees without changing the recorded digest.
    """

    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise AcceptanceError(f"{label} is unavailable: {exc}") from None
    if stat.S_ISLNK(root_stat.st_mode):
        raise AcceptanceError(f"{label} must not be a symlink")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise AcceptanceError(f"{label} must be a directory")

    directories: list[Path] = []
    regular_files: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as scanned:
                entries = sorted(scanned, key=lambda entry: entry.name)
        except OSError as exc:
            raise AcceptanceError(f"cannot enumerate {label}: {exc}") from None
        for entry in entries:
            path = Path(entry.path)
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise AcceptanceError(
                    f"cannot inspect {label} entry {path}: {exc}"
                ) from None
            mode = entry_stat.st_mode
            if stat.S_ISLNK(mode):
                raise AcceptanceError(f"{label} contains symlink {path.name}")
            if stat.S_ISDIR(mode):
                directories.append(path)
                pending.append(path)
            elif stat.S_ISREG(mode):
                regular_files.append(path)
            else:
                raise AcceptanceError(f"{label} contains a special file {path.name}")
    return tuple(sorted(directories)), tuple(sorted(regular_files))


def _inert_external_bytecode_cache_files(
    root: Path,
    directories: Sequence[Path],
    files: Sequence[Path],
    label: str,
) -> frozenset[Path]:
    """Identify local PEP-3147 caches only when the active loader ignores them."""

    cache_directories = tuple(
        path for path in directories if path.name == "__pycache__"
    )
    if not cache_directories:
        return frozenset()
    if sys.pycache_prefix is None:
        raise AcceptanceError(
            f"{label} contains loader-visible local bytecode caches"
        )
    try:
        cache_prefix = Path(sys.pycache_prefix).resolve(strict=False)
        source_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AcceptanceError(
            f"cannot validate {label} bytecode isolation: {exc}"
        ) from None
    if cache_prefix == source_root or source_root in cache_prefix.parents:
        raise AcceptanceError(
            f"{label} bytecode cache prefix is inside the source tree"
        )

    skipped: set[Path] = set()
    for directory in directories:
        relative = directory.relative_to(root)
        if "__pycache__" in relative.parts and directory.name != "__pycache__":
            raise AcceptanceError(
                f"{label} contains a directory inside __pycache__"
            )
    for path in files:
        relative = path.relative_to(root)
        if "__pycache__" not in relative.parts:
            continue
        if path.parent.name != "__pycache__" or path.suffix != ".pyc":
            raise AcceptanceError(
                f"{label} contains an unexpected bytecode-cache file"
            )
        module_name = path.name.split(".", 1)[0]
        source = path.parent.parent / f"{module_name}.py"
        try:
            source_stat = os.lstat(source)
        except OSError:
            raise AcceptanceError(
                f"{label} contains bytecode without its captured source"
            ) from None
        if not stat.S_ISREG(source_stat.st_mode) or stat.S_ISLNK(
            source_stat.st_mode
        ):
            raise AcceptanceError(
                f"{label} contains bytecode without a plain captured source"
            )
        skipped.add(path)
    return frozenset(skipped)


def _is_compiled_loader_name(name: str, module: str) -> bool:
    """Recognize CPython extension competitors independently of host ABI."""

    return name.startswith(module + ".") and name.endswith((".so", ".pyd"))


def _assert_namespace_parent(directory: Path, module: str, label: str) -> None:
    """Require the reviewed namespace layout and reject loader competitors."""

    _plain_directory(directory, label)
    root = directory.parent
    _plain_directory(root, f"{label} parent")
    try:
        with os.scandir(root) as scanned:
            root_names = tuple(entry.name for entry in scanned)
        with os.scandir(directory) as scanned:
            namespace_names = tuple(entry.name for entry in scanned)
    except OSError as exc:
        raise AcceptanceError(f"cannot inspect {label}: {exc}") from None

    for name in root_names:
        if name in {f"{module}.py", f"{module}.pyc"} or _is_compiled_loader_name(
            name, module
        ):
            raise AcceptanceError(f"{label} has a competing module loader")
    for name in namespace_names:
        if name in {"__init__.py", "__init__.pyc"} or _is_compiled_loader_name(
            name, "__init__"
        ):
            raise AcceptanceError(f"{label} must remain a namespace package")


def _assert_script_extension_closure(relative_paths: Sequence[str]) -> None:
    """Reject ABI extensions or sourceless bytecode shadowing selected scripts."""

    python_scripts = tuple(
        Path(relative)
        for relative in relative_paths
        if Path(relative).parent == Path("scripts")
        and Path(relative).suffix == ".py"
    )
    scripts = _plain_directory(
        REPOSITORY_ROOT / "scripts", "primary semantic scripts directory"
    )
    try:
        with os.scandir(scripts) as scanned:
            names = tuple(entry.name for entry in scanned)
    except OSError as exc:
        raise AcceptanceError(
            f"cannot inspect primary semantic scripts: {exc}"
        ) from None
    for script in python_scripts:
        for name in names:
            if name == script.name:
                continue
            if (
                name in {script.stem, f"{script.stem}.pyc"}
                or _is_compiled_loader_name(name, script.stem)
            ):
                raise AcceptanceError(
                    f"primary semantic script {script.name} has a competing loader"
                )


def _primary_semantic_source_identity() -> dict[str, object]:
    """Hash the closed model/search/kernel source used by the primary run."""

    package = PEANO_PYTHON / "peano_lab"
    training = REPOSITORY_ROOT / "training" / "peano_policy"
    package_directories, package_entries = _closed_tree_entries(
        package, "Peano semantic source package"
    )
    training_directories, training_entries = _closed_tree_entries(
        training, "policy semantic source package"
    )
    package_caches = _inert_external_bytecode_cache_files(
        package,
        package_directories,
        package_entries,
        "Peano semantic source package",
    )
    training_caches = _inert_external_bytecode_cache_files(
        training,
        training_directories,
        training_entries,
        "policy semantic source package",
    )

    reviewed_noncode = frozenset(PRIMARY_SEMANTIC_TRAINING_REVIEWED_NONCODE_FILES)
    externally_sealed = frozenset(PRIMARY_SEMANTIC_EXTERNALLY_SEALED_FILES)
    observed_noncode: set[str] = set()
    observed_external: set[str] = set()
    relative_paths: list[str] = [
        *PRIMARY_SEMANTIC_SCRIPT_FILES,
        *PRIMARY_SEMANTIC_PROTOCOL_FILES,
    ]
    for path in package_entries:
        if path in package_caches:
            continue
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if path.suffix != ".py":
            raise AcceptanceError(
                f"Peano semantic source package contains unreviewed file {relative}"
            )
        relative_paths.append(relative)
    for path in training_entries:
        if path in training_caches:
            continue
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if path.suffix == ".py":
            relative_paths.append(relative)
        elif relative in reviewed_noncode:
            observed_noncode.add(relative)
            relative_paths.append(relative)
        elif relative in externally_sealed:
            observed_external.add(relative)
        else:
            raise AcceptanceError(
                f"policy semantic source package contains unreviewed file {relative}"
            )
    if observed_noncode != set(reviewed_noncode):
        raise AcceptanceError("primary semantic reviewed non-code inventory changed")
    if observed_external != set(externally_sealed):
        raise AcceptanceError("primary semantic external seal inventory changed")

    _assert_namespace_parent(
        REPOSITORY_ROOT / "scripts", "scripts", "scripts namespace"
    )
    _assert_namespace_parent(
        REPOSITORY_ROOT / "training", "training", "training namespace"
    )
    _assert_script_extension_closure(relative_paths)
    if len(relative_paths) != len(set(relative_paths)):
        raise AcceptanceError("primary semantic source inventory is duplicated")
    files = {
        relative: _sha256_file(
            _plain_file(
                REPOSITORY_ROOT / relative,
                f"primary semantic source {relative}",
            )
        )
        for relative in sorted(relative_paths)
    }
    return {
        "algorithm": "sha256-json-v1(path-to-file-sha256)",
        "file_count": len(files),
        "files": files,
        "sha256": _sha256_json(files),
    }


def _semantic_source_record(value: object, label: str) -> dict[str, object]:
    record = _mapping(value, label)
    files = _mapping(record.get("files"), f"{label}.files")
    if (
        set(record) != {"algorithm", "file_count", "files", "sha256"}
        or record.get("algorithm") != "sha256-json-v1(path-to-file-sha256)"
        or record.get("file_count") != len(files)
        or record.get("sha256") != _sha256_json(files)
    ):
        raise AcceptanceError(f"{label} is not a closed path-bound inventory")
    for relative, digest in files.items():
        if type(relative) is not str or type(digest) is not str:
            raise AcceptanceError(f"{label} contains a malformed file identity")
        path = Path(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not relative.startswith(
                (
                    "scripts/",
                    "slurm/",
                    "training/peano_policy/",
                    "peano-lab/py/peano_lab/",
                )
            )
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise AcceptanceError(f"{label} contains an unsafe file identity")
    return record


def _validated_primary_semantic_source(
    manifest: Mapping[str, object],
) -> dict[str, object]:
    subject = _mapping(manifest.get("subject"), "subject")
    expected = _semantic_source_record(
        subject.get("primary_semantic_source"), "subject.primary_semantic_source"
    )
    current = _primary_semantic_source_identity()
    if expected != current:
        raise AcceptanceError("primary semantic source identity changed")
    return current


def _expected_evaluation_sources(
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """Project the sealed semantic inventory onto the evaluator's exact set."""

    semantic = _semantic_source_record(
        _mapping(manifest.get("subject"), "subject").get(
            "primary_semantic_source"
        ),
        "subject.primary_semantic_source",
    )
    files = _mapping(semantic.get("files"), "primary semantic files")
    evaluator_scripts = {
        "scripts/eval_trained_peano_policy.py",
        "scripts/eval_peano_policy.py",
        "scripts/peano_policy_proof_request.py",
    }
    selected = {
        relative: digest
        for relative, digest in files.items()
        if relative in evaluator_scripts
        or (
            relative.startswith("training/peano_policy/")
            and relative.endswith(".py")
            and "/" not in relative[len("training/peano_policy/") :]
        )
        or (
            relative.startswith("peano-lab/py/peano_lab/")
            and relative.endswith(".py")
        )
    }
    if set(evaluator_scripts) - set(selected):
        raise AcceptanceError("primary semantic inventory lacks evaluator sources")
    return {"sha256": _sha256_json(selected), "files": selected}


def _base_snapshot_authority(manifest: Mapping[str, object]) -> dict[str, object]:
    from training.peano_policy.base_snapshot import authority_identity

    subject = _mapping(manifest.get("subject"), "subject")
    base = _mapping(subject.get("base_model"), "subject.base_model")
    snapshot = _mapping(base.get("snapshot"), "subject.base_model.snapshot")
    expected = authority_identity()
    if (
        set(base) != {"id", "revision", "snapshot"}
        or base.get("id") != "Qwen/Qwen3-1.7B-Base"
        or base.get("revision") != "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
        or snapshot != expected
    ):
        raise AcceptanceError("subject.base_model is not the closed Qwen snapshot")
    return expected


def _validated_base_snapshot(manifest: Mapping[str, object]) -> dict[str, object]:
    from training.peano_policy.base_snapshot import validate_base_snapshot

    authority = _base_snapshot_authority(manifest)
    base = _mapping(
        _mapping(manifest.get("subject"), "subject").get("base_model"),
        "subject.base_model",
    )
    try:
        current = validate_base_snapshot(
            model_id=_text(base.get("id"), "base model id"),
            revision=_text(base.get("revision"), "base model revision"),
        )
    except (OSError, TypeError, ValueError) as exc:
        raise AcceptanceError(f"base model snapshot validation failed: {exc}") from None
    if (
        current.get("sha256") != authority.get("snapshot_sha256")
        or current.get("file_count") != authority.get("file_count")
        or current.get("total_bytes") != authority.get("total_bytes")
    ):
        raise AcceptanceError("base model snapshot differs from preregistration")
    return current


def _submission_ledger_path(manifest: Mapping[str, object]) -> Path:
    execution = _mapping(
        _mapping(manifest.get("protocol"), "protocol").get("wmi_execution"),
        "protocol.wmi_execution",
    )
    relative = _text(execution.get("submission_ledger"), "submission ledger")
    return _repository_path(relative, "submission ledger")


def _load_submission_ledger(
    manifest: Mapping[str, object],
) -> tuple[dict[str, str], ...]:
    path = _plain_file(_submission_ledger_path(manifest), "WMI submission ledger")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise AcceptanceError(f"cannot stat WMI submission ledger: {exc}") from None
    if size > 16_000_000:
        raise AcceptanceError("WMI submission ledger is unexpectedly large")
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != WMI_SUBMISSION_FIELDS:
                raise AcceptanceError("WMI submission ledger header changed")
            rows = tuple(dict(row) for row in reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AcceptanceError(f"cannot parse WMI submission ledger: {exc}") from None
    seen_jobs: set[str] = set()
    for ordinal, row in enumerate(rows, 1):
        if set(row) != set(WMI_SUBMISSION_FIELDS) or any(
            type(row.get(field)) is not str
            or any(character in str(row[field]) for character in "\r\n\t")
            for field in WMI_SUBMISSION_FIELDS
        ):
            raise AcceptanceError(f"WMI submission row {ordinal} is malformed")
        job_id = row["job_id"]
        if _JOB_ID_RE.fullmatch(job_id) is None or job_id in seen_jobs:
            raise AcceptanceError("WMI submission job ids are malformed or duplicated")
        seen_jobs.add(job_id)
        if (
            row["git_dirty"] != "false"
            or _COMMIT_RE.fullmatch(row["git_commit"]) is None
            or row["workdir"] != WMI_PROJECT_ROOT
            or _SHA256_RE.fullmatch(row["script_sha256"]) is None
        ):
            raise AcceptanceError(f"WMI submission row {ordinal} is not clean and fixed")
        dependency = row["dependency_job_id"]
        if dependency and _JOB_ID_RE.fullmatch(dependency) is None:
            raise AcceptanceError(f"WMI submission row {ordinal} has a bad dependency")
    return rows


def _unique_script_row(
    rows: Sequence[Mapping[str, str]], script: str
) -> tuple[int, dict[str, str]]:
    matches = [
        (index, dict(row))
        for index, row in enumerate(rows)
        if row.get("script") == script
    ]
    if len(matches) != 1:
        raise AcceptanceError(
            f"WMI submission ledger must contain the earliest and only {script} job"
        )
    return matches[0]


def _validate_submission_script(row: Mapping[str, str], script: str) -> None:
    if script == WMI_DATASET_GENERATOR_SCRIPT:
        expected_sha256 = WMI_DATASET_GENERATOR_SCRIPT_SHA256
    elif script in WMI_TRAINING_SCRIPT_SHA256:
        expected_sha256 = WMI_TRAINING_SCRIPT_SHA256[script]
    elif script in WMI_ACCEPTANCE_SCRIPTS:
        expected_sha256 = _current_composite_script_sha256(script)
    else:
        raise AcceptanceError(f"WMI job {script} is outside the acceptance protocol")
    if row.get("script") != script or row.get("script_sha256") != expected_sha256:
        raise AcceptanceError(f"WMI job {script} does not use its committed script")


def _validate_finalize_submission_chain(
    manifest: Mapping[str, object],
    rows: Sequence[Mapping[str, str]],
) -> dict[str, dict[str, str]]:
    """Validate the historical generator and the official recovery finalizer."""

    contract = _mapping(
        _mapping(manifest.get("subject"), "subject").get("training_contract"),
        "training contract",
    )
    generator_index, generator = _unique_script_row(
        rows, WMI_DATASET_GENERATOR_SCRIPT
    )
    prepare_index, prepare = _unique_script_row(rows, WMI_PREPARE_SCRIPT)
    _validate_submission_script(generator, WMI_DATASET_GENERATOR_SCRIPT)
    _validate_submission_script(prepare, WMI_PREPARE_SCRIPT)
    if generator_index >= prepare_index:
        raise AcceptanceError(
            "WMI dataset generator does not predate the recovery finalizer"
        )
    if (
        generator.get("job_id") != WMI_DATASET_GENERATOR_EVIDENCE["job_id"]
        or generator.get("git_commit")
        != contract.get("dataset_generation_source_commit")
        or generator.get("git_dirty") != "false"
        or generator.get("dependency_job_id") != ""
        or generator.get("workdir") != WMI_PROJECT_ROOT
    ):
        raise AcceptanceError("WMI dataset generator is not the sealed precursor")
    if (
        prepare.get("git_dirty") != "false"
        or prepare.get("dependency_job_id") != ""
        or prepare.get("workdir") != WMI_PROJECT_ROOT
    ):
        raise AcceptanceError("WMI recovery finalizer is not a clean standalone job")
    return {"generator": generator, "prepare": prepare}


def _validate_training_submission_chain(
    manifest: Mapping[str, object],
    rows: Sequence[Mapping[str, str]],
) -> dict[str, dict[str, str]]:
    selected = _validate_finalize_submission_chain(manifest, rows)
    prepare_index = next(
        index
        for index, row in enumerate(rows)
        if row.get("job_id") == selected["prepare"]["job_id"]
    )
    selected = {
        **selected,
        "train_pair": _unique_script_row(rows, WMI_TRAIN_SCRIPT),
        "eval_pair": _unique_script_row(rows, WMI_EVAL_SCRIPT),
    }
    prepare = selected["prepare"]
    train_index, train = selected["train_pair"]
    eval_index, evaluate = selected["eval_pair"]
    if not prepare_index < train_index < eval_index:
        raise AcceptanceError("WMI training jobs are not in finalize/train/eval order")
    for script, row in (
        (WMI_PREPARE_SCRIPT, prepare),
        (WMI_TRAIN_SCRIPT, train),
        (WMI_EVAL_SCRIPT, evaluate),
    ):
        _validate_submission_script(row, script)
        if (
            row.get("git_commit") != prepare.get("git_commit")
            or row.get("git_dirty") != "false"
            or row.get("sync_timestamp") != prepare.get("sync_timestamp")
            or row.get("workdir") != WMI_PROJECT_ROOT
        ):
            raise AcceptanceError("WMI training jobs do not share the sealed deployment")
    if (
        train.get("dependency_job_id") != prepare.get("job_id")
        or evaluate.get("dependency_job_id") != train.get("job_id")
    ):
        raise AcceptanceError("WMI finalize/train/eval dependencies are not exact")
    return {
        "generator": selected["generator"],
        "prepare": prepare,
        "train": train,
        "eval": evaluate,
    }


def _expected_source_sync(row: Mapping[str, str]) -> dict[str, object]:
    source_line = (
        f"{row.get('git_commit')}\tfalse\t{row.get('sync_timestamp')}\n"
    ).encode("ascii")
    return {
        "status": "synced",
        "path": ".peano-source-provenance.tsv",
        "sha256": hashlib.sha256(source_line).hexdigest(),
        "git_commit": row.get("git_commit"),
        "git_dirty": False,
        "synced_at": row.get("sync_timestamp"),
    }


def _validate_job_identity(
    value: object,
    *,
    expected_row: Mapping[str, str],
    expected_script: str,
    expected_job_name: str,
    label: str,
) -> dict[str, object]:
    """Join a runtime job record to the independently appended WMI row."""

    job = _mapping(value, label)
    submission = _mapping(job.get("submission"), f"{label}.submission")
    deployment = _mapping(job.get("deployment"), f"{label}.deployment")
    source_sync = _mapping(deployment.get("source_sync"), f"{label}.source_sync")
    job_script = _mapping(deployment.get("job_script"), f"{label}.job_script")
    support = _mapping(deployment.get("support_script"), f"{label}.support_script")
    declaration = _mapping(
        deployment.get("runtime_declaration"), f"{label}.runtime_declaration"
    )
    environment = _mapping(job.get("environment"), f"{label}.environment")
    ledger = _mapping(job.get("ledger"), f"{label}.ledger")
    support_sha256 = (
        WMI_TRAINING_SUPPORT_SHA256
        if expected_script in WMI_TRAINING_SCRIPTS
        else _current_protocol_file_sha256(
            "scripts/wmi_job_environment.sh", "acceptance support script"
        )
    )
    if submission != dict(expected_row):
        raise AcceptanceError(f"{label} is not joined to its only submission row")
    if (
        job.get("scheduler") != "slurm"
        or job.get("job_id") != expected_row.get("job_id")
        or ledger
        != {
            "path": WMI_SUBMISSION_LEDGER,
            "row_sha256": _sha256_json(dict(expected_row)),
        }
        or deployment.get("mode") != "slurm"
        or source_sync.get("status") != "synced"
        or source_sync.get("path") != ".peano-source-provenance.tsv"
        or source_sync.get("git_commit") != expected_row.get("git_commit")
        or source_sync.get("git_dirty") is not False
        or source_sync.get("synced_at") != expected_row.get("sync_timestamp")
        or source_sync.get("sha256")
        != hashlib.sha256(
            (
                f"{expected_row.get('git_commit')}\tfalse\t"
                f"{expected_row.get('sync_timestamp')}\n"
            ).encode("ascii")
        ).hexdigest()
        or job_script.get("status") != "declared"
        or job_script.get("path") != expected_script
        or job_script.get("sha256") != expected_row.get("script_sha256")
        or support.get("status") != "declared"
        or support.get("path") != "scripts/wmi_job_environment.sh"
        or support.get("sha256") != support_sha256
        or support.get("sourced_sha256") != support.get("sha256")
        or declaration.get("backend") != "wmi"
        or declaration.get("base_environment") != "pytorch-gpu"
        or environment.get("SLURM_JOB_NAME") != expected_job_name
        or environment.get("SLURM_SUBMIT_DIR") != WMI_PROJECT_ROOT
    ):
        raise AcceptanceError(f"{label} has inconsistent WMI deployment identity")
    job_support = _mapping(job_script.get("support_script"), f"{label}.job support")
    if job_support != support:
        raise AcceptanceError(f"{label} job/support script identities disagree")
    modules = _mapping(deployment.get("modules"), f"{label}.modules")
    if (
        modules.get("status") != "loaded"
        or modules.get("requested") != "anaconda/2025.12-1"
        or type(modules.get("loaded_modules")) is not list
        or "anaconda/2025.12-1" not in modules["loaded_modules"]
    ):
        raise AcceptanceError(f"{label} does not carry the reviewed WMI module")
    base_manifest = _mapping(
        declaration.get("base_manifest"), f"{label}.base_manifest"
    )
    requirements = _mapping(
        declaration.get("requirements"), f"{label}.requirements"
    )
    if (
        base_manifest
        != {
            "path": "training/peano_policy/wmi-base-v1.json",
            "sha256": "67311313504c3f67dc12cbe6018812720ff4d925ad656961dcc4d9816306941a",
        }
        or requirements
        != {
            "path": "training/peano_policy/requirements-wmi-overlay.lock",
            "sha256": "6bcc1633302b2df72a1374e5c5e93f05b483bbb276541551cc471c83c5d3b82d",
        }
    ):
        raise AcceptanceError(f"{label} does not use the reviewed WMI runtime lock")
    return job


def validate_manifest(
    manifest: Mapping[str, object],
    *,
    manifest_path: Path | None = None,
) -> dict[str, object]:
    """Validate goals, collisions, authority, runners, and thresholds."""

    if (
        manifest.get("format") != MANIFEST_FORMAT
        or manifest.get("v") != MANIFEST_VERSION
    ):
        raise AcceptanceError("unsupported acceptance preregistration")
    if manifest_path is not None:
        digest = _sha256_file(manifest_path)
        if digest != EXPECTED_MANIFEST_SHA256:
            raise AcceptanceError("the repository preregistration hash is not pinned")

    seal = _mapping(manifest.get("scientific_seal"), "scientific_seal")
    if seal != {
        "parent_commit": "035321951eabc8b8f06b918323fada2e372b77e8",
        "parent_manifest_sha256": (
            "44df39cbf78f458591a156548c9314d71c8f695be12d4d8c8bf38e5e89a679b1"
        ),
        "preserved_choices": [
            "goal statements, order, categories, and visibility",
            "decoder seeds and search budgets",
            "binary and stretch decision thresholds",
        ],
    }:
        raise AcceptanceError("the externally sealed scientific choices changed")

    # Hash every importable model/search/kernel source before importing any of
    # it.  A changed module must not get an opportunity to run import-time code
    # before the closed-source seal rejects the deployment.
    _validated_primary_semantic_source(manifest)
    _base_snapshot_authority(manifest)

    from peano_lab.library.theorems import THEOREMS
    from training.peano_policy.contract import (
        HELD_OUT_POLICY_GOALS,
        held_out_contract_sha256,
        model_v2_environment,
    )
    from training.peano_policy.library_identity import (
        model_v2_library_identity_sha256,
    )

    environment = model_v2_environment()
    allowed_names = frozenset(environment.capabilities.allowed_theorems or ())
    subject = _mapping(manifest.get("subject"), "subject")
    authority = _mapping(subject.get("authority"), "subject.authority")
    expected_authority = {
        "surface": "model-v2",
        "classical": False,
        "environment_sha256": environment.sha256,
        "library_identity_sha256": model_v2_library_identity_sha256(),
        "held_out_contract_sha256": held_out_contract_sha256(),
        "allowed_theorem_count": len(allowed_names),
    }
    if authority != expected_authority:
        raise AcceptanceError("subject.authority is not the exact model-v2 identity")
    training_contract = _mapping(
        subject.get("training_contract"), "subject.training_contract"
    )
    expected_config = (
        REPOSITORY_ROOT
        / "training"
        / "peano_policy"
        / "configs"
        / "qwen3_1_7b_v2_heavy.toml"
    )
    expected_training_contract = {
        "dataset_generation_source_commit": (
            "1b2d26c60cddf7ffb49a91b2fd652519b9d6bcb1"
        ),
        "source_file_count": 25,
        "source_sha256": (
            "2951471a7c9942e61700d78e0defafa628fbf261e47151d3b6c093e7692f2ba3"
        ),
        "config_path": "training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml",
        "config_sha256": _sha256_file(expected_config),
        "dataset_directory": "data/peano-policy-v2",
        "dataset_sha256": (
            "919078e0732275c95cc0675f44e44a0b9ad0cb674b0ed03a7069bead57f63a6d"
        ),
        "dataset_profile": "model-v2",
        "dataset_generator": "proof-first-synthetic-v2",
        "dataset_catalog_version": 4,
        "dataset_seed": "peano-synthetic-v2",
        "positive_tactic_rows": 100_000,
        "realized_split_rows": {"train": 80_494, "val": 9_600, "test": 9_906},
        "training_examples": 80_494,
        "eval_examples": 4_000,
        "splits": list(DATASET_SPLITS),
        "acceptance_contamination_rule": (
            "zero alpha-equivalent C/I/H formulas in any formula subtree of "
            "compiled roots, proof-state targets, rendered prompt targets, "
            "have/suffices tactical propositions, or allowed library statements; "
            "R retrieval goals are exempt"
        ),
    }
    if training_contract != expected_training_contract:
        raise AcceptanceError("subject.training_contract changed or is stale")
    primary_semantic_source = _semantic_source_record(
        subject.get("primary_semantic_source"), "subject.primary_semantic_source"
    )
    if subject.get("adapter_identity_rule") != (
        "The scorer recomputes the training-manifest, closed adapter, and "
        "closed tokenizer hashes from the supplied adapter directory and "
        "requires every outcome to carry that one identity."
    ):
        raise AcceptanceError("subject.adapter_identity_rule changed")

    def canonical(source: str) -> str:
        return _canonical_statement(source, "public theorem")

    public_by_formula: dict[str, list[str]] = {}
    for theorem in THEOREMS:
        public_by_formula.setdefault(canonical(theorem.statement), []).append(
            theorem.name
        )

    rows = _goal_records(manifest)
    expected_ids = tuple(
        [f"R{index}" for index in range(1, 4)]
        + [f"C{index}" for index in range(1, 6)]
        + [f"I{index}" for index in range(1, 5)]
        + [f"H{index}" for index in range(1, 5)]
    )
    if tuple(row["id"] for row in rows) != expected_ids:
        raise AcceptanceError("goal order or ids differ from the preregistration")

    held_out = {
        name: canonical(statement) for name, statement in HELD_OUT_POLICY_GOALS
    }
    category_counts = {
        name: 0
        for name in ("retrieval", "composition", "induction", "sealed")
    }
    collision_count = 0
    for row in rows:
        goal_id = _text(row.get("id"), "goal id")
        category = _text(row.get("category"), f"{goal_id}.category")
        if category not in category_counts:
            raise AcceptanceError(f"{goal_id} has an unknown category")
        category_counts[category] += 1
        statement = _canonical_statement(row.get("statement"), f"{goal_id}.statement")
        if statement != row.get("statement"):
            raise AcceptanceError(f"{goal_id}.statement is not canonical")
        declared = _sequence(
            row.get("public_collisions"), f"{goal_id}.public_collisions"
        )
        if not all(type(name) is str for name in declared):
            raise AcceptanceError(f"{goal_id}.public_collisions must contain names")
        actual = public_by_formula.get(statement, [])
        if declared != actual:
            raise AcceptanceError(
                f"{goal_id} public collisions differ: declared {declared}, "
                f"actual {actual}"
            )
        collision_count += len(actual)
        visibility = row.get("model_v2_visibility")
        if category == "retrieval":
            retrieval = row.get("retrieval_theorem")
            if (
                visibility != "allowed"
                or declared != [retrieval]
                or retrieval not in allowed_names
            ):
                raise AcceptanceError(
                    f"{goal_id} is not an allowed exact retrieval goal"
                )
        elif category in {"composition", "induction"}:
            if visibility != "fresh" or declared:
                raise AcceptanceError(
                    f"{goal_id} is not fresh relative to the public catalog"
                )
        else:
            sealed_name = row.get("sealed_name")
            if (
                visibility != "sealed"
                or declared != [sealed_name]
                or sealed_name in allowed_names
                or held_out.get(str(sealed_name)) != statement
            ):
                raise AcceptanceError(f"{goal_id} is not the declared sealed benchmark")

    from peano_lab.kernel.formulas import parse_formula_with_names

    forbidden_library_subformulas: dict[object, str] = {}
    for row in rows:
        if row["category"] == "retrieval":
            continue
        formula, names = parse_formula_with_names(str(row["statement"]))
        if names:  # pragma: no cover - canonical validation above rejects this
            raise AcceptanceError("acceptance target unexpectedly has free names")
        forbidden_library_subformulas[formula] = str(row["id"])
    library_collisions: list[str] = []
    for theorem in THEOREMS:
        if theorem.name not in allowed_names:
            continue
        formula, _names = parse_formula_with_names(theorem.statement)
        library_collisions.extend(
            _formula_subtree_collisions(
                formula,
                forbidden_library_subformulas,
                label=f"allowed-library:{theorem.name}",
            )
        )
    if library_collisions:
        raise AcceptanceError(
            "acceptance target occurs inside an allowed library statement: "
            + ", ".join(sorted(set(library_collisions)))
        )

    if category_counts != {
        "retrieval": 3,
        "composition": 5,
        "induction": 4,
        "sealed": 4,
    }:
        raise AcceptanceError("goal category cardinalities changed")

    protocol = _mapping(manifest.get("protocol"), "protocol")
    if protocol.get("wmi_execution") != {
        "project_root": WMI_PROJECT_ROOT,
        "submission_ledger": WMI_SUBMISSION_LEDGER,
        "proof_request_ledger": WMI_PROOF_REQUEST_LEDGER,
        "pretraining_data_audit_report": WMI_PRETRAIN_DATA_AUDIT,
        "dataset_generator_job": WMI_DATASET_GENERATOR_SCRIPT,
        "dataset_generator_script_sha256": WMI_DATASET_GENERATOR_SCRIPT_SHA256,
        "dataset_generator_evidence": WMI_DATASET_GENERATOR_EVIDENCE,
        "training_jobs": list(WMI_TRAINING_SCRIPTS),
        "training_script_sha256": WMI_TRAINING_SCRIPT_SHA256,
        "training_support_script_sha256": WMI_TRAINING_SUPPORT_SHA256,
        "heldout_report": WMI_HELDOUT_REPORT,
        "final_report": WMI_FINAL_REPORT,
        "primary_job": WMI_PRIMARY_SCRIPT,
        "scorer_job": WMI_SCORER_SCRIPT,
        "one_submission_per_script": True,
        "scorer_loads_model": False,
    }:
        raise AcceptanceError("protocol.wmi_execution changed")
    rules = _mapping(protocol.get("primary_run_rules"), "primary_run_rules")
    if rules != {
        "attempts_per_goal": 1,
        "retry_failed_goals": False,
        "reorder_goals": False,
        "change_seed": False,
        "select_best_run": False,
    }:
        raise AcceptanceError("primary-run rules changed")
    if protocol.get("primary_session") != {
        "format": PRIMARY_SESSION_FORMAT,
        "v": PRIMARY_SESSION_VERSION,
        "one_loaded_adapter": True,
        "non_resumable": True,
        "fixed_output_below_adapter": PRIMARY_SESSION_DIRECTORY,
        "ledger": PRIMARY_SESSION_LEDGER,
        "open_marker": PRIMARY_SESSION_OPEN,
    }:
        raise AcceptanceError("primary-session transaction changed")
    interactive = _mapping(protocol.get("interactive"), "protocol.interactive")
    sealed = _mapping(protocol.get("sealed_evaluator"), "protocol.sealed_evaluator")
    if interactive.get("goal_ids") != list(expected_ids[:12]):
        raise AcceptanceError("interactive goal order changed")
    if sealed.get("goal_ids") != list(expected_ids[12:]):
        raise AcceptanceError("sealed goal order changed")
    for label, runner, expected_budget, expected_decoding in (
        (
            "interactive",
            interactive,
            {
                "max_depth": 32,
                "beam_width": 4,
                "candidates_per_state": 4,
                "max_model_calls": 128,
                "max_states": 2048,
            },
            {
                "max_new_tokens": 96,
                "do_sample": False,
                "temperature": 0.8,
                "top_p": 0.95,
            },
        ),
        (
            "sealed_evaluator",
            sealed,
            {
                "max_depth": 32,
                "beam_width": 16,
                "candidates_per_state": 8,
                "max_model_calls": 512,
                "max_states": 4096,
            },
            {
                "max_new_tokens": 96,
                "do_sample": True,
                "temperature": 1.0,
                "top_p": 1.0,
            },
        ),
    ):
        if runner.get("seed") != 20260728:
            raise AcceptanceError(f"{label} seed changed")
        _exact_int_mapping(
            runner.get("search_budget_per_goal"), expected_budget, f"{label} budget"
        )
        if runner.get("decoding") != expected_decoding:
            raise AcceptanceError(f"{label} decoding changed")

    decision = _mapping(manifest.get("decision_rule"), "decision_rule")
    binary = _mapping(decision.get("binary_pass"), "decision_rule.binary_pass")
    if (
        binary.get("category_minimums")
        != {
            "retrieval": 3,
            "composition": 3,
            "induction": 2,
            "sealed": 1,
        }
        or binary.get("synthesis_minimum") != 7
        or binary.get("overall_minimum") != 10
    ):
        raise AcceptanceError("binary decision thresholds changed")
    if binary.get("nontrivial_induction_goal_ids") != ["I2", "I3", "I4"]:
        raise AcceptanceError("nontrivial induction subset changed")
    if binary.get("nontrivial_induction_minimum") != 1:
        raise AcceptanceError("nontrivial induction threshold changed")

    return {
        "preregistration_id": manifest.get("preregistration_id"),
        "goal_count": len(rows),
        "category_counts": category_counts,
        "declared_public_collisions": collision_count,
        "model_v2_environment_sha256": environment.sha256,
        "model_v2_library_identity_sha256": model_v2_library_identity_sha256(),
        "primary_semantic_source_sha256": primary_semantic_source["sha256"],
        "held_out_names": [
            row["sealed_name"] for row in rows if row["category"] == "sealed"
        ],
    }


def _finite_number(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in {int, float} or not math.isfinite(float(value)):
        raise AcceptanceError(f"{label} must be a finite number")
    number = float(value)
    if (positive and number <= 0) or (not positive and number < 0):
        qualifier = "positive" if positive else "nonnegative"
        raise AcceptanceError(f"{label} must be {qualifier}")
    return number


def _validate_training_metrics(
    value: object,
    *,
    contract: Mapping[str, object],
    config: object,
) -> None:
    metrics = _mapping(value, "training metrics")
    if set(metrics) != {"train", "eval", "train_examples", "eval_examples"}:
        raise AcceptanceError("training metrics have an incompatible schema")
    if (
        metrics.get("train_examples") != contract.get("training_examples")
        or metrics.get("eval_examples") != contract.get("eval_examples")
    ):
        raise AcceptanceError("training consumed the wrong number of examples")
    train = _mapping(metrics.get("train"), "training metrics.train")
    evaluate = _mapping(metrics.get("eval"), "training metrics.eval")
    required_train = {
        "epoch",
        "total_flos",
        "train_loss",
        "train_runtime",
        "train_samples_per_second",
        "train_steps_per_second",
    }
    required_eval = {
        "epoch",
        "eval_loss",
        "eval_runtime",
        "eval_samples_per_second",
        "eval_steps_per_second",
    }
    if not required_train.issubset(train) or not required_eval.issubset(evaluate):
        raise AcceptanceError("training/evaluation metrics are incomplete")
    for label, record in (("train", train), ("eval", evaluate)):
        for field, number in record.items():
            if type(number) in {int, float}:
                _finite_number(number, f"training metrics.{label}.{field}")
            elif type(number) not in {str, bool, type(None)}:
                raise AcceptanceError(
                    f"training metrics.{label}.{field} is not scalar JSON"
                )
    for field in (
        "total_flos",
        "train_runtime",
        "train_samples_per_second",
        "train_steps_per_second",
    ):
        _finite_number(train.get(field), f"training metrics.train.{field}", positive=True)
    for field in ("eval_runtime", "eval_samples_per_second", "eval_steps_per_second"):
        _finite_number(
            evaluate.get(field), f"training metrics.eval.{field}", positive=True
        )
    _finite_number(train.get("train_loss"), "training metrics.train.train_loss")
    _finite_number(evaluate.get("eval_loss"), "training metrics.eval.eval_loss")
    expected_epochs = getattr(getattr(config, "trainer", None), "epochs", None)
    if train.get("epoch") != expected_epochs or evaluate.get("epoch") != expected_epochs:
        raise AcceptanceError("heavy training did not complete all configured epochs")


def _validate_training_runtime(
    training: Mapping[str, object],
    *,
    deployment: Mapping[str, object],
    manifest: Mapping[str, object],
    config: object,
) -> dict[str, object]:
    """Require the real WMI training schema, not merely config declarations."""

    runtime = _mapping(training.get("runtime"), "training runtime")
    required_fields = {
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "dtype",
        "attention",
        "resume",
        "environment",
        "job",
        "base_snapshot",
    }
    if set(runtime) != required_fields:
        raise AcceptanceError("training runtime has an incompatible schema")
    if (
        runtime.get("torch") != "2.5.1"
        or runtime.get("transformers") != "4.53.3"
        or runtime.get("peft") != "0.16.0"
        or runtime.get("accelerate") != "1.8.1"
        or runtime.get("dtype") != "bfloat16"
        or runtime.get("attention") != "sdpa"
        or runtime.get("resume")
        != {
            "trainer_value": False,
            "checkpoint": None,
            "checkpoint_sha256": None,
            "global_step": None,
        }
    ):
        raise AcceptanceError("training runtime is not the exact fresh WMI run")

    environment = _mapping(runtime.get("environment"), "training environment")
    packages = _mapping(environment.get("packages"), "training packages")
    if (
        environment.get("implementation") != "CPython"
        or environment.get("python") != "3.12.12"
        or environment.get("machine") != "x86_64"
        or type(environment.get("platform")) is not str
        or not str(environment.get("platform")).startswith("Linux-")
        or type(environment.get("hostname")) is not str
        or not str(environment.get("hostname")).endswith(".cluster.wmi.amu.edu.pl")
        or packages != WMI_RUNTIME_PACKAGES
        or environment.get("packages_sha256") != _sha256_json(packages)
        or environment.get("requirements")
        != {
            "path": "training/peano_policy/requirements-wmi-overlay.lock",
            "sha256": "6bcc1633302b2df72a1374e5c5e93f05b483bbb276541551cc471c83c5d3b82d",
        }
        or environment.get("base_manifest")
        != {
            "path": "training/peano_policy/wmi-base-v1.json",
            "sha256": "67311313504c3f67dc12cbe6018812720ff4d925ad656961dcc4d9816306941a",
        }
    ):
        raise AcceptanceError("training package/runtime identity is not reviewed WMI")
    accelerator = _mapping(environment.get("accelerator"), "training accelerator")
    driver = accelerator.get("nvidia_driver")
    if (
        accelerator.get("torch") != "2.5.1"
        or accelerator.get("cuda_available") is not True
        or accelerator.get("cuda_runtime") != "12.4"
        or type(accelerator.get("cudnn")) is not int
        or accelerator.get("device_capability") != [8, 0]
        or accelerator.get("bf16_supported") is not True
        or type(accelerator.get("device_name")) is not str
        or "A100" not in str(accelerator.get("device_name"))
        or type(accelerator.get("total_memory")) is not int
        or int(accelerator.get("total_memory", 0)) < 75 * 1024**3
        or type(driver) is not str
        or re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", driver) is None
    ):
        raise AcceptanceError("training accelerator is not one WMI A100-80GB")

    rows = _load_submission_ledger(manifest)
    chain = _validate_training_submission_chain(manifest, rows)
    job = _validate_job_identity(
        runtime.get("job"),
        expected_row=chain["train"],
        expected_script=WMI_TRAIN_SCRIPT,
        expected_job_name="peano-wmi-qwen17-v2",
        label="training runtime.job",
    )
    if job.get("deployment") != dict(deployment):
        raise AcceptanceError("training job and input deployment identities differ")
    from training.peano_policy.base_snapshot import expected_base_snapshot

    expected_snapshot = expected_base_snapshot()
    snapshot_checks = _mapping(
        runtime.get("base_snapshot"), "training base_snapshot"
    )
    if (
        set(snapshot_checks) != {"before_load", "after_load", "after_training"}
        or any(
            snapshot_checks.get(phase) != expected_snapshot
            for phase in ("before_load", "after_load", "after_training")
        )
    ):
        raise AcceptanceError("training did not preserve the closed base snapshot")
    _validate_training_metrics(
        training.get("metrics"), contract=_mapping(
            _mapping(manifest.get("subject"), "subject").get("training_contract"),
            "training contract",
        ), config=config
    )
    return {"job": job, "chain": chain}


def validate_adapter_authority(
    adapter_directory: Path,
    manifest: Mapping[str, object],
) -> AdapterAuthority:
    """Recompute the closed adapter identity without loading model weights."""

    from training.peano_policy.config import load_config
    from training.peano_policy.contract import (
        attested_training_environment,
        held_out_contract_sha256,
        model_v2_environment,
    )
    from training.peano_policy.library_identity import (
        model_v2_library_identity_sha256,
    )
    from training.peano_policy.manifest import (
        ADAPTER_SUBDIR,
        MANIFEST_VERSION,
        TOKENIZER_SUBDIR,
        require_safetensors_adapter,
        verify_artifact_directory,
    )
    from training.peano_policy.prompt import (
        PEANO_PROMPT_V2,
        prompt_contract_sha256,
    )

    directory = _plain_directory(adapter_directory, "adapter directory")
    if directory != _subject_adapter_directory(manifest):
        raise AcceptanceError(
            "adapter must occupy the one preregistered repository directory"
        )
    training_path = _plain_file(
        directory / TRAINING_MANIFEST, "adapter training manifest"
    )
    training = _read_json(training_path)
    if training.get("v") != MANIFEST_VERSION:
        raise AcceptanceError("adapter training manifest has the wrong version")
    subject = _mapping(manifest.get("subject"), "subject")
    contract = _mapping(
        subject.get("training_contract"), "subject.training_contract"
    )
    authority = _mapping(subject.get("authority"), "subject.authority")
    config_path = REPOSITORY_ROOT / str(contract.get("config_path"))
    if _sha256_file(_plain_file(config_path, "training configuration")) != contract.get(
        "config_sha256"
    ):
        raise AcceptanceError("the preregistered training configuration changed")
    try:
        config = load_config(config_path)
        environment = attested_training_environment(training)
    except (OSError, TypeError, ValueError) as exc:
        raise AcceptanceError(f"adapter training authority is invalid: {exc}") from None
    expected_environment = model_v2_environment()
    if environment != expected_environment:
        raise AcceptanceError("adapter was not trained under the exact model-v2 authority")
    if (
        training.get("prompt_version") != PEANO_PROMPT_V2
        or training.get("prompt_contract_sha256")
        != prompt_contract_sha256(PEANO_PROMPT_V2)
    ):
        raise AcceptanceError("adapter uses the wrong prompt contract")

    if training.get("run") != asdict(config.run) or training.get(
        "generation"
    ) != asdict(config.generation):
        raise AcceptanceError("adapter run/generation configuration is not preregistered")
    if (
        config.run.name != subject.get("run_name")
        or config.run.output_dir != subject.get("adapter_directory")
        or config.run.seed != 20260728
        or config.model.model_id
        != _mapping(subject.get("base_model"), "subject.base_model").get("id")
        or config.model.revision
        != _mapping(subject.get("base_model"), "subject.base_model").get("revision")
    ):
        raise AcceptanceError("resolved training config differs from the subject")

    base = _mapping(training.get("base_model"), "training base_model")
    tokenizer = _mapping(training.get("tokenizer"), "training tokenizer")
    if (
        base.get("id") != config.model.model_id
        or base.get("requested_revision") != config.model.revision
        or base.get("resolved_snapshot_hash") != config.model.revision
        or type(base.get("config_sha256")) is not str
        or _SHA256_RE.fullmatch(str(base.get("config_sha256"))) is None
        or tokenizer.get("resolved_snapshot_hash") != config.model.revision
        or type(tokenizer.get("identity_sha256")) is not str
        or _SHA256_RE.fullmatch(str(tokenizer.get("identity_sha256"))) is None
    ):
        raise AcceptanceError("adapter base/tokenizer revision is not the pinned commit")

    inputs = _mapping(training.get("inputs"), "training inputs")
    config_record = _mapping(inputs.get("config"), "training inputs.config")
    if (
        config_record.get("sha256") != contract.get("config_sha256")
        or not _has_path_suffix(config_record.get("path"), contract.get("config_path"))
    ):
        raise AcceptanceError("training manifest carries the wrong config hash")
    train_record = _mapping(inputs.get("train_data"), "training train_data")
    eval_record = _mapping(inputs.get("eval_data"), "training eval_data")
    if (
        train_record.get("path") != config.data.train_path
        or eval_record.get("path") != config.data.eval_path
    ):
        raise AcceptanceError("training manifest names the wrong compiled splits")

    attestation = _mapping(
        inputs.get("dataset_attestation"), "training dataset_attestation"
    )
    split_records = _mapping(attestation.get("splits"), "attestation splits")
    split_row_counts: list[int] = []
    for name in DATASET_SPLITS:
        rows = _mapping(split_records.get(name), f"attestation {name}").get("rows")
        if type(rows) is not int or rows < 0:
            raise AcceptanceError(f"attestation {name} has an invalid row count")
        split_row_counts.append(rows)
    if (
        attestation.get("format") != "peano-policy-dataset-attestation"
        or attestation.get("v") != 1
        or attestation.get("independent_replay") is not True
        or attestation.get("held_out_contamination") != 0
        or attestation.get("held_out_contract_sha256")
        != held_out_contract_sha256()
        or attestation.get("library_snapshot_sha256")
        != model_v2_library_identity_sha256()
        or set(split_records) != set(DATASET_SPLITS)
        or {
            name: _mapping(split_records.get(name), f"attestation {name}").get("rows")
            for name in DATASET_SPLITS
        }
        != contract.get("realized_split_rows")
        or sum(split_row_counts) != contract.get("positive_tactic_rows")
    ):
        raise AcceptanceError("training dataset attestation is not the fixed 100k gate")
    dataset_sha256 = attestation.get("dataset_sha256")
    if dataset_sha256 != contract.get("dataset_sha256"):
        raise AcceptanceError("training dataset is not the realized sealed 100k corpus")

    deployment = _mapping(inputs.get("deployment"), "training deployment")
    source_sync = _mapping(deployment.get("source_sync"), "training source_sync")
    if (
        source_sync.get("git_dirty") is not False
        or source_sync.get("status") != "synced"
        or _COMMIT_RE.fullmatch(str(source_sync.get("git_commit"))) is None
    ):
        raise AcceptanceError("adapter was not trained from one clean synced source")
    _validate_source_identity(inputs.get("source"), contract, "training source")

    run_identity_record = _mapping(
        inputs.get("run_identity"), "training run_identity"
    )
    run_identity_path = _plain_file(
        directory / RUN_IDENTITY, "adapter run identity"
    )
    if (
        not _has_path_suffix(
            run_identity_record.get("path"),
            f"{config.run.output_dir}/{RUN_IDENTITY}",
        )
        or run_identity_record.get("sha256") != _sha256_file(run_identity_path)
    ):
        raise AcceptanceError("training manifest carries the wrong run identity")
    run_identity = _read_json(run_identity_path)
    run_config = _mapping(run_identity.get("config"), "run identity config")
    resolved = _mapping(run_config.get("resolved"), "run identity resolved config")
    expected_resolved = _json_copy(
        {
            "run": asdict(config.run),
            "model": asdict(config.model),
            "data": asdict(config.data),
            "lora": asdict(config.lora),
            "trainer": asdict(config.trainer),
            "generation": asdict(config.generation),
        }
    )
    run_inputs = _mapping(run_identity.get("inputs"), "run identity inputs")
    from training.peano_policy.base_snapshot import expected_base_snapshot

    expected_snapshot = expected_base_snapshot()
    if (
        run_identity.get("v") != 1
        or run_config.get("sha256") != contract.get("config_sha256")
        or not _has_path_suffix(run_config.get("path"), contract.get("config_path"))
        or resolved != expected_resolved
        or run_identity.get("model")
        != {"id": config.model.model_id, "revision": config.model.revision}
        or run_identity.get("prompt_version") != PEANO_PROMPT_V2
        or run_identity.get("prompt_contract_sha256")
        != prompt_contract_sha256(PEANO_PROMPT_V2)
        or run_inputs
        != {
            "train": train_record.get("sha256"),
            "eval": eval_record.get("sha256"),
            "train_manifest": _mapping(
                inputs.get("train_dataset_manifest"),
                "training train_dataset_manifest",
            ).get("sha256"),
            "eval_manifest": _mapping(
                inputs.get("eval_dataset_manifest"),
                "training eval_dataset_manifest",
            ).get("sha256"),
            "dataset_attestation": attestation,
        }
        or run_identity.get("source") != inputs.get("source")
        or run_identity.get("base_snapshot")
        != {
            "before_load": expected_snapshot,
            "required_after_load": expected_snapshot,
        }
        or run_identity.get("deployment") != deployment
    ):
        raise AcceptanceError(
            "training run identity does not attest the exact config and inputs"
        )

    _validate_training_runtime(
        training,
        deployment=deployment,
        manifest=manifest,
        config=config,
    )

    adapter_record = _mapping(training.get("adapter"), "training adapter")
    tokenizer_artifacts = _mapping(
        tokenizer.get("artifacts"), "training tokenizer artifacts"
    )
    try:
        require_safetensors_adapter(adapter_record)
        verify_artifact_directory(directory, adapter_record, ADAPTER_SUBDIR)
        verify_artifact_directory(directory, tokenizer_artifacts, TOKENIZER_SUBDIR)
    except (OSError, TypeError, ValueError) as exc:
        raise AcceptanceError(f"adapter artifact closure is invalid: {exc}") from None

    training_sha256 = _sha256_file(training_path)
    adapter_sha256 = adapter_record.get("sha256")
    tokenizer_sha256 = tokenizer_artifacts.get("sha256")
    if not all(
        type(value) is str and _SHA256_RE.fullmatch(value)
        for value in (adapter_sha256, tokenizer_sha256)
    ):
        raise AcceptanceError("adapter/tokenizer aggregate hash is malformed")
    identity = {
        "training_manifest_sha256": training_sha256,
        "adapter_sha256": str(adapter_sha256),
        "tokenizer_sha256": str(tokenizer_sha256),
        "dataset_sha256": str(dataset_sha256),
        "config_sha256": str(contract["config_sha256"]),
        "environment_sha256": str(authority["environment_sha256"]),
        "base_snapshot_sha256": str(
            _base_snapshot_authority(manifest)["snapshot_sha256"]
        ),
    }
    return AdapterAuthority(directory, training, identity)


def _goal_context_surface(
    goal_text: object, label: str
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    goal = _text(goal_text, label)
    if goal.count("⊢") != 1:
        raise AcceptanceError(f"{label} is not one canonical Peano goal")
    context_text, target = goal.split("⊢")
    target = target.strip()
    if not target:
        raise AcceptanceError(f"{label} has an empty target")
    context_text = context_text.strip()
    if not context_text:
        return target, (), ()
    variables: list[str] = []
    hypotheses: list[str] = []
    for declaration in context_text.split(", "):
        if " : " not in declaration:
            raise AcceptanceError(f"{label} has a malformed context declaration")
        name, type_text = declaration.split(" : ", 1)
        if not name or not type_text:
            raise AcceptanceError(f"{label} has a malformed context declaration")
        if type_text == "ℕ":
            if hypotheses:
                raise AcceptanceError(f"{label} declares a variable after a hypothesis")
            variables.append(name)
        else:
            hypotheses.append(type_text)
    return target, tuple(variables), tuple(hypotheses)


def _close_formula_source(
    source: str,
    variables: Sequence[str],
    hypotheses: Sequence[str] = (),
) -> str:
    reconstructed = source
    for hypothesis in reversed(hypotheses):
        reconstructed = f"({hypothesis}) → ({reconstructed})"
    if variables:
        reconstructed = f"∀ {' '.join(variables)}. ({reconstructed})"
    return reconstructed


def _goal_formula_surfaces(goal_text: object, label: str) -> tuple[tuple[str, str], ...]:
    """Return every independently visible formula surface in one goal.

    Metavariables are local to a declaration.  A flexible target or hypothesis
    must not suppress contamination checks for the other, rigid declarations
    that the model can still read.
    """

    target, variables, hypotheses = _goal_context_surface(goal_text, label)
    surfaces: list[tuple[str, str]] = [("target", target)]
    if variables:
        surfaces.append(
            ("target-variable-closed", _close_formula_source(target, variables))
        )
    for index, hypothesis in enumerate(hypotheses):
        surfaces.append((f"hypothesis[{index}]", hypothesis))
        if variables:
            surfaces.append(
                (
                    f"hypothesis-variable-closed[{index}]",
                    _close_formula_source(hypothesis, variables),
                )
            )
    rigid_hypotheses = tuple(
        hypothesis
        for hypothesis in hypotheses
        if re.search(r"\?t[0-9]+\b", hypothesis) is None
    )
    if rigid_hypotheses:
        reconstructed = _close_formula_source(
            target, variables, rigid_hypotheses
        )
        surfaces.append(("intro-closed", reconstructed))
    return tuple(surfaces)


def _scan_goal_targets(
    goals: Sequence[object],
    forbidden: Mapping[object, str],
    *,
    label: str,
) -> list[str]:
    from peano_lab.kernel.formulas import parse_formula_with_names

    collisions: list[str] = []
    for index, goal in enumerate(goals):
        for surface, source in _goal_formula_surfaces(goal, f"{label}[{index}]"):
            # A flexible term must not hide an unrelated rigid formula in the
            # same declaration.  Give metavariables fresh parser-only names;
            # they remain free, while closed sibling occurrences can still be
            # compared with the forbidden set.
            parser_source = re.sub(
                r"\?t([0-9]+)\b", r"__peano_meta_\1", source
            )
            try:
                formula, _free_names = parse_formula_with_names(parser_source)
            except (TypeError, ValueError, RecursionError) as exc:
                raise AcceptanceError(
                    f"{label}[{index}] {surface} is not a PA formula: {exc}"
                ) from None
            collisions.extend(
                _formula_subtree_collisions(
                    formula,
                    forbidden,
                    label=f"{label}[{index}].{surface}",
                )
            )
    return collisions


def _formula_subtree_collisions(
    formula: object,
    forbidden: Mapping[object, str],
    *,
    label: str,
) -> list[str]:
    """Find literal and scope-closed acceptance formulas at every AST node.

    Pulling an occurrence out of ``∀ x. A ∧ B`` must restore the binder;
    pulling it out of ``H → A ∧ B`` must restore the antecedent.  Otherwise
    a visible ``A`` can evade an acceptance target ``∀ x. A`` or ``H → A``.
    The same traversal is shared by dataset roots, rendered goals, local
    propositions, library statements, and proof-history statements.
    """

    from peano_lab.kernel.formulas import And, Exists, Forall, Imp, Or

    collisions: list[str] = []
    # Frames are ordered outermost-to-innermost.  Rebuilding in reverse keeps
    # the original de Bruijn indices and implication scope intact.
    stack: list[tuple[object, tuple[tuple[str, object | None], ...]]] = [
        (formula, ())
    ]
    while stack:
        current, frames = stack.pop()
        candidates = [current]
        if frames:
            scoped = current
            for kind, payload in reversed(frames):
                if kind == "imp":
                    scoped = Imp(payload, scoped)
                elif kind == "forall":
                    scoped = Forall(scoped)
                elif kind == "exists":
                    scoped = Exists(scoped)
                else:  # pragma: no cover - frames are constructed below
                    raise AssertionError("unknown formula scope frame")
            candidates.append(scoped)
        for candidate in candidates:
            goal_id = forbidden.get(candidate)
            if goal_id is not None:
                collisions.append(f"{goal_id}@{label}")
        if type(current) is Imp:
            stack.append(
                (current.right, frames + (("imp", current.left),))
            )
            stack.append((current.left, frames))
        elif type(current) in (And, Or):
            stack.append((current.right, frames))
            stack.append((current.left, frames))
        elif type(current) in (Forall, Exists):
            kind = "forall" if type(current) is Forall else "exists"
            stack.append((current.body, frames + ((kind, None),)))
    return collisions


def _tactic_surface_leaves(source: object, *, label: str) -> tuple[str, ...]:
    """Flatten every primitive leaf using the exact public tactical grammar."""

    from peano_lab.engine.tactics import TacticError
    from peano_lab.ui.prove import _first_items, _scan_split, _strip_group

    if type(source) is not str or not source.strip():
        raise AcceptanceError(f"{label} is not one non-empty tactic")
    leaves: list[str] = []
    budget = [0]

    def walk(raw: str) -> None:
        budget[0] += 1
        if budget[0] > 256:
            raise AcceptanceError(f"{label} exceeds the surface tactical node limit")
        text = _strip_group(raw.strip())
        alternatives = _scan_split(text, "<|>")
        if len(alternatives) > 1:
            for item in alternatives:
                walk(item)
            return
        sequence = _scan_split(text, ";")
        if len(sequence) > 1:
            for item in sequence:
                walk(item)
            return
        for prefix in ("repeat", "all_goals"):
            if re.match(rf"^{prefix}(?:\s|$)", text):
                child = text[len(prefix) :].strip()
                if not child:
                    raise AcceptanceError(f"{label} has malformed {prefix} syntax")
                walk(child)
                return
        if re.match(r"^focus(?:\s|$)", text):
            match = re.fullmatch(r"focus\s+(\d+)\s+(.+)", text, re.DOTALL)
            if match is None or int(match.group(1)) < 1:
                raise AcceptanceError(f"{label} has malformed focus syntax")
            walk(match.group(2))
            return
        if re.match(r"^first(?:\s|$)", text):
            match = re.fullmatch(r"first\s*\[(.*)\]", text, re.DOTALL)
            if match is None:
                raise AcceptanceError(f"{label} has malformed first syntax")
            for item in _first_items(match.group(1)):
                walk(item)
            return
        leaves.append(text)

    try:
        walk(source)
    except (TacticError, RecursionError) as exc:
        raise AcceptanceError(f"{label} has invalid tactical syntax: {exc}") from None
    return tuple(leaves)


def _tactic_local_propositions(source: object, *, label: str) -> tuple[str, ...]:
    """Extract every ``have``/``suffices`` proposition from the UI grammar.

    Dead ``first``/``orelse`` branches and nested combinators are deliberately
    included: visibility, rather than successful execution, defines leakage.
    """

    propositions: list[str] = []
    for leaf in _tactic_surface_leaves(source, label=label):
        pieces = leaf.split(maxsplit=1)
        name = pieces[0]
        if name not in {"have", "suffices"}:
            continue
        args = pieces[1].strip() if len(pieces) > 1 else ""
        local_name, separator, proposition = args.partition(":")
        if not separator or not local_name.strip() or not proposition.strip():
            raise AcceptanceError(f"{label} has malformed {name} syntax")
        propositions.append(proposition.strip())
    return tuple(propositions)


def _scan_tactic_propositions(
    tactics: Sequence[object],
    forbidden: Mapping[object, str],
    *,
    label: str,
    contexts: Sequence[tuple[Sequence[str], Sequence[str]]] = (),
) -> list[str]:
    from peano_lab.kernel.formulas import parse_formula_with_names

    collisions: list[str] = []
    for index, tactic in enumerate(tactics):
        tactic_label = f"{label}[{index}]"
        leaves = _tactic_surface_leaves(tactic, label=tactic_label)
        local_sources = _tactic_local_propositions(tactic, label=tactic_label)
        leaf_names = tuple(leaf.split(maxsplit=1)[0] for leaf in leaves)
        if local_sources and (
            any(name in {"intro", "cases", "induction"} for name in leaf_names)
            or len(local_sources) > 1
        ):
            raise AcceptanceError(
                f"{tactic_label} mixes local propositions with scope-changing "
                "tactics; split it into separate dataset steps"
            )
        for proposition_index, source in enumerate(local_sources):
            try:
                formula, free_names = parse_formula_with_names(source)
            except (TypeError, ValueError, RecursionError) as exc:
                raise AcceptanceError(
                    f"{tactic_label} has an invalid local proposition: {exc}"
                ) from None
            surface_sources: list[tuple[str, str]] = [("direct", source)]
            if free_names:
                surface_sources.append(
                    ("free-variable-closed", _close_formula_source(source, free_names))
                )
            for context_index, (variables, hypotheses) in enumerate(contexts):
                scope = tuple(variables)
                missing = tuple(name for name in free_names if name not in scope)
                scope += missing
                rigid_hypotheses = tuple(
                    hypothesis
                    for hypothesis in hypotheses
                    if re.search(r"\?t[0-9]+\b", hypothesis) is None
                )
                surface_sources.append(
                    (
                        f"context-closed[{context_index}]",
                        _close_formula_source(source, scope, rigid_hypotheses),
                    )
                )
            surfaces: list[tuple[str, object]] = []
            seen_sources: set[str] = set()
            for surface, candidate_source in surface_sources:
                if candidate_source in seen_sources:
                    continue
                seen_sources.add(candidate_source)
                try:
                    candidate, candidate_free_names = parse_formula_with_names(
                        candidate_source
                    )
                except (TypeError, ValueError, RecursionError) as exc:
                    raise AcceptanceError(
                        f"{tactic_label} local proposition cannot be closed: {exc}"
                    ) from None
                if surface != "direct" and candidate_free_names:
                    raise AcceptanceError(
                        f"{tactic_label} local proposition did not close"
                    )
                surfaces.append((surface, candidate))
            for surface, candidate in surfaces:
                collisions.extend(
                    _formula_subtree_collisions(
                        candidate,
                        forbidden,
                        label=(
                            f"{tactic_label}.proposition[{proposition_index}]."
                            f"{surface}"
                        ),
                    )
                )
    return collisions


def _validate_synthetic_row_redundancy(
    record: Mapping[str, object],
    *,
    formula: str,
    location: str,
) -> None:
    metadata = _mapping(record.get("metadata"), f"{location}.metadata")
    statement_sha256 = hashlib.sha256(formula.encode("utf-8")).hexdigest()
    template = _text(metadata.get("template"), f"{location}.metadata.template")
    root_material = json.dumps(
        [4, template, formula],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    root = f"synthetic-v2/{template}/{hashlib.sha256(root_material).hexdigest()[:20]}"
    expected_theorem = f"synthetic.{template}.{root.rsplit('/', 1)[-1]}"
    tactics = metadata.get("tactics")
    step = record.get("step")
    completion = record.get("completion")
    if (
        metadata.get("statement") != formula
        or metadata.get("statement_sha256") != statement_sha256
        or metadata.get("root") != root
        or record.get("family") != root
        or record.get("lineage") != root
        or record.get("theorem") != expected_theorem
        or type(tactics) is not list
        or not all(type(tactic) is str and tactic for tactic in tactics)
        or metadata.get("tactic_rows") != len(tactics)
        or type(step) is not int
        or not 1 <= step <= len(tactics)
        or completion != f"{tactics[step - 1]}</tactic>"
    ):
        raise AcceptanceError(f"{location} root/formula/script redundancy is forged")


def _scan_dataset_split(
    path: Path,
    split: str,
    expected: Mapping[str, object],
    forbidden: Mapping[object, str],
) -> dict[str, object]:
    """Hash one strict compiled split and reject acceptance-target roots."""

    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
    from training.peano_policy.contract import model_v2_environment
    from training.peano_policy.data import MAX_DATASET_LINE_BYTES, ROW_FIELDS
    from training.peano_policy.prompt import (
        PEANO_PROMPT_V2,
        parse_prompt,
        render_prompt,
    )

    split_path = _plain_file(path, f"{split} dataset split")
    environment = model_v2_environment()
    digest = hashlib.sha256()
    rows = 0
    contaminated: list[str] = []
    try:
        stream = split_path.open("rb")
    except OSError as exc:  # pragma: no cover - _plain_file already opened metadata
        raise AcceptanceError(f"cannot open {split_path}: {exc}") from None
    with stream:
        for line_number, raw in enumerate(stream, 1):
            digest.update(raw)
            if len(raw) > MAX_DATASET_LINE_BYTES or raw == b"\n" or not raw.endswith(
                b"\n"
            ):
                raise AcceptanceError(
                    f"{split_path}:{line_number} is not bounded complete JSONL"
                )
            try:
                text_value = raw[:-1].decode("utf-8")
                record = json.loads(
                    text_value,
                    object_pairs_hook=_reject_duplicate_keys,
                    parse_constant=_reject_constant,
                )
            except (UnicodeError, json.JSONDecodeError, AcceptanceError) as exc:
                raise AcceptanceError(
                    f"{split_path}:{line_number} is invalid: {exc}"
                ) from None
            if (
                type(record) is not dict
                or tuple(record) != ROW_FIELDS
                or record.get("split") != split
            ):
                raise AcceptanceError(
                    f"{split_path}:{line_number} is not a canonical {split} row"
                )
            formula_source = record.get("formula")
            try:
                formula, free_names = parse_formula_with_names(formula_source)
            except (TypeError, ValueError, RecursionError) as exc:
                raise AcceptanceError(
                    f"{split_path}:{line_number} has an invalid formula: {exc}"
                ) from None
            if free_names:
                raise AcceptanceError(
                    f"{split_path}:{line_number} has a non-closed formula"
                )
            if pretty_formula(formula, list(free_names)) != formula_source:
                raise AcceptanceError(
                    f"{split_path}:{line_number} has a non-canonical root formula"
                )
            location = f"{split_path}:{line_number}"
            _validate_synthetic_row_redundancy(
                record, formula=str(formula_source), location=location
            )
            state = record.get("state")
            if (
                type(state) is not list
                or not state
                or not all(type(goal) is str and goal for goal in state)
                or type(record.get("focus")) is not int
                or not 0 <= int(record["focus"]) < len(state)
                or record.get("v") != 1
                or record.get("task") != "next_tactic"
                or record.get("surface") != "model-v2"
                or record.get("classical") is not False
                or record.get("environment_sha256") != environment.sha256
                or record.get("env") != environment.text
                or record.get("capabilities") != environment.capabilities.to_record()
                or _mapping(record.get("metadata"), f"{location}.metadata").get(
                    "library_identity_sha256"
                )
                != environment.library_sha256
            ):
                raise AcceptanceError(f"{location} has forged model-v2 row authority")
            try:
                parsed = parse_prompt(record.get("prompt"))
                expected_prompt = render_prompt(
                    goals=state,
                    focus=record["focus"],
                    environment=environment,
                )
            except (TypeError, ValueError, RecursionError) as exc:
                raise AcceptanceError(f"{location} has an invalid prompt: {exc}") from None
            if (
                record.get("prompt") != expected_prompt
                or parsed.goals != tuple(state)
                or parsed.focus != record.get("focus")
                or parsed.prompt_version != PEANO_PROMPT_V2
                or parsed.environment != environment.text
                or parsed.environment_sha256 != environment.sha256
                or parsed.library_sha256 != environment.library_sha256
            ):
                raise AcceptanceError(f"{location} prompt/state redundancy is forged")
            contaminated.extend(
                _formula_subtree_collisions(
                    formula,
                    forbidden,
                    label=f"root:{line_number}",
                )
            )
            contaminated.extend(
                _scan_goal_targets(state, forbidden, label=f"row-state:{line_number}")
            )
            contaminated.extend(
                _scan_goal_targets(
                    parsed.goals,
                    forbidden,
                    label=f"prompt-state:{line_number}",
                )
            )
            metadata = _mapping(record.get("metadata"), f"{location}.metadata")
            tactics = _sequence(metadata.get("tactics"), f"{location}.metadata.tactics")
            contaminated.extend(
                _scan_tactic_propositions(
                    tactics,
                    forbidden,
                    label=f"tactic-script:{line_number}",
                )
            )
            focus = int(record["focus"])
            _target, variables, hypotheses = _goal_context_surface(
                state[focus], f"row-state:{line_number}[{focus}]"
            )
            contexts = ((variables, hypotheses),)
            contaminated.extend(
                _scan_tactic_propositions(
                    (tactics[int(record["step"]) - 1],),
                    forbidden,
                    label=f"completion:{line_number}",
                    contexts=contexts,
                )
            )
            rows += 1
    actual_sha256 = digest.hexdigest()
    if expected.get("rows") != rows or expected.get("sha256") != actual_sha256:
        raise AcceptanceError(f"{split} split count/hash differs from its manifest")
    if contaminated:
        raise AcceptanceError(
            f"acceptance target contamination in {split}: "
            + ", ".join(sorted(set(contaminated)))
        )
    return {"rows": rows, "sha256": actual_sha256, "contamination": 0}


def audit_dataset(
    data_directory: Path,
    manifest: Mapping[str, object],
    adapter: AdapterAuthority | None = None,
) -> dict[str, object]:
    """Bind and scan the exact corpus, before or after adapter training."""

    from peano_lab.kernel.formulas import parse_formula_with_names
    from training.peano_policy.contract import environment_record, model_v2_environment
    from training.peano_policy.data import load_dataset_manifest

    directory = _plain_directory(data_directory, "compiled dataset directory")
    subject = _mapping(manifest.get("subject"), "subject")
    contract = _mapping(subject.get("training_contract"), "training contract")
    expected_directory = _repository_path(
        _text(contract.get("dataset_directory"), "dataset directory"),
        "dataset directory",
    ).resolve(strict=False)
    if directory != expected_directory:
        raise AcceptanceError("dataset must occupy the preregistered repository path")
    data_manifest_path = _plain_file(
        directory / DATASET_MANIFEST, "compiled dataset manifest"
    )
    source_manifest_path = _plain_file(
        directory / DATASET_SOURCE_MANIFEST, "dataset source manifest"
    )
    attestation_path = _plain_file(
        directory / DATASET_ATTESTATION, "dataset attestation"
    )
    try:
        compiled = load_dataset_manifest(data_manifest_path)
    except (OSError, TypeError, ValueError) as exc:
        raise AcceptanceError(f"compiled dataset manifest is invalid: {exc}") from None
    source = _read_json(source_manifest_path)
    attestation = _read_json(attestation_path)
    training_inputs: dict[str, object] | None = None
    if adapter is not None:
        training_inputs = _mapping(adapter.manifest.get("inputs"), "training inputs")
        embedded = _mapping(
            training_inputs.get("dataset_attestation"),
            "embedded dataset attestation",
        )
        if attestation != embedded:
            raise AcceptanceError("on-disk and training-embedded attestations differ")

    source_config = _mapping(source.get("config"), "source corpus config")
    source_counts = _mapping(source.get("counts"), "source corpus counts")
    if (
        source.get("format") != "peano-policy-corpus"
        or source.get("version") != 1
        or source.get("profile") != contract.get("dataset_profile")
        or source.get("generator") != contract.get("dataset_generator")
        or source.get("catalog_version") != contract.get("dataset_catalog_version")
        or source_config.get("seed") != contract.get("dataset_seed")
        or source_config.get("row_budget") != contract.get("positive_tactic_rows")
        or source_counts.get("positive_tactic_rows")
        != contract.get("positive_tactic_rows")
        or source.get("environment") != environment_record(model_v2_environment())
    ):
        raise AcceptanceError("source corpus is not the preregistered 100k model-v2 run")

    compiled_sha256 = _sha256_file(data_manifest_path)
    if training_inputs is not None:
        for field in ("train_dataset_manifest", "eval_dataset_manifest"):
            record = _mapping(training_inputs.get(field), f"training {field}")
            if record.get("sha256") != compiled_sha256:
                raise AcceptanceError("training manifest names another compiled dataset")
    expected_dataset_sha256 = _text(
        contract.get("dataset_sha256"), "training contract dataset_sha256"
    )
    if compiled.get("dataset_sha256") != expected_dataset_sha256:
        raise AcceptanceError("compiled dataset is not the realized sealed corpus")
    if (
        attestation.get("manifest_sha256") != compiled_sha256
        or attestation.get("dataset_sha256") != expected_dataset_sha256
    ):
        raise AcceptanceError("dataset attestation names another compiled corpus")
    if adapter is not None and adapter.identity["dataset_sha256"] != expected_dataset_sha256:
        raise AcceptanceError("compiled and trained dataset identities differ")
    replay = _mapping(compiled.get("replay"), "compiled replay")
    if replay.get("positive_rows") != contract.get("positive_tactic_rows"):
        raise AcceptanceError("compiled dataset does not contain exactly 100k rows")
    splits = _mapping(compiled.get("splits"), "compiled splits")
    attested_splits = _mapping(attestation.get("splits"), "attested splits")
    if set(splits) != set(DATASET_SPLITS) or set(attested_splits) != set(
        DATASET_SPLITS
    ):
        raise AcceptanceError("compiled dataset has the wrong split set")

    forbidden: dict[object, str] = {}
    for goal in _goal_records(manifest):
        if goal["category"] == "retrieval":
            continue
        formula, free_names = parse_formula_with_names(str(goal["statement"]))
        if free_names:  # pragma: no cover - manifest validation catches this first
            raise AcceptanceError("acceptance target unexpectedly has free names")
        forbidden[formula] = str(goal["id"])

    aggregate = hashlib.sha256()
    split_audit: dict[str, object] = {}
    for split in DATASET_SPLITS:
        expected = _mapping(splits.get(split), f"compiled {split}")
        attested = _mapping(attested_splits.get(split), f"attested {split}")
        if {
            "rows": expected.get("rows"),
            "sha256": expected.get("sha256"),
        } != attested:
            raise AcceptanceError(f"compiled and attested {split} records differ")
        split_path = directory / f"{split}.jsonl"
        record = _scan_dataset_split(split_path, split, expected, forbidden)
        split_audit[split] = record
        aggregate.update(split.encode("ascii") + b"\0")
        with split_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                aggregate.update(chunk)
    if aggregate.hexdigest() != expected_dataset_sha256:
        raise AcceptanceError("compiled dataset aggregate hash differs from training")
    if training_inputs is not None:
        train_input = _mapping(training_inputs.get("train_data"), "training train_data")
        eval_input = _mapping(training_inputs.get("eval_data"), "training eval_data")
        if (
            train_input.get("sha256")
            != _mapping(split_audit["train"], "train audit").get("sha256")
            or eval_input.get("sha256")
            != _mapping(split_audit["val"], "val audit").get("sha256")
        ):
            raise AcceptanceError("training split hashes differ from the audited files")

    raw_artifacts = _mapping(source.get("artifacts"), "source artifacts")
    attested_artifacts = _mapping(
        attestation.get("source_artifacts"), "attested source artifacts"
    )
    source_hashes: dict[str, str] = {}
    for label, filename in (
        ("trace", "raw-traces.jsonl"),
        ("metadata", "session-metadata.jsonl"),
    ):
        record = _mapping(raw_artifacts.get(label), f"source {label}")
        artifact = _plain_file(directory / filename, f"source {label}")
        if record.get("path") != filename or record.get("sha256") != _sha256_file(
            artifact
        ):
            raise AcceptanceError(f"source {label} bytes differ from their manifest")
        source_hashes[label] = str(record.get("sha256"))
    if (
        attested_artifacts.get("metadata") != source_hashes["metadata"]
        or attested_artifacts.get("traces") != [source_hashes["trace"]]
    ):
        raise AcceptanceError("source artifacts differ from the training attestation")

    positive_rows = sum(
        int(_mapping(split_audit[name], name)["rows"]) for name in DATASET_SPLITS
    )
    realized_rows = {
        name: int(_mapping(split_audit[name], name)["rows"]) for name in DATASET_SPLITS
    }
    if (
        positive_rows != contract.get("positive_tactic_rows")
        or realized_rows != contract.get("realized_split_rows")
    ):
        raise AcceptanceError("audited split row total differs from preregistration")
    result: dict[str, object] = {
        "format": "peano-policy-acceptance-data-audit",
        "v": 1,
        "phase": "post-training" if adapter is not None else "pre-training",
        "dataset_sha256": expected_dataset_sha256,
        "compiled_manifest_sha256": compiled_sha256,
        "source_manifest_sha256": _sha256_file(source_manifest_path),
        "attestation_sha256": _sha256_file(attestation_path),
        "positive_tactic_rows": positive_rows,
        "forbidden_goal_ids": [
            str(goal["id"])
            for goal in _goal_records(manifest)
            if goal["category"] != "retrieval"
        ],
        "contamination": 0,
        "splits": split_audit,
    }
    if adapter is not None:
        result["pretraining_report_sha256"] = _validate_pretraining_data_report(
            manifest, result
        )
    return result


def _pretraining_data_report(
    manifest: Mapping[str, object],
    *,
    manifest_path: Path,
    data_audit: Mapping[str, object],
) -> dict[str, object]:
    from training.peano_policy.runtime import slurm_job_identity, source_sync_identity

    chain = _validate_finalize_submission_chain(
        manifest, _load_submission_ledger(manifest)
    )
    source_sync = source_sync_identity(required=True)
    if source_sync != _expected_source_sync(chain["prepare"]):
        raise AcceptanceError(
            "pre-training data audit is not running at the recovery finalizer's "
            "sealed source"
        )
    finalizer_job = _validate_job_identity(
        slurm_job_identity(),
        expected_row=chain["prepare"],
        expected_script=WMI_PREPARE_SCRIPT,
        expected_job_name="peano-wmi-v2-finalize",
        label="pre-training finalizer job",
    )
    snapshot_checks = _validated_finalizer_snapshot_checks(
        manifest, chain["prepare"]
    )
    finalizer_gates = _validated_finalizer_gate_artifacts(
        manifest, chain["prepare"], data_audit=data_audit
    )
    return {
        "format": "peano-policy-acceptance-data-pretraining",
        "v": 1,
        "created_at": _now_utc(),
        "preregistration": {
            "id": manifest.get("preregistration_id"),
            "sha256": _sha256_file(manifest_path),
        },
        "tool": {
            "name": Path(__file__).name,
            "sha256": _sha256_file(Path(__file__)),
        },
        "primary_semantic_source": _validated_primary_semantic_source(manifest),
        "training_source_sync": source_sync,
        "finalizer_job": finalizer_job,
        "base_snapshot_checks": snapshot_checks,
        "finalizer_gates": finalizer_gates,
        "data_audit": dict(data_audit),
    }


def _base_snapshot_check_path(job_id: str, phase: str) -> Path:
    if _JOB_ID_RE.fullmatch(job_id) is None or phase not in {"before", "after"}:
        raise AcceptanceError("base snapshot check identity is malformed")
    return _repository_path(
        f"logs/peano-wmi-v2-base-snapshot-{phase}-{job_id}.json",
        f"base snapshot {phase} report",
    )


def _validated_finalizer_snapshot_checks(
    manifest: Mapping[str, object], finalizer: Mapping[str, str]
) -> dict[str, object]:
    from training.peano_policy.base_snapshot import expected_base_snapshot

    job_id = _text(finalizer.get("job_id"), "finalizer job id")
    expected_authority = _base_snapshot_authority(manifest)
    expected_snapshot = expected_base_snapshot()
    result: dict[str, object] = {}
    timestamps: list[datetime] = []
    for phase in ("before", "after"):
        path = _plain_file(
            _base_snapshot_check_path(job_id, phase),
            f"base snapshot {phase} report",
        )
        report = _read_json(path)
        identity = _mapping(
            report.get("identity"), f"base snapshot {phase} identity"
        )
        if (
            set(report) != {"format", "v", "phase", "created_at", "job_id", "identity"}
            or report.get("format") != "peano-policy-base-snapshot-check"
            or report.get("v") != 1
            or report.get("phase") != phase
            or report.get("job_id") != job_id
            or identity != expected_snapshot
            or identity.get("sha256") != expected_authority.get("snapshot_sha256")
        ):
            raise AcceptanceError(
                f"finalizer base snapshot {phase} report has the wrong identity"
            )
        timestamps.append(
            _utc_timestamp(
                report.get("created_at"), f"base snapshot {phase} created_at"
            )
        )
        result[phase] = {
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": _sha256_file(path),
            "identity": identity,
        }
    if timestamps[0] > timestamps[1]:
        raise AcceptanceError("finalizer base snapshot checks are out of order")
    return result


def _validated_finalizer_gate_artifacts(
    manifest: Mapping[str, object],
    finalizer: Mapping[str, str],
    *,
    data_audit: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Validate and bind every job-specific finalizer success artifact."""

    from training.peano_policy.base_snapshot import expected_base_snapshot

    job_id = _text(finalizer.get("job_id"), "finalizer job id")
    contract = _mapping(
        _mapping(manifest.get("subject"), "subject").get("training_contract"),
        "training contract",
    )
    expected_snapshot = expected_base_snapshot()
    dataset_directory = _repository_path(
        _text(contract.get("dataset_directory"), "dataset directory"),
        "dataset directory",
    )
    fixed_attestation_path = _plain_file(
        dataset_directory / DATASET_ATTESTATION, "fixed dataset attestation"
    )
    fixed_attestation = _read_json(fixed_attestation_path)

    attestation_path = _plain_file(
        _repository_path(
            f"logs/peano-wmi-v2-dataset-attestation-{job_id}.json",
            "finalizer dataset attestation",
        ),
        "finalizer dataset attestation",
    )
    attestation = _read_json(attestation_path)
    attested_splits = _mapping(attestation.get("splits"), "finalizer attested splits")
    if (
        attestation != fixed_attestation
        or attestation.get("format") != "peano-policy-dataset-attestation"
        or attestation.get("v") != 1
        or attestation.get("independent_replay") is not True
        or attestation.get("held_out_contamination") != 0
        or attestation.get("dataset_sha256") != contract.get("dataset_sha256")
        or set(attested_splits) != set(DATASET_SPLITS)
        or {
            split: _mapping(attested_splits.get(split), f"attested {split}").get(
                "rows"
            )
            for split in DATASET_SPLITS
        }
        != contract.get("realized_split_rows")
    ):
        raise AcceptanceError("finalizer dataset attestation is not the sealed replay")

    token_path = _plain_file(
        _repository_path(
            f"logs/peano-wmi-v2-token-audit-{job_id}.json",
            "finalizer token audit",
        ),
        "finalizer token audit",
    )
    token = _read_json(token_path)
    token_config = _mapping(token.get("config"), "finalizer token config")
    token_model = _mapping(token.get("tokenizer"), "finalizer tokenizer")
    token_inputs = _mapping(token.get("inputs"), "finalizer token inputs")
    token_splits = _mapping(token.get("splits"), "finalizer token splits")
    token_snapshot = _mapping(token.get("base_snapshot"), "finalizer token snapshot")
    config_relative = _text(contract.get("config_path"), "training config path")
    expected_rows = {
        "train": contract.get("training_examples"),
        "eval": contract.get("eval_examples"),
    }
    for split, expected_rows_count in expected_rows.items():
        summary = _mapping(token_splits.get(split), f"finalizer token {split}")
        if (
            set(summary)
            != {"rows", "minimum", "median", "p95", "p99", "maximum", "mean", "budget", "headroom"}
            or summary.get("rows") != expected_rows_count
            or summary.get("budget") != 2048
            or type(summary.get("maximum")) is not int
            or int(summary["maximum"]) > 2048
            or summary.get("headroom") != 2048 - int(summary["maximum"])
            or int(summary["headroom"]) < 0
        ):
            raise AcceptanceError(f"finalizer {split} token audit is incomplete")
    expected_split_hashes = (
        {
            split: _mapping(
                _mapping(data_audit.get("splits"), "data audit splits").get(split),
                f"data audit {split}",
            ).get("sha256")
            for split in ("train", "val")
        }
        if data_audit is not None
        else None
    )
    if (
        set(token) != {
            "format", "v", "status", "config", "tokenizer", "base_snapshot", "inputs", "splits"
        }
        or token.get("format") != "peano-policy-token-audit"
        or token.get("v") != 1
        or token.get("status") != "passed"
        or token_config
        != {
            "path": f"{WMI_PROJECT_ROOT}/{config_relative}",
            "sha256": contract.get("config_sha256"),
            "max_length": 2048,
        }
        or token_model.get("model_id") != "Qwen/Qwen3-1.7B-Base"
        or token_model.get("requested_revision")
        != "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
        or token_model.get("resolved_revision")
        != "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
        or token_snapshot
        != {"before_load": expected_snapshot, "after_audit": expected_snapshot}
        or set(token_inputs) != {"train", "eval"}
        or _mapping(token_inputs.get("train"), "token train input").get("path")
        != "data/peano-policy-v2/train.jsonl"
        or _mapping(token_inputs.get("eval"), "token eval input").get("path")
        != "data/peano-policy-v2/val.jsonl"
        or (
            expected_split_hashes is not None
            and (
                _mapping(token_inputs.get("train"), "token train input").get("sha256")
                != expected_split_hashes["train"]
                or _mapping(token_inputs.get("eval"), "token eval input").get("sha256")
                != expected_split_hashes["val"]
            )
        )
    ):
        raise AcceptanceError("finalizer token audit is not the sealed full-corpus gate")

    smoke_path = _plain_file(
        _repository_path(
            f"logs/peano-wmi-v2-finalize-runtime-{job_id}.json",
            "finalizer A100 smoke",
        ),
        "finalizer A100 smoke",
    )
    smoke = _read_json(smoke_path)
    smoke_model = _mapping(smoke.get("model"), "finalizer smoke model")
    smoke_snapshot = _mapping(smoke.get("base_snapshot"), "finalizer smoke snapshot")
    smoke_job = _mapping(smoke.get("job"), "finalizer smoke job")
    _validate_job_identity(
        smoke_job,
        expected_row=finalizer,
        expected_script=WMI_PREPARE_SCRIPT,
        expected_job_name="peano-wmi-v2-finalize",
        label="finalizer smoke job",
    )
    if (
        smoke.get("format") != "peano-policy-wmi-a100-v2-smoke"
        or smoke.get("v") != 1
        or smoke.get("status") != "passed"
        or smoke_model
        != {
            "id": "Qwen/Qwen3-1.7B-Base",
            "requested_revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
            "model_commit": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
            "tokenizer_commit": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        }
        or smoke_snapshot
        != {"before_load": expected_snapshot, "after_reload": expected_snapshot}
        or smoke.get("platform_contract")
        != {
            "expected_machine": "x86_64",
            "minimum_cuda_capability": [8, 0],
            "report_format": "peano-policy-wmi-a100-v2-smoke",
        }
    ):
        raise AcceptanceError("finalizer A100 smoke is not the allocated gate")

    return {
        "dataset_attestation": {
            "path": attestation_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": _sha256_file(attestation_path),
            "dataset_sha256": attestation["dataset_sha256"],
        },
        "token_audit": {
            "path": token_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": _sha256_file(token_path),
            "config_sha256": token_config["sha256"],
            "train_rows": expected_rows["train"],
            "eval_rows": expected_rows["eval"],
        },
        "a100_smoke": {
            "path": smoke_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": _sha256_file(smoke_path),
            "job_id": job_id,
        },
    }


def record_base_snapshot_check(
    manifest: Mapping[str, object], *, phase: str
) -> Path:
    """Atomically record one allocated-finalizer cache check."""

    from training.peano_policy.runtime import slurm_job_identity

    chain = _validate_finalize_submission_chain(
        manifest, _load_submission_ledger(manifest)
    )
    job = _validate_job_identity(
        slurm_job_identity(),
        expected_row=chain["prepare"],
        expected_script=WMI_PREPARE_SCRIPT,
        expected_job_name="peano-wmi-v2-finalize",
        label="base snapshot finalizer job",
    )
    identity = _validated_base_snapshot(manifest)
    path = _base_snapshot_check_path(str(job["job_id"]), phase)
    record = {
        "format": "peano-policy-base-snapshot-check",
        "v": 1,
        "phase": phase,
        "created_at": _now_utc(),
        "job_id": job["job_id"],
        "identity": identity,
    }
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise AcceptanceError("base snapshot report parent is not a plain directory")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(_render(record, compact=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise AcceptanceError("base snapshot phase report already exists") from None
    except OSError as exc:
        raise AcceptanceError(f"cannot publish base snapshot report: {exc}") from None
    return path


def _validated_pretraining_report(
    manifest: Mapping[str, object],
    chain: Mapping[str, Mapping[str, str]],
    *,
    adapter_dataset_sha256: str | None = None,
    expected_audit: Mapping[str, object] | None = None,
) -> tuple[Path, dict[str, object]]:
    path = _plain_file(
        _repository_path(WMI_PRETRAIN_DATA_AUDIT, "pre-training data report"),
        "pre-training data report",
    )
    report = _read_json(path)
    preregistration = _mapping(
        report.get("preregistration"), "pre-training preregistration"
    )
    tool = _mapping(report.get("tool"), "pre-training audit tool")
    semantic_source = _mapping(
        report.get("primary_semantic_source"), "pre-training semantic source"
    )
    source_sync = _mapping(
        report.get("training_source_sync"), "pre-training source sync"
    )
    finalizer_job = _mapping(
        report.get("finalizer_job"), "pre-training finalizer job"
    )
    snapshot_checks = _mapping(
        report.get("base_snapshot_checks"), "pre-training base snapshot checks"
    )
    finalizer_gates = _mapping(
        report.get("finalizer_gates"), "pre-training finalizer gates"
    )
    audit = _mapping(report.get("data_audit"), "pre-training data audit")
    contract = _mapping(
        _mapping(manifest.get("subject"), "subject").get("training_contract"),
        "training contract",
    )
    if (
        set(report)
        != {
            "format",
            "v",
            "created_at",
            "preregistration",
            "tool",
            "primary_semantic_source",
            "training_source_sync",
            "finalizer_job",
            "base_snapshot_checks",
            "finalizer_gates",
            "data_audit",
        }
        or report.get("format") != "peano-policy-acceptance-data-pretraining"
        or report.get("v") != 1
        or preregistration
        != {
            "id": manifest.get("preregistration_id"),
            "sha256": EXPECTED_MANIFEST_SHA256,
        }
        or tool
        != {
            "name": "peano_policy_acceptance.py",
            "sha256": _sha256_file(Path(__file__)),
        }
        or semantic_source != _validated_primary_semantic_source(manifest)
        or source_sync != _expected_source_sync(chain["prepare"])
        or snapshot_checks
        != _validated_finalizer_snapshot_checks(manifest, chain["prepare"])
        or finalizer_gates
        != _validated_finalizer_gate_artifacts(
            manifest, chain["prepare"], data_audit=audit
        )
    ):
        raise AcceptanceError("pre-training data audit report is not the sealed scan")
    _validate_job_identity(
        finalizer_job,
        expected_row=chain["prepare"],
        expected_script=WMI_PREPARE_SCRIPT,
        expected_job_name="peano-wmi-v2-finalize",
        label="pre-training finalizer job",
    )
    splits = _mapping(audit.get("splits"), "pre-training audited splits")
    realized = {
        name: _mapping(splits.get(name), f"pre-training {name}").get("rows")
        for name in DATASET_SPLITS
    }
    if (
        audit.get("format") != "peano-policy-acceptance-data-audit"
        or audit.get("v") != 1
        or audit.get("phase") != "pre-training"
        or audit.get("dataset_sha256") != contract.get("dataset_sha256")
        or (
            adapter_dataset_sha256 is not None
            and audit.get("dataset_sha256") != adapter_dataset_sha256
        )
        or audit.get("positive_tactic_rows") != contract.get("positive_tactic_rows")
        or audit.get("contamination") != 0
        or set(splits) != set(DATASET_SPLITS)
        or realized != contract.get("realized_split_rows")
        or any(
            _SHA256_RE.fullmatch(str(audit.get(field))) is None
            for field in (
                "compiled_manifest_sha256",
                "source_manifest_sha256",
                "attestation_sha256",
            )
        )
        or audit.get("forbidden_goal_ids")
        != [
            str(goal["id"])
            for goal in _goal_records(manifest)
            if goal["category"] != "retrieval"
        ]
        or (expected_audit is not None and audit != dict(expected_audit))
    ):
        raise AcceptanceError("pre-training data audit report has the wrong identity")
    report_created = _utc_timestamp(
        report.get("created_at"), "pre-training report created_at"
    )
    snapshot_times = []
    for phase in ("before", "after"):
        snapshot_record = _mapping(
            snapshot_checks.get(phase), f"pre-training snapshot {phase}"
        )
        snapshot_report = _read_json(
            _repository_path(
                _text(snapshot_record.get("path"), f"snapshot {phase} path"),
                f"snapshot {phase} report",
            )
        )
        snapshot_times.append(
            _utc_timestamp(
                snapshot_report.get("created_at"), f"snapshot {phase} created_at"
            )
        )
    if not snapshot_times[0] <= snapshot_times[1] <= report_created:
        raise AcceptanceError("finalizer snapshot/report timestamps are out of order")
    return path, report


def _validate_pretraining_data_report(
    manifest: Mapping[str, object],
    post_training_audit: Mapping[str, object],
) -> str:
    expected_audit = dict(post_training_audit)
    expected_audit["phase"] = "pre-training"
    expected_audit.pop("pretraining_report_sha256", None)
    chain = _validate_training_submission_chain(
        manifest, _load_submission_ledger(manifest)
    )
    path, report = _validated_pretraining_report(
        manifest, chain, expected_audit=expected_audit
    )
    _validate_pretraining_report_time(
        path, report.get("created_at"), chain["train"].get("timestamp")
    )
    return _sha256_file(path)


def _validate_pretraining_report_identity(
    manifest: Mapping[str, object],
    adapter: AdapterAuthority,
) -> str:
    """Check the fixed audit seal cheaply before submitting the GPU primary."""

    chain = _validate_training_submission_chain(
        manifest, _load_submission_ledger(manifest)
    )
    path, report = _validated_pretraining_report(
        manifest,
        chain,
        adapter_dataset_sha256=adapter.identity.get("dataset_sha256"),
    )
    _validate_pretraining_report_time(
        path, report.get("created_at"), chain["train"].get("timestamp")
    )
    return _sha256_file(path)


def preflight_training_submission(manifest: Mapping[str, object]) -> dict[str, object]:
    """Validate the fixed finalizer seal without rescanning the 100k corpus."""

    chain = _validate_finalize_submission_chain(
        manifest, _load_submission_ledger(manifest)
    )
    _require_completed_jobs(chain, ("prepare",))
    generator = _require_dataset_generator_terminal(chain)
    path, report = _validated_pretraining_report(manifest, chain)
    _validate_pretraining_report_time(
        path,
        report.get("created_at"),
        datetime.now(timezone.utc).isoformat(),
    )
    return {
        "status": "ready-for-one-training-submission",
        "dataset_generator_job_id": chain["generator"]["job_id"],
        "dataset_generator": generator,
        "finalizer_job_id": chain["prepare"]["job_id"],
        "finalizer_gates": report["finalizer_gates"],
        "base_snapshot_checks": report["base_snapshot_checks"],
        "pretraining_report_sha256": _sha256_file(path),
    }


def _base_policy(identity: object, label: str) -> dict[str, object]:
    wrapper = _mapping(identity, label)
    base = wrapper.get("base_policy")
    if type(base) is not dict:
        raise AcceptanceError(f"{label} has no base policy identity")
    return base


def _validate_base_policy(
    base: Mapping[str, object],
    manifest: Mapping[str, object],
    *,
    runner: str,
    adapter_identity: Mapping[str, str],
) -> tuple[str, str, str, str]:
    from training.peano_policy.contract import model_v2_environment
    from training.peano_policy.prompt import PEANO_PROMPT_V2, prompt_contract_sha256

    subject = _mapping(manifest.get("subject"), "subject")
    authority = _mapping(subject.get("authority"), "subject.authority")
    protocol = _mapping(manifest.get("protocol"), "protocol")
    run = _mapping(protocol.get(runner), f"protocol.{runner}")
    environment = _mapping(base.get("environment"), "base policy environment")
    expected_environment = model_v2_environment()
    if (
        base.get("kind") != "peano-policy-adapter-v1"
        or type(base.get("name")) is not str
        or not str(base.get("name")).strip()
        or
        environment.get("surface") != authority.get("surface")
        or environment.get("classical") is not False
        or environment.get("environment_sha256")
        != authority.get("environment_sha256")
        or environment.get("capabilities")
        != expected_environment.capabilities.to_record()
    ):
        raise AcceptanceError("report uses the wrong model-v2 authority")
    if (
        base.get("prompt_version") != PEANO_PROMPT_V2
        or base.get("prompt_contract_sha256")
        != prompt_contract_sha256(PEANO_PROMPT_V2)
        or base.get("decoding") != run.get("decoding")
    ):
        raise AcceptanceError(f"report uses the wrong {runner} decoder")
    provenance = _mapping(base.get("provenance"), "base policy provenance")
    expected_model = _mapping(subject.get("base_model"), "subject.base_model")
    expected = {
        "run_name": subject.get("run_name"),
        "base_model_id": expected_model.get("id"),
        "base_model_revision": expected_model.get("revision"),
        "environment_sha256": authority.get("environment_sha256"),
        "held_out_contract_sha256": authority.get("held_out_contract_sha256"),
        "library_snapshot_sha256": authority.get("library_identity_sha256"),
        "base_snapshot_sha256": _base_snapshot_authority(manifest).get(
            "snapshot_sha256"
        ),
    }
    for field, value in expected.items():
        if provenance.get(field) != value:
            raise AcceptanceError(f"adapter provenance has wrong {field}")
    identity_fields = (
        provenance.get("training_manifest_sha256"),
        provenance.get("adapter_sha256"),
        provenance.get("dataset_sha256"),
        provenance.get("base_snapshot_sha256"),
    )
    if not all(
        type(value) is str and _SHA256_RE.fullmatch(value)
        for value in identity_fields
    ):
        raise AcceptanceError("adapter provenance has incomplete content hashes")
    if identity_fields != (
        adapter_identity.get("training_manifest_sha256"),
        adapter_identity.get("adapter_sha256"),
        adapter_identity.get("dataset_sha256"),
        adapter_identity.get("base_snapshot_sha256"),
    ):
        raise AcceptanceError("report identity does not match the supplied adapter")
    return identity_fields  # type: ignore[return-value]


def _capabilities() -> object:
    from peano_lab.ui.prove import SurfaceCapabilities
    from training.peano_policy.contract import model_v2_environment

    environment = model_v2_environment()
    return SurfaceCapabilities(
        label="model-v2",
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )


def _kernel_replay(
    goal_id: str,
    statement: str,
    commands: Sequence[object],
    expected_nodes: object,
) -> bool:
    from peano_lab.batch import verify_proof

    if not all(type(command) is str for command in commands):
        raise AcceptanceError(f"{goal_id} commands must be text")
    replay = verify_proof(
        statement,
        tuple(commands),
        request_id=f"acceptance-{goal_id}",
        classical=False,
        capabilities=_capabilities(),
    )
    return bool(
        replay.status == "proved"
        and replay.kernel_checked is True
        and replay.theorem == statement
        and replay.failed_tactics == 0
        and replay.tactics_applied == len(commands)
        and replay.proof_nodes == expected_nodes
    )


def _validate_search_accounting(
    goal_id: str,
    search: Mapping[str, object],
    budget: Mapping[str, object],
    *,
    candidate_lines: int | None = None,
) -> dict[str, int]:
    """Check invariants implied by ``training.peano_policy.search`` itself."""

    counters: dict[str, int] = {}
    limits = {
        "model_calls": "max_model_calls",
        "states_discovered": "max_states",
        "frontier_peak": "beam_width",
        "depth_reached": "max_depth",
    }
    for field in (
        "model_calls",
        "states_expanded",
        "states_discovered",
        "candidates_executed",
        "frontier_peak",
        "depth_reached",
    ):
        value = search.get(field)
        minimum = 0 if field in {"candidates_executed", "depth_reached"} else 1
        if type(value) is not int or value < minimum:
            raise AcceptanceError(f"{goal_id} has invalid {field} accounting")
        counters[field] = value
    for field, limit in limits.items():
        if counters[field] > budget[limit]:
            raise AcceptanceError(f"{goal_id} exceeds its {field} budget")
    if (
        counters["states_expanded"] != counters["model_calls"]
        or counters["states_expanded"] > counters["states_discovered"]
        or counters["states_discovered"] > counters["candidates_executed"] + 1
        or counters["frontier_peak"]
        > min(int(budget["beam_width"]), counters["states_discovered"])
        or counters["candidates_executed"]
        > counters["model_calls"] * int(budget["candidates_per_state"])
        or (
            candidate_lines is not None
            and counters["candidates_executed"] > candidate_lines
        )
    ):
        raise AcceptanceError(f"{goal_id} search counters are mutually inconsistent")
    commands = _sequence(search.get("commands"), f"{goal_id}.commands")
    status = search.get("status")
    if (
        len(commands) > budget["max_depth"]
        or (status == "proof" and counters["depth_reached"] != len(commands))
        or (status != "proof" and commands)
    ):
        raise AcceptanceError(f"{goal_id} command/depth accounting is inconsistent")
    diagnostics = _sequence(search.get("diagnostics"), f"{goal_id}.diagnostics")
    for index, raw in enumerate(diagnostics):
        diagnostic = _mapping(raw, f"{goal_id}.diagnostics[{index}]")
        if set(diagnostic) != {
            "kind",
            "depth",
            "state_sha256",
            "command",
            "message",
        }:
            raise AcceptanceError(f"{goal_id} diagnostic schema changed")
        depth = diagnostic.get("depth")
        command = diagnostic.get("command")
        message = diagnostic.get("message")
        if (
            type(diagnostic.get("kind")) is not str
            or not diagnostic.get("kind")
            or type(depth) is not int
            or not 0 <= depth <= budget["max_depth"]
            or type(diagnostic.get("state_sha256")) is not str
            or _SHA256_RE.fullmatch(str(diagnostic.get("state_sha256"))) is None
            or (command is not None and (type(command) is not str or not command))
            or type(message) is not str
            or not message
            or len(message) > 1_000
        ):
            raise AcceptanceError(f"{goal_id} has a malformed search diagnostic")
    return counters


def _interactive_outcome(
    goal: Mapping[str, object],
    report: Mapping[str, object],
    manifest: Mapping[str, object],
    adapter_identity: Mapping[str, str],
) -> tuple[GoalOutcome, tuple[str, str, str, str]]:
    goal_id = str(goal["id"])
    statement = str(goal["statement"])
    if (
        report.get("format") != "peano-policy-interactive-result"
        or report.get("v") != 1
    ):
        raise AcceptanceError(f"{goal_id} is not an interactive result")
    request = _mapping(report.get("request"), f"{goal_id}.request")
    if request.get("canonical_theorem") != statement:
        raise AcceptanceError(f"{goal_id} report has the wrong theorem")
    run = _mapping(
        _mapping(manifest.get("protocol"), "protocol").get("interactive"),
        "protocol.interactive",
    )
    if report.get("budget") != run.get("search_budget_per_goal"):
        raise AcceptanceError(f"{goal_id} report has the wrong search budget")
    adapter = _mapping(report.get("adapter"), f"{goal_id}.adapter")
    base = _base_policy(adapter.get("policy"), f"{goal_id}.adapter.policy")
    identity = _validate_base_policy(
        base,
        manifest,
        runner="interactive",
        adapter_identity=adapter_identity,
    )
    authority = _mapping(report.get("authority"), f"{goal_id}.authority")
    base_environment = _mapping(base.get("environment"), "base policy environment")
    if authority.get("classical") is not False or authority.get(
        "capabilities"
    ) != base_environment.get("capabilities"):
        raise AcceptanceError(f"{goal_id} execution authority differs from its adapter")
    policy = _mapping(adapter.get("policy"), f"{goal_id}.adapter.policy")
    if (
        policy.get("kind") != "peano-kernel-guided-candidate-policy-v1"
        or policy.get("seed") != run.get("seed")
        or policy.get("seed_schedule")
        != "sha256-json-v1(seed,call_index,canonical_goals)"
        or policy.get("batching")
        != "one-model-generate-call-per-search-state"
    ):
        raise AcceptanceError(f"{goal_id} report has the wrong seed")
    search = _mapping(report.get("search"), f"{goal_id}.search")
    commands = _sequence(search.get("commands"), f"{goal_id}.commands")
    budget = _mapping(run.get("search_budget_per_goal"), "interactive budget")
    _validate_search_accounting(goal_id, search, budget)
    if (
        search.get("theorem") != statement
        or search.get("status") not in {"proof", "exhausted", "limit"}
    ):
        raise AcceptanceError(f"{goal_id} search result exceeds its fixed budget")
    publication = _mapping(report.get("publication"), f"{goal_id}.publication")
    proved = publication.get("status") == "kernel-checked-proof"
    nodes = search.get("certificate_nodes")
    if nodes is not None and (type(nodes) is not int or nodes < 1):
        raise AcceptanceError(f"{goal_id} has invalid proof-node accounting")
    kernel_checked = False
    if proved:
        verification = _mapping(
            report.get("kernel_verification"), f"{goal_id}.kernel_verification"
        )
        if (
            search.get("status") != "proof"
            or verification.get("status") != "proved"
            or verification.get("kernel_checked") is not True
            or verification.get("theorem") != statement
            or verification.get("surface") != "model-v2"
            or verification.get("classical") is not False
            or verification.get("failed_tactics") != 0
            or verification.get("tactics_applied") != len(commands)
            or verification.get("proof_nodes") != nodes
        ):
            raise AcceptanceError(f"{goal_id} publication lacks exact kernel evidence")
        kernel_checked = _kernel_replay(goal_id, statement, commands, nodes)
    elif (
        publication.get("status") != "no-checked-proof"
        or search.get("status") == "proof"
        or publication.get("script_sha256") is not None
        or report.get("kernel_verification") is not None
        or commands
        or nodes is not None
    ):
        raise AcceptanceError(f"{goal_id} has an incoherent failure report")
    retrieval = goal.get("retrieval_theorem")
    retrieval_hit = bool(
        proved and retrieval is not None and f"use {retrieval}" in commands
    )
    return (
        GoalOutcome(
            goal_id,
            str(goal["category"]),
            proved,
            retrieval_hit,
            kernel_checked,
            str(search.get("status")),
            len(commands),
            nodes if type(nodes) is int else None,
        ),
        identity,
    )


def _sealed_outcomes(
    goals: Sequence[Mapping[str, object]],
    report: Mapping[str, object],
    manifest: Mapping[str, object],
    adapter_identity: Mapping[str, str],
) -> tuple[tuple[GoalOutcome, ...], tuple[str, str, str, str]]:
    from scripts import eval_peano_policy as evaluator
    from training.peano_policy.contract import model_v2_environment

    environment = model_v2_environment()
    capabilities = environment.capabilities
    evaluator_goals = tuple(
        evaluator.EvalGoal(
            str(goal["sealed_name"]),
            str(goal["statement"]),
            classical=False,
            surface_profile="model-v2",
            allowed_theorems=capabilities.allowed_theorems,
        )
        for goal in goals
    )
    expected_goal_set_sha256 = evaluator._goal_set_sha256(evaluator_goals)

    if report.get("mode") != "kernel-guided-search" or report.get("judge") != (
        "checked_final(original_target, exact_mode)"
    ):
        raise AcceptanceError("sealed report is not a kernel-guided evaluation")
    evaluator_record = _mapping(report.get("evaluator"), "sealed evaluator")
    if (
        report.get("v") != evaluator.EVAL_VERSION
        or report.get("goal_set_sha256") != expected_goal_set_sha256
        or evaluator_record.get("source_sha256")
        != evaluator.EVALUATOR_SOURCE_SHA256
        or evaluator_record.get("semantic_sources")
        != evaluator.EVALUATOR_SEMANTIC_SOURCES
        or type(evaluator_record.get("runtime")) is not dict
    ):
        raise AcceptanceError("sealed evaluator source/goal identity changed")
    run = _mapping(
        _mapping(manifest.get("protocol"), "protocol").get("sealed_evaluator"),
        "protocol.sealed_evaluator",
    )
    if (
        type(report.get("seed")) is not int
        or report.get("seed") != run.get("seed")
        or type(report.get("k")) is not int
        or report.get("k") != 1
        or type(report.get("max_steps")) is not int
        or report.get("max_steps")
        != run["search_budget_per_goal"]["max_depth"]  # type: ignore[index]
    ):
        raise AcceptanceError("sealed report has the wrong seed or depth")
    search = _mapping(report.get("search"), "sealed search")
    limits = _mapping(run.get("search_budget_per_goal"), "sealed budget")
    expected_upper_bound = {
        "model_generate_calls": len(goals) * limits["max_model_calls"],
        "candidate_sequences": (
            len(goals)
            * limits["max_model_calls"]
            * limits["candidates_per_state"]
        ),
        "generated_sequence_tokens": (
            len(goals)
            * limits["max_model_calls"]
            * limits["candidates_per_state"]
            * _mapping(run.get("decoding"), "sealed decoding")["max_new_tokens"]
        ),
    }
    if (
        search.get("engine") != "training.peano_policy.search.search-v1"
        or search.get("budget_scope") != "per-goal"
        or search.get("limits") != limits
        or search.get("aggregate_upper_bound") != expected_upper_bound
    ):
        raise AcceptanceError("sealed report has the wrong search budget")
    policy_identity = _mapping(report.get("policy_identity"), "policy_identity")
    if (
        policy_identity.get("kind") != "peano-kernel-guided-search-v1"
        or policy_identity.get("limits") != run.get("search_budget_per_goal")
        or policy_identity.get("seed") != run.get("seed")
        or policy_identity.get("seed_schedule")
        != "sha256-json-v1(seed,goal_name,goal_statement)"
        or policy_identity.get("decoder_batching")
        != "one-model-generate-call-per-search-state"
    ):
        raise AcceptanceError("policy identity has the wrong search budget")
    sealed_base = _base_policy(policy_identity, "policy_identity")
    identity = _validate_base_policy(
        sealed_base,
        manifest,
        runner="sealed_evaluator",
        adapter_identity=adapter_identity,
    )
    provenance = _mapping(sealed_base.get("provenance"), "sealed provenance")
    evaluation = _mapping(provenance.get("evaluation"), "sealed evaluation provenance")
    expected_evaluation_sources = _expected_evaluation_sources(manifest)
    if evaluation.get("sources") != expected_evaluation_sources:
        raise AcceptanceError("sealed evaluation used unregistered semantic sources")
    from training.peano_policy.base_snapshot import expected_base_snapshot

    expected_snapshot = expected_base_snapshot()
    evaluation_integrity = _mapping(
        report.get("evaluation_integrity"), "sealed evaluation integrity"
    )
    if evaluation_integrity != {
        "base_snapshot": {
            "before_load": expected_snapshot,
            "after_evaluation": expected_snapshot,
        },
        "sources": expected_evaluation_sources,
    }:
        raise AcceptanceError(
            "sealed evaluation lacks before/after source and base-snapshot closure"
        )
    evaluation_job = evaluation.get("job")
    chain = _validate_training_submission_chain(
        manifest, _load_submission_ledger(manifest)
    )
    _validate_job_identity(
        evaluation_job,
        expected_row=chain["eval"],
        expected_script=WMI_EVAL_SCRIPT,
        expected_job_name="peano-wmi-qwen17-v2-eval",
        label="sealed evaluation job",
    )
    result_rows = _sequence(report.get("goals"), "sealed goals")
    search_rows = _sequence(search.get("goals"), "sealed search goals")
    if len(result_rows) != len(goals) or len(search_rows) != len(goals):
        raise AcceptanceError("sealed report must contain exactly four goals")
    if (
        report.get("policy") != policy_identity.get("name")
        or type(report.get("goal_count")) is not int
        or report.get("goal_count") != len(goals)
        or type(report.get("attempt_count")) is not int
        or report.get("attempt_count") != len(goals)
    ):
        raise AcceptanceError("sealed report summary is not one exact primary run")

    outcomes: list[GoalOutcome] = []
    total_model_calls = 0
    total_states_expanded = 0
    total_states_discovered = 0
    total_candidates_executed = 0
    total_sequences_requested = 0
    total_sequences_returned = 0
    total_candidate_lines = 0
    total_malformed_sequences = 0
    frontier_peak = 0
    status_counts = {status: 0 for status in evaluator.ATTEMPT_STATUSES}
    for goal, raw, raw_search in zip(goals, result_rows, search_rows, strict=True):
        goal_id = str(goal["id"])
        sealed_name = goal.get("sealed_name")
        statement = str(goal["statement"])
        row = _mapping(raw, f"{goal_id} result")
        search_row = _mapping(raw_search, f"{goal_id} search result")
        if (
            row.get("name") != sealed_name
            or row.get("statement") != statement
            or search_row.get("name") != sealed_name
            or row.get("classical") is not False
            or row.get("surface_profile") != "model-v2"
            or row.get("allowed_theorems") != list(capabilities.allowed_theorems or ())
            or row.get("environment_sha256")
            != environment.sha256
            or search_row.get("environment_sha256") != environment.sha256
        ):
            raise AcceptanceError(f"{goal_id} does not match its frozen held-out name")
        attempts = _sequence(row.get("attempts"), f"{goal_id}.attempts")
        if len(attempts) != 1:
            raise AcceptanceError(f"{goal_id} must have one primary attempt")
        attempt = _mapping(attempts[0], f"{goal_id}.attempt")
        result = _mapping(search_row.get("result"), f"{goal_id}.search.result")
        commands = _sequence(attempt.get("commands"), f"{goal_id}.commands")
        seed_payload = json.dumps(
            [1, run["seed"], sealed_name, statement],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        expected_seed = int.from_bytes(
            hashlib.sha256(seed_payload).digest()[:8], "big"
        ) & (2**63 - 1)
        if (
            attempt.get("sample") != 0
            or attempt.get("seed") != expected_seed
            or attempt.get("steps") != len(commands)
        ):
            raise AcceptanceError(f"{goal_id} attempt schedule changed")
        if commands != result.get("commands"):
            raise AcceptanceError(f"{goal_id} command records disagree")
        result_status = result.get("status")
        expected_attempt_status = {
            "proof": "proof",
            "limit": "limit",
            "exhausted": "failing",
        }.get(result_status)
        if expected_attempt_status is None or attempt.get("status") != expected_attempt_status:
            raise AcceptanceError(f"{goal_id} search and attempt statuses disagree")
        status_counts[expected_attempt_status] += 1
        expected_goal_counts = {
            status: int(status == expected_attempt_status)
            for status in evaluator.ATTEMPT_STATUSES
        }
        row_status_counts = _mapping(
            row.get("status_counts"), f"{goal_id}.status_counts"
        )
        if row_status_counts != expected_goal_counts or any(
            type(row_status_counts.get(status)) is not int
            for status in evaluator.ATTEMPT_STATUSES
        ):
            raise AcceptanceError(f"{goal_id} status-count summary is inconsistent")
        proved = expected_attempt_status == "proof"
        if (
            row.get("passed") is not proved
            or (attempt.get("error") is None) is not proved
        ):
            raise AcceptanceError(f"{goal_id} status records disagree")
        nodes = attempt.get("proof_nodes")
        if nodes != result.get("certificate_nodes"):
            raise AcceptanceError(f"{goal_id} proof-node records disagree")
        decoder = _mapping(search_row.get("decoder"), f"{goal_id}.decoder")
        decoder_counts: dict[str, int] = {}
        for field in (
            "model_generate_calls",
            "candidate_sequences_requested",
            "candidate_sequences_returned",
            "candidate_lines_returned",
            "malformed_sequences_rejected",
        ):
            value = decoder.get(field)
            if type(value) is not int or value < 0:
                raise AcceptanceError(f"{goal_id} has invalid decoder accounting")
            decoder_counts[field] = value
        _validate_search_accounting(
            goal_id,
            result,
            limits,
            candidate_lines=decoder_counts["candidate_lines_returned"],
        )
        if (
            result.get("theorem") != statement
            or decoder.get("one_batched_call_per_search_state") is not True
            or decoder_counts["model_generate_calls"] != result["model_calls"]
            or decoder_counts["candidate_sequences_requested"]
            != result["model_calls"] * limits["candidates_per_state"]
            or decoder_counts["candidate_sequences_returned"]
            > decoder_counts["candidate_sequences_requested"]
            or decoder_counts["candidate_lines_returned"]
            + decoder_counts["malformed_sequences_rejected"]
            != decoder_counts["candidate_sequences_returned"]
        ):
            raise AcceptanceError(f"{goal_id} search accounting exceeds its budget")
        if proved and (type(nodes) is not int or nodes < 1):
            raise AcceptanceError(f"{goal_id} has invalid proof-node accounting")
        if not proved and (commands or nodes is not None):
            raise AcceptanceError(f"{goal_id} failure claims proof data")
        total_model_calls += int(result["model_calls"])
        total_states_expanded += int(result["states_expanded"])
        total_states_discovered += int(result["states_discovered"])
        total_candidates_executed += int(result["candidates_executed"])
        total_sequences_requested += decoder_counts["candidate_sequences_requested"]
        total_sequences_returned += decoder_counts["candidate_sequences_returned"]
        total_candidate_lines += decoder_counts["candidate_lines_returned"]
        total_malformed_sequences += decoder_counts["malformed_sequences_rejected"]
        frontier_peak = max(frontier_peak, int(result["frontier_peak"]))
        kernel_checked = (
            _kernel_replay(goal_id, statement, commands, nodes) if proved else False
        )
        outcomes.append(
            GoalOutcome(
                goal_id,
                "sealed",
                proved,
                False,
                kernel_checked,
                str(result.get("status")),
                len(commands),
                nodes if type(nodes) is int else None,
            )
        )
    expected_actual = {
        "model_generate_calls": total_model_calls,
        "states_expanded": total_states_expanded,
        "states_discovered": total_states_discovered,
        "candidates_executed": total_candidates_executed,
        "candidate_sequences_requested": total_sequences_requested,
        "candidate_sequences_returned": total_sequences_returned,
        "candidate_lines_returned": total_candidate_lines,
        "malformed_sequences_rejected": total_malformed_sequences,
        "frontier_peak_per_goal": frontier_peak,
    }
    proved_goals = sum(outcome.proved for outcome in outcomes)
    report_status_counts = _mapping(report.get("status_counts"), "sealed status_counts")
    if (
        search.get("actual") != expected_actual
        or type(report.get("proved_goals")) is not int
        or report.get("proved_goals") != proved_goals
        or type(report.get("pass@k")) is not float
        or report.get("pass@k") != proved_goals / len(goals)
        or report_status_counts != status_counts
        or any(
            type(report_status_counts.get(status)) is not int
            for status in evaluator.ATTEMPT_STATUSES
        )
    ):
        raise AcceptanceError("sealed report aggregate accounting is inconsistent")
    return tuple(outcomes), identity


def _validate_acceptance_submission_chain(
    manifest: Mapping[str, object],
    rows: Sequence[Mapping[str, str]],
    *,
    require_scorer: bool,
) -> dict[str, dict[str, str]]:
    training = _validate_training_submission_chain(manifest, rows)
    primary_index, primary = _unique_script_row(rows, WMI_PRIMARY_SCRIPT)
    _validate_submission_script(primary, WMI_PRIMARY_SCRIPT)
    eval_index = next(
        index
        for index, row in enumerate(rows)
        if row.get("job_id") == training["eval"]["job_id"]
    )
    if (
        primary_index <= eval_index
        or primary.get("dependency_job_id") != ""
        or primary.get("git_commit") != training["prepare"].get("git_commit")
        or primary.get("sync_timestamp")
        != training["prepare"].get("sync_timestamp")
        or primary.get("workdir") != WMI_PROJECT_ROOT
    ):
        raise AcceptanceError(
            "acceptance primary is not a later standalone job from the shared "
            "sealed deployment"
        )
    scorer_matches = [
        (index, dict(row))
        for index, row in enumerate(rows)
        if row.get("script") == WMI_SCORER_SCRIPT
    ]
    if not scorer_matches:
        if require_scorer:
            raise AcceptanceError(
                "WMI ledger must contain the earliest and only scorer job"
            )
        return {**training, "primary": primary}
    if len(scorer_matches) != 1:
        raise AcceptanceError("WMI ledger must contain the earliest and only scorer job")
    scorer_index, scorer = scorer_matches[0]
    _validate_submission_script(scorer, WMI_SCORER_SCRIPT)
    if (
        scorer_index <= primary_index
        or scorer.get("dependency_job_id") != primary.get("job_id")
        or scorer.get("git_commit") != primary.get("git_commit")
        or scorer.get("sync_timestamp") != primary.get("sync_timestamp")
        or scorer.get("workdir") != WMI_PROJECT_ROOT
    ):
        raise AcceptanceError("acceptance scorer is not the primary job's exact successor")
    return {**training, "primary": primary, "scorer": scorer}


def _current_wmi_job(
    manifest: Mapping[str, object],
    *,
    role: str,
) -> tuple[dict[str, object], dict[str, dict[str, str]]]:
    from training.peano_policy.runtime import slurm_job_identity

    if role not in {"primary", "scorer"}:
        raise ValueError("unknown acceptance WMI role")
    rows = _load_submission_ledger(manifest)
    chain = _validate_acceptance_submission_chain(
        manifest, rows, require_scorer=role == "scorer"
    )
    expected_script = WMI_PRIMARY_SCRIPT if role == "primary" else WMI_SCORER_SCRIPT
    expected_name = (
        "peano-wmi-v2-accept-primary"
        if role == "primary"
        else "peano-wmi-v2-accept-score"
    )
    job = _validate_job_identity(
        slurm_job_identity(),
        expected_row=chain[role],
        expected_script=expected_script,
        expected_job_name=expected_name,
        label=f"acceptance {role} job",
    )
    completed_roles = ("prepare", "train", "eval") + (
        ("primary",) if role == "scorer" else ()
    )
    _require_completed_jobs(chain, completed_roles)
    _require_dataset_generator_terminal(chain)
    return job, chain


def _require_job_state(
    row: Mapping[str, str], role: str, accepted: frozenset[str]
) -> None:
    job_id = row.get("job_id")
    if type(job_id) is not str or _JOB_ID_RE.fullmatch(job_id) is None:
        raise AcceptanceError(f"WMI {role} predecessor has a bad job id")
    try:
        completed = subprocess.run(
            ["sacct", "-n", "-X", "-j", job_id, "--format=State", "-P"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise AcceptanceError(f"cannot verify WMI {role} job state: {exc}") from None
    states = [
        line.strip().split("+", 1)[0]
        for line in completed.stdout.splitlines()
        if line.strip()
    ]
    if not states or states[0] not in accepted:
        raise AcceptanceError(
            f"WMI {role} job state is not one of {sorted(accepted)}"
        )


def _require_completed_jobs(
    chain: Mapping[str, Mapping[str, str]],
    roles: Sequence[str],
) -> None:
    """Ask Slurm accounting for the terminal state of every predecessor."""

    for role in roles:
        row = chain.get(role)
        if row is None:
            raise AcceptanceError(f"missing WMI {role} predecessor")
        _require_job_state(row, role, frozenset({"COMPLETED"}))


def _require_dataset_generator_terminal(
    chain: Mapping[str, Mapping[str, str]],
) -> dict[str, object]:
    row = chain.get("generator")
    if row is None:
        raise AcceptanceError("missing WMI dataset-generator precursor")
    job_id = row.get("job_id")
    if job_id != WMI_DATASET_GENERATOR_EVIDENCE["job_id"]:
        raise AcceptanceError("WMI dataset-generator job id changed")
    try:
        accounting = subprocess.run(
            [
                "sacct",
                "-n",
                "-X",
                "-j",
                str(job_id),
                "--format=State,ExitCode,Elapsed,Start,End",
                "-P",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise AcceptanceError(
            f"cannot verify WMI dataset generator evidence: {exc}"
        ) from None
    lines = [line.strip() for line in accounting.stdout.splitlines() if line.strip()]
    fields = lines[0].split("|") if len(lines) == 1 else []
    observed = (
        dict(zip(("state", "exit_code", "elapsed", "start", "end"), fields))
        if len(fields) == 5
        else {}
    )
    expected_accounting = {
        key: WMI_DATASET_GENERATOR_EVIDENCE[key]
        for key in ("state", "exit_code", "elapsed", "start", "end")
    }
    if observed != expected_accounting:
        raise AcceptanceError("WMI dataset-generator accounting evidence changed")
    logs: dict[str, object] = {}
    for stream in ("stdout", "stderr"):
        expected = _mapping(
            WMI_DATASET_GENERATOR_EVIDENCE[stream],
            f"dataset generator {stream}",
        )
        path = _plain_file(
            _repository_path(
                _text(expected.get("path"), f"dataset generator {stream} path"),
                f"dataset generator {stream}",
            ),
            f"dataset generator {stream}",
        )
        digest = _sha256_file(path)
        if digest != expected.get("sha256"):
            raise AcceptanceError(f"WMI dataset-generator {stream} log changed")
        logs[stream] = {"path": expected["path"], "sha256": digest}
    return {
        "submission_job_id": job_id,
        "accounting": observed,
        "logs": logs,
    }


def _inventory_hash(path: Path, label: str) -> dict[str, object]:
    if not path.exists():
        return {"sha256": _sha256_json({}), "files": {}, "count": 0}
    directory = _plain_directory(path, label)
    files: dict[str, str] = {}
    total_bytes = 0
    try:
        entries = sorted(directory.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise AcceptanceError(f"cannot enumerate {label}: {exc}") from None
    if len(entries) > 100_000:
        raise AcceptanceError(f"{label} contains too many artifacts")
    for entry in entries:
        if entry.is_symlink() or not entry.is_file():
            raise AcceptanceError(f"{label} contains a non-regular artifact")
        try:
            size = entry.stat().st_size
        except OSError as exc:
            raise AcceptanceError(f"cannot stat {label} artifact: {exc}") from None
        if size > 64_000_000:
            raise AcceptanceError(f"{label} contains an oversized artifact")
        total_bytes += size
        if total_bytes > 4_000_000_000:
            raise AcceptanceError(f"{label} inventory is unexpectedly large")
        files[entry.name] = _sha256_file(entry)
    return {"sha256": _sha256_json(files), "files": files, "count": len(files)}


def _load_proof_request_ledger(
    manifest: Mapping[str, object],
) -> tuple[tuple[dict[str, str], ...], str | None]:
    execution = _mapping(
        _mapping(manifest.get("protocol"), "protocol").get("wmi_execution"),
        "wmi_execution",
    )
    path = _repository_path(
        _text(execution.get("proof_request_ledger"), "proof request ledger"),
        "proof request ledger",
    )
    if not path.exists():
        return (), None
    ledger_path = _plain_file(path, "WMI proof-request ledger")
    if ledger_path.stat().st_size > 16_000_000:
        raise AcceptanceError("WMI proof-request ledger is unexpectedly large")
    fields = ("timestamp", "job_id", "request_id", "request_sha256")
    try:
        with ledger_path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != fields:
                raise AcceptanceError("WMI proof-request ledger header changed")
            rows = tuple(dict(row) for row in reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AcceptanceError(f"cannot parse WMI proof-request ledger: {exc}") from None
    seen_jobs: set[str] = set()
    seen_requests: set[str] = set()
    for row in rows:
        if (
            set(row) != set(fields)
            or _JOB_ID_RE.fullmatch(row.get("job_id", "")) is None
            or _SHA256_RE.fullmatch(row.get("request_id", "")) is None
            or _SHA256_RE.fullmatch(row.get("request_sha256", "")) is None
            or row["job_id"] in seen_jobs
            or row["request_id"] in seen_requests
        ):
            raise AcceptanceError("WMI proof-request ledger is malformed or duplicated")
        seen_jobs.add(row["job_id"])
        seen_requests.add(row["request_id"])
    return rows, _sha256_file(ledger_path)


def _validate_proof_result_artifacts(
    proof_rows: Sequence[Mapping[str, str]],
    requests: Mapping[str, Mapping[str, object]],
    inventory: Mapping[str, object],
    forbidden: Mapping[object, str],
) -> None:
    """Bind every proof-result artifact to one immutable ledgered request."""

    root = REPOSITORY_ROOT / "results" / "peano-policy" / "user-proofs"
    files = _mapping(inventory.get("files"), "proof result files")
    by_request: dict[str, dict[str, str]] = {}
    collisions: list[str] = []

    def scan_commands(value: object, *, label: str) -> None:
        stack = [value]
        visited = 0
        while stack:
            current = stack.pop()
            visited += 1
            if visited > 100_000:
                raise AcceptanceError(f"{label} has too many JSON nodes")
            if type(current) is dict:
                for key, child in current.items():
                    if key == "commands":
                        commands = _sequence(child, f"{label}.commands")
                        if not all(type(command) is str and command for command in commands):
                            raise AcceptanceError(f"{label} has malformed proof commands")
                        collisions.extend(
                            _scan_tactic_propositions(
                                commands,
                                forbidden,
                                label=f"{label}.commands",
                            )
                        )
                    elif key == "command":
                        if child is None:
                            continue
                        if type(child) is not str or not child:
                            raise AcceptanceError(
                                f"{label} has a malformed proof command"
                            )
                        collisions.extend(
                            _scan_tactic_propositions(
                                (child,),
                                forbidden,
                                label=f"{label}.command",
                            )
                        )
                    else:
                        stack.append(child)
            elif type(current) is list:
                stack.extend(current)
    pattern = re.compile(r"([0-9a-f]{64})(\.run\.json|\.json|\.pa)")
    for name, digest in files.items():
        match = pattern.fullmatch(name)
        if (
            type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
            or match is None
            or match.group(1) not in requests
        ):
            raise AcceptanceError("proof result inventory contains an orphan artifact")
        by_request.setdefault(match.group(1), {})[match.group(2)] = digest

    rows_by_request = {row["request_id"]: dict(row) for row in proof_rows}
    for request_id, artifacts in by_request.items():
        request = requests[request_id]
        row = rows_by_request[request_id]
        report_digest = artifacts.get(".json")
        summary_digest = artifacts.get(".run.json")
        proof_digest = artifacts.get(".pa")
        if summary_digest is not None and report_digest is None:
            raise AcceptanceError("proof run summary has no evaluation report")
        if proof_digest is not None and report_digest is None:
            raise AcceptanceError("proof artifact has no evaluation report")

        if report_digest is not None:
            report = _read_json(root / f"{request_id}.json")
            goals = _sequence(report.get("goals"), "proof-result goals")
            if len(goals) != 1:
                raise AcceptanceError("proof-result report is not one theorem attempt")
            goal = _mapping(goals[0], "proof-result goal")
            if goal.get("statement") != request.get("theorem"):
                raise AcceptanceError("proof-result theorem differs from its request")
            scan_commands(report, label=f"proof-result:{request_id}")

        proof_lines: list[str] | None = None
        if proof_digest is not None:
            proof_path = root / f"{request_id}.pa"
            try:
                proof_lines = proof_path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError) as exc:
                raise AcceptanceError(f"cannot read proof artifact: {exc}") from None
            if (
                len(proof_lines) < 2
                or proof_lines[0] != f"pa prove {request.get('theorem')}"
                or proof_lines[-1] != "qed"
                or any(not line for line in proof_lines[1:-1])
            ):
                raise AcceptanceError(
                    "proof artifact differs from its ledgered theorem"
                )
            collisions.extend(
                _scan_tactic_propositions(
                    tuple(proof_lines[1:-1]),
                    forbidden,
                    label=f"proof-script:{request_id}",
                )
            )

        if summary_digest is None:
            continue
        summary = _read_json(root / f"{request_id}.run.json")
        request_record = _mapping(summary.get("request"), "proof summary request")
        ledger_record = _mapping(
            summary.get("request_ledger"), "proof summary ledger"
        )
        evaluation = _mapping(
            summary.get("evaluation_report"), "proof summary evaluation"
        )
        proof = summary.get("proof")
        expected_request_path = (
            f"results/peano-policy/requests/{request_id}.json"
        )
        expected_report_path = (
            f"results/peano-policy/user-proofs/{request_id}.json"
        )
        if (
            set(summary)
            != {
                "format",
                "v",
                "status",
                "request",
                "request_ledger",
                "evaluation_report",
                "proof",
            }
            or summary.get("format") != "peano-policy-wmi-proof-run"
            or summary.get("v") != 1
            or summary.get("status") not in {"proved", "no-proof"}
            or request_record
            != {
                "id": request_id,
                "path": expected_request_path,
                "sha256": row["request_sha256"],
            }
            or ledger_record.get("path") != WMI_PROOF_REQUEST_LEDGER
            or ledger_record.get("row") != row
            or ledger_record.get("row_sha256") != _sha256_json_line(row)
            or evaluation
            != {"path": expected_report_path, "sha256": report_digest}
        ):
            raise AcceptanceError("proof run summary is not joined to its request")
        if summary.get("status") == "proved":
            if (
                type(proof) is not dict
                or proof
                != {
                    "path": f"results/peano-policy/user-proofs/{request_id}.pa",
                    "sha256": proof_digest,
                }
                or proof_digest is None
            ):
                raise AcceptanceError("proved request has a forged proof artifact")
        elif proof is not None or proof_digest is not None:
            raise AcceptanceError("unproved request unexpectedly has a proof artifact")
    if collisions:
        raise AcceptanceError(
            "acceptance goal appeared in a WMI proof result tactic: "
            + ", ".join(sorted(set(collisions)))
        )


def audit_proof_history(
    manifest: Mapping[str, object],
    adapter: AdapterAuthority,
) -> dict[str, object]:
    """Reject any WMI proof preview of an acceptance theorem."""

    _validated_primary_semantic_source(manifest)
    from peano_lab.kernel.formulas import parse_formula_with_names
    from scripts import peano_policy_proof_request as request_tool

    submissions = _load_submission_ledger(manifest)
    proof_rows, proof_ledger_sha256 = _load_proof_request_ledger(manifest)
    by_job = {row["job_id"]: row for row in submissions}
    prove_submissions = {
        row["job_id"]
        for row in submissions
        if row.get("script") == "slurm/peano_wmi_prove_theorem.sbatch"
    }
    proof_jobs = {row["job_id"] for row in proof_rows}
    if prove_submissions != proof_jobs:
        raise AcceptanceError(
            "WMI theorem-proof submissions and request ledger are not bijective"
        )
    request_inventory = _inventory_hash(
        REPOSITORY_ROOT / "results" / "peano-policy" / "requests",
        "proof request inventory",
    )
    expected_request_files = {
        f"{row['request_id']}.json": row["request_sha256"] for row in proof_rows
    }
    if _mapping(request_inventory.get("files"), "proof request files") != (
        expected_request_files
    ):
        raise AcceptanceError(
            "proof request ledger and artifact inventory are not bijective"
        )
    forbidden: dict[object, str] = {}
    for goal in _goal_records(manifest):
        formula, names = parse_formula_with_names(str(goal["statement"]))
        if names:
            raise AcceptanceError("acceptance proof-history target is not closed")
        forbidden[formula] = str(goal["id"])
    collisions: list[str] = []
    requests: dict[str, dict[str, object]] = {}
    for row in proof_rows:
        submission = by_job.get(row["job_id"])
        if submission is None or submission.get("script") != (
            "slurm/peano_wmi_prove_theorem.sbatch"
        ):
            raise AcceptanceError("proof-request row is not joined to its WMI job")
        try:
            request, request_path, request_sha256 = request_tool.load_request(
                row["request_id"]
            )
        except (OSError, TypeError, ValueError) as exc:
            raise AcceptanceError(f"proof request {row['request_id']} is invalid: {exc}") from None
        expected_path = (
            REPOSITORY_ROOT
            / "results"
            / "peano-policy"
            / "requests"
            / f"{row['request_id']}.json"
        )
        if request_path != expected_path or request_sha256 != row["request_sha256"]:
            raise AcceptanceError("proof-request artifact differs from its ledger")
        requests[row["request_id"]] = request
        formula, names = parse_formula_with_names(str(request.get("theorem")))
        if names:
            raise AcceptanceError("ledgered proof request is unexpectedly open")
        collisions.extend(
            _formula_subtree_collisions(
                formula,
                forbidden,
                label=f"proof-request:{row['request_id']}",
            )
        )
    if collisions:
        raise AcceptanceError(
            "acceptance goal was previewed through WMI proof requests: "
            + ", ".join(collisions)
        )
    result_inventory = _inventory_hash(
        REPOSITORY_ROOT / "results" / "peano-policy" / "user-proofs",
        "proof result inventory",
    )
    _validate_proof_result_artifacts(
        proof_rows, requests, result_inventory, forbidden
    )
    return {
        "format": "peano-policy-acceptance-proof-history",
        "v": 1,
        "submission_history_sha256": _sha256_json(
            [row for row in submissions if row.get("script") != WMI_SCORER_SCRIPT]
        ),
        "proof_ledger_sha256": proof_ledger_sha256,
        "request_inventory_sha256": request_inventory["sha256"],
        "result_inventory_sha256": result_inventory["sha256"],
        "proof_request_rows": len(proof_rows),
        "audited_requests": len(proof_rows),
        "request_artifacts": request_inventory["count"],
        "result_artifacts": result_inventory["count"],
        "training_manifest_sha256": adapter.identity["training_manifest_sha256"],
        "adapter_sha256": adapter.identity["adapter_sha256"],
        "forbidden_goal_ids": [str(goal["id"]) for goal in _goal_records(manifest)],
        "collisions": [],
    }


def preflight_primary_submission(
    manifest: Mapping[str, object],
    adapter: AdapterAuthority,
    heldout_report_path: Path,
) -> dict[str, object]:
    """Validate the completed sealed chain before the one primary submission."""

    expected_report = _repository_path(WMI_HELDOUT_REPORT, "held-out report").resolve(
        strict=False
    )
    report_path = _plain_file(heldout_report_path, "held-out report")
    if report_path != expected_report:
        raise AcceptanceError("held-out report is not the fixed WMI evaluation artifact")
    rows = _load_submission_ledger(manifest)
    if any(row.get("script") in WMI_ACCEPTANCE_SCRIPTS for row in rows):
        raise AcceptanceError("an acceptance primary/scorer submission already exists")
    chain = _validate_training_submission_chain(manifest, rows)
    from training.peano_policy.runtime import source_sync_identity

    if source_sync_identity(required=True) != _expected_source_sync(
        chain["prepare"]
    ):
        raise AcceptanceError(
            "current WMI source sync differs from the sealed training deployment"
        )
    _require_completed_jobs(chain, ("prepare", "train", "eval"))
    _require_dataset_generator_terminal(chain)
    pretraining_report_sha256 = _validate_pretraining_report_identity(
        manifest, adapter
    )
    history = audit_proof_history(manifest, adapter)
    base_snapshot = _base_snapshot_authority(manifest)
    report = _read_json(report_path)
    outcomes, _identity = _sealed_outcomes(
        _goal_records(manifest)[12:], report, manifest, adapter.identity
    )
    return {
        "status": "ready-for-one-primary-submission",
        "training_job_id": chain["train"]["job_id"],
        "sealed_evaluation_job_id": chain["eval"]["job_id"],
        "heldout_report_sha256": _sha256_file(report_path),
        "sealed_checked_proofs": sum(outcome.kernel_checked for outcome in outcomes),
        "pretraining_report_sha256": pretraining_report_sha256,
        "proof_history_sha256": _sha256_json(history),
        "base_snapshot_sha256": base_snapshot["snapshot_sha256"],
    }


def _primary_session_id(
    manifest_sha256: str,
    adapter_identity: Mapping[str, str],
    data_audit: Mapping[str, object],
    proof_history: Mapping[str, object],
    semantic_source: Mapping[str, object],
    base_snapshot: Mapping[str, object],
    wmi_job: Mapping[str, object],
) -> str:
    return _sha256_json(
        {
            "preregistration_sha256": manifest_sha256,
            "adapter": dict(adapter_identity),
            "data_audit_sha256": _sha256_json(data_audit),
            "proof_history_sha256": _sha256_json(proof_history),
            "primary_semantic_source_sha256": _sha256_json(semantic_source),
            "base_snapshot_sha256": _sha256_json(base_snapshot),
            "wmi_job_sha256": _sha256_json(wmi_job),
        }
    )


def run_primary_session(
    manifest: Mapping[str, object],
    *,
    manifest_sha256: str,
    adapter: AdapterAuthority,
    data_audit: Mapping[str, object],
) -> Path:
    """Load once and execute R1--I4 once in one non-resumable directory."""

    semantic_source = _validated_primary_semantic_source(manifest)
    base_snapshot_before = _validated_base_snapshot(manifest)
    base_snapshot_checks = {
        "before_load": base_snapshot_before,
        "after_search": base_snapshot_before,
    }
    from scripts import peano_policy_repl as repl

    run = _mapping(
        _mapping(manifest.get("protocol"), "protocol").get("interactive"),
        "protocol.interactive",
    )
    decoding = _mapping(run.get("decoding"), "interactive decoding")
    budget_record = _mapping(
        run.get("search_budget_per_goal"), "interactive search budget"
    )
    session_directory = adapter.directory / PRIMARY_SESSION_DIRECTORY
    if os.path.lexists(session_directory):
        raise AcceptanceError(
            "the fixed primary-session directory already exists; this run cannot "
            "resume or replace an earlier attempt"
        )
    try:
        repl._validated_results_dir(session_directory)
    except (OSError, TypeError, ValueError) as exc:
        raise AcceptanceError(
            f"primary adapter must live below the repository results directory: {exc}"
        ) from None
    try:
        session_directory.mkdir()
    except OSError as exc:
        raise AcceptanceError(f"cannot create primary-session directory: {exc}") from None

    wmi_job, _chain = _current_wmi_job(manifest, role="primary")
    proof_history = audit_proof_history(manifest, adapter)
    session_id = _primary_session_id(
        manifest_sha256,
        adapter.identity,
        data_audit,
        proof_history,
        semantic_source,
        base_snapshot_checks,
        wmi_job,
    )
    started_at = _now_utc()
    open_record = {
        "format": PRIMARY_SESSION_FORMAT,
        "v": PRIMARY_SESSION_VERSION,
        "status": "open-non-resumable",
        "session_id": session_id,
        "started_at": started_at,
        "preregistration_sha256": manifest_sha256,
        "adapter": dict(adapter.identity),
        "data_audit_sha256": _sha256_json(data_audit),
        "proof_history": dict(proof_history),
        "primary_semantic_source": dict(semantic_source),
        "base_snapshot": base_snapshot_checks,
        "wmi_job": dict(wmi_job),
        "goal_ids": list(run["goal_ids"]),
    }
    open_path = session_directory / PRIMARY_SESSION_OPEN
    repl._atomic_create_text(open_path, _render(open_record, compact=False) + "\n")

    runtime = repl.load_model_runtime(
        adapter.directory,
        seed=int(run["seed"]),
        max_new_tokens=int(decoding["max_new_tokens"]),
        sample=bool(decoding["do_sample"]),
        temperature=float(decoding["temperature"]),
        top_p=float(decoding["top_p"]),
    )
    runtime_adapter = _mapping(
        dict(runtime.adapter_identity).get("policy"), "runtime adapter policy"
    )
    _validate_base_policy(
        _base_policy(runtime_adapter, "runtime adapter policy"),
        manifest,
        runner="interactive",
        adapter_identity=adapter.identity,
    )
    if runtime_adapter.get("seed") != run.get("seed"):
        raise AcceptanceError("loaded primary policy has the wrong seed")
    budget = repl.SearchBudget(**budget_record)

    goals = _goal_records(manifest)[:12]
    entries: list[dict[str, object]] = []
    for ordinal, goal in enumerate(goals, 1):
        goal_id = str(goal["id"])
        attempt = repl.run_checked_search(
            str(goal["statement"]),
            runtime,
            budget,
            created_at=_now_utc(),
        )
        stem = f"{ordinal:02d}-{goal_id}"
        saved = repl.save_attempt(attempt, session_directory, stem=stem)
        entry: dict[str, object] = {
            "ordinal": ordinal,
            "goal_id": goal_id,
            "statement": goal["statement"],
            "report_path": saved.report.name,
            "report_sha256": _sha256_file(saved.report),
            "proof_path": None,
            "proof_sha256": None,
        }
        if saved.proof is not None:
            entry["proof_path"] = saved.proof.name
            entry["proof_sha256"] = _sha256_file(saved.proof)
        entries.append(entry)

    final_wmi_job, _final_chain = _current_wmi_job(manifest, role="primary")
    final_proof_history = audit_proof_history(manifest, adapter)
    final_semantic_source = _validated_primary_semantic_source(manifest)
    base_snapshot_after = _validated_base_snapshot(manifest)
    if (
        final_wmi_job != wmi_job
        or final_proof_history != proof_history
        or final_semantic_source != semantic_source
        or base_snapshot_after != base_snapshot_before
    ):
        raise AcceptanceError(
            "WMI job, proof-request history, or semantic source changed during "
            "the primary session"
        )
    completed_at = _now_utc()
    ledger = {
        "format": PRIMARY_SESSION_FORMAT,
        "v": PRIMARY_SESSION_VERSION,
        "status": "complete",
        "session_id": session_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "preregistration_sha256": manifest_sha256,
        "open_marker": {
            "path": open_path.name,
            "sha256": _sha256_file(open_path),
        },
        "adapter": dict(adapter.identity),
        "data_audit": dict(data_audit),
        "proof_history": dict(proof_history),
        "primary_semantic_source": dict(semantic_source),
        "base_snapshot": base_snapshot_checks,
        "wmi_job": dict(wmi_job),
        "protocol": {
            "goal_ids": list(run["goal_ids"]),
            "seed": run["seed"],
            "decoding": dict(decoding),
            "search_budget_per_goal": dict(budget_record),
            "one_loaded_adapter": True,
            "attempts_per_goal": 1,
            "resumable": False,
        },
        "goals": entries,
    }
    ledger_path = session_directory / PRIMARY_SESSION_LEDGER
    repl._atomic_create_text(ledger_path, _render(ledger, compact=False) + "\n")
    return ledger_path


def _relative_session_file(
    directory: Path, value: object, expected_name: str, label: str
) -> Path:
    name = _text(value, label)
    if name != expected_name or Path(name).name != name:
        raise AcceptanceError(f"{label} is not the fixed session artifact name")
    return _plain_file(directory / name, label)


def load_primary_session(
    manifest: Mapping[str, object],
    *,
    manifest_sha256: str,
    adapter: AdapterAuthority,
    data_audit: Mapping[str, object],
) -> PrimarySession:
    """Validate the only fixed primary ledger and every path/hash it commits."""

    semantic_source = _validated_primary_semantic_source(manifest)
    from training.peano_policy.base_snapshot import expected_base_snapshot

    expected_snapshot = expected_base_snapshot()
    directory = _plain_directory(
        adapter.directory / PRIMARY_SESSION_DIRECTORY,
        "primary-session directory",
    )
    ledger_path = _plain_file(directory / PRIMARY_SESSION_LEDGER, "primary ledger")
    ledger = _read_json(ledger_path)
    proof_history = audit_proof_history(manifest, adapter)
    chain = _validate_acceptance_submission_chain(
        manifest, _load_submission_ledger(manifest), require_scorer=True
    )
    wmi_job = _mapping(ledger.get("wmi_job"), "primary ledger WMI job")
    base_snapshot = _mapping(
        ledger.get("base_snapshot"), "primary ledger base snapshot"
    )
    _validate_job_identity(
        wmi_job,
        expected_row=chain["primary"],
        expected_script=WMI_PRIMARY_SCRIPT,
        expected_job_name="peano-wmi-v2-accept-primary",
        label="primary ledger WMI job",
    )
    expected_session_id = _primary_session_id(
        manifest_sha256,
        adapter.identity,
        data_audit,
        proof_history,
        semantic_source,
        base_snapshot,
        wmi_job,
    )
    if (
        ledger.get("format") != PRIMARY_SESSION_FORMAT
        or ledger.get("v") != PRIMARY_SESSION_VERSION
        or ledger.get("status") != "complete"
        or ledger.get("session_id") != expected_session_id
        or ledger.get("preregistration_sha256") != manifest_sha256
        or ledger.get("adapter") != adapter.identity
        or ledger.get("data_audit") != dict(data_audit)
        or ledger.get("proof_history") != proof_history
        or ledger.get("primary_semantic_source") != semantic_source
        or base_snapshot
        != {
            "before_load": expected_snapshot,
            "after_search": expected_snapshot,
        }
    ):
        raise AcceptanceError("primary ledger has the wrong experiment identity")
    started = _utc_timestamp(ledger.get("started_at"), "primary started_at")
    completed = _utc_timestamp(ledger.get("completed_at"), "primary completed_at")
    if completed < started:
        raise AcceptanceError("primary-session timestamps run backwards")

    open_record = _mapping(ledger.get("open_marker"), "primary open_marker")
    open_path = _relative_session_file(
        directory,
        open_record.get("path"),
        PRIMARY_SESSION_OPEN,
        "primary open marker",
    )
    if open_record.get("sha256") != _sha256_file(open_path):
        raise AcceptanceError("primary open marker hash mismatch")
    opened = _read_json(open_path)
    if opened != {
        "format": PRIMARY_SESSION_FORMAT,
        "v": PRIMARY_SESSION_VERSION,
        "status": "open-non-resumable",
        "session_id": expected_session_id,
        "started_at": ledger.get("started_at"),
        "preregistration_sha256": manifest_sha256,
        "adapter": adapter.identity,
        "data_audit_sha256": _sha256_json(data_audit),
        "proof_history": proof_history,
        "primary_semantic_source": semantic_source,
        "base_snapshot": {
            "before_load": expected_snapshot,
            "after_search": expected_snapshot,
        },
        "wmi_job": wmi_job,
        "goal_ids": _mapping(
            _mapping(manifest.get("protocol"), "protocol").get("interactive"),
            "protocol.interactive",
        ).get("goal_ids"),
    }:
        raise AcceptanceError("primary open marker does not bind the final ledger")

    run = _mapping(
        _mapping(manifest.get("protocol"), "protocol").get("interactive"),
        "protocol.interactive",
    )
    if ledger.get("protocol") != {
        "goal_ids": run.get("goal_ids"),
        "seed": run.get("seed"),
        "decoding": run.get("decoding"),
        "search_budget_per_goal": run.get("search_budget_per_goal"),
        "one_loaded_adapter": True,
        "attempts_per_goal": 1,
        "resumable": False,
    }:
        raise AcceptanceError("primary ledger protocol differs from preregistration")

    rows = _sequence(ledger.get("goals"), "primary goals")
    goals = _goal_records(manifest)[:12]
    if len(rows) != len(goals):
        raise AcceptanceError("primary ledger must contain exactly twelve outcomes")
    reports: list[dict[str, object]] = []
    common_adapter: object | None = None
    previous_calls = 0
    previous_requested = 0
    previous_returned = 0
    previous_lines = 0
    previous_malformed = 0
    previous_report_time = started
    expected_artifacts = {PRIMARY_SESSION_OPEN, PRIMARY_SESSION_LEDGER}
    for ordinal, (goal, raw) in enumerate(zip(goals, rows, strict=True), 1):
        row = _mapping(raw, f"primary goal {ordinal}")
        goal_id = str(goal["id"])
        expected_report_name = f"{ordinal:02d}-{goal_id}.json"
        if (
            row.get("ordinal") != ordinal
            or row.get("goal_id") != goal_id
            or row.get("statement") != goal["statement"]
        ):
            raise AcceptanceError("primary ledger goal order changed")
        report_path = _relative_session_file(
            directory,
            row.get("report_path"),
            expected_report_name,
            f"{goal_id} report",
        )
        if row.get("report_sha256") != _sha256_file(report_path):
            raise AcceptanceError(f"{goal_id} report hash mismatch")
        expected_artifacts.add(expected_report_name)
        report = _read_json(report_path)
        artifacts = _mapping(report.get("artifacts"), f"{goal_id}.artifacts")
        if artifacts.get("report") != expected_report_name:
            raise AcceptanceError(f"{goal_id} report artifact name changed")
        report_time = _utc_timestamp(report.get("created_at"), f"{goal_id}.created_at")
        if not previous_report_time <= report_time <= completed:
            raise AcceptanceError(f"{goal_id} report lies outside its session")
        previous_report_time = report_time

        policy_adapter = _mapping(report.get("adapter"), f"{goal_id}.adapter")
        if common_adapter is None:
            common_adapter = policy_adapter
        elif policy_adapter != common_adapter:
            raise AcceptanceError("primary outcomes did not use one loaded adapter")
        generation = _mapping(report.get("generation"), f"{goal_id}.generation")
        search = _mapping(report.get("search"), f"{goal_id}.search")
        calls = generation.get("model_generate_calls")
        requested = generation.get("candidate_sequences_requested")
        returned = generation.get("candidate_sequences_returned")
        lines = generation.get("candidate_lines_returned")
        malformed = generation.get("malformed_sequences_rejected")
        model_calls = search.get("model_calls")
        candidates_executed = search.get("candidates_executed")
        candidates_per_state = _mapping(
            run.get("search_budget_per_goal"), "interactive budget"
        )["candidates_per_state"]
        if (
            type(calls) is not int
            or type(requested) is not int
            or type(returned) is not int
            or type(lines) is not int
            or type(malformed) is not int
            or type(model_calls) is not int
            or type(candidates_executed) is not int
            or calls - previous_calls != model_calls
            or requested - previous_requested != model_calls * candidates_per_state
            or not 0 <= returned - previous_returned <= requested - previous_requested
            or lines - previous_lines < 0
            or malformed - previous_malformed < 0
            or lines
            - previous_lines
            + malformed
            - previous_malformed
            != returned - previous_returned
            or candidates_executed > lines - previous_lines
            or generation.get("one_batched_call_per_search_state") is not True
        ):
            raise AcceptanceError(
                f"{goal_id} generation counters do not continue one loaded session"
            )
        _validate_search_accounting(
            goal_id,
            search,
            _mapping(run.get("search_budget_per_goal"), "interactive budget"),
            candidate_lines=lines - previous_lines,
        )
        previous_calls = calls
        previous_requested = requested
        previous_returned = returned
        previous_lines = lines
        previous_malformed = malformed

        proof_name = row.get("proof_path")
        proof_sha = row.get("proof_sha256")
        publication = _mapping(report.get("publication"), f"{goal_id}.publication")
        if publication.get("status") == "kernel-checked-proof":
            expected_proof_name = f"{ordinal:02d}-{goal_id}.pa"
            proof_path = _relative_session_file(
                directory, proof_name, expected_proof_name, f"{goal_id} proof"
            )
            proof_bytes = proof_path.read_bytes()
            if (
                proof_sha != hashlib.sha256(proof_bytes).hexdigest()
                or publication.get("script_sha256")
                != hashlib.sha256(proof_bytes).hexdigest()
                or artifacts.get("proof") != expected_proof_name
            ):
                raise AcceptanceError(f"{goal_id} proof artifact hash mismatch")
            expected_artifacts.add(expected_proof_name)
        elif (
            proof_name is not None
            or proof_sha is not None
            or artifacts.get("proof") is not None
        ):
            raise AcceptanceError(f"{goal_id} failure unexpectedly has a proof file")
        reports.append(report)
    try:
        actual_artifacts = {entry.name for entry in directory.iterdir()}
    except OSError as exc:
        raise AcceptanceError(f"cannot close primary-session directory: {exc}") from None
    if actual_artifacts != expected_artifacts:
        raise AcceptanceError("primary-session directory contains uncommitted artifacts")
    return PrimarySession(ledger, tuple(reports))


def score_outcomes(
    manifest: Mapping[str, object],
    outcomes: Sequence[GoalOutcome],
    *,
    identity_integrity: bool,
) -> dict[str, object]:
    """Apply the preregistered binary and stretch rules without a model."""

    rows = _goal_records(manifest)
    expected_ids = [str(row["id"]) for row in rows]
    complete = [outcome.goal_id for outcome in outcomes] == expected_ids
    all_claimed_successes_kernel_checked = all(
        not outcome.proved or outcome.kernel_checked for outcome in outcomes
    )
    integrity = bool(
        complete and identity_integrity and all_claimed_successes_kernel_checked
    )
    counts = {
        category: sum(
            outcome.counted_success and outcome.category == category
            for outcome in outcomes
        )
        for category in ("retrieval", "composition", "induction", "sealed")
    }
    overall = sum(counts.values())
    synthesis = counts["composition"] + counts["induction"] + counts["sealed"]
    decision = _mapping(manifest.get("decision_rule"), "decision_rule")
    binary = _mapping(decision.get("binary_pass"), "binary_pass")
    minima = _mapping(binary.get("category_minimums"), "category_minimums")
    nontrivial_ids = set(
        _sequence(
            binary.get("nontrivial_induction_goal_ids"),
            "nontrivial induction ids",
        )
    )
    nontrivial = sum(
        outcome.counted_success and outcome.goal_id in nontrivial_ids
        for outcome in outcomes
    )
    criteria = {
        "integrity": integrity,
        **{
            f"{category}_minimum": counts[category] >= minima[category]
            for category in counts
        },
        "nontrivial_induction_minimum": nontrivial
        >= binary["nontrivial_induction_minimum"],
        "synthesis_minimum": synthesis >= binary["synthesis_minimum"],
        "overall_minimum": overall >= binary["overall_minimum"],
    }
    stretch = _mapping(decision.get("stretch"), "stretch")
    stretch_minima = _mapping(stretch.get("category_minimums"), "stretch minima")
    stretch_pass = bool(
        integrity
        and all(counts[name] >= stretch_minima[name] for name in counts)
        and overall >= stretch["overall_minimum"]
    )
    return {
        "integrity": {
            "passed": integrity,
            "complete_exact_primary_run": complete,
            "one_shared_adapter_identity": identity_integrity,
            "all_claimed_successes_kernel_checked": (
                all_claimed_successes_kernel_checked
            ),
        },
        "counts": {
            "categories": counts,
            "synthesis": synthesis,
            "overall": overall,
            "nontrivial_induction": nontrivial,
        },
        "criteria": criteria,
        "binary_pass": all(criteria.values()),
        "stretch_pass": stretch_pass,
    }


def build_report(
    manifest: Mapping[str, object],
    primary_session: PrimarySession,
    sealed_report: Mapping[str, object],
    *,
    manifest_sha256: str,
    adapter: AdapterAuthority,
    data_audit: Mapping[str, object],
) -> dict[str, object]:
    """Validate one fixed run, independently replay successes, and score it."""

    scorer_job, chain = _current_wmi_job(manifest, role="scorer")
    goals = _goal_records(manifest)
    interactive_reports = primary_session.reports
    if len(interactive_reports) != 12:
        raise AcceptanceError("primary session must contain exactly 12 reports")
    outcomes: list[GoalOutcome] = []
    identities: list[tuple[str, str, str, str]] = []
    for goal, report in zip(goals[:12], interactive_reports, strict=True):
        outcome, identity = _interactive_outcome(
            goal,
            report,
            manifest,
            adapter.identity,
        )
        outcomes.append(outcome)
        identities.append(identity)
    sealed_outcomes, identity = _sealed_outcomes(
        goals[12:], sealed_report, manifest, adapter.identity
    )
    outcomes.extend(sealed_outcomes)
    identities.append(identity)
    identity_integrity = len(set(identities)) == 1
    score = score_outcomes(
        manifest,
        outcomes,
        identity_integrity=identity_integrity,
    )
    return {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "preregistration": {
            "id": manifest.get("preregistration_id"),
            "sha256": manifest_sha256,
        },
        "adapter": dict(adapter.identity),
        "primary_session": {
            "session_id": primary_session.ledger.get("session_id"),
            "ledger_sha256": _sha256_json(primary_session.ledger),
        },
        "wmi_execution": {
            "dataset_generator": _require_dataset_generator_terminal(chain),
            "prepare_job_id": chain["prepare"]["job_id"],
            "training_job_id": chain["train"]["job_id"],
            "sealed_evaluation_job_id": chain["eval"]["job_id"],
            "primary_job_id": chain["primary"]["job_id"],
            "scorer_job": scorer_job,
        },
        "data_audit": dict(data_audit),
        "goals": [
            {
                "id": outcome.goal_id,
                "category": outcome.category,
                "status": outcome.status,
                "proved": outcome.proved,
                "retrieval_hit": outcome.retrieval_hit,
                "kernel_checked": outcome.kernel_checked,
                "counted_success": outcome.counted_success,
                "command_count": outcome.command_count,
                "proof_nodes": outcome.proof_nodes,
            }
            for outcome in outcomes
        ],
        **score,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--compact", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the sealed preregistration")
    audit = subparsers.add_parser(
        "audit-data",
        help="scan the sealed corpus before training, optionally cross-bind an adapter",
    )
    subparsers.add_parser(
        "preflight-training",
        help="verify the completed finalizer and fixed data seal before training",
    )
    snapshot = subparsers.add_parser(
        "verify-base-snapshot",
        help="record an allocated finalizer check of the pinned base bytes",
    )
    snapshot.add_argument("--phase", choices=("before", "after"), required=True)
    preflight = subparsers.add_parser(
        "preflight-primary",
        help="verify the completed one-shot WMI train/eval chain before submission",
    )
    primary = subparsers.add_parser(
        "run-primary",
        help="load once and execute the fixed R1--I4 session exactly once",
    )
    report = subparsers.add_parser(
        "report", help="score the fixed primary ledger and sealed evaluator report"
    )
    verify_report = subparsers.add_parser(
        "verify-report",
        help="rebuild and compare the fixed report without loading a model",
    )
    audit.add_argument("--adapter-dir", type=Path)
    audit.add_argument("--data-dir", type=Path, required=True)
    audit.add_argument("--output", type=Path)
    preflight.add_argument("--adapter-dir", type=Path, required=True)
    preflight.add_argument("--heldout-report", type=Path, required=True)
    for command in (primary, report, verify_report):
        command.add_argument("--adapter-dir", type=Path, required=True)
        command.add_argument("--data-dir", type=Path, required=True)
    for command in (report, verify_report):
        command.add_argument("--heldout-report", type=Path, required=True)
    report.add_argument("--output", type=Path)
    verify_report.add_argument("--output", type=Path, required=True)
    return parser


def _render(value: object, *, compact: bool) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=None if compact else 2,
        sort_keys=True,
        separators=(",", ":") if compact else None,
    )


def _atomic_create_fixed(path: Path, relative: str, label: str, text: str) -> None:
    expected = _repository_path(relative, label).resolve(strict=False)
    candidate = path.resolve(strict=False)
    if candidate != expected or candidate.parent != expected.parent:
        raise AcceptanceError(f"{label} must use its one fixed WMI output path")
    if candidate.parent.is_symlink() or not candidate.parent.is_dir():
        raise AcceptanceError(f"{label} parent is not a plain existing directory")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(candidate, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise AcceptanceError(f"the fixed {label} already exists") from None
    except OSError as exc:
        raise AcceptanceError(f"cannot publish {label}: {exc}") from None


def _atomic_create_report(path: Path, text: str) -> None:
    _atomic_create_fixed(path, WMI_FINAL_REPORT, "final report", text)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _read_json(args.manifest)
        validation = validate_manifest(manifest, manifest_path=args.manifest)
        manifest_sha256 = _sha256_file(args.manifest)
        if args.command == "validate":
            print(
                _render(
                    {"status": "valid", "sha256": manifest_sha256, **validation},
                    compact=args.compact,
                )
            )
            return 0
        if args.command == "audit-data":
            adapter = (
                validate_adapter_authority(args.adapter_dir, manifest)
                if args.adapter_dir is not None
                else None
            )
            data_audit = audit_dataset(args.data_dir, manifest, adapter)
            output_record: dict[str, object] = {
                "status": "valid",
                "adapter": None if adapter is None else adapter.identity,
                "data_audit": data_audit,
            }
            if args.output is not None:
                if adapter is not None:
                    raise AcceptanceError(
                        "the fixed data-audit output is reserved for pre-training"
                    )
                output_record = _pretraining_data_report(
                    manifest,
                    manifest_path=args.manifest,
                    data_audit=data_audit,
                )
                _atomic_create_fixed(
                    args.output,
                    WMI_PRETRAIN_DATA_AUDIT,
                    "pre-training data report",
                    _render(output_record, compact=False) + "\n",
                )
            print(_render(output_record, compact=args.compact))
            return 0
        if args.command == "preflight-training":
            preflight = preflight_training_submission(manifest)
            print(_render(preflight, compact=args.compact))
            return 0
        if args.command == "verify-base-snapshot":
            path = record_base_snapshot_check(manifest, phase=args.phase)
            print(_render({"base_snapshot_report": str(path)}, compact=args.compact))
            return 0
        adapter = validate_adapter_authority(args.adapter_dir, manifest)
        if args.command == "preflight-primary":
            preflight = preflight_primary_submission(
                manifest, adapter, args.heldout_report
            )
            print(_render(preflight, compact=args.compact))
            return 0
        data_audit = audit_dataset(args.data_dir, manifest, adapter)
        if args.command == "run-primary":
            ledger = run_primary_session(
                manifest,
                manifest_sha256=manifest_sha256,
                adapter=adapter,
                data_audit=data_audit,
            )
            print(_render({"primary_session": str(ledger)}, compact=args.compact))
            return 0
        primary = load_primary_session(
            manifest,
            manifest_sha256=manifest_sha256,
            adapter=adapter,
            data_audit=data_audit,
        )
        heldout_path = _plain_file(args.heldout_report, "held-out report")
        if heldout_path != _repository_path(
            WMI_HELDOUT_REPORT, "held-out report"
        ).resolve(strict=False):
            raise AcceptanceError("report must consume the fixed WMI held-out artifact")
        heldout = _read_json(heldout_path)
        report = build_report(
            manifest,
            primary,
            heldout,
            manifest_sha256=manifest_sha256,
            adapter=adapter,
            data_audit=data_audit,
        )
        if args.command == "verify-report":
            expected_output = _repository_path(
                WMI_FINAL_REPORT, "final report"
            ).resolve(strict=False)
            output_path = _plain_file(args.output, "published final report")
            if output_path != expected_output:
                raise AcceptanceError(
                    "report verification requires the fixed WMI output path"
                )
            if _read_json(output_path) != report:
                raise AcceptanceError(
                    "published final report differs from independent rescoring"
                )
            print(
                _render(
                    {
                        "status": "verified",
                        "report": str(output_path),
                        "sha256": _sha256_file(output_path),
                        "binary_pass": report["binary_pass"],
                    },
                    compact=args.compact,
                )
            )
            return 0
    except (AcceptanceError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"acceptance input rejected: {exc}", file=sys.stderr)
        return 2
    try:
        rendered = _render(report, compact=args.compact)
        if args.output is not None:
            _atomic_create_report(args.output, rendered + "\n")
            # Re-open and parse the newly published inode before returning a
            # scientific 0/1 result.  Thus exit 1 can only mean a genuine,
            # durable binary-rule failure, never a publication exception.
            published = _read_json(
                _plain_file(args.output, "newly published final report")
            )
            if published != report:
                raise AcceptanceError("published final report differs from scoring")
            print(_render({"report": str(args.output)}, compact=args.compact))
        else:
            print(rendered)
    except (AcceptanceError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"acceptance output rejected: {exc}", file=sys.stderr)
        return 2
    return 0 if report["binary_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
