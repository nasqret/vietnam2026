#!/usr/bin/env python3
"""Collect one completed retention model by a bounded read-only SSH exchange.

Inspect mode collects the terminal manifest and controls without opening model
artifact files. Model mode requires that previously observed manifest raw SHA.
The transfer and extracted bytes are retained separately in a fresh directory;
neither a failed exchange nor an existing file is retried or overwritten.
Collection establishes byte identity, not semantic artifact or proof admission.
"""
import time
STARTED = time.monotonic()
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tarfile

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
FROZEN = ARCHIVE.parents[1] / '_deploy/hydra-retention-execution-20260830'
PACKAGE = '_deploy/hydra-retention-pilot-v1'
REMOTE_HELPER = ARCHIVE / 'collect-retention-model-remote-01.py'
REMOTE_HELPER_SHA = '0bf9321e211c2e60a450d8da1bbe8f3ef01e30497c397ffc2bafd7337df89257'
LOCAL_HELPER = ARCHIVE / 'collect-retention-model-01.py'
PROFILE, RUN_ID = 'peano-hydra-retention-pilot-v1', 'retention-pilot-v1'
SOURCE_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
PLAN_SHA = 'da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0'
RECEIPT_SCHEMA = 'peano-hydra-retention-model-collection-v1'
MAX_JSON, MAX_INDEX = 4 * 1024**2, 256 * 1024
MAX_STREAM, MAX_FILES, MAX_RETAINED = 130 * 1024**2, 128 * 1024**2, 264 * 1024**2
MAX_RSS, MAX_STDERR = 384 * 1024**2, 64 * 1024
CPU, WALL = 20, 150


def require(value, message):
    if not value: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(raw): return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, 'metadata byte cap')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate metadata key')
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(result) is dict, 'metadata object required')
    canonical(result)
    return result


def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(path.parts) <= 64, 'unsafe local directory')
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0: os.close(fd)


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def open_local(path, maximum):
    path = Path(path)
    parent = directory(path.parent)
    try: fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally: os.close(parent)
    stream = os.fdopen(fd, 'rb')
    before = os.fstat(fd)
    try:
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'local input is not bounded single-link regular data')
    except BaseException:
        stream.close(); raise
    return stream, before


def read_local(path, maximum=MAX_JSON):
    stream, before = open_local(path, maximum)
    with stream:
        raw = stream.read(maximum + 1)
        require(len(raw) == before.st_size and signature(before) == signature(os.fstat(stream.fileno())),
                'local input changed during read')
    again, now = open_local(path, maximum); again.close()
    require(signature(now) == signature(before), 'local input was replaced')
    return raw


def hash_local(path, maximum):
    stream, before = open_local(path, maximum)
    checksum, count = hashlib.sha256(), 0
    with stream:
        while True:
            checked_resources()
            block = stream.read(65536)
            if not block: break
            checksum.update(block); count += len(block)
            require(count <= maximum, 'local artifact grew beyond cap')
        require(count == before.st_size and signature(before) == signature(os.fstat(stream.fileno())),
                'local artifact changed while hashing')
    again, now = open_local(path, maximum); again.close()
    require(signature(before) == signature(now), 'local artifact was replaced')
    return {'bytes': count, 'sha256': checksum.hexdigest()}


def create_file(path):
    path = Path(path)
    parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
    finally: os.close(parent)
    before = os.fstat(fd)
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == 0,
            'fresh local regular output required')
    return os.fdopen(fd, 'wb')


def write(path, raw):
    require(type(raw) is bytes and len(raw) <= MAX_JSON, 'metadata output cap')
    with create_file(path) as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    require(read_local(path) == raw, 'metadata publication changed bytes')
    return {'bytes': len(raw), 'sha256': sha(raw)}


def mkdir_exclusive(path):
    path = Path(path)
    parent = directory(path.parent)
    try: os.mkdir(path.name, 0o700, dir_fd=parent)
    finally: os.close(parent)
    fd = directory(path); os.close(fd)


def usage_record():
    own = resource.getrusage(resource.RUSAGE_SELF)
    waited = resource.getrusage(resource.RUSAGE_CHILDREN)
    scale = 1 if sys.platform == 'darwin' else 1024
    return {'wall_seconds': time.monotonic() - STARTED,
            'parent_cpu_seconds': own.ru_utime + own.ru_stime,
            'waited_child_cpu_seconds': waited.ru_utime + waited.ru_stime,
            'accounted_cpu_seconds': own.ru_utime + own.ru_stime + waited.ru_utime + waited.ru_stime,
            'parent_peak_rss_bytes': int(own.ru_maxrss * scale),
            'waited_child_peak_rss_bytes': int(waited.ru_maxrss * scale)}


