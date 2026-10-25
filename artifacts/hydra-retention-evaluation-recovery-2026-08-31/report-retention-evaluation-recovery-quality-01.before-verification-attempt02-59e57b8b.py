#!/usr/bin/env python3
"""Publish only independently verified, byte-pinned retention DEV comparisons.

The metrics are the exact output of the unchanged frozen summarize_outcomes
called by the independently supervised verifier. This reporter neither creates
a BoundEvaluation nor loads a model nor runs a native proof. Every positive is
joined again to its actual retained replay process input/output identity.
"""
import time
STARTED = time.monotonic()
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys

WORKSPACE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = WORKSPACE / 'artifacts/hydra-retention-evaluation-recovery-2026-08-31'
HELPER = ARCHIVE / 'report-retention-evaluation-recovery-quality-01.py'
VERIFIER = ARCHIVE / 'verify-retention-evaluation-recovery-checkpoint-local-01.py'
VERIFIER_SHA = 'f4fc10fea71a3f444af7efcfbe0477b5a3721b6f07750ddf188cc55edcfde8d0'
VERIFICATION = ARCHIVE / 'evaluation-verification-01'
INVOCATION = ARCHIVE / 'evaluation-verification-invocation-01.json'
OUTPUT = ARCHIVE / 'evaluation-quality-01'
FROZEN = WORKSPACE / '_deploy/hydra-retention-evaluation-recovery-execution-20260831'
EVALUATION_SOURCE_SHA = '730ee488675d8912a943f8487dedb27cae342478741f00131beebdd830eb0cbc'
COMMIT = 'dca88930b59e3147a95d0234d804076ccf757a74'
COHORTS, ROLES, BUDGETS = ('retention-dev32', 'frontier-dev32'), ('saved-corrected', 'mixed-retention'), (8, 16)
MAX_FILE, MAX_OUTPUT = 32 * 1024**2, 4 * 1024**2
CPU, WALL, RSS = 60, 90, 2 * 1024**3
CLAIMS = {'training_goals_scored': False, 'heldout_or_reserved_goals_scored': False,
          'research_claim_eligible': False, 'sealed_benchmark': False,
          'benchmark_acceptance_eligible': False, 'self_training_readiness_eligible': False,
          'historical_gpu_inference_attested': False}


def require(value, message):
    if not value: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(value): return sha(canonical(value))


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_FILE, 'bounded report metadata required')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate metadata key'); result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(value) is dict, 'metadata object required')
    canonical(value)
    return value


def audit(event, args):
    if event.startswith(('subprocess.', 'os.system', 'os.posix_spawn', 'socket.')):
        raise RuntimeError('quality reporting cannot execute any process or network action')
    if event == 'import' and args[0].split('.')[0] in {
            'training', 'peano_lab', 'torch', 'transformers', 'peft', 'tokenizers', 'accelerate', 'datasets', 'vllm'}:
        raise RuntimeError('quality reporting cannot import scientific/model/native execution modules')


def measurements():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    value = {'wall_seconds': time.monotonic() - STARTED, 'cpu_seconds': usage.ru_utime + usage.ru_stime,
             'peak_rss_bytes': int(usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024)}
    require(value['wall_seconds'] < WALL and value['cpu_seconds'] < CPU and value['peak_rss_bytes'] <= RSS,
            'quality reporter resource envelope reached')
    return value


def read_module(path, expected, name):
    require(re.fullmatch(r'[0-9a-f]{64}', expected) and path == path.resolve(strict=True), 'reviewed fixed helper pin required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 128 * 1024,
                'bounded single-link helper source required')
        raw = stream.read(128 * 1024 + 1)
        after = os.fstat(stream.fileno())
        require(len(raw) == before.st_size and sha(raw) == expected
                and (before.st_mtime_ns, before.st_ctime_ns) == (after.st_mtime_ns, after.st_ctime_ns),
                'reviewed reporter dependency changed')
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec); module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def pinned_json(base, path, expected):
    pin, raw = base.fingerprint(path, maximum=MAX_FILE, retain=True, deadline=STARTED + WALL)
    require(pin['sha256'] == expected, 'externally pinned evidence changed: ' + str(path))
    return decode(raw), {'path': str(path), **pin}


