
import base64,hashlib,json,os,resource,signal,sys,time
from pathlib import Path
os.umask(0o077);signal.alarm(120)
resource.setrlimit(resource.RLIMIT_CPU,(90,90))
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
started=time.monotonic();request=json.loads(sys.stdin.buffer.read(10*1024**2))
campaign=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
output=campaign/'jobs/p7-clean-base-admission-01';output.mkdir(exist_ok=False)
app=campaign/'bundles/source-data-05/source/hydra-playground'
origin=campaign/'base-models/deepseek-prover-v2-7b-teacher'
view=campaign/'authenticated-bases-01/deepseek-prover-v2-7b-teacher';view.mkdir(exist_ok=False)
code=output/'code';code.mkdir()
allowed={'experimental_teacher.py','experimental-models/deepseek-teacher-v1.json',
         'model.safetensors.index.json','tokenizer.json','tokenizer_config.json'}
assert set(request['files'])==allowed
for name,entry in request['files'].items():
 raw=base64.b64decode(entry['base64'],validate=True)
 assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
 target=(code if name.startswith('experimental') else view)/name
 target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb')as stream:stream.write(raw)
 target.chmod(0o444)
assert hashlib.sha256((code/'experimental_teacher.py').read_bytes()).hexdigest()=='944524ec52ac0166dffa10bda13143357f6c6daad5d7354b820a422158ac45e2'
assert hashlib.sha256((code/'experimental-models/deepseek-teacher-v1.json').read_bytes()).hexdigest()=='a56dad7ac6368964c039c9ddabab5ac6174939f9684ae23bf6872080cf38c105'
spec=json.loads((code/'experimental-models/deepseek-teacher-v1.json').read_bytes())
expected={**spec['metadata_files'],**spec['weight_files']}
for name in sorted(expected):
 if name in request['files']:continue
 target=(origin/name).resolve(strict=True);assert target.is_file()
 (view/name).symlink_to(target)
sys.path.insert(0,str(code))
import experimental_teacher
identity=experimental_teacher.authenticate_teacher(view,app_root=app,should_stop=lambda:time.monotonic()-started>=110)
assert not any(k=='torch' or k.startswith('torch.') or k=='transformers' for k in sys.modules)
record={'schema':'hydra-teacher-clean-base-admission-v1','completed':True,'view':str(view),
 'original_download_unchanged':True,'metadata_origin':'previously pinned local official metadata',
 'identity':identity,'elapsed_seconds':time.monotonic()-started,
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
 'gpu_allocations':0,'model_calls':0,'automatic_retry':False}
(output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
