"""Observe one actually released retention evaluation; never launch or retry it.

Adapted from the reviewed training watcher. Each slot invokes the unchanged
bounded read-only observer once. Failed/uncertain observations stop this
watcher. Only EVALUATION_LIVE_STATUS.md is a mutable convenience view; every
underlying observation and the one-use start/result records remain separate.
An observed HEAD counter is operational progress, never a proof score.
"""
import time
STARTED = time.monotonic()
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import tempfile

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
HELPER = ARCHIVE / 'watch-retention-evaluation-01.py'
BASE = ARCHIVE / 'watch-retention-training-01.py'
BASE_SHA = '7b27f0933f5dceb22ffb36f3342500dd4d1da8fb360748208fc134ac4e5cf93f'
OBSERVER = ARCHIVE / 'observe-retention-job-01.py'
OBSERVER_SHA = 'b6571e17bc906ee698e62d4dace2c9d44b7390c59d8b637720ad6eddb33ee0c7'
LAUNCHER = ARCHIVE / 'invoke-retention-launch-01.py'
LAUNCHER_SHA = '23675c909b1824884e2911c8a26d33e64e013304e6be4bdc7b153d5470d0f3c1'
LAUNCH = ARCHIVE / 'launch-evaluate-submit-01.json'
COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
APPROVAL = '556cef2186a2003bf90ea327b927cc6cb3ea6ec0bd57f65e421bb6841e74d233'
HEADER = '224ad02b154eb32a64e07cfd02710f81020cb4b108c83d6514b2dcf918802333'
PROFILE, RUN_ID = 'peano-hydra-retention-pilot-v1', 'retention-pilot-v1'
STILL_ACTIVE = {'PENDING', 'RUNNING', 'CONFIGURING', 'COMPLETING', 'SUSPENDED'}
LIVE = ARCHIVE / 'EVALUATION_LIVE_STATUS.md'
SCHEMA = 'peano-hydra-retention-read-only-evaluation-watch-v1'
MAX_WALL, MAX_OBSERVATIONS, INTERVAL = 7500, 125, 60


def require(value, message):
    if not value: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def read_file(path, maximum):
    require(path.is_absolute() and path == path.resolve(strict=True), 'canonical nonsymlink local input required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'bounded single-link regular input required')
        raw = stream.read(maximum + 1)
        signature = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size, x.st_mtime_ns, x.st_ctime_ns, x.st_nlink)
        require(len(raw) == before.st_size and signature(before) == signature(os.fstat(stream.fileno())) == signature(path.lstat()),
                'local input changed during read')
    return raw


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 8 * 1024**2, 'bounded JSON object required')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate metadata key')
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(value) is dict, 'metadata must be an object')
    canonical(value)
    return value


def validate_submit(record, job):
    """A successful pinned original submit returns only after durable release."""
    require(record.get('schema') == 'peano-hydra-retention-launch-invocation-v1'
        and record.get('status') == 'passed' and record.get('mode') == 'submit' and record.get('stage') == 'evaluate'
        and record.get('helper_sha256') == LAUNCHER_SHA and record.get('remote_command_started') is True
        and record.get('automatic_retry') is False and record.get('frozen_source_modified') is False,
        'actual successful evaluation submission receipt required; no draft, training, test-only or uncertain submit')
    process, context, result = record['process'], record['context'], record['result']
    require(process['returncode'] == 0 and process['reason'] == 'exited' and process['error'] is None
        and decode(process['stdout'].encode()) == result, 'submission result differs from actual successful frozen CLI stdout')
    identity = context['identity']
    require(context['source_header_sha256'] == HEADER == hashlib.sha256(canonical(identity)).hexdigest()
        and identity['approval_sha256'] == APPROVAL and identity['source_commit'] == COMMIT
        and context['reservations']['evaluate'] == {'seconds': 3600, 'gpus': 1, 'cpus': 8, 'memory_gib': 64},
        'submitted evaluation changed exact approval/source/resource identity')
    require(result == {'status': 'submitted', 'profile': PROFILE, 'run_id': RUN_ID, 'stage': 'evaluate', 'job_id': job,
        'reserved_gpu_seconds': 3600, 'maximum_aggregate_gpu_seconds': 10800, 'maximum_concurrent_gpus': 1,
        'ledger': 'logs/hydra-retention-pilot-v1-evaluate.jsonl',
        'output': 'results/peano-hydra/evaluations/retention-pilot-v1',
        'automatic_retry': False, 'resume': False, 'refunds': False},
        'submission receipt does not identify the actual requested released evaluation job')
    return context


