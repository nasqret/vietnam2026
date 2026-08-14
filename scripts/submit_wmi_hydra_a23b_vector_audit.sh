#!/usr/bin/env bash
# Deposit and optionally submit the immutable, bounded Hydra A2.3b WMI audit.
set -euo pipefail

readonly confirm_token="PEANO-HYDRA-A23B-WMI-VECTOR-AUDIT"
mode=test-only
confirmation=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=test-only; shift ;;
    --submit) mode=submit; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { echo "--confirm requires a phrase" >&2; exit 2; }
      confirmation="$2"; shift 2
      ;;
    --help|-h)
      echo "usage: $0 [--test-only]" >&2
      echo "       $0 --submit --confirm $confirm_token" >&2
      exit 0
      ;;
    *) printf 'unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
if [ "$mode" = submit ] && [ "$confirmation" != "$confirm_token" ]; then
  printf 'real submission requires --submit --confirm %s\n' "$confirm_token" >&2
  exit 2
fi
if [ "$mode" = test-only ] && [ -n "$confirmation" ]; then
  echo "--confirm is valid only with --submit" >&2
  exit 2
fi
if [ -z "$confirmation" ]; then confirmation=none; fi

ssh_target="${WMI_SSH_TARGET:-wmicluster}"
if [[ "$ssh_target" == -* ]] || \
   [[ ! "$ssh_target" =~ ^[A-Za-z0-9._-]+(@[A-Za-z0-9.-]+)?$ ]]; then
  printf 'invalid WMI_SSH_TARGET: %s\n' "$ssh_target" >&2
  exit 2
fi
ssh_jump="${WMI_SSH_JUMP:-}"
ssh_route=()
if [ -n "$ssh_jump" ]; then
  if [[ "$ssh_jump" == -* ]] || \
     [[ ! "$ssh_jump" =~ ^[A-Za-z0-9._-]+(@[A-Za-z0-9.-]+)?$ ]]; then
    printf 'invalid WMI_SSH_JUMP: %s\n' "$ssh_jump" >&2
    exit 2
  fi
  ssh_route=(-J "$ssh_jump")
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
stage="$(mktemp -d)"
stage="$(cd "$stage" && pwd -P)"
cleanup() {
  case "$stage" in
    /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*)
      rm -rf -- "$stage"
      ;;
    *) printf 'refusing unsafe temporary cleanup: %s\n' "$stage" >&2 ;;
  esac
}
trap cleanup EXIT

# Capture the external clean-Git identity before deriving any evidence.  The
# source-state program repeats a deeper stage-0/blob/HEAD audit independently.
head_before="$stage/head-before.txt"
tree_before="$stage/tree-before.txt"
status_before="$stage/status-before.bin"
head_after="$stage/head-after.txt"
tree_after="$stage/tree-after.txt"
status_after="$stage/status-after.bin"
git -C "$repo_root" rev-parse --verify HEAD > "$head_before"
git -C "$repo_root" rev-parse --verify 'HEAD^{tree}' > "$tree_before"
git -C "$repo_root" status --porcelain=v1 -z --untracked-files=all > "$status_before"
commit="$(tr -d '\n' < "$head_before")"
tree="$(tr -d '\n' < "$tree_before")"
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$tree" =~ ^[0-9a-f]{40}$ ]]
if [ -s "$status_before" ]; then
  echo "A2.3b WMI submission requires a clean committed Git worktree" >&2
  exit 2
fi

source_state="$stage/producer-source-state.json"
git_receipt="$stage/producer-git-verification-receipt.json"
evidence_envelope="$stage/producer-evidence.json"
check_envelope="$stage/producer-evidence-check.json"
python3 "$repo_root/scripts/build_peano_hydra_a23b_producer_source_state.py" \
  --repository-root "$repo_root" \
  --source-state-output "$source_state" \
  --git-receipt-output "$git_receipt" > "$evidence_envelope"
python3 "$repo_root/scripts/build_peano_hydra_a23b_producer_source_state.py" \
  --repository-root "$repo_root" \
  --source-state-output "$source_state" \
  --git-receipt-output "$git_receipt" \
  --check > "$check_envelope"
cmp -s "$evidence_envelope" "$check_envelope" || {
  echo "producer evidence envelope changed across create/check" >&2
  exit 1
}

git -C "$repo_root" rev-parse --verify HEAD > "$head_after"
git -C "$repo_root" rev-parse --verify 'HEAD^{tree}' > "$tree_after"
git -C "$repo_root" status --porcelain=v1 -z --untracked-files=all > "$status_after"
cmp -s "$head_before" "$head_after" && \
  cmp -s "$tree_before" "$tree_after" && \
  cmp -s "$status_before" "$status_after" || {
    echo "Git HEAD, tree, or status changed during A2.3b evidence derivation" >&2
    exit 1
  }

