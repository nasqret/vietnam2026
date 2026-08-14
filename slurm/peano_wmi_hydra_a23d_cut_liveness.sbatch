#!/bin/bash
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --job-name=peano-hydra-a23d-cut
#SBATCH --open-mode=append

# The submission wrapper supplies absolute, snapshot-scoped stdout/stderr
# paths.  This file never runs against the mutable deployment checkout.

set -euo pipefail
umask 077

python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ] || {
  printf 'missing reviewed WMI CPython: %s\n' "$python_path" >&2
  exit 1
}

snapshot_root="${PEANO_A23D_SNAPSHOT_ROOT:?snapshot root required}"
source_root="${PEANO_A23D_SOURCE_ROOT:?source root required}"
input_root="${PEANO_A23D_INPUT_ROOT:?input root required}"
[[ "${PEANO_A23D_SNAPSHOT_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
expected_snapshot_root="/work/bnaskrecki/peano-lab-training/tmp/hydra-a23d-cut-liveness/$PEANO_A23D_SNAPSHOT_SHA256"
[ "$snapshot_root" = "$expected_snapshot_root" ] || {
  echo "unsafe A2.3d snapshot root" >&2
  exit 2
}
[ "$source_root" = "$snapshot_root/source" ]
[ "$input_root" = "$snapshot_root/inputs" ]
[ -d "$source_root" ] && [ ! -L "$source_root" ]
[ -d "$input_root" ] && [ ! -L "$input_root" ]

[[ "${PEANO_A23D_GIT_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
[[ "${PEANO_A23D_GIT_TREE:-}" =~ ^[0-9a-f]{40}$ ]]
for digest_name in \
  PEANO_A23D_SOURCE_STATE_SHA256 \
  PEANO_A23D_GIT_RECEIPT_SHA256 \
  PEANO_A23D_INFRASTRUCTURE_SHA256 \
  PEANO_A23D_PROVENANCE_SHA256
do
  [[ "${!digest_name:-}" =~ ^[0-9a-f]{64}$ ]] || {
    printf 'malformed %s\n' "$digest_name" >&2
    exit 2
  }
done
[ "${PEANO_A23D_REQUESTED_PARTITION:-}" = cpu_idle ]
[ "${PEANO_A23D_REQUESTED_NODES:-}" = 1 ]
[ "${PEANO_A23D_REQUESTED_NTASKS:-}" = 1 ]
[ "${PEANO_A23D_REQUESTED_CPUS_PER_TASK:-}" = 1 ]
[ "${PEANO_A23D_REQUESTED_MEMORY_MIB:-}" = 4096 ]
[ "${PEANO_A23D_REQUESTED_TIME_LIMIT:-}" = 00:15:00 ]
[ "${PEANO_A23D_REQUESTED_TIME_LIMIT_SECONDS:-}" = 900 ]

PYTHONPYCACHEPREFIX=/proc/peano-hydra-a23d-disabled-pycache \
  "$python_path" -B -P -s -S - <<'PY'
import platform
import sys

if platform.python_version() != "3.12.12":
    raise SystemExit(f"requires CPython 3.12.12, got {platform.python_version()}")
if platform.machine() != "x86_64":
    raise SystemExit(f"requires x86_64, got {platform.machine()}")
if sys.flags.optimize != 0:
    raise SystemExit("PYTHONOPTIMIZE is forbidden")
if (
    not sys.dont_write_bytecode
    or not sys.flags.safe_path
    or not sys.flags.no_site
    or not sys.flags.no_user_site
):
    raise SystemExit("reviewed Python isolation flags are absent")
if sys.pycache_prefix != "/proc/peano-hydra-a23d-disabled-pycache":
    raise SystemExit("reviewed Python cache prefix is absent")
PY

run_root="$snapshot_root/runs/${SLURM_JOB_ID:?SLURM job id required}"
set +e
env -i \
  HOME=/nonexistent/peano-a23d-wmi \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH=/usr/bin:/bin \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONHASHSEED=17 \
  PYTHONNOUSERSITE=1 \
  PYTHONPYCACHEPREFIX=/proc/peano-hydra-a23d-disabled-pycache \
  TZ=UTC \
  SLURM_JOB_ID="$SLURM_JOB_ID" \
  PEANO_A23D_SNAPSHOT_ROOT="$snapshot_root" \
  PEANO_A23D_SOURCE_ROOT="$source_root" \
  PEANO_A23D_INPUT_ROOT="$input_root" \
  PEANO_A23D_SNAPSHOT_SHA256="$PEANO_A23D_SNAPSHOT_SHA256" \
  PEANO_A23D_GIT_COMMIT="$PEANO_A23D_GIT_COMMIT" \
  PEANO_A23D_GIT_TREE="$PEANO_A23D_GIT_TREE" \
  PEANO_A23D_SOURCE_STATE_SHA256="$PEANO_A23D_SOURCE_STATE_SHA256" \
  PEANO_A23D_GIT_RECEIPT_SHA256="$PEANO_A23D_GIT_RECEIPT_SHA256" \
  PEANO_A23D_INFRASTRUCTURE_SHA256="$PEANO_A23D_INFRASTRUCTURE_SHA256" \
  PEANO_A23D_PROVENANCE_SHA256="$PEANO_A23D_PROVENANCE_SHA256" \
  PEANO_A23D_REQUESTED_PARTITION="$PEANO_A23D_REQUESTED_PARTITION" \
  PEANO_A23D_REQUESTED_NODES="$PEANO_A23D_REQUESTED_NODES" \
  PEANO_A23D_REQUESTED_NTASKS="$PEANO_A23D_REQUESTED_NTASKS" \
  PEANO_A23D_REQUESTED_CPUS_PER_TASK="$PEANO_A23D_REQUESTED_CPUS_PER_TASK" \
  PEANO_A23D_REQUESTED_MEMORY_MIB="$PEANO_A23D_REQUESTED_MEMORY_MIB" \
  PEANO_A23D_REQUESTED_TIME_LIMIT="$PEANO_A23D_REQUESTED_TIME_LIMIT" \
  PEANO_A23D_REQUESTED_TIME_LIMIT_SECONDS="$PEANO_A23D_REQUESTED_TIME_LIMIT_SECONDS" \
  "$python_path" -B -P -s -S "$source_root/scripts/run_peano_hydra_a23d_cut_liveness_wmi.py" execute \
    --source-root "$source_root" \
    --run-root "$run_root" \
    --source-state "$input_root/cut-liveness-source-state.json" \
    --git-receipt "$input_root/cut-liveness-git-verification-receipt.json" \
    --infrastructure-manifest "$input_root/wmi-infrastructure-manifest.json" \
    --provenance "$input_root/.peano-source-provenance.tsv"
worker_status=$?
set -e

receipt="$run_root/execution-receipt.json"
if [ -f "$receipt" ] && [ ! -L "$receipt" ]; then
  sync -f "$receipt"
  # The execution receipt is the run commit marker.  Freeze every producer,
  # verifier, and child-log byte before terminal collection hashes them.
  chmod -R a-w "$run_root"
  sha256sum "$receipt"
else
  echo "A2.3d execution receipt is absent; collector must classify unknown" >&2
fi
exit "$worker_status"
