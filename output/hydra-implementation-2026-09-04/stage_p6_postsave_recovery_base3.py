"""Explicit Base3 recovery: three new files and a separately recorded CPU check.

Output-only preparation. Every actual phase requires the new approval record for
this exact rejected payload/action; the earlier source08 approval is not reused.
Each invocation performs at most one SSH operation and no scheduler calls. The
CPU verifier uses inference-only source09 while preserving source07 training.
The exact EL8 Python+libffi environment is unchanged from observed diagnosis04.
Run stage, verify, collect and stage-actual separately. Only after verify's real
successful exit may root create metadata-actual-completion-base3.json. This
driver never invents that receipt, a completion chunk or a model reload result.
"""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import importlib.util
import json
import re
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKAGE = HERE / "p6-postsave-recovery-v3"
OUT = HERE / "p6-postsave-metadata-base3-01"
REVIEW = HERE / "p6-upload-review-02"
PREPARED_SHA = "49ff6678f8afcf84eb3ced73c6f81277cafb5bffa292e7149b4e92e682d1f39c"
RUNTIME_MANIFEST_SHA = "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"
PREDECESSOR_SHA = "89445ede120c97709fc6675e2e4683f08e04d0ff9705ae73c94404eaeb1da841"
HELPERS = {"p6_smoke_transport.py": "6587fb953d693abfb76223c4a1fbd9dc8ace424f13e09017237a1a1240193d55",
           "stage_p6_remote.py": "da136813840325da6c211169745a66c546dfc174a9d3a45d9475a7da96666f81"}
PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
PYTHON_LIB = '/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib:/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64'
OLD_INPUT_PINS = {
    "metadata_recovery.py": {"bytes": 25101, "sha256": "1f485e4207430fb3bc9d42849053cbc7bf32eb07dda789f6c0c9e63d5c07b86e"},
    "gpu_saved_reload.py": {"bytes": 20056, "sha256": "573b4522cc94b5af2d03c17216fd34163882a25746f190f59a91bf969072ff5a"},
    "controller-source-pins.json": {"bytes": 99834, "sha256": "898f5b8a1ee68b7201a397acc9b7e353910453e261386881979c86f715b44547"},
    "observation013.json": {"bytes": 5019, "sha256": "a1d56e0e322a8b3f49d2ecd51da21309efe3ccc6cd091c3482edebef10375923"},
    "observation013-transport.json": {"bytes": 320, "sha256": "ac2b0deec46aaac68a7fc0405b6d28acab8c8157b0b45c95a0b52ac55b388269"},
}

