"""Two explicit local invocations for one bounded, original Helios origin check.

Only a small orchestration program is sent. Source/data/weights already on the
server are read there. The native stage writes a fresh sibling evidence archive,
never the completed training tree. No scheduler or model execution is requested.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import selectors
import shlex
import signal
import subprocess
import time


ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
REMOTE_HELPER = ARCHIVE / 'origin-check-remote-03.py'
HELPER_SHA = '37b9c8752d9505cb1142598a94a0da58819ee021b8d431989ddd92629d75b8e4'
PYTHON = '/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3'
LIBRARY = ('/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib:'
           '/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64')


def write_once(path, raw):
    assert path.parent == ARCHIVE and len(raw) <= 16 * 1024**2
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('stage', choices=('inventory', 'authenticate'))
    parser.add_argument('--inventory-sha256')
    args = parser.parse_args()
    assert (args.inventory_sha256 is not None) == (args.stage == 'authenticate')
    assert ARCHIVE.resolve() == ARCHIVE and not REMOTE_HELPER.is_symlink()
    helper = REMOTE_HELPER.read_bytes()
    assert len(helper) < 65536 and hashlib.sha256(helper).hexdigest() == HELPER_SHA
    prefix = 'candidate-origin-' + args.stage + '-01'
    names = {label: ARCHIVE / (prefix + '.' + suffix) for label, suffix in (
        ('start', 'started.json'), ('stdout', 'stdout.json'), ('stderr', 'stderr.log'), ('receipt', 'process.json'))}
    assert not any(os.path.lexists(path) for path in names.values())
    arguments = ['--inventory-only']
    inventory = None
    if args.stage == 'authenticate':
        path = ARCHIVE / 'candidate-origin-inventory-01.stdout.json'
        raw = path.read_bytes()
        assert len(raw) <= 32768 and hashlib.sha256(raw).hexdigest() == args.inventory_sha256
        value = json.loads(raw)
        assert value['status'] == 'inventory-only-passed' and value['original_validator_executed'] is False
        inventory = {'path': path.name, 'bytes': len(raw), 'sha256': args.inventory_sha256}
        arguments = ['--authenticate', '--inventory-receipt-base64', base64.b64encode(raw).decode(),
                     '--expected-inventory-sha256', args.inventory_sha256]
    remote = shlex.join(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LC_ALL=C',
                         'LD_LIBRARY_PATH=' + LIBRARY, PYTHON, '-I', '-B', '-X',
                         'pycache_prefix=/dev/null', '-', *arguments])
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
               '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
               '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
               '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--',
               'plgnasqret@helios.cyfronet.pl', remote]
    wall = 50 if args.stage == 'inventory' else 245
    started = time.monotonic()
    start = {'schema': 'peano-hydra-candidate-origin-transport-start-v1', 'stage': args.stage,
             'helper_sha256': HELPER_SHA, 'program_bytes_sent': len(helper), 'inventory': inventory,
             'started_at_utc': datetime.now(timezone.utc).isoformat(),
             'transport_wall_seconds': wall, 'automatic_retry': False,
             'private_source_or_model_payload_uploaded': False,
             'new_evidence_directory_creation_requested': args.stage == 'authenticate',
             'invocation_correction': 'Fresh instrumented check with unchanged two-library runtime and native/supervisor limits',
             'runtime_import_probe_sha256': '089288eb9d8d84c5bd440d7a724be988a193ebde00e9cb7f8abee9845da8a92a',
             'prior_original_validator_import_failure_preserved': '../hydra-advancement-2026-08-30/candidate-origin-authenticate-01.stdout.json',
             'prior_inventory_failure_preserved': '../hydra-advancement-2026-08-30/candidate-origin-inventory-01.process.json',
             'local_controller_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_once(names['start'], (json.dumps(start, sort_keys=True, indent=2) + '\n').encode())
    resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    caps = {'stdout': 8 * 1024**2, 'stderr': 128 * 1024}
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    selector = selectors.DefaultSelector()
    reason, error = 'exited', None
    try:
        process.stdin.write(helper)
        process.stdin.close()
        for label, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map() or process.poll() is None:
            if time.monotonic() - started > wall:
                raise TimeoutError('bounded SSH transport deadline')
            for key, _ in selector.select(0.1):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                room = caps[key.data] - len(output[key.data])
                output[key.data].extend(chunk[:room])
                if len(chunk) > room:
                    raise ValueError('bounded SSH output exceeded')
        process.wait(timeout=1)
    except BaseException as failure:
        reason, error = 'transport-stopped', type(failure).__name__ + ': ' + str(failure)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        selector.close()
        process.stdout.close()
        process.stderr.close()
    descriptors = {label: write_once(names[label], bytes(raw)) for label, raw in output.items()}
    record = {**start, 'schema': 'peano-hydra-candidate-origin-transport-result-v1',
              'reason': reason, 'error': error, 'returncode': process.returncode,
              'wall_seconds': time.monotonic() - started, 'streams': descriptors,
              'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'remote_program_unchanged': hashlib.sha256(REMOTE_HELPER.read_bytes()).hexdigest() == HELPER_SHA,
              'model_weights_downloaded': False, 'scheduler_calls': False}
    remote_result = None
    if reason == 'exited' and process.returncode in (0, 2):
        try:
            remote_result = json.loads(output['stdout'])
            record['remote_status'] = remote_result['status']
            if 'origin_receipt_base64' in remote_result:
                raw = base64.b64decode(remote_result['origin_receipt_base64'], validate=True)
                assert len(raw) <= 4 * 1024**2 and hashlib.sha256(raw).hexdigest() == remote_result['origin_receipt_sha256']
                record['original_origin_receipt'] = write_once(ARCHIVE / 'candidate-origin-receipt-01.json', raw)
        except (ValueError, KeyError, TypeError, AssertionError) as failure:
            record['decoding_error'] = type(failure).__name__ + ': ' + str(failure)
    descriptor = write_once(names['receipt'], (json.dumps(record, sort_keys=True, indent=2) + '\n').encode())
    summary = {'stage': args.stage, 'returncode': process.returncode, 'reason': reason,
               'remote_status': record.get('remote_status'), 'receipt': descriptor,
               'stdout': descriptors['stdout'], 'original_origin_receipt': record.get('original_origin_receipt')}
    if remote_result is not None and 'error' in remote_result:
        summary['remote_error'] = remote_result['error']
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if process.returncode == 0 and reason == 'exited' and 'decoding_error' not in record else 1


if __name__ == '__main__':
    raise SystemExit(main())
