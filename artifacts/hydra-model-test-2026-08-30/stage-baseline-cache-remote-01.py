"""Copy the exact historical baseline cache into its fresh declared location.

Definitions only until main(plan_raw, expected_sha, stage) is explicitly
called. Only standard-library byte copying and metadata hashing: no model or
native imports, subprocess, scheduler, links, overwrite, removal, or retry.
Read-only preflight is separate from the one fresh staging operation.
"""
import datetime
import hashlib
import json
import os
import re
import resource
import signal
import stat
import sys
import time

SOURCE_ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/search-v2/_deploy/hydra-search-v2'
DESTINATION_ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/_deploy/hydra-search-v2'
LOCAL_REFERENCE_ROOT = '/Users/bnaskrecki/codex/peano/_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2'
PLAN_SHA = '7687216add248abbd4f7faa2701eb5f463521e233c6e6fb24fe53980c4506ffb'
PLAN_BYTES = 118873
DIRECTIVE_SHA = '04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778'
REQUEST_SHA = '49117e3c7d62f9fd50931a84abfcbf3ce2c24d50fff672ae78d7b526c7b5354b'
SOURCE_MANIFEST_SHA = '7cb1a9d35b078989991362a979c3ea0d6abac929fbfcf9ae1e457458a24e513d'
ORIGIN_RECEIPT_SHA = '9f3509835a2dffeabf7590af8347aad9a622342f5131a20e26eaf0faa40ab7d1'
MODEL_MANIFEST_SHA = '172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c'
FILE_COUNT = 725
TOTAL_BYTES = 235986082
PREFIXES = ('origin-source', 'model')
ALLOWED_MODES = (0o600, 0o644, 0o700, 0o755)
LIMITS = {'cpu_seconds': 60, 'wall_seconds': 90, 'address_space_bytes': 320 * 1024**2,
          'file_bytes': 128 * 1024**2, 'files': 1024, 'total_bytes': 256 * 1024**2,
          'output_bytes': 1024**2, 'automatic_retry': False}
HEX = re.compile(r'[0-9a-f]{64}\Z')
FORBIDDEN = frozenset(('.git', '.cache', '.venv', '__pycache__', 'node_modules',
                       'id_rsa', 'id_ed25519', 'credentials.json', 'secrets.json', 'auth.json'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMITS['output_bytes'], 'bounded plan bytes required')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(_value):
        raise ValueError('nonfinite or unexpected floating-point plan value')
    def integer(value):
        require(len(value) <= 32, 'oversized JSON integer')
        return int(value)
    result = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid,
                        parse_float=invalid, parse_int=integer)
    require(type(result) is dict, 'one plan JSON object required')
    return result


def relative(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_.\-/]{1,1024}', name), 'unsafe relative path alphabet')
    parts = name.split('/')
    require(len(parts) <= 32 and all(part not in ('', '.', '..') for part in parts), 'unsafe relative path')
    require(not set(parts).intersection(FORBIDDEN), 'forbidden cache path component')
    return name


def validate_plan(raw, expected_sha):
    require(type(expected_sha) is str and expected_sha == PLAN_SHA
            and type(raw) is bytes and len(raw) == PLAN_BYTES and digest(raw) == expected_sha,
            'the exact approved baseline staging plan is required')
    plan = decode(raw)
    require(plan.get('schema') == 'peano-hydra-baseline-cache-stage-plan-v1'
            and plan.get('source_root') == SOURCE_ROOT and plan.get('destination_root') == DESTINATION_ROOT
            and plan.get('local_reference_root') == LOCAL_REFERENCE_ROOT
            and plan.get('user_authorization_sha256') == DIRECTIVE_SHA
            and plan.get('resource_request_sha256') == REQUEST_SHA
            and plan.get('original_source_manifest_sha256') == SOURCE_MANIFEST_SHA
            and plan.get('original_origin_receipt_sha256') == ORIGIN_RECEIPT_SHA
            and plan.get('original_model_manifest_sha256') == MODEL_MANIFEST_SHA
            and plan.get('file_count') == FILE_COUNT and plan.get('total_bytes') == TOTAL_BYTES
            and plan.get('limits') == LIMITS and plan.get('allowed_actual_source_modes') == list(ALLOWED_MODES)
            and plan.get('preserve_actual_source_modes') is True
            and all(plan.get(key) is False for key in ('gpu_allocation_authorized_by_this_staging_plan',
                'native_or_model_work_authorized', 'overwrite_or_link_creation_authorized')),
            'fixed baseline source/destination, authority, identities or limits changed')
    files = plan.get('files')
    require(type(files) is dict and len(files) == FILE_COUNT <= LIMITS['files'], 'baseline file inventory changed')
    total = 0
    for name, item in files.items():
        relative(name)
        require(name.split('/')[0] in PREFIXES and '/' in name, 'only origin-source/ and model/ may be copied')
        require(type(item) is dict and set(item) == {'bytes', 'sha256'}
                and type(item['bytes']) is int and 0 <= item['bytes'] <= LIMITS['file_bytes']
                and type(item['sha256']) is str and HEX.fullmatch(item['sha256']), 'invalid baseline file descriptor')
        parts = name.split('/')
        require(all('/'.join(parts[:i]) not in files for i in range(1, len(parts))), 'file/directory prefix collision')
        total += item['bytes']
    require(total == TOTAL_BYTES <= LIMITS['total_bytes']
            and files['model/manifest.json']['sha256'] == MODEL_MANIFEST_SHA
            and {name.split('/')[0] for name in files} == set(PREFIXES), 'baseline byte totals or model manifest changed')
    return plan


