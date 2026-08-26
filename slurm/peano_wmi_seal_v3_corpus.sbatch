#!/bin/bash -l
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v3-seal
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v3-seal-%j.out
#SBATCH --error=logs/peano-wmi-v3-seal-%j.err

# One-time bridge from the independently replayed historical model-v3 corpus
# to its immutable, current-source seal.  The Slurm submission contains the
# launcher itself.  Python therefore hashes the staged CLI before compiling
# those same in-memory bytes; it never asks Python to execute the CLI pathname.
set -euo pipefail

readonly project_root=/work/bnaskrecki/peano-lab-training
readonly historical_source_commit=5faa3d27cbaf522198ffa1bdcd11fa9d57341658
readonly historical_prepare_job=173040
readonly expected_manifest_sha256=ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983
readonly expected_dataset_attestation_sha256=4e1cf0d00725a739d6f371062ff2079cfb9bc3e36daf4f4219cbbe1399a68a12
readonly expected_token_audit_sha256=c290b285eabcf9d39ab13b4d6f0f194588541484390d35c00681041979e2f8d8
readonly expected_runtime_smoke_sha256=86cc35bfcf2d5ff51931c140f3eb7168e3f641e1f80d54a3984dba9e49e40749
readonly expected_cli_sha256=0b391513878c5fa333505a4e01049611fabbd091f11384c08462d6241604cc5d
readonly expected_module_sha256=a7c5cb45092c5fb1a0880cd27ba800fd6774bf203bcbf2f9dab4d6a56238adec
readonly destination=checkpoints/corpora/peano-policy-v3-173040
readonly -a artifact_names=(
  balanced-raw-traces.jsonl
  balanced-session-metadata.jsonl
  balanced-source-manifest.json
  combined-metadata-manifest.json
  library-raw-traces.jsonl
  library-session-metadata.jsonl
  library-source-manifest.json
  manifest.json
  session-metadata.jsonl
  test.jsonl
  train.jsonl
  val.jsonl
)
readonly -a artifact_hashes=(
  a44ddce9a31130a45d355e1fb50eb27856e226ab53ac756508e4411abb388897
  8cba2105b623aa745041b30ecab549596d214a28588f8dbb5dbb9c99e61f7289
  77aa015c9428b7f34895d8df1176d6601e6d853d248fbc8d2e3da398ecbd9082
  306c7e195ebd4e6a5047794fed1a9aad9fcf73ea463e1ea41bd8397bb37ec036
  89a67806ba6a074db8008754f2c1446308829f3f3fc664f6d7c9b4b40bda529a
  b0fbf0b83162c4fbe941895bab74bf4291ab4e7837f2caad8b908f3467c53241
  56fd066324542bf519d60717cd3c207edf1d3f41878f1ea304778d63d9b27d7e
  ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983
  b56cffb1fcc32212de04bdb6762087c9761177853d765933d6edb7b529858b73
  c4477c38124457880cdf7883782fa28213f0a6414e1194c182713ecafd8925cc
  626bcf4456efd98eae80828efceb9b89386e6ef83be463251fc1d07b3c2ff15e
  784512bbcb15b3d46fc7333fd3f917fa440d5d1d263385b7d2c16e9a40f0dd27
)

require_sha256_anchor() {
  local label="${1:?anchor label required}"
  local value="${2:?anchor value required}"
  if [[ ! "$value" =~ ^[0-9a-f]{64}$ ]]; then
    printf '%s is not an admitted SHA-256 anchor: %s\n' "$label" "$value" >&2
    exit 1
  fi
}

# The dataset-attestation digest has been authenticated.  The remaining two
# deliberately non-digest report values keep the job non-runnable until their
# hashes are learned through the same process.  This gate precedes sacct,
# mktemp, preflight, or seal publication.
require_sha256_anchor dataset_manifest "$expected_manifest_sha256"
require_sha256_anchor dataset_attestation "$expected_dataset_attestation_sha256"
require_sha256_anchor token_audit "$expected_token_audit_sha256"
require_sha256_anchor runtime_smoke "$expected_runtime_smoke_sha256"
require_sha256_anchor standalone_cli "$expected_cli_sha256"
require_sha256_anchor standalone_module "$expected_module_sha256"
test "${#artifact_names[@]}" -eq 12
test "${#artifact_hashes[@]}" -eq "${#artifact_names[@]}"
for index in "${!artifact_names[@]}"; do
  artifact_name="${artifact_names[$index]}"
  require_sha256_anchor \
    "artifact $artifact_name" "${artifact_hashes[$index]}"
done
test "${artifact_hashes[7]}" = "$expected_manifest_sha256"

