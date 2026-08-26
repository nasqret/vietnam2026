#!/usr/bin/env bash
# Invoke the WMI-side guarded submission tool. Test-only is the default.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

usage() {
  echo "usage: $0 [--test-only] [--afterok JOB_ID | --completed-predecessor JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
  echo "       $0 --submit --confirm $PEANO_WMI_CONFIRM_TOKEN [--afterok JOB_ID | --completed-predecessor JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
}

mode=--test-only
confirmation=""
predecessor_job_id=""
predecessor_mode=""
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
      [ -z "$predecessor_job_id" ] || { echo "only one predecessor option is allowed" >&2; exit 2; }
      predecessor_job_id="$2"; predecessor_mode=afterok; shift 2
      ;;
    --completed-predecessor)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$predecessor_job_id" ] || { echo "only one predecessor option is allowed" >&2; exit 2; }
      predecessor_job_id="$2"; predecessor_mode=completed; shift 2
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
[ -z "$predecessor_job_id" ] || peano_wmi_validate_single_job_id "$predecessor_job_id" || {
  printf 'invalid predecessor job id: %s\n' "$predecessor_job_id" >&2
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
  [ -n "$predecessor_job_id" ] || { echo "WMI train/eval requires a predecessor job" >&2; exit 2; }
  peano_wmi_validate_predecessor_mode "$job_script" "$predecessor_mode" || {
    echo "WMI training requires --completed-predecessor; evaluation accepts it or --afterok" >&2
    exit 2
  }
elif [ -n "$predecessor_job_id" ]; then
  echo "this WMI job must not have a predecessor" >&2
  exit 2
fi

ssh_target="$(peano_wmi_ssh_target)"
remote_args=("$mode")
[ "$mode" = --test-only ] || remote_args+=(--confirm "$confirmation")
if [ "$predecessor_mode" = afterok ]; then
  remote_args+=(--afterok "$predecessor_job_id")
elif [ "$predecessor_mode" = completed ]; then
  remote_args+=(--completed-predecessor "$predecessor_job_id")
fi
[ -z "$request_id" ] || remote_args+=(--request-id "$request_id")
remote_args+=("$job_script")

# Every argument has been restricted to a conservative allowlist or digits.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "cd $PEANO_WMI_PROJECT_ROOT && exec ./scripts/submit_wmi_slurm_job.sh ${remote_args[*]}"
