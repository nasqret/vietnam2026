#!/bin/bash -l
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --job-name=peano-hydra-alpha-evaluate
#SBATCH --output=logs/peano-hydra-alpha-evaluate-%j.out
#SBATCH --error=logs/peano-hydra-alpha-evaluate-%j.err

# Compare the pinned pretrained base and independently trained Alpha adapter
# sequentially on one GPU only after the explicitly declared training dependency.
set -euo pipefail
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
source_provenance=.peano-source-provenance.tsv
if [ ! -f "$source_provenance" ] || [ -L "$source_provenance" ]; then
  printf '%s\n' 'Hydra evaluation requires one regular source-provenance file' >&2
  exit 1
fi
IFS=$'\t' read -r source_commit source_dirty source_timestamp source_extra \
  < "$source_provenance"
if [[ ! "$source_commit" =~ ^[0-9a-f]{40}$ ]] || \
   [ "$source_dirty" != false ] || [ -n "${source_extra:-}" ]; then
  printf '%s\n' 'Hydra evaluation requires an explicitly clean committed source' >&2
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
export PEANO_JOB_SCRIPT=slurm/peano_hydra_alpha_evaluate.sbatch

adapter_dir="$("$hydra_python" -c '
import json
from pathlib import Path
import sys

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
candidate = manifest["training"]["adapter_output_dir"]
path = Path(candidate)
if (
    type(candidate) is not str
    or path.is_absolute()
    or ".." in path.parts
    or path.parts[:2] != ("results", "peano-hydra")
):
    raise SystemExit("Hydra adapter output escaped its reviewed results directory")
print(path.as_posix())
' _deploy/hydra-posttrain/manifest.json)"
test -f "$adapter_dir/manifest.json"
mkdir -p results/peano-hydra/evaluations
evaluation_output="results/peano-hydra/evaluations/matched-alpha-${SLURM_JOB_ID:?}.json"

"$hydra_python" -m pip check
nvidia-smi -L
"$hydra_python" scripts/eval_peano_hydra_posttrain.py \
  --preparation-dir _deploy/hydra-posttrain \
  --execute-models --trained-adapter "$adapter_dir" \
  --output "$evaluation_output"
