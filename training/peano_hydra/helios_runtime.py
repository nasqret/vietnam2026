"""Explicit central-module libraries for the new scheduled Helios experiment.

The ordinary review executor continues stripping all dynamic-loader controls.
This selector is not a general environment inheritance mechanism: it accepts
only reviewed authority-scale/corrective jobs and their known site modules.
Saved path receipts can be validated offline without invoking this selector.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import os
from pathlib import Path
import re
import stat

from .review_runtime import (
    ReviewRuntimeError, runtime_library_record, validate_runtime_library_directories,
)


_MODULE = re.compile(r"[A-Za-z0-9_+.-]{1,96}/[A-Za-z0-9_+.-]{1,96}\Z")
_JOBS = {
    "slurm/peano_hydra_authority_scale_prepare.sbatch":
        ("x86_64", "PEANO_HELIOS_CPU_MODULE", "Python/3.11.5"),
    "slurm/peano_hydra_authority_scale_train.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_authority_scale_evaluate.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_authority_scale_evaluate_recovery.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_corrective_prepare.sbatch":
        ("x86_64", "PEANO_HELIOS_CPU_MODULE", "Python/3.11.5"),
    "slurm/peano_hydra_corrective_train.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_corrective_evaluate.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_search_evaluate.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_frontier_train.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_frontier_evaluate.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_frontier_training.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_frontier_evaluation.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_frontier_diagnostic.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_retention_train.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
    "slurm/peano_hydra_retention_evaluate.sbatch":
        ("aarch64", "PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10"),
}
# The operational v2 jobs retain the reviewed script filenames. Historical v1
# library receipts keep their profile; neither version accepts an arbitrary
# experiment label or relaxes the architecture/module/library checks below.
_CORRECTIVE_PROFILES = frozenset({"peano-hydra-corrective-v1", "peano-hydra-corrective-v2"})
# One site-maintained modulefile alias, read and reviewed on 2026-08-28.
# No version-range inference or Lua execution is permitted by this exception.
_REVIEWED_MODULE_ALIASES = {
    ("libpng/1.6.50", "/net/software/aarch64/el9/libpng/1.6.52", "1.6.52"): (
        "/net/software/aarch64/el9modules/all/Compiler/GCCcore/14.3.0/libpng/1.6.50.lua",
        "/net/software/aarch64/el9modules/all/Core/libpng/1.6.52.lua",
        1172,
        "c9756b9edf3d38edc686263142992360bc709998e29449241278cfe5d888ebc2",
    ),
}


def _reviewed_module_alias(owner: str, root: str, version: str) -> bool:
    alias = _REVIEWED_MODULE_ALIASES.get((owner, root, version))
    if alias is None:
        return False
    requested, resolved, size, digest = alias
    try:
        if str(Path(requested).resolve(strict=True)) != resolved:
            return False
        with Path(resolved).open("rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & stat.S_IWOTH
                or metadata.st_size != size):
                return False
            raw = stream.read(size + 1)
        return len(raw) == size and hashlib.sha256(raw).hexdigest() == digest
    except (OSError, RuntimeError, ValueError):
        return False


def _easybuild_name(name: str) -> str:
    """The environment spelling used by the reviewed site's EasyBuild modules."""
    return name.upper().replace("+", "PLUS").replace("-", "MIN").replace(".", "")


def _declared_module_for_root(parts: tuple[str, ...], modules: list[str],
                              values: Mapping[str, str]) -> str | None:
    if len(parts) < 8:
        return None
    package, installed_version = parts[5:7]
    owners = [module for module in modules if module.split("/", 1)[0] == package]
    if len(owners) != 1:
        return None
    owner = owners[0]
    if owner == f"{package}/{installed_version}":
        return owner
    # Hierarchical module names omit their compiler/toolchain installation
    # suffix. Never guess it by stripping version text: require the exact root
    # and software version exported by the uniquely loaded EasyBuild module.
    # For example Python/3.13.5 owns 3.13.5-GCCcore-14.3.0, and
    # Clang/21.1.2-CUDA-12.9.1 owns 21.1.2-GCCcore-14.3.0-CUDA-12.9.1.
    name = _easybuild_name(package)
    if sum(_easybuild_name(module.split("/", 1)[0]) == name for module in modules) != 1:
        return None
    root = str(Path(*parts[:7]))
    version = values.get(f"EBVERSION{name}")
    if (values.get(f"EBROOT{name}") != root or type(version) is not str
        or _MODULE.fullmatch(f"{package}/{version}") is None):
        return None
    module_version = owner.split("/", 1)[1]
    if (not all(candidate == version or candidate.startswith(version + "-")
                for candidate in (module_version, installed_version))
        and not _reviewed_module_alias(owner, root, version)):
        return None
    return owner


