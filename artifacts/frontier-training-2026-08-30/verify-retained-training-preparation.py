"""Complete the original read-only preflight in a separate bounded process.

The earlier admission worker remains a failed attempt. This does not recreate
its success receipt or write into either retained/staged preparation directory.
The original posttrain.preflight performs one complete native replay and exact
prepared-payload reconstruction; this helper checks the remaining admission
postconditions and saves genuine preflight output only in the new archive.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-training-2026-08-30')
ADMITTED = ROOT / '_deploy/hydra-frontier-training-v1/admitted'
RUN_ID = 'frontier-training-v1'
STAGING_FILE = 'prepared-payload-staging-01.json'
STAGING_SHA = 'd61e6aca4f678fd7bd08ab5bb1ea12e1a4a6228789cc4046bfd45297ac7f0cdb'
PRIOR_FILE = 'admission-worker-process-01.json'
PRIOR_SHA = 'fce75f08552161842a1cf3a06b3ea8d224ba5a96b7883c3ef9243273a6753250'
PREFLIGHT_FILE = 'independent-original-preflight-01.json'
RESULT_FILE = 'independent-preparation-verification-01.json'
PROCESS_FILE = 'independent-preparation-verification-process-01.json'
SCHEMA = 'peano-hydra-retained-preparation-independent-verification-v1'
MAX_METADATA = 16 * 1024**2
MAX_OUTPUT = 8 * 1024**2
MAX_TREE = 128 * 1024**2
SUMMARY_KEYS = ('schema', 'run_id', 'epoch_sha256', 'training_rows', 'development_rows',
    'quarantined_rows', 'expected_optimizer_steps', 'required_pythonhashseed',
    'adapter_output_dir', 'preparation_manifest_sha256', 'model_trained',
    'cuda_initialized', 'token_budget_verified', 'tokenizer_audit_required_before_model_weights',
    'research_claim_eligible', 'unseen_holdout_claim_eligible')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode()


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check_preflight(preflight, admission, manifest, preparation_sha256):
    """The exact remaining post-preflight assertions, without another replay."""
    require(type(preflight) is dict and preflight.get('run_id') == RUN_ID
            and preflight.get('epoch_sha256') == admission['bindings']['epoch_sha256']
            and manifest['epoch_sha256'] == preflight['epoch_sha256']
            and preflight.get('preparation_manifest_sha256') == preparation_sha256,
            'original preflight changed the admitted run, epoch or preparation bytes')
    require(all(preflight.get(key) is False for key in ('model_trained', 'cuda_initialized',
            'token_budget_verified', 'research_claim_eligible', 'unseen_holdout_claim_eligible'))
            and preflight.get('tokenizer_audit_required_before_model_weights') is True,
            'original preflight changed its no-model/no-token/no-research boundary')
    counts = {'train': preflight.get('training_rows'), 'dev': preflight.get('development_rows'),
              'quarantine': preflight.get('quarantined_rows')}
    require(all(type(value) is int for value in counts.values()) and counts['quarantine'] == 0
            and sum(counts.values()) == admission['counts']['candidate_projected_rows']
            and all(counts[split] == admission['counts']['candidate_projected_split_rows'][split]
                    == manifest['splits'][split]['rows'] for split in ('train', 'dev')),
            'original preflight counts differ from the exact admitted projection')
    require(type(preflight.get('expected_optimizer_steps')) is int
            and preflight['expected_optimizer_steps'] == (counts['train'] + 7) // 8
            and preflight.get('required_pythonhashseed') == '20260826',
            'original preflight changed the reviewed batch/accumulation schedule or seed')
    return counts


def inventory(tree, expected):
    """Bind every one of the retained 17 files before and after the replay."""
    require(type(expected) is dict and len(expected) == 17
            and sum(record['bytes'] for record in expected.values()) <= MAX_TREE,
            'retained preparation inventory changed count/byte bound')
    require(set(os.listdir(tree.directory())) == {
        'candidate-readiness.json', 'lineage-proposal.json', 'lineage-review.json',
        'native-summary.json', 'training-admission.json', 'source', 'preparation'},
        'retained preparation has extra or missing top-level entries')
    for directory in ('source', 'preparation'):
        require(set(os.listdir(tree.directory(directory))) == {
            name.removeprefix(directory + '/') for name in expected if name.startswith(directory + '/')},
            'retained preparation has extra or missing child files')
    actual = {}
    for name, pinned in sorted(expected.items()):
        found, _ = tree.fingerprint(name, maximum=64 * 1024**2)
        actual[name] = {key: found[key] for key in ('bytes', 'sha256')}
        require(actual[name] == pinned, 'retained file changed from its externally pinned staging receipt: ' + name)
    tree.assert_unchanged()
    return actual


def verify():
    sys.path[:0] = [str(ROOT), str(ROOT / 'peano-lab/py')]
    from training.peano_hydra import origin_bridge as bridge
    from training.peano_hydra import posttrain, scaling_admission as admission, scaling_experiment as experiment
    with bridge._Tree(ARCHIVE) as archive, bridge._Tree(ADMITTED) as tree:
        staging_raw = archive.read(STAGING_FILE, 64 * 1024)
        prior_raw = archive.read(PRIOR_FILE, MAX_OUTPUT)
        require(descriptor(staging_raw)['sha256'] == STAGING_SHA
                and descriptor(prior_raw)['sha256'] == PRIOR_SHA, 'external staging/prior-failure anchor changed')
        staging = bridge._decode(staging_raw, 64 * 1024, 'retained preparation staging')
        prior = bridge._decode(prior_raw, MAX_OUTPUT, 'failed original admission worker')
        require(staging.get('exact_fresh_copy') is True and staging.get('source_unchanged') is True
                and staging.get('original_admission_worker_succeeded') is False
                and staging.get('destination') == str(ADMITTED)
                and prior.get('reason') == 'cpu_limit' and prior.get('returncode') != 0,
                'separate verification may not relabel the original failed attempt')
        files_before = inventory(tree, staging['files'])
        admission_raw = tree.read('training-admission.json', MAX_METADATA)
        record = bridge._decode(admission_raw, MAX_METADATA, 'training admission')
        readiness = bridge._decode(tree.read('candidate-readiness.json', MAX_METADATA), MAX_METADATA, 'candidate readiness')
        source_files_before = experiment.execution_source_inventory()
        require(source_files_before == readiness['source_files'], 'candidate-bound native execution source changed')
        identity = admission.admission_identity(ADMITTED / 'source')
        require(identity['admission_file_sha256'] == descriptor(admission_raw)['sha256'], 'raw admission anchor changed')
        manifest_raw = tree.read('preparation/manifest.json', MAX_METADATA)
        manifest = bridge._decode(manifest_raw, MAX_METADATA, 'published preparation')
        require(record['run_id'] == RUN_ID and manifest['run_id'] == RUN_ID
                and manifest['source']['directory'] == '_deploy/hydra-frontier-training-v1/admitted/source'
                and manifest['source']['manifest_sha256'] == identity['source_manifest_sha256']
                and manifest['source_projection'] == admission._source_projection(record)
                and manifest['curriculum_identity']['projection_policy'] == admission.PROJECTION_POLICY
                and manifest['curriculum_identity']['dataset_schema'] == admission.REFERENCE_EXAMPLE_SCHEMA
                and manifest['curriculum_identity']['review_admission'] == identity,
                'published projection/policy/native-source/admission identity differs')
        require(set(manifest['files']) == admission.PREPARATION_FILES - {'manifest.json'}
                and all({key: value[key] for key in ('bytes', 'sha256')} == files_before['preparation/' + name]
                        for name, value in manifest['files'].items())
                and sum(files_before['preparation/' + name]['bytes'] for name in admission.PREPARATION_FILES)
                    <= admission.MAX_PREPARATION_BYTES,
                'prepared payload inventory or unchanged byte ceiling differs')
        # No wrapper, monkeypatch, alternative validator or second preparation:
        # this is the unmodified original public function, with its native gate.
        preflight = posttrain.preflight(ADMITTED / 'preparation')
        counts = check_preflight(preflight, record, manifest, descriptor(manifest_raw)['sha256'])
        files_after = inventory(tree, staging['files'])
        require(admission.admission_identity(ADMITTED / 'source') == identity
                and source_files_before == experiment.execution_source_inventory(),
                'admission identity or native execution source changed during replay')
        tree.assert_unchanged()
        archive.assert_unchanged()
        require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules),
                'native preflight imported model/tokenizer code')
        preflight_raw = canonical(preflight) + b'\n'
        require(len(preflight_raw) <= MAX_METADATA, 'genuine original preflight exceeds unchanged metadata ceiling')
        result = {'schema': SCHEMA, 'status': 'independent-original-preflight-passed',
            'run_id': RUN_ID, 'admitted_directory': str(ADMITTED),
            'staging_receipt': {'path': STAGING_FILE, 'sha256': STAGING_SHA},
            'original_failed_process': {'path': PRIOR_FILE, 'sha256': PRIOR_SHA, 'reason': 'cpu_limit'},
            'original_admission_worker_succeeded': False,
            'independent_original_preflight_passed': True,
            'original_public_preflight_called_once': True,
            'full_native_source_replayed_and_preparation_reconstructed': True,
            'projection_and_native_reference_joins': 'Original load_preparation -> admitted native verifier -> first-occurrence projection -> reconstructed examples -> exact seven-file byte comparison; original preflight resolves complete native references.',
            'remaining_admission_postconditions_passed': True,
            'files_before': files_before, 'files_after': files_after, 'inputs_unchanged': True,
            'execution_source_files': source_files_before,
            'admission': identity, 'preparation_manifest_sha256': descriptor(manifest_raw)['sha256'],
            'prepared_split_rows': counts, 'candidate_projected_split_rows': record['counts']['candidate_projected_split_rows'],
            'native_source_split_rows': record['counts']['native_source_split_rows'],
            'duplicate_split_rows': record['counts']['duplicate_split_rows'],
            'preflight_file': {'path': PREFLIGHT_FILE, **descriptor(preflight_raw)},
            'preflight_summary': {key: preflight[key] for key in SUMMARY_KEYS},
            'human_review_record_created': False, 'human_identity_attested': False,
            'token_budget_verified': False, 'model_trained': False, 'cuda_initialized': False,
            'model_training_authorized': False, 'gpu_execution_authorized': False,
            'reference_readiness_passed': False, 'benchmark_comparison_authorized': False,
            'research_claim_eligible': False, 'sealed_benchmark': False,
            'scope': 'Separate read-only completion of original preflight; no repair or relabeling of the failed original worker, no new authorization.'}
        result['verification_sha256'] = hashlib.sha256(canonical(result)).hexdigest()
        require(len(canonical(result)) <= 64 * 1024, 'independent verification metadata exceeds compact result ceiling')
        return {'preflight': preflight, 'result': result}


def publish(name, raw):
    require(name in {PREFLIGHT_FILE, RESULT_FILE, PROCESS_FILE}, 'unexpected archive output')
    with (ARCHIVE / name).open('xb') as stream:
        stream.write(raw)


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode, 'isolated no-bytecode helper required')
    if sys.argv[1:] == ['--worker']:
        print(canonical(verify()).decode(), flush=True)
        return 0
    require(not sys.argv[1:], 'this bounded stage takes no implicit or caller-selected source paths')
    for name in (PREFLIGHT_FILE, RESULT_FILE, PROCESS_FILE):
        require(not (ARCHIVE / name).exists() and not (ARCHIVE / name).is_symlink(), 'fresh archive outputs required')
    sys.path[:0] = [str(ROOT)]
    from training.peano_hydra import origin_bridge as bridge, scaling_experiment as experiment
    from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
    command = (sys.executable, '-I', '-B', '-X', 'pycache_prefix=/dev/null', str(Path(__file__).absolute()), '--worker')
    limits = ProcessLimits(cpu_seconds=120, wall_seconds=180, rss_bytes=2 * 1024**3, output_bytes=MAX_OUTPUT)
    helper_before = descriptor(Path(__file__).read_bytes())
    code_before = experiment.execution_source_inventory()
    record = {'schema': SCHEMA + '-process', 'status': 'failed', 'helper_before': helper_before,
        'original_failed_process_sha256': PRIOR_SHA, 'staging_receipt_sha256': STAGING_SHA,
        'source_files_before': code_before, 'input_writes_performed': False, 'gpu_jobs_started': 0}
    try:
        process = run_bounded(command, cwd=ROOT, limits=limits)
        record['process'] = process
        record['helper_after'] = descriptor(Path(__file__).read_bytes())
        record['source_files_after'] = experiment.execution_source_inventory()
        validate_process_record(process, command=command, limits=limits, input_bytes=b'', success_codes=(0,))
        require(record['helper_after'] == helper_before and record['source_files_after'] == code_before,
                'helper or native execution source changed during final preflight')
        output = bridge._decode(process['stdout'].encode(), MAX_OUTPUT, 'original preflight and independent verification')
        require(output['result']['status'] == 'independent-original-preflight-passed', 'independent verification did not pass')
        preflight_raw = canonical(output['preflight']) + b'\n'
        require(descriptor(preflight_raw) == {key: output['result']['preflight_file'][key] for key in ('bytes', 'sha256')},
                'complete original preflight output descriptor changed')
        publish(PREFLIGHT_FILE, preflight_raw)
        publish(RESULT_FILE, canonical(output['result']) + b'\n')
        record['status'] = 'passed'
        record['preflight_file'] = descriptor(preflight_raw)
        record['result_file'] = descriptor(canonical(output['result']) + b'\n')
    except BaseException as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
    publish(PROCESS_FILE, canonical(record) + b'\n')
    print(json.dumps({'status': record['status'], 'preflight_file': str(ARCHIVE / PREFLIGHT_FILE),
        'result_file': str(ARCHIVE / RESULT_FILE), 'process_receipt': str(ARCHIVE / PROCESS_FILE),
        'error': record.get('error')}, sort_keys=True), flush=True)
    return 0 if record['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
