"""One bounded read-only inspection after the source04 SSH exit 255; never a retry."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,os,resource,signal,stat
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(5,6))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(30)
assert os.getuid()==105923 and hasattr(os,'O_PATH')
campaign=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
dest=campaign/'bundles/combined-source-04'
fds={'/':os.open('/',os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW)}
path_only=1;readable=0
try:
 for target in (dest,campaign/'bundles/combined-source-03'):
  current=Path('/')
  for part in target.parts[1:]:
   parent=current;current=current/part;key=str(current)
   if key in fds:continue
   owned=current==campaign or str(current).startswith(str(campaign)+'/')
   flags=(os.O_RDONLY if owned else os.O_PATH)|os.O_DIRECTORY|os.O_NOFOLLOW
   fd=os.open(part,flags,dir_fd=fds[str(parent)]);s=os.fstat(fd)
   assert stat.S_ISDIR(s.st_mode)
   if owned:assert s.st_uid==105923
   fds[key]=fd
   if owned:readable+=1
   else:path_only+=1
 names=os.listdir(fds[str(dest)])
 assert names==['source'], 'Source04 root no longer matches pre-mutation state.'
 fd=os.open('manifest.json',os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fds[str(campaign/'bundles/combined-source-03')])
 with os.fdopen(fd,'rb')as f:
  s=os.fstat(f.fileno());assert stat.S_ISREG(s.st_mode)and s.st_uid==105923 and s.st_size==253855
  raw=f.read(253856)
 assert hashlib.sha256(raw).hexdigest()=='bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08'
 print(json.dumps({'schema':'hydra-read-only-opath-traversal-check-v1','passed':True,'uid':os.getuid(),'path_only_ancestor_fds':path_only,'readable_owned_directory_fds':readable,'parent_manifest_exact':True,'source04_root_entries':names,'repair01_marker_absent':True,'source04_metadata_absent':True,'remote_writes':0,'allocations':0}),flush=True)
finally:
 for fd in reversed(list(fds.values())):os.close(fd)
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