source_state_sha256="$(shasum -a 256 "$source_state" | awk '{print $1}')"
git_receipt_sha256="$(shasum -a 256 "$git_receipt" | awk '{print $1}')"
[[ "$source_state_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$git_receipt_sha256" =~ ^[0-9a-f]{64}$ ]]
infrastructure_manifest="$stage/wmi-infrastructure-manifest.json"
python3 "$repo_root/scripts/run_peano_hydra_a23b_wmi.py" \
  build-infrastructure-manifest \
  --repository-root "$repo_root" \
  --git-commit "$commit" \
  --git-tree "$tree" \
  --output "$infrastructure_manifest"
infrastructure_sha256="$(shasum -a 256 "$infrastructure_manifest" | awk '{print $1}')"
[[ "$infrastructure_sha256" =~ ^[0-9a-f]{64}$ ]]
sync_timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
provenance="$stage/.peano-source-provenance.tsv"
printf '%s\tfalse\t%s\n' "$commit" "$sync_timestamp" > "$provenance"
provenance_sha256="$(shasum -a 256 "$provenance" | awk '{print $1}')"
[[ "$provenance_sha256" =~ ^[0-9a-f]{64}$ ]]

package="$stage/package"
mkdir -p "$package/source" "$package/inputs"
git -C "$repo_root" archive --format=tar HEAD | tar -xf - -C "$package/source"
install -m 0600 "$source_state" "$package/inputs/producer-source-state.json"
install -m 0600 "$git_receipt" "$package/inputs/producer-git-verification-receipt.json"
install -m 0600 "$infrastructure_manifest" "$package/inputs/wmi-infrastructure-manifest.json"
install -m 0600 "$provenance" "$package/inputs/.peano-source-provenance.tsv"
archive="$stage/peano-hydra-a23b-vector-audit.tar"
COPYFILE_DISABLE=1 tar -cf "$archive" -C "$package" source inputs
archive_bytes="$(wc -c < "$archive" | tr -d ' ')"
snapshot_sha256="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$archive_bytes" =~ ^[1-9][0-9]*$ ]]
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]

# Close the packaging race as well as the source-evidence race.
git -C "$repo_root" rev-parse --verify HEAD > "$head_after"
git -C "$repo_root" rev-parse --verify 'HEAD^{tree}' > "$tree_after"
git -C "$repo_root" status --porcelain=v1 -z --untracked-files=all > "$status_after"
cmp -s "$head_before" "$head_after" && \
  cmp -s "$tree_before" "$tree_after" && \
  cmp -s "$status_before" "$status_after" || {
    echo "Git HEAD, tree, or status changed during A2.3b packaging" >&2
    exit 1
  }

remote_root=/work/bnaskrecki/peano-lab-training/tmp/hydra-a23b-vector-audit
transfer_id="$$"
remote_incoming="$remote_root/.incoming-$snapshot_sha256-$transfer_id.tar"
ssh -o BatchMode=yes -o ConnectTimeout=15 "${ssh_route[@]}" "$ssh_target" \
  "bash -c 'set -euo pipefail; mkdir -p -- $remote_root; umask 077; set -o noclobber; exec 3> $remote_incoming; dd status=none >&3'" \
  < "$archive"

ssh -o BatchMode=yes -o ConnectTimeout=15 "${ssh_route[@]}" "$ssh_target" \
  "bash -s -- $snapshot_sha256 $archive_bytes $commit $tree $source_state_sha256 $git_receipt_sha256 $infrastructure_sha256 $provenance_sha256 $sync_timestamp $mode $confirmation $transfer_id" <<'REMOTE'
set -euo pipefail
umask 077
snapshot_sha256="${1:?snapshot hash required}"
archive_bytes="${2:?archive bytes required}"
commit="${3:?commit required}"
tree="${4:?tree required}"
source_state_sha256="${5:?source-state hash required}"
git_receipt_sha256="${6:?Git receipt hash required}"
infrastructure_sha256="${7:?infrastructure hash required}"
provenance_sha256="${8:?provenance hash required}"
sync_timestamp="${9:?sync timestamp required}"
mode="${10:?mode required}"
confirmation="${11:?confirmation required}"
transfer_id="${12:?transfer id required}"
[[ "$snapshot_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$archive_bytes" =~ ^[1-9][0-9]*$ ]]
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$tree" =~ ^[0-9a-f]{40}$ ]]
[[ "$source_state_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$git_receipt_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$infrastructure_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$provenance_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$sync_timestamp" =~ ^[0-9TZ:-]+$ ]]
[[ "$transfer_id" =~ ^[1-9][0-9]*$ ]]
case "$mode" in test-only|submit) ;; *) exit 2 ;; esac

