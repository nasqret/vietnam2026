#!/usr/bin/env python3
"""Collect the exact terminal diagnostic checkpoint without verifying proofs.

One read-only SSH exchange; all original checkpoint entries are retained.
No model, native validator, scheduler mutation, retry, or remote file writes.
Partial local transport/extraction remains evidence if any guard rejects it.
"""
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
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
REMOTE_HELPER = ARCHIVE / 'collect-diagnostic-checkpoint-remote-02.py'
REMOTE_HELPER_SHA = 'c36be7646549d0e5feba6dbc0a27bf01d6dc70c536ab5dc24f8ead8b17ad563f'
LOCAL_HELPER = ARCHIVE / 'collect-diagnostic-checkpoint-02.py'
EXECUTION = ARCHIVE.parents[1] / '_deploy/hydra-model-test-execution-20260830'
PACKAGE = EXECUTION / '_deploy/hydra-frontier-diagnostic-v1'
REMOTE_ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-diagnostic-v1'
PROFILE = 'peano-hydra-frontier-diagnostic-v1'
REMOTE_PACKAGE = '_deploy/hydra-frontier-diagnostic-v1'
RESULT = 'results/peano-hydra/evaluations/frontier-diagnostic-v1'
EXACT_JOB = '21453693'
EXACT_APPROVAL = '10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e'
EXACT_REQUEST = '49117e3c7d62f9fd50931a84abfcbf3ce2c24d50fff672ae78d7b526c7b5354b'
EXACT_EVALUATION = '9c4fe30f658558410bea892ae201529e2114d7959c54a5257ed56e2547bc9c88'
SOURCE_COMMIT = '612d1ea9e4905dfe2af104696924a19bc5883752'
INDEX_SCHEMA = 'peano-hydra-diagnostic-checkpoint-collection-index-v1'
RECEIPT_SCHEMA = 'peano-hydra-diagnostic-checkpoint-collection-v1'
MAX_STREAM = 66 * 1024**2
MAX_FILES = 64 * 1024**2
MAX_RETAINED = 136 * 1024**2
MAX_RSS = 384 * 1024**2
MAX_CHECKPOINT_ENTRIES = 132
MAX_DATA_FILES = 140
MAX_CHECKPOINT_FILE = 4 * 1024**2
MANDATORY = {'ledger.jsonl', 'approval.json', 'resource-request.json', 'evaluation-request.json'}
TERMINAL = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def decode(raw, maximum):
    require(0 < len(raw) <= maximum, 'metadata byte cap')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate metadata key')
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(result) is dict, 'metadata object required')
    return result


def path_name(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]{1,1024}', name)
            and all(part not in ('', '.', '..') for part in name.split('/')), 'unsafe archive relative path')
    return name


def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(path.parts) <= 64, 'unsafe local directory')
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def read_local(path, maximum):
    path = Path(path)
    parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                    and 0 <= before.st_size <= maximum, 'local input is not bounded single-link regular data')
            raw = stream.read(maximum + 1)
            require(len(raw) == before.st_size and signature(before) == signature(os.fstat(stream.fileno()))
                    and signature(before) == signature(os.stat(path.name, dir_fd=parent, follow_symlinks=False)),
                    'local input changed during read')
        return raw
    finally:
        os.close(parent)


