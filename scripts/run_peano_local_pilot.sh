#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_python="/Users/bnaskrecki/codex/bielik/.venv/bin/python"
ml_python="${PEANO_ML_PYTHON:-${default_python}}"

if [[ ! -x "${ml_python}" ]]; then
  echo "Peano ML Python is not executable: ${ml_python}" >&2
  echo "Set PEANO_ML_PYTHON to the Python with torch, transformers, and peft." >&2
  exit 2
fi

export PYTHONHASHSEED="${PYTHONHASHSEED:-20260729}"
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

exec "${ml_python}" "${repository_root}/scripts/peano_local_pilot.py" \
  --device mps \
  --max-new-tokens 16 \
  --depth 8 \
  --beam 4 \
  --candidates 4 \
  --model-calls 16 \
  --states 256 \
  "$@"