def launch_binding(job, expected_sha):
    require(type(job) is str and re.fullmatch(r'[1-9][0-9]{0,19}', job)
        and type(expected_sha) is str and re.fullmatch(r'[0-9a-f]{64}', expected_sha),
        'actual job ID and externally supplied launch receipt raw SHA required')
    raw = read_file(LAUNCH, 4 * 1024**2)
    require(hashlib.sha256(raw).hexdigest() == expected_sha, 'actual submitted evaluation receipt differs from external pin')
    require(hashlib.sha256(read_file(LAUNCHER, 65536)).hexdigest() == LAUNCHER_SHA,
            'original launch receipt producer source changed')
    context = validate_submit(decode(raw), job)
    value = {'path': str(LAUNCH), 'bytes': len(raw), 'sha256': expected_sha, 'context': context}
    require(len(canonical(value)) <= 4096, 'bounded exact launch descriptor required for final watcher index')
    return value


def write_new(path, value):
    require(path in (ARCHIVE / 'watch-evaluation-started-01.json', ARCHIVE / 'watch-evaluation-result-01.json'),
            'watcher may only write its own fixed one-use metadata records')
    raw = canonical(value) + b'\n'
    require(len(raw) <= 65536 and path.parent == path.parent.resolve(strict=True), 'bounded canonical watcher output required')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    require(read_file(path, 65536) == raw, 'watcher receipt changed during publication')


def observation_item(record, raw, output, job):
    require(record['schema'] == 'peano-hydra-retention-job-observation-receipt-v1'
        and record['status'] == 'observed-not-proof-verified' and record['returncode'] == 0 and record['error'] is None
        and record['job_id'] == job and record['stage'] == 'evaluate' and record['source_commit'] == COMMIT
        and record['approval_sha256'] == APPROVAL and record['source_header_sha256'] == HEADER
        and record['helper']['sha256'] == OBSERVER_SHA and record['read_only'] is True
        and record['automatic_retry'] is False and record['proofs_independently_verified'] is False
        and record['quality_claim'] is None, 'actual bounded observation changed its job or no-proof scope')
    actual = record['observation']; binding = actual['binding']
    require(actual['read_only'] is True and actual['scheduler_mutation_performed'] is False
        and actual['proofs_independently_verified'] is False and actual['quality_claim'] is None
        and actual['remote_file_writes'] is False and actual['model_loaded'] is False
        and binding['job_id'] == job and binding['stage'] == 'evaluate'
        and binding['approval_sha256'] == APPROVAL and binding['source_header_sha256'] == HEADER
        and binding['source_commit'] == COMMIT and binding['ledger_phase'] == 'released' and binding['ledger_events'] == 6
        and binding['reservation'] == {'seconds': 3600, 'gpus': 1, 'cpus': 8, 'memory_gib': 64},
        'observer did not join the actual released one-use evaluation ledger')
    progress, metadata = actual['progress'], actual['metadata']
    require(progress['expected_checkpoint_records'] == 256 and progress['checkpoint_rows_or_proofs_verified'] is False
        and progress['quality_claim'] is None, 'HEAD observation acquired a score or changed its prescribed count')
    count = progress['checkpoint_completed_records']
    head = metadata['checkpoint_head'].get('value')
    if count is not None:
        require(type(count) is int and 0 <= count <= 256 and type(head) is dict
            and head.get('schema') == 'peano-hydra-retention-evaluation-checkpoint-head-v1'
            and head.get('completed') == count and progress.get('checkpoint_head_self_digest_matches') is True
            and head['head_sha256'] == hashlib.sha256(canonical({k: v for k, v in head.items() if k != 'head_sha256'})).hexdigest(),
            'operational committed count is not the actual observed self-consistent HEAD')
    row = actual['scheduler']['sacct']['bound_row']
    state = actual['scheduler']['observed_state']
    require(state is None or type(state) is str and len(state) <= 64
        and re.fullmatch(r'[A-Z_+]+(?: by [0-9]+)?', state), 'unknown scheduler state format')
    require(type(actual['observed_at_utc']) is str
        and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', actual['observed_at_utc']),
        'original observer UTC timestamp required')
    elapsed = None if row is None else int(row[4])
    require(elapsed is None or 0 <= elapsed <= 604800, 'invalid observed allocation clock')
    return {'job_id': job, 'observation_file': output.name, 'observation_sha256': hashlib.sha256(raw).hexdigest(),
        'state': state, 'observed_at_utc': actual['observed_at_utc'], 'elapsed_seconds': elapsed,
        'checkpoint_committed_records': count, 'expected_checkpoint_records': 256,
        'head_counter_only_not_verified_rows': True, 'proofs_verified': False, 'quality_claim': None}


