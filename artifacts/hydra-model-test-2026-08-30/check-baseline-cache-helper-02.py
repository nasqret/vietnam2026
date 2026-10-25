"""One tiny readonly0444 copy and exact version-delta checks; no actual cache work."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import stat
import sys
import tempfile
import time

started = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('5-second readonly fixture deadline')))
signal.alarm(5)
archive = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
p = archive / 'stage-baseline-cache-remote-02.py'
raw = p.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'ee0dc43c43b0c8ded0080fb7476cb8f885a03b93ec874692d7e4c57284845fda'
old = (archive / 'stage-baseline-cache-remote-01.py').read_bytes()
select = lambda t: {n.name: ast.dump(n, include_attributes=False) for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
assert select(ast.parse(raw, feature_version=(3, 9))) == select(ast.parse(old))
spec = importlib.util.spec_from_file_location('_baseline_cache_readonly_fixture', p)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
plan = helper.validate_plan((archive / 'baseline-cache-stage-plan-02.json').read_bytes(), helper.PLAN_SHA)
assert plan['allowed_actual_source_modes'] == [0o444, 0o600, 0o644, 0o700, 0o755]
assert len(plan['files']) == 725 and sum(v['bytes'] for v in plan['files'].values()) == 235986082
with tempfile.TemporaryDirectory(prefix='hydra-cache-readonly-', dir='/private/tmp') as scratch:
    base = Path(scratch)
    source, target = base / 'historical', base / 'fresh'
    source.mkdir()
    files = {}
    for name in ('model/manifest.json', 'origin-source/fixture.py'):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = b'SYNTHETIC READONLY FIXTURE\n'
        path.write_bytes(payload)
        path.chmod(0o444)
        files[name] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
    helper.SOURCE_ROOT, helper.DESTINATION_ROOT = str(source), str(target)
    progress = {'destination_created': False, 'files_copied': 0, 'bytes_copied': 0}
    result = helper.perform({'files': files}, True, progress, time.monotonic() + 3)
    assert result['status'] == 'staged-and-independently-rehashed'
    assert progress['source_modes'] == {name: 0o444 for name in files}
    for name in files:
        assert (target / name).read_bytes() == (source / name).read_bytes()
        assert stat.S_IMODE((target / name).stat().st_mode) == 0o444
        assert (target / name).stat().st_ino != (source / name).stat().st_ino
        assert (target / name).stat().st_nlink == 1
assert p.read_bytes() == raw
assert not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules)
usage = resource.getrusage(resource.RUSAGE_SELF)
assert usage.ru_maxrss < 128 * 1024**2
record = {'schema': 'peano-hydra-baseline-cache-readonly-mode-check-v1', 'status': 'passed',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'helper_sha256': hashlib.sha256(raw).hexdigest(),
    'plan_sha256': plan and helper.PLAN_SHA, 'original_helper_sha256': hashlib.sha256(old).hexdigest(),
    'all_function_and_class_definitions_unchanged': True, 'python39_syntax': True,
    'only_observed0444_added_to_safe_modes': True, 'original_file_hashes_counts_and_resource_caps_unchanged': True,
    'actual_plan02_validated_without_source_reads': True,
    'tiny_readonly_copy_passed': True, 'fixture_files': 2, 'fixture_total_bytes': sum(v['bytes'] for v in files.values()),
    'actual_mode_preserved': '0444', 'source_and_target_byte_hashes_rechecked': True,
    'limits': {'cpu_seconds': 5, 'wall_seconds': 5, 'checked_peak_rss_bytes': 128 * 1024**2},
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - started,
                  'peak_rss_bytes': usage.ru_maxrss},
    'actual_cache_or_remote_access_performed': False, 'native_or_model_work_performed': False,
    'gpu_job_submitted': False, 'main_linux_resource_envelope_executed': False}
output = archive / 'baseline-cache-helper-checks-02.json'
with output.open('x') as stream:
    json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'status': 'passed', 'receipt_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'helper_sha256': record['helper_sha256'], 'resources': record['resources'], 'fixture_bytes': record['fixture_total_bytes']}, sort_keys=True))
