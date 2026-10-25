"""Read-only exact source and token compatibility of the new frozen snapshot."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-training-execution-20260830')
OLD = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830')
WORK = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-training-2026-08-30')
COMMIT = 'b08a6b1303d73217f6cc23800ae15e50b17db792'
sys.path[:0] = [str(ROOT)]
from training.peano_hydra import scaling_experiment as experiment, frontier_training_launch as gate, origin_bridge as bridge


def main():
    with bridge._Tree(ROOT) as root, bridge._Tree(OLD) as old, bridge._Tree(WORK) as work, bridge._Tree(ARCHIVE) as archive:
        ready_raw = old.read('_deploy/hydra-frontier-candidate-v1/readiness.json', 64 * 1024)
        ready = bridge._decode(ready_raw, 64 * 1024, 'candidate readiness')
        assert hashlib.sha256(ready_raw).hexdigest() == 'f5bf419b74d10f8dab70ec97c79303e5b22764988e718cfcd29f7f631d386f50'
        actual = experiment.execution_source_inventory()
        assert ready['source_files'] == actual and len(actual) == 53, 'candidate53 source changed'
        native_raw = work.read('_deploy/hydra-frontier-training-v1/admitted/source/manifest.json', 4 * 1024**2)
        native_manifest = bridge._decode(native_raw, 4 * 1024**2, 'admitted native manifest')
        assert hashlib.sha256(native_raw).hexdigest() == 'bc2e5c7ccbeadd6b0d26c289095a89e3558265d7916196bfc68f8c2879be353a'
        native_files = native_manifest['composition']['plan']['source_identity']['files']
        assert len(native_files) == 38
        for name, expected in native_files.items():
            observed, _ = root.fingerprint(name, maximum=4 * 1024**2)
            assert observed['sha256'] == expected, 'native38 source changed: ' + name
        plan_raw = archive.read('training-execution-plan-01.json', 2 * 1024**2)
        assert hashlib.sha256(plan_raw).hexdigest() == 'fbe68bb706bce0e7b670a0ff068e1ebf34072a2bdf26a4ee2fb02ca482e6d3c3'
        plan = bridge._decode(plan_raw, 2 * 1024**2, 'training source plan')
        assert gate.REQUIRED_SOURCES <= set(plan['files']), 'launch-required source is absent from snapshot'
        token_raw = archive.read('token-preflight.json', 4 * 1024**2)
        assert hashlib.sha256(token_raw).hexdigest() == '5e429426d1899f2a898b7e5affc1a3ee141224ddac286a9bacd1c40afe38f365'
        tokens = bridge._decode(token_raw, 4 * 1024**2, 'genuine production token preflight')
        token_sources = tokens['execution_source_files']
        assert set(token_sources) == gate.TOKEN_PREFLIGHT_SOURCES
        for name, expected in token_sources.items():
            observed, _ = root.fingerprint(name, maximum=4 * 1024**2)
            assert observed['sha256'] == expected, 'token preflight source changed: ' + name
        for tree in (root, old, work, archive):
            tree.assert_unchanged()
        record = {'schema': 'peano-hydra-frontier-training-final-source-compatibility-v1', 'status': 'passed',
            'snapshot_root': str(ROOT), 'git_commit': COMMIT,
            'candidate_readiness_file_sha256': hashlib.sha256(ready_raw).hexdigest(),
            'candidate53_files_unchanged': True, 'candidate_execution_source_files': actual,
            'native_manifest_sha256': hashlib.sha256(native_raw).hexdigest(),
            'native38_files_unchanged': True, 'native_source_files': native_files,
            'training_launch_required_source_count': len(gate.REQUIRED_SOURCES),
            'training_launch_required_sources_present': True,
            'token_preflight_file_sha256': hashlib.sha256(token_raw).hexdigest(),
            'token_execution_source_files': token_sources, 'token_source_files_unchanged': True,
            'candidate_rebuild_required': False,
            'generation_commit_remains': '278d80552ab55b080365ddbae0d1d49be2fdc396',
            'separate_training_execution_snapshot': True, 'native_proofs_replayed_by_this_check': 0,
            'training_authorized_by_this_check': False, 'gpu_execution_authorized_by_this_check': False}
        raw = json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2).encode() + b'\n'
        path = ARCHIVE / 'final-source-compatibility-01.json'
        with path.open('xb') as stream:
            stream.write(raw)
        print(json.dumps({'status': 'passed', 'file': str(path), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'candidate_files': len(actual), 'native_files': len(native_files),
            'launch_required_files': len(gate.REQUIRED_SOURCES), 'token_files': len(token_sources)}, sort_keys=True))


if __name__ == '__main__':
    main()
