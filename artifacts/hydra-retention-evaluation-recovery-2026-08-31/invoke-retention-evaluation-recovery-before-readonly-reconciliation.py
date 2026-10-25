#!/usr/bin/env python3
"""Invoke only the new frozen evaluation-only gate through the reviewed transport.

The genuine frozen gate owns all resource reservation, held validation and release.
Transfer success alone is never treated as successful gate validation. Only evaluate is supported, with one exclusive local attempt per mode. A submit
also requires its successful raw-pinned test-only receipt. Any uncertain submit
must be reconciled against the original remote ledger, never retried here.
"""
import time
STARTED = time.monotonic()
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shlex
import signal
import stat
import sys

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
HELPER = ARCHIVE / 'invoke-retention-evaluation-recovery-01.py'
FROZEN = ARCHIVE.parents[1] / '_deploy/hydra-retention-evaluation-recovery-execution-20260831'
REMOTE_ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-evaluation-recovery-v1'
PRODUCER_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
PROFILE, RUN_ID = 'peano-hydra-retention-evaluation-recovery-v1', 'retention-evaluation-recovery-v1'
PACKAGE = '_deploy/hydra-retention-evaluation-recovery-v1'
GATE = 'training/peano_hydra/retention_evaluation_recovery_launch.py'
TRANSPORT = ARCHIVE / 'transfer-evaluation-recovery-01.py'
TRANSPORT_SHA = '1ca738064b8be3526dec4ec3b301b8ecaec9b9580344ab32692a56f61f658618'
CONTROLS = ARCHIVE / 'source-transfer-01/send-result.json'
CONTROL_RECEIPT = '.peano-retention-evaluation-recovery-transfer-receipt.json'
BOOTSTRAP_SOURCES = {
    'training/peano_hydra/__init__.py': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    GATE: 'dfe56aef1ba17c1fa49473858070d89d6e34bd5f0b0316351546cf5d2e14e88d',
    'training/peano_hydra/search_launch.py': '3d393ceb547c5199297748af647c7c6c51c67bf176011dcd68b257dc6d3f97ca',
}
MODEL_MANIFEST = {'bytes': 191597, 'sha256': 'cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca'}
PRODUCER = {
    'source_commit': PRODUCER_COMMIT, 'training_job_id': '21456251', 'failed_evaluation_job_id': '21457058',
    'model_manifest': MODEL_MANIFEST,
    'approval_sha256': '556cef2186a2003bf90ea327b927cc6cb3ea6ec0bd57f65e421bb6841e74d233',
    'resource_request_sha256': '67e0be409cf42ac90048029632479328e9b98b19c4f44f637f1fab6b5392f361',
    'source_header_sha256': '224ad02b154eb32a64e07cfd02710f81020cb4b108c83d6514b2dcf918802333',
    'training_ledger_sha256': '3d1b5fa3114c4e7bbe0cbb7f6fee526bd46ecc99bd9a470aefcdd0b95e53ecb6',
    'failed_evaluation_ledger_sha256': 'acdde37ddabdca99602b937939ba33848ba2946fa104367595ceb71a086049b3',
    'reserved_gpu_seconds': 10800, 'reservations_fully_consumed': True, 'reservation_reuse_allowed': False, 'refunds': False,
}
RESERVATIONS = {'evaluate': {'seconds': 3600, 'gpus': 1, 'cpus': 8, 'memory_gib': 64}}
MAX_JSON, CPU, WALL = 4 * 1024**2, 60, 120


def require(value, message):
    if not value: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, 'bounded JSON metadata required')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate metadata key'); result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(result) is dict, 'metadata object required')
    canonical(result)
    return result


def load_transport():
    require(TRANSPORT.parent.resolve() == ARCHIVE and not TRANSPORT.is_symlink(), 'fixed transport path required')
    fd = os.open(TRANSPORT, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 65536,
                'bounded single-link transport source required')
        raw = os.read(fd, 65537)
        after = os.fstat(fd)
        require(len(raw) == before.st_size and sha(raw) == TRANSPORT_SHA
                and (before.st_mtime_ns, before.st_ctime_ns) == (after.st_mtime_ns, after.st_ctime_ns),
                'reviewed bounded transport changed')
    finally: os.close(fd)
    spec = importlib.util.spec_from_loader('retention_launch_bounded_transport', loader=None)
    module = importlib.util.module_from_spec(spec); module.__file__ = str(TRANSPORT)
    exec(compile(raw, str(TRANSPORT), 'exec'), module.__dict__)
    return module


