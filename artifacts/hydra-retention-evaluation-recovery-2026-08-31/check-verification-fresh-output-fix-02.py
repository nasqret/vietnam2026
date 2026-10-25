#!/usr/bin/env python3
"""Offline regression using the real frozen output guard and fingerprint API.

Only the changed guard/fingerprint expressions are executed against temporary
fixture files. No scientific binding, verifier/CLI main, proof, model or network
operation is invoked. AST checks retain all other production/helper controls.
"""
import time
STARTED = time.monotonic()
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import tempfile
import types
import unittest

W = Path('/Users/bnaskrecki/codex/peano')
B = W / 'artifacts/hydra-retention-evaluation-recovery-2026-08-31'
F = W / '_deploy/hydra-retention-evaluation-recovery-execution-20260831'
V = B / 'verify-retention-evaluation-recovery-checkpoint-local-01.py'
P = B / 'report-retention-evaluation-recovery-quality-01.py'
VB = B / 'verify-retention-evaluation-recovery-checkpoint-local-01.before-fresh-output-guard-fix-f4fc10fe.py'
PB = B / 'report-retention-evaluation-recovery-quality-01.before-verification-attempt02-59e57b8b.py'
BEFORE = B / 'verification-fresh-output-fix-before-01.json'
GUARD = F / 'training/peano_hydra/corrective_workflow.py'
BASE = W / 'artifacts/hydra-model-test-2026-08-30/verify-diagnostic-local-02.py'
DIFF = B / 'verification-fresh-output-fix-02.diff'
RECEIPT = B / 'verification-fresh-output-fix-checks-02.json'
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
def deadline(*_): raise TimeoutError('offline freshness checks15-second wall limit')
signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 15)


def pin(path):
    h, count = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for raw in iter(lambda: stream.read(65536), b''):
            h.update(raw); count += len(raw)
    return {'bytes': count, 'sha256': h.hexdigest()}


before_sources = {str(path): pin(path) for path in (V, P, VB, PB, GUARD, BASE)}
assert before_sources[str(VB)]['sha256'] == 'f4fc10fea71a3f444af7efcfbe0477b5a3721b6f07750ddf188cc55edcfde8d0'
assert before_sources[str(PB)]['sha256'] == '59e57b8b281a3bbdd58667d4f883c2a301dd26a7d222f2e930e77c6446ff505b'
assert before_sources[str(BASE)]['sha256'] == '7df14454b45ffd8b85d8d2ed4903fd968c0decc642b4b9e35f7255c6fa8bd155'
catalog = json.loads((F / '_deploy/hydra-retention-evaluation-recovery-source.json').read_text())
assert before_sources[str(GUARD)] == {key: catalog['files'][str(GUARD.relative_to(F))][key] for key in ('bytes', 'sha256')}
retained_before = json.loads(BEFORE.read_text())


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.posix_spawn', 'os.exec'):
        raise RuntimeError('offline fixtures cannot run processes or network')
    if event == 'import' and str(args[0]).split('.')[0] in {'torch', 'transformers', 'peft', 'peano_lab', 'tokenizers'}:
        raise RuntimeError('offline fixtures cannot load model/native frameworks')
sys.addaudithook(audit)


def module(path, name):
    item = types.ModuleType(name); item.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), item.__dict__)
    return item


files, base = module(GUARD, 'actual_frozen_output_guard'), module(BASE, 'actual_original_fingerprint')
tree, old_tree = ast.parse(V.read_text()), ast.parse(VB.read_text())
functions = lambda value: {node.name: node for node in value.body if isinstance(node, ast.FunctionDef)}
new, old = functions(tree), functions(old_tree)
dump = lambda value: ast.dump(value, include_attributes=False)
is_guard = lambda node: isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'guard_output'
old_guards = [node for node in old['scientific_join'].body if is_guard(node)]
worker_guards = [node for node in new['worker'].body if is_guard(node)]
post_fingerprint = next(node for node in new['worker'].body if isinstance(node, ast.Expr)
    and isinstance(node.value, ast.Call) and len(node.value.args) == 2
    and isinstance(node.value.args[1], ast.Constant)
    and node.value.args[1].value == 'original checkpoint verification receipt changed during post-replay checks')


def expressions(nodes, values):
    fragment = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes), type_ignores=[]))
    exec(compile(fragment, '<actual-helper-guard-expressions-only>', 'exec'), values)


