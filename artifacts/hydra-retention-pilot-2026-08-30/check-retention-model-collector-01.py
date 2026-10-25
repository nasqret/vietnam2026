"""Tiny synthetic archive checks only; never invoke either collector main()."""
import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import tarfile
import tempfile
import time

STARTED = time.monotonic()
A = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
RESULT = A / 'model-collector-helper-checks-01.json'
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
for name in ('collect-retention-model-01.py', 'collect-retention-model-remote-01.py'):
    raw = (A / name).read_bytes()
    ast.parse(raw, feature_version=(3, 9)); compile(raw, str(A / name), 'exec')
    pins[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
spec = importlib.util.spec_from_file_location('synthetic_retention_collector', A / 'collect-retention-model-01.py')
local = importlib.util.module_from_spec(spec); spec.loader.exec_module(local)
remote = local.load_protocol((A / 'collect-retention-model-remote-01.py').read_bytes())
job, approval = '999999999999', 'a' * 64


def fixture(mode):
    # Deliberately fictional tiny bytes. No model, native handle, origin, job
    # reservation or actual control admission is constructed or invoked.
    artifacts = {name: ('synthetic:' + name).encode() for names in remote.ARTIFACTS.values() for name in names}
    reservation = {'stage': 'train', 'job_id': job, 'approval_sha256': approval,
        'source_commit': remote.SOURCE_COMMIT, 'reservation': {'seconds': 7200, 'gpus': 1, 'cpus': 8, 'memory_gib': 64}}
    manifest = {'schema': 'peano-hydra-retention-trained-adapter-v1', 'profile': remote.PROFILE, 'run_id': remote.RUN_ID,
        'model_trained': True, 'training_plan_sha256': remote.PLAN_SHA,
        'initialization': {'kind': 'fresh-pinned-base-new-lora', 'continued_from_ancestor_adapter': False},
        'automatic_retry': False, 'resume': False, 'reservation': reservation, 'final_reservation': reservation,
        'metrics': {'actual_optimizer_steps': 1469}}
    for group, names in remote.ARTIFACTS.items():
        files = {name: remote.sha(artifacts[name]) for name in names}
        manifest[group] = {'root': group, 'files': files, 'sha256': remote.sha(remote.canonical(files))}
    fixed = remote.metadata_files(job)
    bodies = {'model/manifest.json': remote.canonical(manifest) + b'\n'}
    for name in ('metadata/approval.json', 'metadata/resource-request.json', 'metadata/train-request.json', 'metadata/train-ledger.jsonl'):
        bodies[name] = ('synthetic:' + name).encode()
    # The pin argument is the digest of synthetic approval bytes in this test.
    actual_approval = remote.sha(bodies['metadata/approval.json'])
    manifest['reservation']['approval_sha256'] = actual_approval
    bodies['model/manifest.json'] = remote.canonical(manifest) + b'\n'
    if mode == 'model': bodies.update({'model/' + name: raw for name, raw in artifacts.items()})
    files = {name: {'bytes': len(raw), 'sha256': remote.sha(raw),
                   'remote_path': fixed[name][0] if name in fixed else remote.MODEL + '/' + name[len('model/'):]}
             for name, raw in bodies.items()}
    binding = {'job_id': job, 'approval_sha256': actual_approval, 'resource_request_sha256': files['metadata/resource-request.json']['sha256'],
        'source_commit': remote.SOURCE_COMMIT, 'source_files_sha256': 'b' * 64, 'payloads_sha256': 'c' * 64,
        'training_request_sha256': files['metadata/train-request.json']['sha256'], 'training_plan_sha256': remote.PLAN_SHA,
        'ledger_sha256': files['metadata/train-ledger.jsonl']['sha256'], 'ledger_events': 6, 'reserved_gpu_seconds': 7200,
        'manifest': {key: files['model/manifest.json'][key] for key in ('bytes', 'sha256')},
        'validated_by_frozen_training_completed': True}
    top = [job, remote.PROFILE + '-train', 'COMPLETED', '0:0', '4000', '120', '8', '64G', 'gres/gpu=1',
           remote.ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret']
    index = {'schema': remote.INDEX_SCHEMA, 'mode': mode, 'binding': binding,
        'accounting': {'returncode': 0, 'stdout': '|'.join(top) + '|\n', 'top_row': top, 'state': 'COMPLETED',
                      'exit_code': '0:0', 'elapsed_seconds': 4000},
        'files': files, 'absent_files': ['metadata/training.err.log', 'metadata/training.out.log'],
        'total_file_bytes': sum(len(raw) for raw in bodies.values()),
        'declared_artifact_files': {name: remote.sha(raw) for name, raw in artifacts.items()},
        'model_artifact_files_collected': mode == 'model', 'read_only': True,
        **{key: False for key in ('model_frameworks_imported', 'artifact_semantics_authenticated',
                                 'proofs_independently_verified', 'scheduler_mutation_performed', 'automatic_retry')}}
    return index, bodies


def archive_bytes(index, bodies, extra=None):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        entries = [('collection-index.json', remote.canonical(index) + b'\n')] + sorted(bodies.items())
        if extra: entries.insert(1, extra)
        for name, raw in entries:
            member = tarfile.TarInfo(name); member.size = len(raw); member.mode = 0o600
            archive.addfile(member, io.BytesIO(raw))
    return result.getvalue()


checks = ['python39_syntax_and_python311_compile']
with tempfile.TemporaryDirectory(prefix='retention-model-collector-fixture-') as temporary:
    root = Path(temporary).resolve()
    def check(label, mode='model', mutation=None, expected_ok=False):
        index, bodies = fixture(mode)
        output = root / label; output.mkdir()
        expected = index['binding']['manifest']['sha256'] if mode == 'model' else None
        extra = None
        if mutation == 'manifest-pin': expected = 'f' * 64
        if mutation == 'artifact-byte': bodies['model/adapter/adapter_model.safetensors'] += b'changed'
        if mutation == 'path': extra = ('../escape', b'forbidden')
        raw = archive_bytes(index, bodies, extra)
        path = output / 'transfer.tar'; path.write_bytes(raw)
        pin = {'bytes': len(raw), 'sha256': remote.sha(raw)}
        arguments = (path, output, remote, mode, job, index['binding']['approval_sha256'], expected, index['binding'], pin)
        try:
            local.extract(*arguments)
            if mutation == 'overwrite': local.extract(*arguments)
        except (ValueError, OSError, KeyError, TypeError, tarfile.TarError):
            if expected_ok: raise
        else:
            if not expected_ok: raise AssertionError('guard did not reject: ' + label)
        checks.append(label)
    check('metadata_inspection_preserves_bytes', mode='inspect', expected_ok=True)
    check('complete_declared_model_preserves_bytes', expected_ok=True)
    check('external_manifest_mismatch_rejected', mutation='manifest-pin')
    check('changed_artifact_rejected', mutation='artifact-byte')
    check('traversal_member_rejected', mutation='path')
    check('existing_output_never_overwritten', mutation='overwrite')
for name, pin in pins.items():
    assert hashlib.sha256((A / name).read_bytes()).hexdigest() == pin['sha256']
usage = resource.getrusage(resource.RUSAGE_SELF)
record = {'schema': 'peano-hydra-retention-model-collector-helper-checks-v1', 'status': 'passed',
    'helpers': pins, 'checks': checks, 'only_synthetic_artifacts': True,
    'collector_main_invoked': False, 'actual_gate_invoked': False, 'network_or_subprocess_performed': False,
    'model_tokenizer_or_native_proof_executed': False, 'frozen_source_edited': False,
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - STARTED,
                  'peak_rss_bytes': usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024}}
raw = local.canonical(record) + b'\n'
with RESULT.open('xb') as output: output.write(raw)
print(json.dumps({'status': 'passed', 'checks': len(checks), 'receipt': str(RESULT),
                  'sha256': hashlib.sha256(raw).hexdigest()}, sort_keys=True))
