"""Small pure command/result checks; no invocation, transport, gate or job work."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import shlex
import signal
import sys
import time
import types

started = time.monotonic()
A = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
P = A / 'invoke-retention-launch-01.py'
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('pure launch checks wall cap')))
signal.alarm(20)


def audit(event, args):
    if event.startswith(('subprocess.', 'os.system', 'os.posix_spawn', 'socket.')):
        raise RuntimeError('pure fixtures cannot execute a process or network')
    if event == 'import' and args[0].split('.')[0] in {'training', 'torch', 'transformers', 'peft', 'tokenizers'}:
        raise RuntimeError('pure fixtures cannot import deployment or model code')


sys.addaudithook(audit)
raw = P.read_bytes()
ast.parse(raw, feature_version=(3, 9)); compile(raw, str(P), 'exec')
spec = importlib.util.spec_from_file_location('retention_launch_invoker_fixture', P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
context = {'identity': {'approval_sha256': 'a' * 64, 'resource_request_sha256': 'b' * 64},
           'remote_control_receipt': {'sha256': 'c' * 64}, 'source_header_sha256': 'd' * 64}
checks = ['python39_syntax_and_python311_compile']
for stage in ('train', 'evaluate'):
    seconds = 7200 if stage == 'train' else 3600
    for mode in ('test-only', 'submit'):
        body = m.remote_body(mode, stage, context)
        lines = body.splitlines()
        command = shlex.split(lines[-1][len('exec '):])
        assert command == ['/usr/bin/python3.9', '-I', '-B', m.GATE, '--approval-sha256', 'a' * 64,
                           '--' + mode, stage, '--source-commit', m.COMMIT]
        assert lines[0] == 'set -euo pipefail' and lines[1] == 'cd -- ' + m.REMOTE_ROOT
        assert body.index('sha256sum --check --status') < body.index('--check)') < body.index('exec ')
        assert '--source-commit' in body and 'module load' not in body and '\nsbatch ' not in body
        if mode == 'test-only':
            value = {'status': 'test-only', 'stage': stage, 'reservation': {'seconds': seconds, 'gpus': 1, 'cpus': 8, 'memory_gib': 64},
                'allocation_performed': False, 'automatic_retry': False,
                'model_manifest': None if stage == 'train' else {'bytes': 100, 'sha256': 'e' * 64}}
        else:
            value = {'status': 'submitted', 'profile': m.PROFILE, 'run_id': m.RUN_ID, 'stage': stage,
                'job_id': '999999999999', 'reserved_gpu_seconds': seconds, 'maximum_aggregate_gpu_seconds': 10800,
                'maximum_concurrent_gpus': 1, 'automatic_retry': False, 'resume': False, 'refunds': False,
                'ledger': 'logs/hydra-retention-pilot-v1-' + stage + '.jsonl',
                'output': 'results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1' if stage == 'train'
                          else 'results/peano-hydra/evaluations/retention-pilot-v1'}
        assert m.validate_result(value, mode, stage) == value
        bad = dict(value, stage='evaluate' if stage == 'train' else 'train')
        try: m.validate_result(bad, mode, stage)
        except ValueError: pass
        else: raise AssertionError('wrong stage admitted')
        checks.append(stage + '_' + mode + '_exact_command_and_result_scope')

# The transport is an explicit read-only fixture. It never loads the real
# transport module or constructs a success receipt for real controls/jobs.
failure = m.canonical({'schema': 'peano-hydra-retention-controls-transfer-send-result-v2',
                       'status': 'failed-no-automatic-retry'})
b = types.SimpleNamespace(read_file=lambda path, maximum: failure)
for label, pin in (('failed_control_transfer_rejected', m.sha(failure)), ('wrong_control_transfer_raw_pin_rejected', 'f' * 64)):
    try: m.control_context(b, pin, 'a' * 64, 'd' * 64)
    except ValueError: pass
    else: raise AssertionError(label)
    checks.append(label)
assert P.read_bytes() == raw
usage = resource.getrusage(resource.RUSAGE_SELF)
record = {'schema': 'peano-hydra-retention-launch-invoker-checks-v1', 'status': 'passed',
    'helper': {'path': str(P), 'bytes': len(raw), 'sha256': m.sha(raw)}, 'checks': checks,
    'fixtures_only': True, 'actual_invoker_or_gate_called': False, 'transport_loaded': False,
    'network_scheduler_model_native_or_frozen_source_edits': False,
    'resources': {'wall_seconds': time.monotonic() - started, 'cpu_seconds': usage.ru_utime + usage.ru_stime,
                  'peak_rss_bytes': usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024}}
output = A / 'launch-invoker-helper-checks-01.json'
receipt = m.canonical(record) + b'\n'
with output.open('xb') as stream: stream.write(receipt)
print(json.dumps({'status': 'passed', 'checks': len(checks), 'receipt': str(output), 'sha256': m.sha(receipt)}, sort_keys=True))
