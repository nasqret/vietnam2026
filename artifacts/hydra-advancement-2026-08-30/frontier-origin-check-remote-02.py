#!/usr/bin/env python3
"""Derive exact already-transferred metadata, then one explicit CPU origin check.

Invocation is generic orchestration through stdin, not a source/model upload.
--inventory-only writes nothing. --authenticate requires the independently
saved inventory receipt and consumes one fresh sibling evidence directory.
This separate correction includes the existing matching libffi directory; the
first failed origin-check archive is preserved. The original source, training
package, weights, ledgers and installed runtime are never
modified. There is no scheduler invocation, install, model inference or retry.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import time

STARTED = time.monotonic()
ROOT = Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-training-v1')
OUT = ROOT.parent / 'frontier-origin-check-20260830-02'
PYTHON = '/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3'
LIBRARIES = ('/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib',
             '/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64')
LIBRARY = ':'.join(LIBRARIES)
PACKAGE = '_deploy/hydra-frontier-training-v1'
COMMIT = 'b08a6b1303d73217f6cc23800ae15e50b17db792'
REQUEST_SHA = '02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb'
MANIFEST_SHA = '346f9ac39c7d66ebb2c340922d77fc5dbef8a2e867cb1825dddcea92e616ca3b'
MANIFEST_BYTES = 184587
PREPARATION_SHA = '729b97bf8418cb227d0ef1b1ba350fde5da537e46da4ad55774d8b4ca73517d3'
ADAPTER_SHA = '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'
ADAPTER_RELATIVE = 'results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1/manifest.json'
SCHEMA = 'peano-hydra-frontier-origin-check-control-v2'
EXCLUDED = {'.gitignore', 'LICENSE', 'requirements.txt',
    'slurm/peano_hydra_frontier_train.sbatch', 'slurm/peano_hydra_frontier_evaluate.sbatch',
    'slurm/peano_hydra_frontier_training.sbatch'}
BOOTSTRAP = {
    'training/peano_hydra/__init__.py': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    'training/peano_hydra/origin_bridge.py': '0bdaad5f11031fc889ba9fc92e34944b129a505bba7bdd9dbde51e6ae0129e26',
}


def require(value, message):
    if not value: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def decode(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate JSON field')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _v: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def directory(path):
    path = Path(path).absolute()
    require('..' not in path.parts and len(path.parts) <= 64, 'unsafe control path')
    access = os.O_PATH if sys.platform == 'linux' else os.O_RDONLY
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def read(path, maximum):
    path = Path(path)
    parent = directory(path.parent)
    try: fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally: os.close(parent)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'input must be a bounded regular single-link file')
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
        signature = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(signature(before) == signature(after) and len(raw) == before.st_size, 'input changed while reading')
    return raw


def write_new(path, raw):
    require(path.parent in (OUT, OUT / 'inputs') and len(raw) <= 4 * 1024**2, 'unapproved evidence output')
    parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally: os.close(parent)


def derive():
    require(sys.version_info[:2] == (3, 11) and Path(sys.executable).absolute() == Path(PYTHON),
            'use only the actually probed installed EL8 Python3.11.5')
    require(os.environ.get('LD_LIBRARY_PATH') == LIBRARY and not os.environ.get('SLURM_JOB_ID'),
            'exact two reviewed CPU library paths and no allocation required')
    require(not any(k.startswith(('SBATCH_', 'DYLD_')) or k in ('LD_PRELOAD', 'LD_AUDIT', 'BASH_ENV', 'ENV')
                    for k in os.environ), 'unreviewed loader/scheduler controls are forbidden')
    require(not os.path.lexists(ROOT / 'training/__init__.py'), 'unexpected namespace package initializer')
    for name, expected in BOOTSTRAP.items():
        require(hashlib.sha256(read(ROOT / name, 128 * 1024)).hexdigest() == expected,
                'uploaded bootstrap source changed')
    sys.dont_write_bytecode = True
    sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(ROOT), str(ROOT / 'peano-lab/py')]
    from training.peano_hydra import origin_bridge as bridge
    request_raw = read(ROOT / PACKAGE / 'resource-request.json', 4 * 1024**2)
    require(hashlib.sha256(request_raw).hexdigest() == REQUEST_SHA, 'original approved request bytes changed')
    request = decode(request_raw)
    require(request['source_commit'] == COMMIT and request['run_id'] == 'frontier-training-v1',
            'original frozen request/commit changed')
    expected = request['source_files']
    require(type(expected) is dict and len(expected) == 851, 'original source inventory changed')
    selected = {name for name in expected if any(name.startswith(p + '/') for p in bridge.SOURCE_SCOPES)}
    selected.update(bridge._epoch_paths('v28'))
    require(len(selected) == 845 and set(expected) - selected == EXCLUDED and selected <= set(expected),
            'source scope projection changed')
    with bridge._Tree(ROOT) as tree:
        identities = {}
        for name in sorted(selected):
            item, _ = tree.fingerprint(name, maximum=bridge.MAX_SOURCE_FILE_BYTES)
            require({k: item[k] for k in ('bytes', 'sha256')} == expected[name], 'approved source bytes changed: ' + name)
            identities[name] = item
        manifest = {'schema': bridge.SOURCE_SCHEMA, 'git_commit': COMMIT, 'scopes': list(bridge.SOURCE_SCOPES),
                    'epoch_version': 'v28', 'files': identities, 'files_sha256': bridge._digest(identities),
                    'coverage': bridge.SOURCE_COVERAGE}
        bridge._check_sources(tree, manifest)
        raw = bridge._canonical(manifest) + b'\n'
        require(len(raw) == MANIFEST_BYTES and hashlib.sha256(raw).hexdigest() == MANIFEST_SHA,
                'derived source metadata differs from the externally anchored real-Git manifest; no fallback')
        tree.assert_unchanged()
    require(read(ROOT / PACKAGE / 'resource-request.json', 4 * 1024**2) == request_raw, 'original request changed')
    require(hashlib.sha256(read(ROOT / ADAPTER_RELATIVE, 4 * 1024**2)).hexdigest() == ADAPTER_SHA,
            'completed final adapter metadata changed')
    identity = {'schema': bridge.REQUEST_SCHEMA, 'source_manifest_sha256': MANIFEST_SHA,
        'source_commit': COMMIT, 'preparation_relative_path': PACKAGE + '/admitted/preparation',
        'preparation_manifest_sha256': PREPARATION_SHA, 'adapter_manifest_sha256': ADAPTER_SHA,
        'authority_profile': bridge.AUTHORITY_PROFILE}
    locations = {'source_root': str(ROOT), 'source_manifest': str(OUT / 'inputs/source-manifest.json'),
                 'adapter_manifest': str(ROOT / ADAPTER_RELATIVE)}
    return bridge, raw, identity, locations


def proof_of_inventory(raw, expected_sha):
    require(len(raw) <= 32768 and re.fullmatch('[0-9a-f]{64}', expected_sha or '')
            and hashlib.sha256(raw).hexdigest() == expected_sha, 'external inventory receipt raw pin differs')
    value = decode(raw)
    require(value['schema'] == SCHEMA and value['status'] == 'inventory-only-passed'
            and value['source_root'] == str(ROOT) and value['fresh_output'] == str(OUT)
            and value['source_manifest'] == {'bytes': MANIFEST_BYTES, 'sha256': MANIFEST_SHA, 'file_count': 845}
            and value['source_commit'] == COMMIT and value['files_written'] is False
            and value['model_weights_read'] is False and value['original_validator_executed'] is False,
            'native check requires the actual separately retained inventory-only result')


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--inventory-only', action='store_true')
    mode.add_argument('--authenticate', action='store_true')
    parser.add_argument('--inventory-receipt-base64')
    parser.add_argument('--expected-inventory-sha256')
    args = parser.parse_args()
    require((args.inventory_receipt_base64 is not None) == args.authenticate
            and (args.expected_inventory_sha256 is not None) == args.authenticate,
            'only explicit native authentication accepts its saved inventory receipt')
    # Proof-worker limits themselves are unchanged. Parent metadata uses at
    # most20CPU seconds; its hard CPU ceiling permits the child to establish
    # the original120-second limit after exec. The supervisor's210-second
    # total wall bound allows30seconds of metadata around the180-second child.
    resource.setrlimit(resource.RLIMIT_CPU, (20, 121))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0) if args.inventory_only else (4 * 1024**2, 4 * 1024**2))
    def budget(_signum, _frame): raise TimeoutError('bounded CPU origin supervisor limit reached')
    signal.signal(signal.SIGALRM, budget)
    signal.signal(signal.SIGXCPU, budget)
    signal.alarm(30 if args.inventory_only else 210)
    created = False
    try:
        require(not os.path.lexists(OUT), 'one-use origin-check directory already exists; no retry or adoption')
        if args.authenticate:
            proof_of_inventory(base64.b64decode(args.inventory_receipt_base64, validate=True), args.expected_inventory_sha256)
        bridge, raw, identity, locations = derive()
        self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        require(self_rss <= 512 * 1024**2, 'metadata supervisor RSS exceeds512MiB')
        record = {'schema': SCHEMA, 'source_root': str(ROOT), 'fresh_output': str(OUT), 'source_commit': COMMIT,
            'source_manifest': {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'file_count': 845},
            'origin_identity': identity, 'locations': locations, 'runtime_library_paths': list(LIBRARIES),
            'native_worker_limits': bridge.ORIGIN_LIMITS.to_dict(), 'resource_request_sha256': REQUEST_SHA,
            'metadata_supervisor_limits': {'cpu_seconds': 20, 'wall_seconds': 30 if args.inventory_only else 210,
                'checked_peak_rss_bytes': 512 * 1024**2, 'single_file_bytes': 0 if args.inventory_only else 4 * 1024**2},
            'files_written': False, 'model_weights_read': False, 'original_validator_executed': False,
            'model_inference_performed': False, 'allocation_performed': False, 'automatic_retry': False,
            'metadata_supervisor_peak_rss_bytes': self_rss, 'wall_seconds': time.monotonic() - STARTED}
        if args.inventory_only:
            record['status'] = 'inventory-only-passed'
            print(canonical(record).decode(), flush=True)
            return 0
        parent = directory(OUT.parent)
        try:
            os.mkdir(OUT.name, 0o700, dir_fd=parent)
            created = True
            os.fsync(parent)
        finally: os.close(parent)
        parent = directory(OUT)
        try:
            os.mkdir('inputs', 0o700, dir_fd=parent)
            os.fsync(parent)
        finally: os.close(parent)
        write_new(OUT / 'inputs/source-manifest.json', raw)
        opening = dict(record, status='native-origin-check-reserved', files_written=True,
                       inventory_receipt_sha256=args.expected_inventory_sha256)
        write_new(OUT / 'reservation.json', canonical(opening) + b'\n')
        origin = bridge.authenticate_origin(bridge._request(identity, locations), python=Path(PYTHON),
                                             runtime_library_paths=LIBRARIES)
        require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules), 'CPU parent imported model code')
        self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        require(self_rss <= 512 * 1024**2, 'metadata supervisor RSS exceeds512MiB')
        write_new(OUT / 'origin-receipt.json', origin.receipt_bytes)
        record.update(status='original-origin-authenticated', files_written=True, model_weights_read=True,
                      original_validator_executed=True, inventory_receipt_sha256=args.expected_inventory_sha256,
                      origin_receipt_sha256=origin.receipt_sha256,
                      metadata_supervisor_peak_rss_bytes=self_rss,
                      wall_seconds=time.monotonic() - STARTED,
                      metadata_supervisor_cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime
                        + resource.getrusage(resource.RUSAGE_SELF).ru_stime)
        write_new(OUT / 'result.json', canonical(record) + b'\n')
        # Exact original receipt is returned for bounded local capture. No
        # model bytes leave the server; receipt re-use retains its raw anchor.
        print(canonical(dict(record, origin_receipt_base64=base64.b64encode(origin.receipt_bytes).decode())).decode(), flush=True)
        return 0
    except BaseException as error:
        record = {'schema': SCHEMA, 'status': 'failed-no-retry', 'source_root': str(ROOT), 'fresh_output': str(OUT),
            'error_type': type(error).__name__, 'error': ' '.join(str(error).split())[:2048],
            'fresh_archive_created': created, 'automatic_retry': False, 'allocation_performed': False,
            'model_inference_performed': False, 'wall_seconds': time.monotonic() - STARTED}
        observation = getattr(error, 'observation', None)
        if observation is not None: record['original_validator_failure'] = observation
        if created:
            try: write_new(OUT / 'failure.json', canonical(record) + b'\n')
            except (OSError, ValueError): pass
        print(canonical(record).decode(), flush=True)
        return 2
    finally: signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
