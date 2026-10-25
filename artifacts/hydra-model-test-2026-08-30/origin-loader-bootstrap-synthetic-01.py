#!/usr/bin/env python3
"""Tiny import-only reproduction; never an origin, native replay or model check.

Run with an installed Python >=3.10. Only four raw-pinned bridge bootstrap
files plus small authored fixture modules are copied into one fresh temporary
directory. The frozen loader is executed unchanged. No __file__ value, loader
guard or sys.modules entry named __main__ is modified.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / '_deploy/hydra-frontier-training-execution-20260830'
HELPER = HERE / 'origin-check-remote-04.py'
PREVIOUS = HERE / 'origin-check-remote-03.py'
START = time.monotonic()

DRIVER = r"""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import sys
import time

resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (16384, 16384))
signal.alarm(4)
started = time.monotonic()
root, bootstrap, case = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
spec = importlib.util.spec_from_file_location('bridge_bootstrap_fixture', bootstrap)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
files = {}
for relative in (
    'training/peano_hydra/__init__.py', 'training/peano_hydra/probe.py',
    'scripts/bootstrap_probe.py', 'scripts/untracked_probe.py',
):
    raw = (root / relative).read_bytes()
    files[relative] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
with bridge._Tree(root) as tree:
    finder = bridge._SourceFinder(tree, files)
    sys.meta_path.insert(0, finder)
    probe = importlib.import_module('training.peano_hydra.probe')
    assert probe.VALUE == 'synthetic-pinned-source'
    assert 'training.peano_hydra.probe' in finder.loaded
    if case == 'untracked':
        spec2 = importlib.util.spec_from_file_location(
            'untracked_fixture', root / 'scripts/untracked_probe.py')
        module2 = importlib.util.module_from_spec(spec2)
        sys.modules[spec2.name] = module2
        spec2.loader.exec_module(module2)
    try:
        loaded = finder.validate_loaded()
    except bridge.OriginBridgeError as error:
        assert str(error) == 'original code bypassed the pinned source-only loader'
        assert case in {'inside', 'untracked'}
        status = 'expected-inside-root-rejection' if case == 'inside' else 'untracked-source-import-rejected'
        if case == 'inside':
            assert Path(sys.modules['__main__'].__file__).is_relative_to(root)
            assert '__main__' not in finder.loaded
        else:
            assert 'untracked_fixture' not in finder.loaded
    else:
        assert case == 'external'
        assert not Path(sys.modules['__main__'].__file__).is_relative_to(root)
        assert not Path(bridge.__file__).is_relative_to(root)
        assert set(loaded) == {'training.peano_hydra', 'training.peano_hydra.probe'}
        assert getattr(sys.modules['training'], '__file__', None) is None
        status = 'external-controller-import-check-passed'
    finally:
        sys.meta_path.remove(finder)
assert not any(name == first or name.startswith(first + '.')
               for name in sys.modules for first in ('torch', 'transformers', 'peft', 'tokenizers', 'peano_lab'))
