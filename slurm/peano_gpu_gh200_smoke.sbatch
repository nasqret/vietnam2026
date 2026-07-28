#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gres=gpu:1
#SBATCH --time=00:03:00
#SBATCH --job-name=peano-gh200-smoke
#SBATCH --output=logs/peano-gh200-smoke-%j.out
#SBATCH --error=logs/peano-gh200-smoke-%j.err

set -euo pipefail
module purge
module load "${PEANO_HELIOS_ML_MODULE:-ML-bundle/25.10}"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
test -x .venv-helios/bin/python
export PYTHONNOUSERSITE=1
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR"
hostname
date -Is
uname -m
.venv-helios/bin/python --version
nvidia-smi -L
.venv-helios/bin/python - <<'PY'
import platform

import torch
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero

assert platform.machine() == "aarch64", platform.machine()
assert torch.cuda.is_available()
zero = Zero()
assert check((), EqRefl(zero), Eq(zero, zero))
print("torch", torch.__version__)
print("cuda", torch.version.cuda)
print("device", torch.cuda.get_device_name(0))
print("Peano kernel GH200 smoke: OK")
PY
