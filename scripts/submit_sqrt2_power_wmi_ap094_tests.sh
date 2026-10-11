#!/usr/bin/env bash
# One changed-strategy AP094 test-only follow-up; retain the failed pip record.
set -euo pipefail
if [ "$#" != 4 ] || [ "$2" != --submit ] || [ "$3" != --confirm ] || [ "$4" != AP094-TESTS-V1 ]; then
  echo "usage: $0 SNAPSHOT.tar --submit --confirm AP094-TESTS-V1" >&2; exit 2
fi
archive="$1"
[ -f "$archive" ] && [ ! -L "$archive" ]
snapshot="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
ssh_options=(-T -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no
  -o ConnectTimeout=15 -o ClearAllForwardings=yes -o ServerAliveInterval=10 -o ServerAliveCountMax=3)
ssh "${ssh_options[@]}" wmicluster "umask 077; set -C; cat > '$root/incoming-$snapshot.tar'" < "$archive"
ssh "${ssh_options[@]}" wmicluster "bash -s -- $snapshot" <<'REMOTE'
set -euo pipefail
snapshot="${1:?}"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
stage="$root/$snapshot";incoming="$root/incoming-$snapshot.tar"
ledger="$root/authorization-AP094-tests-v1"
exec 8>"$root/.submission.lock"
flock -x 8
[ "$(timeout 10s sacct -n -X -j 284694 --format=JobIDRaw,State,ExitCode -P)" = '284694|FAILED|1:0' ]
[ ! -e "$ledger" ] && [ ! -e "$stage" ]
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot" ]
python3 - "$incoming" "$stage" "$root" <<'EXTRACT'
import hashlib,json,pathlib,sys,tarfile
archive,destination,root=map(pathlib.Path,sys.argv[1:])
prior=root/'8661c34d98d55bfd2239a9c03a9eb7ec6f77f83b9256296d4d5ecca8584bd532'
report=json.loads((prior/'evidence/pilot-report.json').read_bytes())
if report['status']!='failed_or_incomplete' or report['job_id']!='284694':raise ValueError('original AP094 run changed')
if report['exception']['message']!='failed bounded phase: offline-test-dependencies' or report['processes']['offline-test-dependencies']['reason']!='unexpected_descendant':raise ValueError('different failed phase')
if report['ha']['status']!='fresh_ordinary_HA_checked' or report['lean']['status']!='fresh_lean_checked':raise ValueError('proof gates did not pass')
ha=prior/'source/research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-v1/report.json'
if hashlib.sha256(ha.read_bytes()).hexdigest()!='d3a7c127b6ac9f241009ab6faefeff6c80ba0342c01fbbf26582f9e8dfcc4864':raise ValueError('AP094 HA receipt changed')
lean=prior/'source/research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-lean-wmi-v1/report.json'
if hashlib.sha256(lean.read_bytes()).hexdigest()!='91c0c82efa1f01eb37d46049d239fe20937aff9edc42833b3a6e84e6d5983c9d':raise ValueError('AP094 Lean receipt changed')
with tarfile.open(archive,'r:') as handle:
    members=handle.getmembers();names=set();total=0
    for member in members:
        p=pathlib.PurePosixPath(member.name)
        if (not member.isfile() or p.is_absolute() or '..' in p.parts or str(p)!=member.name
                or member.name in names or (p.parts[0] not in {'source','lean'} and member.name!='snapshot-manifest.json')
                or not 0<=member.size<=32*1024**2):raise ValueError('unsafe archive member')
        names.add(member.name);total+=member.size
    if not members or total>128*1024**2 or len(members)>3000:raise ValueError('snapshot boundary exceeded')
    destination.mkdir(mode=0o700);handle.extractall(destination)
EXTRACT
python=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
"$python" -B "$stage/source/scripts/package_sqrt2_power_wmi.py" --verify "$stage"
script="$stage/source/slurm/peano_wmi_sqrt2_ap094_tests.sbatch"
args=(--partition=cpu,cpu_idle --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4096M
  --time=00:45:00 --no-requeue --chdir="$stage/source" --output="$stage/slurm-%j.out" --error="$stage/slurm-%j.err")
sbatch --test-only "${args[@]}" "$script" "$stage" "$snapshot"
mkdir "$ledger"
printf '%s\n' "$snapshot" > "$ledger/snapshot.txt"
printf '%s\n' "$(date -Is)" > "$ledger/requested-at.txt"
printf '%s\n' 284694 > "$ledger/predecessor-job-id.txt"
job="$(sbatch --hold --parsable "${args[@]}" "$script" "$stage" "$snapshot")"
job="${job%%;*}"
[[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > "$ledger/job-id.txt"
printf '%s\t%s\t%s\n' "$(date -Is)" "$job" "$snapshot" > "$stage/submission.tsv"
scontrol release "$job"
printf 'job_id=%s\nsnapshot_sha256=%s\n' "$job" "$snapshot"
REMOTE
