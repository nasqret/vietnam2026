"""File-only review preparation; does not select or execute the proposed repair."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
REPO = CAMPAIGN.parent.parent


def pin(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(REPO).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


remote = pin(HERE / 'remote_repair.py')
assert remote['sha256'] == '769692f2821f953a855ad40bf554dc74be131a388bf9477425a4b278039ac8fe'
ast.parse((HERE / 'remote_repair.py').read_bytes(), feature_version=(3, 6))
bundle = CAMPAIGN / 'combined-source-bundle-04'
payloads = {name: pin(bundle / name) for name in ('manifest.json', 'paired-source-pins.json')}
controller = 'source/output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py'
payloads[controller] = pin(bundle / controller)
assert sum(item['bytes'] for item in payloads.values()) == 423394
manifest = json.loads((bundle / 'manifest.json').read_text())
inventory = json.loads((CAMPAIGN / 'p6-source04-reconciliation-03/stdout.jsonl').read_text())
assert inventory['file_count'] == 821
assert [item['path'] for item in inventory['files']] == sorted(manifest['files'])[:821]
review = {
    'schema': 'hydra-source04-partial-copy-repair-review-v1',
    'status': 'prepared_locally_not_executed_not_selected',
    'purpose': 'One explicit exception to packet05 no-resume/no-automatic-retry scope: complete only the partial source04 transfer while preserving its failed255 attempt.',
    'remote_code': remote,
    'payloads': payloads,
    'failed_stage_actual': pin(CAMPAIGN / 'combined-inference-transfer-04/actual-completion.json'),
    'failed_stage_tool_actual': pin(CAMPAIGN / 'combined-inference-transfer-04/actual-tool-completion.json'),
    'partial_inventory': pin(CAMPAIGN / 'p6-source04-reconciliation-03/stdout.jsonl'),
    'partial_inventory_tool_actual': pin(CAMPAIGN / 'p6-source04-reconciliation-03/actual-tool-completion.json'),
    'partial_assessment': pin(CAMPAIGN / 'p6-source04-reconciliation-03/ASSESSMENT.json'),
    'packet05': pin(CAMPAIGN / 'p6-upload-review-05/PENDING_ACTION.json'),
    'packet05_approval': pin(CAMPAIGN / 'p6-upload-review-05/USER_APPROVAL.json'),
    'destination': {
        'host': 'helios.cyfronet.pl', 'ssh_user': 'plgnasqret', 'uid': 105923,
        'directory': '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-04',
        'source_parent': '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-03',
    },
    'effects': {
        'existing_source_files_preserved': 821, 'existing_source_bytes_preserved': 79300068,
        'missing_source_files_created': 504, 'missing_source_bytes_created': 32782277,
        'final_source_files_verified': 1325, 'final_source_bytes_verified': 112082345,
        'metadata_files_created': 5, 'intent_files_created': 1, 'repair_receipts_created': 1,
        'new_source_directories': 29, 'source_directories_finalized_mode_0555': 62,
        'raw_payload_files_uploaded': 3, 'raw_payload_bytes_uploaded': 423394,
        'source_payloads_identical_to_packet05': True,
        'model_weights_uploaded': False, 'archive_uploaded': False,
        'old_source_or_existing_file_overwrites': 0, 'file_deletions': 0,
        'hardlinks_created': 0, 'application_executions': 0, 'model_calls': 0,
        'native_runs': 0, 'scheduler_queries': 0,
    },
    'bounds': {
        'remote_wall_seconds': 120, 'remote_cpu_soft_seconds': 60,
        'remote_cpu_hard_seconds': 75, 'remote_address_space_bytes': 536870912,
        'ssh_wall_seconds': 150, 'maximum_input_bytes': 2097152,
        'maximum_stdout_bytes': 65536, 'maximum_stderr_bytes': 65536,
    },
    'additional_bounds': {
        'ssh_failure_kill_reap_seconds': 5,
        'quota_queries': 1, 'quota_query_wall_seconds': 10, 'quota_child_reap_seconds': 3,
        'quota_output_bytes': 16384, 'maximum_open_directory_fds': 192,
        'maximum_cached_missing_bytes': 32782277,
        'inode_quota_required_with_reserve': 796,
    },
    'integrity': [
        'Reject any source04 namespace other than the exact observed821-file prefix and its32 subdirectories.',
        'Verify existing821 file contents before any write; preserve their identity, mode, size, modification/change timestamps and bytes.',
        'Verify all1325 source03 input files before and after the copy, plus its manifest and copied source maps.',
        'Use authenticated directory descriptors, O_NOFOLLOW and exclusive creates; reject unlisted paths, symlinks, hardlinks and changed owners.',
        'Create only504 missing files, then independently hash all1325 source04 files and verify full namespace.',
        'Create final metadata and a new repair receipt only after integrity checks; keep original stage255 evidence unchanged.',
        'Both local attempt-01 directory and remote repair-attempt-01.json are one-use guards, retained after any failure.',
    ],
    'allocations': 0, 'automatic_retry': False,
    'repeat_or_resume_experiments': False, 'new_training': False,
    'runtime_or_model_or_theorem_or_search_limits_changed': False,
    'completion_within_limit_guaranteed': False,
    'failure_behavior': 'Stop, retain any new partial evidence and reconcile read-only. Do not rerun, delete/recycle guards, allocate jobs, or claim success.',
    'execution_requires_explicit_single_repair_selection': True,
    'specific_repair_approval_record': None,
}
with (HERE / 'REPAIR_REVIEW.json').open('x') as file:
    json.dump(review, file, indent=2, sort_keys=True)
    file.write('\n')
print(json.dumps(pin(HERE / 'REPAIR_REVIEW.json')), flush=True)
