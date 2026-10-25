#!/usr/bin/env python3
"""One bounded CPU admission/input check, followed by separate exit custody.

Run modes never publish usable custody. The operator must observe the actual
owner process exit and retain an independently pinned invocation-exit.json;
only a later --seal-admission call can join it to the provisional admission.
The unchanged v2 supervisor owns the process tree. Its sampled CPU/RSS caveats
remain explicit. No model, tokenizer, native proof, network or GPU work occurs.
"""
import time
STARTED = time.monotonic()
import argparse
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import runpy
import signal
import stat
import sys
import types

WORKSPACE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = WORKSPACE / 'artifacts/hydra-retention-evaluation-recovery-2026-08-31'
HELPER = ARCHIVE / 'run-recovery-cpu-preflight-01.py'
SOURCE = WORKSPACE / '_deploy/hydra-retention-evaluation-recovery-execution-20260831'
PACKAGE = SOURCE / '_deploy/hydra-retention-evaluation-recovery-v1'
CATALOG = SOURCE / '_deploy/hydra-retention-evaluation-recovery-source.json'
CLI = SOURCE / 'scripts/execute_peano_hydra_retention_evaluation_recovery.py'
ADMISSION_WORKER = SOURCE / 'scripts/authenticate_peano_hydra_retention_saved.py'
SUPERVISOR = WORKSPACE / 'artifacts/hydra-advancement-2026-08-30/run-v28-hotspots-supervised-v2.py'
SUPERVISOR_SHA = '1be34563858e2deba8e23ea47dc9f5966ffe092c3e0d23fe80a81a411b94af1c'
PYTHON = Path('/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
FRAMEWORK_PYTHON = PYTHON.parent.parent / 'Resources/Python.app/Contents/MacOS/Python'
RUNTIME_PYTHON_ALIAS = '/opt/homebrew/opt/python@3.11/bin/python3.11'
PYTHON_FILES = {
    str(PYTHON): {'bytes': 52640, 'sha256': '4df3f520de9c3b86c4ae895c68921509ff29cfb9562656f7c31ed25591d68b29'},
    str(FRAMEWORK_PYTHON): {'bytes': 51584, 'sha256': '631bb98f8a6a3bd3aceb01eb052344339a835877f0e873bef052ba89a33458c8'},
}
PRODUCER_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
LIMITS = {'cpu_seconds': 40, 'wall_seconds': 90, 'rss_bytes': 2 * 1024**3, 'output_bytes': 16 * 1024**2}
MAX_METADATA, MAX_SOURCE_TOTAL, MAX_SOURCE_FILES = 4 * 1024**2, 128 * 1024**2, 2048
MODES = ('authenticate-admission', 'check-inputs')
OWNER_SCHEMA = 'peano-hydra-retention-recovery-cpu-owner-v1'
REQUEST_SCHEMA = 'peano-hydra-retention-recovery-cpu-request-v1'
GUARD_SCHEMA = 'peano-hydra-retention-recovery-cpu-guard-v1'
NO_WORK = {'model_weights_loaded': False, 'tokenizer_loaded': False, 'native_proof_work': False,
    'gpu_allocated': False, 'network_work': False, 'training_performed': False,
    'original_load_training_artifact_succeeded': False, 'automatic_retry': False, 'resume': False}
FORBIDDEN = frozenset({'torch', 'transformers', 'tokenizers', 'peft', 'accelerate', 'safetensors',
    'tensorflow', 'flax', 'jax', 'datasets', 'peano_lite'})


def require(condition, message):
    if not condition: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(raw): return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_METADATA, 'bounded metadata object required')
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, 'duplicate metadata field'); result[name] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(value) is dict, 'metadata must be an object')
    return value


def exact(path, *, exists=True):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(path.parts) <= 64
        and len(str(path).encode()) <= 4096 and path == path.resolve(strict=exists),
        'canonical nonsymlink absolute path required')
    return path


def fingerprint(path, *, maximum=MAX_METADATA, retain=False, deadline=None):
    path = exact(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
            'bounded single-link regular input required')
        hasher, pieces, size = hashlib.sha256(), [], 0
        while True:
            if deadline is not None: require(time.monotonic() < deadline, 'whole-call deadline during byte checks')
            block = stream.read(65536)
            if not block: break
            size += len(block); require(size <= maximum, 'input grew beyond its declared bound')
            hasher.update(block)
            if retain: pieces.append(block)
        signature = lambda v: (v.st_dev, v.st_ino, v.st_mode, v.st_size, v.st_mtime_ns, v.st_ctime_ns, v.st_nlink)
        require(size == before.st_size and signature(before) == signature(os.fstat(stream.fileno())) == signature(path.lstat()),
            'input changed during streaming hash')
    return {'path': str(path), 'bytes': size, 'sha256': hasher.hexdigest()}, b''.join(pieces)


