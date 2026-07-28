#!/usr/bin/env bash
# Invoke the WMI-side guarded submission tool. Test-only is the default.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

usage() {
  echo "usage: $0 [--test-only] [--afterok JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
  echo "       $0 --submit --confirm $PEANO_WMI_CONFIRM_TOKEN [--afterok JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
}

mode=--test-only
confirmation=""
afterok=""
request_id=""
job_script=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=--test-only; shift ;;
    --submit) mode=--submit; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      confirmation="$2"; shift 2
      ;;
    --afterok)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$afterok" ] || { echo "--afterok may appear only once" >&2; exit 2; }
      afterok="$2"; shift 2
      ;;
    --request-id)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$request_id" ] || { echo "--request-id may appear only once" >&2; exit 2; }
      request_id="$2"; shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    --*) printf 'unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
    *)
      [ -z "$job_script" ] || { echo "only one job script is allowed" >&2; exit 2; }
      job_script="$1"; shift
      ;;
  esac
done

[ -n "$job_script" ] || { usage; exit 2; }
peano_wmi_validate_script_name "$job_script"
[ -z "$request_id" ] || peano_wmi_validate_request_id "$request_id" || {
  printf 'invalid --request-id: %s\n' "$request_id" >&2
  exit 2
}
if [ "$job_script" = slurm/peano_wmi_prove_theorem.sbatch ]; then
  [ -n "$request_id" ] || { echo "WMI theorem proof requires --request-id" >&2; exit 2; }
elif [ -n "$request_id" ]; then
  echo "--request-id is valid only for the WMI theorem-proof job" >&2
  exit 2
fi
[ -z "$afterok" ] || peano_wmi_validate_single_job_id "$afterok" || {
  printf 'invalid --afterok job id: %s\n' "$afterok" >&2
  exit 2
}
if [ "$mode" = --test-only ] && [ -n "$confirmation" ]; then
  echo "--confirm is only valid with --submit" >&2
  exit 2
fi
if [ "$mode" = --submit ] && [ "$confirmation" != "$PEANO_WMI_CONFIRM_TOKEN" ]; then
  echo "real WMI submission requires: --submit --confirm $PEANO_WMI_CONFIRM_TOKEN" >&2
  exit 2
fi
if peano_wmi_expected_predecessor "$job_script" >/dev/null; then
  [ -n "$afterok" ] || { echo "WMI train/eval requires --afterok JOB_ID" >&2; exit 2; }
elif [ -n "$afterok" ]; then
  echo "this WMI job must not have a dependency" >&2
  exit 2
fi

ssh_target="$(peano_wmi_ssh_target)"
remote_args=("$mode")
[ "$mode" = --test-only ] || remote_args+=(--confirm "$confirmation")
[ -z "$afterok" ] || remote_args+=(--afterok "$afterok")
[ -z "$request_id" ] || remote_args+=(--request-id "$request_id")
remote_args+=("$job_script")

# Every argument has been restricted to a conservative allowlist or digits.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "cd $PEANO_WMI_PROJECT_ROOT && exec ./scripts/submit_wmi_slurm_job.sh ${remote_args[*]}"
