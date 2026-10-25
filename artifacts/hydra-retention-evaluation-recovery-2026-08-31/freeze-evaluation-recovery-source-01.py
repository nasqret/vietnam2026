#!/usr/bin/env python3
"""Select reviewed source, then attest an actually committed recovery tree.

The two modes are separate operator invocations. Neither mode commits, uploads,
loads a model, executes project code, or submits a scheduler job. Original source,
inputs and collected model bytes are read only. Outputs are exclusive.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import time

BASE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = BASE / 'artifacts/hydra-retention-evaluation-recovery-2026-08-31'
OLD = BASE / '_deploy/hydra-retention-execution-20260830'
WORK = BASE / '_deploy/hydra-frontier-recovery-work-20260830'
NEW = BASE / '_deploy/hydra-retention-evaluation-recovery-execution-20260831'
MODEL = BASE / 'artifacts/hydra-retention-pilot-2026-08-30/trained-model-collected-01/model'
OLD_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
OLD_PACKAGE = '_deploy/hydra-retention-pilot-v1'
SELECTION = ARCHIVE / 'source-selection-01.json'
CATALOG = '_deploy/hydra-retention-evaluation-recovery-source.json'
FREEZE = '_deploy/hydra-retention-evaluation-recovery-execution-freeze.json'
NAMES = (
    'training/peano_hydra/retention_training.py',
    'training/peano_hydra/retention_evaluation.py',
    'training/peano_hydra/helios_runtime.py',
    'training/peano_hydra/retention_saved_artifact.py',
    'training/peano_hydra/retention_evaluation_recovery_launch.py',
    'scripts/authenticate_peano_hydra_retention_saved.py',
    'scripts/execute_peano_hydra_retention_evaluation_recovery.py',
    'scripts/run_peano_hydra_retention_evaluation_recovery.sh',
    'slurm/peano_hydra_retention_evaluation_recovery.sbatch',
    'peano-lab/py/tests/test_peano_hydra_retention_training.py',
    'peano-lab/py/tests/test_peano_hydra_retention_saved_artifact.py',
    'peano-lab/py/tests/test_peano_hydra_retention_evaluation_recovery_cli.py',
    'peano-lab/py/tests/test_peano_hydra_retention_evaluation_recovery_launch.py',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, maximum=64 * 1024**2):
    require(path.is_absolute() and path.resolve(strict=True) == path, 'canonical nonsymlink source path required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                'bounded single-link regular file required')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read(maximum + 1)
        after = os.fstat(fd)
        signature = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size, x.st_mtime_ns, x.st_ctime_ns, x.st_nlink)
        require(len(raw) == before.st_size and signature(before) == signature(after) == signature(path.stat()),
                'source changed during read')
        return raw
    finally:
        os.close(fd)


def pin(path, maximum=64 * 1024**2):
    raw = read(path, maximum)
    return {'bytes': len(raw), 'sha256': sha(raw)}


def publish(path, value):
    raw = canonical(value) + b'\n'
    require(len(raw) <= 2 * 1024**2 and path.parent.resolve(strict=True) == path.parent, 'receipt bound or path')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def git(root, *args):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('GIT_', 'PYTHON', 'LD_', 'DYLD_'))}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
        GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_OPTIONAL_LOCKS='0')
    result = subprocess.run(['/usr/bin/git', '-C', str(root), *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=10, check=False, env=environment)
    require(result.returncode == 0 and len(result.stdout) <= 2 * 1024**2 and len(result.stderr) <= 65536,
            'bounded Git read failed')
    return result.stdout


def clean(root, commit=None):
    actual = git(root, 'rev-parse', 'HEAD').decode().strip()
    require(len(actual) == 40 and (commit is None or actual == commit), 'unexpected actual Git commit')
    require(git(root, 'status', '--porcelain=v1', '--untracked-files=all') == b'', 'source tree is not clean')
    return actual


def tracked(root):
    records = git(root, 'ls-files', '--stage', '-z').split(b'\0')
    result = {}
    for line in records:
        if not line:
            continue
        metadata, raw_name = line.split(b'\t', 1)
        mode, blob, stage = metadata.decode().split()
        name = raw_name.decode()
        require(stage == '0' and mode in ('100644', '100755') and name not in result
                and not Path(name).is_absolute() and '..' not in Path(name).parts,
                'unmerged or nonregular source entry')
        raw = read(root / name)
        require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob,
                'working source differs from its genuine Git blob')
        require(stat.S_IMODE((root / name).stat().st_mode) == int(mode[-3:], 8), 'actual source mode differs from Git')
        result[name] = {'bytes': len(raw), 'sha256': sha(raw), 'mode': mode, 'git_blob': blob}
    require(1 <= len(result) <= 2000 and sum(x['bytes'] for x in result.values()) <= 256 * 1024**2,
            'source inventory exceeded declared freeze bounds')
    return dict(sorted(result.items()))


def preserved_data():
    request = json.loads(read(OLD / OLD_PACKAGE / 'resource-request.json'))
    require(pin(OLD / OLD_PACKAGE / 'resource-request.json')['sha256'] ==
            '67e0be409cf42ac90048029632479328e9b98b19c4f44f637f1fab6b5392f361', 'producer request changed')
    result = {}
    for name, expected in request['payloads'].items():
        actual = pin(OLD / name)
        require(actual == expected, 'preserved producer payload changed')
        result['producer/' + name] = actual
    for name in (OLD_PACKAGE + '/resource-request.json', OLD_PACKAGE + '/approval.json',
                 '_deploy/hydra-retention-origin-source.json', '_deploy/hydra-retention-execution-freeze.json'):
        result['producer/' + name] = pin(OLD / name)
    require(pin(MODEL / 'manifest.json') == {'bytes': 191597,
        'sha256': 'cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca'}, 'actual saved manifest changed')
    names = sorted(path.relative_to(MODEL).as_posix() for path in MODEL.rglob('*') if not path.is_dir())
    require(len(names) == 11, 'collected model inventory changed')
    for name in names:
        # Model bytes are only rehashed locally, never selected for transfer.
        # Keep the original model collector's distinct 128 MiB file bound.
        result['saved-model/' + name] = pin(MODEL / name, 128 * 1024**2)
    return result


def select(plan_path, expected_sha):
    plan_raw = read(plan_path, 65536)
    require(sha(plan_raw) == expected_sha, 'external reviewed selection pin changed')
    plan = json.loads(plan_raw)
    require(set(plan) == {'schema', 'files'} and plan['schema'] == 'peano-hydra-recovery-reviewed-source-selection-v1'
            and set(plan['files']) == set(NAMES), 'unexpected source selection')
    clean(OLD, OLD_COMMIT)
    clean(NEW, OLD_COMMIT)
    before_source = tracked(OLD)
    require(tracked(NEW) == before_source, 'new root is not the untouched original base')
    before_data = preserved_data()
    selected = {}
    for name in NAMES:
        raw = read(WORK / name, 2 * 1024**2)
        require(sha(raw) == plan['files'][name], 'reviewed work source changed')
        mode = stat.S_IMODE((WORK / name).stat().st_mode)
        require(mode in (0o644, 0o755), 'unexpected selected source mode')
        selected[name] = {'bytes': len(raw), 'sha256': sha(raw), 'mode': format(mode, '04o')}
    require(not SELECTION.exists(), 'source selection is one-use')
    for name in NAMES:
        path = NEW / name
        parent = NEW
        for part in Path(name).parts[:-1]:
            parent = parent / part
            if not parent.exists():
                parent.mkdir(mode=0o755)
            require(parent.is_dir() and parent.resolve(strict=True) == parent,
                    'selected source directory is not a canonical real directory')
        raw = read(WORK / name, 2 * 1024**2)
        require(sha(raw) == selected[name]['sha256'], 'selected source changed before copying')
        require(path.parent.resolve(strict=True) == path.parent, 'selected destination parent changed')
        if path.exists():
            require(name in before_source and sha(read(path)) == before_source[name]['sha256'],
                    'refusing to overwrite anything but the checked original source')
            fd = os.open(path, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
        else:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            os.fchmod(stream.fileno(), int(selected[name]['mode'], 8))
            stream.flush()
            os.fsync(stream.fileno())
    require({name: {**pin(NEW / name), 'mode': format(stat.S_IMODE((NEW / name).stat().st_mode), '04o')}
             for name in NAMES} == selected, 'selected destination bytes changed')
    require(tracked(OLD) == before_source and preserved_data() == before_data, 'preserved producer or model changed')
    clean(OLD, OLD_COMMIT)
    return publish(SELECTION, {'schema': 'peano-hydra-recovery-source-selection-result-v1',
        'status': 'copied-reviewed-source-not-yet-committed', 'producer_commit': OLD_COMMIT,
        'snapshot_root': str(NEW), 'selection_plan_sha256': expected_sha, 'files': selected,
        'preserved_source_files_sha256': sha(canonical(before_source)), 'preserved_data': before_data,
        'training_performed': False, 'gpu_allocated': False, 'network_work': False})


def freeze(expected_sha):
    raw = read(SELECTION, 2 * 1024**2)
    require(sha(raw) == expected_sha, 'external selection result pin changed')
    selection = json.loads(raw)
    require(selection['schema'] == 'peano-hydra-recovery-source-selection-result-v1'
            and set(selection['files']) == set(NAMES), 'wrong genuine selection result')
    clean(OLD, OLD_COMMIT)
    commit = clean(NEW)
    require(commit != OLD_COMMIT and git(NEW, 'rev-parse', 'HEAD^').decode().strip() == OLD_COMMIT,
            'recovery must be one actual new commit on preserved producer source')
    actual = tracked(NEW)
    delta = set(git(NEW, 'diff', '--name-only', OLD_COMMIT, 'HEAD').decode().splitlines())
    require(delta == set(NAMES) and set(NAMES) <= set(actual), 'commit changed a different source scope')
    for name, item in selection['files'].items():
        require({**pin(NEW / name), 'mode': format(stat.S_IMODE((NEW / name).stat().st_mode), '04o')} == item,
                'committed source differs from reviewed selection')
    preserved = tracked(OLD)
    require(sha(canonical(preserved)) == selection['preserved_source_files_sha256']
            and preserved_data() == selection['preserved_data'], 'original source, inputs or model changed')
    (NEW / '_deploy').mkdir(exist_ok=True)
    catalog = {'schema': 'peano-hydra-evaluation-recovery-source-bundle-v1', 'git_commit': commit,
        'producer_source_commit': OLD_COMMIT, 'files': actual, 'files_sha256': sha(canonical(actual)),
        'coverage': 'All actual tracked files of the separately committed evaluation recovery source.',
        'saved_model_retrained': False}
    catalog_pin = publish(NEW / CATALOG, catalog)
    require(tracked(NEW) == actual and tracked(OLD) == preserved
            and preserved_data() == selection['preserved_data'], 'source/data changed while freezing')
    clean(OLD, OLD_COMMIT)
    clean(NEW, commit)
    record = {'schema': 'peano-hydra-retention-evaluation-recovery-source-freeze-v1',
        'status': 'complete', 'snapshot_root': str(NEW), 'git_commit': commit,
        'snapshot_clean': True, 'all_selected_files_and_jobs_committed': True,
        'all_declared_ancillary_files_committed': True, 'source_bytes_unchanged': True,
        'data_bytes_unchanged': True, 'files': actual, 'files_sha256': sha(canonical(actual)),
        'file_count': len(actual), 'total_bytes': sum(item['bytes'] for item in actual.values()),
        'origin_source_manifest': {'path': CATALOG, **{k: catalog_pin[k] for k in ('bytes', 'sha256')}},
        'selection_result_sha256': expected_sha, 'producer_source_commit': OLD_COMMIT,
        'preserved_source_files_sha256': selection['preserved_source_files_sha256'],
        'preserved_data_sha256': sha(canonical(selection['preserved_data'])),
        'model_weights_loaded': False, 'training_performed': False, 'gpu_allocated': False,
        'network_work': False}
    return publish(NEW / FREEZE, record)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('mode', choices=('select', 'freeze'))
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    require((args.mode == 'select') == (args.plan is not None), 'mode and explicit plan differ')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('90-second freeze deadline')))
    signal.alarm(90)
    try:
        result = select(args.plan, args.expected_sha256) if args.mode == 'select' else freeze(args.expected_sha256)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        peak = usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
        require(peak <= 512 * 1024**2 and time.monotonic() - started < 90, 'freeze resource envelope exceeded')
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0
    except BaseException as error:
        print(type(error).__name__ + ': ' + str(error)[:2048], file=sys.stderr, flush=True)
        return 2
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
