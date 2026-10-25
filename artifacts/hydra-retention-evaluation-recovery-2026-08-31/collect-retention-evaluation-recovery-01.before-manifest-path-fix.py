#!/usr/bin/env python3
"""Collect all actual terminal retention checkpoint evidence without replay.

The fresh model collector's reviewed streaming/file primitives are copied here
unchanged. This caller admits no model, origin, evaluation row or proof; the
remote frozen launcher owns the genuine source/job/ledger authentication.
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

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
FROZEN = ARCHIVE.parents[1] / '_deploy/hydra-retention-evaluation-recovery-execution-20260831'
PACKAGE = '_deploy/hydra-retention-evaluation-recovery-v1'
LOCAL_HELPER = ARCHIVE / 'collect-retention-evaluation-recovery-01.py'
REMOTE_HELPER = ARCHIVE / 'collect-retention-evaluation-recovery-remote-01.py'
REMOTE_HELPER_SHA = '5c6c6e6937732df6f222559bcaaea5e9daca35dc41a157875bc63c4bf17e041e'
PRODUCER_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
RECEIPT_SCHEMA = 'peano-hydra-retention-evaluation-recovery-collection-v1'
MAX_JSON, MAX_INDEX = 4 * 1024**2, 1024**2
MAX_STREAM, MAX_FILES, MAX_RETAINED = 66 * 1024**2, 64 * 1024**2, 136 * 1024**2
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

def failure_record(error):
    return {'type': type(error).__name__, 'message': ' '.join(str(error).split())[:2048]}


def load_protocol(raw):
    require(sha(raw) == REMOTE_HELPER_SHA, 'reviewed remote evaluation collector changed')
    spec = importlib.util.spec_from_loader('retention_evaluation_recovery_collection_protocol', loader=None)
    module = importlib.util.module_from_spec(spec); module.__file__ = str(REMOTE_HELPER)
    exec(compile(raw, str(REMOTE_HELPER), 'exec'), module.__dict__)
    return module


def controls(approval_sha, source_commit, protocol):
    # Pure metadata joins; scientific admission is not executed by collection.
    result = protocol.control_binding(lambda name: read_local(FROZEN / PACKAGE / name),
                                      source_commit, approval_sha)
    request = decode(read_local(FROZEN / PACKAGE / 'resource-request.json'))
    for name, pin in protocol.BOOTSTRAP_SOURCES.items():
        require(request['source_files'][name]['sha256'] == pin
                and sha(read_local(FROZEN / name, 65536)) == pin,
                'local frozen recovery gate bootstrap differs from the reviewed source')
    return result


def validate_local_join(index, local):
    binding, identity = index['binding'], index['binding']['execution_identity']
    for key, value in local.items():
        require((identity if key in ('source_files_sha256', 'payloads_sha256') else binding).get(key) == value,
                'actual local and remote source/control identities differ: ' + key)


def extract(path, output, protocol, mode, job, approval, header_sha, source_commit, head_sha, manifest_sha, local, transport_pin):
    stream, before = open_local(path, MAX_STREAM)
    require(before.st_size == transport_pin['bytes'] and before.st_size >= 1024 and before.st_size % 512 == 0,
            'bounded complete USTAR required')
    checksum, consumed, total = hashlib.sha256(), 0, 0
    index, index_pin, expected, seen = None, None, [], []
    def take(count):
        nonlocal consumed
        require(0 <= count <= 65536 and consumed + count <= before.st_size, 'truncated or excessive USTAR entry')
        raw = stream.read(count)
        require(len(raw) == count, 'truncated USTAR stream')
        consumed += count; checksum.update(raw)
        return raw
    with stream:
        while True:
            checked_resources()
            raw_header = take(512)
            if raw_header == bytes(512):
                remaining = before.st_size - consumed
                require(512 <= remaining <= 19968, 'invalid USTAR terminal padding size')
                while remaining:
                    block = take(min(65536, remaining)); remaining -= len(block)
                    require(not any(block), 'USTAR has data after terminal blocks')
                break
            require(raw_header[257:265] == b'ustar\x0000' and raw_header[156:157] in (tarfile.REGTYPE, tarfile.DIRTYPE),
                    'only original USTAR regular files and directories are permitted')
            member = tarfile.TarInfo.frombuf(raw_header, 'utf-8', 'strict')
            protocol.path_name(member.name)
            require(not member.linkname and not member.pax_headers and 0 <= member.size <= 48 * 1024**2
                    and (not member.isdir() or member.size == 0), 'archive special entry or size changed')
            if index is None:
                require(member.isfile() and member.name == 'collection-index.json' and 0 < member.size <= MAX_INDEX,
                        'bounded collection index must be first')
                raw = bytearray()
                while len(raw) < member.size: raw.extend(take(min(65536, member.size - len(raw))))
                raw = bytes(raw); index = decode(raw)
                require(raw == canonical(index) + b'\n', 'collection index is not canonical original JSON')
                protocol.validate_index(index, mode, job, approval, header_sha, source_commit, head_sha, manifest_sha)
                validate_local_join(index, local)
                expected = [(name, 'directory') for name in index['directories']]
                expected += [(name, 'file') for name in sorted(index['files'])]
                require(len(expected) <= protocol.MAX_CHECKPOINT_ENTRIES + protocol.MAX_DATA_FILES + 1, 'archive entry count cap')
                index_pin = write(output / member.name, raw)
            else:
                kind = 'directory' if member.isdir() else 'file'
                require(len(seen) < len(expected) and (member.name, kind) == expected[len(seen)],
                        'archive order, paths, kinds, duplicates or extras differ from original inventory')
                if kind == 'directory': mkdir_exclusive(output / member.name)
                else:
                    item = index['files'][member.name]
                    require(member.size == item['bytes'], 'archive file size differs from declaration')
                    digest, count = hashlib.sha256(), 0
                    with create_file(output / member.name) as destination:
                        while count < member.size:
                            checked_resources()
                            block = take(min(65536, member.size - count))
                            destination.write(block); digest.update(block); count += len(block)
                        destination.flush(); os.fsync(destination.fileno())
                        info = os.fstat(destination.fileno())
                        require(info.st_size == count and info.st_nlink == 1 and stat.S_ISREG(info.st_mode),
                                'local extracted file changed')
                    require(count == item['bytes'] and digest.hexdigest() == item['sha256'], 'actual archive bytes differ')
                    total += count
                    require(total <= MAX_FILES, 'extracted aggregate byte cap')
                seen.append((member.name, kind))
            require(not any(take((-member.size) % 512)), 'USTAR member padding is not zero')
        require(signature(before) == signature(os.fstat(stream.fileno())), 'raw archive changed while extracting')
    again, now = open_local(path, MAX_STREAM); again.close()
    require(signature(before) == signature(now) and consumed == before.st_size
            and checksum.hexdigest() == transport_pin['sha256'], 'raw transport identity changed')
    require(index is not None and seen == expected and total == index['total_file_bytes'], 'incomplete original checkpoint archive')
    for name, item in sorted(index['files'].items()):
        require(hash_local(output / name, MAX_FILES) == {key: item[key] for key in ('bytes', 'sha256')},
                'complete local readback differs from actual original bytes')
    if 'execution-binding.json' in index['files']:
        protocol.validate_execution_metadata(read_local(output / 'execution-binding.json'), index['binding'])
    if 'execution-status.json' in index['files']:
        protocol.validate_interruption_metadata(read_local(output / 'execution-status.json'), index['binding'])
    return index, index_pin


def retained_bytes(output, protocol):
    total, count = 0, 0
    for root, dirs, names in os.walk(output, followlinks=False):
        require(len(dirs) <= protocol.MAX_CHECKPOINT_ENTRIES and len(names) <= protocol.MAX_DATA_FILES + 6,
                'retained output count cap')
        for name in dirs:
            require(stat.S_ISDIR(os.stat(Path(root) / name, follow_symlinks=False).st_mode), 'retained directory became a link')
        for name in names:
            info = os.stat(Path(root) / name, follow_symlinks=False)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'retained output no longer single-link regular data')
            count += 1; total += info.st_size
            require(count <= protocol.MAX_DATA_FILES + 6 and total <= MAX_RETAINED, 'retained output byte/count cap')
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--mode', choices=('inspect', 'checkpoint'), required=True)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--source-header-sha256', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--expected-helper-sha256', required=True)
    parser.add_argument('--expected-checkpoint-head-sha256')
    parser.add_argument('--expected-model-manifest-sha256')
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
            and Path(__file__).absolute() == LOCAL_HELPER, 'exact isolated uncached local evaluation collector required')
    require(re.fullmatch(r'[1-9][0-9]{0,19}', args.job_id) and args.job_id not in ('21456251', '21457058'),
            'actual new evaluation job id required; original spent jobs cannot be adopted')
    require(re.fullmatch(r'[0-9a-f]{40}', args.source_commit) and args.source_commit != PRODUCER_COMMIT,
            'externally supplied actual new frozen source commit required')
    for value in (args.approval_sha256, args.source_header_sha256, args.expected_helper_sha256):
        require(re.fullmatch(r'[0-9a-f]{64}', value), 'external actual raw/source-header SHA required')
    head_sha, manifest_sha = args.expected_checkpoint_head_sha256, args.expected_model_manifest_sha256
    require((args.mode == 'inspect' and head_sha is None and manifest_sha is None) or
            (args.mode == 'checkpoint' and type(head_sha) is str and (head_sha == 'absent' or re.fullmatch(r'[0-9a-f]{64}', head_sha))
                and type(manifest_sha) is str and re.fullmatch(r'[0-9a-f]{64}', manifest_sha)),
            'full checkpoint collection requires separately observed raw HEAD and candidate manifest pins')
    head_sha, manifest_sha = head_sha or '-', manifest_sha or '-'
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_STREAM, MAX_STREAM)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('local evaluation collection whole-call wall cap')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    local_sha = sha(read_local(LOCAL_HELPER, 128 * 1024))
    require(local_sha == args.expected_helper_sha256, 'reviewed local evaluation collector changed')
    program = read_local(REMOTE_HELPER, 128 * 1024)
    protocol = load_protocol(program)
    local = controls(args.approval_sha256, args.source_commit, protocol)
    output = args.output_directory
    pattern = ('evaluation-inspected-' if args.mode == 'inspect' else 'evaluation-checkpoint-collected-') + '[0-9]{2}'
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch(pattern, output.name), 'fresh direct archive collection directory required')
    require(shutil.disk_usage(ARCHIVE).free >= MAX_RETAINED + 1024**3, 'insufficient retained collection disk reserve')
    checked_resources(); mkdir_exclusive(output)
    start = {'schema': 'peano-hydra-retention-evaluation-recovery-collection-start-v1', 'mode': args.mode,
        'job_id': args.job_id, 'approval_sha256': args.approval_sha256, 'source_header_sha256': args.source_header_sha256,
        'source_commit': args.source_commit,
        'expected_checkpoint_head_sha256': head_sha, 'expected_model_manifest_sha256': manifest_sha,
        'local_helper_sha256': local_sha, 'remote_helper_sha256': REMOTE_HELPER_SHA, 'local_control_binding': local,
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'read_only': True, 'automatic_retry': False,
        'limits': {'local_parent_cpu_seconds': CPU, 'local_parent_cpu_hard_seconds': CPU + 1, 'local_whole_call_wall_seconds': WALL,
            'local_parent_plus_waited_child_cpu_completion_cap_seconds': CPU,
            'local_observed_parent_or_waited_child_peak_rss_bytes': MAX_RSS,
            'remote_parent_cpu_seconds': protocol.CPU, 'remote_wall_seconds': protocol.WALL,
            'remote_address_space_bytes': protocol.ADDRESS_SPACE, 'remote_file_write_bytes': 0,
            'raw_transfer_bytes': MAX_STREAM, 'aggregate_original_file_bytes': MAX_FILES,
            'retained_bytes': MAX_RETAINED, 'stderr_bytes': MAX_STDERR}}
    started_pin = write(output / 'started.json', canonical(start) + b'\n')
    remote = '/usr/bin/python3.9 -I -B -c ' + shlex.quote(program.decode()) + ' ' + ' '.join(shlex.quote(value) for value in
        (args.mode, args.job_id, args.approval_sha256, args.source_header_sha256, args.source_commit, head_sha, manifest_sha))
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl', remote]
    index = index_pin = transport = stderr_pin = None
    error, code, reason = None, None, 'not-started'
    try:
        code, reason, transport, stderr = exchange(command, output)
        stderr_pin = write(output / 'stderr.log', stderr)
        require(code == 0 and reason == 'exited', 'remote collection failed; partial transfer preserved: ' + reason)
        index, index_pin = extract(output / 'transfer.tar', output, protocol, args.mode, args.job_id,
            args.approval_sha256, args.source_header_sha256, args.source_commit, head_sha, manifest_sha, local, transport)
        require(controls(args.approval_sha256, args.source_commit, protocol) == local and sha(read_local(LOCAL_HELPER, 128 * 1024)) == local_sha
                and sha(read_local(REMOTE_HELPER, 128 * 1024)) == REMOTE_HELPER_SHA,
                'local control/helper identity changed during collection')
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError, tarfile.TarError) as failure:
        error = failure_record(failure)
    retained = retained_bytes(output, protocol)
    try:
        usage = checked_resources(final=True)
        require(retained <= MAX_RETAINED - MAX_INDEX, 'no bounded receipt space remains')
    except (ValueError, OSError) as failure:
        error = error or failure_record(failure); usage = usage_record()
    record = {'schema': RECEIPT_SCHEMA, 'status': ('terminal-metadata-inspected' if args.mode == 'inspect' else
        'collected-terminal-failure-no-head' if index is not None and index['checkpoint_head'] is None else 'collected-not-proof-verified')
        if error is None else 'failed-partial-output-preserved', 'mode': args.mode,
        'job_id': args.job_id, 'approval_sha256': args.approval_sha256, 'source_header_sha256': args.source_header_sha256,
        'source_commit': args.source_commit,
        'local_helper_sha256': local_sha, 'remote_helper_sha256': REMOTE_HELPER_SHA, 'output_directory': str(output),
        'expected_checkpoint_head_sha256': head_sha, 'expected_model_manifest_sha256': manifest_sha,
        'returncode': code, 'reason': reason, 'error': error, 'started': started_pin, 'transport': transport, 'stderr': stderr_pin,
        'index': index_pin, 'files': None if index is None else index['files'], 'binding': None if index is None else index['binding'],
        'accounting': None if index is None else index['accounting'],
        'checkpoint_head': None if index is None else index['checkpoint_head'],
        'checkpoint_observation': None if index is None else index['checkpoint_observation'],
        'model_manifest': None if index is None else index['model_manifest'],
        'checkpoint_entry_inventory': None if index is None else index['checkpoint_entry_inventory'],
        'checkpoint_all_actual_entries_collected': error is None and args.mode == 'checkpoint',
        'checkpoint_original_lock_collected': False if index is None else index['checkpoint_original_lock_collected'],
        'checkpoint_debris_filtered': False, 'checkpoint_files_modified': False,
        'resources': dict(usage, retained_bytes_before_receipt=retained), 'limits': start['limits'],
        'read_only': True, 'model_loaded': False, 'proofs_independently_verified': False,
        'full_comparison_verified': False, 'scheduler_mutation_performed': False, 'remote_files_written': False,
        'automatic_retry': False, 'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    raw = canonical(record) + b'\n'
    require(len(raw) <= MAX_INDEX and retained + len(raw) <= MAX_RETAINED, 'final collection receipt cap')
    receipt_pin = write(output / 'collection-receipt.json', raw)
    print(json.dumps({'status': record['status'], 'directory': str(output), 'receipt': receipt_pin,
                      'checkpoint_head': record['checkpoint_head'], 'model_manifest': record['model_manifest']}, sort_keys=True), flush=True)
    checked_resources(final=True); signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if error is None else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError, tarfile.TarError) as failure:
        print('retention-evaluation-recovery-collection: ' + ' '.join(str(failure).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
