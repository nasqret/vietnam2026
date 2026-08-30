#!/usr/bin/env bash
# One fresh evaluation-only reservation. No upload, install, training or retry.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "$script_dir/.." && pwd -P)"
usage() {
  printf 'usage: %s --approval-sha256 SHA [--test-only]\n' "$0" >&2
  printf '       %s --approval-sha256 SHA --submit --confirm PEANO-HYDRA-EVALUATION\n' "$0" >&2
}
approval_sha=""
mode=--test-only
mode_set=false
confirmation=""
while [ "$#" -gt 0 ]; do
  case "$1" in
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
    *) printf 'unknown evaluation-only launch option: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done
[[ "$approval_sha" =~ ^[0-9a-f]{64}$ ]] || { usage; exit 2; }
if { [ "$mode" = --submit ] && [ "$confirmation" != PEANO-HYDRA-EVALUATION ]; } || \
   { [ "$mode" = --test-only ] && [ -n "$confirmation" ]; }; then
  printf '%s\n' 'submission requires a new explicit evaluation-only confirmation' >&2; exit 2
fi
[ -z "${SLURM_JOB_ID:-}" ] || { printf '%s\n' 'submission cannot nest in a scheduled job' >&2; exit 2; }
for option in ${!SBATCH_@}; do
  printf 'SBATCH override is not authorized: %s\n' "$option" >&2; exit 2
done
ssh_target=plgnasqret@helios.cyfronet.pl
[ "${HELIOS_SSH_TARGET:-$ssh_target}" = "$ssh_target" ] || {
  printf '%s\n' 'this approval authorizes only the configured Helios endpoint' >&2; exit 2;
}
for option in ${!GIT_@}; do unset "$option"; done
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_NO_REPLACE_OBJECTS=1 GIT_NO_LAZY_FETCH=1 GIT_OPTIONAL_LOCKS=0
cd "$repo_root"
[ "$(git rev-parse --show-toplevel)" = "$repo_root" ] || exit 2
commit="$(git rev-parse --verify HEAD)"
[[ "$commit" =~ ^[0-9a-f]{40}$ ]] && [ -z "$(git status --porcelain --untracked-files=all)" ] || {
  printf '%s\n' 'evaluation requires its clean frozen local execution checkout' >&2; exit 2;
}
# No native/model imports and no project writes, even before SSH --test-only.
python3 -I -B training/peano_hydra/search_launch.py --check --approval-sha256 "$approval_sha"
[ "$(git rev-parse --verify HEAD)" = "$commit" ] && [ -z "$(git status --porcelain --untracked-files=all)" ] || {
  printf '%s\n' 'local execution source changed during metadata admission' >&2; exit 2;
}
checksum() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}
[ "$(checksum _deploy/hydra-search-v2/approval.json)" = "$approval_sha" ] || exit 2
helper_sha="$(checksum training/peano_hydra/search_launch.py)"
[[ "$helper_sha" =~ ^[0-9a-f]{64}$ ]] || exit 2
ssh -o BatchMode=yes -o ConnectTimeout=15 -- "$ssh_target" \
  "bash -l -s -- $approval_sha $commit $helper_sha $mode" <<'REMOTE'
set -euo pipefail
[ "$#" -eq 4 ] || exit 2
# Intentionally NOT the completed training project's source checkout.
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training/experiments/search-v2"
cd "$project_root"
printf '%s  %s\n' "$3" training/peano_hydra/search_launch.py | sha256sum --check --status
arguments=(--approval-sha256 "$1" --source-commit "$2" "$4")
if [ "$4" = --submit ]; then arguments+=(--confirm PEANO-HYDRA-EVALUATION); fi
exec python3 -I -B training/peano_hydra/search_launch.py "${arguments[@]}"
REMOTE
