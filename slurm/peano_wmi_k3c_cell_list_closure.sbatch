#!/bin/bash -l
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32768M
#SBATCH --time=04:00:00
#SBATCH --job-name=peano-k3c-cell
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-k3c-cell-%j.out
#SBATCH --error=logs/peano-k3c-cell-%j.err

set -euo pipefail

run_root="${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
cd "$run_root"

[[ "${PEANO_K3C_PAYLOAD_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
[[ "${PEANO_K3C_LOCAL_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
case "${PEANO_K3C_LOCAL_DIRTY:-}" in
  true|false) ;;
  *) echo "invalid PEANO_K3C_LOCAL_DIRTY" >&2; exit 2 ;;
esac
case "${PEANO_K3C_REQUESTED_PARTITION:-}" in
  cpu_idle) ;;
  *) echo "K3C closure requires cpu_idle" >&2; exit 2 ;;
esac
for positive_resource in \
  PEANO_K3C_REQUESTED_NODES \
  PEANO_K3C_REQUESTED_NTASKS \
  PEANO_K3C_REQUESTED_CPUS_PER_TASK \
  PEANO_K3C_REQUESTED_MEMORY_MIB \
  PEANO_K3C_REQUESTED_TIME_LIMIT_SECONDS
do
  [[ "${!positive_resource:-}" =~ ^[1-9][0-9]*$ ]] || {
    printf 'invalid %s\n' "$positive_resource" >&2
    exit 2
  }
done
[[ "${PEANO_K3C_REQUESTED_TIME_LIMIT:-}" =~ ^([0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]
[ "$PEANO_K3C_REQUESTED_NODES" = 1 ]
[ "$PEANO_K3C_REQUESTED_NTASKS" = 1 ]
[ "$PEANO_K3C_REQUESTED_CPUS_PER_TASK" = 1 ]
[ "$PEANO_K3C_REQUESTED_MEMORY_MIB" = 32768 ]
[ "$PEANO_K3C_REQUESTED_TIME_LIMIT" = 04:00:00 ]
[ "$PEANO_K3C_REQUESTED_TIME_LIMIT_SECONDS" = 14400 ]

# Independently bind the actual allocation exported by Slurm.
[ "${SLURM_JOB_PARTITION:-}" = cpu_idle ]
[ "${SLURM_JOB_NUM_NODES:-}" = 1 ]
[ "${SLURM_NTASKS:-}" = 1 ]
[ "${SLURM_CPUS_PER_TASK:-}" = 1 ]
[ "${SLURM_MEM_PER_NODE:-}" = 32768 ]

selection="${PEANO_K3C_THEOREMS:-all}"
arguments=(--passes 2)
if [ "$selection" != all ]; then
  IFS=, read -r -a requested_theorems <<< "$selection"
  [ "${#requested_theorems[@]}" -gt 0 ]
  for theorem in "${requested_theorems[@]}"; do
    case "$theorem" in
      cell_list_valid_nil|cell_list_valid_cell_intro|\
      cell_list_valid_cases|cell_list_valid_cell_elim|\
      list_at_implies_cell_list_valid|\
      list_member_implies_cell_list_valid|list_member_nil_false|\
      list_member_cell_intro_head|list_member_cell_intro_tail|\
      list_member_cell_elim|list_member_cell_iff|\
      list_member_pointwise_transport|list_at_exists_unique|\
      cell_list_nonempty_iff_head_exists|\
      cell_list_code_eq_lookup_values|\
      cell_list_code_eq_iff_pointwise|cell_list_decompose_unique)
        arguments+=(--theorem "$theorem")
        ;;
      *) printf 'invalid K3C theorem: %s\n' "$theorem" >&2; exit 2 ;;
    esac
  done
fi

export PYTHONHASHSEED=20260809
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
report="results/peano-k3c-cell-list-closure-${SLURM_JOB_ID}.json"
[ ! -e "$report" ] && [ ! -L "$report" ] || {
  printf 'refusing existing report: %s\n' "$report" >&2
  exit 1
}

printf 'payload_sha256=%s\n' "$PEANO_K3C_PAYLOAD_SHA256"
printf 'local_commit=%s\n' "$PEANO_K3C_LOCAL_COMMIT"
printf 'local_dirty=%s\n' "$PEANO_K3C_LOCAL_DIRTY"
printf 'theorems=%s\n' "$selection"
printf 'passes=2\n'
printf 'resources=cpu_idle,1-node,1-task,1-cpu,32768-MiB,04:00:00\n'
printf 'host=%s\n' "$(hostname)"
"$python_path" --version
"$python_path" scripts/run_wmi_k3c_cell_list_closure.py \
  "${arguments[@]}" --report "$report"
sha256sum "$report"