def directory(path):
    require(type(path) is str and path.startswith('/') and '..' not in path.split('/'), 'absolute safe directory required')
    parts = path.split('/')[1:]
    require(all(parts) and len(parts) <= 64, 'unsafe directory components')
    access = getattr(os, 'O_PATH', os.O_RDONLY) if sys.platform == 'linux' else os.O_RDONLY
    fd = os.open('/', access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(parts, 1):
            child = os.open(part, (os.O_RDONLY if index == len(parts) else access)
                            | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def boundary(deadline):
    require(time.monotonic() < deadline, 'baseline cache operation reached its whole-call wall limit')


class Tree:
    def __init__(self, path):
        self.path, self.fd = path, directory(path)
        info = os.fstat(self.fd)
        self.root_identity = (info.st_dev, info.st_ino)

    def close(self):
        os.close(self.fd)

    def anchored(self):
        fd = directory(self.path)
        try:
            info = os.fstat(fd)
            require((info.st_dev, info.st_ino) == self.root_identity, 'cache root was replaced')
        finally:
            os.close(fd)

    def parent(self, name):
        relative(name)
        fd = os.dup(self.fd)
        try:
            for part in name.split('/')[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            result, fd = fd, -1
            return result
        finally:
            if fd >= 0:
                os.close(fd)

    def open_file(self, name):
        fd = -1
        parent = self.parent(name)
        try:
            fd = os.open(name.split('/')[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and 0 <= info.st_size <= LIMITS['file_bytes']
                    and stat.S_IMODE(info.st_mode) in ALLOWED_MODES, 'unsafe source/target file or mode: ' + name)
            result, fd = fd, -1
            return result, identity(info)
        finally:
            os.close(parent)
            if fd >= 0:
                os.close(fd)

    def fingerprint(self, name, deadline):
        boundary(deadline)
        self.anchored()
        fd, before = self.open_file(name)
        hasher, size = hashlib.sha256(), 0
        try:
            while True:
                boundary(deadline)
                block = os.read(fd, 65536)
                if not block:
                    break
                size += len(block)
                require(size <= LIMITS['file_bytes'], 'cache file grew past its bound')
                hasher.update(block)
            require(identity(os.fstat(fd)) == before and size == before[4], 'cache file changed during hashing')
        finally:
            os.close(fd)
        again, after = self.open_file(name)
        os.close(again)
        require(after == before, 'cache pathname changed during hashing')
        self.anchored()
        return {'bytes': size, 'sha256': hasher.hexdigest()}, before

    def files(self, prefixes, deadline):
        result, stack, entries = set(), [], 0
        try:
            if prefixes is None:
                stack.append(('', os.dup(self.fd)))
            else:
                for prefix in prefixes:
                    relative(prefix)
                    stack.append((prefix + '/', os.open(prefix, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd)))
            while stack:
                boundary(deadline)
                prefix, fd = stack.pop()
                try:
                    for part in os.listdir(fd):
                        name = prefix + part
                        relative(name)
                        entries += 1
                        require(entries <= LIMITS['files'] * 3, 'cache directory entry bound exceeded')
                        info = os.stat(part, dir_fd=fd, follow_symlinks=False)
                        if stat.S_ISDIR(info.st_mode):
                            stack.append((name + '/', os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)))
                        else:
                            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'cache link or special file rejected')
                            result.add(name)
                            require(len(result) <= LIMITS['files'], 'cache file count exceeded')
                finally:
                    os.close(fd)
            self.anchored()
            return result
        finally:
            for _, fd in stack:
                os.close(fd)


def assert_absent(parent, leaf):
    parent.anchored()
    try:
        os.stat(leaf, dir_fd=parent.fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise ValueError('declared baseline cache already exists; no overwrite, retry or adoption')


def create_directories(tree, names, deadline):
    directories = set()
    for name in names:
        parts = name.split('/')
        directories.update('/'.join(parts[:i]) for i in range(1, len(parts)))
    require(len(directories) <= LIMITS['files'] * 2, 'cache directory count exceeded')
    for name in sorted(directories, key=lambda x: (x.count('/'), x)):
        boundary(deadline)
        parent = tree.parent(name)
        try:
            os.mkdir(name.split('/')[-1], 0o700, dir_fd=parent)
        finally:
            os.close(parent)
    tree.anchored()


def copy_file(source, target, name, pin, before, deadline):
    boundary(deadline)
    source.anchored()
    target.anchored()
    source_fd, opened_source = source.open_file(name)
    target_fd = parent = -1
    try:
        require(opened_source == before, 'source changed after preflight: ' + name)
        mode = stat.S_IMODE(opened_source[2])
        parent = target.parent(name)
        target_fd = os.open(name.split('/')[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                            0o600, dir_fd=parent)
        opened_target = os.fstat(target_fd)
        require(stat.S_ISREG(opened_target.st_mode) and opened_target.st_nlink == 1, 'unsafe newly created target')
        remaining, hasher = pin['bytes'], hashlib.sha256()
        while remaining:
            boundary(deadline)
            block = os.read(source_fd, min(65536, remaining))
            require(bool(block), 'truncated source during copy')
            remaining -= len(block)
            hasher.update(block)
            view = memoryview(block)
            while view:
                wrote = os.write(target_fd, view)
                require(wrote > 0, 'short target write')
                view = view[wrote:]
        require(os.read(source_fd, 1) == b'' and hasher.hexdigest() == pin['sha256'], 'source bytes changed during copy')
        require(identity(os.fstat(source_fd)) == opened_source, 'source metadata changed during copy')
        os.fchmod(target_fd, mode)
        os.fsync(target_fd)
        current = os.stat(name.split('/')[-1], dir_fd=parent, follow_symlinks=False)
        require((current.st_dev, current.st_ino) == (opened_target.st_dev, opened_target.st_ino)
                and stat.S_ISREG(current.st_mode) and current.st_nlink == 1
                and current.st_size == pin['bytes'] and stat.S_IMODE(current.st_mode) == mode,
                'copied file identity or exact source mode changed')
    finally:
        os.close(source_fd)
        if target_fd >= 0:
            os.close(target_fd)
        if parent >= 0:
            os.close(parent)
    again, after = source.open_file(name)
    os.close(again)
    require(after == before, 'source pathname changed through copy')
    source.anchored()
    target.anchored()


def perform(plan, stage, progress, deadline):
    """Internal byte-copy implementation; main first requires the exact pinned plan."""
    require(type(stage) is bool, 'stage choice must be Boolean')
    files = plan['files']
    source = Tree(SOURCE_ROOT)
    parent_path, leaf = DESTINATION_ROOT.rsplit('/', 1)
    parent = target = None
    try:
        parent = Tree(parent_path)
        assert_absent(parent, leaf)
        require(source.files(PREFIXES, deadline) == set(files), 'historical baseline source/model inventory differs')
        before, modes = {}, {}
        for name, pin in sorted(files.items()):
            actual, before[name] = source.fingerprint(name, deadline)
            require(actual == pin, 'historical baseline bytes differ from authenticated local reference: ' + name)
            modes[name] = stat.S_IMODE(before[name][2])
        progress.update(source_inventory_sha256=digest(canonical(files)), source_modes=modes,
                        source_modes_sha256=digest(canonical(modes)), original_bytes_checked=True)
        require(source.files(PREFIXES, deadline) == set(files), 'historical inventory changed during preflight')
        assert_absent(parent, leaf)
        if not stage:
            return {'status': 'read-only-preflight-passed', 'destination_created': False,
                    'file_count': len(files), 'total_bytes': sum(item['bytes'] for item in files.values()),
                    'source_mode_policy': 'actual safe remote modes checked; no local mode equivalence inferred'}
        boundary(deadline)
        os.mkdir(leaf, 0o700, dir_fd=parent.fd)
        progress['destination_created'] = True
        created = os.stat(leaf, dir_fd=parent.fd, follow_symlinks=False)
        target = Tree(DESTINATION_ROOT)
        require((created.st_dev, created.st_ino) == target.root_identity, 'fresh declared cache was replaced')
        create_directories(target, files, deadline)
        for name, pin in sorted(files.items()):
            copy_file(source, target, name, pin, before[name], deadline)
            progress['files_copied'] += 1
            progress['bytes_copied'] += pin['bytes']
            require(progress['files_copied'] <= FILE_COUNT and progress['bytes_copied'] <= TOTAL_BYTES,
                    'baseline copy exceeded its exact count/byte reservation')
        require(source.files(PREFIXES, deadline) == set(files) and target.files(None, deadline) == set(files),
                'source or target inventory changed during staging')
        for name, pin in sorted(files.items()):
            observed_source, source_after = source.fingerprint(name, deadline)
            observed_target, target_after = target.fingerprint(name, deadline)
            require(observed_source == observed_target == pin and source_after == before[name]
                    and stat.S_IMODE(target_after[2]) == modes[name], 'final source/target hash, identity or mode differs')
        source.anchored()
        target.anchored()
        parent.anchored()
        os.fsync(target.fd)
        os.fsync(parent.fd)
        boundary(deadline)
        return {'status': 'staged-and-independently-rehashed', 'file_count': len(files),
                'total_bytes': sum(item['bytes'] for item in files.values()),
                'all_destination_hashes_checked': True, 'all_source_hashes_and_identities_rechecked': True,
                'all_actual_source_modes_preserved': True, 'historical_source_unchanged': True,
                'new_cache_is_read_only_input_for_diagnostic': True}
    finally:
        if target is not None:
            target.close()
        if parent is not None:
            parent.close()
        source.close()


def main(plan_raw, expected_sha, stage):
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'linux'
            and sys.version_info >= (3, 9) and not any(name.startswith(('SLURM_', 'SBATCH_')) for name in os.environ),
            'isolated Linux login CPU process outside an allocation is required')
    require(type(stage) is bool, 'explicit Boolean stage choice required')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (LIMITS['address_space_bytes'], LIMITS['address_space_bytes']))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS['file_bytes'], LIMITS['file_bytes']))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    def timed_out(_signum, _frame):
        raise TimeoutError('baseline cache90-second whole-call wall deadline')
    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(90)
    started = time.monotonic()
    result = {'schema': 'peano-hydra-baseline-cache-stage-result-v1', 'mode': 'stage' if stage else 'preflight',
              'source_root': SOURCE_ROOT, 'destination_root': DESTINATION_ROOT, 'started_at_utc': utc(),
              'plan_sha256': expected_sha, 'user_authorization_sha256': DIRECTIVE_SHA,
              'resource_request_sha256': REQUEST_SHA, 'limits': dict(LIMITS),
              'destination_created': False, 'files_copied': 0, 'bytes_copied': 0,
              'gpu_job_submitted': False, 'native_or_model_work_performed': False,
              'overwrite_link_or_deletion_performed': False, 'automatic_retry': False,
              'partial_destination_preserved_on_failure': True}
    code = 2
    try:
        plan = validate_plan(plan_raw, expected_sha)
        result.update(perform(plan, stage, result, started + LIMITS['wall_seconds']))
        code = 0
    except BaseException as error:
        result.update(status='failed-partial-destination-preserved',
                      error=(type(error).__name__ + ': ' + ' '.join(str(error).split()))[:2048])
    finally:
        signal.alarm(0)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result.update(finished_at_utc=utc(), wall_seconds=time.monotonic() - started,
                      cpu_seconds=usage.ru_utime + usage.ru_stime,
                      peak_rss_bytes=int(usage.ru_maxrss * 1024))
        raw = canonical(result)
        require(len(raw) <= LIMITS['output_bytes'], 'baseline cache result exceeds its output bound')
        print(raw.decode('utf-8'), flush=True)
    return code
