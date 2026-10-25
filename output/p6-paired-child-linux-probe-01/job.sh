#!/bin/bash -l
# New probe only: one CPU, no GPU, 60-second scheduler envelope / 30-second inner wall.
set -euo pipefail
umask 077
test "$#" -eq 2
HYDRA_MONITOR_PACKAGE=$1
HYDRA_MONITOR_MANIFEST_SHA=$2
HYDRA_MONITOR_PYTHON_ROOT=/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0
export LD_LIBRARY_PATH="$HYDRA_MONITOR_PYTHON_ROOT/lib"
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1
unset PYTHONPATH PYTHONHOME
test -x /usr/bin/timeout
test -n "${SLURM_JOB_ID:-}"
set +e
/usr/bin/timeout --signal=TERM --kill-after=1s 29s \
  "$HYDRA_MONITOR_PYTHON_ROOT/bin/python3" -B -s "$HYDRA_MONITOR_PACKAGE/run_probe.py" \
  --manifest-sha256 "$HYDRA_MONITOR_MANIFEST_SHA" --job-id "$SLURM_JOB_ID"
HYDRA_MONITOR_ACTUAL_EXIT=$?
set -e
(set -o noclobber; printf '%s\n' "$HYDRA_MONITOR_ACTUAL_EXIT" > "$HYDRA_MONITOR_PACKAGE/actual-process-exit.txt")
exit "$HYDRA_MONITOR_ACTUAL_EXIT"
