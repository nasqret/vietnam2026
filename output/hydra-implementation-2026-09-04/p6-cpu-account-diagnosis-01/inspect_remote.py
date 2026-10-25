"""One bounded read-only inspection after the source04 SSH exit 255; never a retry."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
REMOTE = r'''
import json,os,resource,signal,subprocess,time
resource.setrlimit(resource.RLIMIT_CPU,(5,6))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(30)
assert os.getuid()==105923
commands=[['squeue','--array','-h','-u','105923','-o','%i|%T|%j|%b'],['sacct','-X','-j','21911728','--noheader','--parsable2','--format=JobID,User,Account,Partition,State,ExitCode,AllocTRES'],['sacctmgr','-nP','show','associations','where','user=plgnasqret','format=Cluster,Account,Partition'],['sinfo','-h','-o','%P|%a|%l|%D']]
for command in commands:
 began=time.monotonic()
 try:
  result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=5)
  assert len(result.stdout)<=65536
  record={'command':command,'actual_exit_code':result.returncode,'elapsed_seconds':time.monotonic()-began,'output':result.stdout.decode('utf-8','replace'),'read_only':True}
 except subprocess.TimeoutExpired as e:
  record={'command':command,'timeout':True,'elapsed_seconds':time.monotonic()-began,'output':(e.stdout or b'')[:65536].decode('utf-8','replace'),'read_only':True}
 print(json.dumps(record),flush=True)
print(json.dumps({'completed':True,'allocations':0,'mutating_commands':0}),flush=True)
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
