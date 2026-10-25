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
cd /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-08/source
read -r HYDRA_TRAINING_RESERVATION_SHA < /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-training-fresh-4b-v3-01/reservation.sha256
set +e
/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python -B -P /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-08/source/output/p6-prototype/remote_training_pilot.py --app-root /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-08/source/hydra-playground --reservation /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-training-fresh-4b-v3-01/reservation.json --reservation-sha256 "$HYDRA_TRAINING_RESERVATION_SHA" --model-key qwen3-4b-base --config /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-08/source/hydra-playground/training-v5/configs/qwen3_4b_decisions_v2_pilot.toml --dataset-manifest /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-08/source/output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json --base-directory /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/authenticated-bases-01/qwen3-4b-base --output /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-training-fresh-4b-v3-01/result
HYDRA_TRAINING_ACTUAL_EXIT=$?
set -C
printf '%s\n' "$HYDRA_TRAINING_ACTUAL_EXIT" > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-training-fresh-4b-v3-01/actual-process-exit.txt
exit "$HYDRA_TRAINING_ACTUAL_EXIT"
