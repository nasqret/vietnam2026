#!/usr/bin/env python3
"""Verify a completed diagnostic locally using explicit portable model origins.

This archive-only caller does not change the frozen diagnostic deployment.
It never creates a CheckedRequest, alters a bound plan, patches a validator,
loads a model framework, authenticates a new origin, contacts Helios, or runs
inference. A real completed run and its externally supplied raw pins are
required. Metadata, approvals and the saved job are checked before local
artifact binding and before unchanged independent positive-proof replay.

The existing frozen process-tree supervisor is reused with its unchanged
300 wall / 180 sampled aggregate CPU / 2 GiB / 64 MiB envelope. Its original
receipt and measurement limitations are retained, not relabelled. Each
original proof worker still has 30 CPU / 45 wall / 1 GiB limits. The final
whole-call receipt, not a worker file alone, determines completion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import resource
import stat
import sys
import time

STARTED = time.monotonic()
WORKSPACE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = WORKSPACE / 'artifacts/hydra-model-test-2026-08-30'
HELPER = ARCHIVE / 'verify-diagnostic-local-02.py'
EXECUTION = WORKSPACE / '_deploy/hydra-model-test-execution-20260830'
EXECUTION_COMMIT = '612d1ea9e4905dfe2af104696924a19bc5883752'
FREEZE = EXECUTION / '_deploy/hydra-diagnostic-execution-freeze.json'
FREEZE_SHA = '25ce03ef653c03440f163a7bdefdf41bfd90056f140a9128cfba2781aba0cff1'
SUPERVISOR = WORKSPACE / 'artifacts/hydra-advancement-2026-08-30/run-v28-hotspots-supervised-v2.py'
SUPERVISOR_SHA = '1be34563858e2deba8e23ea47dc9f5966ffe092c3e0d23fe80a81a411b94af1c'
PYTHON = Path('/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
PACKAGE = EXECUTION / '_deploy/hydra-frontier-diagnostic-v1'
LOCAL_MODELS = {
    'saved-corrected': WORKSPACE / '_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/model/manifest.json',
    'new-frontier': ARCHIVE / 'candidate-model/manifest.json',
}
SCHEMA = 'peano-hydra-diagnostic-portable-local-verification-v1'
OWNER_SCHEMA = 'peano-hydra-diagnostic-portable-local-verification-owner-v1'
MAX_METADATA = 8 * 1024**2
WHOLE_LIMITS = {'wall_seconds': 300, 'cpu_seconds': 180,
                'rss_bytes': 2 * 1024**3, 'output_bytes': 64 * 1024**2}
PROOF_LIMITS = {'wall_seconds': 45, 'cpu_seconds': 30,
                'rss_bytes': 1024**3, 'output_bytes': 1024**2}
SHA = re.compile(r'[0-9a-f]{64}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def exact_path(path, *, exists=True):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and path == path.resolve(strict=exists), 'canonical nonsymlink absolute path required')
    return path


def fingerprint(path, *, maximum=MAX_METADATA, retain=False, deadline=None):
    path = exact_path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 <= before.st_size <= maximum, 'bounded regular single-link file required')
        digest, raw, size = hashlib.sha256(), bytearray(), 0
        while block := stream.read(65536):
            require(deadline is None or time.monotonic() < deadline, 'whole-call deadline during byte checks')
            size += len(block)
            require(size <= maximum, 'file grew beyond its byte bound')
            digest.update(block)
            if retain:
                raw.extend(block)
        after, current = os.fstat(stream.fileno()), path.lstat()
        signature = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size,
                               x.st_mtime_ns, x.st_ctime_ns, x.st_nlink)
        require(size == before.st_size and signature(before) == signature(after) == signature(current),
                'file changed during fingerprinting')
    return {'bytes': size, 'sha256': digest.hexdigest()}, bytes(raw)


def read_json(path, expected, *, maximum=MAX_METADATA):
    require(type(expected) is str and SHA.fullmatch(expected), 'external raw SHA256 required')
    identity, raw = fingerprint(path, maximum=maximum, retain=True)
    require(identity['sha256'] == expected, 'externally pinned metadata changed')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite JSON number: ' + value)
    def finite(value):
        number = float(value)
        require(math.isfinite(number), 'nonfinite JSON float')
        return number
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad, parse_float=finite)
    require(type(value) is dict, 'one JSON object required')
    return value, raw


def write_new(path, value):
    raw = canonical(value) + b'\n'
    require(len(raw) <= 32 * 1024**2, 'verification metadata exceeds its file bound')
    path = exact_path(path, exists=False)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def whole_cpu_lower_bound(prefix_cpu, supervised_cpu, returned_cpu, current_cpu):
    """Include measured parent postchecks even when sampled descendants dominate."""
    require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0
                for value in (prefix_cpu, supervised_cpu, returned_cpu, current_cpu))
            and current_cpu >= returned_cpu, 'invalid cumulative CPU observations')
    tail_cpu = current_cpu - returned_cpu
    return max(current_cpu, prefix_cpu + supervised_cpu + tail_cpu)


def check_execution(*, deadline=None):
    freeze, _ = read_json(FREEZE, FREEZE_SHA)
    require(freeze['git_commit'] == EXECUTION_COMMIT and freeze['snapshot_root'] == str(EXECUTION)
            and freeze['snapshot_clean'] is True and freeze['file_count'] == 877,
            'wrong frozen diagnostic execution snapshot')
    inventory = freeze['files']
    require(type(inventory) is dict and len(inventory) == 877
            and sum(item['bytes'] for item in inventory.values()) <= 128 * 1024**2,
            'frozen source inventory exceeds its unchanged envelope')
    for name, expected in inventory.items():
        relative = PurePosixPath(name)
        require(type(name) is str and not relative.is_absolute()
                and all(part not in ('', '.', '..') for part in relative.parts), 'unsafe source path')
        observed, _ = fingerprint(EXECUTION / name, maximum=64 * 1024**2, deadline=deadline)
        require(observed == {key: expected[key] for key in ('bytes', 'sha256')}, 'frozen source bytes changed')
    return {'source_commit': EXECUTION_COMMIT, 'freeze_sha256': FREEZE_SHA,
            'source_files': len(inventory), 'source_bytes': sum(item['bytes'] for item in inventory.values())}


def modules():
    sys.dont_write_bytecode = True
    sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(EXECUTION), str(EXECUTION / 'peano-lab/py')]
    from training.peano_hydra import frontier_diagnostic_run as diagnostic
    from training.peano_hydra import frontier_diagnostic_launch as launch
    from training.peano_hydra import scaling_evaluation as evaluation
    from training.peano_hydra import origin_bridge as bridge
    require(all(module.ROOT == EXECUTION for module in (diagnostic, launch, evaluation, bridge)),
            'verification imported another execution root')
    evaluation.paired._model_free()
    require(evaluation.capacity.REPLAY_LIMITS.to_dict() == PROOF_LIMITS, 'original proof-worker limits changed')
    return diagnostic, launch, evaluation, bridge


def wrapper_metadata(diagnostic, launch, checked, request):
    """Preserve the complete original verify_run pre-bind wrapper checks."""
    directory = exact_path(request['run_directory'])
    raw = diagnostic.bridge._read(directory / 'run.json', diagnostic.MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == request['run_sha256'], 'saved diagnostic run raw SHA differs')
    record = diagnostic.bridge._decode(raw, diagnostic.MAX_METADATA, 'saved diagnostic run')
    fields = {'schema', 'status', 'request_file_sha256', 'resource_approval_file_sha256',
        'resource_request_file_sha256', 'reservation', 'candidate_adapter_manifest_sha256',
        'origin_receipt_sha256', 'report', 'caller_sources', 'whole_allocation_soft_deadline_seconds',
        'observed_wall_seconds', 'limits', 'soft_stop_boundary',
        'positive_proof_independent_verification_complete', 'claim_boundary', 'run_sha256', *diagnostic.CLAIMS}
    diagnostic.bridge._keys(record, fields, 'saved diagnostic run manifest')
    require(record['schema'] == diagnostic.RUN_SCHEMA and record['status'] == 'complete-pending-independent-replay'
        and record['request_file_sha256'] == checked.raw_sha256 and record['limits'] == diagnostic.LIMITS
        and record['caller_sources'] == checked.record['caller_sources'] == diagnostic.caller_sources()
        and record['run_sha256'] == diagnostic.digest({k: v for k, v in record.items() if k != 'run_sha256'})
        and record['candidate_adapter_manifest_sha256'] == checked.candidate.request.adapter_manifest_sha256
        and record['origin_receipt_sha256'] == {role: ref.receipt_sha256 for role, ref in zip(
            diagnostic.evaluation.ROLES, (checked.baseline, checked.candidate), strict=True)},
        'saved diagnostic identity changed')
    require(all(record[key] is False for key in (*diagnostic.CLAIMS, 'positive_proof_independent_verification_complete'))
        and record['claim_boundary'] == diagnostic.evaluation.CLAIM
        and record['soft_stop_boundary'] == 'before model loads and between goals; scheduler hard limit remains 900 seconds'
        and type(record['observed_wall_seconds']) in (int, float) and math.isfinite(record['observed_wall_seconds'])
        and 0 < record['observed_wall_seconds'] <= 900
        and type(record['whole_allocation_soft_deadline_seconds']) in (int, float)
        and math.isfinite(record['whole_allocation_soft_deadline_seconds'])
        and 0 < record['whole_allocation_soft_deadline_seconds'] <= 720,
        'saved diagnostic changed its allocation bounds or claim boundary')
    require(record['resource_approval_file_sha256'] == request['approval_sha256'],
            'saved run differs from the separately supplied resource approval pin')
    approval, resource_record = launch.validate_metadata(request['approval_sha256'])
    identity = launch._identity(approval, resource_record, request['approval_sha256'], local=True)
    require(identity['source_commit'] == EXECUTION_COMMIT, 'saved approval uses another execution commit')
    diagnostic._resource_join(checked, resource_record)
    diagnostic._saved_reservation(checked, record, approval, resource_record)
    return record, raw, identity


def local_references(checked, evaluation, bridge):
    """Explicit supported relocation; retain exact portable requests and receipt SHAs."""
    references = {}
    for role, original in zip(evaluation.ROLES, (checked.baseline, checked.candidate), strict=True):
        locations = original.request.locations()
        locations['adapter_manifest'] = str(exact_path(LOCAL_MODELS[role]))
        request = bridge._request(original.request.to_dict(), locations)
        relocated = evaluation.OriginReference(request, original.receipt_path, original.receipt_sha256)
        require(relocated.to_dict() == original.to_dict(), 'local relocation changed portable origin identity')
        references[role] = relocated
    return references


def worker(request_path, expected_sha):
    request, _ = read_json(request_path, expected_sha)
    fields = {'schema', 'supervisor_pid', 'output_directory', 'run_directory', 'run_sha256',
              'evaluation_request_sha256', 'approval_sha256', 'helper_sha256', 'created_at_utc'}
    require(set(request) == fields and request['schema'] == OWNER_SCHEMA
            and type(request['supervisor_pid']) is int and request['supervisor_pid'] == os.getppid(),
            'internal worker requires its live owner reservation')
    require(sys.flags.isolated and sys.dont_write_bytecode and Path(sys.executable).resolve() == PYTHON
            and sys.version_info >= (3, 11) and sys.platform == 'darwin'
            and not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
            'local isolated Python3.11 verification outside any allocation is required')
    require(fingerprint(HELPER)[0]['sha256'] == request['helper_sha256'], 'local verification helper changed')
    output = exact_path(request['output_directory'])
    require(exact_path(request_path) == output / 'reservation.json', 'worker reservation path changed')
    check_execution()
    diagnostic, launch, evaluation, bridge = modules()
    target = output / 'verification.json'
    protected = launch.output_protections(extra=(Path(request['run_directory']),
        *(path.parent for path in LOCAL_MODELS.values())))
    diagnostic.files.guard_output(target, protected=protected)
    checked = diagnostic.check_request(PACKAGE / 'evaluation-request.json', request['evaluation_request_sha256'])
    record, raw_run, source_identity = wrapper_metadata(diagnostic, launch, checked, request)
    references = local_references(checked, evaluation, bridge)
    descriptor = checked.record['evaluation_plan']
    plan = evaluation.bind_evaluation(diagnostic._descriptor(descriptor),
        expected_evaluation_plan_sha256=descriptor['sha256'],
        baseline=references[evaluation.ROLES[0]], candidate=references[evaluation.ROLES[1]])
    report_path, report = diagnostic._run_file(Path(request['run_directory']), record['report'], evaluation.MAX_REPORT_BYTES)
    require(plan.to_dict() == report['plan'], 'portable local plan differs from the actual GPU report')
    authorization_sha = diagnostic.digest(diagnostic._authorization(plan))
    evaluation.verify_result(plan, report, expected_authorization_sha256=authorization_sha, replay=False)
    verification = evaluation.verify_result(plan, report, expected_authorization_sha256=authorization_sha, replay=True)
    require(diagnostic.check_request(checked.path, checked.raw_sha256).record == checked.record,
            'diagnostic admission changed during native verification')
    final_record, final_raw, final_identity = wrapper_metadata(diagnostic, launch, checked, request)
    require(final_raw == raw_run and final_record == record and final_identity == source_identity,
            'run, source or approval changed during independent verification')
    _, report_after = diagnostic._run_file(Path(request['run_directory']), record['report'], evaluation.MAX_REPORT_BYTES)
    require(report_after == report, 'saved report changed during independent verification')
    evaluation.paired._model_free()
    result = {'schema': SCHEMA, 'status': 'diagnostic-proofs-independently-replayed',
        'run_file_sha256': request['run_sha256'], 'request_file_sha256': checked.raw_sha256,
        'resource_approval_file_sha256': request['approval_sha256'], 'source_identity': source_identity,
        'portable_plan_sha256': plan.to_dict()['plan_sha256'], 'authorization_sha256': authorization_sha,
        'origin_references': {role: ref.to_dict() for role, ref in references.items()},
        'explicit_local_locations': {role: ref.request.locations() for role, ref in references.items()},
        'original_remote_declarations_changed': False, 'production_source_changed': False,
        'new_original_origin_authentication_performed': False, 'current_model_artifact_bytes_rechecked': True,
        'verification': verification, 'metrics': report['metrics'], 'model_outputs_regenerated': False,
        'historical_gpu_inference_attested': False, 'claim_boundary': evaluation.CLAIM,
        'whole_call_completion_requires': 'owner-result.json status verified-within-whole-call-envelope',
        'original_proof_worker_limits': PROOF_LIMITS, **diagnostic.CLAIMS}
    diagnostic.files.guard_output(target, protected=protected)
    write_new(target, result)
    print(json.dumps({'status': result['status'], 'plan_sha256': result['portable_plan_sha256'],
                      'model_loaded': False, 'whole_call_receipt_required': True}, sort_keys=True))


def supervise(args):
    require(sys.flags.isolated and sys.dont_write_bytecode and Path(sys.executable).resolve() == PYTHON
            and sys.platform == 'darwin' and sys.version_info >= (3, 11), 'use the fixed isolated local Python3.11')
    require(not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
            'verification must be local and outside an allocation or inherited loader override')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 181))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    for name in ('run_sha256', 'evaluation_request_sha256', 'approval_sha256', 'helper_sha256'):
        require(type(getattr(args, name)) is str and SHA.fullmatch(getattr(args, name)), 'external raw pin missing: ' + name)
    require(fingerprint(HELPER)[0]['sha256'] == args.helper_sha256, 'local verification helper differs from external pin')
    require(fingerprint(SUPERVISOR)[0]['sha256'] == SUPERVISOR_SHA, 'retained process-tree supervisor changed')
    run_directory, output = exact_path(args.run_directory), exact_path(args.output_directory, exists=False)
    require(run_directory != ARCHIVE and ARCHIVE in run_directory.parents, 'saved run must be in this local archive')
    require(output.parent == ARCHIVE and re.fullmatch(r'diagnostic-local-verification-[0-9]{2}', output.name)
            and not os.path.lexists(output) and output not in run_directory.parents and run_directory not in output.parents,
            'whole-call output must be a fresh dedicated archive, separate from saved inputs')
    # Missing/completely uncollected runs fail before reserving an attempt.
    read_json(run_directory / 'run.json', args.run_sha256, maximum=4 * 1024**2)
    before = check_execution(deadline=STARTED + 300)
    spec = importlib.util.spec_from_file_location('_hydra_retained_local_supervisor_v2', SUPERVISOR)
    supervisor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = supervisor
    spec.loader.exec_module(supervisor)
    require(supervisor.HELPER == SUPERVISOR and supervisor.Limits().__dict__ == WHOLE_LIMITS,
            'retained supervisor helper or resource envelope changed')
    os.mkdir(output, 0o700)
    reservation = {'schema': OWNER_SCHEMA, 'supervisor_pid': os.getpid(),
        'output_directory': str(output), 'run_directory': str(run_directory), 'run_sha256': args.run_sha256,
        'evaluation_request_sha256': args.evaluation_request_sha256, 'approval_sha256': args.approval_sha256,
        'helper_sha256': args.helper_sha256, 'created_at_utc': datetime.now(timezone.utc).isoformat()}
    pin = write_new(output / 'reservation.json', reservation)
    command = (str(PYTHON), '-I', '-B', str(HELPER), '--worker', str(output / 'reservation.json'), pin['sha256'])
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    prefix_cpu = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    process = supervisor.supervise(command, cwd=EXECUTION, directory=output, limits=supervisor.Limits(),
        metadata={'purpose': 'independent local verification of an already completed DEV diagnostic',
                  'reservation_sha256': pin['sha256'], 'helper_sha256': args.helper_sha256,
                  'supervisor_sha256': SUPERVISOR_SHA, 'production_source_changed': False},
        started=STARTED, deadline=STARTED + 300)
    returned_own = resource.getrusage(resource.RUSAGE_SELF)
    returned_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    returned_cpu = (returned_own.ru_utime + returned_own.ru_stime
                    + returned_children.ru_utime + returned_children.ru_stime)
    process_pin = write_new(output / 'supervision.json', process)
    failure = None
    verification_pin = None
    try:
        require(process['status'] == 'process-completed-with-open-gates', 'local verification did not finish under supervision')
        require(check_execution(deadline=STARTED + 300) == before, 'frozen execution changed')
        require(fingerprint(HELPER)[0]['sha256'] == args.helper_sha256
                and fingerprint(SUPERVISOR)[0]['sha256'] == SUPERVISOR_SHA, 'local orchestration code changed')
        verification_pin, verification_raw = fingerprint(output / 'verification.json', maximum=32 * 1024**2, retain=True)
        verification = json.loads(verification_raw)
        require(verification['schema'] == SCHEMA and verification['status'] == 'diagnostic-proofs-independently-replayed'
                and verification['run_file_sha256'] == args.run_sha256
                and verification['request_file_sha256'] == args.evaluation_request_sha256,
                'worker did not produce the exact requested verification')
        require(time.monotonic() - STARTED <= 300, 'whole-call wall boundary exceeded after verification')
    except (ValueError, OSError, KeyError, TypeError) as error:
        failure = type(error).__name__ + ': ' + ' '.join(str(error).split())[:2048]
    retained_bytes = supervisor.retained_bytes(output)
    own_after, children_after = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    cumulative_cpu = own_after.ru_utime + own_after.ru_stime + children_after.ru_utime + children_after.ru_stime
    accounted_cpu = whole_cpu_lower_bound(prefix_cpu, process['accounted_cpu_lower_bound_seconds'],
                                         returned_cpu, cumulative_cpu)
    if accounted_cpu >= 180:
        failure = failure or 'whole-call accounted CPU lower bound reached 180 seconds'
    parent_peak_rss = int(own_after.ru_maxrss)  # This helper requires macOS byte units.
    combined_peak_rss = max(parent_peak_rss, process['peak_sampled_combined_rss_bytes'])
    if combined_peak_rss >= WHOLE_LIMITS['rss_bytes']:
        failure = failure or 'whole-call measured RSS boundary reached'
    if retained_bytes >= WHOLE_LIMITS['output_bytes']:
        failure = failure or 'whole-call retained output boundary reached'
    result = {'schema': OWNER_SCHEMA, 'status': 'verified-within-whole-call-envelope' if failure is None else 'incomplete',
        'error': failure, 'run_file_sha256': args.run_sha256,
        'evaluation_request_sha256': args.evaluation_request_sha256,
        'resource_approval_sha256': args.approval_sha256, 'helper_sha256': args.helper_sha256,
        'supervisor_sha256': SUPERVISOR_SHA, 'original_supervisor_receipt': process_pin,
        'verification_file': verification_pin, 'execution_source': before,
        'wall_seconds': time.monotonic() - STARTED, 'whole_limits': WHOLE_LIMITS,
        'accounted_cpu_lower_bound_seconds': accounted_cpu,
        'post_supervision_accounted_cpu_seconds': cumulative_cpu - returned_cpu,
        'parent_reported_peak_rss_bytes': parent_peak_rss,
        'whole_call_peak_observed_rss_bytes': combined_peak_rss,
        'retained_output_bytes_before_owner_result': retained_bytes,
        'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
        'remaining_live_owned_pids': process['remaining_live_owned_pids'],
        'original_proof_worker_limits': PROOF_LIMITS, 'original_resource_caps_changed': False,
        'gpu_job_submitted': False, 'model_loaded': False, 'network_contacted': False,
        'pilot_acceptance_eligible': False, 'benchmark_acceptance_eligible': False,
        'self_training_readiness_eligible': False, 'automatic_retry': False, 'resume': False}
    if result['wall_seconds'] > WHOLE_LIMITS['wall_seconds']:
        failure = result['error'] = failure or 'whole-call wall boundary reached during final accounting'
        result['status'] = 'incomplete'
    # Refuse publication rather than knowingly exceed the whole retained-byte
    # envelope. No owner receipt means the attempt has not completed.
    require(retained_bytes + len(canonical(result)) + 1 <= WHOLE_LIMITS['output_bytes'],
            'owner receipt does not fit within the retained output reservation')
    write_new(output / 'owner-result.json', result)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if failure is None else 2


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        worker(Path(sys.argv[2]), sys.argv[3])
        return 0
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--run-directory', required=True, type=Path)
    parser.add_argument('--run-sha256', required=True)
    parser.add_argument('--evaluation-request-sha256', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--output-directory', required=True, type=Path)
    return supervise(parser.parse_args())


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print('local-diagnostic-verification: ' + ' '.join(str(error).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
