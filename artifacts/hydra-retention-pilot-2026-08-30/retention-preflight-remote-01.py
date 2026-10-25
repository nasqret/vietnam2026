"""One tokenizer-only preflight in the existing cached Helios CPU runtime.

This is a new CPU caller, not a change to any native proof-worker envelope.
It never invokes Slurm submission, downloads, installs, or a model constructor.
The fixed child runs under an owned process group, sampled RSS/output/wall
guards, and inherited per-process CPU/file limits. Failed output is retained.
"""
import time
STARTED = time.monotonic()

import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import signal
import stat
import subprocess
import sys

ROOT = Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-pilot-v1')
PARENT = ROOT.parent.parent
PACKAGE = ROOT / '_deploy/hydra-retention-pilot-v1'
CLI = ROOT / 'scripts/execute_peano_hydra_retention.py'
OUTPUT = ROOT / '_deploy/retention-token-preflight-01.json'
START = ROOT / '_deploy/retention-token-preflight-started-01.json'
RECEIPT = ROOT / '_deploy/retention-token-preflight-process-01.json'
CPU, WALL, RSS, PIPE, FILE = 180, 300, 2 * 1024**3, 256 * 1024, 4 * 1024**2
DEADLINE = STARTED + WALL
BOOTSTRAP_RECEIPT = '.peano-retention-bootstrap-receipt.json'


def require(value, message):
    if not value: raise ValueError(message)


def raw(path, maximum):
    for part in (path.parent, *path.parent.parents):
        require(stat.S_ISDIR(part.lstat().st_mode), 'non-directory/symlink input ancestor')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= maximum, 'unsafe or oversized input file')
        with os.fdopen(fd, 'rb', closefd=False) as stream: value = stream.read(maximum + 1)
        after, current = os.fstat(fd), path.lstat()
        signature = lambda item: (item.st_dev, item.st_ino, item.st_mode, item.st_nlink,
                                  item.st_size, item.st_mtime_ns, item.st_ctime_ns)
        require(len(value) == info.st_size and signature(info) == signature(after) == signature(current),
                'input changed while reading')
        return value
    finally: os.close(fd)


def pin(value): return {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}


def write_new(path, record):
    value = (json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    require(len(value) <= FILE, 'CPU receipt exceeds its bound')
    for parent in (path.parent, *path.parent.parents):
        require(stat.S_ISDIR(parent.lstat().st_mode), 'unsafe output parent')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)
    return pin(value)


def parse_process_stat(text, ticks, page_size):
    require(type(text) is str and len(text) <= 16384 and text.rfind(')') > 0, 'unreadable bounded /proc stat')
    fields = text[text.rfind(')') + 2:].split()
    require(len(fields) >= 22, 'incomplete /proc stat')
    counters = [int(fields[index]) for index in (11, 12, 13, 14)]
    require(all(value >= 0 for value in counters) and int(fields[21]) >= 0, 'negative process accounting')
    return {'group': int(fields[2]), 'start_ticks': int(fields[19]), 'state': fields[0],
            'rss': int(fields[21]) * page_size, 'direct_cpu': sum(counters[:2]) / ticks,
            'cpu_with_waited_children': sum(counters) / ticks}


def process_stat(pid):
    try:
        with open('/proc/' + str(pid) + '/stat', encoding='utf-8') as stream:
            text = stream.read(16385)
    except (FileNotFoundError, ProcessLookupError):
        return None
    # Permission/parse errors are not interpreted as zero resource usage.
    return parse_process_stat(text, os.sysconf('SC_CLK_TCK'), os.sysconf('SC_PAGE_SIZE'))


def sample_group(group, seen):
    total, members, cpu = 0, [], 0.0
    for name in os.listdir('/proc'):
        if not name.isdigit(): continue
        pid = int(name)
        value = process_stat(pid)
        if value is None: continue
        key = (pid, value['start_ticks'])
        if key in seen:
            seen[key] = max(seen[key], value['direct_cpu'])
            require(value['group'] == group, 'previously owned process escaped its group')
        if value['group'] != group: continue
        seen[key] = max(seen.get(key, 0.0), value['direct_cpu'])
        total += value['rss']
        cpu += value['cpu_with_waited_children']
        members.append({'pid': pid, 'start_ticks': value['start_ticks'], 'state': value['state']})
    require(len(members) <= 64, 'unexpected process count in owned preflight group')
    require(len(seen) <= 4096, 'owned process history exceeds its bounded receipt inventory')
    return total, members, cpu


