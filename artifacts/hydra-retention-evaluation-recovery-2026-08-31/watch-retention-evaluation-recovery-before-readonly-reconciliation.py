"""Observe one actually released retention evaluation; never launch or retry it.

Adapted from the reviewed original evaluation watcher. Each slot invokes the pinned
bounded recovery observer once. Failed/uncertain observations stop this
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

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31')
HELPER = ARCHIVE / 'watch-retention-evaluation-recovery-01.py'
BASE = ARCHIVE.parent / 'hydra-retention-pilot-2026-08-30/watch-retention-evaluation-01.py'
BASE_SHA = 'ba2b11fc89bb1b5833bd913f313e98d7940fb81820fdada01f5f19b46e71ae9d'
OBSERVER = ARCHIVE / 'observe-retention-evaluation-recovery-01.py'
OBSERVER_SHA = 'c870482f303d9c9828e1be20daada191d30a1a63430b1b39196d6ff24b003308'
LAUNCHER = ARCHIVE / 'invoke-retention-evaluation-recovery-01.py'
LAUNCHER_SHA = 'f4a8592b3c31ec1be1b4c7af182d2902a1267179b635ea6638a72e959f8df09a'
LAUNCH = ARCHIVE / 'launch-evaluate-submit-01.json'
PRODUCER_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
PROFILE, RUN_ID = 'peano-hydra-retention-evaluation-recovery-v1', 'retention-evaluation-recovery-v1'
STILL_ACTIVE = {'PENDING', 'RUNNING', 'CONFIGURING', 'COMPLETING', 'SUSPENDED'}
LIVE = ARCHIVE / 'EVALUATION_LIVE_STATUS.md'
SCHEMA = 'peano-hydra-retention-evaluation-recovery-read-only-watch-v1'
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
    """Read the actual new invocation; the pinned gate owns the release."""
    require(record.get('schema') == 'peano-hydra-retention-evaluation-recovery-launch-invocation-v1'
        and record.get('status') == 'passed' and record.get('mode') == 'submit' and record.get('stage') == 'evaluate'
        and record.get('helper_sha256') == LAUNCHER_SHA and record.get('remote_command_started') is True
        and record.get('automatic_retry') is False and record.get('frozen_source_modified') is False,
        'actual successful new evaluation submission required; no draft, training, test-only or uncertain submit')
    source = read_file(LAUNCHER, 65536)
    require(hashlib.sha256(source).hexdigest() == LAUNCHER_SHA, 'reviewed launch receipt producer changed')
    module = {'__name__': 'read_only_recovery_launch_validation', '__file__': str(LAUNCHER)}
    exec(compile(source, str(LAUNCHER), 'exec'), module)
    process, context, result = record['process'], record['context'], record['result']
    require(process['returncode'] == 0 and process['reason'] == 'exited' and process['error'] is None
        and decode(process['stdout'].encode()) == result, 'submission result differs from actual successful new gate stdout')
    identity = context['identity']
    require(type(identity['source_commit']) is str and re.fullmatch(r'[0-9a-f]{40}', identity['source_commit'])
        and identity['source_commit'] != PRODUCER_COMMIT
        and all(type(identity[key]) is str and re.fullmatch(r'[0-9a-f]{64}', identity[key]) for key in
            ('approval_sha256', 'resource_request_sha256', 'source_files_sha256', 'payloads_sha256', 'producer_sha256', 'historical_admission_sha256'))
        and context['source_header_sha256'] == hashlib.sha256(canonical(identity)).hexdigest()
        and context['reservations'] == module['RESERVATIONS'] and context['producer'] == module['PRODUCER']
        and context['model_manifest'] == module['MODEL_MANIFEST']
        and identity['producer_sha256'] == hashlib.sha256(canonical(context['producer'])).hexdigest(),
        'submitted evaluation changed actual source/approval or preserved producer identity')
    module['validate_result'](result, 'submit', 'evaluate')
    require(result['job_id'] == job, 'submission receipt names another new evaluation job')
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


def observation_item(record, raw, output, job, context):
    identity = context['identity']
    commit, approval, header = identity['source_commit'], identity['approval_sha256'], context['source_header_sha256']
    require(record['schema'] == 'peano-hydra-retention-evaluation-recovery-observation-receipt-v1'
        and record['status'] == 'observed-not-proof-verified' and record['returncode'] == 0 and record['error'] is None
        and record['job_id'] == job and record['stage'] == 'evaluate' and record['source_commit'] == commit
        and record['approval_sha256'] == approval and record['source_header_sha256'] == header
        and record['helper']['sha256'] == OBSERVER_SHA and record['read_only'] is True
        and record['automatic_retry'] is False and record['proofs_independently_verified'] is False
        and record['quality_claim'] is None, 'actual bounded observation changed its job or no-proof scope')
    actual = record['observation']; binding = actual['binding']
    require(actual['read_only'] is True and actual['scheduler_mutation_performed'] is False
        and actual['proofs_independently_verified'] is False and actual['quality_claim'] is None
        and actual['remote_file_writes'] is False and actual['model_loaded'] is False
        and binding['job_id'] == job and binding['stage'] == 'evaluate'
        and binding['approval_sha256'] == approval and binding['source_header_sha256'] == header
        and binding['source_commit'] == commit and binding['ledger_phase'] == 'released' and binding['ledger_events'] == 6
        and binding['reservation'] == {'seconds': 3600, 'gpus': 1, 'cpus': 8, 'memory_gib': 64}
        and binding['producer'] == context['producer'] and binding['reserved_model_manifest'] == context['model_manifest']
        and all(binding.get(key) == value for key, value in identity.items()),
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
    row = actual['scheduler']['sacct'].get('bound_row')
    require(row is None or type(row) is list and len(row) == 13 and row[0] == job,
        'one bounded actual accounting row required when available')
    exit_code = None if row is None else row[3]
    require(exit_code is None or type(exit_code) is str and re.fullmatch(r'[0-9]{1,3}:[0-9]{1,3}', exit_code)
        and all(int(value) <= 255 for value in exit_code.split(':')), 'bounded actual scheduler exit code required')
    state = actual['scheduler']['observed_state']
    require(state is None or type(state) is str and len(state) <= 64
        and re.fullmatch(r'[A-Z_+]+(?: by [0-9]+)?', state), 'unknown scheduler state format')
    require(type(actual['observed_at_utc']) is str
        and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', actual['observed_at_utc']),
        'original observer UTC timestamp required')
    elapsed = None if row is None else int(row[4])
    require(elapsed is None or 0 <= elapsed <= 604800, 'invalid observed allocation clock')
    return {'job_id': job, 'observation_file': output.name, 'observation_sha256': hashlib.sha256(raw).hexdigest(),
        'state': state, 'exit_code': exit_code, 'terminal': state is not None and state not in STILL_ACTIVE, 'observed_at_utc': actual['observed_at_utc'], 'elapsed_seconds': elapsed,
        'checkpoint_committed_records': count, 'expected_checkpoint_records': 256,
        'head_counter_only_not_verified_rows': True, 'proofs_verified': False, 'quality_claim': None}


def observation_index(observations):
    """Bound the final receipt; every complete original observation stays saved."""
    require(type(observations) is list and len(observations) <= MAX_OBSERVATIONS, 'watcher observation count bound')
    return [{key: item[key] for key in ('observation_file', 'observation_sha256', 'state',
        'observed_at_utc', 'elapsed_seconds', 'checkpoint_committed_records', 'exit_code', 'terminal')} for item in observations]


def publish_view(item):
    count = item['checkpoint_committed_records']
    progress = ('No valid checkpoint HEAD counter is present in this observation.' if count is None else
        f"Checkpoint HEAD reports **{count} / 256** committed records ({count / 256:.1%}).")
    quality = ('The scheduler reports a terminal failure; model quality remains unknown.'
        if item['terminal'] and item['state'] != 'COMPLETED' else
        'Model quality still requires collected matched results and independent proof replay.')
    body = f'''# Hydra live evaluation recovery status

Job **{item['job_id']}**: **{item['state'] or 'UNAVAILABLE'}**, observed {item['observed_at_utc']}.
Scheduler exit code: {item['exit_code'] or 'not yet available'}.

{progress}

This is an observed progress counter. Checkpoint rows and proofs have not been
independently verified by this watcher; no model score is inferred.

Elapsed allocation time: {item['elapsed_seconds']} seconds. Limit: 3,600 seconds;
one GH200, eight CPUs and 64 GiB. No automatic retry or resume.

Source: [{item['observation_file']}]({item['observation_file']})
(raw SHA `{item['observation_sha256']}`). This convenience view comes from
retained read-only observations and may become stale. This view performs no remote action.

{quality}
A terminal scheduler state or a 256-record HEAD counter alone
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
    require(not os.path.lexists(LIVE), 'evaluation watcher view already exists; original pilot views are never reused')
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
    context = launched['context']; identity = context['identity']
    approval, header, commit = identity['approval_sha256'], context['source_header_sha256'], identity['source_commit']
    require(not os.path.lexists(ARCHIVE / 'watch-evaluation-result-01.json'), 'evaluation watcher result already exists')
    write_new(ARCHIVE / 'watch-evaluation-started-01.json', {
        'schema': SCHEMA, 'job_id': args.job_id, 'stage': 'evaluate', 'launch': launched,
        'helper_sha256': args.expected_helper_sha256, 'original_evaluation_watcher_source_sha256': BASE_SHA,
        'observer_sha256': OBSERVER_SHA, 'approval_sha256': approval, 'source_header_sha256': header, 'source_commit': commit,
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
                '--approval-sha256', approval, '--source-header-sha256', header, '--source-commit', commit,
                '--expected-helper-sha256', OBSERVER_SHA, '--output', str(output)]
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            stdout, stderr = child.communicate(timeout=65)
            require(child.returncode == 0 and len(stdout) < 65536 and len(stderr) < 65536,
                'observer failed; evaluation watcher stops without retry')
            raw = read_file(output, 8 * 1024**2)
            item = observation_item(decode(raw), raw, output, args.job_id, context)
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
            'error': error, 'observations': observation_index(observations),
            'terminal_state': observations[-1]['state'] if observations and observations[-1]['terminal'] else None,
            'terminal_exit_code': observations[-1]['exit_code'] if observations and observations[-1]['terminal'] else None,
            'terminal_state_is_not_quality_evidence': True, 'wall_seconds': time.monotonic() - STARTED,
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
