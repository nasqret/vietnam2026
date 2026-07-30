#!/usr/bin/env bash
# Build the native macOS inference environment and cache the pinned Qwen base.

set -euo pipefail

readonly repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly lock="$repository_root/training/peano_policy/requirements-macos-arm64.lock"
readonly environment_parent="$repository_root/.venv"
readonly environment="$environment_parent/peano-model-macos"
readonly cache_parent="$repository_root/.cache"
readonly hf_home="$cache_parent/huggingface"
readonly minimum_free_kib=$((6 * 1024 * 1024))

if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  printf 'this bootstrap requires native arm64 macOS\n' >&2
  exit 1
fi
if [ ! -f "$lock" ] || [ -L "$lock" ]; then
  printf 'missing or unsafe macOS package lock: %s\n' "$lock" >&2
  exit 1
fi
available_kib="$(df -Pk "$repository_root" | awk 'NR == 2 {print $4}')"
if ! [[ "$available_kib" =~ ^[0-9]+$ ]] || [ "$available_kib" -lt "$minimum_free_kib" ]; then
  printf 'at least 6 GiB of free disk is required before bootstrap\n' >&2
  exit 1
fi

bootstrap_python="${PEANO_MACOS_BOOTSTRAP_PYTHON:-}"
if [ -z "$bootstrap_python" ]; then
  if [ -x /opt/homebrew/Caskroom/miniconda/base/bin/python ]; then
    bootstrap_python=/opt/homebrew/Caskroom/miniconda/base/bin/python
  elif command -v python3.12 >/dev/null 2>&1; then
    bootstrap_python="$(command -v python3.12)"
  else
    printf 'native CPython 3.12 is required (Miniconda or python3.12)\n' >&2
    exit 1
  fi
fi
if [ ! -x "$bootstrap_python" ]; then
  printf 'bootstrap Python is not executable: %s\n' "$bootstrap_python" >&2
  exit 1
fi
"$bootstrap_python" - <<'PY'
import platform
import sys
if platform.machine() != "arm64" or sys.version_info[:2] != (3, 12):
    raise SystemExit(
        f"bootstrap requires arm64 CPython 3.12, got {platform.machine()} "
        f"{platform.python_version()}"
    )
PY

if [ -L "$environment_parent" ] || [ -L "$environment" ]; then
  printf 'refusing symlinked local environment path\n' >&2
  exit 1
fi
mkdir -p "$environment_parent"
if [ ! -x "$environment/bin/python" ]; then
  if [ -e "$environment" ]; then
    printf 'existing local environment is incomplete: %s\n' "$environment" >&2
    exit 1
  fi
  "$bootstrap_python" -m venv "$environment"
fi
readonly peano_python="$environment/bin/python"
export PYTHONNOUSERSITE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
"$peano_python" -m pip install \
  --only-binary=:all: \
  --require-hashes \
  --requirement "$lock"
"$peano_python" -m pip check

# This must be run from a normal Terminal.  Sandboxes which deny sysctl can
# make PyTorch report a false-negative MPS availability result.
"$peano_python" - <<'PY'
import importlib.metadata
import platform
import torch
import torch.nn.functional as functional

expected = {
    "accelerate": "1.8.1",
    "huggingface-hub": "0.33.4",
    "peft": "0.16.0",
    "safetensors": "0.5.3",
    "tokenizers": "0.21.2",
    "torch": "2.8.0",
    "transformers": "4.53.3",
}
if platform.machine() != "arm64":
    raise SystemExit(f"local environment is not native arm64: {platform.machine()}")
for name, version in expected.items():
    observed = importlib.metadata.version(name)
    if observed != version:
        raise SystemExit(f"package mismatch for {name}: {observed} != {version}")
if not torch.backends.mps.is_built() or not torch.backends.mps.is_available():
    raise SystemExit("PyTorch MPS is unavailable; run this bootstrap outside a sandbox")
query = torch.randn((1, 2, 32, 64), device="mps", dtype=torch.bfloat16)
result = functional.scaled_dot_product_attention(
    query, query, query, is_causal=True
)
torch.mps.synchronize()
if result.dtype != torch.bfloat16 or not torch.isfinite(result.float()).all():
    raise SystemExit("MPS BF16 causal-attention probe failed")
print("MPS BF16 causal-attention probe passed")
PY

for directory in "$cache_parent" "$hf_home"; do
  if [ -L "$directory" ]; then
    printf 'refusing symlinked Hugging Face cache path: %s\n' "$directory" >&2
    exit 1
  fi
  mkdir -p "$directory"
done
export HF_HOME="$hf_home"
export HF_HUB_DISABLE_TELEMETRY=1
export HF_XET_HIGH_PERFORMANCE=1
export DO_NOT_TRACK=1
"$peano_python" "$repository_root/scripts/prefetch_peano_base_model.py"
# Exercise the same strict path with no network-capable API call.
"$peano_python" \
  "$repository_root/scripts/prefetch_peano_base_model.py" \
  --verify-only

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
printf 'PEANO_MODEL_PYTHON=%s\n' "$peano_python"
printf 'PEANO_HF_HOME=%s\n' "$HF_HOME"
printf 'Bootstrap complete. Transfer the adapter with:\n  %s/scripts/sync_peano_morning_adapter.sh\n' "$repository_root"