def nonnegative(value, maximum, label, *, integer=False):
    require(type(value) is int if integer else type(value) in (int, float), label + ' has an invalid number type')
    require(math.isfinite(value) and 0 <= value <= maximum, label + ' exceeds its original bound')
    return value


def join_positive_replays(base, verifier, request, collected, original, verification):
    """Compare actual replay summaries to saved rows, never synthesize receipts."""
    directory, index = verifier.EVALUATION_COLLECTION, collected['evaluation']['index']
    header, header_raw = base.read_json(directory / 'checkpoint/header.json', index['files']['checkpoint/header.json']['sha256'])
    head, head_raw = base.read_json(directory / 'checkpoint/HEAD.json', request['checkpoint_head_sha256'])
    require(original['schema'] == 'peano-hydra-retention-evaluation-verification-v1'
            and original['status'] == 'native-prefix-verified' and original['proof_replay_performed'] is True
            and original['model_outputs_regenerated'] is False and original['total_goal_records'] == 256
            and original['checkpoint_head_sha256'] == head['head_sha256']
            and original['checkpoint_header_sha256'] == header['header_sha256']
            and header['authorization_sha256'] == request['authorization_sha256'] == digest(header['authorization'])
            and original['plan_sha256'] == header['plan']['plan_sha256'], 'actual native verification/HEAD/header/authorization join failed')
    require(digest({key: value for key, value in head.items() if key != 'head_sha256'}) == head['head_sha256']
            and digest({key: value for key, value in header.items() if key != 'header_sha256'}) == header['header_sha256'],
            'retained original checkpoint signed metadata changed')
    count = nonnegative(head['completed'], 256, 'committed records', integer=True)
    require(original['completed_goal_records'] == count and original['inflight'] == head['inflight']
            and original['all_goal_records_present'] is (count == 256 and head['inflight'] is None)
            and original['verification_complete'] is original['all_goal_records_present'],
            'native verification invented missing or unfinished checkpoint outcomes')
    for key, value in CLAIMS.items(): require(original.get(key) is value, 'native receipt inflated claim: ' + key)
    proposal = header['plan']['evaluation_plan']
    actual_proposal, _ = base.read_json(directory / 'evaluation-plan.json', index['files']['evaluation-plan.json']['sha256'])
    require(proposal == actual_proposal, 'checkpoint proposal differs from actual collected preregistration')
    require(proposal['cohort_order'] == list(COHORTS) and proposal['roles'] == list(ROLES)
            and proposal['budgets'] == list(BUDGETS) and proposal['goal_records'] == 256
            and len(proposal['goals']) == 64 and len(proposal['ordered_slots']) == 256,
            'original evaluation plan changed fixed public DEV comparisons')
    goals = {goal['name']: goal for goal in proposal['goals']}
    cohorts = {goal['name']: cohort for cohort in COHORTS for goal in proposal['cohorts'][cohort]}
    require(len(goals) == len(cohorts) == 64 and all(len(proposal['cohorts'][cohort]) == 32 for cohort in COHORTS),
            'the two original DEV cohorts changed membership')
    capabilities = header['plan']['execution_binding']['contract']['environment']['capabilities']
    rows, positives, raw_pins = [], [], []
    for ordinal in range(1, count + 1):
        name = 'checkpoint/' + str(ordinal).zfill(6) + '.goal.json'
        record, raw = base.read_json(directory / name, index['files'][name]['sha256'])
        slot = proposal['ordered_slots'][ordinal - 1]
        row = record['row']
        require(record['ordinal'] == ordinal and all(record[key] == slot[key] for key in ('role', 'max_model_calls', 'goal'))
                and row['goal'] == slot['goal'] and record['row_sha256'] == digest(row), 'retained committed row/slot changed')
        rows.append(row); raw_pins.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
        if row['kernel_checked']:
            require(row['status'] == 'proof', 'positive retained row changed proof status')
            positives.append((slot, row))
    replayed = original['independently_replayed_proofs']
    require(type(replayed) is list and len(replayed) == len(positives), 'every committed positive requires exactly one independent replay')
    proof_joins = []
    for (slot, row), replay in zip(positives, replayed):
        require(set(replay) == {'role', 'max_model_calls', 'goal', 'commands_sha256', 'proof_nodes', 'replay_process'}
                and all(replay[key] == slot[key] for key in ('role', 'max_model_calls', 'goal'))
                and replay['commands_sha256'] == row['commands_sha256'] and replay['proof_nodes'] == row['proof_nodes'],
                'independent positive replay was omitted, duplicated or assigned to another row')
        goal, saved = goals[slot['goal']], row['evidence']['replay']
        payload = canonical({'source': goal['source'], 'statement': goal['statement'],
            'commands': row['evidence']['search']['commands'], 'id': saved['id'], 'session': saved['session'],
            'capabilities': capabilities})
        expected_output = canonical(saved) + b'\n'
        process = replay['replay_process']
        command = process['command']
        require(type(command) is list and len(command) == 3, 'exact original replay command required')
        python = verifier.runtime_python(command[0])
        require(command == [python, str(FROZEN / 'scripts/eval_peano_hydra_capacity.py'), '--replay-worker']
                and process['limits'] == verifier.PROOF_LIMITS and process['returncode'] == 0 and process['reason'] == 'exited'
                and process['stdin_bytes'] == len(payload) and process['stdin_sha256'] == sha(payload)
                and process['stdout_bytes'] == len(expected_output) and process['stdout_sha256'] == sha(expected_output)
                and process['output_encoding'] == 'utf-8' and process['output_truncated'] is False,
                'actual original replay command/input/output/resource identity differs')
        require(type(process['stderr_bytes']) is int and 0 <= process['stderr_bytes'] <= verifier.PROOF_LIMITS['output_bytes']
                and re.fullmatch(r'[0-9a-f]{64}', process['stderr_sha256']), 'original replay stderr accounting changed')
        resources = process['resources']
        nonnegative(resources['cpu_seconds'], 30, 'original proof CPU')
        nonnegative(resources['wall_seconds'], 45, 'original proof wall')
        nonnegative(resources['peak_rss_bytes'], 1024**3, 'original proof RSS')
        proof_joins.append({'cohort': cohorts[slot['goal']], **slot, 'commands_sha256': row['commands_sha256'],
            'proof_nodes': row['proof_nodes'], 'replay_process_sha256': digest(process),
            'native_request_sha256': sha(payload), 'native_result_sha256': sha(expected_output)})
    require(original['committed_model_generate_calls'] == sum(row['model_generate_calls'] for row in rows),
            'original checkpoint call accounting differs')
    require(verification['checkpoint_raw_head_sha256'] == sha(head_raw)
            and verification['checkpoint_raw_header_sha256'] == sha(header_raw)
            and verification['committed_rows_sha256'] == digest(rows)
            and verification['committed_row_files'] == {item['path'][len('checkpoint/'):]:
                {key: item[key] for key in ('bytes', 'sha256')} for item in raw_pins},
            'original frozen metrics were not joined to these exact retained rows')
    return {'header': header, 'head': head, 'rows': rows, 'raw_row_pins': raw_pins, 'positive_replay_joins': proof_joins}


