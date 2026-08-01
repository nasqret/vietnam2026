#!/usr/bin/env bash
# Fixed constants and conservative validators for WMI control tools.

readonly PEANO_WMI_DEFAULT_SSH_TARGET="wmicluster"
readonly PEANO_WMI_PROJECT_ROOT="/work/bnaskrecki/peano-lab-training"
readonly PEANO_WMI_CONFIRM_TOKEN="PEANO-LAB-WMI-TRAINING"

peano_wmi_ssh_target() {
  local target="${WMI_SSH_TARGET:-$PEANO_WMI_DEFAULT_SSH_TARGET}"
  if [[ "$target" == -* ]] || \
     [[ ! "$target" =~ ^[A-Za-z0-9._-]+(@[A-Za-z0-9.-]+)?$ ]]; then
    printf 'invalid WMI_SSH_TARGET: %s\n' "$target" >&2
    return 2
  fi
  printf '%s\n' "$target"
}

peano_wmi_validate_single_job_id() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

peano_wmi_validate_job_id_list() {
  [[ "$1" =~ ^[0-9][0-9_,.%:-]*$ ]]
}

peano_wmi_validate_request_id() {
  [[ "$1" =~ ^[0-9a-f]{64}$ ]]
}

# Parse the one exact allocation row requested from sacct with:
#   --format=JobIDRaw,State,ExitCode,DerivedExitCode -P
# Step rows, arrays, duplicate rows, truncation, and malformed exit codes are
# rejected rather than guessed at.
peano_wmi_parse_predecessor_accounting() {
  local expected_job_id="$1"
  local record="$2"
  peano_wmi_validate_single_job_id "$expected_job_id" || return 1
  if [[ "$record" =~ ^${expected_job_id}\|([A-Z_]+)\|([0-9]+:[0-9]+)\|([0-9]+:[0-9]+)$ ]]; then
    printf '%s|%s|%s\n' \
      "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
    return 0
  fi
  return 1
}

# Print a scheduler dependency argument only for a predecessor that is still
# live.  A completed predecessor is instead authenticated by sacct, the
# immutable submission ledger, and its terminal reports; Slurm rejects a new
# afterok edge once MinJobAge has expired.
peano_wmi_scheduler_dependency_argument() {
  local mode="$1"
  local state="$2"
  local exit_code="$3"
  local derived_exit_code="$4"
  local job_id="$5"
  peano_wmi_validate_single_job_id "$job_id" || return 1
  [ "$exit_code" = 0:0 ] && [ "$derived_exit_code" = 0:0 ] || return 1
  case "$mode:$state" in
    completed:COMPLETED)
      return 0
      ;;
    afterok:PENDING|afterok:CONFIGURING|afterok:RUNNING|afterok:COMPLETING)
      printf '%s\n' "--dependency=afterok:$job_id"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

peano_wmi_validate_predecessor_mode() {
  local job_script="$1"
  local mode="$2"
  case "$job_script:$mode" in
    slurm/peano_wmi_train_qwen3_1_7b.sbatch:completed|\
    slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch:completed|\
    slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch:completed|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:afterok|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch:completed|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:afterok|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch:completed|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:afterok|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch:completed|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:afterok|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch:completed)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

peano_wmi_validate_script_name() {
  case "$1" in
    slurm/peano_wmi_a100_probe.sbatch|\
    slurm/peano_wmi_prepare_training.sbatch|\
    slurm/peano_wmi_train_qwen3_1_7b.sbatch|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch|\
    slurm/peano_wmi_prepare_v2_training.sbatch|\
    slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch|\
    slurm/peano_wmi_seal_v3_corpus.sbatch|\
    slurm/peano_wmi_prepare_v3_sealed_training.sbatch|\
    slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch|\
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch|\
    slurm/peano_wmi_prove_theorem.sbatch)
      return 0
      ;;
    *)
      printf 'job script is not in the WMI allowlist: %s\n' "$1" >&2
      return 2
      ;;
  esac
}

peano_wmi_expected_predecessor() {
  case "$1" in
    slurm/peano_wmi_train_qwen3_1_7b.sbatch)
      printf '%s\n' slurm/peano_wmi_prepare_training.sbatch
      ;;
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch)
      printf '%s\n' slurm/peano_wmi_train_qwen3_1_7b.sbatch
      ;;
    slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch)
      printf '%s\n' slurm/peano_wmi_prepare_v2_training.sbatch
      ;;
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch)
      printf '%s\n' slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch
      ;;
    slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch)
      printf '%s\n' slurm/peano_wmi_prepare_v3_sealed_training.sbatch
      ;;
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch)
      printf '%s\n' slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch
      ;;
    slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch)
      printf '%s\n' slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch
      ;;
    *)
      return 1
      ;;
  esac
}
