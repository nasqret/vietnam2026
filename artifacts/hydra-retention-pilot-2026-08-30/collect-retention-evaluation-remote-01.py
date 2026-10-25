"""Retain actual terminal retention-evaluation evidence, never proof scores.

File traversal/hash/USTAR primitives are copied unchanged from reviewed model
and diagnostic collectors. Only the genuine frozen retention gate authenticates
jobs, original ledgers and the completed candidate manifest. Inspection omits
proof rows; full collection requires externally observed HEAD/manifest pins.
"""
import time
STARTED = time.monotonic()
import datetime
import fcntl
import hashlib
import importlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import tarfile

ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-pilot-v1'
PROFILE, RUN_ID = 'peano-hydra-retention-pilot-v1', 'retention-pilot-v1'
PACKAGE = '_deploy/hydra-retention-pilot-v1'
RESULT = 'results/peano-hydra/evaluations/retention-pilot-v1'
MODEL = 'results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1'
CHECKPOINT = RESULT + '/checkpoint'
SOURCE_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
INDEX_SCHEMA = 'peano-hydra-retention-evaluation-collection-index-v1'
MAX_JSON, MAX_TOTAL, MAX_CHECKPOINT_FILE = 4 * 1024**2, 64 * 1024**2, 4 * 1024**2
MAX_CHECKPOINT_ENTRIES, MAX_DATA_FILES, MAX_CHECKPOINT_DEPTH = 264, 288, 8
CPU, WALL, ADDRESS_SPACE = 20, 120, 320 * 1024**2
BOOTSTRAP_SOURCES = {
    'training/peano_hydra/__init__.py': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    'training/peano_hydra/retention_launch.py': 'bed869bec7d2d873885fd90c97e90c1910948ab39a492caa829299f7f599c9c0',
    'training/peano_hydra/search_launch.py': '3d393ceb547c5199297748af647c7c6c51c67bf176011dcd68b257dc6d3f97ca',
}
TERMINAL = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}
MANDATORY = {'model-manifest.json', 'train-ledger.jsonl', 'evaluate-ledger.jsonl',
             'approval.json', 'resource-request.json', 'train-request.json', 'evaluate-request.json',
             'inputs.json', 'token-preflight.json', 'evaluation-plan.json'}
INSPECTION_ENTRIES = ('HEAD.json', 'header.json', '.lock')

def require(value, message):
    if not value: raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def sha(raw): return hashlib.sha256(raw).hexdigest()

def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, 'metadata byte cap')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate metadata key')
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(value) is dict, 'metadata object required')
    canonical(value)
    return value

def path_name(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]{1,1024}', name)
            and all(part not in ('', '.', '..') for part in name.split('/')), 'unsafe relative collection path')
    return name

def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(path.parts) <= 64, 'unsafe directory')
    access = getattr(os, 'O_PATH', os.O_RDONLY)
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for number, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if number == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0: os.close(fd)

def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)

def opened(relative, maximum):
    path_name(relative)
    parent_name, leaf = (ROOT + '/' + relative).rsplit('/', 1)
    parent = directory(parent_name)
    try: fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally: os.close(parent)
    stream = os.fdopen(fd, 'rb')
    before = os.fstat(fd)
    try:
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'collection input is not a bounded single-link regular file')
    except BaseException:
        stream.close(); raise
    return stream, before

def read_file(relative, maximum, retain=False):
    stream, before = opened(relative, maximum)
    with stream:
        checksum, count, body = hashlib.sha256(), 0, bytearray()
        while True:
            require(time.monotonic() - STARTED < WALL, 'remote collection whole-call wall deadline')
            block = stream.read(65536)
            if not block: break
            count += len(block); checksum.update(block)
            require(count <= maximum, 'collection input grew beyond cap')
            if retain: body.extend(block)
        require(count == before.st_size and signature(before) == signature(os.fstat(stream.fileno())),
                'collection input changed during hashing')
    current, now = opened(relative, maximum)
    current.close()
    require(signature(now) == signature(before), 'collection input was replaced')
    return {'bytes': count, 'sha256': checksum.hexdigest()}, bytes(body), signature(before)

