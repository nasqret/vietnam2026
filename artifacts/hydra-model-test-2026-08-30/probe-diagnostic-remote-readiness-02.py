"""One bounded read-only login-node probe; compatible with installed Python3.9."""
import datetime
import hashlib
import json
import os
import pathlib
import resource
import signal
import stat
import subprocess
import time

resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(35)
started = time.monotonic()
parent = pathlib.Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training')
destination = parent / 'experiments/frontier-diagnostic-v1'
checks = {}
models = {
    'saved-corrected': (
        '_deploy/hydra-search-v2/model/manifest.json',
        '172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c'),
    'new-frontier': (
        'experiments/frontier-training-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1/manifest.json',
        '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'),
}
for role, (rel, expected) in models.items():
    path = parent / rel
    before = os.stat(path, follow_symlinks=False)
    assert stat.S_ISREG(before.st_mode) and before.st_size <= 4 * 1024**2
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        raw = stream.read(4 * 1024**2 + 1)
    after = os.stat(path, follow_symlinks=False)
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == expected
    checks[role] = {'path': str(path), 'bytes': len(raw), 'sha256': digest, 'matches': True}
try:
    queue = subprocess.run(
        ['squeue', '--noheader', '--user=plgnasqret', '--format=%i|%j|%T|%M|%l|%R'],
        capture_output=True, text=True, timeout=10)
    assert len(queue.stdout.encode()) + len(queue.stderr.encode()) <= 65536
    queue_record = {'returncode': queue.returncode, 'stdout': queue.stdout, 'stderr': queue.stderr}
except OSError as exc:
    queue_record = {'error': type(exc).__name__ + ': ' + str(exc)}
space = os.statvfs(parent)
usage = resource.getrusage(resource.RUSAGE_SELF)
result = {
    'schema': 'peano-hydra-diagnostic-remote-readiness-v1',
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'destination': str(destination), 'destination_exists': os.path.lexists(destination),
    'existing_model_manifests': checks,
    'source_roots_present': {
        'saved-corrected': (parent / '_deploy/hydra-search-v2/origin-source').is_dir(),
        'new-frontier': (parent / 'experiments/frontier-training-v1').is_dir(),
    },
    'venv_python_present': (parent / '.venv-helios/bin/python').exists(),
    'base_snapshot_present': (parent / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1').is_dir(),
    'available_bytes': space.f_bavail * space.f_frsize, 'queue': queue_record,
    'model_weights_read': False, 'native_or_model_work_performed': False,
    'files_written': False, 'gpu_job_submitted': False,
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime,
                  'wall_seconds': time.monotonic() - started, 'maxrss_kib': usage.ru_maxrss},
}
print(json.dumps(result, sort_keys=True))