class Checks(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix='fresh-output-regression-', dir=str(B))
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name); output = root / 'output'; output.mkdir()
        protected = root / 'protected'; protected.mkdir()
        values = {'api': {'files': files, 'training': types.SimpleNamespace(MAX_METADATA=4096)},
            'base': base, 'require': base.require, 'OUTPUT': output, 'protected': (protected,),
            'cli_output': output / 'checkpoint-verification.json'}
        return output, protected, values

    def test_real_regression_existing_replay_output_accepts_postcheck(self):
        output, _, values = self.fixture()
        expressions(worker_guards[:2], values)
        (output / 'checkpoint-verification.json').write_bytes(b'{"fixture":"receipt"}\n')
        values['verification_pin'] = base.fingerprint(values['cli_output'])[0]
        with self.assertRaisesRegex(ValueError, 'output must be fresh'):
            expressions(old_guards, values)
        expressions([post_fingerprint], values)
        expressions(worker_guards[2:], values)  # verification.json is still fresh
        self.assertFalse((output / 'verification.json').exists())

    def test_preexisting_checkpoint_and_report_are_rejected_before_work(self):
        output, _, values = self.fixture()
        for name in ('checkpoint-verification.json', 'verification.json'):
            with self.subTest(name=name):
                target = output / name; target.write_bytes(b'fixture')
                with self.assertRaisesRegex(ValueError, 'output must be fresh'):
                    expressions(worker_guards[:2], values)
                target.unlink()

    def test_mutated_replay_receipt_fails_the_exact_new_postcheck(self):
        output, _, values = self.fixture()
        target = output / 'checkpoint-verification.json'
        target.write_bytes(b'{"fixture":"before"}\n')
        values['verification_pin'] = base.fingerprint(target)[0]
        target.write_bytes(b'{"fixture":"after!"}\n')
        with self.assertRaisesRegex(ValueError, 'receipt changed during post-replay checks'):
            expressions([post_fingerprint], values)

    def test_protected_path_and_symlink_output_still_rejected(self):
        output, protected, values = self.fixture()
        values['OUTPUT'] = protected
        with self.assertRaisesRegex(ValueError, 'protected input'):
            expressions(worker_guards[:2], values)
        values['OUTPUT'] = output
        (output / 'checkpoint-verification.json').symlink_to(protected / 'missing')
        with self.assertRaises(ValueError): expressions(worker_guards[:2], values)

    def test_only_the_declared_verifier_control_flow_changed(self):
        self.assertEqual(len(old_guards), 2); self.assertEqual(len(worker_guards), 3)
        self.assertEqual([dump(n) for n in old_guards], [dump(n) for n in worker_guards[:2]])
        restored_join = copy.deepcopy(new['scientific_join'])
        old_without_guards = copy.deepcopy(old['scientific_join'])
        old_without_guards.body = [n for n in old_without_guards.body if not is_guard(n)]
        self.assertEqual(dump(restored_join), dump(old_without_guards))
        removed = {dump(node) for node in (*worker_guards[:2], post_fingerprint)}
        restored_worker = copy.deepcopy(new['worker'])
        # Retain the final verification.json guard; remove the first two only.
        restored_worker.body = [node for i, node in enumerate(restored_worker.body)
            if not (i in [new['worker'].body.index(n) for n in worker_guards[:2]] or dump(node) == dump(post_fingerprint))]
        self.assertEqual(dump(restored_worker), dump(old['worker']))
        for name in set(new) - {'scientific_join', 'worker'}:
            self.assertEqual(dump(new[name]), dump(old[name]), name)
        self.assertEqual(dump(next(n for n in new['worker'].body if isinstance(n, ast.With))),
                         dump(next(n for n in old['worker'].body if isinstance(n, ast.With))))
        self.assertLess(new['worker'].body.index(worker_guards[1]),
                        next(i for i, n in enumerate(new['worker'].body) if isinstance(n, ast.With)))
        later_join = next(i for i, node in enumerate(new['worker'].body)
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple)
            and any(isinstance(n, ast.Name) and n.id == 'after_bound' for n in node.targets[0].elts))
        self.assertGreater(new['worker'].body.index(post_fingerprint), later_join)
        self.assertLess(new['worker'].body.index(post_fingerprint), new['worker'].body.index(worker_guards[2]))
        normalized = V.read_text().replace("OUTPUT = ARCHIVE / 'evaluation-verification-02'",
            "OUTPUT = ARCHIVE / 'evaluation-verification-01'")
        normalized = normalized.replace("    # Freshness belongs before replay; the later scientific join rechecks inputs.\n" +
            ''.join(ast.get_source_segment(V.read_text(), n).join(('    ', '\n')) for n in worker_guards[:2]), '')
        self.assertEqual({k for k in new if dump(new[k]) != dump(old[k])}, {'scientific_join', 'worker'})

    def test_reporter_only_uses_new_pin_and_attempt02_paths(self):
        prior = PB.read_text()
        expected = prior.replace('f4fc10fea71a3f444af7efcfbe0477b5a3721b6f07750ddf188cc55edcfde8d0', pin(V)['sha256'])
        expected = expected.replace("ARCHIVE / 'evaluation-verification-01'", "ARCHIVE / 'evaluation-verification-02'")
        expected = expected.replace("ARCHIVE / 'evaluation-verification-invocation-01.json'", "ARCHIVE / 'evaluation-verification-invocation-02.json'")
        self.assertEqual(P.read_text(), expected)
        for path in (V, P): ast.parse(path.read_text(), feature_version=(3, 9))
        self.assertIn("OUTPUT = ARCHIVE / 'evaluation-verification-02'", V.read_text())
        self.assertIn("INVOCATION = ARCHIVE / 'evaluation-verification-invocation-02.json'", P.read_text())


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
after_sources = {name: pin(Path(name)) for name in before_sources}
attempt = B / 'evaluation-verification-01'
attempt_after = {path.name: pin(path) for path in sorted(attempt.iterdir()) if path.is_file() and not path.is_symlink()}
unchanged = after_sources == before_sources and attempt_after == retained_before['failed_attempt_files']
diff = ''.join(''.join(difflib.unified_diff(prior.read_text().splitlines(True), current.read_text().splitlines(True),
    fromfile=prior.name, tofile=current.name)) for prior, current in ((VB, V), (PB, P)))
