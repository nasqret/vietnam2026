#!/usr/bin/env bash
# Shared WMI compute-job environment. Source this only from Bash Slurm jobs.

readonly PEANO_WMI_PROJECT_ROOT="/work/bnaskrecki/peano-lab-training"
readonly PEANO_WMI_CONDA_MODULE="anaconda/2025.12-1"
readonly PEANO_WMI_BASE_ENV="pytorch-gpu"
readonly PEANO_WMI_CENTRAL_PREFIX="/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu"
readonly PEANO_WMI_REQUIREMENTS_LOCK="training/peano_policy/requirements-wmi-overlay.lock"
readonly PEANO_WMI_BASE_MANIFEST="training/peano_policy/wmi-base-v1.json"

peano_wmi_activate_base() {
  if [ "${SLURM_SUBMIT_DIR:-}" != "$PEANO_WMI_PROJECT_ROOT" ]; then
    printf 'unexpected WMI submit directory: %s\n' "${SLURM_SUBMIT_DIR:-}" >&2
    return 1
  fi
  cd "$PEANO_WMI_PROJECT_ROOT"
  unset PEANO_HELIOS_ML_MODULE
  unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
  unset HUGGINGFACE_HUB_CACHE HF_HUB_CACHE TRANSFORMERS_CACHE
  unset PYTHONOPTIMIZE
  module purge
  export PEANO_ML_MODULE="$PEANO_WMI_CONDA_MODULE"
  module load "$PEANO_ML_MODULE"

  # The central MKL hook is not nounset-clean. Limit the relaxation to Conda's
  # administrator-owned activation hooks, then restore the caller's strictness.
  set +u
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate "$PEANO_WMI_BASE_ENV"
  set -u
  if [ "${CONDA_PREFIX:-}" != "$PEANO_WMI_CENTRAL_PREFIX" ]; then
    printf 'unexpected WMI Conda prefix: %s\n' "${CONDA_PREFIX:-}" >&2
    return 1
  fi

  export PEANO_CLUSTER_BACKEND=wmi
  export PEANO_BASE_ENV="$PEANO_WMI_BASE_ENV"
  export PEANO_REQUIREMENTS_LOCK="$PEANO_WMI_REQUIREMENTS_LOCK"
  export PEANO_BASE_MANIFEST="$PEANO_WMI_BASE_MANIFEST"
  export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
  export PYTHONHASHSEED=20260728
  export PYTHONNOUSERSITE=1
  export PYTHONPATH="$PEANO_WMI_PROJECT_ROOT/peano-lab/py:$PEANO_WMI_PROJECT_ROOT"
  export HF_HOME="$PEANO_WMI_PROJECT_ROOT/.cache/huggingface"
  export TOKENIZERS_PARALLELISM=false
}

peano_wmi_verify_base_manifest() {
  PEANO_WMI_EXPECTED_MODULE="$PEANO_WMI_CONDA_MODULE" \
    PEANO_WMI_EXPECTED_ENV="$PEANO_WMI_BASE_ENV" \
    PEANO_WMI_EXPECTED_CENTRAL_PREFIX="$PEANO_WMI_CENTRAL_PREFIX" \
    python - "$PEANO_WMI_BASE_MANIFEST" <<'PY'
import importlib.metadata
import ensurepip
import json
import os
from pathlib import Path
import platform
import sys

import torch

path = Path(sys.argv[1])
raw = path.read_text(encoding="utf-8")
manifest = json.loads(raw)
if type(manifest) is not dict:
    raise TypeError("WMI base manifest must be one JSON object")
if raw != json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n":
    raise ValueError("WMI base manifest is not canonical JSON")
if set(manifest) != {
    "base_environment",
    "central_prefix",
    "ensurepip",
    "machine",
    "module",
    "packages",
    "python",
    "torch_cuda",
    "v",
}:
    raise ValueError("WMI base manifest has unexpected fields")
central = Path(os.environ["PEANO_WMI_EXPECTED_CENTRAL_PREFIX"]).resolve()
expected_scalars = {
    "base_environment": os.environ["PEANO_WMI_EXPECTED_ENV"],
    "central_prefix": str(central),
    "ensurepip": ensurepip.version(),
    "machine": platform.machine(),
    "module": os.environ["PEANO_WMI_EXPECTED_MODULE"],
    "python": platform.python_version(),
    "torch_cuda": torch.version.cuda,
    "v": 1,
}
for name, actual in expected_scalars.items():
    if manifest.get(name) != actual:
        raise ValueError(f"WMI base manifest mismatch for {name}: {actual!r}")
if Path(sys.prefix).resolve() != central:
    raise ValueError(f"central Python prefix mismatch: {sys.prefix}")
packages = manifest.get("packages")
if type(packages) is not dict or not packages:
    raise ValueError("WMI base manifest has no package inventory")
for requested, expected_version in packages.items():
    if type(requested) is not str or type(expected_version) is not str:
        raise TypeError("WMI base package inventory must map strings to strings")
    distribution = importlib.metadata.distribution(requested)
    if distribution.version != expected_version:
        raise ValueError(
            f"WMI base package mismatch for {requested}: {distribution.version}"
        )
    location = Path(distribution.locate_file("")).resolve()
    if not location.is_relative_to(central):
        raise ValueError(f"WMI base package escaped central prefix: {requested}")
print(json.dumps({"base_manifest": str(path), "status": "verified"}, sort_keys=True))
PY
}

