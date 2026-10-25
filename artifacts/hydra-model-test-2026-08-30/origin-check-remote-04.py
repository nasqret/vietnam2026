#!/usr/bin/env python3
"""Derive exact already-transferred metadata, then one explicit CPU origin check.

Invocation is generic orchestration through stdin, not a source/model upload.
--inventory-only writes nothing. --authenticate requires the independently
saved inventory receipt and consumes one fresh sibling evidence directory.
This fresh invocation uses the unchanged bridge from an explicit execution
root outside the preserved source tree, as supported by its separate bridge
support contract. Exactly four already-uploaded, raw-pinned bootstrap files are
copied into the fresh sibling archive. No loader exemption, changed __file__,
checker patch, source relocation, or additional validation subprocess is used.
Earlier failures and the complete diagnostic history remain preserved. All
worker/supervisor limits and TimeoutError signal handling are unchanged. The
original source, training package, weights, ledgers and runtime are never
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
OUT = ROOT.parent / 'frontier-origin-check-20260830-04'
SUPPORT_ROOT = OUT / 'bridge-execution'
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
SCHEMA = 'peano-hydra-frontier-origin-check-control-v4'
EXCLUDED = {'.gitignore', 'LICENSE', 'requirements.txt',
    'slurm/peano_hydra_frontier_train.sbatch', 'slurm/peano_hydra_frontier_evaluate.sbatch',
    'slurm/peano_hydra_frontier_training.sbatch'}
BOOTSTRAP = {
    'training/peano_hydra/__init__.py': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    'training/peano_hydra/origin_bridge.py': '0bdaad5f11031fc889ba9fc92e34944b129a505bba7bdd9dbde51e6ae0129e26',
}
SUPPORT_SCHEMA = 'peano-hydra-origin-external-bridge-bootstrap-v1'
SUPPORT_IDENTITIES = {
    'training/peano_hydra/__init__.py': {
        'bytes': 1325,
        'sha256': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    },
    'training/peano_hydra/origin_bridge.py': {
        'bytes': 57822,
        'sha256': '0bdaad5f11031fc889ba9fc92e34944b129a505bba7bdd9dbde51e6ae0129e26',
    },
    'training/peano_hydra/review_runtime.py': {
        'bytes': 26924,
        'sha256': '37a7ae0dcbd27cb244d7239084d89e3efaa09b755e9be47f6698cb3638147962',
    },
    'scripts/hydra_bounded_exec.py': {
        'bytes': 1387,
        'sha256': 'e54b1f8bd807cb294b121f6c0aa0be789d3a9a43473c1c26f8735d3d4e97ceb2',
    },
}
MAX_SUPPORT_FILE_BYTES = 64 * 1024
MAX_SUPPORT_TOTAL_BYTES = 128 * 1024
SUPPORT_TOTAL_BYTES = 87458
SUPPORT_DIRECTORIES = {
    '': frozenset({'training', 'scripts'}),
    'training': frozenset({'peano_hydra'}),
    'training/peano_hydra': frozenset({'__init__.py', 'origin_bridge.py', 'review_runtime.py'}),
    'scripts': frozenset({'hydra_bounded_exec.py'}),
}

_DIAGNOSTIC_PHASES = frozenset({
    'configured', 'inventory_requested', 'inventory_verified', 'inventory_derived',
    'inventory_complete', 'archive_creation', 'support_staging', 'support_staged', 'native_reserved',
    'authenticating_original', 'original_authenticated', 'result_record', 'failed',
})
_CURRENT_PHASE = 'startup'
_PHASE_USAGE = []
_PHASE_USAGE_TRUNCATED = False
_LAST_RESOURCE_SIGNAL = None
_RESOURCE_SIGNAL_COUNT = 0
_MAX_PHASE_RECORDS = 12
_MAX_EXCEPTION_RECORDS = 8
_MAX_TRACEBACK_FRAMES = 12


def usage_snapshot():
    """Cumulative self/reaped-child usage; never aggregate live-group usage."""
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    rss_multiplier = 1 if sys.platform == 'darwin' else 1024

    def row(value):
        return {
            'user_cpu_seconds': value.ru_utime,
            'system_cpu_seconds': value.ru_stime,
            'cpu_seconds': value.ru_utime + value.ru_stime,
            'reported_maxrss_bytes': int(value.ru_maxrss * rss_multiplier),
        }

    return {'wall_seconds': time.monotonic() - STARTED,
            'self': row(own), 'reaped_children': row(children)}


def note_phase(name):
    global _CURRENT_PHASE, _PHASE_USAGE_TRUNCATED
    require(name in _DIAGNOSTIC_PHASES, 'unknown diagnostic phase')
    _CURRENT_PHASE = name
    if len(_PHASE_USAGE) < _MAX_PHASE_RECORDS:
        _PHASE_USAGE.append(dict(usage_snapshot(), phase=name))
    else:
        _PHASE_USAGE_TRUNCATED = True


def budget(signum, _frame):
    """Retain the prior exception/control flow, but remember its true source."""
    global _LAST_RESOURCE_SIGNAL, _RESOURCE_SIGNAL_COUNT
    _RESOURCE_SIGNAL_COUNT += 1
    _LAST_RESOURCE_SIGNAL = {
        'number': int(signum),
        'name': 'SIGXCPU' if signum == signal.SIGXCPU else (
            'SIGALRM' if signum == signal.SIGALRM else 'unexpected'),
        'phase': _CURRENT_PHASE,
        'usage': usage_snapshot(),
    }
    raise TimeoutError('bounded CPU origin supervisor limit reached')


def exception_chain(error):
    """No frame locals, sampled process rows, environment or raw ps output."""
    rows, seen = [], set()
    relation = 'raised'
    while error is not None and len(rows) < _MAX_EXCEPTION_RECORDS and id(error) not in seen:
        seen.add(id(error))
        frames, tb = [], error.__traceback__
        while tb is not None and len(frames) < _MAX_TRACEBACK_FRAMES:
            code = tb.tb_frame.f_code
            frames.append({'file': code.co_filename[-512:], 'function': code.co_name[:96],
                           'line': int(tb.tb_lineno)})
            tb = tb.tb_next
        rows.append({
            'relation': relation, 'error_type': type(error).__name__[:128],
            'error': ' '.join(str(error).split())[:2048],
            'frames': frames, 'frames_truncated': tb is not None,
            'context_suppressed': bool(error.__suppress_context__),
        })
        if error.__cause__ is not None:
            error, relation = error.__cause__, 'cause'
        else:
            error, relation = error.__context__, 'context'
    return {'records': rows, 'truncated_or_cycle': error is not None}


def diagnostics(error=None, failed_phase=None):
    record = {
        'schema': 'peano-hydra-origin-supervisor-diagnostics-v1',
        'current_phase': _CURRENT_PHASE, 'failed_phase': failed_phase,
        'phase_usage': list(_PHASE_USAGE), 'phase_usage_truncated': _PHASE_USAGE_TRUNCATED,
        'resource_signals_seen': _RESOURCE_SIGNAL_COUNT,
        'last_resource_signal': _LAST_RESOURCE_SIGNAL,
        'usage_semantics': (
            'Cumulative RUSAGE_SELF and RUSAGE_CHILDREN from this interpreter. '
            'Reaped children can include ps and the original validator after cleanup; '
            'their maxrss is not aggregate group RSS. Wall starts after initial imports. '
            'These diagnostic snapshots do not replace the unchanged worker receipt.'
        ),
        'bounds': {'phase_records': _MAX_PHASE_RECORDS,
                   'exception_records': _MAX_EXCEPTION_RECORDS,
                   'frames_per_exception': _MAX_TRACEBACK_FRAMES,
                   'error_characters_per_exception': 2048,
                   'file_characters_per_frame': 512,
                   'function_characters_per_frame': 96},
    }
    if error is not None:
        record['exception_chain'] = exception_chain(error)
    return record


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
    support_name = path.relative_to(SUPPORT_ROOT).as_posix() if path.is_relative_to(SUPPORT_ROOT) else None
    if support_name is not None:
        require(support_name in SUPPORT_IDENTITIES and len(raw) <= MAX_SUPPORT_FILE_BYTES
                and {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} == SUPPORT_IDENTITIES[support_name],
                'support output is not one of the four exact reviewed source files')
    else:
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


def support_contract():
    require(not SUPPORT_ROOT.is_relative_to(ROOT) and not ROOT.is_relative_to(SUPPORT_ROOT),
            'bridge execution and preserved source roots must be disjoint')
    return {
        'schema': SUPPORT_SCHEMA, 'source_root': str(ROOT), 'execution_root': str(SUPPORT_ROOT),
        'files': SUPPORT_IDENTITIES, 'file_count': 4, 'total_bytes': SUPPORT_TOTAL_BYTES,
        'max_file_bytes': MAX_SUPPORT_FILE_BYTES, 'max_total_bytes': MAX_SUPPORT_TOTAL_BYTES,
        'outside_preserved_source': True, 'source_bytes_modified': False,
        'loader_exemptions': False, 'additional_validation_subprocess': False,
    }


def support_payloads(root):
    payloads = {}
    total = 0
    for name, expected in SUPPORT_IDENTITIES.items():
        raw = read(root / name, MAX_SUPPORT_FILE_BYTES)
        require({'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} == expected,
                'exact bridge bootstrap bytes changed: ' + name)
        payloads[name] = raw
        total += len(raw)
        require(total <= MAX_SUPPORT_TOTAL_BYTES, 'bridge bootstrap exceeds aggregate byte cap')
    require(total == SUPPORT_TOTAL_BYTES and len(payloads) == 4, 'bridge bootstrap inventory changed')
    return payloads


def check_support_root(root):
    count = 0
    for relative, expected in SUPPORT_DIRECTORIES.items():
        parent = directory(root / relative)
        try:
            found = set()
            with os.scandir(parent) as stream:
                for entry in stream:
                    count += 1
                    require(count <= 8 and entry.name in expected, 'extra bridge bootstrap directory entry')
                    info = entry.stat(follow_symlinks=False)
                    name = relative + '/' + entry.name if relative else entry.name
                    require(not stat.S_ISLNK(info.st_mode), 'bridge bootstrap acquired a symlink')
                    require(stat.S_ISDIR(info.st_mode) if name in SUPPORT_DIRECTORIES else
                            stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                            'bridge bootstrap entry changed kind')
                    found.add(entry.name)
            require(found == expected, 'bridge bootstrap directory inventory changed')
        finally:
            os.close(parent)
    require(count == 7, 'bridge bootstrap entry count changed')
    return support_payloads(root)


def prepare_support_root(payloads):
    require(set(payloads) == set(SUPPORT_IDENTITIES), 'support staging inventory changed')
    for path in (OUT / 'inputs', SUPPORT_ROOT, SUPPORT_ROOT / 'training',
                 SUPPORT_ROOT / 'training/peano_hydra', SUPPORT_ROOT / 'scripts'):
        parent = directory(path.parent)
        try:
            os.mkdir(path.name, 0o700, dir_fd=parent)
            os.fsync(parent)
        finally:
            os.close(parent)
    for name in SUPPORT_IDENTITIES:
        write_new(SUPPORT_ROOT / name, payloads[name])
    require(check_support_root(SUPPORT_ROOT) == payloads, 'staged support differs from original bytes')


def checked_parent_bridge(execution_root):
    import importlib.machinery
    require(execution_root in (ROOT, SUPPORT_ROOT), 'unreviewed parent import root')
    require(not any(name == first or name.startswith(first + '.')
                    for name in sys.modules for first in ('training', 'peano_lab', 'scripts')),
            'parent already imported project modules before its checked bootstrap')
    support_payloads(execution_root)
    if execution_root == SUPPORT_ROOT:
        check_support_root(execution_root)
    require(not os.path.lexists(execution_root / 'training/__init__.py')
            and not os.path.lexists(execution_root / 'training.py'),
            'unexpected parent training namespace initializer')
    sys.dont_write_bytecode = True
    sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(execution_root), str(ROOT / 'peano-lab/py')]
    expected_namespace = [str(execution_root / 'training')]
    namespace_spec = importlib.machinery.PathFinder.find_spec('training', sys.path)
    require(namespace_spec is not None and namespace_spec.loader is None
            and namespace_spec.origin is None
            and list(namespace_spec.submodule_search_locations or ()) == expected_namespace,
            'parent training namespace resolves outside the exact execution root')
    modules = {
        'training.peano_hydra': 'training/peano_hydra/__init__.py',
        'training.peano_hydra.origin_bridge': 'training/peano_hydra/origin_bridge.py',
        'training.peano_hydra.review_runtime': 'training/peano_hydra/review_runtime.py',
    }
    for name, relative in modules.items():
        parent = execution_root / ('training' if name == 'training.peano_hydra' else 'training/peano_hydra')
        spec = importlib.machinery.PathFinder.find_spec(name, [str(parent)])
        require(spec is not None and isinstance(spec.loader, importlib.machinery.SourceFileLoader)
                and spec.origin == str(execution_root / relative),
                'parent module resolution differs from exact pinned bootstrap: ' + name)
    from training.peano_hydra import origin_bridge as bridge
    from training.peano_hydra import review_runtime
    namespace = sys.modules['training']
    require(getattr(namespace, '__file__', None) is None
            and list(getattr(namespace, '__path__', ())) == expected_namespace,
            'loaded parent namespace escaped its checked root')
    for name, relative in modules.items():
        module = sys.modules.get(name)
        require(module is not None and getattr(module, '__file__', None) == str(execution_root / relative)
                and getattr(getattr(module, '__spec__', None), 'origin', None) == str(execution_root / relative),
                'loaded parent module escaped exact bootstrap: ' + name)
    require({name for name in sys.modules if name == 'training' or name.startswith('training.')}
            == {'training', *modules}, 'unexpected parent project submodule')
    require(not any(name == first or name.startswith(first + '.')
                    for name in sys.modules for first in ('peano_lab', 'scripts', 'torch', 'transformers', 'peft', 'tokenizers')),
            'bootstrap imported native project or model code')
    require(bridge.ROOT == execution_root and review_runtime.ROOT == execution_root
            and review_runtime.GUARD == execution_root / 'scripts/hydra_bounded_exec.py',
            'bridge or worker guard escaped the checked execution root')
    support_payloads(execution_root)
    if execution_root == SUPPORT_ROOT:
        check_support_root(execution_root)
    return bridge


def check_invocation_runtime():
    require(sys.version_info[:2] == (3, 11) and Path(sys.executable).absolute() == Path(PYTHON),
            'use only the actually probed installed EL8 Python3.11.5')
    require(os.environ.get('LD_LIBRARY_PATH') == LIBRARY and not os.environ.get('SLURM_JOB_ID'),
            'exact two reviewed CPU library paths and no allocation required')
    require(not any(k.startswith(('SBATCH_', 'DYLD_')) or k in ('LD_PRELOAD', 'LD_AUDIT', 'BASH_ENV', 'ENV')
                    for k in os.environ), 'unreviewed loader/scheduler controls are forbidden')


def derive(execution_root):
    check_invocation_runtime()
    require(not os.path.lexists(ROOT / 'training/__init__.py'), 'unexpected namespace package initializer')
    for name, expected in BOOTSTRAP.items():
        require(hashlib.sha256(read(ROOT / name, 128 * 1024)).hexdigest() == expected,
                'uploaded bootstrap source changed')
    bridge = checked_parent_bridge(execution_root)
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
            and value['model_weights_read'] is False and value['original_validator_executed'] is False
            and value['bridge_support'] == support_contract()
            and value['bridge_parent_import_root'] == str(ROOT)
            and value['bridge_support_copied'] is False,
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
    signal.signal(signal.SIGALRM, budget)
    signal.signal(signal.SIGXCPU, budget)
    signal.alarm(30 if args.inventory_only else 210)
    created = False
    try:
        note_phase('configured')
        require(not os.path.lexists(OUT), 'one-use origin-check directory already exists; no retry or adoption')
        if args.authenticate:
            proof_of_inventory(base64.b64decode(args.inventory_receipt_base64, validate=True), args.expected_inventory_sha256)
            note_phase('inventory_verified')
        else:
            note_phase('inventory_requested')
        check_invocation_runtime()
        payloads = support_payloads(ROOT)
        if args.authenticate:
            note_phase('archive_creation')
            parent = directory(OUT.parent)
            try:
                os.mkdir(OUT.name, 0o700, dir_fd=parent)
                created = True
                os.fsync(parent)
            finally:
                os.close(parent)
            note_phase('support_staging')
            prepare_support_root(payloads)
            note_phase('support_staged')
        execution_root = SUPPORT_ROOT if args.authenticate else ROOT
        bridge, raw, identity, locations = derive(execution_root)
        note_phase('inventory_derived')
        self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        require(self_rss <= 512 * 1024**2, 'metadata supervisor RSS exceeds512MiB')
        record = {'schema': SCHEMA, 'source_root': str(ROOT), 'fresh_output': str(OUT), 'source_commit': COMMIT,
            'source_manifest': {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'file_count': 845},
            'origin_identity': identity, 'locations': locations, 'runtime_library_paths': list(LIBRARIES),
            'native_worker_limits': bridge.ORIGIN_LIMITS.to_dict(), 'resource_request_sha256': REQUEST_SHA,
            'metadata_supervisor_limits': {'cpu_seconds': 20, 'wall_seconds': 30 if args.inventory_only else 210,
                'checked_peak_rss_bytes': 512 * 1024**2, 'single_file_bytes': 0 if args.inventory_only else 4 * 1024**2},
            'files_written': created, 'model_weights_read': False, 'original_validator_executed': False,
            'bridge_support': support_contract(), 'bridge_parent_import_root': str(execution_root),
            'bridge_support_copied': created,
            'model_inference_performed': False, 'allocation_performed': False, 'automatic_retry': False,
            'metadata_supervisor_peak_rss_bytes': self_rss, 'wall_seconds': time.monotonic() - STARTED,
            'supervisor_diagnostics': diagnostics()}
        if args.inventory_only:
            note_phase('inventory_complete')
            record['supervisor_diagnostics'] = diagnostics()
            record['status'] = 'inventory-only-passed'
            print(canonical(record).decode(), flush=True)
            return 0
        require(created and execution_root == SUPPORT_ROOT, 'authentication lost its separate checked support root')
        require(check_support_root(SUPPORT_ROOT) == payloads, 'support changed before native reservation')
        write_new(OUT / 'inputs/source-manifest.json', raw)
        note_phase('native_reserved')
        opening = dict(record, status='native-origin-check-reserved', files_written=True,
                       inventory_receipt_sha256=args.expected_inventory_sha256,
                       supervisor_diagnostics=diagnostics())
        write_new(OUT / 'reservation.json', canonical(opening) + b'\n')
        note_phase('authenticating_original')
        origin = bridge.authenticate_origin(bridge._request(identity, locations), python=Path(PYTHON),
                                             runtime_library_paths=LIBRARIES)
        note_phase('original_authenticated')
        require(check_support_root(SUPPORT_ROOT) == payloads, 'support changed through native validation')
        require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules), 'CPU parent imported model code')
        self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        require(self_rss <= 512 * 1024**2, 'metadata supervisor RSS exceeds512MiB')
        write_new(OUT / 'origin-receipt.json', origin.receipt_bytes)
        note_phase('result_record')
        record.update(status='original-origin-authenticated', files_written=True, model_weights_read=True,
                      original_validator_executed=True, inventory_receipt_sha256=args.expected_inventory_sha256,
                      origin_receipt_sha256=origin.receipt_sha256,
                      metadata_supervisor_peak_rss_bytes=self_rss,
                      wall_seconds=time.monotonic() - STARTED,
                      metadata_supervisor_cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime
                        + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                      supervisor_diagnostics=diagnostics())
        write_new(OUT / 'result.json', canonical(record) + b'\n')
        # Exact original receipt is returned for bounded local capture. No
        # model bytes leave the server; receipt re-use retains its raw anchor.
        print(canonical(dict(record, origin_receipt_base64=base64.b64encode(origin.receipt_bytes).decode())).decode(), flush=True)
        return 0
    except BaseException as error:
        failed_phase = _CURRENT_PHASE
        note_phase('failed')
        record = {'schema': SCHEMA, 'status': 'failed-no-retry', 'source_root': str(ROOT), 'fresh_output': str(OUT),
            'error_type': type(error).__name__, 'error': ' '.join(str(error).split())[:2048],
            'fresh_archive_created': created, 'automatic_retry': False, 'allocation_performed': False,
            'model_inference_performed': False, 'wall_seconds': time.monotonic() - STARTED,
            'bridge_support': support_contract(),
            'supervisor_diagnostics': diagnostics(error, failed_phase)}
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
