"""Fresh package staging plus the unchanged frozen CLI's metadata-only bind.

The only subprocess commands are bounded read-only git identity/status checks.
No model, native proof, tokenizer, network, scheduler or approval work occurs.
"""
from __future__ import annotations
import contextlib
import hashlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import resource
import runpy
import signal
import stat
import subprocess
import sys
import threading
import time

ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-retention-pilot-2026-08-30'
WORK = ROOT / '_deploy/hydra-frontier-recovery-work-20260830'
FROZEN = ROOT / '_deploy/hydra-retention-execution-20260830'
REL = Path('_deploy/hydra-retention-pilot-v1')
SOURCE, DEST = WORK / REL, FROZEN / REL
FREEZE = FROZEN / '_deploy/hydra-retention-execution-freeze.json'
FREEZE_SHA = '2cc7a302ac0156972acca3a2c7d0c4374426224c6e6493d2930a00855444bf52'
COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
BOOTSTRAP = ARCHIVE / 'bootstrap-metadata-01.json'
BOOTSTRAP_SHA = '13059932806e4cd8d5a2fb86e09a8901c2615890955f4d19d6ee30d45f2446c1'
INPUTS_SHA = '3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388'
MANIFEST_SHA = 'bb67f5f0737003d2c40b45885d7759f395f27bf0e88d358bfe1844df2a30ba21'
CLI = FROZEN / 'scripts/execute_peano_hydra_retention.py'
CLI_SHA = '7e435d11124fca0946ca74012329b1ee68dc19efb19cb8a05655b71dbd258518'
PLAN = ARCHIVE / 'training-bound-plan-local-01.json'
STAGE_RECEIPT = ARCHIVE / 'package-stage-local-01.json'
RECEIPT = ARCHIVE / 'training-bound-plan-local-01.process.json'
ARGV = [str(CLI), '--check-inputs', '--inputs', str(DEST / 'inputs.json'),
        '--expected-inputs-sha256', INPUTS_SHA, '--output', str(PLAN)]
LIMITS = {'cpu_soft_seconds': 60, 'cpu_hard_seconds': 61, 'wall_seconds': 90,
          'observed_rss_bytes': 2 * 1024**3, 'metadata_output_bytes': 4 * 1024**2,
          'staged_payload_bytes': 128 * 1024**2, 'single_staged_file_bytes': 64 * 1024**2,
          'stream_bytes_each': 65536, 'max_package_files': 32, 'max_package_directories': 16}
START, CPU_START = time.monotonic(), time.process_time()
SIGNALS, GIT_RECORDS, PHASES = [], [], []
CLI_OBSERVATION = {}
GIT_ALLOW = [('/usr/bin/git', '-C', str(FROZEN), 'rev-parse', 'HEAD'),
             ('/usr/bin/git', '-C', str(FROZEN), 'status', '--porcelain=v1', '--untracked-files=normal')]


def require(ok, message):
    if not ok: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def digest(raw): return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def signature(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def physical(path):
    require(path.is_absolute() and path.resolve(strict=True) == path, 'aliased or noncanonical path: ' + str(path))


def fingerprint(path, *, maximum=64 * 1024**2, retain=False):
    physical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                'file is not a bounded single-link regular file: ' + str(path))
        sha, count, parts = hashlib.sha256(), 0, []
        while True:
            chunk = os.read(fd, min(65536, maximum + 1 - count))
            if not chunk: break
            count += len(chunk); sha.update(chunk)
            require(count <= maximum, 'file grew past cap')
            if retain: parts.append(chunk)
        require(count == before.st_size and signature(before) == signature(os.fstat(fd)) == signature(os.lstat(path)),
                'file changed during read: ' + str(path))
        result = {'bytes': count, 'sha256': sha.hexdigest(), 'mode': stat.S_IMODE(before.st_mode)}
        return (result, b''.join(parts)) if retain else result
    finally: os.close(fd)


def small(path, expected=None, maximum=4 * 1024**2):
    desc, raw = fingerprint(path, maximum=maximum, retain=True)
    require(expected is None or desc['sha256'] == expected, 'external raw pin differs: ' + str(path))
    return raw


def content_map(inventory):
    return {name: {key: entry[key] for key in ('bytes', 'sha256')} for name, entry in inventory.items()}


