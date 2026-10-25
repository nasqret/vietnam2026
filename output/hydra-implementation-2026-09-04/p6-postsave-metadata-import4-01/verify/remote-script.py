
import base64,hashlib,json,os,re,signal,stat,subprocess,sys,time
from pathlib import Path
PINS = json.loads('{"gpu_saved_reload_import4.py": {"bytes": 26778, "sha256": "b50a2f9c54e977d13dd1f1830cb414701631bd5f46317fe1c8346ce5c49e43e6"}, "metadata_recovery_import4.py": {"bytes": 34348, "sha256": "aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16"}}')
OLD_INPUT_PINS = json.loads('{"controller-source-pins.json": {"bytes": 99834, "sha256": "898f5b8a1ee68b7201a397acc9b7e353910453e261386881979c86f715b44547"}, "gpu_saved_reload.py": {"bytes": 20056, "sha256": "573b4522cc94b5af2d03c17216fd34163882a25746f190f59a91bf969072ff5a"}, "gpu_saved_reload_base3.py": {"bytes": 26760, "sha256": "7cea491f147d7feebc6478cd0589965df9c4ac106e0bbf03e3c15243c3064639"}, "metadata_recovery.py": {"bytes": 25101, "sha256": "1f485e4207430fb3bc9d42849053cbc7bf32eb07dda789f6c0c9e63d5c07b86e"}, "metadata_recovery_base3.py": {"bytes": 33724, "sha256": "3f11a9e6ef501cc4834662f01a4dd7a388892f71cae1bc70ad4a272524c5d2be"}, "observation013-transport.json": {"bytes": 320, "sha256": "ac2b0deec46aaac68a7fc0405b6d28acab8c8157b0b45c95a0b52ac55b388269"}, "observation013.json": {"bytes": 5019, "sha256": "a1d56e0e322a8b3f49d2ecd51da21309efe3ccc6cd091c3482edebef10375923"}, "runtime-source-pins-base3.json": {"bytes": 99834, "sha256": "d981ef26de980dc983b3f0efd0885d46aaf2a08767e34b924e83632928f8cb5f"}}')
PREVIOUS_FAILURE_PINS = json.loads('{"metadata-base3-invocation.json": {"bytes": 1914, "sha256": "50dbb1d05aa53d984bdbec292a13882a5cae8b54bf85e0512d597c0374400c27"}, "metadata-base3-process-completion.json": {"bytes": 359, "sha256": "1639feb4eb42938667a003b07521cafba09c9c7e09f453c39823a5741ff82c8b"}, "metadata-base3-stderr.txt": {"bytes": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, "metadata-base3-stdout.txt": {"bytes": 272, "sha256": "96d8a93da82747a49d525e9d1399693ace309167cc7a5888f466d24e86568eba"}, "metadata-env2-invocation.json": {"bytes": 1684, "sha256": "add8b4891133cc19d0c1bbd34cc2a5784254324e45c66e8de2066b9b5258af60"}, "metadata-env2-process-completion.json": {"bytes": 359, "sha256": "a8a623d3f80443682c9408e5f0e63221975cf6992cf69a378430bb181cce7851"}, "metadata-env2-stderr.txt": {"bytes": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, "metadata-env2-stdout.txt": {"bytes": 262, "sha256": "925b5b1847ea97dac8900ffc7a3b82584af3540c2eef538f6f6ee211e8efd36d"}, "metadata-invocation.json": {"bytes": 1424, "sha256": "fc600a5c142893c82b0c89afcd62be1a11ee37d42ef517b1e167f09122846ca0"}, "metadata-process-completion.json": {"bytes": 359, "sha256": "e16a3a874b95919e235a79ef562d577aa90418394efe9f655f4f79768afe567a"}, "metadata-recovery-base3.json": {"bytes": 10324, "sha256": "f5005f9f660e58bb4d2847a57b63371ec4f0dea9786c9eddff447b94851bdae7"}, "metadata-recovery-env2.json": {"bytes": 8376, "sha256": "9cf80bbb214e410de16e3579e8aaa7a6408a7618c6ad190bc6252fc878b61c7d"}, "metadata-recovery.json": {"bytes": 8380, "sha256": "81573ee064690fee6223c4721e176fc05d36558e457748adf467f042d26a49cd"}, "metadata-stderr.txt": {"bytes": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, "metadata-stdout.txt": {"bytes": 266, "sha256": "cd20dcecfa6e2233af2d7d851cd816f0c09dec60ebb4e07896f72f021fc532ef"}}')
COLLECT_NAMES = json.loads('["metadata-recovery-import4.json", "metadata-recovery-import4.prepared-plan.json", "metadata-recovery-import4.runtime-plan.json", "metadata-import4-invocation.json", "metadata-import4-process-completion.json", "metadata-import4-stdout.txt", "metadata-import4-stderr.txt", "metadata-recovery-import4.admission-failure/expected-manifest.json", "metadata-recovery-import4.admission-failure/regenerated-manifest.json", "metadata-recovery-import4.admission-failure/diff.json"]')
PREPARED_SHA = 'f822805dea7e3c3f21828f15bfacb8ee54380348b723ea019582f16fed1eedc4'
RUNTIME_MANIFEST_SHA = 'baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff'
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
 for key in ('continuation_sha256','driver_sha256'):
  require(type(request.get(key)) is str and re.fullmatch('[0-9a-f]{64}',request[key]),'Missing exact continuation identity')
 continuation_raw=base64.b64decode(request['continuation_base64'],validate=True)
 authority_raw=base64.b64decode(request['standing_authority_base64'],validate=True)
 approval_raw=base64.b64decode(request['prior_approval_base64'],validate=True)
 require(len(continuation_raw)<=16384 and len(authority_raw)<=8192 and len(approval_raw)<=8192,'Authority record bound')
 require(pin(continuation_raw)['sha256']==request['continuation_sha256'],'Continuation bytes differ')
 require(pin(authority_raw)['sha256']=='90104131a70120cb8c735dd8b2390986111bf90283441f5b8e1c025b105e5f62','Standing authority differs')
 require(pin(approval_raw)['sha256']=='08f5191195e577a466664d5f1c5825768bdc7d166d6a40e96cdb218514307d0e','Prior approval evidence differs')
 continuation=json.loads(continuation_raw);approval=json.loads(approval_raw)
 require(type(continuation) is dict and continuation.get('schema')=='hydra-p6-postsave-import4-continuation-v1'
  and continuation.get('recovery_prepared_sha256')==PREPARED_SHA
  and continuation.get('runtime_manifest_sha256')==RUNTIME_MANIFEST_SHA
  and continuation.get('cpu_driver_sha256')==request['driver_sha256']
  and continuation.get('new_user_approval_claimed') is False
  and continuation.get('automatic_retry') is False,'Continuation does not bind this exact separately revised follow-up')
 require(continuation.get('new_remote_input_pins')==PINS and continuation.get('previous_failed_output_pins')==PREVIOUS_FAILURE_PINS,
  'Continuation input or preserved failure pins differ')
 require(type(approval) is dict and approval.get('status')=='approved_by_user'
  and approval.get('pending_action_sha256')=='716d01952c5af9cdbe7b35754f9c4d5df3f727ff4d2609bc19936496781857ed',
  'Previously approved source09 workflow provenance differs')
