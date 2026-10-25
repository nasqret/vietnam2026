#!/usr/bin/env python3
"""One explicit bounded local original-origin authentication; no model loading.

The candidate's original b08 source/preparation and raw-pinned source manifest
remain read-only. Exact unchanged bridge code runs from the separate clean
612d1ea9 execution snapshot, so its bootstrap is outside the audited source.
The candidate model directory is assembled separately before this command.
No download, scheduler command, retry, receipt adoption, loader exemption or
guard modification is implemented here.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time

STARTED = time.monotonic()
WORKSPACE = Path('/Users/bnaskrecki/codex/peano')
ROOT = WORKSPACE / '_deploy/hydra-frontier-training-execution-20260830'
EXECUTION = WORKSPACE / '_deploy/hydra-model-test-execution-20260830'
ARCHIVE = WORKSPACE / 'artifacts/hydra-model-test-2026-08-30'
SOURCE_MANIFEST = ROOT / '_deploy/frontier-training-origin-source.json'
PREPARATION = ROOT / '_deploy/hydra-frontier-training-v1/admitted/preparation'
ADAPTER = ARCHIVE / 'candidate-model/manifest.json'
APPROVED_REQUEST = ROOT / '_deploy/hydra-frontier-training-v1/resource-request.json'
EXECUTION_RECEIPT = EXECUTION / '_deploy/hydra-diagnostic-execution-freeze.json'
PYTHON_ALIAS = Path('/opt/homebrew/opt/python@3.11/bin/python3.11')
PYTHON_PHYSICAL = Path('/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
SOURCE_COMMIT = 'b08a6b1303d73217f6cc23800ae15e50b17db792'
EXECUTION_COMMIT = '612d1ea9e4905dfe2af104696924a19bc5883752'
SOURCE_MANIFEST_SHA = '346f9ac39c7d66ebb2c340922d77fc5dbef8a2e867cb1825dddcea92e616ca3b'
PREPARATION_SHA = '729b97bf8418cb227d0ef1b1ba350fde5da537e46da4ad55774d8b4ca73517d3'
ADAPTER_SHA = '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'
APPROVED_REQUEST_SHA = '02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb'
EXECUTION_RECEIPT_SHA = '25ce03ef653c03440f163a7bdefdf41bfd90056f140a9128cfba2781aba0cff1'
SCHEMA = 'peano-hydra-local-original-origin-authentication-v1'
OUTPUTS = {
    'reservation': ARCHIVE / 'candidate-origin-local-01.reservation.json',
    'receipt': ARCHIVE / 'candidate-origin-receipt-local-01.json',
    'result': ARCHIVE / 'candidate-origin-local-01.result.json',
    'failure': ARCHIVE / 'candidate-origin-local-01.failure.json',
}
PARENT_LIMITS = {'cpu_seconds':20, 'cpu_hard_seconds_for_child_inheritance':121,
                 'wall_seconds':210, 'checked_peak_rss_bytes':512 * 1024**2,
                 'single_evidence_file_bytes':4 * 1024**2}
NATIVE_LIMITS = {'cpu_seconds':120, 'wall_seconds':180,
                 'rss_bytes':1024**3, 'output_bytes':2 * 1024**2}

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

_DIAGNOSTIC_PHASES = frozenset({
    'configured', 'metadata_checked', 'bootstrap_imported', 'native_reserved',
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
    require(path in OUTPUTS.values() and path.parent == ARCHIVE
            and len(raw) <= PARENT_LIMITS['single_evidence_file_bytes'],
            'unapproved or oversized local origin evidence')
    parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return {'path':str(path), 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def verify_bootstrap(root):
    total = 0
    for name, expected in SUPPORT_IDENTITIES.items():
        raw = read(root / name, MAX_SUPPORT_FILE_BYTES)
        require({'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()} == expected,
                'original bootstrap bytes changed: ' + name)
        total += len(raw)
        require(total <= MAX_SUPPORT_TOTAL_BYTES, 'bootstrap aggregate bytes exceeded')
    require(total == SUPPORT_TOTAL_BYTES and len(SUPPORT_IDENTITIES) == 4,
            'bootstrap inventory changed')


def checked_parent_bridge(execution_root):
    import importlib.machinery
    require(execution_root == EXECUTION, 'unreviewed parent import root')
    require(not any(name == first or name.startswith(first + '.')
                    for name in sys.modules for first in ('training', 'peano_lab', 'scripts')),
            'parent already imported project modules before its checked bootstrap')
    verify_bootstrap(execution_root)
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
    verify_bootstrap(execution_root)
    return bridge



def check_runtime():
    require(sys.platform == 'darwin' and sys.version_info[:2] == (3, 11),
            'this bounded local check requires the installed Mac Python3.11')
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == '/dev/null',
            'invoke with -I -B -X pycache_prefix=/dev/null')
    require(PYTHON_ALIAS.resolve(strict=True) == PYTHON_PHYSICAL
            and Path(sys.executable).resolve(strict=True) == PYTHON_PHYSICAL,
            'active interpreter differs from the reviewed physical Homebrew Python3.11')
    require(not any(name.startswith(('LD_', 'DYLD_', 'SBATCH_'))
                    or name in ('SLURM_JOB_ID', 'BASH_ENV', 'ENV')
                    for name in os.environ),
            'unreviewed loader or scheduler controls are forbidden')
    require(not ROOT.is_relative_to(EXECUTION) and not EXECUTION.is_relative_to(ROOT)
            and not ARCHIVE.is_relative_to(ROOT) and not ARCHIVE.is_relative_to(EXECUTION),
            'preserved inputs, execution and output roots must be disjoint')
    for path in (ROOT, EXECUTION, ARCHIVE, ADAPTER.parent):
        fd = directory(path)
        os.close(fd)


def pinned_json(path, expected_sha, expected_bytes=None):
    raw = read(path, 4 * 1024**2)
    require(hashlib.sha256(raw).hexdigest() == expected_sha
            and (expected_bytes is None or len(raw) == expected_bytes),
            'raw-pinned original metadata changed: ' + path.name)
    value = decode(raw)
    require(type(value) is dict, 'expected pinned metadata object')
    return value


def metadata_preflight():
    source = pinned_json(SOURCE_MANIFEST, SOURCE_MANIFEST_SHA, 184587)
    require(source['schema'] == 'peano-hydra-origin-source-bundle-v1'
            and source['git_commit'] == SOURCE_COMMIT and len(source['files']) == 845,
            'original source manifest identity changed')
    request = pinned_json(APPROVED_REQUEST, APPROVED_REQUEST_SHA)
    require(request['source_commit'] == SOURCE_COMMIT and request['run_id'] == 'frontier-training-v1',
            'original approved training request changed')
    pinned_json(PREPARATION / 'manifest.json', PREPARATION_SHA)
    pinned_json(ADAPTER, ADAPTER_SHA, 3369364)
    frozen = pinned_json(EXECUTION_RECEIPT, EXECUTION_RECEIPT_SHA)
    require(frozen['git_commit'] == EXECUTION_COMMIT and frozen['snapshot_clean'] is True
            and frozen['snapshot_root'] == str(EXECUTION)
            and frozen['file_count'] == 877,
            'execution freeze receipt differs from the reviewed snapshot')
    verify_bootstrap(EXECUTION)
    require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= PARENT_LIMITS['checked_peak_rss_bytes'],
            'local metadata supervisor RSS exceeds512MiB')


def base_record():
    return {
        'schema':SCHEMA, 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_root':str(ROOT), 'source_commit':SOURCE_COMMIT,
        'source_manifest':{'path':str(SOURCE_MANIFEST), 'bytes':184587, 'sha256':SOURCE_MANIFEST_SHA},
        'preparation':{'path':str(PREPARATION), 'manifest_sha256':PREPARATION_SHA},
        'adapter_manifest':{'path':str(ADAPTER), 'bytes':3369364, 'sha256':ADAPTER_SHA},
        'approved_training_request_sha256':APPROVED_REQUEST_SHA,
        'execution_root':str(EXECUTION), 'expected_execution_commit':EXECUTION_COMMIT,
        'execution_freeze_receipt_sha256':EXECUTION_RECEIPT_SHA,
        'execution_bootstrap':SUPPORT_IDENTITIES,
        'python':{'invocation_alias':str(PYTHON_ALIAS), 'reviewed_physical_path':str(PYTHON_PHYSICAL),
                  'active_executable':sys.executable},
        'parent_limits':PARENT_LIMITS, 'native_worker_limits':NATIVE_LIMITS,
        'runtime_library_paths':[], 'network_access_performed':False,
        'model_inference_performed':False, 'allocation_performed':False,
        'automatic_retry':False, 'preserved_inputs_modified':False,
        'loader_or_resource_guards_modified':False,
        'scope':'Original CPU validation only; no model test result or GPU authorization.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--authenticate', action='store_true', required=True)
    parser.parse_args()
    require(not any(os.path.lexists(path) for path in OUTPUTS.values()),
            'local original-auth attempt already has evidence; no retry or adoption')
    # Same parent CPU reservation; the hard limit allows the unchanged child
    # guard to install its original120/121-second worker limits after exec.
    resource.setrlimit(resource.RLIMIT_CPU, (20, 121))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    signal.signal(signal.SIGXCPU, budget)
    signal.signal(signal.SIGALRM, budget)
    signal.alarm(210)
    reserved = False
    authentication_invoked = False
    try:
        note_phase('configured')
        check_runtime()
        metadata_preflight()
        note_phase('metadata_checked')
        bridge = checked_parent_bridge(EXECUTION)
        require(bridge.ORIGIN_LIMITS.to_dict() == NATIVE_LIMITS,
                'original native worker limits changed')
        note_phase('bootstrap_imported')
        request = bridge.OriginRequest(
            source_root=ROOT, source_manifest=SOURCE_MANIFEST,
            source_manifest_sha256=SOURCE_MANIFEST_SHA, source_commit=SOURCE_COMMIT,
            preparation_directory=PREPARATION, preparation_manifest_sha256=PREPARATION_SHA,
            adapter_manifest=ADAPTER, adapter_manifest_sha256=ADAPTER_SHA,
            authority_profile=bridge.AUTHORITY_PROFILE,
        )
        note_phase('native_reserved')
        record = dict(base_record(), status='one-local-original-auth-reserved',
                      original_authentication_invoked=False, request=request.to_dict(),
                      locations=request.locations(), supervisor_diagnostics=diagnostics())
        reservation = write_new(OUTPUTS['reservation'], canonical(record) + b'\n')
        reserved = True
        note_phase('authenticating_original')
        authentication_invoked = True
        origin = bridge.authenticate_origin(
            request, python=PYTHON_PHYSICAL, limits=bridge.ORIGIN_LIMITS,
            runtime_library_paths=(),
        )
        note_phase('original_authenticated')
        verify_bootstrap(EXECUTION)
        require(not any(name == first or name.startswith(first + '.')
                        for name in sys.modules for first in ('torch', 'transformers', 'peft', 'tokenizers')),
                'local CPU parent imported model code')
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= PARENT_LIMITS['checked_peak_rss_bytes'],
                'local metadata supervisor RSS exceeds512MiB')
        receipt = write_new(OUTPUTS['receipt'], origin.receipt_bytes)
        require(receipt['sha256'] == origin.receipt_sha256, 'original receipt bytes changed during publication')
        note_phase('result_record')
        record = dict(base_record(), status='original-candidate-origin-authenticated',
                      original_authentication_invoked=True, reservation=reservation,
                      request=request.to_dict(), locations=request.locations(),
                      receipt=receipt, origin=origin.origin, supervisor_diagnostics=diagnostics())
        result = write_new(OUTPUTS['result'], canonical(record) + b'\n')
        print(canonical({'status':record['status'], 'receipt':receipt, 'result':result,
                         'supervisor_diagnostics':record['supervisor_diagnostics']}).decode(), flush=True)
        return 0
    except BaseException as error:
        failed_phase = _CURRENT_PHASE
        note_phase('failed')
        record = dict(base_record(), status='failed-no-retry',
                      error_type=type(error).__name__, error=' '.join(str(error).split())[:2048],
                      reservation_written=reserved, original_authentication_invoked=authentication_invoked,
                      supervisor_diagnostics=diagnostics(error, failed_phase))
        observation = getattr(error, 'observation', None)
        if observation is not None:
            record['original_validator_failure'] = observation
        raw = canonical(record) + b'\n'
        saved = None
        try:
            saved = write_new(OUTPUTS['failure'], raw)
        except (OSError, ValueError) as save_error:
            # Never overwrite a consumed failure or enlarge an evidence cap.
            record['failure_publication_error'] = type(save_error).__name__ + ': ' + str(save_error)[:1024]
        print(canonical({'status':record['status'], 'failure':saved, 'error_type':record['error_type'],
                         'error':record['error'], 'supervisor_diagnostics':record['supervisor_diagnostics'],
                         'failure_publication_error':record.get('failure_publication_error')}).decode(), flush=True)
        return 2
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
