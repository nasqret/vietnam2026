#!/bin/bash -l
#SBATCH --job-name=hydra-upgrade-20261020
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01/job-%j.out
#SBATCH --error=/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01/job-%j.err
set -euo pipefail
umask 077
module purge
module load ML-bundle/25.10
unset PYTHONPATH PYTHONHOME
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 CUBLAS_WORKSPACE_CONFIG=:4096:8
cd /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01
mkdir results
for arm in historical_retention wmi_c6_vanilla47 helios_c5_vanilla29; do
  /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python -B -s /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01/run_arm.py --study /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01/study.json --study-sha256 b85c30a8d02a5dcc8a32d6c41b5b2d7a28449693499a509a3c3049109ed2d897 --arm "$arm" --output /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01/results/"$arm"
done