def limits():
    own, waited = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    value = {'whole_wall_seconds': time.monotonic() - STARTED,
             'parent_and_waited_child_cpu_seconds': own.ru_utime + own.ru_stime + waited.ru_utime + waited.ru_stime,
             'parent_peak_rss_bytes': own.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)}
    require(value['whole_wall_seconds'] < WALL and value['parent_and_waited_child_cpu_seconds'] < CPU
            and value['parent_peak_rss_bytes'] <= 384 * 1024**2, 'launch caller resource envelope reached')
    return value


def new_json(b, path, value):
    require(path.parent == ARCHIVE and re.fullmatch(r'launch-evaluate-(test-only|submit)-01(?:\.started)?\.json', path.name),
            'launch receipt outside its exact fresh archive names')
    raw = canonical(value) + b'\n'
    require(len(raw) <= MAX_JSON, 'launch receipt byte cap')
    parent = b.r.directory(str(ARCHIVE))
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.fsync(parent)
    finally: os.close(parent)
    require(b.read_file(path, MAX_JSON) == raw, 'launch receipt publication changed bytes')
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def control_context(b, expected_transfer, approval_sha, header_sha, commit):
    """Join actual nonexecuting transfer evidence; gate checks still run next."""
    raw = b.read_file(CONTROLS, MAX_JSON)
    require(sha(raw) == expected_transfer, 'actual recovery transfer receipt differs from external pin')
    sent = decode(raw)
    require(sent.get('schema') == 'peano-hydra-retention-evaluation-recovery-transfer-send-result-v1'
            and sent.get('status') == 'transferred-and-rehashed' and sent.get('network_contacted') is True
            and sent.get('local_inputs_rechecked') is True and sent.get('job_submitted') is False
            and sent.get('automatic_retry') is False
            and sent.get('external_remote_source_and_model_inputs_verified') is False,
            'successful nonlaunching actual recovery transfer is required')
    process, remote = sent['ssh_process'], sent['remote']
    require(process['reason'] == 'exited' and process['returncode'] == 0 and process['error'] is None
            and decode(process['stdout'].encode()) == remote
            and remote['schema'] == 'peano-hydra-retention-evaluation-recovery-transfer-remote-result-v1'
            and remote['status'] == 'transferred-and-rehashed' and remote['remote_root'] == REMOTE_ROOT
            and remote['source_commit'] == commit, 'actual remote transfer source/result differs')
    for key in ('exact_inventory_checked', 'all_file_hashes_rechecked', 'resource_request_present', 'approval_present'):
        require(remote.get(key) is True, 'actual transfer byte check missing: ' + key)
    for key in ('job_submission_performed', 'installation_performed', 'model_loaded', 'native_work_performed'):
        require(remote.get(key) is False, 'transfer performed unexpected work')
    plan_raw = b.read_file(b.PLAN, MAX_JSON)
    plan = b.r.validate_plan(plan_raw, remote['plan_sha256'])
    require(plan['source_commit'] == commit and commit != PRODUCER_COMMIT, 'new frozen evaluation source required')
    freeze_raw = b.read_file(FROZEN / plan['freeze_receipt']['path'], MAX_JSON)
    frozen = b.r.validate_freeze(plan, freeze_raw)
    header_path = ARCHIVE / 'source-transfer-01/send-header.json'
    header_raw = b.read_file(header_path, MAX_JSON)
    require(sent['send_header'] == {'path': str(header_path), 'bytes': len(header_raw), 'sha256': sha(header_raw)},
            'actual transfer header descriptor changed')
    header = decode(header_raw)
    b.r.validate_header(header, plan)
    require(header['sender_sha256'] == TRANSPORT_SHA and header['receiver_sha256'] == b.RECEIVER_SHA
            and sha(canonical(header)) == sent['send_header_wire_sha256'] == remote['header_sha256'],
            'reviewed transport or actual wire header changed')
    provenance = remote['source_provenance'].encode('ascii')
    require(provenance == (commit + '\tfalse\t' + remote['transfer_started_at_utc'] + '\n').encode('ascii')
            and len(provenance) <= b.r.MAX_PROVENANCE and sha(provenance) == remote['source_provenance_sha256'],
            'actual remote source provenance changed')
    durable = b.r.receipt_record(plan, header, remote['header_sha256'], remote['transfer_started_at_utc'], provenance, remote['bundle'])
    durable_raw = canonical(durable) + b'\n'
    require(remote['remote_receipt'] == {'path': CONTROL_RECEIPT, 'bytes': len(durable_raw), 'sha256': sha(durable_raw)}
            and remote['files_sha256'] == durable['files_sha256'], 'durable actual transfer receipt changed')
    approval_raw = b.read_file(FROZEN / PACKAGE / 'approval.json', MAX_JSON)
    request_raw = b.read_file(FROZEN / PACKAGE / 'resource-request.json', MAX_JSON)
    approval, request = decode(approval_raw), decode(request_raw)
    require(sha(approval_raw) == approval_sha and sha(request_raw) == approval['request_file_sha256']
            and approval['schema'] == 'peano-hydra-retention-evaluation-recovery-standing-resource-approval-v1'
            and approval['profile'] == PROFILE and approval['run_id'] == RUN_ID and approval['approved'] is True
            and request['schema'] == 'peano-hydra-retention-evaluation-recovery-resource-request-v1'
            and request['profile'] == PROFILE and request['run_id'] == RUN_ID and request['source_commit'] == commit
            and request['producer'] == PRODUCER and request['model_manifest'] == MODEL_MANIFEST
            and request['reservations'] == RESERVATIONS and set(request['scientific_inputs']) == {'evaluate'}
            and request['maximum_aggregate_gpu_seconds'] == 3600 and request['maximum_concurrent_gpus'] == 1
            and all(request[key] is False for key in ('automatic_retry', 'resume', 'refunds', 'training_authorized', 'historical_checkpoint_reuse_allowed')),
            'local resource approval changed exact new evaluation or preserved producer scope')
    def raw_inventory(mapping):
        return {name: {key: item[key] for key in ('bytes', 'sha256')} for name, item in mapping.items()}
    sources = raw_inventory(frozen['files'])
    payloads = {name: item for name, item in raw_inventory(plan['bootstrap_files']).items()
                if name not in (PACKAGE + '/resource-request.json', PACKAGE + '/approval.json')}
    require(request['source_files'] == sources and request['payloads'] == payloads
            and request['payloads_sha256'] == sha(canonical(payloads)),
            'source and control inventories differ from actual frozen/transferred bytes')
    for name, content in ((PACKAGE + '/approval.json', approval_raw), (PACKAGE + '/resource-request.json', request_raw)):
        require(raw_inventory(plan['bootstrap_files'])[name] == {'bytes': len(content), 'sha256': sha(content)},
                'actual uploaded raw control differs from local control')
    for relative, expected in BOOTSTRAP_SOURCES.items():
        content = b.read_file(FROZEN / relative, 65536)
        require(sha(content) == expected == sources[relative]['sha256']
                and len(content) == sources[relative]['bytes'], 'reviewed new gate bootstrap source changed')
    identity = {'approval_sha256': approval_sha, 'resource_request_sha256': sha(request_raw),
        'producer_sha256': sha(canonical(PRODUCER)),
        'historical_admission_sha256': request['historical_admission']['sha256'],
        'source_commit': commit, 'source_files_sha256': sha(canonical(sources)),
        'payloads_sha256': request['payloads_sha256'], 'synced_at': remote['transfer_started_at_utc'],
        'job_script_sha256': {'evaluate': sources['slurm/peano_hydra_retention_evaluation_recovery.sbatch']['sha256']}}
    require(sha(canonical(identity)) == header_sha, 'expected installed source header differs from actual provenance and controls')
    return {'transfer': {'path': str(CONTROLS), 'bytes': len(raw), 'sha256': sha(raw)},
            'identity': identity, 'source_header_sha256': header_sha,
            'remote_control_receipt': remote['remote_receipt'], 'scientific_inputs': request['scientific_inputs'],
            'reservations': request['reservations'], 'model_manifest': MODEL_MANIFEST,
            'producer': PRODUCER, 'transfer_did_not_execute_gate': True}


