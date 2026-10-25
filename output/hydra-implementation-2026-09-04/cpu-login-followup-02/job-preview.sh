#!/bin/bash -l
set -eu
umask 077
export PATH=/net/slurm/releases/production.el9.x86_64/bin:"$PATH"
command -v scontrol > /net/exact-job/selected-scontrol.txt
set +e
/usr/bin/timeout 5 /net/slurm/releases/production.el8.x86_64/bin/scontrol --version > /net/exact-job/old-client.stdout.txt 2> /net/exact-job/old-client.stderr.txt
HYDRA_CLIENT_DIAGNOSTIC_EXIT=$?
printf '%s\n' "$HYDRA_CLIENT_DIAGNOSTIC_EXIT" > /net/exact-job/old-client.actual-exit.txt
set -e
exec /bin/bash /net/exact-source/output/control/remote_cpu_job.sh /net/exact-source /net/exact-job
