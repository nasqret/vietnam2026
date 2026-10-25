"""One bounded read-only inspection after the source04 SSH exit 255; never a retry."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
REMOTE = r'''
import json,os,resource,signal,stat,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(5,6))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(30)
assert os.getuid()==105923
root=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-04/source')
assert root.is_dir() and not root.is_symlink()
stack=[root];files=[];directories=[];began=time.monotonic()
while stack:
 directory=stack.pop()
 with os.scandir(str(directory))as entries:
  for entry in entries:
   path=Path(entry.path);s=entry.stat(follow_symlinks=False)
   assert s.st_uid==105923 and not stat.S_ISLNK(s.st_mode)
   relative=str(path.relative_to(root))
   if stat.S_ISDIR(s.st_mode):
    directories.append(relative);stack.append(path)
    assert len(directories)<=500
   else:
    assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
    files.append({'path':relative,'bytes':s.st_size,'mode':oct(stat.S_IMODE(s.st_mode)),'mtime_ns':s.st_mtime_ns})
    assert len(files)<=1500
files.sort(key=lambda v:v['path'])
print(json.dumps({'schema':'hydra-read-only-partial-source-inventory-v1','root':str(root),'read_only':True,'file_count':len(files),'directory_count':len(directories),'total_bytes':sum(v['bytes']for v in files),'elapsed_seconds':time.monotonic()-began,'files':files,'directories':sorted(directories),'remote_writes':0,'allocations':0}),flush=True)
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

if code==0:
    value=json.loads(out)
    print(json.dumps({k:v for k,v in value.items() if k not in ('files','directories')}),flush=True)
    print(json.dumps({'first_file':value['files'][0] if value['files'] else None,'last_file':value['files'][-1] if value['files'] else None}),flush=True)
print(err.decode('utf-8','replace')[:4096],end='',flush=True)
raise SystemExit(code)
