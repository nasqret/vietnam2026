#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=00:45:00
#SBATCH --job-name=peano-wmi-prepare
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-prepare-%j.out
#SBATCH --error=logs/peano-wmi-prepare-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PEANO_JOB_SCRIPT=slurm/peano_wmi_prepare_training.sbatch
mkdir -p .cache/huggingface .venv-wmi/releases logs tmp

exec 9>.venv-wmi/prepare.lock
flock -x 9
environment_id="$(peano_wmi_environment_id)" || exit 1
release="$PEANO_WMI_PROJECT_ROOT/.venv-wmi/releases/$environment_id"
release_created=false
if [ ! -d "$release" ]; then
  incoming="$PEANO_WMI_PROJECT_ROOT/.venv-wmi/incoming-${SLURM_JOB_ID:?}"
  if [ -e "$incoming" ]; then
    printf 'refusing pre-existing WMI environment stage: %s\n' "$incoming" >&2
    exit 1
  fi
  cleanup_incoming() {
    if [ -d "$incoming" ]; then
      rm -rf -- "$incoming"
    fi
  }
  trap cleanup_incoming EXIT
  unset PYTHONPATH
  python -m venv --system-site-packages "$incoming"
  export PYTHONPATH="$PEANO_WMI_PROJECT_ROOT/peano-lab/py:$PEANO_WMI_PROJECT_ROOT"
  "$incoming/bin/python" -m pip install \
    --disable-pip-version-check \
    --index-url https://pypi.org/simple \
    --only-binary=:all: \
    --no-deps \
    --require-hashes \
    --requirement "$PEANO_WMI_REQUIREMENTS_LOCK"
  "$incoming/bin/python" -m pip check
  peano_wmi_assert_runtime "$incoming/bin/python"
  mv -- "$incoming" "$release"
  trap - EXIT
  release_created=true
fi

cleanup_unaccepted_release() {
  if [ "$release_created" = true ] && [ -d "$release" ]; then
    rm -rf -- "$release"
  fi
}
trap cleanup_unaccepted_release EXIT

wmi_python="$release/bin/python"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

"$wmi_python" -m training.peano_policy.attest \
  --train data/peano-policy-v1/train.jsonl \
  --eval data/peano-policy-v1/val.jsonl \
  --output "logs/peano-wmi-dataset-attestation-${SLURM_JOB_ID}.json"
"$wmi_python" -m training.peano_policy.smoke \
  --config training/peano_policy/configs/qwen3_1_7b_wmi_smoke.toml \
  --expected-machine x86_64 \
  --minimum-cuda-capability 8.0 \
  --report-format peano-policy-wmi-a100-smoke \
  --output "logs/peano-wmi-prepare-runtime-${SLURM_JOB_ID}.json"

# Publish the pointer only after package, data, accelerator, model, LoRA, save,
# reload, and finite-loss validation have all succeeded.
pointer_stage="$(mktemp "$PEANO_WMI_PROJECT_ROOT/.venv-wmi/current.XXXXXX")"
printf '%s\n' "$environment_id" > "$pointer_stage"
mv -f -- "$pointer_stage" "$PEANO_WMI_PROJECT_ROOT/.venv-wmi/current"
release_created=false
trap - EXIT
test "$(peano_wmi_current_python)" = "$wmi_python"
