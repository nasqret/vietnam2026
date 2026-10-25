"""One exact public Base download into a new owned Helios directory; no GPU."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "helios-8b-download-01"
REGISTRY = ROOT / "hydra-playground/experimental-models/qwen3-base-v1.json"
REGISTRY_SHA = "3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1"
REMOTE = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/base-models/qwen3-8b-base"
SCRIPT = r'''
import hashlib,json,os,re,shutil,signal,sys,time,urllib.request
from pathlib import Path
os.umask(0o077)
signal.alarm(1250)
started=time.monotonic()
spec=CONFIG['spec']
assert spec['model_id']=='Qwen/Qwen3-8B-Base'
assert spec['revision']=='49e3418fbbbca6ecbdf9608b4d22e5a407081db4'
directory=Path(CONFIG['directory'])
expected=dict(spec['metadata_files']);expected.update(spec['weight_files'])
assert 1<=len(expected)<=16
total=sum(row['bytes'] for row in expected.values())
assert total<17*1024**3
project=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training')
assert shutil.disk_usage(str(project)).free>total+1024**3
directory.mkdir(parents=True,exist_ok=False)
record={'schema':'hydra-base-download-v1','status':'running','registry_sha256':CONFIG['registry_sha256'],
 'model_id':spec['model_id'],'revision':spec['revision'],'directory':str(directory),
 'expected_bytes':total,'max_wall_seconds':1200,'automatic_retry':False,'resumption':False,
 'gpu_allocations':0,'files':{}}
def save():
 (directory/'download-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
def event(value):
 print(json.dumps(value),flush=True)
save()
try:
 for name,descriptor in sorted(expected.items()):
  assert re.fullmatch(r'[A-Za-z0-9_.-]+',name) and name not in ('.','..')
  assert 0<descriptor['bytes']<5*1024**3
  assert re.fullmatch(r'[0-9a-f]{64}',descriptor['sha256'])
  if time.monotonic()-started>=1200:raise TimeoutError('Download wall ceiling reached')
  url='https://huggingface.co/'+spec['model_id']+'/resolve/'+spec['revision']+'/'+name+'?download=true'
  partial=directory/(name+'.partial')
  digest=hashlib.sha256();observed=0;notice=256*1024**2
  event({'file':name,'status':'starting','expected_bytes':descriptor['bytes']})
  with urllib.request.urlopen(url,timeout=30) as response, partial.open('xb') as destination:
   assert response.status==200
   while True:
    if time.monotonic()-started>=1200:raise TimeoutError('Download wall ceiling reached')
    block=response.read(1024**2)
    if not block:break
    observed+=len(block)
    if observed>descriptor['bytes']:raise ValueError('Response exceeds exact pinned size')
    digest.update(block);destination.write(block)
    if observed>=notice:
     event({'file':name,'status':'downloading','bytes':observed})
     notice+=256*1024**2
   destination.flush();os.fsync(destination.fileno())
  actual={'bytes':observed,'sha256':digest.hexdigest()}
  assert actual==descriptor,'Base file hash/size mismatch: '+name
  partial.rename(directory/name)
  record['files'][name]=actual;save()
  event({'file':name,'status':'verified','bytes':observed})
 record['status']='complete'
except BaseException as error:
 record.update(status='failed',error=type(error).__name__+': '+str(error)[:500])
 raise
finally:
 record['elapsed_seconds']=time.monotonic()-started
 save();event(record)
'''


def main():
    raw=REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=REGISTRY_SHA:
        raise ValueError("Frozen model registry changed before staging")
    spec=json.loads(raw)["models"]["qwen3-8b-base"]
    OUT.mkdir(exist_ok=False)
    config={"spec":spec,"directory":REMOTE,"registry_sha256":REGISTRY_SHA}
    (OUT/"request.json").write_text(json.dumps({**config,"authority":"HYDRA_EXPERIMENT_AUTHORITY.md",
        "cpu_login_download_only":True,"gpu_allocations":0,"max_wall_seconds":1200,
        "no_retry_or_resume":True},indent=2)+"\n")
    source="CONFIG = "+repr(config)+"\n"+SCRIPT
    (OUT/"remote-script.py").write_text(source)
    command=["/usr/bin/ssh","-T","-o","BatchMode=yes","-o","ConnectTimeout=15",
        "-o","ServerAliveInterval=10","-o","ServerAliveCountMax=2","-o","ForwardAgent=no",
        "-o","ClearAllForwardings=yes","-o","StrictHostKeyChecking=yes","-o","UpdateHostKeys=no",
        "-o","ControlMaster=no","-o","ControlPath=none","--","plgnasqret@helios.cyfronet.pl","python3 -u -"]
    started=time.monotonic()
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                             text=True)
    process.stdin.write(source);process.stdin.close()
    with (OUT/"transport-output.txt").open("x") as log:
        for line in process.stdout:
            log.write(line);log.flush();print(line,end="",flush=True)
    actual=process.wait(timeout=5)
    receipt={"actual_ssh_exit_code":actual,"elapsed_seconds":time.monotonic()-started,
        "remote_directory":REMOTE,"gpu_allocations":0,"automatic_retry":False,
        "script_sha256":hashlib.sha256(source.encode()).hexdigest()}
    (OUT/"actual-completion.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return actual


if __name__=="__main__":
    raise SystemExit(main())
