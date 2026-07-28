"""Reproducible source, scheduler, and package identity for Peano runs.

The Slurm submission ledger and the adapter manifest serve different purposes:
the former records that a job was accepted, while the latter records what that
job produced.  This module joins them by job id and rejects a mismatched source
sync or job script before a result can be published.
"""

from __future__ import annotations

import csv
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import socket
from typing import Any, Iterable

from .manifest import hash_files, sha256_file, sha256_json


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PROVENANCE_PATH = REPOSITORY_ROOT / ".peano-source-provenance.tsv"
SUBMISSION_LEDGER_PATH = REPOSITORY_ROOT / "logs" / "submissions.tsv"
REQUIREMENTS_PATH = (
    REPOSITORY_ROOT / "training" / "peano_policy" / "requirements-helios.lock"
)
SUBMISSION_FIELDS = (
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
RUNTIME_DISTRIBUTIONS = (
    "accelerate",
    "certifi",
    "charset-normalizer",
    "filelock",
    "fsspec",
    "hf-xet",
    "huggingface-hub",
    "idna",
    "Jinja2",
    "MarkupSafe",
    "mpmath",
    "networkx",
    "numpy",
    "packaging",
    "peft",
    "psutil",
    "PyYAML",
    "regex",
    "requests",
    "safetensors",
    "sympy",
    "tokenizers",
    "tomli",
    "torch",
    "tqdm",
    "transformers",
    "typing-extensions",
    "urllib3",
)
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_JOB_ID_RE = re.compile(r"[0-9]+")
_TIMESTAMP_RE = re.compile(r"[0-9TZ:+-]+")


def _one_line(label: str, value: object, pattern: re.Pattern[str]) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise ValueError(f"{label} is missing or malformed")
    return value


def source_sync_identity(*, required: bool) -> dict[str, object]:
    """Read the small source record written by ``helios_sync_project.sh``."""

    path = SOURCE_PROVENANCE_PATH
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"missing Helios source provenance: {path}")
        return {"status": "not-synced"}
    if path.is_symlink() or path.stat().st_size > 1_024:
        raise ValueError("Helios source provenance is not one small regular file")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError("Helios source provenance is not UTF-8") from exc
    if text.count("\n") != 1 or not text.endswith("\n"):
        raise ValueError("Helios source provenance must contain exactly one row")
    fields = text[:-1].split("\t")
    if len(fields) != 3:
        raise ValueError("Helios source provenance must contain three TSV fields")
    commit = _one_line("source commit", fields[0], _COMMIT_RE)
    dirty = fields[1]
    if dirty not in {"true", "false"}:
        raise ValueError("source dirty flag must be true or false")
    synced_at = _one_line("source sync timestamp", fields[2], _TIMESTAMP_RE)
    return {
        "status": "synced",
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": sha256_file(path),
        "git_commit": commit,
        "git_dirty": dirty == "true",
        "synced_at": synced_at,
    }


def job_script_identity(*, required: bool) -> dict[str, object]:
    """Hash the exact Slurm script named by the running job."""

    value = os.environ.get("PEANO_JOB_SCRIPT")
    if value is None:
        if required:
            raise ValueError("PEANO_JOB_SCRIPT is required inside a Slurm job")
        return {"status": "not-declared"}
    if (
        not value.startswith("slurm/")
        or Path(value).is_absolute()
        or ".." in Path(value).parts
        or re.fullmatch(r"[A-Za-z0-9._/-]+", value) is None
    ):
        raise ValueError("PEANO_JOB_SCRIPT must be one safe relative slurm path")
    path = (REPOSITORY_ROOT / value).resolve()
    slurm_root = (REPOSITORY_ROOT / "slurm").resolve()
    if path.parent != slurm_root or not path.is_file() or path.is_symlink():
        raise ValueError("PEANO_JOB_SCRIPT does not name a regular repository job")
    return {"status": "declared", "path": value, "sha256": sha256_file(path)}


def module_identity(*, required: bool) -> dict[str, object]:
    """Record the pinned module request and Lmod's resolved module stack."""

    requested = os.environ.get("PEANO_HELIOS_ML_MODULE")
    loaded = os.environ.get("LOADEDMODULES")
    if requested is None and loaded is None:
        if required:
            raise ValueError("the scheduled job did not record its module stack")
        return {"status": "not-loaded"}
    for label, value in (
        ("PEANO_HELIOS_ML_MODULE", requested),
        ("LOADEDMODULES", loaded),
    ):
        if value is not None and (not value or len(value) > 4_000 or any(
            ord(character) < 32 or ord(character) == 127 for character in value
        )):
            raise ValueError(f"{label} is required and must contain safe text")
    if required and (requested is None or loaded is None):
        raise ValueError("the scheduled job did not record its complete module stack")
    if required and requested not in loaded.split(":"):
        raise ValueError("the requested ML module is absent from LOADEDMODULES")
    return {
        "status": "loaded",
        "requested": requested,
        "loaded_modules": None if loaded is None else loaded.split(":"),
    }


def deployment_identity() -> dict[str, object]:
    """Stable source identity suitable for a resumable run identity."""

    scheduled = os.environ.get("SLURM_JOB_ID") is not None
    return {
        "mode": "slurm" if scheduled else "local",
        "source_sync": source_sync_identity(required=scheduled),
        "job_script": job_script_identity(required=scheduled),
        "modules": module_identity(required=scheduled),
    }


