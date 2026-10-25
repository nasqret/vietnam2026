#!/usr/bin/env python3
"""Pure arithmetic/audit/cleanup fixtures; no CPU owner, admission or seal run."""
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time
from types import SimpleNamespace

A = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
TARGET = A / 'run-recovery-cpu-preflight-01.py'
STARTED = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('pure fixture deadline')))
signal.alarm(15)


def deny_actions(event, args):
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.fork', 'os.exec', 'os.posix_spawn'):
        raise RuntimeError('real process/network actions forbidden in pure fixtures')
    if event == 'import' and args[0].split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers', 'peano_lite'):
        raise RuntimeError('framework imports forbidden in pure fixtures')


sys.addaudithook(deny_actions)
raw = TARGET.read_bytes()
tree = ast.parse(raw)
spec = importlib.util.spec_from_file_location('cpu_owner_pure_fixture', TARGET)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checked = []


def rejects(call):
    try: call()
    except (ValueError, RuntimeError): return
    raise AssertionError('invalid synthetic input was accepted')


assert m.whole_cpu(.5, 38.7, 10.5, 11.5) == 40.2
assert m.whole_cpu(.5, 2, 10.5, 11.5) == 11.5
for values in ((True, 1, 2, 3), (0, math.nan, 2, 3), (0, 1, 4, 3), (-1, 1, 2, 3)):
    rejects(lambda values=values: m.whole_cpu(*values))
checked.append('post-supervision tail remains charged when descendant accounting dominates')

record = {'cpu_seconds': 39, 'wall_seconds': 89, 'peak_rss_bytes': 1024, 'retained_bytes': 1024}
assert m.within(record)
for key, value in (('cpu_seconds', 40.01), ('wall_seconds', 90.01), ('peak_rss_bytes', 2*1024**3+1),
                   ('retained_bytes', 16*1024**2+1), ('cpu_seconds', math.nan), ('cpu_seconds', True)):
    assert not m.within({**record, key: value})
checked.append('fixed whole-call finite CPU/wall/RSS/retained-byte boundaries')

real_sys = m.sys
runtime = str(m.SOURCE / 'training/peano_hydra/review_runtime.py')
python = '/synthetic-only/python'
child = (python, str(m.SOURCE / 'scripts/hydra_bounded_exec.py'), '--cpu-seconds', '25', '--rss-bytes', str(2*1024**3),
         '--', python, '-I', '-B', str(m.ADMISSION_WORKER))
limits = SimpleNamespace(cpu_seconds=25, wall_seconds=50, rss_bytes=2*1024**3, output_bytes=4*1024**2)
launch = SimpleNamespace(f_code=SimpleNamespace(co_filename=runtime, co_name='run_bounded'),
    f_locals={'limits': limits, 'command': (python, '-I', '-B', str(m.ADMISSION_WORKER)), 'process': SimpleNamespace(pid=123)}, f_back=None)
sampler = SimpleNamespace(f_code=SimpleNamespace(co_filename=runtime, co_name='_group_members'),
                         f_locals={'pid': 123}, f_back=launch)
current, hooks = [launch], []
m.sys = SimpleNamespace(_getframe=lambda *_: current[0], addaudithook=lambda hook: hooks.append(hook))
try:
    attempts, counts = m.install_worker_guard({'mode': 'authenticate-admission', 'cli_command': [python]})
    hook = hooks[-1]
    hook('subprocess.Popen', (python, child, '/synthetic-only/producer', {}))
    assert counts['admission_worker'] == 1 and not attempts
    current[0] = sampler
    hook('subprocess.Popen', ('/bin/ps', ['/bin/ps', '-axo', 'pid=,pgid=,rss='], None, None))
    assert counts['original_group_sampler'] == 1
    current[0] = launch
    rejects(lambda: hook('subprocess.Popen', (python, child, None, None)))
    rejects(lambda: hook('socket.connect', (None,)))
    rejects(lambda: hook('ctypes.dlopen', ('/synthetic/native.so',)))
    assert len(attempts) == 3
    checked.append('only one exact original bounded metadata worker and its actual sampler frame are allowed')
    attempts, counts = m.install_worker_guard({'mode': 'check-inputs', 'cli_command': [python]})
    rejects(lambda: hooks[-1]('subprocess.Popen', (python, child, None, None)))
    assert counts['admission_worker'] == 0
    current[0] = SimpleNamespace(f_code=SimpleNamespace(co_filename='/wrong/source.py', co_name='run_bounded'),
                                f_locals=launch.f_locals, f_back=None)
    attempts, counts = m.install_worker_guard({'mode': 'authenticate-admission', 'cli_command': [python]})
    rejects(lambda: hooks[-1]('subprocess.Popen', (python, child, None, None)))
    assert counts['admission_worker'] == 0
    checked.append('input-only mode and wrong source frames cannot spawn metadata or native children')