def reviewed_runtime_library_paths(environment: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Select canonical ordered module-library directories, or local default ().

    Only LD_LIBRARY_PATH is considered. Raw and resolved module paths must stay
    below the expected architecture's central /net/software tree. Legitimate
    site lib/lib64 symlinks are resolved before the executor's real-directory
    check. Hierarchical installation names additionally require the loaded
    module's exact EBROOT and compatible EBVERSION metadata. One reviewed site
    alias additionally pins its resolved modulefile and complete raw bytes.
    Unknown scheduled jobs/modules, user paths, empty components, loader knobs, and ambiguous or
    reordered-by-deduplication selections fail closed.
    """
    values = os.environ if environment is None else environment
    if not isinstance(values, Mapping):
        raise ReviewRuntimeError("Helios runtime selection requires an environment mapping")
    if "SLURM_JOB_ID" not in values:
        return ()
    job_id = values.get("SLURM_JOB_ID")
    job = values.get("PEANO_JOB_SCRIPT")
    if (type(job_id) is not str or re.fullmatch(r"[1-9][0-9]{0,19}", job_id) is None
        or type(job) is not str or job not in _JOBS):
        raise ReviewRuntimeError("central runtime libraries require one reviewed scheduled authority job")
    if (job.startswith("slurm/peano_hydra_corrective_")
        and (type(values.get("PEANO_HYDRA_PROFILE")) is not str
             or values["PEANO_HYDRA_PROFILE"] not in _CORRECTIVE_PROFILES)):
        raise ReviewRuntimeError("scheduled corrective job changed its exact experiment profile")
    if (job == "slurm/peano_hydra_search_evaluate.sbatch"
        and values.get("PEANO_HYDRA_PROFILE") != "peano-hydra-search-v2"):
        raise ReviewRuntimeError("scheduled search evaluation changed its exact experiment profile")
    if (job in ("slurm/peano_hydra_frontier_train.sbatch", "slurm/peano_hydra_frontier_evaluate.sbatch")
        and values.get("PEANO_HYDRA_PROFILE") != "peano-hydra-frontier-v1"):
        raise ReviewRuntimeError("scheduled frontier job changed its exact experiment profile")
    if (job == "slurm/peano_hydra_frontier_training.sbatch"
        and values.get("PEANO_HYDRA_PROFILE") != "peano-hydra-frontier-training-v1"):
        raise ReviewRuntimeError("scheduled training-only job changed its exact experiment profile")
    if (job == "slurm/peano_hydra_frontier_evaluation.sbatch"
        and values.get("PEANO_HYDRA_PROFILE") != "peano-hydra-frontier-evaluation-v1"):
        raise ReviewRuntimeError("scheduled evaluation-only job changed its exact experiment profile")
    if (job == "slurm/peano_hydra_frontier_diagnostic.sbatch"
        and values.get("PEANO_HYDRA_PROFILE") != "peano-hydra-frontier-diagnostic-v1"):
        raise ReviewRuntimeError("scheduled DEV diagnostic changed its exact experiment profile")
    if (job in ("slurm/peano_hydra_retention_train.sbatch", "slurm/peano_hydra_retention_evaluate.sbatch")
        and values.get("PEANO_HYDRA_PROFILE") != "peano-hydra-retention-pilot-v1"):
        raise ReviewRuntimeError("scheduled retention pilot changed its exact experiment profile")
    architecture, marker, expected_module = _JOBS[job]
    if values.get(marker) != expected_module:
        raise ReviewRuntimeError("scheduled authority job changed its reviewed central module")
    other_marker = "PEANO_HELIOS_ML_MODULE" if marker == "PEANO_HELIOS_CPU_MODULE" else "PEANO_HELIOS_CPU_MODULE"
    if other_marker in values:
        raise ReviewRuntimeError("scheduled authority job has conflicting CPU/GPU module markers")
    loaded = values.get("LOADEDMODULES")
    if type(loaded) is not str or not 1 <= len(loaded) <= 16384:
        raise ReviewRuntimeError("scheduled authority job has no bounded loaded-module inventory")
    modules = loaded.split(":")
    if (not 1 <= len(modules) <= 128 or len(set(modules)) != len(modules)
        or any(_MODULE.fullmatch(module) is None for module in modules)
        or expected_module not in modules
        or sum(module.split("/", 1)[0] == expected_module.split("/", 1)[0] for module in modules) != 1):
        raise ReviewRuntimeError("scheduled authority job has an unknown or ambiguous module selection")
    if any(type(name) is str and name.startswith(("LD_", "DYLD_")) and name != "LD_LIBRARY_PATH"
           for name in values):
        raise ReviewRuntimeError("reviewed central modules do not authorize other dynamic-loader variables")
    raw = values.get("LD_LIBRARY_PATH")
    if type(raw) is not str or not 1 <= len(raw) <= 32768:
        raise ReviewRuntimeError("scheduled authority job has no bounded central library path")
    paths = tuple(raw.split(":"))
    # Syntax and directory-list bounds are checked before any filesystem access.
    runtime_library_record(paths)
    prefix = f"/net/software/{architecture}/"
    resolved = []
    found_python = False
    for value in paths:
        if not value.startswith(prefix):
            raise ReviewRuntimeError("scheduled authority job mixed central runtime architectures")
        parts = Path(value).parts
        owner = _declared_module_for_root(parts, modules, values)
        if owner is None:
            raise ReviewRuntimeError(
                f"runtime library path is not owned by a declared loaded module: {value}")
        found_python |= owner == "Python/3.11.5"
        try:
            real = str(Path(value).resolve(strict=True))
        except (OSError, RuntimeError, ValueError) as error:
            raise ReviewRuntimeError("reviewed central module library is unavailable") from error
        if not real.startswith(prefix):
            raise ReviewRuntimeError("central module library symlink escapes its reviewed architecture")
        resolved.append(real)
    if architecture == "x86_64" and not found_python:
        raise ReviewRuntimeError("CPU runtime paths omit the reviewed Python shared library")
    selected = tuple(resolved)
    runtime_library_record(selected)
    validate_runtime_library_directories(selected)
    return selected
