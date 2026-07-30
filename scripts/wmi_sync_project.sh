#!/usr/bin/env bash
# Deploy one clean Git tree to WMI under a cluster-wide source lock.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

ssh_target="$(peano_wmi_ssh_target)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
local_commit="$(git -C "$repo_root" rev-parse HEAD)"
local_tree="$(git -C "$repo_root" rev-parse 'HEAD^{tree}')"
if [[ ! "$local_commit" =~ ^[0-9a-f]{40}$ ]] || \
   [[ ! "$local_tree" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'refusing malformed local Git identity: %s %s\n' \
    "$local_commit" "$local_tree" >&2
  exit 2
fi
if [ -n "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]; then
  printf '%s\n' 'WMI synchronization requires a clean committed worktree' >&2
  exit 2
fi
sync_timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# git archive is the closed tracked tree: ignored bytecode, editor files, local
# caches, and other uncommitted material never enter the deployment stream. The
# upload is inert; publication happens in the separately locked transaction.
remote_archive="$PEANO_WMI_PROJECT_ROOT/.incoming-source-$local_commit-$$.tar"
cleanup_remote_archive() {
  ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
    "rm -f -- $remote_archive" >/dev/null 2>&1 || true
}
trap cleanup_remote_archive EXIT
git -C "$repo_root" archive --format=tar HEAD | \
  ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
    "bash -lc 'set -euo pipefail; mkdir -p -- $PEANO_WMI_PROJECT_ROOT; set -o noclobber; exec 3> $remote_archive; dd status=none >&3'"

ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- $local_commit $local_tree $sync_timestamp $remote_archive" <<'REMOTE'
set -euo pipefail
commit="${1:?commit required}"
tree="${2:?tree required}"
synced_at="${3:?sync timestamp required}"
archive="${4:?archive required}"
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$tree" =~ ^[0-9a-f]{40}$ ]]
[[ "$synced_at" =~ ^[0-9TZ:-]+$ ]]

project_root=/work/bnaskrecki/peano-v3-morning-diagnostic-20260731-r1
expected_archive="$project_root/.incoming-source-$commit-"
if [[ "$archive" != "$expected_archive"[0-9]*.tar ]] || [ ! -f "$archive" ] || \
   [ -L "$archive" ]; then
  printf 'refusing unsafe WMI source archive: %s\n' "$archive" >&2
  exit 1
fi
mkdir -p -- "$project_root" "$project_root/logs" "$project_root/results" \
  "$project_root/tmp" "$project_root/checkpoints" \
  "$project_root/.cache/huggingface" "$project_root/.venv-wmi"
exec 8>"$project_root/.deployment.lock"
if ! flock -n -x 8; then
  printf '%s\n' 'refusing WMI sync while a deployment or Peano job is active' >&2
  exit 1
fi

if ! queue="$(squeue -h --me -o '%A|%j|%T')"; then
  printf '%s\n' 'cannot verify the WMI scheduler before source mutation' >&2
  exit 1
fi
active="$(
  printf '%s\n' "$queue" | awk -F'|' \
    '$2 == "peano-wmi-prepare" || $2 == "peano-wmi-qwen17" || \
     $2 == "peano-wmi-qwen17-eval" || $2 == "peano-wmi-v2-prepare" || \
     $2 == "peano-wmi-qwen17-v2" || $2 == "peano-wmi-qwen17-v2-eval" || \
     $2 == "peano-wmi-v3-prepare" || $2 == "peano-wmi-qwen17-v3" || \
     $2 == "peano-wmi-qwen17-v3-eval" || $2 == "peano-v3-morning" || \
     $2 == "peano-v3-showcase" || \
     $2 == "peano-wmi-prove" || $2 == "peano-wmi-probe"'
)"
if [ -n "$active" ]; then
  printf '%s\n' 'refusing WMI sync while a Peano job is queued:' >&2
  printf '%s\n' "$active" >&2
  exit 1
fi

stage="$(mktemp -d "$project_root/.sync-stage.XXXXXX")"
cleanup_stage() {
  rm -rf -- "$stage"
  rm -f -- "$archive"
}
trap cleanup_stage EXIT
tar -xf "$archive" -C "$stage"
rm -f -- "$archive"

# Reconstruct the Git tree object remotely. This verifies every transferred
# tracked byte and executable bit against the clean local commit before publish.
git -C "$stage" init -q
git -C "$stage" -c core.autocrlf=false add -f -A
observed_tree="$(git -C "$stage" write-tree)"
if [ "$observed_tree" != "$tree" ]; then
  printf 'WMI transfer tree mismatch: %s != %s\n' "$observed_tree" "$tree" >&2
  exit 1
fi
rm -rf -- "$stage/.git"

provenance="$project_root/.peano-source-provenance.tsv"
if [ -L "$provenance" ] || { [ -e "$provenance" ] && [ ! -f "$provenance" ]; }; then
  printf '%s\n' 'refusing unsafe existing WMI source provenance' >&2
  exit 1
fi
if [ -f "$provenance" ]; then
  mv -- "$provenance" "$project_root/logs/source-provenance-before-$synced_at.tsv"
fi

# The live tree is unavailable to new submissions while provenance is absent.
# Existing jobs hold a shared deployment lock, so reaching this mutation point
# also proves no job can be reading the old source.
rsync -a --delete-delay \
  --filter='protect /.deployment.lock' \
  --filter='protect /.venv-helios/***' \
  --exclude='/.venv-helios/***' \
  --filter='protect /.venv-wmi/***' \
  --exclude='/.venv-wmi/***' \
  --filter='protect /.cache/huggingface/***' \
  --exclude='/.cache/huggingface/***' \
  --filter='protect /data/peano-policy-v3/***' \
  --exclude='/data/peano-policy-v3/***' \
  --filter='protect /checkpoints/***' \
  --exclude='/checkpoints/***' \
  --filter='protect /results/***' \
  --exclude='/results/***' \
  --filter='protect /logs/***' \
  --exclude='/logs/***' \
  --filter='protect /tmp/***' \
  --exclude='/tmp/***' \
  --filter='protect /.peano-source-provenance.tsv' \
  --exclude='/.peano-source-provenance.tsv' \
  "$stage/" "$project_root/"

provenance_stage="$(mktemp "$project_root/.peano-source-provenance.tsv.XXXXXX")"
trap 'rm -rf -- "$stage"; rm -f -- "$provenance_stage"' EXIT
umask 077
printf '%s\tfalse\t%s\n' "$commit" "$synced_at" > "$provenance_stage"
mv -- "$provenance_stage" "$provenance"
sync -f "$provenance"
trap - EXIT
rm -rf -- "$stage"
printf 'published clean WMI source commit=%s tree=%s synced_at=%s\n' \
  "$commit" "$tree" "$synced_at"
REMOTE
trap - EXIT

printf 'WMI deployment accepted for clean commit %s\n' "$local_commit"
printf '%s\n' 'preserved environments, model cache, checkpoints, results, logs, and tmp'
