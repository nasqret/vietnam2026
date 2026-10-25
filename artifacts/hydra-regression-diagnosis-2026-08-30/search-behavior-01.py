"""Count behavior in the already verified eight-call traces; no model/proof work."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import time

started = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
ROOT = Path('/Users/bnaskrecki/codex/peano')
TEST = ROOT / 'artifacts/hydra-model-test-2026-08-30'
OUT = ROOT / 'artifacts/hydra-regression-diagnosis-2026-08-30'
DATA = TEST / 'diagnostic-checkpoint-collected-01'


def read(path, expected_sha):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha
    return json.loads(raw)


owner = read(TEST / 'diagnostic-prefix-verification-01/owner-result.json',
             '53b2fe67f6bcbba5dc20106b71b11862dc1a583036a10d566a6e8a698becadac')
assert owner['status'] == 'prefix-verified-within-whole-call-envelope'
receipt = read(DATA / 'collection-receipt.json',
               'ee866f7cdb19008f71959abc9b8309b7eec728aba2c8482a811dde5364f5a5a0')
lanes = {}
for role, numbers in [('old', range(1, 33)), ('new', range(65, 97))]:
    heads, depths, calls, frontiers, native, outcomes = (Counter() for _ in range(6))
    states = multiple = proposals = 0
    for ordinal in numbers:
        name = f'checkpoint/{ordinal:06d}.goal.json'
        row = read(DATA / name, receipt['files'][name]['sha256'])['row']
        search = row['evidence']['search']
        assert row['model_generate_calls'] <= 8
        depths[search['depth_reached']] += 1
        calls[row['model_generate_calls']] += 1
        frontiers[search['frontier_peak']] += 1
        states += search['states_discovered']
        outcomes[row['status']] += 1
        for proposal in row['evidence']['proposal_records']:
            proposals += 1
            multiple += len(proposal['goals']) > 1
            heads.update(command.split()[0] for command in proposal['candidates'])
        native.update(item['kind'] for item in search['diagnostics'])
    lanes[role] = {
        'goals': 32, 'max_model_calls_per_goal': 8,
        'proposal_heads': dict(heads.most_common()),
        'depth_histogram': dict(sorted(depths.items())),
        'model_call_histogram': dict(sorted(calls.items())),
        'frontier_peak_histogram': dict(sorted(frontiers.items())),
        'states_discovered': states, 'proposal_calls': proposals,
        'calls_with_multiple_goals': multiple,
        'retained_native_diagnostics': dict(native), 'outcomes': dict(outcomes),
    }

usage = resource.getrusage(resource.RUSAGE_SELF)
record = {
    'schema': 'peano-hydra-regression-retained-search-analysis-v1',
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'read-only-analysis-of-verified-eight-call-rows',
    'job_id': '21453693', 'lanes': lanes,
    'collection_receipt_sha256': 'ee866f7cdb19008f71959abc9b8309b7eec728aba2c8482a811dde5364f5a5a0',
    'verification_owner_sha256': '53b2fe67f6bcbba5dc20106b71b11862dc1a583036a10d566a6e8a698becadac',
    'analysis_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'search_source_sha256': hashlib.sha256((ROOT / '_deploy/hydra-model-test-execution-20260830/training/peano_policy/search.py').read_bytes()).hexdigest(),
    'mechanism': 'The search expands each frontier layer before the next depth. Each expanded state consumes one model call, so extra viable branches consume the eight-call budget before a direct route reaches its closing steps.',
    'limits': [
        'This is observational trace analysis, not a causal intervention or a new model evaluation.',
        'Native diagnostic lists are capped at 128 records per goal; counts describe retained events.',
        'The candidate sixteen-call pass is unstarted and unknown.',
    ],
    'model_loaded': False, 'native_proof_executed': False, 'network_used': False,
    'frozen_evidence_changed': False,
    'resources': {'wall_seconds': time.monotonic() - started,
                  'cpu_seconds': usage.ru_utime + usage.ru_stime,
                  'maxrss_bytes': usage.ru_maxrss},
}
raw = (json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
with (OUT / 'search-behavior-01.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'path': str(OUT / 'search-behavior-01.json'), 'bytes': len(raw),
                  'sha256': hashlib.sha256(raw).hexdigest(), 'status': record['status']}))
