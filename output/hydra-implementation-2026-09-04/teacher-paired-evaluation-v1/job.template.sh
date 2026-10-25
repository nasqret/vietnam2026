#!/bin/bash -l
# Prepared body only. Root must bind/review an actual held allocation, reconcile
# the full campaign charge, and observe successful CPU admission before release.
set -euo pipefail
umask 077
: "${HYDRA_TEACHER_SOURCE:?Bind the exact new derived source root}"
: "${HYDRA_TEACHER_JOB:?Bind the owned new job directory}"
: "${HYDRA_TEACHER_STUDY_SHA:?Bind the admitted study byte hash}"
module purge
module load ML-bundle/25.10
unset PYTHONPATH PYTHONHOME
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
cd "$HYDRA_TEACHER_SOURCE"
read -r HYDRA_TEACHER_RESERVATION_SHA < "$HYDRA_TEACHER_JOB/reservation.sha256"
set +e
/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/.venv-helios/bin/python -B \
  "$HYDRA_TEACHER_SOURCE/output/hydra-implementation-2026-09-04/teacher-paired-evaluation-v1/paired_controller.py" \
  --app-root "$HYDRA_TEACHER_SOURCE/hydra-playground" \
  --study "$HYDRA_TEACHER_JOB/study.json" --study-sha256 "$HYDRA_TEACHER_STUDY_SHA" \
  --reservation "$HYDRA_TEACHER_JOB/reservation.json" --reservation-sha256 "$HYDRA_TEACHER_RESERVATION_SHA" \
  --output "$HYDRA_TEACHER_JOB/result"
HYDRA_TEACHER_ACTUAL_EXIT=$?
set -C
printf '%s\n' "$HYDRA_TEACHER_ACTUAL_EXIT" > "$HYDRA_TEACHER_JOB/actual-process-exit.txt"
exit "$HYDRA_TEACHER_ACTUAL_EXIT"
