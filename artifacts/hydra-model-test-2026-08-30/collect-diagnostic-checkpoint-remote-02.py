"""Read-only exact-job checkpoint collection, including original lock and debris.

No remote files, imports from the project, model/runtime imports, ps calls,
proof workers or scheduler mutations. Only the externally pinned released
diagnostic job can be read. Incomplete checkpoint metadata is not a score.
"""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import time

ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-diagnostic-v1'
PROFILE = 'peano-hydra-frontier-diagnostic-v1'
PACKAGE = '_deploy/hydra-frontier-diagnostic-v1'
RESULT = 'results/peano-hydra/evaluations/frontier-diagnostic-v1'
LEDGER = 'logs/hydra-frontier-diagnostic-v1.jsonl'
SOURCE_COMMIT = '612d1ea9e4905dfe2af104696924a19bc5883752'
MAX_TOTAL = 64 * 1024**2
MAX_JSON = 4 * 1024**2
EXACT_JOB = '21453693'
EXACT_APPROVAL = '10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e'
EXACT_REQUEST = '49117e3c7d62f9fd50931a84abfcbf3ce2c24d50fff672ae78d7b526c7b5354b'
CHECKPOINT = RESULT + '/checkpoint'
MAX_CHECKPOINT_ENTRIES = 132
MAX_DATA_FILES = 140
MAX_CHECKPOINT_FILE = 4 * 1024**2
MAX_CHECKPOINT_DEPTH = 8
INDEX_SCHEMA = 'peano-hydra-diagnostic-checkpoint-collection-index-v1'
TERMINAL = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(0 < len(raw) <= MAX_JSON, 'metadata byte limit')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate metadata key')
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda text: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(value) is dict, 'metadata object required')
    return value


def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(path.parts) <= 64, 'unsafe directory')
    access = getattr(os, 'O_PATH', os.O_RDONLY)
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def opened(relative, maximum):
    require(re.fullmatch(r'[A-Za-z0-9_.\-/]{1,1024}', relative)
            and all(part not in ('', '.', '..') for part in relative.split('/')), 'unsafe collection path')
    parent_path, leaf = (ROOT + '/' + relative).rsplit('/', 1)
    parent = directory(parent_path)
    try:
        fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    stream = os.fdopen(fd, 'rb')
    info = os.fstat(fd)
    try:
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 <= info.st_size <= maximum,
                'not one bounded regular collection file')
    except BaseException:
        stream.close()
        raise
    return stream, info


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def read_file(relative, maximum, retain=False):
    stream, before = opened(relative, maximum)
    with stream:
        digest, count, body = hashlib.sha256(), 0, bytearray()
        while True:
            block = stream.read(65536)
            if not block:
                break
            count += len(block)
            require(count <= maximum, 'file grew beyond bound')
            digest.update(block)
            if retain:
                body.extend(block)
        require(count == before.st_size and signature(before) == signature(os.fstat(stream.fileno())),
                'file changed during collection inventory')
    again, current = opened(relative, maximum)
    again.close()
    require(signature(current) == signature(before), 'collection file was replaced')
    return {'bytes': count, 'sha256': digest.hexdigest()}, bytes(body), signature(before)