PINS = {'metadata_recovery_base3.py': {'bytes': 33724, 'sha256': '3f11a9e6ef501cc4834662f01a4dd7a388892f71cae1bc70ad4a272524c5d2be'}, 'gpu_saved_reload_base3.py': {'bytes': 26760, 'sha256': '7cea491f147d7feebc6478cd0589965df9c4ac106e0bbf03e3c15243c3064639'}, 'runtime-source-pins-base3.json': {'bytes': 99834, 'sha256': 'd981ef26de980dc983b3f0efd0885d46aaf2a08767e34b924e83632928f8cb5f'}}
PREVIOUS_FAILURE_PINS = {'metadata-recovery.json': {'bytes': 8380, 'sha256': '81573ee064690fee6223c4721e176fc05d36558e457748adf467f042d26a49cd'}, 'metadata-invocation.json': {'bytes': 1424, 'sha256': 'fc600a5c142893c82b0c89afcd62be1a11ee37d42ef517b1e167f09122846ca0'}, 'metadata-process-completion.json': {'bytes': 359, 'sha256': 'e16a3a874b95919e235a79ef562d577aa90418394efe9f655f4f79768afe567a'}, 'metadata-stdout.txt': {'bytes': 266, 'sha256': 'cd20dcecfa6e2233af2d7d851cd816f0c09dec60ebb4e07896f72f021fc532ef'}, 'metadata-stderr.txt': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, 'metadata-recovery-env2.json': {'bytes': 8376, 'sha256': '9cf80bbb214e410de16e3579e8aaa7a6408a7618c6ad190bc6252fc878b61c7d'}, 'metadata-env2-invocation.json': {'bytes': 1684, 'sha256': 'add8b4891133cc19d0c1bbd34cc2a5784254324e45c66e8de2066b9b5258af60'}, 'metadata-env2-process-completion.json': {'bytes': 359, 'sha256': 'a8a623d3f80443682c9408e5f0e63221975cf6992cf69a378430bb181cce7851'}, 'metadata-env2-stdout.txt': {'bytes': 262, 'sha256': '925b5b1847ea97dac8900ffc7a3b82584af3540c2eef538f6f6ee211e8efd36d'}, 'metadata-env2-stderr.txt': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}}
COLLECT_NAMES = (
    "metadata-recovery-base3.json", "metadata-recovery-base3.prepared-plan.json",
    "metadata-recovery-base3.runtime-plan.json", "metadata-base3-invocation.json",
    "metadata-base3-process-completion.json", "metadata-base3-stdout.txt", "metadata-base3-stderr.txt",
    "metadata-recovery-base3.admission-failure/expected-manifest.json",
    "metadata-recovery-base3.admission-failure/regenerated-manifest.json",
    "metadata-recovery-base3.admission-failure/diff.json",
)

