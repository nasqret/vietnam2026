"""Bounded local inventory selector; original files are read-only inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

WORK = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
LOCAL = WORK.parents[1]
HISTORY = Path('/Users/bnaskrecki/codex/test/vietnam2026-new-theorems')
ORIGIN = LOCAL / '_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2'
PILOT = LOCAL / '_deploy/hydra-frontier-pilot-recovery-20260830'
sys.path[:0] = [str(WORK), str(WORK / 'peano-lab/py')]
from training.peano_hydra import frontier_benchmark_audit as audit


def select():
    specs = {}
    omitted = []

    def add(path, role, expected=None, anchor='fresh-local-observation-not-historical-attestation'):
        path = Path(path)
        if str(path) in specs:
            if expected is not None:
                specs[str(path)].update(expected_sha256=expected, anchor_origin=anchor)
            return
        specs[str(path)] = {'path': str(path), 'format': 'jsonl' if path.suffix == '.jsonl' else 'json',
                            'role': role, 'anchor_origin': anchor}
        if expected is not None:
            specs[str(path)]['expected_sha256'] = expected

    # These two anchors are external to the files and were retained in the
    # recovery guide before this benchmark work began.
    base = ORIGIN / 'origin-source/_deploy/hydra-corrective-v2/source'
    for directory, manifest_sha, role in [
        (base, '3e7fccb43804f5272a61282005c961b492ef891dbb37998f1c4a81ee9dfb4ef4', 'saved-baseline-training-source'),
        (PILOT / 'source', 'bc2e5c7ccbeadd6b0d26c289095a89e3558265d7916196bfc68f8c2879be353a', 'current-unadmitted-frontier-candidate-source')]:
        manifest = directory / 'manifest.json'
        raw, _ = audit.read_file(manifest, manifest_sha)
        value = json.loads(raw)
        add(manifest, role, manifest_sha, 'externally-pinned-recovery-source-manifest')
        for name, identity in value['files'].items():
            if name.endswith('.jsonl'):
                add(directory / name, role, identity['sha256'], 'file-descriptor-in-pinned-source-manifest')
    add(PILOT / 'readiness.json', 'current-candidate-readiness',
        'ac99cebd6fc3014c666fda8c2ad6b5edc78c0bc10d868e04b6910a300a21cfb4',
        'external-recovery-readiness-anchor')
    add(ORIGIN / 'model/manifest.json', 'baseline-model-metadata-no-weights')
    add(ORIGIN / 'origin/origin-receipt.json', 'preserved-origin-receipt',
        '9f3509835a2dffeabf7590af8347aad9a622342f5131a20e26eaf0faa40ab7d1',
        'origin-manifest-previously-retained-receipt-anchor')

    dataset_names = {'sft.jsonl', 'train.jsonl', 'dev.jsonl', 'val.jsonl', 'test.jsonl',
                     'preferences.jsonl', 'discovery.jsonl', 'quarantine.jsonl',
                     'raw-traces.jsonl', 'session-metadata.jsonl', 'cases.jsonl'}
    roots = [(ORIGIN / 'origin-source', 'preserved-origin-training-and-public-corpus'),
             (HISTORY / '_deploy', 'historical-local-build-datasets'),
             (HISTORY / 'results/peano-hydra', 'historical-collected-run-datasets'),
             (HISTORY / 'data', 'historical-policy-datasets'),
             (HISTORY / 'peano-lab/corpus', 'historical-public-corpus'),
             (LOCAL / 'data', 'original-local-policy-datasets'),
             (LOCAL / 'peano-lab/corpus', 'original-local-public-corpus')]
    for root, role in roots:
        for path in sorted(root.rglob('*.jsonl')):
            if path.name not in dataset_names:
                omitted.append({'path': str(path), 'reason': 'not-a-selected-dataset-basename'})
                continue
            if any('pytest' in part or part.startswith('test_') or part == 'tests' for part in path.parts):
                omitted.append({'path': str(path), 'reason': 'unit-test-fixture-not-production-exposure'})
                continue
            if path.is_symlink():
                omitted.append({'path': str(path), 'reason': 'symlink-not-followed'})
                continue
            add(path, role)
            manifest = path.parent / 'manifest.json'
            if manifest.is_file() and not manifest.is_symlink():
                add(manifest, role + '-manifest')
    # Every recorded Hydra JSON/JSONL artifact in the interrupted repository,
    # including public comparison goals and completed search states. Captured
    # stdout strings are not recursively interpreted as source documents.
    for path in sorted((HISTORY / 'artifacts/peano-hydra').rglob('*')):
        if path.is_file() and path.suffix in {'.json', '.jsonl'} and not path.is_symlink():
            add(path, 'historical-hydra-public-development-and-receipts')
    for path in sorted((PILOT / 'shards').glob('*.json*')):
        add(path, 'current-proposed-deduplicated-train-dev-projection')
    # Both available epoch catalogs are public exposure even when a catalog
    # theorem was not used in an optimizer row. Dependencies remain explicit.
    for root in (ORIGIN / 'origin-source', WORK):
        catalogs = sorted((root / 'artifacts/peano-library/alpha').glob('catalog-v*.json'))
        catalogs.append(root / 'artifacts/peano-library/catalog-v1.json')
        for path in catalogs:
            add(path, 'public-catalog-statements-and-declared-dependencies')
    return list(specs.values()), omitted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to replace an exposure receipt')
    specs, omitted = select()
    coverage_gaps = [
        'Qwen base-model pretraining and other unrecorded external exposure are unavailable; no semantic-unseen claim.',
        'Files selected by the exact attached selector only; arbitrary source-code/test/prose/session-history strings and uncollected remote records are not exhaustively interpreted as formulas.',
        'Historical local files without an external anchor are conservatively counted as exposure; fresh hashes do not authenticate their original training use.',
        'Captured stdout/stderr strings inside transport receipts are not recursively parsed as JSON; standalone source/results documents are included when present.',
        'Only declared family/parent/dependency relations are collected; unknown or semantic derivational links need human review.',
        'Canonical comparisons use this pinned native parser profile; out-of-profile formulas/metavariables are separately reported, not silently treated as clean.',
        'Independent human benchmark ownership and final-test sealing are not established by this local audit.'
    ]
    print(json.dumps({'selected_files': len(specs), 'omitted_jsonl_paths': len(omitted)}), flush=True)
    result = audit.build_exposure_index(specs, coverage_gaps=coverage_gaps)
    result['selector_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['auditor_sha256'] = hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest()
    result['omitted_discovered_jsonl'] = omitted
    result['current_pilot_projection'] = {'native_routes': 1152, 'native_transitions': 15264,
        'proposed_train_rows': 12772, 'proposed_dev_rows': 2096, 'approved_model_rows': 0,
        'evidence_anchor': 'ac99cebd6fc3014c666fda8c2ad6b5edc78c0bc10d868e04b6910a300a21cfb4'}
    result['index_sha256'] = audit.digest(result)
    with args.output.open('xb') as stream:
        stream.write(audit.canonical_bytes(result) + b'\n')
    print(json.dumps({'output': str(args.output), 'bytes': args.output.stat().st_size,
                     'inventory_sha256': result['source_inventory_sha256'],
                     'features': {k: len(v) for k, v in result['features'].items()},
                     'parse_gaps': result['parse_gaps'], 'listed_bytes': result['listed_bytes'],
                     'unique_payloads': result['unique_payloads']}), flush=True)


if __name__ == '__main__':
    main()
