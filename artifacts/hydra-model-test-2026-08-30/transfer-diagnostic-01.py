#!/usr/bin/env python3
"""Prepare and send exactly one approved diagnostic transfer; never launch jobs.

prepare is local-only. send requires the externally retained prepared-plan SHA
and consumes an exclusive send marker. The original tar, source and package
are read only. Required existing remote model/source inputs are NOT verified
or materialized by this transport; that remains a separate launch gate.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import selectors
import shlex
import signal
import stat
import struct
import subprocess
import sys
import time
import types

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
RECEIVER = ARCHIVE / 'transfer-diagnostic-remote-01.py'
RECEIVER_SHA = 'cc3036885e5a074c3b41e381c5f2b35a232ef62a3829e46ab0c372e21ad82e33'
PLAN = ARCHIVE / 'transfer-plan-01.json'
BUNDLE = ARCHIVE / 'diagnostic-source-inputs-01.tar.gz'
DIRECTIVE = ARCHIVE / 'explicit-experiment-approval-01.json'
ATTEMPT = ARCHIVE / 'diagnostic-transfer-01'
HOST = 'plgnasqret@helios.cyfronet.pl'
OUTPUT_NAMES = frozenset({
    'prepare-started.json', 'prepared-plan.json', 'prepare-result.json',
    'send-started.json', 'send-header.json', 'ssh-process.json', 'send-result.json',
})


def load_receiver():
    assert RECEIVER.parent.resolve() == ARCHIVE and not RECEIVER.is_symlink()
    fd = os.open(RECEIVER, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= 65536
        raw = os.read(fd, 65537)
        assert len(raw) == info.st_size and hashlib.sha256(raw).hexdigest() == RECEIVER_SHA
        assert (os.fstat(fd).st_mtime_ns, os.fstat(fd).st_ctime_ns) == (info.st_mtime_ns, info.st_ctime_ns)
    finally:
        os.close(fd)
    module = types.ModuleType('diagnostic_transfer_receiver')
    module.__file__ = str(RECEIVER)
    exec(compile(raw, str(RECEIVER), 'exec'), module.__dict__)
    return module, raw


r, RECEIVER_RAW = load_receiver()
LOCAL_ROOT = Path(r.LOCAL_ROOT)


def read_file(path, maximum):
    tree = r.Tree(str(path.parent))
    try:
        fd, identity = tree.open_file(path.name)
        os.close(fd)
        r.require(identity[4] <= maximum, 'metadata read exceeds its declared cap')
        pin, raw, _ = tree.fingerprint(path.name, retain=True)
        r.require(pin['bytes'] <= maximum, 'metadata grew beyond its declared cap')
        return raw
    finally:
        tree.close()


def pin(raw):
    return {'bytes':len(raw), 'sha256':r.sha(raw)}


def new_json(name, record):
    r.require(name in OUTPUT_NAMES, 'unapproved local receipt path')
    raw = r.canonical(record) + b'\n'
    r.require(len(raw) <= r.LIMITS['receipt_file_bytes'], 'local receipt byte cap')
    parent = r.directory(str(ATTEMPT))
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return {'path':str(ATTEMPT / name), **pin(raw)}


def source_environment():
    result = {k:v for k,v in os.environ.items()
              if not k.startswith(('GIT_', 'PYTHON', 'SBATCH_', 'LD_', 'DYLD_'))}
    result.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                  GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_OPTIONAL_LOCKS='0',
                  PYTHONDONTWRITEBYTECODE='1')
    return result


def bounded(command, timeout, prefix=None, bundle_stream=None):
    """Bound one process group; stream bounded input/output without blocking writes."""
    started = time.monotonic()
    before_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    def child_limits():
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    child = subprocess.Popen(command, stdin=subprocess.PIPE if prefix is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=str(ARCHIVE), env=source_environment(),
                             start_new_session=True, preexec_fn=child_limits)
    selector = selectors.DefaultSelector()
    output = {'stdout':bytearray(), 'stderr':bytearray()}
    reason, error = 'exited', None
    prefix_offset, remaining, pending, sent = 0, r.BUNDLE_BYTES if bundle_stream is not None else 0, b'', 0
    body_hash = hashlib.sha256()
    try:
        for label in output:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        if prefix is not None:
            r.require(bundle_stream is not None and len(prefix) <= r.MAX_JSON,
                      'bounded transfer prefix and tar required')
            os.set_blocking(child.stdin.fileno(), False)
            selector.register(child.stdin, selectors.EVENT_WRITE, 'stdin')
        while selector.get_map():
            r.require(time.monotonic()-started < timeout, 'bounded process wall deadline')
            own = resource.getrusage(resource.RUSAGE_SELF)
            rss = own.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
            r.require(rss <= r.LIMITS['local_checked_rss_bytes'], 'local sender RSS exceeds cap')
            for key, _ in selector.select(0.1):
                if key.data == 'stdin':
                    if not pending:
                        if prefix_offset < len(prefix):
                            pending = prefix[prefix_offset:prefix_offset+65536]
                            prefix_offset += len(pending)
                        elif remaining:
                            pending = bundle_stream.read(min(65536, remaining))
                            r.require(pending, 'local tar truncated during send')
                            remaining -= len(pending)
                            body_hash.update(pending)
                        else:
                            r.require(body_hash.hexdigest() == r.BUNDLE_SHA, 'sent tar body changed')
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                            continue
                    try:
                        count = os.write(key.fileobj.fileno(), pending)
                    except BlockingIOError:
                        continue
                    r.require(count > 0, 'short SSH input write')
                    pending = pending[count:]
                    sent += count
                else:
                    raw = os.read(key.fileobj.fileno(), 65536)
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    cap = r.LIMITS['ssh_stdout_bytes'] if key.data == 'stdout' else r.LIMITS['ssh_stderr_bytes']
                    room = cap - len(output[key.data])
                    output[key.data].extend(raw[:room])
                    r.require(len(raw) <= room, 'bounded process output cap')
        child.wait(timeout=max(0.01, timeout-(time.monotonic()-started)))
    except BaseException as failure:
        reason = 'stopped'
        error = type(failure).__name__ + ': ' + str(failure)[:2048]
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=2)
    finally:
        selector.close()
        if child.stdin is not None and not child.stdin.closed:
            child.stdin.close()
        child.stdout.close()
        child.stderr.close()
    after_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        'returncode':child.returncode, 'reason':reason, 'error':error,
        'wall_seconds':time.monotonic()-started, 'wire_bytes_sent':sent,
        'sent_compressed_sha256':body_hash.hexdigest() if bundle_stream is not None and remaining == 0 else None,
        'reaped_child_cpu_delta_seconds':after_children.ru_utime+after_children.ru_stime-before_children.ru_utime-before_children.ru_stime,
        **{name:bytes(raw).decode('utf-8', 'replace') for name,raw in output.items()},
    }


def git_state():
    prefix = ['/usr/bin/git', '--no-optional-locks', '-c', 'core.hooksPath=/dev/null',
              '-c', 'core.fsmonitor=false', '-C', str(LOCAL_ROOT)]
    rows = []
    for arguments in (['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain=v1', '--untracked-files=all']):
        row = bounded(prefix + arguments, timeout=5)
        r.require(row['reason'] == 'exited' and row['returncode'] == 0,
                  'fixed read-only Git command did not complete')
        rows.append(row['stdout'])
    r.require(rows == [r.SOURCE_COMMIT + '\n', ''], 'source is not the exact clean diagnostic snapshot')
    return {'commit':r.SOURCE_COMMIT, 'clean':True, 'optional_locks':False}


def context():
    plan_raw = read_file(PLAN, r.PLAN_BYTES)
    plan = r.validate_plan(plan_raw)
    request_raw = read_file(LOCAL_ROOT / r.REQUEST, r.REQUEST_BYTES)
    approval_raw = read_file(LOCAL_ROOT / r.APPROVAL, r.MAX_APPROVAL)
    r.validate_controls(plan, request_raw, approval_raw)
    directive_raw = read_file(DIRECTIVE, r.MAX_JSON)
    r.require(r.sha(directive_raw) == r.DIRECTIVE_SHA, 'actual user approval directive changed')
    r.require(read_file(RECEIVER, 65536) == RECEIVER_RAW, 'reviewed receiver changed')
    return plan, plan_raw, request_raw, approval_raw


def check_selected(plan):
    state = git_state()
    tree = r.Tree(str(LOCAL_ROOT))
    try:
        for name, expected in plan['selected_files'].items():
            actual, _, identity = tree.fingerprint(name)
            r.require(actual == {k:expected[k] for k in ('bytes', 'sha256')}
                      and stat.S_IMODE(identity[2]) == int(expected['mode'], 8),
                      'selected local bytes or mode changed: ' + name)
        approval_pin, _, _ = tree.fingerprint(r.APPROVAL)
        r.require(approval_pin == {'bytes':r.APPROVAL_BYTES, 'sha256':r.APPROVAL_SHA},
                  'local explicit approval changed')
        package = r.Tree(str(LOCAL_ROOT / r.PACKAGE))
        try:
            actual = {r.PACKAGE + '/' + name for name in package.files()}
            expected = {name for name in plan['selected_files'] if name.startswith(r.PACKAGE + '/')} | {r.APPROVAL}
            r.require(actual == expected, 'local diagnostic package is not closed')
        finally:
            package.close()
        tree.anchored()
    finally:
        tree.close()
    r.require(git_state() == state, 'source Git state changed during selected checks')
    return state


def bundle_open():
    tree = r.Tree(str(ARCHIVE))
    try:
        fd, before = tree.open_file(BUNDLE.name)
        r.require(before[4] == r.BUNDLE_BYTES, 'pinned compressed tar size changed')
        stream = os.fdopen(fd, 'rb')
        hasher = hashlib.sha256()
        while True:
            raw = stream.read(65536)
            if not raw:
                break
            hasher.update(raw)
        r.require(hasher.hexdigest() == r.BUNDLE_SHA and r.identity(os.fstat(stream.fileno())) == before,
                  'pinned compressed tar changed')
        check, after = tree.open_file(BUNDLE.name)
        os.close(check)
        r.require(after == before, 'tar path changed during hashing')
        tree.anchored()
        stream.seek(0)
        return stream, before
    finally:
        tree.close()


def prepared_record(source_state, tar_check):
    return {
        'schema':'peano-hydra-diagnostic-transfer-prepared-v1',
        'status':'prepared-local-only', 'source':source_state,
        'source_root':r.LOCAL_ROOT, 'destination_host':HOST, 'destination_directory':r.REMOTE_ROOT,
        'plan_sha256':r.PLAN_SHA, 'resource_request_sha256':r.REQUEST_SHA,
        'approval_sha256':r.APPROVAL_SHA, 'directive_sha256':r.DIRECTIVE_SHA,
        'bundle':{'path':str(BUNDLE), 'bytes':r.BUNDLE_BYTES, 'sha256':r.BUNDLE_SHA},
        'sender':pin(read_file(Path(__file__).absolute(), 65536)),
        'receiver':pin(RECEIVER_RAW), 'selected_files':r.SELECTED_FILES,
        'selected_uncompressed_bytes':r.SELECTED_BYTES,
        'approval_bytes':r.APPROVAL_BYTES, 'maximum_provenance_bytes':r.MAX_PROVENANCE,
        'maximum_installed_bytes':r.MAX_TOTAL, 'maximum_installed_files':r.MAX_FILES,
        'provenance_policy':'Receiver creates commit/false/UTC at actual transfer; exact bytes and SHA retained in send receipt.',
        'mode_policy':'original executable status preserved with private0600/0700 permissions',
        'tar_validation':tar_check, 'limits':r.LIMITS,
        'network_contacted':False, 'source_package_tar_mutated':False,
        'external_remote_source_and_model_inputs_verified':False,
        'native_or_model_work_performed':False, 'job_submitted':False,
        'automatic_retry':False, 'partial_outputs_preserved':True,
    }


def prepare():
    parent = r.directory(str(ARCHIVE))
    try:
        os.mkdir(ATTEMPT.name, 0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    new_json('prepare-started.json', {'started_at_utc':r.utc(), 'network_contacted':False,
             'plan_sha256':r.PLAN_SHA, 'automatic_retry':False})
    record = {'schema':'peano-hydra-diagnostic-transfer-prepare-result-v1', 'network_contacted':False}
    try:
        plan, _, _, _ = context()
        state = check_selected(plan)
        stream, before = bundle_open()
        try:
            def consume(name, item, expanded):
                remaining, hasher = item['bytes'], hashlib.sha256()
                while remaining:
                    raw = r.exact(expanded, min(65536, remaining))
                    remaining -= len(raw)
                    hasher.update(raw)
                r.require(hasher.hexdigest() == item['sha256'], 'tar payload differs: ' + name)
            tar_check = r.consume_tar(stream, plan['selected_files'], consume)
            r.require(stream.read(1) == b'' and r.identity(os.fstat(stream.fileno())) == before,
                      'local tar stream grew or changed')
        finally:
            stream.close()
        context()
        prepared = prepared_record(state, tar_check)
        artifact = new_json('prepared-plan.json', prepared)
        record.update(status='prepared-local-only', prepared_plan=artifact, checks=tar_check,
                      source=state, external_remote_source_and_model_inputs_verified=False)
    except BaseException as error:
        record.update(status='failed-local-only', error=type(error).__name__+': '+str(error)[:2048])
    result = new_json('prepare-result.json', record)
    print(r.canonical({'status':record['status'], 'result':result,
                       'prepared_plan':record.get('prepared_plan'), 'error':record.get('error')}).decode(), flush=True)
    return 0 if record['status'] == 'prepared-local-only' else 2


def send(expected_prepared_sha):
    r.require(type(expected_prepared_sha) is str and r.HEX.fullmatch(expected_prepared_sha),
              'external prepared-plan SHA required')
    new_json('send-started.json', {'started_at_utc':r.utc(), 'prepared_plan_sha256':expected_prepared_sha,
             'network_contacted':False, 'automatic_retry':False})
    result = {'schema':'peano-hydra-diagnostic-transfer-send-result-v1', 'network_contacted':False,
              'automatic_retry':False, 'partial_outputs_preserved':True,
              'external_remote_source_and_model_inputs_verified':False, 'job_submitted':False}
    try:
        prepared_raw = read_file(ATTEMPT / 'prepared-plan.json', r.MAX_JSON)
        r.require(r.sha(prepared_raw) == expected_prepared_sha, 'external prepared-plan bytes changed')
        prepared = r.decode(prepared_raw)
        ready = r.decode(read_file(ATTEMPT / 'prepare-result.json', r.MAX_JSON))
        r.require(ready.get('status') == 'prepared-local-only'
                  and ready.get('prepared_plan', {}).get('sha256') == expected_prepared_sha,
                  'successful exact local preparation missing')
        plan, plan_raw, request_raw, approval_raw = context()
        state = check_selected(plan)
        r.require(prepared == prepared_record(state, prepared['tar_validation']),
                  'prepared package/helper/control binding changed')
        stream, before = bundle_open()
        try:
            header = {
                'schema':'peano-hydra-diagnostic-transfer-header-v1',
                'plan_sha256':r.PLAN_SHA, 'request_sha256':r.REQUEST_SHA,
                'approval_sha256':r.APPROVAL_SHA, 'directive_sha256':r.DIRECTIVE_SHA,
                'source_commit':r.SOURCE_COMMIT, 'local_source_clean':True,
                'send_started_at_utc':r.utc(), 'sender_sha256':prepared['sender']['sha256'],
                'receiver_sha256':RECEIVER_SHA, 'limits':r.LIMITS,
            }
            r.validate_header(header)
            raw = r.canonical(header)
            r.require(len(raw) <= r.MAX_HEADER, 'send header byte cap')
            header_artifact = new_json('send-header.json', header)
            header_sha = r.sha(raw)
            prefix = r.MAGIC + struct.pack('>Q', len(raw)) + raw + plan_raw + request_raw + approval_raw
            program = RECEIVER_RAW.decode('utf-8') + '\nmain()\n'
            remote = shlex.join(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin',
                                  '/usr/bin/python3', '-I', '-B', '-c', program, header_sha])
            command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                       '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
                       '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes',
                       '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
                       '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', HOST, remote]
            result.update(network_contacted=True, send_header=header_artifact,
                          send_header_wire_sha256=header_sha,
                          receiver_program_sha256=r.sha(program.encode('utf-8')))
            process = bounded(command, timeout=r.LIMITS['ssh_wall_seconds'],
                              prefix=prefix, bundle_stream=stream)
            new_json('ssh-process.json', process)
            result['ssh_process'] = process
            r.require(r.identity(os.fstat(stream.fileno())) == before, 'tar changed during SSH transfer')
        finally:
            stream.close()
        r.require(check_selected(plan) == state, 'local inputs changed through transfer')
        context()
        stream, _ = bundle_open()
        stream.close()
        result['local_inputs_rechecked'] = True
        r.require(process['reason'] == 'exited' and process['returncode'] == 0, 'transfer did not complete; no retry')
        remote_result = r.decode(process['stdout'].encode('utf-8'))
        r.require(remote_result.get('schema') == 'peano-hydra-diagnostic-transfer-remote-result-v1'
                  and remote_result.get('status') == 'transferred-and-rehashed'
                  and remote_result.get('header_sha256') == header_sha
                  and remote_result.get('remote_root') == r.REMOTE_ROOT
                  and remote_result.get('source_commit') == r.SOURCE_COMMIT
                  and remote_result.get('plan_sha256') == r.PLAN_SHA
                  and remote_result.get('request_sha256') == r.REQUEST_SHA
                  and remote_result.get('approval_sha256') == r.APPROVAL_SHA
                  and remote_result.get('file_count') == r.MAX_FILES
                  and remote_result.get('exact_inventory_checked') is True
                  and remote_result.get('all_file_hashes_rechecked') is True
                  and remote_result.get('job_submission_performed') is False
                  and remote_result.get('installation_performed') is False
                  and remote_result.get('model_loaded') is False, 'remote transfer receipt changed')
        provenance = remote_result['source_provenance'].encode('ascii')
        r.require(provenance == (r.SOURCE_COMMIT+'\tfalse\t'+remote_result['transfer_started_at_utc']+'\n').encode('ascii')
                  and len(provenance) <= r.MAX_PROVENANCE
                  and r.sha(provenance) == remote_result['source_provenance_sha256']
                  and remote_result['total_bytes'] == r.SELECTED_BYTES + r.APPROVAL_BYTES + len(provenance)
                  and remote_result['total_bytes'] <= r.MAX_TOTAL
                  and remote_result['bundle']['compressed_bytes'] == r.BUNDLE_BYTES
                  and remote_result['bundle']['compressed_sha256'] == r.BUNDLE_SHA,
                  'actual provenance or payload receipt changed')
        result.update(status='transferred-and-rehashed', remote=remote_result)
    except BaseException as error:
        result.update(status='failed-no-automatic-retry', error=type(error).__name__+': '+str(error)[:2048])
    result.update(finished_at_utc=r.utc())
    receipt = new_json('send-result.json', result)
    print(r.canonical({'status':result['status'], 'receipt':receipt,
                      'network_contacted':result['network_contacted'], 'error':result.get('error')}).decode(), flush=True)
    return 0 if result['status'] == 'transferred-and-rehashed' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('mode', choices=('prepare', 'send'))
    parser.add_argument('--expected-prepared-plan-sha256')
    args = parser.parse_args()
    r.require(sys.flags.isolated and sys.dont_write_bytecode, 'invoke with -I -B')
    r.require((args.expected_prepared_plan_sha256 is not None) == (args.mode == 'send'),
              'only send takes the external prepared-plan SHA')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    def deadline(signum, frame):
        raise TimeoutError('local diagnostic transfer90-second wall deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(90)
    try:
        return prepare() if args.mode == 'prepare' else send(args.expected_prepared_plan_sha256)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())