cd "$project_root"
test "$(pwd -P)" = "$project_root"
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PEANO_JOB_SCRIPT=slurm/peano_wmi_seal_v3_corpus.sbatch
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
test "$(peano_wmi_current_python)" = "$wmi_python"
"$wmi_python" -I -B -S - "$wmi_python" <<'PYTHON_RUNTIME_GATE'
from pathlib import Path
import platform
import sys

expected = Path(sys.argv[1])
if platform.python_version() != "3.12.12":
    raise SystemExit(f"unexpected reviewed WMI Python version: {platform.python_version()}")
if platform.python_implementation() != "CPython" or Path(sys.executable) != expected:
    raise SystemExit(f"unexpected reviewed WMI Python identity: {sys.executable}")
PYTHON_RUNTIME_GATE

# This is deliberately not a normal same-source Slurm dependency.  Job 173040
# ran from the historical clean checkout.  Require its authoritative root job
# record before touching either seal lane.
historical_rows=0
historical_state=
while IFS='|' read -r observed_job observed_state extra; do
  if [ "$observed_job" = "$historical_prepare_job" ]; then
    historical_rows=$((historical_rows + 1))
    historical_state="${observed_state%%+*}"
    test -z "$extra"
  fi
done < <(sacct -n -X -j "$historical_prepare_job" --format=JobIDRaw,State -P)
if [ "$historical_rows" -ne 1 ] || [ "$historical_state" != COMPLETED ]; then
  printf 'historical WMI preparation %s is not uniquely COMPLETED: rows=%s state=%s\n' \
    "$historical_prepare_job" "$historical_rows" "$historical_state" >&2
  exit 1
fi

readonly artifact_dir=data/peano-policy-v3
readonly dataset_attestation="logs/peano-wmi-v3-dataset-attestation-${historical_prepare_job}.json"
readonly token_audit="logs/peano-wmi-v3-token-audit-${historical_prepare_job}.json"
readonly runtime_smoke="logs/peano-wmi-v3-prepare-runtime-${historical_prepare_job}.json"
readonly seal_report="logs/peano-wmi-v3-corpus-seal-${SLURM_JOB_ID:?}.json"
destination_exists=false
if [ -L "$destination" ] || { [ -e "$destination" ] && [ ! -d "$destination" ]; }; then
  printf 'existing corpus seal destination is unsafe: %s\n' "$destination" >&2
  exit 1
elif [ -d "$destination" ]; then
  destination_exists=true
fi

# Creation alone reads the mutable historical paths.  Recovery is deliberately
# verify-only: once the no-replace seal directory exists, the original corpus
# and reports may be absent.  The fresh verifier below checks the sealed copies
# themselves against all fifteen literal data/report anchors.
if [ "$destination_exists" = false ]; then
  for report in "$dataset_attestation" "$token_audit" "$runtime_smoke"; do
    if [ ! -f "$report" ] || [ -L "$report" ] || [ "$(stat -c '%h' "$report")" -ne 1 ]; then
      printf 'historical preparation report is not one regular single-link file: %s\n' \
        "$report" >&2
      exit 1
    fi
  done
  test "$(sha256sum "$dataset_attestation" | awk '{print $1}')" = \
    "$expected_dataset_attestation_sha256"
  test "$(sha256sum "$token_audit" | awk '{print $1}')" = \
    "$expected_token_audit_sha256"
  test "$(sha256sum "$runtime_smoke" | awk '{print $1}')" = \
    "$expected_runtime_smoke_sha256"

  if [ ! -d "$artifact_dir" ] || [ -L "$artifact_dir" ]; then
    printf 'historical corpus is not one non-symlink directory: %s\n' \
      "$artifact_dir" >&2
    exit 1
  fi
  mapfile -t observed_artifacts < <(
    find "$artifact_dir" -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort
  )
  if [ "${#observed_artifacts[@]}" -ne "${#artifact_names[@]}" ]; then
    printf 'historical corpus does not have exactly twelve artifacts\n' >&2
    exit 1
  fi
  for index in "${!artifact_names[@]}"; do
    artifact_name="${artifact_names[$index]}"
    test "${observed_artifacts[$index]}" = "$artifact_name"
    artifact_path="$artifact_dir/$artifact_name"
    test -f "$artifact_path"
    test ! -L "$artifact_path"
    test "$(stat -c '%h' "$artifact_path")" -eq 1
    test "$(sha256sum "$artifact_path" | awk '{print $1}')" = \
      "${artifact_hashes[$index]}"
  done
fi
if [ -L "$seal_report" ]; then
  printf 'existing corpus seal report is a symlink: %s\n' "$seal_report" >&2
  exit 1
fi

for source in \
  scripts/seal_peano_v3_corpus.py \
  training/peano_policy/corpus_seal.py; do
  if [ ! -f "$source" ] || [ -L "$source" ]; then
    printf 'reviewed seal source is not one regular file: %s\n' "$source" >&2
    exit 1
  fi
