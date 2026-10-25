"""Summarize already verified diagnostic evidence; no inference or proof work."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-model-test-2026-08-30'
COLLECTED = ARCHIVE / 'diagnostic-checkpoint-collected-01'
VERIFIED = ARCHIVE / 'diagnostic-prefix-verification-01'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load(path, expected_sha):
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha
    return json.loads(raw)


def write_new(path, value):
    raw = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    with path.open('x') as stream:
        stream.write(raw)
    return pin(path)


owner = load(VERIFIED / 'owner-result.json', '53b2fe67f6bcbba5dc20106b71b11862dc1a583036a10d566a6e8a698becadac')
verification = load(VERIFIED / 'verification.json', '8cfa3a299800fc9afbef248d290c6e01db132aa99f9b31983e4bc3756aefc470')
collection = load(COLLECTED / 'collection-receipt.json', 'ee866f7cdb19008f71959abc9b8309b7eec728aba2c8482a811dde5364f5a5a0')
assert owner['status'] == 'prefix-verified-within-whole-call-envelope' and owner['error'] is None
assert owner['verification_file'] == {key: pin(VERIFIED / 'verification.json')[key] for key in ('bytes', 'sha256')}
assert verification['verification']['status'] == 'native-prefix-verified'
assert verification['verification']['completed_goal_records'] == 96
assert verification['verification']['verification_complete'] is False
assert len(verification['verification']['independently_replayed_proofs']) == 14
assert verification['full_comparison_verification_complete'] is False
assert verification['metrics']['comparisons'][0]['all_64_matched_rows_present'] is True
assert verification['metrics']['comparisons'][0]['unknown_pair_goals'] == []
assert verification['metrics']['comparisons'][1]['all_64_matched_rows_present'] is False

header = load(COLLECTED / 'checkpoint/header.json', collection['files']['checkpoint/header.json']['sha256'])
slots = header['plan']['evaluation_plan']['ordered_slots']
rows = []
for ordinal in range(1, 97):
    name = f'checkpoint/{ordinal:06d}.goal.json'
    row = load(COLLECTED / name, collection['files'][name]['sha256'])['row']
    assert row['goal'] == slots[ordinal - 1]['goal']
    rows.append(row)

families = []
for family in ('disjunction', 'universal'):
    item = {'family': family, 'goals': 16, 'max_model_calls': 8}
    for role in ('saved-corrected', 'new-frontier'):
        chosen = [row for slot, row in zip(slots, rows) if slot['role'] == role
                  and slot['max_model_calls'] == 8 and f'_{family}_diagnostic_' in row['goal']]
        assert len(chosen) == 16
        item[role] = sum(row['kernel_checked'] for row in chosen)
    families.append(item)

lanes = {(lane['role'], lane['max_model_calls']): lane for lane in verification['metrics']['lanes']}
old, new = lanes[('saved-corrected', 8)], lanes[('new-frontier', 8)]
assert old['independently_verified_proofs'] == 7 and new['independently_verified_proofs'] == 0
assert sum(item['saved-corrected'] for item in families) == 7
assert sum(item['new-frontier'] for item in families) == 0
assert [item['saved-corrected'] for item in families] == [6, 1]
assert lanes[('saved-corrected', 16)]['independently_verified_proofs'] == 7
assert lanes[('new-frontier', 16)]['missing_unknown_goal_records'] == 32

quality = {
    'schema': 'peano-hydra-verified-dev-quality-summary-v1',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'verified-regression-at-eight-model-calls',
    'job_id': '21453693',
    'cohort': 'review-candidate-dev',
    'source_commit': '612d1ea9e4905dfe2af104696924a19bc5883752',
    'portable_plan_sha256': verification['portable_plan_sha256'],
    'models': {'saved-corrected': 'v25 corrected baseline', 'new-frontier': 'v28 newly trained frontier adapter'},
    'matched_eight_call_result': {
        'goals': 32, 'old_proved': 7, 'new_proved': 0,
        'old_fraction': 7 / 32, 'new_fraction': 0.0,
        'change_percentage_points': -100 * 7 / 32,
        'gains': 0, 'losses': 7, 'neither_proved': 25, 'unknown_pairs': 0,
        'family_breakdown': families,
        'comparison': verification['metrics']['comparisons'][0],
    },
    'verified_prefix_metrics': verification['metrics'],
    'positive_proof_records_independently_replayed': 14,
    'all_96_retained_rows_metadata_validated': True,
    'all_128_requested_rows_complete': False,
    'new_sixteen_call_result': 'unstarted; all 32 outcomes unknown',
    'scheduler': {key: collection['accounting'][key] for key in ('state', 'exit_code', 'elapsed_seconds')},
    'stop': 'Planned safety deadline, clean checkpoint boundary, no inflight goal.',
    'reservation_gpu_seconds_consumed': 900,
    'automatic_retry': False, 'resume': False, 'training_performed': False,
    'promotion_recommended': False,
    'benchmark_acceptance_eligible': False, 'unseen_test_generalization_established': False,
    'diagnosis': {
        'observations': [
            'New model: 29 call-limit outcomes and three exhausted searches at eight calls.',
            'Both models record zero malformed decoder sequences; two of 988 new-model sequences fail authority checks.',
            'Recorded duplicate-state events: 244 old, 434 new; beam-pruning events: three old, 28 new.',
            'The new disjunction_019 trace opens induction and an auxiliary universal subgoal instead of completing the old six-call proof.',
        ],
        'interpretation': 'The retained traces point to poor tactic selection and unproductive search branches. The training root cause is not established.',
        'limitations': 'Native diagnostic lists are capped at 128 entries per goal; counts are retained events, not an uncapped error-rate estimate.',
        'representative_old_row': pin(COLLECTED / 'checkpoint/000003.goal.json'),
        'representative_new_row': pin(COLLECTED / 'checkpoint/000067.goal.json'),
    },
    'claim_limits': [
        'Only 32 public, correlated DEV goals from two families; no unseen or sealed benchmark claim.',
        'This is a complete matched eight-call comparison within a partial 128-row experiment.',
        'The new sixteen-call pass is unmeasured, not a failed 0/32 result.',
        'Recorded goal resource totals exclude setup, model loading and other allocation overhead.',
        'Native replay verifies retained proofs; it does not regenerate model outputs or attest historical GPU inference.',
    ],
    'evidence': {name: pin(path) for name, path in {
        'collection_receipt': COLLECTED / 'collection-receipt.json',
        'verification': VERIFIED / 'verification.json',
        'owner_result': VERIFIED / 'owner-result.json',
        'summary_source': Path(__file__),
    }.items()},
}
quality_pin = write_new(ARCHIVE / 'quality-summary-01.json', quality)

report = '''# Hydra model test — 2026-08-30

**The newly trained v28 adapter regressed at the tested eight-call budget:
0/32 goals solved, versus 7/32 (21.875%) for the corrected v25 baseline.**
There were seven paired losses, no gains, and 25 goals solved by neither model.
Do not promote this checkpoint on these results.

| Eight-call comparison | Old v25 | New v28 |
|---|---:|---:|
| Disjunction goals | 6/16 | 0/16 |
| Universal goals | 1/16 | 0/16 |
| All goals | **7/32 (21.875%)** | **0/32 (0%)** |
| Total model calls | 212 | 247 |
| Recorded goal time, excluding setup/loading | 78.31 s | 162.70 s |

These are 32 public, correlated DEV goals, not an unseen or sealed benchmark.
Both models used the same goals, search profile, eight-call ceiling, depth 16,
beam width four, four candidates per state, 64-state limit, 64 output tokens,
and seed 20260826. The result establishes a regression at this budget; it does
not establish general model accuracy or performance at larger budgets.

The unchanged native checkpoint verifier validated all 96 retained outcome
records and independently replayed all 14 positive proof records: seven old
proofs at eight calls and seven old proofs at 16 calls. Verification completed
in 31.565 wall seconds within the existing resource envelope. The full 128-row
experiment remains incomplete. The original verification and complete-run
flags have not been changed to claim otherwise.

The run stopped at the planned safety deadline after 719 seconds on one GH200,
with eight CPUs and 64 GiB requested. Slurm records FAILED / 0:10; the application
records a clean CheckpointPaused boundary with no inflight goal. The new model's
16-call pass never started: all 32 of those outcomes are **unknown**, not zero
successes. The old model separately scored 7/32 at 16 calls, but there is no
matched 16-call comparison. No retraining, resume, resubmission or automatic
retry occurred. The full 900-second reservation remains consumed.

The new model reached the call limit on 29 goals and exhausted search on three.
Both models recorded zero malformed decoder sequences, and only two of 988 new
sequences failed authority checks. The new search recorded more duplicate states
(434 versus 244) and more beam pruning (28 versus three). These are retained
diagnostic counts, capped at 128 entries per goal, rather than uncapped rates.

On disjunction_019, the [old model's saved proof](diagnostic-checkpoint-collected-01/checkpoint/000003.goal.json)
uses `intro n`, `intro m`, `intro h`, `rewrite h`, `left`, `refl` in six calls.
The [new model's trace](diagnostic-checkpoint-collected-01/checkpoint/000067.goal.json)
opens induction and `have hz : forall z. 0 = z` branches, proposes inapplicable
tactics at the direct disjunction, and spends its eight calls without closing
the proof. The recorded prompt contract, authority, decoding and search settings
match; neither row records degradation, a memory error or an infrastructure error.
This points to tactic selection and unproductive branches as the immediate
failure mode. It does not prove the cause in the training data or optimizer.

The next development step is to audit the v28 training examples and action
distribution against these concrete regressions, then design a fresh bounded
comparison that measures the candidate's 16-call behavior. Keep these exposed
DEV cases diagnostic; any later generalization claim requires separate held-out
evaluation. Do not start more training merely because the training loss fell.
Future experiment permission is already recorded in
[HYDRA_EXPERIMENT_AUTHORITY.md](../../HYDRA_EXPERIMENT_AUTHORITY.md); the current
spent run must not be reused.

The future-only progress patch is retained in
[future-diagnostic-progress-01.patch](future-diagnostic-progress-01.patch), with
one focused passing check. It was not deployed into this frozen experiment.

Evidence: [machine-readable quality summary](quality-summary-01.json),
[verification owner receipt](diagnostic-prefix-verification-01/owner-result.json),
[original prefix verification and metrics](diagnostic-prefix-verification-01/verification.json),
[complete checkpoint collection](diagnostic-checkpoint-collected-01/collection-receipt.json),
and [terminal checkpoint](checkpoint-03.json). Source commit
`612d1ea9e4905dfe2af104696924a19bc5883752` remains unchanged.
'''
report_pin = write_new(ARCHIVE / 'RESULT.md', report)

previous_recovery = ROOT / 'RECOVERY.md'
recovery_archive = ARCHIVE / 'RECOVERY-before-diagnostic-result.md'
with recovery_archive.open('xb') as stream:
    stream.write(previous_recovery.read_bytes())

checkpoint = {
    'schema': 'peano-hydra-model-test-verified-prefix-checkpoint-v1',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'bounded-experiment-finished-verified-eight-call-regression',
    'job_id': '21453693', 'scheduler_state': 'FAILED', 'exit_code': '0:10',
    'elapsed_seconds': 719, 'committed_rows': 96, 'requested_rows': 128, 'inflight': None,
    'matched_eight_call_comparison_verified': True,
    'old_eight_call_proofs': 7, 'new_eight_call_proofs': 0, 'paired_goals': 32,
    'full_comparison_verification_complete': False,
    'new_sixteen_call_outcomes': 'all 32 unstarted and unknown',
    'positive_proof_records_independently_replayed': 14,
    'source_commit': quality['source_commit'],
    'portable_plan_sha256': quality['portable_plan_sha256'],
    'automatic_retry': False, 'resume': False, 'training_performed': False,
    'full_900_second_reservation_remains_consumed': True,
    'standing_experiment_authority': pin(ROOT / 'HYDRA_EXPERIMENT_AUTHORITY.md'),
    'result': report_pin, 'quality_summary': quality_pin,
    'prior_checkpoint': pin(ARCHIVE / 'checkpoint-03.json'),
    'previous_recovery': pin(recovery_archive),
    'evidence': quality['evidence'],
    'next_action': 'Keep v25 as the comparison baseline. Audit v28 tactic selection and training examples before any fresh bounded experiment. Do not resume or resubmit this run.',
}
checkpoint_pin = write_new(ARCHIVE / 'checkpoint-04.json', checkpoint)

previous_recovery.write_text('''# Peano / Hydra session recovery — 2026-08-30

The bounded model test is finished and its retained evidence is independently
verified. **At eight model calls per goal, the new v28 adapter solved 0/32 DEV
goals; the corrected v25 baseline solved 7/32 (21.875%).** Seven paired losses,
no gains. Do not promote the new checkpoint on this evidence.

Start with the [result](artifacts/hydra-model-test-2026-08-30/RESULT.md),
[quality summary](artifacts/hydra-model-test-2026-08-30/quality-summary-01.json),
and [checkpoint-04](artifacts/hydra-model-test-2026-08-30/checkpoint-04.json).
All 96 retained rows passed the unchanged original prefix verifier, including
fresh native replay of all 14 positive proof records. Only the 32-goal matched
eight-call comparison is complete. These are public, correlated DEV goals;
unseen-test generalization, benchmark acceptance and self-training readiness
are not established.

Diagnostic job `21453693` is terminal: Slurm FAILED / 0:10, elapsed 719 seconds.
The application stopped at its planned safety deadline at a clean checkpoint
boundary, with 96/128 rows and no inflight goal. Both eight-call passes and the
old 16-call pass were retained. The new 16-call pass never started; its 32
outcomes remain unknown. The full 900-second allocation remains consumed.
**Do not resume, retry or resubmit this run.** No retraining occurred.

The user explicitly said **“You don't have to ask my permission to run new
experiments.”** Follow [HYDRA_EXPERIMENT_AUTHORITY.md](HYDRA_EXPERIMENT_AUTHORITY.md).
This supersedes the older recovered requirement for fresh chat approval before
every Hydra upload or GPU allocation. Record exact source/input/resource limits
and a separate one-use reservation for each fresh experiment. Resource permission
does not replace proof checks or human benchmark review.

Helios control is restored through `plgnasqret@helios.cyfronet.pl`. The diagnostic
deployment is
`/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-diagnostic-v1`.
Its ledger is `logs/hydra-frontier-diagnostic-v1.jsonl`; stdout/stderr are
`logs/peano-hydra-frontier-diagnostic-v1-evaluate-21453693.out` and `.err`.
The checkpoint is under
`results/peano-hydra/evaluations/frontier-diagnostic-v1/checkpoint`.
The full actual checkpoint and logs are preserved locally in
`artifacts/hydra-model-test-2026-08-30/diagnostic-checkpoint-collected-01`.
Verification is in the sibling `diagnostic-prefix-verification-01` directory.
Do not alter the actual checkpoint, its zero-byte lock, or the spent ledger.

The immutable diagnostic snapshot is `_deploy/hydra-model-test-execution-20260830`,
commit `612d1ea9e4905dfe2af104696924a19bc5883752` (877 files). Continue development
only in `_deploy/hydra-frontier-recovery-work-20260830`, preserving its existing
uncommitted work. Future-only progress logging and one focused passing check
are recorded in `future-diagnostic-progress-source-01.json` and the corresponding
patch in the model-test archive; that change was not deployed into this run.

The retained traces point to unproductive tactic choices and auxiliary subgoals.
Audit the v28 training examples/action distribution against the recorded losses
before more training, and design a fresh bounded comparison to measure 16-call
candidate behavior. Keep the old v25 model as the comparison baseline. Existing
full-reference, Lean 4.31, human benchmark review and pilot-acceptance gates stay
open for broader claims.

Training job `21438102` previously completed all 1,597 updates; its saved losses
are not theorem-solving accuracy. Earlier history, exact receipts and continuation
links are preserved in
[RECOVERY-before-diagnostic-result.md](artifacts/hydra-model-test-2026-08-30/RECOVERY-before-diagnostic-result.md),
[the training handoff](artifacts/frontier-training-2026-08-30/CONTINUE_TRAINING.md),
and [the recovered history](artifacts/session-recovery-2026-08-30/RECOVERED_HISTORY.md).
''')

print(json.dumps({'status': 'reported', 'quality_summary': quality_pin,
                  'report': report_pin, 'checkpoint': checkpoint_pin,
                  'recovery': pin(previous_recovery)}, sort_keys=True))