def accounted_cpu(parent_cpu, waited_children_cpu, sampled_group_cpu, retained_direct_cpu):
    # These counters overlap, so never sum waited usage with its live/retained
    # descendants. /proc snapshots can themselves overlap across a wait; that
    # conservatively causes early rejection rather than claiming exact usage.
    return parent_cpu + max(waited_children_cpu, sampled_group_cpu, retained_direct_cpu)


def parent_limits():
    child_limits()
    def expired(_signum, _frame):
        raise TimeoutError('whole-call CPU preflight wall deadline')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, DEADLINE - time.monotonic()))


def child_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE, FILE))


def main():
    parent_limits()
    request_raw = sys.stdin.buffer.read(16385)
    require(0 < len(request_raw) <= 16384, 'bounded explicit CPU preflight request required')
    request = json.loads(request_raw)
    require(set(request) == {'schema', 'source_commit', 'inputs_sha256', 'cli_sha256', 'bootstrap_receipt', 'bootstrap_receipt_sha256'}
            and request['schema'] == 'peano-hydra-retention-tokenizer-cpu-request-v1', 'wrong CPU preflight request')
    require(sys.platform == 'linux' and not os.environ.get('SLURM_JOB_ID') and Path.cwd() == ROOT,
            'preflight must run outside any GPU allocation in the exact new Linux deployment')
    for key in ('inputs_sha256', 'cli_sha256', 'bootstrap_receipt_sha256'):
        require(type(request[key]) is str and re.fullmatch('[0-9a-f]{64}', request[key]), 'raw SHA pin missing')
    require(re.fullmatch('[0-9a-f]{40}', request['source_commit']), 'frozen commit missing')
    receipt_name = request['bootstrap_receipt']
    require(receipt_name == BOOTSTRAP_RECEIPT, 'exact retained bootstrap receipt required')
    inputs = raw(PACKAGE / 'inputs.json', FILE)
    source = raw(CLI, 65536)
    bootstrap = raw(ROOT / receipt_name, FILE)
    provenance = raw(ROOT / '.peano-source-provenance.tsv', 1024)
    require(pin(inputs)['sha256'] == request['inputs_sha256'] and pin(source)['sha256'] == request['cli_sha256']
            and pin(bootstrap)['sha256'] == request['bootstrap_receipt_sha256'], 'bootstrap/CLI/input bytes differ from external pins')
    require(re.fullmatch((request['source_commit'] + r'\tfalse\t[0-9TZ:+-]{1,40}\n').encode(), provenance), 'frozen source provenance differs')
    require(not any(os.path.lexists(path) for path in (OUTPUT, START, RECEIPT)), 'CPU preflight attempt already exists; no automatic retry')
    require(not os.path.lexists(PACKAGE / 'resource-request.json') and not os.path.lexists(PACKAGE / 'approval.json'),
            'bootstrap preflight must precede the final resource request')
    write_new(START, {'schema': 'peano-hydra-retention-cpu-preflight-start-v1', 'request': request,
        'started_at_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'limits': {'per_process_cpu_seconds': CPU, 'whole_wall_seconds': WALL, 'sampled_group_rss_bytes': RSS,
                   'sampled_whole_cpu_seconds': CPU, 'combined_child_output_bytes': PIPE, 'file_bytes': FILE},
        'model_weights_requested': False, 'gpu_allocation_requested': False, 'automatic_retry': False})
    arguments = [str(PARENT / '.venv-helios/bin/python'), '-I', '-B', '-X', 'pycache_prefix=/dev/null', str(CLI),
        '--token-preflight', '--inputs', str(PACKAGE / 'inputs.json'), '--expected-inputs-sha256', request['inputs_sha256'],
        '--output', str(OUTPUT)]
    script = 'set -euo pipefail\nmodule purge\nmodule load ML-bundle/25.10\nexec ' + shlex.join(arguments)
    environment = {k: v for k, v in os.environ.items() if not k.startswith(('PYTHON', 'SBATCH_', 'LD_', 'DYLD_'))
                   and k not in ('BASH_ENV', 'ENV')}
    environment.update(PYTHONHASHSEED='20260826', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPYCACHEPREFIX='/dev/null', PYTHONMALLOC='malloc', PYTHONUNBUFFERED='1', CUDA_VISIBLE_DEVICES='',
        HF_HOME=str(PARENT / '.cache/huggingface'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        TOKENIZERS_PARALLELISM='false', HF_HUB_DISABLE_TELEMETRY='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    child, selector = None, None
    outputs = {'stdout': bytearray(), 'stderr': bytearray()}
    peak, seen, error, sampled, group_cpu = 0, {}, None, 0.0, 0.0
    remaining, quiescent, output_seen = [], False, 0
    def failed(failure):
        nonlocal error
        error = error or (type(failure).__name__ + ': ' + ' '.join(str(failure).split()))[:2048]
    def usage():
        own, waited = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        parent_cpu = own.ru_utime + own.ru_stime
        waited_cpu = waited.ru_utime + waited.ru_stime
        return {'parent_cpu_seconds': parent_cpu, 'waited_children_cpu_seconds': waited_cpu,
                'sampled_group_cpu_seconds': group_cpu, 'retained_observed_direct_cpu_seconds': sum(seen.values()),
                'accounted_whole_cpu_seconds': accounted_cpu(parent_cpu, waited_cpu, group_cpu, sum(seen.values())),
                'parent_peak_rss_bytes': int(own.ru_maxrss) * 1024,
                'peak_sampled_parent_plus_group_rss_bytes': peak,
                'whole_wall_seconds': time.monotonic() - STARTED}
    def check_usage():
        measured = usage()
        require(measured['accounted_whole_cpu_seconds'] < CPU, 'whole-call sampled CPU cap')
        require(max(measured['parent_peak_rss_bytes'], peak) <= RSS, 'whole-call measured RSS cap')
        require(time.monotonic() < DEADLINE, 'whole-call wall deadline')
        return measured
    def sample():
        nonlocal peak, group_cpu, remaining
        memory, members, sampled_cpu = sample_group(child.pid, seen)
        parent = process_stat(os.getpid())
        require(parent is not None, 'parent resource accounting unavailable')
        peak = max(peak, memory + parent['rss'])
        group_cpu = max(group_cpu, sampled_cpu)
        remaining = [value for value in members if value['state'] not in ('Z', 'X')]
    def kill_owned():
        # The group is created by this Popen. Also stop an observed process
        # that escaped the group, but never a reused PID with another start.
        try: os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        for pid, start_ticks in tuple(seen):
            value = process_stat(pid)
            if value is not None and value['start_ticks'] == start_ticks:
                try: os.kill(pid, signal.SIGKILL)
                except ProcessLookupError: pass
    try:
        check_usage()
        require(time.monotonic() < DEADLINE - 5, 'no whole-call time remains for child and cleanup')
        child = subprocess.Popen(['/bin/bash', '-l', '-c', script], cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, preexec_fn=child_limits)
        selector = selectors.DefaultSelector()
        for name, stream in (('stdout', child.stdout), ('stderr', child.stderr)):
            os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or child.poll() is None:
            require(time.monotonic() < DEADLINE - 5, 'CPU preflight wall stop reserves final cleanup/publication')
            if time.monotonic() - sampled >= .1:
                sample(); sampled = time.monotonic()
                check_usage()
            for key, _ in selector.select(.05):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block: selector.unregister(key.fileobj); continue
                output_seen += len(block)
                available = PIPE - sum(map(len, outputs.values()))
                outputs[key.data].extend(block[:available])
                require(output_seen <= PIPE, 'CPU preflight child output cap')
        child.wait(timeout=min(1, max(.001, DEADLINE - time.monotonic())))
    except BaseException as failure:
        failed(failure)
    finally:
        if child is not None:
            try: kill_owned()
            except BaseException as failure: failed(failure)
            try: child.wait(timeout=min(3, max(.001, DEADLINE - time.monotonic() - 1)))
            except BaseException as failure: failed(failure)
            try:
                cleanup_deadline = min(time.monotonic() + 3, DEADLINE - 1)
                while True:
                    sample()
                    if not remaining:
                        quiescent = True
                        break
                    require(time.monotonic() < cleanup_deadline, 'owned process group did not become quiescent')
                    kill_owned()
                    time.sleep(.02)
            except BaseException as failure: failed(failure)
        else:
            quiescent = True
        if selector is not None:
            try: selector.close()
            except BaseException as failure: failed(failure)
        if child is not None:
            for stream in (child.stdout, child.stderr):
                if stream is not None:
                    try: stream.close()
                    except BaseException as failure: failed(failure)
    unchanged, payload = False, None
    try:
        unchanged = (raw(PACKAGE / 'inputs.json', FILE) == inputs and raw(CLI, 65536) == source
                     and raw(ROOT / receipt_name, FILE) == bootstrap and raw(ROOT / '.peano-source-provenance.tsv', 1024) == provenance)
        require(unchanged, 'externally pinned preflight inputs changed')
        require(child is not None and child.returncode == 0, 'preflight child did not exit successfully')
        require(quiescent, 'owned process cleanup was not verified')
        check_usage()
        if error is None:
            payload = raw(OUTPUT, FILE)
        check_usage()
    except BaseException as failure: failed(failure)
    measured = usage()
    try: check_usage()
    except BaseException as failure: failed(failure)
    passed = error is None and child is not None and child.returncode == 0 and quiescent and unchanged and payload is not None
    record = {'schema': 'peano-hydra-retention-cpu-preflight-process-v1', 'status': 'passed' if passed else 'failed',
        'request': request, 'command': arguments, 'returncode': None if child is None else child.returncode, 'error': error,
        'measurements': measured, 'observed_process_ids': sorted({pid for pid, _ in seen}),
        'remaining_live_owned_processes': remaining, 'owned_group_quiescent': quiescent,
        'input_pins_unchanged': unchanged, 'child_output_bytes_observed': output_seen,
        'stdout': outputs['stdout'].decode('utf-8', 'replace'), 'stderr': outputs['stderr'].decode('utf-8', 'replace'),
        'limits': {'per_process_cpu_seconds': CPU, 'whole_wall_seconds': WALL, 'sampled_group_rss_bytes': RSS,
                   'sampled_whole_cpu_seconds': CPU, 'combined_child_output_bytes': PIPE, 'file_bytes': FILE},
        'resource_measurement': 'Parent CPU plus max(waited-child CPU, peak sampled group utime/stime/cutime/cstime, retained observed direct CPU); parent+group RSS sampled. Snapshot overlap can reject conservatively; short-lived processes are not an exact instantaneous aggregate measurement.',
        'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
        'completion_requires_zero_exit_and_complete_response': True,
        'failed_outputs_deleted': False,
        'preflight': None if not passed else {'path': str(OUTPUT), **pin(payload)},
        'model_weights_requested': False, 'gpu_allocation_requested': False, 'automatic_retry': False}
    # All substantive postchecks and serialization stay inside the original
    # process-entry alarm. A retained receipt alone never implies zero exit.
    encoded_payload = None if not passed else base64.b64encode(payload).decode()
    record['measurements'] = usage()
    try: check_usage()
    except BaseException as failure:
        failed(failure)
        passed, encoded_payload = False, None
        record.update(status='failed', error=error, preflight=None)
    receipt_raw = (json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    response = {'receipt': {'path': str(RECEIPT), **pin(receipt_raw)}, 'record': record,
                'preflight_base64': encoded_payload}
    encoded = json.dumps(response, sort_keys=True, separators=(',', ':')).encode()
    require(len(encoded) <= 8 * 1024**2, 'CPU receipt transport bound')
    require(time.monotonic() < DEADLINE, 'no time remains for CPU failure/completion receipt')
    if passed: check_usage()
    require(write_new(RECEIPT, record) == pin(receipt_raw), 'published CPU receipt identity differs')
    # write_new returns the raw identity, without the transport-only path.
    require(raw(RECEIPT, FILE) == receipt_raw, 'published CPU receipt differs from its transport pin')
    sys.stdout.buffer.write(encoded + b'\n'); sys.stdout.buffer.flush()
    if passed: check_usage()
    require(time.monotonic() < DEADLINE, 'CPU receipt publication exceeded whole-call wall')
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
