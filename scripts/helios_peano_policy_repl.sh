#!/usr/bin/env bash
# Open one guarded Helios GH200 allocation and keep the trained policy loaded.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

readonly repl_job_name="peano-helios-repl"
readonly repl_adapter="results/peano-policy/qwen3-1.7b-lora-v2-heavy"

usage() {
  printf 'usage: %s [--test-only]\n' "$0" >&2
  printf '       %s --connect --confirm %s\n' \
    "$0" "$PEANO_HELIOS_CONFIRM_TOKEN" >&2
}

remote_run() {
  if [ -z "${SSH_CONNECTION:-}" ]; then
    printf '%s\n' '--remote-run is reserved for the fixed SSH hop' >&2
    exit 2
  fi
  readonly project_root="${SCRATCH:?SCRATCH is not defined}/$PEANO_HELIOS_PROJECT_SUFFIX"
  cd "$project_root"
  if [ ! -d "$repl_adapter" ] || [ -L "$repl_adapter" ] || \
     [ ! -f "$repl_adapter/training-manifest.json" ] || \
     [ -L "$repl_adapter/training-manifest.json" ]; then
    printf 'trained model-v2 adapter is unavailable: %s/%s\n' \
      "$project_root" "$repl_adapter" >&2
    exit 1
  fi
  active="$(squeue -h --me --name "$repl_job_name" -o '%A')"
  if [ -n "$active" ]; then
    printf 'a Helios Peano REPL allocation already exists: %s\n' \
      "$active" >&2
    exit 1
  fi

  # This command body is fixed. Theorem text arrives only after Python has
  # loaded the adapter, through the REPL's validated standard-input boundary.
  exec srun \
    --account="$PEANO_HELIOS_GPU_ACCOUNT" \
    --partition=plgrid-gpu-gh200 \
    --nodes=1 \
    --ntasks=1 \
    --cpus-per-task=8 \
    --mem=64G \
    --gres=gpu:1 \
    --time=04:00:00 \
    --job-name="$repl_job_name" \
    --chdir="$project_root" \
    --pty \
    bash -l -c '
set -euo pipefail
readonly project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
cd "$project_root"
exec 8>"$project_root/.deployment.lock"
flock -s 8
module purge
unset PEANO_ML_MODULE PEANO_CLUSTER_BACKEND PEANO_BASE_ENV PEANO_REQUIREMENTS_LOCK
unset PEANO_BASE_MANIFEST PEANO_JOB_ENV_SCRIPT PEANO_JOB_ENV_SHA256
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"
test -x .venv-helios/bin/python
export SLURM_SUBMIT_DIR="$project_root"
export PYTHONHASHSEED=20260728
export PYTHONNOUSERSITE=1
export PYTHONPATH="$project_root/peano-lab/py:$project_root"
export HF_HOME="$project_root/.cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=scripts/helios_peano_policy_repl.sh
exec .venv-helios/bin/python scripts/peano_policy_repl.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-v2-heavy \
  --results-dir results/peano-policy/interactive \
  --depth 32 \
  --beam 4 \
  --candidates 4 \
  --model-calls 128 \
  --states 2048
'
}

mode="${1:---test-only}"
case "$mode" in
  --help|-h)
    [ "$#" -eq 1 ] || { usage; exit 2; }
    usage
    exit 0
    ;;
  --test-only)
    [ "$#" -le 1 ] || { usage; exit 2; }
    ssh_target="$(peano_helios_ssh_target)"
    printf '%s\n' 'Helios Peano policy REPL: dry run (no SSH, no allocation)'
    printf 'host=%s\n' "$ssh_target"
    printf 'project=$SCRATCH/%s\n' "$PEANO_HELIOS_PROJECT_SUFFIX"
    printf '%s\n' \
      'account=plgccaiautore2026-gpu-gh200 partition=plgrid-gpu-gh200 gpu=gh200:1 time=04:00:00'
    printf 'adapter=%s\n' "$repl_adapter"
    ;;
  --connect)
    if [ "$#" -ne 3 ] || [ "$2" != --confirm ] || \
       [ "$3" != "$PEANO_HELIOS_CONFIRM_TOKEN" ]; then
      printf 'real Helios allocation requires: --connect --confirm %s\n' \
        "$PEANO_HELIOS_CONFIRM_TOKEN" >&2
      exit 2
    fi
    ssh_target="$(peano_helios_ssh_target)"
    # The target is conservatively validated. -tt carries stdin from this
    # terminal to the fixed Python formula prompt on the allocated node.
    exec ssh -tt -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
      "bash -l -c 'cd \"\${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training\" && exec ./scripts/helios_peano_policy_repl.sh --remote-run'"
    ;;
  --remote-run)
    [ "$#" -eq 1 ] || { usage; exit 2; }
    remote_run
    ;;
  *)
    printf 'unknown option: %s\n' "$mode" >&2
    usage
    exit 2
    ;;
esac
