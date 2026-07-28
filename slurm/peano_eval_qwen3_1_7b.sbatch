#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --job-name=peano-qwen17-eval
#SBATCH --output=logs/peano-qwen17-eval-%j.out
#SBATCH --error=logs/peano-qwen17-eval-%j.err

set -euo pipefail
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
test -x .venv-helios/bin/python
export PYTHONHASHSEED=20260728
export PYTHONNOUSERSITE=1
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR"
export HF_HOME="$SLURM_SUBMIT_DIR/.cache/huggingface"
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=slurm/peano_eval_qwen3_1_7b.sbatch

.venv-helios/bin/python scripts/eval_trained_peano_policy.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-smoke \
  --k 4 \
  --sample \
  --max-steps 16 \
  --output results/peano-policy/qwen3-1.7b-lora-smoke/heldout-k4.json
