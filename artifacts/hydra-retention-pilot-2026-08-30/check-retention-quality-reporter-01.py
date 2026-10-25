"""Targeted in-memory reporter fixtures; no production result is generated."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import sys
import time
import types

started = time.monotonic()
A = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
P = A / 'report-retention-quality-01.py'
EXPECTED = 'f5e4ef4a3ae572ab74555469fc2b7eba69844852cb5dc1e366661541eabfdc59'
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('reporter pure fixture wall cap')))
signal.alarm(20)


def audit(event, args):
    if event.startswith(('subprocess.', 'os.system', 'os.posix_spawn', 'socket.')):
        raise RuntimeError('reporter fixtures cannot execute any child/network work')
    if event == 'import' and args[0].split('.')[0] in {'training', 'peano_lab', 'torch', 'transformers', 'peft', 'tokenizers'}:
        raise RuntimeError('reporter fixtures cannot import scientific or model execution')


sys.addaudithook(audit)
raw = P.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
ast.parse(raw, feature_version=(3, 11)); compile(raw, str(P), 'exec')
spec = importlib.util.spec_from_file_location('retention_reporter_projection_fixture', P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(known):
    # Only a synthetic summary *shape* for the new table projection. No original
    # BoundEvaluation, proof receipt, actual job or successful admission exists.
    metrics = {'schema': 'peano-hydra-retention-evaluation-metadata-v1',
        'status': 'metadata-only-not-independent-proof-verification', 'proof_replay_performed': False,
        'partial_pairs_scored': False, 'completed_goal_records': 256 if known else 0,
        'missing_unknown_goal_records': 0 if known else 256, 'all256_records_present': known, 'cohorts': {},
        **{key: value for key, value in m.CLAIMS.items() if key != 'historical_gpu_inference_attested'}}
    for cohort in m.COHORTS:
        lanes, comparisons = [], []
        for budget in m.BUDGETS:
            for role in m.ROLES:
                lanes.append({'role': role, 'max_model_calls': budget, 'planned_goals': 32,
                    'committed_goal_records': 32 if known else 0, 'reported_proofs': 0,
                    'unknown_outcomes_including_missing': 0 if known else 32,
                    'missing_unknown_goal_records': 0 if known else 32, 'known_unproved_within_budget': 32 if known else 0,
                    'reported_proof_fraction_if_all_known': 0.0 if known else None,
                    'committed_model_generate_calls': budget * 32 if known else 0,
                    'malformed_sequences_rejected': 0, 'authority_sequences_rejected': 0})
            comparisons.append({'max_model_calls': budget, 'all64_matched_rows_present': known,
                'known_paired_goals': 32 if known else None, 'unknown_pair_goals': [] if known else None,
                'reported_gains': [] if known else None, 'reported_losses': [] if known else None})
        metrics['cohorts'][cohort] = {'lanes': lanes, 'matched_comparisons': comparisons}
    return metrics, {'rows': [None] * (256 if known else 0), 'positive_replay_joins': []}


checks = ['python311_syntax_without_reporter_invocation']
metrics, joined = fixture(False)
table = m.table_from_frozen_metrics(metrics, joined)
assert len(table) == 4 and all(row['paired_wins'] is None and row['paired_losses'] is None for row in table)
assert all(arm['successes_out_of_32'] is None and arm['success_fraction'] is None
           for row in table for arm in row['arms'].values())
checks.append('missing_all_lanes_remains_unknown_never_zero')

metrics, joined = fixture(True)
table = m.table_from_frozen_metrics(metrics, joined)
assert all(row['paired_wins'] == row['paired_losses'] == 0 for row in table)
assert all(arm['successes_out_of_32'] == 0 and arm['success_fraction'] == 0.0
           for row in table for arm in row['arms'].values())
checks.append('fully_known_zero_is_distinct_from_missing')

metrics, joined = fixture(True)
lane = next(item for item in metrics['cohorts']['retention-dev32']['lanes']
            if item['role'] == 'mixed-retention' and item['max_model_calls'] == 8)
lane.update(unknown_outcomes_including_missing=1, known_unproved_within_budget=31,
            reported_proof_fraction_if_all_known=None)
comparison = metrics['cohorts']['retention-dev32']['matched_comparisons'][0]
comparison.update(known_paired_goals=31, unknown_pair_goals=['synthetic-unresolved-goal'])
row = m.table_from_frozen_metrics(metrics, joined)[0]
assert row['paired_wins'] is None and row['paired_losses'] is None
assert row['arms']['mixed-retention']['successes_out_of_32'] is None
checks.append('one_unresolved_pair_hides_partial_wins_and_losses')

metrics, joined = fixture(True)
metrics['cohorts']['retention-dev32']['lanes'][0]['reported_proofs'] = 1
try: m.table_from_frozen_metrics(metrics, joined)
except ValueError as error: assert 'proof count' in str(error)
else: raise AssertionError('unjoined positive proof count was admitted')
checks.append('reported_positive_without_actual_replay_join_rejected')

# A deliberately failing metadata-only fixture checks rejection at the first
# native-receipt/HEAD join. No passing native result is constructed or invoked.
authorization = {'synthetic': True}
header = {'header_sha256': 'a' * 64, 'authorization_sha256': m.digest(authorization),
          'authorization': authorization, 'plan': {'plan_sha256': 'b' * 64}}
head = {'head_sha256': 'c' * 64}
base = types.SimpleNamespace(read_json=lambda path, pin: (header if path.name == 'header.json' else head, b'{}'))
verifier = types.SimpleNamespace(EVALUATION_COLLECTION=Path('/synthetic-only'))
request = {'checkpoint_head_sha256': 'd' * 64, 'authorization_sha256': m.digest(authorization)}
collected = {'evaluation': {'index': {'files': {'checkpoint/header.json': {'sha256': 'e' * 64}}}}}
original = {'schema': 'peano-hydra-retention-evaluation-verification-v1', 'status': 'native-prefix-verified',
    'proof_replay_performed': True, 'model_outputs_regenerated': False, 'total_goal_records': 256,
    'checkpoint_head_sha256': 'f' * 64, 'checkpoint_header_sha256': 'a' * 64, 'plan_sha256': 'b' * 64}
try: m.join_positive_replays(base, verifier, request, collected, original, {})
except ValueError as error: assert 'native verification/HEAD/header/authorization' in str(error)
else: raise AssertionError('native receipt from another HEAD was admitted')
checks.append('native_receipt_from_different_head_rejected')
assert P.read_bytes() == raw
assert not m.OUTPUT.exists(), 'fixture must never create an actual quality report'
usage = resource.getrusage(resource.RUSAGE_SELF)
record = {'schema': 'peano-hydra-retention-quality-reporter-checks-v1', 'status': 'passed',
    'helper': {'path': str(P), 'bytes': len(raw), 'sha256': EXPECTED}, 'checks': checks,
    'only_synthetic_projection_and_rejection_fixtures': True, 'production_quality_report_generated': False,
    'reporter_main_or_render_called': False, 'original_core_validator_called': False,
    'actual_verification_model_native_network_scheduler_or_observer_work': False,
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - started,
                  'peak_rss_bytes': usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024}}
receipt = m.canonical(record) + b'\n'
output = A / 'quality-reporter-helper-checks-01.json'
with output.open('xb') as stream: stream.write(receipt)
print(json.dumps({'status': 'passed', 'checks': len(checks), 'receipt': str(output), 'sha256': m.sha(receipt)}, sort_keys=True))