def _submission_row(job_id: str) -> dict[str, str]:
    path = SUBMISSION_LEDGER_PATH
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"missing Slurm submission ledger: {path}")
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != SUBMISSION_FIELDS:
                raise ValueError("Slurm submission ledger has an incompatible header")
            matches = [dict(row) for row in reader if row.get("job_id") == job_id]
    except UnicodeError as exc:
        raise ValueError("Slurm submission ledger is not UTF-8") from exc
    if len(matches) != 1:
        raise ValueError(
            f"Slurm submission ledger must contain exactly one row for job {job_id}"
        )
    return matches[0]


def slurm_job_identity() -> dict[str, object]:
    """Join the running Slurm environment to its independently written ledger."""

    raw_job_id = os.environ.get("SLURM_JOB_ID")
    if raw_job_id is None:
        return {"scheduler": "none", "deployment": deployment_identity()}
    job_id = _one_line("SLURM_JOB_ID", raw_job_id, _JOB_ID_RE)
    deployment = deployment_identity()
    source = deployment["source_sync"]
    script = deployment["job_script"]
    if type(source) is not dict or type(script) is not dict:
        raise RuntimeError("internal deployment identity is malformed")
    row = _submission_row(job_id)
    for field in SUBMISSION_FIELDS:
        if type(row.get(field)) is not str or any(
            character in row[field] for character in "\r\n\t"
        ):
            raise ValueError(f"submission ledger field {field!r} is malformed")
    if (
        row["script"] != script.get("path")
        or row["script_sha256"] != script.get("sha256")
        or row["git_commit"] != source.get("git_commit")
        or (row["git_dirty"] == "true") != source.get("git_dirty")
        or row["sync_timestamp"] != source.get("synced_at")
        or Path(row["workdir"]).resolve() != REPOSITORY_ROOT.resolve()
    ):
        raise ValueError("Slurm ledger row does not match the running source deployment")
    if row["git_dirty"] not in {"true", "false"}:
        raise ValueError("Slurm ledger dirty flag is malformed")
    dependency = row["dependency_job_id"]
    if dependency and _JOB_ID_RE.fullmatch(dependency) is None:
        raise ValueError("Slurm ledger dependency job id is malformed")

    environment_fields = {
        name: os.environ.get(name)
        for name in (
            "SLURM_JOB_NAME",
            "SLURM_JOB_ACCOUNT",
            "SLURM_JOB_PARTITION",
            "SLURM_CLUSTER_NAME",
            "SLURM_JOB_NODELIST",
            "SLURM_SUBMIT_DIR",
        )
    }
    for name, value in environment_fields.items():
        if value is not None and (
            not value
            or len(value) > 1_000
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ValueError(f"{name} contains unsafe text")
    submit_dir = environment_fields["SLURM_SUBMIT_DIR"]
    if submit_dir is None or Path(submit_dir).resolve() != REPOSITORY_ROOT.resolve():
        raise ValueError("SLURM_SUBMIT_DIR differs from the repository root")
    return {
        "scheduler": "slurm",
        "job_id": job_id,
        "environment": environment_fields,
        "deployment": deployment,
        "submission": row,
        "ledger": {
            "path": SUBMISSION_LEDGER_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "row_sha256": sha256_json(row),
        },
    }


def runtime_identity(torch_module: Any | None = None) -> dict[str, object]:
    """Record behavior-relevant Python distributions and accelerator details."""

    packages: dict[str, str | None] = {}
    for distribution in RUNTIME_DISTRIBUTIONS:
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = None
    result: dict[str, object] = {
        "implementation": platform.python_implementation(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "packages": packages,
        "packages_sha256": sha256_json(packages),
        "requirements": {
            "path": REQUIREMENTS_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": sha256_file(REQUIREMENTS_PATH),
        },
    }
    if torch_module is not None:
        cuda_available = bool(torch_module.cuda.is_available())
        accelerator: dict[str, object] = {
            "torch": str(torch_module.__version__),
            "cuda_available": cuda_available,
            "cuda_runtime": torch_module.version.cuda,
            "cudnn": (
                torch_module.backends.cudnn.version() if cuda_available else None
            ),
        }
        if cuda_available:
            accelerator.update(
                device_name=torch_module.cuda.get_device_name(0),
                device_capability=list(torch_module.cuda.get_device_capability(0)),
                bf16_supported=bool(torch_module.cuda.is_bf16_supported()),
            )
        result["accelerator"] = accelerator
    return result


def source_files_identity(paths: Iterable[Path]) -> dict[str, object]:
    """Hash a closed, explicit set of repository source files."""

    resolved = tuple(path.resolve() for path in paths)
    if not resolved or any(
        not path.is_file() or REPOSITORY_ROOT.resolve() not in path.parents
        for path in resolved
    ):
        raise ValueError("source fingerprint requires repository regular files")
    return hash_files(REPOSITORY_ROOT, resolved)


def detached_json(value: object) -> object:
    """Return a strict detached JSON copy for untrusted report composition."""

    return json.loads(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


__all__ = [
    "RUNTIME_DISTRIBUTIONS",
    "SUBMISSION_FIELDS",
    "deployment_identity",
    "detached_json",
    "job_script_identity",
    "module_identity",
    "runtime_identity",
    "slurm_job_identity",
    "source_files_identity",
    "source_sync_identity",
]
