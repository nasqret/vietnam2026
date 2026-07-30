#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=12:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-qwen17-v3-base
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-qwen17-v3-base-%j.out
#SBATCH --error=logs/peano-wmi-qwen17-v3-base-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PYTHONHASHSEED=20260729
export PEANO_JOB_SCRIPT=slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
comparison=results/peano-policy/qwen3-1.7b-lora-v3-library
model_snapshot=.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1
test -f "$comparison/training-manifest.json"
test -d "$model_snapshot"
test -n "${PEANO_TRAIN_JOB_ID:?}"
nvidia-smi -L
"$wmi_python" - <<'PY'
import torch

if torch.cuda.device_count() != 1:
    raise SystemExit("pretrained baseline requires exactly one visible CUDA device")
if not torch.cuda.is_bf16_supported():
    raise SystemExit("pretrained baseline requires BF16 support")
PY

# No goal, decoder, or search option is exposed here.  The separate baseline
# entry point fixes the same four model-v3 goals, seed 20260728, depth 32, beam
# 16, eight candidates/state, 512 calls/goal, 4096 states/goal, and 256 tokens
# used by the trained-treatment evaluation.  It verifies the comparison
# adapter/tokenizer trees but loads only the pinned Qwen base weights.
"$wmi_python" scripts/eval_pretrained_peano_policy.py \
  --comparison-adapter "$comparison" \
  --output "$comparison/pretrained-base-heldout-search-wmi-b16-c8-d32.json"