def read_pinned(path, expected, *, maximum=MAX_METADATA, deadline=None):
    require(type(expected) is str and re.fullmatch(r'[0-9a-f]{64}', expected), 'external raw SHA256 required')
    item, raw = fingerprint(path, maximum=maximum, retain=True, deadline=deadline)
    require(item['sha256'] == expected, 'externally pinned input changed: ' + str(path))
    return decode(raw), item, raw


def write_new(path, value):
    path = exact(path, exists=False)
    require(ARCHIVE in path.parents and SOURCE not in path.parents and not os.path.lexists(path),
            'fresh external archive output required')
    raw = canonical(value) + b'\n'
    require(len(raw) <= MAX_METADATA, 'metadata publication exceeds its bound')
    exact(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    item, observed = fingerprint(path, retain=True)
    require(observed == raw, 'publication changed bytes')
    return item


def relative(name):
    require(type(name) is str and name and not name.startswith('/') and len(name.encode()) <= 4096
        and all(part not in ('', '.', '..') for part in name.split('/')), 'safe source-relative path required')
    return name


def attempt(mode):
    require(mode in MODES, 'only admission and evaluation-input checks are supported')
    # Failed layout/wrapper starts remain immutable in admission-01 and 02.
    return ARCHIVE / ('admission-03' if mode == MODES[0] else 'input-check-01')


def input_path(mode):
    return PACKAGE / ('admission-request.json' if mode == MODES[0] else 'inputs.json')


def output_path(mode):
    return attempt(mode) / ('inner/admission.json' if mode == MODES[0] else 'preflight.json')


def source_snapshot(commit, catalog_sha, mode, input_sha, cli_sha, worker_sha, *, deadline):
    require(type(commit) is str and re.fullmatch(r'[0-9a-f]{40}', commit) and commit != PRODUCER_COMMIT,
            'distinct actual new source commit required')
    require(exact(SOURCE / '.git').is_dir(),
            'the unchanged scientific output guard requires a normal local Git directory, not a linked-worktree Git file')
    catalog, descriptor, _ = read_pinned(CATALOG, catalog_sha, deadline=deadline)
    require(set(catalog) == {'schema', 'git_commit', 'producer_source_commit', 'files', 'files_sha256', 'coverage', 'saved_model_retrained'}
        and catalog['schema'] == 'peano-hydra-evaluation-recovery-source-bundle-v1'
        and catalog['git_commit'] == commit and catalog['producer_source_commit'] == PRODUCER_COMMIT
        and catalog['saved_model_retrained'] is False and type(catalog['files']) is dict
        and 0 < len(catalog['files']) <= MAX_SOURCE_FILES and catalog['files_sha256'] == sha(canonical(catalog['files'])),
        'actual frozen source catalogue differs from declared recovery identity')
    checked, total = {}, 0
    for name, declared in sorted(catalog['files'].items()):
        relative(name)
        require(type(declared) is dict and set(declared) == {'bytes', 'sha256', 'mode', 'git_blob'}
            and declared['mode'] in ('100644', '100755') and type(declared['git_blob']) is str
            and re.fullmatch(r'[0-9a-f]{40}', declared['git_blob']) and type(declared['bytes']) is int
            and 0 <= declared['bytes'] <= 64 * 1024**2, 'source catalogue entry changed its exact raw/Git shape')
        item, _ = fingerprint(SOURCE / name, maximum=64 * 1024**2, deadline=deadline)
        require({key: item[key] for key in ('bytes', 'sha256')} == {key: declared[key] for key in ('bytes', 'sha256')}
            and bool((SOURCE / name).stat().st_mode & 0o111) == (declared['mode'] == '100755'),
            'actual frozen source byte or executable mode changed: ' + name)
        total += item['bytes']; require(total <= MAX_SOURCE_TOTAL, 'source catalogue aggregate byte bound')
        checked[name] = {key: item[key] for key in ('bytes', 'sha256')}
    for path, expected in ((CLI, cli_sha), (ADMISSION_WORKER, worker_sha)):
        require(type(expected) is str and re.fullmatch(r'[0-9a-f]{64}', expected)
                and checked.get(path.relative_to(SOURCE).as_posix(), {}).get('sha256') == expected,
                'actual CLI/admission worker differs from external source pins')
    input_record, input_descriptor, _ = read_pinned(input_path(mode), input_sha, deadline=deadline)
    require(input_record.get('schema') == 'peano-hydra-retention-evaluation-recovery-inputs-v1'
        and input_record.get('profile') == 'peano-hydra-retention-evaluation-recovery-v1'
        and input_record.get('run_id') == 'retention-evaluation-recovery-v1', 'wrong fixed recovery input manifest')
    require(read_pinned(CATALOG, catalog_sha, deadline=deadline)[1] == descriptor, 'source catalogue changed during hashing')
    return {'source_commit': commit, 'source_manifest': descriptor, 'files': checked, 'files_sha256': sha(canonical(checked)),
        'file_count': len(checked), 'total_source_bytes': total, 'input': input_descriptor,
        'external_origin_data_and_artifact_authentication': 'performed by the unchanged frozen scientific CLI inside the guarded worker'}


def load_supervisor():
    item, raw = fingerprint(SUPERVISOR, maximum=65536, retain=True)
    require(item['sha256'] == SUPERVISOR_SHA, 'original v2 process-tree supervisor changed')
    module = types.ModuleType('retention_recovery_original_supervisor_v2')
    module.__file__ = str(SUPERVISOR); sys.modules[module.__name__] = module
    exec(compile(raw, str(SUPERVISOR), 'exec'), module.__dict__)
    require(module.HELPER == SUPERVISOR, 'retained supervisor entrypoint changed')
    return module, item


def cumulative_cpu():
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def whole_cpu(prefix, supervised, returned, current):
    require(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (prefix, supervised, returned, current))
        and current >= returned, 'invalid cumulative CPU measurements')
    return max(current, prefix + supervised + current - returned)


