#!/usr/bin/env python3
"""One guarded local tokenizer preflight using the unchanged frozen CLI.

This is a separate CPU attempt, not a successful remote run or a retry of an
allocation. The original failed remote observation remains pinned. The exact
previously reviewed Mac process-tree supervisor owns the guarded runpy worker.
No model framework, extra child, socket, SSH, installation or proof run is allowed.
"""
from __future__ import annotations
import time
STARTED = time.monotonic()

import argparse
import contextlib
import hashlib
import importlib.metadata
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

ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-retention-pilot-2026-08-30'
HELPER = ARCHIVE / 'run-retention-preflight-local-02.py'
FROZEN = ROOT / '_deploy/hydra-retention-execution-20260830'
PACKAGE = FROZEN / '_deploy/hydra-retention-pilot-v1'
CLI = FROZEN / 'scripts/execute_peano_hydra_retention.py'
CLI_SHA = '7e435d11124fca0946ca74012329b1ee68dc19efb19cb8a05655b71dbd258518'
COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
FREEZE = FROZEN / '_deploy/hydra-retention-execution-freeze.json'
FREEZE_SHA = '2cc7a302ac0156972acca3a2c7d0c4374426224c6e6493d2930a00855444bf52'
INPUTS_SHA = '3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388'
LOCAL_PLAN = ARCHIVE / 'training-bound-plan-local-01.json'
LOCAL_PLAN_SHA = '2079ff87df8c37a68cbb57ca0bd5256991d5a91b438679062727e426b1a44f99'
LOCAL_PLAN_SEMANTIC = 'da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0'
FAILED = ARCHIVE / 'cpu-preflight-01/ssh-process.json'
FAILED_PIN = {'bytes':6976, 'sha256':'2826daaaab440f214abbfd4c422a3a081f5c90e005e809577100809445cb9035'}
RUNTIME = Path('/private/tmp/hydra-retention-tokenizer-runtime-20260831-02')
CACHE = RUNTIME / 'hf-cache'
RUNTIME_MANIFEST = ARCHIVE / 'tokenizer-runtime-02.json'
RUNTIME_SHA = '19d2d4e42ad2eaa49f4371c7403336d79eb5046ec086df6932b82508210f055b'
IPV6_PROBE_SOURCE = RUNTIME / 'lib/python3.11/site-packages/urllib3/util/connection.py'
IPV6_PROBE_PIN = {'bytes':4444,'sha256':'2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74'}
PYTHON = Path('/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
RUNTIME_EXECUTABLE = RUNTIME / 'bin/python-owner-02'
PYTHON_COPY_RECEIPT = ARCHIVE / 'tokenizer-runtime-python-copy-02.json'
PYTHON_COPY_SHA = '79bef7d768b7636bc0b1efb339f6f5d3a87c5dee549554737b815c7ece7df86b'
SUPERVISOR = ROOT / 'artifacts/hydra-advancement-2026-08-30/run-v28-hotspots-supervised-v2.py'
SUPERVISOR_SHA = '1be34563858e2deba8e23ea47dc9f5966ffe092c3e0d23fe80a81a411b94af1c'
OUTPUT = ARCHIVE / 'cpu-preflight-local-02'
PREFLIGHT = OUTPUT / 'token-preflight.json'
PROCESS = OUTPUT / 'process.json'
REVISION = 'ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
MODEL_ID = 'Qwen/Qwen3-1.7B-Base'
LIMITS = {'per_process_cpu_seconds':180, 'sampled_whole_cpu_seconds':180, 'whole_wall_seconds':300,
          'sampled_group_rss_bytes':2147483648, 'combined_cli_output_bytes':262144,
          'supervisor_total_retained_bytes':67108864, 'file_bytes':4194304}
PACKAGES = {'certifi':'2025.7.14', 'charset-normalizer':'3.4.2', 'filelock':'3.18.0', 'fsspec':'2025.5.1',
    'hf-xet':'1.1.5', 'huggingface-hub':'0.33.4', 'idna':'3.10', 'numpy':'2.3.1', 'packaging':'25.0',
    'pip':'25.0.1', 'pyyaml':'6.0.2', 'regex':'2024.11.6', 'requests':'2.32.4', 'safetensors':'0.5.3',
    'setuptools':'78.1.0', 'tokenizers':'0.21.2', 'tqdm':'4.67.1', 'transformers':'4.53.3',
    'typing-extensions':'4.14.1', 'urllib3':'2.5.0'}
FORBIDDEN = frozenset(('torch','tensorflow','flax','jax','jaxlib','peft','accelerate','datasets','vllm',
                       'peano_lite','peano_native','_peano_native'))
OFFLINE = {'USE_TORCH':'0', 'USE_TF':'0', 'USE_FLAX':'0', 'HF_HUB_OFFLINE':'1', 'TRANSFORMERS_OFFLINE':'1',
           'HF_DATASETS_OFFLINE':'1', 'HF_HUB_DISABLE_TELEMETRY':'1', 'HF_HUB_DISABLE_XET':'1',
           'HF_HOME':str(CACHE), 'HF_HUB_CACHE':str(CACHE), 'HUGGINGFACE_HUB_CACHE':str(CACHE),
           'TOKENIZERS_PARALLELISM':'false', 'OMP_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1',
           'OPENBLAS_NUM_THREADS':'1', 'CUDA_VISIBLE_DEVICES':'', 'PYTHONDONTWRITEBYTECODE':'1'}
SHA = re.compile(r'[0-9a-f]{64}\Z')
SCHEMA = 'peano-hydra-retention-local-tokenizer-preflight-process-v2'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def pin(raw):
    return {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate metadata key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('nonfinite metadata')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    require(type(value) is dict, 'one JSON metadata object required')
    return value


def exact(path, exists=True):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve(strict=exists),
            'canonical nonsymlink absolute path required')
    return path


def fingerprint(path, maximum=64 * 1024**2, retain=False, deadline=None):
    path = exact(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'bounded single-link regular input required: ' + str(path))
        hasher, size, chunks = hashlib.sha256(), 0, []
        while True:
            require(deadline is None or time.monotonic() < deadline, 'whole-call deadline during file checks')
            block = os.read(fd, min(65536, maximum - size + 1))
            if not block:
                break
            size += len(block)
            require(size <= maximum, 'input grew beyond declared bound')
            hasher.update(block)
            if retain:
                chunks.append(block)
        signature = lambda item: (item.st_dev,item.st_ino,item.st_mode,item.st_size,item.st_mtime_ns,item.st_ctime_ns,item.st_nlink)
        require(signature(before) == signature(os.fstat(fd)) == signature(path.lstat()) and size == before.st_size,
                'input changed during fingerprinting')
        return {'bytes':size, 'sha256':hasher.hexdigest()}, b''.join(chunks)
    finally:
        os.close(fd)


def read_pinned(path, expected, maximum=LIMITS['file_bytes'], deadline=None):
    require(type(expected) is str and SHA.fullmatch(expected), 'external raw input SHA required')
    item, raw = fingerprint(path, maximum, True, deadline)
    require(item['sha256'] == expected, 'pinned metadata changed: ' + str(path))
    return decode(raw), raw


def write_new(path, record):
    require(path.parent == OUTPUT and exact(path, False) == path, 'fresh immediate local attempt output required')
    raw = canonical(record) + b'\n'
    require(len(raw) <= LIMITS['file_bytes'], 'local preflight metadata exceeds bound')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path':str(path), **pin(raw)}


def relative(name):
    require(type(name) is str and name and not name.startswith('/') and len(name) <= 4096
            and all(part not in ('', '.', '..') for part in name.split('/')), 'safe declared inventory path required')
    return name


def walk_files(root, *, skip_bytecode=False, maximum=8192):
    result, pending, entries = set(), [exact(root)], 0
    while pending:
        parent = pending.pop()
        for entry in os.scandir(parent):
            entries += 1
            require(entries <= maximum * 3, 'bounded metadata inventory exceeded')
            if skip_bytecode and entry.name == '__pycache__':
                require(entry.is_dir(follow_symlinks=False), 'unsafe bytecode directory')
                continue
            require(not entry.is_symlink(), 'unexpected symlink in declared code/package inventory')
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                pending.append(Path(entry.path))
            else:
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unexpected special input')
                result.add(str(Path(entry.path).relative_to(root)))
                require(len(result) <= maximum, 'input file-count cap')
    return result


def check_runtime(manifest, *, deadline):
    require(manifest.get('schema') == 'peano-hydra-retention-local-tokenizer-runtime-v1'
            and manifest.get('status') == 'ready' and manifest.get('runtime') == str(RUNTIME)
            and manifest.get('cache_root') == str(CACHE)
            and manifest.get('site_packages') == str(RUNTIME / 'lib/python3.11/site-packages')
            and manifest.get('model_id') == MODEL_ID and manifest.get('revision') == REVISION
            and manifest.get('packages') == PACKAGES
            and manifest.get('required_packages') == {k:v for k,v in PACKAGES.items() if k not in ('pip','setuptools')},
            'runtime path/dependency/base-tokenizer contract changed')
    require(all(manifest.get(key) is False for key in ('gpu_allocated','model_weights_downloaded','project_data_uploaded','tokenizer_loaded')),
            'runtime preparation claimed model/GPU work')
    require(manifest.get('framework_packages_absent') == ['torch','tensorflow','flax','jax','peft','accelerate','datasets','vllm'],
            'runtime framework absence contract changed')
    executable = RUNTIME / 'bin/python'
    require(executable.resolve(strict=True) == PYTHON and exact(PYTHON) == PYTHON
            and manifest['python'] == {'path':str(PYTHON), **fingerprint(PYTHON,deadline=deadline)[0]},
            'runtime interpreter target/raw identity changed')
    copied, copy_raw = read_pinned(PYTHON_COPY_RECEIPT,PYTHON_COPY_SHA,deadline=deadline)
    require(copied.get('schema') == 'peano-hydra-retention-local-tokenizer-python-copy-v1'
            and copied.get('status') == 'copied-and-startup-verified'
            and copied.get('source') == manifest['python']
            and copied.get('destination') == {'path':str(RUNTIME_EXECUTABLE),**fingerprint(RUNTIME_EXECUTABLE,deadline=deadline)[0]}
            and {k:copied['destination'][k] for k in ('bytes','sha256')} == {k:manifest['python'][k] for k in ('bytes','sha256')}
            and copied.get('runtime_manifest_sha256') == RUNTIME_SHA
            and copied.get('original_runtime_manifest_unchanged') is True and copied.get('source_unchanged') is True
            and copied.get('startup_returncode') == 0
            and copied.get('startup',{}).get('prefix') == str(RUNTIME)
            and copied['startup'].get('executable') == str(RUNTIME_EXECUTABLE),
            'canonical runtime executable must be the actual separately pinned identical copy')
    cfg_pin, cfg_raw = fingerprint(RUNTIME / 'pyvenv.cfg', 65536, True, deadline)
    require(b'include-system-site-packages = false' in cfg_raw, 'isolated runtime cannot enable system packages')
    items = manifest.get('runtime_files')
    require(type(items) is dict and len(items) == 4478 and manifest.get('runtime_files_bytes') == 100270653
            and sum(item['bytes'] for item in items.values()) == 100270653 <= 128 * 1024**2,
            'exact runtime code inventory required')
    site = RUNTIME / 'lib/python3.11/site-packages'
    names = {'lib/python3.11/site-packages/' + name for name in walk_files(site, skip_bytecode=True)}
    require(names == set(items), 'runtime packages contain undeclared or missing non-bytecode files')
    for name, expected in items.items():
        relative(name)
        require(name.startswith('lib/python3.11/site-packages/')
                and fingerprint(RUNTIME / name, deadline=deadline)[0] == expected, 'runtime code bytes changed')
    tokens = manifest.get('tokenizer_files')
    require(type(tokens) is dict and set(tokens) == {'config.json','generation_config.json','merges.txt','tokenizer.json','tokenizer_config.json','vocab.json'},
            'exact six genuine base-tokenizer files required')
    for name, item in tokens.items():
        declared = CACHE / ('models--Qwen--Qwen3-1.7B-Base/snapshots/' + REVISION) / name
        target = exact(Path(item['resolved_path']))
        require(item['path'] == str(declared) and declared.resolve(strict=True) == target
                and target.is_relative_to(CACHE / 'models--Qwen--Qwen3-1.7B-Base/blobs')
                and fingerprint(target, 16 * 1024**2, deadline=deadline)[0] == {k:item[k] for k in ('bytes','sha256')},
                'authentic pinned base-tokenizer cache target changed')
    return {'manifest_sha256':RUNTIME_SHA, 'runtime_files_sha256':hashlib.sha256(canonical(items)).hexdigest(),
            'tokenizer_files_sha256':hashlib.sha256(canonical(tokens)).hexdigest(), 'pyvenv_config':cfg_pin,
            'interpreter':manifest['python'], 'canonical_runtime_interpreter':copied['destination'],
            'canonical_interpreter_copy_receipt':{'path':str(PYTHON_COPY_RECEIPT),**pin(copy_raw)}, 'packages':PACKAGES}


def check_inputs(*, deadline):
    freeze, _ = read_pinned(FREEZE, FREEZE_SHA, deadline=deadline)
    require(freeze.get('git_commit') == COMMIT and freeze.get('snapshot_root') == str(FROZEN)
            and freeze.get('snapshot_clean') is True and freeze.get('file_count') == 886
            and freeze.get('total_bytes') == 91043396, 'actual frozen source receipt changed')
    files = freeze['files']
    require(len(files) == 886 and sum(item['bytes'] for item in files.values()) <= 128 * 1024**2,
            'source inventory exceeded its unchanged bound')
    for name, item in files.items():
        relative(name)
        require(fingerprint(FROZEN / name, deadline=deadline)[0] == {k:item[k] for k in ('bytes','sha256')},
                'immutable frozen source bytes changed')
    origin = freeze['origin_source_manifest']
    require(origin['path'] == '_deploy/hydra-retention-origin-source.json'
            and fingerprint(FROZEN / origin['path'],deadline=deadline)[0] == {k:origin[k] for k in ('bytes','sha256')},
            'frozen origin-source metadata changed')
    package_names = walk_files(PACKAGE, maximum=32)
    require(len(package_names) == 18 and not {'token-preflight.json','train-request.json','evaluate-request.json','resource-request.json','approval.json'} & package_names,
            'local CPU preflight requires the original eighteen-file bootstrap package')
    package = {name:fingerprint(PACKAGE / name, deadline=deadline)[0] for name in sorted(package_names)}
    require(sum(item['bytes'] for item in package.values()) == 96025573
            and package['inputs.json']['sha256'] == INPUTS_SHA
            and fingerprint(CLI,deadline=deadline)[0]['sha256'] == CLI_SHA,
            'actual bootstrap/CLI input pins changed')
    plan, raw = read_pinned(LOCAL_PLAN, LOCAL_PLAN_SHA, deadline=deadline)
    require(plan.get('training_plan_sha256') == LOCAL_PLAN_SEMANTIC
            and hashlib.sha256(canonical({k:v for k,v in plan.items() if k != 'training_plan_sha256'})).hexdigest() == LOCAL_PLAN_SEMANTIC
            and (plan.get('training_rows'),plan.get('development_rows'),plan.get('expected_optimizer_steps')) == (11751,2840,1469),
            'original genuine local training plan changed')
    require(fingerprint(FAILED,deadline=deadline)[0] == FAILED_PIN, 'failed remote attempt01 must remain unchanged')
    return {'source_commit':COMMIT,'freeze_sha256':FREEZE_SHA,'source_files_sha256':hashlib.sha256(canonical(files)).hexdigest(),
            'package_files':package,'local_plan_raw_sha256':pin(raw)['sha256'],'previous_remote_failure':FAILED_PIN}


def load_supervisor():
    item, raw = fingerprint(SUPERVISOR, 65536, True)
    require(item['sha256'] == SUPERVISOR_SHA, 'original reviewed process-tree supervisor changed')
    module = types.ModuleType('retention_tokenizer_pinned_supervisor')
    module.__file__ = str(SUPERVISOR)
    sys.modules[module.__name__] = module
    exec(compile(raw,str(SUPERVISOR),'exec'),module.__dict__)
    return module


def whole_cpu(prefix, supervised, returned, current):
    require(all(type(v) in (int,float) and math.isfinite(v) and v >= 0 for v in (prefix,supervised,returned,current))
            and current >= returned, 'invalid cumulative CPU accounting')
    return max(current, prefix + supervised + current - returned)


def cumulative_cpu():
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def install_worker_guards():
    """Deny every socket; distinguish urllib3's documented failed IPv6 probe.

    The pinned import probe catches OSError and reports IPv6 unavailable. No
    socket is created, connected or bound. Only this exact call site and socket
    signature receive that nonfatal fallback; every other socket event is fatal.
    """
    import socket
    require(fingerprint(IPV6_PROBE_SOURCE,65536)[0] == IPV6_PROBE_PIN,
            'reviewed urllib3 capability-probe source changed')
    attempts = {'forbidden_imports':[], 'network_events':[], 'subprocess_events':[]}
    blocked_probes = []
    def exact_probe(event,args):
        if event != 'socket.__new__' or len(args) != 4 or tuple(args[1:]) != (socket.AF_INET6,socket.SOCK_STREAM,0):
            return False
        frame = sys._getframe(1)
        for _ in range(8):
            if frame is None:break
            if (frame.f_code.co_filename == str(IPV6_PROBE_SOURCE) and frame.f_code.co_name == '_has_ipv6'
                    and frame.f_locals.get('host') == '::1'):
                return True
            frame = frame.f_back
        return False
    def audit(event,args):
        if event == 'import' and args[0].split('.')[0] in FORBIDDEN:
            if len(attempts['forbidden_imports']) < 32: attempts['forbidden_imports'].append(str(args[0])[:128])
            raise RuntimeError('model/native framework import forbidden in tokenizer-only worker')
        if event.startswith('socket.'):
            if exact_probe(event,args) and len(blocked_probes) < 4:
                blocked_probes.append({'event':event,'source':str(IPV6_PROBE_SOURCE),**IPV6_PROBE_PIN,
                                       'function':'_has_ipv6','host':'::1','socket_created':False,
                                       'action':'denied-before-socket-creation-with-documented-OSError-fallback'})
                raise OSError('offline tokenizer guard denies optional IPv6 capability socket')
            if len(attempts['network_events']) < 32: attempts['network_events'].append(event)
            raise RuntimeError('network operation forbidden in offline tokenizer worker')
        if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty','os.exec'}:
            if len(attempts['subprocess_events']) < 32: attempts['subprocess_events'].append(event)
            raise RuntimeError('extra subprocess forbidden in tokenizer worker')
    sys.addaudithook(audit)
    return attempts,blocked_probes


def worker(request_path, expected_sha):
    request, _ = read_pinned(request_path, expected_sha)
    require(request_path == OUTPUT / 'reservation.json' and request.get('schema') == 'peano-hydra-retention-local-tokenizer-reservation-v2'
            and request.get('owner_pid') == os.getppid() and type(request.get('owner_pid')) is int
            and request.get('runtime_manifest_sha256') == RUNTIME_SHA and request.get('limits') == LIMITS
            and request.get('source_commit') == COMMIT and request.get('inputs_sha256') == INPUTS_SHA
            and type(request.get('deadline')) in (int,float) and math.isfinite(request['deadline'])
            and time.monotonic() < request['deadline'] <= time.monotonic()+300,
            'worker needs its actual owner reservation')
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin' and sys.version_info[:2] == (3,11)
            and Path(sys.prefix) == RUNTIME and exact(Path(sys.executable)) == RUNTIME_EXECUTABLE
            and all(os.environ.get(key) == value for key,value in OFFLINE.items()),
            'isolated exact offline tokenizer runtime required')
    require(fingerprint(HELPER)[0]['sha256'] == request['helper_sha256'], 'guarded worker helper changed')
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    resource.setrlimit(resource.RLIMIT_CPU,(min(180,soft),min(180,hard)))
    resource.setrlimit(resource.RLIMIT_FSIZE,(LIMITS['file_bytes'],LIMITS['file_bytes']))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    def expired(*_):
        raise TimeoutError('local tokenizer worker whole-call deadline')
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,max(.001,request['deadline']-time.monotonic()))
    versions = {re.sub(r'[-_.]+','-',dist.metadata['Name']).lower():dist.version for dist in importlib.metadata.distributions()}
    require(versions == PACKAGES, 'actual isolated dependency versions differ from literal reviewed versions')
    require(not FORBIDDEN.intersection(sys.modules), 'model/native module was loaded before guarded CLI entry')
    attempts, blocked_probes = install_worker_guards()
    total = [0]
    class Captured(io.StringIO):
        def write(self,text):
            total[0] += len(text.encode())
            require(total[0] <= LIMITS['combined_cli_output_bytes'], 'combined original CLI output cap')
            return super().write(text)
    out, err, code, error = Captured(), Captured(), None, None
    argv = [str(CLI),'--token-preflight','--inputs',str(PACKAGE/'inputs.json'),
            '--expected-inputs-sha256',INPUTS_SHA,'--output',str(PREFLIGHT)]
    original = sys.argv
    try:
        sys.argv = list(argv)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                runpy.run_path(str(CLI),run_name='__main__')
                code = 0
            except SystemExit as stopped:
                code = stopped.code if type(stopped.code) is int else (0 if stopped.code is None else 1)
        require(code == 0, 'unchanged frozen tokenizer CLI did not exit successfully')
        require(not any(attempts.values()) and not FORBIDDEN.intersection(sys.modules), 'tokenizer worker crossed its declared boundary')
        preflight, raw = read_pinned(PREFLIGHT, fingerprint(PREFLIGHT)[0]['sha256'])
        local_plan, _ = read_pinned(LOCAL_PLAN, LOCAL_PLAN_SHA)
        require(preflight.get('schema') == 'peano-hydra-retention-pilot-preflight-v1'
                and preflight.get('profile') == 'peano-hydra-retention-pilot-v1'
                and preflight.get('run_id') == 'retention-pilot-v1' and preflight.get('training_plan') == local_plan
                and all(preflight.get(key) is False for key in ('model_weights_loaded','gpu_allocated','training_authorized')),
                'actual tokenizer output differs from the genuine archived training plan')
        token = preflight['token_preflight']
        require(token.get('schema') == 'peano-hydra-retention-token-preflight-v1'
                and token.get('training_plan_sha256') == LOCAL_PLAN_SEMANTIC
                and token.get('token_preflight_sha256') == hashlib.sha256(canonical({k:v for k,v in token.items() if k!='token_preflight_sha256'})).hexdigest()
                and token.get('model_weights_loaded') is False and token.get('model_training_authorized') is False,
                'actual token exposure record changed its no-model scope')
        result_pin = {'path':str(PREFLIGHT),**pin(raw)}
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2048]
        result_pin = None
    finally:
        sys.argv = original
    observation = {'schema':'peano-hydra-retention-local-tokenizer-worker-v2','status':'passed' if error is None else 'failed',
        'cli':{'path':str(CLI),'sha256':CLI_SHA}, 'argv':argv,
        'execution':'unchanged fixed CLI via guarded runpy.run_path', 'returncode':code,'error':error,
        'preflight':result_pin,'archived_local_plan_equal':error is None, 'packages':versions,
        'stdout':out.getvalue(),'stderr':err.getvalue(),'combined_cli_output_bytes':total[0],
        'guard_attempts':attempts,'blocked_optional_ipv6_capability_probe':blocked_probes,'forbidden_modules_loaded':sorted(FORBIDDEN.intersection(sys.modules)),
        'python_audit_guard_is_not_an_OS_sandbox':True,'model_weights_loaded':False,'gpu_allocated':False,
        'native_proofs_executed':False,'network_contacted':False,'ssh_contacted':False,'automatic_retry':False,'resume':False}
    write_new(OUTPUT/'worker.json',observation)
    print(json.dumps({'status':observation['status'],'returncode':code,'error':error,'preflight':result_pin},sort_keys=True),flush=True)
    signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if error is None else 2


