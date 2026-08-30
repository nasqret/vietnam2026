#!/usr/bin/env bash
# WMI-side guarded Slurm submission with an append-before-release ledger.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wmi_common.sh
source "$script_dir/wmi_common.sh"

usage() {
  echo "usage: $0 [--test-only] [--afterok JOB_ID | --completed-predecessor JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
  echo "       $0 --submit --confirm $PEANO_WMI_CONFIRM_TOKEN [--afterok JOB_ID | --completed-predecessor JOB_ID] [--request-id ID] slurm/wmi-job.sbatch" >&2
}

mode=--test-only
confirmation=""
predecessor_job_id=""
predecessor_mode=""
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
      [ -z "$predecessor_job_id" ] || { echo "only one predecessor option is allowed" >&2; exit 2; }
      predecessor_job_id="$2"; predecessor_mode=afterok; shift 2
      ;;
    --completed-predecessor)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$predecessor_job_id" ] || { echo "only one predecessor option is allowed" >&2; exit 2; }
      predecessor_job_id="$2"; predecessor_mode=completed; shift 2
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
[ -z "$predecessor_job_id" ] || peano_wmi_validate_single_job_id "$predecessor_job_id" || {
  printf 'invalid predecessor job id: %s\n' "$predecessor_job_id" >&2
  exit 2
}
expected_predecessor="$(peano_wmi_expected_predecessor "$job_script" || true)"
if [ -n "$expected_predecessor" ]; then
  [ -n "$predecessor_job_id" ] || { echo "WMI train/eval requires a predecessor job" >&2; exit 2; }
  peano_wmi_validate_predecessor_mode "$job_script" "$predecessor_mode" || {
    echo "WMI training requires --completed-predecessor; evaluation accepts it or --afterok" >&2
    exit 2
  }
elif [ -n "$predecessor_job_id" ]; then
  echo "this WMI job must not have a predecessor" >&2
  exit 2
fi

sbatch_args=()
case "$job_script" in
  slurm/peano_wmi_train_qwen3_1_7b.sbatch|\
  slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch|\
  slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch)
    sbatch_args+=("--export=ALL,PEANO_PREPARE_JOB_ID=$predecessor_job_id")
    ;;
  slurm/peano_wmi_eval_qwen3_1_7b.sbatch|\
  slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch|\
  slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch|\
  slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch)
    sbatch_args+=("--export=ALL,PEANO_TRAIN_JOB_ID=$predecessor_job_id")
    ;;
  slurm/peano_wmi_prove_theorem.sbatch)
    sbatch_args+=("--export=ALL,PEANO_PROOF_REQUEST_ID=$request_id")
    ;;
esac
scheduler_dependency_arg=""
verify_predecessor_accounting() {
  local raw_record parsed_record predecessor_state exit_code derived_exit_code extra
  scheduler_dependency_arg=""
  if ! raw_record="$(
    sacct -n -X -j "$predecessor_job_id" \
      --format=JobIDRaw,State,ExitCode,DerivedExitCode -P
  )"; then
    echo "cannot verify the WMI predecessor accounting record" >&2
    return 1
  fi
  if ! parsed_record="$(
    peano_wmi_parse_predecessor_accounting "$predecessor_job_id" "$raw_record"
  )"; then
    printf 'WMI predecessor %s has no unique canonical accounting row\n' \
      "$predecessor_job_id" >&2
    return 1
  fi
  IFS='|' read -r predecessor_state exit_code derived_exit_code extra \
    <<< "$parsed_record"
  if [ -n "${extra:-}" ]; then
    echo "internal WMI predecessor-accounting parse failure" >&2
    return 1
  fi
  if ! scheduler_dependency_arg="$(
    peano_wmi_scheduler_dependency_argument \
      "$predecessor_mode" "$predecessor_state" "$exit_code" \
      "$derived_exit_code" "$predecessor_job_id"
  )"; then
    if [ "$predecessor_mode" = afterok ] && \
       [ "$predecessor_state" = COMPLETED ] && \
       [ "$exit_code" = 0:0 ] && [ "$derived_exit_code" = 0:0 ]; then
      printf 'WMI predecessor %s is complete; use --completed-predecessor\n' \
        "$predecessor_job_id" >&2
    else
      printf 'WMI predecessor %s is not admissible in %s mode: %s %s %s\n' \
        "$predecessor_job_id" "$predecessor_mode" "$predecessor_state" \
        "$exit_code" "$derived_exit_code" >&2
    fi
    return 1
  fi
}
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
  if [ -n "$predecessor_job_id" ]; then
    verify_predecessor_accounting
    [ -z "$scheduler_dependency_arg" ] || \
      sbatch_args+=("$scheduler_dependency_arg")
  fi
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

