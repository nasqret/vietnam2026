#!/usr/bin/env python3
"""One-use nonlaunching retention bootstrap construction, preparation and transfer.

build-plan and prepare are local-only, independently operator-invoked stages.
Only actual freeze/plan pins can advance them; send consumes an exclusive marker.
All five later resource/control files are forbidden. Existing remote origins,
models, CPU preflight, scheduler, allocation and training remain separate gates.
"""
import argparse
import gzip
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
import tarfile
import time
import types

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
RECEIVER = ARCHIVE / 'transfer-retention-bootstrap-remote-01.py'
RECEIVER_SHA = '40d8391d2d770e509470c81c7a5fe21f0e7ec3a80048e4b70fa9cb0059e6edc2'
PLAN = ARCHIVE / 'transfer-plan-01.json'
BUNDLE = ARCHIVE / 'retention-bootstrap-source-inputs-01.tar.gz'
ATTEMPT = ARCHIVE / 'bootstrap-transfer-01'
HOST = 'plgnasqret@helios.cyfronet.pl'
OUTPUT_NAMES = frozenset({
    'prepare-started.json', 'prepared-plan.json', 'prepare-result.json',
    'send-started.json', 'send-header.json', 'ssh-process.json', 'send-result.json',
})
BUILD_OUTPUTS = frozenset({'bootstrap-build-started.json', 'transfer-plan-01.json', 'bootstrap-build-result.json'})