root=/work/bnaskrecki/peano-lab-training/tmp/hydra-a23b-vector-audit
incoming="$root/.incoming-$snapshot_sha256-$transfer_id.tar"
snapshot_root="$root/$snapshot_sha256"
stage="$root/.stage-$snapshot_sha256-$transfer_id"
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(stat -c %s "$incoming")" = "$archive_bytes" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot_sha256" ] || {
  echo "A2.3b WMI snapshot hash mismatch" >&2
  exit 1
}

exec 8>"$root/.deposit.lock"
flock -x 8
if [ ! -e "$snapshot_root" ]; then
  [ ! -e "$stage" ]
  mkdir "$stage"
  tar -xf "$incoming" -C "$stage"
  [ -d "$stage/source" ] && [ ! -L "$stage/source" ]
  [ -d "$stage/inputs" ] && [ ! -L "$stage/inputs" ]
  for input in \
    producer-source-state.json \
    producer-git-verification-receipt.json \
    wmi-infrastructure-manifest.json \
    .peano-source-provenance.tsv
  do
    [ -f "$stage/inputs/$input" ] && [ ! -L "$stage/inputs/$input" ]
  done
  [ "$(sha256sum "$stage/inputs/producer-source-state.json" | awk '{print $1}')" = "$source_state_sha256" ]
  [ "$(sha256sum "$stage/inputs/producer-git-verification-receipt.json" | awk '{print $1}')" = "$git_receipt_sha256" ]
  [ "$(sha256sum "$stage/inputs/wmi-infrastructure-manifest.json" | awk '{print $1}')" = "$infrastructure_sha256" ]
  [ "$(sha256sum "$stage/inputs/.peano-source-provenance.tsv" | awk '{print $1}')" = "$provenance_sha256" ]
  expected_provenance="$(printf '%s\tfalse\t%s' "$commit" "$sync_timestamp")"
  [ "$(sed -n '1p' "$stage/inputs/.peano-source-provenance.tsv")" = "$expected_provenance" ]
  [ "$(wc -l < "$stage/inputs/.peano-source-provenance.tsv")" -eq 1 ]

  # Reconstruct the transferred tracked tree and compare it with HEAD^{tree}.
  git -C "$stage/source" init -q
  git -C "$stage/source" -c core.autocrlf=false add -f -A
  observed_tree="$(git -C "$stage/source" write-tree)"
  [ "$observed_tree" = "$tree" ] || {
    printf 'A2.3b transferred Git tree mismatch: %s != %s\n' "$observed_tree" "$tree" >&2
    exit 1
  }
  rm -rf -- "$stage/source/.git"
  mkdir "$stage/logs" "$stage/runs" "$stage/collections"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$snapshot_sha256" "$archive_bytes" "$commit" "$tree" \
    "$source_state_sha256" "$git_receipt_sha256" "$infrastructure_sha256" "$provenance_sha256" \
    "$sync_timestamp" > "$stage/deposit.tsv"
  sync -f "$stage/deposit.tsv"
  chmod -R a-w "$stage/source" "$stage/inputs"
  chmod a-w "$stage/deposit.tsv"
  mv "$stage" "$snapshot_root"
  sync -f "$root"
else
  [ -d "$snapshot_root" ] && [ ! -L "$snapshot_root" ]
  [ -f "$snapshot_root/deposit.tsv" ] && [ ! -L "$snapshot_root/deposit.tsv" ]
  expected_deposit="$(printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' \
    "$snapshot_sha256" "$archive_bytes" "$commit" "$tree" \
    "$source_state_sha256" "$git_receipt_sha256" "$infrastructure_sha256" "$provenance_sha256" \
    "$sync_timestamp")"
  [ "$(sed -n '1p' "$snapshot_root/deposit.tsv")" = "$expected_deposit" ] || {
    echo "existing A2.3b WMI immutable deposit identity mismatch" >&2
    exit 1
  }
fi
rm -f -- "$incoming"
flock -u 8

