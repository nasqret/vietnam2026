#!/usr/bin/env python3
"""Synthetic local metadata/archive tests only; no SSH, model or proof run."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import resource
import signal
import sys
import tarfile
import tempfile
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-model-test-2026-08-30')
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('synthetic checks wall cap')))
signal.alarm(15)
names = ('collect-diagnostic-remote-01.py', 'collect-diagnostic-results-01.py', 'report-diagnostic-results-01.py')
raws = {name: (ARCHIVE / name).read_bytes() for name in names}
for name, raw in raws.items():
    ast.parse(raw, feature_version=(3, 9) if 'remote' in name else (3, 11))


def load(name):
    spec = importlib.util.spec_from_file_location('_synthetic_' + name.replace('-', '_').replace('.', '_'), ARCHIVE / name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


collector = load('collect-diagnostic-results-01.py')
reporter = load('report-diagnostic-results-01.py')
assert hashlib.sha256(raws['collect-diagnostic-remote-01.py']).hexdigest() == collector.REMOTE_HELPER_SHA
job, approval, evaluation = '999999', 'a' * 64, 'b' * 64
payload = b'{"synthetic_only":true}\n'
index = {'schema': 'peano-hydra-diagnostic-terminal-collection-index-v1',
    'binding': {'job_id': job, 'approval_sha256': approval, 'evaluation_request_sha256': evaluation,
        'source_commit': '612d1ea9e4905dfe2af104696924a19bc5883752', 'reserved_gpu_seconds': 900},
    'files': {'run.json': {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}},
    'total_file_bytes': len(payload), 'proofs_independently_verified': False,
    'model_weights_read_or_downloaded': False, 'synthetic_only': True}


def archive_bytes(member_name='run.json', body=payload, symbolic=False):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        data = collector.canonical(index) + b'\n'
        header = tarfile.TarInfo('collection-index.json')
        header.size = len(data)
        archive.addfile(header, io.BytesIO(data))
        member = tarfile.TarInfo(member_name)
        member.size = len(body)
        if symbolic:
            member.type, member.linkname, member.size = tarfile.SYMTYPE, '../outside', 0
        archive.addfile(member, io.BytesIO(body))
    return buffer.getvalue()


checks = {'python39_remote_and_python311_local_syntax': True, 'remote_program_pin_matches': True}
with tempfile.TemporaryDirectory(prefix='hydra-result-tools-synthetic-') as temporary:
    root = Path(temporary).resolve()
    good = root / 'good'; good.mkdir()
    assert collector.extract(archive_bytes(), good, job, approval, evaluation) == index
    assert (good / 'run.json').read_bytes() == payload
    checks['allowlisted_archive_roundtrip_exact_bytes'] = True
    for ordinal, sample in enumerate((archive_bytes('../outside'), archive_bytes(symbolic=True),
                                    archive_bytes(body=b'X' * len(payload)))):
        target = root / str(ordinal); target.mkdir()
        try:
            collector.extract(sample, target, job, approval, evaluation)
        except (ValueError, tarfile.TarError):
            pass
        else:
            raise AssertionError('unsafe archive fixture accepted')
    assert not (root / 'outside').exists()
    checks['archive_traversal_links_and_changed_hashes_rejected'] = True
    owner = root / 'untrusted-owner'; owner.mkdir()
    value = {'schema': 'peano-hydra-diagnostic-portable-local-verification-owner-v1',
        'status': 'verified-within-whole-call-envelope', 'error': None, 'helper_sha256': '0' * 64}
    raw = collector.canonical(value)
    (owner / 'owner-result.json').write_bytes(raw)
    try:
        reporter.verified_inputs(good, {}, owner, hashlib.sha256(raw).hexdigest())
    except ValueError:
        pass
    else:
        raise AssertionError('untrusted verifier helper accepted')
    checks['wrong_verification_helper_rejected_before_report_scoring'] = True

goals = [{'name': 'synthetic_g%02d' % index} for index in range(32)]
slots = [{'role': role, 'max_model_calls': budget, 'goal': goal['name']}
         for role in reporter.ROLES for budget in reporter.BUDGETS for goal in goals]
rows = []
for slot in slots:
    row = {'goal': slot['goal'], 'status': 'exhausted', 'kernel_checked': False, 'model_generate_calls': 0,
        'generation': {'candidate_sequences_requested': 0, 'candidate_sequences_returned': 0,
            'candidate_lines_returned': 0, 'malformed_sequences_rejected': 0, 'authority_sequences_rejected': 0},
        'evidence': {'search': {'diagnostics': []}},
        'resources': {'goal_wall_seconds': 0.0, 'goal_cpu_seconds': 0.0, 'process_peak_rss_bytes': 0,
            'cuda_peak_allocated_bytes': 0, 'cuda_peak_reserved_bytes': 0},
        'synthetic_only': 'unit aggregation fixture; not a proof or model result'}
    if slot['max_model_calls'] == 8:
        proof = ((slot['role'] == 'saved-corrected' and slot['goal'] in ('synthetic_g00', 'synthetic_g02'))
                 or (slot['role'] == 'new-frontier' and slot['goal'] == 'synthetic_g01'))
        if proof:
            row.update(status='proof', kernel_checked=True, model_generate_calls=1)
            row['generation'].update(candidate_sequences_requested=4, candidate_sequences_returned=4,
                                     candidate_lines_returned=4)
        if slot['role'] == 'new-frontier' and slot['goal'] == 'synthetic_g00':
            row.update(status='limit', model_generate_calls=1)
    rows.append(row)
lanes, pairs = reporter.aggregate({'evaluation_plan': {'ordered_slots': slots, 'goals': goals}}, rows)
assert pairs[0]['gains'] == ['synthetic_g01'] and pairs[0]['losses'] == ['synthetic_g02']
assert pairs[0]['unknown_pairs'] == 1 and pairs[0]['known_paired_goals'] == 31
assert pairs[1]['gains'] == pairs[1]['losses'] == []
assert lanes[0]['independently_verified_proofs'] == 2 and lanes[1]['independently_verified_proofs'] == 1
assert lanes[1]['unknown_outcomes'] == 1
assert reporter.outcome({'kernel_checked': False, 'status': 'limit', 'model_generate_calls': 8}, 8) == 'call-limit'
assert reporter.outcome({'kernel_checked': False, 'status': 'limit', 'model_generate_calls': 7}, 8) == 'unknown'
checks['synthetic_unknown_pairs_never_count_as_losses'] = True
checks['same_budget_paired_gains_losses_and_call_limits'] = True
assert not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules)
assert not any(name.startswith(('training.', 'peano_lab')) for name in sys.modules)
assert all((ARCHIVE / name).read_bytes() == raw for name, raw in raws.items())
usage = resource.getrusage(resource.RUSAGE_SELF)
result = {'schema': 'peano-hydra-diagnostic-result-tools-synthetic-checks-v1', 'status': 'passed',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
    'sources': {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in raws.items()},
    'resources': {'cpu_seconds': usage.ru_utime + usage.ru_stime, 'wall_seconds': time.monotonic() - STARTED,
                  'maxrss_bytes': usage.ru_maxrss},
    'limits': {'cpu_seconds': 10, 'wall_seconds': 15, 'checked_peak_rss_bytes': 256 * 1024**2},
    'native_proofs_replayed': 0, 'model_loaded': False, 'ssh_or_scheduler_called': False,
    'real_results_scored': False, 'human_approval_created': False}
assert result['resources']['cpu_seconds'] < 10 and result['resources']['wall_seconds'] < 15
assert usage.ru_maxrss < 256 * 1024**2
collector.write(ARCHIVE / 'diagnostic-result-tools-checks-01.json', collector.canonical(result) + b'\n')
signal.alarm(0)
print(json.dumps(result, sort_keys=True))
