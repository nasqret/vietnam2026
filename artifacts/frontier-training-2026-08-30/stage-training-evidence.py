"""Stage only the byte-pinned exclusion and authorization evidence for training."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat

BASE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = Path(__file__).absolute().parent
OLD = BASE / 'artifacts/frontier-experiment-2026-08-30'
ROOT = BASE / '_deploy/hydra-frontier-recovery-work-20260830'
PACKAGE = ROOT / '_deploy/hydra-frontier-training-v1'
BENCHMARK = PACKAGE / 'benchmark-evidence'
BASELINE = BASE / '_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/model/manifest.json'


def read(path):
    info = path.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 16 * 1024**2
    assert not any(parent.is_symlink() for parent in path.parents)
    raw = path.read_bytes()
    assert len(raw) == info.st_size
    return raw


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def copy(source, destination, expected):
    raw = read(source)
    assert identity(raw) == expected, 'evidence bytes changed: ' + str(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
    assert read(source) == read(destination) == raw


def main():
    assert not BENCHMARK.exists() and not (PACKAGE / 'tokenizer-provenance').exists()
    output = ARCHIVE / 'training-evidence-staging-01.json'
    assert not output.exists()
    audit_name = 'benchmark-exposure-audit-01.json'
    audit_raw = read(OLD / audit_name)
    assert hashlib.sha256(audit_raw).hexdigest() == '914129cf15f70f308b2fcc42b23428debae0b87daa53cfe922667d131a04b51c'
    audit = json.loads(audit_raw)
    descriptors = {audit_name: identity(audit_raw)}
    for value in audit['candidate_identity'].values():
        if isinstance(value, dict) and set(value) == {'path', 'bytes', 'sha256'}:
            descriptors[value['path']] = {key: value[key] for key in ('bytes', 'sha256')}
    manifest_path = audit['candidate_identity']['manifest']['path']
    manifest_raw = read(OLD / manifest_path)
    assert hashlib.sha256(manifest_raw).hexdigest() == '5ab52c795d0821e76fd32264b8a9557451effaecd044ebb49b8a6ff893be61ee'
    manifest = json.loads(manifest_raw)
    for name, expected in manifest['artifacts'].items():
        relative = (Path(manifest_path).parent / name).as_posix()
        assert relative not in descriptors or descriptors[relative] == expected
        descriptors[relative] = expected
    assert len(descriptors) <= 128 and sum(row['bytes'] for row in descriptors.values()) <= 32 * 1024**2
    for name, expected in sorted(descriptors.items()):
        assert not Path(name).is_absolute() and all(part not in ('.', '..') for part in Path(name).parts)
        copy(OLD / name, BENCHMARK / name, expected)
    baseline_raw = read(BASELINE)
    assert hashlib.sha256(baseline_raw).hexdigest() == '172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c'
    copy(BASELINE, PACKAGE / 'tokenizer-provenance/manifest.json', identity(baseline_raw))
    instruction_raw = read(ARCHIVE / 'user-instruction.json')
    assert hashlib.sha256(instruction_raw).hexdigest() == '7158689e94fd42e60710b15a134ec8a2a2f446da993ef0b52e9cd815138ed164'
    copy(ARCHIVE / 'user-instruction.json', PACKAGE / 'authorization/user-instruction.json', identity(instruction_raw))
    record = {'schema': 'peano-hydra-training-evidence-staging-v1', 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'benchmark_root': str(BENCHMARK), 'benchmark_files': descriptors,
        'benchmark_file_count': len(descriptors), 'benchmark_total_bytes': sum(row['bytes'] for row in descriptors.values()),
        'tokenizer_provenance_manifest': identity(baseline_raw), 'user_instruction': identity(instruction_raw),
        'benchmark_review_created': False, 'reference_readiness_claimed': False,
        'model_weights_copied': False, 'gpu_jobs_started': 0}
    with output.open('xb') as stream:
        stream.write((json.dumps(record, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({key: value for key, value in record.items() if key != 'benchmark_files'}, sort_keys=True))


if __name__ == '__main__':
    main()