def validate_result(value, mode, stage):
    require(stage == 'evaluate' and value['stage'] == stage and value['automatic_retry'] is False,
            'only the new evaluation stage may be returned')
    if mode == 'test-only':
        require(value == {'status': 'test-only', 'stage': 'evaluate', 'reservation': RESERVATIONS['evaluate'],
            'allocation_performed': False, 'model_manifest': MODEL_MANIFEST, 'automatic_retry': False},
            'test-only altered the saved model or exact one-hour evaluation reservation')
    else:
        job = value.get('job_id')
        require(type(job) is str and re.fullmatch(r'[1-9][0-9]{0,19}', job)
                and job not in (PRODUCER['training_job_id'], PRODUCER['failed_evaluation_job_id']),
                'new evaluation cannot adopt either original spent job')
        require(value == {'status': 'submitted', 'profile': PROFILE, 'run_id': RUN_ID, 'stage': 'evaluate', 'job_id': job,
            'reserved_gpu_seconds': 3600, 'maximum_aggregate_gpu_seconds': 3600, 'maximum_concurrent_gpus': 1,
            'ledger': 'logs/hydra-retention-evaluation-recovery-v1-evaluate.jsonl',
            'output': 'results/peano-hydra/evaluations/retention-evaluation-recovery-v1',
            'automatic_retry': False, 'resume': False, 'refunds': False},
            'submitted job changed its independent evaluation reservation or output')
    return value


