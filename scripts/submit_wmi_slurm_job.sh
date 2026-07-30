#!/usr/bin/env bash
# WMI-side guarded Slurm submission with an append-before-release ledger.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

usage() {
  echo "usage: $0 [--test-only] [--afterok JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
  echo "       $0 --submit --confirm $PEANO_WMI_CONFIRM_TOKEN [--afterok JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
}

mode=--test-only
confirmation=""
afterok=""
request_id=""
job_script=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only) mode=--test-only; shift ;;
    --submit) mode=--submit; shift ;;
    --confirm)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      confirmation="$2"; shift 2
      ;;
    --afterok)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$afterok" ] || { echo "--afterok may appear only once" >&2; exit 2; }
      afterok="$2"; shift 2
      ;;
    --request-id)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$request_id" ] || { echo "--request-id may appear only once" >&2; exit 2; }
      request_id="$2"; shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    --*) printf 'unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
    *)
      [ -z "$job_script" ] || { echo "only one job script is allowed" >&2; exit 2; }
      job_script="$1"; shift
      ;;
  esac
done

[ "$(pwd -P)" = "$PEANO_WMI_PROJECT_ROOT" ] || {
  printf 'unexpected WMI project root: %s\n' "$(pwd -P)" >&2
  exit 2
}
exec 8>.deployment.lock
flock -s 8
[ -n "$job_script" ] || { usage; exit 2; }
peano_wmi_validate_script_name "$job_script"
[ -z "$request_id" ] || peano_wmi_validate_request_id "$request_id" || {
  printf 'invalid --request-id: %s\n' "$request_id" >&2
  exit 2
}
if [ "$job_script" = slurm/peano_wmi_prove_theorem.sbatch ]; then
  [ -n "$request_id" ] || { echo "WMI theorem proof requires --request-id" >&2; exit 2; }
elif [ -n "$request_id" ]; then
  echo "--request-id is valid only for the WMI theorem-proof job" >&2
  exit 2
fi
[ -f "$job_script" ] && [ ! -L "$job_script" ] || {
  printf 'WMI job script is not one regular file: %s\n' "$job_script" >&2
  exit 2
}
[ -z "$afterok" ] || peano_wmi_validate_single_job_id "$afterok" || {
  printf 'invalid --afterok job id: %s\n' "$afterok" >&2
  exit 2
}
expected_predecessor="$(peano_wmi_expected_predecessor "$job_script" || true)"
if [ -n "$expected_predecessor" ]; then
  [ -n "$afterok" ] || { echo "WMI train/eval requires --afterok JOB_ID" >&2; exit 2; }
elif [ -n "$afterok" ]; then
  echo "this WMI job must not have a dependency" >&2
  exit 2
fi

sbatch_args=()
[ -z "$afterok" ] || sbatch_args+=("--dependency=afterok:$afterok")
case "$job_script" in
  slurm/peano_wmi_train_qwen3_1_7b.sbatch|\
  slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch|\
  slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch)
    sbatch_args+=("--export=ALL,PEANO_PREPARE_JOB_ID=$afterok")
    ;;
  slurm/peano_wmi_eval_qwen3_1_7b.sbatch|\
  slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch|\
  slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch|\
  slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch)
    sbatch_args+=("--export=ALL,PEANO_TRAIN_JOB_ID=$afterok")
    ;;
  slurm/peano_wmi_prove_theorem.sbatch)
    sbatch_args+=("--export=ALL,PEANO_PROOF_REQUEST_ID=$request_id")
    ;;
esac
request_sha256=""
if [ -n "$request_id" ]; then
  request_path="results/peano-policy/requests/$request_id.json"
  [ -f "$request_path" ] && [ ! -L "$request_path" ] || {
    printf 'missing regular WMI proof request: %s\n' "$request_path" >&2
    exit 1
  }
  python3 scripts/peano_policy_proof_request.py verify \
    --request-id "$request_id" >/dev/null
  request_sha256="$(sha256sum "$request_path" | awk '{print $1}')"
fi
if [ "$mode" = --test-only ]; then
  [ -z "$confirmation" ] || { echo "--confirm is only valid with --submit" >&2; exit 2; }
  exec sbatch --test-only "${sbatch_args[@]}" "$job_script"
fi
if [ "$confirmation" != "$PEANO_WMI_CONFIRM_TOKEN" ]; then
  echo "real WMI submission requires: --submit --confirm $PEANO_WMI_CONFIRM_TOKEN" >&2
  exit 2
fi

