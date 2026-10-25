"""Metadata boundary checks only; does not plan, run Git or freeze a source."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('execution_freeze', HERE / 'frontier-training-execution-freeze.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def fixture():
    entry = {'bytes': 3, 'sha256': '1' * 64, 'git_blob': '2' * 40, 'mode': '100644'}
    # Synthetic metadata only: the freeze stage always regenerates the actual
    # scaling plan and byte-compares it before creating any output directory.
    source = {'schema': helper.freezer.PLAN_SCHEMA, 'source_root': str(helper.ROOT),
              'files': {'training/peano_hydra/example.py': dict(entry)}}
    source['plan_sha256'] = helper.digest(source)
    jobs = {name: dict(entry) for name in helper.JOBS}
    files = {**source['files'], **jobs}
    record = {'schema': helper.PLAN_SCHEMA, 'source_root': str(helper.ROOT),
        'output_directory': str(helper.ROOT.parent / 'test-execution-fixture-never-created'),
        'source_plan': source, 'jobs': jobs, 'files': files,
        'files_sha256': helper.digest(files), 'file_count': len(files), 'total_bytes': sum(row['bytes'] for row in files.values()),
        'limits': {'max_files': helper.MAX_FILES, 'max_total_bytes': helper.MAX_BYTES,
                   'max_job_bytes': helper.MAX_JOB_BYTES},
        'native_or_model_work_requested': False, 'network_or_scheduler_work_requested': False}
    record['plan_sha256'] = helper.digest(record)
    return record


def resign(record):
    record['files'] = {**record['source_plan']['files'], **record['jobs']}
    record['files_sha256'] = helper.digest(record['files'])
    record['file_count'] = len(record['files'])
    record['total_bytes'] = sum(v['bytes'] for v in record['files'].values())
    record['plan_sha256'] = helper.digest({k: v for k, v in record.items() if k != 'plan_sha256'})


class ExecutionFreezeMetadataTests(unittest.TestCase):
    def test_exact_declared_three_job_contract(self):
        helper.validate_plan(fixture())
        value = fixture()
        value['jobs']['slurm/undeclared.sbatch'] = dict(next(iter(value['jobs'].values())))
        resign(value)
        with self.assertRaises(ValueError):
            helper.validate_plan(value)

    def test_recomputed_digest_does_not_raise_job_bound(self):
        value = fixture()
        value['jobs'][helper.JOBS[0]]['bytes'] = helper.MAX_JOB_BYTES + 1
        resign(value)
        with self.assertRaises(ValueError):
            helper.validate_plan(value)

    def test_original_source_hash_tampering_is_rejected(self):
        value = fixture()
        value['source_plan']['files']['training/peano_hydra/example.py']['sha256'] = 'f' * 64
        resign(value)
        with self.assertRaises(ValueError):
            helper.validate_plan(value)

    def test_original_repo_cannot_be_destination(self):
        value = fixture()
        value['output_directory'] = str(helper.ROOT)
        resign(value)
        with self.assertRaises(ValueError):
            helper.validate_plan(value)

    def test_recomputed_digest_cannot_add_training_authority(self):
        value = fixture()
        value['network_or_scheduler_work_requested'] = True
        resign(value)
        with self.assertRaises(ValueError):
            helper.validate_plan(value)

    def test_sampled_fork_exec_names_do_not_admit_shell_or_remote_tools(self):
        for value in ('git', '/usr/bin/git', 'Python', '(Python)', helper.sys.executable):
            self.assertTrue(helper.allowed_sampled_child(value))
        for value in ('bash', 'sh', 'ssh', 'sbatch', 'curl', 'git-remote-https'):
            self.assertFalse(helper.allowed_sampled_child(value))


    def test_missing_new_training_only_job_rejected(self):
        value = fixture()
        del value['jobs']['slurm/peano_hydra_frontier_training.sbatch']
        resign(value)
        with self.assertRaises(ValueError):
            helper.validate_plan(value)

    def test_prior_frozen_source_and_sealed_archive_are_protected(self):
        self.assertIn(helper.ROOT.parent / 'hydra-frontier-execution-20260830', helper.PROTECTED)
        self.assertIn(Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-experiment-2026-08-30'), helper.PROTECTED)
        self.assertEqual(helper.MAX_FILES, 2048)
        self.assertEqual(helper.MAX_BYTES, 128 * 1024**2)
        self.assertEqual(helper.MAX_JOB_BYTES, 64 * 1024)

if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExecutionFreezeMetadataTests))
    receipt = {'schema': 'peano-hydra-training-execution-freeze-helper-metadata-tests-v1',
        'passed': result.wasSuccessful(), 'tests': result.testsRun, 'output': stream.getvalue(),
        'helper_sha256': hashlib.sha256((HERE / 'frontier-training-execution-freeze.py').read_bytes()).hexdigest(),
        'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_plan_executed': False, 'git_executed': False, 'source_freeze_executed': False,
        'scope': 'Synthetic metadata checks for exact jobs, file bounds, destination isolation, tampering and authority; no end-to-end source freeze claim.'}
    with (HERE / 'training-freezer-helper-tests-01.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
    print(json.dumps(receipt, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
