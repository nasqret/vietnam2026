#!/usr/bin/env python3
"""One bounded local test invocation; synthetic fixtures are not proof evidence."""
import hashlib
import json
from pathlib import Path
import sys

WORK = Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830')
ARCHIVE = Path(__file__).absolute().parent
sys.path[:0] = [str(WORK), str(WORK / 'peano-lab/py')]
import importlib.util
SUPERVISOR = Path('/Users/bnaskrecki/codex/peano/artifacts/frontier-training-2026-08-30/check_training_launch.py')
spec = importlib.util.spec_from_file_location('_reviewed_local_test_supervisor', SUPERVISOR)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)
SOURCES = (
 'training/peano_hydra/frontier_evaluation_launch.py',
 'training/peano_hydra/frontier_saved_benchmark_run.py',
 'training/peano_hydra/helios_runtime.py',
 'scripts/prepare_peano_hydra_frontier_evaluation_launch.py',
 'scripts/eval_peano_hydra_frontier_saved_benchmark.py',
 'scripts/helios_hydra_frontier_evaluation.sh',
 'scripts/run_peano_hydra_frontier_evaluation.sh',
 'slurm/peano_hydra_frontier_evaluation.sbatch',
 'peano-lab/py/tests/test_peano_hydra_frontier_evaluation_launch.py',
 'peano-lab/py/tests/test_peano_hydra_frontier_saved_benchmark.py',
 'training/peano_hydra/frontier_training_launch.py',
 'training/peano_hydra/frontier_pilot_launch.py',
 'training/peano_hydra/frontier_benchmark_run.py',
 'training/peano_hydra/frontier_benchmark_protocol.py',
 'training/peano_hydra/scaling_evaluation.py',
)
before = {name: hashlib.sha256((WORK / name).read_bytes()).hexdigest() for name in SOURCES}

CODE = r'''
import json,sys,resource
resource.setrlimit(resource.RLIMIT_CPU,(60,61))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
sys.path[:0]=[
 '/Users/bnaskrecki/Library/Python/3.10/lib/python/site-packages',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830/peano-lab/py',
 '/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-recovery-work-20260830/peano-lab/py/tests']
import pytest
status=pytest.main(['-q','--maxfail=3','--tb=short','-p','no:cacheprovider',
 'peano-lab/py/tests/test_peano_hydra_frontier_saved_benchmark.py'])
forbidden=sorted({'torch','transformers','peft','tokenizers'} & set(sys.modules))
print('FORBIDDEN_MODEL_MODULES '+json.dumps(forbidden))
assert not forbidden
raise SystemExit(status)
'''
command = ('/Library/Frameworks/Python.framework/Versions/3.10/bin/python3', '-I', '-B',
           '-X', 'pycache_prefix=/dev/null', '-c', CODE)
process = supervisor.trusted_local_tests(command)
after = {name: hashlib.sha256((WORK / name).read_bytes()).hexdigest() for name in SOURCES}
result = {'schema': 'peano-hydra-frontier-evaluation-integration-test-receipt-v1',
    'status': 'passed' if process['reason'] == 'exited' and process['returncode'] == 0 and before == after else 'failed',
    'sources_before': before, 'sources_after': after, 'sources_unchanged': before == after,
    'correction': 'Focused pretraining benchmark manifest/audit pin join regression; no historical criterion or native guard changes',
    'preceding_guard_stop_receipt': 'evaluation-integration-tests-01.json',
    'supervisor_sha256': hashlib.sha256(SUPERVISOR.read_bytes()).hexdigest(),
    'process': process, 'proof_evidence': False, 'human_approval_created': False,
    'network_contacted': False, 'gpu_execution_authorized': False,
    'test_runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target = ARCHIVE / 'evaluation-integration-tests-03.json'
with target.open('x') as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(json.dumps({'status': result['status'], 'receipt': str(target),
                  'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}))
print(process['stdout'])
if process['stderr']: print(process['stderr'], file=sys.stderr)
raise SystemExit(0 if result['status'] == 'passed' else 2)
