"""Retain the final source delta, tests and immutable execution identities."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import resource
import signal


ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-advancement-2026-08-30'
WORK = ROOT / '_deploy/hydra-frontier-recovery-work-20260830'
BASE = ROOT / '_deploy/hydra-frontier-training-execution-20260830'
FINAL = ROOT / '_deploy/hydra-advancement-execution-v2-20260830'
OUT = ARCHIVE / 'implementation-01'
RECEIPTS = {
    'baseline': (BASE / '_deploy/frontier-training-execution-freeze.json', None),
    'final': (FINAL / '_deploy/hydra-advancement-execution-freeze-v2.json',
              '8ea0b2861b37bc680cf99738e0a384a51d078d911fa6c2739e764b2fd142f91c'),
    'proposals': (ARCHIVE / 'self-training-proposal-source-01.json',
                  'fa5b34165a4bd2819b8c7e18a0ff7c39dd7d7da67445a6117b659bac4e5a7aed'),
    'reference': (ARCHIVE / 'v28-input-preflight-tests-source-01.json',
                  '71f57e21d24b264eddf28d743c67a68642a69696f2bbeb2c1720e902d1137c40'),
    'evaluation': (ARCHIVE / 'evaluation-integration-package-01.json',
                   '74ff9caa9d0835a4e26228fca0870cc2ed61900484442690f10db8a03b0c9084'),
}
TEST_ROOTS = (
    'conftest.py', 'test_peano_hydra_cold_replay_v28.py', 'test_peano_hydra_review_v28.py',
    'test_peano_hydra_review_inputs_v28.py', 'test_peano_hydra_frontier_evaluation_launch.py',
    'test_peano_hydra_frontier_saved_benchmark.py', 'test_peano_hydra_self_training_proposals.py',
    'test_peano_hydra_cold_replay.py', 'test_peano_hydra_review.py',
    'test_peano_hydra_self_training.py', 'test_peano_hydra_helios_runtime.py',
)


def read(path, maximum=2 * 1024**2):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= maximum
    raw = path.read_bytes()
    assert len(raw) <= maximum
    return raw


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, raw):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
    return pin(raw)


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(25)
    records, anchors = {}, {}
    for name, (path, expected) in RECEIPTS.items():
        raw = read(path)
        if expected is not None:
            assert hashlib.sha256(raw).hexdigest() == expected
        records[name] = json.loads(raw)
        anchors[name] = {'path': str(path), **pin(raw)}
    assert records['baseline']['git_commit'] == 'b08a6b1303d73217f6cc23800ae15e50b17db792'
    assert records['final']['git_commit'] == '1aa7ae8d61ca9e1e4f2410042b75ce9c3621a927'
    assert records['final']['snapshot_clean'] is True
    before, after = records['baseline']['files'], records['final']['files']
    assert not set(before) - set(after)
    changed = {name: value for name, value in after.items() if before.get(name) != value}
    data = records['final']['data_files']
    source_changes = {name: value for name, value in changed.items() if name not in data}
    patch = []
    for name, expected in sorted(source_changes.items()):
        raw = read(FINAL / name)
        assert pin(raw) == {k: expected[k] for k in ('bytes', 'sha256')}
        old = read(BASE / name) if name in before else b''
        patch.append('diff --git a/' + name + ' b/' + name + '\n')
        if name not in before:
            patch.append('new file mode ' + expected['mode'] + '\n')
        patch.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),
            raw.decode().splitlines(keepends=True), fromfile='a/' + name if name in before else '/dev/null',
            tofile='b/' + name))
    patch_raw = ''.join(patch).encode()
    assert len(patch_raw) <= 2 * 1024**2

    # Retain the actual final test roots and their statically imported sibling
    # fixtures. This does not claim to package Python/pytest or dynamic imports.
    tests, todo = {}, list(TEST_ROOTS)
    directory = WORK / 'peano-lab/py/tests'
    while todo:
        name = todo.pop()
        if name in tests:
            continue
        assert '/' not in name and name.endswith('.py') and len(tests) < 64
        raw = read(directory / name)
        tests[name] = raw
        for node in ast.walk(ast.parse(raw, filename=name)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                leaf = module.split('.')[0] + '.py'
                if leaf.startswith('test_') and (directory / leaf).is_file():
                    todo.append(leaf)
    assert sum(map(len, tests.values())) <= 8 * 1024**2

    final_evidence = {}
    for record, field in ((records['proposals'], 'changed_files'),
                          (records['reference'], 'source_files_at_recording'),
                          (records['evaluation'], 'changed_files')):
        for name, item in record[field].items():
            if not name.endswith('.py'):
                continue
            expected = item['sha256'] if isinstance(item, dict) else item
            raw = read(WORK / name)
            assert hashlib.sha256(raw).hexdigest() == expected, name
            if name in after:
                assert pin(raw) == {k: after[name][k] for k in ('bytes', 'sha256')}
            final_evidence[name] = expected

    compatibility_path = ROOT / 'artifacts/frontier-training-2026-08-30/final-source-compatibility-01.json'
    compatibility_raw = read(compatibility_path)
    compatibility = json.loads(compatibility_raw)
    preserved = {}
    for field in ('candidate_execution_source_files', 'native_source_files', 'token_execution_source_files'):
        expected = compatibility[field]
        for name, item in expected.items():
            sha = item['sha256'] if isinstance(item, dict) else item
            assert after[name]['sha256'] == sha
        preserved[field] = {'files': len(expected), 'all_hashes_unchanged': True}

    OUT.mkdir(mode=0o700)
    outputs = {'source.patch': save('source.patch', patch_raw)}
    for name, raw in sorted(tests.items()):
        assert read(directory / name) == raw
        path = 'test-sources/peano-lab/py/tests/' + name
        outputs[path] = save(path, raw)
    record = {'schema': 'peano-hydra-advancement-implementation-archive-v1',
              'status': 'final-source-and-test-artifacts-retained', 'anchors': anchors,
              'baseline_commit': records['baseline']['git_commit'],
              'final_commit': records['final']['git_commit'], 'snapshot_root': str(FINAL),
              'file_count': records['final']['file_count'], 'total_bytes': records['final']['total_bytes'],
              'added_files': sorted(set(after) - set(before)),
              'changed_existing_files': sorted(k for k in before if before[k] != after[k]),
              'removed_files': [], 'source_changes': source_changes, 'ancillary_data_inputs': data,
              'data_not_embedded_in_text_patch': True,
              'final_tested_python_hashes_match_current_frozen_source': final_evidence,
              'preserved_training_source_contracts': preserved,
              'compatibility_record': {'path': str(compatibility_path), **pin(compatibility_raw)},
              'test_source_roots': list(TEST_ROOTS), 'test_source_files': len(tests),
              'test_source_scope': 'Named test roots plus statically imported sibling fixtures and conftest; Python/pytest environment is not copied.',
              'outputs': outputs, 'model_weights_copied': False, 'tests_or_proofs_rerun': False,
              'new_gpu_job_submitted': False, 'research_readiness_claimed': False,
              'archive_helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    raw = (json.dumps(record, sort_keys=True, indent=2) + '\n').encode()
    descriptor = save('manifest.json', raw)
    print(json.dumps({'output': str(OUT), 'manifest': descriptor, 'added_files': len(record['added_files']),
                      'changed_existing_files': record['changed_existing_files'],
                      'test_source_files': len(tests), 'preserved_contracts': preserved}, sort_keys=True))
    signal.alarm(0)


if __name__ == '__main__':
    main()
