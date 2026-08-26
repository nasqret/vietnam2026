#!/usr/bin/env bash
# Mirror source to the dedicated Helios project root without deleting outputs.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

ssh_target="$(peano_helios_ssh_target)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
local_commit="$(git -C "$repo_root" rev-parse HEAD)"
if [[ ! "$local_commit" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'refusing malformed local git commit: %s\n' "$local_commit" >&2
  exit 2
fi
if [ -n "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]; then
  local_dirty=true
else
  local_dirty=false
fi
sync_timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

remote_output="$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" 'bash -l -s' <<'REMOTE'
set -euo pipefail
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
active_project_jobs="$(squeue -h -u "$USER" -o '%i|%Z' | awk -F '|' -v root="$project_root" \
  '$2 == root || index($2, root "/") == 1 { print $1 }')"
if [ -n "$active_project_jobs" ]; then
  printf 'refusing to change source used by active Peano jobs: %s\n' "$active_project_jobs" >&2
  exit 1
fi
mkdir -p -- "$project_root"/{logs,results,tmp,data,checkpoints}
printf '%s\n' "$project_root"
REMOTE
)"
remote_path="${remote_output##*$'\n'}"

case "$remote_path" in
  /*/codex-control/projects/peano-lab-training) ;;
  *)
    printf 'refusing unexpected remote project root: %s\n' "$remote_path" >&2
    exit 2
    ;;
esac
if [[ "$remote_path" == *[[:space:]]* || "$remote_path" == *".."* ]]; then
  printf 'refusing unsafe remote project root: %s\n' "$remote_path" >&2
  exit 2
fi

rsync -az --delete-delay \
  --exclude='/.git' \
  --exclude='/.claude-octopus/' \
  --exclude='/.claude/' \
  --exclude='/.codex/' \
  --exclude='/.agents/' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='*.swp' \
  --exclude='/.venv/' \
  --filter='protect /.venv-helios/***' \
  --exclude='/.venv-helios/***' \
  --filter='protect /.cache/huggingface/***' \
  --exclude='/.cache/huggingface/***' \
  --exclude='/node_modules/' \
  --exclude='/lab-lambda/vendor/' \
  --exclude='/peano-lab/vendor/' \
  --exclude='/artifacts/lean/**/.lake/' \
  --exclude='/book/_build/' \
  --exclude='/_deploy/' \
  --exclude='/.DS_Store' \
  --filter='protect /.peano-source-provenance.tsv' \
  --exclude='/.peano-source-provenance.tsv' \
  --filter='protect /checkpoints/***' \
  --filter='protect /results/***' \
  --filter='protect /logs/***' \
  --exclude='/checkpoints/***' \
  --exclude='/results/***' \
  --exclude='/logs/***' \
  "$repo_root/" "$ssh_target:$remote_path/"

# The remote mirror deliberately excludes .git.  Publish a tiny, validated
# source-state record so a submission can still bind itself to the local
# commit and to the fact that the synced worktree contained uncommitted edits.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- $local_commit $local_dirty $sync_timestamp" <<'REMOTE'
set -euo pipefail
commit="${1:?commit required}"
dirty="${2:?dirty flag required}"
synced_at="${3:?sync timestamp required}"
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$dirty" == true || "$dirty" == false ]]
[[ "$synced_at" =~ ^[0-9TZ:-]+$ ]]
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
stage="$(mktemp "$project_root/.peano-source-provenance.tsv.XXXXXX")"
trap 'rm -f -- "$stage"' EXIT
umask 077
printf '%s\t%s\t%s\n' "$commit" "$dirty" "$synced_at" > "$stage"
mv -f -- "$stage" "$project_root/.peano-source-provenance.tsv"
trap - EXIT
REMOTE

printf 'synced %s to %s:%s/\n' "$repo_root" "$ssh_target" "$remote_path"
printf 'preserved remote checkpoints/, results/, and logs/\n'
printf 'source commit=%s dirty=%s synced_at=%s\n' \
  "$local_commit" "$local_dirty" "$sync_timestamp"
