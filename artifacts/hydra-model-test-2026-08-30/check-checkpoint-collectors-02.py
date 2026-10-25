#!/usr/bin/env python3
"""Tiny import/archive fixtures only; never performs a real collection or SSH."""
import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import resource
import signal
import tempfile
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
REMOTE = ARCHIVE / 'collect-diagnostic-checkpoint-remote-02.py'
LOCAL = ARCHIVE / 'collect-diagnostic-checkpoint-02.py'
REMOTE_SHA = 'c36be7646549d0e5feba6dbc0a27bf01d6dc70c536ab5dc24f8ead8b17ad563f'
LOCAL_SHA = 'b464e029b9475aaf33f1df1c721464985b462da210a113d92539a4145ed35582'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, name, pin):
    raw = path.read_bytes()
    assert sha(raw) == pin
    ast.parse(raw)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixture wall cap')))
    signal.alarm(10)
    remote = load(REMOTE, 'fixture_remote_checkpoint_collector', REMOTE_SHA)
    local = load(LOCAL, 'fixture_local_checkpoint_collector', LOCAL_SHA)
    checks = ['both helpers parse and import without main or bytecode writes']
    old = ast.parse((ARCHIVE / 'collect-diagnostic-remote-01.py').read_bytes())
    new = ast.parse(REMOTE.read_bytes())
    for name in ('bound_job', 'accounting'):
        extract = lambda tree: ast.dump(next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name), include_attributes=False)
        assert extract(old) == extract(new)
        checks.append(name + ' AST identical to reviewed collector01')
    def rejected(name, call):
        try:
            call()
        except (ValueError, OSError):
            checks.append(name)
        else:
            raise AssertionError('fixture must reject: ' + name)
    with tempfile.TemporaryDirectory(prefix='hydra-checkpoint-fixture-', dir='/private/tmp') as temporary:
        root = Path(temporary)
        remote.ROOT = str(root / 'remote')
        checkpoint = Path(remote.ROOT) / remote.CHECKPOINT
        checkpoint.mkdir(parents=True)
        controls = Path(remote.ROOT) / remote.PACKAGE
        controls.mkdir(parents=True)
        # Original immutable control bytes are used only as bounded fixture input.
        for name in ('approval.json', 'resource-request.json', 'evaluation-request.json'):
            (controls / name).write_bytes((local.PACKAGE / name).read_bytes())
        ledger = Path(remote.ROOT) / remote.LEDGER
        ledger.parent.mkdir(parents=True)
        ledger.write_bytes(b'{"synthetic_fixture_only":true}\n')
        expected = {
            '.lock': b'',
            'header.json': b'{"synthetic_fixture_only":true,"header":1}\n',
            'HEAD.json': b'{"synthetic_fixture_only":true,"count":1}\n',
            '000001.goal.json': b'{"synthetic_fixture_only":true,"not_a_proof":1}\n',
            '.transaction-demo': b'uncommitted synthetic debris\n',
            'debris/nested.txt': b'unknown original fixture bytes\n',
        }
        (checkpoint / 'debris/empty').mkdir(parents=True)
        for name, raw in expected.items():
            (checkpoint / name).write_bytes(raw)
        binding = {'job_id': local.EXACT_JOB, 'approval_sha256': local.EXACT_APPROVAL,
            'resource_request_sha256': local.EXACT_REQUEST, 'evaluation_request_sha256': local.EXACT_EVALUATION,
            'source_commit': local.SOURCE_COMMIT, 'ledger_sha256': sha(ledger.read_bytes()),
            'ledger_events': 6, 'reserved_gpu_seconds': 900}
        top = [local.EXACT_JOB, local.PROFILE + '-evaluate', 'COMPLETED', '0:0', '1', '15', '8', '64G',
            'cpu=8,gres/gpu=1', local.REMOTE_ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret']
        # Deliberately synthetic accounting is never retained as a real receipt.
        status = {'synthetic_fixture_only': True, 'command': [], 'returncode': 0, 'stdout': '|'.join(top) + '\n',
            'stderr': '', 'top_row': top, 'state': top[2], 'exit_code': top[3], 'elapsed_seconds': 1}
        def build():
            index, wanted, signatures, snapshot = remote.build_inventory(local.EXACT_JOB, binding, status)
            index['synthetic_fixture_only'] = True
            buffer = io.BytesIO()
            remote.emit_archive(index, wanted, signatures, buffer)
            return buffer.getvalue(), index
        raw, index = build()
        assert len(raw) < 256 * 1024 and len(index['checkpoint_entry_inventory']) == 8
        assert set(index['checkpoint_entry_inventory']) == set(expected) | {'debris', 'debris/empty'}
        assert index['checkpoint_debris_filtered'] is False and index['checkpoint_original_lock_collected'] is True
        output = root / 'collected'
        output.mkdir()
        collected, pin = local.extract(raw, output, local.EXACT_JOB, local.EXACT_APPROVAL, local.EXACT_EVALUATION)
        assert collected == index and pin == {'bytes': len((output / 'collection-index.json').read_bytes()),
            'sha256': sha((output / 'collection-index.json').read_bytes())}
        for name, body in expected.items():
            assert (output / 'checkpoint' / name).read_bytes() == body
        assert (output / 'checkpoint/debris/empty').is_dir()
        checks.append('original lock, row, transaction debris, unknown file and empty directory survive exact archive roundtrip')
        rejected('existing local output is never overwritten',
            lambda: local.extract(raw, output, local.EXACT_JOB, local.EXACT_APPROVAL, local.EXACT_EVALUATION))
        mutated = bytearray(raw)
        position = mutated.find(expected['.transaction-demo'])
        assert position >= 0
        mutated[position] ^= 1
        corrupt = root / 'corrupt'
        corrupt.mkdir()
        rejected('tampered archived file bytes fail before collection success',
            lambda: local.extract(bytes(mutated), corrupt, local.EXACT_JOB, local.EXACT_APPROVAL, local.EXACT_EVALUATION))
        (checkpoint / '.lock').unlink()
        no_lock_raw, no_lock_index = build()
        absent = root / 'absent-lock'
        absent.mkdir()
        local.extract(no_lock_raw, absent, local.EXACT_JOB, local.EXACT_APPROVAL, local.EXACT_EVALUATION)
        assert no_lock_index['checkpoint_original_lock_collected'] is False and not (absent / 'checkpoint/.lock').exists()
        checks.append('missing original lock remains absent and is never fabricated')
        (checkpoint / 'unsafe-link').symlink_to('HEAD.json')
        rejected('checkpoint symlink fails closed without dereference', remote.checkpoint_inventory)
        (checkpoint / 'unsafe-link').unlink()
        os.link(checkpoint / 'HEAD.json', checkpoint / 'hardlinked-debris')
        rejected('checkpoint hardlink and transaction debris fail closed without filtering', remote.checkpoint_inventory)
        (checkpoint / 'hardlinked-debris').unlink()
        rejected('archive traversal path is rejected', lambda: local.path_name('checkpoint/../outside'))
        rejected('backslash alias is rejected', lambda: local.path_name('checkpoint/unsafe\\alias'))
        total = sum(item.stat().st_size for item in root.rglob('*') if item.is_file())
        assert total < 2 * 1024**2
    usage = resource.getrusage(resource.RUSAGE_SELF)
    assert usage.ru_maxrss < 128 * 1024**2 and time.monotonic() - started < 10
    receipt = {'schema': 'peano-hydra-checkpoint-collector-synthetic-checks-v1', 'status': 'synthetic-checks-passed',
        'local_helper': {'path': str(LOCAL), 'bytes': LOCAL.stat().st_size, 'sha256': LOCAL_SHA},
        'remote_helper': {'path': str(REMOTE), 'bytes': REMOTE.stat().st_size, 'sha256': REMOTE_SHA},
        'checker_sha256': sha(Path(__file__).read_bytes()), 'checks': checks,
        'fixture_checkpoint_entries': len(index['checkpoint_entry_inventory']), 'fixture_archive_bytes': len(raw),
        'retained_fixture_files': False, 'actual_collection_performed': False, 'network_performed': False,
        'scheduler_commands_performed': False, 'model_imports_or_execution': False, 'native_validation_performed': False,
        'proofs_independently_verified': False, 'original_collectors_modified': False,
        'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - started,
            'maxrss_bytes': usage.ru_maxrss, 'fixture_disk_bytes_at_end': total},
        'limits': {'cpu_soft_seconds': 5, 'cpu_hard_seconds': 6, 'wall_seconds': 10,
            'checked_peak_rss_bytes': 128 * 1024**2, 'file_bytes': 2 * 1024**2, 'fixture_total_bytes': 2 * 1024**2}}
    output = ARCHIVE / 'checkpoint-collector-checks-02.json'
    body = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode() + b'\n'
    with output.open('xb') as stream:
        stream.write(body)
    signal.alarm(0)
    print(json.dumps({'path': str(output), 'bytes': len(body), 'sha256': sha(body), 'checks': len(checks)}, sort_keys=True))


if __name__ == '__main__':
    main()
