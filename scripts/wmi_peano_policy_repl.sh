#!/usr/bin/env bash
# Open one guarded WMI A100 allocation and keep the trained policy loaded.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

readonly repl_job_name="peano-wmi-repl"
readonly repl_adapter="results/peano-policy/qwen3-1.7b-lora-v2-heavy"

usage() {
  printf 'usage: %s [--test-only]\n' "$0" >&2
  printf '       %s --connect --confirm %s\n' \
    "$0" "$PEANO_WMI_CONFIRM_TOKEN" >&2
}

remote_run() {
  if [ -z "${SSH_CONNECTION:-}" ]; then
    printf '%s\n' '--remote-run is reserved for the fixed SSH hop' >&2
    exit 2
  fi
  cd "$PEANO_WMI_PROJECT_ROOT"
  if [ ! -d "$repl_adapter" ] || [ -L "$repl_adapter" ]; then
    printf 'trained model-v2 adapter is unavailable: %s/%s\n' \
      "$PEANO_WMI_PROJECT_ROOT" "$repl_adapter" >&2
    exit 1
  fi
  active="$(squeue -h --me --name "$repl_job_name" -o '%A')"
  if [ -n "$active" ]; then
    printf 'a WMI Peano REPL allocation already exists: %s\n' "$active" >&2
    exit 1
  fi

  # The command body is a literal: theorem text is entered only after the
  # model is loaded, through the Python REPL's validated input boundary.
  exec srun \
    --partition=gpu_csi \
    --nodes=1 \
    --ntasks=1 \
    --cpus-per-task=8 \
    --mem=64G \
    --gpus=nvidia_a100:1 \
    --constraint=vram80g \
    --time=04:00:00 \
    --hint=nomultithread \
    --job-name="$repl_job_name" \
    --chdir="$PEANO_WMI_PROJECT_ROOT" \
    --pty \
    bash -l -c '
set -euo pipefail
readonly project_root=/work/bnaskrecki/peano-lab-training
cd "$project_root"
exec 8>"$project_root/.deployment.lock"
flock -s 8
export SLURM_SUBMIT_DIR="$project_root"
readonly environment_helper="$project_root/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$environment_helper" | awk '\''{print $1}'\'')"
source "$environment_helper"
peano_wmi_activate_base
readonly wmi_python="$(peano_wmi_current_python)"
peano_wmi_assert_runtime "$wmi_python"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PEANO_JOB_SCRIPT=scripts/wmi_peano_policy_repl.sh
exec "$wmi_python" scripts/peano_policy_repl.py \
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
    ssh_target="$(peano_wmi_ssh_target)"
    printf '%s\n' 'WMI Peano policy REPL: dry run (no SSH, no allocation)'
    printf 'host=%s\n' "$ssh_target"
    printf 'project=%s\n' "$PEANO_WMI_PROJECT_ROOT"
    printf '%s\n' \
      'partition=gpu_csi gpu=nvidia_a100:1 constraint=vram80g time=04:00:00'
    printf 'adapter=%s\n' "$repl_adapter"
    ;;
  --connect)
    if [ "$#" -ne 3 ] || [ "$2" != --confirm ] || \
       [ "$3" != "$PEANO_WMI_CONFIRM_TOKEN" ]; then
      printf 'real WMI allocation requires: --connect --confirm %s\n' \
        "$PEANO_WMI_CONFIRM_TOKEN" >&2
      exit 2
    fi
    ssh_target="$(peano_wmi_ssh_target)"
    # The target passes a conservative validator and the remote command has no
    # interpolated user input.  -tt preserves stdin for the formula prompt.
    exec ssh -tt -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
      "cd $PEANO_WMI_PROJECT_ROOT && exec ./scripts/wmi_peano_policy_repl.sh --remote-run"
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
