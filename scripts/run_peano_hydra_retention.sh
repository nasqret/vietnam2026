#!/usr/bin/env bash
# One actual held-and-released retention stage. No installation or retry.
set -euo pipefail
[ "$#" -eq 2 ] || exit 2
stage="$1"
approval_sha="$2"
case "$stage" in train|evaluate) ;; *) exit 2 ;; esac
[[ "$approval_sha" =~ ^[0-9a-f]{64}$ ]] || exit 2
[[ "${SLURM_JOB_ID:-}" =~ ^[1-9][0-9]*$ ]] && [ "${SLURM_RESTART_COUNT:-0}" = 0 ] || exit 2
for option in ${!SBATCH_@}; do printf 'SBATCH override forbidden: %s\n' "$option" >&2; exit 2; done
cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
parent_project="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
[ "$SLURM_SUBMIT_DIR" = "$parent_project/experiments/retention-pilot-v1" ] || exit 2
export PEANO_HYDRA_PROFILE=peano-hydra-retention-pilot-v1
export PEANO_JOB_SCRIPT="slurm/peano_hydra_retention_${stage}.sbatch"
/usr/bin/python3.9 -I -B training/peano_hydra/retention_launch.py \
  --check-job "$stage" --approval-sha256 "$approval_sha"
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"
for dependency in "$parent_project/.venv-helios" "$parent_project/.cache" "$parent_project/.cache/huggingface"; do
  [ -d "$dependency" ] && [ ! -L "$dependency" ] || { printf 'missing/unsafe runtime: %s\n' "$dependency" >&2; exit 2; }
done
retention_python="$parent_project/.venv-helios/bin/python"
test -x "$retention_python"
export PYTHONHASHSEED=20260826 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX=/dev/null PYTHONMALLOC=malloc PYTHONUNBUFFERED=1
export HF_HOME="$parent_project/.cache/huggingface"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_TELEMETRY=1
for output_lock in "$parent_project/results/peano-hydra/.alpha-posttrain.lock" \
                   "$parent_project/results/peano-hydra/.authority-scale-evaluate.lock"; do
  [ -f "$output_lock" ] && [ ! -L "$output_lock" ] || exit 2
done
exec 9<>"$parent_project/results/peano-hydra/.alpha-posttrain.lock"
flock -n 9 || { printf '%s\n' 'another Hydra trainer owns the runtime lock' >&2; exit 2; }
exec 8<>"$parent_project/results/peano-hydra/.authority-scale-evaluate.lock"
flock -n 8 || { printf '%s\n' 'another Hydra evaluator owns the runtime lock' >&2; exit 2; }
"$retention_python" -I -B scripts/check_peano_hydra_frontier_runtime.py
"$retention_python" -I -B -m pip check
exec "$retention_python" -I -B -X pycache_prefix=/dev/null scripts/execute_peano_hydra_retention.py \
  --stage "$stage" --approval-sha256 "$approval_sha"