if [ -n "$predecessor_job_id" ]; then
  expected_predecessor_hash="$(sha256sum "$expected_predecessor" | awk '{print $1}')"
  support_hash="$(sha256sum scripts/wmi_job_environment.sh | awk '{print $1}')"
  expected_predecessor_hash="$({
    printf '%s\n' "$expected_predecessor_hash"
    printf '%s\n' "$support_hash"
  } | sha256sum | awk '{print $1}')"
  if ! python3 scripts/verify_wmi_submission_predecessor.py \
      "$manifest" "$predecessor_job_id" "$expected_predecessor" \
      "$PEANO_WMI_PROJECT_ROOT" "$commit" "$sync_timestamp" \
      "$expected_predecessor_hash"; then
    echo "WMI predecessor is absent or belongs to a different chain" >&2
    exit 1
  fi
  verify_predecessor_accounting
  if [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b.sbatch ] || \
     [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch ] || \
     [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch ]; then
    if [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch ]; then
      eligibility_report="logs/peano-wmi-v3-sealed-eligibility-$predecessor_job_id.json"
      token_report="logs/peano-wmi-v3-token-audit-$predecessor_job_id.json"
      smoke_report="logs/peano-wmi-v3-prepare-runtime-$predecessor_job_id.json"
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
        --prepare-job-id "$predecessor_job_id" >/dev/null
      smoke_report=""
    elif [ "$job_script" = slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch ]; then
      smoke_report="logs/peano-wmi-v2-prepare-runtime-$predecessor_job_id.json"
      data_report="logs/peano-wmi-v2-dataset-attestation-$predecessor_job_id.json"
      smoke_format=peano-policy-wmi-a100-v2-smoke
    else
      smoke_report="logs/peano-wmi-prepare-runtime-$predecessor_job_id.json"
      data_report="logs/peano-wmi-dataset-attestation-$predecessor_job_id.json"
      smoke_format=peano-policy-wmi-a100-smoke
    fi
    if [ -n "$smoke_report" ]; then
      for report in "$smoke_report" "$data_report"; do
        [ -f "$report" ] && [ ! -L "$report" ] || {
          printf 'missing regular WMI preparation report: %s\n' "$report" >&2
          exit 1
        }
      done
      python3 - "$smoke_report" "$predecessor_job_id" "$smoke_format" <<'PY'
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
      if [ -z "$predecessor_job_id" ] || [ "$active_job_id" != "$predecessor_job_id" ]; then
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
if [ -n "$predecessor_job_id" ]; then
  # Re-read accounting immediately before submission.  In live mode a state
  # transition is rejected rather than silently dropping the scheduler edge.
  verify_predecessor_accounting
  [ -z "$scheduler_dependency_arg" ] || \
    sbatch_args+=("$scheduler_dependency_arg")
fi
submission="$(sbatch --hold --parsable "${sbatch_args[@]}" "$job_script")"
held_job="${submission%%;*}"
if [[ ! "$held_job" =~ ^[0-9]+$ ]]; then
  printf 'sbatch returned an invalid job id: %s\n' "$submission" >&2
  exit 1
fi
printf '%s\t%s\t%s\t%s\t%s\t%s\tfalse\t%s\t%s\n' \
  "$timestamp" "$held_job" "$job_script" "$predecessor_job_id" "$PEANO_WMI_PROJECT_ROOT" \
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
