"""Synthetic observer-only host regressions; no SSH, jobs or model execution."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ARCHIVE = Path(__file__).absolute().parent
FROZEN = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-training-execution-20260830')


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ARCHIVE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load('observer_v1_regressions', 'test-training-transfer-observer.py')
client = load('observer_v2_client', 'observe-frontier-training-v2.py')
remote = load('observer_v2_remote', 'observe-frontier-training-remote-v2.py')
base.observer = client
base.observer_remote = remote


class ExistingObservationSafety(base.ObservationSafety):
    """Reuse only the five original observer rejection/tail tests."""


class HostCompatibilitySafety(unittest.TestCase):
    def test_exact_frozen_directory_algorithm_and_other_functions_unchanged(self):
        def functions(source):
            return {node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
        frozen = functions((FROZEN / 'training/peano_hydra/search_launch.py').read_text())
        original = functions((ARCHIVE / 'observe-frontier-training-remote.py').read_text())
        revised = functions((ARCHIVE / 'observe-frontier-training-remote-v2.py').read_text())
        self.assertEqual(ast.dump(revised['directory']), ast.dump(frozen['directory']))
        self.assertEqual(set(revised), set(original))
        for name in revised.keys() - {'directory', 'main'}:
            self.assertEqual(ast.dump(revised[name]), ast.dump(original[name]), name)
        text = (ARCHIVE / 'observe-frontier-training-remote-v2.py').read_text()
        normalized = text.replace('resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2)',
                                  'resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2)')
        self.assertEqual(ast.dump(functions(normalized)['main']), ast.dump(original['main']))

    def test_client_only_changes_remote_selection_not_identity_or_command_logic(self):
        old = ast.parse((ARCHIVE / 'observe-frontier-training.py').read_text())
        new = ast.parse((ARCHIVE / 'observe-frontier-training-v2.py').read_text())
        def normalize(tree):
            kept = []
            for node in tree.body:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    continue
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'REMOTE' for t in node.targets):
                    continue
                kept.append(ast.dump(node))
            return kept
        self.assertEqual(normalize(old), normalize(new))
        self.assertEqual(client.REMOTE.name, 'observe-frontier-training-remote-v2.py')
        self.assertEqual(client.CLIENT.name, 'transfer-frontier-training.py')

    def test_linux_ancestors_use_search_handles_and_final_leaf_is_read_only(self):
        calls, closed = [], []
        path_flag = 0x200000
        def opened(path, flags, **kwargs):
            calls.append((str(path), flags, kwargs.get('dir_fd')))
            return 100 + len(calls)
        with mock.patch.object(remote.sys, 'platform', 'linux'), \
             mock.patch.object(remote.os, 'O_PATH', path_flag, create=True), \
             mock.patch.object(remote.os, 'open', side_effect=opened), \
             mock.patch.object(remote.os, 'close', side_effect=closed.append):
            descriptor = remote.directory('/net/scratch/plgrid/approved-leaf')
            self.assertEqual(descriptor, 105)
        self.assertEqual([row[0] for row in calls], ['/', 'net', 'scratch', 'plgrid', 'approved-leaf'])
        for _, flags, _ in calls[:-1]:
            self.assertTrue(flags & path_flag)
            self.assertTrue(flags & os.O_DIRECTORY)
            self.assertTrue(flags & os.O_NOFOLLOW)
        self.assertEqual(calls[-1][1], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.assertEqual(closed, [101, 102, 103, 104])

    def test_symlink_ancestor_cannot_redirect_log_reads(self):
        with tempfile.TemporaryDirectory(prefix='observer-v2-synthetic-', dir=ARCHIVE) as temporary:
            root = Path(temporary)
            (root / 'real/logs').mkdir(parents=True)
            (root / 'real/logs/test.out').write_bytes(b'unchanged')
            (root / 'alias').symlink_to(root / 'real', target_is_directory=True)
            with mock.patch.object(remote, 'ROOT', str(root / 'alias')):
                with self.assertRaises(OSError):
                    remote.read('logs/test.out', 65536, tail=True)
            self.assertEqual((root / 'real/logs/test.out').read_bytes(), b'unchanged')

    def test_main_keeps_read_only_caps_and_does_not_infer_completion(self):
        limits, commands, alarms = [], [], []
        job = '123456'
        with tempfile.TemporaryDirectory(prefix='observer-v2-synthetic-', dir=ARCHIVE) as temporary:
            def command(arguments):
                commands.append(arguments)
                self.assertIn(arguments[0], ('squeue', 'sacct', 'scontrol'))
                text = ''
                if arguments[0] == 'scontrol':
                    text = ' '.join(key + '=' + value for key, value in {
                        'JobId': job, 'JobName': remote.JOB_NAME, 'WorkDir': temporary,
                        'Account': remote.ACCOUNT, 'Partition': remote.PARTITION,
                        'TimeLimit': '02:00:00', 'NumCPUs': '8', 'JobState': 'RUNNING'}.items())
                return {'returncode': 0, 'reason': 'exited', 'stdout': text, 'stderr': ''}
            output = io.StringIO()
            with mock.patch.object(remote, 'ROOT', temporary), \
                 mock.patch.object(remote.sys, 'argv', ['synthetic', job, 'a' * 64]), \
                 mock.patch.object(remote.resource, 'setrlimit', side_effect=lambda key, value: limits.append((key, value))), \
                 mock.patch.object(remote.signal, 'signal'), \
                 mock.patch.object(remote.signal, 'alarm', side_effect=alarms.append), \
                 mock.patch.object(remote, 'bound_job', return_value={'job_id': job, 'synthetic_not_approval': True}), \
                 mock.patch.object(remote, 'command', side_effect=command), \
                 contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as exited:
                    remote.main()
            self.assertEqual(exited.exception.code, 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result['status'], 'observed')
            self.assertFalse(result['manifest']['exists'])
            self.assertTrue(result['read_only'])
            self.assertFalse(result['job_submission_performed'])
            self.assertEqual(list(Path(temporary).iterdir()), [])
        self.assertEqual(limits, [(remote.resource.RLIMIT_CPU, (20, 20)),
                                 (remote.resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2)),
                                 (remote.resource.RLIMIT_FSIZE, (0, 0))])
        self.assertEqual(alarms, [50, 0])
        self.assertEqual(len(commands), 3)

    def test_remote_retains_python36_compatibility(self):
        ast.parse((ARCHIVE / 'observe-frontier-training-remote-v2.py').read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main(verbosity=2)