REMOTE_TEMPLATE = r'''
import base64,hashlib,json,os,re,signal,stat,subprocess,sys,time
from pathlib import Path
PINS = json.loads(__PINS_JSON__)
OLD_INPUT_PINS = json.loads(__OLD_PINS_JSON__)
PREVIOUS_FAILURE_PINS = json.loads(__FAILED_PINS_JSON__)
COLLECT_NAMES = json.loads(__COLLECT_NAMES_JSON__)
PREPARED_SHA = '__PREPARED_SHA__'
RUNTIME_MANIFEST_SHA = '__RUNTIME_MANIFEST_SHA__'
CAMPAIGN=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
DIRECTORY=CAMPAIGN/'recovery/p6-postsave-recovery-v1'
SOURCE=CAMPAIGN/'bundles/source-data-07/source'
RUNTIME_SOURCE=CAMPAIGN/'bundles/source-data-09/source'
PYTHON='/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3'
LIB='/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib:/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64'
MAX=2*1024**2
def require(ok,message):
 if not ok: raise ValueError(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(path,limit=MAX):
 require(path.resolve(strict=True)==path and not path.is_symlink(),'Nonordinary input path')
 before=path.stat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'Input bound/type')
 with path.open('rb') as stream:raw=stream.read(limit+1)
 after=path.stat()
 require(len(raw)==before.st_size and all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')),'Input changed')
 return raw
def save(name,value):
 raw=canonical(value)+b'\n';require(len(raw)<=MAX,'Output bound')
 with (DIRECTORY/name).open('xb') as stream:stream.write(raw)
def verify_previous_inputs():
 require(DIRECTORY.resolve(strict=True)==DIRECTORY and DIRECTORY.is_dir(),'Wrong staged directory')
 for name,expected in OLD_INPUT_PINS.items():require(pin(read(DIRECTORY/name))==expected,'Original staged input changed: '+name)
 for name,expected in PREVIOUS_FAILURE_PINS.items():require(pin(read(DIRECTORY/name))==expected,'Previous failed output changed: '+name)
def verify_inputs():
 verify_previous_inputs()
 for name,expected in PINS.items():require(pin(read(DIRECTORY/name))==expected,'New staged input hash differs: '+name)
def validate_authority(request):
 for key in ('pending_action_sha256','approval_sha256','driver_sha256'):
  require(type(request.get(key)) is str and re.fullmatch('[0-9a-f]{64}',request[key]),'Missing exact authorization identity')
 pending_raw=base64.b64decode(request['pending_action_base64'],validate=True)
 approval_raw=base64.b64decode(request['approval_base64'],validate=True)
 require(len(pending_raw)<=16384 and len(approval_raw)<=8192,'Authorization record bound')
 require(pin(pending_raw)['sha256']==request['pending_action_sha256'] and pin(approval_raw)['sha256']==request['approval_sha256'],
  'Authorization record bytes differ')
 pending=json.loads(pending_raw);approval=json.loads(approval_raw)
 require(type(pending) is dict and pending.get('recovery_prepared_sha256')==PREPARED_SHA
  and pending.get('runtime_manifest_sha256')==RUNTIME_MANIFEST_SHA and pending.get('cpu_driver_sha256')==request['driver_sha256'],
  'Pending action does not bind this exact Base3 payload, runtime and CPU driver')
 require(type(approval) is dict and approval.get('status')=='approved_by_user'
  and approval.get('pending_action_sha256')==request['pending_action_sha256'],'The new specific action is not approved')
def stage_inputs(request):
 verify_previous_inputs()
 require(type(request.get('files')) is dict and set(request['files'])==set(PINS),'Only the three new Base3 files may be staged')
 decoded={};total=0
 for name,expected in PINS.items():
  require(not (DIRECTORY/name).exists() and not (DIRECTORY/name).is_symlink(),'A new Base3 input already exists; no overwrite/retry')
  item=request['files'][name]
  require(type(item) is dict and set(item)=={'bytes','sha256','base64'} and {k:item[k] for k in ('bytes','sha256')}==expected,
   'New file descriptor differs: '+name)
  raw=base64.b64decode(item['base64'],validate=True);total+=len(raw)
  require(pin(raw)==expected and total<=160318,'New file bytes differ: '+name)
  decoded[name]=raw
 require(total==160318,'New payload total differs')
 for name,raw in decoded.items():
  with (DIRECTORY/name).open('xb') as stream:stream.write(raw)
  (DIRECTORY/name).chmod(0o444)
 verify_inputs()
 return {'files':PINS,'bytes':total,'original_inputs_unchanged':True,'both_failed_cpu_attempts_unchanged':True,
  'cpu_process_started':False,'model_loaded':False}
def successful_metadata():
 raw=read(DIRECTORY/'metadata-recovery-base3.json');value=json.loads(raw)
 expected={'schema':'hydra-p6-postsave-metadata-recovery-v2','passed':True,'eligible_for_saved_reload':True,
  'saved_adapter_reload_required':True,'model_loaded':False,'errors':[],'sources_unchanged':True,
  'metadata_source_sha256':PINS['metadata_recovery_base3.py']['sha256'],
  'job_id':'21912020','original_slurm_state':'FAILED','original_slurm_exit_code':'1:0',
  'original_process_exit_code':1,'original_controller_completed':False,
  'training_source_root':str(SOURCE),'training_source_pins_sha256':'11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c',
  'training_provider_sha256':'7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f',
  'runtime_source_root':str(RUNTIME_SOURCE),'runtime_source_pins_sha256':'85dadd08b91c9678fa8be1cf9624a82a5e0470b1c29f5a2f8cc25c7716a76f55',
  'runtime_provider_sha256':'cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44',
  'runtime_manifest_sha256':RUNTIME_MANIFEST_SHA,'runtime_inference_only':True,'runtime_training_execution_allowed':False,
  'original_recorded_saved_plan_canonical_json_equal':True,'runtime_plan_matches_exact_provider_rebinding':True,
  'training_exposure_changed':False,
  'manifest_sha256':'3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135',
  'final_tensor_population_sha256':'2499801811ee63fb4f6c20e022d59aa0eeb2bb202ee41c9edd6bcd271e646c3c',
  'runtime_regenerated_plan_sha256':'77119db9f4a4ef1b6a3bcb78dea8c28d7f4008671099154f84f8a18a9e86bb1f'}
 require(type(value) is dict and all(type(value.get(k)) is type(v) and value.get(k)==v for k,v in expected.items()),
  'CPU metadata recovery did not pass the exact original-training/new-runtime contract')
 return raw
def cpu_run():
 verify_inputs()
 require(not (DIRECTORY/'metadata-recovery-base3.json').exists(),'CPU result already exists; no retry')
 require(RUNTIME_SOURCE.resolve(strict=True)==RUNTIME_SOURCE and RUNTIME_SOURCE.is_dir(),'New ordinary inference runtime is not staged')
 runtime_manifest=read(RUNTIME_SOURCE.parent/'manifest.json')
 require(pin(runtime_manifest)['sha256']==RUNTIME_MANIFEST_SHA,'New inference runtime manifest differs')
 runtime=json.loads(runtime_manifest)
 require(runtime.get('inference_only') is True and runtime.get('training_execution_allowed') is False,'Runtime is not inference-only')
 argv=[PYTHON,'-B',str(DIRECTORY/'metadata_recovery_base3.py'),'--source-root',str(SOURCE),
  '--runtime-source-root',str(RUNTIME_SOURCE),
  '--job-directory',str(CAMPAIGN/'jobs/p6-training-fresh-1.7b-v2-01'),
  '--observation',str(DIRECTORY/'observation013.json'),'--transport',str(DIRECTORY/'observation013-transport.json'),
  '--output',str(DIRECTORY/'metadata-recovery-base3.json')]
 save('metadata-base3-invocation.json',{'schema':'hydra-postsave-cpu-invocation-v1','argv':argv,
  'metadata_source_sha256':PINS['metadata_recovery_base3.py']['sha256'],'cpu_seconds':90,'wall_seconds':120,
  'address_space_bytes':2*1024**3,'automatic_retry':False,'gpu_allocations':0,
  'environment_revision':'el8-libffi-env2','recovery_revision':'base3-inference-runtime09','python':PYTHON,'ld_library_path':LIB})
 env=dict(os.environ)
 for name in ('PYTHONPATH','PYTHONHOME'):env.pop(name,None)
 env.update(LD_LIBRARY_PATH=LIB,PYTHONHASHSEED='20260904',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
 process=None;code=None;reaped=False;reason=None;started=time.monotonic()
 with (DIRECTORY/'metadata-base3-stdout.txt').open('xb') as stdout,(DIRECTORY/'metadata-base3-stderr.txt').open('xb') as stderr:
  try:
   process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,env=env,cwd=RUNTIME_SOURCE,start_new_session=True)
   while process.poll() is None:
    if time.monotonic()-started>=140:reason='owned_metadata_wall_limit';break
    if os.fstat(stdout.fileno()).st_size+os.fstat(stderr.fileno()).st_size>MAX:reason='owned_metadata_output_limit';break
    time.sleep(0.05)
  except BaseException as failure:reason=type(failure).__name__+': '+str(failure)[:1000]
  finally:
   if process is not None:
    if process.poll() is None:process.kill()
    try:code=process.wait(timeout=3);reaped=True
    except subprocess.TimeoutExpired:reason='owned_metadata_child_not_reaped'
   if os.fstat(stdout.fileno()).st_size+os.fstat(stderr.fileno()).st_size>MAX:reason=reason or 'owned_metadata_output_limit'
 receipt={'schema':'hydra-postsave-cpu-process-v1','actual_metadata_process_exit_code':code,
  'owned_child_reaped':reaped,'stop_reason':reason,'elapsed_seconds':time.monotonic()-started,
  'metadata_source_sha256':PINS['metadata_recovery_base3.py']['sha256'],'automatic_retry':False,
  'gpu_allocations':0,'model_calls':0,'optimizer_updates':0,'native_proof_runs':0}
 save('metadata-base3-process-completion.json',receipt)
 require(code==0 and reaped and reason is None,'Actual CPU metadata process did not complete successfully')
 metadata=successful_metadata();verify_inputs()
 return {'process':receipt,'metadata_recovery':pin(metadata),'actual_completion_companion_created':False}
os.umask(0o077)
def expired(signum,frame):raise TimeoutError('Bounded recovery phase expired; no retry')
signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGTERM,expired);signal.alarm(180)
response={'schema':'hydra-postsave-cpu-phase-v2','completed':False,'error':None,'automatic_retry':False,'gpu_allocations':0}
try:
 require(os.getuid()==105923 and Path(sys.executable).resolve()==Path(PYTHON).resolve(),'Wrong CPU interpreter/owner')
 raw=sys.stdin.buffer.read(256*1024+1);require(len(raw)<=256*1024,'Input bound')
 request=json.loads(raw);phase=request['phase'];response['phase']=phase
 require(phase in ('stage','verify','collect','stage-actual'),'Unknown phase')
 validate_authority(request)
 if phase=='stage':response['result']=stage_inputs(request)
 elif phase=='verify':response['result']=cpu_run()
 elif phase=='collect':
  verify_inputs();files={};total=0
  for name in COLLECT_NAMES:
   path=DIRECTORY/name
   if not path.exists():continue
   raw=read(path);total+=len(raw);require(total<=8*1024**2,'Collection total bound')
   files[name]={**pin(raw),'base64':base64.b64encode(raw).decode()}
  response['result']={'files':files,'bytes':total,'read_only':True,'collection_is_not_cpu_success':True}
 else:
  verify_inputs();metadata=successful_metadata()
  process=json.loads(read(DIRECTORY/'metadata-base3-process-completion.json'))
  require(process.get('actual_metadata_process_exit_code')==0 and process.get('owned_child_reaped') is True
   and process.get('stop_reason') is None,'No actual successful owned CPU process receipt')
  raw=base64.b64decode(request['actual_base64'],validate=True);require(len(raw)<=65536 and pin(raw)['sha256']==request['actual_sha256'],'Actual companion hash/bound')
  value=json.loads(raw)
  require(set(value)=={'schema','actual_exit_code','completion_chunk','receipt_sha256','verifier_sha256'}
   and value['schema']=='hydra-p6-postsave-metadata-actual-completion-v1'
   and type(value['actual_exit_code']) is int and value['actual_exit_code']==0
   and value['receipt_sha256']==pin(metadata)['sha256'] and value['verifier_sha256']==PINS['metadata_recovery_base3.py']['sha256']
   and isinstance(value['completion_chunk'],str) and re.fullmatch('[0-9a-f]{6,64}',value['completion_chunk']),
   'Root must supply its separately observed real completion companion')
  with (DIRECTORY/'metadata-actual-completion-base3.json').open('xb') as stream:stream.write(raw)
  (DIRECTORY/'metadata-actual-completion-base3.json').chmod(0o444)
  require(read(DIRECTORY/'metadata-actual-completion-base3.json')==raw,'Actual companion changed on transfer')
  response['result']={'actual_companion':pin(raw),'created_by_root_not_this_driver':True}
 response['completed']=True
except BaseException as failure:response['error']={'type':type(failure).__name__,'detail':str(failure)[:1600]}
finally:
 try:verify_previous_inputs()
 except BaseException as failure:
  response['completed']=False
  response['preserved_inputs_check_error']={'type':type(failure).__name__,'detail':str(failure)[:1600]}
  response['error']=response['error'] or response['preserved_inputs_check_error']
 finally:signal.alarm(0)
raw=canonical(response)+b'\n';require(len(raw)<=12*1024**2,'Response bound')
sys.stdout.buffer.write(raw);sys.stdout.buffer.flush()
raise SystemExit(0 if response['completed'] else 1)
'''
REMOTE = (REMOTE_TEMPLATE.replace("__PINS_JSON__", repr(json.dumps(PINS, sort_keys=True)))
          .replace("__OLD_PINS_JSON__", repr(json.dumps(OLD_INPUT_PINS, sort_keys=True)))
          .replace("__FAILED_PINS_JSON__", repr(json.dumps(PREVIOUS_FAILURE_PINS, sort_keys=True)))
          .replace("__COLLECT_NAMES_JSON__", repr(json.dumps(COLLECT_NAMES)))
          .replace("__PREPARED_SHA__", PREPARED_SHA)
          .replace("__RUNTIME_MANIFEST_SHA__", RUNTIME_MANIFEST_SHA))