def checked_resources(final=False):
    value = usage_record()
    require(value['wall_seconds'] < WALL - (0 if final else 3), 'local whole-call collection wall cap')
    require(value['accounted_cpu_seconds'] < CPU, 'local parent plus waited child CPU cap')
    require(max(value['parent_peak_rss_bytes'], value['waited_child_peak_rss_bytes']) < MAX_RSS,
            'local observed peak RSS cap')
    return value


def controls(approval_sha):
    raw = read_local(FROZEN / PACKAGE / 'approval.json')
    require(sha(raw) == approval_sha, 'external approval differs from final local approval bytes')
    approval = decode(raw)
    request_raw = read_local(FROZEN / PACKAGE / 'resource-request.json')
    request_sha = sha(request_raw)
    require(approval.get('schema') == 'peano-hydra-retention-standing-resource-approval-v1'
            and approval.get('profile') == PROFILE and approval.get('run_id') == RUN_ID
            and approval.get('approved') is True and approval.get('request_file_sha256') == request_sha,
            'local approval does not pin the exact actual resource request')
    request = decode(request_raw)
    require(request.get('schema') == 'peano-hydra-retention-resource-request-v1'
            and request.get('status') == 'ready' and request.get('source_commit') == SOURCE_COMMIT
            and request.get('profile') == PROFILE and request.get('run_id') == RUN_ID
            and request.get('reservations') == {
                'train': {'seconds': 7200, 'gpus': 1, 'cpus': 8, 'memory_gib': 64},
                'evaluate': {'seconds': 3600, 'gpus': 1, 'cpus': 8, 'memory_gib': 64}}
            and request.get('maximum_concurrent_gpus') == 1 and request.get('maximum_aggregate_gpu_seconds') == 10800
            and all(request.get(key) is False for key in ('automatic_retry', 'resume', 'refunds')),
            'local resource scope or source differs')
    require(type(request['source_files']) is dict and type(request['payloads']) is dict
            and sha(canonical(request['payloads'])) == request['payloads_sha256'], 'local raw inventories changed')
    stage = request['scientific_inputs']['train']
    require(stage['path'] == PACKAGE + '/train-request.json'
            and request['payloads'][stage['path']] == {key: stage[key] for key in ('bytes', 'sha256')},
            'local train-stage descriptor changed')
    stage_raw = read_local(FROZEN / stage['path'])
    require({'bytes': len(stage_raw), 'sha256': sha(stage_raw)} == {key: stage[key] for key in ('bytes', 'sha256')},
            'local train-stage bytes changed')
    stage_record = decode(stage_raw)
    require(stage_record.get('schema') == 'peano-hydra-retention-pilot-stage-request-v1'
            and stage_record.get('profile') == PROFILE and stage_record.get('run_id') == RUN_ID
            and stage_record.get('stage') == 'train' and stage_record.get('training_plan_sha256') == PLAN_SHA,
            'local training identity differs')
    return {'approval_sha256': approval_sha, 'resource_request_sha256': request_sha,
            'source_commit': SOURCE_COMMIT, 'source_files_sha256': sha(canonical(request['source_files'])),
            'payloads_sha256': request['payloads_sha256'], 'training_request_sha256': sha(stage_raw),
            'training_plan_sha256': PLAN_SHA}


