#!/usr/bin/env python3
"""Tiny synthetic operation checks. No launcher, observer or watcher is run."""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import tempfile
import time
from types import SimpleNamespace

A = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
OLD = A.parent / 'hydra-retention-pilot-2026-08-30'
STARTED = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('operation pure-check deadline')))
signal.alarm(15)


def guard(event, args):
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.fork', 'os.exec', 'os.posix_spawn'):
        raise RuntimeError('real process/network operations forbidden in these fixtures')
    if event == 'import' and args[0].split('.')[0] in ('torch', 'transformers', 'peft', 'peano_lite'):
        raise RuntimeError('model/native imports forbidden in these fixtures')


sys.addaudithook(guard)
names = ('invoke-retention-evaluation-recovery-01.py', 'observe-retention-evaluation-recovery-01.py',
         'watch-retention-evaluation-recovery-01.py')
sources = {name: (A / name).read_bytes() for name in names}


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), A / name)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


launch, observer, watch = (load(name) for name in names)
remote = {'__name__': 'synthetic_observer_functions_only'}
exec(compile(observer.PROGRAM, '<synthetic remote function definitions>', 'exec'), remote)
checks = []


def rejects(call):
    try: call()
    except (ValueError, RuntimeError): return
    raise AssertionError('invalid synthetic metadata was accepted')


job = '99999999'
submitted = {'status': 'submitted', 'profile': launch.PROFILE, 'run_id': launch.RUN_ID, 'stage': 'evaluate', 'job_id': job,
    'reserved_gpu_seconds': 3600, 'maximum_aggregate_gpu_seconds': 3600, 'maximum_concurrent_gpus': 1,
    'ledger': 'logs/hydra-retention-evaluation-recovery-v1-evaluate.jsonl',
    'output': 'results/peano-hydra/evaluations/retention-evaluation-recovery-v1',
    'automatic_retry': False, 'resume': False, 'refunds': False}
tested = {'status': 'test-only', 'stage': 'evaluate', 'reservation': launch.RESERVATIONS['evaluate'],
          'allocation_performed': False, 'model_manifest': launch.MODEL_MANIFEST, 'automatic_retry': False}
assert launch.validate_result(submitted, 'submit', 'evaluate') == submitted
assert launch.validate_result(tested, 'test-only', 'evaluate') == tested
for change in ({'job_id': '21456251'}, {'job_id': '21457058'}, {'maximum_aggregate_gpu_seconds': 10800},
               {'resume': True}, {'profile': 'peano-hydra-retention-pilot-v1'}):
    rejects(lambda change=change: launch.validate_result({**submitted, **change}, 'submit', 'evaluate'))
rejects(lambda: launch.validate_result({**tested, 'model_manifest': {'bytes': 1, 'sha256': '0'*64}}, 'test-only', 'evaluate'))
rejects(lambda: launch.validate_result(tested, 'test-only', 'train'))
checks.append('new one-hour evaluation cannot reuse producer/failed jobs, old aggregate budget, old profile or another model')

identity = {'approval_sha256': 'a'*64, 'resource_request_sha256': 'b'*64,
    'producer_sha256': launch.sha(launch.canonical(launch.PRODUCER)), 'historical_admission_sha256': 'c'*64,
    'source_commit': 'd'*40, 'source_files_sha256': 'e'*64, 'payloads_sha256': 'f'*64,
    'synced_at': '2026-08-31T00:00:00Z', 'job_script_sha256': {'evaluate': '1'*64}}
context = {'identity': identity, 'source_header_sha256': launch.sha(launch.canonical(identity)),
    'reservations': launch.RESERVATIONS, 'producer': launch.PRODUCER, 'model_manifest': launch.MODEL_MANIFEST,
    'remote_control_receipt': {'path': launch.CONTROL_RECEIPT, 'bytes': 1, 'sha256': '2'*64},
    'scientific_inputs': {'evaluate': {'path': launch.PACKAGE+'/evaluate-request.json', 'bytes': 1, 'sha256': '3'*64}}}
