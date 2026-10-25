#!/usr/bin/env python3
"""Synthetic metadata/aggregation checks only; no original proof/model execution."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import time
from types import SimpleNamespace

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
HELPER = ARCHIVE / 'verify-diagnostic-prefix-local-01.py'


def main():
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('synthetic check wall bound')))
    signal.alarm(15)
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert args.output.parent == ARCHIVE and args.output == args.output.resolve(strict=False) and not args.output.exists()
    raw = HELPER.read_bytes()
    ast.parse(raw, feature_version=(3, 11))
    spec = importlib.util.spec_from_file_location('_prefix_metadata_fixture', HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    goals = [{'name': 'fixture-' + str(index)} for index in range(32)]
    slots = [{'role': role, 'max_model_calls': budget, 'goal': goal['name']}
             for role in ('saved-corrected', 'new-frontier') for budget in (8, 16) for goal in goals]
    # This object is passed only to the new pure aggregation routine, never
    # to bind_evaluation/verify_checkpoint or any original production API.
    plan = SimpleNamespace(proposal={'ordered_slots': slots}, goals=goals)
    rows = []
    for slot in slots:
        ordinal = int(slot['goal'].split('-')[-1])
        positive = (ordinal in (0, 1, 3) if slot['role'] == 'saved-corrected' else ordinal in (0, 2))
        unknown = slot['role'] == 'new-frontier' and ordinal == 1
        rows.append({'goal': slot['goal'], 'kernel_checked': positive, 'status': 'limited' if unknown else 'exhausted',
            'model_generate_calls': 3 if positive or unknown else slot['max_model_calls'],
            'generation': {key: 0 for key in ('candidate_sequences_requested', 'candidate_sequences_returned',
                'candidate_lines_returned', 'malformed_sequences_rejected', 'authority_sequences_rejected')},
            'evidence': {'search': {'diagnostics': []}},
            'resources': {key: 0 for key in ('goal_wall_seconds', 'goal_cpu_seconds', 'process_peak_rss_bytes',
                'cuda_peak_allocated_bytes')}})
    def aggregate(count, inflight=None):
        return module.prefix_metrics(plan, rows[:count], {'completed_goal_records': count, 'inflight': inflight,
            'inflight_model_generate_calls': None if inflight else 0, 'verification_complete': count == 128 and inflight is None})
    checks = ['python311-syntax-without-production-imports']
    early = aggregate(95, {'ordinal': 96})
    assert early['comparisons'][0]['gains'] is None and early['comparisons'][1]['gains'] is None
    assert early['comparisons'][0]['comparison_status'] == 'incomplete-no-paired-score'
    assert early['inflight'] == {'ordinal': 96} and early['inflight_model_generate_calls'] is None
    checks.append('95-row-prefix-does-not-cherry-pick31-matched-goals')
    full8 = aggregate(96)
    comparison = full8['comparisons'][0]
    assert comparison['all_64_matched_rows_present'] and comparison['gains'] == ['fixture-2']
    assert comparison['losses'] == ['fixture-3'] and comparison['unknown_pair_goals'] == ['fixture-1']
    assert comparison['net_gain_among_known_pairs'] == 0 and comparison['known_paired_goals'] == 31
    checks.append('96-row-prefix-reports-complete32-goal8-call-comparison-with-unknown-pair')
    new16 = [lane for lane in full8['lanes'] if lane['role'] == 'new-frontier' and lane['max_model_calls'] == 16][0]
    assert new16['committed_goal_records'] == 0 and new16['missing_unknown_goal_records'] == 32
    assert new16['known_unproved_within_budget'] == 0 and new16['independently_verified_proofs'] == 0
    assert full8['comparisons'][1]['gains'] is None and full8['all128_comparison_complete'] is False
    assert full8['missing_unknown_goal_records'] == 32
    checks.append('unstarted-new16-is32-unknown-and-no16-call-paired-score')
    assert aggregate(0)['comparisons'][0]['gains'] is None
    assert all(lane['unknown_outcomes_including_missing'] == 32 for lane in aggregate(0)['lanes'])
    checks.append('empty-prefix-has-no-proof-or-paired-score')
    assert aggregate(128)['comparisons'][1]['all_64_matched_rows_present']
    checks.append('all128-needed-for-complete16-call-pairs')
    assert aggregate(128)['all128_comparison_complete'] is False
    assert aggregate(128)['complete_run_wrapper_verified'] is False
    checks.append('checkpoint-prefix-path-never-claims-completed-run-wrapper-verification')
    usage = resource.getrusage(resource.RUSAGE_SELF)
    receipt = {'schema': 'peano-hydra-diagnostic-local-prefix-synthetic-checks-v1', 'status': 'passed',
        'checks': checks, 'check_count': len(checks), 'helper': {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
        'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'resources': {'wall_seconds': time.monotonic()-started, 'cpu_seconds': usage.ru_utime+usage.ru_stime,
            'maxrss_bytes': usage.ru_maxrss}, 'network_used': False, 'model_loaded': False, 'native_proofs_executed': False,
        'production_apis_executed': False, 'bound_plan_or_checked_request_fabricated': False,
        'fixture_rows_are_real_results': False, 'production_files_changed': False}
    result = json.dumps(receipt, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'
    with args.output.open('xb') as stream:
        stream.write(result)
    signal.alarm(0)
    print(json.dumps({'receipt': str(args.output), 'sha256': hashlib.sha256(result).hexdigest(), **receipt}, sort_keys=True))


if __name__ == '__main__':
    main()