source_provenance=.peano-source-provenance.tsv
[ -f "$source_provenance" ] && [ ! -L "$source_provenance" ] || {
  echo "missing WMI source provenance" >&2
  exit 1
}
[ "$(wc -l < "$source_provenance")" -eq 1 ] || {
  echo "WMI source provenance must contain exactly one row" >&2
  exit 1
}
IFS=$'\t' read -r commit git_dirty sync_timestamp extra < "$source_provenance"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]] || [ "$git_dirty" != false ] || \
   [[ ! "$sync_timestamp" =~ ^[0-9TZ:-]+$ ]] || [ -n "${extra:-}" ]; then
  echo "WMI source provenance is malformed or dirty" >&2
  exit 1
fi

manifest=logs/submissions.tsv
lock=logs/submissions.lock
header='timestamp\tjob_id\tscript\tdependency_job_id\tworkdir\tgit_commit\tgit_dirty\tsync_timestamp\tscript_sha256'
mkdir -p logs
umask 077
exec 9>"$lock"
flock -x 9
if [ ! -f "$manifest" ]; then
  printf '%b\n' "$header" > "$manifest"
elif [ "$(sed -n '1p' "$manifest")" != "$(printf '%b' "$header")" ]; then
  echo "submission manifest has an incompatible header" >&2
  exit 1
fi
proof_manifest=logs/proof-requests.tsv
proof_header='timestamp\tjob_id\trequest_id\trequest_sha256'
if [ -n "$request_id" ]; then
  if [ ! -f "$proof_manifest" ]; then
    printf '%b\n' "$proof_header" > "$proof_manifest"
  elif [ "$(sed -n '1p' "$proof_manifest")" != "$(printf '%b' "$proof_header")" ]; then
    echo "WMI proof-request manifest has an incompatible header" >&2
    exit 1
  fi
fi

if [ -n "$afterok" ]; then
  expected_predecessor_hash="$(sha256sum "$expected_predecessor" | awk '{print $1}')"
  support_hash="$(sha256sum scripts/wmi_job_environment.sh | awk '{print $1}')"
  expected_predecessor_hash="$({
    printf '%s\n' "$expected_predecessor_hash"
    printf '%s\n' "$support_hash"
  } | sha256sum | awk '{print $1}')"
  if ! python3 scripts/verify_wmi_submission_predecessor.py \
      "$manifest" "$afterok" "$expected_predecessor" \
      "$PEANO_WMI_PROJECT_ROOT" "$commit" "$sync_timestamp" \
      "$expected_predecessor_hash"; then
    echo "WMI dependency is absent or belongs to a different chain" >&2
    exit 1
  fi
  if ! predecessor_states="$(
    sacct -n -X -j "$afterok" --format=State -P
  )"; then
    echo "cannot verify the WMI predecessor state" >&2
    exit 1
  fi
  predecessor_state="$(printf '%s\n' "$predecessor_states" | sed -n '1p')"
  predecessor_state="${predecessor_state%%+*}"
  case "$job_script:$predecessor_state" in
    slurm/peano_wmi_train_qwen3_1_7b.sbatch:COMPLETED|\
    slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch:COMPLETED|\
    slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch:COMPLETED|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:PENDING|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:CONFIGURING|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:RUNNING|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:COMPLETING|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:COMPLETED|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:PENDING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:CONFIGURING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:RUNNING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:COMPLETING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:COMPLETED|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:PENDING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:CONFIGURING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:RUNNING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:COMPLETING|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:COMPLETED|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:PENDING|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:CONFIGURING|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:RUNNING|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:COMPLETING|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:COMPLETED)
      ;;
    *)
      printf 'WMI predecessor %s is not in an acceptable state: %s\n' \
        "$afterok" "$predecessor_state" >&2
      exit 1
      ;;
  esac
  if [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b.sbatch ] || \
     [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch ] || \
     [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch ]; then
    if [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch ]; then
      eligibility_report="logs/peano-wmi-v3-sealed-eligibility-$afterok.json"
      token_report="logs/peano-wmi-v3-token-audit-$afterok.json"
      smoke_report="logs/peano-wmi-v3-prepare-runtime-$afterok.json"
      for report in "$eligibility_report" "$token_report" "$smoke_report"; do
        [ -f "$report" ] && [ ! -L "$report" ] || {
          printf 'missing regular WMI v3 preparation report: %s\n' "$report" >&2
          exit 1
        }
      done
      environment_pointer=.venv-wmi/current
      [ -f "$environment_pointer" ] && [ ! -L "$environment_pointer" ] && \
        [ "$(wc -l < "$environment_pointer")" -eq 1 ] || {
        echo "missing reviewed WMI environment pointer" >&2
        exit 1
      }
      environment_id="$(sed -n '1p' "$environment_pointer")"
      [[ "$environment_id" =~ ^[0-9a-f]{64}$ ]] || {
        echo "malformed reviewed WMI environment pointer" >&2
        exit 1
      }
      verifier_python=".venv-wmi/releases/$environment_id/bin/python"
      [ -x "$verifier_python" ] || {
        echo "reviewed WMI verifier Python is unavailable" >&2
        exit 1
      }
      "$verifier_python" scripts/verify_wmi_v3_sealed_preparation.py \
        --eligibility-report "$eligibility_report" \
        --token-audit-report "$token_report" \
        --smoke-report "$smoke_report" \
        --prepare-job-id "$afterok" >/dev/null
      smoke_report=""
    elif [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch ]; then
      smoke_report="logs/peano-wmi-v2-prepare-runtime-$afterok.json"
      data_report="logs/peano-wmi-v2-dataset-attestation-$afterok.json"
      smoke_format=peano-policy-wmi-a100-v2-smoke
    else
      smoke_report="logs/peano-wmi-prepare-runtime-$afterok.json"
      data_report="logs/peano-wmi-dataset-attestation-$afterok.json"
      smoke_format=peano-policy-wmi-a100-smoke
    fi
    if [ -n "$smoke_report" ]; then
      for report in "$smoke_report" "$data_report"; do
        [ -f "$report" ] && [ ! -L "$report" ] || {
          printf 'missing regular WMI preparation report: %s\n' "$report" >&2
          exit 1
        }
      done
      python3 - "$smoke_report" "$afterok" "$smoke_format" <<'PY'
