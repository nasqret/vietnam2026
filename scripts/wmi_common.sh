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

peano_wmi_validate_script_name() {
  case "$1" in
    slurm/peano_wmi_a100_probe.sbatch|\
    slurm/peano_wmi_prepare_training.sbatch|\
    slurm/peano_wmi_train_qwen3_1_7b.sbatch|\
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch|\
    slurm/peano_wmi_prepare_v2_training.sbatch|\
    slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch|\
    slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch|\
    slurm/peano_wmi_prepare_v3_training.sbatch|\
    slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch|\
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch|\
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
      printf '%s\n' slurm/peano_wmi_prepare_v3_training.sbatch
      ;;
    slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch)
      printf '%s\n' slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch
      ;;
    *)
      return 1
      ;;
  esac
}
