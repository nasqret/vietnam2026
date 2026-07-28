#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --job-name=peano-qwen17-smoke
#SBATCH --output=logs/peano-qwen17-smoke-%j.out
#SBATCH --error=logs/peano-qwen17-smoke-%j.err

set -euo pipefail
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
test -x .venv-helios/bin/python
test -f data/peano-policy-v1/manifest.json
export PYTHONHASHSEED=20260728
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export HF_HOME="$SLURM_SUBMIT_DIR/.cache/huggingface"
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=slurm/peano_train_qwen3_1_7b.sbatch

nvidia-smi -L
.venv-helios/bin/python -m training.peano_policy.train \
  --config training/peano_policy/configs/qwen3_1_7b_smoke.toml
