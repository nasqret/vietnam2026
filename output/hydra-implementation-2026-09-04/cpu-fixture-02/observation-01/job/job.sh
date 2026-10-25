#!/bin/bash -l
set -eu
umask 077
export PATH=/net/slurm/releases/production.el9.x86_64/bin:"$PATH"
command -v scontrol > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/cpu-fixture-02/selected-scontrol.txt
set +e
/usr/bin/timeout 5 /net/slurm/releases/production.el8.x86_64/bin/scontrol --version > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/cpu-fixture-02/old-client.stdout.txt 2> /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/cpu-fixture-02/old-client.stderr.txt
HYDRA_CLIENT_DIAGNOSTIC_EXIT=$?
printf '%s\n' "$HYDRA_CLIENT_DIAGNOSTIC_EXIT" > /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/cpu-fixture-02/old-client.actual-exit.txt
set -e
exec /bin/bash /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-01/source/output/hydra-implementation-2026-09-04/cpu-fixture-control-v1/remote_cpu_job.sh /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-01/source /net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/cpu-fixture-02