def bound_job(job, approval_sha):
    _, raw, _ = read_file(PACKAGE + '/approval.json', MAX_JSON, True)
    require(sha(raw) == approval_sha, 'externally pinned approval differs')
    approval = decode(raw)
    require(approval.get('schema') == 'peano-hydra-frontier-diagnostic-resource-approval-v1'
            and approval.get('profile') == PROFILE and approval.get('run_id') == 'frontier-diagnostic-v1'
            and approval.get('approved') is True, 'wrong diagnostic approval')
    _, request_raw, _ = read_file(PACKAGE + '/resource-request.json', MAX_JSON, True)
    require(sha(request_raw) == approval['request_file_sha256'], 'approved request changed')
    request = decode(request_raw)
    expected = {'evaluate': {'seconds': 900, 'gpus': 1, 'cpus': 8, 'memory_gib': 64}}
    require(request.get('profile') == PROFILE and request.get('source_commit') == SOURCE_COMMIT
            and request.get('reservations') == expected and request.get('maximum_aggregate_gpu_seconds') == 900,
            'wrong diagnostic resource or source scope')
    _, ledger_raw, _ = read_file(LEDGER, 256 * 1024, True)
    lines = ledger_raw.splitlines(keepends=True)
    require(ledger_raw.endswith(b'\n') and len(lines) == 6, 'complete released one-use ledger required')
    previous, events = '0' * 64, []
    kinds = ('header', 'reserve', 'evaluate-accepted', 'held-validated', 'release-authorized', 'evaluate-released')
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {'index', 'previous_sha256', 'payload', 'sha256'}
            and event['index'] == index and event['previous_sha256'] == previous
            and event['sha256'] == sha(canonical({key: event[key] for key in ('index', 'previous_sha256', 'payload')}))
            and canonical(event) + b'\n' == line and event['payload'].get('kind') == kinds[index],
            'released job ledger chain differs')
        previous = event['sha256']
        events.append(event['payload'])
    header, reserve, accepted, held, barrier, released = events
    identity = header['identity']
    require(header.get('schema') == 'peano-hydra-frontier-diagnostic-held-job-ledger-v1'
        and header.get('profile') == PROFILE and header.get('run_id') == 'frontier-diagnostic-v1'
        and identity.get('approval_sha256') == approval_sha
        and identity.get('request_file_sha256') == sha(request_raw)
        and identity.get('source_commit') == SOURCE_COMMIT
        and identity.get('source_files_sha256') == sha(canonical(request['source_files']))
        and identity.get('payloads_sha256') == request['payloads_sha256']
        and identity.get('job_script_sha256') == {'evaluate': request['source_files']['slurm/peano_hydra_frontier_diagnostic.sbatch']['sha256']}
        and reserve.get('reservations') == expected and accepted.get('job_id') == job
        and accepted.get('dependency_job_id') is None and barrier.get('jobs') == {'evaluate': job}
        and released.get('job_id') == job and set(held.get('snapshots', {})) == {'evaluate'},
        'job is not the exact approved released diagnostic')
    return {'job_id': job, 'approval_sha256': approval_sha, 'resource_request_sha256': sha(request_raw),
        'evaluation_request_sha256': request['payloads'][PACKAGE + '/evaluation-request.json']['sha256'],
        'source_commit': SOURCE_COMMIT, 'ledger_sha256': sha(ledger_raw), 'ledger_events': 6,
        'reserved_gpu_seconds': 900}


def accounting(job):
    args = ['sacct', '-n', '-P', '-j', job,
        '--format=JobIDRaw,JobName%80,State%32,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%256,WorkDir%4096,Account,Partition,User']
    child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    streams, selector = {'stdout': bytearray(), 'stderr': bytearray()}, selectors.DefaultSelector()
    started = time.monotonic()
    try:
        for label in streams:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            require(time.monotonic() - started < 10, 'accounting command deadline')
            for key, _ in selector.select(0.1):
                block = os.read(key.fileobj.fileno(), 8192)
                if not block:
                    selector.unregister(key.fileobj)
                else:
                    streams[key.data].extend(block)
                    require(len(streams[key.data]) <= 65536, 'accounting output cap')
        child.wait(timeout=max(0.01, 10 - (time.monotonic() - started)))
    finally:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=2)
        selector.close()
        child.stdout.close()
        child.stderr.close()
    require(child.returncode == 0, 'terminal accounting unavailable')
    text = streams['stdout'].decode('utf-8')
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    require(1 <= len(rows) <= 8 and all(len(row) == 13 and row[0] in (job, job + '.batch', job + '.extern') for row in rows),
            'accounting returned unexpected columns or jobs')
    top = [row for row in rows if row[0] == job]
    require(len(top) == 1, 'unique terminal job accounting required')
    top = top[0]
    require(top[1] == PROFILE + '-evaluate' and top[5] == '15' and top[7] == '64G'
        and top[9] == ROOT and top[10:13] == ['plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret'],
        'accounting identity or requested resources differ')
    require(top[2].split()[0] in TERMINAL, 'collect only after the exact job reaches a terminal state')
    return {'command': args, 'returncode': child.returncode, 'stdout': text,
            'stderr': streams['stderr'].decode('utf-8', 'replace'), 'top_row': top,
            'state': top[2], 'exit_code': top[3], 'elapsed_seconds': int(top[4])}



