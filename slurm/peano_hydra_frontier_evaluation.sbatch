#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --signal=B:USR1@180
#SBATCH --job-name=peano-hydra-frontier-evaluation-v1-evaluate
#SBATCH --output=logs/peano-hydra-frontier-evaluation-v1-evaluate-%j.out
#SBATCH --error=logs/peano-hydra-frontier-evaluation-v1-evaluate-%j.err
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
exec bash -l scripts/run_peano_hydra_frontier_evaluation.sh "$@"
