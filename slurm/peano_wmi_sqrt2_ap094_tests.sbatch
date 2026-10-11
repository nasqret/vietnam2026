#!/bin/bash
#SBATCH --partition=cpu,cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:45:00
#SBATCH --no-requeue
#SBATCH --job-name=peano-sqrt2-ap094-tests
set -euo pipefail
stage="${1:?}"; snapshot="${2:?}"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
[ "$stage" = "/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots/$snapshot" ]
work="$(mktemp -d "/tmp/peano-sqrt2-${SLURM_JOB_ID}.XXXXXX")"
preserve_results() {
  code=$?
  trap - EXIT
  for relative in evidence
  do
    if [ -d "$work/$relative" ]; then
      if [ -e "$stage/$relative" ]; then
        echo "refusing to overwrite prior evidence" >&2; code=1
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
cp "$stage/../incoming-$snapshot.tar" "$work/snapshot.tar"
[ "$(sha256sum "$work/snapshot.tar" | awk '{print $1}')" = "$snapshot" ]
tar -xf "$work/snapshot.tar" -C "$work"
mkdir "$work/tmp"
export TMPDIR="$work/tmp" PEANO_SQRT2_SNAPSHOT_SHA256="$snapshot"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONHASHSEED=20261011
export PYTHONPATH="$work/source/peano-lab/py:$work/source/scripts"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
unset PYTHONOPTIMIZE LEAN_PATH LEAN_SRC_PATH LEAN_SYSROOT LEAN_OPTS
printf 'node_local_stage=%s\n' "$work"
cd "$work/source"
/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python -B \
  scripts/verify_sqrt2_power_wmi_ap094_tests.py --stage "$work" --evidence "$work/evidence"