def table_from_frozen_metrics(metrics, joined):
    """Presentation of existing summaries; no replacement outcome classifier."""
    require(metrics['schema'] == 'peano-hydra-retention-evaluation-metadata-v1'
            and metrics['status'] == 'metadata-only-not-independent-proof-verification'
            and metrics['proof_replay_performed'] is False and metrics['partial_pairs_scored'] is False
            and metrics['completed_goal_records'] == len(joined['rows'])
            and metrics['missing_unknown_goal_records'] == 256 - len(joined['rows'])
            and metrics['all256_records_present'] is (len(joined['rows']) == 256)
            and set(metrics['cohorts']) == set(COHORTS), 'unchanged frozen summary changed its original scope or prefix')
    for key, value in CLAIMS.items():
        if key != 'historical_gpu_inference_attested': require(metrics.get(key) is value, 'frozen summary inflated claim')
    table = []
    for cohort in COHORTS:
        summary = metrics['cohorts'][cohort]
        lanes = {(item['role'], item['max_model_calls']): item for item in summary['lanes']}
        comparisons = {item['max_model_calls']: item for item in summary['matched_comparisons']}
        require(len(summary['lanes']) == len(lanes) == 4 and set(lanes) == {(role, budget) for role in ROLES for budget in BUDGETS}
                and len(summary['matched_comparisons']) == len(comparisons) == 2 and set(comparisons) == set(BUDGETS),
                'frozen summary lane membership changed')
        for budget in BUDGETS:
            arms = {}
            for role in ROLES:
                lane = lanes[(role, budget)]
                actual_positive_count = sum(1 for item in joined['positive_replay_joins']
                    if item['cohort'] == cohort and item['role'] == role and item['max_model_calls'] == budget)
                require(lane['planned_goals'] == 32 and lane['reported_proofs'] == actual_positive_count,
                        'frozen proof count does not match actual independently replayed positives')
                unknown = nonnegative(lane['unknown_outcomes_including_missing'], 32, 'unknown outcomes', integer=True)
                known = lane['committed_goal_records'] == 32 and unknown == 0
                require((lane['reported_proof_fraction_if_all_known'] is None) is (not known), 'missing outcomes acquired a success rate')
                arms[role] = {'successes_out_of_32': lane['reported_proofs'] if known else None,
                    'success_fraction': lane['reported_proof_fraction_if_all_known'],
                    'verified_successes_among_committed': actual_positive_count,
                    'committed_goal_records': lane['committed_goal_records'], 'unknown_outcomes': unknown,
                    'missing_unknown_goal_records': lane['missing_unknown_goal_records'],
                    'known_unproved_within_budget': lane['known_unproved_within_budget'],
                    'model_generate_calls': lane['committed_model_generate_calls'],
                    'malformed_sequences_rejected': lane['malformed_sequences_rejected'],
                    'authority_sequences_rejected': lane['authority_sequences_rejected']}
            comparison = comparisons[budget]
            complete = comparison['all64_matched_rows_present'] is True and comparison['known_paired_goals'] == 32
            require(not complete or all(arms[role]['successes_out_of_32'] is not None for role in ROLES),
                    'paired result cannot resolve unknown lanes')
            table.append({'cohort': cohort, 'max_model_calls': budget, 'planned_paired_goals': 32,
                'status': 'complete-matched-dev-comparison' if complete else 'incomplete-unknown-outcomes',
                'arms': arms, 'paired_wins': len(comparison['reported_gains']) if complete else None,
                'paired_losses': len(comparison['reported_losses']) if complete else None,
                'paired_win_goals': comparison['reported_gains'] if complete else None,
                'paired_loss_goals': comparison['reported_losses'] if complete else None,
                'known_paired_goals': comparison['known_paired_goals'],
                'unknown_pair_goals': comparison['unknown_pair_goals']})
    return table


