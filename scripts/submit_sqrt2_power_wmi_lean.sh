#!/usr/bin/env bash
# Verification only: preserve both predecessors, never rerun HA generation.
set -euo pipefail
if [ "$#" != 4 ] || [ "$2" != --submit ] || [ "$3" != --confirm ]; then
  echo "usage: $0 SNAPSHOT.tar --submit --confirm {SQRT2-AP090-LEAN-V1|SQRT2-AP090-REGRESSIONS-V1}" >&2
  exit 2
fi
case "$4" in
  SQRT2-AP090-LEAN-V1) mode=lean-only ;;
  SQRT2-AP090-REGRESSIONS-V1) mode=regressions ;;
  *) exit 2 ;;
esac
archive="$1"
[ -f "$archive" ] && [ ! -L "$archive" ]
snapshot="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
readonly remote_root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
ssh_options=(-T -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no
  -o ConnectTimeout=15 -o ConnectionAttempts=1 -o ServerAliveInterval=10
  -o ServerAliveCountMax=3 -o ClearAllForwardings=yes)
incoming="$remote_root/incoming-$snapshot.tar"
ssh "${ssh_options[@]}" wmicluster \
  "umask 077; mkdir -p '$remote_root'; set -C; cat > '$incoming'" < "$archive"
ssh "${ssh_options[@]}" wmicluster "bash -s -- $snapshot $mode" <<'REMOTE'
set -euo pipefail
snapshot="${1:?}"
mode="${2:?}"
case "$mode" in
  lean-only) ledger=authorization-AP090-lean-v1 ;;
  regressions) ledger=authorization-AP090-regressions-v1 ;;
  *) exit 2 ;;
esac
[[ "$snapshot" =~ ^[0-9a-f]{64}$ ]]
root=/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots
incoming="$root/incoming-$snapshot.tar"
stage="$root/$snapshot"
[ -f "$incoming" ] && [ ! -L "$incoming" ]
[ "$(sha256sum "$incoming" | awk '{print $1}')" = "$snapshot" ]
exec 8>"$root/.submission.lock"
flock -x 8
prior=e8353c52fbefb9f711d9e08af2870453caee341bce83fa45af39ab17e6d40553
[ "$(sed -n '1p' "$root/authorization-AP090-v2/job-id.txt")" = 258959 ]
[ "$(sed -n '1p' "$root/authorization-AP090-v2/snapshot.txt")" = "$prior" ]
accounting="$(timeout 10s sacct -n -X -j 258959 --format=JobIDRaw,State,ExitCode -P)"
[ "$accounting" = '258959|FAILED|1:0' ]
ha_relative=source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-v1/report.json
ha_sha=d97afbf151e451450e0551b8d49e8c0e0f6ac074c43c42d44b716d6f685ebf86
[ "$(sha256sum "$root/$prior/$ha_relative" | awk '{print $1}')" = "$ha_sha" ]
python3 - "$root/$prior/evidence/pilot-report.json" "$root/$prior/$ha_relative" <<'PREDECESSOR'
import json,sys
with open(sys.argv[1]) as stream: prior=json.load(stream)
with open(sys.argv[2]) as stream: ha=json.load(stream)
if (prior['job_id']!='258959' or prior['full_attempt_started'] is not True
        or prior['status']!='failed_or_incomplete'
        or ha['status']!='fresh_ordinary_HA_checked' or ha['case']!='AP090'):
    raise ValueError('predecessor is not the completed HA / incomplete Lean pilot')
PREDECESSOR
if [ "$mode" = regressions ]; then
  lean_prior=23141c6d4550624976c85c768260639ecb21a97c27f54023918978679a8fafdb
  [ "$(sed -n '1p' "$root/authorization-AP090-lean-v1/job-id.txt")" = 259148 ]
  [ "$(sed -n '1p' "$root/authorization-AP090-lean-v1/snapshot.txt")" = "$lean_prior" ]
  [ "$(timeout 10s sacct -n -X -j 259148 --format=JobIDRaw,State,ExitCode -P)" = '259148|COMPLETED|0:0' ]
  lean_report="$root/$lean_prior/source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-lean-wmi-v2/report.json"
  [ "$(sha256sum "$lean_report" | awk '{print $1}')" = d0e929841e922a9c11ac170d8d1e0a5db8bc56f88990bef04aa0803281aee247 ]
fi
[ ! -e "$root/$ledger" ]
[ ! -e "$stage" ]
python3 - "$incoming" "$stage" <<'EXTRACT'
import pathlib,sys,tarfile
archive,destination=map(pathlib.Path,sys.argv[1:])
with tarfile.open(archive,'r:') as handle:
    members=handle.getmembers(); names=set(); total=0
    for member in members:
        path=pathlib.PurePosixPath(member.name)
        if (not member.isfile() or path.is_absolute() or '..' in path.parts
                or str(path)!=member.name or member.name in names
                or (path.parts[0] not in {'source','lean'} and member.name!='snapshot-manifest.json')
                or member.size<0 or member.size>32*1024**2):
            raise ValueError('unsafe source archive member')
        names.add(member.name); total+=member.size
    if not members or total>128*1024**2 or len(members)>3000:
        raise ValueError('source archive boundary exceeded')
    destination.mkdir(mode=0o700)
    handle.extractall(destination)
EXTRACT
[ "$(sha256sum "$stage/$ha_relative" | awk '{print $1}')" = "$ha_sha" ]
python=/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python
[ -x "$python" ]
"$python" -B "$stage/source/scripts/package_sqrt2_power_wmi.py" --verify "$stage"
script="$stage/source/slurm/peano_wmi_sqrt2_pilot.sbatch"
args=(--partition=cpu_idle --nodes=1 --ntasks=1 --cpus-per-task=1
  --mem=4096M --time=00:45:00 --no-requeue --job-name=peano-ap090-lean
  --chdir="$stage/source" --output="$stage/slurm-%j.out" --error="$stage/slurm-%j.err")
sbatch --test-only "${args[@]}" "$script" "$stage" "$snapshot" "$mode"
mkdir "$root/$ledger"
printf '%s\n' "$snapshot" > "$root/$ledger/snapshot.txt"
printf '%s\n' "$(date -Is)" > "$root/$ledger/requested-at.txt"
printf '%s\n' 258959 > "$root/$ledger/predecessor-job-id.txt"
printf '%s\n' "$mode" > "$root/$ledger/mode.txt"
submission="$(sbatch --hold --parsable "${args[@]}" "$script" "$stage" "$snapshot" "$mode")"
job_id="${submission%%;*}"
[[ "$job_id" =~ ^[0-9]+$ ]]
printf '%s\n' "$job_id" > "$root/$ledger/job-id.txt"
printf '%s\t%s\t%s\n' "$(date -Is)" "$job_id" "$snapshot" > "$stage/submission.tsv"
scontrol release "$job_id"
printf 'job_id=%s\nsnapshot_sha256=%s\nremote_stage=%s\n' "$job_id" "$snapshot" "$stage"
REMOTE
