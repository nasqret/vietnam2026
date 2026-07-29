#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=20:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-qwen17-v3
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-qwen17-v3-%j.out
#SBATCH --error=logs/peano-wmi-qwen17-v3-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PYTHONHASHSEED=20260729
export PEANO_JOB_SCRIPT=slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
test -f data/peano-policy-v3/manifest.json
test -f "logs/peano-wmi-v3-dataset-attestation-${PEANO_PREPARE_JOB_ID:?}.json"
test -f "logs/peano-wmi-v3-token-audit-${PEANO_PREPARE_JOB_ID}.json"
nvidia-smi -L

# WMI's managed Torch 2.5.1 cannot safely reload Trainer optimizer pickles.
# This is therefore one attested, offline, fresh-output training run.
"$wmi_python" -m training.peano_policy.train \
  --config training/peano_policy/configs/qwen3_1_7b_v3_library.toml \
  --resume-from-checkpoint NEVER
