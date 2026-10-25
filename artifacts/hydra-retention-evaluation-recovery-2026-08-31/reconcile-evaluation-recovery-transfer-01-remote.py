"""Read existing installed bytes after the preserved failed transfer.

Definitions only until explicit main(). No received project code is imported or
executed. The original transfer's Tree/read/validation primitives stay unchanged.
An optional original durable receipt is compared with its expected bytes only;
this program never creates that receipt or changes the failed transfer status.
"""
import time
STARTED = time.monotonic()
import hashlib
import io
import json
import math
import os
import resource
import signal
import stat
import struct
import sys
import types

COMMIT = 'dca88930b59e3147a95d0234d804076ccf757a74'
SENDER_SHA = '1ca738064b8be3526dec4ec3b301b8ecaec9b9580344ab32692a56f61f658618'
RECEIVER_SHA = '50ed89b1f564e179e02a64aa881c099f98c869b475c2a07a8df8733a6078a3a8'
FAILED_SHA = '0f8037a34bf68cc13a40a71a68482b86745cd571e7ca37235fc86f119b55fad3'
PREPARED_SHA = '0fdc0b4f7debd71dac6a21c05c0659cab94e6f8d319fb7ed9e7ca313834b87fa'
PLAN_SHA = '7ca53ddc3a771dc300ab6f5c464002d8172e8ed6e3cbd7547ebcbb5451bd133d'
HEADER_SHA = '2453224570abe54b2394f7ef83f14dc8d00b3558c3935738f1e235853a08a623'
HEADER_WIRE_SHA = '4ddbe22c5e1b85b0b6297c4c1543c0e55b50a21ee498675cce3065b58a83f680'
STAMP = '2026-08-31T11:40:10Z'
REQUEST_SCHEMA = 'peano-hydra-retention-evaluation-recovery-installation-inspection-request-v1'
SCHEMA = 'peano-hydra-retention-evaluation-recovery-installation-inspection-v1'
NO_WORK = {'remote_files_written': False, 'durable_receipt_published': False,
    'archive_reuploaded': False, 'original_transfer_reclassified': False,
    'job_submission_performed': False, 'scheduler_work_performed': False,
    'project_code_executed': False, 'model_loaded': False, 'native_work_performed': False,
    'external_remote_source_and_model_inputs_verified': False,
    'automatic_retry': False, 'resume': False}


def load_receiver(raw):
    if type(raw) is not bytes or len(raw) != 34678 or hashlib.sha256(raw).hexdigest() != RECEIVER_SHA:
        raise ValueError('unchanged original receiver source required')
    module = types.ModuleType('_unchanged_recovery_transfer_read_primitives')
    exec(compile(raw, '<unchanged-recovery-transfer-read-primitives>', 'exec'), module.__dict__)
    return module


def raw_pin(r, raw):
    return {'bytes': len(raw), 'sha256': r.sha(raw)}


