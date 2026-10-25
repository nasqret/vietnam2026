#!/usr/bin/env python3
"""Tiny local Tree/adversarial fixtures; never invoke reconciliation/main/SSH."""
import time
STARTED = time.monotonic()
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import tempfile
import types
import unittest

B = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
LOCAL = B / 'reconcile-evaluation-recovery-transfer-01.py'
REMOTE = B / 'reconcile-evaluation-recovery-transfer-01-remote.py'
OUTPUT = B / 'reconciliation-helper-checks-01.json'
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
def timeout(*_):
    raise TimeoutError('tiny reconciliation checks15-second wall limit')
signal.signal(signal.SIGALRM, timeout)
signal.setitimer(signal.ITIMER_REAL, 15)


def pin(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


before = {path.name: pin(path) for path in (LOCAL, REMOTE)}
module = types.ModuleType('reconciliation_offline_fixture_only')
module.__file__ = str(LOCAL)
exec(compile(LOCAL.read_bytes(), str(LOCAL), 'exec'), module.__dict__)
sender, remote, _, _ = module.bootstrap()
r = sender.r


class Checks(unittest.TestCase):
    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='reconcile-evaluation-recovery-check-', dir=str(B))
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / 'sub').mkdir(mode=0o700)
        raw = {'source.py': b'original\n', 'sub/control.json': b'{"mode":"evaluate"}\n',
               r.PROVENANCE: b'fixture-provenance\n', 'empty.py': b''}
        modes = {name: 0o700 if name == 'source.py' else 0o600 for name in raw}
        files = {name: {'bytes': len(value), 'sha256': r.sha(value)} for name, value in raw.items()}
        for name, value in raw.items():
            (root / name).write_bytes(value)
            (root / name).chmod(modes[name])
        tree = r.Tree(str(root))
        self.addCleanup(tree.close)
        return root, tree, files, modes

    def verify(self, tree, files, modes):
        return remote.verify_installed(r, tree, files, modes,
            {'sub/control.json', r.PROVENANCE}, b'{"original":"fixture-only"}\n')

    def test_real_tree_and_zero_byte_file_without_durable_receipt(self):
        _, tree, files, modes = self.fixture()
        result, _ = self.verify(tree, files, modes)
        self.assertEqual(result['input_file_count'], 4)
        self.assertEqual(result['input_total_bytes'], sum(item['bytes'] for item in files.values()))
        self.assertEqual(result['durable_receipt'], {'present': False, 'path': r.REMOTE_RECEIPT})

    def test_existing_durable_receipt_requires_exact_actual_bytes(self):
        root, tree, files, modes = self.fixture()
        receipt = root / r.REMOTE_RECEIPT
        receipt.write_bytes(b'{"original":"fixture-only"}\n')
        receipt.chmod(0o600)
        self.assertTrue(self.verify(tree, files, modes)[0]['durable_receipt']['present'])
        receipt.write_bytes(b'{"original":"wrong-bytes!"}\n')
        with self.assertRaises(ValueError):
            self.verify(tree, files, modes)

    def test_extra_file_and_empty_directory_are_rejected(self):
        root, tree, files, modes = self.fixture()
        (root / 'foreign').write_bytes(b'x')
        with self.assertRaises(ValueError): self.verify(tree, files, modes)
        (root / 'foreign').unlink()
        (root / 'empty-foreign').mkdir(mode=0o700)
        with self.assertRaises(ValueError): self.verify(tree, files, modes)

    def test_missing_file_and_changed_file_mode_or_bytes_are_rejected(self):
        root, tree, files, modes = self.fixture()
        (root / 'source.py').chmod(0o600)
        with self.assertRaises(ValueError): self.verify(tree, files, modes)
        (root / 'source.py').chmod(0o700)
        (root / 'source.py').write_bytes(b'changed!\n')
        with self.assertRaises(ValueError): self.verify(tree, files, modes)
        (root / 'empty.py').unlink()
        with self.assertRaises(ValueError): self.verify(tree, files, modes)

    def test_symlink_and_hardlink_are_rejected(self):
        root, tree, files, modes = self.fixture()
        (root / 'empty.py').unlink()
        (root / 'empty.py').symlink_to('source.py')
        with self.assertRaises(ValueError): self.verify(tree, files, modes)
        (root / 'empty.py').unlink()
        os.link(root / 'source.py', root / 'empty.py')
        with self.assertRaises(ValueError): self.verify(tree, files, modes)

    def test_metadata_mutation_during_full_read_is_rejected(self):
        root, tree, files, modes = self.fixture()
        original = tree.fingerprint
        def changed(name, retain=False):
            result = original(name, retain)
            if name == 'source.py':
                (root / 'sub/control.json').write_bytes(b'{"mode":"training"}\n')
            return result
        tree.fingerprint = changed
        with self.assertRaises(ValueError): self.verify(tree, files, modes)

    def test_readonly_audit_rejects_writes_mutation_subprocess_network(self):
        attempts = []
        audit = remote.readonly_audit(attempts)
        for event, args in (
            ('open', ('fixture', 'w', os.O_WRONLY | os.O_CREAT)),
            ('open', ('fixture', 'r', os.O_RDWR)),
            ('open', ('fixture', 'r+', 0)), ('os.mkdir', ('fixture', 0o700)),
            ('os.rename', ('a', 'b')), ('os.chmod', ('a', 0o600)),
            ('os.remove', ('a',)), ('subprocess.Popen', ('anything',)),
            ('socket.connect', ('anything',)), ('ctypes.dlopen', ('anything',)),
            ('import', ('torch',))):
            with self.subTest(event=event, args=args):
                with self.assertRaises(RuntimeError): audit(event, args)
        audit('open', ('fixture', 'r', os.O_RDONLY))
        self.assertEqual(len(attempts), 11)

    def test_actual_pinned_evidence_and_metadata_request_bounds(self):
        # Reads only existing metadata; no admission, native/model, main or SSH.
        ctx = module.context(sender, remote, before[LOCAL.name]['sha256'])
        self.assertEqual(ctx['plan']['file_count'], 907)
        self.assertEqual(ctx['durable']['file_count'], 908)
        self.assertEqual(ctx['durable']['total_bytes'], 92999725)
        raw = r.canonical(ctx['request']) + b'\n'
        self.assertLess(len(raw), r.MAX_JSON)
        command = module.ssh_command(r, ctx['program'], r.sha(raw))
        self.assertLessEqual(len(command[-1].encode()), 120000)
        for key in ('failed_send_json', 'prepared_plan_json', 'plan_json', 'send_header_json'):
            altered = dict(ctx['request']); altered[key] += ' '
            with self.assertRaises(ValueError): remote.evidence(r, altered)
        self.assertEqual(sender.bounded.__code__.co_filename, str(module.SENDER))
        for path in (LOCAL, REMOTE): ast.parse(path.read_bytes(), feature_version=(3, 9))


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
after = {path.name: pin(path) for path in (LOCAL, REMOTE)}
usage = resource.getrusage(resource.RUSAGE_SELF)
cpu = usage.ru_utime + usage.ru_stime
wall = time.monotonic() - STARTED
rss = int(usage.ru_maxrss)
passed = result.wasSuccessful() and before == after and cpu < 10 and wall < 15 and rss <= 256 * 1024**2
receipt = {'schema': 'peano-hydra-retention-reconciliation-offline-checks-v1',
    'status': 'passed' if passed else 'failed', 'tests_run': result.testsRun,
    'errors': len(result.errors), 'failures': len(result.failures),
    'source_before': before, 'source_after': after, 'source_unchanged': before == after,
    'limits': {'cpu_seconds': 10, 'wall_seconds': 15, 'checked_rss_bytes': 256 * 1024**2},
    'cpu_seconds': cpu, 'wall_seconds': wall, 'peak_rss_bytes': rss,
    'actual_reconciliation_invoked': False, 'main_or_bounded_invoked': False,
    'network_work_performed': False, 'model_or_native_work_performed': False,
    'temporary_fixture_scope': 'synthetic files only; actual preserved evidence read-only'}
with OUTPUT.open('xb') as stream:
    stream.write(r.canonical(receipt) + b'\n')
print(json.dumps({'status': receipt['status'], 'receipt': dict(path=str(OUTPUT), **pin(OUTPUT))}, sort_keys=True))
signal.setitimer(signal.ITIMER_REAL, 0)
raise SystemExit(0 if passed else 2)
