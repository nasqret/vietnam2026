
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
os.umask(0o077)
request=json.loads(sys.stdin.read(128*1024))
spec=request['spec'];script=request['script']
assert hashlib.sha256(script.encode()).hexdigest()==spec['script_sha256']
directory=Path(spec['remote_job_directory'])
assert str(directory).endswith('/hydra-practical-v1-20260904/jobs/p6-smoke-4b-05')
queue=subprocess.run(['squeue','--array','-h','-u',str(os.getuid()),'-o','%i|%T|%j|%b'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert queue.returncode==0 and len(queue.stdout.encode())<=16384
rows=queue.stdout.strip().splitlines();assert len(rows)<=32
observed=[]
for row in rows:
 job=row.split('|')[0].strip();assert re.fullmatch(r'[0-9]{1,20}(?:_[0-9]{1,10})?',job)
 query=subprocess.run(['scontrol','-o','show','job',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=5)
 assert query.returncode==0 and len(query.stdout.encode())<=65536
 fields=dict(re.findall(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)',query.stdout))
 assert 'ReqTRES' in fields
 if '_' in job:
  base,task=job.split('_');assert fields.get('ArrayJobId')==base and fields.get('ArrayTaskId')==task
 else:assert fields.get('JobId')==job
 assert 'gres/gpu' not in fields['ReqTRES'] and 'gres/gpu' not in fields.get('AllocTRES',''),'Another owned GPU allocation/reservation exists'
 observed.append({'job_id':job,'requested_tres':fields['ReqTRES'],'allocated_tres':fields.get('AllocTRES'), 'left_unchanged':True})
directory.mkdir(parents=True,exist_ok=False)
(directory/'job.sbatch').write_text(script)
(directory/'allocation-request.json').write_text(json.dumps(spec,indent=2)+'\n')
command=['sbatch','--hold','--parsable','--no-requeue','--account='+spec['account'],'--partition='+spec['partition'],
 '--nodes=1','--ntasks=1','--cpus-per-task=8','--mem=64G','--gres=gpu:1','--time=00:10:00',
 '--job-name='+spec['job_name'],'--comment=hydra-p6:'+spec['nonce'],
 '--chdir='+str(directory),'--output='+str(directory/'slurm.out'),'--error='+str(directory/'slurm.err'),str(directory/'job.sbatch')]
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
record={'actual_sbatch_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
 'uid':os.getuid(),'command':command,'held':True,'released':False,'gpu_seconds':0,'automatic_retry':False,'other_cpu_jobs':observed}
(directory/'held-submission.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
sys.exit(result.returncode)
