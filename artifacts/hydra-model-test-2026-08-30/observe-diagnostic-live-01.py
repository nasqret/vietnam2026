#!/usr/bin/env python3
"""One read-only SSH observation of approved diagnostic job 21453693."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import signal
import subprocess
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
JOB = '21453693'
APPROVAL = '10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e'
COLLECTOR_SHA = '0d623e8908a2d6cdfef1380a8c012e6b5f456c5293c8d1f497b6e921a945fba4'
OBSERVER_SHA = '20276a347e6d88d763555593b850f055aaa28cfea685e36de87b1a43d470f12a'
STARTED = time.monotonic()


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def write(path, value):
    raw = canonical(value) + b'\n'
    require(len(raw) <= 4 * 1024**2, 'local observation file cap')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'bytes': len(raw), 'sha256': sha(raw)}


def exchange(args):
    child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    values, selector, error = {'stdout': bytearray(), 'stderr': bytearray()}, selectors.DefaultSelector(), None
    try:
        for label in values:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            require(time.monotonic() - STARTED < 50, 'SSH observation deadline')
            for key, _ in selector.select(0.1):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                else:
                    cap = 2 * 1024**2 if key.data == 'stdout' else 65536
                    room = cap - len(values[key.data])
                    values[key.data].extend(block[:room])
                    require(len(block) <= room, 'SSH observation stream cap')
        child.wait(timeout=max(0.01, 50 - (time.monotonic() - STARTED)))
    except (ValueError, OSError, subprocess.TimeoutExpired) as failure:
        error = type(failure).__name__ + ': ' + str(failure)[:1024]
    finally:
        if child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=3)
        selector.close()
        child.stdout.close()
        child.stderr.close()
    return child.returncode, bytes(values['stdout']), bytes(values['stderr']), error


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode, 'use isolated uncached Python')
    output = args.output
    started_path = output.with_name(output.stem + '.started.json')
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch(r'diagnostic-live-observation-[0-9]{2}\.json', output.name)
            and not output.exists() and not started_path.exists(), 'fresh direct archive observation required')
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('local observation wall cap')))
    signal.alarm(60)
    collector = (ARCHIVE / 'collect-diagnostic-remote-01.py').read_bytes()
    observer = (ARCHIVE / 'observe-diagnostic-remote-01.py').read_bytes()
    require(sha(collector) == COLLECTOR_SHA and sha(observer) == OBSERVER_SHA, 'pinned read-only helpers changed')
    package = ARCHIVE.parents[1] / '_deploy/hydra-model-test-execution-20260830/_deploy/hydra-frontier-diagnostic-v1'
    approval_raw = (package / 'approval.json').read_bytes()
    require(sha(approval_raw) == APPROVAL, 'fixed approved package changed')
    approval = json.loads(approval_raw)
    request_raw = (package / 'resource-request.json').read_bytes()
    require(sha(request_raw) == approval['request_file_sha256'], 'fixed resource request changed')
    request = json.loads(request_raw)
    evaluation_sha = request['payloads']['_deploy/hydra-frontier-diagnostic-v1/evaluation-request.json']['sha256']
    # Execute the retained collector only as a definitions namespace; its
    # terminal-only main is never called and its source is never patched.
    program = "COLLECTOR = {'__name__': '_pinned_collector'}\nexec(compile(" + repr(collector.decode())
    program += ", '<pinned-collector>', 'exec'), COLLECTOR)\n" + observer.decode()
    program_sha = sha(program.encode())
    write(started_path, {'schema': 'peano-hydra-diagnostic-live-observation-start-v1',
        'job_id': JOB, 'approval_sha256': APPROVAL, 'remote_program_sha256': program_sha,
        'collector_sha256': COLLECTOR_SHA, 'observer_sha256': OBSERVER_SHA,
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'read_only': True,
        'automatic_retry': False, 'limits': {'remote_cpu_seconds': 20, 'remote_wall_seconds': 30,
        'remote_address_space_bytes': 320 * 1024**2, 'remote_file_write_bytes': 0,
        'local_cpu_seconds': 20, 'local_wall_seconds': 60, 'local_checked_rss_bytes': 320 * 1024**2,
        'stdout_bytes': 2 * 1024**2, 'stderr_bytes': 65536, 'log_tail_bytes_each': 65536}})
    remote = '/usr/bin/python3.9 -I -B -c ' + shlex.quote(program)
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl', remote]
    code, stdout, stderr, error = exchange(command)
    observed = None
    try:
        require(code == 0 and error is None, 'remote observation failed')
        observed = json.loads(stdout)
        binding = observed['binding']
        require(observed['schema'] == 'peano-hydra-diagnostic-live-observation-v1'
            and binding['job_id'] == JOB and binding['approval_sha256'] == APPROVAL
            and binding['resource_request_sha256'] == sha(request_raw)
            and binding['evaluation_request_sha256'] == evaluation_sha
            and binding['source_commit'] == '612d1ea9e4905dfe2af104696924a19bc5883752'
            and binding['ledger_events'] == 6 and binding['reserved_gpu_seconds'] == 900
            and observed['proofs_independently_verified'] is False and observed['quality_claim'] is None,
            'observation job/approval/source/scope mismatch')
    except (ValueError, KeyError, TypeError) as failure:
        error = error or type(failure).__name__ + ': ' + str(failure)[:1024]
        observed = None
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if usage.ru_maxrss >= 320 * 1024**2 or time.monotonic() - STARTED >= 60:
        error = error or 'local observer resource envelope reached'
    record = {'schema': 'peano-hydra-diagnostic-live-observation-receipt-v1',
        'status': 'observed-not-proof-verified' if error is None else 'failed-observation-preserved',
        'job_id': JOB, 'approval_sha256': APPROVAL, 'evaluation_request_sha256': evaluation_sha,
        'remote_program_sha256': program_sha, 'collector_sha256': COLLECTOR_SHA, 'observer_sha256': OBSERVER_SHA,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'returncode': code, 'error': error,
        'stdout_bytes': len(stdout), 'stdout_sha256': sha(stdout), 'stderr': stderr.decode('utf-8', 'replace'),
        'failed_stdout_prefix': stdout[:65536].decode('utf-8', 'replace') if observed is None else None,
        'observation': observed, 'read_only': True, 'automatic_retry': False,
        'proofs_independently_verified': False, 'quality_claim': None,
        'resources': {'wall_seconds': time.monotonic() - STARTED,
            'cpu_seconds': usage.ru_utime + usage.ru_stime, 'maxrss_bytes': usage.ru_maxrss}}
    receipt = write(output, record)
    signal.alarm(0)
    print(json.dumps({'status': record['status'], 'output': str(output), 'receipt': receipt,
        'scheduler_state': None if observed is None else observed['scheduler']['observed_state'],
        'error': error}, sort_keys=True))
    return 0 if error is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
