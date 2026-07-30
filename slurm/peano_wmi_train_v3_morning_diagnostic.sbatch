#!/bin/bash -l
#SBATCH --account=bnaskrecki
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=02:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-v3-morning
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-v3-morning-%j.out
#SBATCH --error=logs/peano-v3-morning-%j.err

# Emergency, non-production diagnostic over the exact authenticated bytes from
# historical WMI preparation 173040.  This does not claim the still-unpublished
# production corpus seal and writes only to a unique diagnostics output path.
set -euo pipefail

readonly main_root=/work/bnaskrecki/peano-lab-training
readonly historical_source_commit=5faa3d27cbaf522198ffa1bdcd11fa9d57341658
readonly historical_prepare_job=173040
readonly config=training/peano_policy/configs/qwen3_1_7b_v3_morning_diagnostic_20260731_r1.toml
readonly output_dir="$main_root/results/peano-policy/diagnostics/qwen3-1.7b-lora-v3-morning-diagnostic-20260731-r1"
readonly attestation="$main_root/logs/peano-wmi-v3-dataset-attestation-173040.json"
readonly token_audit="$main_root/logs/peano-wmi-v3-token-audit-173040.json"
readonly runtime_smoke="$main_root/logs/peano-wmi-v3-prepare-runtime-173040.json"
readonly dataset_manifest="$main_root/data/peano-policy-v3/manifest.json"
readonly train_split="$main_root/data/peano-policy-v3/train.jsonl"
readonly eval_split="$main_root/data/peano-policy-v3/val.jsonl"
readonly expected_attestation_sha256=4e1cf0d00725a739d6f371062ff2079cfb9bc3e36daf4f4219cbbe1399a68a12
readonly expected_token_audit_sha256=c290b285eabcf9d39ab13b4d6f0f194588541484390d35c00681041979e2f8d8
readonly expected_runtime_smoke_sha256=86cc35bfcf2d5ff51931c140f3eb7168e3f641e1f80d54a3984dba9e49e40749
readonly expected_manifest_sha256=ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983
readonly expected_train_sha256=626bcf4456efd98eae80828efceb9b89386e6ef83be463251fc1d07b3c2ff15e
readonly expected_eval_sha256=784512bbcb15b3d46fc7333fd3f917fa440d5d1d263385b7d2c16e9a40f0dd27

exec 9>"$main_root/.qwen3-1.7b-v3-morning-diagnostic-20260731-r1.lock"
if ! flock -n 9; then
  printf 'another r1 morning diagnostic owns the output lock\n' >&2
  exit 1
fi
# Lock source first, then the mutable corpus/output root.  Fail immediately
# rather than burn an A100 allocation behind another deployment or Peano job.
# The exclusive main lock prevents any preparation/sync lane from changing the
# unsealed corpus between its hash check and completed adapter publication.
exec 7>"${SLURM_SUBMIT_DIR:?}/.deployment.lock"
if ! flock -n -s 7; then
  printf 'diagnostic source deployment is active; refusing GPU run\n' >&2
  exit 1
fi
exec 8>"$main_root/.deployment.lock"
if ! flock -n -x 8; then
  printf 'main Peano deployment/job is active; refusing GPU run\n' >&2
  exit 1
fi

peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
peano_wmi_activate_base
export PYTHONHASHSEED=20260731
export PEANO_JOB_SCRIPT=slurm/peano_wmi_train_v3_morning_diagnostic.sbatch
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check
peano_wmi_assert_runtime "$wmi_python"
nvidia-smi -L

test -f "$config"
test -d "$main_root/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
if [ -e "$output_dir" ]; then
  printf 'refusing to replace morning diagnostic output: %s\n' "$output_dir" >&2
  exit 1
fi

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
  printf 'historical preparation is not uniquely COMPLETED: rows=%s state=%s\n' \
    "$historical_rows" "$historical_state" >&2
  exit 1
fi

require_hash() {
  local expected="${1:?expected SHA-256 required}"
  local path="${2:?artifact path required}"
  test -f "$path"
  test ! -L "$path"
  local observed
  observed="$(sha256sum "$path" | awk '{print $1}')"
  if [ "$observed" != "$expected" ]; then
    printf 'authenticated artifact changed: %s != %s for %s\n' \
      "$observed" "$expected" "$path" >&2
    exit 1
  fi
}

require_hash "$expected_attestation_sha256" "$attestation"
require_hash "$expected_token_audit_sha256" "$token_audit"
require_hash "$expected_runtime_smoke_sha256" "$runtime_smoke"
require_hash "$expected_manifest_sha256" "$dataset_manifest"
require_hash "$expected_train_sha256" "$train_split"
require_hash "$expected_eval_sha256" "$eval_split"

"$wmi_python" - \
  "$token_audit" \
  "$runtime_smoke" \
  "$historical_prepare_job" \
  "$historical_source_commit" \
  "$main_root" <<'PY'
import json
from pathlib import Path
import sys

audit = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
smoke = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
deployment = smoke.get("job", {}).get("deployment", {})
source_sync = deployment.get("source_sync", {})
submission = smoke.get("job", {}).get("submission", {})
if (
    audit.get("format") != "peano-policy-token-audit"
    or audit.get("status") != "passed"
    or audit.get("config", {}).get("max_length") != 32768
    or audit.get("splits", {}).get("train", {}).get("maximum", 32769) > 32768
    or audit.get("splits", {}).get("eval", {}).get("maximum", 32769) > 32768
):
    raise SystemExit("historical token audit is not admitted")
if (
    smoke.get("format") != "peano-policy-wmi-a100-v3-smoke"
    or smoke.get("status") != "passed"
    or smoke.get("job", {}).get("job_id") != sys.argv[3]
    or smoke.get("model", {}).get("model_commit")
    != "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
    or source_sync.get("git_commit") != sys.argv[4]
    or source_sync.get("git_dirty") is not False
    or source_sync.get("status") != "synced"
    or submission.get("job_id") != sys.argv[3]
    or submission.get("git_commit") != sys.argv[4]
    or submission.get("git_dirty") != "false"
    or submission.get("script") != "slurm/peano_wmi_prepare_v3_training.sbatch"
    or submission.get("workdir") != sys.argv[5]
):
    raise SystemExit("historical A100 runtime smoke is not admitted")
PY

"$wmi_python" -m training.peano_policy.morning_diagnostic \
  --config "$config" \
  --dataset-attestation "$attestation" \
  --dataset-attestation-sha256 "$expected_attestation_sha256" \
  --dataset-manifest-sha256 "$expected_manifest_sha256" \
  --train-sha256 "$expected_train_sha256" \
  --eval-sha256 "$expected_eval_sha256" \
  --historical-source-commit "$historical_source_commit" \
  --historical-prepare-job-id "$historical_prepare_job"

test -f "$output_dir/training-manifest.json"
test -f "$output_dir/morning-diagnostic.json"
test -f "$output_dir/morning-reload-probe.json"
test -f "$output_dir/adapter/adapter_model.safetensors"
test -f "$output_dir/tokenizer/tokenizer.json"
if find "$output_dir" -mindepth 1 -maxdepth 1 -type d -name 'checkpoint-*' | grep -q .; then
  printf 'morning diagnostic published a forbidden Trainer checkpoint\n' >&2
  exit 1
fi
printf 'MORNING_DIAGNOSTIC_READY=%s\n' "$output_dir"