with DIFF.open('x') as stream: stream.write(diff)
usage = resource.getrusage(resource.RUSAGE_SELF)
cpu, wall, rss = usage.ru_utime + usage.ru_stime, time.monotonic() - STARTED, int(usage.ru_maxrss)
passed = result.wasSuccessful() and unchanged and cpu < 10 and wall < 15 and rss <= 256 * 1024**2
record = {'schema': 'peano-hydra-recovery-verification-fresh-output-fix-v1',
    'status': 'passed' if passed else 'failed', 'tests_run': result.testsRun,
    'prior_check_receipt': {'path': str(B / 'verification-fresh-output-fix-checks-01.json'), **pin(B / 'verification-fresh-output-fix-checks-01.json')},
    'fixture_correction': 'Check declared02 paths, not live absence after root began the actual authorized02 run; prior six-check result retained without alteration.',
    'errors': len(result.errors), 'failures': len(result.failures),
    'before_receipt': {'path': str(BEFORE), **pin(BEFORE)},
    'sources_before': before_sources, 'sources_after': after_sources, 'sources_unchanged_during_checks': after_sources == before_sources,
    'failed_attempt_before': retained_before['failed_attempt_files'], 'failed_attempt_after': attempt_after,
    'failed_attempt_untouched': attempt_after == retained_before['failed_attempt_files'],
    'diff': {'path': str(DIFF), **pin(DIFF)},
    'fresh_verification_directory': str(B / 'evaluation-verification-02'),
    'fresh_invocation_receipt': str(B / 'evaluation-verification-invocation-02.json'),
    'limits': {'cpu_seconds': 10, 'wall_seconds': 15, 'checked_rss_bytes': 256 * 1024**2},
    'cpu_seconds': cpu, 'wall_seconds': wall, 'peak_rss_bytes': rss,
    'actual_frozen_guard_used': True, 'actual_original_fingerprint_used': True,
    'scientific_binding_invoked': False, 'verifier_or_cli_main_invoked': False,
    'native_or_model_or_network_work_performed': False,
    'fixture_scope': 'actual guard/fingerprint expressions on temporary dummy files only; AST-preserved scientific/native/control flow'}
with RECEIPT.open('xb') as stream: stream.write(json.dumps(record, sort_keys=True, separators=(',', ':')).encode() + b'\n')
print(json.dumps({'status': record['status'], 'receipt': {'path': str(RECEIPT), **pin(RECEIPT)},
    'verifier': pin(V), 'reporter': pin(P)}, sort_keys=True))
signal.setitimer(signal.ITIMER_REAL, 0)
raise SystemExit(0 if passed else 2)