def load_protocol(raw):
    require(sha(raw) == REMOTE_HELPER_SHA, 'reviewed remote collector source changed')
    # Only pure metadata/path validators are called locally. Its main() and its
    # genuine remote launch gate remain uncalled, not replaced with mock handles.
    spec = importlib.util.spec_from_loader('retention_model_collection_protocol', loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(REMOTE_HELPER)
    exec(compile(raw, str(REMOTE_HELPER), 'exec'), module.__dict__)
    return module


def exchange(command, output):
    child, selector, reason, code = None, None, 'not-started', None
    stderr = bytearray()
    digest, count = hashlib.sha256(), 0
    try:
        with create_file(output / 'transfer.tar') as destination:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, start_new_session=True, close_fds=True)
            selector = selectors.DefaultSelector()
            for stream, name in ((child.stdout, 'stdout'), (child.stderr, 'stderr')):
                os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map():
                checked_resources()
                for key, _ in selector.select(.20):
                    block = os.read(key.fileobj.fileno(), 65536)
                    if not block:
                        selector.unregister(key.fileobj); continue
                    if key.data == 'stdout':
                        require(count + len(block) <= MAX_STREAM, 'SSH archive exceeds bounded transfer')
                        destination.write(block); digest.update(block); count += len(block)
                    else:
                        require(len(stderr) + len(block) <= MAX_STDERR, 'SSH stderr exceeds output cap')
                        stderr.extend(block)
            child.wait(timeout=max(.001, WALL - 3 - (time.monotonic() - STARTED)))
            destination.flush(); os.fsync(destination.fileno())
            require(os.fstat(destination.fileno()).st_size == count, 'raw transfer byte count changed')
            reason = 'exited'
    except (ValueError, OSError, TimeoutError, subprocess.TimeoutExpired) as error:
        reason = type(error).__name__ + ': ' + ' '.join(str(error).split())[:1024]
    finally:
        if child is not None:
            # Kill only the one process group created for this exchange. A
            # failed attempt never launches a replacement SSH process.
            if child.poll() is None:
                try: os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                child.wait(timeout=2)
            code = child.returncode
            for stream in (child.stdout, child.stderr):
                if stream is not None: stream.close()
        if selector is not None: selector.close()
    return code, reason, {'bytes': count, 'sha256': digest.hexdigest()}, bytes(stderr)


def extract(transport_path, output, protocol, mode, job, approval_sha, manifest_sha, local_binding, transport_pin):
    stream, before = open_local(transport_path, MAX_STREAM)
    require(before.st_size == transport_pin['bytes'] and before.st_size >= 1024 and before.st_size % 512 == 0,
            'bounded complete USTAR required')
    checksum, consumed, total = hashlib.sha256(), 0, 0
    index, index_pin, expected, seen, created = None, None, [], [], set()
    def take(count):
        nonlocal consumed
        require(0 <= count <= 65536 and consumed + count <= before.st_size, 'truncated or excessive USTAR member')
        raw = stream.read(count)
        require(len(raw) == count, 'truncated USTAR stream')
        consumed += count; checksum.update(raw)
        return raw
    with stream:
        while True:
            checked_resources()
            header = take(512)
            if header == bytes(512):
                remaining = before.st_size - consumed
                require(512 <= remaining <= 19968, 'invalid USTAR terminal padding size')
                while remaining:
                    block = take(min(65536, remaining)); remaining -= len(block)
                    require(not any(block), 'USTAR has data after its terminal blocks')
                break
            require(header[257:265] == b'ustar\x0000' and header[156:157] == tarfile.REGTYPE,
                    'only USTAR regular files are permitted')
            member = tarfile.TarInfo.frombuf(header, 'utf-8', 'strict')
            protocol.path_name(member.name)
            require(not member.linkname and not member.pax_headers and member.isfile()
                    and 0 <= member.size <= MAX_FILES, 'archive special entry or member size changed')
            if index is None:
                require(member.name == 'collection-index.json' and 0 < member.size <= MAX_INDEX,
                        'bounded collection index must be the first archive entry')
                raw = bytearray()
                while len(raw) < member.size: raw.extend(take(min(65536, member.size - len(raw))))
                raw = bytes(raw)
                index = decode(raw)
                require(raw == canonical(index) + b'\n', 'collection index is not canonical original JSON')
                protocol.validate_index(index, mode, job, approval_sha, manifest_sha)
                require(all(index['binding'].get(key) == value for key, value in local_binding.items()),
                        'remote collection differs from actual final local controls')
                expected = sorted(index['files'])
                require(len(expected) <= 17, 'collection has excessive file inventory')
                index_pin = write(output / member.name, raw)
            else:
                require(len(seen) < len(expected) and member.name == expected[len(seen)],
                        'archive member order, duplicates or extra paths differ from inventory')
                item = index['files'][member.name]
                require(member.size == item['bytes'], 'archive member size differs from declaration')
                parts = member.name.split('/')
                for length in range(1, len(parts)):
                    relative = '/'.join(parts[:length])
                    require(relative in ('metadata', 'model', 'model/adapter', 'model/tokenizer'), 'unexpected artifact directory')
                    if relative not in created:
                        mkdir_exclusive(output / relative); created.add(relative)
                digest, count = hashlib.sha256(), 0
                with create_file(output / member.name) as destination:
                    while count < member.size:
                        checked_resources()
                        block = take(min(65536, member.size - count))
                        destination.write(block); digest.update(block); count += len(block)
                    destination.flush(); os.fsync(destination.fileno())
                    info = os.fstat(destination.fileno())
                    require(info.st_size == count and info.st_nlink == 1 and stat.S_ISREG(info.st_mode),
                            'extracted file changed during publication')
                require(count == item['bytes'] and digest.hexdigest() == item['sha256'],
                        'archive member bytes differ from declared original')
                total += count
                require(total <= MAX_FILES, 'extracted aggregate cap')
                seen.append(member.name)
            padding = (-member.size) % 512
            require(not any(take(padding)), 'USTAR member padding is not zero')
        require(signature(before) == signature(os.fstat(stream.fileno())), 'raw archive changed during extraction')
    again, now = open_local(transport_path, MAX_STREAM); again.close()
    require(signature(before) == signature(now) and consumed == before.st_size
            and checksum.hexdigest() == transport_pin['sha256'], 'raw transfer identity changed')
    require(index is not None and seen == expected and total == index['total_file_bytes'], 'incomplete model collection')
    manifest_raw = read_local(output / 'model/manifest.json')
    require({'bytes': len(manifest_raw), 'sha256': sha(manifest_raw)} == index['binding']['manifest']
            and (manifest_sha is None or sha(manifest_raw) == manifest_sha), 'extracted manifest differs from actual pin')
    actual = protocol.manifest_artifacts(decode(manifest_raw), job, approval_sha)
    require(actual == index['declared_artifact_files'], 'archive artifact declarations differ from actual raw manifest')
    for name, item in sorted(index['files'].items()):
        require(hash_local(output / name, MAX_FILES) == {key: item[key] for key in ('bytes', 'sha256')},
                'extracted local artifact/control bytes differ after complete readback')
    return index, index_pin


