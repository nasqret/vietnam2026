#!/usr/bin/env bash
# Create one immutable theorem request and submit its guarded WMI A100 job.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

usage() {
  echo "usage: $0 [--test-only] --theorem FORMULA [--sample --k N] [--max-steps N] [--seed N]" >&2
  echo "       $0 --submit --confirm $PEANO_WMI_CONFIRM_TOKEN --theorem FORMULA [--sample --k N] [--max-steps N] [--seed N]" >&2
}

mode=--test-only
confirmation=""
theorem=""
k=1
max_steps=16
seed=20260728
sample=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=--test-only; shift ;;
    --submit) mode=--submit; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      confirmation="$2"; shift 2
      ;;
    --theorem)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$theorem" ] || { echo "--theorem may appear only once" >&2; exit 2; }
      theorem="$2"; shift 2
      ;;
    --k)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      k="$2"; shift 2
      ;;
    --max-steps)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      max_steps="$2"; shift 2
      ;;
    --seed)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      seed="$2"; shift 2
      ;;
    --sample) sample=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done

[ -n "$theorem" ] || { usage; exit 2; }
if [ "$mode" = --test-only ] && [ -n "$confirmation" ]; then
  echo "--confirm is only valid with --submit" >&2
  exit 2
fi
if [ "$mode" = --submit ] && [ "$confirmation" != "$PEANO_WMI_CONFIRM_TOKEN" ]; then
  echo "real WMI submission requires: --submit --confirm $PEANO_WMI_CONFIRM_TOKEN" >&2
  exit 2
fi

create_args=(
  create
  --theorem "$theorem"
  --k "$k"
  --max-steps "$max_steps"
  --seed "$seed"
)
[ "$sample" = false ] || create_args+=(--sample)
request_payload="$(
  python3 "$script_dir/peano_policy_proof_request.py" "${create_args[@]}"
)"
request_id="$(
  printf '%s\n' "$request_payload" |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])'
)"
peano_wmi_validate_request_id "$request_id" || {
  echo "local proof-request builder returned an invalid id" >&2
  exit 1
}

ssh_target="$(peano_wmi_ssh_target)"
printf '%s\n' "$request_payload" | ssh -o BatchMode=yes -o ConnectTimeout=15 \
  "$ssh_target" \
  "cd $PEANO_WMI_PROJECT_ROOT && exec flock -s .deployment.lock python3 scripts/peano_policy_proof_request.py receive --request-id $request_id"

submit_args=("$mode")
[ "$mode" = --test-only ] || submit_args+=(--confirm "$confirmation")
submit_args+=(
  --request-id "$request_id"
  slurm/peano_wmi_prove_theorem.sbatch
)
cd "$repo_root"
"$script_dir/wmi_submit_job.sh" "${submit_args[@]}"
printf 'Peano WMI proof request: %s\n' "$request_id"
