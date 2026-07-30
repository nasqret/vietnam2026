#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=36:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-qwen17-v3
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-qwen17-v3-%j.out
#SBATCH --error=logs/peano-wmi-qwen17-v3-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
exec 9>/work/bnaskrecki/peano-lab-training/.qwen3-1.7b-v3-training.lock
if ! flock -n 9; then
  printf 'another Qwen3-1.7B model-v3 training job owns the output lock\n' >&2
  exit 1
fi
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
prepare_job_id="${PEANO_PREPARE_JOB_ID:?PEANO_PREPARE_JOB_ID is not defined}"
eligibility_report="logs/peano-wmi-v3-sealed-eligibility-${prepare_job_id}.json"
token_report="logs/peano-wmi-v3-token-audit-${prepare_job_id}.json"
smoke_report="logs/peano-wmi-v3-prepare-runtime-${prepare_job_id}.json"
recovery_probe_root="results/peano-policy/recovery-publication-preflights"
recovery_preflight_report="logs/peano-wmi-recovery-publication-preflight-${SLURM_JOB_ID:?}.json"
"$wmi_python" scripts/verify_wmi_v3_sealed_preparation.py \
  --eligibility-report "$eligibility_report" \
  --token-audit-report "$token_report" \
  --smoke-report "$smoke_report" \
  --prepare-job-id "$prepare_job_id"
mkdir -p "$recovery_probe_root"
if [ -e "$recovery_preflight_report" ]; then
  printf 'refusing to replace recovery publication preflight: %s\n' "$recovery_preflight_report" >&2
  exit 1
fi
"$wmi_python" scripts/preflight_recovery_publication.py run \
  --probe-root "$recovery_probe_root" \
  --report "$recovery_preflight_report"
"$wmi_python" scripts/preflight_recovery_publication.py verify \
  --report "$recovery_preflight_report"
nvidia-smi -L

# WMI's managed Torch 2.5.1 cannot safely reload Trainer optimizer pickles.
# This is therefore one attested, offline, fresh-output training run.
"$wmi_python" -m training.peano_policy.train \
  --config training/peano_policy/configs/qwen3_1_7b_v3_library.toml \
  --preparation-eligibility-report "$eligibility_report" \
  --preparation-token-audit-report "$token_report" \
  --preparation-runtime-smoke-report "$smoke_report" \
  --prepare-job-id "$prepare_job_id" \
  --recovery-publication-preflight-report "$recovery_preflight_report" \
  --resume-from-checkpoint NEVER