class NoFrameworks(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        require(fullname.split('.')[0] not in {'torch', 'transformers', 'peft', 'tokenizers', 'accelerate', 'datasets', 'vllm'},
                'collection cannot import a model/tokenizer framework')
        return None

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


def bound_job(job, approval_sha, header_sha):
    for relative, expected in BOOTSTRAP_SOURCES.items():
        require(read_file(relative, 65536)[0]['sha256'] == expected, 'frozen metadata gate bootstrap source changed')
    existing = sys.modules.get('training.peano_hydra.retention_launch')
    require(not any(name == 'training' or name.startswith('training.') for name in sys.modules)
            or existing is not None and existing.ROOT == Path(ROOT), 'foreign deployment already imported')
    sys.path.insert(0, ROOT)
    gate = importlib.import_module('training.peano_hydra.retention_launch')
    require(gate.ROOT == Path(ROOT), 'metadata gate came from another source')
    approval, request = gate.validate_metadata(approval_sha)
    bound = gate.identity(approval, request, approval_sha)
    require(bound['source_commit'] == SOURCE_COMMIT and sha(canonical(bound)) == header_sha,
            'actual installed source/request header changed')
    lock = gate._lock(False)
    try:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        states = {stage: gate.load_ledger(stage, bound) for stage in gate.STAGES}
        gate._history(states, bound)
        train, evaluate = states['train'], states['evaluate']
        require(evaluate['job_id'] == job and evaluate['phase'] == train['phase'] == 'released'
                and len(evaluate['events']) == len(train['events']) == 6
                and evaluate['gpu_seconds'] == 3600 and train['gpu_seconds'] == 7200,
                'exact released one-use training and evaluation ledgers required')
        manifest = gate._training_completed(states)
        require(manifest == evaluate['model_manifest'], 'completed candidate changed from actual evaluation reservation')
        train_pin = read_file(gate.LEDGERS['train'], 256 * 1024)[0]
        evaluate_pin = read_file(gate.LEDGERS['evaluate'], 256 * 1024)[0]
    finally: os.close(lock)
    command = ['sacct', '-n', '-P', '-X', '-j', job,
        '--format=JobIDRaw,JobName%80,State%32,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%256,WorkDir%4096,Account,Partition,User']
    output = gate.safe.run(command)
    rows = [line.split('|') for line in output.splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) in (13, 14)
            and (len(rows[0]) == 13 or rows[0][13] == ''), 'unique terminal evaluation accounting required')
    row = rows[0][:13]
    require(row[0:2] == [job, PROFILE + '-evaluate'] and row[2].split()[0] in TERMINAL
            and re.fullmatch(r'[0-9]+:[0-9]+', row[3]) and row[4].isdigit() and 0 <= int(row[4]) <= 604800
            and row[5:8] == ['60', '8', '64G'] and row[9:] == [ROOT, gate.ACCOUNT, gate.PARTITION, 'plgnasqret'],
            'evaluation must be terminal with its exact original scheduler identity and resources')
    binding = {'job_id': job, 'train_job_id': train['job_id'], 'approval_sha256': approval_sha,
        'resource_request_sha256': bound['resource_request_sha256'], 'source_commit': SOURCE_COMMIT,
        'execution_identity': bound, 'source_header_sha256': header_sha,
        'training_request_sha256': request['scientific_inputs']['train']['sha256'],
        'evaluation_request_sha256': request['scientific_inputs']['evaluate']['sha256'],
        'training_ledger_sha256': train_pin['sha256'], 'evaluation_ledger_sha256': evaluate_pin['sha256'],
        'training_ledger_events': 6, 'evaluation_ledger_events': 6,
        'reserved_gpu_seconds': 3600, 'training_reserved_gpu_seconds': 7200, 'model_manifest': manifest,
        'candidate_matches_original_evaluation_reservation': True,
        'validated_by_frozen_training_completed': True}
    status = {'command': command, 'stdout': output, 'top_row': row, 'state': row[2], 'exit_code': row[3],
              'elapsed_seconds': int(row[4]), 'returncode': 0}
    return binding, status


