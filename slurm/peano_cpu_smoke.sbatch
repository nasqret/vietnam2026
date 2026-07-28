#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-cpu
#SBATCH --partition=plgrid-now
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:03:00
#SBATCH --job-name=peano-cpu-smoke
#SBATCH --output=logs/peano-cpu-smoke-%j.out
#SBATCH --error=logs/peano-cpu-smoke-%j.err

set -euo pipefail
module purge
unset PEANO_ML_MODULE PEANO_CLUSTER_BACKEND PEANO_BASE_ENV PEANO_REQUIREMENTS_LOCK
unset PEANO_BASE_MANIFEST PEANO_JOB_ENV_SCRIPT PEANO_JOB_ENV_SHA256
module load "${PEANO_HELIOS_ML_MODULE:-ML-bundle/25.10}"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py${PYTHONPATH:+:$PYTHONPATH}"
hostname
date -Is
uname -m
python3 --version
python3 - <<'PY'
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero

zero = Zero()
assert check((), EqRefl(zero), Eq(zero, zero))
print("Peano kernel CPU smoke: OK")
PY
