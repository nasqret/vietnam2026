#!/usr/bin/env bash
# One AP095 attempt after the audited AP094 proof; preserve both failed jobs.
set -euo pipefail
if [ "$#" != 4 ] || [ "$2" != --submit ] || [ "$3" != --confirm ] || [ "$4" != AP095-FULL-V1 ]; then
  echo "usage: $0 SNAPSHOT.tar --submit --confirm AP095-FULL-V1" >&2; exit 2
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
ledger="$root/authorization-AP095-full-v1"
exec 8>"$root/.submission.lock"
flock -x 8
[ "$(timeout 10s sacct -n -X -j 284694 --format=JobIDRaw,State,ExitCode -P)" = '284694|FAILED|1:0' ]
[ "$(timeout 10s sacct -n -X -j 284696 --format=JobIDRaw,State,ExitCode -P)" = '284696|FAILED|1:0' ]
[ ! -e "$ledger" ] && [ ! -e "$stage" ]
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot" ]
python3 - "$incoming" "$stage" "$root" <<'EXTRACT'
import hashlib,json,pathlib,sys,tarfile
archive,destination,root=map(pathlib.Path,sys.argv[1:])
prior=root/'8661c34d98d55bfd2239a9c03a9eb7ec6f77f83b9256296d4d5ecca8584bd532'
obs=pathlib.Path('source/research/arithmetic-library/sqrt2-power/observations')
for folder,digest in (
    ('shared-wave-exp-log-root-half-transport-v1','d3a7c127b6ac9f241009ab6faefeff6c80ba0342c01fbbf26582f9e8dfcc4864'),
    ('shared-wave-exp-log-root-half-transport-lean-wmi-v1','91c0c82efa1f01eb37d46049d239fe20937aff9edc42833b3a6e84e6d5983c9d')):
    if hashlib.sha256((prior/obs/folder/'report.json').read_bytes()).hexdigest()!=digest:
        raise ValueError('AP094 successful HA/Lean receipt changed')
with tarfile.open(archive,'r:') as handle:
    members=handle.getmembers();names=set();total=0
    for member in members:
        p=pathlib.PurePosixPath(member.name)
        if (not member.isfile() or p.is_absolute() or '..' in p.parts or str(p)!=member.name
                or member.name in names or (p.parts[0] not in {'source','lean'} and member.name!='snapshot-manifest.json')
                or not 0<=member.size<=32*1024**2):raise ValueError('unsafe archive member')
        names.add(member.name);total+=member.size
    if not members or total>128*1024**2 or len(members)>3000:raise ValueError('snapshot boundary exceeded')
    raw=handle.extractfile(str(obs/'exp-log-root-half-transport-wmi-progress-audit-v1.json')).read()
    if hashlib.sha256(raw).hexdigest()!='aeeb8dea61b9808dc291f50d18d94f155906194a84c7e1758bd03aa2128ff5c1':
        raise ValueError('AP094 combined audit changed')
    receipt=json.loads(raw)
    if receipt['case']!='AP094' or receipt['status']!='passed' or not receipt['original_installer_failure_preserved']:
        raise ValueError('AP094 not accepted by its exact combined audit')
    destination.mkdir(mode=0o700);handle.extractall(destination)
EXTRACT
python=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
"$python" -B "$stage/source/scripts/package_sqrt2_power_wmi.py" --verify "$stage"
script="$stage/source/slurm/peano_wmi_sqrt2_ap095.sbatch"
args=(--partition=cpu,cpu_idle --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4096M
  --time=00:30:00 --no-requeue --chdir="$stage/source" --output="$stage/slurm-%j.out" --error="$stage/slurm-%j.err")
sbatch --test-only "${args[@]}" "$script" "$stage" "$snapshot"
mkdir "$ledger"
printf '%s\n' "$snapshot" > "$ledger/snapshot.txt"
printf '%s\n' "$(date -Is)" > "$ledger/requested-at.txt"
printf '%s\n' 284694 284696 > "$ledger/predecessor-job-ids.txt"
job="$(sbatch --hold --parsable "${args[@]}" "$script" "$stage" "$snapshot")"
job="${job%%;*}"
[[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > "$ledger/job-id.txt"
printf '%s\t%s\t%s\n' "$(date -Is)" "$job" "$snapshot" > "$stage/submission.tsv"
scontrol release "$job"
printf 'job_id=%s\nsnapshot_sha256=%s\n' "$job" "$snapshot"
REMOTE
