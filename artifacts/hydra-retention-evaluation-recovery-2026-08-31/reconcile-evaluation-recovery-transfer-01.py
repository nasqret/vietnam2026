#!/usr/bin/env python3
"""One new read-only reconciliation of the actual failed recovery transfer.

This does not retry, reupload, repair or reclassify that failed transfer. It uses
the unchanged sender bounded() transport only for an inspection JSON request.
The remote program has a zero file-size limit and a read-only audit guard.
Only a fresh local reconciliation directory is written. Importing this module
does not contact the server; validate_record() is local read/hash validation.
"""
import time
STARTED = time.monotonic()
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import resource
import shlex
import signal
import stat
import struct
import sys
import types

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
HELPER = ARCHIVE / 'reconcile-evaluation-recovery-transfer-01.py'
REMOTE_HELPER = ARCHIVE / 'reconcile-evaluation-recovery-transfer-01-remote.py'
REMOTE_HELPER_SHA = '79744f1ac012d47d1fe2a234b617e9cadb5072116a1220706f9e8b6dd52e44a5'
SENDER = ARCHIVE / 'transfer-evaluation-recovery-01.py'
SENDER_SHA = '1ca738064b8be3526dec4ec3b301b8ecaec9b9580344ab32692a56f61f658618'
RECEIVER = ARCHIVE / 'transfer-evaluation-recovery-remote-01.py'
RECEIVER_SHA = '50ed89b1f564e179e02a64aa881c099f98c869b475c2a07a8df8733a6078a3a8'
ORIGINAL = ARCHIVE / 'source-transfer-01'
OUTPUT = ARCHIVE / 'installation-reconciliation-01'
OUTPUT_NAMES = frozenset(('started.json', 'request.json', 'ssh-process.json', 'reconciliation-result.json'))
SCHEMA = 'peano-hydra-retention-evaluation-recovery-installation-reconciliation-v1'
FIXED = {
    'failed_send': (ORIGINAL / 'send-result.json', 2812,
        '0f8037a34bf68cc13a40a71a68482b86745cd571e7ca37235fc86f119b55fad3'),
    'prepared_plan': (ORIGINAL / 'prepared-plan.json', 2974,
        '0fdc0b4f7debd71dac6a21c05c0659cab94e6f8d319fb7ed9e7ca313834b87fa'),
    'plan': (ARCHIVE / 'transfer-plan-01.json', 295448,
        '7ca53ddc3a771dc300ab6f5c464002d8172e8ed6e3cbd7547ebcbb5451bd133d'),
    'send_header': (ORIGINAL / 'send-header.json', 1037,
        '2453224570abe54b2394f7ef83f14dc8d00b3558c3935738f1e235853a08a623'),
    'prepare_result': (ORIGINAL / 'prepare-result.json', 691,
        '3d1a6251776f7f28fded9424428c5b5639daa4feb3d689b5a53c99009294c38c'),
    'original_ssh_process': (ORIGINAL / 'ssh-process.json', 1969,
        '2ff57426e2a75bc973401815597fb431bf675cefdf054570e0c6fcc5283082e7'),
    'original_send_started': (ORIGINAL / 'send-started.json', 182,
        '74a27617f9f1536235136eb25304d99277759bb044fd4cdcfa2db300d70ba223'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_bootstrap(path, maximum=65536):
    require(path.is_absolute() and path.parent.resolve() == path.parent and not path.is_symlink(),
            'fixed nonsymlink reviewed helper path required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= maximum,
                'bounded single-link reviewed helper required')
        raw = bytearray()
        while True:
            part = os.read(fd, min(65536, maximum + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
            require(len(raw) <= maximum, 'reviewed helper grew past cap')
        after = os.fstat(fd)
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                and len(raw) == before.st_size, 'reviewed helper changed during read')
    finally:
        os.close(fd)
    observed = path.lstat()
    require((observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns) ==
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns),
            'reviewed helper path changed')
    return bytes(raw)


def bootstrap():
    sender_raw, remote_raw = read_bootstrap(SENDER), read_bootstrap(REMOTE_HELPER)
    require(pin(sender_raw)['sha256'] == SENDER_SHA and pin(remote_raw)['sha256'] == REMOTE_HELPER_SHA,
            'unchanged sender or reviewed read-only helper pin differs')
    sender = types.ModuleType('_original_recovery_transfer_bounded_transport')
    sender.__file__ = str(SENDER)
    exec(compile(sender_raw, str(SENDER), 'exec'), sender.__dict__)
    remote = types.ModuleType('_recovery_installation_reconciliation_protocol')
    remote.__file__ = str(REMOTE_HELPER)
    exec(compile(remote_raw, str(REMOTE_HELPER), 'exec'), remote.__dict__)
    require(pin(sender.RECEIVER_RAW) == {'bytes': 34678, 'sha256': RECEIVER_SHA},
            'actual unchanged receiver source differs')
    return sender, remote, sender_raw, remote_raw


def external_pins(expected_helper_sha256, expected_failed_send_sha256,
                  expected_prepared_plan_sha256, expected_plan_sha256, expected_send_header_sha256):
    values = {'helper': expected_helper_sha256, 'failed_send': expected_failed_send_sha256,
        'prepared_plan': expected_prepared_plan_sha256, 'plan': expected_plan_sha256,
        'send_header': expected_send_header_sha256}
    require(all(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
                for value in values.values()), 'actual external helper/evidence raw pins required')
    require(all(values[key] == FIXED[key][2] for key in values if key != 'helper'),
            'this reconciliation belongs only to the preserved failed transfer')
    require(pin(read_bootstrap(HELPER))['sha256'] == values['helper'], 'externally reviewed local helper changed')
    return values


def context(sender, remote, expected_helper_sha256):
    r = sender.r
    raws, descriptors = {}, {}
    for name, (path, size, expected) in FIXED.items():
        raw = sender.read_file(path, r.MAX_JSON)
        require(pin(raw) == {'bytes': size, 'sha256': expected}, 'preserved original evidence changed: ' + name)
        raws[name], descriptors[name] = raw, {'path': str(path), **pin(raw)}
    program = 'RECEIVER_SOURCE = ' + repr(sender.RECEIVER_RAW.decode('utf-8')) + '\n' + \
        sender.read_file(REMOTE_HELPER, 65536).decode('utf-8') + '\nmain(RECEIVER_SOURCE)\n'
    request = {'schema': remote.REQUEST_SCHEMA, 'source_commit': remote.COMMIT,
        'helper_sha256': expected_helper_sha256, 'remote_helper_sha256': REMOTE_HELPER_SHA,
        'remote_program_sha256': r.sha(program.encode('utf-8')),
        **{name + '_json': raws[name].decode('utf-8') for name in ('failed_send', 'prepared_plan', 'plan', 'send_header')},
        'metadata_only_request': True, 'limits': r.LIMITS}
    plan, prepared, header, provenance, durable, durable_raw = remote.evidence(r, request)
    require(prepared == sender.prepared_record(plan, raws['plan'], prepared['source'], prepared['tar_validation']),
            'original preparation does not match its unchanged actual source/transport metadata')
    prepare_result = r.decode(raws['prepare_result'])
    failed, process = r.decode(raws['failed_send']), r.decode(raws['original_ssh_process'])
    require(prepare_result['status'] == 'prepared-local-only'
        and prepare_result['prepared_plan'] == descriptors['prepared_plan']
        and failed['ssh_process'] == process
        and r.decode(raws['original_send_started'])['prepared_plan_sha256'] == remote.PREPARED_SHA,
        'original start/preparation/process evidence no longer joins the actual failure')
    # These are reference/control metadata reads, not a scientific admission or
    # a claim to have verified external model/ancestor inputs.
    names = sorted(set(plan['bootstrap_files']) | {r.FREEZE_RECEIPT, r.ORIGIN_MANIFEST})
    metadata = {}
    for name in names:
        raw = sender.read_file(Path(r.LOCAL_ROOT) / name, r.MAX_FREEZE)
        item = plan['selected_files'][name]
        require(pin(raw) == {key: item[key] for key in ('bytes', 'sha256')},
                'local approved reference/control metadata changed: ' + name)
        metadata[name] = pin(raw)
        if name == r.FREEZE_RECEIPT:
            r.validate_freeze(plan, raw)
        elif name == r.AUTHORITY:
            r.validate_authority(plan, raw)
    for name, path, expected in (('sender', SENDER, SENDER_SHA), ('receiver', RECEIVER, RECEIVER_SHA),
            ('remote_helper', REMOTE_HELPER, REMOTE_HELPER_SHA), ('helper', HELPER, expected_helper_sha256)):
        actual = pin(sender.read_file(path, 65536))
        require(actual['sha256'] == expected, 'reviewed reconciliation dependency changed: ' + name)
        descriptors[name] = {'path': str(path), **actual}
    return {'request': request, 'program': program, 'plan': plan, 'prepared': prepared,
        'header': header, 'provenance': provenance, 'durable': durable, 'durable_raw': durable_raw,
        'descriptors': descriptors, 'local_reference_metadata': metadata}


def ssh_command(r, program, request_sha):
    remote = shlex.join(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin',
        '/usr/bin/python3.9', '-I', '-B', '-c', program, request_sha])
    require(len(remote.encode('utf-8')) <= 120000, 'inline read-only program exceeds fixed command bound')
    return ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', r.HOST, remote]


def validate_remote(r, remote, value, ctx, request_sha):
    require(type(value) is dict and value.get('schema') == remote.SCHEMA
        and value.get('status') == 'installed-state-verified-read-only'
        and value['request_sha256'] == request_sha and value['limits'] == r.LIMITS
        and value['read_only'] is True and value['remote_file_size_limit_bytes'] == 0
        and value['forbidden_attempts'] == [] and all(value[key] is False for key in remote.NO_WORK),
        'actual successful read-only remote inspection required')
    for key in ('helper_sha256', 'remote_helper_sha256', 'remote_program_sha256'):
        require(value[key] == ctx['request'][key], 'remote reviewed program/request identity changed')
    require(value['source_commit'] == remote.COMMIT and value['remote_root'] == r.REMOTE_ROOT
        and value['plan_sha256'] == remote.PLAN_SHA and value['prepared_plan_sha256'] == remote.PREPARED_SHA
        and value['failed_send_sha256'] == remote.FAILED_SHA and value['send_header_sha256'] == remote.HEADER_SHA
        and value['send_header_wire_sha256'] == remote.HEADER_WIRE_SHA
        and value['transfer_started_at_utc'] == remote.STAMP
        and value['source_provenance'] == ctx['provenance'].decode('ascii')
        and value['source_provenance_sha256'] == r.sha(ctx['provenance'])
        and value['original_transfer_status'] == 'failed-no-automatic-retry'
        and value['original_transfer_returncode'] == 2,
        'reconciliation replaced original failed-transfer or source/provenance identity')
    for key in ('source_files_sha256', 'bootstrap_files_sha256', 'selected_files_sha256'):
        require(value[key] == ctx['plan'][key], 'installed inventory digest changed: ' + key)
    optional = value['durable_receipt']
    require(type(optional) is dict and type(optional.get('present')) is bool
        and optional.get('path') == r.REMOTE_RECEIPT
        and set(optional) == ({'present', 'path', 'bytes', 'sha256'} if optional['present'] else {'present', 'path'}),
        'actual original durable-receipt presence must be explicit')
    actual_receipt = None
    if optional['present']:
        require({key: optional[key] for key in ('bytes', 'sha256')} == pin(ctx['durable_raw']),
                'existing original durable receipt differs from the exact pure expected bytes')
        actual_receipt = {key: optional[key] for key in ('path', 'bytes', 'sha256')}
    files = ctx['durable']['files']
    metadata_names = set(ctx['plan']['bootstrap_files']) | {r.FREEZE_RECEIPT, r.ORIGIN_MANIFEST, r.PROVENANCE}
    metadata = {name: files[name] for name in metadata_names}
    if optional['present']:
        metadata[r.REMOTE_RECEIPT] = pin(ctx['durable_raw'])
    dirs = remote.parent_directories(files)
    require(value['input_file_count'] == len(files) == 908 and value['input_total_bytes'] == 92999725
        and value['file_count'] == 908 + int(optional['present'])
        and value['total_bytes'] == 92999725 + (len(ctx['durable_raw']) if optional['present'] else 0)
        and value['files_sha256'] == ctx['durable']['files_sha256']
        and value['private_modes_sha256'] == r.sha(r.canonical(ctx['durable']['private_modes']))
        and value['directory_count'] == len(dirs) and value['directory_names_sha256'] == r.sha(r.canonical(sorted(dirs)))
        and value['metadata_files_rehashed'] == len(metadata)
        and value['metadata_sha256'] == r.sha(r.canonical(metadata)), 'actual complete installed inventory differs')
    for key in ('exact_inventory_checked', 'all_file_hashes_rechecked', 'metadata_rehashed_before_and_after',
                'paths_and_modes_unchanged', 'single_link_regular_files', 'nonsymlink_directory_chain',
                'resource_request_present', 'approval_present'):
        require(value[key] is True, 'installed-state check omitted a required boundary: ' + key)
    remote.check_measurements(r, value)
    require('error' not in value, 'remote read-only inspection retained an error')
    return actual_receipt


def new_json(r, name, record):
    require(name in OUTPUT_NAMES, 'unapproved local reconciliation output name')
    raw = r.canonical(record) + b'\n'
    require(len(raw) <= r.LIMITS['receipt_file_bytes'], 'local reconciliation receipt byte bound')
    parent = r.directory(str(OUTPUT))
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return {'path': str(OUTPUT / name), **pin(raw)}


def measurements():
    own, child = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'cpu_seconds': own.ru_utime + own.ru_stime + child.ru_utime + child.ru_stime,
        'parent_cpu_seconds': own.ru_utime + own.ru_stime,
        'reaped_child_cpu_seconds': child.ru_utime + child.ru_stime,
        'wall_seconds': time.monotonic() - STARTED,
        'peak_rss_bytes': int(own.ru_maxrss * (1 if sys.platform == 'darwin' else 1024))}


