"""Narrow source/schema checks; never build, prepare, send, or receive a run."""
import ast
import copy
import hashlib
import json
import resource
import signal
import time
import types
from pathlib import Path

START = time.monotonic()
BASE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
HERE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
signal.alarm(15)


def read(name, expected):
    raw = name.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    return raw


old_receiver = read(BASE / 'transfer-retention-bootstrap-remote-01.py',
    '40d8391d2d770e509470c81c7a5fe21f0e7ec3a80048e4b70fa9cb0059e6edc2')
old_sender = read(BASE / 'transfer-retention-bootstrap-01.py',
    '5c8513abd6e4f9f94321a6fa3a7f45290fee3fba442020e1975921aa5a3694a5')
receiver = read(HERE / 'transfer-evaluation-recovery-remote-01.py',
    '50ed89b1f564e179e02a64aa881c099f98c869b475c2a07a8df8733a6078a3a8')
sender = read(HERE / 'transfer-evaluation-recovery-01.py',
    '1ca738064b8be3526dec4ec3b301b8ecaec9b9580344ab32692a56f61f658618')


def nodes(raw):
    return {node.name: ast.dump(node, include_attributes=False)
        for node in ast.parse(raw, feature_version=(3, 9)).body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


receiver_primitives = ('require', 'utc', 'canonical', 'sha', 'decode', 'relative',
    'directory', 'identity', 'Tree', 'exact', 'create_directories',
    'write_stream_file', 'descriptor', 'LimitedBundle', 'tar_text', 'tar_octal',
    'tar_member', 'consume_tar')
sender_primitives = ('read_file', 'pin', 'source_environment', 'bounded',
    'bundle_open', 'HashReader', 'construct_bundle')
for before, after, selected in ((old_receiver, receiver, receiver_primitives),
                              (old_sender, sender, sender_primitives)):
    left, right = nodes(before), nodes(after)
    assert all(left[name] == right[name] for name in selected)

r = types.ModuleType('_checked_recovery_transfer_receiver')
r.__file__ = str(HERE / 'transfer-evaluation-recovery-remote-01.py')
exec(compile(receiver, r.__file__, 'exec'), r.__dict__)
old = types.ModuleType('_original_transfer_constants')
old.__file__ = str(BASE / 'transfer-retention-bootstrap-remote-01.py')
exec(compile(old_receiver, old.__file__, 'exec'), old.__dict__)
assert r.LIMITS == old.LIMITS
assert (r.MAX_FILES, r.MAX_FILE, r.MAX_TOTAL, r.MAX_BUNDLE, r.MAX_JSON,
        r.MAX_FREEZE, r.MAX_HEADER, r.MAX_PREFIX) == (
    old.MAX_FILES, old.MAX_FILE, old.MAX_TOTAL, old.MAX_BUNDLE, old.MAX_JSON,
    old.MAX_FREEZE, old.MAX_HEADER, old.MAX_PREFIX)

# In-memory schema fixtures only. These are never written as a run, freeze,
# approval, transfer plan, or admission receipt.
item = {'bytes': 1, 'sha256': 'a' * 64, 'mode': '0644'}
sources = {name: dict(item) for name in ('training/example.py', r.FREEZE_RECEIPT, r.ORIGIN_MANIFEST)}
payloads = {r.PACKAGE + '/' + name: dict(item) for name in (
    'resource-request.json', 'approval.json', 'inputs.json', 'admission.json',
    'evaluate-request.json', 'preflight.json', 'evaluation-plan.json')}
payloads[r.AUTHORITY] = {'bytes': 2107, 'sha256': r.DIRECTIVE_SHA, 'mode': '0600'}


def refreshed(plan):
    plan['selected_files'] = {**plan['source_files'], **plan['bootstrap_files']}
    for key in ('source_files', 'bootstrap_files', 'selected_files'):
        plan[key + '_sha256'] = r.sha(r.canonical(plan[key]))
    plan['file_count'] = len(plan['selected_files'])
    plan['selected_uncompressed_bytes'] = sum(x['bytes'] for x in plan['selected_files'].values())
    plan['maximum_installed_files'] = plan['file_count'] + 2
    plan['maximum_installed_bytes'] = plan['selected_uncompressed_bytes'] + r.MAX_PROVENANCE + r.MAX_JSON
    return plan


plan = refreshed({
    'schema': 'peano-hydra-retention-evaluation-recovery-transfer-plan-v1',
    'status': 'prepared-evaluation-recovery-local-only', 'profile': r.PROFILE,
    'run_id': r.RUN_ID, 'source_root': r.LOCAL_ROOT, 'source_commit': 'a' * 40,
    'destination_directory': r.REMOTE_ROOT, 'destination_host': r.HOST,
    'freeze_receipt': {'path': r.FREEZE_RECEIPT, 'bytes': 1, 'sha256': 'a' * 64},
    'source_files': sources, 'bootstrap_files': payloads,
    'bundle': {'path': r.ARCHIVE_ROOT + '/' + r.BUNDLE_NAME, 'bytes': 1, 'sha256': 'b' * 64},
    'directive_sha256': r.DIRECTIVE_SHA, 'limits': r.LIMITS,
    'model_weights_in_bundle': False, 'resource_request_in_bundle': True,
    'approval_in_bundle': True, 'gpu_job_submitted': False,
    'native_or_model_work_performed': False, 'remote_transfer_performed': False,
    'automatic_retry': False, 'resume': False,
})


def validate(value):
    raw = r.canonical(value)
    return r.validate_plan(raw, r.sha(raw))


def rejected(value):
    try:
        validate(value)
    except ValueError:
        return True
    raise AssertionError('invalid transfer scope was accepted')


assert validate(plan) == plan
checks = ['python39-syntax-and-preserved-primitives', 'all-original-resource-caps-unchanged',
          'final-controls-required-in-new-transfer']
for field in ('resource_request_in_bundle', 'approval_in_bundle'):
    bad = copy.deepcopy(plan); bad[field] = False; assert rejected(bad)
for name in ('admission.json', 'preflight.json', 'resource-request.json', 'approval.json'):
    bad = copy.deepcopy(plan); del bad['bootstrap_files'][r.PACKAGE + '/' + name]
    assert rejected(refreshed(bad))
checks.append('missing-actual-admission-preflight-or-controls-rejected')
for name in ('train-request.json', 'token-preflight.json', 'adapter.safetensors'):
    bad = copy.deepcopy(plan); bad['bootstrap_files'][r.PACKAGE + '/' + name] = dict(item)
    assert rejected(refreshed(bad))
checks.append('training-controls-and-model-weights-rejected')
for field, value in (('run_id', 'retention-pilot-v1'), ('destination_directory', old.REMOTE_ROOT),
                     ('automatic_retry', True), ('gpu_job_submitted', True)):
    bad = copy.deepcopy(plan); bad[field] = value; assert rejected(bad)
checks.append('old-run-destination-retry-or-compute-claims-rejected')

s = types.ModuleType('_checked_recovery_transfer_sender')
s.__file__ = str(HERE / 'transfer-evaluation-recovery-01.py')
exec(compile(sender, s.__file__, 'exec'), s.__dict__)
prepared = s.prepared_record(plan, r.canonical(plan), {'commit': 'a' * 40, 'clean': True}, {})
assert prepared['resource_request_present'] is True and prepared['approval_present'] is True
assert prepared['job_submitted'] is False and prepared['native_or_model_work_performed'] is False
assert prepared['network_contacted'] is False
checks.append('prepared-metadata-truthfully-records-present-controls-without-execution')

usage = resource.getrusage(resource.RUSAGE_SELF)
result = {'schema': 'peano-hydra-retention-evaluation-recovery-transfer-helper-checks-v1',
    'status': 'passed', 'checks': checks, 'check_groups': len(checks),
    'receiver_sha256': r.sha(receiver), 'sender_sha256': r.sha(sender),
    'unchanged_receiver_primitives': receiver_primitives,
    'unchanged_sender_primitives': sender_primitives,
    'fixtures_only': True, 'build_prepare_send_receive_invoked': False,
    'actual_run_receipt_created': False, 'network_contacted': False,
    'model_or_native_work_performed': False, 'gpu_allocated': False,
    'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - START,
    'peak_rss_bytes': usage.ru_maxrss}
raw = r.canonical(result) + b'\n'
with (HERE / 'transfer-helper-checks-01.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'status': 'passed', 'check_groups': len(checks), 'receipt_bytes': len(raw),
                  'receipt_sha256': r.sha(raw)}, sort_keys=True))
signal.alarm(0)