def load_receiver():
    if RECEIVER.parent.resolve() != ARCHIVE or RECEIVER.is_symlink():
        raise ValueError('fixed nonsymlink receiver path required')
    fd = os.open(RECEIVER, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not (stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= 65536):
            raise ValueError('bounded single-link receiver required')
        raw = os.read(fd, 65537)
        if len(raw) != info.st_size or hashlib.sha256(raw).hexdigest() != RECEIVER_SHA:
            raise ValueError('reviewed receiver raw SHA changed')
        if (os.fstat(fd).st_mtime_ns, os.fstat(fd).st_ctime_ns) != (info.st_mtime_ns, info.st_ctime_ns):
            raise ValueError('receiver changed during read')
    finally:
        os.close(fd)
    module = types.ModuleType('retention_bootstrap_transfer_receiver')
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


def bounded(command, timeout, prefix=None, bundle_stream=None, bundle=None):
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
    prefix_offset, remaining, pending, sent = 0, bundle['bytes'] if bundle_stream is not None else 0, b'', 0
    body_hash = hashlib.sha256()
    try:
        for label in output:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        if prefix is not None:
            r.require(bundle_stream is not None and len(prefix) <= r.MAX_PREFIX,
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
                            r.require(body_hash.hexdigest() == bundle['sha256'], 'sent tar body changed')
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


def build_json(name, record):
    r.require(name in BUILD_OUTPUTS, 'unapproved local build output')
    raw = r.canonical(record) + b'\n'
    maximum = r.MAX_JSON if name == PLAN.name else r.LIMITS['receipt_file_bytes']
    r.require(len(raw) <= maximum, 'build metadata byte cap')
    parent = r.directory(str(ARCHIVE))
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return {'path':str(ARCHIVE / name), **pin(raw)}


def git_state(expected_commit):
    r.require(type(expected_commit) is str and r.OID.fullmatch(expected_commit), 'actual frozen commit required')
    prefix = ['/usr/bin/git', '--no-optional-locks', '-c', 'core.hooksPath=/dev/null',
              '-c', 'core.fsmonitor=false', '-C', str(LOCAL_ROOT)]
    rows = []
    for arguments in (['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain=v1', '--untracked-files=all']):
        row = bounded(prefix + arguments, timeout=5)
        r.require(row['reason'] == 'exited' and row['returncode'] == 0,
                  'fixed read-only Git command did not complete')
        rows.append(row['stdout'])
    r.require(rows == [expected_commit + '\n', ''], 'source is not the exact clean retention snapshot')
    return {'commit':expected_commit, 'clean':True, 'optional_locks':False}


def context(expected_plan_sha):
    plan_raw = read_file(PLAN, r.MAX_JSON)
    plan = r.validate_plan(plan_raw, expected_plan_sha)
    freeze_raw = read_file(LOCAL_ROOT / r.FREEZE_RECEIPT, r.MAX_FREEZE)
    authority_raw = read_file(LOCAL_ROOT / r.AUTHORITY, r.MAX_AUTHORITY)
    r.validate_freeze(plan, freeze_raw)
    r.validate_authority(plan, authority_raw)
    r.require(read_file(RECEIVER, 65536) == RECEIVER_RAW, 'reviewed receiver changed')
    return plan, plan_raw, freeze_raw, authority_raw


def check_selected(plan):
    state = git_state(plan['source_commit'])
    tree = r.Tree(str(LOCAL_ROOT))
    try:
        for name, expected in plan['selected_files'].items():
            actual, _, identity = tree.fingerprint(name)
            r.require(actual == {k:expected[k] for k in ('bytes', 'sha256')}
                      and stat.S_IMODE(identity[2]) == int(expected['mode'], 8),
                      'selected local bytes or mode changed: ' + name)
        package = r.Tree(str(LOCAL_ROOT / r.PACKAGE))
        try:
            actual = {r.PACKAGE + '/' + name for name in package.files()}
            r.require(actual == set(plan['bootstrap_files']), 'local bootstrap package is not closed')
        finally:
            package.close()
        tree.anchored()
    finally:
        tree.close()
    r.require(git_state(plan['source_commit']) == state, 'source Git state changed during selected checks')
    return state


def bundle_open(bundle):
    tree = r.Tree(str(ARCHIVE))
    try:
        fd, before = tree.open_file(BUNDLE.name)
        r.require(before[4] == bundle['bytes'], 'pinned compressed tar size changed')
        stream = os.fdopen(fd, 'rb')
        hasher = hashlib.sha256()
        while True:
            raw = stream.read(65536)
            if not raw:
                break
            hasher.update(raw)
        r.require(hasher.hexdigest() == bundle['sha256'] and r.identity(os.fstat(stream.fileno())) == before,
                  'pinned compressed tar changed')
        check, after = tree.open_file(BUNDLE.name)
        os.close(check)
        r.require(after == before, 'tar path changed during hashing')
        tree.anchored()
        stream.seek(0)
        return stream, before
    finally:
        tree.close()


def declared_plan(source_commit, freeze_pin, sources, bootstrap, bundle):
    files = {**sources, **bootstrap}
    return {
        'schema':'peano-hydra-retention-bootstrap-transfer-plan-v1', 'status':'prepared-bootstrap-local-only',
        'profile':r.PROFILE, 'run_id':r.RUN_ID, 'source_root':r.LOCAL_ROOT, 'source_commit':source_commit,
        'destination_directory':r.REMOTE_ROOT, 'destination_host':HOST,
        'freeze_receipt':{'path':r.FREEZE_RECEIPT, **freeze_pin},
        'source_files':sources, 'source_files_sha256':r.sha(r.canonical(sources)),
        'bootstrap_files':bootstrap, 'bootstrap_files_sha256':r.sha(r.canonical(bootstrap)),
        'selected_files':files, 'selected_files_sha256':r.sha(r.canonical(files)),
        'file_count':len(files), 'selected_uncompressed_bytes':sum(item['bytes'] for item in files.values()),
        'bundle':{'path':str(BUNDLE), **bundle}, 'directive_sha256':r.DIRECTIVE_SHA,
        'maximum_installed_files':len(files)+2,
        'maximum_installed_bytes':sum(item['bytes'] for item in files.values()) + r.MAX_PROVENANCE + r.MAX_JSON,
        'model_weights_in_bundle':False, 'resource_request_in_bundle':False, 'approval_in_bundle':False,
        'gpu_job_submitted':False, 'native_or_model_work_performed':False, 'remote_transfer_performed':False,
        'automatic_retry':False, 'resume':False, 'limits':r.LIMITS,
    }


def inventory_for_build(expected_freeze_sha, expected_commit):
    r.require(type(expected_freeze_sha) is str and r.HEX.fullmatch(expected_freeze_sha), 'external freeze receipt SHA required')
    state = git_state(expected_commit)
    freeze_raw = read_file(LOCAL_ROOT / r.FREEZE_RECEIPT, r.MAX_FREEZE)
    r.require(r.sha(freeze_raw) == expected_freeze_sha, 'actual frozen-source receipt bytes changed')
    frozen = r.decode(freeze_raw, r.MAX_FREEZE)
    r.require(type(frozen.get('files')) is dict and frozen['files'], 'actual frozen inventory missing')
    tree = r.Tree(str(LOCAL_ROOT))
    sources, bootstrap = {}, {}
    try:
        names = set(frozen['files']) | {r.FREEZE_RECEIPT, r.ORIGIN_MANIFEST}
        r.require(len(names) <= r.MAX_FILES - 3, 'source file count cap')
        for name in sorted(names):
            r.relative(name)
            actual, _, info = tree.fingerprint(name)
            sources[name] = {**actual, 'mode':format(stat.S_IMODE(info[2]), '04o')}
            r.descriptor(sources[name])
        partial = {'source_commit':expected_commit,
                   'freeze_receipt':{'path':r.FREEZE_RECEIPT, **pin(freeze_raw)}, 'source_files':sources}
        r.validate_freeze(partial, freeze_raw)
        package = r.Tree(str(LOCAL_ROOT / r.PACKAGE))
        try:
            for relative_name in sorted(package.files()):
                name = r.PACKAGE + '/' + relative_name
                r.require(name.rsplit('/', 1)[-1] not in r.LATER_CONTROLS,
                          'later resource/approval controls are forbidden in bootstrap')
                actual, _, info = tree.fingerprint(name)
                bootstrap[name] = {**actual, 'mode':format(stat.S_IMODE(info[2]), '04o')}
                r.descriptor(bootstrap[name])
        finally:
            package.close()
        r.require(not set(sources).intersection(bootstrap) and r.AUTHORITY in bootstrap,
                  'source and bootstrap must be disjoint and retain the actual directive')
        files = {**sources, **bootstrap}
        r.require(len(files)+2 <= r.MAX_FILES
                  and sum(item['bytes'] for item in files.values())+r.MAX_PROVENANCE+r.MAX_JSON <= r.MAX_TOTAL,
                  'bootstrap construction exceeds declared aggregate bounds')
        for name in files:
            r.require(name not in (r.PROVENANCE, r.REMOTE_RECEIPT)
                      and name.rsplit('/', 1)[-1] not in r.LATER_CONTROLS, 'generated/later control in source selection')
        authority_raw = read_file(LOCAL_ROOT / r.AUTHORITY, r.MAX_AUTHORITY)
        r.validate_authority({'bootstrap_files':bootstrap}, authority_raw)
        tree.anchored()
    finally:
        tree.close()
    r.require(git_state(expected_commit) == state, 'source Git state changed while constructing inventory')
    return state, freeze_raw, sources, bootstrap


class HashReader:
    def __init__(self, stream, expected):
        self.stream, self.expected, self.count, self.hasher = stream, expected, 0, hashlib.sha256()
    def read(self, count):
        r.require(type(count) is int and 0 <= count <= 65536, 'bounded tar copy read required')
        raw = self.stream.read(count)
        self.count += len(raw)
        r.require(self.count <= self.expected['bytes'], 'source grew during tar construction')
        self.hasher.update(raw)
        return raw


def construct_bundle(files):
    """Create one new deterministic ordinary USTAR/gzip; never extract or rebuild."""
    archive = r.Tree(str(ARCHIVE))
    source = r.Tree(str(LOCAL_ROOT))
    try:
        fd = os.open(BUNDLE.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=archive.fd)
        with os.fdopen(fd, 'wb') as target:
            with gzip.GzipFile(filename='', fileobj=target, mode='wb', compresslevel=6, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
                    for name in sorted(files):
                        item = files[name]
                        source.anchored()
                        opened, before = source.open_file(name)
                        with os.fdopen(opened, 'rb') as payload:
                            r.require(before[4] == item['bytes'] and stat.S_IMODE(before[2]) == int(item['mode'],8),
                                      'source mode/size changed before tar construction')
                            info = tarfile.TarInfo(name)
                            info.size, info.mode = item['bytes'], int(item['mode'],8)
                            info.uid = info.gid = info.mtime = 0
                            info.uname = info.gname = ''
                            reader = HashReader(payload, item)
                            tar.addfile(info, reader)
                            r.require(reader.count == item['bytes'] and reader.hasher.hexdigest() == item['sha256']
                                      and r.identity(os.fstat(payload.fileno())) == before,
                                      'source bytes/identity changed during tar construction')
                        check, after = source.open_file(name)
                        os.close(check)
                        r.require(after == before, 'source path changed during tar construction')
                        r.require(target.tell() <= r.MAX_BUNDLE, 'compressed bundle exceeds cap')
            target.flush()
            os.fsync(target.fileno())
            r.require(0 < target.tell() <= r.MAX_BUNDLE, 'compressed bundle exceeds final cap')
        archive.anchored()
        source.anchored()
        actual, _, _ = archive.fingerprint(BUNDLE.name)
        r.require(0 < actual['bytes'] <= r.MAX_BUNDLE, 'compressed bundle byte cap')
        os.fsync(archive.fd)
        return actual
    finally:
        source.close()
        archive.close()


def build_plan(expected_freeze_sha, expected_commit):
    build_json('bootstrap-build-started.json', {'started_at_utc':r.utc(),
               'freeze_receipt_sha256':expected_freeze_sha, 'source_commit':expected_commit,
               'network_contacted':False, 'automatic_retry':False})
    result = {'schema':'peano-hydra-retention-bootstrap-build-result-v1', 'network_contacted':False,
              'job_submitted':False, 'model_loaded':False, 'automatic_retry':False,
              'partial_outputs_preserved':True}
    try:
        state, freeze_raw, sources, bootstrap = inventory_for_build(expected_freeze_sha, expected_commit)
        bundle = construct_bundle({**sources, **bootstrap})
        plan = declared_plan(expected_commit, pin(freeze_raw), sources, bootstrap, bundle)
        raw = r.canonical(plan) + b'\n'
        r.validate_plan(raw, r.sha(raw))
        r.validate_freeze(plan, freeze_raw)
        r.require(check_selected(plan) == state and read_file(LOCAL_ROOT/r.FREEZE_RECEIPT, r.MAX_FREEZE) == freeze_raw,
                  'actual source/bootstrap changed during bundle construction')
        result.update(status='built-local-only', plan=build_json(PLAN.name, plan), bundle=bundle,
                      source=state, file_count=plan['file_count'], selected_uncompressed_bytes=plan['selected_uncompressed_bytes'])
    except BaseException as error:
        result.update(status='failed-local-only', error=type(error).__name__+': '+str(error)[:2048])
    artifact = build_json('bootstrap-build-result.json', result)
    print(r.canonical({'status':result['status'], 'result':artifact,
                       'plan':result.get('plan'), 'error':result.get('error')}).decode(), flush=True)
    return 0 if result['status'] == 'built-local-only' else 2


def prepared_record(plan, plan_raw, source_state, tar_check):
    return {
        'schema':'peano-hydra-retention-bootstrap-transfer-prepared-v1', 'status':'prepared-local-only',
        'source':source_state, 'source_root':r.LOCAL_ROOT,
        'destination_host':HOST, 'destination_directory':r.REMOTE_ROOT,
        'plan':pin(plan_raw), 'freeze_receipt':plan['freeze_receipt'], 'directive_sha256':r.DIRECTIVE_SHA,
        'bundle':plan['bundle'], 'sender':pin(read_file(Path(__file__).absolute(), 65536)),
        'receiver':pin(RECEIVER_RAW), 'selected_files':plan['file_count'],
        'selected_uncompressed_bytes':plan['selected_uncompressed_bytes'],
        'source_files_sha256':plan['source_files_sha256'],
        'bootstrap_files_sha256':plan['bootstrap_files_sha256'],
        'maximum_provenance_bytes':r.MAX_PROVENANCE, 'remote_receipt_path':r.REMOTE_RECEIPT,
        'maximum_installed_bytes':plan['maximum_installed_bytes'],
        'maximum_installed_files':plan['maximum_installed_files'],
        'provenance_policy':'Receiver creates actual frozen commit/false/UTC after receiving exact bytes; raw provenance retained and hashed.',
        'mode_policy':'original executable status preserved with private0600/0700 permissions',
        'tar_validation':tar_check, 'limits':r.LIMITS, 'network_contacted':False,
        'source_package_tar_mutated':False, 'resource_request_present':False, 'approval_present':False,
        'external_remote_source_and_model_inputs_verified':False, 'native_or_model_work_performed':False,
        'job_submitted':False, 'automatic_retry':False, 'resume':False, 'partial_outputs_preserved':True,
    }


def prepare(expected_plan_sha):
    r.require(type(expected_plan_sha) is str and r.HEX.fullmatch(expected_plan_sha), 'external transfer-plan SHA required')
    parent = r.directory(str(ARCHIVE))
    try:
        os.mkdir(ATTEMPT.name, 0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    new_json('prepare-started.json', {'started_at_utc':r.utc(), 'network_contacted':False,
             'plan_sha256':expected_plan_sha, 'automatic_retry':False})
    record = {'schema':'peano-hydra-retention-bootstrap-transfer-prepare-result-v1', 'network_contacted':False}
    try:
        plan, plan_raw, _, _ = context(expected_plan_sha)
        state = check_selected(plan)
        stream, before = bundle_open(plan['bundle'])
        try:
            def consume(name, item, expanded):
                remaining, hasher = item['bytes'], hashlib.sha256()
                while remaining:
                    raw = r.exact(expanded, min(65536, remaining))
                    remaining -= len(raw)
                    hasher.update(raw)
                r.require(hasher.hexdigest() == item['sha256'], 'tar payload differs: ' + name)
            tar_check = r.consume_tar(stream, plan['selected_files'], consume, plan['bundle'])
            r.require(stream.read(1) == b'' and r.identity(os.fstat(stream.fileno())) == before,
                      'local tar stream grew or changed')
        finally:
            stream.close()
        context(expected_plan_sha)
        r.require(check_selected(plan) == state, 'selected inputs changed during local preparation')
        prepared = prepared_record(plan, plan_raw, state, tar_check)
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
    result = {'schema':'peano-hydra-retention-bootstrap-transfer-send-result-v1', 'network_contacted':False,
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
        expected_plan_sha = prepared['plan']['sha256']
        plan, plan_raw, freeze_raw, authority_raw = context(expected_plan_sha)
        state = check_selected(plan)
        r.require(prepared == prepared_record(plan, plan_raw, state, prepared['tar_validation']),
                  'prepared package/helper/source binding changed')
        stream, before = bundle_open(plan['bundle'])
        try:
            header = {
                'schema':'peano-hydra-retention-bootstrap-transfer-header-v1',
                'plan_sha256':expected_plan_sha, 'plan_bytes':len(plan_raw), 'directive_sha256':r.DIRECTIVE_SHA,
                'source_commit':plan['source_commit'], 'local_source_clean':True,
                'send_started_at_utc':r.utc(), 'sender_sha256':prepared['sender']['sha256'],
                'receiver_sha256':RECEIVER_SHA, 'limits':r.LIMITS,
            }
            r.validate_header(header, plan)
            raw = r.canonical(header)
            r.require(len(raw) <= r.MAX_HEADER, 'send header byte cap')
            header_artifact = new_json('send-header.json', header)
            header_sha = r.sha(raw)
            prefix = r.MAGIC + struct.pack('>Q', len(raw)) + raw + plan_raw + freeze_raw + authority_raw
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
                              prefix=prefix, bundle_stream=stream, bundle=plan['bundle'])
            new_json('ssh-process.json', process)
            result['ssh_process'] = process
            r.require(r.identity(os.fstat(stream.fileno())) == before, 'tar changed during SSH transfer')
        finally:
            stream.close()
        r.require(check_selected(plan) == state, 'local inputs changed through transfer')
        context(expected_plan_sha)
        stream, _ = bundle_open(plan['bundle'])
        stream.close()
        result['local_inputs_rechecked'] = True
        r.require(process['reason'] == 'exited' and process['returncode'] == 0, 'transfer did not complete; no retry')
        remote_result = r.decode(process['stdout'].encode('utf-8'))
        r.require(remote_result.get('schema') == 'peano-hydra-retention-bootstrap-transfer-remote-result-v1'
                  and remote_result.get('status') == 'transferred-and-rehashed'
                  and remote_result.get('header_sha256') == header_sha
                  and remote_result.get('remote_root') == r.REMOTE_ROOT
                  and remote_result.get('source_commit') == plan['source_commit']
                  and remote_result.get('plan_sha256') == expected_plan_sha
                  and remote_result.get('directive_sha256') == r.DIRECTIVE_SHA
                  and remote_result.get('file_count') == plan['maximum_installed_files']
                  and remote_result.get('input_file_count') == plan['file_count']+1
                  and remote_result.get('source_files_sha256') == plan['source_files_sha256']
                  and remote_result.get('bootstrap_files_sha256') == plan['bootstrap_files_sha256']
                  and remote_result.get('exact_inventory_checked') is True
                  and remote_result.get('all_file_hashes_rechecked') is True
                  and remote_result.get('job_submission_performed') is False
                  and remote_result.get('installation_performed') is False
                  and remote_result.get('model_loaded') is False
                  and remote_result.get('native_work_performed') is False
                  and remote_result.get('resource_request_present') is False
                  and remote_result.get('approval_present') is False,
                  'remote bootstrap transfer receipt changed')
        provenance = remote_result['source_provenance'].encode('ascii')
        r.require(provenance == (plan['source_commit']+'\tfalse\t'+remote_result['transfer_started_at_utc']+'\n').encode('ascii')
                  and len(provenance) <= r.MAX_PROVENANCE
                  and r.sha(provenance) == remote_result['source_provenance_sha256']
                  and remote_result['input_total_bytes'] == plan['selected_uncompressed_bytes'] + len(provenance)
                  and remote_result['bundle'] == prepared['tar_validation'],
                  'actual provenance or bundle receipt changed')
        expected_durable = r.receipt_record(plan, header, header_sha, remote_result['transfer_started_at_utc'],
                                            provenance, prepared['tar_validation'])
        durable_raw = r.canonical(expected_durable) + b'\n'
        r.require(remote_result['remote_receipt'] == {'path':r.REMOTE_RECEIPT, **pin(durable_raw)}
                  and remote_result['files_sha256'] == expected_durable['files_sha256']
                  and remote_result['total_bytes'] == remote_result['input_total_bytes']+len(durable_raw)
                  and remote_result['total_bytes'] <= plan['maximum_installed_bytes']
                  and remote_result['file_count'] <= r.MAX_FILES
                  and 0 <= remote_result['cpu_seconds'] < r.LIMITS['remote_cpu_seconds']
                  and 0 <= remote_result['wall_seconds'] < r.LIMITS['remote_wall_seconds']
                  and 0 < remote_result['peak_rss_bytes'] <= r.LIMITS['remote_address_space_bytes'],
                  'durable bootstrap receipt or resource accounting differs from exact expected bytes')
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
    parser.add_argument('mode', choices=('build-plan', 'prepare', 'send'))
    parser.add_argument('--expected-freeze-receipt-sha256')
    parser.add_argument('--expected-source-commit')
    parser.add_argument('--expected-plan-sha256')
    parser.add_argument('--expected-prepared-plan-sha256')
    args = parser.parse_args()
    r.require(sys.flags.isolated and sys.dont_write_bytecode, 'invoke with -I -B')
    r.require(Path(__file__).absolute() == ARCHIVE / 'transfer-retention-bootstrap-01.py', 'fixed sender archive path required')
    r.require((args.mode == 'build-plan' and args.expected_freeze_receipt_sha256 is not None
               and args.expected_source_commit is not None and args.expected_plan_sha256 is None
               and args.expected_prepared_plan_sha256 is None)
              or (args.mode == 'prepare' and args.expected_plan_sha256 is not None
                  and args.expected_freeze_receipt_sha256 is None and args.expected_source_commit is None
                  and args.expected_prepared_plan_sha256 is None)
              or (args.mode == 'send' and args.expected_prepared_plan_sha256 is not None
                  and args.expected_freeze_receipt_sha256 is None and args.expected_source_commit is None
                  and args.expected_plan_sha256 is None), 'each stage requires only its actual external pins')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    fsize = r.MAX_BUNDLE if args.mode == 'build-plan' else r.LIMITS['receipt_file_bytes']
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
    def deadline(signum, frame):
        raise TimeoutError('local retention bootstrap90-second wall deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(90)
    try:
        if args.mode == 'build-plan':
            return build_plan(args.expected_freeze_receipt_sha256, args.expected_source_commit)
        if args.mode == 'prepare':
            return prepare(args.expected_plan_sha256)
        return send(args.expected_prepared_plan_sha256)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
