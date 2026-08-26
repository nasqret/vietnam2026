#!/usr/bin/env bash
# Invoke the remote submission tool. Its independent gate is authoritative.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

usage() {
  echo "usage: $0 [--test-only] [--afterok JOB_ID] slurm/job.sbatch" >&2
  echo "       $0 --submit --confirm $PEANO_HELIOS_CONFIRM_TOKEN [--afterok JOB_ID] slurm/job.sbatch" >&2
}

mode="--test-only"
confirmation=""
afterok=""
job_script=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode="--test-only"; shift ;;
    --submit) mode="--submit"; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      confirmation="$2"
      shift 2
      ;;
    --afterok)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$afterok" ] || { echo "--afterok may appear only once" >&2; exit 2; }
      afterok="$2"
      shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    --*) printf 'unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
    *)
      [ -z "$job_script" ] || { echo "only one job script is allowed" >&2; exit 2; }
      job_script="$1"
      shift
      ;;
  esac
done

[ -n "$job_script" ] || { usage; exit 2; }
peano_helios_validate_script_name "$job_script"
[ -z "$afterok" ] || peano_helios_validate_single_job_id "$afterok" || {
  printf 'invalid --afterok job id: %s\n' "$afterok" >&2
  exit 2
}
if [ "$mode" = "--test-only" ] && [ -n "$confirmation" ]; then
  echo "--confirm is only valid with --submit" >&2
  exit 2
fi
if [ "$mode" = "--submit" ] && [ "$confirmation" != "$PEANO_HELIOS_CONFIRM_TOKEN" ]; then
  echo "real submission requires: --submit --confirm $PEANO_HELIOS_CONFIRM_TOKEN" >&2
  exit 2
fi
if [ "$mode" = "--submit" ] && peano_helios_requires_dependency "$job_script" && [ -z "$afterok" ]; then
  echo "training and evaluation submissions require --afterok JOB_ID" >&2
  exit 2
fi

ssh_target="$(peano_helios_ssh_target)"
if [ "$mode" = "--test-only" ]; then
  remote_args=("--test-only")
else
  remote_args=("--submit" "--confirm" "$confirmation")
fi
[ -z "$afterok" ] || remote_args+=("--afterok" "$afterok")
remote_args+=("$job_script")

# Every interpolated argument is constrained above to a conservative alphabet.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- ${remote_args[*]}" <<'REMOTE'
set -euo pipefail
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
cd "$project_root"
exec ./scripts/submit_slurm_job.sh "$@"
REMOTE
