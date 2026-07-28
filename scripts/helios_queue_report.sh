#!/usr/bin/env bash
# Read-only queue and accounting report for the Peano Lab Helios grant.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

job_ids=""
if [ "$#" -gt 0 ]; then
  for job_id in "$@"; do
    if ! peano_helios_validate_job_id "$job_id"; then
      printf 'invalid job id argument: %s\n' "$job_id" >&2
      exit 2
    fi
    job_ids="${job_ids:+$job_ids,}$job_id"
  done
fi

ssh_target="$(peano_helios_ssh_target)"
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- $job_ids" <<'REMOTE'
set -euo pipefail
job_ids="${1:-}"

echo "== queue report =="
date -Is
hostname
whoami
echo "grant=plgccaiautore2026"

echo
echo "== user queue =="
squeue -u "$USER" -o "%.18i %.9P %.22j %.8T %.10M %.10l %.6D %R" || true

echo
echo "== user start estimates =="
squeue --start -u "$USER" -o "%.24i %.22j %.19S %.9P %.8D %R" || true

echo
echo "== pending reason counts =="
squeue -h -u "$USER" -t PD -o "%R" 2>/dev/null | sort | uniq -c | sort -nr || true

if [ -n "$job_ids" ]; then
  echo
  echo "== accounting =="
  sacct -j "$job_ids" \
    --format=JobIDRaw,JobName%32,State,ExitCode,Elapsed,Timelimit,Partition,NodeList%32,AllocTRES%64 \
    -P -X || true

  echo
  echo "== job details =="
  old_ifs="$IFS"
  IFS=,
  for job_id in $job_ids; do
    clean_job="${job_id%%%*}"
    printf '%s\n' "-- $clean_job --"
    scontrol show job "$clean_job" || true
  done
  IFS="$old_ifs"
fi
REMOTE