body = launch.remote_body('test-only', 'evaluate', context)
assert '--test-only evaluate --source-commit ' + identity['source_commit'] in body
assert '--check' in body and 'historical_admission_sha256' in body and 'producer_sha256' in body
assert 'module load' not in body and 'retention_launch.py' not in body and '--submit' not in body
checks.append('login-shell body checks the new full source header before invoking only the new gate')

fake = SimpleNamespace(read_file=lambda *_: b'{"synthetic_only":true}')
rejects(lambda: launch.control_context(fake, '0'*64, 'a'*64, 'b'*64, 'c'*40))
checks.append('wrong external transfer pin fails before any gate import or invocation')

receipt = {'schema': 'peano-hydra-retention-evaluation-recovery-launch-invocation-v1', 'status': 'passed',
    'mode': 'submit', 'stage': 'evaluate', 'helper_sha256': watch.LAUNCHER_SHA, 'remote_command_started': True,
    'automatic_retry': False, 'frozen_source_modified': False, 'context': context, 'result': submitted,
    'process': {'returncode': 0, 'reason': 'exited', 'error': None, 'stdout': json.dumps(submitted)}}
assert watch.validate_submit(receipt, job) == context
for change in ({'mode': 'test-only'}, {'status': 'failed-or-uncertain'}, {'helper_sha256': '0'*64}):
    rejects(lambda change=change: watch.validate_submit({**receipt, **change}, job))
checks.append('watcher accepts only the exact successful new released-job invocation, not a test or uncertain submit')


def observation(state, row):
    binding = {**identity, 'job_id': job, 'stage': 'evaluate', 'source_header_sha256': context['source_header_sha256'],
        'ledger_phase': 'released', 'ledger_events': 6, 'reservation': launch.RESERVATIONS['evaluate'],
        'producer': launch.PRODUCER, 'reserved_model_manifest': launch.MODEL_MANIFEST}
    actual = {'binding': binding, 'read_only': True, 'scheduler_mutation_performed': False,
        'proofs_independently_verified': False, 'quality_claim': None, 'remote_file_writes': False, 'model_loaded': False,
        'progress': {'expected_checkpoint_records': 256, 'checkpoint_rows_or_proofs_verified': False,
                     'quality_claim': None, 'checkpoint_completed_records': None},
        'metadata': {'checkpoint_head': {'exists': False}},
        'scheduler': {'sacct': {} if row is None else {'bound_row': row}, 'observed_state': state},
        'observed_at_utc': '2026-08-31T00:00:00Z'}
    return {'schema': 'peano-hydra-retention-evaluation-recovery-observation-receipt-v1',
        'status': 'observed-not-proof-verified', 'returncode': 0, 'error': None, 'job_id': job, 'stage': 'evaluate',
        'source_commit': identity['source_commit'], 'approval_sha256': identity['approval_sha256'],
        'source_header_sha256': context['source_header_sha256'], 'helper': {'sha256': watch.OBSERVER_SHA},
        'read_only': True, 'automatic_retry': False, 'proofs_independently_verified': False, 'quality_claim': None,
        'observation': actual}


