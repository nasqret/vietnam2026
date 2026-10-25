#!/bin/bash -l
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --hint=nomultithread
#SBATCH --job-name=peano-wmi-v2-accept-score
#SBATCH --open-mode=append
#SBATCH --output=logs/peano-wmi-v2-accept-score-%j.out
#SBATCH --error=logs/peano-wmi-v2-accept-score-%j.err

set -euo pipefail
exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock
flock -s 8
peano_wmi_job_env="${SLURM_SUBMIT_DIR:?}/scripts/wmi_job_environment.sh"
export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh
export PEANO_JOB_ENV_SHA256="$(sha256sum "$peano_wmi_job_env" | awk '{print $1}')"
source "$peano_wmi_job_env"
PYTHONPYCACHEPREFIX="$(mktemp -d \
  "${SLURM_TMPDIR:-/tmp}/peano-pycache-${SLURM_JOB_ID:?}.XXXXXX")"
export PYTHONPYCACHEPREFIX
peano_wmi_activate_base
export PEANO_JOB_SCRIPT=slurm/peano_wmi_acceptance_scorer.sbatch
wmi_python="$(peano_wmi_current_python)"
"$wmi_python" -m pip check

final_report=results/peano-policy/qwen3-1.7b-lora-v2-heavy/acceptance-v2-report.json
set +e
"$wmi_python" scripts/peano_policy_acceptance.py report \
  --adapter-dir results/peano-policy/qwen3-1.7b-lora-v2-heavy \
  --data-dir data/peano-policy-v2 \
  --heldout-report results/peano-policy/qwen3-1.7b-lora-v2-heavy/heldout-search-wmi-b16-c8-d32.json \
  --output "$final_report"
status=$?
set -e
case "$status" in
  0|1)
    [ -f "$final_report" ] && [ ! -L "$final_report" ] || {
      printf 'scorer did not publish one regular final report\n' >&2
      exit 2
    }
    "$wmi_python" scripts/peano_policy_acceptance.py verify-report \
      --adapter-dir results/peano-policy/qwen3-1.7b-lora-v2-heavy \
      --data-dir data/peano-policy-v2 \
      --heldout-report results/peano-policy/qwen3-1.7b-lora-v2-heavy/heldout-search-wmi-b16-c8-d32.json \
      --output "$final_report" \
      >/dev/null
    exit 0
    ;;
  *) exit "$status" ;;
esac
