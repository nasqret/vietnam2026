#!/bin/bash -l
# PREPARED ONLY. Root submits this script ONCE, held, with the exact reserved
# job name/comment/time, no requeue, one GH200/node, 8 CPUs and 64 GiB.
# Arguments: extracted project root, fresh bound job directory, clean base view.
# This body never allocates, submits, downloads, retries or resumes a job.
set -euo pipefail
set -C
umask 077

if [[ "$#" -ne 3 || ! "${SLURM_JOB_ID-}" =~ ^[0-9]{1,20}$ ]]; then
  printf '%s\n' 'Run only inside the exact root-owned Slurm allocation with three explicit paths.' >&2
  exit 64
fi
readonly HYDRA_P7_BUNDLE="$1"
readonly HYDRA_P7_JOB="$2"
readonly HYDRA_P7_BASE="$3"
readonly HYDRA_P7_PYTHON='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python'

for HYDRA_P7_DIRECTORY in "$HYDRA_P7_BUNDLE" "$HYDRA_P7_JOB" "$HYDRA_P7_BASE"; do
  [[ "$HYDRA_P7_DIRECTORY" == /* && -d "$HYDRA_P7_DIRECTORY" ]]
done
[[ ! -e "$HYDRA_P7_JOB/result" && ! -e "$HYDRA_P7_JOB/actual-process-exit.txt" ]]
[[ ! -e "$HYDRA_P7_JOB/reservation.json.claimed" ]]
read -r HYDRA_P7_SELECTION_SHA < "$HYDRA_P7_JOB/selection.sha256"
read -r HYDRA_P7_SOURCE_SHA < "$HYDRA_P7_JOB/source-pins.sha256"
read -r HYDRA_P7_RESERVATION_SHA < "$HYDRA_P7_JOB/reservation.sha256"
for HYDRA_P7_SHA in "$HYDRA_P7_SELECTION_SHA" "$HYDRA_P7_SOURCE_SHA" "$HYDRA_P7_RESERVATION_SHA"; do
  [[ "$HYDRA_P7_SHA" =~ ^[0-9a-f]{64}$ ]]
done

module purge
module load ML-bundle/25.10
unset PYTHONPATH
export PYTHONHASHSEED=20260904
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1
cd "$HYDRA_P7_BUNDLE"

# The P7 controller delegates actual live scheduler validation to the unchanged
# reviewed P6 parser. It expects Comment=hydra-p6:<nonce>; schema/model and the
# exclusive one-use reservation claim are P7-specific. No model loads before it.
# Do not add -P here: the parent's staged sibling provider must be importable.
set +e
"$HYDRA_P7_PYTHON" -B "$HYDRA_P7_BUNDLE/output/p7-prototype/staged/teacher_campaign.py" run \
  --app-root "$HYDRA_P7_BUNDLE/hydra-playground" \
  --selection "$HYDRA_P7_JOB/selection.json" \
  --selection-sha256 "$HYDRA_P7_SELECTION_SHA" \
  --source-pins-sha256 "$HYDRA_P7_SOURCE_SHA" \
  --reservation "$HYDRA_P7_JOB/reservation.json" \
  --reservation-sha256 "$HYDRA_P7_RESERVATION_SHA" \
  --base-directory "$HYDRA_P7_BASE" \
  --output "$HYDRA_P7_JOB/result"
HYDRA_P7_ACTUAL_EXIT=$?
set -e
printf '%s\n' "$HYDRA_P7_ACTUAL_EXIT" > "$HYDRA_P7_JOB/actual-process-exit.txt"
exit "$HYDRA_P7_ACTUAL_EXIT"
