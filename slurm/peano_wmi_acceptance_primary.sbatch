#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=20:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v2-accept-primary
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v2-accept-primary-%j.out
#SBATCH --error=logs/peano-wmi-v2-accept-primary-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
PYTHONPYCACHEPREFIX="$(mktemp -d \
  "${SLURM_TMPDIR:-/tmp}/peano-pycache-${SLURM_JOB_ID:?}.XXXXXX")"
export PYTHONPYCACHEPREFIX
peano_wmi_activate_base
export PEANO_JOB_SCRIPT=slurm/peano_wmi_acceptance_primary.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"

"$wmi_python" scripts/peano_policy_acceptance.py run-primary \
  --adapter-dir results/peano-policy/qwen3-1.7b-lora-v2-heavy \
  --data-dir data/peano-policy-v2