def evidence(r, request):
    fields = {'schema', 'source_commit', 'helper_sha256', 'remote_helper_sha256',
        'remote_program_sha256', 'failed_send_json', 'prepared_plan_json', 'plan_json',
        'send_header_json', 'metadata_only_request', 'limits'}
    r.require(type(request) is dict and set(request) == fields
        and request['schema'] == REQUEST_SCHEMA and request['source_commit'] == COMMIT
        and request['metadata_only_request'] is True and request['limits'] == r.LIMITS,
        'exact read-only reconciliation request required')
    for key in ('helper_sha256', 'remote_helper_sha256', 'remote_program_sha256'):
        r.require(type(request[key]) is str and r.HEX.fullmatch(request[key]), 'actual reviewed helper pin required')
    records, raws = {}, {}
    for name, expected in (('failed_send', FAILED_SHA), ('prepared_plan', PREPARED_SHA),
                           ('plan', PLAN_SHA), ('send_header', HEADER_SHA)):
        value = request[name + '_json']
        r.require(type(value) is str, 'actual retained JSON bytes required')
        raw = value.encode('utf-8')
        r.require(r.sha(raw) == expected, 'original retained evidence raw pin changed: ' + name)
        records[name], raws[name] = r.decode(raw), raw
    plan = r.validate_plan(raws['plan'], PLAN_SHA)
    header = r.validate_header(records['send_header'], plan)
    prepared, failed = records['prepared_plan'], records['failed_send']
    r.require(plan['source_commit'] == COMMIT and plan['file_count'] == 907
        and plan['selected_uncompressed_bytes'] == 92999657
        and header['plan_bytes'] == len(raws['plan']) and header['plan_sha256'] == PLAN_SHA
        and header['sender_sha256'] == SENDER_SHA and header['receiver_sha256'] == RECEIVER_SHA
        and r.sha(r.canonical(header)) == HEADER_WIRE_SHA,
        'different source, installed inventory, or actual transfer header')
    r.require(prepared['schema'] == 'peano-hydra-retention-evaluation-recovery-transfer-prepared-v1'
        and prepared['status'] == 'prepared-local-only' and prepared['plan'] == raw_pin(r, raws['plan'])
        and prepared['source'] == {'clean': True, 'commit': COMMIT, 'optional_locks': False}
        and prepared['bundle'] == plan['bundle'] and prepared['limits'] == r.LIMITS
        and prepared['sender'] == {'bytes': 36130, 'sha256': SENDER_SHA}
        and prepared['receiver'] == {'bytes': 34678, 'sha256': RECEIVER_SHA}
        and prepared['selected_files'] == 907 and prepared['selected_uncompressed_bytes'] == 92999657
        and prepared['source_files_sha256'] == plan['source_files_sha256']
        and prepared['bootstrap_files_sha256'] == plan['bootstrap_files_sha256'],
        'actual prepared archive/source identity changed')
    process = failed['ssh_process']
    original = r.decode(process['stdout'].encode('utf-8'), 65536)
    r.require(failed['schema'] == 'peano-hydra-retention-evaluation-recovery-transfer-send-result-v1'
        and failed['status'] == 'failed-no-automatic-retry' and failed['automatic_retry'] is False
        and failed['job_submitted'] is False and failed['network_contacted'] is True
        and failed['partial_outputs_preserved'] is True and failed['local_inputs_rechecked'] is True
        and failed['send_header'] == {'path': r.ARCHIVE_ROOT + '/source-transfer-01/send-header.json',
                                      **raw_pin(r, raws['send_header'])}
        and failed['send_header_wire_sha256'] == HEADER_WIRE_SHA
        and process['reason'] == 'exited' and process['returncode'] == 2 and process['error'] is None
        and process['sent_compressed_sha256'] == plan['bundle']['sha256']
        and original['status'] == 'failed-partial-output-preserved'
        and original['error'] == 'TimeoutError: remote retention bootstrap receiver55-second wall deadline'
        and original['source_commit'] == COMMIT and original['plan_sha256'] == PLAN_SHA
        and original['header_sha256'] == HEADER_WIRE_SHA and original['remote_root'] == r.REMOTE_ROOT
        and original['transfer_started_at_utc'] == STAMP
        and original['files_written'] == 908 and original['bytes_written'] == 92999725
        and original['destination_created'] is True
        and original['job_submission_performed'] is False and original['model_loaded'] is False
        and original['native_work_performed'] is False and original['limits'] == r.LIMITS,
        'this operation reconciles only the actual failed one-use transfer')
    provenance = (COMMIT + '\tfalse\t' + STAMP + '\n').encode('ascii')
    r.require(len(provenance) == 68, 'actual preserved source provenance size changed')
    durable = r.receipt_record(plan, header, HEADER_WIRE_SHA, STAMP, provenance, prepared['tar_validation'])
    durable_raw = r.canonical(durable) + b'\n'
    return plan, prepared, header, provenance, durable, durable_raw


def parent_directories(names):
    result = set()
    for name in names:
        parts = name.split('/')
        result.update('/'.join(parts[:length]) for length in range(1, len(parts)))
    return result


