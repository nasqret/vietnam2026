#!/usr/bin/env bash
# Scheduled frontier runtime only. Never submits, transfers, installs or retries.
set -euo pipefail
[ "$#" -eq 2 ] && { [ "$1" = train ] || [ "$1" = evaluate ]; } && [[ "$2" =~ ^[0-9a-f]{64}$ ]] || exit 2
stage="$1"
approval_sha="$2"
[[ "${SLURM_JOB_ID:-}" =~ ^[1-9][0-9]*$ ]] && [ "${SLURM_RESTART_COUNT:-0}" = 0 ] || exit 2
for option in ${!SBATCH_@}; do printf 'SBATCH override forbidden: %s\n' "$option" >&2; exit 2; done
cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
parent_project="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
[ "$SLURM_SUBMIT_DIR" = "$parent_project/experiments/frontier-v1" ] || exit 2
export PEANO_HYDRA_PROFILE=peano-hydra-frontier-v1
export PEANO_JOB_SCRIPT="slurm/peano_hydra_frontier_${stage}.sbatch"
admission="$(/usr/bin/python3 -I -B training/peano_hydra/frontier_pilot_launch.py \
  --check-job "$stage" --approval-sha256 "$approval_sha")"
printf '%s\n' "$admission"
evaluation_sha="$(/usr/bin/python3 -I -B -c \
  'import json,re,sys; x=json.loads(sys.argv[1]); s=x["evaluation_request_sha256"]; assert x["status"]=="job-verified" and re.fullmatch("[0-9a-f]{64}",s); print(s)' "$admission")"
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"
for dependency in "$parent_project/.venv-helios" "$parent_project/.cache" "$parent_project/.cache/huggingface"; do
  [ -d "$dependency" ] && [ ! -L "$dependency" ] || { printf 'missing/unsafe runtime: %s\n' "$dependency" >&2; exit 2; }
done
hydra_python="$parent_project/.venv-helios/bin/python"
test -x "$hydra_python"
export PYTHONHASHSEED=20260826 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX=/dev/null PYTHONMALLOC=malloc
export HF_HOME="$parent_project/.cache/huggingface"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_TELEMETRY=1
# Existing parent exclusion locks are opened and locked, never created,
# truncated or written. New experiment logs live only under frontier-v1.
for output_lock in "$parent_project/results/peano-hydra/.alpha-posttrain.lock" \
                   "$parent_project/results/peano-hydra/.authority-scale-evaluate.lock"; do
  [ -f "$output_lock" ] && [ ! -L "$output_lock" ] || exit 2
done
exec 9<>"$parent_project/results/peano-hydra/.alpha-posttrain.lock"
flock -n 9 || { printf '%s\n' 'another Hydra trainer owns the runtime lock' >&2; exit 2; }
exec 8<>"$parent_project/results/peano-hydra/.authority-scale-evaluate.lock"
flock -n 8 || { printf '%s\n' 'another Hydra evaluator owns the runtime lock' >&2; exit 2; }
"$hydra_python" -I -B scripts/check_peano_hydra_frontier_runtime.py
"$hydra_python" -I -B -m pip check
"$hydra_python" -I -B -X pycache_prefix=/dev/null scripts/eval_peano_hydra_frontier_benchmark.py \
  --check --request _deploy/hydra-frontier-v1/evaluation-request.json --expected-request-sha256 "$evaluation_sha"
if [ "$stage" = train ]; then
  # The trainer replays admitted source and enforces production token limits
  # before fresh weights; no resume or periodic checkpoint selection is allowed.
  exec "$hydra_python" -I -B -X pycache_prefix=/dev/null scripts/execute_peano_hydra_frontier_train.py \
    --approval-sha256 "$approval_sha"
fi
evaluation_output="results/peano-hydra/evaluations/frontier-v1-${SLURM_JOB_ID}"
[ ! -e "$evaluation_output" ] && [ ! -L "$evaluation_output" ] || exit 2
soft_seconds=$((1800 - SECONDS - 180))
if [ "$soft_seconds" -gt 1500 ]; then soft_seconds=1500; fi
[ "$soft_seconds" -gt 0 ] || { printf '%s\n' 'setup exhausted evaluation reservation; inference not started' >&2; exit 3; }
exec "$hydra_python" -I -B -X pycache_prefix=/dev/null scripts/eval_peano_hydra_frontier_benchmark.py \
  --execute --request _deploy/hydra-frontier-v1/evaluation-request.json --expected-request-sha256 "$evaluation_sha" \
  --approval _deploy/hydra-frontier-v1/approval.json --expected-approval-sha256 "$approval_sha" \
  --output "$evaluation_output" --stop-after-seconds "$soft_seconds"
