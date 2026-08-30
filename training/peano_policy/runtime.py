"""Reproducible source, scheduler, and package identity for Peano runs.

The Slurm submission ledger and the adapter manifest serve different purposes:
the former records that a job was accepted, while the latter records what that
job produced.  This module joins them by job id and rejects a mismatched source
sync or job script before a result can be published.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
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
    "pip",
    "psutil",
    "PyYAML",
    "regex",
    "requests",
    "safetensors",
    "setuptools",
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
_REQUIREMENTS_OVERRIDE_RE = re.compile(
    r"training/peano_policy/requirements-[A-Za-z0-9._-]{1,80}\.lock"
)
_BASE_MANIFEST_RE = re.compile(
    r"training/peano_policy/wmi-base-v[0-9]{1,3}\.json"
)
_SAFE_DECLARATION_RE = re.compile(r"[A-Za-z0-9._/-]{1,128}")
_NVIDIA_DRIVER_RE = re.compile(r"[0-9]+(?:\.[0-9]+){1,2}")


def _one_line(label: str, value: object, pattern: re.Pattern[str]) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise ValueError(f"{label} is missing or malformed")
    return value


def source_sync_identity(*, required: bool) -> dict[str, object]:
    """Read the small source record written by a cluster sync tool."""

    path = SOURCE_PROVENANCE_PATH
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"missing source provenance: {path}")
        return {"status": "not-synced"}
    if path.is_symlink() or path.stat().st_size > 1_024:
        raise ValueError("source provenance is not one small regular file")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError("source provenance is not UTF-8") from exc
    if text.count("\n") != 1 or not text.endswith("\n"):
        raise ValueError("source provenance must contain exactly one row")
    fields = text[:-1].split("\t")
    if len(fields) != 3:
        raise ValueError("source provenance must contain three TSV fields")
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
    candidate = REPOSITORY_ROOT / value
    slurm_root = (REPOSITORY_ROOT / "slurm").resolve()
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError("PEANO_JOB_SCRIPT does not name a regular repository job")
    path = candidate.resolve()
    if path.parent != slurm_root:
        raise ValueError("PEANO_JOB_SCRIPT does not name a regular repository job")
    file_sha256 = sha256_file(path)
    result: dict[str, object] = {
        "status": "declared",
        "path": value,
        "sha256": file_sha256,
    }
    if os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi":
        support = support_script_identity(required=True)
        support_sha256 = support.get("sha256")
        if type(support_sha256) is not str:
            raise RuntimeError("WMI support script identity is malformed")
        result["file_sha256"] = file_sha256
        result["support_script"] = support
        result["sha256"] = hashlib.sha256(
            f"{file_sha256}\n{support_sha256}\n".encode("ascii")
        ).hexdigest()
    return result


def module_identity(*, required: bool) -> dict[str, object]:
    """Record the pinned module request and Lmod's resolved module stack."""

    generic = os.environ.get("PEANO_ML_MODULE")
    legacy = os.environ.get("PEANO_HELIOS_ML_MODULE")
    if generic is not None and legacy is not None and generic != legacy:
        raise ValueError("generic and Helios module declarations disagree")
    requested = generic if generic is not None else legacy
    loaded = os.environ.get("LOADEDMODULES")
    if requested is None and loaded is None:
        if required:
            raise ValueError("the scheduled job did not record its module stack")
        return {"status": "not-loaded"}
    for label, value in (
        ("requested ML module", requested),
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


def _requirements_path() -> Path:
    """Resolve one declared repository lock, preserving the Helios default."""

    value = os.environ.get("PEANO_REQUIREMENTS_LOCK")
    if value is None:
        path = REQUIREMENTS_PATH
    else:
        candidate = Path(value)
        if (
            not value
            or candidate.is_absolute()
            or ".." in candidate.parts
            or _REQUIREMENTS_OVERRIDE_RE.fullmatch(value) is None
        ):
            raise ValueError("requirements lock must be one safe relative path")
        path = REPOSITORY_ROOT / candidate
    if path.is_symlink() or not path.is_file():
        raise ValueError("requirements lock must be one repository regular file")
    resolved = path.resolve()
    root = REPOSITORY_ROOT.resolve()
    if root not in resolved.parents:
        raise ValueError("requirements lock resolves outside the repository")
    return resolved


def requirements_identity() -> dict[str, str]:
    """Hash the exact runtime lock selected by the scheduled wrapper."""

    path = _requirements_path()
    return {
        "path": path.relative_to(REPOSITORY_ROOT.resolve()).as_posix(),
        "sha256": sha256_file(path),
    }


def _base_manifest_path() -> Path:
    """Resolve the reviewed WMI central-environment contract."""

    value = os.environ.get("PEANO_BASE_MANIFEST")
    if value is None:
        raise ValueError("PEANO_BASE_MANIFEST is required for this runtime")
    candidate = Path(value)
    if (
        candidate.is_absolute()
        or ".." in candidate.parts
        or _BASE_MANIFEST_RE.fullmatch(value) is None
    ):
        raise ValueError("base manifest must be one safe relative path")
    path = REPOSITORY_ROOT / candidate
    if path.is_symlink() or not path.is_file():
        raise ValueError("base manifest must be one repository regular file")
    resolved = path.resolve()
    root = REPOSITORY_ROOT.resolve()
    if root not in resolved.parents:
        raise ValueError("base manifest resolves outside the repository")
    return resolved


def base_manifest_identity() -> dict[str, str]:
    """Hash the reviewed central package inventory selected by WMI."""

    path = _base_manifest_path()
    return {
        "path": path.relative_to(REPOSITORY_ROOT.resolve()).as_posix(),
        "sha256": sha256_file(path),
    }


def support_script_identity(*, required: bool) -> dict[str, object]:
    """Hash a fixed scheduled-job helper sourced outside the Slurm spool."""

    value = os.environ.get("PEANO_JOB_ENV_SCRIPT")
    if value is None:
        if required:
            raise ValueError("PEANO_JOB_ENV_SCRIPT is required for this runtime")
        return {"status": "not-declared"}
    candidate = Path(value)
    if (
        not value.startswith("scripts/")
        or candidate.is_absolute()
        or ".." in candidate.parts
        or re.fullmatch(r"[A-Za-z0-9._/-]+", value) is None
    ):
        raise ValueError("PEANO_JOB_ENV_SCRIPT must be one safe scripts path")
    path = REPOSITORY_ROOT / candidate
    scripts_root = (REPOSITORY_ROOT / "scripts").resolve()
    if (
        path.is_symlink()
        or not path.is_file()
        or path.resolve().parent != scripts_root
    ):
        raise ValueError(
            "PEANO_JOB_ENV_SCRIPT does not name one regular repository helper"
        )
    file_sha256 = sha256_file(path)
    declared_sha256 = os.environ.get("PEANO_JOB_ENV_SHA256")
    if required and declared_sha256 is None:
        raise ValueError("PEANO_JOB_ENV_SHA256 is required for this runtime")
    if declared_sha256 is not None and (
        re.fullmatch(r"[0-9a-f]{64}", declared_sha256) is None
        or declared_sha256 != file_sha256
    ):
        raise ValueError("sourced WMI helper hash does not match its current file")
    result: dict[str, object] = {
        "status": "declared",
        "path": value,
        "sha256": file_sha256,
    }
    if declared_sha256 is not None:
        result["sourced_sha256"] = declared_sha256
    return result


def _runtime_declaration() -> dict[str, object] | None:
    """Bind non-default cluster runtime choices into pre-run identity."""

    backend = os.environ.get("PEANO_CLUSTER_BACKEND")
    base_environment = os.environ.get("PEANO_BASE_ENV")
    lock = os.environ.get("PEANO_REQUIREMENTS_LOCK")
    base_manifest = os.environ.get("PEANO_BASE_MANIFEST")
    values = (backend, base_environment, lock, base_manifest)
    if values == (None, None, None, None):
        return None
    if any(value is None for value in values):
        raise ValueError("cluster runtime declaration is incomplete")
    assert backend is not None and base_environment is not None
    for label, value in (
        ("PEANO_CLUSTER_BACKEND", backend),
        ("PEANO_BASE_ENV", base_environment),
    ):
        if _SAFE_DECLARATION_RE.fullmatch(value) is None:
            raise ValueError(f"{label} is malformed")
    return {
        "backend": backend,
        "base_environment": base_environment,
        "base_manifest": base_manifest_identity(),
        "requirements": requirements_identity(),
    }


def deployment_identity() -> dict[str, object]:
    """Stable source identity suitable for a resumable run identity."""

    scheduled = os.environ.get("SLURM_JOB_ID") is not None
    result: dict[str, object] = {
        "mode": "slurm" if scheduled else "local",
        "source_sync": source_sync_identity(required=scheduled),
        "job_script": job_script_identity(required=scheduled),
        "modules": module_identity(required=scheduled),
    }
    declaration = _runtime_declaration()
    if declaration is not None:
        result["runtime_declaration"] = declaration
    support_required = scheduled and os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi"
    if support_required or os.environ.get("PEANO_JOB_ENV_SCRIPT") is not None:
        result["support_script"] = support_script_identity(
            required=support_required
        )
    return result


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

    environment_names = (
        "SLURM_JOB_NAME",
        "SLURM_JOB_ACCOUNT",
        "SLURM_JOB_PARTITION",
        "SLURM_CLUSTER_NAME",
        "SLURM_JOB_NODELIST",
        "SLURM_SUBMIT_DIR",
    )
    if os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi":
        environment_names += ("SLURM_JOB_CONSTRAINTS", "SLURM_JOB_GRES")
    environment_fields = {
        name: os.environ.get(name) for name in environment_names
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

    distributions = RUNTIME_DISTRIBUTIONS
    if os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi":
        distributions += ("torchaudio", "torchvision", "triton")
    packages: dict[str, str | None] = {}
    for distribution in distributions:
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
        "requirements": requirements_identity(),
    }
    if os.environ.get("PEANO_BASE_MANIFEST") is not None:
        result["base_manifest"] = base_manifest_identity()
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
            if os.environ.get("PEANO_CLUSTER_BACKEND") == "wmi":
                accelerator["total_memory"] = int(
                    torch_module.cuda.get_device_properties(0).total_memory
                )
                accelerator["nvidia_driver"] = _nvidia_driver_version()
        result["accelerator"] = accelerator
    return result


def _nvidia_driver_version() -> str:
    """Return one canonical driver version even on a multi-GPU WMI node."""

    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=driver_version",
            "--format=csv,noheader",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    driver_versions = {
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    }
    if (
        len(driver_versions) != 1
        or _NVIDIA_DRIVER_RE.fullmatch(next(iter(driver_versions), "")) is None
    ):
        raise RuntimeError("WMI nodes must report one canonical NVIDIA driver")
    return driver_versions.pop()


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
    "base_manifest_identity",
    "deployment_identity",
    "detached_json",
    "job_script_identity",
    "module_identity",
    "requirements_identity",
    "runtime_identity",
    "slurm_job_identity",
    "source_files_identity",
    "source_sync_identity",
    "support_script_identity",
]