def inventory(r, tree, expected_files):
    """Closed files AND directories, using the original rooted descriptors."""
    allowed_dirs = parent_directories(expected_files)
    files, directories, stack, count = {}, {}, [('', os.dup(tree.fd))], 0
    try:
        while stack:
            prefix, fd = stack.pop()
            try:
                for part in os.listdir(fd):
                    name = prefix + part
                    r.relative(name)
                    count += 1
                    r.require(count <= r.MAX_FILES * 3, 'installed directory-entry bound')
                    info = os.stat(part, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        r.require(name in allowed_dirs and stat.S_IMODE(info.st_mode) == 0o700,
                                  'unexpected or nonprivate installed directory')
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                        r.require(r.identity(os.fstat(child)) == r.identity(info), 'directory changed while opening')
                        directories[name] = r.identity(info)
                        stack.append((name + '/', child))
                    else:
                        r.require(name in expected_files and stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                                  'unexpected, linked or special installed file')
                        files[name] = r.identity(info)
            finally:
                os.close(fd)
        r.require(set(files) == set(expected_files) and set(directories) == allowed_dirs,
                  'installed tree is missing declared files or directories')
        tree.anchored()
        root = r.identity(os.fstat(tree.fd))
        r.require(stat.S_IMODE(root[2]) == 0o700, 'installed root is not private')
        return {'root': root, 'files': files, 'directories': directories}
    finally:
        for _, fd in stack:
            os.close(fd)


def verify_installed(r, tree, files, modes, metadata, durable_raw):
    """Full byte/mode pass plus before/after metadata and closed inventory."""
    observed = tree.files()
    receipt_present = r.REMOTE_RECEIPT in observed
    expected = set(files) | ({r.REMOTE_RECEIPT} if receipt_present else set())
    r.require(observed == expected, 'foreign or missing installed file')
    before = inventory(r, tree, expected)
    expected_receipt = raw_pin(r, durable_raw)
    metadata = set(metadata) | ({r.REMOTE_RECEIPT} if receipt_present else set())
    metadata_before, retained = {}, {}
    for name in sorted(metadata):
        actual, raw, info = tree.fingerprint(name, retain=True)
        expected_pin = expected_receipt if name == r.REMOTE_RECEIPT else files[name]
        expected_mode = 0o600 if name == r.REMOTE_RECEIPT else modes[name]
        r.require(actual == expected_pin and stat.S_IMODE(info[2]) == expected_mode,
                  'installed metadata byte/mode changed: ' + name)
        if name == r.REMOTE_RECEIPT:
            r.require(raw == durable_raw, 'existing durable receipt is not the exact original expected bytes')
        metadata_before[name], retained[name] = actual, raw
    total, checked = 0, {}
    for name, item in files.items():
        actual, _, info = tree.fingerprint(name)
        r.require(actual == item and stat.S_IMODE(info[2]) == modes[name]
                  and info == before['files'][name], 'installed bytes/mode/path changed: ' + name)
        checked[name] = actual
        total += actual['bytes']
        r.require(total <= r.MAX_TOTAL and len(checked) <= r.MAX_FILES, 'installed verification bound')
    for name in sorted(metadata):
        actual, raw, info = tree.fingerprint(name, retain=True)
        r.require(actual == metadata_before[name] and raw == retained[name]
            and info == before['files'][name], 'installed metadata changed during full rehash: ' + name)
    r.require(inventory(r, tree, expected) == before and tree.files() == expected,
              'installed tree changed during verification')
    actual_receipt = {'present': receipt_present, 'path': r.REMOTE_RECEIPT}
    if receipt_present:
        actual_receipt.update(expected_receipt)
    return {'input_file_count': len(checked), 'input_total_bytes': total,
        'file_count': len(expected), 'total_bytes': total + (len(durable_raw) if receipt_present else 0),
        'files_sha256': r.sha(r.canonical(checked)),
        'private_modes_sha256': r.sha(r.canonical({name: format(mode, '04o') for name, mode in modes.items()})),
        'directory_count': len(before['directories']),
        'directory_names_sha256': r.sha(r.canonical(sorted(before['directories']))),
        'metadata_files_rehashed': len(metadata),
        'metadata_sha256': r.sha(r.canonical(metadata_before)),
        'durable_receipt': actual_receipt,
        'exact_inventory_checked': True, 'all_file_hashes_rechecked': True,
        'metadata_rehashed_before_and_after': True, 'paths_and_modes_unchanged': True,
        'single_link_regular_files': True, 'nonsymlink_directory_chain': True}, retained


def readonly_audit(attempts):
    mutation = {'os.remove', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.link', 'os.symlink',
        'os.chmod', 'os.chown', 'os.utime', 'os.truncate', 'os.system', 'os.exec',
        'os.posix_spawn', 'os.fork', 'os.forkpty', 'os.chdir', 'os.fchdir', 'ctypes.dlopen'}
    forbidden_imports = {'torch', 'transformers', 'peft', 'tokenizers', 'safetensors', 'tensorflow', 'jax', 'flax'}
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
    def audit(event, args):
        denied = event in mutation or event.startswith(('subprocess.', 'socket.'))
        if event == 'open':
            mode, flags = args[1], args[2]
            denied = (type(mode) is str and any(c in mode for c in 'wax+')) or (
                type(flags) is int and bool(flags & write_flags))
        if event == 'import':
            denied = str(args[0]).split('.')[0] in forbidden_imports
        if denied:
            if len(attempts) < 16:
                attempts.append(event)
            raise RuntimeError('read-only installation inspection rejected ' + event)
    return audit


def inspect(r, request):
    plan, prepared, header, provenance, durable, durable_raw = evidence(r, request)
    tree = r.Tree(r.REMOTE_ROOT)
    try:
        files = durable['files']
        modes = {name: int(mode, 8) for name, mode in durable['private_modes'].items()}
        metadata = set(plan['bootstrap_files']) | {r.FREEZE_RECEIPT, r.ORIGIN_MANIFEST, r.PROVENANCE}
        checked, retained = verify_installed(r, tree, files, modes, metadata, durable_raw)
        r.validate_freeze(plan, retained[r.FREEZE_RECEIPT])
        r.validate_authority(plan, retained[r.AUTHORITY])
        r.require(retained[r.PROVENANCE] == provenance and checked['input_file_count'] == 908
            and checked['input_total_bytes'] == 92999725 and checked['files_sha256'] == durable['files_sha256'],
            'actual installed source/provenance does not match the original failed transfer')
        tree.anchored()
    finally:
        tree.close()
    return {**checked, 'status': 'installed-state-verified-read-only',
        'source_commit': COMMIT, 'remote_root': r.REMOTE_ROOT,
        'source_files_sha256': plan['source_files_sha256'],
        'bootstrap_files_sha256': plan['bootstrap_files_sha256'],
        'selected_files_sha256': plan['selected_files_sha256'],
        'plan_sha256': PLAN_SHA, 'prepared_plan_sha256': PREPARED_SHA,
        'failed_send_sha256': FAILED_SHA, 'send_header_sha256': HEADER_SHA,
        'send_header_wire_sha256': HEADER_WIRE_SHA,
        'transfer_started_at_utc': STAMP, 'source_provenance': provenance.decode('ascii'),
        'source_provenance_sha256': r.sha(provenance),
        'original_transfer_status': 'failed-no-automatic-retry', 'original_transfer_returncode': 2,
        'resource_request_present': True, 'approval_present': True}


def measure():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {'cpu_seconds': usage.ru_utime + usage.ru_stime,
        'wall_seconds': time.monotonic() - STARTED,
        'peak_rss_bytes': int(usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024))}