def read(path, expected=None, maximum=2 * 1024**2):
    path = Path(path).absolute()
    assert path.resolve(strict=True) == path and path.is_file() and not path.is_symlink()
    before = path.stat()
    assert before.st_size <= maximum
    raw = path.read_bytes()
    after = path.stat()
    assert all(getattr(before, k) == getattr(after, k)
               for k in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns"))
    assert len(raw) == before.st_size
    assert expected is None or hashlib.sha256(raw).hexdigest() == expected
    return raw


def load_helper(name):
    path = HERE / name
    read(path, HELPERS[name])
    spec = importlib.util.spec_from_file_location("postsave_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("stage", "verify", "collect", "stage-actual"))
    parser.add_argument("--pending-action-sha256", required=True, help="Exact new p6-upload-review-02 pending action.")
    parser.add_argument("--approval-sha256", required=True, help="Exact new user approval for that pending action.")
    parser.add_argument("--index", type=int, default=1, help="Fresh collection index only.")
    parser.add_argument("--actual-sha256", help="Exact root-created actual completion companion, stage-actual only.")
    args = parser.parse_args(argv)
    ast.parse(REMOTE)
    assert re.fullmatch(r"[0-9a-f]{64}", args.pending_action_sha256)
    assert re.fullmatch(r"[0-9a-f]{64}", args.approval_sha256)
    pending_raw = read(REVIEW / "PENDING_ACTION.json", args.pending_action_sha256, 16384)
    approval_raw = read(REVIEW / "USER_APPROVAL.json", args.approval_sha256, 8192)
    pending, approval = json.loads(pending_raw), json.loads(approval_raw)
    driver_sha = hashlib.sha256(read(__file__)).hexdigest()
    assert type(pending) is dict and pending.get("recovery_prepared_sha256") == PREPARED_SHA
    assert pending.get("runtime_manifest_sha256") == RUNTIME_MANIFEST_SHA and pending.get("cpu_driver_sha256") == driver_sha
    assert type(approval) is dict and approval.get("status") == "approved_by_user"
    assert approval.get("pending_action_sha256") == args.pending_action_sha256
    prepared = json.loads(read(PACKAGE / "PREPARED-GPU.json", PREPARED_SHA))
    assert prepared["schema"] == "hydra-p6-saved-recovery-base3-prepared-v1"
    assert prepared["new_remote_input_total_bytes"] == 160318
    assert {r["destination"]: {k: r[k] for k in ("bytes", "sha256")}
            for r in prepared["new_remote_inputs"]} == PINS
    request = {"phase": args.phase, "pending_action_sha256": args.pending_action_sha256,
        "approval_sha256": args.approval_sha256, "driver_sha256": driver_sha,
        "pending_action_base64": base64.b64encode(pending_raw).decode(),
        "approval_base64": base64.b64encode(approval_raw).decode(),
        "environment_revision": "el8-libffi-env2", "recovery_revision": "base3-inference-runtime09",
        "predecessor_driver_sha256": PREDECESSOR_SHA}
    if args.phase == "stage":
        request["files"] = {}
        for row in prepared["new_remote_inputs"]:
            source = ROOT / row["path"]
            assert source.parent == PACKAGE
            raw = read(source, row["sha256"])
            assert len(raw) == row["bytes"]
            request["files"][row["destination"]] = {k: row[k] for k in ("bytes", "sha256")}
            request["files"][row["destination"]]["base64"] = base64.b64encode(raw).decode()
    if args.phase == "stage-actual":
        assert args.actual_sha256 and re.fullmatch(r"[0-9a-f]{64}", args.actual_sha256)
        raw = read(PACKAGE / "metadata-actual-completion-base3.json", args.actual_sha256, 65536)
        value = json.loads(raw)
        metadata = read(PACKAGE / "metadata-recovery-base3.json")
        assert value["receipt_sha256"] == hashlib.sha256(metadata).hexdigest()
        verify = json.loads(read(OUT / "verify/transport-completion.json"))
        assert verify["actual_ssh_exit_code"] == 0 and verify["remote_completed"] is True
        request.update(actual_base64=base64.b64encode(raw).decode(), actual_sha256=args.actual_sha256)
    else:
        assert args.actual_sha256 is None
    assert len(json.dumps(request).encode()) <= 256 * 1024
    assert 1 <= args.index <= 99 and (args.phase == "collect" or args.index == 1)
    directory = OUT / ("collect-" + str(args.index).zfill(3) if args.phase == "collect" else args.phase)
    assert directory.parent.resolve() == directory.parent
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (directory / "remote-script.py").write_text(REMOTE)
    transport = load_helper("p6_smoke_transport.py")
    ssh = load_helper("stage_p6_remote.py").SSH
    command = shlex.join(["/usr/bin/env", "LD_LIBRARY_PATH=" + PYTHON_LIB, PYTHON, "-I", "-B", "-c", REMOTE])
    started = time.monotonic()
    result = transport.run_ssh(ssh + [command], input=json.dumps(request).encode(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=200,
        directory=directory, phase=args.phase)
    (directory / "stdout.json").write_bytes(result.stdout)
    (directory / "stderr.txt").write_bytes(result.stderr)
    response = None
    try:
        if len(result.stdout) <= 12 * 1024**2:
            response = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        pass
    completed = bool(type(response) is dict and response.get("schema") == "hydra-postsave-cpu-phase-v2"
                     and response.get("phase") == args.phase and response.get("completed") is True
                     and response.get("error") is None)
    receipt = {"schema": "hydra-postsave-transport-completion-v1", "phase": args.phase,
        "actual_ssh_exit_code": result.returncode, "remote_completed": completed,
        "remote_outcome": "reported" if response is not None else "unknown",
        "elapsed_seconds": time.monotonic() - started, "automatic_retry": False,
        "gpu_allocations": 0, "completion_chunk_generated": False,
        "driver_sha256": hashlib.sha256(read(__file__)).hexdigest(),
        "remote_script_sha256": hashlib.sha256(REMOTE.encode()).hexdigest()}
    (directory / "transport-completion.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if args.phase == "collect" and result.returncode == 0 and completed:
        assert type(response["result"]["files"]) is dict and set(response["result"]["files"]) <= set(COLLECT_NAMES)
        total = 0
        for name, pin in response["result"]["files"].items():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            raw = base64.b64decode(pin["base64"], validate=True)
            total += len(raw)
            assert total <= 8 * 1024**2
            assert len(raw) == pin["bytes"] <= 2 * 1024**2 and hashlib.sha256(raw).hexdigest() == pin["sha256"]
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: stream.write(raw)
            if name in {"metadata-recovery-base3.json", "metadata-recovery-base3.prepared-plan.json",
                        "metadata-recovery-base3.runtime-plan.json"}:
                target = PACKAGE / name
                if target.exists(): assert read(target) == raw
                else:
                    with target.open("xb") as stream: stream.write(raw)
        print(json.dumps({"phase": args.phase, "collected_files": len(response["result"]["files"])}), flush=True)
    else:
        print(result.stdout.decode(errors="replace")[:12000], end="", flush=True)
    print(result.stderr.decode(errors="replace")[:12000], end="", flush=True)
    print(json.dumps(receipt), flush=True)
    return result.returncode if result.returncode != 0 else (0 if completed else 1)


if __name__ == "__main__":
    raise SystemExit(main())
