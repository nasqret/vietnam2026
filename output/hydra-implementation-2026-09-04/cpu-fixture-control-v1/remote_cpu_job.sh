#!/bin/bash
# Explicit CPU-only compatibility fixture; never a GPU allocation or study.
set -eu
umask 077
if [ "$#" -ne 2 ]; then
  exit 64
fi
HYDRA_CPU_SOURCE=$1
HYDRA_CPU_JOB=$2
IFS= read -r HYDRA_CPU_RESERVATION_SHA < "$HYDRA_CPU_JOB/reservation.sha256"
HYDRA_CPU_PYTHON_ROOT=/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0
export LD_LIBRARY_PATH="$HYDRA_CPU_PYTHON_ROOT/lib"
export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export CUDA_VISIBLE_DEVICES=
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
unset PYTHONPATH PYTHONHOME
set +e
"$HYDRA_CPU_PYTHON_ROOT/bin/python3" -B -s "$HYDRA_CPU_SOURCE/output/hydra-implementation-2026-09-04/cpu-fixture-control-v1/remote_cpu_fixture.py" \
  --source "$HYDRA_CPU_SOURCE" --job-directory "$HYDRA_CPU_JOB" \
  --reservation-sha256 "$HYDRA_CPU_RESERVATION_SHA"
HYDRA_CPU_ACTUAL_EXIT=$?
set -e
(set -o noclobber; printf '%s\n' "$HYDRA_CPU_ACTUAL_EXIT" > "$HYDRA_CPU_JOB/actual-process-exit.txt")
exit "$HYDRA_CPU_ACTUAL_EXIT"