source_root="$snapshot_root/source"
input_root="$snapshot_root/inputs"
logs_root="$snapshot_root/logs"
export PEANO_A23B_SNAPSHOT_ROOT="$snapshot_root"
export PEANO_A23B_SOURCE_ROOT="$source_root"
export PEANO_A23B_INPUT_ROOT="$input_root"
export PEANO_A23B_SNAPSHOT_SHA256="$snapshot_sha256"
export PEANO_A23B_GIT_COMMIT="$commit"
export PEANO_A23B_GIT_TREE="$tree"
export PEANO_A23B_SOURCE_STATE_SHA256="$source_state_sha256"
export PEANO_A23B_GIT_RECEIPT_SHA256="$git_receipt_sha256"
export PEANO_A23B_INFRASTRUCTURE_SHA256="$infrastructure_sha256"
export PEANO_A23B_PROVENANCE_SHA256="$provenance_sha256"
export PEANO_A23B_REQUESTED_PARTITION=cpu_idle
export PEANO_A23B_REQUESTED_NODES=1
export PEANO_A23B_REQUESTED_NTASKS=1
export PEANO_A23B_REQUESTED_CPUS_PER_TASK=1
export PEANO_A23B_REQUESTED_MEMORY_MIB=4096
export PEANO_A23B_REQUESTED_TIME_LIMIT=00:15:00
export PEANO_A23B_REQUESTED_TIME_LIMIT_SECONDS=900
resources=(
  --partition=cpu_idle
  --nodes=1
  --ntasks=1
  --cpus-per-task=1
  --mem=4096M
  --time=00:15:00
  --output="$logs_root/peano-hydra-a23b-%j.out"
  --error="$logs_root/peano-hydra-a23b-%j.err"
)
cd "$source_root"
if [ "$mode" = test-only ]; then
  # Test-only still creates/verifies the immutable content-addressed deposit;
  # it is dry only at the Slurm submission boundary.
  sbatch --test-only "${resources[@]}" --export=ALL \
    slurm/peano_wmi_hydra_a23b_vector_audit.sbatch
  printf 'validated snapshot=%s commit=%s resources=1CPU/4096MiB/00:15:00\n' \
    "$snapshot_sha256" "$commit"
  exit 0
fi
if [ "$confirmation" != PEANO-HYDRA-A23B-WMI-VECTOR-AUDIT ]; then
  echo "invalid A2.3b WMI submission confirmation" >&2
  exit 2
fi

manifest="$root/submissions.tsv"
manifest_lock="$root/submissions.lock"
header='timestamp\tjob_id\tsnapshot_sha256\tgit_commit\tgit_tree\tsource_state_sha256\tgit_receipt_sha256\tinfrastructure_sha256\tprovenance_sha256\tsync_timestamp\tpartition\tntasks\tcpus_per_task\tmemory_mib\ttime_limit\tsbatch_sha256'
umask 077
[ ! -L "$manifest" ] && { [ ! -e "$manifest" ] || [ -f "$manifest" ]; } || {
  echo "unsafe A2.3b WMI submission ledger" >&2
  exit 1
}
[ ! -L "$manifest_lock" ] && { [ ! -e "$manifest_lock" ] || [ -f "$manifest_lock" ]; } || {
  echo "unsafe A2.3b WMI submission ledger lock" >&2
  exit 1
}
exec 9>"$manifest_lock"
flock -x 9
if [ ! -f "$manifest" ]; then
  printf '%b\n' "$header" > "$manifest"
elif [ "$(sed -n '1p' "$manifest")" != "$(printf '%b' "$header")" ]; then
  echo "A2.3b WMI submission ledger header mismatch" >&2
  exit 1
fi
sbatch_sha256="$(sha256sum slurm/peano_wmi_hydra_a23b_vector_audit.sbatch | awk '{print $1}')"
[[ "$sbatch_sha256" =~ ^[0-9a-f]{64}$ ]]
held_job=""
cancel_held() {
  if [[ "$held_job" =~ ^[1-9][0-9]*$ ]]; then
    scancel "$held_job" || true
  fi
}
trap cancel_held EXIT INT TERM HUP
submission="$(sbatch --hold --parsable "${resources[@]}" --export=ALL \
  slurm/peano_wmi_hydra_a23b_vector_audit.sbatch)"
held_job="${submission%%;*}"
[[ "$held_job" =~ ^[1-9][0-9]*$ ]] || {
  printf 'sbatch returned malformed job id: %s\n' "$submission" >&2
  exit 1
}
timestamp="$(date -Is)"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tcpu_idle\t1\t1\t4096\t00:15:00\t%s\n' \
  "$timestamp" "$held_job" "$snapshot_sha256" "$commit" "$tree" \
  "$source_state_sha256" "$git_receipt_sha256" "$infrastructure_sha256" "$provenance_sha256" \
  "$sync_timestamp" "$sbatch_sha256" >> "$manifest"
sync -f "$manifest"
job_pointer="$snapshot_root/job-$held_job.tsv"
set -o noclobber
printf '%s\t%s\t%s\n' "$held_job" "$snapshot_sha256" "$timestamp" > "$job_pointer"
set +o noclobber
sync -f "$job_pointer"
scontrol release "$held_job"
printf 'submitted job_id=%s snapshot=%s\n' "$held_job" "$snapshot_sha256"
printf 'ledger=%s\n' "$manifest"
held_job=""
trap - EXIT INT TERM HUP
REMOTE

trap - EXIT
cleanup