def prior_test(b, stage, expected_sha, context):
    path = ARCHIVE / ('launch-' + stage + '-test-only-01.json')
    raw = b.read_file(path, MAX_JSON)
    require(sha(raw) == expected_sha, 'submit requires its actual matching successful test-only raw receipt')
    record = decode(raw)
    require(record['schema'] == 'peano-hydra-retention-evaluation-recovery-launch-invocation-v1' and record['status'] == 'passed'
            and record['mode'] == 'test-only' and record['stage'] == stage
            and record['context'] == context and record['process']['reason'] == 'exited'
            and record['process']['returncode'] == 0 and record['automatic_retry'] is False,
            'submit test-only prerequisite changed stage/source/control identity or status')
    validate_result(record['result'], 'test-only', stage)
    require(decode(record['process']['stdout'].encode()) == record['result'], 'test-only result was not actual CLI output')
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def remote_body(mode, stage, context):
    identity = context['identity']
    checksum_files = {**BOOTSTRAP_SOURCES,
        PACKAGE + '/approval.json': identity['approval_sha256'],
        PACKAGE + '/resource-request.json': identity['resource_request_sha256'],
        CONTROL_RECEIPT: context['remote_control_receipt']['sha256']}
    checks = ''.join(expected + '  ' + name + '\n' for name, expected in sorted(checksum_files.items()))
    # This only compares the unchanged gate's real metadata output with the
    # exact installed identity. The following original CLI owns all launch work.
    checker = (
        'import hashlib,json,sys; m=json.load(sys.stdin); '
        'keys=("approval_sha256","resource_request_sha256","source_commit","source_files_sha256",'
        '"payloads_sha256","synced_at","job_script_sha256","producer_sha256","historical_admission_sha256"); '
        'raw=json.dumps({k:m[k] for k in keys},sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode(); '
        'ok=m.get("status")=="metadata-verified" and hashlib.sha256(raw).hexdigest()==sys.argv[1]; '
        'sys.exit(0 if ok else "installed source/header changed before launch")')
    gate_command = ['/usr/bin/python3.9', '-I', '-B', GATE, '--approval-sha256', identity['approval_sha256']]
    return '\n'.join([
        'set -euo pipefail', 'cd -- ' + shlex.quote(REMOTE_ROOT),
        'test "$(pwd -P)" = ' + shlex.quote(REMOTE_ROOT),
        "printf '%s' " + shlex.quote(checks) + ' | /usr/bin/sha256sum --check --status',
        'checked="$(' + shlex.join(gate_command + ['--check']) + ')"',
        "printf '%s' \"$checked\" | " + shlex.join(['/usr/bin/python3.9', '-I', '-B', '-c', checker, context['source_header_sha256']]),
        'exec ' + shlex.join(gate_command + ['--' + mode, stage, '--source-commit', identity['source_commit']]), ''])


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('mode', choices=('test-only', 'submit'))
    parser.add_argument('stage', choices=('evaluate',))
    parser.add_argument('--expected-helper-sha256', required=True)
    parser.add_argument('--expected-transfer-sha256', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--source-header-sha256', required=True)
    parser.add_argument('--expected-test-only-sha256')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
            and Path(__file__).absolute() == HELPER, 'exact isolated local launch invoker required')
    for key, value in vars(args).items():
        if key.endswith('sha256') and value is not None:
            require(re.fullmatch(r'[0-9a-f]{64}', value), 'external raw/semantic SHA256 required: ' + key)
    require(re.fullmatch(r'[0-9a-f]{40}', args.source_commit) and args.source_commit != PRODUCER_COMMIT, 'actual new frozen commit required')
    require((args.mode == 'submit') == (args.expected_test_only_sha256 is not None),
            'only submit requires an explicit successful test-only receipt pin')
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_JSON, MAX_JSON))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('whole launch invocation exceeded 120 seconds')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    b = load_transport()
    helper_raw = b.read_file(HELPER, 65536)
    require(sha(helper_raw) == args.expected_helper_sha256, 'reviewed local launch invoker changed')
    context = control_context(b, args.expected_transfer_sha256, args.approval_sha256, args.source_header_sha256, args.source_commit)
    test = prior_test(b, args.stage, args.expected_test_only_sha256, context) if args.mode == 'submit' else None
    stem = 'launch-' + args.stage + '-' + args.mode + '-01'
    start_path, result_path = ARCHIVE / (stem + '.started.json'), ARCHIVE / (stem + '.json')
    require(not os.path.lexists(start_path) and not os.path.lexists(result_path), 'stage/mode attempt already exists; no retry')
    record = {'schema': 'peano-hydra-retention-evaluation-recovery-launch-invocation-v1', 'status': 'failed-or-uncertain',
        'mode': args.mode, 'stage': args.stage, 'context': context,
        'helper_sha256': args.expected_helper_sha256, 'bounded_transport_sha256': TRANSPORT_SHA,
        'test_only_prerequisite': test, 'automatic_retry': False,
        'local_check': None, 'process': None, 'remote_command_started': False,
        'frozen_source_modified': False, 'zero_local_child_file_size_cap_retained': True,
        'remote_ledger_reconciliation_required_on_uncertain_submit': True,
        'limits': {'whole_wall_seconds': WALL, 'parent_cpu_seconds': CPU, 'child_cpu_seconds': 60,
                   'checked_parent_plus_waited_child_cpu_seconds': CPU, 'ssh_wall_seconds': 110,
                   'local_metadata_wall_seconds': 45, 'child_file_write_bytes': 0,
                   'ssh_stdout_bytes': b.r.LIMITS['ssh_stdout_bytes'], 'ssh_stderr_bytes': b.r.LIMITS['ssh_stderr_bytes']}}
    new_json(b, start_path, {**record, 'schema': 'peano-hydra-retention-evaluation-recovery-launch-invocation-start-v1',
                           'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    try:
        local_command = [sys.executable, '-I', '-B', str(FROZEN / GATE), '--check', '--local',
                         '--approval-sha256', args.approval_sha256]
        checked = b.bounded(local_command, timeout=min(45, WALL - 3 - limits()['whole_wall_seconds']))
        record['local_check'] = checked
        require(checked['reason'] == 'exited' and checked['returncode'] == 0 and checked['error'] is None,
                'the actual frozen local metadata check failed')
        metadata = decode(checked['stdout'].encode())
        require(metadata['status'] == 'metadata-verified' and metadata['synced_at'] is None
                and all(metadata.get(key) == value for key, value in context['identity'].items() if key != 'synced_at')
                and metadata['scientific_inputs'] == context['scientific_inputs'] and metadata['reservations'] == context['reservations'],
                'frozen local source/request controls differ from actual installed remote identity')
        body = remote_body(args.mode, args.stage, context)
        remote = shlex.join(['bash', '-l', '-c', body, 'hydra-retention-evaluation-recovery-approved-launch'])
        command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
            '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
            '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
            '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', 'plgnasqret@helios.cyfronet.pl', remote]
        record.update(command=command, remote_body_sha256=sha(body.encode()), remote_command_started=True)
        process = b.bounded(command, timeout=min(110, WALL - 3 - limits()['whole_wall_seconds']))
        record['process'] = process
        require(process['reason'] == 'exited' and process['returncode'] == 0 and process['error'] is None,
                'remote CLI failed or is uncertain; reconcile original ledger without retry')
        record['result'] = validate_result(decode(process['stdout'].encode()), args.mode, args.stage)
        require(control_context(b, args.expected_transfer_sha256, args.approval_sha256, args.source_header_sha256, args.source_commit) == context
                and b.read_file(HELPER, 65536) == helper_raw and sha(b.read_file(TRANSPORT, 65536)) == TRANSPORT_SHA,
                'local source/control/transport identity changed through invocation')
        record['measurements'] = limits()
        record['status'] = 'passed'
    except BaseException as failure:
        record['error'] = type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2048]
    record['recorded_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt = new_json(b, result_path, record)
    print(json.dumps({'status': record['status'], 'receipt': receipt, 'result': record.get('result'),
                      'error': record.get('error'), 'automatic_retry': False}, sort_keys=True), flush=True)
    limits(); signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if record['status'] == 'passed' else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError) as failure:
        print('retention-launch-invocation: ' + ' '.join(str(failure).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
