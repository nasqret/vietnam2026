#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=00:45:00
#SBATCH --job-name=peano-prepare
#SBATCH --output=logs/peano-prepare-%j.out
#SBATCH --error=logs/peano-prepare-%j.err

set -euo pipefail
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
export PYTHONHASHSEED=20260728
export PYTHONNOUSERSITE=1
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR"
export HF_HOME="$SLURM_SUBMIT_DIR/.cache/huggingface"
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=slurm/peano_prepare_training.sbatch
mkdir -p .cache/huggingface logs tmp

expected_wheels=/net/software/aarch64/el9/wheels/ML-bundle/25.10
test "${PIP_FIND_LINKS:-}" = "$expected_wheels"
python3 -m venv --clear .venv-helios
.venv-helios/bin/python -m pip install \
  --disable-pip-version-check \
  --only-binary=:all: \
  --no-deps \
  --find-links "$expected_wheels" \
  --requirement training/peano_policy/requirements-helios.lock
.venv-helios/bin/python -m pip check
.venv-helios/bin/python -c 'import torch; assert torch.__version__ == "2.9.1+cu129"; assert torch.version.cuda == "12.9"'
nvidia-smi -L
.venv-helios/bin/python -m training.peano_policy.smoke \
  --config training/peano_policy/configs/qwen3_1_7b_smoke.toml \
  --output "logs/peano-prepare-runtime-${SLURM_JOB_ID:?SLURM_JOB_ID is not defined}.json"
