#!/usr/bin/env python3
"""Independently replay the actual terminal DEV checkpoint prefix, read-only.

No completed run or reservation is fabricated. The real released job ledger,
terminal collection, approval and checkpoint header provide their separate
bindings. Original check_request, origin binding and verify_checkpoint remain
unchanged. Missing rows, inflight work and transaction debris are never fixed.
The reviewed full-run verifier02 is imported only for unchanged utilities;
its worker, supervisor entrypoint and completed-run wrapper are never called.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import sys
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
HELPER = ARCHIVE / 'verify-diagnostic-prefix-local-01.py'
BASE = ARCHIVE / 'verify-diagnostic-local-02.py'
BASE_SHA = '7df14454b45ffd8b85d8d2ed4903fd968c0decc642b4b9e35f7255c6fa8bd155'
COLLECTORS = {
    'collect-diagnostic-checkpoint-02.py': 'b464e029b9475aaf33f1df1c721464985b462da210a113d92539a4145ed35582',
    'collect-diagnostic-checkpoint-remote-02.py': 'c36be7646549d0e5feba6dbc0a27bf01d6dc70c536ab5dc24f8ead8b17ad563f',
}
JOB = '21453693'
APPROVAL = '10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e'
EVALUATION = '9c4fe30f658558410bea892ae201529e2114d7959c54a5257ed56e2547bc9c88'
PLAN = '82f8b72179b9decb989622868af28cc6435d0d8838c16652d236c29be8ce791c'
REMOTE = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-diagnostic-v1'
PROFILE = 'peano-hydra-frontier-diagnostic-v1'
SCHEMA = 'peano-hydra-diagnostic-local-prefix-verification-v1'
OWNER_SCHEMA = 'peano-hydra-diagnostic-local-prefix-verification-owner-v1'
COLLECTION_SCHEMA = 'peano-hydra-diagnostic-checkpoint-collection-v1'
INDEX_SCHEMA = 'peano-hydra-diagnostic-checkpoint-collection-index-v1'
TERMINAL = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def base_module():
    require(BASE == BASE.resolve(strict=True) and BASE.stat().st_nlink == 1
        and BASE.stat().st_size <= 65536 and hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA,
        'reviewed verifier02 utility bytes changed')
    spec = importlib.util.spec_from_file_location('_retained_diagnostic_verifier02_utilities', BASE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check_collection(base, directory, expected_sha):
    """Raw-byte collection binding; the original API later checks every row."""
    receipt, receipt_raw = base.read_json(directory / 'collection-receipt.json', expected_sha)
    require(receipt['schema'] == COLLECTION_SCHEMA and receipt['status'] == 'collected-not-proof-verified'
        and receipt['job_id'] == JOB and receipt['approval_sha256'] == APPROVAL
        and receipt['evaluation_request_sha256'] == EVALUATION,
        'exact terminal checkpoint collection required')
    for name, expected in COLLECTORS.items():
        require(base.SHA.fullmatch(expected) and base.fingerprint(ARCHIVE / name)[0]['sha256'] == expected,
                'pinned checkpoint collector changed or is not finalized')
    require(receipt['local_helper_sha256'] == COLLECTORS['collect-diagnostic-checkpoint-02.py']
        and receipt['remote_helper_sha256'] == COLLECTORS['collect-diagnostic-checkpoint-remote-02.py'],
        'collection was not produced by the pinned bounded reader')
    index, index_raw = base.read_json(directory / 'collection-index.json', receipt['index']['sha256'])
    require(len(index_raw) == receipt['index']['bytes'] and index['schema'] == INDEX_SCHEMA
        and index['checkpoint_root_present'] is True and index['checkpoint_all_actual_entries_collected'] is True
        and index['checkpoint_original_lock_collected'] is True and index['checkpoint_debris_filtered'] is False
        and index['checkpoint_files_modified'] is False and index['proofs_independently_verified'] is False
        and index['read_only'] is True and index['automatic_retry'] is False,
            'checkpoint collection index identity changed')
    binding = index['binding']
    require(binding == receipt['binding'] and binding['job_id'] == JOB
        and binding['approval_sha256'] == APPROVAL and binding['evaluation_request_sha256'] == EVALUATION
        and binding['source_commit'] == base.EXECUTION_COMMIT
        and binding['ledger_events'] == 6 and binding['reserved_gpu_seconds'] == 900,
        'collection bound another job/source/approval')
    require(index['accounting'] == receipt['accounting'], 'terminal accounting snapshots differ')
    accounting = index['accounting']
    row = accounting['top_row']
    require(accounting['returncode'] == 0 and accounting['state'].split()[0] in TERMINAL
        and len(row) == 13 and row[:2] == [JOB, PROFILE + '-evaluate']
        and row[2] == accounting['state'] and row[3] == accounting['exit_code']
        and row[5] == '15' and row[7] == '64G' and row[9] == REMOTE
        and row[10:] == ['plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret'],
        'collection lacks the actual terminal approved-job accounting')
    files = index['files']
    require(type(files) is dict and len(files) <= 140 and files == receipt['files']
        and 0 <= index['total_file_bytes'] <= 64 * 1024**2,
        'checkpoint collection file inventory/byte reservation changed')
    total = 0
    for name, descriptor in files.items():
        require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_.\-/]{1,1024}', name)
            and all(part not in ('', '.', '..') for part in name.split('/')), 'unsafe collected input path')
        observed, _ = base.fingerprint(directory / name, maximum=64 * 1024**2)
        require(observed == {key: descriptor[key] for key in ('bytes', 'sha256')}, 'collected input bytes changed')
        total += observed['bytes']
        require(total <= 64 * 1024**2, 'checkpoint input aggregate byte cap')
    require(total == index['total_file_bytes'], 'collection total byte count changed')
    for name in ('ledger.jsonl', 'approval.json', 'resource-request.json', 'evaluation-request.json',
                 'checkpoint/.lock', 'checkpoint/header.json', 'checkpoint/HEAD.json'):
        require(name in files, 'actual checkpoint/ledger/approval file missing: ' + name)
    require(files['approval.json']['sha256'] == APPROVAL
        and files['resource-request.json']['sha256'] == binding['resource_request_sha256']
        and files['evaluation-request.json']['sha256'] == EVALUATION
        and files['ledger.jsonl']['sha256'] == binding['ledger_sha256'], 'collected raw identity pins differ')
    # No filtering: preserve the exact inventory, including directories/debris.
    # Original EvaluationCheckpoint._inventory will refuse any extra entry.
    inventory = index['checkpoint_entry_inventory']
    require(type(inventory) is dict and len(inventory) <= 132, 'checkpoint inventory entry cap')
    observed_names, pending = set(), [directory / 'checkpoint']
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                require(len(observed_names) < 132 and not entry.is_symlink(), 'checkpoint inventory/link bound')
                path = Path(entry.path)
                require(entry.is_file(follow_symlinks=False) or entry.is_dir(follow_symlinks=False),
                        'special checkpoint entry')
                observed_names.add(str(path.relative_to(directory / 'checkpoint')))
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
    require(observed_names == set(inventory), 'collected checkpoint inventory omitted or added entries')
    return receipt, index, receipt_raw, index_raw


def ledger_join(base, directory, index, launch, source_identity):
    """Validate the real captured released ledger; never mint a reservation."""
    _, raw = base.fingerprint(directory / 'ledger.jsonl', maximum=256 * 1024, retain=True)
    require(hashlib.sha256(raw).hexdigest() == index['binding']['ledger_sha256'], 'released ledger hash changed')
    lines = raw.splitlines(keepends=True)
    require(raw.endswith(b'\n') and len(lines) == 6, 'full one-use released ledger required')
    previous, payloads = '0' * 64, []
    kinds = ('header', 'reserve', 'evaluate-accepted', 'held-validated', 'release-authorized', 'evaluate-released')
    for position, line in enumerate(lines):
        event = launch.decode(line)
        require(set(event) == {'index', 'previous_sha256', 'payload', 'sha256'}
            and type(event['index']) is int and event['index'] == position
            and event['previous_sha256'] == previous and event['sha256'] == launch.digest(
                {key: event[key] for key in ('index', 'previous_sha256', 'payload')})
            and launch.canonical(event) + b'\n' == line and event['payload'].get('kind') == kinds[position],
            'actual released ledger chain/order changed')
        previous = event['sha256']
        payloads.append(event['payload'])
    header, reserve, accepted, held, barrier, released = payloads
    remote_identity = header['identity']
    require(set(remote_identity) == set(source_identity)
        and {key: value for key, value in remote_identity.items() if key != 'synced_at'} ==
            {key: value for key, value in source_identity.items() if key != 'synced_at'}
        and type(remote_identity['synced_at']) is str
        and re.fullmatch(r'[0-9TZ:+-]{1,40}', remote_identity['synced_at'])
        and launch.canonical(header) == launch.canonical(launch._header(remote_identity)),
        'released ledger source/request/reservations changed')
    require(set(reserve) == {'kind', 'reservations', 'created_at'} and reserve['reservations'] == launch.RESERVATIONS
        and type(reserve['created_at']) is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', reserve['created_at'])
        and accepted == {'kind': 'evaluate-accepted', 'job_id': JOB, 'dependency_job_id': None}
        and barrier == {'kind': 'release-authorized', 'jobs': {'evaluate': JOB}}
        and released == {'kind': 'evaluate-released', 'job_id': JOB}
        and set(held) == {'kind', 'snapshots'} and set(held['snapshots']) == {'evaluate'},
        'released job is not the one actual900-second reservation')
    snapshot = held['snapshots']['evaluate']
    require(set(snapshot) == {'raw', 'raw_sha256', 'fields'} and type(snapshot['raw']) is str
        and 0 < len(snapshot['raw'].encode()) <= 65536 and len(snapshot['raw'].strip().splitlines()) == 1
        and snapshot['raw_sha256'] == hashlib.sha256(snapshot['raw'].encode()).hexdigest(), 'held snapshot raw identity')
    keys = {'JobId', 'JobName', 'WorkDir', 'JobState', 'Reason', 'Priority', 'Dependency', 'Requeue',
            'Account', 'Partition', 'TimeLimit', 'NumNodes', 'NumCPUs', 'ReqTRES', 'RunTime'}
    fields = {}
    for match in re.finditer(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)', snapshot['raw']):
        key, value = match.groups()
        if key in keys:
            require(key not in fields, 'duplicate held scheduler field')
            fields[key] = value
    require(set(fields) == keys and fields == snapshot['fields'] and fields['JobId'] == JOB
        and fields['JobName'] == PROFILE + '-evaluate' and fields['WorkDir'] == REMOTE
        and fields['JobState'] == 'PENDING' and fields['Reason'] == 'JobHeldUser' and fields['Priority'] == '0'
        and fields['Dependency'] in ('(null)', '(null)(unfulfilled)') and fields['Requeue'] == '0'
        and fields['Account'] == launch.ACCOUNT and fields['Partition'] == launch.PARTITION
        and fields['TimeLimit'] == '00:15:00' and fields['NumNodes'] in ('1', '1-1')
        and fields['NumCPUs'] == '8' and launch._elapsed_seconds(fields['RunTime']) == 0,
        'held snapshot changed exact job/root/resource/restart scope')
    resources = {}
    for text in fields['ReqTRES'].split(','):
        key, separator, value = text.partition('=')
        require(separator and key and value and key not in resources, 'ambiguous held resources')
        resources[key] = value
    require(resources.get('cpu') == '8' and resources.get('node') == '1'
        and resources.get('gres/gpu') == '1' and resources.get('mem') in ('64G', '65536M', '67108864K')
        and all(value == '1' for key, value in resources.items() if key.startswith('gres/gpu:')),
        'held snapshot changed one-GPU64GiB resources')
    return {'ledger_sha256': index['binding']['ledger_sha256'], 'held_snapshot_sha256': snapshot['raw_sha256'],
            'source_identity': remote_identity, 'actual_job_id': JOB, 'reservation_fabricated': False}


def prefix_metrics(plan, rows, verification):
    slots, goals = plan.proposal['ordered_slots'], plan.goals
    require(len(slots) == 128 and len(goals) == 32 and len(rows) == verification['completed_goal_records'],
            'fixed DEV prefix size differs')
    by_slot = {(slot['role'], slot['max_model_calls'], slot['goal']): row for slot, row in zip(slots, rows)}
    def outcome(row, budget):
        if row is None: return 'missing-unknown'
        if row['kernel_checked']: return 'proof'
        if row['status'] == 'exhausted': return 'exhausted'
        return 'call-limit' if row['model_generate_calls'] == budget else 'unknown'
    lanes, comparisons = [], []
    roles = ('saved-corrected', 'new-frontier')
    for budget in (8, 16):
        for role in roles:
            selected = [by_slot.get((role, budget, goal['name'])) for goal in goals]
            statuses = Counter(outcome(row, budget) for row in selected)
            committed = [row for row in selected if row is not None]
            generation = {name: sum(row['generation'][name] for row in committed) for name in (
                'candidate_sequences_requested', 'candidate_sequences_returned', 'candidate_lines_returned',
                'malformed_sequences_rejected', 'authority_sequences_rejected')}
            native = Counter(item['kind'] for row in committed for item in row['evidence']['search']['diagnostics'])
            calls = sum(row['model_generate_calls'] for row in committed)
            requested = generation['candidate_sequences_requested']
            lanes.append({'role': role, 'max_model_calls': budget, 'planned_goals': 32,
                'committed_goal_records': len(committed), 'all_lane_rows_present': len(committed) == 32,
                'missing_unknown_goal_records': statuses['missing-unknown'],
                'unknown_outcomes_including_missing': statuses['unknown'] + statuses['missing-unknown'],
                'independently_verified_proofs': statuses['proof'],
                'known_unproved_within_budget': statuses['exhausted'] + statuses['call-limit'],
                'outcomes': dict(statuses), 'committed_model_generate_calls': calls,
                'calls_per_verified_proof_in_committed_rows': calls/statuses['proof'] if statuses['proof'] else None,
                'verified_proof_fraction_if_all_lane_rows_present': statuses['proof']/32 if len(committed) == 32 else None,
                'rejected_sequence_fraction_committed': (generation['malformed_sequences_rejected']
                    + generation['authority_sequences_rejected'])/requested if requested else None,
                'generation_for_committed_rows': generation, 'retained_native_diagnostics_by_kind': dict(sorted(native.items())),
                'goal_wall_seconds_sum_committed': sum(row['resources']['goal_wall_seconds'] for row in committed),
                'goal_cpu_seconds_sum_committed': sum(row['resources']['goal_cpu_seconds'] for row in committed),
                'max_reported_process_rss_bytes': max((row['resources']['process_peak_rss_bytes'] for row in committed), default=None),
                'max_goal_cuda_allocated_bytes': max((row['resources']['cuda_peak_allocated_bytes'] for row in committed), default=None)})
        complete = all((role, budget, goal['name']) in by_slot for role in roles for goal in goals)
        item = {'max_model_calls': budget, 'all_64_matched_rows_present': complete,
                'planned_paired_goals': 32, 'comparison_status': 'complete-matched-DEV-rows' if complete else 'incomplete-no-paired-score',
                'gains': None, 'losses': None, 'unknown_pair_goals': None, 'net_gain_among_known_pairs': None}
        if complete:
            gains, losses, unknown, common = [], [], [], []
            for goal in goals:
                name = goal['name']
                old, new = (outcome(by_slot[(role, budget, name)], budget) for role in roles)
                if 'unknown' in (old, new): unknown.append(name)
                elif old == new == 'proof': common.append(name)
                elif old != 'proof' and new == 'proof': gains.append(name)
                elif old == 'proof' and new != 'proof': losses.append(name)
            item.update(gains=gains, losses=losses, unknown_pair_goals=unknown,
                        common_verified_proofs=common, known_paired_goals=32-len(unknown),
                        net_gain_among_known_pairs=len(gains)-len(losses))
        comparisons.append(item)
    return {'lanes': lanes, 'comparisons': comparisons, 'completed_goal_records': len(rows),
        'total_goal_records': 128, 'missing_unknown_goal_records': 128-len(rows),
        'inflight': verification['inflight'], 'inflight_model_generate_calls': verification['inflight_model_generate_calls'],
        'all128_checkpoint_records_verified': verification['verification_complete'],
        'all128_comparison_complete': False, 'complete_run_wrapper_verified': False,
        'rows_removed_or_invented': False, 'partial_pairs_scored': False,
        'native_diagnostics_scope': 'Only retained diagnostics from committed rows; capped at128 per goal.',
        'resource_scope': 'Committed goal resources omit setup/model-loading and unknown inflight work.'}


def worker(request_path, expected_sha):
    base = base_module()
    request, _ = base.read_json(request_path, expected_sha)
    require(set(request) == {'schema', 'supervisor_pid', 'output_directory', 'collection_directory',
        'collection_receipt_sha256', 'evaluation_request_sha256', 'approval_sha256', 'helper_sha256', 'created_at_utc'}
        and request['schema'] == OWNER_SCHEMA and type(request['supervisor_pid']) is int
        and request['supervisor_pid'] == os.getppid(), 'internal prefix worker requires live owner')
    require(sys.flags.isolated and sys.dont_write_bytecode and Path(sys.executable).resolve() == base.PYTHON
        and sys.platform == 'darwin' and sys.version_info >= (3, 11)
        and not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
        'isolated local Python outside allocations required')
    require(request['approval_sha256'] == APPROVAL and request['evaluation_request_sha256'] == EVALUATION
        and base.fingerprint(HELPER)[0]['sha256'] == request['helper_sha256'], 'worker input/helper pins changed')
    output, directory = base.exact_path(request['output_directory']), base.exact_path(request['collection_directory'])
    require(base.exact_path(request_path) == output / 'reservation.json', 'owner reservation location changed')
    base.check_execution()
    diagnostic, launch, evaluation, bridge = base.modules()
    protected = launch.output_protections(extra=(directory, *(path.parent for path in base.LOCAL_MODELS.values())))
    target = output / 'verification.json'
    diagnostic.files.guard_output(target, protected=protected)
    checked = diagnostic.check_request(base.PACKAGE / 'evaluation-request.json', EVALUATION)
    approval, resource_record = launch.validate_metadata(APPROVAL)
    source_identity = launch._identity(approval, resource_record, APPROVAL, local=True)
    diagnostic._resource_join(checked, resource_record)
    receipt, index, receipt_raw, index_raw = check_collection(base, directory, request['collection_receipt_sha256'])
    require(index['binding']['resource_request_sha256'] == approval['request_file_sha256'], 'resource request join differs')
    ledger = ledger_join(base, directory, index, launch, source_identity)
    if 'execution-status.json' in index['files']:
        status, _ = base.read_json(directory / 'execution-status.json', index['files']['execution-status.json']['sha256'])
        require(status['schema'] == diagnostic.RUN_SCHEMA and status['request_file_sha256'] == checked.raw_sha256
            and status['status'] == 'interrupted-or-failed-prefix-retained' and status['uncompleted_outcomes'] == 'unknown'
            and status['automatic_retry'] is False and status['resume'] is False
            and all(status[key] is False for key in diagnostic.CLAIMS), 'actual interrupted-run status changed')
    references = base.local_references(checked, evaluation, bridge)
    descriptor = checked.record['evaluation_plan']
    plan = evaluation.bind_evaluation(diagnostic._descriptor(descriptor),
        expected_evaluation_plan_sha256=descriptor['sha256'],
        baseline=references[evaluation.ROLES[0]], candidate=references[evaluation.ROLES[1]])
    require(plan.to_dict()['plan_sha256'] == PLAN and plan.proposal['cohort'] == 'review-candidate-dev',
            'portable bound plan differs from exact approved32-goal DEV experiment')
    authorization_sha = diagnostic.digest(diagnostic._authorization(plan))
    # The original implementation validates ALL committed metadata before
    # starting its existing per-positive-proof bounded original-kernel replay.
    verification = evaluation.verify_checkpoint(plan, directory / 'checkpoint',
        expected_authorization_sha256=authorization_sha, replay=True)
    require(verification['status'] == 'native-prefix-verified' and verification['proof_replay_performed'] is True
        and verification['plan_sha256'] == PLAN, 'original prefix replay did not complete')
    rows = []
    for ordinal in range(1, verification['completed_goal_records'] + 1):
        name = f'checkpoint/{ordinal:06d}.goal.json'
        record, _ = base.read_json(directory / name, index['files'][name]['sha256'])
        rows.append(record['row'])
    metrics = prefix_metrics(plan, rows, verification)
    require(diagnostic.check_request(checked.path, checked.raw_sha256).record == checked.record,
            'original diagnostic admission changed during replay')
    final_approval, final_resource = launch.validate_metadata(APPROVAL)
    require(final_approval == approval and final_resource == resource_record
        and launch._identity(final_approval, final_resource, APPROVAL, local=True) == source_identity,
        'approved source/resource changed during replay')
    after = check_collection(base, directory, request['collection_receipt_sha256'])
    require(after == (receipt, index, receipt_raw, index_raw), 'actual checkpoint collection changed during replay')
    evaluation.paired._model_free()
    result = {'schema': SCHEMA, 'status': 'committed-prefix-proofs-independently-replayed',
        'collection_receipt_sha256': request['collection_receipt_sha256'], 'job_id': JOB,
        'evaluation_request_sha256': EVALUATION, 'resource_approval_sha256': APPROVAL,
        'portable_plan_sha256': PLAN, 'authorization_sha256': authorization_sha,
        'source_identity': source_identity, 'actual_released_ledger': ledger,
        'origin_references': {role: ref.to_dict() for role, ref in references.items()},
        'explicit_local_locations': {role: ref.request.locations() for role, ref in references.items()},
        'verification': verification, 'metrics': metrics, 'claim_boundary': evaluation.CLAIM,
        'full_comparison_verification_complete': False, 'complete_run_wrapper_verified': False,
        'current_model_artifact_bytes_rechecked': True, 'new_original_origin_authentication_performed': False,
        'model_outputs_regenerated': False, 'historical_gpu_inference_attested': False,
        'completed_run_or_reservation_fabricated': False, 'original_proof_worker_limits': base.PROOF_LIMITS,
        'whole_call_completion_requires': 'owner-result.json status prefix-verified-within-whole-call-envelope',
        **diagnostic.CLAIMS}
    diagnostic.files.guard_output(target, protected=protected)
    base.write_new(target, result)
    print(json.dumps({'status': result['status'], 'completed_goal_records': len(rows),
        'model_loaded': False, 'whole_call_receipt_required': True}, sort_keys=True))


def supervise(args):
    base = base_module()
    require(sys.flags.isolated and sys.dont_write_bytecode and Path(sys.executable).resolve() == base.PYTHON
        and sys.platform == 'darwin' and sys.version_info >= (3, 11)
        and not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
        'fixed isolated local Python outside allocations required')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 181))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    for name in ('collection_receipt_sha256', 'evaluation_request_sha256', 'approval_sha256', 'helper_sha256'):
        require(type(getattr(args, name)) is str and base.SHA.fullmatch(getattr(args, name)), 'external raw pin: ' + name)
    require(args.approval_sha256 == APPROVAL and args.evaluation_request_sha256 == EVALUATION
        and base.fingerprint(HELPER)[0]['sha256'] == args.helper_sha256
        and base.fingerprint(base.SUPERVISOR)[0]['sha256'] == base.SUPERVISOR_SHA, 'fixed helper/approval/evaluation changed')
    directory, output = base.exact_path(args.collection_directory), base.exact_path(args.output_directory, exists=False)
    require(directory.parent == ARCHIVE and re.fullmatch(r'diagnostic-checkpoint-collected-[0-9]{2}', directory.name),
            'actual checkpoint collection must use its archive directory')
    require(output.parent == ARCHIVE and re.fullmatch(r'diagnostic-prefix-verification-[0-9]{2}', output.name)
        and not os.path.lexists(output), 'fresh separate prefix verification archive required')
    # No native proof or model import here; fail closed on missing collection.
    check_collection(base, directory, args.collection_receipt_sha256)
    before = base.check_execution(deadline=STARTED + 300)
    spec = importlib.util.spec_from_file_location('_retained_prefix_supervisor_v2', base.SUPERVISOR)
    supervisor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = supervisor
    spec.loader.exec_module(supervisor)
    require(supervisor.HELPER == base.SUPERVISOR and supervisor.Limits().__dict__ == base.WHOLE_LIMITS,
            'retained supervisor envelope changed')
    os.mkdir(output, 0o700)
    reservation = {'schema': OWNER_SCHEMA, 'supervisor_pid': os.getpid(), 'output_directory': str(output),
        'collection_directory': str(directory), 'collection_receipt_sha256': args.collection_receipt_sha256,
        'evaluation_request_sha256': EVALUATION, 'approval_sha256': APPROVAL, 'helper_sha256': args.helper_sha256,
        'created_at_utc': datetime.now(timezone.utc).isoformat()}
    pin = base.write_new(output / 'reservation.json', reservation)
    command = (str(base.PYTHON), '-I', '-B', str(HELPER), '--worker', str(output / 'reservation.json'), pin['sha256'])
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    prefix_cpu = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    process = supervisor.supervise(command, cwd=base.EXECUTION, directory=output, limits=supervisor.Limits(),
        metadata={'purpose': 'independent local replay of actual terminal DEV checkpoint prefix',
            'reservation_sha256': pin['sha256'], 'helper_sha256': args.helper_sha256,
            'supervisor_sha256': base.SUPERVISOR_SHA, 'production_source_changed': False},
        started=STARTED, deadline=STARTED + 300)
    returned_own, returned_children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    returned_cpu = returned_own.ru_utime + returned_own.ru_stime + returned_children.ru_utime + returned_children.ru_stime
    process_pin = base.write_new(output / 'supervision.json', process)
    failure = verification_pin = verification = None
    try:
        require(process['status'] == 'process-completed-with-open-gates' and process['remaining_live_owned_pids'] == [],
                'prefix verification did not finish within original supervision')
        require(base.check_execution(deadline=STARTED + 300) == before
            and base.fingerprint(HELPER)[0]['sha256'] == args.helper_sha256
            and base.fingerprint(BASE)[0]['sha256'] == BASE_SHA
            and base.fingerprint(base.SUPERVISOR)[0]['sha256'] == base.SUPERVISOR_SHA, 'frozen code changed')
        verification_pin, raw = base.fingerprint(output / 'verification.json', maximum=32 * 1024**2, retain=True)
        verification = json.loads(raw)
        require(verification['schema'] == SCHEMA and verification['status'] == 'committed-prefix-proofs-independently-replayed'
            and verification['collection_receipt_sha256'] == args.collection_receipt_sha256
            and verification['evaluation_request_sha256'] == EVALUATION and verification['job_id'] == JOB,
            'worker did not verify the exact real checkpoint collection')
        require(time.monotonic() - STARTED <= 300, 'whole-call wall boundary after prefix replay')
    except (ValueError, OSError, KeyError, TypeError) as error:
        failure = type(error).__name__ + ': ' + ' '.join(str(error).split())[:2048]
    retained = supervisor.retained_bytes(output)
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    cumulative = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    accounted = base.whole_cpu_lower_bound(prefix_cpu, process['accounted_cpu_lower_bound_seconds'], returned_cpu, cumulative)
    peak = max(int(own.ru_maxrss), process['peak_sampled_combined_rss_bytes'])
    if accounted >= 180: failure = failure or 'whole-call accounted CPU lower bound reached180seconds'
    if peak >= base.WHOLE_LIMITS['rss_bytes']: failure = failure or 'whole-call observed RSS boundary reached'
    if retained >= base.WHOLE_LIMITS['output_bytes']: failure = failure or 'whole-call retained output boundary reached'
    result = {'schema': OWNER_SCHEMA, 'status': 'prefix-verified-within-whole-call-envelope' if failure is None else 'incomplete',
        'error': failure, 'job_id': JOB, 'collection_receipt_sha256': args.collection_receipt_sha256,
        'evaluation_request_sha256': EVALUATION, 'resource_approval_sha256': APPROVAL,
        'helper_sha256': args.helper_sha256, 'utility_helper_sha256': BASE_SHA, 'supervisor_sha256': base.SUPERVISOR_SHA,
        'original_supervisor_receipt': process_pin, 'verification_file': verification_pin,
        'execution_source': before, 'whole_limits': base.WHOLE_LIMITS, 'original_proof_worker_limits': base.PROOF_LIMITS,
        'wall_seconds': time.monotonic() - STARTED, 'accounted_cpu_lower_bound_seconds': accounted,
        'post_supervision_accounted_cpu_seconds': cumulative-returned_cpu, 'parent_reported_peak_rss_bytes': int(own.ru_maxrss),
        'whole_call_peak_observed_rss_bytes': peak, 'retained_output_bytes_before_owner_result': retained,
        'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
        'remaining_live_owned_pids': process['remaining_live_owned_pids'], 'original_resource_caps_changed': False,
        'completed_goal_records': None if verification is None else verification['verification']['completed_goal_records'],
        'all128_checkpoint_records_verified': False if verification is None else verification['verification']['verification_complete'],
        'full_comparison_verification_complete': False, 'complete_run_wrapper_verified': False,
        'gpu_job_submitted': False, 'model_loaded': False, 'network_contacted': False,
        'pilot_acceptance_eligible': False, 'benchmark_acceptance_eligible': False, 'self_training_readiness_eligible': False,
        'automatic_retry': False, 'resume': False}
    if result['wall_seconds'] > 300:
        result['error'] = failure = failure or 'whole-call wall boundary reached during final accounting'
        result['status'] = 'incomplete'
    require(retained + len(base.canonical(result)) + 1 <= base.WHOLE_LIMITS['output_bytes'], 'owner receipt exceeds retained cap')
    base.write_new(output / 'owner-result.json', result)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if failure is None else 2


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        worker(Path(sys.argv[2]), sys.argv[3])
        return 0
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--collection-directory', required=True, type=Path)
    parser.add_argument('--collection-receipt-sha256', required=True)
    parser.add_argument('--evaluation-request-sha256', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--output-directory', required=True, type=Path)
    return supervise(parser.parse_args())


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print('local-diagnostic-prefix-verification: ' + ' '.join(str(error).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
