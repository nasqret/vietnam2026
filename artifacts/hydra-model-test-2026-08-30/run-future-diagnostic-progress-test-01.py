"""One bounded synthetic future-progress test; immutable current deployment is only hashed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
FROZEN = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-model-test-execution-20260830')
ARCHIVE = Path(__file__).absolute().parent
SUPERVISOR = ARCHIVE / 'run-diagnostic-integration-tests-v2.py'
OUTPUT = ARCHIVE / 'future-diagnostic-progress-test-01.json'
SOURCES = ('scripts/eval_peano_hydra_frontier_diagnostic.py',
           'training/peano_hydra/frontier_diagnostic_run.py',
           'peano-lab/py/tests/test_peano_hydra_frontier_diagnostic_progress.py')
UNCHANGED = ('training/peano_hydra/scaling_evaluation.py',
             'training/peano_hydra/comparison_checkpoint.py',
             'training/peano_hydra/origin_bridge.py',
             'training/peano_hydra/frontier_diagnostic_launch.py')

def pins(root, names):
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}

if OUTPUT.exists():
    raise SystemExit('fresh test receipt required')
source_before = pins(ROOT, SOURCES)
frozen_before = pins(FROZEN, (*SOURCES[:2], *UNCHANGED))
assert pins(ROOT, UNCHANGED) == {name: frozen_before[name] for name in UNCHANGED}
spec = importlib.util.spec_from_file_location('_retained_local_test_supervisor', SUPERVISOR)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)
code = """
import json,resource,sys
resource.setrlimit(resource.RLIMIT_CPU,(30,31))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
sys.path[:0]=[
 '/Users/bnaskrecki/Library/Python/3.10/lib/python/site-packages',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830/peano-lab/py',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830/peano-lab/py/tests']
import pytest
status=pytest.main(['-q','--maxfail=1','--tb=short','-p','no:cacheprovider',
 'peano-lab/py/tests/test_peano_hydra_frontier_diagnostic_progress.py::test_future_cli_forwards_flushed_bounded_operational_events'])
forbidden=sorted({'torch','transformers','peft','tokenizers'} & set(sys.modules))
print('FORBIDDEN_MODEL_MODULES '+json.dumps(forbidden))
assert not forbidden
raise SystemExit(status)
"""
process = supervisor.trusted_local_tests(('/Library/Frameworks/Python.framework/Versions/3.10/bin/python3',
    '-I','-B','-X','pycache_prefix=/dev/null','-c',code))
source_after = pins(ROOT, SOURCES)
frozen_after = pins(FROZEN, (*SOURCES[:2], *UNCHANGED))
result = {'schema': 'peano-hydra-future-diagnostic-progress-test-v1',
    'status': 'passed' if process['returncode'] == 0 and process['reason'] == 'exited'
        and source_before == source_after and frozen_before == frozen_after else 'failed',
    'process': process, 'source_files_before': source_before, 'source_files_after': source_after,
    'current_frozen_files_before': frozen_before, 'current_frozen_files_after': frozen_after,
    'unchanged_engine_and_gate_files': list(UNCHANGED), 'test_scope': 'One synthetic CLI-to-runner-to-engine progress forwarding, flushing and event-bound regression; no actual model/native/job execution',
    'source_changes_are_future_work_only': True, 'current_job_id': '21453693',
    'current_deployment_commit': '612d1ea9e4905dfe2af104696924a19bc5883752',
    'current_job_or_package_modified': False, 'model_loaded': False, 'native_proof_executed': False,
    'scheduler_contacted': False, 'network_contacted': False, 'deployed': False,
    'test_runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'supervisor_sha256': hashlib.sha256(SUPERVISOR.read_bytes()).hexdigest()}
with OUTPUT.open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({'status':result['status'],'path':str(OUTPUT),
    'receipt_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'process':process},sort_keys=True))
raise SystemExit(0 if result['status']=='passed' else 2)