def inventory(root):
    physical(root)
    files, directories = {}, []
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs):
            path = Path(current) / name
            require(stat.S_ISDIR(os.lstat(path).st_mode) and not path.is_symlink(), 'unsafe package directory')
            directories.append(path.relative_to(root).as_posix())
        require(len(directories) <= LIMITS['max_package_directories'], 'too many package directories')
        for name in sorted(names):
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            files[relative] = fingerprint(path)
            require(len(files) <= LIMITS['max_package_files'] and
                    sum(v['bytes'] for v in files.values()) <= LIMITS['staged_payload_bytes'], 'package exceeds cap')
    return dict(sorted(files.items())), sorted(directories)


def frozen_inventory(declared):
    result = {}
    require(len(declared) == 886, 'frozen source file count changed')
    for name, pin in sorted(declared.items()):
        require(not Path(name).is_absolute() and all(p not in ('', '.', '..') for p in name.split('/')), 'unsafe frozen path')
        actual = fingerprint(FROZEN / name)
        require({k: actual[k] for k in ('bytes', 'sha256')} == {k: pin[k] for k in ('bytes', 'sha256')},
                'frozen source hash changed: ' + name)
        result[name] = actual
    require(sum(v['bytes'] for v in result.values()) == 91043396, 'frozen source bytes changed')
    return result


def write_new(path, raw):
    require(len(raw) <= LIMITS['metadata_output_bytes'], 'metadata exceeds cap')
    physical(path.parent)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view); require(count > 0, 'short metadata write'); view = view[count:]
        os.fsync(fd)
    finally: os.close(fd)
    require(small(path) == raw, 'published metadata changed')


def copy_new(relative, expected):
    source, dest = SOURCE / relative, DEST / relative
    physical(source); physical(dest.parent)
    src = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(src)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
                stat.S_IMODE(before.st_mode) in (0o600, 0o644), 'unexpected input copy mode/link')
        dst = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            sha, count = hashlib.sha256(), 0
            while True:
                chunk = os.read(src, 65536)
                if not chunk: break
                count += len(chunk); sha.update(chunk)
                require(count <= expected['bytes'], 'copy source grew')
                view = memoryview(chunk)
                while view:
                    n = os.write(dst, view); require(n > 0, 'short payload write'); view = view[n:]
            require({'bytes': count, 'sha256': sha.hexdigest()} == expected and
                    signature(before) == signature(os.fstat(src)) == signature(os.lstat(source)),
                    'copy source changed')
            os.fsync(dst)
        finally: os.close(dst)
    finally: os.close(src)


