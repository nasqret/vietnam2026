"""Unexecuted one-use completion of the exact partial source04 file copy.

No original source or existing destination file is opened for writing. This is
a separate repair receipt, never a replacement for the original SSH255 result.
Python3.6-compatible stdlib only; no application/model/native imports.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import select
import signal
import stat
import subprocess
import sys
import time

CAMPAIGN = Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
OLD = CAMPAIGN / 'bundles/combined-source-03'
DEST = CAMPAIGN / 'bundles/combined-source-04'
CHANGED = 'output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py'
OLD_MANIFEST_SHA = 'bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08'
OLD_CONTENT_SHA = '9b73388872811477057ff6f3ddff9e5b54020b12c22059d12519594bea15da62'
NEW_CONTENT_SHA = 'aa001fceb6eaefcf3073287f8cb8a8efacffc245fe524759ad95a0d34571c9dd'
INVENTORY_SHA = 'd95cf025fc969aa0e6f1ec2e810ab9d038b0d025d5f6152f4acb65efab32e2b8'
EXISTING_NAMES_SHA = 'dd254b328eb75325e737ac755288506391c27c9acd747e030af3a1d60f3f95cc'
METADATA = {
 'manifest.json': (253561, '4beeb386a118229b4e3fa9b751d7a4a560853252ab3103cff661a48dc2eb9f0e'),
 'paired-source-pins.json': (126170, 'd32c30a437070986df9777bf97dbb56f362e720d63ba32be16d8b728155ecf9d'),
 'teacher-source-pins.json': (108200, 'e76da7607ea7be7681c30a5583bfb71c998aab7660754e28cb0c4cb61f5b3d7a'),
 'student-source-pins.json': (101298, '8e55a8f20c5aaf8893d5850c008d0a54408cac9600d2827de4b6eeb95f2c887c'),
 'teacher-paired-source-pins.json': (126761, 'd184338a35b8aebde03a5edad16995038717502d4d84924da7f4750e36247ce9'),
}
LIMITS = {'remote_wall_seconds': 120, 'remote_cpu_soft_seconds': 60,
          'remote_cpu_hard_seconds': 75, 'remote_address_space_bytes': 512 * 1024**2,
          'quota_query_wall_seconds': 10, 'quota_output_bytes': 16384,
          'maximum_open_directories': 192, 'request_bytes': 2 * 1024**2,
          'maximum_cached_missing_bytes': 32782277}


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': digest(raw)}


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class Directories:
    """Authenticate each ancestor once; retain directory capabilities, not path guesses."""
    def __init__(self):
        self.fds = {'/': os.open('/', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)}

    def get(self, path):
        path = Path(path)
        require(path.is_absolute() and '..' not in path.parts and '.' not in path.parts,
                'Noncanonical directory path.')
        current = Path('/')
        for part in path.parts[1:]:
            parent = current
            current = current / part
            key = str(current)
            if key not in self.fds:
                require(len(self.fds) < LIMITS['maximum_open_directories'], 'Directory capability bound reached.')
                owned = key == str(CAMPAIGN) or key.startswith(str(CAMPAIGN) + '/')
                access = os.O_RDONLY if owned else os.O_PATH
                fd = os.open(part, access | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fds[str(parent)])
                info = os.fstat(fd)
                if owned:
                    if info.st_uid != 105923:
                        os.close(fd)
                        raise ValueError('Directory owner differs.')
                self.fds[key] = fd
        return self.fds[str(path)]

    def verify_paths(self):
        for key, fd in self.fds.items():
            if key == '/':
                continue
            path = Path(key)
            current = os.stat(path.name, dir_fd=self.fds[str(path.parent)], follow_symlinks=False)
            held = os.fstat(fd)
            require(stat.S_ISDIR(current.st_mode) and (current.st_dev, current.st_ino, current.st_uid)
                    == (held.st_dev, held.st_ino, held.st_uid), 'A held directory was replaced or redirected.')

    def close(self):
        for fd in reversed(list(self.fds.values())):
            os.close(fd)


def regular(info, expected_size):
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 105923 and info.st_nlink == 1
            and info.st_size == expected_size, 'Wrong file type, ownership, link count or size.')


def read_file(dirs, path, expected):
    parent = dirs.get(path.parent)
    fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        regular(before, expected['bytes'])
        raw = stream.read(expected['bytes'] + 1)
        require(stamp(os.fstat(stream.fileno())) == stamp(before), 'File changed during the read.')
    require(stamp(os.stat(path.name, dir_fd=parent, follow_symlinks=False)) == stamp(before)
            and descriptor(raw) == expected, 'File path or exact bytes changed.')
    return raw, stamp(before)


def write_new(dirs, path, raw):
    require(len(raw) <= 128 * 1024**2, 'Exclusive output exceeds file bound.')
    parent = dirs.get(path.parent)
    fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fchmod(stream.fileno(), 0o444)
        regular(os.fstat(stream.fileno()), len(raw))


def directory_names(files):
    result = {''}
    for name in files:
        path = Path(name)
        require(path.parts and not path.is_absolute() and path.as_posix() == name
                and '..' not in path.parts and '.' not in path.parts, 'Invalid whitelisted path.')
        result.update(parent.as_posix() for parent in path.parents if parent.as_posix() != '.')
    require(not (set(files) & result), 'A file aliases a parent directory.')
    return result


def namespace(dirs, root, files, expected_dirs):
    observed, seen_dirs, pending = set(), set(), ['']
    while pending:
        relative = pending.pop()
        seen_dirs.add(relative)
        fd = dirs.get(root / relative)
        for name in os.listdir(fd):
            key = name if not relative else relative + '/' + name
            if key in files:
                observed.add(key)
            else:
                require(key in expected_dirs and key not in seen_dirs and key not in pending,
                        'Unlisted or duplicate source-tree entry.')
                dirs.get(root / key)  # O_DIRECTORY | O_NOFOLLOW, even before any file is read.
                pending.append(key)
    require(seen_dirs == expected_dirs, 'Source directory inventory differs.')
    return observed


def quota_once(began):
    require(time.monotonic() - began < 107, 'No quota child/cleanup reserve remains.')
    argv = ['/usr/bin/lfs', 'quota', '-q', '-u', '105923', str(CAMPAIGN)]
    process, output, started, reason, code, reaped = None, bytearray(), time.monotonic(), None, None, False
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.set_blocking(process.stdout.fileno(), False)
        eof = False
        while not (eof and process.poll() is not None):
            require(time.monotonic() - started < 10, 'Quota query wall ceiling.')
            if not eof and select.select([process.stdout], [], [], 0.05)[0]:
                chunk = os.read(process.stdout.fileno(), min(4096, 16385 - len(output)))
                if chunk:
                    output.extend(chunk)
                    require(len(output) <= 16384, 'Quota query output ceiling.')
                else:
                    eof = True
            elif eof:
                time.sleep(0.02)
    except BaseException as error:
        reason = type(error).__name__ + ': ' + str(error)[:256]
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            try:
                code = process.wait(timeout=3)
                reaped = True
            except subprocess.TimeoutExpired:
                reason = 'Owned quota child did not reap.'
            process.stdout.close()
    require(code == 0 and reaped and reason is None, 'One owned quota query failed: ' + str(reason))
    text = bytes(output).decode('utf-8')
    numbers = text.splitlines()[-1].split()[-8:]
    require(len(numbers) == 8, 'Unexpected quota row.')
    used, ceiling = int(numbers[4].rstrip('*')), int(numbers[6])
    require(0 <= used <= ceiling, 'Invalid inode quota accounting.')
    return {'actual_exit_code': code, 'owned_child_reaped': reaped,
            'elapsed_seconds': time.monotonic() - started, 'stdout_stderr': text,
            'used': used, 'limit': ceiling, 'automatic_retry': False}


def run():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 75))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    began = time.monotonic()
    require(os.getuid() == 105923, 'Wrong remote owner.')
    request_raw = sys.stdin.buffer.read(LIMITS['request_bytes'] + 1)
    require(len(request_raw) <= LIMITS['request_bytes'], 'Repair request is too large.')
    request = json.loads(request_raw)
    require(set(request) == {'schema', 'authority', 'payloads', 'automatic_retry', 'review_sha256'}
            and request['schema'] == 'hydra-source04-partial-copy-repair-request-v2'
            and request['authority'] == 'HYDRA_EXPERIMENT_AUTHORITY.md'
            and request['automatic_retry'] is False and type(request['review_sha256']) is str
            and re.fullmatch('[0-9a-f]{64}', request['review_sha256']), 'Wrong fixed repair request.')
    require(set(request['payloads']) == {'manifest.json', 'paired-source-pins.json', 'source/' + CHANGED},
            'Exactly the original three approved payloads are required.')
    payloads = {name: base64.b64decode(raw, validate=True) for name, raw in request['payloads'].items()}
    require(sum(len(raw) for raw in payloads.values()) == 423394, 'Payload byte count differs.')
    for name in ('manifest.json', 'paired-source-pins.json'):
        require(descriptor(payloads[name]) == {'bytes': METADATA[name][0], 'sha256': METADATA[name][1]},
                'Approved raw metadata changed.')
    manifest = json.loads(payloads['manifest.json'])
    require(digest(canonical(manifest)) == NEW_CONTENT_SHA
            and manifest['schema'] == 'hydra-combined-inference-source-v4'
            and manifest['runtime_destination'] == 'combined-source-04/source'
            and manifest['file_count'] == 1325 and manifest['expanded_bytes'] == 112082345
            and manifest['archive_sha256'] == '63bad7bea869d8ee279124ab6ec00a66c5dd5cc399f4e7d4a68c5bd0189479a4'
            and manifest['automatic_launch'] is False and manifest['automatic_retry'] is False,
            'The final source04 identity changed.')
    files = manifest['files']
    require(len(files) == 1325 and set(manifest['changed_files']) == {CHANGED}
            and descriptor(payloads['source/' + CHANGED]) == files[CHANGED], 'Wrong sole source change.')
    all_dirs = directory_names(files)
    existing = set(sorted(files)[:821])
    missing = set(files) - existing
    require(len(missing) == 504 and CHANGED not in existing
            and max(existing) == 'hydra-playground/native-v7/peano_lab/library/euler_scaled_inverse_candidate.py'
            and sum(files[name]['bytes'] for name in existing) == 79300068
            and sum(files[name]['bytes'] for name in missing) == 32782277, 'Assessed partial prefix differs.')
    existing_dirs = directory_names(existing)
    require(len(existing_dirs) == 33 and len(all_dirs) == 62, 'Partial/final directory scope changed.')
    dirs = Directories()
    try:
        old_manifest_raw, unused = read_file(dirs, OLD / 'manifest.json', {'bytes': 253855, 'sha256': OLD_MANIFEST_SHA})
        original = json.loads(old_manifest_raw)
        require(digest(canonical(original)) == OLD_CONTENT_SHA and original['file_count'] == 1325
                and original['expanded_bytes'] == 112070657 and set(original['files']) == set(files)
                and manifest['parent_manifest_sha256'] == OLD_MANIFEST_SHA
                and original['archive_sha256'] == manifest['parent_archive_sha256'], 'Original source03 binding differs.')
        require({name for name in files if files[name] != original['files'][name]} == {CHANGED},
                'More than the reviewed source change exists.')
        require(set(os.listdir(dirs.get(DEST))) == {'source'}, 'Repair destination already has metadata, an intent or unlisted files.')
        starting_names = namespace(dirs, DEST / 'source', files, existing_dirs)
        require(starting_names == existing and digest(canonical(sorted(starting_names))) == EXISTING_NAMES_SHA,
                'Actual partial namespace differs from the observed inventory.')
        preserved = {}
        for name in sorted(existing):
            path = DEST / 'source' / name
            raw, before = read_file(dirs, path, files[name])
            preserved[name] = before
        require(namespace(dirs, OLD / 'source', original['files'], all_dirs) == set(files), 'Original namespace differs.')
        metadata = {}
        for name, (size, sha) in METADATA.items():
            if name in payloads:
                raw = payloads[name]
            else:
                raw, unused = read_file(dirs, OLD / name, {'bytes': size, 'sha256': sha})
            require(descriptor(raw) == {'bytes': size, 'sha256': sha}, 'A source-map raw descriptor differs.')
            metadata[name] = raw
        for kind, scope_pin in manifest['source_maps'].items():
            raw = metadata[kind + '-source-pins.json']
            scope = json.loads(raw)
            require(descriptor(raw) == {key: scope_pin[key] for key in ('bytes', 'sha256')}
                    and len(scope) == scope_pin['files'] and digest(canonical(scope)) == scope_pin['content_sha256'],
                    'Source-map identity differs.')
            require(all(files[name]['sha256'] == value if kind == 'teacher' else files[name] == value
                        for name, value in scope.items()), 'Source-map entries differ from final file pins.')
        quota = quota_once(began)
        inode_reserve = len(missing) + len(all_dirs - existing_dirs) + 5 + 2 + 256
        require(quota['limit'] - quota['used'] >= inode_reserve, 'Insufficient exact repair inode reserve.')
        cached, original_stamps, cache_bytes = {}, {}, 0
        for name in sorted(files):
            raw, before = read_file(dirs, OLD / 'source' / name, original['files'][name])
            original_stamps[name] = before
            if name in missing:
                data = payloads['source/' + CHANGED] if name == CHANGED else raw
                require(descriptor(data) == files[name], 'A missing-file payload differs.')
                cached[name] = data
                cache_bytes += len(data)
                require(cache_bytes <= LIMITS['maximum_cached_missing_bytes'], 'Missing-byte cache limit.')
        require(cache_bytes == 32782277, 'Incomplete missing-byte cache.')
        dirs.verify_paths()
        # A separately selected one-use repair, not another invocation of the old stager.
        stage_retained = {'exit_code': 255, 'completion_chunk': 'add706', 'partial_inventory_sha256': INVENTORY_SHA}
        prior_repair_retained = {'exit_code': 1, 'completion_chunk': '908edc',
                                'failure_phase': 'initial_parent_manifest_open', 'source_write_phase_reached': False}
        intent = {'schema': 'hydra-source04-partial-copy-repair-intent-v2', 'review_sha256': request['review_sha256'],
                  'request_sha256': digest(request_raw), 'stage_retained': stage_retained,
                  'prior_repair_retained': prior_repair_retained,
                  'existing_files': 821, 'missing_files': 504, 'limits': LIMITS, 'automatic_retry': False}
        write_new(dirs, DEST / 'repair-attempt-02.json', canonical(intent) + b'\n')
        for relative in sorted(all_dirs - existing_dirs, key=lambda value: (value.count('/'), value)):
            path = DEST / 'source' / relative
            os.mkdir(path.name, mode=0o700, dir_fd=dirs.get(path.parent))
            dirs.get(path)
        for name in sorted(missing):
            write_new(dirs, DEST / 'source' / name, cached.pop(name))
        require(not cached, 'Unused missing payload remained.')
        require(namespace(dirs, DEST / 'source', files, all_dirs) == set(files), 'Final source04 namespace differs.')
        verified_bytes = 0
        for name in sorted(files):
            raw, after = read_file(dirs, DEST / 'source' / name, files[name])
            verified_bytes += len(raw)
            if name in existing:
                require(after == preserved[name], 'An existing file was replaced or modified.')
        require(verified_bytes == 112082345, 'Final source04 byte population differs.')
        require(namespace(dirs, OLD / 'source', original['files'], all_dirs) == set(files), 'Original namespace changed.')
        for name in sorted(files):
            raw, after = read_file(dirs, OLD / 'source' / name, original['files'][name])
            require(after == original_stamps[name], 'An original source file changed.')
        require(read_file(dirs, OLD / 'manifest.json', descriptor(old_manifest_raw))[0] == old_manifest_raw,
                'Original manifest changed.')
        for name in set(METADATA) - set(payloads):
            require(read_file(dirs, OLD / name, descriptor(metadata[name]))[0] == metadata[name], 'Original source map changed.')
        dirs.verify_paths()
        require(set(os.listdir(dirs.get(DEST))) == {'source', 'repair-attempt-02.json'}, 'Unlisted repair-root mutation.')
        for name in sorted(metadata):
            write_new(dirs, DEST / name, metadata[name])
            require(read_file(dirs, DEST / name, descriptor(metadata[name]))[0] == metadata[name], 'Written metadata differs.')
        # Complete the original destination-only permission freeze. Existing
        # file stamps and all parent03 directory permissions remain untouched.
        for relative in sorted(all_dirs, key=lambda value: (-value.count('/'), value)):
            fd = dirs.get(DEST / 'source' / relative)
            os.fchmod(fd, 0o555)
            require(stat.S_IMODE(os.fstat(fd).st_mode) == 0o555, 'Source04 directory freeze failed.')
        elapsed = time.monotonic() - began
        require(elapsed < 120, 'Repair wall bound reached before completion.')
        record = {'schema': 'hydra-source04-partial-copy-repair-receipt-v2', 'completed': True,
          'review_sha256': request['review_sha256'], 'request_sha256': digest(request_raw),
          'directory': str(DEST), 'source': str(DEST / 'source'), 'derived_from_source': str(OLD / 'source'),
          'stage_retained': stage_retained, 'prior_repair_retained': prior_repair_retained,
          'original_stage_success_claimed': False,
          'manifest_sha256': METADATA['manifest.json'][1], 'manifest_content_sha256': NEW_CONTENT_SHA,
          'manifest_raw_bytes_preserved': True, 'parent_remote_manifest_sha256': OLD_MANIFEST_SHA,
          'parent_local_manifest_sha256': OLD_MANIFEST_SHA, 'parent_manifest_content_sha256': OLD_CONTENT_SHA,
          'source_maps': manifest['source_maps'], 'provider_sha256': manifest['provider_sha256'],
          'provider_profile': manifest['provider_profile'], 'verified_files': 1325, 'verified_bytes': verified_bytes,
          'existing_files_preserved': 821, 'missing_files_created': 504, 'metadata_files_created': 5,
          'starting_source_names_sha256': EXISTING_NAMES_SHA, 'initial_inventory_is_not_a_content_hash_attestation': True,
          'all_final_source_bytes_verified': True,
          'source_directories_read_only': True, 'source_directories_frozen': 62,
          'intent_files_created': 1, 'repair_receipts_created': 1, 'existing_file_stamps_preserved': True,
          'old_whitelisted_sources_unchanged': True, 'no_overwrites': True, 'no_symlinks': True, 'no_hardlinks': True,
          'non_whitelisted_files_copied': 0, 'hardlinks_created': 0, 'saved_artifact_files_read': 0,
          'uploaded_payload_files': 3, 'uploaded_payload_bytes': 423394, 'wire_payload_bytes': len(request_raw),
          'copied_unchanged_metadata_files': sorted(set(METADATA) - set(payloads)),
          'local_reference_archive_sha256': manifest['archive_sha256'], 'remote_archive_available': False,
          'archive_bytes_uploaded': 0, 'application_executions': 0, 'gpu_allocations': 0,
          'model_calls': 0, 'native_runs': 0, 'scheduler_queries': 0, 'automatic_retry': False,
          'experiment_retry_or_resume': False, 'limits': LIMITS, 'elapsed_seconds': elapsed,
          'maximum_cached_missing_bytes': cache_bytes, 'open_directory_capabilities': len(dirs.fds),
          'quota_query': quota, 'inode_quota_required_with_reserve': inode_reserve}
        receipt = canonical(record) + b'\n'
        write_new(dirs, DEST / 'repair-receipt-02.json', receipt)
        require(read_file(dirs, DEST / 'repair-receipt-02.json', descriptor(receipt))[0] == receipt,
                'Final repair receipt write differs.')
        require(set(os.listdir(dirs.get(DEST))) == {'source', 'repair-attempt-02.json', 'repair-receipt-02.json'} | set(METADATA),
                'Unexpected final repair-root entry.')
        dirs.verify_paths()
        signal.alarm(0)
        print(json.dumps(record, sort_keys=True), flush=True)
        return 0
    finally:
        dirs.close()


if __name__ == '__main__':
    raise SystemExit(run())