def checkpoint_inventory():
    """Retain every bounded real entry; reject links/specials, never filter debris."""
    try:
        root_fd = directory(ROOT + '/' + CHECKPOINT)
    except FileNotFoundError:
        return {'present':False, 'root_signature':None, 'entries':{}}
    entries = {}
    root_before = signature(os.fstat(root_fd))
    def visit(fd, prefix, depth):
        require(depth <= MAX_CHECKPOINT_DEPTH, 'checkpoint directory depth cap')
        with os.scandir(fd) as stream:
            for entry in stream:
                name = prefix + entry.name
                require(re.fullmatch(r'[A-Za-z0-9_./-]{1,1024}', name)
                        and all(part not in ('', '.', '..') for part in name.split('/')),
                        'unsafe checkpoint entry name')
                require(name not in entries and len(entries) < MAX_CHECKPOINT_ENTRIES,
                        'checkpoint entry count or alias cap')
                info = entry.stat(follow_symlinks=False)
                require(not stat.S_ISLNK(info.st_mode), 'checkpoint symlink rejected without dereference')
                if stat.S_ISDIR(info.st_mode):
                    item = {'kind':'directory', 'source_signature':list(signature(info)),
                            'source_mode':stat.S_IMODE(info.st_mode)}
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                            and 0 <= info.st_size <= MAX_CHECKPOINT_FILE,
                            'checkpoint entry is not bounded regular single-link data')
                    item = {'kind':'file', 'bytes':info.st_size,
                            'source_signature':list(signature(info)), 'source_mode':stat.S_IMODE(info.st_mode)}
                entries[name] = item
                # Validate USTAR representability before writing any transport bytes.
                test = tarfile.TarInfo('checkpoint/' + name + ('/' if item['kind'] == 'directory' else ''))
                test.type = tarfile.DIRTYPE if item['kind'] == 'directory' else tarfile.REGTYPE
                test.tobuf(format=tarfile.USTAR_FORMAT)
                if item['kind'] == 'directory':
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        require(signature(os.fstat(child)) == tuple(item['source_signature']),
                                'checkpoint subdirectory changed before inventory')
                        visit(child, name + '/', depth + 1)
                        require(signature(os.fstat(child)) == tuple(item['source_signature']),
                                'checkpoint subdirectory changed during inventory')
                    finally:
                        os.close(child)
                    require(signature(os.stat(entry.name, dir_fd=fd, follow_symlinks=False))
                            == tuple(item['source_signature']), 'checkpoint directory pathname changed')
    try:
        visit(root_fd, '', 0)
        require(signature(os.fstat(root_fd)) == root_before, 'checkpoint root changed during inventory')
    finally:
        os.close(root_fd)
    again = directory(ROOT + '/' + CHECKPOINT)
    try:
        require(signature(os.fstat(again)) == root_before, 'checkpoint root pathname changed')
    finally:
        os.close(again)
    return {'present':True, 'root_signature':list(root_before), 'entries':dict(sorted(entries.items()))}


def fixed_metadata(job):
    return {
        'run.json': (RESULT + '/run.json', 4 * 1024**2),
        'execution-status.json': (RESULT + '/execution-status.json', 4 * 1024**2),
        'diagnostic.out.log': ('logs/' + PROFILE + '-evaluate-' + job + '.out', 2 * 1024**2),
        'diagnostic.err.log': ('logs/' + PROFILE + '-evaluate-' + job + '.err', 2 * 1024**2),
        'ledger.jsonl': (LEDGER, 256 * 1024),
        'approval.json': (PACKAGE + '/approval.json', 4096),
        'resource-request.json': (PACKAGE + '/resource-request.json', 4 * 1024**2),
        'evaluation-request.json': (PACKAGE + '/evaluation-request.json', 4 * 1024**2),
    }


