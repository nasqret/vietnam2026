#!/usr/bin/env bash
# Explicit AP091 preparation or one full attempt; preserve every consumed ledger.
set -euo pipefail
if [ "$#" != 4 ] || [ "$2" != --submit ] || [ "$3" != --confirm ]; then
  echo "usage: $0 SNAPSHOT.tar --submit --confirm {AP091-PREPARE-V1|AP091-PREPARE-V2|AP091-FULL-V1}" >&2
  exit 2
fi
case "$4" in
  AP091-PREPARE-V1) phase=prepare; revision=1 ;;
  AP091-PREPARE-V2) phase=prepare; revision=2 ;;
  AP091-FULL-V1) phase=full; revision=1 ;;
  *) exit 2 ;;
esac
archive="$1"
[ -f "$archive" ] && [ ! -L "$archive" ]
snapshot="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
ssh_options=(-T -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no
  -o ConnectTimeout=15 -o ClearAllForwardings=yes -o ServerAliveInterval=10 -o ServerAliveCountMax=3)
ssh "${ssh_options[@]}" wmicluster "umask 077; set -C; cat > '$root/incoming-$snapshot.tar'" < "$archive"
ssh "${ssh_options[@]}" wmicluster "bash -s -- $snapshot $phase $revision" <<'REMOTE'
set -euo pipefail
snapshot="${1:?}";phase="${2:?}";revision="${3:?}"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
[[ "$phase" = prepare || "$phase" = full ]]
[[ "$revision" = 1 || "$phase:$revision" = prepare:2 ]]
root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
stage="$root/$snapshot";incoming="$root/incoming-$snapshot.tar"
ledger="$root/authorization-AP091-$phase-v$revision"
exec 8>"$root/.submission.lock"
flock -x 8
[ "$(timeout 10s sacct -n -X -j 259307 --format=JobIDRaw,State,ExitCode -P)" = '259307|COMPLETED|0:0' ]
if [ "$phase" = full ]; then
  prior="$(sed -n '1p' "$root/authorization-AP091-prepare-v2/job-id.txt")"
  [ "$prior" = 268994 ]
  [ "$(sed -n '1p' "$root/authorization-AP091-prepare-v2/snapshot.txt")" = 5d3a7f7ab86e1fb9a9b37eb1281556463b914028d35ca9d432e34c900b5f0642 ]
  state="$(timeout 10s sacct -n -X -j "$prior" --format=JobIDRaw,State,ExitCode -P)"
  case "$state" in
    '268994|PENDING|0:0'|'268994|RUNNING|0:0'|'268994|COMPLETING|0:0'|'268994|COMPLETED|0:0') ;;
    *) echo 'the exact preparation must still be eligible or have succeeded' >&2; exit 1 ;;
  esac
fi
if [ "$phase:$revision" = prepare:2 ]; then
  [ "$(sed -n '1p' "$root/authorization-AP091-prepare-v1/job-id.txt")" = 268413 ]
  state="$(timeout 10s sacct -n -X -j 268413 --format=JobIDRaw,State,ExitCode -P)"
  [[ "$state" = '268413|CANCELLED'* || "$state" = '268413|FAILED|1:0' ]]
fi
[ ! -e "$ledger" ] && [ ! -e "$stage" ]
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot" ]
python3 - "$incoming" "$stage" <<'EXTRACT'
import pathlib,sys,tarfile
archive,destination=map(pathlib.Path,sys.argv[1:])
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
script="$stage/source/slurm/peano_wmi_sqrt2_campaign.sbatch"
time_limit=00:45:00
if [ "$phase" = prepare ]; then time_limit=00:05:00; fi
args=(--partition=cpu,cpu_idle --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4096M
  --time="$time_limit" --no-requeue --chdir="$stage/source" --output="$stage/slurm-%j.out" --error="$stage/slurm-%j.err")
if [ "$phase" = full ]; then
  args+=(--dependency="afterok:$prior" --kill-on-invalid-dep=yes)
fi
sbatch --test-only "${args[@]}" "$script" "$stage" "$snapshot" "$phase"
mkdir "$ledger"
printf '%s\n' "$snapshot" > "$ledger/snapshot.txt"
printf '%s\n' "$(date -Is)" > "$ledger/requested-at.txt"
printf '%s\n' "$phase" > "$ledger/phase.txt"
if [ "$phase" = full ]; then printf '%s\n' "$prior" > "$ledger/afterok-job-id.txt"; fi
job="$(sbatch --hold --parsable "${args[@]}" "$script" "$stage" "$snapshot" "$phase")"
job="${job%%;*}"
[[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > "$ledger/job-id.txt"
printf '%s\t%s\t%s\n' "$(date -Is)" "$job" "$snapshot" > "$stage/submission.tsv"
scontrol release "$job"
printf 'job_id=%s\nsnapshot_sha256=%s\nphase=%s\n' "$job" "$snapshot" "$phase"
REMOTE
