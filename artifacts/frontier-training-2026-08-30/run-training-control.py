"""One explicit preparation/test/submission step with durable fresh receipts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-training-execution-20260830')
ARCHIVE = Path(__file__).absolute().parent
PACKAGE = ROOT / '_deploy/hydra-frontier-training-v1'
COMMIT = 'b08a6b1303d73217f6cc23800ae15e50b17db792'
REVIEW = '24a3813bec310ee498cec5223c6611590c380b5ae9e8f186548b1ed4910dece7'
INSTRUCTION = '7158689e94fd42e60710b15a134ec8a2a2f446da993ef0b52e9cd815138ed164'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--phase', choices=('ready-request', 'test-only', 'submit'), required=True)
    parser.add_argument('--approval-sha256')
    args = parser.parse_args()
    assert sha(ARCHIVE / 'user-instruction.json') == INSTRUCTION
    labels = {'ready-request': 'request-prepare-01', 'test-only': 'launch-test-only-01', 'submit': 'launch-submit-01'}
    label = labels[args.phase]
    paths = {key: ARCHIVE / (label + suffix) for key, suffix in
             (('started', '.started.json'), ('receipt', '.json'), ('stdout', '.stdout.log'), ('stderr', '.stderr.log'))}
    assert all(not path.exists() and not path.is_symlink() for path in paths.values()), 'fresh control invocation required; no automatic retries'
    if args.phase == 'ready-request':
        assert args.approval_sha256 is None and not (PACKAGE / 'resource-request.json').exists()
        command = [sys.executable, '-I', '-B', '-X', 'pycache_prefix=/dev/null',
            'scripts/prepare_peano_hydra_frontier_training_launch.py', '--ready-request', '--source-commit', COMMIT,
            '--review-sha256', REVIEW, '--output', str(PACKAGE / 'resource-request.json')]
    else:
        assert re.fullmatch('[0-9a-f]{64}', args.approval_sha256 or '')
        assert sha(PACKAGE / 'approval.json') == args.approval_sha256
        command = ['/bin/bash', 'scripts/helios_hydra_frontier_training.sh', '--approval-sha256', args.approval_sha256,
                   '--' + args.phase]
        if args.phase == 'submit':
            command += ['--confirm', 'PEANO-HYDRA-FRONTIER-TRAINING-7200-GPU-SECONDS']
    env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'PYTHON', 'SLURM_', 'SBATCH_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX='/dev/null', PYTHONNOUSERSITE='1')
    env['PATH'] = '/opt/homebrew/opt/python@3.11/libexec/bin:' + env.get('PATH', '/usr/bin:/bin')
    assert Path(shutil.which('python3', path=env['PATH'])).resolve() == Path(sys.executable).resolve()
    started = datetime.now(timezone.utc).isoformat()
    write(paths['started'], {'phase': args.phase, 'command': command, 'cwd': str(ROOT), 'started_at_utc': started,
        'source_commit': COMMIT, 'approval_sha256': args.approval_sha256, 'user_instruction_sha256': INSTRUCTION,
        'automatic_retry': False, 'maximum_gpu_seconds': 7200 if args.phase == 'submit' else 0})
    clock = time.monotonic()
    timeout = False
    with paths['stdout'].open('xb') as out, paths['stderr'].open('xb') as err:
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err, timeout=60)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code, timeout = None, True
    assert paths['stdout'].stat().st_size <= 1024**2 and paths['stderr'].stat().st_size <= 256 * 1024
    stdout, stderr = paths['stdout'].read_text(), paths['stderr'].read_text()
    record = {'schema': 'peano-hydra-frontier-training-control-invocation-v1', 'phase': args.phase,
        'command': command, 'cwd': str(ROOT), 'started_at_utc': started,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'wall_seconds': time.monotonic() - clock,
        'source_commit': COMMIT, 'approval_sha256': args.approval_sha256,
        'returncode': code, 'timed_out': timeout, 'automatic_retry': False, 'stdout': stdout, 'stderr': stderr,
        'logs': {key: {'path': str(paths[key]), 'bytes': paths[key].stat().st_size, 'sha256': sha(paths[key])} for key in ('stdout', 'stderr')}}
    write(paths['receipt'], record)
    last = stdout.strip().splitlines()[-1] if stdout.strip() else None
    print(json.dumps({'phase': args.phase, 'returncode': code, 'timed_out': timeout,
        'receipt': str(paths['receipt']), 'receipt_sha256': sha(paths['receipt']), 'last_stdout_line': last,
        'stderr': stderr, 'automatic_retry': False}, sort_keys=True), flush=True)
    raise SystemExit(0 if code == 0 and not timeout else 2)


if __name__ == '__main__':
    main()
