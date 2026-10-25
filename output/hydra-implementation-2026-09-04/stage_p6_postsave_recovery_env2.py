"""Diagnosed EL8-library follow-up: same verifier, fresh env2 CPU evidence.

Each invocation performs at most one SSH operation, with no scheduler calls.
The exact EL8 Python+libffi environment was observed by root in diagnosis04
(actual exit 0 / c0bbc5). No module loading or interpreter replacement occurs.
Run verify and collect separately; the five approved inputs are already staged. Only after observing verify's real exit
may root create metadata-actual-completion-env2.json and invoke stage-actual with
its exact SHA. This driver never invents that receipt or a completion chunk.
"""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import importlib.util
import json
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUT_PACKAGE = HERE / "p6-postsave-recovery-v1"
PACKAGE = HERE / "p6-postsave-recovery-v2"
OUT = HERE / "p6-postsave-metadata-env2-01"
PENDING_SHA = "b698f3877632ded40f63adc2cdc13f80931d019a05f09ad9659f7448b3f8737f"
APPROVAL_SHA = "4d67d759cce4acade20fa4d7f9f1a149fad37e51b3ade90d3eadd91d6bedb392"
PREPARED_SHA = "0ec40b3b48e606f0cf49072b4c429de906bfe1a9f9218adafd5b4697ddb96718"
HELPERS = {"p6_smoke_transport.py": "6587fb953d693abfb76223c4a1fbd9dc8ace424f13e09017237a1a1240193d55",
           "stage_p6_remote.py": "da136813840325da6c211169745a66c546dfc174a9d3a45d9475a7da96666f81"}
PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
PYTHON_LIB = '/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib:/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64'
PINS = {
    "metadata_recovery.py": {"bytes": 25101, "sha256": "1f485e4207430fb3bc9d42849053cbc7bf32eb07dda789f6c0c9e63d5c07b86e"},
    "gpu_saved_reload.py": {"bytes": 20056, "sha256": "573b4522cc94b5af2d03c17216fd34163882a25746f190f59a91bf969072ff5a"},
    "controller-source-pins.json": {"bytes": 99834, "sha256": "898f5b8a1ee68b7201a397acc9b7e353910453e261386881979c86f715b44547"},
    "observation013.json": {"bytes": 5019, "sha256": "a1d56e0e322a8b3f49d2ecd51da21309efe3ccc6cd091c3482edebef10375923"},
    "observation013-transport.json": {"bytes": 320, "sha256": "ac2b0deec46aaac68a7fc0405b6d28acab8c8157b0b45c95a0b52ac55b388269"},
}