def render(summary):
    full = summary['full_comparison_resolved']
    opening = 'The fixed development comparison is complete.' if full else 'The verified development evidence is partial.'
    if not full:
        opening += (' All checkpoint outcomes are resolved, but no completed final report was verified.'
                    if summary['all_paired_outcomes_resolved'] else ' Unfinished or unresolved outcomes remain unknown.')
    lines = [
        opening, '',
        str(summary['independently_replayed_positive_outcomes']) + ' saved positive outcomes were independently rechecked with the original native proof limits across '
        + str(summary['completed_goal_records']) + ' of 256 committed evaluation records.', '',
        '| Development set | Calls | Saved corrected adapter | Mixed retention pilot | Paired wins / losses |',
        '| --- | ---: | ---: | ---: | ---: |']
    def cell(arm):
        return str(arm['successes_out_of_32']) + '/32' if arm['successes_out_of_32'] is not None else \
            'unknown (' + str(arm['unknown_outcomes']) + ' unresolved)'
    for item in summary['comparisons']:
        label = 'Old DEV' if item['cohort'] == 'retention-dev32' else 'Frontier DEV'
        paired = str(item['paired_wins']) + ' / ' + str(item['paired_losses']) if item['paired_wins'] is not None else 'unknown'
        lines.append('| ' + label + ' | ' + str(item['max_model_calls']) + ' | ' + cell(item['arms'][ROLES[0]])
            + ' | ' + cell(item['arms'][ROLES[1]]) + ' | ' + paired + ' |')
    lines += ['', 'Wins and losses compare the mixed pilot with the saved corrected adapter on the same 32 goals and call budget.', '',
        'Both sets are exposed development diagnostics. These results make no TRAIN-probe, unseen-test, sealed-benchmark, acceptance, or readiness claim.', '',
        'The JSON summary retains exact frozen metrics, incomplete/in-flight accounting, per-positive replay joins, actual job resources and raw evidence hashes.', '']
    return '\n'.join(lines).encode()


