"""Copy the fully verified staging package into the fresh frozen execution root."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

BASE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = Path(__file__).absolute().parent
WORK = BASE / '_deploy/hydra-frontier-recovery-work-20260830'
ROOT = BASE / '_deploy/hydra-frontier-training-execution-20260830'
COMMIT = 'b08a6b1303d73217f6cc23800ae15e50b17db792'
PACKAGE = '_deploy/hydra-frontier-training-v1'
sys.path[:0] = [str(ROOT), str(ROOT / 'peano-lab/py')]
from training.peano_hydra import origin_bridge as bridge, scaling_freeze as freezer
from training.peano_hydra import scaling_admission, scaling_experiment


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def files(root):
    names = set()
    for parent, directories, leaves in os.walk(root, followlinks=False):
        assert all(not (Path(parent) / name).is_symlink() for name in directories)
        for leaf in leaves:
            path = Path(parent) / leaf
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 64 * 1024**2
            names.add(path.relative_to(root).as_posix())
    assert 1 <= len(names) <= 512
    return names


def main():
    output = ARCHIVE / 'final-package-assembly-01.json'
    assert not (ROOT / PACKAGE).exists() and not output.exists()
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, env=env, text=True).strip()
    assert git('rev-parse', 'HEAD') == COMMIT and git('status', '--porcelain=v1', '--untracked-files=all') == ''
    required = {'admitted/preflight.json': '6206e26abdef81502eb54693f9601f44bbf459b4d8419d8fb22eed71e36d61b2',
        'token-preflight.json': '5e429426d1899f2a898b7e5affc1a3ee141224ddac286a9bacd1c40afe38f365',
        'training-inputs.json': '9d15bfe21749821b1939b3f0bc07be117f83dce90a70b0f7f98525a52a2673eb',
        'authorization/user-instruction.json': '7158689e94fd42e60710b15a134ec8a2a2f446da993ef0b52e9cd815138ed164'}
    names = files(WORK / PACKAGE)
    assert set(required) <= names and not {'resource-request.json', 'approval.json'} & names
    with bridge._Tree(WORK) as source, bridge._Tree(ROOT) as destination:
        inventory = {}
        for name in sorted(names):
            relative = PACKAGE + '/' + name
            desc, raw = source.fingerprint(relative, maximum=64 * 1024**2, retain=True)
            inventory[relative] = {key: desc[key] for key in ('bytes', 'sha256')}
            if name in required:
                assert desc['sha256'] == required[name]
            assert sum(row['bytes'] for row in inventory.values()) <= 256 * 1024**2
            freezer._new_file(destination, relative, raw, 0o600)
        for name, expected in inventory.items():
            for tree in (source, destination):
                desc, _ = tree.fingerprint(name, maximum=64 * 1024**2)
                assert {key: desc[key] for key in ('bytes', 'sha256')} == expected
        source.assert_unchanged()
        destination.assert_unchanged()
    assert files(WORK / PACKAGE) == files(ROOT / PACKAGE) == names
    ready = json.loads((ROOT / PACKAGE / 'admitted/candidate-readiness.json').read_bytes())
    assert ready['source_files'] == scaling_experiment.execution_source_inventory()
    token = json.loads((ROOT / PACKAGE / 'token-preflight.json').read_bytes())
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected for name, expected in token['execution_source_files'].items())
    identity = scaling_admission.admission_identity(ROOT / PACKAGE / 'admitted/source')
    assert identity == token['admission'] and identity['review_sha256'] == '24a3813bec310ee498cec5223c6611590c380b5ae9e8f186548b1ed4910dece7'
    assert git('status', '--porcelain=v1', '--untracked-files=all') == ''
    record = {'schema': 'peano-hydra-final-training-package-assembly-v1', 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_root': str(WORK), 'execution_root': str(ROOT), 'execution_commit': COMMIT,
        'package': PACKAGE, 'files': inventory, 'file_count': len(inventory),
        'total_bytes': sum(row['bytes'] for row in inventory.values()),
        'files_sha256': hashlib.sha256(canonical(inventory)).hexdigest(),
        'candidate_execution_files_match': True, 'token_execution_files_match': True,
        'admission_identity_unchanged': True, 'frozen_source_still_clean': True,
        'native_replay_repeated_by_copy': False, 'gpu_jobs_started': 0}
    with output.open('xb') as stream:
        stream.write((json.dumps(record, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({key: value for key, value in record.items() if key != 'files'}, sort_keys=True))


if __name__ == '__main__':
    main()
