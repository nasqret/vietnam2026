"""Join the fixed candidate receipts to the completed exposure inventory."""
from __future__ import annotations

import hashlib
import io
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'peano-lab/py')]
from training.peano_hydra import frontier_benchmark_audit as audit


def descriptor(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(OUT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write(audit.canonical_bytes(value) + b'\n')


def main():
    required_outputs = ['benchmark-exposure-audit-01.json', 'benchmark-exposure-evidence-01.json',
                        'benchmark-audit-tests-01.json', 'rejected-template-evidence-01.json']
    if any((OUT / name).exists() for name in required_outputs):
        raise SystemExit('refusing to overwrite finalized audit evidence')
    source = OUT / 'benchmark-candidates-build-02'
    manifest = json.loads((source / 'manifest.json').read_text())
    plan = json.loads((source / 'plan.json').read_text())
    bundle = json.loads((source / 'bundle.json').read_text())
    exposure = json.loads((OUT / 'exposure-index-02.json').read_text())
    identity = {name: descriptor(OUT / path) for name, path in {
        'manifest': 'benchmark-candidates-build-02/manifest.json',
        'plan': 'benchmark-candidates-build-02/plan.json',
        'bundle': 'benchmark-candidates-build-02/bundle.json',
        'native_build_process': 'benchmark-candidates-build-02/process.json',
        'native_verify_process': 'benchmark-candidates-verify-01/process.json',
        'native_verify_result': 'benchmark-candidates-verify-01/verification.json'}.items()}
    identity.update({
        'manifest_sha256': manifest['manifest_sha256'], 'plan_sha256': plan['plan_sha256'],
        'bundle_sha256': bundle['bundle_sha256'],
        'source_identity_sha256': manifest['source_identity']['source_files_sha256'],
        'primary_goals_sha256': audit.digest(manifest['primary_goals']),
        'reserved_goals_sha256': audit.digest(manifest['reserved_goals'])})
    rows = [dict(row, theorem_name=proof['name']) for proof in bundle['proofs']
            for row in proof['native_result']['trace'][:-1]]
    counts = {proof['name']: proof['native_result']['tactics_applied'] for proof in bundle['proofs']}
    result = audit.audit_candidates(exposure, plan['routes'], candidate_identity=identity,
                                    reference_records=rows, reference_expected_counts=counts)
    summary = audit.audit_summary(result)
    if summary['status'] != 'no-detected-overlap-in-declared-sources':
        raise SystemExit(json.dumps(summary, sort_keys=True))
    write('benchmark-exposure-audit-01.json', result)

    test_path = ROOT / 'peano-lab/py/tests/test_peano_hydra_frontier_benchmark_audit.py'
    spec = importlib.util.spec_from_file_location('benchmark_audit_test', test_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    forbidden = sorted(name for name in sys.modules if name.split('.')[0] in {'torch', 'transformers', 'peft', 'tokenizers'})
    write('benchmark-audit-tests-01.json', {'schema': 'peano-hydra-benchmark-audit-tests-v1',
        'test_count': tests.testsRun, 'failures': len(tests.failures), 'errors': len(tests.errors),
        'passed': tests.wasSuccessful() and not forbidden, 'output': stream.getvalue(),
        'auditor_sha256': hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest(),
        'tests_sha256': hashlib.sha256(test_path.read_bytes()).hexdigest(),
        'scope': 'small synthetic exposure fixtures and native parser only; no native QED/model training claim',
        'forbidden_model_modules': forbidden})
    rejected = audit.audit_candidates(exposure, [{'id': 'rejected_not_exists_to_forall_not',
        'family': 'rejected_not_exists_to_forall_not',
        'statement': 'forall n. ~(exists x. x + 2 = n) -> forall x. ~(x + 2 = n)'}],
        candidate_identity={'design_only_never_evaluated': True,
                            'known_parent': 'not_multiple_pointwise'})
    write('rejected-template-evidence-01.json', rejected)
    evidence = {'schema': 'peano-hydra-benchmark-exposure-evidence-v1',
        'audit': descriptor(OUT / 'benchmark-exposure-audit-01.json'),
        'exposure_index': descriptor(OUT / 'exposure-index-02.json'),
        'exposure_process': descriptor(OUT / 'exposure-inventory-process-02.json'),
        'tests': descriptor(OUT / 'benchmark-audit-tests-01.json'),
        'rejected_template': descriptor(OUT / 'rejected-template-evidence-01.json'),
        'selector': descriptor(OUT / 'run-exposure-inventory.py'),
        'finalizer': descriptor(Path(__file__)),
        'producer_auditor_sha256': exposure['auditor_sha256'],
        'consumer_auditor_sha256': hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest(),
        'listed_files': len(exposure['source_inventory']), 'unique_payloads': exposure['unique_payloads'],
        'listed_bytes': exposure['listed_bytes'], 'exposure_features': {k: len(v) for k, v in exposure['features'].items()},
        'summary': summary, 'all_64_candidate_reference_transitions': len(rows),
        'human_review_created': False, 'training_rows_created': 0, 'models_loaded': False,
        'server_writes': False, 'gpu_jobs_started': 0,
        'historical_template_hash_namespace_complete': False,
        'template_check_scope': 'declared family IDs and whole-root logical skeleton; no complete semantic derivation algorithm',
        'raw_signature_note': 'Raw SHA-256 and canonical audit_sha256 are different identities; neither self-signs authorship.'}
    write('benchmark-exposure-evidence-01.json', evidence)
    print(json.dumps({'audit': evidence['audit'], 'status': summary['status'],
                      'tests_passed': tests.wasSuccessful(), 'candidate_count': len(plan['routes']),
                      'reference_transitions': len(rows)}, sort_keys=True))
    if not tests.wasSuccessful() or forbidden:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
