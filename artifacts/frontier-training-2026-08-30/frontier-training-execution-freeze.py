"""Fresh local training-only execution snapshot: unchanged selection plus three jobs.

This separate utility does not widen any existing freezer scope or ceiling.
It retains failed fresh directories, changes no original repository, stages
only its own new Git repository, and never invokes SSH, Slurm, models or proofs.
The explicit plan and the freeze are separate operator-invoked stages.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time


ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-training-2026-08-30')
JOBS = ('slurm/peano_hydra_frontier_evaluate.sbatch', 'slurm/peano_hydra_frontier_train.sbatch',
        'slurm/peano_hydra_frontier_training.sbatch')
SUPPORT = ('training/peano_hydra/scaling_freeze.py', 'training/peano_hydra/origin_bridge.py',
           'training/peano_hydra/review_sources.py', 'training/peano_hydra/__init__.py')
PROTECTED = (
    ROOT.parent / 'hydra-search-v2-build-20260829',
    ROOT.parent / 'hydra-frontier-frozen-20260830',
    ROOT.parent / 'hydra-frontier-pilot-recovery-20260830',
    ROOT.parent / 'hydra-frontier-execution-20260830',
    Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-experiment-2026-08-30'),
    Path('/Users/bnaskrecki/codex/test/vietnam2026-new-theorems'),
)
PLAN_SCHEMA = 'peano-hydra-frontier-training-execution-freeze-plan-v1'
RECEIPT_SCHEMA = 'peano-hydra-frontier-training-execution-freeze-receipt-v1'
ORIGIN_PATH = '_deploy/frontier-training-origin-source.json'
RECEIPT_PATH = '_deploy/frontier-training-execution-freeze.json'
FAILURE_PATH = '_deploy/frontier-training-execution-freeze-failed.json'
MAX_FILES, MAX_BYTES, MAX_JOB_BYTES = 2048, 128 * 1024**2, 64 * 1024
CPU, WALL, RSS, OUTPUT = 120, 120, 1024**3, 2 * 1024**2
_SHA = re.compile(r'[0-9a-f]{64}\Z')
sys.path[:0] = [str(ROOT)]
from training.peano_hydra import origin_bridge as bridge
from training.peano_hydra import scaling_freeze as freezer


def require(value, message):
    if not value:
        raise freezer.ScalingFreezeError(message)


def canonical(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                     separators=(',', ':')).encode()
    require(len(raw) <= OUTPUT, 'execution-freeze metadata exceeds bound')
    return raw


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_plan(record):
    require(type(record) is dict and record.get('schema') == PLAN_SCHEMA, 'wrong execution plan schema')
    require(record.get('plan_sha256') == digest({k: v for k, v in record.items() if k != 'plan_sha256'}),
            'execution plan canonical SHA differs')
    expected_keys = {'schema', 'source_root', 'output_directory', 'source_plan', 'jobs', 'files',
        'files_sha256', 'file_count', 'total_bytes', 'limits', 'native_or_model_work_requested',
        'network_or_scheduler_work_requested', 'plan_sha256'}
    require(set(record) == expected_keys, 'execution plan fields changed')
    source = record['source_plan']
    require(source.get('schema') == freezer.PLAN_SCHEMA and source.get('plan_sha256') ==
            digest({k: v for k, v in source.items() if k != 'plan_sha256'}), 'source plan canonical SHA differs')
    require(record['source_root'] == source['source_root'] == str(ROOT), 'source root changed')
    destination = bridge._absolute(Path(record['output_directory']))
    require(destination.parent == ROOT.parent and destination != ROOT
            and freezer._SAFE_PATH.fullmatch(destination.name), 'destination must be a dedicated sibling snapshot')
    require(type(record['jobs']) is dict and set(record['jobs']) == set(JOBS), 'exactly three declared job files required')
    require(not set(JOBS) & set(source['files']), 'jobs unexpectedly entered historical freezer scope')
    combined = dict(sorted({**source['files'], **record['jobs']}.items()))
    require(record['files'] == combined and record['files_sha256'] == digest(combined), 'execution inventory changed')
    require(len(combined) == record['file_count'] <= MAX_FILES
            and len({p.casefold() for p in combined}) == len(combined), 'file count or portable names changed')
    for name, item in combined.items():
        freezer._path(name)
        require(type(item) is dict and set(item) == {'bytes', 'sha256', 'git_blob', 'mode'}
                and type(item['bytes']) is int and item['bytes'] >= 0
                and item['mode'] in {'100644', '100755'}
                and type(item['sha256']) is str and _SHA.fullmatch(item['sha256'])
                and type(item['git_blob']) is str and freezer._OID.fullmatch(item['git_blob']),
                'invalid execution file descriptor')
    require(all(combined[name]['bytes'] <= MAX_JOB_BYTES for name in JOBS), 'job file exceeds bounded source limit')
    require(sum(i['bytes'] for i in combined.values()) == record['total_bytes'] <= MAX_BYTES,
            'complete execution byte total exceeds ceiling')
    require(record['limits'] == {'max_files': MAX_FILES, 'max_total_bytes': MAX_BYTES, 'max_job_bytes': MAX_JOB_BYTES},
            'execution plan raised a ceiling')
    require(record['native_or_model_work_requested'] is False and record['network_or_scheduler_work_requested'] is False,
            'execution source plan grants no native/model/network/scheduler work')
    return record


def execution_plan(source, output, deadline):
    """Read actual working bytes and the exact three job scripts, without staging."""
    source_plan = freezer._plan(source, deadline)
    jobs = {}
    for name in JOBS:
        jobs[name], raw = source.fingerprint(name, maximum=MAX_JOB_BYTES, retain=True)
        require(raw.startswith(b'#!/bin/bash') and b'\0' not in raw, 'job is not bounded shell source')
    files = dict(sorted({**source_plan['files'], **jobs}.items()))
    source.assert_unchanged()
    require(freezer._git_identity(source, deadline) == source_plan['source_git'], 'original Git state changed during execution planning')
    record = {'schema': PLAN_SCHEMA, 'source_root': str(ROOT), 'output_directory': str(output),
        'source_plan': source_plan, 'jobs': jobs, 'files': files, 'files_sha256': digest(files),
        'file_count': len(files), 'total_bytes': sum(i['bytes'] for i in files.values()),
        'limits': {'max_files': MAX_FILES, 'max_total_bytes': MAX_BYTES, 'max_job_bytes': MAX_JOB_BYTES},
        'native_or_model_work_requested': False, 'network_or_scheduler_work_requested': False}
    return validate_plan({**record, 'plan_sha256': digest(record)})


def freeze_execution(request):
    deadline = time.monotonic() + WALL
    output = bridge._absolute(Path(request['output_directory']))
    state = {'phase': 'preflight', 'status': 'incomplete', 'snapshot_root': str(output),
             'copied_files': 0, 'partial_output_retained': False}
    destination = None
    with ExitStack() as stack:
        archive = stack.enter_context(bridge._Tree(ARCHIVE))
        source = stack.enter_context(bridge._Tree(ROOT))
        parent = stack.enter_context(bridge._Tree(output.parent))
        protected = tuple(stack.enter_context(bridge._Tree(p)) for p in PROTECTED)
        try:
            relative_plan = str(Path(request['plan_file']).relative_to(ARCHIVE))
            pin, raw = archive.fingerprint(relative_plan, maximum=OUTPUT, retain=True)
            require(pin['sha256'] == request['expected_plan_file_sha256'], 'external raw execution-plan SHA changed')
            declared = validate_plan(bridge._decode(raw, OUTPUT, 'execution plan'))
            require(declared['plan_sha256'] == request['expected_plan_sha256']
                    and declared['output_directory'] == str(output), 'external canonical plan or destination changed')
            freezer._protect_output(source, parent, output, protected)
            current = execution_plan(source, output, deadline)
            require(canonical(current) == canonical(declared), 'source/job inventory changed after the pinned plan')
            os.mkdir(output.name, 0o700, dir_fd=parent.directory())
            os.fsync(parent.directory())
            state['partial_output_retained'] = True
            created = os.stat(output.name, dir_fd=parent.directory(), follow_symlinks=False)
            destination = stack.enter_context(bridge._Tree(output))
            held = os.fstat(destination.directory())
            require((created.st_dev, created.st_ino) == (held.st_dev, held.st_ino), 'new snapshot root was replaced')
            files = current['files']
            state['phase'] = 'copy'
            for name, expected in files.items():
                freezer._deadline(deadline)
                actual, payload = source.fingerprint(name, maximum=expected['bytes'], retain=True)
                require(actual == expected, 'input changed immediately before copying: ' + name)
                freezer._new_file(destination, name, payload, 0o755 if expected['mode'] == '100755' else 0o644)
                state['copied_files'] += 1
            require(freezer._walk(destination, ('',), deadline=deadline) == set(files), 'unexpected snapshot payload before Git')
            freezer._check_files(source, files, deadline)
            freezer._check_files(destination, files, deadline)
            require(freezer._selection(source, deadline) == (current['source_plan']['epoch_version'], set(current['source_plan']['files'])),
                    'original source selection changed before commit')
            state['phase'] = 'fresh-local-git'
            freezer._git(destination, 'init', '--quiet', '--template=', '--object-format=sha1',
                '--initial-branch=hydra-frontier-training-execution-snapshot', deadline=deadline, synthetic=True)
            destination.directory('.git')
            ignored = (ORIGIN_PATH, RECEIPT_PATH, FAILURE_PATH,
                       'results/peano-hydra/ignore-probe', 'results/peano-policy/ignore-probe')
            ignore_input = b''.join(name.encode() + b'\0' for name in ignored)
            require(freezer._git(destination, 'check-ignore', '--no-index', '-z', '--stdin',
                deadline=deadline, input_bytes=ignore_input, synthetic=True) == ignore_input,
                'copied ignore rules do not exclude receipts and results')
            path_input = b''.join(name.encode() + b'\0' for name in sorted(files))
            freezer._git(destination, 'add', '--force', '--pathspec-from-file=-', '--pathspec-file-nul',
                deadline=deadline, input_bytes=path_input, synthetic=True)
            freezer._git(destination, 'commit', '--quiet', '--no-gpg-sign', '--no-verify', '-m',
                'Synthetic Hydra training-only execution source snapshot with three pinned jobs; no training approval',
                deadline=deadline, synthetic=True)
            commit = freezer._git(destination, 'rev-parse', '--verify', 'HEAD', deadline=deadline,
                                  maximum=80, synthetic=True).decode().strip()
            require(freezer._OID.fullmatch(commit), 'fresh snapshot has no real Git commit')
            freezer._check_git_tree(freezer._git(destination, 'ls-tree', '-r', '-z', 'HEAD',
                deadline=deadline, synthetic=True), files)
            require(freezer._git(destination, 'status', '--porcelain=v1', '-z', '--untracked-files=all',
                deadline=deadline, synthetic=True) == b'', 'fresh snapshot is not clean')
            state['phase'] = 'ordinary-portable-origin'
            origin = bridge.freeze_origin_sources(output, expected_commit=commit)
            portable = bridge._decode(origin, bridge.MAX_BUNDLE_MANIFEST_BYTES, 'portable execution source')
            expected_portable = {name: value for name, value in current['source_plan']['files'].items()
                                 if name not in freezer.EXTRA_FILES}
            require(portable['git_commit'] == commit and portable['files'] == expected_portable,
                    'standard origin manifest changed its historical source scopes')
            freezer._new_file(destination, ORIGIN_PATH, origin)
            freezer._check_files(source, files, deadline)
            freezer._check_files(destination, files, deadline)
            require(canonical(execution_plan(source, output, deadline)) == canonical(declared),
                    'original source plan, jobs or Git state changed during freeze')
            require(archive.fingerprint(relative_plan, maximum=OUTPUT)[0] == pin, 'pinned plan input changed during freeze')
            require(freezer._walk(destination, ('',), deadline=deadline, skip_git=True) == set(files) | {ORIGIN_PATH},
                    'completed execution snapshot contains unexpected payloads')
            require(freezer._git(destination, 'status', '--porcelain=v1', '-z', '--untracked-files=all',
                deadline=deadline, synthetic=True) == b'', 'origin receipt dirtied snapshot')
            for tree in (source, destination, parent, archive, *protected):
                tree.assert_unchanged()
            receipt = {'schema': RECEIPT_SCHEMA, 'status': 'complete', 'source_plan': declared,
                'source_plan_file': {'path': str(ARCHIVE / relative_plan), 'bytes': pin['bytes'], 'sha256': pin['sha256']},
                'snapshot_root': str(output), 'git_commit': commit, 'snapshot_clean': True,
                'all_selected_files_and_jobs_committed': True, 'file_count': len(files),
                'total_bytes': sum(i['bytes'] for i in files.values()),
                'files': files, 'files_sha256': digest(files), 'jobs': current['jobs'],
                'origin_source_manifest': {'path': ORIGIN_PATH, 'bytes': len(origin), 'sha256': hashlib.sha256(origin).hexdigest()},
                'source_bytes_unchanged': True, 'original_git_state_unchanged': True,
                'protected_inputs': [str(p) for p in PROTECTED],
                'native_epoch_verified': False, 'proofs_replayed': 0,
                'training_authorized': False, 'gpu_execution_authorized': False, 'network_transfer_authorized': False,
                'old_freezer_scopes_or_caps_changed': False,
                'coverage': 'Unmodified scaling source selection plus exactly three declared Slurm source files, including the separate training-only job; ordinary code-scope origin manifest remains separate. No comparison or compute approval.'}
            raw_receipt = canonical(receipt) + b'\n'
            freezer._new_file(destination, RECEIPT_PATH, raw_receipt)
            return {'schema': RECEIPT_SCHEMA, 'status': 'complete', 'snapshot_root': str(output),
                'git_commit': commit, 'plan_sha256': declared['plan_sha256'], 'file_count': len(files),
                'total_bytes': receipt['total_bytes'], 'receipt_path': str(output / RECEIPT_PATH),
                'receipt_sha256': hashlib.sha256(raw_receipt).hexdigest(),
                'origin_source_manifest_path': str(output / ORIGIN_PATH),
                'origin_source_manifest_sha256': hashlib.sha256(origin).hexdigest(),
                'snapshot_clean': True, 'training_authorized': False, 'gpu_execution_authorized': False}
        except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
            state['error'] = ' '.join(str(error).split())[:1024]
            if destination is not None:
                try:
                    destination.assert_unchanged()
                    freezer._new_file(destination, FAILURE_PATH, canonical({'schema': RECEIPT_SCHEMA, **state}) + b'\n')
                except (OSError, ValueError):
                    pass
            raise freezer.ScalingFreezeError('execution snapshot incomplete; partial output retained; original repository unstaged',
                                             observation=state) from error


def support_hashes():
    with bridge._Tree(ROOT) as source, bridge._Tree(ARCHIVE) as archive:
        result = {name: source.fingerprint(name, maximum=2 * 1024**2)[0] for name in SUPPORT}
        result['helper'] = archive.fingerprint(Path(__file__).name, maximum=2 * 1024**2)[0]
        return result


def worker():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    raw = sys.stdin.buffer.read(65537)
    request = bridge._decode(raw, 65536, 'execution-freeze worker request')
    require(os.environ.get('HYDRA_FRONTIER_TRAINING_EXECUTION_FREEZE_GUARDED') == '1', 'execution worker requires owned group guard')
    if request['stage'] == 'plan':
        output = bridge._absolute(Path(request['output_directory']))
        with bridge._Tree(ROOT) as source, bridge._Tree(output.parent) as parent:
            freezer._protect_output(source, parent, output)
            result = execution_plan(source, output, time.monotonic() + WALL)
    elif request['stage'] == 'freeze':
        result = freeze_execution(request)
    else:
        raise ValueError('unknown execution-freeze stage')
    require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules), 'source stage imported a model framework')
    require(not any(n == 'peano_lab' or n.startswith('peano_lab.') for n in sys.modules), 'source stage imported native proof engine')
    print(canonical(result).decode(), flush=True)


def stop_group(child):
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait(timeout=5)


def allowed_sampled_child(executable):
    """Allow Git and the short inherited Python name before fork/exec.

    The reviewed freezer starts Git with a held-directory fchdir preexec hook.
    On macOS ps may observe that child as Python or (Python) before exec/reap.
    Executable names are diagnostics, not authentication of a running process;
    fixed source-reviewed Git calls and unchanged support hashes own that scope.
    """
    name = Path(executable).name.strip('()')
    return name in {'git', 'Python', Path(sys.executable).name}


def main():
    if sys.argv[1:] == ['--worker']:
        worker()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('plan', 'freeze'))
    parser.add_argument('--plan-file', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--process-receipt', type=Path, required=True)
    parser.add_argument('--expected-plan-file-sha256')
    parser.add_argument('--expected-plan-sha256')
    args = parser.parse_args()
    require(Path(__file__).absolute() == ARCHIVE / 'frontier-training-execution-freeze.py', 'helper is bound to its own local archive')
    plan_path, receipt_path = bridge._absolute(args.plan_file), bridge._absolute(args.process_receipt)
    require(plan_path.parent == receipt_path.parent == ARCHIVE and plan_path != receipt_path,
            'plan/process receipts must be separate immediate archive files')
    destination = bridge._absolute(args.output_directory)
    require(destination.parent == ROOT.parent and destination != ROOT and freezer._SAFE_PATH.fullmatch(destination.name),
            'destination must be a fresh sibling source snapshot')
    hashes = (args.expected_plan_file_sha256, args.expected_plan_sha256)
    require((args.stage == 'freeze' and all(type(v) is str and _SHA.fullmatch(v) for v in hashes))
            or (args.stage == 'plan' and hashes == (None, None)), 'freeze needs both external plan hashes; plan accepts neither')
    request = {'stage': args.stage, 'output_directory': str(destination), 'plan_file': str(plan_path),
               'expected_plan_file_sha256': hashes[0], 'expected_plan_sha256': hashes[1]}
    with bridge._Tree(ARCHIVE) as archive:
        for path in (receipt_path, plan_path) if args.stage == 'plan' else (receipt_path,):
            try:
                os.stat(path.name, dir_fd=archive.directory(), follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError('fresh receipt/plan required; no overwrite or automatic retry')
        before = support_hashes()
        command = [sys.executable, '-I', '-B', '-X', 'pycache_prefix=/dev/null', str(Path(__file__).absolute()), '--worker']
        environment = {k: v for k, v in os.environ.items()
            if not k.startswith(('LD_', 'DYLD_', 'PYTHON', 'GIT_', 'SLURM_', 'SBATCH_'))
            and k not in {'BASH_ENV', 'ENV', 'HELIOS_SSH_TARGET'}}
        environment['HYDRA_FRONTIER_TRAINING_EXECUTION_FREEZE_GUARDED'] = '1'
        started = time.monotonic()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu_before = usage.ru_utime + usage.ru_stime
        child = subprocess.Popen(command, cwd=ROOT, env=environment, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        child.stdin.write(canonical(request))
        child.stdin.close()
        selector, output = selectors.DefaultSelector(), {'stdout': bytearray(), 'stderr': bytearray()}
        peak, observed, observed_commands = 0, set(), set()
        reason, error, sampled_at = 'exited', None, 0.0
        try:
            for label, stream in (('stdout', child.stdout), ('stderr', child.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)
            while selector.get_map() or child.poll() is None:
                now = time.monotonic()
                if now - started >= WALL:
                    raise TimeoutError('whole execution-freeze stage wall limit')
                if now - sampled_at >= 0.05:
                    sample = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,rss=,comm='],
                        stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=1)
                    require(len(sample.stdout) <= 4 * 1024**2 and len(sample.stderr) <= 65536,
                            'process sampler exceeded output bound')
                    group = []
                    for line in sample.stdout.splitlines():
                        fields = line.split(None, 3)
                        pid, pgid, kib = map(int, fields[:3])
                        if pgid == child.pid:
                            executable = fields[3].decode('utf-8') if len(fields) == 4 else ''
                            observed.add(pid)
                            observed_commands.add(Path(executable).name)
                            require(pid == child.pid or allowed_sampled_child(executable),
                                    'unexpected non-Git descendant in execution-freeze group')
                            group.append(kib * 1024)
                    peak = max(peak, sum(group))
                    require(peak <= RSS, 'whole-group sampled RSS limit')
                    sampled_at = time.monotonic()
                for key, _ in selector.select(0.025):
                    block = os.read(key.fileobj.fileno(), 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                    else:
                        remaining = OUTPUT - sum(map(len, output.values()))
                        output[key.data].extend(block[:remaining])
                        require(len(block) <= remaining, 'combined stage output limit')
            child.wait(timeout=1)
        except BaseException as failure:
            reason, error = 'guard-stopped', type(failure).__name__ + ': ' + str(failure)
        finally:
            stop_group(child)
            selector.close()
            child.stdout.close()
            child.stderr.close()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = usage.ru_utime + usage.ru_stime - cpu_before
        wall = time.monotonic() - started
        try:
            after = support_hashes()
        except (OSError, ValueError) as failure:
            after, reason, error = None, 'source-check-failed', str(failure)
        passed = reason == 'exited' and child.returncode == 0 and before == after and cpu <= CPU and wall <= WALL and peak <= RSS
        stdout, stderr = (bytes(output[k]).decode('utf-8', 'replace') for k in ('stdout', 'stderr'))
        result, plan_identity = None, None
        if passed:
            try:
                result = bridge._decode(bytes(output['stdout']), OUTPUT, 'execution-freeze result')
                if args.stage == 'plan':
                    validate_plan(result)
                    raw = canonical(result) + b'\n'
                    freezer._new_file(archive, plan_path.name, raw, 0o600)
                    plan_identity = {'path': str(plan_path), 'bytes': len(raw),
                        'raw_sha256': hashlib.sha256(raw).hexdigest(), 'plan_sha256': result['plan_sha256']}
                else:
                    require(result['schema'] == RECEIPT_SCHEMA and result['status'] == 'complete'
                            and result['plan_sha256'] == args.expected_plan_sha256, 'freeze result changed request')
            except (KeyError, TypeError, ValueError, OSError) as failure:
                passed, error = False, 'invalid-stage-result: ' + str(failure)
        record = {'schema': 'peano-hydra-frontier-training-execution-freeze-process-v1', 'status': 'passed' if passed else 'failed',
            'stage': args.stage, 'request': request, 'command': command, 'source_files_before': before,
            'source_files_after': after, 'source_files_unchanged': before == after,
            'limits': {'cpu_seconds_per_process': CPU, 'whole_stage_wall_seconds': WALL,
                       'sampled_group_rss_bytes': RSS, 'combined_output_bytes': OUTPUT},
            'reason': reason, 'error': error, 'returncode': child.returncode, 'wall_seconds': wall,
            'cpu_seconds_with_waited_children_and_sampler': cpu, 'peak_sampled_group_rss_bytes': peak,
            'observed_process_ids': sorted(observed), 'observed_executable_names': sorted(observed_commands),
            'sampled_name_policy': 'Git plus inherited Python fork/preexec names; names are diagnostics, not executable attestation. Only fixed reviewed Git calls are requested.',
            'resource_measurement': 'Inherited120/121 CPU per process;120s outer wall;50ms sampled groupRSS. Waited-child CPU includes sampler and is rejected above120s; not instantaneous aggregate CPU enforcement.',
            'stdout': stdout, 'stderr': stderr, 'plan_identity': plan_identity,
            'result': result if args.stage == 'freeze' else None,
            'native_or_model_work_requested': False, 'network_or_scheduler_work_requested': False}
        archive.assert_unchanged()
        raw = canonical(record) + b'\n'
        freezer._new_file(archive, receipt_path.name, raw, 0o600)
        print(json.dumps({'process_receipt': str(receipt_path), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                          'status': record['status'], 'plan': plan_identity,
                          'result': result if args.stage == 'freeze' else None}, sort_keys=True), flush=True)
        return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
