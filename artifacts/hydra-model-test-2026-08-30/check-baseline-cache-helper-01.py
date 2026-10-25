"""Bounded tiny filesystem fixtures only; never touches actual baseline/cache roots."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import tempfile
import time

started = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('10-second fixture boundary')))
signal.alarm(10)
archive = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
helper_path = archive / 'stage-baseline-cache-remote-01.py'
raw = helper_path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '36604b7a7a9293101b8ed2c6e5ea9ae79c0f22aec13ae8f55e1a7f3294c5c28d'
ast.parse(raw, feature_version=(3, 9))
spec = importlib.util.spec_from_file_location('_baseline_cache_tiny_fixture', helper_path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
plan_raw = (archive / 'baseline-cache-stage-plan-01.json').read_bytes()
actual_plan = helper.validate_plan(plan_raw, helper.PLAN_SHA)
assert len(actual_plan['files']) == 725 and sum(v['bytes'] for v in actual_plan['files'].values()) == 235986082
checks = {'python39_syntax': True, 'actual_plan_raw_pin_and_exact_closure': True}
for invalid in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'[]'):
    try:
        helper.decode(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid JSON accepted')
checks['ambiguous_and_nonfinite_json_rejected'] = True
for name in ('../escape', '/absolute', 'model//bad', 'origin-source/.git/config', 'model/id_rsa'):
    try:
        helper.relative(name)
    except ValueError:
        pass
    else:
        raise AssertionError('unsafe path accepted')
checks['traversal_credentials_and_hidden_git_rejected'] = True
with tempfile.TemporaryDirectory(prefix='hydra-baseline-cache-fixture-', dir='/private/tmp') as scratch:
    root = Path(scratch)
    source, destination = root / 'historical', root / 'fresh-cache'
    source.mkdir()
    data = {'model/manifest.json': (b'{"synthetic_only":true}\n', 0o600),
            'model/adapter/fixture.bin': (b'NOT MODEL WEIGHTS\n' * 20, 0o644),
            'origin-source/a.py': (b'# not executed\n', 0o700),
            'origin-source/nested/b.py': (b'# not executed either\n', 0o755),
            'origin-source/empty.json': (b'', 0o600)}
    files = {}
    for name, (payload, mode) in data.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        path.chmod(mode)
        files[name] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
    helper.SOURCE_ROOT, helper.DESTINATION_ROOT = str(source), str(destination)
    helper.FILE_COUNT, helper.TOTAL_BYTES = len(files), sum(item['bytes'] for item in files.values())
    plan = {'files': files}
    def progress():
        return {'destination_created': False, 'files_copied': 0, 'bytes_copied': 0}
    preflight = progress()
    checked = helper.perform(plan, False, preflight, time.monotonic() + 5)
    assert checked['status'] == 'read-only-preflight-passed' and not destination.exists()
    assert preflight['source_modes'] == {name: mode for name, (_, mode) in data.items()}
    checks['preflight_reads_only_and_records_actual_remote_modes'] = True
    staged = progress()
    result = helper.perform(plan, True, staged, time.monotonic() + 5)
    assert result['status'] == 'staged-and-independently-rehashed' and staged['files_copied'] == len(files)
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    for name, (payload, mode) in data.items():
        assert (source / name).read_bytes() == (destination / name).read_bytes() == payload
        assert stat.S_IMODE((destination / name).stat().st_mode) == mode
        assert (source / name).stat().st_ino != (destination / name).stat().st_ino
        assert (destination / name).stat().st_nlink == 1
    checks['exclusive_copy_preserves_all_four_safe_modes_and_rehashes'] = True
    try:
        helper.perform(plan, True, progress(), time.monotonic() + 5)
    except ValueError as error:
        assert 'already exists' in str(error)
    else:
        raise AssertionError('existing cache accepted')
    checks['existing_cache_never_adopted_or_overwritten'] = True
    helper.DESTINATION_ROOT = str(root / 'linked-destination')
    Path(helper.DESTINATION_ROOT).symlink_to(destination, target_is_directory=True)
    try:
        helper.perform(plan, True, progress(), time.monotonic() + 5)
    except ValueError as error:
        assert 'already exists' in str(error)
    else:
        raise AssertionError('symlink destination accepted')
    checks['symlink_destination_rejected'] = True
    helper.DESTINATION_ROOT = str(root / 'should-stay-absent')
    link = source / 'model/alias.bin'
    os.link(source / 'model/adapter/fixture.bin', link)
    try:
        helper.perform(plan, True, progress(), time.monotonic() + 5)
    except ValueError as error:
        assert 'link or special' in str(error)
    else:
        raise AssertionError('hard-linked source accepted')
    assert not Path(helper.DESTINATION_ROOT).exists()
    link.unlink()
    checks['hardlinked_source_rejected_before_destination_creation'] = True
    unsafe = source / 'origin-source/a.py'
    unsafe.chmod(0o666)
    try:
        helper.perform(plan, True, progress(), time.monotonic() + 5)
    except ValueError as error:
        assert 'unsafe source/target file or mode' in str(error)
    else:
        raise AssertionError('unsafe source mode accepted')
    assert not Path(helper.DESTINATION_ROOT).exists()
    unsafe.chmod(0o700)
    checks['unsafe_source_mode_rejected_before_copy'] = True
    real_copy = helper.copy_file
    def changing_copy(source_tree, target_tree, name, pin, before, deadline):
        (source / name).write_bytes(b'SYNTHETIC MODIFICATION')
        return real_copy(source_tree, target_tree, name, pin, before, deadline)
    helper.copy_file = changing_copy
    failed = progress()
    try:
        helper.perform(plan, True, failed, time.monotonic() + 5)
    except ValueError as error:
        assert 'source changed after preflight' in str(error)
    else:
        raise AssertionError('source drift accepted')
    assert failed['destination_created'] and Path(helper.DESTINATION_ROOT).exists()
    assert not any(path.is_file() for path in Path(helper.DESTINATION_ROOT).rglob('*'))
    checks['source_drift_rejected_and_fresh_partial_destination_preserved'] = True
assert helper_path.read_bytes() == raw
assert not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules)
usage = resource.getrusage(resource.RUSAGE_SELF)
assert usage.ru_maxrss < 256 * 1024**2
result = {'schema': 'peano-hydra-baseline-cache-helper-local-checks-v1', 'status': 'passed',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'helper_sha256': hashlib.sha256(raw).hexdigest(),
    'plan_sha256': hashlib.sha256(plan_raw).hexdigest(), 'checks': checks,
    'limits': {'cpu_seconds': 10, 'wall_seconds': 10, 'checked_peak_rss_bytes': 256 * 1024**2},
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - started,
                  'peak_rss_bytes': usage.ru_maxrss},
    'fixture_file_count': 5, 'fixture_total_bytes': sum(len(payload) for payload, _ in data.values()),
    'actual_baseline_sources_read_or_copied': False, 'network_contacted': False,
    'native_or_model_work_performed': False, 'gpu_job_submitted': False,
    'main_linux_resource_envelope_executed': False,
    'limitation': 'Metadata and tiny temporary filesystem checks; no actual baseline cache staging or remote resource test.'}
output = archive / 'baseline-cache-helper-checks-01.json'
with output.open('x') as stream:
    json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'status': 'passed', 'checks': len(checks), 'receipt': str(output),
    'receipt_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'resources': result['resources']}, sort_keys=True))
