"""Run and collect the exact bounded CPU-only tokenizer preflight over SSH.

Fresh one-use local attempt, strict existing host-key verification, no file
overwrite, installation, model loading request or Slurm mutation.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import signal
import stat
import subprocess
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
HELPER = ARCHIVE / 'retention-preflight-remote-01.py'
REQUEST = ARCHIVE / 'cpu-preflight-request-01.json'
ATTEMPT = ARCHIVE / 'cpu-preflight-01'
REMOTE = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-pilot-v1'
MAX_OUTPUT = 8 * 1024**2


def canonical(value): return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
def pin(raw): return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(path, maximum):
    for parent in (path.parent, *path.parent.parents): assert stat.S_ISDIR(parent.lstat().st_mode)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(fd)
        assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size <= maximum
        with os.fdopen(fd, 'rb', closefd=False) as f: raw = f.read(maximum + 1)
        t = os.fstat(fd)
        assert len(raw) == s.st_size and (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns) == (t.st_dev, t.st_ino, t.st_size, t.st_mtime_ns, t.st_ctime_ns)
        return raw
    finally: os.close(fd)


def write(name, raw):
    assert name in {'started.json', 'ssh-process.json', 'response.json', 'remote-process.json', 'token-preflight.json'}
    assert isinstance(raw, bytes) and len(raw) <= MAX_OUTPUT
    fd = os.open(ATTEMPT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return {'path': str(ATTEMPT / name), **pin(raw)}


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--expected-request-sha256', required=True)
    parser.add_argument('--expected-helper-sha256', required=True)
    args = parser.parse_args()
    for value in (args.expected_request_sha256, args.expected_helper_sha256): assert re.fullmatch('[0-9a-f]{64}', value)
    raw_request, raw_helper = read(REQUEST, 16384), read(HELPER, 65536)
    assert pin(raw_request)['sha256'] == args.expected_request_sha256 and pin(raw_helper)['sha256'] == args.expected_helper_sha256
    assert not os.path.lexists(ATTEMPT)
    os.mkdir(ATTEMPT, 0o700)
    write('started.json', canonical({'schema': 'peano-hydra-retention-cpu-preflight-ssh-start-v1',
        'request': pin(raw_request), 'remote_helper': pin(raw_helper), 'automatic_retry': False,
        'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'maximum_wall_seconds': 330, 'maximum_combined_output_bytes': MAX_OUTPUT,
        'model_weights_or_gpu_allocation_requested': False}))
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl',
        'cd ' + shlex.quote(REMOTE) + ' && /usr/bin/python3.9 -I -B -c ' + shlex.quote(raw_helper.decode())]
    resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT, MAX_OUTPUT))
    child, selector, error = None, selectors.DefaultSelector(), None
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    try:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        child.stdin.write(raw_request); child.stdin.close()
        for name, stream in (('stdout', child.stdout), ('stderr', child.stderr)):
            os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or child.poll() is None:
            assert time.monotonic() - started < 325, 'SSH preflight wall limit'
            for key, _ in selector.select(.1):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block: selector.unregister(key.fileobj); continue
                assert sum(map(len, output.values())) + len(block) <= MAX_OUTPUT, 'SSH preflight output cap'
                output[key.data].extend(block)
        child.wait(timeout=1)
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + str(failure)
    finally:
        if child is not None:
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait(timeout=5)
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream is not None: stream.close()
        selector.close()
    passed = child is not None and child.returncode == 0 and error is None and time.monotonic() - started < 330
    response = None
    saved = {}
    try:
        assert read(REQUEST, 16384) == raw_request and read(HELPER, 65536) == raw_helper, 'operator input changed'
        if passed:
            response = json.loads(output['stdout'])
            record = response['record']
            assert record['status'] == 'passed' and record['returncode'] == 0 and record['request'] == json.loads(raw_request)
            assert record['input_pins_unchanged'] is True and record['model_weights_requested'] is False and record['gpu_allocation_requested'] is False
            process_raw = canonical(record)
            assert pin(process_raw) == {k: response['receipt'][k] for k in ('bytes', 'sha256')}
            payload = base64.b64decode(response['preflight_base64'], validate=True)
            assert pin(payload) == {k: record['preflight'][k] for k in ('bytes', 'sha256')}
            assert len(payload) <= 4 * 1024**2
            saved['remote_process'] = write('remote-process.json', process_raw)
            saved['preflight'] = write('token-preflight.json', payload)
            saved['response'] = write('response.json', bytes(output['stdout']))
    except BaseException as failure:
        passed = False; error = type(failure).__name__ + ': ' + str(failure)
    receipt = {'schema': 'peano-hydra-retention-cpu-preflight-ssh-process-v1', 'status': 'passed' if passed else 'failed',
        'returncode': None if child is None else child.returncode, 'error': error,
        'wall_seconds': time.monotonic() - started, 'request': pin(raw_request), 'remote_helper': pin(raw_helper),
        'stdout': pin(bytes(output['stdout'])), 'stderr': output['stderr'].decode('utf-8', 'replace'),
        'saved': saved, 'automatic_retry': False, 'model_weights_or_gpu_allocation_requested': False}
    if not passed: receipt['failure_stdout'] = output['stdout'].decode('utf-8', 'replace')[:256 * 1024]
    receipt_pin = write('ssh-process.json', canonical(receipt))
    print(json.dumps({'status': receipt['status'], 'receipt': receipt_pin, 'saved': saved}, sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__': raise SystemExit(main())
