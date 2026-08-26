#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --job-name=peano-hydra-alpha-train
#SBATCH --output=logs/peano-hydra-alpha-train-%j.out
#SBATCH --error=logs/peano-hydra-alpha-train-%j.err

# This allocation is reachable only through explicit confirmed submission and
# an afterok dependency on completed verifier-backed Alpha preparation.
set -euo pipefail
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
source_provenance=.peano-source-provenance.tsv
if [ ! -f "$source_provenance" ] || [ -L "$source_provenance" ]; then
  printf '%s\n' 'Hydra training requires one regular source-provenance file' >&2
  exit 1
fi
IFS=$'\t' read -r source_commit source_dirty source_timestamp source_extra \
  < "$source_provenance"
if [[ ! "$source_commit" =~ ^[0-9a-f]{40}$ ]] || \
   [ "$source_dirty" != false ] || [ -n "${source_extra:-}" ]; then
  printf '%s\n' 'Hydra training requires an explicitly clean committed source' >&2
  exit 1
fi

hydra_python=.venv-helios/bin/python
test -x "$hydra_python"
test -f _deploy/hydra-posttrain/manifest.json
export PYTHONHASHSEED=20260826
export PYTHONNOUSERSITE=1
export PYTHONMALLOC=malloc
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR"
export HF_HOME="$SLURM_SUBMIT_DIR/.cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=slurm/peano_hydra_alpha_train.sbatch

mkdir -p results/peano-hydra
exec 9>results/peano-hydra/.alpha-posttrain.lock
if ! flock -n 9; then
  printf '%s\n' 'another Alpha Hydra training job owns the output lock' >&2
  exit 1
fi

"$hydra_python" -m pip check
"$hydra_python" -m training.peano_hydra.posttrain \
  --preflight --preparation-dir _deploy/hydra-posttrain
nvidia-smi -L
"$hydra_python" -m training.peano_hydra.posttrain \
  --execute --preparation-dir _deploy/hydra-posttrain
