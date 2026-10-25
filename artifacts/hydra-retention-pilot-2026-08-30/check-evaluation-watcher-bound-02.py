#!/usr/bin/env python3
"""Prove the final125-observation index fits64KiB, without running a watcher.

Only the actual final dictionary expression and pure projection are evaluated
on in-memory maximum-length strings. No observation or launch is fabricated
on disk; the output is solely a syntax/serialization-bound check receipt.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import time
from types import SimpleNamespace

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
HELPER = ARCHIVE / 'watch-retention-evaluation-01.py'
OUTPUT = ARCHIVE / 'evaluation-watcher-bound-checks-02.json'


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--expected-helper-sha256', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (10, 11)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('pure serialization check wall cap')))
    signal.alarm(20)
    started = time.monotonic()
    raw = HELPER.read_bytes(); tree = ast.parse(raw); compile(raw, str(HELPER), 'exec')
    if hashlib.sha256(raw).hexdigest() != args.expected_helper_sha256: raise ValueError('watcher source pin changed')
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
        and node.name in {'require', 'canonical', 'observation_index'}]
    namespace = {'json': json, 'MAX_OBSERVATIONS': 125}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pure-final-index>', 'exec'), namespace)
    require, canonical = namespace['require'], namespace['canonical']
    item = {'job_id': '9' * 20, 'observation_file': 'retention-evaluate-observation-127.json',
        'observation_sha256': 'f' * 64, 'state': 'X' * 64, 'observed_at_utc': '9999-12-31T23:59:59Z',
        'elapsed_seconds': 604800, 'checkpoint_committed_records': None, 'expected_checkpoint_records': 256,
        'head_counter_only_not_verified_rows': True, 'proofs_verified': False, 'quality_claim': None}
    # Any descriptor accepted by launch_binding is <=4096 canonical bytes.
    # This maximum-length placeholder is only a serialization fixture.
    launched = {'padding': ''}
    launched['padding'] = 'x' * (4096 - len(canonical(launched)))
    require(len(canonical(launched)) == 4096, 'maximum launch descriptor fixture bound')
    result_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == 'write_new' and len(node.args) == 2
        and isinstance(node.args[1], ast.Dict)
        and any(isinstance(key, ast.Constant) and key.value == 'observations' for key in node.args[1].keys)]
    require(len(result_calls) == 1, 'one actual final watcher result expression required')
    namespace.update(args=SimpleNamespace(job_id='9' * 20, expected_helper_sha256='f' * 64),
        launched=launched, observations=[item] * 125, error='\x00' * 2048,
        SCHEMA='peano-hydra-retention-read-only-evaluation-watch-v1', OBSERVER_SHA='f' * 64,
        STARTED=0, MAX_WALL=7500, time=SimpleNamespace(monotonic=lambda: 7500.123456789012))
    result = eval(compile(ast.Expression(result_calls[0].args[1]), '<actual-final-result-expression>', 'eval'), namespace)
    rendered = canonical(result) + b'\n'
    # Reserve64 extra bytes for any wider finite wall-clock representation.
    upper = len(rendered) + 64
    require(upper <= 65536 and len(result['observations']) == 125
        and all(set(entry) == {'observation_file', 'observation_sha256', 'state', 'observed_at_utc',
            'elapsed_seconds', 'checkpoint_committed_records'} for entry in result['observations']),
        'declared maximum does not fit unchanged64KiB result cap')
    require(result['observations_are_compact_index_of_unchanged_original_files'] is True
        and result['proofs_verified'] is False and result['quality_claim'] is None,
        'bounded index changed the observation-only evidence scope')
    rejected = False
    try: namespace['observation_index']([item] * 126)
    except ValueError: rejected = True
    require(rejected, 'more than125 observations were admitted')
    # Concrete input bounds are enforced in production, not just assumed by
    # the fixture. These deltas do not invoke an observer or scientific API.
    source = raw.decode()
    require("len(state) <= 64" in source and "len(canonical(value)) <= 4096" in source
        and "error = (type(failure).__name__ + ': ' + ' '.join(str(failure).split()))[:2048]" in source,
        'serialized string bounds are not enforced by the actual watcher')
    own = resource.getrusage(resource.RUSAGE_SELF)
    receipt = {'schema': 'peano-hydra-retention-evaluation-watch-result-bound-v1', 'status': 'passed',
        'helper_sha256': args.expected_helper_sha256, 'observations': 125, 'launch_descriptor_bound_bytes': 4096,
        'state_bound_characters': 64, 'error_bound_characters': 2048,
        'error_fixture_uses_maximum_six_byte_JSON_escapes': True,
        'serialized_result_bytes': len(rendered), 'additional_numeric_representation_reserve_bytes': 64,
        'proven_result_upper_bound_bytes': upper, 'unchanged_result_cap_bytes': 65536,
        'margin_bytes': 65536 - upper, 'extra_observation_rejected': rejected,
        'cpu_seconds': own.ru_utime + own.ru_stime, 'wall_seconds': time.monotonic() - started,
        'watcher_invoked': False, 'observer_invoked': False, 'evaluation_submission_fabricated': False,
        'network_contacted': False, 'scheduler_called': False, 'model_loaded': False, 'native_proofs_executed': False}
    encoded = json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    fd = os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': 'passed', 'upper_bound_bytes': upper, 'margin_bytes': 65536-upper,
        'output': str(OUTPUT), 'sha256': hashlib.sha256(encoded).hexdigest()}, sort_keys=True))
    signal.alarm(0)


if __name__ == '__main__':
    main()