REMOTE_TEMPLATE = r'''
import base64,hashlib,json,os,re,signal,stat,subprocess,sys,time
from pathlib import Path
PINS = json.loads(__PINS_JSON__)
PREVIOUS_FAILURE_PINS = {'metadata-recovery.json': {'bytes': 8380, 'sha256': '81573ee064690fee6223c4721e176fc05d36558e457748adf467f042d26a49cd'}, 'metadata-invocation.json': {'bytes': 1424, 'sha256': 'fc600a5c142893c82b0c89afcd62be1a11ee37d42ef517b1e167f09122846ca0'}, 'metadata-process-completion.json': {'bytes': 359, 'sha256': 'e16a3a874b95919e235a79ef562d577aa90418394efe9f655f4f79768afe567a'}, 'metadata-stdout.txt': {'bytes': 266, 'sha256': 'cd20dcecfa6e2233af2d7d851cd816f0c09dec60ebb4e07896f72f021fc532ef'}, 'metadata-stderr.txt': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}}
CAMPAIGN=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
DIRECTORY=CAMPAIGN/'recovery/p6-postsave-recovery-v1'
SOURCE=CAMPAIGN/'bundles/source-data-07/source'
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
def verify_inputs():
 require(DIRECTORY.resolve(strict=True)==DIRECTORY and DIRECTORY.is_dir(),'Wrong staged directory')
 for name,expected in PINS.items():require(pin(read(DIRECTORY/name))==expected,'Staged input hash differs: '+name)
 for name,expected in PREVIOUS_FAILURE_PINS.items():require(pin(read(DIRECTORY/name))==expected,'Previous failed output changed: '+name)
def successful_metadata():
 raw=read(DIRECTORY/'metadata-recovery-env2.json');value=json.loads(raw)
 require(value.get('schema')=='hydra-p6-postsave-metadata-recovery-v1' and value.get('passed') is True
  and value.get('eligible_for_saved_reload') is True and value.get('saved_adapter_reload_required') is True
  and value.get('model_loaded') is False and value.get('errors')==[] and value.get('sources_unchanged') is True
  and value.get('metadata_source_sha256')==PINS['metadata_recovery.py']['sha256']
  and value.get('original_slurm_state')=='FAILED' and value.get('original_slurm_exit_code')=='1:0'
  and value.get('original_process_exit_code')==1,'CPU metadata recovery did not pass')
 return raw
def cpu_run():
 verify_inputs()
 require(not (DIRECTORY/'metadata-recovery-env2.json').exists(),'CPU result already exists; no retry')
 argv=[PYTHON,'-B',str(DIRECTORY/'metadata_recovery.py'),'--source-root',str(SOURCE),
  '--job-directory',str(CAMPAIGN/'jobs/p6-training-fresh-1.7b-v2-01'),
  '--observation',str(DIRECTORY/'observation013.json'),'--transport',str(DIRECTORY/'observation013-transport.json'),
  '--output',str(DIRECTORY/'metadata-recovery-env2.json')]
 save('metadata-env2-invocation.json',{'schema':'hydra-postsave-cpu-invocation-v1','argv':argv,
  'metadata_source_sha256':PINS['metadata_recovery.py']['sha256'],'cpu_seconds':90,'wall_seconds':120,
  'address_space_bytes':2*1024**3,'automatic_retry':False,'gpu_allocations':0,
  'environment_revision':'el8-libffi-env2','python':PYTHON,'ld_library_path':LIB})
 env=dict(os.environ)
 for name in ('PYTHONPATH','PYTHONHOME'):env.pop(name,None)
 env.update(LD_LIBRARY_PATH=LIB,PYTHONHASHSEED='20260904',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
 process=None;code=None;reaped=False;reason=None;started=time.monotonic()
 with (DIRECTORY/'metadata-env2-stdout.txt').open('xb') as stdout,(DIRECTORY/'metadata-env2-stderr.txt').open('xb') as stderr:
  try:
   process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,env=env,cwd=SOURCE,start_new_session=True)
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
  'metadata_source_sha256':PINS['metadata_recovery.py']['sha256'],'automatic_retry':False,
  'gpu_allocations':0,'model_calls':0,'optimizer_updates':0,'native_proof_runs':0}
 save('metadata-env2-process-completion.json',receipt)
 require(code==0 and reaped and reason is None,'Actual CPU metadata process did not complete successfully')
 metadata=successful_metadata();verify_inputs()
 return {'process':receipt,'metadata_recovery':pin(metadata),'actual_completion_companion_created':False}
os.umask(0o077)
def expired(signum,frame):raise TimeoutError('Bounded recovery phase expired; no retry')
signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGTERM,expired);signal.alarm(180)
response={'schema':'hydra-postsave-cpu-phase-v1','completed':False,'error':None,'automatic_retry':False,'gpu_allocations':0}
try:
 require(os.getuid()==105923 and Path(sys.executable).resolve()==Path(PYTHON).resolve(),'Wrong CPU interpreter/owner')
 raw=sys.stdin.buffer.read(256*1024+1);require(len(raw)<=256*1024,'Input bound')
 request=json.loads(raw);phase=request['phase'];response['phase']=phase
 require(phase in ('verify','collect','stage-actual'),'Unknown phase')
 require(request['pending_action_sha256']=='b698f3877632ded40f63adc2cdc13f80931d019a05f09ad9659f7448b3f8737f'
  and request['approval_sha256']=='4d67d759cce4acade20fa4d7f9f1a149fad37e51b3ade90d3eadd91d6bedb392','Specific approval differs')
 if phase=='verify':response['result']=cpu_run()
 elif phase=='collect':
  verify_inputs();files={};total=0
  names=['metadata-recovery-env2.json','metadata-recovery-env2.prepared-plan.json','metadata-env2-invocation.json',
   'metadata-env2-process-completion.json','metadata-env2-stdout.txt','metadata-env2-stderr.txt']
  names+=['metadata-recovery-env2.admission-failure/'+n for n in ('expected-manifest.json','regenerated-manifest.json','diff.json')]
  for name in names:
   path=DIRECTORY/name
   if not path.exists():continue
   raw=read(path);total+=len(raw);require(total<=8*1024**2,'Collection total bound')
   files[name]={**pin(raw),'base64':base64.b64encode(raw).decode()}
  response['result']={'files':files,'bytes':total,'read_only':True,'collection_is_not_cpu_success':True}
 else:
  verify_inputs();metadata=successful_metadata()
  process=json.loads(read(DIRECTORY/'metadata-env2-process-completion.json'))
  require(process.get('actual_metadata_process_exit_code')==0 and process.get('owned_child_reaped') is True
   and process.get('stop_reason') is None,'No actual successful owned CPU process receipt')
  raw=base64.b64decode(request['actual_base64'],validate=True);require(len(raw)<=65536 and pin(raw)['sha256']==request['actual_sha256'],'Actual companion hash/bound')
  value=json.loads(raw)
  require(set(value)=={'schema','actual_exit_code','completion_chunk','receipt_sha256','verifier_sha256'}
   and value['schema']=='hydra-p6-postsave-metadata-actual-completion-v1'
   and type(value['actual_exit_code']) is int and value['actual_exit_code']==0
   and value['receipt_sha256']==pin(metadata)['sha256'] and value['verifier_sha256']==PINS['metadata_recovery.py']['sha256']
   and isinstance(value['completion_chunk'],str) and re.fullmatch('[0-9a-f]{6,64}',value['completion_chunk']),
   'Root must supply its separately observed real completion companion')
  with (DIRECTORY/'metadata-actual-completion-env2.json').open('xb') as stream:stream.write(raw)
  (DIRECTORY/'metadata-actual-completion-env2.json').chmod(0o444)
  require(read(DIRECTORY/'metadata-actual-completion-env2.json')==raw,'Actual companion changed on transfer')
  response['result']={'actual_companion':pin(raw),'created_by_root_not_this_driver':True}
 response['completed']=True
except BaseException as failure:response['error']={'type':type(failure).__name__,'detail':str(failure)[:1600]}
finally:signal.alarm(0)
raw=canonical(response)+b'\n';require(len(raw)<=12*1024**2,'Response bound')
sys.stdout.buffer.write(raw);sys.stdout.buffer.flush()
raise SystemExit(0 if response['completed'] else 1)
'''
REMOTE = REMOTE_TEMPLATE.replace("__PINS_JSON__", repr(json.dumps(PINS, sort_keys=True)))


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
    parser.add_argument("phase", choices=("verify", "collect", "stage-actual"))
    parser.add_argument("--index", type=int, default=1, help="Fresh collection index only.")
    parser.add_argument("--actual-sha256", help="Exact root-created actual completion companion, stage-actual only.")
    args = parser.parse_args(argv)
    ast.parse(REMOTE)
    read(HERE / "p6-upload-review-01/PENDING_ACTION.json", PENDING_SHA)
    approval = json.loads(read(HERE / "p6-upload-review-01/USER_APPROVAL.json", APPROVAL_SHA))
    assert approval["status"] == "approved_by_user" and approval["pending_action_sha256"] == PENDING_SHA
    prepared = json.loads(read(INPUT_PACKAGE / "PREPARED-GPU.json", PREPARED_SHA))
    assert prepared["minimum_initial_staged_payload_bytes"] == 150330
    assert {r["destination"]: {k: r[k] for k in ("bytes", "sha256")}
            for r in prepared["minimum_initial_staged_payload"]} == PINS
    request = {"phase": args.phase, "pending_action_sha256": PENDING_SHA, "approval_sha256": APPROVAL_SHA,
        "environment_revision": "el8-libffi-env2", "predecessor_driver_sha256": "89c039351980badbbcd2bdd7b57509313a604e5fb7b738d608cf62973fe592c1"}
    if args.phase == "stage-actual":
        assert args.actual_sha256 and len(args.actual_sha256) == 64
        raw = read(PACKAGE / "metadata-actual-completion-env2.json", args.actual_sha256, 65536)
        value = json.loads(raw)
        metadata = read(PACKAGE / "metadata-recovery-env2.json")
        assert value["receipt_sha256"] == hashlib.sha256(metadata).hexdigest()
        verify = json.loads(read(OUT / "verify/transport-completion.json"))
        assert verify["actual_ssh_exit_code"] == 0 and verify["remote_completed"] is True
        request.update(actual_base64=base64.b64encode(raw).decode(), actual_sha256=args.actual_sha256)
    else:
        assert args.actual_sha256 is None
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
    completed = bool(type(response) is dict and response.get("schema") == "hydra-postsave-cpu-phase-v1"
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
        for name, pin in response["result"]["files"].items():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            raw = base64.b64decode(pin["base64"], validate=True)
            assert len(raw) == pin["bytes"] <= 2 * 1024**2 and hashlib.sha256(raw).hexdigest() == pin["sha256"]
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: stream.write(raw)
            if name in {"metadata-recovery-env2.json", "metadata-recovery-env2.prepared-plan.json"}:
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