def git_state():
    values = []
    for command in GIT_ALLOW:
        environment = dict(os.environ); environment['GIT_OPTIONAL_LOCKS'] = '0'
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=False,
                                env=environment)
        require(len(result.stdout) <= 65536 and len(result.stderr) <= 65536 and result.returncode == 0, 'read-only git check failed')
        values.append(result.stdout.decode()); GIT_RECORDS.append({'command': list(command), 'returncode': result.returncode,
            'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()})
    require(values == [COMMIT + '\n', ''], 'frozen Git source is not the pinned clean commit')
    return {'commit': COMMIT, 'tracked_and_visible_untracked_status': 'clean'}


def peak_rss():
    size = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(size if sys.platform == 'darwin' else size * 1024)


def phase(name):
    PHASES.append({'name': name, 'wall_seconds': time.monotonic() - START,
                   'cpu_seconds': time.process_time() - CPU_START, 'peak_rss_bytes': peak_rss()})


def audit(event, args):
    if event == 'subprocess.Popen':
        require(tuple(args[1]) in GIT_ALLOW, 'only fixed read-only git child commands are permitted')
    else:
        require(event not in {'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty',
                             'socket.__new__', 'socket.connect', 'socket.bind'}, 'network/extra child process forbidden')


class FrameworkBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        require(fullname.split('.')[0] not in {'torch', 'transformers', 'peft', 'accelerate', 'datasets', 'vllm', 'tokenizers'},
                'framework/tokenizer import forbidden for check-inputs')
        return None


class Captured(io.StringIO):
    def write(self, text):
        require(len((self.getvalue() + text).encode()) <= LIMITS['stream_bytes_each'], 'CLI stream exceeds cap')
        return super().write(text)


def main():
    for path in (DEST, PLAN, STAGE_RECEIPT, RECEIPT):
        require(not os.path.lexists(path), 'operation output already exists: ' + str(path))
    physical(DEST.parent); physical(ARCHIVE)
    freeze = json.loads(small(FREEZE, FREEZE_SHA))
    require(freeze['git_commit'] == COMMIT and freeze['status'] == 'complete' and freeze['snapshot_root'] == str(FROZEN),
            'freeze identity differs')
    source_before = frozen_inventory(freeze['files'])
    git_before = git_state()
    bootstrap = json.loads(small(BOOTSTRAP, BOOTSTRAP_SHA))
    manifest_raw = small(SOURCE / 'preparation/manifest.json', MANIFEST_SHA)
    manifest = json.loads(manifest_raw)
    expected = dict(bootstrap['output_files'])
    expected['preparation/manifest.json'] = {'bytes': len(manifest_raw), 'sha256': MANIFEST_SHA}
    for name, pin in manifest['files'].items():
        expected['preparation/' + name] = {k: pin[k] for k in ('bytes', 'sha256')}
    before, dirs = inventory(SOURCE)
    require(content_map(before) == expected and len(before) == 18 and sum(v['bytes'] for v in before.values()) == 96025573,
            'source package differs from real bootstrap/preparation pins')
    require(dirs == ['origins', 'origins/frontier-v28', 'origins/saved-v25', 'preparation'], 'package directories changed')
    require(before['inputs.json']['sha256'] == INPUTS_SHA and fingerprint(CLI)['sha256'] == CLI_SHA, 'fixed CLI/input pin differs')
    phase('inputs-and-source-pinned')
    DEST.mkdir(mode=0o700)
    for name in sorted(dirs, key=lambda value: (value.count('/'), value)):
        (DEST / name).mkdir(mode=0o700)
    for name, pin in sorted(expected.items()): copy_new(name, pin)
    source_after_copy, after_dirs = inventory(SOURCE)
    staged, staged_dirs = inventory(DEST)
    require(source_after_copy == before and after_dirs == dirs and staged_dirs == dirs and content_map(staged) == expected,
            'full package inventory changed during copy')
    phase('package-staged-and-full-hash-checked')
    stage = {'schema': 'peano-hydra-retention-package-local-staging-v1', 'status': 'exact-byte-copy',
        'source': str(SOURCE), 'destination': str(DEST), 'source_files_before': before,
        'source_files_after': source_after_copy, 'destination_files': staged, 'directories': dirs,
        'file_count': len(staged), 'total_bytes': sum(v['bytes'] for v in staged.values()),
        'freeze_sha256': FREEZE_SHA, 'source_commit': COMMIT, 'bootstrap_receipt_sha256': BOOTSTRAP_SHA,
        'preparation_manifest_sha256': MANIFEST_SHA, 'no_symlinks_or_hardlinks': True,
        'exclusive_new_destination': True, 'original_source_and_data_modified': False}
    write_new(STAGE_RECEIPT, encode(stage))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    out, err = Captured(), Captured()
    saved_argv = sys.argv
    code = 0
    try:
        sys.argv = list(ARGV)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try: runpy.run_path(str(CLI), run_name='__main__')
            except SystemExit as stop:
                code = stop.code if type(stop.code) is int else (0 if stop.code is None else 1)
    finally:
        sys.argv = saved_argv
        CLI_OBSERVATION.update({'argv': ARGV, 'execution': 'unchanged fixed CLI main via runpy.run_path',
                                'returncode': code, 'stdout': out.getvalue(), 'stderr': err.getvalue(),
                                'cli_sha256': CLI_SHA})
    phase('frozen-cli-returned')
    cli_record = dict(CLI_OBSERVATION)
    require(code == 0, 'frozen check-inputs failed: ' + err.getvalue()[:3000])
    plan_raw = small(PLAN)
    plan = json.loads(plan_raw)
    semantic = dict(plan); semantic.pop('training_plan_sha256')
    require(digest(canonical(semantic)) == plan['training_plan_sha256'] and
            (plan['training_rows'], plan['development_rows'], plan['expected_optimizer_steps']) == (11751, 2840, 1469)
            and plan['model_loaded'] is False and plan['resource_request_created'] is False
            and plan['model_training_authorized'] is False, 'actual bound plan contract differs')
    source_final = frozen_inventory(freeze['files'])
    require(source_final == source_before and inventory(SOURCE) == (before, dirs) and inventory(DEST) == (staged, dirs),
            'source/package full hash inventory changed during binding')
    require(digest(small(FREEZE)) == FREEZE_SHA and digest(small(BOOTSTRAP)) == BOOTSTRAP_SHA, 'owner input record changed')
    git_after = git_state()
    phase('full-inventories-and-git-rechecked')
    require(sum(path.stat().st_size for path in (PLAN, STAGE_RECEIPT)) + 262144 <= LIMITS['metadata_output_bytes'],
            'aggregate metadata exceeds owner cap')
    return {'status': 'inputs-bound-with-original-byte-authentication', 'cli': cli_record,
        'plan': {'path': str(PLAN), 'bytes': len(plan_raw), 'sha256': digest(plan_raw),
                 'training_plan_sha256': plan['training_plan_sha256'], 'training_rows': plan['training_rows'],
                 'development_rows': plan['development_rows'], 'expected_optimizer_steps': plan['expected_optimizer_steps']},
        'stage_receipt': {'path': str(STAGE_RECEIPT), **content_map({'x': fingerprint(STAGE_RECEIPT)})['x']},
        'source_before_inventory_sha256': digest(canonical(source_before)),
        'source_after_inventory_sha256': digest(canonical(source_final)), 'all_886_source_files_unchanged': True,
        'source_and_destination_package_inventories_unchanged': True,
        'git_before': git_before, 'git_after': git_after, 'git_checks': GIT_RECORDS,
        'freeze_sha256': FREEZE_SHA, 'inputs_sha256': INPUTS_SHA,
        'original_receipts_authenticated_and_original_data_joined': True,
        'no_token_preflight_model_native_proof_network_or_gpu': True,
        'new_resource_request_or_specific_approval_created': False}


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    require(not os.path.lexists(RECEIPT), 'owner receipt already exists')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 61))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    def stopped(number, _frame):
        SIGNALS.append({'signal': number, 'wall_seconds': time.monotonic() - START})
        raise TimeoutError('metadata owner resource limit reached')
    for number in (signal.SIGXCPU, signal.SIGALRM, signal.SIGUSR1): signal.signal(number, stopped)
    signal.setitimer(signal.ITIMER_REAL, 90)
    sys.addaudithook(audit)
    sys.meta_path.insert(0, FrameworkBlocker())
    done = threading.Event()
    def watch():
        while not done.wait(0.02):
            children = resource.getrusage(resource.RUSAGE_CHILDREN)
            if peak_rss() > LIMITS['observed_rss_bytes'] or time.process_time() - CPU_START + children.ru_utime + children.ru_stime > 60:
                os.kill(os.getpid(), signal.SIGUSR1); return
    observer = threading.Thread(target=watch, daemon=True); observer.start()
    try: result = main()
    except BaseException as error:
        chain, item = [], error
        while item is not None and len(chain) < 5:
            chain.append({'type': type(item).__name__, 'message': str(item)[:3000]})
            item = item.__cause__ or item.__context__
        result = {'status': 'failed-no-retry', 'exception_chain': chain,
                  'partial_destination_preserved': os.path.lexists(DEST),
                  'plan_exists': os.path.lexists(PLAN), 'git_checks': GIT_RECORDS,
                  'cli': dict(CLI_OBSERVATION)}
    finally: done.set(); observer.join(timeout=0.1)
    result.update({'schema': 'peano-hydra-retention-local-input-bind-process-v1', 'limits': LIMITS,
        'pid': os.getpid(), 'python': str(Path(sys.executable).resolve()),
        'helper': {'path': str(Path(__file__).absolute()), 'sha256': digest(small(Path(__file__).absolute()))},
        'wall_seconds': time.monotonic() - START, 'cpu_seconds': time.process_time() - CPU_START,
        'children_cpu_seconds': sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2]),
        'observed_peak_rss_bytes': peak_rss(), 'phase_observations': PHASES, 'resource_signals': SIGNALS})
    raw = encode(result); require(len(raw) <= 262144, 'process receipt exceeds reserved output cap')
    write_new(RECEIPT, raw)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({'status': result['status'], 'receipt': str(RECEIPT), 'bytes': len(raw), 'sha256': digest(raw),
                      'plan': result.get('plan'), 'cpu_seconds': result['cpu_seconds'],
                      'wall_seconds': result['wall_seconds'], 'observed_peak_rss_bytes': result['observed_peak_rss_bytes']}, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'inputs-bound-with-original-byte-authentication' else 1)
