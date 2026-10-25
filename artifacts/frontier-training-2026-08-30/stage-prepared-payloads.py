"""Copy retained preparation bytes into fresh staging; do not call them verified.

The original CPU-limit failure and its directory remain untouched. Successful
independent preflight and token receipts are still required before any launch.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

BASE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = Path(__file__).absolute().parent
SOURCE_ROOT = BASE / '_deploy/hydra-frontier-execution-20260830'
DEST_ROOT = BASE / '_deploy/hydra-frontier-recovery-work-20260830'
RELATIVE = Path('_deploy/hydra-frontier-training-v1/admitted')
NAMES = tuple(sorted([
    'candidate-readiness.json', 'lineage-proposal.json', 'lineage-review.json',
    'native-summary.json', 'training-admission.json',
    *('source/' + name for name in ('discovery.jsonl', 'epoch.json', 'manifest.json', 'preferences.jsonl', 'sft.jsonl')),
    *('preparation/' + name for name in ('config.toml', 'dev.jsonl', 'discovery.jsonl', 'manifest.json', 'preferences.jsonl', 'quarantine.jsonl', 'train.jsonl')),
]))


def tree(root):
    found = {}
    for parent, directories, files in os.walk(root, followlinks=False):
        assert all(not (Path(parent) / name).is_symlink() for name in directories)
        for name in files:
            path = Path(parent) / name
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 64 * 1024**2
            found[path.relative_to(root).as_posix()] = {'bytes': info.st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    assert set(found) == set(NAMES) and sum(row['bytes'] for row in found.values()) <= 128 * 1024**2
    return found


def main():
    output = ARCHIVE / 'prepared-payload-staging-01.json'
    source, target = SOURCE_ROOT / RELATIVE, DEST_ROOT / RELATIVE
    assert not target.parent.exists() and not target.parent.is_symlink() and not output.exists()
    failure = json.loads((ARCHIVE / 'admission-invocation-01.json').read_bytes())
    assert failure['error'] and failure['result'] is None and failure['gpu_jobs_started'] == 0
    expected = tree(source)
    target.mkdir(parents=True, mode=0o700)
    for name in NAMES:
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (source / name).read_bytes()
        assert {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} == expected[name]
        with path.open('xb') as stream:
            stream.write(raw)
    assert tree(source) == tree(target) == expected
    record = {'schema': 'peano-hydra-retained-preparation-staging-v1',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'source': str(source), 'destination': str(target),
        'files': expected, 'file_count': len(expected), 'total_bytes': sum(row['bytes'] for row in expected.values()),
        'source_unchanged': True, 'exact_fresh_copy': True, 'original_admission_worker_succeeded': False,
        'independent_final_verification_required': True, 'production_token_preflight_required': True,
        'training_started': False, 'gpu_jobs_started': 0}
    with output.open('xb') as stream:
        stream.write((json.dumps(record, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({key: value for key, value in record.items() if key != 'files'}, sort_keys=True))


if __name__ == '__main__':
    main()
