#!/bin/bash -l
#SBATCH --partition=cpu_idle
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32768M
#SBATCH --time=06:00:00
#SBATCH --job-name=peano-bertrand-v3
#SBATCH --open-mode=append
# A submission wrapper may override these with paths in a pre-created run
# directory. Direct submission must not depend on a directory created later.
#SBATCH --output=/dev/null
#SBATCH --error=/dev/null

set -euo pipefail

run_root="${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
cd "$run_root"

[[ "${SLURM_JOB_ID:-}" =~ ^[1-9][0-9]*$ ]]
[ "${SLURM_JOB_NAME:-}" = peano-bertrand-v3 ]
[[ "${SLURM_CLUSTER_NAME:-}" =~ ^[^[:cntrl:]]+$ ]]
[[ "${SLURM_JOB_NODELIST:-}" =~ ^[^[:cntrl:]]+$ ]]

[[ "${PEANO_BERTRAND_PAYLOAD_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]
[[ "${PEANO_BERTRAND_LOCAL_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
[ "${PEANO_BERTRAND_LOCAL_DIRTY:-}" = false ] || {
  echo "Bertrand closure requires a clean committed payload" >&2
  exit 2
}
case "${PEANO_BERTRAND_REQUESTED_PARTITION:-}" in
  cpu_idle) ;;
  *) echo "Bertrand closure requires cpu_idle" >&2; exit 2 ;;
esac
for positive_resource in \
  PEANO_BERTRAND_REQUESTED_NODES \
  PEANO_BERTRAND_REQUESTED_NTASKS \
  PEANO_BERTRAND_REQUESTED_CPUS_PER_TASK \
  PEANO_BERTRAND_REQUESTED_MEMORY_MIB \
  PEANO_BERTRAND_REQUESTED_TIME_LIMIT_SECONDS
do
  [[ "${!positive_resource:-}" =~ ^[1-9][0-9]*$ ]] || {
    printf 'invalid %s\n' "$positive_resource" >&2
    exit 2
  }
done
[[ "${PEANO_BERTRAND_REQUESTED_TIME_LIMIT:-}" =~ ^([0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]
[ "$PEANO_BERTRAND_REQUESTED_NODES" = 1 ]
[ "$PEANO_BERTRAND_REQUESTED_NTASKS" = 1 ]
[ "$PEANO_BERTRAND_REQUESTED_CPUS_PER_TASK" = 1 ]
[ "$PEANO_BERTRAND_REQUESTED_MEMORY_MIB" = 32768 ]
[ "$PEANO_BERTRAND_REQUESTED_TIME_LIMIT" = 06:00:00 ]
[ "$PEANO_BERTRAND_REQUESTED_TIME_LIMIT_SECONDS" = 21600 ]

# Bind the actual Slurm allocation independently from the requested profile.
[ "${SLURM_JOB_PARTITION:-}" = cpu_idle ]
[ "${SLURM_JOB_NUM_NODES:-}" = 1 ]
[ "${SLURM_NTASKS:-}" = 1 ]
[ "${SLURM_CPUS_PER_TASK:-}" = 1 ]
[ "${SLURM_MEM_PER_NODE:-}" = 32768 ]

selection="${PEANO_BERTRAND_THEOREMS:-all}"
arguments=(--passes 2 --execution-mode wmi-slurm)
if [ "$selection" != all ]; then
  IFS=, read -r -a requested_theorems <<< "$selection"
  [ "${#requested_theorems[@]}" -gt 0 ]
  for theorem in "${requested_theorems[@]}"; do
    case "$theorem" in
      prime_strictly_above_decidable|bounded_prime_interval_search|\
      prime_interval_exclusion_refutes_witness|bounded_prime_interval_decidable|\
      mul_le_mul|le_mul_of_one_le_right|le_mul_of_one_le_left|pow_base_monotone|\
      one_le_pow|pow_nonzero_of_one_le|pow_exponent_monotone|\
      power_divides_decidable|power_divides_zero|\
      bounded_power_valuation_search|bounded_power_valuation_exists|\
      power_valuation_exists|power_valuation_functional|\
      power_valuation_power_divides|power_valuation_dominates|\
      prime_power_valuation_exists|prime_power_valuation_functional)
        arguments+=(--theorem "$theorem")
        ;;
      *) printf 'invalid Bertrand theorem: %s\n' "$theorem" >&2; exit 2 ;;
    esac
  done
fi

export PYTHONHASHSEED=20260809
export PEANO_CLUSTER_BACKEND=wmi
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONOPTIMIZE
export PYTHONPATH="$run_root/peano-lab/py:$run_root"

python_path=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python_path" ] || {
  printf 'missing reviewed WMI Python: %s\n' "$python_path" >&2
  exit 1
}
[ -f schemas/peano-bertrand-alpha-v3-cold-closure-v2.schema.json ]
mkdir -p logs results
report="results/peano-bertrand-alpha-v3-closure-${SLURM_JOB_ID}.json"
[ ! -e "$report" ] && [ ! -L "$report" ] || {
  printf 'refusing existing report: %s\n' "$report" >&2
  exit 1
}

printf 'payload_sha256=%s\n' "$PEANO_BERTRAND_PAYLOAD_SHA256"
printf 'local_commit=%s\n' "$PEANO_BERTRAND_LOCAL_COMMIT"
printf 'local_dirty=false\n'
printf 'theorems=%s\n' "$selection"
printf 'passes=2\n'
printf 'execution_mode=wmi-slurm\n'
printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
printf 'slurm_cluster=%s\n' "$SLURM_CLUSTER_NAME"
printf 'resources=cpu_idle,1-node,1-task,1-cpu,32768-MiB,06:00:00\n'
printf 'host=%s\n' "$(hostname)"
"$python_path" --version
"$python_path" scripts/run_bertrand_alpha_v3_cold_closure.py \
  "${arguments[@]}" --report "$report"
sha256sum "$report"
