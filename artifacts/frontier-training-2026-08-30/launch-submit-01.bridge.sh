set -euo pipefail
[ "$#" -eq 3 ] || exit 2
approval_sha="$1"
mode="$2"
confirmation="$3"
[[ "$approval_sha" =~ ^[0-9a-f]{64}$ ]] || exit 2
if { [ "$mode" = --submit ] && [ "$confirmation" != PEANO-HYDRA-FRONTIER-TRAINING-7200-GPU-SECONDS ]; } ||
   { [ "$mode" = --test-only ] && [ -n "$confirmation" ]; }; then exit 2; fi
[ "$mode" = --test-only ] || [ "$mode" = --submit ] || exit 2
[ -z "${SLURM_JOB_ID:-}" ] || exit 2
for option in ${!SBATCH_@}; do printf 'SBATCH override forbidden: %s\n' "$option" >&2; exit 2; done
for option in ${!GIT_@}; do unset "$option"; done
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_NO_REPLACE_OBJECTS=1 GIT_NO_LAZY_FETCH=1 GIT_OPTIONAL_LOCKS=0
export PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/dev/null
gate=training/peano_hydra/frontier_training_launch.py
metadata="$(python3 -I -B "$gate" --check --local --approval-sha256 "$approval_sha")"
read -r commit helper_sha training_inputs_sha < <(python3 -I -B -c \
  'import json,re,sys; x=json.loads(sys.argv[1]); v=[x["source_commit"],x["helper_sha256"],x["training_inputs_sha256"]]; assert x["status"]=="metadata-verified" and re.fullmatch("[0-9a-f]{40}",v[0]) and all(re.fullmatch("[0-9a-f]{64}",s) for s in v[1:]); print(" ".join(v))' "$metadata")
python3 -I -B -X pycache_prefix=/dev/null scripts/check_peano_hydra_frontier_training_inputs.py \
  --check --request _deploy/hydra-frontier-training-v1/training-inputs.json --expected-request-sha256 "$training_inputs_sha"
rechecked="$(python3 -I -B "$gate" --check --local --approval-sha256 "$approval_sha")"
[ "$metadata" = "$rechecked" ] || { printf '%s\n' 'local approval/source changed before SSH' >&2; exit 2; }
ssh -o BatchMode=yes -o ConnectTimeout=15 -- plgnasqret@helios.cyfronet.pl \
  "bash -l -s -- $approval_sha $commit $helper_sha $mode" <<'REMOTE'
set -euo pipefail
[ "$#" -eq 4 ] || exit 2
project="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training/experiments/frontier-training-v1"
cd "$project"
gate=training/peano_hydra/frontier_training_launch.py
printf '%s  %s\n' "$3" "$gate" | sha256sum --check --status
arguments=(--approval-sha256 "$1" --source-commit "$2" "$4")
if [ "$4" = --submit ]; then arguments+=(--confirm PEANO-HYDRA-FRONTIER-TRAINING-7200-GPU-SECONDS); fi
exec /usr/bin/python3.9 -I -B "$gate" "${arguments[@]}"
REMOTE
