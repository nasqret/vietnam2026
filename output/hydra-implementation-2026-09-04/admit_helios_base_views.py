"""Create clean, explicit HF-style snapshot views and fully authenticate on CPU.

Downloaded files and their receipt remain unchanged. Only exact registry files
are linked into fresh owned snapshot directories; no authenticator is relaxed.
"""
from pathlib import Path
import json
import shlex
import subprocess
import time

from stage_p6_remote import SSH

HERE = Path(__file__).resolve().parent
OUT = HERE / "p6-clean-base-admission-01"
PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
SOURCE = CAMPAIGN + "/bundles/source-data-03/source"
REMOTE = r'''
import hashlib,json,os,resource,signal,sys,time
from pathlib import Path
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU,(180,180))
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
signal.alarm(240)
started=time.monotonic()
project,campaign,source=map(Path,(PROJECT,CAMPAIGN,SOURCE))
output=campaign/'jobs/p6-clean-base-admission-01'
output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(source/'hydra-playground'))
import experimental_model as provider
assert hashlib.sha256(Path(provider.__file__).read_bytes()).hexdigest()=='b5b85ed8bba6b0e6cdda4c7772443c5fec630a5643deba7d53598bcdd0cf9598'
origins={
 'qwen3-1.7b-base':project/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1',
 'qwen3-4b-base':campaign/'base-models/qwen3-4b-base',
 'qwen3-8b-base':campaign/'base-models/qwen3-8b-base'}
root=campaign/'authenticated-bases-01';root.mkdir(exist_ok=False)
record={'schema':'hydra-clean-base-admission-v1','source':str(source),'completed':False,
 'gpu_allocations':0,'model_calls':0,'downloaded_files_modified':False,'automatic_retry':False,'models':{}}
try:
 for key,origin in origins.items():
  begin=time.monotonic();spec=provider.model_spec(key)
  expected={**spec['metadata_files'],**spec['weight_files']}
  names={path.name for path in origin.iterdir()}
  assert set(expected)<=names
  extras=names-set(expected)
  assert extras<={'download-receipt.json','README.md','.gitattributes','LICENSE','LICENSE.txt'},extras
  view=root/key;view.mkdir(exist_ok=False)
  for name in sorted(expected):
   assert '/' not in name and name not in ('.','..')
   target=(origin/name).resolve(strict=True)
   assert target.is_file()
   (view/name).symlink_to(target)
  identity=provider.authenticate_base(key,view,should_stop=lambda:time.monotonic()-started>=230)
  entry={'origin':str(origin),'view':str(view),'excluded_metadata_names':sorted(extras),
   'elapsed_seconds':time.monotonic()-begin,'identity':identity}
  record['models'][key]=entry
  (output/(key+'.json')).write_text(json.dumps(entry,indent=2)+'\n')
  print(json.dumps({'model_key':key,'view':str(view),'base_identity_sha256':identity['base_identity_sha256'],
   'elapsed_seconds':entry['elapsed_seconds'],'all_weight_bytes_hashed':True}),flush=True)
 record['completed']=True
except BaseException as error:
 record['error']={'type':type(error).__name__,'detail':str(error)[:800]}
 raise
finally:
 record.update(elapsed_seconds=time.monotonic()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
 (output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(record),flush=True)
'''


def main():
    OUT.mkdir(exist_ok=False)
    source = "PROJECT="+repr(PROJECT)+"\nCAMPAIGN="+repr(CAMPAIGN)+"\nSOURCE="+repr(SOURCE)+"\n"+REMOTE
    (OUT / "remote-script.py").write_text(source)
    base = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0"
    command = ["env", "PYTHONHASHSEED=20260904", "PYTHONDONTWRITEBYTECODE=1", "LD_LIBRARY_PATH="+base+"/lib",
               base+"/bin/python3", "-B", "-P", "-c", source]
    began = time.monotonic()
    result = subprocess.run(SSH+[" ".join(shlex.quote(x) for x in command)],
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=260)
    (OUT / "stdout.jsonl").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code":result.returncode,"elapsed_seconds":time.monotonic()-began,
               "gpu_allocations":0,"model_calls":0,"automatic_retry":False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt,indent=2)+"\n")
    if result.stdout:
        lines = result.stdout.splitlines()
        for line in lines[:-1]:
            print(line.decode())
        record = json.loads(lines[-1])
        print(json.dumps({key:record.get(key) for key in ('completed','error','elapsed_seconds','peak_rss_bytes')}))
    print(result.stderr.decode(),end="")
    print(json.dumps(receipt),flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
