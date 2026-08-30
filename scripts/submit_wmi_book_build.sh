#!/usr/bin/env bash
# Submit an isolated, canonical content-addressed Jupyter Book build to WMI.
set -euo pipefail

readonly confirm_token="PEANO-WMI-BOOK-BUILD"
mode=test-only
confirmation=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=test-only; shift ;;
    --submit) mode=submit; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { echo "--confirm requires a token" >&2; exit 2; }
      confirmation="$2"; shift 2
      ;;
    --help|-h)
      echo "usage: $0 [--test-only]" >&2
      echo "       $0 --submit --confirm $confirm_token" >&2
      exit 0
      ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
if [ "$mode" = submit ] && [ "$confirmation" != "$confirm_token" ]; then
  echo "real submission requires --submit --confirm $confirm_token" >&2
  exit 2
fi
if [ "$mode" = test-only ] && [ -n "$confirmation" ]; then
  echo "--confirm is only valid with --submit" >&2
  exit 2
fi
if [ -n "$confirmation" ]; then
  confirmation_arg="$confirmation"
else
  confirmation_arg=none
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
package_stage="$(mktemp -d)"
cleanup() {
  case "$package_stage" in
    /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*)
      rm -rf -- "$package_stage"
      ;;
    *) printf 'refusing unsafe temporary cleanup: %s\n' "$package_stage" >&2 ;;
  esac
  return 0
}
trap cleanup EXIT

head_before="$package_stage/head-before.txt"
head_after="$package_stage/head-after.txt"
status_before="$package_stage/status-before.bin"
status_after="$package_stage/status-after.bin"
git -C "$repo_root" rev-parse --verify HEAD > "$head_before"
git -C "$repo_root" status --porcelain=v1 -z --untracked-files=all > "$status_before"
head_capture_sha256="$(shasum -a 256 "$head_before" | awk '{print $1}')"
worktree_status_sha256="$(shasum -a 256 "$status_before" | awk '{print $1}')"
local_commit="$(tr -d '\n' < "$head_before")"
[[ "$local_commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$head_capture_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$worktree_status_sha256" =~ ^[0-9a-f]{64}$ ]]
if [ -s "$status_before" ]; then local_dirty=true; else local_dirty=false; fi

archive="$package_stage/peano-wmi-book.tar"
metadata="$package_stage/snapshot-metadata.json"
python3 "$repo_root/scripts/package_wmi_book_snapshot.py" \
  --output "$archive" > "$metadata"
git -C "$repo_root" rev-parse --verify HEAD > "$head_after"
git -C "$repo_root" status --porcelain=v1 -z --untracked-files=all > "$status_after"
head_after_sha256="$(shasum -a 256 "$head_after" | awk '{print $1}')"
status_after_sha256="$(shasum -a 256 "$status_after" | awk '{print $1}')"
if [ "$head_after_sha256" != "$head_capture_sha256" ] || \
   [ "$status_after_sha256" != "$worktree_status_sha256" ] || \
   ! cmp -s "$head_before" "$head_after" || \
   ! cmp -s "$status_before" "$status_after"; then
  echo "repository HEAD or porcelain-v1-z status changed during book packaging" >&2
  exit 1
fi
snapshot_sha256="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive_sha256"])' "$metadata")"
content_sha256="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["content_manifest_sha256"])' "$metadata")"
file_count="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["file_count"])' "$metadata")"
total_bytes="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["total_bytes"])' "$metadata")"
archive_bytes="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive_bytes"])' "$metadata")"
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$content_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$file_count" =~ ^[1-9][0-9]*$ ]]
[[ "$total_bytes" =~ ^[1-9][0-9]*$ ]]
[[ "$archive_bytes" =~ ^[1-9][0-9]*$ ]]
transfer_id="$$"
[[ "$transfer_id" =~ ^[0-9]+$ ]]

ssh_target=wmicluster
remote_root=/work/bnaskrecki/peano-lab-training/tmp/book-builds
remote_incoming="$remote_root/.incoming-$snapshot_sha256-$transfer_id.tar"
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -c 'set -euo pipefail; mkdir -p -- $remote_root; umask 077; dd status=none of=$remote_incoming'" \
  < "$archive"

