"""One bounded, theorem-only test of the existing local Hybrid server."""

from pathlib import Path
import hashlib
import json
import re
import signal
import sys
import time

ROOT = Path('/Users/bnaskrecki/codex/peano')
APP = ROOT / 'hydra-playground'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

import worker
from evaluate_hybrid import (Client, StopRequested, TERMINAL, cancel_owned,
                             classify, descriptor, metrics, utc_now, write_json)


def stop(signum, _frame):
    raise StopRequested('Received signal ' + str(signum))


def main():
    record_path = OUT / 'result.json'
    # Refuse accidental resubmission or replacement of an earlier result.
    with record_path.open('x', encoding='utf-8') as stream:
        stream.write('{"outcome":"preparing","submission_count":0}\n')
    statement_path = ROOT / 'output/hydra-formulas-2026-09-01/fermat-little-expanded.txt'
    raw = statement_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'bbdcd48ca91907c9246db6ab0b16c42701dd287817826e0e3ce120f76805cc03'
    request = {'theorem': raw.decode('utf-8'), 'search_mode': 'hybrid',
               'max_model_calls': 16, 'beam_width': 4}
    worker.validate_request('search', request)
    validate_statement, *_ = worker.load_kernel()
    canonical = validate_statement(request['theorem'])
    source_paths = ['worker.py', 'server.py', 'hybrid_search.py', 'hybrid_runtime.py',
                    'model_runtime.py', 'vampire_bridge.py', 'vampire_process.py',
                    'vampire_worker.py', 'evaluate_hybrid.py',
                    '.runtime/model/manifest.json', '.runtime/vampire/manifest.json']
    pins_before = {name: descriptor(APP / name) for name in source_paths}
    record = {'schema': 'hydra-fermat-hybrid-test-v1', 'request': request,
              'canonical_theorem': canonical, 'input': descriptor(statement_path),
              'runner': descriptor(Path(__file__)), 'source_pins_before': pins_before,
              'started_at_utc': utc_now(), 'submission_count': 0,
              'automatic_retry': False, 'training_performed': False,
              'proof_supplied': False, 'remote_gpu_jobs': 0,
              'kernel_verified': False, 'outcome': 'preflight', 'progress_samples': []}
    write_json(record_path, record)
    client = Client('http://127.0.0.1:8767')
    started = time.monotonic()
    deadline = started + 200.0
    identifier = None
    terminal = False
    for event in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM):
        signal.signal(event, stop)
    signal.setitimer(signal.ITIMER_REAL, 200.0)
    try:
        code, status = client.request('GET', '/api/status', deadline)
        assert code == 200 and status.get('ok') is True
        assert status.get('computation_active') is False, 'Another computation is active; leaving it untouched.'
        assert status.get('search_modes', {}).get('hybrid', {}).get('available') is True
        client.token = status['csrf_token']
        record['preflight'] = {key: value for key, value in status.items() if key != 'csrf_token'}
        record.update(outcome='submitting', submission_count=1)
        write_json(record_path, record)
        code, body = client.request('POST', '/api/search', deadline, request)
        record.update(submission_http_status=code, submission_response=body)
        assert code == 202 and body.get('ok') is True, 'Submission rejected: ' + str(body.get('error'))
        identifier = body.get('job_id')
        assert isinstance(identifier, str) and re.fullmatch(r'[0-9a-f]{32}', identifier)
        record.update(job_id=identifier, outcome='running')
        write_json(record_path, record)
        print(json.dumps({'job_id': identifier, 'mode': 'hybrid', 'max_model_calls': 16,
                          'beam_width': 4, 'input_bytes': len(raw)}), flush=True)
        next_notice = 0.0
        while time.monotonic() < deadline:
            job = client.job(identifier, deadline)
            record['last_job'] = job
            record['metrics'] = metrics(job)
            if job['state'] in TERMINAL:
                terminal = True
                record.update(classify({'expected': 'provable', 'input_supported': True}, job, canonical))
                break
            now = time.monotonic()
            if now >= next_notice:
                progress = job.get('progress') or {}
                sample = {'elapsed_seconds': round(now - started, 3),
                          'phase': progress.get('phase'),
                          'message': progress.get('message'),
                          'counters': record['metrics']['values']}
                record['progress_samples'].append(sample)
                write_json(record_path, record)
                print(json.dumps(sample), flush=True)
                next_notice = now + 15.0
            time.sleep(min(0.75, max(0.0, deadline - time.monotonic())))
        if not terminal:
            record.update(outcome='client_timeout', error='The 200-second client deadline was reached.')
    except (Exception, KeyboardInterrupt) as error:
        record.update(outcome='runner_error', error=type(error).__name__ + ': ' + str(error))
        if identifier is None and record['submission_count'] == 1:
            record['submission_outcome_unknown'] = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 10.0)
        if identifier is not None and not terminal:
            record['cleanup'] = cancel_owned(client, identifier, time.monotonic() + 8.0)
            last = record['cleanup'].get('terminal_job')
            if isinstance(last, dict):
                record['last_job_after_cancel'] = last
                record['metrics'] = metrics(last)
        signal.setitimer(signal.ITIMER_REAL, 0)
        record['finished_at_utc'] = utc_now()
        record['client_elapsed_seconds'] = round(time.monotonic() - started, 4)
        record['source_pins_after'] = {name: descriptor(APP / name) for name in source_paths}
        record['source_pins_unchanged'] = pins_before == record['source_pins_after']
        try:
            code, status = client.request('GET', '/api/status', time.monotonic() + 8.0)
            record['postflight'] = {'http_status': code, 'ok': status.get('ok'),
                                    'computation_active': status.get('computation_active')}
        except Exception as error:
            record['postflight'] = {'error': str(error)}
        record['exit_observation'] = 'Observe the actual outer process exit; this record alone is not completion.'
        write_json(record_path, record)
        print(json.dumps({'outcome': record['outcome'], 'kernel_verified': record['kernel_verified'],
                          'client_elapsed_seconds': record['client_elapsed_seconds'],
                          'metrics': record.get('metrics'), 'postflight': record['postflight'],
                          'source_pins_unchanged': record['source_pins_unchanged'],
                          'record': str(record_path)}), flush=True)
    return 0 if (record['outcome'] in {'proved', 'unknown'}
                 and record['source_pins_unchanged']
                 and record['postflight'].get('computation_active') is False) else 1


if __name__ == '__main__':
    raise SystemExit(main())
