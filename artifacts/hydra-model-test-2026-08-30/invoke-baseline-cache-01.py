"""Invoke the pinned login-node baseline preflight or one server-local copy."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
HELPER = ARCHIVE / 'stage-baseline-cache-remote-01.py'
HELPER_SHA = '36604b7a7a9293101b8ed2c6e5ea9ae79c0f22aec13ae8f55e1a7f3294c5c28d'
PLAN = ARCHIVE / 'baseline-cache-stage-plan-01.json'
PLAN_SHA = '7687216add248abbd4f7faa2701eb5f463521e233c6e6fb24fe53980c4506ffb'


def write(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    assert len(raw) <= 2 * 1024**2
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('mode', choices=('preflight', 'stage'))
    args = parser.parse_args()
    assert sys.flags.isolated and sys.dont_write_bytecode
    resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    helper, plan = HELPER.read_bytes(), PLAN.read_bytes()
    assert not HELPER.is_symlink() and not PLAN.is_symlink()
    assert len(helper) <= 65536 and hashlib.sha256(helper).hexdigest() == HELPER_SHA
    assert len(plan) == 118873 and hashlib.sha256(plan).hexdigest() == PLAN_SHA
    if args.mode == 'stage':
        prior = json.loads((ARCHIVE / 'baseline-cache-preflight-01.json').read_text())
        assert prior['status'] == 'passed' and prior['result']['status'] == 'read-only-preflight-passed'
        assert prior['plan_sha256'] == PLAN_SHA and prior['helper_sha256'] == HELPER_SHA
    program = helper + ('\nraise SystemExit(main(' + repr(plan) + ', ' + repr(PLAN_SHA)
                        + ', ' + repr(args.mode == 'stage') + '))\n').encode()
    assert len(program) <= 256 * 1024
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
               '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
               '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
               '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--',
               'plgnasqret@helios.cyfronet.pl',
               '/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.9 -I -B -']
    stem = 'baseline-cache-' + args.mode + '-01'
    started = time.monotonic()
    write(ARCHIVE / (stem + '.started.json'), {
        'schema': 'peano-hydra-baseline-cache-invocation-start-v1', 'mode': args.mode,
        'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'helper_sha256': HELPER_SHA, 'plan_sha256': PLAN_SHA,
        'program_sha256': hashlib.sha256(program).hexdigest(), 'program_bytes': len(program),
        'automatic_retry': False, 'gpu_job_submitted': False,
    })
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = child.communicate(program, timeout=105)
    except BaseException:
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate(timeout=3)
        write(ARCHIVE / (stem + '.json'), {
            'schema': 'peano-hydra-baseline-cache-invocation-v1', 'status': 'failed-or-uncertain',
            'mode': args.mode, 'helper_sha256': HELPER_SHA, 'plan_sha256': PLAN_SHA,
            'returncode': child.returncode, 'wall_seconds': time.monotonic() - started,
            'stdout': stdout[:1024**2].decode('utf-8', 'replace'),
            'stderr': stderr[:65536].decode('utf-8', 'replace'), 'automatic_retry': False,
        })
        raise
    assert len(stdout) <= 1024**2 and len(stderr) <= 65536
    result = json.loads(stdout)
    expected = 'read-only-preflight-passed' if args.mode == 'preflight' else 'staged-and-independently-rehashed'
    passed = (child.returncode == 0 and result.get('status') == expected
              and result.get('plan_sha256') == PLAN_SHA and result.get('file_count') == 725
              and result.get('total_bytes') == 235986082 and result.get('gpu_job_submitted') is False)
    record = {
        'schema': 'peano-hydra-baseline-cache-invocation-v1', 'status': 'passed' if passed else 'failed-or-uncertain',
        'mode': args.mode, 'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'helper_sha256': HELPER_SHA, 'plan_sha256': PLAN_SHA, 'returncode': child.returncode,
        'wall_seconds': time.monotonic() - started, 'result': result,
        'raw_stdout_sha256': hashlib.sha256(stdout).hexdigest(), 'stderr': stderr.decode('utf-8', 'replace'),
        'automatic_retry': False, 'gpu_job_submitted': False,
    }
    receipt = write(ARCHIVE / (stem + '.json'), record)
    print(json.dumps({'status': record['status'], 'receipt': receipt,
                      'result': {k: v for k, v in result.items() if k != 'source_modes'}}, sort_keys=True))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
