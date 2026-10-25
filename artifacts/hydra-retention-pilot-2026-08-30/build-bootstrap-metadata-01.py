"""One bounded, data-only publication of the real retention bootstrap metadata.

No receipt replay, training bind, model/native execution, resource request,
approval, transfer, or scheduler operation is performed by this helper.
"""
from __future__ import annotations

import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import threading
import time

ROOT = Path('/Users/bnaskrecki/codex/peano')
WORK = ROOT / '_deploy/hydra-frontier-recovery-work-20260830'
REL = Path('_deploy/hydra-retention-pilot-v1')
PACKAGE = WORK / REL
ARCHIVE = ROOT / 'artifacts/hydra-retention-pilot-2026-08-30'
OLD = ROOT / '_deploy/hydra-model-test-execution-20260830/_deploy/hydra-frontier-diagnostic-v1'
REMOTE = Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training')
FUTURE = {'local': ROOT / '_deploy/hydra-retention-execution-20260830',
          'helios': REMOTE / 'experiments/retention-pilot-v1'}
CONFIG = Path('training/peano_hydra/configs/qwen3_1_7b_retention_pilot.toml')
RECEIPT = ARCHIVE / 'bootstrap-metadata-01.json'
MANIFEST_SHA = 'bb67f5f0737003d2c40b45885d7759f395f27bf0e88d358bfe1844df2a30ba21'
CONFIG_SHA = '07c2b9c3d82a6c50bef77e15564d00a8e528075fcc5603cbe0bb8ea48a1c74f3'
FRONTIER_PLAN_SHA = 'a8084683ea64e4128f4d34eea0753c67fc42a55772e1c698a5dbd62865878c4b'
PINS = {
    WORK / 'training/peano_hydra/retention_data.py': (37289, 'b2b9c6fac5b8281d7a3417dff50eb3cda19f59af2c6fc28ae4d0f42c5efc3bdb'),
    WORK / 'training/peano_hydra/retention_training.py': (44828, 'd6529651c031fce3fe535f7b8b9ccbbb3396125083640184f7125065b9e26725'),
    WORK / 'training/peano_hydra/retention_evaluation.py': (59494, '1f42a76f0c1127b7edd2ce171c0e238b5846941a40b1c5cd185f676b9dc5bf92'),
    WORK / CONFIG: (1029, CONFIG_SHA),
    PACKAGE / 'preparation/manifest.json': (744657, MANIFEST_SHA),
    OLD / 'evaluation-plan.json': (32267, FRONTIER_PLAN_SHA),
    OLD / 'evaluation-request.json': (7507, '9c4fe30f658558410bea892ae201529e2114d7959c54a5257ed56e2547bc9c88'),
    OLD / 'origins/baseline/origin-receipt.json': (205992, '9f3509835a2dffeabf7590af8347aad9a622342f5131a20e26eaf0faa40ab7d1'),
    OLD / 'origins/baseline/source-manifest.json': (152356, '7cb1a9d35b078989991362a979c3ea0d6abac929fbfcf9ae1e457458a24e513d'),
    OLD / 'origins/candidate/origin-receipt.json': (241518, 'ee8e851d486bacff4730a6317d839608c2ffd492af2b78fb58a2ab77748defdb'),
    OLD / 'origins/candidate/source-manifest.json': (184587, '346f9ac39c7d66ebb2c340922d77fc5dbef8a2e867cb1825dddcea92e616ca3b'),
    ROOT / 'artifacts/hydra-model-test-2026-08-30/explicit-experiment-approval-01.json': (2107, '04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778'),
    ARCHIVE / 'user-directive-01.json': (1357, '9bb97fcedf3c3711a2f109a9647438f3844ea9c795e9cb320a7ac37708be339d'),
}
LIMITS = {'cpu_soft_seconds': 60, 'cpu_hard_seconds': 61, 'wall_seconds': 90,
          'observed_peak_rss_bytes': 1024**3, 'single_output_file_bytes': 2 * 1024**2,
          'total_new_metadata_bytes': 4 * 1024**2, 'open_files': 128}
WRITTEN = []
SIGNALS = []
START = time.monotonic()
CPU_START = time.process_time()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def stable_read(path, maximum=4 * 1024**2):
    require(path.is_absolute() and path.resolve(strict=True) == path, 'noncanonical input path')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'input is not a bounded single-link regular file')
        raw = bytearray()
        while len(raw) <= maximum:
            chunk = os.read(fd, min(65536, maximum + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        after = os.fstat(fd)
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_mode, s.st_nlink)
        require(signature(before) == signature(after) == signature(os.lstat(path))
                and len(raw) == before.st_size, 'input changed while being read')
        return bytes(raw)
    finally:
        os.close(fd)


def publish(path, raw):
    require(len(raw) <= LIMITS['single_output_file_bytes'], 'output file exceeds cap')
    require(path.parent.resolve(strict=True) == path.parent, 'aliased output parent')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    WRITTEN.append(str(path))
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            require(count > 0, 'short output write')
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    require(stable_read(path) == raw, 'published output differs')


def limit_signal(number, _frame):
    SIGNALS.append({'signal': number, 'wall_seconds': time.monotonic() - START,
                    'cpu_seconds': time.process_time() - CPU_START})
    raise TimeoutError('metadata owner resource limit reached')


def peak_rss():
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(usage if sys.platform == 'darwin' else usage * 1024)


def audit(event, args):
    require(event not in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork',
                         'os.forkpty', 'socket.__new__', 'socket.connect', 'socket.bind'},
            'subprocess or network is forbidden in this metadata operation')


class FrameworkBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        require(fullname.split('.')[0] not in {'torch', 'transformers', 'peft', 'accelerate', 'datasets', 'vllm'},
                'model/framework import is forbidden in this metadata operation')
        return None


def main():
    require(not os.path.lexists(RECEIPT), 'operation receipt already exists')
    require(PACKAGE.resolve(strict=True) == PACKAGE and ARCHIVE.resolve(strict=True) == ARCHIVE,
            'aliased output directory')
    for name in ('evaluation-plan.json', 'inputs.json', 'authority.json', 'user-directive.json', 'origins'):
        require(not os.path.lexists(PACKAGE / name), 'bootstrap output already exists: ' + name)
    source_bytes = {path: stable_read(path) for path in PINS}
    for path, (size, sha) in PINS.items():
        require(descriptor(source_bytes[path]) == {'bytes': size, 'sha256': sha}, 'pinned input changed: ' + str(path))

    sys.path.insert(0, str(WORK))
    from training.peano_hydra import retention_data as data, retention_evaluation as evaluation
    from training.peano_hydra import retention_training as training, origin_bridge as bridge
    from training.peano_hydra.scaling_evaluation import OriginReference

    checked = data.load_preparation(PACKAGE / 'preparation', expected_manifest_sha256=MANIFEST_SHA)
    require(len(checked.train_rows) == 11751 and len(checked.dev_rows) == 2840, 'actual mixed row counts changed')
    plan = evaluation.build_evaluation_plan(checked, frontier_evaluation_plan_path=OLD / 'evaluation-plan.json',
                                          expected_frontier_plan_sha256=FRONTIER_PLAN_SHA)
    plan_raw = encode(plan)
    plan_sha = descriptor(plan_raw)['sha256']
    original = json.loads(source_bytes[OLD / 'evaluation-request.json'])
    payloads = {'evaluation-plan.json': plan_raw,
                'authority.json': source_bytes[ROOT / 'artifacts/hydra-model-test-2026-08-30/explicit-experiment-approval-01.json'],
                'user-directive.json': source_bytes[ARCHIVE / 'user-directive-01.json']}
    roles = {'saved-v25': 'baseline', 'frontier-v28': 'candidate'}
    for role, old_role in roles.items():
        for filename in ('origin-receipt.json', 'source-manifest.json'):
            raw = source_bytes[OLD / 'origins' / old_role / filename]
            key = 'receipt' if filename == 'origin-receipt.json' else 'source_manifest'
            require(descriptor(raw) == {k: original[old_role][key][k] for k in ('bytes', 'sha256')},
                    'original request control descriptor differs')
            payloads['origins/' + role + '/' + filename] = raw
    models = {
        'local': {'saved-v25': ROOT / '_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/model/manifest.json',
                  'frontier-v28': ROOT / 'artifacts/hydra-model-test-2026-08-30/candidate-model/manifest.json'},
        'helios': {'saved-v25': REMOTE / '_deploy/hydra-search-v2/model/manifest.json',
                   'frontier-v28': REMOTE / 'experiments/frontier-training-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1/manifest.json'},
    }
    refs = {}
    for place, root in FUTURE.items():
        origins = {}
        for role, old_role in roles.items():
            entry = original[old_role]
            source_key = 'local' if place == 'local' else 'remote'
            request = bridge._request(entry['identity'], {
                'source_root': entry['source_locations'][source_key],
                'source_manifest': str(root / REL / 'origins' / role / 'source-manifest.json'),
                'adapter_manifest': str(models[place][role]),
            })
            origins[role] = OriginReference(request, root / REL / 'origins' / role / 'origin-receipt.json',
                                            entry['receipt']['sha256'])
            require(request.to_dict() == entry['identity'], 'portable original identity changed')
        refs[place] = training.TrainingInputReference(root / REL / 'preparation', MANIFEST_SHA,
            root / CONFIG, CONFIG_SHA, origins['saved-v25'], origins['frontier-v28'],
            root / REL / 'evaluation-plan.json', plan_sha)
    require(refs['local'].to_dict() == refs['helios'].to_dict(), 'portable identities differ by location')
    inputs = {'schema': 'peano-hydra-retention-pilot-inputs-v1',
              'profile': 'peano-hydra-retention-pilot-v1', 'run_id': 'retention-pilot-v1',
              'training_input': refs['local'].to_dict(),
              'locations': {place: ref.locations() for place, ref in refs.items()}}
    for place, ref in refs.items():
        decoded = training.input_reference(inputs['training_input'], inputs['locations'][place])
        require(decoded == ref, 'constructor-only location/identity round trip failed')
    payloads['inputs.json'] = encode(inputs)
    require(sum(map(len, payloads.values())) <= LIMITS['total_new_metadata_bytes'] - 65536,
            'new bootstrap metadata exceeds retained-output cap')
    # Do not publish if code/config/original control bytes drifted while loading.
    for path, raw in source_bytes.items():
        require(stable_read(path) == raw, 'input drifted before bootstrap publication')
    (PACKAGE / 'origins').mkdir(mode=0o700)
    for role in roles:
        (PACKAGE / 'origins' / role).mkdir(mode=0o700)
    for name, raw in payloads.items():
        publish(PACKAGE / name, raw)
    require(stable_read(PACKAGE / 'preparation/manifest.json') == source_bytes[PACKAGE / 'preparation/manifest.json'],
            'existing preparation manifest changed')
    require(peak_rss() <= LIMITS['observed_peak_rss_bytes'], 'peak RSS exceeded owner cap')
    return {'status': 'metadata-only-built', 'profile': inputs['profile'], 'run_id': inputs['run_id'],
        'future_roots': {k: str(v) for k, v in FUTURE.items()},
        'input_files': {str(path): descriptor(raw) for path, raw in source_bytes.items()},
        'output_directory': str(PACKAGE),
        'output_files': {name: descriptor(raw) for name, raw in sorted(payloads.items())},
        'output_metadata_bytes': sum(map(len, payloads.values())),
        'configuration': {'relative_path': CONFIG.as_posix(), **descriptor(source_bytes[WORK / CONFIG]),
                          'copied_into_package': False},
        'preparation': {'manifest_sha256': MANIFEST_SHA, 'train_rows': len(checked.train_rows),
                        'dev_rows': len(checked.dev_rows), 'payloads_hash_checked': True,
                        'rebuilt': False, 'modified': False},
        'evaluation': {'raw_sha256': plan_sha, 'plan_sha256': plan['plan_sha256'],
                       'goal_count': len(plan['goals']), 'cohort_counts': {k: len(v) for k, v in plan['cohorts'].items()},
                       'budgets': list(evaluation.BUDGETS), 'roles': list(evaluation.ROLES),
                       'row_count': evaluation.TOTAL_RECORDS, 'maximum_model_calls': evaluation.MAX_CALLS,
                       'historical_frontier_raw_sha256': FRONTIER_PLAN_SHA},
        'constructor_round_trips': ['local', 'helios'], 'portable_identity_equal': True,
        'performed': {'original_control_bytes_copied': True, 'metadata_validation': True,
                      'origin_receipt_replay': False, 'bind_training': False, 'model_or_framework_import': False,
                      'model_or_native_execution': False, 'network': False, 'resource_request': False,
                      'new_specific_job_approval': False, 'scheduler_or_gpu': False},
        'authority_scope': 'Original standing directive copied verbatim; no new resource approval or scientific attestation is created.'}


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    require(not os.path.lexists(RECEIPT), 'operation receipt already exists')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 61))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    for number in (signal.SIGXCPU, signal.SIGALRM, signal.SIGUSR1):
        signal.signal(number, limit_signal)
    signal.setitimer(signal.ITIMER_REAL, 90)
    sys.addaudithook(audit)
    sys.meta_path.insert(0, FrameworkBlocker())
    done = threading.Event()
    def watch_rss():
        while not done.wait(0.02):
            if peak_rss() > LIMITS['observed_peak_rss_bytes']:
                os.kill(os.getpid(), signal.SIGUSR1)
                return
    observer = threading.Thread(target=watch_rss, daemon=True)
    observer.start()
    try:
        result = main()
    except BaseException as error:
        result = {'status': 'failed', 'error_type': type(error).__name__, 'error': str(error)[:4096],
                  'written_paths_preserved': list(WRITTEN)}
    finally:
        done.set()
        observer.join(timeout=0.1)
    result.update({'schema': 'peano-hydra-retention-bootstrap-metadata-build-v1',
                   'helper': {'path': str(Path(__file__).absolute()), **descriptor(stable_read(Path(__file__).absolute()))},
                   'limits': LIMITS, 'cpu_seconds': time.process_time() - CPU_START,
                   'wall_seconds': time.monotonic() - START, 'observed_peak_rss_bytes': peak_rss(),
                   'limit_signals': list(SIGNALS)})
    receipt_raw = encode(result)
    require(len(receipt_raw) <= 65536, 'receipt exceeds remaining total-output reservation')
    publish(RECEIPT, receipt_raw)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({'status': result['status'], 'receipt': str(RECEIPT), **descriptor(receipt_raw),
                      'output_files': result.get('output_files', {}),
                      'cpu_seconds': result['cpu_seconds'], 'wall_seconds': result['wall_seconds'],
                      'observed_peak_rss_bytes': result['observed_peak_rss_bytes']}, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'metadata-only-built' else 1)