# WMI's login-shell logout hook returns status 1 after a successful stdin
# script.  The control path uses /usr/bin tools plus an absolute Python path,
# so non-login Bash preserves the script's real status without changing its
# environment boundary.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -s -- $snapshot_sha256 $content_sha256 $file_count $total_bytes $archive_bytes $local_commit $head_capture_sha256 $worktree_status_sha256 $local_dirty $mode $confirmation_arg $transfer_id" <<'REMOTE'
set -euo pipefail
snapshot_sha256="${1:?snapshot hash required}"
content_sha256="${2:?content hash required}"
file_count="${3:?file count required}"
total_bytes="${4:?content byte count required}"
archive_bytes="${5:?archive byte count required}"
local_commit="${6:?local commit required}"
head_capture_sha256="${7:?HEAD capture hash required}"
worktree_status_sha256="${8:?worktree status hash required}"
local_dirty="${9:?dirty flag required}"
mode="${10:?mode required}"
confirmation="${11:-}"
transfer_id="${12:?transfer id required}"
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$content_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$head_capture_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$worktree_status_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$file_count" =~ ^[1-9][0-9]*$ ]]
[[ "$total_bytes" =~ ^[1-9][0-9]*$ ]]
[[ "$archive_bytes" =~ ^[1-9][0-9]*$ ]]
[[ "$local_commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$transfer_id" =~ ^[0-9]+$ ]]
case "$local_dirty" in true|false) ;; *) exit 2 ;; esac
case "$mode" in test-only|submit) ;; *) exit 2 ;; esac

# The reviewed interpreter is addressed absolutely below.  Remove inherited
# Python, venv, and Conda activation state before invoking it.
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV
for inherited_name in ${!CONDA_@}; do unset "$inherited_name"; done
export PYTHONDONTWRITEBYTECODE=1

root=/work/bnaskrecki/peano-lab-training/tmp/book-builds
incoming="$root/.incoming-$snapshot_sha256-$transfer_id.tar"
snapshot_root="$root/$snapshot_sha256"
source_root="$snapshot_root/source"
logs_root="$snapshot_root/logs"
stage="$root/.stage-$snapshot_sha256-$transfer_id"
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(stat -c %s "$incoming")" = "$archive_bytes" ]
observed_archive="$(sha256sum "$incoming" | awk '{print $1}')"
[ "$observed_archive" = "$snapshot_sha256" ] || {
  echo "WMI book archive hash mismatch" >&2
  exit 1
}
python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ]

exec 8>"$root/.book-build.lock"
flock -x 8
if [ ! -d "$source_root" ] || [ -L "$source_root" ]; then
  [ ! -e "$snapshot_root" ] || {
    echo "incomplete or unsafe existing WMI book snapshot: $snapshot_root" >&2
    exit 1
  }
  [ ! -e "$stage" ]
  mkdir -- "$stage"
  tar -xf "$incoming" -C "$stage"
  observed_json="$("$python_path" "$stage/scripts/package_wmi_book_snapshot.py" --manifest-only)"
  observed_content="$(printf '%s' "$observed_json" | "$python_path" -c 'import json,sys; print(json.load(sys.stdin)["content_manifest_sha256"])')"
  observed_files="$(printf '%s' "$observed_json" | "$python_path" -c 'import json,sys; print(json.load(sys.stdin)["file_count"])')"
  observed_bytes="$(printf '%s' "$observed_json" | "$python_path" -c 'import json,sys; print(json.load(sys.stdin)["total_bytes"])')"
  [ "$observed_content" = "$content_sha256" ]
  [ "$observed_files" = "$file_count" ]
  [ "$observed_bytes" = "$total_bytes" ]
  mkdir -- "$snapshot_root"
  mv -- "$stage" "$source_root"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$snapshot_sha256" "$content_sha256" "$file_count" "$total_bytes" \
    "$archive_bytes" "$local_commit" "$head_capture_sha256" \
    "$worktree_status_sha256" "$local_dirty" > "$snapshot_root/snapshot.tsv"
