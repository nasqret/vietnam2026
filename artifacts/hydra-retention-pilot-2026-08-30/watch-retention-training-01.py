"""Observe one already submitted job; never submit, retry, resume, or cancel it.

Each observation invokes the unchanged bounded read-only observer once and
retains a new receipt. A failed observation stops this watcher. LIVE_STATUS.md
is only a mutable convenience view; the underlying observations stay immutable.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
OBSERVER = ARCHIVE / 'observe-retention-job-01.py'
OBSERVER_SHA = 'b6571e17bc906ee698e62d4dace2c9d44b7390c59d8b637720ad6eddb33ee0c7'
JOB = '21456251'
APPROVAL = '556cef2186a2003bf90ea327b927cc6cb3ea6ec0bd57f65e421bb6841e74d233'
HEADER = '224ad02b154eb32a64e07cfd02710f81020cb4b108c83d6514b2dcf918802333'
STILL_ACTIVE = {'PENDING', 'RUNNING', 'CONFIGURING', 'COMPLETING', 'SUSPENDED'}
LIVE = ARCHIVE / 'LIVE_STATUS.md'


def write_new(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    assert len(raw) <= 65536
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def publish_view(item):
    step = item['optimizer_step']
    progress = 'No optimizer event is present in the latest bounded tail.' if step is None else f"Optimizer updates: **{step:,} / 1,469** ({step / 1469:.1%})."
    body = f'''# Hydra live training status

Job **{JOB}**: **{item['state']}**, observed {item['observed_at_utc']}.

{progress}

Elapsed allocation time: {item['elapsed_seconds']} seconds. Limit: 7,200 seconds;
one GH200, eight CPUs and 64 GiB. No automatic retry or resume.

Source: [{item['observation_file']}]({item['observation_file']})
(raw SHA `{item['observation_sha256']}`). This view is derived from retained
read-only observations and may become stale; it performs no remote action.

Model quality is pending the matched evaluation and independent proof replay.
Training loss alone does not establish proof success. A terminal job state
alone does not establish a completed, authenticated model artifact.

See [continuation instructions](CONTINUE.md) for exact source, approval and
control identities. Do not rerun any already consumed training action.
'''
    fd, name = tempfile.mkstemp(prefix='.live-status-', suffix='.tmp', dir=ARCHIVE)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        assert not LIVE.is_symlink()
        os.replace(name, LIVE)
    finally:
        if os.path.lexists(name): os.unlink(name)


def main():
    assert sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
    assert not LIVE.exists() and not LIVE.is_symlink(), 'watcher view already exists'
    assert hashlib.sha256(OBSERVER.read_bytes()).hexdigest() == OBSERVER_SHA
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    started = time.monotonic()
    def stopped(*_): raise TimeoutError('read-only training watcher deadline')
    signal.signal(signal.SIGALRM, stopped); signal.alarm(7500)
    write_new(ARCHIVE / 'watch-training-started-01.json', {
        'schema': 'peano-hydra-retention-read-only-training-watch-v1', 'job_id': JOB,
        'observer_sha256': OBSERVER_SHA, 'approval_sha256': APPROVAL, 'source_header_sha256': HEADER,
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'maximum_wall_seconds': 7500, 'maximum_observations': 125, 'interval_seconds': 60,
        'scheduler_mutation_allowed': False, 'automatic_observation_retry': False})
    observations, error, child = [], None, None
    try:
        for number in range(3, 128):
            assert hashlib.sha256(OBSERVER.read_bytes()).hexdigest() == OBSERVER_SHA
            output = ARCHIVE / f'retention-train-observation-{number:02d}.json'
            assert not output.exists(), 'observation slot already used; no overwrite'
            command = [sys.executable, '-I', '-B', str(OBSERVER), '--job-id', JOB, '--stage', 'train',
                '--approval-sha256', APPROVAL, '--source-header-sha256', HEADER, '--output', str(output)]
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            stdout, stderr = child.communicate(timeout=65)
            assert child.returncode == 0 and len(stdout) < 65536 and len(stderr) < 65536, 'observer failed; watcher stops without retry'
            raw = output.read_bytes(); assert len(raw) < 8 * 1024**2
            record = json.loads(raw)
            assert record['status'] == 'observed-not-proof-verified' and record['returncode'] == 0 and record['error'] is None
            assert record['job_id'] == JOB and record['approval_sha256'] == APPROVAL and record['source_header_sha256'] == HEADER
            actual = record['observation']
            assert actual['read_only'] is True and actual['scheduler_mutation_performed'] is False
            row = actual['scheduler']['sacct']['bound_row']
            item = {'observation_file': output.name, 'observation_sha256': hashlib.sha256(raw).hexdigest(),
                'state': actual['scheduler']['observed_state'], 'observed_at_utc': actual['observed_at_utc'],
                'elapsed_seconds': int(row[4]) if row is not None else None,
                'optimizer_step': actual['progress']['latest_optimizer_step_in_tail']}
            observations.append(item); publish_view(item)
            print(json.dumps(item, sort_keys=True), flush=True)
            child = None
            if item['state'] not in STILL_ACTIVE: break
            due = time.monotonic() + 60
            while time.monotonic() < due:
                time.sleep(min(20, due - time.monotonic()))
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2048]
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=5)
        write_new(ARCHIVE / 'watch-training-result-01.json', {
            'schema': 'peano-hydra-retention-read-only-training-watch-v1', 'job_id': JOB,
            'status': 'finished-observing' if error is None else 'stopped-without-observation-retry',
            'error': error, 'observations': observations, 'wall_seconds': time.monotonic() - started,
            'scheduler_mutation_performed': False, 'model_loaded': False, 'proofs_verified': False})
        signal.alarm(0)
    if error: print(error, file=sys.stderr, flush=True)
    return 0 if error is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