usage = resource.getrusage(resource.RUSAGE_SELF)
rss = int(usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024))
assert rss <= 256 * 1024**2
print(json.dumps({
    'case': case, 'status': status,
    'cpu_seconds': usage.ru_utime + usage.ru_stime,
    'wall_seconds': time.monotonic() - started,
    'peak_rss_bytes': rss,
    'native_validation_performed': False,
    'model_frameworks_imported': False,
    'authenticated_origin': False,
}, sort_keys=True))
"""

def snapshot(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def run_case(command):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout,
                                   stderr=stderr, timeout=5, check=False)
        assert os.fstat(stdout.fileno()).st_size <= 16384
        assert os.fstat(stderr.fileno()).st_size <= 16384
        stdout.seek(0)
        stderr.seek(0)
        output, errors = stdout.read(16384), stderr.read(16384)
    assert completed.returncode == 0, errors.decode(errors='replace')
    assert not errors
    result = json.loads(output)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    result['parent_reaped_child_cpu_delta_seconds'] = (
        after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime)
    return result


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    signal.alarm(12)
    assert sys.version_info >= (3, 10)
    helper_raw = HELPER.read_bytes()
    previous_raw = PREVIOUS.read_bytes()
    new_ast, old_ast = ast.parse(helper_raw), ast.parse(previous_raw)
    ns = {'__name__': 'synthetic_helper_metadata', '__file__': str(HELPER)}
    exec(compile(helper_raw, str(HELPER), 'exec'), ns)
    assert str(ns['OUT']).endswith('/frontier-origin-check-20260830-04')
    assert ns['SUPPORT_ROOT'].parent == ns['OUT']
    assert ns['SCHEMA'] == 'peano-hydra-frontier-origin-check-control-v4'
    assert ns['SUPPORT_TOTAL_BYTES'] == 87458
    assert ns['MAX_SUPPORT_FILE_BYTES'] == 65536
    assert ns['MAX_SUPPORT_TOTAL_BYTES'] == 131072
    old_functions = {n.name:n for n in old_ast.body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name:n for n in new_ast.body if isinstance(n, ast.FunctionDef)}
    for name in ('read', 'directory', 'budget', 'exception_chain', 'diagnostics'):
        assert ast.dump(old_functions[name]) == ast.dump(new_functions[name]), name
    def calls(tree, label):
        return [ast.dump(n) for n in ast.walk(tree) if isinstance(n, ast.Call)
                and label in ast.dump(n.func)]
    for label in ('setrlimit', 'authenticate_origin', 'alarm', 'signal'):
        assert calls(old_functions['main'], label) == calls(new_functions['main'], label), label
    pins_before = {name:snapshot(SOURCE / name) for name in ns['SUPPORT_IDENTITIES']}
    assert pins_before == ns['SUPPORT_IDENTITIES']
    records = []
    with tempfile.TemporaryDirectory(prefix='hydra-origin-loader-', dir='/private/tmp') as temporary:
        base = Path(temporary).resolve()
        original, execution = base / 'original', base / 'execution'
        for target_root in (original, execution):
            for name in ns['SUPPORT_IDENTITIES']:
                target = target_root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((SOURCE / name).read_bytes())
        assert ns['check_support_root'](execution) == ns['support_payloads'](SOURCE)
        extra = execution / 'scripts/unexpected.py'
        extra.write_bytes(b'# explicitly unlisted synthetic bootstrap file\n')
        try:
            ns['check_support_root'](execution)
        except ValueError:
            pass
        else:
            raise AssertionError('support root accepted an extra importable file')
        extra.unlink()
        (original / 'training/peano_hydra/probe.py').write_bytes(
            b"VALUE = 'synthetic-pinned-source'\n")
        (original / 'scripts/untracked_probe.py').write_bytes(
            b"VALUE = 'synthetic-untracked-source'\n")
        inside_driver = original / 'scripts/bootstrap_probe.py'
        outside_driver = base / 'bootstrap_probe.py'
        inside_driver.write_text(DRIVER)
        outside_driver.write_text(DRIVER)
        for case in ('inside', 'external', 'untracked'):
            driver = inside_driver if case == 'inside' else outside_driver
            bridge_root = original if case == 'inside' else execution
            command = [sys.executable, '-I', '-B', '-X', 'pycache_prefix=/dev/null',
                       str(driver), str(original),
                       str(bridge_root / 'training/peano_hydra/origin_bridge.py'), case]
            records.append(run_case(command))
        assert ns['check_support_root'](execution) == ns['support_payloads'](SOURCE)
    assert {name:snapshot(SOURCE / name) for name in pins_before} == pins_before
    assert HELPER.read_bytes() == helper_raw and PREVIOUS.read_bytes() == previous_raw
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024))
    assert rss <= 256 * 1024**2
    record = {
        'schema': 'peano-hydra-origin-bootstrap-import-fixture-v1',
        'status': 'three-import-only-fixtures-and-bootstrap-guards-passed',
        'helper': snapshot(HELPER), 'previous_helper': snapshot(PREVIOUS),
        'probe': snapshot(Path(__file__)), 'exact_source_support': pins_before,
        'cases': records,
        'outer_self_cpu_seconds': usage.ru_utime + usage.ru_stime,
        'outer_peak_rss_bytes': rss, 'wall_seconds': time.monotonic() - START,
        'bounds': {'outer_self_cpu_seconds':5, 'outer_wall_seconds':12,
                   'child_count':3, 'each_child_cpu_seconds':2, 'each_child_wall_seconds':4,
                   'each_child_stream_bytes':16384, 'checked_rss_bytes':256 * 1024**2},
        'original_source_changed': False, 'loader_guard_changed': False,
        'main_module_or_file_location_rewritten': False,
        'native_validation_performed': False, 'model_frameworks_imported': False,
        'remote_or_scheduler_activity': False, 'authenticated_origin': False,
        'scope': 'Tiny synthetic import fixture only; no original-origin receipt or native-validation claim.',
    }
    print(json.dumps(record, indent=2, sort_keys=True))
    signal.alarm(0)


if __name__ == '__main__':
    main()

