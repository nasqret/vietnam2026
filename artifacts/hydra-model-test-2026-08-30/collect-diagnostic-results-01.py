#!/usr/bin/env python3
"""Collect one terminal diagnostic job; read-only SSH, no model/proof execution.

The caller supplies the exact launched job and raw approval hash. The remote
reader checks its released ledger and terminal accounting, hashes only fixed
report/log paths and streams a small allowlisted archive. No automatic retry.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
REMOTE_HELPER = ARCHIVE / 'collect-diagnostic-remote-01.py'
REMOTE_HELPER_SHA = '0d623e8908a2d6cdfef1380a8c012e6b5f456c5293c8d1f497b6e921a945fba4'
EXECUTION = ARCHIVE.parents[1] / '_deploy/hydra-model-test-execution-20260830'
PACKAGE = EXECUTION / '_deploy/hydra-frontier-diagnostic-v1'
MAX_STREAM = 66 * 1024**2
MAX_FILES = 64 * 1024**2
MAX_RETAINED = 136 * 1024**2
ALLOWED = {'run.json', 'diagnostic.json', 'execution-status.json', 'checkpoint/header.json',
           'checkpoint/HEAD.json', 'diagnostic.out.log', 'diagnostic.err.log', 'ledger.jsonl'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def write(path, raw):
    require(type(raw) is bytes and path == path.resolve(strict=False), 'canonical output required')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'bytes': len(raw), 'sha256': sha(raw)}


def exchange(command):
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    values, selector, reason = {'stdout': bytearray(), 'stderr': bytearray()}, selectors.DefaultSelector(), 'exited'
    try:
        for label in values:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            require(time.monotonic() - STARTED < 65, 'local SSH collection deadline')
            for key, _ in selector.select(0.1):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                else:
                    cap = MAX_STREAM if key.data == 'stdout' else 65536
                    room = cap - len(values[key.data])
                    values[key.data].extend(block[:room])
                    require(len(block) <= room, 'collection stream byte cap')
        child.wait(timeout=max(0.01, 65 - (time.monotonic() - STARTED)))
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        reason = type(error).__name__ + ': ' + str(error)[:1000]
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
    return child.returncode, bytes(values['stdout']), bytes(values['stderr']), reason


def extract(raw, output, job, approval_sha, evaluation_sha):
    seen, total, index = set(), 0, None
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            require(member.isfile() and member.name not in seen and not member.pax_headers,
                    'archive contains a duplicate, extension, link or special file')
            if index is None:
                require(member.name == 'collection-index.json' and 0 < member.size <= 1024**2,
                        'bounded collection index must be first')
                body = archive.extractfile(member).read(1024**2 + 1)
                require(len(body) == member.size, 'truncated collection index')
                index = json.loads(body)
                require(index['schema'] == 'peano-hydra-diagnostic-terminal-collection-index-v1'
                    and index['binding']['job_id'] == job and index['binding']['approval_sha256'] == approval_sha
                    and index['binding']['evaluation_request_sha256'] == evaluation_sha
                    and index['binding']['source_commit'] == '612d1ea9e4905dfe2af104696924a19bc5883752'
                    and index['binding']['reserved_gpu_seconds'] == 900
                    and set(index['files']) <= ALLOWED and len(index['files']) <= len(ALLOWED)
                    and index['total_file_bytes'] <= MAX_FILES
                    and index['proofs_independently_verified'] is False
                    and index['model_weights_read_or_downloaded'] is False,
                    'collection index changed approved job/source/scope')
                write(output / member.name, body)
            else:
                require(member.name in index['files'] and member.name in ALLOWED, 'unapproved archive path')
                expected = index['files'][member.name]
                require(type(expected['bytes']) is int and 0 <= expected['bytes'] <= 48 * 1024**2
                        and member.size == expected['bytes'], 'archive member size changed')
                total += member.size
                require(total <= MAX_FILES, 'extracted aggregate exceeds bound')
                path = output / member.name
                if '/' in member.name and not path.parent.exists():
                    require(member.name.startswith('checkpoint/'), 'unexpected nested archive path')
                    path.parent.mkdir(mode=0o700)
                digest, count = hashlib.sha256(), 0
                with path.open('xb') as target, archive.extractfile(member) as source:
                    while True:
                        block = source.read(65536)
                        if not block:
                            break
                        count += len(block)
                        require(count <= expected['bytes'], 'archive file exceeded declared bytes')
                        digest.update(block)
                        target.write(block)
                    target.flush()
                    os.fsync(target.fileno())
                require(count == expected['bytes'] and digest.hexdigest() == expected['sha256'], 'collected file hash differs')
            seen.add(member.name)
            require(len(seen) <= len(ALLOWED) + 1, 'archive member-count limit')
    require(index is not None and seen == set(index['files']) | {'collection-index.json'}
            and total == index['total_file_bytes'], 'archive is incomplete')
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r'[1-9][0-9]{0,19}', args.job_id)
            and re.fullmatch(r'[a-f0-9]{64}', args.approval_sha256), 'exact job and approval raw hash required')
    resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_STREAM, MAX_STREAM))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('local collection wall cap')))
    signal.alarm(75)
    program = REMOTE_HELPER.read_bytes()
    require(sha(program) == REMOTE_HELPER_SHA, 'reviewed remote collector changed')
    approval_raw = (PACKAGE / 'approval.json').read_bytes()
    require(sha(approval_raw) == args.approval_sha256, 'external approval does not match local approved package')
    approval = json.loads(approval_raw)
    request_raw = (PACKAGE / 'resource-request.json').read_bytes()
    require(sha(request_raw) == approval['request_file_sha256'], 'local resource request differs')
    request = json.loads(request_raw)
    evaluation_sha = request['payloads']['_deploy/hydra-frontier-diagnostic-v1/evaluation-request.json']['sha256']
    output = args.output_directory
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch(r'diagnostic-collected-[0-9]{2}', output.name) and not output.exists(),
            'collection needs one fresh direct archive directory')
    require(shutil.disk_usage(ARCHIVE).free >= MAX_RETAINED + 512 * 1024**2, 'insufficient collection disk reserve')
    output.mkdir(mode=0o700)
    write(output / 'started.json', canonical({'schema': 'peano-hydra-diagnostic-collection-start-v1',
        'job_id': args.job_id, 'approval_sha256': args.approval_sha256, 'remote_program_sha256': REMOTE_HELPER_SHA,
        'read_only': True, 'automatic_retry': False, 'remote_limits': {'cpu_seconds': 20, 'wall_seconds': 45,
        'address_space_bytes': 320 * 1024**2, 'file_write_bytes': 0},
        'local_limits': {'cpu_seconds': 30, 'wall_seconds': 75, 'stream_bytes': MAX_STREAM,
        'retained_bytes': MAX_RETAINED, 'checked_peak_rss_bytes': 384 * 1024**2}}) + b'\n')
    # Keep the established login scheduler PATH, as the retained training
    # observer does. Python itself is absolute, isolated and uncached.
    remote = '/usr/bin/python3.9 -I -B -c ' + shlex.quote(program.decode())
    remote += ' ' + args.job_id + ' ' + args.approval_sha256
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl', remote]
    code, stdout, stderr, reason = exchange(command)
    transport = write(output / 'transport.tar', stdout)
    stderr_pin = write(output / 'stderr.log', stderr)
    index, error = None, None
    try:
        require(code == 0 and reason == 'exited', 'remote collection did not finish successfully')
        index = extract(stdout, output, args.job_id, args.approval_sha256, evaluation_sha)
    except (ValueError, OSError, KeyError, TypeError, tarfile.TarError) as failure:
        error = type(failure).__name__ + ': ' + str(failure)[:2048]
    usage = resource.getrusage(resource.RUSAGE_SELF)
    elapsed = time.monotonic() - STARTED
    retained = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    if elapsed >= 75 or usage.ru_maxrss >= 384 * 1024**2 or retained >= MAX_RETAINED - 65536:
        error = error or 'local collection resource envelope reached'
    record = {'schema': 'peano-hydra-diagnostic-results-collection-v1',
        'status': 'collected-not-proof-verified' if error is None else 'failed-partial-output-preserved',
        'job_id': args.job_id, 'approval_sha256': args.approval_sha256,
        'evaluation_request_sha256': evaluation_sha, 'remote_program_sha256': REMOTE_HELPER_SHA,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'returncode': code, 'reason': reason,
        'error': error, 'transport': transport, 'stderr': stderr_pin,
        'files': None if index is None else index['files'], 'accounting': None if index is None else index['accounting'],
        'resources': {'wall_seconds': elapsed, 'cpu_seconds': usage.ru_utime + usage.ru_stime,
                      'maxrss_bytes': usage.ru_maxrss, 'retained_bytes_before_receipt': retained},
        'read_only': True, 'model_loaded': False, 'proofs_independently_verified': False,
        'checkpoint_goal_records_collected': False, 'automatic_retry': False}
    receipt = write(output / 'collection-receipt.json', canonical(record) + b'\n')
    signal.alarm(0)
    print(json.dumps({'status': record['status'], 'directory': str(output), 'receipt': receipt,
        'run_json': None if index is None else index['files'].get('run.json'),
        'diagnostic_json': None if index is None else index['files'].get('diagnostic.json')}, sort_keys=True))
    return 0 if error is None else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print('diagnostic-results-collection: ' + ' '.join(str(error).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
