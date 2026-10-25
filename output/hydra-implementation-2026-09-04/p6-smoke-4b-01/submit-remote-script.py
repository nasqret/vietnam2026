
import hashlib,json,os,subprocess,sys
from pathlib import Path
os.umask(0o077)
request=json.loads(sys.stdin.read(128*1024))
spec=request['spec'];script=request['script']
assert hashlib.sha256(script.encode()).hexdigest()==spec['script_sha256']
directory=Path(spec['remote_job_directory'])
assert str(directory).endswith('/hydra-practical-v1-20260904/jobs/p6-smoke-4b-01')
queue=subprocess.run(['squeue','-h','-u',str(os.getuid()),'-o','%i|%T|%j|%b'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert queue.returncode==0 and not queue.stdout.strip(),'Another owned job is already queued/running; no implicit second GPU'
directory.mkdir(parents=True,exist_ok=False)
(directory/'job.sbatch').write_text(script)
(directory/'allocation-request.json').write_text(json.dumps(spec,indent=2)+'\n')
command=['sbatch','--hold','--parsable','--no-requeue','--account='+spec['account'],'--partition='+spec['partition'],
 '--nodes=1','--ntasks=1','--cpus-per-task=8','--mem=64G','--gres=gpu:1','--time=00:10:00',
 '--job-name='+spec['job_name'],'--comment=hydra-p6:'+spec['nonce'],
 '--chdir='+str(directory),'--output='+str(directory/'slurm.out'),'--error='+str(directory/'slurm.err'),str(directory/'job.sbatch')]
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
record={'actual_sbatch_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
 'uid':os.getuid(),'command':command,'held':True,'released':False,'gpu_seconds':0,'automatic_retry':False}
(directory/'held-submission.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
sys.exit(result.returncode)