def stage_inputs(request):
 verify_previous_inputs()
 require(type(request.get('files')) is dict and set(request['files'])==set(PINS),'Only the two new import4 files may be staged')
 decoded={};total=0
 for name,expected in PINS.items():
  require(not (DIRECTORY/name).exists() and not (DIRECTORY/name).is_symlink(),'A new Import4 input already exists; no overwrite/retry')
  item=request['files'][name]
  require(type(item) is dict and set(item)=={'bytes','sha256','base64'} and {k:item[k] for k in ('bytes','sha256')}==expected,
   'New file descriptor differs: '+name)
  raw=base64.b64decode(item['base64'],validate=True);total+=len(raw)
  require(pin(raw)==expected and total<=61126,'New file bytes differ: '+name)
  decoded[name]=raw
 require(total==61126,'New payload total differs')
 for name,raw in decoded.items():
  with (DIRECTORY/name).open('xb') as stream:stream.write(raw)
  (DIRECTORY/name).chmod(0o444)
 verify_inputs()
 return {'files':PINS,'bytes':total,'original_inputs_unchanged':True,'all_three_failed_cpu_attempts_unchanged':True,
  'cpu_process_started':False,'model_loaded':False}
def successful_metadata():
 raw=read(DIRECTORY/'metadata-recovery-import4.json');value=json.loads(raw)
 expected={'schema':'hydra-p6-postsave-metadata-recovery-v2','passed':True,'eligible_for_saved_reload':True,
  'saved_adapter_reload_required':True,'model_loaded':False,'errors':[],'sources_unchanged':True,
  'metadata_source_sha256':PINS['metadata_recovery_import4.py']['sha256'],
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
 require(not (DIRECTORY/'metadata-recovery-import4.json').exists(),'CPU result already exists; no retry')
 require(RUNTIME_SOURCE.resolve(strict=True)==RUNTIME_SOURCE and RUNTIME_SOURCE.is_dir(),'New ordinary inference runtime is not staged')
 runtime_manifest=read(RUNTIME_SOURCE.parent/'manifest.json')
 require(pin(runtime_manifest)['sha256']==RUNTIME_MANIFEST_SHA,'New inference runtime manifest differs')
 runtime=json.loads(runtime_manifest)
 require(runtime.get('inference_only') is True and runtime.get('training_execution_allowed') is False,'Runtime is not inference-only')
 argv=[PYTHON,'-B',str(DIRECTORY/'metadata_recovery_import4.py'),'--source-root',str(SOURCE),
  '--runtime-source-root',str(RUNTIME_SOURCE),
  '--job-directory',str(CAMPAIGN/'jobs/p6-training-fresh-1.7b-v2-01'),
  '--observation',str(DIRECTORY/'observation013.json'),'--transport',str(DIRECTORY/'observation013-transport.json'),
  '--output',str(DIRECTORY/'metadata-recovery-import4.json')]
 save('metadata-import4-invocation.json',{'schema':'hydra-postsave-cpu-invocation-v1','argv':argv,
  'metadata_source_sha256':PINS['metadata_recovery_import4.py']['sha256'],'cpu_seconds':90,'wall_seconds':120,
  'address_space_bytes':2*1024**3,'automatic_retry':False,'gpu_allocations':0,
  'environment_revision':'el8-libffi-env2','recovery_revision':'import4-inference-runtime09','python':PYTHON,'ld_library_path':LIB})
 env=dict(os.environ)
 for name in ('PYTHONPATH','PYTHONHOME'):env.pop(name,None)
 env.update(LD_LIBRARY_PATH=LIB,PYTHONHASHSEED='20260904',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
 process=None;code=None;reaped=False;reason=None;started=time.monotonic()
 with (DIRECTORY/'metadata-import4-stdout.txt').open('xb') as stdout,(DIRECTORY/'metadata-import4-stderr.txt').open('xb') as stderr:
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
  'metadata_source_sha256':PINS['metadata_recovery_import4.py']['sha256'],'automatic_retry':False,
  'gpu_allocations':0,'model_calls':0,'optimizer_updates':0,'native_proof_runs':0}
 save('metadata-import4-process-completion.json',receipt)
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
  process=json.loads(read(DIRECTORY/'metadata-import4-process-completion.json'))
  require(process.get('actual_metadata_process_exit_code')==0 and process.get('owned_child_reaped') is True
   and process.get('stop_reason') is None,'No actual successful owned CPU process receipt')
  raw=base64.b64decode(request['actual_base64'],validate=True);require(len(raw)<=65536 and pin(raw)['sha256']==request['actual_sha256'],'Actual companion hash/bound')
  value=json.loads(raw)
  require(set(value)=={'schema','actual_exit_code','completion_chunk','receipt_sha256','verifier_sha256'}
   and value['schema']=='hydra-p6-postsave-metadata-actual-completion-v1'
   and type(value['actual_exit_code']) is int and value['actual_exit_code']==0
   and value['receipt_sha256']==pin(metadata)['sha256'] and value['verifier_sha256']==PINS['metadata_recovery_import4.py']['sha256']
   and isinstance(value['completion_chunk'],str) and re.fullmatch('[0-9a-f]{6,64}',value['completion_chunk']),
   'Root must supply its separately observed real completion companion')
  with (DIRECTORY/'metadata-actual-completion-import4.json').open('xb') as stream:stream.write(raw)
  (DIRECTORY/'metadata-actual-completion-import4.json').chmod(0o444)
  require(read(DIRECTORY/'metadata-actual-completion-import4.json')==raw,'Actual companion changed on transfer')
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