else
  [ -f "$snapshot_root/snapshot.tsv" ] && [ ! -L "$snapshot_root/snapshot.tsv" ]
  expected="$(printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' \
    "$snapshot_sha256" "$content_sha256" "$file_count" "$total_bytes" \
    "$archive_bytes" "$local_commit" "$head_capture_sha256" \
    "$worktree_status_sha256" "$local_dirty")"
  [ "$(sed -n '1p' "$snapshot_root/snapshot.tsv")" = "$expected" ] || {
    echo "existing WMI book snapshot provenance mismatch" >&2
    exit 1
  }
fi
[ -d "$source_root" ] && [ ! -L "$source_root" ]
observed_json="$("$python_path" "$source_root/scripts/package_wmi_book_snapshot.py" --manifest-only)"
observed_content="$(printf '%s' "$observed_json" | "$python_path" -c 'import json,sys; print(json.load(sys.stdin)["content_manifest_sha256"])')"
observed_files="$(printf '%s' "$observed_json" | "$python_path" -c 'import json,sys; print(json.load(sys.stdin)["file_count"])')"
observed_bytes="$(printf '%s' "$observed_json" | "$python_path" -c 'import json,sys; print(json.load(sys.stdin)["total_bytes"])')"
[ "$observed_content" = "$content_sha256" ]
[ "$observed_files" = "$file_count" ]
[ "$observed_bytes" = "$total_bytes" ]
rm -f -- "$incoming"
mkdir -p -- "$logs_root"
flock -u 8

cd "$source_root"
export PEANO_BOOK_SNAPSHOT_SHA256="$snapshot_sha256"
export PEANO_BOOK_CONTENT_MANIFEST_SHA256="$content_sha256"
export PEANO_BOOK_LOCAL_COMMIT="$local_commit"
export PEANO_BOOK_HEAD_CAPTURE_SHA256="$head_capture_sha256"
export PEANO_BOOK_WORKTREE_STATUS_SHA256="$worktree_status_sha256"
export PEANO_BOOK_LOCAL_DIRTY="$local_dirty"
export PEANO_BOOK_SOURCE_ROOT="$source_root"
export PEANO_BOOK_REQUESTED_PARTITION=cpu_idle
export PEANO_BOOK_REQUESTED_NODES=1
export PEANO_BOOK_REQUESTED_NTASKS=1
export PEANO_BOOK_REQUESTED_CPUS_PER_TASK=1
export PEANO_BOOK_REQUESTED_MEMORY_MIB=8192
export PEANO_BOOK_REQUESTED_TIME_LIMIT=01:00:00
export PEANO_BOOK_REQUESTED_TIME_LIMIT_SECONDS=3600
sbatch_resources=(
  --partition=cpu_idle
  --nodes=1
  --ntasks=1
  --cpus-per-task=1
  --mem=8192M
  --time=01:00:00
  --output="$logs_root/peano-book-build-%j.out"
  --error="$logs_root/peano-book-build-%j.err"
)
if [ "$mode" = test-only ]; then
  sbatch --test-only "${sbatch_resources[@]}" --export=ALL \
    slurm/peano_wmi_book_build.sbatch
  printf 'validated snapshot=%s content=%s files=%s resources=1CPU/8192MiB/01:00:00 source=%s\n' \
    "$snapshot_sha256" "$content_sha256" "$file_count" "$source_root"
  exit 0
fi
if [ "$confirmation" != PEANO-WMI-BOOK-BUILD ]; then
  echo "invalid WMI book build confirmation" >&2
  exit 2
fi
submission="$(sbatch --parsable "${sbatch_resources[@]}" --export=ALL \
  slurm/peano_wmi_book_build.sbatch)"
job_id="${submission%%;*}"
[[ "$job_id" =~ ^[0-9]+$ ]]
printf '%s\t%s\t%s\t%s\t%s\n' \
  "$(date -Is)" "$job_id" "$snapshot_sha256" "$local_commit" "$local_dirty" \
  >> "$snapshot_root/submissions.tsv"
printf 'submitted job_id=%s snapshot=%s content=%s resources=1CPU/8192MiB/01:00:00 run=%s/runs/%s\n' \
  "$job_id" "$snapshot_sha256" "$content_sha256" "$snapshot_root" "$job_id"
REMOTE
