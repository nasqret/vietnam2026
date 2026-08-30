#!/usr/bin/env bash
# One scheduled exposed DEV diagnostic of two completed adapters; no training or resume.
set -euo pipefail
[ "$#" -eq 1 ] && [[ "$1" =~ ^[0-9a-f]{64}$ ]] || exit 2
approval_sha="$1"
[[ "${SLURM_JOB_ID:-}" =~ ^[1-9][0-9]*$ ]] && [ "${SLURM_RESTART_COUNT:-0}" = 0 ] || exit 2
for option in ${!SBATCH_@}; do printf 'SBATCH override forbidden: %s\n' "$option" >&2; exit 2; done
cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
parent_project="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
[ "$SLURM_SUBMIT_DIR" = "$parent_project/experiments/frontier-diagnostic-v1" ] || exit 2
export PEANO_HYDRA_PROFILE=peano-hydra-frontier-diagnostic-v1
export PEANO_JOB_SCRIPT=slurm/peano_hydra_frontier_diagnostic.sbatch
metadata="$(/usr/bin/python3 -I -B training/peano_hydra/frontier_diagnostic_launch.py \
  --check-job evaluate --approval-sha256 "$approval_sha")"
printf '%s\n' "$metadata"
evaluation_request_sha="$(/usr/bin/python3 -I -B -c \
  'import json,re,sys; x=json.loads(sys.argv[1]); s=x["evaluation_request_sha256"]; assert x["status"]=="job-verified" and re.fullmatch("[0-9a-f]{64}",s); print(s)' "$metadata")"
module purge
export PEANO_HELIOS_ML_MODULE=ML-bundle/25.10
module load "$PEANO_HELIOS_ML_MODULE"
for dependency in "$parent_project/.venv-helios" "$parent_project/.cache" "$parent_project/.cache/huggingface"; do
  [ -d "$dependency" ] && [ ! -L "$dependency" ] || { printf 'missing/unsafe runtime: %s\n' "$dependency" >&2; exit 2; }
done
# The existing venv's normal bin/python link is allowed; no environment install.
hydra_python="$parent_project/.venv-helios/bin/python"
test -x "$hydra_python"
export PYTHONHASHSEED=20260826 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX=/dev/null PYTHONMALLOC=malloc
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
"$hydra_python" -I -B scripts/check_peano_hydra_frontier_runtime.py
"$hydra_python" -I -B -m pip check
# The semantic original-origin and DEV-plan gate and full existing artifact rehash
# both run inside this entrypoint before any inference frameworks or weights.
exec "$hydra_python" -I -B -X pycache_prefix=/dev/null scripts/eval_peano_hydra_frontier_diagnostic.py \
  --execute --request _deploy/hydra-frontier-diagnostic-v1/evaluation-request.json \
  --expected-request-sha256 "$evaluation_request_sha" \
  --approval _deploy/hydra-frontier-diagnostic-v1/approval.json --expected-approval-sha256 "$approval_sha" \
  --output results/peano-hydra/evaluations/frontier-diagnostic-v1 --stop-after-seconds 720
