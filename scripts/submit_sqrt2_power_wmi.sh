#!/usr/bin/env bash
# One explicitly approved AP090 pilot, isolated source, held-before-ledger job.
set -euo pipefail
if [ "$#" != 4 ] || [ "$2" != --submit ] || [ "$3" != --confirm ] || [ "$4" != SQRT2-AP090-WMI-V2 ]; then
  echo "usage: $0 SNAPSHOT.tar --submit --confirm SQRT2-AP090-WMI-V2" >&2
  exit 2
fi
archive="$1"
[ -f "$archive" ] && [ ! -L "$archive" ]
snapshot="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
readonly remote_root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
ssh_options=(-T -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no
  -o ConnectTimeout=15 -o ConnectionAttempts=1 -o ServerAliveInterval=10
  -o ServerAliveCountMax=3 -o ClearAllForwardings=yes)
incoming="$remote_root/incoming-$snapshot.tar"
# noclobber avoids destroying any interrupted earlier upload. Such a collision
# is a stop condition, never a reason to delete an existing remote artifact.
ssh "${ssh_options[@]}" wmicluster \
  "umask 077; mkdir -p '$remote_root'; set -C; cat > '$incoming'" < "$archive"
ssh "${ssh_options[@]}" wmicluster "bash -s -- $snapshot" <<'REMOTE'
set -euo pipefail
snapshot="${1:?}"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
incoming="$root/incoming-$snapshot.tar"
stage="$root/$snapshot"
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot" ]
exec 8>"$root/.submission.lock"
flock -x 8
# Preserve the consumed first request and bind this separately approved
# replacement to its exact terminal preflight failure. Never erase a ledger.
prior=6385ec7eed50950238b44b2d6194f04da13f11fab4c6cdf669cc4b388c453472
[ "$(sed -n '1p' "$root/authorization-AP090-v1/job-id.txt")" = 257867 ]
[ "$(sed -n '1p' "$root/authorization-AP090-v1/snapshot.txt")" = "$prior" ]
accounting="$(timeout 10s sacct -n -X -j 257867 --format=JobIDRaw,State,ExitCode -P)"
[ "$accounting" = '257867|FAILED|1:0' ]
prior_report="$root/$prior/evidence/pilot-report.json"
[ "$(sha256sum "$prior_report" | awk '{print $1}')" = 3fc4c9fa9135e60108675c6764b64007a5a8da490e9ecb4e5517e0d0887b9009 ]
python3 - "$prior_report" <<'PREDECESSOR'
import json,sys
with open(sys.argv[1]) as stream: report=json.load(stream)
if (report['job_id']!='257867' or report['full_attempt_started'] is not False
        or report['status']!='failed_or_incomplete'):
    raise ValueError('predecessor does not establish an unused AP090 attempt')
PREDECESSOR
[ ! -e "$root/$prior/evidence/AP090-attempt-started.json" ]
[ ! -e "$root/authorization-AP090-v2" ]
[ ! -e "$stage" ]
python3 - "$incoming" "$stage" <<'EXTRACT'
import pathlib, sys, tarfile
archive, destination = map(pathlib.Path, sys.argv[1:])
with tarfile.open(archive, 'r:') as handle:
    members = handle.getmembers()
    names = set()
    total = 0
    for member in members:
        path = pathlib.PurePosixPath(member.name)
        if (not member.isfile() or path.is_absolute() or '..' in path.parts
                or str(path) != member.name or member.name in names
                or (path.parts[0] not in {'source', 'lean'} and member.name != 'snapshot-manifest.json')
                or member.size < 0 or member.size > 32*1024**2):
            raise ValueError('unsafe source archive member')
        names.add(member.name)
        total += member.size
    if not members or total > 128*1024**2 or len(members) > 3000:
        raise ValueError('source archive boundary exceeded')
    destination.mkdir(mode=0o700)
    handle.extractall(destination)
EXTRACT
python=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python" ]
"$python" -B "$stage/source/scripts/package_sqrt2_power_wmi.py" --verify "$stage"
script="$stage/source/slurm/peano_wmi_sqrt2_pilot.sbatch"
args=(--partition=cpu_idle --nodes=1 --ntasks=1 --cpus-per-task=1
  --mem=4096M --time=00:45:00 --no-requeue --chdir="$stage/source"
  --output="$stage/slurm-%j.out" --error="$stage/slurm-%j.err")
sbatch --test-only "${args[@]}" "$script" "$stage" "$snapshot"
mkdir "$root/authorization-AP090-v2"
printf '%s\n' "$snapshot" > "$root/authorization-AP090-v2/snapshot.txt"
printf '%s\n' "$(date -Is)" > "$root/authorization-AP090-v2/requested-at.txt"
printf '%s\n' 257867 > "$root/authorization-AP090-v2/predecessor-job-id.txt"
submission="$(sbatch --hold --parsable "${args[@]}" "$script" "$stage" "$snapshot")"
job_id="${submission%%;*}"
[[ "$job_id" =~ ^[0-9]+$ ]]
printf '%s\n' "$job_id" > "$root/authorization-AP090-v2/job-id.txt"
printf '%s\t%s\t%s\n' "$(date -Is)" "$job_id" "$snapshot" > "$stage/submission.tsv"
# A failed release leaves an identifiable held job; it never submits another.
scontrol release "$job_id"
printf 'job_id=%s\nsnapshot_sha256=%s\nremote_stage=%s\n' "$job_id" "$snapshot" "$stage"
REMOTE
