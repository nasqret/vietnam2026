#!/usr/bin/env python3
"""Report actual collected DEV results only after exact local verification.

Without a successful supplied verification-owner receipt this tool reports
availability only, never a model proof score. It runs no model, proof worker,
network command or origin validator. All original evidence stays unchanged.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import sys
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
VERIFIER_SHA = '7df14454b45ffd8b85d8d2ed4903fd968c0decc642b4b9e35f7255c6fa8bd155'
DEV_PLAN_RAW = 'a8084683ea64e4128f4d34eea0753c67fc42a55772e1c698a5dbd62865878c4b'
ROLES, BUDGETS = ('saved-corrected', 'new-frontier'), (8, 16)
CLAIM = '32 public, correlated DEV goals from two diagnostic families; no unseen-test or benchmark-acceptance claim.'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def read(path, expected, maximum=8 * 1024**2):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve(strict=True) and path.is_file()
            and not path.is_symlink() and path.stat().st_nlink == 1 and path.stat().st_size <= maximum,
            'bounded regular nonsymlink evidence required')
    require(type(expected) is str and re.fullmatch(r'[a-f0-9]{64}', expected), 'external raw evidence pin required')
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns
            and before.st_ino == after.st_ino and hashlib.sha256(raw).hexdigest() == expected,
            'pinned evidence changed')
    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, 'duplicate evidence field')
            result[key] = item
        return result
    def finite(text):
        value = float(text)
        require(math.isfinite(value), 'nonfinite evidence')
        return value
    data = json.loads(raw, object_pairs_hook=pairs, parse_float=finite,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite evidence')))
    require(type(data) is dict, 'evidence object required')
    return data, raw


def described(directory, name, descriptor, maximum=8 * 1024**2):
    data, raw = read(directory / name, descriptor['sha256'], maximum)
    require(len(raw) == descriptor['bytes'], 'evidence byte count differs')
    return data, raw


def outcome(row, budget):
    if row['kernel_checked'] is True:
        return 'proof'
    if row['status'] == 'exhausted':
        return 'exhausted'
    if row['model_generate_calls'] == budget:
        return 'call-limit'
    return 'unknown'


def aggregate(plan, rows):
    """Summarize verified rows without treating missing/limited work as false."""
    slots = plan['evaluation_plan']['ordered_slots']
    goals = plan['evaluation_plan']['goals']
    require(len(slots) == len(rows) == 128 and len(goals) == 32, 'complete fixed 128-row factorial report required')
    by_slot = {}
    for slot, row in zip(slots, rows):
        key = (slot['role'], slot['max_model_calls'], slot['goal'])
        require(key not in by_slot and key[0] in ROLES and key[1] in BUDGETS and row['goal'] == key[2],
                'row order or role/budget/goal identity differs')
        by_slot[key] = row
    lanes, pairs = [], []
    for budget in BUDGETS:
        for role in ROLES:
            selected = [by_slot[(role, budget, goal['name'])] for goal in goals]
            statuses = Counter(outcome(row, budget) for row in selected)
            generation = {name: sum(row['generation'][name] for row in selected) for name in (
                'candidate_sequences_requested', 'candidate_sequences_returned', 'candidate_lines_returned',
                'malformed_sequences_rejected', 'authority_sequences_rejected')}
            native = Counter(d['kind'] for row in selected for d in row['evidence']['search']['diagnostics'])
            calls = sum(row['model_generate_calls'] for row in selected)
            proofs = statuses['proof']
            requested = generation['candidate_sequences_requested']
            lanes.append({'role': role, 'max_model_calls': budget, 'goals': 32,
                'independently_verified_proofs': proofs, 'unknown_outcomes': statuses['unknown'],
                'known_unproved_within_budget': 32 - proofs - statuses['unknown'],
                'outcomes': dict(statuses), 'model_generate_calls': calls,
                'calls_per_verified_proof': calls / proofs if proofs else None,
                'generation': generation,
                'rejected_sequence_fraction': (generation['malformed_sequences_rejected']
                    + generation['authority_sequences_rejected']) / requested if requested else None,
                'retained_native_diagnostics_by_kind': dict(sorted(native.items())),
                'native_diagnostic_scope': 'Retained search diagnostics, capped at128 per goal; not a count of every rejection.',
                'goal_wall_seconds_sum': sum(row['resources']['goal_wall_seconds'] for row in selected),
                'goal_cpu_seconds_sum': sum(row['resources']['goal_cpu_seconds'] for row in selected),
                'max_reported_process_rss_bytes': max(row['resources']['process_peak_rss_bytes'] for row in selected),
                'max_goal_cuda_allocated_bytes': max(row['resources']['cuda_peak_allocated_bytes'] for row in selected),
                'max_goal_cuda_reserved_bytes': max(row['resources']['cuda_peak_reserved_bytes'] for row in selected)})
        known, gains, losses, both, unknown = [], [], [], [], []
        for goal in goals:
            name = goal['name']
            old, new = (outcome(by_slot[(role, budget, name)], budget) for role in ROLES)
            if 'unknown' in (old, new):
                unknown.append(name)
                continue
            known.append(name)
            if new == 'proof' and old != 'proof':
                gains.append(name)
            if old == 'proof' and new != 'proof':
                losses.append(name)
            if old == new == 'proof':
                both.append(name)
        pairs.append({'max_model_calls': budget, 'known_paired_goals': len(known), 'unknown_pairs': len(unknown),
            'gains': gains, 'losses': losses, 'net_gain_among_known_pairs': len(gains) - len(losses),
            'common_verified_proofs': both, 'unknown_pair_goals': unknown})
    return lanes, pairs


def verified_inputs(collected, collection, owner_directory, owner_sha):
    owner, _ = read(owner_directory / 'owner-result.json', owner_sha)
    require(owner['schema'] == 'peano-hydra-diagnostic-portable-local-verification-owner-v1'
        and owner['status'] == 'verified-within-whole-call-envelope' and owner['error'] is None
        and owner['helper_sha256'] == VERIFIER_SHA and owner['remaining_live_owned_pids'] == []
        and owner['evaluation_request_sha256'] == collection['evaluation_request_sha256']
        and owner['resource_approval_sha256'] == collection['approval_sha256']
        and owner['accounted_cpu_lower_bound_seconds'] < 180 and owner['wall_seconds'] <= 300
        and owner['whole_call_peak_observed_rss_bytes'] < 2 * 1024**3,
        'successful exact independent verification owner receipt required')
    verification, _ = described(owner_directory, 'verification.json', owner['verification_file'], 32 * 1024**2)
    process, _ = described(owner_directory, 'supervision.json', owner['original_supervisor_receipt'])
    require(process['status'] == 'process-completed-with-open-gates' and process['returncode'] == 0
            and process['remaining_live_owned_pids'] == [], 'independent verification supervision is incomplete')
    run, _ = described(collected, 'run.json', collection['files']['run.json'])
    report, _ = described(collected, 'diagnostic.json', collection['files']['diagnostic.json'], 48 * 1024**2)
    require(owner['run_file_sha256'] == collection['files']['run.json']['sha256']
        and verification['run_file_sha256'] == owner['run_file_sha256']
        and verification['status'] == 'diagnostic-proofs-independently-replayed'
        and verification['request_file_sha256'] == collection['evaluation_request_sha256']
        and verification['resource_approval_file_sha256'] == collection['approval_sha256']
        and run['request_file_sha256'] == collection['evaluation_request_sha256']
        and run['reservation']['job_id'] == collection['job_id']
        and run['reservation']['jobs'] == {'evaluate': collection['job_id']}
        and run['report']['path'] == 'diagnostic.json'
        and all(run['report'][key] == collection['files']['diagnostic.json'][key] for key in ('bytes', 'sha256')),
        'collected job/run/report does not join independently verified evidence')
    checked = verification['verification']
    plan = report['plan']
    require(checked['status'] == 'passed' and checked['verification_complete'] is True
        and checked['proof_replay_performed'] is True
        and checked['evaluation_sha256'] == report['evaluation_sha256']
        and checked['plan_sha256'] == verification['portable_plan_sha256'] == plan['plan_sha256']
        and plan['evaluation_raw_sha256'] == DEV_PLAN_RAW
        and plan['evaluation_plan']['cohort'] == 'review-candidate-dev'
        and plan['evaluation_plan']['roles'] == list(ROLES) and plan['evaluation_plan']['budgets'] == list(BUDGETS)
        and checked['metrics'] == verification['metrics'] == report['metrics'], 'verified result/plan/metric identities differ')
    slots, rows = plan['evaluation_plan']['ordered_slots'], report['rows']
    expected = {(slot['role'], slot['max_model_calls'], slot['goal'], row['commands_sha256'])
                for slot, row in zip(slots, rows) if row['kernel_checked']}
    actual = {(row['role'], row['max_model_calls'], row['goal'], row['commands_sha256'])
              for row in checked['independently_replayed_proofs']}
    require(actual == expected and len(actual) == len(checked['independently_replayed_proofs']),
            'not every positive lane/goal has its independent replay receipt')
    return report, owner


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--collected-directory', required=True, type=Path)
    parser.add_argument('--collection-receipt-sha256', required=True)
    parser.add_argument('--verification-directory', type=Path)
    parser.add_argument('--owner-sha256')
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    require((args.verification_directory is None) == (args.owner_sha256 is None), 'verification directory and raw owner pin go together')
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('reporting wall limit')))
    signal.alarm(30)
    collected = args.collected_directory.resolve(strict=True)
    require(args.collected_directory == collected and ARCHIVE in collected.parents, 'canonical collected archive required')
    collection, _ = read(collected / 'collection-receipt.json', args.collection_receipt_sha256)
    require(collection['schema'] == 'peano-hydra-diagnostic-results-collection-v1'
            and collection['status'] == 'collected-not-proof-verified', 'successful exact job collection required')
    output = args.output_directory
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch(r'diagnostic-report-[0-9]{2}', output.name) and not output.exists()
            and output != collected and output != args.verification_directory, 'fresh separate report archive required')
    result = {'schema': 'peano-hydra-verified-dev-quality-report-v1',
        'status': 'unscored-pending-independent-verification', 'job_id': collection['job_id'],
        'collection_receipt_sha256': args.collection_receipt_sha256,
        'resource_approval_sha256': collection['approval_sha256'],
        'evaluation_request_sha256': collection['evaluation_request_sha256'],
        'accounting': collection['accounting'], 'claim_boundary': CLAIM,
        'model_inference_or_proof_replay_performed_by_reporter': False,
        'benchmark_acceptance_eligible': False, 'self_training_readiness_eligible': False,
        'sealed_test': False, 'research_claim_eligible': False, 'quality_metrics': None}
    lines = ['# Hydra DEV diagnostic result', '',
        'Job **' + collection['job_id'] + '**: **' + collection['accounting']['state'] + '**, exit **'
            + collection['accounting']['exit_code'] + '**.', '']
    if args.verification_directory is None:
        lines += ['**No verified model-quality score is available yet.**', '',
            'The collection is retained. Missing, interrupted or unverified outcomes remain unknown.',
            'Use the local verification helper on a complete collected run before interpreting proof rates.', '']
    else:
        owner_directory = args.verification_directory.resolve(strict=True)
        require(owner_directory == args.verification_directory and ARCHIVE in owner_directory.parents,
                'canonical independent verification archive required')
        report, owner = verified_inputs(collected, collection, owner_directory, args.owner_sha256)
        lanes, pairs = aggregate(report['plan'], report['rows'])
        for pair, saved in zip(pairs, report['metrics']['matched_comparisons']):
            require(pair['max_model_calls'] == saved['max_model_calls']
                and pair['known_paired_goals'] == saved['known_paired_goals']
                and pair['unknown_pairs'] == saved['unknown_pairs']
                and pair['gains'] == saved['reported_gains'] and pair['losses'] == saved['reported_losses'],
                'recomputed paired changes differ from verified original metrics')
        result.update(status='verified-dev-diagnostic-only', verification_owner_sha256=args.owner_sha256,
            verification_helper_sha256=VERIFIER_SHA,
            quality_metrics={'lanes': lanes, 'paired_comparisons': pairs,
                'comparison_inconclusive_on_unknown_pairs': any(pair['unknown_pairs'] for pair in pairs),
                'all_positive_proofs_independently_replayed': True})
        old16, new16 = [lane for lane in lanes if lane['max_model_calls'] == 16]
        lines += ['At **16 model calls per goal**, the new model proved **'
            + str(new16['independently_verified_proofs']) + '/32**, versus **'
            + str(old16['independently_verified_proofs']) + '/32** for the previous model.', '',
            '| Calls/goal | Adapter | Verified proofs | Unknown | Actual calls | Malformed sequences | Authority rejections |',
            '| ---: | --- | ---: | ---: | ---: | ---: | ---: |']
        for lane in lanes:
            generation = lane['generation']
            label = 'Previous' if lane['role'] == ROLES[0] else 'New'
            lines.append('| {} | {} | {}/32 | {} | {} | {} | {} |'.format(lane['max_model_calls'], label,
                lane['independently_verified_proofs'], lane['unknown_outcomes'], lane['model_generate_calls'],
                generation['malformed_sequences_rejected'], generation['authority_sequences_rejected']))
        lines += ['']
        for pair in pairs:
            lines.append('At {} calls: **{} gains, {} losses**, with **{} unknown pairs**.'.format(
                pair['max_model_calls'], len(pair['gains']), len(pair['losses']), pair['unknown_pairs']))
        lines += ['', 'Gains and losses count only goals with known outcomes for both adapters. '
            'An unproved result means no proof was found within this search budget; it does not mean the theorem is false.', '',
            'Sequence rejections count malformed or unauthorized generated tactics, not rejected final mathematical proofs. '
            'The JSON report also retains native diagnostic categories, calls per verified proof, goal-time sums and memory observations.', '',
            'Goal-time sums exclude model loading and other allocation setup. Host RSS is a process high-water mark; '
            'CUDA figures are the maximum of the per-goal recorded peaks.', '',
            'All positive results were freshly replayed through the original native checker. '
            'This is a public DEV comparison on two families, not an unseen theorem benchmark or permission to self-train.', '']
    result['resources'] = {'wall_seconds': time.monotonic() - STARTED,
        'cpu_seconds': resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        'maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    require(result['resources']['maxrss_bytes'] < 1024**3, 'reporting memory envelope reached')
    output.mkdir(mode=0o700)
    for name, raw in [('report.json', canonical(result) + b'\n'), ('README.md', ('\n'.join(lines) + '\n').encode())]:
        require(len(raw) <= 4 * 1024**2, 'report output byte cap')
        with (output / name).open('xb') as stream:
            stream.write(raw)
    signal.alarm(0)
    print(json.dumps({'status': result['status'], 'output_directory': str(output),
        'report_sha256': hashlib.sha256((output / 'report.json').read_bytes()).hexdigest()}, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print('diagnostic-reporting: ' + ' '.join(str(error).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