def retained_bytes(output):
    total, count = 0, 0
    for root, dirs, names in os.walk(output, followlinks=False):
        require(len(dirs) <= 4 and len(names) <= 24, 'local retained output count cap')
        for name in dirs:
            require(stat.S_ISDIR(os.stat(Path(root) / name, follow_symlinks=False).st_mode), 'retained directory became a link')
        for name in names:
            info = os.stat(Path(root) / name, follow_symlinks=False)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'retained output is not single-link regular data')
            count += 1; total += info.st_size
            require(count <= 24 and total <= MAX_RETAINED, 'retained output bytes or count cap')
    return total


def failure_record(error):
    return {'type': type(error).__name__, 'message': ' '.join(str(error).split())[:2048]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--mode', required=True, choices=('inspect', 'model'))
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--expected-helper-sha256', required=True)
    parser.add_argument('--expected-manifest-sha256')
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin', 'isolated uncached macOS collector required')
    require(re.fullmatch(r'[1-9][0-9]{0,19}', args.job_id)
            and re.fullmatch(r'[0-9a-f]{64}', args.approval_sha256)
            and re.fullmatch(r'[0-9a-f]{64}', args.expected_helper_sha256), 'invalid explicit job or raw hash')
    require((args.mode == 'inspect' and args.expected_manifest_sha256 is None)
            or (args.mode == 'model' and type(args.expected_manifest_sha256) is str
                and re.fullmatch(r'[0-9a-f]{64}', args.expected_manifest_sha256)), 'model collection requires a previously observed manifest pin')
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_STREAM, MAX_STREAM))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('local model collection whole-call deadline')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    require(Path(__file__).absolute() == LOCAL_HELPER, 'collector must use its exact archive path')
    local_sha = sha(read_local(LOCAL_HELPER, 128 * 1024))
    require(local_sha == args.expected_helper_sha256, 'local reviewed collector source changed')
    program = read_local(REMOTE_HELPER, 128 * 1024)
    protocol = load_protocol(program)
    local_binding = controls(args.approval_sha256)
    output = args.output_directory
    pattern = ('training-manifest-collected-' if args.mode == 'inspect' else 'trained-model-collected-') + '[0-9]{2}'
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch(pattern, output.name), 'fresh direct archive output required')
    require(shutil.disk_usage(ARCHIVE).free >= MAX_RETAINED + 1024**3, 'insufficient collection disk reserve')
    checked_resources(); mkdir_exclusive(output)
    start = {'schema': 'peano-hydra-retention-model-collection-start-v1', 'mode': args.mode,
        'job_id': args.job_id, 'approval_sha256': args.approval_sha256,
        'expected_manifest_sha256': args.expected_manifest_sha256, 'local_helper_sha256': local_sha,
        'remote_helper_sha256': REMOTE_HELPER_SHA, 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'local_control_binding': local_binding, 'read_only': True, 'automatic_retry': False,
        'limits': {'local_parent_cpu_seconds': CPU, 'local_parent_cpu_hard_seconds': CPU + 1,
            'local_whole_call_wall_seconds': WALL, 'local_observed_parent_or_waited_child_peak_rss_bytes': MAX_RSS,
            'local_parent_plus_waited_child_cpu_completion_cap_seconds': CPU,
            'remote_parent_cpu_seconds': protocol.CPU, 'remote_wall_seconds': protocol.WALL,
            'remote_address_space_bytes': protocol.ADDRESS_SPACE, 'remote_file_write_bytes': 0,
            'raw_transfer_bytes': MAX_STREAM, 'artifact_and_metadata_bytes': MAX_FILES, 'retained_bytes': MAX_RETAINED,
            'stderr_bytes': MAX_STDERR}}
    started_pin = write(output / 'started.json', canonical(start) + b'\n')
    command_text = '/usr/bin/python3.9 -I -B -c ' + shlex.quote(program.decode()) + ' ' + ' '.join(
        shlex.quote(value) for value in (args.mode, args.job_id, args.approval_sha256, args.expected_manifest_sha256 or '-'))
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl', command_text]
    index = index_pin = transport = stderr_pin = None
    error, code, reason = None, None, 'not-started'
    try:
        code, reason, transport, stderr = exchange(command, output)
        stderr_pin = write(output / 'stderr.log', stderr)
        require(code == 0 and reason == 'exited', 'remote collection failed; partial transfer preserved: ' + reason)
        index, index_pin = extract(output / 'transfer.tar', output, protocol, args.mode, args.job_id,
                                  args.approval_sha256, args.expected_manifest_sha256, local_binding, transport)
        require(controls(args.approval_sha256) == local_binding
                and sha(read_local(LOCAL_HELPER, 128 * 1024)) == local_sha
                and sha(read_local(REMOTE_HELPER, 128 * 1024)) == REMOTE_HELPER_SHA,
                'actual local controls or collector source changed during exchange')
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError, tarfile.TarError) as failure:
        error = failure_record(failure)
    retained = retained_bytes(output)
    try:
        usage = checked_resources(final=True)
        require(retained <= MAX_RETAINED - MAX_INDEX, 'no bounded receipt space remains')
    except (ValueError, OSError) as failure:
        error = error or failure_record(failure); usage = usage_record()
    record = {'schema': RECEIPT_SCHEMA,
        'status': ('terminal-manifest-collected' if args.mode == 'inspect' else 'model-bytes-collected-not-semantically-admitted')
                  if error is None else 'failed-partial-output-preserved',
        'mode': args.mode, 'job_id': args.job_id, 'approval_sha256': args.approval_sha256,
        'expected_manifest_sha256': args.expected_manifest_sha256, 'local_helper_sha256': local_sha,
        'remote_helper_sha256': REMOTE_HELPER_SHA, 'output_directory': str(output),
        'returncode': code, 'reason': reason, 'error': error, 'started': started_pin,
        'transport': transport, 'stderr': stderr_pin, 'index': index_pin,
        'files': None if index is None else index['files'], 'binding': None if index is None else index['binding'],
        'accounting': None if index is None else index['accounting'],
        'model_manifest': None if index is None else dict(index['binding']['manifest'], path=str(output / 'model/manifest.json')),
        'resources': dict(usage, retained_bytes_before_receipt=retained), 'limits': start['limits'],
        'read_only': True, 'model_artifact_files_collected': error is None and args.mode == 'model',
        'model_loaded': False, 'artifact_semantics_authenticated': False, 'proofs_independently_verified': False,
        'scheduler_mutation_performed': False, 'remote_files_written': False, 'automatic_retry': False,
        'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    raw_receipt = canonical(record) + b'\n'
    require(len(raw_receipt) <= MAX_INDEX and retained + len(raw_receipt) <= MAX_RETAINED, 'final collection receipt cap')
    receipt_pin = write(output / 'collection-receipt.json', raw_receipt)
    print(json.dumps({'status': record['status'], 'directory': str(output), 'receipt': receipt_pin,
                      'model_manifest': record['model_manifest']}, sort_keys=True), flush=True)
    checked_resources(final=True)
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if error is None else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError, tarfile.TarError) as failure:
        print('retention-model-collection: ' + ' '.join(str(failure).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
