#!/bin/bash -l
# Revalidate the already-generated sealed model-v2 corpus.  This recovery job
# deliberately has no data-generation path: the timed-out generator remains
# historical provenance, while this job becomes training's checked predecessor.
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=12:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v2-finalize
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v2-finalize-%j.out
#SBATCH --error=logs/peano-wmi-v2-finalize-%j.err

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
export PEANO_JOB_SCRIPT=slurm/peano_wmi_finalize_v2_training.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

# Fail closed before any expensive model work if the preserved corpus is not
# the exact preregistered release.  The independent attestor then replays its
# provenance and every split into a job-specific immutable report.
for artifact in \
  data/peano-policy-v2/manifest.json \
  data/peano-policy-v2/source-manifest.json \
  data/peano-policy-v2/train.jsonl \
  data/peano-policy-v2/val.jsonl \
  data/peano-policy-v2/test.jsonl; do
  [ -f "$artifact" ] && [ ! -L "$artifact" ] || {
    printf 'missing regular sealed dataset artifact: %s\n' "$artifact" >&2
    exit 1
  }
done
"$wmi_python" scripts/peano_policy_acceptance.py validate >/dev/null
"$wmi_python" scripts/peano_policy_acceptance.py verify-base-snapshot \
  --phase before >/dev/null
fixed_attestation=data/peano-policy-v2/attestation.json
job_attestation="logs/peano-wmi-v2-dataset-attestation-${SLURM_JOB_ID}.json"
if [ -L "$fixed_attestation" ] || { [ -e "$fixed_attestation" ] && \
    [ ! -f "$fixed_attestation" ]; }; then
  printf 'unsafe fixed dataset attestation: %s\n' "$fixed_attestation" >&2
  exit 1
fi
if [ -e "$job_attestation" ] || [ -L "$job_attestation" ]; then
  printf 'refusing existing job dataset attestation: %s\n' \
    "$job_attestation" >&2
  exit 1
fi
if [ ! -e "$fixed_attestation" ]; then
  attestation_stage="data/peano-policy-v2/.attestation-${SLURM_JOB_ID}.json"
  [ ! -e "$attestation_stage" ] || {
    printf 'refusing existing attestation staging file: %s\n' \
      "$attestation_stage" >&2
    exit 1
  }
  "$wmi_python" -m training.peano_policy.attest \
    --train data/peano-policy-v2/train.jsonl \
    --eval data/peano-policy-v2/val.jsonl \
    --output "$attestation_stage"
  ln "$attestation_stage" "$fixed_attestation"
  ln "$attestation_stage" "$job_attestation"
  rm -f -- "$attestation_stage"
else
  "$wmi_python" -m training.peano_policy.attest \
    --train data/peano-policy-v2/train.jsonl \
    --eval data/peano-policy-v2/val.jsonl \
    --output "$job_attestation"
  cmp -s -- "$fixed_attestation" "$job_attestation" || {
    printf 'fixed and independently replayed attestations differ\n' >&2
    exit 1
  }
fi
[ -f "$fixed_attestation" ] && [ ! -L "$fixed_attestation" ] || {
  printf 'missing regular fixed dataset attestation: %s\n' \
    "$fixed_attestation" >&2
  exit 1
}
[ -f "$job_attestation" ] && [ ! -L "$job_attestation" ] || {
  printf 'missing regular job dataset attestation: %s\n' \
    "$job_attestation" >&2
  exit 1
}

"$wmi_python" -m training.peano_policy.token_audit \
  --config training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml \
  --output "logs/peano-wmi-v2-token-audit-${SLURM_JOB_ID}.json"
"$wmi_python" -m training.peano_policy.smoke \
  --config training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml \
  --expected-machine x86_64 \
  --minimum-cuda-capability 8.0 \
  --report-format peano-policy-wmi-a100-v2-smoke \
  --output "logs/peano-wmi-v2-finalize-runtime-${SLURM_JOB_ID}.json"
"$wmi_python" scripts/peano_policy_acceptance.py verify-base-snapshot \
  --phase after >/dev/null

# This fixed, atomic report is created only after attestation, tokenizer audit,
# and the real A100 optimizer smoke all pass.  Training's login-side preflight
# validates it without rescanning 100,000 rows.
"$wmi_python" scripts/peano_policy_acceptance.py audit-data \
  --data-dir data/peano-policy-v2 \
  --output logs/peano-wmi-v2-acceptance-data-pretrain.json \
  >/dev/null
