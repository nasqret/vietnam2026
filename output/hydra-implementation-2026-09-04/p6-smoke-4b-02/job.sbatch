#!/bin/bash -l
set -euo pipefail
umask 077
module purge
module load ML-bundle/25.10
unset PYTHONPATH
export PYTHONHASHSEED=20260904
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1
cd /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-02/source
read -r HYDRA_RESERVATION_SHA < /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-smoke-4b-02/reservation.sha256
set +e
/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python -B -P /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-02/source/output/p6-prototype/remote_provider_smoke.py --app-root /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-02/source/hydra-playground --reservation /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-smoke-4b-02/reservation.json --reservation-sha256 "$HYDRA_RESERVATION_SHA" --base-directory /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/base-models/qwen3-4b-base --output /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-smoke-4b-02/result --throughput-examples 8 --throughput-config /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-02/source/hydra-playground/training-v5/configs/qwen3_4b_decisions_pilot.toml --dataset-manifest output/hydra-implementation-2026-09-04/decisions-v1-02/manifest.json --dataset-sha256 6ffc5d54678bbe43cdbf7178b4fd6d8493f661ba437526d36d4278111ad8f930
HYDRA_ACTUAL_EXIT=$?
printf '%s\n' "$HYDRA_ACTUAL_EXIT" > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/jobs/p6-smoke-4b-02/actual-process-exit.txt
exit "$HYDRA_ACTUAL_EXIT"