def runtime_wrapper_python():
    """Match the unchanged runtime's raw sys.executable, with a fixed pin."""
    value = sys.executable
    require(value in (str(PYTHON), RUNTIME_PYTHON_ALIAS)
        and Path(value).resolve(strict=True) == PYTHON,
        'runtime wrapper must use the known Homebrew launcher or its exact opt alias')
    item, _ = fingerprint(PYTHON, maximum=65536)
    require({key: item[key] for key in ('bytes', 'sha256')} == PYTHON_FILES[str(PYTHON)],
            'runtime wrapper launcher bytes changed')
    return value


def install_worker_guard(request):
    """Source-bound audit guard for the reviewed metadata caller, not an OS sandbox."""
    attempts, counts = [], {'admission_worker': 0, 'original_group_sampler': 0}
    runtime_path = str(SOURCE / 'training/peano_hydra/review_runtime.py')
    python = request['cli_command'][0]
    wrapper_python = runtime_wrapper_python()
    target = (python, '-I', '-B', str(ADMISSION_WORKER))
    def frame_for(name):
        frame = sys._getframe(1)
        for _ in range(24):
            if frame is None: break
            if frame.f_code.co_filename == runtime_path and frame.f_code.co_name == name: return frame
            frame = frame.f_back
        return None
    def reject(event):
        if len(attempts) < 32: attempts.append(str(event)[:256])
        raise RuntimeError('CPU metadata guard denied ' + str(event))
    def audit(event, args):
        if event == 'import' and args[0].split('.')[0] in FORBIDDEN: reject('framework-import:' + args[0])
        if event.startswith('socket.'): reject(event)
        if event == 'ctypes.dlopen' and args and args[0] is not None: reject('native-library-load')
        if event == 'subprocess.Popen':
            require(len(args) == 4, 'unexpected subprocess audit signature')
            command = tuple(args[1]) if isinstance(args[1], (list, tuple)) else ()
            launch = frame_for('run_bounded')
            if request['mode'] == 'authenticate-admission' and launch is not None:
                limits = launch.f_locals.get('limits')
                expected = (wrapper_python, str(SOURCE / 'scripts/hydra_bounded_exec.py'), '--cpu-seconds',
                    str(getattr(limits, 'cpu_seconds', None)), '--rss-bytes', str(LIMITS['rss_bytes']), '--', *target)
                if (command == expected and args[0] == wrapper_python and runtime_wrapper_python() == wrapper_python
                    and counts['admission_worker'] == 0
                    and tuple(launch.f_locals.get('command', ())) == target
                    and type(getattr(limits, 'cpu_seconds', None)) is int and 1 <= limits.cpu_seconds <= 30
                    and getattr(limits, 'rss_bytes', None) == LIMITS['rss_bytes']
                    and type(getattr(limits, 'wall_seconds', None)) is int and 1 <= limits.wall_seconds <= 60
                    and getattr(limits, 'output_bytes', None) == 4 * 1024**2):
                    counts['admission_worker'] += 1; return
                sample = frame_for('_group_members')
                if (sample is not None and counts['admission_worker'] == 1
                    and command in (('/bin/ps', '-axo', 'pid=,pgid=,rss='), ('/usr/bin/ps', '-axo', 'pid=,pgid=,rss='))
                    and args[0] == command[0] and type(sample.f_locals.get('pid')) is int
                    and sample.f_locals['pid'] == getattr(launch.f_locals.get('process'), 'pid', None)
                    and counts['original_group_sampler'] < 1024):
                    counts['original_group_sampler'] += 1; return
            reject('subprocess:' + repr(command)[:180])
        if event in ('os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'os.exec', 'os.spawn'): reject(event)
    sys.addaudithook(audit)
    return attempts, counts


def worker(request_path, expected_sha):
    request, request_pin, _ = read_pinned(request_path, expected_sha)
    mode = request.get('mode'); out = attempt(mode)
    require(request.get('schema') == REQUEST_SCHEMA and request_path == out / 'request.json'
        and request.get('owner_pid') == os.getppid() and request.get('limits') == LIMITS
        and request.get('output_directory') == str(out), 'guarded worker lacks its actual owner request')
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
        and Path(__file__).absolute() == HELPER and fingerprint(HELPER, maximum=65536)[0] == request['helper'],
        'isolated exact externally pinned metadata worker required')
    require(type(request['deadline']) in (int, float) and math.isfinite(request['deadline'])
        and time.monotonic() < request['deadline'] <= time.monotonic() + LIMITS['wall_seconds'], 'expired owner deadline')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS['output_bytes'], LIMITS['output_bytes']))
    # Do not install an alarm here: the unchanged admission function owns its
    # separate SIGALRM. The external v2 owner supervises this entire process tree.
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'worker must not inherit a caller alarm')
    sys.dont_write_bytecode = True; sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(SOURCE), str(SOURCE / 'peano-lab/py')]
    require(not FORBIDDEN.intersection(sys.modules), 'framework loaded before guarded CLI entry')
    before = source_snapshot(request['source_commit'], request['source_manifest']['sha256'], mode,
        request['input']['sha256'], request['cli']['sha256'], request['admission_worker']['sha256'], deadline=request['deadline'])
    require(before == request['source_before'], 'source/input bytes changed before guarded entry')
    attempts, counts = install_worker_guard(request)
    wrapper_python = runtime_wrapper_python()
    total = [0]
    class Capture(io.StringIO):
        def write(self, value):
            total[0] += len(value.encode()); require(total[0] <= 65536, 'bounded CLI stdout/stderr exceeded')
            return super().write(value)
    stdout, stderr, code, error, result, admission_sources = Capture(), Capture(), None, None, None, None
    original = sys.argv
    try:
        command = request['cli_command']
        expected = [str(Path(sys.executable).resolve(strict=True)), '-I', '-B', str(CLI), '--' + mode,
            '--inputs', str(input_path(mode)), '--expected-inputs-sha256', request['input']['sha256'], '--output',
            str(output_path(mode).parent if mode == 'authenticate-admission' else output_path(mode))]
        require(command == expected, 'guarded CLI command changed its fixed mode/input/output')
        sys.argv = command[3:]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                runpy.run_path(str(CLI), run_name='__main__'); code = 0
            except SystemExit as stopped:
                code = stopped.code if type(stopped.code) is int else (0 if stopped.code is None else 1)
        require(code == 0 and not attempts and not FORBIDDEN.intersection(sys.modules)
            and runtime_wrapper_python() == wrapper_python, 'actual guarded CLI failed or crossed its scope')
        result, raw = fingerprint(output_path(mode), retain=True, deadline=request['deadline'])
        output_record = decode(raw)
        from training.peano_hydra import retention_saved_artifact as saved
        admission_sources = saved.admission_sources()
        require(all(before['files'].get(name, {}).get('sha256') == value for name, value in admission_sources.items()),
            'actual admission source inventory differs from complete current source catalogue')
        if mode == 'authenticate-admission':
            require(counts['admission_worker'] == 1 and output_record.get('schema') == saved.RECEIPT_SCHEMA
                and output_record.get('status') == 'passed-corrected-historical-admission'
                and output_record['request']['admission_sources'] == admission_sources
                and output_record['request']['execution']['python'] == command[0], 'actual provisional admission did not complete')
            expected_stdout = (json.dumps(result, sort_keys=True, allow_nan=False) + '\n').encode()
        else:
            require(counts['admission_worker'] == 0 and output_record.get('schema') == 'peano-hydra-retention-evaluation-recovery-input-check-v1'
                and output_record.get('inputs_sha256') == request['input']['sha256']
                and all(output_record.get(key) is False for key in ('model_weights_loaded', 'gpu_allocated', 'training_authorized', 'native_proof_replay_performed')),
                'actual metadata-only evaluation input check did not complete')
            expected_stdout = (json.dumps({'status': 'written', 'output': result['path'], 'sha256': result['sha256']}, sort_keys=True) + '\n').encode()
        require(stdout.getvalue().encode() == expected_stdout and not stderr.getvalue(), 'actual CLI stdout/exit differs from its published output')
        require(source_snapshot(request['source_commit'], request['source_manifest']['sha256'], mode,
            request['input']['sha256'], request['cli']['sha256'], request['admission_worker']['sha256'], deadline=request['deadline']) == before,
            'source/input bytes changed during guarded CLI work')
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2048]
    finally:
        sys.argv = original
    guard = {'schema': GUARD_SCHEMA, 'status': 'passed' if error is None else 'failed', 'mode': mode,
        'runtime_wrapper_executable': wrapper_python, 'runtime_wrapper_resolved_launcher': str(PYTHON),
        'request_sha256': request_pin['sha256'], 'cli_command': request['cli_command'],
        'cli_sha256': request['cli']['sha256'], 'admission_worker_sha256': request['admission_worker']['sha256'],
        'admission_sources': admission_sources, 'forbidden_attempts': attempts, 'allowed_subprocess_counts': counts,
        'original_cli_returncode': code, 'output': result, 'error': error,
        'python_audit_guard_is_not_an_OS_sandbox': True, **NO_WORK}
    write_new(out / 'worker-guard.json', guard)
    sys.stdout.write(stdout.getvalue()); sys.stdout.flush()
    sys.stderr.write(stderr.getvalue())
    if error is not None: print(error, file=sys.stderr, flush=True)
    require(time.monotonic() < request['deadline'], 'guarded worker publication exceeded owner deadline')
    return 0 if error is None else 2


