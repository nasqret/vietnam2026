#!/bin/bash -l
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --job-name=peano-qr-replay
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-qr-replay-%j.out
#SBATCH --error=logs/peano-qr-replay-%j.err

# The directives above preserve the original profile for existing suites.  The
# reviewed submission wrapper overrides them with 32 GiB and four hours for the
# dedicated Fermat-endpoint and quadratic-reciprocity final/layered/diagnostic
# suites and exports the exact request for the machine-readable receipt.

set -euo pipefail

run_root="${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
cd "$run_root"
[[ "${PEANO_QR_SNAPSHOT_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
[[ "${PEANO_QR_LOCAL_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
case "${PEANO_QR_LOCAL_DIRTY:-}" in
  true|false) ;;
  *) echo "invalid PEANO_QR_LOCAL_DIRTY" >&2; exit 2 ;;
esac
suite="${PEANO_QR_SUITE:-full}"
case "$suite" in
  full|euler-scaled-inverse|fermat-reindex|fermat-balance|fermat-endpoints|wilson-square-one|wilson-inverse-prefix|wilson-inverse-involution|wilson-inverse-endpoints|wilson-inverse-orbit|wilson-pair-product|wilson-pair-order|wilson-pair-order-induction|wilson-pair-order-iteration|gauss-signed-half|gauss-signed-prefix|gauss-magnitude-permutation|gauss-sign-factor-recode|finite-omission|quadratic-reciprocity-final|quadratic-reciprocity-layered|quadratic-reciprocity-recursive-diagnostic) ;;
  *) echo "invalid PEANO_QR_SUITE" >&2; exit 2 ;;
esac
case "${PEANO_QR_REQUESTED_PARTITION:-}" in
  cpu_idle) ;;
  *) echo "invalid PEANO_QR_REQUESTED_PARTITION" >&2; exit 2 ;;
esac
for positive_resource in \
  PEANO_QR_REQUESTED_NODES \
  PEANO_QR_REQUESTED_NTASKS \
  PEANO_QR_REQUESTED_CPUS_PER_TASK \
  PEANO_QR_REQUESTED_MEMORY_MIB \
  PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS
do
  [[ "${!positive_resource:-}" =~ ^[1-9][0-9]*$ ]] || {
    printf 'invalid %s\n' "$positive_resource" >&2
    exit 2
  }
done
[[ "${PEANO_QR_REQUESTED_TIME_LIMIT:-}" =~ ^([0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]] || {
  echo "invalid PEANO_QR_REQUESTED_TIME_LIMIT" >&2
  exit 2
}
if [ "$PEANO_QR_REQUESTED_NODES" != 1 ] || \
   [ "$PEANO_QR_REQUESTED_NTASKS" != 1 ] || \
   [ "$PEANO_QR_REQUESTED_CPUS_PER_TASK" != 1 ]; then
  echo "QR replay must remain a single-node, single-task, single-CPU job" >&2
  exit 2
fi
case "$suite" in
  full|fermat-endpoints|quadratic-reciprocity-final|quadratic-reciprocity-layered|quadratic-reciprocity-recursive-diagnostic)
    [ "$PEANO_QR_REQUESTED_MEMORY_MIB" = 32768 ] && \
      [ "$PEANO_QR_REQUESTED_TIME_LIMIT" = 04:00:00 ] && \
      [ "$PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS" = 14400 ] || {
        echo "$suite requires 32 GiB and four hours" >&2
        exit 2
      }
    ;;
  *)
    [ "$PEANO_QR_REQUESTED_MEMORY_MIB" = 16384 ] && \
      [ "$PEANO_QR_REQUESTED_TIME_LIMIT" = 02:00:00 ] && \
      [ "$PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS" = 7200 ] || {
        echo "invalid resource profile for existing QR replay suite" >&2
        exit 2
      }
    ;;
esac

export PYTHONHASHSEED=20260729
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONOPTIMIZE
export PYTHONPATH="$run_root/peano-lab/py:$run_root"

python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ] || {
  printf 'missing reviewed WMI Python: %s\n' "$python_path" >&2
  exit 1
}
report="logs/peano-qr-replay-${SLURM_JOB_ID}.json"

printf 'snapshot_sha256=%s\n' "$PEANO_QR_SNAPSHOT_SHA256"
printf 'local_commit=%s\n' "$PEANO_QR_LOCAL_COMMIT"
printf 'local_dirty=%s\n' "$PEANO_QR_LOCAL_DIRTY"
printf 'suite=%s\n' "$suite"
printf 'requested_partition=%s\n' "$PEANO_QR_REQUESTED_PARTITION"
printf 'requested_cpus_per_task=%s\n' "$PEANO_QR_REQUESTED_CPUS_PER_TASK"
printf 'requested_memory_mib=%s\n' "$PEANO_QR_REQUESTED_MEMORY_MIB"
printf 'requested_time_limit=%s\n' "$PEANO_QR_REQUESTED_TIME_LIMIT"
printf 'host=%s\n' "$(hostname)"
"$python_path" --version
"$python_path" scripts/run_qr_wmi_replay.py --suite "$suite" --report "$report"
sha256sum "$report"