def owner(args):
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin' and sys.version_info[:2] == (3,11)
            and Path(sys.executable).resolve(strict=True) == PYTHON and Path(__file__).absolute() == HELPER,
            'fixed Mac Python3.11 local owner required')
    require(exact(args.runtime) == RUNTIME and exact(args.hf_cache) == CACHE
            and args.expected_runtime_manifest_sha256 == RUNTIME_SHA
            and type(args.expected_helper_sha256) is str and SHA.fullmatch(args.expected_helper_sha256),
            'actual exact runtime/cache and reviewed helper pins required')
    require(fingerprint(HELPER)[0]['sha256'] == args.expected_helper_sha256 and not os.path.lexists(OUTPUT),
            'fresh local attempt02 and exact helper required; no overwrite/retry')
    resource.setrlimit(resource.RLIMIT_CPU,(180,180))
    resource.setrlimit(resource.RLIMIT_FSIZE,(LIMITS['file_bytes'],LIMITS['file_bytes']))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    def expired(*_):
        raise TimeoutError('whole local tokenizer preflight300-second deadline')
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,max(.001,STARTED+300-time.monotonic()))
    OUTPUT.mkdir(mode=0o700)
    write_new(OUTPUT/'started.json',{'schema':'peano-hydra-retention-local-tokenizer-start-v2',
        'runtime':str(RUNTIME),'cache':str(CACHE),'runtime_manifest_sha256':RUNTIME_SHA,
        'helper_sha256':args.expected_helper_sha256,'source_commit':COMMIT,'inputs_sha256':INPUTS_SHA,
        'limits':LIMITS,'previous_remote_failure':{'path':str(FAILED),**FAILED_PIN},'automatic_retry':False,
        'network_contacted':False,'ssh_contacted':False})
    supervisor = process = result_pin = worker_record = None
    before = runtime_before = None
    prefix_cpu = returned_cpu = 0.0
    error = None
    try:
        manifest, manifest_raw = read_pinned(RUNTIME_MANIFEST,RUNTIME_SHA,deadline=STARTED+300)
        runtime_before = check_runtime(manifest,deadline=STARTED+300)
        before = check_inputs(deadline=STARTED+300)
        supervisor = load_supervisor()
        reservation = {'schema':'peano-hydra-retention-local-tokenizer-reservation-v2','owner_pid':os.getpid(),
            'helper_sha256':args.expected_helper_sha256,'runtime_manifest_sha256':RUNTIME_SHA,
            'source_commit':COMMIT,'inputs_sha256':INPUTS_SHA,'deadline':STARTED+285,'limits':LIMITS}
        reservation_pin = write_new(OUTPUT/'reservation.json',reservation)
        command = (str(RUNTIME_EXECUTABLE),'-I','-B','-X','pycache_prefix=/dev/null',str(HELPER),'--worker',
                   str(OUTPUT/'reservation.json'),reservation_pin['sha256'])
        prefix_cpu = cumulative_cpu()
        # Keep the unchanged supervisor's maxima; deduct actual owner setup
        # CPU and leave fifteen seconds for all final hash/publication checks.
        remaining_cpu = 180-prefix_cpu-1
        require(remaining_cpu >= .1 and time.monotonic() < STARTED+280,'no bounded worker budget remains after input checks')
        saved_environment = {key:os.environ.get(key) for key in OFFLINE}
        os.environ.update(OFFLINE)
        try:
            process = supervisor.supervise(command,cwd=FROZEN,directory=OUTPUT,
                limits=supervisor.Limits(cpu_seconds=remaining_cpu),
                metadata={'purpose':'actual tokenizer-only preflight from immutable retention CLI',
                          'reservation_sha256':reservation_pin['sha256'],'helper_sha256':args.expected_helper_sha256,
                          'runtime_manifest_sha256':RUNTIME_SHA,'native_proof_execution_requested':False},
                started=STARTED,deadline=STARTED+285)
        finally:
            for key,value in saved_environment.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value
        returned_cpu = cumulative_cpu()
        write_new(OUTPUT/'supervision.json',process)
        require(process['status'] == 'process-completed-with-open-gates'
                and process['returncode'] == 0 and not process['remaining_live_owned_pids'],
                'actual tokenizer worker did not complete inside the original process-tree envelope')
        worker_record = decode(fingerprint(OUTPUT/'worker.json',LIMITS['file_bytes'],True)[1])
        require(worker_record['status'] == 'passed' and worker_record['returncode'] == 0
                and worker_record['error'] is None and worker_record['archived_local_plan_equal'] is True
                and not any(worker_record['guard_attempts'].values()) and not worker_record['forbidden_modules_loaded'],
                'actual unchanged CLI/tokenizer worker was not successful')
        result_pin, raw = fingerprint(PREFLIGHT,LIMITS['file_bytes'],True,STARTED+300)
        require(worker_record['preflight'] == {'path':str(PREFLIGHT),**result_pin},'published token preflight bytes differ from worker')
        actual = decode(raw)
        original,_ = read_pinned(LOCAL_PLAN,LOCAL_PLAN_SHA,deadline=STARTED+300)
        require(actual['training_plan'] == original,'actual CPU tokenizer result changed the genuine archived plan')
        require(check_inputs(deadline=STARTED+300) == before
                and check_runtime(manifest,deadline=STARTED+300) == runtime_before
                and fingerprint(RUNTIME_MANIFEST,deadline=STARTED+300)[0] == pin(manifest_raw)
                and fingerprint(HELPER,deadline=STARTED+300)[0]['sha256'] == args.expected_helper_sha256
                and fingerprint(SUPERVISOR,deadline=STARTED+300)[0]['sha256'] == SUPERVISOR_SHA,
                'immutable source/inputs/runtime/cache/owner changed through preflight')
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2048]
    retained = supervisor.retained_bytes(OUTPUT) if supervisor is not None else sum(p.stat().st_size for p in OUTPUT.iterdir() if p.is_file())
    current_cpu = cumulative_cpu()
    accounted = (whole_cpu(prefix_cpu,process['accounted_cpu_lower_bound_seconds'],returned_cpu,current_cpu)
                 if process is not None and returned_cpu else current_cpu)
    own = resource.getrusage(resource.RUSAGE_SELF)
    parent_rss = int(own.ru_maxrss)
    combined_rss = max(parent_rss,process['peak_sampled_combined_rss_bytes'] if process is not None else 0)
    if accounted >= 180 or combined_rss > 2*1024**3 or time.monotonic() >= STARTED+300 or retained >= 64*1024**2:
        error = error or 'whole local CPU/RSS/wall/retained-output boundary reached'
    passed = error is None and result_pin is not None
    result = {'schema':SCHEMA,'status':'passed' if passed else 'failed','error':error,
        'source_commit':COMMIT,'source_root':str(FROZEN),'inputs_sha256':INPUTS_SHA,'cli_sha256':CLI_SHA,
        'local_plan_raw_sha256':LOCAL_PLAN_SHA,'local_plan_sha256':LOCAL_PLAN_SEMANTIC,
        'archived_local_plan_equal':passed,'source_files_unchanged':passed,'input_pins_unchanged':passed,
        'runtime_and_tokenizer_cache_unchanged':passed,
        'owned_group_quiescent':process is not None and not process['remaining_live_owned_pids'],
        'returncode':None if worker_record is None else worker_record['returncode'],
        'preflight':None if not passed else {'path':str(PREFLIGHT),**result_pin},
        'runtime_manifest':{'path':str(RUNTIME_MANIFEST),'bytes':742500,'sha256':RUNTIME_SHA},
        'runtime_root':str(RUNTIME),'hf_cache_root':str(CACHE),
        'previous_remote_failure':{'path':str(FAILED),**FAILED_PIN},
        'helper_sha256':args.expected_helper_sha256,'supervisor_sha256':SUPERVISOR_SHA,
        'supervision':process,'worker':worker_record,'source_inputs_before':before,'runtime_before':runtime_before,
        'measurements':{'accounted_whole_cpu_seconds':accounted,'whole_wall_seconds':time.monotonic()-STARTED,
            'parent_peak_rss_bytes':parent_rss,'peak_sampled_parent_plus_group_rss_bytes':combined_rss},
        'limits':LIMITS,'cpu_is_exact_aggregate':False,'rss_is_instantaneous_hard_cap':False,
        'model_weights_loaded':False,'gpu_allocated':False,'native_proofs_executed':False,'network_contacted':False,
        'ssh_contacted':False,'original_origin_weight_bytes_may_be_hashed':True,
        'actual_remote_CPU_success_claimed':False,'automatic_retry':False,'resume':False}
    require(retained + len(canonical(result)) + 1 <= 64*1024**2,'local owner receipt exceeds original retained-output envelope')
    descriptor = write_new(PROCESS,result)
    print(json.dumps({'status':result['status'],'receipt':descriptor,'preflight':result['preflight'],'error':error},sort_keys=True),flush=True)
    require(time.monotonic() < STARTED+300,'owner receipt publication exceeded whole-call wall')
    final_cpu = cumulative_cpu()
    final_accounted = (whole_cpu(prefix_cpu,process['accounted_cpu_lower_bound_seconds'],returned_cpu,final_cpu)
                       if process is not None and returned_cpu else final_cpu)
    require(final_accounted < 180 and int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) <= 2*1024**3,
            'owner publication exceeded whole-call CPU/RSS; a retained receipt alone does not mean successful exit')
    signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if passed else 2


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        return worker(Path(sys.argv[2]),sys.argv[3])
    parser = argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--runtime',required=True,type=Path)
    parser.add_argument('--hf-cache',required=True,type=Path)
    parser.add_argument('--expected-runtime-manifest-sha256',required=True)
    parser.add_argument('--expected-helper-sha256',required=True)
    return owner(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
