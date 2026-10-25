#!/usr/bin/env python3
"""Tiny syntax/resource-arithmetic/audit-policy fixtures; no replay or owner.

The audit hook is installed into a fixture sys object, never the interpreter.
No helper main/worker, source admission, native proof, model or process runs.
"""
import time
STARTED = time.monotonic()
import argparse
import ast
import hashlib
import importlib.abc
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
from types import SimpleNamespace

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
HELPER = ARCHIVE / 'verify-retention-checkpoint-local-01.py'
UTILITY = ARCHIVE.parents[1] / 'artifacts/hydra-model-test-2026-08-30/verify-diagnostic-local-02.py'
UTILITY_SHA = '7df14454b45ffd8b85d8d2ed4903fd968c0decc642b4b9e35f7255c6fa8bd155'
OUTPUT = ARCHIVE / 'retention-verifier-helper-checks-01.json'


def require(value, message):
    if not value: raise ValueError(message)


def selected(tree, names, namespace):
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    require({node.name for node in nodes} == set(names), 'fixture selected unknown function')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<pure-selected-verifier-fixture>', 'exec'), namespace)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--expected-helper-sha256', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode, 'isolated uncached fixture required')
    resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixture wall cap')))
    signal.setitimer(signal.ITIMER_REAL, 20)
    raw, utility = HELPER.read_bytes(), UTILITY.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == args.expected_helper_sha256
        and hashlib.sha256(utility).hexdigest() == UTILITY_SHA, 'literal reviewed source/utility pin changed')
    tree, old_tree = ast.parse(raw), ast.parse(utility)
    compile(raw, str(HELPER), 'exec')
    tested = ['full-helper-syntax-without-import-or-invocation']
    namespace = {'require': require, 'math': math}
    selected(old_tree, {'whole_cpu_lower_bound'}, namespace)
    cpu = namespace['whole_cpu_lower_bound']
    require(cpu(20, 570, 500, 510.5) == 600.5, 'post-supervision CPU tail escaped600-second boundary')
    require(cpu(10, 400, 300, 315) == 425 and cpu(10, 400, 450, 455) == 455,
            'CPU observation dominance or tail arithmetic changed')
    rejected = False
    try: cpu(10, 400, 450, 449)
    except ValueError: rejected = True
    require(rejected, 'decreasing cumulative CPU accepted')
    tested.append('reviewed-whole-CPU-tail-and-invalid-counter-fixtures')
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in ('LIMITS', 'PROOF_LIMITS') for target in node.targets):
            for target in node.targets:
                if isinstance(target, ast.Name): constants[target.id] = eval(compile(ast.Expression(node.value), '<numeric-limits>', 'eval'), {'__builtins__': {}})
    require(constants['PROOF_LIMITS'] == {'wall_seconds': 45, 'cpu_seconds': 30, 'rss_bytes': 1024**3, 'output_bytes': 1024**2}
        and constants['LIMITS']['whole_cpu_seconds'] == 600 and constants['LIMITS']['whole_wall_seconds'] == 900
        and constants['LIMITS']['controller_cpu_seconds'] == 180
        and constants['LIMITS']['sampled_parent_and_owned_tree_rss_bytes'] == 2 * 1024**3,
        'separate whole256-record and original proof caps differ')
    tested.append('new-whole-envelope-keeps-original-per-proof-and-controller-caps')
    frozen = ARCHIVE.parents[1] / '_deploy/hydra-retention-execution-20260830'
    python = Path('/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
    hooks = []
    fixture_sys = SimpleNamespace(modules={}, meta_path=[], addaudithook=hooks.append)
    policy = {'require': require, 'sys': fixture_sys, 'importlib': __import__('importlib'), 'FROZEN': frozen, 'PYTHON': python}
    selected(tree, {'install_worker_guards'}, policy)
    failures, counts = policy['install_worker_guards'](['training/a.py'])
    require(len(hooks) == 1 and len(fixture_sys.meta_path) == 1, 'audit policy did not register only fixture hooks')
    audit = hooks[0]
    proof = (str(python), str(frozen / 'scripts/hydra_bounded_exec.py'), '--cpu-seconds', '30',
        '--rss-bytes', str(1024**3), '--', str(python), str(frozen / 'scripts/eval_peano_hydra_capacity.py'), '--replay-worker')
    for command, cwd in (
        (('git', '-C', str(frozen), 'status', '--porcelain', '--untracked-files=all'), None),
        (('/bin/ps', '-axo', 'pid=,pgid=,rss='), None), (proof, frozen)):
        audit('subprocess.Popen', (command[0], command, cwd, {}))
    require(counts == {'git_reads': 1, 'native_guard_processes': 1, 'native_process_samplers': 1}
        and not any(failures.values()), 'exact metadata/native sampler command policy rejected reviewed shapes')
    tested.append('exact-read-only-Git-ps-original-native-command-audit-fixtures')
    rejected = 0
    altered = list(proof); altered[3] = '31'
    for event, values in (
        ('subprocess.Popen', ('ssh', ('ssh', 'host'), None, {})),
        ('subprocess.Popen', ('/bin/sh', ('/bin/sh', '-c', 'true'), None, {})),
        ('subprocess.Popen', (str(python), tuple(altered), frozen, {})),
        ('subprocess.Popen', (str(python), proof, ARCHIVE, {})),
        ('socket.__new__', (None, 10, 1, 0)), ('socket.connect', (None, ('example.invalid', 443))),
        ('import', ('torch', None)), ('import', ('transformers', None))):
        try: audit(event, values)
        except (RuntimeError, ValueError): rejected += 1
    require(rejected == 8 and all(failures.values()), 'foreign command/network/framework policy failed open')
    tested.append('all-eight-foreign-command-limit-network-framework-fixtures-rejected')
    proof_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and node.func.attr == 'verify_result']
    require(len(proof_nodes) == 1 and any(keyword.arg == 'replay' and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is False for keyword in proof_nodes[0].keywords),
        'complete report validator must not perform a duplicate native replay round')
    require(not any(isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute)
        and target.attr in ('ROOT', 'Limits', 'REPLAY_LIMITS', 'run_bounded', 'verify_checkpoint') for target in node.targets)
        for node in ast.walk(tree)), 'caller mutates a pinned original execution guard')
    tested.append('source-never-replaces-original-guards-or-runs-duplicate-report-replay')
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_used = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    peak = int(own.ru_maxrss if sys.platform == 'darwin' else own.ru_maxrss * 1024)
    require(cpu_used < 10 and time.monotonic() - STARTED < 20 and peak < 256 * 1024**2, 'fixture resource cap')
    result = {'schema': 'peano-hydra-retention-verifier-helper-pure-checks-v1', 'status': 'passed',
        'helper_sha256': args.expected_helper_sha256, 'utility_sha256': UTILITY_SHA,
        'checks': tested, 'check_count': len(tested), 'cpu_seconds': cpu_used,
        'wall_seconds': time.monotonic() - STARTED, 'peak_rss_bytes': peak,
        'whole_caller_invoked': False, 'process_supervision_executed': False,
        'scientific_API_invoked': False, 'native_proofs_executed': False, 'model_loaded': False,
        'network_contacted': False, 'gpu_allocated': False, 'original_sources_modified': False}
    rendered = json.dumps(result, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    fd = os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(rendered); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': 'passed', 'checks': len(tested), 'output': str(OUTPUT),
        'bytes': len(rendered), 'sha256': hashlib.sha256(rendered).hexdigest()}, sort_keys=True))
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
