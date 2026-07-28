#!/usr/bin/env bash
# Shared, deliberately small constants and validators for Helios control tools.

readonly PEANO_HELIOS_DEFAULT_SSH_TARGET="plgnasqret@helios.cyfronet.pl"
readonly PEANO_HELIOS_GRANT="plgccaiautore2026"
readonly PEANO_HELIOS_CPU_ACCOUNT="plgccaiautore2026-cpu"
readonly PEANO_HELIOS_GPU_ACCOUNT="plgccaiautore2026-gpu-gh200"
readonly PEANO_HELIOS_PROJECT_SUFFIX="codex-control/projects/peano-lab-training"
readonly PEANO_HELIOS_CONFIRM_TOKEN="PEANO-LAB-TRAINING"

peano_helios_ssh_target() {
  local target="${HELIOS_SSH_TARGET:-$PEANO_HELIOS_DEFAULT_SSH_TARGET}"
  if [[ ! "$target" =~ ^[A-Za-z0-9._-]+(@[A-Za-z0-9.-]+)?$ ]]; then
    printf 'invalid HELIOS_SSH_TARGET: %s\n' "$target" >&2
    return 2
  fi
  printf '%s\n' "$target"
}

peano_helios_validate_job_id() {
  [[ "$1" =~ ^[0-9][0-9_,.%:-]*$ ]]
}

peano_helios_validate_single_job_id() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

peano_helios_requires_dependency() {
  case "$1" in
    slurm/peano_gpu_gh200_smoke.sbatch|\
    slurm/peano_train_qwen3_1_7b.sbatch|\
    slurm/peano_eval_qwen3_1_7b.sbatch)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

peano_helios_validate_script_name() {
  local script="$1"
  case "$script" in
    slurm/*.sbatch) ;;
    *)
      printf 'job script must be a relative slurm/*.sbatch path: %s\n' "$script" >&2
      return 2
      ;;
  esac
  if [[ "$script" == *".."* || "$script" == *"//"* || ! "$script" =~ ^[A-Za-z0-9._/-]+$ ]]; then
    printf 'unsafe job script path: %s\n' "$script" >&2
    return 2
  fi
}
