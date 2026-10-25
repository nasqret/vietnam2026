#!/usr/bin/env python3
"""Small local fixtures only; no project calibration, native proofs or models."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
HELPER = HERE / 'run-v28-hotspots-supervised.py'


def fixture(mode):
    python = str(Path(sys.executable).resolve(strict=True))
    command = [python, '-I', '-B', str(Path(__file__).resolve()), '--fixture']
    if mode == 'normal-leaf':
        print(json.dumps({'role': mode, 'pid': os.getpid(), 'pgid': os.getpgrp()}), flush=True)
        time.sleep(1.3)
        return 0
    if mode == 'normal-child':
        child = subprocess.Popen([*command, 'normal-leaf'], start_new_session=True)
        print(json.dumps({'role': mode, 'pid': os.getpid(), 'child_pid': child.pid}), flush=True)
        time.sleep(0.45)
        # Deliberate orphan fixture: the owner must continue to observe the
        # already-seen leaf after both its original parents have exited.
        return 0
    if mode == 'normal-root':
        child = subprocess.Popen([*command, 'normal-child'], start_new_session=True)
        return child.wait(timeout=4)
    if mode == 'burn-leaf':
        print(json.dumps({'role': mode, 'pid': os.getpid(), 'pgid': os.getpgrp()}), flush=True)
        value = 1
        while True:
            value = (value * 33 + 1) % 10000019
    if mode == 'burn-root':
        children = [subprocess.Popen([*command, 'burn-leaf'], start_new_session=True) for _ in range(2)]
        try:
            while any(child.poll() is None for child in children):
                time.sleep(0.02)
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
            for child in children:
                child.wait(timeout=1)
        return 0
    raise ValueError('unknown fixture')


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--fixture':
        return fixture(sys.argv[2])
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.absolute()
    if output.parent != HERE or output.exists() or output.is_symlink():
        raise ValueError('fresh immediate archive fixture directory required')
    output.mkdir(mode=0o700)
    spec = importlib.util.spec_from_file_location('v28_supervisor_fixture_import', HELPER)
    guard = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = guard
    spec.loader.exec_module(guard)
    helper_before = hashlib.sha256(HELPER.read_bytes()).hexdigest()
    started = datetime.now(timezone.utc).isoformat()
    checks, processes = [], []
    status, error = 'passed', None
    try:
        assert guard.cpu_seconds('1:02.50') == 62.5
        assert guard.cpu_seconds('1-02:03:04.25') == 93784.25
        for value in ('not-time', '1:60.00', '-1:00.00'):
            try:
                guard.cpu_seconds(value)
            except ValueError:
                pass
            else:
                raise AssertionError('malformed ps CPU accepted')
        checks.append('bounded process-table CPU parsing')
        for kwargs in ({'wall_seconds': 301}, {'cpu_seconds': 181}, {'rss_bytes': 3 * 1024**3},
                       {'output_bytes': 65 * 1024**2}, {'cpu_seconds': True}):
            try:
                guard.Limits(**kwargs)
            except ValueError:
                pass
            else:
                raise AssertionError('enlarged resource cap accepted')
        checks.append('production ceilings cannot be enlarged through the engine')
        tree = guard.Ownership(10)
        make = lambda pid, ppid, birth: {'pid': pid, 'ppid': ppid, 'pgid': pid, 'rss_bytes': 1024,
            'cpu_seconds': 0.01, 'state': 'S', 'birth': birth, 'command_name': 'fixture'}
        tree.update({10: make(10, 1, 'root'), 11: make(11, 10, 'old')})
        tree.update({10: make(10, 1, 'root'), 11: make(11, 1, 'new')})
        assert tree.matching({11: make(11, 1, 'new')}) == []
        checks.append('PID reuse with a different start identity is not owned')
        for mode, cpu, expected in (('normal-root', 5, 'exited'), ('burn-root', 1, 'sampled-aggregate-cpu-limit')):
            directory = output / mode
            directory.mkdir(mode=0o700)
            command = (str(Path(sys.executable).resolve(strict=True)), '-I', '-B', str(Path(__file__).resolve()), '--fixture', mode)
            result = guard.supervise(command, cwd=HERE, directory=directory,
                limits=guard.Limits(wall_seconds=8, cpu_seconds=cpu, rss_bytes=128 * 1024**2, output_bytes=1024**2),
                metadata={'fixture': mode, 'native_calibration_requested': False,
                          'helper_file_sha256': helper_before})
            raw = guard.canonical(result) + b'\n'
            guard.write_once(directory / 'supervision.json', raw)
            processes.append({'fixture': mode, 'receipt': str(directory / 'supervision.json'),
                              'sha256': hashlib.sha256(raw).hexdigest(), 'reason': result['reason']})
            assert result['reason'] == expected, result
            assert result['cleanup']['controller_reaped'] is True
            assert result['remaining_live_owned_pids'] == [], result
            assert len({row['pgid'] for row in result['observed_processes']}) >= 3, result
            if mode == 'normal-root':
                assert result['status'] == 'process-completed-with-open-gates', result
                assert result['post_controller_exit_live_samples'] > 0, result
                assert result['wall_seconds'] >= 1.0, result
            else:
                assert result['status'] == 'stopped-or-failed', result
                assert result['accounted_cpu_lower_bound_seconds'] >= 1.0, result
            checks.append(mode + ': tracked separate sessions, retained output, reaped controller, no live tracked descendants')
        assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == helper_before
    except BaseException as failure:
        status, error = 'failed', type(failure).__name__ + ': ' + str(failure)[:4000]
    record = {'schema': 'peano-hydra-v28-supervisor-tiny-fixtures-v1', 'status': status,
              'started_at': started, 'finished_at': datetime.now(timezone.utc).isoformat(),
              'helper_file_sha256': helper_before, 'test_file_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'checks': checks, 'process_receipts': processes, 'error': error,
              'real_native_or_model_campaign_performed': False, 'network_or_scheduler_work_performed': False}
    raw = guard.canonical(record) + b'\n'
    guard.write_once(output / 'tests.json', raw)
    print(json.dumps({'status': status, 'checks': len(checks), 'receipt': str(output / 'tests.json'),
                      'sha256': hashlib.sha256(raw).hexdigest(), 'error': error}), flush=True)
    return 0 if status == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
