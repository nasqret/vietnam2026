#!/bin/bash
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:45:00
#SBATCH --no-requeue
#SBATCH --job-name=peano-sqrt2-ap090

set -euo pipefail
stage="${1:?snapshot root required}"
snapshot="${2:?snapshot SHA256 required}"
mode="${3:-full-pilot}"
[[ "$mode" = full-pilot || "$mode" = lean-only || "$mode" = regressions ]]
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
[ "$stage" = "/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots/$snapshot" ]
[ "${SLURM_CPUS_PER_TASK:?}" = 1 ]
[ "${SLURM_JOB_PARTITION:?}" = cpu_idle ]
[ "${SLURM_MEM_PER_NODE:?}" = 4096 ]
[ "${SLURM_RESTART_COUNT:-0}" = 0 ]
work="$(mktemp -d "/tmp/peano-sqrt2-${SLURM_JOB_ID}.XXXXXX")"
results=(evidence)
if [ "$mode" = regressions ]; then
  runner=scripts/verify_sqrt2_power_wmi_regressions.py
elif [ "$mode" = lean-only ]; then
  runner=scripts/verify_sqrt2_power_wmi_lean.py
  results+=(source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-lean-wmi-v2)
else
  runner=scripts/run_sqrt2_power_wmi.py
  results+=(source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-v1
    source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-lean-wmi-v1)
fi
preserve_results() {
  code=$?
  trap - EXIT
  for relative in "${results[@]}"
  do
    if [ -d "$work/$relative" ]; then
      if [ -e "$stage/$relative" ]; then
        echo "refusing to overwrite an earlier result: $relative" >&2
        code=1
      else
        mkdir -p "$(dirname "$stage/$relative")" || code=1
        cp -a "$work/$relative" "$stage/$relative" || code=1
      fi
    fi
  done
  exit "$code"
}
trap preserve_results EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'exit 129' HUP
# One shared-filesystem read; all imports, hashing and proof workers then use
# node-local scratch. The copied tar must match the submitted exact bytes.
cp "$stage/../incoming-$snapshot.tar" "$work/snapshot.tar"
[ "$(sha256sum "$work/snapshot.tar" | awk '{print $1}')" = "$snapshot" ]
tar -xf "$work/snapshot.tar" -C "$work"
mkdir "$work/tmp"
export TMPDIR="$work/tmp"
printf 'node_local_stage=%s\n' "$work"
cd "$work/source"
export PEANO_SQRT2_SNAPSHOT_SHA256="$snapshot"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONHASHSEED=20261004
export PYTHONPATH="$work/source/peano-lab/py:$work/source/scripts"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
unset PYTHONOPTIMIZE
unset LEAN_PATH LEAN_SRC_PATH LEAN_SYSROOT LEAN_OPTS
/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python -B \
  "$runner" --stage "$work" --evidence "$work/evidence"
