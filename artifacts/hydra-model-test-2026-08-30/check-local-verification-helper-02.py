#!/usr/bin/env python3
"""Arithmetic-only regression plus syntax; no source/model/origin/proof binding."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import sys
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
HELPER = ARCHIVE / 'verify-diagnostic-local-02.py'
OLD_HELPER = ARCHIVE / 'verify-diagnostic-local-01.py'
OUTPUT = ARCHIVE / 'local-verification-helper-checks-02.json'
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('arithmetic checks exceeded 10 seconds')))
signal.alarm(10)
raw, old_raw = HELPER.read_bytes(), OLD_HELPER.read_bytes()
assert hashlib.sha256(old_raw).hexdigest() == 'b8dcb493b52c6c5f669b870485b8e6612b04d96cd56b54db484816090f64bc4b'
tree = ast.parse(raw, feature_version=(3, 11))
old_tree = ast.parse(old_raw, feature_version=(3, 11))
functions = {node.name: ast.dump(node, include_attributes=False)
             for node in tree.body if isinstance(node, ast.FunctionDef)}
old_functions = {node.name: ast.dump(node, include_attributes=False)
                 for node in old_tree.body if isinstance(node, ast.FunctionDef)}
assert set(functions) == set(old_functions) | {'whole_cpu_lower_bound'}
assert all(functions[name] == body for name, body in old_functions.items() if name != 'supervise')
spec = importlib.util.spec_from_file_location('_local_verification_arithmetic_check', HELPER)
helper = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helper
spec.loader.exec_module(helper)
assert not any(name.startswith(('training.', 'peano_lab')) for name in sys.modules)
assert helper.WHOLE_LIMITS == {'wall_seconds': 300, 'cpu_seconds': 180,
    'rss_bytes': 2 * 1024**3, 'output_bytes': 64 * 1024**2}
assert helper.PROOF_LIMITS == {'wall_seconds': 45, 'cpu_seconds': 30,
    'rss_bytes': 1024**3, 'output_bytes': 1024**2}
cases = [
    {'prefix': 0.5, 'supervised': 179.0, 'returned': 99.5, 'current': 100.5, 'expected': 180.5},
    {'prefix': 0.5, 'supervised': 10.0, 'returned': 10.0, 'current': 12.0, 'expected': 12.5},
    {'prefix': 0.5, 'supervised': 5.0, 'returned': 10.0, 'current': 12.0, 'expected': 12.0},
]
for case in cases:
    assert helper.whole_cpu_lower_bound(case['prefix'], case['supervised'], case['returned'], case['current']) == case['expected']
assert cases[0]['expected'] >= helper.WHOLE_LIMITS['cpu_seconds']
for invalid in ((0.5, 10.0, 12.0, 10.0), (True, 10.0, 12.0, 13.0),
                (0.5, float('nan'), 12.0, 13.0), (0.5, float('inf'), 12.0, 13.0)):
    try:
        helper.whole_cpu_lower_bound(*invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid CPU accounting accepted')
assert not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules)
assert HELPER.read_bytes() == raw
usage = resource.getrusage(resource.RUSAGE_SELF)
assert usage.ru_maxrss < 256 * 1024**2
assert usage.ru_utime + usage.ru_stime < 10 and time.monotonic() - STARTED < 10
result = {'schema': 'peano-hydra-local-verification-helper-arithmetic-checks-v1', 'status': 'passed',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'helper_sha256': hashlib.sha256(raw).hexdigest(),
    'superseded_helper_sha256': hashlib.sha256(old_raw).hexdigest(),
    'earlier_static_metadata_checks_sha256': 'a3b0ac0d80de8c969c55ffd1074f7ac9a7384b24f26c1e9a1afd54d50a54aa74',
    'python311_syntax': True, 'worker_metadata_origin_and_replay_functions_unchanged': True,
    'original_resource_caps_unchanged': True, 'arithmetic_cases': cases,
    'four_invalid_cpu_inputs_rejected': True, 'no_native_or_model_imports': True,
    'limits': {'cpu_seconds': 10, 'wall_seconds': 10, 'checked_peak_rss_bytes': 256 * 1024**2},
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime,
        'wall_seconds': time.monotonic() - STARTED, 'maxrss_bytes': usage.ru_maxrss},
    'original_origin_authenticated': False, 'native_proofs_replayed': 0, 'model_loaded': False,
    'source_or_plan_binding_rerun': False, 'scheduler_or_network_called': False,
    'whole_process_tree_supervision_executed': False,
    'limitation': 'Arithmetic/syntax checks only; actual saved-run verification remains pending.'}
helper.write_new(OUTPUT, result)
signal.alarm(0)
print(json.dumps(result, sort_keys=True, allow_nan=False))
