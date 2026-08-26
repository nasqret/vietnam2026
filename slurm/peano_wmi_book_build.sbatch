#!/bin/bash
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8192M
#SBATCH --time=01:00:00
#SBATCH --job-name=peano-book-build
#SBATCH --open-mode=append
# The submission wrapper overrides these with snapshot_root/logs paths.  A
# direct sbatch call discards output instead of mutating the immutable source.
#SBATCH --output=/dev/null
#SBATCH --error=/dev/null

set -euo pipefail

snapshot_sha256="${PEANO_BOOK_SNAPSHOT_SHA256:?snapshot SHA-256 is required}"
content_sha256="${PEANO_BOOK_CONTENT_MANIFEST_SHA256:?content manifest is required}"
source_root="${PEANO_BOOK_SOURCE_ROOT:?staged source root is required}"
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$content_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "${PEANO_BOOK_LOCAL_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
[[ "${PEANO_BOOK_HEAD_CAPTURE_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
[[ "${PEANO_BOOK_WORKTREE_STATUS_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
case "${PEANO_BOOK_LOCAL_DIRTY:-}" in true|false) ;; *) exit 2 ;; esac
case "${PEANO_BOOK_REQUESTED_PARTITION:-}" in cpu_idle) ;; *) exit 2 ;; esac
for positive_resource in \
  PEANO_BOOK_REQUESTED_NODES \
  PEANO_BOOK_REQUESTED_NTASKS \
  PEANO_BOOK_REQUESTED_CPUS_PER_TASK \
  PEANO_BOOK_REQUESTED_MEMORY_MIB \
  PEANO_BOOK_REQUESTED_TIME_LIMIT_SECONDS
do
  [[ "${!positive_resource:-}" =~ ^[1-9][0-9]*$ ]] || exit 2
done
[ "$PEANO_BOOK_REQUESTED_NODES" = 1 ]
[ "$PEANO_BOOK_REQUESTED_NTASKS" = 1 ]
[ "$PEANO_BOOK_REQUESTED_CPUS_PER_TASK" = 1 ]
[ "$PEANO_BOOK_REQUESTED_MEMORY_MIB" = 8192 ]
[ "$PEANO_BOOK_REQUESTED_TIME_LIMIT" = 01:00:00 ]
[ "$PEANO_BOOK_REQUESTED_TIME_LIMIT_SECONDS" = 3600 ]

[ -d "$source_root" ] && [ ! -L "$source_root" ]
[ "$(basename "$source_root")" = source ]
snapshot_root="$(dirname "$source_root")"
[ "$(basename "$snapshot_root")" = "$snapshot_sha256" ]
case "$snapshot_root" in
  /work/bnaskrecki/peano-lab-training/tmp/book-builds/*) ;;
  *) echo "unsafe WMI book snapshot root: $snapshot_root" >&2; exit 2 ;;
esac

job_id="${SLURM_JOB_ID:?SLURM_JOB_ID is required}"
[[ "$job_id" =~ ^[0-9]+$ ]]
run_parent="$snapshot_root/runs"
run_root="$run_parent/$job_id"
mkdir -p -- "$run_parent"
[ ! -e "$run_root" ]
mkdir -- "$run_root"
cp -a "$source_root/." "$run_root/"
mkdir -p -- "$run_root/logs"
cd "$run_root"

export PYTHONHASHSEED=20260730
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONOPTIMIZE
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV
for inherited_name in ${!CONDA_@}; do unset "$inherited_name"; done

python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ] || {
  printf 'missing reviewed WMI Python: %s\n' "$python_path" >&2
  exit 1
}
report="$run_root/logs/peano-book-build-$job_id.json"

printf 'snapshot_sha256=%s\n' "$snapshot_sha256"
printf 'content_manifest_sha256=%s\n' "$content_sha256"
printf 'local_commit=%s\n' "$PEANO_BOOK_LOCAL_COMMIT"
printf 'head_capture_sha256=%s\n' "$PEANO_BOOK_HEAD_CAPTURE_SHA256"
printf 'worktree_status_sha256=%s\n' "$PEANO_BOOK_WORKTREE_STATUS_SHA256"
printf 'local_dirty=%s\n' "$PEANO_BOOK_LOCAL_DIRTY"
printf 'requested_partition=%s\n' "$PEANO_BOOK_REQUESTED_PARTITION"
printf 'requested_cpus_per_task=%s\n' "$PEANO_BOOK_REQUESTED_CPUS_PER_TASK"
printf 'requested_memory_mib=%s\n' "$PEANO_BOOK_REQUESTED_MEMORY_MIB"
printf 'requested_time_limit=%s\n' "$PEANO_BOOK_REQUESTED_TIME_LIMIT"
printf 'run_root=%s\n' "$run_root"
printf 'host=%s\n' "$(hostname)"
"$python_path" --version

set +e
"$python_path" scripts/run_wmi_book_build.py --report "$report"
runner_status=$?
set -e
if [ -f "$report" ]; then
  sha256sum "$report"
fi
if [ -f "$run_root/logs/book-integrity.json" ]; then
  sha256sum "$run_root/logs/book-integrity.json"
fi
exit "$runner_status"
