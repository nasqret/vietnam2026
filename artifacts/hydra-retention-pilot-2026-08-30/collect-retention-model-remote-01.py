"""Read-only terminal retention-model export; Python3.9, no ML/native work.

Safe file traversal and USTAR streaming follow the retained diagnostic
collectors. The original frozen launch gate authenticates the actual approval,
released one-use training ledger, and COMPLETED/0:0 training job. Inspection
exports metadata only; model collection additionally requires an external raw
manifest SHA before any adapter/tokenizer file is opened.
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
MODEL = 'results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1'
SOURCE_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
PLAN_SHA = 'da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0'
INDEX_SCHEMA = 'peano-hydra-retention-model-collection-index-v1'
MAX_JSON, MAX_TOTAL, MAX_INSPECTION = 4 * 1024**2, 128 * 1024**2, 20 * 1024**2
CPU, WALL, ADDRESS_SPACE = 20, 120, 320 * 1024**2
BOOTSTRAP_SOURCES = {
    'training/peano_hydra/__init__.py': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    'training/peano_hydra/retention_launch.py': 'bed869bec7d2d873885fd90c97e90c1910948ab39a492caa829299f7f599c9c0',
    'training/peano_hydra/search_launch.py': '3d393ceb547c5199297748af647c7c6c51c67bf176011dcd68b257dc6d3f97ca',
}
ARTIFACTS = {
    'adapter': {'adapter/README.md', 'adapter/adapter_config.json', 'adapter/adapter_model.safetensors'},
    'tokenizer': {'tokenizer/added_tokens.json', 'tokenizer/chat_template.jinja', 'tokenizer/merges.txt',
                  'tokenizer/special_tokens_map.json', 'tokenizer/tokenizer.json',
                  'tokenizer/tokenizer_config.json', 'tokenizer/vocab.json'},
}


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


def metadata_files(job):
    return {
        'model/manifest.json': (MODEL + '/manifest.json', MAX_JSON),
        'metadata/train-ledger.jsonl': ('logs/hydra-retention-pilot-v1-train.jsonl', 256 * 1024),
        'metadata/approval.json': (PACKAGE + '/approval.json', MAX_JSON),
        'metadata/resource-request.json': (PACKAGE + '/resource-request.json', MAX_JSON),
        'metadata/train-request.json': (PACKAGE + '/train-request.json', MAX_JSON),
        'metadata/training.out.log': ('logs/' + PROFILE + '-train-' + job + '.out', MAX_JSON),
        'metadata/training.err.log': ('logs/' + PROFILE + '-train-' + job + '.err', MAX_JSON),
    }


def manifest_artifacts(value, job, approval_sha):
    require(value.get('schema') == 'peano-hydra-retention-trained-adapter-v1'
            and value.get('profile') == PROFILE and value.get('run_id') == RUN_ID
            and value.get('model_trained') is True and value.get('training_plan_sha256') == PLAN_SHA
            and value.get('initialization') == {'kind': 'fresh-pinned-base-new-lora', 'continued_from_ancestor_adapter': False}
            and value.get('automatic_retry') is False and value.get('resume') is False,
            'not the completed exact mixed-retention artifact')
    reservation = value.get('reservation', {})
    final = value.get('final_reservation', {})
    for item in (reservation, final):
        require(item.get('stage') == 'train' and item.get('job_id') == job
                and item.get('approval_sha256') == approval_sha and item.get('source_commit') == SOURCE_COMMIT
                and item.get('reservation') == {'seconds': 7200, 'gpus': 1, 'cpus': 8, 'memory_gib': 64},
                'manifest changed its actual reserved training')
    require(value.get('metrics', {}).get('actual_optimizer_steps') == 1469,
            'incomplete optimizer schedule cannot be collected as a completed model')
    files = {}
    for group, names in ARTIFACTS.items():
        record = value[group]
        require(type(record) is dict and set(record) == {'root', 'files', 'sha256'}
                and record['root'] == group and type(record['files']) is dict and set(record['files']) == names
                and sha(canonical(record['files'])) == record['sha256'], 'declared adapter/tokenizer inventory changed')
        for name, expected in record['files'].items():
            path_name(name)
            require(type(expected) is str and re.fullmatch(r'[0-9a-f]{64}', expected), 'artifact raw hash missing')
            files[name] = expected
    return dict(sorted(files.items()))


class NoFrameworks(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        require(fullname.split('.')[0] not in {'torch', 'transformers', 'peft', 'tokenizers', 'accelerate', 'datasets', 'vllm'},
                'collection cannot import a model/tokenizer framework')
        return None


def bound_training(job, approval_sha):
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
    require(bound['source_commit'] == SOURCE_COMMIT, 'approved source commit changed')
    lock = gate._lock(False)
    try:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        states = {stage: gate.load_ledger(stage, bound) for stage in gate.STAGES}
        gate._history(states, bound)
        state = states['train']
        require(state['job_id'] == job and state['phase'] == 'released' and len(state['events']) == 6
                and state['gpu_seconds'] == 7200, 'exact released one-use training ledger required')
        manifest_pin = gate._training_completed(states)
        ledger_pin = read_file(gate.LEDGERS['train'], 256 * 1024)[0]
    finally:
        os.close(lock)
    command = ['sacct', '-n', '-P', '-X', '-j', job,
        '--format=JobIDRaw,JobName%80,State%32,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%256,WorkDir%4096,Account,Partition,User']
    output = gate.safe.run(command)
    rows = [line.split('|') for line in output.splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) in (13, 14), 'unique terminal training accounting required')
    row = rows[0][:13]
    require(len(rows[0]) == 13 or rows[0][13] == '', 'unexpected trailing accounting field')
    require(row[:4] == [job, PROFILE + '-train', 'COMPLETED', '0:0']
            and row[5:8] == ['120', '8', '64G'] and row[9:] == [ROOT, gate.ACCOUNT, gate.PARTITION, 'plgnasqret']
            and row[4].isdigit() and 0 < int(row[4]) <= 7200, 'terminal training state, scope or elapsed time changed')
    binding = {'job_id': job, 'approval_sha256': approval_sha, 'resource_request_sha256': bound['resource_request_sha256'],
        'source_commit': SOURCE_COMMIT, 'source_files_sha256': bound['source_files_sha256'], 'payloads_sha256': bound['payloads_sha256'],
        'training_request_sha256': request['scientific_inputs']['train']['sha256'], 'training_plan_sha256': PLAN_SHA,
        'ledger_sha256': ledger_pin['sha256'], 'ledger_events': 6, 'reserved_gpu_seconds': 7200,
        'manifest': manifest_pin, 'validated_by_frozen_training_completed': True}
    return binding, {'command': command, 'stdout': output, 'top_row': row, 'state': row[2], 'exit_code': row[3],
                     'elapsed_seconds': int(row[4]), 'returncode': 0}


def validate_index(index, mode, job, approval_sha, expected_manifest_sha=None):
    require(index.get('schema') == INDEX_SCHEMA and index.get('mode') == mode, 'wrong model collection index')
    binding = index['binding']
    require(binding['job_id'] == job and binding['approval_sha256'] == approval_sha
            and binding['source_commit'] == SOURCE_COMMIT and binding['training_plan_sha256'] == PLAN_SHA
            and binding['reserved_gpu_seconds'] == 7200 and binding['ledger_events'] == 6
            and binding['validated_by_frozen_training_completed'] is True, 'collection changed exact training identity')
    require(expected_manifest_sha is None or binding['manifest']['sha256'] == expected_manifest_sha,
            'collection changed the externally observed completed manifest')
    accounting, top = index['accounting'], index['accounting']['top_row']
    rows = [line.split('|') for line in accounting['stdout'].splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) in (13, 14)
            and (len(rows[0]) == 13 or rows[0][13] == '') and rows[0][:13] == top
            and accounting['returncode'] == 0 and top[:4] == [job, PROFILE + '-train', 'COMPLETED', '0:0']
            and top[5:8] == ['120', '8', '64G'] and top[9:] == [ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret']
            and top[4].isdigit() and 0 < int(top[4]) <= 7200 and accounting['elapsed_seconds'] == int(top[4])
            and accounting['state'] == 'COMPLETED' and accounting['exit_code'] == '0:0',
            'collection lacks exact successful terminal accounting')
    fixed = metadata_files(job)
    artifact_names = set().union(*ARTIFACTS.values())
    require(set(index['declared_artifact_files']) == artifact_names, 'declared saved artifact set changed')
    wanted = dict(fixed)
    if mode == 'model':
        wanted.update({'model/' + name: (MODEL + '/' + name, MAX_TOTAL) for name in artifact_names})
    files = index['files']
    mandatory = set(fixed) - {'metadata/training.out.log', 'metadata/training.err.log'}
    require(type(files) is dict and mandatory <= set(files) <= set(wanted)
            and index['absent_files'] == sorted(set(wanted) - set(files))
            and all(name.startswith('metadata/training.') for name in index['absent_files']),
            'model collection omits required inputs or adds foreign files')
    if mode == 'model':
        require({'model/' + name for name in artifact_names} <= set(files), 'model artifact collection is incomplete')
    total = 0
    for name, item in files.items():
        path_name(name)
        require(type(item) is dict and set(item) == {'bytes', 'sha256', 'remote_path'}
                and type(item['bytes']) is int and 0 <= item['bytes'] <= wanted[name][1]
                and type(item['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', item['sha256'])
                and item['remote_path'] == wanted[name][0], 'unsafe collected file declaration')
        if name.startswith(('model/adapter/', 'model/tokenizer/')):
            require(item['sha256'] == index['declared_artifact_files'][name[len('model/'):]], 'artifact raw hash changed')
        total += item['bytes']
    require(total == index['total_file_bytes'] and total <= (MAX_TOTAL if mode == 'model' else MAX_INSPECTION),
            'model collection exceeds aggregate bound')
    for name, key in (('metadata/approval.json', 'approval_sha256'), ('metadata/resource-request.json', 'resource_request_sha256'),
                      ('metadata/train-request.json', 'training_request_sha256'), ('metadata/train-ledger.jsonl', 'ledger_sha256')):
        require(files[name]['sha256'] == binding[key], 'collected control no longer joins training')
    require({key: files['model/manifest.json'][key] for key in ('bytes', 'sha256')} == binding['manifest'],
            'manifest file differs from terminal gate identity')
    require(index['model_artifact_files_collected'] is (mode == 'model') and index['read_only'] is True
            and all(index[key] is False for key in ('model_frameworks_imported', 'artifact_semantics_authenticated',
                'proofs_independently_verified', 'scheduler_mutation_performed', 'automatic_retry')),
            'collection inflated its evidence or execution scope')


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'linux' and len(sys.argv) == 5
            and not os.environ.get('SLURM_JOB_ID'), 'isolated read-only login collection required')
    mode, job, approval_sha, expected_manifest_sha = sys.argv[1:]
    require(mode in ('inspect', 'model') and re.fullmatch(r'[1-9][0-9]{0,19}', job)
            and re.fullmatch(r'[0-9a-f]{64}', approval_sha), 'invalid fixed collection inputs')
    require((mode == 'inspect' and expected_manifest_sha == '-') or
            (mode == 'model' and re.fullmatch(r'[0-9a-f]{64}', expected_manifest_sha)),
            'full model collection requires a previously observed external manifest SHA')
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE, ADDRESS_SPACE))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('remote model collection wall deadline')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    sys.meta_path.insert(0, NoFrameworks())
    binding, accounting = bound_training(job, approval_sha)
    manifest_pin, raw_manifest, _ = read_file(MODEL + '/manifest.json', MAX_JSON, True)
    require(manifest_pin == binding['manifest'] and (mode == 'inspect' or manifest_pin['sha256'] == expected_manifest_sha),
            'completed manifest changed before artifact collection')
    artifacts = manifest_artifacts(decode(raw_manifest), job, approval_sha)
    wanted = metadata_files(job)
    if mode == 'model':
        wanted.update({'model/' + name: (MODEL + '/' + name, MAX_TOTAL) for name in artifacts})
    files, signatures, absent, total = {}, {}, [], 0
    for local, (remote, maximum) in sorted(wanted.items()):
        try: identity, _, before = read_file(remote, maximum)
        except FileNotFoundError:
            require(local in ('metadata/training.out.log', 'metadata/training.err.log'), 'required completed artifact missing')
            absent.append(local); continue
        total += identity['bytes']
        require(total <= (MAX_TOTAL if mode == 'model' else MAX_INSPECTION), 'collection aggregate cap')
        if local.startswith(('model/adapter/', 'model/tokenizer/')):
            require(identity['sha256'] == artifacts[local[len('model/'):]], 'saved artifact bytes differ from manifest')
        files[local], signatures[local] = dict(identity, remote_path=remote), before
    index = {'schema': INDEX_SCHEMA, 'mode': mode, 'binding': binding, 'accounting': accounting,
        'observed_at_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'files': files, 'absent_files': sorted(absent), 'total_file_bytes': total, 'declared_artifact_files': artifacts,
        'model_artifact_files_collected': mode == 'model', 'read_only': True, 'model_frameworks_imported': False,
        'artifact_semantics_authenticated': False, 'proofs_independently_verified': False,
        'scheduler_mutation_performed': False, 'automatic_retry': False}
    validate_index(index, mode, job, approval_sha, None if mode == 'inspect' else expected_manifest_sha)
    header = canonical(index) + b'\n'
    require(len(header) <= MAX_JSON, 'collection index cap')
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        member = tarfile.TarInfo('collection-index.json'); member.size = len(header); member.mode = 0o600
        archive.addfile(member, io.BytesIO(header))
        for local, item in sorted(files.items()):
            stream, before = opened(item['remote_path'], wanted[local][1])
            with stream:
                require(signature(before) == signatures[local], 'file changed before streaming')
                member = tarfile.TarInfo(local); member.size = item['bytes']; member.mode = 0o600
                archive.addfile(member, stream)
                require(signature(before) == signature(os.fstat(stream.fileno())), 'file changed during streaming')
            current, now = opened(item['remote_path'], wanted[local][1]); current.close()
            require(signature(now) == signatures[local], 'streamed file was replaced')
    after, _ = bound_training(job, approval_sha)
    require(after == binding, 'approval/released job/completed manifest changed during collection')
    sys.stdout.buffer.flush()
    require(time.monotonic() - STARTED < WALL, 'remote collection publication exceeded wall cap')
    signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