def fixed_metadata(job, train_job):
    result = {
        'model-manifest.json': (MODEL + '/manifest.json', MAX_JSON),
        'execution-binding.json': (RESULT + '/execution-binding.json', MAX_JSON),
        'execution-status.json': (RESULT + '/execution-status.json', MAX_JSON),
        'evaluation.json': (RESULT + '/evaluation.json', 48 * 1024**2),
        'train-ledger.jsonl': ('logs/hydra-retention-pilot-v1-train.jsonl', 256 * 1024),
        'evaluate-ledger.jsonl': ('logs/hydra-retention-pilot-v1-evaluate.jsonl', 256 * 1024),
        'train.out.log': ('logs/' + PROFILE + '-train-' + train_job + '.out', MAX_JSON),
        'train.err.log': ('logs/' + PROFILE + '-train-' + train_job + '.err', MAX_JSON),
        'evaluate.out.log': ('logs/' + PROFILE + '-evaluate-' + job + '.out', MAX_JSON),
        'evaluate.err.log': ('logs/' + PROFILE + '-evaluate-' + job + '.err', MAX_JSON),
    }
    for name in ('approval.json', 'resource-request.json', 'train-request.json', 'evaluate-request.json',
                 'inputs.json', 'token-preflight.json', 'evaluation-plan.json'):
        result[name] = (PACKAGE + '/' + name, MAX_JSON)
    return result


def optional_pin(relative):
    try: return read_file(relative, MAX_CHECKPOINT_FILE)[0]
    except FileNotFoundError: return None


def check_external_pins(mode, head, manifest, expected_head, expected_manifest):
    if mode == 'inspect':
        require(expected_head == expected_manifest == '-', 'inspection must not substitute previously invented pins')
    else:
        require(manifest['sha256'] == expected_manifest, 'actual candidate differs from external observed manifest pin')
        require((head is None and expected_head == 'absent') or
                (head is not None and head['sha256'] == expected_head), 'actual HEAD differs from external inspection')


def build_inventory(mode, binding, status, head):
    # Inspection exposes raw metadata only; it deliberately does not scan/read
    # goal rows. Full mode retains every actual entry, including lock and debris.
    if mode == 'checkpoint':
        snapshot = checkpoint_inventory()
    else:
        try:
            fd = directory(ROOT + '/' + CHECKPOINT)
            try: root_signature = list(signature(os.fstat(fd)))
            finally: os.close(fd)
            snapshot = {'present': True, 'root_signature': root_signature, 'entries': {}}
        except FileNotFoundError:
            snapshot = {'present': False, 'root_signature': None, 'entries': {}}
    wanted = fixed_metadata(binding['job_id'], binding['train_job_id'])
    if mode == 'inspect': wanted.pop('evaluation.json')
    entries = {name: dict(item) for name, item in snapshot['entries'].items()}
    if mode == 'checkpoint':
        for name, item in entries.items():
            if item['kind'] == 'file': wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    else:
        for name in INSPECTION_ENTRIES: wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    require(len(wanted) <= MAX_DATA_FILES, 'evaluation collection data-file cap')
    files, signatures, absent, total = {}, {}, [], 0
    for local, (remote, maximum) in sorted(wanted.items()):
        try: identity, _, before = read_file(remote, maximum)
        except FileNotFoundError:
            require(local not in MANDATORY and not (mode == 'checkpoint' and local.startswith('checkpoint/')),
                    'required input or inventoried checkpoint entry disappeared')
            absent.append(local); continue
        total += identity['bytes']
        require(total <= MAX_TOTAL, 'evaluation collection aggregate byte cap')
        files[local], signatures[local] = dict(identity, remote_path=remote), before
        if local.startswith('checkpoint/') and mode == 'checkpoint':
            item = entries[local[len('checkpoint/'):]]
            require(list(before) == item['source_signature'] and identity['bytes'] == item['bytes'], 'checkpoint entry changed')
            item['sha256'] = identity['sha256']
    directories = ['checkpoint'] if snapshot['present'] else []
    directories += ['checkpoint/' + name for name, item in entries.items() if item['kind'] == 'directory']
    directories.sort(key=lambda name: (name.count('/'), name))
    index = {'schema': INDEX_SCHEMA, 'mode': mode, 'binding': binding, 'accounting': status,
        'observed_at_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'files': files, 'directories': directories, 'absent_files': sorted(absent), 'total_file_bytes': total,
        'checkpoint_head': head, 'model_manifest': binding['model_manifest'],
        'checkpoint_root_present': snapshot['present'], 'checkpoint_root_signature': snapshot['root_signature'],
        'checkpoint_entry_inventory': entries if mode == 'checkpoint' else None,
        'checkpoint_goal_records_collected': mode == 'checkpoint',
        'checkpoint_all_actual_entries_collected': mode == 'checkpoint',
        'checkpoint_original_lock_collected': 'checkpoint/.lock' in files,
        'checkpoint_debris_filtered': False, 'checkpoint_files_modified': False,
        'checkpoint_metadata_is_not_verified_proof_evidence': True, 'proofs_independently_verified': False,
        'read_only': True, 'model_artifact_directories_read': False, 'model_frameworks_imported': False,
        'scheduler_mutation_performed': False, 'automatic_retry': False,
        'limits': {'checkpoint_entries': MAX_CHECKPOINT_ENTRIES, 'data_files': MAX_DATA_FILES,
                   'checkpoint_file_bytes': MAX_CHECKPOINT_FILE, 'aggregate_file_bytes': MAX_TOTAL}}
    return index, wanted, signatures, snapshot