peano_wmi_environment_id() {
  peano_wmi_verify_base_manifest >/dev/null || return 1
  local base_record overlay_record environment_id
  base_record="$(sha256sum "$PEANO_WMI_BASE_MANIFEST")" || return 1
  overlay_record="$(sha256sum "$PEANO_WMI_REQUIREMENTS_LOCK")" || return 1
  environment_id="$({
    printf '%s\n' "peano-wmi-environment-v2"
    printf '%s\n' "$base_record"
    printf '%s\n' "$overlay_record"
  } | sha256sum | awk '{print $1}')" || return 1
  if [[ ! "$environment_id" =~ ^[0-9a-f]{64}$ ]]; then
    printf 'invalid computed WMI environment id: %s\n' "$environment_id" >&2
    return 1
  fi
  printf '%s\n' "$environment_id"
}

peano_wmi_current_python() {
  local pointer="$PEANO_WMI_PROJECT_ROOT/.venv-wmi/current"
  if [ ! -f "$pointer" ] || [ -L "$pointer" ] || [ "$(wc -l < "$pointer")" -ne 1 ]; then
    printf 'missing or malformed WMI environment pointer: %s\n' "$pointer" >&2
    return 1
  fi
  local environment_id
  environment_id="$(sed -n '1p' "$pointer")" || return 1
  if [[ ! "$environment_id" =~ ^[0-9a-f]{64}$ ]]; then
    printf 'invalid WMI environment id: %s\n' "$environment_id" >&2
    return 1
  fi
  local expected_environment_id
  expected_environment_id="$(peano_wmi_environment_id)" || return 1
  if [ "$environment_id" != "$expected_environment_id" ]; then
    printf 'WMI environment pointer does not match the reviewed runtime: %s != %s\n' \
      "$environment_id" "$expected_environment_id" >&2
    return 1
  fi
  local release="$PEANO_WMI_PROJECT_ROOT/.venv-wmi/releases/$environment_id"
  if [ ! -d "$release" ] || [ -L "$release" ] || [ ! -x "$release/bin/python" ]; then
    printf 'WMI environment release is unavailable: %s\n' "$release" >&2
    return 1
  fi
  printf '%s\n' "$release/bin/python"
}

peano_wmi_assert_runtime() {
  local python_path="${1:?WMI Python path required}"
  PEANO_WMI_EXPECTED_PREFIX="$(dirname "$(dirname "$python_path")")" \
    PEANO_WMI_EXPECTED_CENTRAL_PREFIX="$PEANO_WMI_CENTRAL_PREFIX" \
    "$python_path" - <<'PY'
import importlib.metadata
import math
import os
from pathlib import Path
import platform
import sys

import numpy
import accelerate
import peft
import safetensors
import sympy
import tokenizers
import torch
import transformers

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


release = Path(os.environ["PEANO_WMI_EXPECTED_PREFIX"]).resolve()
central = Path(os.environ["PEANO_WMI_EXPECTED_CENTRAL_PREFIX"]).resolve()
require(platform.machine() == "x86_64", platform.machine())
require(platform.python_version() == "3.12.12", platform.python_version())
require(Path(sys.prefix).resolve() == release, sys.prefix)
require(Path(sys.base_prefix).resolve() == central, sys.base_prefix)
require(Path(sys.executable).parent.parent == release, sys.executable)
require(torch.__version__ == "2.5.1", torch.__version__)
require(torch.version.cuda == "12.4", torch.version.cuda)
require(numpy.__version__ == "2.3.5", numpy.__version__)
require(sympy.__version__ == "1.13.1", sympy.__version__)
require(Path(torch.__file__).resolve().is_relative_to(central), torch.__file__)
require(Path(numpy.__file__).resolve().is_relative_to(central), numpy.__file__)
require(Path(sympy.__file__).resolve().is_relative_to(release), sympy.__file__)
for module in (accelerate, peft, safetensors, tokenizers, transformers):
    require(
        Path(module.__file__).resolve().is_relative_to(release),
        module.__name__,
    )

expected_overlay = {
    "accelerate": "1.8.1",
    "fsspec": "2025.5.1",
    "hf-xet": "1.1.5",
    "huggingface-hub": "0.33.4",
    "peft": "0.16.0",
    "pip": "25.2",
    "regex": "2024.11.6",
    "safetensors": "0.5.3",
    "sympy": "1.13.1",
    "tokenizers": "0.21.2",
    "tqdm": "4.67.1",
    "transformers": "4.53.3",
}
for name, version in expected_overlay.items():
    distribution = importlib.metadata.distribution(name)
    require(distribution.version == version, name)
    location = Path(distribution.locate_file("")).resolve()
    require(location.is_relative_to(release), (name, location))

require(torch.cuda.is_available(), "CUDA is unavailable")
require(torch.cuda.device_count() == 1, torch.cuda.device_count())
require(torch.cuda.is_bf16_supported(), "CUDA BF16 is unavailable")
properties = torch.cuda.get_device_properties(0)
require("A100" in properties.name, properties.name)
require(properties.total_memory >= 75 * 1024**3, properties.total_memory)
probe = torch.tensor([1.0], device="cuda", dtype=torch.bfloat16)
require(math.isfinite(float(probe.float().cpu()[0])), "non-finite CUDA probe")
print(
    {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "numpy": numpy.__version__,
        "device": properties.name,
        "total_memory": properties.total_memory,
        "bf16": torch.cuda.is_bf16_supported(),
        "environment": str(release),
    }
)
PY
}
