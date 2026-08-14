#!/usr/bin/env bash
# Bind terminal Slurm/log evidence for one A2.3d cut-liveness job.
set -euo pipefail

mode=test-only
job_id=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=test-only; shift ;;
    --collect) mode=collect; shift ;;
    --job-id)
      [ "$#" -ge 2 ] || { echo "--job-id requires one id" >&2; exit 2; }
      job_id="$2"; shift 2
      ;;
    --help|-h)
      echo "usage: $0 [--test-only] --job-id JOB_ID" >&2
      echo "       $0 --collect --job-id JOB_ID" >&2
      exit 0
      ;;
    *) printf 'unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
[[ "$job_id" =~ ^[1-9][0-9]*$ ]] || {
  echo "a single positive --job-id is required" >&2
  exit 2
}

ssh_target="${WMI_SSH_TARGET:-wmicluster}"
if [[ "$ssh_target" == -* ]] || \
   [[ ! "$ssh_target" =~ ^[A-Za-z0-9._-]+(@[A-Za-z0-9.-]+)?$ ]]; then
  printf 'invalid WMI_SSH_TARGET: %s\n' "$ssh_target" >&2
  exit 2
fi
ssh_jump="${WMI_SSH_JUMP:-}"
ssh_command=(ssh -o BatchMode=yes -o ConnectTimeout=15)
if [ -n "$ssh_jump" ]; then
  if [[ "$ssh_jump" == -* ]] || \
     [[ ! "$ssh_jump" =~ ^[A-Za-z0-9._-]+(@[A-Za-z0-9.-]+)?$ ]]; then
    printf 'invalid WMI_SSH_JUMP: %s\n' "$ssh_jump" >&2
    exit 2
  fi
  ssh_command+=(-J "$ssh_jump")
fi

"${ssh_command[@]}" "$ssh_target" \
  "bash -s -- $mode $job_id" <<'REMOTE'
set -euo pipefail
umask 077
mode="${1:?mode required}"
job_id="${2:?job id required}"
case "$mode" in test-only|collect) ;; *) exit 2 ;; esac
[[ "$job_id" =~ ^[1-9][0-9]*$ ]]

root=/work/bnaskrecki/peano-lab-training/tmp/hydra-a23d-cut-liveness
manifest="$root/submissions.tsv"
[ -f "$manifest" ] && [ ! -L "$manifest" ]
header='timestamp\tjob_id\tsnapshot_sha256\tgit_commit\tgit_tree\tsource_state_sha256\tgit_receipt_sha256\tinfrastructure_sha256\tprovenance_sha256\tsync_timestamp\tpartition\tntasks\tcpus_per_task\tmemory_mib\ttime_limit\tsbatch_sha256'
[ "$(sed -n '1p' "$manifest")" = "$(printf '%b' "$header")" ]
rows="$(awk -F '\t' -v expected="$job_id" 'NR > 1 && $2 == expected { print }' "$manifest")"
[ -n "$rows" ] || { echo "job id is absent from the A2.3d submission ledger" >&2; exit 1; }
[ "$(printf '%s\n' "$rows" | wc -l)" -eq 1 ] || {
  echo "job id has multiple A2.3d submission ledger rows" >&2
  exit 1
}
IFS=$'\t' read -r \
  timestamp recorded_job snapshot_sha256 commit tree source_state_sha256 \
  git_receipt_sha256 infrastructure_sha256 provenance_sha256 sync_timestamp \
  partition ntasks cpus memory_mib \
  time_limit sbatch_sha256 extra <<< "$rows"
[ "$recorded_job" = "$job_id" ]
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$tree" =~ ^[0-9a-f]{40}$ ]]
[ "$partition" = cpu_idle ]
[ "$ntasks" = 1 ] && [ "$cpus" = 1 ] && [ "$memory_mib" = 4096 ]
[ "$time_limit" = 00:15:00 ]
[ -z "${extra:-}" ]

snapshot_root="$root/$snapshot_sha256"
source_root="$snapshot_root/source"
logs_root="$snapshot_root/logs"
run_root="$snapshot_root/runs/$job_id"
collections_root="$snapshot_root/collections"
deposit="$snapshot_root/deposit.tsv"
sbatch_file="$source_root/slurm/peano_wmi_hydra_a23d_cut_liveness.sbatch"
[ -d "$snapshot_root" ] && [ ! -L "$snapshot_root" ]
[ -d "$source_root" ] && [ ! -L "$source_root" ]
[ -d "$logs_root" ] && [ ! -L "$logs_root" ]
[ -d "$collections_root" ] && [ ! -L "$collections_root" ]
[ -f "$deposit" ] && [ ! -L "$deposit" ]
[ -f "$sbatch_file" ] && [ ! -L "$sbatch_file" ]
stdout="$logs_root/peano-hydra-a23d-cut-liveness-$job_id.out"
stderr="$logs_root/peano-hydra-a23d-cut-liveness-$job_id.err"
execution="$run_root/execution-receipt.json"
collection="$collections_root/job-$job_id.json"

sacct_format=JobIDRaw,State,ExitCode,DerivedExitCode,ElapsedRaw,MaxRSS,ReqMem,AllocCPUS,NodeList
if [ "$mode" = test-only ]; then
  printf 'collection test-only job_id=%s snapshot=%s\n' "$job_id" "$snapshot_sha256"
  sacct -n -X -j "$job_id" --format="$sacct_format" -P
  for path in "$execution" "$stdout" "$stderr"; do
    if [ -f "$path" ] && [ ! -L "$path" ]; then
      sha256sum "$path"
    else
      printf 'missing %s\n' "$path"
    fi
  done
  exit 0
fi

[ ! -e "$collection" ] && [ ! -L "$collection" ] || {
  echo "A2.3d collection receipt already exists" >&2
  exit 1
}
sacct_stage="$(mktemp "$collections_root/.sacct-$job_id.XXXXXX")"
submission_stage="$(mktemp "$collections_root/.submission-$job_id.XXXXXX")"
cleanup() { rm -f -- "$sacct_stage" "$submission_stage"; }
trap cleanup EXIT
printf '%s\n' "$rows" > "$submission_stage"
sync -f "$submission_stage"
sacct -n -X -j "$job_id" --format="$sacct_format" -P > "$sacct_stage"
sync -f "$sacct_stage"
python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ]
set +e
env -i \
  HOME=/nonexistent/peano-a23d-wmi \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH=/usr/bin:/bin \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONHASHSEED=23 \
  PYTHONNOUSERSITE=1 \
  PYTHONPYCACHEPREFIX=/proc/peano-hydra-a23d-disabled-pycache \
  TZ=UTC \
  "$python_path" -B -P -s -S "$source_root/scripts/run_peano_hydra_a23d_cut_liveness_wmi.py" collect \
    --job-id "$job_id" \
    --submission-record "$submission_stage" \
    --deposit-record "$deposit" \
    --sbatch-file "$sbatch_file" \
    --source-root "$source_root" \
    --input-root "$snapshot_root/inputs" \
    --run-root "$run_root" \
    --sacct-record "$sacct_stage" \
    --execution-receipt "$execution" \
    --stdout "$stdout" \
    --stderr "$stderr" \
    --output "$collection"
collection_status=$?
set -e
if [ -f "$collection" ] && [ ! -L "$collection" ]; then
  chmod a-w "$collection"
  sync -f "$collection"
  sha256sum "$collection"
else
  echo "collector did not publish a terminal A2.3d receipt" >&2
fi
exit "$collection_status"
REMOTE