def source_signature(item, kind):
    value = item['source_signature']
    require(type(value) is list and len(value) == 7 and all(type(x) is int for x in value)
            and all(value[i] >= 0 for i in (0, 1, 3)) and value[6] >= 1,
            'invalid checkpoint source signature')
    require((stat.S_ISDIR(value[2]) if kind == 'directory' else stat.S_ISREG(value[2]))
            and item['source_mode'] == stat.S_IMODE(value[2]), 'checkpoint source kind or mode changed')
    if kind == 'file': require(value[6] == 1 and value[3] == item['bytes'], 'checkpoint file size or links changed')


def validate_index(index, mode, job, approval_sha, header_sha, expected_head='-', expected_manifest='-'):
    require(index.get('schema') == INDEX_SCHEMA and index.get('mode') == mode and mode in ('inspect', 'checkpoint'),
            'wrong retention evaluation collection index')
    binding = index['binding']
    identity = binding['execution_identity']
    require(binding['job_id'] == job and binding['approval_sha256'] == approval_sha
            and binding['source_commit'] == SOURCE_COMMIT and binding['source_header_sha256'] == header_sha
            and identity['approval_sha256'] == approval_sha and identity['source_commit'] == SOURCE_COMMIT
            and binding['resource_request_sha256'] == identity['resource_request_sha256']
            and sha(canonical(identity)) == header_sha and re.fullmatch(r'[1-9][0-9]{0,19}', binding['train_job_id'])
            and binding['reserved_gpu_seconds'] == 3600 and binding['training_reserved_gpu_seconds'] == 7200
            and binding['training_ledger_events'] == binding['evaluation_ledger_events'] == 6
            and binding['candidate_matches_original_evaluation_reservation'] is True
            and binding['validated_by_frozen_training_completed'] is True, 'actual released evaluation identity changed')
    accounting, top = index['accounting'], index['accounting']['top_row']
    rows = [line.split('|') for line in accounting['stdout'].splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) in (13, 14) and (len(rows[0]) == 13 or rows[0][13] == '')
            and rows[0][:13] == top and top[:2] == [job, PROFILE + '-evaluate'] and top[2].split()[0] in TERMINAL
            and accounting['returncode'] == 0 and accounting['state'] == top[2] and accounting['exit_code'] == top[3]
            and re.fullmatch(r'[0-9]+:[0-9]+', top[3]) and top[4].isdigit() and 0 <= int(top[4]) <= 604800
            and accounting['elapsed_seconds'] == int(top[4]) and top[5:8] == ['60', '8', '64G']
            and top[9:] == [ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret'],
            'actual terminal accounting changed')
    for key in ('checkpoint_metadata_is_not_verified_proof_evidence', 'read_only'):
        require(index[key] is True, 'collection inflated its evidence scope')
    for key in ('checkpoint_debris_filtered', 'checkpoint_files_modified', 'proofs_independently_verified',
                'model_artifact_directories_read', 'model_frameworks_imported', 'scheduler_mutation_performed', 'automatic_retry'):
        require(index[key] is False, 'collection altered evidence or work scope')
    require(index['checkpoint_goal_records_collected'] is (mode == 'checkpoint')
            and index['checkpoint_all_actual_entries_collected'] is (mode == 'checkpoint')
            and index['limits'] == {'checkpoint_entries': MAX_CHECKPOINT_ENTRIES, 'data_files': MAX_DATA_FILES,
                'checkpoint_file_bytes': MAX_CHECKPOINT_FILE, 'aggregate_file_bytes': MAX_TOTAL}, 'collection caps or completeness scope changed')
    present, entries = index['checkpoint_root_present'], index['checkpoint_entry_inventory']
    require(type(present) is bool, 'checkpoint presence must be observed')
    if present:
        source_signature({'source_signature': index['checkpoint_root_signature'],
                          'source_mode': stat.S_IMODE(index['checkpoint_root_signature'][2])}, 'directory')
    else: require(index['checkpoint_root_signature'] is None, 'absent checkpoint has a directory signature')
    wanted = fixed_metadata(job, binding['train_job_id'])
    if mode == 'inspect': wanted.pop('evaluation.json')
    directories = ['checkpoint'] if present else []
    if mode == 'checkpoint':
        require(type(entries) is dict and len(entries) <= MAX_CHECKPOINT_ENTRIES and (present or not entries),
                'checkpoint entry inventory changed')
        for name, item in entries.items():
            path_name(name)
            require(type(item) is dict and item.get('kind') in ('file', 'directory'), 'unknown checkpoint entry kind')
            kind = item['kind']; source_signature(item, kind)
            require(len(name.split('/')) <= (8 if kind == 'directory' else 9), 'checkpoint nesting cap')
            fields = {'kind', 'source_signature', 'source_mode'}
            if kind == 'file':
                fields |= {'bytes', 'sha256'}
                require(type(item['bytes']) is int and 0 <= item['bytes'] <= MAX_CHECKPOINT_FILE
                        and re.fullmatch(r'[0-9a-f]{64}', item['sha256']), 'checkpoint file declaration changed')
                wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
            else: directories.append('checkpoint/' + name)
            require(set(item) == fields, 'unexpected checkpoint entry fields')
            if '/' in name:
                parent = name.rsplit('/', 1)[0]
                require(parent in entries and entries[parent]['kind'] == 'directory', 'checkpoint directory parent missing')
    else:
        require(entries is None, 'inspection must not invent a complete checkpoint inventory')
        for name in INSPECTION_ENTRIES: wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    directories.sort(key=lambda name: (name.count('/'), name))
    require(index['directories'] == directories, 'checkpoint directory inventory changed')
    files = index['files']
    require(type(files) is dict and len(files) <= MAX_DATA_FILES and MANDATORY <= set(files) <= set(wanted)
            and index['absent_files'] == sorted(set(wanted) - set(files)), 'missing or foreign collected files')
    if mode == 'checkpoint':
        require({name for name in files if name.startswith('checkpoint/')} ==
                {'checkpoint/' + name for name, item in entries.items() if item['kind'] == 'file'},
                'actual checkpoint entries were filtered or fabricated')
    total = 0
    for name, item in files.items():
        path_name(name)
        require(type(item) is dict and set(item) == {'bytes', 'sha256', 'remote_path'}
                and type(item['bytes']) is int and 0 <= item['bytes'] <= wanted[name][1]
                and re.fullmatch(r'[0-9a-f]{64}', item['sha256']) and item['remote_path'] == wanted[name][0],
                'collected file declaration changed')
        if name.startswith('checkpoint/'):
            require(present, 'absent checkpoint cannot contain files')
            if mode == 'checkpoint':
                require(all(item[key] == entries[name[len('checkpoint/'):]][key] for key in ('bytes', 'sha256')),
                        'checkpoint file differs from complete inventory')
        total += item['bytes']
    require(total == index['total_file_bytes'] and total <= MAX_TOTAL, 'evaluation aggregate collection bound')
    for name, key in (('approval.json', 'approval_sha256'), ('resource-request.json', 'resource_request_sha256'),
            ('train-request.json', 'training_request_sha256'), ('evaluate-request.json', 'evaluation_request_sha256'),
            ('train-ledger.jsonl', 'training_ledger_sha256'), ('evaluate-ledger.jsonl', 'evaluation_ledger_sha256')):
        require(files[name]['sha256'] == binding[key], 'raw control/ledger pin differs from released binding')
    manifest = {key: files['model-manifest.json'][key] for key in ('bytes', 'sha256')}
    head = None if 'checkpoint/HEAD.json' not in files else {key: files['checkpoint/HEAD.json'][key] for key in ('bytes', 'sha256')}
    require(manifest == binding['model_manifest'] == index['model_manifest'] and head == index['checkpoint_head'],
            'collected raw HEAD/candidate pin differs')
    require(index['checkpoint_original_lock_collected'] is ('checkpoint/.lock' in files), 'original lock collection claim differs')
    check_external_pins(mode, head, manifest, expected_head, expected_manifest)


