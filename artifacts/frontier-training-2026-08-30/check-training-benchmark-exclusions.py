"""Independent bounded audit of actual admitted TRAIN/DEV benchmark exclusions.

This archive-only helper creates no dataset, human review, reference-readiness
assertion, training approval or comparison authority. It checks every actual
model row against its complete admitted native transition, then independently
audits roots, whole logical templates and complete benchmark reference states
against those exact TRAIN/DEV bytes. No proof, model, SSH or scheduler runs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-training-2026-08-30')
PACKAGE = '_deploy/hydra-frontier-training-v1/admitted'
SCHEMA = 'peano-hydra-frontier-training-benchmark-exclusions-v1'
MAX_ROW = 256 * 1024
MAX_ROWS = 16384
MAX_INPUT_BYTES = 128 * 1024**2
MAX_REPORT_BYTES = 2 * 1024**2
SUPPORT = ('training/peano_hydra/scaling_admission.py', 'training/peano_hydra/scaling_workflow.py',
           'training/peano_hydra/frontier_benchmark_candidates.py', 'training/peano_hydra/frontier_benchmark_audit.py',
           'training/peano_hydra/frontier_benchmark_protocol.py', 'training/peano_hydra/origin_bridge.py',
           'training/peano_hydra/review_runtime.py', 'scripts/hydra_bounded_exec.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode()


def digest(record):
    return hashlib.sha256(canonical(record)).hexdigest()


def expected_reference(row, *, edition_identity_sha256, source_manifest_sha256):
    """Independent reconstruction of the complete compact model-facing row."""
    require(row['split'] in {'train', 'dev'} and row['kernel_checked'] is True,
            'native row escaped the admitted positive TRAIN/DEV boundary')
    return {'schema': 'peano-hydra-frontier-posttrain-reference-v1',
        'epoch_sha256': row['epoch_sha256'], 'edition_identity_sha256': edition_identity_sha256,
        'theorem_name': row['theorem_name'],
        'theorem_statement_sha256': hashlib.sha256(row['theorem'].encode()).hexdigest(),
        'lineage_sha256': row['lineage_sha256'], 'split': row['split'], 'source_split': row['split'],
        'source_transition_sha256': digest(row), 'state_sha256': row['state_sha256'],
        'action': row['action'], 'prompt': row['prompt'], 'completion': row['completion'],
        'environment_sha256': row['environment_sha256'], 'kernel_checked': True,
        'authority_profile': 'peano-authority-primitive-v1', 'family': row['family'],
        'source_manifest_sha256': source_manifest_sha256}


def check_reference(row, expected_hash, *, split, source_sha, reference_hashes):
    require(type(row) is dict and row.get('split') == split and row.get('source_split') == split
            and row.get('source_manifest_sha256') == source_sha
            and row.get('source_transition_sha256') == expected_hash
            and digest(row) == reference_hashes.get(expected_hash),
            'actual model row differs from the full native reference or first-occurrence order')


def _rows(tree, filename, expected):
    """Stream one exact admitted JSONL with no links, mutation or truncation."""
    from training.peano_hydra import origin_bridge as bridge
    descriptor = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=tree.directory())
    seen, size, sha = 0, 0, hashlib.sha256()
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == expected['bytes'],
                'model rows are not one bounded pinned regular file')
        while raw := stream.readline(MAX_ROW + 1):
            seen += 1
            size += len(raw)
            require(seen <= MAX_ROWS and len(raw) <= MAX_ROW and raw.endswith(b'\n') and size <= expected['bytes'],
                    'model row framing/count/bytes exceeded')
            sha.update(raw)
            yield bridge._decode(raw, MAX_ROW, 'actual admitted model row')
        after = os.fstat(stream.fileno())
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_nlink, s.st_mtime_ns, s.st_ctime_ns)
    require(signature(before) == signature(after) == signature(os.stat(filename, dir_fd=tree.directory(), follow_symlinks=False))
            and size == expected['bytes'] and sha.hexdigest() == expected['sha256'] and seen == expected['rows'],
            'actual model row file differs from its complete published descriptor')


def audit_admitted(request):
    root = Path(request['source_root'])
    sys.path[:0] = [str(root), str(root / 'peano-lab/py')]
    from training.peano_hydra import origin_bridge as bridge
    from training.peano_hydra import scaling_admission as admission
    from training.peano_hydra import scaling_workflow as workflow
    from training.peano_hydra import frontier_benchmark_audit as audit_api
    from training.peano_hydra.frontier_benchmark_protocol import benchmark_review_requirements
    admitted = bridge._absolute(Path(request['admitted_directory']))
    require(admitted == root / PACKAGE, 'training-only admitted path changed from the explicit package')
    benchmark_manifest = bridge._absolute(Path(request['benchmark_manifest']))
    benchmark_audit = bridge._absolute(Path(request['benchmark_audit']))
    # This is the non-authorizing metadata entry point: no accepted benchmark
    # review or uncompleted reference-readiness descriptor is required here.
    requirements = benchmark_review_requirements(benchmark_manifest, request['benchmark_manifest_sha256'],
                                                benchmark_audit, request['benchmark_audit_sha256'])
    require(requirements['status'] == 'pending_external_human_review_and_reference_readiness',
            'training-only exclusion check must not silently claim comparison readiness')
    with bridge._Tree(benchmark_manifest.parent) as benchmark_tree:
        manifest_raw = benchmark_tree.read(benchmark_manifest.name, 512 * 1024)
        require(hashlib.sha256(manifest_raw).hexdigest() == request['benchmark_manifest_sha256'], 'benchmark raw pin changed')
        benchmark = bridge._decode(manifest_raw, 512 * 1024, 'benchmark candidate manifest')
        bundle_raw = benchmark_tree.read('bundle.json', 8 * 1024**2)
        require(hashlib.sha256(bundle_raw).hexdigest() == benchmark['artifacts']['bundle.json']['sha256'],
                'complete benchmark reference bundle changed')
        bundle = bridge._decode(bundle_raw, 8 * 1024**2, 'benchmark native reference bundle')
        benchmark_tree.assert_unchanged()
    with bridge._Tree(admitted) as admitted_tree, bridge._Tree(admitted / 'preparation') as preparation:
        admission_raw = admitted_tree.read('training-admission.json', 16 * 1024**2)
        require(hashlib.sha256(admission_raw).hexdigest() == request['admission_sha256'], 'training admission external raw pin changed')
        admitted_record = bridge._decode(admission_raw, 16 * 1024**2, 'training admission')
        identity = admission.admission_identity(admitted / 'source')
        require(identity['admission_file_sha256'] == request['admission_sha256'], 'admission identity changed')
        manifest_raw = preparation.read('manifest.json', 4 * 1024**2)
        require(hashlib.sha256(manifest_raw).hexdigest() == request['preparation_manifest_sha256'], 'preparation external raw pin changed')
        manifest = bridge._decode(manifest_raw, 4 * 1024**2, 'admitted preparation')
        source_sha = identity['source_manifest_sha256']
        require(manifest['curriculum_identity']['review_admission'] == identity
                and manifest['source']['manifest_sha256'] == source_sha
                and root / manifest['source']['directory'] == admitted / 'source'
                and manifest['epoch_sha256'] == requirements['candidate_binding']['epoch_sha256']
                and manifest['authority_profile'] == 'peano-authority-primitive-v1',
                'admission/preparation/native-source/benchmark epoch join changed')
        require(set(manifest['splits']) == {'train', 'dev'}, 'unexpected model-facing split')
        observed_files = {}
        for filename, expected in manifest['files'].items():
            observed, _ = preparation.fingerprint(filename, maximum=64 * 1024**2)
            observed_files[filename] = {key: observed[key] for key in ('bytes', 'sha256')}
            require(observed_files[filename] == {key: expected[key] for key in ('bytes', 'sha256')},
                    'actual preparation bytes changed: ' + filename)
        require(sum(row['bytes'] for row in observed_files.values()) <= 64 * 1024**2,
                'actual preparation exceeds its unchanged64MiB boundary')
        require(all(observed_files[name]['bytes'] == 0 for name in ('quarantine.jsonl', 'preferences.jsonl', 'discovery.jsonl')),
                'this training-only pilot must not add quarantine/preferences/discovery consumption')
        # This independent stream/index never instantiates a VerifiedSource or
        # pretends metadata was a fresh native proof execution.
        reference_hashes, ordered, dedup, raw_counts, duplicate_counts = {}, {'train': [], 'dev': []}, {}, Counter(), Counter()
        native_root_names, native_families, native_lineages, native_statements = set(), set(), set(), set()
        for row in workflow.source_rows(admitted / 'source', expected_manifest_sha256=source_sha):
            split = row['split']
            require(split in ordered and row['epoch_sha256'] == manifest['epoch_sha256'], 'native source row escaped admitted split/epoch')
            raw_counts[split] += 1
            require(sum(raw_counts.values()) <= MAX_ROWS, 'complete native source row bound exceeded')
            ref = expected_reference(row, edition_identity_sha256=manifest['edition_identity_sha256'], source_manifest_sha256=source_sha)
            row_sha = ref['source_transition_sha256']
            reference_hashes[row_sha] = digest(ref)
            key = digest([row['epoch_sha256'], row['environment_sha256'], row['lineage_sha256'], row['state_sha256'], row['action']])
            if key in dedup:
                require(dedup[key] == split, 'same dedup identity crosses TRAIN/DEV')
                duplicate_counts[split] += 1
            else:
                dedup[key] = split
                ordered[split].append(row_sha)
            native_root_names.add(row['theorem_name'])
            native_families.add(row['family'])
            native_lineages.add(row['lineage_sha256'])
            native_statements.add(ref['theorem_statement_sha256'])
        actual_counts = {}
        for split in ('train', 'dev'):
            count = 0
            for position, row in enumerate(_rows(preparation, split + '.jsonl', manifest['files'][split + '.jsonl'])):
                require(position < len(ordered[split]), 'actual split has extra native references')
                check_reference(row, ordered[split][position], split=split, source_sha=source_sha, reference_hashes=reference_hashes)
                count += 1
            require(count == len(ordered[split]) == manifest['splits'][split]['rows']
                    == identity['counts']['candidate_projected_split_rows'][split], 'actual split lost a complete first-occurrence reference')
            actual_counts[split] = count
        require(sum(raw_counts.values()) == identity['counts']['native_transition_rows']
                and sum(duplicate_counts.values()) == identity['counts']['duplicate_transitions_removed'],
                'native/source/model-row accounting differs from admitted counts')
        excluded = requirements['whole_template_exclusions']
        require(len(excluded) == 64 and not native_root_names & {r['name'] for r in excluded}
                and not native_families & {r['family'] for r in excluded}
                and not native_lineages & {r['lineage_sha256'] for r in excluded}
                and not native_statements & {r['statement_sha256'] for r in excluded},
                'benchmark primary/reserved identity entered an actual admitted source split')
        specs = []
        for split in ('train', 'dev'):
            specs.append({'path': str(admitted / 'preparation' / (split + '.jsonl')), 'format': 'jsonl',
                'role': 'actual-admitted-' + split + '-model-rows', 'anchor_origin': 'externally pinned preparation manifest',
                'expected_sha256': manifest['files'][split + '.jsonl']['sha256']})
        specs += [{'path': str(admitted / 'source' / name), 'format': 'jsonl' if name.endswith('.jsonl') else 'json',
                   'role': 'complete-admitted-native-source', 'anchor_origin': 'externally pinned training admission',
                   'expected_sha256': admitted_record['source_files'][name]['sha256']}
                  for name in ('manifest.json', 'sft.jsonl')]
        require(sum(Path(spec['path']).stat().st_size for spec in specs) <= MAX_INPUT_BYTES, 'independent audit input byte bound exceeded')
        exposure = audit_api.build_exposure_index(specs, coverage_gaps=[
            'This receipt audits only the actual admitted TRAIN/DEV preparation and complete native source, not all historical/model-pretraining exposure.',
            'It supplies no human benchmark review, reference readiness, unseen-semantics claim or comparison authorization.',
            'Coarse logical-template checks and exact rendered states retain the existing bounded audit limitations.'])
        reference_rows = [{**row, 'theorem_name': proof['name']} for proof in bundle['proofs']
                          for row in proof['native_result']['trace'][:-1]]
        expected_counts = {proof['name']: proof['native_result']['tactics_applied'] for proof in bundle['proofs']}
        audit = audit_api.audit_candidates(exposure, bundle['plan']['routes'], candidate_identity={
            'benchmark_manifest_file_sha256': request['benchmark_manifest_sha256'],
            'benchmark_bundle_sha256': bundle['bundle_sha256'], 'admission_file_sha256': request['admission_sha256'],
            'preparation_manifest_file_sha256': request['preparation_manifest_sha256']},
            reference_records=reference_rows, reference_expected_counts=expected_counts)
        summary = audit_api.audit_summary(audit)
        preparation.assert_unchanged()
        admitted_tree.assert_unchanged()
        require(admission.admission_identity(admitted / 'source') == identity, 'admitted identity changed during independent exclusion check')
        result = {'schema': SCHEMA, 'status': 'passed' if summary['status'] == 'no-detected-overlap-in-declared-sources' else 'blocked',
            'request': request, 'admission_identity': identity, 'source_manifest_sha256': source_sha,
            'actual_model_rows': actual_counts, 'native_source_rows': dict(raw_counts),
            'deduplicated_rows_removed': sum(duplicate_counts.values()), 'all_actual_model_references_checked': True,
            'first_occurrence_order_checked': True, 'reference_projection_sha256': digest(ordered),
            'benchmark_candidates_excluded': 64, 'benchmark_primary_count': 32, 'benchmark_reserved_count': 32,
            'benchmark_exclusions_sha256': requirements['candidate_binding']['all64_exclusions_sha256'],
            'audit': audit, 'audit_summary': summary,
            'proofs_replayed': 0, 'model_calls': 0, 'reference_readiness_granted': False,
            'comparison_authorized': False, 'training_authorized': False, 'gpu_execution_authorized': False,
            'sealed_benchmark': False, 'research_claim_eligible': False,
            'scope': 'Actual admitted row/source/exclusion byte check; no native/reference execution or new authorization'}
        result['check_sha256'] = digest(result)
        require(len(canonical(result)) <= MAX_REPORT_BYTES, 'independent exclusion report exceeds bound')
        return result


def main():
    if sys.argv[1:] == ['--worker']:
        request = json.loads(sys.stdin.buffer.read(32769))
        result = audit_admitted(request)
        require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules), 'exclusion audit imported model/tokenizer code')
        print(canonical(result).decode(), flush=True)
        return 0 if result['status'] == 'passed' else 1
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--admitted-directory', type=Path, required=True)
    parser.add_argument('--expected-preparation-sha256', required=True)
    parser.add_argument('--expected-admission-sha256', required=True)
    parser.add_argument('--benchmark-manifest', type=Path, required=True)
    parser.add_argument('--expected-benchmark-manifest-sha256', required=True)
    parser.add_argument('--benchmark-audit', type=Path, required=True)
    parser.add_argument('--expected-benchmark-audit-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--process-receipt', type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.absolute()
    sys.path[:0] = [str(root)]
    from training.peano_hydra import origin_bridge as bridge
    from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
    output, receipt = bridge._absolute(args.output), bridge._absolute(args.process_receipt)
    require(output.parent == receipt.parent == ARCHIVE and output != receipt and not output.exists() and not receipt.exists(),
            'fresh independent audit/result receipts are required in the new training archive')
    request = {'source_root': str(root), 'admitted_directory': str(args.admitted_directory.absolute()),
        'preparation_manifest_sha256': args.expected_preparation_sha256, 'admission_sha256': args.expected_admission_sha256,
        'benchmark_manifest': str(args.benchmark_manifest.absolute()), 'benchmark_manifest_sha256': args.expected_benchmark_manifest_sha256,
        'benchmark_audit': str(args.benchmark_audit.absolute()), 'benchmark_audit_sha256': args.expected_benchmark_audit_sha256}
    payload = canonical(request)
    before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in SUPPORT}
    before['archive_helper'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    command = (sys.executable, '-I', '-B', '-X', 'pycache_prefix=/dev/null', str(Path(__file__).absolute()), '--worker')
    limits = ProcessLimits(cpu_seconds=120, wall_seconds=150, rss_bytes=1024**3, output_bytes=MAX_REPORT_BYTES)
    record = {'schema': SCHEMA + '-process', 'request': request, 'source_files_before': before, 'status': 'failed'}
    try:
        process = run_bounded(command, cwd=root, limits=limits, input_bytes=payload)
        record['process'] = process
        after = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in SUPPORT}
        after['archive_helper'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        record['source_files_after'] = after
        validate_process_record(process, command=command, limits=limits, input_bytes=payload, success_codes=(0,))
        require(before == after, 'audit helper or inspected code changed during execution')
        result = bridge._decode(process['stdout'].encode(), MAX_REPORT_BYTES, 'independent exclusion report')
        require(result['status'] == 'passed', 'actual admitted benchmark exclusions are blocked')
        with output.open('xb') as stream:
            stream.write(canonical(result) + b'\n')
        record['status'] = 'passed'
        record['result_file_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    except BaseException as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
    with receipt.open('xb') as stream:
        stream.write(canonical(record) + b'\n')
    print(json.dumps({'status': record['status'], 'output': str(output) if output.exists() else None,
                      'process_receipt': str(receipt), 'error': record.get('error')}, sort_keys=True))
    return 0 if record['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
