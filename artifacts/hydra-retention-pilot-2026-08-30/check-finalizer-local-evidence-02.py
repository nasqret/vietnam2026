"""Pure metadata fixtures; never call the finalizer, gate or tokenizer."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
OLD = ARCHIVE / 'finalize-retention-controls-01.py'
NEW = ARCHIVE / 'finalize-retention-controls-02.py'
OUT = ARCHIVE / 'finalizer-local-evidence-checks-02.json'
OLD_SHA = 'f49173753cff7a5c4281fd803aabf0214fd702644bf1b09169c365568de0205e'
NEW_SHA = 'c022da64313b771ffe15e85429c34764c264d9f4247f4c1e8f60dc1d597019a0'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    started, cpu = time.monotonic(), time.process_time()
    resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixture wall cap')))
    signal.alarm(15)
    old_raw, new_raw = OLD.read_bytes(), NEW.read_bytes()
    assert sha(old_raw) == OLD_SHA and sha(new_raw) == NEW_SHA
    old_ast, new_ast = ast.parse(old_raw), ast.parse(new_raw)
    definitions = lambda tree: {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    old_defs, new_defs = definitions(old_ast), definitions(new_ast)
    unchanged = sorted(set(old_defs) - {'prepare', 'main'})
    assert all(ast.dump(old_defs[name], include_attributes=False) == ast.dump(new_defs[name], include_attributes=False)
               for name in unchanged)
    assert set(new_defs) - set(old_defs) == {'validate_local_cpu'}
    def constant(tree, name):
        return next(ast.dump(n.value, include_attributes=False) for n in tree.body if isinstance(n, ast.Assign)
                    and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name)
    assert constant(old_ast, 'LIMITS') == constant(new_ast, 'LIMITS')
    assert constant(old_ast, 'CONTROL_NAMES') == constant(new_ast, 'CONTROL_NAMES')
    # Loading definitions has no entrypoint side effects. Only this pure guard
    # is exercised; synthetic success is never published as real CPU evidence.
    spec = importlib.util.spec_from_file_location('finalizer02_fixture_definitions', NEW)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    preflight_pin = {'bytes': 1, 'sha256': 'a' * 64}
    runtime_pin = {'bytes': 1, 'sha256': 'b' * 64}
    ssh_pin = {'bytes': 1, 'sha256': 'c' * 64}
    runtime = {'runtime': '/synthetic/tokenizer-runtime', 'cache_root': '/synthetic/tokenizer-runtime/cache'}
    record = {
        'schema': 'peano-hydra-retention-local-tokenizer-preflight-process-v2', 'status': 'passed',
        'returncode': 0, 'error': None, 'source_commit': module.COMMIT, 'source_root': str(module.FROZEN),
        'inputs_sha256': module.INPUTS_SHA, 'cli_sha256': module.CLI_SHA,
        'local_plan_raw_sha256': module.LOCAL_PLAN_SHA, 'local_plan_sha256': module.LOCAL_PLAN_SEMANTIC,
        'archived_local_plan_equal': True, 'source_files_unchanged': True,
        'input_pins_unchanged': True, 'owned_group_quiescent': True,
        'model_weights_loaded': False, 'gpu_allocated': False, 'native_proofs_executed': False,
        'network_contacted': False, 'ssh_contacted': False, 'automatic_retry': False, 'resume': False,
        'preflight': {'path': str(module.PREFLIGHT), **preflight_pin},
        'runtime_manifest': {'path': str(module.RUNTIME_MANIFEST), **runtime_pin},
        'runtime_root': runtime['runtime'], 'hf_cache_root': runtime['cache_root'],
        'previous_remote_failure': {'path': str(module.CPU_SSH), **ssh_pin},
        'limits': dict(module.LOCAL_PREFLIGHT_LIMITS),
        'measurements': {'accounted_whole_cpu_seconds': 10.0, 'whole_wall_seconds': 12.0,
                         'parent_peak_rss_bytes': 1024, 'peak_sampled_parent_plus_group_rss_bytes': 2048}}
    kwargs = {'preflight_pin': preflight_pin, 'runtime': runtime, 'runtime_pin': runtime_pin, 'ssh_pin': ssh_pin}
    module.validate_local_cpu(record, **kwargs)
    cases = {'valid_explicitly_synthetic_metadata': 'passed'}
    changes = {
        'remote_schema_cannot_be_relabelled_local': lambda r: r.update(schema='peano-hydra-retention-cpu-preflight-process-v1'),
        'failed_process_not_admitted': lambda r: r.update(status='failed', returncode=1, error='synthetic failure'),
        'boolean_exit_code_not_zero_exit': lambda r: r.update(returncode=False),
        'wrong_runtime_pin_rejected': lambda r: r['runtime_manifest'].update(sha256='d' * 64),
        'remote_output_path_not_local_evidence': lambda r: r['preflight'].update(path='/synthetic/remote/output.json'),
        'missing_quiescence_rejected': lambda r: r.update(owned_group_quiescent=False),
        'native_proof_scope_rejected': lambda r: r.update(native_proofs_executed=True),
        'cpu_boundary_rejected': lambda r: r['measurements'].update(accounted_whole_cpu_seconds=180),
        'nonfinite_measurement_rejected': lambda r: r['measurements'].update(whole_wall_seconds=float('nan')),
        'expanded_limits_rejected': lambda r: r['limits'].update(whole_wall_seconds=301),
    }
    for name, mutate in changes.items():
        value = copy.deepcopy(record); mutate(value)
        try: module.validate_local_cpu(value, **kwargs)
        except ValueError: cases[name] = 'passed'
        else: raise AssertionError(name)
    assert NEW.read_bytes() == new_raw and OLD.read_bytes() == old_raw
    assert not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules)
    result = {'schema': 'peano-hydra-retention-finalizer-local-evidence-fixtures-v1', 'status': 'passed',
        'original_source_sha256': OLD_SHA, 'reviewed_source_sha256': NEW_SHA,
        'syntax_checked': True, 'unchanged_ast_definitions': unchanged, 'unchanged_resource_caps_and_control_names': True,
        'harness_note': 'Initial literal_eval check rejected arithmetic cap expressions before any fixture; changed only the checker to compare their complete ASTs.',
        'cases': cases, 'synthetic_cases_are_not_actual_preflight_evidence': True,
        'finalizer_main_or_prepare_invoked': False, 'gate_or_git_invoked': False,
        'actual_control_files_written': False, 'network_model_tokenizer_native_execution': False,
        'cpu_seconds': time.process_time() - cpu, 'wall_seconds': time.monotonic() - started,
        'peak_rss_bytes': int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
    raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    signal.alarm(0)
    print(json.dumps({'status': 'passed', 'cases': len(cases), 'receipt': str(OUT), 'bytes': len(raw), 'sha256': sha(raw)}, sort_keys=True))


if __name__ == '__main__':
    main()
