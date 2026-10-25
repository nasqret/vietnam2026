"""One bounded metadata-only v28 plan from the clean advancement snapshot."""
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-advancement-2026-08-30'
SOURCE = ROOT / '_deploy/hydra-advancement-execution-v2-20260830'
SUPERVISOR = ROOT / 'artifacts/frontier-training-2026-08-30/check_training_launch.py'
SUPERVISOR_SHA = '0fdb341b6aace58bb39ba37496c35844c01766362648892a1542c1bccf392612'
PLAN = ARCHIVE / 'v28-native-hotspots-plan-02.json'
RECEIPT = ARCHIVE / 'v28-native-hotspots-plan-process-02.json'
SOURCE_PIN = SOURCE / '_deploy/hydra-advancement-origin-source.json'
SOURCE_PIN_SHA = 'd503c0f0b61f1d79e4ac36bb1db61011d4dc2c3e369bc57138f8a92ac40b087d'


def main():
    assert not PLAN.exists() and not RECEIPT.exists()
    assert hashlib.sha256(SUPERVISOR.read_bytes()).hexdigest() == SUPERVISOR_SHA
    assert hashlib.sha256(SOURCE_PIN.read_bytes()).hexdigest() == SOURCE_PIN_SHA
    spec = importlib.util.spec_from_file_location('_fixed_hydra_planning_guard', SUPERVISOR)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    code = r'''
import hashlib,json,os,resource,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(30,31))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
root=Path('/Users/bnaskrecki/codex/peano/_deploy/hydra-advancement-execution-v2-20260830')
os.chdir(root)
sys.path[:0]=[str(root),str(root/'peano-lab/py')]
from training.peano_hydra.review_v28 import build_review_plan
from training.peano_hydra.frontier import canonical
plan=build_review_plan(mode='native-hotspots')
assert plan['source']['git_commit']=='1aa7ae8d61ca9e1e4f2410042b75ce9c3621a927'
assert plan['source']['git_dirty'] is False and plan['mode']=='native-hotspots'
raw=canonical(plan)+b'\n'
assert len(raw)<=4*1024**2
path=Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-advancement-2026-08-30/v28-native-hotspots-plan-02.json')
with path.open('xb') as stream: stream.write(raw)
assert not {'torch','transformers','peft','tokenizers'} & set(sys.modules)
print(json.dumps({'plan':str(path),'bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),
                  'plan_sha256':plan['plan_sha256'],'source_commit':plan['source']['git_commit'],
                  'epoch_targets':plan['cold_plan']['target_count'],'native_proofs_replayed':0,
                  'gpu_or_reference_authorization_granted':False},sort_keys=True))
'''
    command = ('/opt/homebrew/bin/python3.11', '-I', '-B', '-X', 'pycache_prefix=/dev/null', '-c', code)
    process = supervisor.trusted_local_tests(command)
    unchanged = (hashlib.sha256(SUPERVISOR.read_bytes()).hexdigest() == SUPERVISOR_SHA
                 and hashlib.sha256(SOURCE_PIN.read_bytes()).hexdigest() == SOURCE_PIN_SHA)
    passed = process['reason'] == 'exited' and process['returncode'] == 0 and unchanged
    result = {'schema': 'peano-hydra-v28-hotspot-metadata-plan-process-v1',
              'status': 'passed' if passed else 'failed', 'process': process,
              'source_pin_sha256': SOURCE_PIN_SHA, 'supervisor_sha256': SUPERVISOR_SHA,
              'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_pins_unchanged': unchanged, 'native_proofs_replayed': 0,
              'network_or_scheduler_calls': False, 'model_execution': False,
              'metadata_file_limit_bytes': 4 * 1024**2,
              'resource_scope': 'Existing trusted group supervisor; planning child narrowed to 30 CPU seconds. No proof workers.'}
    if passed:
        result['plan'] = json.loads(process['stdout'])
    raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    with RECEIPT.open('xb') as stream:
        stream.write(raw)
    print(json.dumps({'status': result['status'], 'receipt': str(RECEIPT),
                      'raw_sha256': hashlib.sha256(raw).hexdigest(), 'plan': result.get('plan')}, sort_keys=True))
    if not passed:
        print(process['stderr'])
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