def accounting(supervisor, out, process, prefix, returned):
    retained = supervisor.retained_bytes(out)
    own = resource.getrusage(resource.RUSAGE_SELF)
    current = cumulative_cpu()
    cleanup = process.get('cleanup') if type(process) is dict else None
    return {'limits': LIMITS, 'cpu_seconds': whole_cpu(prefix, process['accounted_cpu_lower_bound_seconds'], returned, current)
        if process is not None else current, 'wall_seconds': time.monotonic() - STARTED,
        'peak_rss_bytes': max(own.ru_maxrss, 0 if process is None else process['peak_sampled_combined_rss_bytes']),
        'retained_bytes': retained, 'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
        'whole_process_tree_quiescent': type(cleanup) is dict and process.get('remaining_live_owned_pids') == []
            and cleanup.get('controller_reaped') is True and cleanup.get('remaining_live_owned_pids') == []
            and cleanup.get('remaining_zombie_owned_pids') == [] and cleanup.get('errors') == [],
        'post_supervision_accounted_cpu_seconds': max(0, current - returned),
        'measurement_boundary': 'Final postcheck measurement; publication tail is rechecked before actual owner exit. Custody requires separately observed zero exit.'}


def within(record):
    return all(type(record.get(key)) in (int, float) and math.isfinite(record[key]) and 0 <= record[key] <= maximum
        for key, maximum in (('cpu_seconds', 40), ('wall_seconds', 90), ('peak_rss_bytes', LIMITS['rss_bytes']),
                              ('retained_bytes', LIMITS['output_bytes'])))