def owner_evidence(base, verifier, args, expected):
    owner, owner_pin = pinned_json(base, VERIFICATION / 'owner-result.json', args.owner_result_sha256)
    verified, verified_pin = pinned_json(base, VERIFICATION / 'verification.json', args.verification_sha256)
    original, original_pin = pinned_json(base, VERIFICATION / 'checkpoint-verification.json', args.checkpoint_verification_sha256)
    invocation, invocation_pin = pinned_json(base, INVOCATION, args.invocation_exit_sha256)
    require(owner['schema'] == verifier.OWNER_SCHEMA and owner['status'] in (
                'complete-artifacts-verified-within-envelope', 'prefix-verified-within-envelope')
            and owner['error'] is None and owner['source_commit'] == COMMIT and owner['worker_returncode'] == 0
            and owner['owned_group_quiescent'] is True and owner['remaining_live_owned_pids'] == []
            and owner['whole_limits'] == verifier.LIMITS and owner['original_proof_worker_limits'] == verifier.PROOF_LIMITS,
            'independent replay owner did not complete successfully inside its unchanged limits')
    require(verified['schema'] == verifier.SCHEMA and verified['status'] in (
                'complete-artifacts-independently-verified', 'committed-prefix-independently-verified')
            and verified['source_commit'] == COMMIT and verified['original_cli_returncode'] == 0
            and verified['original_cli_sha256'] == verifier.CLI_SHA
            and verified['original_proof_worker_limits'] == verifier.PROOF_LIMITS
            and verified['original_receipts_and_model_bytes_reauthenticated_after_replay'] is True
            and verified['all_collected_entries_retained_and_rechecked'] is True
            and not any(verified['guard_attempts'].values()), 'actual independent worker verification did not pass all original joins')
    for value in (owner, verified):
        require(all(value[key] == item for key, item in expected.items()), 'actual verifier receipt changed external evidence pins')
        for key, item in verifier.FALSE_CLAIMS.items(): require(value[key] is item, 'verifier escaped original work/claim scope')
    require(owner['verification_file'] == {key: verified_pin[key] for key in ('bytes', 'sha256')}
            and owner['checkpoint_verification_file'] == verified['checkpoint_verification'] == original_pin
            and verified['verification'] == original, 'owner/worker/original native receipt byte joins differ')
    measured = owner['measurements']
    require(nonnegative(measured['accounted_whole_cpu_lower_bound_seconds'], 600, 'whole replay CPU') < 600
            and nonnegative(measured['whole_wall_seconds'], 900, 'whole replay wall') < 900
            and nonnegative(measured['peak_sampled_parent_plus_tree_rss_bytes'], 2 * 1024**3, 'whole replay RSS') < 2 * 1024**3
            and nonnegative(measured['parent_peak_rss_bytes'], 2 * 1024**3, 'owner RSS') < 2 * 1024**3
            and measured['retained_output_bytes_before_owner_result'] + owner_pin['bytes'] <= 64 * 1024**2,
            'independent replay final resource boundary was reached')
    supervision, supervision_pin = pinned_json(base, VERIFICATION / 'supervision.json', owner['supervision_file']['sha256'])
    reservation, reservation_pin = pinned_json(base, VERIFICATION / 'reservation.json', owner['reservation_file']['sha256'])
    require({key: supervision_pin[key] for key in ('bytes', 'sha256')} == owner['supervision_file']
            and {key: reservation_pin[key] for key in ('bytes', 'sha256')} == owner['reservation_file']
            and all(reservation[key] == value for key, value in expected.items())
            and reservation['output_directory'] == str(VERIFICATION), 'actual owner reservation/supervision evidence changed')
    require(supervision['schema'] == verifier.SUPERVISION_SCHEMA and supervision['status'] == 'completed-with-open-gates'
            and supervision['returncode'] == 0 and supervision['reason'] == 'exited' and supervision['error'] is None
            and supervision['owned_group_quiescent'] is True and supervision['remaining_live_owned_pids'] == []
            and supervision['new_whole_envelope'] == verifier.LIMITS
            and supervision['original_limits_constructor_changed'] is False
            and supervision['metadata']['helper_sha256'] == VERIFIER_SHA
            and supervision['metadata']['reservation_sha256'] == reservation_pin['sha256'],
            'actual owned replay process tree did not complete its guards')
    log_pins = {}
    for name in ('stdout', 'stderr'):
        actual, _ = base.fingerprint(VERIFICATION / (name + '.log'), maximum=1024**2, deadline=STARTED + WALL)
        require(actual == supervision['logs'][name], 'actual verification log bytes changed')
        log_pins[name] = {'path': str(VERIFICATION / (name + '.log')), **actual}
    require(invocation['schema'] == 'peano-hydra-retention-evaluation-recovery-verification-invocation-exit-v1'
            and invocation['status'] == 'exited' and invocation['source_commit'] == COMMIT
            and invocation['run_id'] == 'retention-evaluation-recovery-v1' and type(invocation['exit_code']) is int and invocation['exit_code'] == 0
            and invocation['observed_from'] == 'actual-tool-process-completion' and invocation['automatic_retry'] is False,
            'actual external zero-exit observation is required; an owner file alone is insufficient')
    helper_pin, _ = base.fingerprint(VERIFIER, maximum=128 * 1024, deadline=STARTED + WALL)
    require(invocation['helper'] == {'path': str(VERIFIER), **helper_pin} and helper_pin['sha256'] == VERIFIER_SHA
            and invocation['owner_result'] == owner_pin and invocation['verification'] == verified_pin
            and invocation['checkpoint_verification'] == original_pin, 'actual exit observation belongs to other evidence')
    argv = invocation['argv']
    require(type(argv) is list and argv[:4] == [str(verifier.PYTHON), '-I', '-B', str(VERIFIER)]
            and len(argv) == 4 + 2 * len(expected), 'external invocation changed the exact owner command')
    arguments = dict(zip(argv[4::2], argv[5::2]))
    require(len(arguments) == len(expected) and arguments == {'--' + key.replace('_', '-'): value for key, value in expected.items()},
            'externally observed command did not use the exact verified raw inputs')
    return {'owner': owner, 'verification': verified, 'original': original, 'supervision': supervision,
            'pins': {'invocation': invocation_pin, 'owner_result': owner_pin, 'verification': verified_pin,
                'checkpoint_verification': original_pin, 'supervision': supervision_pin, 'reservation': reservation_pin,
                'logs': log_pins, 'verifier_helper': {'path': str(VERIFIER), **helper_pin}}}


