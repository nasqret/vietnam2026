#!/bin/bash -l
#SBATCH --account=bnaskrecki
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=00:20:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-v3-showcase
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-v3-showcase-%j.out
#SBATCH --error=logs/peano-v3-showcase-%j.err

# Deterministic, diagnostic-only held-out rollout over the bounded morning
# adapter.  The evaluator executes every proposed tactic in Peano Lab and only
# records ``proof`` after the original target's explicit certificate passes the
# kernel checker.
set -euo pipefail

readonly main_root=/work/bnaskrecki/peano-lab-training
readonly adapter="$main_root/results/peano-policy/diagnostics/qwen3-1.7b-lora-v3-morning-diagnostic-20260731-r1"
readonly report="${SLURM_SUBMIT_DIR:?}/results/peano-policy/showcase/morning-rollout-${SLURM_JOB_ID:?}.json"
readonly expected_manifest_sha256=68d3ba2bfe080d83995bdd59eb3eb516a22d268276f78b17350c262d5ff22302
readonly expected_probe_sha256=6f745a13c0fceab4aff4ac2292e8b8fdec597c9a96b1b3aae4e1981e0af6937d
readonly expected_adapter_sha256=817e4f4bf8edb9d47511533c6ef1a9810aa9f0f2353fd4de57af97c82e632324

# Prevent source or adapter publication from changing underneath evaluation.
exec 7>"$SLURM_SUBMIT_DIR/.deployment.lock"
if ! flock -n -s 7; then
  printf 'diagnostic source deployment is active; refusing showcase run\n' >&2
  exit 1
fi
exec 8>"$main_root/.deployment.lock"
if ! flock -n -s 8; then
  printf 'main Peano deployment is active; refusing showcase run\n' >&2
  exit 1
fi

peano_wmi_job_env="$SLURM_SUBMIT_DIR/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PYTHONHASHSEED=20260731
export PEANO_JOB_SCRIPT=slurm/peano_wmi_eval_v3_morning_showcase.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

require_hash() {
  local expected="${1:?expected SHA-256 required}"
  local path="${2:?artifact path required}"
  test -f "$path"
  test ! -L "$path"
  local observed
  observed="$(sha256sum "$path" | awk '{print $1}')"
  if [ "$observed" != "$expected" ]; then
    printf 'showcase input changed: %s != %s for %s\n' \
      "$observed" "$expected" "$path" >&2
    exit 1
  fi
}

require_hash "$expected_manifest_sha256" "$adapter/training-manifest.json"
require_hash "$expected_probe_sha256" "$adapter/morning-reload-probe.json"
require_hash "$expected_adapter_sha256" "$adapter/adapter/adapter_model.safetensors"
test -f "$adapter/morning-diagnostic.json"
test ! -L "$adapter/morning-diagnostic.json"
mkdir -p "$(dirname "$report")"
if [ -e "$report" ]; then
  printf 'refusing to replace showcase report: %s\n' "$report" >&2
  exit 1
fi

"$wmi_python" scripts/eval_trained_peano_policy.py \
  --adapter "$adapter" \
  --diagnostic \
  --mode rollout \
  --goal closed_arithmetic_seven \
  --goal double_right_zero \
  --k 1 \
  --max-steps 4 \
  --max-new-tokens 64 \
  --seed 20260731 \
  --output "$report"

test -s "$report"
printf 'MORNING_SHOWCASE_REPORT=%s\n' "$report"
