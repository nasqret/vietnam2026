"""Synthetic metadata boundary checks; no source plan, Git or freeze execution."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import unittest


HERE = Path(__file__).absolute().parent
HELPER = HERE / 'hydra-advancement-execution-freeze-v2.py'
OLD_HELPER = HERE / 'hydra-advancement-execution-freeze.py'
spec = importlib.util.spec_from_file_location('advancement_freeze_v2', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def fixture():
    entry = {'bytes': 3, 'sha256': '1' * 64, 'git_blob': '2' * 40, 'mode': '100644'}
    source = {'schema': helper.freezer.PLAN_SCHEMA, 'source_root': str(helper.ROOT),
              'files': {'training/peano_hydra/example.py': dict(entry)}}
    source['plan_sha256'] = helper.digest(source)
    record = {
        'schema': helper.PLAN_SCHEMA, 'source_root': str(helper.ROOT), 'data_root': str(helper.DATA_ROOT),
        'output_directory': str(helper.ROOT.parent / 'metadata-fixture-never-created'),
        'source_plan': source, 'jobs': {name: dict(entry) for name in helper.JOBS},
        'data_files': {name: {**entry, **pin} for name, pin in helper.DATA_PINS.items()},
        'limits': {'max_files': helper.MAX_FILES, 'max_total_bytes': helper.MAX_BYTES,
                   'max_job_bytes': helper.MAX_JOB_BYTES, 'max_data_file_bytes': helper.MAX_DATA_FILE_BYTES},
        'native_or_model_work_requested': False, 'network_or_scheduler_work_requested': False,
    }
    resign(record)
    return record


def resign(record, *, source=False):
    if source:
        sub = record['source_plan']
        sub['plan_sha256'] = helper.digest({k: v for k, v in sub.items() if k != 'plan_sha256'})
    data = record['data_files']
    record['data_files_sha256'] = helper.digest(data)
    record['data_file_count'] = len(data)
    record['data_total_bytes'] = sum(item['bytes'] for item in data.values())
    record['files'] = {**record['source_plan']['files'], **record['jobs'], **data}
    record['files_sha256'] = helper.digest(record['files'])
    record['file_count'] = len(record['files'])
    record['total_bytes'] = sum(item['bytes'] for item in record['files'].values())
    seal(record)


def seal(record):
    record['plan_sha256'] = helper.digest({k: v for k, v in record.items() if k != 'plan_sha256'})


class MetadataBoundaries(unittest.TestCase):
    def rejected(self, record):
        with self.assertRaises(ValueError):
            helper.validate_plan(record)

    def test_fixed_data_set_is_separate_and_included_in_total(self):
        record = fixture()
        self.assertIs(helper.validate_plan(record), record)
        self.assertEqual(record['data_file_count'], 2)
        self.assertEqual(record['data_total_bytes'], 16887078)
        self.assertEqual(record['file_count'], 7)
        self.assertFalse(set(record['source_plan']['files']) & set(record['data_files']))

    def test_resealed_missing_or_extra_ancillary_file_is_rejected(self):
        for name in helper.DATA_PINS:
            with self.subTest(missing=name):
                record = fixture()
                del record['data_files'][name]
                resign(record)
                self.rejected(record)
        record = fixture()
        record['data_files']['research/unreviewed.json'] = dict(next(iter(record['data_files'].values())))
        resign(record)
        self.rejected(record)

    def test_resealed_raw_pin_or_size_or_executable_change_is_rejected(self):
        for name in helper.DATA_PINS:
            for key, changed in (('sha256', 'f' * 64), ('bytes', 1), ('mode', '100755')):
                with self.subTest(file=name, field=key):
                    record = fixture()
                    record['data_files'][name][key] = changed
                    resign(record)
                    self.rejected(record)

    def test_read_only_root_cannot_be_substituted(self):
        record = fixture()
        record['data_root'] = str(helper.ROOT)
        resign(record)
        self.rejected(record)

    def test_data_cannot_be_reclassified_as_historical_source(self):
        record = fixture()
        name = next(iter(record['data_files']))
        record['source_plan']['files'][name] = dict(record['data_files'][name])
        resign(record, source=True)
        self.rejected(record)

    def test_old_source_ceiling_is_not_an_additional_data_allowance(self):
        record = fixture()
        data_and_jobs = record['data_total_bytes'] + sum(item['bytes'] for item in record['jobs'].values())
        record['source_plan']['files']['training/peano_hydra/example.py']['bytes'] = helper.MAX_BYTES - data_and_jobs + 1
        resign(record, source=True)
        self.assertEqual(record['total_bytes'], helper.MAX_BYTES + 1)
        self.rejected(record)

    def test_data_cannot_be_omitted_from_declared_byte_total(self):
        record = fixture()
        record['total_bytes'] -= record['data_total_bytes']
        seal(record)
        self.rejected(record)

    def test_resealed_data_inventory_summary_changes_are_rejected(self):
        for key, changed in (('data_files_sha256', 'f' * 64), ('data_file_count', 3), ('data_total_bytes', 0)):
            with self.subTest(field=key):
                record = fixture()
                record[key] = changed
                seal(record)
                self.rejected(record)

    def test_resealed_limits_and_authority_cannot_be_increased(self):
        for key in fixture()['limits']:
            with self.subTest(limit=key):
                record = fixture()
                record['limits'][key] += 1
                resign(record)
                self.rejected(record)
        for key in ('native_or_model_work_requested', 'network_or_scheduler_work_requested'):
            record = fixture()
            record[key] = True
            resign(record)
            self.rejected(record)

    def test_all_four_existing_jobs_remain_required_and_bounded(self):
        for name in helper.JOBS:
            with self.subTest(missing=name):
                record = fixture()
                del record['jobs'][name]
                resign(record)
                self.rejected(record)
        record = fixture()
        record['jobs'][helper.JOBS[-1]]['bytes'] = helper.MAX_JOB_BYTES + 1
        resign(record)
        self.rejected(record)

    def test_15d_and_earlier_snapshots_stay_protected(self):
        for name in ('hydra-advancement-execution-20260830', 'hydra-frontier-training-execution-20260830',
                     'hydra-frontier-execution-20260830'):
            with self.subTest(snapshot=name):
                record = fixture()
                destination = helper.ROOT.parent / name
                self.assertIn(destination, helper.PROTECTED)
                record['output_directory'] = str(destination)
                resign(record)
                self.rejected(record)
        self.assertEqual((helper.MAX_FILES, helper.MAX_BYTES, helper.MAX_JOB_BYTES), (2048, 128 * 1024**2, 64 * 1024))
        self.assertEqual((helper.CPU, helper.WALL, helper.RSS, helper.OUTPUT), (120, 120, 1024**3, 2 * 1024**2))
        self.assertEqual(helper.MAX_DATA_FILE_BYTES, 16 * 1024**2)


if __name__ == '__main__':
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (HELPER, OLD_HELPER)}
    started = time.monotonic()
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(MetadataBoundaries))
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (HELPER, OLD_HELPER)}
    forbidden = sorted(name for name in sys.modules if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers', 'peano_lab'))
    passed = result.wasSuccessful() and before == after and not forbidden
    receipt = {
        'schema': 'peano-hydra-advancement-execution-freeze-v2-helper-metadata-tests-v1',
        'passed': passed, 'tests': result.testsRun, 'output': stream.getvalue(),
        'wall_seconds': time.monotonic() - started, 'helper_hashes_before': before,
        'helper_hashes_after': after, 'helper_hashes_unchanged': before == after,
        'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'forbidden_modules': forbidden, 'source_plan_executed': False, 'git_executed': False,
        'source_freeze_executed': False, 'actual_data_files_read': False,
        'scope': 'Synthetic metadata boundaries only. No source inventory, JSON data read, copy, Git, native proof, model, network or scheduler execution; not end-to-end freezer validation.',
    }
    path = HERE / 'advancement-freezer-v2-helper-tests-01.json'
    with path.open('x') as output:
        json.dump(receipt, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(receipt, sort_keys=True))
    raise SystemExit(0 if passed else 1)
