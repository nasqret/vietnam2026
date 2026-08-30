#!/usr/bin/env bash
# One complete held chain; no upload, retry, continuation, or implicit allocation.
# The local workflow checks the approval; Python3.6-compatible remote metadata
# code independently authenticates the same bytes BEFORE any sbatch call.
# Local workflow checking requires Python 3.11+ with standard-library TOML.
# Both interpreters ignore ambient Python paths before importing guard code.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "$script_dir/.." && pwd -P)"
source "$script_dir/helios_common.sh"
usage() {
  printf 'usage: %s --chain --approval-sha256 SHA [--test-only]\n' "$0" >&2
  printf '       %s --chain --approval-sha256 SHA --submit --confirm PEANO-HYDRA-CORRECTIVE\n' "$0" >&2
}
chain=false
approval_sha=""
mode=--test-only
mode_set=false
confirmation=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --chain)
      [ "$chain" = false ] || { usage; exit 2; }
      chain=true; shift ;;
    --approval-sha256)
      [ "$#" -ge 2 ] && [ -z "$approval_sha" ] || { usage; exit 2; }
      approval_sha="$2"; shift 2 ;;
    --test-only|--submit)
      [ "$mode_set" = false ] || { usage; exit 2; }
      mode="$1"; mode_set=true; shift ;;
    --confirm)
      [ "$#" -ge 2 ] && [ -z "$confirmation" ] || { usage; exit 2; }
      confirmation="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown corrective launch option: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done
[ "$chain" = true ] && [[ "$approval_sha" =~ ^[0-9a-f]{64}$ ]] || { usage; exit 2; }
if { [ "$mode" = --submit ] && [ "$confirmation" != PEANO-HYDRA-CORRECTIVE ]; } || \
   { [ "$mode" = --test-only ] && [ -n "$confirmation" ]; }; then
  printf '%s\n' 'real corrective submission requires its explicit new confirmation' >&2; exit 2
fi
[ -z "${SLURM_JOB_ID:-}" ] || { printf '%s\n' 'corrective submission cannot nest in a scheduled job' >&2; exit 2; }
for option in ${!SBATCH_@}; do
  printf 'SBATCH override is not authorized: %s\n' "$option" >&2; exit 2
done
# Ignore Git redirection/replacement hooks when identifying this actual checkout.
for option in ${!GIT_@}; do unset "$option"; done
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_NO_REPLACE_OBJECTS=1 GIT_NO_LAZY_FETCH=1 GIT_OPTIONAL_LOCKS=0
cd "$repo_root"
[ "$(git rev-parse --show-toplevel)" = "$repo_root" ] || exit 2
commit="$(git rev-parse --verify HEAD)"
[[ "$commit" =~ ^[0-9a-f]{40}$ ]] && [ -z "$(git status --porcelain --untracked-files=all)" ] || {
  printf '%s\n' 'corrective launch requires its clean frozen local checkout' >&2; exit 2;
}
approval=_deploy/hydra-corrective-v2-inputs/approval.json
for input_directory in _deploy _deploy/hydra-corrective-v2-inputs; do
  [ -d "$input_directory" ] && [ ! -L "$input_directory" ] || exit 2
done
[ -f "$approval" ] && [ ! -L "$approval" ] && [ "$(wc -c < "$approval")" -le 4194304 ] || exit 2
checksum() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}
[ "$(checksum "$approval")" = "$approval_sha" ] || {
  printf '%s\n' 'local approval differs from its externally supplied raw SHA' >&2; exit 2;
}
export PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/dev/null
python3 -I -B -X pycache_prefix=/dev/null scripts/prepare_peano_hydra_corrective.py \
  --check-approval --stage prepare --origin-request _deploy/hydra-corrective-v2-inputs/origin-request.json \
  --approval "$approval" --output-dir _deploy/hydra-corrective-v2 --run-id corrective-v2
[ "$(git rev-parse --verify HEAD)" = "$commit" ] && [ -z "$(git status --porcelain --untracked-files=all)" ] && \
  [ "$(checksum "$approval")" = "$approval_sha" ] || {
  printf '%s\n' 'local source or approval changed during preflight' >&2; exit 2;
}
helper_sha="$(checksum training/peano_hydra/corrective_launch.py)"
[[ "$helper_sha" =~ ^[0-9a-f]{64}$ ]] || exit 2
ssh_target="$(peano_helios_ssh_target)"
# Every argument below is fixed or checked against a conservative alphabet.
ssh -o BatchMode=yes -o ConnectTimeout=15 -- "$ssh_target" \
  "bash -l -s -- $approval_sha $commit $helper_sha $mode" <<'REMOTE'
set -euo pipefail
[ "$#" -eq 4 ] || exit 2
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
cd "$project_root"
printf '%s  %s\n' "$3" training/peano_hydra/corrective_launch.py | sha256sum --check --status
arguments=(--chain --approval-sha256 "$1" --source-commit "$2" "$4")
if [ "$4" = --submit ]; then arguments+=(--confirm PEANO-HYDRA-CORRECTIVE); fi
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -B training/peano_hydra/corrective_launch.py "${arguments[@]}"
REMOTE
