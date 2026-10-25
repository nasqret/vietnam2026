#!/usr/bin/env python3
"""Same frozen launch gates, with the probed login Python 3.9 invocation only.

Archive-only correction: no frozen file, approval, package or resource changes.
The copied local sequence remains metadata -> bounded input check -> identical
metadata. Only then does SSH invoke the same frozen gate using /usr/bin/python3.9.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-training-execution-20260830')
ARCHIVE = Path(__file__).absolute().parent
PACKAGE = ROOT / '_deploy/hydra-frontier-training-v1'
COMMIT = 'b08a6b1303d73217f6cc23800ae15e50b17db792'
APPROVAL = '9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd'
REQUEST = '02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb'
PINS = {
    'user-instruction.json': '7158689e94fd42e60710b15a134ec8a2a2f446da993ef0b52e9cd815138ed164',
    'explicit-transfer-approval-01.json': '77f6d087bef03c3b4666681b429b66382a9fd79132aeeaa76702867b3023c8ae',
    'transfer-02/send-result.json': 'da3432ba727296a9fd48a69e0fd41325ba6625dfbfbec3e599dafae15b4e57fe',
    'launch-test-only-01.json': '4ef5e3976a3a05bfceb9096a2635420bb106cf12633f11d8c544802e45a4cfed',
    'launch-python-environment-probe-01.json': '40ceae1a708c3b866f48c7a0d1befed3c210cb5d6b4a360e237bdbe44ff31e6a',
}
CONFIRM = 'PEANO-HYDRA-FRONTIER-TRAINING-7200-GPU-SECONDS'

# These are the original frozen shell's three local gates and remote argument
# join. This archive body has a fixed working directory instead of deriving
# one from its own (different) archive location. No PATH command interception.
BRIDGE = r'''set -euo pipefail
[ "$#" -eq 3 ] || exit 2
approval_sha="$1"
mode="$2"
confirmation="$3"
[[ "$approval_sha" =~ ^[0-9a-f]{64}$ ]] || exit 2
if { [ "$mode" = --submit ] && [ "$confirmation" != PEANO-HYDRA-FRONTIER-TRAINING-7200-GPU-SECONDS ]; } ||
   { [ "$mode" = --test-only ] && [ -n "$confirmation" ]; }; then exit 2; fi
[ "$mode" = --test-only ] || [ "$mode" = --submit ] || exit 2
[ -z "${SLURM_JOB_ID:-}" ] || exit 2
for option in ${!SBATCH_@}; do printf 'SBATCH override forbidden: %s\n' "$option" >&2; exit 2; done
for option in ${!GIT_@}; do unset "$option"; done
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_NO_REPLACE_OBJECTS=1 GIT_NO_LAZY_FETCH=1 GIT_OPTIONAL_LOCKS=0
export PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/dev/null
gate=training/peano_hydra/frontier_training_launch.py
metadata="$(python3 -I -B "$gate" --check --local --approval-sha256 "$approval_sha")"
read -r commit helper_sha training_inputs_sha < <(python3 -I -B -c \
  'import json,re,sys; x=json.loads(sys.argv[1]); v=[x["source_commit"],x["helper_sha256"],x["training_inputs_sha256"]]; assert x["status"]=="metadata-verified" and re.fullmatch("[0-9a-f]{40}",v[0]) and all(re.fullmatch("[0-9a-f]{64}",s) for s in v[1:]); print(" ".join(v))' "$metadata")
python3 -I -B -X pycache_prefix=/dev/null scripts/check_peano_hydra_frontier_training_inputs.py \
  --check --request _deploy/hydra-frontier-training-v1/training-inputs.json --expected-request-sha256 "$training_inputs_sha"
rechecked="$(python3 -I -B "$gate" --check --local --approval-sha256 "$approval_sha")"
[ "$metadata" = "$rechecked" ] || { printf '%s\n' 'local approval/source changed before SSH' >&2; exit 2; }
ssh -o BatchMode=yes -o ConnectTimeout=15 -- plgnasqret@helios.cyfronet.pl \
  "bash -l -s -- $approval_sha $commit $helper_sha $mode" <<'REMOTE'
set -euo pipefail
[ "$#" -eq 4 ] || exit 2
project="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training/experiments/frontier-training-v1"
cd "$project"
gate=training/peano_hydra/frontier_training_launch.py
printf '%s  %s\n' "$3" "$gate" | sha256sum --check --status
arguments=(--approval-sha256 "$1" --source-commit "$2" "$4")
if [ "$4" = --submit ]; then arguments+=(--confirm PEANO-HYDRA-FRONTIER-TRAINING-7200-GPU-SECONDS); fi
exec /usr/bin/python3.9 -I -B "$gate" "${arguments[@]}"
REMOTE
'''


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, maximum=4 * 1024**2):
    # Fixed local archive/source paths, checked without following the leaf.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        import stat
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                'bounded single-link regular evidence required')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(maximum + 1)
        after = os.fstat(fd)
        require(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns
                and before.st_ctime_ns == after.st_ctime_ns, 'evidence changed while reading')
        return raw
    finally:
        os.close(fd)


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())


def prerequisites(approval_sha):
    require(approval_sha == APPROVAL, 'exact original training approval required')
    records = {}
    for name, expected in PINS.items():
        raw = read(ARCHIVE / name)
        require(sha(raw) == expected, 'correction evidence changed: ' + name)
        records[name] = json.loads(raw)
    require(sha(read(PACKAGE / 'approval.json')) == APPROVAL
            and sha(read(PACKAGE / 'resource-request.json')) == REQUEST, 'frozen request/approval changed')
    transfer = records['transfer-02/send-result.json']
    require(transfer.get('status') == 'transferred-and-rehashed' and transfer.get('original_inputs_rechecked') is True
            and transfer.get('source_commit') == COMMIT and transfer.get('approval_sha256') == APPROVAL
            and transfer.get('request_sha256') == REQUEST
            and transfer.get('remote', {}).get('all_file_hashes_rechecked') is True,
            'exact verified transfer is missing')
    failed = records['launch-test-only-01.json']
    require(failed.get('phase') == 'test-only' and failed.get('returncode') != 0 and failed.get('timed_out') is False,
            'original failed test-only receipt changed')
    probe = records['launch-python-environment-probe-01.json']
    require(probe.get('read_only') is True and probe.get('job_submission_performed') is False
            and probe.get('process', {}).get('returncode') == 0, 'runtime probe did not succeed read-only')
    candidates = []
    for line in probe['process']['stdout'].splitlines():
        if line.startswith('{'):
            value = json.loads(line)
            if value.get('candidate_python') == '/usr/bin/python3.9':
                candidates.append(value)
    require(len(candidates) == 1 and candidates[0].get('machine') == 'x86_64'
            and candidates[0].get('version', '').startswith('3.9.25 '), 'exact installed login interpreter not confirmed')
    return candidates[0]


def require_successful_v2_test(helper_sha):
    raw = read(ARCHIVE / 'launch-test-only-02.json')
    record = json.loads(raw)
    require(record.get('schema') == 'peano-hydra-frontier-training-control-invocation-v1'
            and record.get('phase') == 'test-only' and record.get('returncode') == 0
            and record.get('timed_out') is False and record.get('source_commit') == COMMIT
            and record.get('approval_sha256') == APPROVAL and record.get('helper_sha256') == helper_sha,
            'submit requires the successful exact v2 test-only invocation')
    result = json.loads(record['stdout'].strip().splitlines()[-1])
    require(result.get('status') == 'test-only' and result.get('allocation_performed') is False,
            'prior test does not establish a nonallocating launch check')
    return sha(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--phase', choices=('test-only', 'submit'), required=True)
    parser.add_argument('--approval-sha256', required=True)
    args = parser.parse_args(argv)
    require(sys.flags.isolated and sys.dont_write_bytecode, 'run with python -I -B')
    login_python = prerequisites(args.approval_sha256)
    helper_sha = sha(read(Path(__file__).absolute()))
    preceding_test = require_successful_v2_test(helper_sha) if args.phase == 'submit' else None
    label = 'launch-test-only-02' if args.phase == 'test-only' else 'launch-submit-01'
    paths = {key: ARCHIVE / (label + suffix) for key, suffix in
             (('started', '.started.json'), ('receipt', '.json'), ('stdout', '.stdout.log'), ('stderr', '.stderr.log'), ('bridge', '.bridge.sh'))}
    require(all(not os.path.lexists(path) for path in paths.values()), 'fresh control invocation required; no retry or overwrite')
    env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'PYTHON', 'SLURM_', 'SBATCH_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX='/dev/null', PYTHONNOUSERSITE='1')
    env['PATH'] = '/opt/homebrew/opt/python@3.11/libexec/bin:' + env.get('PATH', '/usr/bin:/bin')
    found = shutil.which('python3', path=env['PATH'])
    require(found is not None and Path(found).resolve() == Path(sys.executable).resolve(), 'invoke this controller with the existing /opt/homebrew/bin/python3.11')
    with paths['bridge'].open('xb') as stream:
        stream.write(BRIDGE.encode()); stream.flush(); os.fsync(stream.fileno())
    command = ['/bin/bash', str(paths['bridge']), args.approval_sha256, '--' + args.phase,
               CONFIRM if args.phase == 'submit' else '']
    started = datetime.now(timezone.utc).isoformat()
    correction = {'kind': 'invocation-only-login-python-correction', 'remote_python': '/usr/bin/python3.9',
                  'installed_runtime_probe': login_python, 'retained_evidence_sha256': dict(PINS),
                  'frozen_source_changed': False, 'package_or_approval_changed': False,
                  'resource_limits_changed': False, 'package_initialization_skipped': False,
                  'path_shim_used': False, 'preceding_test_sha256': preceding_test}
    write(paths['started'], {'phase': args.phase, 'command': command, 'cwd': str(ROOT), 'started_at_utc': started,
        'source_commit': COMMIT, 'approval_sha256': args.approval_sha256, 'helper_sha256': helper_sha,
        'bridge_sha256': sha(BRIDGE.encode()), 'correction': correction, 'automatic_retry': False,
        'maximum_gpu_seconds': 7200 if args.phase == 'submit' else 0, 'maximum_control_wall_seconds': 60})
    clock, timeout = time.monotonic(), False
    with paths['stdout'].open('xb') as out, paths['stderr'].open('xb') as err:
        child = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            timeout = True
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=2)
            code = None
        out.flush(); err.flush(); os.fsync(out.fileno()); os.fsync(err.fileno())
    require(paths['stdout'].stat().st_size <= 1024**2 and paths['stderr'].stat().st_size <= 256 * 1024,
            'original control output bound exceeded; logs retained, no retry')
    stdout, stderr = paths['stdout'].read_text(), paths['stderr'].read_text()
    record = {'schema': 'peano-hydra-frontier-training-control-invocation-v1', 'phase': args.phase,
        'command': command, 'cwd': str(ROOT), 'started_at_utc': started,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'wall_seconds': time.monotonic() - clock,
        'source_commit': COMMIT, 'approval_sha256': args.approval_sha256, 'helper_sha256': helper_sha,
        'correction': correction, 'bridge_sha256': sha(BRIDGE.encode()),
        'returncode': code, 'timed_out': timeout, 'automatic_retry': False, 'stdout': stdout, 'stderr': stderr,
        'logs': {key: {'path': str(paths[key]), 'bytes': paths[key].stat().st_size,
                      'sha256': sha(paths[key].read_bytes())} for key in ('stdout', 'stderr')}}
    write(paths['receipt'], record)
    last = stdout.strip().splitlines()[-1] if stdout.strip() else None
    print(json.dumps({'phase': args.phase, 'returncode': code, 'timed_out': timeout,
        'receipt': str(paths['receipt']), 'receipt_sha256': sha(read(paths['receipt'])),
        'last_stdout_line': last, 'stderr': stderr, 'automatic_retry': False}, sort_keys=True), flush=True)
    return 0 if code == 0 and not timeout else 2


if __name__ == '__main__':
    raise SystemExit(main())
