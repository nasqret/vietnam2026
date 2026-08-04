#!/bin/bash -l
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32768M
#SBATCH --time=04:00:00
#SBATCH --job-name=peano-k3b-cell
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-k3b-cell-%j.out
#SBATCH --error=logs/peano-k3b-cell-%j.err

set -euo pipefail

run_root="${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
cd "$run_root"

[[ "${PEANO_K3B_PAYLOAD_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
[[ "${PEANO_K3B_LOCAL_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
case "${PEANO_K3B_LOCAL_DIRTY:-}" in
  true|false) ;;
  *) echo "invalid PEANO_K3B_LOCAL_DIRTY" >&2; exit 2 ;;
esac
case "${PEANO_K3B_REQUESTED_PARTITION:-}" in
  cpu_idle) ;;
  *) echo "K3B closure requires cpu_idle" >&2; exit 2 ;;
esac
for positive_resource in \
  PEANO_K3B_REQUESTED_NODES \
  PEANO_K3B_REQUESTED_NTASKS \
  PEANO_K3B_REQUESTED_CPUS_PER_TASK \
  PEANO_K3B_REQUESTED_MEMORY_MIB \
  PEANO_K3B_REQUESTED_TIME_LIMIT_SECONDS
do
  [[ "${!positive_resource:-}" =~ ^[1-9][0-9]*$ ]] || {
    printf 'invalid %s\n' "$positive_resource" >&2
    exit 2
  }
done
[[ "${PEANO_K3B_REQUESTED_TIME_LIMIT:-}" =~ ^([0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]
[ "$PEANO_K3B_REQUESTED_NODES" = 1 ]
[ "$PEANO_K3B_REQUESTED_NTASKS" = 1 ]
[ "$PEANO_K3B_REQUESTED_CPUS_PER_TASK" = 1 ]
[ "$PEANO_K3B_REQUESTED_MEMORY_MIB" = 32768 ]
[ "$PEANO_K3B_REQUESTED_TIME_LIMIT" = 04:00:00 ]
[ "$PEANO_K3B_REQUESTED_TIME_LIMIT_SECONDS" = 14400 ]

# Validate the allocation Slurm actually exported, independently of the
# caller-supplied provenance fields above.
[ "${SLURM_JOB_PARTITION:-}" = cpu_idle ]
[ "${SLURM_JOB_NUM_NODES:-}" = 1 ]
[ "${SLURM_NTASKS:-}" = 1 ]
[ "${SLURM_CPUS_PER_TASK:-}" = 1 ]
[ "${SLURM_MEM_PER_NODE:-}" = 32768 ]

passes="${PEANO_K3B_PASSES:-2}"
[[ "$passes" =~ ^[1-9][0-9]*$ ]] && [ "$passes" -le 16 ] || {
  echo "PEANO_K3B_PASSES must be in 1..16" >&2
  exit 2
}
selection="${PEANO_K3B_THEOREMS:-all}"
arguments=(--passes "$passes")
if [ "$selection" != all ]; then
  IFS=, read -r -a requested_theorems <<< "$selection"
  [ "${#requested_theorems[@]}" -gt 0 ]
  for theorem in "${requested_theorems[@]}"; do
    case "$theorem" in
      cell_history_nil|cell_history_extend|cell_history_succ_elim|\
      cell_history_extend_preserves_prefix|\
      cell_list_zero_iff_nil|cell_list_succ_iff_cell|\
      cell_list_length_functional|cell_list_length_le_code|\
      cell_list_length_total|list_at_domain|list_at_head_iff|\
      list_at_succ_iff|list_at_external_bound|list_at_exists|\
      list_at_functional|list_at_history_independent|\
      cell_list_extensional)
        arguments+=(--theorem "$theorem")
        ;;
      *) printf 'invalid K3B theorem: %s\n' "$theorem" >&2; exit 2 ;;
    esac
  done
fi

export PYTHONHASHSEED=20260804
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONOPTIMIZE
export PYTHONPATH="$run_root/peano-lab/py:$run_root"

python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ] || {
  printf 'missing reviewed WMI Python: %s\n' "$python_path" >&2
  exit 1
}
mkdir -p logs results
report="results/peano-k3b-cell-history-closure-${SLURM_JOB_ID}.json"
[ ! -e "$report" ] && [ ! -L "$report" ] || {
  printf 'refusing existing report: %s\n' "$report" >&2
  exit 1
}

printf 'payload_sha256=%s\n' "$PEANO_K3B_PAYLOAD_SHA256"
printf 'local_commit=%s\n' "$PEANO_K3B_LOCAL_COMMIT"
printf 'local_dirty=%s\n' "$PEANO_K3B_LOCAL_DIRTY"
printf 'theorems=%s\n' "$selection"
printf 'passes=%s\n' "$passes"
printf 'resources=cpu_idle,1-node,1-task,1-cpu,32768-MiB,04:00:00\n'
printf 'host=%s\n' "$(hostname)"
"$python_path" --version
"$python_path" scripts/run_wmi_k3b_cell_history_closure.py \
  "${arguments[@]}" --report "$report"
sha256sum "$report"
