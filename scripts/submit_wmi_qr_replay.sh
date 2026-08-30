#!/usr/bin/env bash
# Submit an isolated, content-addressed dirty-worktree QR replay to WMI.
set -euo pipefail

readonly confirm_token="PEANO-QR-WMI-REPLAY"
readonly suite_usage="full|euler-scaled-inverse|fermat-reindex|fermat-balance|fermat-endpoints|wilson-square-one|wilson-inverse-prefix|wilson-inverse-involution|wilson-inverse-endpoints|wilson-inverse-orbit|wilson-pair-product|wilson-pair-order|wilson-pair-order-induction|wilson-pair-order-iteration|gauss-signed-half|gauss-signed-prefix|gauss-magnitude-permutation|gauss-sign-factor-recode|finite-omission|quadratic-reciprocity-final|quadratic-reciprocity-layered|quadratic-reciprocity-recursive-diagnostic"
mode=test-only
confirmation=""
suite=full
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=test-only; shift ;;
    --submit) mode=submit; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { echo "--confirm requires a token" >&2; exit 2; }
      confirmation="$2"; shift 2
      ;;
    --suite)
      [ "$#" -ge 2 ] || { echo "--suite requires a name" >&2; exit 2; }
      suite="$2"; shift 2
      ;;
    --help|-h)
      echo "usage: $0 [--test-only] [--suite $suite_usage]" >&2
      echo "       $0 --submit --confirm $confirm_token [--suite $suite_usage]" >&2
      exit 0
      ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
case "$suite" in
  full|euler-scaled-inverse|fermat-reindex|fermat-balance|fermat-endpoints|wilson-square-one|wilson-inverse-prefix|wilson-inverse-involution|wilson-inverse-endpoints|wilson-inverse-orbit|wilson-pair-product|wilson-pair-order|wilson-pair-order-induction|wilson-pair-order-iteration|gauss-signed-half|gauss-signed-prefix|gauss-magnitude-permutation|gauss-sign-factor-recode|finite-omission|quadratic-reciprocity-final|quadratic-reciprocity-layered|quadratic-reciprocity-recursive-diagnostic) ;;
  *) echo "unknown QR replay suite: $suite" >&2; exit 2 ;;
esac
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
local_commit="$(git -C "$repo_root" rev-parse HEAD)"
[[ "$local_commit" =~ ^[0-9a-f]{40}$ ]]
if [ -n "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]; then
  local_dirty=true
else
  local_dirty=false
fi

stage="$(mktemp -d)"
cleanup() {
  case "$stage" in
    /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) rm -rf -- "$stage" ;;
    *) printf 'refusing unsafe temporary cleanup: %s\n' "$stage" >&2 ;;
  esac
  return 0
}
trap cleanup EXIT
archive="$stage/peano-qr-replay.tar"
(
  cd "$repo_root"
  COPYFILE_DISABLE=1 tar -cf "$archive" \
    --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' \
    peano-lab/py/peano_lab \
    peano-lab/py/tests \
    scripts/profile_peano_certificate_capacity.py \
    scripts/run_qr_wmi_replay.py \
    scripts/submit_wmi_qr_replay.sh \
    slurm/peano_wmi_qr_replay.sbatch
)
snapshot_sha256="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
transfer_id="$$"
[[ "$transfer_id" =~ ^[0-9]+$ ]]

ssh_target="${PEANO_QR_SSH_TARGET:-wmicluster}"
remote_root=/work/bnaskrecki/peano-lab-training/tmp/qr-replays
remote_incoming="$remote_root/.incoming-$snapshot_sha256-$transfer_id.tar"
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -lc 'set -euo pipefail; mkdir -p -- $remote_root; umask 077; dd status=none of=$remote_incoming'" \
  < "$archive"

# WMI's login-shell logout hook returns status 1 after a successful stdin
# script.  All commands used below have absolute paths or live in /usr/bin, so
# a non-login Bash is both sufficient and preserves the remote script's real
# exit status for the local receipt chain.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -s -- $snapshot_sha256 $local_commit $local_dirty $mode $confirmation_arg $suite $transfer_id" <<'REMOTE'
set -euo pipefail
snapshot_sha256="${1:?snapshot hash required}"
local_commit="${2:?local commit required}"
local_dirty="${3:?dirty flag required}"
mode="${4:?mode required}"
confirmation="${5:-}"
suite="${6:?suite required}"
transfer_id="${7:?transfer id required}"
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$local_commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$transfer_id" =~ ^[0-9]+$ ]]
case "$local_dirty" in true|false) ;; *) exit 2 ;; esac
case "$mode" in test-only|submit) ;; *) exit 2 ;; esac
case "$suite" in full|euler-scaled-inverse|fermat-reindex|fermat-balance|fermat-endpoints|wilson-square-one|wilson-inverse-prefix|wilson-inverse-involution|wilson-inverse-endpoints|wilson-inverse-orbit|wilson-pair-product|wilson-pair-order|wilson-pair-order-induction|wilson-pair-order-iteration|gauss-signed-half|gauss-signed-prefix|gauss-magnitude-permutation|gauss-sign-factor-recode|finite-omission|quadratic-reciprocity-final|quadratic-reciprocity-layered|quadratic-reciprocity-recursive-diagnostic) ;; *) exit 2 ;; esac

