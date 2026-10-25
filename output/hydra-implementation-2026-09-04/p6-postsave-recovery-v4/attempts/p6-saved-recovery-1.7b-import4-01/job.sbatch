#!/bin/bash -l
set -euo pipefail
umask 077
module purge
module load ML-bundle/25.10
unset PYTHONPATH
export PYTHONHASHSEED=20260904
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
cd /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-09/source
read -r HYDRA_RECOVERY_RESERVATION_SHA < /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-saved-recovery-1.7b-import4-01/reservation.sha256
set +e
/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python -B -P /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/recovery/p6-postsave-recovery-v1/gpu_saved_reload_import4.py --reservation-sha256 "$HYDRA_RECOVERY_RESERVATION_SHA"
HYDRA_RECOVERY_ACTUAL_EXIT=$?
set -C
printf '%s\n' "$HYDRA_RECOVERY_ACTUAL_EXIT" > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-saved-recovery-1.7b-import4-01/actual-process-exit.txt
exit "$HYDRA_RECOVERY_ACTUAL_EXIT"
