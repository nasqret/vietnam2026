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

# Build both checked model-v3 corpora, replay the exact split, independently
# attest it, audit every selected example against Qwen's 32768-token hard limit,
# and finish with the reviewed one-batch A100 LoRA save/reload smoke.
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
mkdir -p "$data_dir" logs

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

"$wmi_python" scripts/generate_peano_library_policy_corpus.py \
  --trace-output "$data_dir/library-raw-traces.jsonl" \
  --metadata-output "$data_dir/library-session-metadata.jsonl" \
  --manifest "$data_dir/library-source-manifest.json"

"$wmi_python" scripts/generate_peano_v3_balanced_corpus.py \
  --profile model-v3 \
  --trace-output "$data_dir/balanced-raw-traces.jsonl" \
  --metadata-output "$data_dir/balanced-session-metadata.jsonl" \
  --manifest "$data_dir/balanced-source-manifest.json" \
  --row-budget 70000 \
  --budget-mode exact \
  --seed peano-policy-v3-balanced-wmi-20260729

combined_metadata="$data_dir/session-metadata.jsonl"
"$wmi_python" scripts/combine_peano_v3_corpus_metadata.py \
  --library-metadata "$data_dir/library-session-metadata.jsonl" \
  --synthetic-metadata "$data_dir/balanced-session-metadata.jsonl" \
  --output "$combined_metadata" \
  --manifest "$data_dir/combined-metadata-manifest.json"

"$wmi_python" scripts/build_peano_policy_dataset.py \
  "$data_dir/library-raw-traces.jsonl" \
  "$data_dir/balanced-raw-traces.jsonl" \
  --metadata "$combined_metadata" \
  --output-dir "$data_dir" \
  --seed peano-policy-v3

"$wmi_python" -m training.peano_policy.attest \
  --train "$data_dir/train.jsonl" \
  --eval "$data_dir/val.jsonl" \
  --output "logs/peano-wmi-v3-dataset-attestation-${SLURM_JOB_ID:?}.json"

"$wmi_python" -m training.peano_policy.token_audit \
  --config "$config" \
  --output "logs/peano-wmi-v3-token-audit-${SLURM_JOB_ID}.json"

"$wmi_python" -m training.peano_policy.smoke \
  --config "$config" \
  --expected-machine x86_64 \
  --minimum-cuda-capability 8.0 \
  --report-format peano-policy-wmi-a100-v3-smoke \
  --output "logs/peano-wmi-v3-prepare-runtime-${SLURM_JOB_ID}.json"