import json
from pathlib import Path
import sys

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if (
    report.get("format") != sys.argv[3]
    or report.get("status") != "passed"
    or report.get("job", {}).get("job_id") != sys.argv[2]
):
    raise SystemExit("WMI preparation smoke report is not an accepted predecessor")
PY
    fi
  fi
fi

if ! queue="$(squeue -h --me -o '%A|%j|%T')"; then
  echo "cannot verify active WMI jobs; refusing submission" >&2
  exit 1
fi
while IFS='|' read -r active_job_id active_name active_state; do
  case "$active_name" in
    peano-wmi-prepare|peano-wmi-qwen17|peano-wmi-qwen17-eval|\
    peano-wmi-v2-prepare|peano-wmi-qwen17-v2|peano-wmi-qwen17-v2-eval|\
    peano-wmi-v3-prepare|peano-wmi-qwen17-v3|peano-wmi-qwen17-v3-eval|\
    peano-wmi-v3-seal|peano-wmi-v3-sealprep|peano-wmi-qwen17-v3-base|\
    peano-wmi-prove|peano-wmi-probe)
      if [ -z "$afterok" ] || [ "$active_job_id" != "$afterok" ]; then
        printf 'another WMI Peano job is active: %s %s %s\n' \
          "$active_job_id" "$active_name" "$active_state" >&2
        exit 1
      fi
      ;;
  esac
done <<< "$queue"

support_script=scripts/wmi_job_environment.sh
[ -f "$support_script" ] && [ ! -L "$support_script" ] || {
  echo "missing regular WMI job environment helper" >&2
  exit 1
}
job_file_sha256="$(sha256sum "$job_script" | awk '{print $1}')"
support_sha256="$(sha256sum "$support_script" | awk '{print $1}')"
script_sha256="$({
  printf '%s\n' "$job_file_sha256"
  printf '%s\n' "$support_sha256"
} | sha256sum | awk '{print $1}')"
timestamp="$(date -Is)"
held_job=""
cancel_held() {
  if [[ "$held_job" =~ ^[0-9]+$ ]]; then
    scancel "$held_job" || true
  fi
}
trap cancel_held EXIT
submission="$(sbatch --hold --parsable "${sbatch_args[@]}" "$job_script")"
held_job="${submission%%;*}"
if [[ ! "$held_job" =~ ^[0-9]+$ ]]; then
  printf 'sbatch returned an invalid job id: %s\n' "$submission" >&2
  exit 1
fi
printf '%s\t%s\t%s\t%s\t%s\t%s\tfalse\t%s\t%s\n' \
  "$timestamp" "$held_job" "$job_script" "$afterok" "$PEANO_WMI_PROJECT_ROOT" \
  "$commit" "$sync_timestamp" "$script_sha256" >> "$manifest"
sync -f "$manifest"
if [ -n "$request_id" ]; then
  printf '%s\t%s\t%s\t%s\n' \
    "$timestamp" "$held_job" "$request_id" "$request_sha256" >> "$proof_manifest"
  sync -f "$proof_manifest"
fi
scontrol release "$held_job"
printf 'submitted job_id=%s\n' "$held_job"
printf 'manifest=%s\n' "$manifest"
held_job=""
trap - EXIT