def owner_invocation(python, interpreter_argv):
    """Retain Homebrew's real framework argv and the external launcher form.

    Homebrew rewrites argv[0] before Python starts. This is a fixed, byte-pinned
    mapping, not a claim that the running owner observed the tool invocation.
    A later external exit receipt must match the complete launcher argv before
    any usable custody can be published.
    """
    require(python == str(PYTHON) and type(interpreter_argv) is list and len(interpreter_argv) >= 5
        and all(type(value) is str for value in interpreter_argv)
        and interpreter_argv[0] in (str(PYTHON), str(FRAMEWORK_PYTHON))
        and interpreter_argv[1:4] == ['-I', '-B', str(HELPER)],
        'exact isolated pinned Homebrew launcher/framework invocation required')
    observed_files = {}
    for name, expected in PYTHON_FILES.items():
        item, _ = fingerprint(Path(name), maximum=65536)
        require({key: item[key] for key in ('bytes', 'sha256')} == expected,
                'actual pinned Python launcher/framework bytes changed')
        observed_files[name] = item
    return [str(PYTHON), *interpreter_argv[1:]], {
        'interpreter_orig_argv': list(interpreter_argv), 'python_files': observed_files,
        'mapping': 'fixed Homebrew 3.11.12 launcher to framework executable',
        'external_owner_argv_observed_by_running_helper': False,
        'exact_external_exit_argv_match_required_for_custody': True,
    }


