#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=12:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v3-prepare
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v3-prepare-%j.out
#SBATCH --error=logs/peano-wmi-v3-prepare-%j.err

# Complete preparation of the already-built model-v3 corpus.  Historical job
# 172729 finished all twelve corpus artifacts but its independent attestor
# could not fit a second five-hour replay plus the tokenizer/GPU gates into the
# original twelve-hour allocation.  This job accepts only that exact manifest,
# independently replays it from the same compiler snapshot, audits every row
# against Qwen's 32768-token hard limit, and finishes with the reviewed A100
# LoRA save/reload smoke.  It never regenerates or rewrites corpus data.
set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PYTHONHASHSEED=20260729
export PEANO_JOB_SCRIPT=slurm/peano_wmi_prepare_v3_training.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
test "$(peano_wmi_current_python)" = "$wmi_python"
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

config=training/peano_policy/configs/qwen3_1_7b_v3_library.toml
data_dir=data/peano-policy-v3
model_snapshot=".cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
test -f "$config"
test -d "$model_snapshot"
if [ -L "$data_dir" ]; then
  printf 'refusing symlinked WMI v3 data directory: %s\n' "$data_dir" >&2
  exit 1
fi
if [ -e "$data_dir" ] && [ ! -d "$data_dir" ]; then
  printf 'refusing non-directory WMI v3 data path: %s\n' "$data_dir" >&2
  exit 1
fi
mkdir -p logs

"$wmi_python" - "$config" <<'PY'
from pathlib import Path
import sys

from training.peano_policy.config import load_config

config = load_config(Path(sys.argv[1]))
if config.data.max_length != 32768:
    raise SystemExit("model-v3 training must retain Qwen's 32768-token limit")
if config.model.model_id != "Qwen/Qwen3-1.7B-Base":
    raise SystemExit("model-v3 preparation received the wrong base model")
if config.model.revision != "ea980cb0a6c2ae4b936e82123acc929f1cec04c1":
    raise SystemExit("model-v3 preparation received an unreviewed model revision")
PY

# Fail closed unless this is the exact closed artifact set produced by 172729.
# The attestor below then checks all embedded source/compiler hashes and
# reproduces train/val/test byte-for-byte in a private temporary directory.
expected_manifest_sha256=ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983
expected_files=(
  balanced-raw-traces.jsonl
  balanced-session-metadata.jsonl
  balanced-source-manifest.json
  combined-metadata-manifest.json
  library-raw-traces.jsonl
  library-session-metadata.jsonl
  library-source-manifest.json
  manifest.json
  session-metadata.jsonl
  test.jsonl
  train.jsonl
  val.jsonl
)
test -d "$data_dir"
test ! -L "$data_dir"
mapfile -t observed_files < <(
  find "$data_dir" -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort
)
if [ "${#observed_files[@]}" -ne "${#expected_files[@]}" ]; then
  printf 'model-v3 corpus is not closed: expected %s files, found %s\n' \
    "${#expected_files[@]}" "${#observed_files[@]}" >&2
  exit 1
fi
for index in "${!expected_files[@]}"; do
  expected="${expected_files[$index]}"
  if [ "${observed_files[$index]}" != "$expected" ]; then
    printf 'model-v3 corpus entry mismatch at %s: expected %s, found %s\n' \
      "$index" "$expected" "${observed_files[$index]}" >&2
    exit 1
  fi
  test -f "$data_dir/$expected"
  test ! -L "$data_dir/$expected"
done
test "$(sha256sum "$data_dir/manifest.json" | awk '{print $1}')" = \
  "$expected_manifest_sha256"

attestation_report="logs/peano-wmi-v3-dataset-attestation-${SLURM_JOB_ID:?}.json"
token_report="logs/peano-wmi-v3-token-audit-${SLURM_JOB_ID}.json"
smoke_report="logs/peano-wmi-v3-prepare-runtime-${SLURM_JOB_ID}.json"
for report in "$attestation_report" "$token_report" "$smoke_report"; do
  test ! -e "$report"
  test ! -L "$report"
done

"$wmi_python" -m training.peano_policy.attest \
  --train "$data_dir/train.jsonl" \
  --eval "$data_dir/val.jsonl" \
  --output "$attestation_report"

"$wmi_python" -m training.peano_policy.token_audit \
  --config "$config" \
  --output "$token_report"

"$wmi_python" -m training.peano_policy.smoke \
  --config "$config" \
  --expected-machine x86_64 \
  --minimum-cuda-capability 8.0 \
  --report-format peano-policy-wmi-a100-v3-smoke \
  --output "$smoke_report"
