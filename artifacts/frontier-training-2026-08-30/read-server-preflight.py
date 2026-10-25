"""One bounded, read-only Helios observation for the newly authorized training.

No transfer, allocation, package installation, cache write or model import.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ARCHIVE = Path(__file__).absolute().parent
OUTPUT = ARCHIVE / "server-preflight-01.json"
REMOTE = r'''set -euo pipefail
exec /usr/bin/python3 -I -B - <<'PY'
import datetime, json, os, pathlib, stat, subprocess
root = pathlib.Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training')
paths = {
 'new_experiment': root / 'experiments/frontier-training-v1',
 'runtime': root / '.venv-helios',
 'python': root / '.venv-helios/bin/python',
 'cache': root / '.cache/huggingface',
 'base_snapshot': root / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1',
 'trainer_lock': root / 'results/peano-hydra/.alpha-posttrain.lock',
 'evaluator_lock': root / 'results/peano-hydra/.authority-scale-evaluate.lock',
}
records = {}
for name, path in paths.items():
 record = {'path': str(path), 'exists': os.path.lexists(str(path))}
 if record['exists']:
  info = os.lstat(str(path))
  record.update(bytes=info.st_size, symlink=stat.S_ISLNK(info.st_mode), directory=stat.S_ISDIR(info.st_mode), regular=stat.S_ISREG(info.st_mode), executable=os.access(str(path), os.X_OK))
  if name == 'base_snapshot' and record['directory']:
   names = sorted(os.listdir(str(path)))
   assert len(names) <= 64
   record['files'] = [{'name': x, 'readable': os.access(str(path / x), os.R_OK), 'bytes': os.stat(str(path / x)).st_size} for x in names]
 records[name] = record
commands = {
 'queue': ['squeue', '--noheader', '--user=plgnasqret', '--format=%i|%j|%T|%P|%M|%l|%R'],
 'filesystem': ['df', '-Pk', str(root)],
 'partition': ['scontrol', 'show', 'partition', 'plgrid-gpu-gh200', '-o'],
}
observations = {}
for name, command in commands.items():
 result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=15)
 assert len(result.stdout.encode()) <= 65536 and len(result.stderr.encode()) <= 16384
 observations[name] = {'command': command, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
print(json.dumps({'schema': 'peano-hydra-training-server-preflight-v1', 'observed_at_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'paths': records, 'observations': observations, 'read_only': True, 'model_imported': False, 'gpu_jobs_started': 0}, sort_keys=True))
PY
'''


def main():
    if os.path.lexists(OUTPUT):
        raise SystemExit("fresh receipt required")
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
               "-o", "ServerAliveCountMax=2", "--", "plgnasqret@helios.cyfronet.pl", "bash -l -s"]
    started = time.time()
    try:
        result = subprocess.run(command, input=REMOTE.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        code, out, err, timeout = result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired as error:
        code, out, err, timeout = None, error.stdout or b"", error.stderr or b"", True
    assert len(out) <= 131072 and len(err) <= 65536
    record = {"command": command, "remote_program_sha256": hashlib.sha256(REMOTE.encode()).hexdigest(),
              "started_unix": started, "wall_seconds": time.time() - started, "returncode": code,
              "timed_out": timeout, "stdout": out.decode(), "stderr": err.decode(), "automatic_retry": False}
    with OUTPUT.open("xb") as stream:
        stream.write((json.dumps(record, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps(record, sort_keys=True))
    raise SystemExit(0 if code == 0 else 2)


if __name__ == "__main__":
    main()
