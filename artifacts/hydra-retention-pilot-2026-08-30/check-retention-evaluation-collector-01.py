"""Tiny synthetic checkpoint archives only: no actual gate, model or replay."""
import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import resource
import signal
import stat
import sys
import tarfile
import tempfile
import time

started = time.monotonic()
A = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('tiny archive checks wall cap')))
signal.alarm(30)


def audit(event, args):
    if event.startswith(('subprocess.', 'os.system', 'os.posix_spawn', 'socket.')):
        raise RuntimeError('synthetic checks cannot execute processes or network')
    if event == 'import' and args[0].split('.')[0] in {'training', 'torch', 'transformers', 'peft', 'tokenizers', 'vllm'}:
        raise RuntimeError('synthetic checks cannot import scientific/model code')


sys.addaudithook(audit)
pins = {}
for name in ('collect-retention-evaluation-01.py', 'collect-retention-evaluation-remote-01.py'):
    raw = (A / name).read_bytes()
    ast.parse(raw, feature_version=(3, 9)); compile(raw, str(A / name), 'exec')
    pins[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
spec = importlib.util.spec_from_file_location('synthetic_retention_evaluation_collector', A / 'collect-retention-evaluation-01.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r = m.load_protocol((A / 'collect-retention-evaluation-remote-01.py').read_bytes())
job, train_job = '999999999999', '999999999998'


def file_signature(size): return [1, 100, stat.S_IFREG | 0o600, size, 1, 1, 1]
def directory_signature(): return [1, 200, stat.S_IFDIR | 0o700, 0, 1, 1, 2]


def fixture(mode, absent_head=False):
    # These clearly fictional bytes test transport shape only, not any proof,
    # model, approval, native handle or runtime authenticity decision.
    fixed = r.fixed_metadata(job, train_job)
    if mode == 'inspect': fixed.pop('evaluation.json')
    bodies = {name: ('synthetic:' + name).encode() for name in r.MANDATORY}
    cp = {'.lock': b'', 'header.json': b'{"synthetic":true}\n', 'HEAD.json': b'{"synthetic_head":true}\n',
          '00000.goal.json': b'{"synthetic_not_a_proof":true}\n', 'debris/tiny.tmp': b'original debris'}
    if absent_head: cp.pop('HEAD.json')
    if mode == 'inspect': cp = {name: raw for name, raw in cp.items() if name in r.INSPECTION_ENTRIES}
    bodies.update({'checkpoint/' + name: raw for name, raw in cp.items()})
    entries = None
    directories = ['checkpoint']
    if mode == 'checkpoint':
        entries = {name: {'kind': 'file', 'bytes': len(raw), 'sha256': r.sha(raw),
                         'source_signature': file_signature(len(raw)), 'source_mode': 0o600} for name, raw in cp.items()}
        entries['debris'] = {'kind': 'directory', 'source_signature': directory_signature(), 'source_mode': 0o700}
        directories.append('checkpoint/debris')
    wanted = dict(fixed)
    for name in cp: wanted['checkpoint/' + name] = (r.CHECKPOINT + '/' + name, r.MAX_CHECKPOINT_FILE)
    if mode == 'inspect':
        for name in r.INSPECTION_ENTRIES: wanted['checkpoint/' + name] = (r.CHECKPOINT + '/' + name, r.MAX_CHECKPOINT_FILE)
    files = {name: {'bytes': len(raw), 'sha256': r.sha(raw), 'remote_path': wanted[name][0]} for name, raw in bodies.items()}
    identity = {'approval_sha256': files['approval.json']['sha256'], 'source_commit': r.SOURCE_COMMIT,
        'resource_request_sha256': files['resource-request.json']['sha256'], 'source_files_sha256': 'a' * 64,
        'payloads_sha256': 'b' * 64, 'synced_at': 'synthetic', 'job_script_sha256': {'train': 'c' * 64, 'evaluate': 'd' * 64}}
    manifest = {key: files['model-manifest.json'][key] for key in ('bytes', 'sha256')}
    head = None if absent_head else {key: files['checkpoint/HEAD.json'][key] for key in ('bytes', 'sha256')}
    binding = {'job_id': job, 'train_job_id': train_job, 'approval_sha256': identity['approval_sha256'],
        'resource_request_sha256': identity['resource_request_sha256'], 'source_commit': r.SOURCE_COMMIT,
        'execution_identity': identity, 'source_header_sha256': r.sha(r.canonical(identity)),
        'training_request_sha256': files['train-request.json']['sha256'], 'evaluation_request_sha256': files['evaluate-request.json']['sha256'],
        'training_ledger_sha256': files['train-ledger.jsonl']['sha256'], 'evaluation_ledger_sha256': files['evaluate-ledger.jsonl']['sha256'],
        'training_ledger_events': 6, 'evaluation_ledger_events': 6, 'reserved_gpu_seconds': 3600,
        'training_reserved_gpu_seconds': 7200, 'model_manifest': manifest,
        'candidate_matches_original_evaluation_reservation': True, 'validated_by_frozen_training_completed': True}
    top = [job, r.PROFILE + '-evaluate', 'FAILED', '0:10', '3000', '60', '8', '64G', 'gres/gpu=1',
           r.ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret']
    index = {'schema': r.INDEX_SCHEMA, 'mode': mode, 'binding': binding,
        'accounting': {'stdout': '|'.join(top) + '|\n', 'top_row': top, 'state': 'FAILED', 'exit_code': '0:10',
                      'elapsed_seconds': 3000, 'returncode': 0},
        'files': files, 'directories': directories, 'absent_files': sorted(set(wanted) - set(files)),
        'total_file_bytes': sum(len(raw) for raw in bodies.values()), 'checkpoint_head': head, 'model_manifest': manifest,
        'checkpoint_root_present': True, 'checkpoint_root_signature': directory_signature(), 'checkpoint_entry_inventory': entries,
        'checkpoint_goal_records_collected': mode == 'checkpoint', 'checkpoint_all_actual_entries_collected': mode == 'checkpoint',
        'checkpoint_original_lock_collected': True, 'checkpoint_metadata_is_not_verified_proof_evidence': True, 'read_only': True,
        **{key: False for key in ('checkpoint_debris_filtered', 'checkpoint_files_modified', 'proofs_independently_verified',
                                 'model_artifact_directories_read', 'model_frameworks_imported', 'scheduler_mutation_performed', 'automatic_retry')},
        'limits': {'checkpoint_entries': r.MAX_CHECKPOINT_ENTRIES, 'data_files': r.MAX_DATA_FILES,
                   'checkpoint_file_bytes': r.MAX_CHECKPOINT_FILE, 'aggregate_file_bytes': r.MAX_TOTAL}}
    local = {key: identity[key] for key in ('approval_sha256', 'resource_request_sha256', 'source_commit', 'source_files_sha256', 'payloads_sha256')}
    local.update({key: binding[key] for key in ('training_request_sha256', 'evaluation_request_sha256')})
    return index, bodies, local


def archive_bytes(index, bodies):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        raw = r.canonical(index) + b'\n'
        member = tarfile.TarInfo('collection-index.json'); member.size = len(raw)
        archive.addfile(member, io.BytesIO(raw))
        for name in index['directories']:
            member = tarfile.TarInfo(name + '/'); member.type = tarfile.DIRTYPE
            archive.addfile(member)
        for name, raw in sorted(bodies.items()):
            member = tarfile.TarInfo(name); member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
    return result.getvalue()


checks = ['python39_syntax_and_python311_compile']
with tempfile.TemporaryDirectory(prefix='retention-evaluation-collector-fixture-') as temporary:
    root = Path(temporary).resolve()
    def check(label, mode='checkpoint', mutation=None, absent_head=False, expected_ok=False):
        index, bodies, local = fixture(mode, absent_head)
        output = root / label; output.mkdir()
        head = '-' if mode == 'inspect' else ('absent' if absent_head else index['checkpoint_head']['sha256'])
        manifest = '-' if mode == 'inspect' else index['model_manifest']['sha256']
        if mutation == 'head-pin': head = 'f' * 64
        if mutation == 'manifest-pin': manifest = 'f' * 64
        if mutation == 'missing-lock':
            del bodies['checkpoint/.lock']; del index['files']['checkpoint/.lock']
        if mutation == 'changed-goal': bodies['checkpoint/00000.goal.json'] += b'changed'
        raw = archive_bytes(index, bodies)
        path = output / 'transfer.tar'; path.write_bytes(raw)
        binding = index['binding']
        args = (path, output, r, mode, job, binding['approval_sha256'], binding['source_header_sha256'], head, manifest,
                local, {'bytes': len(raw), 'sha256': r.sha(raw)})
        try:
            m.extract(*args)
            if mutation == 'overwrite': m.extract(*args)
        except (ValueError, OSError, KeyError, TypeError, tarfile.TarError):
            if expected_ok: raise
        else:
            if not expected_ok: raise AssertionError('guard did not reject: ' + label)
            assert (output / 'checkpoint/.lock').read_bytes() == b''
            if mode == 'checkpoint': assert (output / 'checkpoint/debris/tiny.tmp').read_bytes() == b'original debris'
        checks.append(label)
    check('metadata_inspection_only', mode='inspect', expected_ok=True)
    check('all_entries_empty_lock_and_debris_preserved', expected_ok=True)
    check('absent_head_remains_absent', absent_head=True, expected_ok=True)
    check('external_head_mismatch_rejected', mutation='head-pin')
    check('external_manifest_mismatch_rejected', mutation='manifest-pin')
    check('omitted_original_lock_rejected', mutation='missing-lock')
    check('changed_goal_bytes_rejected', mutation='changed-goal')
    check('existing_output_never_overwritten', mutation='overwrite')
for name, pin in pins.items(): assert hashlib.sha256((A / name).read_bytes()).hexdigest() == pin['sha256']
usage = resource.getrusage(resource.RUSAGE_SELF)
record = {'schema': 'peano-hydra-retention-evaluation-collector-checks-v1', 'status': 'passed', 'helpers': pins,
    'checks': checks, 'synthetic_archives_only': True, 'actual_collector_or_gate_invoked': False,
    'network_subprocess_model_tokenizer_native_or_scheduler_work': False, 'frozen_source_edited': False,
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - started,
                  'peak_rss_bytes': usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024}}
raw = m.canonical(record) + b'\n'
output = A / 'evaluation-collector-helper-checks-01.json'
with output.open('xb') as stream: stream.write(raw)
print(json.dumps({'status': 'passed', 'checks': len(checks), 'receipt': str(output), 'sha256': m.sha(raw)}, sort_keys=True))