def check_local(values):
    require(type(values) is dict and set(values) == {'cpu_seconds', 'parent_cpu_seconds',
        'reaped_child_cpu_seconds', 'wall_seconds', 'peak_rss_bytes'}
        and all(type(item) in (int, float) and math.isfinite(item) and item >= 0 for item in values.values())
        and values['cpu_seconds'] < 60 and values['wall_seconds'] < 90
        and 0 < values['peak_rss_bytes'] <= 512 * 1024**2,
        'local read-only reconciliation whole-call CPU/wall/RSS boundary')


def validate_record(record, expected_helper_sha256, expected_failed_send_sha256,
                    expected_prepared_plan_sha256, expected_plan_sha256, expected_send_header_sha256):
    """Local reads/hash checks only; no gate, subprocess, network or main call."""
    external_pins(expected_helper_sha256, expected_failed_send_sha256,
                  expected_prepared_plan_sha256, expected_plan_sha256, expected_send_header_sha256)
    sender, remote, _, _ = bootstrap()
    r = sender.r
    ctx = context(sender, remote, expected_helper_sha256)
    require(type(record) is dict and record.get('schema') == SCHEMA
        and record.get('status') == 'installed-state-verified-read-only' and record.get('error') is None
        and record['source_commit'] == remote.COMMIT and record['profile'] == r.PROFILE and record['run_id'] == r.RUN_ID
        and record['output_directory'] == str(OUTPUT) and record['limits'] == r.LIMITS
        and record['network_contacted'] is True and record['original_transfer_status'] == 'failed-no-automatic-retry'
        and record['original_transfer_returncode'] == 2 and record['original_transfer_attempt_untouched'] is True
        and all(record[key] is False for key in remote.NO_WORK), 'successful distinct read-only reconciliation required')
    for name, item in ctx['descriptors'].items():
        require(record[name] == item, 'actual original evidence/helper descriptor differs: ' + name)
    require(record['send_header_wire_sha256'] == remote.HEADER_WIRE_SHA
        and record['local_reference_metadata_before'] == record['local_reference_metadata_after'] == ctx['local_reference_metadata']
        and record['local_evidence_unchanged'] is True and record['metadata_only_request_sent'] is True,
        'actual local original evidence changed through the read-only inspection')
    own_files = {}
    for key, name in (('request_file', 'request.json'), ('started_file', 'started.json'), ('ssh_process_file', 'ssh-process.json')):
        actual = sender.read_file(OUTPUT / name, r.LIMITS['receipt_file_bytes'])
        require(record[key] == {'path': str(OUTPUT / name), **pin(actual)}, 'actual local reconciliation record changed')
        own_files[name] = r.decode(actual, r.LIMITS['receipt_file_bytes'])
    require(own_files['request.json'] == ctx['request'], 'actual read-only request changed')
    request_raw = r.canonical(ctx['request']) + b'\n'
    wire = struct.pack('>Q', len(request_raw)) + request_raw
    started, process = own_files['started.json'], own_files['ssh-process.json']
    command = ssh_command(r, ctx['program'], r.sha(request_raw))
    require(started['schema'] == SCHEMA and started['status'] == 'read-only-attempt-started'
        and started['original_transfer_status'] == 'failed-no-automatic-retry'
        and started['failed_send_sha256'] == remote.FAILED_SHA
        and started['request_sha256'] == r.sha(request_raw)
        and started['ssh_command_sha256'] == r.sha(r.canonical(command))
        and started['metadata_only_wire_bytes'] == len(wire)
        and all(started[key] is False for key in remote.NO_WORK), 'one-use local inspection start differs')
    require(record['request_sha256'] == r.sha(request_raw)
        and record['remote_program_sha256'] == ctx['request']['remote_program_sha256']
        and record['ssh_process'] == process and process['reason'] == 'exited'
        and process['returncode'] == 0 and process['error'] is None
        and process['wire_bytes_sent'] == len(wire) and process['sent_compressed_sha256'] == r.sha(wire)
        and type(process['wall_seconds']) in (int, float) and 0 <= process['wall_seconds'] < 60
        and type(process['reaped_child_cpu_delta_seconds']) in (int, float)
        and 0 <= process['reaped_child_cpu_delta_seconds'] < 60
        and len(process['stdout'].encode('utf-8')) <= 65536 and len(process['stderr'].encode('utf-8')) <= 65536,
        'actual unchanged bounded SSH process did not finish successfully')
    observed = r.decode(process['stdout'].encode('utf-8'), 65536)
    require(record['remote'] == observed and process['stdout'].encode('utf-8') == r.canonical(observed) + b'\n',
            'actual remote stdout does not match the reconciliation observation')
    require(record['remote_control_receipt'] == validate_remote(r, remote, observed, ctx, r.sha(request_raw)),
            'optional original durable-receipt descriptor changed')
    require(record['ssh_transport_body_kind'] == 'bounded-inspection-json-not-an-archive'
        and record['whole_call_completion_requires'] == 'successful reconciliation record AND actual local owner exit zero',
        'reconciliation inflated its transfer or completion claim')
    check_local(record['accounting'])
    require(context(sender, remote, expected_helper_sha256) == ctx, 'reference evidence changed during local validation')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ('helper-sha256', 'failed-send-sha256', 'prepared-plan-sha256', 'plan-sha256', 'send-header-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and Path(__file__).absolute() == HELPER
        and not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
        'fixed isolated metadata-only caller outside allocations required')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def deadline(*_):
        raise TimeoutError('local installation reconciliation90-second wall deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 90 - (time.monotonic() - STARTED)))
    external_pins(args.helper_sha256, args.failed_send_sha256, args.prepared_plan_sha256,
                  args.plan_sha256, args.send_header_sha256)
    sender, remote, _, _ = bootstrap()
    r = sender.r
    ctx = context(sender, remote, args.helper_sha256)
    request_raw = r.canonical(ctx['request']) + b'\n'
    require(len(request_raw) <= r.MAX_JSON, 'bounded metadata-only request required')
    wire = struct.pack('>Q', len(request_raw)) + request_raw
    command = ssh_command(r, ctx['program'], r.sha(request_raw))
    parent = r.directory(str(ARCHIVE))
    try:
        os.mkdir(OUTPUT.name, 0o700, dir_fd=parent)
    finally:
        os.close(parent)
    request_file = new_json(r, 'request.json', ctx['request'])
    started_file = new_json(r, 'started.json', {'schema': SCHEMA, 'status': 'read-only-attempt-started',
        'started_at_utc': r.utc(), 'original_transfer_status': 'failed-no-automatic-retry',
        'failed_send_sha256': remote.FAILED_SHA, 'request_sha256': r.sha(request_raw),
        'ssh_command_sha256': r.sha(r.canonical(command)), 'metadata_only_wire_bytes': len(wire), **remote.NO_WORK})
    result = {'schema': SCHEMA, 'status': 'failed-read-only-reconciliation', 'error': None,
        'source_commit': remote.COMMIT, 'profile': r.PROFILE, 'run_id': r.RUN_ID,
        'output_directory': str(OUTPUT), 'limits': r.LIMITS, 'network_contacted': False,
        **ctx['descriptors'], 'original_transfer_status': 'failed-no-automatic-retry',
        'original_transfer_returncode': 2, 'original_transfer_attempt_untouched': True,
        'send_header_wire_sha256': remote.HEADER_WIRE_SHA,
        'request_file': request_file, 'started_file': started_file, 'ssh_process_file': None,
        'request_sha256': r.sha(request_raw), 'remote_program_sha256': ctx['request']['remote_program_sha256'],
        'local_reference_metadata_before': ctx['local_reference_metadata'], 'local_reference_metadata_after': None,
        'local_evidence_unchanged': False, 'metadata_only_request_sent': False,
        'ssh_process': None, 'remote': None, 'remote_control_receipt': None,
        'ssh_transport_body_kind': 'bounded-inspection-json-not-an-archive',
        'whole_call_completion_requires': 'successful reconciliation record AND actual local owner exit zero', **remote.NO_WORK}
    code = 2
    try:
        check_local(measurements())
        result['network_contacted'] = True
        # Preserve the original bounded() function and child RLIMIT_FSIZE=0.
        # Its legacy body-hash field is retained verbatim; this body is JSON,
        # never a compressed archive or any installed project file.
        process = sender.bounded(command, timeout=60, prefix=b'',
            bundle_stream=io.BytesIO(wire), bundle=pin(wire))
        result.update(ssh_process=process, ssh_process_file=new_json(r, 'ssh-process.json', process))
        after = context(sender, remote, args.helper_sha256)
        require(after == ctx, 'actual local evidence changed during read-only reconciliation')
        result.update(local_reference_metadata_after=after['local_reference_metadata'], local_evidence_unchanged=True)
        require(process['reason'] == 'exited' and process['returncode'] == 0 and process['error'] is None,
                'actual read-only SSH inspection failed; no retry or repair')
        observed = r.decode(process['stdout'].encode('utf-8'), 65536)
        result.update(remote=observed,
            remote_control_receipt=validate_remote(r, remote, observed, ctx, r.sha(request_raw)),
            metadata_only_request_sent=True, status='installed-state-verified-read-only', accounting=measurements())
        validate_record(result, args.helper_sha256, args.failed_send_sha256,
                        args.prepared_plan_sha256, args.plan_sha256, args.send_header_sha256)
        check_local(measurements())
        code = 0
    except BaseException as error:
        result.update(status='failed-read-only-reconciliation', error=(type(error).__name__ + ': ' + str(error))[:2048])
    result.update(finished_at_utc=r.utc(), accounting=measurements())
    if code == 0:
        check_local(result['accounting'])
    output = new_json(r, 'reconciliation-result.json', result)
    if code == 0:
        check_local(measurements())
        require(sender.read_file(OUTPUT / 'reconciliation-result.json', r.LIMITS['receipt_file_bytes']) ==
                r.canonical(result) + b'\n', 'fresh reconciliation receipt changed during final readback')
    print(r.canonical({'status': result['status'], 'receipt': output,
        'original_transfer_status': 'failed-no-automatic-retry', 'error': result['error']}).decode(), flush=True)
    if code == 0:
        check_local(measurements())
    signal.setitimer(signal.ITIMER_REAL, 0)
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TypeError, KeyError, RuntimeError, TimeoutError, KeyboardInterrupt) as error:
        print('installation-reconciliation: ' + ' '.join(str(error).split())[:2048], file=sys.stderr, flush=True)
        raise SystemExit(2)
