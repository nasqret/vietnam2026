#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=04:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v2-prepare
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v2-prepare-%j.out
#SBATCH --error=logs/peano-wmi-v2-prepare-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PEANO_JOB_SCRIPT=slurm/peano_wmi_prepare_v2_training.sbatch
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

make \
  PEANO_CORPUS_PYTHON="$wmi_python" \
  PEANO_POLICY_DIR=data/peano-policy-v2 \
  PEANO_POLICY_ROWS=100000 \
  peano-policy-v2-data

"$wmi_python" -m training.peano_policy.attest \
  --train data/peano-policy-v2/train.jsonl \
  --eval data/peano-policy-v2/val.jsonl \
  --output "logs/peano-wmi-v2-dataset-attestation-${SLURM_JOB_ID}.json"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
"$wmi_python" -m training.peano_policy.token_audit \
  --config training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml \
  --output "logs/peano-wmi-v2-token-audit-${SLURM_JOB_ID}.json"
"$wmi_python" -m training.peano_policy.smoke \
  --config training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml \
  --expected-machine x86_64 \
  --minimum-cuda-capability 8.0 \
  --report-format peano-policy-wmi-a100-v2-smoke \
  --output "logs/peano-wmi-v2-prepare-runtime-${SLURM_JOB_ID}.json"