def owner(args, mode):
    out = attempt(mode); exact(ARCHIVE)
    require(not os.path.lexists(out), 'one-use CPU attempt already exists; no retry or resume')
    helper, _ = fingerprint(HELPER, maximum=65536)
    require(helper['sha256'] == args.expected_helper_sha256, 'external CPU owner helper pin changed')
    supervisor, supervisor_pin = load_supervisor()
    before = source_snapshot(args.source_commit, args.expected_source_catalog_sha256, mode, args.expected_input_sha256,
        args.expected_cli_sha256, args.expected_admission_worker_sha256, deadline=STARTED + 90)
    python = str(Path(sys.executable).resolve(strict=True))
    argv, python_launch_identity = owner_invocation(python, list(sys.orig_argv))
    os.mkdir(out, 0o700)
    command_cli = [python, '-I', '-B', str(CLI), '--' + mode, '--inputs', str(input_path(mode)),
        '--expected-inputs-sha256', args.expected_input_sha256, '--output',
        str(output_path(mode).parent if mode == 'authenticate-admission' else output_path(mode))]
    request = {'schema': REQUEST_SCHEMA, 'mode': mode, 'owner_pid': os.getpid(), 'owner_argv': argv,
        'python_launch_identity': python_launch_identity,
        'source_commit': args.source_commit, 'source_manifest': before['source_manifest'], 'source_before': before,
        'input': before['input'], 'helper': helper, 'supervisor': supervisor_pin,
        'cli': fingerprint(CLI)[0], 'admission_worker': fingerprint(ADMISSION_WORKER)[0],
        'cli_command': command_cli, 'output_directory': str(out), 'deadline': STARTED + 90, 'limits': LIMITS, **NO_WORK}
    request_pin = write_new(out / 'request.json', request)
    command = (python, '-I', '-B', str(HELPER), '--worker', '--request', request_pin['path'], '--expected-request-sha256', request_pin['sha256'])
    process, guard, guard_pin, result, after, error, sources = None, None, None, None, None, None, None
    prefix, returned = cumulative_cpu(), cumulative_cpu()
    try:
        remaining = 40 - prefix - 1
        require(remaining >= .1 and time.monotonic() < STARTED + 80, 'no bounded metadata budget remains after initial checks')
        process = supervisor.supervise(command, cwd=SOURCE, directory=out,
            limits=supervisor.Limits(cpu_seconds=remaining, wall_seconds=85, rss_bytes=LIMITS['rss_bytes'], output_bytes=LIMITS['output_bytes']),
            metadata={'purpose': 'actual frozen metadata-only retention recovery ' + mode, 'request_sha256': request_pin['sha256'], **NO_WORK},
            started=STARTED, deadline=STARTED + 85)
        returned = cumulative_cpu()
        write_new(out / 'process.json', process)
        require(process['status'] == 'process-completed-with-open-gates' and process['reason'] == 'exited'
            and process['returncode'] == 0 and process['error'] is None and not process['remaining_live_owned_pids'],
            'actual guarded CLI did not complete successfully under the unchanged original supervisor')
        guard_pin, guard_raw = fingerprint(out / 'worker-guard.json', retain=True)
        guard = decode(guard_raw)
        require(guard['schema'] == GUARD_SCHEMA and guard['status'] == 'passed' and guard['mode'] == mode
            and guard['request_sha256'] == request_pin['sha256'] and guard['cli_command'] == command_cli
            and guard['original_cli_returncode'] == 0 and guard['error'] is None and guard['forbidden_attempts'] == []
            and guard['allowed_subprocess_counts']['admission_worker'] == (1 if mode == 'authenticate-admission' else 0)
            and all(guard.get(key) is False for key in NO_WORK), 'actual CPU worker guard did not finish cleanly')
        result, output_raw = fingerprint(output_path(mode), retain=True)
        output_record = decode(output_raw); sources = guard['admission_sources']
        require(guard['output'] == result and guard['cli_sha256'] == args.expected_cli_sha256
            and guard['admission_worker_sha256'] == args.expected_admission_worker_sha256,
            'actual guard output or source pin differs from the requested CLI')
        expected_stdout = (json.dumps(result if mode == 'authenticate-admission' else
            {'status': 'written', 'output': result['path'], 'sha256': result['sha256']}, sort_keys=True, allow_nan=False) + '\n').encode()
        require(process['logs']['stdout'] == {'bytes': len(expected_stdout), 'sha256': sha(expected_stdout)}
            and fingerprint(out / 'stdout.log', retain=True)[1] == expected_stdout
            and process['logs']['stderr'] == {'bytes': 0, 'sha256': sha(b'')}, 'original CLI stdout/stderr evidence changed')
        if mode == 'authenticate-admission':
            require(output_record['request']['admission_sources'] == sources, 'actual admission source inventory differs from worker guard')
        after = source_snapshot(args.source_commit, args.expected_source_catalog_sha256, mode, args.expected_input_sha256,
            args.expected_cli_sha256, args.expected_admission_worker_sha256, deadline=STARTED + 90)
        require(after == before and fingerprint(HELPER, maximum=65536)[0] == helper
            and fingerprint(SUPERVISOR, maximum=65536)[0] == supervisor_pin
            and owner_invocation(python, list(sys.orig_argv)) == (argv, python_launch_identity),
            'source/input/owner/supervisor or actual Python launcher changed during CPU work')
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2048]
    measured = accounting(supervisor, out, process, prefix, returned)
    if not within(measured) or not measured['whole_process_tree_quiescent']:
        error = error or 'final CPU owner accounting or process-tree quiescence failed'
    record = {'schema': OWNER_SCHEMA, 'status': 'passed' if error is None else 'failed', 'mode': mode,
        'helper': helper, 'supervisor': supervisor_pin, 'source_commit': args.source_commit,
        'source_manifest': before['source_manifest'], 'input': before['input'], 'request_file': request_pin, 'request': request,
        'cli_command': command_cli, 'command': list(command), 'supervision': process,
        'worker_guard_file': guard_pin, 'worker_guard': guard, 'output': result,
        'source_before': before, 'source_after': after, 'source_unchanged': before == after,
        'inputs_unchanged': before == after, 'accounting': measured, 'admission_sources': sources,
        'error': error, 'usable_admission_custody_published': False, 'actual_owner_exit_requires_external_observation': True, **NO_WORK}
    # Include this final receipt's bytes without mutating any earlier file.
    for _ in range(4):
        measured['retained_bytes'] = supervisor.retained_bytes(out) + len(canonical(record)) + 1
    require(within(measured), 'owner metadata cannot fit within the retained resource envelope')
    owner_pin = write_new(out / 'owner.json', record)
    require(within(accounting(supervisor, out, process, prefix, returned)), 'owner publication exceeded its whole-call envelope')
    print(json.dumps({'status': record['status'], 'mode': mode, 'owner_result': owner_pin, 'output': result,
        'usable_admission_custody_published': False, 'error': error}, sort_keys=True), flush=True)
    require(within(accounting(supervisor, out, process, prefix, returned)), 'owner final output exceeded its whole-call envelope')
    return 0 if error is None else 2


