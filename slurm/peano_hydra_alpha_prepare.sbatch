#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --job-name=peano-hydra-alpha-prepare
#SBATCH --output=logs/peano-hydra-alpha-prepare-%j.out
#SBATCH --error=logs/peano-hydra-alpha-prepare-%j.err

# Freeze and independently replay the Alpha corpus before consuming GPU time.
# This job never loads model weights, starts CUDA training, or submits jobs.
set -euo pipefail
module purge
# The CPU partition is x86-64; .venv-helios belongs to the ARM GH200 nodes.
# Preparation uses only the standard library and must not load GPU packages.
module load Python/3.11.5

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
source_provenance=.peano-source-provenance.tsv
if [ ! -f "$source_provenance" ] || [ -L "$source_provenance" ]; then
  printf '%s\n' 'Hydra preparation requires one regular source-provenance file' >&2
  exit 1
fi
IFS=$'\t' read -r source_commit source_dirty source_timestamp source_extra \
  < "$source_provenance"
if [[ ! "$source_commit" =~ ^[0-9a-f]{40}$ ]] || \
   [ "$source_dirty" != false ] || [ -n "${source_extra:-}" ]; then
  printf '%s\n' 'Hydra preparation requires an explicitly clean committed source' >&2
  exit 1
fi

hydra_python="$(command -v python3)"
test -x "$hydra_python"
export PYTHONHASHSEED=20260826
export PYTHONNOUSERSITE=1
export PYTHONMALLOC=malloc
export PYTHONPATH="$SLURM_SUBMIT_DIR/peano-lab/py:$SLURM_SUBMIT_DIR"
export HF_HOME="$SLURM_SUBMIT_DIR/.cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PEANO_JOB_SCRIPT=slurm/peano_hydra_alpha_prepare.sbatch

"$hydra_python" scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra --include-graphs \
  --catalog-all --catalog-limit 192 --catalog-max-decisions 16
"$hydra_python" scripts/prepare_peano_hydra_posttrain.py \
  --source-dir _deploy/hydra --output-dir _deploy/hydra-posttrain
"$hydra_python" -m training.peano_hydra.posttrain \
  --preflight --preparation-dir _deploy/hydra-posttrain
"$hydra_python" scripts/eval_peano_hydra_posttrain.py \
  --preparation-dir _deploy/hydra-posttrain --check