def write(path, raw):
    require(isinstance(raw, (bytes, memoryview)) and len(raw) <= MAX_STREAM, 'local output byte cap')
    path = Path(path)
    parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'exclusive output regular file required')
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
            after = os.fstat(stream.fileno())
            require(after.st_size == len(raw) and after.st_nlink == 1
                    and (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
                    and signature(after) == signature(os.stat(path.name, dir_fd=parent, follow_symlinks=False)),
                    'local output identity changed')
    finally:
        os.close(parent)
    return {'bytes': len(raw), 'sha256': sha(raw)}


def mkdir_exclusive(path):
    path = Path(path)
    parent = directory(path.parent)
    try:
        os.mkdir(path.name, 0o700, dir_fd=parent)
        child = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            require(signature(os.fstat(child)) == signature(os.stat(path.name, dir_fd=parent, follow_symlinks=False)),
                    'new output directory changed')
        finally:
            os.close(child)
    finally:
        os.close(parent)


def checked_rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    value = value if sys.platform == 'darwin' else value * 1024
    require(value < MAX_RSS, 'local checked RSS envelope reached')
    return value


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
            checked_rss()
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


def fixed_metadata(job):
    return {
        'run.json': (RESULT + '/run.json', 4 * 1024**2),
        'execution-status.json': (RESULT + '/execution-status.json', 4 * 1024**2),
        'diagnostic.out.log': ('logs/' + PROFILE + '-evaluate-' + job + '.out', 2 * 1024**2),
        'diagnostic.err.log': ('logs/' + PROFILE + '-evaluate-' + job + '.err', 2 * 1024**2),
        'ledger.jsonl': ('logs/hydra-frontier-diagnostic-v1.jsonl', 256 * 1024),
        'approval.json': (REMOTE_PACKAGE + '/approval.json', 4096),
        'resource-request.json': (REMOTE_PACKAGE + '/resource-request.json', 4 * 1024**2),
        'evaluation-request.json': (REMOTE_PACKAGE + '/evaluation-request.json', 4 * 1024**2),
    }


def source_signature(item, kind):
    value = item['source_signature']
    require(type(value) is list and len(value) == 7 and all(type(x) is int for x in value)
            and all(value[i] >= 0 for i in (0, 1, 3)) and value[6] >= 1,
            'invalid checkpoint source signature')
    require((stat.S_ISDIR(value[2]) if kind == 'directory' else stat.S_ISREG(value[2]))
            and item['source_mode'] == stat.S_IMODE(value[2]), 'checkpoint source kind or mode changed')
    if kind == 'file':
        require(value[6] == 1 and value[3] == item['bytes'], 'checkpoint source file size or links changed')


def validate_index(index, job, approval_sha, evaluation_sha):
    require(index.get('schema') == INDEX_SCHEMA, 'wrong checkpoint collection schema')
    binding = index['binding']
    require(type(binding) is dict and set(binding) == {'job_id', 'approval_sha256', 'resource_request_sha256',
        'evaluation_request_sha256', 'source_commit', 'ledger_sha256', 'ledger_events', 'reserved_gpu_seconds'}
        and binding['job_id'] == job == EXACT_JOB and binding['approval_sha256'] == approval_sha == EXACT_APPROVAL
        and binding['resource_request_sha256'] == EXACT_REQUEST
        and binding['evaluation_request_sha256'] == evaluation_sha == EXACT_EVALUATION
        and binding['source_commit'] == SOURCE_COMMIT and binding['ledger_events'] == 6
        and binding['reserved_gpu_seconds'] == 900
        and re.fullmatch(r'[0-9a-f]{64}', binding['ledger_sha256']), 'collection binding changed')
    accounting = index['accounting']
    top = accounting['top_row']
    rows = [line.split('|') for line in accounting['stdout'].splitlines() if line.strip()]
    require(accounting['returncode'] == 0 and 1 <= len(rows) <= 8
        and all(len(row) == 13 and row[0] in (job, job + '.batch', job + '.extern') for row in rows)
        and [row for row in rows if row[0] == job] == [top]
        and top[1] == PROFILE + '-evaluate' and top[5] == '15' and top[7] == '64G'
        and top[9] == REMOTE_ROOT and top[10:13] == ['plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret']
        and top[2].split()[0] in TERMINAL and accounting['state'] == top[2]
        and accounting['exit_code'] == top[3] and accounting['elapsed_seconds'] == int(top[4]),
        'terminal accounting binding changed')
    for key in ('checkpoint_goal_records_collected', 'checkpoint_all_actual_entries_collected',
                'checkpoint_metadata_is_not_verified_proof_evidence', 'read_only'):
        require(index.get(key) is True, 'collection evidence scope changed: ' + key)
    for key in ('checkpoint_debris_filtered', 'checkpoint_files_modified', 'proofs_independently_verified',
                'model_artifact_directories_read', 'model_frameworks_imported', 'scheduler_mutation_performed', 'automatic_retry'):
        require(index.get(key) is False, 'collection work scope changed: ' + key)
    require(index['limits'] == {'checkpoint_entries': MAX_CHECKPOINT_ENTRIES, 'data_files': MAX_DATA_FILES,
        'checkpoint_file_bytes': MAX_CHECKPOINT_FILE, 'aggregate_file_bytes': MAX_FILES}, 'collection caps changed')
    entries, present = index['checkpoint_entry_inventory'], index['checkpoint_root_present']
    require(type(entries) is dict and len(entries) <= MAX_CHECKPOINT_ENTRIES and type(present) is bool,
            'checkpoint inventory cap or type changed')
    if present:
        source_signature({'source_signature': index['checkpoint_root_signature'],
                          'source_mode': stat.S_IMODE(index['checkpoint_root_signature'][2])}, 'directory')
    else:
        require(not entries and index['checkpoint_root_signature'] is None, 'absent checkpoint has entries')
    directories = ['checkpoint'] if present else []
    wanted = fixed_metadata(job)
    for name, item in entries.items():
        path_name(name)
        require(type(item) is dict and item.get('kind') in ('file', 'directory'), 'unknown checkpoint entry kind')
        kind = item['kind']
        require(len(name.split('/')) <= (8 if kind == 'directory' else 9), 'checkpoint nesting cap')
        expected_keys = {'kind', 'source_signature', 'source_mode'}
        if kind == 'file':
            expected_keys |= {'bytes', 'sha256'}
            require(type(item['bytes']) is int and 0 <= item['bytes'] <= MAX_CHECKPOINT_FILE
                    and re.fullmatch(r'[0-9a-f]{64}', item['sha256']), 'checkpoint file declaration changed')
            wanted['checkpoint/' + name] = (RESULT + '/checkpoint/' + name, MAX_CHECKPOINT_FILE)
        else:
            directories.append('checkpoint/' + name)
        require(set(item) == expected_keys, 'unexpected checkpoint entry fields')
        source_signature(item, kind)
        if '/' in name:
            parent = name.rsplit('/', 1)[0]
            require(parent in entries and entries[parent]['kind'] == 'directory', 'checkpoint directory parent missing')
    directories.sort(key=lambda name: (name.count('/'), name))
    require(index['directories'] == directories, 'checkpoint archive directories differ from original inventory')
    require(index['checkpoint_original_lock_collected'] is ('.lock' in entries and entries['.lock']['kind'] == 'file'),
            'original checkpoint lock claim differs')
    files = index['files']
    require(type(files) is dict and len(files) <= MAX_DATA_FILES and MANDATORY <= set(files)
            and set(files) <= set(wanted), 'unapproved or missing collected metadata')
    checkpoint_files = {'checkpoint/' + name for name, item in entries.items() if item['kind'] == 'file'}
    require({name for name in files if name.startswith('checkpoint/')} == checkpoint_files,
            'checkpoint entries were filtered or fabricated')
    require(index['absent_files'] == sorted(set(fixed_metadata(job)) - set(files)), 'absent metadata declaration changed')
    total = 0
    for name, item in files.items():
        path_name(name)
        require(type(item) is dict and set(item) == {'bytes', 'sha256', 'remote_path'}
            and type(item['bytes']) is int and 0 <= item['bytes'] <= wanted[name][1]
            and re.fullmatch(r'[0-9a-f]{64}', item['sha256']) and item['remote_path'] == wanted[name][0],
            'collected file scope or size differs')
        if name.startswith('checkpoint/'):
            original = entries[name[len('checkpoint/'):]]
            require(all(item[key] == original[key] for key in ('bytes', 'sha256')), 'checkpoint file pin differs')
        total += item['bytes']
    require(type(index['total_file_bytes']) is int and index['total_file_bytes'] == total <= MAX_FILES,
            'collected aggregate size differs')
    for name, key in (('approval.json', 'approval_sha256'), ('resource-request.json', 'resource_request_sha256'),
                      ('evaluation-request.json', 'evaluation_request_sha256'), ('ledger.jsonl', 'ledger_sha256')):
        require(files[name]['sha256'] == binding[key], 'raw collected control pin differs: ' + name)


def strict_members(raw):
    require(type(raw) is bytes and 1024 <= len(raw) <= MAX_STREAM and len(raw) % 512 == 0, 'bounded USTAR bytes required')
    view, offset, count = memoryview(raw), 0, 0
    while offset + 512 <= len(raw):
        header = raw[offset:offset + 512]
        if header == bytes(512):
            require(1024 <= len(raw) - offset <= 20480 and not any(view[offset:]), 'invalid archive end padding')
            return
        count += 1
        require(count <= MAX_CHECKPOINT_ENTRIES + len(fixed_metadata(EXACT_JOB)) + 2, 'USTAR entry cap')
        require(header[257:265] == b'ustar\x0000' and header[156:157] in (tarfile.REGTYPE, tarfile.DIRTYPE),
                'only original USTAR regular files and directories are permitted')
        member = tarfile.TarInfo.frombuf(header, 'utf-8', 'strict')
        path_name(member.name)
        require(not member.linkname and not member.pax_headers and 0 <= member.size <= MAX_CHECKPOINT_FILE,
                'archive special entry or member cap')
        require(not member.isdir() or member.size == 0, 'archive directory has data')
        begin, end = offset + 512, offset + 512 + member.size
        next_offset = begin + (member.size + 511) // 512 * 512
        require(next_offset <= len(raw) and not any(view[end:next_offset]), 'archive data truncation or padding')
        yield member, view[begin:end]
        offset = next_offset
    raise ValueError('archive terminal blocks missing')


def extract(raw, output, job, approval_sha, evaluation_sha):
    index, index_pin, expected, seen, total = None, None, [], [], 0
    for member, body in strict_members(raw):
        checked_rss()
        if index is None:
            require(member.isfile() and member.name == 'collection-index.json' and 0 < member.size <= 1024**2,
                    'bounded collection index must be first')
            index = decode(bytes(body), 1024**2)
            require(canonical(index) + b'\n' == body, 'collection index is not canonical original JSON')
            validate_index(index, job, approval_sha, evaluation_sha)
            expected = [(name, 'directory') for name in index['directories']]
            expected += [(name, 'file') for name in sorted(index['files'])]
            index_pin = write(output / member.name, body)
            continue
        position = len(seen)
        require(position < len(expected), 'archive has undeclared extra entry')
        name, kind = expected[position]
        require(member.name == name and (member.isdir() if kind == 'directory' else member.isfile()),
                'archive entry order, path or kind differs from inventory')
        if kind == 'directory':
            mkdir_exclusive(output / name)
        else:
            pin = index['files'][name]
            require(member.size == pin['bytes'] and sha(body) == pin['sha256'], 'archive file bytes differ from inventory')
            written = write(output / name, body)
            require(written == {key: pin[key] for key in ('bytes', 'sha256')}, 'local written identity differs')
            total += member.size
            require(total <= MAX_FILES, 'extracted aggregate cap')
        seen.append((name, kind))
    require(index is not None and seen == expected and total == index['total_file_bytes'], 'archive is incomplete')
    return index, index_pin


def error_chain(error):
    result, seen = [], set()
    while error is not None and len(result) < 4 and id(error) not in seen:
        seen.add(id(error))
        result.append({'type': type(error).__name__, 'message': ' '.join(str(error).split())[:1024]})
        error = error.__cause__ or (None if error.__suppress_context__ else error.__context__)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode, 'isolated uncached local Python required')
    require(args.job_id == EXACT_JOB and args.approval_sha256 == EXACT_APPROVAL, 'only the exact approved job is supported')
    resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_STREAM, MAX_STREAM))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('local checkpoint collection wall cap')))
    signal.alarm(75)
    require(Path(__file__).absolute() == LOCAL_HELPER, 'local collector must use its exact archive path')
    local_sha = sha(read_local(LOCAL_HELPER, 128 * 1024))
    program = read_local(REMOTE_HELPER, 128 * 1024)
    require(sha(program) == REMOTE_HELPER_SHA, 'reviewed remote checkpoint collector changed')
    approval_raw = read_local(PACKAGE / 'approval.json', 4096)
    require(sha(approval_raw) == EXACT_APPROVAL, 'local raw approval differs')
    approval = decode(approval_raw, 4096)
    request_raw = read_local(PACKAGE / 'resource-request.json', MAX_CHECKPOINT_FILE)
    require(sha(request_raw) == EXACT_REQUEST == approval['request_file_sha256'], 'approved resource request differs')
    request = decode(request_raw, MAX_CHECKPOINT_FILE)
    require(request['source_commit'] == SOURCE_COMMIT and request['payloads'][REMOTE_PACKAGE + '/evaluation-request.json']['sha256']
            == EXACT_EVALUATION, 'approved source or evaluation request differs')
    require(sha(read_local(PACKAGE / 'evaluation-request.json', MAX_CHECKPOINT_FILE)) == EXACT_EVALUATION,
            'local original evaluation request differs')
    output = args.output_directory
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch(r'diagnostic-checkpoint-collected-[0-9]{2}', output.name), 'fresh direct archive output required')
    require(shutil.disk_usage(ARCHIVE).free >= MAX_RETAINED + 512 * 1024**2, 'insufficient collection disk reserve')
    mkdir_exclusive(output)
    started = write(output / 'started.json', canonical({'schema': 'peano-hydra-diagnostic-checkpoint-collection-start-v1',
        'job_id': EXACT_JOB, 'approval_sha256': EXACT_APPROVAL, 'local_helper_sha256': local_sha,
        'remote_helper_sha256': REMOTE_HELPER_SHA, 'read_only': True, 'automatic_retry': False,
        'remote_limits': {'cpu_seconds': 20, 'wall_seconds': 45, 'address_space_bytes': 320 * 1024**2, 'file_write_bytes': 0},
        'local_limits': {'cpu_seconds': 30, 'cpu_hard_seconds': 31, 'wall_seconds': 75, 'stream_bytes': MAX_STREAM,
        'retained_bytes': MAX_RETAINED, 'checked_peak_rss_bytes': MAX_RSS}}) + b'\n')
    # Preserve the proven observer's login PATH for sacct; isolated Python is absolute.
    remote = '/usr/bin/python3.9 -I -B -c ' + shlex.quote(program.decode()) + ' ' + EXACT_JOB + ' ' + EXACT_APPROVAL
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl', remote]
    code, stdout, stderr, reason = exchange(command)
    transport = write(output / 'transport.tar', stdout)
    stderr_pin = write(output / 'stderr.log', stderr)
    index, index_pin, error = None, None, None
    try:
        require(code == 0 and reason == 'exited', 'remote checkpoint collection did not finish successfully')
        index, index_pin = extract(stdout, output, EXACT_JOB, EXACT_APPROVAL, EXACT_EVALUATION)
        require(sha(read_local(LOCAL_HELPER, 128 * 1024)) == local_sha
                and sha(read_local(REMOTE_HELPER, 128 * 1024)) == REMOTE_HELPER_SHA, 'collector source changed during exchange')
    except (ValueError, OSError, KeyError, TypeError, IndexError, tarfile.TarError) as failure:
        error = error_chain(failure)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    elapsed = time.monotonic() - STARTED
    peak = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024
    # Only our exclusive regular files are counted; no local symlink is followed.
    retained = 0
    for parent, dirs, names in os.walk(output, followlinks=False):
        require(len(dirs) <= MAX_CHECKPOINT_ENTRIES and len(names) <= MAX_DATA_FILES + 6, 'local output count cap')
        for name in names:
            item = os.stat(Path(parent) / name, follow_symlinks=False)
            require(stat.S_ISREG(item.st_mode) and item.st_nlink == 1, 'local output is no longer regular single-link data')
            retained += item.st_size
    if elapsed >= 75 or peak >= MAX_RSS or retained >= MAX_RETAINED - 65536:
        error = error or [{'type': 'ResourceEnvelope', 'message': 'local checkpoint collection envelope reached'}]
    record = {'schema': RECEIPT_SCHEMA,
        'status': 'collected-not-proof-verified' if error is None else 'failed-partial-output-preserved',
        'job_id': EXACT_JOB, 'approval_sha256': EXACT_APPROVAL, 'evaluation_request_sha256': EXACT_EVALUATION,
        'local_helper_sha256': local_sha, 'remote_helper_sha256': REMOTE_HELPER_SHA,
        'remote_program_sha256': REMOTE_HELPER_SHA, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'returncode': code, 'reason': reason, 'error': error, 'transport': transport, 'stderr': stderr_pin,
        'started': started, 'index': index_pin,
        'files': None if index is None else index['files'], 'binding': None if index is None else index['binding'],
        'accounting': None if index is None else index['accounting'],
        'checkpoint_entry_inventory': None if index is None else index['checkpoint_entry_inventory'],
        'checkpoint_all_actual_entries_collected': error is None,
        'checkpoint_original_lock_collected': False if index is None else index['checkpoint_original_lock_collected'],
        'checkpoint_debris_filtered': False, 'checkpoint_files_modified': False,
        'resources': {'wall_seconds': elapsed, 'cpu_seconds': usage.ru_utime + usage.ru_stime,
            'maxrss_bytes': peak, 'retained_bytes_before_receipt': retained},
        'read_only': True, 'model_loaded': False, 'proofs_independently_verified': False,
        'checkpoint_goal_records_collected': error is None, 'automatic_retry': False}
    receipt = write(output / 'collection-receipt.json', canonical(record) + b'\n')
    signal.alarm(0)
    print(json.dumps({'status': record['status'], 'directory': str(output), 'receipt': receipt,
                     'checkpoint_entries': None if index is None else len(index['checkpoint_entry_inventory'])}, sort_keys=True))
    return 0 if error is None else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError) as error:
        print('diagnostic-checkpoint-collection: ' + ' '.join(str(error).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