resource_partition=cpu_idle
resource_nodes=1
resource_ntasks=1
resource_cpus_per_task=1
case "$suite" in
  full|fermat-endpoints|quadratic-reciprocity-final|quadratic-reciprocity-layered|quadratic-reciprocity-recursive-diagnostic)
    resource_memory_mib=32768
    resource_time_limit=04:00:00
    resource_time_limit_seconds=14400
    ;;
  *)
    resource_memory_mib=16384
    resource_time_limit=02:00:00
    resource_time_limit_seconds=7200
    ;;
esac

root=/work/bnaskrecki/peano-lab-training/tmp/qr-replays
incoming="$root/.incoming-$snapshot_sha256-$transfer_id.tar"
run="$root/$snapshot_sha256"
stage="$root/.stage-$snapshot_sha256-$transfer_id"
[ -f "$incoming" ] && [ ! -L "$incoming" ]
observed="$(sha256sum "$incoming" | awk '{print $1}')"
if [ "$observed" != "$snapshot_sha256" ]; then
  echo "WMI QR snapshot hash mismatch" >&2
  exit 1
fi

exec 8>"$root/.qr-replay.lock"
flock -x 8
if [ ! -d "$run" ]; then
  mkdir -- "$stage"
  tar -xf "$incoming" -C "$stage"
  mkdir -p -- "$stage/logs"
  printf '%s\t%s\t%s\n' "$snapshot_sha256" "$local_commit" "$local_dirty" \
    > "$stage/snapshot.tsv"
  mv -- "$stage" "$run"
else
  [ -f "$run/snapshot.tsv" ] && [ ! -L "$run/snapshot.tsv" ]
  expected="$(printf '%s\t%s\t%s' "$snapshot_sha256" "$local_commit" "$local_dirty")"
  [ "$(sed -n '1p' "$run/snapshot.tsv")" = "$expected" ] || {
    echo "existing WMI QR snapshot provenance mismatch" >&2
    exit 1
  }
fi
rm -f -- "$incoming"
flock -u 8

cd "$run"
export PEANO_QR_SNAPSHOT_SHA256="$snapshot_sha256"
export PEANO_QR_LOCAL_COMMIT="$local_commit"
export PEANO_QR_LOCAL_DIRTY="$local_dirty"
export PEANO_QR_SUITE="$suite"
export PEANO_QR_REQUESTED_PARTITION="$resource_partition"
export PEANO_QR_REQUESTED_NODES="$resource_nodes"
export PEANO_QR_REQUESTED_NTASKS="$resource_ntasks"
export PEANO_QR_REQUESTED_CPUS_PER_TASK="$resource_cpus_per_task"
export PEANO_QR_REQUESTED_MEMORY_MIB="$resource_memory_mib"
export PEANO_QR_REQUESTED_TIME_LIMIT="$resource_time_limit"
export PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS="$resource_time_limit_seconds"
sbatch_resources=(
  --partition="$resource_partition"
  --nodes="$resource_nodes"
  --ntasks="$resource_ntasks"
  --cpus-per-task="$resource_cpus_per_task"
  --mem="${resource_memory_mib}M"
  --time="$resource_time_limit"
)
if [ "$mode" = test-only ]; then
  sbatch --test-only "${sbatch_resources[@]}" --export=ALL slurm/peano_wmi_qr_replay.sbatch
  printf 'validated snapshot=%s suite=%s resources=%sCPU/%sMiB/%s run=%s\n' \
    "$snapshot_sha256" "$suite" "$resource_cpus_per_task" \
    "$resource_memory_mib" "$resource_time_limit" "$run"
  exit 0
fi
if [ "$confirmation" != PEANO-QR-WMI-REPLAY ]; then
  echo "invalid WMI QR replay confirmation" >&2
  exit 2
fi
submission="$(sbatch --parsable "${sbatch_resources[@]}" --export=ALL slurm/peano_wmi_qr_replay.sbatch)"
job_id="${submission%%;*}"
[[ "$job_id" =~ ^[0-9]+$ ]]
printf '%s\t%s\t%s\t%s\t%s\n' \
  "$(date -Is)" "$job_id" "$snapshot_sha256" "$local_commit" "$suite" \
  >> submissions.tsv
printf 'submitted job_id=%s snapshot=%s suite=%s resources=%sCPU/%sMiB/%s run=%s\n' \
  "$job_id" "$snapshot_sha256" "$suite" "$resource_cpus_per_task" \
  "$resource_memory_mib" "$resource_time_limit" "$run"
REMOTE