def seal(args):
    """Use actual separately observed exit evidence; never create it here."""
    out = attempt('authenticate-admission')
    target = out / 'admission-custody.json'
    require(not os.path.lexists(target), 'admission custody already exists; no overwrite')
    helper, _ = fingerprint(HELPER, maximum=65536)
    require(helper['sha256'] == args.expected_helper_sha256, 'sealing helper differs from external pin')
    owner_record, owner_pin, _ = read_pinned(out / 'owner.json', args.expected_owner_sha256)
    invocation, invocation_pin, invocation_raw = read_pinned(out / 'invocation-exit.json', args.expected_invocation_sha256)
    require(owner_record.get('mode') == 'authenticate-admission' and owner_record.get('helper') == helper,
            'sealing must use this exact actual admission owner')
    _, supervisor_pin = load_supervisor()
    require(owner_record['supervisor'] == supervisor_pin, 'original owner supervisor changed before custody')
    request = owner_record['request']
    before = source_snapshot(owner_record['source_commit'], owner_record['source_manifest']['sha256'], 'authenticate-admission',
        owner_record['input']['sha256'], request['cli']['sha256'], request['admission_worker']['sha256'], deadline=STARTED + 90)
    require(before == owner_record['source_after'], 'source/input bytes changed before custody sealing')
    inner, inner_pin, inner_raw = read_pinned(output_path('authenticate-admission'), owner_record['output']['sha256'])
    require(inner_pin == owner_record['output'] and canonical(inner) + b'\n' == inner_raw, 'provisional admission bytes changed')
    for descriptor in (owner_record['request_file'], owner_record['worker_guard_file']):
        require(fingerprint(Path(descriptor['path']), retain=True)[0] == descriptor, 'actual retained owner input/guard bytes changed')
    process_pin, process_raw = fingerprint(out / 'process.json', retain=True)
    require(decode(process_raw) == owner_record['supervision'], 'actual retained supervision receipt changed')
    for label in ('stdout', 'stderr'):
        item, _ = fingerprint(out / (label + '.log'))
        require({k: item[k] for k in ('bytes', 'sha256')} == owner_record['supervision']['logs'][label], 'actual supervision stream changed')
    sys.dont_write_bytecode = True; sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(SOURCE), str(SOURCE / 'peano-lab/py')]
    require(not FORBIDDEN.intersection(sys.modules), 'sealing cannot inherit frameworks')
    # This entrypoint only validates already retained JSON. It never calls
    # .load(), authenticate_admission(), model code, native code or a scheduler.
    from training.peano_hydra import retention_saved_artifact as saved
    custody = {'schema': saved.CUSTODY_SCHEMA, 'status': 'completed-caller-admission',
        'admission': inner, 'admission_file': inner_pin, 'owner_result': owner_record, 'owner_result_file': owner_pin,
        'invocation_json': invocation_raw.decode('utf-8'), 'invocation_file': invocation_pin,
        'owner_helper': helper, 'owner_supervisor': supervisor_pin,
        'claim_boundary': 'Actual externally observed successful CPU owner exit plus original-source corrected metadata admission; no model quality, native proof or GPU authority.',
        **NO_WORK}
    saved._validate_custody(custody)
    require(source_snapshot(owner_record['source_commit'], owner_record['source_manifest']['sha256'], 'authenticate-admission',
        owner_record['input']['sha256'], request['cli']['sha256'], request['admission_worker']['sha256'], deadline=STARTED + 90) == before,
        'source/input bytes changed while checking actual custody')
    require(cumulative_cpu() <= 40 and time.monotonic() - STARTED <= 90
        and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= LIMITS['rss_bytes'], 'sealing resource envelope reached')
    require(len(canonical(custody)) + 1 <= MAX_METADATA, 'completed custody exceeds original metadata cap')
    # The original attempt and all later custody evidence share the same
    # retained-byte ceiling; no old record is removed to manufacture room.
    supervisor, _ = load_supervisor()
    require(supervisor.retained_bytes(out) + len(canonical(custody)) + 1 <= LIMITS['output_bytes'], 'custody exceeds retained byte ceiling')
    result = write_new(target, custody)
    require(cumulative_cpu() <= 40 and time.monotonic() - STARTED <= 90
        and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= LIMITS['rss_bytes'], 'custody publication exceeded sealing envelope')
    print(json.dumps({'status': 'completed-caller-admission', 'custody': result, 'actual_owner_exit_observed_by_this_helper': False}, sort_keys=True), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--authenticate-admission', action='store_true')
    modes.add_argument('--check-inputs', action='store_true')
    modes.add_argument('--seal-admission', action='store_true')
    modes.add_argument('--worker', action='store_true')
    parser.add_argument('--request', type=Path)
    parser.add_argument('--expected-request-sha256')
    for name in ('helper', 'source-catalog', 'input', 'cli', 'admission-worker', 'owner', 'invocation'):
        parser.add_argument('--expected-' + name + '-sha256')
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
        and sys.version_info >= (3, 11) and Path(__file__).absolute() == HELPER,
        'fixed isolated Mac Python3.11+ CPU helper required')
    require(not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
        'CPU helper cannot inherit an allocation or dynamic-loader overrides')
    if args.worker:
        require(args.request is not None and args.expected_request_sha256 is not None
            and all(getattr(args, name) is None for name in ('expected_helper_sha256', 'expected_source_catalog_sha256',
                'expected_input_sha256', 'expected_cli_sha256', 'expected_admission_worker_sha256',
                'expected_owner_sha256', 'expected_invocation_sha256', 'source_commit')), 'worker only accepts its exact owner request')
        return worker(args.request, args.expected_request_sha256)
    require(args.request is None and args.expected_request_sha256 is None, 'owner modes cannot adopt a worker request')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0)); resource.setrlimit(resource.RLIMIT_CPU, (40, 41))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS['output_bytes'], LIMITS['output_bytes']))
    def expired(*_): raise TimeoutError('CPU owner whole-call 90-second deadline')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 90 - (time.monotonic() - STARTED)))
    if args.seal_admission:
        require(all(type(getattr(args, name)) is str for name in ('expected_helper_sha256', 'expected_owner_sha256', 'expected_invocation_sha256'))
            and all(getattr(args, name) is None for name in ('expected_source_catalog_sha256', 'source_commit',
                'expected_input_sha256', 'expected_cli_sha256', 'expected_admission_worker_sha256')), 'sealing only accepts actual helper/owner/invocation pins')
        result = seal(args)
    else:
        require(all(type(getattr(args, name)) is str for name in ('expected_helper_sha256', 'expected_source_catalog_sha256',
            'source_commit', 'expected_input_sha256', 'expected_cli_sha256', 'expected_admission_worker_sha256'))
            and args.expected_owner_sha256 is None and args.expected_invocation_sha256 is None, 'actual external source/input/worker pins required')
        result = owner(args, 'authenticate-admission' if args.authenticate_admission else 'check-inputs')
    require(cumulative_cpu() <= 40 and time.monotonic() - STARTED <= 90, 'final caller envelope reached')
    signal.setitimer(signal.ITIMER_REAL, 0)
    return result


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, TimeoutError) as error:
        print('retention-recovery-cpu: ' + ' '.join(str(error).split())[:2048], file=sys.stderr, flush=True)
        raise SystemExit(2)
