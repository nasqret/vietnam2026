"""One bounded read-only inspection after the source04 SSH exit 255; never a retry."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,os,resource,signal,stat,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(5,6))
resource.setrlimit(resource.RLIMIT_AS,(128*1024**2,128*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(30)
assert os.getuid()==105923
base=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles')
print(json.dumps({'phase':'authenticated','uid':os.getuid(),'read_only':True}),flush=True)
def inspect(path,contents=False):
 out={'path':str(path)}
 try:s=path.lstat()
 except FileNotFoundError:
  out['exists']=False;return out
 out.update(exists=True,mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid,nlink=s.st_nlink,bytes=s.st_size,mtime_ns=s.st_mtime_ns,regular=stat.S_ISREG(s.st_mode),directory=stat.S_ISDIR(s.st_mode),symlink=stat.S_ISLNK(s.st_mode))
 if contents:
  assert stat.S_ISREG(s.st_mode) and s.st_uid==105923 and s.st_size<=1024*1024
  fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
  with os.fdopen(fd,'rb')as f:
   opened=os.fstat(f.fileno());assert (opened.st_dev,opened.st_ino,opened.st_size)==(s.st_dev,s.st_ino,s.st_size)
   raw=f.read(1024*1024+1)
   after=os.fstat(f.fileno())
  assert len(raw)==s.st_size and after.st_mtime_ns==s.st_mtime_ns and after.st_size==s.st_size
  out.update(sha256=hashlib.sha256(raw).hexdigest())
  if path.name=='transfer-receipt.json':out['receipt']=json.loads(raw)
 return out
for relative,contents in [('combined-source-03/manifest.json',True),('combined-source-04',False),('combined-source-04/source',False),('combined-source-04/manifest.json',True),('combined-source-04/paired-source-pins.json',True),('combined-source-04/transfer-receipt.json',True)]:
 path=base/relative
 assert not base.is_symlink()
 for p in list(path.parents)[:len(Path(relative).parts)-1]:assert not p.is_symlink()
 print(json.dumps(inspect(path,contents),sort_keys=True),flush=True)
print(json.dumps({'phase':'inspection_complete','remote_writes':0,'allocations':0}),flush=True)
signal.alarm(0)
'''
SSH = ['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15',
       '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2',
       '-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
       '-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no',
       '-o','ControlMaster=no','-o','ControlPath=none',
       '--','plgnasqret@helios.cyfronet.pl']
intent=HERE/'intent.json'
with intent.open('x') as f:
    json.dump({'schema':'hydra-read-only-source-reconciliation-intent-v1',
               'remote_code_sha256':hashlib.sha256(REMOTE.encode()).hexdigest(),
               'remote_writes':0,'allocations':0,'automatic_retry':False,
               'purpose':'Inspect uncertain source04 stage; do not rerun transfer'},f,indent=2)
(HERE/'remote-read-only.py').write_text(REMOTE)
began=time.monotonic()
timed_out=False
try:
    result=subprocess.run(SSH+['/usr/bin/python3 -I -B -c '+shlex.quote(REMOTE)],
                          stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
    code=result.returncode;out=result.stdout;err=result.stderr
except subprocess.TimeoutExpired as e:
    code=124;out=e.stdout or b'';err=e.stderr or b'';timed_out=True
(HERE/'stdout.jsonl').write_bytes(out)
(HERE/'stderr.txt').write_bytes(err)
record={'schema':'hydra-read-only-source-reconciliation-completion-v1','ssh_exit_code':code,
        'outer_timeout':timed_out,'elapsed_seconds':time.monotonic()-began,
        'remote_writes':0,'allocations':0,'automatic_retry':False,
        'stdout_bytes':len(out),'stderr_bytes':len(err)}
(HERE/'completion.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
print(out.decode('utf-8','replace')[:65536],end='',flush=True)
print(err.decode('utf-8','replace')[:4096],end='',flush=True)
raise SystemExit(code)