def check_measurements(r, values):
    r.require(all(type(values[key]) in (int, float) and math.isfinite(values[key]) and values[key] >= 0
                  for key in ('cpu_seconds', 'wall_seconds', 'peak_rss_bytes'))
        and values['cpu_seconds'] < 45 and values['wall_seconds'] < 55
        and 0 < values['peak_rss_bytes'] <= 320 * 1024**2, 'remote read-only CPU/wall/RSS boundary')


def main(receiver_source):
    if not (sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 2):
        raise ValueError('isolated no-bytecode Python and exact request raw SHA required')
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def deadline(*_):
        raise TimeoutError('remote installation reconciliation55-second wall deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 55 - (time.monotonic() - STARTED)))
    r = load_receiver(receiver_source.encode('utf-8'))
    attempts = []
    sys.addaudithook(readonly_audit(attempts))
    result = {'schema': SCHEMA, 'started_at_utc': r.utc(), 'limits': r.LIMITS,
        'remote_file_size_limit_bytes': 0, 'read_only': True,
        'request_sha256': sys.argv[1], 'forbidden_attempts': attempts, **NO_WORK}
    code = 2
    try:
        r.require(r.HEX.fullmatch(sys.argv[1]), 'external inspection request raw pin required')
        length = struct.unpack('>Q', r.exact(sys.stdin.buffer, 8))[0]
        r.require(0 < length <= r.MAX_JSON, 'inspection request byte bound')
        raw = r.exact(sys.stdin.buffer, length)
        r.require(r.sha(raw) == sys.argv[1] and sys.stdin.buffer.read(1) == b'',
                  'inspection request raw bytes or EOF changed')
        request = r.decode(raw)
        result.update(inspect(r, request))
        result.update(helper_sha256=request['helper_sha256'], remote_helper_sha256=request['remote_helper_sha256'],
                      remote_program_sha256=request['remote_program_sha256'])
        r.require(not attempts, 'a forbidden read-only action was attempted')
        check_measurements(r, measure())
        code = 0
    except BaseException as error:
        result.update(status='failed-read-only-inspection', error=(type(error).__name__ + ': ' + str(error))[:2000])
    result.update(finished_at_utc=r.utc(), **measure())
    raw = r.canonical(result) + b'\n'
    r.require(len(raw) <= 65536, 'read-only remote output byte cap')
    sys.stdout.write(raw.decode('utf-8'))
    sys.stdout.flush()
    if code == 0:
        check_measurements(r, measure())
        r.require(not attempts and resource.getrlimit(resource.RLIMIT_FSIZE) == (0, 0),
                  'read-only publication boundary changed')
    signal.setitimer(signal.ITIMER_REAL, 0)
    raise SystemExit(code)