def build_inventory(job, binding, status):
    snapshot = checkpoint_inventory()
    wanted = fixed_metadata(job)
    for name, item in snapshot['entries'].items():
        if item['kind'] == 'file':
            wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    require(len(wanted) <= MAX_DATA_FILES, 'collected data-file count cap')
    files, signatures, absent, total = {}, {}, [], 0
    entries = {name:dict(item) for name,item in snapshot['entries'].items()}
    for local, (remote, maximum) in sorted(wanted.items()):
        try:
            identity, _, before = read_file(remote, maximum)
        except FileNotFoundError:
            require(not local.startswith('checkpoint/'), 'checkpoint entry disappeared after inventory')
            absent.append(local)
            continue
        total += identity['bytes']
        require(total <= MAX_TOTAL, 'checkpoint collection aggregate cap')
        files[local], signatures[local] = dict(identity, remote_path=remote), before
        if local.startswith('checkpoint/'):
            name = local[len('checkpoint/'):]
            require(list(before) == entries[name]['source_signature']
                    and identity['bytes'] == entries[name]['bytes'],
                    'checkpoint entry changed after directory inventory')
            entries[name]['sha256'] = identity['sha256']
    mandatory = {'ledger.jsonl', 'approval.json', 'resource-request.json', 'evaluation-request.json'}
    require(mandatory <= set(files), 'released job control metadata must be collected')
    require(files['ledger.jsonl']['sha256'] == binding['ledger_sha256']
            and files['approval.json']['sha256'] == binding['approval_sha256'] == EXACT_APPROVAL
            and files['resource-request.json']['sha256'] == binding['resource_request_sha256'] == EXACT_REQUEST
            and files['evaluation-request.json']['sha256'] == binding['evaluation_request_sha256'],
            'collected controls differ from exact released job binding')
    require(checkpoint_inventory() == snapshot, 'checkpoint inventory changed during hashing')
    directories = ([] if not snapshot['present'] else ['checkpoint'])
    directories += ['checkpoint/' + name for name,item in entries.items() if item['kind'] == 'directory']
    directories.sort(key=lambda name:(name.count('/'), name))
    index = {
        'schema':INDEX_SCHEMA, 'binding':binding,
        'observed_at_utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'accounting':status, 'files':files, 'directories':directories,
        'absent_files':absent, 'total_file_bytes':total,
        'checkpoint_root_present':snapshot['present'],
        'checkpoint_root_signature':snapshot['root_signature'],
        'checkpoint_entry_inventory':entries,
        'checkpoint_goal_records_collected':True,
        'checkpoint_all_actual_entries_collected':True,
        'checkpoint_original_lock_collected':'.lock' in entries and entries['.lock']['kind'] == 'file',
        'checkpoint_debris_filtered':False, 'checkpoint_files_modified':False,
        'checkpoint_metadata_is_not_verified_proof_evidence':True,
        'proofs_independently_verified':False, 'read_only':True,
        'model_artifact_directories_read':False, 'model_frameworks_imported':False,
        'scheduler_mutation_performed':False, 'automatic_retry':False,
        'limits':{'checkpoint_entries':MAX_CHECKPOINT_ENTRIES, 'data_files':MAX_DATA_FILES,
                  'checkpoint_file_bytes':MAX_CHECKPOINT_FILE, 'aggregate_file_bytes':MAX_TOTAL},
    }
    return index, wanted, signatures, snapshot


def emit_archive(index, wanted, signatures, stream):
    header = canonical(index) + b'\n'
    require(len(header) <= 1024**2, 'checkpoint collection index cap')
    with tarfile.open(fileobj=stream, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        member = tarfile.TarInfo('collection-index.json')
        member.size, member.mode = len(header), 0o600
        archive.addfile(member, io.BytesIO(header))
        for name in index['directories']:
            member = tarfile.TarInfo(name + '/')
            member.type, member.mode = tarfile.DIRTYPE, 0o700
            archive.addfile(member)
        for local, item in sorted(index['files'].items()):
            source, before = opened(item['remote_path'], wanted[local][1])
            with source:
                require(signature(before) == signatures[local], 'collected entry changed before streaming')
                member = tarfile.TarInfo(local)
                member.size, member.mode = item['bytes'], 0o600
                archive.addfile(member, source)
                require(signature(before) == signature(os.fstat(source.fileno())),
                        'collected entry changed during streaming')
            again, current = opened(item['remote_path'], wanted[local][1])
            again.close()
            require(signature(current) == signatures[local], 'collected entry pathname changed during streaming')


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 3,
            'isolated exact-job arguments required')
    job, approval_sha = sys.argv[1:]
    require(job == EXACT_JOB and approval_sha == EXACT_APPROVAL, 'only the exact approved diagnostic job may be collected')
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('remote checkpoint collection wall cap')))
    signal.alarm(45)
    binding = bound_job(job, approval_sha)
    status = accounting(job)
    index, wanted, signatures, snapshot = build_inventory(job, binding, status)
    emit_archive(index, wanted, signatures, sys.stdout.buffer)
    require(checkpoint_inventory() == snapshot, 'checkpoint entries changed through transport')
    for local, item in sorted(index['files'].items()):
        actual, _, after = read_file(item['remote_path'], wanted[local][1])
        require(actual == {key:item[key] for key in ('bytes', 'sha256')}
                and after == signatures[local], 'collected bytes changed through transport')
    for local in index['absent_files']:
        try:
            unexpected, _ = opened(wanted[local][0], wanted[local][1])
        except FileNotFoundError:
            continue
        else:
            unexpected.close()
            raise ValueError('previously absent metadata appeared during collection')
    require(bound_job(job, approval_sha) == binding, 'release/approval binding changed during checkpoint collection')
    signal.alarm(0)


if __name__ == '__main__':
    main()
