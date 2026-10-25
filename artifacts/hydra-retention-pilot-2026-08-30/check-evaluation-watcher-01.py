#!/usr/bin/env python3
"""Narrow syntax and negative metadata checks; never invoke the watcher."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import resource
import signal
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
HELPER = ARCHIVE / 'watch-retention-evaluation-01.py'
OUTPUT = ARCHIVE / 'evaluation-watcher-helper-checks-01.json'


def require(value, message):
    if not value: raise ValueError(message)


def rejected(function, *args):
    try: function(*args)
    except (ValueError, KeyError, TypeError): return
    raise ValueError('negative fixture unexpectedly admitted an invalid evaluation launch')


def main():
    began = time.monotonic()
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--expected-helper-sha256', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (10, 11)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('pure watcher check wall cap')))
    signal.alarm(20)
    raw = HELPER.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == args.expected_helper_sha256, 'candidate watcher pin changed')
    tree = ast.parse(raw); compile(raw, str(HELPER), 'exec')
    checks = ['complete-candidate-syntax-without-main-or-observer-invocation']
    functions = {'require', 'canonical', 'decode', 'validate_submit'}
    constants = {'LAUNCHER_SHA', 'COMMIT', 'APPROVAL', 'HEADER', 'PROFILE', 'RUN_ID'}
    selected = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in functions: selected.append(node)
        if isinstance(node, ast.Assign):
            names = {item.id for target in node.targets for item in ast.walk(target) if isinstance(item, ast.Name)}
            if names and names <= constants: selected.append(node)
    namespace = {'json': json, 'hashlib': hashlib, 're': re}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<watcher-pure-launch-rejections>', 'exec'), namespace)
    require(functions | constants <= set(namespace), 'pure fixture omitted required source functions/constants')
    train_raw = (ARCHIVE / 'launch-train-submit-01.json').read_bytes()
    train = json.loads(train_raw)
    rejected(namespace['validate_submit'], train, train['result']['job_id'])
    checks.append('actual-successful-training-submit-cannot-be-adopted-as-evaluation')
    for changes in ({'status': 'failed'}, {'mode': 'test-only'}, {'remote_command_started': False},
                    {'helper_sha256': '0' * 64}, {'automatic_retry': True}):
        record = copy.deepcopy(train)
        record['stage'] = 'evaluate'
        record.update(changes)
        rejected(namespace['validate_submit'], record, train['result']['job_id'])
    # Merely relabeling the top-level stage cannot turn the original7200-second
    # training result into the required3600-second released evaluation result.
    relabeled = copy.deepcopy(train); relabeled['stage'] = 'evaluate'
    rejected(namespace['validate_submit'], relabeled, train['result']['job_id'])
    checks.append('six-failed-test-only-foreign-helper-retry-relabel-fixtures-rejected')
    rejected(namespace['decode'], b'{"stage":"train","stage":"evaluate"}')
    rejected(namespace['decode'], b'{"wall":NaN}')
    checks.append('duplicate-and-nonfinite-input-metadata-rejected')
    main_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    ranges = [node for node in ast.walk(main_node) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == 'range']
    require(len(ranges) == 1 and [ast.literal_eval(item) for item in ranges[0].args] == [3, 128],
            'watcher consumed initial observation slots or enlarged125-slot reservation')
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple):
            names = [part.id for part in node.targets[0].elts]
            if names == ['MAX_WALL', 'MAX_OBSERVATIONS', 'INTERVAL']:
                values = dict(zip(names, ast.literal_eval(node.value)))
    require(values == {'MAX_WALL': 7500, 'MAX_OBSERVATIONS': 125, 'INTERVAL': 60}, 'watch limits changed')
    commands = [node.value for node in ast.walk(main_node) if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'command' for target in node.targets)]
    require(len(commands) == 1 and isinstance(commands[0], ast.List)
        and any(isinstance(item, ast.Constant) and item.value == 'evaluate' for item in commands[0].elts)
        and not any(isinstance(item, ast.Constant) and item.value == 'train' for item in commands[0].elts),
        'bounded observer stage changed')
    source = raw.decode()
    require("LIVE = ARCHIVE / 'EVALUATION_LIVE_STATUS.md'" in source
        and "'watch-evaluation-started-01.json'" in source and "'watch-evaluation-result-01.json'" in source
        and "'retention-evaluate-observation-" in source,
        'evaluation observation/view/receipts are not disjoint from training')
    checks.append('original-time-count-interval-and-separate-evaluation-only-output-scope')
    own = resource.getrusage(resource.RUSAGE_SELF)
    measured = {'cpu_seconds': own.ru_utime + own.ru_stime, 'wall_seconds': time.monotonic() - began,
        'peak_rss_bytes': int(own.ru_maxrss if sys.platform == 'darwin' else own.ru_maxrss * 1024)}
    require(measured['cpu_seconds'] < 10 and measured['wall_seconds'] < 20 and measured['peak_rss_bytes'] < 256 * 1024**2,
            'pure check resource cap')
    result = {'schema': 'peano-hydra-retention-evaluation-watch-pure-checks-v1', 'status': 'passed',
        'helper_sha256': args.expected_helper_sha256, 'actual_training_receipt_sha256': hashlib.sha256(train_raw).hexdigest(),
        'check_count': len(checks), 'checks': checks, 'measurements': measured,
        'watcher_main_invoked': False, 'observer_invoked': False, 'evaluation_submission_fabricated': False,
        'network_contacted': False, 'scheduler_called': False, 'model_loaded': False, 'native_proofs_executed': False}
    rendered = json.dumps(result, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    with OUTPUT.open('xb') as stream: stream.write(rendered)
    print(json.dumps({'status': 'passed', 'checks': len(checks), 'output': str(OUTPUT),
        'bytes': len(rendered), 'sha256': hashlib.sha256(rendered).hexdigest()}, sort_keys=True))
    signal.alarm(0)


if __name__ == '__main__':
    main()