finally:
    m.sys = real_sys

original_cpu = m.cumulative_cpu
m.cumulative_cpu = lambda: 11.5
supervisor = SimpleNamespace(retained_bytes=lambda _: 128)
process = {'cleanup': None, 'remaining_live_owned_pids': [], 'accounted_cpu_lower_bound_seconds': 38.7,
           'peak_sampled_combined_rss_bytes': 1024}
try:
    result = m.accounting(supervisor, Path('/synthetic-only'), process, .5, 10.5)
    assert result['cpu_seconds'] == 40.2 and result['whole_process_tree_quiescent'] is False
    assert m.accounting(supervisor, Path('/synthetic-only'), None, 0, 0)['whole_process_tree_quiescent'] is False
    process['cleanup'] = {'controller_reaped': True, 'remaining_live_owned_pids': [], 'remaining_zombie_owned_pids': [], 'errors': []}
    assert m.accounting(supervisor, Path('/synthetic-only'), process, .5, 10.5)['whole_process_tree_quiescent'] is True
    process['cleanup']['errors'] = ['synthetic sampler unavailable']
    assert m.accounting(supervisor, Path('/synthetic-only'), process, .5, 10.5)['whole_process_tree_quiescent'] is False
    checked.append('unavailable sampler/absent cleanup stays a retained failure, never false quiescence')
finally:
    m.cumulative_cpu = original_cpu

worker = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'worker')
assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr in ('alarm', 'setitimer') for node in ast.walk(worker))
assert b"read_pinned(out / 'invocation-exit.json', args.expected_invocation_sha256)" in raw
assert b"write_new(out / 'invocation-exit.json'" not in raw
assert b'saved._validate_custody(custody)' in raw
checked.append('guarded worker leaves inner SIGALRM alone; custody requires separately supplied actual exit bytes')

assert TARGET.read_bytes() == raw
usage = resource.getrusage(resource.RUSAGE_SELF)
observed = {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic()-STARTED,
            'peak_rss_bytes': usage.ru_maxrss}
assert observed['cpu_seconds'] < 10 and observed['wall_seconds'] < 15 and observed['peak_rss_bytes'] < 128*1024**2
result = {'schema': 'peano-hydra-retention-recovery-cpu-helper-pure-checks-v1', 'status': 'passed',
    'helper': {'path': str(TARGET), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
    'check_groups': len(checked), 'checks': checked, 'observed': observed,
    'limits': {'cpu_seconds': 10, 'wall_seconds': 15, 'rss_bytes': 128*1024**2, 'output_bytes': 65536},
    'actual_owner_worker_seal_or_admission_invoked': False, 'actual_source_binding_invoked': False,
    'native_model_network_scheduler_actions_performed': False, 'synthetic_fixtures_are_not_admission_evidence': True}
body = (json.dumps(result, sort_keys=True, indent=2)+'\n').encode()
path = A / 'recovery-cpu-helper-checks-01.json'
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, 'wb') as stream:
    stream.write(body); stream.flush(); os.fsync(stream.fileno())
signal.alarm(0)
print(json.dumps({'status': 'passed', 'groups': len(checked), 'receipt': str(path), 'sha256': hashlib.sha256(body).hexdigest(),
                  'helper_sha256': result['helper']['sha256'], 'observed': observed}, sort_keys=True))
