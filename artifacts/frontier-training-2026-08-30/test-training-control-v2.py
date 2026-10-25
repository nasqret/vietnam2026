"""Offline invocation-correction checks; no SSH, submission or main() call."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock

ARCHIVE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('control_v2', ARCHIVE / 'run-training-control-v2.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def without_comments(value):
    return '\n'.join(line for line in value.splitlines() if line.strip() and not line.lstrip().startswith('#'))


class InvocationCorrection(unittest.TestCase):
    def test_actual_pinned_transfer_failure_and_python_probe_join(self):
        value = control.prerequisites(control.APPROVAL)
        self.assertEqual(value['candidate_python'], '/usr/bin/python3.9')
        self.assertEqual(value['machine'], 'x86_64')
        self.assertTrue(value['version'].startswith('3.9.25 '))

    def test_different_approval_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact original'):
            control.prerequisites('0' * 64)

    def test_original_three_local_gates_are_byte_equivalent_without_comments(self):
        frozen = (control.ROOT / 'scripts/helios_hydra_frontier_training.sh').read_text()
        start = 'metadata="$(python3 -I -B "$gate" --check --local'
        old = frozen[frozen.index(start):frozen.index('ssh -o BatchMode=yes')]
        new = control.BRIDGE[control.BRIDGE.index(start):control.BRIDGE.index('ssh -o BatchMode=yes')]
        self.assertEqual(without_comments(old), without_comments(new))

    def test_only_remote_executable_changes_in_frozen_remote_gate_block(self):
        frozen = (control.ROOT / 'scripts/helios_hydra_frontier_training.sh').read_text()
        old = frozen.split("<<'REMOTE'\n", 1)[1]
        new = control.BRIDGE.split("<<'REMOTE'\n", 1)[1]
        self.assertEqual(old, new.replace('exec /usr/bin/python3.9 -I -B', 'exec python3 -I -B'))

    def test_bridge_is_valid_bash_without_executing_it(self):
        result = subprocess.run(['/bin/bash', '-n'], input=control.BRIDGE.encode(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_submit_requires_same_helper_and_successful_nonallocating_test(self):
        record = {'schema': 'peano-hydra-frontier-training-control-invocation-v1', 'phase': 'test-only',
                  'returncode': 0, 'timed_out': False, 'source_commit': control.COMMIT,
                  'approval_sha256': control.APPROVAL, 'helper_sha256': 'a' * 64,
                  'stdout': json.dumps({'status': 'test-only', 'allocation_performed': False})}
        with mock.patch.object(control, 'read', return_value=json.dumps(record).encode()):
            self.assertRegex(control.require_successful_v2_test('a' * 64), '[0-9a-f]{64}')
            with self.assertRaisesRegex(ValueError, 'successful exact'):
                control.require_successful_v2_test('b' * 64)
        record['returncode'] = 1
        with mock.patch.object(control, 'read', return_value=json.dumps(record).encode()):
            with self.assertRaisesRegex(ValueError, 'successful exact'):
                control.require_successful_v2_test('a' * 64)


if __name__ == '__main__':
    unittest.main(verbosity=2)