failed_row = [job, launch.PROFILE+'-evaluate', 'FAILED', '2:0', '23', '60', '8', '64G', 'gpu=1',
              launch.REMOTE_ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret']
items = {}
for state, row in ((None, None), ('PENDING', None), ('FAILED', failed_row)):
    value = observation(state, row)
    items[state] = watch.observation_item(value, watch.canonical(value), A/'retention-evaluate-observation-03.json', job, context)
    assert items[state]['checkpoint_committed_records'] is None and items[state]['quality_claim'] is None
assert items[None]['terminal'] is False and items['PENDING']['terminal'] is False
assert items['FAILED']['terminal'] is True and items['FAILED']['exit_code'] == '2:0'
bad = observation('FAILED', [*failed_row[:3], '9'*65536, *failed_row[4:]])
rejects(lambda: watch.observation_item(bad, watch.canonical(bad), A/'retention-evaluate-observation-03.json', job, context))
checks.append('absent scheduler/accounting/HEAD remain unknown; actual bounded failure is retained with no score')

with tempfile.TemporaryDirectory(prefix='recovery-watch-pure-', dir='/private/tmp') as temp:
    original_archive, original_live = watch.ARCHIVE, watch.LIVE
    watch.ARCHIVE, watch.LIVE = Path(temp), Path(temp)/'synthetic-view.md'
    try:
        watch.publish_view(items[None]); text = watch.LIVE.read_text()
        assert 'terminal failure' not in text and 'No valid checkpoint HEAD' in text
        watch.publish_view(items['FAILED']); text = watch.LIVE.read_text()
        assert 'terminal failure; model quality remains unknown' in text and '0 / 256' not in text
    finally:
        watch.ARCHIVE, watch.LIVE = original_archive, original_live
checks.append('temporary convenience-view fixture never labels missing state as a failure or missing rows as zero')

remote['bound_job'] = lambda *_: {'synthetic_only': True}
remote['scheduler'] = lambda *_: {'observed_state': 'FAILED'}
remote['tail'] = lambda name: {'path': name, 'exists': False}
remote['metadata'] = lambda name, *args: {'path': name, 'exists': False}
value = remote['observe'](job, 'evaluate', 'a'*64, 'b'*64)
assert value['progress']['checkpoint_completed_records'] is None and value['progress']['expected_checkpoint_records'] == 256
assert value['quality_claim'] is None and value['proofs_independently_verified'] is False
checks.append('actual observer projection preserves absent files and no-proof claims without manufacturing checkpoints')


def functions(source):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}


old_observer = (OLD/'observe-retention-job-01.py').read_bytes()
old_tree = ast.parse(old_observer)
old_program = ast.literal_eval(next(node.value for node in old_tree.body if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == 'PROGRAM' for target in node.targets)))
for name in ('directory', 'read_file', 'command', 'scheduler', 'tail', 'metadata'):
    assert functions(old_program)[name] == functions(observer.PROGRAM)[name]
assert functions(old_observer)['exchange'] == functions(sources[names[1]])['exchange']
assert functions((OLD/'transfer-retention-bootstrap-01.py').read_bytes())['bounded'] == functions((A/'transfer-evaluation-recovery-01.py').read_bytes())['bounded']
old_namespace = {'__name__': 'old_observer_constants_only', '__file__': str(OLD/'observe-retention-job-01.py')}
exec(compile(old_observer, str(OLD/'observe-retention-job-01.py'), 'exec'), old_namespace)
assert observer.LIMITS == old_namespace['LIMITS']
assert watch.MAX_WALL == 7500 and watch.MAX_OBSERVATIONS == 125 and watch.INTERVAL == 60
assert len(watch.canonical(watch.observation_index([items['FAILED']]*125))) < 65536-4096
checks.append('original SSH/process/log-tail supervisors are AST-identical and watcher compact index remains bounded')

assert all((A/name).read_bytes() == raw for name, raw in sources.items())
usage = resource.getrusage(resource.RUSAGE_SELF)
observed = {'cpu_seconds': usage.ru_utime+usage.ru_stime, 'wall_seconds': time.monotonic()-STARTED, 'rss_bytes': usage.ru_maxrss}
assert observed['cpu_seconds'] < 10 and observed['wall_seconds'] < 15 and observed['rss_bytes'] < 128*1024**2
result = {'schema': 'peano-hydra-retention-evaluation-recovery-operation-pure-checks-v1', 'status': 'passed',
    'check_groups': len(checks), 'checks': checks, 'source_pins': {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        for name, raw in sources.items()}, 'observed': observed,
    'limits': {'cpu_seconds': 10, 'wall_seconds': 15, 'rss_bytes': 128*1024**2, 'output_bytes': 65536},
    'real_launcher_observer_watcher_invoked': False, 'scheduler_network_native_model_work_performed': False,
    'synthetic_records_are_not_real_submission_observation_or_quality_evidence': True}
body = (json.dumps(result, sort_keys=True, indent=2)+'\n').encode()
path = A/'recovery-operation-checks-01.json'
fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, 'wb') as stream:
    stream.write(body); stream.flush(); os.fsync(stream.fileno())
signal.alarm(0)
print(json.dumps({'status': 'passed', 'groups': len(checks), 'receipt': str(path), 'sha256': hashlib.sha256(body).hexdigest(),
                  'observed': observed}, sort_keys=True))