done
test "$(sha256sum scripts/seal_peano_v3_corpus.py | awk '{print $1}')" = \
  "$expected_cli_sha256"
test "$(sha256sum training/peano_policy/corpus_seal.py | awk '{print $1}')" = \
  "$expected_module_sha256"

# Retain a fresh, read-only bootstrap for audit.  It contains exactly three
# directories and two single-link files; the CLI repeats this inventory check.
for retained_parent in logs checkpoints checkpoints/corpora tmp; do
  if [ -L "$retained_parent" ] || \
     { [ -e "$retained_parent" ] && [ ! -d "$retained_parent" ]; }; then
    printf 'retained WMI path is not one non-symlink directory: %s\n' \
      "$retained_parent" >&2
    exit 1
  fi
done
mkdir -p "$project_root/logs" "$project_root/checkpoints/corpora" "$project_root/tmp"
test "$(cd "$project_root/tmp" && pwd -P)" = "$project_root/tmp"

# The retained probe runs beneath the seal parent.  The canonical report uses
# the same no-replace primitive beneath logs, so require both publication
# parents to be on the very same filesystem covered by that probe.
seal_parent_device="$(stat -c '%d' "$project_root/checkpoints/corpora")"
report_parent_device="$(stat -c '%d' "$project_root/logs")"
if [ "$seal_parent_device" != "$report_parent_device" ]; then
  printf 'seal and report publication parents are on different filesystems: %s != %s\n' \
    "$seal_parent_device" "$report_parent_device" >&2
  exit 1
fi

# Exercise both production publication node types on the exact shared
# filesystem used by the seal and its report, then bind one selected profile.
# A same-job requeue verifies the retained report and live probe instead of
# creating another; both paths are reverified immediately before any seal work.
readonly publication_preflight_report="logs/peano-wmi-v3-corpus-seal-publication-preflight-${SLURM_JOB_ID}.json"
if [ -L "$publication_preflight_report" ]; then
  printf 'existing corpus seal publication preflight is a symlink: %s\n' \
    "$publication_preflight_report" >&2
  exit 1
elif [ -e "$publication_preflight_report" ]; then
  "$wmi_python" scripts/preflight_recovery_publication.py verify \
    --report "$publication_preflight_report"
else
  "$wmi_python" scripts/preflight_recovery_publication.py run \
    --probe-root "$project_root/checkpoints/corpora" \
    --report "$publication_preflight_report"
fi
publication_preflight_summary="$(
  "$wmi_python" scripts/preflight_recovery_publication.py verify \
    --report "$publication_preflight_report"
)"
publication_profile="$(
  "$wmi_python" -I -c \
    'import json,sys; print(json.loads(sys.argv[1])["publication_profile"])' \
    "$publication_preflight_summary"
)"
case "$publication_profile" in
  native-no-replace-rename-v1|exclusive-type-matched-claim-rename-v1) ;;
  *)
    printf 'unrecognized publication profile: %s\n' "$publication_profile" >&2
    exit 1
    ;;
esac
readonly publication_profile

bootstrap_root="$(
  mktemp -d "$project_root/tmp/peano-v3-seal-bootstrap-${SLURM_JOB_ID}.XXXXXX"
)"
test -d "$bootstrap_root"
test ! -L "$bootstrap_root"
mkdir -m 0700 "$bootstrap_root/scripts"
mkdir -m 0700 "$bootstrap_root/training"
mkdir -m 0700 "$bootstrap_root/training/peano_policy"
install -m 0444 scripts/seal_peano_v3_corpus.py \
  "$bootstrap_root/scripts/seal_peano_v3_corpus.py"
install -m 0444 training/peano_policy/corpus_seal.py \
  "$bootstrap_root/training/peano_policy/corpus_seal.py"
test "$(stat -c '%h' "$bootstrap_root/scripts/seal_peano_v3_corpus.py")" -eq 1
test "$(stat -c '%h' "$bootstrap_root/training/peano_policy/corpus_seal.py")" -eq 1
chmod 0555 \
  "$bootstrap_root/scripts" \
  "$bootstrap_root/training/peano_policy" \
  "$bootstrap_root/training" \
  "$bootstrap_root"
printf 'retained bootstrap: %s\n' "$bootstrap_root"

unset PYTHONHOME PYTHONPATH PYTHONSTARTUP
anchor_arguments=(
  --dataset-manifest-sha256 "$expected_manifest_sha256"
  --dataset-attestation-sha256 "$expected_dataset_attestation_sha256"
  --token-audit-sha256 "$expected_token_audit_sha256"
  --runtime-smoke-sha256 "$expected_runtime_smoke_sha256"
)
for index in "${!artifact_names[@]}"; do
  artifact_name="${artifact_names[$index]}"
  anchor_arguments+=(
    --artifact-sha256 "$artifact_name=${artifact_hashes[$index]}"
  )
