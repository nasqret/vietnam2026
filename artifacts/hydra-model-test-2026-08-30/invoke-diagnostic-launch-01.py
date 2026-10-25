"""Capture one invocation of the unchanged approved diagnostic launch wrapper."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
EXECUTION = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-model-test-execution-20260830')
PACKAGE = EXECUTION / '_deploy/hydra-frontier-diagnostic-v1'
TRANSPORT = ARCHIVE / 'transfer-diagnostic-01.py'
TRANSPORT_SHA = 'f8f0c72a5c8e28807a9ca3ee18a3bf782f3738ac186187cf6e469746b362a0b9'
REQUEST_SHA = '49117e3c7d62f9fd50931a84abfcbf3ce2c24d50fff672ae78d7b526c7b5354b'
APPROVAL_SHA = '10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e'
SCRIPT = 'scripts/helios_hydra_frontier_diagnostic.sh'


def read(path):
    assert not path.is_symlink() and path.stat().st_size <= 4 * 1024**2
    return path.read_bytes()


def write(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    assert len(raw) <= 1024**2
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('mode', choices=('test-only', 'submit'))
    args = parser.parse_args()
    assert sys.flags.isolated and sys.dont_write_bytecode
    resource.setrlimit(resource.RLIMIT_CPU, (60, 61))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def alarm(signum, frame):
        raise TimeoutError('whole launch invocation exceeded 120 seconds')
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(120)
    assert hashlib.sha256(read(TRANSPORT)).hexdigest() == TRANSPORT_SHA
    spec = importlib.util.spec_from_file_location('hydra_reviewed_bounded_transport', TRANSPORT)
    transport = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = transport
    spec.loader.exec_module(transport)
    request_raw, approval_raw = read(PACKAGE / 'resource-request.json'), read(PACKAGE / 'approval.json')
    assert hashlib.sha256(request_raw).hexdigest() == REQUEST_SHA
    assert hashlib.sha256(approval_raw).hexdigest() == APPROVAL_SHA
    request = json.loads(request_raw)
    assert hashlib.sha256(read(EXECUTION / SCRIPT)).hexdigest() == request['source_files'][SCRIPT]['sha256']
    assert json.loads(read(ARCHIVE / 'diagnostic-transfer-01/send-result.json'))['status'] == 'transferred-and-rehashed'
    if args.mode == 'submit':
        prior = json.loads(read(ARCHIVE / 'launch-test-only-01.json'))
        assert prior['status'] == 'passed' and prior['result']['status'] == 'test-only'
        assert prior['approval_sha256'] == APPROVAL_SHA and prior['resource_request_sha256'] == REQUEST_SHA
    stem = 'launch-' + args.mode + '-01'
    command = ['/bin/bash', str(EXECUTION / SCRIPT), '--approval-sha256', APPROVAL_SHA, '--' + args.mode]
    if args.mode == 'submit':
        command += ['--confirm', 'PEANO-HYDRA-FRONTIER-DIAGNOSTIC-900-GPU-SECONDS']
    write(ARCHIVE / (stem + '.started.json'), {
        'schema': 'peano-hydra-diagnostic-launch-invocation-start-v1',
        'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'mode': args.mode, 'command': command, 'approval_sha256': APPROVAL_SHA,
        'resource_request_sha256': REQUEST_SHA, 'automatic_retry': False,
    })
    process = transport.bounded(command, timeout=110)
    record = {
        'schema': 'peano-hydra-diagnostic-launch-invocation-v1', 'mode': args.mode,
        'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'failed-or-uncertain', 'approval_sha256': APPROVAL_SHA,
        'resource_request_sha256': REQUEST_SHA,
        'source_commit': '612d1ea9e4905dfe2af104696924a19bc5883752',
        'command': command, 'process': process, 'automatic_retry': False,
        'wrapper_source_changed': False, 'remote_ledger_reconciliation_required_on_uncertain_submit': True,
    }
    if process['reason'] == 'exited' and process['returncode'] == 0:
        try:
            result = json.loads(process['stdout'])
            expected = 'test-only' if args.mode == 'test-only' else 'submitted'
            assert result['status'] == expected and result['automatic_retry'] is False
            if args.mode == 'submit':
                assert result['reserved_gpu_seconds'] == 900 and result['maximum_concurrent_gpus'] == 1
            record.update(status='passed', result=result)
        except (ValueError, KeyError, TypeError, AssertionError) as error:
            record['parse_error'] = type(error).__name__ + ': ' + str(error)
    receipt = write(ARCHIVE / (stem + '.json'), record)
    print(json.dumps({'status': record['status'], 'receipt': receipt, 'result': record.get('result'),
                      'stderr': process['stderr'], 'automatic_retry': False}, sort_keys=True))
    return 0 if record['status'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