def emit_archive(index, wanted, signatures, stream):
    header = canonical(index) + b'\n'
    require(len(header) <= 1024**2, 'checkpoint collection index cap')
    with tarfile.open(fileobj=stream, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        member = tarfile.TarInfo('collection-index.json'); member.size, member.mode = len(header), 0o600
        archive.addfile(member, io.BytesIO(header))
        for name in index['directories']:
            member = tarfile.TarInfo(name + '/'); member.type, member.mode = tarfile.DIRTYPE, 0o700
            archive.addfile(member)
        for local, item in sorted(index['files'].items()):
            source, before = opened(item['remote_path'], wanted[local][1])
            with source:
                require(signature(before) == signatures[local], 'collected entry changed before streaming')
                member = tarfile.TarInfo(local); member.size, member.mode = item['bytes'], 0o600
                archive.addfile(member, source)
                require(signature(before) == signature(os.fstat(source.fileno())), 'collected entry changed during streaming')
            again, current = opened(item['remote_path'], wanted[local][1]); again.close()
            require(signature(current) == signatures[local], 'collected pathname changed during streaming')


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'linux' and len(sys.argv) == 7
            and not os.environ.get('SLURM_JOB_ID'), 'isolated terminal login collection required')
    mode, job, approval_sha, header_sha, expected_head, expected_manifest = sys.argv[1:]
    require(mode in ('inspect', 'checkpoint') and re.fullmatch(r'[1-9][0-9]{0,19}', job)
            and re.fullmatch(r'[0-9a-f]{64}', approval_sha) and re.fullmatch(r'[0-9a-f]{64}', header_sha),
            'invalid exact evaluation collection identity')
    require((mode == 'inspect' and expected_head == expected_manifest == '-') or
            (mode == 'checkpoint' and (expected_head == 'absent' or re.fullmatch(r'[0-9a-f]{64}', expected_head))
                and re.fullmatch(r'[0-9a-f]{64}', expected_manifest)), 'full collection requires external inspected HEAD/manifest pins')
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE, ADDRESS_SPACE))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('remote evaluation collection wall cap')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    sys.meta_path.insert(0, NoFrameworks())
    binding, status = bound_job(job, approval_sha, header_sha)
    head = optional_pin(CHECKPOINT + '/HEAD.json')
    check_external_pins(mode, head, binding['model_manifest'], expected_head, expected_manifest)
    index, wanted, signatures, snapshot = build_inventory(mode, binding, status, head)
    validate_index(index, mode, job, approval_sha, header_sha, expected_head, expected_manifest)
    emit_archive(index, wanted, signatures, sys.stdout.buffer)
    if mode == 'checkpoint': require(checkpoint_inventory() == snapshot, 'actual checkpoint entries changed through export')
    for local, item in sorted(index['files'].items()):
        actual, _, after = read_file(item['remote_path'], wanted[local][1])
        require(actual == {key: item[key] for key in ('bytes', 'sha256')} and after == signatures[local],
                'collected bytes changed through export')
    for local in index['absent_files']:
        try: unexpected, _ = opened(wanted[local][0], wanted[local][1])
        except FileNotFoundError: continue
        unexpected.close(); raise ValueError('previously absent metadata appeared during export')
    after, _ = bound_job(job, approval_sha, header_sha)
    require(after == binding and optional_pin(CHECKPOINT + '/HEAD.json') == head,
            'source/job/candidate/HEAD changed during collection')
    sys.stdout.buffer.flush()
    require(time.monotonic() - STARTED < WALL, 'remote evaluation collection publication deadline')
    signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