done

run_seal_cli() {
  "$wmi_python" -I -B -S - \
    "$bootstrap_root" \
    "$expected_cli_sha256" \
    "$expected_module_sha256" \
    "$@" <<'PEANO_CORPUS_SEAL_LAUNCHER'
# PEANO_CORPUS_SEAL_LAUNCHER_BEGIN
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"Peano v3 corpus seal launcher failed: {message}")


def identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def stable_single_link_source(path: Path) -> bytes:
    if not hasattr(os, "O_NOFOLLOW"):
        fail("this platform cannot open the staged CLI without following links")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
    try:
        before = os.lstat(path)
        descriptor = os.open(path, flags)
    except OSError as exc:
        fail(f"cannot open staged CLI {path}: {exc}")
    try:
        opened = os.fstat(descriptor)
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or before.st_nlink != 1
            or opened.st_nlink != 1
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            fail(f"staged CLI is not one stable regular single-link file: {path}")
        chunks = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = os.lstat(path)
    except OSError as exc:
        fail(f"staged CLI disappeared after reading: {path}: {exc}")
    if (
        identity(before) != identity(opened)
        or identity(opened) != identity(after_open)
        or identity(after_open) != identity(after_path)
    ):
        fail(f"staged CLI changed while being read: {path}")
    return b"".join(chunks)


if not (
    sys.flags.isolated
    and sys.flags.ignore_environment
    and sys.flags.no_site
    and sys.dont_write_bytecode
):
    fail("requires python -I -B -S")
if len(sys.argv) < 5:
    fail("requires ROOT CLI_SHA256 MODULE_SHA256 and a CLI command")

root_text, cli_sha256, module_sha256, *cli_arguments = sys.argv[1:]
if (
    not root_text.startswith("/")
    or os.path.abspath(root_text) != root_text
    or ".." in Path(root_text).parts
):
    fail("bootstrap root must be one absolute traversal-free path")
for label, digest in (("CLI", cli_sha256), ("module", module_sha256)):
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        fail(f"{label} digest must be one lowercase SHA-256 value")

root = Path(root_text)
try:
    root_stat = os.lstat(root)
except OSError as exc:
    fail(f"cannot inspect bootstrap root {root}: {exc}")
if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
    fail("bootstrap root must be one non-symlink directory")

cli_path = root / "scripts" / "seal_peano_v3_corpus.py"
cli_source = stable_single_link_source(cli_path)
actual_sha256 = hashlib.sha256(cli_source).hexdigest()
if actual_sha256 != cli_sha256:
    fail(
        f"staged CLI digest mismatch: expected {cli_sha256}, got {actual_sha256}"
    )

sys.argv = [
    str(cli_path),
    "--standalone-root",
    str(root),
    "--standalone-cli-sha256",
    cli_sha256,
    "--standalone-module-sha256",
    module_sha256,
    *cli_arguments,
]
namespace = {
    "__name__": "__main__",
    "__file__": str(cli_path),
    "__package__": "",
    "__cached__": None,
    "__loader__": None,
    "__spec__": None,
}
code = compile(
    cli_source,
    str(cli_path),
    "exec",
    dont_inherit=True,
    optimize=0,
)
exec(code, namespace)
# PEANO_CORPUS_SEAL_LAUNCHER_END
PEANO_CORPUS_SEAL_LAUNCHER
}

if [ "$destination_exists" = false ]; then
  run_seal_cli create \
    --artifact-dir "$artifact_dir" \
    --dataset-attestation "$dataset_attestation" \
    --token-audit "$token_audit" \
    --runtime-smoke "$runtime_smoke" \
    --destination "$destination" \
    --source-commit "$historical_source_commit" \
    --prepare-job-id "$historical_prepare_job" \
    --publication-profile "$publication_profile" \
    "${anchor_arguments[@]}"
fi
verify_output="$(
  run_seal_cli verify \
    --seal "$destination" \
    --source-commit "$historical_source_commit" \
    --prepare-job-id "$historical_prepare_job" \
    "${anchor_arguments[@]}"
)"
report_output="$(
  run_seal_cli report \
    --seal "$destination" \
    --report "$seal_report" \
    --source-commit "$historical_source_commit" \
    --prepare-job-id "$historical_prepare_job" \
    --publisher-job-id "$SLURM_JOB_ID" \
    --publication-profile "$publication_profile" \
    "${anchor_arguments[@]}"
)"
test -n "$verify_output"
test -n "$report_output"
printf 'Peano v3 corpus seal verified: %s\n' "$destination"
