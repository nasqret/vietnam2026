#!/usr/bin/env bash
# Read-only WMI scheduler and provenance report.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"
ssh_target="$(peano_wmi_ssh_target)"
job_ids="${1:-}"
if [ -n "$job_ids" ] && ! peano_wmi_validate_job_id_list "$job_ids"; then
  printf 'invalid WMI job id list: %s\n' "$job_ids" >&2
  exit 2
fi

ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- $job_ids" <<'REMOTE'
set -euo pipefail
job_ids="${1:-}"
project_root=/work/bnaskrecki/peano-v3-morning-diagnostic-20260731-r1
printf '%s\n' '== gpu partitions =='
sinfo -o '%P|%a|%l|%D|%t|%G|%N' | grep -E '^(PARTITION|gpu)'
printf '%s\n' '== peano queue =='
squeue --me -o '%i|%P|%j|%T|%R|%b|%M|%l' | grep -E '^(JOBID|.*peano)' || true
if [ -n "$job_ids" ]; then
  printf '%s\n' '== accounting =='
  sacct -j "$job_ids" --format=JobID,JobName,Partition,State,ExitCode,Elapsed,AllocTRES -P
fi
printf '%s\n' '== morning diagnostic ledger =='
if [ -f "$project_root/logs/submissions.tsv" ]; then
  sed -n '1,240p' "$project_root/logs/submissions.tsv"
else
  printf '%s\n' '(absent)'
fi
REMOTE
