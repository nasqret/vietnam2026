#!/usr/bin/env python3
"""Bounded metadata/syntax checks only; no model, origin auth or proof replay."""
import ast
from datetime import datetime, timezone
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

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
HELPER = ARCHIVE / 'verify-diagnostic-local-01.py'
OUTPUT = ARCHIVE / 'local-verification-helper-checks-01.json'
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('metadata checks exceeded 20 seconds')))
signal.alarm(20)
raw = HELPER.read_bytes()
source_sha = hashlib.sha256(raw).hexdigest()
tree = ast.parse(raw, feature_version=(3, 11))
checks = {'python311_syntax': True}
forbidden_calls = {'CheckedRequest', 'execute_evaluation', 'authenticate_origin', 'setattr'}
called = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
          for node in ast.walk(tree) if isinstance(node, ast.Call)
          and isinstance(node.func, (ast.Attribute, ast.Name))}
assert not (called & forbidden_calls)
checks['no_constructed_checked_request_or_model_or_origin_auth_calls'] = True
spec = importlib.util.spec_from_file_location('_local_verification_helper_check', HELPER)
helper = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helper
spec.loader.exec_module(helper)
checks['stdlib_only_helper_import'] = not any(name.startswith(('training.', 'peano_lab')) for name in sys.modules)
assert checks['stdlib_only_helper_import']

with tempfile.TemporaryDirectory(prefix='hydra-local-verification-metadata-') as temporary:
    root = Path(temporary).resolve()
    value = root / 'metadata.json'
    value.write_bytes(b'{"metadata_only":true}\n')
    identity, body = helper.fingerprint(value, retain=True)
    assert identity == {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    assert helper.read_json(value, identity['sha256'])[0] == {'metadata_only': True}
    for raw_bad in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'[]'):
        value.write_bytes(raw_bad)
        try:
            helper.read_json(value, hashlib.sha256(raw_bad).hexdigest())
        except ValueError:
            pass
        else:
            raise AssertionError('bad metadata accepted')
    checks['duplicate_nonfinite_nonobject_metadata_rejected'] = True
    alias = root / 'alias.json'
    alias.symlink_to(value)
    try:
        helper.fingerprint(alias)
    except ValueError:
        pass
    else:
        raise AssertionError('symbolic link input accepted')
    checks['symlink_inputs_rejected'] = True
    value.write_bytes(b'{}\n')
    try:
        helper.worker(value, hashlib.sha256(value.read_bytes()).hexdigest())
    except ValueError as error:
        assert 'live owner reservation' in str(error)
    else:
        raise AssertionError('unowned worker accepted')
    checks['unowned_worker_rejected_before_native_import'] = True

execution = helper.check_execution(deadline=STARTED + 20)
diagnostic, launch, evaluation, bridge = helper.modules()
checks['all877_frozen_execution_file_pins_verified'] = execution['source_files'] == 877
checks['genuine_modules_loaded_from_frozen612_without_model_import'] = True
assert evaluation.capacity.REPLAY_LIMITS.to_dict() == helper.PROOF_LIMITS
checks['unchanged_original_per_proof_caps'] = True
# This constructs portable request metadata only, never a CheckedRequest or
# authenticated handle. No receipt loader or proof validator is invoked.
with tempfile.TemporaryDirectory(prefix='hydra-portable-request-metadata-') as temporary:
    root = Path(temporary).resolve()
    identity = {'schema': bridge.REQUEST_SCHEMA, 'source_manifest_sha256': 'a' * 64,
        'source_commit': 'b' * 40, 'preparation_relative_path': '_deploy/original/preparation',
        'preparation_manifest_sha256': 'c' * 64, 'adapter_manifest_sha256': 'd' * 64,
        'authority_profile': bridge.AUTHORITY_PROFILE}
    locations = {'source_root': str(root / 'source'), 'source_manifest': str(root / 'source-manifest.json'),
                 'adapter_manifest': str(root / 'first-model/manifest.json')}
    first = bridge._request(identity, locations)
    second = bridge._request(identity, dict(locations, adapter_manifest=str(root / 'second-model/manifest.json')))
    a = evaluation.OriginReference(first, root / 'receipt.json', 'e' * 64)
    b = evaluation.OriginReference(second, root / 'receipt-copy.json', 'e' * 64)
    assert a.to_dict() == b.to_dict() and first.locations() != second.locations()
checks['existing_originreference_identity_excludes_explicit_physical_locations'] = True
assert not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules)
assert HELPER.read_bytes() == raw
usage = resource.getrusage(resource.RUSAGE_SELF)
assert usage.ru_maxrss < 256 * 1024**2
assert usage.ru_utime + usage.ru_stime < 10 and time.monotonic() - STARTED < 20
result = {'schema': 'peano-hydra-local-verification-helper-static-checks-v1', 'status': 'passed',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'helper_sha256': source_sha,
    'checks': checks, 'execution_source': execution,
    'limits': {'cpu_seconds': 10, 'wall_seconds': 20, 'checked_peak_rss_bytes': 256 * 1024**2},
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime,
                  'wall_seconds': time.monotonic() - STARTED, 'maxrss_bytes': usage.ru_maxrss},
    'original_origin_authenticated': False, 'native_proofs_replayed': 0, 'model_loaded': False,
    'scheduler_or_network_called': False, 'human_approval_created': False,
    'whole_process_tree_supervision_executed': False,
    'limitation': 'Static/metadata checks only; actual saved-run verification remains pending.'}
helper.write_new(OUTPUT, result)
signal.alarm(0)
print(json.dumps(result, sort_keys=True, allow_nan=False))
