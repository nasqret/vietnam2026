#!/usr/bin/env bash
# One exact AP093 attempt after accepted AP092; no retry or ledger deletion.
set -euo pipefail
if [ "$#" != 4 ] || [ "$2" != --submit ] || [ "$3" != --confirm ] || [ "$4" != AP093-FULL-V1 ]; then
  echo "usage: $0 SNAPSHOT.tar --submit --confirm AP093-FULL-V1" >&2; exit 2
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
ledger="$root/authorization-AP093-full-v1"
exec 8>"$root/.submission.lock"
flock -x 8
[ "$(timeout 10s sacct -n -X -j 284684 --format=JobIDRaw,State,ExitCode -P)" = '284684|COMPLETED|0:0' ]
[ ! -e "$ledger" ] && [ ! -e "$stage" ]
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot" ]
python3 - "$incoming" "$stage" "$root" <<'EXTRACT'
import hashlib,json,pathlib,sys,tarfile
archive,destination,root=map(pathlib.Path,sys.argv[1:])
prior=root/'9257c94c11d59b1211c4afeff0dc9562469197d0a69a611ab194dcc5ca11ae26'
report=json.loads((prior/'evidence/pilot-report.json').read_bytes())
if report['status']!='HA_Lean_and_regressions_checked' or report['job_id']!='284684':raise ValueError('AP092 did not pass')
ha=prior/'source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-fine-root-v1/report.json'
if hashlib.sha256(ha.read_bytes()).hexdigest()!='894f2e9fee8e423a655bb66d1414982836f7b910a6b46e518ea58909b107896a':raise ValueError('AP092 receipt changed')
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
script="$stage/source/slurm/peano_wmi_sqrt2_ap093.sbatch"
args=(--partition=cpu,cpu_idle --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4096M
  --time=00:45:00 --no-requeue --chdir="$stage/source" --output="$stage/slurm-%j.out" --error="$stage/slurm-%j.err")
sbatch --test-only "${args[@]}" "$script" "$stage" "$snapshot"
mkdir "$ledger"
printf '%s\n' "$snapshot" > "$ledger/snapshot.txt"
printf '%s\n' "$(date -Is)" > "$ledger/requested-at.txt"
printf '%s\n' 284684 > "$ledger/predecessor-job-id.txt"
job="$(sbatch --hold --parsable "${args[@]}" "$script" "$stage" "$snapshot")"
job="${job%%;*}"
[[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > "$ledger/job-id.txt"
printf '%s\t%s\t%s\n' "$(date -Is)" "$job" "$snapshot" > "$stage/submission.tsv"
scontrol release "$job"
printf 'job_id=%s\nsnapshot_sha256=%s\n' "$job" "$snapshot"
REMOTE
