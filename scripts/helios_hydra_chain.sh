#!/usr/bin/env bash
# Queue dependencies immediately: Helios can forget finished jobs in seconds.
# The existing remote submitter remains the authority for every allocation.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

usage() {
  printf 'usage: %s [--test-only]\n' "$0" >&2
  printf '       %s --submit --confirm %s\n' "$0" "$PEANO_HELIOS_CONFIRM_TOKEN" >&2
}

mode="--test-only"
mode_set=false
confirmation=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only|--submit)
      [ "$mode_set" = false ] || { usage; exit 2; }
      mode="$1"
      mode_set=true
      shift
      ;;
    --confirm)
      [ "$#" -ge 2 ] && [ -z "$confirmation" ] || { usage; exit 2; }
      confirmation="$2"
      shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done
if [ "$mode" = "--test-only" ] && [ -n "$confirmation" ]; then
  printf '%s\n' '--confirm is only valid with --submit' >&2
  exit 2
fi
if [ "$mode" = "--submit" ] && [ "$confirmation" != "$PEANO_HELIOS_CONFIRM_TOKEN" ]; then
  printf 'real submission requires: --submit --confirm %s\n' "$PEANO_HELIOS_CONFIRM_TOKEN" >&2
  exit 2
fi

jobs=(
  slurm/peano_hydra_alpha_prepare.sbatch
  slurm/peano_hydra_alpha_train.sbatch
  slurm/peano_hydra_alpha_evaluate.sbatch
)
stages=(prepare train evaluate)
launcher="$script_dir/helios_submit_job.sh"

if [ "$mode" = "--test-only" ]; then
  # Test-only jobs have no real IDs. Validate each script without inventing
  # dependencies; the real path below supplies the actual accepted IDs.
  for job in "${jobs[@]}"; do
    "$launcher" --test-only "$job"
  done
  printf '%s\n' 'chain_status=test-only' 'No jobs submitted; real order is prepare -> train -> evaluate.'
  exit 0
fi

repo_root="$(cd "$script_dir/.." && pwd -P)"
git_root="$(git -C "$repo_root" rev-parse --show-toplevel)"
if [ "$(cd "$git_root" && pwd -P)" != "$repo_root" ]; then
  printf '%s\n' 'Hydra chain must run from its own repository checkout' >&2
  exit 1
fi
commit="$(git -C "$repo_root" rev-parse HEAD)"
local_changes="$(git -C "$repo_root" status --porcelain --untracked-files=all)"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]] || \
   [ -n "$local_changes" ]; then
  printf '%s\n' 'Hydra chain requires clean committed local source; review and commit first' >&2
  exit 1
fi

# Read only the fixed remote project's provenance. Do not synchronize, install,
# cancel, or alter anything remotely; deployment stays a separate guarded step.
ssh_target="$(peano_helios_ssh_target)"
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- $commit" <<'REMOTE'
set -euo pipefail
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
source_provenance="$project_root/.peano-source-provenance.tsv"
if [ ! -f "$source_provenance" ] || [ -L "$source_provenance" ] || \
   [ "$(wc -c < "$source_provenance")" -gt 1024 ] || \
   [ "$(wc -l < "$source_provenance")" -ne 1 ]; then
  printf '%s\n' 'Hydra chain requires one small regular remote source-provenance row' >&2
  exit 1
fi
IFS=$'\t' read -r remote_commit remote_dirty remote_synced remote_extra < "$source_provenance"
source_record="$(< "$source_provenance")"
if [ "$remote_commit" != "$1" ] || [ "$remote_dirty" != false ] || \
   [[ ! "$remote_synced" =~ ^[0-9TZ:+-]+$ ]] || [ -n "${remote_extra:-}" ] || \
   [ "$source_record" != "$remote_commit"$'\t'"false"$'\t'"$remote_synced" ]; then
  printf '%s\n' 'Remote Hydra source differs from the clean local commit; synchronize separately before submission' >&2
  exit 1
fi
printf 'verified_source_commit=%s\n' "$remote_commit"
REMOTE

current_commit="$(git -C "$repo_root" rev-parse HEAD)"
local_changes="$(git -C "$repo_root" status --porcelain --untracked-files=all)"
if [ "$current_commit" != "$commit" ] || [ -n "$local_changes" ]; then
  printf '%s\n' 'Local Hydra source changed during the remote provenance check' >&2
  exit 1
fi

job_ids=("" "" "")
current_stage=prepare
report_chain() {
  printf 'chain_status=%s\n' "$1"
  printf 'prepare_job_id=%s\n' "${job_ids[0]:-not-submitted}"
  printf 'train_job_id=%s\n' "${job_ids[1]:-not-submitted}"
  printf 'evaluate_job_id=%s\n' "${job_ids[2]:-not-submitted}"
}
report_failure() {
  local status="$?"
  if [ "$status" -ne 0 ]; then
    report_chain partial >&2
    printf 'failed_stage=%s\n' "$current_stage" >&2
    printf '%s\n' \
      'Previously accepted jobs were not cancelled. If a response was lost, inspect logs/submissions.tsv before retrying.' >&2
  fi
}
trap report_failure EXIT

# No queue polling, completion waits, or additional SSH checks between these
# submissions: the scheduler must receive each dependency before it expires.
for index in 0 1 2; do
  current_stage="${stages[$index]}"
  args=(--submit --confirm "$confirmation")
  if [ "$index" -gt 0 ]; then
    args+=(--afterok "${job_ids[$((index - 1))]}")
  fi
  args+=("${jobs[$index]}")
  # A failed SSH call can lose the response after Slurm accepted a job. Keep
  # that stage distinct from later stages that were never attempted.
  job_ids[$index]=unconfirmed
  if submission="$("$launcher" "${args[@]}")"; then
    :
  else
    status="$?"
    printf '%s\n' "$submission" >&2
    printf 'Hydra %s submission failed\n' "$current_stage" >&2
    exit "$status"
  fi
  matches=0
  accepted_id=""
  while IFS= read -r line; do
    case "$line" in
      'submitted job_id='*)
        matches=$((matches + 1))
        accepted_id="${line#submitted job_id=}"
        ;;
    esac
  done <<< "$submission"
  if [ "$matches" -ne 1 ] || \
     ! peano_helios_validate_single_job_id "$accepted_id" || \
     [ "$accepted_id" = 0 ]; then
    printf 'Hydra %s returned no unique valid accepted job ID:\n%s\n' \
      "$current_stage" "$submission" >&2
    exit 1
  fi
  job_ids[$index]="$accepted_id"
  printf 'submitted %s job_id=%s\n' "$current_stage" "$accepted_id"
done
report_chain submitted
