#!/usr/bin/env bash
# Execute Hydra Alpha training only inside an existing reviewed WMI allocation.
# This script never synchronizes sources, submits a Slurm job, or bypasses the
# separate clean-source/guarded-submission workflow.
set -euo pipefail

if [[ ! "${SLURM_JOB_ID:-}" =~ ^[0-9]+$ ]]; then
  printf 'Hydra GPU execution requires an existing WMI Slurm allocation\n' >&2
  exit 2
fi

if [[ "$#" -gt 1 ]]; then
  printf 'usage: %s [_deploy/hydra-posttrain]\n' "$0" >&2
  exit 2
fi

hydra_preparation_dir="${1:-_deploy/hydra-posttrain}"

# shellcheck source=wmi_job_environment.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/wmi_job_environment.sh"
peano_wmi_activate_base
peano_wmi_verify_base_manifest
hydra_wmi_python="$(peano_wmi_current_python)"
peano_wmi_assert_runtime "$hydra_wmi_python"

# Must be set before the target interpreter starts; the runner independently
# rejects every other seed, multiple devices, and distributed execution.
export PYTHONHASHSEED=20260826
exec "$hydra_wmi_python" -m training.peano_hydra.posttrain \
  --execute \
  --preparation-dir "$hydra_preparation_dir"
