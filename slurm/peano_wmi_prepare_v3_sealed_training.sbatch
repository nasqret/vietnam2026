#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=08:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v3-sealprep
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v3-sealprep-%j.out
#SBATCH --error=logs/peano-wmi-v3-sealprep-%j.err

# Reuse the immutable corpus produced by the historical full-replay job.  This
# current-source gate performs no theorem generation and no proof replay.  It
# verifies the entire seal and current compiler/kernel inventory, audits every
# selected row with the pinned tokenizer, and exercises both the longest
# sequence and longest supervised completion (one row if they coincide, two
# otherwise) through indexed-logit A100 LoRA optimizer/save/reload probes.
# Eligibility, token audit, and smoke each reverify the seal independently;
# the eight-hour bound includes those three full artifact scans rather than
# sharing mutable in-process trust between gates.
set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PYTHONHASHSEED=20260729
export PEANO_JOB_SCRIPT=slurm/peano_wmi_prepare_v3_sealed_training.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
test "$(peano_wmi_current_python)" = "$wmi_python"
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

config=training/peano_policy/configs/qwen3_1_7b_v3_library.toml
model_snapshot=".cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
eligibility_report="logs/peano-wmi-v3-sealed-eligibility-${SLURM_JOB_ID:?}.json"
token_report="logs/peano-wmi-v3-token-audit-${SLURM_JOB_ID}.json"
smoke_report="logs/peano-wmi-v3-prepare-runtime-${SLURM_JOB_ID}.json"
test -f "$config"
test -d "$model_snapshot"
mkdir -p logs tmp
for report in "$eligibility_report" "$token_report" "$smoke_report"; do
  if [ -e "$report" ]; then
    printf 'refusing to replace WMI v3 preparation report: %s\n' "$report" >&2
    exit 1
  fi
done

# This first, model-free check is intentionally separate so an incompatible or
# mutated seal fails before the tokenizer scan or GPU model load.
"$wmi_python" scripts/verify_peano_v3_corpus_eligibility.py \
  --config "$config" \
  --output "$eligibility_report"

"$wmi_python" -m training.peano_policy.token_audit \
  --config "$config" \
  --output "$token_report"

"$wmi_python" -m training.peano_policy.smoke \
  --config "$config" \
  --expected-machine x86_64 \
  --minimum-cuda-capability 8.0 \
  --report-format peano-policy-wmi-a100-v3-smoke \
  --output "$smoke_report"

# Cross-check the three reports while the same source lock is still held.  The
# dependent training job repeats this verification immediately before loading
# the model.
"$wmi_python" scripts/verify_wmi_v3_sealed_preparation.py \
  --eligibility-report "$eligibility_report" \
  --token-audit-report "$token_report" \
  --smoke-report "$smoke_report" \
  --prepare-job-id "$SLURM_JOB_ID"