def observation_index(observations):
    """Bound the final receipt; every complete original observation stays saved."""
    require(type(observations) is list and len(observations) <= MAX_OBSERVATIONS, 'watcher observation count bound')
    return [{key: item[key] for key in ('observation_file', 'observation_sha256', 'state',
        'observed_at_utc', 'elapsed_seconds', 'checkpoint_committed_records')} for item in observations]


def publish_view(item):
    count = item['checkpoint_committed_records']
    progress = ('No valid checkpoint HEAD counter is present in this observation.' if count is None else
        f"Checkpoint HEAD reports **{count} / 256** committed records ({count / 256:.1%}).")
    body = f'''# Hydra live evaluation status

Job **{item['job_id']}**: **{item['state'] or 'UNAVAILABLE'}**, observed {item['observed_at_utc']}.

{progress}

This is an observed progress counter. Checkpoint rows and proofs have not been
independently verified by this watcher; no model score is inferred.

Elapsed allocation time: {item['elapsed_seconds']} seconds. Limit: 3,600 seconds;
one GH200, eight CPUs and 64 GiB. No automatic retry or resume.

Source: [{item['observation_file']}]({item['observation_file']})
(raw SHA `{item['observation_sha256']}`). This convenience view comes from
retained read-only observations and may become stale. It performs no remote action.

Model quality remains pending complete matched comparison and independent
proof replay. A terminal scheduler state or a 256-record HEAD counter alone
does not establish a successful, authenticated evaluation.

See [continuation instructions](CONTINUE.md) for exact source, approval and
control identities. Do not rerun an already consumed evaluation action.
'''
    require(len(body.encode()) <= 16384, 'bounded evaluation convenience view required')
    fd, name = tempfile.mkstemp(prefix='.evaluation-live-status-', suffix='.tmp', dir=ARCHIVE)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        if os.path.lexists(LIVE):
            info = LIVE.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not LIVE.is_symlink(), 'unsafe evaluation view target')
        os.replace(name, LIVE)
    finally:
        if os.path.lexists(name): os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--expected-launch-sha256', required=True)
    parser.add_argument('--expected-helper-sha256', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
        and Path(__file__).absolute() == HELPER and ARCHIVE == ARCHIVE.resolve(strict=True),
        'exact isolated local watcher required')
    require(not os.path.lexists(LIVE), 'evaluation watcher view already exists; training view is never reused')
    require(re.fullmatch(r'[0-9a-f]{64}', args.expected_helper_sha256)
        and hashlib.sha256(read_file(HELPER, 65536)).hexdigest() == args.expected_helper_sha256
        and hashlib.sha256(read_file(BASE, 65536)).hexdigest() == BASE_SHA
        and hashlib.sha256(read_file(OBSERVER, 65536)).hexdigest() == OBSERVER_SHA, 'reviewed watcher/observer source changed')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def stopped(*_): raise TimeoutError('read-only evaluation watcher deadline')
    signal.signal(signal.SIGALRM, stopped)
    signal.setitimer(signal.ITIMER_REAL, max(.001, MAX_WALL - (time.monotonic() - STARTED)))
    launched = launch_binding(args.job_id, args.expected_launch_sha256)
    require(not os.path.lexists(ARCHIVE / 'watch-evaluation-result-01.json'), 'evaluation watcher result already exists')
    write_new(ARCHIVE / 'watch-evaluation-started-01.json', {
        'schema': SCHEMA, 'job_id': args.job_id, 'stage': 'evaluate', 'launch': launched,
        'helper_sha256': args.expected_helper_sha256, 'training_watcher_source_sha256': BASE_SHA,
        'observer_sha256': OBSERVER_SHA, 'approval_sha256': APPROVAL, 'source_header_sha256': HEADER,
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'maximum_wall_seconds': MAX_WALL, 'maximum_observations': MAX_OBSERVATIONS, 'interval_seconds': INTERVAL,
        'observation_slots': {'first': 3, 'last': 127}, 'parent_cpu_seconds': 60,
        'observer_process_timeout_seconds': 65, 'observer_stdout_and_stderr_bytes_each': 65536,
        'scheduler_mutation_allowed': False, 'automatic_observation_retry': False,
        'proofs_verified': False, 'quality_claim': None})
    observations, error, child = [], None, None
    try:
        for number in range(3, 128):
            require(launch_binding(args.job_id, args.expected_launch_sha256) == launched
                and hashlib.sha256(read_file(HELPER, 65536)).hexdigest() == args.expected_helper_sha256
                and hashlib.sha256(read_file(OBSERVER, 65536)).hexdigest() == OBSERVER_SHA,
                'actual launch or reviewed observer/caller changed')
            # Leave enough room for the observer's existing60-second guard and
            # its unchanged cleanup. No observation is started at the deadline.
            require(time.monotonic() - STARTED < MAX_WALL - 70, 'no bounded observation time remains')
            output = ARCHIVE / f'retention-evaluate-observation-{number:02d}.json'
            mark = output.with_name(output.stem + '.started.json')
            require(not os.path.lexists(output) and not os.path.lexists(mark), 'observation slot already used; no overwrite or retry')
            command = [sys.executable, '-I', '-B', str(OBSERVER), '--job-id', args.job_id, '--stage', 'evaluate',
                '--approval-sha256', APPROVAL, '--source-header-sha256', HEADER, '--output', str(output)]
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            stdout, stderr = child.communicate(timeout=65)
            require(child.returncode == 0 and len(stdout) < 65536 and len(stderr) < 65536,
                'observer failed; evaluation watcher stops without retry')
            raw = read_file(output, 8 * 1024**2)
            item = observation_item(decode(raw), raw, output, args.job_id)
            require(launch_binding(args.job_id, args.expected_launch_sha256) == launched,
                'actual submission identity changed during observation')
            observations.append(item); publish_view(item)
            print(json.dumps(item, sort_keys=True), flush=True)
            child = None
            if item['state'] not in STILL_ACTIVE: break
            due = time.monotonic() + INTERVAL
            while time.monotonic() < due:
                time.sleep(min(20, due - time.monotonic()))
    except BaseException as failure:
        error = (type(failure).__name__ + ': ' + ' '.join(str(failure).split()))[:2048]
    finally:
        if child is not None and child.poll() is None:
            # SIGINT lets the pinned observer execute its existing SSH cleanup;
            # fallback only targets this watcher's own child process group.
            try:
                os.killpg(child.pid, signal.SIGINT); child.wait(timeout=4)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=1)
        write_new(ARCHIVE / 'watch-evaluation-result-01.json', {
            'schema': SCHEMA, 'job_id': args.job_id, 'stage': 'evaluate', 'launch': launched,
            'helper_sha256': args.expected_helper_sha256, 'observer_sha256': OBSERVER_SHA,
            'status': 'finished-observing' if error is None else 'stopped-without-observation-retry',
            'error': error, 'observations': observation_index(observations), 'wall_seconds': time.monotonic() - STARTED,
            'maximum_wall_seconds': MAX_WALL, 'maximum_observations': MAX_OBSERVATIONS,
            'observations_are_compact_index_of_unchanged_original_files': True,
            'expected_checkpoint_records': 256, 'head_counter_only_not_verified_rows': True,
            'scheduler_mutation_performed': False, 'model_loaded': False, 'proofs_verified': False,
            'quality_claim': None, 'automatic_observation_retry': False, 'resume': False})
        signal.setitimer(signal.ITIMER_REAL, 0)
    if error: print(error, file=sys.stderr, flush=True)
    return 0 if error is None else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, TimeoutError) as error:
        print('retention-evaluation-watch: ' + ' '.join(str(error).split())[:2048], file=sys.stderr, flush=True)
        raise SystemExit(2)