def publish(base, name, raw):
    require(name in ('qualitysummary.json', 'RESULT.md', 'report-receipt.json') and type(raw) is bytes and len(raw) <= MAX_OUTPUT,
            'fixed bounded quality outputs only')
    parent = os.open(OUTPUT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.fsync(parent)
    finally: os.close(parent)
    pin, _ = base.fingerprint(OUTPUT / name, maximum=MAX_OUTPUT, deadline=STARTED + WALL)
    require(pin == {'bytes': len(raw), 'sha256': sha(raw)}, 'quality output publication changed its exact bytes')
    return {'path': str(OUTPUT / name), **pin}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--expected-helper-sha256', required=True)
    for name in ('model_collection_sha256', 'evaluation_collection_sha256', 'model_manifest_sha256',
            'checkpoint_head_sha256', 'authorization_sha256', 'approval_sha256', 'source_header_sha256',
            'verification_sha256', 'owner_result_sha256', 'checkpoint_verification_sha256', 'invocation_exit_sha256'):
        parser.add_argument('--' + name.replace('_', '-'), required=True)
    parser.add_argument('--train-job-id', required=True)
    parser.add_argument('--evaluation-job-id', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin' and Path(__file__).absolute() == HELPER,
            'exact isolated uncached local reporter required')
    for key, value in vars(args).items():
        require(re.fullmatch(r'[0-9a-f]{64}' if key.endswith('sha256') else r'[1-9][0-9]{0,19}', value),
                'actual external raw identity required: ' + key)
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT, MAX_OUTPUT)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('quality reporter whole-call wall cap')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    require(not any(name == 'training' or name.startswith('training.') or name == 'peano_lab' or name.startswith('peano_lab.')
                    for name in sys.modules), 'reporter must start without imported scientific execution modules')
    sys.addaudithook(audit)
    verifier = read_module(VERIFIER, VERIFIER_SHA, '_retention_quality_reviewed_verifier_metadata')
    # Only the actual reviewed metadata utilities are reused. No worker,
    # scientific_join, supervisor, model loader, original CLI or native API runs.
    base = verifier.load_module(verifier.BASE, verifier.BASE_SHA, '_retention_quality_readonly_file_utilities')
    helper_pin, _ = base.fingerprint(HELPER, maximum=128 * 1024, deadline=STARTED + WALL)
    require(helper_pin['sha256'] == args.expected_helper_sha256, 'reviewed quality reporter source changed')
    require(base.exact_path(OUTPUT, exists=False) == OUTPUT and OUTPUT.parent == ARCHIVE and not os.path.lexists(OUTPUT),
            'fresh fixed quality output directory required; no overwrite')
    expected = {'helper_sha256': VERIFIER_SHA,
        **{key: getattr(args, key) for key in (*verifier.PIN_FIELDS[1:], 'train_job_id', 'evaluation_job_id')}}
    require(set(expected) == set(verifier.PIN_FIELDS) | {'train_job_id', 'evaluation_job_id'}, 'verifier external pin interface changed')
    before_source = verifier.source_inputs(base, args.approval_sha256, deadline=STARTED + WALL)
    require(base.fingerprint(FROZEN / 'training/peano_hydra/retention_evaluation.py', deadline=STARTED + WALL)[0]['sha256']
            == EVALUATION_SOURCE_SHA, 'frozen original metric implementation changed')
    collected = verifier.collections(base, expected, deadline=STARTED + WALL)
    evidence = owner_evidence(base, verifier, args, expected)
    owner, verified, original = evidence['owner'], evidence['verification'], evidence['original']
    require(owner['source_inputs'] == verified['source_inputs'] == before_source, 'verification used other frozen source/input bytes')
    joined = join_positive_replays(base, verifier, expected, collected, original, verified)
    require(verified['guard_counts']['native_guard_processes'] == len(joined['positive_replay_joins']),
            'actual original native process count differs from positive proofs')
    scientific = verified['scientific_binding']
    require(scientific['bound_evaluation_plan_sha256'] == joined['header']['plan']['plan_sha256']
            and scientific['authorization_sha256'] == args.authorization_sha256
            and scientific['actual_remote_identity'] == collected['evaluation']['index']['binding']['execution_identity']
            and scientific['baseline_reference'] == joined['header']['plan']['baseline_reference']
            and scientific['candidate_reference'] == joined['header']['plan']['candidate_reference'],
            'original verified scientific binding differs from actual collected checkpoint')
    metrics = verified['metrics']
    comparisons = table_from_frozen_metrics(metrics, joined)
    report_check = verified['completed_report_metadata_verification']
    report_matches = verified['complete_report_matches_verified_checkpoint']
    require(owner['complete_report_matches_verified_checkpoint'] is report_matches
            and owner['full_comparison_verification_complete'] is report_matches
            and verified['full_comparison_verification_complete'] is report_matches
            and owner['all256_checkpoint_records_independently_verified'] is original['verification_complete']
            and verified['all256_checkpoint_records_independently_verified'] is original['verification_complete'],
            'owner and worker disagree about complete versus prefix verification')
    if report_matches:
        require(original['verification_complete'] is True and report_check is not None
                and report_check['schema'] == 'peano-hydra-retention-evaluation-verification-v1'
                and report_check['status'] == 'metadata-checked-native-replay-not-performed'
                and report_check['verification_complete'] is False and report_check['proof_replay_performed'] is False
                and report_check['metrics'] == metrics and report_check['plan_sha256'] == original['plan_sha256'],
                'complete report lacks the existing original metadata validator result')
        report, raw = base.read_json(verifier.EVALUATION_COLLECTION / 'evaluation.json', verified['completed_report_raw_sha256'],
                                    maximum=48 * 1024**2)
        require(report['rows'] == joined['rows'] and report['metrics'] == metrics
                and report['evaluation_sha256'] == report_check['evaluation_sha256'], 'completed report differs from actual replayed checkpoint rows')
    else:
        require(report_check is None and verified['completed_report_raw_sha256'] is None,
                'prefix-only verification cannot claim a separately completed report')
    all_pairs = all(item['status'] == 'complete-matched-dev-comparison' for item in comparisons)
    full = report_matches and original['verification_complete'] is True and all_pairs
    summary = {'schema': 'peano-hydra-retention-evaluation-recovery-quality-summary-v1',
        'status': 'independently-verified-complete-dev-comparison' if full else 'independently-verified-partial-dev-comparison',
        'run_id': 'retention-evaluation-recovery-v1', 'source_commit': COMMIT, 'full_comparison_resolved': full,
        'all_paired_outcomes_resolved': all_pairs,
        'all256_checkpoint_records_independently_verified': original['verification_complete'],
        'complete_final_report_matches_checkpoint': report_matches,
        'completed_goal_records': original['completed_goal_records'],
        'missing_unknown_goal_records': 256 - original['completed_goal_records'],
        'inflight': original['inflight'], 'inflight_model_generate_calls': original['inflight_model_generate_calls'],
        'committed_model_generate_calls': original['committed_model_generate_calls'],
        'independently_replayed_positive_outcomes': len(joined['positive_replay_joins']),
        'comparisons': comparisons, 'frozen_metrics': metrics, 'frozen_metrics_sha256': digest(metrics),
        'frozen_metric_source_sha256': EVALUATION_SOURCE_SHA, 'positive_replay_joins': joined['positive_replay_joins'],
        'committed_row_files': verified['committed_row_files'], 'committed_rows_sha256': verified['committed_rows_sha256'],
        'evidence': evidence['pins'], 'external_inputs': expected,
        'training_job_accounting': collected['model']['index']['accounting'],
        'evaluation_job_accounting': collected['evaluation']['index']['accounting'],
        'independent_verification_resources': owner['measurements'], 'independent_verification_limits': owner['whole_limits'],
        'original_per_proof_limits': verifier.PROOF_LIMITS,
        'proof_replay_performed_by_reporter': False, 'model_loaded': False, 'network_contacted': False,
        'scheduler_called': False, 'partial_pairs_scored': False, 'automatic_retry': False,
        'claim_boundary': metrics['claim_boundary'], **CLAIMS,
        'created_at_utc': datetime.now(timezone.utc).isoformat()}
    # Evidence and dependencies are rehashed once more before publishing either
    # result file. This is metadata/byte checking, never another proof replay.
    require(verifier.source_inputs(base, args.approval_sha256, deadline=STARTED + WALL) == before_source
            and verifier.collections(base, expected, deadline=STARTED + WALL) == collected
            and owner_evidence(base, verifier, args, expected) == evidence
            and base.fingerprint(HELPER, maximum=128 * 1024, deadline=STARTED + WALL)[0] == helper_pin,
            'actual evidence/source changed during report preparation')
    measurements()
    os.mkdir(OUTPUT, 0o700)
    outputs = {'qualitysummary.json': publish(base, 'qualitysummary.json', canonical(summary) + b'\n'),
               'RESULT.md': publish(base, 'RESULT.md', render(summary))}
    receipt = {'schema': 'peano-hydra-retention-evaluation-recovery-quality-report-publication-v1', 'status': 'published-from-verified-evidence',
        'helper': {'path': str(HELPER), **helper_pin}, 'outputs': outputs, 'evidence': evidence['pins'],
        'resources': measurements(), 'limits': {'cpu_seconds': CPU, 'wall_seconds': WALL, 'observed_peak_rss_bytes': RSS},
        'fresh_native_or_model_work_performed': False, 'network_or_scheduler_work_performed': False,
        'frozen_source_or_collected_inputs_modified': False, 'automatic_retry': False}
    publication = publish(base, 'report-receipt.json', canonical(receipt) + b'\n')
    print(json.dumps({'status': receipt['status'], 'summary_status': summary['status'], 'outputs': outputs,
                      'receipt': publication}, sort_keys=True), flush=True)
    measurements(); signal.setitimer(signal.ITIMER_REAL, 0)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, IndexError, RuntimeError, TimeoutError) as error:
        print('retention-quality-report: ' + ' '.join(str(error).split())[:2048], file=sys.stderr, flush=True)
        raise SystemExit(2)
