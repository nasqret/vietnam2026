
import base64,hashlib,json,os,signal,subprocess,sys
from pathlib import Path
def phase_timeout(signum,frame):raise TimeoutError('Read-only collection exceeded 70 seconds; no automatic retry.')
signal.signal(signal.SIGALRM,phase_timeout);signal.alarm(70)
request=json.loads(sys.stdin.read(65536));directory=Path(request['directory']);job=request['job_id']
assert directory.name=='p6-smoke-4b-08'
bound=directory/'reservation.json';assert bound.is_file() and not bound.is_symlink() and bound.stat().st_size<=32768
reservation=json.loads(bound.read_bytes())
assert reservation==request['reservation'] and reservation['job_id']==job and reservation['uid']==os.getuid()
assert reservation['job_name']=='hydra-p6-smoke-4b-08' and reservation['seconds']==600
record={'job_id':job,'read_only':True,'files':{},'scheduler':{}};total=0
for name,args in (('sacct',['sacct','-n','-P','-j',job,'--format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%200,NodeList']),
                  ('scontrol',['scontrol','-o','show','job',job])):
 result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
 assert len(result.stdout.encode())+len(result.stderr.encode())<=65536
 record['scheduler'][name]={'actual_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
for relative in ('slurm.out','slurm.err','actual-process-exit.txt','reservation.json.claimed',
 'result/request.json','result/scheduler.jsonl','result/model-admission.json','result/primitive.json',
 'result/planner.json','result/throughput.json','result/completion.json'):
 path=directory/relative
 if not path.is_file():continue
 assert not path.is_symlink()
 size=path.stat().st_size
 assert size<=4*1024*1024 and total+size<=8*1024*1024
 with path.open('rb') as stream:raw=stream.read(size)
 assert len(raw)==size
 total+=len(raw)
 record['files'][relative]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
    'base64':base64.b64encode(raw).decode(),'unchanged_size_after_read':path.stat().st_size==size}
print(json.dumps(record),flush=True)
