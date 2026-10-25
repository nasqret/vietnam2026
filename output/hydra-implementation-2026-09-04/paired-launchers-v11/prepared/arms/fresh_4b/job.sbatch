#!/bin/bash -l
set -euo pipefail
umask 077
module purge
module load ML-bundle/25.10
unset PYTHONPATH PYTHONHOME
export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
cd /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-05/source
read -r HYDRA_PAIRED_RESERVATION_SHA < /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-paired-fresh-4b-v6-01/reservation.sha256
set +e
/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python -B /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-05/source/output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py --app-root /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-05/source/hydra-playground --study /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-paired-fresh-4b-v6-01/study.json --study-sha256 6124c2110209680f05530885e121e4600ef830b68bae883e3d9a539819ff2d02 --reservation /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-paired-fresh-4b-v6-01/reservation.json --reservation-sha256 "$HYDRA_PAIRED_RESERVATION_SHA" --output /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-paired-fresh-4b-v6-01/result
HYDRA_PAIRED_ACTUAL_EXIT=$?
set -C
printf '%s\n' "$HYDRA_PAIRED_ACTUAL_EXIT" > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-paired-fresh-4b-v6-01/actual-process-exit.txt
exit "$HYDRA_PAIRED_ACTUAL_EXIT"
