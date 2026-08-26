#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=20:00:00
#SBATCH --job-name=peano-qwen17-v2
#SBATCH --output=logs/peano-qwen17-v2-%j.out
#SBATCH --error=logs/peano-qwen17-v2-%j.err

set -euo pipefail
module purge
unset PEANO_ML_MODULE PEANO_CLUSTER_BACKEND PEANO_BASE_ENV PEANO_REQUIREMENTS_LOCK
unset PEANO_BASE_MANIFEST PEANO_JOB_ENV_SCRIPT PEANO_JOB_ENV_SHA256
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
test -x .venv-helios/bin/python
test -f data/peano-policy-v2/manifest.json
export PYTHONHASHSEED=20260728
export PYTHONNOUSERSITE=1
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR"
export HF_HOME="$SLURM_SUBMIT_DIR/.cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=slurm/peano_train_qwen3_1_7b_v2.sbatch

.venv-helios/bin/python -m pip check
nvidia-smi -L
.venv-helios/bin/python -m training.peano_policy.train \
  --config training/peano_policy/configs/qwen3_1_7b_v2_heavy.toml
