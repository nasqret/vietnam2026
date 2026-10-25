#!/usr/bin/env python3
"""One-use local process-tree supervision for the fixed frozen v28 hotspot run.

This is a sampled resource guard for reviewed code, not a hostile-code sandbox
or an operating-system accounting attestation. No network or scheduler actions.
The production CLI has no command, source-root or resource-limit override.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-advancement-2026-08-30')
SOURCE = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-advancement-execution-20260830')
HELPER = ARCHIVE / 'run-v28-hotspots-supervised.py'
CONTROLLER = 'scripts/check_peano_hydra_review_v28.py'
EPOCH = 'f64b5f100c9c9bc77049ea627f13e641be83ac72aaa474216682076679a468ad'
SCHEMA = 'peano-hydra-v28-hotspot-process-tree-supervision-v1'
MAX_RECORD = 32 * 1024**2
MAX_SOURCE_TOTAL = 128 * 1024**2
MAX_SOURCE_FILES = 2048
MAX_OBSERVED_PROCESSES = 2048
SAMPLE_SECONDS = 0.05
SHA = re.compile(r'[a-f0-9]{64}\Z')
CLAIMS = {'h0_complete': False, 'h1_complete': False, 'reference_ready': False,
          'human_review_granted': False, 'model_training_authorized': False,
          'gpu_execution_authorized': False, 'research_claim_eligible': False,
          'network_access_requested': False, 'automatic_retry': False}


class GuardError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise GuardError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    require(type(raw) is bytes and len(raw) <= MAX_RECORD, 'metadata byte bound exceeded')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise GuardError('nonfinite JSON value: ' + value)
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    require(type(result) is dict, 'one JSON object required')
    return result


def absolute(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and path == path.resolve(strict=False), 'canonical nonsymlink absolute path required')
    return path


def fingerprint(path, *, maximum=MAX_RECORD, retain=False, deadline=None):
    path = absolute(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 <= before.st_size <= maximum, 'bounded regular nonsymlink file required: ' + str(path))
        sha, body, size = hashlib.sha256(), bytearray(), 0
        while block := stream.read(65536):
            if deadline is not None:
                require(time.monotonic() < deadline, 'whole supervisor wall deadline during file checks')
            sha.update(block)
            size += len(block)
            require(size <= maximum, 'input grew beyond byte bound')
            if retain:
                body.extend(block)
        after = os.fstat(stream.fileno())
        current = path.lstat()
        signature = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
        require(signature(before) == signature(after) == signature(current) and size == before.st_size,
                'input changed while hashing')
        return {'bytes': size, 'sha256': sha.hexdigest()}, bytes(body)


def write_once(path, raw):
    require(type(raw) is bytes and len(raw) <= MAX_RECORD, 'retained metadata exceeds bound')
    path = absolute(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


@dataclass(frozen=True)
class Limits:
    wall_seconds: float = 300
    cpu_seconds: float = 180
    rss_bytes: int = 2 * 1024**3
    output_bytes: int = 64 * 1024**2

    def __post_init__(self):
        for name, maximum in (('wall_seconds', 300), ('cpu_seconds', 180)):
            value = getattr(self, name)
            require(type(value) in (int, float) and math.isfinite(value) and 0.1 <= value <= maximum,
                    'invalid or enlarged supervisor ' + name)
        require(type(self.rss_bytes) is int and 32 * 1024**2 <= self.rss_bytes <= 2 * 1024**3,
                'invalid or enlarged supervisor RSS cap')
        require(type(self.output_bytes) is int and 512 * 1024 <= self.output_bytes <= 64 * 1024**2,
                'invalid or enlarged supervisor output cap')


def cpu_seconds(value):
    require(type(value) is str and re.fullmatch(r'(?:[0-9]+-)?[0-9]+:[0-9]{2}(?::[0-9]{2})?(?:\.[0-9]{1,6})?', value),
            'unreadable ps CPU counter')
    days, rest = (value.split('-', 1) if '-' in value else ('0', value))
    parts = rest.split(':')
    require(len(parts) in (2, 3), 'invalid ps CPU field count')
    hours, minutes, seconds = (['0', *parts] if len(parts) == 2 else parts)
    require(float(seconds) < 60 and (len(parts) == 2 or int(minutes) < 60), 'invalid ps CPU range')
    return int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_ps(raw):
    require(type(raw) is bytes and len(raw) <= 8 * 1024**2, 'ps output exceeds its bound')
    rows = {}
    for line in raw.decode('utf-8', 'strict').splitlines():
        fields = line.split(None, 11)
        require(len(fields) == 12 and all(re.fullmatch(r'[0-9]+', item) for item in fields[:4]),
                'malformed process-table row')
        pid, ppid, pgid, rss = map(int, fields[:4])
        require(pid not in rows and len(rows) < 32768, 'duplicate or excessive ps process inventory')
        birth = ' '.join(fields[6:11])
        require(re.fullmatch(r'[A-Za-z]{3} [A-Za-z]{3} [0-9]{1,2} [0-9:]{8} [0-9]{4}', birth),
                'unreadable process start identity')
        rows[pid] = {'pid': pid, 'ppid': ppid, 'pgid': pgid, 'rss_bytes': rss * 1024,
                     'cpu_seconds': cpu_seconds(fields[4]), 'state': fields[5],
                     'birth': birth, 'command_name': Path(fields[11]).name[:256]}
    return rows


def snapshot():
    """Read bounded ps metadata. Never persist unrelated process rows or argv."""
    environment = {**os.environ, 'LC_ALL': 'C', 'TZ': 'UTC'}
    command = ['/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss=,time=,stat=,lstart=,comm=']
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=environment)
    try:
        # ps is a fixed local system reader, not a supplied executable. Its
        # output is bounded again before parsing; the timeout is one second.
        stdout, stderr = process.communicate(timeout=1)
        require(process.returncode == 0 and not stderr and len(stdout) <= 8 * 1024**2,
                'process-tree sampler unavailable or exceeded bounds')
        return parse_ps(stdout)
    except BaseException:
        process.kill()
        process.wait(timeout=1)
        raise


class Ownership:
    """Remember PID plus observed start identity across reparenting/sessions."""
    def __init__(self, root_pid):
        self.root_pid = root_pid
        self.records = {}
        self.live = {}
        self.zombies = {}
        self.samples = 0
        self.peak_rss = 0
        self.max_live = 0
        self.post_controller_exit_samples = 0

    def update(self, rows, *, controller_exited=False):
        if not self.records:
            require(self.root_pid in rows, 'owned entry process was not observed before execution')
            first = rows[self.root_pid]
            self.records[(first['pid'], first['birth'])] = dict(first)
        known = {pid for pid, birth in self.records if pid in rows and rows[pid]['birth'] == birth}
        changed = True
        while changed:
            additions = {pid for pid, row in rows.items() if row['ppid'] in known and pid not in known}
            changed = bool(additions)
            known.update(additions)
        require(len(self.records) + len(known) <= 2 * MAX_OBSERVED_PROCESSES,
                'owned process inventory exceeded its fixed bound')
        active, zombies = {}, {}
        for pid in sorted(known):
            row = rows[pid]
            key = (pid, row['birth'])
            if key not in self.records:
                require(len(self.records) < MAX_OBSERVED_PROCESSES, 'too many owned processes')
                self.records[key] = dict(row)
            saved = self.records[key]
            saved['cpu_seconds'] = max(saved['cpu_seconds'], row['cpu_seconds'])
            saved['rss_bytes'] = max(saved['rss_bytes'], row['rss_bytes'])
            saved['last_ppid'], saved['last_pgid'] = row['ppid'], row['pgid']
            (zombies if 'Z' in row['state'] else active)[pid] = row
        self.live, self.zombies = active, zombies
        self.samples += 1
        if controller_exited and active:
            self.post_controller_exit_samples += 1
        # Include the supervisor itself as additional conservative overhead.
        combined = sum(row['rss_bytes'] for row in active.values()) + rows.get(os.getpid(), {}).get('rss_bytes', 0)
        self.peak_rss = max(self.peak_rss, combined)
        self.max_live = max(self.max_live, len(active))
        return sum(row['cpu_seconds'] for row in self.records.values()), combined

    def matching(self, rows):
        return [pid for pid, birth in self.records if pid in rows and rows[pid]['birth'] == birth]


def retained_bytes(directory):
    total, count = 0, 0
    pending = [directory]
    while pending:
        parent = pending.pop()
        with os.scandir(parent) as entries:
            for entry in entries:
                count += 1
                require(count <= 4096 and not entry.is_symlink(), 'unsafe or excessive retained output entries')
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(entry.path))
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'output is not one regular owned file')
                    total += info.st_size
    return total


def _signal(pid, sig):
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        pass


def _reap(process):
    if process.returncode is not None:
        return None
    try:
        pid, status, usage = os.wait4(process.pid, os.WNOHANG)
    except ChildProcessError:
        raise GuardError('controller was reaped outside its owner')
    if not pid:
        return None
    process.returncode = os.waitstatus_to_exitcode(status)
    return {'cpu_seconds': usage.ru_utime + usage.ru_stime,
            'peak_rss_bytes': int(usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024),
            'accounting_scope': 'OS wait4 for direct controller; not summed again with observed descendants'}


def cleanup(process, ownership, *, deadline):
    """Use matching identities, never kill an unowned session or an unrelated PID."""
    errors, signals, usage = [], [], None
    try:
        rows = snapshot()
        ownership.update(rows, controller_exited=process.returncode is not None)
    except BaseException as error:
        errors.append(str(error)[:512])
        rows = {}
    # SIGINT activates the pinned Python controller's existing finally/wait4
    # cleanup. Tracked descendants are also signalled in their own sessions.
    for pid in sorted(ownership.matching(rows), key=lambda p: p == process.pid):
        sig = signal.SIGINT if pid == process.pid else signal.SIGTERM
        _signal(pid, sig)
        signals.append({'pid': pid, 'signal': int(sig)})
    if not rows and process.returncode is None:
        # A direct unreaped child cannot have been PID-reused.
        _signal(process.pid, signal.SIGINT)
    grace = min(deadline, time.monotonic() + 0.5)
    while time.monotonic() < deadline:
        reaped = _reap(process)
        if reaped is not None:
            usage = reaped
        try:
            rows = snapshot()
            ownership.update(rows, controller_exited=process.returncode is not None)
        except BaseException as error:
            errors.append(str(error)[:512])
            if process.returncode is None:
                _signal(process.pid, signal.SIGKILL)
            break
        if not ownership.live and process.returncode is not None:
            break
        if time.monotonic() >= grace:
            for pid in ownership.matching(rows):
                if 'Z' not in rows[pid]['state']:
                    _signal(pid, signal.SIGKILL)
                    signals.append({'pid': pid, 'signal': int(signal.SIGKILL)})
        time.sleep(0.02)
    if process.returncode is None:
        _signal(process.pid, signal.SIGKILL)
        # Nonblocking polling preserves the enclosing wall bound.
        until = min(deadline, time.monotonic() + 0.2)
        while process.returncode is None and time.monotonic() < until:
            usage = _reap(process) or usage
            time.sleep(0.01)
    return {'signals': signals[:4096], 'errors': errors[:16],
            'controller_reaped': process.returncode is not None,
            'remaining_live_owned_pids': sorted(ownership.live),
            'remaining_zombie_owned_pids': sorted(ownership.zombies),
            'grandchild_reaping': 'performed by their own parents or the OS; supervisor cannot wait4 nonchildren'}, usage


def _environment():
    result = {key: value for key, value in os.environ.items()
              if not key.startswith(('LD_', 'DYLD_', 'PYTHON', 'GIT_', 'SLURM_', 'SBATCH_'))
              and key not in {'BASH_ENV', 'ENV', 'LEAN_PATH', 'LEAN_SRC_PATH', 'LEAN_SYSROOT', 'LEAN_OPTS'}}
    result['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin'
    result['PYTHONDONTWRITEBYTECODE'] = '1'
    return result


def owned_entry():
    """Wait until the owner observes our PID/start identity, then exec once."""
    require(sys.flags.isolated and sys.dont_write_bytecode, 'owned entry requires isolated uncached Python')
    request = decode(sys.stdin.buffer.read(65537))
    require(set(request) == {'command', 'cwd', 'cpu_seconds'} and type(request['command']) is list
            and 1 <= len(request['command']) <= 32 and all(type(x) is str and '\x00' not in x and len(x) <= 8192
                                                        for x in request['command']), 'invalid owned-entry command')
    absolute(request['command'][0])
    cwd = absolute(request['cwd'])
    cpu = request['cpu_seconds']
    require(type(cpu) is int and 1 <= cpu <= 180, 'invalid owned-entry CPU fallback')
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
    os.chdir(cwd)
    os.execvpe(request['command'][0], request['command'], os.environ)


def supervise(command, *, cwd, directory, limits, metadata, started=None, deadline=None):
    """Internal engine; production callers use the fixed CLI below.

    Small test fixtures may supply lower limits and arbitrary *local fixture*
    commands. Production exposes neither of those interfaces as CLI options.
    """
    require(type(limits) is Limits and type(command) is tuple, 'exact local guard contract required')
    directory, cwd = absolute(directory), absolute(cwd)
    require(directory.is_dir(), 'fresh owner-created archive required')
    started = time.monotonic() if started is None else started
    deadline = started + limits.wall_seconds if deadline is None else deadline
    cleanup_margin = min(5.0, limits.wall_seconds / 4)
    run_deadline = deadline - cleanup_margin
    metadata_reserve = min(1024**2, limits.output_bytes // 4)
    data_cap = limits.output_bytes - metadata_reserve
    interpreter = str(Path(sys.executable).resolve(strict=True))
    process = None
    ownership = None
    selector = selectors.DefaultSelector()
    logs, descriptors = {}, {}
    reason, error, usage, cleanup_record = 'exited', None, None, None
    baseline_self = resource.getrusage(resource.RUSAGE_SELF)
    baseline_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    sampled_cpu, accounted_cpu, streamed_bytes, next_sample = 0.0, 0.0, 0, 0.0
    controller_usage_removed = 0.0
    try:
        snapshot()  # Fail before the target starts if macOS process access is denied.
        for label in ('stdout', 'stderr'):
            path = directory / (label + '.log')
            logs[label] = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        process = subprocess.Popen((interpreter, '-I', '-B', str(HELPER), '--owned-entry'),
            cwd=cwd, env=_environment(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True)
        ownership = Ownership(process.pid)
        ownership.update(snapshot())
        process.stdin.write(canonical({'command': list(command), 'cwd': str(cwd),
                                      'cpu_seconds': int(math.ceil(limits.cpu_seconds))}))
        process.stdin.close()
        for label, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while True:
            now = time.monotonic()
            if now >= run_deadline:
                reason = 'wall-limit'
                break
            reaped = _reap(process)
            if reaped is not None:
                usage = reaped
                controller_usage_removed = usage['cpu_seconds']
            if now >= next_sample:
                rows = snapshot()
                sampled_cpu, combined_rss = ownership.update(rows, controller_exited=process.returncode is not None)
                self_now = resource.getrusage(resource.RUSAGE_SELF)
                children_now = resource.getrusage(resource.RUSAGE_CHILDREN)
                own_cpu = (self_now.ru_utime + self_now.ru_stime - baseline_self.ru_utime - baseline_self.ru_stime)
                # Waited direct children are only the sampler and controller.
                # Remove the controller wait4 charge before adding ps overhead;
                # max() below avoids double-counting descendant observations.
                sampler_cpu = max(0.0, children_now.ru_utime + children_now.ru_stime
                                  - baseline_children.ru_utime - baseline_children.ru_stime - controller_usage_removed)
                accounted_cpu = max(sampled_cpu, controller_usage_removed) + own_cpu + sampler_cpu
                if accounted_cpu >= limits.cpu_seconds:
                    reason = 'sampled-aggregate-cpu-limit'
                    break
                if combined_rss >= limits.rss_bytes:
                    reason = 'sampled-combined-rss-limit'
                    break
                if retained_bytes(directory) >= data_cap:
                    reason = 'retained-output-limit'
                    break
                next_sample = time.monotonic() + SAMPLE_SECONDS
            for key, _ in selector.select(0.02):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                room = max(0, data_cap - retained_bytes(directory))
                kept = block[:room]
                if kept:
                    os.write(logs[key.data], kept)
                streamed_bytes += len(block)
                if len(block) > room:
                    reason = 'retained-output-limit'
                    break
            if reason != 'exited':
                break
            if process.returncode is not None and not ownership.live and not selector.get_map():
                break
        if reason == 'exited' and process.returncode != 0:
            reason = 'controller-failed'
    except BaseException as failure:
        reason, error = 'guard-failed', type(failure).__name__ + ': ' + str(failure)[:2000]
    finally:
        if process is not None:
            if ownership is not None:
                cleanup_record, cleanup_usage = cleanup(process, ownership, deadline=deadline)
                usage = usage or cleanup_usage
            elif process.returncode is None:
                _signal(process.pid, signal.SIGKILL)
                usage = _reap(process)
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        selector.close()
        for descriptor in logs.values():
            os.fsync(descriptor)
            os.close(descriptor)
    for label in logs:
        descriptors[label] = fingerprint(directory / (label + '.log'), maximum=limits.output_bytes)[0]
    if ownership is not None:
        sampled_cpu = sum(row['cpu_seconds'] for row in ownership.records.values())
    self_now = resource.getrusage(resource.RUSAGE_SELF)
    children_now = resource.getrusage(resource.RUSAGE_CHILDREN)
    own_cpu = self_now.ru_utime + self_now.ru_stime - baseline_self.ru_utime - baseline_self.ru_stime
    controller_usage_removed = 0.0 if usage is None else usage['cpu_seconds']
    sampler_cpu = max(0.0, children_now.ru_utime + children_now.ru_stime
                      - baseline_children.ru_utime - baseline_children.ru_stime - controller_usage_removed)
    accounted_cpu = max(sampled_cpu, controller_usage_removed) + own_cpu + sampler_cpu
    elapsed = time.monotonic() - started
    live = [] if ownership is None else sorted(ownership.live)
    success = (reason == 'exited' and process is not None and process.returncode == 0 and not live
               and elapsed <= limits.wall_seconds and accounted_cpu < limits.cpu_seconds
               and (ownership is None or ownership.peak_rss < limits.rss_bytes))
    return {'schema': SCHEMA, 'status': 'process-completed-with-open-gates' if success else 'stopped-or-failed',
            'reason': reason, 'error': error, 'command': list(command), 'cwd': str(cwd),
            'limits': asdict(limits), 'sample_interval_seconds': SAMPLE_SECONDS,
            'returncode': None if process is None else process.returncode,
            'wall_seconds': elapsed, 'accounted_cpu_lower_bound_seconds': accounted_cpu,
            'sampled_owned_process_cpu_seconds': sampled_cpu,
            'supervisor_self_cpu_seconds': own_cpu, 'waited_sampler_cpu_seconds': sampler_cpu,
            'peak_sampled_combined_rss_bytes': 0 if ownership is None else ownership.peak_rss,
            'max_observed_live_owned_processes': 0 if ownership is None else ownership.max_live,
            'post_controller_exit_live_samples': 0 if ownership is None else ownership.post_controller_exit_samples,
            'observed_processes': [] if ownership is None else list(ownership.records.values()),
            'controller_wait4': usage, 'cleanup': cleanup_record, 'remaining_live_owned_pids': live,
            'logs': descriptors, 'pipe_bytes_observed': streamed_bytes, 'retained_bytes_before_receipt': retained_bytes(directory),
            'metadata': metadata,
            'measurement': {'cpu': 'sum of per-PID maximum sampled own CPU; max with direct wait4; plus supervisor/sampler overhead',
                'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
                'rss': 'sampled sum of live owned controller/descendant RSS plus supervisor RSS; shared pages may be counted more than once',
                'ownership': 'observed PID/start identity and parent ancestry retained after reparenting and across new sessions',
                'unobserved_daemon_containment_guaranteed': False,
                'limitations': 'short-lived processes and exit-between-sample CPU tails may be missed; ps birth identity has one-second precision; no hostile-daemon sandbox'},
            **CLAIMS}


def source_inputs(plan, source_pin, *, deadline):
    require(source_pin.get('schema') == 'peano-hydra-origin-source-bundle-v1'
            and source_pin.get('epoch_version') == 'v28'
            and type(source_pin.get('files')) is dict and 1 <= len(source_pin['files']) <= MAX_SOURCE_FILES
            and source_pin.get('files_sha256') == digest(source_pin['files']), 'invalid frozen original-source pin')
    source = plan['source']
    require(source['git_dirty'] is False and source['git_commit'] == source_pin['git_commit']
            and re.fullmatch(r'[a-f0-9]{40}', source['git_commit'])
            and source['files_sha256'] == digest(source['files']), 'plan lost exact clean frozen source identity')
    require(CONTROLLER in source['files'] and set(source['files']) <= set(source_pin['files']),
            'frozen original-source pin omits controller/review files')
    total, checked = 0, {}
    for relative, item in sorted(source_pin['files'].items()):
        require(type(relative) is str and PurePosixPath(relative).as_posix() == relative
                and not relative.startswith('/') and all(part not in ('', '.', '..') and not part.startswith('.')
                                                        for part in relative.split('/')), 'unsafe source pin path')
        require(type(item) is dict and set(item) == {'bytes', 'sha256', 'git_blob', 'mode'}
                and type(item['bytes']) is int and 0 <= item['bytes'] <= 64 * 1024**2
                and type(item['sha256']) is str and SHA.fullmatch(item['sha256'])
                and item['mode'] in {'100644', '100755'}, 'invalid source pin descriptor')
        total += item['bytes']
        require(total <= MAX_SOURCE_TOTAL, 'frozen source inventory exceeds unchanged 128 MiB ceiling')
        observed, _ = fingerprint(SOURCE / relative, maximum=item['bytes'], deadline=deadline)
        require(observed == {key: item[key] for key in ('bytes', 'sha256')}, 'frozen source bytes changed: ' + relative)
        if relative in source['files']:
            require(observed == source['files'][relative], 'review plan differs from full frozen source pin')
        checked[relative] = observed
    return {'files': len(checked), 'bytes': total, 'checked_files_sha256': digest(checked),
            'git_commit': source['git_commit'], 'review_files_sha256': source['files_sha256'],
            'original_source_files_sha256': source_pin['files_sha256']}


def check_plan(plan):
    require(plan.get('schema') == 'peano-hydra-reference-cold-review-v28-v1'
            and plan.get('status') == 'planned' and plan.get('mode') == 'native-hotspots'
            and plan.get('execution_root') == str(SOURCE) and plan.get('epoch_sha256') == EPOCH
            and plan.get('plan_sha256') == digest({k: v for k, v in plan.items() if k != 'plan_sha256'}),
            'only the exact frozen v28 native-hotspots plan can execute')
    require(plan['reference'] is None and plan['reference_project'] is None
            and plan['cold_plan']['target_count'] == 2764
            and plan['cold_selection']['indices'] == [1108, 1940]
            and plan['cold_selection']['batches'] == [[1108], [1940]]
            and plan['cold_selection']['passes'] == 2
            and plan['cold_selection']['limits'] == {'cpu_seconds': 30, 'wall_seconds': 45,
                'rss_bytes': 1024**3, 'output_bytes': 1024**2}
            and plan['worker_reservations']['workers'] == 4
            and plan['worker_reservations']['sum_worker_cpu_seconds'] == 120
            and plan['worker_reservations']['sum_worker_wall_seconds'] == 180,
            'hotspot target/worker reservation changed')
    require(all(plan[key] is False for key in ('h0_complete', 'h1_complete', 'research_claim_eligible',
                'model_training_authorized', 'independent_human_review_granted', 'sealed_benchmark')),
            'a plan cannot grant research or allocation approval')


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if arguments == ['--owned-entry']:
        owned_entry()
        return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--source-pin-file', type=Path, required=True)
    parser.add_argument('--source-pin-sha256', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(arguments)
    require(sys.flags.isolated and sys.dont_write_bytecode and Path(__file__).absolute() == HELPER,
            'run the exact archived helper with isolated uncached Python')
    require(sys.platform in {'darwin', 'linux'} and hasattr(os, 'wait4'), 'Unix process accounting required')
    for pin in (args.plan_sha256, args.helper_sha256, args.source_pin_sha256):
        require(type(pin) is str and SHA.fullmatch(pin), 'all external raw pins are required')
    output = absolute(args.output_dir)
    require(output.parent == ARCHIVE and re.fullmatch(r'native-hotspots-[A-Za-z0-9_-]{1,80}', output.name),
            'one fresh immediate native-hotspots archive is required')
    require(not output.exists() and not output.is_symlink(), 'one-use output already exists; no retry or overwrite')
    require(fingerprint(HELPER)[0]['sha256'] == args.helper_sha256, 'helper changed from its external raw pin')
    started, limits = time.monotonic(), Limits()
    initial_usage = resource.getrusage(resource.RUSAGE_SELF)
    initial_self_cpu = initial_usage.ru_utime + initial_usage.ru_stime
    deadline = started + limits.wall_seconds
    output.mkdir(mode=0o700)
    metadata = {'source_root': str(SOURCE), 'plan_file': str(args.plan), 'plan_file_sha256': args.plan_sha256,
                'helper_file_sha256': args.helper_sha256, 'source_pin_file': str(args.source_pin_file),
                'source_pin_file_sha256': args.source_pin_sha256,
                'started_at': datetime.now(timezone.utc).isoformat(), 'native_calibration_requested': True}
    write_once(output / 'one-use-claim.json', canonical({'schema': SCHEMA, 'metadata': metadata,
                                                      'limits': asdict(limits), **CLAIMS}) + b'\n')
    try:
        plan_pin, raw_plan = fingerprint(args.plan, retain=True, deadline=deadline)
        source_pin_descriptor, raw_source = fingerprint(args.source_pin_file, maximum=2 * 1024**2,
                                                       retain=True, deadline=deadline)
        require(plan_pin['sha256'] == args.plan_sha256 and source_pin_descriptor['sha256'] == args.source_pin_sha256,
                'external plan/source raw bytes differ')
        plan, source_pin = decode(raw_plan), decode(raw_source)
        check_plan(plan)
        before = source_inputs(plan, source_pin, deadline=deadline)
        write_once(output / 'plan-input.json', raw_plan)
        write_once(output / 'source-pin-input.json', raw_source)
        interpreter = str(Path(sys.executable).resolve(strict=True))
        metadata['interpreter'] = {'path': interpreter, **fingerprint(Path(interpreter), maximum=128 * 1024**2)[0]}
        command = (interpreter, '-I', '-B', str(SOURCE / CONTROLLER), '--run',
                   '--plan-file', str(output / 'plan-input.json'), '--plan-sha256', args.plan_sha256,
                   '--output-dir', str(output / 'calibration'))
        before_supervision = resource.getrusage(resource.RUSAGE_SELF)
        result = supervise(command, cwd=SOURCE, directory=output, limits=limits,
                           metadata=metadata, started=started, deadline=deadline - 5)
        after_supervision = resource.getrusage(resource.RUSAGE_SELF)
        after = source_inputs(plan, source_pin, deadline=deadline)
        require(fingerprint(args.plan)[0] == plan_pin and fingerprint(args.source_pin_file, maximum=2 * 1024**2)[0] == source_pin_descriptor
                and fingerprint(HELPER)[0]['sha256'] == args.helper_sha256 and before == after,
                'plan/helper/source drifted during the one-use run')
        result.update(source_files_before=before, source_files_after=after, source_files_unchanged=True,
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      wall_seconds_including_postchecks=time.monotonic() - started)
        final_usage = resource.getrusage(resource.RUSAGE_SELF)
        source_check_cpu = (before_supervision.ru_utime + before_supervision.ru_stime - initial_self_cpu
                            + final_usage.ru_utime + final_usage.ru_stime
                            - after_supervision.ru_utime - after_supervision.ru_stime)
        result['outer_source_check_cpu_seconds'] = source_check_cpu
        result['accounted_cpu_lower_bound_including_postchecks_seconds'] = result['accounted_cpu_lower_bound_seconds'] + source_check_cpu
        require(result['wall_seconds_including_postchecks'] <= limits.wall_seconds,
                'whole supervisor wall cap exceeded during postchecks')
        require(result['accounted_cpu_lower_bound_including_postchecks_seconds'] < limits.cpu_seconds,
                'sampled aggregate CPU cap exceeded including source checks')
        raw_result = canonical(result) + b'\n'
        require(retained_bytes(output) + len(raw_result) <= limits.output_bytes, 'retained output cap exceeded')
        descriptor = write_once(output / 'supervision.json', raw_result)
        print(json.dumps({'status': result['status'], 'receipt': str(output / descriptor['path']),
                          'sha256': descriptor['sha256'], **CLAIMS}, sort_keys=True), flush=True)
        return 0 if result['status'] == 'process-completed-with-open-gates' else 1
    except BaseException as failure:
        record = {'schema': SCHEMA, 'status': 'preflight-or-postcheck-failed-partial-archive-retained',
                  'metadata': metadata, 'error_type': type(failure).__name__, 'error': str(failure)[:4000],
                  'wall_seconds': time.monotonic() - started, **CLAIMS}
        if 'result' in locals():
            record['supervision'] = result
        write_once(output / 'failure.json', canonical(record) + b'\n')
        print(json.dumps({'status': record['status'], 'archive': str(output), 'error': record['error']}), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
